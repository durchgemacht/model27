#!/usr/bin/env python3
"""CHIPS (notes/83): an added machine, Plaits' hard-synced square and its 32-step triangle bass, with an arpeggio
inside the note and a pitch sweep at every trig, after the ChiptuneEngine of Mutable Instruments Plaits (eurorack
08460a6, MIT, Emilie Gillet; tools/machines/chips/LICENSE-Plaits), written anew in fixed point in
tools/machines/chips/chips.c and checked against Plaits' unchanged oscillators on the host (notes/83 §3).

This generator writes the package's tables (tools/machines/chips/chips_tables.h) and compiles its committed object
(tools/machines/chips/chips.o, ld -r of the source: notes/60 §2). Nothing here is copied from Plaits' tables: exp2
is computed here (as gen_solid.py does); the slave's ratio is Plaits' formula (super_square_oscillator.h) at each
COLOR; the eleven chords are those of Plaits' chord bank (chord_bank.cc, its names and its notes in semitones), folded
into one octave and their doubled notes dropped as its ChordBank::Sort and Reset do (since 2026-11-16 again, notes/83
§10; from §8 to then the stock CHORD machine's). The rest are the maintainer's choices of 2026-11-15 (notes/83 §2):
the arpeggio's tempo a mix (CONTOUR 0 to 63 divisions of the song's tempo, no off since 2026-11-16, notes/83 §9; 64
to 127 free from 16 to 64 Hz), the sweep ±48 semitones at the knob's ends, exponential with 30 ms; and the texts
SHAPE and CONTOUR show. With --cycles it also composes the machine alone through tools/compose.py, which places the
object with tools/relocate.py as any build does, into tweaks/model-cycles_OS1.13/84-chips.json: the card's build
alone, which the web flasher composes in the page (its excludes come from that tweak's conflicts, notes/83 §12).

    python3 tools/gen_chips.py [--check]                                           # tables and object
    python3 tools/gen_chips.py --cycles firmware/model-cycles_OS1.13.syx [--check]   # and the card's tweak
    python3 tools/gen_chips.py --tables-only [--check]                             # no toolchain
"""
import argparse
import json
import math
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PKG = HERE / "machines" / "chips"
TABLES = PKG / "chips_tables.h"

SR = 48000
BLOCK = 32
BPS = SR // BLOCK                   # 1 500 blocks a second

MIX = ((1, "1/4"), (1.5, "1/4T"), (2, "1/8"), (3, "1/8T"), (4, "1/16"), (6, "1/16T"), (8, "1/32"))   # steps a quarter
MIX_SPLIT = 64                      # CONTOUR below: the divisions, 9 values each; from here free
MIX_W = 9
FREE_LO, FREE_HI = 16.0, 64.0       # Hz at CONTOUR 64 and 127, exponential
SW_MAX = 48.0                       # semitones at SWEEP's ends
SW_MS = 30.0                        # the sweep's time constant
SW_CUT = 1 << 19                    # it ends below 2^-12 of its start (48 semitones: 1.2 cent)
BASS_SHIFT = 23                     # a bass step 2^23 (PUNCH on): its peak 7.5 x 2^23 = 0.47 of Q27


def q(x, bits):
    return int(round(x * (1 << bits)))


def l2(x):
    return q(math.log2(x), 24)


def slave_ratio(shape):
    """super_square_oscillator.h: the slave's frequency against the master's."""
    return (0.51 + 0.98 * shape) if shape < 0.5 else 1.0 + 16.0 * (shape - 0.5) * (shape - 0.5)


def arr(name, ctype, vals, per_line=8):
    rows = [", ".join(str(v) for v in vals[i:i + per_line]) for i in range(0, len(vals), per_line)]
    return f"static const {ctype} {name}[{len(vals)}] = {{\n\t" + ",\n\t".join(rows) + "\n};"


# Plaits' chord bank (plaits/dsp/chords/chord_bank.cc, eurorack 08460a6, MIT, Emilie Gillet): its names and notes
PLAITS_CHORDS = (
    ("OCT", (0.00, 0.01, 11.99, 12.00)),
    ("5", (0.00, 7.00, 7.01, 12.00)),
    ("sus4", (0.00, 5.00, 7.00, 12.00)),
    ("m", (0.00, 3.00, 7.00, 12.00)),
    ("m7", (0.00, 3.00, 7.00, 10.00)),
    ("m9", (0.00, 3.00, 10.00, 14.00)),
    ("m11", (0.00, 3.00, 10.00, 17.00)),
    ("69", (0.00, 2.00, 9.00, 16.00)),
    ("M9", (0.00, 4.00, 11.00, 14.00)),
    ("M7", (0.00, 4.00, 7.00, 11.00)),
    ("M", (0.00, 4.00, 7.00, 12.00)),
)


# the names on the display: the OS's big font has capitals, digits and m only, and 3 of its characters fill the window
# (the maintainer, 2026-11-16: « nenne es gleich SUS oder SU4. 4 zeichen werden nicht gut aussehen »)
SHOWN = {"sus4": "SUS"}


def chord_tones(notes):
    """ChordBank::Reset (the count: the notes that only double another, 0.01, 7.01, 11.99 and 12, are not played) and
    Sort (folded into one octave, sorted): the tones the arpeggio plays, semitones above the root."""
    count = sum(1 for s in notes if s not in (0.01, 7.01, 11.99, 12.00))
    rs = []
    for s in notes:
        r = 2 ** (s / 12)
        while r > 2.0:
            r *= 0.5
        rs.append(r)
    rs.sort()
    semis = [12 * math.log2(r) for r in rs[:count]]
    out = [int(round(x)) for x in semis]
    assert all(abs(a - b) < 1e-9 for a, b in zip(out, semis)), (notes, semis)
    return out


def free_hz(c):
    """The free tempo at CONTOUR c (64 .. 127), Hz: FREE_LO x (FREE_HI / FREE_LO)^((c - 64) / 63)."""
    return FREE_LO * (FREE_HI / FREE_LO) ** ((c - MIX_SPLIT) / (127 - MIX_SPLIT))


def tables():
    mix_k = [q(spb * 2 ** 41 / (60 * BPS), 0) for spb, _ in MIX]
    mix_z = [0] + [(v - 1) // MIX_W for v in range(1, MIX_SPLIT)]   # 0 .. 9 1/4 (0 was off until 2026-11-16)
    assert max(mix_k) < 2 ** 31 and max(mix_z) == len(MIX) - 1 and (MIX_SPLIT - 1) % MIX_W == 0
    out = ["/* CHIPS's tables (notes/83), generated by tools/gen_chips.py: do not edit. */",
           "#ifndef CHIPS_TABLES_H", "#define CHIPS_TABLES_H", "#include <stdint.h>", ""]
    consts = [
        ("L2_INC0", l2(440.0) + q(32 - math.log2(SR), 24), "log2 of 440 Hz's phase step (Q32) at 48 kHz, Q24"),
        ("L2_BLK", q(32 - math.log2(BPS), 24), "log2 (2^32 / 1500 blocks a second), Q24"),
        ("RL0", l2(FREE_LO), f"log2 {FREE_LO:g} Hz, Q24: the free tempo at CONTOUR {MIX_SPLIT}"),
        ("RSPAN", l2(FREE_HI / FREE_LO), f"log2 ({FREE_HI:g} / {FREE_LO:g}), Q24: to CONTOUR 127"),
        ("MIX_SPLIT", MIX_SPLIT, "CONTOUR below: a division of the song's tempo; from here free"),
        ("SW_MAX", q(SW_MAX, 16), f"{SW_MAX:g} semitones << 16: the sweep at SWEEP's ends"),
        ("SW_K", min(q(math.exp(-1.0 / (SW_MS / 1000 * BPS)), 31), 0x7fffffff),
         f"e^(-1 / ({SW_MS:g} ms x 1500)), Q31: what is left of the sweep a block later"),
        ("SW_CUT", SW_CUT, "the sweep ends below 2^-12 of its start, Q31"),
        ("BASS_SHIFT", BASS_SHIFT, "a bass step 2^23 with PUNCH, 2^22 without"),
        ("NCHORD", len(PLAITS_CHORDS), "SHAPE's eleven zones of 0 .. 127 (11 or 12 values each), one a chord: "
         + ", ".join(n for n, _ in PLAITS_CHORDS)),
    ]
    for k, v, why in consts:
        out.append(f"#define {k} {v}\t/* {why} */")
    out.append("")
    out.append(arr("EXP2_T", "uint32_t", [q(2 ** (i / 256), 30) for i in range(257)]) + "\t/* 2^(i / 256), Q30 */")
    out.append(arr("LR_T", "int32_t", [l2(slave_ratio(c / 127.0 * 0.995)) for c in range(129)])
               + "\t/* log2 of the slave's ratio at COLOR i (shape = COLOR / 127 x 0.995), Q24 */")
    tones = [chord_tones(nt) for _, nt in PLAITS_CHORDS]
    out.append(arr("ARP_T", "int8_t", [t for ts in tones for t in ts + [0] * (4 - len(ts))], 4)
               + "\t/* [chord][4]: the arpeggio's tones, semitones above the root (Plaits' chords, one octave) */")
    out.append(arr("ARP_N", "uint8_t", [len(ts) for ts in tones], 16) + "\t/* the chord's number of tones */")
    names = ", ".join(f'"{SHOWN.get(n, n)}"' for n, _ in PLAITS_CHORDS)
    out.append(f"static const char CHORD_NAME[{len(PLAITS_CHORDS)}][4] = {{ {names} }};"
               "\t/* SHAPE's text, in the OS's big font: capitals and m only, 3 characters at most */")
    out.append(arr("FREE_HZ", "uint8_t", [int(round(free_hz(c))) for c in range(MIX_SPLIT, 128)], 16)
               + f"\t/* CONTOUR {MIX_SPLIT} .. 127: the free tempo shown, Hz */")
    out.append(arr("MIX_K", "int32_t", mix_k) + "\t/* " + ", ".join(n for _, n in MIX)
               + ": mul(bpm 8.8 << 14, k) = the clock's step a block, Q32 */")
    out.append(arr("MIX_Z", "uint8_t", mix_z, 16) + "\t/* CONTOUR 0 .. 63 -> its division */")
    lv = [((s if s < 16 else 31 - s) << BASS_SHIFT) - (15 << BASS_SHIFT) // 2 for s in range(32)]
    out.append(arr("BASS_LV", "int32_t", lv) + "\t/* the bass's step s, Q27, offset -7.5 steps (PUNCH on) */")
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
        m = compose.load_manifest("chips")
        with tempfile.TemporaryDirectory() as d:
            obj = compose.build_object(m, pathlib.Path(d))
        bad |= bool(compose.emit_bytes(compose.object_path(m), obj, args.check))
        if args.cycles:
            import gen_sdvintage_exact as gx   # noqa: E402
            import gen_sdvintage_7th as g7     # noqa: E402
            img = g7.cycles_main(args.cycles)
            if len(img) != gx.IMAGE_LEN:
                raise SystemExit("!! not the official MAIN OS 1.13")
            tweak, info = compose.compose(img, ["chips"])
            tweak["description"].append("Generated by tools/gen_chips.py through tools/compose.py (notes/83).")
            bad |= bool(gm.emit(compose.DEV / "84-chips.json", json.dumps(tweak, indent=1, ensure_ascii=False) + "\n",
                                args.check))
            p = info["packages"][0]
            print(f"  chips: {len(tweak['writes'])} writes, code {p['code']} bytes, variables {p['bss']} bytes, "
                  f"{info['image']} bytes added to the image, {len(tweak['conflicts'])} conflicts computed")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
