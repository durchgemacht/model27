# 84 — Max Saw (MAXSAW; working title Ultra Saw): seven sawtooths after Adam Szabo's analysis of the Super Saw (step 1, 2026-11-16, English)

The maintainer's request (2026-11-16): next to the Syntakt's SY SWARM, model27's SWARM (notes/82, after Plaits'
granular `SwarmEngine`) is a different instrument; asked whether SY SWARM is Plaits (it is not, §2), the maintainer
chose a machine of model27's own: « dann baue das auf der grundlage von Adam Szabos », working title « Ultra Saw ». It
follows the path of SOLID, SWARM and CHIPS: (1) the fixed point on the host against a float reference, (2) the
package, (3) the proof in Unicorn and the load, (4) digiemu, (5) the device, (6) the card, the guide, the release.
Step 1 is done; its programs, renders and listening page live outside the repository (`_scratch/ultrasaw/`).

## 1. In short

- **Source:** Adam Szabo, *How to Emulate the Super Saw*, BSc thesis, KTH (Royal Institute of Technology),
  Stockholm 2010, TRITA-CSC-E 2010:131, <https://www.adamszabo.com/internet/adam_szabo_how_to_emulate_the_super_saw.pdf>.
  He measured the Super Saw from recordings of the synthesizer and published the model as numbers and formulas; he states that
  no code or copyrighted technique from the synthesizer was used. Max Saw takes the model (facts and formulas), not
  text or code; the code is model27's own (MIT), the numbers are computed from his formulas by our generator.
- **The model** (§3): seven naive sawtooths, the centre at the note, six at Szabo's offsets times his 11th-degree
  detune curve; the centre's and the side oscillators' gains from his two mix polynomials; the sum through a high-pass
  at the fundamental; a random phase for every oscillator at each trig.
- **Step 1** (§5): the fixed point against the same model in double: the first 2 048 frames 80–145 dB apart, the
  third-octave spectrum of every clip within 0.5 dB, the pitch within 0.0045 cents; the ColdFire object equal to the
  host bit for bit in a ColdFire interpreter. C compiled by GCC: 3 524 instructions a block (interpreter's count, the
  core alone; SWARM's C core 4 309).
- **Step 2** (§9, 2026-11-16): the package `tools/machines/maxsaw/` and `tools/gen_maxsaw.py`, composed alone into
  `85-maxsaw.json` and next to SAMPLE, SOLID, CHIPS and the whole build; the committed object equal to the host core
  in a ColdFire interpreter as the voice loop calls it; about 4 060 instructions a block of update + render in C.
- **The maintainer's decisions** (§7, 2026-11-16): naive sawtooths and the 2-pole high-pass; COLOR Detune, SHAPE Mix,
  SWEEP Tone (the high-pass's cutoff against the fundamental), CONTOUR Phase (the random phases' width at a trig),
  MACHINES + PUNCH Sub (the centre two octaves lower, §8). Voices (fewer sawtooths) is kept in mind for the load later.
  After the listening page (§8): « passt alles, hört sich gut an ».

## 2. SY SWARM on the Syntakt is not Plaits [FAIT]

Read in the Syntakt OS 1.42's audio program (section 7, the same as 1.41), engine 10 (update `0x400092ec`, render
`0x400096e8`, Modded-Cycles notes/22): seven sawtooths from band-limited tables, one per octave (`0x40006588` picks
them by note, `0x40006434` reads them with linear interpolation); a centre (SUB moves it down 0, 1 or 2 octaves) and
six detuned through six tables indexed by DET; ANIM, three slow sine oscillators (about 1, 2 and 5 Hz, `0x40006074`)
that phase-modulate the oscillator pairs in opposite directions; NMOD, a noise generator (`0x40003eb4`) that
phase-modulates the six; MIX, two gain tables; a random phase per oscillator at a trig. **Its six detune tables are
Szabo's offsets times his detune polynomial, to 0.000 cents over all 128 × 6 values**; its mix curves are not his.
Nothing of the Syntakt is used in Max Saw; the comparison only showed which model Elektron followed for the detune.

## 3. Szabo's model [FAIT, read in the thesis]

| Part | Szabo | Page |
|---|---|---|
| Oscillators | seven sawtooths; osc 4 the centre at the played frequency, three above, three below | 7 |
| Offsets | frequency = centre × (1 + offset × detune): −0.11002313, −0.06288439, −0.01952356, 0, +0.01991221, +0.06216538, +0.10745242 | 9 (table 1) |
| Detune curve | x = knob / 127; y = 10028.7312891634 x¹¹ − 50818.8652045924 x¹⁰ + 111363.4808729368 x⁹ − 138150.6761080548 x⁸ + 106649.6679158292 x⁷ − 53046.9642751875 x⁶ + 17019.9518580080 x⁵ − 3425.0836591318 x⁴ + 404.2703938388 x³ − 24.1878824391 x² + 0.6717417634 x + 0.0030115596 (fitted to 17 measured points, `polyfit`) | 11–12 |
| Mix | x = knob / 127; centre = −0.55366 x + 0.99785; each side = −0.73764 x² + 1.2841 x + 0.044372; equal at about 95 | 15 |
| Shape | plain sawtooths, not band-limited: the aliasing is part of the sound; after the sum a high-pass at the fundamental, pitch-tracked, removes what folds below it | 16–19 |
| Phase | free running: each note trigger gives every oscillator a random phase, static while the note is held (an LFO on the phase gave artifacts) | 20–22 |

Not in the thesis: the high-pass's order and kind, the synthesizer's internal sample rate (his recordings were 44.1 kHz).

Two properties of the published curve, kept as published: y(0) = 0.0030 (at knob 0 the outer oscillators are 0.6 cents
off, not 0), and a small dip between knob 4 and 6 (0.0099 → 0.0098, 0.07 cents at the outermost oscillator).

## 4. Our choices where Szabo leaves it open (step 1)

- Pitch as on every Cycles machine: note 69 = 440 Hz at 48 kHz; the note, detune and mix read once a block of 32
  frames; the gains ramp across the block, the frequencies step; a trig sets the gains at once.
- The high-pass at the centre's fundamental (the note, clamped to 0–128; the cut at most 0.45 × 48 kHz). Step 1 has three
  variants (`USAW_HPF`): none, one pole (TPT), 2-pole state-variable (TPT, Butterworth, k = √2), the default.
- The sawtooth naive (`USAW_BLEP 0`, Szabo) or with a polyBLEP (`1`, SWARM's, notes/82), for comparison.
- Output Q27 (a single sawtooth at gain 1 = 1.0, as SWARM's); the level against TONE is step 2's.

## 5. Step 1: the core on the host (2026-11-16)

`_scratch/ultrasaw/`: `ultrasaw.c` (the core, one file for device and host, `USAW_HOST`), `gen_ultrasaw.py` →
`ultrasaw_tables.h` (offsets, the detune curve and the two mix curves at 0–127 plus a guard, the high-pass
coefficients at notes 0–128, `EXP2_T`; 5.5 KB with code), `ref/szabo_ref.c` (the same model in double, his polynomials
evaluated exactly, the filters with exact `tan`), `compare.py`, `bench.py`, `page.py` + `index.html` (the listening
page: 1 fixed point against the reference, 2 the high-pass's three kinds, 3 naive against polyBLEP), `run.sh`.

| Measure | Result |
|---|---|
| fixed point against the double reference, first 2 048 frames | 80–145 dB (naive saws 116–145, polyBLEP 80–104: its time in Q15) |
| third-octave bands of whole clips (bands within 60 dB of the loudest) | within 0.52 dB; without a high-pass at note 84, 2.65 dB in the aliasing below the fundamental, which moves with the smallest pitch difference |
| the seven increments against exact, every ¼ semitone of note 0–127 and every 3rd detune | within 0.0045 cents |
| the ColdFire object (m68k-elf-gcc 16.2, -O2) against the host build in `_scratch/cfemu` | the same bits, all four variants, with ramps and trigs |
| instructions a block (C, the core alone, interpreter) | 3 524 (2-pole), 3 090 (one pole), 2 712 (none), 5 852 (2-pole + polyBLEP); a trig +48 |

Over seconds the two renders drift apart by single samples at the naive sawtooths' drops (a pitch difference of
thousandths of a cent moves a drop by a frame), so the long clips are compared by spectrum, not sample for sample.

The C loop keeps the seven phases in memory; an assembly loop with the phases in registers (about 20 instructions a
frame for the sawtooths, plus the high-pass) is the next saving, as SWARM's was (notes/82 §6.3). [À FAIRE]

## 6. Open [À FAIRE]

- Step 3 (§9.6): the proof on the OS's own code (Unicorn), the level against TONE, the load.
- Step 2 is done (§9): the package, the stock amp chain (DECAY, GATE, PUNCH), the trig with the stock VCA's cut kept
  (the random phases jump there, unlike SWARM's, notes/82 §6.5).
- The name, and the machine's name on the device (`USAW` for now): « Ultra Saw » is a working title; no maker's or synthesizer's name in it. Decided in §15.

## 7. The maintainer's decisions and three more controls (2026-11-16)

After the listening page's cards 2 and 3: **naive sawtooths and the 2-pole high-pass** (« Naive, 2-pole HP »), the
core's defaults; the one-pole and polyBLEP stay compile-time switches of the scratch core only. The knobs, in the
maintainer's words: Tone « welches ja ein cutoff ist, auf sweep; das ist gelernt das dort genau solche params liegen »;
Sub « über [machines]+punch (damit lassen sich nur 2 stufen realisieren, aber das ist ok, entscheidung welche nach
hörtest) »; Voices « behalten wir im blick, ist dann vermutlich ein guter kandidat später wenn es an die performance
optimierung geht ».

| Control | What it does in the core | Cost |
|---|---|---|
| COLOR Detune | Szabo's curve (§3) | — |
| SHAPE Mix | Szabo's two curves (§3) | — |
| SWEEP **Tone** | the high-pass's cutoff note = the centre's note + 0.75 semitones × (Tone − 32): 16 steps an octave, at 32 Szabo's (the fundamental), at 0 two octaves below, at 127 about 5.9 octaves above (capped at 0.45 × 48 kHz); the tables cover cutoff notes −36 to 140 | once a block |
| CONTOUR **Phase** | a trig's seven phases = the random numbers (int32) × Phase / 127 of a cycle, around phase 0 (the sawtooths' middle, rising): 127 Szabo's random phases, 0 all seven equal at every trig (a hard attack, then the flanging of Szabo's figure 19) | at a trig |
| MACHINES + PUNCH **Sub** | the centre's increment shifted right by 1 or 2 (one or two octaves lower), the high-pass's cutoff with it so that it does not cut the sub; on the device a switch (k 32, as CHIPS' bass) with two states | once a block |

Against the reference with the same three controls (`_scratch/ultrasaw/`, 43 clips): first 2 048 frames 68–139 dB,
third-octave bands within 0.47 dB, the ColdFire object equal to the host bit for bit (now also with Phase 0, Sub 2 and
Tone 127). C, the core alone: 3 554 instructions a block (+30), a block with a trig +70.

Levels: Tone above 32 thins the sound and lowers it (−6 dB at 64, −12 dB at 96, about −18 dB at 127 at note 48);
Phase 0 sums the seven sawtooths in phase at a trig, its peak 4.5 to 6 dB above the random phases' (on the device the
amp envelope starts from zero at the trig). The output stage's level against TONE is step 2's.

## 8. The listening page heard (2026-11-16)

The maintainer on cards 1, 4, 5 and 6: « passt alles, hört sich gut an. festkomma, klar was sonst?! » and for Sub
« -2octaves »: the fixed point, Tone's range (16 steps an octave, Szabo's at 32) and Phase as in §7 stay; **Sub on =
the centre two octaves lower** (the core's `sub` 2; off = 0). Step 1 is done.

## 9. Step 2: the package (2026-11-16)

The maintainer: « Yes, step 2 », with the proposed defaults.

### 9.1 Files

| File | What |
|---|---|
| `tools/machines/maxsaw/maxsaw.c` | step 1's core with the chosen variant only (naive sawtooths, the 2-pole high-pass; the one-pole and polyBLEP left out), its host entries under `MSAW_HOST`, the glue for the voice loop |
| `tools/machines/maxsaw/maxsaw_tables.h` | generated: Szabo's offsets, detune curve and mix curves at 0–127, the high-pass's a1, a2, a3 at cutoff notes −36 to 140, `EXP2_T` |
| `tools/machines/maxsaw/maxsaw.o` | the committed object (`ld -r`, m68k-elf-gcc 16.2) |
| `tools/machines/maxsaw/manifest.json` | machine `USAW` (a working name; `MAXSAW` since §15), CHORD's picture (5) until it has its own, DECAY 80; knobs Saw Detune / DET 64 (MaxSaw Detune … since §15), Saw Mix / MIX 95, Saw Tone / TONE 32, Saw Phase / PHAS 127; the shortcut MACHINES + PUNCH (Sub); claims k 32 and record slot 18, as CHIPS's switches; order 85 |
| `tools/machines/maxsaw/LICENSE` | MIT (model27) |
| `tools/gen_maxsaw.py` | the tables from Szabo's formulas, the object, with `--cycles` the composed tweak `85-maxsaw.json` |

The 18 other composed tweaks regenerated by their generators: each gained the conflict `maxsaw`, nothing else
changed (their objects and tables byte for byte the same); `REGISTRY.md` regenerated.

### 9.2 The glue

As CHIPS's (notes/83 §4): one voice and one set of knobs a track in the package's variables; `maxsaw_update` sets up
the stock amp chain as TONE does (DECAY through `LUT_DECAY`, the envelope's words and PUNCH's in the block of `+0x38`),
computes the note as every machine (the trig's note + PITCH − 64 + FINE), reads COLOR / SHAPE / SWEEP / CONTOUR as
Detune / Mix / Tone / Phase and the switch Sub from bit 8 of k 32 in the note's sound (a preview's copy when there is no
sound, a trig's lock when it holds the switch); `maxsaw_render` pauses while the envelope is closed and no trig comes,
else saves MACSR, makes a fresh voice when the track took the machine (the init draws its phases through the EMAC, so
it runs here and not in update), draws the new phases in the block of `+0x38` (the attack's start, the VCA at zero)
with that block's Phase, runs the core, puts it on the bus, then AMP_ENV, VCA and PUNCH, and gives MACSR back. The
stock VCA's cut at a trig is kept (TONE's behaviour): the phases jump there.

### 9.3 The level [HYP until step 3]

PUNCH (`0x400a967a`, read 2026-11-16) works a frame as: x × 4 × `+0x2a0` saturated (off ×1, on ×3: its drive), then ×
the transient's envelope × `+0x2a4`; the voice loop halves the voice (notes/71 §3). `+0x2a4` is a plain gain after the
saturation. Max Saw's seven sawtooths add up to 4.3 at Mix 95 and more at a coherent start (Phase 0) and through the
high-pass's overshoot (up to about 7.8 in the listening page's clips), so the core's Q27 goes onto the bus × 2 (8.0 full
scale: the core never saturates) and `+0x2a4` is `0x7fffffff`, TONE's × 4: a track's output is the core's / 16, a single
sawtooth at gain 1 a TONE voice at full scale − 6 dB. From the host core at the defaults (note 48): peak about −13 dB,
RMS about −27 dB (TONE −18.1 / −24.1, notes/71 §6). To be measured in Unicorn and decided by the maintainer (step 3).

### 9.4 Proofs (`_scratch/ultrasaw/pkgcheck/`)

- `same_bits.py`: the package's core against step 1's chosen variant (h2b0), the 36 clips of the listening page: the same
  bits.
- `cf_object.py`: the committed object linked with empty AMP_ENV, VCA and PUNCH and run in the ColdFire interpreter as
  the voice loop calls it, six tracks: render = the host core (Q27 × 2) over 300 blocks each with random knobs, notes,
  PITCH and FINE, trigs and the Sub switch; MACSR given back; DECAY 100 in `+0x250`; PUNCH's words off and on as TONE's,
  `+0x2a4` Max Saw's; Sub from the sound, from a preview's copy, from a trig's lock that holds it (on and off) and
  one that does not; the pause (out 0, the state unchanged, 195 instructions); a trig with the envelope closed runs the
  core; a change of machine gives a fresh voice with the track's seed: ALL OK. The interpreter learned `bset`, `bclr`
  and the bit instructions on a byte in memory for it (GCC tests the lock's flag in memory).
- update + render, without the OS's chain: 4 060 instructions a block on average (4 055 to 4 371; the core alone 3 554).
- `tools/compose.py` (official file): alone (MAIN OS `3b4284bd…`), with SAMPLE (`4a2b46e0…`), SOLID (`eb29dacf…`),
  CHIPS (`50096d9d…`), all four (`0c4b9566…`), and the whole build with every offered card and Max Saw as machine 9
  (`cb4c78b8…`).
- Without firmware: `registry.py --check`, `check_overlaps.py`, `claims.py --check --self-test`,
  `gen_flasher_tweaks.py --check`, `gen_maxsaw.py --cycles … --check`, `py_compile`: ok.

### 9.5 Not done in step 2

The flasher's card, guide, release, `PROVENANCE.md`, `BUILD.md`, `README.md`, the web composer's checks (step 6); the
assembly loop (with the load, step 3); own pictures.

### 9.6 Step 3

See §10.

## 10. Step 3: the proof on the OS's own code (2026-11-16)

The maintainer: « Yes, step 3 ». `tools/emu/test_maxsaw.py` and `tools/emu/maxsaw_ref.c`, after test_chips.py
(notes/83 §5), without its display part (Max Saw shows its values as numbers, the stock way):

| Part | What it checks |
|---|---|
| startup | the bootstrap and the boot hook, the registrar's tables, lookups, MACHINES page, records and knobs (as test_compose.py); the shortcut layer's presses byte for Max Saw 1 (MACHINES + PUNCH, not GATE) |
| core | at every block not paused, what `maxsaw_render` gives AMP_ENV = the host core (`maxsaw_ref.c`: a fresh voice with the track's seed, the trig's phases in the block of `+0x38` with that block's Phase), fed the inputs computed from memory: 81 cases (39 with --quick) (Detune, Mix, Tone, Phase across their range, notes 0–127 with and without Sub, the top oscillator at its highest, Phase 0 in phase, PUNCH, Sub from the sound, a preview and a lock, PITCH, FINE, DECAY, GATE, retrigs, knobs moving every block); the pause and the wake; the chain called once each in order |
| inputs | Sub, Phase 0, Tone 0, Detune 0 change the sound; a trig's lock of Sub plays as Sub in the sound |
| chain | the envelope and the chain's words TONE's block for block, `+0x2a4` 0x7fffffff (TONE 0x20000000); PUNCH acts |
| tracks | a change of machine (Max Saw, TONE, Max Saw: a fresh voice); six tracks exact and as alone; Max Saw among KICK, METAL, PERC, CHORD; the stock machines without Max Saw identical to the stock OS, no instruction of Max Saw |
| next | next to SAMPLE and next to CHIPS (machine 7): start-up, the track as alone, the stock machines unchanged |
| compare | loudness (BS.1770) against TONE, PERC, METAL, CHORD; the fundamental at Detune 0, with and without Sub |
| measure | peak and RMS over 100 ms and 0.5 s next to the stock machines; instructions a block of one voice, a paused voice, six tracks against six TONE, the stack |

`--dry` (no Unicorn, run here): Max Saw machine 6 alone (code `0x43000000..0x43001c9e`, variables 636 bytes at
`0x43036000`), machine 7 next to SAMPLE and next to CHIPS; the host core at the defaults, note 60: peak −9.5 dB, RMS
−20.9 dB of the bus, a track after the chain / 2: about −15.5 / −26.9 dB (TONE −18.1 / −24.1). The Unicorn parts stop
with SIGILL in Claude's sandbox (exit 132): the maintainer's run.

### 10.1 The maintainer's run (2026-11-16): ALL OK

Every part passes: start-up and the registrar alone and as machine 7 next to SAMPLE and next to CHIPS (the MACHINES
page shows `USAW` with CHORD's picture; the shortcut layer's presses byte 1); the core exact in 81 cases, 13 758 blocks;
the pause (385 blocks) and the wake; the chain called once each in order; the inputs act; the chain TONE's block for
block with `+0x2a4` 0x7fffffff; the tracks (a change of machine, six tracks, mixed, the stock machines identical to
the stock OS); next to SAMPLE and CHIPS the track as alone.

Measured, note 60:

| | peak / RMS 100 ms (dB) | 0.5 s at DECAY 127 | loudness 0.5 s (LUFS, against TONE) |
|---|---|---|---|
| TONE | −18.1 / −24.1 | | −22.8 (0) |
| PERC / METAL / CHORD | −15.1 / −27.0, −14.7 / −32.3, −22.4 / −30.7 | | +1.1, +1.6, −7.7 |
| Max Saw, the defaults | −16.7 / −28.3 | −15.9 / −28.0 | −27.7 (−4.9) |
| Detune 0 / 127 | −18.3 / −26.8, −14.3 / −27.3 | | −27.1 (−4.3) at Detune 0 |
| Mix 0 / 127 | −18.5 / −31.1, −17.6 / −28.8 | | −31.2 (−8.4), −28.1 (−5.3) |
| Sub | −14.3 / −27.4 | | −27.4 (−4.6) |
| Tone 0 / 96 | −17.0 / −27.5, −20.0 / −39.2 | | −36.5 (−13.7) at Tone 96 |
| Phase 0 | −6.5 / −22.1 | −6.5 / −26.8 | |
| PUNCH on | −8.9 / −24.5 | | |

The fundamental at Detune 0: 261.7 Hz (note 60.0), with Sub too (the seven's period); TONE 261.6 Hz.

The cost, instructions a block of one voice (the voice loop less the muted loop): 4 791 in every setting (PUNCH on
4 786), the trig's block 5 583, Phase 0 with a trig every 10 blocks 4 801 on average, paused 211; TONE 5 291, PERC 6 079,
METAL 6 431, KICK 7 429, SNARE 7 158, CHORD 8 300. Six tracks 28 746 against six TONE 31 746 (0.91 ×); the stack 168 bytes
below the voice loop. All in C: the assembly loop is not written yet.

**The level.** Max Saw at the defaults is 4.9 LU quieter than TONE, its peak 1.4 dB above TONE's. It cannot get
louder without clipping somewhere: `+0x2a4` is at its top (1.0), and Phase 0's in-phase start already brings the bus
to about −0.5 dB before the chain (the track's −6.5 dB is the bus × 1/2). A higher gain on the bus (× 4 instead of × 2)
would make the defaults about as loud as TONE, and clip Phase 0's start and the widest settings before the envelope.
The maintainer's choice (2026-11-16): **keep it** (« Keep it »): 4.9 LU below TONE, no clipping anywhere; a track
is raised with its Track Level or Volume as usual.

## 11. The frame loops in assembly (2026-11-16)

The maintainer: « Yes, assembly », after the C version's cost (§10.1). `tools/machines/maxsaw/maxsaw_cf.S`, two
loops a block, each two frames a pass; `msaw_block` calls them on the device and runs its C loop on the host (the
proofs' model):

- `msaw_saws`: the seven phases in d0–d6 for the block, the increments read from memory (`add.l (d,a5),Dn`), the
  centre's gain in d7 and the sides' in a2 ramped by a3/a4, seven `mac.l` and one `movclr.l` a frame: 20 instructions
  a frame.
- `msaw_hpf`: the high-pass in place, s1/s2 and the four coefficients in registers, then onto the bus: y × 2 with
  `add.l` and, only past full scale, a branch that saturates (render's C loop for that is gone on the device): 25
  instructions a frame.
- `maxsaw_render` itself only tests the pause and zeroes the block; the rest is `render_live` (not inlined), so that
  the pause's path saves no registers (GCC had made it 258 instructions with the assembly inlined; now 191).

Checked in the ColdFire interpreter (`_scratch/ultrasaw/pkgcheck/`): `cf_object.py` ALL OK as in §9.4, the object
equal to the host core over six tracks with trigs and Sub; `hpf_edges.py`: `msaw_hpf` alone against the C loop's
arithmetic with the × 2 saturation, 300 blocks with inputs at and past the limit (2 453 saturated values, both signs):
equal. update + render without the OS's chain: **1 845 instructions a block** (C: 4 060, −55 %), paused 191 (C: 195).
`gen_maxsaw.py --check` and every other generator's `--check`, `registry.py` (regenerated), `check_overlaps.py`,
`claims.py`, `gen_flasher_tweaks.py --check`, the whole build: ok. `tools/emu/emac.py` takes `mac.l` and `movclr.l`
with address registers (its `REG` holds a0–a7), which the Unicorn proof needs.

The maintainer's Unicorn run of the assembly (2026-11-16, `--only core,chain,tracks,next,measure`): ALL OK, the core exact in the 81 cases, the level unchanged; one voice **2 576** instructions a block in every setting (C 4 791), the trig's block 3 368, paused 207; six tracks 15 456 against six TONE 31 746 (**0.49 ×**); the stack 260 bytes below the voice loop.

## 12. Step 4: a build for digiemu (2026-11-16)

The maintainer asked for a build to try in digiemu while the Unicorn run of §11 was still out. `tools/compose.py
--machines maxsaw --tool elektron-firmware-tool` on the official file: Max Saw alone as machine 6 (code 7 674 bytes
at `0x43000000`, variables 636 bytes at `0x43036000`) and the shortcut layer (one switch, code 2 088 bytes at
`0x43001dfc`); MAIN OS 1 759 788 bytes, SHA-256 `65ea533b…`; elektron-firmware-tool: checksums and HMAC ok, the same
MAIN OS. The file (`_scratch/ultrasaw/build/digiemu/model27-ultrasaw-0.1.syx`, SHA-256 `15ce184a…`) is outside the
repository. The maintainer went to the device instead (§13).

## 13. Sub on the device, and a new Sub (2026-11-16)

The maintainer on the device: « klingt grundsätzlich sehr gut », but with Sub on often no pressure below, rather
artefacts in the mids and highs, crackle, a short noise. Their two recordings (COLOR 81, SHAPE 13, SWEEP 12, CONTOUR 119,
DECAY 37, GATE on, PUNCH off, the pad's note, C5 on the Cycles = 261.6 Hz) against the host core at the same settings
(`_scratch/ultrasaw/device/`): third-octave bands within 0.6 dB, the same lines from 25 to 140 Hz, no clipping (peak
−14 dBFS); with Sub the 65.4 Hz line is the strongest. The device does what §7 says: Sub is the centre's sawtooth two
octaves down, which brings as many overtones as fundamental, its reset every 15 ms a buzz in the highs; at Mix 95 the
centre is one of seven (its fundamental −12 to −14 dB of the whole, §7's high-pass −3 dB on it). The high-pass going down
with it lets 4 to 8 dB more aliasing below the note through (`_scratch/ultrasaw/subcheck/`).

SY SWARM's SUB does the same (`_scratch/sy-swarm/befund.md`, « SUB in detail »): the centre's increment shifted right by
2 or 1 and its wavetable picked again for the lower note; no other oscillator, no gain, no filter. Its sawtooths come
from band-limited tables (at 65 Hz all 255 harmonics of a 512-point table, no aliasing).

A listening page (`_scratch/ultrasaw/subvar/`, cards 7 to 9: the maintainer's settings, the defaults, a line of six
notes; variants x.1 off, x.2 the current Sub, x.3 sine −2, x.4 sine −1, x.5 triangle −2, x.6 square −1, x.7 the
sawtooth −2 through a low-pass): the seven sawtooths from the package's core bit for bit, the new forms a draft in double
added after the high-pass, each as strong as a sine of height 1. The maintainer: « bei allen 3 beispielen: säge
gefiltert -2 ».

**Sub from now on:** an extra oscillator, a naive sawtooth two octaves below the note (phase 0, its middle rising, at each
trig) through a 2-pole low-pass (TPT, Butterworth) at the note, added after the high-pass; the centre and the high-pass
stay at the note. On the page its level is a sine's of height 1 (the filtered sawtooth × 1.34).

The bus at CONTOUR 0 (all in phase at the trig), Mix 95, notes 36 to 96, the worst (`_scratch/ultrasaw/subvar/`, the
draft): without the new Sub +0.26 dB at Detune 0, below full scale from Detune 40; with it at the page's level +1.36 dB
(Detune 0), +0.98 (16), +0.31 (40), −0.39 (64); 1.5 dB quieter +1.19, +0.81, +0.12, −0.47; even 12 dB quieter +0.55 at
Detune 0. A quieter Sub does not keep CONTOUR 0 with little Detune below full scale (the seven alone touch it); at
CONTOUR 127 nothing saturates. The maintainer first chose 1.5 dB quieter on the claim that nothing would saturate
then, which was wrong: asked again.

By CONTOUR, the new Sub at the page's level, Mix 95, notes 36 to 96, 12 trigs each, the worst: CONTOUR 0 +1.36 dB
(Detune 0), +0.98 (16), +0.31 (40); CONTOUR 8 +0.54, +0.47, +0.09; CONTOUR 16 −0.35, −0.42, −0.55; CONTOUR 32 about
−2 dB. The saturation sits where the core goes onto the bus (§9.3, before the envelope, the VCA and PUNCH); Volume +
Dist and Track Level act later, in the mixer (`0x40056f58`, `0x400567ba`), so turning them down does not undo it. In the
machine: scaling Max Saw as a whole down 1.5 dB costs nothing (the mix tables and the Sub's gain are constants) and
keeps CONTOUR 0 below full scale at Mix 95, at 6.4 LU below TONE instead of 4.9; a soft clip instead of the hard one
would cost instructions (not measured).

The maintainer asked whether CONTOUR could start above 8 instead. The phases are random within CONTOUR's width, so a
floor only makes coincidences rarer: over 10 800 trigs (notes 36, 60, 84; Detune 0, 16, 40; Mix 95, 127; Tone 0, 32; the
new Sub at the page's level), trigs over full scale at CONTOUR 8: 6.78 % (worst +0.94 dB), 12: 1.50 % (+0.70), 16: 0.44 %
(+0.60), 20: 0.11 % (+0.25), 24: 0.07 % (+0.22), 32: none (−0.01 dB). A floor would have to be about 32, and would drop
CONTOUR 0's in-phase start. CONTOUR 0's worst over notes 36 to 96, Detune 0 to 40, Mix 64 to 127, Tone 0 to 48: +1.34 dB
(note 48, Detune 0), so Max Saw 1.5 dB quieter keeps all of these below full scale. The maintainer: « Leave it »: the
Sub at the page's level, Max Saw's level as it was; at CONTOUR 0 to about 24 with little Detune a trig's start may
saturate briefly.

## 14. The new Sub built (2026-11-16)

- `maxsaw.c`: `struct msaw` takes the Sub's phase and its low-pass's state (`sph`, `l1`, `l2`; 92 bytes a track);
  a trig sets `sph` to 0; `params` no longer moves the centre and gives the note's increment; the high-pass's cutoff is
  the note's moved by Tone, with or without Sub. With Sub on, a block runs the Sub first: its sawtooth (`sph` read as
  int32 × `SUB_GAIN`, `sph` += the note's increment >> 2), the 2-pole TPT low-pass at the note (the high-pass's tables
  `SVA1_T`..`SVA3_T` at the note), its v2 into a block `sbuf` (one for all tracks, 128 bytes); the high-pass then adds it
  before the bus. Sub off runs nothing of it (the phase and the state stand still; the next trig sets the phase to 0).
- `SUB_GAIN` (Q27, 1.3428): `gen_maxsaw.py` computes it in double, the filtered sawtooth two octaves below note 60
  with the RMS of a sine of height 1 (the listening page's level).
- `maxsaw_cf.S`: `msaw_sub` (18 instructions a frame, two frames a pass) and `msaw_hpf` with a fourth argument, the
  Sub's block or 0 (a second loop with one `add.l` a frame more).
- Proofs (`_scratch/ultrasaw/subimpl/host_checks.py`, `_scratch/ultrasaw/pkgcheck/`): Sub off, the host core equal to
  the core before §13 bit for bit (40 runs of 400 blocks, knobs, notes and trigs moving); the Sub (Sub on less Sub off)
  equal to the draft in double to 97.5 dB at worst (notes 24 to 108); the bus at CONTOUR 0 / 8 / 32 +1.35 / +0.53 /
  −2.01 dB as the draft's; `cf_object.py`: the object equal to the host core, six tracks with Sub switched, the switch,
  the pause, MACSR, ALL OK; `sub_edges.py`: `msaw_sub` (the phase's wrap) and `msaw_hpf` with the Sub (the saturation
  both ways) equal to the C loops, 300 blocks each; `hpf_edges.py` without the Sub as before.
- The cost in the ColdFire interpreter, update + render without the OS's chain, the defaults: Sub off 1 832, Sub on
  2 549 instructions a block (+717). The maintainer's Unicorn run (`test_maxsaw.py --only core,chain,tracks,next,
  measure`, 2026-11-16): ALL OK. One voice, instructions a block: Sub off 2 567 (the trig's block 3 391; before
  §13 2 576 / 3 368), Sub on 3 284 (+717; the trig's block 4 108), Phase 0 with a trig every 10 blocks and Sub
  3 294 on average, PUNCH on 2 562, paused 207; six tracks with Sub 19 704 against six TONE 31 746 (0.62 ×);
  the stack 280 bytes below the voice loop. The level with Sub, note 60: peak / RMS −14.1 / −25.1 dB (before §13
  −14.3 / −27.4; Sub off −16.7 / −28.3 unchanged).
- `85-maxsaw.json`: code 8 546 bytes, variables 836, 16 468 bytes added to the image; `REGISTRY.md` regenerated;
  `registry.py --check`, `check_overlaps.py`, `claims.py --check --self-test`, `gen_flasher_tweaks.py --check`, the
  harness's `--dry`: ok. The manifest: version 0.2.
- The full build for the device (`_scratch/ultrasaw/build/digiemu/model27-ultrasaw-full-0.2.syx`, SHA-256
  `f63473bd…`, MAIN OS `2ff7d5e3…`, elektron-firmware-tool: checksums and HMAC ok): every OFFERED card and Max Saw as
  machine 9. The maintainer on the device (2026-11-16): « gerät passt, sub klingt jetzt gut. fett alter, nice ».

## 15. The name: Max Saw, MAXSAW (2026-11-16)

The maintainer did not like `USAW` (« liest sich wie US of A ») and wanted « irgendwas mit saw und einem superlativ
davor »; up to six characters fit on the device (SAMPLE). Proposed: MAXSAW, GIGSAW, MEGSAW, HYPSAW, TITAN, FATSAW (not
« Massive », Native Instruments' synth, nor « Super Saw », a maker's term); a web search found no synth or plugin named
« FatSaw » or « MaxSaw » (no trademark register searched). The maintainer: « MAXSAW (Max Saw) ». Renamed everywhere
before the first commit: the package `tools/machines/maxsaw/` (`maxsaw.c`, `maxsaw_cf.S`, `maxsaw_tables.h`,
`maxsaw.o`), `tools/gen_maxsaw.py` → `85-maxsaw.json`, `tools/emu/test_maxsaw.py` and `maxsaw_ref.c`, the symbols
(`maxsaw_update`, `maxsaw_render`, `msaw_*`), the voice's mark `'MXS1'`, the 18 other tweaks' conflict lists; the
machine on the device `MAXSAW`. The text above says Max Saw for the machine throughout; the scratch folder keeps its
name (`_scratch/ultrasaw/`), and so do the builds made before (`model27-ultrasaw-*.syx`).

Checked after the rename: `gen_maxsaw.py --cycles … --check`, `gen_chips.py --cycles … --check` (a conflict list
re-sorted as its generator writes it), `registry.py` (regenerated), `check_overlaps.py`, `claims.py --check
--self-test`, `gen_flasher_tweaks.py --check`, `test_maxsaw.py --dry`: ok; in the ColdFire interpreter `cf_object.py`,
`hpf_edges.py`, `sub_edges.py` and the host checks of §14 as before (the same instructions a block). The full build for
the device: `_scratch/ultrasaw/build/digiemu/model27-maxsaw-full-0.2.syx` (SHA-256 `cff81c92…`, MAIN OS `4d3cb59c…`,
elektron-firmware-tool: checksums and HMAC ok), Max Saw as machine 9. On the device (2026-11-16): « machine name passt.
in den regler steht nur Saw und in der zweiten zeile der custom parameter name » (the popup's two lines, notes/71 §10:
the knobs' long names are still « Saw Detune » … from the working title). As the other machines (« Snare Contour », « Solid
Body », « Chips Wave »: the machine's name on the popup's first line), the maintainer: « Yes, MaxSaw »: MaxSaw Detune,
MaxSaw Mix, MaxSaw Tone, MaxSaw Phase (the short names DET, MIX, TONE, PHAS as before). Checks as above: ok (the image 12 bytes
longer). The full build: `_scratch/ultrasaw/build/digiemu/model27-maxsaw-full-0.2b.syx` (SHA-256 `2a3cc704…`, MAIN OS
`acc36d7a…`, checksums and HMAC ok). On the device (2026-11-16): « passt, alles steht ganz da ».

## 16. Step 6: the card, the guide and release 0.69 (2026-11-16)

The maintainer: « mach erstmal alles fertig damit die neue machine wie sie jetzt ist veröffentlicht werden kann »; on the
texts: « "based on Adam Szabo" finde ich besser. texte aus nutzer sicht. füge ihn auch auf dem "kassenzettel" im footer
hinzu, link auf seine website/pdf. […] grafiken kommen später. rest passt », and the synthesizer's maker named
nowhere. So: no maker's or synthesizer's name anywhere (the notes, the code's comments, the manifest, AGENTS.md cleaned too; « Super Saw »
only in the thesis's title), Chord's picture for now.

The branch first moved up to main (`b3520b1`, a fast-forward: nothing of ours committed yet, none of main's files
touched by ours). Then, as CHIPS (notes/83 §12):

- `gen_flasher_tweaks.py`: the `FEATURES` entry `maxsaw` after CHIPS (`package`, `cat` sound, experimental), in
  `OFFERED`; its credit `{"kind": "based", "who": "Adam Szabo", "url": <the thesis on his site>}`: a credit may carry a
  `url` instead of a `repo` (a work published outside GitHub); `tweaks.js` regenerated (nineteen cards).
- `app.js`: the card's texts (`FEAT.maxsaw`, from the player's side: COLOR, SHAPE, SWEEP, CONTOUR, MACHINES + PUNCH, a
  step's lock), `GUIDE_OF`; `creditHtml` with a `url` says « based on Adam Szabo », his name the link; the credits list
  takes an entry with `url` and `name` (« How to Emulate the Super Saw by Adam Szabo »); `REF_MAINOS` and `REF_MODS`
  regenerated (`ref_mainos.py`: 191 combinations, 65 538 mods, 8 min).
- The footer's receipt (`flasher/index.html`): « 1 supersaw analysis — Adam Szabo », linked to his thesis: the one name
  that does not link a GitHub profile, by the maintainer's choice (docs/AGENTS.md).
- The guide: section 6 MAXSAW (« Based on Adam Szabo », the steps, the knob table with the names on screen, the facts,
  Experimental), the later sections renumbered, MAXSAW in every other card's list of mods (and CHIPS with it in the
  LP/HP Filter's, where it was missing); the home page lists it (`10 MAXSAW / WIDE SAW`).
- Release 0.69 (`release.js`), the stamp 2026-11-16-22 on the six pages; README (nineteen cards), BUILD.md (section
  « Machine MAXSAW », the MAIN OS of `maxsaw` alone `9d9ae4e5…`, with SAMPLE `cd4bdccd…`, with every card `acc36d7a…`),
  PROVENANCE (`85-maxsaw.json`), THIRD-PARTY-NOTICES (a published analysis, no code), AGENTS.md.
- `webflash_smoke.js`: the nineteen cards and rows, MAXSAW in Machines, its credit, alone / with SAMPLE / with the
  other machines and with every card, its tag; the receipt's eleven names (Adam Szabo's link his thesis), the credits
  list; `webcompose_synth.py`: MAXSAW alone, with SAMPLE both ways, with SOLID, CHIPS, CHORD Tables and Crush, and the
  full set.

Checked: `gen_flasher_tweaks.py --check`, `registry.py --check`, `check_overlaps.py`, `claims.py --check --self-test`,
`ref_mainos.py --check`, `node --check` of the scripts, `py_compile`, `webbuild_check.sh`, `webflash_check.sh`,
`webcompose_check.sh` on the official file (83 builds identical to compose.py, five with MAXSAW),
`gen_wavetables_page.py --check`; the pages served locally in a browser: the card, its Details, the credit, the tag,
the receipt, the credits, the guide's section, the home page, no console error. Not run here: `webflash_smoke.sh`
(npm's registry is out of the sandbox's reach); the maintainer's first run: one FAIL, the check of the cards'
names, which still listed eighteen (MAXSAW added after CHIPS; the page's names checked in a browser against the
new list); the run again (2026-11-16): « all ok ». Committed `43231c3`.

## 17. Flashed from the page: tested (2026-11-16)

The maintainer flashed release 0.69 from the page, served locally with every card ticked, onto their Model:Cycles:
« geflasht von der seite, alles gut ». Before, MAXSAW in a build with every card from the command line (§14, §15). The
card's status tested (`gen_flasher_tweaks.py`, `tweaks.js`): no tag; the guide's line Tested, the release entry
without « experimental », README (all nineteen cards tested), BUILD.md, PROVENANCE, AGENTS.md, the manifest
(`tests.hardware`, tested), `webflash_smoke.js` (the card without a tag); the stamp 2026-11-16-23 on the six pages.

