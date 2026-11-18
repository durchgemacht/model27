# 86 — VOSIM (working name): Braids' VOSIM oscillator with formant tracking and a decaying window (steps 1 and 2, 2026-11-18, English)

The maintainer's plan (notes/83, notes/85): machines after the Mutable Instruments engines the Cycles lacks. After a
listening page of the originals (outside the repository, `_scratch/plaits-listen/pd-vosim/`: « Hörproben sind gut »)
they chose VOSIM first, on Braids' code rather than Plaits' `VOSIMOscillator`. It follows the path of TERRA (notes/85):
(1) the fixed point on the host against the original, (2) the package, (3) the proof in Unicorn and the load, (4)
digiemu, (5) the device, (6) the card. All six are done (§3 to §12); the card is tested, flashed from the page (§13). Step 1's
programs, renders and listening page live outside the repository (`_scratch/vosim-machine/`, README there), step 2's
proofs next to them (`_scratch/vosim-machine/step2/`). The name is open; VOSIM is a working name.

Source: Mutable Instruments Braids by Émilie Gillet, MIT (eurorack `08460a6`, stmlib `e3bd7c9`):
`braids/digital_oscillator.cc` (`DigitalOscillator::RenderVosim`, `ComputePhaseIncrement`), `braids/resources.cc`
(`lut_bell`, `wav_sine`, `lut_oscillator_increments`) and stmlib's `Interpolate824`. Unlike TERRA, the oscillator is
**carried over integer for integer**: the same integer steps in C, and the three tables copied as they are by the
generator (LICENSE-Braids next to the package). The tracking, the window family and its level, and the DC stage are
model27's.

Adresses : VA de l'OS 1.13.

## 1. In short

- **What it does:** two sine formants (the second at half the level), windowed over each period of the note and
  restarted with it, as Braids' VOSIM model. Braids runs it at 96 kHz; the Cycles at 48 kHz with every phase step
  doubled, one point a sample.
- **The knobs** (the maintainer's decisions, §2): COLOR formant 1 (Braids' TIMBRE), SHAPE formant 2 (Braids' COLOR);
  the knob's value is the formant's MIDI note (69 = 440 Hz, 127 ≈ 12.5 kHz). SWEEP the formants follow the note: 0
  fixed as Braids, 127 fully (reversed for a test and back, §10), linearly in semitones, agreeing at C5 (MIDI 60), held below Braids' table end (13.3
  kHz). CONTOUR the window: Braids' bell at 0, then 16 steps towards an e-curve that falls by 24 dB over the period
  (the classic VOSIM: the formants fade within each period), the level made up (3.5 dB at the end).
- **The DC:** Braids' output carries the window's offset (window × 24 576 − 24 576, about −12 000 on average); the
  core takes out the mean of the last period, each sample weighted by its phase step (exactly zero for a steady
  sound, no high-pass settling after a note change).
- **Step 1** (§3): with SWEEP 0 and CONTOUR 0 the core is Braids' `RenderVosim` with doubled steps **bit for bit**
  (324 500 blocks, a trig as Braids' sync included); against a model in double at least 76.7 dB SNR; the pitch within
  0.003 cents. The listening page decided every point (§2); the last, whether a trig restarts the oscillator, on its
  card 10 (§6): it runs on, as Braids.
- **Step 2** (§4, §5): the package `tools/machines/vosim/` and `tools/gen_vosim.py`, composed alone into
  `87-vosim.json`; its core gives step 1's bits; the sample loop in ColdFire assembly (`vosim_cf.S`, kept: the same
  bits and 22 % fewer instructions a block than GCC's loop); the window family a far table (notes/85 §5). In a
  ColdFire interpreter, update + render 2 185 instructions a block at the defaults (TERRA, the same measure: 2 590).

## 2. The maintainer's decisions (2026-11-18)

| Point | Decision | Their words |
|---|---|---|
| The base | Braids' code, not Plaits' `VOSIMOscillator` | |
| Rate | 48 kHz, one point a sample | (« 1× ändert fast nichts », notes/85) |
| COLOR, SHAPE | formant 1, formant 2 (Braids' TIMBRE and COLOR, the second at half the level) | |
| SWEEP | the formants follow the note (step 1's card 2) | « passt » |
| The tracking's reference | C5 (MIDI 60): there SWEEP changes nothing, a fresh trig plays C5 (card 3) | « c5 » |
| The tracking's curve | linear in semitones (card 4) | « linear » |
| The ceiling | 13.3 kHz, Braids' table end (card 5) | « 13,3 » |
| The decaying end | an e-curve, 24 dB down at the period's end (card 6) | « -24 » |
| Bell → end | 17 steps, no mix between them (card 7) | « 17 stufen ist das günstigste nimm das » |
| The DC | the mean of the last period (card 8) | « mittel der periode » |
| The level at CONTOUR 127 | made up in the window's tables, no extra instruction (§3.3) | (main chat) |
| Assembly | tried; kept only when bit for bit and faster in the interpreter (§4.4) | (main chat) |
| A trig's restart | none: carrier and formants run on through a trig, as Braids without sync (card 10, §6); the restart stays an option at no cost | « durchlaufend » (main chat) |
| Name, knobs, defaults, picture | VOSIM, TONE's picture (4); Vosim F1 / FRM1 77, Vosim F2 / FRM2 86, Vosim Follow / TRCK 0, Vosim Window / WIND 0, DECAY 64 (§10) | « Voreinstellungen der Regler und Name kann so bleiben » (main chat) |
| The level | kept: Braids' full scale onto the bus as TERRA puts Plaits', TERRA's output stage; 5.3 LU below TONE at the defaults, no clipping without PUNCH (§8.1) | « So lassen » (main chat) |

## 3. Step 1: the core on the host (`_scratch/vosim-machine/`)

### 3.1 The arithmetic

Braids' loop as it is: the carrier phase and two formant phases (uint32), the formants from `wav_sine` (which starts at
its trough, so each period's pulses start at zero, as VOSIM's sin² pulses), the window from `lut_bell` (a rise over the
first sixteenth of the period, then a cosine fall), `sample = (24 576 + f₁/2 + f₂/4) × (bell >> 1) >> 15`, the formants
restarted and the sample 0 when the carrier wraps. The pitch: Braids' pitch `(note + 256) >> 9` (1/128 semitone),
`ComputePhaseIncrement` for 96 kHz, doubled. COLOR and SHAPE (8.8) are Braids' parameters as they are.

- **Interpolate824 on uint16:** stmlib computes it in uint32 and truncates to uint16; for a falling segment that gives
  a − ⌈d f / 2¹⁶⌉, which the signed form with an arithmetic shift gives too while (b − a) f fits in int32 (every window
  table steps by less than 2¹⁵; `lut_bell` by 6 622 at most). Its cast to int16 on `wav_sine` changes nothing (the
  result lies between two entries) and is left out.
- **The window's product** in unsigned arithmetic (both operands ≥ 0): the same bits as Braids' for the bell, and room
  for the level made up (§3.3).
- **The tracking:** formant = knob + t · (note − C5) in 1/128 semitone, t = SWEEP/127 in Q15 (`× 66053 >> 16`, 127 =
  1.0 exactly), clamped to 0 … MIDI 128 − 1/128. Off at SWEEP 0 (Braids' path).
- **The DC stage:** a sum of the windowed sample (one addition a sample); at each block's end the block's sum × its
  phase step / 2³² (one EMAC product, Q8) joins the period's mean; at the carrier's wrap that mean becomes the offset
  subtracted in the next period. Weighting by the phase step keeps a note change within a period bounded (without it,
  the sum of a long period times the new short step ran to 8 · 10⁶, found by the level check and fixed).
- **A trig's restart** (option, §6): Braids' sync on the block's first sample (the phase set so that it reads 0 there);
  the offset kept, since the restart ends no whole period.

### 3.2 The checks (`make.py`, « ALLES OK »)

| Check | Result |
|---|---|
| SWEEP 0, CONTOUR 0, no DC stage, against `RenderVosim` with doubled steps (`braids_vosim.h`, copied unchanged), 32 samples a block: every clip of the page, random notes up to 140 and knobs, the edges, a note and the knobs every block; 8 runs with trigs as Braids' sync | 36 runs, 324 500 blocks: **the same bits** |
| the core against a model in double of the same structure (window, mixes, computed ends, the 17 steps with their level, the four DC stages), the core's own steps | 48 combinations, at least 76.7 dB SNR |
| the tracking's formant frequency against the formula (linear, quadratic, linear in Hz; both ceilings) | within 0.77 cents |
| carrier and fixed formants from the steps, notes 0 … 127 | within 0.003 cents |
| the ColdFire object in the interpreter against the host core, every cost case | the same bits |

### 3.3 The level made up

The decaying windows hold less energy than the bell: at CONTOUR 127 about 3.5 dB less (RMS, the listening page's card 6).
A model of one period averaged over formant settings shows the loss growing almost exactly linearly over the 17 steps
(0.31 dB a step). So step j's table is stored at half scale (as Braids' `Interpolate824(...) >> 1`) and times
10^(3.5 j / 16 / 20): at most 49 030, interpolated with 15 bits of the phase and no shift after. The bell (j = 0) keeps
Braids' path. No instruction more: the same loop reads another table.

### 3.4 The level

Braids' scale (int16 full scale 32 768): without the DC stage the output is Braids' (peak −2.5 dB under int16); after
it the signal swings round zero, its largest value over every clip and check +3.5 dB over int16, +4.6 dB with the level
made up (55 654); over a grid of steady settings (§8.1) +5.3 dB (60 143, COLOR and SHAPE 127,
CONTOUR 127, note 36).

### 3.5 The listening page

`_scratch/vosim-machine/index.html`, 90 WAVs: (1) Braids at 96 kHz against the core, (2) SWEEP 0 … 127, (3) the
reference note, (4) the curve, (5) the ceiling, (6) the decaying end at CONTOUR 127 (each level-matched to the bell),
(7) bell → end: two tables mixed, a family of 9 mixed, 17 steps, a mixed table a block, (8) the DC stages, (9) the cost
and the proof, (10) a trig's restart (§6).

### 3.6 The load of the variants (interpreter, the core alone, C, instructions a block)

| Choice | median |
|---|---|
| Braids' path (CONTOUR 0, SWEEP 0, no DC stage) | 2 490 |
| SWEEP above 0: linear or quadratic / linear in Hz | +20 / +120 |
| the DC: the period's mean / a one-pole high-pass a sample / a fixed offset | +110 / +318 / −31 |
| CONTOUR between: two tables mixed / a family of 9 mixed / 17 steps / a mixed table a block (moving) | +705 / +812 / ±0 / ±0 (+2 837) |
| the decided set (17 steps with their level, the period's mean) | 2 606 … 2 695, also with CONTOUR moving |

## 4. Step 2: the package (2026-11-18)

### 4.1 Files

| File | What |
|---|---|
| `tools/machines/vosim/vosim.c` | step 1's core with the chosen variant only, `VOSIM_RESET` (the trig's restart: 0, decided; 1 an option), its host entries under `VOSIM_HOST`, the glue for the voice loop |
| `tools/machines/vosim/vosim_cf.S` | the sample loop in ColdFire assembly, the bell's and a step's (§4.4) |
| `tools/machines/vosim/vosim_tables.h` | generated: Braids' three tables, the bell's mean, `FAM_H` (the 16 steps, a far table on the device) |
| `tools/machines/vosim/vosim.o` | the committed object (`ld -r`, m68k-elf-gcc 16.2) |
| `tools/machines/vosim/manifest.json` | machine `VOSIM`, TONE's picture (4) until it has its own, DECAY 64; knobs Vosim F1 / FRM1 77, Vosim F2 / FRM2 86, Vosim Follow / TRCK 0, Vosim Window / WIND 0 (names, defaults and picture decided, §2, §10); no claims; order 87 |
| `tools/machines/vosim/LICENSE`, `LICENSE-Braids` | MIT (model27), Braids' MIT notice with what was taken |
| `tools/gen_vosim.py` | the tables (Braids' from `resources.cc` with `--braids`, else kept, checked against their SHA-256 at `08460a6`; the family computed, checked against its SHA-256), the object, with `--cycles` the composed tweak `87-vosim.json` |

The 20 other composed tweaks regenerated by their generators: each gained the conflict `vosim`, nothing else changed.
`gen_sampler.py` could not run since notes/85 §5 (`compose.place_package` returns the far tables as a fourth value): it
takes them now, and refuses one (SAMPLE has none); its output is unchanged but for the conflict. `REGISTRY.md`
regenerated.

### 4.2 The glue

As TERRA's (notes/85 §4.2, §9): one voice and one set of inputs a track in the package's variables; `vosim_update`
sets up the stock amp chain as TONE does (DECAY through `LUT_DECAY`, the envelope's and PUNCH's words in the block of
`+0x38`), computes the note as every machine (the trig's note + PITCH − 64 + FINE), reads COLOR / SHAPE / SWEEP /
CONTOUR, with `VOSIM_RESET` 1 also a trig from `+0x38` (the block where the envelope starts, as CHIPS; with 0 not
even read), and makes a fresh voice when the
track took the machine (the mark `VOS1` at `+0x2c`); `vosim_render` pauses while the envelope is closed and no trig
comes (out 0, the voice stands still), else saves MACSR, runs the core onto the bus, then AMP_ENV, the VCA without the
trig's flags (notes/85 §9) and PUNCH, and gives MACSR back.

### 4.3 The level (measured in §8.1, kept: the maintainer, 2026-11-18)

TERRA's output stage: `+0x2a4` = `0x7fffffff` (TONE's × 4), the core onto the bus << 14 (Q29: Braids' int16 full scale
a quarter of the bus, where TERRA puts Plaits' full scale), so Braids' full scale is a TONE voice at full scale − 18
dB. After the DC stage the peaks reach about 1.8 of that (+5.3 dB, §3.4), 6.8 dB under the bus's full scale; PUNCH's
drive (× 3) saturates from 1.33 of it, so PUNCH will clip VOSIM's peaks more often than TERRA's. To be measured in
step 3 and decided by the maintainer.

### 4.4 Assembly, kept

`vosim_cf.S`: the two forms of the sample loop (the bell, a step of `FAM_H`), called by `vosim_block` on the device
(`VOSIM_ASM` 1); the host builds the C loop. The carrier's phase in an address register frees a data register for the
output's shift; the entry and the fraction of each interpolation from one shift and a `swap` (`mvz.w` both halves);
the products in `muls.l` / `mulu.l` as in C, the DC stage's two through the EMAC as `mul()`. 58 instructions a sample
against GCC's 77 (GCC spills two steps and three temporaries); a block of update + render 2 185 against 2 793. Bit for
bit: the interpreter compares every block with the host's C (§5).

## 5. Step 2's proofs (`_scratch/vosim-machine/step2/`)

| Proof | Result |
|---|---|
| `same_bits.py`: the package's core (host, Braids' scale) against step 1's core in the chosen variant, without and with the restart, on every input of the listening page (trigs every sixteenth) and 40 random sequences (knobs held, moved, out of range, notes, trigs) | 260 runs, 1 576 200 blocks: the same bits |
| `cf_object.py`: the committed object (and the same source with `VOSIM_RESET` 1, and both with the C loop) linked with stand-ins for AMP_ENV, VCA and PUNCH, the far table at `0x43040000`, run in the ColdFire interpreter as the voice loop calls it, six tracks × 400 blocks with random knobs, notes, PITCH, FINE and trigs, against the host core (Q29) | ALL OK (68 checks): every block equal; MACSR given back; DECAY in `+0x250`; PUNCH's words as TONE's, `+0x2a4` `0x7fffffff`; the pause; a trig while paused runs the core; a fresh voice after the mark is cleared; the VCA without the trig's flags, PUNCH with them |
| `tools/gen_vosim.py --check` | tables and object up to date |
| `compose.py --compare-ld` (the relocator against the linker): VOSIM alone, after and before SAMPLE, after SOLID, CHIPS, Max Saw and TERRA | identical |
| `compose.py`: the largest sets that compose (§7: SAMPLE, SOLID, CHIPS, Max Saw, TERRA, VOSIM and every effect, Track FX, CPU, RESAMPLE, Transpose, Perform Kit; or without Max Saw and with CHORD Tables) | ok, the payload ends at `0x43178850` / `0x43178a84` |
| without firmware: `claims.py --check --self-test`, `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check` | ok |

VOSIM alone: machine 6, code and tables 3 406 bytes at `0x43000000`, the far table and variables 8 560 bytes at
`0x43036000`, payload `0x43000000..0x43038170`, 17 360 bytes added to the image, MAIN OS 1 761 552 bytes, SHA-256
`4796c93f…`; after SAMPLE `9b40a8e3…`, before it `26c9acc8…`. In the code window VOSIM takes 3.4 KiB (TERRA left 10.3 KiB free next to every offered card).

Cost in the interpreter, update + render without the OS's chain, instructions a block (as decided, the restart off;
with it within +30):

| Setting (note 60) | C loop | `vosim_cf.S` |
|---|---|---|
| the defaults (COLOR 77, SHAPE 86, SWEEP 0, CONTOUR 0) | 2 793 | 2 185 |
| SWEEP 64 / CONTOUR 64 / CONTOUR 127 / both 64 | 2 808 / 2 799 / 2 799 / 2 814 | 2 200 / 2 188 / 2 188 / 2 203 |
| COLOR and SHAPE 0 (the pitch's longest loop) | 2 845 | 2 237 |
| random settings: median (least, most) | 2 814 (2 626, 2 897) | 2 227 (2 167, 2 299) |
| paused | 167 | 167 |

## 6. A trig's restart (listening card 10): runs on, decided (2026-11-18)

`VOSIM_RESET` 1: a trig restarts carrier and formants (Braids' sync), every note starts the same; 0: they run on (as
Braids without sync, as TERRA), each note starts where the period stands. Both proven (§5). The listening page's card
10 plays both with the decided variant and an envelope like the stock one (a block's rise at the trig, then each block
the Cycles' own factor for DECAY, `LUT_DECAY` read from the official file for the page only, the VCA ramped over each
block): the restart makes the wave jump at a trig on a sounding note, the largest step there 2 469 / 13 432 / 5 980 /
4 182 (16 bit) against 978 / 1 276 / 1 428 / 1 345 running on (bass DECAY 30, melody DECAY 70, quarters DECAY 127,
quarters CONTOUR 127). **Decided** (the maintainer, 2026-11-18, through the main chat): « durchlaufend », no restart,
as Braids without sync. `VOSIM_RESET` stays 0; with 0 the glue does not even read the trig (28 bytes and 5
instructions a block less), so the option costs nothing and stays in the source.

## 7. Open `[À FAIRE]`

- The name, the knobs' names and defaults and the picture (TONE's, « das Bild kannst du benutzen »): decided (§2, 2026-11-18).
- ~~Seven machines~~: the dispatchers hold eight since 2026-11-18 (§11, notes/63 §33).

## 8. Step 3: the proof on the OS's own code (prepared 2026-11-18)

`tools/emu/test_vosim.py` and `tools/emu/vosim_ref.c`, after test_terra.py (notes/85 §7), the maintainer's « Ja,
Schritt 3 »:

| Part | What it checks |
|---|---|
| startup | the bootstrap and the boot hook, the registrar's tables, lookups, MACHINES page, records and knobs (as test_compose.py); the far table (FAM_H, 8 224 bytes) at the start of VOSIM's variables' room, above the code window, byte for byte the package's after the boot hook's copy |
| core | at every block not paused, what `vosim_render` gives AMP_ENV = the host core (`vosim_ref.c`: vosim.c's C loop against the device's `vosim_cf.S`, Q29), fed the inputs computed from memory: COLOR and SHAPE across their range, SWEEP at six notes away from C5, CONTOUR on the bell and every step, notes 0–127, PUNCH, PITCH, FINE, DECAY, GATE, retrigs, every knob moving every block; the pause and the wake; the chain called once each in order |
| inputs | COLOR, SHAPE, SWEEP (at C4) and CONTOUR each change the sound; at C5 SWEEP changes nothing |
| chain | the envelope and the chain's words TONE's block for block (the level but in a trig's block), `+0x2a4` `0x7fffffff` (TONE `0x20000000`); PUNCH acts; a retrig on a sounding track at DECAY 127, 60 and 30: the VCA's gain never dips (one block more of the decay allowed, notes/85 §9) and never steps |
| tracks | a change of machine (VOSIM, TONE, VOSIM: a fresh voice); six tracks exact and as alone; VOSIM among KICK, METAL, PERC, CHORD; the stock machines without VOSIM identical to the stock OS, no instruction of VOSIM |
| next | next to SAMPLE, CHIPS, Max Saw and TERRA (machine 7; with TERRA two far tables): start-up, the track as alone, the stock machines unchanged |
| compare | loudness (BS.1770) and the fundamental against TONE, PERC, METAL, CHORD |
| measure | peak and RMS over 100 ms and 0.5 s next to the stock machines; instructions a block of one voice (the defaults, COLOR and SHAPE 0, SWEEP, CONTOUR 64 and 127, PUNCH, notes 24 and 96, each knob moving and all four), paused, six tracks against six TONE, the stack |

`--dry` (no Unicorn, run here, 2026-11-18): VOSIM machine 6 alone (code `0x43000000..0x43000d4e`, the far table and
variables 8 560 bytes at `0x43036000`), machine 7 next to SAMPLE (`0x43045520`), CHIPS (`0x430363e0`), Max Saw
(`0x43036344`) and TERRA (`0x43042780`, after TERRA's own far table); in each the far table in the payload as the boot
hook leaves it is the package's. The host core before the chain, the defaults: peak −13.2 dB, RMS −20.5 dB of the
bus; CONTOUR 127: −12.6 / −21.0 dB (the level made up holds within 0.5 dB). For comparison TERRA between surfaces 3 and
4 −12.1 / −14.9, Max Saw's defaults −9.5 / −20.9 (notes/85 §7, notes/84 §10). The Unicorn parts stop with SIGILL in
Claude's sandbox: the maintainer's run.

### 8.1 The maintainer's run (2026-11-18): ALL OK

Every part passes (the log, 218 lines: `_scratch/vosim-machine/step3-unicorn.log`): start-up and the registrar alone
and as machine 7 next to SAMPLE, CHIPS, Max Saw and TERRA (the MACHINES page shows `VOSIM` with TONE's picture; a
change of machine Chord → VOSIM gives the defaults 77, 86, 0, 0, DECAY 64); the far table at `0x43036000` alone
(`0x43045520` next to SAMPLE, `0x430363e0` next to CHIPS, `0x43036344` next to Max Saw, `0x43042780` next to TERRA),
byte for byte the package's after the boot hook's copy; the core exact in 92 cases, 12 626 blocks (vosim_cf.S on the OS
against vosim.c's C on the host); the pause (385 blocks) and the wake; the chain called once each in order; the inputs
act, at C5 SWEEP changes nothing; the chain TONE's block for block with `+0x2a4` `0x7fffffff`; PUNCH acts (peak −10.9
dB, without −19.4 dB); a retrig at DECAY 127, 60, 30: the lowest gain from the trig on 0.956, 0.794, 0.392 (at least
0.954, 0.792, 0.391), the largest step a frame 0.0014, 0.0064, 0.0190 (at most 0.0040, 0.0115, 0.0295); the tracks (a
change of machine, six tracks, mixed, the stock machines identical to the stock OS without one instruction of VOSIM);
next to the four machines the track as alone.

The cost, instructions a block of one voice (the voice loop less the muted loop), note 60, DECAY 127:

| Setting | median (most; the trig's block) |
|---|---|
| the defaults (COLOR 77, SHAPE 86, SWEEP 0, CONTOUR 0) | 2 910 (2 926; 3 324) |
| COLOR and SHAPE 0 (the pitch's longest loop) | 2 962 |
| SWEEP 64 at note 48 / CONTOUR 64 / CONTOUR 127 / both at note 48 | 2 933 / 2 913 / 2 913 / 2 936 |
| PUNCH on / note 24 / note 96 | 2 905 / 2 922 / 2 914 |
| COLOR / SHAPE / SWEEP / CONTOUR moving every block | 2 918 (2 942) / 2 922 (2 946) / 2 933 (2 953) / 2 917 (2 933) |
| all four moving every block | 2 948 (2 982) |
| paused | 183 |
| six tracks (CONTOUR 64) | 17 478 against six TONE 31 746 (0.55 ×) |

Stock: TONE 5 291, PERC 6 079, METAL 6 431, KICK 7 429, SNARE 7 158, CHORD 8 300; TERRA 3 325 at its defaults, Max Saw
4 791, CHIPS 1 672. VOSIM costs the same in every setting (the steps of CONTOUR read another table, nothing more), a
little over half of TONE; the stack 216 bytes below the voice loop.

The level, note 60:

| | peak / RMS 100 ms (dB) | loudness 0.5 s at DECAY 127 (LUFS, against TONE) |
|---|---|---|
| TONE | −18.1 / −24.1 | −22.8 (0) |
| PERC / METAL / CHORD | −15.1 / −27.0, −14.7 / −32.3, −22.4 / −30.7 | +1.1, +1.6, −7.7 |
| VOSIM, the defaults (COLOR 77, SHAPE 86) | −19.5 / −27.6 | −28.1 (−5.3) |
| COLOR 40 / COLOR 100 | −26.7 / −35.2, −18.5 / −27.8 | −12.6, −3.8 |
| SHAPE 60 / SHAPE 110 | −20.8 / −28.4, −17.7 / −27.6 | −6.2, −4.9 |
| CONTOUR 64 / CONTOUR 127 | −19.1 / −27.9, −18.8 / −28.1 | −5.5, −5.8 |
| COLOR and SHAPE 0 / 127 | −26.7 / −41.5, −17.2 / −26.7 | −28.8, −1.6 |
| PUNCH on | −10.9 / −24.3 | |
| note 36 with SWEEP 127 / note 96 | −19.2 / −27.5, −30.4 / −39.1 | |

The fundamental 261.6–261.7 Hz (note 60.0) as TONE's in every setting but COLOR and SHAPE 127 (132.2 Hz: the
autocorrelation takes a sub-octave there). CONTOUR 127 is within 0.5 dB of the bell: the level made up holds (§3.3).
VOSIM's peaks are TONE's within 1.4 dB, its loudness 5.3 LU below TONE at the defaults: its pulses have a crest factor of
8.1 dB against TONE's 6.0. Low formants are much quieter (COLOR 40: −12.6 LU; COLOR and SHAPE 0, formants near 8 Hz:
almost silent).

**The headroom**, the core onto the bus, PUNCH's drive saturating above a third of the bus (x × 4 × `+0x2a0`, on × 3,
notes/84 §9.3), over 630 settings (COLOR and SHAPE 40 … 127, CONTOUR 0 / 64 / 127, notes 36 … 84; the loudest core peak
60 143 in Braids' scale, +5.3 dB over int16, at COLOR and SHAPE 127, CONTOUR 127, note 36):

| Gain | loudness at the defaults against TONE | headroom without PUNCH: defaults / worst | with PUNCH: defaults / worst | settings past PUNCH's limit | cost |
|---|---|---|---|---|---|
| as it is (`<< 14`) | −5.3 LU | 13.4 / 6.8 dB | 3.8 / −2.8 dB | 51 of 630 (all at CONTOUR 127 with formants from 90) | 0 |
| + 3.5 dB (`<< 14` + `<< 13`) | −1.8 LU | 9.9 / 3.3 dB | 0.3 / −6.3 dB | 322 of 630 | 2 instructions a sample (≈ 64 a block) |
| + 6 dB (`<< 15`) | +0.7 LU | 7.3 / 0.7 dB | −2.2 / −8.8 dB | 442 of 630 | 0 |

Proposed: keep it, as Max Saw (4.9 LU below TONE, « Keep it », notes/84 §13): no clipping anywhere without PUNCH,
with PUNCH only the brightest decaying windows touch its limit briefly (at most 2.8 dB); a track is raised with its
Track Level or Volume as usual. Louder means the peaks go above TONE's and PUNCH clips most settings.

**The level, decided** (the maintainer, 2026-11-18, through the main chat: « So lassen »): kept as it is.

## 9. Steps 4 and 5: one full build for digiemu and the device (2026-11-18)

The maintainer: one build for both, as Max Saw's (notes/84 §14), every OFFERED card and VOSIM, **without CHIPS**: with
it the build would hold six added machines and CHORD Tables, seven entries in the tables by machine, and the dispatchers
hold six (§7). Always with the CPU page (notes/85 §8).

    python3 tools/compose.py --cycles firmware/model-cycles_OS1.13.syx \
        --machines sampler,solid,maxsaw,terra,vosim,chordtables,digidelay,pots,smpfilter,crush,ring,reso,eq \
        --cpu --resample --transpose --perform --with control-all-config,trig-cond-order,trig-preview \
        --tool ../elektron-firmware-tool-main/elektron-firmware-tool

SAMPLE machine 6, SOLID 7, Max Saw 8, TERRA 9, **VOSIM 10** (code 3 406 bytes at `0x43014d78`, the far table and
variables 8 560 bytes at `0x43152c78`); payload `0x43000000..0x431789e8`, 260 120 bytes added to the image; MAIN OS
2 004 312 bytes, SHA-256 `ad1d7f302fad5d45f283b00bf325d6e43b7b4506bd010a512664d9bed1234cac`; elektron-firmware-tool:
checksums and HMAC ok, the same MAIN OS. The file, outside the repository:
`_scratch/vosim-machine/build/full-0.1/model27-vosim-full-0.1-cpu.syx` (1 139 104 bytes, SHA-256
`8a276a1275ec2cf861e77e1a3effb3f0c9c15a2899bc8769b95ee286073e1700`; digiemu's folder `mc-1.13-8a276a12`).

Without CHIPS the machines after SAMPLE and SOLID move up one number against the page's full build (Max Saw 8 instead
of 9, TERRA 9 instead of 10): a sound saved with one of them in that build plays another machine in this one.

## 10. On the device; SWEEP reversed (2026-11-18)

The maintainer on the device with `model27-vosim-full-0.1-cpu.syx` (§9): « sound ist gut ». Two findings:

- **The knobs' names on the popup's second line:** COLOR and SHAPE show only « Formant » (« Vosim Formant 1 » and « 2 »
  cut), « Tracking » fits but looks squeezed: seven characters is the limit that still looks right, eight fit. The
  popup breaks a long name at every space (notes/71 §10), so « Vosim Formant 1 » became « Vosim », « Formant » and a
  third line out of sight: the second line must be one word of seven characters at most. Proposed Form1 / Formnt1 / F1
  / Fmt1 and Track / Follow / KeyTrk; the maintainer chose **F1, F2, Follow** (Window stays): the long names « Vosim
  F1 », « Vosim F2 », « Vosim Follow », « Vosim Window »; the short names FRM1, FRM2, TRCK, WIND unchanged.
- **SWEEP reversed:** « wäre es aufwändig die skala von tracking umzukehren? glaube es würde sich besser anfühlen, wenn
  0 tief klingt und 127 hoch. kennt man vom filter … nichts ändern außer das verhalten des knobs umdrehen ». Below C5
  (where most notes are) more tracking lowers the formants: now SWEEP 127 is no tracking (as Braids) and 0 full
  tracking, so turning it up brightens the sound there, as a filter's cutoff. In `vosim.c` the tracking's amount is
  `knob_q15(127 << 8 − SWEEP)`, one subtraction a block; nothing else changed, the knob's default stays 0 (now full
  tracking; at C5, a fresh trig's note, the same sound either way). Step 1's core and its page keep the old direction:
  `same_bits.py` feeds it 127 − SWEEP (the same expression, clamped in both): 260 runs, 1 576 200 blocks, the same
  bits; `cf_object.py` ALL OK; `gen_vosim.py --check`, `registry.py --check`, `check_overlaps.py`, `claims.py`,
  `gen_flasher_tweaks.py --check`, `compose.py --compare-ld`, `test_vosim.py --dry`: ok. Code 3 412 bytes (6 more); in the
  interpreter the defaults now take the tracking's path, 2 201 instructions a block of update + render (2 185 before; at
  SWEEP 127, Braids' path, as before). With SWEEP 127 and CONTOUR 0 the core is Braids' `RenderVosim` (before: SWEEP 0).
  `test_vosim.py` (Unicorn) runs the same source on both sides and is not affected in what it checks; a run of
  `--only core,inputs` would confirm the object.
- The build: as §9, `_scratch/vosim-machine/build/full-0.2/model27-vosim-full-0.2-cpu.syx` (SHA-256
  `f6a980f4040b73d9c4bfae10ff6b2a98bc2fda7c8d0c05d2fc31f6fb6bc6d272`), MAIN OS 2 004 316 bytes, SHA-256
  `87ec8603d708adb4daa99a78d9ebe56da64a2922ed787110a48469621681d51e`, checksums and HMAC ok; VOSIM machine 10.
- With the new names (the tweak 16 bytes shorter, the code unchanged; `gen_vosim.py --check`, `registry.py --check`,
  `check_overlaps.py`, `claims.py`, `gen_flasher_tweaks.py --check`, `compose.py --compare-ld`, `cf_object.py`: ok):
  `_scratch/vosim-machine/build/full-0.3/model27-vosim-full-0.3-cpu.syx` (SHA-256
  `0fccf6c78ce68439a49dc4c6d119c545400f9be94e48c7fe357578969cff9966`), MAIN OS 2 004 300 bytes, SHA-256
  `484519f255a56d732b3658c0dcad3456e109093b7153bb08bd3bf00a847955f4`, checksums and HMAC ok; VOSIM machine 10.
- **On the device** (the maintainer, 2026-11-18, 0.3): « am gerät getestet, passt »: the names F1, F2, Follow, Window on the popup and SWEEP reversed.
- **SWEEP back** (the maintainer, 2026-11-18: « namen sind gut so. mach das mit dem reglerweg wieder rückgängig »): 0 fixed as
  Braids, 127 fully, as in §1; `vosim.c` and `same_bits.py` as before the reversal, the names kept. Code 3 406 bytes,
  the defaults 2 185 instructions a block of update + render; `same_bits.py` (260 runs, 1 576 200 blocks) and `cf_object.py`
  ALL OK; `gen_vosim.py --check`, `registry.py --check`, `check_overlaps.py`, `claims.py`, `gen_flasher_tweaks.py --check`,
  `compose.py --compare-ld`: ok. The build: `_scratch/vosim-machine/build/full-0.4/model27-vosim-full-0.4-cpu.syx` (SHA-256
  `ccee431958b31ade629583f466937354e490acf13758aff41893f5773710119d`), MAIN OS 2 004 296 bytes, SHA-256
  `af97cd4819008d81753c6642e14202014bea22397c7dc12eb39d355dfafb79f7`, checksums and HMAC ok; VOSIM machine 10.

## 11. Every offered card with CHIPS and VOSIM: the dispatchers to eight (2026-11-18)

The maintainer: raise the dispatchers' limit from six to eight (notes/63 §33), so that the six added machines and CHORD
Tables (seven entries) compose together. Done in `tools/machines/dispatch/` (0.4); the registrar stays at six added
machines (seven comes with PD). `webcompose_check.sh` identical with the full set with CHIPS and VOSIM; eight laid out,
nine refused.

The full build, every OFFERED card with CHIPS and VOSIM, with the CPU page (as §9 plus `chips`):
SAMPLE 6, SOLID 7, CHIPS 8, Max Saw 9, TERRA 10, **VOSIM 11**; the dispatchers' block 164 bytes; MAIN OS 2 012 644
bytes, SHA-256 `8136b1bec005d722fc1ff3d280b1db02fea558ad17746ff59a59c12abe9adc78`, checksums and HMAC ok;
`_scratch/vosim-machine/build/full-0.5/model27-vosim-full-0.5-cpu.syx` (1 145 504 bytes, SHA-256
`ed994defef739f338a44b80545ded9b8e8f41033a8a3affd2d73045f1ff99605`). The machines' numbers are again the page's full
build's (CHIPS 8, Max Saw 9, TERRA 10), VOSIM after them.

**On the device** (the maintainer, 2026-11-18, 0.5): « am gerät getestet, passt »: it starts, every machine can be chosen, CHIPS and VOSIM sound. The Unicorn proofs of dispatch 0.4 (`test_views.py`, `test_compose.py`, `test_chordtables.py`): ALL OK (notes/63 §33).

## 12. Step 6: the card (2026-11-18)

The maintainer: « schritt 6, danach commit », after release 0.74 (another session's) was committed. As TERRA's card
(notes/85 §10):

- `tools/gen_flasher_tweaks.py`: the FEATURES entry `vosim` after `terra` (cat `sound`, credit « based on » Émilie
  Gillet, `pichenettes/eurorack`, license `LICENSE-Braids`, package `vosim`, `experimental`) and OFFERED;
  `tweaks/model-cycles_OS1.13/LICENSE-Braids`, served as `docs/flasher/LICENSE-Braids.txt`, names VOSIM next to MACRO;
  `tweaks.js` regenerated (twenty-one cards).
- `docs/flasher/app.js`: `GUIDE_OF.vosim`, `FEAT.vosim` (label, `credit_name` Braids, the short, a block per knob in
  the user's words: COLOR and SHAPE the formants by their note, SWEEP how far they follow the note, CONTOUR the
  window), the credits' Émilie Gillet line extended; REF_MAINOS and REF_MODS regenerated.
- The guide: section 8 VOSIM (the steps, the knobs' table with the names on screen, Sound, Level from §8.1, Load,
  Other mods, Tested), the later sections renumbered, VOSIM in every other card's list; the home page lists it
  (`12 VOSIM / FORMANTS`); release 0.75 (VOSIM, and every machine card ticked together, §11); the stamps
  2026-11-18-03; README (twenty-one cards), BUILD.md (section « Machine VOSIM », the MAIN OS: VOSIM alone
  `8d398d8d…`, with SAMPLE `44388c48…`, with every card of the page `8136b1be…`), PROVENANCE, AGENTS.md.
- `tools/webflash_smoke.js`: the twenty-one cards and rows, VOSIM in Machines, its credit and license, alone, with
  SAMPLE and with SOLID, CHIPS, MAXSAW, TERRA, CHORD Tables, Crush and Transpose (seven entries in the dispatchers),
  every card together, its tag Experimental. `tools/webcompose_synth.py` has VOSIM's selections since §11.

The card stays experimental until it is flashed from the page (§13).

## 13. Flashed from the page: tested (2026-11-18)

After the commit of the card (`08b8ed8`), the maintainer flashed release 0.75 from the page, served locally with every
card ticked, onto their Model:Cycles: « ich habe vosim von der seite geflasht, passt ». Before, every offered card with
CHIPS and VOSIM from the command line (§9 to §11). The card's status tested (`gen_flasher_tweaks.py`, `tweaks.js`): no
tag; the guide's line Tested, the release entry without « experimental », BUILD.md, PROVENANCE, AGENTS.md, the
manifest (`tests.hardware`, tested), notes/README, CHANGELOG.md, `webflash_smoke.js` (the card without a tag); the stamp
2026-11-18-04 on the six pages.
