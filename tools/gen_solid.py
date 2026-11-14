#!/usr/bin/env python3
"""SOLID (notes/71): an added machine, a bank of modes struck by a mallet, a noise burst or sustained noise, its
material gliding from string to glass on SHAPE. Its sound was settled by ear in a float listening prototype (three
rounds with the maintainer, outside the repo); tools/machines/solid/solid.c is its fixed point.

This generator writes the package's tables (tools/machines/solid/solid_tables.h), its own pictures
(tools/machines/solid/solid_pictures.c: the MACHINES page's card, its pixels set by solid_card.c, and icon, the track
icon, the icons from the 1-bit files in tools/machines/solid/pictures/, notes/71 §13) and compiles its committed
object
(tools/machines/solid/solid.o, ld -r of the sources: notes/60 §2). With --cycles it also composes the machine alone
through tools/compose.py, which places that object with tools/relocate.py as any build does, into
tweaks/model-cycles_OS1.13/71-solid.json: the card's build alone, which the web flasher composes in the page (its
excludes come from that tweak's conflicts, notes/71 §12).

The material tables are the prototype's numbers: the first 16 mode ratios of each material, computed there from
textbook physics (a string with a little stiffness, the zeros of the Bessel functions for an ideal membrane, a free
bar after Euler-Bernoulli, a marimba bar with its first three modes tuned, a church bell and a glass approximated),
kept here as decimals; and each material's signature, the level and the relative T60 of each mode at COLOR 64.

    python3 tools/gen_solid.py [--check]                                         # tables and object
    python3 tools/gen_solid.py --cycles firmware/model-cycles_OS1.13.syx [--check]   # and the card's tweak
    python3 tools/gen_solid.py --tables-only [--check]                           # no toolchain
"""
import argparse
import json
import math
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PKG = HERE / "machines" / "solid"
TABLES = PKG / "solid_tables.h"
PICTURES = PKG / "solid_pictures.c"
# SOLID's own pictures (notes/71 §13): the MACHINES page's card (its pixels set on the screen's tick, solid_card.c)
# and icon, the track icon of the preset dialogs; the icons drawn for it in 1 bit (light = lit) and kept in the OS's
# sprite layout, as the 1-Bit Editor saves them
RUNTIME_PICTURES = {"card": "solid_card_px"}

SR = 48000
BLOCK = 32
MAXM = 16                           # modes in the material tables; solid.c plays the first SOLID_MODES
CHOKE_BLOCKS = 5                    # a strike on another note or material damps the body over 5 blocks first
CHOKE_DEPTH = 0.25                  # by 12 dB (the maintainer's choice of round 2, "teilweise")
CONTACT_DAMP = 0.5                  # any other strike halves the ringing body
BURST_GAIN = 0.6                    # the noise burst's energy
GAIN = 0.4                          # the output's gain
CLICK_PEAK = 1.311326813110747      # the expected peak of the click (uniform noise, its first difference): the
                                    # mean over 20 000 clicks, measured in the prototype

# (name, damping factor on T60, the first 16 mode ratios)
MATERIALS = (
    ("String", 1.0, (1.0, 2.000899528, 3.003596764, 4.008987205, 5.017962337, 6.031408346, 7.050204847,
                     8.075223664, 9.107327653, 10.147369574, 11.196191031, 12.254621466, 13.32347723, 14.403560714,
                     15.495659565, 16.600545972)),
    ("Membrane", 0.45, (1.0, 1.593340506, 2.135548787, 2.295417267, 2.653066405, 2.917295455, 3.155464815,
                        3.50014749, 3.598484674, 3.647451179, 4.058931883, 4.13173816, 4.230439128, 4.601044534,
                        4.610051645, 4.831885263)),
    ("Marimba", 0.7, (1.0, 3.98, 9.85, 16.282550356, 24.32332113, 33.972241653, 45.229315823, 58.094543435,
                      72.567924498, 88.649459013, 106.339146979, 125.636988397, 146.542983266, 169.057131587,
                      193.179433359, 218.909888583)),
    ("Bar", 1.0, (1.0, 2.756538507, 5.403917632, 8.932950352, 13.344286694, 18.637887887, 24.813756069,
                  31.871891128, 39.81229307, 48.634961894, 58.339897601, 68.927100191, 80.396569662, 92.748306016,
                  105.982309253, 120.098579372)),
    ("Bell", 1.6, (1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166, 5.433, 6.796, 8.215, 9.67, 11.2123,
                   12.847138, 14.58006628, 16.416970257)),
    ("Glass", 1.8, (1.0, 2.32, 4.25, 6.63, 9.38, 12.46, 15.9096, 19.773152, 24.10033024, 28.946769869,
                    34.374782253, 40.454156123, 47.263054858, 54.889021441, 63.430104014, 72.996116496)),
)


def tail(head, v):
    """The marimba's signature: three modes set by hand, then v / (1 + 0.3 j)."""
    return list(head) + [v / (1 + 0.3 * j) for j in range(MAXM - len(head))]


def signature(name, ratios):
    """(level, relative T60) of each mode at COLOR 64 (round 2): each material its own, so that five of six no
    longer end in a decaying sine after 60 ms."""
    i = range(MAXM)
    return {
        "String": ([1 / (1 + k) ** 0.7 for k in i], [1 / (1 + 0.04 * k) for k in i]),
        "Membrane": ([1 / (1 + 0.12 * k) for k in i], [1 / (1 + 0.25 * k) for k in i]),
        "Marimba": (tail((1.0, 0.9, 0.45), 0.12), tail((1.0, 0.3, 0.15), 0.1)),
        "Bar": ([1 / (1 + 0.35 * k) for k in i], [1 / (1 + 0.12 * k) for k in i]),
        "Bell": ([1.0 if k == 3 else 1 / (1 + 0.08 * k) for k in i], [r ** -0.35 for r in ratios]),
        "Glass": ([1 / (1 + 0.8 * k) for k in i], [r ** -0.3 for r in ratios]),
    }[name]


def q(x, bits):
    return int(round(x * (1 << bits)))


def l2(x):
    return q(math.log2(x), 24)


def knob_span(span):
    """For kmap(k, span) = mul(k << 16, span): span x (k / 127), k in 8.8."""
    return q(span * 128 / 127, 24)


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def one_pole(fc):
    a = math.exp(-2 * math.pi * fc / SR)
    return a, (1 - a) / (1 + a)                 # the pole, and the output's variance over the input's (white)


def burst_gain(note):
    """The prototype made the RMS of each burst's spectrum at its first six harmonics 1.6 x 0.886 x the root of its
    energy, at most x 2.5. A voice cannot measure a burst before it plays it: the expected spectrum of the 6 kHz
    one-pole's noise stands in for the measured one."""
    a, var = one_pole(6000.0)
    hn2 = []
    for k in range(1, 7):
        w = 2 * math.pi * k * note_hz(note) / SR
        hn2.append((1 - a) ** 2 / (1 - 2 * a * math.cos(w) + a * a) / var)
    return min(1.6 * 0.886 / math.sqrt(sum(hn2) / 6), 2.5)


def mallet_gain(qq):
    """1 / (|X(f0)| / the pulse's sum) for a half sine lasting qq periods of f0: (1 - 4 q^2) / cos(pi q)."""
    if abs(qq - 0.5) < 1e-9:
        return 4 / math.pi
    return (1 - 4 * qq * qq) / math.cos(math.pi * qq)


def arr(name, ctype, vals, per_line=8):
    rows = [", ".join(str(v) for v in vals[i:i + per_line]) for i in range(0, len(vals), per_line)]
    return f"static const {ctype} {name}[{len(vals)}] = {{\n\t" + ",\n\t".join(rows) + ",\n};"


def arr2(name, ctype, rows2):
    inner = ["{ " + ", ".join(str(v) for v in r) + " }" for r in rows2]
    return f"static const {ctype} {name}[{len(rows2)}][{len(rows2[0])}] = {{\n\t" + ",\n\t".join(inner) + ",\n};"


def tables():
    lr, lsa, lsd, ldamp = [], [], [], []
    for name, damp, ratios in MATERIALS:
        amp, dec = signature(name, ratios)
        lr.append([l2(r) for r in ratios])
        lsa.append([l2(v) for v in amp])
        lsd.append([l2(v) for v in dec])
        ldamp.append(l2(damp))
    a6, v6 = one_pole(6000.0)
    a4, v4 = one_pole(4000.0)
    var_tri = 1 / 6                             # (u1 + u2) / 2, u uniform in [-1, 1)
    consts = {
        "MAXM": (MAXM, "modes in the material tables"),
        "L2_440": (l2(440.0), "log2 440 Hz"),
        "L2_INC": (q(32 - math.log2(SR), 24), "log2 of 2^32 / 48000: Hz to a phase step a frame"),
        "L2_SR": (l2(SR), "log2 48000"),
        "L2_LIVE": (l2(0.45 * SR), "modes at or above 0.45 fs are left out"),
        "L2_T60_LO": (l2(0.02), "DECAY 0: 20 ms"),
        "T60_SPAN": (knob_span(math.log2(400.0)), "DECAY 127: 8 s"),
        "L2_DK": (l2(3 * math.log(10) / SR), "d = 3 ln 10 / (T fs): r = exp(-d)"),
        "L2_LOG2E": (l2(math.log2(math.e)), "log2 log2 e"),
        "L2_T_GATE": (l2(0.12), "GATE: the body is damped to 0.12 s once the note ends"),
        "CHOKE_Q": (q(CHOKE_DEPTH ** (1 / (CHOKE_BLOCKS * BLOCK)), 31), "-12 dB over the choke's blocks"),
        "L2_Q_SOFT": (l2(0.35), "the soft mallet's contact: 0.35 of a period"),
        "Q_SPAN": (q(math.log2(0.03 / 0.35), 24), "to the hard mallet's 0.03"),
        "CLICK_DEC": (q(math.exp(-1 / (0.0008 * SR)), 31), "the click's decay a frame"),
        "CLICK_N": (int(0.003 * SR), "the click's length, frames"),
        "CLICK_AMP": (q(0.3 / CLICK_PEAK, 28), "0.3 / the expected peak; the difference is kept halved"),
        "CLICK_AMP1": (q(0.3, 28), "the same for an impulse (the proofs' click)"),
        "L2_BL0": (l2(0.003 * SR), "the shortest burst, 3 ms, in frames"),
        "BL_SPAN": (q(math.log2(50.0), 24), "to 150 ms"),
        "B_LP": (q(1 - a6, 31), "the burst's 6 kHz one-pole"),
        "B_NS": (q(1 / math.sqrt(var_tri * v6), 28), "its noise to unit variance"),
        "BURST_GAIN": (q(BURST_GAIN, 30), "the burst's energy"),
        "S_LP": (q(1 - a4, 31), "the sustained noise's 4 kHz one-pole"),
        "S_NS": (q(0.5 / math.sqrt(var_tri * v4), 28), "0.5 x its noise to unit variance"),
        "S_ATT": (int(0.04 * SR), "the sustained exciter's attack, frames"),
        "S_REL": (int(0.08 * SR), "and release"),
        "L2_HOLD3": (l2(SR / 3), "without GATE it is held a third of the body's T60"),
        "L2_DROPK": (l2(math.log2(math.e) * BLOCK / SR), "the drop decays exp(-te / tau): log2 e x a block"),
        "GAIN": (q(GAIN, 31), "the output's gain"),
        "CONTACT_SHIFT": (int(round(-math.log2(CONTACT_DAMP))), "a strike halves the ringing body"),
    }
    out = ["/* SOLID's tables (tools/gen_solid.py, notes/71). Generated: do not edit. */", "#include <stdint.h>", ""]
    for k, (v, why) in consts.items():
        out.append(f"#define {k:13s} {v}\t/* {why} */")
    out += ["", "/* materials: " + ", ".join(m[0] for m in MATERIALS) + " (SHAPE 0, 25, 51, 76, 102, 127) */",
            arr2("LR", "int32_t", lr) + "\t/* log2 ratio */",
            arr2("LSA", "int32_t", lsa) + "\t/* log2 level of each mode at COLOR 64 */",
            arr2("LSD", "int32_t", lsd) + "\t/* log2 T60 of each mode, relative */",
            arr("LDAMP", "int32_t", ldamp) + "\t/* log2 the material's T60 factor */", "",
            arr("SIN_T", "int32_t", [min(q(math.sin(i * math.pi / 512), 31), 0x7fffffff) for i in range(257)])
            + "\t/* sin, a quarter turn in 256 steps, Q31 */",
            arr("EXP2_T", "uint32_t", [q(2 ** (i / 256), 30) for i in range(257)]) + "\t/* 2^(i / 256), Q30 */",
            arr("LOG2_T", "int32_t", [q(math.log2(1 + i / 64), 24) for i in range(65)])
            + "\t/* log2(1 + i / 64), Q24 */",
            arr("G_BURST", "int32_t", [q(burst_gain(n), 28) for n in range(129)])
            + "\t/* the burst's gain by note, Q28 */",
            arr("G_MALLET", "int32_t", [q(mallet_gain(i / 64), 28) for i in range(65)])
            + "\t/* (1 - 4 q^2) / cos(pi q), q = i / 64, Q28 */"]
    return "\n".join(out) + "\n"


def pictures():
    """solid_pictures.c: the three pictures as the OS's Bitmaps, their table (solid_pictures, the registrar's pictures
    pointer: card, icon, track icon), a mask per picture on its own rows (tools/machine_pictures.py)."""
    import machine_pictures as mp
    return mp.sprites_c("solid", ["/* SOLID's own pictures (tools/gen_solid.py from tools/machines/solid/pictures/, "
                                  "notes/71 §13). Generated:", "   do not edit."], PKG, RUNTIME_PICTURES)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx: also compose the machine alone")
    ap.add_argument("--tables-only", action="store_true", help="the tables, without the toolchain")
    ap.add_argument("--check", action="store_true", help="checks that the committed files match")
    args = ap.parse_args()
    import gen_macro as gm             # noqa: E402
    bad = bool(gm.emit(TABLES, tables(), args.check))
    bad |= bool(gm.emit(PICTURES, pictures(), args.check))
    if not args.tables_only:
        import compose                 # noqa: E402
        m = compose.load_manifest("solid")
        with tempfile.TemporaryDirectory() as d:
            obj = compose.build_object(m, pathlib.Path(d))
        bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
        if args.cycles:
            import gen_sdvintage_exact as gx   # noqa: E402
            import gen_sdvintage_7th as g7     # noqa: E402
            img = g7.cycles_main(args.cycles)
            if len(img) != gx.IMAGE_LEN:
                raise SystemExit("!! not the official MAIN OS 1.13")
            tweak, info = compose.compose(img, ["solid"])
            tweak["description"].append("Generated by tools/gen_solid.py through tools/compose.py (notes/71).")
            bad |= bool(gm.emit(compose.DEV / "71-solid.json", json.dumps(tweak, indent=1, ensure_ascii=False) + "\n",
                                args.check))
            p = info["packages"][0]
            print(f"  solid: {len(tweak['writes'])} writes, code {p['code']} bytes, variables {p['bss']} bytes, "
                  f"{info['image']} bytes added to the image, {len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
