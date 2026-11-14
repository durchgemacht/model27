#!/usr/bin/env python3
"""SOLID's proof on the OS's own code (notes/71 §7, step 3): the machine as tools/compose.py composes it (alone,
machine 6; next to SAMPLE, machine 7), run in Unicorn with its payload as the boot hook leaves it.

  1. Start-up and the registrar, as test_compose.py checks any composed machine: the bootstrap reads the grown OS
     back, the boot hook copies the payload; the tables, lookups, MACHINES page, records and knobs of the machine.
  2. The core, exact: at every block, what solid_render gives the amp chain (the entry of AMP_ENV called from SOLID)
     is, bit for bit, the same core compiled for the host (tools/emu/solid_ref.c), fed the knobs solid_update must
     take from the voice, the parameters and the OS's velocity gain, computed here from notes/71 §3 (not read from
     the machine): six materials and the glides between them, notes 0 to 127, the knobs at their ends, the three
     exciters, DECAY, GATE and the note's end, velocities, retrigs on the same note (the body halved), on another note
     or material (damped over 5 blocks first), after silence, knobs moving every block. solid_render is called at
     every block; the strike comes in the block after the trig (v+0x38); a voice with nothing ringing does no work
     and its track is silent.
  3. The stock chain (notes/71 §9): without PUNCH the track's output is SOLID's (the core halved by SOLID, no VCA,
     no PUNCH) halved by the voice loop, exactly; SOLID never calls the VCA; the amp envelope stays open over a long
     note; a retrig does not cut the ringing body; PUNCH acts as on TONE (TONE's values when PUNCH is on); GATE damps
     the body to about 0.12 s once the note ends (the voice loop sets v+0x3c for one block only, SOLID keeps it), and
     without GATE the note's end changes nothing.
  4. The tracks: a change of machine leaves nothing ringing (SOLID, TONE, SOLID again: a fresh body); six SOLID tracks,
     each exact and the same as alone (the exciter's buffers are shared); SOLID among the stock machines, these
     identical to the stock OS; the stock machines without a SOLID track identical to the stock OS, without one
     instruction of SOLID; SOLID as machine 7 next to SAMPLE the same as alone.
  5. The OS's sequencer (seqrig.py: the real audio interrupt and the parameters' smoother): each step's velocity
     reaches its strike; a SHAPE p-locked on a step: what the strike sees and whether the smoother glides it
     afterwards (notes/71 §7, [HYP]: it would retune the body over about 20 ms).
  6. Measured, not checked: the level next to TONE, PERC and METAL, and the cost, instructions a block of one SOLID
     voice (materials, exciters, the strike's block, a silent voice) against the stock machines, six SOLID tracks
     ringing, the stack. With --modes 8,16 the 16-mode build too (SOLID_MODES=16, compiled with the m68k toolchain):
     exact on a few cases, and its cost, which decides 8 or 16 modes.

Not here: the governor of the Syntakt engines (only in builds with them, notes/71 §7), digiemu and the device.

Needs Unicorn and numpy (pip install unicorn numpy), a C compiler for the host and m68k-elf-objdump; --modes 16 the
m68k toolchain. Unicorn's JIT stops with SIGILL in a sandbox that forbids generated code: run it in a normal terminal.
--dry builds and lays out the firmwares and the host core only, without Unicorn. Duration: not measured yet.

    python3 tools/emu/test_solid.py --cycles firmware/model-cycles_OS1.13.syx [--quick] [--modes 8,16]
"""
import argparse
import ctypes
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402
import mcengine as E                # noqa: E402
import seqrig as S                  # noqa: E402
import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_syntakt_machines as TS  # noqa: E402

check = t7.check

PKG = HERE.parent / "machines" / "solid"
MARK = 0x4d4f4431                   # 'MOD1' at v+0x2c: the track is on SOLID since its last change of machine
AMP_ENV, VCA = 0x400a9252, 0x400a9430
KICK, SNARE, METAL, PERC, TONE, CHORD = range(6)
STOCK = {KICK: "KICK", SNARE: "SNARE", METAL: "METAL", PERC: "PERC", TONE: "TONE", CHORD: "CHORD"}
KW = dict(note=60, pitch=64, finetune=64, color=64, shape=51, sweep=40, contour=30, punch=0, gate=0, decay=80)
GAIN0 = 100                         # the OS's velocity gain of a step at the default velocity
TOL = 1 << 12                       # the amp chain at full level, against the core halved: -114 dB of full scale
VOICE_ENV = 0x230                   # the amp envelope's level (negative, 0x80000000 full scale)


def seed(t):
    """The random generator of track t as solid_update seeds it."""
    return (0x12345678 + t * 0x9e3779b9) & 0xffffffff


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def s32(x):
    return x - (1 << 32) if x & 0x80000000 else x


def to_bus(x, punch=0):
    """What solid_render makes of the core's Q27 (notes/71 §9): with PUNCH, Q31 saturated, into the stock PUNCH;
    without, half of that (PUNCH's 1/2 done by SOLID): the core clamped to +-1.0, x 8."""
    if punch:
        return np.where(x > 0x7ffffff, 0x7fffffff, np.where(x < -0x8000000, -0x80000000, x * 16))
    return np.clip(x, -0x8000000, 0x7ffffff) * 8


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def db(x, ref=2.0 ** 31):
    return 20 * np.log10(max(x, 1e-9) / ref)


def info(msg):
    print(f"  info  {msg}", flush=True)


# --- the host's core ---------------------------------------------------------------------------------------------
class Ref:
    """solid.c's core compiled for the host (tools/emu/solid_ref.c), SOLID_MODES modes."""

    def __init__(self, tmp, modes):
        cc = shutil.which("cc") or shutil.which("gcc") or "cc"
        so = tmp / f"solid_ref_{modes}.so"
        r = subprocess.run([cc, "-O2", "-std=c99", "-fwrapv", "-Wall", "-Wextra", "-Werror", f"-DSOLID_MODES={modes}",
                            f"-I{PKG}", "-shared", "-fPIC", "-o", str(so), str(HERE / "solid_ref.c")],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit("!! the host build of solid_ref.c failed:\n" + r.stderr)
        self.lib = ctypes.CDLL(str(so))
        self.lib.solid_ref_render.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self.lib.solid_ref_work.restype = ctypes.c_longlong
        self.modes = self.lib.solid_ref_modes()
        assert self.modes == modes, (self.modes, modes)

    def run(self, knobs, sd):
        """knobs: one list of 11 words a block (struct knobs); the core's output, blocks x 32, Q27."""
        n = len(knobs)
        blk = np.ascontiguousarray(np.array(knobs, dtype=np.int32).reshape(-1))
        out = np.zeros(32 * n, dtype=np.int32)
        self.lib.solid_ref_render(blk.ctypes.data, n, out.ctypes.data, sd)
        return out.reshape(n, 32).astype(np.int64)


# --- the firmwares -----------------------------------------------------------------------------------------------
def with_modes(modes, fn):
    """fn() with SOLID's manifest asking for SOLID_MODES=modes (a build compiled with the toolchain, never offered)."""
    orig = compose.load_manifest

    def lm(mid):
        m = orig(mid)
        if mid == "solid":
            m["build"]["defines"] = dict(m["build"].get("defines", {}), SOLID_MODES=str(modes))
        return m
    compose.load_manifest = lm
    try:
        return fn()
    finally:
        compose.load_manifest = orig


class Fw:
    """One firmware: the stock OS (ids None) or a composed build; the payload as in memory; SOLID's place."""

    def __init__(self, stock, ids, modes=8):
        self.ids, self.modes, self.tweak, self.runtime = ids, modes, None, None
        self.index, self.code = None, (0, 0)
        if ids is None:
            self.img = bytes(stock)
            return
        if modes == 8:
            tweak, info_ = compose.compose(stock, ids)
        else:
            tweak, info_ = with_modes(modes, lambda: compose.compose(stock, ids, relocator="ld"))
        patched, _ = build.apply_writes(stock, [tweak])
        self.runtime = build.payload_runtime(tweak, stock, None)
        self.img = bytes(patched) + build.payload_image(tweak, self.runtime)
        self.tweak = tweak
        pkg = next(p for p in info_["packages"] if p["id"] == "solid")
        at = pkg["code_at"] if isinstance(pkg["code_at"], int) else int(pkg["code_at"], 16)
        self.index, self.code = pkg["index"], (at, at + pkg["code"])
        self.upd = int(tweak["symbols"]["solid_update"], 16)
        self.rnd = int(tweak["symbols"]["solid_render"], 16)
        self.bss = (pkg["bss_at"], pkg["bss"])

    def engine(self, gain=GAIN0):
        """The voice loop alone; every track muted until a trig gives it a machine; the velocity gain of every track."""
        e = TC.engine(self.img, self.runtime, self.tweak) if self.runtime else TC.engine(self.img)
        S.ensure_map(e.uc, 0x40800000, 0x01800000)       # the OS's BSS above 0x40800000: the velocity's gain
        for t in range(6):
            e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE + 4, struct.pack(">I", TC.MUTED))
            set_gain(e, t, gain)
        return e


def set_gain(e, t, g):
    """What the OS holds for track t after a trig of velocity g with the default sound: gain = velocity."""
    e.uc.mem_write(S.GAIN + 2 * t, struct.pack(">h", g))
    e.uc.mem_write(S.GAIN_NEXT + 2 * t, struct.pack(">h", g))
    e.uc.mem_write(S.VEL + 2 * t, struct.pack(">h", g << 8))


# --- what SOLID receives, gives and should do ---------------------------------------------------------------------
class Probe:
    """At every block and for every track watched: the knobs solid_update must take (notes/71 §3, solid.c's statics
    kept here as there), whether solid_render ran, what it gave AMP_ENV, and whether it called the VCA."""

    def __init__(self, fw, e, tracks=(0,)):
        self.fw, self.tracks, self.block = fw, tuple(tracks), 0
        self.recs = {t: [] for t in self.tracks}
        self.last = [[0, 0] for _ in range(6)]           # last_note, last_shape: never cleared
        self.vel = [0] * 6                               # kin[t].vel: kept from one strike to the next
        self.ended = [0] * 6
        self.out_at = {}
        uc = self.uc = e.uc
        uc.hook_add(UC_HOOK_CODE, self._upd, begin=fw.upd, end=fw.upd)
        uc.hook_add(UC_HOOK_CODE, self._rnd, begin=fw.rnd, end=fw.rnd)
        uc.hook_add(UC_HOOK_CODE, self._amp, begin=AMP_ENV, end=AMP_ENV)
        uc.hook_add(UC_HOOK_CODE, self._vca, begin=VCA, end=VCA)

    def arg(self, k):
        sp = self.uc.reg_read(mk.UC_M68K_REG_A7)
        return struct.unpack(">I", self.uc.mem_read(sp + 4 * k, 4))[0]

    @staticmethod
    def track(v):
        return (v - E.VOICE0) // E.VSTRIDE if (v - E.VOICE0) % E.VSTRIDE == 0 and 0 <= v - E.VOICE0 < 6 * E.VSTRIDE \
            else -1

    def ours(self):
        return self.fw.code[0] <= self.arg(0) < self.fw.code[1]

    def _upd(self, uc, a, s, u):
        v = self.arg(2)
        t = self.track(v)
        if t not in self.tracks:
            return
        pmod, p = s32(self.arg(1)), self.arg(3)
        vb, pb = bytes(uc.mem_read(v, 0x40)), bytes(uc.mem_read(p, 0x28))
        v32 = lambda o: struct.unpack_from(">i", vb, o)[0]
        p16 = lambda o: struct.unpack_from(">h", pb, o)[0]
        init = v32(0x2c) != MARK
        if init:
            self.ended[t] = 0
        note = clamp(pmod + (p16(0x14) << 8) + ((p16(0x22) - 0x4000) << 3) - (64 << 16), 0, 127 << 16)
        shape, gate = p16(0x18), int(p16(0x20) != 0)
        if v32(0x38):
            self.ended[t] = 0
        if v32(0x3c) and not v32(0x34):
            self.ended[t] = 1
        strike = 0
        if v32(0x38):
            g = struct.unpack(">h", uc.mem_read(S.GAIN + 2 * t, 2))[0]
            self.vel[t] = clamp(g, 0, 127) * 258
            ln, ls = self.last[t]
            strike = 2 if note != ln or shape - ls >= 256 or shape - ls <= -256 else 1
            self.last[t] = [note, shape]
        knobs = [strike, note, p16(0x16), shape, p16(0x1a), p16(0x1c), p16(0x24), 0, self.vel[t], gate,
                 int(gate and self.ended[t])]
        self.recs[t].append(dict(block=self.block, init=init, knobs=knobs, render=0, done=0, v34=v32(0x34),
                                 v34_vca=None))

    def _rnd(self, uc, a, s, u):
        t = self.track(self.arg(2))
        if t in self.tracks and self.recs[t]:
            self.out_at[t] = self.arg(1)
            self.recs[t][-1]["render"] = 1

    def _amp(self, uc, a, s, u):
        t = self.track(self.arg(1))
        if t in self.tracks and self.ours() and self.recs[t]:
            r = self.recs[t][-1]
            r["done"] = 1
            r["pre"] = np.frombuffer(bytes(uc.mem_read(self.out_at[t], 128)), ">i4").astype(np.int64)
            v = self.arg(1)
            r["punch"], r["drive"], r["out_gain"] = (struct.unpack(">i", uc.mem_read(v + o, 4))[0]
                                                     for o in (0x48, 0x2a0, 0x2a4))

    def _vca(self, uc, a, s, u):
        v = self.arg(2)
        t = self.track(v)
        if t in self.tracks and self.ours() and self.recs[t]:
            self.recs[t][-1]["v34_vca"] = struct.unpack(">i", uc.mem_read(v + 0x34, 4))[0]

    def strikes(self, t=0):
        return [r["block"] for r in self.recs[t] if r["knobs"][0]]

    def verify(self, ref, t, final, chain=True):
        """final: the track's output, blocks x 32. Returns (what is wrong, measures)."""
        recs, bad, dev = self.recs[t], [], 0
        if not recs:
            return [f"track {t + 1}: no block on SOLID"], dict(inits=0, idle=0, blocks=0, dev=0)
        starts = [i for i, r in enumerate(recs) if r["init"]]
        if not starts or starts[0] != 0:
            bad.append(f"track {t + 1}: its first block on SOLID is not a fresh voice")
        unrendered = [r["block"] for r in recs if not r["render"]]
        if unrendered:
            bad.append(f"track {t + 1}: solid_render not called in blocks {unrendered[:4]}")
        for a, b in zip(starts, starts[1:] + [len(recs)]):
            seg = recs[a:b]
            want = ref.run([r["knobs"] for r in seg], seed(t))
            for r, h in zip(seg, want):
                hb = to_bus(h, r.get("punch", 0))
                if r["done"] and not np.array_equal(r["pre"], hb):
                    i = int(np.nonzero(r["pre"] != hb)[0][0])
                    bad.append(f"track {t + 1} block {r['block']}: the core differs from the host's at frame {i} "
                               f"({int(r['pre'][i])} against {int(hb[i])})")
                    break
                if not r["done"] and h.any():
                    bad.append(f"track {t + 1} block {r['block']}: not rendered, yet the host's core rings")
                    break
        for r in recs:
            y = final[r["block"]]
            if r["done"]:
                if chain and not r["punch"]:
                    # PUNCH off: nothing after SOLID (no VCA, no PUNCH) but the voice loop's halving
                    d = int(np.abs(y - (r["pre"] >> 1)).max())
                    dev = max(dev, d)
                    if d > TOL:
                        bad.append(f"track {t + 1} block {r['block']}: the output is not SOLID's halved by the voice "
                                   f"loop (off by {d})")
                        break
                if r["v34_vca"] is not None:
                    bad.append(f"track {t + 1} block {r['block']}: SOLID called the VCA")
                    break
            elif y.any():
                bad.append(f"track {t + 1} block {r['block']}: a voice with nothing ringing, its output is not 0")
                break
        return bad, dict(inits=len(starts), idle=sum(1 for r in recs if not r["done"]), blocks=len(recs), dev=dev)


def play(fw, kw, blocks, trigs=(1,), changes=None, gains=None, rels=(), track=0, probe=True, machine=None):
    """One track on SOLID (or machine), the others muted. changes: {block: knobs}; gains: {block: velocity gain written
    before it}; rels: blocks with a note's end. Returns (the track's output, blocks x 32; the Probe; the engine)."""
    e = fw.engine()
    e.set(track, machine=fw.index if machine is None else machine, **kw)
    pr = Probe(fw, e, (track,)) if probe and fw.runtime else None
    out = []
    for b in range(blocks):
        for k, v in (changes or {}).get(b, {}).items():
            e.set(track, **{k: v})
        if gains and b in gains:
            set_gain(e, track, gains[b])
        if pr:
            pr.block = b
        out.append(e.block(1 << track if b in trigs else 0, 1 << track if b in rels else 0)[track])
    return np.stack(out), pr, e


# --- 1. start-up and the registrar ------------------------------------------------------------------------------
def startup(cycles, stock, fw):
    print(f"start-up and the registrar ({'+'.join(fw.ids)})")
    X.bootstrap_depack_ok(cycles, fw.tweak, None) or t7.FAIL.append(f"{'+'.join(fw.ids)}: bootstrap")
    X.boot_hook_ok(fw.img, fw.runtime) or t7.FAIL.append(f"{'+'.join(fw.ids)}: boot hook")
    added = TC.configure(fw.ids)
    TC.own_pictures(fw.tweak, fw.runtime, added)        # SOLID's own pictures (notes/71 §13)
    a, b = TS.tables(stock, fw.img, fw.runtime)
    TS.lookups(a, b)
    TS.accessors(a, b, stock, fw.img)
    TS.screens(stock, fw.img, fw.runtime)
    TS.setter_and_wheel(stock, fw.img, fw.runtime)
    TS.records_and_change(stock, fw.img, fw.runtime)
    TS.out_of_range(stock, fw.img, fw.runtime)
    TS.small_icon(stock, fw.img, fw.runtime)


# --- 2. the core, exact ------------------------------------------------------------------------------------------
def cases(quick):
    """(name, knobs, extra for play)."""
    out = []
    shapes = (0, 25, 51, 76, 102, 127) + (() if quick else (12, 38, 64, 89, 115))
    for sh in shapes:
        out.append((f"SHAPE {sh}", dict(KW, shape=sh), dict(blocks=300, trigs=(1, 150))))
    for n in ((24, 96) if quick else (12, 24, 36, 48, 72, 84, 96, 108, 120)):
        for sh in ((0, 127) if quick else (0, 51, 102, 127)):
            out.append((f"note {n}, SHAPE {sh}", dict(KW, note=n, shape=sh), dict(blocks=200)))
    for c in ((0, 63, 80, 110) if quick else (0, 20, 45, 63, 64, 80, 95, 96, 110, 127)):
        out.append((f"CONTOUR {c}", dict(KW, contour=c, decay=100), dict(blocks=300 if c > 95 else 200)))
    for k, vals in (("color", (0, 127) if quick else (0, 32, 96, 127)), ("sweep", (0, 127) if quick else (0, 64, 127)),
                    ("decay", (0, 127) if quick else (0, 20, 64, 127))):
        for x in vals:
            out.append((f"{k.upper()} {x}", dict(KW, **{k: x}), dict(blocks=250)))
    out += [
        ("PITCH 0, note 0: the note held at 0", dict(KW, pitch=0, note=0), dict(blocks=120)),
        ("PITCH 127, note 127, glass: modes above 0.45 fs left out", dict(KW, pitch=127, note=127, shape=127),
         dict(blocks=120)),
        ("FINE 0, then FINE 127", dict(KW, finetune=0), dict(blocks=120, trigs=(1, 60), changes={60: dict(finetune=127)})),
        ("DECAY 127, glass, 600 blocks", dict(KW, decay=127, shape=127), dict(blocks=600)),
        ("GATE, the note ends at 120", dict(KW, gate=1, decay=110), dict(blocks=500, rels=(120,))),
        ("GATE, sustained noise (CONTOUR 127), the note ends at 150", dict(KW, gate=1, contour=127, decay=100),
         dict(blocks=500, rels=(150,))),
        ("no GATE, sustained noise, the note ends at 150", dict(KW, contour=127, decay=100),
         dict(blocks=400, rels=(150,))),
        ("velocity 1, 64, 127 on three strikes", dict(KW, contour=40),
         dict(blocks=300, trigs=(1, 100, 200), gains={0: 1, 99: 64, 199: 127})),
        ("retrigs on the same note: the body halved", dict(KW, decay=110), dict(blocks=300, trigs=(1, 60, 61, 120))),
        ("retrigs on other notes while it rings: damped over 5 blocks, then struck", dict(KW, decay=110),
         dict(blocks=300, trigs=(1, 60, 120), changes={60: dict(note=67), 120: dict(note=55)})),
        ("a retrig on another material while it rings", dict(KW, decay=110, shape=25),
         dict(blocks=300, trigs=(1, 80), changes={80: dict(shape=102)})),
        # not in the blocks right after the first trig: the voice's reset at the change of machine (block 2) clears a
        # trig of that block (v+0x34), as for any machine
        ("trigs in four blocks in a row, the note changing", dict(KW, decay=90),
         dict(blocks=200, trigs=(1, 20, 21, 22, 23), changes={21: dict(note=62), 22: dict(note=64), 23: dict(note=65)})),
        ("the body dies out, then a strike after silence", dict(KW, decay=0, shape=0),
         dict(blocks=300, trigs=(1, 250), changes={250: dict(note=72)})),
        ("knobs moving at every block", dict(KW, decay=100),
         dict(blocks=150, trigs=(1, 50, 100),
              changes={b: dict(color=(3 * b) % 128, shape=127 - (5 * b) % 128, sweep=(7 * b) % 128,
                               contour=(11 * b) % 128, decay=100 - b % 50) for b in range(150)})),
        ("every knob at 0", dict(KW, color=0, shape=0, sweep=0, contour=0, decay=0), dict(blocks=100)),
        ("every knob at 127", dict(KW, color=127, shape=127, sweep=127, contour=127, decay=127), dict(blocks=400)),
    ]
    return out


def exact(fw, ref, todo, label):
    bad, idle, blocks, dev = [], 0, 0, 0
    for name, kw, ex in todo:
        ex = dict(ex)
        n = ex.pop("blocks")
        y, pr, e = play(fw, kw, n, **ex)
        why, m = pr.verify(ref, 0, y)
        want = [t + 1 for t in ex.get("trigs", (1,)) if t + 1 < n]
        if pr.strikes() != want:
            why.append(f"strikes in blocks {pr.strikes()}, expected {want} (the block after each trig)")
        idle += m["idle"]
        blocks += m["blocks"]
        dev = max(dev, m["dev"])
        if why or e.unmapped or m["inits"] != 1 or not y.any():
            bad.append(name)
            print(f"        DIFF {name}: {why[:2]}, fresh voices {m['inits']}, outside memory {e.unmapped[:2]}")
    check(not bad, f"{label}: at every block, what solid_render gives AMP_ENV is the host's core, bit for bit, fed the "
                   f"knobs solid_update must take; solid_render called at every block, the strike in the block after "
                   f"each trig ({len(todo)} cases, {blocks} blocks) {bad[:4]}")
    check(idle > 0 and not bad, f"{label}: a voice with nothing ringing is not rendered and its track is silent "
                                f"({idle} blocks)")
    check(not bad, f"{label}: without PUNCH the track's output is SOLID's halved by the voice loop, off by at most "
                   f"{dev} (0: exactly); SOLID never calls the VCA")


# --- 3. the stock chain ------------------------------------------------------------------------------------------
def chain(fw, ref):
    """A long note: the envelope stays open; a retrig on the ringing body is not cut; PUNCH plays."""
    e = fw.engine()
    e.set(0, machine=fw.index, **dict(KW, decay=127, shape=102))
    pr = Probe(fw, e)
    y, lv = [], []
    for b in range(600):
        pr.block = b
        y.append(e.block(1 if b in (1, 300) else 0)[0])
        lv.append(abs(s32(struct.unpack(">I", e.uc.mem_read(E.VOICE0 + VOICE_ENV, 4))[0])))
    y = np.stack(y)
    why, _ = pr.verify(ref, 0, y)
    low = min(lv[3:]) / 2 ** 31
    check(not why and low > 0.9999 and not e.unmapped,
          f"the amp envelope stays open over 600 blocks (0.4 s): its level at least {low:.6f} of full scale {why[:1]}")
    cut = rms(y[300]) / max(rms(y[299]), 1)
    check(not why and cut > 0.5, f"a retrig on the ringing body (bell, DECAY 127): the trig's block keeps "
                                 f"{20 * np.log10(max(cut, 1e-9)):+.1f} dB of the block before, no cut to silence")
    p, pr2, e2 = play(fw, dict(KW, punch=1, decay=100), 200)
    q, _, _ = play(fw, dict(KW, decay=100), 200, probe=False)
    why2, _ = pr2.verify(ref, 0, p, chain=False)
    check(not why2 and p.any() and not np.array_equal(p, q) and not e2.unmapped,
          f"PUNCH: the core the same, the stock PUNCH acts on the output, peak {db(np.abs(p).max()):.1f} dB "
          f"(without {db(np.abs(q).max()):.1f} dB) {why2[:1]}")


def gate(fw):
    """GATE: the note's end damps the body to a T60 of about 0.12 s (180 blocks): about -60 dB 180 blocks after it
    (after the sustained exciter's release of 80 ms, 120 blocks, when there is one), where the held note (DECAY 127,
    about 8 s) has barely moved. Without GATE the note's end changes nothing."""
    rel, rows, ok = 100, [], True
    for name, kw, wait in (("mallet", dict(KW, decay=127, shape=102, contour=20), 180),
                           ("sustained noise", dict(KW, decay=127, shape=102, contour=127), 300)):
        n_b = rel + wait + 30
        g, _, e1 = play(fw, dict(kw, gate=1), n_b, rels=(rel,), probe=False)
        h, _, e2 = play(fw, dict(kw, gate=1), n_b, probe=False)
        n, _, e3 = play(fw, kw, n_b, rels=(rel,), probe=False)
        n0, _, e4 = play(fw, kw, n_b, probe=False)
        w = slice(rel + wait, rel + wait + 20)
        after = 20 * np.log10(max(rms(g[w]), 1e-9) / max(rms(g[rel - 20:rel]), 1e-9))
        held = 20 * np.log10(max(rms(h[w]), 1e-9) / max(rms(h[rel - 20:rel]), 1e-9))
        same = np.array_equal(n, n0)
        ok &= after < -45 and held > -12 and same and not (e1.unmapped or e2.unmapped or e3.unmapped or e4.unmapped)
        rows.append(f"{name}: {after:+.1f} dB {wait} blocks after the note's end (held: {held:+.1f} dB), without GATE "
                    f"{'identical' if same else 'DIFFERENT'}")
    check(ok, "GATE damps the body once the note ends, until the next strike; without GATE the note's end changes "
              "nothing: " + "; ".join(rows))


# --- 4. the tracks -----------------------------------------------------------------------------------------------
def change(fw, ref):
    """SOLID rings (DECAY 127), TONE takes the track (trig at 60), SOLID again (trig at 120): a fresh body."""
    y, pr, e = play(fw, dict(KW, decay=127, shape=102), 260, trigs=(1, 60, 120),
                    changes={60: dict(machine=TONE), 120: dict(machine=fw.index)})
    why, m = pr.verify(ref, 0, y)
    tone = np.abs(y[62:120]).max()
    check(not why and m["inits"] == 2 and pr.strikes() == [2, 121] and tone > 1e6 and not e.unmapped,
          f"a change of machine: SOLID, TONE (peak {db(tone):.1f} dB), SOLID again: a fresh voice, exact, nothing left "
          f"ringing from before {why[:1]}")


def six(fw, ref):
    """Six SOLID tracks with different knobs: each exact, and the same as alone."""
    kws = [dict(KW, note=36 + 7 * t, shape=(25 * t) % 128, contour=(30 + 20 * t) % 128, decay=60 + 10 * t)
           for t in range(6)]
    e = fw.engine()
    for t, kw in enumerate(kws):
        e.set(t, machine=fw.index, **kw)
    pr = Probe(fw, e, tuple(range(6)))
    x = []
    for b in range(200):
        pr.block = b
        x.append(e.block(0x3f if b in (1, 100) else 0))
    x = np.stack(x)
    bad = []
    for t in range(6):
        why, _ = pr.verify(ref, t, x[:, t])
        y, _, _ = play(fw, kws[t], 200, trigs=(1, 100), track=t, probe=False)
        if why or not np.array_equal(x[:, t], y) or not y.any():
            bad.append(t + 1)
            print(f"        DIFF track {t + 1}: {why[:1]}, same as alone {np.array_equal(x[:, t], y)}")
    check(not bad and not e.unmapped, f"six SOLID tracks together: each exact and identical to the same track alone "
                                      f"(the exciter's buffers are shared) {bad}")


def multi(fw, setup, blocks, trigs):
    e = fw.engine()
    for t, kw in setup.items():
        e.set(t, **kw)
    return np.stack([e.block(trigs.get(b, 0)) for b in range(blocks)]), e.unmapped


def mixed(fw, off, ref):
    """SOLID on tracks 2 and 5 among KICK, METAL, PERC and CHORD: the stock tracks identical to the stock OS, the SOLID
    tracks identical to alone."""
    mach = [KICK, fw.index, METAL, PERC, fw.index, CHORD]
    ours = {1: dict(KW, decay=60, shape=0), 4: dict(KW, note=48, shape=102, decay=60)}
    stock_kw = lambda m: dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[m]))
    setup = {t: dict(ours[t], machine=m) if t in ours else dict(KW, **stock_kw(m), machine=m) for t, m in enumerate(mach)}
    trigs = {1: 0x3f, 150: 0x3f}
    x, unm = multi(fw, setup, 300, trigs)
    r, unm_r = multi(off, {t: dict(kw, machine=KICK if t in ours else kw["machine"]) for t, kw in setup.items()},
                     300, trigs)
    ok = not unm and not unm_r
    for t in range(6):
        if t in ours:
            y, _, _ = play(fw, ours[t], 300, trigs=(1, 150), track=t, probe=False)
            ok &= np.array_equal(x[:, t], y) and y.any()
        else:
            ok &= np.array_equal(x[:, t], r[:, t]) and r[:, t].any()
    check(ok, "SOLID on tracks 2 and 5 among KICK, METAL, PERC, CHORD: the stock tracks identical to the stock OS, the "
              "SOLID tracks identical to alone")


def stock_unchanged(off, fw, label):
    """The six stock machines, no SOLID track: identical to the stock OS, without one instruction of SOLID."""
    def run(f, hook):
        e = f.engine()
        for t in range(6):
            e.set(t, **dict(KW, **dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[t])), machine=t))
        ran = []
        if hook:
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=f.code[0], end=f.code[1] - 1)
        x = np.stack([e.block(0x3f if b in (1, 150) else 0) for b in range(300)])
        return x, ran, e.unmapped
    r, _, _ = run(off, False)
    x, ran, unm = run(fw, True)
    check(np.array_equal(r, x) and np.abs(x).max() > 1e7 and not ran and not unm,
          f"{label}: the six stock machines identical to the stock OS, sample for sample, without one instruction of "
          "SOLID")


def like(alone, fw, label):
    """The SOLID track's output identical in two firmwares."""
    bad = []
    for kw, ex in ((KW, dict(trigs=(1, 120))), (dict(KW, shape=127, decay=110), dict(trigs=(1, 120))),
                   (dict(KW, gate=1, contour=127, decay=100), dict(trigs=(1,), rels=(150,)))):
        a, _, _ = play(alone, kw, 250, probe=False, **ex)
        b, _, e = play(fw, kw, 250, probe=False, **ex)
        if not np.array_equal(a, b) or e.unmapped or not a.any():
            bad.append(kw)
    check(not bad, f"{label}: the SOLID track identical to SOLID alone (marimba, glass, GATE with sustained noise) "
                   f"{bad[:1]}")


# --- 5. the sequencer --------------------------------------------------------------------------------------------
def sequence(fw, steps, kw=None, bpm=300, tail=60):
    """Track 1 on SOLID played by the OS's sequencer: steps = [(step, its settings)] (vel, length, note, locks {slot:
    8.8}). Returns (the bench's info a block, Probe, outside memory)."""
    e = fw.engine()
    rig = S.Rig(e, bpm)
    for k, v in dict(KW, **(kw or {})).items():
        if k in E.SLOT:
            rig.param(0, E.SLOT[k], int(round(v * 256)))
    rig.param(0, E.SLOT["machine"], fw.index << 8)
    pr = Probe(fw, e)
    t0 = rig.now + 2 * rig.blk + rig.blk // 3
    last = 0
    for s, st in steps:
        st = dict(st)
        for slot, value in st.pop("locks", {}).items():
            rig.set_lock(0, s, slot, value)
        rig.set_step(0, s, **st)
        rig.schedule_step(0, s, t0 + s * S.STEP)
        last = max(last, s)
    infos = []
    for b in range(int((last + 1) * S.STEP / rig.blk) + tail + 3):
        pr.block = b
        infos.append(rig.block())
    return infos, pr, e.unmapped


def sequencer(fw, ref):
    """Steps two apart at 300 BPM (150 blocks): velocities; then SHAPE p-locked on three of four steps."""
    vels = (127, 40, 100, 10)
    infos, pr, unm = sequence(fw, [(2 * i, dict(vel=v)) for i, v in enumerate(vels)], dict(contour=40))
    out = np.stack([i["out"][0] for i in infos])
    why, _ = pr.verify(ref, 0, out, chain=False)
    got = [r["knobs"][8] for r in pr.recs[0] if r["knobs"][0]]
    want = [v * 258 for v in vels]
    check(not why and got == want and not unm,
          f"the sequencer: each step's velocity {list(vels)} reaches its own strike (the gain of the block after the "
          f"trig), exact {why[:1]}{'' if got == want else f'; strikes saw {[g // 258 for g in got]}'}")
    locks = (0, 127, None, 102)
    steps = [(2 * i, dict(locks={E.SLOT['shape']: v << 8}) if v is not None else dict()) for i, v in enumerate(locks)]
    infos, pr, unm = sequence(fw, steps, dict(decay=100))
    out = np.stack([i["out"][0] for i in infos])
    why, _ = pr.verify(ref, 0, out, chain=False)
    recs = pr.recs[0]
    at = [i for i, r in enumerate(recs) if r["knobs"][0]]
    rows, glide = [], False
    exact_at = True
    for k, i in enumerate(at):
        # up to the next trig's block, which already carries the next step's value (one block before its strike)
        end = at[k + 1] - 1 if k + 1 < len(at) else len(recs)
        seen = [recs[j]["knobs"][3] for j in range(i, end)]
        moves = [j for j in range(1, len(seen)) if seen[j] != seen[j - 1]]
        glide |= bool(moves)
        want_v = (KW["shape"] if locks[k] is None else locks[k]) << 8
        exact_at &= seen[0] == want_v
        lock = f"lock {locks[k]}" if locks[k] is not None else f"no lock ({KW['shape']})"
        rows.append(f"{lock}: the strike sees {seen[0] / 256:.2f}"
                    + (f", then it moves {len(moves)} times, to {seen[-1] / 256:.2f}" if moves
                       else f", held for {len(seen)} blocks"))
    check(not why and len(at) == 4 and not unm, f"the sequencer: SHAPE p-locked on steps, the core exact {why[:1]}")
    info("SHAPE p-locks and the OS's smoother (notes/71 §7): " + "; ".join(rows)
         + (" -> the smoother GLIDES the material after the strike" if glide else
            " -> no glide: the step's value arrives in the trig's block and holds until the next trig")
         + ("" if exact_at else " (a strike did NOT see its step's value)"))


# --- 6. level and cost -------------------------------------------------------------------------------------------
def level(fw):
    """Peak and RMS of the track's output over the first 100 ms (blocks 2..152), before the OS's velocity gain."""
    def meas(machine, kw):
        y, _, _ = play(fw, kw, 152, probe=False, machine=machine)
        z = y[2:152]
        return db(np.abs(z).max()), db(rms(z))
    rows = []
    for m in (TONE, PERC, METAL):
        p, r = meas(m, dict(KW, **dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[m]))))
        rows.append(f"{STOCK[m]} {p:.1f} / {r:.1f}")
    for name, kw in (("SOLID default", KW), ("string", dict(KW, shape=0)), ("membrane", dict(KW, shape=25)),
                     ("bar", dict(KW, shape=76)), ("bell", dict(KW, shape=102)), ("glass", dict(KW, shape=127)),
                     ("burst", dict(KW, contour=80)), ("sustained", dict(KW, contour=127)),
                     ("hard mallet, note 36", dict(KW, contour=63, note=36))):
        p, r = meas(None, kw)
        rows.append(f"{name} {p:.1f} / {r:.1f}")
    info("level, peak / RMS in dB of full scale, note 60, default knobs: " + "; ".join(rows))


def cost(fw, label):
    """Instructions a block: the whole voice loop, less the same loop with every track muted."""
    def run(machine, kw, blocks, trigs=(1,), tracks=(0,)):
        e = fw.engine()
        if machine is not None:
            for t in tracks:
                e.set(t, machine=machine, **kw)
        n = {"i": 0, "sp": 1 << 32}

        def hk(uc, a, s, u):
            n["i"] += 1
            if fw.code[0] <= a < fw.code[1]:
                n["sp"] = min(n["sp"], uc.reg_read(mk.UC_M68K_REG_A7))
        e.uc.hook_add(UC_HOOK_CODE, hk)
        mask = sum(1 << t for t in tracks)
        per = []
        for b in range(blocks):
            i0 = n["i"]
            e.block(mask if b in trigs else 0)
            per.append(n["i"] - i0)
        return np.array(per), n["sp"]
    zero = int(np.median(run(None, KW, 4, trigs=())[0]))
    m = lambda x, a=4: int(np.median(x[a:])) - zero
    stock = {}
    for idx in (TONE, PERC, METAL, KICK, SNARE, CHORD):
        x, _ = run(idx, dict(KW, **dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[idx]))), 24)
        stock[idx] = m(x)
    rows, sps = [], []
    for name, kw in (("marimba, mallet (default)", KW), ("string, note 36", dict(KW, shape=0, note=36)),
                     ("glass, note 60", dict(KW, shape=127)), ("glass, note 96", dict(KW, shape=127, note=96)),
                     ("burst", dict(KW, contour=80)), ("sustained noise", dict(KW, contour=120, decay=100))):
        x, sp = run(fw.index, kw, 24)
        sps.append(sp)
        rows.append(f"{name} {m(x)} (strike's block {int(x[2]) - zero})")
    idle, sp = run(fw.index, dict(KW, decay=0), 300)
    sps.append(sp)
    six_m, sp = run(fw.index, dict(KW, contour=120, decay=100), 24, tracks=range(6))
    sps.append(sp)
    six_t, _ = run(TONE, dict(KW, **dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[TONE]))), 24,
                   tracks=range(6))
    deep = E.STACK - 0x100 - min(sps)
    info(f"{label}: instructions a block of one SOLID voice: " + "; ".join(rows)
         + f"; silent {int(np.median(idle[250:])) - zero}. Stock: "
         + ", ".join(f"{STOCK[k]} {v}" for k, v in stock.items())
         + f". Six SOLID tracks ringing {m(six_m)} against six TONE {m(six_t)} ({m(six_m) / max(m(six_t), 1):.2f}x); "
         f"stack {deep} bytes below the voice loop")


def dry(stock, args):
    """No Unicorn: the firmwares' layout and the host's core."""
    builds = [(["solid"], 8), (["sampler", "solid"], 8)] + [(["solid"], m) for m in args if m != 8]
    for ids, m in builds:
        f = Fw(stock, ids, modes=m)
        print(f"{'+'.join(ids)}, {m} modes: SOLID machine {f.index}, code {f.code[0]:#x}..{f.code[1]:#x}, update "
              f"{f.upd:#x}, render {f.rnd:#x}, variables {f.bss[1]} bytes at {f.bss[0]:#x}, payload "
              f"{len(f.runtime)} bytes")
    with tempfile.TemporaryDirectory() as d:
        for modes in sorted({8} | set(args)):
            ref = Ref(pathlib.Path(d), modes)
            k = [list(x) for x in [[1, 60 << 16, 64 << 8, 51 << 8, 40 << 8, 30 << 8, 80 << 8, 0, 100 * 258, 0, 0]]
                 + [[0, 60 << 16, 64 << 8, 51 << 8, 40 << 8, 30 << 8, 80 << 8, 0, 100 * 258, 0, 0]] * 299]
            y = ref.run(k, seed(0))
            peak = np.abs(to_bus(y, 1)).max(axis=1)
            print(f"host core, {modes} modes: a strike, peak {db(peak.max()):.1f} dB, {db(peak[-1]):.1f} dB at block "
                  f"300, {ref.lib.solid_ref_work()} mode-blocks")
    print("\n(dry run: no emulation)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--quick", action="store_true", help="fewer cases")
    ap.add_argument("--modes", default="8", help="8, or 8,16: the 16-mode build too (needs the m68k toolchain)")
    ap.add_argument("--dry", action="store_true", help="build and lay out only, no emulation")
    args = ap.parse_args()
    modes = sorted({int(x) for x in args.modes.split(",") if x.strip()})
    stock = T.main_os_from_syx(args.cycles)
    if args.dry:
        return dry(stock, modes)
    off, alone = Fw(stock, None), Fw(stock, ["solid"])
    with tempfile.TemporaryDirectory() as d:
        ref = Ref(pathlib.Path(d), 8)
        print(f"== solid: SOLID as machine {alone.index}, code {alone.code[0]:#x}..{alone.code[1]:#x}")
        startup(args.cycles, stock, alone)
        print("the core, exact")
        exact(alone, ref, cases(args.quick), "SOLID alone")
        print("the stock chain")
        chain(alone, ref)
        gate(alone)
        print("the tracks")
        change(alone, ref)
        six(alone, ref)
        mixed(alone, off, ref)
        stock_unchanged(off, alone, "SOLID alone")
        both = Fw(stock, ["sampler", "solid"])
        print(f"\n== sampler+solid: SOLID as machine {both.index}")
        startup(args.cycles, stock, both)
        print("the tracks")
        like(alone, both, "next to SAMPLE")
        stock_unchanged(off, both, "next to SAMPLE")
        print("\nthe sequencer")
        sequencer(alone, ref)
        print("\nlevel and cost")
        level(alone)
        cost(alone, "8 modes")
        if 16 in modes:
            if not shutil.which(compose.gx.CROSS + "gcc"):
                print(f"  skip  16 modes: no {compose.gx.CROSS}gcc here")
            else:
                f16, ref16 = Fw(stock, ["solid"], modes=16), Ref(pathlib.Path(d), 16)
                print(f"\n== solid, 16 modes: code {f16.code[1] - f16.code[0]} bytes, variables {f16.bss[1]} bytes")
                exact(f16, ref16, cases(True)[:8] + cases(True)[-8:], "SOLID, 16 modes")
                cost(f16, "16 modes")
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
