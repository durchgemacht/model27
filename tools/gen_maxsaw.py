#!/usr/bin/env python3
"""Max Saw (notes/84): an added machine, seven sawtooths after Adam Szabo's analysis of the Super Saw
("How to Emulate the Super Saw", BSc thesis, KTH 2010, TRITA-CSC-E 2010:131), written in fixed
point in tools/machines/maxsaw/maxsaw.c and checked against the same model in double on the host (notes/84 §5).

This generator writes the package's tables (tools/machines/maxsaw/maxsaw_tables.h) and compiles its committed
object (tools/machines/maxsaw/maxsaw.o, ld -r of the source: notes/60 §2). The tables are computed here from
Szabo's published formulas, nothing is taken from any firmware: his table 1 (the six side oscillators' offsets), his
11th-degree detune polynomial (p. 12) and his two mix polynomials (p. 15), each at the knob's 128 values; the 2-pole
state-variable high-pass's coefficients (TPT, Butterworth: our choice, Szabo names no kind) at the cutoff notes -36 to
140; exp2. The knobs' ranges are the maintainer's choices of 2026-11-16 (notes/84 §7): Tone 16 steps an octave with
Szabo's cutoff at 32, Phase the random phases' width; the Sub's level the listening page's (notes/84 §13), computed
here from its filtered sawtooth in double. With --cycles it also composes the machine alone through
tools/compose.py, which places the object with tools/relocate.py as any build does, into
tweaks/model-cycles_OS1.13/85-maxsaw.json: the card's build alone, which the web flasher composes in the page.

    python3 tools/gen_maxsaw.py [--check]                                           # tables and object
    python3 tools/gen_maxsaw.py --cycles firmware/model-cycles_OS1.13.syx [--check]   # and the card's tweak
    python3 tools/gen_maxsaw.py --tables-only [--check]                             # no toolchain
"""
import argparse
import json
import math
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PKG = HERE / "machines" / "maxsaw"
TABLES = PKG / "maxsaw_tables.h"

SR = 48000.0
# Szabo, table 1 (p. 9): oscillator n's frequency over the centre's, written 1 +- offset; osc 4 is the centre
OFFSETS = (-0.11002313, -0.06288439, -0.01952356, 0.0, 0.01991221, 0.06216538, 0.10745242)
# Szabo, p. 12: the detune curve, x = knob / 127 (0 .. 1), highest power first
DETUNE_POLY = (10028.7312891634, -50818.8652045924, 111363.4808729368, -138150.6761080548, 106649.6679158292,
               -53046.9642751875, 17019.9518580080, -3425.0836591318, 404.2703938388, -24.1878824391, 0.6717417634,
               0.0030115596)
# Szabo, p. 15: the mix, x = knob / 127
MIX_CENTRE = (-0.55366, 0.99785)                  # y = -0.55366 x + 0.99785
MIX_SIDE = (-0.73764, 1.2841, 0.044372)           # y = -0.73764 x^2 + 1.2841 x + 0.044372
SVF_K = math.sqrt(2.0)                            # the 2-pole high-pass: Butterworth (Q = 1 / sqrt 2)
TONE_AT, TONE_STEPS = 32, 16                      # Tone: Szabo's cutoff (the fundamental) at 32, 16 steps an octave
HP_LO, HP_HI = -36, 140                           # the cutoff's note range (0.45 x 48 kHz is note 135.6)
SUB_RMS = 1 / math.sqrt(2)                        # the Sub's level: the RMS of a sine of height 1 (notes/84 §13)


def poly(c, x):
    y = 0.0
    for a in c:
        y = y * x + a
    return y


def detune_curve(k):
    return poly(DETUNE_POLY, k / 127)


def mix_gains(k):
    x = k / 127
    return poly(MIX_CENTRE, x), poly(MIX_SIDE, x)


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def svf(n):
    """the 2-pole state-variable high-pass (TPT) at the cutoff note n, 48 kHz: a1, a2, a3"""
    g = math.tan(math.pi * min(note_hz(n), 0.45 * SR) / SR)
    a1 = 1 / (1 + g * (g + SVF_K))
    return a1, g * a1, g * g * a1


def sub_gain():
    """The Sub's gain (notes/84 §13): its naive sawtooth (height 1, phase 0 its middle, rising) two octaves below note
    60, through the 2-pole low-pass (TPT, the coefficients of svf) at the note, has this RMS times the gain = SUB_RMS,
    as the listening page set it; in double over 3 s after 1 s. The low-pass follows the note, so the ratio holds at
    every note (to the bilinear transform's warping)."""
    f = note_hz(60) / 4
    a1, a2, a3 = svf(60)
    ph = s1 = s2 = acc = 0.0
    n = 0
    for i in range(int(4 * SR)):
        x = 2 * ph if ph < 0.5 else 2 * ph - 2
        ph = (ph + f / SR) % 1.0
        v3 = x - s2
        v1 = a1 * s1 + a2 * v3
        v2 = s2 + a2 * s1 + a3 * v3
        s1, s2 = 2 * v1 - s1, 2 * v2 - s2
        if i >= SR:
            acc += v2 * v2
            n += 1
    return SUB_RMS / math.sqrt(acc / n)


def q(x, bits):
    return int(round(x * (1 << bits)))


def q31(x):
    return max(min(q(x, 31), 0x7fffffff), -0x80000000)


def arr(name, ctype, vals, per_line=8):
    rows = [", ".join(str(v) for v in vals[i:i + per_line]) for i in range(0, len(vals), per_line)]
    return f"static const {ctype} {name}[{len(vals)}] = {{\n\t" + ",\n\t".join(rows) + "\n};"


def tables():
    out = ["/* Max Saw's tables (notes/84), generated by tools/gen_maxsaw.py from Adam Szabo's description of the Super",
           " * Saw (KTH 2010): do not edit. */", "#ifndef MAXSAW_TABLES_H", "#define MAXSAW_TABLES_H",
           "#include <stdint.h>", ""]
    consts = [
        ("L2_440", q(math.log2(440.0), 24), "log2 440 Hz, Q24"),
        ("L2_INC", q(math.log2(2 ** 32 / SR), 24), "log2 (2^32 / 48 kHz): Hz to the phase increment, Q24"),
        ("Q_TWELFTH", q31(1 / 12), "1/12, Q31: semitones to octaves"),
        ("SVF_KM1", q31(SVF_K - 1), "k - 1 of the 2-pole high-pass, Q31 (k = sqrt 2)"),
        ("HP_LO", HP_LO, "the high-pass tables' first cutoff note"),
        ("HP_N", HP_HI - HP_LO + 1, "their entries (notes HP_LO .. HP_HI), plus a guard"),
        ("TONE_AT", TONE_AT << 8, "Tone (8.8) where the cutoff is the fundamental (Szabo)"),
        ("TONE_Q16", (12 << 16) // TONE_STEPS // 256, "semitones << 16 a Tone step of 1/256: 12 / 16 x 2^16 / 2^8"),
        ("PHASE_K", (1 << 31) // (127 << 8), "Phase (8.8) to the random phases' width, Q31: 2^31 / 32512"),
        ("SUB_GAIN", q(sub_gain(), 27), "the Sub's filtered sawtooth to a sine's RMS of height 1, Q27 (notes/84 §13)"),
    ]
    for k, v, why in consts:
        out.append(f"#define {k} {v}\t/* {why} */")
    out.append("")
    out.append(arr("OFF_T", "int32_t", [q31(o) for o in OFFSETS], 7)
               + "\t/* Szabo table 1: each oscillator's offset, Q31 (osc 4, the centre, 0) */")
    det = [q31(detune_curve(k)) for k in range(128)]
    out.append(arr("DETY_T", "int32_t", det + det[-1:]) + "\t/* Szabo's detune curve at knob 0 .. 127, Q31 */")
    mc = [q31(mix_gains(k)[0]) for k in range(128)]
    ms = [q31(mix_gains(k)[1]) for k in range(128)]
    out.append(arr("MIXC_T", "int32_t", mc + mc[-1:]) + "\t/* Szabo: the centre's gain at mix 0 .. 127, Q31 */")
    out.append(arr("MIXS_T", "int32_t", ms + ms[-1:]) + "\t/* Szabo: each side oscillator's gain, Q31 */")
    hp = [svf(n) for n in range(HP_LO, HP_HI + 1)]
    hp.append(hp[-1])
    whys = ("a1 = 1 / (1 + g (g + k)), g = tan(pi f / fs)", "a2 = g a1", "a3 = g a2")
    for j, (nm, why) in enumerate(zip(("SVA1_T", "SVA2_T", "SVA3_T"), whys)):
        out.append(arr(nm, "int32_t", [q31(h[j]) for h in hp])
                   + f"\t/* the high-pass at cutoff note {HP_LO} .. {HP_HI}: {why}, Q31 */")
    out.append(arr("EXP2_T", "uint32_t", [q(2 ** (i / 256), 30) for i in range(257)]) + "\t/* 2^(i / 256), Q30 */")
    out.append("\n#endif")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx: also compose the machine alone, the card's tweak")
    ap.add_argument("--tables-only", action="store_true", help="the tables, without the toolchain")
    ap.add_argument("--check", action="store_true", help="checks that the committed files match")
    args = ap.parse_args()
    import gen_macro as gm             # noqa: E402
    bad = bool(gm.emit(TABLES, tables(), args.check))
    if not args.tables_only:
        import compose                 # noqa: E402
        m = compose.load_manifest("maxsaw")
        with tempfile.TemporaryDirectory() as d:
            obj = compose.build_object(m, pathlib.Path(d))
        bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
        if args.cycles:
            import gen_sdvintage_exact as gx   # noqa: E402
            import gen_sdvintage_7th as g7     # noqa: E402
            img = g7.cycles_main(args.cycles)
            if len(img) != gx.IMAGE_LEN:
                raise SystemExit("!! not the official MAIN OS 1.13")
            tweak, info = compose.compose(img, ["maxsaw"])
            tweak["description"].append("Generated by tools/gen_maxsaw.py through tools/compose.py (notes/84).")
            bad |= bool(gm.emit(compose.DEV / "85-maxsaw.json",
                                json.dumps(tweak, indent=1, ensure_ascii=False) + "\n", args.check))
            p = info["packages"][0]
            print(f"  maxsaw: {len(tweak['writes'])} writes, code {p['code']} bytes, variables {p['bss']} bytes, "
                  f"{info['image']} bytes added to the image, {len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
