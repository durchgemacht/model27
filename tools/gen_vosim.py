#!/usr/bin/env python3
"""VOSIM (working name, notes/86): an added machine, Braids' VOSIM oscillator (DigitalOscillator::RenderVosim of
Mutable Instruments Braids, Emilie Gillet, MIT, eurorack 08460a6) carried over integer for integer in
tools/machines/vosim/vosim.c, with formant tracking, a decaying window and a DC stage of model27's.

This generator writes the package's tables (tools/machines/vosim/vosim_tables.h) and compiles its committed object
(tools/machines/vosim/vosim.o, ld -r of the source: notes/60 §2). The tables: Braids' lut_bell (the window),
wav_sine (the formants) and lut_oscillator_increments (the pitch, 96 kHz), from Braids' braids/resources.cc (--braids)
or else kept from the committed header, either way checked against their SHA-256 at 08460a6 (big-endian); and
model27's window family: 16 steps from Braids' bell to an e-curve that falls by 24 dB over the period (Bell^(1-c)
End^c, c = j / 16, the start linear in c), at half scale (as Braids' Interpolate824(...) >> 1) with the level made up,
3.5 dB j / 16 (notes/86 §3). On the device the family is a far table (section .far.vosim_fam: at the start of the
package's variables' room, outside the code window, notes/85 §5). With --cycles it composes the machine alone through
tools/compose.py into tweaks/model-cycles_OS1.13/87-vosim.json: the card's build alone.

    python3 tools/gen_vosim.py [--braids …/eurorack/braids/resources.cc] [--check]          # tables and object
    python3 tools/gen_vosim.py --cycles firmware/model-cycles_OS1.13.syx [--check]           # and the card's tweak
    python3 tools/gen_vosim.py --tables-only [--check]                                       # no toolchain
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

PKG = HERE / "machines" / "vosim"
TABLES = PKG / "vosim_tables.h"

BRAIDS = {                          # name in resources.cc, the header's name, C type, count, struct code, SHA-256 at 08460a6
    "lut_bell": ("LUT_BELL", "uint16_t", 257, "H", "fe68a8b7b60d3512be8d31f0ffe32eed758bc70bdc4cad8fc282cba4748dbcbc"),
    "wav_sine": ("WAV_SINE", "int16_t", 257, "h", "b34160c3f35560f30a7a166bd70f1653ea3579bcebdf046cf337b4d4a28296ea"),
    "lut_oscillator_increments": ("LUT_INC", "uint32_t", 97, "I",
                                  "8266dd7ac938ed100d79aca35d6b53af6d33f515ff6365967f174c847aff7c31"),
}
END_DB = 24.0                       # the decaying end: exp(-k x) over the period, 24 dB down at its end
STEPS = 16                          # CONTOUR: the bell and 16 steps towards the end (17 positions, notes/86 §2)
GAIN_DB = 3.5                       # the level made up at the end, 3.5 dB j / 16 (the maintainer's 2026-11-18)
FAM_SHA256 = "5fbbefe8f4d1a140ce3ef44753524addc95abebc838e02428c686fb274a31640"   # the 16 steps at 08460a6 (gen_vosim.py)


def sha(vals, code):
    return hashlib.sha256(struct.pack(f">{len(vals)}{code}", *vals)).hexdigest()


def braids_from_source(path):
    s = pathlib.Path(path).read_text(encoding="utf-8")
    out = {}
    for name in BRAIDS:
        m = re.search(r"const \w+ %s\[\] = \{(.*?)\};" % name, s, re.S)
        if not m:
            raise SystemExit(f"!! {name} not found in {path}")
        out[name] = [int(v) for v in re.findall(r"-?\d+", m.group(1))]
    return out


def braids_from_header():
    if not TABLES.exists():
        raise SystemExit("!! no vosim_tables.h yet: give --braids …/braids/resources.cc")
    s = TABLES.read_text(encoding="utf-8")
    out = {}
    for name, (cname, _t, _n, _c, _h) in BRAIDS.items():
        m = re.search(r"%s\[\d+\] = \{(.*?)\};" % cname, s, re.S)
        out[name] = [int(v) for v in re.findall(r"-?\d+", m.group(1))]
    return out


def family(bell):
    """The 16 steps after the bell: Bell^(1 - c) End^c (c = j / 16), the start (bell 0, end 1) linear in c, then at
    half scale with the level made up: x 10^(3.5 dB j / 16 / 20) / 2. Rows j = 1 .. 16."""
    k = math.log(10) * END_DB / 20
    end = [round(65535 * math.exp(-k * i / 256)) for i in range(257)]
    rows = []
    for j in range(1, STEPS + 1):
        c = j / STEPS
        if j == STEPS:
            row = list(end)
        else:
            row = [round(65535 * (b / 65535) ** (1 - c) * (e / 65535) ** c) if b > 0 else 0 for b, e in zip(bell, end)]
            row[0] = round(65535 * c)
        g = 10 ** (GAIN_DB * j / STEPS / 20)
        rows.append([round(v * g / 2) for v in row])
    assert max(max(r) for r in rows) < 1 << 16
    return rows


def mean_half(t):
    """The mean of (w >> 1) over a period, interpolated as Interpolate824 does, Q15: the bell's DC at the start."""
    h = [v >> 1 for v in t]
    return round(sum((h[i] + h[i + 1]) / 2 for i in range(256)) / 256)


def arr(name, ctype, vals, per_line=16, attr=""):
    rows = [", ".join(str(v) for v in vals[i:i + per_line]) for i in range(0, len(vals), per_line)]
    return f"static const {ctype} {name}[{len(vals)}]{attr} = {{\n\t" + ",\n\t".join(rows) + "\n};"


def tables(b, fam):
    out = ["/* VOSIM's tables (notes/86), generated by tools/gen_vosim.py: do not edit. LUT_BELL, WAV_SINE, LUT_INC are",
           " * Braids' lut_bell, wav_sine and lut_oscillator_increments (braids/resources.cc, eurorack 08460a6), unchanged:",
           " * Mutable Instruments Braids, Copyright 2012 Emilie Gillet, MIT (LICENSE-Braids). FAM_H: model27's window",
           " * family, Bell^(1 - c) End^c towards an e-curve 24 dB down at the period's end, at half scale with the level",
           " * made up (3.5 dB j / 16), rows j = 1 .. 16. */",
           "#ifndef VOSIM_TABLES_H", "#define VOSIM_TABLES_H", "#include <stdint.h>", ""]
    for name, (cname, ctype, _n, _c, _h) in BRAIDS.items():
        out.append(arr(cname, ctype, b[name], 8 if ctype == "uint32_t" else 16) + f"\t/* Braids' {name} */")
    out.append(f"#define WMEAN_BELL {mean_half(b['lut_bell'])}\t/* the mean of (lut_bell >> 1), Q15 */")
    out.append("/* On the device a far table (notes/85 §5): at the start of VOSIM's variables' room, copied there at boot. */")
    out.append("#ifdef VOSIM_HOST\n#define VOSIM_FAR\n#else\n"
               "#define VOSIM_FAR __attribute__((section(\".far.vosim_fam\")))\n#endif")
    rows = []
    for r in fam:
        rows.append("\t{ " + ",\n\t  ".join(", ".join(str(v) for v in r[i:i + 16]) for i in range(0, 257, 16)) + " }")
    out.append(f"static const uint16_t FAM_H[{len(fam)}][257] VOSIM_FAR = {{\n" + ",\n".join(rows) + "\n};")
    out.append("\n#endif")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--braids", help="Braids' braids/resources.cc (eurorack 08460a6): the three tables")
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx: also compose the machine alone, the card's tweak")
    ap.add_argument("--tables-only", action="store_true", help="the tables, without the toolchain")
    ap.add_argument("--check", action="store_true", help="checks that the committed files match")
    args = ap.parse_args()
    b = braids_from_source(args.braids) if args.braids else braids_from_header()
    for name, (_cn, _t, n, code, h) in BRAIDS.items():
        if len(b[name]) != n or sha(b[name], code) != h:
            raise SystemExit(f"!! {name} is not Braids' at 08460a6 ({len(b[name])} values, {sha(b[name], code)[:16]}…)")
    fam = family(b["lut_bell"])
    fs = sha([v for r in fam for v in r], "H")
    if fs != FAM_SHA256:
        raise SystemExit(f"!! the window family computes to {fs}, not {FAM_SHA256}: another libm? (notes/86 §3)")
    import gen_macro as gm             # noqa: E402
    bad = bool(gm.emit(TABLES, tables(b, fam), args.check))
    if not args.tables_only:
        import compose                 # noqa: E402
        m = compose.load_manifest("vosim")
        with tempfile.TemporaryDirectory() as d:
            obj = compose.build_object(m, pathlib.Path(d))
        bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
        if args.cycles:
            import gen_sdvintage_exact as gx   # noqa: E402
            import gen_sdvintage_7th as g7     # noqa: E402
            img = g7.cycles_main(args.cycles)
            if len(img) != gx.IMAGE_LEN:
                raise SystemExit("!! not the official MAIN OS 1.13")
            tweak, info = compose.compose(img, ["vosim"])
            tweak["description"].append("Generated by tools/gen_vosim.py through tools/compose.py (notes/86).")
            bad |= bool(gm.emit(compose.DEV / "87-vosim.json",
                                json.dumps(tweak, indent=1, ensure_ascii=False) + "\n", args.check))
            p = info["packages"][0]
            print(f"  vosim: {len(tweak['writes'])} writes, code {p['code']} bytes, variables {p['bss']} bytes, "
                  f"{info['image']} bytes added to the image, {len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
