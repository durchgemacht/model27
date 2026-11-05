#!/usr/bin/env python3
"""Proof of the machine shortcuts (notes/63 §3, step B4b) and of the switches (notes/63 §16, §17) on the OS's own code:
the shortcut layer that tools/compose.py adds to a build whose machines declare a shortcut (tools/machines/shortcuts/),
with REF2's MACHINES + COLOR = Octave, -2 to +2, MACHINES + PUNCH = Square and MACHINES + GATE = Tone open, and SAMPLE's
MACHINES + PUNCH = Loop and MACHINES + GATE = Reverse (since One-Shot 0.11, notes/63 §21). The key held is MACHINES
since the layer's 0.3 (the key map of 2026-10-31); RETRIG, the key up to 0.2, is among the cases that give the stock
answer.

For each selection (by default: refmachine2; sampler,refmachine2; refmachine2,sampler; sampler,refmachine,refmachine2),
on the official OS 1.13:
  1. the sites: the knob lookup's entry in ParameterPageView's vtable (0x401005a8) and the three sound record functions
     jump into the layer; with SAMPLE in the build, its record wrappers are the next of the chain and their own jumps
     are not written; jmp sc_press at 0x4001ac4a and jsr sc_leds at 0x4001cc86, REF2's and SAMPLE's bytes of presses 3
     (and in a build whose machines declare no switch, REFC's, both sites stock and every byte of presses 0);
  2. the knob, through the vtable entry and the OS's own key test: MACHINES held + COLOR on a REF2 track gives
     descriptor 1; every other knob, every other machine (stock, SAMPLE, REF, one the build does not have), MACHINES
     not held, or FUNC, TRACK, LFO or a trig held with it, give the stock lookup's answer; the stock lookup is called
     once each time with the same arguments, and the stack comes back;
  3. descriptor 1: k 28, -2..+2 as 8.8, default 0, no CC and no NRPN, "Octave" / "OCT", still machine -1, the rest
     of the table untouched; the OS's range getter (0x4005a65a) reads -2..+2 and its value setter (0x4000b274) clamps
     to it, signed; interface object 1, built by the OS's own constructor, shows -2..+2 as "-2".."2" (FMT_INT) without
     the "Error" picture;
  4. the tables built at boot (0x4005a274): the same with descriptor 1 installed as without (rows, k -> descriptor,
     CC, NRPN), so a shortcut value is no LFO destination, CC or NRPN;
  5. a sound saved (versions 2 and 1) and loaded: the record is the stock one plus k 28..31 in slots 28..31 and the
     switches, k 32, in slot 18, and the load gives them back with the rest as the stock load (k 0, where the stock
     load puts slot 18, at 0 as in the stock OS, whose save never writes slot 18); a record without them (the
     official OS's) loads k 28..32 at 0; a version 1 record is refused by the load as before, and the sound is left
     as it was; a SAMPLE sound keeps its key, as in SAMPLE's build alone;
  6. a real machine change into REF2 (0x40014072, through the wheel 0x400a2712) keeps k 28..31;
  7. the voice loop: REF2 at Octave +1 and note 48 plays note 60 at Octave 0, sample for sample, and so does -1 at
     note 72; +3 plays as +2; REF ignores k 28. The switches: Square, Tone open and both each sound different; they
     are read in the note's sound (CUR_SNDS[t] + 84) before the copy of its 66 bytes (0x800015ae + 66 t + 64); a
     switch flipped while a note plays acts from the next block; REF ignores k 32;
  8. the press (0x4001ac4a, called with the view and parameter 44 PUNCH or 45 GATE, as MainScreenView's key handler
     calls it): MACHINES held, TRACK not, on a REF2 or SAMPLE track flips bit 8 or 9 of k 32 in the track's sound, asks
     once for a new LED frame (0x400760ba with the view) and switches nothing (0x4001abe2 not called), when no trig is
     held (0x4006b736 asked once, since the layer's 0.5); every other case (no key, RETRIG, TRACK, TRACK + MACHINES,
     another machine, no project, no sound, another parameter) calls what the stock OS calls with the same arguments
     and leaves k 32; d2..d7 and a2..a6 and the stack come back. With a trig held (the layer's 0.5, notes/63 §27), on
     the OS's own lock functions (0x4001646a, 0x400164b0, 0x4000dece, 0x4000dcec) over a pattern in memory: the sound
     stays, each held step below the pattern's length gets its switch flipped as a lock of k 32 (bits 8/9 the values,
     10/11 the switches it holds), a switch flipped back to the sound's value leaves the lock, a lock that holds none is
     cleared, other steps and other k untouched; the stock knob lock's bracket around the writes (0x4006b740 sets +356,
     0x4006b954 clears the step words), one LED frame, the hold marked. With a step held, the step keys' handler
     (0x40022382) takes PUNCH and GATE before MainScreenView (the stock p-lock of PUNCH or GATE, 0x40022eac): run from
     its entry, stock and with the layer (jmp sc_steplock, notes/63 §29), for a machine with switches and a stock one,
     no key, MACHINES, MACHINES + TRACK, PUNCH and GATE: with MACHINES alone on the switches' machine the switch locked
     on the held steps and the press taken; every other case on to the stock lock (0x40022ebc); not a fresh press:
     taken, nothing locked; no step held: the press not taken, 0x40022eac not reached;
  9. the LEDs: MainScreenView's LED method from 0x4001cc80 to its second LED (0x4001ccc2), with PUNCH and GATE of the
     selected track in d2 and d0: MACHINES held, TRACK not, on a REF2 or SAMPLE track, LED 19 and 20 show the switches
     (state 2 on, 1 off); every other case lights them as the stock OS; d5 leaves as the stock code leaves it there, the
     other registers kept; with a trig held (0.5), the first held step's switches: a locked switch the lock's value, the
     other the sound's. With a trig held, PatternGridView's LED method (0x40021d22) lights PUNCH's and GATE's LEDs after
     MainScreenView's, from bits 1 and 2 of a byte of its frame (a held step with a p-lock of PUNCH or GATE): from
     0x40022110 to after its loop over the LEDs 0x12, 0x13, 0x14, 0x15, 0x1b (0x40022156), stock and with the layer
     (jsr sc_gridleds at 0x40022112, notes/63 §30): MACHINES held, TRACK not, on a track of a machine with switches,
     bits 1 and 2 the first held step's switches, the other bits and LEDs as they were; every other case as the stock
     OS; 0x400cfc5e called once with the method's object, registers and the frame kept.
  10. MACHINES as the level's key (the layer's 0.4): MainScreenView's key handler from its MACHINES case (0x4001c252),
     stock and with the layer, for every machine, the MACHINES list open or not, a shortcut or switch used in between or
     not: on a track of a machine with a shortcut or a switch a press that would open the list is taken and the release
     opens it unless something acted; a press with the list open closes it at once; FUNC + MACHINES goes to the PRESET
     browser; a held trig too, but on a track of a machine with a switch (the layer's 0.5, jmp sc_mtrig at 0x4001c274)
     the press is taken and the release opens the browser through the handler's own path unless a switch acted (then
     the event passes on), and asks once for a new LED frame (0x400760ba with the view), so that PUNCH's and GATE's
     LEDs show the held step's switches at once; every other machine as the stock OS; registers and stack kept; a
     switch flipped and a shortcut turned mark the hold, a knob turned without MACHINES does not.
  11. the pattern's p-lock rows (the layer's 0.5, notes/63 §25; the filter slot's fix up to its 0.10): 0x4005aa34 ->
     jmp sc_conv and the operands 0x4005b998, 0x4005baca -> sc_ptab in every build with the layer; 0x4005aa1a (track,
     index -> k) for tracks 0..6 and indices 0..40: index 18 -> k 32 and 24..32 -> k 23..31 on tracks 0..5, every other
     answer the stock OS's; a pattern with locks of stock parameters, of k 23..31 and of k 32 (the switches) saved
     whole (0x4005b95c) has k 32's row at index 18 and k 23..31's at 24..32, and loads (0x4005b766) every lock back on
     its k; one lock of k 32 updated (0x4005ba90) too; with locks of stock parameters only, the file byte for byte the
     stock OS's; the official OS loading the layer's file puts the rows of k 32 and of k 23..31 on k 0, which nothing
     reads (0x4005aa1a: index 18 through the table, 24..32 past it), and keeps every stock lock.
Not covered here: that the sound found through the project's track is the one in CUR_SNDS[t], that a MACHINES press and
release redraw the LEDs, and whether the project keeps a switch alone (notes/63 §17.2, §17.5: the device).

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_shortcuts.py --cycles model-cycles_OS1.13.syx [--machines sampler,refmachine2] [--blocks 60]
"""
import argparse
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_syntakt_machines as TS  # noqa: E402
from test_sdvintage_7th import check, fill_records, fake_track, SCRATCH  # noqa: E402

SELECTIONS = [["refmachine2"], ["sampler", "refmachine2"], ["refmachine2", "sampler"],
              ["sampler", "refmachine", "refmachine2"]]
KNOB_ENTRY, LOOKUP, KEY_HELD = 0x401005a8, 0x4001e814, 0x4007faf4
KEY_TABLE, KEY_BITS = 0x4010ae5c, 0x40f95744
TRACK_MACHINE, UI_STATE, TRIG_HELD = 0x4001e318, 0x400cf9a8, 0x4006b736
UI_OBJ, FMT_INT, RANGE, SET_VALUE, BUILDER = 0x40a71754, 0x400456c8, 0x4005a65a, 0x4000b274, 0x4005a274
FUNC, TRACK, RETRIG, MACHINES, LFO = 1, 2, 4, 5, 8
LAYER = MACHINES                    # the layer's key since 0.3 (the key map of 2026-10-31); RETRIG up to 0.2
SAVE2, SAVE1, LOAD = 0x4005afa0, 0x4005b054, 0x4005aecc
STOCK_HEAD = "4feffff448d71c00"
SOUND, RECORD, VIEW, OBJ = 0x91100000, 0x91200000, 0x90200000, 0x93700000
STOCK_ANSWER = 0x55                      # what the stubbed stock lookup returns
VALUES = (0x0100, 0xfe00, 0x1234, 0x7f00)  # k 28..31 of the test sounds: +1, -2, and two other words
# the switches (notes/63 §16)
PRESS, PRESS_BODY, SWITCH, VIEW_LEDS = 0x4001ac4a, 0x4001ac50, 0x4001abe2, 0x400760ba
LED_SITE, LED_FROM, LED_UNTIL, LED_SET, LED_COLOUR = 0x4001cc86, 0x4001cc80, 0x4001ccc2, 0x40005f86, 0x404a8cb8
PROJECT, PROJECT_TRACKS, ACTIVE_TRACK = 0x400cf866, 0x4000eb90, 0x40012412
PROJ, SEL, TRACK_VT, SOUND_FN, LEDS = 0x93a00000, 0x93a10000, 0x93b00000, 0x93b00100, 0x93c00000
PUNCH_P, GATE_P, K32, BIT = 44, 45, 84, {44: 0x100, 45: 0x200}
CUR_SNDS, TARGETS = 0x800017ec, 0x800015ae
SND, FLIP = 0x40781000, 20     # a sound in the engine's memory; the block a switch flips at
KEPT = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")]
# MACHINES as the level's key (the layer's 0.4): MainScreenView's MACHINES case, where it goes, the list's views
MACH_CASE, MACH_SITE, MACHINES_VT, CONTROLLER = 0x4001c252, 0x4001ca1e, 0x40117920, 0x93d00000
MACH_STOPS = {0x4001ca2a: "toggle", 0x4001c2a8: "taken", 0x4001c608: "pass", 0x4001c996: "browser"}
EVENT, PENDING, USED = 0x93d10000, 0x12, 0x13


class UI(t7.UI):
    """test_sdvintage_7th's UI with a heap for operator new (the interface objects' constructor), the stack checked
    after each call, and the OS's key bitmap."""

    def __init__(self, img, payload=b""):
        super().__init__(img, payload)
        self.heap, self.sp_ok = 0x93000000, False

    def _hook(self, uc, addr, size, ud):
        h = self.hooks.get(addr)
        if isinstance(h, tuple) and h[0] == "new":
            n = struct.unpack(">I", uc.mem_read(uc.reg_read(mk.UC_M68K_REG_A7) + 4, 4))[0]
            self.hooks[addr] = ("new", self.heap)
            self.heap = (self.heap + n + 15) & ~15
        super()._hook(uc, addr, size, ud)

    def call(self, fn, *args, count=20_000_000):
        d0 = super().call(fn, *args, count=count)
        self.sp_ok = self.uc.reg_read(mk.UC_M68K_REG_A7) == t7.STACK - 0x400 + 4
        return d0

    def cstr(self, a):
        return bytes(self.uc.mem_read(a, 64)).split(b"\0")[0].decode("latin-1")

    def hold(self, code, held):
        bit = struct.unpack(">i", self.uc.mem_read(KEY_TABLE + 4 * code, 4))[0]
        v = self.uc.mem_read(KEY_BITS + (bit >> 3), 1)[0]
        v = v | 1 << (bit & 7) if held else v & ~(1 << (bit & 7))
        self.uc.mem_write(KEY_BITS + (bit >> 3), bytes([v]))

    def keys(self, held):
        for c in (FUNC, TRACK, RETRIG, MACHINES, LFO):
            self.hold(c, c in held)


def s32(x):
    return struct.unpack(">i", struct.pack(">I", x & 0xffffffff))[0]


def knob(u, machine, knob_, trig=0):
    """The knob lookup through the vtable entry, the stock lookup and the track's machine stubbed: (descriptor,
    whether the stock lookup was called once with the same arguments, the stack came back and memory stayed in
    bounds)."""
    u.hooks = {LOOKUP: ("lookup", STOCK_ANSWER), TRACK_MACHINE: ("machine", machine & 0xffffffff),
               UI_STATE: ("ui", 0x93a00000), TRIG_HELD: ("trig", trig)}
    u.calls.clear()
    d = u.call(u.u32(KNOB_ENTRY), VIEW, knob_, 0, 0xffffffff)
    looked = [a[:4] for n, a in u.calls if n == "lookup"]
    return d, looked == [(VIEW, knob_, 0, 0xffffffff)] and u.sp_ok and not u.bad


# --- 2. the knob ----------------------------------------------------------------------------------------------------
def knob_tests(key, img, runtime, ref2, machines):
    u = UI(img, runtime)
    ok = True
    for c in (FUNC, TRACK, RETRIG, MACHINES, LFO):
        u.hold(c, True)
        ok &= u.call(KEY_HELD, c) == 1
        u.hold(c, False)
        ok &= u.call(KEY_HELD, c) == 0
    check(ok, f"{key}: the OS's key test (0x4007faf4) sees FUNC, TRACK, RETRIG, MACHINES and LFO held, then released")
    got, fwd = {}, True
    for held in ((), (LAYER,), (LAYER, FUNC), (LAYER, TRACK), (LAYER, LFO), (FUNC,), (LFO,), (RETRIG,)):
        u.keys(held)
        for trig in (0, 1):
            for m in machines:
                for k in range(16):
                    got[held, trig, m, k], ok_ = knob(u, m, k, trig)
                    fwd &= ok_
    u.keys(())
    want = {c: 1 if c[0] == (LAYER,) and not c[1] and c[2] == ref2 and c[3] == 4 else STOCK_ANSWER for c in got}
    bad = [c for c in got if got[c] != want[c]]
    check(not bad, f"{key}: descriptor 1 for MACHINES + COLOR on REF2 (machine {ref2}) only; the stock answer for the "
                   f"15 other knobs, machines {', '.join(str(s32(m)) for m in machines if m != ref2)}, no key, FUNC, "
                   f"TRACK, LFO or a trig held with MACHINES, and RETRIG alone ({len(got)} cases)"
                   + (f"; DIFFERENT {bad[:4]}" if bad else ""))
    check(fwd, f"{key}: the stock lookup called once per call with the same arguments; the stack comes back; no access "
               "outside memory")


# --- 3. descriptor 1, its range, its value and its display -----------------------------------------------------------
def descriptor_tests(key, img, runtime, ref2):
    u = UI(img, runtime)
    u.hooks = {0x400802e0: ("new", 0), 0x400cf044: ("atexit", 0)}
    u.call(0x400de244, count=50_000_000)             # the interface objects, as the OS builds them at boot
    built = not u.bad
    ndesc = 76 + 5 * TS.N
    table = lambda: [bytes(u.uc.mem_read(gs.DESCN + 0x38 * i, 0x38)) for i in range(ndesc)]
    before = table()
    u.hold(LAYER, True)
    d, ok = knob(u, ref2, 4)
    u.hold(LAYER, False)
    after = table()
    f, f0 = struct.unpack(">14i", after[1]), struct.unpack(">14i", before[1])
    names = (u.cstr(f[11] & 0xffffffff), u.cstr(f[13] & 0xffffffff))
    check(d == 1 and ok and f[0] == -1 and f[1:9] == (28, -512, 512, 0, 0, -1, -1, 0) and f[9:11] == f0[9:11]
          and f[12] == f0[12] and names == ("Octave", "OCT"),
          f"{key}: descriptor 1 installed: k 28, -2..+2 (8.8), default 0, no CC, no NRPN, {names[0]} / {names[1]}, "
          f"machine still -1, flags {f[9]:#x} and the rest as before")
    check(all(after[i] == before[i] for i in range(ndesc) if i != 1),
          f"{key}: the other {ndesc - 1} descriptors of the table the OS uses ({gs.DESCN:#x}) untouched")
    u.call(RANGE, 1)
    rng = struct.unpack(">3i", u.uc.mem_read(SCRATCH, 12))
    check(rng == (-512, 512, 0), f"{key}: the OS's range getter (0x4005a65a) reads descriptor 1 as {rng}")
    # the value setter, on a parameter object whose methods are stubs: it clamps, then hands the value on
    vt = OBJ + 0x100
    u.uc.mem_write(OBJ, struct.pack(">I", vt))
    for off in range(0, 0x80, 4):
        u.uc.mem_write(vt + off, struct.pack(">I", OBJ + 0x200 + off))
    tries, clamped = (-1000, -513, -512, -300, 0, 300, 512, 513, 1000), []
    for v in tries:
        u.hooks = {OBJ + 0x200 + 24: ("check", 1), OBJ + 0x200 + 92: ("set", 0), OBJ + 0x200 + 72: ("notify", 0),
                   OBJ + 0x200 + 28: ("get", 0)}
        u.calls.clear()
        u.call(SET_VALUE, OBJ, 1, v, 0, 0, 0)
        clamped.append([s32(a[2]) for n, a in u.calls if n == "set"])
    want = [[min(max(v, -512), 512)] for v in tries]
    check(clamped == want and not u.bad, f"{key}: the OS's value setter (0x4000b274) clamps to -2..+2, signed: "
                                         + ", ".join(f"{v} -> {c[0] if c else None}" for v, c in zip(tries, clamped)))
    obj = UI_OBJ + 100
    shown = []
    for v in range(-2, 3):
        u.uc.mem_write(SCRATCH + 0x100, bytes(32))
        u.call(u.u32(obj + 0x20), obj + 0x14, v << 8, SCRATCH + 0x100)
        shown.append(u.cstr(SCRATCH + 0x100))
    check(built and u.u32(obj + 0x20) == FMT_INT and u.u32(obj + 0x2c) == 0 and u.u32(obj + 0x1c) != 0
          and shown == ["-2", "-1", "0", "1", "2"],
          f"{key}: interface object 1 (built by the OS's constructor): FMT_INT, no 'Error' picture, shows {shown}")


# --- 4. the tables built at boot ------------------------------------------------------------------------------------
def maps(u):
    pid = [u.call(0x4005a692, k, m) for k in range(34) for m in range(TS.NM)]
    cc = [u.call(0x4005a8ce, t, m, c) for t in (0, 5) for m in range(TS.NM) for c in range(128)]
    nr = [u.call(0x4005a92e, 0, 0, n) for n in range(0x180)]
    return pid, cc, nr


def table_tests(key, img, runtime, ref2):
    a, b = UI(img, runtime), UI(img, runtime)
    b.hold(LAYER, True)
    knob(b, ref2, 4)                                 # descriptor 1 installed before the tables are built
    b.hold(LAYER, False)
    a.hooks, b.hooks = {}, {}
    a.call(BUILDER)
    b.call(BUILDER)
    lo, hi = t7.BSS_TABLES
    same = bytes(a.uc.mem_read(lo, hi - lo)) == bytes(b.uc.mem_read(lo, hi - lo))
    rows = all(bytes(a.uc.mem_read(r, TS.NM * 32)) == bytes(b.uc.mem_read(r, TS.NM * 32)) for r in (TS.ROWS, TS.CCROWS))
    check(same and rows and maps(a) == maps(b) and not a.bad and not b.bad,
          f"{key}: the tables built at boot (0x4005a274) identical with descriptor 1 installed: rows, CC rows, "
          f"k -> descriptor for {TS.NM} machines, CC, NRPN")


# --- 5. save and load -----------------------------------------------------------------------------------------------
def sound_bytes(rng, machine, values=VALUES):
    """A sound as the OS holds it: random where the save copies bytes, valid where it looks a table up. The LFO's
    destination (k 4's high byte, +28) and the velocity's (the long at +88) index 0x4010ee4c without a bound, as in
    test_track_filter.py's sound_bytes."""
    s = bytearray(rng.integers(0, 256, 100, dtype=np.uint8).tobytes())
    for k in range(33):
        struct.pack_into(">H", s, 20 + 2 * k, int(rng.integers(0, 0x7f01)))
    struct.pack_into(">H", s, 38, machine << 8)
    for k, v in zip(range(28, 32), values):
        struct.pack_into(">H", s, 20 + 2 * k, v)
    struct.pack_into(">H", s, 28, 13 << 8)          # LFO -> SWEEP
    struct.pack_into(">I", s, 88, 17)               # velocity -> FINE
    struct.pack_into(">H", s, 92, 0x3000)
    struct.pack_into(">I", s, 96, 0x40)
    return bytes(s)


def save_load(u, sound, fn):
    u.uc.mem_write(SOUND, sound)
    u.uc.mem_write(RECORD, b"\xee" * 100)
    r1 = u.call(fn, RECORD, SOUND) & 0xff
    rec = bytes(u.uc.mem_read(RECORD, 100))
    u.uc.mem_write(SOUND, b"\xcc" * 100)
    r2 = u.call(LOAD, SOUND, RECORD) & 0xff
    return r1, rec, r2, bytes(u.uc.mem_read(SOUND, 100))


def save_tests(key, stock, img, runtime, ref2, smp, alone):
    rng = np.random.default_rng(63)
    a, b = UI(stock), UI(img, runtime)
    for fn, ver in ((SAVE2, 2), (SAVE1, 1)):
        snd = sound_bytes(rng, ref2)
        ra, reca, la, backa = save_load(a, snd, fn)
        rb, recb, lb, backb = save_load(b, snd, fn)
        diff = [i for i in range(100) if reca[i] != recb[i]]
        check(ra == rb == 1 and set(diff) <= set(range(84, 92)) | {64, 65} and recb[84:92] == snd[76:84]
              and recb[64:66] == snd[84:86] and reca[64:66] == bytes(2) and b.sp_ok and not b.bad,
              f"{key}: save version {ver} of a REF2 sound: the stock record (slot 18 at 0) plus k 28..31 in slots "
              f"28..31 and k 32 = {snd[84:86].hex()} in slot 18 (bytes {diff})")
        if ver == 2:
            check(la == lb == 1 and backb[76:86] == snd[76:86] and backb[:76] == backa[:76] and backb[86:] == backa[86:]
                  and backa[20:22] == backb[20:22] == bytes(2) and backa[84:86] == bytes(2),
                  f"{key}: loaded: k 28..31 back (+1, -2, 0x1234, 0x7f00) and k 32 ({snd[84:86].hex()}); k 0 at 0 as "
                  "the stock load leaves it; everything else as the stock load")
        else:
            check(la == lb == 0 and backb == backa == b"\xcc" * 100,
                  f"{key}: a version 1 record: the load refuses it as before and the sound stays as it was")
    snd = sound_bytes(rng, ref2)
    _, reca, _, _ = save_load(a, snd, SAVE2)        # a record from the official OS: slots 28..31 at 0
    b.uc.mem_write(RECORD, reca)
    b.uc.mem_write(SOUND, b"\xcc" * 100)
    b.call(LOAD, SOUND, RECORD)
    old = bytes(b.uc.mem_read(SOUND, 100))
    check(old[76:86] == bytes(10) and reca[84:92] == bytes(8) and reca[64:66] == bytes(2),
          f"{key}: a record saved by the official OS loads k 28..31 and k 32 at 0, the shortcuts' and switches' default")
    if smp is None:
        return
    # a SAMPLE sound: the key through SAMPLE's wrappers, behind the layer, as in SAMPLE's build alone
    s, (img_s, runtime_s) = UI(img, runtime), alone
    c = UI(img_s, runtime_s)
    for values in ((0, 0, 0, 0), VALUES):
        snd = bytearray(sound_bytes(rng, smp, values))
        snd[70:76] = bytes.fromhex("0123456789ab")  # k 25..27: the sample's key
        alone_snd = bytearray(snd)
        alone_snd[38] = 6                           # SAMPLE is machine 6 in its build alone
        r1, rec, r2, back = save_load(s, bytes(snd), SAVE2)
        q1, recq, q2, backq = save_load(c, bytes(alone_snd), SAVE2)
        same = [i for i in range(100) if rec[i] != recq[i] and i not in range(84, 92) and i not in (64, 65)]
        check(r1 == q1 == 1 and r2 == q2 == 1 and rec[76:82] == snd[70:76] and back[70:76] == snd[70:76]
              and rec[84:92] == bytes(snd[76:84]) and back[76:84] == bytes(snd[76:84])
              and rec[64:66] == bytes(snd[84:86]) and back[84:86] == bytes(snd[84:86])
              and (smp != 6 or not same) and not s.bad,
              f"{key}: a SAMPLE sound (machine {smp}) with k 28..31 = {[hex(v) for v in values]}: its key saved and "
              "loaded by SAMPLE's wrappers, k 28..32 by the layer"
              + (", the record otherwise SAMPLE's build alone's" if smp == 6 else ""))


# --- 6. a machine change ----------------------------------------------------------------------------------------------
def change_tests(key, img, runtime, ref2):
    u = UI(img, runtime)
    fill_records(u)
    obj, snd = fake_track(u, ref2 - 1)
    del u.hooks[0x40014072]
    this = 0x93900000
    for k in range(6):
        u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
    for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                  0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
        u.hooks[a_] = (f"{a_:#x}", v)
    u.uc.mem_write(snd + 76, struct.pack(">4H", *VALUES))
    u.call(0x400a2712, this, 1, 0, 0)
    mach = struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8
    kept = struct.unpack(">4H", u.uc.mem_read(snd + 76, 8))
    m = next(m for m in TS.ADDED if m["index"] == ref2)
    vals = [struct.unpack(">h", u.uc.mem_read(snd + 0x14 + 2 * sl, 2))[0] >> 8 for sl in (0xb, 0xc, 0xd, 0xe, 0x12)]
    check(mach == ref2 and vals == [k[2] for k in m["knobs"]] + [m["decay"]] and kept == VALUES and not u.bad,
          f"{key}: a real machine change {TS.NAMES[ref2 - 1]} -> REF2 (0x40014072): REF2's knobs at their defaults "
          f"{vals}, k 28..31 kept {[hex(x) for x in kept]}")


# --- 8. the press, 9. the LEDs (the switches, notes/63 §16) ---------------------------------------------------------
def project(u, t, machine, k32, has_project=True, has_sound=True):
    """The project as sc_track finds it: track t of the project singleton at +212 + 68 t, its vtable's method +40
    giving the sound (one sound for every track, machine at +38, k 32 at +84); the selection chain stubbed, as are
    0x4001abe2 (the stock switch) and 0x400760ba (a new LED frame). Returns the hooks."""
    for i in range(6):
        u.uc.mem_write(PROJ + 212 + 68 * i, struct.pack(">I", TRACK_VT))
    u.uc.mem_write(TRACK_VT + 40, struct.pack(">I", SOUND_FN))
    snd = bytearray(100)
    snd[38] = machine & 0xff
    struct.pack_into(">H", snd, K32, k32)
    u.uc.mem_write(SOUND, bytes(snd))
    return {PROJECT: ("project", PROJ if has_project else 0), PROJECT_TRACKS: ("tracks", SEL),
            ACTIVE_TRACK: ("active", t), SOUND_FN: ("sound", SOUND if has_sound else 0), SWITCH: ("switch", 0),
            VIEW_LEDS: ("leds", 0), TRIG_HELD: ("trig", 1), UI_STATE: ("ui", 0x93a20000)}


def sentinels(u):
    vals = [0x5a5a0000 + i for i in range(len(KEPT))]
    for r, v in zip(KEPT, vals):
        u.uc.reg_write(r, v)
    return vals


def press(u, held, t, machine, k32, param, trig=0, **kw):
    """0x4001ac4a(view, param) as MainScreenView's key handler calls it: (the calls it made, k 32 after, whether the
    stack and the registers d2..d7, a2..a6 came back and memory stayed in bounds)."""
    u.keys(held)
    u.hooks = project(u, t, machine, k32, **kw)
    u.hooks[TRIG_HELD] = ("trig", trig)
    u.calls.clear()
    vals = sentinels(u)
    u.call(PRESS, VIEW, param)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in KEPT] == vals
    calls = [(n, a[:2] if n == "switch" else a[:1]) for n, a in u.calls if n in ("switch", "leds", "trig")]
    return calls, struct.unpack(">H", u.uc.mem_read(SOUND + K32, 2))[0], u.sp_ok and kept and not u.bad


def press_tests(key, stock, img, runtime, ref2, machines, switchers):
    a, b = UI(stock), UI(img, runtime)
    cases, bad, acted = 0, [], 0
    helds = ((), (LAYER,), (TRACK,), (LAYER, TRACK), (LAYER, FUNC), (RETRIG,))
    for held in helds:
        for m in machines:
            for t in (0, 3, 5):
                for k32 in (0, 0x100, 0x200, 0x300):
                    for param in (PUNCH_P, GATE_P, 43, 46):
                        ca, ka, oka = press(a, held, t, m, k32, param)
                        cb, kb, okb = press(b, held, t, m, k32, param)
                        cases += 1
                        act = LAYER in held and TRACK not in held and m in switchers and param in BIT
                        if act:
                            acted += 1
                            good = cb == [("trig", (STATE,)), ("leds", (VIEW,))] and kb == k32 ^ BIT[param] and okb
                        else:
                            good = cb == ca and kb == ka == k32 and okb and oka
                        if not good:
                            bad.append((held, s32(m), t, hex(k32), param, cb, ca, hex(kb)))
    check(not bad and acted, f"{key}: the press (0x4001ac4a): MACHINES held, TRACK not, on a track of a machine with "
                             f"switches (machines {sorted(switchers)}), no trig held: "
                             f"bit 8 (PUNCH) or 9 (GATE) of k 32 flipped, one LED frame asked with the view, no stock "
                             f"switch ({acted} cases); every other case calls what the stock OS calls ({cases} cases "
                             f"in all; keys, machines, tracks 0, 3, 5, k 32, parameters 43..46); registers and stack "
                             f"come back" + (f"; DIFFERENT {bad[:3]}" if bad else ""))
    edge = []
    for kw in ({"has_project": False}, {"has_sound": False}):
        ca, ka, oka = press(a, (LAYER,), 0, ref2, 0, PUNCH_P, **kw)
        cb, kb, okb = press(b, (LAYER,), 0, ref2, 0, PUNCH_P, **kw)
        edge.append(cb == ca and kb == ka and okb and oka)
    a.keys(())
    b.keys(())
    check(all(edge), f"{key}: MACHINES + PUNCH without a project, or without a sound for the track: the stock press")
    # the stock switch itself: without TRACK once on the selected track, with TRACK on all six (Control All)
    _, _, _ = press(a, (), 3, ref2, 0, PUNCH_P)
    one = [c for c in a.calls if c[0] == "switch"]
    _, _, _ = press(a, (TRACK,), 3, ref2, 0, GATE_P)
    six = [c[1][:2] for c in a.calls if c[0] == "switch"]
    a.keys(())
    check([c[1][:2] for c in one] == [(PUNCH_P, 3)] and six == [(GATE_P, i) for i in range(6)],
          "the stock OS's press, as the proof stubs it: 0x4001abe2(44, 3) for PUNCH on track 3, (45, 0..5) with TRACK")


# the switches as p-locks (the layer's 0.5, notes/63 §27): a sequence and its pattern in memory, the OS's lock
# functions
STATE = 0x93a20000                                   # what project() gives as the UI's state
SEQ, SEQVT, SEQ_PAT, PATTRK = 0x93e10000, 0x93e20000, 0x93e20100, 0x93e30000
HOLDER, HVT, H_BASE, H_NOTE = 0x93e40000, 0x93e50000, 0x93e50100, 0x93e50200
SEQ_OF, REDRAW = 0x4000f23e, 0x40069b84


def seq_hooks(u, t, length):
    """The selected track's sequence (0x4000f23e stubbed): its pattern of `length` steps, its locks in PL_RAM through
    the object at +44, track t; the hooks to add."""
    for a, v in ((SEQ, SEQVT), (SEQ + 44, HOLDER), (SEQ + 56, t), (SEQ + 60, 0), (SEQVT + 40, SEQ_PAT), (HOLDER, HVT),
                 (HVT + 40, H_BASE), (HVT + 16, H_NOTE)):
        u.uc.mem_write(a, struct.pack(">I", v))
    u.uc.mem_write(PATTRK + 713, struct.pack(">h", length))
    return {SEQ_OF: ("seq", SEQ), SEQ_PAT: ("pattern", PATTRK), H_BASE: ("locks", PL_RAM), H_NOTE: ("note", 0),
            REDRAW: ("redraw", 0)}


def held_mask(u, steps):
    m = sum(1 << n for n in steps)
    u.uc.mem_write(STATE + 348, struct.pack(">II", m >> 32, m & 0xffffffff))


def lock_press(u, t, machine, k32, param, steps, length, data):
    """0x4001ac4a with MACHINES held, a trig held over these steps: (the k 32 locks {step: word}, the other locks, the
    sound's k 32 after, the calls by name, the step words cleared, the hold marked, regs/stack/memory fine)."""
    u.keys((LAYER,))
    u.hooks = project(u, t, machine, k32)
    u.hooks.update(seq_hooks(u, t, length))
    u.hooks[TRIG_HELD] = ("trig", 1)
    held_mask(u, steps)
    u.uc.mem_write(STATE + 92, b"\x01" * 256)
    u.uc.mem_write(data + PENDING, bytes(2))
    u.calls.clear()
    vals = sentinels(u)
    u.call(PRESS, VIEW, param)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in KEPT] == vals
    w = pl_words(u)
    mine = w.pop((t, 32), {})
    names = [n for n, _a in u.calls if n in ("trig", "seq", "leds", "switch", "redraw")]
    return (mine, w, struct.unpack(">H", u.uc.mem_read(SOUND + K32, 2))[0], names,
            bytes(u.uc.mem_read(STATE + 92, 256)) == bytes(256), u.uc.mem_read(data + USED, 1)[0],
            u.sp_ok and kept and not u.bad)


def lock_tests(key, img, runtime, machine, data):
    """The switches as p-locks: a sequence of steps, each press against what the previous ones left."""
    u = UI(img, runtime)
    t = 3
    pl_init(u)
    pl_lock(u, t, 5, 28, 0x1234)                      # another k's lock on a held step stays
    pl_lock(u, t, 7, 32, 0x0e00)                      # a step not held keeps its lock
    other = {(t, 28): {5: 0x1234}}
    seq = [  # (sound's k 32, press, held steps, length, the k 32 locks after, why)
        (0x0005, PUNCH_P, (2, 5, 40), 64, {2: 0x0500, 5: 0x0500, 7: 0x0e00, 40: 0x0500},
         "Loop on as a lock on the three held steps, the sound's Track FX byte not in it"),
        (0x0005, PUNCH_P, (2, 5, 40), 64, {7: 0x0e00}, "Loop back to the sound's: the locks cleared"),
        (0x0100, PUNCH_P, (3,), 64, {3: 0x0400, 7: 0x0e00}, "the sound loops: Loop off as a lock"),
        (0x0100, GATE_P, (3,), 64, {3: 0x0e00, 7: 0x0e00}, "Reverse on next to it"),
        (0x0100, PUNCH_P, (3,), 64, {3: 0x0a00, 7: 0x0e00}, "Loop back to the sound's: the lock keeps Reverse"),
        (0x0100, GATE_P, (3,), 64, {7: 0x0e00}, "Reverse back too: the lock cleared"),
        (0x0000, GATE_P, (1, 20), 16, {1: 0x0a00, 7: 0x0e00}, "a step past the length (20 of 16) left alone"),
        (0x0200, GATE_P, (1, 7), 16, {1: 0x0800, 7: 0x0c00},
         "the sound reverses: both held locks hold Reverse off now, step 7 keeps its Loop"),
    ]
    bad = []
    for k32, param, steps, length, want, why in seq:
        mine, w, after, names, cleared, used, ok = lock_press(u, t, machine, k32, param, steps, length, data)
        good = (mine == want and w == other and after == k32 and "switch" not in names and names.count("leds") == 1
                and names.count("trig") == 1 and names.count("seq") == 1 and cleared and used == 1 and ok)
        if not good:
            bad.append((why, {s_: hex(v) for s_, v in mine.items()}, hex(after), names, cleared, used, ok))
    check(not bad, f"{key}: MACHINES + PUNCH / GATE with a trig held on machine {s32(machine)}: the switch of each "
                   "held step flipped as a lock of k 32 (bits 8/9 the values, 10/11 what it holds), back to the "
                   "sound's value it leaves the lock, a lock that holds none cleared, a step past the length, a step "
                   "not held and another k untouched; the sound stays; one LED frame, the hold marked, the step words cleared; "
                   f"{len(seq)} presses in a row" + (f"; DIFFERENT {bad[:2]}" if bad else ""))


STEP_KEYS, STEP_SITE, STEP_STOCK = 0x40022382, 0x40022eac, 0x40022ebc
EVENT2 = 0x93d30000


def step_press(u, layer_data, t, machine, k32, held, code, flags, steps, length=16):
    """The step keys' handler (0x40022382) from its entry with this key's event: (whether 0x40022eac was reached,
    whether it went on to the stock lock at 0x40022ebc, d0's byte when it returned, the k 32 locks, the other locks,
    the hold mark, the calls by name, registers kept when it returned)."""
    u.keys(held)
    u.hooks = project(u, t, machine, k32)
    u.hooks.update(seq_hooks(u, t, length))
    u.uc.mem_write(STATE + 357, b"\x01\x01")              # 0x4006b978: the held steps' mode
    u.uc.mem_write(STATE + 389, b"\x00")                   # 0x4006bb18
    held_mask(u, steps)
    u.uc.mem_write(STATE + 92, b"\x01" * 256)
    u.uc.mem_write(EVENT2, bytes(32))
    u.uc.mem_write(EVENT2 + 12, struct.pack(">II", code, flags))
    if layer_data:
        u.uc.mem_write(layer_data + PENDING, bytes(2))
    pl_init(u)
    seen = []

    def stop(uc, addr, size, ud):
        if addr in (STEP_SITE, STEP_STOCK):
            seen.append(addr)
            if addr == STEP_STOCK:
                uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, stop)
    u.calls.clear()
    vals = sentinels(u)
    d0 = u.call(STEP_KEYS, VIEW, EVENT2)
    u.uc.hook_del(h)
    stock = STEP_STOCK in seen
    kept = stock or ([u.uc.reg_read(r) & 0xffffffff for r in KEPT] == vals and u.sp_ok)
    w = pl_words(u)
    mine = w.pop((t, 32), {})
    used = u.uc.mem_read(layer_data + USED, 1)[0] if layer_data else 0
    names = [n for n, _a in u.calls if n in ("leds", "switch", "seq")]
    return STEP_SITE in seen, stock, d0 & 0xff, mine, w, used, names, kept and not u.bad


def step_tests(key, stock, img, runtime, data, switchers):
    """PUNCH and GATE with a step held, through the step keys' handler (0x40022382), stock and with the layer."""
    a, b = UI(stock), UI(img, runtime)
    t, steps, bad, n, ours = 3, (2, 5), [], 0, 0
    machines = sorted(switchers) + [0]
    for m in machines:
        for held in ((), (LAYER,), (LAYER, TRACK)):
            for code in (6, 7):
                ra = step_press(a, 0, t, m, 0, held, code, 1, steps)
                rb = step_press(b, data, t, m, 0, held, code, 1, steps)
                n += 1
                if held == (LAYER,) and m in switchers:
                    ours += 1
                    want = {s_: (0x0500 if code == 6 else 0x0a00) for s_ in steps}
                    good = (rb[0] and not rb[1] and rb[2] == 1 and rb[3] == want and rb[4] == {} and rb[5] == 1
                            and rb[6].count("leds") == 1 and "switch" not in rb[6] and rb[7])
                else:
                    good = rb[0] and rb[1] and rb[3] == {} and rb[7]
                good &= ra[0] and ra[1] and ra[3] == {} and ra[7]
                if not good:
                    bad.append((s32(m), held, code, ra[:3], rb[:3], {s_: hex(v) for s_, v in rb[3].items()}, rb[5:]))
    for im, d_ in ((a, 0), (b, data)):              # not a fresh press; no step held
        r1 = step_press(im, d_, t, machines[0], 0, (LAYER,), 6, 9, steps)
        r2 = step_press(im, d_, t, machines[0], 0, (LAYER,), 6, 1, ())
        n += 2
        if not (r1[0] and not r1[1] and r1[2] == 1 and r1[3] == {} and r1[7]):
            bad.append(("not fresh", r1[:3]))
        if not (not r2[0] and not r2[1] and r2[2] == 0 and r2[3] == {} and r2[7]):
            bad.append(("no step held", r2[:3]))
    msg = (f"{key}: the step keys' handler (0x40022382), PUNCH and GATE with steps held: MACHINES held, TRACK not, on "
           f"machines {sorted(s32(m) for m in switchers)}: the switch locked on the held steps, the press taken, one "
           "LED frame, the hold marked; every other case (no key, MACHINES + TRACK, a stock machine, the stock OS) on "
           "to the stock lock of PUNCH or GATE (0x40022ebc); not a fresh press: taken, nothing locked; no step held: "
           f"not taken ({n} cases)")
    check(not bad and ours, msg + (f"; DIFFERENT {bad[:2]}" if bad else ""))


def led_lock_tests(key, img, runtime, machine):
    """The LEDs with a trig held: the first held step's switches."""
    u = UI(img, runtime)
    t, bad, n = 3, [], 0
    for k32 in (0, 0x100, 0x200, 0x300):
        for word in (None, 0x0500, 0x0400, 0x0a00, 0x0800, 0x0e00, 0x0c00):
            pl_init(u)
            if word is not None:
                pl_lock(u, t, 6, 32, word)
            pl_lock(u, t, 9, 32, 0x0f00)              # a later held step: not shown
            extra = seq_hooks(u, t, 64)
            held_mask(u, (6, 9))
            got, regs, ok = leds(u, (LAYER,), t, machine, k32, 0, 0, trig=1, extra=extra)
            show = k32
            for i in (0, 1):
                if word is not None and word >> (10 + i) & 1:
                    show = show & ~(1 << (8 + i)) | (word >> (8 + i) & 1) << (8 + i)
            want = [(0x13, 2 if show & 0x100 else 1), (0x14, 2 if show & 0x200 else 1)]
            n += 1
            if got != want or not ok:
                bad.append((hex(k32), word and hex(word), got, want))
    check(not bad, f"{key}: the LEDs with a trig held: the first held step's switches, a locked switch the lock's "
                   f"value, the other the sound's ({n} cases)" + (f"; DIFFERENT {bad[:3]}" if bad else ""))


def leds(u, held, t, machine, k32, punch, gate, trig=0, extra=None):
    """MainScreenView's LED method from 0x4001cc80 (PUNCH in d2, GATE in d0, the selected track in d4, the LED
    singleton in d3, the LED setter in a4, as the method has them there) to 0x4001ccc2, after its second LED: its LED
    calls [(led, state)], the registers d2..d7, a2..a6 after, and whether it got there with memory in bounds."""
    u.keys(held)
    u.hooks = project(u, t, machine, k32)
    u.hooks[TRIG_HELD] = ("trig", trig)
    u.hooks.update(extra or {})
    u.hooks[LED_SET] = ("led", 0)
    u.calls.clear()
    sentinels(u)
    for r, v in ((mk.UC_M68K_REG_D0, gate), (mk.UC_M68K_REG_D2, punch), (mk.UC_M68K_REG_D3, LEDS),
                 (mk.UC_M68K_REG_D4, t), (mk.UC_M68K_REG_A4, LED_SET), (mk.UC_M68K_REG_A7, t7.STACK - 0x400)):
        u.uc.reg_write(r, v)
    u.bad.clear()
    u.uc.emu_start(LED_FROM, LED_UNTIL, count=1_000_000)
    regs = [u.uc.reg_read(r) & 0xffffffff for r in KEPT]
    got = [(a_[1], a_[2]) for n, a_ in u.calls if n == "led" and a_[0] == LEDS and a_[3] == LED_COLOUR]
    return got, regs, not u.bad and u.uc.reg_read(mk.UC_M68K_REG_PC) == LED_UNTIL


def led_tests(key, stock, img, runtime, ref2, machines, switchers):
    a, b = UI(stock), UI(img, runtime)
    cases, bad, acted = 0, [], 0
    for held in ((), (LAYER,), (TRACK,), (LAYER, TRACK), (RETRIG,)):
        for m in machines:
            for k32 in (0, 0x100, 0x200, 0x300):
                for punch in (0, 0x100):
                    for gate in (0, 0x100):
                        ga, ra, oka = leds(a, held, 3, m, k32, punch, gate)
                        gb, rb, okb = leds(b, held, 3, m, k32, punch, gate)
                        cases += 1
                        if LAYER in held and TRACK not in held and m in switchers:
                            acted += 1
                            want = [(0x13, 2 if k32 & 0x100 else 1), (0x14, 2 if k32 & 0x200 else 1)]
                            # d5 holds what lit GATE's LED; every other register as the stock code leaves it
                            good = (gb == want and rb[3] == k32 & 0x200 and rb[:3] + rb[4:] == ra[:3] + ra[4:]
                                    and okb and oka)
                        else:
                            good = gb == ga and rb == ra and okb and oka
                        if not good:
                            bad.append((held, s32(m), hex(k32), punch, gate, gb, ga))
    a.keys(())
    b.keys(())
    stock_ok = all(leds(a, (), 3, ref2, 0, p, g)[0] == [(0x13, 2 if p else 1), (0x14, 2 if g else 1)]
                   for p in (0, 0x100) for g in (0, 0x100))
    check(not bad and acted and stock_ok,
          f"{key}: the LEDs (0x4001cbfe from 0x4001cc80): MACHINES held, TRACK not, on a track of a machine with "
          f"switches (machines {sorted(switchers)}), LED 19 and 20 show "
          f"the switches of k 32 ({acted} cases); every other case as the stock OS, which shows PUNCH and GATE "
          f"({cases} cases in all); the other registers kept" + (f"; DIFFERENT {bad[:3]}" if bad else ""))


# PatternGridView's LED method with a trig held (the layer's 0.5, notes/63 §30)
GRID_FROM, GRID_SITE, GRID_UNTIL, GRID_STOCK = 0x40022110, 0x40022112, 0x40022156, 0x400cfc5e
GRID_VEC, GRID_LIST, GRID_LEDS = 0x404dd980, 0x40100a94, (0x12, 0x13, 0x14, 0x15, 0x1b)
GRID_OBJ = 0x93e60000                                # what d3 holds there: the object 0x400cfc5e gets


def grid(u, held, t, machine, k32, bits, extra=None):
    """PatternGridView's LED method from 0x40022110 to 0x40022156, after its loop over the LEDs of 0x40100a94: its frame
    B at sp + 20, the byte B + 63 = bits, d3 the object, d2 the LEDs, a4 the LED setter and d7 0 as the method has them
    there, the list's vector at 0x404dd980 as its first run builds it. Returns its LED calls [(led, state)], the
    arguments 0x400cfc5e got, the byte after, the registers d2..d7, a2..a6 after, and whether it got there with sp at B
    and memory in bounds."""
    u.keys(held)
    u.hooks = project(u, t, machine, k32)
    u.hooks.update(extra or {})
    u.hooks[LED_SET] = ("led", 0)
    u.hooks[GRID_STOCK] = ("grid", 0)
    end = GRID_LIST + 4 * len(GRID_LEDS)
    u.uc.mem_write(GRID_VEC, struct.pack(">III", GRID_LIST, end, end))
    frame = t7.STACK - 0x400
    u.uc.mem_write(frame + 60, b"\xa5\xa5\xa5" + bytes([bits]) + b"\xa5\xa5\xa5\xa5")
    u.calls.clear()
    sentinels(u)
    for r, v in ((mk.UC_M68K_REG_D2, LEDS), (mk.UC_M68K_REG_D3, GRID_OBJ), (mk.UC_M68K_REG_D7, 0),
                 (mk.UC_M68K_REG_A4, LED_SET), (mk.UC_M68K_REG_A7, frame - 20)):
        u.uc.reg_write(r, v)
    u.bad.clear()
    u.uc.emu_start(GRID_FROM, GRID_UNTIL, count=1_000_000)
    regs = [u.uc.reg_read(r) & 0xffffffff for r in KEPT]
    got = [(a_[1], a_[2]) for n, a_ in u.calls if n == "led" and a_[0] == LEDS and a_[3] == LED_COLOUR]
    objs = [a_[0] for n, a_ in u.calls if n == "grid"]
    around = bytes(u.uc.mem_read(frame + 60, 8))
    ok = (not u.bad and u.uc.reg_read(mk.UC_M68K_REG_PC) == GRID_UNTIL and u.uc.reg_read(mk.UC_M68K_REG_A7) == frame
          and around[:3] + around[4:] == b"\xa5" * 7)
    return got, objs, around[3], regs, ok


def grid_tests(key, stock, img, runtime, switchers):
    """PUNCH's and GATE's LEDs from PatternGridView's LED method with a trig held, stock and with the layer."""
    a, b = UI(stock), UI(img, runtime)
    t, bad, cases, acted = 3, [], 0, 0
    for held in ((), (LAYER,), (TRACK,), (LAYER, TRACK), (RETRIG,)):
        words = (None, 0x0500, 0x0400, 0x0a00, 0x0800, 0x0e00, 0x0c00) if held == (LAYER,) else (None, 0x0e00)
        for m in sorted(switchers) + [0]:
            for k32 in (0, 0x100, 0x200, 0x300):
                for word in words:
                    for bits in (0x00, 0x1f, 0x06, 0x19):
                        pl_init(b)
                        if word is not None:
                            pl_lock(b, t, 6, 32, word)
                        pl_lock(b, t, 9, 32, 0x0f00)        # a later held step: not shown
                        extra = seq_hooks(b, t, 64)
                        held_mask(b, (6, 9))
                        ga, oa, ba, ra, oka = grid(a, held, t, m, k32, bits)
                        gb, ob, bb, rb, okb = grid(b, held, t, m, k32, bits, extra)
                        cases += 1
                        want = bits
                        if LAYER in held and TRACK not in held and m in switchers:
                            acted += 1
                            show = k32
                            for i in (0, 1):
                                if word is not None and word >> (10 + i) & 1:
                                    show = show & ~(1 << (8 + i)) | (word >> (8 + i) & 1) << (8 + i)
                            want = bits & ~0x06 | (0x02 if show & 0x100 else 0) | (0x04 if show & 0x200 else 0)
                        leds_want = [(led, 2 if want >> i & 1 else 1) for i, led in enumerate(GRID_LEDS)]
                        stock_want = [(led, 2 if bits >> i & 1 else 1) for i, led in enumerate(GRID_LEDS)]
                        good = (ga == stock_want and gb == leds_want and ba == bits and bb == want and oa == ob == [GRID_OBJ]
                                and ra == rb and oka and okb)
                        if not good:
                            bad.append((held, s32(m), hex(k32), word and hex(word), hex(bits), gb, ga, hex(bb), oa, ob,
                                        oka, okb))
    a.keys(())
    b.keys(())
    check(not bad and acted, f"{key}: PatternGridView's LEDs with a trig held (0x40022110 to 0x40022156): MACHINES held, "
                             f"TRACK not, on a track of a machine with switches (machines {sorted(switchers)}), LED 0x13 "
                             "(PUNCH) and 0x14 (GATE) show the first held step's switches, a locked switch the lock's "
                             f"value, the other the sound's ({acted} cases), the other LEDs and bits as they were; every "
                             f"other case as the stock OS, which shows the held steps' p-locks of PUNCH and GATE ({cases} "
                             "cases in all); 0x400cfc5e once with the method's object; registers, stack and frame kept"
          + (f"; DIFFERENT {bad[:2]}" if bad else ""))


# --- 7. the voice loop ----------------------------------------------------------------------------------------------
def voice_tests(key, tweak, img, runtime, added, blocks):
    def play(m, note, k28):
        e = TC.engine(img, runtime, tweak)
        e.uc.mem_write(E.PARAMS + 0xe + 2 * 28, struct.pack(">h", k28))      # track 0's k 28
        x = TC.play(e, 0, m["index"], [k[2] for k in m["knobs"]], m["decay"], blocks, note=note)
        return x, not e.unmapped

    def switched(m, targets, sound=None, flip=None):
        """m playing note 60 with Tone 64 on track 0: k 32 in the copy of the note's sound (0x800015ae + 64) and, if
        sound is given, in a sound CUR_SNDS[0] points at; flip: at that block Square goes on in that sound."""
        e = TC.engine(img, runtime, tweak)
        e.uc.mem_write(CUR_SNDS, bytes(24))
        e.uc.mem_write(TARGETS + 64, struct.pack(">H", targets))
        if sound is not None:
            e.uc.mem_write(SND, bytes(100))
            e.uc.mem_write(SND + K32, struct.pack(">H", sound))
            e.uc.mem_write(CUR_SNDS, struct.pack(">I", SND))
        e.set(0, machine=m["index"], note=60, pitch=64, finetune=64, color=64, shape=0, sweep=64, contour=100,
              punch=0, gate=0, decay=m["decay"])

        def at(e_, b):
            if flip is not None and b == flip:
                e_.uc.mem_write(SND + K32, struct.pack(">H", 0x100))
        x = e.render(blocks, trig_at=(1,), track=0, on_block=at)
        return x, not e.unmapped

    for m in added:
        if m["code"] == "refmachine2":
            x0, ok0 = play(m, 60, 0)
            up, ok1 = play(m, 48, 0x100)
            down, ok2 = play(m, 72, -0x100)
            p1, _ = play(m, 60, 0x100)
            p2, _ = play(m, 60, 0x200)
            p3, _ = play(m, 60, 0x300)
            check(np.max(np.abs(x0)) > 1e6 and np.array_equal(x0, up) and np.array_equal(x0, down)
                  and not np.array_equal(x0, p1) and np.array_equal(p2, p3) and ok0 and ok1 and ok2,
                  f"{key}: REF2 (machine {m['index']}): note 48 at Octave +1 and note 72 at -1 play note 60 at 0, sample "
                  "for sample; +1 differs from 0; +3 plays as +2")
            w = {x: switched(m, x) for x in (0, 0x100, 0x200, 0x300)}
            ok = all(o for _, o in w.values())
            w = {x: s for x, (s, _) in w.items()}
            distinct = all(not np.array_equal(w[i], w[j]) for i in w for j in w if i < j)
            check(distinct and min(np.max(np.abs(s)) for s in w.values()) > 1e6 and ok,
                  f"{key}: REF2's switches from k 32: off, Square, Tone open and both play four different sounds "
                  "(Tone 64, so that the open lowpass is heard)")
            snd_on, ok1 = switched(m, 0, sound=0x100)
            snd_off, ok2 = switched(m, 0x100, sound=0)
            check(np.array_equal(snd_on, w[0x100]) and np.array_equal(snd_off, w[0]) and ok1 and ok2,
                  f"{key}: REF2 reads k 32 in the note's sound (CUR_SNDS[0] + 84) and its 66-byte copy only without one: "
                  "Square in the sound plays Square over a copy without it, and the other way round")
            flip, ok3 = switched(m, 0, sound=0, flip=FLIP)
            cut = FLIP * 32
            check(np.array_equal(flip[:cut], snd_off[:cut]) and not np.array_equal(flip[cut:], snd_off[cut:]) and ok3,
                  f"{key}: Square switched on in the sound at block {FLIP}, while the note plays: the same sound up to "
                  "that block, Square from it on")
        elif m["code"] == "refmachine":
            x0, _ = play(m, 60, 0)
            x1, ok = play(m, 60, 0x100)
            check(np.array_equal(x0, x1) and np.max(np.abs(x0)) > 1e6 and ok,
                  f"{key}: REF (machine {m['index']}) ignores k 28, sample for sample")
            y0, _ = switched(m, 0)
            y1, ok = switched(m, 0x300, sound=0x300)
            check(np.array_equal(y0, y1) and ok, f"{key}: REF (machine {m['index']}) ignores k 32, sample for sample")


def mach(u, flags, machine, opened, trig=0):
    """MainScreenView's key handler from its MACHINES case (0x4001c252) with an event of these flags (bit 0 pressed,
    bit 1 FUNC), the selected track's machine, the MACHINES list among the controller's views or not, and a held trig
    or not: where it goes (MACH_STOPS), the registers d2..d7, a2..a6 and the stack as they came, memory in bounds."""
    u.hooks = project(u, 0, machine, 0)
    u.hooks[TRIG_HELD] = ("trig", trig)
    u.calls.clear()
    u.uc.mem_write(VIEW + 44, struct.pack(">I", CONTROLLER))
    head, other, node, view_o, view_m = CONTROLLER + 20, CONTROLLER + 0x100, CONTROLLER + 0x200, CONTROLLER + 0x300, \
        CONTROLLER + 0x400
    u.uc.mem_write(view_o, struct.pack(">I", 0x40100860))          # another view in the list: the pattern selection
    u.uc.mem_write(view_m, struct.pack(">I", MACHINES_VT))
    u.uc.mem_write(other, struct.pack(">III", node if opened else head, 0, view_o))
    u.uc.mem_write(node, struct.pack(">III", head, 0, view_m))
    u.uc.mem_write(head, struct.pack(">I", other))
    u.uc.mem_write(EVENT, bytes(32))
    u.uc.mem_write(EVENT + 16, struct.pack(">I", flags))
    vals = [0x5a5a0000 + i for i in range(len(KEPT))]
    vals[KEPT.index(mk.UC_M68K_REG_D3)], vals[KEPT.index(mk.UC_M68K_REG_A2)] = EVENT, VIEW
    for r, v in zip(KEPT, vals):
        u.uc.reg_write(r, v)
    sp = t7.STACK - 0x400
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.bad.clear()
    got = []

    def stop(uc, addr, size, ud):
        if addr in MACH_STOPS:
            got.append(MACH_STOPS[addr])
            uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, stop)
    u.uc.emu_start(MACH_CASE, 0x90000000, count=200_000)
    u.uc.hook_del(h)
    regs = [u.uc.reg_read(r) & 0xffffffff for r in KEPT]
    mine = {KEPT.index(mk.UC_M68K_REG_D2), KEPT.index(mk.UC_M68K_REG_A3)}   # the case's own: the test's answer, the test
    ok = all(regs[i] == vals[i] for i in range(len(KEPT)) if i not in mine) and u.uc.reg_read(mk.UC_M68K_REG_A7) == sp \
        and not u.bad
    return (got[0] if got else None), ok


def mach_tests(key, stock, img, runtime, data, machines, layer, switches=()):
    """MACHINES as the level's key (the layer's 0.4, the key map of 2026-10-31), on the OS's own key handler, stock
    and with the layer: on the tracks of a machine with a shortcut or a switch, a press that would open the MACHINES
    list opens nothing and is taken, the release opens it unless a shortcut or a switch acted in between; a press
    while the list is open closes it at once; FUNC + MACHINES and MACHINES with a held trig go to the PRESET browser as
    before; every other machine as the stock OS. Then that the press of a switch and the knob of a shortcut mark the
    hold."""
    a, b = UI(stock), UI(img, runtime)
    press_f, release_f, func_f = 1, 0, 3
    bad, cases = [], 0
    for m in machines:
        for opened in (False, True):
            for used in (False, True):
                b.uc.mem_write(data + PENDING, bytes(2))
                seq_a = [mach(a, press_f, m, opened), mach(a, release_f, m, opened)]
                pa = mach(b, press_f, m, opened)
                if used:
                    b.uc.mem_write(data + USED, b"\x01")
                ra = mach(b, release_f, m, opened)
                seq_b = [pa, ra]
                want = [w for w, _ in seq_a]
                if m in layer and not opened:
                    want = ["taken", "pass" if used else "toggle"]
                cases += 1
                if [w for w, _ in seq_b] != want or not all(ok for _, ok in seq_a + seq_b):
                    bad.append((s32(m), opened, used, [w for w, _ in seq_b], want))
            cases += 1
            if mach(a, func_f, m, opened)[0] != "browser" or mach(b, func_f, m, opened)[0] != "browser":
                bad.append((s32(m), opened, "FUNC"))
            for used in (False, True):          # a held trig: the stock browser, or on a switch's track on the release
                cases += 1
                b.uc.mem_write(data + PENDING, bytes(2))
                sa = mach(a, press_f, m, opened, 1)
                pb = mach(b, press_f, m, opened, 1)
                frames = [c[1][0] for c in b.calls if c[0] == "leds"]
                if frames != ([VIEW] if m in switches else []):
                    bad.append((s32(m), opened, "trig", used, "LED frames", frames))
                if used:
                    b.uc.mem_write(data + USED, b"\x01")
                rb = mach(b, release_f, m, opened, 1)
                want = ["taken", "pass" if used else "browser"] if m in switches else ["browser"]
                got = [pb[0], rb[0]] if m in switches else [pb[0]]
                if sa[0] != "browser" or got != want or not (sa[1] and pb[1] and (rb[1] or m not in switches)):
                    bad.append((s32(m), opened, "trig", used, got, want))
    check(not bad, f"{key}: MACHINES (0x4001c252): on machines {sorted(s32(m) for m in layer)} a press that would open "
                   "the list is taken, the release opens it unless a shortcut or a switch acted; a press with the list "
                   "open closes it at once; FUNC + MACHINES: the PRESET browser; a held trig: the PRESET browser, on "
                   f"machines {sorted(s32(m) for m in switches)} on the release unless a switch acted (else the event "
                   f"passes on), the press asking once for a new LED frame; the other machines as the stock OS ({cases} "
                   "cases; registers and stack kept)"
                   + (f"; DIFFERENT {bad[:3]}" if bad else ""))
    return b


# --- 11. the pattern's p-lock rows (the layer's 0.5) ----------------------------------------------------------------
PL_RAM, PL_FILE = 0x91300000, 0x91400000          # the pattern's locks (6 x 4385 bytes) and its file (80 x 130 bytes)
CONV, PTAB, IDX_TO_K = 0x4005aa34, (0x4005b998, 0x4005baca), 0x4005aa1a


def pl_init(u):
    u.uc.mem_write(PL_RAM, (b"\xff\xff" * (34 * 64) + b"\x00" * 33) * 6)


def pl_lock(u, t, step, k, v):
    u.uc.mem_write(PL_RAM + t * 4385 + step * 68 + 2 * k, struct.pack(">h", v))
    u.uc.mem_write(PL_RAM + t * 4385 + 4352 + k, b"\x01")


def pl_words(u):
    """{(track, k): {step: value}} of every word of k 0..32 that is not -1."""
    out = {}
    for t in range(6):
        blk = bytes(u.uc.mem_read(PL_RAM + t * 4385, 4385))
        for k in range(33):
            got = {}
            for s_ in range(64):
                v = struct.unpack_from(">h", blk, s_ * 68 + 2 * k)[0]
                if v != -1:
                    got[s_] = v
            if got:
                out[t, k] = got
    return out


def pl_rows(u):
    f = bytes(u.uc.mem_read(PL_FILE, 80 * 130))
    return sorted((f[130 * r], f[130 * r + 1]) for r in range(80) if f[130 * r] != 0xff and f[130 * r + 1] != 0xff)


def pl_save(u, locks):
    pl_init(u)
    for lk in locks:
        pl_lock(u, *lk)
    u.uc.mem_write(PL_FILE, bytes(80 * 130))
    u.call(0x4005b95c, PL_FILE, PL_RAM, 0)
    return pl_rows(u), bytes(u.uc.mem_read(PL_FILE, 80 * 130))


def pl_load(u, file):
    pl_init(u)
    u.uc.mem_write(PL_FILE, file)
    u.call(0x4005b766, PL_RAM, PL_FILE)
    return pl_words(u)


def plock_tests(key, stock, img, runtime, syms):
    """The pattern's p-lock rows (the layer's 0.5): the sites, the index -> k step, a pattern saved and loaded, one
    lock updated, the stock OS's file for stock locks, the official OS reading the layer's file."""
    check(bytes(img[CONV - E.BASE:CONV - E.BASE + 6]) == bytes.fromhex("4ef9") + struct.pack(">I", syms["sc_conv"])
          and all(struct.unpack_from(">I", img, a - E.BASE)[0] == syms["sc_ptab"] for a in PTAB),
          f"{key}: 0x4005aa34 -> jmp sc_conv, 0x4005b998 and 0x4005baca -> sc_ptab")
    a, b = UI(stock), UI(img, runtime)
    bad = []
    for t in range(8):
        for i in range(41):
            want = s32(a.call(IDX_TO_K, t, i))
            if t <= 5 and i == 18:
                want = 32
            elif t <= 5 and 24 <= i <= 32:
                want = i - 1
            got = s32(b.call(IDX_TO_K, t, i))
            if got != want or b.bad:
                bad.append((t, i, got, want))
    check(not bad, f"{key}: 0x4005aa1a (track, index -> k), tracks 0..7, indices 0..40: 18 -> k 32 and 24..32 -> k "
                   "23..31 on tracks 0..5, every other answer the stock OS's"
                   + (f"; DIFFERENT {bad[:4]}" if bad else ""))
    locks = [(0, 0, 1, 0x3000), (2, 5, 32, 0x0101), (2, 6, 32, 0x0e00), (5, 63, 32, 0x0200), (3, 4, 31, 0x0400),
             (1, 3, 23, 0x0800), (4, 9, 9, 0x0500), (4, 9, 32, 0x0301), (0, 15, 13, 0x4400)]
    rows, file = pl_save(b, locks)
    want_rows = sorted({(18 if k == 32 else k + 1 if k >= 18 else k, t) for t, _s, k, _v in locks})
    back = pl_load(b, file)
    want = {}
    for t, s_, k, v in locks:
        want.setdefault((t, k), {})[s_] = v
    check(rows == want_rows and back == want and not b.bad,
          f"{key}: a pattern saved whole (0x4005b95c): rows (index, track) {rows}, k 32's at 18; loaded (0x4005b766): "
          "every lock back on its k, k 32 next to k 9 on track 4" + ("" if back == want else f"; DIFFERENT {back}"))
    _, file = pl_save(b, [(0, 0, 1, 0x3000)])
    pl_init(b)
    pl_lock(b, 0, 0, 1, 0x3000)
    pl_lock(b, 2, 7, 32, 0x0100)
    b.uc.mem_write(PL_FILE, file)
    b.call(0x4005ba90, PL_FILE, PL_RAM, 0, 32, 2)
    upd = pl_rows(b)
    back = pl_load(b, bytes(b.uc.mem_read(PL_FILE, 80 * 130)))
    check(upd == [(1, 0), (18, 2)] and back == {(0, 1): {0: 0x3000}, (2, 32): {7: 0x0100}} and not b.bad,
          f"{key}: one lock of k 32 updated (0x4005ba90): its row at 18 ({upd}), loaded back on k 32")
    plain = [lk for lk in locks if lk[2] < 23]
    _, fa = pl_save(a, plain)
    _, fb = pl_save(b, plain)
    check(fa == fb, f"{key}: locks of stock parameters only: the file byte for byte the stock OS's")
    _, file = pl_save(b, locks)
    off = pl_load(a, file)
    want_off = {}
    for t, s_, k, v in locks:                  # no two of these rows of one track share a step
        want_off.setdefault((t, k if k < 23 else 0), {})[s_] = v
    check(off == want_off and not a.bad,
          f"{key}: the official OS loading the layer's file: the rows of k 32 and k 23..31 on k 0, which nothing "
          "reads, every stock lock kept" + ("" if off == want_off else f"; DIFFERENT {off}"))


def no_switch_tests(stock):
    """A build whose machines declare no switch (REFC, the reference extension of CHORD: one knob shortcut): the
    layer is there, the press and the LEDs stay stock, every byte of presses is 0."""
    tweak, info, img, runtime = TC.built(stock, ["refchord"])
    u = UI(img, runtime)
    data = int(tweak["symbols"]["sc_data"], 16)
    sites = [bytes(u.uc.mem_read(a, 6)) == bytes(stock[a - E.BASE:a - E.BASE + 6])
             for a in (PRESS, LED_SITE, 0x4001c274, 0x40022eac, GRID_SITE)]
    n = u.uc.mem_read(data + 0x11, 1)[0]
    check(all(sites) and bytes(u.uc.mem_read(data + 0x14, 8)) == bytes(8) and n >= 1 and info["part"]["switches"] == 0,
          f"refchord: no switch declared: 0x4001ac4a, 0x4001cc86, 0x4001c274, 0x40022eac and 0x40022112 stock, the layer's {n} "
          "byte(s) of presses 0")
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    check(bytes(u.uc.mem_read(MACH_SITE, 6)).hex() == f"4eb9{syms['sc_mach']:08x}",
          "refchord: 0x4001ca1e -> jsr sc_mach: MACHINES is the level's key with a knob shortcut alone too")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--blocks", type=int, default=60, help="blocks of 32 frames per sound")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    alone = None
    for ids in selections:
        if "refmachine2" not in ids:
            sys.exit(f"!! {'+'.join(ids)}: the proof needs REF2, the machine with a shortcut")
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        added = TC.configure(ids)
        ref2 = next(m["index"] for m in added if m["code"] == "refmachine2")
        smp = next((m["index"] for m in added if m["code"] == "sampler"), None)
        if smp is not None and alone is None:
            _, _, img_s, runtime_s = TC.built(stock, ["sampler"])
            alone = (img_s, runtime_s)
        print(f"\n{key}: " + ", ".join(f"{m['name']} = machine {m['index']}" for m in added)
              + f"; shortcut layer at {info['part']['code_at']:#x}, data at {info['part']['data_at']:#x}, "
              f"record chain {', '.join(info['part']['chained'])}")
        syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
        u = UI(img, runtime)
        chain = [u.u32(syms["sc_data"] + 4 * i) for i in range(3)]
        want = [syms[s] for s in ("smp_hook_save2", "smp_hook_save1", "smp_hook_load")] if smp is not None else [0] * 3
        sites = {SAVE2: "sc_save2", SAVE1: "sc_save1", LOAD: "sc_load"}
        check(u.u32(KNOB_ENTRY) == syms["sc_knob"]
              and all(bytes(u.uc.mem_read(va, 8)).hex() == f"4ef9{syms[s]:08x}4e71" for va, s in sites.items())
              and chain == want,
              f"{key}: 0x401005a8 -> sc_knob; the three record functions -> sc_save2, sc_save1, sc_load; next of the "
              + ("chain: SAMPLE's wrappers, whose own jumps are not written" if smp is not None else "chain: the stock body"))
        first, count = u.uc.mem_read(syms["sc_data"] + 0x10, 2)
        presses = list(u.uc.mem_read(syms["sc_data"] + 0x14, 8))
        switchers = {ref2} | ({smp} if smp is not None else set())     # REF2's and SAMPLE's presses (notes/63 §21)
        want_p = [3 if first + i in switchers else 0 for i in range(8)]
        check(bytes(u.uc.mem_read(PRESS, 6)).hex() == f"4ef9{syms['sc_press']:08x}"
              and bytes(u.uc.mem_read(LED_SITE, 6)).hex() == f"4eb9{syms['sc_leds']:08x}"
              and presses == want_p and count == len(added),
              f"{key}: 0x4001ac4a -> jmp sc_press, 0x4001cc86 -> jsr sc_leds; the bytes of presses {presses[:count]} "
              f"for machines {first}..{first + count - 1} (REF2's and SAMPLE's 3: PUNCH and GATE)")
        machines = [0, 1, 4, 5] + [m["index"] for m in added] + [TS.NM, 100, 0xffffffff]
        print("the knob")
        knob_tests(key, img, runtime, ref2, machines)
        print("descriptor 1, its range, its value, its display")
        descriptor_tests(key, img, runtime, ref2)
        print("the tables built at boot")
        table_tests(key, img, runtime, ref2)
        print("save and load")
        save_tests(key, stock, img, runtime, ref2, smp, alone)
        print("a machine change")
        change_tests(key, img, runtime, ref2)
        print("the voice loop")
        voice_tests(key, tweak, img, runtime, added, args.blocks)
        print("the press")
        press_tests(key, stock, img, runtime, ref2, machines, switchers)
        print("the press with a trig held: the switches as p-locks")
        for m in sorted(switchers):
            lock_tests(key, img, runtime, m, syms["sc_data"])
        check(bytes(u.uc.mem_read(STEP_SITE, 6)).hex() == f"4ef9{syms['sc_steplock']:08x}",
              f"{key}: 0x40022eac -> jmp sc_steplock (the step keys' handler, the layer's 0.5)")
        step_tests(key, stock, img, runtime, syms["sc_data"], switchers)
        print("the LEDs")
        led_tests(key, stock, img, runtime, ref2, machines, switchers)
        for m in sorted(switchers):
            led_lock_tests(key, img, runtime, m)
        check(bytes(u.uc.mem_read(GRID_SITE, 6)).hex() == f"4eb9{syms['sc_gridleds']:08x}",
              f"{key}: 0x40022112 -> jsr sc_gridleds (PatternGridView's LEDs, the layer's 0.5)")
        grid_tests(key, stock, img, runtime, switchers)
        print("MACHINES, the level's key")
        check(bytes(u.uc.mem_read(MACH_SITE, 6)).hex() == f"4eb9{syms['sc_mach']:08x}",
              f"{key}: 0x4001ca1e -> jsr sc_mach")
        layer = switchers | {ref2}
        check(bytes(u.uc.mem_read(0x4001c274, 6)).hex() == f"4ef9{syms['sc_mtrig']:08x}",
              f"{key}: 0x4001c274 -> jmp sc_mtrig (a held trig and MACHINES, the layer's 0.5)")
        mb = mach_tests(key, stock, img, runtime, syms["sc_data"], machines, layer, switchers)
        mb.uc.mem_write(syms["sc_data"] + PENDING, bytes(2))
        press(mb, (LAYER,), 0, ref2, 0, PUNCH_P)
        flipped = mb.uc.mem_read(syms["sc_data"] + USED, 1)[0]
        mb.uc.mem_write(syms["sc_data"] + PENDING, bytes(2))
        mb.keys((LAYER,))
        knob(mb, ref2, 4)
        turned = mb.uc.mem_read(syms["sc_data"] + USED, 1)[0]
        mb.uc.mem_write(syms["sc_data"] + PENDING, bytes(2))
        mb.keys(())
        knob(mb, ref2, 6)
        other = mb.uc.mem_read(syms["sc_data"] + USED, 1)[0]
        check(flipped == 1 and turned == 1 and other == 0,
              f"{key}: a switch flipped (MACHINES + PUNCH on REF2) and a shortcut turned (MACHINES + COLOR) mark the hold; "
              "SWEEP turned without MACHINES does not")
        print("the pattern's p-lock rows")
        plock_tests(key, stock, img, runtime, syms)
    print("\na build with no switch")
    no_switch_tests(stock)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
