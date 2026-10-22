#!/usr/bin/env python3
"""Proof of the dispatchers and of REF2's views and UI hooks (notes/63 §4, steps B4c and B4d) on the OS's own code:
the main screen's and the knob view's draw methods, the screen's tick and the browser's file opening, which REF2
takes as SAMPLE does, directly when it is the only machine that takes them and through the builder's dispatchers
(tools/machines/dispatch/) when SAMPLE is in the build too.

For each selection (by default: refmachine2; sampler,refmachine2; refmachine2,sampler; sampler,refmachine,refmachine2),
on the official OS 1.13:
  1. the sites: REF2 alone writes its two draws into MainScreenView's vtable entry (0x400ffe30) and the knob view's
     (0x4010053c), and its tick and browser hook at 0x400075f0 and 0x400a6602, with no dispatcher; with SAMPLE, all
     four go to the dispatchers, whose tables hold SAMPLE's and REF2's methods at their machines and nothing at the
     others;
  2. the dispatchers (builds with SAMPLE):
     - the draws: for the selected track on every machine (stock, SAMPLE, REF, REF2, one past the last, 100), on a
       track past 5 and without a project, each entry calls once, with the same arguments, the draw of that track's
       machine or the stock draw, and the stack comes back;
     - the tick: every machine's tick, in machine order, then the stock getter 0x40076be4 once, whose answer it gives;
     - the browser: for the track the browser loads into on every machine, past 5 and without a project, the hook of
       that track's machine or the stock open (0x400a3052), with a0 (&result), a2 (the browser), d4 (the entry's
       index) and the stack as at the call;
  3. REF2's main draw, as its entry or the dispatcher calls it: the stock draw once (a stub: the screen is filled
     beforehand as a stock picture, dark in the free band), then OCT and the Octave drawn by the OS's own text code in
     its small font, only in the right half's free band, x 64..127, rows 44..56, five different labels for -2..+2;
     nothing more while a value window is open or on another machine's track;
  4. REF2's knob draw, likewise: while the Octave (descriptor 1) is shown on a REF2 track and no trig is held, the
     screen blanked, OCTAVE above, and five boxes 16 x 16 at x 8 + 24 i, rows 20..35, the current one filled and the
     others outlined, the values below, without the stock knob view; for another parameter, with a trig held, without
     a value window or on another machine's track: the stock knob view once, with the same arguments, and the screen
     untouched;
  5. REF2's tick: the getter's answer at every tick; a redraw of the main screen (View::setNeedsRedraw, 0x40076082) every
     16 ticks on a REF2 track, none on another track or with a value window open; the label's dot (x 120..121, rows
     49..50) lit after 16 ticks and dark again after 32;
  6. REF2's browser hook: on a REF2 track, the entry's name asked of the browser's list (its method +16, with the
     entry's index), the string destroyed, then the stock open with a0, a2, d4 and the stack as at the call; the label
     shows the name's first 10 characters for 6 redraws of that track, then OCT again; another track keeps OCT; on
     another machine's track, the stock open alone.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_views.py --cycles model-cycles_OS1.13.syx [--machines sampler,refmachine2] [--show]
"""
import argparse
import pathlib
import random
import struct
import sys

from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_syntakt_machines as TS  # noqa: E402
from test_sdvintage_7th import check  # noqa: E402
from test_shortcuts import UI       # noqa: E402  (with a heap for operator new and the stack's check)

SELECTIONS = [["refmachine2"], ["sampler", "refmachine2"], ["refmachine2", "sampler"],
              ["sampler", "refmachine", "refmachine2"]]
MAIN_ENTRY, KNOB_ENTRY, TICK_SITE, OPEN_SITE = 0x400ffe30, 0x4010053c, 0x400075f0, 0x400a6602
MAIN_DRAW, KNOB_DRAW, TICK_STOCK, OPEN_STOCK = 0x4001b22a, 0x4001e40a, 0x40076be4, 0x400a3052
NEEDS_REDRAW, STRING_DROP = 0x40076082, 0x400f7d5c
PROJECT, GROUP, SELECTED = 0x400cf866, 0x4000eb90, 0x40012412
UI_STATE, VALUE_SHOWN, TRIG_HELD = 0x400cf9a8, 0x4006b704, 0x4006b736
NEW, DELETE, BMP_CTOR = 0x400802e0, 0x400802ec, 0x40070172
PROJ, TRACK_VT, SOUND_FN, SOUND = 0x93a00000, 0x93a10000, 0x93a20000, 0x93a30000
VIEW, BMP, FB, SCREEN = 0x93a40000, 0x93a50000, 0x93a60000, 0x93a90000
RESULT, HANDLE, BROWSER_PP, BROWSER = 0x93aa0000, 0x93ab0000, 0x93ac0000, 0x93ac0100
LIST, LIST_VT, NAME_FN, NAME = 0x93ac0400, 0x93ac0500, 0x93ac0600, 0x93ac0700
INDEX, FILE, GETTER = 0x1234, b"KICK-HARD-01X", 0x5a
W, H, PITCH = 128, 64, 2
BAND = (64, 127, 44, 56)                 # the right half's free band: x0, x1, y0, y1
DOT = ((120, 49), (121, 49), (120, 50), (121, 50))
BOX_LEFT, BOX_STEP, BOX_W, BOX_Y = 8, 24, 16, (20, 35)
POINTS = {"main": (MAIN_ENTRY, 4, "smp_main_draw", "ref2_main_draw", "dp_main"),
          "knob": (KNOB_ENTRY, 28, "smp_knob_draw", "ref2_knob_draw", "dp_knob"),
          "tick": (TICK_SITE, 52, "smp_hook_tick", "ref2_hook_tick", "dp_tick"),
          "open": (OPEN_SITE, 76, "smp_hook_open", "ref2_hook_open", "dp_open")}
REGS_IN = {mk.UC_M68K_REG_A0: RESULT, mk.UC_M68K_REG_A2: BROWSER_PP, mk.UC_M68K_REG_D4: INDEX}


class VUI(UI):
    """test_shortcuts.py's UI, plus: the stubs named in REGS also note a0, a2, d4 and the stack at their call, and the
    "name" stub writes a std::string (a pointer to NAME) where a0 points, as the browser's list method does."""
    REGS = ("open", "smp_hook_open", "ref2_hook_open", "name")

    def __init__(self, img, payload=b""):
        super().__init__(img, payload)
        self.regs = []

    def _hook(self, uc, addr, size, ud):
        h = self.hooks.get(addr)
        if isinstance(h, tuple) and h[0] in self.REGS:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            a0 = uc.reg_read(mk.UC_M68K_REG_A0)
            self.regs.append((h[0], a0, uc.reg_read(mk.UC_M68K_REG_A2), uc.reg_read(mk.UC_M68K_REG_D4),
                              struct.unpack(">3I", uc.mem_read(sp, 12))))
            if h[0] == "name":
                uc.mem_write(a0, struct.pack(">I", NAME))
        super()._hook(uc, addr, size, ud)

    def call_regs(self, fn, regs, *args):
        """call() with registers set (a0, a2, d4 of the browser's call)."""
        sp = t7.STACK - 0x400
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), t7.STOP, *[a & 0xffffffff for a in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        for r, v in regs.items():
            self.uc.reg_write(r, v)
        self.bad.clear()
        self.uc.emu_start(fn, t7.STOP, count=20_000_000)
        self.sp_ok = self.uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        return self.uc.reg_read(mk.UC_M68K_REG_D0)


def world(u, machine, track=0, project=True, value=False, trig=False, k28=0x100):
    """The selected track playing machine: the project singleton, the track's object, whose method +40 gives its sound,
    the sound's machine (+38) and Octave (k 28, +76); the stock methods and the UI's state are stubs."""
    u.hooks = {PROJECT: ("project", PROJ if project else 0), GROUP: ("group", 0x93a70000), SELECTED: ("track", track),
               UI_STATE: ("ui", 0x93a80000), VALUE_SHOWN: ("value", int(value)), TRIG_HELD: ("trig", int(trig)),
               MAIN_DRAW: ("main", 0), KNOB_DRAW: ("knob", 0), SOUND_FN: ("sound", SOUND), NEW: ("new", 0),
               DELETE: ("delete", 0), TICK_STOCK: ("getter", GETTER), NEEDS_REDRAW: ("redraw", 0)}
    for t in range(6):
        u.uc.mem_write(PROJ + 212 + t * 68, struct.pack(">I", TRACK_VT))
    u.uc.mem_write(TRACK_VT + 40, struct.pack(">I", SOUND_FN))
    snd = bytearray(100)
    snd[38] = machine & 0xff
    struct.pack_into(">h", snd, 76, k28)
    u.uc.mem_write(SOUND, bytes(snd))


def browser(u, track):
    """The browser that opens a file into track: its object (+664 the track, +640 its list), the list's method +16 (a
    stub that names the entry FILE), the string's destructor and the stock open (stubs)."""
    u.uc.mem_write(BROWSER_PP, struct.pack(">I", BROWSER))
    u.uc.mem_write(BROWSER + 664, struct.pack(">i", track))
    u.uc.mem_write(BROWSER + 640, struct.pack(">I", LIST))
    u.uc.mem_write(LIST, struct.pack(">I", LIST_VT))
    u.uc.mem_write(LIST_VT + 16, struct.pack(">I", NAME_FN))
    u.uc.mem_write(NAME, FILE + b"\0")
    u.hooks.update({NAME_FN: ("name", 0), STRING_DROP: ("drop", 0), OPEN_STOCK: ("open", 0)})
    u.regs.clear()


def bitmap(u):
    u.hooks = {}
    u.call(BMP_CTOR, BMP, W, H, FB, 0)                   # the OS's own Bitmap: 128 x 64, its words at FB


def screen(u):
    return bytes(u.uc.mem_read(FB, W * PITCH * 4))


def lit(fb, x, y):
    w = struct.unpack_from(">I", fb, 4 * (x * PITCH + (y >> 5)))[0]
    return w >> (31 - (y & 31)) & 1


def picture(rng, band_dark=True):
    """A stock picture: random pixels, dark in the free band."""
    fb = bytearray(rng.getrandbits(8) for _ in range(W * PITCH * 4))
    if band_dark:
        x0, x1, y0, y1 = BAND
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                i = 4 * (x * PITCH + (y >> 5))
                w = struct.unpack_from(">I", fb, i)[0] & ~(1 << (31 - (y & 31)))
                struct.pack_into(">I", fb, i, w)
    return bytes(fb)


def ascii_screen(fb, x0=0, x1=W, y0=0, y1=H):
    return "\n".join(f"y={y:2d}  " + "".join("#" if lit(fb, x, y) else "." for x in range(x0, x1))
                     for y in range(y1 - 1, y0 - 1, -1))


def diff_in_band(a, b):
    """The pixels that differ between two screens, and whether they all lie in the free band."""
    d = [(x, y) for x in range(W) for y in range(H) if lit(a, x, y) != lit(b, x, y)]
    x0, x1, y0, y1 = BAND
    return d, all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in d)


def draws(u, names):
    return [(n, a[:2]) for n, a in u.calls if n in names]


# --- 1. the sites -------------------------------------------------------------------------------------------------
def site_tests(key, img, runtime, syms, added):
    u = VUI(img, runtime)
    smp = next((m["index"] for m in added if m["code"] == "sampler"), None)

    def at(site, sym):                                   # a vtable entry holds the address, a hook is a jsr to it
        if site in (MAIN_ENTRY, KNOB_ENTRY):
            return u.u32(site) == syms[sym]
        return bytes(u.uc.mem_read(site, 6)) == b"\x4e\xb9" + struct.pack(">I", syms[sym])
    if smp is None:
        check(all(at(p[0], p[3]) for p in POINTS.values()) and "dp_main" not in syms,
              f"{key}: REF2 alone: 0x400ffe30 -> ref2_main_draw, 0x4010053c -> ref2_knob_draw, 0x400075f0 jsr "
              "ref2_hook_tick, 0x400a6602 jsr ref2_hook_open, no dispatcher")
        return
    data = syms["dp_data"]
    first, count = bytes(u.uc.mem_read(data, 2))
    ok = (first, count) == (6, len(added))
    for _name, (site, table, smp_sym, ref2_sym, dp_sym) in POINTS.items():
        got = struct.unpack(">6I", u.uc.mem_read(data + table, 24))
        want = tuple(syms[{"sampler": smp_sym, "refmachine2": ref2_sym}[m["code"]]]
                     if m["code"] in ("sampler", "refmachine2") else 0 for m in added) + (0,) * (6 - len(added))
        ok &= at(site, dp_sym) and got == want
    check(ok, f"{key}: 0x400ffe30, 0x4010053c, 0x400075f0 and 0x400a6602 -> dp_main, dp_knob, dp_tick, dp_open; their "
              f"tables, machines 6..{5 + len(added)}: "
              + ", ".join(m["name"] + " " + ("its methods" if m["code"] in ("sampler", "refmachine2") else "none")
                          for m in added))


# --- 2. the dispatchers -------------------------------------------------------------------------------------------
def dispatch_tests(key, img, runtime, syms, added):
    names = {syms[p[i]]: p[i] for p in POINTS.values() for i in (2, 3)}
    by_code = {m["code"]: m["index"] for m in added}
    u = VUI(img, runtime)
    cases = [(m, 0, True) for m in list(range(6)) + [m["index"] for m in added] + [TS.NM, 100]]
    cases += [(by_code["refmachine2"], 6, True), (by_code["refmachine2"], 0, False)]
    ok, seen = True, []
    for kind, stock in (("main", "main"), ("knob", "knob")):
        entry = POINTS[kind][0]
        for machine, track, project in cases:
            world(u, machine, track, project)
            for a, n in names.items():
                u.hooks[a] = (n, 0)
            u.calls.clear()
            u.call(u.u32(entry), VIEW, BMP)
            got = draws(u, set(names.values()) | {stock})
            code = next((m["code"] for m in added if m["index"] == machine), None) if track < 6 and project else None
            want = {"sampler": f"smp_{kind}_draw", "refmachine2": f"ref2_{kind}_draw"}.get(code, stock)
            good = got == [(want, (VIEW, BMP))] and u.sp_ok and not u.bad
            ok &= good
            if not good:
                seen.append(f"{kind} machine {machine} track {track} project {project}: {got}")
    check(ok, f"{key}: the draws' dispatchers call the selected track's machine's draw (SAMPLE's, REF2's) or the stock "
              f"draw, once with the same arguments, for machines 0..5, {', '.join(str(m['index']) for m in added)}, "
              f"{TS.NM}, 100, track 6 and no project ({2 * len(cases)} cases)" + (f"; DIFFERENT {seen[:3]}" if seen else ""))
    # the tick: every machine's, in machine order, then the getter once
    world(u, by_code["refmachine2"])
    for a, n in names.items():
        u.hooks[a] = (n, 0)
    u.calls.clear()
    r = u.call(syms["dp_tick"], SCREEN)
    got = [(n, a[0]) for n, a in u.calls if n in set(names.values()) | {"getter"}]
    want = [({"sampler": "smp_hook_tick", "refmachine2": "ref2_hook_tick"}[m["code"]], SCREEN) for m in added
            if m["code"] in ("sampler", "refmachine2")] + [("getter", SCREEN)]
    check(got == want and r == GETTER and u.sp_ok and not u.bad,
          f"{key}: the tick's dispatcher: {', '.join(n for n, _ in want)}, in machine order, then gives the getter's "
          f"answer")
    # the browser: the method of the machine of the track it loads into, with the call's registers and stack
    ok, seen = True, []
    for machine, track, project in cases:
        world(u, machine, 0, project)
        browser(u, track)
        for a, n in names.items():
            u.hooks[a] = (n, 0)
        u.calls.clear()
        u.call_regs(syms["dp_open"], REGS_IN, HANDLE)
        code = next((m["code"] for m in added if m["index"] == machine), None) if track < 6 and project else None
        want = {"sampler": "smp_hook_open", "refmachine2": "ref2_hook_open"}.get(code, "open")
        got = [(r_[0], r_[1], r_[2], r_[3], r_[4][:2]) for r_ in u.regs]
        good = got == [(want, RESULT, BROWSER_PP, INDEX, (t7.STOP, HANDLE))] and u.sp_ok and not u.bad
        ok &= good
        if not good:
            seen.append(f"machine {machine} track {track} project {project}: {got}")
    check(ok, f"{key}: the browser's dispatcher goes to the hook of the machine of the track it loads into (SAMPLE's, "
              f"REF2's) or to the stock open, with a0, a2, d4 and the stack as at the call ({len(cases)} cases)"
              + (f"; DIFFERENT {seen[:3]}" if seen else ""))


# --- 3. REF2's main screen ------------------------------------------------------------------------------------------
def main_tests(key, img, runtime, syms, ref2, other, show):
    u = VUI(img, runtime)
    bitmap(u)
    rng = random.Random(63)
    stock = picture(rng)
    fn = syms["ref2_main_draw"]
    labels, ok = {}, True
    for oct_ in range(-2, 3):
        world(u, ref2, k28=oct_ << 8)
        u.uc.mem_write(FB, stock)
        u.calls.clear()
        u.call(fn, VIEW, BMP)
        fb = screen(u)
        diff, inside = diff_in_band(fb, stock)
        ok &= draws(u, {"main"}) == [("main", (VIEW, BMP))] and inside and len(diff) > 10 and u.sp_ok and not u.bad
        labels[oct_] = frozenset(diff)
        if show and oct_ == 1:
            print("        the right half after REF2's main draw at Octave +1 (rows 40..60):")
            print("\n".join("        " + l for l in ascii_screen(fb, 64, 128, 40, 61).splitlines()))
    span = [p for v in labels.values() for p in v] or [(0, 0)]
    check(ok and len(set(labels.values())) == 5,
          f"{key}: REF2's main screen: the stock draw once, then OCT and the Octave by the OS's text code only in the "
          f"free band of the right half (x {min(x for x, _ in span)}..{max(x for x, _ in span)}, rows "
          f"{min(y for _, y in span)}..{max(y for _, y in span)}), five different labels for -2..+2 "
          f"({min(len(v) for v in labels.values())} to {max(len(v) for v in labels.values())} pixels)")
    quiet = True
    for machine, value in ((ref2, True), (other, False), (0, False)):
        world(u, machine, value=value)
        u.uc.mem_write(FB, stock)
        u.calls.clear()
        u.call(fn, VIEW, BMP)
        quiet &= draws(u, {"main"}) == [("main", (VIEW, BMP))] and screen(u) == stock and not u.bad
    check(quiet, f"{key}: no label while a value window is open, or on machine {other}'s or KICK's track: the stock draw "
                 "alone")


# --- 4. REF2's knob view --------------------------------------------------------------------------------------------
def knob_tests(key, img, runtime, syms, ref2, other, show):
    u = VUI(img, runtime)
    bitmap(u)
    rng = random.Random(64)
    fn = syms["ref2_knob_draw"]
    ok, pics = True, {}
    for oct_ in range(-2, 3):
        world(u, ref2, value=True, k28=oct_ << 8)
        u.uc.mem_write(VIEW + 0x230, struct.pack(">i", 1))
        u.uc.mem_write(FB, picture(rng, band_dark=False))
        u.calls.clear()
        u.call(fn, VIEW, BMP)
        fb = screen(u)
        for v in range(-2, 3):
            bx = BOX_LEFT + (v + 2) * BOX_STEP
            for x in range(bx, bx + BOX_W):
                for y in range(BOX_Y[0], BOX_Y[1] + 1):
                    edge = x in (bx, bx + BOX_W - 1) or y in BOX_Y
                    ok &= lit(fb, x, y) == (1 if v == oct_ or edge else 0)
        boxes = {(BOX_LEFT + i * BOX_STEP + dx, y) for i in range(5) for dx in range(BOX_W)
                 for y in range(BOX_Y[0], BOX_Y[1] + 1)}
        stray = [(x, y) for x in range(W) for y in range(H) if lit(fb, x, y) and (x, y) not in boxes
                 and not 44 <= y <= 63 and not 0 <= y <= 18]          # the title's rows, the values' rows
        ok &= not stray and not draws(u, {"knob"}) and u.sp_ok and not u.bad
        pics[oct_] = fb
    check(ok, f"{key}: REF2's knob view at Octave -2..+2: the screen blanked, five boxes, the current one filled and the "
              "others outlined, text only above (rows 44..63) and below (rows 0..18), no stock knob view")
    if show:
        print("        REF2's knob view at Octave +1:")
        print("\n".join("        " + l for l in ascii_screen(pics[1]).splitlines()))
    quiet = True
    for machine, value, trig, param in ((ref2, True, False, 76), (ref2, True, True, 1), (ref2, False, False, 1),
                                        (other, True, False, 1)):
        world(u, machine, value=value, trig=trig)
        u.uc.mem_write(VIEW + 0x230, struct.pack(">i", param))
        stock = picture(rng, band_dark=False)
        u.uc.mem_write(FB, stock)
        u.calls.clear()
        u.call(fn, VIEW, BMP)
        quiet &= draws(u, {"knob"}) == [("knob", (VIEW, BMP))] and screen(u) == stock and not u.bad
    check(quiet, f"{key}: the stock knob view, once and alone, for another parameter, with a trig held, without a value "
                 f"window, and on machine {other}'s track")


# --- 5. REF2's tick and the label's dot -----------------------------------------------------------------------------
def tick_tests(key, img, runtime, syms, ref2, other, show):
    u = VUI(img, runtime)
    bitmap(u)
    stock = picture(random.Random(66))
    draw, tick = syms["ref2_main_draw"], syms["ref2_hook_tick"]

    def label():
        world(u, ref2)
        u.uc.mem_write(FB, stock)
        u.call(draw, VIEW, BMP)                          # also notes the main screen's view
        return screen(u)
    before = label()
    redraws, answers, getters, pics, ok_ = [], set(), 0, {}, True
    for n in range(1, 65):                               # 1..32 on REF2, 33..48 on another machine, 49..64 a value shown
        world(u, ref2 if n <= 32 or n > 48 else other, value=n > 48)
        u.calls.clear()
        answers.add(u.call(tick, SCREEN))
        redraws += [(n, a[0]) for c, a in u.calls if c == "redraw"]
        getters += sum(1 for c, a in u.calls if c == "getter" and a[0] == SCREEN)
        ok_ &= u.sp_ok and not u.bad
        if n in (16, 32):
            pics[n] = label()
    dots = {n: [lit(p, x, y) for x, y in DOT] for n, p in pics.items()}
    d16, inside = diff_in_band(pics[16], before)
    check(ok_ and redraws == [(16, VIEW), (32, VIEW)] and answers == {GETTER} and getters == 64
          and [lit(before, x, y) for x, y in DOT] == [0] * 4 and dots == {16: [1] * 4, 32: [0] * 4}
          and set(d16) == set(DOT) and inside and pics[32] == before,
          f"{key}: REF2's tick: the getter's answer at each of 64 ticks; a redraw of the main screen at ticks 16 and 32 "
          f"on a REF2 track, none on machine {other}'s track or with a value window open; the dot (x 120..121, rows "
          f"49..50) lit after 16 ticks, dark again after 32, nothing else changed")
    if show:
        print("        the right half after 16 ticks, the dot lit (rows 44..56):")
        print("\n".join("        " + l for l in ascii_screen(pics[16], 64, 128, 44, 57).splitlines()))


# --- 6. REF2's browser hook and the file's name ---------------------------------------------------------------------
def open_tests(key, img, runtime, syms, ref2, other, show):
    u = VUI(img, runtime)
    bitmap(u)
    stock = picture(random.Random(67))
    draw, hook = syms["ref2_main_draw"], syms["ref2_hook_open"]

    def label(track=0):
        world(u, ref2, track)
        u.uc.mem_write(FB, stock)
        u.call(draw, VIEW, BMP)
        return screen(u)
    octave = label()
    world(u, ref2)
    browser(u, 0)
    u.calls.clear()
    u.call_regs(hook, REGS_IN, HANDLE)
    asked = [(n, a[:2]) for n, a in u.calls if n == "name"]
    slot = [r[1] for r in u.regs if r[0] == "name"]
    dropped = [a[0] for n, a in u.calls if n == "drop"]
    opened = [(r[0], r[1], r[2], r[3], r[4][:2]) for r in u.regs if r[0] == "open"]
    ok = (asked == [("name", (LIST, INDEX))] and len(slot) == 1 and dropped == slot
          and opened == [("open", RESULT, BROWSER_PP, INDEX, (t7.STOP, HANDLE))] and u.sp_ok and not u.bad)
    elsewhere = label(1)                                 # another track keeps OCT
    named = [label() for _ in range(7)]
    d, inside = diff_in_band(named[0], stock)
    check(ok and elsewhere == octave and all(p == named[0] for p in named[:6]) and named[0] != octave and inside
          and len(d) > 10 and named[6] == octave,
          f"{key}: REF2's browser hook on a REF2 track: the entry's name asked of the browser's list (method +16, index "
          f"{INDEX:#x}), the string destroyed, the stock open with a0, a2, d4 and the stack as at the call; the label "
          f"shows the name for 6 redraws of track 1, then OCT again; track 2 keeps OCT")
    if show:
        print(f"        the right half after opening {FILE.decode()} (rows 44..56):")
        print("\n".join("        " + l for l in ascii_screen(named[0], 64, 128, 44, 57).splitlines()))
    world(u, other)
    browser(u, 0)
    u.calls.clear()
    u.call_regs(hook, REGS_IN, HANDLE)
    opened = [(r[0], r[1], r[2], r[3], r[4][:2]) for r in u.regs]
    check(opened == [("open", RESULT, BROWSER_PP, INDEX, (t7.STOP, HANDLE))]
          and not [n for n, _a in u.calls if n in ("name", "drop")] and u.sp_ok and not u.bad,
          f"{key}: on machine {other}'s track, REF2's browser hook goes straight to the stock open, the registers and "
          "the stack as at the call, no name asked")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--show", action="store_true", help="REF2's label, knob view, dot and file name in ASCII")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    for ids in selections:
        if "refmachine2" not in ids:
            sys.exit(f"!! {'+'.join(ids)}: the proof needs REF2, the machine with views")
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        added = TC.configure(ids)
        syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
        ref2 = next(m["index"] for m in added if m["code"] == "refmachine2")
        other = next((m["index"] for m in added if m["code"] != "refmachine2"), 5)
        d = info["dispatch"]
        print(f"\n{key}: " + ", ".join(f"{m['name']} = machine {m['index']}" for m in added)
              + (f"; dispatchers at {d['code_at']:#x}, data at {d['data_at']:#x}" if d else "; no dispatcher"))
        print("the sites")
        site_tests(key, img, runtime, syms, added)
        if d:
            print("the dispatchers")
            dispatch_tests(key, img, runtime, syms, added)
        print("REF2's main screen")
        main_tests(key, img, runtime, syms, ref2, other, args.show)
        print("REF2's knob view")
        knob_tests(key, img, runtime, syms, ref2, other, args.show)
        print("REF2's tick")
        tick_tests(key, img, runtime, syms, ref2, other, args.show)
        print("REF2's browser hook")
        open_tests(key, img, runtime, syms, ref2, other, args.show)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
