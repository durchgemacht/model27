#!/usr/bin/env python3
"""Proof of CHORD Tables 0.3 (notes/66 §27 to §32) on the OS's own code: the package tools/machines/chordtables/ as
tools/compose.py composes it, alone and next to SAMPLE, the effect slots and the filter slot.

Since 0.3 the pattern chooses one table for every CHORD track (PATTERN + SWEEP, the header's bytes 36 and 37) and the
whole table takes the stock table's place in SRAM. The reference for the sound is the stock OS itself, its pointer
table 0x40118590 rewritten in the same blocks to point at the table's frames: a CHORD track then plays the table as
the stock function plays it, and 0.3 must sound the same, sample for sample, through every change, every copy into
SRAM and every move of the voices' pointers (notes/66 §29.6).

For each selection (by default: chordtables; sampler,chordtables; chordtables,digidelay; chordtables,crush):
  0. start-up and the sites: the bootstrap's own depacker reads the grown OS back, the boot hook copies the payload;
     CHORD's call -> cw_setup, the tick -> ct_hook_tick (or the dispatcher with SAMPLE), the knob lookup's vtable entry
     -> ct_knob, 0x4001f886 -> ct_keys, PATTERN's release, the header's loader and initializer -> ct_release, ct_load,
     ct_init; each chain hook's entry behind, read in the placed code: the stock lookup or the part's (sc_knob,
     fl_knob), fl_keys or fx_keys, fx_release, fx_load, fx_init, or 0 (notes/66 §31.4);
  P1. the stock table (the voice loop, six CHORD tracks, a scenario of notes, high ones that switch sub-voices off,
     SWEEP creeping, jumping, negative, fast, a track to TONE and back): the patterns unlinked, a pattern at 0, one
     choosing an empty slot, one with a wrong check byte, one past 127: identical to the stock OS, sample for sample;
     the stock frames in SRAM never written, nothing copied, the stock function called for every CHORD voice;
  P2. a pattern's table, against the stock OS whose pointer table is switched in the same blocks: a change to a table,
     a change during a change, back to the stock table, a table that comes back while some of its frames still sit in
     SRAM, the playing pattern's value edited, an empty slot, a wrong check, the loader's new buffer for a table, the
     patterns unlinked: identical on the six tracks, sample for sample; and the move late (a table chosen before it):
     the stock table until the move;
  P3. in every P2 run: no slot written while a sub-voice points at it, nothing but the package writing the slots;
     every change home in some blocks (findings: how many); at the end, back at the stock table, every slot holding
     its stock frame again and the stock function called;
  P4. the pattern (as test_fxslot.py §5): the stock loader (0x4005b3b4) and initializer (0x40061526) leave bytes 36 and
     37 as the buffer held them; with the build: copied when their check holds, 0 and 0x5a otherwise, 0 and 0x5a in a
     new header, the header untouched with keep, a whole pattern saved, loaded and copied, an old file; with the effect
     slots (the chain to fx_load, fx_init) their bytes 29 to 31 as test_fxslot.py expects them too; every write masked;
  P5. the gesture: ct_knob (the lookup behind it intercepted) gives descriptor 10 for PATTERN + SWEEP on CHORD
     (descriptor 73) and writes its rows and its interface object, the lookup's answer otherwise; ct_keys, as the
     encoder handler calls it, steps the shown pattern's value (two steps a table, 0 to 127), calls the header's notify,
     ends the handler; anything else goes to the entry behind or isKeyHeld(2); ct_fmt prints the table; PATTERN's
     release (test_fxslot.py's test): the selection's wait cleared;
  L. the loader (ct_hook_tick in the UI harness), the four file system calls answered by this proof: the first tick's
     move; the scan of /Wavetables/01 to /63, one a tick (64 never read); the OS's sine put in front of a file whose
     first frame is not one, a sine within 4 steps taken as one; the tables built exactly as computed here; added,
     replaced, deleted files, the drive not mounted or locked, no free buffer; a retired buffer kept while it is wanted
     or a voice points into it, then freed with its slots' tags cleared;
  C. the cost by the standard's method (STANDARD.md §6): instructions per block per voice in the real voice loop,
     CHORD alone on track 1: the stock OS, 0.3 at the stock table, 0.3 with a table at home, the blocks of a change.

P1, P2, P3 and C run for chordtables and sampler,chordtables; every other part for every selection (--machines runs
everything for the selections it names).

Needs Unicorn and numpy (pip install unicorn numpy) and m68k-elf-objdump; Unicorn's JIT does not run inside a
sandbox that forbids it: run it in a normal terminal (model27's .venv-emu has both). A few minutes.

    python3 tools/emu/test_chordtables.py --cycles model-cycles_OS1.13.syx [--machines chordtables,sampler]
    python3 tools/emu/test_chordtables.py --cycles model-cycles_OS1.13.syx --dry    # builds, sites, chains; no Unicorn
"""
import argparse
import math
import pathlib
import random
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compose                      # noqa: E402
import mcengine as E                # noqa: E402
import test_compose as TC           # noqa: E402
import test_fxslot as F             # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_shortcuts as S          # noqa: E402
import wavetable as W               # noqa: E402  (tools/wavetable.py, the converter of notes/66 §4)
from test_sdvintage_7th import check  # noqa: E402

SELECTIONS = [["chordtables"], ["sampler", "chordtables"], ["chordtables", "digidelay"], ["chordtables", "crush"]]
AUDIO = {"chordtables", "sampler+chordtables"}  # P1, P2, P3 and C by default
SETUP, CALL_AT, TICK_AT, GETTER = 0x400a8080, 0x400ab15e, 0x400075f0, 0x40076be4
KNOB_VT, KEYS_AT, RELEASE_AT, LOAD_AT, INIT_AT = 0x401005a8, 0x4001f886, 0x40020dca, 0x4005b4b0, 0x4006155e
LOOKUP = 0x4001e814                             # the stock knob lookup
CHORD = 5
RAM, RAM_END = 0x43400000, 0x43700000           # the package's RAM claim
TABLES, STAGE_BYTES, BUF_BYTES, POINTERS, FRAMES, FRAME_LEN = 63, 16384, 33040, 33, 32, 257
BUFFERS = TABLES + 8
SINE, CHORD_TABLE, FRAME1 = 0x8000eee4, 0x40118590, 0x40118648
OPEN, CLOSE, ENTRY, READ = 0x4007bc5e, 0x4007bc1c, 0x4007de78, 0x4007baaa
MOUNTED, FS_LOCK, RUNNING, INDEX_COUNT, INDEX = 0x40f07cf4, 0x40fe6df0, 0x422fef30, 0x401fb8a0, 0x401fb8a4
TASK = 0x93f80000                               # the running task, as the proof names it
SRAM_LO, SRAM_HI = 0x80000000, 0x80010000
HDR = 36                                        # the header's byte 36: the value 0..127; 37: 0x5a + byte 36
SWEEP_DESC, TABLE_DESC = 73, 10                 # Chord Sweep; the table's display (notes/66 §28)
DESC, DSTRIDE = 0x4010dce0, 0x38
PAT_FIX = 0x94000000                            # the patterns in the voice loop's memory
MAPS = ((RAM, RAM_END - RAM), (0x40a00000, 0x100000), (0x40f00000, 0x100000), (PAT_FIX, 0x40000))


def buf(b):
    return RAM + STAGE_BYTES + b * BUF_BYTES


STOCK = buf(BUFFERS)                            # the stock frames' copy, after the 71 buffers


def stock_slots(img):
    """Positions 2..31's slots: the stock table's entries 1..30, 30 distinct frames in SRAM (notes/66 §19.1)."""
    return [struct.unpack_from(">I", img, CHORD_TABLE + 4 * (i - 1) - E.BASE)[0] for i in range(2, FRAMES)]


def frame_pointers(uc):
    """The six voices' frame pointers: +168, +172, +176 and +180 of their four sub-voices."""
    raw = bytes(uc.mem_read(E.VOICE0, 6 * E.VSTRIDE))
    return [struct.unpack_from(">I", raw, t * E.VSTRIDE + 120 * j + 168 + 4 * i)[0]
            for t in range(6) for j in range(4) for i in range(4)]


def be32s(words):
    return b"".join(struct.pack(">I", w & 0xffffffff) for w in words)


def jsr(va):
    return b"\x4e\xb9" + struct.pack(">I", va)


def finding(msg):
    print("finding  " + msg)


# --- 0. start-up, the sites, the chains -------------------------------------------------------------------------------
def chains_of(read, syms):
    """Each chain hook's entry behind, read in the placed code: ct_knob's first jsr, the immediates of ct_keys and
    ct_release (move.l #imm,-(sp)), ct_load (move.l #imm,d0), ct_init (move.l #imm,d1)."""
    def imm(sym, op, n=64):
        code = read(syms[sym], n)
        i = code.find(op)
        return struct.unpack(">I", code[i + len(op):i + len(op) + 4])[0] if i >= 0 else None
    return {"knob": imm("ct_knob", b"\x4e\xb9"), "keys": imm("ct_keys", b"\x2f\x3c"),
            "release": imm("ct_release", b"\x2f\x3c"), "load": imm("ct_load", b"\x20\x3c"),
            "init": imm("ct_init", b"\x22\x3c")}


def site_tests(key, ids, tweak, img, runtime, info):
    """Read in the built bytes, no emulator: the patched OS (img) and the payload as the boot hook leaves it."""
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}

    def at(va, n):
        if va >= E.PAYLOAD_DST:
            return bytes(runtime[va - E.PAYLOAD_DST:va - E.PAYLOAD_DST + n])
        return bytes(img[va - E.BASE:va - E.BASE + n])
    check(at(CALL_AT, 6) == jsr(syms["cw_setup"]), f"{key}: {CALL_AT:#x} -> jsr cw_setup ({syms['cw_setup']:#x})")
    tick = syms.get("dp_tick", syms["ct_hook_tick"])
    check(at(TICK_AT, 6) == jsr(tick), f"{key}: {TICK_AT:#x} -> jsr {'dp_tick' if 'dp_tick' in syms else 'ct_hook_tick'}")
    check(at(KNOB_VT, 4) == struct.pack(">I", syms["ct_knob"]) and at(KEYS_AT, 6) == jsr(syms["ct_keys"])
          and at(RELEASE_AT, 6) == jsr(syms["ct_release"]) and at(LOAD_AT, 6) == jsr(syms["ct_load"])
          and at(INIT_AT, 6) == jsr(syms["ct_init"]),
          f"{key}: the knob lookup's entry -> ct_knob, {KEYS_AT:#x} -> ct_keys, {RELEASE_AT:#x} -> ct_release, "
          f"{LOAD_AT:#x} -> ct_load, {INIT_AT:#x} -> ct_init (in front of the parts, notes/66 §30.2)")
    got = chains_of(at, syms)
    sc, fl, fx = "sc_knob" in syms, "fl_knob" in syms, "fx_keys" in syms
    want = {"knob": syms["fl_knob"] if fl else syms["sc_knob"] if sc else LOOKUP,
            "keys": syms["fl_keys"] if fl else syms["fx_keys"] if fx else 0,
            "release": syms["fx_release"] if fx else 0, "load": syms["fx_load"] if fx else 0,
            "init": syms["fx_init"] if fx else 0}
    name = {v: k for k, v in syms.items() if k in ("fl_knob", "sc_knob", "fl_keys", "fx_keys", "fx_release", "fx_load",
                                                   "fx_init")}
    name.update({LOOKUP: "the stock lookup", 0: "0"})
    check(got == want, f"{key}: the entries behind the chain hooks: "
          + ", ".join(f"{k} {name.get(v, hex(v) if v is not None else '?')}" for k, v in got.items()))
    check(info["end"] <= RAM, f"{key}: the payload ({info['pay']:#x}..{info['end']:#x}) below the RAM claim {RAM:#x}")
    return syms


# --- the voice loop -----------------------------------------------------------------------------------------------------
class Voice:
    """The voice loop of a build, or of the stock OS, with the RAM claim mapped, CHORD on the given tracks and the
    patterns as the OS links them (test_fxslot.py's Patterns, four of them): the playing pattern's header is what
    cw_setup reads."""

    def __init__(self, img, runtime=None, tweak=None, syms=None, tracks=range(6)):
        e = self.e = TC.engine(img, runtime, tweak)
        for lo, n in MAPS:
            e.uc.mem_map(lo, n)
        self.syms = syms or {}
        self.pat = F.Patterns(lambda va, d: e.uc.mem_write(va, d), PAT_FIX, count=4)
        self.pat.link(playing=0)
        self.entries = [self.r32(CHORD_TABLE + 4 * i) for i in range(32)]
        self.setups = 0

        def hk(uc, a, s, u_):
            self.setups += 1
        e.uc.hook_add(UC_HOOK_CODE, hk, begin=SETUP, end=SETUP)
        self.tracks = list(tracks)
        for t in self.tracks:
            e.set(t, machine=CHORD, note=60, pitch=64, finetune=64, color=3, shape=43, sweep=24, contour=64,
                  punch=0, gate=0, decay=64)

    def r32(self, a):
        return struct.unpack(">I", self.e.uc.mem_read(a, 4))[0]

    def frame(self, va):
        return bytes(self.e.uc.mem_read(va, 4 * FRAME_LEN))

    def value(self, n, v, bad=False):
        """Pattern n's bytes 36 and 37: the value, its check (or a wrong one)."""
        self.e.uc.mem_write(self.pat.headers[n] + HDR, bytes([v & 0xff, (0x5a + v + (1 if bad else 0)) & 0xff]))

    def table(self, slot, b, frames):
        """A table in buffer b (its frames, each 257 longs as bytes, and 33 pointers, the sine at 0); published in slot
        (0-based) when this is a build. Returns its pointers."""
        base = buf(b)
        ptrs = [base + 4 * POINTERS + 4 * FRAME_LEN * s for s in range(FRAMES)]
        for s in range(FRAMES):
            self.e.uc.mem_write(ptrs[s], frames[s])
        ptrs = [SINE] + ptrs[1:] + [ptrs[-1]]
        self.e.uc.mem_write(base, be32s(ptrs))
        if slot is not None and self.syms:
            self.e.uc.mem_write(self.syms["ct_slot"] + 4 * slot, struct.pack(">I", base))
            self.e.uc.mem_write(self.syms["ct_owner"] + b, bytes([slot + 1]))
        return ptrs

    def unslot(self, slot):
        self.e.uc.mem_write(self.syms["ct_slot"] + 4 * slot, struct.pack(">I", 0))

    def point(self, ptrs):
        """The stock OS's pointer table at a list's frames (positions 1..32 at entries 0..31), or back at its own."""
        self.e.uc.mem_write(CHORD_TABLE, be32s(self.entries if ptrs is None else ptrs[1:]))

    def move(self):
        """The move (notes/66 §31), by the package's own tick, with the drive not mounted so that it does nothing
        else. Returns ct_moved (1)."""
        self.e.call(self.syms["ct_tick"])
        return self.r32(self.syms["ct_moved"])


class Watch:
    """P3: every write into the 30 slots, its writer and whether a voice points at the frame it starts."""

    def __init__(self, v, slots):
        self.v, self.writes, self.foreign, self.hits, self.last = v, 0, [], [], None
        runs = []
        for a in sorted(slots):
            if runs and a == runs[-1][1]:
                runs[-1][1] = a + 4 * FRAME_LEN
            else:
                runs.append([a, a + 4 * FRAME_LEN])
        self.runs = runs
        for lo, hi in runs:
            v.e.uc.hook_add(UC_HOOK_MEM_WRITE, self._hook, begin=lo, end=hi - 1)

    def _hook(self, uc, access, addr, size, value, ud):
        lo = next((lo for lo, hi in self.runs if lo <= addr < hi), None)
        if lo is None:
            return
        base = lo + (addr - lo) // (4 * FRAME_LEN) * 4 * FRAME_LEN
        self.writes += 1
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        if not E.PAYLOAD_DST <= pc < RAM:
            self.foreign.append((pc, addr))
        if addr == base or base != self.last:
            self.last = base
            if base in frame_pointers(uc):
                self.hits.append((pc, base))


def notes(blocks, seed, end_low=0):
    """Per block: the trigs and the knobs, the same for every OS: notes now and then (high ones on tracks 5 and 6, so
    that sub-voices switch off), SWEEP creeping, jumping, negative, fast, still and anywhere, the chord shape at each
    note, track 3 to TONE and back; in the last end_low blocks, every track takes a low note and keeps it."""
    rng = random.Random(seed)
    sweep, out = [24, 40, 64, 0, 100, 10], []
    for b in range(blocks):
        ev = {"trig": 0, "set": [], "pat": []}
        for t in range(6):
            if b < blocks - end_low and (b == 1 + 3 * t or (b > 8 and rng.random() < 0.06)):
                ev["trig"] |= 1 << t
                high = t >= 4 and rng.random() < 0.8
                ev["set"].append((t, {"note": rng.randrange(96, 121) if high else rng.randrange(36, 73),
                                      "shape": rng.randrange(128)}))
            if end_low and b == blocks - end_low:
                ev["trig"] |= 1 << t
                ev["set"].append((t, {"note": 48 + t, "shape": 3}))
        sweep[0] = (sweep[0] + 3) % 128
        if b % 5 == 0:
            sweep[1] = rng.randrange(128)
        if b % 7 == 0:
            sweep[2] = rng.randrange(-40, 128)
        sweep[3] = (sweep[3] + 17) % 128
        sweep[5] = rng.randrange(-8, 128)
        ev["set"] += [(t, {"sweep": sweep[t]}) for t in range(6)]
        if b == 60:
            ev["set"].append((2, {"machine": 4}))
        if b == 70:
            ev["set"].append((2, {"machine": CHORD}))
        out.append(ev)
    return out


class World:
    """What the patterns and the slots say, as both OSes are told: which list a CHORD track should play now."""

    def __init__(self):
        self.linked, self.playing, self.values, self.slots = True, 0, {0: (0, False)}, {}

    def wanted(self):
        if not self.linked or self.playing not in self.values:
            return None
        v, bad = self.values[self.playing]
        if bad or v >= 128 or not v >> 1:
            return None
        return self.slots.get((v >> 1) - 1)


def play(v, plan, tables, world, stock=False, move_at=None, watch=None, away=None):
    """Runs the plan: per block the patterns' events (("play", n), ("value", n, v, bad), ("unlink",), ("link",),
    ("slot", s, b or None)), then the knobs and the trigs. The stock OS gets its pointer table switched whenever the
    list wanted changes; a build gets the patterns and the slots, and the move at move_at (0: before block 0)."""
    out, pointed = [], "init"
    for b, ev in enumerate(plan):
        if move_at == b and not stock:
            v.move()
        for e in ev["pat"]:
            if e[0] == "play":
                world.playing = e[1]
                v.pat.link(playing=e[1])
            elif e[0] == "value":
                world.values[e[1]] = (e[2], e[3])
                v.value(e[1], e[2], e[3])
            elif e[0] == "unlink":
                world.linked = False
                v.pat.link(root=False, active=False, playing=world.playing)
            elif e[0] == "link":
                world.linked = True
                v.pat.link(playing=world.playing)
            elif e[0] == "slot":
                s, bb = e[1], e[2]
                if bb is None:
                    world.slots.pop(s, None)
                    if not stock:
                        v.unslot(s)
                else:
                    world.slots[s] = v.table(None if stock else s, bb, tables[bb])
        if stock:
            want = world.wanted() if move_at is None or b >= move_at else None
            key = None if want is None else tuple(want)
            if key != pointed:
                v.point(want)
                pointed = key
        for t, kw in ev["set"]:
            v.e.set(t, **kw)
        out.append(v.e.block(ev["trig"]))
        if away is not None:
            away.append(v.r32(v.syms["ct_away"]))
    return np.array(out)


def tables_of(ref):
    """Eight tables for the buffers 0..7: the stock frames turned around and shifted, each frame 257 longs."""
    entries = [ref.r32(CHORD_TABLE + 4 * i) for i in range(31)]
    stock = [ref.frame(SINE)] + [ref.frame(a) for a in entries]
    out = [stock[::-1]] + [stock[i:] + stock[:i] for i in (5, 11, 17, 23, 3, 9, 27)]
    return {b: out[b] for b in range(8)}


P_BLOCKS, END_LOW = 150, 30


def stock_tests(key, stock, tweak, img, runtime, syms):
    """P1: the stock table in every guise, against the stock OS."""
    slots = stock_slots(img)
    ref = Voice(stock)
    tables = tables_of(ref)
    plan = notes(P_BLOCKS, 66, END_LOW)
    plan[0]["pat"] = [("slot", 1, 1), ("value", 1, 4, False), ("value", 2, 10, False), ("value", 3, 4, True)]
    plan[20]["pat"] = [("unlink",)]
    plan[35]["pat"] = [("link",), ("play", 2)]     # table 5: an empty slot
    plan[55]["pat"] = [("play", 3)]                # table 2, loaded, its check byte wrong
    plan[75]["pat"] = [("value", 3, 200, False)]   # past 127, its check right
    plan[95]["pat"] = [("play", 0)]                # the stock table, 0
    x = play(ref, plan, tables, World(), stock=True)
    v = Voice(img, runtime, tweak, syms)
    w = Watch(v, slots)
    y = play(v, plan, tables, World(), move_at=0, watch=w)
    chord_blocks = v.setups
    check(np.array_equal(x, y) and np.max(np.abs(x)) > 1e6 and not v.e.unmapped and not ref.e.unmapped,
          f"{key}: P1 the patterns unlinked, a pattern choosing an empty slot, one with a wrong check byte, one past "
          f"127, one at 0: identical to the stock OS on six CHORD tracks, sample for sample, over {P_BLOCKS} blocks")
    check(w.writes == 0 and v.r32(syms["ct_copies"]) == 0 and v.r32(syms["ct_away"]) == 0
          and chord_blocks == ref.setups,
          f"{key}: P1 the stock frames in SRAM never written, nothing copied, the stock function called as often as on "
          f"the stock OS ({chord_blocks} calls)")


def table_tests(key, stock, tweak, img, runtime, syms):
    """P2 and P3: a pattern's table, against the stock OS switched in the same blocks."""
    slots = stock_slots(img)
    ref = Voice(stock)
    tables = tables_of(ref)
    plan = notes(P_BLOCKS, 67, END_LOW)
    plan[0]["pat"] = [("slot", 0, 0), ("slot", 1, 1), ("value", 1, 2, False), ("value", 2, 4, False),
                      ("value", 3, 10, False)]
    plan[10]["pat"] = [("play", 1)]                # to table 1
    plan[12]["pat"] = [("play", 2)]                # a change during a change: table 2
    plan[30]["pat"] = [("play", 0)]                # back to the stock table
    plan[32]["pat"] = [("play", 2)]                # table 2 again, some of its frames still at home
    plan[45]["pat"] = [("value", 2, 3, False)]     # the playing pattern edited from 4 to 3: table 1
    plan[55]["pat"] = [("play", 3)]                # table 5: an empty slot, the stock table
    plan[65]["pat"] = [("value", 3, 10, True)]     # a wrong check byte
    plan[70]["pat"] = [("play", 1)]                # table 1
    plan[80]["pat"] = [("slot", 0, 2)]             # the loader's new buffer for table 1 (another file)
    plan[95]["pat"] = [("unlink",)]                # no patterns: the stock table
    plan[100]["pat"] = [("link",)]                 # table 1 again
    plan[P_BLOCKS - END_LOW]["pat"] = [("play", 0)]    # the stock table to the end
    x = play(ref, plan, tables, World(), stock=True)
    v = Voice(img, runtime, tweak, syms)
    stock_frames = {a: v.frame(a) for a in slots}
    w = Watch(v, slots)
    away = []
    y = play(v, plan, tables, World(), move_at=0, watch=w, away=away)
    same = np.array_equal(x, y)
    first = next((b for b in range(P_BLOCKS) if not np.array_equal(x[b], y[b])), None)
    check(same and np.max(np.abs(x)) > 1e6 and not v.e.unmapped and not ref.e.unmapped,
          f"{key}: P2 tables 1 and 2, a change during a change, back to the stock table, a table coming back, the value "
          "edited while it plays, an empty slot, a wrong check byte, the loader's new buffer, the patterns unlinked: "
          f"identical to the stock OS switched in the same blocks, six CHORD tracks, sample for sample, over {P_BLOCKS} "
          "blocks" + ("" if same else f" (first difference in block {first})"))
    check(not w.hits and not w.foreign,
          f"{key}: P3 no slot written while a sub-voice points at it ({len(w.hits)}), nothing but the package writes "
          f"the slots ({len(w.foreign)})")
    changes = [b for b in range(1, P_BLOCKS) if away[b] and not away[b - 1]]
    spans = []
    for b in changes:
        e_ = next((k for k in range(b, P_BLOCKS) if not away[k]), None)
        spans.append((b, None if e_ is None else e_ - b + 1))
    copies = v.r32(syms["ct_copies"])
    finding(f"{key}: P3 {len(changes)} changes with frames to bring home, blocks until home (six CHORD tracks, high "
            f"notes switching sub-voices off): {spans}; {copies} frames copied ({w.writes // FRAME_LEN} seen written)")
    back = all(v.frame(a) == stock_frames[a] for a in slots)
    before = v.setups
    v.e.block(0)
    check(away[-1] == 0 and back and v.setups > before and v.r32(syms["ct_want"]) == STOCK,
          f"{key}: P3 at the end, back at the stock table: every position home, each slot holding its stock frame "
          "again, the stock function called")
    # the move late: a table chosen from block 0, the move in block 30
    plan2 = notes(60, 68)
    plan2[0]["pat"] = [("slot", 0, 0), ("value", 1, 2, False), ("play", 1)]
    ref2 = Voice(stock)
    x2 = play(ref2, plan2, tables, World(), stock=True, move_at=30)
    v2 = Voice(img, runtime, tweak, syms)
    y2 = play(v2, plan2, tables, World(), move_at=30)
    check(np.array_equal(x2, y2) and np.array_equal(x2[:30], play(Voice(stock), plan2, tables, World(), stock=True,
                                                                     move_at=10_000)[:30]),
          f"{key}: P2 a table chosen before the move: the stock table until the first tick's move (block 30), then the "
          "table, as the stock OS switched in block 30")


# --- P4. the pattern: the header's loader, initializer, save and load ---------------------------------------------------
def rec(v, bad=False):
    return bytes([v & 0xff, (0x5a + v + (1 if bad else 0)) & 0xff])


def storage_tests(key, stock, img, runtime, fx):
    s, p = t7.UI(stock), t7.UI(img, runtime)
    for u in (s, p):
        u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    H1, H2, H3 = 0x92000000, 0x92001000, 0x92002000
    B1, B2, SER = 0x92010000, 0x92020000, 0x92030000
    unprotected = []
    F.watch(p.uc, [(h + HDR, h + HDR + 2) for h in (H1, H2, H3, B2 + F.HDR_AT)], unprotected)
    ours, theirs = slice(HDR, HDR + 2), slice(F.HDR, F.HDR + 3)

    def rd(u, va, n=64):
        return bytes(u.uc.mem_read(va, n))

    def header(u, at, mine, fxr=None):           # a header as the OS initializes it, then bytes 36, 37 (and 29 to 31)
        u.uc.mem_write(at, bytes(64))
        u.call(F.HDR_INIT, at, 0)
        u.uc.mem_write(at + HDR, mine)
        if fxr is not None:
            u.uc.mem_write(at + F.HDR, fxr)

    def outside(raw):
        raw = bytearray(raw)
        raw[ours] = b"\0\0"
        if fx:
            raw[theirs] = b"\0\0\0"
        return bytes(raw)
    header(s, H1, rec(12))
    s.uc.mem_write(H2, b"\xa5" * 64)
    d0 = s.call(F.HDR_LOAD, H2, H1)
    s.uc.mem_write(H3, b"\xa5" * 64)
    s.call(F.HDR_INIT, H3, 0)
    kept = rd(s, H2)[ours] == rd(s, H3)[ours] == b"\xa5" * 2
    s.call(F.HDR_COPY, H3, H1)
    check(d0 & 0xff == 1 and kept and rd(s, H3) == rd(s, H1),
          f"{key}: P4 the stock OS: its loader and its initializer leave bytes 36 and 37 as the buffer held them, its "
          "header copy keeps the 64 bytes")
    ok = True
    cases = [("a table", rec(12)), ("127", rec(127)), ("past 127", rec(200)), ("a wrong check byte", rec(12, True)),
             ("zeros", bytes(2)), ("0xff", b"\xff\xff")]
    for _name, r in cases:
        fxr = F.hdr(254, 255) if fx else None
        for u in (s, p):
            header(u, H1, r, fxr)
            u.uc.mem_write(H2, b"\xa5" * 64)
        ds, dp = s.call(F.HDR_LOAD, H2, H1), p.call(F.HDR_LOAD, H2, H1)
        rs, rp = rd(s, H2), rd(p, H2)
        good = r[0] < 128 and r[1] == (0x5a + r[0]) & 0xff
        ok &= ds & 0xff == dp & 0xff == 1 and outside(rp) == outside(rs) and rp[ours] == (r if good else rec(0))
        if fx:
            ok &= rp[theirs] == F.hdr(254, 255)
    check(ok, f"{key}: P4 the loader with ct_load{' and fx_load behind it' if fx else ''}: "
          f"{', '.join(n for n, _r in cases)}: the header as the stock OS loads it, bytes 36 and 37 copied when their "
          "check holds, 0 and 0x5a otherwise" + (", the effect slots' bytes 29 to 31 copied too" if fx else "")
          + ", its return 1")
    for u in (s, p):
        u.uc.mem_write(H3, b"\xa5" * 64)
        u.call(F.HDR_INIT, H3, 0)
    new_ok = outside(rd(p, H3)) == outside(rd(s, H3)) and rd(p, H3)[ours] == rec(0)
    if fx:
        new_ok &= rd(p, H3)[theirs] == F.hdr()
    header(p, H3, rec(12), F.hdr(254, 255) if fx else None)
    before = rd(p, H3)
    p.call(F.HDR_INIT, H3, 1)
    check(new_ok and rd(p, H3) == before,
          f"{key}: P4 the initializer with ct_init{' and fx_init' if fx else ''}: a new header as the stock OS's plus "
          "0 and 0x5a" + (" and the stock effects" if fx else "") + "; with keep, the header untouched")
    p.uc.mem_write(B1, bytes(F.PAT_LEN))
    p.call(F.PAT_INIT, B1, 0)
    p.uc.mem_write(B1 + F.HDR_AT + HDR, rec(9))
    p.uc.mem_write(SER, bytes(F.SER_LEN))
    saved = p.call(F.PAT_SAVE, SER, B1, 0) & 0xff == 1 and rd(p, SER + F.SER_HDR_AT) == rd(p, B1 + F.HDR_AT)
    serial = rd(p, SER, F.SER_LEN)
    for u in (s, p):
        u.uc.mem_write(SER, serial)
        u.uc.mem_write(B2, b"\xa5" * F.PAT_LEN)
    ls, lp = s.call(F.PAT_LOAD, B2, SER, 73), p.call(F.PAT_LOAD, B2, SER, 73)
    bs, bp = rd(s, B2, F.PAT_LEN), rd(p, B2, F.PAT_LEN)
    at = F.HDR_AT + HDR
    mask = lambda raw: raw[:at] + raw[at + 2:] if not fx else (raw[:F.HDR_AT + F.HDR] + raw[F.HDR_AT + F.HDR + 3:at]
                                                              + raw[at + 2:])
    loaded = (ls & 0xff == lp & 0xff == 1 and bp[at:at + 2] == rec(9) and mask(bp) == mask(bs)
              and struct.unpack_from(">I", bp, F.NUM_AT)[0] == 73)
    p.uc.mem_write(B1, bytes(F.PAT_LEN))
    p.call(F.MEMCPY, B1, B2, F.PAT_LEN)
    copied = rd(p, B1, F.PAT_LEN) == bp
    check(saved and loaded and copied, f"{key}: P4 a whole pattern at 9 (table 4): saved (0x4005ba0a) with its header, "
          "loaded (0x4005b894) as the stock OS loads it plus bytes 36 and 37, its number 73, copied (0x4008f1f0) whole")
    for bad in (b"\x12\x34", bytes(2)):
        p.uc.mem_write(SER, serial)
        p.uc.mem_write(SER + F.SER_HDR_AT + HDR, bad)
        p.uc.mem_write(B2, b"\xa5" * F.PAT_LEN)
        p.call(F.PAT_LOAD, B2, SER, 73)
        loaded &= rd(p, B2 + at, 2) == rec(0)
    check(loaded, f"{key}: P4 a file whose bytes 36 and 37 choose nothing (12 34, zeros, as the stock OS saved them): "
          "loaded at the stock table")
    check(not unprotected and p.uc.reg_read(mk.UC_M68K_REG_SR) & 0x700 == 0,
          f"{key}: P4 every write of bytes 36 and 37 with the interrupts masked, the level back after"
          + (f"; {[(hex(pc), hex(a)) for pc, a in unprotected[:3]]}" if unprotected else ""))


# --- P5. the gesture ----------------------------------------------------------------------------------------------------
class Gesture:
    """ct_keys and ct_knob as the encoder handler calls them, the held keys in the OS's key bitmap, the patterns as the
    OS links them, the shown one chosen by the bench (0x4006a96c), the header's notify counted (0x400d0f6c)
    (test_fxslot.py's Gesture, for this package)."""

    def __init__(self, img, runtime, syms):
        self.u = t7.UI(img, runtime)
        self.u.uc.mem_map(0xfc070000, 0x1000)
        self.u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        self.u.hooks = {F.SHOWN_OK: ("shown", 1), F.NOTIFY: ("notify", 0)}
        self.show(0)
        self.syms = syms
        self.pat = F.Patterns(lambda va, data: self.u.uc.mem_write(va, data), F.GFIX)
        self.pat.link()
        self.unprotected = []
        F.watch(self.u.uc, [(h + HDR, h + HDR + 2) for h in self.pat.headers.values()], self.unprotected)
        self.exits = 0
        self.behind = {}
        for name in ("fx_keys", "fl_keys"):
            if name in syms:
                self.behind[name] = 0

                def hk(uc, addr, size, ud, name=name):
                    self.behind[name] += 1
                self.u.uc.hook_add(UC_HOOK_CODE, hk, begin=syms[name], end=syms[name])

        def end(uc, addr, size, ud):
            self.exits += 1
        self.u.uc.hook_add(UC_HOOK_CODE, end, begin=F.HANDLER_END, end=F.HANDLER_END)

    def show(self, n):
        self.u.hooks[F.SHOWN_IDX] = ("selected", n)

    def read(self, va, n):
        return bytes(self.u.uc.mem_read(va, n))

    def hold(self, keys):
        for name, code in dict(F.KEY_CODE, RETRIG=4).items():
            idx = struct.unpack(">i", self.read(F.KEY_INDEX + 4 * code, 4))[0]
            at, bit = F.KEY_BITMAP + (idx >> 3), 1 << (idx & 7)
            b = self.read(at, 1)[0]
            self.u.uc.mem_write(at, bytes([b | bit if name in keys else b & ~bit & 0xff]))

    def header(self, n):
        return self.read(self.pat.headers[n] + HDR, 2)

    def count(self, name):
        return sum(1 for n, _a in self.u.calls if n == name)

    def keys(self, desc, step, keys=("PATTERN",)):
        """(taken, registers as expected): a knob turn as the handler meets 0x4001f886, with these keys held."""
        uc, u = self.u.uc, self.u
        self.hold(keys)
        fp, old_fp = 0x93000100, 0x93000400
        saved = [0x6b6b0000 + i for i in range(len(F.FRAME))]
        uc.mem_write(fp - 84, struct.pack(">10I", *saved))
        uc.mem_write(fp + F.STEP_AT, struct.pack(">h", step))
        uc.mem_write(fp, struct.pack(">II", old_fp, t7.STOP))
        sp = t7.STACK - 0x400
        uc.mem_write(sp, struct.pack(">II", t7.STOP, 0x5a5a5a5a))
        uc.reg_write(mk.UC_M68K_REG_A7, sp)
        uc.reg_write(mk.UC_M68K_REG_A6, fp)
        live = [0x3c3c0000 + i for i in range(len(F.FRAME))]
        live[F.FRAME.index(mk.UC_M68K_REG_D3)] = desc
        for r, val in zip(F.FRAME, live):
            uc.reg_write(r, val)
        before = self.exits
        u.calls.clear()
        u.bad.clear()
        uc.emu_start(self.syms["ct_keys"], t7.STOP, count=200_000)
        taken = self.exits > before
        regs = [uc.reg_read(r) for r in F.FRAME]
        a6, a7 = uc.reg_read(mk.UC_M68K_REG_A6), uc.reg_read(mk.UC_M68K_REG_A7)
        if taken:                                # the handler's end: its registers from its frame
            ok = regs == saved and a6 == old_fp and a7 == fp + 8
        else:
            ok = regs == live and a6 == fp and a7 == sp and struct.unpack(">I", self.read(sp, 4))[0] == 2
        ok &= uc.reg_read(mk.UC_M68K_REG_SR) & 0x700 == 0
        return taken, ok and not u.bad


def gesture_tests(key, img, runtime, syms, desc_used):
    g = Gesture(img, runtime, syms)
    u = g.u
    behind = chains_of(lambda va, n: g.read(va, n), syms)["knob"]
    # ct_knob, the lookup behind it intercepted
    results = []
    for keys, answer in ((("PATTERN",), SWEEP_DESC), ((), SWEEP_DESC), (("PATTERN",), 48), (("PATTERN",), 74)):
        g.hold(keys)
        u.hooks[behind] = ("behind", answer)
        u.calls.clear()
        d = u.call(syms["ct_knob"], S.VIEW, 6, 0, 0xffffffff)
        asked = [a[:4] for n, a in u.calls if n == "behind"]
        results.append((d, asked == [(S.VIEW, 6, 0, 0xffffffff)]))
    check(results[0] == (TABLE_DESC, True) and results[1] == (SWEEP_DESC, True) and results[2] == (48, True)
          and results[3] == (74, True),
          f"{key}: P5 ct_knob asks the lookup behind it ({behind:#x}) with the handler's arguments: PATTERN + SWEEP on "
          "CHORD (73) gives descriptor 10; 73 without PATTERN, KICK's SWEEP (48) and CHORD's CONTOUR (74) with PATTERN "
          "stay the lookup's answer")
    o = 0x40a71754 + 100 * TABLE_DESC
    rows_ok = True
    for table in sorted({DESC, desc_used}):
        row = struct.unpack(">14I", g.read(table + DSTRIDE * TABLE_DESC, 56))
        names = (bytes(u.uc.mem_read(row[11], 12)).split(b"\0")[0], bytes(u.uc.mem_read(row[13], 8)).split(b"\0")[0])
        rows_ok &= (row[0] == 0xffffffff and row[1:9] == (0, 0, 0x7f00, 0, 0, 0xffffffff, 0xffffffff, 0)
                    and names == (b"Wavetable", b"WAVE"))
    obj_ok = (u.u32(o + 0x20) == syms["ct_fmt"] and u.u32(o + 0x2c) == 0
              and u.u32(o + 0x10) == u.u32(0x40a71754 + 100 * SWEEP_DESC + 0x10))
    check(rows_ok and obj_ok,
          f"{key}: P5 descriptor 10's rows in the stock table and the one the OS uses ({desc_used:#x}): group -1, k 0, "
          "0..0x7f00, no CC or NRPN, Wavetable / WAVE; its interface object: ct_fmt, no picture, Chord Sweep's steps")
    # ct_keys, as the handler calls it
    g.u.uc.mem_write(g.pat.headers[0] + HDR, rec(0))
    # the handler's step is 8.8, as the interface object gives it (0x4006f96a, notes/70 §2): 0x100 a detent, more
    # for a fast turn, less with FUNC (the device showed the first build adding it whole: notes/66 §33.3)
    turns = (0x100, 0x100, 0x100, -0x500, 0x300, 0x40, 0x4000, 0x4000, 0x100, -0x7f00)
    steps, ok, notified = [], True, 0
    for step in turns:
        taken, regs = g.keys(TABLE_DESC, step)
        ok &= taken and regs
        steps.append(g.header(0)[0])
        notified += g.count("notify")
    check(ok and steps == [1, 2, 3, 0, 3, 4, 68, 127, 127, 0] and g.header(0) == rec(0) and notified == len(turns),
          f"{key}: P5 ct_keys on descriptor 10 with PATTERN: the handler's end, its registers from its frame; the shown "
          f"pattern's value {steps} for the handler's steps (8.8) of a detent three times, -5 detents, a fast turn of "
          f"3, a fine step (0x40: one), 64 twice, a detent, -127 (0 to 127); its check byte, the header's notify at "
          f"each step ({notified})")
    g.u.uc.mem_write(g.pat.headers[0] + HDR, rec(7))
    out = []
    for n in (7, 0, 127, 20):
        g.u.uc.mem_write(g.pat.headers[0] + HDR, rec(n))
        u.call(syms["ct_fmt"], 0, 0, 0x93500000)
        out.append(bytes(u.uc.mem_read(0x93500000, 4)).split(b"\0")[0].decode())
    g.u.uc.mem_write(g.pat.headers[0] + HDR, rec(12, True))
    u.call(syms["ct_fmt"], 0, 0, 0x93500000)
    out.append(bytes(u.uc.mem_read(0x93500000, 4)).split(b"\0")[0].decode())
    check(out == ["3", "0", "63", "10", "0"],
          f"{key}: P5 ct_fmt prints the shown pattern's table: values 7, 0, 127, 20 and a wrong check byte -> {out}")
    g.show(1)
    g.u.uc.mem_write(g.pat.headers[1] + HDR, rec(5))
    taken, regs = g.keys(TABLE_DESC, 0x200)
    check(taken and regs and g.header(1) == rec(7) and g.header(0)[0] == 12,
          f"{key}: P5 the shown pattern is the one edited: pattern 1 from 5 to 7, pattern 0 untouched")
    others = []
    for desc, keys in ((SWEEP_DESC, ()), (37, ("PATTERN",)), (5, ("RETRIG",)), (SWEEP_DESC, ("TRACK",))):
        before = dict(g.behind)
        h = g.header(1)
        taken, regs = g.keys(desc, 1, keys)
        reached = [n for n in g.behind if g.behind[n] > before[n]]
        others.append((desc, keys, taken, regs, reached, g.header(1) == h))
    want_behind = "fl_keys" if "fl_keys" in syms else "fx_keys" if "fx_keys" in syms else None
    good = all(same and regs and (want_behind in reached if want_behind else not reached)
               for _d, _k, _taken, regs, reached, same in others)
    check(good and not g.unprotected,
          f"{key}: P5 any other turn (SWEEP alone, PATTERN + Delay Time, RETRIG + PITCH's descriptor 5, TRACK + SWEEP) "
          f"leaves bytes 36 and 37 and goes to {want_behind or 'isKeyHeld(2), as the handler asked'}; every write masked")


# --- L. the loader --------------------------------------------------------------------------------------------------------
def sample_file(samples, stereo=False):
    """A sample file as the Model:Samples and the uploader write it (One-Shot §7)."""
    n = len(samples) // (2 if stereo else 1)
    head = bytearray(64)
    head[1] = 1 if stereo else 0
    struct.pack_into(">III", head, 4, 2 * len(samples), 48000, 0)
    struct.pack_into(">I", head, 16, n - 1)
    head[20] = 0x7f
    return bytes(head) + struct.pack(f">{len(samples)}h", *samples) + bytes(16)


def frames_of(k, seed):
    rng = np.random.default_rng(seed)
    x = rng.integers(-32768, 32768, k * 256)
    x[0], x[1] = -32768, 32767
    return [int(v) for v in x]


def os_sine16(img):
    """The OS's sine (0x8000eee4, the image's 0x401a9934) as 16 bits, rounded, its peak kept at 32 767 (notes/66 §28.5)."""
    words = struct.unpack_from(">256i", img, 0x401a2a50 + (SINE - 0x80008000) - E.BASE)
    return [min(32767, (w >> 16) + ((w >> 15) & 1)) for w in words]


def expected(samples, k, sine):
    """The 32 frames the loader must build: the OS's sine in front when the first frame is not one (within 4 steps),
    the spread with C's integer division, Q31, the 257th sample."""
    front = any(abs(samples[m] - sine[m]) > 4 for m in range(256))
    src = (sine + samples) if front else samples
    n = k + (1 if front else 0)
    out = []
    for s in range(FRAMES):
        pos = s * (n - 1)
        i0, rem = pos // (FRAMES - 1), pos % (FRAMES - 1)
        a = src[i0 * 256:(i0 + 1) * 256]
        b = src[(i0 + 1) * 256:(i0 + 2) * 256] if rem else a
        f = []
        for j in range(256):
            d = (b[j] - a[j]) * rem
            q = abs(d) // (FRAMES - 1)
            f.append(((a[j] + (q if d >= 0 else -q)) << 16) & 0xffffffff)
        out.append(be32s(f + [f[0]]))
    return out, front


DIR_OPEN, DIR_NEXT, DIR_HIDDEN = 0x4007aa78, 0x4007ab26, 0x4007ecc2   # the OS's folder calls (notes/66 §36.1)
DE_BYTES, FOLDER = 276, "/Wavetables"
PAYLOAD = 0x43000000


class Drive:
    """The +Drive as the loader sees it since 0.4 (notes/66 §36): folders and files by path in the order they were
    made, their inodes and ids, the index in memory; the OS's folder calls (open, next entry, hidden) and the two
    file calls answered here, each one noted. A folder lists ".", ".." and then what is in it. A rename keeps the
    inode, the id and the place in the folder, and leaves the index as it was (an id is the content's hash)."""

    def __init__(self, u):
        self.u, self.files, self.dirs, self.order = u, {}, {"/": 1}, []
        self.hidden, self.calls, self.next_ino = set(), [], 100
        u.uc.mem_map(RAM, RAM_END - RAM)
        for va, fn in ((OPEN, self._open), (CLOSE, self._close), (ENTRY, self._entry), (READ, self._read),
                       (DIR_OPEN, self._opendir), (DIR_NEXT, self._readdir), (DIR_HIDDEN, self._hidden)):
            u.uc.hook_add(UC_HOOK_CODE, self._wrap(fn), begin=va, end=va)
        self.mkdir(FOLDER)
        self.mount(True)
        self.w32(FS_LOCK, 0)
        self.w32(RUNNING, TASK)

    def w32(self, a, v):
        self.u.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def mount(self, on):
        self.w32(MOUNTED, 1 if on else 0)

    def mkdir(self, path):
        self.dirs[path] = self.next_ino
        self.next_ino += 1
        self.order.append(path)

    def put(self, path, data):
        self.files[path] = (self.next_ino, (hash(data) & 0x7ffffffe) | 1, data)
        self.next_ino += 1
        self.order.append(path)
        self.index()

    def drop(self, path):
        del self.files[path]
        self.order.remove(path)
        self.index()

    def rmdir(self, path):
        for p in [p for p in self.order if p == path or p.startswith(path + "/")]:
            self.order.remove(p)
            self.files.pop(p, None)
            self.dirs.pop(p, None)
        self.index()

    def rename(self, old, new):
        self.files[new] = self.files.pop(old)
        self.order[self.order.index(old)] = new

    def hide(self, path):
        self.hidden.add(self.files[path][0])

    def index(self):
        pairs = sorted((idn, ino) for ino, idn, _d in self.files.values())
        self.w32(INDEX_COUNT, len(pairs))
        self.u.uc.mem_write(INDEX, b"".join(struct.pack(">II", a, b) for a, b in pairs))

    def _wrap(self, fn):
        def hook(uc, addr, size, ud):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">4I", uc.mem_read(sp + 4, 16))
            r = fn(*args)
            uc.reg_write(mk.UC_M68K_REG_D0, r & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        return hook

    def cstr(self, a):
        return bytes(self.u.uc.mem_read(a, 256)).split(b"\0")[0].decode("latin-1")

    def by_ino(self, ino):
        return next(((n, f) for n, f in self.files.items() if f[0] == ino), (None, None))

    def children(self, folder):
        """(name, inode, type) of a folder's entries, as the OS lists them: ".", "..", then by the order they came."""
        up = folder.rsplit("/", 1)[0] or "/"
        out = [(".", self.dirs[folder], 1), ("..", self.dirs.get(up, 1), 1)]
        for p in self.order:
            if p.rsplit("/", 1)[0] == folder:
                out.append((p.rsplit("/", 1)[1], self.dirs[p] if p in self.dirs else self.files[p][0],
                            1 if p in self.dirs else 2))
        return out

    def _open(self, path, mode, h, _x):
        self.calls.append(("open", self.cstr(path)))          # 0.3's call: 0.4 never makes it
        return -1

    def _close(self, h, *_x):
        self.calls.append(("close",))
        return 0

    def _opendir(self, path, h, *_x):
        p = self.cstr(path)
        self.calls.append(("opendir", p))
        if p not in self.dirs:
            return -1
        self.u.uc.mem_write(h, struct.pack(">4I", self.dirs[p], 0, 0, 0))
        return 0

    def _readdir(self, h, d, *_x):
        ino, _b, _o, i = struct.unpack(">4I", self.u.uc.mem_read(h, 16))
        folder = next(p for p, n in self.dirs.items() if n == ino)
        kids = self.children(folder)
        self.calls.append(("readdir", i))
        if i >= len(kids):
            return 0
        name, e_ino, typ = kids[i]
        raw = struct.pack(">IH2xIII", e_ino, typ, ino, 0, i) + name.encode("latin-1")[:255] + b"\0"
        self.u.uc.mem_write(d, raw + bytes(DE_BYTES - len(raw)))
        self.u.uc.mem_write(h + 12, struct.pack(">I", i + 1))
        return 1

    def _hidden(self, ino, *_x):
        self.calls.append(("hidden", ino))
        return 1 if ino in self.hidden else 0

    def _entry(self, ino, out, *_x):
        name, f = self.by_ino(ino)
        self.calls.append(("entry", name))
        if not f:
            return -1
        self.u.uc.mem_write(out, struct.pack(">4I", ino, f[1], len(f[2]), 0))
        return 0

    def _read(self, b, n, fh, _x):
        ino, pos = struct.unpack(">II", self.u.uc.mem_read(fh, 8))
        name, f = self.by_ino(ino)
        self.calls.append(("read", name, pos, n))
        if not f:
            return -1
        data = f[2][pos:pos + n]
        self.u.uc.mem_write(b, data)
        return len(data)


class Loader:
    """The UI side with the drive: the tick, and what a proof reads of the loader's state."""

    def __init__(self, img, runtime, syms):
        self.u = u = S.UI(img, runtime)
        u.uc.mem_map(SRAM_LO, 0x20000)           # the internal SRAM as the bootstrap leaves it: the move reads it
        u.uc.mem_write(SRAM_LO, img[0x4019b590 - E.BASE:0x401a2a50 - E.BASE])
        u.uc.mem_write(0x80008000, img[0x401a2a50 - E.BASE:0x401aa140 - E.BASE])
        self.d = Drive(u)
        u.hooks = {GETTER: ("getter", 0x5a)}
        for s in ("sample_hook_tick", "smp_hook_tick"):   # SAMPLE's own tick, with the dispatcher: not this proof's
            if s in syms:
                u.hooks[syms[s]] = (s, 0x5a)
        self.syms, self.tick_va, self.insns = syms, syms.get("dp_tick", syms["ct_hook_tick"]), 0
        self.sine = os_sine16(img)

        def count(uc, addr, size, ud):
            self.insns += 1
        u.uc.hook_add(UC_HOOK_CODE, count, begin=PAYLOAD, end=RAM - 1)

    def r32(self, a):
        return struct.unpack(">I", self.u.uc.mem_read(a, 4))[0]

    def var(self, name, i=0):
        return self.r32(self.syms[name] + 4 * i)

    def slot(self, n):
        return self.var("ct_slot", n - 1)

    def owner(self, b):
        return self.u.uc.mem_read(self.syms["ct_owner"] + b, 1)[0]

    def ticks(self, n):
        """n ticks: per tick, the getter's answer, the drive's calls and the instructions run in the payload."""
        out = []
        for _ in range(n):
            self.d.calls.clear()
            self.insns = 0
            r = self.u.call(self.tick_va, S.VIEW) & 0xff
            out.append((r, list(self.d.calls), self.insns))
        return out

    def table_ok(self, n, samples, k, front=None):
        b = self.slot(n)
        if not b:
            return False
        ptrs = struct.unpack(f">{POINTERS}I", self.u.uc.mem_read(b, 4 * POINTERS))
        want = [b + 4 * POINTERS + 4 * FRAME_LEN * s for s in range(FRAMES)]
        frames, put_front = expected(samples, k, self.sine)
        if list(ptrs) != [SINE] + want[1:] + [want[-1]] or (front is not None and put_front != front):
            return False
        return all(bytes(self.u.uc.mem_read(p, 4 * FRAME_LEN)) == f for p, f in zip(want, frames))


def calls(log, kind):
    return [c for _r, cs, _n in log for c in cs if c[0] == kind]


def loader_tests(key, img, runtime, syms):
    L = Loader(img, runtime, syms)
    d, slot, P = L.d, L.slot, (lambda name: f"{FOLDER}/{name}")
    slots = stock_slots(img)
    clip = lambda x: max(-32768, min(32767, x))
    near = [clip(L.sine[m] + (3 if m % 2 else -3)) for m in range(256)] + frames_of(2, 21)
    off = [clip(L.sine[m] + (5 if m == 100 else 0)) for m in range(256)] + frames_of(2, 22)
    saw = [sum(math.sin(h * (2 * math.pi * m / 2048 + 0.5 * j)) / h for h in range(1, 120)) * 0.5
           for j in range(4) for m in range(2048)]
    conv, _rep = W.convert(saw)
    # table: (frames, samples, the file's name); then the names that play nothing
    files = {1: (32, frames_of(32, 11), "01"), 2: (1, frames_of(1, 12), "02 Saw Pad"), 3: (4, frames_of(4, 13), "03-pulse"),
             63: (2, frames_of(2, 14), "63"), 10: (3, near, "10.wav"), 11: (3, off, "11 off"),
             8: (5, conv, "08 Converted"), 12: (2, frames_of(2, 24), "12 Glass")}
    for n, (_k, data, name) in files.items():
        if n == 8:
            d.put(P(name), W.device_bytes(conv))
        elif n == 12:
            d.put(P("12 Pad"), sample_file(frames_of(2, 25)))   # made first, but "12 Glass" comes first in byte order
            d.put(P(name), sample_file(data))
        else:
            d.put(P(name), sample_file(data))
    d.put(P("05 Stereo"), sample_file(frames_of(2, 15), stereo=True))
    d.put(P("06 short"), sample_file(frames_of(2, 16)[:300]))
    d.put(P("07 Big"), sample_file(frames_of(33, 17)))
    for name, seed in (("64 Pad", 23), ("7 Pad", 26), ("070", 27), ("Glass 16", 28)):
        d.put(P(name), sample_file(frames_of(2, seed)))
    d.mkdir(P("13"))                                            # a folder named 13, a file 14 in it
    d.put(P("13/14"), sample_file(frames_of(2, 29)))
    d.put(P("15"), sample_file(frames_of(2, 30)))
    d.hide(P("15"))                                             # an entry the OS leaves out of its listing
    d.put("/17", sample_file(frames_of(2, 31)))                 # outside the folder
    entries = len(d.children(FOLDER))

    # a. the first tick: the move; the listing after the mount, then the pass (2 + 11 ticks; the listing on time comes
    # 64 ticks after this one started, so b and c count from here)
    log = L.ticks(20)
    reads = calls(log, "readdir")
    per_tick = [sum(1 for c in cs if c[0] == "readdir") for _r, cs, _n in log]
    hidden_asked = {c[1] for c in calls(log, "hidden")}
    numbered = {d.files[P(nm)][0] for nm in ("01", "02 Saw Pad", "03-pulse", "63", "10.wav", "11 off", "08 Converted",
                                            "12 Pad", "12 Glass", "05 Stereo", "06 short", "07 Big", "15")}
    entry_names = {c[1] for c in calls(log, "entry")}
    found = {n: L.var("ct_found", n - 1) for n in range(1, 64)}
    check([c[1] for c in calls(log, "opendir")] == [FOLDER] and not calls(log, "open") and not calls(log, "close")
          and [c[1] for c in reads] == list(range(entries + 1)) and per_tick[:2] == [16, entries + 1 - 16]
          and L.var("ct_listing") == 0 and L.var("ct_scan") == 0 and not L.u.bad,
          f"{key}: L the listing: /Wavetables opened once, its {entries} entries read in order, 16 a tick, to the end; "
          "no file opened by its path; the pass ends")
    check(hidden_asked == numbered,
          f"{key}: L the OS asked whether an entry is hidden only for the files whose name has a number (not for "
          "64 Pad, 7 Pad, 070, Glass 16, the folder 13, . and ..)")
    check({n for n, ino in found.items() if ino} == {1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 63}
          and found[12] == d.files[P("12 Glass")][0]
          and entry_names == {P(f) for f in ("01", "02 Saw Pad", "03-pulse", "05 Stereo", "06 short", "07 Big",
                                             "08 Converted", "10.wav", "11 off", "12 Glass", "63")},
          f"{key}: L the names: 01, 02 Saw Pad, 03-pulse, 63, 10.wav, 11 off, 08 Converted found as their numbers; of "
          "12 Pad and 12 Glass, 12 Glass; nothing for 64 Pad, 7 Pad, 070, Glass 16, the folder 13 and the file in it, "
          "the hidden 15, /17 outside the folder; each file found looked at once")
    check({r for r, _c, _n in log} == {0x5a}, f"{key}: L every tick returns the stock getter's answer")
    ptrs = [L.r32(STOCK + 4 * i) for i in range(POINTERS)]
    tags = [L.var("ct_tag", i) for i in range(FRAMES)]
    copies_ok = all(bytes(L.u.uc.mem_read(ptrs[i], 4 * FRAME_LEN)) == bytes(L.u.uc.mem_read(slots[i - 2], 4 * FRAME_LEN))
                    for i in range(2, FRAMES))
    check(L.var("ct_moved") == 1 and ptrs[0] == SINE and ptrs[1] == FRAME1 and ptrs[32] == ptrs[31]
          and all(STOCK + 4 * POINTERS <= p < STOCK + BUF_BYTES for p in ptrs[2:]) and copies_ok
          and tags[2:] == [STOCK] * 30,
          f"{key}: L the first tick made the move: ct_moved 1; STOCK's 33 pointers the selector's (the sine, frame 1 "
          "where the OS has it, the copies of frames 2 to 31 equal to the SRAM frames); every slot's tag STOCK")
    ok = lambda n, front=None: L.table_ok(n, files[n][1], files[n][0], front)
    check(ok(1, True) and ok(2, True) and ok(3, True) and ok(63, True) and ok(8, False) and ok(10, False)
          and ok(11, True) and ok(12),
          f"{key}: L files 01 (32 frames), 02 Saw Pad (1), 03-pulse (4), 63 (2): the OS's sine put in front; 08 "
          "Converted (made by tools/wavetable.py, its first frame a sine) and 10.wav (a sine within 3 steps): taken as "
          "they are; 11 off (one sample 5 steps off): the sine put in front; 12 from 12 Glass; every table built "
          "exactly as computed here")
    check(all(slot(n) == 0 for n in range(1, 64) if n not in files),
          f"{key}: L a stereo file (05), 300 samples (06), 33 frames (07), the folder 13, the hidden 15 and the numbers "
          "without a file: empty slots")

    # b. nothing changed: no call to the drive
    log = L.ticks(10)
    check(not any(cs for _r, cs, _n in log), f"{key}: L nothing changed: no call to the drive in 10 ticks")

    # c. the listing on time, about every 2 s (at the 65th tick since the first listing started): the folder read again,
    # no file looked at again
    before = {n: slot(n) for n in range(1, 64)}
    log = L.ticks(64)
    check(len(calls(log, "opendir")) == 1 and len(calls(log, "readdir")) == entries + 1
          and not calls(log, "entry") and not calls(log, "read") and all(slot(n) == before[n] for n in range(1, 64)),
          f"{key}: L on time (64 ticks after the last listing): the folder listed once more; no file looked at again, "
          "the unplayable ones neither; every slot as it was")

    # d. a rename: the index stays as it was; the listing on time finds it
    index_before = bytes(L.u.uc.mem_read(INDEX_COUNT, 8))
    old2 = slot(2)
    d.rename(P("02 Saw Pad"), P("04 Saw Pad"))
    log = L.ticks(70)
    check(bytes(L.u.uc.mem_read(INDEX_COUNT, 8)) == index_before
          and {c[1] for c in calls(log, "read")} == {P("04 Saw Pad")} and {c[1] for c in calls(log, "entry")} == {P("04 Saw Pad")}
          and slot(2) == 0 and L.table_ok(4, files[2][1], 1) and L.owner((old2 - buf(0)) // BUF_BYTES) == 0,
          f"{key}: L 02 Saw Pad renamed 04 Saw Pad (the index unchanged): at the listing on time, table 4 from it, "
          "table 2 back to the stock one, its buffer free again; only the renamed file read")
    files[4] = (1, files[2][1], "04 Saw Pad")
    del files[2]

    # e. a file added: the index changes; every file's id looked at, only the new one read
    before = {n: slot(n) for n in files}
    data9 = frames_of(3, 18)
    d.put(P("09 New"), sample_file(data9))
    log = L.ticks(64)
    frames_read = {c[1] for c in calls(log, "read") if c[2] == 64}
    check(frames_read == {P("09 New")} and {c[1] for c in calls(log, "entry")} >= {P(f[2]) for f in files.values()}
          and all(slot(n) == before[n] for n in files) and L.table_ok(9, data9, 3),
          f"{key}: L a file added: a new listing; every file's id looked at, the others kept without a read; 09 New "
          "loaded")
    files[9] = (3, data9, "09 New")
    data12 = frames_of(2, 32)
    d.put(P("12 Aa"), sample_file(data12))
    L.ticks(64)
    check(L.table_ok(12, data12, 2) and L.var("ct_found", 11) == d.files[P("12 Aa")][0],
          f"{key}: L 12 Aa added: it comes before 12 Glass in byte order, so table 12 plays it")
    files[12] = (2, data12, "12 Aa")

    # f. a file replaced while its buffer is the table wanted and a voice points into it
    old = slot(1)
    old_b = (old - buf(0)) // BUF_BYTES
    L.u.uc.mem_write(syms["ct_want"], struct.pack(">I", old))
    ptr_at = E.VOICE0 + 2 * E.VSTRIDE + 120 + 176
    L.u.uc.mem_write(ptr_at, struct.pack(">I", old + 4 * POINTERS + 4 * FRAME_LEN * 3))
    tag_at = syms["ct_tag"] + 4 * 7
    L.u.uc.mem_write(tag_at, struct.pack(">I", old))
    data1 = frames_of(2, 19)
    d.drop(P("01"))
    d.put(P("01"), sample_file(data1))
    L.ticks(64)
    replaced = slot(1) not in (0, old) and L.table_ok(1, data1, 2) and L.owner(old_b) == 0xff
    L.u.uc.mem_write(syms["ct_want"], struct.pack(">I", STOCK))
    L.ticks(2)
    held = L.owner(old_b) == 0xff and L.r32(tag_at) == old
    L.u.uc.mem_write(ptr_at, struct.pack(">I", 0))
    L.ticks(1)
    check(replaced and held and L.owner(old_b) == 0 and L.r32(tag_at) == 0,
          f"{key}: L a file replaced: table 1 in a new buffer, built from the new file; the old buffer stays retired while "
          "it is the table wanted, then while a voice points into it; then free at the next tick, the tag of the slot "
          "holding one of its frames cleared")
    L.u.uc.mem_write(tag_at, struct.pack(">I", STOCK))
    files[1] = (2, data1, "01")

    # g. a file deleted
    d.drop(P("03-pulse"))
    L.ticks(64)
    del files[3]
    check(slot(3) == 0 and all(slot(n) for n in files), f"{key}: L a file deleted: table 3 empty, the others kept")

    # h. the drive not mounted, then its lock held by the running task
    d.mount(False)
    log1 = L.ticks(5)
    d.mount(True)
    d.w32(FS_LOCK, TASK)
    log2 = L.ticks(5)
    d.w32(FS_LOCK, 0)
    log3 = L.ticks(2)
    check(not any(cs for _r, cs, _n in log1 + log2) and [sum(1 for c in cs if c[0] == "opendir") for _r, cs, _n in log3] == [1, 0],
          f"{key}: L the drive not mounted, then its lock held by the running task: no call to the drive; free again "
          "after the mount: a new listing")
    L.ticks(64)

    # i. no free buffer: the pass waits on the table
    full = bytes(L.u.uc.mem_read(syms["ct_owner"], BUFFERS))
    L.u.uc.mem_write(syms["ct_owner"], bytes(b if b else 0x40 for b in full))
    data18 = frames_of(1, 20)
    d.put(P("18 Wait"), sample_file(data18))
    L.ticks(40)
    waiting = L.var("ct_scan") == 18 and slot(18) == 0
    L.u.uc.mem_write(syms["ct_owner"], full)
    L.ticks(60)
    check(waiting and L.table_ok(18, data18, 1) and L.var("ct_scan") == 0 and not L.u.bad,
          f"{key}: L no free buffer: the pass waits on table 18; once a buffer is free, 18 Wait is loaded and the pass "
          "ends")

    # j. the folder gone: every table back to the stock one
    d.rmdir(FOLDER)
    log = L.ticks(64)
    check(all(slot(n) == 0 for n in range(1, 64)) and len(calls(log, "opendir")) == 1 and not calls(log, "readdir"),
          f"{key}: L /Wavetables deleted: its opening refused, no entry read; every table back to the stock one")

    # k. 63 files: how long and how much a tick, up to the end of the first pass (the listing on time follows it)
    L = Loader(img, runtime, syms)
    for n in range(1, 64):
        L.d.put(P(f"{n:02d} Table {n}"), sample_file(frames_of(1, 100 + n)))
    log = []
    while len(log) < 80:
        log += L.ticks(1)
        if not L.var("ct_listing") and not L.var("ct_scan"):
            break
    listing = [n for _r, cs, n in log if any(c[0] == "readdir" for c in cs)]
    loading = [n for _r, cs, n in log if any(c[0] == "read" for c in cs)]
    check(all(L.slot(n) for n in range(1, 64)) and len(calls(log, "opendir")) == 1 and len(listing) == 5
          and len(loading) == 63 and len(log) == 68,
          f"{key}: L 63 files 01 Table 1 to 63 Table 63: listed in 5 ticks (65 entries, 16 a tick), then loaded one a "
          f"tick, all 63, the pass ending at tick 68 ({len(log)})")
    finding(f"{key}: L 63 files: at most {max(listing[1:] or [0])} instructions in the package a tick while listing (the "
            f"first tick, with the move, {listing[0] if listing else 0}; the OS's folder calls not counted), at most "
            f"{max(loading or [0])} while loading a table")


# --- C. the cost, by the standard's method (STANDARD.md §6) -----------------------------------------------------------
COST_BLOCKS = 21


def cost_run(img, runtime=None, tweak=None, syms=None, table=None, trig=True, sweep=None, switch_at=None):
    """Instructions per block in the real voice loop, track 1 alone on CHORD (note 60, SWEEP 24 or sweep(b)), trig in
    block 1: [block 0, block 1, ...]. A build: the move first, then pattern 0 playing, at the stock table, or at the
    table from block switch_at (0: before block 0, the change then done before counting)."""
    v = Voice(img, runtime, tweak, syms, tracks=(0,))
    if syms:
        v.move()
        v.value(0, 0)
        if table is not None:
            v.table(0, 0, table)
            v.value(1, 2)
            if switch_at == 0:               # the note makes the voice CHORD's, then the change comes home
                v.pat.link(playing=1)
                for k in range(40):
                    v.e.block(1 if k == 1 else 0)
    v.e.count_instructions()
    counts = []
    for b in range(3 + COST_BLOCKS):
        if switch_at and b == switch_at:
            v.pat.link(playing=1)
        if sweep:
            v.e.set(0, sweep=sweep(b))
        before = v.e.instructions
        v.e.block(1 if trig and b == 1 else 0)
        counts.append(v.e.instructions - before)
    return counts


def cost_tests(key, stock, tweak, img, runtime, syms):
    idle = cost_run(stock, trig=False)
    per_voice = lambda c: [x - y for x, y in zip(c, idle)]
    table = tables_of(Voice(stock))[0]
    built = (img, runtime, tweak, syms)
    out = {}
    for name, args, kw in (("stock CHORD", (stock,), {}), ("0.3 at the stock table", built, {}),
                           ("0.3, a table at home", built, {"table": table, "switch_at": 0}),
                           ("stock CHORD, SWEEP creeping", (stock,), {"sweep": lambda b: (24 + 3 * b) % 128}),
                           ("0.3, a table at home, SWEEP creeping", built,
                            {"table": table, "switch_at": 0, "sweep": lambda b: (24 + 3 * b) % 128})):
        c = per_voice(cost_run(*args, **kw))
        first, rest = c[2], c[3:3 + COST_BLOCKS]
        out[name] = (first, sum(rest) / len(rest), max(rest))
        finding(f"{key}: cost, {name}: first block {first}, then mean {out[name][1]:.0f}, max {out[name][2]} "
                f"instructions per block per voice (over {COST_BLOCKS} blocks)")
    d0 = out["0.3 at the stock table"][1] - out["stock CHORD"][1]
    d1 = out["0.3, a table at home"][1] - out["stock CHORD"][1]
    d2 = out["0.3, a table at home, SWEEP creeping"][1] - out["stock CHORD, SWEEP creeping"][1]
    check(0 <= d0 < 100 and -100 < d1 < 150 and -100 < d2 < 150,
          f"{key}: C 0.3 adds {d0:+.0f} instructions per block per voice at the stock table, {d1:+.0f} with a table at "
          f"home, {d2:+.0f} with a table and SWEEP creeping, against stock CHORD: no copy while a table plays")
    c = per_voice(cost_run(*built, table=table, switch_at=5))
    change = c[5:3 + COST_BLOCKS]
    home = next((k for k in range(len(change)) if change[k] <= out["0.3, a table at home"][2] + 50), None)
    finding(f"{key}: cost of a change, one CHORD track (one frame a block): blocks 5.. after the switch {change[:34]}; "
            f"the first block back at the table's own cost: {home}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--dry", action="store_true", help="the builds, their sites and chains only, without emulation")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    for ids in selections:
        if "chordtables" not in ids:
            sys.exit(f"!! {'+'.join(ids)}: the proof needs chordtables")
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        added = TC.configure([i for i in ids if compose.load_manifest(i)["_machine"]])
        desc_used = compose.gs.DESCN if added else DESC
        fx = any(compose.load_manifest(i)["_effect"] for i in ids)
        print(f"\n{key}: CHORD extended (machine 5)" + "".join(f", {m['name']} = machine {m['index']}" for m in added)
              + f"; payload {len(runtime)} bytes at {compose.gs.PAY_ALONE:#x}, RAM claim {RAM:#x}..{RAM_END:#x}")
        print("0. start-up, the sites, the chains")
        if not args.dry:
            X.bootstrap_depack_ok(args.cycles, tweak, None) or t7.FAIL.append(f"{key}: bootstrap")
            X.boot_hook_ok(img, runtime) or t7.FAIL.append(f"{key}: boot hook")
        syms = site_tests(key, ids, tweak, img, runtime, info)
        if args.dry:
            continue
        if args.machines or key in AUDIO:
            print("P1. the stock table")
            stock_tests(key, stock, tweak, img, runtime, syms)
            print("P2 and P3. a pattern's table, against the stock OS switched in the same blocks")
            table_tests(key, stock, tweak, img, runtime, syms)
        print("P4. the pattern header")
        storage_tests(key, stock, img, runtime, fx)
        print("P5. the gesture, PATTERN's release")
        gesture_tests(key, img, runtime, syms, desc_used)
        F.release_tests(key, stock, img, runtime)
        print("L. the loader")
        loader_tests(key, img, runtime, syms)
        if args.machines or key in AUDIO:
            print("C. the cost (STANDARD.md §6)")
            cost_tests(key, stock, tweak, img, runtime, syms)
    print(("\n(dry run: no emulation) " if args.dry else "\n")
          + ("ALL OK" if not t7.FAIL else f"{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6])))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
