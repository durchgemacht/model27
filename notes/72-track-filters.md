# 72 — A filter on every track, the Model:Samples' first: the filter slot and Samples

The maintainer's request of 2026-10-31, step K4 of the key map of that day (RETRIG is the filter's level): a filter on
every track, chosen per sound; first SAMPLE's filter as it is, its envelope (Env depth, AD) later in the same filter.
Decided with it: at most two filters in a build, the choice kept by each sound, and a build has either a machine's knob
values (MACHINES + a knob) or filters. The builder's part `fltslot` (`tools/machines/fltslot/`), the filter package
`smpfilter` (`tools/machines/smpfilter/`, id 1, "Samples"), the reference filter REFF (`tools/machines/refflt/`, id 255,
never offered), the card's tweak `72-smpfilter.json` (`tools/gen_smpfilter.py`), proof in emulation
`tools/emu/test_fltslot.py`. Addresses: VAs of OS 1.13.

## In short

- **A filter point on every track**, after Volume + Dist (`0x40059852`), where the Model:Samples has its own filter: a
  builder part (like `fxslot`, notes/68) with a table of filters by id; each sound chooses one (k 32 bits 0–7, 0 = none).
- **The first filter, "Samples"** (id 1): SAMPLE's filter as it is (Cycles One-Shot's `smp_filter`, the Model:Samples'
  laws measured and rebuilt), on Cutoff and Reso. Env depth and AD can come later into the same filter, under the same id.
- **Its values are real parameters of every machine** (descriptors 1–4, k 28–31): p-locks, LFO and velocity
  destinations, Control All, CC 74 / 71. With RETRIG held: SWEEP Cutoff, CONTOUR Reso, COLOR and SHAPE reserved for Env
  depth and AD, PITCH the filter's type.
- **Zero is neutral everywhere**, so a sound of the official OS, of an older build or a new one plays as before, and a
  later Env / AD changes no saved sound. The official OS reads a filter build's sound without its filter, nothing else
  lost.
- **Cost:** about 0.25 % of a block for the part; Samples 922 to 1 492 instructions a track and block while it filters,
  160 at the centre, by the emulator's count; on the machine, six filters with Control All on Cutoff took at most
  10.0 % of a block (§18).
- Proven in emulation (§7), tested on the Model:Cycles from the command line (§20) and from the page (§23); a card of
  the flasher's Filters section.

## 1. What a sound keeps

| Where | What | Words | Neutral |
|---|---|---|---|
| k 28 | Cutoff | 0..0x7f00, centre 0x4000 = off; below a lowpass, above a highpass (SAMPLE's SWEEP) | 0x4000 |
| k 29 | Reso | 0..0x7f00 | 0 |
| k 30 | Env depth (reserved) | 0..0x7f00, centre 0x4000 = no envelope | 0x4000 |
| k 31 | AD (reserved) | 0..0x7f00, centre 0x4000 = the shortest | 0x4000 |
| k 32 bits 0–7 | the filter's id | 0 none, 1 Samples, 2–239 later filters, 240–255 references | 0 |
| k 32 bits 8–9 | the machine's switches (unchanged, notes/63 §16) | | |
| record slots 28–31 | k 28–31 XOR the value's neutral word; 0 for a value no filter of the build declares | | 0 in the record |
| record slot 18 | k 32's low 10 bits; bits 10–12 the LFO's destination, 13–15 the velocity's (§5) | | |

- The record's XOR is the Modded-Cycles track filter's way (notes/47 §4.1, proven on the machine there): a record that
  never held the values reads 0 and loads the neutral word. A new sound gets the descriptors' defaults `[FAIT, §9, §11]`.
- Unsigned words with a centre: the OS maps CC and the LFO onto a descriptor's minimum..maximum, as the track filter
  did on the machine.
- Sounds whose k 28–31 hold a machine's knob values (REF2's Octave, CHORD Tables' table) mean something else in a filter
  build. Neither machine is offered, and the composer refuses them with a filter (rule R1, §6).

## 2. The audio

- **The point** `[FAIT]`: `0x40059852`, `jsr 0x40056f58` (Volume + Dist, `TRK` = `0x80001858`, the smoothed parameters
  in a2) in the audio block; the six track buffers `0x80001858 + 128 t` (32 × int32, mono) after Volume + Dist, before
  level, pan and sends; the smoothed words of track t at `a2 + 14 + 66 t + 2 k`, so k 28–31 at `+56..+62` with p-locks,
  LFO and velocity in them; `a3 + 16` the tracks triggered in the block (notes/47 §2, the standard's
  `track.post_voldist`). Contract: d2–d7 / a2–a6 kept, MACSR restored, acc0–acc3 left at 0.
- **The part `fltslot`**: `fl_post` runs Volume + Dist with the stack it expects, then `fl_run(a2, *(a3 + 16))`: per
  track the id in the low byte of k 32 of the sound the note plays (`*0x800017ec[t] + 84`, or the copy
  `0x800015ae + 66 t + 64` when there is no sound), its entry in the table (an id the build lacks counts as none: the
  track untouched, bit for bit). Same entry: `process(block, words, track, triggered)`. A change of id: the stopping
  filter runs on a copy of the input, the starting one is reset and runs on the block, a crossfade across the 32 frames,
  then the stopping one is reset. Before each `process`: MACSR 0xa0, acc0–acc3 cleared. MACSR back and the
  accumulators cleared only when a filter ran.
- **The filter's contract** (point `track.filter`): `process(int32_t *block, const int16_t *words, uint32_t track,
  uint32_t triggered)`, words the smoothed k 28..31; `reset(uint32_t track)`; C ABI. The filter keeps its six states in
  its own variables (as the effects do); `triggered` is there for an AD envelope.
- **Samples**: Cycles One-Shot's `smp_filter.c`, `smp_filter_cf.S` and `smp_filter_tab.c`, compiled from SAMPLE's package
  (`tools/machines/sampler/src/`, byte-identical to One-Shot `c32c49d`), and a glue of its own (`smpfilter.c`): per track
  and block `smp_filter_set` with the smoothed k 28 and k 29, then `smp_filter_run`. At the centre the block passes
  untouched. Since 0.2 (§17) `smp_filter_set` is skipped while the words and the filter have settled (bit for bit), and a
  silent block is skipped once the filter has rung out (below -102 dB). k 30, k 31 and the trig bit are not read yet.
- **Cost** (instructions per track and block, Samples' own code, counted by the proof and declared in its manifest):
  lowpass 922, highpass 976, centre 160, gliding 1 464, silent 176, the first block after a reset 1 492; the part 263
  with every track on none. The composer's rule (`compose.fl_cost`): six times the dearest declared state, refused past
  the effect slots' limit; Samples' worst is 8 952 instructions a block, 8.3 % (108 225).

## 3. The knobs (the key map's RETRIG level)

- **The lookup** `[FAIT]`: ParameterPageView's vtable entry `0x401005a8` (stock `0x4001e814`) gives the descriptor under
  a knob for a turn, TRACK + knob and the popup at a track change. `fl_knob` takes it in front of the shortcut layer's
  `sc_knob`: RETRIG + SWEEP / CONTOUR / COLOR / SHAPE give descriptors 1 / 2 / 3 / 4 when the build has that value, on
  every machine, also with FUNC, TRACK (Control All), LFO, MACHINES or a held trig (a p-lock): they are real parameters,
  unlike a machine's values. Names and formatter follow the track's sound's filter (the first filter's for none), in both
  descriptor tables and the interface object. Since `fltslot` 0.10 (notes/73 §19) a knob the selected track's filter
  has no value on, and every knob on none, gives descriptor 5 as a popup that changes nothing (Track FX over OFF, the
  filter's tag over `---`).
- **The descriptors** `[FAIT, notes/47 §3]`: 1–4 are the OS's unused "Error" entries. `fl_boot` (at `0x4004486c`, in
  place of `jsr 0x4005a274`, then the builder) writes them as the track filter did: group 7 (every machine), k 28..,
  0..32512, defaults 0x4000 / 0 / 0x4000 / 0x4000, CC 74 / 71, NRPN 1:20 / 1:21, the first filter's names; only as many
  as the build's filters declare values. Into the stock table and the one the OS uses when the build adds machines.
- **The type**: RETRIG + PITCH alone (or with MACHINES) gives descriptor 5, another "Error" entry, written as a
  display-only row: group -1 (no table, no CC, no LFO, no p-lock row), k 0, the formatter the type's name, descriptor 1's
  step settings. `fl_keys`, at the encoder handler's question for TRACK (`0x4001f886`), in front of `fxslot`'s `fx_keys`:
  on descriptor 5, `fl_step` steps the sound's id through none and the build's filters (four detents a step, a pause of
  0.4 s starts the count again, the ends stop, an unknown id counts as none) and ends the handler without an edit.
- **LFO + a knob** `[FAIT, §15]`: the OS's own path (`0x4001eaa2`) builds its own list of descriptors and does not ask
  the lookup; `fl_lfo` at `0x4001ead8` gives descriptors 1..n there too for RETRIG + COLOR..CONTOUR.
- **P-locks of k ≥ 23** `[FAIT, notes/47 §4.3]`: the stock OS saves them onto LFO Speed or loses them. The part carries
  the track filter's fix: the pattern's p-lock table k → index at `0x4005b998` and `0x4005baca` (operand `0x4010ee4c`)
  points at a table of 33 entries (k 23..31 → index 24..32, k 32 → 0), and the index → k step at `0x4005aa34` jumps to
  `fl_conv` for 24..32. Claimed as `plock_rows`.

## 4. The record

- The shortcut layer copies k 28–31 into slots 28–31 and k 32 into slot 18 for every sound (notes/63 §3, §16); a filter
  build always carries it. `fl_save2`, `fl_save1` and `fl_load` take the three record functions in front of the layer's
  wrappers; after the chain, the save writes slots 28–31 XOR the neutral words (0 for an undeclared value) and the
  destinations (§5), the load undoes both.
- The official OS reading a filter build's record `[FAIT, §9, §12]`: it loads slots 0–23 only, slot 18 lands on k 0
  (unused), the destinations read "none". The sound keeps its machine, its parameters and SAMPLE's key, and loses only
  its filter and the destinations to it.

## 5. LFO and velocity destinations

- `[FAIT, §9]` The OS keeps the LFO's destination in descriptor 32 (k 4's high byte) and the velocity's in a long at the
  sound's `+88`, and saves both through the k → slot table without a bound: a destination k 28–31 comes back as k 5–8,
  another parameter. The track filter kept its own in slot 27, which is SAMPLE's: not possible here.
- The part's save writes "none" where the OS keeps them (slot 4's word and `+94` = 0) and keeps them in slot 18: bits
  10–12 the LFO's destination among k 28–31 (0 none, 1–4), bits 13–15 the velocity's; the load puts them back (only for a
  value the build has) and clears those bits in k 32.

## 6. Claims, composers, flasher

- **Claims** (`part.json`): k 28–31, record slots 28–31, descriptors 1–4, `plock_rows`, CC 74 / 71, NRPN 1:20 / 1:21,
  the gestures RETRIG + SWEEP / CONTOUR / COLOR / SHAPE, RETRIG + PITCH and LFO + RETRIG + a knob. Descriptor 5 stays
  unclaimed: the claims' vocabulary (the standard's §3.1) knows 1–4. k 32's low byte and slot 18's bits 10–15 are shared
  with the layer by agreement (the claims have no bits). In a filter build the layer's claims are narrowed
  (`claims.narrowed`) by the part's.
- **Composers** (`compose.py`, `composer.js`, byte for byte): a package whose uses name `track.filter` is a filter (one
  filter a package, never with a machine or an effect); at most two in a build, an id once; **R1**: a filter is refused
  with a machine that declares a knob value (REF2, CHORD Tables, REFC); every filter build carries the shortcut layer;
  the part's sites in front of the layer's (knob, records) and of `fxslot`'s (TRACK's question); the load (`fl_cost`).
- **Flasher**: a fourth section, Filters, with the card Samples (experimental); the page composes it with the machine
  and effect cards into one tweak.
- **Not done**: the standard's text (a point `track.filter`, descriptor 5 in the vocabulary), only on the maintainer's
  word.

## 7. The proof

`tools/emu/test_fltslot.py --cycles model-cycles_OS1.13.syx` (Unicorn; `--dry`: sites, data block and refusals only),
selections refflt; refflt + refflt2 (a copy of REFF with id 254); sampler + refflt; refdelay + refflt; smpfilter;
smpfilter + refflt; sampler + smpfilter:

- start-up (the bootstrap's depacker, the boot hook); the sites and the data block;
- the audio: the voice loop then `0x4005984a..0x40059858`, stock and with the build, five scenes of 24 to 40 blocks
  (ids 0, an id not held, the switches alone: the stock OS's bit for bit; filters bit for bit against the models, REFF's
  exact integer model and the host build of SAMPLE's own sources through ctypes; changes; a hot scene with Volume + Dist
  at 127, Reso at the top and Cutoff sweeping across the centre); MACSR and the accumulators at each filter's entry and
  after the part; registers and stack; the costs, counted and checked against the manifest;
- the boot's tables (rows, k → descriptor on every machine, CC, NRPN, a new sound's defaults), the knob lookup (every key
  set × a held trig × 16 knobs), LFO + a knob through `0x4001eaa2`, the formatters, the type through the handler's
  frame, the pattern's p-locks, a real machine change, the record (v2, v1, the load, the official OS both ways, a SAMPLE
  sound through the whole chain), the load window of the measuring build;
- the composer's refusals (the manifest's rules, three filters, an id twice, R1).

## 8. Steps

| Step | What | Done when |
|---|---|---|
| T0 | Read the open points: a new sound's k 28–31, descriptor 5 unused, the OS's "no destination", the level after Volume + Dist, the official OS reading a filter record | **done 2026-10-31 (§9)** |
| T1 | The part: the audio point, ids, states, change of id | **done 2026-10-31 (§10)** |
| T2 | The knobs: RETRIG + knob, descriptors at boot, the type, the p-lock fix | **done 2026-10-31 (§11)** |
| T3 | The record: XOR, destinations | **done 2026-10-31 (§12)** |
| T4 | Samples as a package (id 1), its cost | **done 2026-10-31 (§13)** |
| T6 | The machine (pulled before T5) | **« passt », 2026-11-01 (§14 to §18, §20)** |
| T5 | Composers, claims, registry, the card, the guide | **done 2026-11-01 (§19)** |
| T7 (later) | Env depth and AD in Samples, same id | its proof, the machine |

## 9. T0, read in the code (2026-10-31)

- **A new sound's k 28–31** `[FAIT]` (notes/47 §3.4 and its emulation tests): a sound initialized (`0x400618f2` →
  `0x40061866`: a new project, a cleared sound) takes for each k the default of its descriptor through the tables built
  at boot (`0x4005a274`). With descriptors 1–4 in group 7 (every machine) and copied into the active table at boot, a new
  sound gets the centre for Cutoff, Env and AD and 0 for Reso. A machine change resets only the five parameters of the
  machine's record (`0x40014072`, notes/63 §9): the filter's values and its id stay (proven in §11).
- **Descriptor 5** `[FAIT]`: the stock table's 0–5 and 10–13 are "Error" entries, group -1, k -1, range 0..0, sort key
  32767, names "Error" / "ERR" (6–9 are Machine Type, Solo, Mute, Track Level, group -1 but used). Their CC fields are
  leftovers: 1 → CC 1 (+33), 2 → CC 2 (+34), 3 → CC 6 (+38), **5 → CC 10**, 10 → CC 99/98, 11–13 → CC 120, 121, 123;
  no NRPN. Group -1 keeps them out of the tables built at boot, so no CC reaches them; an edit would still send the CC,
  so every descriptor the part uses gets its own CC or none. For the type, descriptor 5 stays group -1 with **k 0**, the
  OS's unused parameter, its interface object's "Error" picture (`+0x2c`) cleared. That no machine's knob row holds 5:
  proven in §11.
- **LFO and velocity destinations** `[FAIT]` (save `0x4005afa0`, load `0x4005aecc`): the LFO's destination is a
  parameter of its own, descriptor 32 "Destination" / "DEST" (group 17, k 4, 0..32512, default 0), whose high byte is
  the destination's k; the velocity's is a long at the sound's `+88`, a k too. **k 0 means none** (the default, and the
  OS's unused parameter). The save writes the record's `+36` (slot 4) as `table[k] << 8` and `+94` as `table[k]`'s low
  byte with the k → slot table `0x4010ee4c` (23 entries) and no bound: for k 28–31 it reads past the table into the slot
  → k table `0x4010eea8`, so the record gets slots 5–8 and the load gives back k 5–8. The load maps `+36`'s high byte
  through `0x4010eea8` (24 entries, slot 18 → k 0) without a bound, and `+94` with one (24 and above → k 0).
- **The level after Volume + Dist** `[FAIT, by reading]`: the stage at `0x40056f58` is the distortion (drive 0.154 up to
  1.0 above V 64, three soft clips `2u - u|u|`, a crossfade from V 60 to 68); the volume itself (`min(V/64, 1)²`) and
  Track Level are applied later, in the mixer (`0x400567ba`). So the filter sees the voice's level when V ≤ 60 and up to
  full scale with the distortion. SAMPLE's loop runs on half the signal and saturates only an output beyond full scale:
  a hot, distorted track with high resonance clips its peaks, where the Model:Samples wraps. No change planned.
- **The official OS reading a filter build's record** `[FAIT]`: slots 0–23 only (slots 28–31 ignored), slot 18 on k 0,
  the destinations "none" (above).

## 10. T1, the part (2026-10-31)

- **`fltslot` 0.1** (`tools/machines/fltslot/`: `entries.S`, `fltslot.c`, `part.json`, MIT): `fl_post` at `0x40059852`
  and `fl_run` as in §2. 642 bytes of code; data block 188 bytes (count, 4 entries of id / process / reset, cur[6],
  old[32]).
- **REFF** (`tools/machines/refflt/`, id 255, never offered): a one-pole lowpass with a shift from k 28 and an attenuation
  from k 29, restarted by a note; exact integer arithmetic, modelled in the proof. Object built by
  `tools/gen_refmachine.py`.
- **compose.py**: `FILTER_POINT = "track.filter"`; `load_manifest` validates a filter (id 1..255, process first in roots,
  reset in roots, no patch points, uses only the slot and RAM, name ≤ 15, short ≤ 5, one filter a package, never with a
  machine or an effect); `fl_layer` (table by id, at most the part's `most` = 2, an id once, the sites). Builds without
  filters unchanged.
- **Unicorn, the maintainer's run (2026-10-31): ALL OK** for refflt, refflt + refflt2, sampler + refflt, refdelay +
  refflt: start-up; sites and data block; four scenes bit for bit against the model (24 of 24 quiet blocks the stock
  OS's, 116 blocks with a filter, 11 changes, 14 with two filters); 503 / 506 filter calls with MACSR 0xa0 and clear
  accumulators, after the part the stock OS's EMAC; registers, stack, no access outside memory; all refusals. The part
  cost 258 instructions a block with every track on none (294 with two filters), about 0.24 % of a block; with REFF on
  all six tracks 3 420.

## 11. T2, the knobs (2026-10-31)

- **`fltslot` 0.2** (2 228 bytes of code, data block 700 bytes + strings): `fl_boot` and the rows (§3); `fl_knob` in front
  of `sc_knob` (the composer drops the layer's own write, so builds without filters stay byte for byte); RETRIG + PITCH
  → 5 only alone or with MACHINES (not with FUNC, TRACK, LFO or a trig: an LFO destination or Control All on k 0 would be
  nonsense); object 5 gets the type's formatter and **descriptor 1's step settings (+0x10)**, since the handler's step
  (`0x4006f96a`) reads the object's settings and descriptor 1 is the layer's, proven on the machine; `fl_keys` in front
  of `fx_keys` (the composer drops `fxslot`'s write); `fl_fmt_cut` (L64 .. OFF .. H63, three characters) and
  `fl_fmt_type` (the selected track's filter's tag or "OFF"); formats "int" = `0x400456c8`, "centre" = `0x40045bd6`,
  "cutoff" = `fl_fmt_cut`, or a symbol of the filter; the p-lock fix (§3; the other references of `0x4010ee4c`,
  `0x4005aa82` / `0x4005aff4` / `0x4005b0a8`, stay).
- **The filter's manifest**: `short` is the type's name on screen (1..3 characters); `params`: 1..4 values in the order
  k 28..31 (RETRIG + SWEEP, CONTOUR, COLOR, SHAPE), each long ≤ 15, short ≤ 4, a format. REFF 0.2: "REF", POLE / ATTN.
- **The composer**: every filter build carries the shortcut layer (for the record chain of T3); rule R1.
- **Noted for T3**: a sound made in a build whose filters declare 2 values holds k 30 = k 31 = 0 (no descriptor, no
  default); saved with the plain XOR it would come back as full negative once Env / AD exist. So the save writes the
  record slots of undeclared values as 0.
- **Unicorn, the maintainer's run (2026-10-31): ALL OK**, sections 1–10. T0's two open points are proven: a real machine
  change (KICK → SNARE through `0x40014072`) after the boot's tables with group-7 descriptors keeps k 28..31; descriptor 5
  lands in no table (k → descriptor for k 0 and all others unchanged on every machine, no CC, no NRPN).

## 12. T3, the record (2026-10-31)

- **`fltslot` 0.3** (2 688 bytes of code, data 720 bytes + strings): `fl_save2`, `fl_save1`, `fl_load` take the three
  record functions' first 8 bytes (jmp + nop, as the layer did) in front of the layer's `sc_save2` / `sc_save1` /
  `sc_load` (the composer drops the layer's three writes). The layer's wrappers still run the next of their chain
  (SAMPLE's wrapper or the stock body) and copy k 28..31 / k 32; then the part saves or loads as in §4 and §5. The load
  works on version 2 only, as the stock load.
- A sound from a build without filters but with the layer (REF2's Octave in k 28) loads XORed in a filter build: the
  accepted case (neither REF2 nor CHORD Tables is offered; R1 keeps them apart).
- **Unicorn, the maintainer's run (2026-10-31): ALL OK**, sections 1–11: record v2 and v1 (slots 28..31 0x5234 / 0x5600 /
  0 / 0, slot 18 0x47ff, none at slot 4 and `+94`), the load (values back, undeclared at the neutral word, LFO → k 28,
  velocity → k 29, k 32's low bits), the official OS on a filter record (no destination, where its own record gave k 5
  and 6) and a filter build on an official record (neutral words, no filter), a SAMPLE sound's key and switches through
  the whole chain.

## 13. T4, Samples (2026-10-31)

- **Package `smpfilter`** (MIT, order 72, id 1, name "Samples", type tag "SMP"; values Filter Cutoff / FREQ with the
  part's L/OFF/H formatter, Filter Reso / RESO int): `smpfilter.c` and SAMPLE's own sources by path (§2), no copy.
  19 518 bytes of code and table; a build with SAMPLE carries the table twice.
- **`tools/gen_smpfilter.py`**: the object (`--check`) and the card's tweak (T5).
- **The proof**: selections smpfilter; smpfilter + refflt; sampler + smpfilter; a fifth scene (Volume + Dist at 127, Reso
  127, Cutoff sweeping across the centre); `filter_cost` counts Samples' own instructions per track and block into
  `build/filter-cost.json` and checks them against `cost.emulation` in the manifest.
- **Unicorn, the maintainer's run (2026-10-31)**: Samples bit for bit against the host build of SAMPLE's sources in every
  scene, the hot one too (peaks 0.91 FS), switching Samples ↔ REFF, with SAMPLE in the build; the cost line failed once by
  design (nothing declared yet). Counted: lowpass 1 101, highpass 1 165, centre 50, gliding 1 576, first 1 598; declared;
  the rerun ALL OK.

## 14. Builds for the machine (T6 pulled before T5, 2026-10-31)

Built with `tools/compose.py` (git-ignored `build/k4-device/`): Samples alone; SAMPLE + Samples; Samples + REFF (the type
through OFF / SMP / REF); SAMPLE, Digital Delay, POTS, Samples with Control All Config, Trig Condition Order and Trig
Preview. What to try: the type (RETRIG + PITCH), Cutoff and Reso (RETRIG + SWEEP / CONTOUR, no click across the
centre), a hot track with high Reso, p-locks (a trig held + RETRIG + a knob, both orders), the LFO's destination (LFO +
RETRIG + SWEEP), FUNC, Control All, a sound lock with another type, new sounds, save and reload, SAMPLE's own filter and
switches next to it, two filters' names and the crossfade, the effect gesture and the other cards.

## 15. The machine, the first build (2026-11-01), and `fltslot` 0.4

The maintainer on Samples alone: everything fine but three points.

- **LFO + RETRIG + SWEEP did not reach Cutoff** (a bug). LFO + a knob does not ask the knob lookup: ParameterPageView's
  `0x4001eaa2` (called by the encoder handler at `0x4001f598` when LFO is held) builds its own list of 12 descriptors from
  a machine record (`0x4000bf42(1)`, KICK's: only the k matters, `0x4005a4e8` maps a descriptor to its k), takes
  `list[knob]` at `0x4001ead8` and sets descriptor 32 to `k << 8` on the selected track's sound, or on all six with TRACK
  held (Control All Config hooks that loop at `0x4001ebd2`, another site). RETRIG was never read there. **Fix, `fltslot`
  0.4:** `jsr fl_lfo` at `0x4001ead8` over `move.l (a0,d2.l*4),d2 ; tst.l a0` (free in the registry): descriptor 1..n for
  COLOR..CONTOUR with RETRIG held, then `tst.l a0` for the branch that frees the list.
- **FUNC + RETRIG + SWEEP's "fine steps"**: the test list took "FUNC + knob = fine adjust" from the claims' stock list
  (notes/63 §1.2) without checking it on the machine. What FUNC does there is the stock OS's; the same behaviour as FUNC +
  a stock knob is all that matters. Not a filter question.
- **"A new sound"** meant a sound the OS initializes (a new project, a cleared sound): type OFF, Cutoff at the centre,
  Reso 0. A sound from an older project gives the same (the record's XOR).
- The proof's section 5b runs the whole `0x4001eaa2` with the records filled, against the build without the filters. Its
  first run failed on a fault of the test (the boot's rows not written before, so k -1); with `fl_boot` first, the rerun
  (2026-11-01) **ALL OK**: LFO + RETRIG + SWEEP / CONTOUR set the destination to k 28 / 29 through the OS's own path.

## 16. The machine, the four builds (2026-11-01): fine, but the load

The maintainer: « passt alles soweit ». But with the filter on all six tracks the display got very laggy while turning
with the pattern running (Control All on Cutoff); no dropouts. Two cross-checks on the same build: **A** six tracks on
SMP, Control All on a stock knob: laggy; **B** six tracks on OFF, TRACK + RETRIG + SWEEP: fluid. So the UI path of RETRIG
+ a knob is not it: six running filters leave the UI too little time once Control All's six edits a detent come on top.
The emulator counts instructions and does not time memory or the EMAC's waits (each `movclr` waits for the MAC
pipeline; the Chamberlin loop is four dependent chains a frame). The same holds for six SAMPLE tracks with SAMPLE's own
filter.

## 17. Measured, and lighter: `fltslot` 0.5, Samples 0.2 (2026-11-01)

- **`fltslot` 0.5**: `fl_run` times itself with DMA timer 0 (135.168 MHz, a block is 90 112 ticks; `fl_measure`: a window
  of 750 blocks = 0.5 s, average and peak share of a block in tenths of a percent; data block 740 bytes). A measuring
  build (`compose.py --diag-filters`) shows the average in Filter Cutoff's popup and the peak in the type's; normal
  builds count but show the values. 3 336 bytes of code.
- **Samples 0.2**: `smp_filter_set` skipped while the words are unchanged and the filter has settled (no glide left in
  its coefficients or weights: it would write the same fields, so bit for bit; the proof's model still calls it every
  block, which proves it); a silent block (all 0) is not run once the filter has rung out (`smp_filter_ringing` false):
  its states cleared, the block stays 0 (the model mirrors this: below -102 dB). SAMPLE's sources unchanged.
- **Unicorn (2026-11-01)**: everything ok but the cost line, by design. New cost, declared: lowpass 922 (was 1 101),
  highpass 976 (1 165), centre 160 (50: the silent scan now runs before the off filter's early return), gliding 1 464
  (1 576), silent 176, first 1 492 (1 598). Six steady lowpasses 5 884 instructions (6 948).

## 18. The machine, measured (2026-11-01)

- On a measuring build with SAMPLE, Digital Delay, POTS, Samples, Control All Config, Trig Condition Order and Trig
  Preview: « 10,0 war das höchste » with all six tracks on a filter and Control All on Cutoff; « hakt nichts mehr ».
  Reading: six filters gliding are about 9 000 instructions by the emulator's count, 5.4 % at one cycle an
  instruction; 10 % on the machine means about two cycles an instruction (the EMAC's waits). With Samples 0.2 the UI no
  longer lags.
- Left for later, small: Samples at the centre (160 a track) could return before the silent scan when the filter is off
  (bit for bit, about 0.6 % for six tracks). Interleaving two tracks in the loop, or code and states in SRAM, are not
  needed for now.

## 19. T5, the card (2026-11-01)

- **Claims and composers** as in §6; `compose.fl_cost`; `composer.js`'s twins (`flLayer`, `flCost`, `narrowed`, the
  filter kind, R1, the chains); `web_package` passes `track.filter` and the cost, `web_part` the part's sites. The
  page's composer gives the same tweaks as `compose.py`, conflicts included, for Samples alone, with REFF, with SAMPLE
  before and after, with Digital Delay, and with every card.
- **The card**: `72-smpfilter.json` from `gen_smpfilter.py`; the composed tweaks of the folder regenerated (only
  "smpfilter" added to their conflicts); the card in `FEATURES` (experimental, credit Cycles One-Shot and its license),
  the Filters section, its texts and guide link; `REF_MAINOS` (29 combinations) and `REF_MODS`; `REGISTRY.md`,
  `PROVENANCE.md`.
- **The guide**: section 6, Samples filter (the following sections renumbered).
- **The smoke test** with both official OS files: ALL OK (the first run found its own credit count out of date).
- **`test_fltslot.py` on the final state, the maintainer's run (2026-11-01): ALL OK**, all seven selections, the cost line
  as declared, the refusals.

## 20. Tested on the machine (2026-11-01)

From the command line (builds of `tools/compose.py`), the maintainer: Samples alone, SAMPLE + Samples, Samples + REFF and
the full set with `fltslot` 0.4 (§15, §16): « passt alles soweit » (the type, Cutoff and Reso, p-locks with a held trig,
the LFO's destination once fixed, save and reload, SAMPLE next to it, the other cards); then the measuring build (§18);
then the normal builds with Samples 0.2: Samples alone (MAIN OS `76b47553…`) and every card (`449b7df8…`), the same MAIN
OS the page composes (`REF_MAINOS`). Experimental on the page until flashed from it.

## 21. What is left

- Samples' early return at the centre (§18).
- T7: Env depth and AD in Samples, under the same id (k 30, k 31, the trig bit).
- A second filter (the Modded-Cycles track filter could follow, with its envelope).
- The standard's text (§6), only on the maintainer's word.

## 22. Cutoff as on SAMPLE, CUTO for the LFO (2026-11-01, release 0.24)

The maintainer after 0.23: « "L64" und "H63" sieht nicht gut aus und besonders das L ist irreführend bzw leicht mit
PAN L zu verwechseln. einfach -64 und 63 nutzen wie beim SAMPLE », and as the LFO's destination « CUTO » rather than
« FREQ ».

- **`fltslot` 0.6**: `fl_fmt_cut` writes -64 .. -1 (the lowpass side), 0 (off), 1 .. 63 (the highpass side), as SAMPLE's
  `smp_fmt_cutoff` (`(word >> 8) - 64`, the same value for every word, fine steps included); a measuring build still
  shows the load there. 3 264 bytes of code.
- **Samples 0.3**: Cutoff's short name, which the LFO's destination shows, is CUTO.
- **The proof**: section 6 expects SAMPLE's 128 values; the normal build's Cutoff at the centre reads 0. Unicorn, the
  maintainer's run (2026-11-01): **ALL OK**, all seven selections.
- MAIN OS (`REF_MAINOS`): Samples alone `92f6955e…`, with SAMPLE `83801ea7…`, every card `e6a60aa3…`. The builds of
  §20 (`76b47553…`, `449b7df8…`) showed L64 .. OFF .. H63 and FREQ; only the display changed, not on the machine yet.

## 23. Tested from the page (2026-11-01, release 0.25)

The maintainer flashed a build of the live page (`fe96f39`, release 0.24, stamp 2026-11-01-02, the page's files compared
byte for byte with the commit) and tried Samples on their Model:Cycles: « passt ». The card is tested since release
0.25 (`FEATURES`, the guide's line, README).

## 24. The Track FX (2026-11-01)

The slot holds effects as well as filters since `fltslot` 0.7, four in a build, the type's row "Track FX"; the first
effect is Crush: [73](73-track-fx-crush.md).
