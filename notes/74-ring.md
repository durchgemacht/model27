# 74 — Ring: a ring modulator in the Track FX

The second effect of the Track FX ([73](73-track-fx-crush.md)), from the maintainer's list of insert effects
(notes/73 §1) and built as §16 laid out: in a session of its own, on the branch `trackfx-ring` cut from `trackfx`
(`df1b562`, `fltslot` 0.9), next to Reso (id 4) and EQ (id 5). Ring multiplies a track by a carrier: its note on
RETRIG + SWEEP, the mix on RETRIG + CONTOUR, its shape from sine to square on RETRIG + COLOR. The package `ring`
(`tools/machines/ring/`, id 3, "Ring", "RNG" on screen), the card's tweak `74-ring.json` (`tools/gen_ring.py`, order 74),
proof in emulation `tools/emu/test_fltslot.py` (unchanged: the manifest's `proof` section is the model and the cost
states). No OS address of its own: the filter slot calls it (notes/72, notes/73).

## In short

- **Freq** (k 28, RETRIG + SWEEP, CC 74): the carrier's frequency as a MIDI note, 0 (8.2 Hz) to 127 (12.5 kHz), 60
  middle C, one step a semitone (FUNC between them). A sound starts at 64 (E4, 330 Hz), the slot's neutral word.
- **Mix** (k 29, RETRIG + CONTOUR, CC 71): 0 dry, an amplitude modulation at the middle (the input at half with its
  sidebands), the ring alone at 127. 0 is the slot's neutral word: a new sound starts dry.
- **Wave** (k 30, RETRIG + COLOR, no CC; called Shape until 0.3, §14): the carrier a sine at 0 (its start word,
  declared), driven into a clip towards a square at 127. k 31 (SHAPE) is not read.
- **A note starts the carrier at its peak**, so every hit sounds the same and its attack comes through.
- **Off is dry**: at Mix 0 the track passes untouched, bit for bit; the carrier runs on underneath.
- **Exact integers**: the host build of `ring.c` is the proof's model, bit for bit; since 0.2 (§10) each frame's
  product runs on the EMAC on the device, the same bits as 0.1's split.
- **Cost** (0.2, §10), counted by the proof and declared: off 39, sine 727, shape 967, glide 948, silent 202, first
  734 instructions a track and block; six tracks at most 5 802 a block, 5.4 % (0.1: 7 410, 6.8 %; Samples' worst
  8 952, 8.3 %; Crush's 7 872, 7.3 %). The proof averages six tracks of which one is silent; six playing tracks with
  Shape count about 6 700, 6.2 % (§4, §10). The load not measured on the machine yet.
- **Played on the Model:Cycles** from the command line (2026-11-01, §9): « passt ». Experimental until flashed
  from the page.
- **Ring 0.2** (§10): the same output, bit for bit, in about three quarters of the instructions (each frame's product
  on the EMAC); the maintainer's run ALL OK, its counts declared; played on the Model:Cycles: « getestet, passt ».
- **Ring 0.3** (§13): another carrier, a cosine of 2 048 steps without interpolation (its noise about 60 dB under
  0.2's output, 51 dB at Shape 127; heard by the maintainer: « passt »), the frames in `ring_cf.S`, a loop of one
  frame: about a third fewer instructions (the interpreter: shape 1 119 → 733), and fewer cycles under every cache
  assumption of notes/27's model. The proof's run and the machine are to do.

## 1. Decisions (2026-11-01)

| Question | Decided | Consequence |
|---|---|---|
| The knobs | proposed Freq on SWEEP and Mix on CONTOUR, a carrier shape as an option; the maintainer: « Dazu SHAPE-Form » | three values: Freq, Mix, Shape |
| Shape on SHAPE or COLOR? | `compose.py` takes a Track FX's values without gaps from k 28 (`params` "in the order of k 28 to k 31"), so Shape on SHAPE would leave k 30 a value that does nothing, on RETRIG + COLOR and as an LFO destination in every build with Ring; the maintainer: « Ja, auf COLOR » | Shape on k 30 (RETRIG + COLOR), k 31 not declared |

Decided while building, within those (not asked separately):

- **Freq's law**: MIDI notes, `f = 440 · 2^((v − 69) / 12)`. The value reads as a note number in the `int` format
  (60 middle C); the top, 12.5 kHz, is still under half the rate. The bottom, 8.2 Hz, already chops (a tremolo whose
  sign flips); lower rates are the LFO's.
- **Mix's law**: the gain `1 − m + m · c`, so the knob goes dry → amplitude modulation → ring modulation; at 127 the
  input is gone (the ring is 3 dB quieter than the input on a sine).
- **The carrier's phase at a note**: 0 is its peak (a cosine), so the attack of a hit passes at any frequency; a sine's
  zero would swallow it at low frequencies (a quarter period: 31 ms at 8 Hz).
- **Shape's law**: the drive `D = 1 + 15 (v / 127)^2` (1 to 16). The harmonics come in over the first quarter of the
  knob and the edges sharpen over the rest (3rd harmonic −36.7 dB at 8, −13.1 at 32, −10.1 at 64, −9.6 at 127; the
  31st −74, −57, −60, −36 dB); the ring up to 2.9 dB louder at 127. A crossfade from sine to square was not taken: it
  brings every harmonic of the hard square in at once from the first step, only quieter, where the clip brings them in
  from the low ones up.
- **Names**: Ring Freq / FREQ, Ring Mix / MIX, Ring Shape / SHPE; all in the `int` format (0 .. 127).

## 2. The values

| Where | What | Words | Neutral / start |
|---|---|---|---|
| k 28 (RETRIG + SWEEP, CC 74) | Freq | 0..0x7f00, `n = w >> 8` a note, the low byte between two notes | 0x4000 (E4) |
| k 29 (RETRIG + CONTOUR, CC 71) | Mix | 0..0x7f00; `m = w · 128 / 127` in Q15, 0 .. 32768 | 0 (dry) |
| k 30 (RETRIG + COLOR) | Shape | 0..0x7f00; the drive `256 + (w² / 32512) · 3840 / 32512` in 8.8, 256 .. 4096 | 0x4000; Ring's start word 0 (sine) |
| k 31 | not read | | |

Words outside 0..0x7f00 (an LFO can push them there) are clamped.

## 3. The arithmetic

Exact integers, the same C compiled for the host as the proof's model (as Crush):

- **The carrier**: a 32-bit phase, 2^32 a period, adds `inc` each frame; `inc = RING_INC[n] + ((RING_INC[n + 1] −
  RING_INC[n]) >> 8) · (w & 0xff)`, `RING_INC[n] = round(2^32 · f(n) / 48000)` for n = 0..128 (the last only read as
  the step after 127). The carrier `c` from `RING_COS[i] = round(32767 cos(2π i / 256))`, i = 0..256: the phase's top
  8 bits the step, the next 8 between two, `c = a + (((b − a) · fr) >> 8)` (−32767 .. 32767). Both tables are written
  by `gen_ring.py` into `ring_tab.h`. Linear between two notes, the pitch is at most 0.7 cent off.
- **Shape**: at drive 256 (Shape below about 1, `w² / 32512 · 3840 / 32512` rounds to 0) the sine as is; above it
  `c = clip((c · D) >> 8, ±32767)` (`c · D` at most 2^27). Two loops, so that the sine pays nothing for it.
- **Mix**: the gain `g = (32768 − m) + ((m · c) >> 15)`, from −32767 to 32768 (−32768 cannot happen: at m = 32768
  it is c).
- **The product**: `y = ⌊x · g / 2^15⌋` split at 16 bits, `2 · ((x >> 16) · g) + (((x & 0xffff) · g) >> 15)`: each
  term and the sum within 32 bits for any frame and any g of that range, and `|y| ≤ |x|` but for the floor. Since
  0.2 the device computes it on the EMAC and the host as here (§10).
- **Off**: Mix 0: the block untouched; the phase moves on by 32 · inc, so that a Mix that opens in a note (a lock, the
  LFO) finds the carrier where it would have been.
- **The silent start of a block**: the frames before the first that is not 0 give 0 whatever the carrier; only the
  phase moves on across them. A silent block is a scan (about 7 instructions a frame) and the phase.
- **A note** (the trig bit): the phase again at 0, the carrier's peak, at the block's first frame. **reset(track)**: the
  same, so that a track coming to Ring starts there too.

## 4. Cost

Measured before the proof, in the ColdFire interpreter of notes/69 §20.1 (`_scratch/pots-load/cfemu.py`, outside the
repository), with a bench after `_scratch/crush-opt/bench.py` (`_scratch/ring-load/bench.py`): the device object
linked alone, against the host build of the same source over 1 500 blocks (a decaying tone with noise, a note every
40 blocks, silences, blocks silent but for their last frames, full scale, random words with every corner, resets):
**none differ**. Instructions a track and block (8 blocks of warm-up, the most of 8 more), the committed object:

| State | Words (k 28, k 29, k 30) | Instructions |
|---|---|---|
| off | 64, 0, 0 | 38 |
| sine | 64, 95, 0 (also Mix 127, Freq 0) | 1 142 |
| shape | 64, 95, 127 | 1 429 |
| glide | jumping every block, Shape never 0 | 1 407 |
| silent | no note | 264 |

So 36 instructions a frame on the sine, 45 with Shape, for a track that plays.

**The proof's counts against these** (§5): the proof counts the six tracks' sum in the dearest block and divides it by
six, and one of the six stock tracks is silent in its scenes, so each count is five playing tracks and one silent:
(5 · 1 142 + 264) / 6 = 996 (sine), (5 · 1 429 + 264) / 6 = 1 235 (shape), (5 · 1 407 + 264) / 6 = 1 217 (glide), to
the instruction; off and silent the same in both. Crush's counts are the same mix: (5 · 930 + 162) / 6 = 802 and
(5 · 1 387 + 162) / 6 = 1 183, its hard and soft states (notes/73 §12, where the gap was put down to a harder signal).
So the declared numbers, and the composer's load from them (`fl_cost`: six times the dearest state over 108 225
instructions a block), compare like for like between the Track FX, and all of them sit about a sixth under six
playing tracks: for Ring 7 410 declared, 6.8 %; six playing tracks with Shape 8 574, 7.9 %.

Tried and dropped (the same bits, more instructions with this GCC, 16.2): the loops by pointer (1 186), the loops in
functions of their own (1 190 / 1 512), unrolled by two (larger, and the interpreter does not know the `move` to the
CCR GCC then uses), the clip as one unsigned compare (1 523), the clip skipped by a threshold on the unshaped carrier
(1 376 at Shape 127 but no better near Shape 1, the worst case). Assembly would give about 29 a frame on the sine
(−13 %); the EMAC (a `mac.l` for the product) about 7 a frame less, at the price of an EMAC model in the host build.
Neither is needed under Samples' bound.

**The interpreter's `ext.l`**: `cfemu.py` ran `ext.l` as `ext.w` (a byte to a word), which this code has (the frame's
upper half, `swap` and `ext.l`): the device object differed from the host build in almost every block until a copy
with `ext.l` (and `extb.l`) was used, `_scratch/ring-load/cfemu.py`. The counts do not change with it. Earlier benches
compared two device objects in the same interpreter (Crush's ref and opt), where such a fault cancels out; the
original file is left as it was.

## 5. The proof

`test_fltslot.py` takes Ring from its manifest (notes/73 §16): the host build as the model (`HostModel`: `ring.c`
compiled with `-O2 -std=c99 -fwrapv`), a selection `ring` of its own, a place in the full table (`smpfilter`, `crush`,
`ring`, then REFF and four copies: eight in one build) and its cost in `proof.cost_states` (off, sine, shape, glide,
silent; "first" the block in which the tracks come to it from none).

- `--dry` **ALL OK** (2026-11-01): the sites, the 15 writes, the data block (Ring with three values: descriptors 1 to 3;
  in the full table OFF, SMP, CRU, RNG, R51 .. R54, REF), the start words (Ring's `0x4000 0x0000 0x0000 0x4000`), the
  refusals (nine filters). Unicorn stops with SIGILL in this sandbox.
- **The host build under the sanitizers** (`-fsanitize=undefined,address`, without `-fwrapv`, so that any signed
  overflow is reported; `_scratch/ring-load/ubsan.c`): every corner of k 28, k 29 and k 30 (−32768, −1, 0, 1, 0xff,
  0x100, 0x101, 0x3eff, 0x3fff, 0x4000, 0x4001, 0x40ff, 0x7e00, 0x7eff, 0x7f00, 0x7f01, 0x7fff), against eight kinds
  of blocks (silent, ±full scale, alternating, random, silent but the last frame, silent first frames), notes,
  resets, track 6, then 2 million random blocks: **no fault, 2 039 304 blocks**. Mix 0 and track 6 leave the block
  untouched; `|y| ≤ |x| + 1`; 0 in gives 0 out. The carrier on a constant input at Mix 127: 8.18, 55, 261.6, 329.6,
  440, 2 093, 8 372 and 12 544 Hz measured for notes 0, 33, 60, 64, 69, 96, 120 and 127 (zero crossings in one
  second, within half a hertz), the first frame of a note at the peak; Mix 64 a gain from −0.008 to 1; a Mix that
  opens after eight blocks off gives the same frames as one open throughout; silent first frames leave the carrier
  as played ones.
- **The full run, the maintainer's** (Unicorn in a normal terminal), from this worktree:

  ```sh
  "../.venv-emu/bin/python" tools/emu/test_fltslot.py --cycles ../model27/firmware/model-cycles_OS1.13.syx
  ```

  **The maintainer's run (2026-11-01): ALL OK but Ring's cost line, by design** (its manifest declared no counts
  yet). Ring bit for bit its host build in every scene, alone and in the full table of eight (OFF, SMP, CRU, RNG,
  R51 .. R54, REF): the sounds choosing it, the changes of Track FX and of sound, an id the build lacks, the hot
  tracks; MACSR and the accumulators; the registers and the stack. The boot's rows for descriptors 1 to 3 (k 28..30 on
  the six machines, CC 74 and 71, NRPN 1:20 and 1:21, a new sound's k 30 at 0x4000), the knob lookup (RETRIG + SWEEP /
  CONTOUR / COLOR → descriptors 1..3), the names ("Ring Freq"), the type's formatter (RNG) and steps, the start words
  on a step (none → RNG: Shape 0, Freq and Mix kept; CRU → RNG: 0x4000 0x0000 0x0000), the p-locks of k 28..31, a
  machine change, the record (k 30 stored relative to its neutral word: 0x2a00 → 0x6a00), the load. Ring's own cost,
  instructions per track and block: **off 38, sine 996, shape 1 235, glide 1 217, silent 264, first 1 003**, now
  declared in its manifest (`tests.emulation.date` 2026-11-01); the composer's load for six tracks 7 410, 6.8 % of a
  block. The other selections as before (Samples' and Crush's costs as declared).

## 6. The other checks (2026-11-01)

- `gen_ring.py --cycles … --check`: the tables, the object (1 884 bytes of code and tables, 24 of variables) and
  `74-ring.json` (15 writes, 274 conflicts) up to date.
- `check_overlaps.py`, `claims.py --check --self-test`: ALL OK (294 tweaks).
- `webcompose_check.sh`: composer.js places `ring.o` as `relocate.py` does (23 of 23 placements); with the official
  file the composed selections identical (they do not hold Ring yet, §11).
- `gen_flasher_tweaks.py --check` up to date (no card yet); `py_compile` of the generator.
- `registry.py --check` reports `REGISTRY.md` out of date, as expected: it gains Ring's payload row and Ring among
  the targets of the slot's hooks, and is generated again at the merge (notes/73 §16.2), as the other composed
  tweaks' conflicts (Ring among them) are.

## 7. Known

- **Values glide in** after a switch, as with Crush (notes/73 §11): from CRU (Bits at 127, k 29 0x7f00) to RNG the
  Mix glides from 127 to 0 in about 70 ms, so a note playing through the switch hears a short ring that fades.
- **From none** the slot writes only the start words that differ from the neutral ones (notes/73 §11): Shape 0, but
  Freq and Mix as the sound holds them. Within a build a sound only reaches none through the first Track FX and back,
  so it holds Ring's own last values or the neutral ones, unless a value was turned on OFF (RETRIG + CONTOUR there
  names the build's first Track FX's value). A sound saved in another build with a Track FX this one lacks counts
  as none and keeps its k 29: stepped to Ring, it may start with Mix up (Crush's Bits 127 gives Mix 127).
- **RETRIG + COLOR on other tracks**: in a build with Samples or Crush, their tracks and OFF show Ring Shape on
  RETRIG + COLOR (a value is named after the first Track FX that has it, notes/72) and turning it changes nothing
  there; it is an LFO destination in every build with Ring.
- **The measuring build** (`--diag-filters`): Ring's Freq is in the `int` format, so its popup shows the value; the
  average load reads in Samples' Cutoff or Crush's Rate popup on another track, the peak in the type's popup.
- **Shape aliases** at high Freq (the clipped carrier's harmonics above 24 kHz fold back); towards the square the ring is
  up to 2.9 dB louder.
- **No note name**: Freq shows the note's number; a formatter of its own could show C4, E4 … later (three characters).

## 8. For the machine

Builds in `build/ring-0.1/` of this worktree (git-ignored), made by `compose.py` from the official file and read back
by its own checks (sections, checksums, signature); not checked by elektron-firmware-tool (not installed here):

| Build | MAIN OS |
|---|---|
| Ring alone | `a32b09d0a422cf56f455816aac51ea8b517bdae2936a1d440c1426e57c2f09b7` |
| Samples + Crush + Ring | `ce50adf3c62ae3ef5fff2b3705437f4a2f9345116b3739b537e3f71f7b9a877f` |
| every card + Ring, as the page would compose it | `9647a93b90412c4b8bf84f6ee91fd3c9dc65b9661ebf3ef4784fb582211e1ac4` |
| the same, measuring (`measure/`, `--diag-filters`) | `106b4f4a403f00eabaa7acf7be506843203dbf44c3550fbcc1118cf51e0d5017` |

What to try: RETRIG + PITCH to RNG (with Samples and Crush: OFF, SMP, CRU, RNG), the sound unchanged until Mix turns;
Mix up to 127 on a drum and on a held note; Freq across the range (low: a chop; middle: bells; high: metallic); every
hit the same (the carrier from its peak), even at low Freq; RETRIG + COLOR from sine to square; a lock on a held trig,
LFO + RETRIG + SWEEP (FREQ), TRACK + RETRIG + CONTOUR (Control All), CC 74 / 71; CRU ↔ RNG and SMP ↔ RNG while it
plays (Ring starts dry, §7's short glide); save and reload; in the measuring build six tracks on Ring at Shape 127:
the type's popup shows the peak.

## 9. Tested on the machine (2026-11-01)

The maintainer, after the builds of `build/ring-0.1/` and the list of §8 (from the command line): « passt ». The load
the measuring build showed was not reported. Experimental on the page until flashed from it, as Samples and Crush were
(notes/72 §20, §23; notes/73 §10, §15).

## 10. The same bits, fewer instructions: Ring 0.2 (2026-11-01)

The maintainer: « prüfen welche performance optimierungen möglich sind », then « Ja, übernehmen ».

- **Measured outside the proof**, as Crush 0.3 (notes/73 §12): the device objects in the ColdFire interpreter, now the
  Reso session's copy (`_scratch/reso-bench/cfemu.py`: its indexed displacements read in hex, as objdump prints them,
  `btst`, MAC with load, the accumulator's moves in fractional mode, and the `ext.l` of §4; Ring's 0.1 object uses
  displacements of 0, 2 and 4 only, so its counts of §4 stand), against the host build of the same source.
- **Kept** (`ring.c` 0.2), three changes, the output 0.1's bit for bit:
  - **The product on the EMAC**: `mac.l` x, g << 16 and `movclr.l` from a clear acc0 give ⌊x · g · 2^16 / 2^31⌋, the
    product truncated (MACSR 0xa0: signed, fractional, saturating, truncating), as `tools/emu/emac.py` executes it,
    which is 0.1's ⌊x · g / 2^15⌋ for every g of −32767 .. 32767 (g ≤ 32767 whenever Mix is on: at c = 32767,
    ⌊m · 32767 / 2^15⌋ = m − 1). Two instructions a frame where the split took ten. On the host the split stays (the
    proof's model, `#ifdef __mcoldfire__`). Ring sets MACSR to 0xa0 and clears acc0 at each block's start, as the slot
    calls it (two instructions a block; POTS does the same), so it does not depend on what ran before.
  - **The gain's shift is a mask**: ⌊m · c / 2^15⌋ · 2^16 is 2m · c with its low 16 bits cleared, so g << 16 =
    (32768 − m) · 2^16 + (2m · c & 0xffff0000): a multiply, an `and.l` and an add where a multiply, a shift by 15,
    an add and a `swap` / `clr.w` were. 2m is kept even (2 · ⌊128 w / 127⌋) so that the first term has no low half;
    `w · 256 / 127` gave other bits in 466 of 1 500 blocks (odd values carry half an LSB of g).
  - **The silent start scanned by pointer**: four instructions a frame where the index and its compare with 32 took
    seven.
- **Checked**: the 0.2 object in the interpreter against its host build, 1 500 blocks: none differ; the host builds
  of 0.2 and 0.1 against each other, 300 000 blocks (every corner of the words, full scale, random and partly silent
  blocks, notes, resets): none differ; the host build under the sanitizers as in §5: no fault; `gen_ring.py --check`,
  `test_fltslot.py --dry` ALL OK, `check_overlaps.py`, `claims.py`, `webcompose_check.sh` with and without the
  official file. `emac.py` knows each form the object uses (`mac.l %a1,%d0,%acc0`, `movclr.l`, `move.l #0,%acc0`,
  `move.l #160,%macsr`).
- **Instructions a playing track and block**, the interpreter, 0.1 → 0.2: off 38 → 39, sine 1 142 → 831 (−27 %),
  shape 1 429 → 1 119 (−22 %), glide 1 407 → 1 097 (−22 %), silent 264 → 202 (−23 %); 1 914 bytes of code and
  tables (1 884). In the proof's average (five playing tracks and a silent one, §4) about sine 726, shape 966, glide
  948: six tracks about 5 800 a block, 5.4 % (6.8 %); six playing tracks with Shape 6 714, 6.2 % (7.9 %).
- **Dropped** (estimated, not built): MAC with load for the next frame (one instruction a frame, but a pipelined
  loop and the last frame apart, or a read past the block); the loops in assembly (two or three a frame); a larger
  cosine without interpolation (five a frame, but phase noise at −56 to −62 dB, another sound); the clip through the
  EMAC's saturation (only with a change of mode in each frame).
- **The proof, the maintainer's run (2026-11-01): ALL OK but Ring's cost line, by design** (0.1's counts still
  declared): Ring 0.2 bit for bit its host build in every scene, alone and eight in one build, with the EMAC as
  `emac.py` executes it; MACSR and the accumulators after the part as the stock OS's. Counted for 0.2, now declared:
  **off 39, sine 727, shape 967, glide 948, silent 202, first 734** (0.1: 38, 996, 1 235, 1 217, 264, 1 003), as
  predicted from the interpreter (five playing tracks and a silent one, §4); the composer's load for six tracks 5 802,
  5.4 % of a block (6.8 %).
- MAIN OS: Ring alone `3cdd61c0…`, with Samples and Crush `b5a8c7e9…`, every card `6960abd2…`, measuring `61128e62…`.
  Builds in `build/ring-0.2/` (git-ignored), made and read back by `compose.py`. **For the machine**: Ring must sound
  as 0.1 (§8's list, with Shape and Mix at their ends, on six tracks at once); new is only that the EMAC computes the
  product on the device.
- **Tested on the machine (2026-11-01)**: the maintainer, after the builds of `build/ring-0.2/` (from the command
  line): « getestet, passt ». The load the measuring build showed was not reported.

## 11. For the integration

What the merge adds outside this package (the files of notes/73 §16.2), ready to paste.

**`tools/gen_flasher_tweaks.py`**, `FEATURES`, after Crush (and `"ring"` in `OFFERED` after `"crush"`):

```python
    {
        "id": "ring",
        "cat": "sound",
        "label": "Ring (Track FX)",
        "desc": "A ring modulator on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound Ring; "
                "RETRIG + SWEEP is Freq (the carrier's note, 0 to 127), RETRIG + CONTOUR is Mix (0 dry, 127 the ring "
                "alone), RETRIG + COLOR is Shape (sine to square), with p-locks, LFO and CC 74 / 71.",
        # model27's own (notes/74): a Track FX through the filter slot (fltslot 0.9); bit for bit the host build of
        # the same source in emulation; on the Model:Cycles from the command line on 2026-11-01 (notes/74 §9)
        "status": "experimental",
        "credit": {"kind": "by", "who": "durchgemacht", "repo": "durchgemacht/model27"},   # model27's own: the card links the project
        # a Track FX composed in the page from its package (notes/74), with the machines, effects and the other Track
        # FX ticked: alone it gives 74-ring.json byte for byte, whose conflicts give its excludes
        "package": "ring",
    },
```

**`docs/flasher/app.js`**: `GUIDE_OF` `ring: "ring",`; `FEAT`:

```js
  ring: { label: "Ring",
    short: "A ring modulator on any track: the carrier's note, the mix, and its shape from sine to square.",
    desc: "Hold RETRIG and turn PITCH to give the track's sound Ring (RNG). Then hold RETRIG and turn CONTOUR for Mix: 0 is dry, in the middle the sound stays at half with bell-like tones around it, at 127 only the ring is left. RETRIG + SWEEP sets the carrier's note, Freq: 0 is 8 Hz, a fast chop; 60 is middle C; 127 is 12.5 kHz, metallic. RETRIG + COLOR sets Shape: 0 is a sine, turning right drives it towards a square, harsher and a little louder. Each time you switch to Ring it starts with Mix at 0 and Shape at 0, so nothing changes until you turn.\n\nAll three are real parameters of every machine: lock them on a trig, make them the LFO's destination (hold LFO and RETRIG and turn the knob), set them on all tracks with TRACK, or send CC 74 (Freq) and 71 (Mix). Each sound keeps its own settings, saved with it. Every note starts the carrier again from its peak, so every hit sounds the same. Ring comes after Volume + Dist.",
    note: "A sound saved on this firmware loses Ring on another firmware, nothing else." },
```

**`docs/guide/index.html`**: a section after Crush (`<li><a href="#ring">Ring</a></li>` in the contents; the
sections after it renumbered), and in the Samples and Crush sections' steps and facts "Samples, Crush or Ring":

```html
      <section id="ring">
        <h2><span class="n">8</span>Ring</h2>
        <p class="by">model27's own · MIT license</p>
        <p class="lede">A ring modulator on any track, after Volume + Dist: the track multiplied by a carrier, from a chop to bells to metal. It is a Track FX: each sound chooses one, or none.</p>
        <ol>
          <li>Hold <b>RETRIG</b> and turn <b>PITCH</b> to the right: every four detents the track's sound steps to the next Track FX: OFF, then <b>SMP</b> and <b>CRU</b> if the <a href="#samples-filter">Samples filter</a> and <a href="#crush">Crush</a> are ticked too, then <b>RNG</b>. To the left it steps back. Ring starts with Mix at 0 and Shape at 0, so nothing changes until you turn.</li>
          <li>Hold <b>RETRIG</b> and turn <b>CONTOUR</b> for <b>Ring Mix</b>: at 0 off. Turning right brings in the ring: in the middle the sound stays at half, with new tones above and below it; at 127 only those are left, the sound itself is gone.</li>
          <li>Hold <b>RETRIG</b> and turn <b>SWEEP</b> for <b>Ring Freq</b>, the carrier's note: 0 is 8 Hz, a fast chop; 60 is middle C (262 Hz); 127 is 12.5 kHz. Each step is a semitone; hold <b>FUNC</b> as well to go between them. Low notes chop and wobble, middle ones ring like bells, high ones sound metallic.</li>
          <li>Hold <b>RETRIG</b> and turn <b>COLOR</b> for <b>Ring Shape</b>: at 0 the carrier is a sine, turning right drives it towards a square: harsher, brighter, a little louder.</li>
          <li>All three are parameters like any other: hold a trig as well to lock them on that step, hold <b>LFO</b> as well to make them the LFO's destination (it reads FREQ, MIX or SHPE), hold <b>TRACK</b> as well to set them on all six tracks, or send CC 74 (Freq) and CC 71 (Mix).</li>
          <li>Save the kit or the project: each sound keeps its Track FX and its settings.</li>
        </ol>
        <dl class="facts">
          <div><dt>Sound</dt><dd>every note starts the carrier again from its peak, so every hit sounds the same and its attack comes through. At Mix 0 the sound passes untouched. With Shape up, high notes alias. Values glide in, as any parameter does on the Model:Cycles, so right after a switch you may hear them settle for a moment.</dd></div>
          <div><dt>Other mods</dt><dd>goes with SAMPLE, the effects, the Samples filter, Crush and Control All Config. A sound has one Track FX at a time. With Ring installed, RETRIG + COLOR reads Ring Shape on every track, but works only on Ring. On a firmware without Ring, the official one too, a sound plays without it and keeps everything else.</dd></div>
          <div><dt>Tested</dt><dd>checked in an emulator on the OS's own code, bit for bit against its own code built for a computer. Played on a Model:Cycles (2026-11-01) from the command line.</dd></div>
        </dl>
      </section>
```

**`docs/assets/release.js`**, the release that brings it:

```js
    { en: "New card in Track FX, Ring: a ring modulator on any track. RETRIG + CONTOUR is Mix: 0 dry, the ring alone at 127. RETRIG + SWEEP is Freq, the carrier's note from 8 Hz to 12.5 kHz; RETRIG + COLOR is Shape, from sine to square. Every note starts the carrier again, so every hit sounds the same. All three work on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71" },
    { en: "Ring is checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01); experimental here until flashed from this page" },
```

**`README.md`**, after Crush's sentence: « The ninth, **Ring**, model27's own third Track FX, multiplies a track by a
carrier: its note, the mix and its shape on three knobs. »

**`BUILD.md`**, after « Crush (Track FX) » (in French, as the file):

~~~markdown
### Ring (Track FX)

`tweaks/model-cycles_OS1.13/74-ring.json` est produit par `tools/gen_ring.py`, qui écrit les tables de la porteuse
(`tools/machines/ring/ring_tab.h` : le pas de phase par note, le cosinus), compile `tools/machines/ring/ring.c` et le
compose seul avec `tools/compose.py` : le deuxième effet (id 3) des Track FX ([note 74](notes/74-ring.md)). RETRIG +
SWEEP est Freq (la note de la porteuse, de 8,2 Hz à 12,5 kHz), RETRIG + CONTOUR est Mix (0 sec, 127 l'anneau seul),
RETRIG + COLOR est Shape (du sinus au carré ; un son qui passe à Ring part du sinus, sa valeur de départ), les
descripteurs 1 à 3. La preuve est celle des Track FX, avec Ring au bit près contre le build hôte du même fichier et
une sélection de huit dans un build :
```sh
python3 tools/gen_ring.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_fltslot.py --cycles model-cycles_OS1.13.syx
python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines ring
python3 tools/compose.py --cycles model-cycles_OS1.13.syx --machines smpfilter,crush,ring   # avec Samples et Crush
```
MAIN OS patché, `ring` seul : `3cdd61c01181408642e1ed3b58458bf98ffcb2d0d30986a48e692c7b4ed2ec4d` ; avec Samples et
Crush : `b5a8c7e99016f066e6f469e9f7c1cbc217e6344a02e90dca65066eca7a4d52a9` ; avec toutes les cartes de la page :
`6960abd2a932360ca61df9cc785208681a2ed261a0a04312ff4fdb902c1971f1` (Ring 0.2, le produit sur l'EMAC, `fltslot` 0.9, joués sur un Model:Cycles depuis la ligne de commande le
01/11/2026 ; à recalculer à la fusion avec Reso et EQ ; avec Ring 0.1, le même son, joués sur un Model:Cycles depuis la ligne de
commande le 01/11/2026 : `a32b09d0…`, `ce50adf3…`, `9647a93b…`).
~~~

**`tweaks/model-cycles_OS1.13/PROVENANCE.md`**, after `73-crush.json`:

| `74-ring.json` | durchgemacht and Claude (model27) | Ring, a Track FX effect (notes/74): a ring modulator, model27's own code (`tools/machines/ring/ring.c`, its tables `ring_tab.h` written by `tools/gen_ring.py`), compiled by `tools/gen_ring.py` and composed alone by `tools/compose.py` with the parts `fltslot` (0.9) and `shortcuts`; no third-party code. On the device bit for bit the host build of the same source, checked in the emulator by `tools/emu/test_fltslot.py`. Card in the flasher, experimental. |

**`notes/README.md`**, after 73:

| [74-ring.md](74-ring.md) | **Ring: a ring modulator in the Track FX (2026-11-01, English)**: id 3, "RNG"; Freq on RETRIG + SWEEP (the carrier's note, MIDI 0 .. 127, 8.2 Hz to 12.5 kHz), Mix on RETRIG + CONTOUR (0 dry, amplitude modulation at the middle, the ring alone at 127), Shape on RETRIG + COLOR (a sine driven into a clip towards a square, start word 0; on COLOR because the values have no gaps from k 28); a note starts the carrier at its peak; off is dry bit for bit; exact integers (a cosine table of 256 steps, the product split at 16 bits), the host build the proof's model; since 0.2 each frame's product on the EMAC (the same bits, about three quarters of the instructions); the cost measured first in the ColdFire interpreter (`cfemu.py`'s `ext.l` fixed in a copy), the host build under the sanitizers over the words' corners; the proof's states from the manifest, ALL OK in the maintainer's run, the cost declared (0.2: at most 967 a track and block, six tracks 5.4 %; the proof's counts average five playing tracks and a silent one, Crush's too); known: the values' glide after a switch, from none, RETRIG + COLOR named Ring Shape on other tracks |

**`AGENTS.md`**, the map, after `tools/machines/crush/`:

```
tools/machines/ring/          Ring (notes/74): a ring modulator, the Track FX's second effect (id 3): Freq, Mix and the
                              carrier's Shape on RETRIG + SWEEP / CONTOUR / COLOR; tools/gen_ring.py writes its tables
                              and builds it into 74-ring.json; proven by test_fltslot.py from its manifest
```

and in « Adding a feature for users », the last note and the reserved ones as the merge leaves them.

**Generated at the merge**: `REGISTRY.md` (`registry.py`), the other composed tweaks' conflicts (their generators;
Ring among them), `tweaks.js`, `REF_MAINOS` / `REF_MODS` (`ref_mainos.py`: Ring alone and its pairs), and the
checks' lists: `webflash_smoke.js` (the cards' order, the packages, `KIND` `ring: "filter"`, the credits),
`webcompose_synth.py` (selections with Ring: alone, with Samples and Crush, every card).

## 12. Merged, tested from the page (2026-11-01)

Merged into `main` with Reso and EQ (notes/73 §17, release 0.28): the maintainer's proof on the merge ALL OK, the build of
every card played on the Model:Cycles, then a build flashed from the page: « getestet, passt » (notes/73 §18, release
0.29). The card is tested.

## 13. Another carrier, a third fewer instructions: Ring 0.3 (2026-11-03)

The maintainer: « track Fx: prüfen: wesentliche performance optimierungen möglich wenn der fokus nicht darauf liegt das
am ende alle bytegleich rauskommt, sondern wirklich darauf die cpu last zu reduzieren » (a change of sound allowed);
after a listening page, « passt », then « Tc übernehmen ».

### 13.1 Measured outside the repository

A prototype with one switch per idea (`_scratch/ring-opt/`, its `REPORT.md`) against 0.2, in the ColdFire interpreter of
notes/69 §20.1 (`_scratch/cfemu/cfemu.py`): each device object against its own host build (none differ, 1 500 blocks
each), the manifest's cost states, a sweep of Shape at Freq 0, 64 and 127 and of Freq at five Shapes (the dearest block
is the manifest's `shape` state in every build: the cost states cover it), and the host builds against 0.2 on a mix
(kick, hat, bass, chord) in twelve scenes. Instructions a track and block on the interpreter (its own signal, so compare
shares, not counts):

| | sine | shape (the dearest) | silent | sound against 0.2 |
|---|---:|---:|---:|---|
| 0.2 | 831 | 1 119 | 202 | |
| E: 0.2's arithmetic in assembly, four frames a turn, MAC with load | 648 | 880 (−21 %) | 144 | bit for bit |
| E1p: the same, a loop of one frame | 729 | 961 (−14 %) | 144 | bit for bit |
| T: a cosine of 2 048 steps, not interpolated, four frames a turn | 424 | 656 (−41 %) | 144 | 61 dB under it, 51 at Shape 127 |
| **Tc: the same, a loop of one frame (kept)** | 505 | 737 (−34 %) | 144 | as T |
| O: the carrier from a rotation on the EMAC (cos and sin in Q31) | 573 | 891 (−20 %) | 154 | 55 dB (its 0.2 % lower level) |
| OQ: O with Shape as a blend towards a square | 574 | 744 (−34 %) | 154 | 12 to 19 dB: another sound |

- **The code's size counts.** The proof and `compose.fl_cost` count instructions, which is the load with every cache
  warm. With the model of notes/27 §2 (1.54 cycles an instruction, 15 a 16-byte line read from SDRAM, calibrated there
  on the machine) and the lines each call reads, the dearest of six states (sine and shape at Freq 0, 64, 127), in
  cycles a track and block:

  | | warm | cold once a block | cold at every call |
  |---|---:|---:|---:|
  | 0.2 | 1 723 | 1 821 | 2 527 |
  | E | 1 355 (−21 %) | 1 610 (−12 %) | 2 885 (+14 %) |
  | E1p | 1 480 (−14 %) | 1 645 (−10 %) | 2 470 (−2 %) |
  | T | 1 010 (−41 %) | 1 248 (−31 %) | 2 435 (−4 %) |
  | **Tc** | 1 135 (−34 %) | 1 302 (−29 %) | 2 140 (−15 %) |

  Four frames a turn doubles the code's lines (49 to 67 against 28 to 31); when the voices evict Ring between its
  calls (heavy machines on the other tracks, notes/27 §2), that costs more than the instructions it saves. The loops of
  one frame win under every assumption. Which column holds on the machine, only the measuring build says (§13.4).
- **Tc's table** is 4 KB against 0.2's 514 bytes and touches more data lines a block at middle frequencies (35 against 11
  at Freq 64); the model above counts them.
- **Its sound**: each step's value at its middle, the phase's top 11 bits: the steps' phase noise lies about 61 dB under
  0.2's output on a sine, 51 dB at Shape 127, where the clip steepens the edges. The effect's strength (the output
  against the dry input) is 0.2's to 0.1 dB in every scene. The maintainer heard both on a listening page (a private page
  whose browser computes 0.2 and Tc, bit for bit as their host builds, with a track of their difference at +40 dB): a
  sine tone, E4, Mix 127, Shape 0, « passt ».
- **Dropped**: O (no cheaper than E, its rotation set again every block), OQ (another sound, dearer than Tc), 1 024
  steps (the same cost, 6 dB more noise), the loops of four frames (§above).
- **The interpreter's `movem`**: a register range from the d into the a registers (`%d2-%a0`, as objdump prints it)
  gave an empty list; fixed in `_scratch/cfemu/cfemu.py`, its self-test identical before and after.

### 13.2 `ring.c` 0.3, `ring_cf.S`

- **The carrier**: `RING_COS[2048]`, 32 767 cos(2π (i + ½) / 2 048), read at `ph >> 21` (`tools/gen_ring.py`); a note
  still starts it at its peak (the first step's value, 32 767).
- **The frames in `ring_cf.S`** on the device, a loop of one frame with the block's values in registers (loaded with one
  `movem.l` from a static `struct run`, so that GCC keeps no frame pointer): the carrier, Shape's clip, the gain
  k16 + (2 Mix c with its low half cleared) and the product on the EMAC, as 0.2. 13 instructions a frame on the sine,
  20 with the clip. `frames()` in `ring.c` is its model on the host, the proof's.
- **The whole block** runs once a frame is not 0 (a frame of 0 gives 0 at any gain); a block is silent when its first
  frame and the or of the others are 0. The phase is stored once a block, before the test for Mix 0: the same values
  as 0.2's three stores.
- **Shape 0** no longer divides for the drive.
- Code and tables 5 454 bytes (0.2: 1 914), variables 52 (24); 11 492 bytes added to the image (7 952).

### 13.3 Proven, checked

- The repository's host build against the prototype's Tc over 30 000 blocks (random words with every corner, notes,
  resets, silences, partly silent blocks, full scale, a lone sample anywhere): none differ. The device object in the
  interpreter against its host build, 1 500 blocks: none differ. The host build under UBSan and ASan, 400 000 blocks:
  no fault. The bench's 0.2 counts as §10's (sine 831, shape 1 119, glide 1 097, silent 202).
- Interpreter counts, 0.2 → 0.3: off 39 → 42, sine 831 → 501 (−40 %), shape 1 119 → 733 (−34 %), glide
  1 097 → 732, silent 202 → 143, first 831 → 501. In the proof's average (five playing tracks and a silent one, §4),
  about sine 440 and shape 635.
- **Green:** `gen_ring.py --check` and the other four Track FX generators, `gen_parts.py --check`,
  `check_overlaps.py`, `registry.py --check` and `gen_flasher_tweaks.py --check` (after regenerating them),
  `claims.py --check --self-test`, `webbuild_check.sh`, `webcompose_check.sh` with the official file (identical),
  `webflash_check.sh`, `webmanager_check.sh`, `ref_mainos.py --check` (after regenerating: only the combinations with
  Ring change), `py_compile`, and `test_fltslot.py --dry` ALL OK.
- **The proof**, the maintainer's run (2026-11-03, Unicorn, on the tree of this section): everything OK but Ring's
  cost line, as expected with 0.2's numbers still declared. Counted: off 42, sine 442, shape 635, glide 634, silent
  143, first 449 (0.2 declared 39, 727, 967, 948, 202, 734: sine −39 %, shape −34 %). These are now Ring's
  `cost.emulation` (tests dated 2026-11-03); the filters' load of a build with Ring as its dearest Track FX falls from
  6 × 967 = 5 802 to 6 × 635 = 3 810 instructions a block (5.4 % → 3.5 %). After declaring them: `gen_ring.py
  --check` and the other four, `gen_flasher_tweaks.py --check` (`tweaks.js` regenerated, it carries the cost),
  `check_overlaps.py`, `registry.py --check`, `claims.py --check --self-test`, the four web checks, `py_compile` and
  `test_fltslot.py --dry` ALL OK again; the MAIN OS does not change (the cost is only reported).

MAIN OS, on `0c24e8e` (the CPU page, release 0.37, notes/78; POTS 0.2 and RESAMPLE, releases 0.38 and 0.39, notes/69
§24 and notes/79; Ring's release 0.36 below 0.37, the stamp 2026-11-04-03) with the name of §14: Ring alone
`a6340129…`, with Samples and Crush `4a1554a4…`, with the CPU page `df80d34a…` (0.2's: `333bae39…`), all three as on
`ea102e2` and `22704dc`; every card of the page, thirteen with the CPU page and RESAMPLE, `021d39d1…` (0.2's:
`289e6c14…`). All match `REF_MAINOS` (92 combinations, only those with Ring changed) or `webcompose_check.sh`; every
check of §13.3 green again on this tree (with `gen_cpu.py`, `gen_resample.py`, `gen_pots.py`, `gen_digidelay.py` and
`gen_parts.py --check`), and `webflash_smoke.sh` with both official files ALL PARTS OK. `BUILD.md`'s Track FX sections
carry the thirteen cards' hash. Builds in `build/ring-0.3-main/` (git-ignored): Ring alone, with Samples and Crush,
`ring-cpu/` and `ring02-cpu/` (Ring 0.3 and 0.2, each with the CPU page alone, to compare the load on the page's
TRACK FX line; 0.2 composed from `main` as it is), and `every-card/`. The earlier builds of `build/ring-0.3/` and
`build/ring-0.3-cpu/` are superseded (their every card lacks cards of the page; their `ring-cpu/` builds are the same).

### 13.4 On the machine

The maintainer tried Ring 0.3 on their Model:Cycles (2026-11-04), from the builds of §13.3, and asked for it on
main: « habe auf gerät getestet. kannst du in main packen ». The CPU page's numbers (0.3 against 0.2 on six tracks)
were not reported. The card stays `tested`; the release text says it was tried on the machine.

## 14. Shape becomes Wave (2026-11-03)

The maintainer: « "Ring Shape" liegt auf dem "Color" knob. das ist etwas unglücklich weil direkt daneben ist der knob
"Shape". würdest du eher unseren Regler umbenennen oder ihn einfach auf den anderen (shape) knob schieben? », then
« Ja, Ring Wave ».

- **Renamed, not moved.** The value stays k 30 on RETRIG + COLOR, so the sounds, p-locks and LFO destinations saved
  with Ring since release 0.28 keep it. Moving it to SHAPE would leave COLOR a value that does nothing, as §1 found
  (`compose.py` takes a Track FX's values in order from k 28), or need gaps in the filter slot, and would lose what is
  saved in k 30. COLOR holds the sound's colour on the stock machines, as on Reso (Tone, notes/75 §14).
- **The names**: Ring Wave / WAVE (were Ring Shape / SHPE): the manifest's `params`, the card (`FEAT` in `app.js` and
  `FEATURES` in `gen_flasher_tweaks.py`), the guide, `AGENTS.md`. The popup breaks it into « Ring » over « Wave ». The
  LFO's destination list reads WAVE. Nothing else changes: the cost states keep their keys (`shape` is the state with
  Wave at 127).
- In the firmware only the names' strings change (the filter slot's data 1 byte shorter); `74-ring.json`,
  `tweaks.js`, `REGISTRY.md` and `REF_MAINOS` regenerated (again only the combinations with Ring change); the checks of
  §13.3 again green, `test_fltslot.py --dry` ALL OK.
