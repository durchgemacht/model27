#!/usr/bin/env python3
"""Proof of SAMPLE's pan step (One-Shot 0.15, notes/63 §31) on the OS's own code: FUNC + LEVEL/DATA on the main
screen adds 2 a step to the track's pan (0x4006f73a(event, 2, 16), 16 in the fast mode) and the setter clamps it to
-64..63, so from 63 the stock OS goes on odd values; SAMPLE's two hooks (0x4001ab14 one track, 0x4001ab52 each track
with TRACK held) hand the sum to smp_pan_step, which on a SAMPLE track moves a pan on an odd value one less, onto the
even value next to it in the turning direction.

For the selections sampler and sampler,refmachine2, on the official OS 1.13:
  1. the sites: 0x4001ab14 -> jsr smp_hook_pan and 0x4001ab52 -> jsr smp_hook_pan_all, the stock bytes before them;
  2. MainScreenView's encoder handler (0x4001aa4e) from its entry, stock and with SAMPLE: LEVEL/DATA turned by -3, -1,
     +1, +3 steps, in the normal and the fast mode, the selected track 0, 1 or 5, FUNC held or not, TRACK held or
     not, tracks 0, 2 and 5 on SAMPLE and the others on machine 0, every track's pan at -64, -63, -1, 0, 1, 62, 63 or
     an odd value with a fraction: the setters (the pan's 0x4000b274, the volume's 0x4000a3ae; stubbed) get the same
     calls as on the stock OS, the stock OS's pan being pan + step, except that on a SAMPLE track a pan on an odd value
     gets pan + step one less in the turning direction; the handler's answer, d2..d7/a2..a6 and the stack as on the
     stock OS; another encoder passes the event on (0x4006fb90) as on the stock OS;
  3. the maintainer's walk on a SAMPLE track, the setter clamping as the OS (-64..63): from 0 turned right a step at a
     time to 63, then left to -64: with SAMPLE only even values on the way back, 0 among them; the stock OS 61, 59 ...
     and no 0 before -64; on a track of machine 0 the stock OS's values.
Not covered here: the OS's own setter (stubbed; its clamp is read in notes/44) and the screen (One-Shot's host test
test_pan_step, and the device).

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_sample_pan.py --cycles model-cycles_OS1.13.syx
"""
import argparse
import pathlib
import struct
import sys

from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_shortcuts as TSC        # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

SELECTIONS = [["sampler"], ["sampler", "refmachine2"]]
BASE = 0x40000400
ENC = 0x4001aa4e                                    # MainScreenView's encoder handler (this, event)
SITES = {0x4001ab14: ("2f032f02d880", "smp_hook_pan"), 0x4001ab52: ("2f022800d887", "smp_hook_pan_all")}
PROJECT, TRACKS, ACTIVE, KIT_OF, PARAMS = 0x400cf866, 0x4000eb90, 0x40012412, 0x4000eb9c, 0x400097f0
SET_PAN, VOL_GET, VOL_SET, PASS = 0x4000b274, 0x40009ca0, 0x4000a3ae, 0x4006fb90
THIS, EVT = 0x93f00000, 0x93f00100
PROJ, SEL, KIT = 0x93f10000, 0x93f20000, 0x93f30000
HOLD, PVT, GET = 0x93f40000, 0x93f50000, 0x93f50100   # track t's parameters at HOLD + 0x100 t, their vtable, +28
TVT, SNDF, SND = 0x93f60000, 0x93f60100, 0x93f70000   # the project's tracks' vtable, its +40, sound t at SND + 0x100 t
SAMPLE_TRACKS = (0, 2, 5)
PANS = (0, 1, 63, 64, 65, 126, 127)                   # -64, -63, -1, 0, 1, 62, 63 as the OS keeps them (8.8 >> 8)
FUNC, TRACK = TSC.FUNC, TSC.TRACK


class UI(TSC.UI):
    """test_shortcuts' UI, whose stubs may also be functions of their arguments."""

    def _hook(self, uc, addr, size, ud):
        h = self.hooks.get(addr)
        if callable(h):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
            self.calls.append((h.__name__, args))
            uc.reg_write(mk.UC_M68K_REG_D0, h(args) & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
            return
        super()._hook(uc, addr, size, ud)


def s32(x):
    return struct.unpack(">i", struct.pack(">I", x & 0xffffffff))[0]


class Rig:
    """The handler's world: the project, its kit's track parameters (each track's pan), the project's tracks and
    their sounds (machine at +38), the setters recording, or with clamp the pan setter keeping the clamped value."""

    def __init__(self, u, smp, clamp=False):
        self.u, self.smp, self.clamp = u, smp, clamp
        self.pans = [64 << 8] * 6
        self.track = 0
        w = u.uc.mem_write
        for t in range(6):
            w(HOLD + 0x100 * t, struct.pack(">I", PVT))
            w(PROJ + 212 + 68 * t, struct.pack(">I", TVT))
            snd = bytearray(0x100)
            snd[38] = smp if t in SAMPLE_TRACKS else 0
            w(SND + 0x100 * t, bytes(snd))
        w(PVT + 28, struct.pack(">I", GET))
        w(TVT + 40, struct.pack(">I", SNDF))

        def params(a):          # 0x400097f0(kit, t)
            return HOLD + 0x100 * a[1]

        def pan_get(a):         # vtable[28](parameters, 0x1c)
            return self.pans[(a[0] - HOLD) // 0x100] if a[1] == 0x1c else 0

        def sound(a):           # the project's track t's vtable +40
            return SND + 0x100 * ((a[0] - PROJ - 212) // 68)

        def pan_set(a):         # 0x4000b274(parameters, 0x1c, value, t, 0, 1)
            if self.clamp:
                v = s32(a[2])
                self.pans[(a[0] - HOLD) // 0x100] = max(0, min(127 << 8, v))
            return 0

        def active(a):
            return self.track
        self.stubs = {PROJECT: ("project", PROJ), TRACKS: ("tracks", SEL), ACTIVE: active, KIT_OF: ("kit", KIT),
                      PARAMS: params, GET: pan_get, SNDF: sound, SET_PAN: pan_set, VOL_GET: ("volume", 100 << 8),
                      VOL_SET: ("set_volume", 0), PASS: ("pass", 1)}

    def turn(self, held, delta, fast=0, enc=1):
        """One turn of an encoder on the main screen: (the setters' and the pass's calls, d0's byte, d2..d7/a2..a6
        and the stack kept, memory in bounds)."""
        u = self.u
        u.keys(held)
        u.hooks = dict(self.stubs)
        u.uc.mem_write(EVT, struct.pack(">IIIIiB3x", 0x400fbebc, 0, 0, enc, delta, fast))
        u.calls.clear()
        vals = TSC.sentinels(u)
        d0 = u.call(ENC, THIS, EVT)
        kept = [u.uc.reg_read(r) & 0xffffffff for r in TSC.KEPT] == vals
        calls = [(n, a[:6] if n == "pan_set" else a[:3]) for n, a in u.calls
                 if n in ("pan_set", "set_volume", "pass")]
        return calls, d0 & 0xff, kept and u.sp_ok and not u.bad


def handler_tests(key, stock, img, runtime, smp):
    a, b = Rig(UI(stock), smp), Rig(UI(img, runtime), smp)
    bad, cases, snapped = [], 0, 0
    for track in (0, 1, 5):
        for held in ((), (FUNC,), (TRACK,), (FUNC, TRACK)):
            for delta in (-3, -1, 1, 3):
                for fast in (0, 1):
                    for pan in [p << 8 for p in PANS] + [(65 << 8) | 0x80]:
                        for r in (a, b):
                            r.track, r.pans = track, [pan] * 6
                        ca, da, oka = a.turn(held, delta, fast)
                        cb, db, okb = b.turn(held, delta, fast)
                        cases += 1
                        step = delta * (16 if fast else 2) << 8
                        want = []
                        for n, args in ca:
                            if n == "pan_set":
                                t = args[3]
                                if s32(args[2]) != pan + step:
                                    bad.append(("stock model", track, held, delta, fast, hex(pan), hex(args[2])))
                                v = pan + step
                                if t in SAMPLE_TRACKS and pan >> 8 & 1:
                                    v -= 0x100 if step > 0 else -0x100
                                    snapped += 1
                                args = args[:2] + (v & 0xffffffff,) + args[3:]
                            want.append((n, args))
                        if FUNC in held:
                            tracks = sorted(args[3] for n, args in ca if n == "pan_set")
                            if tracks != (list(range(6)) if TRACK in held else [track]):
                                bad.append(("stock tracks", track, held, tracks))
                        if not (cb == want and db == da and oka and okb):
                            bad.append((track, held, delta, fast, hex(pan), cb[:2], want[:2], db, da, oka, okb))
    for enc in (0, 2):                                   # another encoder: passed on, as on the stock OS
        ca, da, oka = a.turn((FUNC,), 1, 0, enc)
        cb, db, okb = b.turn((FUNC,), 1, 0, enc)
        cases += 1
        if not (cb == ca and [n for n, _ in ca] == ["pass"] and db == da and oka and okb):
            bad.append(("encoder", enc, cb, ca))
    a.u.keys(())
    b.u.keys(())
    check(not bad and snapped, f"{key}: MainScreenView's encoder handler (0x4001aa4e), stock and with SAMPLE: the "
                               "setters' calls as on the stock OS (pan + step, the volume, the other encoders "
                               f"passed on), but on SAMPLE's tracks {list(SAMPLE_TRACKS)} a pan on an odd value one "
                               f"less in the turning direction ({snapped} such calls; {cases} cases: tracks 0, 1, 5, "
                               "FUNC, TRACK, steps -3..+3, the fast mode, pans -64..63 and a fraction); the answer, "
                               "registers and stack as on the stock OS" + (f"; DIFFERENT {bad[:3]}" if bad else ""))


def walk(r, track, held, delta, n):
    seen = []
    for _ in range(n):
        r.turn(held, delta)
        seen.append((r.pans[track] >> 8) - 64)
    return seen


def walk_tests(key, stock, img, runtime, smp):
    a, b = Rig(UI(stock), smp, clamp=True), Rig(UI(img, runtime), smp, clamp=True)
    out = {}
    for name, r in (("stock", a), ("SAMPLE", b)):
        for track, held in ((2, (FUNC,)), (1, (FUNC,)), (5, (FUNC, TRACK))):
            r.track, r.pans = track, [64 << 8] * 6
            right = walk(r, track, held, 1, 40)
            left = walk(r, track, held, -1, 70)
            out[(name, track, held)] = (right, left)
    sr, sl = out[("SAMPLE", 2, (FUNC,))]
    tr, tl = out[("stock", 2, (FUNC,))]
    check(sr[-1] == 63 and 0 in sl and all(v % 2 == 0 for v in sl) and sl[-1] == -64 and sl[0] == 62,
          f"{key}: the walk on a SAMPLE track (track 3): right to 63, then left 62, 60 ... 0 ... -64, only even values")
    check(tr[-1] == 63 and tl[0] == 61 and 0 not in tl and tl[-1] == -64,
          f"{key}: the same on the stock OS: 63, then 61, 59 ... no 0 on the way to -64 (what the maintainer saw)")
    check(out[("SAMPLE", 1, (FUNC,))] == out[("stock", 1, (FUNC,))],
          f"{key}: the walk on a track of machine 0 (track 2): the stock OS's values")
    sa, st = out[("SAMPLE", 5, (FUNC, TRACK))], out[("stock", 5, (FUNC, TRACK))]
    check(0 in sa[1] and all(v % 2 == 0 for v in sa[1]) and 0 not in st[1],
          f"{key}: with TRACK held, track 6 (SAMPLE): the even values and 0, the stock OS's odd ones")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    for ids in SELECTIONS:
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        smp = next(m["index"] for m in TC.configure(ids) if m["code"] == "sampler")
        syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
        print(f"\n{key}: SAMPLE = machine {smp}")
        for va, (old, sym) in SITES.items():
            check(stock[va - BASE:va - BASE + 6].hex() == old
                  and img[va - BASE:va - BASE + 6].hex() == f"4eb9{syms[sym]:08x}",
                  f"{key}: {va:#x}: {old} on the stock OS -> jsr {sym}")
        print("the encoder handler")
        handler_tests(key, stock, img, runtime, smp)
        print("the walk")
        walk_tests(key, stock, img, runtime, smp)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
