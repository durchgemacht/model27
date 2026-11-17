#!/usr/bin/env python3
"""TERRA (notes/85): an added machine, wave terrain synthesis after the WaveTerrainEngine of Mutable Instruments
Plaits (Emilie Gillet, MIT, eurorack 08460a6), written in fixed point in tools/machines/terra/terra.c.

This generator writes the package's tables (tools/machines/terra/terra_tables.h) and compiles its committed object
(tools/machines/terra/terra.o, ld -r of the source: notes/60 §2). The tables: Squash(Sine(p), 2) over a period (terrain
1), 1 / m on [1, 2) (the divisions), exp2 (the pitch), the Cycles' sine (the host's copy of the table the device reads
in its SRAM at 0x8000eee4, as SWARM's), the terrains' constants from wave_terrain_engine.cc, and Plaits' wavetable
data wav_integrated_waves (banks 0 to 2, 25 344 values), which terrains 6 to 8 read; on the device a far table
(section .far.terra_wt: at the start of TERRA's variables' room, outside the code window, notes/85 §5). Those data
come from Plaits' plaits/resources.cc (--plaits); without it the generator keeps the ones in the committed header; either way they must
have the SHA-256 below (the values at eurorack 08460a6, big-endian int16). With --cycles it also checks the OS's sine
table against SIN256 (read from the user's file, nothing kept) and composes the machine alone through tools/compose.py
into tweaks/model-cycles_OS1.13/86-terra.json: the card's build alone, which the web flasher composes in the page.

    python3 tools/gen_terra.py [--plaits …/eurorack/plaits/resources.cc] [--check]          # tables and object
    python3 tools/gen_terra.py --cycles firmware/model-cycles_OS1.13.syx [--check]           # and the card's tweak
    python3 tools/gen_terra.py --tables-only [--check]                                       # no toolchain
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
import struct
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PKG = HERE / "machines" / "terra"
TABLES = PKG / "terra_tables.h"

SR = 48000.0
SIN_SRAM = 0x8000eee4               # the Cycles' sine table in its internal SRAM, 257 words (notes/26 §4, notes/82)
SIN_ROM = 0x401a2a50 + (SIN_SRAM - 0x80008000)   # where the boot copies it from
WT_N = 3 * 64 * 132                 # wav_integrated_waves: 3 banks of 64 waves of 128 + 4 values
WT_SHA256 = "b34f209848ab075152cb029abc2b00f58e211c0d42615f24b672853df817bf2c"   # eurorack 08460a6, >h each


def q(x, bits):
    return int(round(x * (1 << bits)))


def q31(x):
    return max(-(1 << 31), min(q(x, 31), 0x7fffffff))


def l2(x):
    return q(math.log2(x), 24)


def sin256():
    """The 257 words the Cycles keeps at SIN_SRAM: sin(2 pi i / 256) in Q31, 0x7fffffff at the top, -2^31 below."""
    return [q31(math.sin(2 * math.pi * k / 256)) for k in range(257)]


def squash256():
    """Plaits' Squash(Sine(p), 2) = 2 s / (1 + |2 s|) over a period, Q31."""
    out = []
    for i in range(257):
        s = 2 * math.sin(2 * math.pi * i / 256)
        out.append(q31(s / (1 + abs(s))))
    return out


def recip64():
    """1 / m for m = 1 + i / 64 (i = 0 .. 64), Q31; m = 1 saturated."""
    return [q31(1 / (1 + i / 64)) for i in range(65)]


def consts():
    """The terrains' constants (wave_terrain_engine.cc): coordinates Q29, phases Q32, heights Q30 (terra.c)."""
    return [
        ("L2_INC0", l2(440.0) + q(32 - math.log2(SR), 24), "log2 of the phase step (Q32) of 440 Hz at 48 kHz, Q24"),
        ("SIN_SRAM", f"{SIN_SRAM:#x}", "the Cycles' sine table in its SRAM (the device reads it there)"),
        ("K0_X", q(1.273 * 8 / 16, 31), "terrain 1: Sine(1.273 x): the phase mul(X, K) << 4"),
        ("C0_1571", q(1.571, 29), "terrain 1: x + 1.571, Q29"),
        ("K0_Y", q(0.637, 31), "terrain 1: Sine(0.637 y (x + 1.571)): mul(m, K) << 5, m Q27"),
        ("K0_057", q(0.57, 31), "terrain 1: x 0.57"),
        ("K1_S", q(0.637, 31), "terrain 2: Sine(0.637 (x + y)): mul(X + Y, K) << 3"),
        ("C1_02", q(0.2, 27), "terrain 2: 0.2 + (xy)^2, Q27"),
        ("K_0159", q(0.159, 31), "terrains 2, 3, 5: x 0.159"),
        ("K2_XY", q(2.387 * 32 / 128, 31), "terrain 3: Sine(2.387 xy): mul(xy, K) << 7, xy Q27"),
        ("C2_035", q(0.35, 27), "terrains 3, 5: 0.35 + ..., Q27"),
        ("C_025", q(0.25, 29), "terrains 4, 5: 0.25, Q29"),
        ("C3_2", q(2.0, 27), "terrain 4: 2 + |5 (x - 0.25)(y + 0.25)|, Q27"),
        ("K3_6366", q(6.366 / 8, 31), "terrain 4: x 6.366 / 8"),
        ("C4_017", q(0.17, 27), "terrain 5: 0.17 + |y - 0.25|, Q27"),
        ("C_05", q(0.5, 29), "terrain 5: x + 0.5, Q29"),
        ("C_15", q(1.5, 29), "terrain 5: y + 1.5, Q29"),
        ("K_0477", q(0.477, 31), "terrain 5: x 0.477"),
        ("KWT", q(31.5 * 2 ** 18 / 2 ** 31, 31), "terrains 6-8: the wave (x + 1) 31.5 in Q16 = mul(X + 2^29, K)"),
    ]


def wt_sha(vals):
    return hashlib.sha256(struct.pack(f">{len(vals)}h", *vals)).hexdigest()


def wt_from_plaits(path):
    m = re.search(r"const int16_t wav_integrated_waves\[\] = \{(.*?)\};", pathlib.Path(path).read_text(), re.S)
    if not m:
        raise SystemExit(f"!! wav_integrated_waves not found in {path}")
    return [int(v) for v in re.findall(r"-?\d+", m.group(1))]


def wt_from_header():
    if not TABLES.exists():
        raise SystemExit("!! no terra_tables.h yet: give --plaits …/plaits/resources.cc")
    m = re.search(r"WT_T\[\d+\](?: TERRA_FAR)? = \{(.*?)\};", TABLES.read_text(), re.S)
    return [int(v) for v in re.findall(r"-?\d+", m.group(1))]


def arr(name, ctype, vals, per_line=8):
    rows = [", ".join(str(v) for v in vals[i:i + per_line]) for i in range(0, len(vals), per_line)]
    return f"static const {ctype} {name}[{len(vals)}] = {{\n\t" + ",\n\t".join(rows) + "\n};"


def tables(wt):
    out = ["/* TERRA's tables (notes/85), generated by tools/gen_terra.py: do not edit. The terrains' constants after",
           " * Plaits' wave_terrain_engine.cc, WT_T Plaits' wav_integrated_waves (resources.cc, eurorack 08460a6);",
           " * Mutable Instruments Plaits, Copyright 2016-2021 Emilie Gillet, MIT (LICENSE-Plaits). */",
           "#ifndef TERRA_TABLES_H", "#define TERRA_TABLES_H", "#include <stdint.h>", ""]
    for k, v, why in consts():
        out.append(f"#define {k} {v}\t/* {why} */")
    out.append("")
    out.append(arr("EXP2_T", "uint32_t", [q(2 ** (i / 256), 30) for i in range(257)]) + "\t/* 2^(i / 256), Q30 */")
    out.append("#ifdef TERRA_HOST")
    out.append(arr("SIN256_T", "int32_t", sin256()) + "\t/* sin(2 pi i / 256), Q31: the host's copy of the table at "
               "SIN_SRAM */")
    out.append("#endif")
    out.append(arr("SQS256_T", "int32_t", squash256()) + "\t/* Squash(sin(2 pi i / 256), 2), Q31 (terrain 1) */")
    out.append(arr("RCP64_T", "int32_t", recip64()) + "\t/* 1 / (1 + i / 64), Q31 */")
    out.append("/* Plaits' wav_integrated_waves: 3 banks x 64 waves x 132. On the device a far table (notes/85 §5): placed")
    out.append(" * at the start of TERRA's variables' room, outside the code window, and copied there at boot. */")
    out.append("#ifdef TERRA_HOST\n#define TERRA_FAR\n#else\n#define TERRA_FAR __attribute__((section(\".far.terra_wt\")))\n#endif")
    out.append(arr("WT_T", "int16_t", wt, 12).replace("WT_T[%d] = {" % len(wt), "WT_T[%d] TERRA_FAR = {" % len(wt)))
    out.append("\n#endif")
    return "\n".join(out) + "\n"


def check_os_sine(cycles):
    """The OS's table, as the boot copies it into the SRAM, against sin256(): read, compared, nothing kept."""
    import gen_sdvintage_exact as gx    # noqa: E402
    import gen_sdvintage_7th as g7      # noqa: E402
    img = bytes(g7.cycles_main(cycles))
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! not the official MAIN OS 1.13")
    got = list(struct.unpack_from(">257i", img, SIN_ROM - 0x40000400))
    ok = got == sin256()
    print(f"    the OS's sine table ({SIN_SRAM:#x}, 257 words) {'is sin(2 pi i / 256) in Q31' if ok else 'DIFFERS'}")
    return not ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plaits", help="Plaits' plaits/resources.cc (eurorack 08460a6): the wavetable data")
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx: also check the OS's sine and compose the machine "
                                     "alone, the card's tweak")
    ap.add_argument("--tables-only", action="store_true", help="the tables, without the toolchain")
    ap.add_argument("--check", action="store_true", help="checks that the committed files match")
    args = ap.parse_args()
    wt = wt_from_plaits(args.plaits) if args.plaits else wt_from_header()
    if len(wt) != WT_N or wt_sha(wt) != WT_SHA256:
        raise SystemExit(f"!! the wavetable data are not Plaits' at 08460a6 ({len(wt)} values, {wt_sha(wt)[:16]}…)")
    import gen_macro as gm             # noqa: E402
    bad = bool(gm.emit(TABLES, tables(wt), args.check))
    if args.cycles:
        bad |= check_os_sine(args.cycles)
    if not args.tables_only:
        import compose                 # noqa: E402
        m = compose.load_manifest("terra")
        with tempfile.TemporaryDirectory() as d:
            obj = compose.build_object(m, pathlib.Path(d))
        bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
        if args.cycles:
            import gen_sdvintage_exact as gx   # noqa: E402
            import gen_sdvintage_7th as g7     # noqa: E402
            img = g7.cycles_main(args.cycles)
            if len(img) != gx.IMAGE_LEN:
                raise SystemExit("!! not the official MAIN OS 1.13")
            tweak, info = compose.compose(img, ["terra"])
            tweak["description"].append("Generated by tools/gen_terra.py through tools/compose.py (notes/85).")
            bad |= bool(gm.emit(compose.DEV / "86-terra.json",
                                json.dumps(tweak, indent=1, ensure_ascii=False) + "\n", args.check))
            p = info["packages"][0]
            print(f"  terra: {len(tweak['writes'])} writes, code {p['code']} bytes, variables {p['bss']} bytes, "
                  f"{info['image']} bytes added to the image, {len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
