#!/usr/bin/env python3
"""Generates the tweak of the SAMPLE machine: Cycles One-Shot, a one-shot sampler for samples on the +Drive, as an
added machine of the Model:Cycles.

  - 27-sampler.json: 7th machine, after the 6 stock ones.

The code is Cycles One-Shot's (durchgemacht, MIT: tools/machines/sampler/LICENSE, copied next to the tweaks as
LICENSE-One-Shot), taken as is from https://github.com/durchgemacht/cycles-one-shot at tag v0.9 (UPSTREAM_COMMIT below; 0.8 made the
patch points SAMPLE_MACHINE and DESC_START symbols behind CM_SYMBOLS in pool.h and view.c, and gave each assembly
file a section of its own, for builders like this one; 0.9 splits the bar above the waveform into the pattern's
number and the sample's name), with the same paths as there: src/ the sound core
(6-tap polyphase interpolation at 96 kHz, the Model:Samples' filter), machine/ the bridge to the voice loop, the
sample memory (loaded from the +Drive, chosen in the PRESET browser, saved with the sound), the waveform view and
the hooks. The build recipe is tools/machines/sampler/manifest.json; the compiled object sampler.o is committed next
to it and placed by tools/relocate.py (notes/60). What differs from One-Shot's own build (its machine/build.py) is
that and the file name, the English name and description, and the "version" and "source" fields. The tweak carries, of the OS, only the short stock bytes ("old") that check the
official file; the descriptor table is copied at build time from YOUR file ("cycles" recipe, as for MACRO).

The mechanics are MACRO's and ACID's (notes/43, notes/54): the same moved tables, the same place in the payload
(0x43000000), the same detours, but assembled once as the registrar runtime and fed a parameter block per build
(compose.registrar_writes, notes/60) instead of gen_macro.added_machine assembling them for each tweak. SAMPLE's own hooks follow: the browser's file open, the sound record save
(two versions) and load, the screen's redraw, and the draw methods of the main screen and of the knob view (vtable
entries). The sample pool is the RAM from 8 MB above the payload window to Model-TG's window
(0x43800000..0x46700000, 47 MB; POOL below): a combined build whose payload ends above POOL[0] must move it.

What this tweak conflicts with is computed, not listed by hand: every other tweak of the folder that writes other
bytes to the same address, or whose payload runs in SAMPLE's payload window or in its pool (the machine-adding
tweaks, Model-TG, the track filter), plus sample-preview by name (it plays sample files from the same browser and
needs Model-TG). Rerun this generator when a tweak is added, so that the list stays current (--check says so).

MACRO's and ACID's optional writes (usb_steady, voice_loop) are left out, as in One-Shot's own build. The MAIN OS
differs from the one One-Shot's own build gives (0.9's, tested on a Model:Cycles on 2026-10-24) only where the patch
points are read: move.l #symbol instead of moveq, three sites.

    python3 tools/gen_sampler.py --cycles model-cycles_OS1.13.syx [--check]

The committed object and JSON are compiled with m68k-elf-gcc 16.2 (Homebrew); another GCC can give other bytes, and
--check says so (it names the compiler of the committed object).
"""
import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import compose                     # noqa: E402
import gen_macro as gm             # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402

DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "27-sampler.json"
LICENSE_OUT = DEV / "LICENSE-One-Shot"
SRC = HERE / "machines" / "sampler"
BASE = build.BASE

UPSTREAM = "https://github.com/durchgemacht/cycles-one-shot"
UPSTREAM_TAG, UPSTREAM_COMMIT = "v0.9", "4f8c7b52908a9c67c8b9f02f4de05dccbf086f40"
VERSION = "0.9"

# The machine, as One-Shot's machine/build.py declares it: knobs COLOR, SHAPE, SWEEP, CONTOUR = (long name, short
# name, default[, min, max]); Start and Length run to 120 as on the Model:Samples; decay = default of its Amp Decay;
# image = the picture it borrows (the OS has only 6; 4 = TONE).
MACHINE = dict(name="SAMPLE", image=4, decay=127,
               knobs=(("Start", "STRT", 0, 0, 120), ("Length", "LEN", 120, 0, 120), ("Cutoff", "FREQ", 64),
                      ("Reso", "RESO", 0)))
POOL = (0x43800000, 0x46700000)
# The build recipe (sources, flags, defines, patch points, symbols to keep) is the manifest's,
# tools/machines/sampler/manifest.json: this generator compiles it into the committed object sampler.o and places
# that object with tools/relocate.py, exactly as tools/compose.py does for any build (notes/60 §2, §3).
BSS_OFF = gm.BSS_OFF               # as MACRO: variables above the moved tables (gs.LAYOUT)
# SAMPLE's hooks: (address, stock bytes, "jsr" or "jmp", symbol). A jmp replaces the first 8 bytes of a function
# (lea -12(sp),sp ; movem.l a2-a4,(sp)), which the hook runs itself (machine/hooks.S).
HOOKS = ((0x400a6602, "4eb9400a3052", "jsr", "smp_hook_open"),       # the browser opens a file
         (0x4005afa0, "4feffff448d71c00", "jmp", "smp_hook_save2"),  # sound -> record, version 2
         (0x4005b054, "4feffff448d71c00", "jmp", "smp_hook_save1"),  # sound -> record, version 1
         (0x4005aecc, "4feffff448d71c00", "jmp", "smp_hook_load"),   # record -> sound
         (0x400075f0, "4eb940076be4", "jsr", "smp_hook_tick"))       # the screen's redraw, about 30 Hz
# SAMPLE's view: (vtable entry, stock method, symbol). Entry +16 is a view's draw method, called by the screen's
# redraw (0x40076c76) with the view and the screen's Bitmap; each entry is the only reference to its method, and
# SAMPLE's calls the stock one for anything else.
VIEWS = ((0x400ffe30, 0x4001b22a, "smp_main_draw"),       # MainScreenView (vtable 0x400ffe20)
         (0x4010053c, 0x4001e40a, "smp_knob_draw"))       # the knob view (vtable 0x4010052c)
EXTRA_CONFLICTS = {"sample-preview", "sample-preview-st"}
ORDER = 27


def compile_machine(tmp, code_at, bss_at, code_end, machine_index, desc_start, check=False):
    """One-Shot's core, table, filter, bridge, sample memory, view and hooks: compiled with the manifest's recipe
    into the package's object (written, or with check compared with the committed one), then placed at code_at
    (code and data) and bss_at (variables) by the relocator, with machine_index and desc_start resolved as the
    patch-point symbols. Returns (bytes from code_at to the end of the data, symbols, end of the variables, check
    result)."""
    m = compose.load_manifest("sampler")
    obj = compose.build_object(m, tmp)
    bad = compose.emit_bytes(compose.object_path(m), obj, check)
    blob, syms, bss_end = compose.place_package(m, code_at, bss_at, code_end,
                                                {"machine_index": machine_index, "descriptor_base": desc_start}, obj)
    return blob, syms, bss_end, bad


def own_writes(img, syms):
    """SAMPLE's hooks and view entries as writes, each checked against the stock bytes."""
    writes = []
    for va, old, op, sym in HOOKS:
        old = bytes.fromhex(old)
        new = (bytes.fromhex("4eb9") + g7.be32(syms[sym]) if op == "jsr"
               else bytes.fromhex("4ef9") + g7.be32(syms[sym]) + bytes.fromhex("4e71"))
        if len(new) != len(old):
            raise SystemExit(f"!! hook at {va:#x}: {len(new)} bytes for {len(old)}")
        if img[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! {va:#x}: {old.hex()} expected, {img[va - BASE:va - BASE + len(old)].hex()} found")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new.hex()})
    for va, method, sym in VIEWS:
        if g7.refs32(img, method) != [va]:
            raise SystemExit(f"!! references to {method:#x}: {[hex(r) for r in g7.refs32(img, method)]}")
        writes.append({"off": va - BASE, "old": g7.be32(method).hex(), "new": g7.be32(syms[sym]).hex()})
    return writes


def computed_conflicts(writes, ram):
    """The ids of the folder's other tweaks this one cannot be installed with: a write of other bytes to the same
    address, or a payload that runs in one of our RAM ranges (the payload window, the pool). The same whole write
    (a sprite mask freed by both) is not a conflict, as in check_overlaps.py."""
    mine = {}
    for w in writes:
        for i, b in enumerate(bytes.fromhex(w["new"])):
            mine[w["off"] + i] = b
    ids = set()
    for f in sorted(DEV.glob("*.json")):
        if f.name in ("device.json", OUT.name):
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        tid = t.get("id")
        if not tid:
            continue
        clash = any(mine.get(w["off"] + i, b) != b
                    for w in t.get("writes", []) for i, b in enumerate(bytes.fromhex(w["new"])))
        ap = t.get("append")
        if ap and not clash:
            lo, hi = int(ap["dest"], 16), int(ap["dest"], 16) + ap["size"]
            clash = any(lo < b and a < hi for a, b in ram)
        if clash:
            ids.add(tid)
    return ids


def build_tweak(img, check=False):
    """The tweak: SAMPLE registered as the 7th machine through the registrar runtime (compose.registrar_writes,
    notes/60 §5: the committed runtime and stub template, a parameter block for this build), at the alone payload
    window, with its own hooks and view entries, and the conflicts computed from the folder's tweaks."""
    pay = gs.PAY_ALONE
    gs.set_base(pay)
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        blob, syms, bss_end, bad = compile_machine(tmp, pay, pay + BSS_OFF, gs.STUBS, 6, 76, check)
        if bss_end > POOL[0]:
            raise SystemExit(f"!! the payload ends at {bss_end:#x}, inside the sample pool ({POOL[0]:#x}): move POOL")
        machine = dict(MACHINE, update=syms["sampler_update"], render=syms["sampler_render"])
    writes, append = compose.registrar_writes(img, [machine], [(pay, blob)], bss_end, compose.load_registrar())
    writes += own_writes(img, syms)
    writes.sort(key=lambda x: x["off"])
    for a_, b_ in zip(writes, writes[1:]):
        if a_["off"] + len(a_["new"]) // 2 > b_["off"]:
            raise SystemExit(f"!! writes overlap at {BASE + b_['off']:#x}")
    conflicts = (computed_conflicts(writes, [(pay, bss_end), POOL]) | EXTRA_CONFLICTS) - {"sampler"}
    out = {
        "id": "sampler",
        "order": ORDER,
        "name": "SAMPLE machine: one-shot sampler for samples on the +Drive (Cycles One-Shot %s)" % VERSION,
        "description": [
            "7th machine after the 6 stock ones, registered like MACRO and ACID through the registrar runtime",
            "(tools/machines/registrar/, notes/60) with a parameter block for this build. Plays a",
            "sample from the +Drive once per trig: 6-tap polyphase interpolation at 96 kHz, the stock decimator, the",
            "amp chain set up like TONE, then the Model:Samples' filter. The sample is chosen for a SAMPLE track in",
            "the PRESET browser (FUNC + MACHINE) and saved with the sound; stereo files play as mono, other rates at",
            "their pitch. COLOR = Start, SHAPE = Length (0..120 each, as on the Model:Samples; the trig ends at",
            "Start + Length), SWEEP = Cutoff (-64 .. 63: lowpass below 0, off at 0, highpass above), CONTOUR = Reso;",
            "DECAY, GATE and PUNCH: the stock amp chain. On a SAMPLE track the main screen shows the pattern's number",
            "and the sample's name in two boxes, and the waveform with the start and end marked.",
            "Code of Cycles One-Shot %s (durchgemacht, MIT, %s, tag %s), copied as is into tools/machines/sampler/,"
            % (VERSION, UPSTREAM, UPSTREAM_TAG),
            "compiled once with CM_SYMBOLS into sampler.o and placed by tools/relocate.py (notes/60).",
            "Samples live in %#x..%#x (%d MB); the payload runs at %#x. Conflicts computed from the other tweaks:"
            % (POOL[0], POOL[1], (POOL[1] - POOL[0]) >> 20, pay),
            "other bytes at the same address, or a payload in SAMPLE's window or pool. Generated by",
            "tools/gen_sampler.py.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "version": VERSION,
        "source": f"{UPSTREAM}/tree/{UPSTREAM_COMMIT}",
        "conflicts": sorted(conflicts),
        "writes": writes,
        "append": append,
        # for the proofs: the entries of the bridge, the hooks and the view
        "symbols": {k: f"{syms[k]:#x}" for k in ("sampler_update", "sampler_render") + tuple(h[3] for h in HOOKS)
                    + tuple(v[2] for v in VIEWS)},
    }
    build.apply_writes(img, [out])            # a bad "old" fails here, not in the user's build
    segs = sum(n for _, n in append["pack"])
    return out, dict(code=len(blob), bss=bss_end - pay - BSS_OFF, image=segs, pay=pay, bss_end=bss_end, bad=bad)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx (without it: only the license file)")
    ap.add_argument("--check", action="store_true", help="checks that the committed files match")
    args = ap.parse_args()
    bad = gm.emit(LICENSE_OUT, (SRC / "LICENSE").read_text(encoding="utf-8"), args.check)
    if args.cycles:
        img = g7.cycles_main(args.cycles)
        if len(img) != gx.IMAGE_LEN:
            raise SystemExit("!! not the official MAIN OS 1.13")
        if build.sha(img) != json.loads((DEV / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
            raise SystemExit("!! not the official MAIN OS 1.13 (section 3 hash)")
        tweak, info = build_tweak(img, args.check)
        bad += info["bad"]
        text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
        print(f"  {tweak['id']}: {len(tweak['writes'])} writes, code and tables {info['code']} bytes, variables "
              f"{info['bss']} bytes, {info['image']} bytes added to the image, payload {info['pay']:#x}..{info['bss_end']:#x}, "
              f"pool {POOL[0]:#x}..{POOL[1]:#x}, {len(tweak['conflicts'])} conflicts computed")
        bad += gm.emit(OUT, text, args.check)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
