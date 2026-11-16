# 83 — CHIPS, a chip square with an arpeggio inside the note, after Plaits

The maintainer's plan of 2026-11-15 (notes/82): new machines after single engines of Mutable Instruments Plaits, one
engine a machine, each built on SOLID's path (notes/71): (1) the fixed point on the host against a float reference,
(2) the package, (3) the proof in Unicorn and the load, (4) digiemu, (5) the device, (6) the card, the guide, the
release. The second is **CHIPS**, after Plaits' `ChiptuneEngine` (eurorack 08460a6,
`plaits/dsp/engine2/chiptune_engine.{h,cc}`, its `SuperSquareOscillator`, `NESTriangleOscillator` and chord bank, MIT,
© 2016–2021 Emilie Gillet), which the maintainer chose after hearing the unchanged engine, then changed: Plaits'
arpeggio (a trig a chord tone) and its chord mode are gone; an arpeggio inside the note, as old sound chips play
chords, and a pitch sweep take their place. Steps 1 and 2 are done here; the maintainer asked to go one step at a time.

Package `tools/machines/chips/` (`chips.c`, `chips_tables.h`, `chips.o`, `manifest.json`, `LICENSE`,
`LICENSE-Plaits`), generator `tools/gen_chips.py`. Step 1's programs, renders, listening page and the step 2 proofs
live outside the repository (`_scratch/chips-machine/`, `_scratch/chips-machine/step2/`). Addresses: VAs of OS 1.13.

## 1. In short

- One voice: Plaits' hard-synced square (polyBLEP) and, on a switch, its 32-step triangle bass an octave below.
- COLOR = **Wave** (Plaits' MORPH), SHAPE = **Chord** (Plaits' eleven chords within one octave, a zone of 11 or 12
  values each over 0–127; since §10 named on the display, since §11 in the OS's big font: OCT, one tone, a mono synth,
  then 5, SUS, m, m7, m9, m11, 69, M9, M7, M; from §8 to §10 the stock CHORD machine's), SWEEP = **Sweep** (the
  note starts up to 48 semitones above or below its pitch and falls onto it, 30 ms), CONTOUR = **Arp** (0–63 the
  song's tempo, 1/4 to 1/32 with triplets; 64–127 free, 16 to 64 changes a second; since §8 shown as 1/4 .. 1/32 and
  Hz; no off since §9: one tone is OCT's). The defaults since §9: Chord 0 (OCT, one tone), Arp 1/16.
- MACHINES + PUNCH = the bass, MACHINES + GATE = the arpeggio up and down; PUNCH also sets the bass's level (on: as
  loud as the square; off: 6 dB lower). DECAY, GATE and PUNCH the stock amp chain as on TONE, its output stage too (since §7; 6 dB louder before).
- The arpeggio starts on the root at every trig; the oscillators run on; while the envelope is closed the core is not
  called and stands still, as SWARM's.
- Fixed point on the EMAC: against Plaits' unchanged oscillators in double, with the core's frequencies, the largest
  error is −113 dB (Plaits' own float32 is −4.8 dB off its double over a second). The maintainer, after the listening
  page: « klingt geil ».
- The proof on the OS's own code (step 3, §5): ALL OK, the maintainer's runs of 2026-11-15. One voice with the OS's
  chain: 1 672 instructions a block as a square (0.32 × TONE's 5 291), 2 215 with the bass (0.42 ×), 4 052 with the
  bass above 750 Hz (0.77 ×), 226 paused; six tracks with the arpeggio and the bass 0.42 × six TONE. The square's peak
  is TONE's (−18.1 dB).
- digiemu and the device (steps 4 and 5, §6, 2026-11-15): « passt », the switches, their lock, PUNCH, the sweep, the
  tempo; the CPU page not measured yet.

## 2. The maintainer's decisions (2026-11-15)

| Question | Decision |
|---|---|
| Name | CHIPS |
| Plaits' arpeggio and chord mode | gone (« ohne Mehrwert ») |
| Instead | the arpeggio inside the note (old sound chips), restarting at every trig; tempo 0 = off, a mono synth (until §9: since 2026-11-16 the mono synth is SHAPE's one tone alone) |
| Knobs | COLOR = waveform, SHAPE = chord, SWEEP = pitch sweep, CONTOUR = arpeggio tempo |
| Switches | MACHINES + PUNCH = bass on/off, MACHINES + GATE = the arpeggio's direction (up, up-down) |
| Chords | Plaits' 11 at first; from §8 (2026-11-15) the stock CHORD machine's, its table read from the OS at run time and its own display (« die Anzeige der Akkorde ist mit 0–127 absolut nutzlos »; « bau es so »); since §10 (2026-11-16) Plaits' again, one a step and named (« ich glaube ich will zurück zu den plaits akkorden. die haben mir besser gefallen ») |
| Envelope | the stock one (DECAY, GATE), outside the core; PUNCH as on the stock machines |
| Priority | a low CPU load first |
| Arpeggio tempo | the mix: CONTOUR 1–63 divisions of the song's tempo (1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, nine values each, no 1/32T), 64–127 free, 16 to 64 Hz exponential; the bounds confirmed; since §9 (2026-11-16) 0 is 1/4 too, no off |
| Range | one octave (Plaits' chords folded); from §8 to §10 CHORD's chords as CHORD plays them, up to 19 semitones above the root; since §10 one octave again |
| OCT | one tone as in Plaits, so that CHIPS on OCT is a mono synth; from §8 to §10 CHORD's SHAPE 0–2 (its unisons); since §10 OCT again, SHAPE 0 |
| CONTOUR's display | OFF, the divisions, then Hz (§8); since §9 the divisions from 0, then Hz |
| One way to stop the arpeggio | SHAPE 0–2 (one tone; since §10 OCT, SHAPE 0); CONTOUR's OFF gone, Chord's default 0 (one tone), Arp's 1/16 (§9, 2026-11-16: « Ja, OFF raus ») |
| SHAPE's steps and display | §10 one step a chord, 0–10, the name in the medium font (the agent's choice); §11 (« die reglersteps zu klein, das ist zu fummelig »; « große systemschrift … in der auch die ganz normalen werte 0-127 angezeigt werden ») eleven zones of 0–127 again, the name in the big font, sus4 as SUS (« nenne es gleich SUS oder SU4. 4 zeichen werden nicht gut aussehen ») |
| CONTOUR's display | §11: the narrow big font (12 × 22), one line: 1/4 .. 1/32, 16HZ .. 64HZ (the agent's variant A; B, two lines as CHORD's COLOR shows at 32, 62, 74, 84, not taken) |
| Sweep | ±48 semitones at the knob's ends, quadratic in between; exponential, 30 ms |
| Bass | follows the arpeggio (an octave below the tone it plays), follows the sweep; its level on PUNCH (on: as loud as the square, off: −6 dB) |
| Level | TONE's output stage: the 6 dB of SOLID and SWARM taken out after the device (« viel zu hoch »), §7 |
| The bass above 750 Hz | kept as Plaits plays it (its fade to a naive triangle): the maintainer left it to the agent after step 3 (« entscheide du »), §5.2 |

## 3. Step 1: the fixed point on the host `[FAIT]`

Step 1's report is `_scratch/chips-machine/README.md` (in German, for the maintainer), its numbers in
`_scratch/chips-machine/results.md`; `make.py` there rebuilds and checks everything. In short:

### 3.1 Plaits' parts

- `SuperSquareOscillator`: a master and a hard-synced slave at `(0.51 + 0.98 shape) f` below shape 0.5, `(1 + 16
  (shape − 0.5)²) f` above; polyBLEP at every edge (`stmlib/dsp/polyblep.h`), the edges' times by divisions; both
  frequencies at most 0.25 (`kMaxFrequency`). `shape = MORPH × 0.995` (`ChiptuneEngine`).
- `NESTriangleOscillator<5>`: 32 steps with a BLEP at each; above f = 1/64 it fades into a naive triangle with
  integrated BLEPs at its corners, fully from f = 1/32.
- `ChordBank`: 11 chords of four notes; `Reset` does not count 0.01, 7.01, 11.99 and 12.00, `Sort` folds the ratios into
  an octave and sorts them: OCT 0; 5 0 7; sus4 0 5 7; m 0 3 7; m7 0 3 7 10; m9 0 2 3 10; m11 0 3 5 10; 69 0 2 4 9; M9 0 2
  4 11; M7 0 4 7 11; M 0 4 7 (checked against the unchanged `ChordBank`).

### 3.2 The core

Per block: the arpeggio's clock (a phase step a block, Q32; a division `mul(bpm 8.8 << 14, k) + 1`, rounded up so that
a change on a block's start comes in that block; free `ex2`), its position and tone; the sweep's rest × e^(−1/45) a
block; the master's, slave's and bass's frequencies through `ex2` only when their note (note + tone + sweep) or COLOR
moved, each with a normalizing shift and a reciprocal `2^61 / (inc << sh)` from the same logarithm. Per frame: the
square in Plaits' steps, the slave's phase kept within its half period (`h = sp << 1`) so that each edge is one carry,
every BLEP's time `t = x / inc` a product with the reciprocal; the bass's phase kept within its step (`q = bp << 5`),
each step one carry, its level from a table, two loops compiled for its two levels; above 750 Hz Plaits' fade, in a
loop of its own. Output Q27: the square ±0.5, the bass ±0.47 (PUNCH off ±0.23).

### 3.3 What differs from Plaits, and why

| What | Why | What it costs |
|---|---|---|
| no trigger arpeggio, no chord mode, no `envelope_shape_` | the maintainer's | – |
| pitch at exactly 48 kHz, not `kCorrectedSampleRate` | to sit with the other machines (as SOLID's `l2note`) | Plaits sounds 4.6 cents higher at 48 kHz |
| the frequency constant over a block, not Plaits' ramp | one add a frame and oscillator less, the reciprocal good for the block | against the ramp (both double): level ±0.01 dB, octave bands ≤ 0.8 dB in the tone's bands (up to 2.8 dB below the note, where the level depends on the phase at the trig) |
| the BLEPs' time a product with a reciprocal | no division | in the rounding below |
| the chord by fixed zones, not `HysteresisQuantizer2` | a digital knob | no hysteresis at the zones' edges |
| square and bass mixed into one output | one track | – |
| the bass's step 2^23 (peak 0.47, not 0.5) | the BLEP and the level by shifts | the bass 0.6 dB below the square's peak |

polyBLEP stays: without it the power off the harmonics rises by 16 to 18 dB (−39.7 → −23.6 dB at note 60, −29.2 →
−11.7 dB at note 108).

### 3.4 Compared `[FAIT]`

- The rounding alone (the core against Plaits' unchanged oscillators compiled in double, fed the core's
  frequencies), 198 cases of 1 s: the largest error −113.3 dB, RMS −124.3 dB; over the listening page's 93 runs
  −104 dB at most. Plaits' float32 against its double: −4.8 dB, RMS −31.5 dB.
- Against the float model with exact pitch (the arpeggio and the sweep in double): levels and octave bands equal
  (≤ 0.02 dB), pitch within 0.003 cent, the same chord tone in the same block everywhere.
- `chips.c` against `chips_plain.c` (the line-by-line transcription of Plaits' loops): 428 runs, about 1.28 million
  blocks, the same bits.

### 3.5 Cost, estimated `[FAIT en émulation]`, not the declared cost

The core compiled as the package is (`m68k-elf-gcc` 16.2.0), counted in the ColdFire interpreter `_scratch/cfemu`,
its own signal, without the OS's chain; the object equal to the host build in every case. Instructions a block
(median):

| Case | Bass off | Bass on |
|---|---|---|
| note 36, COLOR 0 / 64 / 127 | 458 / 458 / 458 | 946 / 945 / 946 |
| note 60, COLOR 0 / 64 / 127 | 458 / 458 / 508 | 1 006 / 1 006 / 1 056 |
| note 96, COLOR 0 / 64 / 127 (the bass above 750 Hz) | 530 / 563 / 836 | 2 572 / 2 569 / 2 853 |
| the arpeggio at 64 Hz, m7, note 60 | 474 | 1 052 |
| a sweep from SWEEP 127 every 0.1 s | – | 1 364 (the largest block 2 954) |
| a drum pattern (locks, sweeps, bass) | – | 1 284 (the largest 1 496) |

The trig's block about 270 more. The costly part is Plaits' fade of the bass above 750 Hz (about 0.7 steps a frame
with a BLEP each): the maintainer's to decide after step 3.

## 4. Step 2: the package

### 4.1 The OS side `[FAIT]` (read in SAMPLE, SOLID and SWARM, notes/54, notes/63 §17, §28, notes/71 §3, notes/82 §4)

`chips_update(pmod, v, p)`: the first block since the track changed machine (the mark `'CHP1'` at `+0x2c` cleared by
the voice's reset `0x400a7ab8`) starts a fresh voice (Plaits' `Init`); DECAY's factor into `+0x250` from TONE's table
`0x4011d84c` every block; in the block of `+0x38` the amp chain and PUNCH set the way TONE sets them (`0x400aa7b8`;
PUNCH on `0x400aa8de`, off `0x400aa8fe`), PUNCH's output stage `+0x2a4` at `0x40000000` (§4.4; TONE's `0x20000000` since §7). The note: the trig's
note + PITCH − 64 + FINE (±2 semitones), as every machine. The core's trig is `+0x38`, the block after the
sequencer's, where the amp envelope starts. The knobs: COLOR `p+0x16`, SHAPE `+0x18`, SWEEP `+0x1a`, CONTOUR `+0x1c`,
8.8, smoothed by the OS as on every machine. PUNCH `p+0x1e`. The switches, k 32 bits 8 and 9, read as SAMPLE reads
them (notes/63 §17.2, §28): in the sound the note plays (`CUR_SNDS[t]` `0x800017ec` + 84), in the copy of its 66
bytes when that is 0 (a preview note, `0x800015ae + 66 t + 64`), and when the trig locked k 32 (bit 0 of
`0x423087f8 + 8 t + 4`) each switch the lock holds (bits 10, 11) from the lock; every block. The song's tempo from
`0x40149310` (1/120 BPM, notes/38), turned into BPM 8.8 (× 32 / 15) when it changes.

`chips_render(out, v)`: no trig in this block or the last (`+0x34`, `+0x38`) and the envelope's levels `+0x230`,
`+0x234` below −102 dB: 32 zeros, the core not called, its state kept (the pause, as SWARM). Otherwise MACSR saved,
the core's block (MACSR 0xa0, acc0 emptied by every read), Q27 to Q31 saturated, then `AMP_ENV` (`0x400a9252`),
`VCA` (`0x400a9430`), `PUNCH` (`0x400a967a`), and MACSR given back.

### 4.2 Files

| File | What |
|---|---|
| `chips.c` | the core (step 1's, the chosen variant fixed) and the machine; the host entry `chips_host_render` (`CHIPS_HOST`) for the proofs |
| `chips_tables.h` | generated: `exp2`, the slave's log ratio per COLOR, the semitone thresholds for CHORD's ratios (§8), the divisions and the free tempo shown in Hz, the bass's step levels, the constants (until §8 Plaits' chords' tones and counts) |
| `manifest.json` | order 84 (the next free after SWARM's 83; the maintainer's to confirm), TONE's picture (4) until CHIPS has its own, DECAY 64 by default, the knobs Chips Wave / `WAVE` 64, Chips Chord / `CHRD` 5 (OCT: a mono synth; since §8 0–37, 3 as on CHORD), Chips Sweep / `SWEP` 64 (none), Chips Arp / `ARP` 0 (off): by default a plain square; the two switches MACHINES + PUNCH (Bass) and MACHINES + GATE (Up-down), claims k 32 and record slot 18 as SAMPLE's; names and defaults are the maintainer's to decide; experimental |
| `chips.o` | `ld -r` of the source, written and checked by `tools/gen_chips.py` |
| `LICENSE`, `LICENSE-Plaits` | model27's MIT; Plaits' MIT notice, the work CHIPS follows |

Code 5 254 bytes, tables 1 819 bytes, variables 992 bytes (six voices of 124 bytes and their inputs); since §8
code 6 472 bytes (the display 924 of them), tables 2 024 bytes, variables 1 136 bytes (six voices of 148 bytes).

### 4.3 Proven `[FAIT en émulation]` (2026-11-15, `_scratch/chips-machine/step2/prove.py`)

- The package's core gives the same bits as step 1's core with the chosen options: the listening page's 70 runs with
  those options (368 000 blocks), 264 runs over notes, COLOR, bass and PUNCH, and eight random sequences in which every
  input moves (120 000 blocks).
- The committed `chips.o`, linked with `AMP_ENV`, `VCA` and `PUNCH` as bare returns, run in the ColdFire interpreter
  as the voice loop calls it (a copy of `_scratch/cfemu` with `bclr` and a byte `btst` added): six tracks over 2 400
  blocks, each its own notes, knobs jumping, PITCH, FINE and DECAY moving, the switches in the sound, in a preview's
  copy and in a trig's lock, PUNCH, five tempos (60 to 546 BPM), trigs, the envelope closing: the output equal at
  every block to the host core fed with what §4.1 says the glue hands it (Q27 << 4; zeros in 1 318 paused blocks, the
  state kept), a fresh voice after each of four cleared marks; DECAY's factor TONE's; the chain's words in a trig's
  block TONE's with PUNCH's output stage `0x40000000`; MACSR given back with acc0 empty. Update about 90 instructions a
  block, render about 1 280 over that mix (without the OS's chain).
- `compose.py --compare-ld`: relocator and ld identical alone (machine 6, descriptors 76 to 80, code at
  `0x43000000`, variables at `0x43036000`; the shortcut layer with two switches; 129 writes, 15 004 bytes added to the
  image), as `sampler,chips`, `chips,sampler`, `solid,swarm,chips` and `sampler,solid,swarm,chips` (machine 9,
  descriptors 91 to 95).
- `gen_chips.py --check`, `claims.py --check --self-test` (the package's four claims), `check_overlaps.py`,
  `registry.py --check`, `gen_flasher_tweaks.py --check`: OK; nothing changed outside the package and this note's
  index rows (no tweak yet).

### 4.4 The level `[HYP]` until step 3

The core hands the bus 1.0 = Q27 2²⁷ as full scale (SWARM's arrangement); the chain is TONE's with PUNCH's output stage
6 dB louder, as SOLID and SWARM (× 1/4 with PUNCH off, then the voice loop's × 1/2). Expected, peak at the track:
the square alone at TONE's peak (−18.1 dB); with the bass and PUNCH off about −14.7 dB; with PUNCH on the stock PUNCH
acts on top (its drive), and the bass at the square's level: about −12.3 dB before PUNCH. Step 3 measures it.

## 5. Step 3: the proof (2026-11-15): ALL OK `[FAIT en émulation]`

`tools/emu/test_chips.py` (after `test_swarm.py`) with `tools/emu/chips_ref.c`, the package's core for the host. Five
parts, `--only` runs some of them:

1. **startup**: the bootstrap and the boot hook, the registrar's tables, lookups, screens, records and knobs (as
   `test_compose.py` checks any composed machine), and the shortcut layer told that CHIPS takes MACHINES + PUNCH and
   MACHINES + GATE (its presses' byte 3 in `sc_data`).
2. **core**: at every block chips_render does not pause, what it hands `AMP_ENV` is the host's core bit for bit, fed
   what §4.1 says `chips_update` must take, computed by the proof from memory (the voice, the parameters, the note's
   sound, its 66-byte copy, the lock's mask and word, the tempo at `0x40149310`): every COLOR, every chord, CONTOUR
   across the divisions and the free part, SWEEP both ways, notes 0 to 127 with the bass, the bass above 750 Hz,
   PUNCH flipped during a note, up-down, the bass switched during a note, a preview note, three kinds of lock,
   60 to 546 BPM and a moving tempo, PITCH, FINE, DECAY, GATE, retrigs, knobs moving every block; the pause and its
   wake-up; the chain called once each in order. Then the inputs act: the bass, up-down, PUNCH and the tempo each
   change the sound, and a trig's lock of the bass plays as the bass in the sound.
3. **chain**: the amp envelope and the chain's words TONE's block for block, PUNCH's output stage `0x40000000`;
   PUNCH acts.
4. **tracks**: CHIPS, TONE, CHIPS again (a fresh voice); six CHIPS tracks with their own knobs and switches, each exact
   and as alone; CHIPS among the stock machines; the stock machines without CHIPS identical to the stock OS without
   one instruction of CHIPS; **next**: CHIPS as machine 7 next to SAMPLE the same as alone.
5. **measure**: the level next to TONE, PERC, METAL, CHORD; instructions a block of one voice (the whole voice loop
   less the loop muted) for a square, sync, the bass, PUNCH, the arpeggio, the sweep, a paused voice, six tracks
   against six TONE, the stack.

Not covered: the shortcut layer's presses and LEDs themselves (`test_shortcuts.py` proves them on REF2 and SAMPLE,
the same code for every machine that declares them; its selections hold REF2, so CHIPS is not among them), the
sequencer's writing of a lock (written here as the audio side writes it, notes/63 §28).

Here (the agent's sandbox): the syntax and `--dry` (both builds laid out, CHIPS machine 6 alone and 7 next to
SAMPLE, the layer's data found; the host core runs); Unicorn stops with SIGILL in the sandbox, so the run is the
maintainer's, in a normal terminal:

    python3 tools/emu/test_chips.py --cycles firmware/model-cycles_OS1.13.syx

### 5.1 The first run (the maintainer, 2026-11-15)

Every check passed but one, a fault of the proof: « the inputs act » played m7 at 1/16 for 150 blocks, while at
120 BPM the arpeggio's first change comes at block 188, so up-down and the tempo could not be heard
(`{'updown': False, 'tempo': False}`; `lock: False` is right: a lock of the bass plays as the bass in the sound). The
same inputs were exact in the core's 85 cases. Fixed: m7 at 1/32 over 600 blocks, its own part `inputs`; on the
host's core up-down then differs from block 377 and 60 BPM from block 97.

- **startup** `[FAIT en émulation]`: CHIPS machine 6 alone (7 next to SAMPLE), descriptors 76 to 79 named Chips Wave,
  Chips Chord, Chips Sweep, Chips Arp, TONE's picture, the change of machine sets 64, 5, 64, 0 and DECAY 64; the
  shortcut layer takes both presses on CHIPS.
- **core** `[FAIT en émulation]`: 85 cases, 17 050 blocks, exact; 385 blocks paused, woken twice; the chain in order.
- **chain**: TONE's words block for block, the output stage `0x40000000`; PUNCH acts (peak −12.0 dB, without
  −18.1 dB).
- **tracks**, **next**: all as in §5.
- **measure**, the level, peak / RMS of the track in dB of full scale, note 60, the first 100 ms:

| Sound | Peak / RMS |
|---|---|
| TONE, PERC, METAL, CHORD | −18.1 / −24.1, −15.1 / −27.0, −14.7 / −32.3, −22.4 / −30.7 |
| a square (the defaults), a narrow pulse (COLOR 10), sync (COLOR 120) | −18.1 / −19.1, −18.1 / −19.1, −18.1 / −19.3 |
| the bass, PUNCH off / on | −14.7 / −18.7, −12.0 / −19.8 |
| m7 at 50 Hz with the bass; a kick (note 36, SWEEP 120, the bass, PUNCH on) | −14.7 / −18.8; −12.0 / −19.8 |

  The square's peak is TONE's, as §4.4 expected; its RMS 5 dB above TONE's (a square against TONE's softer wave).

- **measure**, the cost, instructions a block of one voice (the whole voice loop less the same loop muted, note 60,
  DECAY 127 unless named):

| Voice | Instructions (most, the trig's block) |
|---|---|
| the defaults (a mono square) | 1 672 (1 723, 2 751) |
| COLOR 127 (sync) | 1 722 (1 744, 2 777) |
| the bass, note 60 / PUNCH on / note 36 | 2 215 / 2 207 / 2 158 |
| m7 at 64 Hz with the bass; m7 at 1/16 up and down | 2 234 (2 593); 1 693 |
| note 96, COLOR 127, the bass above 750 Hz | 4 052 (4 156, 5 174) |
| SWEEP 127, a trig every 10 blocks, the bass (the bass sweeps through 750 Hz) | 4 170 on average (4 695) |
| paused | 226 |
| six tracks, m7 at 50 Hz with the bass | 13 404 (six TONE 31 746: 0.42 ×) |

  Stock: TONE 5 291, PERC 6 079, METAL 6 431, KICK 7 429, SNARE 7 158, CHORD 8 300. A CHIPS voice is 0.32 × TONE as a
  square, 0.42 × with the bass, 0.77 × with the bass above 750 Hz. The OS's chain (`AMP_ENV`, the VCA, PUNCH) and the
  update are about 1 200 of a square's 1 672 (the core alone about 460, §3.5). Stack 208 bytes below the voice loop.

The maintainer's run of `--only inputs` after the fix (2026-11-15): ALL OK. With §5.1 every part has passed.

### 5.2 The bass above 750 Hz (decided 2026-11-15)

The maintainer left it to the agent. Kept as Plaits plays it: the 32 steps fading into a naive triangle with integrated
BLEPs between f = 1/64 and 1/32 (the bass above about 750 Hz, a root above F♯6, or a sweep from above passing there).
Why: at worst 4 052 instructions a block (0.77 × TONE), still below one stock voice, and only there; a cheaper bass
there (the naive triangle at once, or the steps without the fade) would sound different from Plaits in that range and
would need its own listening test; six tracks stay at 0.42 × six TONE. If the CPU page asks for it on the device,
this is the first place to save.

## 6. digiemu and the device (2026-11-15)

The build: CHIPS alone, `compose.py --cycles firmware/model-cycles_OS1.13.syx --machines chips --tool
../elektron-firmware-tool-main/elektron-firmware-tool`, `.syx` `c9db10d1…`, MAIN OS `953a0e1e…` (checksums and HMAC
checked by elektron-firmware-tool). Each test gave every setting it needs (the maintainer's rule of 2026-11-15).

- **digiemu** (step 4, the maintainer): the start, CHIPS on the MACHINES page with TONE's picture, the four popups
  Chips Wave, Chips Chord, Chips Sweep, Chips Arp on two lines, m7 at CONTOUR 116 (a flutter through the chord) and at
  41 (a tone a sixteenth): « passt ». The rest on the device, digiemu's handling being tedious.
- **The device** (step 5, the maintainer), all « passt »: MACHINES + PUNCH adds the bass an octave below the arpeggio,
  its LED lit while MACHINES is held; MACHINES + GATE up and down, its LED; PUNCH makes the bass as loud as the square;
  SWEEP 120 on a low note a kick from above, SWEEP 20 from below; CONTOUR 59 (1/32) slows with the tempo from 120 to
  90 BPM and stays in time; SHAPE 5 (OCT) at CONTOUR 116 a single tone; a trig held + MACHINES + PUNCH: only that step
  with the bass; up-down in the sound and that lock kept through a project's save and reload.
- **A question on the device:** at CONTOUR 100 the arpeggio seemed to slow with the tempo. The free part does not
  depend on the tempo: the package's core gives the same samples at 120 and 90 BPM for CONTOUR 64, 100 and 127 (and
  differs, as it should, at 41 and 59), the device the same bits as that core (§5). What follows the tempo is the
  restart at every trig. Heard on one note at CONTOUR 100 with the tempo moved from 120 to 60 BPM while it rings:
  « passt, flirren bleibt gleich ».
- Not measured: the CPU page (this build has none).

## 7. The level: TONE's output stage (2026-11-15)

**The maintainer, on the device:** « die Lautstärke ist viel zu hoch ». From the proof's own measure (§5.1, note 60, the
first 100 ms): a square's peak was TONE's (−18.1 dB), but its RMS −19.1 dB, 5 dB above TONE's −24.1 and 8 to 13 dB
above PERC, METAL and CHORD. A square stays near full scale, so its RMS is close to its peak, and the 6 dB that lifted
SOLID and SWARM (both quieter than TONE) were too much here. (A rough comparison: the stock machines' short default
DECAY already falls within those 100 ms.)

**The maintainer's choice (2026-11-15): the 6 dB out.** `chips_update` sets PUNCH's output stage `+0x2a4` to TONE's
`0x20000000`, PUNCH on or off; the core and its bits unchanged. Expected, 6 dB below §5.1: a square −24.1 / −25.1 dB
(peak / RMS), the bass with PUNCH off −20.7 / −24.7, with PUNCH on about −18.0 / −25.8; the cost unchanged.

- The ColdFire object in the interpreter as the voice loop calls it (§4.3's proof, `0x2a4` now `0x20000000`): the same
  bits as the host core in 14 400 blocks, the chain's words TONE's, MACSR given back.
- `test_chips.py`: the chain's check now asks for TONE's stage on both tracks.
- The build: CHIPS alone, `.syx` `0ef37afe…`, MAIN OS `71daddea…` (elektron-firmware-tool: checksums and HMAC ok).
- `test_chips.py --only chain,measure`, the maintainer's run of 2026-11-15: ALL OK. The chain's words and the
  output stage TONE's block for block; PUNCH acts (peak −18.1 dB, without −24.1). Peak / RMS, note 60, the first
  100 ms: a square −24.1 / −25.2 (TONE −18.1 / −24.1), a narrow pulse −24.1 / −25.2, sync −24.1 / −25.3, the bass with
  PUNCH off −20.7 / −24.8, with PUNCH on −18.1 / −25.8, m7 at 50 Hz with the bass −20.7 / −24.8: the RMS now at TONE's
  within about 1 dB. The cost unchanged (a square 1 672 instructions a block).
- **On the device, the maintainer:** « ist chips eine oktave höher? … lautheit ist immer noch nicht gleich » (CHIPS at
  DECAY 100 against TONE's own short DECAY in the test asked for, an unfair comparison).
- **`test_chips.py --only compare`** (added: every machine at note 60 and DECAY 127, 0.5 s from the trig, the
  fundamental by autocorrelation and ITU-R BS.1770's loudness, K-weighted, ungated; the maintainer's run of
  2026-11-15): TONE −22.8 LUFS, fundamental 261.6 Hz (note 60.0); PERC −21.7 (+1.1), 134.6 Hz; METAL −21.2 (+1.6);
  CHORD −30.5 (−7.7), 130.7 Hz (note 48.0); CHIPS a square −25.5 (−2.7), 261.6 Hz (note 60.0); a narrow pulse −28.1
  (−5.3); sync (COLOR 120) −24.4 (−1.6; its autocorrelation finds the synced overtone, 1 064 Hz); the bass with PUNCH
  off −25.2 (−2.4), with PUNCH on −24.3 (−1.5); m7 at 1/16 −25.3 (−2.5). **CHIPS plays TONE's pitch** (PERC and CHORD
  sound an octave lower); with the same envelope CHIPS is now about 2.5 dB quieter than TONE.
- **The maintainer's choice (2026-11-15), after the comparison:** « lass es so, passt schon »: TONE's output stage
  stays (no lift of the measured 2.5 dB).

## 8. SHAPE: CHORD's chords; the display of Chord and Arp (2026-11-15) `[FAIT en émulation]`, Unicorn ALL OK, device ok (2026-11-16); the chords replaced by Plaits' again in §10

The maintainer, after the device: « die shape anzeige der akkords ist mit 0-127 absolut nutzlos; contour auch »;
asked to check whether CHORD's chords, which have a display, could be taken; then: 0–2 are CHORD's unisons (2x, 3x,
4x), one tone in CHIPS; « ja, bau es so ».

### 8.1 The chords: CHORD's table at run time

- CHORD's SHAPE (descriptor 72, `0x4010eca0`: 0..37, default 3, CC 17) picks a row of four ratios to the root in
  `0x4012142c` (38 × 4 `int32`, Q26; notes/42 §3). Read from the official 1.13: rows 3..37 are exact powers of
  2^(1/12) (each ratio within 0 of `round(2^(n/12) × 2^26)`), the root first, the others rising, 1 to 19 semitones
  (3 `0 3 7 12`, 4 `0 4 7 12`, 7 `0 3 7 10`, 10 `0 4 7 11`, 13 `0 3 7 14`, … 36 `0 5 12 17`, 37 `0 7 12 19`); rows
  0..2 (CHORD's unisons, its detune) hold ratios near 60.
- CHIPS reads the row on the device, as CHORD does (`chord_set`, only when the knob's whole value moves): rows 0..2
  one tone (the mono synth: the arpeggio plays the root alone), rows 3..37 four tones, each ratio turned into
  semitones by counting the thresholds 2^((k + 0.5)/12) below it (`SEMI_T`, 36 of them). Nothing of CHORD's table is
  in the repository; the generator holds only the thresholds. The arpeggio, up and up-down, the bass an octave below
  the tone it plays and the sweep are unchanged; up-down runs 0 1 2 3 2 1.
- The knob: `min 0`, `max 37`, default 3 (CHORD's; 0 since §9); the word is 8.8 as every knob's, CHIPS takes its whole part.
  A word above 37 (the OS gives none) plays row 37.

### 8.2 The display

A track's parameter object (vtable `0x400fd134`) shows a knob's value through three entries, each with the knob's
descriptor: +60 `0x4000a70e` the text (the value window's fallback, the TRACK + knob popup, the locks), +64
`0x4000a66a` a value drawn instead of the text in the value window, +68 `0x4000a6b0` the picture (read in the OS:
each takes the descriptor's interface object `0x4004df40(d)`, 100 bytes from `0x40a71754`; the build gives the added
machines' descriptors SNARE's objects). The value window (`0x4001d818`) draws the picture at (32, 19), then the value
at (96, 34): the drawn one if the object has one, else the text in the 16-pixel font, centred.

- CHORD's SHAPE has its own drawn value: `0x4004611e` draws a sprite of the chord's name, frame (value >> 8) of the
  list at `0x40fe40f4`, centred on (x, y + 3); its text and picture come from its object too.
- CHIPS goes in front of the three entries (chain hooks: `knob.text`, `knob.draw`, `knob.picture`, each calls the
  entry behind it, the stock one or a part's) and hands every descriptor on but two of its own:
  - **Chord** (its first descriptor + 1): the three entries with CHORD's object (descriptor 72), as `0x4000a70e`,
    `0x4000a66a` and `0x4000a6b0` do for CHORD; the value's check stays the object's own (+24, `"ERR"` for a value
    the descriptor does not take).
  - **Arp** (+3): the text `OFF` (until §9), `1/4`, `1/4T`, `1/8`, `1/8T`, `1/16`, `1/16T`, `1/32` (nine values each, as the
    tempo), then the free tempo in whole Hz (`16Hz` .. `64Hz`, `FREE_HZ`, rounded); in the value window the same
    text in the OS's medium font (7 × 9, `0x4014120c`), centred on x, 6 rows above y, as Chord Keys draws its labels
    (notes/42 §12.4): the 16-pixel font holds three characters in the 64-pixel box and has no lowercase. Its picture
    stays SNARE's CONTOUR's, as before.
- The three entries are held by four vtables (`0x400fd108`, `0x400fd170`, `0x400fd1d8`, `0x400fd240` for the text;
  the same for the other two); CHIPS takes the track parameters' table only. `compose.py` checked that a vtable
  use's stock method is referenced once; a use now names the other tables in `shared`, and the check wants exactly
  those (`package_writes`).
- Chord Keys (tweak 45, not offered) takes `0x400fd170` and `0x400fd174` as well: the two together are a conflict by
  their bytes, as before.

### 8.3 Proven so far

- The tones: `chord_set` on the host, CHORD's table from the official 1.13: rows 0..2 one tone, rows 3..37 the
  table's semitones, all 38 equal.
- `tools/gen_chips.py` writes the tables and the object; `compose.py --compare-ld` composes CHIPS alone, next to
  SAMPLE and next to SAMPLE, SOLID and SWARM, the relocator and `ld` identical, the firmware tool's checksums and HMAC
  ok; in the image the three entries point into CHIPS's code, which compares with its descriptors (77 and 79 alone)
  and jumps to the stock entries otherwise.
- `_scratch/chips-machine/step2/prove.py` (now builds `pkg_host` and `dev.elf` from the package and reads CHORD's table
  from the official firmware): A. the package's core equal to step 1's chosen variant wherever both play the same
  chord (one tone, `0 3 7 10`, `0 4 7 11`; any chord with the arpeggio off): 49 clips of the listening page (21
  left out: Plaits' other chords), 264 runs of the matrix, 8 random sequences with the chords moving within those
  three; B. the ColdFire object in the interpreter with CHORD's table at `0x4012142c`, six tracks, SHAPE across
  0..37 and above: every block equal to the host core, DECAY, the chain's words, MACSR. 7 ok, 0 FAIL.
- `tools/emu/test_chips.py` updated: the host core given CHORD's table read from the stock MAIN OS; the core cases
  every SHAPE 0..37, a SHAPE changing during a note, a word above 37; a new part `display` (the OS's value window
  and the text path for CHIPS's Chord against CHORD's SHAPE, value for value; its Arp's text and how it is drawn; the
  76 stock descriptors and CHIPS's other knobs unchanged; next to SAMPLE, SAMPLE's as without CHIPS). `--dry` ok.
- **The maintainer's Unicorn runs (2026-11-16): ALL OK** with `--only startup,core` and `--only display,next`. The
  first run of `display` stopped in the test, not in CHIPS: the window's object check of a value (vt[24],
  `0x4000c0a6`) asks, for the descriptors whose flags (`0x4005a85e`, `0x4010dce0 + 56 d + 24`) have bit 16 (41 of
  the 76, 0 among them), the track behind the object (`obj + 4`, through vt[52], `0x4000a830`), and the test's object
  has none (a read at address 0). Since then the check accepts the value there too, as the text path did already,
  and a window the test cannot build must stop at the same place in both builds. 12 of the 304 stock windows stop
  so, those of 15, 32 and 42 (PITCH): in the drawing function `0x40071c10`, its second argument null here (a read at
  address 4), in both builds alike; the other 292 and all 20 of SAMPLE's are the same pixels, sprites and texts.
  Not rerun since §8: `inputs`, `chain`, `tracks` (the six tracks are in the interpreter's proof above), `compare`,
  `measure` (the costs in the manifest are from before §8).
- **The device (the maintainer, 2026-11-16)**, `build/model-cycles_OS1.13-chips.syx` (`cd43f1ec…`): a CHIPS track,
  SHAPE turned through (CHORD's names), CONTOUR turned through (OFF, the divisions, Hz), PITCH's window (one of the
  three windows the test cannot build), the arpeggio from SHAPE's fourth position: « passt alles. schriftgröße ist
  gut ». The rest (the names as CHORD's, the tones) is the emulation's: the same sprites as CHORD's, the core exact
  against the host for every SHAPE.

## 9. CONTOUR without OFF (2026-11-16) `[FAIT en émulation]`, Unicorn ALL OK, device ok

After the device test of §8 the maintainer: « jetzt gibt es zwei stellen um den arp zu stoppen … man kann mit contour
und mit shape den arp "ausschalten" ». So since step 1 (tempo 0 off, OCT one tone), and both gave the same: the root
alone; a SHAPE locked to 0 does what a CONTOUR locked to 0 did. Offered: CONTOUR without its OFF, SHAPE alone choosing
one tone or a chord, the defaults a plain mono synth (Chord 0, Arp 1/16); the alternative, CONTOUR's OFF holding the
whole chord, left out (four oscillators, and Plaits' chord mode was dropped as « ohne Mehrwert », §2). « Ja, OFF
raus ».

- `chips.c`: the arpeggio's clock runs whenever the chord has more than one tone (`nn > 1`), at every CONTOUR; 0 is a
  division too, `MIX_Z[0]` was 0 already (1/4): 1/4 holds 0 .. 9, the other divisions 9 values each, unchanged.
  `c_contour` starts at -1 (it started at 0, the tempo's change made the first rate anyway). Arp's text: no "OFF".
  Code 8 464 bytes (−32).
- The manifest: Chord's default 0, Arp's 41 (1/16, the middle of 37 .. 45); the description and the display's `why`.
- `tools/emu/test_chips.py`: `KW` the new defaults (one tone, 1/16), `arp_want` 1/4 at 0; the cases named for "the
  arpeggio off" now one tone. `_scratch/chips-machine/step2/prove.py` A unchanged (where step 1's arpeggio is off it
  gives the package SHAPE 0, one tone: the same root as before), B on the new object: 7 ok, 0 FAIL; render 1 673
  instructions a block (median). Composed alone, next to SAMPLE and next to SAMPLE, SOLID and SWARM: relocator and
  `ld` identical, checksums and HMAC ok; `build/model-cycles_OS1.13-chips.syx` `607efea1…`, MAIN OS `86b7ffd5…`.
- The maintainer's Unicorn run (2026-11-16, `--only startup,core,display`): ALL OK; a change of machine gives CHIPS
  `[64, 0, 64, 41, 64]` (Wave, Chord, Sweep, Arp, DECAY), the core exact in its 114 cases (CONTOUR 0 now 1/4), Arp's
  texts from `1/4` at 0; the 12 stock windows the test cannot build as in §8.3.
- The device (the maintainer, 2026-11-16, `607efea1…`): a fresh CHIPS track one tone with CONTOUR at 1/16, CONTOUR's
  left end 1/4 and no OFF, the arpeggio at 1/4 from SHAPE's fourth position: « ja, passt ».
- The maintainer's question afterwards: a pattern whose CHIPS track had alternated between two tones now plays four
  with a major chord. Before §8 the chords were Plaits' eleven folded into one octave, the doubled tones dropped (OCT
  `0`, 5 `0 7`, sus4 `0 5 7`, m `0 3 7`, m7 `0 3 7 10`, m9 `0 2 3 10`, m11 `0 3 5 10`, 69 `0 2 4 9`, M9 `0 2 4 11`,
  M7 `0 4 7 11`, M `0 4 7`; SHAPE 0..127 in eleven zones of 11 or 12 values); CHORD's rows 3..37 all have four
  different tones (its major `0 4 7 12`), none two: the nearest to Plaits' 5 is row 37, `0 7 12 19`. A pattern saved
  before §8 keeps its SHAPE number, which now names a row of CHORD's (above 37: row 37).

## 10. Plaits' chords again, one a step and named (2026-11-16) `[FAIT en émulation]`, Unicorn and device ok

After §9 the maintainer: « ich glaube ich will zurück zu den plaits akkorden. die haben mir besser gefallen » (CHORD's
have four different tones each, its major `0 4 7 12`; a pattern that had alternated between two tones, Plaits' 5,
played four). Back, with what §8 was for, a display that names the chord:

- The chords: Plaits' eleven as before §8 (§9 lists them), folded into one octave and their doubled notes dropped as
  `ChordBank::Sort` and `Reset` do; `tools/gen_chips.py` writes `ARP_T` (11 × 4 tones), `ARP_N` and `CHORD_NAME`
  from `chord_bank.cc`'s names and notes (MIT, credited in `THIRD-PARTY-NOTICES.md` again). CHORD's table is no
  longer read; `chips_host_chords`, `chord_set` and the voice's `c_shape`, `nn`, `tone[4]` are gone (24 bytes a voice).
- SHAPE: one step a chord, 0–10 (the knob's `max` 10; before §8 eleven zones of 0..127). The agent's choice, not
  asked: as CHORD's knob, every chord one click, and patterns made before §8 or since play another chord either way.
  OCT (0) is one tone, the mono synth and the default; a word above 10 plays M.
- The display: Chord's text and its value in the knob view the chord's name in the medium font, as Arp's; Chord's
  picture the stock one (SNARE's SHAPE object, as Wave's and Sweep's are SNARE's) at the value spread over 0..127
  (`(c × 127 + 5) / 10`), so that it runs across as before; CHORD's interface object no longer used.
- Proven: `_scratch/chips-machine/step2/prove.py` A now compares every one of the listening page's 70 clips (none left
  out: step 1's zone of a chord is the package's step), the matrix and the random sequences, bit for bit against step
  1's core; B on the new object, six tracks with SHAPE 0..10 and above: 7 ok, 0 FAIL, render 1 300 instructions a
  block (median). Composed alone, next to SAMPLE and next to SAMPLE, SOLID and SWARM: relocator and `ld` identical,
  checksums and HMAC ok. Code 8 176 bytes (−288), variables 992 (six voices). `tools/emu/test_chips.py`: the cases
  every chord, the display part the eleven names, drawn once in the medium font, and the picture's one call at the
  spread value (a hook on the stock `0x4000a6b0`). `build/model-cycles_OS1.13-chips.syx` `bd9971b4…`, MAIN OS
  `08ca335e…`.
- The maintainer (2026-11-16), after the Unicorn run (`--only startup,core,display`) and the device (`bd9971b4…`:
  SHAPE turned through, the eleven names, OCT one tone, 5 two, M three): « passt, alles ok » (the run's output not
  pasted).

## 11. SHAPE in zones and the big font, CONTOUR in the narrow big font (2026-11-16) `[FAIT en émulation]`, Unicorn and device ok

The maintainer after §10 on the device: « shape: große systemschrift verwenden in der auch die ganz normalen werte
0-127 angezeigt werden »; « bei shape sind die reglersteps zu klein, das ist zu fummelig einzustellen »; for CONTOUR
a look at CHORD's COLOR, which shows two lines at some values (84) and big numbers elsewhere, and a proposal first.

- What the OS has `[FAIT]` (read in the official 1.13; nothing of it in the repository): the fonts are descriptors
  `{w, h, widths, offsets, columns}` (`w` × `h`, the tables one entry a character code, a glyph's offset 0 when it
  has none): `0x401429ec` 16 × 22, the value window's numbers (capitals, digits, some signs, and `m` alone of the
  small letters), `0x40141b08` 12 × 22 the same in narrow (capitals, digits, no `m`; the OS draws with it through
  `0x40071c10`), `0x4014120c` 7 × 9 and `0x40140ab0` 5 × 9 with small letters, `0x40143d28` 6 × 10, and three of
  3 to 4 × 5 to 6. The value window (`0x4001d818`) writes the text of `vt+60` in the big font at (`0x60`, `0x22`),
  centred, when `vt+64` gives 0. CHORD's COLOR (the draw `0x40050168`) writes its value as a number in the big font,
  except at 32, 62, 74 and 84: there a picture of 48 × 22 from the OS's sprites (`0x40fe3e98`, `0x40fe38f0`,
  `0x40fe36e8`, `0x40fe3f78`, drawn 11 rows up), two lines: the root position or the first, second, third
  inversion, and below, small, the value in brackets. Elektron's pictures: not taken.
- Proposed (variant A taken, « den rest wie vorgeschlagen »): SHAPE eleven zones of 0..127 as before §8 (OCT 0–11,
  5 12–23, SUS 24–34, m 35–46, m7 47–58, m9 59–69, m11 70–81, 69 82–93, M9 94–104, M7 105–116, M 117–127; patterns
  made before §8 play their chords again), the name written by the window in the big font as a number (`vt+64`
  gives 0; at most 3 characters, sus4 as `SUS`); CONTOUR in the narrow big font, one line where a number goes:
  `1/4` .. `1/32` (`1/16T` 60 pixels), `16HZ` .. `64HZ` (capitals: the font has no small letters). Variant B (the
  free tempo as plain numbers, the divisions in two lines of 9 to 10 pixels as CHORD's COLOR) not taken.
- `chips.c`: `chord_of(shape)` = `(clamp(shape, 0, 127 << 8) × 11) >> 15`, for the core and the text; the picture
  hook gone (the knob's picture the stock one at its value), `chips_ui_draw` gives 0 for Chord and draws Arp's text
  in `0x40141b08` at (x, y); `CHORD_NAME` from `tools/gen_chips.py` (`SHOWN`: sus4 → SUS). The manifest: Chord's
  range the default 0..127, two vtable uses (`knob.text`, `knob.draw`).
- Proven: `prove.py` A (step 1's SHAPE word as it is, OCT where its arpeggio is off): the 70 clips, the matrix, the
  random sequences bit for bit; B six tracks: 7 ok, 0 FAIL, render 1 278 instructions a block (median). Composed alone,
  next to SAMPLE and next to SAMPLE, SOLID and SWARM: relocator and `ld` identical, checksums and HMAC ok. Code 7 846
  bytes. `test_chips.py`: the core at every zone's ends, the knobs moving across 0..127; the display: Chord's text for
  all 128 values, its window at the zones' ends (the name written once by the window, in the big font, at the
  number's place; the stock picture called once at the value), Arp in the narrow big font.
  `build/model-cycles_OS1.13-chips.syx` `f6a0d95b…`, MAIN OS `3db03b31…`.
- The maintainer (2026-11-16), after the Unicorn run (`--only startup,core,display`) and the device (`f6a0d95b…`:
  SHAPE's names in the big font and its steps, CONTOUR's texts in the narrow big font, `1/16T` too): « all ok » (the
  run's output not pasted).

## 12. The card (step 6, 2026-11-16) `[FAIT en émulation]`, flashed from the page: ok

- `tools/gen_chips.py --cycles` composes CHIPS alone into `tweaks/model-cycles_OS1.13/84-chips.json` (131 writes,
  283 conflicts computed, none with a card offered that is not composed: so no excludes). The other composed tweaks
  regenerated by their generators, each with one conflict more, `chips` (17 files, nothing else changed).
- `tools/gen_flasher_tweaks.py`: the FEATURES entry after SOLID (`cat` sound, `package` chips, `credit` based on
  pichenettes/eurorack, `license` `LICENSE-Plaits`, served as `docs/flasher/LICENSE-Plaits.txt` from
  `tweaks/model-cycles_OS1.13/LICENSE-Plaits`), `experimental`; OFFERED; `tweaks.js` (eighteen cards).
- `docs/flasher/app.js`: the card's texts (`FEAT.chips`, `credit_name` Plaits), its guide link, Émilie Gillet's
  credit extended to CHIPS; `REF_MAINOS` and `REF_MODS` regenerated.
- The guide: section 5 CHIPS (the later ones renumbered), CHIPS in every other card's list of mods it goes with;
  release 0.68; the stamps `2026-11-16-01`; README, BUILD.md, PROVENANCE.md, REGISTRY.md, AGENTS.md.
- `tools/webflash_smoke.js` (the card in Machines, alone, with SAMPLE, with SOLID, CHORD Tables, Crush and
  Transpose, every card ticked, its credit and license, its Experimental tag) and `tools/webcompose_synth.py`
  (CHIPS alone, before and after SAMPLE, with SOLID, CHORD Tables and Crush, the full set).
- Composed with every card (`--machines sampler,solid,chips,chordtables,digidelay,pots,smpfilter,crush,ring,reso,eq
  --cpu --resample --transpose --perform --with control-all-config,trig-preview,trig-cond-order`): MAIN OS
  `242fccca…`, checksums and HMAC ok. Not tried on the device in that build, nor flashed from the page.
- The device (the maintainer, 2026-11-16): the page served locally (`python3 -m http.server` in `docs/`), the test
  asking for every card ticked, flashed onto the Model:Cycles; CHIPS's names and speeds, the bass on MACHINES + PUNCH:
  « habe gerade von der lokalen seite auf gerät geflasht, alles gut ».
- The home page's list: CHIPS after SOLID (« ja, soll im flasher erscheinen », to the question whether it goes into
  the home page's list), `09 CHIPS / CHIPTUNE` on the screen, the knobs, MACHINES, PUNCH and GATE lit.
- `tools/webcompose_check.sh` on the official file: 78 of 78 selections identical to `compose.py`, five with CHIPS.
  `tools/webflash_smoke.sh` on both official files (npm is closed in the agent's sandbox), the maintainer's run
  (2026-11-16): « all ok ».
- Not done: CHIPS's own pictures (it shows TONE's), a load on the CPU page.

## 13. Left to do

- **Step 5:** the CPU page on the device (a build with `--cpu`), if the maintainer wants the load measured there.
- **Step 6:** `tested` in its own commit (the page's build ok on the device, §12); CHIPS's own pictures.
- The maintainer's: the knobs' names, DECAY's default, the order 84 (Chord's and Arp's defaults decided, §9).
- For the card (step 6): CHIPS claims k 32 and the switches as SAMPLE does; the page composes machine cards together
  through the shortcut layer (`sampler,chips` composes), but the conflicts computed for CHIPS alone list SAMPLE's,
  REF2's and lfo-plus's tweaks by those claims: to check when the card comes.
