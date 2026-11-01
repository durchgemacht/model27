#!/usr/bin/env python3
"""Generates EQ, a three-band equalizer as Track FX 5 (the filter slot, notes/76, tools/machines/eq/): writes its
coefficient tables into tools/machines/eq/eq_tab.h, compiles eq.c and eq_cf.S with the manifest's recipe into
tools/machines/eq/eq.o (ld -r, notes/60 §2), then composes it alone through tools/compose.py, which places that object
with tools/relocate.py as any build does, into tweaks/model-cycles_OS1.13/76-eq.json: the card's build alone, which
the web flasher composes in the page (its excludes come from that tweak's conflicts). Needs the m68k toolchain (for
the object); the tables and compose.py do not.

The bands are the Audio EQ Cookbook's biquads (R. Bristow-Johnson): a low shelf at 100 Hz and a high shelf at 8 kHz,
slope S = 1, and a peaking bell of Q 1 from 200 Hz to 5 kHz; every gain 12 dB * (k - 64) / 64 for the knob value k.
The tables hold the coefficients normalized by a0, scaled as eq_cf.S multiplies them (over 2, High over 4), rounded
to Q31; eq.c derives each band's last coefficient from the others. EQ_HIGH_FIT is the first word of High whose
coefficients, as eq.c works them out, do not all fit over 2: below it eq.c doubles them and the loop doubles once
(since EQ 0.3).

    python3 tools/gen_eq.py --cycles model-cycles_OS1.13.syx [--check]
    python3 tools/gen_eq.py --response           # the bands' response from the tables against the cookbook's
"""
import argparse
import cmath
import functools
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

PACKAGE = "eq"
TABLE = compose.MACHINES / PACKAGE / "eq_tab.h"
OUT = compose.DEV / "76-eq.json"
FS = 48000.0
LOW_HZ, HIGH_HZ = 100.0, 8000.0    # the shelves' corners (the maintainer, 2026-11-01)
SLOPE, MID_Q = 1.0, 1.0            # the shelves' slope S, the bell's Q
DB = 12.0                          # the gains' range, either way
STEPS = 128                        # the shelves' rows: k = 0 .. 128 (the word's high byte and the next one)
MID_G, MID_F = 8, 4                # the bell's grid: a row every 8 knob steps of gain, a column every 4 of frequency
SHIFT = {"low": 1, "mid": 1, "high": 2}   # the coefficients over 2^shift (eq_cf.S doubles the sum that many times)


def gain_db(k):
    """The gain of knob value k (0 .. 128, fractions between): -12 dB at 0, flat at 64, +12 dB at 128."""
    return DB * (k - 64) / 64


def mid_hz(k):
    """Mid Freq's centre at knob value k: 200 Hz at 0, 1 kHz at 64, 5 kHz at 128 (4.9 kHz at 127)."""
    return 1000.0 * 5 ** ((k - 64) / 64)


def shelf(kind, f, db):
    """The cookbook's low or high shelf, normalized: (b0, b1, b2, a1, a2)."""
    A = 10 ** (db / 40)
    w = 2 * math.pi * f / FS
    c, s = math.cos(w), math.sin(w)
    sq = 2 * math.sqrt(A) * s / 2 * math.sqrt((A + 1 / A) * (1 / SLOPE - 1) + 2)
    if kind == "low":
        b = (A * ((A + 1) - (A - 1) * c + sq), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sq))
        a = ((A + 1) + (A - 1) * c + sq, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sq)
    else:
        b = (A * ((A + 1) + (A - 1) * c + sq), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sq))
        a = ((A + 1) - (A - 1) * c + sq, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sq)
    return tuple(v / a[0] for v in b) + (a[1] / a[0], a[2] / a[0])


def bell(f, db):
    """The cookbook's peaking EQ, constant Q, normalized: (b0, b1, b2, a1, a2)."""
    A = 10 ** (db / 40)
    w = 2 * math.pi * f / FS
    c, al = math.cos(w), math.sin(w) / (2 * MID_Q)
    a0 = 1 + al / A
    return ((1 + al * A) / a0, -2 * c / a0, (1 - al * A) / a0, -2 * c / a0, (1 - al / A) / a0)


def q31(v, shift):
    """v over 2^shift in Q31, rounded; it must fit."""
    r = round(v * 2 ** (31 - shift))
    if not -2 ** 31 <= r < 2 ** 31:
        raise SystemExit(f"!! a coefficient {v} does not fit over 2^{shift}")
    return r


@functools.lru_cache(maxsize=None)
def tables():
    """The three tables: Low and High (b0, b1, a1, a2) by k = 0 .. 128, Mid (b0, a1, a2) by gain row then column."""
    low = [[q31(shelf("low", LOW_HZ, gain_db(k))[i], SHIFT["low"]) for i in (0, 1, 3, 4)] for k in range(STEPS + 1)]
    high = [[q31(shelf("high", HIGH_HZ, gain_db(k))[i], SHIFT["high"]) for i in (0, 1, 3, 4)]
            for k in range(STEPS + 1)]
    mid = [[[q31(bell(mid_hz(fk), gain_db(gk))[i], SHIFT["mid"]) for i in (0, 3, 4)]
            for fk in range(0, STEPS + 1, MID_F)] for gk in range(0, STEPS + 1, MID_G)]
    return low, high, mid


def lerp(a, b, t):
    """eq.c's lerp: 8 bits of the difference dropped (Python's >> floors as the ColdFire's asr)."""
    return a + ((b - a) >> 8) * t


def high_fit():
    """The first word of High whose five coefficients, interpolated and b2 derived as eq.c does them over 4, do not
    all fit over 2 (under 2^30 over 4); every word below must fit and none from it, or eq.c's test would be wrong."""
    high = tables()[1]

    def fits(w):
        p, q = high[w >> 8], high[(w >> 8) + 1]
        b0, b1, a1, a2 = (lerp(p[i], q[i], w & 0xff) for i in range(4))
        b2 = (1 << 29) + (a1 - b1) + (a2 - b0)
        return all(-(1 << 30) <= c < (1 << 30) for c in (b2, b0, b1, a1, a2))

    ok = [fits(w) for w in range(0x7f01)]
    first = ok.index(False)
    if not all(ok[:first]) or any(ok[first:]):
        raise SystemExit("!! High's coefficients fit over 2 below a word and not from it: no single threshold")
    return first


def header():
    low, high, mid = tables()
    fit = high_fit()

    def rows(t):
        return ",\n\t".join("{" + ", ".join(f"{v:11d}" for v in r) + "}" for r in t)

    mids = ",\n\t".join("{ /* " + f"{gain_db(g * MID_G):+.1f} dB */\n\t\t" + ",\n\t\t".join(
        "{" + ", ".join(f"{v:11d}" for v in c) + "}" for c in row) + "\n\t}" for g, row in enumerate(mid))
    return ("/* EQ's coefficients (notes/76), written by tools/gen_eq.py from the Audio EQ Cookbook's biquads, normalized by\n"
            " * a0 and rounded to Q31 over 2^shift (eq_cf.S doubles the sum as often): y = b0 x + b1 x1 + b2 x2 - a1 y1 - a2 y2.\n"
            f" * EQ_LOW: the low shelf at {LOW_HZ:g} Hz (S {SLOPE:g}), b0, b1, a1, a2 over 2, by knob value k = 0 .. 128, the gain\n"
            f" * {DB:g} dB * (k - 64) / 64. EQ_HIGH: the high shelf at {HIGH_HZ:g} Hz, the same, over 4. EQ_MID: the bell (Q {MID_Q:g}), b0,\n"
            f" * a1, a2 over 2, by gain every {MID_G} knob steps (17 rows) then centre every {MID_F} (33 columns), the centre\n"
            " * 1000 Hz * 5^((k - 64) / 64).\n"
            f" * EQ_HIGH_FIT: the first word of High ({fit / 256:.1f}, {gain_db(fit / 256):+.1f} dB) whose coefficients do not all fit over\n"
            " * 2; below it eq.c doubles them, and the loop doubles the sum once.\n"
            " * The last coefficient of each band comes from the others (eq.c). */\n"
            "#ifndef EQ_TAB_H\n#define EQ_TAB_H\n#include <stdint.h>\n\n"
            f"#define EQ_HIGH_FIT {fit:#06x}\n\n"
            f"static const int32_t EQ_LOW[{STEPS + 1}][4] = {{\n\t" + rows(low) + "\n};\n\n"
            f"static const int32_t EQ_HIGH[{STEPS + 1}][4] = {{\n\t" + rows(high) + "\n};\n\n"
            f"static const int32_t EQ_MID[{STEPS // MID_G + 1}][{STEPS // MID_F + 1}][3] = {{\n\t" + mids + "\n};\n\n"
            "#endif\n")


def from_tables(band, w, f=0x4000):
    """The coefficients eq.c works out for word w (and Mid's centre word f): (b0, b1, b2, a1, a2) as floats."""
    low, high, mid = tables()
    if band in ("low", "high"):
        t, s = (low, SHIFT["low"]) if band == "low" else (high, SHIFT["high"])
        p, q = t[w >> 8], t[(w >> 8) + 1]
        b0, b1, a1, a2 = (lerp(p[i], q[i], w & 0xff) for i in range(4))
        one = 1 << (31 - s)
        b2 = one - a1 + a2 - b0 + b1 if band == "low" else one + a1 + a2 - b0 - b1
    else:
        s = SHIFT["mid"]
        gi, gt, fi, ft = w >> 11, (w >> 3) & 0xff, f >> 10, (f >> 2) & 0xff
        b0, a1, a2 = (lerp(lerp(mid[gi][fi][i], mid[gi][fi + 1][i], ft), lerp(mid[gi + 1][fi][i], mid[gi + 1][fi + 1][i], ft),
                           gt) for i in range(3))
        b1, b2 = a1, (1 << (31 - s)) + a2 - b0
    return tuple(v / 2 ** (31 - s) for v in (b0, b1, b2, a1, a2))


def db_at(c, hz):
    z = cmath.exp(-2j * math.pi * hz / FS)
    b0, b1, b2, a1, a2 = c
    return 20 * math.log10(abs((b0 + b1 * z + b2 * z * z) / (1 + a1 * z + a2 * z * z)))


def response():
    """The bands from the tables (as eq.c reads them) against the cookbook's, over 20 Hz .. 20 kHz: the largest
    difference in dB, the shelves at every 64th word, Mid at every 128th word of gain and 256th of centre (on 50
    frequencies and the centre); and each band's gain where it should hold it."""
    hz = [20 * 1000 ** (i / 199) for i in range(200)]
    words = range(0, 0x7f01, 64)
    worst = {}
    for band in ("low", "high"):
        e = max((max(abs(db_at(from_tables(band, w), h) - db_at(shelf(band, LOW_HZ if band == "low" else HIGH_HZ,
                                                                         gain_db(w / 256)), h)) for h in hz), w)
                for w in words)
        worst[band] = e
    e, few = (0, 0, 0), hz[::4]
    for g in range(0, 0x7f01, 128):
        for f in range(0, 0x7f01, 256):
            d = max(abs(db_at(from_tables("mid", g, f), h) - db_at(bell(mid_hz(f / 256), gain_db(g / 256)), h))
                    for h in few + [mid_hz(f / 256)])
            e = max(e, (d, g, f))
    worst["mid"] = e
    for band, v in worst.items():
        print(f"  {band}: at most {v[0]:.4f} dB from the cookbook's (word {v[1]:#x}"
              + (f", centre {v[2]:#x})" if band == "mid" else ")"))
    print("  at the ends: Low 0 / 127 at 20 Hz %+.2f / %+.2f dB, at 20 kHz %+.4f / %+.4f dB" % (
        db_at(from_tables("low", 0), 20), db_at(from_tables("low", 0x7f00), 20),
        db_at(from_tables("low", 0), 20000), db_at(from_tables("low", 0x7f00), 20000)))
    print("               High 0 / 127 at 20 kHz %+.2f / %+.2f dB, at 20 Hz %+.4f / %+.4f dB" % (
        db_at(from_tables("high", 0), 20000), db_at(from_tables("high", 0x7f00), 20000),
        db_at(from_tables("high", 0), 20), db_at(from_tables("high", 0x7f00), 20)))
    for f in (0, 0x4000, 0x7f00):
        print(f"               Mid 0 / 127 at {mid_hz(f / 256):.0f} Hz %+.2f / %+.2f dB" % (
            db_at(from_tables("mid", 0, f), mid_hz(f / 256)), db_at(from_tables("mid", 0x7f00, f), mid_hz(f / 256))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx")
    ap.add_argument("--check", action="store_true", help="checks that the committed tables, object and tweak match")
    ap.add_argument("--response", action="store_true", help="prints the bands' response against the cookbook's")
    args = ap.parse_args()
    if args.response:
        response()
        return
    if not args.cycles:
        ap.error("--cycles is needed (or --response)")
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! not the official MAIN OS 1.13")
    bad = bool(gm.emit(TABLE, header(), args.check))
    m = compose.load_manifest(PACKAGE)
    with tempfile.TemporaryDirectory() as d:
        obj = compose.build_object(m, pathlib.Path(d))
    bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
    tweak, info = compose.compose(img, [PACKAGE])
    tweak["description"].append("Generated by tools/gen_eq.py through tools/compose.py (notes/76).")
    bad |= bool(gm.emit(OUT, json.dumps(tweak, indent=1, ensure_ascii=False) + "\n", args.check))
    p, f = info["packages"][0], info["filters"]
    print(f"  {PACKAGE}: {len(tweak['writes'])} writes, code and tables {p['code']} bytes, variables {p['bss']} bytes, "
          f"the filter slot {f['code'] + f['data']} bytes, {info['image']} bytes added to the image, "
          f"{len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
