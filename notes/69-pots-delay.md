# 69 — POTS: a telephone-line delay for the delay slot (plan, 2026-10-27, English)

The maintainer, 2026-10-27, asked for the plan of porting v6 as an effect of model27's delay slot: fixed point, cost,
and the frequency shift as a third knob; the plan first, nothing built. The sound was worked out by ear with the
maintainer in a float prototype kept outside the repository, round by round (v1 to v6), with listening pages and
measurements; v6 is the sound to port. No code or data of any other product: the effect is written from a sound
brief. §1 to §11 are the plan; what was done follows from §12 on. Addresses: VA of OS 1.13.

## 1. In short

- **What it is.** A mono delay whose repeats go down an old telephone line on every pass: a skewed soft clip in the
  transmitter, a second wandering tap (scatter), a frequency shift that adds up pass after pass, random fading and
  rare dropouts, a 7-bit μ-law codec, a steep telephone band with an earpiece resonance, and a leveler. Time and Fdbk
  on their knobs, as Digital Delay (§18 of [68](68-fx-slots.md)). In v0.1 the shift is fixed at 2 Hz upwards.
- **Name** (decided 2026-10-27): **POTS**, the telephone trade's "plain old telephone service".
- **Where.** An effect package of the delay slot, id 2, on the contract of [68](68-fx-slots.md) §15 and §16: no hook of
  its own, its line the slot's.
- **Fixed point.** Samples in Q2.29, products on the EMAC in fractional mode, as SD VINTAGE does
  ([14](14-machine-sd-vintage.md)); everything that the prototype computes with `powf`, `logf`, `sinf` runs once a
  block from small tables. The level the float sound was tuned at has to be found on the device's send bus first
  (§4.1): the clip, the codec and the leveler depend on it.
- **Cost.** `[HYP]` about 6 500 instructions a block at 48 kHz (6 % of a block by the emulator's count, 3.5 % above
  the stock delay), about 4 000 if the loop runs at 24 kHz (§5). Under the composer's 10 % warning either way. The
  device's share is the open risk: the stock effects count 10 % and measure 30 % on the device (§17.4 of 68).
- **The shift as a third knob** comes after v0.1 (decided 2026-10-27): v0.1 has two knobs and is tested on the device
  first. The third parameter needs the format to grow past two parameters (68 §15.8, the standard's §3.5 "reserved");
  §6 keeps the design for then.
- **Decisions:** §10.

## 2. The sound to port: v6

Each frame, in this order (the loop is everything from the read to the write):

| Stage | v6, as the prototype computes it | In the loop |
|---|---|---|
| Send | (L + R) / 2 | |
| Read | `line[w − D]`, D in frames from Time by the stock formula, slewing by `diff / 8192` a frame, else one frame every fourth (Digital's) | yes |
| Scatter | + 0.35 × the line `D + s` frames back, s wandering 24..144 frames (linear interpolation; a new aim every 0.5..2 s, 0.5 s glide); × 0.9438798 | yes |
| Shift | a Hilbert pair (two allpass chains, 90° apart) and a phasor: `I cos φ − Q sin φ`; φ turns at 2 Hz × (1 + 0.4 (0.7 sin(2πt/7.3 s) + 0.3 sin(2πt/2.9 s))) | yes |
| Fading | × 10^(12 v / 40) dB-wise, v wandering in −1..1 (a new aim every 30..150 ms, 25 ms glide): ±6 dB | yes |
| Dropouts | × 0.125 (−18 dB) for 8..25 ms, every 1.5..5 s | yes |
| Codec | μ-law, μ = 255, 7 bits (63 steps a side), full scale 1.0; mixed out (dry) as the leveler's envelope falls from 0.01 to 0.0025 | yes |
| Receiver | high pass 350 Hz and low pass 3 kHz, each 4-pole Butterworth, peak +6 dB at 1.5 kHz (Q 1), the chain scaled so its loudest frequency passes at unity | yes |
| Leveler | envelope = the peak of the *next* block on the line (attack 0.5, release 0.0017 a block); in the loop a compressor, 3:1 above 0.25; on the echo a make-up √(0.15 / env), 0.6..2.5 | in the loop: the compressor |
| Feedback | 1.18 × (3t − t³)/2, t = Fdbk / 127 (Digital's curve, past unity at the top) | yes |
| Transmitter | `(c(5 s + 0.12) − c(0.12)) / 5`, `c(x) = x − 4x³/27` clamped at ±1.5; then a 1-pole low pass at 4 kHz and a 1-pole high pass at 200 Hz | yes |
| Write | clamped to ±2.0 | |
| Echo | the receiver's output × make-up × 1.5, the same on both channels | |

Float 1.0 is the codec's full scale; the prototype's sources peak at 0.45..0.5 on the send. The measurements that
settle the sound (all in the prototype): the decay to −60 dB after a phrase at Fdbk 40 / 64 / 90 / 100 is about
2.6 / 4.9 / 20 / 23 s, from about 110 a tail no longer dies; the codec adds 6 to 8 dB more grain in the band than the
8-bit codec of v5 and about 25 dB less above 4 kHz; a tail's end stays at about 1.5 kHz with nothing above 2 kHz;
with a loud input at Fdbk 127 the echo peaks at −5.6 dB; silence in gives exact silence out.

Settled by the maintainer (2026-10-27): the shift at 2 Hz upwards; the band from 350 Hz (a snare's body falls below
it); mono; Time slides as the stock delay's does.

## 3. What the slot gives `[FAIT]`

From [68](68-fx-slots.md) §15.3, §16.3, §17 and Digital Delay (§18, `tools/machines/digidelay/digidelay.c`):

- `process(out, in, params)` once a block in the audio interrupt: 32 stereo frames of signed 32 bits in, the same out,
  every word written; `params` → Time at +0 and Fdbk at +2, each × 256, smoothed by the OS.
- `reset()` before the first block after the effect is chosen, short. Digital Delay only marks its state; its first
  block then starts from silence and reads a frame only once it was written since (`n`).
- The line: the slot's, a multiple of 16 bytes up to 4 MiB, the address through the patch point `fx_line`, shared with
  the slot's other effects, through the cache, the CPU only.
- The C ABI: `d2`–`d7` / `a2`–`a6` kept; the EMAC is free, the mixer sets `MACSR` again after the call.
- The build: `-mcpu=54418 -O2 -ffreestanding -fno-builtin -nostdlib`: no libgcc, so no 64-bit multiply in C
  (Digital splits its products in two 32-bit ones).
- The composer: `cost.emulation` declared, warning past 10 822 instructions a block over the stock delay's 2 659,
  refusal past 27 056.

## 4. Fixed point

### 4.1 The level `[À FAIRE]`

The clip (drive 5), the codec (full scale 1.0, faded out at 0.01), the compressor (0.25) and the make-up (0.15) were
tuned on the prototype's float scale. On the device the send bus is signed 32-bit, and Digital Delay takes `(L >> 3)
+ (R >> 3)`; what a loud machine puts on the send at Delay Send 127 has not been measured. Step 1 measures it in the
emulator (`mcengine.py`, a stock machine at its default level and a loud one, Delay Send 127, the send's peak and RMS)
and fixes the scale `K` (float 1.0 ↔ `K` on the bus) so that a loud send peaks at about 0.5, as in the prototype. All
thresholds then follow from `K`. If the send's level depends on the track's volume (pre- or post-fader), the
character does too, as it would on a real line: to be heard on the device.

### 4.2 Numbers

- **Samples** in Q2.29 (1.0 = 2^29, headroom ×4 for the clamp at 2.0); the line holds Q2.29 words, one a frame.
- **Products** on the EMAC, `mac.l` in signed fractional mode (`MACSR = 0xa0`, set at the start of `process`), then
  `movclr.l`, as `sdvintage.c` does; coefficients in Q1.31, those past 1 (a biquad's `a1`) halved and the sum doubled.
  For the host build the same C has a macro with the EMAC's exact rounding, so the host and the device give the same
  bits (`tools/emu/emac.py` already executes the EMAC exactly in the proof; Unicorn's own EMAC is wrong in this mode,
  [14](14-machine-sd-vintage.md) §4).
- **Once a block, from tables**: the phasor's step (for under 25 Hz, `θ` and `1 − θ²/2` are exact enough); the fading
  gain (a 33-entry dB table, interpolated); the leveler's two gains (a log2 from `ff1` and a 32-entry table, an exp2
  back); the shift's slow wander (two slow sines from a 256-entry table); the random aims (xorshift32, as the
  prototype).
- **The codec**: 63 decision levels a side in a table (a binary search, six compares) and 64 output levels; the gate a
  mix with one product.
- **The clip**: `c(x)` in three products and two compares.
- **The Hilbert pair**: the prototype's coefficients are a published design whose terms could not be read (the page
  would not load for the fetcher). The port computes **its own** pair with a script of the repository (a minimax fit of
  the phase difference): the line holds the transmitter's band, and the receiver keeps 350 Hz..3 kHz, so 90° ± 1° is
  needed only from about 150 Hz to 6 kHz, which three sections a chain may give instead of four (`[HYP]`, to compute).
  No third-party code or numbers then.
- **The reset**: as Digital's, a mark; frames read only once written since (`n`).

### 4.3 The 24 kHz option

Everything in the loop sits below about 4 kHz: the line could run at 24 kHz, the send halved by a small half-band
filter, the echo doubled by another. The loop's work halves, and the line too (512 KiB for the same 5.46 s). It changes
the sound a little (what the transmitter's gentle low pass lets through above 12 kHz folds or goes). Step 1 renders
both against v6, measures them (§2's numbers) and puts them on the listening page as tabs; the maintainer picks (D2).

## 5. Cost `[HYP]`

Instructions a frame, estimated from the operations (EMAC products about 2 instructions each, the states in
registers or the cache):

| Part | 48 kHz | 24 kHz loop |
|---|---|---|
| Send, read, slew, write, echo | 26 | 26 at 48 kHz + 10 for the two half-band filters |
| Scatter | 14 | 7 |
| Hilbert pair (3 + 3 sections) and phasor | 58 | 29 |
| Fading, dropouts | 3 | 2 |
| Codec and gate | 20 | 10 |
| Receiver (five biquads) | 45 | 23 |
| Leveler (frame part), feedback | 13 | 7 |
| Transmitter | 16 | 8 |
| **A frame** | **about 195** | **about 120** |
| Once a block (gains, tables, peak look-ahead) | about 250 | about 200 |
| **A block** | **about 6 500 (6 % of a block)** | **about 4 000 (3.7 %)** |
| Above the stock delay (2 659) | +3 800 (+3.5 %) | +1 300 (+1.2 %) |

- Under the composer's warning (10 %) both ways; the block of a switch adds only the reset (a mark) and `fxslot`'s
  200.
- **The device**: the emulator does not time memory. The stock effects count about 10 % of a block and take about 30 %
  on the device ([68](68-fx-slots.md) §17.4); the Syntakt engines cost nearly twice their count
  ([23](23-optimisation-charge.md) §4). The Cycles idles at about 76 %, the interface starves above about 85 %. At
  48 kHz and twice its count POTS would add about 7 % on the device: close to that limit with six voices playing.
  Hence step 5's measurement, and the 24 kHz option.
- RAM: the line (1 MiB, or 512 KiB), about 300 bytes of state, about 1 KiB of tables. Code: about 3 to 4 KiB.

## 6. The shift as a third parameter (after v0.1)

Kept for the step after v0.1; its gesture, storage and range are the maintainer's to decide then (D4–D6).

### 6.1 What the format needs

68 §15.8 reserves "more parameters"; the standard's §3.5 says the same. For a third one an effect declares `params[2]`
with its names, range, default and formatter, and the slot needs a place for the value, a way to edit it and a way to
show it:

- **The value, per pattern** `[HYP]` design: header byte 36 the delay slot's third parameter (0..127), 37 the reverb
  slot's, 39 a check (`0x5a` + 36 + 37); copied by `fxslot`'s load hook (`0x4005b4b0`) and set by its init hook
  (`0x4006155e`) as the choice in 29..31 is (68 §14); a failed check gives each effect its declared default. The three
  bytes are free in the standard's table (§5.9) and clear of Chord Keys. Like the choice it is not lockable per step
  and has no CC (a CC stays reserved).
- **The gesture**, three ways:
  - **TRACK + FUNC + Delay Time**: today it edits Fdbk as without TRACK (68 §9), so nothing is lost (FUNC + Delay Time
    still edits Fdbk). TRACK becomes the effect's own layer: TRACK + knob the choice, TRACK + FUNC + knob the third
    parameter. Only when the playing effect declares one; otherwise the stock edit, as today.
  - A long TRACK press then the knob: no spare long press is known on TRACK.
  - The reverb knob for the delay's third parameter: confusing, and the reverb slot's own effects would want it.
- **The display**: the popup reads the descriptor's names and formatter when it draws (68 §11.1); while TRACK + FUNC is
  held on knob 15 the part names descriptor 38 after the third parameter and gives it the third formatter, and gives
  Fdbk's back when TRACK is released. `[À FAIRE]`: read where the popup's value comes from for descriptor 38 (the P
  word, not the header byte), and whether the part can feed it the header byte's value.
- **The name** of the third parameter: to choose with the maintainer.

### 6.2 The shift's range

A proposal for then: 0..127 → 0..12 Hz on a square law (`12 Hz × (k / 127)²`): fine steps where the sound is subtle;
k = 52 gives the 2.0 Hz of v6, the default. The wander (±40 %) and the upward direction stay fixed. The prototype heard
0, 0.7, 2, 5 and 12 Hz.

### 6.3 What changes where

`fxslot` (load and init hooks, the gesture, names and formatter of the third parameter, a header accessor), the
manifest schema (`params` of three), `compose.py` and `composer.js` (the third names and formatter in the data block),
`claims.py` (TRACK + FUNC + knob 15, header bytes 36, 37, 39 as `saved`), the proof (§8), the standard (Draft 0.7: §3.5
"reserved" becomes the rule, §5.9 the three bytes). The standard changes only on the maintainer's explicit go.

## 7. The package

- `tools/machines/pots/`: `pots.c` (MIT, "durchgemacht and Claude"), `manifest.json` (id 2, `fx.delay`, `line` 1 MiB
  or 512 KiB, params "POTS Time" / TIME and "POTS Fdbk" / FDBK with the stock formatters, name "POTS", short "POTS",
  `cost.emulation` from the proof), `pots.o`.
- `tools/gen_pots.py`: the object, `--check`, the build alone (as `gen_digidelay.py`); later `70-pots.json` (§19.1) and the
  flasher card.
- `tools/gen_hilbert.py`: the allpass pair (§4.2), its phase error printed, `--check` against the numbers in
  `hilbert.json`, which `gen_pots.py` writes into the tables.
- No third-party file: the code, the coefficients and the sound brief are model27's own.

## 8. The proof

As Digital Delay's (68 §18.5), in `tools/emu/test_fxslot.py`:

1. **Host against device, bit for bit**: `pots.c` compiled for the host (the EMAC macro) and the device object in the
   OS under Unicorn with `emac.py`, the same blocks (noise, a burst, silence, a Time slide, Fdbk 0..127), 400 blocks
   and more, zero differences.
2. **Against v6**: the host build against the float prototype on the prototype's measurements (§2): decay table within
   10 %, tail end, codec in and above the band within 2 dB, peak at Fdbk 127, silence. These numbers go into the note.
3. **In the slot**: chosen by the pattern, reset, shared line with Digital Delay (a switch Digital → POTS → Digital
   reads nothing of the other), the stock delay's block of silence.
4. **Cost**: counted as §17.2 of 68, declared in the manifest, checked by a second run.
5. Unicorn does not run in this sandbox: the runs are the maintainer's.

## 9. Steps

v0.1 is steps 1 to 5 and 7 (two knobs, the shift fixed at 2 Hz); step 6 comes after it.

1. **Prototype, fixed point**: the C of §4 written once, built for the host inside the prototype; the level `K`
   measured (a script for the maintainer's terminal); 48 kHz against 24 kHz; own Hilbert pair; the measurements of §2
   and a listening tab "v6 fixed point" next to v6. Decision D2.
2. **The package** (§7) and `gen_hilbert.py`; checks without emulation. *Built: §13.*
3. **The proof** (§8), the maintainer's run; the cost declared. *Done: §14 (ALL OK §14.7, the cost declared; its
   check run ALL OK).*
4. **Build for the device**, two knobs, the shift at 2 Hz: `build/fx-pots/`. *Built: §15.*
5. **The device**: the maintainer listens against the page and reads the load (`syntakt-meter`,
   [23](23-optimisation-charge.md) §5): POTS, Digital Delay and the stock delay, with six voices playing. If it comes
   close to 85 %: the 24 kHz loop (if not chosen in step 1), fewer Hilbert sections, the codec's search as a table. *Done: §18.*
6. **After v0.1, the third parameter** (§6): `fxslot`, schema, composers, claims, proof (the header load and save as
   `probe_chord_storage.py`, the gesture, the popup), POTS's shift on it; the device.
7. **The flasher**: the card (experimental), guide, release; after the maintainer's test, tested. *Built: §19.*
8. **The standard**: Draft 0.7 (POTS's id; with step 6, the third parameter and the header bytes), on the
   maintainer's go.

## 10. Decisions

The maintainer, 2026-10-27, by clicked answers:

| | Question | Decided |
|---|---|---|
| D1 | The name | **POTS** / POTS; the parameters "POTS Time", "POTS Fdbk" |
| D2 | 48 kHz or a 24 kHz loop | **24 kHz** (2026-10-28, §12.6) |
| D3 | Two knobs first, the third later | **yes: v0.1 has two knobs, the shift fixed at 2 Hz** |
| D4 | The third parameter's gesture | later (step 6); proposal TRACK + FUNC + Delay Time |
| D5 | Its storage | later (step 6); proposal per pattern, header 36 (+ 37, 39) |
| D6 | The shift's range | later (step 6); proposal 0..12 Hz, square law, default 52 = 2 Hz |
| D7 | The standard | at step 8, on an explicit go |
| D8 | The codec's grain at 24 kHz, about 3 dB more in the band than v6 (§14.2) | **kept** as in the clips (2026-10-28) |
| D9 | POTS's echo against the stock delay's (§17) | **+6 dB** (12 dB above the prototype's echo), 2026-10-28 |
| D10 | The feedback's curve against the stock delay's (§17) | **kept** (v6's decay times) |
| D11 | Digital Delay's level (§17) | **kept** (PPPCCC's sound bit for bit) |

## 11. Left to read or measure

- `[À FAIRE]` the send bus's level (§4.1). *Measured: §12.4.*
- `[À FAIRE]` own Hilbert coefficients and their phase error (§4.2). *Computed: §12.1.*
- `[À FAIRE]` for step 6: the popup's value source for descriptor 38 while TRACK + FUNC is held (§6.1).
- `[HYP]` the cost (§5) until counted; the device share until measured.

## 12. Step 1, in the prototype (2026-10-27 and 28)

The maintainer, 2026-10-27: « Ja, fang mit Schritt 1 an: Festkomma-Modell im Prototyp, eigene Hilbert-Koeffizienten,
48 gegen 24 kHz, mit Hörprobe neben v6. Das Pegel-Skript für mein Terminal vorbereiten. » Everything in the prototype
outside the repository; nothing in model27 yet but this section.

### 12.1 The Hilbert pair, model27's own

A minimax fit (Nelder-Mead from many starts) of the two chains' phase difference over 150 Hz..6 kHz, for both forms of
§4.2: sections in z⁻² do better than first-order ones at the same number of products.

| Loop | Form | Products | Phase error | The other side |
|---|---|---|---|---|
| 48 kHz | z⁻², 4 + 4 sections, chain A a frame late | 8 | ±0.62° | 45 dB under (46.2 measured in the model) |
| 24 kHz | z⁻², 3 + 3 sections | 6 | ±0.35° | 50 dB under (50.9 measured) |

v6 had 49 dB. The 24 kHz loop needs fewer sections because the band then spans most of the rate.

### 12.2 The fixed point

A single C file written as the device's (integers only, no 64-bit product, divisions only where the ColdFire has
`divs.l`), with the EMAC as `tools/emu/emac.py` executes it: each product truncated to 2⁻²³ of an LSB, the accumulator
read as `acc >> 31`, saturated. Tables and constants from a generator. The loop at 48 kHz, or at 24 kHz between a
half-band decimator `(−1, 0, 9, 16, 9, 0, −1) / 32` and the four-point interpolator. Compiled for the host; a host-only
switch turns stages off for the checks.

Checked against the float prototype built with the same Hilbert pair, wave for wave (the difference under the float):

| What runs | First 0.5 s | To 2.2 s | To 6.2 s |
|---|---|---|---|
| The radio stages alone, sines 0.1 to 0.9 | −101 to −104 dB | | |
| All the arithmetic, no fading, scatter or codec | −81 dB | −70 dB | −55 dB |
| Everything | −56 dB | −53 dB | −39 dB |

What remains is the codec deciding a step the other way at its thresholds, carried round by the feedback.

Two faults found by that comparison, both of which the device would have had:

- `mul()` inside a run of `mac` calls empties the accumulator: the phasor's renormalization added `M²` into the
  running `c² + s²` and read zero; the phasor grew without bound. Compute every `mul()` before a run of `mac`.
- The skewed clip's polynomial in Q30 overflowed: `u` reaches 1.5, so `u²` = 2.25 and `u³` = 3.375 do not fit; the clip
  came out 18 % too loud. It runs in Q2.29 now.

### 12.3 Against v6

| | v6 (float) | 48 kHz | 24 kHz |
|---|---|---|---|
| Decay to −60 dB at Fdbk 90 / 100 | 20.1 / 23.3 s | 21.1 / 24.6 s | 19.8 / 23.0 s |
| A tail's end at 25 s | 1491 Hz, 0.1 % above 2 kHz | 1482 Hz, 0 % | 1496 Hz, 0.1 % |
| Colour, repeat 1 → 7 | 983 → 1455 Hz | 981 → 1455 Hz | 983 → 1457 Hz |
| Octave bands 250 Hz..4 kHz | | within 0.5 dB | within 0.6 dB |
| Echo level, pluck / stab | −27.8 / −32.5 dB | −28.0 / −32.4 dB | −28.0 / −32.9 dB |
| Peak at Fdbk 127, loud input | −5.6 dB | −5.6 dB | −5.6 dB |
| Silence in | silence | exact zero | exact zero |

At 24 kHz the snare's echoes come about 2 dB quieter. Listening clips of both rates sit next to v6 on the prototype's
page. D2 (48 or 24 kHz) is the maintainer's, by ear.

### 12.4 The send bus's level `[FAIT en émulation]`

Measured with the OS's own audio interrupt (`seqrig.py`) and, unlike `seqrig`, the mixer, Volume + Dist and the
block's accounting left running; the bus read where the mixer calls the delay (`0x4005699c`), every block; one track,
a stock machine at its defaults, Delay Send 127. Two things the mixer needs that `seqrig` never gave it:

- **Track Level** is not a sound word (descriptor 9, k = −1): the mixer reads it as word `t` of P, before the
  tracks' blocks (`0x400567f4`: `mvsw %fp@+,%d6`), and computes every gain from it, Volume + Dist (`a2@(52)`, k 19),
  Pan (`a2@(58)`, k 22) and the sends (`a2@(−12)` and `a2@(−10)` after `a2` moved on by 66: k 20, k 21), each block,
  into `0x40a78bd0` / `…bb8` (delay) and `0x40a78b9c` / `…b80` (reverb). At 0 the bus is silent: the first full run.
- **The mixer's one wait**: `0x4005697e..0x4005698a` reads `0xfc0453de` until bit 4 clears, the eDMA reading the delay
  line; no other polling loop in `0x40056700..0x40058700` (the mixer, the stock effects and their DMA calls). The run
  clears the bit there, as the finished DMA would.

| Machine | Peak, velocity 100 | Peak, velocity 127 | RMS, velocity 100 |
|---|---|---|---|
| KICK | −22.8 dBFS | −20.7 dBFS | −34.3 dBFS |
| SNARE | −19.9 dBFS | −18.0 dBFS | −46.0 dBFS |
| METAL | −24.6 dBFS | −21.4 dBFS | −48.2 dBFS |
| PERC | −25.0 dBFS | −22.9 dBFS | −42.8 dBFS |
| TONE | −28.0 dBFS | −25.9 dBFS | −38.7 dBFS |
| CHORD | −32.2 dBFS | −30.1 dBFS | −43.6 dBFS |

### 12.5 Decided (2026-10-28): the level in and out

The maintainer, by clicked answers:

- **In: the median machine** at Delay Send 127 and velocity 100 peaks at 0.5 on the prototype's scale: `K_BUS` =
  247 586 784, `IN_GAIN_Q29` = 1 164 158 973 (2.17, past Q30's range). KICK, METAL and PERC then reach the level the
  sound was tuned at, SNARE drives harder (0.87), CHORD less (0.21). (Against the loudest machine: 4.8 dB less drive.)
- **Out: 6 dB above the prototype's echo**, about as loud as Digital Delay: `OUT_GAIN_Q30` = 990 347 136 (0.922).
  Before it, against Digital Delay at the same send (both in float): POTS's echo was 6.8 dB quieter on the pluck, 3.1 dB
  on the stab, 19 dB on the snare (the band takes its body).

With both, every measurement of §12.3 is unchanged; the loudest return (SNARE's level, Fdbk 127) is −18.2 dBFS on the
bus. On the device the maintainer may still move both by ear (step 5).

### 12.6 Decided (2026-10-28): the loop at 24 kHz

The maintainer, 2026-10-28: « mach 24 ». Why: the receiver leaves nothing above about 3 kHz (−48 dB at 12 kHz), so a
loop up to 12 kHz loses nothing measurable (§12.3; the other side even 51 dB under against 46); the load, the plan's
largest risk (§5), drops from about 6 500 to about 4 000 instructions a block (+1.2 % of a block above the stock delay
instead of +3.5 %); three Hilbert sections a chain instead of four; the line 512 KiB instead of 1 MiB for the same
5.46 s. The cost: the snare's echoes about 2 dB quieter, and some 0.06 ms of the half-band filters' latency. Both
rates stay in the one C file (`POTS_RATE`), so 48 kHz remains a rebuild away until the device's load is measured
(step 5). The package of §7 takes `line` 524 288 bytes.

## 13. Step 2, the package (2026-10-28)

The maintainer, 2026-10-28: « Ja, Schritt 2 ». Built in model27 as §7 has it, with the checks that run without the
emulator.

### 13.1 The files

| File | What it is |
|---|---|
| `tools/machines/pots/pots.c` | The C file of §12.2, its arithmetic unchanged. On the device the EMAC by inline `mac.l`, `msac.l` (with `<<` for the Q30 products) and `movclr.l`, the leading zeros by `ff1.l`; `pots_process` sets `MACSR` to `0xa0` and clears `acc0` first. On the host (`POTS_HOST`) the same products as `tools/emu/emac.py` executes them, and the switches and the render entry the checks use. `POTS_RATE` 2 by default |
| `tools/machines/pots/pots_tables.h` | Generated by `gen_pots.py`: the codec, log2, exp2 and sine tables, the Hilbert pairs, the receiver's biquads, the constants, both rates |
| `tools/machines/pots/hilbert.json` | The two pairs of §12.1, from `gen_hilbert.py` |
| `tools/machines/pots/manifest.json` | id 2 in `fx.delay`, `line` 524 288, "POTS Time" / TIME and "POTS Fdbk" / FDBK with the stock formatters, name and short "POTS", order 40, `POTS_RATE` 2 in the defines. No `cost.emulation` yet: the composer reports the slot's load as unknown until step 3. Tests: emulation not yet run; experimental |
| `tools/machines/pots/pots.o` | The committed object (`ld -r`): 5 818 bytes of code and tables, 344 bytes of variables, 167 relocations, all `R_68K_32`; `fx_line` the one undefined symbol |
| `tools/machines/pots/LICENSE` | MIT, durchgemacht and Claude |
| `tools/gen_pots.py` | The tables (standard library alone), the object, the build alone through `compose.py`, in memory; `--check`. The tweak and the card come with step 7 |
| `tools/gen_hilbert.py` | `--check` (the default) recomputes each pair's phase error from `hilbert.json`; `--design` fits them again. The one tool here that needs numpy |

The plan's "group" is not a key of the manifest's schema: the name "POTS" is what the device and the flasher show.
`K_BUS` is written into `gen_pots.py` from the two middle peaks of §12.4, so that the generator does not read the
prototype's files.

### 13.2 Checked

| Check | Result |
|---|---|
| `gen_pots.py --check` | the tables and the object up to date. The build alone: 7 writes, code 5 818 bytes, variables 344 bytes, the slot's line 512 KiB at `0x43036000`, 8 680 bytes added to the image, 269 conflicts computed |
| The tables against the prototype's | every value the same; the receiver's scale on the standard library gives the numpy figure's Q30 words. The prototype's two unused constants dropped, the clip's two limits named |
| The host build of `pots.c` against the prototype's file, the one §12.2 and §12.3 measured | both rates; three runs of the knobs (fixed; Time and Fdbk sweeping; a Time jump with Fdbk rising to 127), each with every stage on, every stage off, the codec off, a fixed shift step: 24 runs of 4 000 blocks, **0 words differ**. `-Wall -Wextra -Werror` on the host too |
| The device object | 73 `mac.l`, 1 `msac.l`, 58 `movclr.l`, 1 `ff1.l`, all from the inline assembly (GCC 16.2 emits no EMAC instruction of its own: checked on a multiply-accumulate loop, which gives `muls.l`); `MACSR` set before the first; 5 `muls.l`, the Time formula's signed division and the codec gate's unsigned one; no call outside the object (no `__muldi3`); `d2`–`d7`/`a2`–`a6` saved |
| `gen_hilbert.py --check` | 24 kHz ±0.351°, the other side 50.3 dB under; 48 kHz ±0.618°, 45.4 dB |
| `claims.py --check --self-test` | ALL OK (package pots: 0 claims) |
| `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`, `py_compile` | ok (289 tweaks; POTS is not in the flasher yet) |
| `webcompose_check.sh`, with the official file | part 1: pots 23/23 placements identical to `relocate.place`; part 2 OK |
| `gen_digidelay.py --check` | unchanged |
| `relocate_6ch.py --check` | fails as it did on HEAD before (binutils 2.47 against the committed bytes), untouched |

Not proved yet: that the device object computes what the host build does (step 3: Unicorn with `emac.py`, the same
blocks, the maintainer's run), and the cost.

## 14. Step 3, the proof (prepared 2026-10-28)

The maintainer, 2026-10-28: « Start step 3 ». The proof of §8 written; the runs that need Unicorn are the
maintainer's (§14.5).

### 14.1 Limits against a full-scale bus

Writing the proof showed that the host build could not follow the device at a full-scale bus, which section 3 of
`test_fxslot.py` feeds every fifth block: the host's accumulator was 64 bits wide, and `mul29` of two full-scale words
(2^64 before the shift) wrapped it, where `emac.py` (unbounded) and the device (8 bits above 1.0) do not. Three more
sums could wrap in C at that level. Changed in `pots.c` (§13's object rebuilt):

- the host's accumulator 128 bits wide (`__int128`);
- the input held at ±2.0 before the decimator (its sums then stay under 1.2 × 2^30; anything above 0.35 is clipped
  by the transmitter anyway);
- the feedback added to the input saturating (`add_sat`);
- the echo held at ±0.75 of full scale before the interpolator (its sums then stay under 0.94), 16 dB above the
  loudest return measured (§12.5);
- `-fwrapv` on both sides, so that any other wrap is the same on the host and the device.

At the prototype's levels nothing changed: the host build still gives the prototype's bits at both rates (the 24 runs
of §13.2). The code grew from 5 818 to 6 122 bytes, still only `R_68K_32`.

### 14.2 On the host, against v6

`tools/emu/pots_host.py` builds `pots.c` with the host's C compiler at the manifest's rate. Section 8 compares the
device's object with it, and it takes the measurements of §12.3 again on that build. The sources are synthesized as
in the prototype. It runs without Unicorn or firmware (`python3 tools/emu/pots_host.py`); here, ALL OK:

| | The port (24 kHz) | v6 | Allowed |
|---|---|---|---|
| The shift | up, the other side 50.9 dB under | up | ≥ 45 dB |
| Decay to −60 dB, Fdbk 40 / 64 / 90 / 100 | 2.45 / 4.85 / 19.75 / 22.95 s | 2.55 / 4.85 / 20.1 / 23.3 s | 10 % |
| Fdbk 110, 127 | not dead after 25 s | the same | |
| A tail's end at 25 s | 1496 Hz, 0.1 % above 2 kHz | 1491 Hz, 0.1 % | 3 %, ≤ 1 % |
| Colour, repeats 1 → 7 | 983 → 1457 Hz | 983 → 1455 Hz | 3 % each |
| Octave bands 250 Hz..4 kHz | within 0.6 dB | | 1 dB |
| Echo level, pluck / stab | −28.0 / −32.9 dB | −27.8 / −32.5 dB | 1 dB |
| Codec's grain in the tail, in the band, at 1 / 3 / 6 / 15 s | −35.4 / −30.3 / −24.0 / −20.1 dB | −38.4 / −33.2 / −26.3 / −19.7 dB | −2 to +5 dB |
| The same above 4 kHz | −59.7 / −62.0 / −57.6 / −58.4 dB | −60.6 / −62.7 / −58.8 / −59.0 dB | ≤ +2 dB |
| Peak at Fdbk 127, loud input | −5.6 dB | −5.6 dB | 0.5 dB |
| Silence in | exact zero | silence | |

**New: the codec's grain is about 3 dB stronger in the band at 24 kHz**, early in a tail (1 to 6 s), the same by
15 s. The codec's error has the same power at either rate. At 24 kHz it lies in half the band, so twice as much of it
passes the receiver. The 48 kHz loop measured the same way stays within 1 dB of v6 (−37.8 / −33.4 / −26.6 /
−18.7 dB). §12.3 did not measure it; it is in the 24 kHz clips the maintainer chose by ear (§12.6). The check allows
the rate's 10 log10(48 / 24) = 3 dB above v6 on top of the 2 dB. **Decided (2026-10-28), the maintainer: « Keep
it »**: the grain stays as the 24 kHz loop gives it (D8, §10); not matched to v6.

### 14.3 In `tools/emu/test_fxslot.py`

- The selections `pots` and `sampler,pots,refreverb`, with POTS's host build as the model of the delay slot. Sections
  2 to 6 as for every effect: the sites, the line, the audio against the model bit for bit (the playing pattern
  choosing POTS, the stock delay's block of silence, the reset), the gesture, the pattern, the cost.
- Section 8, POTS alone, against its host build, bit for bit: a burst at the median machine's level and its echoes;
  noise at that level; full-scale noise at Fdbk 127 (the limits of §14.1); Time sliding 0 to 6 with Fdbk rising to
  127 under bursts; silence. Then a reset and it all again, then 2 400 blocks more, past the first dropout
  (2 250 blocks after the reset). 3 380 blocks, Time 0 and 1 so that the loop goes round some twenty times.
- Section 9, once a run: the measurements of §14.2 as checks.
- Section 10, once a run: `digidelay,pots` composed, the pattern choosing Digital, POTS, Digital, POTS through
  `fx_delay` (80 blocks each), the slot's line (1 MiB) filled with noise before each switch. Each return must be its
  model's from its reset: neither effect reads what was on the line before it.
- The cost: counted as for every effect (68 §17.2) into `build/fx-cost.json`. The manifest declares it after the
  maintainer's run, and a second run checks it.

### 14.4 Checked here

`test_fxslot.py --dry` for `pots`, `sampler,pots,refreverb` and `digidelay,refreverb`: ALL OK (the sites, the data
block with "POTS Time" / "POTS Fdbk" / "POTS", the stock formatters, the line of 512 KiB at `0x43036000`). Sections 8
to 10 run against a stand-in for the device that runs the same models and fxslot's switch rule (outside the
repository): every check passes. That checks the proof's own code, not the device. `gen_pots.py --check`,
`gen_hilbert.py --check`, `claims.py`, `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`,
`py_compile` and `webcompose_check.sh` with the official file (POTS 23/23 placements): OK.

### 14.5 The maintainer's run

```sh
python3 tools/emu/test_fxslot.py --cycles <model-cycles_OS1.13.syx> --machines pots --machines sampler,pots,refreverb
```

Then the cost from `build/fx-cost.json` goes into the manifest's `cost.emulation`, and the same command again
checks it.

### 14.6 The maintainer's first run (2026-10-28): a fault of the proof

Every check passed except POTS's two bit-for-bit ones (sections 8 and 10). Both parted at block 23, where the first
echo comes back at Time 0; before it, both sides return silence. The general audio check of section 3 had passed
only because its delay times are long enough that no echo came back.

A probe outside the repository compared the state (86 words by name), the line and the output after each block. On
the device side every EMAC product was 0 from block 0 on. The cause was the proof's own: before each call
`Side.effect` replaced `emac.acc` with a new list, while `emac.py`'s fast `mac.l` / `msac.l` closures keep the list
they were made with. From the first call on, the products went into the old list and `movclr.l` read the new one.
Fixed: the list cleared in place (as `test_track_filter.py` does), and a comment in `emac.py`. Shown with `emac.py`
alone: 0.5 × 0.5 gives 0 with the list replaced, 0.25 with the fix. Nothing proven before is touched: REFD, REFR,
Digital Delay and fxslot have no EMAC instruction, SAMPLE does not play in this proof, and the stock effects ran the
same code on both sides. POTS is the first effect with EMAC code. Ruled out on the way: every one of POTS's 148
EMAC instructions is hooked by `emac.py` and decoded as in the object; every kind of instruction in `pots.o` also
occurs in packages already proven in Unicorn.

The cost counted in that run is not declared yet: first 10 043, mean 9 857, max 9 874, reset 2 instructions a block
(+7 302 steadily above the stock delay, 6.7 % of a block, under the composer's 10 % warning). With the products
right, the branches that depend on them (the clip, the codec's search, the leveler) may count differently. It is
2.5 times the estimate of §5 and §12.6 (about 4 000), which makes the device's load (step 5) the thing to watch.

### 14.7 The second run (2026-10-28): ALL OK

The maintainer, after the fix of §14.6: « allok ». Proven on the OS's own code, for `pots` and
`sampler,pots,refreverb`:

- POTS's process gives its host build's bits: the 3 380 blocks of section 8, from start-up, after a reset and past
  the first dropout, at full scale included; the playing pattern choosing it in section 3.
- Digital Delay and POTS share the delay slot's line without reading each other's frames (section 10).
- The measurements of §14.2 hold for the device (section 9 on the host build, which section 8 ties to the device).
- The sites, the line, the gesture, the pattern header and the register contract, as for every effect.

The cost counted (68 §17.2), now declared in the manifest's `cost.emulation`: first 10 043, mean 10 080, max 10 118,
reset 2 instructions a block. The composer's load of the delay slot (`compose.fx_cost`): steadily +7 546 above the
stock delay, 7.0 % of a block, under the 10 % warning (10 822); a switch's block +10 244 (the warning at 54 112). The
manifest's `tests.emulation` carries the run.

The check run (2026-10-28, `--machines pots`), the maintainer: « all ok »: the declared cost is the one counted.
Step 3 is done; next step 4, the build for the device.

## 15. Step 4, the builds for the device (2026-10-28)

The maintainer, 2026-10-28: « Start step 4 ». Composed from the committed packages of `dcbab86` with
`tools/compose.py --cycles <official> --machines <selection> --out build/fx-pots --tool <elektron-firmware-tool>`.
v0.1 has two knobs, Time and Fdbk, and the shift fixed at 2 Hz upwards.

### 15.1 The builds

| Selection | Writes | Added to the image | MAIN OS (SHA-256) | The `.syx` (bytes) |
|---|---|---|---|---|
| digidelay, pots | 7 | 9 912 bytes | `ea856974…` | 900 384 |
| sampler, digidelay, pots | 130 | 50 420 bytes | `3f29e96e…` | 948 384 |
| pots | 7 | 8 984 bytes | `b7ed020d…` | 899 488 |

In `build/fx-pots/` (git-ignored), each with its report (`.syx.json`). The C tool: checksums and HMAC ok, the same
MAIN OS, for all three. The composer: the delay slot's load +7 546 instructions a block on the stock delay (7.0 % of a
block), +10 244 in the block of a switch. The delay slot's line is Digital's 1 MiB when both are in. The proof of §14
ran `pots`, `sampler,pots,refreverb` and `digidelay,pots`; `sampler,digidelay,pots` is placed by the same composer,
and `webcompose_check.sh` showed POTS placed identically in 23 placements.

The load meter (`syntakt-meter`, [23](23-optimisation-charge.md) §5) cannot go in: it is a payload of its own, among
POTS's computed conflicts. Step 5 judges the load as Digital Delay's was judged (68 §18.7): by ear and by the interface.

### 15.2 For the device (step 5)

`digidelay+pots` (or the same with SAMPLE), a send on a track:

1. The start-up as usual (the boot now clears the 1 MiB line and the state).
2. TRACK + Delay Time, four detents right a step: Delay → Digital → POTS. With POTS the knobs read `POTS Time` /
   `POTS Fdbk`, the group `POTS`; the stock formatters.
3. The sound, against the prototype's listening page: the telephone band, the repeats drifting up pass after pass,
   fading and now and then a dropout, the codec's grain on a tail (a little more of it than v6, D8). Time slides when
   turned, as the stock delay's does; at Fdbk 127 a tail sustains without running away.
4. Loud: several tracks with Delay Send 127 and high velocities at once: no crackle from a wrap (§14.1), the echo held.
5. Switching between Delay, Digital and POTS while playing: each starts from silence, no old echo; a pattern change,
   save and load keep the choice.
6. **The load, the open risk.** The emulator counts POTS at 10 118 instructions a block (9.3 % of a block),
   2.5 times §5's estimate. The device has taken 2 to 3 times the count before: the Syntakt engines about twice
   ([23](23-optimisation-charge.md) §4), the stock effects about three times (68 §17.4). The Cycles idles at about
   76 % and the interface starves above about 85 % (§5). Six tracks playing with POTS, then with Digital, then with the
   stock delay: is the interface slow (knobs, screen), does the audio drop out, and from how many voices?
7. Back to the official OS by USB, as before.

If the load is too much, what keeps the sound bit for bit comes first: the codec's search as a table, the half-band
filters' histories as rings instead of shifted arrays. After that, what changes it, each by ear: fewer Hilbert
sections, a lighter receiver.

## 16. The device, first try (2026-10-28): no echo, the EMAC's scale factor

The maintainer, 2026-10-28, with `digidelay+pots` of §15: « man hört kein delay wenn man pots auswählt. entweder zu
leise oder kaputt ».

- **Not the level.** On the host build, at the median machine's level, Time 23 and Fdbk 64, POTS's echo is 1 to 4 dB
  under Digital's on tones, 7 dB on a snare and 20 dB on a kick: audible.
- **The cause.** POTS took its Q30 and Q29 products with the EMAC's scale factor (`mac.l Ry,Rx,<<,ACC0`, the product
  doubled). Nothing that has run on the device uses it: none of the OS's EMAC instructions, none in the packages.
  `emac.py` applied it in fractional mode. QEMU, which is Unicorn's core and digiemu's patched one, applies it in
  integer mode only. With the shift ignored, the host build's echo falls by 85 dB (a tone, Time 23, Fdbk 64): silence,
  as heard. So the proof of §14 was exact for `emac.py`'s reading of the EMAC, not for the device.
- **Fixed.** POTS uses no scale factor: a doubled product is two `mac.l` (`mac2`), a quadrupled one four (`mul29`).
  `emac.py` now ignores the scale factor in fractional mode, as QEMU does and as the device did here, so the emulator
  computes such code as the device does. The object: 106 `mac.l`, 64 `movclr.l`, 1 `msac.l`, code 6 226 bytes
  (+104), only `R_68K_32`.
- On the host the measurements of §14.2 are unchanged, ALL OK: the products differ in the last bit only.
- The manifest's cost is taken out until the next count (more `mac.l`). Its tests say the proof is to run again, and
  that the device test of `dcbab86` heard no echo.
- The builds of §15.1 again, from this object: MAIN OS `97ab648b…` (digidelay, pots), `93d997ce…` (with SAMPLE),
  `ce70996f…` (pots); the C tool ok, the same sizes.

**The proof again (2026-10-28), the maintainer's run: ALL OK**, with `emac.py` ignoring the scale factor: every
section of §14.7 again, sections 8 and 10 bit for bit. The cost counted and declared in the manifest: first 10 716,
mean 10 753, max 10 791, reset 2 instructions a block (two `mac.l` for one cost about +670). The delay slot's load:
+8 219 steadily above the stock delay (7.6 % of a block, under the 10 % warning), +10 917 in the block of a switch.
The declared cost does not enter the build: the MAIN OS of `digidelay+pots` stays `97ab648b…`, the builds of this
section stand. The check run (`--machines pots`), the maintainer: « prüflauf all ok »: the declared cost is the
one counted. Next the maintainer tries the build in digiemu, then on the device (§15.2).

## 17. The device, second try (2026-10-28): the echo there, quieter than the stock delay

The maintainer, 2026-10-28, with the builds of §16 in digiemu and on the device: the echo is there; « digi und pots
sind viel leiser als stock-delay ».

### 17.1 The stock delay, read from its code

`0x40057488`, its constants in the image. Each frame:

- The line's frame through a soft clip `2x − x·|x|` (gain 2 for small signals), × 1/32, then × 16: the line's level.
- A one-pole low pass, pole `0x4013ff84` = 0.8286 (about 1.4 kHz), whose gain below it is **2**.
- A one-pole high pass, pole `0x4013fb84` = 0.9980 (about 15 Hz), at unity above it. This is the echo.
- The line written with the send at unity plus the echo × 66 053 × the Fdbk word / 2³¹ (linear in the knob).

So the stock delay's echo stands about 6 dB above the send below 1.4 kHz, and its loop gain there is
2 × Fdbk / 127: 0.63 at 40, **1.0 at 64**, 1.4 at 90, where the soft clip holds it. From the middle of the knob on, its
repeats hardly die and stand loud. Digital Delay's and POTS's curve (Digital's, × 1.18 for POTS) decay as v6 was tuned.

### 17.2 The levels

A float model of the stock delay from §17.1 against Digital Delay's model and POTS's host build. The send is at the
median machine's level, Time 23 (375 ms). The first echo is Fdbk 0; at the other settings the level is taken over 3 s.
In dB against the stock delay (outside the repository: `levels_vs_stock.py` next to the prototype):

| | first echo | Fdbk 40 | Fdbk 64 | Fdbk 90 |
|---|---|---|---|---|
| Tone C5: Digital / POTS before / POTS now | −1.7 / −3.8 / **+2.2** | −2.3 / −4.3 / +1.7 | −6.0 / −6.7 / −0.7 | −16.7 / −16.5 / −10.5 |
| Tone C3 | −6.0 / −12.2 / **−6.1** | −7.8 / −13.3 / −7.3 | −13.5 / −17.0 / −11.0 | −25.1 / −26.1 / −20.0 |
| Snare | −1.9 / −11.5 / **−5.4** | −3.3 / −12.1 / −6.1 | −9.1 / −16.6 / −10.6 | −22.6 / −27.4 / −21.4 |
| Kick | −12.0 / −28.9 / **−22.8** | −13.9 / −30.6 / −24.5 | −20.1 / −36.4 / −30.4 | −33.1 / −48.6 / −42.6 |

A model read from the code, not a measurement on the device; it agrees with what the maintainer heard.

### 17.3 Decided (2026-10-28) and built

The maintainer, by clicked answers:

- **POTS +6 dB** (D9): `OUT_X` 4 in `gen_pots.py`, `OUT_GAIN_Q30` = 1 980 694 272 (1.84). The first echo now stands
  about at the stock delay's on middle tones; low tones, snare and kick stay under it, which is the telephone band.
  The loudest return is −12.3 dBFS (SNARE's level, Fdbk 127), 10 dB under the echo's limit of §14.1.
- **The feedback curve kept** (D10): the decay times of §14.2.
- **Digital Delay kept** (D11): PPPCCC's level, bit for bit.

The measurements of §14.2 are taken on the prototype's scale, so they are unchanged: ALL OK. The device's object
changed (one table word), so the proof runs again; its count should not move (the gain sits outside every branch but
the echo's limit). Builds again in `build/fx-pots/`: MAIN OS `c3b508f6…` (digidelay, pots), `dc7a3497…` (with
SAMPLE), `4a17782e…` (pots); the C tool ok.

The proof again (2026-10-28), the maintainer: « bewies all ok »: bit for bit, and the declared cost the one counted.
Next the device with these builds (§15.2).

## 18. The device, third try (2026-10-28): it works, the load too

The maintainer, 2026-10-28, with the builds of §17.3 (the echo 6 dB up), asked whether they were tried on the device,
by a clicked answer: « Gerät ok, auch die Last ». The level, the sound, switching between the effects and six voices
playing at once are fine on the Model:Cycles. Which of the three builds was not named; just before, the maintainer had
asked for the one with SAMPLE.

So step 5 is done: the load of §15.2 (item 6), the open risk, did not show, and none of the fallbacks there is needed.
The card comes next (step 7, §19). As Digital Delay's (68 §19.4), it stays experimental until the maintainer flashes
it from the page.

## 19. Step 7, the card (2026-10-28)

The maintainer, 2026-10-28: « ok, passt. weiter », after the device's third try (§18). Built as Digital Delay's card
(68 §19).

### 19.1 What was built

- **The card's build alone**: `70-pots.json` by `gen_pots.py` (as `gen_digidelay.py`). The manifest's order is 70, not
  the 40 of §7: 40 is arp's and the 30s are full, so `tweaks/AGENTS.md` gives the slots' effects `70`–`79` (Digital
  Delay came first, as 39). The order moves nothing in the builds of §17.3: composed again with order 70, their MAIN OS
  are the same (`c3b508f6…`, `dc7a3497…`, `4a17782e…`), and `build.py -t pots` gives `4a17782e…` too.
- The tweaks whose conflicts are computed against the folder gained `pots` and nothing else: `27-sampler`,
  `28-refmachine`, `29-refmachine2`, `34-refchord`, `36-chordtables`, `39-digidelay`. `REGISTRY.md` regenerated: the
  four hooks of `fxslot` now have two targets, by the combination.
- **The card**: `FEATURES` (`cat` sound, experimental, `package` pots, no `credit` and no `license`: model27's own code,
  under the repository's MIT), `OFFERED`; `tweaks.js` generated. The page composes it with the other package cards
  into one tweak: `digidelay+pots`, `sampler+digidelay+pots`.
- **`app.js`**: the card's texts (en, fr), its guide anchor `pots`; `REF_MAINOS` (11 combinations) and `REF_MODS` (8)
  by `ref_mainos.py`: POTS alone `4a17782e…` and with Digital `c3b508f6…`, the builds of §17.3.
- **`tools/webcompose_synth.py`**: four selections with POTS (alone, with Digital in both orders, with SAMPLE and
  Digital).
- **`tools/webflash_smoke.js`**: four cards, their order by section, POTS without a credit, POTS alone, with Digital,
  with SAMPLE and with Control All Config, its tag, the French texts.
- **For users**: the guide's section 5, POTS (en, fr; the sections after it renumbered; Digital's "Other mods" names
  POTS), release 0.12, the stamp `2026-10-28-01`, `README.md`, `PROVENANCE.md`, `BUILD.md`, the repository map in
  `AGENTS.md`. No word of the sound's working names and no third-party credit: the sound and the code are model27's.

### 19.2 Checks (2026-10-28)

- `webcompose_check.sh` with the official file: every selection identical to `compose.py`, the four new ones too
  (`pots` `4a17782e…`, `digidelay+pots` `c3b508f6…`, `sampler+digidelay+pots` `dc7a3497…`, the builds of §17.3;
  `pots+digidelay` `54e07bd2…`); `fill` 6/6.
- `webflash_smoke.sh` with both official files: 184 checks, **ALL PARTS OK**.
- `ref_mainos.py --check`, `webbuild_check.sh`, `webflash_check.sh`, `check_overlaps.py`, `registry.py --check`,
  `claims.py --check`, `py_compile`: green.
- `gen_pots`, `gen_digidelay`, `gen_sampler`, `gen_refmachine`, `gen_chordtables`, `gen_parts`, `gen_registrar`,
  `gen_flasher_tweaks` with `--check`, `gen_hilbert.py --check`, `pots_host.py` (the measurements of §14.2): green.
- Red as on `HEAD` before this step, nothing to do with POTS: `claims.py --self-test` (three cases on SAMPLE's
  claims: × Model-TG, × the track filter, × REF2) and `relocate_6ch.py --check` (§13.2).
- Not run again: `test_fxslot.py` (Unicorn, the maintainer's terminal). The object is unchanged since its last run
  (§17.3); only the manifest's order moved, which the proof does not read.

### 19.3 For the device

From the page, served from the work copy (as 68 §19.4): POTS alone (MAIN OS `4a17782e…`), with Digital (`c3b508f6…`)
and with SAMPLE (`sampler+digidelay+pots`, `dc7a3497…`), the steps of §15.2. If all is as expected, the card becomes
"tested" in a commit of its own (AGENTS.md step 8).
