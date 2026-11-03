# 78 — A CPU page: how much of the Model:Cycles' time the audio takes

The maintainer's request (2026-11-03), after the build of every card of release 0.35 slowed the screen down on a
dense pattern (§1): « Eigene Seite wie TG », a page of its own as Model-TG has one, showing the load. Model-TG's
System page (TinyGregAudio, MIT, `tweaks/model-cycles_OS1.13/LICENSE-Model-TG`) is the model for the page's mechanics
(§2). This note is the plan; step 1, the measure, is built (§8). Addresses: load addresses of the Model:Cycles OS 1.13's main section
(base `0x40000400`).

## In short (the plan)

- **Where:** SETTINGS, in the device configuration list (USB mode, LCD, LED, Contrast), one more row that opens the
  page. Return or SETTINGS closes it.
- **What:** the audio's share of the CPU over the last half second, its worst block since the page opened, a bar.
  Later, if the maintainer wants it: the Track FX' and the effect slots' shares, and each track's.
- **How it is measured:** a probe around the OS's call of its audio function (voices, mix, effects), timed with the
  DMA timer 0, as `syntakt-meter` did (notes/23 §5): busy time over the time between two blocks.
- **How the page is built:** as Model-TG builds its pages: the stock machine-select page object with its vtables
  pointed at a private copy in which the key handler, the render, the encoder and the destructors are ours, presented
  as the stock opener presents a page.
- **Open:** how the page redraws itself twice a second (§4.4), and whether it is a builder part or a tweak (§4.5): both settled, §8 and §10.

## 1. Why (2026-11-03)

- The maintainer flashed `build/smpfilter-0.4/every-card/` (every card of the page, MAIN OS `2fbe6c3f…`) and played
  pattern A05, a dense one, with Crush on all six tracks, a SAMPLE track and Control All. The screen became very slow,
  also with the SAMPLE track not selected; the sound kept playing without dropouts. With every Track FX at OFF, the same
  pattern and the SAMPLE track: fluid. RETRIG + PITCH then turned the track's PITCH instead of stepping the Track FX
  type; without the load it works. `fl_knob` (fltslot) falls back to the stock answer only when RETRIG does not read
  as held, or FUNC, TRACK, LFO or a trig is held as well `[FAIT]`; `[HYP]` under that load the key's hold reaches the
  lookup late.
- notes/25 §1 measured on the machine: the mix and effects about 30 % of a block, each sounding stock voice about 8 %,
  and the interface short of time above about 85 % on average. A dense pattern with six sounding tracks is near 80 %
  before any mod; six Crush add at most 5.9 % by the proof's count, about twice that on the machine (notes/72 §18).
- Twice the screen `EXCEPTION V03-M0-P24300000` came up, with the screen mirror Elek_View running (aveycole's fork of
  BlueSGL's page: the debug SysEx screen dump `F0 00 20 3C 10 00 … 04 F7`, up to 20 times a second). Decoded from the
  OS's handler `0x40078ce2` `[FAIT]`: V is the vector (3, address error), M the low nibble of SR's high byte (the
  interrupt mask, 0: not in an interrupt), P the PC, and the 18 numbers the stack after the exception frame. `[HYP]`
  The jump target and several stack values hold only bytes under `0x80` (`24 30 00 00`, `00 24 00 28`, `24 24 24 24`),
  as MIDI data do: a SysEx buffer overrun under load. Not seen again without the tool; not shown to be the cause.
  The second screen's stack holds `0x400594ae`, the return address after `jsr 0x40053330` in the audio path.

## 2. Model-TG's System page `[FAIT]` (its `src/model_tg.s`)

| Part | What it does |
|---|---|
| Measure | `isr_prof` replaces the audio interrupt's vector (`0x400002fc` → `0x40058c5e`) and stamps DTIM2's free-running counter (`0xfc07800c`) at the interrupt's entry; `prof_end`, called once the final mix is written, stamps it again. Busy time over the time between block starts is the share; also the worst block and the share of each track (its voice-loop hook) |
| Row | `cfg_hook` at `0x40032aee`, the end of the device configuration's constructor (`DeviceSettingsMenuView`, ctor `0x40032726`, the menu in `a2`): two rows added with `lm_add_row(menu, {label, value, turn, press})`, then the replaced `moveml` and `jmp 0x40032af4` |
| Page | `mm_open`: `operator new(0xd0)`, the stock machine-select constructor `0x400a22b0`, the object's two first vtable pointers set to a private copy of its vtable group `0x40117918..0x401179c8` with the destructors (`+0x00`, `+0x04` of the primary table: `0x400f43ca`, `0x400f4486`), key handler (`+0x08`, `0x400a292c`), render (`+0x10`, `0x400a24ca`) and encoder (`+0x44`, `0x400a28b4`; `0x400a2926` in the `+4` base) replaced; a reference holder (vtable `0x401000c4`) as the stock opener `0x4001ca40` builds it; presented with `0x4007700e` |
| Redraw | `sys_tick`, from its tick chain, every 750 blocks: `0x40076082(page)` |
| Close | Return (code 12, as the machine page closes), PRESET or SETTINGS on a fresh press |

All those addresses are function starts or the vtable group in our OS 1.13 `[FAIT]` (read in the disassembly; the
vtable group read with the base `0x40000400`).

## 3. The OS points

| Address | What is there | Use |
|---|---|---|
| `0x40059382` | `jsr 0x4005979e`, the interrupt's call of the audio function `[FAIT]` | the probe (notes/23 §5) |
| `0xfc07000c` | DMA timer 0, 135,168 MHz, 90 112 ticks a block `[FAIT]` (notes/23 §5, fltslot's `fl_measure`) | the clock |
| `0x40032aee` | `moveml %sp@(24),%d2-%d6/%a2-%fp`, then `lea %sp@(128),%sp; rts` at `0x40032af4` `[FAIT]` | the row |
| `0x400a22b0`, `0x40117918` | the machine-select page's constructor and vtable group `[FAIT]` | the page |
| `0x4007700e`, `0x401000c4` | present, the holder's vtable (from Model-TG) | opening |
| `0x40076082` | a view's redraw request (from Model-TG, `[À VÉRIFIER]`) | redraw |
| `0x40070dea`, `0x40070f6e`, `0x40071a04` | fill and box, text (One-Shot's views use them) | drawing |
| `0x400075f0` | `jsr 0x40076be4`, the screen's tick, taken by SAMPLE and by the dispatch part `[FAIT]` | redraw, §4.4 |

## 4. Design

### 4.1 Measure

The probe keeps the return address, reads the timer, calls the audio function with the stack unchanged, reads the
timer again. Per block: busy ticks and the period since the last block's start. Over a window of 750 blocks (0,5 s):
average = Σ busy / Σ period, and the worst block; a second worst block since the page opened. About 20 instructions a
block. Everything the interrupt does outside the audio function is not counted (`[À VÉRIFIER]` how much: Model-TG
counts from the interrupt's entry).

### 4.2 The page (128 × 64)

- **CPU** and the average in %, large, with a bar across the screen; a mark at 85 % (notes/25: the interface is short
  of time above it).
- **PEAK** and the worst block since the page opened.
- Phase 2, if wanted: **TRACK FX** (fltslot already times itself, `fl_measure`) and **EFFECTS** (the slots, to time),
  as shares of the same block; phase 3: T1 … T6 as Model-TG's second page.

### 4.3 Opening and closing

SETTINGS → the device configuration list → the new row (label to choose, §7). Return or SETTINGS closes the page; the
sequencer keeps running behind it.

### 4.4 Redraw `[À DÉCIDER]`

The page has to redraw itself twice a second. Two ways:
- **A, the view's own periodic method**, if the view stack calls one for the top view each frame (the knob view's
  popup counts down in its vtable's `+0x2c`, `0x4001efaa`; the machine-select page has a stub there, `0x40075f2e`,
  `rts`). To check in emulation; no hook outside the page then.
- **B, the screen's tick** (`0x400075f0`), as SAMPLE's loader runs; two packages taking it go through the dispatch
  part (notes/63 §4). This makes the page a builder part.

### 4.5 Packaging `[À DÉCIDER]`

- **A builder part** (like `fltslot`, `fxslot`): compose.py adds it when its card is ticked, it can share the tick
  through the dispatch part, its claims are computed with the packages'. The web flasher composes it in the page.
- **A tweak with its own generator**, code in a freed sprite mask: possible only if redraw way A works (no tick).
- The Cycles Mod Standard is not touched either way.

### 4.6 Conflicts

Model-TG takes the same row point and its own probe; `syntakt-meter` and the governor (Syntakt engines) take
`0x40059382`. None of them is offered (`OFFERED` in `gen_flasher_tweaks.py`); the claims declare the points.

### 4.7 Credit

The page's mechanics and the row builder follow Model-TG's (MIT): its license next to the code, a line in
`THIRD-PARTY-NOTICES.md`, the card's credit.

## 5. Proof (plan)

On the OS's own code (Unicorn), with a simulated timer:
- the probe: the audio output bit for bit as without it, the arguments, stack and registers the audio function sees
  unchanged, known blocks give known shares (as `test_meter.py`);
- the device configuration list: built by its constructor, it has the new row after the stock ones;
- the row's press: one page presented, its vtables the private copy, the stock entries everywhere else;
- the render: the page's pixels for known values (the views' harness, `test_views.py`);
- closing: the page gone, the next opening works;
- redraw: twice a second while the page is up, never when it is not.

## 6. Steps

1. The probe and the measure, proven (no display yet).
2. The row and a static page, proven; tried on the machine.
3. The redraw and the live values; the card (experimental), the guide, a release.
4. If wanted: Track FX and effects, then each track.

## 7. Decisions (2026-11-03)

The maintainer chose:
- the row's label **CPU**;
- the first version shows the total, the peak **and the Track FX' and the effect slots' shares** (phase 2 of §4.2
  moves into step 1);
- **a card of its own** in the flasher (experimental until their test).

What follows for the design: the page has to read what `fltslot` and `fxslot` measure, whose data blocks the composer
places per build, so the page is best a **builder part** (§4.5), placed by compose.py next to them, and its redraw
takes the screen's tick (§4.4 B) chained in front of whatever takes it in that build (SAMPLE's tick, the dispatch part
or the stock `0x40076be4`), as the shortcut layer chains SAMPLE's record wrapper. `fxslot` needs a timer of its own,
as `fltslot` has (`fl_measure`). To confirm while building step 1.

## 8. Step 1: the measure (2026-11-03)

Built, nothing shown yet. A **builder part**, as §7 expected: `tools/machines/cpu/` (`part.json`, `cpu.c`, `entries.S`,
`cpu.o` built by `tools/gen_parts.py`), added by `compose.py --cpu` (`compose(img, ids, cpu=True)`), also without any
package (the tweak's id is then `cpu`, else the packages' ids and `+cpu`). It is placed after the other parts, whose
measures it reads; adding it to a build changes nothing else but the probe's write and the payload's boot stub
(`0x4016cae8`), and the payload holds the same parts at the same places plus the page's `[FAIT]` (`test_cpu.py` §1).

**The probe** (`cpu_probe`, jsr from `0x40059382`): the return address goes to the data block, so that the audio
function sees the stack as from the stock call (syntakt-meter's way, notes/23 §5); the timer read before and after,
then `cpu_block(busy)`; d0 kept. 13 instructions; `cpu_block` 21 to 29 a block, 53 at a window's end (counted on the
compiled code with `_scratch/cfemu`): about 40 instructions a block, 0.04 % of one.

**The share**: busy ticks over the **nominal block** (90 112 ticks), not over the measured period as §4.1 said: the
interrupt runs once per codec block, the window is 750 blocks, and the shares then add up with the Track FX' (fltslot
counts the same way). Over a window: average = Σ busy / 67 584 (750 × 90 112 / 1000) in tenths of a percent, the
window's dearest block, and the dearest block since the counter was last cleared (`top`, for PEAK: the page clears it
when it opens, step 2). A block counts at most 46 blocks (`0x400000` ticks): no overflow. `windows` counts the windows
ended, for the redraw.

**The Track FX' share**: fltslot's last average (`avg_t`, its own window of 750 blocks, out of step with the page's by
less than 0.5 s); fltslot is unchanged. **The effect slots' share**: fxslot 0.7 adds the ticks of each slot's run
(`fx_run`, the chosen effect or the stock one, with a switch's block of silence and reset) to a counter from boot
(`busy`, data block +1180, 1184 bytes now); the page takes its difference over its window. A slot without an effect in
the build keeps its stock call and is not counted: the share is that of the slots that hold model27 effects. The
composer writes both addresses into the page's data block (`fl_avg`, `fx_busy`), 0 when the build has not that part.

fxslot 0.7 costs 6 instructions more a call (5 without a playing pattern, 7 in the block of a switch), from the
disassembly: the effect is no longer a tail call. Its declared overhead in `part.json` is set to that prediction
(delay 87 / 93 / 206, reverb 86 / 92 / 204 for stock / effect / switch); `test_fxslot.py` §6 counted exactly these
in the maintainer's run (2026-11-03, ALL OK on its nine selections, `build/fx-cost.json`) `[FAIT]`. The effect builds (`39-digidelay.json`, `70-pots.json`), `tweaks.js`,
`REF_MAINOS` / `REF_MODS` and `REGISTRY.md` regenerated for it.

**Proof**: `tools/emu/test_cpu.py`: the build and the data block (`--dry`, run here: ALL OK); start-up; the probe with a
stand-in audio function (its argument and stack as from the stock call, d0, d2-d7/a2-a6); the window (known blocks give
known shares, the Track FX' and the effects', the counter's wrap, the top cleared, the clamp: checked first on the
compiled code with cfemu); the whole audio interrupt, block for block, without and with the page, Crush on three
tracks and POTS for a while, the timer simulated as the count of instructions outside the page's code: the same bits
everywhere outside the page, its busy each block the audio function's instruction count, fxslot's and fltslot's ticks
inside it. The maintainer's run (2026-11-03, Unicorn does not run in the agent's sandbox): ALL OK on the five
selections `[FAIT]`; the audio function took 71 411 to 84 121 instructions a block in those scenes.

Still open for step 2 and 3: the row (`cfg_hook`), the page, the redraw (§4.4: the screen's tick, chained); the card,
its generator and tweak file (as a package's), claims (a view), the guide, the release (0.37 if Ring's 0.36 lands
first), Model-TG's credit with the page's code.

## 9. Step 2: the row and a static page (2026-11-03)

Built in the same part (`cpu` 0.2), as Model-TG builds its System page (§2), its code followed with its MIT notice
(`tools/machines/cpu/LICENSE`):
- **The row**: `jmp cpu_cfg` at `0x40032aee`; `cpu_add_row` is Model-TG's `lm_add_row` unchanged (the closures'
  managers `0x4002f136`, `0x4002f188`, the item `0x400734b0`, added with `0x40072ce6`); the label `CPU` (`cpu_lab`,
  Model-TG's `gm_lab`), no value (`cpu_nop`), the press `cpu_open`.
- **The page** (`cpu_open`, C): the stock machine-select page, its first two vtable pointers at a private copy of the
  group in the data block (now 228 bytes: the page pointer at +48, the copy at +52), presented as Model-TG presents it
  (`0x400d0974() + 64`, a holder `{0x401000c4, 1, 1, page}`). Ours in the copy: the destructors (forget the page, then
  the stock ones), **also the +4 base's two destructor thunks** (`0x400f447c`, `0x400f44c0`, which go to the stock
  destructor directly: Model-TG leaves them stock), the key handler, the render, the encoder handler and its thunk.
- **Keys**: Return closes the page (as the stock machine page, `0x400a292c`), every other key goes to the stock view's
  dispatch (`0x40075f3c`), as Model-TG passes the keys it does not take. Unlike Model-TG's page, PRESET and SETTINGS do
  not close it: Model-TG needs a key hook of its own (`kh_mod`) to swallow the SETTINGS release after such a close.
  **Knobs**: DATA's turn does nothing (on the machine page it changes the machine), the others go to the base
  (`0x4006fb90`), as on the stock page.
- **The render** (C): the whole screen; the text by the OS in its small font (`0x40140ab0`, as REF2's views), the
  lines' top rows 1, 22, 33, 44: CPU and the average, PEAK (the top: until step 3 the dearest block since boot, since
  nothing clears it before the page can redraw itself), TRACK FX and EFFECTS (`--` without that part); the bar rows
  12..16, x 2..125, filled from x 3 (122 pixels at 100 %, capped), the mark at 85 % at x 106, rows 10..11 and 17..18.
- No claim: the page is not one of the views of the claims' vocabulary (main, knob, note); the row's site is a byte
  conflict with Model-TG (computed).

Checked on the compiled code with `_scratch/cfemu` and the OS's calls stubbed: the render's texts (positions, flags,
`72.3%`, `--`) and the bar, the key and encoder handlers, `cpu_open` (refusals, the copy, present's pair and holder).
The proof, `test_cpu.py` §6 to §8: the device configuration list's own constructor with the row, the page's opening,
destructors, keys and knobs, the render into the OS's own Bitmap: the maintainer's run on crush,pots (2026-11-03) ALL
OK `[FAIT]`, the page drawn as planned (CPU 72.3%, PEAK 85.1%, TRACK FX 12.0%, EFFECTS 8.5%, the bar and its mark).
Then on the machine: `build/cpu-0.2/model-cycles_OS1.13-crush+pots+cpu.syx`, MAIN OS `7773846a…`: the row CPU at the
list's end, the page with its four lines and the bar, Return back to the list, the page again on the next press: the
maintainer, 2026-11-03, « Passt » `[FAIT]`.

## 10. Step 3: the redraw, the card, the release (2026-11-03)

- **The redraw**, §4.4's way A after all: the OS calls the method +0x2c of every view of its view stack on a timer
  (`0x40005970` → `0x400778e2`, which walks the screen's list at +20 from its last view to its first; registered at
  `0x40006ec6` with 30, as the screen's draw `0x4000768a`) `[FAIT]` (the disassembly); the knob view counts its popup
  down there (`0x4001efaa`), the machine-select page's is an empty `rts` (`0x40075f2e`). The page's is `cpu_tick`: a
  redraw (`0x40076082`) when `windows` has moved since the last (`drawn`, data block +46), so twice a second while the
  page is up and never when it is not. No hook on the screen's tick: nothing to chain with SAMPLE's or the dispatch
  part's. The page's opening clears the top with the interrupts masked (PEAK from then) and notes `windows`.
- **Packaging**: the part `cpu` 0.3; its tweak alone `78-cpu.json` (`tools/gen_cpu.py`), whose conflicts give the
  card's excludes (none among the offered cards); the other composed tweaks now name `cpu` among their conflicts (the
  same payload), as they name each other. A card of a new kind, `"part": "cpu"` in `gen_flasher_tweaks.py`: composed
  with the machine, effect and Track FX cards into one tweak, its id last (`cpu`, `sampler+cpu`, …); `composer.js`
  has the twin (`cpuLayer`, `compose(…, { cpu })`), `webcompose_check.sh` compares five selections with it,
  `ref_mainos.py` composes every set with and without it (REF_MODS 514 entries, REF_MAINOS 79), `webflash_smoke.js`
  ticks it alone and with others. Guide section 14, release 0.37 (Ring's worktree holds 0.36), stamp `2026-11-03-04`.
- **Proof** (`test_cpu.py` §7): the copy's ninth entry, the periodic method: a redraw once a window has ended, none
  otherwise, and the OS's own pass `0x400778e2` over a screen holding the page calls it; the top cleared at the
  opening. Checked first on the compiled code with `_scratch/cfemu` (the opening, the method). The maintainer's run on
  the five selections (2026-11-03): ALL OK `[FAIT]`. Then on the machine,
  `build/cpu-0.3/model-cycles_OS1.13-pots+crush+cpu.syx`, MAIN OS `49a0e74a…` (the page's build of POTS, Crush and the
  CPU page): CPU and the bar moving about twice a second while a pattern plays, falling when it stops, PEAK never
  under CPU and starting again at the next opening: the maintainer, 2026-11-03, « Passt » `[FAIT]`. The card stays
  experimental until it is flashed from the page.
