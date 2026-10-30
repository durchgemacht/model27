#!/usr/bin/env python3
"""Writes tweaks/model-cycles_OS1.13/80-trig-cond-order.json: a trig held + CHANCE goes through the trig conditions in
another order (notes/70).

The stock knob steps the condition code itself: FILL, !FILL, PRE, !PRE, NEI, !NEI, 1st, !1st, then 1% to 99%, then
1:2 to 8:8. With the tweak it steps through ORDER below (the A:B conditions before the percentages), and the value
window's five dots show the position in that order; the code a trig keeps, plays and shows is the stock one, so
patterns are the same with and without the mod.

tools/machines/trig_cond_order/: trig_cond_order.S (TrigParameterSet's "value + delta" method for Trig Cond, the
dots' detour, and the order this script writes into it), linked by trig_cond_order.ld into the freed 48x22 sprite
mask 0x40152d38 (tools/sprites.py). The writes on the OS are VTABLE and HOOK below; every write carries its stock
bytes, checked on the official MAIN OS.

    python3 tools/gen_trig_cond_order.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import sprites                     # noqa: E402
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "trig_cond_order"
OUT = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "80-trig-cond-order.json"
BASE = gx.BASE
MASK = 0x40152d38                                   # freed 48x22 mask (192 bytes)
# Condition codes (the sequencer's jump table 0x40091428, the names 0x401090b4): 0-7 FILL !FILL PRE !PRE NEI !NEI 1st
# !1st, 8-28 1% to 99%, 29-63 1:2 to 8:8. ORDER[position] = the code the knob shows at that position.
ORDER = list(range(0, 8)) + list(range(29, 64)) + list(range(8, 29))
TPS_VTABLE, TPS_TYPEINFO = 0x400fd204, 0x400fd080   # TrigParameterSet's vtable (address point) and typeinfo
# (address, stock bytes, symbol, role)
VTABLE = (TPS_VTABLE + 0x14, "4000a980", "tco_step",
          "TrigParameterSet vtable +0x14, \"value + delta\" (called by ParameterSet's knob step 0x4000a5f8): "
          "0x4000a980 -> tco_step (Trig Cond in ORDER, the rest to 0x4000a980)")
# (address, stock bytes, symbol, role), in the value window (ParameterPageView's vtable +0x90, 0x4001d818)
HOOK = (0x4001d91c, "2045e78ced88", "tco_dots",
        "the five dots: movea.l d5,a0 ; lsl.l #3,d4 ; lsl.l #6,d0 -> jsr tco_dots (for Trig Cond, the position in "
        "ORDER instead of the code)")
SYMBOLS = ("tco_step", "tco_dots", "tco_order")     # for tools/emu/test_trig_cond_order.py


def compile_tco():
    """The linked code: (address, bytes) of the cave, symbols."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf, out = d / "tco.o", d / "tco.elf", d / "cave.bin"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(SRC / "trig_cond_order.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "trig_cond_order.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        heads = subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                               check=True).stdout
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".cave", str(elf), str(out)])
        return (int(heads.split(".cave")[1].split()[1], 16), out.read_bytes()), syms


def build_tweak(stock):
    if sorted(ORDER) != list(range(64)):
        raise SystemExit("!! ORDER must hold each code 0..63 once")
    (addr, code), syms = compile_tco()
    size, shared = sprites.MASKS[MASK][0], sprites.MASKS[MASK][3]
    if addr != MASK or len(code) > size:
        raise SystemExit(f"!! {len(code)} bytes at {addr:#x}, room {size} bytes at {MASK:#x}")
    if stock[MASK - BASE:MASK - BASE + size] != stock[shared - BASE:shared - BASE + size]:
        raise SystemExit(f"!! mask {MASK:#x} differs from the kept mask {shared:#x}")
    at = syms["tco_order"] - addr
    if code[at:at + 64] != bytes(64):
        raise SystemExit("!! tco_order is not the 64 bytes the generator fills")
    code = code[:at] + bytes(ORDER) + code[at + 64:]
    va, old_hex, sym, _ = VTABLE
    if stock[va - BASE:va - BASE + 4].hex() != old_hex:
        raise SystemExit(f"!! unexpected stock bytes at {va:#x}")
    if struct.unpack_from(">I", stock, TPS_VTABLE - 4 - BASE)[0] != TPS_TYPEINFO \
            or b"16TrigParameterSet\0" not in stock[0x4012536e - BASE:0x4012536e - BASE + 19]:
        raise SystemExit(f"!! {TPS_VTABLE:#x} is not TrigParameterSet's vtable")
    hva, hold, hsym, _ = HOOK
    if stock[hva - BASE:hva - BASE + 6].hex() != hold:
        raise SystemExit(f"!! unexpected stock bytes at {hva:#x}")
    writes = [
        {"off": addr - BASE, "old": stock[addr - BASE:addr - BASE + len(code)].hex(), "new": code.hex()},
        sprites.redirect_write(MASK),
        {"off": va - BASE, "old": old_hex, "new": f"{syms[sym]:08x}"},
        {"off": hva - BASE, "old": hold, "new": struct.pack(">HI", 0x4eb9, syms[hsym]).hex()},
    ]
    writes.sort(key=lambda w: w["off"])
    tweak = {
        "id": "trig-cond-order",
        "order": 80,
        "name": "Trig conditions in another order on the knob",
        "description": [
            "A trig held + CHANCE goes through the trig conditions as FILL, !FILL, PRE, !PRE, NEI, !NEI, 1st, !1st, "
            "then 1:2 to 8:8, then 1% to 99% (stock: the percentages before the A:B conditions).",
            "Only the knob's order changes: a trig keeps the same condition code as in the stock OS, plays it and "
            "shows its name the same way, so patterns are the same with and without the tweak, both ways. The first "
            "turn on a trig without a condition still gives FILL; fast turns and FUNC step as many positions as the "
            "stock knob steps codes.",
            "The five dots under the value follow the new order too, like a scroll bar of the list.",
            "TrigParameterSet's \"value + delta\" method (its vtable entry) goes to the tweak's code for Trig Cond "
            "only; every other parameter keeps the stock method. A 6-byte detour in the value window (0x4001d91c) "
            "gives the dots the position in the new order instead of the code, for Trig Cond only.",
            f"Code and order in a freed 48x22 sprite mask (tools/sprites.py): {len(code)} bytes at {addr:#x}. "
            "Written by tools/gen_trig_cond_order.py, notes/70.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": writes,
    }
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="the official model-cycles_OS1.13.syx")
    ap.add_argument("--check", action="store_true", help="checks that the committed JSON is up to date")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((OUT.parent / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! not the official MAIN OS 1.13")
    tweak = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # the stock bytes match
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'is up to date' if ok else 'DIFFERS (another binutils?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  written: {OUT} ({len(tweak['writes'])} writes)")


if __name__ == "__main__":
    main()
