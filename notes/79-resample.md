# 79 — RESAMPLE: a track, the main mix or USB recorded to a sample

A builder's part `resample` (`tools/machines/resample/`, `compose.py --resample`, also without packages), its host build
`tools/emu/resample_host.py` and its proof `tools/emu/test_resample.py`. This note is the plan with the maintainer's
decisions of the same day; step R1, the capture into RAM, is built and proven in emulation (§9). The page was decided on
a clickable mockup (local, not in the repository). Addresses: VAs of the Model:Cycles OS 1.13 MAIN OS (base
`0x40000400`); `[FAIT]` read in the code or tried on the machine, `[HYP]` to read or prove first.

The maintainer (2026-11-03): « prüf mal ob es möglich wäre, wenn man bei gestopptem seq "trig preview" nutzt, dass
gespielte audio aufzuzeichnen und als sample zu speichern », then « wäre es sogar möglich usb, Master oder spur
auswählbar zu machen? dann bräuchten wir eine view die nach der tastenkombi angezeigt wird, die den sample vorgang
aktiviert. da könnten auch die einstellungen bzgl. start der aufnahme rein », and « settings+record fände ich besser ».

## In short

- **SETTINGS + RECORD opens a page of its own**, RESAMPLE. Eight knobs set the source (T1–T6, MAIN, USB), how the take
  starts (TRIG, LEVEL, NOW) and LEVEL's threshold, stereo, how it stops (SILENT, LENGTH, RECORD) and its length, NORM
  and TO TRACK. **RECORD on the page arms**, and again cancels or stops.
- **The take starts on its own**: with TRIG, on the block where the source track is triggered, by Trig Preview (a held
  trig + PAGE, drumkilla's file unchanged), by a trig key played as a note or by MIDI; with LEVEL, when the source
  passes the threshold; with NOW, at once.
- **When it ends, the stock name editor asks for its name** (prefilled with the next free `REC-001`, …); the take is
  saved in `/recordings/` as a sample file in the format SAMPLE plays, and the page closes with `SAVED <name>`. Two
  switches: **NORM** (to the peak, or as heard) and **TO TRACK** (the take becomes the selected SAMPLE track's sample).
- **Where the audio is taken** `[FAIT]`: around the mixer's call `0x40059872`: a track before it, the main mix and USB
  after it. No offered card takes that place.
- **A builder part** `resample` like the CPU page's (notes/78), whose page mechanics it follows; both follow Model-TG's
  (TinyGregAudio, MIT), which records a track, the master or USB on the Model:Cycles and saves to the +Drive.

## 1. What the stock OS does with SETTINGS and RECORD `[FAIT]`

- **The key scanner** (`0x4007fbde`) gives each event flags at `+16`: bit 0 press, 1 FUNC, 2 double press, 3 repeat, **4
  a tap** (the release of the key pressed last, no other key pressed in between), **5 a long hold** (the timer
  `0x4007f914`, registered at `0x4007fe66`; the hold time `0x40148cc8` is set at run time). Predicates `0x40072434` (bit
  4), `0x40072444` (bit 5). A press moves the hold timer to the new key (`0x4007fcb6`).
- **SETTINGS** (MainScreenView, code 13, `0x4001c54c`): a tap opens the settings menu (`0x40077da8`), FUNC + a tap
  `0x4001040e`; a long hold asks to save the project (`0x40039570`, "Unsaved Project. Save to empty slot?"). The
  maintainer on the machine: the question comes after **1 s**. No stock code asks whether SETTINGS is held
  (`isKeyHeld(13)`).
- **RECORD** (code 9): PatternGridView (`0x400225c2`) takes it only with PAGE held ("Copy Page") or a held step ("Copy
  %d Trig%s"); otherwise the transport handler (`0x4002439a`) toggles GRID RECORDING on the press, without FUNC
  (`0x40024482`: `0x4006ba90(0)`, then the toggle `0x4006ba20`).
- **So SETTINGS + RECORD toggles GRID RECORDING** and SETTINGS is not read. The release of SETTINGS after RECORD is not
  a tap, so the settings menu stays closed `[FAIT from the scanner; to prove, Model-TG swallows that release anyway]`. A
  long hold before RECORD still asks to save, as in the stock OS: RECORD within the second avoids it. Kept so.

## 2. The page

### 2.1 Opening and closing

- `jsr rs_key` at `0x40024482` in place of the two stock calls: with SETTINGS held, open the page (or close it when it
  is up) and leave GRID RECORDING as it was; else the stock calls. In GRID RECORDING the press reaches this place only
  without PAGE and without a held step (§1), so Copy Page and Copy Trigs stay.
- The page closes with RETURN (code 12: the stock OS closes the MACHINES list with it on a tap, `0x400a292c`; Model-TG
  calls it "return", in lower case, as a key without a printed name; which key it is on the panel: to confirm) or
  SETTINGS + RECORD. Closing while armed cancels; closing while recording stops and opens the name editor `[À DÉCIDER]`.
  After the save the page closes by itself (the maintainer, 2026-11-03).
- Built as the CPU page (notes/78 §2, §9): the stock machine-select page (`0x400a22b0`), its first two vtable pointers
  at a private copy of the group `0x40117918..0x401179c8` with our key handler (`+0x08`), render (`+0x10`), encoder
  handler (`+0x44`, and its thunk) and destructors; presented with `0x4007700e` and a holder (vtable `0x401000c4`). The
  page code is shared with the CPU page once that is proven (step 2 of notes/78).

### 2.2 Keys on the page

| Key | Idle | Armed | Recording | Name editor | Unsaved | Saving |
|---|---|---|---|---|---|---|
| RECORD | arm | cancel | stop, then the name editor | the editor's own keys | the name editor again | nothing |
| RETURN | close | cancel, close | stop, then the name editor | back to the page, the take kept: Unsaved | drop the take, close | nothing |
| SETTINGS + RECORD | close | as RETURN | as RETURN | as RETURN | as RETURN | nothing |
| every other key | passed on | passed on | passed on | the editor's | passed on | passed on |

The Recording, Name editor and Unsaved columns are a proposal (2026-11-03), for the maintainer to try in the mockup:
nothing is lost by a key pressed once; only RETURN on the Unsaved page drops a take.

- **Passed on** = to the stock view dispatch `0x40075f3c` and from there to the views below `[HYP]`, as the MACHINES
  list passes PUNCH and GATE on (tried on the machine, K3). That is how a held trig + PAGE reaches PatternGridView and
  Trig Preview plays under the page; with GRID RECORDING off, the trig keys play notes. To prove first (§6).
- GRID RECORDING has to be on for Trig Preview; the page leaves it as it was.

### 2.3 The eight knobs

| Knob | Setting | Values | Default |
|---|---|---|---|
| PITCH | SOURCE | T1 … T6, MAIN, USB | the selected track |
| DECAY | START | TRIG, LEVEL, NOW (USB: LEVEL, NOW) | TRIG (USB: LEVEL) |
| COLOR | THRESH, LEVEL's threshold | −60 … −12 dB, 3 dB steps | −40 dB |
| SHAPE | STEREO | OFF, ON (a track is mono: OFF only) | OFF |
| SWEEP | STOP | SILENT, LENGTH, RECORD | SILENT |
| CONTOUR | LENGTH: the longest take, with STOP LENGTH its length | 1 … 20 s stereo, 1 … 40 s mono (§3.3) | 10 s |
| the knob after CONTOUR | NORM | OFF (as heard), ON (the peak to −0.3 dBFS) (§3.3) | OFF |
| the next one | TO T*n* (the selected track) | NO, YES (§4); `--` when the selected track does not run SAMPLE or the build has no SAMPLE | NO |

- **The two switches** (the maintainer, 2026-11-03: "on/off switch anbieten", "als Option ja/nein anbieten") sit on
  **the two knobs after CONTOUR in the panel's second row** (the maintainer, 2026-11-03). Which knobs those are: DELAY
  SEND and REVERB SEND (the maintainer, 2026-11-03), encoders 8 and 9 in `tools/claims.py`. The page's encoder handler
  must take them itself, or they change the sends as on the stock page (to prove, §6).
- **A value that does not apply shows `---`** (the maintainer, 2026-11-03), as the Track FX show it (notes/73 §19):
  STEREO with a track as the source, THRESH without START LEVEL, TO T*n* without a SAMPLE track; its knob then changes
  nothing. A few comparisons when the page redraws, in the UI task: nothing in the audio.
- Changed only while idle; armed and recording they are shown, not changed. DATA does nothing otherwise (on the machine
  page it changes the machine).
- TRIG with MAIN: any track's trigger. The values stay until the machine is switched off, in RAM only (the maintainer,
  2026-11-03).

### 2.4 What the page shows (128 × 64, mockup)

- **Idle**: the eight values **as the knobs lie** (the maintainer, 2026-11-03: the second row starts at SWEEP, the
  switches on its two free knobs): SOURCE, START, THRESH, STEREO on PITCH, DECAY, COLOR, SHAPE in four columns of 32
  pixels, under them STOP, LENGTH, NORM and TO T*n* on SWEEP, CONTOUR, DELAY SEND, REVERB SEND; `RECORD: ARM`, `RETURN:
  CLOSE`. A value is at most 29 pixels wide in the mockup's narrow font, hence SILENT rather than SILENCE.
- **Armed**: `WAIT FOR TRIG` / `WAIT FOR LEVEL`, under it the source and how the take ends (`T3 MONO    STOPS WHEN
  SILENT`, `STOPS AT 10S`, `RECORD STOPS`), the source's level meter with the threshold's mark, `RECORD: CANCEL`.
- **Recording**: `REC` and the seconds, the meter, a bar up to LENGTH, `CLIP` if a sample clipped, `RECORD: STOP`.
- **Naming**: the stock name editor (§4), prefilled with the next free `REC-nnn`.
- **Saving**: `SAVING` and a bar; then the page closes and the stock popup says `SAVED <name>` (as "Copy Page",
  `0x4002283c`).
- **Header** (the maintainer, 2026-11-03): `RESAMPLE` on the left (SAMPLE is the machine's name), the state on the right
  only while something happens (`ARMED`, `REC`, `UNSAVED`, `SAVING`); nothing when idle.
- **Unsaved**: `NOT SAVED`, the take's length and channels, `RECORD: SAVE`, `RETURN: DISCARD`.
- **Errors**: `DRIVE FULL`, `SAVE FAILED`; `FULL` when the buffer ends a take (it is saved).
- Redraw: as the CPU page redraws itself (notes/78 §8, its step 3), from the page's own periodic method (the view
  stack's `+0x2c`, called on the OS's timer): `0x40076082(page)` about 20 times a second while armed or recording (the
  meter), twice a second otherwise; no tick of the screen to share.

## 3. The audio

### 3.1 Where `[FAIT]`

The audio block's function calls the mixer at `0x40059872` (`jsr 0x400567ba`, the main output `0x4a3ed080 + (a3[40] <<
8)`, a2 the smoothed parameters). `rs_mix` takes that call:
- **before** the mixer: the tracks' buffers `0x80001858 + 128 t` (32 × int32, mono), after Volume + Dist and the filter
  slot (notes/72 §2), before level, pan and the sends: the track **dry**;
- the mixer: `jsr 0x400567ba` with the stack it expects;
- **after**: the main bus `0x8000b990` (32 × {L, R} int32, scaled ×4 in place at `0x40056b42`, without USB), and USB
  `0x8000b990 + 256` (copied there at `0x40056b48` from `0x40fe4cf0`, which `0x40002ae0` fills at `0x40059338`, only in
  the USB audio mode).
- `*(a3 + 16)`: the tracks triggered in the block (notes/72 §2), for TRIG.

Under `OFFERED` nobody takes `0x40059872` (only `syntakt-tg-*` 1/33 and Model-TG, neither offered). Cost: about 10
instructions a block idle, about 120 armed or recording (a copy of 32 or 64 values with peak and clip), counted later.

### 3.2 Start and stop

- **TRIG**: the take starts with the block whose source bit is set in `*(a3 + 16)` `[HYP]`: that Trig Preview's event
  (`0x40092116`, field +12 = 2) sets it; the proof shows it (§6), else TRIG falls back to LEVEL at −60 dB.
- **LEVEL**: a ring of 256 frames runs while armed (as Model-TG's `RS_EARLY`); the take begins 256 frames before the
  first sample over THRESH, so the attack is whole.
- **NOW**: the next block.
- **SILENT**: once 50 ms are in, the take ends after 250 ms below −72 dBFS; the tail after the last block over −90 dBFS
  is cut. **LENGTH**: at CONTOUR's length. **RECORD**: on the press. Every mode also ends on RECORD and when the buffer
  is full.

### 3.3 The buffer and the level

- RAM `0x42800000..0x43000000` (8 MiB; free in the stock OS, Model-TG checked the region on the machine; `memory.ram`
  claim, no offered card holds it): the take **in 32 bits**, as the mixer has it, stereo interleaved: 43 s mono, 21 s
  stereo; LENGTH up to 40 s mono, 20 s stereo. 32 bits because of NORM: a quiet take scaled up after a 16-bit capture
  would keep the coarse steps of 16 bits at its low level.
- At the save, piece by piece into s16 big-endian: **NORM OFF** by a shift per source, chosen so that a take replays on
  a SAMPLE track at the level it was heard (SAMPLE plays `s << 15`, notes on One-Shot; the factors measured in
  emulation, as Model-TG measured its bus factor 0.382 `[À MESURER]`), with saturation; **NORM ON** by one gain that
  puts the take's peak (kept while recording) at −0.3 dBFS. `CLIP` on the page when a sample would pass full scale with
  NORM OFF.

## 4. The save

- **Format** `[FAIT]`: the uploader's and SAMPLE's: header +1 stereo flag, +4 audio bytes, +8 48000, +0x10 frames − 1,
  +0x14 `0x7F000000`, then the PCM, then 16 zero bytes. One-Shot reads stereo files (header +1 = 1) and mixes them to
  mono as they load (`machine/pool.c`).
- **Only in the UI task**, from a periodic point there (the screen's tick `0x400075f0`, chained, or the page's own
  periodic method if it runs in the UI task: `[HYP]`, to read in R3): the stock FileWriter (ctor `0x4007c7ca(fw, path,
  size)`, which makes the folder; vtable +0x10 write, +0x14 commit, +0x18 abort and delete; dtor `0x4007c76a`; object
  0x8110 bytes), 32 KiB a tick (a write past its 32-KiB buffer drops the rest, so exactly that). The FileWriter mutes
  the audio while it lives, as every stock save; with the sequencer stopped that is a short silence. Model-TG's way
  around it is not taken in the first version.
- **Name** (the maintainer, 2026-11-03: the name editor): the stock name editor ModelsNameView, as the pattern and
  preset renames (`0x4002c92a`, `0x400a516e`): ctor `0x40041152(view, title, name, prompt, 0, 12, draw, save)` (0xac
  bytes), presented with `0x40076220(parent, view, 0)`, the save callback given the name (from Model-TG's notes, to read
  in our OS); up to 12 characters, prefilled with the first free `REC-nnn` (open `0x4007bc5e` "r" fails). The file:
  `/recordings/<name>`. Proposal (2026-11-03, to try in the mockup): a name that exists keeps the editor open with `NAME
  EXISTS`, nothing is overwritten; backing out of the editor goes back to the page with the take kept (Unsaved, §2.2).
  The OS hashes the file on close.
- The file then shows in SAMPLE's browser like any uploaded sample.
- **TO TRACK** (the maintainer, 2026-11-03: offered as an option): after the commit, the file's hash (the open file's
  entry, `0x4007cdd4` `[HYP]`) goes into the selected track's sound the way SAMPLE's browser puts a file there (name
  into `sound + 4`, `0x400a6650`; SAMPLE's key; its loader then fills a pool slot). Only with SAMPLE in the build and on
  a SAMPLE track; the part calls SAMPLE's code, so the composer links the two (to design in R3).

## 5. Packaging and conflicts

- **Builder part** `tools/machines/resample/` (part.json, C, entries.S), added by compose.py like `cpu`; a card of its
  own (experimental until the maintainer's test). The Cycles Mod Standard is not touched.
- **Claims**: `audio` at `0x40059872`; the key site `0x40024482`; the combination SETTINGS + RECORD (situation any;
  replaces "toggles GRID RECORDING, SETTINGS not read"); `memory.ram` `0x42800000..0x43000000`; the tick, chained, if
  the save needs it (§4).
- **claims.py**: `KEYS["SETTINGS"] = 13`, `KEYS["RETURN"] = 12`; stock entries SETTINGS (a tap opens the settings menu),
  SETTINGS held 1 s (asks to save the project), SETTINGS + RECORD (toggles GRID RECORDING).
- **The key map** (the key map of 2026-10-31, notes/72's opening: a mod takes a place in a level, never a held key of
  its own): SETTINGS becomes a row of its own, "the device", with + RECORD the SAMPLE page; rule 1 ("no held key of its
  own") then names it.
- Against the offered cards (`sampler`, `digidelay`, `pots`, `smpfilter`, `crush`, `ring`, `reso`, `eq`,
  `control-all-config`, `trig-cond-order`, `trig-preview`): no shared write; the tick chained if the save needs it; the
  CPU page's row in the settings list is another place. With Model-TG (not offered): the same combination and
  `0x40059872`, a computed conflict.

## 6. Proof (plan; Unicorn, the maintainer's run)

1. The hook: audio bit for bit as without it while idle; the take equals the track's, main's or USB's buffer block for
   block.
2. **TRIG with Trig Preview**: the real PatternGridView, drumkilla's cave and the audio block: the held step + PAGE sets
   the track's bit in `*(a3 + 16)` in the block the voice starts (the `[HYP]` of §3.2).
3. The combination: SETTINGS + RECORD through the real transport handler opens the page, GRID RECORDING unchanged, the
   release of SETTINGS opens no settings menu; RECORD alone still toggles, Copy Page / Copy Trigs stay.
4. Passing on: with the page up, a held trig + PAGE builds the preview's event (the `[HYP]` of §2.2).
5. Host tests (cc): header, s16 conversion and saturation, start and stop logic, SILENT's cut, the ring for LEVEL.
6. The save in digiemu: the file on the drive image (`tools/ekfs.py --ls`), SAMPLE plays it; then the machine.

## 7. Steps

| Step | What | Done when |
|---|---|---|
| R0 | The maintainer decides §8 and the page (mockup) | answers |
| R1 | Audio capture and start/stop in RAM, host tests, proofs 1, 2, 5 | ALL OK; **built 2026-11-03** on branch `resample` (worktree `model27-resample`, from `22704dc`): the part `tools/machines/resample/` 0.1, `compose.py --resample`, `tools/emu/resample_host.py` ALL OK, the device object against the host build in cfemu (`_scratch/resample/cfcheck/`) ALL OK, `tools/emu/test_resample.py --dry` ALL OK; **the Unicorn run (proofs 1, 2) ALL OK in the maintainer's terminal (2026-11-03)**: Trig Preview's event starts the take in the block after it, the one whose frame +16 has the track's bit (`[FAIT]` now); 659 to 1 112 instructions a block for main mono, 848 to 1 600 for USB stereo; nothing committed |
| R2 | The combination and the page (idle, armed, recording), proofs 3, 4 | ALL OK, tried on the machine |
| R3 | The save, the saved state, errors; digiemu, the machine | the take plays on SAMPLE |
| R4 | The card, the guide, a release | live |

## 8. To decide

Decided by the maintainer (2026-11-03):
- the name editor at each save; NORM as a switch; TO TRACK as a switch; the page closes after the save; the settings
  only until power off; RETURN is the key's name; the switches on the two free knobs of the second row; the header
  (§2.4).

Still open:
1. The proposal for RETURN while recording, backing out of the name editor and a name that exists (§2.2, §4): the
   maintainer tries it in the mockup.

The order (the maintainer, 2026-11-03): SOURCE, START, THRESH, STEREO in the first row; STOP, LENGTH, NORM, TO T*n* in
the second.

The labels (the maintainer, 2026-11-03): LENGTH rather than MAX; CHN was unclear, so SOURCE and STEREO OFF/ON are spelt
out.

## 9. Step R1: the capture into RAM (2026-11-03)

The maintainer (2026-11-03): « Ja, R1 starten ». Built on the branch `resample`, from `22704dc`:

- **The part** `tools/machines/resample/` 0.1 (`resample.c`, `entries.S`, `part.json`, `resample.o` by
  `tools/gen_parts.py`): `rs_mix` at `0x40059872` (§3.1), the recorder (§3.2, §3.3) and the UI task's functions for the
  page and the save (`rs_arm`, `rs_stop`, `rs_cancel`, `rs_release`, `rs_header`, `rs_norm`, `rs_pcm16`); no page yet,
  nothing on the drive. The data block (64 bytes): the take's buffer `0x42800900`, 2 096 576 words, the ring
  `0x42800000` (nine blocks of 64 words, 2 304 bytes), the shifts 0 for the three kinds of source until the levels are
  measured. 2 650 bytes of code, no EMAC instruction, no library call.
- **The composer**: `compose.resample_layer` and `compose(..., resample=True)` (`--resample`), the RAM claim checked
  against the payload and every package's claim, declared as the part's claim (`ram`). Not yet in
  `docs/flasher/composer.js`: it comes with the card (R4).
- **Host build** (`tools/emu/resample_host.py`, cc and python3): the data block's layout, arming, idle and taken, the
  three starts with the ring, main and USB in stereo and mono, the four ends with the tail's cut, the peak, the header,
  NORM, the 16-bit words: ALL OK `[FAIT]`.
- **The device object against the host build** in `_scratch/cfemu` (`_scratch/resample/cfcheck/check.py`, local):
  `resample.o` linked at `0x43000000` with a stand-in mixer at `0x400567ba`; `rs_mix` hands the mixer its arguments and
  stack as the call replaced, d0 back, d2-d7/a2-a6 kept, 7 instructions idle; six scenarios (a track with RECORD, main
  stereo with LENGTH 1 s, main mono with TRIG, USB stereo with LEVEL and the ring, a track with SILENT and the cut, a
  full buffer) the same state each block and the same take, bit for bit; the save's functions the same: ALL OK `[FAIT]`.
- **The proof** (`tools/emu/test_resample.py`, Unicorn), the recorder alone, with `sampler,smpfilter,digidelay` and with
  `crush,pots,cpu`: the build (`--dry`, here); idle, the whole audio interrupt the same memory, registers and EMAC with
  7 instructions more a block; recording a track, main stereo, main mono and USB stereo, everything outside the recorder
  the same as without it and the take the signal block for block; Trig Preview's event (as drumkilla's code builds and
  sends it) starting the take in the block whose frame `+16` has the track's bit, the block after the event, the track
  silent before it. **ALL OK in the maintainer's terminal (2026-11-03)** `[FAIT en émulation]`: the `[HYP]` of §3.2
  holds.
- **Cost** (the proof's count): 659 to 1 112 instructions a block for main mono, 848 to 1 600 for USB stereo, about 1 %
  of a block; once about 7 800 in the block a LEVEL take starts in (the ring's copy, counted with cfemu).
- Checked as well: `gen_parts.py --check` (the other parts' objects unchanged), `claims.py --check --self-test`,
  `check_overlaps.py`, `registry.py --check`, `gen_flasher_tweaks.py --check`, `test_cpu.py --dry`, `test_fltslot.py
  --dry`, `webcompose_check.sh`, `py_compile`.

Next: R2, SETTINGS + RECORD and the page (§2, proofs 3 and 4).
