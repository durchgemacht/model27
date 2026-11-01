#!/usr/bin/env python3
"""Generates Reso, a tuned resonator as effect 4 of the Track FX (the filter slot, notes/75,
tools/machines/reso/): writes its tables into tools/machines/reso/reso_tab.h, compiles reso.c with the manifest's
recipe into tools/machines/reso/reso.o (ld -r, notes/60 §2), then composes it alone through tools/compose.py, which
places that object with tools/relocate.py as any build does, into tweaks/model-cycles_OS1.13/75-reso.json: the card's
build alone, which the web flasher composes in the page (its excludes come from that tweak's conflicts). Needs the
m68k toolchain (for the object); the tables and compose.py do not.

    python3 tools/gen_reso.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import math
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compose                     # noqa: E402
import gen_macro as gm             # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402

PACKAGE = "reso"
TABLE = compose.MACHINES / PACKAGE / "reso_tab.h"
OUT = compose.DEV / "75-reso.json"
SR = 48000
T60 = (0.02, 10.0)                 # Decay 0 and 127, seconds; exponential between
DAMP = (4.0, 256.0)                # Tone 0 and 127: the damping's cutoff, harmonics of the pitch; none at 127
ONE = 2 ** 31 - 1


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def q31(v):
    return min(ONE, round(v * 2 ** 31))


def tables():
    """name -> (C type, values): the pitch, the damping (Tone) and the decay by value (0 .. 128, the last one for the
    interpolation of 127), the allpass by its fraction, and the functions."""
    L = [round(SR / note_hz(n) * 4096) for n in range(129)]                     # the period, frames in 20.12
    half = [math.pi * note_hz(n) / SR for n in range(129)]                      # w0 / 2, radians
    lo, hi = DAMP
    top = math.atan(1 / hi)
    phi = [max(0.0, math.atan(1 / (lo * (hi / lo) ** (b / 127))) - top * b / 127) if b < 127 else 0.0
           for b in range(129)]                                                 # the damping's phase at the pitch
    t0, t1 = T60
    E = [round(math.log2(1000) / (SR * t0 * (t1 / t0) ** (d / 127)) * 2 ** 37) for d in range(129)]   # 1/T60, Q37
    ETA = [q31((1 - d) / (1 + d)) for d in (0.5 + k / 64 for k in range(65))]  # the allpass, delay 0.5 .. 1.5
    EXP = [q31(2 ** (-k / 256)) for k in range(257)]                            # 2^(-k/256), Q31
    SQRT = [q31(math.sqrt(k / 256)) for k in range(257)]                        # sqrt(k/256), Q31
    return {"RESO_L": ("uint32_t", L), "RESO_SH": ("int32_t", [q31(math.sin(h)) for h in half]),
            "RESO_CH": ("int32_t", [q31(math.cos(h)) for h in half]),
            "RESO_P": ("uint32_t", [round(p / (2 * math.pi) * 2 ** 32) for p in phi]),
            "RESO_SP2": ("int32_t", [q31(math.sin(p / 2)) for p in phi]),
            "RESO_CP2": ("int32_t", [q31(math.cos(p / 2)) for p in phi]),
            "RESO_E": ("uint32_t", E), "RESO_ETA": ("int32_t", ETA), "RESO_EXP": ("int32_t", EXP),
            "RESO_SQRT": ("int32_t", SQRT)}


def header():
    out = ["/* Reso's tables (notes/75 §3), written by tools/gen_reso.py. By value 0 .. 128 (the last for the",
           " * interpolation of 127): RESO_L the period of note n, 48000 / f(n) frames in 20.12 (f(n) = 440 * 2^((n - 69) / 12),",
           " * Pitch is the MIDI note), RESO_SH and RESO_CH sin and cos of half its pitch, w0 / 2 = pi f(n) / 48000;",
           " * RESO_P the damping's phase P at the pitch in turns by Tone, Q32:",
           f" * atan(1 / R) / 2pi with R = {DAMP[0]:g} * {DAMP[1] / DAMP[0]:g}^(b / 127) harmonics, less its value at 127 times b / 127,",
           " * 0 at 127 (no damping), RESO_SP2 and RESO_CP2 sin and cos of half of it; RESO_E log2(1000) / (48000 * T60) by",
           f" * Decay, Q37, T60 = {T60[0]:g} * {T60[1] / T60[0]:g}^(d / 127) s. RESO_ETA the allpass (1 - D) / (1 + D) for a delay",
           " * D = 0.5 + k/64 frames; RESO_EXP 2^(-k/256), RESO_SQRT sqrt(k/256); all Q31. */",
           "#ifndef RESO_TAB_H", "#define RESO_TAB_H", "#include <stdint.h>", ""]
    for name, (ctype, vals) in tables().items():
        rows = [", ".join(f"{v:10d}" for v in vals[i:i + 8]) for i in range(0, len(vals), 8)]
        out.append(f"static const {ctype} {name}[{len(vals)}] = {{\n\t" + ",\n\t".join(rows) + "\n};\n")
    out.append("#endif")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--check", action="store_true", help="checks that the committed tables, object and tweak match")
    args = ap.parse_args()
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! not the official MAIN OS 1.13")
    bad = bool(gm.emit(TABLE, header(), args.check))
    m = compose.load_manifest(PACKAGE)
    with tempfile.TemporaryDirectory() as d:
        obj = compose.build_object(m, pathlib.Path(d))
    bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
    tweak, info = compose.compose(img, [PACKAGE])
    tweak["description"].append("Generated by tools/gen_reso.py through tools/compose.py (notes/75).")
    bad |= bool(gm.emit(OUT, json.dumps(tweak, indent=1, ensure_ascii=False) + "\n", args.check))
    p, f = info["packages"][0], info["filters"]
    print(f"  {PACKAGE}: {len(tweak['writes'])} writes, code and tables {p['code']} bytes, variables {p['bss']} bytes, "
          f"the filter slot {f['code'] + f['data']} bytes, {info['image']} bytes added to the image, "
          f"{len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
