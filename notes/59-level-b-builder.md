# 59 — Level B: a builder that composes machines at build time (plan)

**Status: plan, 2026-10-21. Nothing of it is built.** Level B is Level B of the Cycles Mod Standard (draft 0.1): the
builder, not the author, assigns a machine's place, so that a machine is one file whatever it is combined with.
This note says what that means in this repository, what was checked in the code, and in which order to build it.
The alternative, pre-built combinations as `gen_acid_combos.py` makes them, is §9: it is what Level B replaces.
Scope: OS 1.13, no Model-TG, no Syntakt engines. Addresses are VAs of OS 1.13; payload offsets from `gs.PAY_ALONE`
(`0x43000000`).

## 0. In short

- **Today** every machine is a tweak whose places (machine index, descriptors, payload offsets, detours) were fixed
  when its generator ran. Two machines need a tweak of their own, `n` machines `2ⁿ − 1` tweaks (283 files
  upstream, 252 of them Syntakt combinations). `sampler`, `macro` and `acid` exclude each other for that reason
  alone.
- **Level B** makes a machine a *package*: a relocatable object (`.o`) plus a manifest. A *composer* takes the
  packages the user picked, lays them out, relocates them, fills one set of tables, computes what conflicts, and
  emits the same kind of tweak `tools/build.py` and the web flasher apply today. One file per machine, one build per
  selection, nothing pre-built.
- **Two facts from the code make it cheap** (§1): the objects carry only absolute 32-bit relocations, so relocating
  them is a loop over a table, in Python as in JavaScript; and the detours the registrar assembles per build depend
  on a handful of numbers per machine, so they can be assembled once and read a table.
- **Four increments** (§7): B1 a composer on the command line that reuses `added_machine` and the linker; B2 the
  table-driven registrar runtime and a relocator, so that nobody needs a toolchain to build; B3 the same in the web
  flasher, cards become packages; B4 the number registry and the dispatcher tables for shared hooks.
- **What does not change:** the tweak format, `build.py`, the flasher's checks (`REF_MODS`, `REF_MAINOS`), the mods
  that are not machines (they stay plain tweaks and compose with the machines as today, byte-checked).
- **Decision of 2026-10-21:** MACRO and ACID stay out of model27 for now. Their sources and generators remain in
  the repository, but no package is built for them. The second machine that every increment needs to prove
  composition is a **minimal reference machine** (§2a), never offered to users.

## 1. What was checked in the code

- **Relocations.** One-Shot's objects compiled with the build's own flags (`-fno-pic -fno-common
  -ffunction-sections -fdata-sections -O2`, `m68k-elf-gcc` 16.2) contain only `R_68K_32`: `pool.o` 69,
  `sampler.o` 31, `view.o` 17, `smp_filter.o` 8, `hooks.o` 4. No PC-relative relocation survives the assembler;
  calls between functions are absolute (`jsr abs.l`). A relocator therefore places each section, then writes
  `symbol address + addend` at each relocation's offset, 4 bytes big-endian. Nothing else.
- **The registrar's detours.** `gs.detours_asm(n, images, firsts, tg, lofi)` (`gen_syntakt_engines.py`) generates
  assembly per build, but every build-dependent instruction is one of: a constant per machine (`shown`: machine →
  picture; `record_at` / `record_of`: machine → record at `RECS + 0x60 i`, descriptor base − 51; `desc_machine`,
  `builder_row`: descriptor range → machine), a bound (`last = 76 + 5 n`, `first`, `top`, `DATA + 12 (first + n)`),
  or MACRO's lo-fi special case (`lofi`: one machine whose FUNC + PITCH edits FINE through three callbacks written
  into the FTUN interface object, `lofi_asm`). `map_state`, `cc_bounds`, `rec_build`, `knob_vec`, `small_icon`,
  `drum_icons` are the same code for every build apart from those numbers. With more than 7 machines `marks_asm`
  adds the second row of the MACHINES page.
- **The rest of `added_machine`** is arithmetic on `n`: the moved-table references (fixed addresses), the `moveq`
  bounds (`b1 + 5 n`, `top`, `nm`, `32 nm`), the jumps and calls into the stubs, the descriptor copy (`cycles`
  recipe) plus 5 new descriptors per machine, the `reloc` list, and the boot stub assembled from `stub.S` with the
  segment list (`PACK`).
- **The web flasher** (`builder.js`) is a port of `build.py`: it applies writes, checks caves, lays `append.parts`
  out and repacks. It does not assemble or link; whatever Level B needs in the browser has to be data, not code
  generation.

## 2. The package

One folder per machine under `tools/machines/<id>/`, as today, plus:

- `manifest.json` (Cycles Mod Standard §4; the SAMPLE example in STANDARD.md §7.1 is the model): `build.objects`
  (one or more `.o`), `build.symbols` (`update`, `render`), `build.patch_points`, `uses` (the `machine` entry with
  `image`, `decay_default`, `knobs`; the other points the package needs: `browser.open`, `sound.record`,
  `screen.tick`, `view.main`, `view.knob`, `memory.ram`; MACRO's `gesture` becomes a `knob_hook` callback, §3),
  `claims`, `cost`, `compat`, `tests`.
- The compiled `.o` files, **committed**, built by the package's own generator from its sources with the pinned
  toolchain and checked by `--check` (as the tweak JSONs are today). Users and the web flasher never compile.
- **Patch points** replace compile-time constants that depend on the build: One-Shot's `SAMPLE_MACHINE` (`pool.c`,
  `is_sample`) and `DESC_START` (`view.c`) become data words the composer writes (`"patch_points": [{"symbol":
  "smp_machine_index", "kind": "machine_index"}, …]`). `CUTOFF_OBJECT` stays constant (51 + 2: every added
  machine's knobs share SNARE's interface objects, `map_state`). `POOL_BASE` / `POOL_LIMIT` stay constants of the
  package (the pool is a `memory.ram` claim the composer checks against the payload's end).
- **A package's own hooks** (One-Shot's five `jsr`/`jmp` and two vtable entries) are claims with symbols; the composer
  writes them, as `gen_sampler.own_writes` does, once it knows the symbols' addresses.

Packages planned: `sampler` (first, its sources are already in `tools/machines/sampler/`) and the reference
machine of §2a. ACID and MACRO are not packaged for now (decision above); when they return, ACID needs nothing
from outside, MACRO needs the Braids clone at the pinned commit to *rebuild* its `.o`, not to use it.

## 2a. The reference machine

A second machine is needed to prove that the composer places two machines, assigns indices 6 and 7, descriptors
76 to 85, two records and two pictures, and that neither disturbs the other. Without MACRO and ACID that machine is
`tools/machines/refmachine/` (working name): the smallest 4-knob machine that follows the contract of the standard
§2, a few hundred bytes of C: one sine or one noise burst through the stock chain, four knobs with plain names, one
picture, no hooks, no claims beyond its payload. It is MIT, model27's own, and serves three purposes: the proof of
every increment, the template a new author copies (the standard's "core machine" made real), and the measure of
the registrar's own cost. It is never in `OFFERED`.

## 3. The registrar runtime

The detours become one assembled blob with a **parameter block** the composer fills, instead of assembly generated
per build:

```
struct regs {
  u8  n, first, top, last;          /* machines added, first index, highest index, first free descriptor */
  u32 data, descn, rows, recs;      /* the moved tables (today DATA, DESCN, ROWSN, RECS of gs.LAYOUT) */
  struct { u8 image; u8 first_desc; u16 pad; u32 record; u32 knob_hook; } machine[6];
};
```

`shown`, `record_at`, `record_of`, `desc_machine`, `builder_row`, `knob_vec`, `map_state`, `cc_bounds` read the
block instead of carrying their constants in `moveq` chains; `marks_asm` is always present and reads `n`. MACRO's
lo-fi is a `knob_hook`: `knob_vec` calls the machine's hook when one is set, and the hook (MACRO's own code, today
`lofi_asm`, moved into its package) installs its three callbacks. The boot stub reads its segment list from a table
at a fixed place in the payload instead of `segs.inc`. The runtime is a package of its own (`tools/machines/
registrar/`), assembled once, committed, checked.

Proof of the runtime: for every selection the old generator can build (sampler alone; the reference machine
alone through a generator of its own, written like `gen_sampler.py`), the composed image behaves like the generated
one in `tools/emu` (boot, MACHINES page, knob rows, records, machine locks, each machine's sound identical to its
standalone tweak), and for the pair the two machines behave like each alone. Bytes differ where the detours differ;
behaviour must not.

## 4. The composer

`tools/compose.py` (Python, standard library plus the ELF reader):

1. reads the manifests of the chosen packages and the plain tweaks chosen with them;
2. **orders** the machines (B1: the order given; B4: by registry id) and assigns `first + i`, `76 + 5 i`;
3. **lays out** the payload: the registrar runtime, then each package's sections one after the other from `pay`
   (code, rodata, data) with BSS above the tables at `+0x36000` as MACRO does; refuses when the end crosses a
   `memory.ram` claim (SAMPLE's pool at `0x43800000`) or `gs.STUBS`;
4. **relocates**: B1 with `m68k-elf-ld` and a generated linker script (as `gen_sampler.compile_machine` does
   today); B2 with its own `R_68K_32` loop over the ELF relocation tables;
5. writes the **patch points** and fills the **parameter block**;
6. produces the **writes**: B1 by calling `gm.added_machine(img, None, machines, tmp, blobs, bss_end)` unchanged
   (it already takes the list); B2 by its own arithmetic (§1, third bullet) plus the packages' hooks;
7. **conflicts**: the computed rule of `gen_sampler.py` (other bytes at the same address, a payload or a claim in
   the same memory), applied to the composed writes against every tweak of the folder, plus claim-level rules of
   the standard §4.4 as the manifests fill up;
8. emits one tweak JSON for the selection (`id` = the package ids joined by `+`, `order` = the lowest), which
   `build.py` applies like any other, or applies it straight away with `build.py`'s functions, as One-Shot's
   `machine/build.py` does.

The composer never needs the Braids clone or any source: it reads committed `.o` files.

## 5. The web flasher (B3)

- `tweaks.js` embeds packages (manifest + `.o` as hex) and the registrar runtime instead of pre-built machine
  tweaks; the other mods stay embedded as tweaks. The bundle shrinks to the sum of the packages.
- `builder.js` gets the composer's steps 2 to 6 in JavaScript: ELF reader, `R_68K_32` loop, layout, parameter block,
  writes. The Python composer is the reference; `tools/webbuild_check.sh` compares the two byte for byte, as it
  does for `build.py` today.
- Cards: one per package; `joins` / `versions` disappear for machines, the page simply composes what is ticked.
  `REF_MODS` becomes the hash of each package's bytes; `REF_MAINOS` keeps its sample (each card alone, every pair,
  the largest sets), built by `ref_mainos.py` through the composer.
- Fast flashing, the Official firmware and Samples OS tabs: unchanged.
- Refined by measurement in [notes/61](61-level-b3-web-flasher.md) (2026-10-22): the page gets each object placed
  once at offset 0 with its relocations instead of an ELF reader, and the registrar as a frame per number of machines
  instead of a port of its arithmetic; the composer goes into a `composer.js` of its own, checked against
  `compose.py` by `tools/webcompose_check.sh`.

## 6. Registry and shared hooks (B4)

- **Stable machine ids** (standard §5.1): the registry file names a permanent id per package; the composer orders
  by id and fills the gaps with a placeholder entry (a silent machine named `----`), so that a sound saved with
  SAMPLE as machine 6 stays SAMPLE whatever else is ticked. Until B4, ids are the order given (B1) with SAMPLE
  first, which keeps SAMPLE at 6 in every selection. *Decided 2026-10-22 ([notes/62](62-level-b4-stable-machine-ids.md)
  §9): not built; the order given stays, and a project belongs to its build.*
- **Shared hooks** (`sound.record`, `screen.tick`, `view.*`, `browser.open`): today only SAMPLE uses them among the
  offered packages. The first second package that needs one brings the dispatcher table of the standard §3.3 (a
  fixed table of callbacks in the runtime's payload, walked by code assembled once).

## 7. Increments, each one usable

1. **B1, composer with the linker** (needs the m68k toolchain, like every generator today): `tools/compose.py`,
   `tools/machines/sampler/manifest.json`, the reference machine and its manifest. Reuses `added_machine` and
   `own_writes`. Done when `compose.py --machines sampler` reproduces `27-sampler.json`'s MAIN OS byte for byte
   (same code, same place, same detours: it must), and `compose.py --machines sampler,refmachine` and
   `refmachine,sampler` build, pass `check_overlaps.py` and `registry.py`, and play both machines in the emulator
   (SAMPLE identical to SAMPLE alone, the reference machine identical to itself alone).
2. **B2, no toolchain at build time**: the registrar runtime (§3) as a package; the ELF reader and `R_68K_32`
   relocator in Python; committed `.o` files with `--check`. Done when B1's images are reproduced in behaviour
   (emulation proof, §3) and the composer runs with `python3` alone.
   Detailed plan, measurements and proofs: [notes/60](60-level-b2-relocator-runtime.md) (2026-10-21).
3. **B3, the web flasher** (§5). Done when `webbuild_check.sh` shows JavaScript and Python composing the same bytes
   for every card alone and every pair, and the page flashes a composed selection.
   Detailed plan, measurements and proofs: [notes/61](61-level-b3-web-flasher.md) (2026-10-22).
4. **B4, registry and dispatchers** (§6), when a second package needs a shared hook or a stable id.
   Plan for the stable ids, measurements and the dispatchers as an outlook: [notes/62](62-level-b4-stable-machine-ids.md)
   (2026-10-22); decided the same day: option C, no stable ids (§9 there). The dispatchers and the machine
   shortcuts, proven by a second reference machine: [notes/63](63-level-b4-shortcuts-dispatchers.md) (plan, 2026-10-22).

Hardware tests follow every increment, by the maintainer, before anything is called tested.

## 8. Preconditions, unchanged from before

- **Toolchain:** one pinned compiler for every package, `m68k-elf-gcc` 16.2 (Homebrew): SAMPLE and the reference
  machine are built with it today. (Upstream's `25-macro.json` and `26-acid.json` were compiled with
  `m68k-linux-gnu-gcc` 13.3 and `gen_acid.py --check` fails here; that only matters if they return.)
- **Braids:** only needed if MACRO returns (a clone of `pichenettes/eurorack` at `08460a6` with stmlib `e3bd7c9`
  in `vendor/eurorack`, git-ignored; the sandbox cannot clone it). Not a precondition now.
- **Unicorn:** the proofs need it; this session's Python 3.14 has no wheel. A Python 3.12 or 3.13 virtualenv, or
  the maintainer's own environment.
- **Which machines are offered** stays the maintainer's call; MACRO and ACID are out for now, so B1 and B2 are
  proven with SAMPLE and the reference machine, and the flasher keeps its one card until a second machine worth
  offering exists.

## 8a. B1 built (2026-10-21)

`tools/compose.py`, `tools/machines/sampler/manifest.json`, `tools/machines/refmachine/` (`refmachine.c`, 1 304 bytes
of code, 192 of variables, five `R_68K_32` relocations, no undefined symbol) and `tools/gen_refmachine.py`
(`28-refmachine.json`, 116 writes, the reference machine alone). Results:

- `compose.py --machines sampler` gives `27-sampler.json`'s writes, payload and symbols **byte for byte**, the MAIN
  OS `7e40344e…` of One-Shot 0.7, and even the same `.syx` as One-Shot's own build (`c0c44621…`): the composer's
  path for one machine is the generator's path.
- `sampler,refmachine` and `refmachine,sampler` build (MAIN OS `0e79c89d…` and `1f10fb27…`: the order changes the
  indices, so the bytes), 295 160 bytes of payload, 37 636 added to the image; with `arp` and `trig-hold` too.
  The emitted pair tweak, dropped into `tweaks/`, is applied by `build.py -t sampler+refmachine` to the same MAIN
  OS, so the flasher could take it as it is.
- `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check` pass with `28-refmachine.json` in the
  folder (285 tweaks). A composed tweak's conflict list is computed against the folder at compose time: composed
  before `28-refmachine.json` existed, the pair did not name `refmachine` and the checker said so; recomposed, it
  does. A composed tweak is a build, valid for the folder it was built from.
- digiemu (maintainer, 2026-10-21): the reference machine alone (`222ddeec…`) and the pair `sampler+refmachine`
  (`06155a2a…`) run; REF plays, and SAMPLE in the pair plays the files put in `/incoming` as it does alone. "Passt."
- Not done here: the emulation proof (no Unicorn in this Python) and the hardware test. Nothing is offered in the
  flasher.

## 9. The way not taken: pre-built combinations

`gen_acid_combos.py` builds MACRO and ACID into one tweak at fixed offsets (ACID at `+0x76000`, variables at
`+0x78000`); the same could be done for SAMPLE (`+0x7a000` / `+0x82000`, the pool untouched), with SAMPLE first in
the list so that it keeps index 6, three new files `27-sampler-macro`, `27-sampler-acid`, `27-sampler-macro-acid`,
cards with `sampler` as host (`versions`) and MACRO and ACID joining it. It works, it is what upstream would do,
and it is one more round of files that doubles with the next machine. Level B spends the same effort once.
