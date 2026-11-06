#!/usr/bin/env python3
"""Proof of Transpose (the plan of 2026-11-05, _scratch/machines-transpose/plan.md, step P1) on the OS's own code,
through the builder's part tools/machines/transpose/ and the shortcut layer's 0.6 (MACHINES a held key on every track).
P0 (probe_transpose.py) read the stock sites; this compares the stock OS and the builds with Transpose.

  1. the build (no Unicorn, also with --dry), for Transpose alone, with SAMPLE, with POTS and Crush, and with the full
     offered set: KeyboardView's key slot (0x400ff9cc) -> tr_keys, jsr tr_kbt at 0x4001a164, jsr tr_pitch at
     0x400597a8, jsr tr_frame at 0x40006a76; the part's data block: the shortcut layer's data block's address, the
     rest zero; the layer always there, its +0x1c (every) 1, and 0 in the same build without Transpose; every other
     write as in that build (alone: only the layer's and the payload's boot); the payload as in that build up to
     Transpose's code but for the every byte; the tweaks that write other bytes at its sites among the computed
     conflicts; since 0.3 jsr tr_reload at the reload's three calls (0x4001c19c, 0x4001b884, 0x4002cad0);
  2. the keys, KeyboardView's key handler through its vtable entry, the stock OS and the build with Transpose side by
     side, the project's chain stubbed as in P0: every key code 15..32, held keys none / MACHINES / MACHINES + FUNC /
     MACHINES + TRACK, keyboard mode / grid mode / an armed pattern selection, a press, a release, a repeat and a long
     press: TRIG 8, 9, 11, 12, 15, 16 pressed with MACHINES alone in keyboard mode are taken (d0 1, nothing played,
     one new LED frame asked for the view), everything else does what the stock OS does (the same d0 and the same
     calls); then the values: TRIG 16 three times -> +1, +2, +2; TRIG 15 five times -> +1, 0, -1, -2, -2; TRIG 12 ->
     +7, again -> 0, TRIG 9 -> -5, TRIG 11 -> +5; another track keeps its own; a taken press marks the layer's +0x13;
     its release and repeats are taken too, a release whose press went to the keyboard reaches the stock release;
     d2-d7/a2-a6 and the stack kept;
  3. the keyboard's octave: with MACHINES not held, a key plays note = key index + 52 + KBT + 12 x the track's octave,
     clamped to KBT's -60..+60 (KBT 0, +-12, +-55, +-60, octaves -2..+2); another track's octave changes nothing; at
     octave 0 the same note as the stock OS;
  4. the jumps on tr_pitch itself (the smoother stubbed): the PITCH words of the tracks with a jump moved by -7 / -5 /
     +5 / +7 semitones and clamped to 0x2800..0x5800, the others untouched, the smoother's buffer returned; a new
     playing pattern number (or none) clears every octave and jump and is kept; the same number changes nothing;
  5. the jumps on the audio path (seqrig: the real interrupt, smoother and voices; the stock OS and the build side by
     side): for each stock machine, a jump of -7 and of +7 plays as PITCH set to that sum on the stock OS, sample for
     sample; no jump plays as the stock OS; a jump on another track changes nothing on this one; the clamp at +24 and
     -24;
  6. the LEDs, the LED frame 0x40006a4a with the views and the hardware stubbed: with MACHINES alone in keyboard mode,
     TRIG 15 / 16 dim, mid or full for the octave and TRIG 8 / 9 / 11 / 12 full for the jump in force and dim
     otherwise (every octave and jump), the views called once after, every other LED as the stock frame leaves it;
     without MACHINES, with FUNC or TRACK, in grid mode, with the selection armed or without a project: the same
     states as the stock frame;
  7. MACHINES on every track (the layer's 0.6, MainScreenView's MACHINES case 0x4001c252): on every stock machine and
     SAMPLE's, a press that would open the list is taken, the release opens it unless +0x13 was marked; with the list
     open the press closes it; FUNC + MACHINES the PRESET browser; the same build without Transpose: the stock
     machines toggle on the press as before;
  8. the dimming (0.2), the real panel interrupt (start, key columns, LED steps; test_trigless_dim.py's rig: the port,
     PIT3's counter and the latches modelled, the OS's own start-up copying the payload) on the stock OS and the build:
     without a mask every write and every latched byte as the stock OS, start-up included; with masks (TRIG 8, 11, 15
     dim, 9, 16 mid, 12 full), a period of 4 ms and of 3 ms: no hazard on the latches, registers back at every rte,
     every other write as the stock OS, step 0 [DIR, (DATA, SET 8, CLR 0xfff7) x k, DATA] with k <= 3 on rows 3..5,
     at least 272 counts (2 us) between writes, every other LED bit the stock one at the same instants, a dim key lit
     1 cycle of n and a mid one 2 of n in steady state, never lit when the stock OS has it dark, the running light and
     a blink dark at least as long; 20 us of latency: the light over every 100 ms within 1.5 % of 1/4 and 1/2; step 0
     late (PIT3 reloading): the gaps kept; PIT3 standing still: every step ends; the masks cleared: every LED back to
     the stock OS within 2 cycles;
  9. the pattern's reload (0.3), the stock OS and the build side by side, the reload (0x400107d8) stubbed: FUNC +
     PATTERN tapped through MainScreenView's PATTERN case (0x4001c154) reloads from the temp area, FUNC + PATTERN
     held opens the prompt, PATTERN alone neither; the prompt's YES (0x4001b858, and 0x4002caa4 from the menu)
     reloads from the project, NO does not; the same calls with the same arguments on both; when the reload says
     reloaded every track's jump is 0, the octaves and the rest of the data block as they were; when it fails nothing
     changes; tr_reload itself: the reload called once with its five arguments, its d0 returned whole, d2-d7/a2-a6
     and the stack kept.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it:
run it in a normal terminal. Some minutes, most of them sections 5 and 8.

    python3 tools/emu/test_transpose.py --cycles model-cycles_OS1.13.syx
    python3 tools/emu/test_transpose.py --cycles model-cycles_OS1.13.syx --dry      # section 1 only, without Unicorn
"""
import argparse
import gc
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

PART = compose.load_part("transpose")
DATA = PART["data"]
LAYER = compose.load_part("shortcuts")
EVERY, USED, PENDING = LAYER["data"]["every"], LAYER["data"]["used"], LAYER["data"]["pending"]
SELECTIONS = [[], ["sampler"], ["pots", "crush"], ["sampler", "digidelay", "pots", "smpfilter", "crush", "ring", "reso",
                                                   "eq"]]
KB_SLOT, KB_KEYS = 0x400ff9cc, 0x4001a0d2
SITES = {0x4001a164: ("4eb940016da6", "4eb9", "tr_kbt"), 0x400597a8: ("4eb940058474", "4eb9", "tr_pitch"),
         0x40006a76: ("4eb940076ca2", "4eb9", "tr_frame")}
RELOAD, RELOAD_SITES = 0x400107d8, (0x4001c19c, 0x4001b884, 0x4002cad0)    # the pattern's reload and its calls (0.3)
SITES.update({va: ("4eb9400107d8", "4eb9", "tr_reload") for va in RELOAD_SITES})
LED_SITE = (0x40059dea, "76ff781533c38c000000", "tr_led")    # jmp tr_led ; nop ; nop (0.2)
ALL_SITES = set(SITES) | {KB_SLOT, LED_SITE[0]}
BOOT_SITES = {0x400004b2, 0x400b1106, 0x4016cae8}   # the payload's boot: the hook, the stub's mask and its sprite
OURS = {23: 0, 24: 1, 26: 2, 27: 3, 30: 4, 31: 5}   # key code -> bit: TRIG 8, 9, 11, 12, 15, 16
JUMP_WORD = {1: -0x700, 2: -0x500, 3: 0x500, 4: 0x700}
FULL, MID, DIM = 2, 0x202, 0x102


def composed(stock, sel, transpose):
    tweak, info = compose.compose(stock, sel, transpose=transpose)
    patched, _ = build.apply_writes(stock, [tweak])
    runtime = build.payload_runtime(tweak, stock, None)
    return tweak, info, bytes(patched) + build.payload_image(tweak, runtime), runtime


def layer_sites():
    s = LAYER["sites"]
    out = {int(s["knob"]["vtable"], 16), int(s["conv"]["jmp"], 16)} | {int(r["at"], 16) for r in s["record"]}
    out |= {int(k["at"], 16) for k in s["keys"]} | {int(a, 16) for a in s["ptab"]["operands"]}
    return out


# --- 1. the build -----------------------------------------------------------------------------------------------------
def build_tests(key, stock, w, wo):
    tweak, info, _img, runtime = w
    ti, li = info["transpose"], info["part"]
    by = {x["off"] + compose.BASE: x for x in tweak["writes"]}
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    kw = by.get(KB_SLOT)
    check(kw is not None and kw["old"] == f"{KB_KEYS:08x}" and kw["new"] == f"{syms['tr_keys']:08x}",
          f"{key}: KeyboardView's key slot {KB_SLOT:#x}: {KB_KEYS:#x} -> tr_keys ({syms['tr_keys']:#x})")
    for va, (old, op, name) in SITES.items():
        x = by.get(va)
        check(x is not None and x["old"] == old and x["new"] == op + f"{syms[name]:08x}",
              f"{key}: {va:#x} {old} -> {op} {name} ({syms[name]:#x})")
    va, old, name = LED_SITE
    x = by.get(va)
    check(x is not None and x["old"] == old and x["new"] == f"4ef9{syms[name]:08x}4e714e71",
          f"{key}: {va:#x} {old} -> jmp {name} ({syms[name]:#x}) ; nop ; nop")
    pay = compose.gs.PAY_ALONE
    block = runtime[ti["data_at"] - pay:ti["data_at"] - pay + DATA["size"]]
    sc = struct.unpack_from(">I", block, DATA["sc"])[0]
    rest = bytearray(block[4:])
    period, rest[DATA["n"] - 4] = rest[DATA["n"] - 4], 0
    check(li is not None and sc == li["data_at"] and period == DATA["n_value"] and not any(rest)
          and syms["tr_data"] == ti["data_at"],
          f"{key}: the data block at {ti['data_at']:#x}: the shortcut layer's data block ({sc:#x}), the period "
          f"{period} ms, the rest zero")
    check(li is not None and runtime[li["data_at"] - pay + EVERY] == 1,
          f"{key}: the shortcut layer there, its every byte (+{EVERY:#x}) 1")
    if wo is None:
        others = set(by) - ALL_SITES
        check(others == layer_sites() | BOOT_SITES,
              f"{key}: nothing else written but the shortcut layer's sites and the payload's boot "
              f"({len(by)} writes; {sorted(map(hex, others - layer_sites() - BOOT_SITES))})")
    else:
        bw = {x["off"] + compose.BASE: x for x in wo[0]["writes"]}
        diff = sorted(a for a in set(by) | set(bw) if by.get(a) != bw.get(a))
        check(set(diff) <= ALL_SITES | BOOT_SITES and not ALL_SITES & set(bw),
              f"{key}: every other write as in the build without Transpose ({len(by)} writes; differing "
              f"{', '.join(map(hex, diff))})")
        lw = wo[1]["part"]
        rwo = wo[3]
        n = ti["code_at"] - pay
        a, b = bytearray(runtime[:n]), bytearray(rwo[:n])
        ok = lw is not None and lw["data_at"] == li["data_at"] and b[li["data_at"] - pay + EVERY] == 0
        if ok:
            b[li["data_at"] - pay + EVERY] = 1
        check(ok and a == b, f"{key}: the payload as in the build without Transpose up to Transpose's code "
                             f"({ti['code_at']:#x}) but for the layer's every byte (0 there)")
    ours = {va: len(by[va]["new"]) // 2 for va in ALL_SITES}
    takers = set()
    for f in compose.DEV.glob("*.json"):
        if f.name == "device.json":
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(t, dict):
            continue
        for x in t.get("writes", []):
            va, n = x["off"] + compose.BASE, len(x["new"]) // 2
            if any(va < s_ + k and s_ < va + n for s_, k in ours.items()) and (va not in by or by[va]["new"] != x["new"]):
                takers.add(t["id"])
    check(takers <= set(tweak["conflicts"]),
          f"{key}: the tweaks that write other bytes at its sites ({', '.join(sorted(takers)) or 'none'}) among the "
          "computed conflicts")


# --- the interface: KeyboardView's keys ---------------------------------------------------------------------------
def ui(img, runtime=None):
    import test_shortcuts as SH
    return SH.UI(img, runtime or b"")


def reset(u, data_at, keep_sc=True):
    if data_at:
        sc = u.u32(data_at) if keep_sc else 0
        u.uc.mem_write(data_at, struct.pack(">I", sc) + bytes(DATA["size"] - 4))


def kb(u, code, flags, held=(), mode=None, t=2, kbt=0, oct_=None, data_at=None, project=True):
    """KeyboardView's key handler as the OS calls it, through its vtable entry (view, event): (d0, the calls, kept)."""
    import probe_transpose as P
    import test_shortcuts as SH
    u.keys(held)
    st = bytearray(0x200)
    if mode == "grid":
        st[P.GRID_A] = st[P.GRID_B] = 1
    elif mode == "select":
        st[P.SELECT] = 1
    u.uc.mem_write(P.STATE, bytes(st))
    u.uc.mem_write(P.HOLDER, struct.pack(">I", P.HVT))
    u.uc.mem_write(P.HVT + 40, struct.pack(">I", P.H_PAT))
    pat = bytearray(722)
    pat[721] = kbt & 0xff
    pat[708] = 0x11
    u.uc.mem_write(P.PATTRK, bytes(pat))
    if oct_ is not None and data_at:
        u.uc.mem_write(data_at + DATA["oct"], bytes(o & 0xff for o in oct_))
    ev = bytearray(32)
    struct.pack_into(">II", ev, 12, code, flags)
    u.uc.mem_write(SH.EVENT, bytes(ev))
    u.hooks = {SH.UI_STATE: ("ui", P.STATE), SH.PROJECT: ("project", SH.PROJ if project else 0),
               SH.PROJECT_TRACKS: ("tracks", SH.SEL), P.TRACK_OF: ("track", t), P.HOLDER_OF: ("holder", P.HOLDER),
               P.H_PAT: ("pattern", P.PATTRK), P.PSLOT_OF: ("pslot", P.PSLOT), P.SEQ_OF: ("seq", P.HOLDER),
               P.F_D0DC: ("d0dc", 0), P.F_CCC0: ("ccc0", 0), P.VEL_WORD: ("velword", 0x64), P.PLAY: ("play", 0),
               P.RELEASE: ("release", 0), P.KEY_BASE: ("base", 0), SH.VIEW_LEDS: ("leds", 0)}
    u.calls.clear()
    vals = SH.sentinels(u)
    d0 = u.call(u.u32(KB_SLOT), SH.VIEW, SH.EVENT)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals
    calls = [(n, a[:4]) for n, a in u.calls if n in ("play", "release", "base", "leds")]
    return d0 & 0xff, calls, u.sp_ok and kept and not u.bad


def key_tests(key, stock, w):
    import test_shortcuts as SH
    tweak, info, img, runtime = w
    da, sc = info["transpose"]["data_at"], info["part"]["data_at"]
    a, b = ui(stock), ui(img, runtime)
    M, F, Tk = SH.MACHINES, SH.FUNC, SH.TRACK
    bad, taken, cases = [], 0, 0
    for code in range(15, 33):
        for held in ((), (M,), (M, F), (M, Tk)):
            for mode in (None, "grid", "select"):
                for flags in (1, 0, 1 | 8, 1 | 0x20):
                    reset(b, da)
                    ra = kb(a, code, flags, held, mode)
                    rb = kb(b, code, flags, held, mode, data_at=da)
                    ours = code in OURS and held == (M,) and mode is None and flags == 1
                    cases += 1
                    if ours:
                        taken += 1
                        if rb[0] != 1 or [(n_, x[0]) for n_, x in rb[1]] != [("leds", SH.VIEW)] or not rb[2]:
                            bad.append((code, held, mode, flags, rb))
                    elif ra[0] != rb[0] or ra[1] != rb[1] or not (ra[2] and rb[2]):
                        bad.append((code, held, mode, flags, ra, rb))
    check(not bad, f"{key}: {cases} key events on the stock OS and on the build: the {taken} presses of TRIG 8, 9, 11, "
                   "12, 15, 16 with MACHINES alone in keyboard mode taken (nothing played, one LED frame asked), every "
                   "other as the stock OS (the same d0 and calls; releases and repeats without a press of ours too); "
                   "registers and stack kept" + (f"; DIFFERENT {bad[:3]}" if bad else ""))

    def press(code, t=2):
        r = kb(b, code, 1, (M,), t=t, data_at=da)
        kb(b, code, 0, (M,), t=t, data_at=da)
        return r

    def vals(t):
        return struct.unpack(">b", b.uc.mem_read(da + DATA["oct"] + t, 1))[0], b.uc.mem_read(da + DATA["jump"] + t, 1)[0]
    reset(b, da)
    octs = []
    for code in (31, 31, 31, 30, 30, 30, 30, 30):
        press(code)
        octs.append(vals(2)[0])
    jumps = []
    for code in (27, 27, 24, 26):
        press(code)
        jumps.append(vals(2)[1])
    press(23, t=4)
    other = vals(4), vals(2)
    check(octs == [1, 2, 2, 1, 0, -1, -2, -2] and jumps == [4, 0, 2, 3] and other == ((0, 1), (-2, 3)),
          f"{key}: TRIG 16 x3, TRIG 15 x5: octaves {octs}; TRIG 12, 12, 9, 11: jumps {jumps} (+7, 0, -5, +5); TRIG 8 on "
          f"track 4: {other[0]}, track 2 keeps {other[1]}")
    b.uc.mem_write(sc + USED, b"\x00")
    reset(b, da)
    r_press = kb(b, 26, 1, (M,), data_at=da)
    used = b.uc.mem_read(sc + USED, 1)[0]
    r_rep = kb(b, 26, 1 | 8, (M,), data_at=da)
    r_rel = kb(b, 26, 0, (), data_at=da)              # MACHINES let go first: the release is still ours
    held_after = b.uc.mem_read(da + DATA["held"], 1)[0]
    kb(b, 26, 1, (), data_at=da)                      # a press that goes to the keyboard
    r_rel2 = kb(b, 26, 0, (M,), data_at=da)           # its release with MACHINES held: the stock release
    ra = kb(a, 26, 0, (M,))
    check(r_press[0] == 1 and used == 1 and r_rep == (1, [], True) and r_rel == (1, [], True) and held_after == 0
          and r_rel2 == ra and ra[1] and ra[1][0][0] == "release",
          f"{key}: a taken press marks the layer's +0x13 ({used}); its repeat and its release (MACHINES let go first) "
          f"taken, nothing else; a release whose press went to the keyboard reaches the stock release ({r_rel2[1]})")
    return a, b


# --- 3. the keyboard's octave -----------------------------------------------------------------------------------------
def kbt_tests(key, a, b, da):
    bad, n = [], 0
    for kbt in (0, 12, -12, 55, -55, 60, -60):
        for o in (-2, -1, 0, 1, 2):
            for idx in (0, 8, 15):
                octs = [0] * 6
                octs[2] = o
                octs[3] = 2 if o != 2 else -2            # another track's octave: no effect
                rb = kb(b, 16 + idx, 1, (), kbt=kbt, oct_=octs, data_at=da)
                ra = kb(a, 16 + idx, 1, (), kbt=kbt)
                want = idx + 52 + max(-60, min(60, kbt + 12 * o))
                got = struct.unpack(">i", struct.pack(">I", rb[1][0][1][3]))[0] if rb[1] and rb[1][0][0] == "play" else None
                stock = struct.unpack(">i", struct.pack(">I", ra[1][0][1][3]))[0] if ra[1] else None
                n += 1
                if got != want or (o == 0 and rb != ra) or stock != idx + 52 + kbt or not rb[2]:
                    bad.append((kbt, o, idx, got, want, stock))
    reset(b, da)
    check(not bad, f"{key}: {n} keys: note = key index + 52 + clamp(KBT + 12 x octave, -60, 60), another track's octave "
                   "ignored, at octave 0 the stock note and calls" + (f"; DIFFERENT {bad[:3]}" if bad else ""))


# --- 4. tr_pitch itself -----------------------------------------------------------------------------------------------
def pitch_unit_tests(key, b, syms, da):
    buf, pat = 0x93f20000, 0x93f40000
    words = [0x4000, 0x5600, 0x2a00, 0x4321, 0x3000, 0x5800]
    u = b

    def run(jumps, octs, number, last):
        u.uc.mem_write(buf, bytes(0x200))
        for t, wv in enumerate(words):
            u.uc.mem_write(buf + 34 + 66 * t, struct.pack(">H", wv))
            u.uc.mem_write(buf + 32 + 66 * t, b"\x12\x34")             # k 9, next to it: untouched
        u.uc.mem_write(da + DATA["oct"], bytes(o & 0xff for o in octs))
        u.uc.mem_write(da + DATA["jump"], bytes(jumps))
        u.uc.mem_write(da + DATA["last"], struct.pack(">I", last))
        if number is None:
            u.uc.mem_write(0x40a7887c, bytes(4))
        else:
            u.uc.mem_write(0x40a7887c, struct.pack(">I", pat))
            u.uc.mem_write(pat + 30706, struct.pack(">I", number))
        u.hooks = {0x40058474: ("smoother", buf)}
        u.calls.clear()
        d0 = u.call(syms["tr_pitch"], 0x800015a0)
        got = [struct.unpack(">H", u.uc.mem_read(buf + 34 + 66 * t, 2))[0] for t in range(6)]
        side = all(bytes(u.uc.mem_read(buf + 32 + 66 * t, 2)) == b"\x12\x34" for t in range(6))
        st = (list(struct.unpack(">6b", u.uc.mem_read(da + DATA["oct"], 6))), list(u.uc.mem_read(da + DATA["jump"], 6)),
              u.u32(da + DATA["last"]))
        args = [a[0] for n, a in u.calls if n == "smoother"]
        return d0 & 0xffffffff, got, side and u.sp_ok and not u.bad and args == [0x800015a0], st
    jumps, octs = [0, 4, 1, 3, 2, 4], [1, 0, -2, 0, 2, 0]
    d0, got, ok, st = run(jumps, octs, 7, 7)
    want = [max(0x2800, min(0x5800, wv + (JUMP_WORD[j] if j else 0))) for wv, j in zip(words, jumps)]
    check(d0 == buf and got == want and ok and st == (octs, jumps, 7),
          f"{key}: tr_pitch: the smoother's buffer back, PITCH words {[f'{x:#06x}' for x in got]} (jumps {jumps}, "
          "clamped to 0x2800..0x5800), k 9 next to them untouched, the values kept on the same pattern")
    d0, got, ok, st = run(jumps, octs, 8, 7)
    check(got == words and ok and st == ([0] * 6, [0] * 6, 8),
          f"{key}: another playing pattern (7 -> 8): every octave and jump cleared before the words, the number kept")
    d0, got, ok, st = run(jumps, octs, None, 8)
    check(got == words and ok and st == ([0] * 6, [0] * 6, 0xffffffff),
          f"{key}: no playing pattern: cleared too, 0xffffffff kept")
    reset(b, da)


# --- 5. the jumps on the audio path -----------------------------------------------------------------------------------
def play(img, m, base, runtime=None, tweak=None, jump=None, blocks=20, t=2):
    import mcengine as E
    import seqrig as S
    import test_compose as TC
    if runtime is None:
        e = E.Engine(img)
    else:
        e = E.Engine(img, payload=(E.PAYLOAD_DST, runtime), payload_code=TC.code_ranges(tweak))
    rig = S.Rig(e, bpm=120)
    c, s, w_, ct, d = E.DEFAULTS[m]
    for k, v in dict(machine=m, color=c, shape=s, sweep=w_, contour=ct, decay=d, finetune=64).items():
        rig.param(t, E.SLOT[k], int(round(v * 256)))
    rig.param(t, 0x0a, base)
    if jump:
        da, track, j = jump
        e.uc.mem_write(da + DATA["last"], struct.pack(">I", 0xffffffff))     # no playing pattern in the rig
        e.uc.mem_write(da + DATA["jump"] + track, bytes([j]))
    rig.set_step(t, 0)
    rig.schedule_step(t, 0, rig.now + 2 * rig.blk + rig.blk // 3)
    import numpy as np
    out = np.concatenate([rig.block()["out"][t] for _ in range(blocks)])
    res = out, list(e.unmapped)
    del rig, e
    gc.collect()
    return res


def audio_tests(key, stock, w):
    import numpy as np
    import mcengine as E
    tweak, info, img, runtime = w
    da = info["transpose"]["data_at"]
    bad = []
    for m, name in enumerate(E.MACH):
        ref0, u0 = play(stock, m, 0x4000)
        none, u1 = play(img, m, 0x4000, runtime, tweak)
        for j in (1, 4):
            ref, u2 = play(stock, m, 0x4000 + JUMP_WORD[j])
            got, u3 = play(img, m, 0x4000, runtime, tweak, (da, 2, j))
            if not np.array_equal(ref, got) or np.max(np.abs(ref)) < 1e6 or u2 or u3:
                bad.append((name, j))
        if not np.array_equal(ref0, none) or u0 or u1:
            bad.append((name, "no jump"))
    check(not bad, f"{key}: every stock machine: a jump of -7 and of +7 plays as PITCH 0x3900 and 0x4700 on the stock "
                   "OS, sample for sample; no jump as the stock OS" + (f"; DIFFERENT {bad}" if bad else ""))
    tone = E.MACH["TONE"]
    ref, _ = play(stock, tone, 0x4000)
    got, u4 = play(img, tone, 0x4000, runtime, tweak, (da, 4, 4))
    hi_ref, _ = play(stock, tone, 0x5800)
    hi, u5 = play(img, tone, 0x5600, runtime, tweak, (da, 2, 4))
    lo_ref, _ = play(stock, tone, 0x2800)
    lo, u6 = play(img, tone, 0x2a00, runtime, tweak, (da, 2, 1))
    check(np.array_equal(ref, got) and np.array_equal(hi_ref, hi) and np.array_equal(lo_ref, lo) and not (u4 or u5 or u6),
          f"{key}: TONE: a jump on track 4 changes nothing on track 2; PITCH +22 with +7 plays as +24, -22 with -7 as -24")


# --- 6. the LEDs ------------------------------------------------------------------------------------------------------
def frame(u, held=(), mode=None, t=2, project=True, octs=None, jumps=None, da=None):
    import probe_transpose as P
    import test_shortcuts as SH
    u.keys(held)
    st = bytearray(0x200)
    if mode == "grid":
        st[P.GRID_A] = st[P.GRID_B] = 1
    elif mode == "select":
        st[P.SELECT] = 1
    u.uc.mem_write(P.STATE, bytes(st))
    if da:
        u.uc.mem_write(da + DATA["oct"], bytes(o & 0xff for o in octs))
        u.uc.mem_write(da + DATA["jump"], bytes(jumps))
    u.uc.mem_write(P.LEDOBJ, bytes(0x200))
    u.hooks = {P.FRAME_DUE: ("due", 1), P.LED_OBJ_OF: ("ledobj", P.LEDOBJ), P.VIEWS: ("views", 0),
               P.LED_CHECK: ("check", 0), P.LED_ON: ("on", 0), P.LED_OFF: ("off", 0), P.LED_SEND: ("send", 0),
               SH.UI_STATE: ("ui", P.STATE), SH.PROJECT: ("project", SH.PROJ if project else 0),
               SH.PROJECT_TRACKS: ("tracks", SH.SEL), P.TRACK_OF: ("track", t)}
    u.calls.clear()
    u.call(P.FRAME, P.FRAME_ARG)
    states = [u.u32(P.LEDOBJ + 40 + 4 * i) for i in range(54)]
    order = [n for n, _ in u.calls if n in ("due", "views", "send")]
    return states, order, u.sp_ok and not u.bad


def masks(u, da):
    return (list(u.uc.mem_read(da + DATA["m1"], 8)), list(u.uc.mem_read(da + DATA["m2"], 8)),
            u.uc.mem_read(da + DATA["any"], 1)[0])


def led_tests(key, a, b, da):
    table = struct.unpack(">54l", bytes(a.uc.mem_read(0x4010abf8, 216)))
    ref, ref_order, ok_a = frame(a)
    bad, n = [], 0
    for o in (-2, -1, 0, 1, 2):
        for j in range(5):
            octs, jumps = [0] * 6, [0] * 6
            octs[2], jumps[2] = o, j
            octs[1], jumps[1] = 2, 4                     # another track's values: not shown
            st, order, ok = frame(b, (5,), octs=octs, jumps=jumps, da=da)
            want = list(ref)
            want[15] = (MID if o == -1 else FULL) if o < 0 else DIM
            want[16] = (MID if o == 1 else FULL) if o > 0 else DIM
            for i, led in enumerate((8, 9, 11, 12)):
                want[led] = FULL if j == i + 1 else DIM
            m1, m2 = [0] * 8, [0] * 8
            for led in (8, 9, 11, 12, 15, 16):
                bit = table[led]
                if want[led] == DIM:
                    m1[bit >> 3] |= 1 << (bit & 7)
                elif want[led] == MID:
                    m2[bit >> 3] |= 1 << (bit & 7)
            n += 1
            if st != want or order != ref_order or not ok or masks(b, da) != (m1, m2, 1):
                bad.append((o, j, [hex(st[x]) for x in (8, 9, 11, 12, 15, 16)], masks(b, da)))
    check(not bad and ok_a, f"{key}: the LED frame with MACHINES in keyboard mode, {n} octaves and jumps: TRIG 15 / 16 "
                            "dim, mid or full, TRIG 8 / 9 / 11 / 12 full for the jump in force, else dim, and their bits "
                            "in the masks (dim in m1, mid in m2, by the LED table 0x4010abf8); every other LED as the "
                            "stock frame; the views once, then the end" + (f"; DIFFERENT {bad[:3]}" if bad else ""))
    import test_shortcuts as SH
    off = []
    for held, mode, project in (((), None, True), ((5, SH.FUNC), None, True), ((5, SH.TRACK), None, True),
                                ((5,), "grid", True), ((5,), "select", True), ((5,), None, False)):
        sa = frame(a, held, mode, project=project)
        b.uc.mem_write(da + DATA["any"], b"\x01")
        b.uc.mem_write(da + DATA["m1"], b"\x5a" * 16)          # masks of an earlier frame: cleared
        sb = frame(b, held, mode, project=project, octs=[2] * 6, jumps=[4] * 6, da=da)
        if sa != sb or masks(b, da) != ([0] * 8, [0] * 8, 0):
            off.append((held, mode, project))
    reset(b, da)
    check(not off, "{}: without MACHINES, with FUNC or TRACK, in grid mode, with the selection armed, without a "
                   "project: the same states and calls as the stock frame, the masks cleared".format(key)
          + (f"; DIFFERENT {off}" if off else ""))


# --- 7. MACHINES on every track ---------------------------------------------------------------------------------------
def machines_tests(key, stock, w, wo):
    import test_shortcuts as SH
    tweak, info, img, runtime = w
    b = ui(img, runtime)
    sc = info["part"]["data_at"]
    sample = next((p["index"] for p in info["packages"] if p["id"] == "sampler"), None)
    machines = list(range(6)) + ([sample] if sample is not None else [])
    bad, n = [], 0
    for m in machines:
        for opened in (False, True):
            for used in (False, True):
                b.uc.mem_write(sc + PENDING, bytes(2))
                p = SH.mach(b, 1, m, opened)
                if used:
                    b.uc.mem_write(sc + USED, b"\x01")
                r = SH.mach(b, 0, m, opened)
                want = ["toggle"] if opened else ["taken", "pass" if used else "toggle"]
                got = [p[0]] if opened else [p[0], r[0]]
                n += 1
                if got != want or not (p[1] and (r[1] or opened)):
                    bad.append((m, opened, used, got))
        if SH.mach(b, 3, m, False)[0] != "browser":
            bad.append((m, "FUNC"))
    check(not bad, f"{key}: MACHINES on machines {machines}: a press that would open the list taken, the release opens "
                   "it unless +0x13 was marked; with the list open the press closes it; FUNC + MACHINES the PRESET "
                   f"browser ({n} cases)" + (f"; DIFFERENT {bad[:4]}" if bad else ""))
    if wo is not None:
        c = ui(wo[2], wo[3])
        stock_m = [SH.mach(c, 1, m, False)[0] for m in range(6)]
        check(stock_m == ["toggle"] * 6, f"{key}: the same build without Transpose: the stock machines still toggle the "
                                         f"list on the press ({stock_m})")


# --- 8. the dimming: the panel interrupt -------------------------------------------------------------------------------
DIM_LEDS, MID_LEDS, FULL_LEDS = (8, 11, 15), (9, 16), (12,)
PANEL_STATES = {8: 2, 9: 2, 11: 2, 12: 2, 15: 2, 16: 2, 1: 2, 2: 3, 5: 4, 13: 2, 14: 2}


def panel_rig(img, runtime=None, frozen=False):
    """test_trigless_dim.py's rig (the real panel interrupt, the port, PIT3's counter and the latches modelled; its
    start-up runs 0x4000045c, the copy of .data into the SRAM), the payload's memory mapped and the payload written
    there as the boot hook 0x400004b2, a routine of its own after it, leaves it (as mcengine.Engine does)."""
    import test_trigless_dim as TD

    class PRig(TD.Rig):
        def call(self, fn, *args, regs=None):
            if not getattr(self, "_pay", False):
                self._pay = True
                self.uc.mem_map(0x43000000, 0x00400000)
            return super().call(fn, *args, regs=regs)
    r = PRig(img, frozen)
    if runtime:
        r.uc.mem_write(0x43000000, bytes(runtime))
    return r


def set_masks(rig, da, n, on=True):
    table = rig.table
    m1, m2 = bytearray(8), bytearray(8)
    for leds, m in ((DIM_LEDS, m1), (MID_LEDS, m2)):
        for led in leds:
            m[table[led] >> 3] |= 1 << (table[led] & 7)
    rig.uc.mem_write(da + DATA["n"], bytes([n]))
    rig.uc.mem_write(da + DATA["m1"], bytes(m1) if on else bytes(8))
    rig.uc.mem_write(da + DATA["m2"], bytes(m2) if on else bytes(8))
    rig.uc.mem_write(da + DATA["any"], b"\x01" if on else b"\x00")


def panel_tests(key, stock, w):
    import collections
    import test_trigless_dim as TD
    tweak, info, img, runtime = w
    da, sc = info["transpose"]["data_at"], info["part"]["data_at"]
    probe = panel_rig(img, runtime)
    tr_led = int(tweak["symbols"]["tr_led"], 16)
    site = bytes(probe.uc.mem_read(LED_SITE[0], 10))
    check(probe.r32(da + DATA["sc"]) == sc and probe.uc.mem_read(da + DATA["n"], 1)[0] == DATA["n_value"]
          and site == bytes.fromhex(f"4ef9{tr_led:08x}4e714e71") and probe.r32(tr_led) != 0,
          f"{key}: the rig: the payload in memory (its data block at {da:#x} as composed, tr_led's code at "
          f"{tr_led:#x}), the LED step's jmp to it at {LED_SITE[0]:#x}")
    res = {}
    for name, im in (("stock", stock), ("build", img)):
        r = panel_rig(im, runtime if im is img else None)
        r.w32(TD.LED_OBJ, 0)                           # start-up: no LED object yet, no frame
        TD.timeline(r, 0.25, 3, {}, frames=False)
        nb = len(r.wlog)
        r.w32(TD.LED_OBJ, TD.OBJ)
        flips = [(0.40, lambda q: q.call(TD.FLIP, 8, 6)), (0.45, lambda q: q.call(TD.FLIP, 2, 42))]
        TD.timeline(r, 0.6, 7, PANEL_STATES, events=flips)
        res[name] = (r, nb)
    (a, na), (b, nb) = res["stock"], res["build"]
    check([x[1:] for x in a.wlog] == [x[1:] for x in b.wlog] and a.qlog == b.qlog and na == nb and len(a.wlog) > 10000
          and not (a.hazards or b.hazards or a.regfail or b.regfail or a.bad or b.bad),
          f"{key}: no mask: every write on the panel's port and every latched byte as the stock OS, start-up included "
          f"({len(a.wlog)} writes, {len(a.qlog)} changes); registers and stack back at every rte")
    for n in (4, 3):
        events = [(0.40, lambda q: q.call(TD.FLIP, 8, 6)),     # the running light on a dim key
                  (0.40, lambda q: q.call(TD.FLIP, 12, 6)),    # ... on a full one
                  (0.90, lambda q: q.call(TD.FLIP, 16, 42))]   # the stock blink's timer on a mid one
        out = {}
        for name, im in (("stock", stock), ("build", img)):
            r = panel_rig(im, runtime if im is img else None)
            if im is img:
                set_masks(r, da, n)
            end = TD.timeline(r, 1.5, 11, PANEL_STATES, events=events)
            out[name] = r
        a, b = out["stock"], out["build"]
        tag = f"{key}, a period of {n} ms"
        check(not (a.hazards or b.hazards or a.regfail or b.regfail or a.bad or b.bad) and a.isr_mem == b.isr_mem,
              f"{tag}: no hazard on the latches, registers and stack back at every rte, the interrupt writes the "
              "stock OS's memory as the stock OS (its own state lives in the payload)")
        other = lambda q: [(x[1], x[2], x[3]) for x in q.wlog if x[1] != 9]          # noqa: E731
        check(other(a) == other(b) and len(other(a)) > 15000,
              f"{tag}: the start, the key columns, LED steps 1 and 2: the stock writes, write for write")
        la, lb = TD.led0_writes(a), TD.led0_writes(b)
        ok, ks = len(la) == len(lb), collections.Counter()
        for x, y in zip(la, lb):
            k = (len(y) - 2) // 3
            ks[k] += 1
            ok &= len(x) == 2 and x[0][1:] == y[0][1:] == (0, 0xffff) and len(y) == 2 + 3 * k and k <= 3
            ok &= y[-1][1] == 2 and (x[1][2] & 0xff) == (y[-1][2] & 0xff)
            for i in range(k):
                d_, s_, c_ = y[1 + 3 * i:4 + 3 * i]
                ok &= d_[1] == 2 and not d_[2] & 9 and (d_[2] >> 5) & 7 in (3, 4, 5) and s_[1:] == (0xa, 8) \
                    and c_[1:] == (6, 0xfff7)
        check(ok, f"{tag}: LED step 0: stock [DIR, DATA]; the build [DIR, (DATA, SET 8, CLR 0xfff7) x k, DATA], k <= 3, "
                  f"only rows 3, 4, 5 out of their turn ({len(la)} steps, k: {dict(sorted(ks.items()))})")
        g = TD.gaps(b)
        check(g and min(g) >= TD.WAIT, f"{tag}: at least {TD.WAIT} counts of PIT3 between two writes of step 0 "
                                       f"(the least {min(g)})")
        table = a.table
        masked = {table[x] for x in DIM_LEDS + MID_LEDS}
        others = [bit for bit in range(56) if bit not in masked]
        check(all(TD.wave(a.qlog, x, end) == TD.wave(b.qlog, x, end) for x in others),
              f"{tag}: the {len(others)} other LED bits (TRIG 12 at full among them): the same values at the same "
              "instants as the stock OS")
        for leds, on_ in ((DIM_LEDS, 1), (MID_LEDS, 2)):
            allon, alloff, bad, dark = collections.Counter(), collections.Counter(), 0, []
            for led in leds:
                wa, wb = TD.wave(a.qlog, table[led], end), TD.wave(b.qlog, table[led], end)
                bad += sum(1 for t0, t1, lit in wb if lit and TD.lit_time(wa, t0, t1) != t1 - t0)
                for t0, t1, lit in wb[1:-1]:
                    if TD.lit_time(wa, t0 - 3 * TD.CYCLE, t1 + 3 * TD.CYCLE) == t1 - t0 + 6 * TD.CYCLE:
                        (allon if lit else alloff)[round((t1 - t0) / TD.CYCLE, 1)] += 1
                for t0, t1, lit in wa[1:-1]:
                    if not lit:
                        run = [(u0, u1) for u0, u1, l_ in wb if not l_ and u0 <= t0 and u1 >= t1]
                        dark.append(((t1 - t0) / TD.CYCLE, (run[0][1] - run[0][0]) / TD.CYCLE if run else None))
            what = "dim" if on_ == 1 else "mid"
            check(set(allon) == {float(on_)} and set(alloff) == {float(n - on_)} and sum(allon.values()) > 300
                  and bad == 0 and all(m is not None and o <= m <= o + 2 * n for o, m in dark),
                  f"{tag}: the {what} keys {leds}: lit {on_} cycle(s) of 1 ms, dark {n - on_} ({1000 / n:.0f} Hz, "
                  f"{on_}/{n}) in steady state ({dict(allon)}, {dict(alloff)}); never lit when the stock OS has them "
                  f"dark; the running light and the blink dark at least as long as on the stock OS "
                  f"({[(round(o, 1), round(m, 1)) for o, m in dark if m is not None]} cycles)")
        cost = [x for x in b.led0 if x[0]]
        print(f"     finding: {tag}: a step 0 with k rows loaded costs at most {max(x[2] for x in cost) / TD.F_BUS * 1e6:.1f} "
              f"us; {sum(x[2] for x in b.led0) / len(b.led0) / TD.F_BUS * 1e6:.1f} us a cycle on average while dimming")
    r = panel_rig(img, runtime)                         # the interrupts' latency
    set_masks(r, da, 4)
    end = TD.timeline(r, 1.0, 23, PANEL_STATES, lat_us=20.0, blinks=False)
    duty = {1: [], 2: []}
    table = r.table
    for leds, on_ in ((DIM_LEDS, 1), (MID_LEDS, 2)):
        for led in leds:
            w_ = TD.wave(r.qlog, table[led], end)
            duty[on_] += [TD.lit_time(w_, t, t + TD.F_BUS // 10) / (TD.F_BUS // 10)
                          for t in range(TD.F_BUS // 10, end - TD.F_BUS // 10, TD.F_BUS // 20)]
    g = TD.gaps(r)
    check(0.235 < min(duty[1]) and max(duty[1]) < 0.265 and 0.485 < min(duty[2]) and max(duty[2]) < 0.515
          and min(g) >= TD.WAIT and not r.hazards,
          f"{key}: interrupts 0 to 20 us late: dim {min(duty[1]):.3f}..{max(duty[1]):.3f}, mid {min(duty[2]):.3f}.."
          f"{max(duty[2]):.3f} of the light over every 100 ms; writes at least {min(g)} counts apart")
    r = panel_rig(img, runtime)                         # step 0 late: the counter reloads during the writes
    set_masks(r, da, 4)
    TD.timeline(r, 0.3, 29, PANEL_STATES, led0_lat=(80.0, 83.0), blinks=False)
    g, wrapped = TD.gaps(r), sum(1 for ws in TD.led0_writes(r) if len(ws) > 2 and
                                 (ws[-1][0] - r.phi3) // TD.P3 != (ws[0][0] - r.phi3) // TD.P3)
    check(min(g) >= TD.WAIT and wrapped > 20 and not r.hazards,
          f"{key}: step 0 80 to 83 us late: the counter reloaded during {wrapped} steps, the writes still at least "
          f"{min(g)} counts apart")
    r = panel_rig(img, runtime, frozen=True)            # a counter that stands still
    set_masks(r, da, 4)
    TD.timeline(r, 0.05, 31, PANEL_STATES)
    with_k = [x for x in r.led0 if x[0]]
    check(with_k and not r.regfail and all(x[3] == 3 * 64 * x[0] for x in with_k),
          f"{key}: PIT3's counter standing still: every step 0 ends, 64 reads a wait "
          f"({max(x[2] for x in with_k) / TD.F_BUS * 1e6:.0f} us modelled at most)")
    out = {}
    for name, im in (("stock", stock), ("build", img)):  # MACHINES let go: the masks cleared, the rows back
        r = panel_rig(im, runtime if im is img else None)
        if im is img:
            set_masks(r, da, 4)
        clear = [(0.3, lambda q: set_masks(q, da, 4, on=False))] if im is img else []
        end = TD.timeline(r, 0.6, 37, PANEL_STATES, events=clear, blinks=False)
        out[name] = (r, end)
    (a, end), (b, _) = out["stock"], out["build"]
    t_back = int(0.3 * TD.F_BUS) + 2 * TD.CYCLE      # the same timeline on both: the clear at 0.3 s, then 2 cycles

    def after(w_):
        return [(max(t0, t_back), t1, lit) for t0, t1, lit in w_ if t1 > t_back]
    back = all(after(TD.wave(a.qlog, bit, end)) == after(TD.wave(b.qlog, bit, end)) for bit in range(56))
    late = TD.led0_writes(b)[-50:]
    check(back and all(len(ws) == 2 for ws in late) and b.uc.mem_read(da + DATA["dirty"], 1)[0] == 0,
          f"{key}: the masks cleared (MACHINES let go): within 2 cycles every LED as on the stock OS, step 0 back to "
          "[DIR, DATA], no row left dimmed")


# --- 9. the pattern's reload ------------------------------------------------------------------------------------------
PAT_CASE = 0x4001c154                   # MainScreenView's PATTERN case (d3 the event)
PAT_STOPS = {0x4001cbee: "reloaded", 0x4001c618: "prompt", 0x4001c2a8: "taken"}
YES_CBS = (0x4001b858, 0x4002caa4)      # the prompt's answer (ctx, answer): 0 YES
CUR_PAT, OK_RET, FAIL_RET = 5, 1, 0x4012ff00
JUMPS0, OCTS0 = [1, 2, 3, 4, 2, 1], [2, -1, 0, 1, -2, 1]


def reload_hooks(ret):
    import test_shortcuts as SH
    return {0x400cfd0e: ("ui2", 0x93a20000), 0x4006a96c: ("current", CUR_PAT), SH.PROJECT: ("project", SH.PROJ),
            RELOAD: ("reload", ret), 0x4002c680: ("after", 0)}


def preset(u, da):
    """Jumps and octaves on every track before a reload: the data block as it was (None on the stock OS)."""
    if not da:
        return None
    reset(u, da)
    u.uc.mem_write(da + DATA["jump"], bytes(JUMPS0))
    u.uc.mem_write(da + DATA["oct"], bytes(o & 0xff for o in OCTS0))
    return bytes(u.uc.mem_read(da, DATA["size"]))


def after(u, da, before, ret):
    """The data block after the calls made: every jump 0 when the reload was called and answered reloaded (ret's
    byte), the rest as it was; without a call of the reload, nothing changed."""
    if not da:
        return True
    want = bytearray(before)
    if ret & 0xff and any(n == "reload" for n, _ in u.calls):
        want[DATA["jump"]:DATA["jump"] + 6] = bytes(6)
    return bytes(u.uc.mem_read(da, DATA["size"])) == bytes(want)


def pat_case(u, flags, ret, da=None):
    """MainScreenView's PATTERN case with an event of these flags: (where it goes, the calls, the data block right)."""
    import test_shortcuts as SH
    from unicorn import UC_HOOK_CODE
    import unicorn.m68k_const as mk
    before = preset(u, da)
    u.hooks = reload_hooks(ret)
    u.calls.clear()
    u.uc.mem_write(SH.EVENT, bytes(32))
    u.uc.mem_write(SH.EVENT + 16, struct.pack(">I", flags))
    vals = [0x5a5a0000 + i for i in range(len(SH.KEPT))]
    vals[SH.KEPT.index(mk.UC_M68K_REG_D3)], vals[SH.KEPT.index(mk.UC_M68K_REG_A2)] = SH.EVENT, SH.VIEW
    for r, v in zip(SH.KEPT, vals):
        u.uc.reg_write(r, v)
    u.uc.reg_write(mk.UC_M68K_REG_A7, t7.STACK - 0x400)
    u.bad.clear()
    got = []

    def stop(uc, addr, size, ud):
        if addr in PAT_STOPS:
            got.append(PAT_STOPS[addr])
            uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, stop)
    u.uc.emu_start(PAT_CASE, 0x90000000, count=200_000)
    u.uc.hook_del(h)
    calls = [(n, a[:5] if n == "reload" else ()) for n, a in u.calls]      # the others' stacks: not arguments
    return (got[0] if got else None), calls, after(u, da, before, ret) and not u.bad


def answer(u, cb, ans, ret, da=None):
    """The prompt's answer callback (ctx, answer): (the calls, the data block right, the stack and registers kept)."""
    import test_shortcuts as SH
    before = preset(u, da)
    u.hooks = reload_hooks(ret)
    u.calls.clear()
    vals = SH.sentinels(u)
    u.call(cb, 0x93a30000, ans)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals
    calls = [(n, a[:5] if n == "reload" else ()) for n, a in u.calls]      # the others' stacks: not arguments
    return calls, after(u, da, before, ret) and not u.bad, u.sp_ok and kept


def reload_tests(key, stock, w):
    import test_shortcuts as SH
    tweak, info, img, runtime = w
    da = info["transpose"]["data_at"]
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    a, b = ui(stock), ui(img, runtime)
    proj = SH.PROJ
    bad, n = [], 0
    for flags, where, args in ((0x12, "reloaded", (proj, 1, CUR_PAT, 1, 1)), (0x13, "reloaded", (proj, 1, CUR_PAT, 1, 1)),
                               (0x22, "prompt", None), (0x10, "taken", None), (0x02, "taken", None)):
        for ret in (OK_RET, FAIL_RET):
            ra, rb = pat_case(a, flags, ret), pat_case(b, flags, ret, da)
            n += 1
            reloads = [c[1] for c in rb[1] if c[0] == "reload"]
            if ra[0] != where or rb[0] != where or ra[1] != rb[1] or not (ra[2] and rb[2]) \
                    or reloads != ([args] if args else []):
                bad.append((hex(flags), ret, ra, rb))
    check(not bad, f"{key}: MainScreenView's PATTERN case: FUNC + PATTERN tapped reloads from the temp area (project, 1, "
                   f"pattern {CUR_PAT}, 1, 1), FUNC + PATTERN held opens the prompt, PATTERN alone neither; the same "
                   "calls as the stock OS; reloaded: every jump 0, the octaves and the rest of the data block kept; "
                   f"failed: nothing changed ({n} cases)" + (f"; DIFFERENT {bad[:3]}" if bad else ""))
    bad, n = [], 0
    for cb in YES_CBS:
        for ans in (0, 1):
            for ret in (OK_RET, FAIL_RET):
                ra, rb = answer(a, cb, ans, ret), answer(b, cb, ans, ret, da)
                reloads = [c[1] for c in rb[0] if c[0] == "reload"]
                n += 1
                if ra[0] != rb[0] or not (ra[1] and rb[1] and ra[2] and rb[2]) \
                        or reloads != ([(proj, 0, CUR_PAT, 1, 1)] if ans == 0 else []):
                    bad.append((hex(cb), ans, ret, ra, rb))
    check(not bad, f"{key}: the prompt's answer ({', '.join(map(hex, YES_CBS))}): YES reloads from the project (project, "
                   f"0, pattern {CUR_PAT}, 1, 1), NO does not; the same calls as the stock OS; reloaded: every jump 0, "
                   "the octaves and the rest kept; failed or NO: nothing changed; registers and stack kept "
                   f"({n} cases)" + (f"; DIFFERENT {bad[:3]}" if bad else ""))
    res = []
    for ret in (OK_RET, FAIL_RET, 0xabcd0001):
        before = preset(b, da)
        b.hooks = reload_hooks(ret)
        b.calls.clear()
        vals = SH.sentinels(b)
        d0 = b.call(syms["tr_reload"], proj, 1, CUR_PAT, 1, 0x101)
        kept = [b.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals
        calls = [(nm, x[:5]) for nm, x in b.calls]
        res.append((d0 & 0xffffffff) == ret and calls == [("reload", (proj, 1, CUR_PAT, 1, 0x101))] and kept and b.sp_ok
                   and after(b, da, before, ret) and not b.bad)
    check(all(res), f"{key}: tr_reload: the reload called once with its five arguments, its d0 returned whole "
                    f"({OK_RET:#x}, {FAIL_RET:#x}, 0xabcd0001), the jumps cleared on byte 1 only, d2-d7/a2-a6 and the "
                    f"stack kept ({res})")
    reset(b, da)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--dry", action="store_true", help="section 1 only (the builds, no Unicorn)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    builds = {}
    print("1. the build")
    for sel in SELECTIONS:
        key = "+".join(sel + ["transpose"])
        w = composed(stock, sel, True)
        wo = composed(stock, sel, False) if sel else None
        builds[key] = (w, wo)
        build_tests(key, stock, w, wo)
    if not args.dry:
        alone, with_sample = builds["transpose"][0], builds["sampler+transpose"]
        print("2. the keys")
        a, b = key_tests("transpose", stock, alone)
        da = alone[1]["transpose"]["data_at"]
        print("3. the keyboard's octave")
        kbt_tests("transpose", a, b, da)
        print("4. tr_pitch itself")
        pitch_unit_tests("transpose", b, {k: int(v, 16) for k, v in alone[0]["symbols"].items()}, da)
        print("5. the jumps on the audio path (seqrig)")
        audio_tests("transpose", stock, alone)
        print("6. the LEDs")
        led_tests("transpose", a, b, da)
        print("7. MACHINES on every track")
        machines_tests("transpose", stock, alone, None)
        machines_tests("sampler+transpose", stock, *with_sample)
        print("8. the dimming: the panel interrupt")
        panel_tests("transpose", stock, alone)
        print("9. the pattern's reload")
        reload_tests("transpose", stock, alone)
        reload_tests("sampler+transpose", stock, with_sample[0])
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
