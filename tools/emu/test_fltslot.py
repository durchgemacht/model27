#!/usr/bin/env python3
"""Proof of the filter slot (the track filters, notes/72 §10 to §19; the Track FX since fltslot 0.7, notes/73) on the
OS's own code, with REFF, the reference filter (tools/machines/refflt/), Samples, the Model:Samples' filter
(tools/machines/smpfilter/, id 1), and every Track FX whose manifest names its host build ("proof": {"host": ...,
"cost_states": ...}, notes/73 §16; Crush, tools/machines/crush/, id 2, the first), through the builder's part
tools/machines/fltslot/. A new Track FX needs no change here: its manifest's proof section is its model and its cost.

For each selection (by default: refflt; refflt,refflt2; sampler,refflt; refdelay,refflt; smpfilter; smpfilter,refflt;
sampler,smpfilter; each hosted Track FX alone; and the full table: Samples, the hosted ones, then REFF and its copies,
up to the part's most, eight; refflt2 to refflt9 are copies of REFF with ids 254 to 247 and names of their own, made
for the test in a folder of packages of its own), on the official OS 1.13:
  1. start-up: the bootstrap's own aPLib depacker reads the grown OS back; the boot hook copies the payload and clears
     the BSS;
  2. the sites: the audio block's call of Volume + Dist (0x40059852) -> jsr fl_post, the boot's call of the parameter
     tables' builder (0x4004486c) -> jsr fl_boot, the encoder handler's question for TRACK (0x4001f886) -> jsr fl_keys,
     the knob lookup's vtable entry (0x401005a8) -> fl_knob, the sound record functions (0x4005afa0, 0x4005b054,
     0x4005aecc -> jmp fl_save2, fl_save1, fl_load, in front of the layer's); the shortcut layer's MACHINES case and,
     since fltslot 0.11 (the layer's 0.5, notes/63 §25), the pattern's p-lock tables (0x4005b998, 0x4005baca ->
     sc_ptab, 0x4005aa34 -> jmp sc_conv), in every filter build;
     every other write as in the build without the filters; the data block: the table (entry 0 none, then the build's
     filters by id, with their process, reset, the type's name and the values' names and formatters), the build's
     values, the lookup, the gesture and the record wrappers behind the part's (the layer's sc_knob, sc_save2, sc_save1,
     sc_load, the effect slots' fx_keys), the rows of descriptors 1 to n and 5, the neutral words, the state zero,
     each entry's start words (fltslot 0.8: the filter's params[].start, else the neutral word) and count of values
     (fltslot 0.10, none 0);
  3. the audio: a stock engine and the build's engine side by side, block for block, on the OS's own code: the voice
     loop (0x400a7d4a) with six stock machines and trigs, then the audio function from 0x4005984a to 0x40059858 (move.l
     a2,(sp) ; pea 0x80001858 ; jsr Volume + Dist), with a2 the smoothed parameters and a3 a message whose +16 is the
     block's triggered tracks, as the OS passes them to the voice loop. The tracks' sounds are objects of the test
     (*0x800017ec[t], k 32 at +84), or none, and then the copy at 0x800015ae + 66 t + 64:
     - every sound with id 0, an id the build does not hold, or the machine's switches alone in k 32's high byte: the
       six tracks the stock OS's, bit for bit, and the EMAC as Volume + Dist left it;
     - sounds choosing REFF, refflt2, Samples or Crush: each track the model's, bit for bit: the stock output
       through the filter its sound chose, with the track's k 28 and k 29 and its trig (REFF's arithmetic in Python;
       Samples' the host build of SAMPLE's own sources, src/smp_filter.c's C model of the EMAC loops, as One-Shot's
       host tests use it; a hosted Track FX's its host build); the id read in the sound or, with none, in the copy; with
       more than two filters in the build, the third and fourth on two tracks of the fourth scene;
       a change of filter (another id, a sound that chose another, none) faded across the block from the filter that
       stops (on a copy of the input) to the one that starts (after its reset), the one that stops reset after; a
       filter that comes back starting from its reset;
     - each filter called with MACSR 0xa0 and acc0-acc3 clear; after the part, MACSR as the OS had it and acc0-acc3
       clear; d2-d7/a2-a6 and the stack as the call replaced leaves them; no access outside memory;
     - hot tracks (Volume + Dist at 127, Reso at the top, Cutoff sweeping across the centre every block): the same;
     - what the part costs, in instructions per block (the part's code and the filters'): every track with none,
       every track with the first filter; each real filter's own cost per track and block (Samples: steady lowpass,
       steady highpass, at the centre, gliding, the first block after its reset; a hosted Track FX the states its
       manifest names, Crush: off, a hard hold with Bits, a
       soft one with Bits, Bits alone, gliding, silent, the first block), written to build/filter-cost.json and equal
       to what its manifest declares (cost.emulation);
  4. the boot (T2): the OS's own builder of the parameter tables (0x4005a274), stock and through fl_boot: descriptors
     1 to n of the table the OS uses (and of the stock one) the build's rows (group 7, k 28.., 0..127, the defaults,
     CC 74 / 71, NRPN 1:20 / 1:21, the first filter's names), descriptor 5 the type's (machine -1, k 0, no CC);
     k 28.. -> descriptors 1.. on every machine, every other k as in the stock OS, k 0 on nothing new; CC 74 and 71
     and NRPN 1:20 and 1:21 on them, nothing else changed; a new sound (0x400618f2) with the defaults on k 28..,
     everything else as in the stock OS;
  5. the knob lookup (T2), through the vtable entry, the layer's and the stock lookup behind it (the stock one
     stubbed), on the selected track's sound with none, an id the build lacks and each filter: RETRIG + SWEEP /
     CONTOUR / COLOR / SHAPE -> descriptors 1 to 4 when that filter has the value, else 5, display only (fltslot 0.10:
     the part's na set, descriptor 5 under the filter's tag, or Track FX for none, with the type's formatter), also
     with FUNC, TRACK, LFO or a trig held; RETRIG + PITCH alone -> 5 (na clear, under Track FX again), with FUNC,
     TRACK, LFO or a trig: the stock answer; every other knob, and everything without RETRIG: the stock answer; the
     stock lookup called once each time with the same arguments; the values' names and formatters those of the
     selected track's filter's entry, in both descriptor tables and the interface objects; Control All's lookups of
     each track (0..5): the value's descriptor whatever that track's filter, the names left alone; descriptor 5's
     object with the type's formatter and descriptor 1's steps;
  5b. LFO + a knob (0x4001eaa2, ParameterPageView's own path for the LFO's destination, which builds its knob list from
     the machine record, 0x4000bf42, and asks no lookup), run whole after the boot's tables (the destination's k is
     read in the descriptor's row, which fl_boot writes) with the records filled as at boot, on the selected track's
     sound with none and each filter: with RETRIG held, COLOR..CONTOUR set the destination to the values that filter
     has (k 28 + its place), also with FUNC or TRACK; a value it lacks, or none: no destination set, the knob list
     freed as the routine frees it (fltslot 0.10); every other knob, and everything without RETRIG, the destination
     of the build without the filters;
  6. the formatters: Filter Cutoff's (fl_fmt_cut) over the 128 steps, -64 .. 0 .. 63 as SAMPLE's, three characters at most; the
     type's (fl_fmt_type) naming the selected track's filter, OFF for none or an id the build lacks; on a knob without
     a value (fltslot 0.10) "---" for a filter and OFF for none, also in a measuring build;
  7. the type (T2): fl_keys as the encoder handler calls it at 0x4001f886, with the handler's frame: on descriptor 5
     the handler's end with 0 and its registers, four detents for a step, the count again after a change of direction
     or 0.4 s, the steps through none and the build's filters in the selected track's sound, stopping at the ends, an
     id the build lacks counting as none, the switches in k 32's high byte kept; on another descriptor, the effect
     slots' gesture when the build has it (PATTERN + Delay Time taken there), else isKeyHeld(2) as asked; the start
     words (fltslot 0.8): a step from none gives the sound those that differ from the neutral ones, a step from a
     filter all of them, a step to none none, in the sound and in the targets of the tracks whose note plays it; on a
     knob without a value (fltslot 0.10) the handler's end and no step;
  8. the pattern's p-locks (T2, notes/47 §4.3; the shortcut layer's fix since fltslot 0.11): a pattern saved
     (0x4005b95c) and loaded (0x4005b766) brings back the p-locks of k 23 to 31 and 32 on their parameter, an update of
     one p-lock (0x4005ba90) too, against the stock OS, which loses them or moves them; a file without them the stock
     OS's byte for byte;
  9. a machine change (0x40014072, through the wheel 0x400a2712) after the boot's tables keeps k 28..31;
 12. the load (fltslot 0.5): fl_measure over a window of 750 blocks (the average and the peak share of a block, in
     tenths of a percent, the window cleared after); in a measuring build (compose.py --diag-filters) Filter Cutoff's
     popup shows the average and the type's the peak ("6.4", "12", "99" above 99 %), in every other build the values;
 11. the record (T3), through the real functions and the whole chain (the part, the layer, SAMPLE's wrapper, the stock
     body), against the build without the filters: a save (version 2 and 1) writes the stock record but for slots
     28..31 (each value XOR its neutral word, a value no filter declares 0), slot 18 (k 32's low 10 bits and the
     LFO's and velocity's destinations on a value in bits 10-12 and 13-15) and "none" at slot 4 and +94 for those
     destinations; the load brings the values, k 32 and the destinations back, everything else as without the
     filters; a record of the official OS loads the neutral words and no filter; the official OS reads a filter
     build's record with no destination and slot 18 on k 0 only; a SAMPLE sound keeps its key and switches;
 10. the composer's refusals: a filter with a machine or an effect in one package, an id out of 1..255, its process
     not first in build.roots, its reset not in them, a patch point, another use, a name, type name or value name too
     long, no values or five, an unknown formatter, two filters in one package; nine filters in one build, two
     filters with one id, a filter with a machine's knob value (the rule R1: REF2, CHORD Tables).

Needs Unicorn and numpy (pip install unicorn numpy) and m68k-elf-objdump; Unicorn's JIT does not run inside a sandbox
that forbids it (it stops with SIGILL at the first memory map): run it in a normal terminal.

    python3 tools/emu/test_fltslot.py --cycles model-cycles_OS1.13.syx [--machines refflt,refflt2] [--blocks 120]
    python3 tools/emu/test_fltslot.py --cycles model-cycles_OS1.13.syx --dry      # builds and sites only, no Unicorn
"""
import argparse
import atexit
import contextlib
import ctypes
import json
import math
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np
from unicorn import UcError, UC_HOOK_CODE
from unicorn import m68k_const as mk

import compose                      # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import relocate                     # noqa: E402
import mcengine as E                # noqa: E402
import test_compose as TC           # noqa: E402
import test_shortcuts as SH         # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_exact as X    # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

PART = compose.load_part("fltslot")
DATA = PART["data"]
POST, VOLDIST = 0x40059852, 0x40056f58
H3_FROM, H3_TO = 0x4005984a, 0x40059858                     # move.l a2,(sp) ; pea 0x80001858 ; jsr ; the next one
TRK = 0x80001858
CUR_SND, TARGETS = 0x800017ec, 0x800015ae
SOUND_K32 = 84
SNDS = 0x40740000                                           # the test's sound objects, 0x100 apart
CTX = 0x40760000                                            # the block's message (+16: the triggered tracks)
BOOT_SITES = {0x400004b2, 0x400b1106, 0x4016cae8}           # the payload's boot: the hook, the stub's mask and its sprite
CONV, KNOB, PTAB = 0x4005aa34, 0x401005a8, (0x4005b998, 0x4005baca)
# the shortcut layer's records, MACHINES case and, since its 0.5, the pattern's p-lock tables
LAYER_SITES = {0x4005aecc, 0x4005afa0, 0x4005b054, 0x4001ca1e, CONV, *PTAB}
JSRS = {0x40059852: "fl_post", 0x4004486c: "fl_boot", 0x4001f886: "fl_keys", 0x4001ead8: "fl_lfo"}
RECORD_JMPS = {0x4005afa0: "fl_save2", 0x4005b054: "fl_save1", 0x4005aecc: "fl_load"}
OURS = set(JSRS) | {KNOB} | set(RECORD_JMPS)
BUILDER, DESC_OP, NEW_SOUND, HANDLER_END = 0x4005a274, 0x4005a2de, 0x400618f2, 0x4001f96a
FORMATS = {"int": 0x400456c8, "centre": 0x40045bd6}
UI_OBJ, TIMER, STEP_AT = 0x40a71754, 0xfc07000c, -38
REF_IDS = {"refflt": 255, **{f"refflt{k}": 256 - k for k in range(2, 10)}}   # refflt2 254 .. refflt9 247
COPIES = tuple(i for i in REF_IDS if i != "refflt")         # REFF's copies, made in a folder of their own


def hosted():
    """The Track FX whose manifest names its host build ("proof": {"host": ...}, notes/73 §16), by filter id: each gets
    a selection of its own and goes into the full one, with no change here."""
    out = []
    for d in sorted(compose.MACHINES.iterdir()):
        mf = d / "manifest.json"
        if not mf.is_file():
            continue
        m = json.loads(mf.read_text(encoding="utf-8"))
        u = next((x for x in m.get("uses", []) if x.get("point") == compose.FILTER_POINT), None)
        if u and m.get("proof", {}).get("host"):
            out.append((u["id"], m["id"]))
    return [mid for _i, mid in sorted(out)]


def default_selections():
    """The default selections: the slot's references, Samples, each hosted Track FX alone, and the full table, the
    build's most (Samples, the hosted ones, then REFF and its copies)."""
    base = [["refflt"], ["refflt", "refflt2"], ["sampler", "refflt"], ["refdelay", "refflt"], ["smpfilter"],
            ["smpfilter", "refflt"], ["sampler", "smpfilter"]]
    own = hosted()
    full = (["smpfilter", *own] + ["refflt", *COPIES])[:PART["most"]]
    return base + [[mid] for mid in own] + [full]
FRAMES, TRACKS = 32, 6


def jsr(va):
    return bytes.fromhex("4eb9") + struct.pack(">I", va)


def s32(x):
    return (x + 2 ** 31) % 2 ** 32 - 2 ** 31


@contextlib.contextmanager
def folder(copies):
    """compose.MACHINES pointed at a folder of its own: every package and part (1 MB or so), and for each (name, id) of
    copies a copy of REFF under that name with that id."""
    kept = compose.MACHINES
    with tempfile.TemporaryDirectory() as d:
        compose.MACHINES = pathlib.Path(d)
        try:
            for src in sorted(x for x in kept.iterdir() if x.is_dir()):
                shutil.copytree(src, compose.MACHINES / src.name)
            for name, fid in copies:
                two = compose.MACHINES / name
                shutil.copytree(kept / "refflt", two)
                (two / "refflt.o").rename(two / f"{name}.o")
                m = json.loads((two / "manifest.json").read_text())
                m["id"] = name
                m["build"]["objects"] = [f"{name}.o"]
                u = m["uses"][0]
                u["id"] = fid
                u["short"] = f"R{fid % 100:02d}"
                for prm in u["params"]:
                    prm["long"] = prm["long"].replace("REFF", f"R{fid}")
                (two / "manifest.json").write_text(json.dumps(m))
            yield
        finally:
            compose.MACHINES = kept


def built(stock, ids):
    copies = [(i, REF_IDS[i]) for i in ids if i in COPIES]
    if copies:
        with folder(copies):
            return TC.built(stock, ids)
    return TC.built(stock, ids)


def entry_points(info, mans):
    """{filter id: (process, reset)} where the composer placed them, from each filter's place and its object's
    symbols: REFF's copies share its names, so the tweak's symbols hold one of them only."""
    out = {}
    for p in info["packages"]:
        if p.get("filter_id"):
            u = mans[p["id"]]["_filter"]
            own = compose.MACHINES / p["id"] / f"{p['id']}.o"           # REFF's copies are REFF's object
            obj = (own if own.is_file() else compose.MACHINES / "refflt" / "refflt.o").read_bytes()
            lay = relocate.layout(obj, *compose.roots_of(mans[p["id"]]), p["id"])
            out[u["id"]] = tuple(p["code_at"] + lay["symbols"][n][1] for n in (u["process"], u["reset"]))
    return out


# --- 2. the sites and the data block ----------------------------------------------------------------------------------
def u32(runtime, va):
    return struct.unpack_from(">I", runtime, va - compose.gs.PAY_ALONE)[0]


def cstr(stock, runtime, va):
    """A string of the payload or of the image."""
    if va >= compose.gs.PAY_ALONE:
        raw = runtime[va - compose.gs.PAY_ALONE:va - compose.gs.PAY_ALONE + 64]
    else:
        raw = stock[va - compose.BASE:va - compose.BASE + 64]
    return raw.split(b"\0")[0].decode("latin-1")


def want_names(mans, fid, p):
    """Value p's (long, short, format) for the entry of filter fid (0: none): the filter's own, else the first
    filter's by id that declares it."""
    by_id = sorted((m for m in mans.values() if m["_filter"]), key=lambda m: m["_filter"]["id"])
    m = next((x for x in by_id if x["_filter"]["id"] == fid), None)
    src = m if m and p < len(m["_filter"]["params"]) else next(x for x in by_id if p < len(x["_filter"]["params"]))
    prm = src["_filter"]["params"][p]
    return prm["long"], prm["short"], prm["format"]


def site_tests(key, stock, tweak, info, img, runtime, mans):
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    ok = all(img[va - compose.BASE:va - compose.BASE + 6] == jsr(syms[sym]) for va, sym in JSRS.items())
    ok &= img[CONV - compose.BASE:CONV - compose.BASE + 6] == bytes.fromhex("4ef9") + struct.pack(">I", syms["sc_conv"])
    ok &= struct.unpack_from(">I", img, KNOB - compose.BASE)[0] == syms["fl_knob"]
    ok &= all(struct.unpack_from(">I", img, a - compose.BASE)[0] == syms["sc_ptab"] for a in PTAB)
    ok &= all(img[va - compose.BASE:va - compose.BASE + 8] == bytes.fromhex("4ef9") + struct.pack(">I", syms[sym])
              + bytes.fromhex("4e71") for va, sym in RECORD_JMPS.items())
    check(ok, f"{key}: " + ", ".join(f"{va:#x} -> jsr {sym}" for va, sym in JSRS.items())
          + f", {CONV:#x} -> jmp sc_conv (the layer's), {KNOB:#x} -> fl_knob, " + " and ".join(f"{a:#x}" for a in PTAB)
          + " -> sc_ptab (the layer's), "
          + ", ".join(f"{va:#x} -> jmp {sym}" for va, sym in RECORD_JMPS.items()))
    sites = {compose.BASE + w["off"] for w in tweak["writes"]}
    without = [i for i, m in mans.items() if not m["_filter"]]
    alone = BOOT_SITES if not without else {compose.BASE + w["off"] for w in compose.compose(stock, without)[0]["writes"]}
    check(sites == alone | LAYER_SITES | OURS,
          f"{key}: {len(sites)} writes: the filter slot's {len(OURS)}, the shortcut layer's, and those of "
          + (", ".join(without) if without else "the payload's boot") + " as without the filters"
          + (f"; DIFFERENT {sorted(hex(a) for a in sites ^ (alone | LAYER_SITES | OURS))}" if sites != alone | LAYER_SITES | OURS else ""))
    at = syms["fl_data"]
    added = any(m["_machine"] for m in mans.values())
    desc_used = compose.gs.DESCN if added else g7.DESC
    filters = sorted((m["_filter"]["id"], i) for i, m in mans.items() if m["_filter"])
    n = max(len(mans[i]["_filter"]["params"]) for _f, i in filters)
    places = entry_points(info, mans)
    head = struct.unpack_from(">6I", runtime, at - compose.gs.PAY_ALONE)
    tail = struct.unpack_from(">4H3I", runtime, at + DATA["neutral"] - compose.gs.PAY_ALONE)
    check(tail == (*PART["values"]["defaults"], syms["sc_save2"], syms["sc_save1"], syms["sc_load"]),
          f"{key}: the record's neutral words {[hex(v) for v in tail[:4]]}, the layer's wrappers behind the part's")
    check(head == (len(filters) + 1, n, syms["sc_knob"], syms.get("fx_keys", 0), g7.DESC, desc_used),
          f"{key}: the data block at {at:#x}: {len(filters)} filter(s), {n} values, the lookup behind it the layer's "
          f"sc_knob, the gesture behind it {'the effect slots' + chr(39) + ' fx_keys' if 'fx_keys' in syms else 'none'}, "
          f"the descriptor tables {g7.DESC:#x} and {desc_used:#x}")
    good, shown = True, []
    for k, (fid, mid) in enumerate([(0, None)] + filters):
        e = at + DATA["entry"] + DATA["entry_size"] * k
        got = struct.unpack_from(">4I", runtime, e - compose.gs.PAY_ALONE)
        want = (fid, *(places[fid] if fid else (0, 0)))
        tag = cstr(stock, runtime, got[3])
        wtag = mans[mid]["_filter"]["short"] if mid else PART["type"]["none"]
        good &= got[:3] == want and tag == wtag
        for p in range(n):
            lp, sp, fp = struct.unpack_from(">3I", runtime, e + 16 + 12 * p - compose.gs.PAY_ALONE)
            wl, ws, wf = want_names(mans, fid, p)
            wfmt = FORMATS.get(wf, syms.get("fl_fmt_cut") if wf == "cutoff" else None)
            good &= (cstr(stock, runtime, lp), cstr(stock, runtime, sp), fp) == (wl, ws, wfmt)
        shown.append(f"{fid} {tag!r}")
    check(good, f"{key}: the table: " + ", ".join(shown) + ", each with its values' names and formatters (a value it "
                "lacks named after the first filter that has it)")
    vals, ty = PART["values"], PART["type"]
    rows = [struct.unpack_from(">14I", runtime, at + DATA["rows"] + 56 * r - compose.gs.PAY_ALONE) for r in range(5)]
    good = True
    for p in range(n):
        wl, ws, _f = want_names(mans, 0, p)
        r = rows[p]
        good &= r[:11] == (7, vals["sound_slots"][p], 0, vals["max"], vals["defaults"][p], 0, int(vals["cc"][p], 16),
                           int(vals["nrpn"][p], 16), 0, int(vals["flags"], 16), vals["sort"][p])
        good &= r[12] == int(vals["group_name"], 16) and (cstr(stock, runtime, r[11]), cstr(stock, runtime, r[13])) == (wl, ws)
    good &= not any(map(any, rows[n:4]))
    stock5 = struct.unpack_from(">14I", stock, g7.DESC + 0x38 * 5 - compose.BASE)
    r5 = rows[4]
    good &= r5[0] == 0xffffffff and r5[1:9] == (0, 0, vals["max"], 0, 0, 0xffffffff, 0xffffffff, 0)
    good &= r5[9:11] == stock5[9:11] and r5[12] == stock5[12]
    good &= (cstr(stock, runtime, r5[11]), cstr(stock, runtime, r5[13])) == (ty["long"], ty["short"])
    check(good, f"{key}: the rows fl_boot writes: descriptors 1 to {n} (group 7, k 28.., 0..127, the defaults, CC and "
                f"NRPN, the first filter's names), descriptor 5 the type ({ty['long']!r}, machine -1, k 0, no CC)")
    rest = runtime[at + DATA["cur"] - compose.gs.PAY_ALONE:at + DATA["neutral"] - compose.gs.PAY_ALONE]
    meter = runtime[at + DATA["diag"] - compose.gs.PAY_ALONE:at + DATA["start"] - compose.gs.PAY_ALONE]
    check(not any(rest) and len(rest) == DATA["neutral"] - DATA["cur"] and not any(meter),
          f"{key}: the state zero at boot, not a measuring build")
    starts = [list(struct.unpack_from(">4H", runtime, at + DATA["start"] + 8 * k - compose.gs.PAY_ALONE))
              for k in range(DATA["entries"])]
    want = [[start_word(mans, fid, p) for p in range(4)] for fid, _m in [(0, None)] + filters]
    want += [[0] * 4] * (DATA["entries"] - len(want))
    check(starts == want, f"{key}: each entry's start words (fltslot 0.8), the filter's own, else the neutral ones: "
          + "; ".join(f"{fid}: {' '.join(f'{v:#06x}' for v in w)}" for (fid, _m), w in zip([(0, None)] + filters, starts)))
    nvals = list(runtime[at + DATA["nvals"] - compose.gs.PAY_ALONE:at + DATA["nvals"] + DATA["entries"] - compose.gs.PAY_ALONE])
    want = [0] + [len(mans[mid]["_filter"]["params"]) for _f, mid in filters]
    want += [0] * (DATA["entries"] - len(want))
    check(nvals == want, f"{key}: each entry's count of values (fltslot 0.10), none 0: {nvals[:len(filters) + 1]}")
    return syms


# --- 3. the audio -----------------------------------------------------------------------------------------------------
class Reff:
    """REFF's arithmetic (tools/machines/refflt/refflt.c), per track."""

    def __init__(self):
        self.lp = [0] * TRACKS

    def reset(self, t):
        self.lp[t] = 0

    def __call__(self, x, words, t, trig):
        c, r = max(words[0], 0), max(words[1], 0)
        s, g = 1 + (c >> 12), r >> 8
        y = x[0] if trig else self.lp[t]
        out = []
        for v in x:
            d = (v >> 1) - (y >> 1)
            assert d == s32(d)
            y += d >> (s - 1)
            assert y == s32(y)
            out.append(y - (y >> 7) * g)
        self.lp[t] = y
        return out


class Samples:
    """Samples' arithmetic: SAMPLE's filter (tools/machines/sampler/src/) compiled for the host, whose C model of the
    EMAC loops One-Shot's host tests use, one state per track (smp_filter, 17 longs)."""
    _lib = []

    @classmethod
    def lib(cls):
        if not cls._lib:
            src = HERE.parent / "machines" / "sampler" / "src"
            d = pathlib.Path(tempfile.mkdtemp(prefix="smpf-host-"))
            atexit.register(shutil.rmtree, d, True)
            out = d / "smpf.so"
            cc = shutil.which("cc") or shutil.which("gcc") or "cc"
            r = subprocess.run([cc, "-O2", "-std=c99", "-fwrapv", "-Wall", "-Wextra", "-Werror", f"-I{src}", "-shared",
                                "-fPIC", "-o", str(out), str(src / "smp_filter.c"), str(src / "smp_filter_tab.c")],
                               capture_output=True, text=True)
            if r.returncode:
                sys.exit("!! the host build of smp_filter.c failed:\n" + r.stderr)
            cls._lib.append(ctypes.CDLL(str(out)))
        return cls._lib[0]

    def __init__(self):
        self.st = [(ctypes.c_int32 * 17)() for _ in range(TRACKS)]

    def reset(self, t):
        self.lib().smp_filter_reset(self.st[t])

    def __call__(self, x, words, t, trig):
        """smpf_process: the set every block (the package skips it only where it would change nothing: the proof of
        that saving), then the silent block skipped once the filter has rung out (|l|, |b| < 2^14 at half scale),
        its states cleared."""
        lib = self.lib()
        lib.smp_filter_set(self.st[t], ctypes.c_int32(words[0]), ctypes.c_int32(words[1]))
        st = self.st[t]
        if not any(x) and not (st[6] != 0 and (abs(st[0]) >= 1 << 14 or abs(st[1]) >= 1 << 14)):
            st[0] = st[1] = 0
            return list(x)
        buf = (ctypes.c_int32 * FRAMES)(*x)
        lib.smp_filter_run(self.st[t], buf)
        return list(buf)


class HostModel:
    """A Track FX's arithmetic from its host build (its manifest's "proof": {"host": {"sources", "include", "defines"}},
    notes/73 §16): the package's sources compiled for the host, called through the device contract,
    process(block, words, track, triggered) and reset(track), its states in the library's own variables. One library
    a package; the part resets a track before its first block on a filter, so the library's earlier state does not
    matter."""
    _libs = {}

    def __init__(self, mid):
        self.lib = self.build(mid)
        u = compose.load_manifest(mid)["_filter"]
        self.process, self.reset_fn = getattr(self.lib, u["process"]), getattr(self.lib, u["reset"])

    @classmethod
    def build(cls, mid):
        if mid not in cls._libs:
            src = compose.MACHINES / mid
            h = json.loads((src / "manifest.json").read_text(encoding="utf-8"))["proof"]["host"]
            d = pathlib.Path(tempfile.mkdtemp(prefix=f"{mid}-host-"))
            atexit.register(shutil.rmtree, d, True)
            out = d / f"{mid}.so"
            cc = shutil.which("cc") or shutil.which("gcc") or "cc"
            r = subprocess.run([cc, "-O2", "-std=c99", "-fwrapv", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                                *[f"-I{src / i}" for i in h.get("include", ["."])],
                                *[f"-D{k}={v}" for k, v in h.get("defines", {}).items()],
                                "-o", str(out), *[str(src / f) for f in h["sources"]]], capture_output=True, text=True)
            if r.returncode:
                sys.exit(f"!! the host build of {mid} failed:\n" + r.stderr)
            cls._libs[mid] = ctypes.CDLL(str(out))
        return cls._libs[mid]

    def reset(self, t):
        self.reset_fn(ctypes.c_uint32(t))

    def __call__(self, x, words, t, trig):
        buf = (ctypes.c_int32 * FRAMES)(*x)
        w = (ctypes.c_int16 * 4)(*words)
        self.process(buf, w, ctypes.c_uint32(t), ctypes.c_uint32(trig))
        return list(buf)


MODELS = {"refflt": Reff, "smpfilter": Samples, **{i: Reff for i in COPIES}}


def model_of(mid):
    """The model class (a factory) of filter package mid: REFF's, Samples', or the host build its manifest names."""
    if mid in MODELS:
        return MODELS[mid]
    if mid in hosted():
        return lambda: HostModel(mid)
    return None


class PartModel:
    """fltslot.c's fl_run on the stock output, with the build's filters by id: {id: model class}."""

    def __init__(self, models):
        self.order = [0] + sorted(models)
        self.f = {i: c() for i, c in models.items()}
        self.cur = [0] * TRACKS

    def __call__(self, x, words, ids, trig):
        out = []
        for t in range(TRACKS):
            i = ids[t] if ids[t] in self.f else 0
            was, tr = self.cur[t], trig >> t & 1
            blk = list(x[t])
            if i == was:
                out.append(self.f[i](blk, words[t], t, tr) if i else blk)
                continue
            self.cur[t] = i
            old = self.f[was](blk, words[t], t, tr) if was else blk
            if i:
                self.f[i].reset(t)
            new = self.f[i](blk, words[t], t, tr) if i else blk
            mixed = [((old[n] >> 6) * (FRAMES - 1 - n) + (new[n] >> 6) * (n + 1)) * 2 for n in range(FRAMES)]
            assert all(v == s32(v) for v in mixed)
            out.append(mixed)
            if was:
                self.f[was].reset(t)
        return out


class Audio:
    """One engine, the voice loop then the audio function's call of Volume + Dist (or fl_post)."""

    def __init__(self, img, runtime=None, tweak=None, entries=()):
        self.e = TC.engine(img, runtime, tweak)
        uc = self.e.uc
        uc.mem_map(0x40800000, 0x01800000)                  # the OS's BSS
        for t in range(TRACKS):
            self.e.machine_defaults(t, t)
            self.e.set(t, note=48 + 3 * t, decay=90)
            self.setw(t, 19, 0x4800)                        # Volume + Dist
        self.seen, self.instr, self.counting = [], 0, None
        for va in entries:                                  # the filters' entries: the EMAC as they find it
            uc.hook_add(UC_HOOK_CODE, self._entry, begin=va, end=va)

    def _entry(self, uc, addr, size, ud):
        self.seen.append((self.e.emac.macsr, tuple(self.e.emac.acc)))

    def count(self, ranges):
        def hk(uc, a, s, u):
            self.instr += 1
        for lo, hi in ranges:
            self.e.uc.hook_add(UC_HOOK_CODE, hk, begin=lo, end=hi - 1)

    def setw(self, t, k, v):
        self.e.uc.mem_write(word_at(t, k), struct.pack(">h", v))

    def words(self, t):
        return list(struct.unpack(">4h", self.e.uc.mem_read(word_at(t, 28), 8)))

    def chosen(self, t):
        """The id fl_run reads for track t: the sound's k 32 low byte, or the copy's when there is no sound."""
        uc = self.e.uc
        snd = struct.unpack(">I", uc.mem_read(CUR_SND + 4 * t, 4))[0]
        return uc.mem_read(snd + SOUND_K32 + 1, 1)[0] if snd else uc.mem_read(TARGETS + 66 * t + 65, 1)[0]

    def sound(self, t, k32=None, copy=None):
        """Track t's note plays the test's sound t with k32 (None: no sound), and the copy holds copy."""
        uc = self.e.uc
        if k32 is None:
            uc.mem_write(CUR_SND + 4 * t, struct.pack(">I", 0))
        else:
            uc.mem_write(SNDS + 0x100 * t + SOUND_K32, struct.pack(">H", k32))
            uc.mem_write(CUR_SND + 4 * t, struct.pack(">I", SNDS + 0x100 * t))
        if copy is not None:
            uc.mem_write(TARGETS + 66 * t + 64, struct.pack(">H", copy))

    def block(self, trig):
        e, uc = self.e, self.e.uc
        e.block(trig)
        uc.mem_write(CTX + 16, struct.pack(">I", trig))
        sp0 = E.STACK - 0x300
        uc.mem_write(sp0, struct.pack(">I", 0xdeadbeef))
        regs = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A4", "A5", "A6")]
        marks = {r: 0x1111 * (i + 1) for i, r in enumerate(regs)}
        for r, v in marks.items():
            uc.reg_write(r, v)
        uc.reg_write(mk.UC_M68K_REG_A2, E.PARAMS)
        uc.reg_write(mk.UC_M68K_REG_A3, CTX)
        uc.reg_write(mk.UC_M68K_REG_A7, sp0)
        e.emac.macsr = 0x20
        e.emac.acc[:] = [0, 0, 0, 0]
        try:
            uc.emu_start(H3_FROM, H3_TO, count=3_000_000)
        except UcError as err:
            e.unmapped.append((uc.reg_read(mk.UC_M68K_REG_PC), str(err)))
        ok = uc.reg_read(mk.UC_M68K_REG_PC) == H3_TO
        ok &= all(uc.reg_read(r) == v for r, v in marks.items())
        ok &= uc.reg_read(mk.UC_M68K_REG_A2) == E.PARAMS and uc.reg_read(mk.UC_M68K_REG_A3) == CTX
        ok &= uc.reg_read(mk.UC_M68K_REG_A7) == sp0 - 4
        ok &= struct.unpack(">II", uc.mem_read(sp0 - 4, 8)) == (TRK, E.PARAMS)
        out = [list(struct.unpack(">32i", uc.mem_read(TRK + 128 * t, 128))) for t in range(TRACKS)]
        return out, ok, (e.emac.macsr, tuple(e.emac.acc))


def word_at(t, k):
    """Track t's smoothed k in the parameters the audio function passes in a2."""
    return E.PARAMS + 14 + 66 * t + 2 * k


# the scenes: block -> {track: (k32 of the sound or None, the copy's k32)}; ids are the low byte
def scenes(ids):
    a, b = ids[0], ids[-1]
    c, d = (ids[1], ids[2]) if len(ids) > 2 else (a, b)    # four in a build: the other two on two tracks
    return [
        ("every sound with id 0, an id not held, or the switches alone", 0, 24, {
            0: (0x0000, None), 1: (0x0100, None), 2: (0x0300, None), 3: (0x0007, None), 4: (None, 0x0000),
            5: (None, 0x02f0)}),
        ("sounds choosing the filters; one with no sound, its copy choosing one", 24, 64, {
            0: (a, None), 1: (0x0000, None), 2: (None, a), 3: (0x0300 | b, None), 4: (0x0007, None), 5: (b, None)}),
        ("changes: none, another filter, another sound, back", 64, 104, {
            0: (0x0000, None), 1: (a, None), 2: (None, b), 3: (0x0300 | a, None), 4: (b, None), 5: (0x0000, None)}),
        ("back again; a sound that chose an id the build lacks", 104, 140, {
            0: (a, None), 1: (c, None), 2: (0x0009, None), 3: (b, None), 4: (d, None), 5: (b, None)}),
        ("hot tracks: Volume + Dist at 127, Reso at the top, Cutoff sweeping across the centre", 140, 180, {
            0: (a, None), 1: (b, None), 2: (a, None), 3: (b, None), 4: (a, None), 5: (b, None)}),
    ]


HOT = 140                                                   # the hot scene's first block


def hot_words(t, blk):
    """The hot scene's (Cutoff, Reso) of track t in block blk: a sweep across the centre, different per track, that
    lands on the centre now and then."""
    c = int(0x4000 + 0x3e00 * math.sin(2 * math.pi * blk / (11 + 3 * t) + t))
    c = 0x4000 if blk % 9 == t else c
    return min(max(c, 0), 0x7f00), 0x7f00


TRIGS = {1: 0x3f, 30: 0x3f, 64: 0x3c, 66: 0x2a, 90: 0x15, 106: 0x3f, 120: 0x01, 141: 0x3f, 160: 0x2a}   # 64: in a change
WORDS = [(0x4000, 0x2000), (0x2000, 0x4000), (0x7f00, 0x7f00), (0x1000, 0x2000), (-0x100, 0x6000), (0x3000, -1)]


def audio_tests(key, stock, img, runtime, tweak, info, syms, mans, blocks):
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    entries = [pr for pr, _r in entry_points(info, mans).values()]
    s = Audio(stock)
    b_ = Audio(img, runtime, tweak, entries)
    for a in (s, b_):
        for t in range(TRACKS):
            a.setw(t, 28, WORDS[t][0])
            a.setw(t, 29, WORDS[t][1])
            a.setw(t, 30, 0x4000 + t)
            a.setw(t, 31, 0x4000 - t)
    model = PartModel({m["_filter"]["id"]: model_of(i) for i, m in mans.items() if m["_filter"]})
    bad, quiet, untouched, filtered, changes, emac_ok, contract, peak = [], 0, 0, 0, 0, True, True, 0
    for name, lo, hi, scene in scenes(ids):
        for t, (k32, copy) in scene.items():
            b_.sound(t, k32, 0 if copy is None else copy)
        if lo == HOT:
            for a in (s, b_):
                for t in range(TRACKS):
                    a.setw(t, 19, 0x7f00)
        good = True
        for blk in range(lo, min(hi, lo + blocks)):
            if blk % 7 == 3:                                # the words move, as p-locks and the LFO move them
                t = blk % TRACKS
                b_.setw(t, 28, (WORDS[t][0] + 0x480 * blk) % 0x7f00)
            if lo == HOT:
                for t in range(TRACKS):
                    c, r = hot_words(t, blk)
                    b_.setw(t, 28, c)
                    b_.setw(t, 29, r)
            trig = TRIGS.get(blk, 0)
            x, ok_s, emac_s = s.block(trig)
            n_seen = len(b_.seen)
            y, ok_b, emac_b = b_.block(trig)
            words = [b_.words(t) for t in range(TRACKS)]
            chosen = [b_.chosen(t) for t in range(TRACKS)]
            prev = list(model.cur)
            want = model(x, words, chosen, trig)
            peak = max(peak, max(abs(v) for row in x for v in row))
            ran = any(model.cur) or prev != model.cur
            contract &= ok_s and ok_b
            if y != want:
                good = False
                bad.append(f"block {blk}, tracks {[t for t in range(TRACKS) if y[t] != want[t]]}")
            filtered += any(model.cur)
            changes += sum(a_ != b2 for a_, b2 in zip(prev, model.cur))
            if not ran:
                quiet += 1
                untouched += y == x
            emac_ok &= emac_b == emac_s and not any(emac_b[1])
            emac_ok &= (len(b_.seen) > n_seen) == ran and all(m == 0xa0 and not any(acc) for m, acc in b_.seen[n_seen:])
        check(good, f"{key}: {name} (blocks {lo} to {min(hi, lo + blocks) - 1}): every track the model's, bit for bit"
              + (f"; DIFFERENT at {', '.join(bad[:3])}" if bad else ""))
    check(peak > 1e8 and filtered > 0 and changes > 0 and quiet > 0 and untouched == quiet,
          f"{key}: the stock tracks peak at {peak / 2 ** 31:.2f} FS; {filtered} blocks with a filter, {changes} changes "
          f"of filter; {untouched} of the {quiet} blocks without a filter or a change the stock OS's, bit for bit")
    check(emac_ok, f"{key}: each filter called with MACSR 0xa0 and the accumulators clear ({len(b_.seen)} calls); "
          "after the part, MACSR and the accumulators (clear) as the stock OS's after Volume + Dist")
    check(contract and not s.e.unmapped and not b_.e.unmapped,
          f"{key}: every block: d2-d7/a2-a6 kept, 0x80001858 and a2 left on the stack as the call replaced leaves them, "
          "no access outside memory" + (f"; {b_.e.unmapped[:2]}" if b_.e.unmapped else ""))
    cost_tests(key, img, runtime, tweak, info, syms, ids)
    filter_cost(key, img, runtime, tweak, info, mans)


def cost_tests(key, img, runtime, tweak, info, syms, ids):
    """Instructions per block in the part and the filters: every track with none, then every track with the first
    filter, after a warm-up."""
    code = [(syms["fl_post"], syms["fl_data"])]
    code += [(p["code_at"], p["code_at"] + p["code"]) for p in info["packages"] if p.get("filter_id")]
    out = {}
    for name, k32 in (("none", 0), (f"id {ids[0]} on every track", ids[0])):
        a = Audio(img, runtime, tweak)
        for t in range(TRACKS):
            a.setw(t, 28, 0x2000)
            a.sound(t, k32, 0)
        for blk in range(4):
            a.block(0x3f if blk == 1 else 0)
        a.count(code)
        counts = []
        for blk in range(8):
            n0 = a.instr
            a.block(0)
            counts.append(a.instr - n0)
        out[name] = max(counts)
    check(out["none"] < 400, f"{key}: the part costs " + "; ".join(f"{n}: {v} instructions a block" for n, v in out.items()))


COST = {}                                                   # what filter_cost counts, for build/filter-cost.json
COST_STATES = {                                             # by package: state -> the (k 28, k 29[, k 30, k 31]) of its
    "smpfilter": {"lowpass": ((0x2000, 0x5000),), "highpass": ((0x6000, 0x5000),), "centre": ((0x4000, 0x5000),),
                  "glide": ((0x3000, 0x7000), (0x5800, 0x2000)), "silent": ((0x2000, 0x5000),)}}   # blocks, in turn


def cost_states(mid, man):
    """A filter's cost states: Samples' above, else its manifest's "proof": {"cost_states": {state: [[k 28, k 29(,
    k 30, k 31)], ...]}} (notes/73 §16); "silent" plays no note."""
    if mid in COST_STATES:
        return COST_STATES[mid]
    return {k: tuple(tuple(w) for w in v) for k, v in man.get("proof", {}).get("cost_states", {}).items()}


def filter_cost(key, img, runtime, tweak, info, mans):
    """Each real filter's instructions per track and block, its own code only (the part's are cost_tests'): all six
    tracks on it, the stock machines playing, a state held for 8 blocks after 8 of warm-up (glide: the words jumping
    every block, across the centre; silent: no note played, the filter set and rung out), and the block in which the
    tracks come to it from none (its reset and first block). Against cost.emulation in its manifest, when the
    selection is the filter alone (once a run)."""
    for p in info["packages"]:
        mid = p["id"]
        states = cost_states(mid, mans[mid]) if p.get("filter_id") else {}
        if not states or mid in COST:
            continue
        code = [(p["code_at"], p["code_at"] + p["code"])]
        got = {}
        for state, words in states.items():
            a = Audio(img, runtime, tweak)
            for t in range(TRACKS):
                a.sound(t, p["filter_id"], 0)
            counts = []
            for blk in range(16):
                ws = words[blk % len(words)]
                for t in range(TRACKS):
                    for k, v in enumerate(ws):              # k 28, k 29 (and k 30, k 31 when the state names them)
                        a.setw(t, 28 + k, v)
                if blk == 8:
                    a.count(code)
                n0 = a.instr
                a.block(0x3f if blk == 1 and state != "silent" else 0)     # silent: no note at all
                if blk >= 8:
                    counts.append(a.instr - n0)
            got[state] = -(-max(counts) // TRACKS)
        a = Audio(img, runtime, tweak)
        for t in range(TRACKS):
            a.sound(t, 0, 0)
            a.setw(t, 28, 0x2000)
            a.setw(t, 29, 0x5000)
        for blk in range(8):
            a.block(0x3f if blk == 1 else 0)
        a.count(code)
        for t in range(TRACKS):
            a.sound(t, p["filter_id"], 0)
        n0 = a.instr
        a.block(0)
        got["first"] = -(-(a.instr - n0) // TRACKS)
        COST[mid] = got
        declared = {k: v for k, v in mans[mid].get("cost", {}).get("emulation", {}).items() if k in got}
        check(declared == got, f"{key}: {mid}'s cost, instructions per track and block: "
              + ", ".join(f"{k} {v}" for k, v in got.items())
              + (", as its manifest declares" if declared == got else f"; its manifest declares {declared or 'nothing'}"))


# --- 4. the boot: the descriptors and the parameter tables (T2) ------------------------------------------------------
def maps(u, nm):
    """The tables the builder made: k -> descriptor by machine (0x4005a692), CC -> descriptor by track (0x4005a8ce),
    NRPN -> descriptor (0x4005a92e)."""
    pid = {(k, m): u.call(0x4005a692, k, m) for k in range(33) for m in range(nm)}
    cc = {(t, c): u.call(0x4005a8ce, t, 0, c) for t in range(TRACKS) for c in range(128)}
    nr = {x: u.call(0x4005a92e, 0, 0, x) for x in range(0x180)}
    return pid, cc, nr


def boot_tests(key, base, img, runtime, syms, mans, nm):
    """base: (image, payload) of the build without its filters."""
    a, b = SH.UI(*base), SH.UI(img, runtime)
    a.call(BUILDER)
    b.call(syms["fl_boot"])
    check(not a.bad and not b.bad and b.sp_ok, f"{key}: the builder run through fl_boot, no access outside memory, "
                                               "the stack back")
    n = max(len(m["_filter"]["params"]) for m in mans.values() if m["_filter"])
    used = b.u32(DESC_OP)
    vals, ty = PART["values"], PART["type"]
    good = True
    for table in {g7.DESC, used}:
        rows = [struct.unpack(">14I", b.uc.mem_read(table + 0x38 * d, 0x38)) for d in range(1, 6)]
        for p in range(n):
            wl, ws, _f = want_names(mans, 0, p)
            good &= rows[p][:11] == (7, 28 + p, 0, vals["max"], vals["defaults"][p], 0, int(vals["cc"][p], 16),
                                     int(vals["nrpn"][p], 16), 0, int(vals["flags"], 16), vals["sort"][p])
            good &= (b.cstr(rows[p][11]), b.cstr(rows[p][13])) == (wl, ws)
        stock_rows = [struct.unpack(">14I", a.uc.mem_read(table + 0x38 * d, 0x38)) for d in range(1, 6)]
        good &= rows[n:4] == stock_rows[n:4]
        good &= rows[4][0] == 0xffffffff and rows[4][1:9] == (0, 0, vals["max"], 0, 0, 0xffffffff, 0xffffffff, 0)
        good &= (b.cstr(rows[4][11]), b.cstr(rows[4][13])) == (ty["long"], ty["short"])
    check(good, f"{key}: descriptors 1 to {n} and 5 in the table the OS uses ({used:#x}"
                + (f", and the stock {g7.DESC:#x}" if used != g7.DESC else "") + "): the build's rows")
    pa, ca, na = maps(a, nm)
    pb, cb, nb = maps(b, nm)
    ours = {(28 + p, m): p + 1 for p in range(n) for m in range(nm)}
    diff = {km: (pa[km], pb[km]) for km in pa if pa[km] != pb[km]}
    check(diff == {km: (0, v) for km, v in ours.items()},
          f"{key}: k 28..{27 + n} -> descriptors 1..{n} on the {nm} machines, every other k (k 0 too) as without the "
          f"filters ({len(diff)} differences)")
    want_cc = {(t, c): (0, p + 1) for t in range(TRACKS) for p, c in enumerate((74, 71)[:n])}
    diff_cc = {k: (ca[k], cb[k]) for k in ca if ca[k] != cb[k]}
    check(diff_cc == want_cc, f"{key}: CC 74 -> descriptor 1" + (", 71 -> 2" if n > 1 else "") + " on the six tracks, "
                              f"nothing else changed ({len(diff_cc)} differences)")
    want_nr = {x: (0, p + 1) for p, x in enumerate((0x94, 0x95)[:n])}
    diff_nr = {k: (na[k], nb[k]) for k in na if na[k] != nb[k]}
    check(diff_nr == want_nr, f"{key}: NRPN 1:20 -> descriptor 1" + (", 1:21 -> 2" if n > 1 else "")
                              + f", nothing else changed ({diff_nr})")
    same, seen = True, set()
    for m in range(nm):
        for u in (a, b):
            u.uc.mem_write(SH.SOUND, b"\xcc" * 100)
            u.call(NEW_SOUND, SH.SOUND, m)
        sa, sb = bytes(a.uc.mem_read(SH.SOUND, 100)), bytes(b.uc.mem_read(SH.SOUND, 100))
        same &= sa[:76] == sb[:76] and sa[76 + 2 * n:] == sb[76 + 2 * n:]
        seen.add(struct.unpack_from(f">{n}H", sb, 76))
    check(same and seen == {tuple(vals["defaults"][:n])},
          f"{key}: a new sound (0x400618f2) on the {nm} machines: k 28..{27 + n} at {[hex(v) for v in vals['defaults'][:n]]}"
          ", everything else as without the filters")


# --- 5. the knob lookup (T2) ------------------------------------------------------------------------------------------
def lookup(u, knob_, held, trig=0, k32=0, track=0xffffffff):
    """The lookup through the vtable entry (fl_knob, then the layer's, then the stock one, stubbed): (descriptor,
    whether the stock lookup was called once with the same arguments, the stack came back and memory stayed in
    bounds)."""
    hooks = SH.project(u, 0, 0, k32)
    hooks.update({SH.LOOKUP: ("lookup", SH.STOCK_ANSWER), SH.TRACK_MACHINE: ("machine", 0), SH.TRIG_HELD: ("trig", trig)})
    u.hooks = hooks
    u.keys(held)
    u.calls.clear()
    d = u.call(u.u32(KNOB), SH.VIEW, knob_, 0, track)
    looked = [a[:4] for nm_, a in u.calls if nm_ == "lookup"]
    return d, looked == [(SH.VIEW, knob_, 0, track)] and u.sp_ok and not u.bad


def nvals_of(mans):
    """Each filter id's count of values (fltslot 0.10); an id the build lacks, and none, have none."""
    return {m["_filter"]["id"]: len(m["_filter"]["params"]) for m in mans.values() if m["_filter"]}


def type_row(u, used):
    """Descriptor 5's long name in both tables (a set: one name when they agree)."""
    return {u.cstr(u.u32(t + 0x38 * 5 + 0x2c)) for t in {g7.DESC, used}}


def knob_tests(key, img, runtime, syms, mans):
    u = SH.UI(img, runtime)
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    tags = {m["_filter"]["id"]: m["_filter"]["short"] for m in mans.values() if m["_filter"]}
    nv = nvals_of(mans)
    n = max(nv.values())
    added = any(m["_machine"] for m in mans.values())
    used = compose.gs.DESCN if added else g7.DESC
    na_at = syms["fl_data"] + DATA["na"]
    R, F, T_, L, M = SH.RETRIG, SH.FUNC, SH.TRACK, SH.LFO, SH.MACHINES
    got, want, fwd = {}, {}, True
    for k32 in [0, 7] + ids:                             # none, an id the build lacks, each filter
        fid = k32 if k32 in ids else 0
        for held in ((), (R,), (R, F), (R, T_), (R, L), (R, M), (F,), (L,), (M,)):
            for trig in (0, 1):
                for k in range(16):
                    got[k32, held, trig, k], ok = lookup(u, k, held, trig, k32)
                    fwd &= ok
                    w = SH.STOCK_ANSWER
                    if R in held and 4 <= k <= 7:
                        w = [2, 3, 0, 1][k - 4] + 1 if [2, 3, 0, 1][k - 4] < nv.get(fid, 0) else 5
                    elif R in held and k == 2 and not trig and not set(held) & {F, T_, L}:
                        w = 5
                    want[k32, held, trig, k] = w
    bad = [(k32, h, t, k, g, want[k32, h, t, k]) for (k32, h, t, k), g in got.items() if g != want[k32, h, t, k]]
    check(not bad, f"{key}: RETRIG + SWEEP / CONTOUR / COLOR / SHAPE -> descriptors 1..4 when the selected track's "
          f"filter has the value ({', '.join(f'{tags[i]} {nv[i]}' for i in ids)}), else 5, display only (none, an id "
          "the build lacks, a value the filter lacks; fltslot 0.10), also with FUNC, TRACK, LFO, MACHINES or a trig "
          "held; RETRIG + PITCH -> 5 alone (or with MACHINES), the stock answer with FUNC, TRACK, LFO or a trig; every "
          "other knob and everything without RETRIG the stock answer" + (f"; DIFFERENT {bad[:4]}" if bad else ""))
    check(fwd, f"{key}: the stock lookup called once, with the same arguments, each time; the stack back")
    wrong, shown = [], []
    for k32 in [0, 7] + ids + [0x0300 | ids[-1]]:
        fid = k32 & 0xff if k32 & 0xff in ids else 0
        for p in range(4):
            for q in range(n):
                u.uc.mem_write(UI_OBJ + 100 * (q + 1) + 0x2c, struct.pack(">I", 0xdeadbeef))
            u.uc.mem_write(UI_OBJ + 500 + 0x2c, struct.pack(">I", 0xdeadbeef))
            d, _ok = lookup(u, [6, 7, 4, 5][p], (R,), 0, k32)
            for q in range(n):                           # every value named after the selected track's filter's entry
                wl, ws, wf = want_names(mans, fid, q)
                wfmt = FORMATS.get(wf, syms.get("fl_fmt_cut") if wf == "cutoff" else None)
                for table in {g7.DESC, used}:
                    row = struct.unpack(">14I", u.uc.mem_read(table + 0x38 * (q + 1), 0x38))
                    if (u.cstr(row[11]), u.cstr(row[13])) != (wl, ws):
                        wrong.append((hex(k32), p, f"value {q} named {u.cstr(row[11])!r}/{u.cstr(row[13])!r}"))
                if u.u32(UI_OBJ + 100 * (q + 1) + 0x20) != wfmt or u.u32(UI_OBJ + 100 * (q + 1) + 0x2c) != 0:
                    wrong.append((hex(k32), p, f"value {q}'s object"))
            # na is read only on descriptor 5 and set by each answer of 5: after a value's answer it may hold the last
            # popup's, so it is checked on 5 alone
            if p < nv.get(fid, 0):
                if d != p + 1:
                    wrong.append((hex(k32), p, f"descriptor {d}"))
            else:                                        # the popup that changes nothing: Track FX / OFF, CRU / ---
                name = tags[fid] if fid else PART["type"]["long"]
                if d != 5 or u.uc.mem_read(na_at, 1)[0] != 1 or type_row(u, used) != {name}:
                    wrong.append((hex(k32), p, f"descriptor {d}, na {u.uc.mem_read(na_at, 1)[0]}, {type_row(u, used)}"))
                if u.u32(UI_OBJ + 500 + 0x20) != syms["fl_fmt_type"] or u.u32(UI_OBJ + 500 + 0x2c) != 0:
                    wrong.append((hex(k32), p, "descriptor 5's object"))
        shown.append(f"k 32 {k32:#06x}: " + " / ".join(
            want_names(mans, fid, p)[0] if p < nv.get(fid, 0) else (tags[fid] if fid else PART["type"]["long"])
            for p in range(4)))
    check(not wrong, f"{key}: the values named after the selected track's filter in both tables and the interface "
                     "objects (formatter, no Error picture); a knob without a value: descriptor 5 under the filter's "
                     "tag, or Track FX for none, with the type's formatter: " + "; ".join(shown)
                     + (f"; WRONG {wrong[:4]}" if wrong else ""))
    ca, names_kept = True, True
    for k32 in [0, ids[0]]:
        fid = k32 if k32 in ids else 0
        for p in range(4):
            before = [bytes(u.uc.mem_read(t + 0x38, 0x38 * 5)) for t in {g7.DESC, used}]
            for t in range(6):
                d, ok = lookup(u, [6, 7, 4, 5][p], (R, T_), 0, k32, t)
                ca &= ok and d == (p + 1 if p < n else SH.STOCK_ANSWER)
            names_kept &= [bytes(u.uc.mem_read(t + 0x38, 0x38 * 5)) for t in {g7.DESC, used}] == before
    check(ca and names_kept, f"{key}: Control All's lookups of each track (0..5): the value's descriptor whatever the "
                             "track's filter, the stock answer past the build's values; the names left as they were")
    u.uc.mem_write(UI_OBJ + 100 + 0x10, struct.pack(">I", 0x93f00000))
    u.uc.mem_write(UI_OBJ + 500 + 0x2c, struct.pack(">I", 0xdeadbeef))
    lookup(u, 4, (R,), 0, 0)                             # a knob without a value first: na set
    for t in {g7.DESC, used}:                            # and another name on the row, which the type puts back
        u.uc.mem_write(t + 0x38 * 5 + 0x2c, bytes(u.uc.mem_read(t + 0x38 + 0x2c, 4)))
    d, _ok = lookup(u, 2, (R,), 0, ids[0])
    check(d == 5 and u.u32(UI_OBJ + 500 + 0x10) == 0x93f00000 and u.u32(UI_OBJ + 500 + 0x20) == syms["fl_fmt_type"]
          and u.u32(UI_OBJ + 500 + 0x2c) == 0 and u.uc.mem_read(na_at, 1)[0] == 0
          and type_row(u, used) == {PART["type"]["long"]},
          f"{key}: RETRIG + PITCH: descriptor 5's object with the type's formatter, descriptor 1's steps, no Error "
          f"picture, under {PART['type']['long']!r} again and not a knob without a value")


# --- 5b. LFO + a knob (since fltslot 0.4) ----------------------------------------------------------------------------
LFO_SET, SOUND_OBJ, SOUND_VT = 0x4001eaa2, 0x93c90000, 0x93c80000


def lfo_dest(u, knob_, held):
    """ParameterPageView's LFO + knob (0x4001eaa2) on the selected track's sound (a stub object whose set and get are
    hooked): the value it sets the LFO's destination (descriptor 32) to, or None; whether the stack came back and
    memory stayed in bounds; the lists it freed."""
    u.keys(held)
    u.calls.clear()
    u.call(LFO_SET, SH.VIEW, knob_, 0)
    sets = [a for n, a in u.calls if n == "set"]
    freed = [a[0] for n, a in u.calls if n == "delete"]
    return (sets[0][2] if sets and sets[0][1] == 0x20 else None), u.sp_ok and not u.bad, freed


def lfo_tests(key, base, img, runtime, syms, mans):
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    nv = nvals_of(mans)
    R, F, T_ = SH.RETRIG, SH.FUNC, SH.TRACK
    got = {}
    ok = True
    for name, (img_, pay) in (("without", base), ("with", (img, runtime))):
        u = SH.UI(img_, pay)
        u.call(syms["fl_boot"] if name == "with" else BUILDER)     # the boot: the rows the destination's k comes from
        t7.fill_records(u)
        u.uc.mem_write(SOUND_OBJ, struct.pack(">I", SOUND_VT))
        u.uc.mem_write(SOUND_VT + 24, struct.pack(">II", 0x93c81000, 0x93c81100))
        for k32 in [0] + ids:                            # the selected track's filter, as the part finds it
            pj = SH.project(u, 0, 0, k32)
            u.hooks = {0x400802e0: ("new", 0), 0x400802ec: ("delete", 0), 0x400cf866: ("project", SH.PROJ),
                       0x4000eb90: ("tracks", SH.PROJ), 0x40012412: ("active", 0), 0x4000eb9c: ("tracks2", SH.PROJ),
                       0x400097f0: ("sound", SOUND_OBJ), 0x400cf9a8: ("ui", 0x93a20000), 0x4006b978: ("trig", 0),
                       0x93c81000: ("set", 0), 0x93c81100: ("get", 0), SH.SOUND_FN: ("track_sound", pj[SH.SOUND_FN][1])}
            for held in ((), (R,), (R, F), (R, T_), (F,)):
                for k in range(12):
                    got[name, k32, held, k] = lfo_dest(u, k, held)
                    ok &= got[name, k32, held, k][1]
    bad, kept = [], 0
    for (name, k32, held, k), (v, _g, freed) in got.items():
        if name != "with":
            continue
        w, wfreed = got["without", k32, held, k][0], got["without", k32, held, k][2]
        if R in held and 2 <= k <= 5:
            p = [2, 3, 0, 1][k - 2]
            if p < nv.get(k32, 0):
                w = (28 + p) << 8
            else:                                        # a value the track's filter lacks: the destination stays
                w, wfreed, kept = None, wfreed[:1], kept + 1
        if v != w or freed != wfreed:
            bad.append((k32, held, k, v, w, freed, wfreed))
    stock = [got["without", 0, (), k][0] for k in range(12)]
    check(ok and not bad and all(r[0] is not None for (nm, *_x), r in got.items() if nm == "without"),
          f"{key}: LFO + a knob through the OS's own path: with RETRIG, SWEEP / CONTOUR / COLOR / SHAPE -> k 28 .. 31 "
          "when the selected track's filter has the value, also with FUNC or TRACK; a value it lacks, or none: no "
          f"destination set, the knob list freed as the routine frees it, the routine's end ({kept} cases, fltslot "
          "0.10); every other knob and everything without RETRIG as without the filters "
          f"(the stock destinations k {[v >> 8 for v in stock]})" + (f"; DIFFERENT {bad[:4]}" if bad else ""))


# --- 6. the formatters (T2) -------------------------------------------------------------------------------------------
BUF = 0x93e00000


def formatter_tests(key, img, runtime, syms, mans):
    u = SH.UI(img, runtime)
    steps = []
    for v in range(128):
        u.uc.mem_write(BUF, b"\xee" * 16)
        u.call(syms["fl_fmt_cut"], 0, v << 8, BUF)
        steps.append(u.cstr(BUF))
    check(steps == [str(v - 64) for v in range(128)]                 # as SAMPLE's smp_fmt_cutoff, since fltslot 0.6
          and all(len(x) <= 3 for x in steps) and not u.bad,
          f"{key}: Filter Cutoff's formatter over the 128 steps: {steps[0]} .. {steps[63]}, {steps[64]}, {steps[65]} .. "
          f"{steps[127]}, three characters at most")
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    tags = {m["_filter"]["id"]: m["_filter"]["short"] for m in mans.values() if m["_filter"]}
    got, want = [], []
    for k32 in [0, 7] + ids + [0x0200 | ids[0]]:
        u.hooks = SH.project(u, 0, 0, k32)
        u.uc.mem_write(BUF, b"\xee" * 16)
        u.call(syms["fl_fmt_type"], 0, 0x1234, BUF)
        got.append(u.cstr(BUF))
        want.append(tags.get(k32 & 0xff, PART["type"]["none"]))
    check(got == want and not u.bad, f"{key}: the type's formatter: {', '.join(got)} (none, an id the build lacks, the "
                                     "filters, a filter with a switch set)")
    u.uc.mem_write(syms["fl_data"] + DATA["na"], b"\x01")
    got, want = [], []
    for diag in (0, 1):                                  # a knob without a value: the same in a measuring build
        u.uc.mem_write(syms["fl_data"] + DATA["diag"], bytes([diag]))
        for k32 in [0, 7] + ids + [0x0200 | ids[0]]:
            u.hooks = SH.project(u, 0, 0, k32)
            u.uc.mem_write(BUF, b"\xee" * 16)
            u.call(syms["fl_fmt_type"], 0, 0x1234, BUF)
            got.append(u.cstr(BUF))
            want.append("---" if k32 & 0xff in tags else PART["type"]["none"])
    u.uc.mem_write(syms["fl_data"] + DATA["diag"], b"\x00\x00")
    check(got == want and not u.bad, f"{key}: the type's formatter on a knob without a value (fltslot 0.10): "
                                     f"{', '.join(got[:len(got) // 2])} (none, an id the build lacks, the filters, a "
                                     "filter with a switch set), the same in a measuring build")


# --- 7. the type (T2) -------------------------------------------------------------------------------------------------
FRAME = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5")]


class Turn:
    """fl_keys, called as the encoder handler calls it at 0x4001f886, with the handler's frame, the held keys in the
    OS's key bitmap and the selected track's sound (SH.project)."""

    def __init__(self, img, runtime, syms, k32=0):
        u = self.u = SH.UI(img, runtime)
        u.uc.mem_map(0xfc070000, 0x1000)
        u.uc.mem_map(0x80000000, 0x10000)                   # SRAM: the notes' sounds and the targets (fltslot 0.8)
        u.hooks = SH.project(u, 0, 0, k32)
        self.syms, self.exits = syms, 0

        def hk(uc, addr, size, ud):
            self.exits += 1
        u.uc.hook_add(UC_HOOK_CODE, hk, begin=HANDLER_END, end=HANDLER_END)

    def k32(self):
        return struct.unpack(">H", self.u.uc.mem_read(SH.SOUND + SOUND_K32, 2))[0]

    def __call__(self, desc, step, now=0, keys=()):
        uc, u = self.u.uc, self.u
        uc.mem_write(TIMER, struct.pack(">I", now & 0xffffffff))
        u.keys([k for k in keys if k != 3])
        u.hold(3, 3 in keys)                             # PATTERN
        fp, old_fp = 0x93000100, 0x93000400
        saved = [0x6b6b0000 + i for i in range(len(FRAME))]
        uc.mem_write(fp - 84, struct.pack(">10I", *saved))
        uc.mem_write(fp + STEP_AT, struct.pack(">h", step))
        uc.mem_write(fp, struct.pack(">II", old_fp, t7.STOP))
        sp = t7.STACK - 0x400
        uc.mem_write(sp, struct.pack(">II", t7.STOP, 0x5a5a5a5a))
        uc.reg_write(mk.UC_M68K_REG_A7, sp)
        uc.reg_write(mk.UC_M68K_REG_A6, fp)
        live = [0x3c3c0000 + i for i in range(len(FRAME))]
        live[FRAME.index(mk.UC_M68K_REG_D3)] = desc
        for r, v in zip(FRAME, live):
            uc.reg_write(r, v)
        before = self.exits
        u.bad.clear()
        uc.emu_start(self.syms["fl_keys"], t7.STOP, count=300_000)
        taken = self.exits > before
        d0 = uc.reg_read(mk.UC_M68K_REG_D0)
        regs = [uc.reg_read(r) for r in FRAME]
        a6, a7 = uc.reg_read(mk.UC_M68K_REG_A6), uc.reg_read(mk.UC_M68K_REG_A7)
        if taken:
            ok = d0 & 0xff == 0 and regs == saved and a6 == old_fp and a7 == fp + 8
        else:
            ok = regs == live and a6 == fp and a7 == sp and struct.unpack(">I", uc.mem_read(sp, 4))[0] == 2
        return taken, d0, ok and not u.bad


def type_tests(key, img, runtime, syms, mans):
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    order = [0] + ids
    pause = 54067200
    t = Turn(img, runtime, syms, 0x0300)
    log, ok, now = [], True, 1000
    seq = [1] * 3 + [1] + [1] * 4 * len(ids) + [1] * 4 + [-1] * 4 + [-1] * 2 + [1] + [-1] * 4
    for st in seq:                                       # up to the end and past it, down, a change of direction
        now += 1000
        taken, _d0, good = t(5, st, now)
        ok &= taken and good
        log.append(t.k32())
    model, acc, last = [], 0, None
    cur = 0
    for st in seq:
        d = 1 if st > 0 else 2
        if d != last:
            acc = 0
        last = d
        acc += 1
        if acc == 4:
            acc = 0
            i = order.index(cur)
            if d == 1 and i + 1 < len(order):
                cur = order[i + 1]
            elif d == 2 and i > 0:
                cur = order[i - 1]
        model.append(0x0300 | cur)
    check(ok and log == model, f"{key}: RETRIG + PITCH on descriptor 5: the handler's end with 0 and its registers each "
                               f"turn; four detents a step through {order}, stopping at the ends, the count again "
                               f"after a change of direction, the switches kept ({[hex(v) for v in log[3::4]]})")
    t2 = Turn(img, runtime, syms, 0x0007)
    for k in range(3):
        t2(5, 1, 10 + k)
    t2(5, 1, 10 + 3 + pause + 1)                         # 0.4 s later: the count starts again
    a = t2.k32()
    for k in range(3):
        t2(5, 1, 2 * pause + k)
    check(a == 0x0007 and t2.k32() == ids[0], f"{key}: a pause of 0.4 s starts the count again; an id the build lacks "
                                              f"(7) counts as none, the next step the first filter ({t2.k32():#06x})")
    good, seen = True, []
    for k32 in (0, ids[0]):                              # a knob without a value (fltslot 0.10): the popup only
        tn = Turn(img, runtime, syms, k32)
        tn.u.uc.mem_write(syms["fl_data"] + DATA["na"], b"\x01")
        for k in range(12):
            taken, _d0, g = tn(5, 1 if k < 8 else -1, 100 + k)
            good &= taken and g
        good &= tn.k32() == k32
        seen.append(f"{tn.k32():#06x}")
    check(good, f"{key}: descriptor 5 on a knob without a value: the handler's end with 0 and its registers each turn, "
                f"no step after twelve detents both ways, the sound untouched ({', '.join(seen)})")
    t3 = Turn(img, runtime, syms, 0)
    res = [t3(37, 1, 5, keys=()), t3(37, 1, 6, keys=(SH.TRACK,)), t3(1, -1, 7, keys=(SH.RETRIG,))]
    good = all(not tk and g for tk, _d, g in res) and [d & 1 for _tk, d, _g in res] == [0, 1, 0] and t3.k32() == 0
    check(good, f"{key}: another descriptor: isKeyHeld(2) as the handler asked (TRACK not held, held), the caller's "
                "registers, the pea's argument on the stack, the sound untouched")
    if "fx_keys" in syms:
        tk, _d, g = t3(37, 1, 8, keys=(3,))
        check(tk and g, f"{key}: PATTERN + Delay Time reaches the effect slots' fx_keys behind fl_keys, which takes it")
    start_tests(key, img, runtime, syms, mans)


def start_word(mans, fid, p):
    """The word value p starts at when a sound steps to filter fid (fltslot 0.8): the filter's params[p].start, else
    the value's neutral word."""
    m = next((x for x in mans.values() if x["_filter"] and x["_filter"]["id"] == fid), None)
    prm = m["_filter"]["params"] if m else []
    return prm[p].get("start", PART["values"]["defaults"][p]) if p < len(prm) else PART["values"]["defaults"][p]


def start_tests(key, img, runtime, syms, mans):
    """A step of the type gives the sound the new filter's start words (fltslot 0.8): from none only those that differ
    from the neutral ones, from a filter all of them, none of them on a step to none; into the sound's k 28.. and into
    the targets (0x800015ae + 66 t + 56..) of the tracks whose note plays that sound, the others untouched."""
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    order = [0] + ids
    n = max(len(m["_filter"]["params"]) for m in mans.values() if m["_filter"])
    neutral = PART["values"]["defaults"]
    t = Turn(img, runtime, syms, 0)
    uc = t.u.uc
    vals = [0x2100, 0x1234, 0x4100, 0x3f00]                 # the sound's k 28..31 before, none of them a start word
    uc.mem_write(SH.SOUND + 76, struct.pack(">4H", *vals))
    other = SH.SOUND + 0x200                                # another sound (a sound lock) on track 1
    plays = {0: SH.SOUND, 1: other, 3: SH.SOUND}
    for tr in range(TRACKS):
        uc.mem_write(CUR_SND + 4 * tr, struct.pack(">I", plays.get(tr, 0)))
        uc.mem_write(TARGETS + 66 * tr + 56, struct.pack(">4H", *[0x7700 + tr] * 4))
    want_snd, want_tgt = list(vals), {tr: [0x7700 + tr] * 4 for tr in range(TRACKS)}
    good, cur, shown, now, acc = True, 0, [], 1000, 0
    for d in [1] * 4 * len(ids) + [-1] * 4 * len(ids):      # up through every filter, then down to none: four detents
        now += 1000                                         # a step, the direction changing after a whole step
        taken, _d0, ok = t(5, d, now)
        good &= taken and ok
        acc += 1
        if acc < 4:
            continue
        acc = 0
        i = order.index(cur)
        j = i + 1 if d > 0 else i - 1
        for p in range(n if j else 0):
            w = start_word(mans, order[j], p)
            if i == 0 and w == neutral[p]:
                continue
            want_snd[p] = w
            for tr, sn in plays.items():
                if sn == SH.SOUND:
                    want_tgt[tr][p] = w
        cur = order[j]
        got = list(struct.unpack(">4H", uc.mem_read(SH.SOUND + 76, 8)))
        tgt = {tr: list(struct.unpack(">4H", uc.mem_read(TARGETS + 66 * tr + 56, 8))) for tr in range(TRACKS)}
        good &= got == want_snd and tgt == want_tgt and t.k32() & 0xff == cur
        shown.append(f"{cur}: {' '.join(f'{v:#06x}' for v in got[:n])}")
    check(good, f"{key}: a step of the type gives the sound the new filter's start words (from none those that differ "
                f"from the neutral ones, from a filter all, to none none), in the sound and in the targets of tracks 0 "
                f"and 3 that play it, not track 1's sound lock nor the others: " + "; ".join(shown))


# --- 8. the pattern's p-locks (T2, notes/47 §4.3) ----------------------------------------------------------------------
RAM, FILE = 0x91300000, 0x91400000


def plock_tests(key, base, img, runtime):
    def ram_init(u):
        u.uc.mem_write(RAM, (b"\xff\xff" * (34 * 64) + b"\x00" * 33) * 6)

    def lock(u, t, step, k, v):
        u.uc.mem_write(RAM + t * 4385 + step * 68 + 2 * k, struct.pack(">h", v))
        u.uc.mem_write(RAM + t * 4385 + 4352 + k, b"\x01")

    def dump(u):
        out = {}
        for t in range(6):
            blk = bytes(u.uc.mem_read(RAM + t * 4385, 4385))
            for k in range(33):
                if blk[4352 + k]:
                    out[t, k] = {s_: struct.unpack_from(">h", blk, s_ * 68 + 2 * k)[0] for s_ in range(64)
                                 if struct.unpack_from(">h", blk, s_ * 68 + 2 * k)[0] != -1}
        return out

    locks = [(2, 5, 28, 0x1234), (2, 7, 29, 0x2000), (2, 9, 23, 0x0800), (2, 1, 1, 0x3000), (3, 4, 31, 0x0400),
             (3, 6, 30, 0x0500), (1, 3, 13, 0x4400), (0, 0, 24, 0x7f00), (5, 63, 27, 0x0100), (4, 11, 32, 0x0e01)]
    res = {}
    for name, (img_, pay) in (("without", base), ("with", (img, runtime))):
        u = SH.UI(img_, pay)
        ram_init(u)
        for lk in locks:
            lock(u, *lk)
        before = dump(u)
        u.uc.mem_write(FILE, b"\x00" * 10400)
        u.call(0x4005b95c, FILE, RAM, 0)
        ram_init(u)
        u.call(0x4005b766, RAM, FILE)
        after = dump(u)
        ram_init(u)
        lock(u, 2, 1, 1, 0x3000)
        u.uc.mem_write(FILE, b"\x00" * 10400)
        u.call(0x4005b95c, FILE, RAM, 0)
        lock(u, 2, 5, 28, 0x1234)
        u.call(0x4005ba90, FILE, RAM, 0, 28, 2)
        ram_init(u)
        u.call(0x4005b766, RAM, FILE)
        res[name] = (before, after, dump(u), not u.bad)
    before, after, inc, nobad = res["with"]
    check(after == before and nobad, f"{key}: a pattern saved and loaded: every p-lock back on its parameter (k 1, 13, "
                                     "23, 24, 27, 28..31, and k 32 through the shortcut layer's row 18)")
    sb, sa, _inc, _ = res["without"]
    lost = sorted(k for k in sb if sa.get(k) != sb[k])
    check(bool(lost), f"{key}: (on the stock OS these were lost or landed on other parameters: {lost})")
    check(inc == {(2, 1): {1: 0x3000}, (2, 28): {5: 0x1234}},
          f"{key}: one p-lock updated (0x4005ba90, k 28): back on k 28, LFO Speed's alone")
    files = []
    for img_, pay in (base, (img, runtime)):
        u = SH.UI(img_, pay)
        ram_init(u)
        for t_, s_, k, v in locks:
            if k < 23:
                lock(u, t_, s_, k, v)
        u.uc.mem_write(FILE, b"\x00" * 10400)
        u.call(0x4005b95c, FILE, RAM, 0)
        files.append(bytes(u.uc.mem_read(FILE, 80 * 130)))
    check(files[0] == files[1], f"{key}: p-locks of the stock parameters only: the file byte for byte as on the stock "
                                "OS")


# --- 9. a machine change (T2) -----------------------------------------------------------------------------------------
VALUES = (0x0100, 0x2000, 0x1234, 0x7f00)


def change_tests(key, img, runtime, syms):
    u = SH.UI(img, runtime)
    u.call(syms["fl_boot"])
    t7.fill_records(u)
    obj, snd = t7.fake_track(u, 0)
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
    check(mach == 1 and kept == VALUES and not u.bad,
          f"{key}: a real machine change KICK -> SNARE (0x40014072) after the boot's tables: k 28..31 kept "
          f"{[hex(x) for x in kept]}")


# --- 11. the record (T3) ---------------------------------------------------------------------------------------------
SAVE2, SAVE1, LOAD = 0x4005afa0, 0x4005b054, 0x4005aecc
OURS_REC = set(range(84, 92)) | {64, 65, 36, 37, 94}       # record bytes the part writes
OURS_SND = {20, 21, 28, 29} | set(range(76, 86)) | set(range(88, 92))   # k 0, k 4, k 28..32, the velocity's dest


def load_into(u, rec):
    u.uc.mem_write(SH.RECORD, rec)
    u.uc.mem_write(SH.SOUND, b"\xcc" * 100)
    r = u.call(LOAD, SH.SOUND, SH.RECORD) & 0xff
    return r, bytes(u.uc.mem_read(SH.SOUND, 100))


def record_tests(key, stock, base, img, runtime, mans):
    rng = np.random.default_rng(71)
    ids = sorted(m["_filter"]["id"] for m in mans.values() if m["_filter"])
    n = max(len(m["_filter"]["params"]) for m in mans.values() if m["_filter"])
    neutral = PART["values"]["defaults"]
    smp = next((6 + i for i, m in enumerate(m for m in mans.values() if m["_machine"]) if m["id"] == "sampler"), None)
    a, b, o = SH.UI(*base), SH.UI(img, runtime), SH.UI(stock)
    words = (0x1234, 0x5600, 0x2a00, 0x7100)
    for fn, ver in ((SAVE2, 2), (SAVE1, 1)):
        snd = bytearray(SH.sound_bytes(rng, 0, words))
        k32 = 0xfc00 | 0x0300 | ids[-1]                      # stray bits 10-15 in memory: the save drops them
        struct.pack_into(">H", snd, 84, k32)
        struct.pack_into(">H", snd, 28, 28 << 8)             # LFO -> the first value
        struct.pack_into(">I", snd, 88, 28 + min(1, n - 1))  # velocity -> the second (or the first)
        ra, reca, _la, backa = SH.save_load(a, bytes(snd), fn)
        rb, recb, lb, backb = SH.save_load(b, bytes(snd), fn)
        diff = {i for i in range(100) if reca[i] != recb[i]}
        slots = [struct.unpack_from(">H", recb, 84 + 2 * p)[0] for p in range(4)]
        want_slots = [words[p] ^ neutral[p] if p < n else 0 for p in range(4)]
        s18 = struct.unpack_from(">H", recb, 64)[0]
        want18 = (k32 & 0x03ff) | 1 << 10 | (min(1, n - 1) + 1) << 13
        check(ra == rb == 1 and diff <= OURS_REC and slots == want_slots and s18 == want18
              and recb[36:38] == bytes(2) and recb[94] == 0 and b.sp_ok and not b.bad,
              f"{key}: save version {ver}: the record as without the filters but for slots 28..31 "
              f"{[hex(v) for v in slots]} (XOR the neutral words, undeclared 0), slot 18 {s18:#06x} (k 32's low bits, "
              "the destinations in bits 10-15) and none at slot 4 and +94")
        if ver != 2:
            continue
        kw = [struct.unpack_from(">H", backb, 76 + 2 * p)[0] for p in range(4)]
        dests = (struct.unpack_from(">H", backb, 28)[0], struct.unpack_from(">I", backb, 88)[0])
        same = {i for i in range(100) if backa[i] != backb[i]} <= OURS_SND
        check(lb == 1 and kw == [words[p] if p < n else neutral[p] for p in range(4)]
              and struct.unpack_from(">H", backb, 84)[0] == k32 & 0x03ff and dests == (28 << 8, 28 + min(1, n - 1))
              and same and backb[20:22] == bytes(2),
              f"{key}: loaded: the values {[hex(v) for v in kw]} (an undeclared one at its neutral word), k 32 "
              f"{struct.unpack_from('>H', backb, 84)[0]:#06x}, LFO -> k {dests[0] >> 8}, velocity -> k {dests[1]}, "
              "everything else as without the filters")
        r_o, back_o = load_into(o, recb)                     # the official OS reads a filter build's record
        _r, rec_o, _l, back_oo = SH.save_load(o, bytes(snd), SAVE2)
        diff_o = {i for i in range(100) if back_o[i] != back_oo[i]}
        check(r_o == 1 and diff_o <= {20, 21, 28, 29, 88, 89, 90, 91} and back_o[28] == 0
              and struct.unpack_from(">I", back_o, 88)[0] == 0,
              f"{key}: the official OS loads that record with no destination (its own record of the sound gave them "
              f"k {back_oo[28]} and {struct.unpack_from('>I', back_oo, 88)[0]}, other parameters) and slot 18 on k 0; "
              "everything else as its own")
        r_n, back_n = load_into(b, rec_o)                    # and a filter build reads the official OS's record
        _r, back_s = load_into(o, rec_o)
        diff_n = {i for i in range(100) if back_n[i] != back_s[i]}
        kn = [struct.unpack_from(">H", back_n, 76 + 2 * p)[0] for p in range(4)]
        check(r_n == 1 and diff_n <= set(range(76, 86)) and kn == list(neutral)
              and struct.unpack_from(">H", back_n, 84)[0] == 0,
              f"{key}: a record of the official OS loads the neutral words {[hex(v) for v in kn]}, no filter (k 32 "
              "0), everything else as the official OS loads it")
    if smp is not None:
        snd = bytearray(SH.sound_bytes(rng, smp, words))
        snd[70:76] = bytes.fromhex("0123456789ab")           # k 25..27: the sample's key
        struct.pack_into(">H", snd, 84, 0x0300 | ids[0])
        _r, rec, lb, back = SH.save_load(b, bytes(snd), SAVE2)
        check(lb == 1 and back[70:76] == snd[70:76] and back[84:86] == snd[84:86]
              and [struct.unpack_from(">H", back, 76 + 2 * p)[0] for p in range(n)] == list(words[:n]),
              f"{key}: a SAMPLE sound: its key (k 25..27) through SAMPLE's wrapper behind the layer, its switches and "
              "its filter back")


# --- 12. the load (fltslot 0.5) --------------------------------------------------------------------------------------
def load_tests(key, stock, ids, img, runtime, syms):
    u = SH.UI(img, runtime)
    at = syms["fl_data"]

    def rd(off, fmt):
        return struct.unpack(fmt, u.uc.mem_read(at + off, struct.calcsize(fmt)))[0]
    ticks = [5000] * 749 + [30000]
    for v in ticks[:-1]:
        u.call(syms["fl_measure"], v)
    mid = (rd(DATA["sum"], ">I"), rd(DATA["n"], ">H"))
    u.call(syms["fl_measure"], ticks[-1])
    got = (rd(DATA["avg_t"], ">H"), rd(DATA["peak_t"], ">H"), rd(DATA["sum"], ">I"), rd(DATA["peak"], ">I"),
           rd(DATA["n"], ">H"))
    want = ((sum(ticks) // 750) * 1000 // 90112, 30000 * 1000 // 90112, 0, 0, 0)
    check(mid == (5000 * 749, 749) and got == want and not u.bad,
          f"{key}: the load over 750 blocks: average {got[0] / 10} %, peak {got[1] / 10} % of a block, the window "
          "cleared after")
    tweak_d, _info = folder_call(ids, lambda: compose.compose(stock, ids, diag_filters=True))
    patched, _ = TC.build.apply_writes(stock, [tweak_d])
    run_d = TC.build.payload_runtime(tweak_d, stock, None)
    img_d = bytes(patched) + TC.build.payload_image(tweak_d, run_d)
    syms_d = {k: int(v, 16) for k, v in tweak_d["symbols"].items()}
    shown = {}
    for name, (im, rt, sy) in (("normal", (img, runtime, syms)), ("measuring", (img_d, run_d, syms_d))):
        w = SH.UI(im, rt)
        w.hooks = SH.project(w, 0, 0, 0)                 # the selected track's sound: no filter
        out = []
        for avg, peak in ((64, 123), (5, 999), (1000, 1500)):
            w.uc.mem_write(sy["fl_data"] + DATA["avg_t"], struct.pack(">HH", avg, peak))
            for fn, v in (("fl_fmt_cut", 0x4000), ("fl_fmt_type", 0)):
                w.uc.mem_write(BUF, b"\xee" * 16)
                w.call(sy[fn], 0, v, BUF)
                out.append(w.cstr(BUF))
        shown[name] = out
        diag = w.uc.mem_read(sy["fl_data"] + DATA["diag"], 1)[0]
        shown[name + " flag"] = diag
    check(shown["measuring"] == ["6.4", "12", "0.5", "99", "99", "99"] and shown["measuring flag"] == 1
          and shown["normal flag"] == 0 and shown["normal"][0::2] == ["0"] * 3,
          f"{key}: a measuring build shows the load (Cutoff's popup the average, the type's the peak: "
          f"{', '.join(shown['measuring'])}); this build the values ({', '.join(shown['normal'][:2])})")


def folder_call(ids, fn):
    copies = [(i, REF_IDS[i]) for i in ids if i in COPIES]
    if copies:
        with folder(copies):
            return fn()
    return fn()


# --- 10. the composer's refusals --------------------------------------------------------------------------------------
def refusal_tests(stock):
    base = json.loads((compose.MACHINES / "refflt" / "manifest.json").read_text())
    cases = [("a filter and a machine in one package", lambda m: m["uses"].append({"point": "machine"})),
             ("a filter and an effect in one package", lambda m: m["uses"].append({"point": "fx.delay", "id": 3})),
             ("id 0", lambda m: m["uses"][0].update(id=0)),
             ("id 256", lambda m: m["uses"][0].update(id=256)),
             ("its process not first in build.roots", lambda m: m["build"].update(roots=["reff_reset", "reff_process"])),
             ("its reset not in build.roots", lambda m: m["uses"][0].update(reset="reff_other")),
             ("a patch point", lambda m: m["build"].update(patch_points=[{"symbol": "x", "kind": "fx_line"}])),
             ("another use", lambda m: m["uses"].append({"point": "shortcut"})),
             ("a name of 16 characters", lambda m: m["uses"][0].update(name="A" * 16)),
             ("a type name of 4", lambda m: m["uses"][0].update(short="ABCD")),
             ("no values", lambda m: m["uses"][0].update(params=[])),
             ("five values", lambda m: m["uses"][0].update(params=m["uses"][0]["params"] * 2 + m["uses"][0]["params"][:1])),
             ("a value's name of 16", lambda m: m["uses"][0]["params"][0].update(long="A" * 16)),
             ("a value's short name of 5", lambda m: m["uses"][0]["params"][0].update(short="ABCDE")),
             ("an unknown formatter", lambda m: m["uses"][0]["params"][0].update(format="reff_nope")),
             ("two filters in one package", lambda m: m["uses"].append(dict(m["uses"][0], id=3)))]
    refused, kept = [], compose.MACHINES
    try:
        with tempfile.TemporaryDirectory() as d:
            compose.MACHINES = pathlib.Path(d)
            for name, change in cases:
                (compose.MACHINES / "refflt").mkdir(exist_ok=True)
                m = json.loads(json.dumps(base))
                change(m)
                (compose.MACHINES / "refflt" / "manifest.json").write_text(json.dumps(m))
                try:
                    compose.load_manifest("refflt")
                except SystemExit:
                    refused.append(name)
    finally:
        compose.MACHINES = kept
    check(len(refused) == len(cases), "the composer refuses a package with " + ", ".join(refused)
          + (f"; accepts {', '.join(n for n, _c in cases if n not in refused)}" if len(refused) < len(cases) else ""))
    for name, copies, ids in (("nine filters in one build", [(i, REF_IDS[i]) for i in COPIES], ["refflt", *COPIES]),
                              ("two filters with one id", [("refflt2", 255)], ["refflt", "refflt2"])):
        with folder(copies):
            try:
                compose.compose(stock, ids)
                done = True
            except SystemExit:
                done = False
        check(not done, f"the composer refuses {name}")
    for ids in (["refmachine2", "refflt"], ["chordtables", "refflt"], ["refflt", "refchord"]):
        try:
            compose.compose(stock, ids)
            done = True
        except SystemExit:
            done = False
        check(not done, f"the composer refuses {' + '.join(ids)}: a machine's value on MACHINES + a knob and a filter "
                        "(the rule R1, k 28..31 hold one meaning)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", action="append", help="one selection, ids comma-separated (repeat for several)")
    ap.add_argument("--blocks", type=int, default=40, help="blocks per scene, at most")
    ap.add_argument("--dry", action="store_true", help="the builds and their sites only, without Unicorn")
    args = ap.parse_args()
    selections = [[i.strip() for i in s.split(",") if i.strip()] for s in args.machines] if args.machines else default_selections()
    stock = T.main_os_from_syx(args.cycles)
    for ids in selections:
        key = "+".join(ids)
        copies = [(i, REF_IDS[i]) for i in ids if i in COPIES]
        with folder(copies) if copies else contextlib.nullcontext():
            mans = {i: compose.load_manifest(i) for i in ids}
        if not any(m["_filter"] for m in mans.values()):
            sys.exit(f"!! {key}: the proof needs a filter (refflt)")
        if any(m["_filter"] and not model_of(i) for i, m in mans.items()):
            sys.exit(f"!! {key}: a filter without a model: REFF and its copies, Samples, or a manifest's proof.host")
        tweak, info, img, runtime = built(stock, ids)
        print(f"\n{key}: filters " + ", ".join(f"{fid} ({i})" for fid, i in info["filters"]["filters"])
              + f"; payload {len(runtime)} bytes at {compose.gs.PAY_ALONE:#x}")
        if not args.dry:
            print("start-up")
            X.bootstrap_depack_ok(args.cycles, tweak, None) or t7.FAIL.append(f"{key}: bootstrap")
            X.boot_hook_ok(img, runtime) or t7.FAIL.append(f"{key}: boot hook")
        print("the sites and the data block")
        syms = site_tests(key, stock, tweak, info, img, runtime, mans)
        if args.dry:
            continue
        print("the audio")
        audio_tests(key, stock, img, runtime, tweak, info, syms, mans, args.blocks)
        without = [i for i, m in mans.items() if not m["_filter"]]
        base = (stock, b"") if not without else built(stock, without)[2:4]
        nm = 6 + sum(1 for m in mans.values() if m["_machine"])
        print("the boot: the descriptors and the parameter tables")
        boot_tests(key, base, img, runtime, syms, mans, nm)
        print("the knob lookup")
        knob_tests(key, img, runtime, syms, mans)
        print("LFO + a knob")
        lfo_tests(key, base, img, runtime, syms, mans)
        print("the formatters")
        formatter_tests(key, img, runtime, syms, mans)
        print("the type")
        type_tests(key, img, runtime, syms, mans)
        print("the pattern's p-locks")
        plock_tests(key, (stock, b""), img, runtime)
        print("a machine change")
        change_tests(key, img, runtime, syms)
        print("the record")
        record_tests(key, stock, base, img, runtime, mans)
        print("the load")
        load_tests(key, stock, ids, img, runtime, syms)
    if COST:
        out = HERE.parent.parent / "build" / "filter-cost.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(COST, indent=1, sort_keys=True) + "\n")
        print(f"\nthe counted costs: {out}")
    print("\nthe composer's refusals")
    refusal_tests(stock)
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
