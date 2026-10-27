#!/usr/bin/env python3
"""Builds the builder's parts into their committed objects (notes/63 §3 to §5, steps B4b and B4c).

A part is code of model27's builder, not a machine: tools/compose.py adds it to the builds that need it, as it adds
the registrar runtime to every build. It lives in tools/machines/<id>/ with its sources and a part.json (schema
model27-part/0.1): the recipe, the roots relocate.py keeps, the patch points, and what the composer writes for it.
This generator compiles or assembles the sources with that recipe and joins them with ld -r into
tools/machines/<id>/<id>.o, as a package's generator writes its object, then checks what the composer relies on: the
roots are defined, the only undefined symbols are the patch points, every relocation is R_68K_32. --check compares
with the committed object.

Today three parts: shortcuts, the machine shortcuts and the sound record chain (tools/machines/shortcuts/, B4b);
dispatch, the dispatchers of the points two machines share (tools/machines/dispatch/, B4c); and fxslot, the effect
slots (tools/machines/fxslot/, notes/68 step F1). Needs the m68k toolchain; compose.py does not.

    python3 tools/gen_parts.py [--check]
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compose                     # noqa: E402
import relocate                    # noqa: E402

PARTS = ("shortcuts", "dispatch", "fxslot")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="checks that the committed objects match")
    args = ap.parse_args()
    bad = False
    for pid in PARTS:
        p = compose.load_part(pid)
        with tempfile.TemporaryDirectory() as d:
            obj = compose.build_object(p, pathlib.Path(d))
        roots = p["build"]["roots"]
        lay = relocate.layout(obj, roots[0], roots[1], roots[2:], pid)
        points = {pp["symbol"] for pp in p["build"]["patch_points"]}
        undefined = {base for _pos, base, _add in lay["relocs"] if base not in ("code", "bss", "abs")}
        if undefined != points:
            raise SystemExit(f"!! {pid}: undefined symbols {sorted(undefined)}, patch points {sorted(points)}")
        if lay["bss"]:
            raise SystemExit(f"!! {pid}: {lay['bss']} bytes of variables: a part keeps its state in its data block")
        print(f"  {pid}: {len(lay['code'])} bytes of code, {len(lay['relocs'])} relocations, roots {', '.join(roots)}")
        bad |= bool(compose.emit_bytes(compose.object_path(p), obj, args.check))
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
