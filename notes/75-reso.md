# 75 — Reso: a tuned resonator in the Track FX

The second of the three Track FX built at the same time after the list of [73](73-track-fx-crush.md) §1 (the
maintainer, 2026-11-01: « dann lass uns erst alles vorbereiten und danach werden parallel die fx gebaut », notes/73
§16): a resonator that turns noise and hits into tones at a pitch, on any track whose sound chose it. Package
`reso` (`tools/machines/reso/`, filter id 4, "RES" on screen), generator `tools/gen_reso.py`, the card's tweak
`75-reso.json` (order 75), proof in emulation `tools/emu/test_fltslot.py` (its model and cost states from the
manifest's `proof` section, notes/73 §16, no change to the proof). Branch `trackfx-reso`, from `trackfx` (`df1b562`,
`fltslot` 0.9). Addresses: VAs of OS 1.13.

## In short

- **A comb**: one line a track, read a period back and fed again through a damping lowpass, so that noise, hats and
  hits ring at a pitch with all its harmonics (a plucked or struck string, a tube, a metallic ring when bright). The
  MODAL prototype (`_scratch/modal-proto/`, notes/71) is the sound reference; a bank of modes did not fit the load
  (§1).
- **Four values** (RETRIG + SWEEP / CONTOUR / COLOR / SHAPE, k 28 to k 31): **Pitch** the MIDI note (60 = C4, 69 =
  A4 = 440 Hz, 8 Hz to 12.5 kHz), **Amount** (0 the track untouched, 127 the resonance alone), **Tone** on COLOR (dull
  at 0, every harmonic ringing as long as the pitch at 127), **Decay** on SHAPE (20 ms to 10 s for the pitch to fall
  by 60 dB, the same on every pitch). All with p-locks, LFO, velocity, Control All; CC 74 / 71 on Pitch and Amount.
  Since Reso 0.3 (§14): Decay on COLOR and Tone, called Brightness, on SHAPE before.
- **Off is dry and is the start**: Amount 0 gives the block back untouched, bit for bit; Amount's neutral word is 0,
  so a sound that steps to Reso starts there. Pitch starts at C4 (its start word 0x3c00, fltslot 0.8).
- **In tune at the pitch**: the allpass and the damping's phase are worked out so that the loop is exactly a period
  long at the pitch: measured within 0.2 cents from C1 to C7 on whole notes, 0.7 between them, +5 at 8 kHz (§7).
- **Never runs away**: the loop's gain stays under 1 − 2⁻¹² at DC and everywhere else, every sum saturates at full
  scale (the EMAC's), a DC blocker at 15 Hz keeps kicks from piling up in the loop.
- **Cost** of Reso 0.2, counted by the proof (§13, the maintainer's run): about 670 instructions a track and block
  held (674 at C4, 706 at C1 while the line is still being cleared), 961 when every word moves every block, 1 106 in
  the first block, 128 for a silent track, 24 off. Six tracks at most 6 636 instructions a block, 6.1 % (Samples'
  worst 8 952, 8.3 %; Reso 0.1 7 398, 6.8 %, §8). The frame loop is ColdFire assembly (`reso_cf.S`, 19 instructions a
  frame, MAC with load); `reso.c`'s C loop is its host model, bit for bit. Not measured on the machine yet.
- **Reso 0.4** (§17): about a fifth fewer instructions where it is dearest (its first block, the coefficients moving):
  the block's bookkeeping and the coefficients in assembly too, bit for bit, and the silence test's energy from every
  fourth frame (a rung-out tail under −90 dB may be let go a block sooner or later). Code and tables 7 808 bytes
  (8 610).
- **On the machine** (2026-11-01): Reso with Samples and Crush, flashed from the command line: « passt » (§12); Reso
  0.3, Tone on COLOR and Decay on SHAPE, the popups checked: « getestet, passt » (§14).

## 1. Decisions (2026-11-01)

Asked one at a time, with a recommendation each:

| Question | The maintainer | Consequence |
|---|---|---|
| Comb or a small modal bank (four modes with MODAL's material ratios)? | « Kamm » (the recommendation) | a comb: all harmonics, about 21 instructions a frame; four modes would cost about 1 300 to 1 500 a track and block and, as MODAL's round 1 heard, leave mostly a sine (MODAL's eight modes cost about 4 000) |
| The knobs: SWEEP Pitch (the MIDI note), CONTOUR Amount (0 dry), COLOR Decay, SHAPE Brightness? | « Wie vorgeschlagen » | Pitch and Amount on the two knobs with a CC |
| (Reso 0.3, after the stock machines' knobs were compared) COLOR and SHAPE swapped, Brightness renamed? | « beide tauschen », « pass auch direct das word "Brightness" an, das ist zu lang für den kasten in dem es steht » | Tone on COLOR, Decay on SHAPE; the names Reso Tone / TONE (§14) |

Decided here, within that design (for the maintainer to change after listening):

| What | Chosen | Why |
|---|---|---|
| Pitch's scale | the value is the MIDI note, `int` format 0 .. 127, whole values semitones, FUNC for the fine tune | the slot has no note formatter (`int`, `centre`, `cutoff`); a note number reads at once, p-locks make melodies |
| Pitch's start | C4 (0x3c00) | the neutral word 0x4000 would be E4 |
| Decay | T60 = 20 ms · 500^(d/127): 0.46 s at 64, 2.2 s at 96, 10 s at 127 | MODAL's range (20 ms to 8 s), a little longer |
| Tone (Brightness until 0.3) | the damping's cutoff from 4 harmonics of the pitch at 0 to 256 at 126, none at 127 | dull to metallic; the cutoff follows the pitch, so the timbre does not change with it |
| The level | white noise in, as loud out (the input scaled by √(1 − g²), g the loop's gain a period) | no growth with Decay, no clipping of noise; a single hit's ring gets quieter as it gets longer (the same energy), a drum loop at Amount 127 comes out 2 to 8 dB under the dry one (§7) |
| A note (the trig bit) | not read: the comb rings on | a resonator's tail is the point; a choke cannot reach the line's far end in time |

## 2. The values

| Where | What | Words | Neutral / start |
|---|---|---|---|
| k 28 (RETRIG + SWEEP, CC 74) | Pitch | 0 .. 0x7f00, the note in 8.8 | 0x4000 / **0x3c00** (C4) |
| k 29 (RETRIG + CONTOUR, CC 71) | Amount | 0 .. 0x7f00: 0 untouched, 0x7f00 the comb alone, a crossfade between | 0 (the start: off) |
| k 30 (RETRIG + COLOR) | Tone | 0 .. 0x7f00 | 0x4000 (32 harmonics) |
| k 31 (RETRIG + SHAPE) | Decay | 0 .. 0x7f00 | 0x4000 (0.46 s) |

Names: Reso Pitch / PTCH, Reso Amount / AMT, Reso Tone / TONE, Reso Decay / DEC; all `int`. Words outside 0 .. 0x7f00
(an LFO pushes them there) are clamped. Until 0.3 (§14) k 30 was Decay and k 31 Brightness (Reso Brightness / BRT,
15 characters, too long for the popup's box).

## 3. The comb

Per frame, all products on the EMAC (signed, fractional, truncating: MACSR 0xa0, as the slot calls a filter):

1. **The input less its DC, scaled**: `hp = nrm (x − x1) + R hp`, R = 1 − 2⁻⁹ (about 15 Hz). Without it a kick's net
   area (a decaying sine starting upwards has one) piles up in the comb's DC mode, which rings as long as the loop's
   gain lets it: measured −75 dBFS of DC after kicks every 0.5 s, and decaying with it (§7).
2. **The line, a period back**: the frame `dint` back and the one before, through a first-order allpass,
   `v = u0 + η (u1 − v1)`, delay 0.5 to 1.5 frames: no loss whatever the fraction (linear interpolation loses up to
   cos(w0/2) a pass, which made the decay of high notes depend on their fraction). η = (1 − Δ)/(1 + Δ) from a table of
   65 steps of Δ (`RESO_ETA`): exact at low pitches, +5 cents at 8 kHz.
3. **The damping**, a one-pole lowpass `lp = kq v + q lp`. Its pole is chosen so that its phase at the pitch is exactly
   the phase P of Tone's table: q = sin P / sin(w0 + P) (from tan P = q sin w0 / (1 − q cos w0)); the line is then
   read P / w0 frames earlier, so that line, allpass and damping together are a period long at the pitch. Computed as
   `kq = 1 − q = 2 cos(P + w0/2) sin(w0/2) / sin(w0 + P)`, a product with no cancellation at low pitches, and one
   division (`divq`: the divisor's 16 top bits, 2⁻¹⁴ of the quotient). P = atan(1/R) less its value at 127 times b/127,
   R = 4 · 64^(b/127): at low pitches the cutoff is R harmonics of the pitch.
4. **The loop**: `y = hp + gt lp`, saturated, written back into the line. gt is the gain a period for the Decay,
   g = 2^(−L E), E = log2(1000) / (48000 T60) (`RESO_E`, `RESO_EXP`), times the damping's loss at the pitch given back,
   `1 / |H(w0)| = cos(w0/2) / cos(P + w0/2)`, the excess `2 sin((w0 + P)/2) sin(P/2) / cos(P + w0/2)` (one division),
   so that Decay holds whatever the tone, as long as gt stays under **G_MAX = 1 − 2⁻¹²**. G_MAX is the loop's
   gain at DC too (the damping passes DC whole): it must stay under 1, so a dull or high pitch held long decays sooner
   than Decay asks (§7, §11).
5. **The input's scale**: nrm = √(1 − g²) (`RESO_SQRT` after an even shift): white noise comes out as loud as it went
   in when nothing damps it.
6. **The output**: `(1 − a) x + a y`, a = Amount (0x7f00 → just under 1).

The coefficients are worked out only when Pitch, Tone or Decay has moved (the words of the last time kept), from
tables by value interpolated on the word's low byte: the period in 20.12 (`RESO_L`), sin and cos of w0/2 (`RESO_SH`,
`RESO_CH`), P and sin, cos of P/2 (`RESO_P`, `RESO_SP2`, `RESO_CP2`); sin and cos of w0 and of P come from them by the
double angle, cos(P + w0/2), sin(w0 + P) and sin((w0 + P)/2) by the sum, all in Q31 products. Linear interpolation of
the period between semitones: at most 0.7 cents off in the middle.

## 4. The line, off, silence

- **The line**: 5 920 frames a track (185 blocks: the longest period, 5 871 frames at note 0, and a block more), then
  32 frames that repeat the first 32 (a window read across the end), and one the loop reads ahead: 23 812 bytes a
  track, 143 424 bytes of variables with the six tracks' state, in the payload's variables (with every card of the
  page the payload ends at `0x4316865c`, far under CHORD Tables' claim at `0x43400000`). The block's 32 frames are
  written at a multiple of 32, so the writes never cross the end; when they start the line, they go into its copy, which
  the reads see, and are copied to the start after the block.
- **Off** (Amount 0): the block untouched; the comb starts again from nothing. A reset (the track coming to Reso) the
  same. The line is not cleared then (six lines of 24 KB in one block would cost tens of thousands of instructions):
  each block clears the frames it is about to read that were written before the comb started, at most 33.
- **Silence**: the comb counts the frames since its output last reached 2⁻¹⁵ of full scale (−90 dB; since 0.2 a
  block's RMS, from its energy in acc1, every frame in 0.1); after a whole line of them, a silent block (all 32 frames 0) is not run, the comb starts again from nothing (128 instructions). After a
  reset or Off the line counts as silent at once, so a track that gets nothing costs nothing from its first block.
- The EMAC truncates, so the loop carries a small DC of its own (−0.5 LSB a sum, gained by the loop at DC): estimated
  at most about −66 dBFS with the longest, dullest settings (measured −75 dBFS with kicks at C2, Tone 0, §7),
  inaudible; it can keep a track from counting as silent there (it then costs as a playing one).

## 5. The device code

`reso_cf.S`, `reso_frames(st)`: two frames a turn (four since 0.2), the input in d0/d1 and the window in a4/a5 in turn;
v1, lp, hp, y, η, the quiet test in d2 to d7 (in acc1 since 0.2); every other constant comes into a6 on the MAC before its first use (MAC with load:
`mac.l Ry,Rx,d16(a3),a6,acc0` uses a6 and loads the next one), and so do the input and the window's next frame:
**20 instructions a frame** (19 since 0.2; GCC's C loop took 31.5: it reloaded the constants from the stack; a large inline asm made
GCC 16.2 stop with an internal error in its scheduler). The state struct's offsets are checked at compile time in
`reso.c`. `reso.c` keeps the same loop in C under `RESO_HOST`, the proof's model: the same products in the same
accumulator in the same order, the EMAC as `tools/emu/emac.py` executes it (POTS's host model).

## 6. Cost

Measured outside the repository with the ColdFire interpreter of notes/69 §20.1, a copy fixed for this
(`_scratch/reso-bench/`: `cfemu.py`, `bench.py`), on the device object, the proof's cost states and a drum signal of
its own (so the shares matter, not the counts), instructions a track and block:

| State | Words (k 28, 29, 30, 31) | 0.1, interpreter | 0.1, the proof (§8) | 0.2, interpreter | 0.2, the proof (§13) |
|---|---|---|---|---|---|
| off | C4, 0, 64, 64 | 23 | 23 | 24 | 24 |
| mid | C4, 127, 64, 64 | 811 | 709 | 771 | 674 |
| low | C1, 127, 127, 32 (the line still being cleared) | 901 | 772 | 822 | 706 |
| high | C7, 127, 127, 32 | 811 | 698 | 771 | 664 |
| glide | every word jumping every block | 1 275 | 1 083 | 1 128 | 961 |
| silent | no note | 128 | 128 | 128 | 128 |
| first | its reset and first block | 1 375 | 1 233 | 1 225 | 1 106 |

The most in 3 000 blocks of random words, notes, silences and resets: 1 434 (the coefficients, the clearing and the
copy in one block). The proof's signal (the stock machines, a note at the start) counts 10 to 15 % lower; its counts
are the declared `cost.emulation`: six tracks on Reso, by the first block, 7 398 instructions a block, 6.8 % (Samples
8 952, 8.3 %); with 0.2 6 636, 6.1 %. Code and tables 8 688 bytes (tables 5 948), the build alone adds 14 376 bytes to the image.

The interpreter needed fixes, noted in `_scratch/reso-bench/FINDINGS.md`: objdump prints an indexed mode's
displacement in hex (`%a0@(38,%a1:l)` is 56), which `cfemu.py` read as decimal (every `state[track].field` went to
the wrong address; device and host differed in 1 344 of 1 500 blocks until fixed); `move.l Rx,%acc0` in fractional
mode, `move.l %acc0,Rx`, `btst` and MAC with load were missing.

## 7. Measured on the host

`_scratch/reso-bench/sound.py` on the host build (the same arithmetic as the device, §5):

- **Pitch** (an impulse, Amount 127, Decay 127, the spectral peak): Tone 127 and 64 within 0.13 cents from note
  24 to 96, +5 to +6 at 108; Tone 0 within 0.2 cents to 84, −0.5 at 96, −1.4 at 108; between semitones −0.5 to
  −0.7 cents (the table's interpolation).
- **Decay** (C4, the fundamental's −10 to −40 dB, doubled): 0.467 s for 0.458 at 64, 2.19 for 2.19 at 96, 10.0 for 10
  at 127, with Tone 127 or 64; Tone 32 holds up to 4.8 s, Tone 0 to 0.76 s (G_MAX, §3.4). At C6
  with Decay 96: 2.19 s bright, 0.14 s at Tone 0; at C7: 2.19 bright, 0.71 at 64, 0.05 at 0. Short decays are
  under this measure's resolution.
- **Level**: white noise in, Amount 127: 0 dB at Decay 0, −4 to −7 at 64, −14 to −18 at 127 (Tone 64: the
  damped harmonics give their energy up faster than the fundamental the scale is set for). A drum loop (kick, snare,
  hats, peaks at full scale) at Amount 127: the loudest 300 ms 2 to 5 dB under the dry loop when bright, 2.5 to 8 dB
  at Tone 20; peaks reach full scale at short decays (saturated, no wrap).
- **DC**: kicks every 0.5 s at C2, Decay 127: −75 dBFS at Tone 0 (the truncation's own, §4), −69 falling to
  −116 at 64.
- **A full-scale sine at the pitch**, Decay 127, Tone 127: the comb saturates (86 % of the frames at full
  scale), bounded.
- **Amount 0**: the input bit for bit.
- Listening samples, rendered by the host build: `_scratch/reso-bench/audio/` (hats dry, through Reso at C4, a
  melody of p-locked pitches, dark and bright with a long decay; a kick at half Amount; noise under a pitch sweep).

## 8. The proof

Done here (2026-11-01):

- the device object (`reso.c` + `reso_cf.S` as the manifest compiles them) against the host build in the interpreter:
  **3 000 blocks, none differ** (random words with every corner, notes, silences, full scale, resets);
- the host build under the undefined-behaviour and address sanitizers, with and without `-fwrapv` (signed overflow
  checked): every corner of the four words (outside 0 .. 0x7f00 too) against full-scale, alternating, silent and noisy
  blocks, notes, resets, a track out of range, 20 000 random blocks: **no fault**; Amount 0 untouched in all 16 524
  blocks that had it; and **14.6 million coefficient sets** on a fine grid of the words, all in range (0 < kq ≤ 1,
  kq + q = 1, 0 ≤ gt ≤ G_MAX, η within (−¼, ½), 1 ≤ dint ≤ LEN − 34). The sanitizer found one fault, fixed: `divq`
  overflowed to a negative coefficient when the quotient came within 2⁻¹⁵ of 1 (Tone just under 127); device and
  host had the same fault, so the bit-for-bit comparison could not see it;
- `tools/emu/emac.py` takes all 32 EMAC instructions of `reso_cf.S` (MAC with load included), run through its
  decoders without Unicorn;
- `test_fltslot.py --dry` **ALL OK**: Reso alone, and the full table of eight (OFF, SMP, CRU, RES, R51 .. R54, REF), its
  start words (4: 0x3c00 0x0000 0x4000 0x4000), the composer's refusals.

The maintainer's run (Unicorn stops with SIGILL in the sandbox), in this worktree:

```sh
"../.venv-emu/bin/python" tools/emu/test_fltslot.py --cycles "../model27/firmware/model-cycles_OS1.13.syx"
```

**The maintainer's run (2026-11-01): ALL OK but Reso's cost line, by design** (its manifest declared nothing yet).
Reso bit for bit its host build in every scene, alone and in the full table of eight (OFF, SMP, CRU, RES, R51 .. R54,
REF): the crossfades, MACSR and the accumulators, the registers and the stack, no access outside memory, the boot's
tables (descriptors 1 to 4 on k 28 to k 31, CC 74 / 71, a new sound's defaults), the knob lookup (RETRIG + SWEEP /
CONTOUR / COLOR / SHAPE, the names Reso Pitch ..), LFO + a knob, the formatters, the type's steps (OFF, RES; through
the nine entries in the full table), the start words (a step to RES gives Pitch 0x3c00), the p-locks, a machine
change, the record (slots 28 to 31 relative to the neutral words), the load. Counted, instructions per track and
block: off 23, mid 709, low 772, high 698, glide 1 083, silent 128, first 1 233, now declared in the manifest
(`tests.emulation.date` 2026-11-01). The part with every track on Reso and Amount 0: 489 instructions a block.

## 9. Built (2026-11-01)

- **Reso 0.1** (`tools/machines/reso/`: `reso.c`, `reso_cf.S`, `reso_tab.h` written by the generator, `reso.o`,
  `manifest.json`, MIT `LICENSE`).
- **`75-reso.json`** (`tools/gen_reso.py`, 15 writes, 274 conflicts). Checks green: `gen_reso.py --check`,
  `check_overlaps.py`, `claims.py --check --self-test`, `gen_flasher_tweaks.py --check`, `py_compile`.
  `registry.py --check` and the other composed tweaks' `--check` (27, 28, 29, 34, 36, 39, 70, 72, 73: reso joins
  their conflicts) differ by design until the merge (notes/73 §16.2).
- MAIN OS: Reso alone `0a4eba0e…`, with Samples and Crush `b274ee03…`, every card of the page with Reso `5a8d16a6…`,
  the same measuring (`--diag-filters`) `4cd103c2…`. Builds in `build/reso-0.1/` (git-ignored), each checked by
  elektron-firmware-tool (checksums and HMAC, the same MAIN OS).

## 10. For the machine

After the proof, from `build/reso-0.1/`:

- RETRIG + PITCH: OFF, RES (with Samples and Crush: OFF, SMP, CRU, RES). A fresh sound → RES reads Pitch 60 and Amount
  0, and sounds unchanged.
- Hats or a noisy snare, Amount 127: a pitched ring; Pitch by semitones (a p-lock per step: a melody on one track);
  against a tuned instrument at the same note: in tune?
- Tone 0 → 127 (dull to metallic), Decay 0 → 127; the dull end at a high pitch decays sooner (§7).
- A kick through it, Amount half way; a long decay with kicks: no thumping, no growing offset.
- Pitch at 0 to 16: short metallic echoes. LFO + RETRIG + SWEEP (PTCH) on Pitch, TRACK + RETRIG + a knob, CC 74 / 71.
- Switching SMP ↔ CRU ↔ RES while it plays; save and reload.
- The measuring build, six tracks on Reso: the type's popup shows the peak load.
- Listen: is the level right (§1, the scale)? Is 4 harmonics dark enough, too dark? Is 10 s long enough?

## 11. Known and open

- The pitch is the knob's: it cannot follow the played note (the slot passes the block, the four values, the track
  and the trig bit only).
- A dull or high pitch cannot ring as long as Decay asks: the damping takes its loss at the pitch, and the loop's
  gain may not go over G_MAX to give it back (its DC mode would grow). Tone 0 holds up to about 0.76 s at C4 and
  0.14 s at C6; Tone 64 up to 0.7 s at C7. A pitch-dependent darkness (gentler at high pitches) or a second-order
  damping (a flatter passband, about +8 instructions a frame) would ease it, if the maintainer wants.
- The allpass's coefficient is exact at low pitches only: +5 cents at 8 kHz.
- The wet path carries a DC of the EMAC's truncation, estimated at most about −66 dBFS (§4).
- `[HYP]` the load on the device (the measuring build tells; the proof counts 6.1 % of a block for six tracks, 0.2).

## 12. Tested on the machine (2026-11-01)

The maintainer flashed the build with Samples, Crush and Reso from `build/reso-0.1/`
(`model-cycles_OS1.13-smpfilter+crush+reso.syx`, MAIN OS `b274ee03…`, from the command line) on their Model:Cycles,
after the list of §10: « passt ». The load the measuring build shows was not reported. Experimental on the page until
flashed from it, as Samples and Crush were (notes/72 §20, notes/73 §15).

## 13. Lighter, the same sound: Reso 0.2 (2026-11-01)

The maintainer: « prüfen ob ud wie performance optimiert werden kann », then « Ja, übernehmen ».

- **Measured outside the proof**, with the interpreter of §6 on the device objects (`_scratch/reso-opt/`: the copy
  and `compare.py`, which runs the copy's device object against its host build and that host build against the
  package's). Where 0.1 spent its instructions, a track and block: the frame loop 686 (21 a frame), the rest of
  `reso_process` 125, the clearing at low pitches 89, the coefficients 464 (the two divisions 72). The frame loop is
  close to its least: every product in it is needed.
- **Kept** (Reso 0.2), each measured against 0.1 (held / C1 / gliding / first):
  1. the frame loop four frames a turn (two before): −16 everywhere;
  2. the line's old frames cleared by `reso_zero` in `reso_cf.S`, eight a `movem` (GCC's loop took 2.25
     instructions a frame): −47 at low pitches and in the first block;
  3. the silence test on the block's energy, `mac.l y,y,acc1`, one instruction a frame where `y + THR` or-ed took
     two: −33 wherever the comb plays. The test becomes the block's RMS under 2⁻¹⁵ of full scale (−90 dB) instead of
     every frame under it, so a fading tail may be skipped a block sooner or later; the sound is otherwise the same;
  4. `work_out` a function of its own (`noinline`: GCC then keeps `reso_process`'s registers), `divq` inlined into it:
     −62 when a word moves and in the first block, +7 held.

  Together, in the interpreter: 811 → 771 held (−5 %), 901 → 822 at C1 (−9 %), 1 275 → 1 128 gliding (−11.5 %),
  1 375 → 1 225 first (−11 %). 3 000 blocks: the device object against its host build, and that host build against
  0.1's, **none differ**; the sanitizers and the coefficient sweep of §8 clean; `emac.py` takes the new forms (acc1).
  Code and tables 8 610 bytes (8 688).
- **Left** (estimated, not built): the per-block bookkeeping in assembly (about −40 to −50 held), the coefficients in
  assembly (about −100 to −150 when a word moves): a second assembly part with a C model of its own, for little.
- MAIN OS: Reso alone `54ec2859…`, with Samples and Crush `4e31c87f…`, every card of the page with Reso `8dede451…`,
  the same measuring `0b511881…`. Builds in `build/reso-0.2/`, each checked by elektron-firmware-tool.
- **The proof, the maintainer's run (2026-11-01): ALL OK but Reso's cost line, by design** (0.1's counts still
  declared). Reso 0.2 bit for bit its host build in every scene, alone and in the full table of eight, everything
  else as in §8. Counted for 0.2, now declared, instructions per track and block (0.1 in brackets): off 24 (23), mid
  674 (709), low 706 (772), high 664 (698), glide 961 (1 083), silent 128 (128), first 1 106 (1 233): −5 to −11 %,
  as the interpreter said. Six tracks at most 6 636 instructions a block, 6.1 % (6.8 %).

## 14. Tone on COLOR, Decay on SHAPE: Reso 0.3 (2026-11-01)

The maintainer, after the main session compared the stock machines' knobs: « beide tauschen », and « pass auch direct
das word "Brightness" an, das ist zu lang für den kasten in dem es steht ».

- **Why**: on the stock machines COLOR holds the colour or the tuning of the sound (a tune offset, a ratio, an
  inharmonicity) and SHAPE its strength, often with feedback (METAL, KICK, SNARE: modulation amount and feedback). The
  damping is the comb's colour; Decay is its feedback.
- **Reso 0.3**: k 30 (RETRIG + COLOR) is **Tone**, Brightness's law unchanged (dull at 0, every harmonic ringing as
  long as the pitch at 127), named **Reso Tone / TONE**; k 31 (RETRIG + SHAPE) is **Decay**, its law unchanged. The
  name: "Reso Brightness", 15 characters, does not fit the popup's box on the device ("Reso Amount", 11, and "Filter
  Cutoff", 13, do); "Reso Tone" has 9. In the code only `work_out`'s two last arguments change places (k 30 the tone,
  k 31 the decay); the cost states of the manifest have their two last words swapped to stay the same states.
- **The start words** are unchanged: the neutral words of k 30 and k 31 are both 0x4000 and neither declares a start
  (`--dry`: 4: 0x3c00 0x0000 0x4000 0x4000).
- **The same sound**: 0.3 with the words (pitch, amount, tone, decay) against 0.2 with (pitch, amount, decay, tone), the
  host builds, 20 000 blocks of random words, notes, silences and resets: **none differ**. The device object against
  its host build in the interpreter, 3 000 blocks: none differ (the cost there as 0.2's: 771 held, 1 128 gliding). The
  sanitizers and the coefficient sweep clean; `gen_reso.py --check`, `check_overlaps.py`, `claims.py --check
  --self-test` green; `test_fltslot.py --dry` ALL OK.
- **Known**: a sound saved with Reso 0.1 or 0.2 reads its two values the other way round (its Decay as Tone, its
  Brightness as Decay): only the maintainer's test sounds, nothing was published.
- MAIN OS: Reso alone `c92e3d14…`, with Samples and Crush `8dc2d4c2…`, every card of the page with Reso `f14b2b21…`,
  the same measuring `b09f4824…` (the slot's data block 5 bytes shorter: the names). Builds in `build/reso-0.3/`, each
  checked by elektron-firmware-tool.
- **The proof, the maintainer's run (2026-11-01): ALL OK**, the cost line too: Reso 0.3 counts what 0.2 counted (off
  24, mid 674, low 706, high 664, glide 961, silent 128, first 1 106; the swapped states take the same paths); the knob
  lookup names the values Reso Pitch .. in every build, the record keeps slots 28 to 31 as before.
- **On the machine (2026-11-01)**: the maintainer, after the build with Samples and Crush from `build/reso-0.3/` and
  the check asked for (Reso Tone on RETRIG + COLOR, Reso Decay on RETRIG + SHAPE, both in the popup's box): « getestet,
  passt ».

## 15. For the integration

What the shared files get when Reso is merged (they stay untouched on this branch, notes/73 §16.2).

**`FEATURES`** (`tools/gen_flasher_tweaks.py`, after Crush):

```python
    {
        "id": "reso",
        "cat": "sound",
        "label": "Reso (Track FX)",
        "desc": "A tuned resonator on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound Reso; "
                "RETRIG + SWEEP is Pitch (the MIDI note, 60 = C4), RETRIG + CONTOUR Amount (0 off), RETRIG + COLOR "
                "Tone, RETRIG + SHAPE Decay, with p-locks, LFO and CC 74 / 71.",
        # model27's own (notes/75): a comb through the filter slot (fltslot 0.9); bit for bit the host build of the
        # same source in emulation; on the Model:Cycles with Samples and Crush from the command line on 2026-11-01
        # (notes/75 §12)
        "status": "experimental",
        "credit": {"kind": "by", "who": "durchgemacht", "repo": "durchgemacht/model27"},
        # a Track FX composed in the page from its package (notes/75), with the machines, effects and the other
        # Track FX ticked: alone it gives 75-reso.json byte for byte, whose conflicts give its excludes
        "package": "reso",
    },
```

and `"reso"` in `OFFERED`.

**The card** (`FEAT` in `docs/flasher/app.js`; `GUIDE_OF`: `reso: "reso"`):

```js
  reso: { label: "Reso",
    short: "A tuned resonator on any track: noise and hits ring at a pitch you set.",
    desc: "Hold RETRIG and turn PITCH to give the track's sound Reso (RES). Then hold RETRIG and turn SWEEP for Pitch: the value is the MIDI note, 60 is middle C (C4), 69 is A at 440 Hz; under about 16 it turns into a short metallic echo. RETRIG + CONTOUR sets Amount: 0 leaves the sound untouched, 127 leaves only the ringing. RETRIG + COLOR sets Tone, dull at 0 (the overtones die fast), every overtone ringing at 127; RETRIG + SHAPE sets Decay, from 20 ms to 10 seconds. Each time you switch to Reso it starts at C4 with Amount 0.\n\nAll four are real parameters of every machine: lock them on a trig (a melody of pitches on one track), make them the LFO's destination (hold LFO and RETRIG and turn the knob), set them on all tracks with TRACK, or send CC 74 (Pitch) and 71 (Amount). Each sound keeps its own settings, saved with it. The pitch does not follow the notes you play: it is the knob's. Reso comes after Volume + Dist.",
    note: "A dull or high pitch rings shorter than Decay asks. A sound saved on this firmware loses Reso on another firmware, nothing else." },
```

**The guide** (`docs/guide/index.html`, after Crush, the sections after it renumbered; `<li><a href="#reso">Reso</a></li>`
in the contents; Samples' and Crush's lists of Track FX and "Other mods" name Reso too):

```html
      <section id="reso">
        <h2><span class="n">8</span>Reso</h2>
        <p class="by">model27's own · MIT license</p>
        <p class="lede">A tuned resonator on any track, after Volume + Dist: hats, noise and hits ring at a pitch you set, like a plucked string or a struck tube. It is a Track FX: each sound chooses one, or none.</p>
        <ol>
          <li>Hold <b>RETRIG</b> and turn <b>PITCH</b> to the right: every four detents the track's sound steps to the next Track FX: OFF, then <b>SMP</b> and <b>CRU</b> if the <a href="#samples-filter">Samples filter</a> and <a href="#crush">Crush</a> are ticked too, then <b>RES</b>. To the left it steps back. Reso starts at C4 with Amount 0, so nothing changes until you turn.</li>
          <li>Hold <b>RETRIG</b> and turn <b>CONTOUR</b> for <b>Reso Amount</b>: at 0 the sound passes untouched, at 127 only the ringing is left, in between both.</li>
          <li>Hold <b>RETRIG</b> and turn <b>SWEEP</b> for <b>Reso Pitch</b>: the value is the MIDI note, 60 is middle C (C4), 69 is A at 440 Hz, 72 is C5; one step is a semitone, FUNC turns finer. From 0 to about 16 it is a short metallic echo rather than a tone.</li>
          <li>Hold <b>RETRIG</b> and turn <b>COLOR</b> for <b>Reso Tone</b>: at 0 dull, the overtones die fast and the pitch rings on; at 127 every overtone rings as long as the pitch, bright and metallic.</li>
          <li>Hold <b>RETRIG</b> and turn <b>SHAPE</b> for <b>Reso Decay</b>: how long it rings, from 20 ms at 0 to 10 seconds at 127 (half a second at 64), the same on every pitch.</li>
          <li>All four are parameters like any other: hold a trig as well to lock them on that step (a pitch per step plays a melody), hold <b>LFO</b> as well to make them the LFO's destination (it reads PTCH, AMT, TONE or DEC), hold <b>TRACK</b> as well to set them on all six tracks, or send CC 74 (Pitch) and CC 71 (Amount).</li>
          <li>Save the kit or the project: each sound keeps its Track FX and its settings.</li>
        </ol>
        <dl class="facts">
          <div><dt>Sound</dt><dd>the pitch is the knob's: it does not follow the notes you play. Noise comes out about as loud as it goes in; a single hit rings quieter the longer it rings. A dull or high pitch rings shorter than Decay asks. At Amount 0 the sound passes untouched. Values glide in, as any parameter does on the Model:Cycles.</dd></div>
          <div><dt>Other mods</dt><dd>goes with SAMPLE, the effects, the Samples filter, Crush and Control All Config. A sound has one Track FX at a time. On a firmware without Reso, the official one too, a sound plays without it and keeps everything else.</dd></div>
          <div><dt>Tested</dt><dd>checked in an emulator on the OS's own code, bit for bit against its own code built for a computer. Played on a Model:Cycles (2026-11-01) from the command line.</dd></div>
        </dl>
      </section>
```

**The release** (`docs/assets/release.js`, a new entry or the merge's):

```js
    { en: "New card in Track FX, Reso: a tuned resonator on any track, so that hats, noise and hits ring at a pitch. RETRIG + SWEEP is Pitch, the MIDI note (60 = C4), RETRIG + CONTOUR is Amount (0 off), RETRIG + COLOR is Tone (dull to metallic), RETRIG + SHAPE is Decay (20 ms to 10 s). All four work on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71" },
    { en: "Reso is checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01); experimental here until flashed from this page" },
```

**`README.md`** (the overview paragraph, after Crush): « The ninth, **Reso**, model27's own third Track FX, makes a
track ring at a pitch you set, like a plucked string or a struck tube, on four knobs. » (and the card count).

**`BUILD.md`** (French, after « Crush (Track FX) »):

```markdown
### Reso (Track FX)

`tweaks/model-cycles_OS1.13/75-reso.json` est produit par `tools/gen_reso.py`, qui écrit les tables
(`tools/machines/reso/reso_tab.h`), compile `tools/machines/reso/reso.c` et `reso_cf.S` et le compose seul avec
`tools/compose.py` : le Track FX 4 du slot de filtre, un résonateur en peigne ([note 75](notes/75-reso.md)). RETRIG +
SWEEP est Pitch (la note MIDI, 60 = C4 ; un son qui passe à Reso part de C4), RETRIG + CONTOUR Amount (0 : la piste
intacte, au bit près), RETRIG + COLOR Tone (de sourd à métallique), RETRIG + SHAPE Decay (20 ms à 10 s). La preuve est celle du filtre
Samples, avec Reso au bit près contre le build hôte de `reso.c` (la boucle en C, modèle de `reso_cf.S`).

    python3 tools/gen_reso.py --cycles model-cycles_OS1.13.syx [--check]
    python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines reso
    python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines smpfilter,crush,reso   # avec Samples et Crush

MAIN OS patché, `reso` seul : `c92e3d1462638eb255b46b43441eeac9524722848fe362d7a5a9fb5447119cef` ; avec Samples et
Crush : `8dc2d4c26dfc1a205fc78c74dd0176fa83d2874be271275c1fecec59590ec7cb` ; avec toutes les cartes de la page :
`f14b2b21591c1dbf58105b12256e6a0fc7a4fdb9072f4969fca9daf29dc87dd1` (Reso 0.3, Tone sur COLOR et Decay sur SHAPE, sur
`fltslot` 0.9, avant la fusion avec Ring et EQ ; avec Reso 0.2, Decay sur COLOR et Brightness sur SHAPE : `54ec2859…`,
`4e31c87f…`, `8dede451…` ; avec Reso 0.1, le même son : `0a4eba0e…`, `b274ee03…`, `5a8d16a6…`). Reso 0.1 avec Samples et Crush joué
sur un Model:Cycles depuis la ligne de commande le 01/11/2026 (note 75 §12).
```

**`tweaks/model-cycles_OS1.13/PROVENANCE.md`**:

```markdown
| `75-reso.json` | durchgemacht and Claude (model27) | Reso, a Track FX (notes/75): a tuned resonator, a comb with an allpass and a damping in its loop, model27's own code (`tools/machines/reso/reso.c`, its frame loop in `reso_cf.S`, its tables `reso_tab.h` written by `tools/gen_reso.py`), compiled by `tools/gen_reso.py` and composed alone by `tools/compose.py` with the parts `fltslot` (0.9) and `shortcuts`; no third-party code. On the device bit for bit the host build of `reso.c`, checked in the emulator by `tools/emu/test_fltslot.py`. Card in the flasher, experimental. |
```

**`notes/README.md`**:

```markdown
| [75-reso.md](75-reso.md) | **Reso: a tuned resonator in the Track FX (2026-11-01, English)**: the maintainer's decisions (a comb rather than a bank of modes; Pitch on SWEEP as the MIDI note, Amount on CONTOUR, 0 dry and the start, Tone on COLOR, Decay on SHAPE, swapped and renamed from Brightness in 0.3, §14); id 4, "RES"; the comb: a DC blocker, the line through a first-order allpass, a one-pole damping whose phase at the pitch is exact (q = sin P / sin(w0 + P)), the loss given back up to a gain of 1 − 2⁻¹² (its DC mode), the input scaled for noise; in tune within 0.2 cents (C1 to C7), Decay as asked when bright; the line cleared lazily, a silent track skipped; the frame loop in ColdFire assembly (MAC with load, 20 instructions a frame), its C model the proof's; cost counted by the proof 709 held, 1 083 gliding, 1 233 first, six tracks 6.8 % of a block (Samples 8.3 %); 0.2 the same sound in 5 to 11 % fewer instructions (the loop four frames a turn, the silence test on acc1, the clearing by movem, the coefficients apart, §13): 674 held, 961 gliding, 1 106 first, 6.1 %, ALL OK in the maintainer's run; sanitizers and 3 000 blocks bit for bit in the interpreter; **`test_fltslot.py` ALL OK in the maintainer's run (2026-11-01)**; **played on the machine 2026-11-01** (with Samples and Crush, from the command line, « passt »). |
```

**`AGENTS.md`** (the repository map, after `tools/machines/crush/`; and in « Adding a feature », 77 the next free note):

```
tools/machines/reso/          Reso (notes/75): a tuned resonator, a comb, the Track FX's id 4; reso_cf.S its frame loop
                              (EMAC, MAC with load), reso.c the rest and the loop's C model for the host;
                              tools/gen_reso.py writes its tables and builds it into 75-reso.json; proven by
                              test_fltslot.py from its manifest's proof section
```

**Generated again at the merge**: `docs/flasher/tweaks.js`, `REF_MAINOS` and `REF_MODS` (`tools/ref_mainos.py`),
`tweaks/model-cycles_OS1.13/REGISTRY.md` (`tools/registry.py`), the composed tweaks whose conflicts gain reso (27,
28, 29, 34, 36, 39, 70, 72, 73 through their generators), `webcompose_synth.py`'s selections if Reso joins them, the
lists of `tools/webflash_smoke.js`; then the checks of AGENTS.md, with the firmware.

## 16. Merged, tested from the page (2026-11-01)

Merged into `main` with Ring and EQ (notes/73 §17, release 0.28): the maintainer's proof on the merge ALL OK, the build of
every card played on the Model:Cycles, then a build flashed from the page: « getestet, passt » (notes/73 §18, release
0.29). The card is tested.

## 17. A fifth fewer where it is dearest: Reso 0.4 (2026-11-04)

The main session, for the maintainer: « Senke die CPU-Last der Track FX Reso und EQ » (a change of sound allowed, a
listening test deciding; bit-for-bit gains need none); after the report, « Reso B+E4, EQ B ».

### 17.1 Measured outside the repository

A prototype with one switch per idea (`_scratch/reso-opt2/`, its `REPORT.md`) against 0.3 in the ColdFire interpreter
(`_scratch/cfemu/cfemu.py`, notes/69 §20.1), on the manifest's cost states as the proof runs them (a new engine, the
slot's reset, 8 blocks of warm-up, the most of the next 8; `first`: 8 blocks on another filter, the reset and the
block). Where 0.3 spent its instructions in `first` (1 297 on the interpreter's own signal): the frame loop 639,
`reso_process` around it 314 (the silence test 96, the copy of the line's first 32 frames 60, the rest GCC keeping
its values on the stack), `work_out` 288, the clearing 38, the reset 18. Instructions a track and block (compare
shares, not counts):

| | mid | low | glide | silent | first | code |
|---|---:|---:|---:|---:|---:|---:|
| 0.3 | 771 | 821 | 1 127 | 128 | 1 297 | 2 682 B |
| A: `reso_process` in assembly | 709 | 744 | 1 059 | 70 | 1 085 (−16 %) | 2 342 B |
| B: A, and `reso_work_out` in assembly | 709 | 744 | 1 006 | 70 | 1 032 (−20 %) | 1 852 B |
| **B + E4: B, the energy from every fourth frame (kept)** | 685 | 720 | 982 | 70 | **1 008 (−22 %)** | 1 840 B |

- **The cost states hold the dearest case**: a sweep (held over Pitch × Tone × Decay, 300 random pairs gliding,
  `first` at every corner, 3 000 random blocks with resets and silences) finds at most 1 % more than `first` (0.3:
  1 305; B: 1 042).
- **The code's size**: with the cache model of notes/27 §2 (as notes/74 §13.1), B and B + E4 win under every
  assumption, the caches warm, the code cold once a block, everything cold at every call (`first`: 1 997 / 3 002 /
  4 727 cycles for 0.3, 1 552 / 2 507 / 3 832 for B + E4): the assembly is smaller than GCC's code.
- **E4's sound**: none of 100 000 random blocks differs from 0.3; aimed at it (a hit, then silence until the comb is
  let go, 72 settings, 9.2 million frames), 4 860 frames differ, at most 54 674 LSB, −91.9 dBFS: the tail is cut a
  block sooner or later. Nothing to hear; no listening page.
- **Dropped**: linear interpolation instead of the allpass (about −9 % more): the high harmonics would then die at a
  rate set by the period's fraction, some notes bright and others dull, which the allpass is there to avoid (§3).

### 17.2 `reso.c` 0.4, `reso_cf.S`

- **`reso_process` in `reso_cf.S`** on the device: the bookkeeping in registers, the frame loop inline (four frames a
  turn, as 0.2), the silence test stopping at the first frame that is not 0, the line's lazy clearing eight frames a
  `movem`, the copy of the line's first 32 frames by four `movem` pairs. The state is the same `struct track`, its
  offsets checked at compile time; `reso_state` and `reso_line` are global for the assembly.
- **`reso_work_out` in `reso_cf.S`**, a section of its own (called by its address): `work_out`'s integer steps and
  EMAC products in the same order, the words clamped and kept there; the tables through `reso_tab`, their addresses in
  `reso.c` (the header's tables are static).
- **The silence test's energy** (E4): `mac.l y,y,acc1` on the first frame of each four only (`FRAME`, then three
  `FRAMEQ`), 18 instructions on those frames; the threshold a quarter (`QUIET_E` 16).
- **`reso.c`** keeps `reso_reset` for the device and, under `RESO_HOST`, the whole model: `work_out`, `frames()`,
  `reso_process`, the proof's.
- Code and tables 7 808 bytes (8 610), variables 143 424 (unchanged); 13 860 bytes added to the image (14 664).

### 17.3 Proven, checked

- The repository's host build against the prototype's B + E4 over 100 000 blocks (random words with every corner,
  notes, resets, silences): none differ. The device object, as the generator commits it (`reso.o`, linked alone), in
  the interpreter against its host build, 5 000 blocks: none differ (after each call the word behind the block
  untouched, every accumulator 0). The prototype's `reso_work_out` against GCC's code of the C over 153 000 word
  triples (every corner of the three words, in range and out, sweeps, random): the same coefficients and keys; four
  branches never run there, none reachable in range (§8). Two faults put into the assembly on purpose showed at once
  in the comparison. UBSan and ASan, 400 000 blocks, without `-fwrapv`: clean.
- `tools/emu/emac.py` takes the new forms (an address register as a product's operand and as `movclr`'s target);
  the MAC with load into one of its operands, `reso_cf.S` 0.3 already ran on the machine.
- **Green**: `gen_reso.py --check` and the other Track FX', parts', CPU page's, RESAMPLE's, POTS' and Digital
  Delay's generators, `check_overlaps.py`, `registry.py --check` and `gen_flasher_tweaks.py --check` (after
  regenerating them), `claims.py --check --self-test`, `webbuild_check.sh`, `webcompose_check.sh` with the official
  file, `webflash_check.sh`, `webmanager_check.sh`, `ref_mainos.py` (regenerated: only the combinations with Reso
  change), `py_compile`, and `test_fltslot.py --dry` ALL OK.
- **The proof**, the maintainer's run (2026-11-04, Unicorn, on the tree of this section): everything OK but Reso's
  cost line, as expected with 0.3's numbers still declared. Counted: off 18, mid 590, low 612, high 583, glide 830,
  silent 70, first 855 (0.3 declared 24, 674, 706, 664, 961, 128, 1 106: first −23 %, glide −14 %, held −12 %).
  These are now Reso's `cost.emulation` (tests dated 2026-11-04); the filters' load of a build with Reso as its
  dearest Track FX falls from 6 × 1 106 = 6 636 to 6 × 855 = 5 130 instructions a block (6.1 % → 4.7 %). The proof
  saves more than the interpreter's ratio foretold (about 880 in `first`), in part because its six tracks average one
  that is silent at the switch, which 0.4 lets go in 70 instructions instead of 128. After declaring them: the checks of the list above
  green again; the MAIN OS does not change (the cost is only reported).

MAIN OS, on `d320fa9`: Reso alone `7626270e…`, with Samples and Crush `ccdcf75a…`, with the CPU page `4bb34c3a…`
(0.3's: `3599328e…`), every card of the page `9e7c87d2…` (0.3's: `021d39d1…`); all as `REF_MAINOS` or
`webcompose_check.sh` give them. Builds in `build/reso-0.4/` (git-ignored): `reso/`, `smpfilter+crush+reso/`,
`reso-cpu/` and `reso03-cpu/` (0.3 with the CPU page, composed from `main`, to compare the TRACK FX line).

### 17.4 On the machine

The maintainer flashed `build/reso-0.4/smpfilter+crush+reso/` (Samples, Crush and Reso 0.4, from the command line) on
their Model:Cycles (2026-11-04), three tests, each « passt »:

1. Hats or noise through Reso, Amount 127, Pitch, Tone and Decay turned: as 0.3, no clicks.
2. Decay 127, Pitch about 12: a short metallic echo; a hit, rung out, five seconds of silence, another hit: the same
   as the first, nothing left of the old one (the comb let go and started again); an LFO on Pitch: a clean glide (the
   coefficients worked out every block).
3. Reso on all six tracks, Amount 127, a long Decay, a full pattern, switching a few times to a pattern without Reso
   and back: no dropout, no stutter, Reso starting cleanly each time (the first block of six tracks).

The CPU page's numbers (`reso-cpu/` against `reso03-cpu/`) were not measured. The card stays `tested`; the release
text says it was tried on the machine.
