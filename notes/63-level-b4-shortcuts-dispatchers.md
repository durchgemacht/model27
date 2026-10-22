# 63 — Level B, step 4: machine shortcuts and dispatchers, proven by a second reference machine (plan)

**Status: plan, 2026-10-22; the maintainer's decisions (§9); B4a built and proven in emulation (§10); B4b built and proven
in emulation (§11: `test_shortcuts.py` and `test_compose.py`, ALL OK); B4c built and proven in emulation (§12: `test_views.py`, `test_shortcuts.py`, `test_compose.py`, ALL OK); B4d built and proven in emulation (§13: the same three proofs, ALL OK); B4e built (§14): the web flasher composes them, the standard's draft 0.3.** What remains of increment B4 of [notes/59](59-level-b-builder.md) (§6) once the stable
ids were dropped ([notes/62](62-level-b4-stable-machine-ids.md) §9). It covers two pieces:

- the dispatcher tables for the hooks two packages share;
- the machine shortcuts, a fixed list of "key held + knob" combinations a machine may use on its own tracks.

The maintainer's aim: finish the machine standard with an internal second reference machine, REF2, before asking
anyone to port a machine, so that authors get a complete template they can follow, by hand or with an AI. Like REF,
REF2 is never offered on the page.

Facts marked `[FAIT]` come from reading the OS 1.13 code: the disassembly `_scratch/control-all/main.dis` (not
committed) and the image of the official `model-cycles_OS1.13.syx`, 2026-10-22. Nothing here was run in emulation
or on the device yet.

## 0. In short

- **The shortcut list, confirmed by the maintainer: RETRIG held + COLOR, SHAPE, SWEEP or CONTOUR.**
  - Four shortcuts; a machine opts in per knob.
  - In the stock OS, RETRIG held changes nothing when a knob turns, and RETRIG pressed without FUNC does nothing on
    the main screen.
  - Every other key is taken or unsuitable (§1). FUNC + knob is the stock fine adjust; PUNCH and GATE switch on the
    press, so PUNCH + DECAY cannot work.
- **Where a shortcut's value lives: machine-scoped slots.**
  - The four shortcuts use the four stock descriptors the OS leaves unused (1–4, "Error"), sound slots k 28–31 and
    record slots 28–31.
  - Each machine gives them its own name, range and display, so two machines can use the same shortcut without
    meeting. This is the track filter's layout ([notes/47](47-filtre-piste.md)), made per machine.
- **Dispatchers only where two packages meet.**
  - A shortcut value must be saved with the sound, so the shortcut layer uses `sound.record`, which SAMPLE uses
    too. That is the first dispatcher.
  - REF2 then uses every other hook SAMPLE uses (decided, §9): the main screen and the knob view, the screen's tick,
    the browser's file opening. Five dispatchers in all.
  - They dispatch by the machine of the sound or the track (the tick runs for all), as every hook of SAMPLE already
    decides by itself.
- **SAMPLE alone stays byte for byte.** The shortcut layer and the dispatchers are separate parts, written only into
  builds that need them: a machine declaring shortcuts, or two packages on one hook. The registrar runtime and
  `frame.json` do not change, and SAMPLE alone keeps `27-sampler.json` and `REF_MAINOS["sampler"]`.
- **Decided** (§9): no p-locks or LFO for shortcut values yet; the values stay when a track changes machine, a happy
  accident written down for users in [notes/64](64-projects-and-machines.md); all five hooks; Octave.

## 1. The keys, and what "key held + knob" does in the stock OS `[FAIT]`

### 1.1 Key codes

`isKeyHeld(code)` (`0x4007faf4`) takes a logical code and looks its bit up in the table at `0x4010ae5c` (the bitmap
is at `0x40f95744`).

| Code | Key | How it is known |
|---|---|---|
| 1 | FUNC | notes/44, 53, 55 |
| 2 | TRACK | notes/58 |
| 4 | RETRIG | notes/32 (the arpeggiator) |
| 5 | MACHINES | notes/47 (the track filter's `KEY_MACHINES`) |
| 6 | PUNCH | its press handler switches parameter 44, PUNCH (below) |
| 8 | LFO | held + knob calls `ParameterPageView::setLFO` (below) |
| 9, 10, 11 | RECORD, PLAY, STOP | TRACK + these copy, clear, paste (notes/58 §2) |
| 16–31 | TRIG 1–16 | notes/58 §2 |
| 3, 7, 12–15, 32 | not traced | — |

### 1.2 Who reads a held key while a knob turns

`ParameterPageView`'s encoder handler, `0x4001f4f0`, reads these held keys (all 33 calls of `isKeyHeld` were listed):

| Held key | Site | Stock meaning |
|---|---|---|
| LFO (8) | `0x4001f562` | the knob's parameter becomes the LFO's destination (`setLFO`, `0x4001eaa2`), unless code 12 is held too |
| code 12 | `0x4001f802` | leaves the normal edit when `0x4006ba76` says so |
| FUNC (1) | `0x4001f81e` | fine adjust: the new value comes from the interface object's function at `+0x50` (notes/55 §8.1) |
| TRACK (2) | `0x4001f88a` | Control All (notes/58 §1) |

RETRIG, PUNCH, GATE and MACHINES are not read there. Then:

- **The knob → descriptor lookup** `0x4001e814` (slot `+0x7c` of `ParameterPageView`'s vtable, `0x401005a8`) gets FUNC
  as an argument and reads the machine's record (17 descriptors at `+8`).
  - Entry `knob − 2` gives the descriptor: PITCH is knob 2, DECAY 3, COLOR 4, SHAPE 5, SWEEP 6, CONTOUR 7.
  - With FUNC, knobs 14 and 15 read entry `knob` instead.
  - The registrar's `knob_vec` sits inside it, at `0x4001e8da`.
  - It is called when a knob turns (`0x4001f6ee`), by TRACK + knob (`0x4001d716`), and by the popup at a track
    change (`0x4001f090`) (notes/47 §3.2).
- **MainScreenView's key handler** `0x4001c0d2` (entry `+8` of its vtable `0x400ffe20`, RTTI `14MainScreenView`)
  switches on codes 1 to 32 (a jump table at `0x4001c100`).
  - PUNCH (6), on a press without FUNC, switches parameter 44 through `0x4001ac4a`; FUNC + PUNCH opens a view.
  - GATE switches parameter 45 through the same function (`0x4001ca9c`); its code was not traced.
  - RETRIG (4) is handled only with FUNC: FUNC + RETRIG opens the retrig menu. A press alone goes on to the views
    below, where `KeyboardView` uses RETRIG held for the trig keys (retrigs, notes/32).
  - LFO (8) opens a view on a press.
- **The other reads of RETRIG** are not on the knob path either. `0x4001d482` is in `0x4001d3de`, which lights LED 27
  (`0x1b`, through the LED singleton `0x400cfaf4`) while RETRIG is held. `0x4001d56a` is in a key handler
  (`0x4001d506`) that notes TRACK and RETRIG pressed together, in a flag at `+112` of its view.

### 1.3 The list

| Key held + knob | Stock | Verdict |
|---|---|---|
| **RETRIG + COLOR / SHAPE / SWEEP / CONTOUR** | the knob edits as usual | **the list** (confirmed 2026-10-22) |
| FUNC + knob | fine adjust | not on the list: the maintainer kept the stock fine adjust |
| TRACK + knob | Control All | taken |
| LFO + knob | LFO destination | taken |
| MACHINES + knob | nothing in the stock OS; the track filter (all tracks) and Model-TG use it | taken in the standard (§5.4) |
| PUNCH / GATE + knob | the press switches PUNCH / GATE | unsuitable: every use would switch them |
| code 12 + knob | read by the encoder handler | taken |
| TRIG + knob | parameter lock | taken |
| RETRIG + PITCH / DECAY | the knob edits as usual | left out: pitch and the amp decay work alike on every machine |

The list stays a property of the builder. A package that declares another combination is refused, and the standard's
gesture registry records the four as machine-scoped.

## 2. The second reference machine, REF2

- **Package and contract.** It is a package like REF (`tools/machines/refmachine2/`, MIT, C99) with the same voice
  contract and stock amp chain (standard §2). Like REF, it is never on the page.
- **Its sound.** REF's sine and noise, plus one shortcut: **RETRIG + COLOR = Octave**, −2 to +2. It is audible, easy
  to check in emulation (the frequency doubles or halves), and the value is saved with the sound.
- **Its other hooks** (every point SAMPLE uses, §9), each with a visible effect for the proofs:
  - **`view.main`:** on a REF2 track the main screen shows a small `REF2 OCT +1` label;
  - **`view.knob`:** while the Octave value is shown, the knob view draws it as REF2 likes;
  - **`screen.tick`:** a dot in the label blinks with the tick;
  - **`browser.open`:** a file opened on a REF2 track has its name shown in the label, and the OS then opens it as
    before (REF2 takes no file).
- **How it reads the value.** The voice loop hands every machine the track's parameters, k 0–32, in `p`. REF2 reads
  k 28 and does nothing else for the shortcut: the shortcut layer does the rest.

## 3. The shortcut layer

### 3.1 How a shortcut reaches the knob

- **A hook in the knob → descriptor lookup.** It goes after the record entry is read (6 bytes at `0x4001e908`:
  `movea.l d0,a1 ; move.l (8,a1,d3.l*4),d2`) `[HYP]`. The site and its register contract are to be proven in
  emulation.
- **What it does.**
  - When RETRIG is held, and neither FUNC, TRACK, LFO nor a trig key is held, it looks up the track's machine.
  - If that machine declared a shortcut for this knob, it returns the shortcut's descriptor (1 to 4) instead of the
    machine's own.
  - It writes the machine's names, range and default into that descriptor, and the machine's formatter into the
    descriptor's interface object, as the track filter installs its formatters at each call (notes/47 §3.3).
- **Why it stays out of p-locks and the LFO.** Holding a trig, LFO, TRACK or FUNC turns the redirection off. Values
  of k ≥ 23 break the stock p-lock file (notes/47 §4.3: they land on LFO Speed), and the LFO destinations have the
  same problem (§4.2). In the first version a shortcut value is neither p-locked nor an LFO destination (§9,
  decision 1).
- **The table.** "Machine → its four shortcuts" is a table the composer fills; the code is assembled once and
  committed, as the registrar runtime is (`tools/machines/registrar/`). The page fills the same table in JavaScript.

### 3.2 Where the values live

| Shortcut | Descriptor | Sound slot | Record slot |
|---|---|---|---|
| RETRIG + COLOR | 1 | k 28 | 28 |
| RETRIG + SHAPE | 2 | k 29 | 29 |
| RETRIG + SWEEP | 3 | k 30 | 30 |
| RETRIG + CONTOUR | 4 | k 31 | 31 |

- **Machine-scoped.** A slot means what the track's machine says. A sound saved on one machine and played on another
  plays the other machine with the same values: the happy accident of notes/62 §9.
- **Saving.**
  - The stock save keeps only k 0–22, and the load reads record slots 0–23 (notes/47 §4.1).
  - The layer saves k 28–31 into record slots 28–31 after the stock save and puts them back after the load, for
    every sound whose machine declared shortcuts.
  - Those are the three functions SAMPLE hooks: `sound.record`, at `0x4005afa0`, `0x4005b054` and `0x4005aecc`.
- **SAMPLE's slots are untouched.** SAMPLE keeps record slots 24–27 on SAMPLE sounds and reads them only there
  (`smp_after_save`, `smp_after_load`), so SAMPLE could use shortcuts too.
- **Copying a sound.** The stock copy of a sound's changes stops at k 22 (`0x4005aa54`, notes/47 §4.4). The track
  filter left this one `[HYP]`, and the layer needs it checked on the device: copy and paste of a sound, preset
  load, kit reload.
- **Conflicts.** This layout clashes with the track filter (descriptors 1–4, k 28–31, slots 30–31), lfo-plus (k
  28–32, slots 30–31) and Model-TG (slots 24–29). model27 offers none of them, and the composer computes the clash
  from their writes as for any tweak.

## 4. Dispatchers

### 4.1 Rule: only where two packages meet

- **A point used by one package keeps the direct hook it has today.** SAMPLE alone therefore writes exactly its
  bytes, with no dispatcher in the build.
- **Two packages on one point get a dispatcher.** The composer writes the point's hook to the dispatcher and fills
  its table. This is the standard's §3.3: code assembled once and committed, a table the builder fills, the same in
  Python and in JavaScript.
- **Every hook SAMPLE has today is machine-scoped.** Each one decides by itself whether the sound or the track plays
  SAMPLE (`is_sample`, `sample_sound`), and otherwise calls the stock code. So the dispatchers dispatch by machine:
  "call the handler of this machine, otherwise the stock code". SAMPLE's code is unchanged; it is only called for
  SAMPLE sounds and tracks.

### 4.2 The points

| Point | Sites | SAMPLE's entries | Dispatch |
|---|---|---|---|
| `sound.record` | save v2 `0x4005afa0`, save v1 `0x4005b054`, load `0x4005aecc` (a `jmp` over their first 8 bytes) | `smp_after_save`, `smp_after_load` (today wrapped by `smp_hook_save2/1`, `smp_hook_load`) | the "around" wrapper once, then the "after" function of the sound's machine and the shortcut layer's |
| `view.main` | vtable entry `0x400ffe30` (stock `0x4001b22a`) | `smp_main_draw` | the draw of the selected track's machine, otherwise the stock draw |
| `view.knob` | vtable entry `0x4010053c` (stock `0x4001e40a`) | `smp_knob_draw` | the same |
| `screen.tick` | `0x400075f0` (`jsr 0x40076be4`) | `smp_hook_tick` | append: every tick runs (SAMPLE loads samples whatever the track) |
| `browser.open` | `0x400a6602` (`jsr 0x400a3052`) | `smp_hook_open` | the opened track's machine |

- **REF2 uses all five** (§9): `sound.record` through the shortcut layer, the four others through its own handlers
  (§2). Every point SAMPLE uses is thus proven with two packages before the call for machines.
- **SAMPLE's manifest** names its "after" and draw functions for the dispatchers. Its object does not change: the
  functions are already global symbols and go into `keep`.

## 5. The manifest and the builder

- **New `uses` entry**, for example:

  ```json
  {"point": "shortcut", "key": "RETRIG", "knob": "COLOR",
   "param": {"long": "Octave", "short": "OCT", "min": 0, "max": 4, "default": 2, "format": "ref2_fmt_oct"}}
  ```

  `format` is optional: a machine function writes the value's text, three characters as the OS shows them.
- **Dispatch fields.** A `view.main` or `sound.record` entry names the machine's function. The builder decides whether
  it goes in directly or through a dispatcher.
- **What the builder refuses:**
  - a shortcut outside the list;
  - two shortcuts on one knob;
  - a hook point without a dispatcher when two packages want it;
  - more than four shortcuts per machine.
- **Python and JavaScript change together.** `compose.py` and `composer.js` fill the shortcut table, the descriptors'
  fields and the dispatcher tables in the same commit, and `webcompose_check.sh` gets the new cases.
- **Committed parts.** `tools/machines/shortcuts/` holds the layer's code assembled once, and
  `tools/machines/dispatch/` the dispatchers, each with its generator and `--check`, like `registrar.json`.

## 6. Proofs and done criteria

- **SAMPLE alone.** `compose.py --machines sampler` still gives `27-sampler.json` byte for byte, and
  `REF_MAINOS["sampler"]` is unchanged. This is checked at every step.
- **Python.** REF2 alone, REF2 + SAMPLE and SAMPLE + REF2 compose; the descriptors 1–4 carry REF2's fields; the
  dispatcher tables hold both packages.
- **JavaScript.** `webcompose_check.sh` gives the same tweaks and MAIN OS for the new selections.
- **Emulation** (`tools/emu/`, run by the maintainer, since Unicorn stops in the sandbox), on the OS's own code:
  - RETRIG + COLOR on a REF2 track edits k 28, and the value window shows `OCT` and the value;
  - without RETRIG the knob is REF2's own;
  - with a trig, LFO, TRACK or FUNC held there is no redirection;
  - on a SAMPLE track COLOR is SAMPLE's Start, with or without RETRIG;
  - k 28 survives save v2 and load; a SAMPLE sound keeps its key;
  - the main screen shows the REF2 label on a REF2 track and SAMPLE's waveform on a SAMPLE track; the knob view
    likewise;
  - both ticks run; a file opened on a REF2 track reaches REF2's handler and then the OS, and one opened on a SAMPLE
    track reaches SAMPLE's;
  - the voice loop plays REF2 an octave up at +1.
- **Device** (maintainer): REF2 alone and with SAMPLE.
  - the shortcut, the display, the octave;
  - save and reload the project, copy and paste a sound, load a preset, which also settles §3.2's `[HYP]`;
  - SAMPLE as before.

## 7. Order of work

| Step | Work | Done when |
|---|---|---|
| **B4a** | REF2 without the shortcut and without `view.main`: a plain second package | composes; webcompose and emulation as for REF |
| **B4b** | the shortcut layer (getParam hook, descriptors 1–4, `sound.record` save and load), REF2's Octave, the `sound.record` dispatcher with SAMPLE | §6 Python and emulation for the shortcut and the save; SAMPLE alone unchanged |
| **B4c** | the `view.main` and `view.knob` dispatchers, REF2's label and its knob view | §6 for the display |
| **B4d** | the `screen.tick` and `browser.open` dispatchers, REF2's blinking dot and file name | §6 for the tick and the browser |
| **B4e** | `composer.js`, the page's tables, `webcompose_check`; the standard 0.3 (the shortcut list, the slots, the dispatchers) and APPLYING (written so that an AI can port a machine from it) | JavaScript equals Python; the standard's examples are REF2's manifest |
| device | the maintainer's tests of §6 | before the call for machines |

One commit per step, with the trailer. None of them changes SAMPLE's firmware alone, so none needs a release entry;
the page changes only in B4e, without new cards.

## 8. Decisions for the maintainer

*Answered in §9.*

1. **P-locks and LFO for shortcut values:** left out of the first version (recommended), or made possible with the
   track filter's fix of the p-lock file (`tf_ptab`, notes/47 §4.3) and its LFO and velocity handling (§4.2).
2. **When a track changes machine:** the shortcut values stay as they were, a happy accident (recommended, nothing to
   hook), or they take the new machine's defaults (one more hook on the machine change, `0x4001477e`).
3. **Which shared hooks REF2 covers:**
   - `sound.record` and `view.main` (recommended);
   - or also `view.knob`, `screen.tick` and `browser.open`, so that every point SAMPLE uses is proven before the
     call.
4. **REF2's sound and name:** Octave on RETRIG + COLOR as above, or another audible use.

## 9. Decisions (2026-10-22)

1. **P-locks and LFO:** left out of the first version. A shortcut value is neither p-locked nor an LFO destination;
   holding a trig or LFO keeps the knob on its usual parameter.
2. **When a track changes machine:** the shortcut values stay, and the new machine reads them its own way, a happy
   accident. The maintainer asked for this, with the other happy accidents and the advice to keep one project per
   build, to be written down for users and later put on the site: [notes/64](64-projects-and-machines.md).
3. **Hooks:** REF2 covers every point SAMPLE uses: `sound.record`, `view.main`, `view.knob`, `screen.tick` and
   `browser.open` (§2, §4.2), so that the standard is complete for machines before the call.
4. **REF2:** Octave on RETRIG + COLOR, −2 to +2.

## 10. B4a built (2026-10-22)

- **`tools/machines/refmachine2/`** (MIT): REF2 is REF's contract and code with three changes:
  - its symbols are `ref2_update` and `ref2_render`, so that a build with both has no clash;
  - its voice marker at `+0x2c` is `'REF2'`, so that a track switching between REF and REF2 restarts;
  - it plays a triangle in place of REF's parabola, so that the two are told apart by ear and in the proofs.

  Its manifest is REF's with order 29, the name REF2, and tests not yet run.
- **`tools/gen_refmachine.py`** now writes both reference machines: `28-refmachine.json` and `29-refmachine2.json`,
  and the committed objects `refmachine.o` (unchanged) and `refmachine2.o`.
- **Measured.**
  - REF2 alone is 116 writes, 1 282 bytes of code and tables, 192 bytes of variables, and 6 852 bytes added to the
    image; its MAIN OS is `59d3a916…`.
  - `--compare-ld` is identical to `ld` and `--compare-b1` to B1 for REF2 alone, SAMPLE + REF2, REF2 + REF, and the
    first build of three machines, SAMPLE 6, REF 7 and REF2 8. That build has 39 428 bytes added, B1's detours 854
    bytes against the runtime's 826, a parameter block of 64 bytes, and MAIN OS `32467e74…`.
- **Conflicts.** With a new tweak in the folder, the composer computes one conflict more for the machines already
  there: `27-sampler.json` and `28-refmachine.json` gain `refmachine2` in their `conflicts`, and nothing else. Their
  writes and payload are unchanged, so `REF_MODS`, `REF_MAINOS` and the page stay as they are. `REGISTRY.md` lists REF2
  at the registrar's sites and its payload.
- **SAMPLE alone is unchanged.** `compose.py --machines sampler` gives `27-sampler.json`'s writes, payload and symbols
  identical, and the MAIN OS `ccdadb37…`.
- **Checks.**
  - `webcompose_check.sh` with the official file: REF2 placed at 23 placements; REF2 alone, SAMPLE + REF2 and the
    three machines identical between JavaScript and Python, MAIN OS included.
  - Also green: `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`, `ref_mainos.py
    --check`, `gen_registrar.py --check`, `webbuild_check.sh`, `webflash_check.sh`, and `test_compose.py --dry` with
    the three new selections.
- **Emulation** `[FAIT]` (the maintainer's run of `tools/emu/test_compose.py`, Unicorn on the OS's own code,
  2026-10-22): **ALL OK** for the seven selections: SAMPLE, REF, both pairs, REF2, SAMPLE + REF2, and SAMPLE + REF +
  REF2.
  - Each starts up: the bootstrap reads the grown OS back, and the boot hook copies the payload and clears the BSS.
  - The registrar's mechanics pass for each, and the runtime equals B1's detours input for input.
  - The three machines:
    - nine names and nine marks on the MACHINES page, on two rows;
    - the machine setter takes 6, 7 and 8 and refuses 9; the wheel stops at 8;
    - records 7, 8 and 9 are SAMPLE's, REF's and REF2's, and a real machine change goes Chord → SAMPLE → REF → REF2;
    - machines 9, 10 and 100 fall back to KICK's record and knobs, with no access outside memory.
  - The voice loop:
    - REF2 plays the same, sample for sample, as machine 6, 7 or 8, and does not sound like REF;
    - REF plays the same as machine 6 or 7;
    - SAMPLE with no sample stays silent;
    - SNARE on track 1 is the stock OS's in every build.

## 11. B4b built (2026-10-22)

### 11.1 What was built

- **The shortcut layer, a part of the builder** (`tools/machines/shortcuts/`, MIT): `shortcuts.S`, assembled once by
  the new `tools/gen_parts.py` into the committed `shortcuts.o` (466 bytes of code, 4 relocations, no variables), and
  `part.json` (schema `model27-part/0.1`): the recipe, the roots, the patch point `sc_data`, the list (RETRIG + COLOR,
  SHAPE, SWEEP, CONTOUR), descriptors 1–4, slots 28–31, the sites and the layout of the data block.
  - **`sc_knob`** replaces the knob → descriptor lookup in `ParameterPageView`'s vtable (`0x401005a8`, stock
    `0x4001e814`). It calls the stock lookup first. With RETRIG held and FUNC, TRACK, LFO and every trig released, on a
    knob 4–7 that the track's machine declared, it writes descriptor `knob − 3` and its interface object, then returns
    that descriptor; otherwise it returns the stock answer.
  - **`sc_save2`, `sc_save1`, `sc_load`** take the first 8 bytes of the three record functions (`jmp` + `nop`). Each
    runs the next of the chain (a package's own wrapper, or the 8 bytes and the stock body), then copies k 28–31 into
    record slots 28–31 (save) or back (load).
- **`tools/compose.py`**:
  - `load_part()` reads a part;
  - `shortcut_uses()` checks the machines' `shortcut` entries against the list;
  - `shortcut_layer()` places the part after the packages, writes its data block after its code, writes the vtable
    entry and the three record sites, and chains a package's record wrapper;
  - `package_writes()` skips the record sites the layer chains.

  A build whose machines declare no shortcut gets no part and does not change.
- **REF2**:
  - its manifest declares `{"point": "shortcut", "key": "RETRIG", "knob": "COLOR", "param": {"long": "Octave",
    "short": "OCT", "min": -2, "max": 2, "default": 0}}`;
  - `refmachine2.c` reads k 28 at `p + 0x38`, clamps it to −2..2 and adds 12 semitones per octave.

  `29-refmachine2.json` is regenerated with 120 writes, 4 more than in B4a: the vtable entry and the three record
  sites.
- **`tools/emu/test_shortcuts.py`**: the proof on the OS's own code (§11.4), to be run by the maintainer.

### 11.2 Where B4b departs from §3, and why `[FAIT]` (code reading)

1. **The hook is the vtable entry**, not 6 bytes at `0x4001e908`.
   - This is the track filter's way, tested on the device (notes/47 §3.2), and the lookup has no direct call: the
     three OS calls go through the entry.
   - Nothing is patched inside the lookup, so the registrar's `knob_vec` there stays as it is.
2. **FUNC is the held key** (`isKeyHeld(1)`), not the lookup's FUNC argument, so that the three call sites behave
   alike. The trig is `0x4006b736(0x400cf9a8())` (`UIStates + 356`, the hold of notes/33), as in SAMPLE's `TRIG_HELD`.
3. **Descriptors 1–4 keep machine −1** (the track filter's are 7).
   - The tables built at boot (`0x4005a274`) leave them out, so a shortcut value is in no row, CC, NRPN or LFO
     destination list.
   - The edit path reads a descriptor's machine in `0x4001dff4`, where −1 goes the way of machines 0–9: the track's
     sound.
   - The value setter `0x4000b274` clamps with `blt`/`ble` (signed) to the range from `0x4005a65a`, so −2..+2 works.
4. **The layer also writes `+0x14` = 0, CC and NRPN = −1 and `+0x20` = 0.**
   - The stock "Error" descriptors 1–3 carry CC 1/33, 2/34 and 6/38 at `+0x18`, which the OS would send when the value
     is edited.
   - Their `+0x14` is 1 and their `+0x20` is 1–4; every parameter's descriptor has 0 there, and so do the track
     filter's.
   - The display is the stock integer formatter `0x400456c8`, signed (`asr`). A machine may name its own (`format`, a
     kept symbol of its object).
5. **k 28–31 are saved and loaded for every sound**, not only for the machines with shortcuts.
   - This is simpler, and a value kept through a machine change (notes/64 §3) survives a save too.
   - The copy runs only when the function did its work, its result byte being 1. The saves and the load return 0 for a
     null record or sound, and the load also for a record of another version than 2, which it leaves untouched.
6. **A machine change keeps the values without a hook**, as decision 2 wants.
   - `0x40014072` resets only the five parameters of the new machine's record (entries 1–5, the list at `0x400feb7c`).
   - The full initialisation (`0x400618f2` → `0x40061866`: new project, cleared sound) writes every k, 0 where the
     machine's rows have no descriptor. A new sound therefore starts with k 28–31 at 0.
7. **0 is every shortcut's default**, a rule of the builder.
   - A new sound, a sound saved before the machine had the shortcut and a sound from the official OS all read 0.
   - `shortcut_uses()` refuses another default, a range without 0 or beyond −128..127, names outside printable ASCII,
     and a short name of more than 4 characters.
8. **`sound.record` with SAMPLE is a chain**, not a dispatcher table.
   - The layer's wrapper runs first and calls SAMPLE's own wrapper as the next one (`sc_data` +0..+8); SAMPLE's jump
     is then not written. SAMPLE's object and manifest do not change.
   - A second package with a wrapper on the same record function is refused (one wrapper behind the layer).
     B4c and B4d bring the dispatchers for the other points.
9. **`composer.js` does not know the layer yet.** That comes with B4e, as §7 orders it, against §5's "in the same
   commit". Until then `webcompose_synth.py` leaves REF2, never offered, out of its selections (`tools/AGENTS.md`).

### 11.3 Measured

| Build | Writes | Added to the image | Layer (code + data) | MAIN OS |
|---|---|---|---|---|
| SAMPLE alone | 123 | 36 096 | none | `ccdadb37…`, unchanged |
| REF2 alone | 120 | 7 484 | 466 + 127 at `0x43000528` | `18161a83…` |
| SAMPLE + REF2 | 124 | 38 468 | 466 + 223 at `0x43007c68` | `0aaf5b0c…` |
| REF2 + SAMPLE | 124 | 38 468 | 466 + 223 at `0x43007c68` | `ea3045a1…` |
| REF + REF2 | 120 | 9 200 | 466 + 223 at `0x43000a40` | `163c175c…` |
| SAMPLE + REF + REF2 | 124 | 40 252 | 466 + 319 at `0x43008180` | `7dd3c1ab…` |

- The data block holds 20 bytes of header, 96 bytes per machine (4 knobs × 24) and the strings.
- With SAMPLE, the chain is SAMPLE's three wrappers (`smp_hook_save2`, `smp_hook_save1`, `smp_hook_load`).
- **Conflicts.** `29-refmachine2.json` gains `track-filter`, computed (the vtable entry and the record sites). Nothing
  else changes in `tweaks/`.

### 11.4 Checks

- **Static checks, green:**
  - `compose.py --machines sampler --compare 27-sampler.json`: writes, payload and symbols identical;
  - `--compare-ld` and `--compare-b1` for the six builds above;
  - `gen_parts.py --check`, `gen_refmachine.py --check`, `gen_sampler.py --check` and `gen_registrar.py --check`;
  - `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check` and `ref_mainos.py --check`;
  - `webcompose_check.sh` (REF2's object at 23 placements; the five selections without REF2 identical);
  - `webbuild_check.sh`, `webflash_check.sh`, `py_compile`, and `test_compose.py --dry`.
- **Emulation** `[FAIT]` (the maintainer's run of `tools/emu/test_shortcuts.py`, Unicorn on the OS's own code,
  2026-10-22): **ALL OK** for the four builds: REF2 alone, SAMPLE + REF2, REF2 + SAMPLE, and SAMPLE + REF + REF2.
  - **The sites:** the vtable entry and the three record functions jump into the layer. With SAMPLE, the chain ends
    in SAMPLE's three wrappers, and their own jumps are not written.
  - **The knob, 1 792 to 2 240 cases per build:** descriptor 1 for RETRIG + COLOR on REF2 only. Every other case gets
    the stock answer: the 15 other knobs, the other machines (stock, SAMPLE, REF, one past the last, 100, −1), no key
    held, and FUNC, TRACK, LFO or a trig held with RETRIG. The stock lookup is called once each time with the same
    arguments, and the stack comes back.
  - **Descriptor 1:**
    - its fields: k 28, −2..+2, default 0, no CC, no NRPN, Octave / OCT, machine −1, the other descriptors untouched;
    - the OS's range getter reads (−512, 512, 0);
    - its value setter clamps −1000 and −513 to −512, and 513 and 1000 to 512;
    - interface object 1, from the OS's own constructor, shows "-2" to "2".
  - **The tables built at boot** are identical with descriptor 1 installed: rows, CC rows, k → descriptor, CC, NRPN.
  - **Save and load:**
    - versions 2 and 1 give the stock record plus k 28–31 in slots 28–31 (bytes 84 to 90 differ);
    - the load gives them back, and everything else as the stock load;
    - a version 1 record is refused as before, and the sound is left as it was;
    - a record from the official OS loads them at 0;
    - a SAMPLE sound keeps its key, and its record is otherwise that of SAMPLE's build alone.
  - **A real machine change** into REF2, from CHORD, SAMPLE or REF: REF2's knobs at their defaults, k 28–31 kept.
  - **The voice loop:** REF2 at Octave +1 and note 48, and at −1 and note 72, plays note 60 at 0, sample for sample;
    +3 plays as +2; REF ignores k 28.
  - The first run stopped in the test itself, before the save: its random sound held a velocity destination that the
    stock save reads as a table index without a bound (`0x4005b02e`). The test sound now carries valid destinations,
    as `test_track_filter.py`'s does.
- **`test_compose.py`** `[FAIT]` (the maintainer's run, 2026-10-22): **ALL OK** for its seven selections. The three
  with REF2 now carry the layer in their payload.
  - Each build starts up: the bootstrap reads the grown OS back, and the boot hook copies the payload.
  - The registrar's mechanics pass, and the runtime equals B1's detours input for input.
  - REF2 plays the same as machine 6, 7 or 8 at Octave 0, and SNARE plays as in the stock OS, sample for sample.
- **Device:** not tried. The tests of §6 apply, with REF2 alone and with SAMPLE: the shortcut and its display, the
  octave, saving and reloading the project, copying a sound (`0x4005aa54`, `[HYP]`) and loading a preset.

## 12. B4c built (2026-10-22)

### 12.1 What was built

- **The dispatchers, a second part** (`tools/machines/dispatch/`, MIT):
  - `dispatch.c`, compiled once by `tools/gen_parts.py` into the committed `dispatch.o` (230 bytes of code, 6
    relocations, no variables);
  - `part.json`: the recipe, the roots `dp_main` and `dp_knob`, the patch point `dp_data`, the two sites
    (MainScreenView's draw entry `0x400ffe30`, stock `0x4001b22a`; the knob view's `0x4010053c`, stock `0x4001e40a`)
    and the layout of the data block (first machine, number of machines, one table of 6 draws per point).

  Each dispatcher finds the selected track's machine as SAMPLE's views do: the project singleton's track
  + 212 + t × 68, the sound from the method at +40 of its vtable, the machine in the sound's byte +38. It then calls
  that machine's draw from its table, or the stock draw, with the same arguments (GCC makes it a `jmp`).
- **`tools/compose.py`**:
  - `dispatch_layer()` takes each point of the part that two or more packages use: the entry goes to the part's
    dispatcher, and the table gets each package's draw at its machine;
  - a point one package takes keeps that package's own entry, so SAMPLE alone, REF2 alone and SAMPLE + REF do not
    change;
  - only the dispatchers a build needs are placed (they are the layout's roots), after the shortcut layer;
  - `package_writes()` skips the entries a dispatcher takes.
- **REF2's views**, in the new `refmachine2/ref2_view.c`:
  - `ref2_main_draw`: on a REF2 track and without a value window, the stock main screen, then `OCT +1` (`OCT 0`,
    `OCT -2`, …) in the free band of its right half;
  - `ref2_knob_draw`: while the Octave is shown on a REF2 track and no trig is held, OCTAVE and five boxes, −2 to
    +2, the current one filled, the values below; any other case draws the stock knob view;
  - the machine number comes from a patch point, `ref2_machine_index` (kind `machine_index`), as SAMPLE's
    `cm_machine_index` does;
  - the manifest gains the `view.main` and `view.knob` entries, the two draws in `keep`, and `claims.views`.

  `29-refmachine2.json` is regenerated: 122 writes, 2 more than in B4b, the two vtable entries, written directly since
  REF2 is alone there.
- **`tools/emu/test_views.py`**: the proof (§12.4), to be run by the maintainer.

### 12.2 Decisions in the build, and why `[FAIT]` (code reading)

1. **The dispatcher picks by the selected track's machine, and the machine's draw still checks the track.**
   - Both points concern the selected track, and SAMPLE's draws already decide that way.
   - With its own check kept, a machine's draw works the same whether it is the only one on the point (its entry,
     no dispatcher) or one of several (through the dispatcher).
   - The dispatcher spares the other machines' draws the calls on tracks that are not theirs. SAMPLE's object and
     manifest do not change: its draws were already kept symbols, named in its `view.main` and `view.knob` entries.
2. **The dispatchers are C, not assembly**, because they call the OS the way SAMPLE's C does. The data block is a
   struct behind the patch point.
3. **Where the label goes.** The stock main draw (`0x4001b22a`) shows:
   - the left half as a lit panel (filled, then turned over: `0x40070dea` with colours 1 and −1);
   - the right half dark, with "TRn" centred at x 96 on rows 34..42 (`0x4001b6ba`), the pan bar at y 25
     (`0x4001b754`) and the level bar at y 12 (`0x4001b7e4`);
   - while `0x40a744c8` is set, a sign at x 65, y 58 (`0x4001b844`).

   Rows 44..56 of the right half stay free. The label is centred at x 96 from row 46, in the small font, 9 rows high.
4. **The knob view's case** is SAMPLE's test for Start and Length, with REF2's descriptor:
   - descriptor 1 at the view's `+0x230`, where the encoder handler keeps the lookup's answer (`0x4001f73a`);
   - a value window open;
   - no trig held.
5. **Still to come.**
   - The `screen.tick` and `browser.open` points come in B4d, which extends the part's data block.
   - `composer.js` does not know the dispatchers yet either: that is B4e, and `webcompose_synth.py` still leaves REF2
     out.

### 12.3 Measured

| Build | Writes | Added to the image | Dispatchers (code + data) | MAIN OS |
|---|---|---|---|---|
| SAMPLE alone | 123 | 36 096 | none | `ccdadb37…`, unchanged |
| SAMPLE + REF | 123 | 37 760 | none | `d1765ab3…`, unchanged |
| REF2 alone | 122 | 8 636 | none: REF2's entries | `44fad54f…` |
| SAMPLE + REF2 | 124 | 39 904 | 230 + 52 at `0x4300839c` | `0392f11d…` |
| REF2 + SAMPLE | 124 | 39 904 | 230 + 52 at `0x4300839c` | `0933c755…` |
| SAMPLE + REF + REF2 | 124 | 41 688 | 230 + 52 at `0x43008914` | `44d5e5e1…` |

- REF2's object is 2 470 bytes of code and tables, 1 152 more than in B4b: its two views.
- With SAMPLE, the tables hold SAMPLE's and REF2's draws at their machines, and 0 at REF's.
- **Conflicts:** unchanged. REF2's new entries only meet SAMPLE's, a conflict already listed. `REGISTRY.md` lists
  the two entries for REF2 and SAMPLE, with two values depending on the build.

### 12.4 Checks

- **Static checks, green:**
  - `compose.py --machines sampler --compare 27-sampler.json`: writes, payload and symbols identical;
  - `--compare-ld` and `--compare-b1` for the six builds above;
  - `gen_parts.py --check` (both parts), `gen_refmachine.py --check`, `gen_sampler.py --check` and
    `gen_registrar.py --check`;
  - `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check` and `ref_mainos.py --check`;
  - `webcompose_check.sh` (REF2's new object at 23 placements, the five selections without REF2 identical);
  - `py_compile` and `test_compose.py --dry`.
- **Emulation** `[FAIT]` (the maintainer's runs, Unicorn on the OS's own code, 2026-10-22): **ALL OK** for
  `test_views.py` (with `--show`), `test_shortcuts.py` and `test_compose.py`, on their default builds.
  - **`test_views.py`**, four builds (REF2 alone, SAMPLE + REF2, REF2 + SAMPLE, SAMPLE + REF + REF2):
    - the sites: REF2 alone writes its two draws itself; with SAMPLE, both entries go to the dispatchers, whose
      tables hold SAMPLE's and REF2's draws at their machines;
    - the dispatchers call the selected track's machine's draw or the stock one, once with the same arguments, for
      every machine, a track past 5 and no project;
    - REF2's main draw, with the OS's own text code and small font: the label only in the free band of the right
      half, five different labels, nothing on another track or with a value window open. With `--show` (REF2
      alone), `OCT +1` lies at x 79..113, rows 46..54, and the five values take 68 to 77 pixels;
    - REF2's knob draw: the blanked screen and its five boxes, and the stock view in every other case. The picture
      shows OCTAVE on rows 50..58, the boxes on rows 20..35 with +1 filled, and −2, −1, 0, +1, +2 under them on
      rows 6..14.
  - **`test_shortcuts.py` and `test_compose.py`** on the B4c builds, where the dispatchers lie in the payload next to
    the shortcut layer: the results of §11.4 again.
- **Device:** not tried. To check with REF2 alone and with SAMPLE:
  - the label on the main screen, and that it hides nothing (with the sign at x 65 shown too);
  - the boxes while RETRIG + COLOR turns;
  - SAMPLE's waveform and its Start and Length views as before.

## 13. B4d built (2026-10-22)

### 13.1 What was built

- **The dispatch part, version 0.2**, with two more dispatchers. The data block grows from 52 to 100 bytes, with a
  tick table at +52 and a browser table at +76. `dispatch.o` is 418 bytes of code with 14 relocations.
  - `dp_tick` sits at `0x400075f0`, the `jsr 0x40076be4` in the screen's redraw. It calls every machine's tick in
    machine order, then the stock `0x40076be4` once, and returns its answer.
  - `dp_open` sits at `0x400a6602`, the browser's `jsr 0x400a3052` (`open.S`):
    - it keeps the call's registers and stack: a0 = &result, a2 = the browser, d2..d7 with d4 = the entry's index;
    - it asks `dp_open_pick` (C) for the hook of the machine of the track the browser loads into (the browser's
      +664), or the stock open;
    - then it jumps there.
  - `dp_main` and `dp_knob` do the same as in B4c. Their machine lookup is now shared with the browser's
    (`machine_of`), so their bytes change.
- **`tools/compose.py`**: `dispatch_layer()` takes hook sites as well as vtable entries.
  - A hook counts as the same point when another package has a `jsr` at the same address with the same stock bytes.
  - The dispatcher's `jsr` goes there, and `package_writes()` skips the package's own.
- **REF2** (`ref2_view.c`, new `ref2_open.S`):
  - `ref2_hook_tick` counts the ticks. Every 16th tick, on a REF2 track without a value window, it asks the main
    screen for a redraw with View::setNeedsRedraw (`0x40076082`), on the view its draw last got. It returns
    `0x40076be4(view)`.
  - The label gains a dot at x 120..121, rows 49..50, lit while the number of ticks divided by 16 is odd: it blinks
    about once a second.
  - `ref2_hook_open`, on a REF2 track:
    - asks the browser's list (+640, method +16) for the entry's name, with the index in d4;
    - keeps the name's first 15 characters;
    - destroys the string (`0x400f7d5c`);
    - jumps to the stock open with the call's registers.

    On another machine's track it goes straight to the stock open.
  - The label shows the name's first 10 characters for the next 6 redraws of that track, then OCT again. The redraws
    come every 16 ticks, so the name stays for about 3 s.
  - The manifest gains the `screen.tick` and `browser.open` hooks, the two hook functions in `keep`, and
    `ref2_open.S` in the sources.

  `29-refmachine2.json` has 124 writes, 2 more than in B4c: the two hooks, which REF2 alone writes itself. REF2's
  object is 3 200 bytes of code and tables and 220 bytes of variables.
- **`tools/emu/test_views.py`** gains sections 5 and 6, and the tick's and the browser's dispatchers in section 2.

### 13.2 Decisions in the build, and why `[FAIT]` (code reading)

1. **The tick goes to every machine.**
   - `0x40076be4(view)` only reads the view's byte +32, whether the view needs drawing.
   - So every machine's tick may end with it, as SAMPLE's does, and the dispatcher calls it once more for the answer
     it gives.
   - SAMPLE's tick and manifest do not change.
2. **The browser goes by the track it loads into**, the browser's +664 as SAMPLE's hook reads it, not by the selected
   track.
3. **`dp_open` keeps the call's registers.** SAMPLE's hook takes a0 and a2, and REF2's takes d4 too.
   - Its C helper is called with them kept: a0 on the stack, d2..d7 and a2 by the C ABI.
4. **The file's name comes the way the OS gets it.**
   - Right after the open, the browser asks its list (+640) for the entry's name: method +16, with the index in d4
     (`0x400a661a..0x400a662c`).
   - The method writes a std::string at a0, and the browser destroys it with `0x400f7d5c` (`0x400a663e`).
   - REF2 does the same before the open. d4 holds the index from `0x400a6518` to that call.
5. **The redraw is the OS's own.**
   - MainScreenView's 1 Hz timer binds View::setNeedsRedraw (`0x40076082`, `0x4001bffc`), which sets the view's +20
     and its screen's +32.
   - REF2 calls it every 16 ticks, on the view its draw last got, only on a REF2 track without a value window.

### 13.3 Measured

| Build | Writes | Added to the image | Dispatchers (code + data) | MAIN OS |
|---|---|---|---|---|
| SAMPLE alone | 123 | 36 096 | none | `ccdadb37…`, unchanged |
| SAMPLE + REF | 123 | 37 760 | none | `d1765ab3…`, unchanged |
| REF2 alone | 124 | 9 364 | none: REF2's entries and hooks | `105b3740…` |
| SAMPLE + REF2 | 124 | 40 868 | 418 + 100 at `0x43008674` | `bbde0178…` |
| REF2 + SAMPLE | 124 | 40 868 | 418 + 100 at `0x43008674` | `1a14e092…` |
| SAMPLE + REF + REF2 | 124 | 42 652 | 418 + 100 at `0x43008bec` | `8c92546a…` |

- With SAMPLE, all four tables hold SAMPLE's and REF2's methods at their machines.
- **Conflicts:** unchanged. `REGISTRY.md` lists REF2 at the tick and browser sites, with two targets depending on the
  build.

### 13.4 Checks

- **Static checks, green:**
  - `compose.py --machines sampler --compare 27-sampler.json`: writes, payload and symbols identical;
  - `--compare-ld` and `--compare-b1` for the six builds above;
  - every generator's `--check`, `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check` and
    `ref_mainos.py --check`;
  - `webcompose_check.sh` (REF2's object at 23 placements);
  - `py_compile` and `test_compose.py --dry`.
- **Emulation** `[FAIT]` (the maintainer's runs, Unicorn on the OS's own code, 2026-10-22): **ALL OK** for
  `test_views.py` (with `--show`), `test_shortcuts.py` and `test_compose.py`, on their default builds.
  - **`test_views.py`**, four builds:
    - the four sites and their tables;
    - the draws' dispatchers;
    - the tick's dispatcher: every machine's tick in machine order, then the getter once;
    - the browser's dispatcher: the hook of the right track's machine, with a0, a2, d4 and the stack as at the call;
    - REF2's label and knob view as in §12.4;
    - REF2's tick: the redraws at ticks 16 and 32, and the dot lit, then dark;
    - REF2's browser hook: the name asked of the list, the string destroyed, the stock open with the call's
      registers, and the name shown for 6 redraws of that track.
  - **`test_shortcuts.py` and `test_compose.py`** on the B4d builds: the results of §11.4 again.
- **Device:** not tried. To check:
  - on a REF2 track, the dot blinks about once a second;
  - opening a preset from the browser on a REF2 track shows its name for about 3 s, and the OS loads the preset as
    before;
  - with SAMPLE, samples still load, and the browser still opens samples on SAMPLE tracks.

## 14. B4e built (2026-10-22)

### 14.1 What was built

- **`docs/flasher/composer.js`** gains `shortcutUses()`, `shortcutLayer()` and `dispatchLayer()`, the ports of
  `compose.shortcut_uses()`, `compose.shortcut_layer()` and `compose.dispatch_layer()`.
  - `compose()` takes the builder's parts as a fifth argument and adds them as `compose.compose()` does.
  - `packageWrites()` skips the sites the parts take.
  - The tweak's symbols gain the parts' symbols.
- **`compose.web_part()`** gives a part as the page reads it: its object laid out once with all its roots
  (`relocate.bundle`), its sites, the layout of its data block, its patch points, the shortcut list and its declared
  conflicts.
  - `gen_flasher_tweaks.py` embeds both parts in `tweaks.js` next to the registrar's frame (5.4 KB more).
  - `app.js` passes them to `MCComposer.compose`.
  - `web_package()` now passes the `shortcut` entries on.
- **The dispatch part is placed whole** as soon as one point is shared, so that it has one layout the page can embed.
  Before, only the dispatchers of the shared points were placed. No build changes: every build so far shares all four
  points or none, and all MAIN OS hashes stay as in §13.3.
- **A declared conflict of the shortcut layer** (`part.json`, `conflicts_declared`): lfo-plus.
  - lfo-plus keeps its LFO 2 in k 28..32 and packs it into record slots 30..31 from inside the stock save and load
    (`0x4005b028`, `0x4005b0dc`, `0x4005af1c`; notes/56).
  - It writes no byte the layer writes, so the composer did not compute the clash. With both, the layer would show
    lfo-plus's words as the machines' shortcuts and overwrite its packed slots.
  - `compose()` and `composer.js` now add the part's declared conflicts to a build that has the layer:
    `29-refmachine2.json` gains `lfo-plus` (267 conflicts).
- **`webcompose_synth.py`** places both parts' objects at 23 placements, as it does for the packages. Its selections
  include REF2 again: REF2 alone, SAMPLE + REF2, REF2 + SAMPLE, SAMPLE + REF + REF2. `webcompose_check.js` passes the
  parts to the composer.
- **The pages' stamp** goes to `2026-10-22-06` (`composer.js`, `app.js` and `tweaks.js` change). The page does not
  change for users: SAMPLE alone needs neither part, so no release entry.
- **`tools/AGENTS.md`**: the Python-only exception of B4b to B4d is gone.
- **The standard**, `cycles-mod-standard`, draft 0.3:
  - `STANDARD.md`:
    - §3.1: the points as model27 dispatches them, and the `shortcut` point;
    - §3.2: the "by machine" rule;
    - §3.3: the parts;
    - §4.2: the `shortcut` entry;
    - §5.1: option C;
    - §5.2 to §5.4: k, record slots and keys;
    - §7.4: REF2's manifest, the template;
    - §8 to §11.
  - `APPLYING.md` §12, porting a machine to model27's builder, step by step, with a prompt for an AI assistant, and
    the inventory's table brought up to date.
  - The README's status.

### 14.2 Checks

- `webcompose_check.sh` with the official file:
  - the three packages and the two parts identical to `relocate.place` at 23 placements each;
  - the nine selections identical to `compose.py`: tweak (writes, payload, symbols, conflicts) and MAIN OS. Among
    them: REF2 alone `105b3740…`, SAMPLE + REF2 `bbde0178…`, REF2 + SAMPLE `1a14e092…`, SAMPLE + REF + REF2
    `8c92546a…`;
  - `fill` for 1 to 6 synthetic machines.
- Every generator's `--check`, `gen_flasher_tweaks.py --check`, `ref_mainos.py --check` (`REF_MAINOS` and `REF_MODS`
  unchanged), `check_overlaps.py`, `registry.py --check`, `webbuild_check.sh`, `webflash_check.sh` and `py_compile`.
- `compose.py` against B4d (`72c6298`) for the eight selections of the Unicorn tests: the same writes and payload;
  only the conflicts of the builds with REF2 gain `lfo-plus`. The emulation runs of §13 hold for B4e.
- `webflash_smoke.sh`, the page in jsdom with both official files, run by the maintainer because it needs
  `registry.npmjs.org`, which this sandbox blocks: ALL OK, 142 checks and one skip (three cards outside the sample:
  only two plain cards are offered). The pages load with the stamp `2026-10-22-06`; SAMPLE composed in the page
  still gives `REF_MAINOS["sampler"]`, MAIN OS `ccdadb37…`.
- **Device:** nothing new to test for users. The B4b to B4d tests of §11.4, §12.4 and §13.4 still apply to REF2.
