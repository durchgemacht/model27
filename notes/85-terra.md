# 85 — TERRA: wave terrain synthesis after Plaits' WaveTerrainEngine (steps 1 to 6, 2026-11-17, English)

The maintainer's plan (2026-11-15, notes/83, notes/82): one machine for each Plaits engine the Cycles lacks. After a
listening page of the original Wave Terrain (outside the repository, `_scratch/plaits-listen/wave-terrain/`: « klingt
gut ») they asked for the machine. It follows the path of SOLID, SWARM, CHIPS and Max Saw: (1) the fixed point on the
host against a float reference, (2) the package, (3) the proof in Unicorn and the load, (4) digiemu, (5) the device,
(6) the card, the guide, the release. Steps 1, 2, 3, 5 and 6 are done (§10), digiemu (4) is left open: the device came first; the card is
experimental until it is flashed from the page. Step 1's programs, renders and listening page live
outside the repository (`_scratch/terrain-machine/`), step 2's proofs next to them (`_scratch/terrain-machine/step2/`).

Source: Mutable Instruments Plaits by Émilie Gillet, MIT (eurorack `08460a6`, stmlib `e3bd7c9`):
`plaits/dsp/engine2/wave_terrain_engine.cc` (the five terrain formulas, the path, the AUX output),
`plaits/dsp/oscillator/sine_oscillator.h` (the FastSineOscillator's quadrature, the "magic circle") and the wavetable
data `wav_integrated_waves` (`plaits/resources.cc`, banks 0 to 2), which TERRA's terrains 6 to 8 read. The algorithms
are written anew in fixed point; no line of the C++ is copied. The wavetable data are copied as they are by the
generator (LICENSE-Plaits next to the package).

## 1. In short

- **What it does:** a point goes round a path over a surface z = f(x, y); the height under it is the sound. Eight
  surfaces: five formulas and three made of Plaits' wavetables (x the wave, y the place in it). One turn a period.
- **The knobs** (the maintainer's layout, 2026-11-17, « Ja, beides »): COLOR the surface (Plaits' HARMONICS, the
  eight surfaces cross-faded between neighbours), SHAPE the path's radius (TIMBRE, 0.1 to 1.0, smaller at very high
  notes), SWEEP its shift (MORPH, the centre from x = −1 to +0.9, the path narrowed towards the edge), CONTOUR the mix
  of AUX into OUT (Plaits' second output). Name: **TERRA** (the maintainer's choice of the proposals TERRA, ORBIT,
  TOPO, RIDGE, MESA).
- **Step 1** (§3): the fixed-point core against Plaits' unchanged engine and a model in double; the surfaces within
  3.7 · 10⁻⁴ of Plaits' (−69 dB), the clips 74–85 dB from the model, Plaits' harmonics within 0.16 dB, the pitch within
  0.023 cents. The maintainer listened and chose (§2): the surfaces cross-faded as in Plaits (A), **no oversampling**,
  the fourth knob mixing AUX in. « hörseite passt ».
- **Step 2** (§4, §5): the package `tools/machines/terra/` and `tools/gen_terra.py`, composed alone into
  `86-terra.json`; the package's core gives step 1's bits; its committed object, in a ColdFire interpreter as the
  voice loop calls it, gives the host core's bits. The wavetable data (50 688 bytes) did not fit the payload's code
  window next to every offered card: the builder learnt **far tables** (`.far*` sections, §5), placed at the start of
  the package's variables' room and copied there at boot like the rest. With them the whole offered set fits.
- **Step 3** (§7): `tools/emu/test_terra.py` on the OS's own code, the maintainer's run of 2026-11-17: ALL OK. Cost,
  instructions a block of one voice: 3 325 at the defaults (one surface), 5 953 to 7 064 between two surfaces, 7 941
  with AUX mixed in, 8 838 at most (COLOR moving with AUX), 185 paused; TONE 5 291, CHORD 8 300; six tracks 1.34 × six
  TONE. Level: TONE's peak, loudness within −3.9 to +2.4 LU of TONE.

## 2. The maintainer's decisions (2026-11-17)

| Point | Decision | Their words |
|---|---|---|
| How COLOR picks the surface | first B (eight zones, one surface each, for the load), then withdrawn: decided after measuring; after the measures (§3.4) and the listening page **A, as Plaits** (cross-faded, two surfaces a point) | « dann nehmen wir die entscheidung zurück und warten erstmal ab », then « A mit 1x » |
| Oversampling | none (Plaits computes two points a sample) | « das klingt nur hörbar anders in tonhöhen die eh schon komplett unangenehm sind » |
| The fourth knob | AUX mixed into OUT, linearly | « vierter knopf mixt aux rein » |
| Level | as the last machines (Max Saw's output stage, §4.3) | « pegel erstmal so wie die letzten machines » |
| Assembly | « assembler kannst du direkt machen »: tried, not kept (§3.5) | |
| Knobs and name | COLOR surface, SHAPE radius, SWEEP shift, CONTOUR AUX; TERRA | « Ja, beides » |
| The wavetable data | kept exact, outside the code window (§5) rather than 8-bit | « dann daten auslagern » |

## 3. Step 1: the core on the host (`_scratch/terrain-machine/`)

### 3.1 The arithmetic

Every product through the EMAC in signed fractional mode (`mac.l` + `movclr.l`, MACSR `0xa0`), on the host the same
arithmetic in `__int128`. Coordinates Q29, heights Q30, the path's oscillator Q30, phases uint32.

- **The path:** Plaits' magic circle (x += e y; y −= e x), e = 2 sin(π f) from a 7th-order series once a note change;
  Plaits uses an approximation (Fast2Sin, up to 7 cents off) and computes for 47 872 Hz (4.6 cents high at 48 kHz).
  The invariant x² + y² + e·x·y is set back to 1 when it drifts by 2⁻¹² (over ten minutes it drifted by 7.6 · 10⁻⁶).
- **The radius:** 0.1 + 0.9 · T · (1 − (8 f₀)²) times 1 − 2 f₀ (Plaits' attenuation and FastSineOscillator's), the
  shift 1.9 M − 1, the surface min(1.05 H, 1) · 6.9999, all ramped per sample across the block of 32.
- **The terrains:** Sine from the Cycles' own table (`0x8000eee4`, 257 words, interpolated: the device reads it in its
  SRAM, no cache line), Squash(Sine(p), 2) one table over the period, the divisions as a 64-entry reciprocal table
  after normalizing (`ff1`), the wavetable terrains on Plaits' data, differentiated as Plaits does, clamped outside
  −1 … 1 (Plaits reads past the ends there).

### 3.2 Against Plaits and against the model

| Check | Result |
|---|---|
| each surface on a 512 × 512 grid, the core against Plaits' own `Terrain()` (unchanged, float) | at most 3.7 · 10⁻⁴, RMS about 7 · 10⁻⁵; the wavetable surfaces exact |
| the formulas in double against Plaits' `Terrain()` | within 7 · 10⁻⁵ (Plaits' sine table) |
| the clips against the model in double of the same structure (with the core's own step) | 74–85 dB SNR, constant over the clip |
| the still clips against Plaits' engine (its note moved by the 4.6 cents) | harmonics 1–16 within 0.01–0.16 dB |
| the pitch (notes 0–127 in quarter tones) | within 0.023 cents of exact |

### 3.3 The listening page

`_scratch/terrain-machine/index.html`: (1) the original against the fixed point, (2) A, B, B with a block's
cross-fade, C (plateaus cross-faded only around the borders), (3) 2× against 1×, (5) the AUX mix at 0/32/64/96/127,
(6) the cost table. 131 WAVs checked (length, peak, RMS, no clipping), every one on the page.

### 3.4 The load of the variants (interpreter, the core alone, instructions a block)

| Choice | 2× (Plaits) | 1× |
|---|---|---|
| A between two surfaces | about 10 200 | 5 081 … 6 228 |
| B, C on one surface | about 5 900 | about 2 900 |

### 3.5 Assembly, tried

A loop of two surfaces (1 and 2) written in ColdFire assembly (`_scratch/terrain-machine/terrain_cf.S`, kept there as
a record): the same bits as GCC's loop, but slower, 4 957 instructions a block against 4 767. GCC keeps nearly
everything in registers here; the work is table reads and products that depend on each other. What a hand-written
loop could still save (the step and two values spilled, a branch around the reciprocal's shift) is about 10 to 15
instructions a sample. Also tried and dropped: separate loops with and without the AUX mix (dearer through the
registers' allocation). Kept: the mix after the loop, only in blocks where it is above 0.

## 4. Step 2: the package (2026-11-17)

### 4.1 Files

| File | What |
|---|---|
| `tools/machines/terra/terra.c` | step 1's core with the chosen variant only (A, one point a sample, the mix), its host entries under `TERRA_HOST`, the glue for the voice loop |
| `tools/machines/terra/terra_tables.h` | generated: the terrains' constants, `EXP2_T`, Squash, reciprocals, the host's copy of the Cycles' sine, Plaits' wavetable data (`WT_T`, a far table on the device) |
| `tools/machines/terra/terra.o` | the committed object (`ld -r`, m68k-elf-gcc 16.2) |
| `tools/machines/terra/manifest.json` | machine `TERRA`, TONE's picture (4) until it has its own, DECAY 64; knobs Terra Surface / SURF 0, Terra Radius / RAD 64, Terra Shift / SHFT 64, Terra Aux / AUX 0; no claims; order 86 |
| `tools/machines/terra/LICENSE`, `LICENSE-Plaits` | MIT (model27), Plaits' MIT notice with what was taken |
| `tools/gen_terra.py` | the tables (the wavetable data from Plaits' `resources.cc` with `--plaits`, else kept, checked against their SHA-256 at `08460a6`), the object, with `--cycles` the OS's sine checked and the composed tweak `86-terra.json` |

The 19 other composed tweaks regenerated by their generators: each gained the conflict `terra`, nothing else changed.
`REGISTRY.md` regenerated.

### 4.2 The glue

As Max Saw's (notes/84 §9.2): one voice and one set of knobs a track in the package's variables; `terra_update` sets
up the stock amp chain as TONE does (DECAY through `LUT_DECAY`, the envelope's and PUNCH's words in the block of
`+0x38`), computes the note as every machine (the trig's note + PITCH − 64 + FINE), reads COLOR / SHAPE / SWEEP /
CONTOUR, and makes a fresh voice when the track took the machine (the mark `TRA1` at `+0x2c`); `terra_render` pauses
while the envelope is closed and no trig comes (out 0, the voice stands still), else saves MACSR, runs the core onto
the bus, then AMP_ENV, VCA and PUNCH, and gives MACSR back. A trig does not reset the path (as Plaits).

### 4.3 The level `[HYP]` until step 3

Max Saw's output stage: `+0x2a4` = `0x7fffffff` (TONE's × 4). TERRA's core is Plaits' engine scale (its heights and
AUX within ±1); it goes onto the bus as Q29 (`TERRA_OSH` 2: Plaits' full scale a quarter of the bus), so a track's
output is the core's / 8: Plaits' full scale is a TONE voice at full scale − 18 dB. From step 1's clips (Plaits' level
× 0.7, RMS −5 to −14 dBFS) that should land near TONE's (−18.1 / −24.1 dB, notes/71 §6). PUNCH's drive (× 3) saturates
from 1.33 of Plaits' scale, which the core does not reach. To be measured in Unicorn and decided by the maintainer.

## 5. Far tables: large read-only tables outside the code window (2026-11-17)

**The problem.** The added machines and the builder's parts lay their code and tables out from `0x43000000` up to
`gs.STUBS` (`0x43033000`, 204 KiB); their variables start at `+0x36000`. With SAMPLE, SOLID, CHIPS, Max Saw, the
effects, the Track FX, CPU, RESAMPLE, Transpose and Perform Kit 34.7 KiB were left there. TERRA
needs 19.2 KiB of code and tables and 49.5 KiB of wavetable data: `compose.py` refused the whole set (« fltslot: code
and tables end at 0x430331b8, past 0x43033000 »). The data take no less room in fewer bits: every wave uses the whole
11-bit range of its differences.

**The way.** The boot hook clears the whole payload, from `0x43000000` to the end of the variables, then copies the
image's parts to their places (`gs.segments`, notes/60 §4); parts in the variables' room already exist (the
registrar's part after `gs.STUBS`). So a package may put large read-only tables in sections named `.far` or `.far.*`:

- `relocate.layout()` places them at offset 0 of the package's variables' room, then the variables; it returns their
  bytes as `far` and counts them in `bss`; a far section may hold no relocation of its own (the code refers to it as
  to a variable); `bundle()` adds
  `far` (hex) only when there is one, so every existing bundle stays byte for byte the same;
- `compose.place_package()` and `compile_package()` (the `ld` path: the linker script gains `.far` at the variables'
  start, before `.bss`) return the far bytes; `compose()` emits them as a payload part at the package's variables'
  address; `--compare-ld` compares them too;
- `docs/flasher/composer.js` does the same (`place()` returns `far`, the package's loop pushes it as a part).

**Where they land.** In the stock OS's unused SDRAM above the payload (STANDARD.md §3.1, notes/66 §2.2, notes/68
§16.2): below CHORD Tables' RAM claim (`0x43400000`) and SAMPLE's pool (`0x43800000`); the composer already refuses a
payload that runs into a claim. With the whole offered set (CHORD Tables too) and TERRA the payload ends at
`0x43176c58`. The image gains the data (256 292 bytes added in that build, the MAIN OS 2 000 484 bytes, under the
image's limit `0x40200000`). The
cache: the data are read from SDRAM wherever they lie (the code window is SDRAM too, copyback cached, notes/23), so
moving them changes nothing in the load; the boot copies 50 KiB more (milliseconds, `[HYP]`).

**Proven.** `compose.py --compare-ld` (the relocator against the linker, far bytes included): TERRA alone and with
SAMPLE and CHIPS, identical. `tools/webcompose_check.sh` with the official file: part 1, TERRA's 23 placements as
`relocate.place`; part 2, every selection identical to `compose.py`, among them five new ones (TERRA alone, SAMPLE
before and after it, with SOLID, CHIPS, MAX SAW, CHORD Tables and a Track FX, and the whole offered set: 180 writes,
256 292 bytes added, MAIN OS `3b98649e…`). The selections without TERRA unchanged.

## 6. Step 2's proofs (`_scratch/terrain-machine/step2/`)

| Proof | Result |
|---|---|
| `same_bits.py`: the package's core (host, Q27) against step 1's core in the chosen variant, the listening page's 56 inputs and 40 random sequences (knobs held, moved, out of range, notes, the mix) | 96 inputs, 431 250 blocks: the same bits |
| `cf_object.py`: the committed object linked with empty AMP_ENV, VCA and PUNCH, the far table at `0x43040000`, the Cycles' sine at `0x8000eee4`, run in the ColdFire interpreter as the voice loop calls it, six tracks × 400 blocks with random knobs, notes, PITCH, FINE and trigs, against the host core (Q29) | ALL OK: every block equal; MACSR given back; DECAY in `+0x250`; PUNCH's words as TONE's, `+0x2a4` `0x7fffffff`; the pause (out 0, state unchanged); a trig while paused runs the core; a fresh voice after the mark is cleared |
| `tools/gen_terra.py --cycles … --check` | tables, object, tweak up to date; the OS's sine table is sin(2πi/256) in Q31 |
| `compose.py`: TERRA alone; with SAMPLE, CHIPS; the whole offered set | ok (§5) |
| without firmware: `claims.py --check --self-test`, `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check` | ok |

Cost in the interpreter, update + render without the OS's chain: median 6 315, 6 089 to 8 087 instructions a block
with random settings; the defaults (COLOR 0: one surface) 2 590; paused 169.

## 7. Step 3: the proof on the OS's own code (prepared 2026-11-17)

`tools/emu/test_terra.py` and `tools/emu/terra_ref.c`, after test_maxsaw.py (notes/84 §10), without its switches:

| Part | What it checks |
|---|---|
| startup | the bootstrap and the boot hook, the registrar's tables, lookups, MACHINES page, records and knobs (as test_compose.py); the far table at the start of TERRA's variables' room, above the code window, byte for byte the package's after the boot hook's copy; the OS's sine at `0x8000eee4` in the SRAM the host core's |
| core | at every block not paused, what `terra_render` gives AMP_ENV = the host core (`terra_ref.c`, Q29), fed the inputs computed from memory: every surface alone and between them, SHAPE, SWEEP, CONTOUR across their range, notes 0–127, PUNCH, PITCH, FINE, DECAY, GATE, retrigs, COLOR moving and jumping, every knob moving every block; the pause and the wake; the chain called once each in order |
| inputs | COLOR, SHAPE, SWEEP, CONTOUR each change the sound |
| chain | the envelope and the chain's words TONE's block for block, `+0x2a4` `0x7fffffff` (TONE `0x20000000`); PUNCH acts |
| tracks | a change of machine (TERRA, TONE, TERRA: a fresh voice); six tracks exact and as alone; TERRA among KICK, METAL, PERC, CHORD; the stock machines without TERRA identical to the stock OS, no instruction of TERRA |
| next | next to SAMPLE, CHIPS and Max Saw (machine 7): start-up, the track as alone, the stock machines unchanged |
| compare | loudness (BS.1770) and the fundamental against TONE, PERC, METAL, CHORD |
| measure | peak and RMS over 100 ms and 0.5 s next to the stock machines; instructions a block of one voice (surfaces alone and between, AUX, PUNCH, notes, COLOR moving), paused, six tracks against six TONE, the stack |

`--dry` (no Unicorn, run here): TERRA machine 6 alone (code `0x43000000..0x43004aea`, the far table and variables
51 072 bytes at `0x43036000`), machine 7 next to SAMPLE (`0x43045520`), CHIPS and Max Saw; in each the far table in the
payload as the boot hook leaves it is the package's. The host core between surfaces 3 and 4, note 60: peak −12.1 dB,
RMS −14.9 dB of the bus before the chain (a track: the bus / 2; Max Saw's defaults −9.5 / −20.9, notes/84 §10). The
Unicorn parts stop with SIGILL in Claude's sandbox: the maintainer's run.

### 7.1 The maintainer's run (2026-11-17): ALL OK

Every part passes: start-up and the registrar alone and as machine 7 next to SAMPLE, CHIPS and Max Saw (the MACHINES
page shows `TERRA` with TONE's picture; a change of machine Chord → TERRA gives the defaults 0, 64, 64, 0, DECAY 64);
the far table at `0x43036000` alone (`0x43045520` next to SAMPLE, `0x430363e0` next to CHIPS, `0x43036344` next to
Max Saw), byte for byte the package's after the boot hook's copy; the SRAM's sine the host core's; the core exact in
63 cases, 9 804 blocks; the pause (385 blocks) and the wake; the chain called once each in order; the inputs act; the
chain TONE's block for block with `+0x2a4` `0x7fffffff`; PUNCH acts (peak −9.0 dB, without −18.1 dB); the tracks (a
change of machine, six tracks, mixed, the stock machines identical to the stock OS without one instruction of TERRA);
next to SAMPLE, CHIPS and Max Saw the track as alone.

Measured, note 60:

| | peak / RMS 100 ms (dB) | loudness 0.5 s at DECAY 127 (LUFS, against TONE) |
|---|---|---|
| TONE | −18.1 / −24.1 | −22.8 (0) |
| PERC / METAL / CHORD | −15.1 / −27.0, −14.7 / −32.3, −22.4 / −30.7 | +1.1, +1.6, −7.7 |
| TERRA, the defaults (surface 1) | −19.3 / −26.0 | −26.2 (−3.4) |
| surface 2 / 5 / 8 | −18.2 / −21.5, −18.1 / −22.2, −18.4 / −29.8 | +2.4, +0.6, −3.9 |
| between 3 and 4 | −18.1 / −22.0 | +0.7 |
| SHAPE 0 / 127 | −31.6 / −37.6, −18.1 / −23.6 | −15.4, +1.2 |
| SWEEP 0 | −18.1 / −24.7 | −1.3 |
| AUX 127 | −18.1 / −22.3 | +1.2 |
| PUNCH on | −9.1 / −18.6 | |

The fundamental 261.6 Hz (note 60.0) as TONE's; between surfaces 3 and 4 the autocorrelation takes the octave (523.2
Hz): that setting's second harmonic is its strongest (step 1, §3.2). **The level:** TERRA's peaks are TONE's (−18.1
dB) wherever the radius is full; its loudness lies within −3.9 to +2.4 LU of TONE across the surfaces (SHAPE 0, the
smallest path, −15.4: little of the surface under it). Proposed: keep it.

The cost, instructions a block of one voice (the voice loop less the muted loop), note 60, DECAY 127:

| Setting | median (most) |
|---|---|
| the defaults (surface 1 alone) | 3 325 |
| surface 5 alone / surface 8 | 6 611 (6 705) / 5 977 |
| between 1 and 2 / 3 and 4 / 5 and 6 / 6 and 7 | 5 953 / 6 156 / 7 064 / 5 977 |
| between 5 and 6, AUX 64 | 7 941 |
| COLOR moving every block, AUX 64 | 7 869 (8 838) |
| PUNCH on / note 24 / note 96 (between 3 and 4) | 6 151 / 6 173 / 6 158 |
| a trig's block (between 5 and 6) | 7 570 |
| paused | 185 |
| six tracks between 5 and 6 | 42 384 against six TONE 31 746 (1.34 ×) |

Stock: TONE 5 291, PERC 6 079, METAL 6 431, KICK 7 429, SNARE 7 158, CHORD 8 300. TERRA lies between TONE and CHORD in
every setting but one (COLOR moving with AUX: 8 838 at most, 6 % above CHORD); the stack 364 bytes below the voice
loop. The cache (the wavetable surfaces read 50 KiB of data, the loops 16 KiB of code) only the CPU page on the device
shows.

**The level, decided** (the maintainer, 2026-11-17: « Ja, so lassen »): kept as it is.

## 8. Step 4: a build for digiemu and the device (2026-11-17)

`tools/compose.py --cycles firmware/model-cycles_OS1.13.syx --machines terra --tool
../elektron-firmware-tool-main/elektron-firmware-tool`: TERRA alone as machine 6 (code 19 178 bytes at `0x43000000`,
the far table and variables 51 072 bytes at `0x43036000`), payload `0x43000000..0x43042780`, 75 584 bytes added to
the image; MAIN OS 1 819 776 bytes, SHA-256 `61ce9175…`; elektron-firmware-tool: checksums and HMAC ok, the same MAIN
OS. The file (`_scratch/terrain-machine/build/device-0.1/model27-terra-0.1.syx`, SHA-256 `95942256…`) is outside the
repository. With the CPU page (the maintainer, 2026-11-17: it should have been in the build from the start):
`--machines terra --cpu`, MAIN OS 1 822 532 bytes, SHA-256 `fab321a5…`, checksums and HMAC ok;
`_scratch/terrain-machine/build/device-0.1b/model27-terra-0.1b-cpu.syx`, SHA-256 `5bf514d0…`.


**On the device** (the maintainer, 2026-11-17, `model27-terra-0.1b-cpu.syx`): six TERRA tracks, one trig each on step
1, C4, DECAY 127, COLOR 70 (between surfaces 5 and 6), SHAPE 64, SWEEP 64, CONTOUR 64 (AUX mixed in, the dearest
steady setting in Unicorn: 7 941 a voice): the CPU page shows **CPU 67 %, PEAK 80 %**. For comparison SWARM's six
tracks showed 72 to 75 % (notes/82 §6.4).

The sound (the maintainer, 2026-11-17): « passt alles, klingt gut »; now and then the small clicks at trigs known from
the other added machines (« hatten wir schon öfter; wahrscheinlich liegt es am amp und neuen trigs »): the stock VCA
cuts at a trig and jumps at the attack (`0x400a9430`), as TONE's chain does with TERRA's output, which runs on through
the trig (notes/82 §6.5, SWARM's fix on its branch, not yet tried on the device).

## 9. No cut at a trig (2026-11-17)

The maintainer: « bau ein, ich teste hier. wir haben das ja auch schon bei weiteren machines gemacht, da hatte es
funktioniert ». As SWARM's (notes/82 §6.5): `terra_render` clears `+0x34` and `+0x38` for the call of the VCA
(`0x400a9430`) and puts them back before PUNCH, so the VCA ramps from the level it had to the envelope's over every
block instead of cutting at a trig and jumping at the attack; AMP_ENV before and PUNCH after see the flags as they are.
The core and its bits are unchanged; code 19 208 bytes (30 more).

- ColdFire interpreter (`_scratch/terrain-machine/step2/cf_object.py`, the VCA and PUNCH as stand-ins that note the
  flags): in a trig's block, an attack's block, both and neither, the VCA sees 0 and 0, PUNCH sees the flags as the voice
  has them, both are back after `terra_render`; the core against the host as before: ALL OK. `same_bits.py`: the same
  bits. `compose.py --compare-ld` identical with SAMPLE and CHIPS.
- `test_terra.py` follows SWARM's: the VCA's flags checked at every call (both 0), PUNCH's `+0x38` as the voice has
  it, the envelope compared with TONE's but for the level in a trig's block (TONE's VCA clears it), and a retrig on a
  sounding track at DECAY 127, 60 and 30: the VCA's gain frame by frame never dips and never steps. The maintainer's
  first run (`--only chain`, 2026-11-17): the chain TONE's (the level but in a trig's block) and PUNCH ok; the retrig
  check failed at DECAY 30 only by its own bound: the gain 0.397 before the trig, 0.392 at its lowest in the trig's
  block, 0.985 after, the largest step 0.019 a frame (at most 0.030). No cut (that would take the gain towards 0): in
  the trig's block the envelope decays one block more (AMP_ENV sets it full only in the next), about 1.3 % at DECAY 30,
  and the bound allowed 0.2 %. The bound now allows one more block of the decay measured just before the trig. **The
  second run (2026-11-17): ALL OK**: the lowest gain from the trig on 0.956, 0.794, 0.392 at DECAY 127, 60, 30 (at
  least 0.954, 0.792, 0.390), the largest step a frame 0.0014, 0.0064, 0.0190 (at most 0.0040, 0.0115, 0.0296).
- The test build: `--machines terra --cpu`, MAIN OS `da29c17f…`, checksums and HMAC ok;
  `_scratch/terrain-machine/build/device-0.2/model27-terra-0.2-cpu.syx`, SHA-256 `2638aee7…`.
- **On the device** (the maintainer, 2026-11-17, 0.2, trigs on the four quarters, COLOR 45, DECAY 127): « weg, keine
  knackser mehr ».

## 10. Step 6: the card (2026-11-17)

The maintainer: « karte bauen … schreibe aus sicht des nutzers », after SOLID's, CHIPS' and MAXSAW's cards
(`43231c3`, notes/84 §16).

- `tools/gen_flasher_tweaks.py`: the FEATURES entry `terra` after `maxsaw` (cat `sound`, credit « based on »
  Émilie Gillet, `pichenettes/eurorack`, license `LICENSE-Plaits`, package `terra`, `experimental`) and OFFERED;
  `tweaks/model-cycles_OS1.13/LICENSE-Plaits`, served as `docs/flasher/LICENSE-Plaits.txt`, names TERRA and the
  wavetable data next to CHIPS; `tweaks.js` regenerated (twenty cards).
- `docs/flasher/app.js`: `GUIDE_OF.terra`, `FEAT.terra` (label, `credit_name` Plaits, the short, a block per knob
  in the user's words: COLOR the surface, SHAPE the circle's size, SWEEP its place, CONTOUR the second sound), the
  credits' Émilie Gillet line extended; REF_MAINOS and REF_MODS regenerated.
- The guide: section 7 TERRA (the steps, the knobs' table with the surfaces' positions, Sound, Surfaces from step 1's
  measurements at SHAPE and SWEEP 64, Level from §7.1, Load from §8, Other mods, Tested), the later sections
  renumbered, TERRA in every other card's list; the home page lists it (`11 TERRA / TERRAIN`); release 0.72; the
  stamps 2026-11-17-04; README (twenty cards), BUILD.md (section « Machine TERRA »), PROVENANCE, AGENTS.md.
- `tools/webflash_smoke.js`: the twenty cards and rows, TERRA in Machines, its credit and license, alone / with
  SAMPLE / with SOLID, CHIPS, MAXSAW, CHORD Tables, Crush and Transpose, every card together, its tag.
- MAIN OS: TERRA alone `9f064a74…`, with SAMPLE `9810197e…`, with every card of the page `b95b1d31…` (payload
  `0x43000000..0x43176c58`), checksums and HMAC ok.

## 11. Open `[À FAIRE]`

- Flash from the page (served locally, every card ticked) on a Model:Cycles: then the card is « tested ».
- digiemu with TERRA; the wavetable surfaces and the cache under load with the other cards.
- Own pictures (TERRA shows TONE's).
- The cost of the code window: TERRA takes 19.2 KiB (16.3 KiB of it the loops, one per surface and per pair, the
  surfaces inlined); 10.3 KiB are left there with every offered card and TERRA (the next machine may need its loops
  shared, or its tables far).
