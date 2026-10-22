#!/usr/bin/env python3
"""Reference data for tools/webcompose_check.js (notes/61): what docs/flasher/composer.js must give, computed by the
Python composer, so that the page and tools/compose.py compose the same bytes.

Part 1 (B3a), no firmware needed: every package of tools/machines/ that has an object, laid out once
(relocate.layout, relocate.bundle), and what relocate.place gives at a set of placements: the code and the variables
at 4-aligned addresses (where the composer puts the packages alone and in pairs, then random ones), the patch points
at assorted values.

Part 2 (B3b), with the official file (--cycles): the tweak compose.compose() composes for each selection of
SELECTIONS and the MAIN OS compose.build_syx() builds from it with the tweaks named on top, and what the page composes
them from: each package as compose.web_package() gives it, the committed frame.json (refused when it is not what
compose.frames() gives), the folder's tweaks reduced to what the conflicts read plus a few probes, device.json. Then
compose.fill() for 1 to 6 synthetic machines, what two packages cannot reach.

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

import relocate  # noqa: E402

MACHINES = HERE / "machines"
CODE_END = 0x48000000                       # no limit here: the composer checks the room, not this comparison
# without REF2 until B4e: its shortcut brings in the shortcut layer (notes/63 §3), which composer.js does not compose yet
SELECTIONS = ((["sampler"], []), (["refmachine"], []), (["sampler", "refmachine"], []), (["refmachine", "sampler"], []),
              (["sampler", "refmachine"], ["arp", "trig-hold"]))
COMPARED = ("id", "order", "name", "version", "conflicts", "writes", "append", "symbols")


def packages():
    """(manifest, object bytes) of every package with exactly one committed object."""
    for d in sorted(p for p in MACHINES.iterdir() if p.is_dir()):
        mf = d / "manifest.json"
        if not mf.is_file():
            continue
        m = json.loads(mf.read_text(encoding="utf-8"))
        objs = m.get("build", {}).get("objects", [])
        if len(objs) == 1 and (d / objs[0]).is_file():
            yield m, (d / objs[0]).read_bytes()


def part1(out):
    rnd = random.Random(61)
    ref = {}
    for m, obj in packages():
        b = m["build"]
        upd, rnd_sym, keep = b["symbols"]["update"], b["symbols"]["render"], b.get("keep", [])
        names = [upd, rnd_sym, *keep]
        lay = relocate.layout(obj, upd, rnd_sym, keep, m["id"])
        points = [pp["symbol"] for pp in b.get("patch_points", []) if "symbol" in pp]
        spots = [(0x43000000, 0x43036000), (0x43000518, 0x430360c0), (0x43007740, 0x4304a038)]
        spots += [(0x43000000 + 4 * rnd.randrange(0x8000), 0x43036000 + 4 * rnd.randrange(0x8000)) for _ in range(20)]
        cases = []
        for code_at, bss_at in spots:
            values = {p: rnd.randrange(200) for p in points}
            blob, syms, end = relocate.place(obj, upd, rnd_sym, keep, code_at, bss_at, CODE_END, values, m["id"])
            cases.append({"code_at": code_at, "bss_at": bss_at, "values": values, "blob": blob.hex(),
                          "symbols": {k: syms[k] for k in names}, "bss_end": end})
        ref[m["id"]] = {"bundle": relocate.bundle(lay, names), "cases": cases}
        print(f"{m['id']}: {len(lay['code'])} bytes of code and tables, {len(lay['relocs'])} relocations, "
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
    pkgs, cases = {}, []
    for ids, with_ in SELECTIONS:
        tweak, info = compose.compose(img, ids, against=tweaks)
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
        "device": device, "frames": frs, "packages": pkgs, "tweaks": tweaks,
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
