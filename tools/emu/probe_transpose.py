#!/usr/bin/env python3
"""Probe P0 of MACHINES + TRIG: the keyboard's octave and the pitch jumps (the plan of 2026-11-05,
_scratch/machines-transpose/plan.md): what the stock OS does at the sites the part `transpose` will use, on the OS's
own code. Nothing is patched: every part runs the official MAIN OS 1.13.

  0. The sites, in the user's MAIN OS (bytes only, no emulation): KeyboardView's key slot (0x400ff9cc -> 0x4001a0d2),
     its call of the KBT getter (0x4001a164), the smoother's call (0x400597a8), the LED frame's call of the views
     (0x40006a76, after the reset), the panel interrupt's LED step 0 (0x40059dea), the layer's MACHINES site
     (0x4001ca1e); the KBT getter's three callers and nothing else, the setter only from TRACK SETUP, the release path
     (0x40019d00..0x40019f44) without either; PITCH's descriptor (42: k 10, 0x2800..0x5800, default 0x4000); the LED
     table: TRIG 8 / 9 on row 3, 11 / 12 on row 4, 15 / 16 on row 5.
  1. The keyboard, KeyboardView's key handler (0x4001a0d2) with the project's chain stubbed and the real KBT getter on
     a pattern track: a trig key plays note = key index + 52 + KBT (TRIG 9 at KBT 0 = note 60) for KBT 0, +-12,
     +-60; d3 at 0x4001a164 is the track the note goes to; grid mode and an armed pattern selection leave the key to
     the views below (0, nothing played); a release reaches 0x40019d00 with the view and the key index only; MACHINES
     held changes nothing (what the part replaces); a code that is no trig goes to the base (0x40075f3c); the handler
     writes nothing in the UI state (finding for the switch locks' held-trig mask, +348 / +352).
  2. The LEDs: 0x40005f86 keeps the first state (a dim state 0x102 stays over a later 1, its base bit on); the blink
     (0x40005efc) times only states 3 and 4; the LED frame (0x40006a4a) has every state cleared when it reaches
     0x40006a76, then the views, then the frame's end (0x40006044), which leaves a state written at 0x40006a76 as it
     is and turns the empty ones off.
  3. Pitch after the smoother, on seqrig (the real audio interrupt, the smoothing, the voice loop): for each stock
     machine a note played with PITCH + 5 semitones (0x4500) and the same note with PITCH 0x4000 and 0x500 added to the
     smoother's output word (0x8000100c + 14 + 66 t + 20) right after its call (0x400597ae) are the same, sample for
     sample, and the smoother's state stays 0x4000 << 16 (nothing fed back); -7 too. A jump added from block 12 on
     equals PITCH set without a glide at block 12, and equals no jump up to that block: the jump acts within the
     block, on the note that plays.

Not probed (plan §5): a pattern change (the device test), the dimming (P2, notes/45), the layer's MACHINES on every
track (P1), SAMPLE (its source reads p + 0x14 every block, sampler.c).

Lines marked "finding" are facts for the design, not failures. Exits non-zero on a FAIL.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it:
run it in a normal terminal. About a minute.

    python3 tools/emu/probe_transpose.py --cycles model-cycles_OS1.13.syx
"""
import argparse
import gc
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import mcengine as E                # noqa: E402
import seqrig as S                  # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_shortcuts as SH         # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

# 0. the sites
KB_SLOT, KB_KEYS = 0x400ff9cc, 0x4001a0d2
KBT_SITE, KBT_GET, KBT_SET = 0x4001a164, 0x40016da6, 0x40016dd6
SMOOTH_SITE, SMOOTHER, AFTER_SMOOTH = 0x400597a8, 0x40058474, 0x400597ae
FRAME, FRAME_VIEWS, VIEWS, RESET, FRAME_END = 0x40006a4a, 0x40006a76, 0x40076ca2, 0x4000602a, 0x40006044
LED_STEP0 = 0x40059dea
RELEASE_FROM, RELEASE_UNTIL = 0x40019d00, 0x40019f44
DESC_TABLE, DESC_SIZE, PITCH_DESC = 0x4010dce0, 0x38, 42
LED_BITS, ROWS = 0x4010abf8, {8: 3, 9: 3, 11: 4, 12: 4, 15: 5, 16: 5}
# 1. the keyboard
PLAY, RELEASE, KEY_BASE = 0x40019f44, 0x40019d00, 0x40075f3c
TRACK_OF, HOLDER_OF, PSLOT_OF, SEQ_OF = 0x40012442, 0x4000f23e, 0x4000f208, 0x4000cfcc
F_D0DC, F_CCC0, VEL_WORD = 0x4000d0dc, 0x4000ccc0, 0x40016086
STATE = SH.STATE                                # 0x93a20000, what the stubbed 0x400cf9a8 gives
HOLDER, HVT, H_PAT, PATTRK, PSLOT = 0x93e40000, 0x93e50000, 0x93e50100, 0x93e30000, 0x93e10000
TRK = 2
GRID_A, GRID_B, SELECT = 357, 358, 389
# 2. the LEDs
LED_SET, LED_CHECK, LED_ON, LED_OFF, LED_TIMER = 0x40005f86, 0x4008e942, 0x4008e964, 0x4008e998, 0x4008e8c4
BLINK, BLINK_PHASE, LED_COLOUR = 0x40005efc, 0x404a90f4, 0x404a8c68
FRAME_DUE, LED_OBJ_OF, LED_SEND = 0x40076bfa, 0x400cfaf4, 0x4008e77e
LEDOBJ, FRAME_ARG = 0x93f00000, 0x93f10000
DIM1, DIM2 = 0x102, 0x202                       # the states the part will give its dim LEDs
# 3. pitch
PITCH_K = 0x0a
BLOCKS, JUMP_AT = 24, 12


def w32(u, a, v):
    u.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))


def s32(x):
    x &= 0xffffffff
    return x - (1 << 32) if x & 0x80000000 else x


# --- 0. the sites ----------------------------------------------------------------------------------------------------
def site_tests(img):
    at = lambda va, n: img[va - E.BASE:va - E.BASE + n]          # noqa: E731
    long_ = lambda va: struct.unpack(">I", at(va, 4))[0]        # noqa: E731

    def every(pat):
        out, i = [], img.find(pat)
        while i >= 0:
            out.append(E.BASE + i)
            i = img.find(pat, i + 1)
        return out
    check(long_(KB_SLOT) == KB_KEYS and at(KB_KEYS, 4).hex() == "4fefffd4",
          "KeyboardView's key slot 0x400ff9cc -> 0x4001a0d2 (lea -44(sp),sp)")
    check(at(KBT_SITE, 6).hex() == "4eb940016da6" and at(0x4001a236, 4).hex() == "4872e834",
          "0x4001a164: jsr 0x40016da6 (the KBT getter, 6 bytes); 0x4001a236: pea 52(a2,fp.l), the note")
    check(at(SMOOTH_SITE, 8).hex() == "4eb9400584742f13",
          "0x400597a8: jsr 0x40058474 (the smoother, 6 bytes), then move.l (a3),-(sp) at 0x400597ae")
    check(at(0x40006a70, 12).hex() == "4ebaf5b82f024eb940076ca2" and at(0x40006a88, 4).hex() == "6000f5ba",
          "the LED frame: jsr 0x4000602a (reset) at 0x40006a70, then jsr 0x40076ca2 (the views, 6 bytes) at 0x40006a76, "
          "then bra 0x40006044 (the end)")
    check(at(LED_STEP0, 10).hex() == "76ff781533c38c000000",
          "the panel interrupt's LED step 0 at 0x40059dea: moveq #-1,d3; moveq #21,d4; move.w d3,0x8c000000 (10 bytes)")
    check(at(SH.MACH_SITE, 6).hex() == "2f034e93588f", "the layer's MACHINES site 0x4001ca1e stock")
    gets = every(struct.pack(">I", KBT_GET))
    sets = every(struct.pack(">I", KBT_SET))
    check(gets == [0x4001a166, 0x4003e3c8, 0x4003e42e] and sets == [0x4003e444],
          f"the KBT getter 0x40016da6 is named only by the keyboard (0x4001a164) and TRACK SETUP (0x4003e3c6, "
          f"0x4003e42c), the setter 0x40016dd6 only by TRACK SETUP's change (0x4003e442): the sequencer never reads KBT "
          f"(operands at {[hex(a) for a in gets]}, {[hex(a) for a in sets]})")
    rel = at(RELEASE_FROM, RELEASE_UNTIL - RELEASE_FROM)
    check(struct.pack(">I", KBT_GET) not in rel and struct.pack(">I", KBT_SET) not in rel,
          "the release path 0x40019d00..0x40019f44 names neither the KBT getter nor the setter")
    d = struct.unpack(">14i", at(DESC_TABLE + DESC_SIZE * PITCH_DESC, DESC_SIZE))
    check(d[0] == 7 and d[1] == PITCH_K and d[2] == 0x2800 and d[3] == 0x5800 and d[4] == 0x4000,
          f"PITCH, descriptor 42: every machine, k {d[1]}, {d[2]:#06x}..{d[3]:#06x}, default {d[4]:#06x}: 0x100 a "
          "semitone, -24..+24")
    bits = {led: struct.unpack(">i", at(LED_BITS + 4 * led, 4))[0] for led in ROWS}
    check({led: b // 8 for led, b in bits.items()} == ROWS,
          f"the LED table 0x4010abf8: TRIG 8 / 9 on row 3, 11 / 12 on row 4, 15 / 16 on row 5 (bits {bits})")


# --- 1. the keyboard -------------------------------------------------------------------------------------------------
def kb(u, code, kbt, mode=None, held=(), pressed=True, t=TRK):
    """KeyboardView's key handler (view, event) for a key code, KBT on the track's pattern data (+721), the UI state
    in grid mode, with the pattern selection armed or neither, these keys held."""
    u.keys(held)
    st = bytearray(0x200)
    if mode == "grid":
        st[GRID_A] = st[GRID_B] = 1
    elif mode == "select":
        st[SELECT] = 1
    u.uc.mem_write(STATE, bytes(st))
    w32(u, HOLDER, HVT)
    w32(u, HVT + 40, H_PAT)
    pat = bytearray(722)
    pat[721] = kbt & 0xff
    pat[708] = 0x11
    u.uc.mem_write(PATTRK, bytes(pat))
    ev = bytearray(32)
    struct.pack_into(">II", ev, 12, code, 1 if pressed else 0)
    u.uc.mem_write(SH.EVENT, bytes(ev))
    u.hooks = {SH.UI_STATE: ("ui", STATE), SH.PROJECT: ("project", SH.PROJ), SH.PROJECT_TRACKS: ("tracks", SH.SEL),
               TRACK_OF: ("track", t), HOLDER_OF: ("holder", HOLDER), H_PAT: ("pattern", PATTRK),
               PSLOT_OF: ("pslot", PSLOT), SEQ_OF: ("seq", HOLDER), F_D0DC: ("d0dc", 0), F_CCC0: ("ccc0", 0),
               VEL_WORD: ("velword", 0x64), PLAY: ("play", 0), RELEASE: ("release", 0), KEY_BASE: ("base", 0)}
    d3, writes = [], []

    def at_site(uc, addr, size, ud):
        d3.append(uc.reg_read(SH.mk.UC_M68K_REG_D3) & 0xffffffff)

    def wrote(uc, access, addr, size, value, ud):
        writes.append(addr - STATE)
    h1 = u.uc.hook_add(UC_HOOK_CODE, at_site, begin=KBT_SITE, end=KBT_SITE)
    h2 = u.uc.hook_add(UC_HOOK_MEM_WRITE, wrote, begin=STATE, end=STATE + 0x1ff)
    u.calls.clear()
    vals = SH.sentinels(u)
    d0 = u.call(KB_KEYS, SH.VIEW, SH.EVENT)
    u.uc.hook_del(h1)
    u.uc.hook_del(h2)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals
    of = lambda n: [a for m, a in u.calls if m == n]            # noqa: E731
    return dict(d0=d0 & 0xff, play=of("play"), release=of("release"), base=of("base"), kbt=len(d3),
                d3=d3, writes=writes, ok=u.sp_ok and kept and not u.bad)


def keyboard_tests(stock):
    u = SH.UI(stock)
    notes, bad = {}, []
    for kbt in (0, 12, -12, 60, -60):
        for idx in (0, 8, 15):
            r = kb(u, 16 + idx, kbt)
            note = s32(r["play"][0][3]) if r["play"] else None
            notes[kbt, idx] = note
            if not (r["d0"] == 1 and len(r["play"]) == 1 and note == idx + 52 + kbt and r["play"][0][1] == idx
                    and r["play"][0][2] == TRK and r["d3"] == [TRK] and r["kbt"] == 1 and r["ok"]):
                bad.append((kbt, idx, r["d0"], note, r["d3"]))
    check(not bad,
          "a trig key plays note = key index + 52 + KBT, the key index and the track as arguments of 0x40019f44, d3 "
          "at 0x4001a164 = that track, KBT read once (TRIG 1 / 9 / 16 at KBT 0, +-12, +-60: "
          + ", ".join(f"{k:+d}: {notes[k, 0]}/{notes[k, 8]}/{notes[k, 15]}" for k in (0, 12, -12, 60, -60))
          + f"){'' if not bad else ' FAILED ' + str(bad)}")
    print("  finding: at KBT -60 the low keys give negative notes, which 0x40019f44 drops (above 127 unsigned): the "
          "stock keyboard is silent there; at +60 TRIG 16 gives 127")
    for mode in ("grid", "select"):
        r = kb(u, 16 + 10, 0, mode=mode)
        check(r["d0"] == 0 and not r["play"] and not r["release"] and r["ok"],
              f"{'grid mode (UI state +357 and +358)' if mode == 'grid' else 'the pattern selection armed (+389)'}: "
              f"TRIG 11 left to the views below (d0 {r['d0']}, nothing played)")
    r = kb(u, 16 + 10, 12, pressed=False)
    check(r["d0"] == 1 and not r["play"] and len(r["release"]) == 1 and r["release"][0][:2] == (SH.VIEW, 10) and r["ok"],
          f"a release of TRIG 11 reaches 0x40019d00 with the view and the key index only, no note "
          f"({[hex(a) for a in r['release'][0][:2]] if r['release'] else r})")
    r = kb(u, 16 + 10, 0, held=(SH.MACHINES,))
    check(r["d0"] == 1 and len(r["play"]) == 1 and s32(r["play"][0][3]) == 62 and r["ok"],
          "MACHINES held: TRIG 11 plays note 62 as without it (what the part replaces)")
    r = kb(u, 15, 0)
    check(len(r["base"]) == 1 and not r["play"] and r["kbt"] == 0 and r["ok"],
          "a code that is no trig key (15) goes to the base 0x40075f3c, nothing read")
    writes = set()
    for args in ((16 + 10, 0), (16 + 14, 12), (16 + 15, -12)):
        writes |= set(kb(u, *args)["writes"]) | set(kb(u, *args, pressed=False)["writes"])
    print(f"  finding: the keyboard handler writes into the UI state: {sorted(writes) or 'nothing'} (the held-trig "
          "mask is +348 / +352, the step words +92..+347)")


# --- 2. the LEDs -----------------------------------------------------------------------------------------------------
def led_state(u, led):
    return u.u32(LEDOBJ + 40 + 4 * led)


def led_tests(stock):
    u = SH.UI(stock)
    u.uc.mem_write(LEDOBJ, bytes(0x200))
    u.hooks = {LED_CHECK: ("check", 0), LED_ON: ("on", 0), LED_OFF: ("off", 0), LED_TIMER: ("timer", 0)}
    u.calls.clear()
    u.call(LED_SET, LEDOBJ, 11, DIM1, LED_COLOUR)
    first = [(n, a[0]) for n, a in u.calls if n in ("on", "off")]
    u.calls.clear()
    u.call(LED_SET, LEDOBJ, 11, 1, LED_COLOUR)
    u.call(LED_SET, LEDOBJ, 12, 1, LED_COLOUR)
    later = [(n, a[0]) for n, a in u.calls if n in ("on", "off")]
    check(led_state(u, 11) == DIM1 and first == [("on", 11)] and later == [("off", 12)] and led_state(u, 12) == 1
          and not u.bad,
          f"0x40005f86 keeps the first state: LED 11 set to {DIM1:#x} (base bit on: {first}), then 1 ignored; LED 12 "
          f"set to 1 (off: {later})")
    u.uc.mem_write(LEDOBJ + 40, bytes(0xd8))
    for led, s in ((11, DIM1), (15, DIM2), (16, 3), (9, 4)):
        w32(u, LEDOBJ + 40 + 4 * led, s)
    w32(u, BLINK_PHASE, 0)
    u.calls.clear()
    u.call(BLINK, LEDOBJ)
    timers = sorted((a[0], a[1]) for n, a in u.calls if n == "timer")
    check(timers == [(9, 42), (16, 6)] and not u.bad,
          f"the blink 0x40005efc times only states 3 (6 ticks) and 4 (42 ticks): {timers}; {DIM1:#x} and {DIM2:#x} "
          "are left alone")
    for led in range(54):
        w32(u, LEDOBJ + 40 + 4 * led, 2)
    seen = {}

    def at_views(uc, addr, size, ud):
        seen["states"] = bytes(uc.mem_read(LEDOBJ + 40, 0xd8))
        uc.mem_write(LEDOBJ + 40 + 4 * 11, struct.pack(">I", DIM1))      # what tr_frame will write there
    h = u.uc.hook_add(UC_HOOK_CODE, at_views, begin=FRAME_VIEWS, end=FRAME_VIEWS)
    u.hooks = {FRAME_DUE: ("due", 1), LED_OBJ_OF: ("ledobj", LEDOBJ), VIEWS: ("views", 0), LED_CHECK: ("check", 0),
               LED_ON: ("on", 0), LED_OFF: ("off", 0), LED_SEND: ("send", 0)}
    u.calls.clear()
    u.call(FRAME, FRAME_ARG)
    u.uc.hook_del(h)
    order = [n for n, _ in u.calls if n in ("due", "views", "send")]
    offs = sorted({a[0] for n, a in u.calls if n == "off"})
    check(seen.get("states") == bytes(0xd8) and order == ["due", "views", "send"] and led_state(u, 11) == DIM1
          and 11 not in offs and len(offs) > 40 and u.sp_ok and not u.bad,
          f"the LED frame 0x40006a4a: every state 0 at 0x40006a76 ({seen.get('states') == bytes(0xd8)}), then the views, "
          f"then the end, which leaves LED 11's {DIM1:#x} (written at 0x40006a76) and turns {len(offs)} empty LEDs off "
          f"({order}): a state set there comes before every view")


# --- 3. pitch after the smoother -------------------------------------------------------------------------------------
def play(stock, m, base, add=0, from_block=0, set_at=None, blocks=BLOCKS, t=TRK):
    """Machine m on track t, one trig on step 0 in block 2, PITCH = base (8.8); add: added to the smoother's output
    word of PITCH right after its call, from block from_block on; set_at = (block, word): PITCH set without a glide
    then. Returns (track t's output, the smoother's state of PITCH per block, unmapped accesses)."""
    e = E.Engine(stock)
    rig = S.Rig(e, bpm=120)
    c, s, w, ct, d = E.DEFAULTS[m]
    for k, v in dict(machine=m, color=c, shape=s, sweep=w, contour=ct, decay=d, finetune=64).items():
        rig.param(t, E.SLOT[k], int(round(v * 256)))
    rig.param(t, PITCH_K, base)
    j = (0xe + 0x42 * t + 2 * PITCH_K) // 2
    now = {"b": 0}

    def after(uc, addr, size, ud):
        if now["b"] >= from_block:
            a = S.PARAMS + 2 * j
            v = struct.unpack(">h", uc.mem_read(a, 2))[0]
            uc.mem_write(a, struct.pack(">h", v + add))
    if add:
        e.uc.hook_add(UC_HOOK_CODE, after, begin=AFTER_SMOOTH, end=AFTER_SMOOTH)
    rig.set_step(t, 0)
    rig.schedule_step(t, 0, rig.now + 2 * rig.blk + rig.blk // 3)
    out, state = [], []
    for b in range(blocks):
        now["b"] = b
        if set_at and b == set_at[0]:
            rig.param(t, PITCH_K, set_at[1])
        info = rig.block()
        out.append(info["out"][t])
        state.append(rig.r32(S.SMOOTH + 4 * j, True))
    res = np.concatenate(out), state, list(e.unmapped)
    del rig, e
    gc.collect()                                # 30 engines one after the other: free each one's memory
    return res


def pitch_tests(stock):
    for m, name in enumerate(E.MACH):
        a, _, ua = play(stock, m, 0x4500)
        b, st, ub = play(stock, m, 0x4000, add=0x500)
        c, _, uc_ = play(stock, m, 0x3900)
        d, st2, ud = play(stock, m, 0x4000, add=-0x700)
        flat = all(x == 0x4000 << 16 for x in st + st2)
        check(np.array_equal(a, b) and np.array_equal(c, d) and np.max(np.abs(a)) > 1e6 and flat
              and not (ua or ub or uc_ or ud),
              f"{name}: PITCH 0x4500 and PITCH 0x4000 + 0x500 after the smoother play the same, sample for sample; "
              f"0x3900 and -0x700 too; the smoother's state 0x4000 << 16 in every block (peak {np.max(np.abs(a)):.3g})")
    for m in (E.MACH["KICK"], E.MACH["TONE"]):
        name = list(E.MACH)[m]
        n, _, _ = play(stock, m, 0x4000)
        j, _, uj = play(stock, m, 0x4000, add=0x500, from_block=JUMP_AT)
        s, _, us = play(stock, m, 0x4000, set_at=(JUMP_AT, 0x4500))
        cut = 32 * JUMP_AT
        check(np.array_equal(j, s) and np.array_equal(j[:cut], n[:cut]) and not np.array_equal(j[cut:], n[cut:])
              and not (uj or us),
              f"{name}: 0x500 added from block {JUMP_AT} on equals PITCH set to 0x4500 without a glide at that block, "
              "and no jump before it: the jump acts within its block, on the note that plays")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--sites", action="store_true", help="section 0 only (no emulation)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    print("0. the sites")
    site_tests(stock)
    if not args.sites:
        print("1. the keyboard")
        keyboard_tests(stock)
        print("2. the LEDs")
        led_tests(stock)
        print("3. pitch after the smoother (seqrig)")
        pitch_tests(stock)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
