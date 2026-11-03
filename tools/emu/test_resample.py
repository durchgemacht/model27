#!/usr/bin/env python3
"""Proof of the RESAMPLE recorder, step R1 (notes/79 §6, proofs 1 and 2, §9), on the OS's own code, through the
builder's part tools/machines/resample/.

For each selection (by default: the recorder alone; with sampler,smpfilter,digidelay; with crush,pots,cpu), on the
official OS 1.13:
  1. the build (no Unicorn, also with --dry): the audio function's call of the mixer (0x40059872, jsr 0x400567ba) ->
     jsr rs_mix; TransportView's toggle (0x40024482) -> rs_key; the key code accessor (0x4007240c) -> jmp rs_code;
     every other write as in the build without the recorder, but for the payload's boot; the payload the
     same parts at the same places, plus the recorder's code and data block after them; the data block: the take's
     buffer and its words, the ring, the sources' shifts as part.json gives them, the rest zero; the RAM claim
     (0x42800000..0x43000000) outside the payload, after the stock delay line (0x42400000..0x42800000) and before
     SAMPLE's pool; the tweaks that write other bytes at 0x40059872 or 0x4007240c among the computed conflicts;
  2. idle: the whole audio interrupt, block for block, from its body (0x40058ca0) through the call of the audio
     function (0x40059382), six stock machines playing with both sends up, on the build without the recorder (the
     stock OS for the recorder alone) and with it: after every block the SRAM, the voices, the mixer's state, the
     effects' lines, the eDMA's registers, the interrupt's frame, the payload outside the recorder, d0, d2-d7/a2-a7 and
     the EMAC the same in both, and exactly 7 instructions more a block (rs_mix's way to the mixer);
  3. recording: the same run, the recorder armed through its own rs_arm (START NOW, STOP RECORD) for a track, the main
     mix in stereo and in mono, and USB in stereo with a known input written where the interrupt reads USB
     (0x40fe4cf0): everything above the same as without the recorder, so that it changes nothing that sounds; the take,
     block for block, the track's buffer as the mixer receives it (0x80001858 + 128 t at 0x400567ba), the main bus
     as the mixer leaves it ({L, R}, or (L >> 1) + (R >> 1)), the USB input as the mixer copied it; its peak the
     largest magnitude; then rs_stop: taken with the next block;
  4. Trig Preview's trigger: the recorder armed for TRIG on a track, nothing playing, then the event Trig Preview
     sends for a held step, as drumkilla's code builds it (notes/34 §6.2): 0x400548ce(track, pattern, kit, step, 0, 0)
     with the step's condition at 0xFF and the track's probability at 100, its +12 at 2, 0x40092116(event). The blocks
     before it leave the recorder armed; the first block whose frame +16 has the track's bit is the one it starts in,
     and the take's first 32 frames are the track's buffer of that block, not silent; the same event on another
     track leaves it armed;
  5. SETTINGS + RECORD (step R2) on TransportView's own handler (0x4002439a), with the real key event and isKeyHeld:
     in the stock OS RECORD toggles GRID RECORDING with SETTINGS held or not, not with FUNC, not on a repeat; in the
     build RECORD alone as in the stock OS, with SETTINGS held the page opens and GRID RECORDING stays; the
     device's case (notes/79 §10.1): the key bitmap says SETTINGS is up but its press (or long hold), read by
     TransportView before RECORD's, opens the page, its release or tap does not; the key code accessor the same as
     the stock one for every event (d0, the other registers, the condition codes), SETTINGS's last bit 0 in set_held;
  6. the key scanner (test_trig_hold.py's bench: the real key interrupt, the scanner 0x4007fbde and the key clock):
     SETTINGS alone, a short press, released as a tap (flag bit 4, the settings menu); SETTINGS + RECORD, released
     without the tap and without a long hold (flag bit 5, the question to save the project); SETTINGS held alone, the
     long hold;
  7. the page (test_cpu.py's way, the OS's calls around it stubbed): one page by the stock constructor, its vtables
     the private copy with our nine entries, presented once, the settings at their first values; none twice, none at
     interrupt level 7 or without the view machinery; the destructors forget it; RECORD arms and is redrawn, its
     release kept, again idle; PAGE, the TRIG keys, SETTINGS, PLAY, STOP, PUNCH, PATTERN go to the stock view's
     dispatch with its answer (as the machine page passes them on to the views below, so that Trig Preview plays
     under the page); RETURN's tap and SETTINGS + RECORD (SETTINGS held in the bitmap or by its events) close it;
     PITCH steps SOURCE, DATA nothing, LFO SPEED the base's handler; the periodic method redraws while armed and when
     the state changed;
  8. the render into the OS's own Bitmap, pixel for pixel the mockup's screens (tools/emu/resample_screens.py, its
     three pixel fonts and coordinates) in nine states: idle (a track, MAIN stereo with TO Tn, USB), armed, recording
     (and clipped), taken (--show prints them; a screen that differs is printed with the mockup's).

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal. A few minutes (every instruction is counted
in part 2).

    python3 tools/emu/test_resample.py --cycles model-cycles_OS1.13.syx [--machines crush,pots] [--blocks 24] [--show]
    python3 tools/emu/test_resample.py --cycles model-cycles_OS1.13.syx --dry      # the builds only, without Unicorn
    python3 tools/emu/test_resample.py --cycles model-cycles_OS1.13.syx --keys     # and the key parts, quickly
"""
import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import test_sdvintage as T          # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

PART = compose.load_part("resample")
DATA = PART["data"]
SELECTIONS = [[], ["sampler", "smpfilter", "digidelay"], ["crush", "pots", "cpu"]]
MIX_SITE, MIXER = 0x40059872, 0x400567ba
KEY_SITE = 0x40024482                           # TransportView's toggle of GRID RECORDING (R2)
CODE_SITE = 0x4007240c                          # the key event's code accessor: SETTINGS's events (R2, notes/79 §10.1)
ISR_BODY, PROBE_SITE, AFTER = 0x40058ca0, 0x40059382, 0x40059388
TRACKS, BUS, USB_COPY, USB_IN = 0x80001858, 0x8000b990, 0x8000ba90, 0x40fe4cf0
BOOT_SITES = {0x400004b2, 0x400b1106, 0x4016cae8}   # the payload's boot: the hook, the stub's mask and its sprite
DELAY_LINE = (0x42400000, 0x42800000)
IDLE, ARMED, REC, TAKEN = range(4)
TRIG, LEVEL, NOW = range(3)
SILENT, LENGTH, RECORD = range(3)
END_RECORD = 3
BUILD_EV, SEND_EV = 0x400548ce, 0x40092116


def ids_of(sel):
    return [i for i in sel if i != "cpu"]


def composed(stock, sel, resample):
    ids = ids_of(sel)
    if not ids and "cpu" not in sel and not resample:
        return None
    tweak, info = compose.compose(stock, ids, cpu="cpu" in sel, resample=resample)
    patched, _ = build.apply_writes(stock, [tweak])
    runtime = build.payload_runtime(tweak, stock, None)
    return tweak, info, bytes(patched) + build.payload_image(tweak, runtime), runtime


def key_of(sel):
    return "+".join(sel + ["resample"])


# --- 1. the build -----------------------------------------------------------------------------------------------------
def build_tests(key, w, wo):
    tweak, info, _img, runtime = w
    ri = info["resample"]
    by = {x["off"] + compose.BASE: x for x in tweak["writes"]}
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    x = by.get(MIX_SITE)
    check(x is not None and x["old"] == PART["mix"]["stock"] and x["new"] == f"4eb9{syms['rs_mix']:08x}",
          f"{key}: {MIX_SITE:#x} jsr {MIXER:#x} -> jsr rs_mix ({syms['rs_mix']:#x})")
    x = by.get(KEY_SITE)
    check(x is not None and x["old"] == PART["key"]["stock"]
          and x["new"] == f"2f034eb9{syms['rs_key']:08x}588f" + "4e71" * 6,
          f"{key}: {KEY_SITE:#x} TransportView's two calls -> move.l d3,-(sp) ; jsr rs_key ({syms['rs_key']:#x}) ; "
          "addq.l #4,sp and six nops, the stock bra after them")
    x = by.get(CODE_SITE)
    check(x is not None and x["old"] == PART["code"]["stock"] and x["new"] == f"4ef9{syms['rs_code']:08x}",
          f"{key}: {CODE_SITE:#x} the key code accessor's movea.l 4(sp),a0 ; move.l 12(a0),d0 -> jmp rs_code "
          f"({syms['rs_code']:#x}), its rts unreached")
    sites = {MIX_SITE, KEY_SITE, CODE_SITE}
    if wo is None:
        others = set(by) - sites
        check(others == BOOT_SITES, f"{key}: nothing else written but the payload's boot ({sorted(map(hex, others))})")
    else:
        bw = {x["off"] + compose.BASE: x for x in wo[0]["writes"]}
        diff = sorted(a for a in set(by) | set(bw) if by.get(a) != bw.get(a))
        check(set(diff) <= sites | BOOT_SITES and not sites & set(bw),
              f"{key}: every other write as in the build without the recorder, but for the payload's boot "
              f"({len(by)} writes; differing {', '.join(map(hex, diff))})")
        pw = [json.dumps(p, sort_keys=True) for p in tweak["append"]["parts"]]
        pwo = [json.dumps(p, sort_keys=True) for p in wo[0]["append"]["parts"]]
        extra = [p for p in pw if p not in pwo]
        check(all(p in pw for p in pwo) and len(extra) == 1 and json.loads(extra[0])["dest"] == f"{ri['code_at']:#x}",
              f"{key}: the payload the same {len(pwo)} parts at the same places, plus the recorder's at "
              f"{ri['code_at']:#x}")
    at = ri["data_at"] - compose.gs.PAY_ALONE
    block = runtime[at:at + DATA["size"]]
    lo, hi = (int(v, 16) for v in PART["ram"])
    buf, cap, ring = struct.unpack_from(">III", block, 0)
    sh = PART["shift"]
    sample = next((p["index"] for p in info["packages"] if p["id"] == "sampler"), 0xff)
    rest = bytearray(block[15:])
    rest[DATA["sample"] - 15] = 0
    ok = (buf, cap, ring) == (lo + PART["ring_bytes"], (hi - lo - PART["ring_bytes"]) // 4, lo) \
        and block[12:15] == bytes([sh["track"], sh["main"], sh["usb"]]) and block[DATA["sample"]] == sample \
        and not any(rest) and syms["rs_data"] == ri["data_at"] and len(block) == DATA["size"]
    check(ok, f"{key}: the data block at {ri['data_at']:#x}: the take at {buf:#x}, {cap} words, the ring at {ring:#x}, "
              f"the shifts {sh['track']}/{sh['main']}/{sh['usb']}, SAMPLE's machine {sample:#x}, the rest zero")
    import test_compose as TC
    check(not (lo < info["end"] and info["pay"] < hi) and lo >= DELAY_LINE[1] and hi <= TC.POOL[0],
          f"{key}: the RAM claim {lo:#x}..{hi:#x} outside the payload ({info['pay']:#x}..{info['end']:#x}), after the "
          f"stock delay line, before SAMPLE's pool")
    for site in (MIX_SITE, CODE_SITE):
        takers = set()
        for f in compose.DEV.glob("*.json"):
            if f.name == "device.json":
                continue
            t = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(t, dict) and any(y["off"] + compose.BASE == site and y["new"] != by[site]["new"]
                                           for y in t.get("writes", [])):
                takers.add(t["id"])
        check(takers and takers <= set(tweak["conflicts"]),
              f"{key}: the {len(takers)} tweaks that take {site:#x} ({', '.join(sorted(takers)[:4])}"
              f"{', ...' if len(takers) > 4 else ''}) among its computed conflicts")


# --- the emulator -----------------------------------------------------------------------------------------------------
def rd(uc, va, fmt):
    return struct.unpack(fmt, bytes(uc.mem_read(va, struct.calcsize(fmt))))[0]


def words(uc, va, n):
    return list(struct.unpack(f">{n}i", bytes(uc.mem_read(va, 4 * n))))


class Side:
    """One build in the whole audio interrupt: test_cpu.py's run (the mixer, the effects and the output stage run),
    six stock machines at their defaults, both sends up, Track Level at its default."""

    def __init__(self, stock, name, img, runtime, tweak, play=True):
        import mcengine as E
        import seqrig as S
        import test_cpu as CP
        import test_fxslot as FX
        from unicorn import UC_HOOK_CODE
        from unicorn import m68k_const as mk

        class Rig(S.Rig):
            def _ret0(self, uc, addr, size, ud):
                if addr not in (0x40056f58, 0x40056ea8, MIXER):
                    super()._ret0(uc, addr, size, ud)

        self.S, self.mk, self.name, self.tweak = S, mk, name, tweak
        self.e = CP.engine(img, runtime, tweak)
        uc = self.uc = self.e.uc
        self.rig = rig = Rig(self.e, bpm=120)
        S.ensure_map(uc, 0x4a000000, 0x00800000)
        uc.mem_map(FX.FIX, 0x00100000)

        def dma_done(u, _a, _s, _d):
            v = struct.unpack(">H", bytes(u.mem_read(FX.DMA_STATUS, 2)))[0]
            u.mem_write(FX.DMA_STATUS, struct.pack(">H", v & ~0x10))
        uc.hook_add(UC_HOOK_CODE, dma_done, begin=FX.DMA_WAIT, end=FX.DMA_WAIT)
        descs = {}
        for i in range(76):
            o = g7.DESC + 0x38 * i - compose.BASE
            a_ = struct.unpack_from(">I", stock, o + 0x2c)[0] - compose.BASE
            descs[stock[a_:stock.index(b"\0", a_)].decode("latin1")] = dict(
                k=struct.unpack_from(">i", stock, o + 4)[0], default=struct.unpack_from(">h", stock, o + 18)[0])
        for t in range(6):
            m = E.MACH[("KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD")[t]]
            c, sh, sw, ct, d = E.DEFAULTS[m]
            for n_, v in (("machine", m), ("color", c), ("shape", sh), ("sweep", sw), ("contour", ct), ("decay", d),
                          ("pitch", 64), ("finetune", 64)):
                rig.param(t, E.SLOT[n_], int(round(v * 256)))
            for n_, v in (("Volume +Dist", descs["Volume +Dist"]["default"]), ("Pan", descs["Pan"]["default"]),
                          ("Delay Send", 127 << 8), ("Reverb Send", 100 << 8)):
                rig.param(t, descs[n_]["k"], v)
            lev = descs["Track Level"]["default"]
            uc.mem_write(S.TARGETS + 2 * t, struct.pack(">h", lev))
            uc.mem_write(S.SMOOTH + 4 * t, struct.pack(">i", lev << 16))
            uc.mem_write(S.PARAMS + 2 * t, struct.pack(">h", lev))
        if play:
            for t in range(6):
                rig.set_step(t, 0, vel=100)
                for k in range(8):
                    rig.schedule_step(t, 0, rig.now + (2 + 12 * k + 2 * t) * rig.blk)
        self.syms = {k: int(v, 16) for k, v in tweak["symbols"].items()} if tweak else {}
        self.usb = None
        self.n = 0
        self.snap_tracks, self.snap_bus, self.snap_usb = [], [], []
        self.UC_HOOK_CODE = UC_HOOK_CODE

        def at_mixer(u, _a, _s, _d):
            self.snap_tracks.append(words(u, TRACKS, 6 * 32))
        uc.hook_add(UC_HOOK_CODE, at_mixer, begin=MIXER, end=MIXER)
        if "rs_post" in self.syms:
            def at_post(u, _a, _s, _d):
                self.snap_bus.append(words(u, BUS, 64))
                self.snap_usb.append(words(u, USB_COPY, 64))
            uc.hook_add(UC_HOOK_CODE, at_post, begin=self.syms["rs_post"], end=self.syms["rs_post"])

    def block(self, count=False):
        """One audio block: the interrupt's body, then (with a USB input given) the input written where the interrupt
        has just read it, then the call of the audio function. Returns (its frame's triggered mask, instructions)."""
        uc, mk, S, rig = self.uc, self.mk, self.S, self.rig
        rig.w32(S.NOW, rig.now)
        fp0 = S.ISTACK - 4
        uc.reg_write(mk.UC_M68K_REG_A6, fp0)
        uc.reg_write(mk.UC_M68K_REG_A7, fp0 - 168)
        uc.reg_write(mk.UC_M68K_REG_D7, 0)
        uc.emu_start(ISR_BODY, PROBE_SITE, count=5_000_000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == PROBE_SITE, hex(uc.reg_read(mk.UC_M68K_REG_PC))
        trig = rd(uc, uc.reg_read(mk.UC_M68K_REG_A6) - 44 + 16, ">I")
        if self.usb is not None:
            uc.mem_write(USB_IN, struct.pack(">64i", *self.usb(len(rig.blocks))))
        rig.blocks.append(None)
        self.n = 0
        h = uc.hook_add(self.UC_HOOK_CODE, self._count) if count else None
        uc.emu_start(PROBE_SITE, AFTER, count=10_000_000)
        if h is not None:
            uc.hook_del(h)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == AFTER, hex(uc.reg_read(mk.UC_M68K_REG_PC))
        rig.now += rig.blk
        return trig, self.n

    def _count(self, _u, _a, _s, _d):
        self.n += 1

    def data(self, field, fmt=">I"):
        return rd(self.uc, self.syms["rs_data"] + DATA[field], fmt)

    def arm(self, src, stereo, start, stop, thr_db=40, seconds=40):
        self.e.call(self.syms["rs_arm"], src, stereo, start, stop, thr_db, seconds)

    def take(self):
        n = self.data("frames") * (2 if self.data("stereo", ">B") else 1)
        return words(self.uc, self.data("buf"), n) if n else []


REGS = ("D0", "D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6", "A7")


def compare(a, b, same, i, diff):
    """The memory, registers and EMAC of both sides after block i."""
    mk = a.mk
    sp = b.uc.reg_read(mk.UC_M68K_REG_A7)
    for lo, n in list(same) + [(sp, a.S.ISTACK - sp)]:
        x, y = bytes(a.uc.mem_read(lo, n)), bytes(b.uc.mem_read(lo, n))
        if x != y and len(diff) < 4:
            k = next(j for j in range(n) if x[j] != y[j])
            diff.append(f"block {i}: memory at {lo + k:#x}")
    ra = [a.uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in REGS]
    rb = [b.uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in REGS]
    if ra != rb and len(diff) < 4:
        diff.append(f"block {i}: registers {[hex(v) for v in ra]} / {[hex(v) for v in rb]}")
    if (a.e.emac.macsr, list(a.e.emac.acc)) != (b.e.emac.macsr, list(b.e.emac.acc)) and len(diff) < 4:
        diff.append(f"block {i}: the EMAC")


def same_regions(info, wo):
    import test_fxslot as FX
    ri = info["resample"]
    out = list(FX.EARLY_SAME)
    if wo:                                       # the payload outside the recorder
        out += [(compose.gs.PAY_ALONE, ri["code_at"] - compose.gs.PAY_ALONE),
                (ri["data_at"] + DATA["size"], info["end"] - ri["data_at"] - DATA["size"])]
    return out


def usb_input(i):
    return [((i * 64 + k) * 2654435761 % (1 << 31)) * (1 if k % 2 else -1) for k in range(64)]


# --- 2. idle, 3. recording --------------------------------------------------------------------------------------------
def interrupt_tests(key, stock, w, wo, blocks):
    tweak, info, img, runtime = w
    without = (wo[2], wo[3], wo[0]) if wo else (stock, None, None)
    same = same_regions(info, wo)
    a = Side(stock, "without", *without)
    b = Side(stock, "with", img, runtime, tweak)
    diff, extra = [], set()
    for i in range(blocks):
        _, na = a.block(count=True)
        _, nb = b.block(count=True)
        compare(a, b, same, i, diff)
        extra.add(nb - na)
    check(not diff and not a.e.unmapped and not b.e.unmapped,
          f"{key}: idle, {blocks} blocks of the whole audio interrupt: the same memory, registers and EMAC on both "
          "builds"
          + (f"; {'; '.join(diff)}" if diff else ""))
    check(extra == {7}, f"{key}: idle, {sorted(extra)} instruction(s) more a block (rs_mix's way to the mixer: 7)")

    cases = [("track 3", 2, 0), ("main, stereo", 6, 1), ("main, mono", 6, 0), ("USB, stereo", 7, 1)]
    for name, src, stereo in cases:
        a = Side(stock, "without", *without)
        b = Side(stock, "with", img, runtime, tweak)
        if src == 7:
            a.usb = b.usb = usb_input
        for _ in range(4):                          # the machines' first notes
            a.block()
            b.block()
        b.arm(src, stereo, NOW, RECORD)
        state = b.data("state", ">B")
        b.snap_tracks.clear()
        b.snap_bus.clear()
        b.snap_usb.clear()
        diff, costs = [], []
        for i in range(blocks):
            _, na = a.block(count=True)
            _, nb = b.block(count=True)
            compare(a, b, same, i, diff)
            costs.append(nb - na)
        if src < 6:
            want = sum((s[32 * src:32 * src + 32] for s in b.snap_tracks), [])
        else:
            snaps = b.snap_bus if src == 6 else b.snap_usb
            want = sum((s if stereo else [(s[2 * k] >> 1) + (s[2 * k + 1] >> 1) for k in range(32)] for s in snaps), [])
        got = b.take()
        peak = max((abs(v) for v in want), default=0)
        what = "track buffer at the mixer" if src < 6 else "bus after the mixer" if src == 6 else "USB input as copied"
        check(not diff and not b.e.unmapped,
              f"{key}, {name}: recording, {blocks} blocks: everything outside the recorder the same as without it"
              + (f"; {'; '.join(diff)}" if diff else ""))
        check(state == ARMED and b.data("state", ">B") == REC and got == want and any(want)
              and b.data("frames") == 32 * blocks and b.data("peak") == peak,
              f"{key}, {name}: the take, {b.data('frames')} frames, the {what} block for block, its peak {peak:#x}; "
              f"{min(costs)} to {max(costs)} instructions a block")
        b.e.call(b.syms["rs_stop"])
        b.block()
        check(b.data("state", ">B") == TAKEN and b.data("end", ">B") == END_RECORD
              and b.data("frames") == 32 * blocks + 32,
              f"{key}, {name}: rs_stop, taken with the next block ({b.data('frames')} frames)")


# --- 4. Trig Preview's trigger ----------------------------------------------------------------------------------------
def preview(side, t, step=0):
    """The event drumkilla's Trig Preview sends for a held step (notes/34 §6.2)."""
    S, rig, uc = side.S, side.rig, side.uc
    rig.set_step(t, step, vel=100)
    tr = S.PAT + 722 * t
    prob, cond = bytes(uc.mem_read(tr + 719, 1)), bytes(uc.mem_read(tr + 516 + step, 1))
    uc.mem_write(tr + 719, bytes([100]))
    uc.mem_write(tr + 516 + step, b"\xff")
    ev = side.e.call(BUILD_EV, t, S.PAT, S.KIT, step, 0, 0)
    uc.mem_write(tr + 516 + step, cond)
    uc.mem_write(tr + 719, prob)
    assert ev, "no event"
    rig.w32(ev + 12, 2)
    side.e.call(SEND_EV, ev)


def preview_tests(key, stock, w, t=2, other=4):
    tweak, info, img, runtime = w
    b = Side(stock, "with", img, runtime, tweak, play=False)
    for _ in range(3):
        b.block()
    b.arm(t, 0, TRIG, RECORD)
    before = []
    for _ in range(3):
        trig, _ = b.block()
        before.append((trig, b.data("state", ">B")))
    check(all(s == ARMED and not trig & 0x3f for trig, s in before), f"{key}: armed for TRIG on track {t + 1}, three "
                                                                     "silent blocks: still armed")
    preview(b, other)
    seen = []
    for _ in range(6):
        trig, _ = b.block()
        seen.append((trig, b.data("state", ">B")))
    hit = [trig for trig, _ in seen if trig >> other & 1]
    check(hit and all(s == ARMED for _, s in seen),
          f"{key}: Trig Preview's event on track {other + 1}: its bit in a block's frame +16 "
          f"({hit[0] if hit else 0:#x}), the recorder still armed")
    preview(b, t)
    b.snap_tracks.clear()
    at = None
    for i in range(6):
        trig, _ = b.block()
        if b.data("state", ">B") != ARMED:
            at = (i, trig)
            break
    started = at is not None and at[1] >> t & 1 and b.data("state", ">B") == REC and b.data("frames") == 32
    for _ in range(3):
        b.block()
    voice = [s[32 * t:32 * t + 32] for s in b.snap_tracks]
    i0 = at[0] if at else 0
    check(started and not any(sum(voice[:i0], [])) and b.take()[:128] == sum(voice[i0:i0 + 4], [])
          and any(b.take()[:128]),
          f"{key}: Trig Preview's event on track {t + 1}: the recorder starts in the block whose frame +16 has its bit "
          f"({at[1] if at else 0:#x}, block {at[0] if at else '-'} after the event), the track silent before it; the "
          f"take's first four blocks the track's buffer of those blocks, the note in them")


# --- 5. to 8.: SETTINGS + RECORD and the page (step R2, notes/79 §2, proofs 3 and 4) --------------------------------
TRANSPORT_KEY = 0x4002439a                      # TransportView::consumeKeyEvent (its vtable 0x40100fec, +8)
GRID_PREP, GRID_TOGGLE = 0x4006ba90, 0x4006ba20
UIS_PTR = 0x40fe4218
UIS_OBJ, TV_OBJ, FAKE, KIT_FAKE = 0x93c50000, 0x93c60000, 0x93c70000, 0x93c80000
SELECTED = 2                                    # the selected track the stubbed project gives (T3)
OURS = {0x08: "rs_dtor0", 0x0c: "rs_dtor1", 0x10: "rs_page_key", 0x18: "rs_page_render", 0x34: "rs_page_tick",
        0x4c: "rs_page_enc", 0x58: "rs_dtor0_th", 0x5c: "rs_dtor1_th", 0x60: "rs_enc_th"}
SETTINGS, RECORD_K, RETURN_K, FUNC_BIT, PRESS, TAP, REPEAT, LONG = 13, 9, 12, 0x02, 0x01, 0x10, 0x08, 0x20


def part_syms(info):
    """Every symbol of the recorder's object where the composer placed it, its local ones too."""
    import relocate
    roots = PART["build"]["roots"]
    lay = relocate.layout(compose.object_path(PART).read_bytes(), roots[0], roots[1], roots[2:], "resample")
    return {n: info["resample"]["code_at"] + off for n, (base, off) in lay["symbols"].items() if base == "code"}


def ui_of(img, runtime):
    """test_shortcuts.py's UI on the build (or the stock OS), with the selected track, the kit's working copy (zero:
    no track plays SAMPLE), the view machinery up and the page's OS calls stubbed as
    tools/emu/test_cpu.py stubs them."""
    import test_cpu as CP
    import test_shortcuts as SH
    u = SH.UI(img, runtime or b"")
    import seqrig as S
    S.ensure_map(u.uc, 0x80000000, 0x00010000)
    u.uc.mem_write(0x800017e4, struct.pack(">I", KIT_FAKE))
    u.uc.mem_write(UIS_PTR, struct.pack(">I", UIS_OBJ))
    u.uc.mem_write(UIS_OBJ, bytes(0x200))
    u.uc.mem_write(TV_OBJ, bytes(0x100))
    u.uc.mem_write(CP.VIEWS_UP, struct.pack(">I", CP.VIEWS_OBJ))
    u.seen = []
    u.base_hooks = {0x400cf866: ("project", FAKE), 0x4000eb90: ("pattern", FAKE), 0x40012412: ("track", SELECTED)}
    u.page_hooks = {CP.NEW: ("new", 0), CP.ALLOC: ("new", 0), CP.PAGE_CTOR: ("page ctor", 0),
                    CP.VIEWS: ("views", CP.VIEWS_OBJ), CP.PRESENT: ("present", 0), CP.DROP: ("drop", 0),
                    CP.DTOR0: ("dtor0", 0), CP.DTOR1: ("dtor1", 0), CP.CLOSE: ("close", 0),
                    CP.KEY_STOCK: ("keys", 0x77), CP.ENC_BASE: ("base", 0x66), CP.NEEDS_REDRAW: ("redraw", 0),
                    GRID_PREP: ("prep", 0), GRID_TOGGLE: ("toggle", 0), **u.base_hooks}
    u.hooks = dict(u.page_hooks)
    from unicorn import m68k_const as mk
    u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)          # the interface's thread
    return u


def event(u, code, flags, knob_delta=None):
    import test_cpu as CP
    v = knob_delta if knob_delta is not None else flags
    u.uc.mem_write(CP.EVENT, struct.pack(">5I", 0, 0, 0, code, v & 0xffffffff))
    return CP.EVENT


def named(u, name):
    return [a for c, a in u.calls if c == name]


def key_tests(key, stock, w):
    """5. The combination on TransportView's own handler, the stock OS and the build."""
    tweak, info, img, runtime = w
    ri = info["resample"]
    out = {}
    for name, im, rt in (("stock", stock, None), ("build", img, runtime)):
        rows = []
        for held, flags in ((False, PRESS), (True, PRESS), (False, PRESS | FUNC_BIT), (True, PRESS | REPEAT)):
            u = ui_of(im, rt)
            u.hold(SETTINGS, held)
            u.calls.clear()
            u.call(TRANSPORT_KEY, TV_OBJ, event(u, RECORD_K, flags))
            page = u.u32(ri["data_at"] + DATA["page"]) if rt else 0
            rows.append((len(named(u, "toggle")), len(named(u, "present")), bool(page), u.sp_ok and not u.bad))
        out[name] = rows
    check(out["stock"] == [(1, 0, False, True), (1, 0, False, True), (0, 0, False, True), (0, 0, False, True)],
          f"{key}: the stock OS: RECORD toggles GRID RECORDING with or without SETTINGS held (SETTINGS not read), not "
          f"with FUNC, not on a repeat ({out['stock']})")
    check(out["build"] == [(1, 0, False, True), (0, 1, True, True), (0, 0, False, True), (0, 0, False, True)],
          f"{key}: the build: RECORD alone toggles GRID RECORDING as in the stock OS; with SETTINGS held the page opens "
          f"instead and GRID RECORDING stays; FUNC + RECORD and a repeat as in the stock OS ({out['build']})")
    # the device's case (notes/79 §10.1): the key bitmap says SETTINGS is up, its events, read by TransportView before
    # RECORD's, say it is down (a press, its long hold) or up again (its release)
    out = {}
    for name, im, rt in (("stock", stock, None), ("build", img, runtime)):
        rows = []
        for before in ([PRESS], [PRESS | REPEAT | LONG], [PRESS, 0], [PRESS, TAP]):
            u = ui_of(im, rt)
            u.hold(SETTINGS, False)
            for flags in before:
                u.call(TRANSPORT_KEY, TV_OBJ, event(u, SETTINGS, flags))
            u.calls.clear()
            u.call(TRANSPORT_KEY, TV_OBJ, event(u, RECORD_K, PRESS))
            page = u.u32(ri["data_at"] + DATA["page"]) if rt else 0
            rows.append((len(named(u, "toggle")), len(named(u, "present")), bool(page), u.sp_ok and not u.bad))
        out[name] = rows
    check(out["stock"] == [(1, 0, False, True)] * 4,
          f"{key}: the stock OS, SETTINGS's events read before RECORD's: RECORD toggles GRID RECORDING "
          f"({out['stock']})")
    check(out["build"] == [(0, 1, True, True), (0, 1, True, True), (1, 0, False, True), (1, 0, False, True)],
          f"{key}: the build, the key bitmap's SETTINGS up: after SETTINGS's press or its long hold the page opens and "
          f"GRID RECORDING stays; after its release (or its tap) RECORD toggles GRID RECORDING ({out['build']})")
    accessor_tests(key, stock, w)


CAPTURE = 0x90000200                            # move.w sr,d7: a return that reads the condition codes on the CPU


def accessor_tests(key, stock, w):
    """5. The key code accessor (0x4007240c) in the build: the same d0, the other registers and the condition codes as
    the stock one for every event; SETTINGS's events kept in set_held (their bit 0), the others leave it. The condition
    codes are read by the CPU itself, the accessor returning into move.w sr,d7 (a second call of the same event):
    Unicorn's SR read after a run does not show the flags the last instruction set (the stock accessor's move.l, which
    clears V and C, reads back with the V and C written before it)."""
    import test_sdvintage_7th as t7
    from unicorn import m68k_const as mk
    _tweak, info, img, runtime = w
    held_at = info["resample"]["data_at"] + DATA["set_held"]
    regs = ([getattr(mk, f"UC_M68K_REG_D{i}") for i in range(1, 8)]
            + [getattr(mk, f"UC_M68K_REG_A{i}") for i in range(1, 7)])
    events = [(code, flags) for code in (0, 1, 9, 12, SETTINGS, 15, 16, 32, 0x7fffffff)
              for flags in (0, PRESS, PRESS | REPEAT, PRESS | REPEAT | LONG, TAP, PRESS | FUNC_BIT, 0xfffffffe)]
    sides = {}
    for name, im, rt in (("stock", stock, None), ("build", img, runtime)):
        u = ui_of(im, rt)
        u.uc.mem_write(CAPTURE, bytes.fromhex("40c74e714e71"))
        rows = []
        for code, flags in events:
            for i, r in enumerate(regs):
                u.uc.reg_write(r, 0x5a000000 + 0x1111 * i)
            u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000 | (code + flags) & 0x1f)
            d0 = u.call(CODE_SITE, event(u, code, flags))
            kept = [u.uc.reg_read(r) & 0xffffffff for r in regs]
            kept = [f"{r:#x}" for r, i in zip(kept, range(len(regs))) if r != 0x5a000000 + 0x1111 * i] or True
            held = u.uc.mem_read(held_at, 1)[0] if rt else None
            sp_ok, bad = u.sp_ok, sorted(map(hex, u.bad))
            u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000 | (code + flags) & 0x1f)
            sp = t7.STACK - 0x400
            u.uc.mem_write(sp, struct.pack(">II", CAPTURE, event(u, code, flags)))
            u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
            u.uc.emu_start(CODE_SITE, CAPTURE + 2)
            ccr = u.uc.reg_read(mk.UC_M68K_REG_D7) & 0x1f
            rows.append((d0 & 0xffffffff, kept, ccr, sp_ok, held, bad))
        sides[name] = rows
    want, held = [], 0
    for code, flags in events:
        held = flags & 1 if code == SETTINGS else held
        want.append(held)
    off = [(f"code {c:#x} flags {f:#x}", "stock (d0, kept, ccr, sp, -, bad)", a, "build", b, "set_held wanted", h)
           for (c, f), a, b, h in zip(events, sides["stock"], sides["build"], want)
           if a[:4] != b[:4] or b[1] is not True or not b[3] or b[4] != h or b[5]]
    check(not off,
          f"{key}: the key code accessor (jmp rs_code): for {len(want)} events the same code in d0, the condition "
          f"codes, d1-d7/a1-a6 and the stack as the stock one; set_held the bit 0 of SETTINGS's last event, the other "
          f"keys leave it" + (f" ({len(off)} events differ, the first: {off[:3]})" if off else ""))


def scanner_tests(key, stock):
    """6. The key scanner's events for SETTINGS (tools/emu/test_trig_hold.py's bench: the real key interrupt, the scanner
    0x4007fbde and the key clock), the same in the stock OS and every build (none of them touches it)."""
    import test_trig_hold as TH
    from unicorn import UC_HOOK_CODE

    def run(events, until):
        rig = TH.Rig(stock)
        # the events only: the bench hands each to PatternGridView, whose RECORD reaches memory it does not set up
        rig.uc.hook_add(UC_HOOK_CODE, rig._stub(lambda a: 0), begin=TH.GRID_KEY, end=TH.GRID_KEY)
        return [(t, kind, code, flags) for t, kind, code, flags in rig.run(events, until) if code == SETTINGS]
    tap = run({10: [(SETTINGS, True)], 60: [(SETTINGS, False)]}, 300)
    chord = run({10: [(SETTINGS, True)], 60: [(RECORD_K, True)], 120: [(RECORD_K, False)], 180: [(SETTINGS, False)]},
                400)
    held = run({10: [(SETTINGS, True)], 1600: [(SETTINGS, False)]}, 1700)
    rel = lambda log: [f for _t, k, _c, f in log if k == "relâché"]
    first_hold = next((t for t, _k, _c, f in held if f & 0x20), None)
    check(rel(tap) and rel(tap)[-1] & TAP and not any(f & 0x20 for *_x, f in tap),
          f"{key}: SETTINGS alone, a short press: its release is a tap (flag bit 4), which opens the settings menu "
          f"({[(t, hex(f)) for t, _k, _c, f in tap]})")
    check(rel(chord) and not rel(chord)[-1] & TAP and not any(f & 0x20 for *_x, f in chord),
          f"{key}: SETTINGS + RECORD: SETTINGS' release is no tap and no long hold came for it: the settings menu "
          f"stays shut, no question to save ({[(t, hex(f)) for t, _k, _c, f in chord]})")
    check(first_hold is not None,
          f"{key}: SETTINGS held alone: a long hold (flag bit 5) at {first_hold} ms on this bench's key clock (the "
          "question to save the project; on the machine after 1 s)")


def page_tests(key, w):
    """7. The page, function by function on the build's code, as test_cpu.py proves the CPU page's."""
    import test_cpu as CP
    from unicorn import m68k_const as mk
    tweak, info, img, runtime = w
    ri = info["resample"]
    at = ri["data_at"]
    ps = part_syms(info)
    u = ui_of(img, runtime)
    u.hold(SETTINGS, True)
    stock_vt = struct.unpack(f">{CP.VT_LEN // 4}I", u.uc.mem_read(CP.VT_SRC, CP.VT_LEN))
    u.calls.clear()
    u.call(TRANSPORT_KEY, TV_OBJ, event(u, RECORD_K, PRESS))
    page = u.u32(at + DATA["page"])
    vt = at + DATA["vt"]
    copy = struct.unpack(f">{CP.VT_LEN // 4}I", u.uc.mem_read(vt, CP.VT_LEN))
    want = tuple(ps[OURS[4 * i]] if 4 * i in OURS else v for i, v in enumerate(stock_vt))
    present = named(u, "present")
    settings = struct.unpack(">8B", u.uc.mem_read(at + DATA["src_set"], 8))
    check(page and named(u, "page ctor") == [named(u, "page ctor")[0]] and named(u, "page ctor")[0][0] == page
          and u.u32(page) == vt + 8 and u.u32(page + 4) == vt + 0x58 and copy == want and len(present) == 1
          and present[0][0] == CP.VIEWS_OBJ + 64 and settings == (SELECTED, TRIG, 40, 0, SILENT, 10, 0, 0)
          and u.sp_ok and not u.bad,
          f"{key}: SETTINGS + RECORD: one page of {CP.PAGE_SIZE:#x} bytes at {page:#x} by the stock constructor, its "
          f"vtables the private copy (the stock group but for its {len(OURS)} entries), presented once on the views' "
          f"screen; the settings at their first values (T{SELECTED + 1}, TRIG, -40 dB, mono, SILENT, 10 s)")
    again = []
    for sr, up in ((0x2000, True), (0x2700, True), (0x2000, False)):
        if not up:
            u.uc.mem_write(CP.VIEWS_UP, bytes(4))
        if again:
            u.uc.mem_write(at + DATA["page"], bytes(4))
        u.calls.clear()
        u.uc.reg_write(mk.UC_M68K_REG_SR, sr)
        u.call(TRANSPORT_KEY, TV_OBJ, event(u, RECORD_K, PRESS))
        again.append(len(named(u, "present")))
    u.uc.mem_write(CP.VIEWS_UP, struct.pack(">I", CP.VIEWS_OBJ))
    u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    u.call(TRANSPORT_KEY, TV_OBJ, event(u, RECORD_K, PRESS))
    page = u.u32(at + DATA["page"])
    check(again == [0, 0, 0] and page, f"{key}: no second page while one is up, none at interrupt level 7 or without "
                                       f"the view machinery; then it opens again ({again})")
    gone = []
    for off, stock_name, this in ((0x08, "dtor0", 0), (0x0c, "dtor1", 0), (0x58, "dtor0", 4), (0x5c, "dtor1", 4)):
        page = u.u32(at + DATA["page"])
        u.calls.clear()
        u.call(copy[off // 4], page + this)
        gone.append(u.u32(at + DATA["page"]) == 0 and [a[0] for a in named(u, stock_name)] == [page] and u.sp_ok)
        u.call(TRANSPORT_KEY, TV_OBJ, event(u, RECORD_K, PRESS))
    check(all(gone), f"{key}: each destructor (and its thunk from the +4 base) forgets the page and goes on to the "
                     f"stock one with it")
    page = u.u32(at + DATA["page"])
    k_ = copy[0x10 // 4]
    st = lambda: u.uc.mem_read(at + DATA["state"], 1)[0]
    rows = []
    u.hold(SETTINGS, False)
    u.calls.clear()
    rows.append((u.call(k_, page, event(u, RECORD_K, PRESS)), st(), len(named(u, "redraw"))))
    rows.append((u.call(k_, page, event(u, RECORD_K, 0)), st()))
    rows.append((u.call(k_, page, event(u, RECORD_K, PRESS)), st()))
    check(rows == [(1, ARMED, 1), (1, ARMED), (1, IDLE)],
          f"{key}: RECORD on the page: armed with the settings and redrawn, its release kept, again idle ({rows})")
    passed = []
    for code in (15, 16, 31, SETTINGS, 10, 11, 6, 3):
        u.calls.clear()
        d0 = u.call(k_, page, event(u, code, PRESS))
        passed.append(d0 == 0x77 and [a[:2] for a in named(u, "keys")] == [(page, 0x93c20000)])
    check(all(passed), f"{key}: PAGE, TRIG 1 and 16, SETTINGS, PLAY, STOP, PUNCH, PATTERN: the stock view's dispatch "
                       f"with the page and its answer, as the machine page passes them on to the views below ({passed})")
    u.call(k_, page, event(u, SETTINGS, 0))         # SETTINGS's release after its press above: set_held again 0
    u.calls.clear()
    tap = (u.call(k_, page, event(u, RETURN_K, 0)), len(named(u, "close")),
           u.call(k_, page, event(u, RETURN_K, TAP)), len(named(u, "close")))
    u.call(k_, page, event(u, RECORD_K, PRESS))
    armed = st()
    u.hold(SETTINGS, True)
    u.calls.clear()
    chord = (u.call(k_, page, event(u, RECORD_K, PRESS)), len(named(u, "close")), st())
    u.hold(SETTINGS, False)
    u.call(k_, page, event(u, RECORD_K, PRESS))
    u.call(k_, page, event(u, SETTINGS, PRESS))      # the device's case: the bitmap up, SETTINGS's press read
    u.calls.clear()
    by_event = (u.call(k_, page, event(u, RECORD_K, PRESS)), len(named(u, "close")), st())
    u.call(k_, page, event(u, SETTINGS, 0))
    check(tap == (1, 0, 1, 1) and armed == ARMED and chord == (1, 1, IDLE) and by_event == (1, 1, IDLE),
          f"{key}: RETURN's tap closes the page (its vtable's +0x28), without the flag only used; SETTINGS + RECORD "
          f"on the page drops the armed take and closes it, with SETTINGS held in the key bitmap or by its events "
          f"({tap}, {chord}, {by_event})")
    e_ = copy[0x4c // 4]
    src0 = u.uc.mem_read(at + DATA["src_set"], 1)[0]
    u.calls.clear()
    enc = [u.call(e_, page, event(u, 2, 0, 1)) & 0xff, u.uc.mem_read(at + DATA["src_set"], 1)[0],
           u.call(e_, page, event(u, 1, 0, 1)) & 0xff, u.call(e_, page, event(u, 10, 0, 1)) & 0xff,
           [a[:2] for a in named(u, "base")], u.call(copy[0x60 // 4], page + 4, event(u, 2, 0, -1)) & 0xff,
           u.uc.mem_read(at + DATA["src_set"], 1)[0]]
    check(enc == [1, (src0 + 1) % 8, 1, 0x66, [(page + 4, 0x93c20000)], 1, src0] and u.sp_ok,
          f"{key}: the encoder handler: PITCH steps SOURCE, DATA does nothing, LFO SPEED goes to the base's handler "
          f"with this + 4; its thunk from the +4 base the same ({enc})")
    t_ = copy[0x34 // 4]
    redraws = []
    for state in (ARMED, ARMED, IDLE, IDLE, TAKEN):
        u.uc.mem_write(at + DATA["state"], bytes([state]))
        u.calls.clear()
        u.call(t_, page)
        redraws.append(len(named(u, "redraw")))
    u.uc.mem_write(at + DATA["state"], bytes([IDLE]))
    check(redraws == [1, 1, 1, 0, 1], f"{key}: the periodic method: a redraw each call while armed, once when the "
                                      f"state changed ({redraws})")
    return u, copy, page


def render_tests(key, w, u, copy, page, show):
    """8. The render into the OS's own Bitmap (0x40070172), pixel for pixel the mockup's screens
    (tools/emu/resample_screens.py: its three pixel fonts and its coordinates), for nine states."""
    import resample_screens as RS
    import test_cpu as CP
    tweak, info, img, runtime = w
    at = info["resample"]["data_at"]
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    u.hooks = dict(u.base_hooks)
    u.call(CP.BMP_CTOR, CP.BMP, CP.W, CP.H, CP.FB, 0)
    r_ = copy[0x18 // 4]
    sample = u.uc.mem_read(at + DATA["sample"], 1)[0]
    kit_byte = KIT_FAKE + 0x1c + 100 * SELECTED + 38          # the selected track's machine (to_track_ok)
    wide = ("frames", "limit", "level", "thr", "peak")

    def draw(kit, **fields):
        u.uc.mem_write(kit_byte, bytes([kit]))
        for name, v in fields.items():
            u.uc.mem_write(at + DATA[name], v.to_bytes(4 if name in wide else 1, "big"))
        u.uc.mem_write(CP.FB, bytes([0xa5]) * (CP.W * CP.PITCH * 4))
        u.call(r_, page, CP.BMP)
        fb = bytes(u.uc.mem_read(CP.FB, CP.W * CP.PITCH * 4))
        return [[CP.lit(fb, x, r) for x in range(CP.W)] for r in range(CP.H)], u.sp_ok and not u.bad

    def down(level):
        return u.call(syms["rs_db"], level, 0) if level else 96
    yes = sample != 0xff                                    # TO Tn applies on a SAMPLE track of a build with SAMPLE
    cases = [
        ("idle, T3, LEVEL -40 dB", 0, dict(state=IDLE, src_set=SELECTED, start_set=LEVEL, thr_set=40, stereo_set=0,
                                           stop_set=SILENT, length_set=10, norm_set=0, to_track=0),
         lambda: RS.idle(SELECTED, LEVEL, 40, 0, SILENT, 10, 0, SELECTED, False, 0)),
        ("idle, MAIN stereo, NORM, TO T3", sample, dict(state=IDLE, src_set=6, start_set=TRIG, stereo_set=1,
                                                         stop_set=LENGTH, length_set=20, norm_set=1, to_track=1),
         lambda: RS.idle(6, TRIG, 40, 1, LENGTH, 20, 1, SELECTED, yes, 1)),
        ("idle, USB (TRIG as LEVEL)", sample, dict(state=IDLE, src_set=7, start_set=TRIG, thr_set=60, stereo_set=0,
                                                   stop_set=RECORD, length_set=40, norm_set=0, to_track=0),
         lambda: RS.idle(7, LEVEL, 60, 0, RECORD, 40, 0, SELECTED, yes, 0)),
        ("armed, MAIN stereo, LEVEL", 0, dict(state=ARMED, src=6, stereo=1, start=LEVEL, stop=SILENT, limit=480000,
                                              level=0x08000000, thr_set=40),
         lambda: RS.armed(6, 1, LEVEL, SILENT, 480000, 40, down(0x08000000))),
        ("armed, T3, TRIG, its length", 0, dict(state=ARMED, src=SELECTED, stereo=0, start=TRIG, stop=LENGTH,
                                                limit=480000, level=0),
         lambda: RS.armed(SELECTED, 0, TRIG, LENGTH, 480000, 40, 96)),
        ("recording, 2.4 s of 10", 0, dict(state=REC, src=SELECTED, stereo=0, frames=115200, limit=480000,
                                           stop=LENGTH, level=0x02000000, peak=0x10000000),
         lambda: RS.recording(115200, 480000, LENGTH, False, down(0x02000000))),
        ("recording, 12 s, clipped", 0, dict(state=REC, src=6, stereo=1, frames=600000, limit=960000, stop=SILENT,
                                             level=0x7fffffff, peak=0x80000000),
         lambda: RS.recording(600000, 960000, SILENT, True, down(0x7fffffff))),
        ("taken, mono", 0, dict(state=TAKEN, frames=115200, stereo=0), lambda: RS.taken(115200, 0)),
        ("taken, stereo", 0, dict(state=TAKEN, frames=96000, stereo=1), lambda: RS.taken(96000, 1)),
    ]
    for name, kit, fields, model in cases:
        got, ok = draw(kit, **fields)
        want = model()
        off = [(x, r) for r in range(CP.H) for x in range(CP.W) if got[r][x] != want[r][x]]
        if show or off:
            print(f"  -- {name}: the device\n" + RS.ascii(got))
            if off:
                print(f"  -- {name}: the mockup\n" + RS.ascii(want))
        check(ok and not off, f"{key}: the render, {name}: pixel for pixel the mockup's screen"
                              + (f" ({len(off)} pixels differ, the first {off[:6]})" if off else ""))
    u.uc.mem_write(at + DATA["state"], bytes([IDLE]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--machines", help="one selection instead of the default ones, comma-separated (cpu: the CPU page)")
    ap.add_argument("--blocks", type=int, default=24)
    ap.add_argument("--dry", action="store_true", help="the builds only, without Unicorn")
    ap.add_argument("--show", action="store_true", help="print the page's screens as the render draws them")
    ap.add_argument("--keys", action="store_true", help="the build and the key parts only (5 to 7), without the audio")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    sels = [[i for i in args.machines.split(",") if i]] if args.machines is not None else SELECTIONS
    for sel in sels:
        key = key_of(sel)
        print(key)
        w = composed(stock, sel, True)
        wo = composed(stock, sel, False)
        build_tests(key, w, wo)
        if args.dry:
            continue
        if not args.keys:
            interrupt_tests(key, stock, w, wo, args.blocks)
            preview_tests(key, stock, w)
        key_tests(key, stock, w)
        u, copy, page = page_tests(key, w)
        render_tests(key, w, u, copy, page, args.show)
    if not args.dry:
        scanner_tests("the stock OS", stock)
    import test_sdvintage_7th as t7
    fails = t7.FAIL if hasattr(t7, "FAIL") else []
    print("\nALL OK" if not fails else f"\n{len(fails)} FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
