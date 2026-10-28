#!/usr/bin/env python3
"""POTS's Hilbert pair (notes/69 §4.2, §12.1): two chains of allpass sections in z^-2, (c - z^-2) / (1 - c z^-2),
chain a one frame late, whose phases stay 90 degrees apart over the band the shift needs (150 Hz to 6 kHz: the line
holds the transmitter's band, the receiver keeps 350 Hz to 3 kHz). model27's own design, no published numbers: a
minimax fit of the phase difference, Nelder-Mead from many seeded starts. The pairs live in
tools/machines/pots/hilbert.json; tools/gen_pots.py writes them into the package's tables.

    python3 tools/gen_hilbert.py [--check]   # recomputes each pair's phase error from hilbert.json and checks it
    python3 tools/gen_hilbert.py --design    # the fit again (about a minute), then writes hilbert.json

Needs numpy.
"""
import argparse
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "machines" / "pots" / "hilbert.json"
BAND = (150.0, 6000.0)
GRID = 600
PAIRS = {"24000": (3, 3), "48000": (4, 4)}  # sections a chain: the loop at 24 kHz (POTS_RATE 2), at 48 kHz (1)
LIMIT_DEG = 1.0                             # the most a pair may be off 90 degrees within the band
STARTS = 60


def phase(c, w):
    z2 = np.exp(-2j * w)
    return np.angle((c - z2) / (1 - c * z2))


def error_deg(a, b, fs):
    """The largest distance from 90 degrees of the phase difference (chain a late by a frame) over the band."""
    w = 2 * math.pi * np.geomspace(*BAND, GRID) / fs
    d = np.degrees(sum(phase(c, w) for c in a) - w - sum(phase(c, w) for c in b))
    d = (d + 180.0) % 360.0 - 180.0
    return float(np.max(np.abs(np.abs(d) - 90.0)))


def image_db(err):
    """How far under the shifted signal the other side lies for a phase error err: tan(err / 2)."""
    return -20 * math.log10(math.tan(math.radians(err) / 2))


def nelder_mead(f, x0, step, iters=4000, tol=1e-10):
    n = len(x0)
    pts = [np.array(x0, float)] + [np.array(x0, float) + step * np.eye(n)[i] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = np.argsort(vals)
        pts, vals = [pts[i] for i in order], [vals[i] for i in order]
        if vals[-1] - vals[0] < tol:
            break
        cen = np.mean(pts[:-1], axis=0)
        xr = cen + (cen - pts[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = cen + 2 * (cen - pts[-1])
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = cen + 0.5 * (pts[-1] - cen)
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0] + 0.5 * (p - pts[0]) for p in pts]
                vals = [f(p) for p in pts]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


def design(na, nb, fs, seed):
    """The best pair from STARTS seeded starts; each c is 1 / (1 + e^-u), so it stays in (0, 1)."""
    rng = np.random.default_rng(seed)
    unpack = lambda u: (1 / (1 + np.exp(-np.clip(u[:na], -40, 40))), 1 / (1 + np.exp(-np.clip(u[na:], -40, 40))))
    f = lambda u: error_deg(*unpack(u), fs)
    best = (None, 1e9)
    for _ in range(STARTS):
        u, v = nelder_mead(f, rng.normal(0, 1.5, na + nb), 0.6)
        u, v = nelder_mead(f, u, 0.1)
        if v < best[1]:
            best = (u, v)
    a, b = unpack(best[0])
    return dict(a=[float(x) for x in a], b=[float(x) for x in b], error_deg=float(best[1]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="the default: check hilbert.json")
    ap.add_argument("--design", action="store_true", help="fit the pairs again and write hilbert.json")
    args = ap.parse_args()
    if args.design:
        data = {"band_hz": list(BAND), "note": "model27's own pair (notes/69 §12.1): a minimax fit by "
                "tools/gen_hilbert.py --design; sections in z^-2, (c - z^-2) / (1 - c z^-2), chain a one frame late"}
        for fs, (na, nb) in PAIRS.items():
            data[fs] = design(na, nb, int(fs), seed=3 if fs == "48000" else 1)
        OUT.write_text(json.dumps(data, indent=1) + "\n")
    data = json.loads(OUT.read_text())
    bad = list(data["band_hz"]) != list(BAND)
    for fs, (na, nb) in PAIRS.items():
        p = data[fs]
        err = error_deg(p["a"], p["b"], int(fs))
        ok = (len(p["a"]), len(p["b"])) == (na, nb) and abs(err - p["error_deg"]) < 1e-6 and err <= LIMIT_DEG \
            and all(0 < c < 1 for c in p["a"] + p["b"])
        bad |= not ok
        print(f"  {'ok' if ok else 'FAIL'}: {fs} Hz, {na} + {nb} sections: 90 degrees +-{err:.3f} from {BAND[0]:g} to "
              f"{BAND[1]:g} Hz, the other side {image_db(err):.1f} dB under")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    sys.exit(main())
