#!/usr/bin/env python3
"""Proof of the machine shortcuts (notes/63 §3, step B4b) and of the switches (notes/63 §16, §17) on the OS's own
code: the shortcut layer that tools/compose.py adds to a build whose machines declare a shortcut
(tools/machines/shortcuts/), with REF2's RETRIG + COLOR = Octave, -2 to +2, RETRIG + PUNCH = Square and RETRIG +
GATE = Tone open, and SAMPLE's RETRIG + PUNCH = Loop and RETRIG + GATE = Reverse (since One-Shot 0.11, notes/63 §21).

For each selection (by default: refmachine2; sampler,refmachine2; refmachine2,sampler; sampler,refmachine,refmachine2),
on the official OS 1.13:
  1. the sites: the knob lookup's entry in ParameterPageView's vtable (0x401005a8) and the three sound record
     functions jump into the layer; with SAMPLE in the build, its record wrappers are the next of the chain and their
     own jumps are not written; jmp sc_press at 0x4001ac4a and jsr sc_leds at 0x4001cc86, REF2's and SAMPLE's bytes
     of presses 3 (and in a build whose machines declare no switch, REFC's, both sites stock and every byte of presses 0);
  2. the knob, through the vtable entry and the OS's own key test: RETRIG held + COLOR on a REF2 track gives
     descriptor 1; every other knob, every other machine (stock, SAMPLE, REF, one the build does not have), RETRIG
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
     calls it): RETRIG held, TRACK not, on a REF2 or SAMPLE track flips bit 8 or 9 of k 32 in the track's sound, asks once for
     a new LED frame (0x400760ba with the view) and switches nothing (0x4001abe2 not called), without asking whether
     a trig is held (0x4006b736 not called);
     every other case (no key, TRACK, TRACK + RETRIG, another machine, no project, no sound, another parameter) calls
     what the stock OS calls with the same arguments and leaves k 32; d2..d7 and a2..a6 and the stack come back;
  9. the LEDs: MainScreenView's LED method from 0x4001cc80 to its second LED (0x4001ccc2), with PUNCH and GATE of
     the selected track in d2 and d0: RETRIG held, TRACK not, on a REF2 or SAMPLE track, LED 19 and 20 show the switches
     (state 2 on, 1 off); every other case lights them as the stock OS; d5 leaves as the stock code leaves it there,
     the other registers kept.
Not covered here: that the sound found through the project's track is the one in CUR_SNDS[t], that a RETRIG press
and release redraw the LEDs, and whether the project keeps a switch alone (notes/63 §17.2, §17.5: the device).

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_shortcuts.py --cycles model-cycles_OS1.13.syx [--machines sampler,refmachine2] [--blocks 60]
"""
import argparse
import pathlib
import struct
import sys

import numpy as np
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
FUNC, TRACK, RETRIG, LFO = 1, 2, 4, 8
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
        for c in (FUNC, TRACK, RETRIG, LFO):
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
    for c in (FUNC, TRACK, RETRIG, LFO):
        u.hold(c, True)
        ok &= u.call(KEY_HELD, c) == 1
        u.hold(c, False)
        ok &= u.call(KEY_HELD, c) == 0
    check(ok, f"{key}: the OS's key test (0x4007faf4) sees FUNC, TRACK, RETRIG and LFO held, then released")
    got, fwd = {}, True
    for held in ((), (RETRIG,), (RETRIG, FUNC), (RETRIG, TRACK), (RETRIG, LFO), (FUNC,), (LFO,)):
        u.keys(held)
        for trig in (0, 1):
            for m in machines:
                for k in range(16):
                    got[held, trig, m, k], ok_ = knob(u, m, k, trig)
                    fwd &= ok_
    u.keys(())
    want = {c: 1 if c[0] == (RETRIG,) and not c[1] and c[2] == ref2 and c[3] == 4 else STOCK_ANSWER for c in got}
    bad = [c for c in got if got[c] != want[c]]
    check(not bad, f"{key}: descriptor 1 for RETRIG + COLOR on REF2 (machine {ref2}) only; the stock answer for the 15 "
                   f"other knobs, machines {', '.join(str(s32(m)) for m in machines if m != ref2)}, no key, and FUNC, "
                   f"TRACK, LFO or a trig held with RETRIG ({len(got)} cases)" + (f"; DIFFERENT {bad[:4]}" if bad else ""))
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
    u.hold(RETRIG, True)
    d, ok = knob(u, ref2, 4)
    u.hold(RETRIG, False)
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
    b.hold(RETRIG, True)
    knob(b, ref2, 4)                                 # descriptor 1 installed before the tables are built
    b.hold(RETRIG, False)
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


def press(u, held, t, machine, k32, param, **kw):
    """0x4001ac4a(view, param) as MainScreenView's key handler calls it: (the calls it made, k 32 after, whether the
    stack and the registers d2..d7, a2..a6 came back and memory stayed in bounds)."""
    u.keys(held)
    u.hooks = project(u, t, machine, k32, **kw)
    u.calls.clear()
    vals = sentinels(u)
    u.call(PRESS, VIEW, param)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in KEPT] == vals
    calls = [(n, a[:2] if n == "switch" else a[:1]) for n, a in u.calls if n in ("switch", "leds", "trig")]
    return calls, struct.unpack(">H", u.uc.mem_read(SOUND + K32, 2))[0], u.sp_ok and kept and not u.bad


def press_tests(key, stock, img, runtime, ref2, machines, switchers):
    a, b = UI(stock), UI(img, runtime)
    cases, bad, acted = 0, [], 0
    helds = ((), (RETRIG,), (TRACK,), (RETRIG, TRACK), (RETRIG, FUNC))
    for held in helds:
        for m in machines:
            for t in (0, 3, 5):
                for k32 in (0, 0x100, 0x200, 0x300):
                    for param in (PUNCH_P, GATE_P, 43, 46):
                        ca, ka, oka = press(a, held, t, m, k32, param)
                        cb, kb, okb = press(b, held, t, m, k32, param)
                        cases += 1
                        act = RETRIG in held and TRACK not in held and m in switchers and param in BIT
                        if act:
                            acted += 1
                            good = cb == [("leds", (VIEW,))] and kb == k32 ^ BIT[param] and okb
                        else:
                            good = cb == ca and kb == ka == k32 and okb and oka
                        if not good:
                            bad.append((held, s32(m), t, hex(k32), param, cb, ca, hex(kb)))
    check(not bad and acted, f"{key}: the press (0x4001ac4a): RETRIG held, TRACK not, on a track of a machine with "
                             f"switches (machines {sorted(switchers)}): "
                             f"bit 8 (PUNCH) or 9 (GATE) of k 32 flipped, one LED frame asked with the view, no stock "
                             f"switch ({acted} cases); every other case calls what the stock OS calls ({cases} cases "
                             f"in all; keys, machines, tracks 0, 3, 5, k 32, parameters 43..46); registers and stack "
                             f"come back" + (f"; DIFFERENT {bad[:3]}" if bad else ""))
    edge = []
    for kw in ({"has_project": False}, {"has_sound": False}):
        ca, ka, oka = press(a, (RETRIG,), 0, ref2, 0, PUNCH_P, **kw)
        cb, kb, okb = press(b, (RETRIG,), 0, ref2, 0, PUNCH_P, **kw)
        edge.append(cb == ca and kb == ka and okb and oka)
    a.keys(())
    b.keys(())
    check(all(edge), f"{key}: RETRIG + PUNCH without a project, or without a sound for the track: the stock press")
    # the stock switch itself: without TRACK once on the selected track, with TRACK on all six (Control All)
    _, _, _ = press(a, (), 3, ref2, 0, PUNCH_P)
    one = [c for c in a.calls if c[0] == "switch"]
    _, _, _ = press(a, (TRACK,), 3, ref2, 0, GATE_P)
    six = [c[1][:2] for c in a.calls if c[0] == "switch"]
    a.keys(())
    check([c[1][:2] for c in one] == [(PUNCH_P, 3)] and six == [(GATE_P, i) for i in range(6)],
          "the stock OS's press, as the proof stubs it: 0x4001abe2(44, 3) for PUNCH on track 3, (45, 0..5) with TRACK")


def leds(u, held, t, machine, k32, punch, gate):
    """MainScreenView's LED method from 0x4001cc80 (PUNCH in d2, GATE in d0, the selected track in d4, the LED
    singleton in d3, the LED setter in a4, as the method has them there) to 0x4001ccc2, after its second LED: its LED
    calls [(led, state)], the registers d2..d7, a2..a6 after, and whether it got there with memory in bounds."""
    u.keys(held)
    u.hooks = project(u, t, machine, k32)
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
    for held in ((), (RETRIG,), (TRACK,), (RETRIG, TRACK)):
        for m in machines:
            for k32 in (0, 0x100, 0x200, 0x300):
                for punch in (0, 0x100):
                    for gate in (0, 0x100):
                        ga, ra, oka = leds(a, held, 3, m, k32, punch, gate)
                        gb, rb, okb = leds(b, held, 3, m, k32, punch, gate)
                        cases += 1
                        if RETRIG in held and TRACK not in held and m in switchers:
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
          f"{key}: the LEDs (0x4001cbfe from 0x4001cc80): RETRIG held, TRACK not, on a track of a machine with "
          f"switches (machines {sorted(switchers)}), LED 19 and 20 show "
          f"the switches of k 32 ({acted} cases); every other case as the stock OS, which shows PUNCH and GATE "
          f"({cases} cases in all); the other registers kept" + (f"; DIFFERENT {bad[:3]}" if bad else ""))


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


def no_switch_tests(stock):
    """A build whose machines declare no switch (REFC, the reference extension of CHORD: one knob shortcut): the
    layer is there, the press and the LEDs stay stock, every byte of presses is 0."""
    tweak, info, img, runtime = TC.built(stock, ["refchord"])
    u = UI(img, runtime)
    data = int(tweak["symbols"]["sc_data"], 16)
    sites = [bytes(u.uc.mem_read(a, 6)) == bytes(stock[a - E.BASE:a - E.BASE + 6]) for a in (PRESS, LED_SITE)]
    n = u.uc.mem_read(data + 0x11, 1)[0]
    check(all(sites) and bytes(u.uc.mem_read(data + 0x14, 8)) == bytes(8) and n >= 1 and info["part"]["switches"] == 0,
          f"refchord: no switch declared: 0x4001ac4a and 0x4001cc86 stock, the layer's {n} byte(s) of presses 0")


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
        print("the LEDs")
        led_tests(key, stock, img, runtime, ref2, machines, switchers)
    print("\na build with no switch")
    no_switch_tests(stock)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
