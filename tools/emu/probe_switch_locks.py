#!/usr/bin/env python3
"""Probe P0 of Loop and Reverse as p-locks (a trig held + MACHINES + PUNCH / GATE on SAMPLE's tracks; the plan of
2026-11-05, draft of notes/80): what the stock OS already does with a p-lock of k 32, the word of the switches, on the
OS's own code. Nothing is patched: every part runs the official MAIN OS 1.13.

  0. The sites, in the user's MAIN OS (bytes only, no emulation): the sound parameters' lock methods in their vtable
     (0x400fd15c set 0x4000bb94, 0x400fd160 clear 0x4000bc00), their jumps to 0x4001646a and 0x400164b0; the MACHINES
     case's held-trig test (0x4001c274..0x4001c28a) and its branch to 0x4001c996; the pattern file's tables: k 32
     read past 0x4010ee4c lands on index 9, index 18 of 0x4010eea8 is k 0, no k of 0..22 has index 18.
  1. The stock knob p-lock ends in a k-based setter. 0x4000bb94, (object, descriptor, value, step), the method a held
     trig + a knob reaches (0x4001dcf2 -> vt+40), takes k from the descriptor (0x4005a4e8), the active track's sequence
     object (0x4000cfcc(0x4000f208(project), track)), and jumps to 0x4001646a(seq, step, k, value) -> 0x4000dece. With
     0x4005a4e8 answering k 32: the pattern's word (track 2, step 5, k 32) holds the value, its flag (+4352 + 32) is
     1, the pattern file is told once ({0x400fdb0c, k 32, track 2}), every other word stays -1; 0x4000bc00 (the clear:
     0x400164b0 -> 0x4000dcec) writes -1 back and the flag 0. 0x4001646a refuses k 33, a negative value and a step
     past the pattern's length, and takes the last step.
  2. Held trigs. 0x4006be48 (state, function, 1) walks the 64-bit mask at +348 / +352 of the UI state: steps 0..31 in
     +352, 32..63 in +348. 0x4006b740(state, 1) sets +356; 0x4006b954(state) clears the 64 step words at +92 (get
     0x4006b8fe, set 0x4006b91a) and keeps the mask: what the stock knob path does around its writes (0x4001e96a,
     0x4001e9c8).
  3. Playing, on seqrig (the real event builder 0x400548ce, the audio interrupt, the smoothing): track 2, its sound's
     k 32 = 0x0101; trigs on steps 0, 1 and 2, step 1 locked to k 32 = 0x0e00 and k 31 = 0x1234. The copy the
     voices are fed from (0x800015ae + 66 t + 2 k) goes 0x0101 -> 0x0e00 -> 0x0101 and k 31 0 -> 0x1234 -> 0; in every
     block the smoother's state is that word << 16 (no glide), and the word the voices read is k 31 itself (finding:
     k 32's, which the smoothing may not cover, notes/63 §17.2); the track's mask (0x423087f8 + 8 t) holds bit k
     while the lock plays: k 32 bit 0 of the long at +4, k 31 bit 31 of +0.
  4. The pattern file on the stock tables. A k-32 lock saved (0x4005b95c) is a row of index 9 and loads (0x4005b766)
     onto k 9, the machine; the update of one p-lock (0x4005ba90, k 32) writes index 9 too. Finding: a k-9 lock and a
     k-32 lock on the same track (two rows of index 9, which the load keeps). A row of index 18 loads onto k 0 (how
     the official OS reads the planned fix's rows).
  5. MACHINES with a held trig, MainScreenView's key handler from its MACHINES case (0x4001c252): a press with a held
     trig reaches 0x4001c996 (the PRESET browser) and a release reaches 0x4001ca1e (the layer's sc_mach) with the
     same stack and frame; from both, the browser's path (0x4001c996, d2 = 1) runs to the handler's end (0x4001cbf2)
     with the same calls (the browser built, pushed on the view's controller with flag 1), the stack balanced and
     d2 = 1 (taken). So the planned sc_mach can open the browser on the release.

Read, not emulated (plan §3, reading.md): the browser asks whether a trig is held when it acts on a preset
(0x400a6c44, 0x400a7112) and walks the held steps then (0x400a68a0), so a browser opened on the release still makes a
preset lock while the trig is held; the step keys keep their state in the words at +92 (0x40022d58, 0x40022e3c), which
0x4006b954 clears, and the trig's release then does not toggle the trig (to see on the machine, plan §6).

Lines marked "finding" are facts for the design, not failures. Exits non-zero on a FAIL.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it:
run it in a normal terminal. Some seconds.

    python3 tools/emu/probe_switch_locks.py --cycles model-cycles_OS1.13.syx
"""
import argparse
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import mcengine as E                # noqa: E402
import seqrig as S                  # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_shortcuts as SH         # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

TRK, STEP, VAL, DESC = 2, 5, 0x0e00, 7          # the lock the probe writes: track 2, step 5, k 32 = 0x0e00
RAM, FILE = 0x91300000, 0x91400000              # the pattern's locks (6 x 4385 bytes) and its file (80 x 130)
TSTRIDE, SSTRIDE, FLAGS = 4385, 68, 4352
# 1. the setter: the stock method, the k-based calls, the sequence object
SETTER, CLEARER = 0x4000bb94, 0x4000bc00
KSET, KCLEAR = 0x4001646a, 0x400164b0
DESC_K, PSLOT_OF = 0x4005a4e8, 0x4000f208
NOTE_VT = 0x400fdb0c                            # the message 0x4000dece sends: {vtable, k, track}
PROJ1, SEL1, PSLOT = 0x93e00000, 0x93e01000, 0x93e10000
SEQ = PSLOT + 112 + 88 * TRK                    # 0x4000cfcc(pslot, t) = pslot + 0x70 + 88 t
SEQVT, SEQ_PAT, PATTRK = 0x93e20000, 0x93e20100, 0x93e30000
HOLDER, HVT, H_BASE, H_NOTE = 0x93e40000, 0x93e50000, 0x93e50100, 0x93e50200
LENGTH = 16
# 2. held trigs
STATE = 0x93a20000
FN, FN_MGR, FN_INV = 0x93e60000, 0x93e60100, 0x93e60200
ITER, BEGIN, END, STEP_GET, STEP_SET, REDRAW = 0x4006be48, 0x4006b740, 0x4006b954, 0x4006b8fe, 0x4006b91a, 0x40069b84
# 3. playing
MASK = 0x423087f8                               # per track two longs: bit k of the k locked by the trig that plays
# 5. MACHINES with a held trig
BROWSER, BROWSER_NEW, PUSH, FN_A, FN_B, HANDLER_END = 0x4001c996, 0x400a68fc, 0x40077da8, 0x400cf23c, 0x400cf044, \
    0x4001cbf2
NEW = 0x400802e0
FRAME = 0x93d20000


def w32(u, a, v):
    u.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))


def ram_init(u):
    u.uc.mem_write(RAM, (b"\xff\xff" * (34 * 64) + b"\x00" * 33) * 6)


def lock(u, t, step, k, v):
    u.uc.mem_write(RAM + t * TSTRIDE + step * SSTRIDE + 2 * k, struct.pack(">h", v))
    u.uc.mem_write(RAM + t * TSTRIDE + FLAGS + k, b"\x01")


def word(u, t, step, k):
    return struct.unpack(">h", u.uc.mem_read(RAM + t * TSTRIDE + step * SSTRIDE + 2 * k, 2))[0]


def flag(u, t, k):
    return u.uc.mem_read(RAM + t * TSTRIDE + FLAGS + k, 1)[0]


def words(u):
    """{(track, k): {step: value}} of every word of k 0..32 that is not -1."""
    out = {}
    for t in range(6):
        blk = bytes(u.uc.mem_read(RAM + t * TSTRIDE, TSTRIDE))
        for k in range(33):
            got = {s: v for s in range(64) if (v := struct.unpack_from(">h", blk, s * SSTRIDE + 2 * k)[0]) != -1}
            if got:
                out[t, k] = got
    return out


def b0(d0):
    return d0 & 0xff


# --- 0. the sites ----------------------------------------------------------------------------------------------------
def site_tests(img):
    at = lambda va, n: img[va - E.BASE:va - E.BASE + n]          # noqa: E731
    long_ = lambda va: struct.unpack(">I", at(va, 4))[0]        # noqa: E731
    check(long_(0x400fd15c) == SETTER and long_(0x400fd160) == CLEARER
          and at(0x4000bbfa, 6).hex() == "4ef94001646a" and at(0x4000bc5e, 6).hex() == "4ef9400164b0"
          and at(SETTER, 4).hex() == "4fefffec" and at(CLEARER, 4).hex() == "4feffff0",
          "the sound parameters' lock methods: 0x400fd15c -> 0x4000bb94 (set), 0x400fd160 -> 0x4000bc00 (clear), "
          "which jump to 0x4001646a and 0x400164b0")
    check(at(0x4001c274, 24).hex() == "4eb9400cf9a82f004eb94006b736588f4a006600070e6000"
          and at(SH.MACH_SITE, 6).hex() == "2f034e93588f",
          "the MACHINES case: the held-trig test at 0x4001c274 (UI state, 0x4006b736, bne 0x4001c996, bra 0x4001ca1e) "
          "and 0x4001ca1e stock")
    k_index = [long_(0x4010ee4c + 4 * k) for k in range(33)]
    index_k = [long_(0x4010eea8 + 4 * i) for i in range(24)]
    check(k_index[:23] == list(range(18)) + list(range(19, 24)) and k_index[32] == 9 and index_k[18] == 0
          and index_k[9] == 9 and 18 not in k_index[:23],
          f"the pattern file's tables: k 0..22 -> {k_index[:23]}, k 32 read past the table -> index {k_index[32]}; "
          f"index 18 -> k {index_k[18]}, index 9 -> k {index_k[9]}")


# --- 1. the setter ---------------------------------------------------------------------------------------------------
def seq_setup(u):
    """The active track's sequence object (+0 vtable, +44 the pattern's holder, +56 the track, +60 0), its method +40
    giving the track's pattern (the length at +713), the holder's +40 giving the locks and +16 the file's note; the
    project's chain stubbed; 0x4005a4e8 answers k 32 for any descriptor."""
    w32(u, SEQ, SEQVT)
    w32(u, SEQ + 44, HOLDER)
    w32(u, SEQ + 56, TRK)
    w32(u, SEQ + 60, 0)
    w32(u, SEQVT + 40, SEQ_PAT)
    u.uc.mem_write(PATTRK + 713, struct.pack(">h", LENGTH))
    w32(u, HOLDER, HVT)
    w32(u, HVT + 40, H_BASE)
    w32(u, HVT + 16, H_NOTE)
    u.hooks = {SH.PROJECT: ("project", PROJ1), SH.PROJECT_TRACKS: ("tracks", SEL1), SH.ACTIVE_TRACK: ("active", TRK),
               DESC_K: ("k", 32), PSLOT_OF: ("pslot", PSLOT), SEQ_PAT: ("pattern", PATTRK), H_BASE: ("locks", RAM),
               H_NOTE: ("note", 0)}


def notes(u):
    return [tuple(struct.unpack(">III", u.uc.mem_read(a[1], 12))) for n, a in u.calls if n == "note"]


def setter_tests(stock):
    u = SH.UI(stock)
    ram_init(u)
    seq_setup(u)
    u.calls.clear()
    d0 = b0(u.call(SETTER, 0, DESC, VAL, STEP))
    asked = [a[0] for n, a in u.calls if n == "k"]
    pslot = [a[0] for n, a in u.calls if n == "pslot"]
    got, nt = words(u), notes(u)
    others = [k for k in range(33) if k != 32 and flag(u, TRK, k)]
    check(d0 == 1 and got == {(TRK, 32): {STEP: VAL}} and flag(u, TRK, 32) == 1 and not others
          and nt == [(NOTE_VT, 32, TRK)] and asked == [DESC] and pslot == [PROJ1] and u.sp_ok and not u.bad,
          f"0x4000bb94 (a held trig + a knob, the descriptor -> k 32 by 0x4005a4e8): through 0x4000cfcc(0x4000f208("
          f"project), track) and 0x4001646a the word (track {TRK}, step {STEP}, k 32) = {VAL:#06x}, its flag 1, the "
          f"pattern file told once {nt}, every other word -1 and flag 0 (d0 {d0}, words {got})")
    u.calls.clear()
    d0 = b0(u.call(CLEARER, 0, DESC, STEP))
    check(d0 == 1 and words(u) == {} and flag(u, TRK, 32) == 0 and notes(u) == [(NOTE_VT, 32, TRK)] and u.sp_ok
          and not u.bad,
          f"0x4000bc00 (the clear, 0x400164b0 -> 0x4000dcec): the word back to -1, the flag 0, the file told once "
          f"(d0 {d0})")
    refused = []
    for step, k, v, why in ((STEP, 33, VAL, "k 33"), (STEP, 32, -0x100, "a negative value"),
                            (LENGTH + 4, 32, VAL, f"step {LENGTH + 4} past the length {LENGTH}")):
        d0 = b0(u.call(KSET, SEQ, step, k, v))
        if d0 != 0 or words(u) != {} or u.bad:
            refused.append((why, d0))
    check(not refused, "0x4001646a(seq, step, k, value) refuses k 33, a negative value and a step past the pattern's "
                       f"length, and writes nothing ({refused or 'all three refused'})")
    d0 = b0(u.call(KSET, SEQ, LENGTH - 1, 32, VAL))
    last = words(u)
    d1 = b0(u.call(KCLEAR, SEQ, LENGTH - 1, 32))
    check(d0 == 1 and last == {(TRK, 32): {LENGTH - 1: VAL}} and d1 == 1 and words(u) == {} and not u.bad,
          f"0x4001646a takes the last step ({LENGTH - 1}) and 0x400164b0 clears it")


# --- 2. held trigs ---------------------------------------------------------------------------------------------------
def walk(u, hi, lo):
    u.uc.mem_write(STATE + 348, struct.pack(">II", hi, lo))
    u.uc.mem_write(FN, struct.pack(">IIII", 0, 0, FN_MGR, FN_INV))
    u.hooks = {FN_MGR: ("manager", 0), FN_INV: ("invoke", 0), REDRAW: ("redraw", 0)}
    u.calls.clear()
    u.call(ITER, STATE, FN, 1)
    return [a[1] for n, a in u.calls if n == "invoke"], u.sp_ok and not u.bad


def held_tests(stock):
    u = SH.UI(stock)
    steps = [0, 5, 31, 32, 63]
    m = sum(1 << s for s in steps)
    got, ok = walk(u, m >> 32, m & 0xffffffff)
    swapped, ok2 = walk(u, m & 0xffffffff, m >> 32)
    check(got == steps and swapped == sorted(s ^ 32 for s in steps) and ok and ok2,
          f"0x4006be48(state, function, 1) walks the held steps of the 64-bit mask: steps 0..31 in +352, 32..63 in "
          f"+348 (mask of steps {steps}: {got}; its two longs swapped: {swapped})")
    u.hooks = {REDRAW: ("redraw", 0)}
    u.uc.mem_write(STATE + 356, b"\x00")
    u.calls.clear()
    u.call(BEGIN, STATE, 1)
    began = u.uc.mem_read(STATE + 356, 1)[0]
    u.uc.mem_write(STATE + 92, b"\x01" * 256)
    u.uc.mem_write(STATE + 348, struct.pack(">II", 0x12345678, 0x9abcdef0))
    u.call(STEP_SET, STATE, 7, 3)
    one = u.call(STEP_GET, STATE, 7)
    u.call(END, STATE)
    cleared = bytes(u.uc.mem_read(STATE + 92, 256)) == bytes(256)
    kept = struct.unpack(">II", u.uc.mem_read(STATE + 348, 8)) == (0x12345678, 0x9abcdef0)
    redraws = sum(1 for n, _ in u.calls if n == "redraw")
    check(began == 1 and one == 3 and cleared and kept and redraws == 3 and not u.bad,
          f"0x4006b740(state, 1) sets +356 ({began}); the step words at +92 + 4 s (0x4006b91a sets step 7 to 3, "
          f"0x4006b8fe reads {one}); 0x4006b954(state) clears all 64 ({cleared}) and keeps the mask ({kept}); "
          f"{redraws} redraws (0x40069b84)")


# --- 3. playing ------------------------------------------------------------------------------------------------------
def play_tests(stock):
    e = E.Engine(stock)
    rig = S.Rig(e, bpm=120)
    t = TRK
    rig.param(t, 32, 0x0101)
    for s in (0, 1, 2):
        rig.set_step(t, s)
    rig.set_lock(t, 1, 32, VAL)
    rig.set_lock(t, 1, 31, 0x1234)
    t0 = rig.now + 2 * rig.blk + rig.blk // 3
    for i, s in enumerate((0, 1, 2)):
        rig.schedule_step(t, s, t0 + 6 * i * rig.blk)
    j32 = (0xe + 0x42 * t + 2 * 32) // 2
    j31 = j32 - 1
    rows = []
    for b in range(22):
        info = rig.block()
        rows.append(dict(
            trig=bool(info["trig"] >> t & 1) or bool(info["v34"][t]),
            t32=rig.r16(S.TARGETS + 2 * j32, False), s32=rig.r32(S.SMOOTH + 4 * j32),
            p32=rig.r16(S.PARAMS + 2 * j32, False), t31=rig.r16(S.TARGETS + 2 * j31, False),
            s31=rig.r32(S.SMOOTH + 4 * j31), p31=rig.r16(S.PARAMS + 2 * j31, False),
            m0=rig.r32(MASK + 8 * t), m1=rig.r32(MASK + 8 * t + 4)))

    def runs(key):
        out = []
        for b, r in enumerate(rows):
            v = r[key] if not callable(key) else key(r)
            if not out or out[-1][1] != v:
                out.append((b, v))
        return out
    seq32 = runs(lambda r: (r["t32"], r["m1"] & 1))
    seq31 = runs(lambda r: (r["t31"], r["m0"] >> 31 & 1))
    print(f"  finding: blocks with a trig on track {t}: {[b for b, r in enumerate(rows) if r['trig']]}")
    check([v for _, v in seq32] == [(0x0101, 0), (VAL, 1), (0x0101, 0)],
          f"k 32 in the copy the voices are fed from (0x800015ae + 66 t + 64) and bit 0 of the mask's long at +4, from "
          f"block: {[(b, f'{w:#06x}', m) for b, (w, m) in seq32]} (the sound's 0x0101, step 1's lock, the sound's "
          "again)")
    check([v for _, v in seq31] == [(0, 0), (0x1234, 1), (0, 0)],
          f"k 31 the same way, bit 31 of the long at +0: {[(b, f'{w:#06x}', m) for b, (w, m) in seq31]}")
    near = lambda s, w: abs(s - (w << 16)) < 0x8000                  # noqa: E731
    glide = [(b, f"{r['s32']:#010x}", f"{r['s31']:#010x}", f"{r['p31']:#06x}") for b, r in enumerate(rows)
             if not near(r["s32"], r["t32"]) or not near(r["s31"], r["t31"]) or r["p31"] != r["t31"]]
    check(not glide and not e.unmapped,
          "in every block the smoother's state rounds to the word (k 32 and k 31) and the voices read k 31 itself: a "
          f"lock arrives whole, without a glide (blocks off: {glide})")
    exact = all(r["s32"] == r["t32"] << 16 and r["s31"] == r["t31"] << 16 for r in rows)
    print(f"  finding: the smoother's state exactly the word << 16 in every block: {exact}")
    p32 = runs("p32")
    print(f"  finding: k 32 as the voices read it (0x8000100c, the smoothed words), from block: "
          f"{[(b, f'{w:#06x}') for b, w in p32]} (SAMPLE reads the copy and the mask, not this word)")
    other = sorted({(r["m0"] & 0x7fffffff, r["m1"] & ~1 & 0xffffffff) for r in rows})
    check(other == [(0, 0)], f"no other bit of track {t}'s mask ({other})")


# --- 4. the pattern file ---------------------------------------------------------------------------------------------
def rows_of(u):
    f = bytes(u.uc.mem_read(FILE, 80 * 130))
    out = []
    for r in range(80):
        idx, trk = struct.unpack_from(">bb", f, 130 * r)
        if idx == -1 or trk == -1:
            continue
        ws = struct.unpack_from(">64h", f, 130 * r + 2)
        out.append((idx, trk, {s: v for s, v in enumerate(ws) if v != -1}))
    return out


def save_load(u, locks, update=None):
    """The locks into a fresh RAM, saved whole (0x4005b95c); then, with update = (track, step, k, value), that lock
    added and the file updated for it (0x4005ba90); the file's rows; loaded (0x4005b766) into a fresh RAM: its words."""
    ram_init(u)
    for lk in locks:
        lock(u, *lk)
    u.uc.mem_write(FILE, bytes(80 * 130))
    u.call(0x4005b95c, FILE, RAM, 0)
    if update:
        lock(u, *update)
        u.call(0x4005ba90, FILE, RAM, 0, update[2], update[0])
    rows = rows_of(u)
    ram_init(u)
    u.call(0x4005b766, RAM, FILE)
    return rows, words(u)


def file_tests(stock):
    u = SH.UI(stock)
    rows, got = save_load(u, [(TRK, STEP, 32, VAL)])
    check(rows == [(9, TRK, {STEP: VAL})] and got == {(TRK, 9): {STEP: VAL}} and not u.bad,
          f"the stock tables: a k-32 lock saved is a row of index 9 ({rows}) and loads onto k 9, the machine ({got})")
    rows, got = save_load(u, [(TRK, 1, 1, 0x3000)], update=(TRK, STEP, 32, VAL))
    check(got == {(TRK, 1): {1: 0x3000}, (TRK, 9): {STEP: VAL}} and not u.bad,
          f"the update of one p-lock (0x4005ba90, k 32): a row of index 9 too ({rows}), loaded onto k 9 ({got})")
    rows, got = save_load(u, [(TRK, 3, 9, 0x0500), (TRK, STEP, 32, VAL)])
    print(f"  finding: a k-9 lock (step 3) and a k-32 lock (step {STEP}) on track {TRK}: rows {rows}; loaded {got}")
    ram_init(u)
    lock(u, TRK, 3, 1, 0x3000)
    u.uc.mem_write(FILE, bytes(80 * 130))
    u.call(0x4005b95c, FILE, RAM, 0)
    f = bytearray(u.uc.mem_read(FILE, 80 * 130))
    at = next((130 * r for r in range(80) if f[130 * r] == 1 and f[130 * r + 1] == TRK), None)
    if at is not None:
        f[at] = 18
        u.uc.mem_write(FILE, bytes(f))
    ram_init(u)
    u.call(0x4005b766, RAM, FILE)
    got = words(u)
    check(at is not None and got == {(TRK, 0): {3: 0x3000}} and not u.bad,
          f"a row of index 18 (a k-1 row renamed) loads onto k 0, which nothing reads: the official OS reading the "
          f"planned fix's rows ({got})")


# --- 5. MACHINES with a held trig ------------------------------------------------------------------------------------
def to_case_stop(u, flags, trig, stops):
    """MainScreenView's key handler from its MACHINES case with an event of these flags (bit 0 pressed), a held trig or
    not, the frame at FRAME: the first of stops reached, the stack pointer and d2, a2, a6 there."""
    u.hooks = SH.project(u, 0, 0, 0)
    u.hooks[SH.TRIG_HELD] = ("trig", trig)
    u.uc.mem_write(SH.VIEW + 44, struct.pack(">I", SH.CONTROLLER))
    head = SH.CONTROLLER + 20
    u.uc.mem_write(head, struct.pack(">I", head))                    # the controller's views: none
    u.uc.mem_write(SH.EVENT, bytes(32))
    u.uc.mem_write(SH.EVENT + 16, struct.pack(">I", flags))
    for i, r in enumerate(SH.KEPT):
        u.uc.reg_write(r, 0x5a5a0000 + i)
    u.uc.reg_write(mk.UC_M68K_REG_D3, SH.EVENT)
    u.uc.reg_write(mk.UC_M68K_REG_A2, SH.VIEW)
    u.uc.reg_write(mk.UC_M68K_REG_A6, FRAME)
    sp = t7.STACK - 0x400
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.bad.clear()
    got = []

    def stop(uc, addr, size, ud):
        if addr in stops:
            got.append(addr)
            uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, stop)
    u.uc.emu_start(SH.MACH_CASE, 0x90000000, count=200_000)
    u.uc.hook_del(h)
    rd = lambda r: u.uc.reg_read(r) & 0xffffffff            # noqa: E731
    return (got[0] if got else None), rd(mk.UC_M68K_REG_A7), rd(mk.UC_M68K_REG_D2), rd(mk.UC_M68K_REG_A2), \
        rd(mk.UC_M68K_REG_A6)


def browser_path(u):
    """From 0x4001c996 with d2 = 1 to the handler's end (0x4001cbf2): the calls, the stack pointer and d2 there."""
    u.uc.reg_write(mk.UC_M68K_REG_D2, 1)
    u.heap = 0x93000000
    u.hooks = {NEW: ("new", 0), BROWSER_NEW: ("browser", 0), PUSH: ("push", 0), FN_A: ("fn_a", 0), FN_B: ("fn_b", 0)}
    u.calls.clear()
    u.bad.clear()
    got = []

    def stop(uc, addr, size, ud):
        if addr == HANDLER_END:
            got.append(addr)
            uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, stop)
    u.uc.emu_start(BROWSER, 0x90000000, count=200_000)
    u.uc.hook_del(h)
    calls = [(n, a[:3]) for n, a in u.calls]
    return bool(got), calls, u.uc.reg_read(mk.UC_M68K_REG_A7) & 0xffffffff, u.uc.reg_read(mk.UC_M68K_REG_D2) & 0xff, \
        not u.bad


def machines_tests(stock):
    u = SH.UI(stock)
    stops = {BROWSER: "browser", SH.MACH_SITE: "sc_mach's site", 0x4001c2a8: "taken"}
    at_p, sp_p, d2_p, a2_p, a6_p = to_case_stop(u, 1, 1, stops)
    end_p, calls_p, sp_pe, d2_pe, ok_p = browser_path(u)
    at_r, sp_r, d2_r, a2_r, a6_r = to_case_stop(u, 0, 0, stops)
    end_r, calls_r, sp_re, d2_re, ok_r = browser_path(u)
    check(at_p == BROWSER and at_r == SH.MACH_SITE and sp_p == sp_r and a2_p == a2_r == SH.VIEW
          and a6_p == a6_r == FRAME,
          f"a press with a held trig reaches 0x4001c996 (d2 {d2_p:#x}), a release reaches 0x4001ca1e (d2 {d2_r:#x}), "
          f"with the same stack ({sp_p:#x}, {sp_r:#x}), view and frame")
    pushed = [a for n, a in calls_p if n == "push"]
    check(end_p and end_r and calls_p == calls_r and sp_pe == sp_p and sp_re == sp_r and d2_pe == d2_re == 1
          and ok_p and ok_r and len(pushed) == 1 and pushed[0][0] == SH.CONTROLLER and pushed[0][2] == 1,
          f"from both, the browser's path (0x4001c996, d2 = 1) runs to the handler's end with the same calls "
          f"{[n for n, _ in calls_p]}, the browser pushed on the view's controller with flag 1, the stack balanced, "
          f"d2 = 1 (taken): the planned sc_mach can open the browser on the release")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--sites", action="store_true", help="section 0 only (no emulation)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    print("0. the sites")
    site_tests(stock)
    if args.sites:
        print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED")
        return 1 if t7.FAIL else 0
    print("1. the stock knob p-lock ends in a k-based setter")
    setter_tests(stock)
    print("2. held trigs")
    held_tests(stock)
    print("3. playing a k-32 lock (seqrig)")
    play_tests(stock)
    print("4. the pattern file on the stock tables")
    file_tests(stock)
    print("5. MACHINES with a held trig")
    machines_tests(stock)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
