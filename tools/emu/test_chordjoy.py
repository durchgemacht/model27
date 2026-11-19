#!/usr/bin/env python3
"""Proof of Chord Joy (notes/87: tools/machines/chordtables/chord_joy.c, in the CHORD+ package since chordtables 0.5),
on the OS's own code (Unicorn).

1. The builds (no Unicorn): chordtables alone, with Transpose, and in the offered set; KeyboardView's key slot
   (0x400ff9cc) -> cj_keys, and cj_next_keys is Transpose's tr_keys when that part is in, else the stock handler.
2. The keys, through the slot as the OS calls it, the stock handler running behind: with Chord Joy off, on another
   machine, with FUNC / TRACK / MACHINES held, in grid mode or the pattern selection, every event gives the same d0
   and the same calls as the stock OS. With it on, on a CHORD track:
     TRIG 1-8   SHAPE set through the parameter object (0x4000ba7a: descriptor 72, the degree's row, recording on),
                then the stock play of the degree's root key (the same call the stock OS makes for that key);
     TRIG 9-16  with a degree held: the stock release of the root, SHAPE to the direction's row, the play again;
                released: SHAPE back (recording off), nothing played; without a degree held: taken, nothing else;
     the degree's release: the stock release of its root key.
   Registers d2-d7/a2-a6 and the stack kept.

    python3 tools/emu/test_chordjoy.py --cycles firmware/model-cycles_OS1.13.syx [--dry]

Unicorn's JIT stops with SIGILL in a sandbox that forbids generated code: run it in a normal terminal.
"""
import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

KB_SLOT, KB_KEYS, PARAM_SET, SHAPE_DESC, CHORD = 0x400ff9cc, 0x4001a0d2, 0x4000ba7a, 72, 5
ROOT = [0, 2, 4, 5, 7, 9, 11, 12]
QUAL = [0, 1, 1, 0, 0, 1, 2, 0]
DIRS = [[4, 23, 3, 8, 3, 10, 16, 6, 14], [3, 23, 4, 8, 19, 7, 15, 6, 13], [19, 23, 3, 8, 12, 21, 5, 6, 27]]
TRIG = lambda n: 15 + n             # noqa: E731  the key code of TRIG n
SELECTIONS = (([], False), ([], True), (["sampler", "digidelay", "pots", "smpfilter", "crush", "ring", "reso", "eq"], True))


def composed(stock, sel, transpose):
    tweak, info = compose.compose(stock, sel + ["chordtables"], transpose=transpose)
    patched, _ = build.apply_writes(stock, [tweak])
    runtime = build.payload_runtime(tweak, stock, None)
    return tweak, info, bytes(patched) + build.payload_image(tweak, runtime), runtime


def sym(tweak, name):
    return int(tweak["symbols"][name], 16)


def build_tests(stock):
    out = []
    for sel, tr in SELECTIONS:
        w = composed(stock, sel, tr)
        tweak, _info, img, _rt = w
        key = "+".join(sel + ["chordtables"] + (["transpose"] if tr else []))
        slot = struct.unpack(">I", img[KB_SLOT - 0x40000400:KB_SLOT - 0x40000400 + 4])[0]
        nxt = sym(tweak, "tr_keys") if tr else KB_KEYS
        cj = sym(tweak, "cj_keys")
        body = bytes(w[3][cj - 0x43000000:cj - 0x43000000 + 0x3e0])   # the payload as it runs, from 0x43000000
        check(slot == sym(tweak, "cj_keys") and body.count(nxt.to_bytes(4, "big")) >= 1
              and (tr or body.count(sym(tweak, "cj_keys").to_bytes(4, "big")) == 0),
              f"{key}: the key slot holds cj_keys ({slot:#x}); the entry behind is "
              f"{'tr_keys' if tr else 'the stock handler'} ({nxt:#x})")
        if sel or tr:                               # the same build without the package, to compare against
            bt, _bi = compose.compose(stock, sel, transpose=tr)
            bp, _ = build.apply_writes(stock, [bt])
            brt = build.payload_runtime(bt, stock, None)
            base = (bytes(bp) + build.payload_image(bt, brt), brt)
        else:
            base = (stock, None)
        out.append((key, w, base))
    return out


# --- 2. the keys ------------------------------------------------------------------------------------------------------
def kb(u, code, flags, held=(), mode=None, t=2, machine=CHORD, k32=0x100):
    """KeyboardView's key handler through its slot (view, event): (d0, the calls, kept)."""
    import probe_transpose as P
    import test_shortcuts as SH
    u.keys(held)
    st = bytearray(0x200)
    if mode == "grid":
        st[P.GRID_A] = st[P.GRID_B] = 1
    elif mode == "select":
        st[P.SELECT] = 1
    u.uc.mem_write(P.STATE, bytes(st))
    u.uc.mem_write(P.HOLDER, struct.pack(">I", P.HVT))
    u.uc.mem_write(P.HVT + 40, struct.pack(">I", P.H_PAT))
    pat = bytearray(722)
    pat[708] = 0x11
    u.uc.mem_write(P.PATTRK, bytes(pat))
    for i in range(6):                              # the project's tracks, their sound (machine +38, k 32 +84)
        u.uc.mem_write(SH.PROJ + 212 + 68 * i, struct.pack(">I", SH.TRACK_VT))
    u.uc.mem_write(SH.TRACK_VT + 40, struct.pack(">I", SH.SOUND_FN))
    snd = bytearray(100)
    snd[38] = machine
    struct.pack_into(">H", snd, 84, k32)
    u.uc.mem_write(SH.SOUND, bytes(snd))
    ev = bytearray(32)
    struct.pack_into(">II", ev, 12, code, flags)
    u.uc.mem_write(SH.EVENT, bytes(ev))
    u.hooks = {SH.UI_STATE: ("ui", P.STATE), SH.PROJECT: ("project", SH.PROJ), SH.PROJECT_TRACKS: ("tracks", SH.SEL),
               P.TRACK_OF: ("track", t), P.HOLDER_OF: ("holder", P.HOLDER), P.H_PAT: ("pattern", P.PATTRK),
               P.PSLOT_OF: ("pslot", P.PSLOT), P.SEQ_OF: ("seq", P.HOLDER), P.F_D0DC: ("d0dc", 0),
               P.F_CCC0: ("ccc0", 0), P.VEL_WORD: ("velword", 0x64), P.PLAY: ("play", 0), P.RELEASE: ("release", 0),
               P.KEY_BASE: ("base", 0), SH.VIEW_LEDS: ("leds", 0), SH.SOUND_FN: ("sound", SH.SOUND),
               PARAM_SET: ("shape", 0)}
    u.calls.clear()
    vals = SH.sentinels(u)
    d0 = u.call(u.u32(KB_SLOT), SH.VIEW, SH.EVENT)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals
    calls = []
    for n, a in u.calls:
        if n in ("play", "base", "leds"):
            calls.append((n, a[:4]))
        elif n == "release":                        # (view, key): two arguments, the rest is the caller's stack
            calls.append((n, a[:2]))
        elif n == "shape":
            calls.append((n, (a[1], a[2], a[3], a[4] & 0xff)))
    return d0 & 0xff, calls, u.sp_ok and kept and not u.bad


def key_tests(key, base, w):
    """base: the same build without the package (the stock OS for chordtables alone)."""
    import test_shortcuts as SH
    _tweak, _info, img, runtime = w
    a, b = SH.UI(base[0], base[1] or b""), SH.UI(img, runtime)
    M, F, Tk = SH.MACHINES, SH.FUNC, SH.TRACK
    bad, cases = [], 0
    for code in range(15, 33):                      # not ours: as the stock OS
        for held, mode, machine, k32 in (((), None, CHORD, 0), ((), None, 1, 0x100), ((F,), None, CHORD, 0x100),
                                         ((Tk,), None, CHORD, 0x100), ((M,), None, CHORD, 0x100),
                                         ((), "grid", CHORD, 0x100), ((), "select", CHORD, 0x100),
                                         ((), None, CHORD, 0x200)):
            for flags in (1, 0, 1 | 8, 1 | 0x20):
                ra = kb(a, code, flags, held, mode, machine=machine, k32=k32)
                rb = kb(b, code, flags, held, mode, machine=machine, k32=k32)
                cases += 1
                if ra[0] != rb[0] or ra[1] != rb[1] or not (ra[2] and rb[2]):
                    bad.append((code, held, mode, machine, k32, flags, ra, rb))
    check(not bad, f"{key}: {cases} key events with Chord Joy off, on another machine, with FUNC / TRACK / MACHINES "
                   "held, in grid mode or the selection: the same d0 and calls as the build without it"
                   + (f"; DIFFERENT {bad[:2]}" if bad else ""))

    def stock_calls(code, flags):
        return kb(a, code, flags, machine=CHORD, k32=0)[1]

    bad = []
    for d in range(1, 9):                           # a degree, pressed and released
        r1 = kb(b, TRIG(d), 1)
        want = [("shape", (SHAPE_DESC, DIRS[QUAL[d - 1]][0] << 8, 2, 1))] + stock_calls(TRIG(1) + ROOT[d - 1], 1)
        r2 = kb(b, TRIG(d), 0)
        if r1[0] != 1 or r1[1] != want or not r1[2] or r2 != (1, stock_calls(TRIG(1) + ROOT[d - 1], 0), True):
            bad.append((d, r1, r2, want))
    check(not bad, f"{key}: TRIG 1-8 with Chord Joy on: SHAPE to the degree's chord (recording on), then the stock "
                   "play of its root key; the release, the stock release of that key"
                   + (f"; DIFFERENT {bad[:2]}" if bad else ""))

    bad = []
    for d in (1, 2, 7):
        for k in range(1, 9):                       # a direction while the degree is held
            root = TRIG(1) + ROOT[d - 1]
            kb(b, TRIG(d), 1)
            r1 = kb(b, TRIG(8 + k), 1)
            want = (stock_calls(root, 0) + [("shape", (SHAPE_DESC, DIRS[QUAL[d - 1]][k] << 8, 2, 1))]
                    + stock_calls(root, 1))
            r2 = kb(b, TRIG(8 + k), 0)
            back = [("shape", (SHAPE_DESC, DIRS[QUAL[d - 1]][0] << 8, 2, 0))]
            r3 = kb(b, TRIG(d), 0)
            if r1 != (1, want, True) or r2 != (1, back, True) or r3 != (1, stock_calls(root, 0), True):
                bad.append((d, k, r1, r2, r3))
    lone = [kb(b, TRIG(9 + i), f) for i in range(8) for f in (1, 0)]
    check(not bad and all(r == (1, [], True) for r in lone),
          f"{key}: TRIG 9-16 with a degree held: its release, SHAPE to the direction's chord, its play again; released: "
          "SHAPE back without recording, nothing played; without a degree: taken, nothing done"
          + (f"; DIFFERENT {bad[:2]}" if bad else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--dry", action="store_true", help="section 1 only (the builds, no Unicorn)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    print("1. the builds")
    builds = build_tests(stock)
    if not args.dry:
        print("2. the keys")
        for key, w, base in builds:
            key_tests(key, base, w)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
