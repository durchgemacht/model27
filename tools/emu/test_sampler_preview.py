#!/usr/bin/env python3
"""Proof of SAMPLE's browser preview (Cycles One-Shot 0.16, notes/60 §24) on the OS's own code: while the PRESET
browser's cursor rests on a sample file on a SAMPLE track, the pad and the TRIG keys play that sample with the track's
settings, as the Model:Samples does, the way they play a preset under the cursor (notes/46 §2); the sequencer keeps
the track's own sound.

The OS's preview (0x400a63ac) reads the entry under the cursor as a preset (jsr 0x400a3052 at 0x400a6426); a sample
file fails its size check, so nothing is marked and the pad plays the track's sound (notes/46 §3.1). SAMPLE takes that
call (smp_hook_preview): on a SAMPLE track a sample file gives the track's sound naming the file (pool.c's
smp_browser_open, the one the open at 0x400a6602 uses), which the OS then copies into one of its two preview buffers
and marks (0x40081bd6, *0x40fb5a04). SAMPLE's tick (the screen's redraw, 0x400075f0) loads what the marked sound names,
next to what the kits and the tracks name, and frees it once nothing is marked.

The images: the official OS 1.13 ("stock") and SAMPLE as compose.py composes it, alone and next to REF2 (whose
browser hook at 0x400a6602 goes through the dispatcher; the preview stays SAMPLE's own hook). The bench is
test_sample_preview.py's (the browser in file mode with the OS's own PresetManager and FileSystemDirectory vtables, its
files' inodes, the note played live up to its post to the audio side), on mcengine's voice loop with the composed
payload. Stood in for: the file system (inodes, the preset reader's file read 0x400a2a28 for preset sizes, the open
0x4007e3a0, SAMPLE's entry 0x4007de78 and read 0x4007baaa, which serve the files' bytes), the allocator, the locks,
the interface's mailboxes, the post of the note (0x4005894a) and the view getter after the tick (0x40076be4). The
audio side's copy of a note's sound (0x40058a0a: +20..+85 into 0x800015ae + 66 t, the note's sound 0 after a preview
note) is written as the OS writes it; test_sample_preview.py §4 runs that event loop itself.

  1. The sites: 0x400a6426 holds jsr 0x400a3052 on the stock OS and jsr smp_hook_preview in each build.
  2. The cursor (the real 0x400a64be, and 0x400a63ac as the browser's opening calls it, 0x400a6d12), track 3 a SAMPLE
     track: on a sample file (mono, stereo, 161 bytes) the stock OS marks nothing; SAMPLE marks one of the OS's two
     buffers holding the track's sound with the file's inode and id in k 25..27, every other byte the track's, without
     the OS opening or reading the file (one read of its 64-byte header by SAMPLE), d2..d7/a2..a6 kept; two files in
     a row alternate the buffers. As on the stock OS: a preset (120 bytes), a file of 160 bytes, a sample file whose
     header is out of range, a sample file on a TONE track, the drive in use by this task.
  3. The note: the pad of the active track (source 0x40, as the pad and the TRIG keys in CHROMATIC mode,
     0x4001d08e / 0x40019edc) posts the marked buffer at +52 of its event; another track's note carries nothing.
  4. The tick and the voice: the track's own sample (level +) loads and plays; the marked file (600 000 bytes, level
     -) is silent on a preview note until the ticks have read it all (one for its header, five of 128 KiB), then a
     preview note plays it and a normal note the track's own; with nothing marked (0x40081bd6(0), as the browser's
     close) and no voice on it, it is freed: a preview note with the old buffer is silent, and marking it again takes
     the ticks again. The cursor moving on before a file is complete: the next one loads and plays. A marked preset
     of another machine makes the tick call nothing of the file system. The tick returns the getter's answer.
  5. The pad held (0x4001d05e and 0x4001d0fc, the pads' own note functions, SAMPLE's hooks at their entries; the TRIG
     keys' 0x40019e7a and 0x40019c84 in the engine tests, the key's note-off at once too, its trigs the track's own): run
     from their entry, the pad's note carries the mark; with the pad held a trig of the track's own sound plays the
     marked sample, a lock's sound its own; the pad let go, the note goes on in the track's own without a trig, and
     the next trig plays the track's own; the browser closed with the pad held does the same.
     Through the audio side's own event loop (0x40058d46..0x400591e4, as test_sample_preview.py §4 runs it), the
     notes posted for real: with nothing marked the pad's note holds its track (rank 2, 0x40fe4c9c) and a sequencer's
     note (rank 1) is dropped, as on the stock OS; with a sample marked SAMPLE sends the pad's note-off at once
     (0x4008145e(track, note, 0x40), once, the registers kept), the track is free again, the sequencer's note reaches
     it and plays the marked sample; the note-off of the release is dropped (the track's rank and note kept), after a
     sequencer's note or without one, and the note goes on in the track's own; with a live recording the press still
     starts the recorded note (0x4008273c) and only the release ends it (0x400827a8).
  6. The cost: instructions in the payload per block of SAMPLE playing a note, One-Shot 0.15 (the last commit's
     27-sampler.json, through git) against 0.16 with nothing held, with the pad held, and the block it is let go.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_sampler_preview.py --cycles model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys
from collections import defaultdict

from unicorn import UcError, UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import mcengine as E                # noqa: E402
import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

SELECTIONS = [["sampler"], ["sampler", "refmachine2"]]
BASE = 0x40000400
# --- the OS (1.13)
SITE, OPEN_SITE = 0x400a6426, 0x400a6602
PREVIEW = 0x400a63ac              # the preview of the entry (browser, index); also called at 0x400a6d12
CURSOR = 0x400a64be               # the cursor moved: 0x400a63ac, else 0x40081bd6(0)
PARSE = 0x400a3052                # reads a preset (a0 = &result, &handle)
READ = 0x400a2a28                 # reads a preset's file (buffer, &handle): 0 / -1
SND_PARSE = 0x4005d776            # decodes the preset read into a sound
OPEN = 0x4007e3a0                 # opens a file by its handle
MARK = 0x40081bd6                 # marks a sound for the next notes played live (*0x40fb5a04)
ARMED = 0x40fb5a04
BUFS = (0x40a78c90, 0x40a78cf4)   # the OS's two preview buffers of 100 bytes, in turn (0x40058504)
NOTE_ON, POST = 0x4008171e, 0x4005894a
ACTIVE = 0x40a700c4               # the active track as the notes see it
CUR_SNDS, TARGETS = 0x800017ec, 0x800015ae
KITP, CUR_KIT, BANK = 0x800017e4, 0x40a78888, 0x406fa040
PROJ_PTR, UIS_PTR = 0x40fe4228, 0x40fe4218
FS_ENTRY, FS_READ = 0x4007de78, 0x4007baaa   # SAMPLE's file system calls (machine/os.h)
MOUNTED, FS_LOCK, RUNNING = 0x40f07cf4, 0x40fe6df0, 0x422fef30
GETTER = 0x40076be4               # the stock call the tick hook returns from (does the view need drawing)
KEY_ON, KEY_OFF = 0x40019e7a, 0x40019c84   # a TRIG key plays its note in CHROMATIC mode (view, track, note, velocity,
                                           # speed), ends it (view, track, note): called only by the keyboard's handler
KEY_ASK = (0x400cf9a8, 0x4006bdfe, 0x4000f23e)   # what the key's note functions ask first (a getter, a setting, as the
                                           # pads' 0x4000f208): stood in for, 0
PAD_ON, PAD_OFF = 0x4001d05e, 0x4001d0fc   # a pad plays its note (view, track, note, velocity, speed), ends it (view,
                                           # track, note): called only by the pads' handler 0x4001d180
NOTE_OFF = 0x4008145e
EV_LOOP, EV_END = 0x40058d46, 0x400591e4   # one pass of the audio interrupt's event loop (test_sample_preview.py §4)
FRAME = 0x9000f000                          # its frame (test_arp)
RANK, HOLDS = 0x40fe4c9c, 0x40fe4cb4        # by track: the rank and the note of the note holding it (0x40058e3e)
QSEND = 0x40092116                          # the post's send into the audio side's queue (0x400589b4)
REC_ASK = (0x4000eb90, 0x40012e82)          # what the pads' note functions ask before a live recording's call
REC_START, REC_END = 0x4008273c, 0x400827a8  # a live recording's note: its start (0x4001d0ec), its end (0x4001d170)
PAD_AFTER = (0x4000f208, 0x4000cfcc, 0x40016e90)   # what the pads' note functions ask after the note: stood in for
PAYLOAD_LO, PAYLOAD_HI = 0x43000000, 0x43800000     # the added machines' code and tables, below the sample pool
# --- the bench
STOP = E.STOP
CALL_SP = 0x9000e000
STACK_POISON = 0x3000
FIX = 0x93000000                  # the bench's objects (0x93000000..0x95000000)
PM, FSD, SPD, ENT, INODE, PMVT, TRKVT, UIST = (FIX + 0x1000 * i for i in range(8))
PROJ, VIEW, MIDI, PADVIEW = FIX + 0x10000, FIX + 0x18000, FIX + 0x20000, FIX + 0x38000
EVT = FIX + 0x30000               # a sequencer's note event
KIT, POOL3, HEAP = 0x93800000, 0x93900000, 0x94000000
TASK = 0x93f80000                 # the running task
CALLEE = [getattr(mk, f"UC_M68K_REG_D{i}") for i in range(2, 8)] + \
         [getattr(mk, f"UC_M68K_REG_A{i}") for i in range(2, 7)]
CALLEE_VALS = [0x22220002, 0x33330003, 0x44440004, 0x55550005, 0x66660006, 0x77770007,
               0x93f00000, 0x93f10000, 0x93f20000, 0x93f30000, 0x93f40000]
TRACK = 2                         # the SAMPLE track (track 3)
TONE_TRACK = 4
PRESET_H = 0x11111111
OWN_H = 0x0000AAAB                # the track's own sample
LEVEL = 8192


def header(nbytes, rate=48000, stereo=False):
    h = bytearray(64)
    h[1] = 1 if stereo else 0
    struct.pack_into(">II", h, 4, nbytes, rate)
    return bytes(h)


def sample(frames, level, stereo=False, rate=48000):
    pcm = struct.pack(">h", level) * (frames * (2 if stereo else 1))
    return header(len(pcm), rate, stereo) + pcm


# The browser's entries: (size, id, the file's bytes or None); None = a folder. Inode = 0x100 + index.
FILES = [
    (None, 0x6809683D, sample(300_000, -LEVEL)),                 # 0: 600 064 bytes, mono, level -
    (120, PRESET_H, None),                                        # 1: a preset
    None,                                                         # 2: a folder
    (None, 0x0BADF00D, sample(1000, -LEVEL, stereo=True)),        # 3: stereo, 4 064 bytes
    (None, 0x77777777, sample(48, -LEVEL)),                       # 4: 161 bytes ... see below
    (160, 0x0A0A0A0B, sample(48, -LEVEL)[:160]),                  # 5: 160 bytes: preset size
    (None, 0x55555555, sample(5000, -LEVEL, rate=0)),             # 6: a header out of range (rate 0)
    (None, OWN_H, sample(10_000, LEVEL)),                         # 7: the track's own sample, level +
]
FILES[4] = (161, FILES[4][1], FILES[4][2] + b"\0")                # a header and 96 bytes of audio, one byte more
FILES = [f if f is None else (f[0] if f[0] is not None else len(f[2]), f[1], f[2]) for f in FILES]


def ino(i):
    return 0x100 + i


def sound(machine, name, seed, key=None):
    """A sound of 100 bytes (name at +4, machine at +38); for SAMPLE: key = (inode, id) at +70..+75, k 32 (+84) 0."""
    s = bytearray((seed + 3 * i) & 0x3f for i in range(100))
    s[0:4] = bytes(4)
    s[4:20] = name.ljust(16, b"\0")[:16]
    s[38] = machine
    if key is not None:
        struct.pack_into(">HHH", s, 70, key[0], key[1] >> 16, key[1] & 0xffff)
        s[84:86] = bytes(2)
    s[96:100] = bytes(4)
    return bytes(s)


def own_sound(smp):
    """The SAMPLE track's sound: SAMPLE naming the track's own sample (file 7)."""
    return sound(smp, b"OWN SAMPLE", 0x09, key=(ino(7), OWN_H))


def named(snd, inode, h):
    return snd[:70] + struct.pack(">HHH", inode, h >> 16, h & 0xffff) + snd[76:]


class Rig:
    """The browser, the note played live, SAMPLE's tick and the voice loop, on one image."""

    def __init__(self, img, smp, runtime=None, tweak=None):
        self.smp = smp
        e = self.e = TC.engine(img, runtime, tweak)
        uc = self.uc = e.uc
        uc.mem_map(0x40800000, 0x01800000)          # the OS's BSS (the browser, the notes, the file system)
        uc.mem_map(0x42400000, 0x00c00000)          # the rest of the SDRAM below the payload (test_model_tg.engine)
        uc.mem_map(FIX, 0x02000000)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        self.heap, self.errors = HEAP, []
        self.calls = defaultdict(list)
        self.posted = []
        self.post_real = False                       # the post (0x4005894a) runs: the note goes into the audio queue
        self.rank1 = False                           # the next note sent into it gets the sequencer's rank
        self.fs_busy = False                         # SAMPLE's view of the drive: this task holds the lock
        for addr, fn in {0x400802e0: self._new, 0x400802ec: lambda a: 0, 0x40001cc4: lambda a: 0,
                         0x40001df6: lambda a: 0, 0x4007e764: self._inode, 0x4007e68c: lambda a: 0,
                         OPEN: self._open, 0x4004067c: lambda a: 0, 0x40001fba: lambda a: 0,
                         0x40056178: self._pos, 0x40080bf6: lambda a: 0, 0x4008a5d0: lambda a: MIDI,
                         READ: self._read, SND_PARSE: self._parse, PARSE: lambda a: None,
                         FS_ENTRY: self._entry, FS_READ: self._fsread, POST: self._post,
                         GETTER: lambda a: 0x5a}.items():
            self.stub(addr, fn)
        w = self.w32
        w(0x40fde8f8, POOL3)                         # the event messages' pool (test_arp.Audio)
        self.call(0x40091d94, 0x42)
        w(KITP, KIT)
        w(KITP + 4, KIT + 628)
        w(CUR_KIT, KIT)
        self.own = own_sound(smp)
        self.sounds = [sound(0, b"Kick", 0x01), sound(2, b"Metal", 0x05), self.own, sound(1, b"Snare", 0x0d),
                       sound(4, b"Tone", 0x11), sound(0, b"Kick 2", 0x15)]
        for t in range(6):
            uc.mem_write(KIT + 28 + 100 * t, self.sounds[t])
            w(0x800015a0 + (153 + t) * 4, KIT)
            w(CUR_SNDS + 4 * t, KIT + 28 + 100 * t)
        w(0x40149310, 120 * 120)
        self.now = 1_000_000
        w(0x40a7887c, BANK)                          # the note: the pattern, the tracks' default flags (0x40061438)
        for t in range(6):
            uc.mem_write(BANK + 722 * t + 710, struct.pack(">H", 0x680))
        uc.mem_write(0x40fb680c, b"\xff" * 4 * 128 * 6)
        w(UIS_PTR, UIST)
        w(PROJ_PTR, PROJ)                            # the project: track t's object -> vtable[40] -> its sound
        for t in range(6):
            vt = TRKVT + 0x40 * t
            w(PROJ + 212 + 68 * t, vt)
            w(vt + 40, vt + 0x30)
            uc.mem_write(vt + 0x30, b"\x20\x3c" + struct.pack(">I", KIT + 28 + 100 * t) + b"\x4e\x75")
        w(ACTIVE, TRACK)
        w(MOUNTED, 1)
        w(FS_LOCK, 0)
        w(RUNNING, TASK)
        uc.mem_write(PM, bytes(0x400))               # the browser in file mode (test_sample_preview.Rig)
        uc.mem_write(PMVT, bytes(uc.mem_read(0x401183ec, 0x100)))
        w(PMVT + 12, 0x400a311e)
        w(PM, PMVT)
        uc.mem_write(FSD, bytes(0x200))
        w(FSD, 0x40112818)
        vec = FSD + 0x180
        for i in range(len(FILES)):
            w(vec + 8 * i, ENT + 16 * i)
            w(ENT + 16 * i, ino(i))
        w(FSD + 260, vec)
        w(FSD + 264, vec + 8 * len(FILES))
        w(SPD, 0x40117a44)
        w(PM + 640, FSD)
        w(PM + 688, SPD)
        w(PM + 632, FSD)
        w(PM + 664, TRACK)                           # the track the browser works for
        for t in range(6):
            e.set(t, machine=0, note=60, pitch=64, decay=127)
        e.set(TRACK, machine=smp, note=60, pitch=64, finetune=64, color=0, shape=120, sweep=64, contour=0, punch=0,
              gate=0, decay=127)

    # -- memory and calls --
    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def mem(self, a, n):
        return bytes(self.uc.mem_read(a, n))

    def stub(self, addr, fn):
        """fn(args) -> the value returned in d0, or None: the real code runs (the call is only noted)."""
        def hook(uc, a, size, ud):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">6I", uc.mem_read(sp + 4, 24))
            self.calls[addr].append(args)
            r = fn(args)
            if r is None:
                return
            uc.reg_write(mk.UC_M68K_REG_D0, r & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        self.uc.hook_add(UC_HOOK_CODE, hook, begin=addr, end=addr)

    def call(self, fn, *args, sr=0x2700, regs=False):
        uc = self.uc
        uc.reg_write(mk.UC_M68K_REG_SR, sr)
        frame = struct.pack(">I", STOP) + b"".join(struct.pack(">I", a & 0xffffffff) for a in args)
        uc.mem_write(CALL_SP - STACK_POISON, b"\xa5" * (STACK_POISON - len(frame)))
        uc.mem_write(CALL_SP - len(frame), frame)
        uc.reg_write(mk.UC_M68K_REG_A7, CALL_SP - len(frame))
        if regs:
            for r, val in zip(CALLEE, CALLEE_VALS):
                uc.reg_write(r, val)
        try:
            uc.emu_start(fn, STOP, count=20_000_000)
        except UcError as ex:
            self.errors.append((hex(fn), hex(uc.reg_read(mk.UC_M68K_REG_PC)), str(ex)))
        if uc.reg_read(mk.UC_M68K_REG_PC) != STOP:
            self.errors.append((hex(fn), hex(uc.reg_read(mk.UC_M68K_REG_PC)), "did not return"))
        self.regs_after = [uc.reg_read(r) for r in CALLEE]
        self.d0 = uc.reg_read(mk.UC_M68K_REG_D0)
        return self.d0

    def clean(self):
        return not self.errors and not self.e.unmapped

    def n(self, addr):
        return len(self.calls[addr])

    # -- stand-ins --
    def _new(self, a):
        p, n = self.heap, (a[0] + 15) & ~15
        self.heap += n
        self.uc.mem_write(p, bytes(n))
        return p

    def _inode(self, a):
        i = a[0] - 0x100
        if not 0 <= i < len(FILES):
            return 0
        rec = INODE + 0x80 * i
        self.uc.mem_write(rec, bytes(0x80))
        size, h = (FILES[i][0], FILES[i][1]) if FILES[i] else (0, 0x22222223 + i)
        self.w32(rec, 0x01000001 if FILES[i] is None else 0x00020001)
        self.w32(rec + 4, size)
        self.w32(rec + 12, h)
        self.w32(rec + 16, 0x1234)
        return rec

    def _open(self, a):
        iid = self.r32(a[0])
        self.w32(a[1], iid)
        return 1 if 0 <= iid - 0x100 < len(FILES) else 0xffffffff

    def _read(self, a):
        """Preset sizes: the content is not emulated (PRESET_H reads, the others do not); otherwise the real code
        (it refuses the size)."""
        size, h = self.r32(a[1] + 8), self.r32(a[1] + 4)
        if not 48 <= size <= 160:
            return None
        return 0 if h == PRESET_H else 0xffffffff

    def _parse(self, a):
        self.uc.mem_write(a[0], sound(4, b"Tone preset", 0x21))
        return 1

    def _pos(self, a):
        self.uc.mem_write(a[2], bytes([a[0] // 1000 % 64, a[1] + 1, 0]))
        return 0

    def _post(self, a):
        self.posted.append(self.mem(a[0], 56))
        return None if self.post_real else 0

    def _send(self, a):                               # 0x40092116(message): a sequencer's note gets rank 1 at +12
        if self.rank1:
            self.w32(a[0] + 12, 1)

    def run(self):
        """One pass of the audio interrupt's event loop (test_sample_preview.Rig.run): the mask of the tracks it
        triggers, or None."""
        uc = self.uc
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_write(FRAME - 168, bytes(168))
        self.w32(FRAME - 80, self.now)
        self.w32(0x8000184c, self.now)
        sp = FRAME - 168 - 0x100
        uc.mem_write(sp, bytes(8))
        for reg, val in ((mk.UC_M68K_REG_A6, FRAME), (mk.UC_M68K_REG_A7, sp), (mk.UC_M68K_REG_D2, 0),
                         (mk.UC_M68K_REG_D5, 0), (mk.UC_M68K_REG_D6, 0)):
            uc.reg_write(reg, val)
        try:
            uc.emu_start(EV_LOOP, EV_END, count=2_000_000)
        except UcError as ex:
            self.errors.append((hex(EV_LOOP), hex(uc.reg_read(mk.UC_M68K_REG_PC)), str(ex)))
            return None
        if uc.reg_read(mk.UC_M68K_REG_PC) != EV_END:
            self.errors.append((hex(EV_LOOP), hex(uc.reg_read(mk.UC_M68K_REG_PC)), "did not reach the loop's end"))
            return None
        return uc.reg_read(mk.UC_M68K_REG_D4)

    def _file(self, inode):
        i = inode - 0x100
        return FILES[i] if 0 <= i < len(FILES) and FILES[i] and FILES[i][2] is not None else None

    def _entry(self, a):                              # FS_ENTRY(ino, h): {inode, id, size, word 16}
        f = self._file(a[0])
        if not f:
            return 0xffffffff
        self.uc.mem_write(a[1], struct.pack(">4I", a[0], f[1], f[0], 0x1234))
        return 0

    def _fsread(self, a):                             # FS_READ(buf, len, fh): fh = {inode, position, -, open}
        buf, n, fh = a[0], a[1], a[2]
        inode, pos = self.r32(fh), self.r32(fh + 4)
        f = self._file(inode)
        if not f:
            return 0xffffffff
        data = f[2][pos:pos + n]
        self.uc.mem_write(buf, data)
        self.w32(fh + 4, pos + len(data))
        return len(data)

    # -- the browser --
    def browse(self, cursor, regs=False):
        """The cursor on entry cursor: 0x400a64be (UI task, level 0). Returns what is marked."""
        self.w32(PM + 16, cursor)
        self.call(CURSOR, PM, 0, sr=0x2000, regs=regs)
        return self.r32(ARMED)

    def open_at(self, index):
        """0x400a63ac(browser, index), as the browser's opening calls it (0x400a6d12)."""
        return self.call(PREVIEW, PM, index, sr=0x2000) & 0xff

    # -- the note --
    def press(self, t, src=0x40):
        """0x4008171e(t, 60, 100, src, 0, -1, -1): the pad (or a TRIG key in CHROMATIC mode); the posted event."""
        self.posted.clear()
        self.w32(0x8000184c, self.now)
        self.call(NOTE_ON, t, 60, 100, src, 0, 0xffffffff, 0xffffffff, sr=0x2000)
        return self.posted[-1] if self.posted else None

    # -- the tick and the voice --
    def tick(self):
        return self.call(self.syms["smp_hook_tick"], VIEW, sr=0x2000)

    def play(self, snd, preview, blocks=24):
        """A note of the track's voice with sound snd: the audio side's copy of its 66 bytes (0x40058a0a), the note's
        sound 0 after a preview note (0x4005910e) or the kit's sound; the mean level after 8 blocks."""
        self.uc.mem_write(TARGETS + 66 * TRACK, snd[20:86])
        self.w32(CUR_SNDS + 4 * TRACK, 0 if preview else KIT + 28 + 100 * TRACK)
        x = self.e.render(blocks, trig_at=(1,), track=TRACK)
        return float(x[32 * 8:].mean())


def site_tests(key, stock, img, syms):
    for va, old, sym in ((PAD_ON, "4feffff07205", "smp_hook_pad_on"), (PAD_OFF, "4feffff47005", "smp_hook_pad_off"),
                         (KEY_ON, "4feffff07005", "smp_hook_key_on")):
        check(stock[va - BASE:va - BASE + 6].hex() == old
              and img[va - BASE:va - BASE + 6] == struct.pack(">HI", 0x4eb9, syms[sym]),
              f"{key}: {va:#x} {old} (lea, moveq) on the stock OS -> jsr {sym} ({syms[sym]:#x})")
    check(stock[SITE - BASE:SITE - BASE + 6].hex() == "4eb9400a3052"
          and img[SITE - BASE:SITE - BASE + 6] == struct.pack(">HI", 0x4eb9, syms["smp_hook_preview"])
          and stock[OPEN_SITE - BASE:OPEN_SITE - BASE + 6].hex() == "4eb9400a3052"
          and img[OPEN_SITE - BASE:OPEN_SITE - BASE + 6] != stock[OPEN_SITE - BASE:OPEN_SITE - BASE + 6],
          f"{key}: {SITE:#x} jsr 0x400a3052 on the stock OS -> jsr smp_hook_preview ({syms['smp_hook_preview']:#x}); "
          f"the open at {OPEN_SITE:#x} taken as before")


def browser_tests(key, stock, img, runtime, tweak, smp):
    def one(image, rt, tw, cursor, track=TRACK, busy=False):
        r = Rig(image, smp, rt, tw)
        r.w32(PM + 664, track)
        r.w32(ACTIVE, track)
        if busy:
            r.w32(FS_LOCK, TASK)
        r.w32(ARMED, 0)
        armed = r.browse(cursor, regs=True)
        content = r.mem(armed, 100) if armed else None
        return dict(armed=armed, content=content, opens=r.n(OPEN), presets=r.n(READ), parse=r.n(PARSE),
                    fsreads=[(a[1],) for a in r.calls[FS_READ]], regs=r.regs_after == CALLEE_VALS,
                    clean=r.clean(), errors=r.errors[:2])
    own = own_sound(smp)
    for cursor, desc in ((0, "a mono sample of 600 064 bytes"), (3, "a stereo sample"), (4, "a sample of 161 bytes")):
        a, b = one(stock, None, None, cursor), one(img, runtime, tweak, cursor)
        size, h, _d = FILES[cursor]
        check(a["armed"] == 0 and a["parse"] == 1 and a["clean"] and a["regs"],
              f"{key}: stock OS, SAMPLE track, {desc}: read as a preset (0x400a3052), refused, nothing marked"
              + ("" if a["clean"] else f"; {a['errors']}"))
        check(b["armed"] in BUFS and b["content"] == named(own, ino(cursor), h) and b["opens"] == 0
              and b["presets"] == 0 and b["parse"] == 0 and b["fsreads"] == [(64,)] and b["regs"] and b["clean"],
              f"{key}: SAMPLE, {desc}: an OS buffer marked with the track's sound naming the file (inode "
              f"{ino(cursor):#x}, id {h:#010x}), every other byte the track's; the file neither opened nor read by "
              f"the OS, its 64-byte header read once; d2..d7/a2..a6 kept"
              + ("" if b["clean"] else f"; {b['errors']}"))
    same = [(1, TRACK, False, "a preset (120 bytes)"), (5, TRACK, False, "a file of 160 bytes (preset size)"),
            (6, TRACK, False, "a sample file whose header is out of range"),
            (0, TONE_TRACK, False, "a sample file on a TONE track"),
            (0, TRACK, True, "a sample file while this task holds the file system's lock")]
    for cursor, track, busy, desc in same:
        a, b = one(stock, None, None, cursor, track, busy), one(img, runtime, tweak, cursor, track, busy)
        keys = ("armed", "content", "opens", "presets", "parse", "regs")
        check(all(a[k] == b[k] for k in keys) and a["clean"] and b["clean"],
              f"{key}: {desc}: as on the stock OS (marked: {'a buffer' if a['armed'] else 'nothing'}, the file "
              f"{'opened' if a['opens'] else 'not opened'})" + ("" if all(a[k] == b[k] for k in keys) else
                                                                 f"; DIFFERENT {[k for k in keys if a[k] != b[k]]}"))
    seq = {}
    for name, image, rt, tw in (("stock", stock, None, None), ("SAMPLE", img, runtime, tweak)):
        r = Rig(image, smp, rt, tw)
        r.w32(ARMED, 0)
        a1 = r.browse(0)
        c1 = r.mem(a1, 100) if a1 else None
        a2 = r.browse(3)
        c2 = r.mem(a2, 100) if a2 else None
        n_read, n_parse = r.n(READ), r.n(SND_PARSE)
        a3 = r.browse(1)
        seq[name] = dict(a1=a1, c1=c1, a2=a2, c2=c2, a3=a3, c3=r.mem(a3, 100) if a3 else None,
                         reads=r.n(READ) - n_read, parses=r.n(SND_PARSE) - n_parse, clean=r.clean())
    o, m = seq["stock"], seq["SAMPLE"]
    check({m["a1"], m["a2"]} == set(BUFS) and m["c1"] == named(own, ino(0), FILES[0][1])
          and m["c2"] == named(own, ino(3), FILES[3][1]) and m["clean"],
          f"{key}: sample -> stereo sample: the buffers take turns ({m['a1']:#x}, {m['a2']:#x}), each with its file")
    check(m["a3"] == o["a3"] and m["c3"] == o["c3"] and (m["reads"], m["parses"]) == (o["reads"], o["parses"])
          and o["clean"] and m["clean"],
          f"{key}: then a preset (120 bytes): as on the stock OS (marked {o['a3']:#x}; the preset's file read "
          f"{o['reads']} time(s), decoded {o['parses']} time(s) on this bench)")
    r.w32(ARMED, 0)
    ok = r.open_at(0)
    marked = r.r32(ARMED)
    check(ok == 1 and marked in BUFS and r.mem(marked, 100) == named(own, ino(0), FILES[0][1]) and r.clean(),
          f"{key}: 0x400a63ac as the browser's opening calls it (0x400a6d12), on a sample file: true, the buffer "
          "marked with the file")


def note_tests(key, img, runtime, tweak, smp):
    r = Rig(img, smp, runtime, tweak)
    armed = r.browse(0)
    ev = r.press(TRACK)
    other = r.press(0)
    check(armed in BUFS and ev is not None and struct.unpack_from(">I", ev, 52)[0] == armed
          and other is not None and struct.unpack_from(">I", other, 52)[0] == 0 and r.clean(),
          f"{key}: the pad of the active SAMPLE track (source 0x40, the TRIG keys' too) posts the marked buffer "
          f"({armed:#x}) at +52 of its event; track 1's note carries nothing" + ("" if r.clean() else f"; {r.errors[:2]}"))


def tick_tests(key, img, runtime, tweak, smp, syms):
    r = Rig(img, smp, runtime, tweak)
    r.syms = syms
    r.w32(ARMED, 0)
    got = [r.tick() for _ in range(3)]
    own = r.play(r.own, False)
    check(all(g == 0x5a for g in got) and own > 1e6 and r.clean(),
          f"{key}: the tick returns the getter's answer; the track's own sample loads and plays (level {own:.3g})"
          + ("" if r.clean() else f"; {r.errors[:2]}"))
    armed = r.browse(0)
    snd = r.mem(armed, 100)
    r.tick()
    early = r.play(snd, True)
    levels, n = [], 1
    while n < 12:
        r.tick()
        n += 1
        x = r.play(snd, True)
        levels.append(x)
        if x < -1e6:
            break
    own2 = r.play(r.own, False)
    check(early == 0 and n == 6 and levels[-1] < -1e6 and all(v == 0 for v in levels[:-1]) and own2 > 1e6
          and r.clean(),
          f"{key}: the marked file (600 064 bytes) silent on a preview note until it is all read: it plays after "
          f"{n} ticks (one for its header, five of 128 KiB; level {levels[-1]:.3g}); a normal note then plays the "
          f"track's own (level {own2:.3g})")
    r.call(MARK, 0, sr=0x2000)                         # the browser closes (0x400a40e4): nothing marked
    for _ in range(2):
        r.tick()
    gone = r.play(snd, True)
    reads = r.n(FS_READ)
    r.browse(0)
    r.tick()
    again_early = r.play(snd, True)
    for _ in range(5):
        r.tick()
    again = r.play(snd, True)
    check(gone == 0 and again_early == 0 and again < -1e6 and r.n(FS_READ) - reads == 1 + 1 + 5 and r.clean(),
          f"{key}: nothing marked and no voice on it: freed (a preview note with the old buffer is silent); marked "
          "again, it is read again (its header twice, once by the cursor and once by the tick, and five reads) "
          "and plays")
    # the cursor moving on before the file is complete
    r.play(r.own, False)                               # the voice back on the track's own sample
    r.call(MARK, 0, sr=0x2000)
    r.tick()                                           # the first file freed
    r.browse(0)
    r.tick()                                           # its header
    r.tick()                                           # its first 128 KiB
    nxt = r.browse(3)
    snd3 = r.mem(nxt, 100)
    for _ in range(3):
        r.tick()
    played0, played3 = r.play(snd, True), r.play(snd3, True)
    check(played3 < -1e6 and played0 == 0 and r.clean(),
          f"{key}: the cursor moving on while a file loads: the first is dropped (silent), the next one (stereo, "
          f"4 064 bytes) loads and plays (level {played3:.3g})")
    # a marked preset of another machine (TONE), as the OS marks one (0x400a647c): nothing for the tick to load
    tone = sound(4, b"Tone preset", 0x21, key=(ino(4), FILES[4][1]))   # k 25..27 as a key to a file not loaded
    r.uc.mem_write(BUFS[0], tone)
    r.w32(ARMED, BUFS[0])
    e0, f0 = r.n(FS_ENTRY), r.n(FS_READ)
    for _ in range(3):
        r.tick()
    check(r.n(FS_ENTRY) == e0 and r.n(FS_READ) == f0 and r.clean(),
          f"{key}: a marked preset of another machine (TONE, its k 25..27 like a key): the tick asks nothing of the "
          "file system")


def pad_rig(img, smp, runtime, tweak, syms):
    """A rig whose pads' note functions run from their entry (SAMPLE's hooks first): the note-off and what both ask
    of the project after the note stood in for ("nothing more to do"), the track's own sample in and the 600 064-byte
    file marked and in."""
    r = Rig(img, smp, runtime, tweak)
    r.syms = syms
    for addr in PAD_AFTER + (NOTE_OFF,):
        r.stub(addr, lambda a: 0)
    for _ in range(3):
        r.tick()
    armed = r.browse(0)
    for _ in range(7):
        r.tick()
    return r, armed


def seq_note(r, snd_at, blocks=24, trig=True):
    """A note of the track's voice from the sequencer with the sound at snd_at (the kit's track sound or a lock's):
    the audio side's copy and the note's sound as the event loop leaves them (0x40058a0a); the mean level after 8
    blocks (or of the blocks, without a trig)."""
    if trig:
        r.uc.mem_write(TARGETS + 66 * TRACK, r.mem(snd_at, 100)[20:86])
        r.w32(CUR_SNDS + 4 * TRACK, snd_at)
    x = r.e.render(blocks, trig_at=(1,) if trig else (), track=TRACK)
    return float(x[32 * 8:].mean()) if trig else x


def pad_tests(key, img, runtime, tweak, smp, syms):
    r, armed = pad_rig(img, smp, runtime, tweak, syms)
    kit_snd = KIT + 28 + 100 * TRACK
    lock_snd = KIT + 694 + 100 * 5
    r.uc.mem_write(lock_snd, own_sound(smp))            # a lock's sound naming the track's own sample (level +)
    before = seq_note(r, kit_snd)
    r.posted.clear()
    r.call(PAD_ON, PADVIEW, TRACK, 60, 100, 0xffffffff, sr=0x2000)
    ev = r.posted[-1] if r.posted else None
    held = seq_note(r, kit_snd)
    locked = seq_note(r, lock_snd)
    check(before > 1e6 and ev is not None and struct.unpack_from(">I", ev, 52)[0] == armed and held < -1e6
          and locked > 1e6 and r.clean(),
          f"{key}: the real pad note function (0x4001d05e, SAMPLE's hook first): its note carries the mark; with the pad "
          f"held a trig of the track's own sound plays the marked sample (level {held:.3g}, before {before:.3g}), a "
          f"lock's sound its own ({locked:.3g})" + ("" if r.clean() else f"; {r.errors[:2]}"))
    seq_note(r, kit_snd, blocks=12)
    r.call(PAD_OFF, PADVIEW, TRACK, 60, sr=0x2000)
    x = seq_note(r, kit_snd, blocks=12, trig=False)
    blocks = [float(x[32 * b:32 * b + 32].mean()) for b in range(12)]
    after = seq_note(r, kit_snd)
    check(blocks[0] < 0 and all(v > 1e6 for v in blocks[2:]) and after > 1e6 and r.clean(),
          f"{key}: the real pad off (0x4001d0fc): the note that plays the marked sample goes on in the track's own "
          f"without a trig (block means {blocks[0]:.3g}, {blocks[1]:.3g}, then {blocks[2]:.3g}); the next trig plays "
          f"the track's own ({after:.3g})")
    r.call(PAD_ON, PADVIEW, TRACK, 60, 100, 0xffffffff, sr=0x2000)
    seq_note(r, kit_snd, blocks=12)
    r.call(MARK, 0, sr=0x2000)                          # the browser closes, the pad still held
    x = seq_note(r, kit_snd, blocks=12, trig=False)
    blocks = [float(x[32 * b:32 * b + 32].mean()) for b in range(12)]
    check(all(v > 1e6 for v in blocks[2:]) and r.clean(),
          f"{key}: the pad held and the browser closed (0x40081bd6(0)): back to the track's own, as when the pad is "
          f"let go ({blocks[2]:.3g})")


def engine_rig(img, smp, runtime, tweak, syms, marked=True, recording=False):
    """A rig whose notes go into the audio side's queue for real (the post 0x4005894a and the note-off 0x4008145e run,
    their calls noted), its event loop run by run(), page 0 mapped (the stock loop reads *(0 + 96) after a preview note,
    0x40059160); the track's own sample in and, when marked, the 600 064-byte file marked and in. recording: the pads'
    note functions see a live recording (0x40016e90 true) and call its start and end, stood in for."""
    r = Rig(img, smp, runtime, tweak)
    r.syms = syms
    r.uc.mem_map(0, 0x1000)
    r.post_real = True
    for addr, fn in ((0x4000f208, lambda a: 0), (0x4000cfcc, lambda a: 0), (0x40016e90, lambda a: 1 if recording else 0),
                     (REC_ASK[0], lambda a: 0), (REC_ASK[1], lambda a: 0), (REC_START, lambda a: 0),
                     (REC_END, lambda a: 0), (NOTE_OFF, lambda a: None), (QSEND, r._send),
                     (KEY_ASK[0], lambda a: 0), (KEY_ASK[1], lambda a: 0), (KEY_ASK[2], lambda a: 0)):
        r.stub(addr, fn)
    for _ in range(3):
        r.tick()
    armed = r.browse(0) if marked else 0
    for _ in range(7):
        r.tick()
    return r, armed


def seq_post(r, ev):
    """A sequencer's note on the track: the pad's event as posted (track, note, velocity, flags) without a sound, sent
    with the sequencer's rank 1 (what its builder writes at +12, 0x40054b7e) instead of the live notes' 2."""
    e = bytearray(ev)
    struct.pack_into(">I", e, 52, 0)
    r.uc.mem_write(EVT, bytes(e))
    r.rank1 = True
    r.call(POST, EVT, sr=0x2000)
    r.rank1 = False


def hx(v):
    return "None" if v is None else f"{v:#x}"


def engine_tests(key, img, runtime, tweak, smp, syms):
    t = TRACK
    # nothing marked: the OS's rule, the held pad's note holds its track and the sequencer's note is dropped
    r, _ = engine_rig(img, smp, runtime, tweak, syms, marked=False)
    r.posted.clear()
    r.call(PAD_ON, PADVIEW, t, 60, 100, 0xffffffff, sr=0x2000)
    ev = r.posted[0] if r.posted else None
    m_pad = r.run()
    rank = r.r32(RANK + 4 * t)
    if ev is not None:
        seq_post(r, ev)
    m_seq = r.run()
    check(ev is not None and r.n(NOTE_OFF) == 0 and m_pad is not None and m_pad >> t & 1 and rank == 2
          and m_seq is not None and not m_seq >> t & 1 and r.clean(),
          f"{key}: nothing marked, the audio side's own event loop (0x40058d46): the pad's note holds its track "
          f"(rank {rank}), a sequencer's note (rank 1) on it dropped (mask {hx(m_seq)}, the pad's {hx(m_pad)}), as on "
          f"the stock OS; no note-off from SAMPLE" + ("" if r.clean() else f"; {r.errors[:2]}"))
    # a sample marked: the pad's note-off at once, the track free, the sequencer's note plays the marked sample
    r, armed = engine_rig(img, smp, runtime, tweak, syms)
    r.posted.clear()
    r.call(PAD_ON, PADVIEW, t, 60, 100, 0xffffffff, sr=0x2000, regs=True)
    regs_ok = r.regs_after == CALLEE_VALS
    on = r.posted[0] if r.posted else None
    off = r.posted[1] if len(r.posted) > 1 else None
    offs = [c[:3] for c in r.calls[NOTE_OFF]]
    m_pad = r.run()
    rank, holds = r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t)
    check(on is not None and struct.unpack_from(">I", on, 52)[0] == armed and off is not None
          and struct.unpack_from(">2I", off, 0) == (t, 60) and struct.unpack_from(">I", off, 12)[0] == 2
          and offs == [(t, 60, 0x40)] and regs_ok and m_pad is not None and m_pad >> t & 1 and rank == 0
          and holds == 0xffffffff and r.clean(),
          f"{key}: a sample marked: the real 0x4001d05e posts the pad's note with the mark, then SAMPLE its note-off "
          f"(0x4008145e{offs[0] if offs else ''}, {len(offs)} call), d2..d7/a2..a6 kept; the loop starts the note and "
          f"frees the track (rank {rank}, note {hx(holds)})" + ("" if r.clean() else f"; {r.errors[:2]}"))
    if on is not None:
        seq_post(r, on)
    m_seq = r.run()
    held = float(r.e.render(24, trig_at=(1,), track=t)[32 * 8:].mean())
    rank = r.r32(RANK + 4 * t)
    check(m_seq is not None and m_seq >> t & 1 and rank == 1 and held < -1e6 and r.clean(),
          f"{key}: the pad held, a sequencer's note reaches the track (mask {hx(m_seq)}, rank {rank}) and plays the "
          f"marked sample (level {held:.3g})")
    before = (r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t))
    r.call(PAD_OFF, PADVIEW, t, 60, sr=0x2000)
    m_off = r.run()
    after = (r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t))
    x = r.e.render(12, trig_at=(), track=t)
    blocks = [float(x[32 * b:32 * b + 32].mean()) for b in range(12)]
    check(r.n(NOTE_OFF) == 2 and m_off is not None and not m_off >> t & 1 and before == after
          and all(v > 1e6 for v in blocks[2:]) and r.clean(),
          f"{key}: let go (the real 0x4001d0fc): its note-off dropped by the loop (rank and note {hx(after[0])}, "
          f"{hx(after[1])} kept), the note goes on in the track's own ({blocks[2]:.3g})")
    r, _ = engine_rig(img, smp, runtime, tweak, syms)
    r.call(PAD_ON, PADVIEW, t, 60, 100, 0xffffffff, sr=0x2000)
    r.run()
    before = (r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t))
    r.call(PAD_OFF, PADVIEW, t, 60, sr=0x2000)
    m_off = r.run()
    after = (r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t))
    check(r.n(NOTE_OFF) == 2 and m_off is not None and before == after == (0, 0xffffffff) and r.clean(),
          f"{key}: let go without a sequencer's note since: the second note-off dropped too (rank {hx(after[0])}, "
          f"note {hx(after[1])})")
    # a TRIG key in CHROMATIC mode (the real 0x40019e7a, SAMPLE's hook first): nothing marked, its note holds its track
    # as on the stock OS; a sample marked, its note-off at once, and a sequencer's note then plays the track's own sample
    r, _ = engine_rig(img, smp, runtime, tweak, syms, marked=False)
    r.posted.clear()
    r.call(KEY_ON, PADVIEW, t, 60, 100, 0xffffffff, sr=0x2000)
    ev = r.posted[0] if r.posted else None
    m_key = r.run()
    rank = r.r32(RANK + 4 * t)
    if ev is not None:
        seq_post(r, ev)
    m_seq = r.run()
    check(ev is not None and r.n(NOTE_OFF) == 0 and m_key is not None and m_key >> t & 1 and rank == 2
          and m_seq is not None and not m_seq >> t & 1 and r.clean(),
          f"{key}: nothing marked, a TRIG key (the real 0x40019e7a): its note holds its track (rank {rank}), a "
          f"sequencer's note dropped (mask {hx(m_seq)}), as on the stock OS; no note-off from SAMPLE"
          + ("" if r.clean() else f"; {r.errors[:2]}"))
    r, armed = engine_rig(img, smp, runtime, tweak, syms)
    r.posted.clear()
    r.call(KEY_ON, PADVIEW, t, 60, 100, 0xffffffff, sr=0x2000, regs=True)
    regs_ok = r.regs_after == CALLEE_VALS
    on = r.posted[0] if r.posted else None
    off = r.posted[1] if len(r.posted) > 1 else None
    offs = [c[:3] for c in r.calls[NOTE_OFF]]
    m_key = r.run()
    rank, holds = r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t)
    check(on is not None and struct.unpack_from(">I", on, 52)[0] == armed and off is not None
          and struct.unpack_from(">2I", off, 0) == (t, 60) and offs == [(t, 60, 0x40)] and regs_ok
          and m_key is not None and m_key >> t & 1 and rank == 0 and holds == 0xffffffff and r.clean(),
          f"{key}: a sample marked: the real 0x40019e7a posts the key's note with the mark, then SAMPLE its note-off "
          f"({len(offs)} call), registers kept; the loop starts the note and frees the track (rank {rank})"
          + ("" if r.clean() else f"; {r.errors[:2]}"))
    if on is not None:
        seq_post(r, on)
    m_seq = r.run()
    own = float(r.e.render(24, trig_at=(1,), track=t)[32 * 8:].mean())
    rank = r.r32(RANK + 4 * t)
    check(m_seq is not None and m_seq >> t & 1 and rank == 1 and own > 1e6 and r.clean(),
          f"{key}: the key held, a sequencer's note reaches the track (mask {hx(m_seq)}, rank {rank}) and plays the "
          f"track's own sample, not the marked one (level {own:.3g})")
    before = (r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t))
    r.call(KEY_OFF, PADVIEW, t, 60, sr=0x2000)
    m_off = r.run()
    after = (r.r32(RANK + 4 * t), r.r32(HOLDS + 4 * t))
    check(r.n(NOTE_OFF) == 2 and m_off is not None and not m_off >> t & 1 and before == after and r.clean(),
          f"{key}: the key let go (the real 0x40019c84): its note-off dropped by the loop (rank and note "
          f"{hx(after[0])}, {hx(after[1])} kept)")
    # a live recording: the press still starts the recorded note and only the release ends it
    r, _ = engine_rig(img, smp, runtime, tweak, syms, recording=True)
    r.call(PAD_ON, PADVIEW, t, 60, 100, 0xffffffff, sr=0x2000, regs=True)
    regs_ok = r.regs_after == CALLEE_VALS
    starts, ends, offs = r.n(REC_START), r.n(REC_END), r.n(NOTE_OFF)
    r.call(PAD_OFF, PADVIEW, t, 60, sr=0x2000)
    check(starts == 1 and ends == 0 and offs == 1 and regs_ok and r.n(REC_END) == 1 and r.n(NOTE_OFF) == 2
          and r.clean(),
          f"{key}: a live recording: the press starts the recorded note ({starts} call of 0x4008273c, the note-off at "
          f"once after it, registers kept), the release alone ends it ({r.n(REC_END)} call of 0x400827a8)"
          + ("" if r.clean() else f"; {r.errors[:2]}"))


def head_tweak():
    """SAMPLE 0.15 alone as the repository's last commit holds it (27-sampler.json at HEAD), or None."""
    try:
        out = subprocess.run(["git", "-C", str(HERE.parent.parent), "show", "HEAD:tweaks/model-cycles_OS1.13/27-sampler.json"],
                             capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def count_blocks(r, n):
    """Instructions run in the payload (the added machines' code) in each of n blocks of the track's note."""
    counts, cur = [], [0]

    def hk(uc, a, size, ud):
        cur[0] += 1
    h = r.uc.hook_add(UC_HOOK_CODE, hk, begin=PAYLOAD_LO, end=PAYLOAD_HI - 1)
    for b in range(n):
        cur[0] = 0
        r.e.block(1 << TRACK if b == 1 else 0)
        counts.append(cur[0])
    r.uc.hook_del(h)
    return counts


def cost_tests(stock, img, runtime, tweak, smp, syms):
    """Instructions a block of SAMPLE playing a note costs: One-Shot 0.15 (HEAD's 27-sampler.json) and 0.16 with
    nothing held, 0.16 with the pad held (the marked sample), and the block in which the pad is let go."""
    base = head_tweak()
    kit_snd = KIT + 28 + 100 * TRACK
    res = {}
    if base is not None and base.get("version") != tweak.get("version"):
        patched, _ = build.apply_writes(stock, [base])
        brt = build.payload_runtime(base, stock, None)
        bimg = bytes(patched) + build.payload_image(base, brt)
        r = Rig(bimg, smp, brt, base)
        r.syms = {k: int(v, 16) for k, v in base["symbols"].items()}
        for _ in range(3):
            r.tick()
        r.uc.mem_write(TARGETS + 66 * TRACK, r.mem(kit_snd, 100)[20:86])
        r.w32(CUR_SNDS + 4 * TRACK, kit_snd)
        res["0.15"] = count_blocks(r, 40)[3:]
    r, armed = pad_rig(img, smp, runtime, tweak, syms)
    r.uc.mem_write(TARGETS + 66 * TRACK, r.mem(kit_snd, 100)[20:86])
    r.w32(CUR_SNDS + 4 * TRACK, kit_snd)
    res["0.16"] = count_blocks(r, 40)[3:]
    r.call(PAD_ON, PADVIEW, TRACK, 60, 100, 0xffffffff, sr=0x2000)
    res["0.16, pad held"] = count_blocks(r, 40)[3:]
    r.call(PAD_OFF, PADVIEW, TRACK, 60, sr=0x2000)
    cur = [0]

    def hk(uc, a, size, ud):
        cur[0] += 1
    h = r.uc.hook_add(UC_HOOK_CODE, hk, begin=PAYLOAD_LO, end=PAYLOAD_HI - 1)
    r.e.block(0)
    r.uc.hook_del(h)
    res["0.16, the block it is let go"] = [cur[0]]
    line = "; ".join(f"{k}: mean {sum(v) / len(v):.0f}, max {max(v)}" for k, v in res.items())
    ok = r.clean() and all(v and min(v) > 0 for v in res.values())
    check(ok, "cost in the payload per block of SAMPLE playing a note (instructions, Unicorn): " + line
          + ("" if base is not None else "; 0.15 not measured (no git, or HEAD holds 0.16 already)"))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    for ids in SELECTIONS:
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        smp = next(m["index"] for m in TC.configure(ids) if m["code"] == "sampler")
        syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
        print(f"\n{key}: SAMPLE = machine {smp}")
        site_tests(key, stock, img, syms)
        print("the cursor")
        browser_tests(key, stock, img, runtime, tweak, smp)
        print("the note")
        note_tests(key, img, runtime, tweak, smp)
        print("the tick and the voice")
        tick_tests(key, img, runtime, tweak, smp, syms)
        print("the pad held")
        pad_tests(key, img, runtime, tweak, smp, syms)
        print("the pad held, through the audio side's event loop")
        engine_tests(key, img, runtime, tweak, smp, syms)
        if ids == ["sampler"]:
            print("the cost")
            cost_tests(stock, img, runtime, tweak, smp, syms)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
