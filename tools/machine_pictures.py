"""An added machine's own pictures as C (notes/60 §25, notes/71 §13): the OS's Bitmaps, a mask each on its own rows,
and the registrar's table of three (the MACHINES page's card and icon, the track icon). gen_solid.py and
gen_sampler.py write their package's file with it."""

BITMAP_VTABLE = 0x401173c8          # the OS's Bitmap (constructor 0x40070172 writes it at +0)
PICTURE_FILES = (("card", 48, 33), ("icon", 34, 34), ("small", 25, 22))


def sprites_c(prefix, opening, pkg, runtime):
    """The C file: `prefix` names the type ({prefix}_sprite), the files (pkg/pictures/{prefix}_{name}_{w}x{h}.bin)
    and the table ({prefix}_pictures); `opening` is the first comment's first two lines; `runtime` maps a picture to
    the array a source of the package fills at run time instead of a file. The masks are set on the pictures' own
    rows only, as the stock masks are (the draw, 0x40071da4, writes whole words: a mask bit above the picture would
    clear the screen there)."""
    out = [*opening,
           "   Each is one of the OS's Bitmaps (constructor 0x40070172): +0 its vtable, +4 width, +8 height, +12 32-bit",
           "   words a column, +16 the pixels, +20 the mask, +24 a byte the constructor clears; the draw (0x40071da4) reads",
           "   +4 to +20. A column's words hold its pixels from the bottom up, bit 31 first. */",
           "#include <stdint.h>", "",
           "typedef struct {",
           "    uint32_t vtable;",
           "    int32_t width, height, pitch;",
           "    const uint32_t *words, *mask;",
           "    uint32_t cleared;",
           f"}} {prefix}_sprite;", ""]
    names = []
    for name, w, h in PICTURE_FILES:
        pitch = (h + 31) // 32
        mask = []
        for _ in range(w):
            for k in range(pitch):
                rows = max(0, min(32, h - 32 * k))
                mask.append(((1 << rows) - 1) << (32 - rows) if rows else 0)
        tables = [("mask", mask)]
        px = f"{name}_px"
        if name in runtime:
            px = runtime[name]
            out.append(f"extern uint32_t {px}[{w * pitch}];")
        else:
            path = pkg / "pictures" / f"{prefix}_{name}_{w}x{h}.bin"
            data = path.read_bytes()
            if len(data) != 4 * pitch * w:
                raise SystemExit(f"!! {path.name}: {len(data)} bytes, {4 * pitch * w} expected for {w} x {h}")
            words = [int.from_bytes(data[i:i + 4], "big") for i in range(0, len(data), 4)]
            if any(x & ~m_ for x, m_ in zip(words, mask)):
                raise SystemExit(f"!! {path.name}: pixels set above the picture's {h} rows")
            tables.insert(0, ("px", words))
        for label, vals in tables:
            out.append(f"static const uint32_t {name}_{label}[{len(vals)}] = {{")
            for i in range(0, len(vals), 8):
                out.append("    " + ", ".join(f"0x{v:08x}" for v in vals[i:i + 8]) + ",")
            out.append("};")
        out.append(f"static const {prefix}_sprite {name} = {{0x{BITMAP_VTABLE:08x}, {w}, {h}, {pitch}, {px}, "
                   f"{name}_mask, 0}};\t/* {w} x {h} */")
        out.append("")
        names.append(name)
    out.append("/* the registrar's pictures (registrar.S, entry +12): the MACHINES page's card and icon, the track icon */")
    out.append(f"const {prefix}_sprite *const {prefix}_pictures[3] = {{" + ", ".join(f"&{n}" for n in names) + "};")
    return "\n".join(out) + "\n"
