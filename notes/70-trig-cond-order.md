# 70 — Trig conditions in another order on the knob: the `trig-cond-order` tweak

The maintainer's request of 2026-10-30: a trig held + CHANCE goes through the trig conditions in a fixed order,
FILL … !1st, then the 21 percentages, then the 35 A:B conditions; they want the A:B conditions before the
percentages, and only the knob's order changed ("nur den Knopf umsortieren"), not what a trig keeps. Tweak
`80-trig-cond-order.json` (`tools/gen_trig_cond_order.py`, sources in `tools/machines/trig_cond_order/`), proof in
emulation `tools/emu/test_trig_cond_order.py`. Addresses: VAs of OS 1.13.

## In short

- **A trig keeps one condition code, 0 to 63**, and everything goes by that code: the sequencer, the names on the
  screen, and the stock knob, which steps the code itself. So the menu's order is the codes' order (§1, §2).
- **The tweak changes the knob only.** One vtable entry, TrigParameterSet's "value + delta" (`0x400fd218`), goes to
  code and order in a freed 48×22 sprite mask: for Trig Cond, the knob steps a position in the new order and writes
  back the code at that position; every other parameter keeps the stock method (§3). Since the first device test,
  a 6-byte detour also gives the value window's five dots that position (§8): 178 bytes in all.
- **New order**: FILL, !FILL, PRE, !PRE, NEI, !NEI, 1st, !1st, 1:2 … 8:8, 1% … 99%.
- **Patterns are the same with and without the tweak, both ways**: the codes stored, played and shown are the stock
  ones. The first turn on a trig without a condition still gives FILL; a fast turn or FUNC steps as many positions
  as the stock knob steps codes.
- Status: **tested on the machine (2026-10-30, §9)**, with the dots' fix (§8); proven in emulation (ALL OK, §6, §8.2).
  A card in the web flasher since release 0.18, experimental there until flashed from the page (§10).

## 1. What a trig keeps, and who reads it `[FAIT]`

| What | Where | Role |
|---|---|---|
| The condition byte | pattern track data `+ 516 + step` (steps 0..63) | -1 = no condition, else the code 0..63 |
| Getter / setter | `0x40015fd0(track, step)` / `0x40016010(track, step, code)` | the data through the track's vtable `+0x28`; the setter clamps to -1..63, stores, then tells the track (`+0x10`, info `0x400ff59c`) |
| The codes | — | 0–7 FILL, !FILL, PRE, !PRE, NEI, !NEI, 1st, !1st; 8–28 1 % … 99 % (21); 29–63 1:2 … 8:8 (35) |
| Descriptor 19, "Trig Cond" / "COND" | `0x4010e108` | group 18 (trig parameters), slot 5, range `0..0x3f00` (8.8), no CC |
| The formatter | `0x4004a4ce` (put in the interface objects at `0x400de37c`) | `value >> 8` > 63 → "ERR", else the name `0x401090b4[code]` |
| The short draw | `0x40050040` | -1 → "-", else `0x40108f54[code]`, the odd codes ≤ 7 with a bar over the name (the "!") |
| The sequencer | `0x400913f0` | a jump table on the code (`0x40091428`): the eight named ones; the percentages against `0x40115dec[code − 8]`; A:B by ranges (29–30 → 2, 31–33 → 3, … 56–63 → 8) |

The menu's order is therefore the codes' order: a new order on the screen without a new storage needs the knob alone.

## 2. The knob for a held trig `[FAIT]`

- `ParameterPageView::consumeEncoderEvent` `0x4001f4f0`: the knob's descriptor (`0x4001e814`, CHANCE → 19 with a trig
  held, notes/68 §8.2), the step from the interface object (`0x4006f96a`, 8.8, faster turns give bigger steps), then
  with a trig held its vtable `+0x74` (`0x4001e93e`), which runs a closure (invoker `0x4001f15a`) for each held trig.
- The closure: the trig's value, `+0x60`. **Without a condition** it only makes one: `+0x6c` / `+0x50` give the
  starting value (the TrigParameterSet's default, `0x4000a880`, which is 0 = FILL for descriptor 19; a value of the
  locked sound when the trig has a sound lock) and `+0x64` sets it ("Lock mem full!" when it can't); this turn moves
  nothing. **With a condition**, a non-zero step goes to `+0x70` = `0x4001e268`.
- `0x4001e268`: its `+0x80` (`0x4001dff4`) gives, for group 18, the pattern track's `TrigParameterSet` (`0x4000f26c`:
  track + 48; built by `0x4000b8f8` from `0x40017fea` and `0x400180a4`, vtable `0x400fd204`, typeinfo `0x400fd080`,
  "16TrigParameterSet"), then a tail call of its `+0x30`, ParameterSet's step `0x4000a5f8(set, desc, delta, step)`:
  - `+0x24` `0x4000aaee`: the trig's value, the condition byte `<< 8` (-1 when it has none, 0 for a step > 63);
  - `+0x14` `0x4000a980`: `value + delta` clamped to the descriptor's range (`0x4005a65a`), then the range check
    `+0x18` (`0x4000aa4e`), which a clamped value always passes;
  - `+0x28` `0x4000abdc`: stores `value >> 8` through `0x40016010`.
- So the stock knob gives `code + (delta >> 8)`, clamped to 0..63: a fraction of a step below zero takes the code
  down by one, above zero it does nothing (arithmetic shift).

## 3. Design

- **Not renumbering.** Changing what the codes mean (names, sequencer, the A:B ranges) would make every pattern
  saved with the stock OS play other conditions with the mod, and the other way round. Only the knob changes.
- **Where.** `TrigParameterSet`'s `+0x14` is a pure function of `(set, desc, value, delta)` between the read and the
  write, and its vtable entry `0x400fd218` is read for TrigParameterSet objects only (the base ParameterSet's vtable
  `0x400fd0cc` and the other sets keep their own `0x4000a980`). One 4-byte write, nothing to replay. The view's
  `+0x70` (`0x4010059c`) was the other candidate (notes in the first reading); it would have meant reading and
  writing the trig's value again in the tweak's code.
- **`tco_step`** (`tools/machines/trig_cond_order/trig_cond_order.S`): for descriptor 19 and a value whose code is
  0..63, the code's position in `tco_order` moves by `delta >> 8`, clamped to 0..63, and the code at the new
  position comes back `<< 8`. Anything else (another descriptor, a trig without a condition, a value out of range)
  jumps to `0x4000a980` with the same arguments. Same step sizes as the stock knob, so fast turns and FUNC behave as
  before, counted in positions.
- **The order** (`ORDER` in the generator, written into the image's 64 bytes after the code): positions 0–7 codes
  0–7, positions 8–42 codes 29–63 (1:2 … 8:8), positions 43–63 codes 8–28 (1 % … 99 %).
- **Unchanged**: the first turn on a trig without a condition (FILL, position 0 in both orders), the names, the short
  draw, the sequencer, the track's Chance (descriptor 22, another set), every other trig parameter.

## 4. Free space and conflicts

- Code and order: 134 bytes at `0x40152d38` in the first version (70 of code, 64 of order), 178 since the dots' fix
  (§8.2), in the freed 48×22 mask (192 bytes) whose constant `0x400b9726` now points at the kept copy `0x4014b364`
  (`tools/sprites.py`, REGISTRY.md §1).
- The vtable entry `0x400fd218`: REGISTRY.md §5 (rewritten pointers). Next to it, lfo-plus rewrites `0x400fd150` and
  `0x400fd190`, chord-keys `0x400fd170` and `0x400fd174`, entries of other sets' vtables.
- No tweak writes the ranges the tweak relies on (the knob path above, the getter and setter, descriptor 19, the
  names, the formatter, the short draw, the sequencer); `tools/check_overlaps.py` passes with it.
- No claims: the vocabulary's descriptors are the unused 1–4 (notes/65); the tweak takes no descriptor, formatter,
  saved byte, key combination or view.

## 5. The tweak `[FAIT]`

| Write | Stock | New |
|---|---|---|
| `0x400b9726` | `0x40152d38` (the mask) | `0x4014b364` (the kept copy) |
| `0x400fd218` | `0x4000a980` | `0x40152d4a`, `tco_step` (`0x40152d38` in the first version) |
| `0x4001d91c` | `2045 e78c ed88` | `jsr tco_dots` (`0x40152d82`), since §8.2 |
| `0x40152d38` | the mask's bytes | `pos`, `tco_step`, `tco_dots`, then `tco_order` at `0x40152daa` (178 bytes; 134 with the order at `0x40152d7e` in the first version) |

`python3 tools/gen_trig_cond_order.py --cycles model-cycles_OS1.13.syx [--check]` (m68k-elf binutils 2.47).

## 6. The proof in emulation

`tools/emu/test_trig_cond_order.py` runs the OS's own code, stock vs modified:

1. the writes (stock bytes, the mask, the vtable entry and its typeinfo, the order, no other tweak on these bytes,
   the ranges of §4 not written);
2. the method alone, as the image's vtable has it, on a TrigParameterSet built by the OS's constructor: Trig Cond,
   each code 0..63 × 25 steps (whole and fractional, ±0x7fff): stock `(code << 8) + delta` clamped, modified
   `ORDER[position + (delta >> 8)] << 8`; without a condition, out of range and every other descriptor 0..79 at
   random: the stock answer; registers and stack;
3. the knob step for a held trig from `0x4001e268` down to the condition byte, through the OS's getter and setter
   (stand-ins for the track's data and the view's `+0x80`): the byte moves as in 2, nothing else in the data, the
   track told once, as stock; without a condition and at step 64, as stock;
4. turning from FILL 63 clicks each way, printed with the names the OS shows.

Result `[FAIT en émulation]`, 2026-10-30, the tweak alone, in the maintainer's terminal (Unicorn stops with SIGILL in
the session that wrote it): **ALL OK**, every line of 1 to 4. The method: 64 codes × 25 steps as modelled, the
other descriptors (3 160 values and deltas) and the trigs without a condition as stock. The knob step: 4 800 turns
each, stock and modified, as modelled, no other byte of the data, the track told once. Turning from FILL:

```
stock   : FILL !FILL PRE !PRE NEI !NEI 1st !1st 1% 2% … 98% 99% 1:2 2:2 1:3 … 7:8 8:8
modified: FILL !FILL PRE !PRE NEI !NEI 1st !1st 1:2 2:2 1:3 … 7:8 8:8 1% 2% … 98% 99%
```

## 7. What is left

- `[À FAIRE]` The proof with the other mods (`--with …`); the bytes it relies on are written by no other tweak (§4).
- `[À FAIRE]` The machine: hold a trig, turn CHANCE right from the start: FILL … !1st, then 1:2, 2:2, 1:3 … 8:8, then
  1% … 99%, and back to the left; turn fast; FUNC + CHANCE; a condition set with the stock OS shows and plays the
  same; two trigs held at once each move in the new order; Trig Length and Nudge as before.

## 8. Tried on the machine (2026-10-30): the five dots

The maintainer flashed the first version alone (`build/trig-cond-order/`, MAIN OS `43562797…`). The order was right;
the five dots under the value were not: "die 5 dots unterhalb der wertanzeige zeigen nicht mehr korrekt an, wo man
sich im regler befindet … der dot springt wild rum, der ist irgendwie noch an die alte reihenfolge gebunden". The dots
are a scroll bar of the list; with regular use one knows which dot a condition sits under, without counting.

### 8.1 Diagnosis `[FAIT]`

- The window a knob turn opens is ParameterPageView's vtable `+0x90`, `0x4001d818(view, bitmap, desc, value, flag,
  1)` (notes/55 §8.1), called at `0x4001e634` with the held trig's value (`fp-52`, the code `<< 8`). It draws the
  name (the set's `+0x44`), then, for any descriptor but 18, the dots, then the value (`+0x40`, else the formatter
  `+0x3c`).
- The dots, `0x4001d8ee..0x4001d98c`: `d7 = (value − min) · 5 / (max − min + 1)` (`divs.l`, `0x4001d944`), min and
  max from the descriptor table; five dots at x = 76 + 9 k, y 0x17..0x1b, dot `d7` drawn by `0x40070efc`, the
  others by `0x40070c4e`. For Trig Cond: `code · 1280 / 16 129`, about 12,6 codes a dot.
- So the dots went by the code: with the new order, the lit dot jumped from 0 to 2 at 1:2 (code 29), then back to
  0 at 1 % (code 8). The tweak had changed the knob, not this second reader of the value.

### 8.2 The fix

- A detour at `0x4001d91c`: `movea.l d5,a0 ; lsl.l #3,d4 ; lsl.l #6,d0` (`2045 e78c ed88`, the value loaded for the
  dots and two shifts of the descriptor's offset) → `jsr tco_dots`. No branch lands inside these 6 bytes (the
  function's targets are `0x4001d8f8`, `0x4001d8fa`, `0x4001d918`, `0x4001d91a`, `0x4001d948`, `0x4001d966`,
  `0x4001d97a`, `0x4001d86c`, `0x4001d990`, `0x4001d8ee`).
- `tco_dots` replays the three instructions; for descriptor 19 and a code 0..63, `a0` = the code's position `<< 8`
  instead (the search `pos`, shared with `tco_step`); `d0` and `d1` are saved around it. Everything else as stock,
  and the value's text still comes from the code.
- With the new order the dots read (dot 1 to 5): FILL … !1st 1:2 … 3:3 / 1:4 … 4:6 / 5:6 … 3:8 / 4:8 … 8:8 1 % … 25 % /
  33 % … 99 %; stock: FILL … 9 % / 13 % … 94 % / 96 % … 4:4 / 1:5 … 2:7 / 3:7 … 8:8.
- Size: 178 bytes in the mask (`pos` 18, `tco_step` 56, `tco_dots` 40, the order 64), of 192. MAIN OS alone
  `018690231f705e49422a5032a36d1685637db2dd682c65942277759d7da351f1`.
- Model-TG rewrites the window's vtable entry (`0x401005bc`, to `0x401ba49c` in its payload); whether its window
  calls the stock one for Trig Cond is not read `[HYP]`. Model-TG is not offered by model27; the tweaks it would go
  with are checked by `check_overlaps.py` as before (no shared byte).
- The proof's section 5 runs the window's own code from `0x4001d8ee` to `0x4001d98c`, the two dot draws intercepted:
  Trig Cond's 64 codes, stock and modified as above, the lit dot never back while the knob goes forward; no
  condition, out of range and the other descriptors' values as stock, registers too. Run by the maintainer the same
  day, the tweak alone: **ALL OK** (sections 1 to 5) `[FAIT en émulation]`. The device: §9.

## 9. Tested on the machine (2026-10-30)

The maintainer flashed the second build, the tweak alone (`build/trig-cond-order/model-cycles_OS1.13-trig-cond-order.syx`,
MAIN OS `018690231f705e49422a5032a36d1685637db2dd682c65942277759d7da351f1`), with the checks of §7 and the dots
moving from 1 to 5 without going back: « Passt ». Still open from §7: the proof with the other mods.

## 10. In the web flasher (2026-10-30, release 0.18)

The maintainer asked for a card. `trig-cond-order` joins `OFFERED` (`tools/gen_flasher_tweaks.py`, section `seq`, no
credit, `"status": "experimental"` until flashed from the page), its texts in `docs/flasher/app.js` (en, fr), the
guide's section 6 (the ones after it renumbered), release 0.18, the stamp `2026-10-30-02`, the README. `REF_MAINOS`
now holds 16 combinations: the card alone gives `018690231f…`, the MAIN OS tested from the command line (§9); with
every other card `6788885f…`. No exclusion with the four other cards (no shared byte, no claim). `[À FAIRE]` flash it
from the page, then `tested`.
