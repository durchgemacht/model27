# 73 — Track FX: effects in the filter slot, and Crush, the first

The maintainer's request of 2026-11-01, after a list of insert effects that could sit next to the filters: « 1. ein slot
für beide 2. auf 4 anheben 3. Track FX — bau als ersten Crush ». So the filter slot of [72](72-track-filters.md) holds
effects too, a build may hold four of them, the section and the type are called Track FX, and the first effect is
Crush, a sample-rate and bit reduction on two knobs (decided the same day: Rate and Bits on their own knobs). The part
`fltslot` 0.7 (`tools/machines/fltslot/`), the package `crush` (`tools/machines/crush/`, id 2, "Crush"), the card's tweak
`73-crush.json` (`tools/gen_crush.py`), proof in emulation `tools/emu/test_fltslot.py`. Addresses: VAs of OS 1.13.

## In short

- **Track FX is the filter slot**, with the same audio point, record, knobs and type (notes/72 §2 to §5). A sound picks
  one Track FX (a filter or an effect) with RETRIG + PITCH; its values are on RETRIG + SWEEP / CONTOUR / COLOR / SHAPE.
  What changes: a build holds four, the type's row reads "Track FX", the flasher's section is called Track FX.
- **Crush** (id 2, "CRU" on screen): RETRIG + SWEEP is **Rate**, the sample rate: 0 (the centre) off, to the right
  a hard hold (aliasing, metallic), to the left a softer one (the held samples joined by lines); RETRIG + CONTOUR is
  **Bits**: 127 off, fewer to the left, 0 = one bit (since Crush 0.2, §11; 0 off in 0.1). Both at once, both real
  parameters (p-locks, LFO, velocity, Control All, CC 74 / 71).
- **Start values** (`fltslot` 0.8, §11): each Track FX declares the words its values start at; a step to it from none
  gives those that differ from the neutral words, a step from another Track FX all of them, so Crush starts with Bits
  off at 127 and Samples behaves as before.
- **Off is dry**: with Rate at 0 and Bits at 127 the track passes untouched, bit for bit, and a sound that steps to
  Crush starts there, so it sounds the same until a knob turns, as with Samples.
- **Cost**, counted by the proof (§9): 883 instructions a track and block for the hard hold with Bits, 1 638 for the
  soft one, 1 670 gliding: six tracks at most 10 020 a block, 9.3 % (Samples' worst 8 952, 8.3 %), under the 10 %
  warning; at 0 / 0 30. Not measured on the machine yet.

## 1. Decisions (2026-11-01)

| Question | Decided | Consequence |
|---|---|---|
| A filter and an effect on one track at once? | No: one slot for both | no second stage; every value is already taken (notes/72 §1) and the sound has no saved place left (the key map's reading of 2026-10-31) |
| How many in a build? | four | the part's table grows by one entry (§2); the load does not depend on it: each track runs one, and `fl_cost` counts six tracks on the dearest |
| What is it called? | Track FX | the type's row on the device and the flasher's section; the values keep each effect's own names |
| Crush's knobs | two: Rate on SWEEP, Bits on CONTOUR | both at once, each with its CC; SWEEP's centre is Rate's off, as Cutoff's is Samples' |

## 2. `fltslot` 0.7

- **Four in a build.** The table's entries are "none" and then the build's filters by id: `ENTRIES` 4 held three, so
  5 now, and the part's `most` 4. The data block grows by one entry of 64 bytes, 740 to 804: `e[5]` moves `rows` 280 →
  344, `cur` 560 → 624, `acc` 630, `last_time` 632, `old` 636, `neutral` 764, `rec_next` 772, `diag` 784, `sum` 788,
  `peak` 792, `n` 796, `avg_t` 798, `peak_t` 800. `entries.S` reads `rec_next` at fixed offsets (`fl_data+708`, `+712`,
  `+716` → `+772`, `+776`, `+780`); `part.json`'s `data` gives the composers the rest (`compose.py` and `composer.js`
  read `entries`, the offsets and `most` from it).
- **The type's name.** Descriptor 5's long name "Filter Type" → "Track FX" (`part.json`'s `type.long`); its short name
  TYPE and "OFF" for none stay.
- Nothing else: the audio, the crossfade, the knobs, the record and the load as in 0.6.

## 3. Crush

### 3.1 The values

| Where | What | Words | Neutral |
|---|---|---|---|
| k 28 (RETRIG + SWEEP, CC 74) | Rate | 0..0x7f00, centre 0x4000 off; `a = |w − 0x4000|` in 8.8 (0 to 64): the rate falls to `1 / 2^(6a/64)` of 48 kHz, to 750 Hz on the left, 800 Hz on the right; right of the centre a hard hold, left a soft one | 0x4000 |
| k 29 (RETRIG + CONTOUR, CC 71) | Bits | 0..0x7f00; since 0.2 (§11) off at the top; since 0.4 (§13) `8 − 7 b / 127` bits with b = 127 − the word in 8.8: 126 about 7.9 bits, 64 about 4.5, 0 one bit (0.2/0.3: `16 − 15 b / 127`; 0.1: off at 0, b the word) | 0 (the slot's); Crush's start word 0x7f00 |
| k 30, k 31 | not read | | |

Formats: Rate `cutoff` (-64 .. 0 .. 63, as Samples' Cutoff), Bits `int` (0 .. 127). Short names RATE and BITS (the
LFO's destination shows them). Words outside 0..0x7f00 (an LFO can push them there) are clamped.

### 3.2 The arithmetic

Exact integers, the same C compiled for the host as the proof's model (as Samples' is):

- **Off**: Rate at the centre and Bits at the top (0 in 0.1): the block untouched; the hold remembers the block's last frame and starts its
  count afresh, so that turning Rate on later holds the latest sample.
- **Rate**: a 16.16 clock `ph` adds `inc` each frame, `inc = 65536 · 2^(−6a/64)` from a table of 65 steps
  (`INC[k]`, k = 0..64, written by the generator) with the word's low byte between two steps. When it passes 65536 it
  wraps and takes the frame (`prev = cur, cur = x`). Hard: `y = cur`. Soft: `y` runs on a line from `prev` to `cur`
  across the hold, `t = min(ph + inc, 65536)`: `y = 2 · (p + ⌊d · t / 65536⌋)` with `p = prev >> 1`,
  `d = (cur >> 1) − p`, split into `(d >> 16) · t + ((d & 0xffff) · t >> 16)` so that nothing leaves 32 bits. At a step
  of one frame (`inc` 65536) both are the input itself; the soft side lags by one hold, at most 1.3 ms.
- **Bits**: with b = 127 − the word (since 0.2), the exponent `e = 16 + 15 b / 127` in 8.8 (16.0 to 31.0); `q(x, s)` rounds half of x to the nearest
  multiple of `2^(s−1)` (mid-tread: small values to 0, no offset) and doubles it, saturating the top level: one bit is
  the three levels −FS, 0, +FS. Between two whole exponents the output blends the two roundings,
  `q(x, s) + ((q(x, s+1) − q(x, s)) >> 8) · frac`, so the knob moves without steps.
- **Order**: Rate, then Bits (the output is quantized).
- **A note** (the trig bit): the clock starts again so that the block's first frame is taken.
- **A silent block** (all 32 frames 0) with a silent hold: the output is 0 anyway; only the clock moves on,
  `ph = (ph + 32 · inc) mod 65536`.
- **reset(track)**: the hold to 0 and the clock marked (65536), so that the next block takes its first frame at once,
  as after a note (§7).

### 3.3 Cost

Estimated before the proof `[HYP]`: hard + Bits about 25 instructions a frame, soft + Bits about 40, so 800 to 1 300 a
track and block. Counted (§9): hard + Bits 883 (28 a frame), Bits alone 705 (22, the two roundings and the blend),
soft + Bits 1 638 (51): the soft line costs more than estimated (its split product, the clamp of t, the halves). The
manifest declares what was counted.

## 4. The proof

`test_fltslot.py` with:

- `Crush`, the host build of `crush.c` (ctypes) as the model; selections `crush`, and `smpfilter,crush,refflt,refflt2`
  (four in one build: the table, the type's steps through five entries, the audio of all four);
- the scenes as before (the hot one sweeps Rate across the centre with Bits at the top), the fourth scene giving the
  third and fourth filter to two tracks when the build has more than two;
- Crush's cost per state, against its manifest;
- the type's row "Track FX"; the refusals: five in one build (was three).

## 5. The flasher, the guide

- The fourth section's title Filters → Track FX; the card Crush (experimental) next to Samples; its excludes from
  `73-crush.json`'s conflicts.
- The guide's section 6 (Samples filter) becomes Track FX, with Samples and Crush.
- A release, README, BUILD.md, PROVENANCE.md, REGISTRY.md.

## 6. Steps

| Step | What | Done when |
|---|---|---|
| X1 | `fltslot` 0.7: four, "Track FX" | **done 2026-11-01 (§7)** |
| X2 | Crush: package, generator, card's tweak | **done 2026-11-01 (§7)** |
| X3 | The proof | **ALL OK** in the maintainer's run (§9) |
| X4 | Flasher, guide, release | **done 2026-11-01 (§7)**, every check green |
| X5 | The machine | **« passt », 2026-11-01: 0.1 (§10), 0.4 with `fltslot` 0.8 (§14), from the page (§15)** |

## 7. Built (2026-11-01)

- **`fltslot` 0.7**: as §2; the code the same size (3 264 bytes), only the offsets in its immediates moved; `gen_parts.py`
  rebuilt `fltslot.o` alone (the other parts byte for byte).
- **Crush 0.1** (`tools/machines/crush/`: `crush.c`, `crush_tab.h`, `crush.o`, `manifest.json`, MIT): 1 216 bytes of
  code and table, 72 bytes of variables. A host build with the undefined-behaviour sanitizer over the words' corners
  (outside 0..0x7f00 too), full-scale and silent blocks, resets and notes: no fault; off is the input bit for bit, one
  bit gives the three levels only, a whole bit count lands on its grid. Two corrections while testing: after a reset
  the clock takes the first frame at once (it held the reset's 0 for up to 60 frames, a gap after the crossfade into
  Crush), and a note sets the clock to 65535 rather than `65536 − inc`, so that the following frames are taken as early
  as the rate lets (at a step just under one frame, every frame but one in 4 096, not one in two).
- **`73-crush.json`** (`tools/gen_crush.py`, 15 writes, 273 conflicts); 27, 28, 29, 34, 36, 39, 70 and 72 regenerated
  (crush in their conflicts; 72 with `fltslot` 0.7). MAIN OS: Crush alone `25aac3ea…`, with Samples `c8cdc37c…`, every
  card `67f0d95e…`; Samples alone now `6f2a4db3…`, with SAMPLE `bef12e28…` (the part's offsets and the type's name).
- **The proof** (§4): `--dry` ALL OK, all nine selections (the table of four: OFF, SMP, CRU, R54, REF), five refused.
  Unicorn stops with SIGILL in this sandbox: the full run is the maintainer's (§9).
- **Flasher**: the section Track FX, the card Crush (experimental), its texts, guide section 7 (8 to 15 renumbered),
  release 0.26, stamp 2026-11-01-05; `REF_MAINOS` 37 combinations, `REF_MODS` 34; `webcompose_synth.py` with four
  Crush selections. Checks: generators, parts, registrar, claims, overlaps, registry, `ref_mainos`, webbuild,
  webflash, webcompose (identical), the smoke test with both official OS files ALL PARTS OK. `relocate_6ch.py --check`
  differs as before this work: this machine's assembler writes a PC-relative `lea` where the committed file has an
  absolute one (toolchain, not this change; the file left as committed).

## 8. For the machine

Builds in `build/crush-0.1/` (git-ignored), each checked by elektron-firmware-tool:

| Build | MAIN OS |
|---|---|
| Crush alone | `25aac3ea…` |
| Samples + Crush | `c8cdc37c…` |
| every card, as the page composes it | `67f0d95e…` |
| the same, measuring (`measure/`, `--diag-filters`) | `bbca505b…` |

What to try: RETRIG + PITCH (the popup Track FX: OFF, CRU; with Samples OFF, SMP, CRU); Rate both ways and Bits, both
at 0 the sound unchanged; a lock on a held trig, LFO + RETRIG + SWEEP (RATE), TRACK + RETRIG + SWEEP, CC 74 / 71;
switching SMP ↔ CRU while it plays; save and reload; Samples as before (its build changed with the part); in the
measuring build six tracks on Crush with Control All on Rate: Rate's popup the average, the type's the peak.

## 9. The proof, the maintainer's run (2026-11-01)

`test_fltslot.py`, all nine selections, 424 checks: **ALL OK but Crush's cost line, by design** (its manifest declared
nothing yet). Crush bit for bit its host build in every scene (alone and four in one build: OFF, SMP, CRU, R54, REF),
the crossfades, MACSR and the accumulators, the boot's tables, the knob lookup, LFO + a knob, the formatters, the type's
steps through five entries, the p-locks, a machine change, the record, the load, the refusals (five in a build). The
part with every track on none costs 263 instructions a block with one filter, 371 with four (the table's search; the
proof's bound 400). Crush counted, instructions per track and block: off 30, hard 883, soft 1 638, bits 705, glide
1 670, silent 163, first 1 661, now declared in its manifest (`tests.emulation.date` 2026-11-01); the composer's load
for six tracks 10 020, 9.3 % of a block. `tweaks.js` regenerated (the manifest it embeds); the MAIN OS unchanged; the
checks again green (claims, overlaps, registry, `ref_mainos`, webcompose identical, the smoke test ALL PARTS OK).

## 10. Tested on the machine (2026-11-01)

The maintainer, after the builds and the list of §8 (from the command line): « passt ». The load the measuring build
showed was not reported. Experimental on the page until flashed from it, as Samples was (notes/72 §20, §23).

## 11. Bits the other way, start values: `fltslot` 0.8, Crush 0.2 (2026-11-01)

The maintainer after the machine: « kannst du den bitrate regler umkehren? er startet mit max bit auf der rechten seite
(127) und wird nach links kleiner ». CONTOUR's neutral word is 0 for every filter (the slot's `values.defaults`, a new
sound's value and the record's XOR; Samples' Reso needs it), so Bits off at 127 needs a start value of its own. Decided:
start values per Track FX, no memory of the other Track FX' values (« egal, ohne gedächtnis. man wird sich daran
gewöhnen … ist doch bei den send fx auch so »); the OS's smoothing of the jump accepted.

- **`fltslot` 0.8**: `start[5][4]` at the data block's end (`+804`, 844 bytes; the other offsets unchanged), written
  by both composers from the manifests' `params[].start` (0 to 32512, else the neutral word; `compose.py` refuses
  another). `fl_step`, on a step to a filter: from none the start words that differ from the neutral ones, from a
  filter all of them; on a step to none nothing. Into the sound (`+76`) and into the targets of each track whose note
  plays that sound (`0x800015ae + 66 t + 56`). `[FAIT]` the OS's smoother `0x40058474` reads its input through the
  caller's pointer (`0x400597a6`), keeps its state at `0x800011e8` and writes `0x8000100c`; the targets are copied from
  the sound only when a note plays another sound (`0x40058a0a`, notes/66 §11.6: a change in the sound object alone
  does not reach them), so the part writes them too. That the smoother's input is the targets' block is `[HYP]`
  (the layout matches: `+14 + 66 t`); the machine will tell (a playing note hears the start values at once).
  3 552 bytes of code (3 264).
- **Crush 0.2**: `b = 127 − Bits` (in 8.8), the same arithmetic; off at the top. Its manifest's Bits starts at 32512.
  The cost states with the words turned round (the same work).
- **The proof**: the data block's start words; `start_tests` (the Turn harness with SRAM mapped: a step from none,
  from a filter, to none; the sound and the targets of tracks 0 and 3 that play it, not track 1's sound lock).
  `--dry` ALL OK; **the maintainer's run (2026-11-01): ALL OK but Crush's cost line** (a few instructions more for
  `127 − Bits`): off 31, hard 885, soft 1 639, bits 708, glide 1 672, silent 163, first 1 663, now declared; six tracks
  10 032 instructions a block, 9.3 %. The steps in four in one build: none → SMP keeps the values, SMP → CRU gives
  Rate 0 and Bits 127, CRU → R54 → REF the neutral words, back down the same, → none keeps them. The checks again
  green (generators, `tweaks.js`, claims, `ref_mainos`, webcompose, the smoke test ALL PARTS OK); the firmware the
  same (the cost is not in it).
- **Known**: right after a switch the values glide in (about 20 ms to two thirds, 70 ms nearly there): from Samples
  with Reso low to Crush, or a fresh sound to Crush, Bits rises from a few bits to off in that time.
- MAIN OS: Crush alone `365f496b…`, with Samples `01cf9060…`, every card `c089f700…`; Samples alone `854342c2…`, with
  SAMPLE `9499b519…`. Checks green: generators, parts, registrar, claims, overlaps, registry, `ref_mainos`, webbuild,
  webflash, webcompose identical, the smoke test ALL PARTS OK.
- **For the machine**: `build/crush-0.2/` (git-ignored, each checked by elektron-firmware-tool): Crush alone, Samples +
  Crush, every card (`c089f700…`), and the measuring build of every card (`measure/`, `55a4e4d7…`). To try: a fresh
  sound OFF → CRU reads Bits 127 and sounds unchanged; Bits to the left; SMP (Reso up) → CRU gives Rate 0 and Bits 127,
  CRU → SMP Cutoff 0 and Reso 0; SMP → OFF → SMP keeps Cutoff and Reso; with the pattern running the new values are
  heard at once (the targets, the open `[HYP]`), gliding in.

## 12. Lighter, the same bits: Crush 0.3 (2026-11-01)

The maintainer: « kannst du schon mal prüfen ob es noch möglichkeiten zur performance optimierung gibt? », then
« ja, übernehmen ».

- **Measured outside the proof**: the ColdFire interpreter of notes/69 §20.1 (`_scratch/pots-load/cfemu.py`, outside
  the repository) runs the device object of 0.2 and of a rewrite side by side (`_scratch/crush-opt/bench.py`): a decaying
  tone with noise, a note every 40 blocks, silences, full scale, random words with every corner, resets: **3 000 blocks,
  none differ**. Its signal is harder than the proof's (0.2 counts higher than the proof's numbers there), so the shares
  matter, not the counts. **Corrected (§17.3)**: that interpreter ran `ext.l` as `ext.w`, and 0.2's soft line uses
  `ext.l`, so its comparison could not see a difference on the soft side. The host builds of 0.2 and 0.3, compared
  directly over 20 000 blocks (about 10 000 on the soft side), give the same bits; the proof checks 0.3 and 0.4 bit for
  bit against their host build. The counts below are the interpreter's shares; the declared ones are the proof's.
- **Kept** (`crush.c` 0.3): the soft line's terms (`p`, `d >> 16`, `d & 0xffff`) worked out when a frame is taken, not
  every frame; the block scanned for silence only when the hold is silent. Instructions a track and block, 0.2 → 0.3 on
  the interpreter: soft + Bits 1 934 → 1 387 (−28 %), glide 1 970 → 1 522 (−23 %), hard + Bits 1 029 → 930 (−10 %),
  Bits 820 → 704 (−14 %), soft alone 1 268 → 719, hard alone 363 → 263, off and silent the same. 1 802 bytes of code
  (1 234): GCC versions the loops.
- **Dropped**: Bits' blend with a single bound on half the frame (`h < 2^30 − 2^(s−1)`, the same bits): GCC computes
  both paths before the branch and spills, 820 → 908. Only assembly would gain there (about 4 instructions a frame).
- **Left for later, small**: Samples could return before its silent scan at the centre (notes/72 §18, about 0.6 % for
  six tracks); the part could keep each track's entry instead of searching the table every block (about 0.1 %).
- **The proof, the maintainer's run (2026-11-01): ALL OK but the cost line** (0.2's numbers still declared). Counted
  for 0.3, now declared: off 31, hard 802, soft 1 183, bits 611, glide 1 307, silent 162, first 1 312 (0.2: 31, 885,
  1 639, 708, 1 672, 163, 1 663): six tracks at most 7 872 instructions a block, 7.3 % (9.3 %). The checks again green. Builds in `build/crush-0.3/` (Crush alone `da5584a0…`, with Samples `167d2883…`, every card `2b2fae73…`,
  measuring `9036b49a…`); the sound the same as 0.2's, bit for bit.

## 13. Bits from 8 bits: Crush 0.4 (2026-11-01)

The maintainer on 0.3: « zwischen 127 und ungefähr 45 passiert nichts hörbares ». The curve was linear in bits from
16 to 1: 112 gave 14.2 bits, 96 12.3, 80 10.4, 64 8.6, 45 6.3, 32 4.8, 16 2.9; above about 6 bits the rounding's noise
(−42 dB under full scale and lower) goes under in drums. Decided: « 8 bis 1 ». Crush 0.4: `e = 24 + 7 b / 127` in 8.8
(6144 + 7 b / 127), so 126 is about 7.9 bits, 96 about 6.3, 64 about 4.5, 32 about 2.8, 0 one bit; 127 off as before,
the step from off to 8 bits at the top. The same code otherwise (cost to be counted again: the blend and the top
level's saturation now come at other knob positions); the sound is not 0.3's below 127.
- Checks green (generators, parts, claims, overlaps, registry, `ref_mainos`, webbuild, webflash, webcompose, the smoke
  test ALL PARTS OK), `test_fltslot.py --dry` ALL OK, the host build under the undefined-behaviour sanitizer clean
  (127 untouched, 126.99 on the 8-bit grid, 0 the three levels). Builds in `build/crush-0.4/`: Crush alone
  `a151818c…`, with Samples `cbf53b93…`, every card `388d2043…`, measuring `84d3eae9…`.
- **The proof, the maintainer's run (2026-11-01): ALL OK**, the cost line too: 0.4 counts what 0.3 counted (off 31, hard
  802, soft 1 183, bits 611, glide 1 307, silent 162, first 1 312; the cost states take the same loops).

## 14. Tested on the machine: Crush 0.4, `fltslot` 0.8 (2026-11-01)

The maintainer, after the builds of `build/crush-0.4/` and the list of §13 (from the command line): « das ist so
geil. passt ». The load the measuring build showed was not reported. Experimental on the page until flashed from it.

## 15. Tested from the page (2026-11-01, release 0.27)

The maintainer flashed a build of the live page (`6ef171e`, release 0.26, stamp 2026-11-01-05, the page's files
compared byte for byte with the commit) on their Model:Cycles: « flash von live site passt ». The card is tested since
release 0.27 (`FEATURES`, the guide's line, README). No tag for now (the maintainer: « tag kommt später vielleicht
mal »).

## 16. Ready for more Track FX: `fltslot` 0.9, the proof from the manifests (2026-11-01)

The maintainer: « dann lass uns erst alles vorbereiten und danach werden parallel die fx gebaut ». Ring, Reso and EQ
(the list of §1's request) are built at the same time, each in a session of its own, on a branch of its own from the
branch `trackfx`, which holds this preparation; `main` stays on release 0.27 (tested) until they are merged.

- **Eight in a build** (`fltslot` 0.9; the maintainer: no hard limit at four, so as many as are offered): the table
  nine entries with none, the data block 1 132 bytes (`rows` 600, `cur` 880, `acc` 886, `old` 892, `neutral` 1020,
  `rec_next` 1028 — `entries.S` reads it there —, `diag` 1040, `sum` 1044, `peak` 1048, `n` 1052, `avg_t` 1054,
  `peak_t` 1056, `start` 1060), `most` 8. Each Track FX costs 72 bytes there; the image has about 265 KB left with every
  card. RETRIG + PITCH takes four detents a type, so a build with all of them is a longer turn. A track on none no
  longer searches the table (`index_of` returns at id 0), so the part's cost on such tracks does not grow with the
  table.
- **The proof from the manifests**: a Track FX whose manifest has `"proof": {"host": {"sources", "include",
  "defines"}, "cost_states": {state: [[k 28, k 29(, k 30, k 31)], ...]}}` gets, with no change to `test_fltslot.py`,
  its host build as the model (`HostModel`: the sources compiled with `cc -O2 -std=c99 -fwrapv`, called as
  `process(block, words, track, triggered)` / `reset(track)`), a selection of its own, a place in the full selection
  (Samples, the hosted ones, then REFF and its copies up to eight) and its cost counted in those states ("silent"
  plays no note). Crush moved there (the same states). REFF's copies go to `refflt9` (id 247); nine are refused.
  `--dry` ALL OK, eight in one build included. `compose.web_package` does not carry the proof section to the page.
- MAIN OS on the branch: Samples alone `adb6d1bf…`, with SAMPLE `62f07d89…`, Crush alone `8f78c203…`, with Samples
  `2b6d98a7…`, every card `74ac0913…` (not played: the part's offsets and the search only).

### 16.1 What is reserved

| Track FX | Package | Filter id | Type on screen | Note | Tweak and order | Branch |
|---|---|---|---|---|---|---|
| Ring | `tools/machines/ring/` | 3 | RNG | `notes/74-ring.md` | `74-ring.json`, order 74 | `trackfx-ring` |
| Reso | `tools/machines/reso/` | 4 | RES | `notes/75-reso.md` | `75-reso.json`, order 75 | `trackfx-reso` |
| EQ | `tools/machines/eq/` | 5 | EQ | `notes/76-eq.md` | `76-eq.json`, order 76 | `trackfx-eq` |

Note 71 stays MODAL's (stashed, not to be touched); 77 is the next free one after these.

### 16.2 What a Track FX session does, and what it leaves

- **Its own files only**: its package (sources, `manifest.json` with `uses` `track.filter`, `params` with `start`
  where its off is not the neutral word, `proof`, `cost`, `LICENSE` MIT), its generator `tools/gen_<id>.py` (as
  `tools/gen_crush.py`), its tweak, its note. Generated files that change with it on the branch (the other composed
  tweaks' conflicts, `REGISTRY.md`) are generated again at the merge, not merged by hand.
- **Not touched**: `fltslot`, `compose.py`, `composer.js`, `test_fltslot.py`, `docs/`, `README.md`, `BUILD.md`,
  `AGENTS.md`, `notes/README.md`, `PROVENANCE.md`, `gen_flasher_tweaks.py`, `webflash_smoke.js`,
  `webcompose_synth.py`. If one of them needs a change, the session stops there and says so. The card's texts, the
  guide section, the release line and the rows for those files go into the note's last section, « For the
  integration ».
- **The values**: four at most (k 28 to k 31: SWEEP and CONTOUR with CC 74 / 71, COLOR and SHAPE without a CC, all
  with p-locks, LFO, velocity, Control All); off is dry and is the start (a sound that steps to it sounds the same
  until a knob turns); exact integers or the EMAC with a C model of it for the host build (as Samples, POTS).
- **The load**: at most Samples' (about 1 500 instructions a track and block), measured first in the ColdFire
  interpreter outside the repository (`_scratch/pots-load/cfemu.py`, `_scratch/crush-opt/bench.py` as the pattern),
  declared from the maintainer's Unicorn run.
- **Checks**: its generator `--check`, `test_fltslot.py --dry`, `check_overlaps.py`, `claims.py --check
  --self-test`; Unicorn stops with SIGILL in the sandbox, so the full proof is the maintainer's. The official files
  are in the main checkout's `firmware/` (a worktree has none).
- **Commits** only with the maintainer's word, on its branch, with the trailer `Co-Authored-By: Claude`; no push, no
  merge.

## 17. Ring, Reso and EQ merged: release 0.28 (2026-11-01)

The maintainer, after the three sessions of §16 had committed on their branches: « Ja, mergen ».

### 17.1 Before the merge

- **The branches** (all from `df1b562`): `trackfx-ring` Ring 0.2 (`7917d3f`), `trackfx-reso` Reso 0.3 (`f1288cc`),
  `trackfx-eq` EQ 0.5 (`69c2fdd`); each proven by the maintainer's run of `test_fltslot.py` and played on the
  Model:Cycles from the command line (notes/74 §10, notes/75 §14, notes/76 §14).
- **The knobs** (the maintainer, after comparing them with the stock machines' COLOR as the timbre, SHAPE as the amount
  and feedback, SWEEP as the pitch, CONTOUR as the depth): Reso's Tone on COLOR and Decay on SHAPE, Brightness renamed
  Tone (too long for the popup); EQ's Mid on SWEEP and CONTOUR, its shelves on COLOR and SHAPE, as every Track FX has
  its frequency on SWEEP and its amount on CONTOUR (notes/75 §14, notes/76 §13). The popup breaks a long name into two
  lines at a space, about six characters each (notes/76 §14).
- **A trial merge** in memory (`git merge-tree`), Ring, Reso, EQ in that order: no conflict; in a worktree of it
  `test_fltslot.py --dry` ALL OK with Samples, Crush, Ring, Reso, EQ and three copies of REFF in one build, and
  `composer.js` composing the five with SAMPLE and both effects as `compose.py`.
- **History**: Reso's and EQ's notes held an absolute path of the maintainer's machine in the proof's command; with
  the maintainer's word their branches were rewritten (only that line, the messages, authors and dates kept) before
  the merge.

### 17.2 The merge

- Three merge commits on `trackfx`, Ring, Reso, EQ; no conflict. Generated again rather than merged: the composed
  tweaks' conflicts (27, 28, 29, 34, 36, 39, 70, 72 to 76 through their generators: `ring`, `reso`, `eq` added, the
  objects unchanged), `REGISTRY.md`, `tweaks.js` (eleven cards), `REF_MAINOS` (67 combinations) and `REF_MODS`.
- **Cards** (experimental): `FEATURES` and `OFFERED` in `tools/gen_flasher_tweaks.py`, `FEAT` and `GUIDE_OF` in
  `docs/flasher/app.js`, the texts of notes/74 §11, notes/75 §15 and notes/76 §15. **Guide**: sections 8 Ring, 9 Reso,
  10 EQ (the later ones moved on by three); RETRIG + PITCH steps through the ticked Track FX in the order of the cards
  (SMP, CRU, RNG, RES, EQ), in every Track FX section; on a track whose Track FX has no value on a knob, RETRIG + that
  knob shows the first ticked Track FX's name for it and changes nothing heard (notes/72's naming rule). **Release**
  0.28, stamp `2026-11-01-07`; `README.md` (eleven cards, the first eight tested), `BUILD.md`, `PROVENANCE.md`,
  `notes/README.md`, the `AGENTS.md` map (76 the last note).
- **Checks' lists**: `tools/webflash_smoke.js` (eleven cards, the three in Track FX, tagged experimental, each alone and
  with Samples and Crush, every card in one build), `tools/webcompose_synth.py` (the three alone, each with Samples and
  Crush, the full offered set).
- MAIN OS: Ring alone `3cdd61c0…`, Reso alone `c92e3d14…`, EQ alone `31e4456f…` (as on their branches); with Samples
  and Crush `b5a8c7e9…`, `8dc2d4c2…`, `be915b71…` (the same); the five Track FX `7b039982…`; every card of the page
  `a1736027…`, also `REF_MAINOS`' key of every card, the same measuring (`--diag-filters`) `f256bb57…`. Builds in
  `build/trackfx-0.28/` (git-ignored).
- **The proof, the maintainer's run on the merge (2026-11-01): ALL OK**, 590 checks: each Track FX alone and the eight
  in one build (Samples, Crush, Ring, Reso, EQ and three copies of REFF) bit for bit their host builds, nineteen changes
  of Track FX in the audio, RETRIG + PITCH through ids 0, 1 to 5, 253 to 255 with each one's start words, the names
  after the track's Track FX; every cost line as its manifest declares (Samples, Crush, Ring 0.2, Reso 0.3, EQ 0.5, so
  Ring's and EQ's last declared counts are checked now too).
- **On the machine (2026-11-01)**: the maintainer, after the build of every card from `build/trackfx-0.28/every-card/`
  (from the command line) and the list asked for (the five Track FX in turn on RETRIG + PITCH, Samples and Crush on
  `fltslot` 0.9, the popups' names, six tracks on different Track FX, a knob without a value, saving and loading):
  « getestet, passt ». The load the measuring build shows was not reported. Experimental on the page until flashed
  from it.

### 17.3 Corrected

§12's comparison in the interpreter (3 000 blocks, Crush 0.2 against 0.3) could not see the soft side: the
interpreter ran `ext.l` as `ext.w` (found by the Ring session, fixed in `_scratch/`). The host builds of both, compared
directly over 20 000 blocks, give the same bits, so 0.3 sounds as 0.2; the proof's checks of 0.3 and 0.4 against their
host build were never affected. A second fault, indexed displacements read as decimal, was found by the Reso session;
Crush uses none above 9. The interpreter's copies stay outside the repository.

## 18. Ring, Reso and EQ tested from the page (2026-11-01, release 0.29)

The maintainer flashed a build of the live page (`d119203`, release 0.28, stamp `2026-11-01-07`, the page's seven files
compared byte for byte with the commit) on their Model:Cycles: « getestet, passt ». Ring, Reso and EQ are tested
(release 0.29): their status in `FEATURES` and `tweaks.js`, the guide's *Tested* lines, `README.md` (all eleven cards
tested), `tools/webflash_smoke.js` (no tag on their cards), stamp `2026-11-01-08`.

## 19. A knob without a value: `fltslot` 0.10 (2026-11-02, release 0.32)

**Report (2026-11-02).** Feedback the maintainer received: names such as Ring Shape stay on a knob when the track's
Track FX is not Ring, and when the Track FX is off.

**Diagnosis `[FAIT]`.** That was the naming rule of §17.2 (notes/72 §3): on a track whose Track FX has no value on a
knob, and on every knob of a track on none, RETRIG + that knob showed the name of the build's first Track FX that has
one (`compose.names()`: a value an entry lacks is named after the first filter that declares it) and edited k 28..31
unheard. Two more places followed from it: Control All's lookups of each track (`0x4001d716`, track 0..5) renamed the
values after each track in turn, so the names left on the descriptor rows were track 6's; LFO + RETRIG + such a knob
made the value the LFO's destination although the track's Track FX does not use it.

**The maintainer's decisions (2026-11-02).** On none: the popup reads *Track FX* over *OFF*. On a Track FX without the
value: its tag over `---` (« CRU --- »), not *Track FX* over *CRU*, which looks like the type's choice. *N.A.* does not
fit: the screen shows three characters of a value (notes/47 §3.3); `-` is in the font (Cutoff's -64), `/` is not known
to be. Nothing changes on such a knob.

### 19.1 The encoder handler, read again `[FAIT]`

ParameterPageView's encoder handler (`0x4001f4f0`), in order:

| Where | What |
|---|---|
| `0x4001f598` | LFO held: `0x4001eaa2`, the destination (no lookup; `fl_lfo` at `0x4001ead8`); the caller ignores its d0 |
| `0x4001f6ee` | the lookup, track -1 (`fl_knob`); descriptor 0 ends the handler at `0x4001f704` |
| `0x4001f708`..`0x4001f768` | the popup: a new (descriptor, track) is set up by `0x4001ddb2`, which keeps the six tracks' values (`+508`), not the names; the names are read from the rows when drawn |
| `0x4001f7ea` | the step (`0x4006f96a`); 0 ends the handler |
| `0x4001f7fe`, `0x4001f81a` | key 12 (to the end, no edit), FUNC (the fine step, no edit) |
| `0x4001f886` | TRACK held? `fl_keys` sits here: on descriptor 5, `fl_step` and the end |
| `0x4001f912` | TRACK: Control All, vtable +0x5c (`0x4001d6e4`, which asks the lookup for each track, `0x4001d716`, and uses its answer without testing it) |
| `0x4001f962` | a held step (`0x4006bdfe`): the p-lock, vtable +0x74 |
| `0x4001f950` | otherwise the edit, vtable +0x54 |

Every edit comes after `0x4001f886`, so descriptor 5 changes nothing with FUNC, TRACK or a held trig either. The
lookup's other caller is the popup at a track change (`0x4001f090`, track -1). `0x4001eaa2`'s own end is `0x4001eccc`
(`movem` from its stack, `lea 60(sp)`, `rts`), where a knob past 11 goes.

### 19.2 `fltslot` 0.10

- **`nvals`**: each entry's count of values, written by both composers at `+1132` (none 0); the data block grows from
  1 132 to 1 144 bytes. `na` (`+1041`) and `lfo_keep` (`+1042`) take two of the spare bytes after `diag`.
- **`fl_knob`**, track -1, RETRIG + SWEEP / CONTOUR / COLOR / SHAPE: the values take the names of the selected track's
  entry (`name_values`), then the value's descriptor when the entry declares it, else descriptor 5 through
  `show_type(1, …)`: `na` set, descriptor 5's long name in both tables the entry's tag (Track FX for none), its
  object with the type's formatter and descriptor 1's steps, as for the type. RETRIG + PITCH: `show_type(0, Track FX)`.
  Track 0..5 (Control All): the value's descriptor when the build has it, as before, and no names written.
- **`fl_fmt_type`**: with `na`, `---` for a filter, OFF for none, also in a measuring build (the type's peak stays on
  RETRIG + PITCH).
- **`fl_step`**: nothing with `na`; after a step the values take the new entry's names.
- **`fl_lfo_desc` / `fl_lfo`**: with RETRIG, a value the selected track's entry lacks (or none) sets `lfo_keep`;
  `fl_lfo` then frees the knob list as the routine does at `0x4001eae2`, drops its return address and goes to
  `0x4001eccc`: no destination set, no popup. A value it has: the names follow it, then the destination as before.
- A knob that no Track FX of the build has (COLOR with only Samples and Crush) now shows the popup too; before 0.10 the
  lookup gave the stock answer there, the machine's value under RETRIG (RETRIG + a knob has no meaning in the stock OS,
  notes/72 §3).
- Code 3 376 → 3 736 bytes, 104 relocations; each Track FX build 372 bytes longer (`REGISTRY.md`).
- `[HYP]` The LFO page shows its destination's short name from the descriptor's row. Those rows now hold the selected
  track's Track FX's names after each RETRIG + knob, LFO + RETRIG + knob and step of the type; a value the Track FX
  lacks keeps the first Track FX's name there. Not looked at on the machine.

### 19.3 Proof and checks

`tools/emu/test_fltslot.py`: the data block's `nvals`; the lookup on the selected track's sound with none, an id the
build lacks and each Track FX (the value's descriptor or 5 with `na`, descriptor 5's name and object), every value
named after the selected track's entry, Control All's lookups of tracks 0..5 (the descriptor, the names untouched),
RETRIG + PITCH clearing `na` and putting Track FX back; LFO + a knob through the OS's own path on each Track FX (no
destination and the list freed as the routine frees it where the Track FX lacks the value); the type's formatter with
`na` (`---`, OFF, also measuring); `fl_keys` with `na`: the handler's end, no step after twelve detents both ways.
Here `--dry` ALL OK (Unicorn stops with SIGILL in this sandbox). **The maintainer's runs (2026-11-02):** the first, 12
ECHEC, all the one check of the values' names in every build, Reso and EQ too: the test expected `na` at 0 after a
value's answer, but the part sets `na` only with descriptor 5, where alone it is read, and the loop starts on none;
the test now checks `na` on descriptor 5 alone and names each condition that fails. The part unchanged. The second
run: **ALL OK** (the cost lines as declared).

Green: `gen_parts.py --check`, the five generators' `--check`, `gen_flasher_tweaks.py --check`, `check_overlaps.py`,
`registry.py --check`, `claims.py --check --self-test`, `webbuild_check.sh`, `webcompose_check.sh` with the official
file (composer.js identical to compose.py), `webflash_check.sh`, `webmanager_check.sh`, `webflash_smoke.sh` with both
official files (ALL PARTS OK, the 67 combinations of `REF_MAINOS` regenerated), `py_compile`.

MAIN OS: Samples alone `62db5452…`, with SAMPLE `7350c436…`; Crush alone `3e95ccad…`, with Samples `32df8895…`; Ring
alone `704f5f65…`, Reso alone `0b0fdba1…`, EQ alone `cf01be47…`; Samples, Crush and Ring `85467706…`, with Reso
`45a81abb…`, with EQ `d53b1fe6…`; every card of the page `09661941…`. Builds in `build/trackfx-0.32/` (git-ignored):
`every-card/` and `smpfilter+crush+ring/`.

**What was asked on the machine (§19.4):** on a sound with Track FX OFF, RETRIG + SWEEP / CONTOUR / COLOR / SHAPE: Track
FX over OFF, nothing changes; on Crush, RETRIG + COLOR or SHAPE: CRU over `---`; on Ring, RETRIG + SHAPE: RNG over `---`;
the same with a trig held (no lock), with TRACK (no track changes) and with FUNC; LFO + RETRIG + COLOR on Crush: the
LFO's destination stays; RETRIG + PITCH still steps and reads Track FX; Control All on a value (TRACK + RETRIG + SWEEP)
still sets six tracks and the popup keeps the selected track's name.

### 19.4 On the machine (2026-11-02)

The maintainer flashed `build/trackfx-0.32/every-card/` (every card of the page, from the command line, MAIN OS
`09661941…`, as `REF_MAINOS`) and went through the list one step at a time: on none, RETRIG + SWEEP and COLOR read
« track fx | off »; on Crush, COLOR and SHAPE CRU over `---`, SWEEP Crush Rate, « passt alles, wie erwartet »; on
Crush with a trig held (no lock), with TRACK (no track changed) and LFO + RETRIG + COLOR (the destination stayed):
« passt »; RETRIG + PITCH steps as before and on Ring SHAPE reads RNG over `---`, COLOR Ring Shape: « passt ». Control
All on a value (TRACK + RETRIG + SWEEP on Ring, Crush on another track) moves the value on every track, and the popup
names the track it is turned on; the maintainer: « so lassen » (Control All stays per knob, as in the stock OS, where one
knob moves a different parameter on each machine; before 0.10 the popup named track 6's).

## 20. Lighter again, the same bits: Crush 0.5 (2026-11-03, release 0.34)

The maintainer: « track Fx: prüfen: wesentliche performance optimierungen möglich wenn der fokus nicht darauf liegt das
am ende alle bytegleich rauskommt, sondern wirklich darauf die cpu last zu reduzieren » (a change of sound allowed);
after a listening page, « 0.4 klingt besser. stufenlos fügt oben viel rauschen hinzu. », then « Ja, einbauen ».

### 20.1 Measured outside the repository

The ColdFire interpreter of notes/69 §20.1 (`_scratch/cfemu/cfemu.py`, outside the repository) ran a prototype with
one switch per idea (`_scratch/crush-opt2/`, its `REPORT.md`) against 0.4. It compared each device object against its
own host build, counted the manifest's cost states, and scanned Rate over its whole range with Bits at 127, 95, 47 and 0.
It also compared the host builds against 0.4 on a mix (kick, hat, bass, chord) in ten states. Instructions a track and
block on the interpreter (its own signal, so compare shares, not counts):

| | hard | soft | bits | glide | first | dearest state | dearest over Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.4 | 930 | 1 387 | 704 | 1 535 | 1 525 | 1 535 | 1 807 |
| the soft line as a ramp, its slope at each take (dropped) | 936 | 1 307 | 712 | 1 671 | 1 460 | 1 671 | |
| the soft line on the EMAC (kept) | 942 | 1 237 | 712 | 1 287 | 1 352 | 1 352 | 1 374 |
| the hard hold's Bits at the take (kept) | 351 | 1 398 | 707 | 1 546 | 1 535 | 1 546 | |
| Bits without steps (dropped by ear) | 703 | 1 210 | 490 | 1 358 | 1 347 | 1 358 | 1 630 |
| the silence scan's ends first (kept) | 936 | 1 398 | 710 | 1 546 | 1 438 | 1 546 | |
| Rate and Bits in one pass (kept) | 837 | 1 273 | 704 | 1 421 | 1 411 | 1 421 | |
| **0.5**, the four kept | 359 | 1 109 | 709 | 1 159 | 1 124 | 1 159 (−24 %) | 1 245 (−31 %) |

- **The ramp, dropped.** With a take every two or three frames (glide's soft side), the slope and the line's start at
  each take cost more than the frames save, and GCC spills. The line on the EMAC does the same work in one product a
  frame, bit for bit.
- **Bits without steps, dropped by ear.** The idea: a step of 2^s · 2^(f/256) itself, the frame times 1/(2m) on the
  EMAC, 0.4's grid, then times 2m, saturated. It equals 0.4 on a whole bit count. Alone it saves 12 %, with the rest
  40 %. Between two counts it has 1 to 4 dB more noise than 0.4's blend at the same knob, because the blend's two
  roundings partly cancel. The maintainer heard both on a listening page (a private page whose browser computes 0.4
  and this one, bit for bit as their host builds) and kept 0.4's.
- **A state the manifest lacked.** 0.4's dearest block was not glide. It was the soft side next to the centre with
  Bits on (Rate −1, Bits 95), a take nearly every frame and the line's terms worked out at each: 1 807 instructions
  against glide's 1 535 on the interpreter. In the proof's terms that is about 1 545, 8.6 % of a block for six tracks
  against the 7.3 % declared (an estimate: the interpreter's ratio to the proof for 0.4, about 1.17, carried over).
  The manifest's cost states now have it: `dense`, `[[16128, 24320]]`.

### 20.2 `crush.c` 0.5

- **The soft line on the EMAC.** 0.4 computes p + dh t + (dl t >> 16), the line's value at half scale. That is
  floor(d t / 2^16) = floor(d (t << 15) / 2^31): one `mac.l` and `movclr.l` from a clear acc0 (truncating, so the
  floor). The host model does the same product in 64 bits, as `tools/emu/emac.py` executes it.
- **The clock** runs as P = ph << 16 with I = inc << 16. A take is the carry of P + I. The line's end, where 0.4 holds
  t at ONE, is the carry of the next P + I. Under it, t << 15 is (P + I) >> 1.
- **The hard hold with Bits** rounds the taken frame once, when it is taken (blend or grid, as 0.4), instead of every
  frame. The same frames come out.
- **Rate and Bits in one pass.** The macros `HARD` and `SOFT` take the frame's output, and `BITS` picks blend or grid
  for the block's count.
- **The silent hold's scan** runs only when the block's first and last frames are 0.
- 644 bytes more in the image (8 472, `crush_process` 2 144 bytes against 1 500). The slot already calls a filter
  with MACSR 0xa0 and the accumulators clear and leaves the EMAC to it (`fltslot.c`). Crush leaves acc0 clear.

### 20.3 Proven, checked

- **Bit for bit against 0.4.** The host builds over 30 000 blocks: random words with every corner, notes, resets,
  silences, full scale, blocks just above −FS, and a lone sample at the block's start, middle and end. Also the mix in
  ten states. None differ. The device object in the interpreter against its host build, over 1 500 blocks: none differ.
- **Interpreter counts, 0.4 → 0.5:** off 31 → 36, hard 930 → 359, soft 1 387 → 1 109, bits 704 → 709, glide
  1 535 → 1 159, silent 162 → 166, first 1 525 → 1 124, dense 1 732 → 1 224. Over Rate's whole range, 1 807 → 1 245.
- **Green:** `gen_crush.py --check` and the other four Track FX generators, `gen_parts.py --check`,
  `gen_flasher_tweaks.py --check`, `check_overlaps.py`, `registry.py --check`, `claims.py --check --self-test`,
  `webbuild_check.sh`, `webcompose_check.sh` with the official file (identical), `webflash_check.sh`,
  `webmanager_check.sh`, `webflash_smoke.sh` with both official files (ALL PARTS OK, the 67 combinations of
  `REF_MAINOS` regenerated), `ref_mainos.py --check`, `py_compile`, and `test_fltslot.py --dry` ALL OK.
  `relocate_6ch.py --check` differs as before (§7).
- **The proof, the maintainer's run (2026-11-03): ALL OK but the cost line**, which still declared 0.4's numbers and
  no `dense`. Counted for 0.5, now declared, with 0.4's in brackets: off 36 (31), hard 327 (802, −59 %), soft 952
  (1 183, −20 %), bits 615 (611), glide 994 (1 307, −24 %), silent 166 (162), first 978 (1 312, −25 %), and `dense`
  1 066, now the dearest. Six tracks come to at most 6 396 instructions a block, 5.9 % (7.3 % declared for 0.4, about
  8.6 % in its `dense` by §20.1's estimate). Then the checks again green, the smoke test ALL PARTS OK.

MAIN OS: Crush alone `36494141…`, with Samples `44e16270…`; Samples, Crush and Ring `7f9371fa…`, with Reso
`c1be9428…`, with EQ `567c2b42…`; every card of the page `0d64b14e…`. All match `REF_MAINOS`. Builds in
`build/crush-0.5/` (git-ignored): Crush alone, with Samples, `every-card/`, and two measuring builds of Samples and
Crush that differ only in Crush, `measure/` (0.5, MAIN OS `59b23039…`) and `measure-0.4/` (0.4 from `3b4e972`,
`4e65f8bf…`).

### 20.4 On the machine (2026-11-03)

The maintainer flashed `build/crush-0.5/every-card/` (every card of the page, from the command line, MAIN OS
`0d64b14e…`, as `REF_MAINOS`). Crush chosen with RETRIG + PITCH, Rate turned both ways, Bits turned down, then Crush
on all six tracks at Rate −1 and Bits 95, the dearest state: « Passt » (the sound as before, no crackle, no dropout).

## 21. CC 75 and 76 on COLOR and SHAPE: `fltslot` 0.12 (2026-11-11, release 0.60)

A check of the MIDI CCs on 2026-11-11 (outside the repository) found the Track FX's values on SWEEP and CONTOUR on
CC 74 / 71 and NRPN 1:20 / 1:21 since `fltslot` 0.2 (notes/72 §3), and those on COLOR and SHAPE on none: Ring's Wave,
Reso's Tone and Decay, EQ's Low and High Gain could not be played from outside. The maintainer's decisions of the same
day: **CC 75 / 76 and NRPN 1:22 / 1:23** for COLOR and SHAPE; no CC for the choice of the Track FX or of a pattern's
effect for now (new code, not data); SAMPLE keeps the Cycles' CCs by knob (COLOR 16 Start, SHAPE 17 Length, SWEEP 18
Cutoff, CONTOUR 19 Reso, DECAY 80, copied from SNARE's descriptors, `compose.py`) rather than the Model:Samples' (its
OS 1.13's descriptor table at its `0x40109048`, read, not run: Pitch 16, Loop 17, Flip 18, Start 19, Length 20,
Cutoff 74, Reso 71, Decay 80, which would meet the Track FX's 74 / 71 and break today's mappings).

### 21.1 The OS's tables `[FAIT]`

- At boot `0x4005a274` builds, from the descriptors, k → descriptor by machine (`0x4005a692`), CC → descriptor by
  track (`0x4005a8ce`) and NRPN → descriptor (`0x4005a92e`); `fl_boot` writes descriptors 1..n before it (notes/72 §3).
  `0x4005a8ce` looks CC 16–23 up only in the row of the track's machine, the others in the rows every machine shares:
  a CC 20–23 on descriptors 3 and 4 (group 7, every machine) reaches nothing. The OS's builder and both lookups, run in
  the interpreter `cfemu` with the stock rows and with candidate rows for 3 and 4: CC 75 / 76 and CC 77 / 78 each reach
  descriptors 3 and 4 on all six tracks and every stock machine, NRPN 1:22 / 1:23 too, nothing else changes; CC 20 / 21
  reach nothing (stock: 16–19 by machine, 20–23 nothing on every track).
- Stock, the CCs that reach a descriptor on a track: 3, 7, 10, 12–19, 65–67, 70, 80, 102–110; on the FX channel 3, 14,
  15, 85–88, 102–110; the NRPNs 1:26–1:30, 1:32–1:39, 3:0. Next to 74 and 71, 72, 73 and 75–79 are free and outside
  the numbers MIDI reserves or controllers use for other things (0 / 32, 64–69, 96–101, 120–127).
- On the Syntakt (manual OS 1.40, appendix B.4) 74 is Filter Frequency, 75 Resonance, 76 Filter Type, 77 Env. Depth,
  78 Env. Delay, NRPN 1:20–1:23 Frequency, Resonance, Type, Env. Depth: 75 / 76 sit next to 74 as the maintainer chose,
  with other meanings than on the Syntakt.
- A CC's value is not scaled: the CC handler (`0x4000b568`) writes it × 256 and the setter `0x4000b274` clamps it to
  the descriptor's range (notes/72 §1, corrected the same day); 0..32512 is the whole range.
- An edit sends the descriptor's CC: the OS's sender (`0x4000b942`, a method of the parameter sets, `0x400fd114` and
  three more) reads it from the stock table (`0x4005a7f8`, `0x4010dce0`), which `fl_boot` writes too `[FAIT, by
  reading]`; RETRIG + COLOR or SHAPE now sends CC 75 or 76 where nothing went out before (§21.4).

### 21.2 `fltslot` 0.12

- **Data only**: in `part.json`, `values.cc` 2 and 3 `0x004bffff` / `0x004cffff` (CC 75 / 76, no LSB), `values.nrpn`
  2 and 3 `0x96` / `0x97` (1:22 / 1:23), `claims.midi` CC 74, 71, 75, 76 and NRPN 1:20–1:23. No code: `fltslot.o` as
  before (`gen_parts.py --check`); both composers write the rows from the manifest (`compose.py`, `composer.js`).
- **Only builds with a third or fourth value change.** The part writes descriptors 1..n, n the most values one of the
  build's Track FX declares: Samples and Crush 2, Ring 3, Reso and EQ 4. A build of Samples, Crush or both keeps its
  MAIN OS; with Ring, CC 75 on COLOR; with Reso or EQ, 75 and 76. `74-ring.json`, `75-reso.json`, `76-eq.json` change
  in the part's data block, `72-smpfilter.json` and `73-crush.json` do not.
- On a Ring track CC 76 writes k 31, which Ring does not use: kept with the sound, not heard, as CC 74 on a track
  without a Track FX `[HYP]` (by reading: the CC handler, `0x4000b568`, writes the descriptor's k without the knob
  lookup that shows `---` since `fltslot` 0.10, §19).
- Users' MIDI mappings of 75 and 76 now reach the Track FX on every track; renumbering them later would break them.

### 21.3 Proven, checked

- **`test_fltslot.py`**: the CCs and NRPNs it expects on descriptors 1..n come from the manifest (74 / 71 and
  1:20 / 1:21 were written into the test before), and a first check says the part's MIDI claim is its values'.
  `--dry` ALL OK. The full run (Unicorn), the maintainer's (2026-11-11): ALL OK.
- **Green**: `gen_smpfilter.py`, `gen_crush.py`, `gen_ring.py`, `gen_reso.py`, `gen_eq.py` (the last three rewritten,
  the first two the same bytes), `gen_parts.py --check`, `gen_flasher_tweaks.py --check`, `check_overlaps.py`,
  `registry.py --check` (REGISTRY.md does not change: it lists no part's MIDI claim before notes/65 §17),
  `claims.py --check`, `webbuild_check.sh`, `webcompose_check.sh` with the official file (identical),
  `webflash_check.sh`, `webmanager_check.sh`, `webuploader_check.sh`, `gen_wavetables_page.py --check`,
  `webflash_smoke.sh` with both official files (ALL PARTS OK, the 137 combinations of `REF_MAINOS`),
  `ref_mainos.py --check`, `py_compile`.
- **MAIN OS**: Samples alone `c422bf38…`, with SAMPLE `5dee5685…`, Crush alone `e3e6b94a…`, Samples and Crush
  `e05c2951…`, all as with 0.11; Ring alone `5f7e2f03…`, with Samples and Crush `9fcac455…`, with the CPU page
  `5cbc86ee…`; Reso `6ff88f34…`, `9ce86da6…`; EQ `b5f6d9d8…`, `bc55e38d…`; every card of the page (sixteen, as in
  notes/71 §11) `dd9183af…`, built in `build/trackfx-cc-0.12/` (git-ignored) for the machine.

### 21.4 On the machine (2026-11-11)

The maintainer flashed `build/trackfx-cc-0.12/` (every card, MAIN OS `dd9183af…`, from the command line) and played,
with a Web MIDI page of the session's (outside the repository) sending and showing the CCs over USB:

- Reso on track 1: CC 75 and 76 on T1's channel change Tone and Decay, RETRIG + COLOR / SHAPE then show the value;
  the same on the AUTO channel; EQ on track 2: CC 75 and 76 move Low and High Gain, track 1 unchanged; NRPN 1:22 and
  1:23 as CC 75 and 76: « funktioniert ».
- Out: RETRIG + COLOR, SHAPE and SWEEP send CC 75, 76 and 74 on T1 OUT's channel. Nothing came at first: TRACK
  SETUP's MOUT was off on track 1, which the OS needs for any knob's CC (manual 9.4.2, with ENCS at I+E); with it on,
  « funktioniert jetzt alles ».
- Not played: Ring's CC 75 (the same rows, the same code as Reso's and EQ's).
- **From the page** (release 0.60, after the push of `3553218`): every card ticked, flashed, Reso on track 1, CC 75 and
  76 on T1's channel: « geflasht, passt ».
