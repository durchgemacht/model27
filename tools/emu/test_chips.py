#!/usr/bin/env python3
"""CHIPS's proof on the OS's own code (notes/83 §5, step 3): the machine as tools/compose.py composes it (alone,
machine 6; next to SAMPLE, machine 7), run in Unicorn with its payload as the boot hook leaves it.

  1. Start-up and the registrar, as test_compose.py checks any composed machine: the bootstrap reads the grown OS
     back, the boot hook copies the payload; the tables, lookups, MACHINES page, records and knobs of the machine;
     the shortcut layer told that CHIPS takes MACHINES + PUNCH and MACHINES + GATE (its presses' byte 3).
  2. The core, exact: at every block that chips_render does not pause, what it gives the amp chain (the entry of
     AMP_ENV called from CHIPS) is, bit for bit, the same core compiled for the host (tools/emu/chips_ref.c), fed the
     inputs chips_update must take from the voice, the parameters, the note's sound and the song's tempo (notes/83
     §4.1, computed here from memory, not read from the machine) and run only through the blocks that are not paused:
     the four knobs across their range, every SHAPE (Plaits' eleven chords, notes/83 §10), the divisions and the
     free tempo, the sweep both ways, notes 0
     to 127 with and without the bass, the bass above 750 Hz, PUNCH (the bass's level) also flipped during a note,
     the switches in the note's sound, in a preview's copy and in a trig's lock, the tempo from 60 to 546 BPM and
     changing, PITCH and FINE, DECAY, GATE, retrigs, knobs moving every block. chips_render is called at every block;
     the first block on CHIPS is a fresh voice; a paused block (no trig in it or the last, the envelope below
     -102 dB) calls neither the core nor the chain and its track is silent; a trig wakes the voice where it stood.
  3. The stock chain: in every block not paused chips_render calls AMP_ENV, the VCA and PUNCH, once each, in that
     order, on its output and its voice; the amp envelope's level and the chain's words are TONE's, block for block,
     for the same DECAY, GATE, note ends and trigs (until the envelope closes and CHIPS pauses), PUNCH's output stage
     (+0x2a4) TONE's 1/4 too (since 2026-11-15, notes/83 §7; SOLID's and SWARM's are 6 dB louder); PUNCH acts.
  4. The tracks: CHIPS, TONE, CHIPS again: a fresh voice; six CHIPS tracks, each its own knobs and switches, each
     exact and the same as alone; CHIPS among the stock machines, these identical to the stock OS; the stock machines
     without a CHIPS track identical to the stock OS, without one instruction of CHIPS; CHIPS as machine 7 next to
     SAMPLE the same as alone.
  5. The display (notes/83 §8, §10), the OS's value window (0x4001d818, the knob view) and the text of a value through
     a track's parameter object (vtable 0x400fd134 +60): CHIPS's Chord shows its chord's name (OCT .. M) written by
     the window in its big font as a number, its Arp 1/4 .. 1/32 and 16HZ .. 64HZ drawn once in the narrow big font,
     each centred where a number goes, inside the window's right half; the pictures the stock ones (notes/83 §11);
     every stock descriptor's window and text as on
     the stock OS, CHIPS's other knobs as SNARE's (whose objects they share), SAMPLE's next to CHIPS as without it. The
     object's check of a value (vt[24]) accepts it: for most stock descriptors it asks the track, which the test's
     object has not; a window or text the test cannot build must stop at the same place in both builds, and is counted.
  6. Measured, not checked: the level next to TONE, PERC, METAL and CHORD, and the cost, instructions a block of one
     CHIPS voice (a mono square, the bass, the arpeggio, the sweep, a paused voice) against the stock machines, six
     CHIPS tracks, the stack.

Not here: the sequencer (the trig's lock of k 32 is written into memory as the audio side writes it at the trig,
notes/63 §28; the knobs are the smoothed words every machine reads), the shortcut layer's presses and LEDs
(test_shortcuts.py, on REF2 and SAMPLE: the same code for every machine that declares the presses), the governor of
the Syntakt engines, digiemu and the device.

Needs Unicorn and numpy (pip install unicorn numpy), a C compiler for the host and m68k-elf-objdump. Unicorn's JIT
stops with SIGILL in a sandbox that forbids generated code: run it in a normal terminal. --dry builds and lays out the
firmwares and the host core only, without Unicorn. Duration: not measured yet.

    python3 tools/emu/test_chips.py --cycles firmware/model-cycles_OS1.13.syx [--quick] [--only chain,measure]

--only runs some parts: startup, core, inputs, chain, tracks, next (the build next to SAMPLE), display, compare (pitch
and loudness against the stock machines), measure.
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


PKG = HERE.parent / "machines" / "chips"
MARK = 0x43485031                   # 'CHP1' at v+0x2c: the track is on CHIPS since its last change of machine
AMP_ENV, VCA, PUNCH = 0x400a9252, 0x400a9430, 0x400a967a
KICK, SNARE, METAL, PERC, TONE, CHORD = range(6)
STOCK = {KICK: "KICK", SNARE: "SNARE", METAL: "METAL", PERC: "PERC", TONE: "TONE", CHORD: "CHORD"}
# the manifest's defaults: Wave 64, Chord 0 (one tone), Sweep 64, Arp 41 (1/16; no off since 2026-11-16, notes/83
# §9); DECAY 64
KW = dict(note=60, pitch=64, finetune=64, color=64, shape=0, sweep=64, contour=41, punch=0, gate=0, decay=64)
IDLE = 1 << 14                      # chips_render's pause: the envelope's levels below -102 dB
ENV = (0x230, 0x234)                # the amp envelope's level and the VCA's last (negative, 0x80000000 full scale)
CHAIN = (0x250, 0x274, 0x278, 0x27c, 0x280, 0x284, 0x288, 0x290, 0x294, 0x29c, 0x2a0, 0x48)
STAGE = 0x2a4                       # PUNCH's output stage: CHIPS's TONE's 0x20000000 (notes/83 §7)
# the note's sound and the song's tempo (notes/63 §17.2, §28; notes/38)
CUR_SNDS, TARGETS, MASK, TEMPO = 0x800017ec, 0x800015ae, 0x423087f8, 0x40149310
SND, K32 = 0x40781000, 84           # six sounds of 0x80 bytes in the engine's free memory (as test_shortcuts.py)
BASS, UPDOWN, BASS_HELD, UPDOWN_HELD = 0x100, 0x200, 0x400, 0x800
T120 = 120 * 120                    # 0x40149310 at 120 BPM (1/120 BPM)
# SHAPE: Plaits' eleven chords, one a step (notes/83 §10), within one octave: OCT one tone; m7 0 3 7 10; m9 0 2 3 10;
# M7 0 4 7 11; M 0 4 7
CHORD_NAMES = ("OCT", "5", "SUS", "m", "m7", "m9", "m11", "69", "M9", "M7", "M")
NCHORD = len(CHORD_NAMES)
ZONE = [next(v for v in range(128) if v * NCHORD // 128 == k) for k in range(NCHORD)]   # each chord's first value
ZONE_END = [z - 1 for z in ZONE[1:]] + [127]
OCT, M7, M9_MINOR, MAJ7, MAJ = 0, 52, 64, 110, 122  # SHAPE inside the zones of OCT, m7, m9, M7, M (notes/83 §11)


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def s32(x):
    return x - (1 << 32) if x & 0x80000000 else x


def mag(x):
    return -x if x < 0 else x


def to_bus(x):
    """What chips_render makes of the core's Q27: Q31, saturated, 1.0 full scale."""
    return np.where(x > 0x7ffffff, 0x7fffffff, np.where(x < -0x8000000, -0x80000000, x * 16))


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def db(x, ref=2.0 ** 31):
    return 20 * np.log10(max(x, 1e-9) / ref)


def info(msg):
    print(f"  info  {msg}", flush=True)


# The modules that need Unicorn, loaded after the arguments so that --dry runs without it.
E = S = TC = T = X = t7 = TS = L = None
UC_HOOK_CODE = mk = None


def load_emulation():
    global E, S, TC, T, X, t7, TS, L, UC_HOOK_CODE, UcError, mk
    from unicorn import UC_HOOK_CODE as hc, UcError as ue
    from unicorn import m68k_const as m
    import lofi_ui
    import mcengine
    import seqrig
    import test_compose
    import test_sdvintage
    import test_sdvintage_exact
    import test_sdvintage_7th
    import test_syntakt_machines
    UC_HOOK_CODE, UcError, mk = hc, ue, m
    E, S, TC, T, X, t7, TS, L = (mcengine, seqrig, test_compose, test_sdvintage, test_sdvintage_exact,
                                 test_sdvintage_7th, test_syntakt_machines, lofi_ui)


def check(ok, msg):
    return t7.check(ok, msg)


def stock_kw(m):
    return dict(KW, **dict(zip(("color", "shape", "sweep", "contour", "decay"), E.DEFAULTS[m])))


# --- the host's core ---------------------------------------------------------------------------------------------
class Ref:
    """chips.c's core compiled for the host (tools/emu/chips_ref.c)."""

    def __init__(self, tmp):
        cc = shutil.which("cc") or shutil.which("gcc") or "cc"
        so = tmp / "chips_ref.so"
        r = subprocess.run([cc, "-O2", "-std=c99", "-fwrapv", "-Wall", "-Wextra", "-Werror", f"-I{PKG}", "-shared",
                            "-fPIC", "-o", str(so), str(HERE / "chips_ref.c")], capture_output=True, text=True)
        if r.returncode:
            sys.exit("!! the host build of chips_ref.c failed:\n" + r.stderr)
        self.lib = ctypes.CDLL(str(so))
        self.lib.chips_ref_render.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

    def run(self, words):
        """words: one list of 10 words a block (struct chips_in); the core's output, blocks x 32, Q27."""
        n = len(words)
        out = np.zeros(32 * max(n, 1), dtype=np.int32)
        if n:
            blk = np.ascontiguousarray(np.array(words, dtype=np.int32).reshape(-1))
            self.lib.chips_ref_render(blk.ctypes.data, n, out.ctypes.data)
        return out[:32 * n].reshape(n, 32).astype(np.int64)


# --- the firmwares -----------------------------------------------------------------------------------------------
class Fw:
    """One firmware: the stock OS (ids None) or a composed build; the payload as in memory; CHIPS's place."""

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
        pkg = next((p for p in info_["packages"] if p["id"] == "chips"), None)
        if pkg is None:                                     # a build without CHIPS (SAMPLE alone, for the display)
            return
        at = pkg["code_at"] if isinstance(pkg["code_at"], int) else int(pkg["code_at"], 16)
        self.index, self.code = pkg["index"], (at, at + pkg["code"])
        self.upd = int(tweak["symbols"]["chips_update"], 16)
        self.rnd = int(tweak["symbols"]["chips_render"], 16)
        self.bss = (pkg["bss_at"], pkg["bss"])

    def engine(self, tempo=T120):
        """The voice loop alone; every track muted until a trig gives it a machine; each track's note plays its own
        sound (k 32 0), no lock, the song at tempo."""
        e = TC.engine(self.img, self.runtime, self.tweak) if self.runtime else TC.engine(self.img)
        S.ensure_map(e.uc, 0x40800000, 0x01800000)       # the OS's BSS above 0x40800000 (the velocity's gain)
        for t in range(6):
            e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE + 4, struct.pack(">I", TC.MUTED))
            switches(e, t, 0)
        e.uc.mem_write(TEMPO, struct.pack(">i", tempo))
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


# --- what CHIPS receives, gives and should do ---------------------------------------------------------------------
class Probe:
    """At every block and for every track watched: the inputs chips_update must take (notes/83 §4.1), whether
    chips_render ran and should pause, what it gave AMP_ENV, and the stock calls it made."""

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
            if lock & BASS_HELD:
                sw = (sw & ~BASS) | (lock & BASS)
            if lock & UPDOWN_HELD:
                sw = (sw & ~UPDOWN) | (lock & UPDOWN)
        tempo = s32(self.u32(TEMPO))
        # struct chips_in: trig, note, COLOR, SHAPE, SWEEP, CONTOUR, bass, updown, bpm 8.8, PUNCH
        words = [1 if v32(0x38) else 0, note, p16(0x16), p16(0x18), p16(0x1a), p16(0x1c), 1 if sw & BASS else 0,
                 1 if sw & UPDOWN else 0, tempo * 32 // 15, 1 if p16(0x1e) else 0]
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
            return [f"track {t + 1}: no block on CHIPS"], dict(inits=0, paused=0, blocks=0, woke=0)
        starts = [i for i, r in enumerate(recs) if r["init"]]
        if not starts or starts[0] != 0:
            bad.append(f"track {t + 1}: its first block on CHIPS is not a fresh voice")
        unrendered = [r["block"] for r in recs if not r["render"]]
        if unrendered:
            bad.append(f"track {t + 1}: chips_render not called in blocks {unrendered[:4]}")
        v = E.VOICE0 + t * E.VSTRIDE
        woke = 0
        for a, b in zip(starts, starts[1:] + [len(recs)]):
            seg = recs[a:b]
            live = [r for r in seg if not r["paused"]]
            want = ref.run([r["words"] for r in live])
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
         preview=False, tempo=T120, env=None):
    """One track on CHIPS (or machine), the others muted. changes: {block: knobs}; rels: blocks with a note's end;
    sw, preview: the track's k 32 (switches()); env: {block: dict(sw=, preview=, lock=, tempo=)}, written before
    that block (a lock stays until a block that gives another or None). Returns (the track's output, blocks x 32;
    the Probe; the engine[; the envelope's level and the chain's words after each block])."""
    e = fw.engine(tempo)
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
            if "tempo" in ch:
                e.uc.mem_write(TEMPO, struct.pack(">i", ch["tempo"]))
            state.update({k: x for k, x in ch.items() if k != "tempo"})
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
    # (bits 0 and 1: PUNCH and GATE; notes/63 §16, test_shortcuts.py)
    e = fw.engine()
    data = int(fw.tweak["symbols"]["sc_data"], 16)
    first, count = e.uc.mem_read(data + 0x10, 2)
    presses = list(e.uc.mem_read(data + 0x14, 8))
    ok = first <= fw.index < first + count and presses[fw.index - first] == 3
    check(ok, f"{'+'.join(fw.ids)}: the shortcut layer takes MACHINES + PUNCH and MACHINES + GATE on CHIPS (machine "
              f"{fw.index}: its presses' byte {presses[fw.index - first] if first <= fw.index < first + count else None})")


# --- 2. the core, exact ------------------------------------------------------------------------------------------
def cases(quick):
    """(name, knobs, extra for play)."""
    m7 = M7
    out = [("the defaults (one tone: the root alone)", KW, dict(blocks=300, trigs=(1, 150)))]
    for x in ((0, 64, 127) if quick else (0, 16, 32, 48, 63, 64, 65, 80, 96, 112, 127)):
        out.append((f"COLOR {x}", dict(KW, color=x, decay=110), dict(blocks=150)))
    for c in ((0, 11, 47, 127) if quick else sorted(set(ZONE + ZONE_END))):
        out.append((f"SHAPE {c} ({CHORD_NAMES[c * NCHORD // 128]}), the arpeggio at 50 Hz, the bass",
                    dict(KW, shape=c, contour=116, decay=110),
                    dict(blocks=200, sw=BASS)))
    out.append(("SHAPE m7 then M9 then OCT during a note, up and down at 1/32", dict(KW, shape=52, contour=59,
                                                                                     decay=127),
                dict(blocks=300, sw=UPDOWN, changes={100: dict(shape=99), 200: dict(shape=0)})))
    for x in ((0, 41, 64, 127) if quick else (0, 1, 5, 14, 23, 32, 41, 50, 59, 63, 64, 80, 96, 116, 127)):
        out.append((f"CONTOUR {x}, m7", dict(KW, shape=m7, contour=x, decay=110), dict(blocks=250, trigs=(1, 120))))
    for x in ((0, 64, 127) if quick else (0, 20, 50, 64, 78, 98, 120, 127)):
        out.append((f"SWEEP {x}, the bass, a trig every 30 blocks", dict(KW, sweep=x, decay=50),
                    dict(blocks=240, trigs=tuple(range(1, 240, 30)), sw=BASS)))
    for n in ((0, 36, 96, 127) if quick else (0, 12, 24, 36, 48, 60, 72, 84, 90, 96, 102, 108, 120, 127)):
        out.append((f"note {n}, M at 50 Hz, the bass", dict(KW, note=n, shape=MAJ, contour=116, decay=110),
                    dict(blocks=120, sw=BASS)))
    out += [
        ("the bass above 750 Hz: note 100, COLOR 127", dict(KW, note=100, color=127, decay=110),
         dict(blocks=150, sw=BASS)),
        ("the bass at 2 kHz: note 108, sweep from above", dict(KW, note=108, sweep=127, decay=110),
         dict(blocks=150, sw=BASS)),
        ("PUNCH on, the bass", dict(KW, punch=1, decay=110), dict(blocks=150, sw=BASS)),
        ("PUNCH flipped every 20 blocks during a note, the bass, m7 at 1/16", dict(KW, shape=m7, contour=41, decay=127),
         dict(blocks=200, sw=BASS, changes={b: dict(punch=(b // 20) % 2) for b in range(0, 200, 20)})),
        ("up and down, m7 at 1/32", dict(KW, shape=m7, contour=59, decay=110), dict(blocks=250, sw=UPDOWN)),
        ("the bass and up and down, m9 at 40 Hz", dict(KW, shape=M9_MINOR, contour=106, decay=110),
         dict(blocks=250, sw=BASS | UPDOWN)),
        ("the bass switched on in the sound at block 60, off at 140", dict(KW, shape=m7, contour=96, decay=127),
         dict(blocks=220, env={60: dict(sw=BASS), 140: dict(sw=0)})),
        ("a preview note: the switches in the copy of its sound", dict(KW, shape=m7, contour=96, decay=110),
         dict(blocks=150, sw=BASS | UPDOWN, preview=True)),
        ("a trig's lock holds the bass on over a sound without, then the next trig without a lock",
         dict(KW, shape=m7, contour=80, decay=90),
         dict(blocks=240, trigs=(1, 120), env={1: dict(lock=BASS_HELD | BASS), 120: dict(lock=None)})),
        ("a lock holds the bass off and up-down on over a sound with the bass",
         dict(KW, shape=m7, contour=59, decay=110),
         dict(blocks=150, sw=BASS, env={1: dict(lock=BASS_HELD | UPDOWN_HELD | UPDOWN)})),
        ("a lock that holds no switch", dict(KW, shape=m7, contour=59, decay=110),
         dict(blocks=120, sw=BASS, env={1: dict(lock=0)})),
        ("1/16 at 60 BPM", dict(KW, shape=m7, contour=41, decay=127), dict(blocks=250, tempo=60 * 120)),
        ("1/16 at 546 BPM", dict(KW, shape=m7, contour=41, decay=127), dict(blocks=150, tempo=546 * 120)),
        ("1/4T at 133.5 BPM, then the tempo moving", dict(KW, shape=MAJ7, contour=14, decay=127),
         dict(blocks=400, tempo=16020, env={b: dict(tempo=7200 + 90 * b) for b in range(100, 400, 25)})),
        ("PITCH 0, note 0: the note held at 0", dict(KW, pitch=0, note=0), dict(blocks=120, sw=BASS)),
        ("PITCH 127, note 127, COLOR 127", dict(KW, pitch=127, note=127, color=127), dict(blocks=120, sw=BASS)),
        ("FINE 0, then FINE 127", dict(KW, finetune=0), dict(blocks=150, changes={75: dict(finetune=127)})),
        ("DECAY 127, 600 blocks, the arpeggio at 1/8T", dict(KW, decay=127, shape=m7, contour=32),
         dict(blocks=600, sw=BASS)),
        ("DECAY 0: the envelope closes, the voice pauses, a trig wakes it", dict(KW, decay=0, shape=m7, contour=96),
         dict(blocks=300, trigs=(1, 150, 151, 260), sw=BASS)),
        ("DECAY 40, retrigs", dict(KW, decay=40, sweep=100), dict(blocks=400, trigs=(1, 60, 61, 120, 300))),
        ("GATE, the note ends at 120", dict(KW, gate=1, decay=60, shape=m7, contour=59), dict(blocks=400, rels=(120,))),
        ("trigs in four blocks in a row", dict(KW, decay=90, sweep=110, shape=m7, contour=96),
         dict(blocks=200, trigs=(1, 20, 21, 22, 23), changes={21: dict(note=62), 22: dict(note=64), 23: dict(note=65)},
              sw=BASS)),
        ("knobs moving at every block", dict(KW, decay=110),
         dict(blocks=200, trigs=(1, 100), sw=BASS,
              changes={b: dict(color=(3 * b) % 128, shape=127 - (5 * b) % 128, sweep=(7 * b) % 128,
                               contour=(11 * b) % 128, decay=110 - b % 40) for b in range(200)})),
        ("every knob at 0", dict(KW, color=0, shape=0, sweep=0, contour=0, decay=0), dict(blocks=100)),
        ("every knob at its top (SHAPE 127, M), the bass", dict(KW, color=127, shape=127, sweep=127, contour=127,
                                                            decay=127), dict(blocks=300, sw=BASS)),
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
    check(not bad, f"{label}: at every block not paused, what chips_render gives AMP_ENV is the host's core, bit for "
                   f"bit, fed the inputs chips_update must take, through the blocks not paused; chips_render called at "
                   f"every block; one fresh voice a case ({len(todo)} cases, {blocks} blocks) {bad[:4]}")
    check(not bad and paused > 0 and woke > 0,
          f"{label}: the pause: no trig and the envelope below -102 dB, neither core nor chain runs and the track is "
          f"silent ({paused} blocks); a trig wakes the voice where it stood ({woke} times)")
    check(not bad, f"{label}: in every block not paused chips_render calls AMP_ENV, the VCA and PUNCH, once each, in "
                   "that order, on its output and its voice")


def switches_heard(fw):
    """The inputs act: the bass, up-down, PUNCH's level, a lock and the tempo each change the sound. m7 at 1/32
    (93.75 blocks a tone at 120 BPM): up and down turns back after the fourth tone, from block 375 on; at 60 BPM the
    first change comes at block 188 instead of 94."""
    base = dict(KW, shape=M7, contour=59, decay=127)
    n = 600
    plain, _, _ = play(fw, base, n, probe=False)
    bass, _, _ = play(fw, base, n, probe=False, sw=BASS)
    updown, _, _ = play(fw, base, n, probe=False, sw=UPDOWN)
    soft, _, _ = play(fw, dict(base, punch=0), n, probe=False, sw=BASS)
    loud, _, _ = play(fw, dict(base, punch=1), n, probe=False, sw=BASS)
    lock, _, _ = play(fw, base, n, probe=False, env={1: dict(lock=BASS_HELD | BASS)})
    slow, _, _ = play(fw, base, n, probe=False, tempo=60 * 120)
    first = lambda a, b: int(np.nonzero(np.any(a != b, axis=1))[0][0]) if not np.array_equal(a, b) else None
    pairs = dict(bass=(plain, bass), updown=(plain, updown), punch=(soft, loud), lock=(lock, bass), tempo=(plain, slow))
    differ = {k: not np.array_equal(a, b) for k, (a, b) in pairs.items()}
    ok = differ["bass"] and differ["updown"] and differ["punch"] and differ["tempo"] and not differ["lock"]
    check(ok, f"the inputs act: the bass, up-down (from block {first(plain, updown)}), PUNCH (the bass's level, with "
              f"the stock PUNCH), the tempo (60 against 120 BPM at 1/32, from block {first(plain, slow)}) each change "
              f"the sound, and a trig's lock of the bass plays as the bass in the sound {differ}")


# --- 3. the stock chain ------------------------------------------------------------------------------------------
def like_tone(fw):
    """The amp envelope and the chain's words of a CHIPS track and of a TONE track, the same DECAY, GATE, note ends,
    trigs and PUNCH: identical after every block, until the envelope closes (CHIPS then pauses, TONE runs on), PUNCH's
    output stage too: 0x20000000 for both from the first trig's block on."""
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
        stage = {x[-1] for x in a[2:n]}, {x[-1] for x in b[2:n]}
        stages |= {(frozenset(stage[0]), frozenset(stage[1]))}
        ok &= same and stage == ({0x20000000}, {0x20000000}) and not e1.unmapped and not e2.unmapped and n > 20
        rows.append(f"{name}: {'identical' if same else 'DIFFERENT'} over {n} blocks")
    check(ok, "the amp envelope and the chain's words (DECAY's factor, the attack, PUNCH's drive and mix) are TONE's, "
              "block for block, PUNCH's output stage too (0x20000000, TONE's level): "
              + "; ".join(rows) + ("" if ok else f"; output stages seen {[(sorted(map(hex, x)), sorted(map(hex, y))) for x, y in stages]}"))
    p, pr, e = play(fw, dict(KW, punch=1, decay=100), 200)
    q, _, _ = play(fw, dict(KW, decay=100), 200, probe=False)
    check(p.any() and not np.array_equal(p, q) and not e.unmapped,
          f"PUNCH: the stock PUNCH acts on the output, peak {db(np.abs(p).max()):.1f} dB "
          f"(without {db(np.abs(q).max()):.1f} dB), a square without the bass")


# --- 4. the tracks -----------------------------------------------------------------------------------------------
def change(fw, ref):
    """CHIPS plays, TONE takes the track (trig at 60), CHIPS again (trig at 120): a fresh voice."""
    y, pr, e = play(fw, dict(KW, decay=127, shape=M7, contour=96), 260, trigs=(1, 60, 120), sw=BASS,
                    changes={60: dict(machine=TONE), 120: dict(machine=fw.index)})
    why, m = pr.verify(ref, 0, y)
    tone = np.abs(y[62:120]).max()
    check(not why and m["inits"] == 2 and tone > 1e6 and not e.unmapped,
          f"a change of machine: CHIPS, TONE (peak {db(tone):.1f} dB), CHIPS again: a fresh voice, exact {why[:1]}")


SIX = [(dict(KW, note=36, decay=90), 0), (dict(KW, note=48, shape=M7, contour=41, decay=100), BASS),
       (dict(KW, note=55, color=20, sweep=110, decay=60), BASS),
       (dict(KW, note=60, shape=MAJ, contour=116, punch=1, decay=110), BASS | UPDOWN),
       (dict(KW, note=72, color=120, shape=M9_MINOR, contour=80, decay=70), UPDOWN),
       (dict(KW, note=84, sweep=10, decay=120), BASS)]


def six(fw, ref):
    """Six CHIPS tracks with different knobs and switches: each exact, and the same as alone."""
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
    check(not bad and not e.unmapped, f"six CHIPS tracks together: each exact (its own knobs and switches) and identical "
                                      f"to the same track alone {bad}")


def multi(fw, setup, blocks, trigs, sws=None):
    e = fw.engine()
    for t, kw in setup.items():
        e.set(t, **kw)
        switches(e, t, (sws or {}).get(t, 0))
    return np.stack([e.block(trigs.get(b, 0)) for b in range(blocks)]), e.unmapped


def mixed(fw, off):
    """CHIPS on tracks 2 and 5 among KICK, METAL, PERC and CHORD: the stock tracks identical to the stock OS, the
    CHIPS tracks identical to alone."""
    mach = [KICK, fw.index, METAL, PERC, fw.index, CHORD]
    ours = {1: (dict(KW, decay=60, shape=M7, contour=59), BASS),
            4: (dict(KW, note=48, color=127, sweep=100, decay=60), 0)}
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
    check(ok, "CHIPS on tracks 2 and 5 among KICK, METAL, PERC, CHORD: the stock tracks identical to the stock OS, the "
              "CHIPS tracks identical to alone")


def stock_unchanged(off, fw, label):
    """The six stock machines, no CHIPS track: identical to the stock OS, without one instruction of CHIPS."""
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
          "CHIPS")


def like(alone, fw, label):
    """The CHIPS track's output identical in two firmwares."""
    bad = []
    for kw, ex in ((KW, dict(trigs=(1, 120))),
                   (dict(KW, shape=M7, contour=59, sweep=100, decay=110), dict(trigs=(1, 120), sw=BASS)),
                   (dict(KW, gate=1, decay=30, contour=116, shape=MAJ), dict(trigs=(1, 200), rels=(100,),
                                                                                        sw=UPDOWN))):
        a, _, _ = play(alone, kw, 250, probe=False, **ex)
        b, _, e = play(fw, kw, 250, probe=False, **ex)
        if not np.array_equal(a, b) or e.unmapped or not a.any():
            bad.append(kw)
    check(not bad, f"{label}: the CHIPS track identical to CHIPS alone (the defaults; m7 at 1/32 with the sweep and the "
                   f"bass; GATE with a pause, up and down) {bad[:1]}")


# --- 5. the display -----------------------------------------------------------------------------------------------
VT = 0x400fd134                     # a track's parameter object's vtable: +60 the text, +64 the drawn value, +68 the
                                    # picture (chips_ui_format, chips_ui_draw, chips_ui_picture in front of the stock)
BIG, NARROW = 0x401429ec, 0x40141b08   # the OS's big font (16 x 22, the window's numbers) and its narrow one (12 x 22)
WIN = (0x60, 0x22)                  # where the value window (0x4001d818) has a value drawn: x 96 (centred), y 34
MIX_NAMES = ("1/4", "1/4T", "1/8", "1/8T", "1/16", "1/16T", "1/32")


def arp_want(c):
    """CONTOUR c's text as the knob is defined (notes/83 §2, §9): the divisions, 1/4 from 0 to 9, the others 9 values
    each, then the free tempo in Hz, 16HZ .. 64HZ (the narrow big font has capitals only); no off since 2026-11-16."""
    if c < 64:
        return MIX_NAMES[max(c - 1, 0) // 9]
    return f"{round(16 * 4 ** ((c - 64) / 63))}HZ"


def fault_of(u):
    """Where the last call stopped on an unmapped access: (the pc, the addresses), or None."""
    return (u.uc.reg_read(mk.UC_M68K_REG_PC), tuple(u.bad)) if u.bad else None


def vtext(u, d, v):
    """The text of value v of descriptor d through a track's parameter object (vtable +60), as the OS asks it; the
    object's check of the value (vt[24], 0x4000c0a6, which needs a real track) accepts it, as lofi_ui's text path.
    None if the call does not return (u.fault: where it stopped, if on an unmapped access)."""
    S = L.SCRATCH + 0x3000
    obj, ovt, out, ok = S, S + 0x100, S + 0x200, S + 0x300
    u.uc.mem_write(ovt, bytes(u.uc.mem_read(VT, 0x80)))
    u.uc.mem_write(ovt + 24, struct.pack(">I", ok))
    u.hooks[ok] = ("valid", 1)
    u.uc.mem_write(obj, struct.pack(">II", ovt, 0))
    u.uc.mem_write(out, bytes(32))
    u.fault = None
    try:
        u.call(u.u32(VT + 60), obj, d, v, out)
    except UcError:
        u.fault = fault_of(u)
        return None
    return u.cstr(out) if u.sp_ok and not u.bad else None


def shown(u, d, v, text=True):
    """The value window of descriptor d at v (the OS's 0x4001d818, lofi_ui.UI.popup): (its pixels, the sprites it
    hands the draw, the texts it draws: (the font's glyphs, x, y, flags, text)); text=False: the texts not drawn.
    As in vtext, the object's check of the value (vt[24], 0x4000c0a6) accepts it: for the descriptors whose flags
    (0x4005a85e, 0x4010dce0 + 56 d + 24) have bit 16, 41 of the 76 stock ones (0 among them), it asks the track
    behind the object (obj + 4, through vt[52], 0x4000a830), which the window's object has not. The stack below the call is cleared, so that a text a formatter
    leaves unwritten is the same empty text in every build. None if the window does not return (u.fault: where it
    stopped, if on an unmapped access)."""
    texts = []

    def hk(uc, a, s_, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        _bmp, font, x, y, fl, fmt, arg = struct.unpack(">7I", uc.mem_read(sp + 4, 28))
        glyphs = struct.unpack(">I", uc.mem_read(font + 4, 4))[0]
        texts.append((glyphs, s32(x), s32(y), fl, u.cstr(arg) if u.cstr(fmt) == "%s" else u.cstr(fmt)))
    chk = u.u32(VT + 24)
    u.hooks[chk] = ("valid", 1)
    u.uc.mem_write(L.STACK - 0x8000, bytes(0x8000 - 0x400))
    if text:
        h = u.uc.hook_add(UC_HOOK_CODE, hk, begin=L.DRAW_TEXT, end=L.DRAW_TEXT)
    else:
        u.hooks[L.DRAW_TEXT] = ("text", 0)
    u.fault = None
    try:
        r = u.popup(d, v)
    except UcError:
        u.fault, r = fault_of(u), None
    finally:
        if text:
            u.uc.hook_del(h)
        else:
            del u.hooks[L.DRAW_TEXT]
        del u.hooks[chk]
        u.hooks.pop(L.DRAW_SPRITE, None)
    return (r[0], tuple(r[1]), tuple(texts)) if r else None


def seen(u, d, v):
    """Descriptor d at v as the stock comparisons take it: its window and its text, or where each stopped."""
    w = shown(u, d, v)
    wf = u.fault
    t = vtext(u, d, v)
    return w, wf, t, u.fault


def lit(fb, x0=0, x1=128):
    return {(x, y) for x in range(x0, x1) for y in range(64) if L.pix(fb, x, y)}


def pictures(u, d, v, entry):
    """The value window of d at v (shown) and the calls of the picture entry `entry` (the stock 0x4000a6b0) it makes:
    (descriptor, x, y, value) each."""
    got = []

    def hk(uc, a, s_, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        _obj, dd, x, y, val = struct.unpack(">5I", uc.mem_read(sp + 4, 20))
        got.append((dd, s32(x), s32(y), val))
    h = u.uc.hook_add(UC_HOOK_CODE, hk, begin=entry, end=entry)
    try:
        r = shown(u, d, v)
    finally:
        u.uc.hook_del(h)
    return r, got


def display(stock, fw, label, first):
    """CHIPS's Chord and Arp (descriptors first + 1, first + 3) in the value window and as text, against the knobs'
    definitions (notes/83 §8, §10) and the stock OS; the stock descriptors unchanged; CHIPS's Wave and Sweep as
    SNARE's."""
    a, b = L.UI(stock), L.UI(fw.img, (E.PAYLOAD_DST, fw.runtime))
    for u in (a, b):
        u.call(0x4005a274)                                  # the parameter tables, at boot
    check(a.init_ok and b.init_ok and not a.bad and not b.bad,
          f"{label}: the OS's interface objects and parameter tables built (0x400de244, 0x4005a274)")
    dc, da = first + 1, first + 3
    # Chord: Plaits' chords' names, eleven zones of 0 .. 127, written by the window in its big font
    want = [CHORD_NAMES[v * NCHORD // 128] for v in range(128)]
    got = [vtext(b, dc, v << 8) for v in range(128)]
    ok = got == want
    check(ok, f"{label}: Chord's text (descriptor {dc}, vtable +60) for each of 0 .. 127: "
              + ", ".join(f"{CHORD_NAMES[k]} {ZONE[k]}-{ZONE_END[k]}" for k in range(NCHORD))
              + ("" if ok else f"; got {[(v, t) for v, t in enumerate(got) if t != want[v]][:4]}"))
    pic = a.u32(VT + 68)                                    # the stock picture entry, 0x4000a6b0
    bad, rows, cols = [], set(), set()
    for v in sorted(set(ZONE + ZONE_END)):
        (y, calls), n = pictures(b, dc, v << 8, pic), shown(b, dc, v << 8, text=False)
        if y is None or n is None:
            bad.append((v, "no window"))
            continue
        drawn = lit(y[0]) ^ lit(n[0])
        rows |= {q for _, q in drawn}
        cols |= {q for q, _ in drawn}
        if y[2] != ((BIG, WIN[0], WIN[1], 2, want[v]),) or not drawn \
                or min(q for q, _ in drawn) < 64 or calls != [(dc, 0x20, 0x13, v << 8)]:
            bad.append((v, y[2], calls))
    check(not bad, f"{label}: Chord's value window at each zone's ends: its name written once by the window, in its "
                   f"big font, centred on x {WIN[0]}, y {WIN[1]}, as a number; inside the right half (columns "
                   f"{min(cols, default=0)} .. {max(cols, default=0)}, rows {min(rows, default=0)} .. "
                   f"{max(rows, default=0)}); the stock picture called once, at the value {bad[:3]}")
    for v in (ZONE[2], ZONE[6], ZONE[9]):
        w = shown(b, dc, v << 8)
        if w:
            print(f"      Chord at {v} (« {want[v]} »):")
            print(L.ascii_popup(w[0]))
    # Arp: the divisions, Hz
    texts = [vtext(b, da, c << 8) for c in range(128)]
    ok = texts == [arp_want(c) for c in range(128)]
    check(ok, f"{label}: Arp's text (descriptor {da}): {texts[0]}, {texts[1]} .. {texts[9]}, {texts[10]}, .. "
              f"{texts[55]} .. {texts[63]}, {texts[64]} .. {texts[127]}"
              + ("" if ok else f"; expected {[arp_want(c) for c in range(128)][:12]}"))
    bad, rows, cols, bigrows = [], set(), set(), set()
    for c in range(128):
        y, n, x = shown(b, da, c << 8), shown(b, da, c << 8, text=False), shown(a, 54, c << 8)
        xn = shown(a, 54, c << 8, text=False)
        if y is None or n is None or x is None or xn is None:
            bad.append((c, "no window"))
            continue
        drawn = lit(y[0]) ^ lit(n[0])
        rows |= {q for _, q in drawn}
        cols |= {q for q, _ in drawn}
        if y[2] != ((NARROW, WIN[0], WIN[1], 2, arp_want(c)),) or not drawn or min(q for q, _ in drawn) < 64 \
                or y[1] != x[1]:
            bad.append((c, y[2], y[1] == x[1]))
        bigrows |= {q for _, q in lit(x[0]) ^ lit(xn[0])}
    check(not bad, f"{label}: Arp's value window for each of 0 .. 127: its text drawn once, in the narrow big font, "
                   f"centred on x {WIN[0]}, y {WIN[1]}; inside the right half (columns {min(cols, default=0)} .. "
                   f"{max(cols, default=0)}, rows {min(rows, default=0)} .. {max(rows, default=0)}; the stock "
                   f"number's rows {min(bigrows, default=0)} .. {max(bigrows, default=0)}); the picture SNARE's "
                   f"CONTOUR's, as before {bad[:3]}")
    for c in (0, 41, 50, 100):
        w = shown(b, da, c << 8)
        if w:
            print(f"      Arp at {c} (« {arp_want(c)} »):")
            print(L.ascii_popup(w[0]))
    # the rest unchanged
    bad, lost = [], []
    for d in range(76):
        for v in (0, 0x2000, 0x4000, 0x7f00):
            x, y = seen(a, d, v), seen(b, d, v)
            if x != y:
                bad.append((d, v))
            if x[0] is None or x[2] is None:
                lost.append((d, v, x[1] or x[3]))
    check(not bad, f"{label}: the 76 stock descriptors' value windows (pixels, sprites, texts) and texts as on the "
                   f"stock OS at 0, 32, 64, 127 {bad[:4]}; "
                   + (f"{len(lost)} of 304 not built here, stopped at the same place in both builds: "
                      f"{sorted({d for d, _, _ in lost})}, the first {lost[0][2]}" if lost else "all 304 built"))
    bad = [(d, v) for k, d in ((0, first), (2, first + 2)) for v in (0, 0x2000, 0x4000, 0x7f00)
           if shown(b, d, v) != shown(b, 51 + k, v) or vtext(b, d, v) != vtext(b, 51 + k, v)
           or shown(b, d, v) is None]
    check(not bad, f"{label}: Wave and Sweep ({first}, {first + 2}) show as SNARE's COLOR and SWEEP (51, 53), whose "
                   f"objects they share, as before {bad[:4]}")
    return b


def display_next(alone_sampler, both, first):
    """Next to SAMPLE: SAMPLE's descriptors (76 .. 80) as without CHIPS; CHIPS's Chord and Arp as alone."""
    x, y = L.UI(alone_sampler.img, (E.PAYLOAD_DST, alone_sampler.runtime)), L.UI(both.img, (E.PAYLOAD_DST, both.runtime))
    for u in (x, y):
        u.call(0x4005a274)
    bad, lost = [], []
    for d in range(76, 81):
        for v in (0, 0x2000, 0x4000, 0x7f00):
            p, q = seen(x, d, v), seen(y, d, v)
            if p != q:
                bad.append((d, v))
            if p[0] is None or p[2] is None:
                lost.append((d, v, p[1] or p[3]))
    check(not bad and x.init_ok and y.init_ok, f"next to SAMPLE: SAMPLE's five descriptors' windows and texts as "
                                               f"without CHIPS {bad[:4]}; "
                                               + (f"{len(lost)} of 20 not built here, stopped at the same place in "
                                                  f"both builds: the first {lost[0]}" if lost else "all 20 built"))
    ok = [vtext(y, first + 1, v << 8) for v in range(128)] == [CHORD_NAMES[v * NCHORD // 128] for v in range(128)] \
        and [vtext(y, first + 3, c << 8) for c in range(128)] == [arp_want(c) for c in range(128)]
    check(ok, f"next to SAMPLE: CHIPS's Chord ({first + 1}) OCT .. M, its Arp ({first + 3}) 1/4 .. 64HZ")


# --- 6. level and cost -------------------------------------------------------------------------------------------
LEVELS = (("a square (the defaults)", KW, 0), ("a narrow pulse (COLOR 10)", dict(KW, color=10), 0),
          ("sync (COLOR 120)", dict(KW, color=120), 0), ("the bass, PUNCH off", KW, BASS),
          ("the bass, PUNCH on", dict(KW, punch=1), BASS),
          ("m7 at 50 Hz, the bass", dict(KW, shape=M7, contour=116), BASS),
          ("a kick (note 36, SWEEP 120, the bass, PUNCH on)", dict(KW, note=36, sweep=120, punch=1), BASS))


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
    0.5 s from the trig (blocks 2..752): the fundamental and BS.1770's loudness (LUFS)."""
    rows = []
    sounds = [(STOCK[m], m, dict(stock_kw(m), decay=127), 0) for m in (TONE, PERC, METAL, CHORD)]
    m7 = M7
    sounds += [("CHIPS a square (COLOR 64, one tone)", None, dict(KW, decay=127), 0),
               ("CHIPS a narrow pulse (COLOR 10)", None, dict(KW, color=10, decay=127), 0),
               ("CHIPS sync (COLOR 120)", None, dict(KW, color=120, decay=127), 0),
               ("CHIPS the bass, PUNCH off", None, dict(KW, decay=127), BASS),
               ("CHIPS the bass, PUNCH on", None, dict(KW, punch=1, decay=127), BASS),
               ("CHIPS m7 at 1/16 (an arpeggio)", None, dict(KW, shape=m7, contour=41, decay=127), 0)]
    ref = None
    for name, m, kw, sw in sounds:
        y, _, _ = play(fw, kw, 752, probe=False, machine=m, sw=sw)
        z = y[2:752]
        lu = loudness(z)
        if m == TONE:
            ref = lu
        hz, note = fundamental(z[150:])
        pitch = "" if "arpeggio" in name else f", fundamental {hz:.1f} Hz (note {note:.1f})"
        rows.append(f"{name}: {lu:.1f} LUFS{'' if ref is None else f' ({lu - ref:+.1f} against TONE)'}{pitch}")
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
    m7 = M7
    rows, sps = [], []
    for name, kw, sw in (("the defaults (a square, one tone)", dict(KW, decay=127), 0),
                         ("COLOR 127 (sync)", dict(KW, color=127, decay=127), 0),
                         ("the bass, note 60", dict(KW, decay=127), BASS),
                         ("the bass, PUNCH on", dict(KW, punch=1, decay=127), BASS),
                         ("m7 at 64 Hz, the bass", dict(KW, shape=m7, contour=127, decay=127), BASS),
                         ("m7 at 1/16, up and down", dict(KW, shape=m7, contour=41, decay=127), UPDOWN),
                         ("note 36, the bass", dict(KW, note=36, decay=127), BASS),
                         ("note 96, COLOR 127, the bass above 750 Hz", dict(KW, note=96, color=127, decay=127), BASS)):
        x, sp = run(fw.index, kw, 40, sw=sw)
        sps.append(sp)
        rows.append(f"{name} {m(x)} (most {hi(x)}, the trig's block {int(x[2]) - zero})")
    x, sp = run(fw.index, dict(KW, sweep=127, decay=127), 80, trigs=tuple(range(1, 80, 10)), sw=BASS)
    sps.append(sp)
    rows.append(f"SWEEP 127, a trig every 10 blocks, the bass: mean {int(np.mean(x[6:])) - zero} (most {hi(x)})")
    idle, sp = run(fw.index, dict(KW, decay=0), 300)
    sps.append(sp)
    six_c, sp = run(fw.index, dict(KW, decay=127, shape=m7, contour=116), 40, tracks=range(6), sw=BASS)
    sps.append(sp)
    six_t, _ = run(TONE, stock_kw(TONE), 40, tracks=range(6))
    deep = E.STACK - 0x100 - min(sps)
    info(f"{label}: instructions a block of one CHIPS voice: " + "; ".join(rows)
         + f"; paused {int(np.median(idle[250:])) - zero}. Stock: "
         + ", ".join(f"{STOCK[k]} {v}" for k, v in stock.items())
         + f". Six CHIPS tracks (m7 at 50 Hz, the bass) {m(six_c)} against six TONE {m(six_t)} "
         f"({m(six_c) / max(m(six_t), 1):.2f}x); stack {deep} bytes below the voice loop")


def dry(stock):
    """No Unicorn: the firmwares' layout and the host's core."""
    for ids in (["chips"], ["sampler", "chips"]):
        f = Fw(stock, ids)
        print(f"{'+'.join(ids)}: CHIPS machine {f.index}, code {f.code[0]:#x}..{f.code[1]:#x}, update {f.upd:#x}, "
              f"render {f.rnd:#x}, variables {f.bss[1]} bytes at {f.bss[0]:#x}, payload {len(f.runtime)} bytes; "
              f"the shortcut layer's data at {f.tweak['symbols']['sc_data']}")
    with tempfile.TemporaryDirectory() as d:
        ref = Ref(pathlib.Path(d))
        k = [[1 if b == 0 else 0, 60 << 16, 64 << 8, 0, 64 << 8, 41 << 8, 1, 0, T120 * 32 // 15, 0] for b in range(300)]
        y = to_bus(ref.run(k))
        print(f"host core, the defaults with the bass: 300 blocks, peak {db(np.abs(y).max()):.1f} dB, RMS "
              f"{db(rms(y)):.1f} dB of the bus's full scale")
    print("\n(dry run: no emulation)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--quick", action="store_true", help="fewer cases")
    ap.add_argument("--dry", action="store_true", help="build and lay out only, no emulation")
    ap.add_argument("--only", default="startup,core,inputs,chain,tracks,next,display,compare,measure",
                    help="the parts to run: startup, core, inputs, chain, tracks, next, display, compare, measure "
                         "(default: all)")
    args = ap.parse_args()
    parts = set(x.strip() for x in args.only.split(",") if x.strip())
    bad_parts = parts - {"startup", "core", "inputs", "chain", "tracks", "next", "display", "compare", "measure"}
    if bad_parts:
        sys.exit(f"!! --only: unknown parts {sorted(bad_parts)}")
    import test_sdvintage as tsv           # the official file's MAIN OS (no Unicorn needed for this)
    stock = tsv.main_os_from_syx(args.cycles)
    if args.dry:
        return dry(stock)
    load_emulation()
    off, alone = Fw(stock, None), Fw(stock, ["chips"])
    with tempfile.TemporaryDirectory() as d:
        ref = Ref(pathlib.Path(d))
        print(f"== chips: CHIPS as machine {alone.index}, code {alone.code[0]:#x}..{alone.code[1]:#x}")
        if "startup" in parts:
            startup(args.cycles, stock, alone)
        if "core" in parts:
            print("the core, exact")
            exact(alone, ref, cases(args.quick), "CHIPS alone")
        if "inputs" in parts:
            print("the inputs")
            switches_heard(alone)
        if "chain" in parts:
            print("the stock chain")
            like_tone(alone)
        if "tracks" in parts:
            print("the tracks")
            change(alone, ref)
            six(alone, ref)
            mixed(alone, off)
            stock_unchanged(off, alone, "CHIPS alone")
        if "display" in parts:
            print("the display")
            display(stock, alone, "CHIPS alone", 76 + 5 * (alone.index - 6))
        if "next" in parts:
            both = Fw(stock, ["sampler", "chips"])
            print(f"\n== sampler+chips: CHIPS as machine {both.index}")
            if "startup" in parts:
                startup(args.cycles, stock, both)
            print("the tracks")
            like(alone, both, "next to SAMPLE")
            stock_unchanged(off, both, "next to SAMPLE")
            if "display" in parts:
                print("the display")
                display_next(Fw(stock, ["sampler"]), both, 76 + 5 * (both.index - 6))
        if "compare" in parts:
            print("\npitch and loudness against the stock machines")
            compare(alone)
        if "measure" in parts:
            print("\nlevel and cost")
            level(alone)
            cost(alone, "one voice")
        if parts != {"startup", "core", "inputs", "chain", "tracks", "next", "display", "compare", "measure"}:
            print(f"\n(only {', '.join(sorted(parts))})")
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
