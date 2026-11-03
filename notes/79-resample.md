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

## 10. Step R2: SETTINGS + RECORD and the page (2026-11-03)

The maintainer (2026-11-03): « Ja, R2 starten ». The part's 0.2 on the branch `resample`:

- **The combination** `[FAIT]`: `0x40024482` (TransportView's `clr.l -(sp) ; move.l d3,-(sp) ; jsr 0x4006ba90 ;
  move.l d3,-(sp) ; jsr 0x4006ba20 ; lea 12(sp),sp`, 22 bytes) becomes `move.l d3,-(sp) ; jsr rs_key ; addq.l #4,sp`
  and six nops, the stock `bra 0x40024650` after them; nothing in the OS branches into the nops. `rs_key` makes the two
  stock calls itself unless SETTINGS is held, then the page opens and GRID RECORDING stays as it was. TransportView is
  named by the OS's own RTTI (`13TransportView`, vtable `0x40100fec`, its keys `0x4002439a`).
- **The page** (`page.c`): built and presented as the CPU page's (§2.1); its key handler, encoder handler, periodic
  method and render as §2.2 to §2.4 say. The settings live in the data block (now 256 bytes: the recorder's 64, then
  the page's pointer, the eight settings, SAMPLE's machine number, the vtable copy), set once at the first opening
  (the selected track, TRIG, -40 dB, mono, SILENT, 10 s) and kept until the machine is switched off. In R2 a finished
  take shows NOT SAVED and only RETURN (which drops it) does something with it: the save is R3's.
- **On the OS's fonts** (corrected in §10.2: the routine adds a pixel to each character, so 6 and 8): the small font
  is 5 pixels a character (`0x40140ab0`, its width table at `0x40140ac4`: every character 5), the medium one 7
  (`0x4014120c`). The four columns of 32 pixels take six characters
  (SOURCE, THRESH, STEREO, SILENT, RECORD, LENGTH: 30 pixels). The mockup's armed line « T3 MONO    STOPS WHEN SILENT »
  is 140 pixels in the OS's font: the page writes it on two lines (« T3 MONO », « STOPS WHEN SILENT »), and the armed
  footer keeps « RECORD: CANCEL » alone (with « RETURN: CLOSE » it would be 135 pixels). The text is drawn without the
  OS's box cleared behind it (flag 0x10): that box took the last row of the line above (the first proof's screens
  showed it), and the page clears the whole screen first anyway.
- **claims.py**: SETTINGS is key 13; two stock entries (SETTINGS: a tap opens the settings menu, held the question to
  save the project after 1 s; SETTINGS + RECORD: toggles GRID RECORDING, SETTINGS not read); the part claims
  SETTINGS + RECORD with what it replaces. `REGISTRY.md` regenerated.
- **Built with `-fno-jump-tables`**: the part's switches as compare chains, which the local interpreter runs.
- **Checked here**: the host build ALL OK; in cfemu (local, `_scratch/resample/cfcheck/page_check.py`, the OS's calls
  stood in for at their addresses) `rs_key` with and without SETTINGS, the key handler, the encoder handler, the
  periodic method and the render's text calls and pixels: ALL OK, and the recorder against the host build again
  ALL OK; `test_resample.py --dry` ALL OK; the repository's checks.
- **The proof** (`test_resample.py` parts 5 to 8, Unicorn): the combination on TransportView's own handler, the key
  scanner's events for SETTINGS, the page function by function, the render into the OS's Bitmap with its fonts
  (`--show` prints the four screens). **ALL OK in the maintainer's terminal (2026-11-03)**, the three selections,
  after a second run: the first one's part 6 stopped in the bench (it hands every key event to PatternGridView, whose
  RECORD reads memory the bench does not set up; the bench's PatternGridView is now stubbed there), and its screens
  showed the clipped rows (the text's flags since). The scanner: SETTINGS' release after RECORD is a plain release
  (flags `0x0`), the long hold on this bench's key clock at 537 ms (the machine: 1 s) `[FAIT en émulation]`.
- **Next**: the machine (R2 done when tried there), then R3.

### 10.1 The first try on the machine: SETTINGS by its events (2026-11-03)

The maintainer: « Geht nicht auf »; SETTINGS + RECORD toggled GRID RECORDING, the RECORD LED lit as without SETTINGS.

- **What the device ran** `[FAIT]`: the device file has the hook at `0x40024482` (`move.l d3,-(sp) ; jsr rs_key`) and
  `rs_key` at its place (`pea 13 ; jsr 0x4007faf4 ; tst.l d0 ; bne` the page, else the two stock calls); GRID
  RECORDING is toggled only there (`0x4006ba20` has no other caller; `0x4006b9f6` also from `0x40024510`, PLAY with
  RECORD held; UIStates +358 is written only at `0x4006ba08`, `0x4006bb0a` and in the constructor `0x4006c488`). So
  isKeyHeld(13) answered 0 when RECORD's press was read.
- **The key path** `[FAIT]`: stock in the build (nothing written in the key interrupt `0x40059e64`, the scanner
  `0x4007fbde` or isKeyHeld `0x4007faf4`); code 13 is bit 6 of row 0 both ways (`0x4010ae5c`, `0x4010aef8`); the
  bitmap `0x40f95744` is written only by the scanner, with the row as the key interrupt read it (four rows of the
  panel's eight bytes at `0x40a791cc`; the other four are the encoders). Why isKeyHeld(13) was 0 there is not found
  `[HYP]`. Model-TG, whose SETTINGS + RECORD works on the machine, does not ask isKeyHeld for SETTINGS: it keeps it
  from SETTINGS' own events, read through the key code accessor (its `key_hook`, `set_held`). PPPCCC asks
  isKeyHeld(13), but was tried on a Model:Samples.
- **The fix, Model-TG's way**: the key event's code accessor `0x4007240c` (`movea.l 4(sp),a0 ; move.l 12(a0),d0 ;
  rts`, which every key handler calls; TransportView at its start for every key) becomes `jmp rs_code`; `rs_code`
  returns the same code and, on SETTINGS' events, keeps their flags' bit 0 (down: a press, its repeats, its long hold;
  up: the release, the tap) in the data block's `set_held` (+79). The events are read in the order the keys were
  pressed, so SETTINGS' press is read before RECORD's. `rs_key` and the page's SETTINGS + RECORD take
  `isKeyHeld(13) || set_held`. Only a0 and d0 are touched, as by the stock accessor, and the condition codes are the
  same (its `move.l 12(a0),d0` last); 4 instructions more per read of a code, 7 for SETTINGS'. Model-TG takes the
  same 6 bytes: the composer counts `model-tg` and `model-tg-st` among the conflicts (both are not offered).
- **Proven here**: `test_resample.py --dry` ALL OK (the new write, the takers of `0x4007240c` among the conflicts);
  in cfemu on the part's object with the stub of `0x4007240c` as the build's `jmp rs_code`: the accessor's code and
  `set_held` for ten events, `rs_key` after SETTINGS' press (the bitmap up: the page) and after its release (the
  toggle), SETTINGS by its event + RECORD on the page: ALL OK; the repository's checks. In Unicorn (parts 5 and 7,
  the maintainer's run): the device's case on TransportView's own handler (the bitmap up, SETTINGS' press or long hold
  read before RECORD's: the page; its release or tap: the toggle), the accessor against the stock one for 63 events
  (d0, d1-d7/a1-a6, the condition codes, the stack, `set_held`), and SETTINGS by its event + RECORD on the page.
- **The maintainer's Unicorn runs (2026-11-03)**: all of it ok but the accessor's comparison, in the three selections;
  `--keys` (new: the build and the key parts only) showed why: d0, the registers, the stack, `set_held` the same, only
  the condition codes differed, read through Unicorn's SR after the run, which does not show what the last
  instruction set (the stock accessor's `move.l`, which clears V and C, read back with the V and C written before it)
  `[FAIT]`. The proof now reads them on the CPU: the accessor returns into `move.w sr,d7` (a second call of the same
  event). In cfemu (local, `_scratch/resample/cfcheck/acc_check.py`, which sets the flags instruction by instruction)
  the stock accessor and `rs_code` leave the same condition codes for the 63 events. **`--keys` then ALL OK**, the
  three selections (the audio parts were ok in the full run before, on the same build).
- **The machine (2026-11-03)**, the build `sampler` + `trig-preview` + RESAMPLE (MAIN OS `76d596ea…`): SETTINGS +
  RECORD opens the page (the maintainer: « geht auf »). The other tests of R2 follow one by one.

### 10.2 The screen in the mockup's fonts (2026-11-03)

The maintainer's photo of the page: the labels ran into each other (SOURCE into START, LENGTH into NORM, SILENT into
10S), STEREO was cut at the right, the footer's halves overlapped, and « they are all the same size, unlike in your
mockup ».

- **Why** `[FAIT]`: the OS's text routine counts a character as its width plus one (`0x40072102`: `(w + 1) × n − 1`
  without a width table, the widths plus `n − 1` with one), so its small font is 6 pixels a character, not 5: a
  column of 32 takes five, and SOURCE, THRESH, STEREO, LENGTH, SILENT and RECORD are six. The emulated render was right
  (the OS's own routine); its checks looked at rows and boxes, not at where one word ends and the next begins.
- **The mockup's fonts were its own** (3 × 5 at 4 pixels a character for the labels, the state, the footer and the
  small lines; 4 × 7 at 5 for the knobs' values; 5 × 7 at 6 for the title and the big lines), not the OS's. The page
  now draws them itself (`page.c`: 44 characters, A-Z, 0-9 and `-.:/%+> `, 412 bytes of glyphs) at the mockup's
  coordinates, and no longer calls the OS's text routine. With them the mockup's layout comes back whole: the armed
  line on one line (« MAIN STEREO    STOPS WHEN SILENT », 127 pixels), both halves of every footer, « OF 10S » under
  the seconds while recording, and « CLIP » after it when the take reached full scale (its peak's `rs_db` 0). The
  taken screen keeps its footer's left half empty until the save (R3). Code 12 413 bytes (+1 749).
- **The proof** is now pixel for pixel: `tools/emu/resample_screens.py` draws the mockup's screens in Python (its
  fonts from the mockup's own strings, its coordinates), and `test_resample.py` part 8 compares the part's render into
  the OS's Bitmap with them in nine states (idle with a track, with MAIN stereo and TO Tn, with USB; armed with LEVEL
  and with TRIG; recording, and clipped; taken mono and stereo). In cfemu (local `page_check.py`, the same nine): ALL
  OK. Build `sampler` + `trig-preview` + RESAMPLE: MAIN OS `e1592479…`, elektron-firmware-tool ok. In the
  maintainer's terminal (`--keys`, 2026-11-03): part 8's nine screens ok in the three selections, as far as the lines
  sent show. On the machine (2026-11-03, the build `e1592479…`): the page as the mockup and its eight knobs, the `---`
  where a value does not apply: « passt »; RECORD arms (ARMED, WAIT FOR TRIG, the meter) and cancels: « passt »;
  TRIG + PAGE under the page plays the step (Trig Preview), the page stays: « passt »; armed for TRIG on the track,
  TRIG + PAGE starts the take, SILENT ends it on its own, NOT SAVED with its length: « passt »; RECORD on the taken
  screen does nothing, RETURN drops the take and closes the page, it opens again with the settings kept: « passt ».
  **R2 done on the machine (2026-11-03).** Next: R3 (the name editor, the save, TO Tn, NORM).

## 11. Step R3a: the name editor and the save (2026-11-03)

The maintainer: « Ja, R3 starten ». R3 is cut in two: **R3a** (this section) names and saves a take, with NORM;
**R3b** puts it on the track (TO T*n*, through SAMPLE's code) and measures the levels "as heard" (§3.3). The part's 0.3.

- **The flow, as the mockup** (§2.2, its simulation): a take that ends (RECORD, RETURN, SETTINGS + RECORD while
  recording, SILENT, LENGTH) brings up the name editor once, prefilled with the first free `REC-nnn` (001 to 999, each
  tried with open "r"); confirmed, the take is written, the page shows SAVING with its progress, then it closes and
  the OS's popup says « Saved » and the name; a name that exists brings the editor back with the name typed and NAME
  EXISTS as its title, nothing is overwritten; backed out of, the page shows the take as NOT SAVED, where RECORD asks
  for the editor again and RETURN drops it. While the file is written RECORD and RETURN do nothing. An error (the
  FileWriter's +0x1c) aborts and deletes the file, the popup says « Save failed » and the take stays; so does a step
  that finds no free message (the UI task frees each after running it, so it is not expected), so that a SAVING page
  never keeps the FileWriter, and the mute, for ever.
- **In the UI task** `[FAIT dans Model-TG, sur la machine]`: every step runs there, as Model-TG's save does
  (TinyGregAudio, MIT; its `sv_post` / `sv_run`, `rs_name_open`, `rs_save_do`): a message of type 6 on the master UI
  task's queue `0x404a9154` (`0x400081fa`: its callback at +0x10 called with its closure +4 and its word +0x14, its
  +0x18 cleared after), each step posting the next on the other of two messages in the data block. Model-TG found that
  a save from the LED clock froze the audio, however it was cut; the page's periodic method only posts.
  - The editor `[FAIT]`: ModelsNameView as the pattern rename opens it (`0x4002c92a`, its title « Ptn Name », its
    prompt « Rename pattern to », the question on confirming): ours « Resample » (« Name exists » when the name given
    was taken) and « Save recording as », 12 characters,
    presented with `0x40076220(page + 0x38, editor, 0)`; its two std::functions `{data, 0, 0x4002f136, invoker}`
    (data from `0x40080064`), released with `0x400cf044` after the ctor copied them. The save invoker gets the name as a
    String (its characters at `*(char **)`), the spaces after it dropped, an empty one keeping the default.
  - The file: `/recordings/<name>` by the stock FileWriter (`0x4007c7ca(fw, path, size)` on 0x8110 bytes, which makes
    the folder; +0x10 write, +0x0c flush, +0x14 commit, +0x18 abort, +0x1c error; dtor `0x4007c76a`, delete
    `0x400802ec`): the header (64 bytes, `rs_header`), the frames in pieces of 16 384 words turned into 32 KiB of 16-bit
    (`rs_pcm16`: as heard `>> 16`, or NORM's shift and gain, `rs_norm`) in 32 KiB the composer keeps at the RAM claim's
    end (`0x42ff8000`, so the take holds 2 088 384 words), each written and flushed (a write only fills the
    FileWriter's 32 KiB buffer), then 16 zero bytes. Stereo is interleaved, as One-Shot reads it (`pool.c`). The
    FileWriter mutes the audio while it lives, as every stock save; Model-TG's way around it is not taken.
  - The popup `[FAIT]`: the OS's own (`0x400747c0` on 0x9c bytes, its holder `0x400fbf40`, presented as `0x4000d750`
    shows « Lock mem full! »).
- **The data block** grows to 512 bytes: +256 saving, asked, exists, act, which; +264 the name; +280 the path; +312 the
  FileWriter; +316 words written, +320 their total; +324 the shift, +328 the gain; +332 the 32 KiB (composer); +336
  the two messages (0x1c each).
- **The screens**: SAVING as the mockup draws it (the name, /RECORDINGS, the bar and the percent, WRITING TO +DRIVE),
  NOT SAVED with RECORD: SAVE on the left; `tools/emu/resample_screens.py` draws both.
- **Not in R3a**: TO T*n* (its knob is there, the save does not use it yet); the level "as heard" is full scale to
  16-bit full scale (`>> 16`, the shifts still 0) until R3b measures it; NORM is exact.
- **Proven here**: in cfemu (local, `_scratch/resample/cfcheck/save_check.py`: the part's object with stand-ins for the
  OS's calls at their addresses, the messages run in their order) the four cases of part 9 below: ALL OK; the page
  in cfemu (`page_check.py`, the new keys, the periodic method's one message, SAVING and NOT SAVED pixel for pixel):
  ALL OK; `test_resample.py --dry`, the host build, the repository's checks. In Unicorn, the maintainer's run:
  `test_resample.py` part 9 (the same cases on the composed build in the OS's image: RECORD on a take, the editor with
  REC-001 over the page; MYTAKE saved, the file byte for byte, committed, the page closed, « Saved »; KICK taken, the
  editor again with NAME EXISTS and no file, KICK2 saved; an error aborted, « Save failed », the take kept; NORM in
  stereo in five pieces; no free message, the file given up), part 7's one message, part 8's SAVING screen. Code
  15 862 bytes; build `sampler` + `trig-preview` + RESAMPLE: MAIN OS `ba791261…`, elektron-firmware-tool ok.
- **The maintainer's Unicorn runs of part 9** (2026-11-03): its first two stopped in the bench, not in the part (the
  render's test had left only the base's stand-ins, so the OS's own allocator ran; `rs_named` is no root, so its
  address comes from the part's symbols); the third ran the editor and the header, then nothing: part 7's periodic
  method had posted a message the bench never runs, so its busy flag stayed and the save's next step found no free
  message. cfemu shows the same with that flag set (64 bytes, then nothing) and the whole save with it clear. Part 9
  now frees both messages first, and the part gives the file up when a step finds none (above). **The fourth run
  (`--keys`): ALL OK**, the three selections, parts 5 to 9.
- **The machine, first try** (2026-11-03, `ba791261…`): the editor did not come up, neither when the take ended nor
  on RECORD: SAVE. `0x40076220(parent, view, x)` reads the parent's +0x2c and does nothing when it is 0
  (`0x4007622a`), and for our page (presented by `0x4007700e` on the views' screen) `page + 0x38 + 0x2c` is that; both
  proofs had stood in for `0x40076220`. The editor is now shown as the page is: `0x4007722a(TARGET(VIEWS()), editor,
  0)` (the generic holder `0x400fbf24`, then `0x4007700e`), and part 9 runs that routine for real (its `0x4007700e`
  stood in for: on the views' screen, the pair's view the editor). Build `2adb7f0b…`; the maintainer's `--keys`:
  ALL OK. **On the machine (2026-11-03)**: a take by Trig Preview, the editor up on its own with REC-001, confirmed,
  SAVING, the page closed, the popup « Saved REC-001 »: « passt »; the file in SAMPLE's browser, loaded and played:
  « passt »; REC-002 offered, REC-001 typed: the editor asks « Save recording as REC-001? » (YES / ABORT / EDIT: the
  prompt is that question, not a line over the name), YES brings the editor back, nothing overwritten; backed out of,
  NOT SAVED; RECORD the editor again; RETURN drops the take and closes: « passt ». So NAME EXISTS is now the editor's
  title (shown while the name is edited), the prompt stays « Save recording as » (build `080869eb…`; the
  maintainer's `--keys`: ALL OK); on the machine: NAME EXISTS as the title, NORM on a quiet take, the file loud and
  clean on SAMPLE: « passt ». **R3a done on the machine (2026-11-03).** The full proof (`test_resample.py` without
  `--keys`, parts 1 to 9) on that build: ALL OK in the maintainer's terminal, the three selections (idle the same
  with 7 instructions more a block, the takes of a track, main and USB, Trig Preview's start). Committed `8238fad`.

### 11.1 GRID RECORDING for Trig Preview (2026-11-03)

The maintainer chose « B: automatisch » over FUNC + RECORD on the page: armed for TRIG (START TRIG, a track or MAIN),
the page turns GRID RECORDING on if it is off, as TransportView's RECORD does (`0x4006ba90(uis, 0)` and the toggle
`0x4006ba20`, the UIStates from `0x400cf9a8`; on is `+357 && +358`, as its LED says), and notes it (`grid_set`, +261);
it turns it off again when RECORD drops the armed take, when the page closes, and with the first UI-task message after
the take ended (the editor's), so that it is as before the page armed. Already on, or START LEVEL or NOW: left alone.
Proven in cfemu (`page_check.py`: off then on then off with RECORD and with RETURN; on already; LEVEL; `save_check.py`:
off with the editor's message, not again in the save): ALL OK; in Unicorn part 7 (the same four cases, the stock
toggle stood in for as it works, `+358 = +357 && !on`) and part 9 (the editor's message): the maintainer's `--keys`,
ALL OK. Code 16 150 bytes; build `182839fa…`. On the machine (2026-11-04): GRID RECORDING off, armed for TRIG: the
REC LED on; RECORD again: off; armed, a take by Trig Preview, the editor up and the LED off again: « passt ».
- **The maintainer, the same day**: GRID RECORDING has to be on before the page opens, since Trig Preview plays only
  with it on and RECORD on the page arms instead of toggling it (§2.2). A point for the page, not the editor's cause;
  decided in §11.1.
