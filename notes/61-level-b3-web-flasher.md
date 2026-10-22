# 61 — Level B, step 3: the web flasher composes the machines (plan)

**Status: plan, 2026-10-22; the maintainer's decisions (§9); B3a built (§10); B3b built (§11); B3c built and checked in a real browser (§12).** This is increment B3 of [notes/59](59-level-b-builder.md)
(§5 the web flasher, §7 item 3), written after B2 landed (`74221c4`: the composer runs with `python3` alone,
[notes/60](60-level-b2-relocator-runtime.md)) and after the maintainer tested the runtime build on their
Model:Cycles (reported 2026-10-22). It measures what the page already does and what composing needs on top, decides
what reaches the browser as data and what as code, and orders the work so that every piece is proven against the
Python composer before the page uses it. Addresses are VAs of OS 1.13; measured on 2026-10-22 with the official
`model-cycles_OS1.13.syx`.

## 0. In short

- **The page can already apply a composed tweak.** A composed tweak uses only what `builder.js` reads today: writes,
  `hex` parts, one `cycles` part, `reloc` and `pack` (no `compress`, no `syntakt`), and `build()` checks it against
  `REF_MODS` by its id like any other tweak. B3 does not touch `build()`: what is missing is the composing itself,
  before the build (§1.1).
- **Two kinds of data, one small loop each.** A package reaches the page as its object **placed once at offset 0**:
  the code, and a list of relocations (position, base, addend) whose base is the code, the variables or a patch
  point. Placing it anywhere is a loop over that list; the ELF reader, the garbage collection and the section order
  stay in `relocate.py` (§2). The registrar reaches the page as a **frame** per number of machines: the writes and
  payload parts that do not depend on the packages, computed by the Python registrar itself; the page fills in what
  does (the data block, the descriptors, the parameter block, the boot stub) (§3).
- **Both forms were tried first, with a throwaway Python prototype** (2026-10-22): the object placed once gives
  `relocate.place`'s bytes at 41 placements for each package; a frame filled per selection gives `compose.compose`'s
  writes and payload for `sampler`, `refmachine` and both pairs, identical.
- **For users nothing changes while SAMPLE is the only machine card.** SAMPLE composed in the page is
  `27-sampler.json` byte for byte (`compose.py --machines sampler --compare` identical; MAIN OS `ccdadb37…` =
  `REF_MAINOS["sampler"]`): the reference blocks of `app.js` stay as they are and the firmware needs no new hardware
  test. What B3 buys is the next machine: one package added to the page, every selection composed and checked, no
  pre-built combination.
- **Three sub-steps, each committed alone** (§6): B3a the packages as data and their placement in JavaScript; B3b
  the registrar frame and the composer in JavaScript, proven against `compose.py` with the official file; B3c the
  page switches its machine cards to packages.

## 1. What was measured (2026-10-22)

### 1.1 The page today

- **`builder.js`** (the port of `build.py`): `applyWrites`, `checkConflicts` (a tweak's `conflicts` and
  `requires`), `checkCaves`, `buildPayload` / `payloadRuntime` (parts `hex`, `cycles`, `syntakt`, then each `reloc`
  with its old value checked, then `pack` or `compress`), repack, signature, SysEx. `build()` checks every tweak
  against `REF_MODS[t.id]` (`w`: its writes; `p`: its payload as it goes into the image) and, through `app.js`, the
  whole MAIN OS against `REF_MAINOS[key]` when the selection is in the sample.
- **`app.js`**: a card reaches its tweaks through `variants` (and `versions`, `joins`, `with` for MACRO, ACID,
  Model-TG and the Syntakt engines); `chosenTweaks()` maps the ticked cards to tweaks in card order; the key of a build
  is their ids joined by `+`. What reads `variants`: `selOf`, the variant sub-choice (`renderVariants`),
  `chosenTweaks`, `chosenLabels`; in `tools/ref_mainos.py`, `Cards.options`.
- **`gen_flasher_tweaks.py`**: `OFFERED = ("sampler",)`. The SAMPLE card points at `27-sampler.json`; its `excludes`
  are copied by hand from the conflicts `gen_sampler.py` computes (the comment says "the cards here mirror them").
- **Sizes**: `tweaks.js` 87 592 bytes for its one card (`27-sampler.json` is 83 207 bytes as committed, 78 565 as
  compact JSON), `builder.js` 45 158, `app.js` 177 758.
- **`webflash_smoke.js`** still expects upstream's cards (`features.length === 22`, MACRO, ACID, Model-TG, no SAMPLE)
  and needs `npm` and the network (jsdom). It is rewritten in B3c anyway.
- **The version stamp** of the pages is `2026-10-21-06` since `60d60ab`: B2a (`0c88fbe`) and B2c (`74221c4`)
  regenerated `tweaks.js` and the reference blocks of `app.js` without a new stamp (§8).

### 1.2 Composed tweaks

| Selection | Writes (registrar + package) | Payload parts, bytes | Added to the image | Compact JSON |
|---|---|---|---|---|
| `sampler` | 123 (116 + 7) | code 30 527; runtime 826; block 32; data 171; descriptor table 4 256 (`cycles`); new descriptors 280 | 36 096 | 78 565 |
| `refmachine` | 116 (116 + 0) | code 1 304; 826; 32; 168; 4 256; 280 | 6 868 | 19 469 |
| `sampler,refmachine` | 123 (116 + 7) | code 30 527 + 1 304 (at `0x43007740`); 826; 48; 235; 4 256; 560 | 37 760 | 82 244 |
| `refmachine,sampler` | 123 (116 + 7) | the same, the two codes swapped (SAMPLE at `0x43000518`) | 37 760 | 82 244 |

- `compose.py --machines sampler --compare tweaks/model-cycles_OS1.13/27-sampler.json`: writes, append and symbols
  identical; MAIN OS `ccdadb3775ca…` = `REF_MAINOS["sampler"]` `[FAIT]`.
- Conflicts computed against the folder's tweaks: `sampler` 267, `refmachine` 264, the pair 268, exactly the union of
  the two. For these two packages no conflict appears only in combination.

### 1.3 The registrar's part against n

`compose.registrar_writes` run for n = 1 to 6 (synthetic machines, the alone layout) writes at 117 sites in all:

- **61 the same for every n**: the sprite redirect and the boot hook; 45 references to the moved descriptor, row and
  name tables; 4 constant bounds (`0x4005a572`, the three icon bounds); the 9 jumps and the call into the runtime's
  fixed entries.
- **53 that change with n only**: 49 two-byte `moveq` (42 descriptor-count bounds, 75 or 76 + 5 n; 7 machine bounds,
  5 + n), the `pea 32·nm` of the row builder (`0x4005a2b8`), and the three references whose table moves with nm
  (update table `DATA + 4 nm`, render table `DATA + 8 nm`, machine map `DATA + 16 nm`).
- **1 site per n for the marks** of the MACHINES page: a `moveq #nm` at `0x400a26e8` for n = 1, a `jmp marks` at
  `0x400a26a2` for n ≥ 2.
- **The boot stub**, which depends on the layout (the segment table, the payload's length).

Payload parts that do not depend on the packages: the runtime (826 bytes), the descriptor table copied from the
user's file (a `cycles` range, 4 256 bytes) and the one `reloc` word, the maximum of the Algorithm parameter
(`00000500` → (5 + n) << 8). What depends on the packages: their code, the data block (names, update and render
addresses, the strings), the five descriptors per machine (SNARE's, with the knob fields set), the parameter block,
the segments and the stub.

A frame holding the 61 writes once, the 54 of each n for n = 1 to 6, the `reloc` of each n and the fixed parts is
19 217 bytes of compact JSON (1 652 of them the runtime's hex). Filled by the prototype the way the page would fill
it, reading the stock values in the official MAIN OS, it gives `compose.compose`'s writes and append for `sampler`,
`refmachine`, `sampler,refmachine` and `refmachine,sampler`, identical `[FAIT]`.

### 1.4 The packages

| | `sampler` | `refmachine` |
|---|---|---|
| Object | 39 592 bytes | 2 388 bytes |
| Allocated sections, kept by the roots | 51, 48 | 4, 4 |
| Largest alignment kept | 4 | 2 |
| Relocations kept | 138: 54 to code, 74 to variables, 10 to patch points | 5: 2 to code, 3 to variables |
| Code and tables placed | 30 527 bytes | 1 304 bytes |
| Variables | 73 784 bytes | 192 bytes |
| Placed once, as JSON (code in hex / in base64) | 64 028 / 43 678 bytes | 2 779 / 1 911 bytes |

Placed once at offset 0 (each relocated word zeroed, each relocation kept as position, base, addend), then applied at
the reference placement and at 40 random 4-aligned code and variable addresses with random patch-point values: the
same bytes, the same entry symbols and the same end of the variables as `relocate.place`, 41 out of 41 for each
package `[FAIT]`. It holds because the composer aligns both cursors to 4 (`compose.align4`) and no kept section asks
for more than 4.

## 2. B3a: the package in the page

- **`relocate.place()` splits in two.** `layout(obj, update, render, keep)` does what depends only on the object (the
  ELF reader, the garbage collection, the linker script's order, the alignments) and returns the code at offset 0,
  the relocations, the entry symbols and the size of the variables; `apply(layout, code_at, bss_at, values)` writes
  each relocation. `place()` becomes `apply(layout(…))`, so nothing the composer writes changes (`--compare-ld` and
  the generators' `--check` stay the proof). `layout` refuses a kept section aligned to more than 4: placed once,
  such an object would not be the same at every 4-aligned address.
- **The JSON form**, `relocate.bundle()`: `{"code": hex, "relocs": [[pos, base, addend], …], "symbols": {name: [base,
  offset]}, "bss": size}`, the base being `"code"`, `"bss"` or the name of a patch point. `gen_flasher_tweaks.py`
  derives it from the committed object when it writes `tweaks.js` (standard library, no firmware), so no new file is
  committed and its `--check` covers it.
- **`docs/flasher/composer.js`** (new, `window.MCComposer`, MIT): `place(bundle, codeAt, bssAt, values)` returns the
  bytes, the symbols and the end of the variables. It is `apply`'s loop.
- **Proof**, `tools/webcompose_check.sh` part 1, no firmware: for every package of `tools/machines/` that has an
  object, `place` in node at 40 or more placements equals `relocate.place` in Python.

## 3. B3b: the registrar frame

- **`compose.registrar_writes` splits in two.** `frame(img, reg, n)` gives what depends on n only: the 61 + 54
  writes, the `reloc`, the runtime and descriptor-copy parts, the addresses the fill reads. `fill(frame, stock,
  machines, blobs, bss_end)` gives the rest: the data block, the descriptors, the parameter block, the parts, the
  segments, the boot stub. `registrar_writes` becomes `fill(frame(…))`: one implementation, so the frame cannot drift
  from what the composer writes.
- **`tools/machines/registrar/frame.json`**, committed, n = 1 to 6 (the runtime's `max_machines`), written by
  `gen_registrar.py --cycles …`: the frame needs the official file as the runtime and the stub need the assembler,
  and `--check` compares all three. About 19 KB of compact JSON.
- **The stock values come from the user's file, not from the frame.** The 6 × 3 stock pointers of the name, update
  and render tables, the 6 bytes of the machine map and SNARE's five descriptors (280 bytes) are read in the user's
  MAIN OS at addresses the frame names, as the Python composer reads them in the official file. The frame carries
  positions, the short `old` bytes every tweak carries, and our own values: no new committed file carries Elektron
  data. The page therefore needs the depacked MAIN OS before it composes: `builder.js` exports `mainOsOf(raw,
  device)` (SysEx, container, depack of section 3, SHA-256 against `device.json`), and the page keeps the result
  with the OS file, so one more depack per file, not per build.

## 4. B3b: the composer in the page

`MCComposer.compose(mainOs, frame, packages, tweaks)` in `composer.js`, the port of `compose.compose` without its
toolchain paths:

1. the packages in the order given (card order, SAMPLE first until B4, notes/59 §6), machine `6 + i`, first
   descriptor `76 + 5 i`;
2. the layout: code from `pay`, variables from `pay + 0x36000`, both cursors aligned to 4; refused when the code
   passes `STUBS` or the payload runs into a package's `memory.ram` claim, or the `memory.ram` claims of two
   packages overlap (`checkRamClaims`, as `compose.check_ram_claims`, 2026-10-22);
3. `place` (§2) with the patch-point values;
4. `fill` (§3) with the stock values read in `mainOs`;
5. the packages' own hooks and vtable entries from their manifests (`package_writes`). Whether a vtable entry is the
   only reference to its method is a property of the stock OS: the Python composer checks it on every build
   (generators, `ref_mainos.py`); the page checks the entry's stock bytes like any write;
6. the conflicts: the rule of `computed_conflicts` against the tweaks the page embeds, plus the manifests' declared
   ones;
7. the tweak, as `compose.py` emits it: `id` (the package ids joined by `+`), `order`, `name`, `version`,
   `conflicts`, `writes`, `append`, `symbols`.

**Proof**, `tools/webcompose_check.sh <model-cycles_OS1.13.syx>` part 2: for `sampler`, `refmachine`, both pairs in
both orders, and the pair with `arp` and `trig-hold` built on top, the node tweak equals `compose.compose`'s (writes,
append, symbols; conflicts within the tweaks given), and `MCBuilder.build` gives the MAIN OS of `compose.build_syx`.
It needs the official file, as `ref_mainos.py` does.

## 5. B3c: the page

- **`tweaks.js`**: a machine card names its package (`"package": "sampler"`) instead of `variants`. The file embeds
  `packages` (the form of §2, plus what the composer reads from the manifest: the machine entry, hooks, vtables, RAM
  claims, patch points, entry symbols, `order`, `version`, declared conflicts) and `registrar` (the frame).
  `27-sampler.json` is no longer embedded; it stays in `tweaks/` for `check_overlaps.py`, `registry.py` and
  `build.py -t sampler`, and as the composer's committed output for SAMPLE alone. Size about as today: 64 KB of
  SAMPLE's code in hex and 19 KB of frame, against the 78 KB of `27-sampler.json`.
- **The cards' `excludes` against plain cards** are generated from each package's computed conflicts (its committed
  alone tweak), mapped to card ids, instead of copied by hand. §1.2: today the union of the alone conflicts is the
  pair's conflicts; the composer's own check (§4 step 6) refuses anything else at build time.
- **`app.js`**: `chosenTweaks()` composes the ticked package cards into one tweak, then adds the plain tweaks as
  today; `selOf`, `chosenLabels` and the variant sub-choice learn the package card. The build key, `REF_MODS` and
  `REF_MAINOS` work as today: SAMPLE alone composes to the id `sampler`, today's key.
- **`ref_mainos.py`** composes through `compose.compose` (it already reads the official file). `REF_MODS` gets one
  entry per non-empty set of offered package cards, in card order (2^k − 1 entries; today one, the same `sampler`
  entry as now), so every composed tweak the page can make is checked against Python's, not only the sample.
  `REF_MAINOS` keeps its sample. `Cards.options` learns the package card, as `app.js` does.
- **`flasher/index.html`** loads `composer.js` before `app.js`; the three pages get a new stamp.
- **`webflash_smoke.js`** is rewritten for model27's list (one card today), with a check that SAMPLE ticked composes
  and passes `REF_MODS` and `REF_MAINOS`.
- **Rules** in `docs/AGENTS.md` and `tools/AGENTS.md`: `composer.js` and `compose.py` (with `relocate.apply` and
  `fill`) stay equivalent, and a change to one goes into the other in the same commit, as for `builder.js` and
  `build.py`.

## 6. Order of work and done criteria

| Step | Work | Done when |
|---|---|---|
| **B3a** | `relocate.layout`, `apply`, `bundle`; `composer.js` `place`; `webcompose_check` part 1 | node = Python for both packages at 40 or more placements each; `compose.py --compare-ld` and the generators' `--check` pass unchanged |
| **B3b** | `compose.frame`, `fill`; `frame.json` from `gen_registrar.py --cycles`; `builder.mainOsOf`; `composer.js` `compose`; `webcompose_check` part 2 | node tweak = Python tweak and the same MAIN OS for the selections of §4; `27-sampler.json` and `28-refmachine.json` unchanged |
| **B3c** | `tweaks.js` with packages and frame; package cards; `app.js`; `ref_mainos.py`; stamp; smoke test; the AGENTS rules | `ref_mainos.py --check` passes with `REF_MODS["sampler"]` and `REF_MAINOS["sampler"]` (`ccdadb37…`) unchanged; `gen_flasher_tweaks.py --check`; the smoke test (maintainer: npm, network); one flash of SAMPLE from the page |

One commit per step, with the trailer. B3a and B3b add code and checks and change nothing on the page; B3c changes
what the page runs, not the firmware it builds.

Hardware: B3 changes no firmware byte for SAMPLE alone (the same MAIN OS as B2c's runtime build), so the firmware
needs no new test; the flash from the page after B3c checks the page. A second machine card brings its own hardware
tests.

## 7. What does not change

- `build()` in `builder.js`, `flasher.js`, the Samples OS tab, the plain tweaks and their cards.
- The command line: `compose.py`, `build.py`, the generators; `--relocator ld` and `--registrar b1` stay for
  development.
- The committed tweaks `27-sampler.json` and `28-refmachine.json`.
- The machine order: card order, SAMPLE first, until B4 gives each package a registry id.

## 8. Risks and open points

- **Alignment.** A future package with a section aligned to 8 or more cannot be placed once at offset 0; `layout`
  refuses it, and the page would then need the alignment rule too. `[HYP]` no package needs it: ColdFire code and
  tables here align to 4 at most.
- **Stale stamp.** B2a and B2c changed `tweaks.js` and the reference hashes of `app.js` under the same stamp. A
  browser that kept one of the two files from before refuses the build at the reference check; it never flashes a
  wrong one. B3c adds `composer.js` to the files that must change together: every commit that regenerates page data
  bumps the stamp, and the next commit to the page bumps it in any case.
- **Checks that need more than this sandbox.** The smoke test needs `npm` and the network (jsdom) and runs on the
  maintainer's machine; `webcompose_check` part 2 needs the official file.
- **Unicorn** (notes/60 §8): unchanged. B3 adds no code to the OS, only a second way to build the same bytes.
- **Two implementations of the fill.** Python stays the reference; the frame and the placed-once form keep the
  JavaScript to loops and arithmetic on data, and `webcompose_check` compares the two on every selection it builds.
- **Open for the maintainer:**
  1. *When.* B3 changes nothing users get until a second machine card exists. B3a and B3b are additions with their
     checks; B3c switches the page, provably to the same bytes. All three now, or B3c with the second machine.
  2. *The reference machine stays off the page* (never in `OFFERED`): the pairs are proven by `webcompose_check` and
     by command-line builds (digiemu, device), not from the page. A hidden switch to tick it on the page would be
     possible; it is not planned.
  3. *Hex or base64* for the packages' code in `tweaks.js`: hex, as everything else in the page (`fromHex`); base64
     would save 20 KB for SAMPLE.
  4. *A release entry*: none planned for B3, which changes nothing for users; the second machine card brings one.

## 9. Decisions (2026-10-22)

The maintainer took the four open points of §8 as recommended: **all three steps now**, one after the other, B3c only
once B3a and B3b are proven against Python; **the reference machine stays off the page**; **hex** for the packages'
code; **no release entry** for B3.

## 10. B3a built (2026-10-22)

- **`tools/relocate.py`**: `place()` is now `apply(layout(...))`. `layout()` does what depends only on the object
  (garbage collection, the linker script's order, the alignments) from offset 0 and keeps each relocation as
  (position, base, addend), the base being `code`, `bss`, `abs` or a patch point's symbol; it refuses a kept section
  aligned to more than 4. `apply()` writes the relocations at the build's 4-aligned addresses. `bundle()` is a layout
  as JSON for the page: the code in hex, the relocations, the symbols named, the variables' size.
- **Unchanged output**: `compose.py --compare-ld` identical to `ld` for SAMPLE and for REF then SAMPLE; `compose.py
  --machines sampler` still `27-sampler.json` (MAIN OS `ccdadb37…`); `gen_sampler.py` and `gen_refmachine.py`
  `--check` up to date.
- **`docs/flasher/composer.js`** (new, `window.MCComposer`): `place(bundle, codeAt, bssAt, values)`, `apply()`'s loop.
  Not loaded by the page yet (B3c).
- **Proof**: `tools/webcompose_check.sh` (no firmware; `tools/webcompose_synth.py` writes the reference, `tools/
  webcompose_check.js` compares): REF and SAMPLE each at 23 placements (where the composer puts them alone and in
  pairs, then random 4-aligned ones, the patch points at random values), the same bytes, entry symbols and end of the
  variables as `relocate.place`, 23 out of 23 `[FAIT]`.

## 11. B3b built (2026-10-22)

- **`tools/compose.py`**: `registrar_writes()` is now `fill(frame(...))`. `frame(img, reg, n)` gives what depends on n
  only: the writes, the reloc of the Algorithm parameter's maximum, the layout, the runtime, the stub template and the
  stock addresses. `fill(frame, img, machines, blobs, bss_end)` gives the rest: the data block, the descriptors, the
  parameter block, the payload parts, the segments and the boot stub. `frames()` gathers n = 1 to 6, the 61 shared
  writes listed once, and checks that `frame_of()` gives each frame back.
  - `web_package(mid)` is a package as the page reads it: from the manifest, the machine, hooks, vtable entries, RAM
    claims, patch points, symbols, order, version and declared conflicts; from the object, its layout at offset 0
    (`bundle()`).
  - `computed_conflicts()` and `compose()` take the tweaks to compute the conflicts against (by default the folder's,
    as before).
  - `fill()` gained two checks: a machine has four knobs (with DECAY, five descriptors), and it reads the stock
    tables for `first` machines instead of a literal 6 (the same value).
- **`tools/machines/registrar/frame.json`** (new): 31 663 bytes as committed, 19 837 as compact JSON.
  - Written by `gen_registrar.py --cycles …`; its `--check` now compares both `registrar.json` and `frame.json`.
  - It holds the 61 writes shared by every n and, for each n, 54 writes (the 53 of §1.3 and the marks site) and one
    reloc.
  - Its 385 writes carry 978 `old` bytes in all, none longer than 8, and its 6 relocs 4 each; the runtime and the
    stub template are `registrar.json`'s. That is positions, short old bytes and our own code and values, no Elektron
    data.
- **`builder.js`**: `mainOsOf(raw, device)` returns section 3 depacked, checked against `device.json` and refused
  without its SHA-256. `build()` is unchanged.
- **`composer.js`**: ports of the Python functions of the same names: `frameOf`, `fill`, `segments`, `bootStub`,
  `parameterBlock`, `packageWrites`, `computedConflicts`, and `compose(mainOs, frames, packages, tweaks)`, which returns
  `{ tweak, info }`. For a vtable entry the page checks its stock bytes; the Python composer still checks that it is
  the method's only reference (§4, step 5).
- **Proof**: `tools/webcompose_check.sh model-cycles_OS1.13.syx`, part 2 `[FAIT]`.
  - Five selections were composed: `sampler`, `refmachine`, both pairs in both orders, and `sampler,refmachine` with
    `arp` and `trig-hold`.
    - In each, the tweak from `composer.js` equals the one from `compose.compose` in id, order, name, version,
      conflicts, writes, append and symbols.
    - `MCBuilder.build` gives the same MAIN OS as `compose.build_syx`. SAMPLE alone gives `ccdadb37…`, which is
      `REF_MAINOS["sampler"]`; the others give `681b4b92…`, `d1765ab3…`, `88425970…` and `77d48896…`.
  - The conflicts are computed against the folder's 285 tweaks plus six probes:
    - the probes are a payload inside the composed payload, one inside SAMPLE's pool, one on the pool's last bytes, one
      just past it, a write of the same bytes as the boot hook's, and a write of other bytes there;
    - the probes are needed because the folder alone never decides the payload rule: each of its tweaks with a payload
      in our ranges also writes bytes of ours.
  - `fill` was compared for 1 to 6 synthetic machines, since the two packages reach n = 1 and 2 only. The machines have
    shared and unique names, knob ranges, gaps of 0 to 92 bytes between their codes, and a table above the stubs. Each
    gives the same writes and payload as `compose.fill`.
  - Mutation test, run once and not part of the check: ten deliberate changes to `composer.js` each make the check
    fail. They touch the parameter block (an entry's value, its size), a descriptor (its short name, a knob's range),
    a hook's `jmp` padding, the segments' merge distance, the string table, and the conflicts (the payload rule, the
    edge of a range, the same bytes).
- **Unchanged**:
  - `compose.py --compare` still matches `27-sampler.json` and `28-refmachine.json`;
  - `--compare-ld` and `--compare-b1` are identical for the four selections;
  - `gen_sampler.py`, `gen_refmachine.py` and `gen_registrar.py --check` are up to date;
  - `webbuild_check.sh`, `webflash_check.sh`, `gen_flasher_tweaks.py --check` and `test_compose.py --dry` pass;
  - no firmware byte changes, so the Unicorn proof (notes/60 §14) stands;
  - the page loads nothing new until B3c.

## 12. B3c built (2026-10-22)

- **`tools/gen_flasher_tweaks.py`**: the SAMPLE card is a machine card, `"package": "sampler"` in place of its
  variant.
  - `tweaks.js` embeds the package (`compose.web_package`) and the registrar's frame (the committed `frame.json`),
    and no longer `27-sampler.json`. That tweak stays in `tweaks/` for `build.py -t sampler`, `check_overlaps.py`,
    `registry.py` and as the composer's committed output.
  - A machine card takes no hand-written `excludes`. `machine_excludes()` computes them from the package's tweak
    alone (its `conflicts`) against the other cards offered; machine cards never exclude each other, since the page
    composes them together.
  - Today that gives no exclusion, because Control All Config goes with SAMPLE. The six ids copied by hand before
    (MACRO, ACID, the Syntakt engines, Model-TG, the track filter, sample preview) are exactly what the same rule gives
    over all of `ALL_FEATURES`, but none of those cards is offered. When one comes back into `OFFERED`, its exclusion
    with SAMPLE comes back by itself.
  - Size: `tweaks.js` is 112 650 bytes (92 850 before; the frame and the relocations take more room indented) and
    37 906 bytes gzipped (37 195 before).
- **`app.js`**:
  - `chosenTweaks()` gives the ticked machine cards one entry, where the first of them is. Its id is their package
    ids joined by `+`, and it stands for them (`{ id, machines }`): the build key, the selection and the Syntakt check
    work as before, before any OS file is read.
  - `makeCycles` composes it on the OS file (`composeMachines`): `MCBuilder.mainOsOf` once per file, then
    `MCComposer.compose` with the page's tweaks for the conflicts. The log says what was composed.
  - `selOf`, `chosenLabels` and the variant sub-choice know the machine card. SAMPLE alone keeps the key `sampler`.
- **`ref_mainos.py`** composes each non-empty set of machine cards with `compose.compose`, in card order, and adds
  each as one `REF_MODS` entry. `Cards` places them as `app.js` does. `REF_MODS["sampler"]` and the three
  `REF_MAINOS` entries came out unchanged (`--check` passes with `app.js`'s blocks untouched): the page's composed
  SAMPLE must give the bytes of `27-sampler.json`, and the whole MAIN OS `ccdadb37…`.
- **`flasher/index.html`** loads `composer.js` after `builder.js`. The stamp is now `2026-10-22-05` on the three
  pages.
- **Rules**:
  - `docs/AGENTS.md` describes the machine card and `composer.js`;
  - `tools/AGENTS.md` says that `compose.py`/`relocate.py` and `composer.js` change together, with
    `webcompose_check.sh`;
  - the root `AGENTS.md` notes that `tweaks.js` embeds the packages.
- **Proof** `[FAIT]`: `tools/webflash_smoke.sh` with the official Model:Cycles and Model:Samples files: 142 checks
  ok, `ALL OK`.
  - The page loads `composer.js` with the new stamp. SAMPLE is a machine card without a sub-choice, with the key
    `sampler` alone and `control-all-config,sampler` with Control All Config.
  - On the real OS, SAMPLE is composed in the page (machine 6, 123 writes, 36 096 bytes added to the OS). Its MAIN OS
    is `REF_MAINOS["sampler"]` and its tweak passes `REF_MODS`. The three combinations of the sample build, and a
    payload that differs from `REF_MODS` is refused.
  - On a Model:Samples, SAMPLE gives the two files of `tools/mods_for_samples.py` (`00ac0d94…`, `d4c5f2ae…`).
  - Also green: `gen_flasher_tweaks.py --check`, `ref_mainos.py --check`, `check_overlaps.py`, `registry.py
    --check`, `webbuild_check.sh`, `webflash_check.sh`, `webcompose_check.sh` with the official file.
- **Hardware**: SAMPLE's firmware is release 0.2's byte for byte (MAIN OS `ccdadb37…`), so the firmware needs no new
  test.
- **In a real browser** `[FAIT]` (maintainer, 2026-10-22): on the live page (stamp `2026-10-22-05`), with SAMPLE
  ticked and the official file loaded, the page logged these lines.
  - "Composed sampler: sampler as machine 6, 123 writes, 36096 bytes added to the OS."
  - "Built sampler: MAIN OS ccdadb3775ca…, 36630 bytes patched, 935456 bytes."
  - That is `compose.py --machines sampler`'s build: the same MAIN OS, the same 935 456-byte `.syx`, and 534 bytes
    written plus 36 096 added.
  - A build gets that far only once it passes `REF_MODS` and `REF_MAINOS["sampler"]`.
  - What B3c changed is how the page builds, and this check shows it in a real browser. It stands for the flash of
    §6: sending (`flasher.js`) is unchanged.
- **Limits**:
  - The page composes only on the official OS 1.13, since `mainOsOf` refuses any other MAIN OS. A custom OS file is
    sent as it is, as before.
  - Two machine cards that hook the same OS address would not be kept apart by the cards. The composer refuses
    their build ("writes overlap"), but the page lets you tick both.
  - A second machine card therefore needs its pairs proven, as `sampler,refmachine` is
    (`webcompose_check.sh`, notes/60 §12).
