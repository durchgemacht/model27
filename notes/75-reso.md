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
  A4 = 440 Hz, 8 Hz to 12.5 kHz), **Amount** (0 the track untouched, 127 the resonance alone), **Decay** (20 ms to
  10 s for the pitch to fall by 60 dB, the same on every pitch), **Brightness** (dull at 0, every harmonic ringing as
  long as the pitch at 127). All with p-locks, LFO, velocity, Control All; CC 74 / 71 on Pitch and Amount.
- **Off is dry and is the start**: Amount 0 gives the block back untouched, bit for bit; Amount's neutral word is 0,
  so a sound that steps to Reso starts there. Pitch starts at C4 (its start word 0x3c00, fltslot 0.8).
- **In tune at the pitch**: the allpass and the damping's phase are worked out so that the loop is exactly a period
  long at the pitch: measured within 0.2 cents from C1 to C7 on whole notes, 0.7 between them, +5 at 8 kHz (§7).
- **Never runs away**: the loop's gain stays under 1 − 2⁻¹² at DC and everywhere else, every sum saturates at full
  scale (the EMAC's), a DC blocker at 15 Hz keeps kicks from piling up in the loop.
- **Cost**, counted by the proof (§8, the maintainer's run): about 700 instructions a track and block held (709 at
  C4, 772 at C1 while the line is still being cleared), 1 083 when every word moves every block, 1 233 in the first
  block, 128 for a silent track, 23 off. Six tracks at most 7 398 instructions a block, 6.8 % (Samples' worst 8 952,
  8.3 %). The frame loop is ColdFire assembly (`reso_cf.S`, 20 instructions a frame, MAC with load); `reso.c`'s C
  loop is its host model, bit for bit. Not measured on the machine yet.

## 1. Decisions (2026-11-01)

Asked one at a time, with a recommendation each:

| Question | The maintainer | Consequence |
|---|---|---|
| Comb or a small modal bank (four modes with MODAL's material ratios)? | « Kamm » (the recommendation) | a comb: all harmonics, about 21 instructions a frame; four modes would cost about 1 300 to 1 500 a track and block and, as MODAL's round 1 heard, leave mostly a sine (MODAL's eight modes cost about 4 000) |
| The knobs: SWEEP Pitch (the MIDI note), CONTOUR Amount (0 dry), COLOR Decay, SHAPE Brightness? | « Wie vorgeschlagen » | Pitch and Amount on the two knobs with a CC |

Decided here, within that design (for the maintainer to change after listening):

| What | Chosen | Why |
|---|---|---|
| Pitch's scale | the value is the MIDI note, `int` format 0 .. 127, whole values semitones, FUNC for the fine tune | the slot has no note formatter (`int`, `centre`, `cutoff`); a note number reads at once, p-locks make melodies |
| Pitch's start | C4 (0x3c00) | the neutral word 0x4000 would be E4 |
| Decay | T60 = 20 ms · 500^(d/127): 0.46 s at 64, 2.2 s at 96, 10 s at 127 | MODAL's range (20 ms to 8 s), a little longer |
| Brightness | the damping's cutoff from 4 harmonics of the pitch at 0 to 256 at 126, none at 127 | dull to metallic; the cutoff follows the pitch, so the timbre does not change with it |
| The level | white noise in, as loud out (the input scaled by √(1 − g²), g the loop's gain a period) | no growth with Decay, no clipping of noise; a single hit's ring gets quieter as it gets longer (the same energy), a drum loop at Amount 127 comes out 2 to 8 dB under the dry one (§7) |
| A note (the trig bit) | not read: the comb rings on | a resonator's tail is the point; a choke cannot reach the line's far end in time |

## 2. The values

| Where | What | Words | Neutral / start |
|---|---|---|---|
| k 28 (RETRIG + SWEEP, CC 74) | Pitch | 0 .. 0x7f00, the note in 8.8 | 0x4000 / **0x3c00** (C4) |
| k 29 (RETRIG + CONTOUR, CC 71) | Amount | 0 .. 0x7f00: 0 untouched, 0x7f00 the comb alone, a crossfade between | 0 (the start: off) |
| k 30 (RETRIG + COLOR) | Decay | 0 .. 0x7f00 | 0x4000 (0.46 s) |
| k 31 (RETRIG + SHAPE) | Brightness | 0 .. 0x7f00 | 0x4000 (32 harmonics) |

Names: Reso Pitch / PTCH, Reso Amount / AMT, Reso Decay / DEC, Reso Brightness / BRT; all `int`. Words outside
0 .. 0x7f00 (an LFO pushes them there) are clamped.

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
   the phase P of Brightness's table: q = sin P / sin(w0 + P) (from tan P = q sin w0 / (1 − q cos w0)); the line is then
   read P / w0 frames earlier, so that line, allpass and damping together are a period long at the pitch. Computed as
   `kq = 1 − q = 2 cos(P + w0/2) sin(w0/2) / sin(w0 + P)`, a product with no cancellation at low pitches, and one
   division (`divq`: the divisor's 16 top bits, 2⁻¹⁴ of the quotient). P = atan(1/R) less its value at 127 times b/127,
   R = 4 · 64^(b/127): at low pitches the cutoff is R harmonics of the pitch.
4. **The loop**: `y = hp + gt lp`, saturated, written back into the line. gt is the gain a period for the Decay,
   g = 2^(−L E), E = log2(1000) / (48000 T60) (`RESO_E`, `RESO_EXP`), times the damping's loss at the pitch given back,
   `1 / |H(w0)| = cos(w0/2) / cos(P + w0/2)`, the excess `2 sin((w0 + P)/2) sin(P/2) / cos(P + w0/2)` (one division),
   so that Decay holds whatever the brightness, as long as gt stays under **G_MAX = 1 − 2⁻¹²**. G_MAX is the loop's
   gain at DC too (the damping passes DC whole): it must stay under 1, so a dull or high pitch held long decays sooner
   than Decay asks (§7, §11).
5. **The input's scale**: nrm = √(1 − g²) (`RESO_SQRT` after an even shift): white noise comes out as loud as it went
   in when nothing damps it.
6. **The output**: `(1 − a) x + a y`, a = Amount (0x7f00 → just under 1).

The coefficients are worked out only when Pitch, Decay or Brightness has moved (the words of the last time kept), from
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
- **Silence**: the comb counts the frames since its output last reached 2⁻¹⁵ of full scale (−90 dB); after a whole line
  of them, a silent block (all 32 frames 0) is not run, the comb starts again from nothing (128 instructions). After a
  reset or Off the line counts as silent at once, so a track that gets nothing costs nothing from its first block.
- The EMAC truncates, so the loop carries a small DC of its own (−0.5 LSB a sum, gained by the loop at DC): estimated
  at most about −66 dBFS with the longest, dullest settings (measured −75 dBFS with kicks at C2, Brightness 0, §7),
  inaudible; it can keep a track from counting as silent there (it then costs as a playing one).

## 5. The device code

`reso_cf.S`, `reso_frames(st)`: two frames a turn, the input in d0/d1 and the window in a4/a5 in turn; v1, lp, hp, y, η,
the quiet test in d2 to d7; every other constant comes into a6 on the MAC before its first use (MAC with load:
`mac.l Ry,Rx,d16(a3),a6,acc0` uses a6 and loads the next one), and so do the input and the window's next frame:
**20 instructions a frame** (GCC's C loop took 31.5: it reloaded the constants from the stack; a large inline asm made
GCC 16.2 stop with an internal error in its scheduler). The state struct's offsets are checked at compile time in
`reso.c`. `reso.c` keeps the same loop in C under `RESO_HOST`, the proof's model: the same products in the same
accumulator in the same order, the EMAC as `tools/emu/emac.py` executes it (POTS's host model).

## 6. Cost

Measured outside the repository with the ColdFire interpreter of notes/69 §20.1, a copy fixed for this
(`_scratch/reso-bench/`: `cfemu.py`, `bench.py`), on the device object, the proof's cost states and a drum signal of
its own (so the shares matter, not the counts), instructions a track and block:

| State | Words (k 28, 29, 30, 31) | Interpreter | The proof (§8) |
|---|---|---|---|
| off | C4, 0, 64, 64 | 23 | 23 |
| mid | C4, 127, 64, 64 | 811 | 709 |
| low | C1, 127, 127, 32 (the line still being cleared) | 901 | 772 |
| high | C7, 127, 127, 32 | 811 | 698 |
| glide | every word jumping every block | 1 275 | 1 083 |
| silent | no note | 128 | 128 |
| first | its reset and first block | 1 375 | 1 233 |

The most in 3 000 blocks of random words, notes, silences and resets: 1 434 (the coefficients, the clearing and the
copy in one block). The proof's signal (the stock machines, a note at the start) counts 10 to 15 % lower; its counts
are the declared `cost.emulation`: six tracks on Reso, by the first block, 7 398 instructions a block, 6.8 % (Samples
8 952, 8.3 %). Code and tables 8 688 bytes (tables 5 948), the build alone adds 14 376 bytes to the image.

The interpreter needed fixes, noted in `_scratch/reso-bench/FINDINGS.md`: objdump prints an indexed mode's
displacement in hex (`%a0@(38,%a1:l)` is 56), which `cfemu.py` read as decimal (every `state[track].field` went to
the wrong address; device and host differed in 1 344 of 1 500 blocks until fixed); `move.l Rx,%acc0` in fractional
mode, `move.l %acc0,Rx`, `btst` and MAC with load were missing.

## 7. Measured on the host

`_scratch/reso-bench/sound.py` on the host build (the same arithmetic as the device, §5):

- **Pitch** (an impulse, Amount 127, Decay 127, the spectral peak): Brightness 127 and 64 within 0.13 cents from note
  24 to 96, +5 to +6 at 108; Brightness 0 within 0.2 cents to 84, −0.5 at 96, −1.4 at 108; between semitones −0.5 to
  −0.7 cents (the table's interpolation).
- **Decay** (C4, the fundamental's −10 to −40 dB, doubled): 0.467 s for 0.458 at 64, 2.19 for 2.19 at 96, 10.0 for 10
  at 127, with Brightness 127 or 64; Brightness 32 holds up to 4.8 s, Brightness 0 to 0.76 s (G_MAX, §3.4). At C6
  with Decay 96: 2.19 s bright, 0.14 s at Brightness 0; at C7: 2.19 bright, 0.71 at 64, 0.05 at 0. Short decays are
  under this measure's resolution.
- **Level**: white noise in, Amount 127: 0 dB at Decay 0, −4 to −7 at 64, −14 to −18 at 127 (Brightness 64: the
  damped harmonics give their energy up faster than the fundamental the scale is set for). A drum loop (kick, snare,
  hats, peaks at full scale) at Amount 127: the loudest 300 ms 2 to 5 dB under the dry loop when bright, 2.5 to 8 dB
  at Brightness 20; peaks reach full scale at short decays (saturated, no wrap).
- **DC**: kicks every 0.5 s at C2, Decay 127: −75 dBFS at Brightness 0 (the truncation's own, §4), −69 falling to
  −116 at 64.
- **A full-scale sine at the pitch**, Decay 127, Brightness 127: the comb saturates (86 % of the frames at full
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
  overflowed to a negative coefficient when the quotient came within 2⁻¹⁵ of 1 (Brightness just under 127); device and
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
- Decay 0 → 127; Brightness 0 → 127 (dull to metallic); the dull end at a high pitch decays sooner (§7).
- A kick through it, Amount half way; a long decay with kicks: no thumping, no growing offset.
- Pitch at 0 to 16: short metallic echoes. LFO + RETRIG + SWEEP (PTCH) on Pitch, TRACK + RETRIG + a knob, CC 74 / 71.
- Switching SMP ↔ CRU ↔ RES while it plays; save and reload.
- The measuring build, six tracks on Reso: the type's popup shows the peak load.
- Listen: is the level right (§1, the scale)? Is 4 harmonics dark enough, too dark? Is 10 s long enough?

## 11. Known and open

- The pitch is the knob's: it cannot follow the played note (the slot passes the block, the four values, the track
  and the trig bit only).
- A dull or high pitch cannot ring as long as Decay asks: the damping takes its loss at the pitch, and the loop's
  gain may not go over G_MAX to give it back (its DC mode would grow). Brightness 0 holds up to about 0.76 s at C4 and
  0.14 s at C6; Brightness 64 up to 0.7 s at C7. A pitch-dependent darkness (gentler at high pitches) or a second-order
  damping (a flatter passband, about +8 instructions a frame) would ease it, if the maintainer wants.
- The allpass's coefficient is exact at low pitches only: +5 cents at 8 kHz.
- The wet path carries a DC of the EMAC's truncation, estimated at most about −66 dBFS (§4).
- `[HYP]` the load on the device (the measuring build tells; the proof counts 6.8 % of a block for six tracks).

## 12. For the integration

What the shared files get when Reso is merged (they stay untouched on this branch, notes/73 §16.2).

**`FEATURES`** (`tools/gen_flasher_tweaks.py`, after Crush):

```python
    {
        "id": "reso",
        "cat": "sound",
        "label": "Reso (Track FX)",
        "desc": "A tuned resonator on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound Reso; "
                "RETRIG + SWEEP is Pitch (the MIDI note, 60 = C4), RETRIG + CONTOUR Amount (0 off), RETRIG + COLOR "
                "Decay, RETRIG + SHAPE Brightness, with p-locks, LFO and CC 74 / 71.",
        # model27's own (notes/75): a comb through the filter slot (fltslot 0.9); bit for bit the host build of the
        # same source in emulation
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
    desc: "Hold RETRIG and turn PITCH to give the track's sound Reso (RES). Then hold RETRIG and turn SWEEP for Pitch: the value is the MIDI note, 60 is middle C (C4), 69 is A at 440 Hz; under about 16 it turns into a short metallic echo. RETRIG + CONTOUR sets Amount: 0 leaves the sound untouched, 127 leaves only the ringing. RETRIG + COLOR sets Decay, from 20 ms to 10 seconds; RETRIG + SHAPE sets Brightness, dull at 0 (the overtones die fast), every overtone ringing at 127. Each time you switch to Reso it starts at C4 with Amount 0.\n\nAll four are real parameters of every machine: lock them on a trig (a melody of pitches on one track), make them the LFO's destination (hold LFO and RETRIG and turn the knob), set them on all tracks with TRACK, or send CC 74 (Pitch) and 71 (Amount). Each sound keeps its own settings, saved with it. The pitch does not follow the notes you play: it is the knob's. Reso comes after Volume + Dist.",
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
          <li>Hold <b>RETRIG</b> and turn <b>COLOR</b> for <b>Reso Decay</b>: how long it rings, from 20 ms at 0 to 10 seconds at 127 (half a second at 64), the same on every pitch.</li>
          <li>Hold <b>RETRIG</b> and turn <b>SHAPE</b> for <b>Reso Brightness</b>: at 0 dull, the overtones die fast and the pitch rings on; at 127 every overtone rings as long as the pitch, bright and metallic.</li>
          <li>All four are parameters like any other: hold a trig as well to lock them on that step (a pitch per step plays a melody), hold <b>LFO</b> as well to make them the LFO's destination (it reads PTCH, AMT, DEC or BRT), hold <b>TRACK</b> as well to set them on all six tracks, or send CC 74 (Pitch) and CC 71 (Amount).</li>
          <li>Save the kit or the project: each sound keeps its Track FX and its settings.</li>
        </ol>
        <dl class="facts">
          <div><dt>Sound</dt><dd>the pitch is the knob's: it does not follow the notes you play. Noise comes out about as loud as it goes in; a single hit rings quieter the longer it rings. A dull or high pitch rings shorter than Decay asks. At Amount 0 the sound passes untouched. Values glide in, as any parameter does on the Model:Cycles.</dd></div>
          <div><dt>Other mods</dt><dd>goes with SAMPLE, the effects, the Samples filter, Crush and Control All Config. A sound has one Track FX at a time. On a firmware without Reso, the official one too, a sound plays without it and keeps everything else.</dd></div>
          <div><dt>Tested</dt><dd>checked in an emulator on the OS's own code, bit for bit against its own code built for a computer. Not played on a Model:Cycles yet.</dd></div>
        </dl>
      </section>
```

**The release** (`docs/assets/release.js`, a new entry or the merge's):

```js
    { en: "New card in Track FX, Reso: a tuned resonator on any track, so that hats, noise and hits ring at a pitch. RETRIG + SWEEP is Pitch, the MIDI note (60 = C4), RETRIG + CONTOUR is Amount (0 off), RETRIG + COLOR is Decay (20 ms to 10 s), RETRIG + SHAPE is Brightness (dull to metallic). All four work on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71" },
    { en: "Reso is checked bit for bit in an emulator; experimental until played on a Model:Cycles" },
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
intacte, au bit près), RETRIG + COLOR Decay (20 ms à 10 s), RETRIG + SHAPE Brightness. La preuve est celle du filtre
Samples, avec Reso au bit près contre le build hôte de `reso.c` (la boucle en C, modèle de `reso_cf.S`).

    python3 tools/gen_reso.py --cycles model-cycles_OS1.13.syx [--check]
    python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines reso
    python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines smpfilter,crush,reso   # avec Samples et Crush

MAIN OS patché, `reso` seul : `0a4eba0e9076b59598d37aeb3af090d1e288aade6c330c52708278523f969373` ; avec Samples et
Crush : `b274ee03706d3e5211e5bcb3f2d7288b8d56c6ba506b41cdbde25782e4751547` ; avec toutes les cartes de la page :
`5a8d16a68a296a2240d6a5c0c412ed77199ec21926fdea68c3bff9fd3531c971` (sur `fltslot` 0.9, avant la fusion avec Ring et EQ).
```

**`tweaks/model-cycles_OS1.13/PROVENANCE.md`**:

```markdown
| `75-reso.json` | durchgemacht and Claude (model27) | Reso, a Track FX (notes/75): a tuned resonator, a comb with an allpass and a damping in its loop, model27's own code (`tools/machines/reso/reso.c`, its frame loop in `reso_cf.S`, its tables `reso_tab.h` written by `tools/gen_reso.py`), compiled by `tools/gen_reso.py` and composed alone by `tools/compose.py` with the parts `fltslot` (0.9) and `shortcuts`; no third-party code. On the device bit for bit the host build of `reso.c`, checked in the emulator by `tools/emu/test_fltslot.py`. Card in the flasher, experimental. |
```

**`notes/README.md`**:

```markdown
| [75-reso.md](75-reso.md) | **Reso: a tuned resonator in the Track FX (2026-11-01, English)**: the maintainer's decisions (a comb rather than a bank of modes; Pitch on SWEEP as the MIDI note, Amount on CONTOUR, 0 dry and the start, Decay on COLOR, Brightness on SHAPE); id 4, "RES"; the comb: a DC blocker, the line through a first-order allpass, a one-pole damping whose phase at the pitch is exact (q = sin P / sin(w0 + P)), the loss given back up to a gain of 1 − 2⁻¹² (its DC mode), the input scaled for noise; in tune within 0.2 cents (C1 to C7), Decay as asked when bright; the line cleared lazily, a silent track skipped; the frame loop in ColdFire assembly (MAC with load, 20 instructions a frame), its C model the proof's; cost counted by the proof 709 held, 1 083 gliding, 1 233 first, six tracks 6.8 % of a block (Samples 8.3 %); sanitizers and 3 000 blocks bit for bit in the interpreter; **`test_fltslot.py` ALL OK in the maintainer's run (2026-11-01)**; not played on the machine yet. |
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
