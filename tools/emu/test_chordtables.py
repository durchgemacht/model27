#!/usr/bin/env python3
"""Proof of CHORD Tables (notes/66, step W4) on the OS's own code: the package tools/machines/chordtables/ as
tools/compose.py composes it, alone and next to SAMPLE.

For each selection (by default: chordtables; chordtables,sampler; sampler,chordtables), on the official OS 1.13:
  0. start-up and the sites: the bootstrap's own depacker reads the grown OS back, the boot hook copies the payload;
     CHORD's call -> cw_setup, the tick -> ct_hook_tick (or the dispatcher with SAMPLE), the payload below the RAM
     claim; the knob, descriptor 3, save and load as for REFC (test_refchord.py: the same shortcut);
  P1. cw_setup in the voice loop (0x400a7d4a), two CHORD tracks with SWEEP moving, k 30 read from the sound object on
     track 1 and from the targets on track 4 (CUR_SNDS[3] = 0, as after a preview note):
     a. Wavetable 0: identical to the stock OS, sample for sample, every setup through the stock function;
     b. a table made of the stock frames (the sine at frame 0, frames 1..31, the last repeated), at other addresses:
        identical to the stock OS, sample for sample; the stock function never called;
     c. another table (the stock frames in reverse): the four sub-voices hold that table's frames SWEEP >> 10 and the
        next, its crossfade and index; the sound differs from the stock OS;
     d. the table is latched when a note starts: k 30 changed during a note changes nothing until the next note;
     e. an empty slot, and k 30 out of range: the stock table; a negative SWEEP: frame 0, no crossfade;
  P2. the loader (ct_hook_tick in the UI harness), with the four file system calls answered by this proof (open by
     path, close, the inode's id and size, a read at a position) and the file index in memory:
     a. a scan after the mount: /Wavetables/01 to /64 opened in order, one per tick, each closed; mono files of
        k x 256 samples (k = 32, 1, 4, 2, and 5 in a file made by tools/wavetable.py, the sine first) built exactly as the proof computes them (the spread, Q31, the 257th sample,
        33 pointers); a stereo file, one of 300 samples, one of 33 frames and a missing one leave their slot empty;
        the tick returns the stock getter's answer;
     b. nothing changes: no file call;
     c. a file added: a new scan, the others kept without a read (same id), the new one loaded;
     d. a file replaced: its slot gets a new buffer, the old one waits while a track's latch holds it, then is free;
     e. a file deleted: its slot empty;
     f. the drive not mounted, or its lock held by the running task: no file call; mounted again: a new scan;
     g. no free buffer: the scan waits on the file, and goes on once a buffer is free;
  C. the cost by the standard's method (STANDARD.md §6): instructions per block per voice in the real voice loop,
     CHORD alone on track 1, the first block of the note then the mean and maximum of the next 21, for stock CHORD,
     Wavetable 0 and a table; printed as findings, and the extension's share checked to stay small.

Needs Unicorn and numpy (pip install unicorn numpy) and m68k-elf-objdump; Unicorn's JIT does not run inside a
sandbox that forbids it: run it in a normal terminal (model27's .venv-emu has both). About two minutes.

    python3 tools/emu/test_chordtables.py --cycles model-cycles_OS1.13.syx [--machines chordtables,sampler]
"""
import argparse
import math
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compose                      # noqa: E402
import mcengine as E                # noqa: E402
import test_compose as TC           # noqa: E402
import test_refchord as R           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_shortcuts as S          # noqa: E402
import wavetable as W               # noqa: E402  (tools/wavetable.py, the converter of notes/66 §4)
from test_sdvintage_7th import check  # noqa: E402

SELECTIONS = [["chordtables"], ["chordtables", "sampler"], ["sampler", "chordtables"]]
SETUP, CALL_AT, TICK_AT, GETTER = 0x400a8080, 0x400ab15e, 0x400075f0, 0x40076be4
CHORD = 5
RAM, RAM_END = 0x43400000, 0x43700000          # the package's RAM claim
STAGE_BYTES, BUF_BYTES, POINTERS, FRAMES, FRAME_LEN = 16384, 33040, 33, 32, 257
CUR_SNDS, TARGETS, SINE, CHORD_TABLE = 0x800017ec, 0x800015ae, 0x8000eee4, 0x40118590
SOUNDS = 0x407c0000                             # the proof's sounds in the voice loop's memory (unused by the OS)
OPEN, CLOSE, ENTRY, READ = 0x4007bc5e, 0x4007bc1c, 0x4007de78, 0x4007baaa
MOUNTED, FS_LOCK, RUNNING, INDEX_COUNT, INDEX = 0x40f07cf4, 0x40fe6df0, 0x422fef30, 0x401fb8a0, 0x401fb8a4
TASK = 0x93f80000                               # the running task, as the proof names it


def buf(b):
    return RAM + STAGE_BYTES + b * BUF_BYTES


def be32s(words):
    return b"".join(struct.pack(">I", w & 0xffffffff) for w in words)


# --- 0. start-up and the sites ---------------------------------------------------------------------------------------
def site_tests(key, tweak, img, runtime, info, added):
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    u = S.UI(img, runtime)
    at = lambda va, n: bytes(u.uc.mem_read(va, n))
    check(at(CALL_AT, 6) == R.jsr(syms["cw_setup"]), f"{key}: {CALL_AT:#x} -> jsr cw_setup ({syms['cw_setup']:#x})")
    tick = syms.get("dp_tick", syms["ct_hook_tick"])
    check(at(TICK_AT, 6) == R.jsr(tick), f"{key}: {TICK_AT:#x} -> jsr {'dp_tick' if 'dp_tick' in syms else 'ct_hook_tick'}")
    sc = syms["sc_data"]
    check(at(sc + 16, 1)[0] == CHORD and at(sc + 17, 1)[0] == 1 + len(added),
          f"{key}: the shortcut layer's tables from machine 5, {1 + len(added)} machine(s)")
    check(info["end"] <= RAM, f"{key}: the payload ({info['pay']:#x}..{info['end']:#x}) below the RAM claim {RAM:#x}")
    return syms


# --- P1. cw_setup in the voice loop ----------------------------------------------------------------------------------
class Voice:
    """The voice loop of a build (or of the stock OS), with the RAM claim mapped, two CHORD tracks (1 and 4), the
    proof's sounds for the sound-object path and the targets for the other."""

    TRACKS = (0, 3)

    def __init__(self, img, runtime=None, tweak=None, syms=None):
        e = self.e = TC.engine(img, runtime, tweak)
        if runtime is not None:
            e.uc.mem_map(RAM, RAM_END - RAM)
        self.syms = syms or {}
        self.stock_calls = 0

        def hk(uc, a, s, u_):
            self.stock_calls += 1
        e.uc.hook_add(UC_HOOK_CODE, hk, begin=SETUP, end=SETUP)
        for t in self.TRACKS:
            e.set(t, machine=CHORD, note=60, pitch=64, finetune=64, color=3, shape=43, sweep=24, contour=64,
                  punch=0, gate=0, decay=64)
        e.uc.mem_write(CUR_SNDS + 4 * 0, struct.pack(">I", SOUNDS))
        e.uc.mem_write(CUR_SNDS + 4 * 3, struct.pack(">I", 0))
        self.k30(0)

    def k30(self, n, track=None):
        """Wavetable n on the proof's tracks: in the sound object (track 1) and in the targets (track 4)."""
        for t in (self.TRACKS if track is None else (track,)):
            w = struct.pack(">h", n << 8 if -128 <= n < 128 else n)
            if t == 0:
                self.e.uc.mem_write(SOUNDS + 80, w)
            else:
                self.e.uc.mem_write(TARGETS + 66 * t + 60, w)

    def frame(self, va):
        return bytes(self.e.uc.mem_read(va, 4 * FRAME_LEN))

    def run(self, blocks, trigs=(1,), sweep=None, at_block=None):
        out = []
        for b in range(blocks):
            if at_block:
                at_block(self, b)
            if sweep:
                for t in self.TRACKS:
                    self.e.set(t, sweep=sweep(b, t))
            mask = sum(1 << t for t in self.TRACKS) if b in trigs else 0
            out.append(self.e.block(mask)[list(self.TRACKS)])
        return np.array(out)

    def sub(self, t):
        """Track t's four sub-voices: (frame 0, frame 1, crossfade, index) each."""
        v = E.VOICE0 + t * E.VSTRIDE
        return [struct.unpack(">4I", self.e.uc.mem_read(v + 120 * j + 168, 8) + self.e.uc.mem_read(v + 120 * j + 156, 4)
                              + self.e.uc.mem_read(v + 120 * j + 184, 4)) for j in range(4)]

    def table(self, slot, b, frames):
        """A table in buffer b, published in slot (0-based): the frames (each 257 longs as bytes) and 33 pointers."""
        base = buf(b)
        ptrs = [base + 4 * POINTERS + 4 * FRAME_LEN * s for s in range(FRAMES)]
        for s in range(FRAMES):
            self.e.uc.mem_write(ptrs[s], frames[s])
        self.e.uc.mem_write(base, be32s(ptrs + [ptrs[-1]]))
        self.e.uc.mem_write(self.syms["ct_slot"] + 4 * slot, struct.pack(">I", base))
        return ptrs + [ptrs[-1]]


def sweeps(b, t):
    return (24 + 3 * b + 40 * t) % 128


def voice_tests(key, stock, tweak, img, runtime, syms, blocks):
    ref = Voice(stock)
    x = ref.run(blocks, trigs=(1, blocks // 2), sweep=sweeps)
    stock_frames = [ref.frame(SINE)] + [ref.frame(struct.unpack(">I", ref.e.uc.mem_read(CHORD_TABLE + 4 * i, 4))[0])
                                         for i in range(31)]
    # a. Wavetable 0
    v = Voice(img, runtime, tweak, syms)
    y = v.run(blocks, trigs=(1, blocks // 2), sweep=sweeps)
    check(np.array_equal(x, y) and np.max(np.abs(x)) > 1e6 and v.stock_calls == ref.stock_calls > 0
          and not v.e.unmapped,
          f"{key}: P1a Wavetable 0: identical to the stock OS, sample for sample; {v.stock_calls} setups through the "
          "stock function, as many as in the stock OS")
    # b. the stock frames as a table
    v = Voice(img, runtime, tweak, syms)
    ptrs = v.table(6, 0, stock_frames)
    v.k30(7)
    y = v.run(blocks, trigs=(1, blocks // 2), sweep=sweeps)
    latched = [struct.unpack(">I", v.e.uc.mem_read(syms["ct_latch"] + 4 * t, 4))[0] for t in v.TRACKS]
    check(np.array_equal(x, y) and v.stock_calls == 0 and latched == [buf(0)] * 2 and not v.e.unmapped,
          f"{key}: P1b Wavetable 7 = the stock frames at {buf(0):#x}: identical to the stock OS, sample for sample; "
          f"the stock function never called; both tracks latched (the sound object and the targets)")
    # c. another table: the stock frames in reverse
    v = Voice(img, runtime, tweak, syms)
    rev = v.table(0, 1, stock_frames[::-1])
    v.k30(1)
    got, ok = [], True
    for b in range(blocks):
        sw = sweeps(b, 0)
        for t in v.TRACKS:
            v.e.set(t, sweep=sweeps(b, t))
        v.e.block(sum(1 << t for t in v.TRACKS) if b == 1 else 0)
        if b >= 3:
            for t in v.TRACKS:
                sw = sweeps(b, t) << 8
                i, xf = sw >> 10, (sw & 1023) << 21
                ok &= all(s == (rev[i], rev[i + 1], xf, i) for s in v.sub(t))
                got.append(i)
    check(ok and len(set(got)) > 10 and not v.e.unmapped,
          f"{key}: P1c Wavetable 1 = the stock frames in reverse: the four sub-voices of both tracks hold its frames "
          f"SWEEP >> 10 and the next, the crossfade and the index, in every block ({len(set(got))} frames reached)")
    v2 = Voice(img, runtime, tweak, syms)
    v2.table(0, 1, stock_frames[::-1])
    v2.k30(1)
    y2 = v2.run(blocks, trigs=(1,), sweep=sweeps)
    x2 = Voice(stock).run(blocks, trigs=(1,), sweep=sweeps)
    check(not np.array_equal(x2, y2) and np.max(np.abs(y2)) > 1e6,
          f"{key}: P1c the reversed table sounds other than the stock OS (peak {np.max(np.abs(y2)):.3g})")
    # d. latched when a note starts
    v = Voice(img, runtime, tweak, syms)
    a_ = v.table(0, 0, stock_frames)
    b_ = v.table(1, 1, stock_frames[::-1])
    v.k30(1)
    seen = []

    def change(vv, b):
        if b == 10:
            vv.k30(2)                       # during the note
        if b == 20:
            seen.append(vv.sub(0)[0][0])

    v.run(30, trigs=(1, 25), at_block=change)
    after = v.sub(0)[0][0]
    check(seen and seen[0] in a_ and after in b_ and not v.e.unmapped,
          f"{key}: P1d k 30 changed during a note: the note keeps table 1 ({seen[0]:#x}); the next note plays table 2 "
          f"({after:#x})")
    # e. empty slot, out of range, negative SWEEP
    for n, why in ((5, "an empty slot"), (65, "k 30 = 65"), (-1, "k 30 = -1")):
        v = Voice(img, runtime, tweak, syms)
        v.k30(n)
        y = v.run(blocks, trigs=(1, blocks // 2), sweep=sweeps)
        check(np.array_equal(x, y) and v.stock_calls == ref.stock_calls, f"{key}: P1e {why}: the stock table, "
              "identical to the stock OS")
    v = Voice(img, runtime, tweak, syms)
    t0 = v.table(0, 0, stock_frames[::-1])
    v.k30(1)
    v.run(4, trigs=(1,), sweep=lambda b, t: -10)
    check(all(s == (t0[0], t0[1], 0, 0) for t in v.TRACKS for s in v.sub(t)),
          f"{key}: P1e a negative SWEEP: frame 0 and frame 1, no crossfade, index 0")


# --- P2. the loader ----------------------------------------------------------------------------------------------------
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


def expected(samples, k):
    """The 32 frames the loader must build: the spread with C's integer division, Q31, the 257th sample."""
    out = []
    for s in range(FRAMES):
        pos = s * (k - 1)
        i0, rem = pos // (FRAMES - 1), pos % (FRAMES - 1)
        a = samples[i0 * 256:(i0 + 1) * 256]
        b = samples[(i0 + 1) * 256:(i0 + 2) * 256] if rem else a
        f = []
        for j in range(256):
            d = (b[j] - a[j]) * rem
            q = abs(d) // (FRAMES - 1)
            f.append(((a[j] + (q if d >= 0 else -q)) << 16) & 0xffffffff)
        out.append(be32s(f + [f[0]]))
    return out


class Drive:
    """The +Drive as the loader sees it: files by path, their inodes and ids, the index in memory; the four calls
    answered here, each one noted."""

    def __init__(self, u):
        self.u, self.files, self.calls, self.next_ino = u, {}, [], 100
        u.uc.mem_map(RAM, RAM_END - RAM)
        for va, fn in ((OPEN, self._open), (CLOSE, self._close), (ENTRY, self._entry), (READ, self._read)):
            u.uc.hook_add(UC_HOOK_CODE, self._wrap(fn), begin=va, end=va)
        self.mount(True)
        self.w32(FS_LOCK, 0)
        self.w32(RUNNING, TASK)

    def w32(self, a, v):
        self.u.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def mount(self, on):
        self.w32(MOUNTED, 1 if on else 0)

    def put(self, name, data):
        self.files[name] = (self.next_ino, (hash(data) & 0x7ffffffe) | 1, data)
        self.next_ino += 1
        self.index()

    def drop(self, name):
        del self.files[name]
        self.index()

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
        return bytes(self.u.uc.mem_read(a, 32)).split(b"\0")[0].decode("latin-1")

    def by_ino(self, ino):
        return next(((n, f) for n, f in self.files.items() if f[0] == ino), (None, None))

    def _open(self, path, mode, h, _x):
        p, m = self.cstr(path), self.cstr(mode)
        self.calls.append(("open", p, m))
        if p not in self.files:
            return -1
        self.u.uc.mem_write(h, struct.pack(">4I", self.files[p][0], 0, 0, 1))
        return 0

    def _close(self, h, *_x):
        self.calls.append(("close", struct.unpack(">I", self.u.uc.mem_read(h, 4))[0]))
        return 0

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


def loader_tests(key, img, runtime, syms):
    u = S.UI(img, runtime)
    d = Drive(u)
    u.hooks = {GETTER: ("getter", 0x5a)}
    for s in ("smp_hook_tick",):              # SAMPLE's own tick, with the dispatcher: not this proof's
        if s in syms:
            u.hooks[syms[s]] = (s, 0x5a)
    tick = syms.get("dp_tick", syms["ct_hook_tick"])
    r32 = lambda a: struct.unpack(">I", u.uc.mem_read(a, 4))[0]
    slot = lambda n: r32(syms["ct_slot"] + 4 * (n - 1))
    owner = lambda b: u.uc.mem_read(syms["ct_owner"] + b, 1)[0]

    def ticks(n):
        rets, opens = [], []
        for _ in range(n):
            d.calls.clear()
            rets.append(u.call(tick, S.VIEW) & 0xff)
            opens.append(sum(1 for c in d.calls if c[0] == "open"))
        return rets, opens

    def table_ok(n, samples, k):
        b = slot(n)
        if not b:
            return False
        ptrs = struct.unpack(f">{POINTERS}I", u.uc.mem_read(b, 4 * POINTERS))
        want = [b + 4 * POINTERS + 4 * FRAME_LEN * s for s in range(FRAMES)]
        if list(ptrs) != want + [want[-1]]:
            return False
        return all(bytes(u.uc.mem_read(p, 4 * FRAME_LEN)) == f for p, f in zip(want, expected(samples, k)))

    files = {1: (32, 11), 2: (1, 12), 3: (4, 13), 64: (2, 14)}
    data = {n: frames_of(k, seed) for n, (k, seed) in files.items()}
    for n, (k, _s) in files.items():
        d.put(f"/Wavetables/{n:02d}", sample_file(data[n]))
    d.put("/Wavetables/05", sample_file(frames_of(2, 15), stereo=True))
    d.put("/Wavetables/06", sample_file(frames_of(2, 16)[:300]))     # 300 samples: not k x 256
    d.put("/Wavetables/07", sample_file(frames_of(33, 17)))
    # 08: what tools/wavetable.py makes of a 4-frame saw table at 2048 samples a frame: the sine, then 4 frames
    saw = [sum(math.sin(h * (2 * math.pi * m / 2048 + 0.5 * j)) / h for h in range(1, 120)) * 0.5
           for j in range(4) for m in range(2048)]
    data[8], _rep = W.convert(saw)
    files[8] = (5, None)                       # the converter's sine, then the 4 frames
    d.put("/Wavetables/08", W.device_bytes(data[8]))
    # a. the scan after the mount
    log = []
    rets, opens = [], []
    for _ in range(64):
        d.calls.clear()
        rets.append(u.call(tick, S.VIEW) & 0xff)
        log.append(list(d.calls))
        opens.append(sum(1 for c in d.calls if c[0] == "open"))
    paths = [c[1] for calls in log for c in calls if c[0] == "open"]
    closes = sum(1 for calls in log for c in calls if c[0] == "close")
    check(paths == [f"/Wavetables/{n:02d}" for n in range(1, 65)] and opens == [1] * 64 and r32(syms["ct_scan"]) == 0
          and all(c[2] == "r" for calls in log for c in calls if c[0] == "open") and closes == 8 and not u.bad,
          f"{key}: P2a the scan: /Wavetables/01 to /64 opened in order, one per tick, read mode, each found one closed; "
          "the scan ends")
    check(set(rets) == {0x5a}, f"{key}: P2a every tick returns the stock getter's answer")
    check(all(table_ok(n, data[n], k) for n, (k, _s) in files.items()),
          f"{key}: P2a files 01 (32 frames), 02 (1), 03 (4), 64 (2) and 08 (5, made by tools/wavetable.py, its first frame "
          "the sine): their tables "
          "built exactly as computed here (spread, Q31, the 257th sample, 33 pointers)")
    check(all(slot(n) == 0 for n in range(1, 65) if n not in files),
          f"{key}: P2a a stereo file (05), 300 samples (06), 33 frames (07) and the missing files: empty slots")
    reads = [c for calls in log for c in calls if c[0] == "read"]
    check(all((c[2], c[3]) in ((0, 64), (64, 2 * 256 * files[int(c[1][-2:])][0])) for c in reads
              if c[1] and int(c[1][-2:]) in files),
          f"{key}: P2a each table read as its header (64 bytes at 0) and its frames (at 64)")
    # b. nothing changes
    _r, opens = ticks(10)
    check(sum(opens) == 0, f"{key}: P2b nothing changed: no file call in 10 ticks")
    # c. a file added
    before = {n: slot(n) for n in files}
    data[4] = frames_of(3, 18)
    d.put("/Wavetables/04", sample_file(data[4]))
    log = []
    for _ in range(64):
        d.calls.clear()
        u.call(tick, S.VIEW)
        log.append(list(d.calls))
    reads = {c[1] for calls in log for c in calls if c[0] == "read"}
    frames_read = {c[1] for calls in log for c in calls if c[0] == "read" and c[2] == 64}
    check(frames_read == {"/Wavetables/04"} and not reads & {f"/Wavetables/{n:02d}" for n in files}
          and all(slot(n) == before[n] for n in files) and table_ok(4, data[4], 3),
          f"{key}: P2c a file added: a new scan; 01, 02, 03 and 64 kept without a read (the same id); 04 loaded "
          "(the rejected 05 to 07 only have their header read again)")
    files[4] = (3, 18)
    # d. a file replaced, its old buffer latched by a track
    old = slot(2)
    old_b = (old - buf(0)) // BUF_BYTES
    u.uc.mem_write(syms["ct_latch"], struct.pack(">I", old))
    data[2] = frames_of(2, 19)
    d.drop("/Wavetables/02")
    d.put("/Wavetables/02", sample_file(data[2]))
    ticks(64)
    check(slot(2) not in (0, old) and table_ok(2, data[2], 2) and owner(old_b) == 0xff,
          f"{key}: P2d a file replaced: slot 2 in a new buffer, built from the new file; the old buffer waits "
          "(a track's latch holds it)")
    u.uc.mem_write(syms["ct_latch"], struct.pack(">I", 0))
    ticks(1)
    check(owner(old_b) == 0, f"{key}: P2d the latch let go: the old buffer is free at the next tick")
    # e. a file deleted
    d.drop("/Wavetables/03")
    ticks(64)
    check(slot(3) == 0 and all(slot(n) for n in (1, 2, 4, 64)), f"{key}: P2e a file deleted: slot 3 empty, the others kept")
    # f. not mounted, the lock held by the running task
    d.mount(False)
    _r, opens = ticks(5)
    d.mount(True)
    d.w32(FS_LOCK, TASK)
    _r, opens2 = ticks(5)
    d.w32(FS_LOCK, 0)
    _r, opens3 = ticks(2)
    check(sum(opens) == 0 and sum(opens2) == 0 and opens3 == [1, 1],
          f"{key}: P2f the drive not mounted, then its lock held by the running task: no file call; free again after "
          "the mount: a new scan")
    ticks(64)
    # g. no free buffer
    full = bytes(u.uc.mem_read(syms["ct_owner"], 72))
    u.uc.mem_write(syms["ct_owner"], bytes(b if b else 0x40 for b in full))
    data[9] = frames_of(1, 20)
    d.put("/Wavetables/09", sample_file(data[9]))
    ticks(12)
    waiting = r32(syms["ct_scan"]) == 9 and slot(9) == 0
    u.uc.mem_write(syms["ct_owner"], full)
    ticks(60)
    check(waiting and table_ok(9, data[9], 1) and r32(syms["ct_scan"]) == 0 and not u.bad,
          f"{key}: P2g no free buffer: the scan waits on file 09; once a buffer is free, 09 is loaded and the scan ends")


# --- C. the cost, by the standard's method (STANDARD.md §6) -----------------------------------------------------------
COST_BLOCKS = 21


def cost_run(img, runtime=None, tweak=None, syms=None, frames=None, n=0, trig=True):
    """Instructions per block in the real voice loop, track 1 alone on CHORD (machine defaults, note 60, SWEEP 24),
    trig in block 1: [block 0, block 1, ...]; the other five voices muted."""
    v = Voice(img, runtime, tweak, syms)
    v.e.set(3, machine=0x7f)
    if frames is not None:
        v.table(0, 0, frames)
    v.k30(n, track=0)
    v.e.count_instructions()
    counts = []
    for b in range(3 + COST_BLOCKS):
        before = v.e.instructions
        v.e.block(1 if trig and b == 1 else 0)
        counts.append(v.e.instructions - before)
    return counts


def cost_tests(key, stock, tweak, img, runtime, syms):
    idle = cost_run(stock, trig=False)
    per_voice = lambda c: [x - y for x, y in zip(c, idle)]
    stock_frames = [Voice(stock).frame(SINE)]
    ref = Voice(stock)
    stock_frames += [ref.frame(struct.unpack(">I", ref.e.uc.mem_read(CHORD_TABLE + 4 * i, 4))[0]) for i in range(31)]
    out = {}
    for name, args in (("stock CHORD", (stock,)), ("Wavetable 0", (img, runtime, tweak, syms)),
                       ("a table", (img, runtime, tweak, syms, stock_frames[::-1], 1))):
        c = per_voice(cost_run(*args))
        first, rest = c[2], c[3:3 + COST_BLOCKS]       # block 2: the note starts (the machine change, §11.6)
        out[name] = (first, sum(rest) / len(rest), max(rest))
        finding(f"{key}: cost, {name}: first block {first}, then mean {out[name][1]:.0f}, max {out[name][2]} "
                f"instructions per block per voice (over {COST_BLOCKS} blocks)")
    d0 = out["Wavetable 0"][1] - out["stock CHORD"][1]
    d1 = out["a table"][1] - out["stock CHORD"][1]
    check(0 <= d0 < 100 and -100 < d1 < 200,
          f"{key}: the extension adds {d0:+.0f} instructions per block per voice at Wavetable 0 and {d1:+.0f} with a "
          "table, against stock CHORD; the emulator does not time memory, and a table's frames are read in SDRAM "
          "instead of SRAM (notes/66 §0)")


def finding(msg):
    print("finding  " + msg)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--blocks", type=int, default=80, help="blocks of 32 frames in the voice loop")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    for ids in selections:
        if "chordtables" not in ids:
            sys.exit(f"!! {'+'.join(ids)}: the proof needs chordtables")
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        added = TC.configure([i for i in ids if compose.load_manifest(i)["_machine"]])
        print(f"\n{key}: CHORD extended (machine 5)" + "".join(f", {m['name']} = machine {m['index']}" for m in added)
              + f"; payload {len(runtime)} bytes at {compose.gs.PAY_ALONE:#x}, RAM claim {RAM:#x}..{RAM_END:#x}")
        print("0. start-up, the sites, the shortcut")
        X.bootstrap_depack_ok(args.cycles, tweak, None) or t7.FAIL.append(f"{key}: bootstrap")
        X.boot_hook_ok(img, runtime) or t7.FAIL.append(f"{key}: boot hook")
        syms = site_tests(key, tweak, img, runtime, info, added)
        R.knob_tests(key, img, runtime, added)
        R.descriptor_tests(key, img, runtime, added)
        R.save_tests(key, stock, img, runtime)
        print("P1. cw_setup in the voice loop")
        voice_tests(key, stock, tweak, img, runtime, syms, args.blocks)
        print("P2. the loader")
        loader_tests(key, img, runtime, syms)
        print("C. the cost (STANDARD.md §6)")
        cost_tests(key, stock, tweak, img, runtime, syms)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
