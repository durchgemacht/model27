#!/usr/bin/env python3
"""Proof of the effect slots (notes/68, steps F1, F2 and F2b, §16 to §18) on the OS's own code, with REFD and REFR,
the reference effects of the delay and reverb slots (tools/machines/refdelay/, tools/machines/refreverb/), Digital
Delay, PPPCCC's (tools/machines/digidelay/), and POTS, model27's telephone-line delay (tools/machines/pots/, notes/69),
through the builder's part tools/machines/fxslot/.

For each selection (by default: refdelay; refreverb; refdelay,refreverb; sampler,refdelay,refreverb; digidelay;
digidelay,refreverb; sampler,digidelay,refreverb; pots; sampler,pots,refreverb), on the official OS 1.13:
  1. start-up: the bootstrap's own aPLib depacker reads the grown OS back; the boot hook copies the payload and clears
     the BSS;
  2. the sites: the mixer's call of each slot that has an effect (0x4005699c, 0x40056a2c) -> jsr fx_delay / fx_reverb,
     a slot without one keeps its stock call; the handler's call at TRACK + a knob (0x4001f89a) -> jsr fx_track; the
     pattern header's loader (0x4005b4b0) -> jsr fx_load, its initializer (0x4006155e) -> jsr fx_init; an
     effects-only build writes nothing else but the payload's boot (no registrar); the slots' lines (§16): one per slot
     whose effects ask for one, 16-aligned at the start of the payload's variables, as large as the largest effect
     asks, apart from every package's variables, its address in the effect's code; the composer refusing a line
     without its patch point, a patch point without a line, a size not a multiple of 16 or past 4 MiB, another kind of
     patch point; the data block: each slot's table
     (entry 0 the stock effect, then the effects by id, with their resets), the names and formatters of the slots'
     parameters for each entry (the stock ones as in the image, the effects' from their manifests), the descriptor
     tables they go into;
  3. the audio: a stock engine and the build's engine run side by side, block for block, what the mixer does around
     the effects (0x4005802e, the delay, the reverb, 0x40057942, 0x400573fa) on the same input and parameters:
     - the part reads the playing pattern's header (bytes 29 to 31) in every block, through the patterns as the OS
       links them. No singleton, no playing pattern, a pattern number past 95, a wrong check byte, a header never
       written, id 0, an id the build does not hold, the other slot's id: the stock effects, their returns and the
       whole SRAM the stock OS's;
     - a pattern choosing the effects: the slots' parameters named after them at the first block, the stock effect
       given one block of silence as it stops (its return thrown away: the stock engine does the same), the effect
       reset, then its return the model's, bit for bit, the rest of the SRAM the stock OS's; a pattern change to a
       pattern with the stock effects (the stock names back), then back, the effect starting from its reset;
     - every call keeping d2-d7/a2-a6 and the stack, no access outside memory;
  4. the gesture (fx_track, as the handler calls it, with the handler's frame): a descriptor that is not the slot's
     knob, or a slot without an effect: the stock call, its answer; TRACK + Delay Time / Reverb Size: the handler's
     end with 0, its registers back from its frame; four detents in one direction for a step, the count starting
     again on a change of direction, of slot, or after 0.4 s of the DMA timer; the steps stopping at the ends of the
     table; at each change the shown pattern's header (the ids, the check byte, written with the interrupts masked)
     and one call of its notify, the parameters' names and group in both descriptor tables and their formatters, no
     save of the settings (0x400449b8); a shown pattern that is not the playing one: its header and its notify only,
     the names those of what plays; an id the build does not hold moves to the first effect; no singleton: nothing;
     all of it against a model of the steps;
  5. the pattern (as tools/emu/probe_chord_storage.py, notes/42 §4): the stock loader (0x4005b3b4) and initializer
     (0x40061526) leave bytes 29 to 31 as the buffer held them, the header's copy (0x4005b4c4) keeps its 64 bytes;
     with fx_load, a header loads as the stock OS loads it plus bytes 29 to 31 when their check holds, the stock
     effects otherwise (a wrong check byte, zeros, 0xff); with fx_init, a new header as the stock OS's plus the stock
     effects, and a header initialized with "keep" untouched; a whole pattern saved (0x4005ba0a), loaded (0x4005b894)
     and copied (0x4008f1f0) keeps the choice, the rest as the stock OS loads it; a file without a valid choice loads
     the stock effects; every write of the three bytes with the interrupts masked, the level back after;
  6. the cost (notes/68 §17, the standard's §6): instructions per block, counted on the OS's own code, noise of
     +-2^28 into both channels, Time 0 and Fdbk 96 for the delay, Size 64 and Tone 96 for the reverb: the stock
     effect of each slot; each effect's process called alone after its reset (its reset counted apart), the first
     block, then the mean and maximum over 21 blocks after 32 more (a delay of 750 frames reads what it wrote); what
     fxslot adds in the slot with the stock choice and with the effect, and in the block of a switch. The numbers go to
     build/fx-cost.json; those the manifests and fxslot's part.json declare must be the ones counted;
  7. Digital Delay (notes/68 §18), its process called alone on a long sequence (750 frames of delay at Fdbk 96; Fdbk
     127 with full-scale noise, saturating; the delay moved to 2 250 frames and slewing; silence, the tail; a reset,
     then it all again from silence), against a model of PPPCCC's arithmetic, bit for bit; with --pppccc, against
     PPPCCC's own code too (their patches/06-delay-fx.json applied to the official OS after 00-core.json, which it
     requires, its entry 0x40160e6c), bit for bit up to the reset, which PPPCCC does not have;
  8. POTS (notes/69 §8.1, §14), its process called alone (a burst at the median machine's level and its echoes; noise;
     full-scale noise at Fdbk 127, past the input's, the feedback's and the echo's limits; Time sliding and Fdbk rising
     under bursts; silence; a reset, then it all again; then on past its first dropout, 2 250 blocks after the reset),
     against its host build (tools/emu/pots_host.py: pots.c compiled with the host's C compiler, the EMAC as emac.py
     executes it), bit for bit.
And once a run (notes/69 §8.2, §8.3):
  9. POTS against v6: the measurements that settled its sound in the float prototype (the shift's direction, the decay,
     a tail's end, the colour, the octave bands, the echo's level, the codec's grain, the peak at Fdbk 127, silence),
     taken again on the host build, which section 8 has found to give the device's bits;
 10. Digital Delay and POTS in the delay slot of one build: the pattern switching Digital -> POTS -> Digital -> POTS
     through fx_delay, the slot's line filled with noise before each switch: each effect's return its model's from
     its reset, bit for bit (neither reads what was on the line before it).

The SDRAM the stock effects use (the delay line 0x42400000-0x42800000, the reverb's lines 0x42340000-0x423d8000, both
through their uncached aliases 0x4a...) is mapped, and the eDMA's registers (0xfc040000-0xfc050000) read as zeros:
the DMA does not run in the emulator, so both engines read the same buffers.

Needs Unicorn and numpy (pip install unicorn numpy), m68k-elf-objdump and the host's C compiler (cc, for POTS's host
build); Unicorn's JIT does not run inside a sandbox that forbids it (it stops with SIGILL at the first memory map): run
it in a normal terminal. A few minutes, most of them POTS's 3 400 blocks of section 8.

    python3 tools/emu/test_fxslot.py --cycles model-cycles_OS1.13.syx [--machines refdelay,refreverb] [--blocks 60]
                                     [--pppccc PPPCCC-Model-Cycles-1.13-Mods/patches/06-delay-fx.json]
    python3 tools/emu/test_fxslot.py --cycles model-cycles_OS1.13.syx --dry      # builds and sites only, no Unicorn
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import tempfile
import struct
import sys

import numpy as np
from unicorn import UcError, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compose                      # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import mcengine as E                # noqa: E402
import pots_host as PH              # noqa: E402
import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

SELECTIONS = [["refdelay"], ["refreverb"], ["refdelay", "refreverb"], ["sampler", "refdelay", "refreverb"],
              ["digidelay"], ["digidelay", "refreverb"], ["sampler", "digidelay", "refreverb"],
              ["pots"], ["sampler", "pots", "refreverb"]]
PART = compose.load_part("fxslot")
SLOTS = {"delay": dict(site=0x4005699c, stock=0x40057488, entry="fx_delay", out=0x8000ba90, params=428, rec=3,
                       desc=(37, 38)),
         "reverb": dict(site=0x40056a2c, stock=0x400579c4, entry="fx_reverb", out=0x8000bb90, params=432, rec=4,
                        desc=(39, 40))}
ORDER = ("delay", "reverb")                                 # the slots' order in the data block
TRACK_SITE, HANDLER_END, STOCK_TEST = 0x4001f89a, 0x4001f96a, 0x4005a5cc
SAVE = 0x400449b8                                           # writes the settings block to the flash: never called
BUS = 0x8000b990                                            # the send bus, the effects' input (notes/68 §1.1)
TAPS, LINES, WRITE = 0x4005802e, 0x40057942, 0x400573fa     # what the mixer calls around the effects
P = 0x40710000                                              # the parameter block the effects read
QUIET, QUIET_OUT = 0x40720000, 0x40721000                   # the stock engine's silence and its thrown-away return
HDR = 29                                                    # the header's bytes: the delay's id, the reverb's, check
LOAD_SITE, INIT_SITE = 0x4005b4b0, 0x4006155e               # in the header's loader and initializer (notes/68 §14)
ROOT_PTR, PLAYING_PTR = 0x40fe4228, 0x40a7887c              # the patterns' singleton, the playing pattern (notes/42 §5)
SHOWN_OK, SHOWN_IDX, NOTIFY = 0x400cfd0e, 0x4006a96c, 0x400d0f6c   # in 0x4000f208's path; where the notify ends
PATTERN_VT, HEADER_VT = 0x400fda54, 0x400fd8c0              # the pattern object's vtable, its header object's
HDR_LOAD, HDR_COPY, HDR_INIT = 0x4005b3b4, 0x4005b4c4, 0x40061526
PAT_INIT, PAT_SAVE, PAT_LOAD, MEMCPY = 0x400615e8, 0x4005ba0a, 0x4005b894, 0x4008f1f0
PAT_LEN, SER_LEN, HDR_AT, SER_HDR_AT, NUM_AT = 30710, 14800, 30642, 14736, 30706
FIX, GFIX = 0x94000000, 0x92400000                          # the patterns' fixtures: audio, gesture
COST_BLOCKS, COST_WARM = 21, 32                            # counted after the first block and 32 more
COST_WORDS = {"delay": (0, 96 << 8), "reverb": (64 << 8, 96 << 8)}   # Time, Fdbk / Size, Tone
TEMPO = 0x40149310                                          # the OS's tempo, which the delay time divides
PPPCCC_DD = 0x40160e6c                                      # PPPCCC 2.0.0's Digital delay entry (patch 06's symbol DD)
COST = {"effects": {}, "slots": {}}                         # what the cost section counts, for build/fx-cost.json
TIMER = 0xfc07000c                                          # the DMA timer 0, 135.168 MHz
PAUSE = 54067200                                            # 0.4 s of it
BOOT_SITES = {0x400004b2, 0x400b1106, 0x4016cae8}           # the payload's boot: the hook, the stub's mask and its sprite
SRAM = (0x80000000, 0x20000)
SDRAM = ((0x42340000, 0x423d8000), (0x42400000, 0x42800000), (0x4a340000, 0x4a3d8000), (0x4a400000, 0x4a800000))
KEPT = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")]
FRAME = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5")]
REF_IDS = {"delay": 254, "reverb": 255}                     # the reference effects' ids (their manifests)
DATA = PART["data"]
STATE = DATA["state"]                                       # cur[2], played[2], acc, last_slot, last_dir, last_time


def obj(i):
    return 0x40a71754 + 100 * i                             # descriptor i's interface object (notes/47 §3.3)


def jsr(va):
    return b"\x4e\xb9" + struct.pack(">I", va)


def hdr(delay=0, reverb=0, bad=False):
    """Bytes 29 to 31 of a pattern header: the delay slot's id, the reverb slot's, the check (or a wrong one)."""
    return bytes([delay, reverb, (0x5a + delay + reverb + (1 if bad else 0)) & 0xff])


def valid(raw):
    return raw[2] == (0x5a + raw[0] + raw[1]) & 0xff


def choice(raw):
    """The ids bytes 29 to 31 choose: themselves when the check holds, the stock effects otherwise."""
    return [raw[0], raw[1]] if valid(raw) else [0, 0]


class Patterns:
    """Patterns as the OS links them (notes/42 §5): the singleton's objects with their real vtables, each with its
    64-byte header, and the playing pattern holding its number at +30706. write(va, bytes) writes the emulator's
    memory."""

    def __init__(self, write, base, count=3):
        self.w, self.root, self.active = write, base, base + 0x20000
        self.headers = {n: base + 0x30000 + 0x100 * n for n in range(count)}
        for n, h in self.headers.items():
            o = self.root + 5192 + 732 * n
            write(o, bytes(732))
            write(o, struct.pack(">I", PATTERN_VT))
            write(o + 44, struct.pack(">I", HEADER_VT))
            write(o + 60, struct.pack(">I", h))
            write(h, bytes(64))

    def link(self, root=True, active=True, playing=0):
        self.w(ROOT_PTR, struct.pack(">I", self.root if root else 0))
        self.w(PLAYING_PTR, struct.pack(">I", self.active if active else 0))
        self.w(self.active + NUM_AT, struct.pack(">I", playing))

    def set(self, n, rec):
        self.w(self.headers[n] + HDR, rec)


def watch(uc, spans, bad):
    """Notes in bad each write into one of spans [(lo, hi)] made with the interrupts not masked (level below 7)."""
    def hk(u, access, addr, size, value, ud):
        if any(lo < addr + size and addr < hi for lo, hi in spans) and u.reg_read(mk.UC_M68K_REG_SR) & 0x700 != 0x700:
            bad.append((u.reg_read(mk.UC_M68K_REG_PC), addr))
    uc.hook_add(UC_HOOK_MEM_WRITE, hk)


# --- the models of the reference effects (refdelay.c, refreverb.c) ---------------------------------------------------
def sat(x):
    return max(-(1 << 31), min((1 << 31) - 1, x))


class RefDelay:
    LEN = 4096

    def __init__(self):
        self.reset()

    def reset(self):
        self.line, self.pos = [0] * (2 * self.LEN), 0

    def __call__(self, x, params):
        g2 = 2 * (params[1] >> 8)
        out, p = [], self.pos
        for f in range(32):
            for c in range(2):
                d = self.line[2 * p + c]
                out.append(d)
                self.line[2 * p + c] = sat(x[2 * f + c] + (d >> 8) * g2)
            p = (p + 1) & (self.LEN - 1)
        self.pos = p
        return out


class RefReverb:
    def __init__(self):
        self.reset()

    def reset(self):
        self.y = [0, 0]

    def __call__(self, x, params):
        k = ((params[0] >> 8) & 0x7f) >> 4          # the byte at +0: Size's integer part
        out = []
        for f in range(32):
            for c in range(2):
                v = self.y[c]
                v += ((x[2 * f + c] >> 1) - (v >> 1)) >> k
                self.y[c] = v
                out.append(v)
        return out


def s32(x):
    x &= 0xffffffff
    return x - (1 << 32) if x >> 31 else x


class Digital:
    """digidelay.c, which is PPPCCC's Digital delay step for step (notes/68 §18)."""
    FRAMES, LONGEST, SHORTEST = 0x40000, 261120, 32
    tempo = 14400                                # set from the image in main()

    def __init__(self):
        self.line = [0] * self.FRAMES
        self.reset()

    def reset(self):
        self.ready = False

    def __call__(self, x, params):
        time, fdbk = params
        f = max(0, min(127, fdbk >> 8))
        t = f * 258
        c = ((t * t) >> 15) * t >> 15
        g = (3 * t - c) >> 1
        d = s32(s32(s32((time + 256) * 48000) >> 10) * 900)
        q = abs(d) // abs(self.tempo)                # divs.l: towards zero
        u = (q if (d < 0) == (self.tempo < 0) else -q) & 0xffffffff
        target = self.LONGEST if u > self.LONGEST else self.SHORTEST if u < self.SHORTEST else u
        if not self.ready:
            self.ready, self.w, self.n, self.lp, self.hp, self.delay = True, 0, 0, 0, 0, target
        out = []
        for fr in range(32):
            diff = s32(target - self.delay)
            step = diff >> 13
            if step == 0 and diff != 0 and not self.w & 3:
                step = 1 if diff > 0 else -1
            self.delay = (self.delay + step) & 0xffffffff
            v = self.line[(self.w - self.delay) & (self.FRAMES - 1)] if self.delay <= self.n else 0
            y = s32((v >> 15) * g + (((v & 0x7fff) * g) >> 15))
            y = sat(y + (x[2 * fr] >> 3) + (x[2 * fr + 1] >> 3))
            q3, p3 = y >> 3, self.lp >> 3
            self.lp = sat((y - (q3 + (q3 >> 1))) + (p3 + (p3 >> 1)))
            h = s32(self.lp - self.hp)
            e = h >> 5
            self.hp = s32(self.hp + e)
            self.line[self.w] = s32(h - e)
            self.n = min(self.n + 1, self.FRAMES)
            y2 = sat(v + v)
            y4 = sat(y2 + y2)
            out += [sat(y4 + y2)] * 2
            self.w = (self.w + 1) & (self.FRAMES - 1)
        return out


MODELS = {"refdelay": RefDelay, "refreverb": RefReverb, "digidelay": Digital, "pots": PH.Pots}


class Effect:
    def __init__(self, mid, u):
        self.id, self.u = mid, u


# --- 2. the sites and the data block --------------------------------------------------------------------------------
class Block:
    """The part's data block, as composed (read from the payload)."""

    def __init__(self, runtime, at):
        self.rt, self.at = runtime, at

    def u32(self, off):
        return struct.unpack_from(">I", self.rt, self.at - E.PAYLOAD_DST + off)[0]

    def table(self, k):
        base = DATA["slots"][k]
        return [tuple(self.u32(base + 4 + 12 * i + 4 * j) for j in range(3)) for i in range(self.u32(base))]

    def names(self, k, i):
        return tuple(self.u32(DATA["names"] + 28 * (DATA["entries"] * k + i) + 4 * j) for j in range(7))


def cstr(stock, runtime, va):
    if E.PAYLOAD_DST <= va < E.PAYLOAD_DST + len(runtime):
        raw = runtime[va - E.PAYLOAD_DST:]
    else:
        raw = stock[va - compose.BASE:]
    return raw[:raw.index(b"\0")].decode("ascii")


def site_tests(key, stock, tweak, img, runtime, slots, only_effects, desc_used):
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    for name, s in SLOTS.items():
        got = img[s["site"] - compose.BASE:s["site"] - compose.BASE + 6]
        if name in slots:
            check(got == jsr(syms[s["entry"]]), f"{key}: {s['site']:#x} -> jsr {s['entry']} ({syms[s['entry']]:#x})")
        else:
            check(got == jsr(s["stock"]), f"{key}: {s['site']:#x} keeps jsr {s['stock']:#x}: no effect in the {name} slot")
    for site, entry in ((TRACK_SITE, "fx_track"), (LOAD_SITE, "fx_load"), (INIT_SITE, "fx_init")):
        got = img[site - compose.BASE:site - compose.BASE + 6]
        check(got == jsr(syms[entry]), f"{key}: {site:#x} -> jsr {entry} ({syms[entry]:#x})")
    sites = {compose.BASE + w["off"] for w in tweak["writes"]}
    if only_effects:
        want = BOOT_SITES | {SLOTS[n]["site"] for n in slots} | {TRACK_SITE, LOAD_SITE, INIT_SITE}
        check(sites == want, f"{key}: {len(sites)} writes, the slots', the gesture's, the header's and the payload's "
              "boot only "
              f"({', '.join(hex(a) for a in sorted(sites ^ want)) or 'nothing of the registrar'})")
    blk = Block(runtime, syms["fx_data"])

    def stock_desc(d, f):
        return struct.unpack_from(">I", stock, g7.DESC + 0x38 * d + f - compose.BASE)[0]
    for k, name in enumerate(ORDER):
        s, part_slot = SLOTS[name], PART["slots"]["fx." + name]
        effects = sorted(slots.get(name, {}).items())
        want = [(0, s["stock"], 0)] + [(i, syms[e.u["process"]], syms[e.u["reset"]]) for i, e in effects]
        check(blk.table(k) == want, f"{key}: the {name} slot's table: "
              + ", ".join(f"{i} -> {fn:#x} (reset {r:#x})" for i, fn, r in blk.table(k)))
        a, b = s["desc"]
        stock_fmt = tuple(int(f, 16) for f in part_slot["formatters"])
        n0 = blk.names(k, 0)
        check(n0 == (stock_desc(a, 0x2c), stock_desc(a, 0x34), stock_desc(b, 0x2c), stock_desc(b, 0x34),
                     stock_desc(a, 0x30)) + stock_fmt,
              f"{key}: the {name} slot's entry 0: the stock names "
              + ", ".join(repr(cstr(stock, runtime, v)) for v in n0[:5])
              + ", the stock formatters " + ", ".join(hex(f) for f in stock_fmt))
        for idx, (_i, e) in enumerate(effects, start=1):
            n = blk.names(k, idx)
            texts = [cstr(stock, runtime, v) for v in n[:5]]
            pa, pb = e.u["params"]
            want_t = [pa["long"], pa["short"], pb["long"], pb["short"], e.u["name"]]
            fmts = [stock_fmt[j] if p.get("format") is None else int(PART["int_format"], 16) if p["format"] == "int"
                    else syms[p["format"]] for j, p in enumerate((pa, pb))]
            check(texts == want_t and list(n[5:]) == fmts,
                  f"{key}: the {name} slot's {e.id}: {', '.join(map(repr, texts))}, formatters "
                  + ", ".join(hex(f) for f in n[5:]))
    check((blk.u32(DATA["desc"]), blk.u32(DATA["desc"] + 4)) == (g7.DESC, desc_used),
          f"{key}: the names go into {g7.DESC:#x} and {desc_used:#x}"
          + (" (the descriptor table the registrar moved)" if desc_used != g7.DESC else " (the stock table, twice)"))
    return syms, blk


def line_tests(key, tweak, info, mans, runtime):
    """The slots' lines (notes/68 §16): where the composer put them, and that the effects' code holds their address."""
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    lines = info["fx_lines"]
    for point in compose.FX_POINTS:
        asks = {m["id"]: m["_effect"]["line"] for m in mans.values()
                if m["_effect"] and m["_effect"]["point"] == point and m["_effect"].get("line")}
        sym = f"fx_line_{point[3:]}"
        if not asks:
            check(point not in lines and sym not in syms, f"{key}: no effect of the {point[3:]} slot asks for a line: none")
            continue
        at, n = lines[point]
        others = [(p["id"], p["bss_at"], p["bss_at"] + p["bss"]) for p in info["packages"] if p["bss"]]
        apart = all(e <= at or at + n <= b for _i, b, e in others)
        first = at == (info["pay"] + compose.gm.BSS_OFF + 15) & ~15 or point == "fx.reverb"
        held = all(struct.pack(">I", at) in runtime[syms[mans[i]["_effect"]["process"]] - E.PAYLOAD_DST:
                                                   syms[mans[i]["_effect"]["process"]] - E.PAYLOAD_DST + 0x400]
                   for i in asks)
        check(syms.get(sym) == at and at % 16 == 0 and n == max(asks.values()) and apart and first and held,
              f"{key}: the {point[3:]} slot's line at {at:#x}, {n} bytes ({', '.join(f'{i} asks {v}' for i, v in asks.items())}"
              f"), 16-aligned at the start of the variables, apart from the packages' variables, its address in the "
              "effect's code")


def sharing_tests(stock):
    """Two effects of one slot share its line (notes/68 §16): REFD and a copy of it with id 253 asking for 64 KiB,
    composed from a folder of packages made for the test."""
    kept = compose.MACHINES
    try:
        with tempfile.TemporaryDirectory() as d:
            compose.MACHINES = pathlib.Path(d)
            for pid in ("refdelay", "fxslot"):
                shutil.copytree(kept / pid, compose.MACHINES / pid)
            two = compose.MACHINES / "refdelay2"
            shutil.copytree(kept / "refdelay", two)
            (two / "refdelay.o").rename(two / "refdelay2.o")
            m = json.loads((two / "manifest.json").read_text())
            m["id"] = "refdelay2"
            m["build"]["objects"] = ["refdelay2.o"]
            m["uses"][0].update(id=253, line=65536)
            (two / "manifest.json").write_text(json.dumps(m))
            tweak, info = compose.compose(stock, ["refdelay", "refdelay2"])
    finally:
        compose.MACHINES = kept
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    at, n = info["fx_lines"]["fx.delay"]
    code = {p["id"]: (p["code_at"], p["code_at"] + p["code"]) for p in info["packages"]}
    blob = {int(p["dest"], 16): bytes.fromhex(p["hex"]) for p in tweak["append"]["parts"] if "hex" in p}
    held = []
    for pid, (lo, hi) in code.items():
        for dest, b in blob.items():
            if dest <= lo < dest + len(b):
                held.append(struct.pack(">I", at) in b[lo - dest:hi - dest])
    check(n == 65536 and syms.get("fx_line_delay") == at and len(held) == 2 and all(held),
          f"two effects of the delay slot (refdelay asks 32768, a copy with id 253 asks 65536): one line at {at:#x}, "
          f"{n} bytes, its address in both effects' code")


def refusal_tests(key):
    """The composer refuses an effect's line in every wrong form (notes/68 §16)."""
    src = compose.MACHINES / "refdelay"
    base = json.loads((src / "manifest.json").read_text())
    cases = [("a line without its patch point", lambda m: m["build"].update(patch_points=[])),
             ("a patch point without a line", lambda m: m["uses"][0].pop("line")),
             ("a size not a multiple of 16", lambda m: m["uses"][0].update(line=32760)),
             ("a size past 4 MiB", lambda m: m["uses"][0].update(line=compose.FX_LINE_MAX + 16)),
             ("another kind of patch point", lambda m: m["build"].update(
                 patch_points=[{"symbol": "fx_line", "kind": "machine_index"}]))]
    refused, kept = [], compose.MACHINES
    try:
        with tempfile.TemporaryDirectory() as d:
            compose.MACHINES = pathlib.Path(d)
            for name, change in cases:
                (compose.MACHINES / "refdelay").mkdir(exist_ok=True)
                m = json.loads(json.dumps(base))
                change(m)
                (compose.MACHINES / "refdelay" / "manifest.json").write_text(json.dumps(m))
                try:
                    compose.load_manifest("refdelay")
                except SystemExit:
                    refused.append(name)
            shutil.rmtree(compose.MACHINES / "refdelay")
    finally:
        compose.MACHINES = kept
    check(len(refused) == len(cases), f"{key}: the composer refuses {', '.join(refused)}"
          + (f"; accepts {', '.join(n for n, _c in cases if n not in refused)}" if len(refused) < len(cases) else ""))


def named(read, blk, k, idx, desc_used):
    """The slot's two parameters named as entry idx of the data block says, in both tables and objects."""
    n = blk.names(k, idx)
    a = SLOTS[ORDER[k]]["desc"][0]
    ok = True
    for t in {g7.DESC, desc_used}:
        da = struct.unpack(">17I", read(t + 0x38 * a + 0x2c, 68))     # a's long, group, short; then b's at +14
        ok &= (da[0], da[2], da[1], da[14], da[16], da[15]) == (n[0], n[1], n[4], n[2], n[3], n[4])
    ok &= struct.unpack(">I", read(obj(a) + 0x20, 4))[0] == n[5]
    ok &= struct.unpack(">I", read(obj(a + 1) + 0x20, 4))[0] == n[6]
    return ok


# --- 3. the audio: two engines side by side -------------------------------------------------------------------------
class Side:
    """One engine and what the mixer does around the effects."""

    def __init__(self, img, runtime=None, tweak=None):
        self.e = TC.engine(img, runtime, tweak)
        uc = self.e.uc
        uc.mem_map(0x40800000, 0x00800000)       # the interface objects (0x40a71754 + 100 i)
        uc.mem_map(0x42400000, 0x00400000)       # the delay line (the engine maps 0x42000000-0x42400000)
        uc.mem_map(0x4a000000, 0x00800000)       # the uncached aliases of the effects' lines
        uc.mem_map(0xfc040000, 0x00010000)       # the eDMA's registers and descriptors: zeros
        uc.mem_map(FIX, 0x00100000)              # the patterns' fixture
        self.bad = []

    def call(self, fn, *args):
        uc = self.e.uc
        sp = E.STACK - 0x200
        uc.mem_write(sp, struct.pack(">I" + "I" * len(args), E.STOP, *args))
        uc.reg_write(mk.UC_M68K_REG_A7, sp)
        vals = [0x5a5a0000 + i for i in range(len(KEPT))]
        for r, v in zip(KEPT, vals):
            uc.reg_write(r, v)
        try:
            uc.emu_start(fn, E.STOP, count=3_000_000)
        except UcError as err:
            self.bad.append(f"{fn:#x}: {err} at {uc.reg_read(mk.UC_M68K_REG_PC):#x}")
            return False
        done = uc.reg_read(mk.UC_M68K_REG_PC) == E.STOP
        kept = all(uc.reg_read(r) == v for r, v in zip(KEPT, vals))
        sp_ok = uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        if not done:
            self.bad.append(f"{fn:#x}: did not return (pc {uc.reg_read(mk.UC_M68K_REG_PC):#x})")
        return done and kept and sp_ok

    def effect(self, fn, out, inp, params):
        self.e.emac.macsr = 0xa0                  # as the mixer leaves them (0x40056940)
        self.e.emac.acc[:] = [0, 0, 0, 0]         # in place: emac.py's fast mac.l keeps this list (notes/69 §14.6)
        return self.call(fn, out, inp, params)

    def read(self, va, n):
        return bytes(self.e.uc.mem_read(va, n))

    def write(self, va, data):
        self.e.uc.mem_write(va, data)

    def frames(self, va):
        return list(struct.unpack(">64i", self.read(va, 256)))


def audio_tests(key, stock, img, runtime, tweak, syms, blk, slots, blocks, desc_used):
    a, b = Side(stock), Side(img, runtime, tweak)
    rng = np.random.default_rng(68)
    D = syms["fx_data"]
    fn = {n: syms[s["entry"]] if n in slots else s["stock"] for n, s in SLOTS.items()}
    ids = {n: next(iter(slots[n])) for n in slots}                  # the effect each slot holds
    models = {n: MODELS[slots[n][ids[n]].id]() for n in slots}
    fx = Patterns(lambda va, data: (a.write(va, data), b.write(va, data)), FIX)   # the same in both engines
    fx.set(1, hdr())                             # pattern 1: the stock effects
    chosen = hdr(**{n: ids.get(n, 0) for n in SLOTS})
    boots = [("no singleton", chosen, dict(root=False)), ("no playing pattern", chosen, dict(active=False)),
             ("pattern number 96", chosen, dict(playing=96)),
             ("a wrong check byte", hdr(**{n: ids.get(n, 0) for n in SLOTS}, bad=True), {}),
             ("a header never written", bytes(3), {}), ("id 0", hdr(), {}),
             ("an id the build does not hold", hdr(77, 77), {}),
             ("the other slot's id", hdr(REF_IDS["reverb"], REF_IDS["delay"]), {})]
    per = max(2, blocks // 12)
    plan = []                                    # (phase, (pattern 0's bytes 29..31, how the patterns are linked))
    for _name, rec, kw in boots:
        plan += [("A", (rec, kw))] + [("A", None)] * (per - 1)
    plan += [("B", (chosen, {}))] + [("B", None)] * (2 * per - 1)
    plan += [("C", (None, dict(playing=1)))] + [("C", None)] * (per - 1)     # a pattern change, to the stock effects
    plan += [("D", (None, {}))] + [("D", None)] * (2 * per - 1)              # and back
    playing, played = set(), set()
    calls_ok, same, model_ok, rest_ok = True, {"A": True, "C": True}, {n: True for n in slots}, True
    names_ok = {"B": False, "C": False, "D": False}
    for i, (phase, act) in enumerate(plan):
        if act:                                  # the part reads the playing pattern at the next block
            if act[0] is not None:
                fx.set(0, act[0])
            fx.link(**act[1])
            playing = set(slots) if phase in "BD" else set()
        x = rng.integers(-(1 << 31), 1 << 31, size=64) if i % 5 == 0 else rng.integers(-(1 << 28), 1 << 28, size=64)
        y = rng.integers(-(1 << 31), 1 << 31, size=64) if i % 7 == 0 else rng.integers(-(1 << 28), 1 << 28, size=64)
        words = [0x7f00] * 4 if i % 9 == 0 else [int(rng.integers(0, 128)) << 8 for _ in range(4)]
        for s in (a, b):
            s.write(P + 428, struct.pack(">4h", *words))
            calls_ok &= s.call(TAPS, P)
        for n, s_ in SLOTS.items():
            inp = [int(v) for v in (x if n == "delay" else y)]
            for s in (a, b):
                s.write(BUS, struct.pack(">64i", *inp))
            if n in playing and n not in played:     # the stock effect stops: a block of silence through it
                calls_ok &= a.effect(s_["stock"], QUIET_OUT, QUIET, QUIET)
                models[n].reset()
            if n not in playing:
                calls_ok &= a.effect(s_["stock"], s_["out"], BUS, P + s_["params"])
            calls_ok &= b.effect(fn[n], s_["out"], BUS, P + s_["params"])
            if n in playing:
                params = struct.unpack(">2h", b.read(P + s_["params"], 4))
                model_ok[n] &= b.frames(s_["out"]) == models[n](inp, params)
        played = set(playing)
        for s in (a, b):
            calls_ok &= s.call(LINES)
            calls_ok &= s.call(WRITE)
        if phase in names_ok and act:            # the first block of a pattern: the names
            names_ok[phase] = all(named(b.read, blk, ORDER.index(n), 0 if phase == "C" else 1, desc_used)
                                  for n in slots)
        sa, sb = bytearray(a.read(*SRAM)), bytearray(b.read(*SRAM))
        for n in playing:                        # an effect's return is the model's (above): the rest is compared
            lo = SLOTS[n]["out"] - SRAM[0]
            sa[lo:lo + 256] = sb[lo:lo + 256] = bytes(256)
        if playing:
            rest_ok &= sa == sb
        else:
            same[phase] &= sa == sb
    check(same["A"], f"{key}: the playing pattern choosing nothing: {', '.join(n for n, _r, _k in boots)}: the stock "
          f"effects, the slots' returns and the whole SRAM the stock OS's ({len(boots) * per} blocks)")
    check(names_ok["B"], f"{key}: a pattern choosing {', '.join(str(ids[n]) for n in slots)}: at the first block the "
          "slots' parameters named after the effects, in the descriptor tables and the formatters")
    for n in slots:
        mid = slots[n][ids[n]].id
        check(model_ok[n], f"{key}: the {n} slot: {mid}'s return the model's, bit for bit, the stock {n} given a block "
              "of silence as it stops, the effect reset as it starts, twice")
    check(rest_ok, f"{key}: while the effects play, the rest of the SRAM is the stock OS's: the stock effects' state "
          "is left alone")
    check(same["C"] and names_ok["C"], f"{key}: a pattern change to a pattern with the stock effects: the stock "
          "effects and the SRAM agree with the stock OS again, the stock names back at its first block")
    check(names_ok["D"], f"{key}: the change back: the effects' names again at its first block")
    big = all(hashlib.sha256(a.read(lo, hi - lo)).digest() == hashlib.sha256(b.read(lo, hi - lo)).digest()
              for lo, hi in SDRAM)
    check(big, f"{key}: the stock effects' lines in SDRAM (and their uncached aliases) as the stock OS leaves them")
    check(calls_ok and not a.bad and not b.bad,
          f"{key}: every call returns to its caller with d2-d7/a2-a6 kept and the stack as the stock effect leaves it"
          + (f"; {'; '.join((a.bad + b.bad)[:3])}" if a.bad or b.bad else ""))
    check(not a.e.unmapped and not b.e.unmapped, f"{key}: no access outside memory "
          f"{[hex(x) for _pc, x in (a.e.unmapped + b.e.unmapped)[:4]]}")


# --- 4. the gesture -------------------------------------------------------------------------------------------------
class StepModel:
    """fx_step as fxslot.c writes it."""

    def __init__(self, tables, cur):
        self.ids = [[e[0] for e in t] for t in tables]
        self.cur, self.acc, self.last_slot, self.last_dir, self.last_time = list(cur), 0, 0, 0, 0

    def __call__(self, desc, step, now):
        slot = 0 if desc == 37 else 1 if desc == 39 else -1
        if slot < 0 or len(self.ids[slot]) < 2:
            return "stock"
        d = 1 if step > 0 else 2
        if slot != self.last_slot or d != self.last_dir or ((now - self.last_time) & 0xffffffff) > PAUSE:
            self.acc = 0
        self.last_slot, self.last_dir, self.last_time = slot, d, now
        self.acc += 1
        if self.acc < 4:
            return "taken"
        self.acc = 0
        ids = self.ids[slot]
        i = ids.index(self.cur[slot]) if self.cur[slot] in ids else 0
        if (i + 1 >= len(ids)) if d == 1 else i == 0:
            return "taken"
        self.cur[slot] = ids[i + 1 if d == 1 else i - 1]
        return "changed"


class Gesture:
    """fx_track, called as the encoder handler calls it at 0x4001f89a, with the handler's frame; the patterns linked as
    the OS links them, the shown one chosen by the bench (0x4006a96c), the header's notify counted (0x400d0f6c)."""

    def __init__(self, img, runtime, syms):
        self.u = t7.UI(img, runtime)
        self.u.uc.mem_map(0xfc070000, 0x1000)    # the DMA timer 0
        self.u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        self.u.hooks = {SAVE: ("save", 0), SHOWN_OK: ("shown", 1), NOTIFY: ("notify", 0)}
        self.show(0)
        self.syms, self.D = syms, syms["fx_data"]
        self.fx = Patterns(lambda va, data: self.u.uc.mem_write(va, data), GFIX)
        self.fx.link()
        self.unprotected = []
        watch(self.u.uc, [(h + HDR, h + HDR + 3) for h in self.fx.headers.values()], self.unprotected)
        self.exits = 0

        def hk(uc, addr, size, ud):
            self.exits += 1
        self.u.uc.hook_add(UC_HOOK_CODE, hk, begin=HANDLER_END, end=HANDLER_END)

    def show(self, n):
        self.u.hooks[SHOWN_IDX] = ("selected", n)

    def track(self, desc, step, now=0):
        """(taken, d0, registers as expected)"""
        uc, u = self.u.uc, self.u
        uc.mem_write(TIMER, struct.pack(">I", now & 0xffffffff))
        fp, old_fp = 0x93000100, 0x93000400
        saved = [0x6b6b0000 + i for i in range(len(FRAME))]
        uc.mem_write(fp - 84, struct.pack(">10I", *saved))
        uc.mem_write(fp, struct.pack(">II", old_fp, t7.STOP))
        sp = t7.STACK - 0x400
        uc.mem_write(sp, struct.pack(">II", t7.STOP, desc))
        uc.reg_write(mk.UC_M68K_REG_A7, sp)
        uc.reg_write(mk.UC_M68K_REG_A6, fp)
        live = [0x3c3c0000 + i for i in range(len(FRAME))]
        live[FRAME.index(mk.UC_M68K_REG_D4)] = step & 0xffffffff
        for r, v in zip(FRAME, live):
            uc.reg_write(r, v)
        before = self.exits
        u.calls.clear()
        u.bad.clear()
        uc.emu_start(self.syms["fx_track"], t7.STOP, count=200_000)
        taken = self.exits > before
        d0 = uc.reg_read(mk.UC_M68K_REG_D0)
        regs = [uc.reg_read(r) for r in FRAME]
        a6 = uc.reg_read(mk.UC_M68K_REG_A6)
        if taken:                                # the handler's end: its registers from its frame, its return 0
            ok = d0 & 0xff == 0 and regs == saved and a6 == old_fp and uc.reg_read(mk.UC_M68K_REG_A7) == fp + 8
        else:                                    # the stock call: the caller's registers, d4 the step
            ok = regs == live and a6 == fp and uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        ok &= uc.reg_read(mk.UC_M68K_REG_SR) & 0x700 == 0      # the interrupt level back
        return taken, d0, ok and not u.bad

    def acc(self):
        return self.read(self.D + STATE + 4, 1)[0]

    def cur(self):
        return list(self.read(self.D + STATE, 2))

    def header(self, n):
        return self.read(self.fx.headers[n] + HDR, 3)

    def count(self, name):
        return sum(1 for n, _a in self.u.calls if n == name)

    def read(self, va, n):
        return bytes(self.u.uc.mem_read(va, n))


def names_now(read, k, desc_used):
    """The slot's two parameters' names, group and formatters as the OS reads them now."""
    a = SLOTS[ORDER[k]]["desc"][0]
    return b"".join(read(t + 0x38 * a + 0x2c, 68) for t in (g7.DESC, desc_used)) + read(obj(a) + 0x20, 4) \
        + read(obj(a + 1) + 0x20, 4)


def gesture_tests(key, img, runtime, syms, blk, slots, desc_used):
    g = Gesture(img, runtime, syms)
    stock_ui = t7.UI(img, runtime)
    tables = [blk.table(k) for k in range(2)]
    model = StepModel(tables, [0, 0])
    # descriptors that are not the gesture's, and slots without an effect: the stock call
    others = [9, 22, 23, 26, 27, 38, 40] + [SLOTS[n]["desc"][0] for n in SLOTS if n not in slots]
    ok = True
    for desc in others:
        taken, d0, regs = g.track(desc, 1)
        ok &= not taken and regs and d0 == stock_ui.call(STOCK_TEST, desc) and not g.u.calls
    check(ok, f"{key}: descriptors {', '.join(map(str, others))}: the stock call 0x4005a5cc, its answer, the caller's "
          "registers kept, nothing read or written")
    # the steps, on the shown pattern, which plays (pattern 0, its header never written), against the model
    now, events = 0, []
    for n in slots:
        d = SLOTS[n]["desc"][0]
        events += [(d, 1, 0)] * 4                                      # four detents: the first effect
        events += [(d, 1, 0)] * 8                                      # past the end: nothing more
        events += [(d, -1, 0)] * 2 + [(d, 1, 0)] + [(d, -1, 0)] * 4    # a change of direction starts the count again
        events += [(d, 1, 0)] * 2 + [(d, 1, PAUSE + 1)] * 2 + [(d, 1, 0)] * 2   # a pause starts it again
    if len(slots) == 2:                                                # a change of slot starts it again
        dd, dr = SLOTS["delay"]["desc"][0], SLOTS["reverb"]["desc"][0]
        events += [(dd, -1, 0)] * 2 + [(dr, -1, 0)] * 2 + [(dd, -1, 0)] * 2 + [(dd, -1, 0)] * 2
    mismatch, changes, bad_regs, bad_names, bad_hdr, bad_notify, saves = [], 0, 0, 0, 0, 0, 0
    for j, (desc, step, gap) in enumerate(events):
        now = (now + 1000 + gap) & 0xffffffff
        want = model(desc, step, now)
        taken, _d0, regs = g.track(desc, step, now)
        raw = g.header(0)
        if taken != (want != "stock") or choice(raw) != model.cur or g.acc() != model.acc:
            mismatch.append(f"event {j} ({desc}, {step:+d}): header {raw.hex()} acc {g.acc()}, "
                            f"model {model.cur} {model.acc}")
        bad_regs += not regs
        saves += g.count("save")
        if want == "changed":
            changes += 1
            k = 0 if desc == 37 else 1
            idx = [e[0] for e in tables[k]].index(model.cur[k])
            bad_names += not named(g.read, blk, k, idx, desc_used) or g.cur()[k] != model.cur[k]
            bad_hdr += raw != hdr(*model.cur)
            bad_notify += g.count("notify") != 1
        else:
            bad_notify += g.count("notify") != 0
    check(not mismatch, f"{key}: {len(events)} detents, the gesture as the model: four in one direction for a step, "
          "the count again after a change of direction, of slot or a pause, the ends of the table"
          + (f"; {'; '.join(mismatch[:3])}" if mismatch else ""))
    check(not bad_regs, f"{key}: each detent ends the handler with 0, its registers back from its frame, the "
          "interrupt level back")
    check(changes > 0 and not bad_hdr and not bad_notify and not saves,
          f"{key}: {changes} changes, each writing the shown pattern's bytes 29 to 31 (the ids, the check byte) and "
          "calling its notify once; no notify without a change; the settings never saved")
    check(not bad_names, f"{key}: each change naming the slot's parameters after the entry at once (the shown pattern "
          "plays): long and short names and group in both descriptor tables, the formatters in the interface objects")
    n = next(iter(slots))
    k, d = ORDER.index(n), SLOTS[n]["desc"][0]
    # a shown pattern that does not play: its header and its notify, the names those of what plays
    g.fx.set(1, hdr())
    g.fx.link(playing=1)
    before, names_before, cur_before = g.header(0), names_now(g.read, k, desc_used), g.cur()
    step = -1 if choice(before)[k] else 1
    res = [g.track(d, step, now + PAUSE + 10 + 1000 * i) for i in range(4)]
    want = choice(before)
    want[k] = tables[k][1][0] if step == 1 else 0
    check(all(r[0] and r[2] for r in res) and g.header(0) == hdr(*want) and g.header(1) == hdr()
          and g.count("notify") == 1 and names_now(g.read, k, desc_used) == names_before and g.cur() == cur_before,
          f"{key}: pattern 0 shown, pattern 1 playing: four detents change pattern 0's header to {want}, one notify; "
          "pattern 1's header, the names and the part's state untouched")
    # an id the build does not hold moves to the first effect
    g.fx.link(playing=0)
    rec = [0, 0]
    rec[k] = 77
    g.fx.set(0, hdr(*rec))
    now += PAUSE + 100000
    res = [g.track(d, 1, now + 1000 * i)[0] for i in range(4)]
    check(all(res) and choice(g.header(0))[k] == tables[k][1][0],
          f"{key}: the {n} slot holding id 77, not in the build: four detents right give {choice(g.header(0))[k]}, "
          "its first effect")
    # no singleton: the detents taken, nothing written
    g.fx.link(root=False)
    before = [g.header(i) for i in range(3)]
    now += PAUSE + 100000
    res = [g.track(d, 1, now + 1000 * i) for i in range(4)]
    check(all(r[0] and r[2] for r in res) and [g.header(i) for i in range(3)] == before and not g.u.calls,
          f"{key}: no patterns' singleton: four detents taken, no header written, nothing called")
    check(not g.unprotected, f"{key}: every write of bytes 29 to 31 with the interrupts masked"
          + (f"; {[(hex(pc), hex(a)) for pc, a in g.unprotected[:3]]}" if g.unprotected else ""))


# --- 5. the pattern: the header's loader, initializer, save and load -------------------------------------------------
def storage_tests(key, stock, img, runtime):
    s, p = t7.UI(stock), t7.UI(img, runtime)
    for u in (s, p):
        u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    H1, H2, H3 = 0x92000000, 0x92001000, 0x92002000
    B1, B2, SER = 0x92010000, 0x92020000, 0x92030000
    unprotected = []
    watch(p.uc, [(h + HDR, h + HDR + 3) for h in (H1, H2, H3, B2 + HDR_AT)], unprotected)   # B1: the OS's own copies

    def rd(u, va, n=64):
        return bytes(u.uc.mem_read(va, n))

    def header(u, at, rec):                      # a header as the OS initializes it, then bytes 29 to 31
        u.uc.mem_write(at, bytes(64))
        u.call(HDR_INIT, at, 0)
        u.uc.mem_write(at + HDR, rec)

    def outside(raw):
        return raw[:HDR] + raw[HDR + 3:]
    # the stock OS: the loader and the initializer leave the bytes, the copy keeps them
    header(s, H1, hdr(254, 255))
    s.uc.mem_write(H2, b"\xa5" * 64)
    d0 = s.call(HDR_LOAD, H2, H1)
    s.uc.mem_write(H3, b"\xa5" * 64)
    s.call(HDR_INIT, H3, 0)
    kept = rd(s, H2)[HDR:HDR + 3] == rd(s, H3)[HDR:HDR + 3] == b"\xa5" * 3
    s.call(HDR_COPY, H3, H1)
    check(d0 & 0xff == 1 and kept and rd(s, H3) == rd(s, H1),
          f"{key}: the stock OS: its loader and its initializer leave bytes 29 to 31 as the buffer held them, its "
          "header copy keeps the 64 bytes")
    # the loader with fx_load
    ok, cases = True, [("a choice", hdr(254, 255)), ("ids the build may not hold", hdr(77, 3)),
                       ("a wrong check byte", hdr(254, 255, bad=True)), ("zeros", bytes(3)), ("0xff", b"\xff" * 3)]
    for _name, rec in cases:
        for u in (s, p):
            header(u, H1, rec)
            u.uc.mem_write(H2, b"\xa5" * 64)
        ds, dp = s.call(HDR_LOAD, H2, H1), p.call(HDR_LOAD, H2, H1)
        rs, rp = rd(s, H2), rd(p, H2)
        want = rec if valid(rec) else hdr()
        ok &= ds & 0xff == dp & 0xff == 1 and outside(rp) == outside(rs) and rp[HDR:HDR + 3] == want
    check(ok, f"{key}: the loader with fx_load: {', '.join(n for n, _r in cases)}: the header as the stock OS loads "
          "it, bytes 29 to 31 copied when their check holds, the stock effects (0, 0, 0x5a) otherwise, its return 1")
    # the initializer with fx_init
    for u in (s, p):
        u.uc.mem_write(H3, b"\xa5" * 64)
        u.call(HDR_INIT, H3, 0)
    new_ok = outside(rd(p, H3)) == outside(rd(s, H3)) and rd(p, H3)[HDR:HDR + 3] == hdr()
    header(p, H3, hdr(254, 255))
    before = rd(p, H3)
    p.call(HDR_INIT, H3, 1)
    check(new_ok and rd(p, H3) == before, f"{key}: the initializer with fx_init: a new header as the stock OS's plus "
          "the stock effects; with keep, the header untouched")
    # a whole pattern: initialized, chosen, saved, loaded, copied
    p.uc.mem_write(B1, bytes(PAT_LEN))
    p.call(PAT_INIT, B1, 0)
    p.uc.mem_write(B1 + HDR_AT + HDR, hdr(254, 255))
    p.uc.mem_write(SER, bytes(SER_LEN))
    saved = p.call(PAT_SAVE, SER, B1, 0) & 0xff == 1 and rd(p, SER + SER_HDR_AT) == rd(p, B1 + HDR_AT)
    serial = rd(p, SER, SER_LEN)
    for u in (s, p):
        u.uc.mem_write(SER, serial)
        u.uc.mem_write(B2, b"\xa5" * PAT_LEN)
    ls, lp = s.call(PAT_LOAD, B2, SER, 73), p.call(PAT_LOAD, B2, SER, 73)
    bs, bp = rd(s, B2, PAT_LEN), rd(p, B2, PAT_LEN)
    at = HDR_AT + HDR
    loaded = (ls & 0xff == lp & 0xff == 1 and bp[at:at + 3] == hdr(254, 255)
              and bp[:at] + bp[at + 3:] == bs[:at] + bs[at + 3:] and struct.unpack_from(">I", bp, NUM_AT)[0] == 73)
    p.uc.mem_write(B1, bytes(PAT_LEN))
    p.call(MEMCPY, B1, B2, PAT_LEN)
    copied = rd(p, B1, PAT_LEN) == bp
    check(saved and loaded and copied, f"{key}: a whole pattern choosing 254, 255: saved (0x4005ba0a) with its header, "
          "loaded (0x4005b894) as the stock OS loads it plus the choice, its number 73, copied (0x4008f1f0) whole")
    for bad in (b"\x12\x34\x56", bytes(3)):      # a file whose bytes choose nothing (the stock OS saved them)
        p.uc.mem_write(SER, serial)
        p.uc.mem_write(SER + SER_HDR_AT + HDR, bad)
        p.uc.mem_write(B2, b"\xa5" * PAT_LEN)
        p.call(PAT_LOAD, B2, SER, 73)
        loaded &= rd(p, B2 + at, 3) == hdr()
    check(loaded, f"{key}: a file whose bytes 29 to 31 choose nothing (12 34 56, zeros): loaded with the stock effects")
    check(not unprotected and p.uc.reg_read(mk.UC_M68K_REG_SR) & 0x700 == 0,
          f"{key}: every write of bytes 29 to 31 with the interrupts masked, the level back after"
          + (f"; {[(hex(pc), hex(a)) for pc, a in unprotected[:3]]}" if unprotected else ""))


# --- 6. the cost ------------------------------------------------------------------------------------------------------
def counted(side, fn, *args):
    before = side.e.instructions
    side.effect(fn, *args) if len(args) == 3 else side.call(fn, *args)
    return side.e.instructions - before


def stats(counts):
    rest = counts[1 + COST_WARM:1 + COST_WARM + COST_BLOCKS]
    return {"first": counts[0], "mean": round(sum(rest) / len(rest)), "max": max(rest)}


def cost_tests(key, stock, img, runtime, tweak, syms, slots):
    a, b, c = Side(stock), Side(img, runtime, tweak), Side(img, runtime, tweak)
    fx = Patterns(lambda va, data: [s.write(va, data) for s in (a, b, c)], FIX)
    for s in (a, b, c):
        s.e.count_instructions()
    rng = np.random.default_rng(17)
    blocks = [[int(v) for v in rng.integers(-(1 << 28), 1 << 28, size=64)] for _ in range(1 + COST_WARM + COST_BLOCKS)]
    entry = {n: syms[SLOTS[n]["entry"]] for n in slots}
    ok = True
    for n, effects in slots.items():
        s_, ((num, e),) = SLOTS[n], effects.items()
        words = struct.pack(">4h", *(COST_WORDS["delay"] + COST_WORDS["reverb"]))

        def run(choice, sides_fns):
            fx.set(0, hdr(**{n: choice}))
            fx.link()
            out = {id(s): [] for s, _f in sides_fns}
            for x in blocks:
                for s, f in sides_fns:
                    s.write(P + 428, words)
                    s.call(TAPS, P)
                    s.write(BUS, struct.pack(">64i", *x))
                    out[id(s)].append(counted(s, f, s_["out"], BUS, P + s_["params"]))
                    s.call(LINES)
                    s.call(WRITE)
            return [out[id(s)] for s, _f in sides_fns]
        stock_c, slot_stock = run(0, [(a, s_["stock"]), (b, entry[n])])
        silence = counted(a, s_["stock"], QUIET_OUT, QUIET, QUIET)     # the stock effect's block of silence
        reset = syms[e.u["reset"]] if e.u.get("reset") else None
        reset_c = counted(c, reset) if reset else 0
        alone, slot_fx = run(num, [(c, syms[e.u["process"]]), (b, entry[n])])
        ok &= not a.bad and not b.bad and not c.bad
        st, ef = stats(stock_c), stats(alone)
        over_stock = max(y - x for x, y in zip(stock_c, slot_stock))
        over_fx = max(y - x for x, y in zip(alone[1:], slot_fx[1:]))
        switch = slot_fx[0] - alone[0] - reset_c - silence
        mine = dict(ef, reset=reset_c, package=e.id)
        slot = {"stock": st, "overhead": {"stock": over_stock, "effect": over_fx, "switch": switch, "silence": silence}}
        for where, k, v in ((COST["effects"], num, mine), (COST["slots"], "fx." + n, slot)):
            if k in where:
                check(where[k] == v, f"{key}: the cost of {k} as counted in the builds before: {v}")
            where[k] = v
        print(f"  cost  {key}: the {n} slot: the stock {n} first {st['first']}, mean {st['mean']}, max {st['max']}; "
              f"{e.id} ({num}) alone first {ef['first']}, mean {ef['mean']}, max {ef['max']}, reset {reset_c}; "
              f"fxslot adds {over_stock} with the stock choice, {over_fx} with the effect, {switch} in a switch's "
              f"block besides the stock effect's block of silence ({silence}) (instructions per block)")
        declared = compose.load_manifest(e.id).get("cost", {}).get("emulation", {})
        if isinstance(declared.get("max"), int):
            want = {k: declared.get(k) for k in ("first", "mean", "max", "reset")}
            got = {k: COST["effects"][num][k] for k in want}
            check(want == got, f"{key}: {e.id}'s declared cost {want} is the one counted {got}")
        else:
            print(f"  note  {key}: {e.id} declares no cost yet: the counted numbers are in build/fx-cost.json")
        pc = PART.get("cost", {}).get("emulation", {})
        if pc.get("stock", {}).get("fx." + n):
            want = {"stock": pc["stock"]["fx." + n], "overhead": pc["overhead"]["fx." + n]}
            check(want == COST["slots"]["fx." + n], f"{key}: fxslot's declared cost for the {n} slot {want} is the one "
                  f"counted {COST['slots']['fx.' + n]}")
        else:
            print(f"  note  {key}: fxslot declares no cost for the {n} slot yet: the counted numbers are in "
                  "build/fx-cost.json")
    check(ok, f"{key}: every counted call returns to its caller with d2-d7/a2-a6 kept")


# --- 7. Digital Delay ------------------------------------------------------------------------------------------------
DIGI_PHASES = [("750 frames of delay, Fdbk 96", 60, 0, 96, 1 << 28),
               ("Fdbk 127, full-scale noise", 40, 0, 127, 1 << 31),
               ("the delay moved to 2 250 frames", 60, 2 << 8, 96, 1 << 28),
               ("silence, the tail", 40, 2 << 8, 96, 0)]


def pppccc_image(stock, path):
    """The official MAIN OS with PPPCCC's patch applied after the patches it requires (06 delay-fx requires 00 core),
    found by id next to it; every write's old bytes checked by their SHA-256."""
    path = pathlib.Path(path)
    by_id = {json.loads(f.read_text()).get("id"): f for f in path.parent.glob("[0-9]*.json")}
    img, done = bytearray(stock), set()

    def apply(f):
        t = json.loads(f.read_text())
        for req in t.get("requires") or []:
            if req not in done:
                if req not in by_id:
                    sys.exit(f"!! {f.name} requires {req}, not found next to it")
                apply(by_id[req])
        for w in t["writes"]:
            old = bytes(img[w["off"]:w["off"] + w["len"]])
            if hashlib.sha256(old).hexdigest() != w["old_sha256"]:
                sys.exit(f"!! {f.name}: {w['va']}: not the bytes it expects")
            img[w["off"]:w["off"] + w["len"]] = bytes.fromhex(w["new"])
        done.add(t["id"])
    apply(path)
    return bytes(img)


def digital_tests(key, stock, img, runtime, tweak, syms, pppccc):
    b = Side(img, runtime, tweak)
    theirs = Side(pppccc_image(stock, pppccc)) if pppccc else None
    model = Digital()
    rng = np.random.default_rng(18)
    out = SLOTS["delay"]["out"]
    bad, theirs_bad, first_bad, n = [], [], None, 0
    for rnd in ("from start-up", "after a reset"):
        if rnd == "after a reset":
            b.call(syms["digi_reset"])
            model.reset()
        for name, count, time, fdbk, amp in DIGI_PHASES:
            for i in range(count):
                x = ([int(v) for v in rng.integers(-amp, amp, size=64)] if amp else [0] * 64)
                for s_ in (b, theirs) if theirs and rnd == "from start-up" else (b,):
                    s_.write(P + 428, struct.pack(">2h", time, fdbk << 8))
                    s_.write(BUS, struct.pack(">64i", *x))
                b.effect(syms["digi_process"], out, BUS, P + 428)
                got, want = b.frames(out), model(x, (time, fdbk << 8))
                if got != want:
                    bad.append(f"{rnd}, {name}, block {i}")
                if theirs and rnd == "from start-up":
                    theirs.effect(PPPCCC_DD, out, BUS, P + 428)
                    if theirs.frames(out) != got:
                        theirs_bad.append(f"{name}, block {i}")
                n += 1
    loud = sum(1 for v in model.line if v)
    check(not bad and not b.bad, f"{key}: Digital Delay alone, {n} blocks ({', '.join(p_[0] for p_ in DIGI_PHASES)}; "
          f"from start-up, then again after a reset): its outputs the model's, bit for bit ({loud} frames of the line "
          "written non-zero)" + (f"; {'; '.join(bad[:3])}" if bad else ""))
    if theirs:
        check(not theirs_bad and not theirs.bad, f"{key}: Digital Delay against PPPCCC's own code ({pppccc}, entry "
              f"{PPPCCC_DD:#x}) from start-up: the same outputs, bit for bit, {n // 2} blocks"
              + (f"; {'; '.join(theirs_bad[:3])}" if theirs_bad else ""))
    else:
        print(f"  note  {key}: no --pppccc: Digital Delay checked against the model only")


# --- 8. POTS ----------------------------------------------------------------------------------------------------------
def noise(rng, amp, burst=1, every=1):
    """The bus, block i: noise of +-amp in the first burst blocks of every every, else silence."""
    return lambda i: ([int(v) for v in rng.integers(-amp, amp, size=64)] if amp and i % every < burst else [0] * 64)


def pots_phases(rng):
    """(name, blocks, the words at P + 428 for block i, the bus for block i)."""
    med = PH.K_BUS // 2                          # the median machine's peak on the bus (notes/69 §12.5)
    return [("a burst at the median machine's level, its echoes (Time 0, Fdbk 96)", 150,
             lambda i: (0, 96 << 8), noise(rng, med, 8, 150)),
            ("noise at that level, Time 1, Fdbk 64", 80, lambda i: (1 << 8, 64 << 8), noise(rng, med)),
            ("full-scale noise at Fdbk 127", 60, lambda i: (0, 127 << 8), noise(rng, 1 << 31)),
            ("Time sliding 0 to 6, Fdbk rising 0 to 127, a burst every 20 blocks", 120,
             lambda i: (6 * 256 * i // 120, 127 * 256 * i // 120), noise(rng, 2 * med, 4, 20)),
            ("silence, the tail at Fdbk 110", 80, lambda i: (0, 110 << 8), noise(rng, 0))]


POTS_LONG = 2400                                 # blocks after the second round: past the first dropout


def pots_tests(key, img, runtime, tweak, syms):
    b, model = Side(img, runtime, tweak), PH.Pots()
    rng = np.random.default_rng(69)
    out = SLOTS["delay"]["out"]
    bad, n = [], 0
    rounds = [("from start-up", pots_phases(rng)), ("after a reset", pots_phases(rng)),
              ("on past the first dropout", [("a burst every 200 blocks, Time 0, Fdbk 90", POTS_LONG,
                                              lambda i: (0, 90 << 8), noise(rng, PH.K_BUS // 2, 6, 200))])]
    for rnd, phases in rounds:
        if rnd == "after a reset":
            b.call(syms["pots_reset"])
            model.reset()
        for name, count, words, bus in phases:
            for i in range(count):
                w, x = words(i), bus(i)
                b.write(P + 428, struct.pack(">2h", *w))
                b.write(BUS, struct.pack(">64i", *x))
                b.effect(syms["pots_process"], out, BUS, P + 428)
                if b.frames(out) != model(x, w):
                    bad.append(f"{rnd}, {name}, block {i}")
                n += 1
    check(not bad and not b.bad, f"{key}: POTS alone, {n} blocks ("
          + "; ".join(p_[0] for p_ in rounds[0][1]) + "; from start-up, then again after a reset, then on past its "
          "first dropout): its outputs its host build's, bit for bit" + (f"; {'; '.join(bad[:3])}" if bad else "")
          + (f"; {'; '.join(b.bad[:3])}" if b.bad else ""))


# --- 9. POTS against v6 ------------------------------------------------------------------------------------------------
def v6_tests():
    out, m = PH.against_v6()
    for ok, text in out:
        check(ok, f"POTS on the host against v6: {text}")
    print(f"  note  the loudest return, SNARE's level at Fdbk 127: {m['return_peak_dbfs']} dBFS on the bus")


# --- 10. Digital Delay and POTS in one slot ---------------------------------------------------------------------------
def switch_tests(stock):
    tweak, info, img, runtime = TC.built(stock, ["digidelay", "pots"])
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    b = Side(img, runtime, tweak)
    fx = Patterns(b.write, FIX)
    models = {1: Digital(), 2: PH.Pots()}
    rng = np.random.default_rng(70)
    out = SLOTS["delay"]["out"]
    at, size = info["fx_lines"]["fx.delay"]
    bad, n, filled = [], 0, True
    for mid in (1, 2, 1, 2):
        b.write(at, rng.integers(-(1 << 31), 1 << 31, size=size // 4, dtype=np.int64).astype(">i4").tobytes())
        filled &= sum(1 for v in struct.unpack(f">{size // 4}i", b.read(at, size)) if v) > size // 8
        fx.set(0, hdr(delay=mid))
        fx.link()
        models[mid].reset()                      # fxslot resets the effect that starts (fxslot.c, fx_run)
        for i in range(80):
            x = [int(v) for v in rng.integers(-(PH.K_BUS // 2), PH.K_BUS // 2, size=64)] if i < 40 else [0] * 64
            w = (0, 96 << 8)
            b.write(P + 428, struct.pack(">2h", *w))
            b.write(BUS, struct.pack(">64i", *x))
            b.effect(syms["fx_delay"], out, BUS, P + 428)
            if b.frames(out) != models[mid](x, w):
                bad.append(f"{'Digital' if mid == 1 else 'POTS'} ({n // 80 + 1}), block {i}")
            n += 1
    check(filled and not bad and not b.bad, f"digidelay+pots: the delay slot's line ({size} bytes at {at:#x}) filled "
          f"with noise before each switch, the pattern choosing Digital, POTS, Digital, POTS (80 blocks each, Time 0, "
          "Fdbk 96): each return its model's from its reset, bit for bit: neither reads what was on the line before it"
          + (f"; {'; '.join(bad[:3])}" if bad else "") + (f"; {'; '.join(b.bad[:3])}" if b.bad else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--blocks", type=int, default=60, help="blocks of 32 frames per selection, about")
    ap.add_argument("--dry", action="store_true", help="the builds and their sites only, without Unicorn")
    ap.add_argument("--pppccc", help="PPPCCC 2.0.0's patches/06-delay-fx.json: Digital Delay against their own code")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    Digital.tempo = PH.Pots.tempo = struct.unpack_from(">i", stock, TEMPO - compose.BASE)[0]
    digital_done = pots_done = False
    for ids in selections:
        key = "+".join(ids)
        mans = {i: compose.load_manifest(i) for i in ids}
        slots = {}
        for i, m in mans.items():
            if m["_effect"]:
                u = m["_effect"]
                slots.setdefault(u["point"][3:], {})[u["id"]] = Effect(i, u)
        if not slots:
            sys.exit(f"!! {key}: the proof needs an effect (refdelay, refreverb)")
        if any(e.id not in MODELS for s in slots.values() for e in s.values()):
            sys.exit(f"!! {key}: only {', '.join(MODELS)} have a model here")
        if any(len(s) > 1 for s in slots.values()):
            sys.exit(f"!! {key}: one effect per slot in this proof")
        tweak, info, img, runtime = TC.built(stock, ids)
        added = any(m["_machine"] for m in mans.values())
        desc_used = compose.gs.DESCN if added else g7.DESC
        print(f"\n{key}: " + "; ".join(f"the {n} slot: " + ", ".join(f"{e.id} ({i})" for i, e in s.items())
                                     for n, s in slots.items())
              + f"; payload {len(runtime)} bytes at {compose.gs.PAY_ALONE:#x}")
        if not args.dry:
            print("start-up")
            X.bootstrap_depack_ok(args.cycles, tweak, None) or t7.FAIL.append(f"{key}: bootstrap")
            X.boot_hook_ok(img, runtime) or t7.FAIL.append(f"{key}: boot hook")
        print("the sites and the data block")
        only_effects = all(m["_effect"] for m in mans.values())
        syms, blk = site_tests(key, stock, tweak, img, runtime, slots, only_effects, desc_used)
        line_tests(key, tweak, info, mans, runtime)
        if args.dry:
            continue
        print("the audio")
        audio_tests(key, stock, img, runtime, tweak, syms, blk, slots, args.blocks, desc_used)
        print("the gesture")
        gesture_tests(key, img, runtime, syms, blk, slots, desc_used)
        print("the pattern")
        storage_tests(key, stock, img, runtime)
        print("the cost")
        cost_tests(key, stock, img, runtime, tweak, syms, slots)
        if "digidelay" in ids and not digital_done:
            print("Digital Delay")
            digital_tests(key, stock, img, runtime, tweak, syms, args.pppccc)
            digital_done = True
        if "pots" in ids and not pots_done:
            print("POTS")
            pots_tests(key, img, runtime, tweak, syms)
            pots_done = True
    if COST["effects"]:
        out = HERE.parent.parent / "build" / "fx-cost.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(COST, indent=1, sort_keys=True) + "\n")
        print(f"\nthe counted costs: {out}")
    if not args.dry:
        print("\nPOTS against v6, on the host")
        v6_tests()
        print("\nDigital Delay and POTS in one slot")
        switch_tests(stock)
    print("\nthe composer's refusals, and a line shared")
    refusal_tests("refdelay")
    sharing_tests(stock)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
