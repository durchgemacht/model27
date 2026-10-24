#!/usr/bin/env python3
"""Measurement for notes/66 §18: the lines of SDRAM CHORD reads and writes per audio block, with the stock table and
with a CHORD Tables table.

The maintainer's report of 2026-10-24: the whole interface lags, more with every CHORD track playing a table. The
stock frames are in the internal SRAM (one cycle an access, not cached), a table's frames in SDRAM, through the data
cache (ACR0 = 0x4007e020, set at 0x40000552: 0x40000000..0x47ffffff cacheable, copyback). The MCF54415 has an 8 KB
data cache of 16-byte lines, and its SDRAM is DDR2 on 8 bits (notes/26 §1). This probe counts, in the real voice loop
(0x400a7d4a, blocks of 32 frames at 48 kHz), what each case costs in lines:
  - distinct lines: the 16-byte lines of SDRAM the voice loop reads or writes in a block, split into the table's
    frames (the RAM claim 0x43400000..0x43700000) and the rest. It is the number of line fills when everything else
    of the block (mixing, effects, the interface) evicts the cache between two blocks, as notes/26 §1 found with six
    voices: "almost every line is read again from SDRAM in every block";
  - cache misses: the same accesses through a model of the data cache (8 KB, 4 ways, 16-byte lines, LRU, write
    allocate, notes/26 §6), the voice loop alone from block to block; with dirty lines written back. A lower bound;
  - the internal SRAM's lines, for the comparison: free of the cache;
  - the first block of the note (block 2: the note starts a block after its trig, notes/66 §11.6), then the mean and
    the maximum of the next blocks, minus the voice loop with no note (the same tracks, no trig).

Cases: one CHORD track (track 1, machine defaults, note 60 or 84, SWEEP still at 24 or moving) and six CHORD tracks
(SWEEP still, 24 to 104, or moving: each track its own frames), for the stock OS, CHORD Tables at Wavetable 0, CHORD Tables with a table (six
tables, one per track, or the same table on all six). A table's frames are the stock frames in another order: only
their addresses matter here. The emulator does not time memory: lines are what it can count, not their cost in time.

Needs Unicorn and numpy (pip install unicorn numpy) and m68k-elf-objdump; Unicorn's JIT does not run inside a
sandbox that forbids it: run it in a normal terminal (model27's .venv-emu has both). About a minute.

    python3 tools/emu/probe_chord_lines.py --cycles model-cycles_OS1.13.syx [--blocks 22]
"""
import argparse
import pathlib
import struct
import sys

from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import test_chordtables as CT       # noqa: E402
import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

SDRAM = (0x40000000, 0x48000000)    # cacheable through ACR0 (0x40000552)
SRAM = (0x80000000, 0x80010000)     # the internal SRAM, 64 KB, not cached
CLAIM = (CT.RAM >> 4, CT.RAM_END >> 4)
WAYS, SETS = 4, 8192 // (16 * 4)    # 8 KB of 16-byte lines, 4 ways: 128 sets


class Cache:
    """The data cache's model: LRU in each set, write allocate, copyback."""

    def __init__(self):
        self.sets = [[] for _ in range(SETS)]       # [line, dirty], least recent first

    def access(self, line, write):
        """(fill, write back) for one access to a line."""
        s = self.sets[line % SETS]
        for i, e in enumerate(s):
            if e[0] == line:
                s.append(s.pop(i))
                e[1] |= write
                return 0, 0
        back = 0
        if len(s) == WAYS:
            back = s.pop(0)[1]
        s.append([line, write])
        return 1, back


class Probe(CT.Voice):
    """The voice loop of a build, every SDRAM and SRAM access of a block recorded by line."""

    def __init__(self, img, runtime=None, tweak=None, syms=None, tracks=(0,), note=60):
        super().__init__(img, runtime, tweak, syms)
        self.on = tuple(tracks)
        for t in range(6):
            if t in self.on:
                self.e.set(t, machine=CT.CHORD, note=note, pitch=64, finetune=64, color=3, shape=43, sweep=24 + 16 * t,
                           contour=64, punch=0, gate=0, decay=64)
            else:
                self.e.set(t, machine=0x7f)         # no voice: the loop skips it (as part C of test_chordtables)
            if t:
                self.e.uc.mem_write(CT.CUR_SNDS + 4 * t, struct.pack(">I", 0))   # k 30 from the targets
        self.rec = None
        self.cache = Cache()
        self.emac_loads = 0
        hk = lambda uc, access, addr, size, value, ud: self._note(addr, size, access == UC_MEM_WRITE)
        self.e.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, hk, begin=SDRAM[0], end=SDRAM[1] - 1)
        self.e.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, hk, begin=SRAM[0], end=SRAM[1] - 1)
        # a MAC with a load is run by emac.py, which reads the long with uc.mem_read: no hook sees it, so it is noted
        # here, from the address the instruction computes
        ea = self.e.emac._ea

        def ea_noted(spec):
            ad, post = ea(spec)
            if self.rec is not None:
                self.emac_loads += 1
            self._note(ad, 4, False)
            return ad, post
        self.e.emac._ea = ea_noted

    def _note(self, addr, size, write):
        if self.rec is None:
            return
        lines = range(addr >> 4, ((addr + size - 1) >> 4) + 1)
        if SDRAM[0] <= addr < SDRAM[1]:
            self.rec[0].extend((line, write) for line in lines)
        elif SRAM[0] <= addr < SRAM[1]:
            self.rec[1].update(lines)

    def wavetables(self, n):
        """Wavetable n (0: the stock table) on every CHORD track: n, n + 1, ... one per track, or n on all six when
        n is negative."""
        for i, t in enumerate(self.on):
            self.k30(0 if not n else -n if n < 0 else n + i, track=t)

    def measure(self, blocks, trig=True, sweep=None):
        """Per block: (distinct SDRAM lines, of them in the RAM claim, distinct SRAM lines, cache fills, write backs)."""
        out = []
        mask = sum(1 << t for t in self.on)
        for b in range(blocks):
            if sweep:
                for t in self.on:
                    self.e.set(t, sweep=sweep(b, t))
            self.rec = ([], set())
            self.e.block(mask if trig and b == 1 else 0)
            acc, sram = self.rec
            self.rec = None
            lines = {line for line, _ in acc}
            fills = backs = 0
            for line, w in acc:
                f, k = self.cache.access(line, w)
                fills += f
                backs += k
            out.append((len(lines), sum(CLAIM[0] <= x < CLAIM[1] for x in lines), len(sram), fills, backs))
        return out


def moving(b, t):
    return CT.sweeps(b, t)


def summary(run, idle, n):
    """The note's first block and the mean / max of the n next, minus the loop with no note: per column."""
    first = [a - b for a, b in zip(run[2], idle[2])]
    rest = [[a - b for a, b in zip(r, i)] for r, i in zip(run[3:3 + n], idle[3:3 + n])]
    mean = [sum(c) / len(c) for c in zip(*rest)]
    peak = [max(c) for c in zip(*rest)]
    return first, mean, peak


def report(key, name, s):
    first, mean, peak = s
    print(f"finding  {key}: {name}: SDRAM lines {mean[0]:.0f} a block (max {peak[0]}, first {first[0]}), "
          f"{mean[1]:.0f} of them a table's frames; cache misses {mean[3]:.0f} (write backs {mean[4]:.0f}); "
          f"SRAM lines {mean[2]:.0f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--blocks", type=int, default=22, help="blocks measured after the note's first one")
    args = ap.parse_args()
    n, total = args.blocks, args.blocks + 3
    stock = T.main_os_from_syx(args.cycles)
    tweak, info, img, runtime = TC.built(stock, ["chordtables"])
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    ref = CT.Voice(stock)
    frames = [ref.frame(CT.SINE)] + [ref.frame(struct.unpack(">I", ref.e.uc.mem_read(CT.CHORD_TABLE + 4 * i, 4))[0])
                                     for i in range(31)]
    built = (img, runtime, tweak, syms)
    loads = {}

    def case(key, name, args_, tracks, note=60, tables=0, sweep=None):
        def make():
            p = Probe(*args_, tracks=tracks, note=note)
            if tables:
                for i in range(len(tracks) if tables > 0 else 1):
                    p.table(i, i, frames[i:] + frames[:i] if i else frames[::-1])
            p.wavetables(1 if tables > 0 else -1 if tables < 0 else 0)
            return p
        p = make()
        run = p.measure(total, sweep=sweep)
        idle = make().measure(total, trig=False, sweep=sweep)
        ok = not p.e.unmapped
        loads[name] = loads.get(name, 0) + p.emac_loads
        s = summary(run, idle, n)
        report(key, name, s)
        return s, ok

    print("One CHORD track (track 1), the others off")
    for note in (60, 84):
        for still in (True, False):
            key = f"1 track, note {note}, SWEEP {'24' if still else 'moving'}"
            sw = None if still else moving
            a, ok_a = case(key, "stock OS", (stock,), (0,), note, sweep=sw)
            b, ok_b = case(key, "Wavetable 0", built, (0,), note, sweep=sw)
            c, ok_c = case(key, "a table", built, (0,), note, tables=1, sweep=sw)
            check(ok_a and ok_b and ok_c and a[1][1] == b[1][1] == 0 and c[1][1] > 0,
                  f"{key}: nothing unmapped; the stock OS and Wavetable 0 read no table frames, a table does "
                  f"({c[1][1]:.0f} lines a block)")
            print(f"finding  {key}: a table adds {c[1][0] - a[1][0]:+.0f} SDRAM lines a block against the stock OS "
                  f"({c[1][3] - a[1][3]:+.0f} misses with the voice loop alone); Wavetable 0 "
                  f"{b[1][0] - a[1][0]:+.0f}")

    print("Six CHORD tracks")
    for still in (True, False):
        key = f"6 tracks, note 60, SWEEP {'still' if still else 'moving'}"
        sw = None if still else moving
        a, ok_a = case(key, "stock OS", (stock,), tuple(range(6)), sweep=sw)
        b, ok_b = case(key, "Wavetable 0", built, tuple(range(6)), sweep=sw)
        c, ok_c = case(key, "six tables", built, tuple(range(6)), tables=1, sweep=sw)
        d, ok_d = case(key, "one table on all six", built, tuple(range(6)), tables=-1, sweep=sw)
        # each track reads its own two frames (its SWEEP differs): one shared table reads about as many lines as six
        check(ok_a and ok_b and ok_c and ok_d and a[1][1] == b[1][1] == 0 and c[1][1] > 0 and d[1][1] > 0,
              f"{key}: nothing unmapped; the stock OS and Wavetable 0 read no table frames, six tables and one shared "
              f"table do ({c[1][1]:.0f} and {d[1][1]:.0f} lines a block)")
        print(f"finding  {key}: six tables add {c[1][0] - a[1][0]:+.0f} SDRAM lines a block against the stock OS "
              f"({c[1][3] - a[1][3]:+.0f} misses with the voice loop alone), one shared table "
              f"{d[1][0] - a[1][0]:+.0f} ({d[1][3] - a[1][3]:+.0f})")
    print("finding  MACs with a load (run by emac.py, noted from their address): "
          + ", ".join(f"{k} {v}" for k, v in loads.items()))
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
