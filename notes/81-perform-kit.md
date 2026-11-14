# 81 — Perform Kit: a pattern change keeps the sounds (2026-11-14)

The maintainer's request (2026-11-14): « Kits », meaning the PERFORM KIT mode of the Digitakt II (its manual, 10.10):
with the mode on, a pattern change keeps the sounds as they are, tweaked, instead of loading the new pattern's kit.
Checked the same day against the Model:Cycles OS 1.13 and the Digitakt II OS 1.17, decided through the questions of
§2, planned, built and tested on a Model:Cycles in one day. This note is that plan as it grew: the sections are in
the order of the work, and a later section corrects an earlier one where it says so (§10.1 against §10).

**In short.** The builder's part `perform` (`tools/machines/perform/`, 0.4; `compose.py --perform`, the card
Perform Kit, `82-perform.json`): SETTINGS + PATTERN switches a mode in which the sequencer's change of the playing
kit copies bytes 0..693 of the kit (the six track sounds, the six levels, the four effect values; not the pool of
lock sounds) into the kit of the pattern about to play, keeps that pattern's own bytes and gives the pattern left
its own back. The kit serializer hands out the pattern's own bytes, so nothing of the mode is saved until the
pattern is; Save Pattern and Reload Pattern make what is saved or loaded the pattern's own. A popup at the switch
and a checkerboard stripe on the main screen show the mode. Proven by `tools/emu/test_perform.py` and tested on a
Model:Cycles (§8.1 to §10.1); the card is experimental until flashed from the page (§11).

`[FAIT]` = read in a disassembly on 2026-11-14 (the Model:Cycles OS 1.13; the Digitakt II OS 1.17, whose MAIN OS
loads at `0x40000400`); `[HYP]` = not proven when written; what became of each is in the later sections.

## 1. What the player gets

- **Mode on:** the sounds stay over pattern changes: the six track sounds (machine, parameters, LFO, sends, Track FX,
  SAMPLE's sample), the six levels and the four effect values (Delay Time, Feedback, Reverb Size, Tone). The
  sequence changes as always: trigs, parameter locks, sound locks, tempo, length, scale.
- **Save:** the stock Save Pattern (FUNC + SETTINGS held, or the menu): with the mode on it saves the tweaked kit
  with the sequence, and the tweaked kit is the active pattern's kit from then on. No gesture of its own.
- **Reload:** the stock Reload Pattern (FUNC + PATTERN held, or the menu): the pattern's saved sequence and kit; the
  mode stays on. The pattern's own kit without the +Drive: mode off and on again. No gesture of its own.
- **Mode off:** the tweaked kit is dropped; the active pattern plays its own kit again.
- **The pattern the mode was switched on in** is never written.
- **Temp save and temp reload** (FUNC + SETTINGS, FUNC + PATTERN) work inside the mode as in any pattern. What was
  temp-saved inside the mode does not come back after the mode is off.
- **Nothing is permanent:** power-on starts with the mode off; a change stays only after Save and then the OS's own
  Save Pattern / Save Project.
- **Not part of this plan:** a kit library. The stock PRESET menu's SAVE KIT and LOAD FOLDER stay as they are.

## 2. Decisions

Taken by the maintainer (2026-11-14):

| # | Question | Answer |
|---|---|---|
| 1 | What belongs to the kit | everything of the sound; checked against the Digitakt II (§3.2): sounds, levels, send effect values yes; locks no |
| 2 | Kit library (slots, names) | may be left out; the stock SAVE KIT / LOAD FOLDER is enough |
| 3 | Where does Save write | into the active pattern |
| 4 | The pattern the mode started in | untouched |
| 5 | Mode off | drops the tweaked kit |
| 6 | Temp save inside the mode, then mode off | dropped, as on the Digitakt II |
| 7 | Gesture | **SETTINGS + PATTERN** switches the mode on and off; Save and Reload are the stock Save Pattern and Reload Pattern (the maintainer, 2026-11-14: « die haben ja die gleichen tastenkombinationen »); the display: an indicator first, the pattern's name inverted perhaps later |

Proposed, not confirmed:

| # | Question | Proposal |
|---|---|---|
| 8 | The way to build it | the copy way (§4): **confirmed by the maintainer, 2026-11-14** |
| 9 | model27's choice of the delay / reverb effect (pattern header 29..31) | follows the pattern: **decided by the maintainer, 2026-11-14** (« nein, lass es erstmal so »); the card says so |
| 10 | CHORD Tables' table per pattern (pattern header 36..37) | follows the pattern: decided with 9; the card says so |
| 11 | Project load, pattern copy / paste / clear while the mode is on | open (P0); simplest: they switch the mode off first |

## 3. What was read

### 3.1 Model:Cycles OS 1.13 `[FAIT]`

- **Memory.** 96 patterns at `0x406fa040 + 30710 n`, 96 kits at `0x409c9c80 + 7094 n` (accessor `0x400d1bb8`).
  A kit: head `+0..27` (version, name, six levels), six track sounds of 100 bytes from `+28`, the effect block
  `+628..693` (66 bytes; saved form: four 8.8 words from kit `+638`, seen in a backup with the defaults 23 / 42 / 64),
  the pool of 64 lock sounds from `+694`. **The kit without its pool is bytes `0..693`.**
- **The sequencer gets pairs** (pattern, kit): `0x40055cd6(list, n)` fills the table `0x40a7863c` (8 bytes an entry);
  stopped, `0x40055c38(pattern, kit)` at once. Every kit pointer of the sequencer comes from there.
- **The change** in the sequencer's interrupt `0x40054c1e`: `0x40054d22..0x40054d70` (queued pattern), `0x4005568c..
  0x4005571e` (chain), `0x4005549e..0x40055572` (stop); playing pattern `0x40a7887c`, playing kit `0x40a78888`. Then
  message 2 to the audio side (`+16` = kit), which sets `0x800017e4` and clears the six current-sound pointers
  (`0x40058ddc`): each track takes its sound at its next trig.
- **Sound locks** come from the kit the sequencer plays: `0x40054bda..0x40054c0a` (kit `+694 + 100 i` when the pool
  sound is valid, else the track sound).
- **The interface binds itself in one function:** `0x4000f36a(obj, force)` compares the bound kit with the playing
  pattern (`0x4006a96c`) and calls `0x40009a1e(obj + 116, n, 1, 0)`: six track objects ← kit `+28 + 100 t`, the effect
  object ← kit `+628`, the pool ← kit `+694`. It runs after the real change, not when the change is queued.
- **Temp area** (P0): project slot 96 on the +Drive, one sequence and one kit per pattern, like a saved project.
  Sequence: save `0x4000fe3c(obj, temp, n)`, load `0x4000ff26`. Kit: save `0x4001002c(obj, temp, n)` (serializer
  `0x4005b2ae(buffer, kit, 0)` at `0x400100ba`, 7680 bytes), load `0x400106de` (loader `0x4005d080`, then the
  refresh `0x400d1f98(obj + 116, n, 0)` at `0x400107c0`).
- **Save and reload of a pattern** (P0): `0x4001040e(project, temp, n, seq, kit)` saves, three callers: FUNC +
  SETTINGS (`0x4001c5b4`, temp 1) and Save Pattern (`0x40038f78`, `0x40038fbe`, temp 0; a save to the project also
  writes the temp slot). `0x400107d8(project, temp, n, seq, kit)` reloads (in notes/80 §3 the last two are named
  the other way round). Both act on the playing pattern only. The record with the pattern at `+4` and the kit at
  `+30714` (37 812 bytes, `0x40010a4a`) is the copy clipboard, not the temp area.
- **The mirror** (P0): every kit has a saved-form mirror in RAM (96 × 7680 bytes, the layout of a `.mcprj`).
  `0x40009a1e` binds the interface's objects to it as well, and a change notice serializes the whole kit n from
  `0x409c9c80 + 7094 n` into it (`0x40009252`, `0x40009600`, `0x40009630`). So a kit the mod writes needs that
  notice, or its mirror keeps the old bytes.
- **A knob** (P0, from cycles-sampler's TECHNICAL.md, read there): the interface writes the sound and calls the audio
  side's `0x40059534(value, track, k)`, which puts the word straight into the voice's targets; the audio side copies
  a sound's 66 parameter bytes only when a note's sound pointer differs from the track's last one.
- **Power off** (P0, by name only): `Brain::saveProjectBackupSync`, string « SaveBackupProject » pushed at
  `0x40006b62`; `Project::updateTempProjectIfNecessary` (`0x4001011e`) writes the whole project to the temp slot
  once, when the slot belongs to another project. Neither body was read.

### 3.2 Digitakt II OS 1.17 `[FAIT]`, field names not checked by offset

- 129 kits; slot 128 is the perform kit. On: the active pattern's whole kit is copied into it (`0x40035e12`) and
  bound (`0x40036cba`). Off: the pattern's kit is bound again, nothing copied back. The flag is cleared at boot.
- Reload (PRESET/KIT + NO): the active pattern's kit into slot 128 again.
- Save pattern, project or temp (`0x40047fe6`, `0x400437a2`): the perform kit goes into its own slot 128; the
  pattern's kit stays. PRESET/KIT + YES opens SAVE (KIT); its body was not followed.
- A kit is `trackSounds`, `fxParams`, `midiParams`, levels; a pattern is `tracks`, `parameterLocks`,
  `patternSettings`; the sound pool is an object of the project.

## 4. The design: the copy way

### 4.1 State

`on`; `home`, the pattern whose kit holds the tweaked sounds now; `orig[694]`, that pattern's own bytes `0..693`;
a second buffer of 694 bytes for the change; `temp_dirty`, set by a temp save inside the mode.

### 4.2 What happens when

| Event | The mod |
|---|---|
| Mode on, in pattern A | `orig` ← kit A `0..693`; `home` = A |
| The real change A → B, in the sequencer, before message 2 | second buffer ← kit B `0..693`; kit B `0..693` ← kit A `0..693`; note A as left |
| The interface's `0x4000f36a`, before it binds B | kit B `0..693` ← kit A `0..693` once more (a knob turned across the change); kit A `0..693` ← `orig`; the buffers change roles; `home` = B |
| Reload Pattern from the project (`0x400107d8`, temp 0), after it loaded | `orig` ← kit `home` `0..693`: the loaded kit is the pattern's own |
| Save Pattern (`0x4001040e`, temp 0), before it saves | `orig` ← kit `home` `0..693`: the tweaked kit is the pattern's own, and the serializer's hook lets it through |
| Mode off | kit `home` `0..693` ← `orig`; `0x4005950e` for the audio side, `0x400d1f98` for the interface; every pattern temp-saved inside the mode gets its kit saved to the temp slot again (`0x4001002c(obj, 1, n)`) |
| Temp save | stock (the tweaked kit goes to the temp slot); the pattern is noted |
| Temp reload (`0x400107d8`, temp 1) | stock: the temp slot's kit is the tweaked kit now; `orig` stays |
| Any other serialization of `home`'s kit (Save Project, power off, mirror, SysEx) | the hook at `0x4005b2ae` gives `orig` (§5) |

The pool is never copied, so each pattern's sound locks play their own sounds. Interface and audio keep using the
active pattern's kit, as on the stock OS.

### 4.3 Cost

- CPU: nothing per audio block. Per pattern change two copies of 694 bytes in the sequencer's interrupt, two more in
  the interface. Counted in §7.1 and §8.1.
- RAM: two buffers of 694 bytes, one of 7094 bytes for the serializer's copy, a set of 96 bits and a few bytes of
  state, in the standard's `memory.ram`.

### 4.4 The other way, not taken

A kit of its own as on the Digitakt II: hooks at `0x4000f36a`, `0x40055cd6` / `0x40055c38`, and an exception for
the pool in the event builder and in `0x40009a1e`. The 96 kits would stay untouched, but the saved mirror has 96
places only and about 15 places compute a kit from the pattern's number.

## 5. P0 (2026-11-14): answered and still open

Answered, by reading:

1. **A knob across the change.** The audio side gets a knob's value directly (§3.1), so a sound's bytes may change
   under a note. A knob turned between the sequencer's copy and the interface's second copy reaches the voice at
   once; the track's first note in the new pattern copies the bytes without that last step, and the knob's next
   step writes it again. Accepted.
2. **Two changes before the interface ran** (a chain of very short patterns): the sequencer's hook then does the
   interface's part itself (kit A ← `orig`) before it goes on. A knob step in that window may land in kit A's own
   bytes; accepted for this case only.
3. **The refresh after a kit was written:** `0x400d1f98(obj + 116, n, 0)`, as the kit load calls it. Whether it also
   makes the audio side copy the six sounds again is `[HYP]` (the kit message clears the pointers only when the kit
   pointer changes, `0x40058dd2`).
4. **The temp area** is per pattern, on the +Drive (§3.1). So « temp-saved inside the mode, dropped after » means:
   the mod keeps a set of the patterns temp-saved inside the mode and, when it leaves such a pattern or the mode
   goes off, saves that pattern's kit to the temp slot again from its own bytes (`0x4001002c(obj, 1, n)`), a write
   to the +Drive.
5. **Saving a kit** always goes through `0x4001002c` → `0x4005b2ae` (7 callers: temp save, Save Pattern, the reload's
   copy to the temp slot, four SysEx receives). Save Pattern inside the mode must write `orig`: the hook at
   `0x400100ba` hands the serializer a copy of the kit with `orig` in bytes `0..693` (a buffer of 7094 bytes) when
   n is `home` and the save is not a temp save.
7. **Other parts at these places** (the ones the flasher offers): only `transpose` (the reload's call `0x4001c19c`)
   and `shortcuts` (`0x4001c274`) write inside MainScreenView's PATTERN case; nothing writes at the sequencer's
   change, at `0x4000f36a`, `0x40009a1e`, `0x4001002c` or `0x400106de`. Found by searching the parts' and tweaks'
   files for addresses, not by a composer run. `fxslot` and Chord Keys hook the pattern load (`0x4005b4b0`), which
   this part does not touch.

Changed by P0:

- **One hook keeps every saved form clean.** Every serialization of a kit goes through `0x4005b2ae(buffer, kit, 0)`:
  Save Pattern and the temp save (`0x400100ba`), the whole project `0x4005d18a` (its kit loop at `0x4005d356`; five
  callers, among them the backup at power off `0x4000fd46` ← `0x40006550` ← `Brain::saveProjectBackupSync`
  `0x40006b1a`, which serializes the project from RAM into 2 163 716 bytes), the mirror's three lambdas, two SysEx
  sends. A hook at its entry hands it, for `home`'s kit, a copy with `orig` in bytes `0..693` (a buffer of 7094
  bytes), except during a temp save by FUNC + SETTINGS. So Save Pattern, Save Project, the backup at power off, the
  mirror and a SysEx dump always hold the pattern's own kit, also after a power cut. **The weak point named
  before is gone; the copy way stays the proposal.**
- **The mirror** then needs no notice after the mod's copies; only Save sends `home`'s change notice.
- **The audio side after Reload and mode off:** `0x4005950e(kit)` sets the kit and clears the cached pointers of the
  six sounds (`0x800017ec`), the six levels (`0x80001804`) and the effect block (`0x800017e8`); each is taken again
  at the next note (`0x4005902c..0x400590f8`). The interface: `0x400d1f98(obj + 116, n, 0)`.
- **SAVE KIT, LOAD FOLDER, preset load, sound copy / paste** act on the active pattern's kit, which holds the
  tweaked sounds: they work on what is heard, with no hook. By the design, not read. SAVE KIT so stores the tweaked
  sounds as a folder of six presets.
- **`fxslot`'s effect choice and CHORD Tables' table** are in the pattern's header (`+29`, 3 bytes; `+36`, 2 bytes,
  from their claims), not in the kit. Keeping them with the mode needs the same mechanism a second time on the
  pattern's side (copy at the change, `orig`, a hook in the pattern serializer `0x4005ba0a`). Proposed: not in the
  first version; they follow the pattern.

Still open (to read in P3, they do not change the design):

6. The entries of project load, pattern paste and pattern clear, where the mode is switched off first.
12. Whether a temp save by FUNC + SETTINGS can be told from the other callers of `0x4001040e` at the hook
    (its call is `0x4001c5b4`).

### 5.1 The gesture SETTINGS + PATTERN, checked 2026-11-14

- **Free:** no stock meaning (no stock code asks whether SETTINGS is held, notes/79 §1; PATTERN's press arms the
  pattern selection whatever else is held, PatternGridView `0x40020a7a` → `0x40020ad0`), and no claim of a part, a
  package or a tweak names it (`tools/claims.py --list`, `claims.json`): the claims with these keys are SETTINGS +
  RECORD (`resample`), PATTERN + SWEEP (`chordtables`) and PATTERN + REVERB-SIZE / DELAY-TIME (`fxslot`).
- **The settings menu stays closed:** SETTINGS opens it on a tap only, and its release after PATTERN is not a tap
  (notes/79 §1, on the device with SETTINGS + RECORD). Held for 1 s before PATTERN, SETTINGS asks to save the
  project, as in the stock OS.
- **PATTERN's press must be taken** while SETTINGS is held, or the pattern selection arms. A place free of other
  parts: `0x40020ad0` (`lea 0x400cf9a8,%a3`, 6 bytes); `fxslot` writes at `0x40020a7a`, `0x40020bda..0x40020bea` and
  `0x40020dca`, `chordtables` at `0x40020dca`. `[HYP]` until composed.
- **« SETTINGS is held » is not free of cost:** on the device isKeyHeld(13) answered 0 (notes/79, the fix of
  Resample 0.2); `resample` therefore keeps SETTINGS' state itself, from its events, through the key code accessor
  `0x4007240c` (`rs_code`, `set_held`). `perform` needs the same state. Both cards cannot write those 6 bytes, so
  the state becomes a piece both use (as the shortcut layer is shared), or `perform` reads `resample`'s when that
  card is in the build and brings its own otherwise. To decide in P1 with the composer.

## 6. Steps

| Step | What | Proof |
|---|---|---|
| P0 | Read §5; fix the hooks and their bytes; decisions 8–11 and the gesture with the maintainer | by reading; this plan updated |
| P1 | Part `perform`: state, mode on / off by a provisional switch, the change (sequencer + `0x4000f36a`) | `test_perform.py` (Unicorn, the maintainer's terminal): changes queued, chained, stopped; a knob across the change; sound locks; stock side by side |
| P2 | Reload, Save, mode off, temp save / reload | the same test, extended |
| P3 | The hook at `0x4005b2ae`; project load, pattern paste / clear switch the mode off | the same test, extended |
| P4 | Later, if wanted: `fxslot`'s effect choice and CHORD Tables' table stay with the mode | `test_fxslot.py`, `test_chordtables.py` + `test_perform.py` |
| P5 | Gesture, display, part.json, claims, both composers, card | smoke test, digiemu |
| P6 | Device test, one test after the other | the maintainer |

## 7. P1 built (2026-11-14)

Worktree `model27-perform`, branch `perform` (from main `7f62956`).

- **The part** `tools/machines/perform/`: `perform.c` (the state, the copies, the switch), `entries.S` (`pk_seq_d0`,
  `pk_seq_d2`, `pk_seq_fp`, `pk_ui`, `pk_pattern`, `pk_code`), `part.json` (seven sites, the data block of 1400
  bytes, the claim SETTINGS + PATTERN), `host_os.h` and `test_perform.c` (the host test). 1130 bytes of code.
- **The sites:** the sequencer's four writes of the playing kit `0x40054d6a`, `0x40055510`, `0x4005571e`,
  `0x40055c62` (6 bytes each, `jsr`); the interface's kit selection `0x4000f36a` (8 bytes, `jmp` and a nop);
  PatternGridView's PATTERN case `0x40020ad0` (6 bytes, `jsr`; a taken event ends the handler at its epilogue
  `0x400212c6` with d3 = 1); the key code accessor `0x4007240c` (`jmp pk_code`), left out in a build with RESAMPLE,
  where `pk_held` is RESAMPLE's `set_held`.
- **The composer:** `compose.py --perform`, `perform_layer`; `gen_parts.py` builds the object. composer.js (the
  page) is not written: P5.
- **Mode off** puts `home`'s own bytes back, calls `0x4005950e(the playing kit)` and `0x400d1f98(project + 116,
  home, 0)`.
- **Proven here:** the host test, ALL OK, 320 checks (the copies, the pool untouched, two changes in a row, there
  and back, mode off, the gesture); `test_perform.py --dry`, ALL OK (the writes alone, with RESAMPLE and with the
  eight offered packages + CPU + RESAMPLE + Transpose: no shared byte, the payload before the part's code
  unchanged); `claims.py --check --self-test`, `gen_parts.py --check`.
- **Not proven:** `tools/emu/test_perform.py` sections 2 to 5 (Unicorn, the maintainer's terminal): the four writes
  as single instructions against the stock ones, `0x4000f36a` with its calls stubbed, the gesture at the PATTERN
  case, the accessor. Written without a run; a failure there may be the test's.
- **Not in P1:** the hook at the serializer (P3: until then Save Pattern, Save Project and power off write the
  tweaked kit for the active pattern), the temp slot's handling, Reload Pattern's `orig`, project load / paste /
  clear, the display.

### 7.1 The Unicorn runs (the maintainer, 2026-11-14)

- Run 1 stopped in section 2: the test wrote a7 before SR, and Unicorn swaps the stack pointers on a change of mode.
  The test writes SR first now and starts in supervisor mode.
- Run 2: sections 3 and 5 ALL OK. **A fault of the part:** with the mode on the sequencer's entries changed X, which
  the stock `move.l` leaves alone; `entries.S` saves the condition codes around the C call since (SAVE / TELL, 1166
  bytes of code). One line of section 4 was the test's: the handled path sets d3 to 1 whole, as the stock
  `0x40020d5e`. Counted in that run: the write with the mode off 19 instructions, a change 1128, a second change
  before the interface ran 1665.
- Run 3: « all ok ». **P1 is proven in emulation.** Not committed, not on a device, not in digiemu.
  Counted in run 3: the write with the mode off 23 instructions, a change 1132, a second change before the
  interface ran 1669.

## 8. P2 and P3 built (2026-11-14)

The part's 0.2: 2104 bytes of code, a data block of 8508 bytes (two buffers of 696, 12 bytes of temp bits, a kit
of 7096 for the serializer's copy). Fourteen sites (thirteen with RESAMPLE).

| Site | Bytes | What |
|---|---|---|
| `0x4005b2ae`, the kit serializer's start | 8, `jmp pk_ser` and a nop | for `home`'s kit and the kit of the pattern left: a copy with the pattern's own bytes in `0..693`, the pool as it is; so Save Project, the backup at power off, the mirror and a SysEx dump hold the pattern's own kit |
| `0x400100ba`, the kit's save to a slot (`0x4001002c`: d4 the pattern, d2 the slot) | 6, `jsr pk_ksave` | Save Pattern: `orig` ← the tweaked bytes, then saved; a temp save (slot 96): saved tweaked, the pattern noted; then into the serializer past `pk_ser` |
| `0x400107a4`, the kit's load from a slot (`0x400106de`: d2 the pattern, d3 the slot) | 6, `jsr pk_kload` | Reload Pattern from the project: `orig` ← the loaded bytes; a temp reload, a failed load: nothing |
| `0x4000eb12`, called by the three project functions (`0x4000f90e` new, `0x4000fbc8`, `0x40010262`) before their list goes to the sequencer | 6, `jmp pk_drop` | the mode dropped, no kit written |
| `0x40010c7a`, `0x4001190c`, `0x40011a7e`, the functions that paste or clear a pattern with its kit | 8 each, `jmp` and a nop | the mode off first |

- **Mode off** now also saves the kit of every pattern temp-saved inside the mode to the temp slot again
  (`0x4001002c(project, 1, n)`), with its own bytes.
- **Proven here:** the host test, ALL OK, 441 checks; `test_perform.py --dry`, ALL OK for the three builds (no
  shared byte with the offered cards); `claims.py --check`; `gen_parts.py --check`.
- **Not proven:** `test_perform.py` sections 6 to 9 (written without a run), and sections 2 to 5 again on the
  larger part.
- **Read by its bytes only, `[HYP]`:** that `0x4001190c` and `0x40011a7e` are clear / cut (they copy pattern and kit
  into a 37 812-byte record first; their callers are `0x4001b14c`, `0x4001b214`, `0x400da984..`); that the three
  callers of `0x4000eb12` are every way a project is replaced; that a temp save from the key handler's context at
  mode off is safe on the device.
- **Known gap:** the interface writes a knob's value into the kit's mirror directly as well (the second half of
  `0x40009a1e`); who reads the mirror was not found. If something saves from the mirror without the serializer, it
  holds the tweaked values of the knobs turned in that pattern.
- **Still missing:** the display (the mode cannot be seen), composer.js and the card (P5), digiemu, the device.

### 8.1 The Unicorn run (the maintainer, 2026-11-14)

`test_perform.py`, sections 1 to 9: **ALL OK**, alone and with RESAMPLE, at the first run of sections 6 to 9. P1 to
P3 are proven in emulation. Counted: the sequencer's write 23 instructions with the mode off, 1132 a change, 1669 a
second change before the interface ran; the serializer's start 30 for a kit passed as it is, **5906 for a copy**
(once per serialization of the active pattern's kit: also at every change notice of that kit, in the interface's
task, not in the audio interrupt). Not committed, not in digiemu, not on a device.

## 9. Committed, and the popup (2026-11-14)

- **Committed** on `perform` (the maintainer: « dann kannst du meinetwegen commiten »): `fcee830`, the part 0.2 with
  P1 to P3, the composer's option, the proof. Not pushed. main untouched.
- **The popup, part 0.3** (2343 bytes of code), not committed: the switch shows the OS's popup, « Perform Kit ON » or
  « Perform Kit OFF », with RESAMPLE's proven routine (`0x400747c0` on `0x9c` bytes, the holder `0x400fbf40`,
  presented on the views' target); paste and clear, which switch the mode off, show it too; another project does
  not. Nothing shows the mode once the popup is gone: the lasting mark (a letter by the pattern's name, the name
  inverted) needs the main view's drawing read first.
- **Proven here:** the host test, ALL OK, 446 checks; `test_perform.py --dry`, ALL OK. **Not run:** section 10 (the
  popup's calls in Unicorn).
- **Unicorn with the popup (the maintainer, 2026-11-14): ALL OK, sections 1 to 10.**
- **On the Model:Cycles (the maintainer, 2026-11-14, by mistake instead of digiemu), the build with Perform Kit alone (MAIN OS `9dadefbd…`): « startet normal. modus funktioniert in einem
  simplen testaufbau ».** Which of the test sheet's tests that covers was
  not said.
- **On the Model:Cycles, every test of the sheet (the maintainer, 2026-11-14, the build with Perform Kit alone):**
  tests 1 to 5 (the start, the switch without the settings menu or the pattern selection, the sounds kept over a
  change, mode off « spielt wieder die alten sounds », sound locks) and S1 to S12 (temp save and reload, Save
  Pattern, Reload Pattern, Save Project and a restart, power off inside the mode, paste, clear ALL DATA, another
  project loaded): « alles wie erwartet », « passt ». One difference: at paste and at clear the « Perform Kit OFF »
  popup is never seen, the OS shows its own message right after; the mode is off as designed.
- **Not tested:** a build with the other cards, a chain, the page.
- **Committed** (the maintainer: « Ja, committen »): `2b66fa0` on `perform`, the popup and the device result. The
  branch is `fcee830` + `2b66fa0`, not pushed, the working tree clean.

## 10. The mark on the main screen (2026-11-14), a first version that was not kept

- **Read:** MainScreenView's draw `0x4001b22a(view, bitmap)`: the left half a lit panel (`0x40070dea(bitmap, 0, 0, 63,
  63, 1)`, its corners rounded by `0x40070f6e`), in it three lines centred at x 32: the pattern's number (« %c%02d »,
  y 34, a larger font), two « %s » lines (y 21, y 8); the right half dark with « TR%d » (x 96, y 34), pan and level.
  With a value window open the draw branches to its epilogue at once. The fill `0x40070dea(bitmap, x0, y0, x1, y1,
  colour)` inverts with a negative colour (`eor.l`), sets with bit 0, clears otherwise.
- **Built:** `pk_mark`, a `jmp` in place of the epilogue's `movem.l -64(a6),d2-d7/a2-a5` (`0x4001b84e`, 6 bytes),
  which every path of the draw reaches and every machine's own main draw passes (they call `0x4001b22a`):
  `pk_mark_c(view, bitmap)` keeps the view and, with the mode on and no value window, inverts x 2..61, rows 31..61,
  the field of the pattern's number (the corners left out). A switch, paste, clear and another project ask the kept
  view for a redraw (`0x40076082`). Paste and clear no longer call the popup.
- **The rows are a guess:** the number's font and its height were not measured, and no picture of the main screen
  was at hand. The maintainer looks at it on the device; the field's rows are four numbers in `pk_mark_c`.
- **Proven here:** the host test, ALL OK, 454 checks; `test_perform.py --dry`, ALL OK, fifteen writes, none shared
  with the offered cards. **Not run:** section 11.

### 10.1 The mark rebuilt (2026-11-14): a checkerboard stripe after any main draw

- **§10's hook was wrong for SAMPLE** (the maintainer: « SAMPLE überschreibt doch mit einer custom view »): on a
  SAMPLE track without a value window `smp_main_draw` (One-Shot's view.c) draws its own view and never calls the
  stock draw, so a hook at the stock epilogue never runs there. Only REF2 calls the stock draw first.
- **Decided by the maintainer on two mockups** (a frame: « sieht nicht so geil aus »): a checkerboard stripe on the
  left, **2 pixels wide, squares of 1 pixel**, painted, not inverted, on every main view.
- **Built:** MainScreenView's draw slot (vtable entry `0x400ffe30`, stock `0x4001b22a`) goes to `pk_main(view,
  bitmap)`: the draw behind it, the view kept, then the stripe while the mode is on and no value window is open.
  The stripe is written straight into the bitmap as the fill `0x40070dea` reads it (`+4` width, `+8` height, `+12`
  the words a column, `+16` the data; column 0 `0xaaaaaaaa`, column 1 `0x55555555`). The hook at `0x4001b84e` and
  the inverted field are gone.
- **The composer** gives `pk_main` the draw behind it in the data block's `next`: the dispatcher's when two packages
  share the slot (its write there left out), the one package's that takes it (left out through the sites taken),
  else the stock draw. Proven in `--dry` for the three cases (alone, SAMPLE, SAMPLE + REF2) and the offered build:
  the address is what the build without Perform Kit has in the slot.
- **Proven here:** the host test, ALL OK, 456 checks; `test_perform.py --dry`, ALL OK, five builds. **Not run:**
  section 11 (rewritten). Builds: alone, MAIN OS `65a6f2a9…`; the offered cards and the three tweaks, MAIN OS `a5b6b6e1…`.
- **Unicorn (the maintainer, 2026-11-14): « all ok », sections 1 to 11.** The stripe is not committed and was not
  seen on a device yet.
- **On the Model:Cycles (the maintainer, 2026-11-14, the build with the offered cards, MAIN OS `a5b6b6e1…`):** the
  stripe on the left on a stock track (« passt, streifen ist links ») and on a SAMPLE track (« auch bei sample
  links »), gone while a value window is open and after the mode is switched off. The saving steps S1 to S12 were
  not repeated with this build.
- **Committed** (the maintainer: « Ja, committen »): `a25fc07` on `perform`. The branch is `fcee830`, `2b66fa0`,
  `a25fc07`, not pushed, the working tree clean. Left: composer.js and the card, the guide, the note, a release.
- **The complete build on the Model:Cycles (the maintainer, 2026-11-14):** SAMPLE, SOLID, CHORD Tables, Digital
  Delay, POTS, the LP/HP filter, Crush, Ring, Reso, EQ, the CPU page, RESAMPLE, Transpose, Perform Kit and the
  three tweaks (MAIN OS `d91ef5bf…`, from `a25fc07`): « passt,
  läuft auf dem gerät ». What was tried with it was not said.
- **Decided (the maintainer, 2026-11-14):** the choice of the delay / reverb effect and CHORD Tables' table stay with
  the pattern. The card gets a hint: which send effect a pattern uses and its wavetable are set for each pattern;
  the mode keeps the effects' values, not their type.

## 11. The card (2026-11-14)

- **The decision on the effects** (the maintainer, after the complete build): the choice of the delay and reverb
  effect and CHORD Tables' table stay with the pattern (§2, 9 and 10); the card says so (« das man sendFX und
  wavetable für jedes pattern festlegen muss »).
- **The generator** `tools/gen_perform.py` composes the part alone into `tweaks/model-cycles_OS1.13/82-perform.json`
  (18 writes, 11 104 bytes added to the image).
- **The page:** `composer.js`'s `performLayer`, the twin of `compose.perform_layer` (the three draws behind the
  mark, RESAMPLE's SETTINGS byte); `tools/webcompose_check.sh` composes Perform Kit alone, with RESAMPLE, with
  SAMPLE, with SAMPLE and REF2 and with every offered card, identical to `compose.py` (writes, conflicts, MAIN OS).
  The card in `FEATURES` (`live`, experimental), its texts in `FEAT`, the guide's section 19, release 0.63.
- **The texts** were written once, to docs/AGENTS.md's *Writing for users*, and accepted as they were (« Ja,
  einsetzen »): the short, nine blocks, a note on what switching the mode off discards.
- **Status:** experimental until flashed from the page. Left for later: a pattern chain and FUNC + PLAY inside the
  mode were not tried; the effect choice and the wavetable could stay with the mode by the same mechanism on the
  pattern's header (§5).
