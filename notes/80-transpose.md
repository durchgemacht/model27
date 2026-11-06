# 80 — Transpose: the TRIG keyboard's octave and pitch jumps on MACHINES

The maintainer's ideas (2026-11-05): a held key + TRIG 15 / 16 moves the trig keyboard an octave down / up, the LEDs
brighter the more often they are pressed; a held key + TRIG 8, 9, 11, 12 makes the track's pitch jump. Checked the
same day (« zwei Mod-Ideen prüfen, noch nichts am Code ändern »), decided through seven questions, then « Ja, Plan
schreiben ».

A builder's part `transpose` (`tools/machines/transpose/`, `compose.py --transpose`, also without packages), always
with the shortcut layer (its 0.6), its tweak alone `81-transpose.json` (`tools/gen_transpose.py`), its probe
`tools/emu/probe_transpose.py` and its proof `tools/emu/test_transpose.py`; the flasher's card Transpose (experimental).
Addresses: VAs of the Model:Cycles OS 1.13 MAIN OS (base `0x40000400`); `[FAIT]` read in the code or proven in
emulation, `[HYP]` to read or prove. The steps P0 to P3 are done (§5.1 to §5.4), and the part's 0.3 clears the jumps
when the pattern is reloaded (§5.5); P4, the device test, is under way (§6, §6.1).

## 1. What the player gets

- **Where:** in keyboard mode only (GRID RECORDING off, no pattern selection armed), on the active track. In GRID
  RECORDING, MACHINES + TRIG sets trigs as on the stock OS.
- **MACHINES held:** TRIG 8, 9, 11, 12, 15 and 16 light up; the other trig keys stay as the stock OS leaves them.
- **Octave, TRIG 15 / 16:** each press moves the keyboard one octave down / up, at most two either way, on top of KBT
  (FUNC + TRACK, TRACK SETUP), which the mod never writes. LEDs 15 / 16: both dim at 0; the side the keyboard moved to
  at mid brightness for one octave, full for two.
- **Pitch, TRIG 8 / 9 / 11 / 12:** −7, −5, +5, +7 semitones from the set PITCH (fixed targets, not summed). The sound
  jumps within one audio block (0.67 ms), the running pattern too, p-locked steps too. The active key full, the other
  three dim; pressing the active key again goes back to 0. PITCH + jump is clamped to ±24. A jump is not recorded and
  sends no MIDI.
- **Kept:** per track, in RAM only; selecting another track keeps the first one's values; a pattern change clears all
  of them; reloading the pattern (FUNC + PATTERN tapped, from the temp area, or held and YES, from the saved project)
  clears every jump and keeps the octaves (0.3); power-on starts at 0.
- **MACHINES on every track** is a held key: the list opens on the release unless something acted (the layer's 0.4
  behaviour, so far only on the tracks of machines with a shortcut); with the list open, a press closes it at once.
- Brightness steps are relative to SETTINGS › Device › LED (LOW / MID / MAX), which sets one current for all LEDs.

## 2. Decisions

Taken by the maintainer (2026-11-05):

| # | Question | Answer |
|---|---|---|
| 1 | What do TRIG 8–12 act on | the sound (PITCH), not the keyboard |
| 2 | Fixed or summed jumps | fixed to the set value, active key full, again = 0 |
| 3 | Intervals | −7 / −5 / +5 / +7 |
| 4 | Octave: write KBT or add to it | add, RAM only |
| 5 | Held key | MACHINES for both |
| 6 | Other track selected | each track keeps its values |
| 7 | Beyond ±24 | clamp at the output |
| – | Grid mode | MACHINES + TRIG sets trigs (stock) |
| – | Octave range | ±2 |
| – | Storage | RAM, cleared on a pattern change |
| – | Pattern reloaded (FUNC + PATTERN tapped or held) | the jumps back to 0, the octaves stay (2026-11-06, after the device test: « dass die Sprünge auch entfernt werden, wenn man den pattern neu lädt », « 15 und 16 sind von dieser änderung nicht betroffen ») |
| – | MACHINES | a held key on every track (« selbes Konzept überall ») |

Still open, small (recommendation first):

- **D1, the other trig keys with MACHINES held** (1–7, 10, 13, 14): play as without MACHINES (stock fall-through),
  or take them silently. Recommended: stock; nothing of ours acted, so the list opens on the release as it would have
  on the press.
- **D2, the dim steps:** 1/4 and 1/2 at 250 Hz, or 1/3 and 2/3 at 333 Hz (the rate notes/45 tested). Decided on the
  device with both builds (P4).
- **D3, the card's name**: « Transpose », as proposed (P3).

## 3. The stock OS `[FAIT]`

**KBT.** The byte +721 of a pattern's track (722 bytes, notes/32 §4), saved with the pattern. Getter `0x40016da6`
(`mvsb 721(a0)` through the track holder's vt+40), setter `0x40016dd6` (clamps −60..+60). Its only readers:
`0x4001a164` (the keyboard) and `0x4003e3c6` / `0x4003e42c` (TRACK SETUP's text and change). The sequencer never
reads it; external MIDI notes do not go through it. The keyboard's note is key index + 52 + KBT
(`pea 52(a2,fp.l)` at `0x4001a236`, displacement 0x34: TRIG 9 at KBT 0 is note 60; read as 34 on 2026-11-05, corrected
2026-11-06); `0x40019f44` drops a note above 127 unsigned, so a negative note is silent (KBT −60 already silences the
eight low keys on the stock OS `[HYP]`, device).

**The keyboard.** `KeyboardView` (vtable `0x400ff9c4`, consumeKeyEvent slot `0x400ff9cc` = `0x4001a0d2`): codes 16–31,
returns "not taken" in grid mode (`0x4006b978`: UIStates +357 and +358) and with the pattern selection armed
(`0x4006bb18`: +389); asks `isKeyHeld(4)` (RETRIG) at `0x4001a188`. Its LED producer is empty (`0x400d7648` = `rts`).
The release path `0x40019d00` works on the held-note records (20 bytes) and does not read KBT, so changing the octave
while a note is held should not leave it hanging `[HYP]`.

**MACHINES.** MainScreenView `0x4001c252`; the toggle on a fresh press at `0x4001ca1e`. The MACHINES list's keys
(`0x400a292c`) take codes 12 and 32 only, every TRIG falls through. The layer 0.4: `sc_mach` at `0x4001ca1e`, `sc_level`
(1 only on the tracks of machines with a switch or a knob shortcut), `sc_data` +0x12 pending, +0x13 used. The layer
0.5 (switch locks, on main since 2026-11-06, release 0.50, `31e5219`): `sc_mtrig` at `0x4001c274` (a held trig +
MACHINES), `sc_steplock` at `0x40022eac` and `sc_gridleds` at `0x40022112` (grid mode, a step held); `sc_mach` and
`sc_level` unchanged (re-read 2026-11-06).

**PITCH.** Descriptor 42: k 10, 8.8 words `0x2800`..`0x5800`, default `0x4000`, so `0x100` per semitone. The audio
block `0x4005979e`: `0x400597a8` `jsr 0x40058474`, the smoother (one pole, its state at `0x800011e8`, its output
rewritten every block into `0x8000100c`, returned in d0); then `0x40056e24` and the LFO `0x40091ab2` change the output;
the voice loop at `0x4005981e` (fxslot's `early` hook). Track t's words at `0x8000100c + 14 + 66 t`, PITCH at +20.
A word changed in the output after the call is not fed back. SAMPLE reads +0x14 every block (`sampler.c`, « as on
every machine »).

**LEDs.** SETTINGS › LED: `0x40008a42` → `0x400537b6` writes DAC1 (`0xFC09C002`): LOW `0xa0`, MID `0x480`, MAX the pin
as GPIO high: one current for every LED. An LED itself is on or off (74HC373 latches, notes/21 §7.2). The LED frame
`0x40006a4a` (30 Hz): reset `0x4000602a`, the views `jsr 0x40076ca2` at `0x40006a76`, the end `0x40006044`.
`0x40005f86`: the first state wins; a state ≠ 1 sets the base bit; the blink `0x40005efc` handles only 3 and 4.
The panel interrupt reloads one latch row per 1 ms cycle (LED step 0 at `0x40059dea`), each row every 7 ms
(notes/45 §3). Rows: TRIG 8 / 9 row 3 (bits 28, 29), TRIG 11 / 12 row 4 (37, 38), TRIG 15 / 16 row 5 (47, 40).
The running light inverts a key through the LED timers, on top of the states.

**Patterns.** The playing one: `*0x40a7887c`, its number at +30706, read byte by byte (fxslot.c). The shown one:
`0x4000f208(*0x40fe4228)`.

**The reload** (read 2026-11-06). `0x400107d8(project, temp, pattern, ptn, seq)` reloads the pattern: `temp` 1 from
the temp area (FUNC + SETTINGS' temporary save), 0 from the saved project (`0x4000f00e`; « N/A: Unsaved Proj » when
there is none, « Prj must be re-saved! » for an old one, « Reload Error »); `ptn` and `seq` the pattern's and the
sequence's parts (both 1 at every call). It shows « Ptn reloaded from » « Temp Area » / « Proj » and returns d0 = 1, or
d0's byte 0 on an error. The pattern's number does not change, so `tr_pitch`'s check does not see it. Its only three
calls (no pointer to it in the image):
- `0x4001c19c`, MainScreenView's PATTERN case (`0x4001c154`): FUNC (event flag bit 1) and the short press (bit 4):
  `(project, 1, the current pattern 0x4006a96c, 1, 1)`. FUNC with the long press (bit 5) goes to `0x4001c618`, the
  prompt « Reload Pattern from\nsaved Project? » (Yes / No).
- `0x4001b884`, that prompt's answer `0x4001b858(ctx, answer)`: 0 (Yes) → `(project, 0, pattern, 1, 1)`, then
  `jmp 0x4002c680`; No returns.
- `0x4002cad0`, the same prompt and answer (`0x4002caa4`) opened by `0x4002cae4`, an item of the list `0x4002c274`
  builds (called from `0x4001ba66` and `0x4003c228`; which menu it is on the device `[HYP]`).
None of the callers reads d0 after the call.

**Free sites.** No offered tweak and no part writes `0x400ff9cc`, `0x4001a164`, `0x400597a8`, `0x40006a76` or
`0x40059dea` (checked against OFFERED and every part.json, 2026-11-05, again after release 0.50 on 2026-11-06). The Modded-Cycles trigless-dim (47, not offered)
also hooks `0x40059dea`: if it ever comes back, the two exclude each other.

## 4. The design

A new builder part `transpose` (MIT, own code; the dimming is written fresh, the idea credited to djd_oz and notes/45),
and one flag in the shortcut layer.

| Site | Stock | The part |
|---|---|---|
| `0x400ff9cc` (vtable, 4 B) | `0x4001a0d2` | `tr_keys`: MACHINES held, FUNC and TRACK not, keyboard mode, a code of TRIG 8, 9, 11, 12, 15, 16 → act on the press, take the press and its release, set the layer's +0x13 (used); else `jmp 0x4001a0d2` |
| `0x4001a164` (6 B) | `jsr 0x40016da6` | `jsr tr_kbt`: KBT + 12 × the track's octave, clamped −60..+60 |
| `0x400597a8` (6 B) | `jsr 0x40058474` | `jsr tr_pitch`: the smoother, then for each track with a jump: the word at +20 += `0x100` × n, clamped `0x2800`..`0x5800`; d0 the buffer |
| `0x40006a76` (6 B) | `jsr 0x40076ca2` | `jsr tr_frame`: with MACHINES held in keyboard mode, the six LEDs' states before every view (so ours win), and the dim masks for the interrupt; else masks 0; then the views |
| `0x40059dea` (10 B) | LED step 0 | `jmp tr_led`: the rows of the dim masks switched off for part of each period (notes/45 §6's principle); the fast path when the masks are 0 |
| `0x4001c19c`, `0x4001b884`, `0x4002cad0` (6 B each, 0.3) | `jsr 0x400107d8` | `jsr tr_reload`: the reload with the same five arguments; when it reloaded (d0's byte 1) every track's jump 0, the octaves kept; d0 as it returned |
| the layer, `sc_level` | — | a byte in `sc_data` (« held key on every track »), written by both composers when `transpose` is in the build |

- **State:** per track an octave (−2..+2) and a jump (0 or ±5 / ±7), each with the pattern number it was set in.
  `tr_pitch` compares the playing pattern's number every block, `tr_kbt` the shown one at each key press, `tr_frame`
  both: a change clears that track's values, so the old jump never sounds into the new pattern.
- **The layer:** `transpose` needs the shortcut layer; the composer adds it. Built on the layer 0.5 (on main since
  2026-11-06) as the layer 0.6, on a branch from main.
- **Claims:** MACHINES + TRIG 8 / 9 / 11 / 12 / 15 / 16, situation keyboard, replaces « plays the note »; the layer's
  claim on MACHINES widens to every track in a build with `transpose`. The keymap concept's MACHINES row gets the
  trig keys (keymap-concept.md §3, the note's map).
- **Cost:** a few hundred bytes of code. The audio block: 6 compares when no jump is set. The panel interrupt: the fast
  path about 20 instructions per ms; with MACHINES held, rows 3–5 reloaded at phase changes, by notes/45 §7's
  figures at most about 20 µs per ms (2 %), only while MACHINES is held. Measured in P2.

## 5. Steps

| Step | What | Proof |
|---|---|---|
| P0 | Probe on the stock OS, nothing patched (`tools/emu/probe_transpose.py`): the keyboard's notes for KBT 0 / ±12 / ±60; a release after KBT changed (no hanging note); whether a keyboard press marks the held-trig mask (UIStates +348 / +352; else MACHINES + TRIG 11 + PUNCH on a SAMPLE track could lock a step with the switch locks); the smoother's output word +0x500 reaching the voice loop and SAMPLE's / a stock machine's pitch, the state unchanged; the playing and shown pattern numbers across a change, stopped and playing; which views set trig LEDs 1–16 in keyboard mode | the maintainer's Unicorn run |
| P1 | The part without dimming (states on / off): `tr_keys`, `tr_kbt`, `tr_pitch`, `tr_frame`; the layer's flag; part.json, claims, compose.py and composer.js in the same commit | `test_transpose.py`: every key × mode (keyboard, grid, selection armed) × held keys (MACHINES, + FUNC, + TRACK) → taken or stock; notes with octaves and KBT at the edges; the PITCH words, the clamp; a pattern change clears; the layer's used flag keeps the list closed; test_shortcuts still ALL OK |
| P2 | The dimming: `tr_frame`'s masks, `tr_led` | like `test_trigless_dim.py`: port writes identical to stock with no mask; with masks the duty per level, waits bounded, the 50 other LED bits identical, registers and stack kept; the cost |
| P3 | Integration: the card, REGISTRY, tweaks.js, REF_MAINOS / REF_MODS, smoke expectations, BUILD.md hashes; every check | the checks here, Unicorn + smoke by the maintainer |
| P4 | Device files: D2's two variants, each with SAMPLE and the switch locks | the Model:Cycles (§6) |
| P5 | The note, the guide, the card text, release, README, keymap concept; commits only on the maintainer's word | |

## 5.1 P0 done (2026-11-06): the maintainer's Unicorn run, ALL OK

`tools/emu/probe_transpose.py` on the branch `transpose` (worktree `model27-transpose`, from main `31e5219`):
- The sites hold the expected bytes; KBT is named only by the keyboard and TRACK SETUP; the release path names
  neither the getter nor the setter; PITCH 0x100 a semitone; the LED rows as in §3.
- The keyboard: note = key index + 52 + KBT (TRIG 1 / 9 / 16 at KBT 0: 52 / 60 / 67; at −60: −8 / 0 / 7, the low keys
  silent on the stock OS; at +60 TRIG 16 = 127); d3 at `0x4001a164` is the note's track; grid mode and an armed
  selection leave the key below; a release carries the key index only; MACHINES held plays as without it; the
  handler writes nothing into the UI state (so it never marks a held trig for the switch locks).
- The LEDs: the first state wins (0x102 stays over a later 1, base bit on); the blink times only 3 and 4; at
  `0x40006a76` every state is 0 and a state written there survives the views and the frame's end.
- Pitch: for KICK, SNARE, METAL, PERC, TONE and CHORD, PITCH 0x4500 and 0x4000 + 0x500 after the smoother play the
  same, sample for sample (−7 too); the smoother's state untouched; a jump from block 12 equals PITCH set without a
  glide there and nothing before (KICK, TONE).

## 5.2 P1 (2026-11-06), committed `686265a` on the branch `transpose`

- **The part** `tools/machines/transpose/` (transpose.c, entries.S, part.json, LICENSE; 0.1, order 81, 1310 bytes of
  code, a 24-byte data block): `tr_keys` on KeyboardView's key slot, `tr_kbt` at `0x4001a164`, `tr_pitch` at
  `0x400597a8`, `tr_frame` at `0x40006a76` (states 0x102 / 0x202 / 2, all lit until P2). The playing pattern's number
  is read byte by byte (GCC had merged the four reads into one long; `volatile` keeps them apart, as fxslot reads it).
  Claims: MACHINES + TRIG 8/9/11/12 and + TRIG 15/16, situation keys, replaces the keyboard's note.
- **The layer 0.6**: `sc_data` +0x1c `every` (bit 0), the shortcuts per machine at +0x20 (were +0x1c); `sc_level`
  answers 1 when it is set; part.json data `every` 28, `entries` 32; the MACHINES claim's text.
- **The composers**: `compose.shortcut_layer(every=)`, `compose.transpose_layer`, `compose(transpose=)`, `--transpose`;
  `composer.js` the same (`shortcutLayer(..., every)`, `transposeLayer`, `opts.transpose`); `webcompose_synth.py` and
  `webcompose_check.js` with four selections more. `gen_parts.py` builds the part.
- **Regenerated by the layer's 0.6** (each +20 bytes of payload, the same conflicts and writes): 27-sampler,
  29-refmachine2, 34-refchord, 36-chordtables, 72-smpfilter, 73-crush, 74-ring, 75-reso, 76-eq; REGISTRY.md (the
  MACHINES claim's text), tweaks.js (the layer's part), REF_MAINOS / REF_MODS (64 of 92 combinations); the smoke
  test's SAMPLE line (46 312 bytes) and the two Model:Samples hashes (`88e7ca9f…`, `c24f8a6a…`; the recipe gives the
  old ones on main). **BUILD.md left for P3**: its hashes carry their history ("la couche 0.5 : …"), rewritten with
  the Transpose section.
- **Checks here, all OK**: gen_parts --check, every composing generator --check, gen_flasher_tweaks --check,
  registry --check, check_overlaps, claims --check --self-test, ref_mainos --check, webcompose (Python = JS, byte for
  byte, the four new selections too), webbuild, webflash, py_compile; --dry of test_transpose (section 1, four
  builds), test_compose, test_cpu, test_fltslot, test_fxslot, test_resample. **New conflicts** of a build with
  Transpose: chord-keys (KeyboardView's slot), model-tg, model-tg-st (3 bytes in it), all command line only.
- **Proof** `tools/emu/test_transpose.py`: sections 2–7 need Unicorn (the maintainer), with test_shortcuts,
  test_refchord, test_chordtables, test_fltslot, test_compose and the smoke test for the layer's 0.6.
- **The maintainer's Unicorn run (2026-11-06): ALL OK, all six**: test_transpose (864 key events
  as the stock OS but the 6 taken; the values; 105 keyboard notes; tr_pitch's words, clamp and pattern change; every
  stock machine a jump of -7 / +7 = PITCH set so, sample for sample; 25 LED states; MACHINES on machines 0..5 and
  SAMPLE's), test_shortcuts 180, test_refchord 86, test_chordtables 165, test_fltslot 638, test_compose 183 checks.
  The smoke test (2026-11-06): ALL OK, 244 checks (SAMPLE 46 312 bytes, the two Model:Samples
  hashes). Committed `686265a` (the maintainer's « Ja, committen »).

## 5.3 P2 (2026-11-06), committed `bcf2627` on `transpose` (after `686265a`), not pushed

- **The dimming, written anew** (the part's 0.2, 2262 bytes of code, a 60-byte data block): `tr_led` (entries.S)
  from the panel interrupt's LED step 0 (`0x40059dea`, 10 bytes: `jmp tr_led ; nop ; nop`) -> `tr_led_c`: DIR first;
  without a mask and with every row back to its stock byte, the stock path; else the phase steps on (0..n-1) and every
  known row whose byte must change is loaded at once (DATA, SET 8, CLR 0xfff7, each followed by a wait of 272 counts
  of PIT3, 64 reads at most), from the byte the stock turn latched last with the masks' LEDs off (dim from the 2nd
  cycle, mid from the 3rd, the rows' phases staggered by their number); the turn row too, from its last byte, so that
  its masked LEDs change now and its other LEDs at the stock instant (the byte returned: the new one with the masks'
  LEDs off, latched by the stock steps 1 and 2). `tr_leds` puts the dim and mid LEDs' bits in two masks per latch row
  (by the LED table `0x4010abf8`) every frame, and clears them when not active.
- **The period** n in the data block (+58), the composer writes part.json's `n_value` (4: 1/4 and 1/2 at 250 Hz);
  `compose.py --transpose-n 3` makes the 333 Hz test build (1/3 and 2/3), never offered, Python only. Both composers
  write the 10-byte site (a jmp padded with nops).
- **New computed conflict**: trigless-dim (47, command line only, the same LED step).
- **Proof** `test_transpose.py` grows: section 1 the fifth site and the period; section 6 the masks; section 8 the real
  panel interrupt on test_trigless_dim.py's rig (port, PIT3, latches; the OS's own start-up copying the payload): no
  mask = the stock writes and latches; masks at 4 and 3 ms: no hazard, registers back, other writes and LEDs the
  stock ones, step 0 [DIR, (DATA, SET, CLR) x k, DATA] with k <= 3 on rows 3..5, gaps >= 272, dim 1 of n and mid 2 of
  n in steady state, never lit when the stock OS has it dark, the running light and a blink dark at least as long;
  20 us latency within 1.5 %; step 0 late; PIT3 standing still; the masks cleared: back within 2 cycles.
- **Checks here**: gen_parts, gen_flasher_tweaks, claims, registry, check_overlaps, py_compile, webcompose (Python =
  JS, 16 writes alone), test_transpose --dry. Unicorn: the maintainer.
- **The maintainer's Unicorn run (2026-11-06): ALL OK, 73 checks** (the first run stopped in
  section 8 on a fault of the test: the rig's start-up 0x4000045c ends before the payload's boot hook 0x400004b2, a
  routine of its own, so the test now writes the payload itself, as mcengine does). Section 8: no mask = the stock
  port writes and latches (11 899 writes); 4 ms: dim 1 on / 3 dark, mid 2 / 2; 3 ms: dim 1 / 2, mid 2 / 1; the 51
  other LED bits at the stock instants; k <= 3 rows a step, gaps >= 299 counts; 20 us latency: dim 0.249..0.253,
  mid 0.499..0.502; PIT3 late or standing still handled; back to stock within 2 cycles. **Cost while MACHINES is
  held: at most 23 us a step, 15.8 us a ms on average at 4 ms (1.6 %), 20.1 us at 3 ms (2.0 %).**

## 5.4 P3, the card (2026-11-06)

- `tools/gen_transpose.py` composes the part alone into `81-transpose.json` (16 writes, 4 444 bytes added to the
  image); the other composed tweaks name `transpose` among their conflicts, as they name `resample`.
- The card Transpose (experimental, cat `live`, model27's own: the card links the project) in `FEATURES` and `OFFERED`;
  in `app.js` its texts, its guide anchor and the composition (`chosenTweaks`, `composeMachines`: `opts.transpose`,
  its id last after `cpu` and `resample`); `tweaks.js` with the part embedded; `ref_mainos.py` composes every set of
  machine cards with and without the CPU page, RESAMPLE and Transpose: REF_MAINOS 106 combinations, REF_MODS 2 050
  entries (1 026 before), `app.js` 547 KB (344 KB before); the smoke test knows the fourteenth card.
- Guide section 16, release 0.51, stamp `2026-11-06-02`, README, PROVENANCE, BUILD.md (the Transpose section, and the
  hashes the layer's 0.6 changed, each with its layer-0.5 value kept).

## 5.5 0.3: a reload clears the jumps (2026-11-06)

The maintainer after step 6 of the device test (« ja, nach spurwechsel noch da »): the jumps should also go when the
pattern is reloaded, FUNC + PATTERN held (from the project) or tapped (from the temp area), the octaves not.
- **The part's 0.3** (2322 bytes of code, the data block unchanged): `tr_reload` (transpose.c) at the reload's three
  calls (§3, *The reload*): `RELOAD(project, temp, pattern, ptn, seq)`, then, when d0's byte is not 0, `jump[0..5]`
  0; `oct[]` and everything else untouched; d0 returned whole. A reload that fails (an unsaved project, an old one)
  keeps the jumps, as it keeps the pattern. The UI task writes the bytes, `tr_pitch` reads them in the audio
  interrupt: single bytes, as `tr_keys` already writes them.
- **Both composers** write the three sites (`reload_tap`, `reload_yes`, `reload_menu` in part.json's `sites`); 19
  writes alone (16 before), 4 504 bytes added to the image. No tweak writes those bytes: no new conflict (281 computed,
  as before).
- **Proof** `test_transpose.py` section 1 the three sites, section 9 (Unicorn, the maintainer): MainScreenView's
  PATTERN case from `0x4001c154` with FUNC + a tap (from the temp area), FUNC + a long press (the prompt), PATTERN
  alone; the prompt's answers at `0x4001b858` and `0x4002caa4`, Yes and No; the reload stubbed answering 1 or an
  error, the stock OS and the build side by side: the same calls and arguments, the jumps 0 only after a reload that
  answered 1, the octaves and the rest of the data block kept; `tr_reload` alone: one call with its five arguments,
  d0 whole, d2-d7/a2-a6 and the stack kept. Alone and with SAMPLE.
- **The maintainer's Unicorn run (2026-11-06): ALL OK, 91 checks** (sections 1 to 9). The first run's four failures
  were the test's own: without a call of the reload (the prompt, PATTERN alone, No) it expected the jumps cleared when
  the stub would have answered 1; the build kept them, as it should. The test now expects the clearing only after a
  call of the reload. The smoke test (the maintainer, 2026-11-06): ALL OK, 259 checks.

## 6. The device test (P4), one at a time

1. Keyboard mode, hold MACHINES: TRIG 8, 9, 11, 12, 15, 16 lit, 15 / 16 and 8–12 dim.
2. MACHINES + TRIG 16 twice: LED 16 mid, then full; the keys play two octaves higher; TRIG 15 twice back.
3. Pattern running, MACHINES + TRIG 12: the track jumps up a fifth at once, LED 12 full; TRIG 12 again: back.
4. MACHINES alone, released: the list opens; MACHINES + a trig key used: the list stays closed.
5. GRID RECORDING on, MACHINES + TRIG 11: a trig on step 11, nothing transposed.
6. Another track, then back: the first track kept its jump; change the pattern: everything back to 0.
7. SETTINGS › LED LOW, MID, MAX: the dim steps still visible and steady? Which of D2's two builds looks better?
8. File C (all fourteen cards): steps 1 to 6 again, next to the other cards.
9. (0.3) A jump and an octave set, FUNC + PATTERN tapped: the jump back to 0, the octave kept; again with FUNC +
   PATTERN held, YES.

## 6.1 The maintainer's device test (2026-11-06)

File A (SAMPLE + Transpose, 4 ms, the part's 0.2): steps 1 to 5 « passt alles, nice »; 6: the jump kept on another
track and gone after a pattern change; 7: « a ist perfekt, werde b gar nicht testen » → **D2 decided: a period of
4 ms (1/4 and 1/2 at 250 Hz), the default**; B not tried. Then the reload's clearing asked for (§5.5). Step 8 (file C)
pending.
File D (all fourteen cards, the part's 0.3, MAIN OS `398b05d1…`), step 9: a jump (+7) and an octave (+1) set, FUNC +
PATTERN tapped: « Ja, passt » (the jump gone, the octave kept); then a jump (−5), FUNC + PATTERN held, YES:
« Ja, passt » (the jump gone, the octave kept).

## 7. Risks and limits

- The dim steps may be hard to see at LED LOW (the current is already low); the fallback is the OS's blink states.
- 250 Hz or 333 Hz can leave a dotted trail when the eyes sweep the panel in the dark, and the switched LED current a
  faint whine (notes/45 §11); only while MACHINES is held.
- The switch locks (layer 0.5) act in grid mode with a step held, this part in keyboard mode. They can only meet if a
  keyboard press marks held trigs (P0): then MACHINES + TRIG 11 + PUNCH on a SAMPLE track could lock a step.
- Playing the keyboard with MACHINES held makes the list open on the release only if nothing of ours acted, so a
  player used to MACHINES opening the list at once sees it a moment later on every track.
