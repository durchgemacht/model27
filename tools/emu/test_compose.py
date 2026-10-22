#!/usr/bin/env python3
"""Proof of Level B's composed builds on the OS's own code (notes/59 §3, notes/60 §5.4 and §8): the machines that
tools/compose.py registers through the registrar runtime (registrar.S, a parameter block per build) behave in the
OS as the per-build detours of B1 (gen_macro.added_machine) made them behave, and the rest of the OS as stock.

For each selection (by default: sampler; refmachine; sampler,refmachine; refmachine,sampler; refmachine2;
sampler,refmachine2; sampler,refmachine,refmachine2), on the official OS 1.13:
  1. start-up: the bootstrap's own aPLib depacker reads the grown OS back; the boot hook copies the packed payload
     to its place, segment by segment, and clears the BSS;
  2. the registrar's mechanics, with the checks of test_syntakt_machines.py configured for the composed machines:
     parameter tables built at boot, lookups, accessors and state per descriptor, the MACHINES page (names,
     pictures, marks, two rows from 8 machines), the machine setter and the wheel, records per machine, a real
     machine change, the main screen's knobs, a machine this build does not have, the small icon;
  3. the runtime against B1: the same results, input for input, from the OS functions that go through the detours
     (B1 is built with the m68k toolchain; without it this part is skipped and says so);
  4. the voice loop: REF plays the same as machine 6 alone and as machine 7 next to SAMPLE, REF2 the same as machine
     6, 7 or 8 (notes/63), and REF2 does not sound like REF; SNARE on track 1 is the stock OS's, sample for sample;
     SAMPLE with no sample loaded stays silent; no access outside memory.

The payload is given to the emulator as it lies in memory (build.payload_runtime) with the code ranges read from the
composed tweak's parts, so the EMAC instructions of a package are emulated wherever the composer placed it
(mcengine.PAYLOAD_CODE only knows the old fixed layout).

Needs Unicorn and numpy (pip install unicorn numpy) and m68k-elf-objdump; Unicorn's JIT does not run inside a
sandbox that forbids it (it stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_compose.py --cycles model-cycles_OS1.13.syx [--machines sampler,refmachine] [--blocks 100]
    python3 tools/emu/test_compose.py --cycles model-cycles_OS1.13.syx --dry      # builds and layouts only, no Unicorn
"""
import argparse
import pathlib
import shutil
import struct
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_syntakt_machines as TS  # noqa: E402
from test_sdvintage_7th import UI, check, fill_records, REC_LEN, SCRATCH  # noqa: E402

SELECTIONS = [["sampler"], ["refmachine"], ["sampler", "refmachine"], ["refmachine", "sampler"],
              ["refmachine2"], ["sampler", "refmachine2"], ["sampler", "refmachine", "refmachine2"]]
POOL = (0x43800000, 0x46700000)          # SAMPLE's sample pool (its memory.ram claim), mapped empty in the voice loop
MUTED = 0x7f                             # a machine no build has: the voice loop renders nothing on that track


def built(stock, ids, registrar="runtime"):
    """The composed tweak, the patched MAIN OS followed by its packed payload (what the image holds), and the
    payload as the boot hook leaves it in memory."""
    tweak, info = compose.compose(stock, ids, registrar=registrar)
    patched, _ = build.apply_writes(stock, [tweak])
    runtime = build.payload_runtime(tweak, stock, None)
    packed = build.payload_image(tweak, runtime)
    return tweak, info, bytes(patched) + packed, runtime


def code_ranges(tweak):
    """The payload's code as the composer placed it: the packages' code and tables, and the runtime."""
    return [(int(p["dest"], 16), int(p["dest"], 16) + len(p["hex"]) // 2) for p in tweak["append"]["parts"]
            if "hex" in p and int(p["dest"], 16) <= gs.STUBS]


def configure(ids):
    """test_syntakt_machines.py's view of the build: the added machines from their manifests, the layout of the
    alone payload (gs.LAYOUT), records RECS + 0x60 i; machines out of range are protected (SAFE)."""
    mans = [compose.load_manifest(i) for i in ids]
    added = []
    for i, m in enumerate(mans):
        mc = m["_machine"]
        knobs = tuple((k["long"], k["short"], k["default"]) + ((k["min"], k["max"]) if "min" in k else ())
                      for k in mc["knobs"])
        added.append(dict(name=mc["name"], label=mc["name"], code=m["id"], index=6 + i, image=mc["image"],
                          decay=mc["decay_default"], knobs=knobs))
    gs.set_base(gs.PAY_ALONE)
    gs.set_rows(len(added))
    TS.ADDED, TS.N = added, len(added)
    TS.NM, TS.TOP = 6 + TS.N, 5 + TS.N
    TS.FIRST = {6 + i: 76 + 5 * i for i in range(TS.N)}
    TS.REC = {6 + i: gs.RECS + 0x60 * i for i in range(TS.N)}
    TS.ROWS, TS.CCROWS = gs.ROWSN, gs.CCROWSN
    TS.NAMES = ["Kick", "Snare", "Metal", "Perc", "Tone", "Chord"] + [m["name"] for m in added]
    TS.SAFE = True
    return added


# --- 3. the runtime against B1 ------------------------------------------------------------------------------------
def probe(img, runtime):
    """What the OS's functions that go through the detours return, for every input worth trying."""
    out, bad = {}, []
    u = UI(img, runtime)

    def c(fn, *a):
        r = u.call(fn, *a)
        bad.extend(u.bad)
        return r
    c(0x4005a274)                                                   # the parameter tables, at boot
    lo, hi = t7.BSS_TABLES
    out["tables"] = bytes(u.uc.mem_read(lo, hi - lo))
    out["rows"] = bytes(u.uc.mem_read(TS.ROWS, TS.NM * 32)) + bytes(u.uc.mem_read(TS.CCROWS, TS.NM * 32))
    last = 76 + 5 * TS.N
    out["slot -> descriptor"] = [c(0x4005a692, s, m) for m in range(TS.NM + 2) for s in range(34)]
    out["own descriptor"] = [c(0x4005a556, i) for i in range(last + 9)]
    out["machine of a descriptor"] = [c(0x4005a50a, i) for i in range(last + 9)]
    out["CC -> descriptor"] = [c(0x4005a8ce, t, m, cc) for t in (0, 5, 6) for m in range(TS.NM + 2) for cc in range(14, 24)]
    out["state per descriptor"] = [c(0x4004df40, i) for i in range(last + 9)]
    out["slot of a descriptor"] = [c(0x4005a4e8, i) for i in range(last + 9)]
    ranges = []
    for i in range(last + 2):
        c(0x4005a65a, i)
        ranges.append(bytes(u.uc.mem_read(SCRATCH, 12)))
    out["ranges and defaults"] = ranges
    out["names"] = [(bytes(u.uc.mem_read(c(0x4000b22a, 0, i), 16)).split(b"\0")[0],
                     bytes(u.uc.mem_read(c(0x4000b208, 0, i), 8)).split(b"\0")[0]) for i in range(76, last)]
    fill_records(u)
    out["record at"] = [c(0x4004df5c, i) for i in list(range(TS.NM + 3)) + [100]]
    out["record of"] = [c(0x4004df76, m) for m in list(range(TS.NM + 2)) + [100]]
    out["records"] = [bytes(u.uc.mem_read(r, REC_LEN)) for r in sorted(set(out["record of"]))]
    this, vec = 0x93900000, 0x93910000
    u.uc.mem_write(vec, struct.pack(">8i", 1, 2, 3, 4, 5, 6, 0, 0))
    u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 24, vec + 24))
    knobs = {}
    for m in list(range(TS.NM + 2)) + [100]:
        u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
        knobs[m] = [c(0x4001e814, this, k, 0, 0) for k in range(2, 16)]
    out["main screen knobs"] = knobs
    out["MACHINES page"] = [t7.drum_select(img, runtime, m)[:3] for m in range(TS.NM)]
    icons = {}
    for m in list(range(TS.NM + 1)) + [100]:
        v = UI(img, runtime)
        v.hooks = {0x40071da4: "image"}
        v.uc.mem_write(0x40fe37f0, struct.pack(">I", 0x92200000))
        fp = t7.STACK - 0x100
        v.uc.mem_write(fp, struct.pack(">II", 0, t7.STOP))
        from unicorn import m68k_const as mk
        v.uc.reg_write(mk.UC_M68K_REG_A6, fp)
        v.uc.reg_write(mk.UC_M68K_REG_A7, fp - 0x80)
        v.uc.reg_write(mk.UC_M68K_REG_D2, m)
        v.uc.reg_write(mk.UC_M68K_REG_A0, 0x91000000)
        v.uc.emu_start(0x400a4dc4, t7.STOP, count=100_000)
        icons[m] = [args[1] for k, args in v.calls if k == "image"]
        bad.extend(v.bad)
    out["small icon"] = icons
    return out, bad


def against_b1(stock, ids, img, runtime):
    if not shutil.which(compose.gx.CROSS + "as"):
        print(f"  skip  runtime against B1: no {compose.gx.CROSS}as here to assemble B1's detours")
        return
    _, _, img1, runtime1 = built(stock, ids, registrar="b1")
    a, bad_a = probe(img1, runtime1)
    b, bad_b = probe(img, runtime)
    diff = [k for k in a if a[k] != b[k]]
    check(not diff and not bad_a and not bad_b,
          f"runtime = B1's detours, input for input: {', '.join(a)}" + (f"; DIFFERENT: {', '.join(diff)}" if diff else "")
          + (f"; access outside memory {[hex(x) for x in (bad_a + bad_b)[:4]]}" if bad_a or bad_b else ""))


# --- 4. the voice loop ----------------------------------------------------------------------------------------
def engine(img, runtime=None, tweak=None):
    if runtime is None:
        e = E.Engine(img)
    else:
        e = E.Engine(img, payload=(E.PAYLOAD_DST, runtime), payload_code=code_ranges(tweak))
        e.uc.mem_map(POOL[0], POOL[1] - POOL[0])
    for t in range(6):
        e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", MUTED))
    return e


def play(e, track, machine, knobs, decay, blocks, note=60):
    e.set(track, machine=machine, note=note, pitch=64, finetune=64, color=knobs[0], shape=knobs[1], sweep=knobs[2],
          contour=knobs[3], punch=0, gate=0, decay=decay)
    return e.render(blocks, trig_at=(1,), track=track)


def voice_loop(stock, builds, blocks):
    """builds: selection key -> (tweak, img, runtime, added)."""
    plays = {"refmachine": "REF", "refmachine2": "REF2"}          # the reference machines, with their default knobs
    out = {code: {} for code in plays}
    for key, (tweak, img, runtime, added) in builds.items():
        for m in added:
            e = engine(img, runtime, tweak)
            x = play(e, 0, m["index"], [k[2] for k in m["knobs"]], m["decay"], blocks)
            if m["code"] in plays:
                out[m["code"]][key] = (m["index"], x)
                check(np.max(np.abs(x)) > 1e6 and not e.unmapped,
                      f"{key}: {plays[m['code']]} (machine {m['index']}) plays, peak {np.max(np.abs(x)):.3g}, "
                      "no access outside memory")
            elif m["code"] == "sampler":
                check(not x.any() and not e.unmapped,
                      f"{key}: SAMPLE (machine {m['index']}) with no sample loaded: silent, no access outside memory")
    for code, got in out.items():
        if len(got) > 1:
            (k0, (i0, x0)), *rest = got.items()
            check(all(np.array_equal(x0, x) for _, (_, x) in rest),
                  f"{plays[code]} identical sample for sample as machine {i0} ({k0}) and as machine "
                  + ", ".join(f"{i} ({k})" for k, (i, _) in rest))
    if out["refmachine"] and out["refmachine2"]:
        x1, x2 = next(iter(out["refmachine"].values()))[1], next(iter(out["refmachine2"].values()))[1]
        check(not np.array_equal(x1, x2), "REF2 does not sound like REF: a triangle, not REF's parabola")
    snare = (0, 127, 8, 0)
    e = engine(stock)
    x = play(e, 1, 1, snare, 40, blocks)
    for key, (tweak, img, runtime, added) in builds.items():
        f = engine(img, runtime, tweak)
        y = play(f, 1, 1, snare, 40, blocks)
        check(np.array_equal(x, y) and np.max(np.abs(x)) > 1e6 and not f.unmapped,
              f"{key}: SNARE on track 1 identical to the stock OS, sample for sample")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--blocks", type=int, default=100, help="blocks of 32 frames per sound")
    ap.add_argument("--dry", action="store_true", help="build and lay out the selections only, no emulation")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    builds = {}
    for ids in selections:
        key = "+".join(ids)
        tweak, info, img, runtime = built(stock, ids)
        added = configure(ids)
        print(f"\n{key}: " + ", ".join(f"{m['name']} = machine {m['index']}" for m in added)
              + f"; payload {len(runtime)} bytes at {E.PAYLOAD_DST:#x}, {len(img) - E.IMAGE_LEN} in the image, "
              f"code {', '.join(f'{a:#x}..{b:#x}' for a, b in code_ranges(tweak))}")
        builds[key] = (tweak, img, runtime, added)
        if args.dry:
            continue
        print("start-up")
        X.bootstrap_depack_ok(args.cycles, tweak, None) or t7.FAIL.append(f"{key}: bootstrap")
        X.boot_hook_ok(img, runtime) or t7.FAIL.append(f"{key}: boot hook")
        print("the registrar's mechanics (test_syntakt_machines.py)")
        a, b = TS.tables(stock, img, runtime)
        TS.lookups(a, b)
        TS.accessors(a, b, stock, img)
        TS.screens(stock, img, runtime)
        TS.setter_and_wheel(stock, img, runtime)
        TS.records_and_change(stock, img, runtime)
        TS.out_of_range(stock, img, runtime)
        TS.small_icon(stock, img, runtime)
        print("the runtime against B1")
        against_b1(stock, ids, img, runtime)
    if args.dry:
        print("\n(dry run: no emulation)")
        return 0
    print("\nthe voice loop")
    voice_loop(stock, builds, args.blocks)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
