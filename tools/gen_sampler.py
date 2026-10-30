#!/usr/bin/env python3
"""Generates the tweak of the SAMPLE machine: Cycles One-Shot, a one-shot sampler for samples on the +Drive, as an
added machine of the Model:Cycles.

  - 27-sampler.json: 7th machine, after the 6 stock ones.

The code is Cycles One-Shot's (durchgemacht, MIT: tools/machines/sampler/LICENSE, copied next to the tweaks as
LICENSE-One-Shot), taken as is from https://github.com/durchgemacht/cycles-one-shot at tag v0.12 (UPSTREAM_COMMIT below; 0.8 made the
patch points SAMPLE_MACHINE and DESC_START symbols behind CM_SYMBOLS in pool.h and view.c, and gave each assembly
file a section of its own, for builders like this one; 0.9 split the bar above the waveform into the pattern's
number and the sample's name; 0.10 puts a column on the left with the pattern's number, the track's number and its
level; 0.11 loops and plays in reverse on two switches, RETRIG + PUNCH and RETRIG + GATE, which it reads only when
built with SMP_SWITCHES, as the manifest builds it here; 0.12 shows the whole view for a held trig while Start or
Length turns, its locks marked, and so takes NoteVelocityView's draw too), with the same paths as there: src/ the sound core
(6-tap polyphase interpolation at 96 kHz, the Model:Samples' filter), machine/ the bridge to the voice loop, the
sample memory (loaded from the +Drive, chosen in the PRESET browser, saved with the sound), the waveform view and
the hooks. The build recipe is tools/machines/sampler/manifest.json; the compiled object sampler.o is committed next
to it and placed by tools/relocate.py (notes/60). What differs from One-Shot's own build (its machine/build.py) is
that and the file name, the English name and description, and the "version" and "source" fields. The tweak carries, of the OS, only the short stock bytes ("old") that check the
official file; the descriptor table is copied at build time from YOUR file ("cycles" recipe, as for MACRO).

The tweak is SAMPLE alone as tools/compose.py composes it, and so as the web flasher builds it (notes/61), as
tools/gen_refmachine.py makes REF2's. The mechanics are MACRO's and ACID's (notes/43, notes/54): the same moved
tables, the same place in the payload (0x43000000), the same detours, but assembled once as the registrar runtime and
fed a parameter block per build (notes/60). SAMPLE's own hooks follow, from the manifest: the browser's file open, the
sound record save (two versions) and load, the screen's redraw, and the draw methods of the main screen, of the
knob view and of NoteVelocityView (vtable entries). Since 0.11 SAMPLE declares the two switches, so the builder's shortcut layer comes with it
(notes/63 §16): the press, the LEDs, and k 32 saved in record slot 18, with SAMPLE's record wrappers chained behind the
layer's. The sample pool is the RAM from 8 MB above the payload window to Model-TG's window (0x43800000..0x46700000,
47 MB; POOL below): a combined build whose payload ends above POOL[0] must move it.

What this tweak conflicts with is computed, not listed by hand, as compose.py computes it: every other tweak of the
folder that writes other bytes to the same address, or whose payload runs in SAMPLE's payload window or in its pool
(the machine-adding tweaks, Model-TG, the track filter), every one whose declared claims clash with SAMPLE's or the
layer's (lfo-plus keeps LFO 2 in k 28..32, notes/65), plus sample-preview by name (it plays sample files from the same
browser and needs Model-TG). Rerun this generator when a tweak is added, so that the list stays current (--check says
so).

MACRO's and ACID's optional writes (usb_steady, voice_loop) are left out, as in One-Shot's own build. One-Shot's own
build has no shortcut layer and no SMP_SWITCHES: it plays one shot, forward.

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

UPSTREAM = "https://github.com/durchgemacht/cycles-one-shot"
UPSTREAM_TAG, UPSTREAM_COMMIT = "v0.12", "c32c49d6e215bad00adda48b88ce71aeaeda545f"
VERSION = "0.12"

POOL = (0x43800000, 0x46700000)
# The build recipe (sources, flags, defines, patch points, symbols to keep) is the manifest's,
# tools/machines/sampler/manifest.json: this generator compiles it into the committed object sampler.o and places
# that object with tools/relocate.py, exactly as tools/compose.py does for any build (notes/60 §2, §3).
BSS_OFF = gm.BSS_OFF               # as MACRO: variables above the moved tables (gs.LAYOUT)
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


def build_tweak(img, check=False):
    """The tweak: SAMPLE alone as compose.py composes it (the registrar runtime with a parameter block for this
    build, notes/60 §5; SAMPLE's hooks and view entries; the shortcut layer for its two switches, notes/63 §16), at
    the alone payload window, with compose.py's conflicts. The object is compiled first (written, or compared with
    --check), and compose.py places that object."""
    pay = gs.PAY_ALONE
    gs.set_base(pay)
    with tempfile.TemporaryDirectory() as d:
        blob, syms, bss_end, bad = compile_machine(pathlib.Path(d), pay, pay + BSS_OFF, gs.STUBS, 6, 76, check)
    if bss_end > POOL[0]:
        raise SystemExit(f"!! the payload ends at {bss_end:#x}, inside the sample pool ({POOL[0]:#x}): move POOL")
    composed, _ = compose.compose(img, ["sampler"])
    if composed["symbols"]["sampler_update"] != f"{syms['sampler_update']:#x}":
        raise SystemExit("!! compose.py placed SAMPLE elsewhere than its own layout")
    out = {
        "id": "sampler",
        "order": ORDER,
        "name": "SAMPLE machine: sampler for samples on the +Drive, one shot or loop, forward or reverse "
                "(Cycles One-Shot %s)" % VERSION,
        "description": [
            "7th machine after the 6 stock ones, registered like MACRO and ACID through the registrar runtime",
            "(tools/machines/registrar/, notes/60) with a parameter block for this build. Plays a",
            "sample from the +Drive once per trig: 6-tap polyphase interpolation at 96 kHz, the stock decimator, the",
            "amp chain set up like TONE, then the Model:Samples' filter. The sample is chosen for a SAMPLE track in",
            "the PRESET browser (FUNC + MACHINE) and saved with the sound; stereo files play as mono, other rates at",
            "their pitch. COLOR = Start, SHAPE = Length (0..120 each, as on the Model:Samples; the trig ends at",
            "Start + Length), SWEEP = Cutoff (-64 .. 63: lowpass below 0, off at 0, highpass above), CONTOUR = Reso;",
            "DECAY, GATE and PUNCH: the stock amp chain. RETRIG + PUNCH = Loop (a hard seam, as on the",
            "Model:Samples), RETRIG + GATE = Reverse (from the next trig), two switches of the builder's shortcut",
            "layer (notes/63 §16), saved with the sound. A trig that cuts a sounding note brings the new one in over",
            "0.67 ms. On a SAMPLE track the main screen shows a column with the pattern's number, the track's number",
            "and its level, the sample's name with L and R while the switches are on, and the waveform with the start",
            "and end marked.",
            "Code of Cycles One-Shot %s (durchgemacht, MIT, %s, tag %s), copied as is into tools/machines/sampler/,"
            % (VERSION, UPSTREAM, UPSTREAM_TAG),
            "compiled once with CM_SYMBOLS and SMP_SWITCHES into sampler.o and placed by tools/relocate.py (notes/60).",
            "Samples live in %#x..%#x (%d MB); the payload runs at %#x. Conflicts computed by tools/compose.py:"
            % (POOL[0], POOL[1], (POOL[1] - POOL[0]) >> 20, pay),
            "other bytes at the same address, a payload in SAMPLE's window or pool, or declared claims that clash.",
            "Generated by tools/gen_sampler.py.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "version": VERSION,
        "source": f"{UPSTREAM}/tree/{UPSTREAM_COMMIT}",
        "conflicts": composed["conflicts"],
        "writes": composed["writes"],
        "append": composed["append"],
        "symbols": composed["symbols"],             # for the proofs: the bridge, the hooks, the view, the layer
    }
    build.apply_writes(img, [out])            # a bad "old" fails here, not in the user's build
    segs = sum(n for _, n in out["append"]["pack"])
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
