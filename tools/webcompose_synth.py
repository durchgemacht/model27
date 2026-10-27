#!/usr/bin/env python3
"""Reference data for tools/webcompose_check.js (notes/61): what docs/flasher/composer.js must give, computed by the
Python composer, so that the page and tools/compose.py compose the same bytes.

Part 1 (B3a), no firmware needed: every package of tools/machines/ that has an object, and every part of the
builder (B4e: the shortcut layer, the dispatchers, laid out with all their roots), laid out once (relocate.layout,
relocate.bundle), and what relocate.place gives at a set of placements: the code and the variables at 4-aligned
addresses (where the composer puts the packages alone and in pairs, then random ones), the patch points at assorted
values.

Part 2 (B3b), with the official file (--cycles): the tweak compose.compose() composes for each selection of
SELECTIONS and the MAIN OS compose.build_syx() builds from it with the tweaks named on top, and what the page composes
them from: each package as compose.web_package() gives it, the committed frame.json (refused when it is not what
compose.frames() gives), the folder's tweaks reduced to what the conflicts read plus a few probes, device.json. Then
compose.fill() for 1 to 6 synthetic machines, what two packages cannot reach. The parts go with them
(compose.web_part), and the selections with REF2 bring in the shortcut layer and the dispatchers (B4e). The
declared claims of the folder's tweaks go with them too (tools/claims.py, notes/65 C2), and a few probes of claims
only: a slot and a combination of the shortcut layer, SAMPLE's formatter object in another scope, SAMPLE's k 25 on
another machine's tracks (no clash), a view (a warning, no clash).

    python3 tools/webcompose_synth.py <outdir> [--cycles model-cycles_OS1.13.syx]
        # writes <outdir>/compose.json, with --cycles also <outdir>/composed.json
"""
import argparse
import contextlib
import io
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import claims as cl  # noqa: E402
import relocate  # noqa: E402

MACHINES = HERE / "machines"
CODE_END = 0x48000000                       # no limit here: the composer checks the room, not this comparison
SELECTIONS = ((["sampler"], []), (["refmachine"], []), (["sampler", "refmachine"], []), (["refmachine", "sampler"], []),
              (["sampler", "refmachine"], ["arp", "trig-hold"]), (["refmachine2"], []), (["sampler", "refmachine2"], []),
              (["refmachine2", "sampler"], []), (["sampler", "refmachine", "refmachine2"], []),
              # notes/66 §3: REFC, the reference extension of CHORD, alone (nothing registered), with SAMPLE before
              # and after it, with REF2 (two shortcuts, machines 5 and 6), and all three
              (["refchord"], []), (["refchord", "sampler"], []), (["sampler", "refchord"], []),
              (["refchord", "refmachine2"], []), (["sampler", "refchord", "refmachine2"], []),
              # notes/66 W3: CHORD Tables, alone, and with SAMPLE before and after it (two RAM claims)
              (["chordtables"], []), (["chordtables", "sampler"], []), (["sampler", "chordtables"], []),
              # notes/68: the effects alone, in both slots, with SAMPLE before and after them, with the shortcut layer
              # and the dispatchers (REF2, SAMPLE), and with an extension of CHORD (the stock descriptor table)
              (["digidelay"], []), (["refdelay", "refreverb"], []), (["sampler", "digidelay"], []),
              (["digidelay", "sampler"], []), (["sampler", "refdelay", "refreverb"], []),
              (["digidelay", "refreverb", "refmachine2", "sampler"], []), (["chordtables", "digidelay"], []))
PARTS = ("shortcuts", "dispatch", "fxslot")
COMPARED = ("id", "order", "name", "version", "conflicts", "writes", "append", "symbols")


def packages():
    """(id, roots, patch points, object bytes) of every package with exactly one committed object, then of every part
    of the builder, laid out with all its roots."""
    for d in sorted(p for p in MACHINES.iterdir() if p.is_dir()):
        mf = d / "manifest.json"
        if not mf.is_file():
            continue
        m = json.loads(mf.read_text(encoding="utf-8"))
        b = m.get("build", {})
        objs = b.get("objects", [])
        if len(objs) == 1 and (d / objs[0]).is_file():
            if "roots" in b:                 # an extension of a stock machine: compose.roots_of()
                r = b["roots"]
                names = [r[0], r[1] if len(r) > 1 else r[0], *dict.fromkeys(r[2:] + b.get("keep", []))]
            else:
                names = [b["symbols"]["update"], b["symbols"]["render"], *b.get("keep", [])]
            yield m["id"], names, b.get("patch_points", []), (d / objs[0]).read_bytes()
    for pid in PARTS:
        b = json.loads((MACHINES / pid / "part.json").read_text(encoding="utf-8"))["build"]
        yield pid, b["roots"], b["patch_points"], (MACHINES / pid / b["objects"][0]).read_bytes()


def part1(out):
    rnd = random.Random(61)
    ref = {}
    for mid, names, pps, obj in packages():
        upd, rnd_sym, keep = names[0], names[1], names[2:]
        lay = relocate.layout(obj, upd, rnd_sym, keep, mid)
        points = [pp["symbol"] for pp in pps if "symbol" in pp]
        spots = [(0x43000000, 0x43036000), (0x43000518, 0x430360c0), (0x43007740, 0x4304a038)]
        spots += [(0x43000000 + 4 * rnd.randrange(0x8000), 0x43036000 + 4 * rnd.randrange(0x8000)) for _ in range(20)]
        cases = []
        for code_at, bss_at in spots:
            values = {p: rnd.randrange(200) for p in points}
            blob, syms, end = relocate.place(obj, upd, rnd_sym, keep, code_at, bss_at, CODE_END, values, mid)
            cases.append({"code_at": code_at, "bss_at": bss_at, "values": values, "blob": blob.hex(),
                          "symbols": {k: syms[k] for k in names}, "bss_end": end})
        ref[mid] = {"bundle": relocate.bundle(lay, names), "cases": cases}
        print(f"{mid}: {len(lay['code'])} bytes of code and tables, {len(lay['relocs'])} relocations, "
              f"{len(cases)} placements")
    (out / "compose.json").write_text(json.dumps(ref), encoding="utf-8")


def part2(out, cycles):
    import compose                     # noqa: E402  (imports the generators: only for part 2)
    import gen_sdvintage_7th as g7     # noqa: E402
    import gen_sdvintage_exact as gx   # noqa: E402
    raw = pathlib.Path(cycles).read_bytes()
    img = g7.cycles_main(cycles)
    if len(img) != gx.IMAGE_LEN:
        sys.exit("!! not the official MAIN OS 1.13")
    frs = json.loads((MACHINES / "registrar" / "frame.json").read_text(encoding="utf-8"))
    if frs != json.loads(json.dumps(compose.frames(img, compose.load_registrar()))):
        sys.exit("!! tools/machines/registrar/frame.json is not up to date: run tools/gen_registrar.py --cycles ...")
    tweaks, full = [], {}
    for t in compose.folder_tweaks():
        slim = {"id": t["id"], "writes": [{"off": w["off"], "new": w["new"]} for w in t.get("writes", [])]}
        if t.get("append"):
            slim["append"] = {"dest": t["append"]["dest"], "size": t["append"]["size"]}
        tweaks.append(slim)
        full[t["id"]] = t
    # probes for the rule the folder leaves undecided (its tweaks with a payload in our ranges also write our bytes):
    # a payload in the composed payload, in SAMPLE's pool, at its edges, beyond; the same bytes, other bytes
    hook = frs["writes"][0]
    tweaks += [{"id": "probe-payload", "writes": [], "append": {"dest": "0x43010000", "size": 0x100}},
               {"id": "probe-pool", "writes": [], "append": {"dest": "0x44000000", "size": 0x10}},
               {"id": "probe-pool-end", "writes": [], "append": {"dest": "0x466ffff0", "size": 0x10}},
               {"id": "probe-past-pool", "writes": [], "append": {"dest": "0x46700000", "size": 0x10}},
               {"id": "probe-same-bytes", "writes": [{"off": hook["off"], "new": hook["new"]}]},
               {"id": "probe-other-bytes", "writes": [{"off": hook["off"], "new": "4e71" * (len(hook["new"]) // 4)}]}]
    probe = {"probe-claim-slot": {"sound_slots": [[29, "all"]]},
             "probe-claim-gesture": {"gestures": [{"combo": "RETRIG + SHAPE", "atoms": [["RETRIG", "SHAPE"]],
                                                    "situation": "params", "scope": "all", "meaning": "a probe",
                                                    "replaces": None}]},
             "probe-claim-formatter": {"formatters": [[53, "machine:CHORD", "a probe"]]},
             "probe-claim-scope": {"sound_slots": [[25, "machine:CHORD"]]},
             "probe-claim-view": {"views": [["main", "all", "a probe"]]}}
    tweaks += [{"id": i, "writes": []} for i in probe]
    ids_ = {t["id"] for t in tweaks}
    claimed = {i: c for i, c in cl.tweak_claims().items() if i in ids_} | probe
    pkgs, cases = {}, []
    for ids, with_ in SELECTIONS:
        tweak, info = compose.compose(img, ids, against=tweaks, against_claims=claimed)   # with the parts it needs
        with contextlib.redirect_stdout(io.StringIO()):          # build.py's report of the caves, for each build
            _syx, patched = compose.build_syx(raw, [tweak] + [full[w] for w in with_])
        for i in ids:
            pkgs.setdefault(i, compose.web_package(i))
        cases.append({"ids": ids, "with": with_, "tweak": {k: tweak[k] for k in COMPARED},
                      "main_os": compose.sha(patched)})
        print(f"{'+'.join(ids)}{''.join(' + ' + w for w in with_)}: {len(tweak['writes'])} writes, "
              f"{info['image']} bytes added, {len(tweak['conflicts'])} conflicts, MAIN OS {compose.sha(patched)[:12]}")
    # fill() for 1 to 6 machines (the two packages give 1 and 2): synthetic machines, their names and knob names
    # shared or not, ranges or not, code with gaps around segments()' 64 bytes, a table above the stubs
    rnd, lay, fills = random.Random(62), frs["layout"], []
    for n in range(1, frs["runtime"]["max_machines"] + 1):
        machines, blobs, at = [], [], lay["pay"]
        for i in range(n):
            size = 4 * rnd.randrange(1, 64)
            blobs.append((at, bytes(rnd.randrange(256) for _ in range(size))))
            machines.append(dict(name="Tone" if i == 1 else f"MACH{i}", image=rnd.randrange(8), decay=rnd.randrange(128),
                                 knobs=[("Tone", "TONE", 127), ("Start", "STRT", 0, 0, 120), (f"Knob{i}", f"K{i}", 64),
                                        ("Level", "LEVL", 100, 1, 127)],
                                 update=at, render=at + 2 * rnd.randrange(size // 2)))
            at += size + 4 * rnd.randrange(24)                  # a gap of 0 to 92 bytes
        bss_end = lay["pay"] + lay["bss_off"]
        if n % 2 == 0:
            blobs.append((bss_end, bytes(rnd.randrange(256) for _ in range(4 * rnd.randrange(1, 32)))))
            bss_end += len(blobs[-1][1])
        bss_end += 4 * rnd.randrange(1, 0x400)
        writes, append = compose.fill(compose.frame_of(frs, n), img, machines, blobs, bss_end)
        fills.append({"machines": machines, "blobs": [[a, b.hex()] for a, b in blobs], "bss_end": bss_end,
                      "writes": writes, "append": append})
    print(f"fill: {len(fills)} synthetic builds of 1 to {len(fills)} machines")
    device = json.loads((compose.DEV / "device.json").read_text(encoding="utf-8"))
    used = {w for _ids, with_ in SELECTIONS for w in with_}
    (out / "composed.json").write_text(json.dumps({
        "device": device, "frames": frs, "packages": pkgs, "parts": {pid: compose.web_part(pid) for pid in PARTS},
        "tweaks": tweaks, "claims": claimed,
        "with": {k: full[k] for k in sorted(used)}, "cases": cases, "fills": fills}), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx: also writes part 2 (composed.json)")
    args = ap.parse_args()
    out = pathlib.Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    part1(out)
    if args.cycles:
        part2(out, args.cycles)


if __name__ == "__main__":
    main()
