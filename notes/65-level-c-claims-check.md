# 65 — Level C: conflicts computed from what mods declare, saved slots and gestures (plan)

**Status: plan, 2026-10-22; the maintainer's decisions the same day: the six recommendations of §9 (§11); step C1
built on 2026-10-23 (§12): the claims as data, checked, nothing computed from them yet.**

The maintainer's request after step B4e (2026-10-22): a "Gesten- und Slot-Prüfung" (a check of gestures and slots),
so that a clash that writes no common byte is computed instead of found by chance. Two such clashes are on record,
both declared by hand:
- lfo-plus with the track filter ([notes/56](56-ajouts-davidcaruso.md) §3.6, found in emulation);
- lfo-plus with the builder's shortcut layer ([notes/63](63-level-b4-shortcuts-dispatchers.md) §14.1, found while
  writing the standard).

This plan covers rules 2 and 3 of the Cycles Mod Standard's computed conflicts (STANDARD.md §4.4) and its migration
steps 3 to 5 (§9). It changes no byte of any firmware: only the tools' `conflicts` lists, `REGISTRY.md` and the build
reports.

Facts marked `[FAIT]` come from the notes cited, the committed manifests and tweaks, and the tools' code
(`tools/compose.py`, `tools/check_overlaps.py`, `tools/registry.py`, `tools/build.py`,
`tools/machines/shortcuts/shortcuts.S`), read on 2026-10-22. No new OS code was read for this plan. Addresses: VA of
OS 1.13.

## 0. In short

- **The gap.** The tools compute three of the standard's seven rules: the same bytes (rule 1), overlapping memory
  (rule 4) and declared conflicts (rule 7). Two mods that keep data in the same saved slot, or answer the same key
  combination, at different bytes, pass every check.
- **What becomes data.** Every mod's claims, in one shape:
  - a package's in its manifest (`claims`, which exists);
  - a part's in its `part.json` (new: the shortcut layer's slots, descriptors and keys);
  - the folder's tweaks in one declared file, `tweaks/model-cycles_OS1.13/claims.json`, each claim with its note.
    `registry.py`'s hand table moves there.
- **What is computed:**
  - rule 2, exclusive points: gestures, descriptors, formatters, p-lock rows;
  - rule 3, numbers: sound slots k, record slots, other saved bytes, MIDI CC and NRPN;
  - each claim with a scope: all tracks and sounds, or those of one machine. Machine ids are no rule since option C
    ([notes/62](62-level-b4-stable-machine-ids.md) §9).
- **Where:**
  - `compose.py` and `composer.js` add the computed ids to a build's `conflicts`, as they do for rules 1 and 4;
  - `check_overlaps.py` refuses two tweaks that can be ticked together and clash in their claims, as it refuses
    shared bytes, until the conflict is declared;
  - `registry.py` writes `REGISTRY.md`'s saved data, gestures and MIDI from the claims.
- **No build changes.** No write and no payload changes: the MAIN OS of every build stays as it is. The shortcut
  part's hand-declared lfo-plus goes, because the slots now compute it.
- **Steps:** C1 the data, C2 the rules in Python, C3 the registry, C4 the page and the standard 0.4 (§8).

## 1. What the tools compute today `[FAIT]`

| Tool | Computes | Does not see |
|---|---|---|
| `check_overlaps.py` ([notes/49](49-verification-mod-par-mod.md)) | two tweaks that can be ticked together never write the same bytes, except the same whole write or one applied on top of the other (`requires`); payloads chain and do not overlap | saved slots, keys, descriptors, MIDI |
| `compose.py`, `computed_conflicts()` | a build's writes against every tweak of the folder: other bytes at the same address (rule 1), a payload in the build's payload or in a claimed RAM range (rule 4); the manifests' `conflicts_declared` and, since B4e, the shortcut part's (rule 7) | the same |
| `composer.js`, `computedConflicts()` | the same in the page, against the offered cards' tweaks | the same |
| `build.py`, `builder.js` | refuse a tweak whose `conflicts` names another tweak of the build, and any `old` byte that is not the official one | — |
| `registry.py` ([notes/52](52-registre-place-libre.md)) | `REGISTRY.md` from the writes: masks, caves, payloads, hooks, pointers; §6, saved data, from a hand table `DECLARED` of two rows (arp, lfo-plus) | everything not in `DECLARED` |
| the flasher | a card's exclusions from the tweaks' `conflicts`; the reason from a hand text per pair (`clash_<id>`, `clashWhy`) | — |

## 2. Three clashes at no shared byte `[FAIT]`

### 2.1 lfo-plus and the track filter (notes/56 §3.6)

- `check_overlaps.py` saw no shared write. The two keep their settings in the same places: k 28–32 against k 28–31,
  record bytes `+88`–`+91` against `+88` and `+90`, and both re-number the p-lock rows of k ≥ 23.
- `test_lfo_plus.py --with macro,track-filter` showed it: 5 checks of the save and the p-locks failed.
- Declared since: `60-lfo-plus.json` lists `track-filter` in `conflicts`.

### 2.2 lfo-plus and the shortcut layer (notes/63 §14.1)

- The layer copies k 28–31 into record slots 28–31 (`+84`–`+91`) after every save, and back after every load, for
  every sound: `sc_post_save` and `sc_post_load` do not look at the machine.
- lfo-plus packs LFO 2 from k 28–32 into `+88`–`+91` from inside the stock save and load. With both, each overwrites
  the other's bytes.
- No write is shared. Declared in B4e: `tools/machines/shortcuts/part.json`, `conflicts_declared`.

### 2.3 A second TRACK + TRIG ([notes/58](58-control-all-config.md) §2)

- `MainScreenView` pushes `TrackSelectionView` (vtable `0x40100ee0`) while TRACK is held. Keys go to the views from
  the end of the list (`0x4007739e`), so that view is served first.
- control-all-config takes TRACK + TRIG 1–6 in its `consumeKeyEvent` (vtable entry `0x40100ee8`). In the stock OS
  these keys fall through to `KeyboardView` (`0x4001a0d2`).
- A second mod reading TRACK + TRIG in `KeyboardView`, or in any view below, would write other bytes. Both would
  install, and the second would never see its keys. No tool would notice.

## 3. The claims to collect

### 3.1 Saved data `[FAIT]`, from the notes and the manifests

| Holder | Sound k | Record slots | Other saved bytes | Scope | Source |
|---|---|---|---|---|---|
| OS | 0–22 | 0–23 (18 unused) | — | all | notes/47 §4.3 |
| Model-TG (`model-tg`, `model-tg-st`) | 23–27 | 24–29 | — | all `[HYP]` | notes/31, notes/47 §11 |
| SAMPLE | 25–27 (sample key) | 24–26 (key), 27 (filter mark) | — | SAMPLE's sounds | its manifest; One-Shot's TECHNICAL §6 |
| track-filter | 28–31 | 18, 27, 30, 31 | the p-lock rows of k ≥ 23 | all | notes/47 §4 |
| lfo-plus | 28–32 (LFO 2) | 30–31 (`+88`–`+91`, packed) | the p-lock rows of k ≥ 23 | all | notes/56 §3 |
| the shortcut layer (a part) | 28–31 | 28–31 | — | all: the copy does not look at the machine | notes/63 §11, `shortcuts.S` |
| REF2, through the layer | 28 (Octave) | 28 | — | REF2's sounds | its manifest |
| arp | — | — | byte `+512` of each track in the pattern | all | notes/32 §4 |

The scope of Model-TG's slots is still to be read in notes/31: its Attack, Filter and Resonance act on the stock
machines too, which suggests all sounds.

### 3.2 Gestures

| Combination | Holder | Scope | Situation | Stock meaning | Source |
|---|---|---|---|---|---|
| MACHINES held + COLOR, SHAPE, SWEEP, CONTOUR | track-filter (Filter Env, Env Decay, Cutoff, Reso) | all tracks | parameter pages | nothing | notes/47 |
| MACHINES held + DECAY, SWEEP, CONTOUR | Model-TG (Attack, Filter, Resonance) | all tracks | parameter pages | nothing | notes/31 |
| FUNC + PITCH | MACRO (lo-fi RATE / BITS) | MACRO's tracks | parameter pages | FINE | notes/55 |
| TRACK held + TRIG 1–6 | control-all-config | all | TRACK held | nothing: falls through to `KeyboardView` | notes/58 §2 |
| TRACK held + FUNC | latching-mute (the mute mode latches) | all | any | `[À FAIRE]` | its tweak |
| a TRIG held + PAGE, sequencer stopped or paused | trig-preview | all | grid | PAGE turns the page | notes/34 |
| RETRIG held + notes | arp (an arpeggio in place of the retrig) | all | keyboard | the retrig | notes/32 |
| TRIG 1–16 in Keys mode | chord-keys | CHORD's tracks | Keys mode | `[À FAIRE]` | notes/42 |
| FUNC + a press of LEVEL/DATA on the OUT/THRU line | midi-live-both | — | CONFIG › MIDI › PORTS | a press alone goes to OUT | notes/53 |
| LFO pressed on the LFO page | lfo-plus (LFO 2, 3, 4) | all | LFO page | closes the page `[HYP]` | notes/56 |
| RETRIG held + COLOR, SHAPE, SWEEP, CONTOUR | the shortcut layer, for the machines that declare a shortcut (REF2: COLOR) | the declaring machine's tracks | parameter pages | nothing | notes/63 §1 |

MACHINES is key code 5, the key Model-TG's guide calls PRESET (notes/31).

**The stock combinations** a mod must not take without saying so, as far as they are read (notes/63 §1.2,
notes/58 §2):
- FUNC + knob (fine adjust), TRACK + knob (Control All), LFO + knob (LFO destination), TRIG + knob (p-lock);
- TRACK + PUNCH / GATE (Control All), FUNC + TRACK (Track Setup), FUNC + MACHINES (the PRESET browser), FUNC + RETRIG
  (the retrig menu), TRACK + RECORD / PLAY / STOP (copy, clear, paste).

Key codes 3, 7, 12–15 and 32 are not traced yet (notes/63 §1.1).

Menu lines are appended, not taken: arp's and chord-keys' lines in the retrig menu make no gesture claim, like the
standard's `menu.track_setup` point (§3.1).

### 3.3 The other claims

- **Descriptors 1–4**, "Error" in the stock OS. The track filter turns them into parameters of every machine, and the
  shortcut layer shows the machines' shortcuts through them (machine −1). Exclusive, scope all.
- **Formatters:** SAMPLE replaces the formatter of its Cutoff (`object 53`, the stock `0x400456c8`), from its
  manifest.
- **MIDI:** the track filter's CC 74 and 71, NRPN 1:20 and 1:21 (notes/47). The stock map is not collected yet
  (STANDARD.md §5.5).
- **RAM:** SAMPLE's pool `0x43800000`–`0x46700000` (its manifest, computed today); lfo-plus's
  `0x4233f000`–`0x4233f49b` (notes/56 §3, only a line in `REGISTRY.md` today).
- **Views:** SAMPLE and REF2 draw the main screen and the knob view on their own tracks, through the dispatchers when
  both are in. level-pan-values draws on the main screen of every track through other hooks (`0x400081f2`,
  `0x4001aa4e`; STANDARD.md §3.1). No byte is shared, but the drawings may meet.

## 4. The claim format

### 4.1 Where claims live

| Kind of mod | File | Default scope |
|---|---|---|
| package | `tools/machines/<id>/manifest.json`, `claims` (exists) | its own machine |
| part of the builder | `tools/machines/<id>/part.json`, `claims` (new) | all |
| tweak of the folder | `tweaks/model-cycles_OS1.13/claims.json` (new): one entry per tweak, its claims and source | all |

- The tweaks' file is declared data, as `PROVENANCE.md` is.
- A tweak without an entry claims nothing the check reads. That holds for the engine tweaks, whose machine tables are
  byte claims, and for most screen and browser tweaks.
- Variants share one entry through a list of ids (`model-tg` and `model-tg-st`, `macro` and `macro-tg`).

### 4.2 Shapes

Today's lists stay valid: an item is a number or a string, with the file's default scope (`"sound_slots": [25, 26,
27]`, `"gestures": ["RETRIG + COLOR"]`). An object adds what a list cannot say, such as `{"slots": [28, 31], "scope":
"all"}` (a range, both ends included). The track filter's entry in `claims.json`:

```json
"track-filter": {
 "source": "notes/47",
 "claims": {
  "sound_slots": [28, 29, 30, 31],
  "record_slots": [18, 27, 30, 31],
  "plock_rows": true,
  "descriptors": [1, 2, 3, 4],
  "midi": {"cc": [74, 71], "nrpn": ["1:20", "1:21"]},
  "gestures": [{"combo": "MACHINES + COLOR/SHAPE/SWEEP/CONTOUR", "situation": "params",
                "meaning": "Filter Env / Env Decay / Filter Cutoff / Filter Reso"}]
 }
}
```

The shortcut layer's, in its `part.json`:

```json
"claims": {
 "sound_slots": [28, 29, 30, 31],
 "record_slots": [28, 29, 30, 31],
 "descriptors": [1, 2, 3, 4],
 "gestures": [{"combo": "RETRIG + COLOR/SHAPE/SWEEP/CONTOUR", "situation": "params",
               "meaning": "the shortcut of the track's machine"}]
}
```

- **Scope:** `all`, `machine` (the declaring package's machine), or `machine:<name>` for another machine, stock or
  package (`machine:CHORD` for chord-keys).
- **Other saved bytes:** `saved`, as `{"where": "pattern track +512", "bytes": 1}`.
- **The schema keeps its name** (`cycles-mod/0.1`): the object forms are additive (STANDARD.md §4.1). An unknown
  claim type makes the tools report "not checked against" instead of passing it.

### 4.3 Gestures as data

- **A combination** is written as the standard's tables write it: the held keys, then one action, joined by `+`, as
  in `TRACK + TRIG 1-6`, `MACHINES + COLOR/SHAPE/SWEEP/CONTOUR`, `RETRIG + notes`.
  - Its words come from one vocabulary: the key codes of notes/63 §1.1 (FUNC, TRACK, RETRIG, MACHINES, PUNCH, LFO,
    RECORD, PLAY, STOP, TRIG 1–16) and the knobs (PITCH, DECAY, COLOR, SHAPE, SWEEP, CONTOUR). Words for the keys not
    traced (PAGE, PATTERN, GATE, LEVEL/DATA, the pads) are added as they are read.
  - `1-6` and `/` expand. The tools compare *atoms*, one set of held keys and one action each: `TRACK + TRIG 1-6` is
    six atoms.
- **A situation** says where the combination acts: `params` (the parameter pages, the knob path of notes/63 §1.2),
  `grid`, `keys`, `page:LFO`, `menu:<name>`, and `any` by default.
  - It is the user's situation, not the view whose code reads the keys. Views are served from the end of the list
    (§2.3), so a view higher up takes a combination from every view below it.
  - Two named situations exclude each other; `any` meets all.
- **Taking a stock combination** (the list in §3.2) needs `"replaces": "<what the OS did>"`. For a package it also
  goes into `stock_behaviour.changes`.

## 5. The rules

### 5.1 Rule 2: exclusive points

Two claims whose scopes meet clash when:
- **gestures:** they share an atom in situations that meet, with another meaning (two identical claims are allowed,
  STANDARD.md §3.2);
- **descriptors:** they name the same descriptor;
- **formatters:** they name the same interface object;
- **p-lock rows:** both re-number the rows of k ≥ 23.

A gesture on a stock combination without `replaces` is refused: no tool can tell that its author meant it.

### 5.2 Rule 3: numbers

Two claims whose scopes meet clash when they name the same sound slot k, the same record slot, the same other saved
bytes, or the same CC or NRPN. A claim on the OS's own slots (k 0–22; record slots 0–23 except 18) is refused.

### 5.3 Rule 4, widened

The tweaks' RAM claims (lfo-plus's) are compared with the packages' RAM claims and with the build's payload, as the
packages' claims are today.

### 5.4 Views: a warning

Two drawings of the same view whose scopes meet, outside the dispatchers, are reported in the build report and in
`REGISTRY.md`, not refused. They may share the screen well, as level-pan-values and SAMPLE do in different places,
and only a look on the device tells.

### 5.5 The builder's parts

- The shortcut layer claims k 28–31, record slots 28–31, descriptors 1–4 and the four RETRIG combinations in
  `params`, with scope all. It owns them, and it copies the slots for every sound.
- A machine's shortcut is the layer's claim narrowed to that machine. Two machines' shortcuts on the same knob never
  clash, and a machine's shortcut clashes with nothing the layer does not clash with.
- So the layer computes, with no text:
  - lfo-plus: k 28–31, record slots 30–31;
  - the track filter: k 28–31, record slots 30–31, descriptors 1–4 (rule 1 finds it today, through the record
    hooks);
  - not arp: `RETRIG + notes` is another atom.

### 5.6 Declared and computed

Each tool lists, next to the computed ids, the declared conflicts it does not compute, and the computed ones that are
not declared (STANDARD.md §9, step 5).
- A declared conflict stays when its text gives a reason the claims cannot carry (sample-preview's: "plays sample
  files from the same browser and needs Model-TG").
- One the claims compute loses its hand entry where the data is model27's (the shortcut part). The folder's tweaks
  come from Modded-Cycles: their `conflicts` stay, and the report shows which ones are now computed.

## 6. Where it runs

- **`compose.py`:** `claim_conflicts()` next to `computed_conflicts()`.
  - A build's claims are its packages' and those of the parts it carries.
  - Against the folder's tweaks (`claims.json`), the ids go into the build's `conflicts`.
  - Between the build's own packages, a clash refuses the build, as overlapping RAM claims do today.
- **`composer.js`:** the same, from the claims the page carries.
  - The packages' come with `web_package`, the parts' with `web_part`.
  - The offered cards' come from `claims.json`, added by `gen_flasher_tweaks.py`.
  - `webcompose_check.sh` compares the lists.
- **`check_overlaps.py`:** the claims too, for every pair it checks today.
  - A clash fails until it is declared, as shared bytes do.
  - It also checks `claims.json`: every id exists, and every word is in the vocabulary.
- **`registry.py`:**
  - `REGISTRY.md` §6, the saved data, from the claims instead of `DECLARED`;
  - new sections for the gestures (combination, holder, scope, situation) and MIDI;
  - `--check` as today.

## 7. Proofs and done criteria

- **No firmware changes.** These stay byte for byte:
  - the MAIN OS of every `REF_MAINOS` entry, and of the nine selections of `webcompose_check.sh`;
  - the `writes` and `append` of `27-sampler.json`, `28-refmachine.json` and `29-refmachine2.json`.

  Only `conflicts` may change.
- **The three cases of §2, computed:**
  - lfo-plus × the track filter (slots, p-lock rows);
  - lfo-plus × the shortcut layer: REF2's `conflicts` keep `lfo-plus` while the part's `conflicts_declared` is
    empty;
  - control-all-config × a synthetic tweak that takes `TRACK + TRIG 3` in `keys`.
- **The known pairs agree:**
  - the track filter × Model-TG (MACHINES + SWEEP and + CONTOUR);
  - SAMPLE × Model-TG (k 25–27) and × the track filter (record slot 27), which rule 1 already finds;
  - two machines with `RETRIG + COLOR` do not clash, and REF2 × arp do not either.
- **A self-test** with synthetic claims (scopes, situations, ranges, the stock list), run without firmware, like
  `check_overlaps.py`.
- **The folder passes.** `check_overlaps.py` finds no clash between two tweaks that can be ticked together. If it
  finds one, that is a finding to record and declare, not to hide.
- **Unchanged:** `registry.py --check`, `webcompose_check.sh` (with claim probes) and the page's smoke test.

## 8. Order of work

| Step | Work | Done when |
|---|---|---|
| **C1** | the vocabulary and the format (§4); `claims.json` for the folder (§3, each entry with its note); `claims` in the shortcut part; the scopes in the three manifests; the data's own check | the data checks; nothing is computed yet |
| **C2** | the rules in Python (§5), in `compose.py` and `check_overlaps.py`; the self-test; the shortcut part's declared lfo-plus removed; the report of declared and computed conflicts | §7 for Python |
| **C3** | `registry.py`: the saved data, the gestures and MIDI from the claims; `DECLARED` removed | `registry.py --check` |
| **C4** | `composer.js` and the page's claims; `webcompose_check.sh`; the standard 0.4 (§4.2 the shapes, §4.4 rules 2 and 3 as built, §5.2 to §5.5 from the registry, §9 steps 3 to 5) and APPLYING | JavaScript equals Python |

One commit per step, with the trailer. No step changes a build, so none needs a release entry, unless the page shows
computed reasons (§9, decision 5).

## 9. Decisions for the maintainer

*Answered in §11.*

1. **Where the tweaks' claims live:** one declared file, `claims.json` (recommended: one place to review, as
   `PROVENANCE.md`), or a `claims` field written by each tweak's generator.
2. **How gestures are written:** strings on a fixed vocabulary, with optional fields (recommended: as the standard's
   tables write them), or fully structured objects.
3. **A stock combination taken without `replaces`:** refused (recommended), or only reported.
4. **Views:** a warning (recommended), or a refusal.
5. **The page:** a computed reason ("both keep data in record slots 30–31") where no hand-written reason exists
   (recommended), or the hand texts only.
6. **Which tweaks get claims in C1:** those of §3 (recommended: the others claim nothing a tool could check), or a
   pass over all 286.

## 10. Open `[À FAIRE]`

- Model-TG's slots and their scope (notes/31, notes/47 §11), and whether it re-numbers the p-lock rows of k 23–27.
- The stock meaning of TRACK held + FUNC (latching-mute), and of the TRIG keys in Keys mode (chord-keys, notes/42).
- The keys not traced (codes 3, 7, 12–15, 32) and the knobs beyond the six, before a mod claims them.
- The stock CC and NRPN map (STANDARD.md §5.5).
- Machine gestures through the registrar's `knob_hook` ([notes/59](59-level-b-builder.md) §3) are not connected:
  `compose.py` and `composer.js` write 0. A package's gesture stays a claim until they are.
- The claims are declared, so a wrong claim gives a wrong answer. The emulation proofs stay the check of what the
  code does: the claims check stands in front of them, not in their place (STANDARD.md §8).

## 11. Decisions (2026-10-22)

The maintainer took the six recommendations of §9: "Übernimm deine Empfehlungen für alle sechs Entscheidungen" (take
your recommendations for all six decisions).

1. **The tweaks' claims** live in one declared file, `tweaks/model-cycles_OS1.13/claims.json`, each entry with its
   source note (§4.1). The tweaks' generators stay as they are.
2. **Gestures** are strings on the fixed vocabulary of §4.3, with the optional fields `situation`, `scope`, `meaning`
   and `replaces`.
3. **A stock combination taken without `replaces`** is refused (C2).
4. **Views:** two drawings of one view whose scopes meet give a warning in the build report and in `REGISTRY.md`, not
   a refusal (C2, C3).
5. **The page** shows a computed reason where no hand-written one exists (C4), in English and French like everything
   users see (AGENTS.md). The two cards offered today do not clash, so no reason shows yet.
6. **C1 covers the tweaks of §3.** The others get no entry: they claim nothing a tool could check.

## 12. C1 built (2026-10-23)

### 12.1 What was built

- **`tools/claims.py`**, standard library only:
  - **the vocabulary:**
    - the keys by their codes (notes/63 §1.1), with GATE, PAGE and PATTERN whose codes are not traced;
    - the knobs by number, and DATA for LEVEL/DATA;
    - two other actions, NOTES (notes on the pads or the keyboard) and DATA-PRESS;
    - the situations `any`, `params`, `grid`, `keys`, `page:LFO`, `menu:RETRIG`, `menu:TRACK-SETUP`,
      `menu:MIDI-PORTS`;
    - the scopes `all`, `machine`, and `machine:<NAME>` for the six stock machines, MACRO, ACID or a package.
  - **the stock list:** 12 combinations, 140 atoms, each with its source. The LFO page's entry is marked as a
    hypothesis.
  - **the reading:** `atoms()` gives a combination's atoms, `normalize()` a holder's claims in one form with their
    scopes, and `holders()` the packages, the parts and the tweaks' entries.
  - **`--check`:**
    - `claims.json`: its schema and fields; each id pattern names tweaks of the folder; no tweak in two entries; no
      package, since a package's claims stay in its manifest;
    - every claim: its type, its range (k 0–32, record slots 0–31, descriptors 1–4, CC and NRPN 0–127), its
      words, its situation and its scope;
    - each manifest's claims against its `uses`: the RAM, the views, and each shortcut with its combination and
      slots;
    - the shortcut part's claims against its own list.
  - `--list`, and `--self-test` (54 cases).
- **`tweaks/model-cycles_OS1.13/claims/claims.json`:** 11 entries for the tweaks of §3. Each has its source note,
  and 6 items are marked `open`.
  - They cover 139 of the 286 tweaks. MACRO's lo-fi accounts for 128 of them: every tweak with MACRO carries it,
    because `gen_syntakt_engines.lofi_index` finds MACRO wherever it stands.
  - The file sits in a subfolder, not next to the tweaks as §4.1 planned. About a dozen tools read every `*.json` of
    the tweak folder as a tweak and would stop on it: `gen_flasher_tweaks.py`, several proofs.
- **The shortcut part's claims:** k 28–31, record slots 28–31, descriptors 1–4, and RETRIG + the four knobs in
  `params`. Its declared lfo-plus stays until C2 computes it.
- **The manifests:**
  - REF2's gesture is now an object (`params`, "Octave");
  - SAMPLE's formatter has scope `all` (§12.2);
  - REF claims nothing.

### 12.2 A formatter belongs to an interface object, not to a machine `[FAIT]`

- SAMPLE shows its Cutoff through interface object 53, which is also SNARE's SWEEP (`machine/view.c`):
  - `smp_fmt_cutoff` falls back to the stock formatter off SAMPLE's tracks;
  - `smp_view_install` puts it in only while the stock formatter is there.
- An object has one formatter pointer. Two formatter claims on one object therefore meet whatever their scopes. A
  second mod on object 53 would leave SAMPLE's Cutoff showing the stock 0..127, and nothing would say so.
- So C2 compares formatters by object alone, a change to §5.1.

### 12.3 Checks

- **New, green:**
  - `claims.py --self-test`: ALL OK (54 cases).
  - `claims.py --check`: ALL OK. That is 11 entries for 139 tweaks, 12 stock combinations (140 atoms), 3 packages
    and 2 parts.
- **Unchanged and green:** `gen_parts.py --check`, `gen_flasher_tweaks.py --check` (no claim reaches the page yet),
  `gen_sampler.py --check`, `gen_refmachine.py --check`, `check_overlaps.py`, `registry.py --check`,
  `webcompose_check.sh` (the nine selections identical, the MAIN OS hashes of §7) and `py_compile`.
- **Nothing is computed yet.** No tool reads the claims for a conflict, so every build is byte for byte what it was.
