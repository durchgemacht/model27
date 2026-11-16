#!/usr/bin/env python3
"""Max Saw's proof on the OS's own code (notes/84 §10, step 3): the machine as tools/compose.py composes it (alone,
machine 6; next to SAMPLE and next to CHIPS, machine 7), run in Unicorn with its payload as the boot hook leaves it.

  1. Start-up and the registrar, as test_compose.py checks any composed machine: the bootstrap reads the grown OS
     back, the boot hook copies the payload; the tables, lookups, MACHINES page, records and knobs of the machine;
     the shortcut layer told that Max Saw takes MACHINES + PUNCH (its presses' byte 1).
  2. The core, exact: at every block that maxsaw_render does not pause, what it gives the amp chain (the entry of
     AMP_ENV called from Max Saw) is, bit for bit, the same core compiled for the host (tools/emu/maxsaw_ref.c),
     fed the inputs maxsaw_update must take from the voice, the parameters and the note's sound (notes/84 §9.2,
     computed here from memory, not read from the machine), the trig's new phases in the block of +0x38 with that
     block's Phase, the track's seed, and run only through the blocks that are not paused: Detune, Mix, Tone and
     Phase across their range, notes 0 to 127 with and without Sub, Sub in the note's sound, in a preview's copy and in
     a trig's lock, PUNCH, PITCH and FINE, DECAY, GATE, retrigs, knobs moving every block. maxsaw_render is called at
     every block; the first block on Max Saw is a fresh voice; a paused block (no trig in it or the last, the
     envelope below -102 dB) calls neither the core nor the chain and its track is silent; a trig wakes the voice.
  3. The stock chain: in every block not paused maxsaw_render calls AMP_ENV, the VCA and PUNCH, once each, in that
     order, on its output and its voice; the amp envelope's level and the chain's words are TONE's, block for block,
     for the same DECAY, GATE, note ends and trigs (until the envelope closes and Max Saw pauses), except PUNCH's
     output stage (+0x2a4): Max Saw's 0x7fffffff, TONE's 0x20000000 (notes/84 §9.3); PUNCH acts.
  4. The tracks: Max Saw, TONE, Max Saw again: a fresh voice; six Max Saw tracks, each its own knobs and Sub,
     each exact and the same as alone; Max Saw among the stock machines, these identical to the stock OS; the stock
     machines without an Max Saw track identical to the stock OS, without one instruction of Max Saw; Max Saw as
     machine 7 next to SAMPLE and next to CHIPS (which takes k 32's bit 8 on its own tracks) the same as alone.
  5. Measured, not checked: pitch and loudness against TONE, PERC, METAL and CHORD; the level (peak and RMS) next to
     them; the cost, instructions a block of one Max Saw voice against the stock machines, a paused voice, six Ultra
     Saw tracks against six TONE, the stack.

Not here: the sequencer (the trig's lock of k 32 is written into memory as the audio side writes it at the trig,
notes/63 §28; the knobs are the smoothed words every machine reads), the shortcut layer's presses and LEDs
(test_shortcuts.py: the same code for every machine that declares the presses), digiemu and the device.

Needs Unicorn and numpy (pip install unicorn numpy), a C compiler for the host and m68k-elf-objdump. Unicorn's JIT
stops with SIGILL in a sandbox that forbids generated code: run it in a normal terminal. --dry builds and lays out the
firmwares and runs the host core only, without Unicorn.

    python3 tools/emu/test_maxsaw.py --cycles firmware/model-cycles_OS1.13.syx [--quick] [--only chain,measure]

--only runs some parts: startup, core, inputs, chain, tracks, next (the builds next to SAMPLE and CHIPS), compare
(pitch and loudness against the stock machines), measure.
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

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402


PKG = HERE.parent / "machines" / "maxsaw"
MARK = 0x4d585331                   # 'MXS1' at v+0x2c: the track is on Max Saw since its last change of machine
SEED0 = 0x55A7                      # the tracks' random numbers: SEED0 + t x 0x9e3779b9 (maxsaw.c)
AMP_ENV, VCA, PUNCH = 0x400a9252, 0x400a9430, 0x400a967a
KICK, SNARE, METAL, PERC, TONE, CHORD = range(6)
STOCK = {KICK: "KICK", SNARE: "SNARE", METAL: "METAL", PERC: "PERC", TONE: "TONE", CHORD: "CHORD"}
# the manifest's defaults: Detune 64, Mix 95, Tone 32, Phase 127; DECAY 80
KW = dict(note=60, pitch=64, finetune=64, color=64, shape=95, sweep=32, contour=127, punch=0, gate=0, decay=80)
IDLE = 1 << 14                      # maxsaw_render's pause: the envelope's levels below -102 dB
ENV = (0x230, 0x234)                # the amp envelope's level and the VCA's last (negative, 0x80000000 full scale)
CHAIN = (0x250, 0x274, 0x278, 0x27c, 0x280, 0x284, 0x288, 0x290, 0x294, 0x29c, 0x2a0, 0x48)
STAGE = 0x2a4                       # PUNCH's output stage: Max Saw's 0x7fffffff, TONE's 0x20000000 (notes/84 §9.3)
MSAW_STAGE, TONE_STAGE = 0x7fffffff, 0x20000000
# the note's sound (notes/63 §17.2, §28)
CUR_SNDS, TARGETS, MASK = 0x800017ec, 0x800015ae, 0x423087f8
SND, K32 = 0x40781000, 84           # six sounds of 0x80 bytes in the engine's free memory (as test_shortcuts.py)
SUB, SUB_HELD = 0x100, 0x400


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def s32(x):
    return x - (1 << 32) if x & 0x80000000 else x


def mag(x):
    return -x if x < 0 else x


def seed(t):
    return (SEED0 + t * 0x9e3779b9) & 0xffffffff


def to_bus(x):
    """What maxsaw_render makes of the core's Q27: x 2, saturated (8.0 full scale)."""
    return np.where(x > 0x3fffffff, 0x7fffffff, np.where(x < -0x40000000, -0x80000000, x * 2))


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def db(x, ref=2.0 ** 31):
    return 20 * np.log10(max(x, 1e-9) / ref)


def info(msg):
    print(f"  info  {msg}", flush=True)


# The modules that need Unicorn, loaded after the arguments so that --dry runs without it.
E = S = TC = T = X = t7 = TS = None
UC_HOOK_CODE = mk = None


def load_emulation():
    global E, S, TC, T, X, t7, TS, UC_HOOK_CODE, mk
    from unicorn import UC_HOOK_CODE as hc
    from unicorn import m68k_const as m
    import mcengine
    import seqrig
    import test_compose
    import test_sdvintage
    import test_sdvintage_exact
    import test_sdvintage_7th
    import test_syntakt_machines
    UC_HOOK_CODE, mk = hc, m
    E, S, TC, T, X, t7, TS = (mcengine, seqrig, test_compose, test_sdvintage, test_sdvintage_exact,
                              test_sdvintage_7th, test_syntakt_machines)


def check(ok, msg):
    return t7.check(ok, msg)


def stock_kw(m):
    return dict(KW, **dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[m])))


# --- the host's core ---------------------------------------------------------------------------------------------
class Ref:
    """maxsaw.c's core compiled for the host (tools/emu/maxsaw_ref.c)."""

    def __init__(self, tmp):
        cc = shutil.which("cc") or shutil.which("gcc") or "cc"
        so = tmp / "maxsaw_ref.so"
        r = subprocess.run([cc, "-O2", "-std=c99", "-fwrapv", "-Wall", "-Wextra", "-Werror", f"-I{PKG}", "-shared",
                            "-fPIC", "-o", str(so), str(HERE / "maxsaw_ref.c")], capture_output=True, text=True)
        if r.returncode:
            sys.exit("!! the host build of maxsaw_ref.c failed:\n" + r.stderr)
        self.lib = ctypes.CDLL(str(so))
        self.lib.maxsaw_ref_render.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]

    def run(self, words, sd):
        """words: one list of 7 words a block (trig, note, Detune, Mix, Tone, Phase, Sub); the core's output, blocks x
        32, Q27, from a fresh voice with the seed sd."""
        n = len(words)
        out = np.zeros(32 * max(n, 1), dtype=np.int32)
        if n:
            blk = np.ascontiguousarray(np.array(words, dtype=np.int32).reshape(-1))
            self.lib.maxsaw_ref_render(blk.ctypes.data, n, out.ctypes.data, sd)
        return out[:32 * n].reshape(n, 32).astype(np.int64)


# --- the firmwares -----------------------------------------------------------------------------------------------
class Fw:
    """One firmware: the stock OS (ids None) or a composed build; the payload as in memory; Max Saw's place."""

    def __init__(self, stock, ids):
        self.ids, self.tweak, self.runtime = ids, None, None
        self.index, self.code = None, (0, 0)
        if ids is None:
            self.img = bytes(stock)
            return
        tweak, info_ = compose.compose(stock, ids)
        patched, _ = build.apply_writes(stock, [tweak])
        self.runtime = build.payload_runtime(tweak, stock, None)
        self.img = bytes(patched) + build.payload_image(tweak, self.runtime)
        self.tweak, self.info = tweak, info_
        pkg = next((p for p in info_["packages"] if p["id"] == "maxsaw"), None)
        if pkg is None:
            return
        at = pkg["code_at"] if isinstance(pkg["code_at"], int) else int(pkg["code_at"], 16)
        self.index, self.code = pkg["index"], (at, at + pkg["code"])
        self.upd = int(tweak["symbols"]["maxsaw_update"], 16)
        self.rnd = int(tweak["symbols"]["maxsaw_render"], 16)
        self.bss = (pkg["bss_at"], pkg["bss"])

    def engine(self):
        """The voice loop alone; every track muted until a trig gives it a machine; each track's note plays its own
        sound (k 32 0), no lock."""
        e = TC.engine(self.img, self.runtime, self.tweak) if self.runtime else TC.engine(self.img)
        S.ensure_map(e.uc, 0x40800000, 0x01800000)       # the OS's BSS above 0x40800000 (the velocity's gain)
        for t in range(6):
            e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE + 4, struct.pack(">I", TC.MUTED))
            switches(e, t, 0)
        return e


def switches(e, t, sw, preview=False, lock=None):
    """Track t's k 32: in its note's sound (CUR_SNDS[t] -> SND + 0x80 t, +84), or with preview in the copy of the
    sound's 66 bytes only (CUR_SNDS[t] = 0); lock: the word a trig's lock of k 32 put in that copy, with its mask's
    bit (as the audio side writes them at the trig, notes/63 §28)."""
    snd = SND + 0x80 * t
    e.uc.mem_write(snd, bytes(0x80))
    e.uc.mem_write(snd + K32, struct.pack(">H", sw))
    e.uc.mem_write(CUR_SNDS + 4 * t, struct.pack(">I", 0 if preview else snd))
    e.uc.mem_write(TARGETS + 66 * t + 64, struct.pack(">H", lock if lock is not None else sw))
    e.uc.mem_write(MASK + 8 * t + 4, struct.pack(">I", 1 if lock is not None else 0))


# --- what Max Saw receives, gives and should do -----------------------------------------------------------------
class Probe:
    """At every block and for every track watched: the inputs maxsaw_update must take (notes/84 §9.2), whether
    maxsaw_render ran and should pause, what it gave AMP_ENV, and the stock calls it made."""

    def __init__(self, fw, e, tracks=(0,)):
        self.fw, self.tracks, self.block = fw, tuple(tracks), 0
        self.recs = {t: [] for t in self.tracks}
        self.out_at = {}
        uc = self.uc = e.uc
        uc.hook_add(UC_HOOK_CODE, self._upd, begin=fw.upd, end=fw.upd)
        uc.hook_add(UC_HOOK_CODE, self._rnd, begin=fw.rnd, end=fw.rnd)
        uc.hook_add(UC_HOOK_CODE, self._amp, begin=AMP_ENV, end=AMP_ENV)
        uc.hook_add(UC_HOOK_CODE, self._call("vca"), begin=VCA, end=VCA)
        uc.hook_add(UC_HOOK_CODE, self._call("punch"), begin=PUNCH, end=PUNCH)

    def arg(self, k):
        sp = self.uc.reg_read(mk.UC_M68K_REG_A7)
        return struct.unpack(">I", self.uc.mem_read(sp + 4 * k, 4))[0]

    def u32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def u16(self, a):
        return struct.unpack(">H", self.uc.mem_read(a, 2))[0]

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
        note = clamp(pmod + (p16(0x14) << 8) + ((p16(0x22) - 0x4000) << 3) - (64 << 16), 0, 127 << 16)
        cur = self.u32(CUR_SNDS + 4 * t)
        sw = self.u16(cur + K32) if cur else self.u16(TARGETS + 66 * t + 64)
        if self.u32(MASK + 8 * t + 4) & 1:
            lock = self.u16(TARGETS + 66 * t + 64)
            if lock & SUB_HELD:
                sw = (sw & ~SUB) | (lock & SUB)
        # trig (the block of +0x38), note, Detune, Mix, Tone, Phase, Sub
        words = [1 if v32(0x38) else 0, note, p16(0x16), p16(0x18), p16(0x1a), p16(0x1c), 2 if sw & SUB else 0]
        self.recs[t].append(dict(block=self.block, init=v32(0x2c) != MARK, words=words, render=0, paused=None,
                                 done=0, calls=[]))

    def _rnd(self, uc, a, s, u):
        v = self.arg(2)
        t = self.track(v)
        if t in self.tracks and self.recs[t]:
            r = self.recs[t][-1]
            vb = bytes(uc.mem_read(v, 0x238))
            v32 = lambda o: struct.unpack_from(">i", vb, o)[0]
            r["render"] = 1
            r["paused"] = not v32(0x34) and not v32(0x38) and all(mag(v32(o)) < IDLE for o in ENV)
            self.out_at[t] = self.arg(1)

    def _amp(self, uc, a, s, u):
        v = self.arg(1)
        t = self.track(v)
        if t in self.tracks and self.ours() and self.recs[t]:
            r = self.recs[t][-1]
            r["done"] = 1
            r["calls"].append(("amp", v))
            r["pre"] = np.frombuffer(bytes(uc.mem_read(self.out_at[t], 128)), ">i4").astype(np.int64)

    def _call(self, name):
        def hook(uc, a, s, u):
            v = self.arg(2)
            t = self.track(v)
            if t in self.tracks and self.ours() and self.recs[t]:
                self.recs[t][-1]["calls"].append((name, v, self.arg(1) == self.out_at.get(t)))
        return hook

    def verify(self, ref, t, final):
        """final: the track's output, blocks x 32. Returns (what is wrong, measures)."""
        recs, bad = self.recs[t], []
        if not recs:
            return [f"track {t + 1}: no block on Max Saw"], dict(inits=0, paused=0, blocks=0, woke=0)
        starts = [i for i, r in enumerate(recs) if r["init"]]
        if not starts or starts[0] != 0:
            bad.append(f"track {t + 1}: its first block on Max Saw is not a fresh voice")
        unrendered = [r["block"] for r in recs if not r["render"]]
        if unrendered:
            bad.append(f"track {t + 1}: maxsaw_render not called in blocks {unrendered[:4]}")
        v = E.VOICE0 + t * E.VSTRIDE
        woke = 0
        for a, b in zip(starts, starts[1:] + [len(recs)]):
            seg = recs[a:b]
            live = [r for r in seg if not r["paused"]]
            want = ref.run([r["words"] for r in live], seed(t))
            for r, h in zip(live, want):
                if not r["done"]:
                    bad.append(f"track {t + 1} block {r['block']}: not paused, yet the chain was not called")
                    break
                hb = to_bus(h)
                if not np.array_equal(r["pre"], hb):
                    i = int(np.nonzero(r["pre"] != hb)[0][0])
                    bad.append(f"track {t + 1} block {r['block']}: the core differs from the host's at frame {i} "
                               f"({int(r['pre'][i])} against {int(hb[i])})")
                    break
                if r["calls"] != [("amp", v), ("vca", v, True), ("punch", v, True)]:
                    bad.append(f"track {t + 1} block {r['block']}: the chain called {r['calls']}")
                    break
            for i in range(1, len(seg)):
                woke += seg[i - 1]["paused"] and not seg[i]["paused"]
        for r in recs:
            if r["paused"] and (r["done"] or r["calls"] or final[r["block"]].any()):
                bad.append(f"track {t + 1} block {r['block']}: paused, yet {'the chain ran' if r['calls'] else ''}"
                           f"{' its output is not 0' if final[r['block']].any() else ''}")
                break
        return bad, dict(inits=len(starts), paused=sum(1 for r in recs if r["paused"]), blocks=len(recs), woke=woke)


def play(fw, kw, blocks, trigs=(1,), changes=None, rels=(), track=0, probe=True, machine=None, levels=False, sw=0,
         preview=False, env=None):
    """One track on Max Saw (or machine), the others muted. changes: {block: knobs}; rels: blocks with a note's end;
    sw, preview: the track's k 32 (switches()); env: {block: dict(sw=, preview=, lock=)}, written before that block (a
    lock stays until a block that gives another or None). Returns (the track's output, blocks x 32; the Probe; the
    engine[; the envelope's level, the chain's words and the output stage after each block])."""
    e = fw.engine()
    e.set(track, machine=fw.index if machine is None else machine, **kw)
    state = dict(sw=sw, preview=preview, lock=None)
    switches(e, track, sw, preview)
    pr = Probe(fw, e, (track,)) if probe and fw.runtime else None
    out, lv = [], []
    v = E.VOICE0 + track * E.VSTRIDE
    for b in range(blocks):
        for k, x in (changes or {}).get(b, {}).items():
            e.set(track, **{k: x})
        ch = (env or {}).get(b)
        if ch:
            state.update(ch)
            switches(e, track, state["sw"], state["preview"], state["lock"])
        if pr:
            pr.block = b
        out.append(e.block(1 << track if b in trigs else 0, 1 << track if b in rels else 0)[track])
        if levels:
            lv.append(tuple(s32(struct.unpack(">I", e.uc.mem_read(v + o, 4))[0]) for o in (0x230,) + CHAIN + (STAGE,)))
    return (np.stack(out), pr, e) + ((lv,) if levels else ())


# --- 1. start-up and the registrar ------------------------------------------------------------------------------
def startup(cycles, stock, fw):
    print(f"start-up and the registrar ({'+'.join(fw.ids)})")
    X.bootstrap_depack_ok(cycles, fw.tweak, None) or t7.FAIL.append(f"{'+'.join(fw.ids)}: bootstrap")
    X.boot_hook_ok(fw.img, fw.runtime) or t7.FAIL.append(f"{'+'.join(fw.ids)}: boot hook")
    added = TC.configure(fw.ids)
    TC.own_pictures(fw.tweak, fw.runtime, added)
    a, b = TS.tables(stock, fw.img, fw.runtime)
    TS.lookups(a, b)
    TS.accessors(a, b, stock, fw.img)
    TS.screens(stock, fw.img, fw.runtime)
    TS.setter_and_wheel(stock, fw.img, fw.runtime)
    TS.records_and_change(stock, fw.img, fw.runtime)
    TS.out_of_range(stock, fw.img, fw.runtime)
    TS.small_icon(stock, fw.img, fw.runtime)
    # the shortcut layer: its data's first machine and count at +0x10, a byte of presses per machine at +0x14
    # (bit 0: PUNCH, bit 1: GATE; notes/63 §16, test_shortcuts.py)
    e = fw.engine()
    data = int(fw.tweak["symbols"]["sc_data"], 16)
    first, count = e.uc.mem_read(data + 0x10, 2)
    presses = list(e.uc.mem_read(data + 0x14, 8))
    got = presses[fw.index - first] if first <= fw.index < first + count else None
    check(got == 1, f"{'+'.join(fw.ids)}: the shortcut layer takes MACHINES + PUNCH (not GATE) on Max Saw (machine "
                    f"{fw.index}: its presses' byte {got})")


# --- 2. the core, exact ------------------------------------------------------------------------------------------
def cases(quick):
    """(name, knobs, extra for play)."""
    out = [("the defaults", KW, dict(blocks=300, trigs=(1, 150)))]
    for x in ((0, 64, 127) if quick else (0, 8, 16, 32, 48, 64, 80, 96, 112, 120, 127)):
        out.append((f"COLOR {x} (Detune)", dict(KW, color=x, decay=110), dict(blocks=150)))
    for x in ((0, 95, 127) if quick else (0, 16, 32, 48, 64, 80, 95, 110, 127)):
        out.append((f"SHAPE {x} (Mix)", dict(KW, shape=x, decay=110), dict(blocks=150)))
    for x in ((0, 32, 127) if quick else (0, 8, 16, 31, 32, 33, 48, 64, 96, 112, 127)):
        out.append((f"SWEEP {x} (Tone)", dict(KW, sweep=x, decay=110), dict(blocks=150)))
    for x in ((0, 127) if quick else (0, 1, 16, 32, 64, 96, 126, 127)):
        out.append((f"CONTOUR {x} (Phase), a trig every 30 blocks", dict(KW, contour=x, decay=60),
                    dict(blocks=240, trigs=tuple(range(1, 240, 30)))))
    for n in ((0, 48, 127) if quick else (0, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 127)):
        out.append((f"note {n}", dict(KW, note=n, decay=110), dict(blocks=120)))
    for n in ((24, 96) if quick else (0, 12, 24, 48, 72, 96, 127)):
        out.append((f"note {n}, Sub", dict(KW, note=n, decay=110), dict(blocks=120, sw=SUB)))
    out += [
        ("note 127, Detune 127, Mix 127: the top oscillator at its highest", dict(KW, note=127, color=127, shape=127,
                                                                                 decay=110), dict(blocks=150)),
        ("Sub, Tone 0 (the cutoff two octaves below the note)", dict(KW, sweep=0, decay=110), dict(blocks=150, sw=SUB)),
        ("Sub, Tone 127", dict(KW, sweep=127, decay=110), dict(blocks=150, sw=SUB)),
        ("Phase 0, Sub, Detune 0: seven sawtooths in phase", dict(KW, contour=0, color=0, decay=110),
         dict(blocks=200, trigs=(1, 100), sw=SUB)),
        ("PUNCH on", dict(KW, punch=1, decay=110), dict(blocks=150)),
        ("PUNCH flipped every 20 blocks during a note, Sub", dict(KW, decay=127),
         dict(blocks=200, sw=SUB, changes={b: dict(punch=(b // 20) % 2) for b in range(0, 200, 20)})),
        ("Sub switched on in the sound at block 60, off at 140", dict(KW, decay=127),
         dict(blocks=220, env={60: dict(sw=SUB), 140: dict(sw=0)})),
        ("a preview note: Sub in the copy of its sound", dict(KW, decay=110), dict(blocks=150, sw=SUB, preview=True)),
        ("a trig's lock holds Sub on over a sound without, then the next trig without a lock", dict(KW, decay=90),
         dict(blocks=240, trigs=(1, 120), env={1: dict(lock=SUB_HELD | SUB), 120: dict(lock=None)})),
        ("a lock holds Sub off over a sound with Sub", dict(KW, decay=110),
         dict(blocks=150, sw=SUB, env={1: dict(lock=SUB_HELD)})),
        ("a lock that holds no switch", dict(KW, decay=110), dict(blocks=120, sw=SUB, env={1: dict(lock=0)})),
        ("PITCH 0, note 0: the note held at 0", dict(KW, pitch=0, note=0), dict(blocks=120, sw=SUB)),
        ("PITCH 127, note 127, Detune 127", dict(KW, pitch=127, note=127, color=127), dict(blocks=120)),
        ("FINE 0, then FINE 127", dict(KW, finetune=0), dict(blocks=150, changes={75: dict(finetune=127)})),
        ("DECAY 127, 600 blocks", dict(KW, decay=127), dict(blocks=600, sw=SUB)),
        ("DECAY 0: the envelope closes, the voice pauses, a trig wakes it", dict(KW, decay=0),
         dict(blocks=300, trigs=(1, 150, 151, 260), sw=SUB)),
        ("DECAY 40, retrigs", dict(KW, decay=40, contour=64), dict(blocks=400, trigs=(1, 60, 61, 120, 300))),
        ("GATE, the note ends at 120", dict(KW, gate=1, decay=60), dict(blocks=400, rels=(120,))),
        ("trigs in four blocks in a row, the note changing", dict(KW, decay=90, contour=40),
         dict(blocks=200, trigs=(1, 20, 21, 22, 23), changes={21: dict(note=62), 22: dict(note=64), 23: dict(note=65)},
              sw=SUB)),
        ("knobs moving at every block", dict(KW, decay=110),
         dict(blocks=200, trigs=(1, 100), sw=SUB,
              changes={b: dict(color=(3 * b) % 128, shape=127 - (5 * b) % 128, sweep=(7 * b) % 128,
                               contour=(11 * b) % 128, decay=110 - b % 40) for b in range(200)})),
        ("every knob at 0", dict(KW, color=0, shape=0, sweep=0, contour=0, decay=0), dict(blocks=100)),
        ("every knob at its top, Sub", dict(KW, color=127, shape=127, sweep=127, contour=127, decay=127),
         dict(blocks=300, sw=SUB)),
    ]
    return out


def exact(fw, ref, todo, label):
    bad, paused, blocks, woke = [], 0, 0, 0
    for name, kw, ex in todo:
        ex = dict(ex)
        n = ex.pop("blocks")
        y, pr, e = play(fw, kw, n, **ex)
        why, m = pr.verify(ref, 0, y)
        paused += m["paused"]
        blocks += m["blocks"]
        woke += m["woke"]
        if why or e.unmapped or m["inits"] != 1 or not y.any():
            bad.append(name)
            print(f"        DIFF {name}: {why[:2]}, fresh voices {m['inits']}, outside memory {e.unmapped[:2]}")
    check(not bad, f"{label}: at every block not paused, what maxsaw_render gives AMP_ENV is the host's core, bit for "
                   f"bit, fed the inputs maxsaw_update must take, through the blocks not paused; maxsaw_render called "
                   f"at every block; one fresh voice a case ({len(todo)} cases, {blocks} blocks) {bad[:4]}")
    check(not bad and paused > 0 and woke > 0,
          f"{label}: the pause: no trig and the envelope below -102 dB, neither core nor chain runs and the track is "
          f"silent ({paused} blocks); a trig wakes the voice ({woke} times)")
    check(not bad, f"{label}: in every block not paused maxsaw_render calls AMP_ENV, the VCA and PUNCH, once each, "
                   "in that order, on its output and its voice")


def inputs_heard(fw):
    """The inputs act: Sub, Phase (0 against 127 at a retrig), Tone (0 against Szabo's 32) and Detune (0 against 64)
    each change the sound, and a trig's lock of Sub plays as Sub in the sound."""
    base = dict(KW, decay=127)
    n = 300
    trigs = (1, 150)
    plain, _, _ = play(fw, base, n, trigs=trigs, probe=False)
    sub, _, _ = play(fw, base, n, trigs=trigs, probe=False, sw=SUB)
    lock, _, _ = play(fw, base, n, trigs=trigs, probe=False, env={1: dict(lock=SUB_HELD | SUB)})
    ph0, _, _ = play(fw, dict(base, contour=0), n, trigs=trigs, probe=False)
    tone0, _, _ = play(fw, dict(base, sweep=0), n, trigs=trigs, probe=False)
    det0, _, _ = play(fw, dict(base, color=0), n, trigs=trigs, probe=False)
    pairs = dict(sub=(plain, sub), phase=(plain, ph0), tone=(plain, tone0), detune=(plain, det0), lock=(lock, sub))
    differ = {k: not np.array_equal(a, b) for k, (a, b) in pairs.items()}
    ok = differ["sub"] and differ["phase"] and differ["tone"] and differ["detune"] and not differ["lock"]
    check(ok, f"the inputs act: Sub, Phase 0, Tone 0 and Detune 0 each change the sound, and a trig's lock of Sub "
              f"plays as Sub in the sound {differ}")


# --- 3. the stock chain ------------------------------------------------------------------------------------------
def like_tone(fw):
    """The amp envelope and the chain's words of an Max Saw track and of a TONE track, the same DECAY, GATE, note
    ends, trigs and PUNCH: identical after every block, until the envelope closes (Max Saw then pauses, TONE runs on),
    except PUNCH's output stage: 0x7fffffff against TONE's 0x20000000 from the first trig's block on."""
    rows, ok, stages = [], True, set()
    for name, kw, ex in (("DECAY 20", dict(KW, decay=20), dict(blocks=200, trigs=(1, 100))),
                         ("DECAY 64", dict(KW, decay=64), dict(blocks=300, trigs=(1, 150))),
                         ("DECAY 127", dict(KW, decay=127), dict(blocks=300, trigs=(1, 150))),
                         ("GATE, ends at 80 and 230", dict(KW, gate=1, decay=50),
                          dict(blocks=400, trigs=(1, 150), rels=(80, 230))),
                         ("PUNCH, DECAY 90", dict(KW, punch=1, decay=90), dict(blocks=250, trigs=(1, 120))),
                         ("DECAY moving", dict(KW, decay=100),
                          dict(blocks=250, trigs=(1, 120), changes={b: dict(decay=40 + b % 80) for b in range(250)}))):
        _, _, e1, a = play(fw, kw, levels=True, probe=False, **ex)
        _, _, e2, b = play(fw, kw, levels=True, probe=False, machine=TONE, **ex)
        n = next((i for i in range(3, len(b)) if mag(b[i][0]) < IDLE and mag(b[i - 1][0]) < IDLE), len(b))
        same = [x[:-1] for x in a[:n]] == [x[:-1] for x in b[:n]]
        stage = {x[-1] & 0xffffffff for x in a[2:n]}, {x[-1] & 0xffffffff for x in b[2:n]}
        stages |= {(frozenset(stage[0]), frozenset(stage[1]))}
        ok &= same and stage == ({MSAW_STAGE}, {TONE_STAGE}) and not e1.unmapped and not e2.unmapped and n > 20
        rows.append(f"{name}: {'identical' if same else 'DIFFERENT'} over {n} blocks")
    check(ok, "the amp envelope and the chain's words (DECAY's factor, the attack, PUNCH's drive and mix) are TONE's, "
              "block for block; PUNCH's output stage Max Saw's 0x7fffffff (TONE 0x20000000): "
              + "; ".join(rows) + ("" if ok else f"; output stages seen {[(sorted(map(hex, x)), sorted(map(hex, y))) for x, y in stages]}"))
    p, pr, e = play(fw, dict(KW, punch=1, decay=100), 200)
    q, _, _ = play(fw, dict(KW, decay=100), 200, probe=False)
    check(p.any() and not np.array_equal(p, q) and not e.unmapped,
          f"PUNCH: the stock PUNCH acts on the output, peak {db(np.abs(p).max()):.1f} dB "
          f"(without {db(np.abs(q).max()):.1f} dB)")


# --- 4. the tracks -----------------------------------------------------------------------------------------------
def change(fw, ref):
    """Max Saw plays, TONE takes the track (trig at 60), Max Saw again (trig at 120): a fresh voice."""
    y, pr, e = play(fw, dict(KW, decay=127), 260, trigs=(1, 60, 120), sw=SUB,
                    changes={60: dict(machine=TONE), 120: dict(machine=fw.index)})
    why, m = pr.verify(ref, 0, y)
    tone = np.abs(y[62:120]).max()
    check(not why and m["inits"] == 2 and tone > 1e6 and not e.unmapped,
          f"a change of machine: Max Saw, TONE (peak {db(tone):.1f} dB), Max Saw again: a fresh voice, exact "
          f"{why[:1]}")


SIX = [(dict(KW, note=36, decay=90), 0), (dict(KW, note=48, color=100, shape=127, decay=100), SUB),
       (dict(KW, note=55, color=20, sweep=0, decay=60), SUB), (dict(KW, note=60, contour=0, punch=1, decay=110), 0),
       (dict(KW, note=72, color=127, shape=40, sweep=80, decay=70), SUB), (dict(KW, note=84, sweep=120, decay=120), 0)]


def six(fw, ref):
    """Six Max Saw tracks with different knobs and Sub: each exact, and the same as alone."""
    e = fw.engine()
    for t, (kw, sw) in enumerate(SIX):
        e.set(t, machine=fw.index, **kw)
        switches(e, t, sw)
    pr = Probe(fw, e, tuple(range(6)))
    x = []
    for b in range(200):
        pr.block = b
        x.append(e.block(0x3f if b in (1, 100) else 0))
    x = np.stack(x)
    bad = []
    for t in range(6):
        why, _ = pr.verify(ref, t, x[:, t])
        y, _, _ = play(fw, SIX[t][0], 200, trigs=(1, 100), track=t, probe=False, sw=SIX[t][1])
        if why or not np.array_equal(x[:, t], y) or not y.any():
            bad.append(t + 1)
            print(f"        DIFF track {t + 1}: {why[:1]}, same as alone {np.array_equal(x[:, t], y)}")
    check(not bad and not e.unmapped, f"six Max Saw tracks together: each exact (its own knobs, Sub and seed) and "
                                      f"identical to the same track alone {bad}")


def multi(fw, setup, blocks, trigs, sws=None):
    e = fw.engine()
    for t, kw in setup.items():
        e.set(t, **kw)
        switches(e, t, (sws or {}).get(t, 0))
    return np.stack([e.block(trigs.get(b, 0)) for b in range(blocks)]), e.unmapped


def mixed(fw, off):
    """Max Saw on tracks 2 and 5 among KICK, METAL, PERC and CHORD: the stock tracks identical to the stock OS, the
    Max Saw tracks identical to alone."""
    mach = [KICK, fw.index, METAL, PERC, fw.index, CHORD]
    ours = {1: (dict(KW, decay=60, color=90), SUB), 4: (dict(KW, note=48, shape=127, sweep=64, decay=60), 0)}
    setup = {t: dict(ours[t][0], machine=m) if t in ours else dict(stock_kw(m), machine=m) for t, m in enumerate(mach)}
    sws = {t: ours[t][1] for t in ours}
    trigs = {1: 0x3f, 150: 0x3f}
    x, unm = multi(fw, setup, 300, trigs, sws)
    r, unm_r = multi(off, {t: dict(kw, machine=KICK if t in ours else kw["machine"]) for t, kw in setup.items()},
                     300, trigs)
    ok = not unm and not unm_r
    for t in range(6):
        if t in ours:
            y, _, _ = play(fw, ours[t][0], 300, trigs=(1, 150), track=t, probe=False, sw=ours[t][1])
            ok &= np.array_equal(x[:, t], y) and y.any()
        else:
            ok &= np.array_equal(x[:, t], r[:, t]) and r[:, t].any()
    check(ok, "Max Saw on tracks 2 and 5 among KICK, METAL, PERC, CHORD: the stock tracks identical to the stock OS, "
              "the Max Saw tracks identical to alone")


def stock_unchanged(off, fw, label):
    """The six stock machines, no Max Saw track: identical to the stock OS, without one instruction of Max Saw."""
    def run(f, hook):
        e = f.engine()
        for t in range(6):
            e.set(t, **dict(stock_kw(t), machine=t))
        ran = []
        if hook:
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=f.code[0], end=f.code[1] - 1)
        x = np.stack([e.block(0x3f if b in (1, 150) else 0) for b in range(300)])
        return x, ran, e.unmapped
    r, _, _ = run(off, False)
    x, ran, unm = run(fw, True)
    check(np.array_equal(r, x) and np.abs(x).max() > 1e7 and not ran and not unm,
          f"{label}: the six stock machines identical to the stock OS, sample for sample, without one instruction of "
          "Max Saw")


def like(alone, fw, label):
    """The Max Saw track's output identical in two firmwares (its seed is its track's: the same in both)."""
    bad = []
    for kw, ex in ((KW, dict(trigs=(1, 120))),
                   (dict(KW, color=110, shape=127, sweep=0, decay=110), dict(trigs=(1, 120), sw=SUB)),
                   (dict(KW, gate=1, decay=30, contour=0), dict(trigs=(1, 200), rels=(100,)))):
        a, _, _ = play(alone, kw, 250, probe=False, **ex)
        b, _, e = play(fw, kw, 250, probe=False, **ex)
        if not np.array_equal(a, b) or e.unmapped or not a.any():
            bad.append(kw)
    check(not bad, f"{label}: the Max Saw track identical to Max Saw alone (the defaults; wide with Sub and Tone 0; "
                   f"GATE with a pause and Phase 0) {bad[:1]}")


# --- 5. measured -------------------------------------------------------------------------------------------------
LEVELS = (("the defaults", KW, 0), ("Detune 0", dict(KW, color=0), 0), ("Detune 127", dict(KW, color=127), 0),
          ("Mix 0", dict(KW, shape=0), 0), ("Mix 127", dict(KW, shape=127), 0), ("Sub", KW, SUB),
          ("Tone 0", dict(KW, sweep=0), 0), ("Tone 96", dict(KW, sweep=96), 0), ("Phase 0", dict(KW, contour=0), 0),
          ("PUNCH on", dict(KW, punch=1), 0), ("note 36", dict(KW, note=36), 0), ("note 84", dict(KW, note=84), 0))


def level(fw):
    """Peak and RMS of the track's output over blocks 2..152 (the first 100 ms) and 2..752 (0.5 s, DECAY 127),
    before the OS's velocity gain."""
    def meas(machine, kw, sw=0, n=152):
        y, _, _ = play(fw, kw, n, probe=False, machine=machine, sw=sw)
        z = y[2:n]
        return db(np.abs(z).max()), db(rms(z))
    rows = []
    for m in (TONE, PERC, METAL, CHORD):
        p, r = meas(m, stock_kw(m))
        rows.append(f"{STOCK[m]} {p:.1f} / {r:.1f}")
    for name, kw, sw in LEVELS:
        p, r = meas(None, kw, sw)
        p2, r2 = meas(None, dict(kw, decay=127), sw, 752)
        rows.append(f"{name} {p:.1f} / {r:.1f} (0.5 s at DECAY 127: {p2:.1f} / {r2:.1f})")
    info("level, peak / RMS in dB of full scale, note 60: " + "; ".join(rows))


def k_weight(x):
    """ITU-R BS.1770-4's K-weighting at 48 kHz (the high shelf, then the high-pass), x in full scale."""
    def biquad(x, b, a):
        y = np.zeros_like(x)
        x1 = x2 = y1 = y2 = 0.0
        for i, v in enumerate(x):
            o = b[0] * v + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
            x2, x1, y2, y1 = x1, v, y1, o
            y[i] = o
        return y
    x = biquad(x, (1.53512485958697, -2.69169618940638, 1.19839281085285), (1.0, -1.69065929318241, 0.73248077421585))
    return biquad(x, (1.0, -2.0, 1.0), (1.0, -1.99004745483398, 0.99007225036621))


def loudness(y):
    """BS.1770's loudness of a mono track over the whole window, without gating: -0.691 + 10 log10(mean K-weighted
    square), in LUFS (full scale = the bus's 2^31)."""
    k = k_weight(np.asarray(y, dtype=np.float64).reshape(-1) / 2.0 ** 31)
    return -0.691 + 10 * np.log10(max(np.mean(k * k), 1e-20))


def fundamental(y):
    """The period by the normalized autocorrelation (lags 20 to 2 000 frames, 24 Hz to 2.4 kHz): the shortest lag whose
    correlation reaches 0.9 of the best, refined by a parabola; in Hz, and as a note (69 = 440 Hz)."""
    x = np.asarray(y, dtype=np.float64).reshape(-1)
    x = x - x.mean()
    n = len(x)
    f = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:2001]
    if ac[0] <= 0:
        return 0.0, 0.0
    r = ac / ac[0]
    best = r[20:2001].max()
    lag = next(i for i in range(20, 2001) if r[i] >= 0.9 * best and r[i] >= r[i - 1] and r[i] >= r[i + 1])
    d = 0.5 * (r[lag - 1] - r[lag + 1]) / (r[lag - 1] - 2 * r[lag] + r[lag + 1]) if lag < 2000 else 0.0
    hz = 48000.0 / (lag + d)
    return hz, 69 + 12 * np.log2(hz / 440.0)


def compare(fw):
    """Pitch and loudness against the stock machines, each at note 60 and DECAY 127 (the same envelope for all), over
    0.5 s from the trig (blocks 2..752): BS.1770's loudness (LUFS); the fundamental where the seven agree (Detune 0)."""
    rows = []
    sounds = [(STOCK[m], m, dict(stock_kw(m), decay=127), 0, False) for m in (TONE, PERC, METAL, CHORD)]
    sounds += [("Max Saw, the defaults", None, dict(KW, decay=127), 0, False),
               ("Max Saw, Detune 0", None, dict(KW, color=0, decay=127), 0, True),
               ("Max Saw, Detune 0, Sub", None, dict(KW, color=0, decay=127), SUB, True),
               ("Max Saw, Mix 0", None, dict(KW, shape=0, decay=127), 0, False),
               ("Max Saw, Mix 127", None, dict(KW, shape=127, decay=127), 0, False),
               ("Max Saw, Sub", None, dict(KW, decay=127), SUB, False),
               ("Max Saw, Tone 96", None, dict(KW, sweep=96, decay=127), 0, False)]
    ref = None
    for name, m, kw, sw, pitch in sounds:
        y, _, _ = play(fw, kw, 752, probe=False, machine=m, sw=sw)
        z = y[2:752]
        lu = loudness(z)
        if m == TONE:
            ref = lu
        txt = ""
        if pitch or m is not None:
            hz, note = fundamental(z[150:])
            txt = f", fundamental {hz:.1f} Hz (note {note:.1f})"
        rows.append(f"{name}: {lu:.1f} LUFS{'' if ref is None else f' ({lu - ref:+.1f} against TONE)'}{txt}")
    info("note 60, DECAY 127, 0.5 s: " + "; ".join(rows))


def cost(fw, label):
    """Instructions a block: the whole voice loop, less the same loop with every track muted."""
    def run(machine, kw, blocks, trigs=(1,), tracks=(0,), sw=0):
        e = fw.engine()
        if machine is not None:
            for t in tracks:
                e.set(t, machine=machine, **kw)
                switches(e, t, sw)
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
    m = lambda x, a=6: int(np.median(x[a:])) - zero
    hi = lambda x, a=6: int(np.max(x[a:])) - zero
    stock = {}
    for idx in (TONE, PERC, METAL, KICK, SNARE, CHORD):
        x, _ = run(idx, stock_kw(idx), 24)
        stock[idx] = m(x)
    rows, sps = [], []
    for name, kw, sw in (("the defaults", dict(KW, decay=127), 0), ("Detune 127", dict(KW, color=127, decay=127), 0),
                         ("Mix 0", dict(KW, shape=0, decay=127), 0), ("Sub", dict(KW, decay=127), SUB),
                         ("PUNCH on", dict(KW, punch=1, decay=127), 0), ("note 24", dict(KW, note=24, decay=127), 0),
                         ("note 96", dict(KW, note=96, decay=127), 0), ("Tone 127", dict(KW, sweep=127, decay=127), 0)):
        x, sp = run(fw.index, kw, 40, sw=sw)
        sps.append(sp)
        rows.append(f"{name} {m(x)} (most {hi(x)}, the trig's block {int(x[2]) - zero})")
    x, sp = run(fw.index, dict(KW, contour=0, decay=127), 80, trigs=tuple(range(1, 80, 10)), sw=SUB)
    sps.append(sp)
    rows.append(f"Phase 0, a trig every 10 blocks, Sub: mean {int(np.mean(x[6:])) - zero} (most {hi(x)})")
    idle, sp = run(fw.index, dict(KW, decay=0), 300)
    sps.append(sp)
    six_u, sp = run(fw.index, dict(KW, decay=127), 40, tracks=range(6), sw=SUB)
    sps.append(sp)
    six_t, _ = run(TONE, stock_kw(TONE), 40, tracks=range(6))
    deep = E.STACK - 0x100 - min(sps)
    info(f"{label}: instructions a block of one Max Saw voice: " + "; ".join(rows)
         + f"; paused {int(np.median(idle[250:])) - zero}. Stock: "
         + ", ".join(f"{STOCK[k]} {v}" for k, v in stock.items())
         + f". Six Max Saw tracks (Sub) {m(six_u)} against six TONE {m(six_t)} "
         f"({m(six_u) / max(m(six_t), 1):.2f}x); stack {deep} bytes below the voice loop")


def dry(stock):
    """No Unicorn: the firmwares' layout and the host's core."""
    for ids in (["maxsaw"], ["sampler", "maxsaw"], ["chips", "maxsaw"]):
        f = Fw(stock, ids)
        print(f"{'+'.join(ids)}: Max Saw machine {f.index}, code {f.code[0]:#x}..{f.code[1]:#x}, update {f.upd:#x}, "
              f"render {f.rnd:#x}, variables {f.bss[1]} bytes at {f.bss[0]:#x}, payload {len(f.runtime)} bytes; "
              f"the shortcut layer's data at {f.tweak['symbols']['sc_data']}")
    with tempfile.TemporaryDirectory() as d:
        ref = Ref(pathlib.Path(d))
        k = [[1 if b == 1 else 0, 60 << 16, 64 << 8, 95 << 8, 32 << 8, 127 << 8, 0] for b in range(300)]
        y = to_bus(ref.run(k, seed(0)))
        print(f"host core, the defaults: 300 blocks, peak {db(np.abs(y).max()):.1f} dB, RMS {db(rms(y)):.1f} dB of the "
              f"bus's full scale, before the chain (a track: the bus x 4 x 0x2a0 x 0x2a4 x 1/2 = / 2)")
    print("\n(dry run: no emulation)")
    return 0


PARTS = ("startup", "core", "inputs", "chain", "tracks", "next", "compare", "measure")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--quick", action="store_true", help="fewer cases")
    ap.add_argument("--dry", action="store_true", help="build and lay out only, no emulation")
    ap.add_argument("--only", default=",".join(PARTS), help="the parts to run: " + ", ".join(PARTS) + " (default: all)")
    args = ap.parse_args()
    parts = set(x.strip() for x in args.only.split(",") if x.strip())
    bad_parts = parts - set(PARTS)
    if bad_parts:
        sys.exit(f"!! --only: unknown parts {sorted(bad_parts)}")
    import test_sdvintage as tsv           # the official file's MAIN OS (no Unicorn needed for this)
    stock = tsv.main_os_from_syx(args.cycles)
    if args.dry:
        return dry(stock)
    load_emulation()
    off, alone = Fw(stock, None), Fw(stock, ["maxsaw"])
    with tempfile.TemporaryDirectory() as d:
        ref = Ref(pathlib.Path(d))
        print(f"== maxsaw: Max Saw as machine {alone.index}, code {alone.code[0]:#x}..{alone.code[1]:#x}")
        if "startup" in parts:
            startup(args.cycles, stock, alone)
        if "core" in parts:
            print("the core, exact")
            exact(alone, ref, cases(args.quick), "Max Saw alone")
        if "inputs" in parts:
            print("the inputs")
            inputs_heard(alone)
        if "chain" in parts:
            print("the stock chain")
            like_tone(alone)
        if "tracks" in parts:
            print("the tracks")
            change(alone, ref)
            six(alone, ref)
            mixed(alone, off)
            stock_unchanged(off, alone, "Max Saw alone")
        if "next" in parts:
            for other in ("sampler", "chips"):
                both = Fw(stock, [other, "maxsaw"])
                print(f"\n== {other}+maxsaw: Max Saw as machine {both.index}")
                if "startup" in parts:
                    startup(args.cycles, stock, both)
                print("the tracks")
                like(alone, both, f"next to {other.upper()}")
                stock_unchanged(off, both, f"next to {other.upper()}")
        if "compare" in parts:
            print("\npitch and loudness against the stock machines")
            compare(alone)
        if "measure" in parts:
            print("\nlevel and cost")
            level(alone)
            cost(alone, "one voice")
        if parts != set(PARTS):
            print(f"\n(only {', '.join(sorted(parts))})")
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
