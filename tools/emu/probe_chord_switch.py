#!/usr/bin/env python3
"""Probe T2 of CHORD Tables' new way (notes/66 §27.3, §28.6, §29): what CHORD's render does when the frames it plays
change address, or content, at the same index between two blocks. Nothing is patched: the official MAIN OS 1.13 runs,
and the probe rewrites the stock table's pointers (0x40118590) between two blocks. That is what a table change of
§27.3 does to the setup: other frames at the same SWEEP.

CHORD alone on track 1 (the voice loop 0x400a7d4a, mcengine), a note from block 1, the switch before block SWITCH:
  A. The same frames at other addresses (copies in free memory), and back to the stock addresses at block BACK:
     steps 1 and 3 of §27.3 with the same content. Is the sound identical, sample for sample, to the run without a
     switch?
       a1 SWEEP between two frames (a crossfade), a2 SWEEP on a frame, a3 SWEEP creeping (the index moves too),
       a4 a high note (sub-voices switched off for their pitch keep +176/+180).
       a5 to a7 (notes/66 §29.5): a1, a3 and a4 with the previous pair moved too: before the switch block, every
       sub-voice's +176 and +180 that point at a frame of the old addresses point at the same frame at the new ones,
       as cw_setup would at step 3. The render then sees no change of frame. Identical to the run without a switch?
  B. Another table at the same index (the stock frames in reverse), against two references: the stock table
     throughout, and the other table throughout. Which block hears the new table; what the switch block plays (the
     old frames, the new ones, or a fade between them); the step at the switch against the waves' own steps.
       b1 SWEEP between two frames, b2 SWEEP creeping, b3 the high note.

Lines marked "finding" are the measurements notes/66 §29 asks for. FAIL only when the probe's own set-up does not
hold: the pointers not taken, an access outside memory, the copies written by someone else, the runs before the
switch not identical.

--wav DIR also writes two seconds of CHORD: four notes, each switching table in its middle (step 1 of §27.3, at
once, no fade), the same four notes with only the frames' addresses switched in their middle (step 3 without moving
the previous pair, case A), and the same four notes without a switch, to listen for the click.

--dry runs only what needs no emulator: the stock table as the image holds it, the copies' place in memory, and the
analysis on made-up runs. That is what an agent can run inside a sandbox that forbids Unicorn's JIT.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it:
run it in a normal terminal (model27's .venv-emu). A few seconds; with --wav about a minute.

    python3 tools/emu/probe_chord_switch.py --cycles model-cycles_OS1.13.syx [--wav DIR] [--dry]
"""
import argparse
import pathlib
import struct
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402

CHORD = 5
TABLE = 0x40118590                  # the selector's: frame n (1..32) at entry n - 1 (notes/66 §19.1)
ENTRIES = 32                        # entry 31 repeats entry 30
FRAME1 = 0x40118648                 # entry 0, the stock frame 1, in the OS's data (SDRAM)
SINE = 0x8000eee4
SRAM_LO, SRAM_HI = 0x80000000, 0x80010000
FRAME_LEN = 257
FRAME_BYTES = 4 * FRAME_LEN
COPY_A = 0x407d0000                 # case A's copies: free memory in the voice loop's map, as test_chordtables' sounds
COPY_B = 0x407e0000                 # case B's table
MAP_END = 0x40800000                # mcengine maps 0x40000000..0x40800000
BUSY = [(E.PARAMS, E.PARAMS + 6 * 0x42 + 0x20), (E.STOP, E.STOP + 4), (0x407c0000, 0x407c1000)]
BLOCKS, SWITCH, BACK = 64, 24, 44
TRIG = 1                            # the note's trig block (the first note after the machine change: notes/66 §11.6)
SETTLED = 6                         # from here on the note's onset is over: the waves' own steps are measured from it
SUB, SUB_FRAMES = 120, 168          # CHORD's four sub-voices; +168 f0, +172 f1, +176 and +180 the previous pair
FAIL = []


def check(ok, msg):
    print(("ok      " if ok else "FAIL    ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)
    return ok


def finding(msg):
    print("finding " + msg, flush=True)


# --- the tables ------------------------------------------------------------------------------------------------------
def stock_entries(read32):
    return [read32(TABLE + 4 * i) for i in range(ENTRIES)]


def layout(entries):
    """Case A's pointers (each distinct stock frame copied once, at COPY_A, in the table's order) and case B's (entry i
    holds the frame of stock entry 30 - i, entry 31 repeats entry 30, at COPY_B): [(pointers, [(dst, src)])]."""
    distinct = list(dict.fromkeys(entries))
    where = {a: COPY_A + FRAME_BYTES * i for i, a in enumerate(distinct)}
    table_a = [where[a] for a in entries]
    copies_a = [(where[a], a) for a in distinct]
    copies_b = [(COPY_B + FRAME_BYTES * i, entries[30 - i]) for i in range(31)]
    table_b = [dst for dst, _ in copies_b] + [copies_b[30][0]]
    return (table_a, copies_a), (table_b, copies_b)


def site_checks(img):
    def read32(a):
        return struct.unpack_from(">I", img, a - E.BASE)[0]
    entries = stock_entries(read32)
    check(entries[0] == FRAME1, f"the stock table's entry 0 is frame 1 in the OS's data, {entries[0]:#x}")
    sram = [a for a in entries[1:31] if SRAM_LO <= a < SRAM_HI and a != SINE]
    check(len(set(sram)) == 30, f"entries 1 to 30 are 30 distinct frames in SRAM ({len(set(sram))})")
    check(entries[31] == entries[30], "entry 31 repeats entry 30")
    (ta, ca), (tb, cb) = layout(entries)
    spans = [(d, d + FRAME_BYTES) for d, _ in ca + cb]
    image_end = E.BASE + len(img)
    ok = all(image_end <= lo and hi <= MAP_END for lo, hi in spans)
    ok &= all(hi <= blo or bhi <= lo for lo, hi in spans for blo, bhi in BUSY)
    ok &= all(hi <= lo2 or hi2 <= lo for i, (lo, hi) in enumerate(spans) for lo2, hi2 in spans[i + 1:])
    check(ok, f"the copies ({len(ca)} for A, {len(cb)} for B) lie in mapped memory past the image, apart from each "
              "other and from what the harness uses")
    check(all(ta[i] != entries[i] for i in range(ENTRIES)), "case A: every entry at another address")
    to_a = dict(zip(entries, ta))
    back = {v: k for k, v in to_a.items()}
    check(all(back[to_a[a]] == a for a in entries) and len(back) == len(to_a) == 31,
          "case A: the previous pair's move (a5 to a7) maps each stock frame to its copy and back")
    same = [i for i in range(31) if entries[30 - i] == entries[i]]
    check(same == [15], f"case B: every entry another frame but the middle one ({same})")
    return entries


# --- the runs --------------------------------------------------------------------------------------------------------
class Run:
    """One engine, CHORD on track 1, the probe's tables in memory."""

    def __init__(self, img, note):
        import test_compose as TC           # imports Unicorn's engine: not for --dry
        self.e = TC.engine(img)
        uc = self.e.uc
        self.stock = stock_entries(lambda a: struct.unpack(">I", uc.mem_read(a, 4))[0])
        (self.table_a, self.copies_a), (self.table_b, self.copies_b) = layout(self.stock)
        for dst, src in self.copies_a + self.copies_b:
            uc.mem_write(dst, bytes(uc.mem_read(src, FRAME_BYTES)))
        self.frames = {dst: bytes(uc.mem_read(dst, FRAME_BYTES)) for dst, _ in self.copies_a + self.copies_b}
        self.tables = {"stock": self.stock, "a": self.table_a, "b": self.table_b}
        to_a = dict(zip(self.stock, self.table_a))  # the same frame at case A's address, and back
        self.moves = {"to a": to_a, "to stock": {v: k for k, v in to_a.items()}}
        self.e.set(0, machine=CHORD, note=note, pitch=64, finetune=64, color=32, shape=3, sweep=0, contour=24,
                   punch=0, gate=0, decay=110)

    def use(self, name):
        self.e.uc.mem_write(TABLE, b"".join(struct.pack(">I", p) for p in self.tables[name]))

    def subs(self):
        """Track 1's four sub-voices: (+168, +172, +176, +180)."""
        v = E.VOICE0
        return [struct.unpack(">4I", self.e.uc.mem_read(v + SUB * j + SUB_FRAMES, 16)) for j in range(4)]

    def move_prev(self, name):
        """Every sub-voice's previous pair (+176, +180) moved to the same frames at the other addresses."""
        mapping = self.moves[name]
        for j in range(4):
            a = E.VOICE0 + SUB * j + SUB_FRAMES + 8
            pair = struct.unpack(">2I", self.e.uc.mem_read(a, 8))
            self.e.uc.mem_write(a, struct.pack(">2I", *(mapping.get(p, p) for p in pair)))

    def play(self, sweep, plan, blocks=BLOCKS, trigs=(TRIG,), moves=None):
        """plan: {block: table name}, written before that block; moves: {block: "to a" or "to stock"}, the previous
        pair moved before that block. Returns the output (blocks x 32) and the sub-voices after each block."""
        out, subs = [], []
        for b in range(blocks):
            if b in plan:
                self.use(plan[b])
            if moves and b in moves:
                self.move_prev(moves[b])
            self.e.set(0, sweep=sweep(b))
            out.append(self.e.block(1 if b in trigs else 0)[0])
            subs.append(self.subs())
        return np.array(out), subs

    def intact(self):
        uc = self.e.uc
        return all(bytes(uc.mem_read(a, FRAME_BYTES)) == f for a, f in self.frames.items())


def run(img, note, sweep, plan, moves=None):
    r = Run(img, note)
    out, subs = r.play(sweep, plan, moves=moves)
    check(not r.e.unmapped, f"no access outside memory ({r.e.unmapped[:3]})")
    check(r.intact(), "the probe's copies unchanged after the run")
    return r, out, subs


# --- the analysis (also run on made-up data by --dry) ----------------------------------------------------------------
def first_diff(x, y):
    d = np.nonzero(np.any(x != y, axis=1))[0]
    return int(d[0]) if len(d) else None


def equal_from(x, y):
    """The first block from which x and y are equal to the end, or None."""
    same = np.all(x == y, axis=1)
    k = len(same)
    while k > 0 and same[k - 1]:
        k -= 1
    return k if k < len(same) else None


def steps(x, lo, hi):
    """The largest step between neighbouring samples in blocks lo..hi - 1 (the step into block lo included)."""
    flat = x.reshape(-1).astype(np.int64)
    a, b = max(lo * 32 - 1, 0), hi * 32
    return int(np.max(np.abs(np.diff(flat[a:b])))) if b - a > 1 else 0


def fade_fit(sw, old, new):
    """What the switch block plays: max |difference| to the old frames, the new ones, and a linear fade from one to
    the other across the block ((n + 1) / 32 and n / 32)."""
    n = np.arange(32)
    fades = {"fade (n + 1)/32": old + (new - old) * (n + 1) // 32, "fade n/32": old + (new - old) * n // 32}
    out = {"old": int(np.max(np.abs(sw - old))), "new": int(np.max(np.abs(sw - new)))}
    out.update({k: int(np.max(np.abs(sw - v))) for k, v in fades.items()})
    return out


def db(x, ref):
    return 20 * np.log10(max(x, 1) / max(ref, 1))


def analyse_a(key, ref, sw):
    check(first_diff(ref[:SWITCH], sw[:SWITCH]) is None, f"{key}: before the switch, identical to the run without it")
    k = first_diff(ref, sw)
    if k is None:
        finding(f"{key}: identical to the run without a switch, sample for sample, through both switches "
                f"(blocks {SWITCH} and {BACK})")
        return True
    d = np.abs(ref - sw)
    peak = int(np.max(np.abs(ref[TRIG + 2:])))
    finding(f"{key}: differs from block {k}: at most {int(d.max())} ({db(int(d.max()), peak):.1f} dB under the "
            f"note's peak {peak}), in blocks {sorted(set(np.nonzero(np.any(d, axis=1))[0].tolist()))[:12]}; "
            f"equal again from block {equal_from(ref, sw)}")
    return False


def analyse_b(key, old, new, sw):
    check(first_diff(old[:SWITCH], sw[:SWITCH]) is None, f"{key}: before the switch, identical to the stock table")
    fit = fade_fit(sw[SWITCH], old[SWITCH], new[SWITCH])
    best = min(fit, key=fit.get)
    eq = equal_from(new, sw)
    own = max(steps(old, SETTLED, BLOCKS), steps(new, SETTLED, BLOCKS))   # past the note's first blocks
    at = steps(sw, SWITCH, SWITCH + 1)
    finding(f"{key}: the switch block (max |difference|): " + ", ".join(f"{k} {v}" for k, v in fit.items())
            + f" -> closest: {best}")
    finding(f"{key}: equal to the other table throughout from block {eq} (the switch at {SWITCH})")
    finding(f"{key}: the largest step into and inside the switch block {at}, the waves' own largest step {own} "
            f"({db(at, own):+.1f} dB)")
    return fit, eq, at, own


def sweeps():
    return {
        "between": lambda b: 50,            # i = 12, f0 = entry 11, f1 = entry 12, crossfade 1/2
        "on": lambda b: 48,                 # i = 12, crossfade 0
        "creeping": lambda b: 30 + b,       # a new index every 4 blocks; i = 13 at the switch
    }


def self_test():
    """The analysis on made-up runs, so that --dry checks the arithmetic."""
    rng = np.random.default_rng(1)
    old = rng.integers(-1 << 20, 1 << 20, (BLOCKS, 32))
    new = rng.integers(-1 << 20, 1 << 20, (BLOCKS, 32))
    sw = old.copy()
    sw[SWITCH:] = new[SWITCH:]
    n = np.arange(32)
    sw[SWITCH] = old[SWITCH] + (new[SWITCH] - old[SWITCH]) * (n + 1) // 32
    fit = fade_fit(sw[SWITCH], old[SWITCH], new[SWITCH])
    check(min(fit, key=fit.get) == "fade (n + 1)/32" and fit["fade (n + 1)/32"] == 0, "self-test: a fade is seen")
    check(equal_from(new, sw) == SWITCH + 1, "self-test: equal from the block after the fade")
    sw2 = old.copy()
    sw2[SWITCH:] = new[SWITCH:]
    check(min(fade_fit(sw2[SWITCH], old[SWITCH], new[SWITCH]).values()) == 0
          and equal_from(new, sw2) == SWITCH, "self-test: a switch at once is seen")
    check(first_diff(old, old) is None and first_diff(old, sw2) == SWITCH, "self-test: the first differing block")
    x = np.zeros((4, 32), dtype=np.int64)
    x[2, 0] = 100
    check(steps(x, 2, 3) == 100 and steps(x, 0, 2) == 0, "self-test: the steps, the one into a block included")


def wav_files(img, out_dir):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n, note_len = 3000, 750                     # two seconds, four notes of half a second
    trigs = tuple(range(TRIG, n, note_len))
    what = {"chord-switch-at-once": ("b", "another table in the middle of each note"),
            "chord-same-frames-moved": ("a", "the same frames at other addresses in the middle of each note"),
            "chord-no-switch": (None, "the same notes")}
    for name, (other, text) in what.items():
        r = Run(img, 60)
        plan = {}
        if other:
            for k, b in enumerate(range(TRIG + note_len // 2, n, note_len)):
                plan[b] = other if k % 2 == 0 else "stock"
        out, _ = r.play(lambda b: 50, plan, blocks=n, trigs=trigs)
        path = out_dir / f"{name}.wav"
        E.wav(str(path), out.reshape(-1))
        print(f"wrote {path} ({text})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="the official model-cycles_OS1.13.syx")
    ap.add_argument("--wav", help="a folder for the two listening files")
    ap.add_argument("--dry", action="store_true", help="only what needs no emulator")
    args = ap.parse_args()
    img = T.main_os_from_syx(args.cycles)
    print("0. the stock table and the probe's copies")
    site_checks(img)
    self_test()
    if args.dry:
        print("dry: no emulation" + (" (ALL OK so far)" if not FAIL else f" ({len(FAIL)} FAIL)"))
        sys.exit(1 if FAIL else 0)
    sw = sweeps()

    print("A. the same frames at other addresses, then back")
    moved = {SWITCH: "to a", BACK: "to stock"}
    for key, note, sweep, moves in (("a1", 60, "between", None), ("a2", 60, "on", None), ("a3", 60, "creeping", None),
                                    ("a4", 96, "between", None), ("a5", 60, "between", moved),
                                    ("a6", 60, "creeping", moved), ("a7", 96, "between", moved)):
        r0, ref, _ = run(img, note, sw[sweep], {})
        r1, out, subs = run(img, note, sw[sweep], {SWITCH: "a", BACK: "stock"}, moves)
        if moves:
            key += ", the previous pair moved too"
        copies = {d for d, _ in r1.copies_a}
        check(all(s[0] in copies and s[1] in copies for s in subs[SWITCH]),
              f"{key}: after block {SWITCH} every sub-voice's two frames are copies")
        check(all(s[0] in r1.stock and s[1] in r1.stock for s in subs[BACK]),
              f"{key}: after block {BACK} every sub-voice's two frames are the stock ones again")
        analyse_a(f"{key} (note {note}, SWEEP {sweep})", ref, out)

    print("B. another table at the same index")
    for key, note, sweep in (("b1", 60, "between"), ("b2", 60, "creeping"), ("b3", 96, "between")):
        _, old, _ = run(img, note, sw[sweep], {})
        _, new, _ = run(img, note, sw[sweep], {0: "b"})
        r2, out, subs = run(img, note, sw[sweep], {SWITCH: "b"})
        table_b = {d for d, _ in r2.copies_b}
        check(all(s[0] in table_b and s[1] in table_b for s in subs[SWITCH]),
              f"{key}: after block {SWITCH} every sub-voice's two frames are the other table's")
        analyse_b(f"{key} (note {note}, SWEEP {sweep})", old, new, out)

    if args.wav:
        print("listening files")
        wav_files(img, args.wav)
    print("ALL OK" if not FAIL else f"{len(FAIL)} FAIL")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
