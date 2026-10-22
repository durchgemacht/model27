#!/usr/bin/env python3
"""Proof of the dispatchers and of REF2's views (notes/63 §4, step B4c) on the OS's own code: the main screen's and
the knob view's draw methods, which REF2 takes as SAMPLE does, directly when it is the only machine that takes them
and through the builder's dispatchers (tools/machines/dispatch/) when SAMPLE is in the build too.

For each selection (by default: refmachine2; sampler,refmachine2; refmachine2,sampler; sampler,refmachine,refmachine2),
on the official OS 1.13:
  1. the sites: REF2 alone writes its two draws into MainScreenView's vtable entry (0x400ffe30) and the knob view's
     (0x4010053c), with no dispatcher; with SAMPLE, both entries go to the dispatchers, whose tables hold SAMPLE's and
     REF2's draws at their machines and nothing at the others;
  2. the dispatchers (builds with SAMPLE): for the selected track on every machine (stock, SAMPLE, REF, REF2, one past
     the last, 100), on a track past 5 and without a project, each entry calls once, with the same arguments, the draw
     of that track's machine or the stock draw, and the stack comes back;
  3. REF2's main draw, as its entry or the dispatcher calls it: the stock draw once (a stub: the screen is filled
     beforehand as a stock picture, dark in the free band), then OCT and the Octave drawn by the OS's own text code in
     its small font, only in the right half's free band, x 64..127, rows 44..56, five different labels for -2..+2;
     nothing more while a value window is open or on another machine's track;
  4. REF2's knob draw, likewise: while the Octave (descriptor 1) is shown on a REF2 track and no trig is held, the
     screen blanked, OCTAVE above, and five boxes 16 x 16 at x 8 + 24 i, rows 20..35, the current one filled and the
     others outlined, the values below, without the stock knob view; for another parameter, with a trig held, without
     a value window or on another machine's track: the stock knob view once, with the same arguments, and the screen
     untouched.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it (it
stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_views.py --cycles model-cycles_OS1.13.syx [--machines sampler,refmachine2] [--show]
"""
import argparse
import pathlib
import random
import struct
import sys

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
MAIN_ENTRY, KNOB_ENTRY = 0x400ffe30, 0x4010053c
MAIN_DRAW, KNOB_DRAW = 0x4001b22a, 0x4001e40a
PROJECT, GROUP, SELECTED = 0x400cf866, 0x4000eb90, 0x40012412
UI_STATE, VALUE_SHOWN, TRIG_HELD = 0x400cf9a8, 0x4006b704, 0x4006b736
NEW, DELETE, BMP_CTOR = 0x400802e0, 0x400802ec, 0x40070172
PROJ, TRACK_VT, SOUND_FN, SOUND = 0x93a00000, 0x93a10000, 0x93a20000, 0x93a30000
VIEW, BMP, FB = 0x93a40000, 0x93a50000, 0x93a60000
W, H, PITCH = 128, 64, 2
BAND = (64, 127, 44, 56)                 # the right half's free band: x0, x1, y0, y1
BOX_LEFT, BOX_STEP, BOX_W, BOX_Y = 8, 24, 16, (20, 35)


def world(u, machine, track=0, project=True, value=False, trig=False, k28=0x100):
    """The selected track playing machine: the project singleton, the track's object, whose method +40 gives its sound,
    the sound's machine (+38) and Octave (k 28, +76); the stock draws and the UI's state are stubs."""
    u.hooks = {PROJECT: ("project", PROJ if project else 0), GROUP: ("group", 0x93a70000), SELECTED: ("track", track),
               UI_STATE: ("ui", 0x93a80000), VALUE_SHOWN: ("value", int(value)), TRIG_HELD: ("trig", int(trig)),
               MAIN_DRAW: ("main", 0), KNOB_DRAW: ("knob", 0), SOUND_FN: ("sound", SOUND), NEW: ("new", 0),
               DELETE: ("delete", 0)}
    for t in range(6):
        u.uc.mem_write(PROJ + 212 + t * 68, struct.pack(">I", TRACK_VT))
    u.uc.mem_write(TRACK_VT + 40, struct.pack(">I", SOUND_FN))
    snd = bytearray(100)
    snd[38] = machine & 0xff
    struct.pack_into(">h", snd, 76, k28)
    u.uc.mem_write(SOUND, bytes(snd))


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


def draws(u, names):
    return [(n, a[:2]) for n, a in u.calls if n in names]


# --- 1. the sites -------------------------------------------------------------------------------------------------
def site_tests(key, img, runtime, syms, added):
    u = UI(img, runtime)
    main, knob = u.u32(MAIN_ENTRY), u.u32(KNOB_ENTRY)
    smp = next((m["index"] for m in added if m["code"] == "sampler"), None)
    if smp is None:
        check(main == syms["ref2_main_draw"] and knob == syms["ref2_knob_draw"] and "dp_main" not in syms,
              f"{key}: REF2 alone: 0x400ffe30 -> ref2_main_draw, 0x4010053c -> ref2_knob_draw, no dispatcher")
        return
    data = syms["dp_data"]
    first, count = bytes(u.uc.mem_read(data, 2))
    tables = {"main": struct.unpack(">6I", u.uc.mem_read(data + 4, 24)),
              "knob": struct.unpack(">6I", u.uc.mem_read(data + 28, 24))}
    want = {kind: tuple(syms[{"sampler": "smp", "refmachine2": "ref2"}[m["code"]] + f"_{kind}_draw"]
                        if m["code"] in ("sampler", "refmachine2") else 0 for m in added) + (0,) * (6 - len(added))
            for kind in ("main", "knob")}
    check(main == syms["dp_main"] and knob == syms["dp_knob"] and (first, count) == (6, len(added)) and tables == want,
          f"{key}: 0x400ffe30 -> dp_main, 0x4010053c -> dp_knob; their tables, machines 6..{5 + len(added)}: "
          + ", ".join(m["name"] + " " + ("its draws" if m["code"] in ("sampler", "refmachine2") else "the stock ones")
                      for m in added))


# --- 2. the dispatchers -------------------------------------------------------------------------------------------
def dispatch_tests(key, img, runtime, syms, added):
    names = {syms[s]: s for s in ("smp_main_draw", "smp_knob_draw", "ref2_main_draw", "ref2_knob_draw")}
    by_code = {m["code"]: m["index"] for m in added}
    u = UI(img, runtime)
    cases = [(m, 0, True) for m in list(range(6)) + [m["index"] for m in added] + [TS.NM, 100]]
    cases += [(by_code["refmachine2"], 6, True), (by_code["refmachine2"], 0, False)]
    ok, seen = True, []
    for entry, kind, stock in ((MAIN_ENTRY, "main", "main"), (KNOB_ENTRY, "knob", "knob")):
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
    check(ok, f"{key}: each dispatcher calls the selected track's machine's draw (SAMPLE's, REF2's) or the stock "
              f"draw, once with the same arguments, for machines 0..5, {', '.join(str(m['index']) for m in added)}, "
              f"{TS.NM}, 100, track 6 and no project ({2 * len(cases)} cases)" + (f"; DIFFERENT {seen[:3]}" if seen else ""))


# --- 3. REF2's main screen ------------------------------------------------------------------------------------------
def main_tests(key, img, runtime, syms, ref2, other, show):
    u = UI(img, runtime)
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
        diff = [(x, y) for x in range(W) for y in range(H) if lit(fb, x, y) != lit(stock, x, y)]
        x0, x1, y0, y1 = BAND
        inside = all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in diff)
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
    u = UI(img, runtime)
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--show", action="store_true", help="REF2's label and knob view in ASCII")
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
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
