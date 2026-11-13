# 60 — Level B, step 2: a relocator and a table-driven registrar, no toolchain at build time (plan)

**Status: plan, 2026-10-21; B2a (§9), B2b (§10) and B2c (§11, 2026-10-22) built: the composer runs with `python3` alone; tested on the Model:Cycles on 2026-10-22, the pair (§12) and SAMPLE alone from the page (§13); proven in emulation with Unicorn (§14).** This is increment B2 of [notes/59](59-level-b-builder.md)
(§3 the registrar runtime, §4 steps 4 and 6 of the composer, §7 item 2), written after B1 landed (`91edc68`:
`tools/compose.py`, the manifests, the reference machine, `28-refmachine.json`). It says what B1 still needs the
m68k toolchain for, measured in the code, how each of those uses becomes committed data plus Python, in which order
to build it, and how to prove each piece without an emulator first. Addresses are VAs of OS 1.13; payload offsets
from `gs.PAY_ALONE` (`0x43000000`); sizes measured on 2026-10-21 with `m68k-elf-gcc` 16.2.

## 0. In short

- **B1 calls the toolchain in two places.** (a) `compose.compile_package`: `gcc`, `ld`, `objcopy`, `nm` for every
  package, every build. (b) `gm.added_machine`: two `assemble()` calls, the detours (`gs.detours_asm`, 606 bytes
  for one machine, 774 for two, 1 094 for six) and the boot stub (`stub.S`, 64 bytes of code plus 8 per segment).
  Everything else in `added_machine` is Python already: the data block, the five descriptors per machine, the
  moved-table references, the 43 bounds, the 7 jumps and the call, the payload parts and the conflict list.
- **B2 replaces both.** (a) becomes a committed relocatable object per package and a relocator in Python (the
  objects carry only `R_68K_32`, §1); (b) becomes two committed binaries with parameter areas, a **registrar
  runtime** that loops over a machine table instead of carrying its constants in `moveq` chains, and a **stub
  template** whose three immediates and segment table the composer fills. After B2, `compose.py` runs with
  `python3` alone; the toolchain is needed only by the generators that build the committed pieces
  (`gen_sampler.py`, `gen_refmachine.py`, a new `gen_registrar.py`), each with `--check`.
- **Two proofs need no emulator.** The relocator is proven against `ld` byte for byte: with the same section order
  and only absolute relocations, the two must produce the same bytes (§3). The runtime is proven by a differential
  against B1: for every selection, the same writes and the same payload except the detour part and the eight sites
  that jump to it (§5). Behaviour is then digiemu and the device; Unicorn when a Python with a wheel exists (§8).
- **Three sub-steps, each committed alone:** B2a the relocator and patch points as symbols, B2b the stub template,
  B2c the runtime and the composer's own writes. After B2c, `27-sampler.json` and `28-refmachine.json` are
  regenerated through the composer (their detour bytes change, nothing else), so SAMPLE alone needs a hardware
  test again before a release.

## 1. What was measured (2026-10-21)

| What | Measured |
|---|---|
| `refmachine.o` | 2 388 bytes; 5 relocations, all `R_68K_32`, in `.rela.*` sections (RELA: type, symbol, addend); sections `.text.ref_update` 0x286, `.text.ref_render` 0x25e, `.rodata.semi` 0x34, `.bss.trk` 0xc0 |
| SAMPLE's 9 objects after `ld -r` | one object of 39 100 bytes; 69 input sections kept apart (`-ffunction-sections`); 132 relocations, all `R_68K_32`, 101 against section symbols, 31 against named symbols; no undefined symbol; alignments 1 and 2 |
| ELF | ELF32, big endian, `e_machine` 68000, type REL. No `pyelftools` here; the reader is `struct` (about 80 lines) |
| Detours (`gs.detours_asm`, `tg=None`, no lo-fi) | n = 1: 606 bytes; n = 2: 774; n = 3: 854; n = 6: 1 094. Room `STUBS..DATA` 2 048 bytes |
| Per-build instructions in the detours | `map_state` (`cmp.l #last`), `cc_bounds` (`moveq #top`), `shown` (one compare per machine), `record_at` / `record_of` and `rec_i` (one compare and one `lea RECS + 0x60 i` per machine, `moveq #first_desc − 51`), `knob_vec` (`top`, `first`, `lea DATA + 12 nm`), `desc_machine` / `builder_row` (two compares per machine), `marks` (`moveq #nm`, only when nm > 7). Constant: `state_at`, `state_connect`, `drum_icons`, `small_icon`, `rec_build` |
| Boot stub (`PACK`, 4 segments) | 104 bytes: 64 of code, 8 per segment, 8 of terminator. Immediates: `lea PAYLOAD_DST` at offset 2, `move.l #PAYLOAD_LONGS` at 8, `lea PAYLOAD_SRC` at 20; the segment table follows the code (`lea segs(%pc)`). Room: `STUB_END − CAVE` = 192 bytes, so 15 segments at most (today 4 or 5) |
| Python | 3.14.2; neither `unicorn` nor `elftools` installed; no 3.12/3.13 on the path |
| Patch points in One-Shot | `SAMPLE_MACHINE` in `pool.c:60` and `view.c:172`; `DESC_START` in `view.c:190` (and `DESC_LENGTH`); both `#ifndef` defaults 6 / 76 |

## 2. The package after B2: a committed object

- **`build.objects`** (standard §4: `objects`, `symbols`, `patch_points`) names one relocatable object,
  `tools/machines/<id>/<id>.o`, produced by the package's generator: compile the sources with the package's flags,
  then `m68k-elf-ld -r` into one file. The object is **committed**, like the tweak JSONs are, and `--check`
  rebuilds and compares it. The sources stay next to it, for reading and for rebuilding. `build.sources`,
  `cflags`, `include` and `defines` stay in the manifest as the recipe of the object; `symbols` and `keep` are the
  relocator's roots.
- **Patch points become symbols, not defines.** Today `SAMPLE_MACHINE` and `DESC_START` are compile-time constants,
  so an object compiled once would carry one index for ever. In B2 the package declares them as undefined symbols
  whose *address* is the value:

  ```c
  extern char cm_machine_index[];                     /* defined by the composer, value = the index */
  #define SAMPLE_MACHINE ((int)(long)cm_machine_index)
  ```

  The compiler emits `move.l #cm_machine_index, %d0` with an `R_68K_32` against the undefined symbol, and the
  composer resolves it like `ld --defsym` would. Cost: 6 bytes instead of 2 at three sites, nothing at run time
  beyond that. Manifest: `"patch_points": [{"symbol": "cm_machine_index", "kind": "machine_index"}, {"symbol":
  "cm_descriptor_base", "kind": "descriptor_base"}]` (the standard's table says symbol + kind; its SAMPLE example
  still shows the define names and is aligned when the standard moves to 0.2). The relocator refuses any other
  undefined symbol by name. For the B1 path (`ld`) the same manifest entries become `--defsym` arguments.
- **This touches One-Shot.** `pool.h` and `view.c` are One-Shot's; the change is a few lines, keeps One-Shot's own
  `machine/build.py` working (it passes `--defsym`), and ships as One-Shot 0.8, which model27 then pins (the
  `UPSTREAM_COMMIT` of `gen_sampler.py`). The reference machine has no patch point.
- **The object's fingerprint.** The `.comment` section of the object names the compiler (`GCC: (GNU) 16.2.0`);
  `--check` reads it, so a package rebuilt with another compiler is refused before the bytes are compared, and the
  message says which compiler the committed object came from.

## 3. B2a: the relocator

`tools/relocate.py` (standard library only), used by `compose.py` in place of `compile_package` and returning the
same triple (blob from `code_at` to the end of the data, symbols, end of the variables):

1. **Read** the ELF32 big-endian object: section headers, `.symtab` + `.strtab`, every `.rela.*` section (`r_offset`,
   `r_info` → symbol index and type, `r_addend`). Refuse a type other than `R_68K_32` (1), naming the section and
   offset.
2. **Collect garbage** like `ld --gc-sections`: roots are the sections of `symbols.update`, `symbols.render` and
   every `keep` symbol; follow relocations from root sections to the sections they reference (section symbols
   and named symbols alike); drop the rest. Without this, SAMPLE's unused helpers would be placed (B1's `ld`
   drops them, so the comparison of step 6 would fail; that is how the rule is checked).
3. **Place** the kept sections in B1's order, which is the linker script's: the section holding `update`, then the
   one holding `render`, then the other `.text*` in file order, then `.rodata*`, then `.data*`, each at its
   `sh_addralign` (1 or 2 here; `ld` honours the same field), from `code_at`; `.bss*` from `bss_at`, not emitted.
   Refuse when the code end passes `code_end` (`gs.STUBS`) as today.
4. **Resolve** every symbol: section symbol → the section's placed address; defined symbol → its section's address
   plus `st_value`; undefined symbol → the composer's value for its patch point, else an error naming it.
5. **Apply**: for each relocation, write `S + A` as 4 bytes big endian at the placed address of the section plus
   `r_offset`. Nothing else: no PC-relative, no 16-bit, no GOT.
6. **Prove against `ld`**: `compose.py --compare-ld` builds every package both ways (B1's `compile_package` and
   the relocator over the object `ld -r` produced from the same compile) and compares blob, symbols and BSS end
   **byte for byte**, for `sampler`, `refmachine`, and the two pairs. Because every relocation is absolute, equal
   placement means equal bytes; a difference is a placement or alignment rule the relocator got wrong, and the
   diff says where. This is B2a's done criterion and needs no emulator and no device.

About 200 lines of Python. The relocator is also the specification of B3's JavaScript relocator (notes/59 §5):
the same steps over the same object bytes.

## 4. B2b: the boot stub template

`gen_registrar.py` assembles `stub.S` once with `PACK` and placeholder values, and commits the 64 bytes of code
with the offsets of its three immediates (2: destination, 8: length in longs, 20: source) in
`tools/machines/registrar/registrar.json`. The composer copies the template, writes the three values, appends the
segment table (`.long address, longs` per segment, then `0, 0`) and checks `CAVE + length ≤ STUB_END` (192 bytes,
15 segments). Proof: for every B1 selection the result equals the stub B1 assembles, byte for byte (same source,
same values). `stub.S` keeps its other variants (`APLIB`, `BOOT2`, `CHAIN_TO`, the SRAM copies) for the Syntakt and
Model-TG generators; B2 uses the plain `PACK` form only.

## 5. B2c: the registrar runtime

### 5.1 Code assembled once, a parameter block filled per build

`tools/machines/registrar/registrar.S`, written by hand from `gs.detours_asm(n, …, tg=None, lofi=None)`, assembled
once at `gs.STUBS` (`0x43033000`) by `gen_registrar.py`, committed as hex in `registrar.json` with its symbol
table (`state_at`, `state_connect`, `cc_bounds`, `drum_icons`, `small_icon`, `record_at`, `record_of`,
`knob_vec`, `desc_machine`, `builder_row`, `marks`: the targets of `g7.JUMPS`, `g8.JUMPS8` and `g7.CALLS`), which
are now **fixed addresses**. The parameter block `regs` lives at a fixed offset in the same area, the last 128 bytes
(`STUBS + 0x780`), away from the code:

```
regs+0   .byte  n, first (6), top (first + n − 1), last (76 + 5 n)
regs+4   .long  knob_tab                 ; DATA + 12 (first + n): knob_vec's table machine -> record
regs+8   machine[6], 16 bytes each:
         .byte  image, first_desc, rec_param (first_desc − 51), 0
         .long  rec                      ; RECS + 0x60 i
         .long  knob_hook                ; 0; MACRO's lo-fi would go here (notes/59 §3)
         .long  0
```

What each entry does with it (register contract of the generated detour kept, see 5.2):

| Entry | Today | B2c |
|---|---|---|
| `map_state` | `cmp.l #last` | reads `last` from `regs+3` |
| `cc_bounds` | `moveq #top` | reads `top` |
| `shown` | n unrolled compares | loop over `machine[]`, returns `image` of the entry whose index is `first + i` |
| `record_at`, `record_of` | n compares each, `rec_i` stubs with `lea RECS + 0x60 i` and `moveq #first_desc − 51` | one loop, `rec` and `rec_param` from the entry, then `rec_build` unchanged |
| `knob_vec` | `moveq #top`, `moveq #first`, `lea DATA + 12 nm` | reads `top`, `first`, `knob_tab`; calls `knob_hook` when non-zero |
| `desc_machine`, `builder_row` | two compares per machine | loop: `first_desc ≤ d ≤ first_desc + 3` → `first + i` |
| `marks` | assembled only when nm > 7, `moveq #nm` | always present, reads `first + n`; the composer still writes the `jmp marks` at `0x400a26a2` only when nm > 7 and the `moveq` at `0x400a26e8` otherwise, as today |
| `state_at`, `state_connect`, `drum_icons`, `small_icon`, `rec_build` | constant | unchanged |

Expected size: 700 to 800 bytes constant (the unrolled n = 6 version is 1 094; loops are shorter), well inside the
2 048 minus 128. Limits unchanged: n ≤ 6 (`gs.check_room`), nm ≤ 14 (two rows of marks). With Model-TG the
runtime is not used: model27 does not offer Model-TG, and the TG variant stays in `gen_macro.added_machine` for
the generators that still need it.

### 5.2 Register contract per entry `[FAIT, 2026-10-21]`

Read in the OS 1.13 code (`m68k-elf-objdump -m m68k:isa-c` over section 3) at each site: what the generated detour
touches today (`detours_asm`), and what the OS still reads after the detour returns or jumps on (a register is
*free* when every path writes it before reading it, or the function restores it from the stack). Two kinds of
entry: a **whole function** replaced from its first instruction (it ends with `rts`, the ABI's scratch registers
d0, d1, a0, a1 are the caller's problem) and a **mid-function** detour that jumps back into the OS, where only
what the following code has given up is free.

| Entry | Site, kind | Today touches | Live after (must keep) | Free (may use) | Loop in B2c |
|---|---|---|---|---|---|
| `state_at` | `0x4004df40`, whole function, `rts` | d0 d1 | d0 = result | d0 d1 (a0 a1 by ABI; stock leaves them) | none: `cmp.l last,%d0` reads the block |
| `state_connect` | `0x4004dfa2`, whole function, calls `0x400ddf60` | d0 d1, the callee's a0 a1 | d0 = result | d0 d1 a0 a1 | none |
| `record_at`, `record_of` | `0x4004df5c`, `0x4004df76`, whole functions | d0 d1 a0 a1 (`rec_build` saves d2 a2; its `0x400f8f02` calls clobber a1) | d0 = result | d0 d1 a0 a1 | pointer a0, temp d1, end pointer from the block (`cmpa.l`) |
| `cc_bounds` | `0x4005a8f0` → `0x4005a8fa` / `0x4005a91c` / `0x4005a928`, mid-function | d2 (written by the stock there too) | d0 (`lsl.l` at `0x4005a90a`), a0 (all exits); d2 restored at `0x4005a92a` | d1 (written at `0x4005a8fe`), d2, a1 (written at `0x4005a90c` / `0x4005a91c`) | none: `mvz.b top,%d2` |
| `shown` (internal, `bsr` from the two below) | | d0 d1 | d0 = picture | d0 d1 a0 (see callers) | table lookup: `lea`, `mvz.b (%a0,%d0.l)`; no stack save needed |
| `drum_icons` | `0x400a2638` → `0x400a2680`, mid-function | d0 d4 a1 a2 (the stock sets a2 there too) | d2 d3 a4 a5 | d0 d1 d4 d5 a0 a1 a2 a3 (d4 d5 a2 a3 reset at `0x400a26a2`, restored by the `movem` at `0x400a2706`) | via `shown` |
| `small_icon` | `0x400a4dc4` → `0x400a4dde`, mid-function | d0 d1 a0 (after the push) | d0 = picture | d1 a0 a1, d2 (reloaded from the frame at `0x400a4dfc`) | via `shown`, after a0 is pushed |
| `knob_vec` | `0x4001e8da` `jsr`+`nop`, back at `0x4001e8e2` | d0 d1 a1 (reads d2 d3 d5) | d0 = index, a1 = table, **a0** (`record_at` pointer loaded at `0x4001e8d4`), d2 d3 d5 a2 a3 a4 | d1, d4 (written at `0x4001e8e8` / `0x4001e922` before any read) | none: `mvz.b top,%d1`, `mvz.b first,%d1`, `movea.l knob_tab,%a1`; `knob_hook` call keeps the same set |
| `desc_machine` | `0x4005a50a`, whole function | d0 d1 a0 | d0 = result | d0 d1 a0 | pointer a0, temp d1, end pointer from the block |
| `builder_row` | `0x4005a340` → `0x4005a346` / `0x4005a384`, mid-function | d0 (sets d5 = result) | d5, **a0** (read at `0x4005a41c`), d2 d3 d4 d6 d7 a2 a3 a5 fp | d0, d1 (written at `0x4005a348` / `0x4005a386`), a1 (written at `0x4005a3ae` / `0x4005a3e0` / `0x4005a436` before read) | pointer **a1**, temps d0 d1 |
| `marks` | `0x400a26a2` → `0x400a26f2`, mid-function | d0 d1 d4 d5 a2 a3 | d2 a4 | d0 d1 d4 d5 a0 a1 a2 a3 (restored by the `movem`) | none: `mvz.b nm,%d0` |
| `rec_build` (internal) | | d0 d1 a0 a1, saves d2 a2 | | unchanged | unchanged |

Conclusions for `registrar.S`:

- **No entry needs a register the detour does not have today**, once the per-build constants move into the
  block: `last` as a long for `cmp.l (abs).l,%d0`, `n`, `first`, `top` as bytes read with `mvz.b (abs).l,%dN`
  (ISA_B and up; the MCF5441x is ISA_C), the pointers `knob_tab` and `machines_end` as longs. So no stack
  saves, no changed argument offsets.
- The loops use **a0** in the whole-function entries (`record_at`, `record_of`, `desc_machine`) and in `shown`,
  and **a1** in `builder_row`, where a0 carries the OS's own pointer; `knob_vec` must not touch a0 either.
- `d1` is free at every entry; `d2` only in `cc_bounds` and `small_icon`; the MACHINES page (`drum_icons`,
  `marks`) frees d4, d5, a2, a3 as well.
- `marks` is assembled in every build but reached only when `nm > 7` (the composer keeps writing the `moveq` at
  `0x400a26e8` otherwise), so its register use is the same as today's.

### 5.3 The composer's own writes

`compose.registrar_writes(img, machines, blobs, bss_end)` replaces the call to `gm.added_machine` for the
alone layout: a port of its Python arithmetic (data block, descriptors, moved references with `refs32`, bounds,
small bounds, jumps and the call to the **fixed** runtime symbols, the `Algorithm` maximum, `reloc`, `segments`,
the stub from the template, the parameter block as one more payload part at `STUBS + 0x780`). `gm.added_machine`
itself is not changed: `gen_macro.py`, `gen_acid.py` and the Syntakt generators keep using it.

### 5.4 Proof

1. **Differential against B1**, `compose.py --compare-b1`, for `sampler`, `refmachine`, `sampler+refmachine`,
   `refmachine+sampler`, and each with `arp` and `trig-hold`: the two tweaks have the same writes except the eight
   sites of `JUMPS` / `JUMPS8` / `CALLS` (whose targets are now the runtime's fixed symbols) and the same payload
   parts except the `STUBS` part (runtime + block instead of generated detours). The stub write is identical
   (B2b). Anything else that differs is a bug in the port.
2. **digiemu**, by the maintainer: boot, MACHINES page (names, marks, pictures), knob names and ranges, machine
   locks across the added machines, a sound saved and reloaded, and each machine's sound against the B1 image.
3. **Unicorn**, when available (§8): the UI checks of `test_syntakt_machines.py` adapted to the runtime (they
   already walk the MACHINES page, the rows and the records) and `mcengine` for the sound, track by track, B2 image
   against B1 image, bit for bit.
4. **Hardware**, by the maintainer, before `27-sampler.json` is regenerated for the flasher.

## 6. The composer after B2

- `compose.py --relocator python` (default once B2a is proven) or `--relocator ld` (development, toolchain);
  `--compare-ld` and `--compare-b1` as above. `compose.py` imports neither `gen_macro` nor the assembler any more;
  it reads `registrar.json`, the packages' objects and manifests, and the user's official OS.
- `gen_sampler.py` and `gen_refmachine.py` become: compile, `ld -r`, write `<id>.o` (`--check`), then call
  `compose.compose` for the tweak JSON, so the committed JSON is the composer's output and `build.py -t sampler`
  equals `compose.py --machines sampler` by construction.
- `ref_mainos.py`, `check_overlaps.py`, `registry.py`, `gen_flasher_tweaks.py`, `build.py` and the flasher:
  unchanged, they consume the JSON. `REF_MODS` / `REF_MAINOS` regenerate when the JSONs change.
- No toolchain: `compose.py`, `build.py`, the flasher checks. Toolchain: the three generators, with `--check` in
  the same place the tweak checks run today.

## 7. Order of work and done criteria

| Step | Work | Done when |
|---|---|---|
| **B2a** | `tools/relocate.py`; `compose.py --relocator`, `--compare-ld`; patch points as symbols in One-Shot (0.8, re-pinned) and in the manifests; `gen_sampler.py` / `gen_refmachine.py` emit and check `<id>.o` | relocator = `ld` byte for byte for both packages and both pairs; `compose.py --machines sampler` still reproduces `27-sampler.json` |
| **B2b** | `gen_registrar.py` (stub part), `registrar.json` with the template; composer fills it | stub bytes = B1's for every selection |
| **B2c** | `registrar.S`, the runtime part of `gen_registrar.py` / `registrar.json`, `compose.registrar_writes`, `--compare-b1`; regenerate `27-sampler.json` and `28-refmachine.json` | differential clean; digiemu by the maintainer; then hardware for SAMPLE alone and the pair |

One commit per step, with the trailer. Each step leaves B1's path working until its own is proven, so a
half-finished step never blocks a build.

## 8. Risks and open points

- **Placement rules of `ld`** (order inside `*(.text*)`, alignment, `.data` after `.rodata`): `--compare-ld`
  settles them; until equal, B2a is not done. `[HYP]` file order and `sh_addralign` are the whole rule.
- **Register contract** when unrolled compares become loops: tabled in §5.2 from the disassembly; every loop
  fits in registers the detour already owns. A wrong clobber would show in digiemu as a wrong knob name or
  record, not as a crash, so the UI checks of §5.4 still matter.
- **Emulation harness**: `mcengine.PAYLOAD_CODE` is fixed (`0x43000000..0x43007298`, `0x43031000..0x43032000`) and
  SAMPLE's code runs to `0x43007727`; the harness must take the code ranges from the tweak's parts before it can
  place EMAC hooks in a composed image `[À FAIRE with Unicorn]`.
- **Unicorn**: no wheel for Python 3.14; `brew install python@3.13` and a venv (outside the sandbox, the
  maintainer's call) is the known way. Until then the proofs are §3 step 6, §5.4 step 1 and digiemu.
- **One-Shot 0.8** is a prerequisite of composing SAMPLE at an index other than 6 from a committed object. The
  convention of notes/59 §6 (SAMPLE first, index 6) holds anyway until B4's registry.
- **Byte changes for users**: after B2c the SAMPLE tweak's detour bytes differ from the hardware-tested 0.7 build;
  `tests.hardware` of the sampler manifest and the flasher card's `HW_TESTED` go back to "not yet" until the
  maintainer flashes the regenerated build.

## 9. B2a built (2026-10-21)

- **`tools/relocate.py`** (about 200 lines, standard library): the ELF32 big-endian reader (`struct`), the
  garbage collection from `update`, `render` and `keep`, the placement in the linker script's order at each
  section's `sh_addralign`, the symbols, the `R_68K_32` loop with undefined symbols resolved from the patch points.
  `python3 tools/relocate.py <object>` lists what an object holds.
- **`tools/compose.py`**: `--relocator python` (default: the committed objects) or `ld` (B1's path, kept whole);
  `--compare-ld` runs both for every package of the build and compares blob, symbols and BSS end. `patch_values`
  takes `{"symbol": …}` (resolved like `--defsym`: by `ld` in the B1 path, by the relocator in B2) and still the
  B1 `{"define": …}`; `build_object` compiles the manifest's recipe and joins it with `ld -r`; `place_package`
  places an object; `emit_bytes` writes or checks a committed binary and names the compiler of the committed one
  (`.comment`) when it differs.
- **Packages**: `build.objects` in both manifests; `tools/machines/sampler/sampler.o` (39 592 bytes) and
  `tools/machines/refmachine/refmachine.o` (2 388 bytes), written and checked by `gen_sampler.py` and
  `gen_refmachine.py`, which now place the object with the relocator (so `build.py -t sampler` is the composer's
  output by construction: MAIN OS `dd7bfd56…`, the same from `compose.py --machines sampler`).
- **One-Shot** (four files, upstream `cycles-sampler/` and the copy here, for 0.8): `pool.h` and `view.c` take the
  index and the first descriptor from the undefined symbols `cm_machine_index` and `cm_descriptor_base` when
  `CM_SYMBOLS` is defined (the manifest defines it; One-Shot's own build and host tests keep the constants);
  `smp_filter_cf.S` and `hooks.S` get sections of their own (`.text.smp_filter_cf`, `.text.smp_hooks`). The
  second change was found by the comparison: **`ld -r` merges same-named input sections and puts the merged
  `.text` first**, so the two assembly files' code, plain `.text` before, left file order and the relocator
  differed from `ld` at `+0xec`. With their own sections the order is the file order again `[FAIT]`.
- **Proof, §3 step 6**: `compare-ld` identical for `sampler` (30 523 bytes), `refmachine` (1 304 bytes),
  `sampler,refmachine` and `refmachine,sampler` (both packages at their place in each). The placement rule, file
  order and `sh_addralign` with the output group aligned to its largest input, is the whole rule `[FAIT]`
  (§8's hypothesis).
- **What changed for users**: `27-sampler.json` is regenerated: code 30 503 → 30 523 bytes (three `move.l #symbol`
  for `moveq`, and the assembly files' alignment), the hooks' addresses move by 14 bytes, the `symbols` with them;
  nothing else. `28-refmachine.json` is unchanged. `REGISTRY.md`, `docs/flasher/tweaks.js` and the reference
  hashes in `app.js` are regenerated; `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`,
  `ref_mainos.py --check` pass; One-Shot's host tests (`test_core`, `test_sampler`) pass.
- **digiemu** (maintainer, 2026-10-21): the regenerated SAMPLE alone (`f938a482…`) and the pair `sampler+refmachine`
  (`583fa4dc…`) run with the five test files in `/incoming`: "passt".
- **Not done**: the regenerated SAMPLE build has not been on a device (the manifest says so in `tests`); One-Shot 0.8 is committed upstream (`f28ef2f`, its own build byte for byte the 0.7 MAIN OS once the
  assembly sections got `.p2align 2`) and `gen_sampler.py` is pinned on it; the tag `v0.8` and the push are the
  maintainer's; the `.comment` check only reports, it does not refuse.

## 10. B2b built (2026-10-21)

- **`tools/gen_registrar.py`** assembles `stub.S` (`PACK`) once at `gx.CAVE` with three placeholder immediates and
  an empty segment table, finds each placeholder once in the code, and commits
  `tools/machines/registrar/registrar.json` (schema `model27-registrar/0.1`): the 64 bytes of code, the offsets
  (`dst_at` 2, `longs_at` 8, `src_at` 20: the source is at 20, not 24 as §1 first said), `segs_at` 64, the
  address and the limit `STUB_END`. `--check` compares with the committed file. Room: 15 segments.
- **`compose.py`**: `boot_stub(reg, src, dst, longs, segs)` fills the template and appends the table (address,
  longs, then `0, 0`), refusing a stub past `STUB_END`; `check_boot_stub` runs on **every build** and compares the
  template's stub with the one `added_machine` assembled, byte for byte. So B2b's proof is permanent, not a
  one-off: it ran for `sampler`, `refmachine`, both pairs, the pair with `arp` and `trig-hold`, and through both
  generators' `--check`; a template with one wrong byte is refused (tried).
- Until B2c, `added_machine` still assembles the stub itself and the template only has to agree; B2c's
  `registrar_writes` takes the stub from `boot_stub` and the assembler goes.

## 11. B2c built (2026-10-22)

- **`tools/machines/registrar/registrar.S`**: the runtime, 826 bytes, assembled once at `STUBS` (`0x43033000`)
  by `gen_registrar.py` and committed in `registrar.json` (`runtime`: code, the addresses of the eleven entries,
  `regs_at`, the block's shape). The parameter block lives at `STUBS + 0x780` (`0x43033780`): header `n`, `first`,
  `top`, `nm` (bytes), `last`, `knob_tab`, `machines_end` (longs), then 16 bytes per machine (`index`, `image`,
  `first_desc`, `rec_param`, `rec`, `knob_hook`, 0): 32 bytes for one machine, 48 for two, 112 at most. The code
  follows §5.1 and keeps §5.2's contracts: `find_machine` (d1 → a0, `cmp.b` against the entry) serves `shown`,
  `record_at`, `record_of` and `knob_vec` (which saves a0 around it and its hook); `find_desc` (d0 → a0) serves
  `desc_machine`; `builder_row` loops on a1; `map_state`, `cc_bounds`, `knob_vec`, `marks` read `last`, `top`,
  `first`, `nm` and `knob_tab` from the block with `cmp.l` / `mvz.b` / `movea.l` from memory.
- **`compose.registrar_writes`**: the port of `added_machine` (`tg=None`) in Python: data block, descriptors, the
  moved references, the 43 bounds, the small bounds, the jumps and the call to the runtime's **fixed** entries, the
  `marks` jump or `moveq`, the `Algorithm` maximum, `reloc`, `segments`, the stub from the template
  (`boot_stub`), with `parameter_block` as one more payload part. `compose.py --registrar runtime` is the default;
  `--registrar b1` keeps `added_machine`; `--compare-b1` does both and compares. `gen_macro.added_machine` is
  untouched (MACRO, ACID, the Syntakt generators). `gen_sampler.py` and `gen_refmachine.py` go through the
  runtime now, so `27-sampler.json` and `28-refmachine.json` carry it.
- **Proof, §5.4 step 1**: `compare-b1` for `sampler`, `refmachine`, `sampler,refmachine`, `refmachine,sampler` and
  the pair with `arp` and `trig-hold`: the same writes but the 11 (12 with `marks`) detour sites, the same payload
  parts but the `STUBS` part (runtime for detours) and the new block part, the same `reloc`, size, source and
  destination. `build.py -t sampler` gives the composer's MAIN OS (`ccdadb37…`). Every checker passes
  (`check_overlaps.py`, `registry.py`, `gen_flasher_tweaks.py`, `ref_mainos.py`, `webbuild_check` by hand).
- **Cost**: the image grows by 252 bytes for one machine (36 096 added instead of 35 844: 826 bytes of runtime
  for 606 of detours, the block, one more segment) and shrinks for six; the stub has one more segment. The
  runtime leaves 1 096 bytes before the block.
- **digiemu** (maintainer, 2026-10-22): the runtime builds `sampler` (`019cce6d…`), `refmachine` (`e92870d5…`) and
  `sampler+refmachine` (`e4000e20…`) run: "funktioniert".
- **Not done**: the device for the runtime build; the emulation proof with Unicorn (§8); the `.comment` check only
  reports. `compose.py` now needs neither compiler nor assembler: `python3 tools/compose.py --cycles … --machines …`
  is the whole build.

## 12. Tested on the Model:Cycles (2026-10-22)

- **Flashed by the maintainer** on their Model:Cycles: the runtime build with both machines of §11, SAMPLE as
  machine 6 and the reference machine as machine 7 (`sampler+refmachine`). Their report: "ich habe den build mit
  beiden machines auf dem gerät getestet" (the build with both machines, tested on the device). No problem reported.
- **What that build carries of B2**: both packages placed by the relocator from their committed objects (§9),
  SAMPLE's index and first descriptor resolved as symbols (One-Shot 0.8), the boot stub from the template (§10), and
  the registrar runtime with its parameter block for two machines (§11), the marks of the MACHINES page included
  (eight machines: the runtime's `marks` entry).
- **Not covered**: SAMPLE alone, the build the web flasher makes (MAIN OS `ccdadb37…`). It has the same objects,
  runtime and stub; what differs are the 53 writes that depend on the number of machines ([notes/61](61-level-b3-web-flasher.md)
  §1.3), the parameter block, and the marks, a `moveq #7` in the OS's own code instead of the runtime's `marks`
  entry. The SAMPLE card stays `experimental` until that build is flashed from the page, as its guide line says.
- Recorded in the manifests' `tests.hardware` (`sampler`, `refmachine`), in the guide's Tested line of SAMPLE and in
  this note's row of `notes/README.md`.

## 13. SAMPLE alone tested from the page (2026-10-22)

- **Flashed by the maintainer from the web flasher** (stamp `2026-10-22-01`): SAMPLE alone. The page builds SAMPLE
  alone only when its MAIN OS is `REF_MAINOS["sampler"]` (`ccdadb37…`), so what was flashed is B2c's SAMPLE alone,
  the case §12 did not cover. Their report: "getestet in digiemu und auf dem device" (tested in digiemu and on the
  device).
- With §12, both cases of the runtime have run on the device: one machine (the marks as the OS's `moveq #7`) and two
  (the runtime's `marks`).
- From this date the SAMPLE card is `tested`: `FEATURES` in `gen_flasher_tweaks.py` and `tweaks.js`, the guide's
  Tested line, release 0.2, the sampler manifest's `tests`.

## 14. Proven in emulation with Unicorn (2026-10-22)

- **`tools/emu/test_compose.py`** runs the OS's own code in Unicorn for SAMPLE alone, REF alone and both pairs, as
  `compose.py` builds them with the registrar runtime:
  - start-up: the bootstrap's aPLib depacker reads the grown OS back, the boot hook copies the packed payload into
    place and clears the BSS;
  - the registrar's mechanics, with the checks of `test_syntakt_machines.py` configured from the manifests: tables
    built at boot, lookups, accessors and state per descriptor, the MACHINES page (a second row of marks from eight
    machines), the setter and the wheel, records, a real machine change, the main screen's knobs, machines out of
    range (KICK's record and knobs, no access outside memory), the small icon;
  - the runtime against B1's per-build detours, input for input, over the OS functions they serve: the same results
    everywhere (§5.4's behaviour proof);
  - the voice loop: REF the same, sample for sample, as machine 6 alone and as machine 7 next to SAMPLE; SNARE on
    another track the stock OS's; SAMPLE silent with no sample loaded; nothing outside memory.

  Run by the maintainer on 2026-10-22: **ALL OK**. This closes §8's `[À FAIRE with Unicorn]` `[FAIT en émulation]`.
- **The harness**: the emulator gets the payload as it lies in memory (`build.payload_runtime`) and the code ranges
  from the composed tweak's parts, not `mcengine.PAYLOAD_CODE`'s fixed ones. SAMPLE's code holds 158 EMAC
  instructions, 8 of them outside those fixed ranges when SAMPLE is alone and 15 when it comes after REF: without
  their hooks they would be emulated wrongly. `emac.py` now finds `m68k-elf-objdump` as well as Debian's
  `m68k-linux-gnu-objdump`, as the generators find their toolchain.
- **Where it runs**: Unicorn 2.1.4 has wheels for Python 3.14 now (`pip install unicorn numpy`), but its JIT stops
  with SIGILL in a sandbox that forbids generated code (`probe_chord_keys.py` says so too): the proof runs in a normal
  terminal. Without Unicorn, `--dry` builds every selection and prints its layout.

## 15. One-Shot 0.9 pinned (2026-10-24)

- **What changed upstream**: One-Shot 0.9 (`4f8c7b5`, tag `v0.9`) splits the bar above the waveform into two boxes in
  the look of the browser's title: the current pattern's number in columns 0–20, read as MainScreenView reads it
  (`0x4006a96c(0x400cfd0e())`, written `"%c%02d"`), and the sample's name in columns 23–127. Only `machine/view.c` and
  `machine/os.h` differ from 0.8; sound, knobs, records and hooks are the same. One-Shot's own build was tested by the
  maintainer in digiemu and on a Model:Cycles (2026-10-24).
- **Here**: the two files copied as they are into `tools/machines/sampler/machine/`; `gen_sampler.py` pinned on `v0.9`;
  `sampler.o` and `27-sampler.json` regenerated (123 writes as before, 30 883 bytes of code and tables, 380 more; the
  writes differ only at the hook and view entries, whose targets moved; the same 270 conflicts); `tweaks.js`,
  `REGISTRY.md` and `REF_MAINOS`/`REF_MODS` regenerated: SAMPLE alone `be01a3dd…` (was `ccdadb37…`), with Control All
  Config `a831d408…` (was `3f4f079a…`).
- **Checked**: `gen_sampler.py --check`, `gen_flasher_tweaks.py --check`, `registry.py --check`,
  `claims.py --check --self-test`, `check_overlaps.py`, `ref_mainos.py --check`, `webcompose_check.sh` with the
  official file (composer.js gives compose.py's tweaks and MAIN OS), `webbuild_check.sh`, `webflash_check.sh`.
  `test_compose.py` stops with SIGILL in the sandbox (§14) and runs in a normal terminal; `webflash_smoke.sh` needs
  jsdom from npm. Both run by the maintainer on 2026-10-25:
  - `test_compose.py`: **ALL OK** (SAMPLE alone, with REF, with REF2 and with both: start-up, the registrar's
    mechanics, the runtime against B1, the voice loop).
  - `webflash_smoke.sh` with both official files: 3 failures, all three values for SAMPLE pinned in
    `tools/webflash_smoke.js` that the pin had not moved: the composer's log line (36 096 bytes added to the OS, now
    36 452, the sum of the tweak's appended segments) and the two Model:Samples packings of `MFS` (now `6e8d2dcb…`
    for `_smp-os` and `d3bf1129…` for `_cyc-os`). The new values were computed apart from the page, with
    `build.py -t sampler --expect-mainos be01a3dd…` and `mods_for_samples.py` on its output, and they are the
    page's. Everything else passed. With them, `webflash_smoke.sh` with both official files: **ALL OK** (2026-10-25,
    jsdom from npm with its cache in a temporary folder). The manifest's emulation entry names the composed 0.9.
    `[À FAIRE]` flashing SAMPLE from the page.
- The card stays `tested`: the change is the view alone, tested on the device in One-Shot's own build, and the
  composed build differs from that one where it always did (§9). Release 0.5 and the guide's Tested line say that the
  page's build of 0.9 has not been flashed yet.

## 16. One-Shot 0.10 pinned (2026-10-25)

- **What changed upstream**: One-Shot 0.10 (`3193c42`, tag `v0.10`) draws a column on the left after the maintainer's drawing:
  the current pattern's number in a lit box, an outline with TRAK and the selected track's number, and the track's
  level as a bar in a frame with ticks, read as MainScreenView reads it (`0x40009c5a(project + 116, t)`, 0–127). The
  sample's name keeps its box, 2 columns to the right; the waveform is 105 columns wide from column 23
  (`SMP_COLUMNS` in `pool.h`). `machine/view.c`, `machine/os.h` and `machine/pool.h` differ from 0.9; sound, knobs,
  records and hooks are the same. One-Shot's own build was tested by the maintainer in digiemu and on a Model:Cycles
  (2026-10-25), the image byte for byte the released one.
- **Here**: the three files copied as they are; `gen_sampler.py` pinned on `v0.10`; `sampler.o` and `27-sampler.json`
  regenerated (123 writes as before, 32 535 bytes of code and tables, 62 008 of variables, 38 104 bytes added to the
  image; the same 270 conflicts); `tweaks.js`, `REGISTRY.md` and `REF_MAINOS`/`REF_MODS` regenerated: SAMPLE alone
  `09dd1ee7…`, with Control All Config `eeb7b2bb…`. The smoke test's pins moved with them (§15's lesson): the log
  line's 38 104 bytes, and the two Model:Samples packings `99b6c7e3…` (`_smp-os`) and `129fcb50…` (`_cyc-os`),
  computed apart from the page with `build.py -t sampler --expect-mainos 09dd1ee7…` and `mods_for_samples.py`.
- **Checked**: listed in the commit; `test_compose.py` in a normal terminal (§14), run by the maintainer on
  2026-10-25: **ALL OK**. Then flashed from the page (§17). The card stays `tested`, as in §15.

## 17. SAMPLE 0.10 tested from the page (2026-10-25)

- **Flashed by the maintainer from the live web flasher** (stamp `2026-10-25-01`), SAMPLE as the page composes it:
  "funktioniert" (works). The page builds SAMPLE alone only when its MAIN OS is `REF_MAINOS["sampler"]`
  (`09dd1ee7…`), so what was flashed is §16's composed 0.10, byte for byte.
- With it the card's `tested` holds for the page's own build again, as it did for 0.8 (§13). The page's build of 0.9
  was never flashed; 0.10 replaces it.
- The guide's Tested line, release 0.7, the sampler manifest's `tests.hardware` and the stamp `2026-10-25-02` say so.

## 18. One-Shot 0.11 pinned: Loop and Reverse on the switches (2026-10-26)

- **What changed upstream**: One-Shot 0.11 (`a874a1c`) loops and plays in reverse, as the Model:Samples does. The core
  plays a window once or in a loop, forward or reverse; a loop goes round with a hard seam and its taps read across the
  seam, so a single cycle loops without a step; switched off, a loop ends at the end of the first pass at least 4 ms
  ahead. The machine reads the two switches, bits 8 and 9 of k 32, in the note's sound (`CUR_SNDS[t]` + 84, the copy
  when that is 0), only when built with `SMP_SWITCHES`; the name's box ends with L and R. A trig that cuts a sounding
  note brings the new one in over 0.67 ms, as the Model:Samples' level stage (`0x400a7266` there); a voice whose amp
  envelope has closed lets go of its sample. `src/smp_core.c/.h`, `machine/pool.h`, `sampler.c` and `view.c` differ
  from 0.10. One-Shot's own build has no shortcut layer and no `SMP_SWITCHES`: one shot, forward.
- **Here**: the five files copied as they are. The manifest builds with `SMP_SWITCHES`, declares RETRIG + PUNCH (Loop)
  and RETRIG + GATE (Reverse) as presses (notes/63 §16.5), and claims k 32, record slot 18 and the two combinations,
  as REF2 does. So the builder's shortcut layer now comes with SAMPLE in every build, SAMPLE alone included: the press
  at `0x4001ac4a`, the LEDs at `0x4001cc86`, the knob lookup's entry, and the record chain with SAMPLE's wrappers
  behind the layer's (the chain `test_shortcuts.py` proves since §18 of notes/63).
- **`gen_sampler.py` builds through `compose.py`**, as `gen_refmachine.py` does for REF2: its own pipeline (the
  registrar's writes, SAMPLE's hooks, the conflicts from bytes and RAM) did not add the layer, so `27-sampler.json`
  would no longer have been what the page composes. It still compiles and checks the object, then takes the writes,
  the payload, the symbols and the conflicts from `compose.compose(img, ["sampler"])`. `compose.py --compare` on the
  result: writes, payload and symbols identical. 126 writes (123 before: the layer's press, LEDs and knob entry),
  33 993 bytes of code and tables, 62 112 of variables, 40 508 bytes added to the image; 271 conflicts, the new one
  **lfo-plus**, by the claims: it keeps LFO 2 in k 28–32 and record slots 30–31, where the layer saves the switches
  and the knob shortcuts (no byte is shared). lfo-plus is not offered on the page, so no card changes;
  `check_overlaps.py` passes with the conflict declared by the tweak.
- **Hashes**: SAMPLE alone `72b596dc…` (the build the maintainer played in digiemu, `.syx` `ba674fac…`, the same from
  `build.py -t sampler`), with Control All Config `327cbd37…`; the smoke test's pins: 126 writes and 40 508 bytes in
  the log line, the Model:Samples packings `46f9acdb…` (`_smp-os`) and `0fecd30e…` (`_cyc-os`), computed apart from
  the page with `build.py -t sampler` and `mods_for_samples.py`.
- **`test_shortcuts.py`**: SAMPLE is now a machine with switches, so its byte of presses is 3 and the press and the LEDs
  act on its tracks as on REF2's (they were the stock press there).
- **Tested**: host tests (One-Shot's `make test`, `make machine-test` with and without the switches); digiemu by the
  maintainer on this build (2026-10-26): Loop, Reverse, single cycles, the fade-in after a cut, "passt". A first report
  of regular clicks with Loop on came, as far as the maintainer can tell, from RETRIG left latched in digiemu. Unicorn,
  run by the maintainer on this pin (2026-10-26, as notes/63 §18.3 runs them): `test_shortcuts.py` 109 checks (SAMPLE's
  byte of presses 3, the press and the LEDs acting on its tracks next to REF2's), `test_views.py` 45, `test_refchord.py`
  86, `test_compose.py` 183, `test_chordtables.py` 165, **ALL OK** `[FAIT en émulation]`. The device is next. The card
  stays `tested`, as in §15–16.

## 19. SAMPLE 0.11 tested from the page (2026-10-26)

- **Flashed by the maintainer from the live web flasher** (stamp `2026-10-26-01`), SAMPLE as the page composes it, and
  played on a Model:Cycles: "passt" (fine), against the list Loop (L, PUNCH's LED while RETRIG is held, the note
  looping until DECAY closes it), Reverse (R, from the next trig), both at once, a single cycle looped, a trig cutting
  a sounding note, PUNCH and GATE without RETRIG and TRACK + PUNCH or GATE as before, a saved project keeping the
  switches. The page builds SAMPLE alone only when its MAIN OS is `REF_MAINOS["sampler"]` (`72b596dc…`), so what was
  flashed is §18's composed 0.11, byte for byte, the build played in digiemu.
- With it the card's `tested` holds for the page's build of 0.11, as it did for 0.10 (§17).
- The guide's Tested line, release 0.9, the sampler manifest's `tests.hardware` and the stamp `2026-10-26-02` say so.

## 20. One-Shot 0.12 pinned: a held trig's view (2026-10-30)

- **What changed upstream**: One-Shot 0.12 (`c32c49d`, tag `v0.12`) shows its whole view while Start or Length turns
  with a trig held: the waveform of what the held trig plays, its start and end on the trig's locks, a sample lock's
  sample and name (One-Shot's TECHNICAL.md §9). For that it takes a third vtable entry, NoteVelocityView's draw
  (`0x40102578`), whose stock draw would cover the left half: `smp_note_draw` calls it except while the knob draw has
  just drawn SAMPLE's view. `machine/os.h`, `view.c` and `view.h` differ from 0.11.
- **Here**: the three files copied as they are. The manifest takes `view.note` (`smp_note_draw`, kept), claims the view
  `note`, and its texts say what the view does. `view.note` is the point the dispatchers 0.3 and REF2 0.2 brought in
  (notes/63 §22): SAMPLE alone writes its entry directly, SAMPLE next to REF2 goes through `dp_note`.
- **`gen_sampler.py`**: pinned on v0.12. 127 writes (126 before: the new vtable entry), 34 606 bytes of code and
  tables, 62 116 of variables, 41 120 bytes added to the image; 273 conflicts, as before. `compose.py --compare`:
  writes, payload and symbols identical to `27-sampler.json`. With REF2 (`compose.py --machines sampler,refmachine2`)
  the dispatchers take five points, `view.note` among them.
- **Hashes**: SAMPLE alone `db7bde6a…` (`.syx` `a067ab59…` from `build.py -t sampler`), with Control All Config
  `c469f1f0…`, with Digital Delay `30d2a1f2…`, with POTS `ffd5d966…`, all four `7abde1c9…`, SAMPLE with both effects
  `1d7bc3b1…` (BUILD.md); the smoke test's pins:
  127 writes and 41 120 bytes in the log line, the Model:Samples packings `6dc0c4c8…` (`_smp-os`) and `34be7dca…`
  (`_cyc-os`), computed apart from the page with `build.py -t sampler` and `mods_for_samples.py`.
- The card's text, the guide's SAMPLE section (a step for the held trig) and Tested line, release 0.17, stamp
  `2026-10-30-01`.
- **Tested**: host tests (One-Shot's `make machine-test` with and without the switches, its new `test_view_held`);
  One-Shot's own image of 0.12 (the same code without `CM_SYMBOLS` and `SMP_SWITCHES`) in digiemu and on a
  Model:Cycles by the maintainer (2026-10-30). Unicorn, run by the maintainer on this pin (2026-10-30, the venv of
  notes/63 §22): `test_views.py` (now with `view.note`'s dispatcher: both methods in its table, each track's draw),
  `test_compose.py`, `test_shortcuts.py`, `test_refchord.py`, `test_chordtables.py`, **ALL OK** `[FAIT en émulation]`.
  The page's build on the device next. The card stays `tested`, as in §18.

## 21. One-Shot 0.13 pinned: Start and Length on the note that plays (2026-11-02)

- **What changed upstream**: One-Shot 0.13 (`213b4e4`, tag `v0.13`) lets Start and Length act on the note that plays
  instead of the next trig only (One-Shot's TECHNICAL.md §10, §11). Playing once, a voice keeps the Start of its trig
  and plays the length Length now gives (`smp_set_length`): its end moves at once, never to less than its whole 4 ms
  fade-out ahead of the playhead, not once the fade-out has begun; Start alone waits for the next trig, so an LFO on
  Start still picks each trig's start. A loop takes the window both give (`smp_set_window`), as the Model:Samples'
  render does (its window in every block, `0x400a6c38` of its MAIN OS; the playhead set only at a trig): the far side
  at once, the side where a pass begins from the next seam (`next`), a far side behind the playhead round at once. The
  bridge hands COLOR and SHAPE over between trigs when they or the loop changed (`follow` in `machine/sampler.c`).
  `src/smp_core.c`, `src/smp_core.h` and `machine/sampler.c` differ from 0.12.
- **Here**: the three files copied as they are; every file of `tools/machines/sampler/` is byte for byte One-Shot's at
  `213b4e4`. The manifest's version, name, description and source; no new point, claim or view.
- **`gen_sampler.py`**: pinned on v0.13. 128 writes and 278 conflicts, as before; 35 862 bytes of code and tables,
  62 248 of variables, 42 616 bytes added to the image (41 360 before). `compose.py --compare`: writes, payload and
  symbols identical to `27-sampler.json`.
- **Hashes**: SAMPLE alone `d3376a65…` (`.syx` `bcf8540a…` from `compose.py --machines sampler` and from
  `build.py -t sampler` alike), with Control All Config `e845a342…`, with Digital Delay `84879b9b…`, with POTS
  `49b77311…`; SAMPLE with both effects `03a2b64e…`, with Samples `d343e6c9…` (BUILD.md); the smoke test's pins: 128
  writes and 42 616 bytes in the log line, the Model:Samples packings `94b8e395…` (`_smp-os`) and `2bbf3d90…`
  (`_cyc-os`), computed apart from the page with `build.py -t sampler` and `mods_for_samples.py`.
- The card's text (and its gesture, MACHINES + PUNCH / GATE as in the guide, where it still read RETRIG), the guide's
  SAMPLE section (a step, the knob table, the Tested line), release 0.33, stamp `2026-11-02-04`; PROVENANCE.md names
  the tag and commit the files come from.
- **Cost**: counted in a ColdFire interpreter (not the proof's emulator) against 0.12's 2 773 instructions for the
  core and the update's share: about +50 a track and block while the knobs rest, +100 to +160 while Start or Length
  move (three or six of them divisions).
- **Clicks on a loop**: the seams stay hard, as on the Model:Samples, which glides its knobs the same way (its audio
  block calls `0x400573b8`, the Cycles' `0x40058474` with the same constants, before its voices), computes the window
  in every block, fetches across the seam in two DMA parts and lowers its level only near the end of a voice that does
  not loop (`0x400a7266`). Moving the window adds a few seams (an end moved behind the playhead goes round at once:
  4 in the second after Start glides from 40 to 0 on a loop of 8 000 frames, against 6 seams a second it has anyway);
  a shorter loop has more seams a second. Its one floor the core does not have: a loop of at least 141 frames.
  The maintainer chose to keep it so (2026-11-02).
- **Tested**: One-Shot's host tests (`make test` with `test_length`, `test_window`, `test_moves_no_click`; `make
  machine-test` with and without the switches, `test_follow`, `test_follow_switches`), under ASan too. The composed
  0.13 with the shortcut layer, built from `54b7095` with these three files (the same `.syx`, `bcf8540a…`, as this pin
  builds), by the maintainer in digiemu and on a Model:Cycles flashed over USB (2026-11-02): Length on a note that
  plays, once and reversed, Start waiting for the next trig, a loop's Start and Length, an LFO on Start and on Length,
  "passt" `[FAIT sur la machine]`. Unicorn, run by the maintainer on this pin (2026-11-02): `test_compose.py`,
  `test_shortcuts.py`, `test_views.py`, `test_refchord.py`, `test_chordtables.py`, `test_fxslot.py`,
  `test_fltslot.py`, **ALL OK** `[FAIT en émulation]` (they load no sample: SAMPLE's place, layout and memory accesses
  in the OS, next to the other packages). The card stays `tested`.

## 22. One-Shot 0.14 pinned: the Model:Samples' pictures for Cutoff and Reso (2026-11-04)

- **What changed upstream**: One-Shot 0.14 (`e7df584`, tag `v0.14`) shows the Model:Samples' own pictures while
  SWEEP (Cutoff) or CONTOUR (Reso) turns on a SAMPLE track (One-Shot's TECHNICAL.md §9 and §16). The knob view draws a
  parameter's picture through its interface object: `0x4001d818` calls the parameter's entry +68 (`0x4000a6b0`), which
  calls the object's `+0x60` as `picture(object + 0x54, bitmap, 32, 19, value)` while `+0x5c` is set. SAMPLE's Cutoff
  and Reso share SNARE's objects 53 and 54, so they showed SNARE's pictures (`0x400466a2`, `0x400466f0`). The Cycles
  OS builds the Model:Samples' sprites at boot anyway (the same constructor as the Model:Samples OS, 2047 sprites pixel
  for pixel), among them its Cutoff's 87 frames of 50 × 22 (`0x40fe3638`) and its Resonance's 11 (`0x40fe35f4`), which
  nothing in the Cycles draws. `smp_pic_cutoff` and `smp_pic_reso` pick and draw those (`0x40072058`, `0x40071da4`)
  on a SAMPLE track and call SNARE's otherwise; the tick puts each into its slot once SNARE's is there, as it does the
  Cutoff formatter. `machine/os.h`, `machine/view.c` and `machine/view.h` differ from 0.13.
- **Here**: the three files copied as they are; every file of `tools/machines/sampler/` is byte for byte One-Shot's at
  `e7df584`. The manifest's version, name, description, source and hardware test, and a new claim: `pictures`, objects
  53 and 54 (Cycles Mod Standard draft 0.8, `4781879`). No new point or view.
- **The claim `pictures`** (`{"knob", "object", "replaces"}`, an interface object's `+0x60`): `tools/claims.py` reads
  it as it reads `formatters`, and rule 2 holds for it the same way: one picture per object, whatever the scopes, so
  two holders of one object's picture clash; a picture and a formatter of one object do not (two pointers). The web
  flasher's `composer.js` applies the same rule (`resolveClaims`, `claimClashes`), `app.js` says why
  (`why_picture`), `registry.py` lists the pictures in `REGISTRY.md` §9, and `webcompose_synth.py` adds a probe
  (object 54 on CHORD's tracks) so that `webcompose_check.sh` compares both composers on it. No other tweak or part of
  the folder writes these two slots (only the OS's boot code does, `0x400e0414` and `0x400e04a2`), so the claim
  changes no conflict today: 280 as before.
- **`gen_sampler.py`**: pinned on v0.14. 128 writes and 280 conflicts, as before; 36 226 bytes of code and tables,
  62 248 of variables, 42 980 bytes added to the image (42 616 before).
- **Hashes**: SAMPLE alone `522bc89c…` (`compose.py` and `build.py -t sampler` alike), with Control All Config
  `26218ef3…`, with Digital Delay `bec8dcca…`, with POTS `e34890b1…`; SAMPLE with both effects `14345987…`, with
  Samples `b7507068…`, with RESAMPLE `87476afd…`, every card of the page `4f6a8756…` (BUILD.md); the smoke test's
  pins: 128 writes and 42 980 bytes in the log line, the Model:Samples packings `60f640bb…` (`_smp-os`) and
  `5438cc6d…` (`_cyc-os`), computed apart from the page with `build.py -t sampler` and `mods_for_samples.py`.
- The card's text, the guide's SAMPLE section (the version, the knob table, the Tested line), release 0.44 (after the
  sections' How to use, 0.43), stamp `2026-11-04-09`; PROVENANCE.md names the tag and commit the files come from.
- **Cost**: the pictures are drawn only while the knob view shows Cutoff or Reso, as SNARE's were, through the same
  two functions; nothing changes on the audio side.
- **Tested**: One-Shot's host tests (`make machine-test` with and without the switches, `test_pictures` and
  `test_pictures_install`, four deliberate faults caught), under ASan too. One-Shot 0.14's own build (without
  CM_SYMBOLS and SMP_SWITCHES), by the maintainer in digiemu and on a Model:Cycles (2026-11-04): the pictures on a
  SAMPLE track, SNARE's on a SNARE track, "passt". Unicorn, run by the maintainer on this pin (2026-11-04):
  `test_compose.py`, `test_shortcuts.py`, `test_views.py`, `test_refchord.py`, `test_chordtables.py`, `test_fxslot.py`,
  `test_fltslot.py`, **ALL OK** `[FAIT en émulation]`. The composed 0.14 with the shortcut layer, SAMPLE alone as
  this pin composes it (`.syx` `856b552f…`, the same file as `build.py -t sampler`, MAIN OS `522bc89c…`), by the
  maintainer on a Model:Cycles flashed over USB (2026-11-04): the pictures on a SAMPLE track, SNARE's on a SNARE track,
  Loop and Reverse with L and R, "passt" `[FAIT sur la machine]`. The card stays `tested`.

## 23. One-Shot 0.15 pinned: Loop and Reverse per step, the step panel, the pan (2026-11-06)

- **What changed upstream**: One-Shot 0.15 (`b5020bb`, tag `v0.15`; its code is `1d24f7b`'s, the release commit
  adds the version and the docs) plays the locks of k 32 that the shortcut layer 0.5 writes (`note_switches`), draws
  a step panel in NoteVelocityView's draw while a trig is held, shows T1..T6 and the pan in the column, and puts
  FUNC + LEVEL/DATA's pan on even values on its tracks (two hooks, point `main.pan`, `0x4001ab14` and `0x4001ab52`).
  The work, its proofs and the device test: notes/63 §25–§32.
- **Here**: every file of `tools/machines/sampler/` is byte for byte One-Shot's at `b5020bb`. The manifest's
  version, name, description, source, two `main.pan` hooks and the two symbols kept, the tests; `gen_sampler.py`
  pinned on v0.15. 136 writes and 280 conflicts; 38 528 bytes of code and tables, 62 248 of variables, 46 292 bytes
  added to the image (42 980 at 0.14: the layer 0.5's code, the panel, the pan hooks).
- **Hashes**: SAMPLE alone `49ac6238…` (the file of the device test's last steps), with both effects `a545a230…`, with
  Samples `1caed5f9…`, with RESAMPLE `d1852177…`, every card of the page `a503f081…`; BUILD.md also gives the other
  builds the layer 0.5 moved (the Track FX alone and together, the CPU page with them). The smoke test's pins: 136
  writes and 46 292 bytes in the log line, the Model:Samples packings `44abb137…` (`_smp-os`) and `5dc14a91…`
  (`_cyc-os`).
- The card's text (a block for TRIG + MACHINES + PUNCH / GATE), the guide's SAMPLE section (the version, a step for the
  locks and the panel, the column and its pan, the table, the limits, the Tested line), README (release 0.50, switches
  lockable), release 0.50, stamp `2026-11-06-01`; PROVENANCE.md names the tag and the commit.
- **Tested**: One-Shot's host tests with and without the switches, under ASan and UBSan too. Unicorn, run by the
  maintainer on the final code (2026-11-05): `test_sample_pan.py`, `test_shortcuts.py`, `test_compose.py`,
  `test_views.py`, `test_refchord.py`, `test_chordtables.py`, `test_fltslot.py` ALL OK; `test_fxslot.py`,
  `test_cpu.py` and `test_resample.py`, whose selections hold SAMPLE or the layer, run by the maintainer on the release's code (2026-11-06): ALL OK (540, 139 and 181 checks) `[FAIT en émulation]`. On a Model:Cycles, flashed
  over USB, ten steps as the work was built, the last ones with this pin's files (SAMPLE alone `49ac6238…`, every card
  `a503f081…`): notes/63 §32. The card stays `tested`.

## 24. One-Shot 0.16 pinned: the sample under the browser's cursor on the pad and the TRIG keys, and with the pad held on the trigs (2026-11-11, 12)

- **The request** (the maintainer, 2026-11-11, from the feasibility check of that day): hear a sample in the PRESET
  browser before opening it. Decided with the maintainer: **as the Model:Cycles does with its presets**. While the
  cursor rests on a sample file of a SAMPLE track, the pad of the active track and the TRIG keys in CHROMATIC mode
  play that sample; the sequencer keeps playing the track's own sound. **With the track's settings** (Start, Length,
  the filter, Loop, Reverse), **as the Model:Samples does**: the maintainer heard it in digiemu with the official
  Model:Samples OS (2026-11-12). (The Model:Cycles plays a preset under the cursor with the preset's own settings; a
  sample file has none.) **Silent until the file has loaded.** History: the first build played with the track's settings on an answer the maintainer had skipped, not
  given; asked again, they chose SAMPLE's defaults (the OS's own new sound, `0x40061866(sound, -, machine)`, whose
  descriptor lookup the added machines' build opens for SAMPLE, `0x4005a6a6`), built on 2026-11-11; after hearing the
  Model:Samples they went back to the first build (2026-11-12), rebuilt byte for byte (the same hashes).
- **The pad held** (the maintainer, 2026-11-12, after the first proof ran; each point asked on its own): while the
  pad of the track the browser is open for is held (only that pad), the track's trigs play the marked sample, with
  everything the step has (note, velocity, length, trig condition, parameter locks); steps with a sample lock keep
  their own; the marked sample not loaded yet, they stay silent; let go, the note that plays the marked sample goes
  on in the track's sample at once, at the same place (the Model:Samples in digiemu, heard by the maintainer); the
  browser closed with the pad held does as a let-go. The TRIG keys keep their stock way: the sequencer plays the
  track's sample, its next trig cuts the note a TRIG key played (one voice a track), and while a TRIG key is held the
  track's trigs pause, on every machine (the maintainer in digiemu, with KICK, 2026-11-12).
- **The Model:Samples** `[FAIT, read in its OS 1.13, not run]`: its browser's key handler `0x400a40e0` takes a pad
  only for the browser's track (`+664`, the key's track from `0x4011257c`); the press puts the file under the cursor
  into the sample slot the track's sound uses (`0x4000fdc4`, the slot's former content kept at `+10792 + 16 t`), the
  let-go puts it back (`0x400a4330`). A step with a sample lock names another slot, so it keeps its sample; any other
  track on the same slot would play the marked one too (SAMPLE switches by track). No code puts the slot back when
  the browser closes with the pad held; its next opening clears the held mask (`0x400a4896`) `[HYP: the marked
  sample then stays on the track, as if loaded]`; SAMPLE does as a let-go instead (the maintainer).
- **What the OS does** `[FAIT]` (notes/46 §2, §3.1): the cursor's preview `0x400a63ac` reads the entry as a preset
  (`jsr 0x400a3052` at `0x400a6426`); a sound read is copied into one of two 100-byte buffers (`0x40058504`,
  `0x4008f1f0`) and marked (`0x40081bd6`, `*0x40fb5a04`). A note played live on the active track (source `0x40`: the
  pads, `0x4001d08e`, and the TRIG keys in keyboard mode, `0x40019edc`) carries the mark at +52 of its event
  (`0x40081860`), the audio side copies its 66 bytes of parameters into `0x800015ae + 66 t` (`0x40058a0a`) and clears
  the note's sound after it (`0x4005910e`); the sequencer's trigs never carry it. A sample file fails the preset
  reader's size check (48..160 bytes), so on SAMPLE 0.15 nothing was marked and the pad played the track's sample;
  the reader had opened the file first and left its "open" bit on (§3.1).
- **What changed upstream**: One-Shot 0.16 (commit `a376832`, tag `v0.16`; the "lock holds" work once
  numbered 0.16, parked on One-Shot's branch `lock-holds` and model27's `sampler-0.16-lock-holds`, gets another number
  if it is taken up):
  - `machine/hooks.S`: `smp_hook_preview` at `0x400a6426` (point `browser.preview`), the same call as the open's
    hook, with the browser in a2 itself (`+664` the track; at `0x400a6602` a2 points at it). It calls
    the open's `smp_browser_open`: on a SAMPLE track a sample file (more than 160 bytes, an odd id, a header SAMPLE
    plays) gives the track's sound naming the file in k 25..27, which the OS copies and marks as it does a preset;
    otherwise `jmp 0x400a3052`, as before. The file is not opened, so a SAMPLE track no longer leaves the bit of §3.1
    on.
  - `machine/pool.c`: the tick notes the marked sound (`PREVIEW_SOUND`, `*0x40fb5a04`, `machine/os.h`) next to the
    kits' and the tracks', so its sample loads while it is marked and is freed once it is not (the cursor moved on, the
    browser closed: `0x400a40e4` marks 0), as soon as no voice plays it. A marked SAMPLE preset names its sample too
    and now loads it `[HYP: that the preset reader's sound goes through SAMPLE's record load, as a loaded preset does]`.
  - The pads (`machine/hooks.S`, point `pad.note`): the Model:Cycles' pads play and end their notes through
    `0x4001d05e(view, track, note, velocity, speed)` and `0x4001d0fc(view, track, note)`, each called only by the
    pads' handler `0x4001d180` (vtable entry `0x4010025c`; the held note at `+88 + 4 t` of its view) `[FAIT]`; the
    TRIG keys play theirs elsewhere (`0x40019edc`, `0x40019cb4`), the only other callers of note on and off. Their
    first 6 bytes (`lea -16(sp),sp ; moveq #5,d1` and `lea -12(sp),sp ; moveq #5,d0`) become `jsr smp_hook_pad_on` /
    `smp_hook_pad_off`, which set or clear `smp_pad_held[t]`, do those two instructions and go on (d0, d1 and a1 free
    there). No tweak or part writes those bytes. The tick clears the flags while nothing is marked.
  - **The held pad's note-off at once** (2026-11-12): in digiemu the held pad's track played nothing, and a held pad
    mutes its track on KICK too (the maintainer). `[FAIT, read in the OS 1.13, not run]`: the audio side's event loop
    keeps, by track, the rank and the note of the note that holds it (`0x40fe4c9c + 4 t`, `0x40fe4cb4 + 4 t`); it
    drops a note of a lower rank (`0x40058e4e`); the sequencer's notes are rank 1 (`+12` of the message,
    `0x40054b7e`), the notes played live rank 2 (`0x4005894a`, from `0x4008171e` and `0x4008145e`); a note-off frees
    the track only with the same rank and note (`0x40058f4c`), and ends the gate (`0x400588c8`, `0x40058530`). The
    Model:Samples' browser takes the pad of its track itself (the key counted as used, so its pads' own functions
    `0x4001e7b6` / `0x4001e854` do not run) and sends the note's note-off right after its note-on (`0x400a3fac`,
    then `0x400a4088`); its sequencer itself not read. SAMPLE does the same: `smp_hook_pad_on` now runs the rest of
    `0x4001d05e` as a subroutine on a copy of its five arguments (its tail call into the recording, `0x4008273c`,
    writes over them), then, when `smp_pad_frees(track)` (`machine/sampler.c`: the pad noted as held, the active
    track, a SAMPLE sound with a sample's id marked) says so, calls `0x4008145e(track, note, 0x40)`, what
    `0x4001d0fc` sends, without its end of a live recording (`0x400827a8`). Consequences: the track's trigs reach it
    while the pad is held; with GATE on the pad's own note no longer holds (it fades with DECAY); the release's
    note-off is dropped by the event loop (the rank of the sequencer's note that holds the track, or 0, against 2),
    the counts of held notes stop at 0 (`0x40fb57ec`), and with MIDI out on the device gets a second note-off; a
    live recording still starts at the press and ends at the release. Any other pad note, the TRIG keys and presets
    under the cursor stay stock. 152 bytes more of code.
  - **The TRIG keys' note-off at once** (2026-11-12, the maintainer: with a TRIG key held the track's trigs paused, as on
    every machine of the stock OS, heard in digiemu; asked for since the start: "wenn man trigs nutzt, muss das momentan
    auf dem track geladene sample trotzdem ganz normal weiterspielen"): the keys' note function in CHROMATIC mode,
    `0x40019e7a(view, track, note, velocity, speed)`, called only by the keyboard's handler (`0x40019f6e`), begins with
    the pad's two instructions (`lea -16(sp),sp ; moveq #5,d0`), so `smp_hook_key_on` (point `key.note`) does as the
    pad's hook: the rest as a subroutine on a copy of the arguments, then, when `smp_key_frees(track)` (a SAMPLE sound
    with a sample's id marked for the active track; no pad noted as held) says so, `0x4008145e(track, note, 0x40)`,
    what the key's note-off `0x40019c84` sends. The track's trigs play on in the track's own sample (the key is not a
    held pad) and the next one cuts the key's note; the release's note-off is dropped as the pad's. No card writes
    there (Transpose replaces the keyboard view's handler, `0x4001a0d2`, which still calls `0x40019e7a`). 140 writes,
    48 552 bytes added.
  - The audio side (`machine/sampler.c`): at a trig, with the pad of the active track (`*0x40a700c4`) held and a
    SAMPLE sound marked, a note whose sound is the played kit's track sound (`CUR_SNDS[t]` = `*0x800017e4 + 28 +
    100 t`, the event loop's own choice) plays the marked sample's id instead; a lock's sound is another pointer and
    keeps its own; a note played live (the pad's own, a TRIG key's) already carries the marked sound and plays it out, as a preset under the cursor does (the Model:Samples in digiemu with the sequencer stopped, heard by the maintainer, 2026-11-12; the first build sent the held pad's own note back too, heard as wrong the same day). A note that took the marked sample's place is remembered (not one of a track whose own sample is the marked one); every block,
    once the pad is let go or nothing is marked, its block is ramped out to silence, the voice re-triggered on the
    track's sample at the frame of the same time (rates scaled, the window as Start and Length give it there), and
    the next block ramped in, as a cut does.
  - Before the pad: `start()` reads the note's sample in the 66-byte copy, which the OS fills from the
    marked sound for a preview note, and the switches there too when the note's sound is 0 (One-Shot 0.11).
- **0.17: the marked copy follows the knobs** (2026-11-12/13, the maintainer: with the browser open, the knobs no longer
  changed the previewed sample). `[FAIT, read in the OS 1.13]`: the audio side's parameter write `0x40059534(value,
  track, k)` (reached from `0x4000e348` / `0x4000e3e2`) puts the word straight into the voice's targets, `0x800015ae +
  66 t + 2 k` (track 6: the FX page at +204), and clears `CUR_SNDS[t]` when the track's note sound is not the kit's;
  so a knob turned reaches a note that already plays, preview note included. But the sound the browser hands out
  (`smp_browser_open`: a copy of `os_sound(track)` naming the file) is copied again by the OS into its preview buffer,
  and every preview note takes its 66 bytes from there (`0x40058a0a`, since `0x4005910e` clears the note's sound after
  each one): the next note played the knobs as they were when the cursor arrived. One-Shot 0.17 (`pool.c`,
  `refresh_mark`, in the tick): the tick remembers which preview buffer holds the copy it handed out (the same 100
  bytes when first seen, then that pointer; the OS's two buffers take turns, so a new mark is a new pointer) and,
  while it is marked, writes the track's sound's k 0..32 but the key (k 25..27) into it; a preset marked (another
  content) is left alone; the cursor arriving on a file again makes a fresh copy, recognised again. No hook, no
  write: 8 more bytes of variables. Host: `test_preview` (a knob turned, the copy before and after a tick, a preset
  left alone, the cursor back on the file), two deliberate faults caught. The proof's tick test grows the knob: **ALL OK** (the maintainer, 2026-11-13) `[FAIT en émulation]`. digiemu starts; on a Model:Cycles, flashed from the command line with every card (the maintainer, 2026-11-13, « passt »): a note after SHAPE turned down is short, after SWEEP turned filtered, the held pad's trigs follow SHAPE at once `[FAIT]`. Then flashed from the page with every card the same day (the maintainer: « seiten-flash passt ») `[FAIT]`: the card is `tested` again. The card went back to `experimental` until the device test, and is `tested` since the page's flash of 2026-11-13. **Hashes 0.17** (MAIN OS): SAMPLE alone `e5db2aef…`, with both effects `a5ecc06d…`, every card of the page `6b88b851…` (the file for digiemu and the device, `.syx` `bb82036a…`); 140 writes, 48 756 bytes added; the smoke test's pins 140 / 48 756, the Model:Samples packings `f5980224…` (`_smp-os`) and `89c1e6e4…` (`_cyc-os`); One-Shot's own image MAIN OS `89c72c29…`, `.syx` `8be4c42f…`; with SOLID `f7b26b90…`, with CHORD Tables `e4d22760…`, with Samples `242fe9b1…`, with RESAMPLE `878d0560…`, with Transpose `5a4d375f…`, with the CPU page `6be5db32…` (`ref_mainos.py`, 137 combinations).
- **`[HYP]` the tick while the browser is open**: SAMPLE's tick is the screen's redraw (`0x400075f0` in `0x400075da`,
  called from `0x40007e92`, `0x40076ff4`, `0x40084522`), which takes the screen object and asks its root view
  (`+64`) whether to draw; nothing there depends on which view is on top. Read, not run: the device decides it (the
  marked sample must play after a moment, and must not stay silent).
- **Costs**: one slot of 128 and the file's memory in the 47 MB pool while it is marked; a 64-byte read of the
  header each time the cursor stops on a sample file (the stock OS reads a whole preset there). Loading is SAMPLE's
  as before, 128 KiB a tick (computed, not measured: about 0.3 s for 10 s of mono, 3 s for 60 s of stereo). The pad
  held adds no voice: the track's one voice plays the marked sample instead of its own; per trig a few tests, per
  block one, and at a let-go one re-trigger. Measured by the proof's step 6, the payload of SAMPLE playing a note in
  instructions per block (Unicorn, run by the maintainer, 2026-11-12): 3 034 on 0.15 (HEAD's pin), 3 042 on 0.16
  (+8), 3 063 with the pad held (+29; 3 070 before the let-go was narrowed to a trig's note), 3 625 in the one block it is let go (+591, the re-trigger and the two ramps),
  of 108 225 a block: 0.03 % while held, 0.55 % once `[FAIT en émulation]` (before the note-off at once, which runs in
  the interface's task, not the audio's; the run with it to follow). Only one track at a time (the
  browser's). The CPU page can show only the playing without the pad: it and the browser are never open together,
  and PEAK counts from the page's opening; on the device the page showed CPU and PEAK as with release 0.60 (the maintainer, 2026-11-12) `[FAIT]`.
- **Here**: `machine/hooks.S`, `os.h`, `pool.c`, `pool.h` and `sampler.c` copied from One-Shot 0.16, every file of
  `tools/machines/sampler/` One-Shot's; the manifest's version, name, description, source, the hook and the kept
  symbol, and the two pad hooks; `gen_sampler.py` pinned on v0.16. 139 writes (three more), 282 conflicts as before, 40 384 bytes of code and
  tables, 62 344 of variables, 48 168 bytes added to the image (with the note-off at once 40 536 and 48 320; with the pad's own note playing out 40 448 and 48 232). Conflicts with the cards of `OFFERED`: none (no card
  writes `0x400a6426`; Model-TG's sample preview does, and conflicts with SAMPLE already). The card went back to
  `experimental` until the device test, and is `tested` since the page's flash of 2026-11-12.
- **Hashes** (MAIN OS, with the pad's own note playing out and the TRIG keys' note-off at once; the build of the note-off alone: SAMPLE alone `0f4f9373…`, every card `fd6f3f56…`, `.syx` `5da2ce6f…`, One-Shot's MAIN OS `0d2004ed…`): SAMPLE alone `37117f68…`, with SOLID `ff513be6…`, with CHORD
  Tables `19d700b5…`, with both effects `109c5582…`, with Samples `d2abae2b…`, with RESAMPLE `b6e4b02c…`, with
  Transpose `8f2eb904…`, with the CPU page `12b24422…`, every card of the page `ab2666d0…` (the file for digiemu and
  the device, `.syx` `234f709f…`; the build before the note-off, `cac9bdc4…`, `.syx` `7330c88f…`, is the one tried in
  digiemu). The smoke test's pins: 140 writes and 48 552 bytes in the log line, the Model:Samples packings
  `30fa4ef8…` (`_smp-os`) and `b7b46a48…` (`_cyc-os`), computed apart from the page with `mods_for_samples.py` on the composed SAMPLE alone. One-Shot's own image: MAIN OS `64f6d76c…`, `.syx` `7a2eb3c0…`.
- The card's text (a block for the pad and the TRIG keys in the PRESET menu), the guide's SAMPLE section (the version,
  a step, the Samples line, the Tested line), README, release 0.61, stamp `2026-11-11-05`; PROVENANCE.md names the
  tag.
- **Tested**: One-Shot's host tests with and without the switches (`test_pad_hold`: the held pad's trigs, a lock's
  own, another track, nothing marked, not loaded, the let-go at the same frame with its ramps, the browser closed, a
  TRIG key's note and the held pad's own playing out at the let-go, a trig of a track whose own sample is marked left
  alone, the tick forgetting the pads; nine deliberate faults caught; `test_pad_frees` with `smp_key_frees`, two more; `test_preview`: the track's sound marked with the
  file, its Start, Length and Loop among them, loaded, silent before,
  played, kept while a voice plays it, freed after, the cursor moving on while a file loads, a project's sample
  shared, another machine's preset ignored; a deliberate fault caught), under ASan and UBSan too (only the known
  messages). Unicorn, `tools/emu/test_sampler_preview.py` (the cursor, the note, the tick and the voice, stock against
  SAMPLE alone and next to REF2), run by the maintainer: ALL OK on 2026-11-12 `[FAIT en émulation]`. Its first run
  failed twice on the bench, not on SAMPLE: its preset read marks nothing, on the stock OS as well, so the sequence
  sample → sample → preset now compares the preset with the stock OS, and the tick's test of another machine's preset
  puts that preset in the buffer itself, as the OS would. That run was before the pad held; with it the proof grows
  the sites of the two pad hooks, step 5 (the real pad note functions: the held pad's trigs, a lock's own, the
  let-go at the same place, the browser closed) and step 6 (the cost, alone only), run by the maintainer: ALL OK on
  2026-11-12, alone and next to REF2 `[FAIT en émulation]`. With the note-off at once the proof grows its step 5
  through the audio side's own event loop (nothing marked: the held pad's track drops a sequencer's note; marked: the
  note-off sent once, the track free, the sequencer's note plays the marked sample, the release's note-off dropped
  with or without a sequencer's note since, a live recording started at the press and ended at the release), run
  by the maintainer: ALL OK on 2026-11-12, alone and next to REF2 `[FAIT en émulation]`; `test_pad_frees` on the host (four deliberate faults caught). digiemu with the
  build before (`7330c88f…`, 2026-11-12): the pad and the TRIG keys play the marked sample in their pitches, the
  sequencer the track's, a TRIG key tapped is cut by the next trig and a held one pauses the track's trigs (stock, KICK
  too): « passt »; the held pad's track silent (above), hence the note-off. digiemu with the build of the note-off (`5da2ce6f…`, 2026-11-12): pressing or holding the pad plays the marked sample and
  the trigs reach the track: « funktioniert jetzt korrekt »; but with the sequencer stopped the pad's own note went back to
  the track's sample at the let-go (no new attack, the track's sample ringing on), which the Model:Samples does not do
  (its pad's note plays out, pressed or held; heard by the maintainer in digiemu with the official OS the same day).
  Rebuilt with the pad's own note playing out (above). The same day the maintainer recalled the TRIG keys: in Test 3 of
  the build of the note-off a held TRIG key paused the track's trigs (taken then for stock behaviour and left), against
  the request; rebuilt with the keys' note-off at once (above); the proof grows its engine tests by the key (nothing
  marked: holds its track; marked: note-off once, the track free, a sequencer's note plays the track's own sample, the
  release's note-off dropped): **ALL OK** (the maintainer, 2026-11-12) `[FAIT en émulation]`. digiemu with this build (the maintainer, 2026-11-12): « passt, habe schon alles getestet » `[FAIT en émulation]`. The device, flashed from the command line with every card (the maintainer, 2026-11-12, « gerät geflasht, tests 5 bis 7 passen »): a long stereo sample silent for a moment, then played (the tick runs with the browser open: the `[HYP]` above holds); the pad, the TRIG keys, the held pad's trigs, the let-go and a locked step as in digiemu, scrolling through many files without a hang, the browser closed with the pad held as a let-go; the CPU page as before `[FAIT]`. Then flashed from the page with every card the same day (the maintainer: « Von der Seite ») `[FAIT]`: the card is `tested`.
