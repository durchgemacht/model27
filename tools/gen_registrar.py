#!/usr/bin/env python3
"""Generates the registrar package's committed data, tools/machines/registrar/registrar.json (notes/60).

B2b (§4): the **boot stub as a template**. tools/machines/syntakt_bridge/stub.S, in its PACK form, is what every
added-machine tweak writes into the freed sprite mask at gx.CAVE: it zeroes the payload window, copies each segment
of the payload from the end of the image to its place, then runs the two instructions it replaced. Only three
immediates and the segment table depend on the build. This generator assembles the stub once with placeholder
values, finds the immediates' offsets by their placeholders, and commits the code bytes with those offsets; the
composer (tools/compose.py, boot_stub) fills them and appends the segment table, with no assembler.

B2c (§5): the **registrar runtime**, registrar.S, the detours of the added machines assembled once at STUBS
(0x43033000) with a parameter block at REGS (STUBS + 0x780) that the composer fills per build (n, first, top, nm,
last, the knob table, and one 16-byte entry per machine: index, picture, first descriptor, record, knob hook, own
pictures, notes/71 §13). Its code and
the addresses of its entries (the targets of the OS's jumps and call) are committed here too.

B3b (notes/61 §3), with --cycles: the **frame** of the registrar's part for n = 1 to 6 machines, what the composer
writes whatever the machines are (compose.frame()), read from the official MAIN OS: tools/machines/registrar/
frame.json, which the web flasher fills like compose.fill(). It carries positions, the short old bytes every tweak
carries and model27's own values; the stock values fill() needs are read in the user's file.

    python3 tools/gen_registrar.py [--cycles model-cycles_OS1.13.syx] [--check]
"""
import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import compose                     # noqa: E402
import gen_macro as gm             # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402

OUT = HERE / "machines" / "registrar" / "registrar.json"
FRAME = HERE / "machines" / "registrar" / "frame.json"
SRC = HERE / "machines" / "registrar" / "registrar.S"
REGS_OFF = 0x780                   # the parameter block: the last 128 bytes of STUBS..DATA
ENTRY, MAX_MACHINES = 16, 6        # one entry per added machine; gs.check_room allows 6 (109 descriptors)
ENTRIES = ("state_at", "state_connect", "cc_bounds", "drum_icons", "small_icon", "record_at", "record_of", "marks",
           "knob_vec", "desc_machine", "builder_row", "main_icon", "preset_icon_a", "preset_icon_b")
PLACEHOLDERS = {"src": 0x7a5a5a51, "dst": 0x7b5b5b52, "longs": 0x7c5c5c53}     # distinct, found once each


def stub_template(tmp):
    """The PACK stub assembled at gx.CAVE with placeholder immediates and an empty segment table:
    (code bytes, {name: offset of its 4-byte immediate}, offset of the segment table)."""
    (tmp / "segs.inc").write_text("")
    blob, _ = gm.assemble(tmp, "stub", gx.SRC / "stub.S", gx.CAVE, [
        f"-DPAYLOAD_SRC={PLACEHOLDERS['src']:#x}", f"-DPAYLOAD_DST={PLACEHOLDERS['dst']:#x}",
        f"-DPAYLOAD_LONGS={PLACEHOLDERS['longs']:#x}", "-DPACK", f"-I{tmp}"])
    if blob[-8:] != bytes(8):
        raise SystemExit("!! the stub does not end with the empty segment table")
    code = blob[:-8]
    offs = {}
    for name, v in PLACEHOLDERS.items():
        b = v.to_bytes(4, "big")
        i = code.find(b)
        if i < 0 or code.find(b, i + 1) >= 0:
            raise SystemExit(f"!! placeholder {name} found {code.count(b)} times in the stub")
        offs[name] = i
    return code, offs, len(code)


def runtime(tmp):
    """registrar.S assembled at gs.STUBS for the alone layout (gs.PAY_ALONE): (code bytes, {entry: address})."""
    gs.set_base(gs.PAY_ALONE)
    regs = gs.STUBS + REGS_OFF
    blob, syms = gm.assemble(tmp, "registrar", SRC, gs.STUBS,
                             [f"-DREGS={regs:#x}", f"-DDESCN={gs.DESCN:#x}", f"-DMARKS_ROW={gs.MARKS_ROW}"])
    if gs.STUBS + len(blob) > regs:
        raise SystemExit(f"!! the runtime ({len(blob)} bytes) runs into its parameter block at {regs:#x}")
    missing = [e for e in ENTRIES if e not in syms]
    if missing:
        raise SystemExit(f"!! entries missing from registrar.S: {missing}")
    return blob, {e: syms[e] for e in ENTRIES}, regs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx: also writes frame.json (B3b)")
    ap.add_argument("--check", action="store_true", help="checks that the committed files match")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as d:
        code, offs, segs_at = stub_template(pathlib.Path(d))
        rt, entries, regs = runtime(pathlib.Path(d))
    data = {
        "schema": "model27-registrar/0.1",
        "description": [
            "The registrar's committed data (notes/60): what tools/compose.py writes without the toolchain.",
            "stub: the PACK boot stub of tools/machines/syntakt_bridge/stub.S assembled at the freed sprite mask",
            "(gx.CAVE), its three build-dependent immediates at the given offsets (4 bytes, big endian: the payload's",
            "source at the end of the image, its destination, its length in longs), and the segment table appended",
            "at segs_at (address, longs per segment, then 0, 0).",
            "runtime: registrar.S assembled at STUBS of the alone layout (0x43033000), the detours of the added",
            "machines reading the parameter block at regs_at (see registrar.S for its layout: 16 bytes of header,",
            "then entry_size bytes per machine, max_machines at most); entries are the addresses the OS's jumps",
            "and call are pointed at (g7.JUMPS, g8.JUMPS8, g7.CALLS). Generated by tools/gen_registrar.py.",
        ],
        "stub": {
            "at": f"{gx.CAVE:#x}",
            "end_limit": f"{gs.STUB_END:#x}",
            "hex": code.hex(),
            "src_at": offs["src"], "dst_at": offs["dst"], "longs_at": offs["longs"],
            "segs_at": segs_at,
        },
        "runtime": {
            "at": f"{gs.STUBS:#x}",
            "hex": rt.hex(),
            "entries": {e: f"{a:#x}" for e, a in entries.items()},
            "regs_at": f"{regs:#x}",
            "regs_header": 16, "entry_size": ENTRY, "max_machines": MAX_MACHINES,
            "descn": f"{gs.DESCN:#x}", "marks_row": gs.MARKS_ROW,
        },
    }
    text = json.dumps(data, indent=1) + "\n"
    print(f"  stub: {len(code)} bytes of code, immediates at {offs}, segment table at {segs_at}, "
          f"room for {(gs.STUB_END - gx.CAVE - segs_at - 8) // 8} segments")
    print(f"  runtime: {len(rt)} bytes at {gs.STUBS:#x}, parameter block at {regs:#x} "
          f"({16 + ENTRY * MAX_MACHINES} bytes for {MAX_MACHINES} machines), {len(entries)} entries")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bad = gm.emit(OUT, text, args.check)
    if args.cycles:
        img = g7.cycles_main(args.cycles)
        if len(img) != gx.IMAGE_LEN:
            raise SystemExit("!! not the official MAIN OS 1.13")
        frs = compose.frames(img, data)
        print(f"  frame: {len(frs['writes'])} writes for every n, "
              f"{', '.join(f'{len(v["writes"])} for n = {n}' for n, v in frs['by_n'].items())}")
        bad |= gm.emit(FRAME, json.dumps(frs, indent=1) + "\n", args.check)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
