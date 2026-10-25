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
  2026-10-25: **ALL OK**. `[À FAIRE]` flashing SAMPLE from the page. The card stays `tested`, as in §15.
