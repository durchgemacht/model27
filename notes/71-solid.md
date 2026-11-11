# 71 — SOLID (MODAL until 2026-11-11): a machine of modes struck like wood, skin, metal or glass (plan and step 2, 2026-10-31, English)

The machine was Claude's proposal of 2026-10-24, when the maintainer asked what Claude would build. Its sound was settled
by ear in a float listening prototype over two rounds, then parked on 2026-10-24 ("FM can do all of that already"). On
2026-10-31 the maintainer took it up again: its quality can only be judged in the emulator or on the device. The
package: [`tools/machines/solid/`](../tools/machines/solid/), its generator [`tools/gen_solid.py`](../tools/gen_solid.py),
its proof [`tools/emu/test_solid.py`](../tools/emu/test_solid.py) (passes, §8); no tweak, no card. Addresses:
VAs of OS 1.13. Called MODAL until 2026-11-11, then **SOLID**, on the machine and in the package, its files and its
symbols (§10).

## 1. In short

- **What it is.** Eight modes, each a rotating phasor in fixed point on the EMAC, struck by a mallet, a noise burst or
  sustained noise. Body (SHAPE) glides through string, membrane, marimba, bar, bell and glass; Bright (COLOR) bends
  the material's own levels and decays; Pickup (SWEEP) is the point the body is heard at; Exciter (CONTOUR) goes from
  a soft mallet to sustained noise; DECAY is the body's T60, 20 ms to 8 s. On the popup each name reads on two lines
  under "Solid", as the stock machines' do (§10).
- **The plan**, six steps: (1) the fixed point, checked against the prototype on the host; (2) the package after REF
  and REF2 (`APPLYING.md` §12 of the Cycles Mod Standard), without a shortcut, not offered; (3) a proof in Unicorn and
  the load with six tracks, which decides 8 or 16 modes; (4) digiemu; (5) the device, next to PERC, METAL and TONE;
  (6) only then Pitch drop on RETRIG + SWEEP, the card and the guide.
- **Done 2026-10-31:** steps 1 and 2 (§4, §5). Every check without emulation OK, `--compare-ld` identical alone and
  with SAMPLE.
- **2026-11-11:** the package brought onto `main` again (it had waited in a stash), still composed identically;
  step 3 done (§8): the proof passes on the OS's own code, the core exact everywhere. Two fixes (§3): GATE damped the
  body for one block only, and PUNCH did nothing; SOLID 6 dB louder (§6).
- **2026-11-11, optimized (§9):** a ringing voice about 64 % fewer instructions in the core, the same bits; the VCA
  and, without PUNCH, PUNCH no longer called. The proof's third run: ALL OK; one ringing voice 3 588 instructions a
  block (9 915 before), under TONE's 5 291; six tracks of sustained noise 1.63 × six TONE (2.7 × before).
- **Open:** step 4, digiemu (§7).

## 2. The sound, as settled with the maintainer

From the listening rounds (the prototype stays outside the repository):

| Round | What the maintainer decided |
|---|---|
| 1 (2026-10-24) | 8 or 16 modes; a string from modes, no Karplus-Strong; toms, rolls, bells, the position under an LFO and the CONTOUR ride good; wood and the held glass not |
| 2 (2026-10-24) | the materials now all different (each its own signature); SHAPE gliding, no plateaus; a new strike on another note or material damps the ringing body by 12 dB ("teilweise"); the pitch drop on glass and bell does not disturb; the held glass now too dull and whistling |
| 3 (2026-10-31) | the fixed point (§4); the held glass's slope offered at −1.0, −0.75 and −0.5, answer open |

The knobs (names since §10): Bright `BRIT` (COLOR, 64 = the material as it is, an exponent 2^((64 − COLOR) / 40) on
its levels and relative decays), Body `BODY` (SHAPE: 0 string, 25 membrane, 51 marimba, 76 bar, 102 bell, 127 glass,
interpolated in the log domain), Pickup `PICK` (SWEEP: the pickup p = 0.5 − 0.48 SWEEP / 127, a mode's weight
0.95 |sin(π k p)| + 0.05), Exciter `EXCT` (CONTOUR: 0–63 a mallet whose contact lasts 0.35 to 0.03 of a period, its fundamental struck at
the same level on every note, a click growing with hardness; 64–95 a hard mallet fading under a noise burst of 3 to
150 ms; 96–127 the 150 ms burst fading into sustained noise that feeds mode k by ratio^−0.75). The velocity shifts the
mallet's hardness by ±20 on CONTOUR around 0.75 and scales the drop by velocity²; the level is the OS's.

## 3. The OS side `[FAIT]`

**The amp envelope** (`0x400a9252`, read 2026-10-31): the level at `+0x230` is negative, `0x80000000` full scale.

| Stage (`+0x23c`) | What happens |
|---|---|
| attack (0) | in the block of `+0x38` the level is set from `+0x248`; `0x80000000` means full at once |
| hold (2) | with GATE (`+0x24c`) until the note ends (`+0x244`, set from `+0x3c`) |
| decay (1) | `level = −level × factor` (`msac.l` in fractional mode), factor at `+0x250` |

The decay table `0x4011d84c` holds negative factors: DECAY 0 `0xffffffff` (silence in a block), 64 `0x8036b311`, 127
`0x800a0f01` (15 s to −60 dB, One-Shot TECHNICAL §5). SOLID writes `0x80000001` every block: × (1 − 2^−31) a block, the
envelope stays open. The body has its own decay and its own GATE (damped to 0.12 s once the note ends), and DECAY means
the body's T60; DECAY's factor on top would shorten every note (at DECAY 64 by about 13 %).

**The VCA** (`0x400a9430`): in a trig's block (`+0x34`) it clears the level, so the ringing body would fall to 0 for
0.67 ms and come back at full level in the next block, a click on every retrig of a ringing body. Its product is
`−sample × level`, identity at full level. Until the optimization of 2026-11-11 SOLID hid `+0x34` from it in that
block; since then it does not call the VCA at all (§9).

**The flags of a voice** (the voice loop `0x400a7d4a`, read 2026-11-11): for every track and block it writes `+0x34`
from the trig mask and `+0x3c` from the release mask (`0x400a7da2`, `0x400a7da8`), so both hold for one block; after
the track's update and render it copies `+0x34` into `+0x38` (`0x400a7e24`). In the block of `+0x38` it takes the
machine from the parameters and, if it changed, resets the voice (`0x400a7ab8`, `+0x2c` cleared: SOLID's mark) and
sets `+0x38` again (`0x400a7dd2`..`0x400a7dde`). Update and render run at every block, whatever the envelope; then the
loop halves the track's 32 frames (`0x400a7e2a`, `asr.l #1`). So SOLID strikes in the block after the trig, and the
note's end is an event: SOLID keeps it in `ended[t]`, set by `+0x3c` outside a trig's block, cleared by the strike and
by a change of machine, and the core's GATE reads that. Until 2026-11-11 solid_update read `+0x3c` itself, and GATE
damped the body for that one block only (0.67 ms) instead of to 0.12 s until the next strike, as the prototype did.

**The velocity** is the OS's gain of the block, `0x40fe4c90 + 2 t` (0..127), applied after the voice loop and copied
from `0x40fe4cd0` in the block after the trig (notes/54), the block SOLID strikes in. SOLID reads it there, for the
sound only.

**PUNCH** (`0x400a967a`, and TONE's setup at `0x400aa8d8`, read 2026-11-11): in the block of `+0x38` TONE sets
PUNCH's words by its PUNCH key (`p+0x1e`): off, `+0x29c` `0x7fffffff`, `+0x2a0` and `+0x2a4` `0x20000000`, `+0x48` 0;
on, `+0x29c` `0x20000000`, `+0x2a0` `0x60000000`, `+0x2a4` `0x20000000`, `+0x48` 1. Off, PUNCH multiplies the block by
4 × `+0x2a0` × `+0x2a4` = 1/4; then the voice loop halves it: a TONE track's output is its voice's × 1/8.
Until 2026-11-11 SOLID always set the off values, so its PUNCH key did nothing; now it sets TONE's for both, except
the output stage `+0x2a4`, `0x40000000` instead of `0x20000000` (the maintainer's +6 dB, §6): a SOLID track's output
is the core's (Q31) × 1/4.

**The EMAC.** The stock chain and the stock machines accumulate into `acc0` without clearing it (the VCA's `msac.l`,
notes/23 §2); the voice loop runs in fractional saturating mode (`MACSR 0xa0`, as `sdvintage.c` states). `solid_render`
saves `MACSR`, sets `0xa0`, leaves `acc0` empty after every product (`movclr.l`) and gives `MACSR` back, as SAMPLE's
filter does.

## 4. The fixed point, checked on the host (step 1)

`solid.c` is POTS's arrangement (notes/69 §12): one file, the EMAC on the device, on the host (`SOLID_HOST`) the same
arithmetic as `tools/emu/emac.py`. Formats: the modes and the output Q27 (1.0 = 2^27, full scale on the bus),
coefficients Q31, logarithms log2 in Q24, knobs 8.8. Per block and mode: the frequency from the note and the material's
log ratio (`ex2`, 256 steps), r = exp(−d) from the T60 (a series where d < 1/16, so that 1 − r is exact for an 8 s
decay), cos and sin from a 257-point quarter table with one Newton step to unit length, the output weight normalized
over the modes. Per frame and mode: two `mac.l`, a `msac.l`, two `movclr.l` for the rotation, one product for the
output.

Measured against the prototype (its rounds' clips, the clicks made an impulse on both sides so that only the
arithmetic differs):

| Clip | Error |
|---|---|
| six materials, SHAPE ride, marimba (two damping rules), wood, bells | −51 to −69 dB |
| the bells before the 256-step `ex2` (64 steps: 0.026 cent flat) | −34 dB; with an exact `exp2` −50 dB, so pitch only |
| an ensemble without noise (p-locks, drop, velocities), the prototype's damping rule | −62.5 dB, −70.3 dB without drop |

Two things a voice cannot do as the prototype did:

- **The burst's level.** The prototype measured each burst's spectrum at the first six harmonics before playing it.
  The voice takes the expected spectrum of its noise instead (`G_BURST`, by note). Over eight seeds the bursts' levels
  agree within 1 dB on average; a snare in the ensemble varies a little more from hit to hit (1.8 against 1.0 dB).
- **The held glass**, now ratio^−0.75: 1.8 % of the energy above 2.5 f0 (round 1 20.7 %, round 2 0.13 %; −1.0 gives
  0.76 %, −0.5 4.35 %).

One rule changed on purpose: a strike on another note or material damps the body first only **while it rings**; after
silence SOLID strikes at once instead of 3.3 ms later. In the ensemble above this is the only difference to the
prototype, which always waited: with its rule the package gives −62.5 dB, with its own the strikes after silence come
3.3 ms earlier. The GATE's sustained exciter fades out when the note ends (`+0x3c`), not after a
length read at the strike.

## 5. The package (step 2)

| File | What |
|---|---|
| `solid.c` | the core and the machine: `solid_update` (the knobs, the strike from `+0x38`, the envelope held open) and `solid_render` (the core, Q27 to Q31 saturated, the amp envelope, the VCA without the trig's cut, PUNCH) |
| `solid_tables.h` | generated: material ratios (the prototype's, 16 per material), signatures, sine, `exp2`, `log2`, the burst's and the mallet's gains |
| `manifest.json` | order 71 (the next free; the maintainer's to confirm), the picture of PERC (3), four knobs, DECAY 80 by default, no claims, no shortcut |
| `solid.o` | `ld -r` of the source, written and checked by `tools/gen_solid.py` |

`relocate.py`: 36 sections, 129 relocations, all `R_68K_32`, nothing undefined. Code 12 218 bytes (with 4.2 KB of
tables), variables 2 592 bytes (six voices, the exciter's three buffers of 32 frames, shared because the voice loop
renders one track after the other). Alone: 116 writes, 17 800 bytes added to the image. With the note's end kept
and PUNCH (§3, 2026-11-11): code 12 240 bytes, variables 2 616 bytes. `compose.py --compare-ld`
identical alone, as `sampler,solid` (machine 7, descriptors 81–85) and as `solid,sampler`. `claims.py --check
--self-test`, `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`: OK, unchanged (SOLID has no
tweak in `tweaks/`).

## 6. The load

The inner loop compiles to about 16 instructions per mode and frame: about 4 000 instructions a block for 8 modes,
plus the coefficients, against about 7 600 for a stock voice (notes/23 §1). 16 modes double the loop. A silent voice
returns at once. Cycles on the device are more than instructions (`movclr.l` waits for the EMAC).

Counted in Unicorn (the maintainer's run of `test_solid.py --quick --modes 8,16`, 2026-11-11, before the PUNCH fix,
which only adds a test in the strike's block): instructions a block of one voice, the whole voice loop less the same
loop muted, note 60 and default knobs unless named.

| Voice | 8 modes | 16 modes |
|---|---|---|
| marimba, mallet (default) | 9 915 (strike's block 13 370) | 10 924 (14 957) |
| string, note 36 | 9 918 (13 899) | 17 889 (22 430) |
| glass, note 60 | 9 915 (13 373) | 17 875 (21 912) |
| glass, note 96 | 6 939 (9 598) | 6 944 (10 179) |
| noise burst (CONTOUR 80) | 11 187 (14 172) | 12 196 (15 757) |
| sustained noise (CONTOUR 120) | 14 331 (16 865) | 15 594 (18 703) |
| silent | 201 | 201 |
| six tracks ringing (sustained) | 85 989 | 93 559 |

Stock, same count: TONE 5 291, PERC 6 079, METAL 6 431, KICK 7 429, SNARE 7 158, CHORD 8 300; six TONE 31 746. A SOLID
voice is about 1.3 × KICK and 1.9 × TONE; six ringing 2.7 × six TONE (16 modes 2.9 ×, but 1.8 × on the materials
whose modes all stay below 0.45 fs). Stack 292 bytes below the voice loop. What this is on the device in per cent of a
block only the CPU page can say (step 5). These are the counts before the optimization; after it, §9.

**The level** (same run, peak / RMS of the track's output over the first 100 ms, dB of full scale): TONE −18.1 /
−24.1, PERC −15.1 / −27.0, METAL −14.7 / −32.3; SOLID (default) −24.3 / −34.7, string −23.9 / −32.6, membrane −19.6 /
−36.1, bar −24.0 / −33.6, bell −20.0 / −31.6, glass −23.3 / −31.5, burst −25.3 / −36.2, sustained −28.8 / −39.3. With
the same chain as TONE (× 1/8), SOLID is about 6 dB lower in peak and 10 dB in RMS: the core's `GAIN` 0.4 (§4). The
maintainer's choice (2026-11-11): +6 dB, up to TONE's peak, in PUNCH's output stage (`+0x2a4` × 2, §3), not in the
core, where the membrane's strike already reaches −1.5 dB of the bus and would clip. After it (the second run): SOLID
(default) −18.3 / −28.7, string −17.8 / −26.5, membrane −13.6 / −30.1, bar −18.0 / −27.6, bell −14.0 / −25.6, glass
−17.3 / −25.4, burst −19.3 / −30.2, sustained −22.8 / −33.3; the cost unchanged.

## 7. Left to do

- **Step 3, `tools/emu/test_solid.py`:** done 2026-11-11, all OK (§8); its runs are the maintainer's (Unicorn does
  not run in the agent's sandbox). Settled: the smoother does not glide a p-locked SHAPE (§8). Measured: the level and
  the load (§6). Decided (the maintainer, 2026-11-11): 8 modes, +6 dB.
- Not in step 3: whether the governor of the Syntakt engines (`GOV_SKIP`, test_acid_combos.py) behaves with an
  envelope that stays open; it exists only in builds with those engines.
- **Step 4:** digiemu (the maintainer). **Step 5:** the device. **Step 6:** Pitch drop on RETRIG + SWEEP (k 30, the
  core reads it already, 0 for now), the card, the guide.
- The maintainer's: the held glass's slope, order 71, the picture, the defaults (the names: decided, §10).

## 8. The proof (step 3, 2026-11-11, passes)

[`tools/emu/test_solid.py`](../tools/emu/test_solid.py) runs the machine as `compose.py` builds it, alone (machine 6)
and next to SAMPLE (machine 7), in the voice loop of `mcengine.py` and under the OS's sequencer (`seqrig.py`). Its
reference is the core compiled for the host, [`tools/emu/solid_ref.c`](../tools/emu/solid_ref.c) (`solid.c` with
`SOLID_HOST`, from silence, a block skipped when nothing rings and nothing is struck, as `solid_render` does). The
knobs it feeds that core are computed in the proof from the voice, the parameters and the velocity gain, as §3 says
`solid_update` must take them, not read from the machine.

| Part | What it checks |
|---|---|
| start-up, registrar | test_compose.py's checks for any composed machine |
| the core | at every block, the words `solid_render` hands `AMP_ENV` equal the host's core (Q27 to Q31, saturated), bit for bit: materials and glides, notes 0..127, the knobs at their ends, the exciters, DECAY, GATE, velocities, retrigs (same note, another note or material while ringing, after silence), knobs moving every block; render called at every block, the strike in the block after each trig, a silent voice not rendered |
| the chain | the track's output is the core's through the amp chain, halved by the voice loop, within 2^12 (−114 dB); the envelope's level stays full over 600 blocks; the VCA never sees a trig; PUNCH acts; GATE damps the body (−45 dB or lower 180 blocks after the note's end, 300 with sustained noise) and without GATE the note's end changes nothing |
| the tracks | SOLID → TONE → SOLID: a fresh voice; six SOLID tracks, each exact and as alone; SOLID among stock machines, these as on the stock OS; stock machines alone, identical to the stock OS without one instruction of SOLID; next to SAMPLE as alone |
| the sequencer | each step's velocity reaches its strike; SHAPE p-locked: what the strike sees, and whether it moves afterwards (printed) |
| measured | level (peak and RMS, first 100 ms) next to TONE, PERC, METAL; instructions a block of one voice, of six, the stack; with `--modes 8,16` the 16-mode build (the toolchain, `SOLID_MODES=16`), exact on 16 cases, and its cost |

`--dry` builds and lays out the firmwares and runs the host core without Unicorn (2026-11-11: machine 6 at
`0x43000000`, 12 240 bytes; next to SAMPLE machine 7 at `0x43009680`; 16 modes: variables 3 768 bytes).

    python3 tools/emu/test_solid.py --cycles firmware/model-cycles_OS1.13.syx --modes 8,16

**The first run** (the maintainer, 2026-11-11, `--quick --modes 8,16`): start-up and the registrar OK, alone and next
to SAMPLE; the core exact at every block in every case, 8 and 16 modes (no block differed from the host's); GATE OK
(−63.4 dB 180 blocks after the note's end, held −0.6 dB; sustained noise −56.7 dB, without GATE identical); SOLID
among the stock machines, the stock machines alone, next to SAMPLE OK; the sequencer's velocities reach their strikes.
The failures were the proof's, and one of SOLID's:

- the chain: the proof took PUNCH off as identity; it is × 1/4 (§3), the outputs differed by exactly 3/8 of the core;
  the proof now reads PUNCH's words from the voice;
- PUNCH did nothing on SOLID (§3), fixed; and SOLID 6 dB louder (§6);
- four trigs in a row from block 1: the trig in block 2 is lost, since the change of machine resets the voice in that
  block, `+0x34` with it (§3), as for any machine; the case now starts its row later;
- SHAPE p-locked (the sequencer): every strike saw exactly its step's value, which arrives in the trig's block and
  holds until the next one: no glide. The proof had counted that next value as a move.

**The second run** (the maintainer, 2026-11-11, all cases, 8 modes, after the PUNCH fix and +6 dB): ALL OK. The core
exact in 84 cases (20 092 blocks); a voice with nothing ringing not rendered (694 blocks); the track's output the
core's through the chain within 65 LSB (−150 dB of full scale), the VCA never seeing a trig; the envelope full over
600 blocks; a retrig on the ringing bell +1.3 dB against the block before, no cut; PUNCH acts (peak −12.1 dB, without
−18.0 dB); GATE as in the first run; SOLID → TONE → SOLID a fresh voice; six SOLID tracks each exact and as alone;
among and without the stock machines, and next to SAMPLE, the stock machines identical to the stock OS; the
sequencer's velocities and SHAPE p-locks as in the first run (every strike sees its step's value, held until the next
trig: no glide).

## 9. Optimized (2026-11-11, the maintainer's choice of stages 1 to 3)

Measured in a ColdFire interpreter that runs in the agent's sandbox (`_scratch/cfemu`, the device object alone, its own
signal: shares only, the declared numbers come from the proof). Instructions a block of the core, before → after:
ringing marimba 8 687 → 3 158 (−64 %), a strike every 40 blocks 8 814 → 3 811 (−57 %), sustained noise 13 070 →
8 167 (−38 %), knobs moving at every block 8 682 → 6 378 (−27 %), the strike's block 10 717 → 9 993. In every case the
same bits as before, and the device object the same bits as the host core (`solid_ref.c`).

| Stage | What | Where |
|---|---|---|
| 1 | the coefficients only when one of their inputs moved (the note, SHAPE, COLOR, DECAY, SWEEP, GATE's end, the sustained exciter; every block while choking or with a drop) | `solid_block`, `struct voice` `c_*` |
| 1 | the drop's factor a block with the coefficients (it only depends on DECAY) | `c_dropf` |
| 1 | a loop for each set of inputs (mallet or burst, sustained noise, both, none), the exciter's buffers cleared only when used | `ring()`, `exciter_block` |
| 2 | the ringing modes two at a time in assembly, four accumulators, the eight products of the rotations before the first read: 21 instructions a frame for two modes (C: 26); the same sums as C, each output product read on its own | `ring_cf.S` `solid_ring2` (host: two `ring()`) |
| 3 | no VCA (at full level it only multiplies by 1); without PUNCH no PUNCH either: its 1/2 done by SOLID (the core clamped to ±1.0, × 8: half the bus), about 700 instructions a block less in the stock chain; with PUNCH as before, without the VCA | `solid_render` |

Stage 3 changes the output by the truncations of the VCA and PUNCH it no longer runs (one or two LSB of the bus). On
the device stage 2 should gain more than the counts say: with four accumulators the EMAC waits less (not measured).
Not done: two modes a pass in C (GCC spills, −3 %), leaving out modes gone silent (little gain in a pattern),
assembly for the inputs' loops (sustained noise), coefficients only for the knob that moved (an LFO on PICK or DECAY).
Code 13 216 bytes, variables 2 832 bytes.

**The third run** (the maintainer, 2026-11-11, `test_solid.py`, all cases, 8 modes, the optimized build): ALL OK. The
core exact in 84 cases (20 092 blocks), a voice with nothing ringing not rendered (694 blocks); without PUNCH the
track's output is SOLID's halved by the voice loop exactly (0 LSB; 65 before stage 3) and the VCA is never called; the
envelope full over 600 blocks, the retrig on the ringing bell +1.3 dB, PUNCH acts (−12.1 dB, without −18.0 dB), GATE
as before (mallet −63.4 dB, sustained noise −56.7 dB); the tracks, next to SAMPLE and the sequencer as in the second
run. The level unchanged (§6, after +6 dB). Counted, instructions a block of one voice as in §6:

| Voice, 8 modes | Before (second run) | After | |
|---|---|---|---|
| marimba, mallet (default) | 9 915 (strike's block 13 375) | 3 588 (11 969) | −64 % |
| string, note 36 | 9 918 | 3 590 (12 496) | −64 % |
| glass, note 60 | 9 915 | 3 591 (11 972) | −64 % |
| glass, note 96 | 6 939 | 2 582 (8 498) | −63 % |
| noise burst (CONTOUR 80) | 11 187 | 6 354 (12 767) | −43 % |
| sustained noise (CONTOUR 120) | 14 331 | 8 598 (15 312) | −40 % |
| silent | 201 | 201 | |
| six tracks ringing (sustained) | 85 989 | 51 589 | −40 % |

A ringing voice is now 0.68 × TONE (5 291) and 0.48 × KICK (7 429); with sustained noise 1.6 × TONE; six tracks of
sustained noise 1.63 × six TONE (31 746; 2.7 × before). The interpreter's estimate of the ringing voice was about
3 700 (above). The strike's block gains least (−10 %, 13 375 → 11 969; why was not looked at). Stack 320 bytes below
the voice loop (292 before). On the device: the CPU page (step 5).

## 10. The names on the popup (2026-11-11)

In digiemu (0.1c) the popup cut "Brightness": ten characters on one line, the box shows about seven ("Material", eight,
filled it to its edges). The popup breaks a long name into two lines at a space (notes/76 §14), and every stock
machine names its knobs that way, machine first: "Snare Contour" / `CONT`, "Chord Shape" / `SHPE` (descriptors 46 to
74 of OS 1.13). The maintainer chose four words of seven characters at most, under the machine's name on the first
line.

The machine's name: **SOLID** instead of MODAL (the maintainer: it is only inspired by modal synthesis, and should
raise no false hopes). Modal is also a synth maker's name. Five letters, in capitals as SAMPLE (the stock names are
Kick, Snare, Metal, Perc, Tone, Chord), and "Solid" on the popup's first line.

| Knob | Long name | Short | Until 0.1c |
|---|---|---|---|
| COLOR | Solid Bright | `BRIT` | Brightness / `BRIT` |
| SHAPE | Solid Body | `BODY` | Material / `MATR` |
| SWEEP | Solid Pickup | `PICK` | Position / `POS` |
| CONTOUR | Solid Exciter | `EXCT` | Exciter / `EXCT` |

Only the manifest's strings change (15 bytes more in the registrar's data); the code, the sound and the cost are
those of §9. Proven by `tools/emu/test_compose.py --machines solid --machines sampler,solid`, the maintainer's run
of 2026-11-11: ALL OK, descriptors 76 to 79 (81 to 84 next to SAMPLE) named Solid Bright, Solid Body, Solid Pickup,
Solid Exciter, SOLID on the MACHINES page, the runtime equal to B1 input for input. Its voice loop played every added
machine but judged only REF, REF2 and SAMPLE; on SOLID it read the velocity's gain at 0x40fe4c90, above the memory it
maps, and stopped. It now leaves out the machines it has nothing to judge by, and says so: this machine's proof is
`test_solid.py`, which maps that memory and sets the gain.

Then, the same day, the inside renamed too: the package `tools/machines/solid/` (id `solid`, `solid.c`,
`solid_tables.h`, `solid.o`), `tools/gen_solid.py`, `tools/emu/test_solid.py`, `tools/emu/solid_ref.c`, this note,
and the symbols (`solid_update`, `solid_render`, `solid_block`, `solid_ring2`, `SOLID_MODES`, `SOLID_HOST`). The
proofs' runs above ran with the old names (the id `modal`); the float prototype keeps its name, outside the
repository.
