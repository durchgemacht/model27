#!/usr/bin/env python3
"""Composes added machines into one tweak at build time (notes/59, increment B1 of the Cycles Mod Standard's
Level B).

A machine is a package: tools/machines/<id>/ with its sources and a manifest.json (schema cycles-mod/0.1). The
composer takes the packages the user names, in that order, and:

  1. places each package's committed object (tools/machines/<id>/<id>.o, written by its generator) at its address
     with tools/relocate.py, the values that depend on the build resolved as symbols (its "patch_points": the
     machine index, 6 + i, and its first descriptor, 76 + 5 i); or, with --relocator ld, compiles and links the
     sources as B1 did (--compare-ld does both and compares them, notes/60 §3);
  2. lays them out in the added machines' payload window (0x43000000, gs.PAY_ALONE): code and tables one after the
     other from the window's start, variables one after the other from +0x36000 (above the moved tables, as MACRO),
     links each one there, and refuses a layout that crosses the stubs or a package's RAM claim, and two
     packages whose RAM claims overlap;
  3. registers them all at once (registrar_writes: the tables of names, update/render, records and descriptors,
     the bounds, the jumps into the committed registrar runtime, its parameter block for this build, the boot
     hook from the committed stub template; tools/machines/registrar/, notes/60 §4-5; --registrar b1 calls
     gen_macro.added_machine instead and --compare-b1 compares the two), then adds each package's own hooks
     and vtable entries from its manifest; when a machine declares a shortcut, adds the shortcut layer
     (tools/machines/shortcuts/, notes/63 §3: a committed part placed after the packages, its data block, the
     knob lookup and the sound record functions jumping into it, a package's record wrapper chained behind it);
     when two packages take the same vtable entry or hook, adds the dispatchers (tools/machines/dispatch/, notes/63
     §4: another part, the entry or hook going to its dispatcher, which calls the right machine's method);
     when a package is an effect (fx.delay or fx.reverb, notes/68), adds the effect slots (tools/machines/fxslot/:
     a part, the mixer's call of each slot that has an effect going to its dispatcher, which calls the effect the
     playing pattern chose, or the stock one; the pattern header's loader and initializer keep the choice);
  4. computes what the result cannot be installed with: every tweak of tweaks/ that writes other bytes to the same
     address or runs a payload in the composed payload or in a claimed RAM range, or whose declared claims clash
     with the build's (the same saved slot, key combination, descriptor or formatter: tools/claims.py, notes/65),
     plus what the manifests declare; refuses a build whose own packages' claims clash;
  5. emits one tweak in Modded-Cycles' format, which tools/build.py and the web flasher apply like any other, and
     builds the .syx with build.py's own steps (writes checked against the stock bytes, caves checked, repacked and
     re-signed, read back).

One machine alone gives the same tweak as its own generator (sampler: 27-sampler.json, byte for byte); two or more
give what no pre-built file holds. The composed tweak is written to build/ (git-ignored), not to tweaks/: it is a
build, not a mod.

    python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines sampler,refmachine \\
        [--with arp,trig-hold] [--out build/] [--emit path.json] [--compare tweaks/model-cycles_OS1.13/27-sampler.json] \\
        [--tool path/to/elektron-firmware-tool] [--relocator python|ld] [--compare-ld]

Runs with python3 alone (the relocator, the committed runtime and stub); --relocator ld, --compare-ld,
--registrar b1 and --compare-b1 need the m68k toolchain, as the generators do (they compile and commit the
objects, the runtime and the stub template).
"""
import argparse
import hashlib
import hmac
import json
import pathlib
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build as mcb                # noqa: E402
import claims as cl                # noqa: E402
import aplib_grow                  # noqa: E402
import gen_macro as gm             # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import gen_syntakt_machines as g8  # noqa: E402
import relocate                    # noqa: E402
import sprites                     # noqa: E402

BASE = mcb.BASE
DEV = ROOT / "tweaks" / "model-cycles_OS1.13"
MACHINES = HERE / "machines"
BUILD = ROOT / "build"
# The stock machines a package may extend ("machine.stock", notes/66 §3), by number: CHORD only for now, the one next
# to the added machines, so that the tables by machine (the shortcut layer's, the dispatchers') start at 5 with it.
STOCK_EXTENDED = {"CHORD": 5}
# The effect slots (notes/68 §2): a package that names one of them in uses is an effect, called in place of the
# mixer's delay or reverb when the playing pattern has chosen it (tools/machines/fxslot/).
FX_POINTS = ("fx.delay", "fx.reverb")
# A slot's line (notes/68 §16): RAM in the payload's variables that every effect of the slot asking for one shares, as
# one effect of a slot plays at a time; its address is the effect's patch point of kind fx_line. At most the stock
# delay's own line, 4 MiB.
FX_LINE_MAX = 0x400000
# The effect slots' load (notes/68 §17), in instructions per block by the standard's count (its §6: 166 667 cycles a
# block at 250 MHz, 1.54 cycles an instruction): a build warns when a slot's dearest effect costs more than FX_WARN
# above the stock effect, steadily, and is refused above FX_REFUSE. The emulator does not time memory: these are the
# numbers every author can produce, a device measurement beats them.
BLOCK_INSTR = 108225
FX_WARN, FX_REFUSE = BLOCK_INSTR // 10, BLOCK_INSTR // 4
FX_PEAK_WARN = BLOCK_INSTR // 2              # the block of a switch, once: a warning past half a block
REGISTRAR = MACHINES / "registrar" / "registrar.json"
LINK = """SECTIONS
{{
  .text {code:#x} : {{ *(.text.{update}) *(.text.{render}) *(.text*) }}
  .rodata : {{ *(.rodata*) }}
  .data : {{ *(.data*) }}
  .bss {bss:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }}
  /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }}
}}
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_manifest(mid):
    path = MACHINES / mid / "manifest.json"
    if not path.is_file():
        sys.exit(f"!! no package {mid}: {path} is missing")
    m = json.loads(path.read_text(encoding="utf-8"))
    if m.get("schema") != "cycles-mod/0.1":
        sys.exit(f"!! {path}: schema {m.get('schema')!r}, expected cycles-mod/0.1")
    if m["id"] != mid:
        sys.exit(f"!! {path}: id {m['id']!r} is not the folder's name")
    m["_dir"] = MACHINES / mid
    m["_machine"] = next((u for u in m["uses"] if u["point"] == "machine"), None)
    m["_stock"] = next((u for u in m["uses"] if u["point"] == "machine.stock"), None)
    m["_effect"] = next((u for u in m["uses"] if u["point"] in FX_POINTS), None)
    if m["_machine"] and m["_stock"]:
        sys.exit(f"!! {mid}: a 'machine' and a 'machine.stock' entry in uses: an added machine or an extension of a "
                 "stock machine, not both")
    if m["_effect"] and (m["_machine"] or m["_stock"]):
        sys.exit(f"!! {mid}: an effect and a machine in uses: an effect is a package of its own (notes/68 §2)")
    if not m["_machine"] and not m["_stock"] and not m["_effect"]:
        sys.exit(f"!! {mid}: no 'machine', 'machine.stock', 'fx.delay' or 'fx.reverb' entry in uses: not an added "
                 "machine, an extension or an effect")
    if m["_effect"]:                         # an effect of the delay or reverb slot (notes/68 §2)
        u = m["_effect"]
        if sum(x["point"] in FX_POINTS for x in m["uses"]) > 1:
            sys.exit(f"!! {mid}: an effect takes one slot")
        if not isinstance(u.get("id"), int) or not 1 <= u["id"] <= 255:
            sys.exit(f"!! {mid}: the effect's id must be 1 to 255 (0 is the stock effect): {u.get('id')!r}")
        roots = m["build"].get("roots", [])
        if not roots or roots[0] != u.get("process"):
            sys.exit(f"!! {mid}: an effect names its process first in build.roots (it has no update and render)")
        pps = m["build"].get("patch_points", [])
        if any(pp.get("kind") != "fx_line" or "symbol" not in pp for pp in pps) or len(pps) > 1:
            sys.exit(f"!! {mid}: an effect has one patch point at most, its line's address (kind fx_line, a symbol)")
        line = u.get("line")
        if bool(pps) != (line is not None):
            sys.exit(f"!! {mid}: an effect that asks for a line gives its size in 'line' and takes its address as a "
                     "patch point of kind fx_line, both or neither (notes/68 §16)")
        if line is not None and (not isinstance(line, int) or not 16 <= line <= FX_LINE_MAX or line % 16):
            sys.exit(f"!! {mid}: line: bytes, a multiple of 16 from 16 to {FX_LINE_MAX:#x}: {line!r}")
        other = [x["point"] for x in m["uses"] if x["point"] not in FX_POINTS + ("memory.ram",)]
        if other:
            sys.exit(f"!! {mid}: an effect uses its slot and its RAM only, not {', '.join(other)} (notes/68 §2)")
        if u.get("reset") and u["reset"] not in roots:
            sys.exit(f"!! {mid}: the effect's reset {u['reset']} is not in build.roots")
        texts = [("name", u.get("name"), 15)]
        params = u.get("params")
        if not isinstance(params, list) or len(params) != 2:
            sys.exit(f"!! {mid}: an effect names the slot's two parameters in params (notes/68 §11)")
        for k, prm in enumerate(params):
            texts += [(f"params[{k}].long", prm.get("long"), 15), (f"params[{k}].short", prm.get("short"), 5)]
            fmt = prm.get("format")
            if fmt not in (None, "int") and fmt not in roots:
                sys.exit(f"!! {mid}: params[{k}].format: 'int', a symbol in build.roots, or none (the stock one)")
        for what, text, most in texts:
            if not isinstance(text, str) or not 0 < len(text) <= most or not all(" " <= c <= "~" for c in text):
                sys.exit(f"!! {mid}: {what}: printable ASCII, 1 to {most} characters: {text!r}")
    if m["_stock"]:                          # an extension of a stock machine (notes/66 §3)
        name = m["_stock"].get("machine")
        if name not in STOCK_EXTENDED:
            sys.exit(f"!! {mid}: machine.stock {name!r}: only {', '.join(STOCK_EXTENDED)} can be extended, next to the "
                     "added machines (notes/66 §3)")
        m["_index"] = STOCK_EXTENDED[name]
        if not m["build"].get("roots"):
            sys.exit(f"!! {mid}: an extension names its entry points in build.roots (it has no update and render)")
        if any(pp["kind"] in ("machine_index", "descriptor_base") for pp in m["build"].get("patch_points", [])):
            sys.exit(f"!! {mid}: an extension has no machine index and no descriptors of its own")
    if any(u["point"] == "memory.sram" for u in m["uses"]) and not m["_stock"]:
        sys.exit(f"!! {mid}: memory.sram is the SRAM the OS gives a stock machine: only an extension of that machine "
                 "may take it (notes/66 §19.5)")
    return m


def roots_of(m):
    """The entry points a package's object is laid out from: an added machine's update and render, then its kept
    symbols; an extension's or an effect's build.roots (its first two in the places of update and render)."""
    b = m["build"]
    if m.get("_stock") or m.get("_effect"):
        r = b["roots"]
        return r[0], r[1] if len(r) > 1 else r[0], list(dict.fromkeys(r[2:] + b.get("keep", [])))
    return b["symbols"]["update"], b["symbols"]["render"], b.get("keep", [])


def load_part(pid):
    """A part of the builder (notes/63 §5): tools/machines/<pid>/part.json (schema model27-part/0.1), code assembled
    once into a committed object (tools/gen_parts.py) that the composer adds to the builds that need it."""
    path = MACHINES / pid / "part.json"
    if not path.is_file():
        sys.exit(f"!! no part {pid}: {path} is missing")
    p = json.loads(path.read_text(encoding="utf-8"))
    if p.get("schema") != "model27-part/0.1":
        sys.exit(f"!! {path}: schema {p.get('schema')!r}, expected model27-part/0.1")
    if p["id"] != pid:
        sys.exit(f"!! {path}: id {p['id']!r} is not the folder's name")
    p["_dir"] = MACHINES / pid
    return p


def align4(x):
    return (x + 3) & ~3


def patch_values(m, values):
    """The build's values for the package's patch points: (defines for the compiler, symbols for the relocator).
    A patch point is {"symbol": name, "kind": kind} (resolved like ld --defsym when the object is placed) or, the
    B1 form, {"define": NAME, "kind": kind} (a compile-time constant: the object then carries one index for ever,
    so a committed object cannot use it)."""
    defines, symbols = [], {}
    for pp in m["build"].get("patch_points", []):
        if pp["kind"] not in values:
            sys.exit(f"!! {m['id']}: patch point kind {pp['kind']!r} unknown")
        if "symbol" in pp:
            symbols[pp["symbol"]] = values[pp["kind"]]
        elif "define" in pp:
            defines.append(f"-D{pp['define']}={values[pp['kind']]}")
        else:
            sys.exit(f"!! {m['id']}: a patch point needs 'symbol' or 'define'")
    return defines, symbols


def compile_objects(m, tmp, defines=()):
    """Compiles the package's sources with its flags (and the given defines) into tmp; returns the objects in the
    manifest's order."""
    b, d = m["build"], m["_dir"]
    defs = [f"-D{k}={v}" for k, v in b.get("defines", {}).items()] + list(defines)
    incs = [f"-I{d / i}" for i in b.get("include", [])]
    objs = []
    for rel in b["sources"]:
        src = d / rel
        if not src.is_file():
            sys.exit(f"!! {m['id']}: source {src} is missing")
        o = tmp / f"{m['id']}-{src.stem}.o"
        gx.run([gx.CROSS + "gcc", *b["cflags"], *defs, *incs, "-c", str(src), "-o", str(o)])
        objs.append(o)
    return objs


def object_path(m):
    objs = m["build"].get("objects", [])
    if len(objs) != 1:
        sys.exit(f"!! {m['id']}: build.objects must name one object (ld -r of the sources), has {objs}")
    return m["_dir"] / objs[0]


def build_object(m, tmp):
    """The package's object as its generator commits it: the sources compiled with the manifest's recipe and
    joined with ld -r (one relocatable file, every function and table still a section of its own, the patch
    points still undefined symbols)."""
    objs = compile_objects(m, tmp)
    out = tmp / f"{m['id']}.o"
    gx.run([gx.CROSS + "ld", "-r", "-o", str(out), *map(str, objs)])
    return out.read_bytes()


def compile_package(m, tmp, code_at, bss_at, code_end, values):
    """The B1 path, with the toolchain: compiles the package's sources with its flags and the build's values for
    its patch points, links them at code_at (code, tables, data) and bss_at (variables); the code must end before
    code_end. Returns (bytes from code_at to the end of the data, symbols, end of the variables)."""
    b = m["build"]
    defines, symbols = patch_values(m, values)
    objs = compile_objects(m, tmp, defines)
    upd, rnd, kept = roots_of(m)
    ld, elf, out = tmp / f"{m['id']}.ld", tmp / f"{m['id']}.elf", tmp / f"{m['id']}.bin"
    ld.write_text(LINK.format(update=upd, render=rnd, code=code_at, bss=bss_at))
    keep = [a for s_ in kept for a in ("-u", s_)]
    defsym = [a for k, v in symbols.items() for a in ("--defsym", f"{k}={v}")]
    gx.run([gx.CROSS + "ld", "-T", str(ld), "--gc-sections", "--no-warn-rwx-segments", "-e", upd, "-u", rnd, *keep,
            *defsym, "-o", str(elf), *map(str, objs)])
    secs = {}
    for line in gx.run([gx.CROSS + "objdump", "-h", str(elf)]).splitlines():
        f = line.split()
        if len(f) > 4 and f[0].isdigit():
            secs[f[1]] = (int(f[3], 16), int(f[2], 16))      # address, size
    if set(secs) - {".text", ".rodata", ".data", ".bss"}:
        sys.exit(f"!! {m['id']}: unexpected sections {sorted(secs)}")
    gx.run([gx.CROSS + "objcopy", "-O", "binary", "-R", ".bss", str(elf), str(out)])
    blob = out.read_bytes()
    syms = {p[2]: int(p[0], 16) for p in (l.split() for l in gx.run([gx.CROSS + "nm", str(elf)]).splitlines())
            if len(p) == 3}
    for s_ in (upd, rnd, *kept):
        if s_ not in syms:
            sys.exit(f"!! {m['id']}: symbol {s_} not in the linked object")
    if code_at + len(blob) > code_end:
        sys.exit(f"!! {m['id']}: code and tables end at {code_at + len(blob):#x}, past {code_end:#x}")
    bss = secs.get(".bss", (bss_at, 0))
    if bss[0] != bss_at:
        sys.exit(f"!! {m['id']}: variables at {bss[0]:#x}, expected {bss_at:#x}")
    return blob, syms, align4(bss[0] + bss[1])


def place_package(m, code_at, bss_at, code_end, values, obj=None):
    """The B2 path, no toolchain: places the package's committed object (or obj, bytes) at code_at and bss_at with
    tools/relocate.py, the patch points resolved to the build's values. Same result as compile_package."""
    defines, symbols = patch_values(m, values)
    if defines:
        sys.exit(f"!! {m['id']}: patch points as defines cannot be applied to a committed object: use symbols")
    if obj is None:
        path = object_path(m)
        if not path.is_file():
            sys.exit(f"!! {m['id']}: {path} is missing: run the package's generator (it writes the object)")
        obj = path.read_bytes()
    upd, rnd, kept = roots_of(m)
    return relocate.place(obj, upd, rnd, kept, code_at, bss_at, code_end, symbols, m["id"])


def exported(m):
    """The symbols of a package a composed tweak lists: its entry points and kept symbols."""
    a, b, keep = roots_of(m)
    return {a, b, *keep}


def placed(p):
    """One package of a build in its tweak's description."""
    if p.get("slot"):
        return f"{p['id']} as effect {p['fx_id']} of the {p['slot']} slot"
    if p.get("extends"):
        return f"{p['id']} extending {p['extends']} (machine {p['index']})"
    return f"{p['id']} as machine {p['index']}"


def web_package(mid):
    """A package as the web flasher reads it (B3b, notes/61 §5): what compose() reads in its manifest (the machine,
    the hooks and vtable entries, the RAM claims, the patch points, the entry and kept symbols, order, version, the
    declared conflicts, the declared claims) and its committed object laid out once (relocate.layout,
    relocate.bundle).
    docs/flasher/composer.js composes from it what compose() composes from the manifest and the object."""
    m = load_manifest(mid)
    b = m["build"]
    upd, rnd, keep = roots_of(m)
    pps = b.get("patch_points", [])
    if any("symbol" not in pp for pp in pps):
        sys.exit(f"!! {mid}: patch points as defines cannot be applied to a committed object: use symbols")
    path = object_path(m)
    if not path.is_file():
        sys.exit(f"!! {mid}: {path} is missing: run the package's generator (it writes the object)")
    lay = relocate.layout(path.read_bytes(), upd, rnd, keep, mid)
    uses = [{k: v for k, v in u.items() if k != "why"} for u in m["uses"]
            if u["point"] in ("machine", "machine.stock", "memory.ram", "shortcut") + FX_POINTS
            or "hook" in u or "vtable" in u]
    names = [upd, rnd, *keep] if m["_machine"] else list(dict.fromkeys([upd, rnd, *keep]))
    out = {"id": mid, "name": m["name"], "order": m["order"], "version": m["version"],
           "symbols": {"update": upd, "render": rnd}, "keep": keep, "patch_points": pps, "uses": uses,
           "conflicts_declared": [c["with"] for c in m.get("compat", {}).get("conflicts_declared", [])],
           "claims": cl.package_claims(m), "bundle": relocate.bundle(lay, names)}
    if m["_effect"]:                         # an effect's load (notes/68 §17), which the page computes as fx_cost()
        out["cost"] = m.get("cost", {})
    return out


def web_part(pid):
    """A part as the web flasher reads it (B4e, notes/63 §5): what shortcut_layer() or dispatch_layer() reads in its
    part.json (the shortcut list, the sites, the data block's layout, the patch points, the roots) and its committed
    object laid out once with all its roots (relocate.layout, relocate.bundle). docs/flasher/composer.js composes the
    layer from it as compose() does from the part."""
    p = load_part(pid)
    b = p["build"]
    path = object_path(p)
    if not path.is_file():
        sys.exit(f"!! {path} is missing: run tools/gen_parts.py")
    roots = b["roots"]
    lay = relocate.layout(path.read_bytes(), roots[0], roots[1], roots[2:], pid)
    out = {"id": pid, "version": p["version"], "roots": roots, "patch_points": b["patch_points"],
           "data": p["data"], "bundle": relocate.bundle(lay, roots)}
    for key in ("sites", "shortcut", "slots", "track", "load", "init", "formatter_sites", "int_format", "cost"):
        if key in p:                         # the effect slots' (notes/68) besides the shortcut layer's and dispatchers'
            out[key] = p[key]
    if "claims" in p:                        # notes/65: what the part claims, in tools/claims.py's to_json form
        out["claims"] = cl.part_claims(p)
    if p.get("conflicts_declared"):
        out["conflicts_declared"] = [c["with"] for c in p["conflicts_declared"]]
    return out


def emit_bytes(path, data, check):
    """Writes a binary file, or with check compares it with the committed one (like gen_macro.emit for text)."""
    if check:
        ok = path.exists() and path.read_bytes() == data
        why = ""
        if not ok and path.exists():
            try:
                why = (f" (committed object: {relocate.Elf(path.read_bytes(), path.name).comment()}; here: "
                       f"{relocate.Elf(data, 'new').comment()})")
            except SystemExit:
                pass
        print(f"    {path.name} {'is up to date' if ok else 'DOES NOT MATCH' + why}")
        return not ok
    path.write_bytes(data)
    print(f"    wrote {path}")
    return 0


def load_registrar():
    """The registrar's committed data (tools/gen_registrar.py, notes/60): the boot stub template, later the runtime."""
    if not REGISTRAR.is_file():
        sys.exit(f"!! {REGISTRAR} is missing: run tools/gen_registrar.py")
    reg = json.loads(REGISTRAR.read_text(encoding="utf-8"))
    if reg.get("schema") != "model27-registrar/0.1":
        sys.exit(f"!! {REGISTRAR}: schema {reg.get('schema')!r}")
    return reg


def boot_stub(reg, src, dst, longs, segs):
    """The boot stub for this build, from the template (B2b, notes/60 §4): the three immediates filled in, the
    segment table (address, longs per segment, then 0, 0) appended. Checked against the room at gx.CAVE."""
    st = reg["stub"]
    if int(st["at"], 16) != gx.CAVE:
        sys.exit(f"!! the stub template is for {st['at']}, the boot hook lives at {gx.CAVE:#x}")
    code = bytearray.fromhex(st["hex"])
    for key, v in (("src_at", src), ("dst_at", dst), ("longs_at", longs)):
        struct.pack_into(">I", code, st[key], v)
    table = b"".join(g7.be32(a) + g7.be32(n // 4) for a, n in segs) + bytes(8)
    stub = bytes(code[:st["segs_at"]]) + table
    if gx.CAVE + len(stub) > int(st["end_limit"], 16):
        sys.exit(f"!! boot stub of {len(stub)} bytes ({len(segs)} segments) does not fit before {st['end_limit']}")
    return stub


def check_boot_stub(reg, writes, append):
    """B2b's proof on every build: the stub the registrar assembled (the write at gx.CAVE) is the template's, byte
    for byte. Returns the write."""
    w = next((w for w in writes if w and w["off"] == gx.CAVE - BASE), None)
    if not w:
        sys.exit("!! no boot stub write at the freed sprite mask")
    segs = [(int(a, 16), n) for a, n in append["pack"]]
    want = boot_stub(reg, int(append["at"], 16), int(append["dest"], 16), append["size"] // 4, segs)
    if bytes.fromhex(w["new"]) != want:
        sys.exit("!! the boot stub from the template differs from the assembled one: regenerate registrar.json "
                 "(tools/gen_registrar.py) or check stub.S")
    return w


def parameter_block(fr, machines):
    """The runtime's parameter block for this build (registrar.S): header and one entry per machine."""
    lay, rt = fr["layout"], fr["runtime"]
    n, first = len(machines), lay["first"]
    nm, regs = first + n, rt["regs_at"]
    if n > rt["max_machines"]:
        sys.exit(f"!! {n} machines: the runtime's block holds {rt['max_machines']}")
    out = bytearray()
    out += bytes([n, first, first + n - 1, nm])
    out += g7.be32(76 + 5 * n)                        # last
    out += g7.be32(lay["data"] + 12 * nm)             # knob_tab
    out += g7.be32(regs + rt["regs_header"] + rt["entry_size"] * n)     # machines_end
    for i, m in enumerate(machines):
        e = bytearray(rt["entry_size"])
        e[0:4] = bytes([first + i, m["image"], 76 + 5 * i, 76 + 5 * i - 51])
        e[4:8] = g7.be32(lay["recs"] + 0x60 * i)      # rec
        e[8:12] = g7.be32(m.get("knob_hook", 0))      # knob_hook
        out += e
    if len(out) > rt["regs_header"] + rt["entry_size"] * rt["max_machines"]:
        sys.exit("!! parameter block too big")
    return bytes(out)


def frame(img, reg, n):
    """The registrar's part of a build of n added machines that does not depend on which machines (B3b, notes/61 §3):
    the writes (moved table references, bounds, the jumps and the call into the runtime's fixed entries, the MACHINES
    page's marks), the reloc of the Algorithm parameter's maximum, and the layout, the runtime, the stub template and
    the stock addresses fill() reads. A port of gen_macro.added_machine(tg=None) whose detours are the committed runtime
    (registrar.S); tools/gen_registrar.py --cycles commits it for n = 1 to 6 (frame.json) for the web flasher."""
    pay, first = gs.PAY_ALONE, 6
    rt = reg["runtime"]
    if int(rt["at"], 16) != gs.STUBS or int(rt["descn"], 16) != gs.DESCN or rt["marks_row"] != gs.MARKS_ROW:
        sys.exit("!! registrar.json was generated for another layout: run tools/gen_registrar.py")
    if not 1 <= n <= rt["max_machines"]:
        sys.exit(f"!! {n} machines: the runtime holds 1 to {rt['max_machines']}")
    nm = first + n
    top = nm - 1
    gs.set_rows(n)
    gs.check_room(n, nm)
    names_at, upd_at, rnd_at, map_at = gs.DATA, gs.DATA + 4 * nm, gs.DATA + 8 * nm, gs.DATA + 16 * nm
    entries = {k: int(v, 16) for k, v in rt["entries"].items()}
    writes = []

    def w(va, old, new_):
        if img[va - BASE:va - BASE + len(old)] != old:
            sys.exit(f"!! {va:#x}: {old.hex()} expected, {img[va - BASE:va - BASE + len(old)].hex()} found")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new_.hex()})

    def moveq(va, old, new_, reg_byte):
        w(va, bytes([reg_byte, old]), bytes([reg_byte, new_]))

    def jmp(va):
        return bytes.fromhex("4ef9") + g7.be32(va)

    red = sprites.redirect_write(gx.CAVE)
    w(BASE + red["off"], bytes.fromhex(red["old"]), bytes.fromhex(red["new"]))
    w(gx.HOOK, bytes.fromhex(gx.HOOK_OLD), jmp(gx.CAVE) + bytes.fromhex("4e71"))
    moved = {g7.DESC: gs.DESCN, g7.DESC + 8: gs.DESCN + 8, g7.DESC + 0x20: gs.DESCN + 0x20, g7.ROWS: gs.ROWSN,
             g7.CCROWS: gs.CCROWSN, g7.NAMES: names_at, g7.UPDATE_TAB: upd_at, g7.RENDER_TAB: rnd_at, gs.MAP: map_at}
    want = {g7.DESC: 34, g7.DESC + 8: 1, g7.DESC + 0x20: 2, g7.ROWS: 5, g7.CCROWS: 2, gs.MAP: 1, g7.RENDER_TAB: 1}
    for old, new_ in moved.items():
        rs = g7.refs32(img, old)
        if len(rs) != want.get(old, 1):
            sys.exit(f"!! references to {old:#x}: {len(rs)}")
        for va in rs:
            w(va, g7.be32(old), g7.be32(new_))
    jumps = g7.JUMPS + g8.JUMPS8
    for va in g7.BOUNDS:
        if va in {j[0] for j in jumps}:
            continue
        b0, b1 = img[va - BASE], img[va - BASE + 1]
        if b0 & 0xf1 != 0x70 or b1 not in (75, 76):
            sys.exit(f"!! {va:#x}")
        moveq(va, b1, b1 + 5 * n, b0)
    for va, reg_byte in ((0x400a7dba, 0x72), (0x400a7df4, 0x70), (0x4005a6a6, 0x72), (0x400147a4, 0x70),
                         (0x400148aa, 0x72), (0x400148b2, 0x70), (0x400a25e0, 0x70)):
        if img[va - BASE] != reg_byte or img[va - BASE + 1] not in (5, 6):
            sys.exit(f"!! bound {va:#x}")
        moveq(va, img[va - BASE + 1], top, reg_byte)
    moveq(0x4005a572, 5, 6, 0x72)
    w(0x4005a2b8, bytes.fromhex("487800c0"), bytes.fromhex("4878") + (32 * nm).to_bytes(2, "big"))
    if nm > gs.MARKS_ROW:
        w(0x400a26a2, bytes.fromhex("7850428545f9"), jmp(entries["marks"]))
    else:
        moveq(0x400a26e8, img[0x400a26e8 - BASE + 1], nm, 0x70)
    for va in (0x4001b69c, 0x400a40a6, 0x400a4fb0):
        moveq(va, 5, 1, 0x70)
    for va, old, sym in jumps:
        w(va, bytes.fromhex(old), jmp(entries[sym]))
    for va, old, sym in g7.CALLS:
        w(va, bytes.fromhex(old), bytes.fromhex("4eb9") + g7.be32(entries[sym]) + bytes.fromhex("4e71"))
    writes.sort(key=lambda x: x["off"])
    lo_, hi_ = g7.DESC - BASE, g7.DESC - BASE + g7.NDESC * g7.DSTRIDE
    final, orig = bytearray(img[lo_:hi_]), img[lo_:hi_]
    alg = g7.ALG_DESC * g7.DSTRIDE + 0x0c
    if struct.unpack_from(">I", final, alg)[0] != (first - 1) << 8:
        sys.exit("!! maximum of the Algorithm parameter")
    struct.pack_into(">I", final, alg, top << 8)
    reloc = [[f"{gs.DESCN + k:#x}", orig[k:k + 4].hex(), final[k:k + 4].hex()]
             for k in range(0, len(final), 4) if final[k:k + 4] != orig[k:k + 4]]
    return {"n": n,
            "layout": {"pay": pay, "bss_off": gm.BSS_OFF, "first": first, "stubs": gs.STUBS, "data": gs.DATA,
                       "descn": gs.DESCN, "recs": gs.RECS, "end_limit": gs.END_LIMIT, "image_end": BASE + gx.IMAGE_LEN,
                       "cave": gx.CAVE, "stub_room": sprites.zone(gx.CAVE)[1], "ndesc": g7.NDESC, "dstride": g7.DSTRIDE},
            "stock": {"names": g7.NAMES, "update": g7.UPDATE_TAB, "render": g7.RENDER_TAB, "map": gs.MAP,
                      "desc": g7.DESC, "snare_desc": g7.DESC + g7.SNARE_DESC * g7.DSTRIDE},
            "runtime": {"at": gs.STUBS, "hex": rt["hex"], "regs_at": int(rt["regs_at"], 16),
                        "regs_header": rt["regs_header"], "entry_size": rt["entry_size"],
                        "max_machines": rt["max_machines"]},
            "stub": reg["stub"],
            "writes": writes, "reloc": reloc}


def frame_alone(img, reg):
    """The frame of a build without an added machine (notes/66 §3): only extensions of stock machines, so nothing is
    registered; the boot hook and the stub copy the payload as in every build. Its writes are the freed sprite mask
    the stub lives in and the boot hook, as frame() writes them; the layout and the stub template are frame()'s."""
    pay, first = gs.PAY_ALONE, 6
    writes = []

    def w(va, old, new_):
        if img[va - BASE:va - BASE + len(old)] != old:
            sys.exit(f"!! {va:#x}: {old.hex()} expected, {img[va - BASE:va - BASE + len(old)].hex()} found")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new_.hex()})

    red = sprites.redirect_write(gx.CAVE)
    w(BASE + red["off"], bytes.fromhex(red["old"]), bytes.fromhex(red["new"]))
    w(gx.HOOK, bytes.fromhex(gx.HOOK_OLD), bytes.fromhex("4ef9") + g7.be32(gx.CAVE) + bytes.fromhex("4e71"))
    writes.sort(key=lambda x: x["off"])
    return {"n": 0,
            "layout": {"pay": pay, "bss_off": gm.BSS_OFF, "first": first, "stubs": gs.STUBS, "data": gs.DATA,
                       "descn": gs.DESCN, "recs": gs.RECS, "end_limit": gs.END_LIMIT, "image_end": BASE + gx.IMAGE_LEN,
                       "cave": gx.CAVE, "stub_room": sprites.zone(gx.CAVE)[1], "ndesc": g7.NDESC, "dstride": g7.DSTRIDE},
            "stub": reg["stub"], "writes": writes, "reloc": []}


def fill_alone(fr, img, blobs, bss_end):
    """The rest of a build without an added machine: the payload parts (the packages and the parts of the builder,
    nothing of the registrar's), the segments and the boot stub. Returns (writes, append) as fill() does."""
    lay = fr["layout"]
    parts = [{"dest": f"{at_:#x}", "hex": b_.hex()} for at_, b_ in sorted(blobs)]
    size = bss_end - lay["pay"]
    segs = gs.segments(parts, size)
    at = lay["image_end"]
    if at + sum(n_ for _, n_ in segs) > lay["end_limit"]:
        sys.exit(f"!! {sum(n_ for _, n_ in segs)} bytes added: the image would pass {lay['end_limit']:#x}")
    stub = boot_stub(fr, at, lay["pay"], size // 4, segs)
    if len(stub) > lay["stub_room"]:
        sys.exit("!! boot stub too big for its mask")
    if img[lay["cave"] - BASE:lay["cave"] - BASE + len(stub)] != b"\xff" * len(stub):
        sys.exit("!! the boot stub's place is taken")
    writes = [dict(w) for w in fr["writes"]] + [{"off": lay["cave"] - BASE, "old": "ff" * len(stub), "new": stub.hex()}]
    writes.sort(key=lambda x: x["off"])
    for a_, b_ in zip(writes, writes[1:]):
        if a_["off"] + len(a_["new"]) // 2 > b_["off"]:
            sys.exit(f"!! writes overlap at {BASE + b_['off']:#x}")
    return writes, {"at": f"{at:#x}", "dest": f"{lay['pay']:#x}", "size": size, "parts": parts, "reloc": [],
                    "pack": [[f"{a_:#x}", n_] for a_, n_ in segs]}


def frames(img, reg):
    """frame.json: the frames of n = 1 to the runtime's maximum, the writes they share listed once (B3b)."""
    per = {n: frame(img, reg, n) for n in range(1, reg["runtime"]["max_machines"] + 1)}
    for f in per.values():
        if any(f[k] != per[1][k] for k in ("layout", "stock", "runtime", "stub")):
            sys.exit("!! the frames differ beyond their writes and reloc")
    common = [w for w in per[1]["writes"] if all(w in f["writes"] for f in per.values())]
    out = {"schema": "model27-registrar-frame/0.1",
           "description": [
               "The registrar's part of a build that depends on the number of machines only (notes/61 §3): for n = 1 to",
               "6, the writes (moved tables, bounds, the jumps and the call into the runtime, the marks), the reloc of the",
               "Algorithm parameter's maximum; once, the layout, the runtime, the boot stub template and the stock",
               "addresses whose values fill() reads in the user's own MAIN OS. Written by tools/gen_registrar.py --cycles",
               "from compose.frame(); docs/flasher/composer.js fills it like compose.fill(). \"alone\": the writes of a",
               "build without an added machine, extensions of a stock machine only (compose.frame_alone(), notes/66 §3)."],
           "layout": per[1]["layout"], "stock": per[1]["stock"], "runtime": per[1]["runtime"], "stub": per[1]["stub"],
           "writes": common,
           "by_n": {str(n): {"writes": [w for w in f["writes"] if w not in common], "reloc": f["reloc"]}
                    for n, f in per.items()}}
    for n, f in per.items():                  # the split loses nothing: frame_of() gives each frame back
        back = frame_of(out, n)
        if back["writes"] != f["writes"] or back["reloc"] != f["reloc"]:
            sys.exit(f"!! frame.json would not give back the frame of {n} machines")
    alone = frame_alone(img, reg)             # notes/66 §3: extensions only, nothing registered
    if alone["layout"] != per[1]["layout"] or alone["stub"] != per[1]["stub"]:
        sys.exit("!! the frame without an added machine differs from the others beyond its writes")
    out["alone"] = {"writes": alone["writes"]}
    if frame_of(out, 0)["writes"] != alone["writes"]:
        sys.exit("!! frame.json would not give back the frame without an added machine")
    return out


def frame_of(frs, n):
    """One n's frame out of frame.json (the composer.js way of reading it); n = 0: extensions only (notes/66 §3)."""
    if n == 0:
        if "alone" not in frs:
            sys.exit("!! frame.json has no frame without an added machine: run tools/gen_registrar.py --cycles")
        return {"layout": frs["layout"], "stub": frs["stub"], "n": 0, "writes": list(frs["alone"]["writes"]),
                "reloc": []}
    if str(n) not in frs["by_n"]:
        sys.exit(f"!! no frame for {n} machines")
    fr = {k: frs[k] for k in ("layout", "stock", "runtime", "stub")}
    fr.update(n=n, writes=sorted(frs["writes"] + frs["by_n"][str(n)]["writes"], key=lambda x: x["off"]),
              reloc=frs["by_n"][str(n)]["reloc"])
    return fr


def fill(fr, img, machines, blobs, bss_end):
    """The rest of the registrar's part, what depends on the machines (B3b, notes/61 §3): the data block (names,
    update and render addresses, the strings), five descriptors per machine (SNARE's, read in the official image, with
    the knob fields set), the parameter block, the payload parts in their order, the segments and the boot stub.
    machines: name, image, decay, knobs, update, render (addresses); blobs: [(address, code and data)]; bss_end: end of
    the variables. docs/flasher/composer.js does the same from frame.json. Returns (writes, append)."""
    lay, stock, rt = fr["layout"], fr["stock"], fr["runtime"]
    n, first = len(machines), lay["first"]
    if n != fr["n"]:
        sys.exit(f"!! a frame for {fr['n']} machines, {n} given")
    for m in machines:
        if len(m["knobs"]) != 4:
            sys.exit(f"!! {m['name']}: {len(m['knobs'])} knobs; a machine has 4 and DECAY, five descriptors")
    nm = first + n
    u32 = lambda va: struct.unpack_from(">I", img, va - BASE)[0]
    map_at = lay["data"] + 16 * nm
    # --- data (as added_machine): names, update/render tables, machine -> record, strings
    strings = [m["name"] for m in machines] + [k[i] for m in machines for k in m["knobs"] for i in (0, 1)]
    at, addr = map_at + ((nm + 3) & ~3), {}
    for s_ in strings:
        if s_ not in addr:
            addr[s_] = at
            at += len(s_) + 1
    names = [u32(stock["names"] + 4 * i) for i in range(first)] + [addr[m["name"]] for m in machines]
    upd = [u32(stock["update"] + 4 * i) for i in range(first)] + [m["update"] for m in machines]
    rnd = [u32(stock["render"] + 4 * i) for i in range(first)] + [m["render"] for m in machines]
    data = bytearray()
    for t in (names, upd, rnd, range(1, nm + 1)):
        data += b"".join(g7.be32(x) for x in t)
    data += img[stock["map"] - BASE:stock["map"] - BASE + first] + bytes(range(first, nm)) + bytes(((nm + 3) & ~3) - nm)
    for s_ in addr:
        data += s_.encode("ascii") + b"\0"
    if lay["data"] + len(data) > lay["descn"]:
        sys.exit("!! data past DESCN")
    # --- 5 descriptors per machine, modelled on SNARE's
    ds, new = lay["dstride"], bytearray()
    for m in machines:
        for k, (long_, short, default, *rng) in enumerate(m["knobs"]):
            e = bytearray(img[stock["snare_desc"] + k * ds - BASE:][:ds])
            e[0x00:0x04] = g7.be32(6)
            if rng:
                e[0x08:0x0c], e[0x0c:0x10] = g7.be32(rng[0] << 8), g7.be32(rng[1] << 8)
            e[0x10:0x14] = g7.be32(default << 8)
            e[0x2c:0x30] = g7.be32(addr[long_])
            e[0x34:0x38] = g7.be32(addr[short])
            new += e
        e = bytearray(img[stock["snare_desc"] + 4 * ds - BASE:][:ds])
        e[0x10:0x14] = g7.be32(m["decay"] << 8)
        new += e
    # --- payload: the packages, the runtime, its parameter block, the data, the descriptors
    regs, code = rt["regs_at"], bytes.fromhex(rt["hex"])
    if lay["stubs"] + len(code) > regs:
        sys.exit("!! the runtime runs into its parameter block")
    block = parameter_block(fr, machines)
    if regs + len(block) > lay["data"]:
        sys.exit("!! parameter block past DATA")
    parts = [{"dest": f"{at_:#x}", "hex": b_.hex()} for at_, b_ in blobs if at_ < lay["stubs"]] + [
        {"dest": f"{lay['stubs']:#x}", "hex": code.hex()},
        {"dest": f"{regs:#x}", "hex": block.hex()},
        {"dest": f"{lay['data']:#x}", "hex": bytes(data).hex()},
        {"dest": f"{lay['descn']:#x}", "cycles": [f"{stock['desc']:#x}", f"{stock['desc'] + lay['ndesc'] * ds:#x}"]},
        {"dest": f"{lay['descn'] + lay['ndesc'] * ds:#x}", "hex": bytes(new).hex()},
    ] + [{"dest": f"{at_:#x}", "hex": b_.hex()} for at_, b_ in blobs if at_ >= lay["stubs"]]
    size = bss_end - lay["pay"]
    segs = gs.segments(parts, size)
    at = lay["image_end"]
    if at + sum(n_ for _, n_ in segs) > lay["end_limit"]:
        sys.exit(f"!! {sum(n_ for _, n_ in segs)} bytes added: the image would pass {lay['end_limit']:#x}")
    stub = boot_stub(fr, at, lay["pay"], size // 4, segs)
    if len(stub) > lay["stub_room"]:
        sys.exit("!! boot stub too big for its mask")
    if img[lay["cave"] - BASE:lay["cave"] - BASE + len(stub)] != b"\xff" * len(stub):
        sys.exit("!! the boot stub's place is taken")
    writes = [dict(w) for w in fr["writes"]] + [{"off": lay["cave"] - BASE, "old": "ff" * len(stub), "new": stub.hex()}]
    writes.sort(key=lambda x: x["off"])
    for a_, b_ in zip(writes, writes[1:]):
        if a_["off"] + len(a_["new"]) // 2 > b_["off"]:
            sys.exit(f"!! writes overlap at {BASE + b_['off']:#x}")
    return writes, {"at": f"{at:#x}", "dest": f"{lay['pay']:#x}", "size": size, "parts": parts,
                    "reloc": [list(r) for r in fr["reloc"]], "pack": [[f"{a_:#x}", n_] for a_, n_ in segs]}


def payload_writes(img, blobs, bss_end, reg):
    """A build of extensions only (notes/66 §3): frame_alone() then fill_alone(), the split the web flasher follows
    with frame.json's "alone"."""
    return fill_alone(frame_alone(img, reg), img, blobs, bss_end)


def registrar_writes(img, machines, blobs, bss_end, reg):
    """B2c: the registrar's writes and payload for the alone layout, without the toolchain: frame() then fill()
    (B3b: the split the web flasher follows). Returns (writes, append)."""
    return fill(frame(img, reg, len(machines)), img, machines, blobs, bss_end)


def compare_b1_(reg, writes, append, writes1, append1):
    """B2c's proof: the runtime's build against added_machine's (B1): the same writes except the sites that jump
    into the detours (g7.JUMPS, g8.JUMPS8, g7.CALLS, the marks jump) and the boot stub (its segment table), the
    same payload parts except the STUBS part, the same reloc, size, source and destination. Exits on a difference."""
    sites = {va - BASE for va, _o, _s in g7.JUMPS + g8.JUMPS8 + g7.CALLS} | {0x400a26a2 - BASE, gx.CAVE - BASE}
    w0 = {w["off"]: (w["old"], w["new"]) for w in writes if w["off"] not in sites}
    w1 = {w["off"]: (w["old"], w["new"]) for w in writes1 if w["off"] not in sites}
    if w0 != w1:
        bad = sorted(set(w0) ^ set(w1) | {k for k in w0 if k in w1 and w0[k] != w1[k]})
        sys.exit(f"!! compare-b1: writes differ at {[hex(BASE + k) for k in bad][:8]}")
    s0 = {int(w["off"]) for w in writes} & sites
    s1 = {int(w["off"]) for w in writes1} & sites
    if s0 != s1:
        sys.exit(f"!! compare-b1: different detour sites {[hex(BASE + k) for k in s0 ^ s1]}")
    regs = reg["runtime"]["regs_at"]
    p0 = [p for p in append["parts"] if p["dest"] not in (f"{gs.STUBS:#x}", regs)]
    p1 = [p for p in append1["parts"] if p["dest"] != f"{gs.STUBS:#x}"]
    if p0 != p1:
        sys.exit("!! compare-b1: payload parts differ beyond the STUBS part and the parameter block")
    for k in ("at", "dest", "size", "reloc"):
        if append[k] != append1[k]:
            sys.exit(f"!! compare-b1: append.{k} differs")
    size_of = lambda ap, dest: len(bytes.fromhex(next(p["hex"] for p in ap["parts"] if p["dest"] == dest)))
    print(f"  compare-b1: identical but the {len(s0)} detour sites, the runtime ({size_of(append, f'{gs.STUBS:#x}')} bytes "
          f"for B1's {size_of(append1, f'{gs.STUBS:#x}')} of detours) and the parameter block ({size_of(append, regs)} bytes)")


def shortcut_uses(mans, part):
    """The shortcuts the machines declare ("shortcut" in their uses), checked against the builder's list (notes/63
    §1.3, §5): [(machine's position, knob's position in the list, param)]. A value is 8.8 in a 16-bit word that a new
    sound, a sound saved before the machine had the shortcut and the official OS leave at 0: 0 is the default."""
    sc = part["shortcut"]
    lo, hi = sc["range"]
    out = []
    for i, m in enumerate(mans):
        seen = set()
        for u in m["uses"]:
            if u["point"] != "shortcut" or "press" in u:      # a switch: shortcut_presses()
                continue
            where = f"{m['id']}: shortcut {u.get('key')} + {u.get('knob')}"
            if u.get("key") != sc["key"] or u.get("knob") not in sc["knobs"]:
                sys.exit(f"!! {where}: not on the builder's list, {sc['key']} + {', '.join(sc['knobs'])} (notes/63 §1.3)")
            if u["knob"] in seen:
                sys.exit(f"!! {where}: declared twice")
            seen.add(u["knob"])
            prm = u["param"]
            names = (prm.get("long", ""), prm.get("short", ""))
            if not all(names) or not all(s_.isascii() and s_.isprintable() for s_ in names) or len(names[1]) > 4:
                sys.exit(f"!! {where}: a long name and a short name of 4 characters at most, in printable ASCII")
            rng = (prm.get("min"), prm.get("max"), prm.get("default", 0))
            if not all(type(v) is int for v in rng) or not lo <= rng[0] <= 0 <= rng[1] <= hi or rng[0] == rng[1]:
                sys.exit(f"!! {where}: integers min <= 0 <= max, from {lo} to {hi}")
            if rng[2] != 0:
                sys.exit(f"!! {where}: default {rng[2]}; a shortcut's default is 0, the value of a new sound, of a sound "
                         "saved before the machine had the shortcut and of the official OS (notes/63 §11)")
            out.append((i, sc["knobs"].index(u["knob"]), prm))
    return out


def shortcut_presses(mans, part):
    """The switches the machines declare ("shortcut" with "press" in their uses), checked against the builder's list
    (notes/63 §16): one byte per machine, bit 0 RETRIG + PUNCH, bit 1 RETRIG + GATE. A switch has no name, range or
    formatter: the machine shows it, if it wants, and reads it in k 32 of its note's sound."""
    sc = part["shortcut"]
    out = []
    for m in mans:
        bits = 0
        for u in m["uses"]:
            if u["point"] != "shortcut" or "press" not in u:
                continue
            where = f"{m['id']}: shortcut {u.get('key')} + {u['press']}"
            if u.get("key") != sc["key"] or u["press"] not in sc["presses"] or "knob" in u or "param" in u:
                sys.exit(f"!! {where}: not on the builder's list, {sc['key']} + {' or '.join(sc['presses'])}, a press "
                         "with no knob and no param (notes/63 §16)")
            bit = 1 << sc["presses"].index(u["press"])
            if bits & bit:
                sys.exit(f"!! {where}: declared twice")
            bits |= bit
        out.append(bits)
    return out


def shortcut_layer(img, part, mans, syms_of, uses, at, code_end, first, descn=None):
    """The shortcut layer of this build (notes/63 §3, B4b): the part's committed object placed at at, its data block
    right after its code, the knob lookup's vtable entry and the three sound record functions jumping into it, and
    when a machine declares a press (§16), the function PUNCH's and GATE's presses call and MainScreenView's LED
    method. A package's own hook on a record function, a wrapper over the same 8 bytes (SAMPLE's), becomes the next of
    the chain and its write is left out. descn: the descriptor table the OS uses, the registrar's moved copy by
    default, the stock table in a build without an added machine (notes/66 §3). Returns (blob, symbols, writes, the
    sites left out, info)."""
    b, d, sc, sites = part["build"], part["data"], part["shortcut"], part["sites"]
    if len(mans) > d["max_machines"]:
        sys.exit(f"!! {len(mans)} machines: the shortcut layer's tables hold {d['max_machines']}")
    presses = shortcut_presses(mans, part)
    path = object_path(part)
    if not path.is_file():
        sys.exit(f"!! {path} is missing: run tools/gen_parts.py")
    roots = b["roots"]
    lay = relocate.layout(path.read_bytes(), roots[0], roots[1], roots[2:], part["id"])
    data_at = align4(at + len(lay["code"]))
    # --- the record chain: one package's wrapper at most behind each record function
    nexts, skip = [], set()
    for s in sites["record"]:
        va = int(s["at"], 16)
        if img[va - BASE:va - BASE + 8] != bytes.fromhex(s["stock"]):
            sys.exit(f"!! {va:#x}: {s['stock']} expected, {img[va - BASE:va - BASE + 8].hex()} found")
        hooked = [(m, u["hook"]) for m in mans for u in m["uses"] if "hook" in u and int(u["hook"]["at"], 16) == va]
        if len(hooked) > 1:
            sys.exit(f"!! {', '.join(m['id'] for m, _ in hooked)} all hook {va:#x}: one wrapper behind the shortcut layer")
        if hooked:
            m, h = hooked[0]
            if h["op"] != "jmp" or h["stock"] != s["stock"]:
                sys.exit(f"!! {m['id']}: its hook at {va:#x} is not a wrapper over the function's first 8 bytes")
            nexts.append(syms_of[m["id"]][h["symbol"]])
            skip.add(va)
        else:
            nexts.append(0)
    # --- the data block: the header, the shortcuts per machine and knob, their strings
    nk, es = len(sc["knobs"]), d["entry_size"]
    entries = bytearray(es * nk * len(mans))
    str_at, strings, addr = data_at + d["entries"] + len(entries), bytearray(), {}
    for i, k, prm in uses:
        for s_ in (prm["long"], prm["short"]):
            if s_ not in addr:
                addr[s_] = str_at + len(strings)
                strings += s_.encode("ascii") + b"\0"
        fmt = int(sc["formatter"], 16)
        if "format" in prm:
            fmt = syms_of[mans[i]["id"]].get(prm["format"])
            if fmt is None:
                sys.exit(f"!! {mans[i]['id']}: formatter {prm['format']} is not a symbol of the package (keep it)")
        struct.pack_into(">IIiiiI", entries, es * (nk * i + k), addr[prm["long"]], addr[prm["short"]], prm["min"] << 8,
                         prm["max"] << 8, prm.get("default", 0) << 8, fmt)
    head = bytearray(d["entries"])
    for j, nxt in enumerate(nexts):
        struct.pack_into(">I", head, d["next"] + 4 * j, nxt)
    struct.pack_into(">I", head, d["descn"], gs.DESCN if descn is None else descn)
    head[d["first"]], head[d["count"]] = first, len(mans)
    head[d["presses"]:d["presses"] + len(presses)] = bytes(presses)
    data = bytes(head + entries + strings)
    if data_at + len(data) > code_end:
        sys.exit(f"!! the shortcut layer ends at {data_at + len(data):#x}, past {code_end:#x}")
    values = {"shortcut_data": data_at}
    code, syms, _ = relocate.apply(lay, at, at, code_end, {pp["symbol"]: values[pp["kind"]] for pp in b["patch_points"]})
    blob = code + bytes(data_at - at - len(code)) + data
    # --- the writes: the knob lookup's vtable entry, a jmp and a nop over each record function's first 8 bytes
    kv = sites["knob"]
    va, method = int(kv["vtable"], 16), int(kv["stock_ptr"], 16)
    if g7.refs32(img, method) != [va]:
        sys.exit(f"!! references to {method:#x}: {[hex(r) for r in g7.refs32(img, method)]}")
    for m in mans:
        if any("vtable" in u and int(u["vtable"]["at"], 16) == va for u in m["uses"]):
            sys.exit(f"!! {m['id']}: replaces the knob lookup ({va:#x}), which the shortcut layer takes")
    writes = [{"off": va - BASE, "old": g7.be32(method).hex(), "new": g7.be32(syms[kv["symbol"]]).hex()}]
    for s in sites["record"]:
        writes.append({"off": int(s["at"], 16) - BASE, "old": s["stock"],
                       "new": (bytes.fromhex("4ef9") + g7.be32(syms[s["symbol"]]) + bytes.fromhex("4e71")).hex()})
    if any(presses):                         # the press and the LEDs, only in the builds with a switch (notes/63 §16)
        for s in sites["press"]:
            va = int(s["at"], 16)
            if img[va - BASE:va - BASE + 6] != bytes.fromhex(s["stock"]):
                sys.exit(f"!! {va:#x}: {s['stock']} expected, {img[va - BASE:va - BASE + 6].hex()} found")
            for m in mans:
                if any("hook" in u and int(u["hook"]["at"], 16) == va for u in m["uses"]):
                    sys.exit(f"!! {m['id']}: hooks {va:#x}, which the shortcut layer takes for the switches")
            op = {"jmp": "4ef9", "jsr": "4eb9"}[s["op"]]
            writes.append({"off": va - BASE, "old": s["stock"],
                           "new": (bytes.fromhex(op) + g7.be32(syms[s["symbol"]])).hex()})
    out = {r: syms[r] for r in roots}
    out.update({pp["symbol"]: values[pp["kind"]] for pp in b["patch_points"]})
    info = dict(id=part["id"], code_at=at, code=len(code), data_at=data_at, data=len(data), shortcuts=len(uses),
                switches=sum(bin(x).count("1") for x in presses), chained=[f"{n:#x}" for n in nexts])
    return blob, out, writes, skip, info


def dispatch_layer(img, part, mans, syms_of, at, code_end, first):
    """The dispatchers of this build (notes/63 §4, B4c and B4d): each point of the part that two or more packages take
    (their vtable entries, or their hooks, at the same address) gets the part's dispatcher there, and the data block
    after the part's code lists each package's method by machine. A point one package takes keeps that package's own
    entry or hook. The part is placed whole as soon as one point is shared, so that it has one layout. Returns None
    when no point is shared, else (blob, symbols, writes, the sites left out, info)."""
    d, sites = part["data"], part["sites"]
    shared = {}
    for name, s in sites.items():
        kind = "vtable" if "vtable" in s else "hook"
        va = int(s[kind], 16)
        users = [(i, m, u[kind]) for i, m in enumerate(mans) for u in m["uses"]
                 if kind in u and int(u[kind]["at"], 16) == va]
        for _i, m, h in users:
            same = (h["stock_ptr"] == s["stock_ptr"] if kind == "vtable"
                    else h["stock"] == s["stock"] and h["op"] == s["op"])
            if not same:
                sys.exit(f"!! {m['id']}: its {kind} at {va:#x} is not the dispatcher's ({name})")
        if len(users) > 1:
            shared[name] = users
    if not shared:
        return None
    if len(mans) > d["max_machines"]:
        sys.exit(f"!! {len(mans)} machines: the dispatchers' tables hold {d['max_machines']}")
    path = object_path(part)
    if not path.is_file():
        sys.exit(f"!! {path} is missing: run tools/gen_parts.py")
    roots = part["build"]["roots"]           # the whole part: one layout, the one the web flasher embeds (B4e)
    lay = relocate.layout(path.read_bytes(), roots[0], roots[1], roots[2:], part["id"])
    data_at = align4(at + len(lay["code"]))
    block = bytearray(d["size"])
    block[d["first"]], block[d["count"]] = first, len(mans)
    for name, users in shared.items():
        for i, m, h in users:
            struct.pack_into(">I", block, sites[name]["table"] + 4 * i, syms_of[m["id"]][h["symbol"]])
    if data_at + len(block) > code_end:
        sys.exit(f"!! the dispatchers end at {data_at + len(block):#x}, past {code_end:#x}")
    values = {"dispatch_data": data_at}
    pps = part["build"]["patch_points"]
    code, syms, _ = relocate.apply(lay, at, at, code_end, {pp["symbol"]: values[pp["kind"]] for pp in pps})
    blob = code + bytes(data_at - at - len(code)) + bytes(block)
    writes, skip = [], set()
    for name in shared:
        s = sites[name]
        target = g7.be32(syms[s["symbol"]])
        if "vtable" in s:
            va, method = int(s["vtable"], 16), int(s["stock_ptr"], 16)
            if g7.refs32(img, method) != [va]:
                sys.exit(f"!! references to {method:#x}: {[hex(r) for r in g7.refs32(img, method)]}")
            writes.append({"off": va - BASE, "old": g7.be32(method).hex(), "new": target.hex()})
        else:
            va, old = int(s["hook"], 16), bytes.fromhex(s["stock"])
            if s["op"] != "jsr" or img[va - BASE:va - BASE + len(old)] != old:
                sys.exit(f"!! {va:#x}: {s['op']} {old.hex()} expected, {img[va - BASE:va - BASE + len(old)].hex()} found")
            writes.append({"off": va - BASE, "old": old.hex(), "new": (bytes.fromhex("4eb9") + target).hex()})
        skip.add(va)
    out = {r: syms[r] for r in roots}
    out.update({pp["symbol"]: values[pp["kind"]] for pp in pps})
    info = dict(id=part["id"], code_at=at, code=len(code), data_at=data_at, data=len(block),
                points={n: [m["id"] for _i, m, _h in users] for n, users in shared.items()})
    return blob, out, writes, skip, info


def fx_layer(img, part, effects, syms_of, at, code_end, desc_used):
    """The effect slots of this build (notes/68 §2, §11, §14; steps F1, F2 and F2b): for each slot that has an effect,
    the mixer's call of the stock effect goes to the part, and so does the handler's call at TRACK + a knob
    (0x4001f89a), where TRACK + Delay Time / Reverb Size step through the slot's effects, and the pattern header's
    loader and initializer (0x4005b4b0, 0x4006155e), which keep the pattern's choice. The data block after the part's code lists each
    slot's effects by id (entry 0 the stock effect, with its process and reset), the names and formatters of the slot's
    two parameters for each entry (the stock ones read from the image), the descriptor tables the names go into (the
    stock one and desc_used, the one the OS uses), then the part's state, then the strings. A slot without an effect
    keeps its stock call. Returns (blob, symbols, writes, the sites taken, info)."""
    d, slots = part["data"], part["slots"]
    path = object_path(part)
    if not path.is_file():
        sys.exit(f"!! {path} is missing: run tools/gen_parts.py")
    for fmt, (site, want) in part["formatter_sites"].items():   # the stock formatters, as the boot code installs them
        va = int(site, 16)
        if img[va - BASE:va - BASE + len(want) // 2] != bytes.fromhex(want):
            sys.exit(f"!! {va:#x}: {want} expected (the formatter {fmt}), {img[va - BASE:va - BASE + len(want) // 2].hex()} found")
    by_slot, seen = {name: [] for name in slots}, {}
    for m in effects:
        u = m["_effect"]
        if u["id"] in seen:
            sys.exit(f"!! {seen[u['id']]} and {m['id']}: the same effect id {u['id']}")
        seen[u["id"]] = m["id"]
        by_slot[u["point"]].append(m)
    roots = part["build"]["roots"]
    lay = relocate.layout(path.read_bytes(), roots[0], roots[1], roots[2:], part["id"])
    data_at = align4(at + len(lay["code"]))
    block, strings, str_at = bytearray(d["size"]), bytearray(), {}

    def string(text):
        if text not in str_at:
            str_at[text] = data_at + d["size"] + len(strings)
            strings.extend(text.encode("ascii") + b"\0")
        return str_at[text]

    def stock_word(desc, field):
        return struct.unpack_from(">I", img, g7.DESC + g7.DSTRIDE * desc + field - BASE)[0]
    info_slots = {}
    for k, (name, s) in enumerate(slots.items()):
        a, b = s["descriptors"]
        stock_fmt = [int(f, 16) for f in s["formatters"]]
        rows = [(0, int(s["stock_fn"], 16), 0,
                 (stock_word(a, 0x2c), stock_word(a, 0x34), stock_word(b, 0x2c), stock_word(b, 0x34),
                  stock_word(a, 0x30), *stock_fmt))]
        for m in sorted(by_slot[name], key=lambda m: m["_effect"]["id"]):
            u, syms = m["_effect"], syms_of[m["id"]]
            fmts = [stock_fmt[j] if p.get("format") is None else int(part["int_format"], 16) if p["format"] == "int"
                    else syms[p["format"]] for j, p in enumerate(u["params"])]
            pa, pb = u["params"]
            rows.append((u["id"], syms[u["process"]], syms[u["reset"]] if u.get("reset") else 0,
                         (string(pa["long"]), string(pa["short"]), string(pb["long"]), string(pb["short"]),
                          string(u["name"]), *fmts)))
        if len(rows) > d["entries"]:
            sys.exit(f"!! {len(rows) - 1} effects in the {name} slot: its table holds {d['entries'] - 1}")
        struct.pack_into(">I", block, d["slots"][k], len(rows))
        for i, (fid, fn, reset, names) in enumerate(rows):
            struct.pack_into(">III", block, d["slots"][k] + 4 + 12 * i, fid, fn, reset)
            struct.pack_into(">7I", block, d["names"] + 28 * (d["entries"] * k + i), *names)
        if by_slot[name]:
            info_slots[name] = [(m["_effect"]["id"], m["id"]) for m in sorted(by_slot[name], key=lambda m: m["_effect"]["id"])]
    struct.pack_into(">II", block, d["desc"], g7.DESC, desc_used)
    blob_data = bytes(block) + bytes(strings)
    if data_at + len(blob_data) > code_end:
        sys.exit(f"!! the effect slots end at {data_at + len(blob_data):#x}, past {code_end:#x}")
    values = {"fx_data": data_at}
    pps = part["build"]["patch_points"]
    code, syms, _ = relocate.apply(lay, at, at, code_end, {pp["symbol"]: values[pp["kind"]] for pp in pps})
    blob = code + bytes(data_at - at - len(code)) + blob_data
    writes, taken = [], set()
    sites = [s for name, s in slots.items() if by_slot[name]]
    sites += [part["track"], part["load"], part["init"]] if effects else []
    for s in sites:
        va, old = int(s["hook"], 16), bytes.fromhex(s["stock"])
        if img[va - BASE:va - BASE + len(old)] != old:
            sys.exit(f"!! {va:#x}: {old.hex()} expected, {img[va - BASE:va - BASE + len(old)].hex()} found")
        writes.append({"off": va - BASE, "old": old.hex(), "new": (bytes.fromhex("4eb9") + g7.be32(syms[s["symbol"]])).hex()})
        taken.add(va)
    out = {r: syms[r] for r in roots}
    out.update({pp["symbol"]: values[pp["kind"]] for pp in pps})
    info = dict(id=part["id"], code_at=at, code=len(code), data_at=data_at, data=len(blob_data), slots=info_slots)
    return blob, out, writes, taken, info


def fx_cost(effects, part):
    """The load of each slot that has effects (notes/68 §17), from the effects' declared cost.emulation and fxslot's:
    {slot: {dearest, steady, peak, share}}, steady the dearest effect's maximum plus what fxslot adds with an effect,
    less the stock effect's maximum; peak the block of a switch (the effect's first block, its reset, the stock
    effect's block of silence, what fxslot adds besides), less the same; or {slot: {missing: [ids]}} when a number
    is not declared."""
    pc = part.get("cost", {}).get("emulation", {})
    out = {}
    for point in FX_POINTS:
        mine = [m for m in effects if m["_effect"]["point"] == point]
        if not mine:
            continue
        stock, over = pc.get("stock", {}).get(point), pc.get("overhead", {}).get(point)
        costs = {m["id"]: m.get("cost", {}).get("emulation", {}) for m in mine}
        missing = [i for i, c in costs.items() if not all(isinstance(c.get(k), int) for k in ("first", "max", "reset"))]
        if missing or not stock or not over:
            out[point] = {"missing": missing + ([] if stock and over else ["fxslot"])}
            continue
        dearest = max(costs, key=lambda i: costs[i]["max"])
        steady = costs[dearest]["max"] + over["effect"] - stock["max"]
        peak = max(c["first"] + c["reset"] + over["silence"] + over["switch"] for c in costs.values()) - stock["max"]
        out[point] = {"dearest": dearest, "steady": steady, "peak": peak, "share": steady / BLOCK_INSTR}
    return out


def package_writes(m, img, syms, skip=()):
    """The package's own hooks (jsr/jmp into its code) and vtable entries, each checked against the stock bytes; the
    hooks and entries at the addresses in skip are left out (the shortcut layer chains them, a dispatcher takes
    them)."""
    writes = []
    for u in m["uses"]:
        if "hook" in u:
            h = u["hook"]
            va, old = int(h["at"], 16), bytes.fromhex(h["stock"])
            if va in skip:
                continue
            target = g7.be32(syms[h["symbol"]])
            new = (bytes.fromhex("4eb9") + target if h["op"] == "jsr"
                   else bytes.fromhex("4ef9") + target + bytes.fromhex("4e71"))
            if len(new) != len(old):
                sys.exit(f"!! {m['id']}: hook at {va:#x}: {len(new)} bytes for {len(old)}")
            if img[va - BASE:va - BASE + len(old)] != old:
                sys.exit(f"!! {m['id']}: {va:#x}: {old.hex()} expected, {img[va - BASE:va - BASE + len(old)].hex()} found")
            writes.append({"off": va - BASE, "old": old.hex(), "new": new.hex()})
        elif "vtable" in u:
            vt = u["vtable"]
            va, method = int(vt["at"], 16), int(vt["stock_ptr"], 16)
            if va in skip:
                continue
            if g7.refs32(img, method) != [va]:
                sys.exit(f"!! {m['id']}: references to {method:#x}: {[hex(r) for r in g7.refs32(img, method)]}")
            writes.append({"off": va - BASE, "old": g7.be32(method).hex(), "new": g7.be32(syms[vt["symbol"]]).hex()})
    return writes


def ram_claims(m):
    return [(int(a, 16), int(b, 16)) for u in m["uses"] if u["point"] == "memory.ram" for a, b in [u["range"]]]


def check_ram_claims(mans):
    """Two packages never claim the same RAM: a build where the claims of two of them overlap is refused."""
    claims = [(m["id"], lo, hi) for m in mans for lo, hi in ram_claims(m)]
    for i, (a, lo, hi) in enumerate(claims):
        for b, lo2, hi2 in claims[i + 1:]:
            if a != b and lo < hi2 and lo2 < hi:
                sys.exit(f"!! {a} and {b} claim the same RAM: {lo:#x}..{hi:#x} and {lo2:#x}..{hi2:#x}")


def folder_tweaks():
    """The tweaks of tweaks/model-cycles_OS1.13/ that have an id: what the conflicts are computed against."""
    out = []
    for f in sorted(DEV.glob("*.json")):
        if f.name == "device.json":
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        if t.get("id"):
            out.append(t)
    return out


def computed_conflicts(writes, ram, declared, tweaks=None):
    """Ids of the tweaks (by default the folder's) this build cannot be installed with: other bytes at the same
    address, or a payload in one of our RAM ranges. The same whole write is not a conflict (check_overlaps.py's
    rule)."""
    mine = {}
    for w in writes:
        for i, b in enumerate(bytes.fromhex(w["new"])):
            mine[w["off"] + i] = b
    ids = set(declared)
    for t in folder_tweaks() if tweaks is None else tweaks:
        tid = t.get("id")
        if not tid:
            continue
        clash = any(mine.get(w["off"] + i, b) != b
                    for w in t.get("writes", []) for i, b in enumerate(bytes.fromhex(w["new"])))
        ap = t.get("append")
        if ap and not clash:
            lo, hi = int(ap["dest"], 16), int(ap["dest"], 16) + ap["size"]
            clash = any(lo < b and a < hi for a, b in ram)
        if clash:
            ids.add(tid)
    return ids


def compose(img, ids, relocator="python", compare_ld=False, registrar="runtime", compare_b1=False, against=None,
            against_claims=None):
    """Builds the tweak for the machines named in ids, in that order. relocator: "python" places each
    package's committed object with tools/relocate.py (no toolchain), "ld" compiles and links it as B1 did;
    compare_ld does both and compares them byte for byte (the proof of the relocator). registrar: "runtime" writes
    the registrar's part itself from the committed runtime and stub template (B2c, no assembler), "b1" calls
    gen_macro.added_machine (assembles the detours per build); compare_b1 does both and compares (notes/60 §5.4).
    against: the tweaks the conflicts are computed against (default: the folder's); against_claims: their claims,
    {id: claims} (default: the folder's, tools/claims.py.tweak_claims). Returns (tweak, info)."""
    if not ids:
        sys.exit("!! name at least one package")
    if len(ids) != len(set(ids)):
        sys.exit("!! a package is named twice")
    mans = [load_manifest(i) for i in ids]
    added = [m for m in mans if m["_machine"]]           # numbered 6, 7, ... in the order given
    exts = [m for m in mans if m["_stock"]]              # extensions of a stock machine (notes/66 §3): CHORD
    effects = [m for m in mans if m["_effect"]]          # effects of the delay and reverb slots (notes/68 §2)
    if len({m["_index"] for m in exts}) != len(exts):
        sys.exit(f"!! {', '.join(m['id'] for m in exts)}: two packages extend the same stock machine")
    pay = gs.PAY_ALONE
    gs.set_base(pay)
    first = 6
    # the tables by machine (the shortcut layer's, the dispatchers'): from the extended stock machine when there is
    # one (CHORD, 5, right before the added machines), else from the first added machine; entry i is machine
    # tab_first + i. Without an extension this is the packages in the order given, as before.
    table = exts + added
    tab_first = exts[0]["_index"] if exts else first
    machines, blobs, syms_of, info_pkgs = [], [], {}, []
    lines = {}                               # the slots' lines (notes/68 §16): slot -> (address, bytes)
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        code_cursor, bss_cursor = pay, pay + gm.BSS_OFF
        for point in FX_POINTS:              # first in the variables, each as large as its largest effect asks
            need = max((m["_effect"].get("line", 0) for m in effects if m["_effect"]["point"] == point), default=0)
            if need:
                at = (bss_cursor + 15) & ~15
                lines[point] = (at, need)
                bss_cursor = at + need
        for m in mans:
            code_at, bss_at = align4(code_cursor), align4(bss_cursor)
            i = added.index(m) if m["_machine"] else None
            values = {"machine_index": first + i, "descriptor_base": 76 + 5 * i} if m["_machine"] else {}
            if m["_effect"] and m["_effect"].get("line"):
                values = {"fx_line": lines[m["_effect"]["point"]][0]}
            if relocator == "ld":
                blob, syms, bss_end = compile_package(m, tmp, code_at, bss_at, gs.STUBS, values)
            else:
                blob, syms, bss_end = place_package(m, code_at, bss_at, gs.STUBS, values)
            if compare_ld:
                if relocator == "ld":
                    b2, s2, e2 = place_package(m, code_at, bss_at, gs.STUBS, values)
                else:
                    b2, s2, e2 = compile_package(m, tmp, code_at, bss_at, gs.STUBS, values)
                same = blob == b2 and bss_end == e2 and all(s2.get(k) == v for k, v in syms.items() if k in s2)
                print(f"  compare-ld {m['id']:12s} {'identical' if same else 'DIFFERENT'}: relocator {len(blob)} bytes, "
                      f"ld {len(b2)} bytes, variables end {bss_end:#x} / {e2:#x}")
                if not same:
                    i_ = next((k for k in range(min(len(blob), len(b2))) if blob[k] != b2[k]), min(len(blob), len(b2)))
                    bad = {k: (f"{v:#x}", f"{s2[k]:#x}") for k, v in syms.items() if k in s2 and s2[k] != v}
                    sys.exit(f"!! {m['id']}: relocator and ld differ, first byte at +{i_:#x}; symbols {bad}")
            mc = m["_machine"]
            if mc:
                knobs = tuple((k["long"], k["short"], k["default"]) + ((k["min"], k["max"]) if "min" in k else ())
                              for k in mc["knobs"])
                machines.append(dict(name=mc["name"], image=mc["image"], decay=mc["decay_default"], knobs=knobs,
                                     update=syms[m["build"]["symbols"]["update"]],
                                     render=syms[m["build"]["symbols"]["render"]]))
            blobs.append((code_at, blob))
            syms_of[m["id"]] = syms
            fx = m["_effect"]
            info_pkgs.append(dict(id=m["id"], index=first + i if mc else m.get("_index"), desc=76 + 5 * i if mc else None,
                                  extends=m["_stock"]["machine"] if m["_stock"] else None,
                                  slot=fx["point"][3:] if fx else None, fx_id=fx["id"] if fx else None,
                                  code_at=code_at, code=len(blob), bss_at=bss_at, bss=bss_end - bss_at))
            code_cursor, bss_cursor = code_at + len(blob), bss_end
        layer, part = None, None             # the shortcut layer, in the builds whose machines declare a shortcut
        if any(u["point"] == "shortcut" for m in mans for u in m["uses"]):
            part = load_part("shortcuts")
            at = align4(code_cursor)
            layer = shortcut_layer(img, part, table, syms_of, shortcut_uses(table, part), at, gs.STUBS, tab_first,
                                   gs.DESCN if added else g7.DESC)
            blobs.append((at, layer[0]))
            code_cursor = at + len(layer[0])
        dispatch = None                      # the dispatchers, in the builds where two packages take one point
        if len(table) > 1:
            at = align4(code_cursor)
            dispatch = dispatch_layer(img, load_part("dispatch"), table, syms_of, at, gs.STUBS, tab_first)
            if dispatch:
                blobs.append((at, dispatch[0]))
                code_cursor = at + len(dispatch[0])
        fxs = None                           # the effect slots, in the builds that have an effect (notes/68 §2)
        if effects:
            at = align4(code_cursor)
            fxs = fx_layer(img, load_part("fxslot"), effects, syms_of, at, gs.STUBS, gs.DESCN if added else g7.DESC)
            blobs.append((at, fxs[0]))
            code_cursor = at + len(fxs[0])
        for m in mans:                       # a package's RAM claim must lie outside the payload
            for lo, hi in ram_claims(m):
                if lo < bss_cursor and pay < hi:
                    sys.exit(f"!! {m['id']}: the payload ({pay:#x}..{bss_cursor:#x}) runs into its RAM claim {lo:#x}..{hi:#x}")
        check_ram_claims(mans)
        reg = load_registrar()
        if not machines:                     # extensions and effects only: their payload copied at boot, nothing registered
            if registrar == "b1" or compare_b1:
                sys.exit("!! --registrar b1 and --compare-b1 need an added machine")
            writes, append = payload_writes(img, blobs, bss_cursor, reg)
        else:
            if registrar == "b1" or compare_b1:
                writes1, append1 = gm.added_machine(img, None, machines, tmp, blobs, bss_cursor)
                check_boot_stub(reg, writes1, append1)          # B2b: the template gives the same stub
            if registrar == "runtime":
                writes, append = registrar_writes(img, machines, blobs, bss_cursor, reg)
                if compare_b1:
                    compare_b1_(reg, writes, append, writes1, append1)
            else:
                writes, append = writes1, append1
    skip = (layer[3] if layer else set()) | (dispatch[3] if dispatch else set()) | (fxs[3] if fxs else set())
    for m in mans:
        writes += package_writes(m, img, syms_of[m["id"]], skip)
    for extra in (layer, dispatch, fxs):
        if extra:
            writes += extra[2]
    writes.sort(key=lambda x: x["off"])
    for a_, b_ in zip(writes, writes[1:]):
        if a_["off"] + len(a_["new"]) // 2 > b_["off"]:
            sys.exit(f"!! writes overlap at {BASE + b_['off']:#x}")
    ram = [(pay, bss_cursor)] + [r for m in mans for r in ram_claims(m)]
    declared = {c["with"] for m in mans for c in m.get("compat", {}).get("conflicts_declared", [])}
    if layer:                                # what the shortcut layer declares (none since notes/65 C2: computed)
        declared |= {c["with"] for c in part.get("conflicts_declared", [])}
    tid = "+".join(ids)
    holders = cl.build_holders(mans, part if layer else None)    # notes/65: the claims, rules 2 and 3
    if fxs:                                  # the effect slots' claims (the pattern header's bytes, notes/68 §14)
        fxc = cl.part_claims(load_part("fxslot"))
        holders.append(("fxslot", fxc, fxc, True))
    load = fx_cost(effects, load_part("fxslot")) if fxs else {}
    for point, c in load.items():             # notes/68 §17: a slot's dearest effect past FX_REFUSE is refused
        if c.get("steady", 0) > FX_REFUSE:
            sys.exit(f"!! the {point[3:]} slot: {c['dearest']} costs {c['steady']} instructions a block above the stock "
                     f"effect ({c['share']:.0%} of a block), past {FX_REFUSE} (notes/68 §17)")
    clash = cl.check_build(holders)
    if clash:
        sys.exit(f"!! the build's own claims clash (notes/65): {'; '.join(clash)}")
    pool = {t["id"] for t in (folder_tweaks() if against is None else against) if t.get("id")}
    others = {i: c for i, c in (cl.tweak_claims() if against_claims is None else against_claims).items()
              if i in pool and i not in ids}          # a package's own tweak: an alternative, its bytes say so
    by_claims = cl.claim_conflicts(holders, others)
    by_bytes = computed_conflicts(writes, ram, set(), against)
    conflicts = (by_bytes | declared | set(by_claims)) - {tid}
    tweak = {
        "id": tid,
        "order": min(m["order"] for m in mans),
        "name": " + ".join(m["name"] for m in mans) if len(mans) > 1 else mans[0]["name"],
        "description": [
            f"Composed by tools/compose.py (notes/59): {', '.join(placed(p) for p in info_pkgs)},",
        ] + ([
            "registered together through the registrar runtime (registrar.S, a parameter block per build) or, with",
            "--registrar b1, gen_macro.added_machine; each machine's code from tools/machines/<id>/",
        ] if machines else [
            "nothing registered: no added machine, the boot stub only copies the payload (notes/66 §3);",
            "each package's code from tools/machines/<id>/",
        ]) + [
            "(manifest.json), compiled and linked at build time at its place in the payload (%#x..%#x)." % (pay, bss_cursor),
            "Conflicts computed from the other tweaks: other bytes at the same address, a payload in this build's",
            "payload or in a claimed RAM range, or declared claims that clash (tools/claims.py, notes/65).",
        ] + [f"{m['id']}: {m['name']}" for m in mans],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "version": "+".join(m["version"] for m in mans),
        "conflicts": sorted(conflicts),
        "writes": writes,
        "append": append,
        "symbols": {k: f"{v:#x}" for m in mans for k, v in syms_of[m["id"]].items() if k in exported(m)},
    }
    if layer:
        li = layer[4]
        tweak["description"].insert(6, f"With the shortcut layer (tools/machines/shortcuts/, notes/63 §3) at {li['code_at']:#x}, "
                                       f"its data at {li['data_at']:#x}: {li['shortcuts']} shortcut(s)"
                                       + (f", {li['switches']} switch(es) (§16)." if li["switches"] else "."))
        tweak["symbols"].update({k: f"{v:#x}" for k, v in layer[1].items()})
    if dispatch:
        di = dispatch[4]
        tweak["description"].insert(6, f"With the dispatchers (tools/machines/dispatch/, notes/63 §4) at {di['code_at']:#x}, "
                                       f"their data at {di['data_at']:#x}: {', '.join(di['points'])}.")
        tweak["symbols"].update({k: f"{v:#x}" for k, v in dispatch[1].items()})
    if fxs:
        fi = fxs[4]
        slots = "; ".join(f"{n}: " + ", ".join(f"{mid} ({i})" for i, mid in e) for n, e in fi["slots"].items())
        tweak["description"].insert(6, f"With the effect slots (tools/machines/fxslot/, notes/68 §2) at {fi['code_at']:#x}, "
                                       f"their data at {fi['data_at']:#x}: {slots}"
                                       + "".join(f"; the {pt[3:]} slot's line at {a:#x}, {n} bytes"
                                                 for pt, (a, n) in lines.items()) + ".")
        tweak["symbols"].update({f"fx_line_{pt[3:]}": f"{a:#x}" for pt, (a, _n) in lines.items()})
        tweak["symbols"].update({k: f"{v:#x}" for k, v in fxs[1].items()})
    info = dict(pay=pay, end=bss_cursor, image=sum(n for _, n in append["pack"]), packages=info_pkgs,
                part=layer[4] if layer else None, dispatch=dispatch[4] if dispatch else None,
                fx=fxs[4] if fxs else None, fx_lines=lines, fx_load=load,
                claims=dict(by_claims={i: w for i, w in sorted(by_claims.items()) if i != tid},
                            declared_only=sorted(declared - by_bytes - set(by_claims) - {tid}),
                            views=cl.claim_views(holders, others)))
    return tweak, info


def build_syx(raw, tweaks, syntakt=None):
    """Applies the tweaks to the stock file with build.py's own steps; returns (syx, patched MAIN OS)."""
    stream, info = mcb.unwrap(raw)
    c = mcb.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    main_os, ops = mcb.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])
    dev = json.loads((DEV / "device.json").read_text(encoding="utf-8"))
    if sha(main_os) != dev["section_sha256"]:
        sys.exit("!! the MAIN OS is not the official 1.13")
    mcb.check_conflicts(tweaks)
    tweaks = sorted(tweaks, key=lambda t: t["order"])
    patched, dirty = mcb.apply_writes(main_os, tweaks)
    mcb.check_caves(main_os, tweaks, False, dirty, patched, dev.get("cave_refs_ok"))
    payload, _ = mcb.build_payload(tweaks, main_os, syntakt)
    orig_len = len(patched)
    patched += payload
    dirty += bytearray(b"\x01") * len(payload)
    new_s3 = aplib_grow.repack_grow(patched, ops, dirty, orig_len)
    if mcb.aplib.depack(new_s3)[0] != patched:
        sys.exit("!! the repacked MAIN OS reads back different")
    msg = c["blob"][:len(c["blob"]) - mcb.container.DIGEST_LEN]
    expect = c["blob"][len(c["blob"]) - mcb.container.DIGEST_LEN:]
    plain = []
    for s in c["sections"]:
        try:
            plain.append(mcb.aplib.depack(c["blob"][s["off"]:s["off"] + s["size"]])[0])
        except Exception:
            pass
    key = mcb.container.find_key(plain, msg, expect)
    if not key:
        sys.exit("!! HMAC key not found")
    blob = mcb.container.rebuild(c, {3: new_s3}, key)
    out = mcb.wrap(mcb.container.build_stream(blob, mcb.BYTES_PER_MSG), info["product"], info["start_seq"])
    stream2, _ = mcb.unwrap(out)
    c2 = mcb.container.parse(stream2)
    s3b = next(s for s in c2["sections"] if s["id"] == 3)
    if mcb.aplib.depack(c2["blob"][s3b["off"]:s3b["off"] + s3b["size"]])[0] != patched:
        sys.exit("!! the written file does not unpack to the patched MAIN OS")
    body = c2["blob"][:len(c2["blob"]) - mcb.container.DIGEST_LEN]
    mac = c2["blob"][len(c2["blob"]) - mcb.container.DIGEST_LEN:]
    if hmac.new(key, body, hashlib.sha256).digest() != mac:
        sys.exit("!! HMAC of the written file does not verify")
    return out, patched


def check_with_tool(tool, path, patched):
    res = subprocess.run([tool, "-i", str(path)], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"!! elektron-firmware-tool rejects the file (exit {res.returncode}):\n{res.stdout}{res.stderr}")
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([tool, "-i", str(path), "-d", "3", "-o", d], check=True, capture_output=True)
        if (pathlib.Path(d) / "section_3_MAIN_OS.bin").read_bytes() != patched:
            sys.exit("!! elektron-firmware-tool unpacks a different MAIN OS")
    print("  elektron-firmware-tool: checksums and HMAC ok, same MAIN OS")


def compare(tweak, path):
    """The composed tweak against a committed one: writes, payload, and the entry points' addresses."""
    ref = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    same = {"writes": tweak["writes"] == ref["writes"], "append": tweak["append"] == ref["append"],
            "symbols": all(tweak["symbols"].get(k) == v for k, v in ref.get("symbols", {}).items())}
    for k, ok in same.items():
        print(f"  compare {k:8s} {'identical' if ok else 'DIFFERENT'} to {pathlib.Path(path).name}")
    return all(same.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--machines", required=True, help="package ids under tools/machines/, in order, comma-separated")
    ap.add_argument("--with", dest="with_", default="", help="other tweaks of tweaks/ to install with it, comma-separated")
    ap.add_argument("--out", default=str(BUILD), help="folder for the .syx and the report (default: build/)")
    ap.add_argument("--emit", help="also write the composed tweak JSON here")
    ap.add_argument("--compare", help="a committed tweak JSON to compare writes and payload with")
    ap.add_argument("--tool", help="elektron-firmware-tool, for an independent check")
    ap.add_argument("--relocator", choices=("python", "ld"), default="python",
                    help="python: place the committed objects with tools/relocate.py (default); ld: compile and link (B1)")
    ap.add_argument("--compare-ld", action="store_true", help="do both and compare them byte for byte")
    ap.add_argument("--registrar", choices=("runtime", "b1"), default="runtime",
                    help="runtime: the committed registrar runtime and stub template (default, no assembler); b1: gen_macro.added_machine")
    ap.add_argument("--compare-b1", action="store_true", help="do both and compare them (notes/60 §5.4)")
    args = ap.parse_args()
    raw = pathlib.Path(args.cycles).read_bytes()
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        sys.exit("!! not the official MAIN OS 1.13")
    ids = [i.strip() for i in args.machines.split(",") if i.strip()]
    tweak, info = compose(img, ids, args.relocator, args.compare_ld, args.registrar, args.compare_b1)
    for p in info["packages"]:
        what = (f"effect {p['fx_id']} of the {p['slot']} slot" if p.get("slot")
                else f"extends {p['extends']} (machine {p['index']})" if p.get("extends")
                else f"machine {p['index']}, descriptors {p['desc']}..{p['desc'] + 4}")
        print(f"  {p['id']:12s} {what}, code {p['code']} bytes at {p['code_at']:#x}, variables {p['bss']} bytes at "
              f"{p['bss_at']:#x}")
    if info["part"]:
        p = info["part"]
        print(f"  {p['id']:12s} {p['shortcuts']} shortcut(s), {p['switches']} switch(es), code {p['code']} bytes at "
              f"{p['code_at']:#x}, data {p['data']} bytes at {p['data_at']:#x}, record chain {', '.join(p['chained'])}")
    if info["dispatch"]:
        p = info["dispatch"]
        print(f"  {p['id']:12s} code {p['code']} bytes at {p['code_at']:#x}, data {p['data']} bytes at {p['data_at']:#x}, "
              + "; ".join(f"{n}: {', '.join(ids)}" for n, ids in p["points"].items()))
    if info["fx"]:
        p = info["fx"]
        print(f"  {p['id']:12s} code {p['code']} bytes at {p['code_at']:#x}, data {p['data']} bytes at {p['data_at']:#x}, "
              + "; ".join(f"{n}: " + ", ".join(f"{mid} ({i})" for i, mid in e) for n, e in p["slots"].items()))
        for point, c in info["fx_load"].items():
            if "missing" in c:
                print(f"  warning, the {point[3:]} slot's load is not known: no cost declared by "
                      f"{', '.join(c['missing'])} (notes/68 §17)")
            else:
                warn = c["steady"] > FX_WARN or c["peak"] > FX_PEAK_WARN
                print(f"  {'warning, ' if warn else ''}the {point[3:]} slot's load: {c['dearest']} at "
                      f"most {c['steady']:+d} instructions a block on the stock effect ({c['share']:+.1%} of a block), "
                      f"{c['peak']:+d} in the block of a switch")
    print(f"  tweak {tweak['id']}: {len(tweak['writes'])} writes, payload {info['pay']:#x}..{info['end']:#x}, "
          f"{info['image']} bytes added to the image, {len(tweak['conflicts'])} conflicts computed")
    ci = info["claims"]
    if ci["by_claims"]:
        print(f"  by the claims (notes/65): {len(ci['by_claims'])}, "
              + "; ".join(f"{i}: {', '.join(w)}" for i, w in list(ci["by_claims"].items())[:6])
              + ("; ..." if len(ci["by_claims"]) > 6 else ""))
    if ci["declared_only"]:
        print(f"  declared only, no byte or claim shows it: {', '.join(ci['declared_only'])}")
    if ci["views"]:
        print("  warning, the same view drawn: " + "; ".join(f"{i}: {', '.join(w)}" for i, w in ci["views"].items()))
    ok = True
    if args.compare:
        ok = compare(tweak, args.compare)
    if args.emit:
        pathlib.Path(args.emit).write_text(json.dumps(tweak, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  wrote {args.emit}")
    others = []
    for tid in (t.strip() for t in args.with_.split(",") if t.strip()):
        path = next((f for f in DEV.glob("*.json") if f.name != "device.json"
                     and json.loads(f.read_text(encoding="utf-8")).get("id") == tid), None)
        if not path:
            sys.exit(f"!! unknown tweak {tid}")
        others.append(json.loads(path.read_text(encoding="utf-8")))
    out, patched = build_syx(raw, [tweak] + others)
    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    name = "+".join([tweak["id"]] + [t["id"] for t in others])
    path = outdir / f"model-cycles_OS1.13-{name}.syx"
    path.write_bytes(out)
    report = {"machines": ids, "with": [t["id"] for t in others], "stock_sha256": sha(raw),
              "main_os": {"sha256": sha(patched), "bytes": len(patched), "end": f"{BASE + len(patched):#x}"},
              "output": {"file": path.name, "sha256": sha(out), "bytes": len(out)}, "layout": info}
    path.with_suffix(".syx.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"  wrote {path} ({len(out)} bytes)\n  MAIN OS {len(patched)} bytes, SHA-256 {sha(patched)}")
    if args.tool:
        check_with_tool(args.tool, path, patched)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
