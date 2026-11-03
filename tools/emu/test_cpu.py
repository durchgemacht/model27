#!/usr/bin/env python3
"""Proof of the CPU page (notes/78: the measure, step 1 of §6, the row and the page, step 2) on the OS's own code,
through the builder's part tools/machines/cpu/ and, for the shares it reads, the filter slot (tools/machines/fltslot/)
and the effect slots' timer (tools/machines/fxslot/, since its 0.7).

For each selection (by default: the CPU page alone; with crush; with pots; with crush,pots; with
sampler,smpfilter,digidelay), on the official OS 1.13:
  1. the build (no Unicorn, also with --dry): the audio interrupt's call of the audio function (0x40059382,
     jsr 0x4005979e) -> jsr cpu_probe, the end of the device configuration list's constructor (0x40032aee, movem.l
     24(sp),d2-d6/a2-a6) -> jmp cpu_cfg; every other write as in the build without the CPU page, but for the payload's
     boot; the payload the same parts at the same places, plus the CPU page's code and data block after them; the
     data block: the address of the filter slot's last average (fl_data + avg_t) and of the effect slots' running
     ticks (fx_data + busy), each 0 when the build has not that part, the rest zero; the tweaks that write other bytes
     at 0x40059382 (the Syntakt engines, syntakt-meter, the governor) or 0x40032aee (Model-TG) among the computed
     conflicts;
  2. start-up: the bootstrap's own aPLib depacker reads the grown OS back; the boot hook copies the payload and clears
     the BSS;
  3. the probe, called as the interrupt calls the audio function, with a stand-in audio function that records what it
     sees and the DMA timer 0 simulated (each read half a block later): the stand-in sees its argument and the stack
     exactly as from the call replaced, d0 comes back from it, d2-d7/a2-a6 are kept, and each block is counted (its
     busy ticks, the window's sum, its dearest block, the top);
  4. the window (cpu_block, called as the probe calls it): 749 blocks at half a block and one at 90 %, then the
     window's end: the average and the peak in tenths of a percent of a block, the Track FX' share copied from the
     filter slot's last average, the effect slots' share from the difference of their running ticks over the window
     (also across the counter's wrap), the window cleared and counted; a second window after the top was cleared (as
     the page clears it when it opens): its own top; a block of more than 46 blocks counted as 46; a build without
     Track FX or effects: their shares stay 0;
  5. the whole audio interrupt, block for block, on the build without the CPU page (the stock OS for the CPU page
     alone) and on the build with it, from the interrupt's body (0x40058ca0) through the call at 0x40059382 (the
     voices, Volume + Dist and the Track FX, the mix, the effects, the output stage), six tracks playing, Crush on
     three of them and POTS in the delay slot for a while when the build has them; the timer simulated as the count
     of the OS's and the other parts' instructions (the CPU page's own instructions not counted, so that both builds
     read the same times): after every block the SRAM, the voices, the mixer's state, the effects' lines, the eDMA's
     registers, the interrupt's frame, the payload outside the CPU page (the filter slot's and the effect slots' data
     blocks with their measures included), d0, d2-d7/a2-a7 and the EMAC the same in both, the same number of
     instructions; the CPU page's busy ticks each block the audio function's instructions (the block's count less the
     call), its sum and count of blocks growing by them; the effect slots' running ticks growing by the ticks
     between their two reads around each slot's run, the filter slot's own sum by its; both inside the CPU page's;
  6. the row: the device configuration list's own constructor (0x40032726), the calls it makes but the closures'
     allocations stubbed, on the stock OS and on the build: four rows added to the list in the stock OS, five in the
     build, the fifth the item built from the row's four closures (the generic manager with the label cpu_lab, the
     manager with an argument with the press cpu_press and the list as its argument, cpu_nop for the value and the
     turn, -1 and 8 as the stock rows), the four closures let go after it; d2-d7/a2-a6 and the stack back as the
     constructor leaves them; the label "CPU" written into the string the list gives (0x400f980c), its pointer back;
  7. the page: the row's press (cpu_press), on the interface's thread with the view machinery up: one page of 0xd0
     bytes built by the stock machine-select constructor, its first two vtable pointers the private copy's (+0x08,
     +0x58), the copy the stock group 0x40117918..0x401179c8 but for its nine entries (the destructors and their +4
     thunks, the key handler, the render, the periodic method, the encoder handler and its thunk), presented once on
     the views' screen (0x400d0974() + 64) with the page and a reference holder {0x401000c4, 1, 1, page} and the holder
     let go, the top cleared (PEAK counts from the opening) and the windows ended noted; no second
     page while it is up, none at an interrupt level above 0 or without the view machinery; each destructor (and its
     thunk from the +4 base) forgets the page and goes on to the stock one with the page, after which the row opens a
     page again; the key handler: Return with its flag closes the page (its vtable's +0x28) and is used, Return
     without the flag only used, any other key the stock view's dispatch (0x40075f3c) with its answer; the encoder
     handler (and its thunk): DATA's turn used and nothing else, any other knob the base's handler 0x4006fb90 with
     this + 4, its answer; the periodic method (+0x2c, the stock page's an empty rts): the page's redraw
     (0x40076082) once a window has ended since the last, none otherwise, and the OS's own timer pass over the view
     stack (0x400778e2, its lock and unlock stubbed) on a screen holding the page calls it;
  8. the render, into the OS's own Bitmap (0x40070172), for known values: the screen cleared, the bar's outline rows
     12 and 16 and sides x 2 and 125, filled from x 3 as far as the average (122 pixels at 100 %, capped there), the
     mark at 85 % (x 106) two rows above and below it, the four lines' label and value in their rows and nothing lit
     elsewhere; other values another bar and other values, the same labels; "--" without Track FX or effects.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal. A few minutes, most of them the whole
interrupt's blocks (every instruction is counted).

    python3 tools/emu/test_cpu.py --cycles model-cycles_OS1.13.syx [--machines crush,pots] [--blocks 40] [--show]
    python3 tools/emu/test_cpu.py --cycles model-cycles_OS1.13.syx --dry      # the builds only, without Unicorn
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
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

PART = compose.load_part("cpu")
DATA = PART["data"]
FL_DATA = compose.load_part("fltslot")["data"]
FX_DATA = compose.load_part("fxslot")["data"]
SELECTIONS = [[], ["crush"], ["pots"], ["crush", "pots"], ["sampler", "smpfilter", "digidelay"]]
PROBE_SITE, AFTER, AUDIO = 0x40059382, 0x40059388, 0x4005979e
ROW_SITE, CFG_CTOR = 0x40032aee, 0x40032726     # the end of the device configuration list's constructor; the constructor
SITES = {PROBE_SITE: ("4eb94005979e", "4eb9", "cpu_probe"), ROW_SITE: ("4cef7c7c0018", "4ef9", "cpu_cfg")}
ISR_BODY = 0x40058ca0
TIMER = 0xfc07000c
BLOCK = 90112                                   # ticks a block (notes/23 §5)
WINDOW, WINDOW_TICKS, TOP_TICKS = 750, 67584, 0x00400000
BOOT_SITES = {0x400004b2, 0x400b1106, 0x4016cae8}   # the payload's boot: the hook, the stub's mask and its sprite
SEEN = 0x93000000                               # where the stand-in audio function writes what it sees
# lea 0x93000000,a0 ; move.l 4(sp),(a0)+ ... 16(sp) ; move.l sp,(a0)+ ; move.l #0x1234,d0 ; rts (test_meter.py's)
STAND_IN = bytes.fromhex("41f99300000020ef000420ef000820ef000c20ef001020cf203c000012344e75")
CRUSH_TRACKS = (0, 2, 4)
POTS_FROM, POTS_TO = 8, 26                      # the blocks in which the playing pattern chooses POTS


def share(ticks):
    """cpu.c's share(): ticks as tenths of a percent of a block, past TOP_TICKS as TOP_TICKS."""
    return min(min(ticks, TOP_TICKS) * 125 // 11264, 0xffff)


def part_syms(info):
    """Every symbol of the CPU page's object where the composer placed it, its local ones too."""
    import relocate
    roots = PART["build"]["roots"]
    lay = relocate.layout(compose.object_path(PART).read_bytes(), roots[0], roots[1], roots[2:], "cpu")
    return {n: info["cpu"]["code_at"] + off for n, (base, off) in lay["symbols"].items() if base == "code"}


def ids_of(sel):
    return "+".join(sel + ["cpu"])


def composed(stock, sel, cpu):
    tweak, info = compose.compose(stock, sel, cpu=cpu)
    patched, _ = build.apply_writes(stock, [tweak])
    runtime = build.payload_runtime(tweak, stock, None)
    return tweak, info, bytes(patched) + build.payload_image(tweak, runtime), runtime


# --- 1. the build -----------------------------------------------------------------------------------------------------
def build_tests(key, stock, sel, w, wo):
    tweak, info, _img, runtime = w
    ci = info["cpu"]
    by = {x["off"] + compose.BASE: x for x in tweak["writes"]}
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    ps = part_syms(info)
    for va, (old, op, name) in SITES.items():
        w = by.get(va)
        check(w is not None and w["old"] == old and w["new"] == op + f"{ps[name]:08x}",
              f"{key}: {va:#x} {old} -> {op} {name} ({ps[name]:#x})")
    if wo is None:
        others = set(by) - set(SITES)
        check(others == BOOT_SITES, f"{key}: nothing else written but the payload's boot ({sorted(map(hex, others))})")
    else:
        bw = {x["off"] + compose.BASE: x for x in wo[0]["writes"]}
        diff = sorted(a for a in set(by) | set(bw) if by.get(a) != bw.get(a))
        check(set(diff) <= set(SITES) | BOOT_SITES and not set(SITES) & set(bw),
              f"{key}: every other write as in the build without the CPU page, but for the payload's boot "
              f"({len(by)} writes; differing {', '.join(map(hex, diff))})")
        pw = [json.dumps(p, sort_keys=True) for p in tweak["append"]["parts"]]
        pwo = [json.dumps(p, sort_keys=True) for p in wo[0]["append"]["parts"]]
        extra = [p for p in pw if p not in pwo]
        parts_ok = all(p in pw for p in pwo) and len(extra) == 1 and json.loads(extra[0])["dest"] == f"{ci['code_at']:#x}"
        check(parts_ok, f"{key}: the payload the same {len(pwo)} parts at the same places, plus the CPU page's at "
                        f"{ci['code_at']:#x}")
    at = ci["data_at"] - compose.gs.PAY_ALONE
    block = runtime[at:at + DATA["size"]]
    fl, fx = info["filters"], info["fx"]
    want_fl = syms["fl_data"] + FL_DATA["avg_t"] if fl else 0
    want_fx = syms["fx_data"] + FX_DATA["busy"] if fx else 0
    got = struct.unpack_from(">II", block, 0)
    check(got == (want_fl, want_fx) and not any(block[8:]) and syms["cpu_data"] == ci["data_at"]
          and runtime[syms["cpu_probe"] - compose.gs.PAY_ALONE:][:2] == b"\x23\xdf",
          f"{key}: the data block at {ci['data_at']:#x}: the Track FX' load at {got[0]:#x}"
          f"{' (none)' if not fl else ''}, the effect slots' ticks at {got[1]:#x}{' (none)' if not fx else ''}, "
          "the rest zero")
    takers = {va: set() for va in SITES}
    for f in compose.DEV.glob("*.json"):
        if f.name == "device.json":
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        for va in SITES:
            if isinstance(t, dict) and any(x["off"] + compose.BASE == va and x["new"] != by[va]["new"]
                                           for x in t.get("writes", [])):
                takers[va].add(t["id"])
    every = takers[PROBE_SITE] | takers[ROW_SITE]
    check(takers[PROBE_SITE] and takers[ROW_SITE] and every <= set(tweak["conflicts"]),
          f"{key}: the {len(takers[PROBE_SITE])} tweaks that take 0x40059382 (the Syntakt engines, syntakt-meter, ...) "
          f"and the {len(takers[ROW_SITE])} that take 0x40032aee ({', '.join(sorted(takers[ROW_SITE]))}) among its "
          f"computed conflicts" + (f"; missing {sorted(every - set(tweak['conflicts']))[:4]}"
                                    if not every <= set(tweak["conflicts"]) else ""))


# --- the emulator -----------------------------------------------------------------------------------------------------
def engine(img, runtime=None, tweak=None):
    import mcengine as E
    import test_compose as TC
    if runtime is None:
        return E.Engine(img)
    e = E.Engine(img, payload=(E.PAYLOAD_DST, runtime), payload_code=TC.code_ranges(tweak))
    e.uc.mem_map(TC.POOL[0], TC.POOL[1] - TC.POOL[0])
    return e


def rd(uc, va, fmt):
    return struct.unpack(fmt, bytes(uc.mem_read(va, struct.calcsize(fmt))))[0]


def state(uc, at):
    names = ("ret", "t0", "sum", "peak", "top", "fx_last")
    out = dict(zip(names, struct.unpack(">6I", bytes(uc.mem_read(at + DATA["ret"], 24)))))
    out.update(zip(("n", "avg", "win_peak", "top_t", "trackfx", "effects", "windows"),
                   struct.unpack(">7H", bytes(uc.mem_read(at + DATA["n"], 14)))))
    return out


# --- 3. the probe ----------------------------------------------------------------------------------------------------
def probe_tests(key, w):
    import mcengine as E
    from unicorn import UC_HOOK_MEM_READ
    from unicorn import m68k_const as mk
    tweak, info, img, runtime = w
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    e = engine(img, runtime, tweak)
    uc = e.uc
    clock = [5_000_000]

    def tick(u, access, addr, size, value, ud):
        clock[0] += BLOCK // 2
        u.mem_write(TIMER, struct.pack(">I", clock[0] & 0xffffffff))
    uc.hook_add(UC_HOOK_MEM_READ, tick, begin=TIMER, end=TIMER + 3)
    uc.mem_map(SEEN, 0x1000)
    uc.mem_write(AUDIO, STAND_IN)
    kept = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")]
    ok = True
    for b in range(3):
        sp = E.STACK - 0x100
        frame = struct.pack(">5I", E.STOP, 0x11111111 + b, 0x22222222, 0x33333333, 0x44444444)
        uc.mem_write(sp, frame)
        uc.reg_write(mk.UC_M68K_REG_A7, sp)
        vals = [0x5a5a0000 + i for i in range(len(kept))]
        for r, v in zip(kept, vals):
            uc.reg_write(r, v)
        uc.emu_start(syms["cpu_probe"], E.STOP, count=100_000)
        seen = struct.unpack(">5I", bytes(uc.mem_read(SEEN, 20)))
        ok &= uc.reg_read(mk.UC_M68K_REG_PC) == E.STOP
        ok &= seen[:4] == struct.unpack(">4I", frame[4:]) and seen[4] == sp           # as from a jsr at the site
        ok &= uc.reg_read(mk.UC_M68K_REG_D0) == 0x1234 and uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        ok &= all(uc.reg_read(r) == v for r, v in zip(kept, vals))
        ok &= bytes(uc.mem_read(sp + 4, 16)) == frame[4:]
    s = state(uc, syms["cpu_data"])
    half = BLOCK // 2
    want = dict(ret=E.STOP, t0=(clock[0] - half) & 0xffffffff, sum=3 * half, peak=half, top=half, n=3,
                top_t=share(half), avg=0, windows=0)
    got = {k: s[k] for k in want}
    check(ok and got == want and not e.unmapped,
          f"{key}: the probe: the audio function sees its argument and the stack as from the call replaced, d0 comes "
          f"back, d2-d7/a2-a6 kept; three blocks of half a block counted (sum {s['sum']}, top {s['top_t'] / 10} %)"
          + ("" if got == want else f"; got {got}, want {want}"))


# --- 4. the window ---------------------------------------------------------------------------------------------------
def window_tests(key, w):
    tweak, info, img, runtime = w
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    e = engine(img, runtime, tweak)
    uc = e.uc
    at = syms["cpu_data"]
    fl_at = syms["fl_data"] + FL_DATA["avg_t"] if info["filters"] else None
    fx_at = syms["fx_data"] + FX_DATA["busy"] if info["fx"] else None
    half, hot = BLOCK // 2, 81101                               # half a block, 90 %
    blocks = [hot if b == 400 else half for b in range(WINDOW)]
    for v in blocks[:-1]:
        e.call(syms["cpu_block"], v)
    mid = state(uc, at)
    if fl_at:
        uc.mem_write(fl_at, struct.pack(">H", 123))             # the filter slot's last average: 12.3 %
    if fx_at:
        uc.mem_write(fx_at, struct.pack(">I", WINDOW * 4506))   # the effect slots' ticks: 5 % of the window
    e.call(syms["cpu_block"], blocks[-1])
    s = state(uc, at)
    want = dict(n=0, sum=0, peak=0, windows=1, avg=sum(blocks) // WINDOW_TICKS, win_peak=share(hot), top=hot,
                top_t=share(hot), trackfx=123 if fl_at else 0, effects=WINDOW * 4506 // WINDOW_TICKS if fx_at else 0,
                fx_last=WINDOW * 4506 if fx_at else 0)
    got = {k: s[k] for k in want}
    check(mid["n"] == WINDOW - 1 and mid["windows"] == 0 and mid["avg"] == 0 and mid["sum"] == sum(blocks[:-1])
          and got == want,
          f"{key}: a window of 750 blocks at 50 % with one at 90 %: average {s['avg'] / 10} %, peak "
          f"{s['win_peak'] / 10} %, Track FX {s['trackfx'] / 10} %, effects {s['effects'] / 10} %, then cleared and "
          "counted" + ("" if got == want else f"; got {got}, want {want}"))
    uc.mem_write(at + DATA["top"], struct.pack(">I", 0))        # the page opens: it clears the top
    uc.mem_write(at + DATA["top_t"], struct.pack(">H", 0))
    if fx_at:
        uc.mem_write(at + DATA["fx_last"], struct.pack(">I", 0xfffff000))
    second = [30000] * WINDOW
    for v in second[:-1]:
        e.call(syms["cpu_block"], v)
    if fx_at:
        uc.mem_write(fx_at, struct.pack(">I", (0xfffff000 + WINDOW * 9011) & 0xffffffff))   # across the wrap
    e.call(syms["cpu_block"], second[-1])
    s = state(uc, at)
    want = dict(windows=2, avg=sum(second) // WINDOW_TICKS, win_peak=share(30000), top=30000, top_t=share(30000),
                effects=WINDOW * 9011 // WINDOW_TICKS if fx_at else 0)
    got = {k: s[k] for k in want}
    check(got == want, f"{key}: a second window at 33 % after the top was cleared: average {s['avg'] / 10} %, top "
                       f"{s['top_t'] / 10} %, effects {s['effects'] / 10} % (their counter across its wrap)"
                       + ("" if got == want else f"; got {got}, want {want}"))
    e.call(syms["cpu_block"], 0x7fffffff)
    s = state(uc, at)
    check(s["sum"] == TOP_TICKS and s["peak"] == TOP_TICKS and s["top"] == TOP_TICKS and s["top_t"] == share(TOP_TICKS)
          and not e.unmapped, f"{key}: a block of 0x7fffffff ticks counted as 46 blocks ({s['top_t'] / 10} %)")


# --- 5. the whole audio interrupt ------------------------------------------------------------------------------------
class Clock:
    """The DMA timer 0 as the count of instructions executed outside skip (the CPU page's code), each read noted with
    the instruction that reads it."""

    def __init__(self, uc, skip):
        from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
        self.n, self.pc, self.reads, self.skip = 0, 0, [], skip
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_READ, self._read, begin=TIMER, end=TIMER + 3)

    def _code(self, uc, addr, size, ud):
        self.pc = addr
        if not self.skip[0] <= addr < self.skip[1]:
            self.n += 1

    def _read(self, uc, access, addr, size, value, ud):
        v = self.n & 0xffffffff
        uc.mem_write(TIMER, struct.pack(">I", v))
        self.reads.append((self.pc, v))


def pairs(reads, lo, hi):
    """The ticks between each two reads made from [lo, hi[, in order."""
    mine = [v for pc, v in reads if lo <= pc < hi]
    return [(b - a) & 0xffffffff for a, b in zip(mine[0::2], mine[1::2])], len(mine)


def interrupt_tests(key, stock, sel, w, wo, blocks):
    import mcengine as E
    import seqrig as S
    import test_fxslot as FX
    from unicorn import UC_HOOK_CODE
    from unicorn import m68k_const as mk

    class Rig(S.Rig):
        def _ret0(self, uc, addr, size, ud):     # seqrig skips the mixer, the effects and the output: run them
            if addr not in (0x40056f58, 0x40056ea8, 0x400567ba):
                super()._ret0(uc, addr, size, ud)

    descs = {}
    for i in range(76):
        o = g7.DESC + 0x38 * i - compose.BASE
        a_ = struct.unpack_from(">I", stock, o + 0x2c)[0] - compose.BASE
        descs[stock[a_:stock.index(b"\0", a_)].decode("latin1")] = dict(
            k=struct.unpack_from(">i", stock, o + 4)[0], default=struct.unpack_from(">h", stock, o + 18)[0])
    tweak, info, img, runtime = w
    ci = info["cpu"]
    crush = next((p["filter_id"] for p in info["packages"] if p["id"] == "crush"), None)
    pots = next((p["fx_id"] for p in info["packages"] if p["id"] == "pots"), None)
    builds = [("without", *(wo[2:4] if wo else (stock, None)), wo[0] if wo else None), ("with", img, runtime, tweak)]
    sides = []
    for name, im, rt, tw in builds:
        e = engine(im, rt, tw)
        uc = e.uc
        rig = Rig(e, bpm=120)
        S.ensure_map(uc, 0x4a000000, 0x00800000)
        uc.mem_map(FX.FIX, 0x00100000)

        def dma_done(u, _a, _s, _d):              # the read the hardware finishes and the emulator never does
            v = struct.unpack(">H", bytes(u.mem_read(FX.DMA_STATUS, 2)))[0]
            u.mem_write(FX.DMA_STATUS, struct.pack(">H", v & ~0x10))
        uc.hook_add(UC_HOOK_CODE, dma_done, begin=FX.DMA_WAIT, end=FX.DMA_WAIT)
        for t in range(6):                        # the six stock machines at their defaults, both sends up
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
            if crush and t in CRUSH_TRACKS:       # Crush on the track's sound (k 32's low byte), Rate low, Bits 6
                uc.mem_write(rig.sound(t) + 85, bytes([crush]))
                rig.param(t, 28, 24 << 8)
                rig.param(t, 29, 6 << 8)
        for j, v in ((214, 23 << 8), (215, 96 << 8), (216, 64 << 8), (217, 96 << 8)):   # Time, Fdbk, Size, Tone
            uc.mem_write(S.TARGETS + 2 * j, struct.pack(">h", v))
            uc.mem_write(S.SMOOTH + 4 * j, struct.pack(">i", v << 16))
            uc.mem_write(S.PARAMS + 2 * j, struct.pack(">h", v))
        for t in range(6):
            rig.set_step(t, 0, vel=100)
            for k in range(blocks // 12 + 1):
                rig.schedule_step(t, 0, rig.now + (2 + 12 * k + 2 * t) * rig.blk)
        pats = FX.Patterns(uc.mem_write, FX.FIX) if pots else None
        if pats:
            pats.link()
        skip = (ci["code_at"], ci["data_at"]) if name == "with" else (0, 0)
        sides.append(dict(name=name, e=e, uc=uc, rig=rig, clock=Clock(uc, skip), pats=pats))
    a, b = sides
    fl, fx = info["filters"], info["fx"]
    pay_same = []                                 # the payload outside the CPU page, when there is one
    if wo:
        pay_same = [(compose.gs.PAY_ALONE, ci["code_at"] - compose.gs.PAY_ALONE),
                    (ci["data_at"] + DATA["size"], info["end"] - ci["data_at"] - DATA["size"])]
    regs = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D0", "D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5",
                                                      "A6", "A7")]
    diff, stopped, busy_bad, fx_bad, fl_bad, inside_bad = [], [], [], [], [], []
    busies, fx_ticks, fl_ticks, prev = [], 0, 0, state(b["uc"], ci["data_at"])
    for i in range(blocks):
        if pots:
            for side in sides:
                side["pats"].set(0, FX.hdr(delay=pots if POTS_FROM <= i < POTS_TO else 0))
        counts = []
        for side in sides:
            uc, rig, ck = side["uc"], side["rig"], side["clock"]
            rig.w32(S.NOW, rig.now)
            fp0 = S.ISTACK - 4
            uc.reg_write(mk.UC_M68K_REG_A6, fp0)
            uc.reg_write(mk.UC_M68K_REG_A7, fp0 - 168)
            uc.reg_write(mk.UC_M68K_REG_D7, 0)
            uc.emu_start(ISR_BODY, PROBE_SITE, count=5_000_000)
            ok = uc.reg_read(mk.UC_M68K_REG_PC) == PROBE_SITE
            ck.reads.clear()
            n0 = ck.n
            uc.emu_start(PROBE_SITE, AFTER, count=10_000_000)
            ok &= uc.reg_read(mk.UC_M68K_REG_PC) == AFTER
            counts.append(ck.n - n0)
            rig.now += rig.blk
            if not ok and len(stopped) < 3:
                stopped.append(f"block {i} ({side['name']}): stopped at {uc.reg_read(mk.UC_M68K_REG_PC):#x}")
        ua, ub = a["uc"], b["uc"]
        sp = ub.reg_read(mk.UC_M68K_REG_A7)
        same = list(FX.EARLY_SAME) + [(sp, S.ISTACK - sp)] + pay_same
        for lo, n in same:
            x, y = bytes(ua.mem_read(lo, n)), bytes(ub.mem_read(lo, n))
            if x != y and len(diff) < 4:
                k = next(j for j in range(n) if x[j] != y[j])
                diff.append(f"block {i}: memory at {lo + k:#x}")
        ra, rb = [ua.reg_read(r) for r in regs], [ub.reg_read(r) for r in regs]
        if ra != rb and len(diff) < 4:
            diff.append(f"block {i}: registers {[hex(x) for x in ra]} / {[hex(x) for x in rb]}")
        ea, eb = a["e"].emac, b["e"].emac
        if (ea.macsr, list(ea.acc)) != (eb.macsr, list(eb.acc)) and len(diff) < 4:
            diff.append(f"block {i}: the EMAC")
        if counts[0] != counts[1] and len(diff) < 4:
            diff.append(f"block {i}: {counts[0]} / {counts[1]} instructions")
        s = state(ub, ci["data_at"])
        probe, n_probe = pairs(b["clock"].reads, ci["code_at"], ci["data_at"])
        busy = probe[0] if n_probe == 2 else None
        busies.append(busy)
        if (busy != counts[0] - 1 or s["sum"] - prev["sum"] != busy or s["n"] != prev["n"] + 1) and len(busy_bad) < 3:
            busy_bad.append(f"block {i}: busy {busy}, {counts[0]} instructions, sum {s['sum'] - prev['sum']}, "
                            f"n {prev['n']} -> {s['n']}")
        parts = 0
        if fx:
            ticks, n_fx = pairs(b["clock"].reads, fx["code_at"], fx["data_at"])
            grown = (rd(ub, fx["data_at"] + FX_DATA["busy"], ">I") - fx_ticks) & 0xffffffff
            fx_ticks += grown
            parts += grown
            want_calls = len(fx["slots"])
            if (grown != sum(ticks) or n_fx != 2 * want_calls or not grown) and len(fx_bad) < 3:
                fx_bad.append(f"block {i}: {n_fx} reads, grown {grown}, between them {sum(ticks)}")
        if fl:
            ticks, n_fl = pairs(b["clock"].reads, fl["code_at"], fl["data_at"])
            now_sum = rd(ub, fl["data_at"] + FL_DATA["sum"], ">I")
            grown = (now_sum - fl_ticks) & 0xffffffff
            fl_ticks = now_sum
            parts += grown
            if (grown != sum(ticks) or n_fl != 2 or not grown) and len(fl_bad) < 3:
                fl_bad.append(f"block {i}: {n_fl} reads, grown {grown}, between them {sum(ticks)}")
        if busy is not None and not parts < busy and len(inside_bad) < 3:
            inside_bad.append(f"block {i}: parts {parts}, busy {busy}")
        prev = s
    check(not stopped and not a["e"].unmapped and not b["e"].unmapped,
          f"{key}: the whole audio interrupt through 0x40059382, {blocks} blocks on both builds, back each time, "
          "nothing unmapped" + (f"; {'; '.join(stopped)}" if stopped else "")
          + (f"; unmapped {[hex(x) for _p, x in (a['e'].unmapped + b['e'].unmapped)[:4]]}"
             if a["e"].unmapped or b["e"].unmapped else ""))
    what = ", ".join(x for x in (f"Crush on tracks {', '.join(str(t + 1) for t in CRUSH_TRACKS)}" if crush else "",
                                 f"POTS in blocks {POTS_FROM} to {POTS_TO - 1}" if pots else "") if x)
    check(not diff, f"{key}: six tracks, both sends{', ' + what if what else ''}: after every block the SRAM, the "
          "voices, the mixer's state, the effects' lines, the eDMA's registers, the interrupt's frame"
          + (", the payload outside the CPU page" if wo else "") + ", d0, d2-d7/a2-a7, the EMAC and the number of "
          f"instructions as {'the stock OS' if not wo else 'without the CPU page'}'s, bit for bit"
          + (f"; DIFFERENT {'; '.join(diff)}" if diff else ""))
    real = [x for x in busies if x is not None]
    check(not busy_bad and len(real) == blocks,
          f"{key}: each block's busy ticks the audio function's instructions ({min(real) if real else 0} to "
          f"{max(real) if real else 0}), the window's sum and blocks growing by them"
          + (f"; {'; '.join(busy_bad)}" if busy_bad else ""))
    if fx:
        check(not fx_bad, f"{key}: the effect slots' running ticks growing each block by the ticks between their two "
                          f"reads around each slot's run ({fx_ticks} in all)" + (f"; {'; '.join(fx_bad)}" if fx_bad else ""))
    if fl:
        check(not fl_bad, f"{key}: the filter slot's own sum growing each block by the ticks around its run"
                          + (f"; {'; '.join(fl_bad)}" if fl_bad else ""))
    if fx or fl:
        check(not inside_bad, f"{key}: the Track FX' and the effect slots' ticks inside the CPU page's each block"
                              + (f"; {'; '.join(inside_bad)}" if inside_bad else ""))


# --- 6. to 8.: the row, the page, the render (the interface's code, function by function) ----------------------------
NEW, ALLOC = 0x400802e0, 0x40080064            # operator new, and the allocator it jumps to (lm_add_row's)
ITEM_CTOR, ADD_ITEM, LET_GO, FORMAT = 0x400734b0, 0x40072ce6, 0x400cf044, 0x400f980c
CFG_STUBS = {0x400406d8: "title", 0x400f7d5c: "string drop", 0x4003ebc2: "member", 0x4007649e: "base"}
GENERIC, WITH_ARG = 0x4002f136, 0x4002f188    # the closures' managers
PAGE_CTOR, VIEWS, PRESENT, DROP, VIEWS_UP = 0x400a22b0, 0x400d0974, 0x4007700e, 0x400cf23c, 0x40fe4178
DTOR0, DTOR1, CLOSE, KEY_STOCK, ENC_BASE = 0x400f43ca, 0x400f4486, 0x40076126, 0x40075f3c, 0x4006fb90
HOLDER_VT, VT_SRC, VT_LEN, PAGE_SIZE = 0x401000c4, 0x40117918, 0xb0, 0xd0
OURS = {0x08: "cpu_dtor0", 0x0c: "cpu_dtor1", 0x10: "cpu_key", 0x18: "cpu_render", 0x34: "cpu_tick", 0x4c: "cpu_enc",
        0x58: "cpu_dtor0_th", 0x5c: "cpu_dtor1_th", 0x60: "cpu_enc_th"}
NEEDS_REDRAW, VIEWS_PASS, STOCK_TICK = 0x40076082, 0x400778e2, 0x40075f2e   # setNeedsRedraw; the views' timer pass
PASS_STUBS = {0x400e8684: "pass lock", 0x400d08ce: "pass unlock"}
SCREEN = 0x93c40000
LIST, VIEWS_OBJ, EVENT = 0x93c00000, 0x93c10000, 0x93c20000
BMP_CTOR, BMP, FB, W, H, PITCH = 0x40070172, 0x93a50000, 0x93a60000, 128, 64, 2
KEPT = ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")


def ui(w):
    import test_shortcuts as SH
    from unicorn import m68k_const as mk

    class UI(SH.UI):
        """test_shortcuts.py's UI (a heap for operator new, the stack's check), with what the stubbed item constructor
        and present were given: the closures and the pair as they were at the call."""

        def _hook(self, uc, addr, size, ud):
            h = self.hooks.get(addr)
            if isinstance(h, tuple) and h[0] in ("item", "present"):
                sp = uc.reg_read(mk.UC_M68K_REG_A7)
                args = struct.unpack(">7I", uc.mem_read(sp + 4, 28))
                rd4 = lambda a, n: struct.unpack(f">{n}I", uc.mem_read(a, 4 * n))
                if h[0] == "item":
                    self.seen.append([rd4(c, 4) for c in args[1:5]])
                else:
                    pair = rd4(args[1], 2)
                    self.seen.append((pair, rd4(pair[1], 4)))
            super()._hook(uc, addr, size, ud)

    tweak, info, img, runtime = w
    u = UI(img, runtime)
    u.seen = []
    u.uc.mem_write(LIST, bytes(0x1000))
    return u


def regs_set(u):
    from unicorn import m68k_const as mk
    vals = [0x5a5a0000 + i for i in range(len(KEPT))]
    for r, v in zip(KEPT, vals):
        u.uc.reg_write(getattr(mk, f"UC_M68K_REG_{r}"), v)
    return lambda: all(u.uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) == v for r, v in zip(KEPT, vals))


def row_tests(key, stock, w):
    tweak, info, img, runtime = w
    ps = part_syms(info)
    rows = {}
    for name, ww in (("stock", (None, None, stock, b"")), ("build", w)):
        u = ui(ww)
        u.hooks = {NEW: ("new", 0), ALLOC: ("new", 0), ITEM_CTOR: ("item", 0), ADD_ITEM: ("add", 0),
                   LET_GO: ("let go", 0), FORMAT: ("format", 0), **{a: (n, 0) for a, n in CFG_STUBS.items()}}
        kept = regs_set(u)
        u.call(CFG_CTOR, LIST)
        calls = lambda n: [a for c, a in u.calls if c == n]
        rows[name] = dict(adds=calls("add"), items=calls("item"), seen=list(u.seen), let_go=calls("let go"),
                          kept=kept() and u.sp_ok and not u.bad, u=u)
    st, b = rows["stock"], rows["build"]
    lists = {a[0] for a in st["adds"] + b["adds"]}
    ours = b["seen"][-1] if len(b["seen"]) == 5 else None
    want = [(GENERIC, ps["cpu_lab"]), (WITH_ARG, ps["cpu_press"]), (GENERIC, ps["cpu_nop"]), (WITH_ARG, ps["cpu_nop"])]
    u = b["u"]
    arg_of = lambda c: struct.unpack(">I", u.uc.mem_read(c[0], 4))[0]
    item_args = b["items"][-1][1:5] if b["items"] else ()
    freed = [a[0] for a in b["let_go"][-4:]]
    ok = (ours is not None and [(c[2], c[3]) for c in ours] == want and [c[1] for c in ours] == [0] * 4
          and arg_of(ours[1]) == LIST and arg_of(ours[3]) == LIST and b["items"][-1][5:7] == (0xffffffff, 8)
          and b["adds"][-1][1] == b["items"][-1][0] and freed == [item_args[3], item_args[2], item_args[1], item_args[0]])
    added = lambda r: [a[1] for a in r["adds"]] == [i[0] for i in r["items"]]
    check(len(st["adds"]) == 4 and len(b["adds"]) == 5 and added(st) and added(b) and lists == {LIST} and len(st["let_go"]) == 16 and len(b["let_go"]) == 20 and ok
          and st["kept"] and b["kept"],
          f"{key}: the device configuration list's constructor: {len(st['adds'])} rows in the stock OS, "
          f"{len(b['adds'])} in the build, the last the row CPU (cpu_lab, cpu_press with the list, cpu_nop twice), its "
          "closures let go after it; the registers and the stack back")
    u.hooks = {FORMAT: ("format", 0)}
    u.calls.clear()
    d0 = u.call(ps["cpu_lab"])
    fmt = [a for c, a in u.calls if c == "format"]
    check(len(fmt) == 1 and fmt[0][0] == t7.SCRATCH and u.cstr(fmt[0][1]) == "CPU" and d0 == t7.SCRATCH and u.sp_ok
          and u.call(ps["cpu_nop"]) == 0,
          f"{key}: the row's label \"{u.cstr(fmt[0][1]) if fmt else '?'}\" into the string the list gives, its pointer "
          "back; its value and turn: none")


def page_hooks(u):
    u.hooks = {NEW: ("new", 0), ALLOC: ("new", 0), PAGE_CTOR: ("page ctor", 0), VIEWS: ("views", VIEWS_OBJ),
               PRESENT: ("present", 0), DROP: ("drop", 0), DTOR0: ("dtor0", 0), DTOR1: ("dtor1", 0),
               CLOSE: ("close", 0), KEY_STOCK: ("keys", 0x77), ENC_BASE: ("base", 0x66), NEEDS_REDRAW: ("redraw", 0),
               **{a: (n, 0) for a, n in PASS_STUBS.items()}}


def press(u, ps, sr=0x2000):
    from unicorn import m68k_const as mk
    u.calls.clear()
    u.seen.clear()
    u.uc.reg_write(mk.UC_M68K_REG_SR, sr)
    return u.call(ps["cpu_press"])


def page_tests(key, w):
    tweak, info, img, runtime = w
    ps = part_syms(info)
    at = info["cpu"]["data_at"]
    u = ui(w)
    page_hooks(u)
    u.uc.mem_write(VIEWS_UP, struct.pack(">I", VIEWS_OBJ))
    r32 = lambda a: struct.unpack(">I", u.uc.mem_read(a, 4))[0]
    stock_vt = struct.unpack(f">{VT_LEN // 4}I", u.uc.mem_read(VT_SRC, VT_LEN))
    u.uc.mem_write(at + DATA["top"], struct.pack(">I", 12345))      # a top from before, 7 windows ended
    u.uc.mem_write(at + DATA["top_t"], struct.pack(">H", 137))
    u.uc.mem_write(at + DATA["windows"], struct.pack(">H", 7))
    d0 = press(u, ps)
    cleared = (r32(at + DATA["top"]), struct.unpack(">HHH", u.uc.mem_read(at + DATA["top_t"], 2) + u.uc.mem_read(
        at + DATA["windows"], 4)))
    ctor = [a for c, a in u.calls if c == "page ctor"]
    present = [a for c, a in u.calls if c == "present"]
    drop = [a for c, a in u.calls if c == "drop"]
    page = r32(at + DATA["page"])
    vt = at + DATA["vt"]
    copy = struct.unpack(f">{VT_LEN // 4}I", u.uc.mem_read(vt, VT_LEN))
    want_copy = tuple(ps[OURS[4 * i]] if 4 * i in OURS else v for i, v in enumerate(stock_vt))
    pair, holder = u.seen[0] if len(u.seen) == 1 else ((0, 0), (0,) * 4)
    check(d0 == 0 and len(ctor) == 1 and ctor[0][0] == page and page and r32(page) == vt + 8
          and r32(page + 4) == vt + 0x58 and copy == want_copy and len(present) == 1
          and present[0][:3] == (VIEWS_OBJ + 64, present[0][1], 0) and pair == (page, pair[1])
          and holder == (HOLDER_VT, 1, 1, page) and len(drop) == 1 and drop[0][0] == present[0][1] + 4
          and cleared == (0, (0, 7, 7)) and u.sp_ok and not u.bad,
          f"{key}: the row's press: one page of {PAGE_SIZE:#x} bytes at {page:#x} by the stock constructor, its vtables "
          f"the private copy (the stock group but for its {len(OURS)} entries), presented once on the views' screen "
          "with a reference holder {0x401000c4, 1, 1, page}, the holder let go; the top cleared (PEAK from now), the "
          f"windows noted ({cleared})")
    again = []
    press(u, ps)
    again.append(len([c for c, _a in u.calls if c in ("present", "page ctor")]))
    u.uc.mem_write(at + DATA["page"], bytes(4))
    press(u, ps, sr=0x2700)
    again.append(len([c for c, _a in u.calls if c in ("present", "page ctor")]))
    u.uc.mem_write(VIEWS_UP, bytes(4))
    press(u, ps)
    again.append(len([c for c, _a in u.calls if c in ("present", "page ctor")]))
    u.uc.mem_write(VIEWS_UP, struct.pack(">I", VIEWS_OBJ))
    press(u, ps)
    again.append(len([c for c, _a in u.calls if c in ("present", "page ctor")]))
    page = r32(at + DATA["page"])
    check(again == [0, 0, 0, 2] and page, f"{key}: no second page while one is up, none at interrupt level 7 or "
                                          f"without the view machinery; the press opens it again ({again})")
    gone = []
    for off, stock_name, this in ((0x08, "dtor0", 0), (0x0c, "dtor1", 0), (0x58, "dtor0", 4), (0x5c, "dtor1", 4)):
        page = r32(at + DATA["page"])
        u.calls.clear()
        u.call(copy[off // 4], page + this)
        called = [a[0] for c, a in u.calls if c == stock_name]
        gone.append(r32(at + DATA["page"]) == 0 and called == [page] and u.sp_ok)
        press(u, ps)
    check(all(gone) and r32(at + DATA["page"]), f"{key}: each destructor (and its thunk from the +4 base) forgets the "
                                                f"page and goes on to the stock one with it; the press opens it again")
    page = r32(at + DATA["page"])
    keys = []
    for code, flags, want_close, want in ((12, 0x10, 1, 1), (12, 0, 0, 1), (5, 0x19, 0, 0x77), (13, 0x19, 0, 0x77)):
        u.uc.mem_write(EVENT, struct.pack(">5I", 0, 0, 0, code, flags))
        u.calls.clear()
        d0 = u.call(copy[0x10 // 4], page, EVENT)
        closed = [a[0] for c, a in u.calls if c == "close"]
        stockd = [a[:2] for c, a in u.calls if c == "keys"]
        keys.append(d0 == want and closed == [page] * want_close
                    and stockd == ([] if code == 12 else [(page, EVENT)]) and u.sp_ok)
    check(all(keys), f"{key}: the key handler: Return with its flag closes the page and is used, without it only used; "
                     f"PRESET and SETTINGS the stock view's dispatch with its answer ({keys})")
    encs = []
    for off, this in ((0x4c, page), (0x60, page + 4)):
        for knob, want in ((1, 1), (2, 0x66)):
            u.uc.mem_write(EVENT, struct.pack(">5I", 0, 0, 0, knob, 0))
            u.calls.clear()
            d0 = u.call(copy[off // 4], this, EVENT)
            base = [a[:2] for c, a in u.calls if c == "base"]
            encs.append(d0 & 0xff == want & 0xff and base == ([] if knob == 1 else [(page + 4, EVENT)]) and u.sp_ok)
    check(all(encs), f"{key}: the encoder handler and its thunk: DATA's turn used and nothing else, another knob the "
                     f"base's handler with this + 4 and its answer ({encs})")
    tick = copy[0x34 // 4]
    redraws = []
    for windows in (7, 7, 8, 8, 9):
        u.uc.mem_write(at + DATA["windows"], struct.pack(">H", windows))
        u.calls.clear()
        u.call(tick, page)
        redraws.append([a[0] for c, a in u.calls if c == "redraw"] == [page])
    empty = stock_vt[0x34 // 4] == STOCK_TICK and bytes(u.uc.mem_read(STOCK_TICK, 2)) == b"\x4e\x75"
    check(redraws == [False, False, True, False, True] and empty and u.sp_ok,
          f"{key}: the page's periodic method (its vtable's +0x2c, the stock page's an empty rts at {STOCK_TICK:#x}): a "
          f"redraw of the page when a window has ended since the last, else none ({redraws})")
    # the OS's timer pass over the view stack (0x400778e2): a screen whose list (+20) holds the page
    node = SCREEN + 0x100
    u.uc.mem_write(SCREEN, bytes(0x200))
    u.uc.mem_write(SCREEN + 20, struct.pack(">II", node, node))     # the sentinel: next, prev
    u.uc.mem_write(node, struct.pack(">III", SCREEN + 20, SCREEN + 20, page))
    u.uc.mem_write(at + DATA["windows"], struct.pack(">H", 10))
    u.calls.clear()
    u.call(VIEWS_PASS, SCREEN)
    passed = [a[0] for c, a in u.calls if c == "redraw"]
    check(passed == [page] and u.sp_ok and not u.bad,
          f"{key}: the OS's own timer pass over the view stack (0x400778e2) calls the page's method, which asks for its "
          "redraw")
    return u, copy, page


def lit(fb, x, row):
    y = H - 1 - row
    return struct.unpack_from(">I", fb, 4 * (x * PITCH + (y >> 5)))[0] >> (31 - (y & 31)) & 1


def ascii_screen(fb):
    return "\n".join(f"{r:2d} " + "".join("#" if lit(fb, x, r) else "." for x in range(W)) for r in range(H))


def render_tests(key, w, u, copy, page, show):
    tweak, info, img, runtime = w
    at = info["cpu"]["data_at"]
    u.hooks = {}
    u.call(BMP_CTOR, BMP, W, H, FB, 0)

    def draw(avg, top, trackfx, effects, fl=None, fx=None):
        u.uc.mem_write(at + DATA["avg"], struct.pack(">HHHHH", avg, 0, top, trackfx, effects))
        if fl is not None:
            u.uc.mem_write(at + DATA["fl_avg"], struct.pack(">II", fl, fx))
        u.uc.mem_write(FB, bytes([0xa5]) * (W * PITCH * 4))         # whatever was there
        u.calls.clear()
        u.call(copy[0x18 // 4], page, BMP)
        return bytes(u.uc.mem_read(FB, W * PITCH * 4)), u.sp_ok and not u.bad
    kept = struct.unpack(">II", u.uc.mem_read(at + DATA["fl_avg"], 8))
    a, ok_a = draw(723, 851, 120, 85, 0x93c30000, 0x93c30010)
    b, ok_b = draw(151, 999, 7, 333)
    c, ok_c = draw(1200, 1500, 120, 85, 0, 0)
    u.uc.mem_write(at + DATA["fl_avg"], struct.pack(">II", *kept))
    if show:
        print(ascii_screen(a))

    def bar_ok(fb, avg):
        fill = min(avg, 1000) * 122 // 1000
        good = all(lit(fb, x, 12) and lit(fb, x, 16) for x in range(2, 126))
        for r in (13, 14, 15):
            good &= lit(fb, 2, r) and lit(fb, 125, r)
            good &= all(lit(fb, x, r) == (x < 3 + fill) for x in range(3, 125))
        for r in (10, 11, 17, 18):
            good &= all(lit(fb, x, r) == (x == 3 + 850 * 122 // 1000) for x in range(W))
        return good
    lines = {"CPU": 1, "PEAK": 22, "TRACK FX": 33, "EFFECTS": 44}
    text_rows = {r0 + i for r0 in lines.values() for i in range(9)}
    bar_rows = set(range(10, 19))

    def placed(fb):
        stray = [(x, r) for r in range(H) for x in range(W) if lit(fb, x, r) and r not in text_rows | bar_rows]
        sides = all(any(lit(fb, x, r0 + i) for x in range(0, 60) for i in range(9))
                    and any(lit(fb, x, r0 + i) for x in range(68, W) for i in range(9)) for r0 in lines.values())
        return not stray and sides

    def part(fb, r0, x0, x1):
        return [lit(fb, x, r0 + i) for x in range(x0, x1) for i in range(9)]
    labels_same = all(part(a, r0, 0, 60) == part(b, r0, 0, 60) == part(c, r0, 0, 60) for r0 in lines.values())
    values_differ = all(part(a, r0, 68, W) != part(b, r0, 68, W) for r0 in lines.values())
    dashes = (part(c, 33, 68, W) != part(a, 33, 68, W) and part(c, 44, 68, W) != part(a, 44, 68, W)
              and sum(part(c, 33, 68, W)) < sum(part(a, 33, 68, W)) and part(c, 33, 68, W) == part(c, 44, 68, W))
    check(ok_a and ok_b and ok_c and bar_ok(a, 723) and bar_ok(b, 151) and bar_ok(c, 1200) and placed(a) and placed(b)
          and placed(c), f"{key}: the render: the screen cleared, the bar outlined and filled to the average (72.3 %, "
                         "15.1 %, 120 % capped), the mark at 85 % above and below it, each line's label and value in "
                         "its rows, nothing lit elsewhere")
    check(labels_same and values_differ and dashes,
          f"{key}: other values: the same labels, other values; without Track FX or effects \"--\" in their lines")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection besides the CPU page, ids comma-separated "
                                                        "(repeat for several; an empty one for the page alone)")
    ap.add_argument("--blocks", type=int, default=40, help="blocks of the whole interrupt")
    ap.add_argument("--dry", action="store_true", help="the builds only, without Unicorn")
    ap.add_argument("--show", action="store_true", help="print the page as the render draws it")
    args = ap.parse_args()
    sels = ([[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines is not None
            else SELECTIONS)
    stock = T.main_os_from_syx(args.cycles)
    for sel in sels:
        key = ids_of(sel)
        w = composed(stock, sel, True)
        wo = composed(stock, sel, False) if sel else None
        print(f"\n{key}: the CPU page at {w[1]['cpu']['code_at']:#x}, its data at {w[1]['cpu']['data_at']:#x}")
        print("the build")
        build_tests(key, stock, sel, w, wo)
        if args.dry:
            continue
        import test_sdvintage_exact as X
        print("start-up")
        X.bootstrap_depack_ok(args.cycles, w[0], None) or t7.FAIL.append(f"{key}: bootstrap")
        X.boot_hook_ok(w[2], w[3]) or t7.FAIL.append(f"{key}: boot hook")
        print("the probe")
        probe_tests(key, w)
        print("the window")
        window_tests(key, w)
        print("the whole audio interrupt")
        interrupt_tests(key, stock, sel, w, wo, args.blocks)
        print("the row")
        row_tests(key, stock, w)
        print("the page")
        u, copy, page = page_tests(key, w)
        print("the render")
        render_tests(key, w, u, copy, page, args.show)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
