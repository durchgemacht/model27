#!/usr/bin/env python3
"""Proof of the RESAMPLE recorder, step R1 (notes/79 §6, proofs 1 and 2, §9), on the OS's own code, through the
builder's part tools/machines/resample/.

For each selection (by default: the recorder alone; with sampler,smpfilter,digidelay; with crush,pots,cpu), on the
official OS 1.13:
  1. the build (no Unicorn, also with --dry): the audio function's call of the mixer (0x40059872, jsr 0x400567ba) ->
     jsr rs_mix; every other write as in the build without the recorder, but for the payload's boot; the payload the
     same parts at the same places, plus the recorder's code and data block after them; the data block: the take's
     buffer and its words, the ring, the sources' shifts as part.json gives them, the rest zero; the RAM claim
     (0x42800000..0x43000000) outside the payload, after the stock delay line (0x42400000..0x42800000) and before
     SAMPLE's pool; the tweaks that write other bytes at 0x40059872 among the computed conflicts;
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
     track leaves it armed.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal. A few minutes (every instruction is counted
in part 2).

    python3 tools/emu/test_resample.py --cycles model-cycles_OS1.13.syx [--machines crush,pots] [--blocks 24]
    python3 tools/emu/test_resample.py --cycles model-cycles_OS1.13.syx --dry      # the builds only, without Unicorn
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
    if wo is None:
        others = set(by) - {MIX_SITE}
        check(others == BOOT_SITES, f"{key}: nothing else written but the payload's boot ({sorted(map(hex, others))})")
    else:
        bw = {x["off"] + compose.BASE: x for x in wo[0]["writes"]}
        diff = sorted(a for a in set(by) | set(bw) if by.get(a) != bw.get(a))
        check(set(diff) <= {MIX_SITE} | BOOT_SITES and MIX_SITE not in bw,
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
    ok = (buf, cap, ring) == (lo + PART["ring_bytes"], (hi - lo - PART["ring_bytes"]) // 4, lo) \
        and block[12:15] == bytes([sh["track"], sh["main"], sh["usb"]]) and not any(block[15:]) \
        and syms["rs_data"] == ri["data_at"]
    check(ok, f"{key}: the data block at {ri['data_at']:#x}: the take at {buf:#x}, {cap} words, the ring at {ring:#x}, "
              f"the shifts {sh['track']}/{sh['main']}/{sh['usb']}, the rest zero")
    import test_compose as TC
    check(not (lo < info["end"] and info["pay"] < hi) and lo >= DELAY_LINE[1] and hi <= TC.POOL[0],
          f"{key}: the RAM claim {lo:#x}..{hi:#x} outside the payload ({info['pay']:#x}..{info['end']:#x}), after the "
          f"stock delay line, before SAMPLE's pool")
    takers = set()
    for f in compose.DEV.glob("*.json"):
        if f.name == "device.json":
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(t, dict) and any(y["off"] + compose.BASE == MIX_SITE and y["new"] != by[MIX_SITE]["new"]
                                       for y in t.get("writes", [])):
            takers.add(t["id"])
    check(takers and takers <= set(tweak["conflicts"]),
          f"{key}: the {len(takers)} tweaks that take {MIX_SITE:#x} ({', '.join(sorted(takers)[:4])}"
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--machines", help="one selection instead of the default ones, comma-separated (cpu: the CPU page)")
    ap.add_argument("--blocks", type=int, default=24)
    ap.add_argument("--dry", action="store_true", help="the builds only, without Unicorn")
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
        interrupt_tests(key, stock, w, wo, args.blocks)
        preview_tests(key, stock, w)
    import test_sdvintage_7th as t7
    fails = t7.FAIL if hasattr(t7, "FAIL") else []
    print("\nALL OK" if not fails else f"\n{len(fails)} FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
