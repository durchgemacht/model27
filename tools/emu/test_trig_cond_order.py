#!/usr/bin/env python3
"""Proof of the trig conditions in another order on the knob (notes/70,
tweaks/model-cycles_OS1.13/80-trig-cond-order.json).

The OS's own code, on the stock MAIN OS and on the modified one (with the tweaks of --with in both):
  1. Writes: the stock bytes; the freed mask identical to the kept one and referenced only by its constructor's
     constant, redirected; 0x400fd218 is entry +0x14 of TrigParameterSet's vtable and held 0x4000a980; the order in
     the image is the generator's ORDER; no other tweak writes other bytes there; the tweak leaves the knob path,
     the getter and setter of the condition byte, descriptor 19, the names and the sequencer as they were.
  2. The method alone, as the image's vtable has it, f(set, desc, value, delta), on a TrigParameterSet built by the
     OS's own constructor (0x4000b8f8): Trig Cond (19), every code 0..63 with deltas from -64 to +64 steps and
     fractions of a step: the stock OS gives (code << 8) + delta clamped to 0..0x3f00, so code + (delta >> 8) clamped
     once stored, the modified one ORDER[position + (delta >> 8)] clamped, << 8; d2-d7/a2-a6 and the stack come
     back. Trig Cond without a condition (-1) or out of range, and every other descriptor 0..79 with values and
     deltas at random: the stock answer.
  3. The knob step for a held trig, ParameterPageView's vtable +0x70 (0x4001e268, which the per-trig closure
     0x4001f15a calls when the trig has a condition), down to ParameterSet's step (0x4000a5f8) and the trig's
     condition byte through the OS's getter and setter (0x40015fd0, 0x40016010). The pattern track is a stand-in
     (its vtable +0x28 gives its data, +0x10 is told of a change), the view another (+0x80 gives the set): the byte
     data + 516 + step moves as in 2, no other byte of the data changes, the track is told once, as in the stock OS;
     a trig without a condition and step 64 as in the stock OS.
  4. Turning: from FILL, 63 clicks to the right then 63 to the left, with the names the OS shows (0x401090b4).
  5. The value window's five dots (ParameterPageView's vtable +0x90, 0x4001d818), its own code from the dots' start
     (0x4001d8ee) to the end of their loop (0x4001d98c), the two dot draws (0x40070efc lit, 0x40070c4e not)
     intercepted: Trig Cond, each code 0..63: the stock OS lights dot (code << 8) * 5 / 0x3f01, the modified one
     the same with the code's position in ORDER, so the lit dot never goes back while the knob goes forward; a trig
     without a condition, and other descriptors at random values: the stock dots and registers.
Not covered here: the encoder handler and the per-trig closure above 0x4001e268 (stock code, untouched, notes/70
§2), the rest of the value window (name and value text, stock code), the screen itself, and the device.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it
(SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_trig_cond_order.py --cycles model-cycles_OS1.13.syx \
        [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import random
import re
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_trig_cond_order as G     # noqa: E402
import sprites                      # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "80-trig-cond-order.json"
BASE = build.BASE
FAIL = []

STOP, STACK, FAKE = 0x9f000000, 0x9e000000, 0x92000000
TRACK, TRACK_VT, SET, VIEW, VIEW_VT = FAKE + 0x100, FAKE + 0x200, FAKE + 0x300, FAKE + 0x600, FAKE + 0x700
GET_DATA, NOTIFY, GET_SET, DATA = FAKE + 0x400, FAKE + 0x410, FAKE + 0x420, FAKE + 0x1000
TPS_CTOR, TPS_ENTRY, KNOB_STEP = 0x4000b8f8, 0x400fd218, 0x4001e268
DOTS_AT, DOTS_END, DOT_LIT, DOT_OFF, BITMAP = 0x4001d8ee, 0x4001d98c, 0x40070efc, 0x40070c4e, FAKE + 0x800
COND = 19
NAMES = 0x401090b4
WINDOW_REGS = [mk.UC_M68K_REG_D0 + i for i in range(8)] + [mk.UC_M68K_REG_A1 + i for i in range(5)]
# stock code the tweak must not touch: (start, end, what)
KEPT = ((0x4001e268, 0x4001e318, "ParameterPageView +0x70, knob step for a held trig"),
        (0x4001f15a, 0x4001f2b6, "the per-trig closure"),
        (0x4000a5f8, 0x4000a64a, "ParameterSet's knob step"),
        (0x4000a980, 0x4000aa9a, "the stock \"value + delta\" and its range check"),
        (0x4000aaee, 0x4000ace8, "TrigParameterSet's get and set"),
        (0x40015fd0, 0x40016086, "the condition byte's getter and setter"),
        (0x4010e108, 0x4010e140, "descriptor 19 (Trig Cond)"),
        (0x4001d818, 0x4001d91c, "the value window, before the dots' detour"),
        (0x4001d922, 0x4001d9bc, "the value window, after the dots' detour"),
        (0x4004a4ce, 0x4004a51a, "the Trig Cond formatter"),
        (0x40050040, 0x40050168, "the condition's short draw"),
        (0x40108f54, 0x401091b4, "the condition names"),
        (0x400913f0, 0x4009162a, "the sequencer's condition test"))
SAVED = [mk.UC_M68K_REG_D2 + i for i in range(6)] + [mk.UC_M68K_REG_A2 + i for i in range(5)]


def check(ok, msg):
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}", flush=True)
    if not ok:
        FAIL.append(msg)


def s32(v):
    v &= 0xffffffff
    return v - (1 << 32) if v & 0x80000000 else v


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def stock_value(code, delta):
    """What the stock method gives: (code << 8) + delta within the descriptor's 0..0x3f00."""
    return clamp((code << 8) + delta, 0, 0x3f00)


def mod_code(code, delta):
    return G.ORDER[clamp(G.ORDER.index(code) + (delta >> 8), 0, 63)]


class Rig:
    """The MAIN OS in memory, a pattern track stand-in, its TrigParameterSet (the OS's constructor) and a view."""

    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)
        uc.mem_map(0x90000000, 0x10000000)
        uc.mem_write(BASE, img)
        self.bad, self.told = [], 0
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        uc.hook_add(UC_HOOK_CODE, self._told, begin=NOTIFY, end=NOTIFY)
        self.lit = []
        for fn, on in ((DOT_LIT, True), (DOT_OFF, False)):
            uc.hook_add(UC_HOOK_CODE, lambda u, a, s, _, on=on: self._dot(on), begin=fn, end=fn)
        uc.mem_write(GET_DATA, struct.pack(">HIH", 0x203c, DATA, 0x4e75))      # move.l #DATA,d0 ; rts
        uc.mem_write(GET_SET, struct.pack(">HIH", 0x203c, SET, 0x4e75))        # move.l #SET,d0 ; rts
        uc.mem_write(NOTIFY, b"\x4e\x75")
        self.w32(TRACK, TRACK_VT)
        self.w32(TRACK_VT + 0x28, GET_DATA)
        self.w32(TRACK_VT + 0x10, NOTIFY)
        self.w32(VIEW, VIEW_VT)
        self.w32(VIEW_VT + 0x80, GET_SET)
        self.call(TPS_CTOR, SET, TRACK, 0)

    def _told(self, uc, addr, size, _):
        self.told += 1

    def _dot(self, on):
        """A dot draw (bitmap, x, 0x17, x + 4, 0x1b, 1): noted, then back to the caller."""
        sp = self.uc.reg_read(mk.UC_M68K_REG_A7)
        bmp, x = struct.unpack(">II", self.uc.mem_read(sp + 4, 8))
        self.lit.append((on, bmp, x))
        self.uc.reg_write(mk.UC_M68K_REG_PC, self.r32(sp))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def dots(self, desc, value):
        """The value window's dots, 0x4001d8ee -> 0x4001d98c, with d2 = descriptor, d3 = bitmap, d5 = value:
        (the lit dot's index or None, the five draws, the registers but a0, the stack back)."""
        sp = STACK - 0x100
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        for k, r in enumerate(WINDOW_REGS):
            self.uc.reg_write(r, 0x01010101 * (k + 1))
        self.uc.reg_write(mk.UC_M68K_REG_D2, desc)
        self.uc.reg_write(mk.UC_M68K_REG_D3, BITMAP)
        self.uc.reg_write(mk.UC_M68K_REG_D5, value & 0xffffffff)
        self.lit = []
        self.uc.emu_start(DOTS_AT, DOTS_END, count=10_000)
        on = [k for k, (o, _, _) in enumerate(self.lit) if o]
        ok = len(self.lit) == 5 and all(b == BITMAP and x == 76 + 9 * k for k, (_, b, x) in enumerate(self.lit))
        regs = {r: self.uc.reg_read(r) for r in WINDOW_REGS}
        return (on[0] if len(on) == 1 else None), ok, regs, self.uc.reg_read(mk.UC_M68K_REG_A7) == sp

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def call(self, fn, *args):
        """fn(args) with d2-d7/a2-a6 set to known values; (d0, registers and stack as they were)."""
        sp = STACK - 4 * (len(args) + 1)
        self.uc.mem_write(sp, struct.pack(">I", STOP) + b"".join(struct.pack(">I", a & 0xffffffff) for a in args))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        pre = {r: 0x01010101 * (k + 1) for k, r in enumerate(SAVED)}
        for r, v in pre.items():
            self.uc.reg_write(r, v)
        self.told = 0
        self.uc.emu_start(fn, STOP, count=100_000)
        kept = all(self.uc.reg_read(r) == v for r, v in pre.items()) and self.uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        return self.uc.reg_read(mk.UC_M68K_REG_D0), kept

    def method(self, desc, value, delta):
        """TrigParameterSet's +0x14 as the image's vtable has it."""
        return self.call(self.r32(self.r32(SET) + 0x14), SET, desc, value, delta)

    def knob(self, step, delta, desc=COND):
        return self.call(KNOB_STEP, VIEW, step, desc, delta)

    def data(self):
        return bytes(self.uc.mem_read(DATA, 1024))


def name(img, code):
    p = struct.unpack_from(">I", img, NAMES + 4 * code - BASE)[0] - BASE
    return img[p:img.index(b"\0", p)].decode()


def writes_ok(stock, base, img, tweak, others):
    for w in tweak["writes"]:
        o, old = w["off"], bytes.fromhex(w["old"])
        check(stock[o:o + len(old)] == old, f"stock bytes at {o + BASE:#x} ({len(old)} bytes)")
    size, ref, _, shared = sprites.MASKS[G.MASK]
    check(stock[G.MASK - BASE:G.MASK - BASE + size] == stock[shared - BASE:shared - BASE + size],
          f"mask {G.MASK:#x} identical to the kept mask {shared:#x}")
    refs = [m.start() + BASE for m in re.finditer(re.escape(struct.pack(">I", G.MASK)), stock)]
    check(refs == [ref] and img[ref - BASE:ref - BASE + 4] == struct.pack(">I", shared),
          f"only reference to mask {G.MASK:#x}: its constructor's constant ({ref:#x}), redirected")
    step, dots, order = (int(tweak["symbols"][n], 16) for n in ("tco_step", "tco_dots", "tco_order"))
    hva, hold = G.HOOK[:2]
    check(stock[hva - BASE:hva - BASE + 6].hex() == hold
          and img[hva - BASE:hva - BASE + 6] == struct.pack(">HI", 0x4eb9, dots),
          f"{hva:#x}: movea.l d5,a0 ; lsl.l #3,d4 ; lsl.l #6,d0 -> jsr tco_dots {dots:#x}")
    check(struct.unpack_from(">I", stock, TPS_ENTRY - BASE)[0] == 0x4000a980
          and struct.unpack_from(">I", stock, G.TPS_VTABLE - 4 - BASE)[0] == G.TPS_TYPEINFO
          and struct.unpack_from(">I", img, TPS_ENTRY - BASE)[0] == step,
          f"{TPS_ENTRY:#x}: TrigParameterSet's +0x14, 0x4000a980 -> tco_step {step:#x}")
    check(list(img[order - BASE:order - BASE + 64]) == G.ORDER and sorted(G.ORDER) == list(range(64)),
          f"the order at {order:#x}: each code 0..63 once, as the generator's ORDER")
    clash = []
    for t in others:
        for v in t["writes"]:
            a, b = v["off"], v["off"] + len(v["old"]) // 2
            for w in tweak["writes"]:
                c, d = w["off"], w["off"] + len(w["old"]) // 2
                if a < d and c < b and (v["off"], v["new"]) != (w["off"], w["new"]):
                    clash.append(f"{t['id']}@{a + BASE:#x}")
    check(not clash, f"no other tweak writes other bytes there ({len(others)} tweaks) {clash[:4]}")
    for lo, hi, what in KEPT:
        check(base[lo - BASE:hi - BASE] == img[lo - BASE:hi - BASE],
              f"not written by the tweak: {what} ({lo:#x}..{hi:#x})"
              + ("" if img[lo - BASE:hi - BASE] == stock[lo - BASE:hi - BASE] else ", changed by a --with tweak"))


DELTAS = sorted({d * s for d in (0x100, 0x200, 0x300, 0x500, 0x1000, 0x4000, 0x7fff, 0x80, 0x7f, 0x1, 0x180, 0x2c0)
                 for s in (1, -1)} | {0})


def method_tests(base, img):
    rs, rm = Rig(base), Rig(img)
    bad, kept = [], True
    for code in range(64):
        for delta in DELTAS:
            vs, ks = rs.method(COND, code << 8, delta)
            vm, km = rm.method(COND, code << 8, delta)
            kept &= ks and km
            if s32(vs) != stock_value(code, delta) or s32(vm) != mod_code(code, delta) << 8:
                bad.append((code, delta, s32(vs), s32(vm)))
    check(not bad, f"Trig Cond, codes 0..63 x {len(DELTAS)} deltas: stock (code << 8) + delta clamped, modified "
          f"ORDER[position + (delta >> 8)] << 8 {bad[:3]}")
    check(kept and not rs.bad and not rm.bad, "d2-d7/a2-a6 and the stack come back, no unmapped access")
    same = []
    for value in (-1, -0x100, 64 << 8, 0x7f00, 0x7fff, -0x8000):
        for delta in DELTAS:
            if rs.method(COND, value, delta)[0] != rm.method(COND, value, delta)[0]:
                same.append((value, delta))
    check(not same, f"Trig Cond without a condition (-1) or out of range: the stock answer {same[:3]}")
    rnd, n = random.Random(70), 0
    for desc in range(80):
        if desc == COND:
            continue
        for _ in range(40):
            value, delta = rnd.randrange(-0x200, 0x8000), rnd.randrange(-0x8000, 0x8000)
            n += 1
            if rs.method(desc, value, delta) != rm.method(desc, value, delta):
                same.append((desc, value, delta))
    check(not same and not rs.bad and not rm.bad, f"descriptors 0..79 but 19, {n} values and deltas at random: the "
          f"stock answer {same[:3]}")


def knob_tests(base, img):
    rnd = random.Random(516)
    out = {}
    for label, im in (("stock", base), ("modified", img)):
        r = Rig(im)
        res, kept = [], True
        for step in (0, 17, 63):
            for code in list(range(64)) + [0xff]:
                for delta in DELTAS:
                    before = bytearray(rnd.randrange(256) for _ in range(1024))
                    before[516 + step] = code
                    r.uc.mem_write(DATA, bytes(before))
                    _, k = r.knob(step, delta)
                    after = r.data()
                    kept &= k
                    others = after[:516 + step] + after[517 + step:] == before[:516 + step] + before[517 + step:]
                    res.append((step, code, delta, after[516 + step], others, r.told))
        for code, delta in ((0, 0x100), (40, -0x300)):
            before = bytes(rnd.randrange(256) for _ in range(1024))
            r.uc.mem_write(DATA, before)
            _, k = r.knob(64, delta)
            kept &= k
            res.append((64, code, delta, r.data() == before, True, r.told))
        out[label] = (res, kept, r.bad)
    rs, rm = out["stock"][0], out["modified"][0]
    conds_s = [x for x in rs if x[0] != 64 and x[1] != 0xff]
    conds_m = [x for x in rm if x[0] != 64 and x[1] != 0xff]
    bad_s = [x for x in conds_s if x[3] != stock_value(x[1], x[2]) >> 8]
    bad_m = [x for x in conds_m if x[3] != mod_code(x[1], x[2])]
    check(not bad_s, f"stock OS: the condition byte moves by delta >> 8, clamped ({len(conds_s)} turns) {bad_s[:3]}")
    check(not bad_m, f"modified: the condition byte moves through ORDER ({len(conds_m)} turns) {bad_m[:3]}")
    check(all(x[4] for x in rs + rm), "no other byte of the track's data changes")
    check(all(x[5] == 1 for x in rs + rm if x[0] != 64), "the track is told of the change once per turn, as in the "
          "stock OS")
    check([x for x in rs if x[1] == 0xff] == [x for x in rm if x[1] == 0xff],
          "a trig without a condition (byte -1): as in the stock OS")
    check([x for x in rs if x[0] == 64] == [x for x in rm if x[0] == 64] and all(x[3] and x[5] == 0 for x in rs
                                                                                 if x[0] == 64),
          "step 64: nothing written, nobody told, as in the stock OS")
    check(out["stock"][1] and out["modified"][1] and not out["stock"][2] and not out["modified"][2],
          "d2-d7/a2-a6 and the stack come back, no unmapped access")


def turning(base, img):
    seqs = {}
    for label, im in (("stock", base), ("modified", img)):
        r = Rig(im)
        r.uc.mem_write(DATA, bytes(1024))
        seq = [0]
        for delta in [0x100] * 63 + [-0x100] * 63:
            r.knob(0, delta)
            seq.append(r.data()[516])
        seqs[label] = seq
        print(f"     {label:8}: " + " ".join(name(im, c) for c in seq[:64]))
    check(seqs["stock"][:64] == list(range(64)) and seqs["stock"][63:] == list(range(63, -1, -1)),
          "stock OS: FILL ... !1st, 1% ... 99%, 1:2 ... 8:8, and back")
    check(seqs["modified"][:64] == G.ORDER and seqs["modified"][63:] == G.ORDER[::-1],
          "modified: FILL ... !1st, 1:2 ... 8:8, 1% ... 99%, and back")
    check([name(img, c) for c in G.ORDER[8:10] + G.ORDER[42:44] + G.ORDER[63:]] == ["1:2", "2:2", "8:8", "1%", "99%"],
          "the names at the seams: 1:2, 2:2 after !1st; 8:8 then 1%; 99% last")


def dot_tests(base, img):
    rs, rm = Rig(base), Rig(img)
    bad, flow, kept, prev = [], True, True, -1
    by_dot = {"stock": [[] for _ in range(5)], "modified": [[] for _ in range(5)]}
    for pos, code in enumerate(G.ORDER):
        ds, fs, gs, ks = rs.dots(COND, code << 8)
        dm, fm, gm, km = rm.dots(COND, code << 8)
        flow &= fs and fm
        kept &= ks and km and all(gs[r] == gm[r] for r in WINDOW_REGS if r != mk.UC_M68K_REG_D7)
        if ds != (code << 8) * 5 // 0x3f01 or dm != (pos << 8) * 5 // 0x3f01:
            bad.append((code, ds, dm))
        if dm is None or dm < prev:
            bad.append(("back", pos, code, dm))
        prev = dm if dm is not None else prev
        by_dot["modified"][dm or 0].append(name(img, code))
        by_dot["stock"][(code << 8) * 5 // 0x3f01].append(name(base, code))
    check(not bad, f"Trig Cond, codes 0..63: stock dot (code << 8) * 5 / 0x3f01, modified the same with the position "
          f"in ORDER, never back while the knob goes forward {bad[:3]}")
    check(flow, "five dot draws each time, at x 76 + 9 k, on the window's bitmap")
    check(kept, "the registers but a0 and the dot index (d7) as the stock code leaves them, the stack back")
    for label in ("stock", "modified"):
        print(f"     {label}:")
        for k, names in enumerate(by_dot[label]):
            print(f"       dot {k + 1}: {' '.join(names)}")
    same = []
    rnd = random.Random(19)
    cases = [(COND, -1), (COND, 64 << 8), (COND, 0x7f00)]
    for desc in list(range(2, 19)) + list(range(20, 76)):
        lo, hi = struct.unpack_from(">ii", img, 0x4010dce0 + 56 * desc + 8 - BASE)
        if hi > lo:
            cases += [(desc, lo), (desc, hi)] + [(desc, rnd.randint(lo, hi)) for _ in range(6)]
    for desc, value in cases:
        if rs.dots(desc, value) != rm.dots(desc, value):
            same.append((desc, value))
    check(not same and not rs.bad and not rm.bad, f"no condition, out of range, and {len(cases) - 3} values of other "
          f"descriptors: the stock dots and registers {same[:3]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="", help="other tweaks applied first (e.g. 6ch-usbup,model-tg)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx, for the Syntakt engines")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    files = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in TWEAK.parent.glob("[0-9]*.json")}
    every = [json.loads(f.read_text(encoding="utf-8")) for i, f in files.items() if i != "trig-cond-order"]
    tweaks = [json.loads(files[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    pl, _ = build.build_payload(tweaks, stock, args.syntakt)
    base = build.apply_writes(stock, sorted(tweaks, key=lambda t: t["order"]))[0] + pl
    img = build.apply_writes(stock, sorted(tweaks + [tweak], key=lambda t: t["order"]))[0] + pl
    print(f"firmware: {', '.join(t['id'] for t in sorted(tweaks + [tweak], key=lambda t: t['order']))}")
    print("1. writes")
    writes_ok(stock, base, img, tweak, every)
    print("2. TrigParameterSet's \"value + delta\" (vtable +0x14)")
    method_tests(base, img)
    print("3. knob step for a held trig (0x4001e268 -> 0x4000a5f8 -> the condition byte)")
    knob_tests(base, img)
    print("4. turning from FILL, the names the OS shows")
    turning(base, img)
    print("5. the value window's five dots (0x4001d8ee -> 0x4001d98c)")
    dot_tests(base, img)
    print("\nALL OK" if not FAIL else f"\n{len(FAIL)} FAILURE(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
