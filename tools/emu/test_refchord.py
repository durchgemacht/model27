#!/usr/bin/env python3
"""Proof of the builder's extensions of a stock machine (notes/66 §3, step W2) on the OS's own code, with REFC, the
reference extension of CHORD (tools/machines/refchord/): a shortcut, RETRIG + SWEEP = Wavetable (k 30, 0 to 64), and
two hooks that count, on CHORD's call for its frames (0x400ab15e) and on the screen's tick (0x400075f0).

For each selection (by default: refchord; refchord,sampler; sampler,refchord; sampler,refchord,refmachine2), on the
official OS 1.13:
  1. start-up: the bootstrap's own aPLib depacker reads the grown OS back; the boot hook copies the payload and clears
     the BSS (REFC alone: nothing registered, the stub only copies);
  2. the sites: 0x400ab15e -> rc_setup; the tick -> rc_hook_tick, or the dispatcher with SAMPLE; the knob lookup's
     entry and the three record functions -> the shortcut layer, SAMPLE's wrappers next in its chain; the layer's
     tables from machine 5 (CHORD), on the descriptor table the OS uses: the stock one without an added machine, the
     registrar's copy with one; REFC alone writes nothing of the registrar's;
  3. the knob, through the vtable entry and the OS's own key test: RETRIG held + SWEEP on a CHORD track gives
     descriptor 3; REF2's RETRIG + COLOR descriptor 1 on its machine; every other knob, machine, key or held trig
     the stock lookup's answer;
  4. descriptor 3: k 30, 0..64 as 8.8, default 0, no CC and no NRPN, "Wavetable" / "WAVE", still machine -1, the rest
     of the table untouched; the OS's range getter and value setter; interface object 3 shows "0".."64";
  5. a CHORD sound saved (versions 2 and 1) and loaded: the stock record plus k 30 in record slot 30 and k 32 (the
     shortcut layer's switches, notes/63 §17) in slot 18, back at the load; a record from the official OS loads k 30
     at 0;
  6. the tick: REFC's counts once and returns the stock getter's answer; with SAMPLE, the dispatcher calls REFC's
     tick first (machine 5), then the others in machine order, then the getter once;
  7. the voice loop: CHORD on two tracks, SWEEP moving, plays as on the stock OS sample for sample, every setup through
     rc_setup (its counter = the stock setup's calls).

Needs Unicorn and numpy (pip install unicorn numpy) and m68k-elf-objdump; Unicorn's JIT does not run inside a
sandbox that forbids it: run it in a normal terminal (model27's .venv-emu has both). About a minute.

    python3 tools/emu/test_refchord.py --cycles model-cycles_OS1.13.syx [--machines refchord,sampler] [--blocks 80]
"""
import argparse
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compose                      # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import test_compose as TC           # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_shortcuts as S          # noqa: E402
from test_sdvintage_7th import check, SCRATCH  # noqa: E402

SELECTIONS = [["refchord"], ["refchord", "sampler"], ["sampler", "refchord"], ["sampler", "refchord", "refmachine2"]]
CHORD, SWEEP_KNOB, DESC = 5, 6, 3            # machine 5; knob 6 = SWEEP; RETRIG + SWEEP is the layer's descriptor 3
K30, MAX = 30, 64
SETUP, CALL_AT, TICK_AT, GETTER = 0x400a8080, 0x400ab15e, 0x400075f0, 0x40076be4   # CHORD's setup, its call, the tick
ALONE_SITES = {0x400004b2, 0x400075f0, 0x4005aecc, 0x4005afa0, 0x4005b054, 0x400ab15e, 0x400b1106, 0x401005a8,
               0x4016cae8}               # the boot hook, the tick, the records, CHORD's call, the stub's mask and room,
                                          # the knob lookup's entry: REFC alone, nothing of the registrar's
VIEW = S.VIEW


def jsr(va):
    return b"\x4e\xb9" + struct.pack(">I", va)


# --- 2. the sites ---------------------------------------------------------------------------------------------------
def site_tests(key, stock, tweak, img, runtime, added):
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    u = S.UI(img, runtime)
    at = lambda va, n: bytes(u.uc.mem_read(va, n))
    check(at(CALL_AT, 6) == jsr(syms["rc_setup"]), f"{key}: {CALL_AT:#x} -> jsr rc_setup ({syms['rc_setup']:#x})")
    tick = syms.get("dp_tick", syms["rc_hook_tick"])
    check(at(TICK_AT, 6) == jsr(tick), f"{key}: {TICK_AT:#x} -> jsr {'dp_tick' if 'dp_tick' in syms else 'rc_hook_tick'}")
    sites = {S.SAVE2: "sc_save2", S.SAVE1: "sc_save1", S.LOAD: "sc_load"}
    sc = syms["sc_data"]
    chain = [u.u32(sc + 4 * i) for i in range(3)]
    smp = "smp_hook_save2" in syms
    want = [syms[s] for s in ("smp_hook_save2", "smp_hook_save1", "smp_hook_load")] if smp else [0] * 3
    check(u.u32(S.KNOB_ENTRY) == syms["sc_knob"]
          and all(at(va, 8).hex() == f"4ef9{syms[s]:08x}4e71" for va, s in sites.items()) and chain == want,
          f"{key}: 0x401005a8 -> sc_knob; the record functions -> the layer; next of the chain: "
          + ("SAMPLE's wrappers" if smp else "the stock body"))
    first, count, descn = at(sc + 16, 1)[0], at(sc + 17, 1)[0], u.u32(sc + 12)
    want_descn = gs.DESCN if added else g7.DESC
    check(first == CHORD and count == 1 + len(added) and descn == want_descn,
          f"{key}: the layer's tables from machine {first} ({count} machines), on the descriptor table at {descn:#x} "
          f"({'the registrar' + chr(39) + 's copy' if added else 'the stock table: nothing moved'})")
    if not added:
        got = {compose.BASE + w["off"] for w in tweak["writes"]}
        check(got == ALONE_SITES, f"{key}: {len(got)} writes, all of them REFC's, the layer's and the payload's boot "
              f"({', '.join(hex(a) for a in sorted(got - ALONE_SITES)) or 'nothing of the registrar'})")
        ptrs = slice(0x40118590 - compose.BASE, 0x40118610 - compose.BASE)
        check(img[ptrs] == stock[ptrs] and g7.refs32(img[:len(stock)], g7.DESC) == g7.refs32(stock, g7.DESC),
              f"{key}: CHORD's pointer table and the references to the stock descriptor table as in the stock OS")
    return syms


# --- 3. the knob ----------------------------------------------------------------------------------------------------
def knob_tests(key, img, runtime, added):
    u = S.UI(img, runtime)
    ref2 = next((m["index"] for m in added if m["code"] == "refmachine2"), None)
    machines = [0, 1, 2, 3, 4, CHORD] + [m["index"] for m in added] + [6 + len(added), 100, 0xffffffff]
    got, fwd = {}, True
    for held in ((), (S.RETRIG,), (S.RETRIG, S.FUNC), (S.RETRIG, S.TRACK), (S.RETRIG, S.LFO), (S.FUNC,), (S.LFO,)):
        u.keys(held)
        for trig in (0, 1):
            for m in machines:
                for k in range(16):
                    got[held, trig, m, k], ok_ = S.knob(u, m, k, trig)
                    fwd &= ok_
    u.keys(())

    def want(held, trig, m, k):
        if held == (S.RETRIG,) and not trig:
            if m == CHORD and k == SWEEP_KNOB:
                return DESC
            if ref2 is not None and m == ref2 and k == 4:
                return 1
        return S.STOCK_ANSWER
    bad = [c for c in got if got[c] != want(*c)]
    check(not bad, f"{key}: descriptor 3 for RETRIG + SWEEP on CHORD (machine 5) only"
          + (f", descriptor 1 for RETRIG + COLOR on REF2 (machine {ref2})" if ref2 else "")
          + f"; the stock answer for every other knob, machine, key and held trig ({len(got)} cases)"
          + (f"; DIFFERENT {bad[:4]}" if bad else ""))
    check(fwd, f"{key}: the stock lookup called once per call with the same arguments; the stack comes back")


# --- 4. descriptor 3 ------------------------------------------------------------------------------------------------
def descriptor_tests(key, img, runtime, added):
    u = S.UI(img, runtime)
    u.hooks = {0x400802e0: ("new", 0), 0x400cf044: ("atexit", 0)}
    u.call(0x400de244, count=50_000_000)              # the interface objects, as the OS builds them at boot
    built = not u.bad
    at_ = gs.DESCN if added else g7.DESC
    ndesc = 76 + 5 * len(added)
    table = lambda: [bytes(u.uc.mem_read(at_ + 0x38 * i, 0x38)) for i in range(ndesc)]
    before = table()
    u.hold(S.RETRIG, True)
    d, ok = S.knob(u, CHORD, SWEEP_KNOB)
    u.hold(S.RETRIG, False)
    after = table()
    f, f0 = struct.unpack(">14i", after[DESC]), struct.unpack(">14i", before[DESC])
    names = (u.cstr(f[11] & 0xffffffff), u.cstr(f[13] & 0xffffffff))
    check(d == DESC and ok and f[0] == -1 and f[1:9] == (K30, 0, MAX << 8, 0, 0, -1, -1, 0) and f[9:11] == f0[9:11]
          and f[12] == f0[12] and names == ("Wavetable", "WAVE"),
          f"{key}: descriptor 3 installed in the table at {at_:#x}: k 30, 0..64 (8.8), default 0, no CC, no NRPN, "
          f"{names[0]} / {names[1]}, machine still -1")
    check(all(after[i] == before[i] for i in range(ndesc) if i != DESC), f"{key}: the other {ndesc - 1} descriptors "
          "untouched")
    u.call(S.RANGE, DESC)
    rng = struct.unpack(">3i", u.uc.mem_read(SCRATCH, 12))
    check(rng == (0, MAX << 8, 0), f"{key}: the OS's range getter (0x4005a65a) reads descriptor 3 as {rng}")
    obj = S.OBJ
    vt = obj + 0x100
    u.uc.mem_write(obj, struct.pack(">I", vt))
    for off in range(0, 0x80, 4):
        u.uc.mem_write(vt + off, struct.pack(">I", obj + 0x200 + off))
    tries, clamped = (-1000, -1, 0, 300, MAX << 8, (MAX << 8) + 1, 100000), []
    for v in tries:
        u.hooks = {obj + 0x200 + 24: ("check", 1), obj + 0x200 + 92: ("set", 0), obj + 0x200 + 72: ("notify", 0),
                   obj + 0x200 + 28: ("get", 0)}
        u.calls.clear()
        u.call(S.SET_VALUE, obj, DESC, v, 0, 0, 0)
        clamped.append([S.s32(a[2]) for n, a in u.calls if n == "set"])
    check(clamped == [[min(max(v, 0), MAX << 8)] for v in tries] and not u.bad,
          f"{key}: the OS's value setter (0x4000b274) clamps to 0..64: "
          + ", ".join(f"{v} -> {c[0] if c else None}" for v, c in zip(tries, clamped)))
    uo = S.UI_OBJ + 100 * DESC
    shown = []
    for v in (0, 1, 32, 63, 64):
        u.uc.mem_write(SCRATCH + 0x100, bytes(32))
        u.call(u.u32(uo + 0x20), uo + 0x14, v << 8, SCRATCH + 0x100)
        shown.append(u.cstr(SCRATCH + 0x100))
    check(built and u.u32(uo + 0x20) == S.FMT_INT and u.u32(uo + 0x2c) == 0 and shown == ["0", "1", "32", "63", "64"],
          f"{key}: interface object 3: FMT_INT, no 'Error' picture, shows {shown}")


# --- 5. save and load -----------------------------------------------------------------------------------------------
def save_tests(key, stock, img, runtime):
    rng = np.random.default_rng(66)
    a, b = S.UI(stock), S.UI(img, runtime)
    values = (0, 0, 0x2000, 0)                      # k 28..31: k 30 = 32
    for fn, ver in ((S.SAVE2, 2), (S.SAVE1, 1)):
        snd = S.sound_bytes(rng, CHORD, values)
        ra, reca, la, backa = S.save_load(a, snd, fn)
        rb, recb, lb, backb = S.save_load(b, snd, fn)
        diff = [i for i in range(100) if reca[i] != recb[i]]
        check(ra == rb == 1 and set(diff) <= set(range(84, 92)) | {64, 65} and recb[88:90] == snd[80:82]
              and recb[64:66] == snd[84:86] and b.sp_ok and not b.bad,
              f"{key}: save version {ver} of a CHORD sound: the stock record plus k 30 in record slot 30, and k 32 (the "
              f"switches, saved for every sound since the layer's 0.2, notes/63 §17) in slot 18 (bytes {diff})")
        if ver == 2:
            check(la == lb == 1 and backb[80:82] == snd[80:82] and backb[84:86] == snd[84:86]
                  and backb[:76] == backa[:76] and backb[86:] == backa[86:],
                  f"{key}: loaded: k 30 back (32) and k 32, everything else as the stock load")
        else:
            check(la == lb == 0 and backb == backa, f"{key}: a version 1 record: refused by the load as before")
    snd = S.sound_bytes(rng, CHORD, values)
    _, reca, _, _ = S.save_load(a, snd, S.SAVE2)
    b.uc.mem_write(S.RECORD, reca)
    b.uc.mem_write(S.SOUND, b"\xcc" * 100)
    b.call(S.LOAD, S.SOUND, S.RECORD)
    check(bytes(b.uc.mem_read(S.SOUND + 80, 2)) == bytes(2),
          f"{key}: a record saved by the official OS loads k 30 at 0, the stock table")


# --- 6. the tick ----------------------------------------------------------------------------------------------------
def tick_tests(key, img, runtime, syms, added):
    u = S.UI(img, runtime)
    tick_of = {"sampler": "smp_hook_tick", "refmachine2": "ref2_hook_tick"}
    others = [(syms[tick_of[m["code"]]], tick_of[m["code"]]) for m in sorted(added, key=lambda m: m["index"])
              if m["code"] in tick_of]          # the other machines' ticks, in machine order
    u.hooks = {GETTER: ("getter", 0x5a)}
    for va, name in others:                         # the other machines' ticks stubbed: their work is not this proof's
        u.hooks[va] = (name, 0x5a)
    target = syms.get("dp_tick", syms["rc_hook_tick"])
    before = u.u32(syms["rc_ticks"])
    r = u.call(target, VIEW)
    order = [n for n, _a in u.calls]
    views = all(a[0] == VIEW for _n, a in u.calls)
    want = ["getter"] + ([n for _v, n in others] + ["getter"] if "dp_tick" in syms else [])
    check(r & 0xff == 0x5a and u.u32(syms["rc_ticks"]) == before + 1 and order == want and views and not u.bad,
          f"{key}: the tick: REFC's counts once and returns the getter's answer; calls {order}")


# --- 7. the voice loop ----------------------------------------------------------------------------------------------
def voice_tests(key, stock, tweak, img, runtime, syms, blocks):
    def run(img_, runtime_=None, tweak_=None):
        e = TC.engine(img_, runtime_, tweak_)
        calls = [0]

        def hk(uc, a, s, u_):
            calls[0] += 1
        e.uc.hook_add(UC_HOOK_CODE, hk, begin=SETUP, end=SETUP)
        for t, sweep in ((0, 24), (3, 90)):
            e.set(t, machine=CHORD, note=60, pitch=64, finetune=64, color=3, shape=43, sweep=sweep, contour=64,
                  punch=0, gate=0, decay=64)
        out = []
        for b in range(blocks):
            e.set(0, sweep=(24 + 3 * b) % 128)      # SWEEP moves during track 0's note
            out.append(e.block(0b001001 if b in (1, blocks // 2) else 0)[[0, 3]])
        return np.array(out), calls[0], e
    x, n0, e0 = run(stock)
    y, n1, e1 = run(img, runtime, tweak)
    counted = struct.unpack(">I", e1.uc.mem_read(syms["rc_setups"], 4))[0]
    check(np.array_equal(x, y) and np.max(np.abs(x)) > 1e6 and not e0.unmapped and not e1.unmapped,
          f"{key}: CHORD on tracks 1 and 4, SWEEP moving: identical to the stock OS, sample for sample "
          f"(peak {np.max(np.abs(x)):.3g})")
    check(n1 == n0 > 0 and counted == n1, f"{key}: every setup through rc_setup: {counted} counted, {n1} calls of "
          f"0x400a8080 ({n0} in the stock OS)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--blocks", type=int, default=80, help="blocks of 32 frames in the voice loop")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else SELECTIONS
    stock = T.main_os_from_syx(args.cycles)
    for ids in selections:
        if "refchord" not in ids:
            sys.exit(f"!! {'+'.join(ids)}: the proof needs refchord")
        key = "+".join(ids)
        tweak, info, img, runtime = TC.built(stock, ids)
        added = TC.configure([i for i in ids if compose.load_manifest(i)["_machine"]])
        print(f"\n{key}: CHORD extended (machine 5)" + "".join(f", {m['name']} = machine {m['index']}" for m in added)
              + f"; payload {len(runtime)} bytes at {compose.gs.PAY_ALONE:#x}")
        print("start-up")
        X.bootstrap_depack_ok(args.cycles, tweak, None) or t7.FAIL.append(f"{key}: bootstrap")
        X.boot_hook_ok(img, runtime) or t7.FAIL.append(f"{key}: boot hook")
        print("the sites")
        syms = site_tests(key, stock, tweak, img, runtime, added)
        print("the knob")
        knob_tests(key, img, runtime, added)
        print("descriptor 3")
        descriptor_tests(key, img, runtime, added)
        print("save and load")
        save_tests(key, stock, img, runtime)
        print("the tick")
        tick_tests(key, img, runtime, syms, added)
        print("the voice loop")
        voice_tests(key, stock, tweak, img, runtime, syms, args.blocks)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
