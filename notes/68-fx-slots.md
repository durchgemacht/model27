# 68 — Effects like machines: the delay and reverb slots (plan)

**Status: plan and code reading, 2026-10-26. Nothing built, nothing proven in emulation.** The maintainer's goal,
2026-10-26: « ziel ist, das man effekte wie machines auswählen kann und auf dem device auswählen kann, welcher aktiv
ist » — effects are ticked in the flasher like machines, and the device chooses which one runs.

The occasion is [PPPCCC's Model:Cycles 1.13 Mods](https://github.com/gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods)
(MIT, v1.0.0): Chorus I/II, Phaser and RAZR on the reverb slot, Digital, VIBDEL and CHODEL on the delay slot, chosen
with TRACK + Reverb Size / Delay Time. They are a first draft and an orientation, not the shape of this design (§6).

Addresses: VA of the OS 1.13 MAIN OS.

Sources of the facts marked `[FAIT]`: the disassembly of the official MAIN OS 1.13 (section 3, SHA-256 `cc99d4f0…`):
`0x400567ba..0x40056a70` (the mixer up to its delay and reverb), `0x40057488..0x40057560` (the delay's entry),
`0x400579c4..0x40057a60` (the reverb's entry), `0x400573fa`, `0x40057942`, `0x4005802e..0x400580a0`,
`0x4005979e..0x40059880` (the block); [67 §3](67-usb-audio-in.md), [35 §5](35-glitches-usb-multipiste.md),
[31](31-model-tg.md).

## 0. Short answer

| | State |
|---|---|
| Delay and reverb are two calls in the mixer with the same signature, `fx(out, in, params)`, one stereo block of 32 frames each | `[FAIT]` (§1) |
| One 6-byte `jsr` per slot is enough to put a table of effects there, the stock effect as entry 0 | design (§2) |
| Their memory (delay line, reverb lines) is written by DMA every block, whatever the slot plays | `[FAIT]` (§1.3) |
| What the four FX parameters mean in the parameter block, where they are saved, how their names are drawn | `[À FAIRE]` (§5, F0) |
| Model-TG takes the same calls | `[FAIT]` by the bytes (§1.4) |

## 1. What the OS does `[FAIT]`

### 1.1 The calls

The block `0x4005979e` gets the smoothed parameter block **P** from `0x40058474` (its argument: the first word of the
block's own argument **B**) and passes it to the mixer as its second argument (`0x40059872`: `0x400567ba(out, P)`).
P holds six tracks of 66 bytes, then the effects' words. In the mixer (`a3` = P):

| Where | What |
|---|---|
| `0x400567d8` | `0x4005802e(P)`: sets up the reverb lines' read DMA for this block (§1.3) |
| `0x4005694a..0x40056978` | the delay send of the six tracks into the stereo bus `0x8000b990` (`0x40056716`, gains `0x40a78bd0` / `…bb8`) |
| `0x4005697e..0x4005698a` | waits for bit 4 of `0xfc0453de` to clear (an eDMA status, the delay line's read, `[HYP]`) |
| `0x4005698c..0x4005699c` | **delay**: `jsr 0x40057488(0x8000ba90, 0x8000b990, P + 428)` |
| `0x400569a2` | `MACSR = 0xa0` |
| `0x400569cc..0x40056a1a` | the delay's return into the bus with its reverb share, the reverb send of the six tracks (`0x40056698`, gains `0x40a78b9c` / `…b80`) |
| `0x40056a1c..0x40056a2c` | **reverb**: `jsr 0x400579c4(0x8000bb90, 0x8000b990, P + 432)` |
| `0x40056a36` | `0x40057942()`: the reverb lines' DMA for the next block (§1.3) |
| `0x40056a3c` | `0x400573fa()`: the delay line's write DMA (§1.3) |
| `0x40056a42` | `MACSR = 0xa0`, then the returns into track slots 6 and 7 and the main mix ([67 §3](67-usb-audio-in.md)) |

On the stack at the call: return address, `out`, `in`, `params`. `in` and `out` are 32 frames of stereo, interleaved
32-bit (L at `+0`, R at `+4`), 256 bytes, in SRAM. Both functions save `d2–d7/a2–a6` with `movem` and use the EMAC;
the mixer sets `MACSR` again after each.

### 1.2 The parameters

| Bytes of P | Read by | As |
|---|---|---|
| `+428..+431` | the delay (`a0` = P + 428) | the word at `+430`, clamped to `0x7f00` (`0x40057494`) |
| `+432..+435` | the reverb (`a0` = P + 432) | the byte at `+432` (`0x40057a1a`) and the word at `+434` (`0x400579d0`) |

When `B + 36` is not 0, the block zeroes the six track words `+50` and the words `+430` and `+432`
(`0x400597e4..0x40059806`), and writes `0x7f00` or 0 to `0x4013e77c` (`[HYP]`: a mute of the output; not read).
Which kit parameter becomes which word, and where the delay time comes from (`0x400581b4`, [38](38-tempo-546-bpm.md)),
is not read yet. *Read in F0: §8.1.*

### 1.3 The memory of the effects

| Range | Owner | How it is reached |
|---|---|---|
| `0x42400000–0x42800000` (uncached `0x4a400000…`) | the delay line: 512 Ki frames of 8 bytes, 10.9 s | written by eDMA (TCD at `0xfc045540`) from the buffer `*0x8000b570`, index `0x8000b988` + 32 per block, wrapped at `0x7ffff` (`0x400573fa`) |
| `0x42340000–0x423d0000` | the reverb: 9 lines of 64 KB (`0x4a340000 + i · 0x10000`) | DMA descriptors at `0x8000a670…`, indices `0x8000a520…` (`0x40057942`) |
| `0x423d0000–0x423d8000` | the reverb: 8 lines of 4 KB (`0x4a3d0000 + i · 0x1000`) | descriptors at `0x8000a570…`, indices `0x8000b550…` (`0x40057942`, `0x4005802e`) |

These DMAs run in every block, from the mixer's own code, whether the stock effect runs or not. An effect that does
not call the stock one must leave this memory alone, or the slot must stop the DMA (not designed). The standard's
`memory.ram` starts at `0x42800000`, right after the delay line; the hole `0x423380b0–0x42340000` between the BSS
and the reverb lines holds lfo-plus (`0x4233f000`) and is what PPPCCC's effects use.

### 1.4 Who takes these places today

- **Model-TG** writes at `0x4005699f`, `0x40056a2f` and `0x40056a3d` (inside the three `jsr`), for its send effects
  that stop after 10.9 s of silence ([31](31-model-tg.md)). A slot and Model-TG exclude each other by the bytes.
- **PPPCCC** (not in this folder) replaces the delay call, the reverb call and the delay line's DMA call, chooses with
  a byte of the device settings (`0x404e9b5c`, `0x404e9b5d`), and renames the parameters by rewriting the OS's
  string pointers from its audio code.

## 2. The design: two slots, a table each

| | `machine` (today) | `fx.delay`, `fx.reverb` (proposed) |
|---|---|---|
| What a package gives | `update` and `render`, five descriptors | `process(out, in, params)` with the stock signature (§1.1), names and ranges of the slot's knobs |
| How many run | one per track | **one per slot**, the chosen one; the stock effect is entry 0 and always there |
| Where the builder writes | the moved tables | one 6-byte `jsr` per slot, to a dispatcher in a builder part, and its table |
| The choice | the sound's machine (`+38`), a number that is the place in the build (option C) | **a fixed effect id from the registry**, saved (§3); an id not in the build plays the stock effect |
| Composition rule | table | table |

Why a table and not a chain: in a slot, the effects replace each other. Effects in series (an insert chain on the
bus, a master effect after the mix) are other points, for later.

Why fixed ids and not option C: the choice is saved and read back by every build. A position in the build would
change meaning when another set of effects is ticked; an id does not, and an unknown id falls back to the stock effect.

**The dispatcher** (part `fxslot`, compiled once like the shortcut layer and the dispatchers of
[63 §11–§13](63-level-b4-shortcuts-dispatchers.md)): reads the slot's chosen id, finds its entry, jumps to it with the
stack unchanged; entry 0 is `0x40057488` or `0x400579c4`. A build without an effect package has no part and no write.

**The register contract** of a package: the stock one (§1.1): keep `d2–d7/a2–a6`; `MACSR`, `acc0–acc3` and
`d0–d1/a0–a1` are free (the mixer sets `MACSR` after the call). `[À FAIRE]`: whether the mixer reads an accumulator
after the call.

**Memory:** a package claims its own RAM (`memory.ram`, or the payload's variables). The delay and reverb lines stay
the stock effect's (§1.3).

**Cost:** per block, not per voice; the governor does not see it. The builder adds, per slot, the heaviest effect
ticked, not their sum. The device number comes from the load meter of [23](23-optimisation-charge.md).

## 3. Choosing on the device

A builder part `fxsel`, added when a build has an effect package, owns:
- the gesture that steps through the slot's effects (the ones ticked, in id order, the stock effect first), with a
  popup in the OS's style;
- the names and formatters of the slot's parameters, switched with the effect (a package gives them as a shortcut
  gives its own, [63](63-level-b4-shortcuts-dispatchers.md));
- where the choice is saved.

Two decisions for the maintainer:

| | Options |
|---|---|
| **Where the choice lives** | **per pattern**, with the effect's parameters, so a project sounds the same after loading (needs a free place in the pattern, `[À FAIRE]`; the pattern header has few bytes left, [42 §4](42-clavier-accords-diatoniques.md)); or **per device**, one choice for every project, as PPPCCC does (free bytes `0x404e9b63..0x404e9c0f` outside the settings' checksum, Modded-Cycles notes/72) |
| **The gesture** | TRACK + Reverb Size / Delay Time, as PPPCCC (the stock meaning of TRACK on these knobs is not read: the effect parameters belong to the pattern, so Control All may do nothing there, `[À FAIRE]`; read in F0, §8.4: it edits as without TRACK); or a combination of the free list ([63 §15](63-level-b4-shortcuts-dispatchers.md)) |

**Decided 2026-10-26: one choice per device** (§7).

## 4. In the flasher

- One card per effect, in two groups, *Delay* and *Reverb*. The stock effect is not a card: it is always there.
- Ticking an effect adds the parts `fxslot` and `fxsel`; the card says how to choose it on the device.
- `excludes` come from the claims and the bytes as for the machines: Model-TG (§1.4) and whatever an effect claims.

## 5. Steps

| Step | Content | Done when |
|---|---|---|
| F0 | Read: the words of P for each kit parameter (`0x40058474`, the delay time `0x400581b4`), the interface objects and formatters of the FX parameters, the knob numbers of the FX page, the stock meaning of TRACK on them, `B + 36`, `*0x8000b570`, where the pattern saves the FX parameters and a free place there | a section of this note per question, `[FAIT]` or `[HYP]` |
| F1 | Part `fxslot` and a reference effect per slot (e.g. a dry pass and a simple chorus, MIT, ours); proof in Unicorn: without a package the image is stock; with one, entry 0 is bit for bit the stock effect, the reference matches its model | proofs ALL OK |
| F2 | Part `fxsel`: gesture, popup, names, the saved choice; proof: the key chain, the names, an unknown id plays the stock effect | proofs ALL OK |
| F3 | Composer and web flasher: the cards, the excludes, the cost per slot | `webcompose_check` |
| F4 | On the device, then the standard's draft 0.5: the two points, the effect id registry, the knob words of the FX page in the claims | maintainer's test |
| F5 | Invite PPPCCC's effects as packages (§6) | — |

**F0 done 2026-10-26** (§8).

## 6. What PPPCCC's effects would change to fit

- each effect a package: `process(out, in, params)` and its names, in a relocatable object placed in the payload,
  not in sprite masks; no switch, no encoder hook, no settings byte of its own (the parts do that);
- the delay effects keep their own delay memory, or a contract for the stock line is written first (§1.3);
- the patches that are not effects (Solo, Live mute, Hold to mute, Delay notes, Strum, Load meter, Grooves) stay
  tweaks on their own cards, without the chain that ties them to the effects today; Grooves' pattern bytes clash with
  Chord Keys ([42 §4](42-clavier-accords-diatoniques.md)) and need another place.

## 7. Decided (2026-10-26): one choice per device

The maintainer, 2026-10-26: « Pro Gerät, eine Wahl für alle Projekte (wie PPPCCC). » The choice of each slot is a
device setting, the same for every project; F0 no longer looks for a place in the pattern.

### 7.1 The settings block `[FAIT]`

Read in the official image (every 32-bit constant from `0x404e9b10` to `0x404e9c20`, and the defaults `0x400449ce`),
with Modded-Cycles notes/72 §1.2:

| Bytes | What |
|---|---|
| `0x404e9b10..0x404e9c1f` | the block the OS saves whole, 272 bytes (`0x404e9b04`, flash offset `0x78000`); `0x400449b8` writes it, `0x400449a8` reads it |
| `0x404e9b18..0x404e9b62` | under the checksum (`0x40044b4e`); the defaults `0x400449ce` clear `0x404e9b10 + 0x53` bytes and set the values |
| `0x404e9b5b..0x404e9b5e` | one reference each, in the defaults (`0x40044a96..0x40044aaa`: 1, 1, 0, 0); nothing else reads or writes them. PPPCCC keeps its choices there, through `0x40044b88` (copy and new checksum) |
| `0x404e9b63..0x404e9c0f` | no reference in the OS; Modded-Cycles 2.0 keeps its *Mod Settings* record at `0x404e9b80..0x404e9b8f`, PPPCCC its strum at `0x404e9b64` |
| `0x404e9c10`, `0x404e9c14` | inside the saved block, used by the OS (`0x4009572e`, `0x4007e94c`) |

### 7.2 The record (proposal)

- A record of its own outside the checksum, after the two above: `0x404e9b90`, 8 bytes, `'F' 'X'`, version, the delay
  slot's effect id, the reverb slot's, two bytes reserved, a check byte. A record that does not check (the official
  OS was there, a settings reset, another mod) means the stock effects; the defaults do not touch it.
- Ids are one byte, 0 is the stock effect; an id not in the build plays the stock effect and stays saved, so the
  same build with the effect ticked again plays it again.
- `fxsel` writes the record and calls `0x400449b8` once the choice settles (the popup closing), not at every detent.
  The choice is then saved at once; PPPCCC's "switch off once before you flash" is not needed (`[HYP]`: how long
  the flash write takes, and from which task it may run).
- A claim `saved` for the record in the part's `part.json`, so the registry shows it and a mod that takes these bytes
  clashes.
- `[HYP]`: the Model:Samples OS, after a cross-flash, reads the same flash block with its own meaning; the record is
  outside the checksum of either, to check in F0. *Answered in §8.5.*

## 8. F0: the parameters, their names, the knobs, TRACK, the Model:Samples (2026-10-26) `[FAIT]`

Sources: the descriptor table `0x4010dce0` (76 entries) read whole; the knob records' initializer
`0x400e0f40..0x400e1540`; the lookup `0x4001e814`; the interface objects' construction `0x400dfc10..0x400dfdc8` and the
formatter prototypes `0x400de2f0..0x400de770`; `ParameterPageView`'s encoder handler `0x4001f860..0x4001f8c0` and
`0x4005a5cc`; the delay time `0x400581ae`; the settings code of both OSes (Model:Cycles `0x40044af4..0x40044b86`,
`0x400ddef8`; Model:Samples MAIN OS 1.13, SHA-256 `a351392c…`, `0x40046008..0x4004609a`, `0x400d9bf2`).

### 8.1 The parameters and their words

| Descriptor | Name, long / short | Group (`+0`) | Slot | Range, default | CC | Word of P | Formatter (invoker) |
|---|---|---|---|---|---|---|---|
| 37 | Delay Time / TIME | `0xb`, "Delay" | 9 | 0..127, 23 | 85 | `+428` | `0x4004dfda` |
| 38 | Delay Fdbk / FDBK | `0xb` | 10 | 0..127, 32 | 86 | `+430` | `0x40045ab8` |
| 39 | Reverb Size / SIZE | `0xa`, "Reverb" | 11 | 0..127, 42 | 87 | `+432` | `0x40045a68` |
| 40 | Reverb Tone / TONE | `0xa` | 12 | 0..127, 64 | 88 | `+434` | `0x4004e00e` |
| 26 | Delay Send / DELS | 7 (every machine), "Amp" | k 20 | 0..127, 0 | 12 | per track | — |
| 27 | Reverb Send / REVS | 7 | k 21 | 0..127, 0 | 13 | per track | — |

- The CC is the high half of the descriptor's `+0x18`; groups `0xa` and `0xb` are the pattern's effects, not a sound's.
- The words: P + 410 + 2 · slot. `+428` is read by the delay time (`0x400581ae`: with the tempo `0x40149310`, capped at
  384 000), `+430` by the delay (`0x40057494`, clamped to `0x7f00`), the byte `+432` and the word `+434` by the reverb
  (`0x40057a1a`, `0x400579d0`, which splits `+434` at 16 383, Tone's centre). Size at `+432` and Tone at `+434` follow
  from the slots and that split, `[HYP]` strong; Time and Fdbk are `[FAIT]`.

### 8.2 The knobs

The six machine records (`0x40a7158c + 76 m`, built at `0x400e0f40..`) give the same entries for every machine
outside PITCH to CONTOUR. The lookup takes entry `knob − 2`; with FUNC, knobs 14 and 15 take entry `knob`:

| Knob | Parameter | FUNC + knob |
|---|---|---|
| 2–7 | PITCH, DECAY, COLOR, SHAPE, SWEEP, CONTOUR | fine adjust |
| 8 | Delay Send | fine adjust |
| 9 | Reverb Send | fine adjust |
| 10 | LFO Speed | fine adjust |
| 11 | Volume + Dist | fine adjust |
| 12 | Swing | fine adjust |
| 13 | Chance | fine adjust |
| **14** | **Reverb Size** | **Reverb Tone** |
| **15** | **Delay Time** | **Delay Fdbk** |

Entry 16 is Track Level (descriptor 9), not reached by the lookup (knob ≤ 15). With a trig held, Chance and Swing become
Trig Cond and Trig Nudge (`0x4001e91c..0x4001e92c`: descriptor 22 → 19, 23 → 18). PPPCCC's encoder numbers (8, 9, 12,
14, 15) agree.

### 8.3 Names and formatters

- **Names** are three pointers in the descriptor: long name `+0x2c`, group `+0x30`, short name `+0x34` (Delay Time
  `0x40129925` "Delay Time", `0x40129930` "Delay", `0x40129699` "TIME"; Reverb Size `0x40129946`, `0x40129952`,
  `0x4012968e`; the others in the same way). The table is in the OS's data, in RAM while it runs: an effect's names are
  these pointers rewritten, which is what PPPCCC does.
- **Formatters**: the interface objects `0x40a71754 + 100 · i` (i the descriptor) are built at boot
  (`0x400dfc10..`). The formatter is the `std::function` at `+0x14`, its invoker at `+0x20`, called by `0x4000a70e`
  ([47 §3.3](47-filtre-piste.md)); it is copied from four prototypes filled at `0x400de2f0..0x400de770`:
  `0x40a706e8` (Time), `0x40a70528` (Fdbk), `0x40a70538` (Size), `0x40a706b8` (Tone), whose invokers are in the
  table above. Switching a formatter is writing `+0x20`, as the track filter does; an object has one formatter, so
  `fxsel` holds the four objects (a claim).
- Not read: the special draw at `+0x2c` of these objects, and the popup at a knob turn.

### 8.4 TRACK on the effect knobs

- `ParameterPageView`'s encoder handler tests TRACK at `0x4001f886`. When it is held, it first calls
  `0x4005a5cc(descriptor)` (`0x4001f89a`), which answers yes for the groups 10 to 12 (Reverb, Delay; 12 is not used),
  and then jumps to `0x4001f92e`, the same place as without TRACK.
- **So TRACK + Reverb Size / Tone / Delay Time / Fdbk edits that parameter as without TRACK**: Control All leaves the
  pattern's effects out. TRACK held shows `TrackSelectionView` ([58 §2](58-control-all-config.md)); its release only
  closes that view: no menu, no save. TRACK is a safe modifier here (SETTINGS is not: its long press saves the
  project).
- A place for `fxsel`'s gesture: the call at `0x4001f89a`, reached only while TRACK is held, with the descriptor in
  `d3`; it costs nothing otherwise. F2 must find how the event ends there without the stock popup (PPPCCC drops the
  event at `0x400081b8` because a zero step opens the popup, `[HYP]`).
- In the claims: TRACK + knob 14 / 15 replaces "the knob edits as without TRACK"; the vocabulary has no words for knobs
  8 to 15 yet (`tools/claims.py`).

### 8.5 The settings block on the Model:Samples OS

- The Model:Samples OS 1.13 keeps the same block at `0x404f65cc`: `COKI`, the checksum at `+4` over `+8` for the length
  at `+12`, version 4 and length 67 written by its defaults as on the Cycles, storage object `0x404f65c0`, 272 bytes,
  flash offset `0x78000`.
- Every 32-bit constant into the block is the same in both OSes, offset by offset and count by count: `+0x00..+0x52`,
  `+0x100`, `+0x104`. Neither references `+0x53..+0xff`; both touch `+0x4b..+0x4e` only in their defaults.
- So after a cross-flash, either OS reads the other's block as its own, and the record at `+0x80` (Cycles
  `0x404e9b90`, Samples `0x404f664c`) is kept by both and read by neither: the `[HYP]` of §7.2 is answered. Not traced:
  an access through a base register and an offset outside the checksum code (which uses the stored length).
- A Model:Samples with the mods runs the Model:Cycles OS ([57](57-os-cycles-quelle-que-soit-la-machine.md)): the
  Cycles addresses apply.

### 8.6 Left for F1 and F2

- whether the mixer reads an accumulator after an effect's call (§2);
- the special draw and the popup of the effect parameters (§8.3);
- how the gesture's event ends without the popup (§8.4);
- `B + 36` (§1.2).

## 9. Decided (2026-10-26): the gesture

The maintainer, 2026-10-26: « TRACK + Reverb Size / Delay Time wählt den Effekt, wie bei PPPCCC. »

- **TRACK held + knob 14 (Reverb Size)** steps through the reverb slot's effects, **TRACK held + knob 15 (Delay
  Time)** through the delay slot's: the stock effect first, then the ticked effects in id order; left goes back.
- Only descriptors 39 and 37 take it. With FUNC as well, the knobs give Tone and Fdbk (§8.2), which `fxsel` leaves to
  the stock edit, so TRACK + FUNC + knob 14 / 15 still edits Tone and Fdbk.
- In the stock OS the combination edits the parameter as without TRACK (§8.4); the claim says so in `replaces`. The
  claims' vocabulary gets the two knobs (proposed words `REVERB` for 14 and `DELAY` for 15, with a note that FUNC
  turns them into Tone and Fdbk).
- Proposals for F2, not decided: a step needs a few detents in one direction (PPPCCC: 4, reset after 0.4 s, a change
  of direction or another knob), so that a slip does not change the effect; the popup shows the slot and the effect's
  name; the choice is saved when the popup closes (§7.2).
- Where: the call at `0x4001f89a` (§8.4), reached only while TRACK is held.

## 10. F1 built (2026-10-26)

### 10.1 What was built

- **The part `fxslot`** (`tools/machines/fxslot/`, MIT): `fxslot.S`, 74 bytes, assembled once by `tools/gen_parts.py`
  into `fxslot.o`; two entries, `fx_delay` and `fx_reverb`, the `jsr` targets of the mixer's two calls (§1.1). Each reads
  the slot's id from the record at `0x404e9b90` (magic `FX` and version 1 checked; the check byte of §7.2 is `fxsel`'s
  to write and test, F2), looks it up in its table and jumps there with the stack unchanged; id 0, a missing record and
  an id the build does not hold give entry 0, the stock effect. It uses d0, d1, a0, a1 and no stack. The data block
  after it, 136 bytes: for each slot (delay at +0, reverb at +68) the number of entries and up to 8 entries
  `{id, function}`, entry 0 `{0, stock}`.
- **`tools/compose.py`**: a package whose `uses` names `fx.delay` or `fx.reverb` is an effect: an id from 1 to 255, its
  `process` first in `build.roots`, no patch point, no point but its slot and `memory.ram`. It is laid out in the payload
  like an extension, nothing registered without an added machine; `fx_layer()` adds the part after the dispatchers,
  writes the `jsr` of each slot that has an effect and fills the tables; a slot without an effect keeps its stock call.
  Two effects with the same id are refused, and more than 7 in a slot. `docs/flasher/composer.js` does not know effects
  yet: that is F3.
- **Effect ids** (`part.json`, `ids`): 0 the stock effect, 1 to 239 the effects (given by the maintainer), 240 to 255 the
  references.
- **The reference effects**, never offered, MIT, their objects written by `tools/gen_refmachine.py` (no tweak in the
  folder yet: each composed tweak of the folder would gain a computed conflict; they come with F3):
  - **REFD** (`tools/machines/refdelay/`, id 254, order 37): an echo of 4 096 frames fed back with 2 · (Fdbk >> 8)
    / 256, saturated; 202 bytes of code, 32 772 bytes of variables;
  - **REFR** (`tools/machines/refreverb/`, id 255, order 38): a one-pole low-pass per channel, its shift 1 + (Size >> 4);
    116 bytes of code, 8 bytes of variables.
  - Orders 37 and 38 are provisional (the maintainer's to give).

### 10.2 The builds

| Selection | Writes | Added to the image | MAIN OS (SHA-256) |
|---|---|---|---|
| refdelay | 4: the boot hook `0x400004b2`, the stub's mask `0x4016cae8` and its sprite `0x400b1106`, `jsr fx_delay` at `0x4005699c` | 416 bytes | `c4ae8ecd…` |
| refreverb | 4: the same, `jsr fx_reverb` at `0x40056a2c` | 328 bytes | `a12e2458…` |
| refdelay, refreverb | 5 | 532 bytes | `6fd048f4…` |
| sampler, refdelay, refreverb | SAMPLE's and the two slots' | 38 636 bytes | `74db3ba0…` |

268 conflicts computed for an effect alone: Model-TG and model-tg-st (their writes in the same calls, §1.4) and every
tweak that runs a payload (the boot hook), as for any package.

### 10.3 Checks without emulation (2026-10-26)

- `gen_parts.py --check`, `gen_refmachine.py --check`, `claims.py --check --self-test` (ALL OK), `check_overlaps.py`
  (288 tweaks, ok), `registry.py --check`, `py_compile`, `test_compose.py --dry`, `webcompose_check.sh` (OK: the twin
  is unchanged and composes no effect yet).
- `test_fxslot.py --dry`: **ALL OK**, the sites of the four selections (the hooks, the writes, the tables).
- REFD and REFR against their models: the C compiled for the host and the proof's Python models, 400 blocks with
  full-scale input and Fdbk 127, identical.
- `gen_flasher_tweaks.py --check` fails in the working tree because of other uncommitted changes; on `HEAD` with F1's
  files alone it passes.

### 10.4 The proof, for the maintainer's terminal

`tools/emu/test_fxslot.py` (Unicorn stops with SIGILL in the agent's sandbox): for each of the four selections, the
start-up (the bootstrap's depacker, the boot hook), the sites, then a stock engine and the build's engine side by side,
block for block, through what the mixer does around the effects (`0x4005802e`, the delay, the reverb, `0x40057942`,
`0x400573fa`):

- with no record, another magic or version, id 0, an id the build does not hold or the other slot's id: the slots'
  returns and the whole SRAM are the stock OS's after every block;
- with the record choosing REFD / REFR: the return is the model's, bit for bit; the rest of the SRAM is the stock OS's
  (the stock effect's state left alone); back to id 0 the engines agree again; the effect again goes on from its state;
- the effects' SDRAM lines as the stock OS leaves them, every call keeping d2–d7/a2–a6 and the stack, no access outside
  memory.

```
python3 tools/emu/test_fxslot.py --cycles firmware/model-cycles_OS1.13.syx
```

### 10.5 The proof run (2026-10-26) `[FAIT en émulation]`

The maintainer, 2026-10-26, in their terminal: « test_fxslot.py ist bei mir durchgelaufen: ALL OK. » So, for refdelay,
refreverb, both, and SAMPLE with both, on the OS's own code: the start-up, the sites, the stock effects identical to
the stock OS's (returns and SRAM) for every form of the record that does not choose an effect, REFD and REFR identical
to their models when chosen with the stock effects' state left alone, back and forth, registers and stack kept, no
access outside memory. **F1 done**; not tried on the device (nothing to hear there before F2).

### 10.6 Left

- F2: `fxsel` (TRACK + Reverb Size / Delay Time, §9; the names and formatters, §8.3; the record with its check byte,
  §7.2).
- F3: `composer.js` and the flasher (cards, excludes, the effects' tweaks). F1 changes how a package is composed, so
  `compose.py` and `composer.js` go into one commit (`tools/AGENTS.md`): F1 waits for F3 before it is committed to
  `main`, or goes on a branch.
- The cost of an effect, measured (§2).

## 11. F2 built (2026-10-26): choosing on the device

The maintainer, 2026-10-26: « Mach mit F2 weiter: fxsel mit TRACK + Reverb Size / Delay Time, Namen und Formatter,
Record mit Prüfbyte. »

### 11.1 The handler, read for F2 `[FAIT]`

- In `ParameterPageView`'s encoder handler (`0x4001f4f0`), the popup is set up before the held keys are read: when the
  parameter or the track changes, `0x4001ddb2` keeps the six tracks' values (for an undo, not names), then
  `+560`/`+564`/`+556` = descriptor, track, knob, `+568` = 60 (the popup's time) and a redraw (`0x4001f708..0x4001f76e`).
  The popup reads the names and the formatter when it draws, so names switched later in the same event show at once
  (PPPCCC saw it on the device: "the parameter names change at once").
- The step is `0x4006f96a`'s answer; a zero step leaves at `0x4001f7fa`, before the held keys. The step, signed, 16 bits,
  is in `d4` (`0x4001f88e`) when TRACK is tested.
- `0x4001f96a` is the handler's end: `move.b d4,d0`, its registers from `fp`, `unlk`, `rts`. Control All ends there with
  `d4` = 0 (`0x4001f92a`), and so does a normal edit. Jumping there with `d4` = 0 ends the event with nothing edited,
  whatever the stack holds.
- `0x400456c8` is the OS's integer formatter: (storage, value, buffer) → `value >> 8` printed with `0x4012a9ea`.

### 11.2 What was built

- **One part, not two:** `fxsel` (§3) is no part of its own; `fxslot` 0.2 holds the audio side and the gesture, one
  data block for both (a part keeps its state in its data block: `gen_parts.py` refuses variables). F1's `fxslot.S`
  became `entries.S` (a source's object is named after its stem, and `fxslot.c` has the same one).
  - `tools/machines/fxslot/entries.S`: `fx_delay` and `fx_reverb` call `fx_run(slot, out, in, params)` and return to
    the mixer; `fx_track`, `jsr` from `0x4001f89a`, calls `fx_step(descriptor, step)` and ends the handler at
    `0x4001f96a` with `d4` = 0 when it took the event, else `jmp 0x4005a5cc` with its argument.
  - `tools/machines/fxslot/fxslot.c`: `fx_run`, `fx_step` and what they share. 1 408 bytes of code in all.
- **The data block** (1 180 bytes, then the strings): each slot's table, entries `{id, process, reset}`, entry 0 the
  stock effect; for each slot and entry the names (long and short of the slot's two parameters, the group) and the
  formatters; the two descriptor tables the names go into (the stock one, and `gs.DESCN` when the registrar moved it);
  a block of zeros and a scratch return (§11.3); the state: `ready`, `cur[2]`, `played[2]`, the detent count, the last
  slot, direction and time.
- **Start:** the first `fx_run` (the first audio block) or `fx_step` reads the record once: magic `FX`, version 1 and
  the check byte (0x5a + the sum of bytes 0–6) or nothing; `cur` = its ids, the slots named after them. After that the
  audio reads `cur` only.
- **The gesture:** descriptor 37 (TRACK + Delay Time) or 39 (TRACK + Reverb Size) on a slot that has an effect; any
  other descriptor, FUNC as well (38, 40), or a slot without an effect: the stock call, so TRACK keeps its stock meaning
  there. Four detents in one direction make a step; the count starts again after a change of direction, of slot, or
  0.4 s (54 067 200 ticks of the DMA timer 0 at `0xfc07000c`). A step moves one entry along the table, the stock
  effect first, and stops at the ends. An id the build does not hold counts as entry 0.
- **At each change:** the slot's two parameters named after the entry: long and short names and group in both
  descriptor tables, the formatter (`+0x20` of the interface objects 37/38 or 39/40); the record written with its
  check byte; `0x400449b8` saves the settings block at once (no "switch off before flashing").
- **Effects in their manifests** (`uses`): `params`, the slot's two parameters as `{long, short, format}` (≤ 15 and 5
  printable characters; `format`: none = the stock formatter, `"int"` = `0x400456c8`, or a symbol of the package);
  `name`, the group's text; `reset`, optional, a symbol in `build.roots`. REFD: "REFD Time" / TIME (stock formatter:
  note values) and "REFD Fdbk" / FDBK (int), `refd_reset` empties the line. REFR: "REFR Speed" / SPD (int) and
  "REFR Tone" / TONE (stock), `refr_reset` clears the filter.

### 11.3 When a slot changes effect

- **The stock effect that stops** gets one call with silence (input and parameters from the block of zeros, its return
  into the scratch block, unheard). Its lines are written by DMA from its own buffers every block whether it runs or
  not (§1.3); without that call, its last block would be written into its lines over and over and come back as a buzz
  when it plays again. For the delay, a silent input with Fdbk 0 writes silence. For the reverb, Size 0 still feeds
  back what its lines hold: `[HYP]` quiet enough, to hear on the device.
- **The effect that starts** gets its `reset`, so that it does not replay what it held when it last played.
- From one effect to another, only the reset; back to the stock effect, nothing (it goes on from its state).

### 11.4 The builds

| Selection | Writes | Added to the image | MAIN OS (SHA-256) |
|---|---|---|---|
| refdelay | 5: the boot (3), `jsr fx_delay` at `0x4005699c`, `jsr fx_track` at `0x4001f89a` | 2 856 bytes | `8e35b22b…` |
| refreverb | 5 | 2 764 bytes | `2bec0fc9…` |
| refdelay, refreverb | 6 | 3 032 bytes | `5d8409e9…` |
| sampler, refdelay, refreverb | SAMPLE's and the three | 41 136 bytes | `75c1cdad…` |

No tweak of the folder writes `0x4001f89a` (the conflicts computed are those of F1: 268 for an effect alone).

### 11.5 Checks without emulation (2026-10-26)

`gen_parts.py --check`, `gen_refmachine.py --check`, `claims.py --check --self-test`, `check_overlaps.py`,
`registry.py --check`, `py_compile`, `test_compose.py --dry`, `webcompose_check.sh` (the twin unchanged): green.
`test_fxslot.py --dry`: **ALL OK** (the sites, the tables, the names and formatters of every entry, the descriptor
tables). REFD and REFR against their models, compiled for the host: 400 blocks, identical.

### 11.6 The proof, for the maintainer's terminal

`tools/emu/test_fxslot.py`, rewritten for F2 (§10.4 is F1's): the start-up, the sites and the data block; the audio
side by side with the stock OS (the record in seven forms that choose nothing, then the effects: named at the first
block, the stock effect's block of silence mirrored, the effect reset and bit for bit its model, id 0 between, the
effect again from its reset); the gesture through `fx_track` with the handler's frame (other descriptors and slots
without an effect: the stock call; the detents, the pause, the ends against a model of the steps; names, formatters,
the record and one save at each change; an id the build does not hold).

```
python3 tools/emu/test_fxslot.py --cycles firmware/model-cycles_OS1.13.syx
```

### 11.7 The proof run (2026-10-26) `[FAIT en émulation]`

The maintainer, 2026-10-26, in their terminal: « test_fxslot.py (F2) ist bei mir durchgelaufen: ALL OK. » So, for
refdelay, refreverb, both, and SAMPLE with both, on the OS's own code: the sites and the data block; the start from
the record in every form, the names at the first block, the stock effect's block of silence, the resets, the effects
bit for bit, the stock OS's SRAM and lines everywhere else; the gesture as the handler calls it, against the model
of the steps, with the names, the formatters, the record and one save at each change. **F2 done in emulation**; not
tried on the device.

### 11.8 Left

- On the device (F4): the popup showing the effect's names as the step happens; the time `0x400449b8` takes in the
  middle of the knob's events; the reverb after its block of silence (§11.3); the sound of the slots.
- The claims: the part takes TRACK + knobs 14 and 15, the formatters of objects 37–40 and 8 saved bytes; the
  vocabulary of `tools/claims.py` has no words for knobs 8–15 yet (§8.4). With F3 and the standard's draft.
- F3: `composer.js`, the flasher, the effects' tweaks; F1 and F2 wait for it before `main` (§10.6).

### 11.9 For the device (F4), prepared 2026-10-26

The build: `python3 tools/compose.py --cycles firmware/model-cycles_OS1.13.syx --machines refdelay,refreverb --out
build/fx-f2` → `build/fx-f2/model-cycles_OS1.13-refdelay+refreverb.syx` (893 728 bytes, MAIN OS `5d8409e9…`, the
table of §11.4). What to try:

1. After the start: delay and reverb as on the official OS, the names Delay Time, Delay Fdbk, Reverb Size, Reverb Tone.
2. TRACK held + Delay Time, four detents right: the popup's name becomes REFD Time; the delay a fixed echo of 85 ms
   whose repeats follow Fdbk (shown as 0–127). Four more: nothing changes.
3. Four detents left: Delay Time and the stock delay again; listen right after for a buzz (§11.3).
4. The same with TRACK + Reverb Size: REFR Speed (0–127), a low-pass of the reverb send; back to the reverb, listen
   for a buzz or noise right after (the `[HYP]` of §11.3).
5. Fewer than four detents, a pause, a change of direction: no change.
6. Off and on again: the choice kept (saved at the change), its names at once.
7. TRACK + the other knobs: Control All as before; TRACK + FUNC + knob 14 / 15: Tone and Fdbk edited as before.
8. The knob while stepping: any stall when the settings are written (`0x400449b8`).

## 12. PPPCCC 2.0.0 (2026-10-26)

The maintainer, 2026-10-26: « prüf das repo erneut. es gab eben ein größeres update ». PPPCCC's 2.0.0 (commit
`db7a846f`) rebuilt the set; checked against model27 `4e696fb` (the tweaks' bytes, as in §6) and read in its docs:

- **Modular.** Patch 00 `core` holds what several features share: a gesture dispatcher on the encoder dispatch
  (`0x400081b8`, 8 slots, a handler answers "not mine", "handled" or "handled, pass on with 0 steps"), key slots for
  SETTINGS, a popup in the firmware's style (`0x40076c88`), SETTINGS as a modifier, the 4-detent selection, and the
  pattern header bytes 40–63 (tag `PCv2` in 60–63). Every other feature needs the core only: the chain of 1.0.0 is gone.
- **The effects** are two patches, `05 reverb-fx` (Chorus I/II, Phaser, RAZR) and `06 delay-fx` (Digital, VIBDEL,
  CHODEL), bit-identical to 1.0.0, chosen with TRACK + Reverb Size / Delay Time, 4 detents a step (the gesture of §9).
  They still hook the mixer's calls (`0x40056a2c`, `0x4005699c`, `0x40056a3c`): they and `fxslot` exclude each other.
- **The choice is per pattern** now (header byte 52 the reverb slot, 53 the delay slot, 54 the delay's speed), not a
  device setting: "Every pattern can have its own reverb-slot effect". model27 decided per device (§7); the header's
  bytes 40–63 are Chord Keys' too ([42 §4](42-clavier-accords-diatoniques.md)).
- **New:** `10 control-mode` (TRACK + tap SETTINGS: Control All absolute; it replaces the vtable entry `0x40100588`,
  and in absolute mode writes the other five tracks itself, past what Control All Config leaves out) and `11
  trig-select` (SETTINGS + PAGE). `0x404e9b5d` holds the control mode.
- **Against model27's tweaks:** RAZR's 1 024 bytes still take the boot hook's mask `0x4016cae8` (every build with a
  payload, SAMPLE's too); the load meter takes the governor's probe `0x40059382`; the core's tables lie in
  level-pan-values' mask, so every patch meets it; 12 019 bytes written in 46 masks, 8 839 of them in masks model27's
  tweaks use (§13.1). The core no longer reaches the USB stubs at `0x4015c23c`. The original bytes all check against
  the official image.
- **For §6:** the split asked there (shared parts apart, each feature on its own) is done; what is left for the effects
  to come into model27 is the same: each effect a package of its slot (`fxslot`), its code in the payload, the choice
  where model27 keeps it.

## 13. Per pattern against per device: the cost (2026-10-27)

The maintainer, 2026-10-27: « du kannst pro pattern prüfen und die kosten vergleichen. hat sich was am
speicherplatzbedarf der mods geändert? ». Nothing built; read in the OS and in Chord Keys, which keeps its settings in
the same place.

### 13.1 PPPCCC's space, 1.0.0 and 2.0.0 `[FAIT]`

Bytes each patch writes, by where they land (`_scratch/pppccc-check/size_cmp.py`, local, against the registry of
model27 `4e696fb`; "used" = masks a model27 tweak writes too):

| | 1.0.0 | 2.0.0 |
|---|---|---|
| Written, all patches | 13 006 B (124 writes) | 12 401 B (131 writes) |
| In sprite masks | 12 654 B in 42 masks | 12 019 B in 46 masks |
| In masks model27 uses | 6 965 B | 8 839 B |
| The same features (2.0.0 without control-mode 738 B, trig-select 1 464 B) | 13 006 B | 10 199 B (−22 %) |
| Reverb slot: chorus + phaser + razer → reverb-fx | 3 862 B | 2 318 B |
| Delay slot: digi-delay + mod-delays → delay-fx (+ core, which took the popup and the gesture from mod-delays) | 4 788 B | 2 083 B (+ 1 126 B) |

PPPCCC's own memory table gives 13 462 / 15 066 bytes of masks: it counts each mask whole, except live-mute's (62 B,
the bytes it writes). In model27 an effect's code goes to the payload, not into masks: the payloads share
`0x401aa140..0x40200000` (351 936 B, the image's end, registry §3), of which the largest Syntakt builds take about
270 KB.

### 13.2 The pattern header, read `[FAIT]`

- **Load** (serialized A → working B): `0x4005b3b4`, called only from the pattern load `0x4005b894` (`0x4005b8c6`).
  It copies the name (0..15), the words 16, 18, 20, 22, the bytes 24..28 and 38, each checked; nothing else.
- **Save** (B → A): `0x4005ba0a` copies the 64 bytes whole (`memcpy 0x4008f1f0`, B + 30642 → A + 14736).
- **Init**: `0x40061526(header, keep)`, only when `keep` is 0: the words 16..22, the bytes 24..27 and 38, the name.
  Callers: `0x4000c7fc`, and `0x4005b8d4` when a load fails. Bytes 28..37 and 39..63 stay as they were.
- **Whole patterns**: 30 710-byte copies (`pea 0x77f6` / `#30710` at `0x4000d216`, `0x4000ec40`, `0x40010aee`,
  `0x400617dc`, …) carry the header whole. Which of them are the copy and paste of the interface: `[HYP]`, not traced.
- **Free bytes**: no stock instruction addresses bytes 29..39 by the pattern's base (B + 30671..30681, A +
  14765..14775); accesses through a header pointer with a small displacement were not excluded (too many generic
  hits), `[HYP]` strong. Chord Keys holds 32..35 and 40..63 ([42 §4](42-clavier-accords-diatoniques.md), tested on
  the Model:Cycles, 42 §18). **Left: 29, 30, 31, 36, 37, 39, six bytes.**
- **Hooks clear of Chord Keys** (`0x4005b4a8`, `0x40061564`): load at `0x4005b4b0` (`move.b 38(a3),38(a2)`, 6 bytes,
  then on to `0x4005b4ba` with `d0` = 1); init at `0x4006155e` (`clr.b d0; move.b d0,38(a0)`, 6 bytes, back to
  `0x40061564`, Chord Keys' jump, so both run). PPPCCC's core takes the same two places (an alternative anyway).
- **Accessors** as Chord Keys' (`tools/machines/chord_keys/chord_storage.c`): audio, the playing pattern
  `*0x40a7887c`, its number at +30706, the object `root + 5192 + 732 · n`, its header at +60; interface, `0x4000f208`
  (the shown pattern) + 44, its header at +16, then the header's notify (vtable entry 4), as the stock setters.

### 13.3 Per pattern in `fxslot` (sketch, not built)

- Header byte 29 the reverb slot's id, 30 the delay slot's, 31 a check (`0x5a` + 29 + 30, as the record's §11.2).
  Claim `{"where": "pattern, header +29", "bytes": 3}`.
- Load hook: copy 29..31 when the check holds, else write the stock choice; then byte 38 as the OS. Init hook: the
  stock choice, then byte 38.
- `fx_run` reads the playing pattern's ids each block instead of the record once; a change runs §11.3 (the silence
  call, the reset) and renames the knobs.
- `fx_step` writes into the shown pattern with interrupts masked and calls its notify; no settings save
  (`0x400449b8` goes). Which pattern is "shown" while a pattern change waits for the end of the current one: `[HYP]`.

### 13.4 The cost

| | Per device (F2, built and proven) | Per pattern |
|---|---|---|
| Saved bytes | 8 in the settings block (`0x404e9b90`, outside its checksum) | 3 of the 6 header bytes left after Chord Keys; 3 left for every later pattern mod |
| Stock places hooked | the two mixer calls, TRACK's encoder | + load `0x4005b4b0`, + init `0x4006155e` |
| Code (payload) | 1 408 B | an estimate of +100 to +200 B: two stubs and the header accessors, less the record's code |
| Flash writes | the settings block at each choice (its time on the device: `[HYP]`, §11.9 step 8) | none; saved with the project, as every edit of the pattern |
| Proof | `test_fxslot.py` | + the real load and save (B → A → B), init, notify, a pattern change in the audio (template: `tools/emu/probe_chord_storage.py`) |
| Device test | §11.9 | + save and reload a project, a pattern change while playing, copy and paste a pattern, clear one, an old project |
| Claims | settings bytes | header bytes; `claims.py` compares saved places as strings, not ranges (`clash_items`), so "header +29" and a later "header +30" would not clash: a range check is needed first |
| Standard | a registry of device-settings bytes | a registry of pattern-header bytes (Chord Keys, Groove would use it too) |

### 13.5 What the musician gets

- **Per pattern**: the choice belongs to the pattern like Size, Time, Fdbk and Tone, whose meaning depends on the
  effect; a project sounds the same after loading, and on another device that has the same effects (an id it does not
  have plays the stock effect, §11.2); a pattern change can change the effect, and a tail ends when it does (§11.3);
  the choice is kept by saving the project, and lost with any unsaved edit. PPPCCC 2.0.0 works this way.
- **Per device**: one effect for every project; a pattern change never ends a tail by itself; the Size and Time of an
  old project are read by whatever effect is chosen today.
- **The stock OS** ignores the bytes; a project it saves carries whatever its buffer held in 29..31, so the check byte
  lets a random choice through once in 256 (`[HYP]`: the buffers are zero at start-up, not read).

### 13.6 Verdict

Per pattern costs little code and two hooks next to Chord Keys'. Its real costs: a longer proof and device test, and
a range check in `claims.py` once a second mod claims header bytes. What it buys: the choice and its parameters stay
together, no flash write at each choice (F2's open step 8 goes), and PPPCCC's users keep the behaviour they know.
Proposed to the maintainer: per pattern, as a change of F2 (F2b), before F3.

### 13.7 Against what the flasher offers (2026-10-27)

The maintainer, 2026-10-27: « alter was laberst du die ganze zeit von mods die überhaupt nicht im flasher sind ».
§12 and §13.1–13.4 weighed PPPCCC and the header against every tweak of `tweaks/`; the flasher offers two cards,
`OFFERED = ("sampler", "control-all-config")` (`tools/gen_flasher_tweaks.py`), the rest is for the command-line build
until reviewed. Against those two:

- **PPPCCC 2.0.0, bytes:** one clash only, `05 reverb-fx` (RAZR) in the boot hook's mask `0x4016cae8` (SAMPLE's 112
  bytes, and every composed machine build's boot stub). Every other patch shares no byte with SAMPLE or Control All
  Config (`pppccc_overlap.py` against `27-sampler.json`, `49-control-all-config.json`).
- **PPPCCC 2.0.0, behaviour:** `10 control-mode` in absolute mode writes the five other tracks itself, past the tracks
  Control All Config takes out.
- **The header:** neither card keeps anything in the pattern header (SAMPLE: sound and record slots; Control All
  Config: a gesture only). Free: 29..37 and 39..63, 34 bytes. Per pattern takes 3 of them; 29..31 keep clear of
  Chord Keys in case it comes back into the flasher, nothing more.
- The mask and governor figures of §12 and §13.1 ("in masks model27 uses") count tweaks the flasher does not offer.

## 14. F2b built (2026-10-27): the choice in the pattern

The maintainer, 2026-10-27: « Stell F2 auf pro Pattern um (F2b): Kopf-Bytes 29–31, Lade- und Init-Hook, Beweis nach
probe_chord_storage. », then « Ja, fang mit Schritt 1 an (Wahl pro Pattern). » The decision of §7 (per device) is
replaced: the choice belongs to the pattern, as its Size, Time, Fdbk and Tone (§13.5). Built in a copy of model27
`4e696fb` with F1 and F2 (nothing in the repository, nothing committed).

### 14.1 What was built

- **`fxslot` 0.3** (`fxslot.c`, `entries.S`, 1 642 bytes of code; F2: 1 408). The settings record is gone (no
  `0x404e9b90`, no `0x400449b8`). The pattern header's byte 29 holds the delay slot's id, 30 the reverb slot's, 31 a
  check, `0x5a` + byte 29 + byte 30; a header whose check fails chooses the stock effects. Every write of the three
  bytes masks the interrupts (`move.w %sr` / `ori 0x700` / back), so the audio never reads half of one.
- **`fx_run`** reads the playing pattern's choice in every block (`*0x40a7887c`, its number at +30706, its object
  `*0x40fe4228` + 5192 + 732 n, the header at +60: Chord Keys' reader, §13.2); when it is not the one the slot's
  parameters are named after (`cur`), it names them after it. The change of effect is §11.3's.
- **`fx_step`** steps the shown pattern's choice (`0x4000f208` on the singleton, + 44, the header at + 16), writes the
  three bytes and calls the header's notify (vtable entry 4, as the stock setters); when the shown pattern is the
  playing one it names the slot at once, with the interrupts masked (the audio names the same way).
- **`fx_load`**, `jsr` at `0x4005b4b0` in place of `move.b 38(a3),38(a2)` (6 bytes): the instruction, then
  `fx_hdr_load(a2, a3)` copies the three bytes when their check holds, else writes the stock effects (0, 0, `0x5a`);
  `d0` (= 1, the loader's return) and `d1`/`a0`/`a1` kept. **`fx_init`**, `jsr` at `0x4006155e` in place of
  `clr.b d0; move.b d0,38(a0)` (6 bytes): the instructions, then `fx_hdr_init(a0)`, the stock effects; `d0` = 0 and
  `a0` kept for `0x40061564`. Both places are clear of Chord Keys' (`0x4005b4a8`, `0x40061564`), so both chains run if
  it comes back into the flasher.
- **`part.json`** 0.3: `load`, `init`, `pattern` (the bytes, the pointers) instead of `record`; `claims`: `saved`
  "pattern, header +29", 3 bytes. **`compose.py`**: `fx_layer` writes the two hooks with the others; the build's
  holders get `fxslot`'s claims (`cl.part_claims`). The data block keeps its 1 180 bytes; its state is `cur[2]`,
  `played[2]`, `acc`, `last_slot`, `last_dir` at 1168, `last_time` at 1176.
- REFD and REFR unchanged (objects up to date); their manifests say "the playing pattern chooses", emulation date back
  to "not yet run".

### 14.2 The builds

| Selection | Writes | Added to the image | MAIN OS (SHA-256) |
|---|---|---|---|
| refdelay | 7: the boot (3), the delay's call, TRACK's, the loader, the initializer | 3 092 bytes | `6edb86ee…` |
| refreverb | 7 | 3 000 bytes | `8204fa6d…` |
| refdelay, refreverb | 8 | 3 268 bytes | `34db917f…` |
| sampler, refdelay, refreverb | SAMPLE's and the five | 43 776 bytes | `248cd17c…` |

For the device: `build/fx-f2b/model-cycles_OS1.13-refdelay+refreverb.syx` (894 112 bytes, git-ignored).

### 14.3 Checks without emulation (2026-10-27)

`gen_parts.py --check` (`shortcuts.o`, `dispatch.o` byte-identical to `4e696fb`), `gen_refmachine.py --check`,
`claims.py --check --self-test`, `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`,
`py_compile`, `test_compose.py --dry`, `webcompose_check.sh` (the twin unchanged): green. `test_fxslot.py --dry`:
**ALL OK** (the five sites, the tables, names, formatters, descriptor tables). Unicorn stops with SIGILL in the
sandbox: the proof runs in the maintainer's terminal.

### 14.4 The proof, for the maintainer's terminal

`tools/emu/test_fxslot.py` for F2b: the audio reads the playing pattern through the patterns as the OS links them
(eight ways of choosing nothing, a pattern choosing the effects, a pattern change to the stock effects and back, the
names at each first block); the gesture writes the shown pattern's bytes, calls its notify once per change, never
saves the settings, leaves the names and a playing pattern alone when the shown one does not play, and does nothing
without the singleton; **5. the pattern**, as `probe_chord_storage.py`: the stock loader and initializer leave the
bytes, the header's copy keeps them; with the hooks, five kinds of saved bytes, a new header, "keep", a whole pattern
saved, loaded and copied, two files that choose nothing; the interrupts masked at every write.

```
python3 tools/emu/test_fxslot.py --cycles firmware/model-cycles_OS1.13.syx
```

### 14.5 The proof run (2026-10-27) `[FAIT en émulation]`

The maintainer, 2026-10-27, in their terminal: « test_fxslot.py (F2b) ist bei mir durchgelaufen: ALL OK. » So, for
refdelay, refreverb, both, and SAMPLE with both, on the OS's own code: the five sites and the data block; the audio
choosing from the playing pattern (eight ways of choosing nothing, the choice, a pattern change and back, the names at
each first block), the effects bit for bit, the stock OS's SRAM and lines everywhere else; the gesture writing the
shown pattern with its notify, never saving the settings, leaving a playing pattern that is not shown alone; the
header's loader, initializer, a whole pattern saved, loaded and copied, every write of the three bytes with the
interrupts masked. **F2b done in emulation**; not tried on the device (§14.7).

### 14.6 Left

- Which pattern is "shown" while a pattern change waits for the end of the current one, `[HYP]`: the gesture edits
  the shown one, the names follow the playing one.
- The interface's copy and paste of a pattern: the 30 710-byte copies carry the header (§13.2), which of them it
  uses `[HYP]`; what the notify does beyond calling the observers (`0x400d0f6c`) `[HYP]`. Both for the device.
- `claims.py` compares saved places as strings (§13.4): to extend when a second offered mod keeps header bytes.
- A device that ran F2 keeps its 8 bytes at `0x404e9b90`, read by nothing now.
- F3: the composer's twin (`composer.js`), the flasher's effect cards.

### 14.7 For the device, prepared 2026-10-27

The build above, with a send on a track (Delay Send, Reverb Send):

1. A new pattern: the stock Delay and Reverb, their own names.
2. TRACK + Delay Time, four detents right: REF Delay, the knobs named REFD Time / REFD Fdbk at once (REFD reads Fdbk
   only: Time shows its value, the echo stays 85 ms; the maintainer heard no change of Time, 2026-10-27, as built);
   TRACK + Reverb Size: REF Reverb (a low-pass, not a reverb), REFR Speed / REFR Tone.
3. Another pattern with the stock effects: at the pattern change, the stock effects and names; back: the REF ones.
4. Save the project, power off and on, load it: each pattern's choice kept.
5. Copy a pattern with REF effects and paste it on another: the choice comes with it.
6. Clear a pattern: the stock effects.
7. A project saved before this build: the stock effects everywhere.
8. Turning the knob while stepping: no stall (nothing is written to the flash any more).
9. TRACK + the other knobs: Control All as before; TRACK + FUNC + knob 14 / 15: Tone and Fdbk as before.

### 14.8 Tested on the Model:Cycles (2026-10-27)

The maintainer, 2026-10-27, with the build of §14.2 (refdelay, refreverb): « getestet, past », after the steps of
§14.7 (step 2 as built: REFD does not read Time). **F2b works on the device**: the choice per pattern, its names, the
pattern changes, the project saved and loaded, copy and paste, a cleared pattern, an older project, the knob without a
stall, TRACK and TRACK + FUNC on the other knobs as before. The HYPs of §14.6 on the interface's copy and paste and on
the waiting pattern change are answered by this test as far as it went; what the notify does inside the OS stays
unread.

## 15. The effect format, a draft (2026-10-27)

The maintainer, 2026-10-27, on the gaps listed to them (more knobs, the delay line, the load, more slots, MIDI, the
web flasher, a specification): « ich würde mit 2, 3, 6 und 7 starten. mehr regler kann dann später als erweiterung
kommen. », then « ja » to this draft first. So this section fixes what an effect package is and gets today, leaves the
delay line (§15.6) and the load (§15.7) as the questions of the next two steps, and reserves the extensions (§15.8)
without building them. It is written for model27; the standard's text follows from it at the last step. What it
states as built is F2b (§14), tested on the device.

### 15.1 What an effect is

- A package: a folder `tools/machines/<id>/` with its sources, its committed object (`ld -r`, only `R_68K_32`, placed
  by `relocate.py` in the payload like a machine's) and a manifest, schema `cycles-mod/0.1`.
- Its `uses` holds exactly one `fx.delay` or `fx.reverb` entry (§15.2), and `memory.ram` claims if it needs RAM beyond
  its variables. Nothing else: no machine, no hook, no vtable entry, no patch point (`load_manifest` refuses them).
- `build.roots` names the process first, then the reset and any formatter.
- An effect never writes the OS: the composer adds the part `fxslot` to every build that holds an effect, and
  `fxslot` alone hooks the OS (§14.1).

### 15.2 The slot entry

| Field | Value |
|---|---|
| `point` | `fx.delay` or `fx.reverb`: the slot the effect plays in, in place of the stock effect |
| `id` | the effect's number, 1–255, fixed (§15.5) |
| `process` | the symbol called every block (§15.3) |
| `reset` | optional: the symbol called before the first block the effect plays after being chosen |
| `params` | the slot's two parameters as the effect names them, in the slot's order (delay: Time, Fdbk; reverb: Size, Tone): `long` (1–15 characters), `short` (1–5), `format`: none (the slot's stock formatter), `"int"` (0–127, `0x400456c8`) or a symbol of the package (reserved: its signature, the interface object's `std::function` invoker at +0x20, is not written down yet) |
| `name` | the effect's name, 1–15 characters: shown as the parameters' group |
| `short` | a short name; not read by the composer today |
| `why` | what the entry is for, in words |

Printable ASCII only; the composer refuses any other value.

### 15.3 The call

- `process(out, in, params)`, in the audio interrupt, once per block (32 frames at 48 kHz, 666.7 µs), in place of the
  stock effect, with its arguments (§1.1): `in` the send bus, 32 stereo frames of signed 32 bits, L at +0 and R at +4
  (256 bytes in SRAM, `0x8000b990`); `out` the slot's return, the same shape (`0x8000ba90` delay, `0x8000bb90`
  reverb), all 64 words written every call; `params` the stock effect's smoothed words (§8.1): P + 428 for the delay
  (Time at +0, Fdbk at +2), P + 432 for the reverb (Size's byte at +0, Tone at +2), each value × 256.
- The C ABI: `d2`–`d7`/`a2`–`a6` kept; the EMAC free (the mixer sets `MACSR` again after the call).
- Not allowed: the interface's code, an allocation, a wait, a lock; the stock effects' lines and DMA (until §15.6).
- `reset()`, optional, in the audio interrupt, just before the first `process` after the effect is chosen (a pattern
  change, the gesture, a load), in the same block: it must be short. Not called at start-up: the boot hook zeroes the
  payload's variables.
- The effect's state: its variables (the payload's, zero at start-up) or its `memory.ram` claims.
- As an effect starts, `fxslot` gives the slot's stock effect one block of silence (§11.3), so the stock line holds no
  old sound when the stock effect comes back.

### 15.4 What the device does (given by `fxslot`)

- The choice is the pattern's (bytes 29–31 of its header, §14); TRACK + Delay Time / Reverb Size steps through the
  slot: the stock effect, then the build's effects by id, four detents a step, stopping at the ends.
- While an effect plays, the slot's two parameters carry its names, its group name and its formatters.
- An id the build does not hold plays the stock effect and stays in the pattern: a project moves between builds.
- At most seven effects per slot in one build (a table of eight with the stock effect).

### 15.5 The ids

- 0 is the stock effect. 1–239 are given to effects users get, once, in model27's registry, never reused: the id
  lands in users' patterns (the standard's §5, numbers in users' data). One space for both slots.
- 240–255 are for references and private tests, never offered: REFD 254, REFR 255.
- Proposed for the registry: a table in `REGISTRY.md` generated from the manifests (id, slot, package, author), and
  `check_overlaps.py` / the composer refusing two packages with one id (the composer already refuses it in a build).

### 15.6 Open, step 2: the delay line (answered in §16)

A delay needs a long line: the stock delay's is `0x42400000`–`0x42800000` (4 MiB SDRAM), fed by DMA every block
(`0x400573fa` writes; the read is set up in `0x4005802e`, which also computes the delay time: `0x400581ae` lies
in it, read 2026-10-27, §1.3). The questions: what the DMA reads and writes, block by block; whether an effect may own the line while it
plays (`fxslot` holding the stock write DMA back, or moving it, as PPPCCC does); or an effect's own RAM, read and
written by the CPU. The answer becomes a field of the slot entry (a `line` claim) or of `memory.ram`.

### 15.7 Open, step 3: the load (answered in §17)

The standard's §6: a block is 166 667 cycles at 250 MHz; the mixer and stock effects take about 30 %; above about
85 % the interface starves. Proposed: each effect declares `cost.emulation {mean, max}` in instructions per block,
measured by its proof on noise and silence, and `cost.device {percent_per_block}` once measured on the device. One
effect per slot plays at a time, so a build's worst case is the dearest effect of each slot, not their sum. The
composer warns, or refuses, above a threshold; whether the audio side also guards (the governor of notes/25, 28, 30,
36 mutes voices only) is read in step 3.

### 15.8 Reserved, not built

- **More parameters:** `params` may grow past two entries, reached on a page or by a gesture to be chosen; a package
  with two keeps working.
- **More slots:** the names `fx.*` are kept for other places (an insert on the main mix, for instance); each needs a
  hook in the mixer of its own.
- **MIDI:** a CC to choose the slot's effect.
- **The stock effect inside an effect** (RAZR runs the stock reverb with its own parameters): allowed when the first
  effect that does it is proven.
- **A formatter of the package's own:** its signature, with the first effect that needs it.

### 15.9 The steps from here

1. The delay line (§15.6): read, decide, extend `fxslot`, prove.
2. The load (§15.7): measure REFD and REFR, the fields, the composer's check, the governor read.
3. Digital Delay (PPPCCC, MIT) as the first real effect: the line and the load proven on it; its time computed by its
   own code (17 bytes of PPPCCC's setup match the OS at `0x400581be`).
4. The web flasher: `composer.js` as `compose.py` for effects, effect cards, Digital Delay "experimental".
5. The standard: this format as `fx.delay` / `fx.reverb` in its draft, in place of the unmapped `fx.bus`.

## 16. The delay line (2026-10-27)

The maintainer, 2026-10-27: « Der Entwurf passt, mach mit der Delay-Zeile weiter. » Step 1 of §15.9.

### 16.1 How the stock delay uses its line `[FAIT]`

- **The line**: `0x42400000`–`0x42800000` (uncached `0x4a400000`), 512 Ki frames of 8 bytes (two 32-bit words), a
  ring of 4 MiB (index mask `0x7ffff`): 10.9 s at 48 kHz.
- **The write**, `0x400573fa`, called by the mixer at `0x40056a3c` after the effects: `w` = `*0x8000b988` (in frames)
  becomes `(w + 32) & 0x7ffff`; the eDMA channel at `0xfc045540` copies 16 × 16 bytes (32 frames) from `*0x8000b570`
  (the delay's buffer in SRAM) to `0x4a400000 + 8 w`, the destination taken modulo 4 MiB (ATTR `0x04b4`), then loads
  the next descriptor from `0x8000a560` (CSR `0x11`, scatter-gather).
- **The read and the time**, in `0x4005802e` (the mixer's call at `0x400567d8`, before the effects): the time
  `((P428 + 256) · 48000 >> 10) · 900 / *0x40149310` (the tempo), at most 384 000; the delay `D` in frames follows it
  through a one-pole smoothing (`*0x8000b980`, about 255/256 a block), the previous `D` kept at `*0x8000b984`; the
  eDMA channel at `0xfc0453c0` (source modulo 4 MiB) reads 17 × 16 bytes from `0x4a400000 + 8 ((w − D) & 0x7ffff)`
  into `0x8000b590`, then, from the descriptor it builds at `0x8000b960`, the same from `w − D_previous` into
  `0x8000b6a0`; the mixer waits on `0xfc0453de` before calling the delay (§1.1).
- **So the line belongs to the DMA**: every block, whatever the slot plays, `0x4005802e` reads it and `0x400573fa`
  writes 32 frames at `w` from the delay's buffer (§11.3 gives that buffer a block of silence as an effect starts).

### 16.2 Decided: a line per slot, apart from the stock one

- **(a) The stock line for the effect.** `fxslot` would hold back the write (`0x40056a3c`) or move it, as PPPCCC moves
  it to the other half; a second hook in the mixer; the stock delay, coming back, reads what the effect left at
  `w − D` and plays it.
- **(b) A line of the slot's own.** RAM in the payload's variables, one per slot, as large as the largest of the
  slot's effects asks, shared by them (one plays at a time); the CPU alone reads and writes it, through the cache
  (`0x40000000`–`0x47ffffff` copyback, notes/23), never a DMA; zero at start-up (the boot hook clears the variables).
  No new hook; the stock line and its DMA stay the stock delay's.

**Chosen: (b).** Its costs: the variables grow by the line (they start at `0x43036000`; with SAMPLE its pool starts at
`0x43800000`, about 7.8 MiB for every package's variables and the lines; the composer refuses a payload that runs into
a claim); the boot clears it (some milliseconds for 4 MiB, `[HYP]`).

### 16.3 The contract (added to §15)

- The slot entry's `line`: the bytes the effect needs, a multiple of 16 from 16 to 4 MiB (`FX_LINE_MAX`), with one
  patch point `{"symbol": <name>, "kind": "fx_line"}`: both or neither.
- The line is 16-aligned, at least as large as asked, zero at start-up, and shared with the slot's other effects. At
  `reset` its content is another effect's or an old one: an effect reads only what it wrote since its reset (a count
  of the frames written), or clears it in `reset` when that fits in a block (REFD: 32 KB).
- The CPU only, through the cache; no DMA on it.
- A reverb slot's effect may ask for a line too (its own, apart from the delay slot's).

### 16.4 What was built

- **`compose.py`**: `FX_LINE_MAX`; `load_manifest` takes one patch point of kind `fx_line` and the slot entry's `line`
  together, refuses every other form; the lines are laid out first in the variables, the delay slot's then the
  reverb slot's, each 16-aligned, and every effect of the slot that asks gets its address; the tweak's description and
  symbols (`fx_line_delay`, `fx_line_reverb`) and the info (`fx_lines`) say where.
- **REFD 0.3**: its echo line (32 768 bytes) is the delay slot's (`extern int32_t fx_line[]`, `"line": 32768`); its own
  variables are 4 bytes. Its sound is unchanged; emulation date back to "not yet run".
- **`test_fxslot.py`**: the lines in every build (where, how large, apart from the packages' variables, the address
  in the effect's code); the composer's five refusals; two effects of one slot sharing its line (REFD and a copy with
  id 253 asking for 64 KiB, composed from a folder made for the test: one line of 64 KiB, the address in both).

| Selection | MAIN OS (SHA-256) | Payload |
|---|---|---|
| refdelay | `c295efc3…` | `0x43000000`..`0x4303e004`, the line at `0x43036000` |
| refdelay, refreverb | `cf575c77…` | `0x43000000`..`0x4303e00c` |
| sampler, refdelay, refreverb | `3363e2b1…` | `0x43000000`..`0x4304d2ac` |

The payloads end where they did: the line takes the place of REFD's array.

### 16.5 Checks (2026-10-27)

`claims.py --check --self-test`, `gen_refmachine.py --check`, `gen_parts.py --check`, `check_overlaps.py`,
`registry.py --check`, `gen_flasher_tweaks.py --check`, `py_compile`, `test_compose.py --dry`, `webcompose_check.sh`:
green. `test_fxslot.py --dry`: **ALL OK**, with the lines, the refusals and the shared line. The full proof (REFD
bit for bit from the slot's line) for the maintainer's terminal:

```
python3 tools/emu/test_fxslot.py --cycles firmware/model-cycles_OS1.13.syx
```

### 16.6 The proof run (2026-10-27) `[FAIT en émulation]`

The maintainer, 2026-10-27, in their terminal: « test_fxslot.py (Delay-Zeile) ist bei mir durchgelaufen: ALL OK. »
So, besides everything of §14.5: REFD bit for bit from the delay slot's line, in every build; the lines placed and
sized, the refusals, the shared line. **The delay line done in emulation.**

### 16.7 Left

- `composer.js` must lay the lines out as `compose.py` does (step 4 of §15.9).
- The boot's clearing time for a large line, on the device, with the first real delay (Digital Delay, 2 MiB).
- A device run of REFD 0.3 is not needed for the line itself (the same kind of memory as its array before); it comes
  with Digital Delay.

## 17. The load (2026-10-27)

The maintainer, 2026-10-27: « Ja, mach mit der Rechenlast weiter. » Step 2 of §15.9.

### 17.1 What there is `[FAIT]`

- The standard's §6: a block is 32 frames at 48 kHz, 666.7 µs, 166 667 cycles at 250 MHz; at 1.54 cycles an
  instruction about 108 225 instructions. The mixer and the stock effects take about 30 % of a block on the device,
  the interface starves above about 85 %. A package declares `cost.emulation {first, mean, max, pattern}`, counted
  with `mcengine.py`'s counter (`count_instructions`, every instruction executed), as CHORD Tables does
  (`tools/machines/chordtables/manifest.json`).
- The governor (`tools/machines/gov/`, notes/25, 28, 30, 36) lives in the Syntakt engines' builds: the audio
  function's probe (`0x40059382`), the block's load from the DMA timer, voices muted when the load stays high. None
  of the cards the flasher offers carries it, and it mutes voices, never an effect.

### 17.2 Decided

- **Counted, declared, checked.** Each effect declares `cost.emulation {first, mean, max, reset, pattern}`:
  instructions per block of its process called alone after its reset (the reset counted apart), noise of ±2^28 into
  both channels, the slot's first word 64 and its second 96 (× 256), the first block then the mean and maximum over
  the next 21 (since §18: Time 0 for the delay, the mean and maximum over 21 blocks after 32 more, so that a delay
  reads what it wrote; the numbers of REFD, REFR and the stock effects do not depend on it). `fxslot`'s `part.json` declares, per slot, the stock effect's numbers counted the same way and what the
  slot adds: with the stock choice, with an effect, in the block of a switch, and the stock effect's block of
  silence. `test_fxslot.py` counts them all on the OS's own code and checks the declared numbers are the counted ones.
- **The composer's rule.** One effect of a slot plays at a time, so a build's load is per slot: its dearest effect's
  maximum plus what `fxslot` adds with an effect, less the stock effect's maximum (steady), and the block of a switch
  (peak). Above 10 % of a block (`FX_WARN`, 10 822 instructions) the composer warns; above 25 % (`FX_REFUSE`, 27 056)
  it refuses the build; an effect without numbers is a warning, "load not known"; a switch's block past half a block
  is a warning too (`FX_PEAK_WARN`, §17.4). The thresholds are a proposal:
  PPPCCC measured its two dearest effects together at about 9 % of a block on the device (§12; idle 76 %, CHODEL with
  RAZR 85 %).
- **No guard at run time, for now.** A guard in `fxslot` (the DMA timer around the effect, the stock effect back
  when it stays too long) would act on numbers nobody has measured on the device yet, and would drop an effect
  without a word to the musician. Reserved, to be weighed with the first real effect's device numbers (Digital Delay).

### 17.3 What was built

- **`compose.py`**: `BLOCK_INSTR`, `FX_WARN`, `FX_REFUSE`; `fx_cost(effects, part)`, the load per slot from the
  declared numbers; a build past `FX_REFUSE` refused; the info (`fx_load`) and the summary print it per slot, with
  "warning" past `FX_WARN` or when a number is missing.
- **`test_fxslot.py`** section 6 (the cost): three engines (stock, the build through the slot, the build calling the
  effect directly) on the same blocks; the numbers per effect and per slot, the same in every build of the run, written
  to `build/fx-cost.json`, compared with the declared ones where declared.
- Not declared yet: the counts come from the maintainer's run (Unicorn does not run in the sandbox), then go into
  REFD's and REFR's manifests and `fxslot`'s `part.json`, and a second run checks them.

### 17.4 The numbers (2026-10-27) `[FAIT en émulation]`

The maintainer, 2026-10-27: « test_fxslot.py (Rechenlast) ist bei mir durchgelaufen, build/fx-cost.json ist da. »
Counted the same in every build of the run (instructions per block):

| | first | mean | max | reset |
|---|---|---|---|---|
| the stock delay | 2 659 | 2 659 | 2 659 | — |
| the stock reverb | 8 205 | 8 205 | 8 205 | — |
| REFD (254) | 1 741 | 1 741 | 1 741 | 24 579 |
| REFR (255) | 658 | 658 | 658 | 3 |

What `fxslot` adds: 81 (delay) and 80 (reverb) with the stock choice, 87 and 86 with an effect, 199 and 197 in the
block of a switch besides the effect's first block, its reset and the stock effect's block of silence. Declared in
REFD's and REFR's manifests and in `part.json`; the composer now prints, for refdelay with refreverb:

```
the delay slot's load: refdelay at most -831 instructions a block on the stock effect (-0.8% of a block), +26519 in the block of a switch
the reverb slot's load: refreverb at most -7461 instructions a block on the stock effect (-6.9% of a block), +858 in the block of a switch
```

- The stock effects together take about 10 % of a block by this count (10 864 instructions), a third of the 30 % the
  device shows for the mixer and its effects (the emulator does not time memory).
- **REFD's reset is a quarter of a block** (24 579 instructions: 32 KB cleared). So the block of a switch to REFD runs
  about 24.5 % above the stock one. This is what §16.3 means: a line of 2 MiB (Digital Delay) can never be cleared in
  a reset; it keeps a count of the frames written. The composer warns past half a block in the block of a switch
  (`FX_PEAK_WARN`).
- A second run checks the declared numbers against the counted ones.

### 17.5 The second run (2026-10-27) `[FAIT en émulation]`

The maintainer, 2026-10-27: « test_fxslot.py (zweiter Lauf, Rechenlast) ist bei mir durchgelaufen: ALL OK. » The
declared numbers are the counted ones, in every build of the run. **The load done in emulation.**

### 17.6 Left

- The device's share of a block, with Digital Delay (`cost.device`, the standard's §6); with it, whether a guard at
  run time is wanted (§17.2).
- `composer.js` computes the same load for the web flasher (step 4 of §15.9).
- `composer.js` computes the same load for the web flasher (step 4 of §15.9).

## 18. Digital Delay, the first real effect (2026-10-27)

The maintainer, 2026-10-27: « Ja, fang mit Digital Delay als erstem echten Effekt-Paket an. » Step 3 of §15.9.

### 18.1 PPPCCC's code, read `[FAIT]`

From patch 06 `delay-fx` of PPPCCC 2.0.0 (`db7a846f`; generators `src/gen_digidelay_113.py`, `src/gen_fx4.py`,
`src/v2/g2_delayfx.py`), disassembled from the patch's bytes:

- **Setup** `DD` at `0x40160e6c` (234 bytes), entered with the stock delay's stack: the gain from Fdbk, the delay from
  Time, the state, then `jmp` to the loop. **Loop** at `0x40185f48` (216 bytes), 32 frames. **TC** at `0x4018fd3a`:
  Time + 256, or the delay-notes patch's routine when `0x400581b8` holds its `jsr`. **State** at `0x4233c140`, 20
  bytes: the write index, the delay now, a mark `DIG1` (absent: a first block, everything from zero and the delay at
  the knob's), the low-pass, the high-pass. **Line** at `0x4a400000` (uncached), 262 144 frames of 8 bytes, both words
  written, the first read.
- **The arithmetic**, per frame: the delay slews towards the knob's by `diff >> 13`, or one frame every fourth frame
  when that is 0; `d = line[w − delay]`; `x = sat((d >> 15) g + ((d & 0x7fff) g >> 15) + (L >> 3) + (R >> 3))` with
  `g = (3t − (t² >> 15) t >> 15) >> 1`, `t = Fdbk 0..127 × 258`; low-pass `lp = sat(x − 3x/16 + 3lp/16)` (each 3/16
  as `v >> 3` plus half of it); high-pass `h = lp − hp`, `hp += h >> 5`, `line[w] = h − (h >> 5)`; out `6 d`,
  saturated in three steps, on both channels.
- **The delay**: `((Time + 256) · 48000 >> 10) · 900 / tempo` (`*0x40149310`, 14 400 at start-up), clamped unsigned
  to 32..261 120 frames: the stock delay's formula (§16.1), so the stock Delay Time formatter shows Digital's time.
  Those instructions, 17 bytes of the setup, are the same as the stock ones at `0x400581be`: the port computes the
  formula in C of its own.
- **`W2`** moves the stock write DMA into the other half of the line while one of PPPCCC's delays plays (§16.2 a).
  With the slot's own line the port needs none of it.

### 18.2 The port

- **`tools/machines/digidelay/`**: `digidelay.c`, PPPCCC's arithmetic step for step in C (900 bytes compiled, 24
  bytes of variables); `manifest.json` (id 1, `line` 1 MiB: one word a frame, as only the first is read; `Digi Time`
  / `TIME`, `Digi Fdbk` / `FDBK` with the stock formatters, the group `Digital`, PPPCCC's names); `LICENSE`, PPPCCC's
  MIT text; credit "PPPCCC (gialloinfuso)". **`tools/gen_digidelay.py`**: the object, `--check`, the build alone (no
  tweak, as REFD and REFR). **`THIRD-PARTY-NOTICES.md`**: a row.
- **What differs from PPPCCC**, none of it heard from start-up: the line is the slot's (1 MiB, through the cache, the
  CPU only); `digi_reset`, called by the slot when Digital is chosen, starts it again from silence as PPPCCC's first
  block does, and a frame is read only once it was written since (`n`), where PPPCCC keeps its state and line across a
  switch and plays an old echo back; no coupling to delay-notes (not in model27: the stock + 256).
- **Id 1**, the first of 1–239 (§15.5): a proposal, fixed once Digital ships.

### 18.3 The builds

| Selection | Writes | Added to the image | MAIN OS (SHA-256) | Payload |
|---|---|---|---|---|
| digidelay | 7 | 3 764 bytes | `4fb4eac7…` | `0x43000000`..`0x43136018`, the line from `0x43036000` |
| digidelay, refreverb | 8 | 3 936 bytes | `7a755c6e…` | `0x43000000`..`0x43136020` |
| sampler, digidelay, refreverb | 131 | 44 444 bytes | `4b3e448d…` | `0x43000000`..`0x431452c0` |

For the device: `build/fx-digi/model-cycles_OS1.13-digidelay.syx` (894 496 bytes, git-ignored).

### 18.4 Checks (2026-10-27)

`gen_digidelay.py --check`, `claims.py --check --self-test`, `check_overlaps.py`, `registry.py --check`,
`gen_flasher_tweaks.py --check`, `gen_parts.py --check`, `gen_refmachine.py --check`, `py_compile`,
`test_compose.py --dry`, `webcompose_check.sh`: green. `test_fxslot.py --dry`: **ALL OK** (the sites, tables, names
and the line of the three new selections). On the Mac, `digidelay.c` compiled for the host against the proof's model
(`_scratch/digidelay/hostcheck.py`, local): 400 blocks, §18.5's sequence twice with a reset between, 22 600 outputs
not zero, **no difference**.

### 18.5 The proof, for the maintainer's terminal

`test_fxslot.py` holds Digital in the selections (section 3: the playing pattern choosing it, against the model;
section 6: its cost) and a section 7: its process alone over 200 blocks (750 frames of delay at Fdbk 96; Fdbk 127 with
full-scale noise, saturating; the delay moved to 2 250 frames and slewing; silence, the tail), from start-up and again
after a reset, against the model bit for bit; with `--pppccc`, against PPPCCC's own code too (their
`patches/06-delay-fx.json` applied to the official OS, entry `0x40160e6c`), bit for bit up to the reset:

```
python3 tools/emu/test_fxslot.py --cycles firmware/model-cycles_OS1.13.syx --pppccc <PPPCCC>/patches/06-delay-fx.json
```

**First run (2026-10-27):** every selection with REFD and REFR ALL OK as before (their declared costs the counted
ones under the new pattern), then `digidelay` stopped at the start-up check: `boot_hook_ok`
(`test_sdvintage_exact.py`) mapped 1 MiB for the payload and its variables, and with Digital's line they reach
`0x43136018`; `t7.UI` (`test_sdvintage_7th.py`) mapped the same 1 MiB. Both now map the payload's size rounded up to
a MiB, at least 1 MiB (every other proof's map is unchanged). A limit of the proofs, not of the build: on the device
the variables lie in SDRAM like the rest of the payload.

**Second run (2026-10-27), with `--pppccc`:** every REF selection ALL OK again; `digidelay` ALL OK through the
start-up, the sites, the audio (the playing pattern choosing it, against the model), the gesture, the pattern and the
cost: **Digital first 2 621, mean 3 131, max 3 131 instructions a block, reset 2** (the stock delay 2 659), declared
since in its manifest. Then section 7 stopped before running: PPPCCC's 06 `delay-fx` requires their 00 `core` (it
writes into the core's slot table at `0x4018f5f8`), and the proof applied 06 alone, so its SHA-256 check refused the
bytes. `pppccc_image` now applies the required patches first, found by id next to the file (core, then delay-fx),
each write checked: on the Mac, both apply to the official image (3 037 bytes changed).

**Third run (2026-10-27), with `--pppccc`:** the maintainer: « test_fxslot.py (Digital Delay, mit --pppccc) ist bei
mir durchgelaufen: ALL OK. » So, besides every REF selection: Digital in its three builds through the start-up (the
1 MiB line cleared), the sites, the audio, the gesture, the pattern; its declared cost the counted one in each build
(`build/fx-cost.json`: first 2 621, mean and max 3 131, reset 2); and section 7, its process alone over 200 blocks
from start-up and after a reset, **bit for bit the model's and, up to the reset, PPPCCC's own code's** (their 00 core
and 06 delay-fx on the official OS, entry `0x40160e6c`). **Digital Delay done in emulation**; not tried on the device.

### 18.6 For the device, prepared 2026-10-27

The build of §18.3 alone, a send on a track:

1. TRACK + Delay Time, four detents right: the knobs `Digi Time` / `Digi Fdbk`, the group `Digital`.
2. Bright, clean repeats, each a little thinner in the lows; Time up to the knob's top (5.4 s at most), Fdbk 127 close
   to endless without blowing up.
3. Back to the stock Delay and to Digital again: Digital starts from silence, no old echo.
4. A pattern change between a pattern with Digital and one without; saved and loaded.
5. The start-up: 1 MiB more cleared by the boot, a longer start? `[HYP]` a few ms.
6. All six tracks playing with Digital: no stutter (§17: its cost by the emulator, the device's share unknown).

### 18.7 Tested on the Model:Cycles (2026-10-27)

The maintainer, 2026-10-27, with the build of §18.3 (Digital alone): « alle punkte getestet, nichts auffällige, alles
wie erwartet », after the six steps of §18.6. **Digital Delay works on the device**: chosen with TRACK + Delay Time
under its names, its sound, Time and Fdbk to their tops, the switch back and forth starting from silence, the pattern
changes, saved and loaded, the start-up, all six tracks playing with it. The device's share of a block was not
measured (no meter in the build); nothing was heard to stutter.

### 18.8 Left

- The flasher (step 4 of §15.9), and with it Digital's card; the id decided for good.

## 19. The web flasher: effects as cards (2026-10-27)

The maintainer, 2026-10-27: « Ja, fang mit dem Web-Flasher für Effekte an. » Step 4 of §15.9.

### 19.1 What was built

- **`compose.py`**: `web_package()` carries an effect's slot entry and its cost; `web_part()` carries the part's own
  fields, `fxslot`'s (`slots`, `track`, `load`, `init`, `formatter_sites`, `int_format`, `cost`) besides `sites` and
  `shortcut`.
- **`docs/flasher/composer.js`**, the twin: effects among the packages (an effect and a machine in one package refused),
  the slots' lines first in the variables, `fxLayer()` as `fx_layer()`, `fxCost()` as `fx_cost()` with `FX_WARN`,
  `FX_REFUSE`, `FX_PEAK_WARN`, `fxslot`'s claims among the build's holders, the lines' symbols, the info (`slot`,
  `fx_id`, `fx`, `fx_lines`, `fx_load`).
- **`tools/webcompose_synth.py`**: seven selections with effects (Digital alone; REFD with REFR; SAMPLE with Digital,
  both orders; SAMPLE with REFD and REFR; Digital, REFR, REF2 and SAMPLE, with the shortcut layer, the dispatchers and
  the moved descriptor table; CHORD Tables with Digital, the stock table), `fxslot` among the parts.
- **The card's build alone**: `39-digidelay.json` by `gen_digidelay.py`, with `LICENSE-PPPCCC`. The tweaks whose
  conflicts are computed against the folder gained `digidelay` and nothing else (`27-sampler`, `28-refmachine`,
  `29-refmachine2`, `34-refchord`, `36-chordtables`); `REGISTRY.md` regenerated.
- **The card**: `FEATURES` (`cat` sound, experimental, credit "based on PPPCCC-Model-Cycles-1.13-Mods by
  gialloinfuso", `license` LICENSE-PPPCCC, `package` digidelay), `OFFERED`, `fxslot` among the page's parts;
  `tweaks.js` and `docs/flasher/LICENSE-PPPCCC.txt` generated. The page composes every ticked package card into one
  tweak, machines and effects alike (`sampler+digidelay`).
- **`app.js`**: the card's texts (en, fr), its guide anchor, a line in the credits, the composer's log (the effect's
  slot; a warning when a slot's load passes `FX_WARN` or a switch's block `FX_PEAK_WARN`), `REF_MAINOS` (7
  combinations) and `REF_MODS` (4) regenerated by `ref_mainos.py`.
- **For users**: the guide's section 4, Digital Delay (en, fr; the sections after it renumbered), release 0.10, the
  stamp `2026-10-27-01`, `README.md`, `PROVENANCE.md`, `BUILD.md`.
- **`tools/webflash_smoke.js`**: three cards, their order by section, the credits (six links, ten repositories),
  Digital alone, with SAMPLE (one composed tweak) and with Control All Config, the French texts.

### 19.2 Checks (2026-10-27)

`webcompose_check.sh` with the official file: every selection identical to `compose.py` (the seven new ones too; Digital
alone gives MAIN OS `4fb4eac7…`, the image played on the device), `fill` 6/6. `ref_mainos.py --check`.
`webflash_smoke.sh` with both official files: 178 checks, **ALL PARTS OK**. `webbuild_check.sh`, `webflash_check.sh`,
`gen_digidelay`, `gen_sampler`, `gen_refmachine`, `gen_chordtables`, `gen_parts`, `gen_flasher_tweaks` with
`--check`, `check_overlaps.py`, `registry.py --check`, `claims.py --check --self-test`, `py_compile`: green.

### 19.3 Left

- **The device, from the page**: Digital alone, then with SAMPLE; then the card's status to "tested" (the guide's line,
  the release, the stamp), as AGENTS.md's step 8.
- **Id 1** is Digital's from the commit that ships it: fixed for good then (§15.5).
- **The gesture's claim** (TRACK + Delay Time / Reverb Size) is not declared: the claims' vocabulary has no names for
  knobs 8 to 15 yet (§11.8).
- **The standard** (step 5 of §15.9).

## 20. The standard: draft 0.6 (2026-10-27)

The maintainer, 2026-10-27: « Ja, schreib das Effekt-Format in den Cycles Mod Standard. » Step 5 of §15.9, the
explicit order the rule "the standard is not changed" asks for. Written in `cycles-mod-standard/` as its draft 0.6:

- **`STANDARD.md`**, draft 0.6: the terms *effect* and *slot* (§1); `fx.bus`, unmapped until 0.5, replaced by the
  rows `fx.delay` and `fx.reverb` (§3.1, table by id), the gesture TRACK + Delay Time / Reverb Size in the `gesture`
  row; the table rule with the effects' ids (§3.2), the effect slots as the builder's third part (§3.3), their limits
  (§3.4); **new §3.5, the effect slots**: the call, the line, the choice in the pattern header, the gesture, what is
  reserved (this note's §15 and §16 as built); §4.2 an effect's `build.roots`, its patch point `fx_line`, its entry in
  `uses`; **new §5.8 the effect ids** (1 Digital, 254 REFD, 255 REFR) and **§5.9 the pattern header** (OS 0–28 and
  38, the slots 29–31, Chord Keys 32–35 and 40–63, free 36, 37, 39); §6 the effects' cost and the rule per slot (§17);
  **new §7.5, Digital Delay's manifest** (this work copy's, tested); §8 to §11 brought up to date, "Decided in 0.6".
- **`README.md`**: the effect slots in the points' table, in the cost, the status and the decisions; note 68 read.
- **`APPLYING.md`**: the mixer's calls mapped to `fx.delay` / `fx.reverb` (§4); **new §13, porting an effect** to
  model27's builder, with Digital Delay as the template (object, call, line, manifest, cost, proofs, not allowed, a
  prompt).

Its links to model27's `notes/68-fx-slots.md` and `tools/machines/digidelay/manifest.json` hold once this work is in
model27's repository. The status line says "draft 0.6, 2026-10-27", without "public": it becomes public with its
push.
