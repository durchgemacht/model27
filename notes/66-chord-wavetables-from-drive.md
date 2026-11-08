# 66 — CHORD plays wavetables from the +Drive, chosen with RETRIG + a knob (plan)

**Status: plan, 2026-10-23; the maintainer's decisions the same day: the six recommendations of §8 (§10). W1
prepared the same day (§11): three facts read in the code and one measured; the probe of the trig block,
`tools/emu/probe_chord_tables.py`, run by the maintainer: the sites and the event loop ok, the voice loop corrected
(§11.6: a note starts in the block with `v + 0x38` set, k 30 comes from the sound object); the second run ALL OK
(§11.7). W1 done. W2 built the same day (§12): the builder takes a package that extends CHORD, proven by REFC, the
reference extension; the builds that existed are unchanged, byte for byte; `tools/emu/test_refchord.py` ALL OK in the
maintainer's run (§12.4). W2 done. W3 built the same day (§13): the package `chordtables` and
`tools/gen_chordtables.py`, `36-chordtables.json`, composed alone and with SAMPLE. W4 prepared (§14):
`tools/emu/test_chordtables.py`, P1 `cw_setup` and P2 the loader, ALL OK in the maintainer's second run (§14.2):
W4 done. W5 built and W6 prepared the same day (§15): `tools/wavetable.py` (self-test ALL OK), the proof's cost part
and a converter-made file; the maintainer's third run ALL OK (§15.4), the cost in the manifest. Tested in digiemu by
the maintainer on 2026-10-24 (§15.7): "getestet, funktioniert". The device test is open.**

**Later: 0.2 tested on the device and paused (§25, §26). 2026-11-05: a new way planned, one table per pattern in the
stock table's place (§27).**

The maintainer asked on 2026-10-23 whether a mod could let the stock CHORD machine load wavetables from the +Drive
and pick them with RETRIG + CONTOUR ("the exact knob does not matter"), or with FUNC + MACHINES as SAMPLE does. Two
ways were weighed the same day. Way A, a shortcut, is this plan ("weg a planen"). Way B, the browser, stays a later
option (§9).

Sources of the facts marked `[FAIT]`:
- the disassembly of MAIN OS 1.13 for this plan: `0x400a8060..0x400a80e6`, `0x400aae88..0x400aaeb4`,
  `0x400ab0f0..0x400ab170`, and the entries of `0x4007bc5e`, `0x4007bc1c` and `0x4007afd4`;
- notes/27 §3.3, 28 §2 and §4, 46 §2 and 63 §1 to §11;
- One-Shot's TECHNICAL.md §5, §7, §8 and §12;
- `tools/compose.py`, `tools/machines/shortcuts/` and `tools/machines/dispatch/part.json`;
- a scan of the 287 tweaks of `tweaks/model-cycles_OS1.13/`.

Model-TG's code (MIT) opens files by path. Its calls give the signatures of §1.4, which are still to be proven here.

Addresses: VA of OS 1.13.

## 0. In short

- **What the musician gets.**
  - Up to 64 wavetables on the +Drive, files `01` to `64` in a folder `/Wavetables`.
  - On a CHORD track, RETRIG held + SWEEP picks one: 0 is the stock table, 1–64 a file (§10).
  - SWEEP still moves through the table's frames, as on the stock machine. With a file, its whole range is the file.
  - The choice is saved with the sound. A new table starts at the next trig.
- **Where it goes into the OS.** CHORD's update gets its two frames through one call:
  - `jsr 0x400a8080` at `0x400ab15e`, with the voice and the parameters `[FAIT]`;
  - that call becomes a call to our setup;
  - at 0 our setup jumps into the stock function, so a CHORD track plays bit for bit as before;
  - otherwise it gives the voice the frames of the chosen table.
  - No tweak writes there today `[FAIT]`.
- **What is already built.**
  - The shortcut layer (notes/63 §11) shows, edits and saves the value, unchanged. It reads the machine range from its
    data block, so machine 5 needs no new code `[FAIT]`.
  - The loader follows One-Shot's tick (UI task, about 30 Hz).
- **What the builder lacks.** The composer only takes added machines:
  - `load_manifest` refuses a package without a `machine` entry `[FAIT]`;
  - the registrar has frames for 1 to 6 machines only `[FAIT]`.

  A package that extends a stock machine is new builder work (§3).
- **Cost.**
  - About +0,6 to +1,2 points of the audio block per CHORD track playing a loaded table: the frames are read in
    SDRAM, not SRAM. This is estimated (notes/27 §3.3, 28 §4), not measured.
  - The number of tables loaded costs RAM only: about 32 KB each.
- **On the official OS** a sound keeps the value in a record slot the stock load never reads (notes/63 §3.2), so it
  plays the stock table. The track stays a CHORD track: unlike an added machine, nothing must be switched back
  before flashing the official OS.

## 1. What the OS does `[FAIT]`

### 1.1 How CHORD gets its frames

| Where | What |
|---|---|
| `0x400aae88(pmod, v, p)` | CHORD's update. Same contract as every machine (One-Shot §5): `a2` = v, the track's voice (`0x42308828 + t · 0x31c`), `a3` = p, the note's parameters as 8.8 words |
| `0x400ab15e` | `jsr 0x400a8080` with (v, p); the only caller (notes/27 §3.3) |
| `0x400a8080(v, p)` | reads SWEEP at `p + 0x1a`: index = SWEEP >> 10 (0–31), crossfade = (SWEEP & 1023) << 21. Takes frames index and index + 1 through the selector, then for each of the four sub-voices (`v + 120 j`): the two frame pointers at `+168` and `+172`, the crossfade at `+156`, the index at `+184` (its previous value moved to `+188`) |
| `0x400a8060(index)` | index 1–32 → pointer `index − 1` of the table at `0x40118590`; any other index → the sine at `0x8000eee4`. Called PC-relative (`lea pc, a2 ; jsr (a2)`) |
| frames | 257 big-endian Q31 samples, one cycle, the last equal to the first (1 028 bytes). Pointer 32 repeats pointer 31 |

- The stock function is 102 bytes and only moves pointers and numbers into the voice. That other pointers are enough
  is proven: notes/28 §3 moved the frames and rewrote only the pointer table, and CHORD's output stayed identical.
- The Syntakt engines' 251 tweaks rewrite the 31 pointers at `0x40118594` to copies in their payload (notes/28 §2).
  They write nothing at `0x400a8060..0x400a80e6` or at the call. Since the stock path at 0 is the stock function, it
  follows their pointers too.

### 1.2 Which parameters the setup can read

- The voice loop's `p` holds k 0–32. The shortcuts' k 28–31 are at `p + 0x38..0x3e` (REF2 reads k 28 there,
  notes/63 §11).
- When a note's sound differs from the track's last one, the audio side copies its 66 bytes (k 0–32) to
  `0x800015ae + 66 · t`, before any smoothing (`0x40058a0a`). One-Shot reads its sample key from this copy at the
  trig.
- `v + 0x34` is set in the block of a trig, before update runs. `v + 0x00..0x3c` is cleared when the track changes
  machine (`0x400a7ab8`).
- The voice loop looks at the machine only in a block with `v + 0x38` set: the first note after a machine change
  starts one block late, and its trig flag is cleared by the reset. Measured on 2026-10-23, §11.6.

### 1.3 The shortcut layer, for machine 5

- `sc_knob` asks `TRACK_MACHINE` (`0x4001e318`) for the track's machine and subtracts `first`, a byte at
  `sc_data + 0x10`. It refuses a result below 0 or at least `count` (`+0x11`), then reads 4 entries of 24 bytes per
  machine.
- The composer writes `first` = 6 today (`compose()`, `first = 6`). With `first` = 5 and CHORD's entries first, the
  same object serves CHORD.
- It saves k 28–31 in record slots 28–31 for every sound and puts them back at the load, with SAMPLE's record
  wrappers chained behind it (notes/63 §11.2 points 5 and 8).
- The value is a shortcut's: no p-lock, no LFO destination, 0 by default (notes/63 §9, decision 1).

### 1.4 Reading a file from the UI task

- One-Shot reads by inode: `0x4007de78(ino, out)` and `0x4007baaa(buf, len, handle)`. It also has the lock rules:
  - the FS lock `0x40fe6df0` lets its holder in again but does not count;
  - the tick leaves the drive alone while the running task holds the lock or while `0x40f07cf4` = 0 (not mounted);
  - the redraw runs from two tasks, so the tick takes its own `tas` lock (One-Shot §7).
- The file index `0x401fb8a4` (count at `0x401fb8a0`) is built at mount and again whenever a file is finished. A
  file's id is a content hash: there is no path in the index.
- Open by path:
  - Model-TG's code calls `0x4007bc5e(path, "r", handle[16])`, then `0x4007baaa`, then `0x4007bc1c(handle)`, from the
    UI task.
  - Read here: `0x4007bc5e` is a function entry with three arguments (`link fp,#-28`, arguments at `fp + 8/12/16`);
    `0x4007bc1c` takes the FS lock `0x40fe6df0`.
  - `[HYP]` Calling it from the tick is safe under One-Shot's lock rules. To prove in W1 (§7).
- A sample file has a 64-byte header (`+1` 1 = stereo, `+4` bytes of audio, `+8` rate, `+16` last frame, `+20`
  `0x7f` = no loop), the frames as big-endian 16-bit, then 16 zero bytes (One-Shot §7). The uploader writes it from a
  WAV at 48 kHz, mono, under the name typed (One-Shot §12).

## 2. The design

### 2.1 The audio side: `cw_setup`

The call at `0x400ab15e` becomes `jsr cw_setup` (6 bytes, `old` = `4eb9400a8080`). `cw_setup(v, p)`:

1. t = (v − `0x42308828`) / `0x31c`.
2. In the block a note starts (`v + 0x38` ≠ 0: the block after the trig, or the machine change, §11.6):
   - n = the shortcut's value, k 30 (RETRIG + SWEEP, §10), >> 8. It is read from the sound object
     `CUR_SNDS[t] + 80`, or from the targets `0x800015ae + 66 · t + 60` when `CUR_SNDS[t]` is 0 (a preview note).
     The targets alone go stale when the value changes on a sound that keeps playing (§11.6);
   - `latch[t]` = the pointer list of table n, or 0 if n = 0, if n is out of range or if table n is not loaded.
3. `latch[t]` = 0: `jmp 0x400a8080`, the stock function with its own arguments.
4. Otherwise the stock function's body with `latch[t]` in place of the selector: frames index and index + 1 from a
   list of 33 pointers.

- **Why at the trig.** A table changed mid-note would jump the wave. The stock SWEEP crossfades, but a table number
  cannot. Taking it from the unsmoothed copy at the trig, as One-Shot takes its key, avoids both the click and the
  question of how the OS smooths k 30.
- **Size.** About 120 bytes of assembly, plus `latch[6]` in the package's variables.
- The flags and the sources were checked by W1's probe (§11.6). The first version of this plan latched on
  `v + 0x34` and read the targets only; both were wrong.

### 2.2 The tables in RAM

- A loaded table is 32 frames of 1 028 bytes (32 896 bytes) and a list of 33 pointers (index 0–32, the last
  repeating frame 31).
- SWEEP 0 is the table's first frame, not the stock sine (§10, decision 2): the whole SWEEP range is the file.
- 64 slots, plus 8 spare buffers so that a reload never writes into a table a track has latched: 72 × 32 896 =
  2 368 512 bytes.
- **RAM claim** `0x43400000`–`0x43700000` (3 MB, a `memory.ram` use):
  - inside the range the stock OS leaves unused (STANDARD.md §3.1, `memory.ram`);
  - above every payload (the largest in REGISTRY.md §3 is 492 288 bytes, to `0x43078300`; the composer refuses a
    layout that runs into a claim anyway);
  - below SAMPLE's pool (`0x43800000`);
  - clear of lfo-plus's `0x4233f000` (REGISTRY.md §6).

### 2.3 The loader: on the screen's tick

- **When.** Once the drive is mounted, then again whenever the file index changes (its count, or a sum of its ids).
  - `[HYP]` that catches every upload, replacement and deletion; W1 checks it in digiemu.
- **How.** One file per tick at most. It tries `/Wavetables/01` to `/Wavetables/64` in turn by path (§1.4) and
  reads at most 16 464 bytes (64 + 32 × 256 × 2 + 16).
- **What it takes.**
  - A mono file whose frame count is k × 256, k = 1 to 32.
  - Anything else leaves the slot empty: tracks that name it play the stock table.
  - The k frames are spread over the 32 slots, interpolating linearly between neighbours. 32 frames stay as they
    are; 1 frame fills every slot.
  - Each frame becomes Q31 (16-bit << 16) plus its 257th sample.
  - No filtering on the machine: a table must come band-limited (§4).
- **Publishing.** It fills a spare buffer, then stores the slot's pointer in one 32-bit write. The old buffer goes
  back to the spares once no `latch[t]` points at it.
- **Its code** follows One-Shot's `pool.c` (the tick, the lock rules, the reads), written anew for tables:
  - C, about 1 to 2 KB;
  - no FS call under a held lock, as One-Shot's host tests check.

### 2.4 The knob

The manifest's shortcut entry: RETRIG + SWEEP (§10, decision 3), range 0–64, default 0, long name "Wavetable", short
name "WAVE". It takes descriptor 3, k 30 and record slot 30 (notes/63 §3.2). The stock integer formatter `0x400456c8`
shows the number (notes/63 §11.2 point 4).

## 3. What the builder needs: a package that extends a stock machine

| Where | Today `[FAIT]` | Change |
|---|---|---|
| manifest | a package must have `{"point": "machine"}` (`load_manifest`) | a new point `{"point": "machine.stock", "machine": "CHORD"}` in its place. The claims already know the scope `machine:CHORD` (`tools/claims.py`, `STOCK_MACHINES`) |
| `compose()` | every package gets machine `6 + i`, descriptors `76 + 5 i` and a registrar entry | an extension is placed like a package (code from `0x43000000`, variables from `+0x36000`). It gets no number, no descriptor and no registrar entry, and refuses the patch points `machine_index` and `descriptor_base` |
| tables by machine | `first` = 6 in the shortcut layer's and the dispatchers' data blocks; entry i is the build's i-th package | with the CHORD extension, `first` = 5: the extension is entry 0, the added machines 6, 7, … follow. `shortcuts.o` and `dispatch.o` keep their bytes. The dispatchers hold 6 entries (`max_machines`), so 5 added machines at most next to it |
| the payload with no added machine | the registrar's frame exists for 1 to 6 machines only (`frame()`); the boot stub and the copy list come with it | a frame for 0 machines: the boot stub, the segments and the copy list, nothing registered. The extension alone needs it; with SAMPLE, the frame of 1 does as today |
| hooks | `package_writes` writes any declared `jsr`/`jmp` hook, checked against its stock bytes; `screen.tick` goes through the tick dispatcher when two packages take it | none: the call at `0x400ab15e` is a plain hook (STANDARD.md §3: a place the standard does not own, declared and checked byte for byte), the tick as SAMPLE's |
| `docs/flasher/composer.js` | the twin of `compose.py` (B4e); reads the `machine` point at line 573 | the same three changes, and `webcompose_check` |
| the standard | Level A knows only added machines; a core machine detours no OS function (STANDARD.md §2.6) | a section for stock machine extensions: what they may take (a plain hook on that machine's own path, its shortcuts, the tick), and the rule that value 0 plays bit for bit as the stock machine. Draft 0.5 |

## 4. Files on the +Drive

- **Names.** Folder `/Wavetables`, files `01` to `64` (§10, decision 1). A fixed name means no folder listing is needed,
  and a number keeps meaning the same file. Renaming a file moves it to another number, a happy accident in the
  sense of notes/62 §9.
- **Format.** Mono 16-bit at 48 kHz, k × 256 samples, each frame:
  - one cycle;
  - band-limited (the stock frames have nothing above harmonic 40);
  - starting on a rising zero crossing;
  - in phase with its neighbours, otherwise the SWEEP crossfade dips in level.
- **Upload.** One-Shot's uploader writes the file under the typed name, without extension (One-Shot §12,
  `uploader/app.js`).
  A 48 kHz WAV keeps its length through the browser's decode at 48 kHz, its values within one step (§11.4).
- **Converter** (§10, decision 5): `tools/wavetable.py`.
  - In: WAV frames of 256 or 2 048 samples (2 048 is the common wavetable size).
  - Out: the 48 kHz WAV for the uploader, or the device file for digiemu (`ekfsadd`).
  - It band-limits each frame to 40 harmonics, scales it to full level and aligns phases.

## 5. Conflicts and compatibility

| With | Bytes | Claims | Verdict |
|---|---|---|---|
| SAMPLE | different sites; the record functions and the tick through the shortcut layer and the dispatcher | k 30 and record slot 30 on CHORD's sounds; SAMPLE keeps 24–27 on its own | **together**, to be proven (P1) |
| control-all-config | none found | TRACK + TRIG 1–6, another combination | together |
| chord-keys (not offered) | none at the call or the selector | TRIG 1–16 in Keys mode on CHORD's tracks, another combination | together, to be heard together on the device |
| Syntakt engines (251 tweaks, not offered) | their payload is at `0x43000000`, like every package's | — | excluded by the payload, as SAMPLE is |
| track-filter, lfo-plus, Model-TG (not offered) | — | k 28–31 / record slots 28–31 against the shortcut layer | excluded, computed (notes/65) |
| arp | — | RETRIG + NOTES, another combination | together |

## 6. Proofs and done criteria

- **P1, Unicorn, the OS's own code** (`tools/emu/test_chord_tables.py`, run by the maintainer: Unicorn is missing in
  the sandbox). Three CHORD tracks, random SHAPE, COLOR and SWEEP, sweeps during the notes:
  - value 0 on every track: the output is identical to the stock build, block for block;
  - value n with a table built from the user's own stock frames (extracted at test time, never committed): identical
    to stock;
  - value n with another table: the frames used are that table's, checked against the pointer list;
  - n changed mid-note: nothing changes until the next trig;
  - n naming an empty slot: stock;
  - together with SAMPLE: SAMPLE's tracks identical to SAMPLE alone;
  - the cost by the standard's method (§6), CHORD on a table against CHORD stock.
- **P2, host tests of the loader** (C on the computer, a fake drive):
  - the header;
  - k × 256 for k = 1 to 32, and lengths that are not;
  - the spread over 32 slots;
  - Q31 and the 257th sample;
  - the spare buffers under a latched table;
  - no FS call under a held lock.
- **P3, digiemu** (the maintainer):
  - files placed with `ekfsadd`;
  - RETRIG + knob shows 0–64;
  - a table plays, survives a project save and reload, and survives an upload of another file;
  - a missing file plays stock.
- **P4, the device** (the maintainer): the same, and the official OS 1.13 afterwards.
- **Done:** P1 and P2 green, P3 and P4 reported by the maintainer. Then the card, as `experimental`, then `tested`.

## 7. Order of work

1. **W1, the open facts**, in emulation:
   - v + 0x34 and the parameter copy in CHORD's trig block (§2.1);
   - `0x4007bc5e` from the tick: arguments, lock, what a missing file returns (§1.4);
   - the file index on upload, replacement and deletion (§2.3, digiemu);
   - the uploader's length at 48 kHz (§4).
2. **W2, the builder** (§3) in `compose.py`, `composer.js` and their checks. `test_compose.py` and `test_shortcuts.py`
   stay green with every existing build byte for byte.
3. **W3, the package** `tools/machines/chordtables/`: `cw_setup` (assembly), the loader (C), the manifest, the
   generator, the committed object.
4. **W4, P1 and P2.**
5. **W5, the converter** (§4).
6. **W6, the maintainer's P3 and P4.**
7. **W7, the card**, after P4: text in English and French, credit, license. Then the standard's draft 0.5 (§3).

## 8. Decisions for the maintainer (decided, §10)

1. **The names:** fixed `01`–`64` in `/Wavetables` (recommended), or free names in sorted order. Free names need the
   folder listing decoded (the browser's folder object, `getEntry` `0x4007cdd4`, notes/46 §2), and numbers shift
   when a file is added.
2. **SWEEP 0:** the table's first frame, so that SWEEP crosses the whole file (recommended), or the stock sine as on
   the stock machine (31 frames per file).
3. **The knob:** RETRIG + SWEEP (recommended: SWEEP picks the frame, RETRIG + SWEEP the table) or RETRIG + CONTOUR,
   as first asked.
4. **When a new table starts:** at the next trig (recommended), or at once with a possible click.
5. **The converter:** `tools/wavetable.py` in model27 (recommended), or an export in the maintainer's CHORD Wave Bank
   editor (which they keep free of new features since 2026-10-12).
6. **The name** of the package and the card: `chordtables`, "CHORD Tables" (proposal).

## 9. Later: way B, the browser

- FUNC + MACHINES opens the stock PRESET browser on every track. One-Shot takes files at `0x400a6602` (One-Shot §8).
- A CHORD hook there could name a table by file. Sound locks would then come through the browser's stock lock path,
  as SAMPLE's do.
- It needs a key of the file in the sound. That is a record wrapper of its own, and STANDARD.md §3.1 allows one
  behind the layer, which SAMPLE holds. So it needs a dispatcher on `sound.record` or SAMPLE's slots shared by
  machine.
- `cw_setup` and the loader of this plan serve it unchanged.

## 10. Decisions (2026-10-23)

The maintainer took the six recommendations of §8.

1. **Names:** fixed, `01` to `64` in `/Wavetables`. No folder listing; renaming a file moves it to another number.
2. **SWEEP 0:** the table's first frame. A file's frames are spread over the 32 positions SWEEP reaches; the stock
   sine plays only at value 0, as part of the stock table.
3. **The knob:** RETRIG + SWEEP. SWEEP picks the frame, RETRIG + SWEEP the table: descriptor 3, k 30, record slot 30.
4. **When a new table starts:** at the next trig, from the parameter copy of the trig's block.
5. **The converter:** `tools/wavetable.py` in model27. The CHORD Wave Bank editor gets no new feature.
6. **The name:** package `chordtables`, card "CHORD Tables".

Next: W1 (§7).

## 11. W1 prepared (2026-10-23)

### 11.1 The trig block: a probe, and a design question it settles

- **Read in the code** `[FAIT]`: `0x40058a0a(sound, t)` sets `CUR_SNDS[t]` (`0x800015a0 + (147 + t) · 4`) and copies
  the sound's 66 bytes from `+20` to `0x800015ae + 66 t`. It runs only when the note's sound is not `CUR_SNDS[t]`
  (`0x400590d6`, notes/46 §2).
- **The question.** After RETRIG + SWEEP is turned on a sound that keeps playing, do the targets get the new k 30?
  - The stock edit path may notify them. That passage was never emulated end to end (notes/56 §3.9).
  - If it does not, `cw_setup` must read the sound object: `CUR_SNDS[t] + 80`. After a preview note
    `CUR_SNDS[t]` is 0 (`0x4005910e`), and then it must read the targets, which hold the previewed sound.
- **The probe** `tools/emu/probe_chord_tables.py`. Unicorn, the stock OS only, nothing patched:
  - **the sites:** the call at `0x400ab15e` and no other, the selector's table, the copy's addresses. They pass
    here, replayed on the stock MAIN OS without Unicorn;
  - **the voice loop:** three CHORD tracks next to KICK, SNARE and TONE, trigs in chosen blocks, including two
    blocks in a row. At the setup's entry it checks:
    - one call per block for each CHORD track, from `0x400ab164`;
    - v and p as in §1.1;
    - `v + 0x34` exactly in the trig blocks, `v + 0x38` in the block after;
    - `p + 0x3c` = k 30;
  - **the event loop** (`test_arp.Audio`):
    - a new sound: the targets and `CUR_SNDS[t]`;
    - the same sound after k 30 changed in the sound object: the targets' k 30, reported as a finding;
    - a preview note (the event's `+52`): `CUR_SNDS[t]` = 0, the targets = the preview sound;
    - a normal note after it: copied again.
- The probe answers for the event loop only; the notification itself comes from the interface. The answer, and
  why `cw_setup` reads the sound object, are in §11.6.

### 11.2 Opening a file by path `[FAIT]` (code reading)

`0x4007bc5e(path, mode, handle[16])`:
- returns −1, without the lock, when the drive is not mounted (`0x40f07cf4`), the path is null or longer than 255
  (`0x400cbde4`), or the mode or the handle is null;
- takes the FS lock `0x40fe6df0` (`0x40001cc4`). A mode containing `w` (`0x400cb7d4(mode, 'w')`) opens for writing;
- resolves the path (`0x4007d454`);
- **a file found:** the handle becomes {inode, position 0, write flag, open = 1}, the inode is marked open
  (`0x4007ed54`), the lock is given back and it returns 0;
- **in read mode, no file:** the lock is given back and it returns −1.

`0x4007bc1c(handle)` closes only a handle whose `+12` is set, under the same lock. The stock OS calls the open from
the FileWriter (`0x4007c4ba`) and the preset save (`0x400a2b72`), both in the UI task. The handle is the one
`0x4007baaa` reads (One-Shot §7).

The loader may call it from the tick under One-Shot's rules (§1.4). That it runs there in practice is checked with
the first build (P3).

### 11.3 When the file index changes `[FAIT]` (code reading)

- `0x4007e042` rebuilds the index only at mount (its one caller, `0x4007d644`).
- **A finished file:** `0x4007e2f6` hashes it and enters it in the index, which changes the count. It is called
  from the FileWriter's close (`0x4007c03e`) and the preset save (`0x400a2bfc`): an upload over USB is a FileWriter
  (One-Shot §12).
- **A deleted file:** `0x4007dfde` clears the inode's id, and `0x4007df92` takes the pair out of the index,
  count − 1.
- **Replacing a file** is a delete and an upload: the uploader refuses a name that exists. Both steps take seconds,
  so a 30 Hz tick sees both changes.
- **A rename** changes neither the count nor an id. Watching the count and a sum of the ids catches uploads,
  deletions and replacements, not a rename `[HYP]`: a renamed table is seen at the next start.

### 11.4 The uploader at 48 kHz `[FAIT]` (measured)

Measured in the desktop app's built-in browser (Chromium 152), with the uploader's own conversion
(`OfflineAudioContext` at 48 kHz, `mixDown`, `toInt16`):

| WAV | Length | Values |
|---|---|---|
| mono, 48 kHz, 8 192 samples | 8 192 | 6 098 of 8 192 exact: every sample from 16 368 up comes back one step high |
| stereo, 48 kHz, both channels the same | 8 192 | as mono |
| mono, 44,1 kHz, 8 192 samples | 8 916 | resampled: no longer k × 256 |
| mono, 48 kHz, every value −32 768 … 32 767 | 65 536 | negative values exact; positive values from 16 368 up are 1 step high (16 400 values) |

- **Why.** Chromium decodes 16-bit asymmetrically: negative values / 32 768, positive values / 32 767 (32 767 gives
  1,0). The uploader multiplies both by 32 768.
- **For tables** the error is at most 1 step (about −90 dB): harmless. A table must come at 48 kHz, so the
  converter writes 48 kHz (§4).

### 11.5 What the maintainer runs

```sh
../.venv-emu/bin/python3 tools/emu/probe_chord_tables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

Then:
- the result goes into this section;
- `cw_setup`'s source of k 30 follows from 11.1;
- W2 starts.

No separate digiemu probe was written. Items 11.2 and 11.3 are read in the code, and running them takes the loader
itself, so they are checked with the first build in digiemu (P3).

### 11.6 The first run (the maintainer, 2026-10-23)

The probe ran in `.venv-emu` with Unicorn 2.1.4, against the official file. Result: the sites and the event loop ok,
3 FAIL in the voice loop.

- **The FAILs.**
  - 93 calls instead of 102 (34 blocks × 3 tracks);
  - no `v + 0x34` in the first trig block;
  - no `v + 0x38` after track 2's second trig, which came in the block right after its first.
- **Why** `[FAIT]`, read in `0x400a7d4a`. Per track the voice loop:
  1. writes the trig bit to `v + 0x34` and the release bit to `v + 0x3c`;
  2. only if `v + 0x38` is set, compares the parameters' machine (`p + 18`, through `0x40118640`) with `v + 4`;
     when they differ it resets the voice (`0x400a7ab8`, which clears `v + 0x00..0x3c`), sets `v + 0x38` = 1 and
     writes the machine to `v` and `v + 4`;
  3. calls update and render of the machine at `v` when it is 0–5;
  4. copies `v + 0x34` to `v + 0x38`.
- **So the first note after a machine change:**
  - its trig block still runs the old machine;
  - CHORD's update starts in the next block, with `v + 0x34` clear and `v + 0x38` set;
  - a trig in that block is lost to the reset.

  The probe expected otherwise. The OS is right, the probe was wrong.
- **The event loop** `[FAIT en émulation]`: after k 30 changed in the sound object without a new sound, the targets
  keep the old value (0x0300 against 0x0500). A preview note leaves `CUR_SNDS[t]` at 0 and the targets holding the
  preview sound. The next normal note copies the kit sound again.
- **What changes in the design (§2.1):**
  - `cw_setup` latches in the block with `v + 0x38` set, which is the block a note starts in on every machine
    (One-Shot §5);
  - it reads k 30 from `CUR_SNDS[t] + 80`, and from the targets only when `CUR_SNDS[t]` is 0.
  - Whether the interface's edit path also writes the targets no longer matters.
- **The probe** now expects the machine change: no call in block 0, the change in block 1 (and track 2's trig there
  lost), then the flags exactly as before, with a pair of consecutive trigs on track 5. To run again:

```sh
../.venv-emu/bin/python3 tools/emu/probe_chord_tables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

### 11.7 The second run (the maintainer, 2026-10-23)

The corrected probe, same command: **ALL OK** `[FAIT en émulation]`.
- **Sites, voice loop, event loop:** all green.
- **The voice loop:**
  - no call in the first trig block, then the machine change in the next;
  - one call per block for each CHORD track and no other;
  - `v + 0x34` and `v + 0x38` exactly as §11.6 says, with two trigs in consecutive blocks too.

W1 is done. `cw_setup` latches in the block with `v + 0x38` set and reads k 30 from `CUR_SNDS[t] + 80`, or from the
targets when `CUR_SNDS[t]` is 0 (§2.1). Next: W2 (§7).

## 12. W2 built (2026-10-23)

### 12.1 What was built

- **`tools/compose.py`:**
  - `STOCK_EXTENDED = {"CHORD": 5}`.
  - `load_manifest()` takes a package with `{"point": "machine.stock", "machine": "CHORD"}` in place of `machine`. It
    refuses both or neither, another stock machine, an extension without `build.roots`, and the patch points
    `machine_index` and `descriptor_base`.
  - `roots_of()` gives the entry points an object is laid out from: update and render, or `build.roots`.
- **`compose()`:**
  - added machines are numbered 6, 7, … by their place among the added machines, in the order given;
  - the tables by machine (the shortcut layer's data, the dispatchers') are the extension, then the added
    machines, from `first` = 5. Without an extension they are the packages in the order given and `first` = 6, as
    before. `shortcuts.o` and `dispatch.o` keep their bytes; a CHORD entry with no method goes to the stock code, as
    any empty entry did;
  - the shortcut layer is told the descriptor table the OS uses: the registrar's copy (`0x43034000`) with an
    added machine, the stock table (`0x4010dce0`) without one;
  - without an added machine nothing is registered: `frame_alone()` and `fill_alone()` (`payload_writes()`) write
    the freed mask the stub lives in, the boot hook and the stub, and the payload is the packages and the parts.
- **`frame.json`** gains `"alone"`, those two writes. `frames()` checks that the layout and the stub are the others',
  and `frame_of(…, 0)` gives the frame back. The frames of 1 to 6 machines do not change.
- **`tools/claims.py`:** `own_scope()`: an extension's scope `machine` is the stock machine (`machine:CHORD`), in
  `build_holders()` and `tweak_claims()`. `tools/registry.py` does the same.
- **`docs/flasher/composer.js`:** the same changes:
  - `STOCK_EXTENDED`;
  - the kind of each package;
  - the table and its `first`;
  - `frameOf(…, 0)` and `fillAlone()`;
  - `ownScope()`;
  - the stock descriptor table without an added machine.

  `tools/webcompose_synth.py` reads `build.roots` and composes five selections with REFC.
- **REFC**, the reference extension (`tools/machines/refchord/`, MIT, order 34), never offered:
  - RETRIG + SWEEP = Wavetable, 0 to 64, on CHORD's tracks through the shortcut layer (k 30);
  - `rc_setup` on the call at `0x400ab15e` and `rc_hook_tick` on the tick: each counts, then calls the stock
    function;
  - 24 bytes of code and 8 of variables;
  - `tools/gen_refmachine.py` writes `34-refchord.json`, whose description ends on this note, so that the registry
    names it.
- **`tools/emu/test_refchord.py`**, the proof, in seven parts:
  - the start-up;
  - the sites;
  - the knob;
  - descriptor 3;
  - save and load of a CHORD sound;
  - the tick;
  - the voice loop: CHORD identical to the stock OS, every setup through `rc_setup`.
- **Regenerated:**
  - `27-sampler.json`, `28-refmachine.json` and `29-refmachine2.json`, which gain the computed conflict `refchord`;
  - `REGISTRY.md` and `docs/flasher/tweaks.js` (which embeds `frame.json`);
  - the pages' stamp, `2026-10-23-03`;
  - a `PROVENANCE.md` row and the repository map in `AGENTS.md`.
- **A bug found while building.** The first build of REFC alone pointed the layer at `0x43034000`, the registrar's
  copy of the descriptors, which a build with nothing registered does not have. It was found by decoding the layer's
  data block, before any run. Hence the `descn` argument.

### 12.2 Measured

| Build | Writes | Added to the image | Tables by machine | MAIN OS |
|---|---|---|---|---|
| refchord | 9 | 624 | from 5, 1 machine, descriptors at `0x4010dce0` | `a2925916…` |
| refchord + sampler | 125 | 37 336 | from 5, 2 machines; tick: REFC, SAMPLE | `1bc8c715…` |
| sampler + refchord | 125 | 37 336 | the same | `66f5dac7…` |
| refchord + refmachine2 | 125 | 10 020 | from 5; WAVE on 5, OCT on 6 | `5c7a3227…` |
| sampler + refchord + refmachine2 | 125 | 41 004 | from 5; WAVE on 5, OCT on 7; tick: REFC, SAMPLE, REF2 | `864f27e2…` |

REFC alone writes exactly:
- the boot hook, the stub's mask and its room;
- the knob lookup's entry and the three record functions;
- the tick and CHORD's call.

Nothing of the registrar's: CHORD's pointer table and the references to the descriptor table stay stock.

### 12.3 Checks

- **The builds that existed are unchanged, byte for byte.** HEAD's `compose.py` and the new one give the same MAIN OS
  for sampler, refmachine, refmachine2 and the five combinations of them. `compose.py --machines sampler --compare
  27-sampler.json` is identical too.
- **`webcompose_check.sh` with the official file:**
  - the 14 selections (9 before, 5 with REFC) are identical to `compose.py`: tweak and MAIN OS;
  - the 6 synthetic fills are identical;
  - every object's 23 placements are identical.
- **Green:**
  - `gen_refmachine.py`, `gen_sampler.py`, `gen_registrar.py --cycles` and `gen_parts.py` with `--check`;
  - `check_overlaps.py`, `registry.py --check`, `claims.py --check --self-test`;
  - `gen_flasher_tweaks.py --check`, `ref_mainos.py --check`;
  - `webbuild_check.sh`, `webflash_check.sh` and `webflash_smoke.sh` (ALL OK);
  - `py_compile`.
- **Not green:** `relocate_6ch.py --check` says `11-6ch-usbup.json` is not up to date. It says the same on HEAD,
  untouched here.
- **Emulation:** `test_refchord.py` compiles and finds every helper it uses; Unicorn does not run in the sandbox.
  The maintainer's run:

```sh
../.venv-emu/bin/python3 tools/emu/test_refchord.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

Then: W3, the package `chordtables`, on these extensions. The standard's section on extensions comes with W7.

### 12.4 Proven in emulation (the maintainer, 2026-10-23)

`test_refchord.py`, the command above: **ALL OK** for the four selections `[FAIT en émulation]`: refchord, refchord +
sampler, sampler + refchord, and sampler + refchord + refmachine2.
- **Start-up.** The bootstrap's depacker reads the grown OS back, from 1 744 816 bytes (REFC alone) to 1 785 196.
  The boot hook copies the payload intact and clears the BSS.
- **The sites:**
  - CHORD's call goes to `rc_setup`;
  - the tick goes to `rc_hook_tick` alone and to `dp_tick` with SAMPLE;
  - the layer's chain ends in SAMPLE's wrappers when SAMPLE is in the build;
  - the tables start at machine 5, on `0x4010dce0` alone and on `0x43034000` with an added machine;
  - REFC alone has 9 writes, CHORD's pointer table and the descriptor references stay stock.
- **The knob:** descriptor 3 only for RETRIG + SWEEP on CHORD, and descriptor 1 for REF2's RETRIG + COLOR on machine
  7. Every other case gets the stock answer: 2 016 to 2 464 cases per build, the stack back each time.
- **Descriptor 3:**
  - k 30, 0..64, no CC, no NRPN, "Wavetable" / "WAVE", machine −1, the other 75 to 85 descriptors untouched;
  - the range getter reads (0, 16 384, 0);
  - the setter clamps to 0..16 384;
  - interface object 3 shows "0" to "64".
- **Save and load:** a CHORD sound's record differs from the stock one at byte 88 only, record slot 30, in versions 2
  and 1. Version 2 loads k 30 back with the rest as the stock load, version 1 is refused as before, and a record of
  the official OS loads 0.
- **The tick:** REFC's tick counts once and returns the getter's answer. With SAMPLE: getter, `smp_hook_tick`, getter.
  With REF2 too: getter, `smp_hook_tick`, `ref2_hook_tick`, getter. That is machine order, then the stock getter once.
- **The voice loop:** CHORD on tracks 1 and 4 with SWEEP moving plays as on the stock OS, sample for sample (peak
  1,63e8). There are 156 setups in the stock OS and 156 in every build, all through `rc_setup`.

W2 is done. Next: W3, the package `chordtables`.

## 13. W3 built (2026-10-23)

### 13.1 What was built

- **The package** `tools/machines/chordtables/` (MIT, order 36): `chordtables.c`, the manifest and the committed
  object. Its uses:
  - `machine.stock` CHORD;
  - the shortcut RETRIG + SWEEP = Wavetable, 0 to 64;
  - `cw_setup` on the call at `0x400ab15e`;
  - `ct_hook_tick` on the tick;
  - `memory.ram` `0x43400000`–`0x43700000`.

  Its claims: k 30, record slot 30, the RAM range and the combination.
- **The generator** `tools/gen_chordtables.py` writes the object and `36-chordtables.json`, CHORD Tables alone.
  It has 9 writes, the same sites as REFC's, and adds 2 068 bytes to the image.
- **`cw_setup`, as §2.1 and §11.6 say:**
  - in the block with `v + 0x38` set, it latches the table named by k 30. k 30 comes from `CUR_SNDS[t] + 80`, or
    from the targets when that is 0;
  - without a table it jumps to the stock function with its own arguments;
  - with one it writes the stock function's five fields in the four sub-voices.
- **The loader, as §2.3 says:**
  - the tick takes its own `tas` lock, and drives the file system only when it is mounted and its lock is not the
    running task's;
  - the index's signature is its count and the sum of its ids, read over 8 192 pairs at most. A new signature
    starts a scan of `/Wavetables/01` to `64`, one file per tick;
  - for each file: open by path, take the inode and close; read the id and the size (`0x4007de78`); a slot that
    holds the same id is kept; then the header, the frames, the table built and published.

  The layout:

  | Part | Size |
  |---|---|
  | One file as read | 16 384 bytes from `0x43400000` |
  | 72 buffers of 33 040 bytes | 33 pointers and 32 × 257 Q31 samples each |
  | End | `0x43648c80`, inside the claim |

- **Decisions taken while writing it**, for the maintainer to know:
  - a negative SWEEP (an LFO under 0) plays the first frame; the stock function would take the sine;
  - a file that is stereo, empty, not a multiple of 512 bytes, over 16 384 bytes of audio or shorter than its
    header says empties its slot;
  - with no free buffer, the scan waits on that file until one is free;
  - a track that leaves CHORD keeps its latch, and so a buffer, until it plays CHORD again. The 8 spare buffers
    cover the six tracks.
- **Regenerated:**
  - `27-sampler.json`, `28-refmachine.json`, `29-refmachine2.json` and `34-refchord.json` gain the computed conflict
    `chordtables`;
  - `REGISTRY.md`;
  - `webcompose_synth.py` composes CHORD Tables alone and with SAMPLE before and after it.

  Also a `PROVENANCE.md` row and the repository map. `tweaks.js` does not change: the package is not offered.

### 13.2 Measured

| Build | Writes | Added to the image | Code and tables | Variables | MAIN OS |
|---|---|---|---|---|---|
| chordtables | 9 | 2 068 | 1 465 | 624 | `f796d93e…` |
| chordtables + sampler | 125 | 38 780 | 1 465 + SAMPLE | 624 + SAMPLE | `96eeffbf…` |
| sampler + chordtables | 125 | 38 780 | | | `be21c9a0…` |

- **Conflicts:** CHORD Tables alone computes 269 of them, among them `model-tg` and `model-tg-st`, whose sample
  zone covers the RAM claim. `refchord` and `chordtables` cannot be built together: two packages extend CHORD.
- **The code read back:** `cw_setup` checks the voice's range, latches on `v + 0x38`, computes the crossfade as
  `(SWEEP << 21) & 0x7fe00000`, and tail-jumps to `0x400a8080` with its arguments in place.

### 13.3 Checks

- **Green:**
  - `gen_chordtables.py`, `gen_refmachine.py` and `gen_sampler.py` with `--check`;
  - `claims.py --check --self-test`;
  - `check_overlaps.py` (288 tweaks), `registry.py --check`;
  - `gen_flasher_tweaks.py --check`, `ref_mainos.py --check`;
  - `webcompose_check.sh` with the official file: every selection identical to `compose.py`, the three new ones
    included;
  - `py_compile`.
- **Nothing ran on the OS's code yet.** That is W4:
  - P1: Unicorn, `cw_setup` in the voice loop, with a table built from the stock frames that must play like the
    stock OS;
  - P2: the loader in Unicorn, with the file system's four calls answered by the proof.

## 14. W4 prepared (2026-10-23)

`tools/emu/test_chordtables.py`, for chordtables alone and with SAMPLE before and after it.

**0. Start-up and sites:**
- the bootstrap's depacker and the boot hook;
- CHORD's call goes to `cw_setup`, the tick to `ct_hook_tick` or the dispatcher;
- the layer's tables from 5, the payload below the RAM claim;
- the knob, descriptor 3, save and load, through `test_refchord.py`'s checks: the same shortcut.

**P1, `cw_setup` in the voice loop.** Two CHORD tracks with SWEEP moving. k 30 comes from the sound object on
track 1 and from the targets on track 4.
- **a.** Wavetable 0 is identical to the stock OS, every setup through the stock function.
- **b.** A table made of the stock frames (the sine, frames 1 to 31, the last repeated), copied into the RAM claim,
  is identical to the stock OS sample for sample, and the stock function is never called. This shows the frame
  arithmetic is the stock function's.
- **c.** With the stock frames in reverse, the four sub-voices hold that table's frames, crossfade and index in every
  block, and the sound differs from the stock OS.
- **d.** k 30 changed during a note changes nothing until the next note.
- **e.** An empty slot, 65 and −1 play the stock table. A negative SWEEP plays frame 0 with no crossfade.
- **Read beforehand in the OS:** in CHORD's code only `0x400a8080` writes the fields `+156`, `+168`, `+172`,
  `+184` and `+188` of a sub-voice. The other writes of `+168` and `+172` (`0x400aa342`, `0x400aa9da`) are other
  machines' code. So what the proof reads after a block is what `cw_setup` wrote.

**P2, the loader.** It runs in the UI harness with the drive emulated by the proof: files by path, inodes, ids,
the index in memory, and the four calls `0x4007bc5e`, `0x4007bc1c`, `0x4007de78` and `0x4007baaa`.
- **a. The scan after the mount:**
  - 01 to 64 are opened in order, one per tick, in read mode, and each found one is closed;
  - the tables of 32, 1, 4 and 2 frames are built exactly as the proof computes them (C's integer division, Q31,
    the 257th sample, 33 pointers);
  - a stereo file, 300 samples, 33 frames and a missing file leave their slot empty;
  - each tick returns the getter's answer.
- **b.** Nothing changes: no file call.
- **c.** A file added starts a new scan. The kept files are not read again; only the rejected ones get their
  header read.
- **d.** A file replaced: a new buffer, and the old one is held while a latch points at it, then freed.
- **e.** A file deleted: its slot is emptied.
- **f.** Not mounted, or the lock held by the running task: no call. Free again: a new scan.
- **g.** No free buffer: the scan waits on the file, then goes on.

It compiles, and every helper it takes from the other proofs exists. Unicorn does not run in the sandbox. The
maintainer's run:

```sh
../.venv-emu/bin/python3 tools/emu/test_chordtables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

### 14.1 The first run (the maintainer, 2026-10-23)

- **Result:** everything green but one check in each of the three selections: P2a, "a stereo file (05), 300 samples
  (06), 33 frames (07) and the missing files: empty slots".
- **Why: the proof, not the loader.** File 06 was cut from `frames_of(1, …)`, which gives 256 samples, so `[:300]`
  left 256. The file was a valid one-frame table, and the loader rightly loaded it.
- The loader's checks read back as written:
  - `tstb` of the header's `+1` (stereo);
  - bytes − 1 > 16 383 (0 or over 32 frames);
  - bytes & 511 (not k × 256 samples);
  - bytes + 64 above the file's size.

  Each goes to the path that empties the slot.
- File 06 now has 300 samples. The run is to be repeated.

### 14.2 The second run (the maintainer, 2026-10-23)

**ALL OK** for chordtables, chordtables + sampler and sampler + chordtables `[FAIT en émulation]`.

- **Start-up and sites.** The depacker reads the grown OS back (1 746 260 bytes alone, 1 782 972 with SAMPLE), and
  the boot hook copies the payload intact.
- **The sites:**
  - CHORD's call goes to `cw_setup`;
  - the tick goes to `ct_hook_tick` alone and to `dp_tick` with SAMPLE;
  - the layer's tables start at 5;
  - the payload ends at `0x43036270` alone and at `0x430482a8` with SAMPLE, below the claim.
- **The shortcut:** descriptor 3 only for RETRIG + SWEEP on CHORD (2 016 or 2 240 cases). Its fields, range,
  setter and display are right, and k 30 lands in record slot 30, as for REFC.
- **P1:**
  - Wavetable 0 is identical to the stock OS, with 156 setups through the stock function, as in the stock OS;
  - the stock frames as table 7, at `0x43404000`, are identical to the stock OS sample for sample; the stock
    function is never called, and both tracks latched, the sound object's and the targets';
  - the reversed table: the sub-voices hold its frames, crossfade and index in every block, 32 frames reached, and
    the sound differs;
  - k 30 changed during a note keeps table 1 at `0x4340589c` until the next note, which plays table 2 at
    `0x4340d9ac`;
  - an empty slot, 65 and −1 play the stock table, identical to the stock OS;
  - a negative SWEEP gives frames 0 and 1, no crossfade, index 0.
- **P2:**
  - the scan opens 01 to 64 in order, one per tick, in read mode;
  - the tables of 32, 1, 4 and 2 frames are exactly as computed here;
  - stereo, 300 samples, 33 frames and missing files leave their slots empty;
  - each table is read as its header, then its frames;
  - with nothing changed, no call;
  - added, replaced (the old buffer held by a latch, then free), deleted, not mounted, the lock held, no free
    buffer: each as §14 says.

W4 is done. Still to do:
- W5, the converter `tools/wavetable.py`;
- W6, the maintainer's digiemu and device: open by path from the tick (§11.2), the index on a real upload (§11.3),
  the sound;
- W7, the card and the standard.

## 15. W5 built, W6 prepared (2026-10-23)

The maintainer: "bau es wie geplant". So the cost measurement that §6 asked of P1 was added first, then W5 was built
and W6 prepared. W7 waits for the device, as §7 orders it.

### 15.1 The cost, added to the proof

`test_chordtables.py` part C follows STANDARD.md §6:
- instructions per block per voice in the real voice loop;
- CHORD alone on track 1, minus a run with every voice muted;
- the note's first block, then the mean and the maximum of the next 21;
- for stock CHORD, Wavetable 0 and a table.

The numbers are printed as findings, and the extension's share is checked: under 100 instructions at Wavetable 0,
between −100 and +200 with a table. The emulator does not time memory: what a table's frames cost in SDRAM instead
of SRAM only the device shows. The numbers go into the manifest's `cost.emulation` after the maintainer's run.

### 15.2 The converter `tools/wavetable.py` (W5)

Plain Python, no extra package, MIT. The steps:
1. **Reads a WAV:** 8, 16, 24 or 32-bit PCM or 32-bit float, mixed to mono.
2. **Cuts it into frames** of `--frame` samples: 2 048 when the length is a multiple of it, else 256. A table that
   is both, 8 × 256 = 2 048 for one, needs `--frame`.
3. **Keeps 32 frames at most**, evenly picked (`--frames`). Since §16: 31, after a sine as the first frame.
4. **For each frame:**
   - takes harmonics 1 to 40 (`--harmonics`) by a DFT and synthesises 256 samples: no DC, nothing above;
   - turns the frame so that its fundamental starts in sine phase, the same for all of them (`--no-align`);
   - scales it to full level (`--keep-levels`: one gain for the table).
5. **Writes** the 48 kHz mono 16-bit WAV for the uploader (`-o`) and/or the +Drive's sample file (`--device`),
   refused if the loader would refuse it.

`--self-test`: **ALL OK** here, 13 checks.

| What | Checked |
|---|---|
| A saw table of 4 frames of 2 048 samples, harmonics to 199 | 4 × 256 samples |
| What it keeps | nothing above harmonic 40 but rounding, no DC, each frame at full level |
| The phase | every fundamental in sine phase; each frame starts on a rising zero crossing |
| The device file | its header fields; the loader's rules take it (4 frames) and refuse a stereo file, 300 samples and 33 frames |
| 256-sample frames under 40 harmonics | the same samples, scaled once |
| 64 frames | 32 kept, evenly |
| WAV formats | 16-bit stereo at 44,1 kHz, 24-bit and float read as the 16-bit WAV |

`test_chordtables.py` P2a now also loads a file the converter made, as `/Wavetables/08`: a 4-frame saw table at
2 048 samples a frame. Its table must come out exactly as computed.

```sh
python3 tools/wavetable.py my-table.wav -o 01.wav
python3 tools/wavetable.py --self-test
```

### 15.3 What the maintainer runs and tests (W6)

1. **The proof again**, for part C and the converter's file:

   ```sh
   ../.venv-emu/bin/python3 tools/emu/test_chordtables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
   ```

2. **The firmware.** CHORD Tables alone, or with SAMPLE:

   ```sh
   python3 tools/compose.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --machines chordtables --out build/
   python3 tools/compose.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --machines sampler,chordtables --out build/
   ```

   These give `build/model-cycles_OS1.13-chordtables.syx` and `…-sampler+chordtables.syx`. They are flashed the way
   the pair SAMPLE + REF was (notes/60 §12): the web flasher does not offer the package.
3. **The tables:**
   - `tools/wavetable.py` for each one;
   - in One-Shot's uploader, a folder `Wavetables` at the drive's root;
   - the files uploaded under the names `01`, `02`, … (the uploader drops the extension).
4. **digiemu.** `ekfsadd.py` writes only into a folder that exists. model27 carries no tool that makes one:
   digiemu's file system code is GPL-2.0, and copying or paraphrasing it here is not allowed. The Cycles makes the
   folder itself (§15.6).
5. **On the device:**
   1. on a CHORD track, RETRIG held + SWEEP shows Wavetable 0 to 64, and 0 sounds as before;
   2. Wavetable 1 plays file 01 from the next note, and SWEEP moves through its frames without a click;
   3. the Wavetable changed while a note holds takes effect at the next note;
   4. a file uploaded while the Cycles runs plays about 2 s later (the scan, one file per tick);
   5. the project saved, the Cycles off and on: the tables come back;
   6. sound locks with different Wavetables (the copy of a sound beyond k 22 is open, notes/63 §3.2);
   7. the other tracks, and SAMPLE in the build with it, as before;
   8. the load with six CHORD tracks on tables;
   9. back on the official OS 1.13: CHORD sounds play the stock table.

   Only the device shows three things: the open by path from the tick (§11.2), the file index on a real upload
   (§11.3), and the cost of the frames in SDRAM.

### 15.4 The third run (the maintainer, 2026-10-23)

**ALL OK** for the three selections `[FAIT en émulation]`. Everything of §14.2 holds again, and two things are new:

- **P2a, the converter's file:** `/Wavetables/08`, made by `tools/wavetable.py`, loads as a table of 4 frames
  exactly as computed.
- **C, the cost** by STANDARD.md §6, in instructions per block per voice:

  | | First block | Mean | Max |
  |---|---|---|---|
  | Stock CHORD | 8 737 | 8 292 | 8 300 |
  | CHORD Tables at Wavetable 0 | 8 778 | 8 314 | 8 322 |
  | CHORD Tables on a table | 8 755 | 8 291 | 8 299 |

  The extension adds +22 at Wavetable 0. On a table it adds −1: its loop takes the stock function's place. The
  numbers are the same in the three selections.
- **In the manifest:** `cost.emulation` holds the Wavetable 0 line as `mean` / `max`, and the other two lines and
  the pattern with it. `cost.device` stays "not measured".
- **What the emulator does not time:** a table's frames read in SDRAM instead of SRAM. By notes/27 and 28's
  estimates that is about +0,6 to +1,2 points of a block per CHORD voice on a table; the device measures it (§15.3,
  point 5.8).

### 15.6 In digiemu first (2026-10-23)

The maintainer tests the build in digiemu before the device.

- **The folder.** The stock OS makes folders in the PRESET browser `[FAIT]` (read in the code after the maintainer
  did not find the item: the first version of this step named no key):
  - `0x400a6d5c` is the browser's key handler. For key code 1 (FUNC) it opens a popup of three items: "Save Preset",
    "Save Kit" and "Create folder" (`0x400a6e08`–`0x400a6eb2`, the string at `0x40130323`);
  - it does so only on a click, FUNC pressed and released alone (`0x40072434`: bit 4 of the event, notes/63 §15);
  - the browser must show the drive's files, not the pool (`vt[152]`, `0x400a3308`: `+640 == +632`, notes/40);
  - the folder must be writable: `0x4007cd30` → `0x4007ec78`, bit 0 of the inode's `+1` clear, so not inside
    `factory`.

  So the emulated Cycles makes `/Wavetables` itself: FUNC + MACHINES, then FUNC alone at the drive's root.
  - `[HYP]` The name must be typed `Wavetables` exactly. Whether the naming screen offers lowercase, and whether the
    path is compared without case, is not read.
- **The builds:**

  | File | `.syx` SHA-256 | MAIN OS |
  |---|---|---|
  | `build/model-cycles_OS1.13-chordtables.syx` | `e4dafb31…` | `f796d93e…` |
  | `build/model-cycles_OS1.13-sampler+chordtables.syx` | `77a10a97…` | `be21c9a0…` |

- **Four test tables**, made by `tools/wavetable.py` from synthetic 2 048-sample tables, in
  `_scratch/chordtables-digiemu/` (not in the repository):

  | File | Table |
  |---|---|
  | `01.wav` | saw → square, 32 frames |
  | `02.wav` | sine → saw, 32 frames |
  | `03.wav` | pulse width 6 % → 50 %, 32 frames |
  | `04.wav` | an organ cycle, 1 frame |

- **Checked here with digiemu's own conversion** (`wav_to_sample`, run locally, not copied): each file becomes a
  sample file the loader takes, of 32, 32, 32 and 1 frames, within one step of the WAV. The card names are `01` to
  `04`, since `ekfsadd` drops the extension.
- **The steps:**
  1. open the `.syx` in digiemu once, so that its folder `mc-1.13-<SHA8>` and `plusdrive.img` exist;
  2. in the emulated Cycles, FUNC + MACHINES; at the browser's root, FUNC pressed and released alone; "Create
     folder"; name `Wavetables`;
  3. close digiemu;
  4. `ekfsadd.py <plusdrive.img> 01.wav 02.wav 03.wav 04.wav --dir Wavetables`;
  5. start digiemu again.
- **What digiemu can show:**
  - the boot;
  - RETRIG + SWEEP on CHORD, 0 to 64;
  - tables 1 to 4 and SWEEP through their frames;
  - a change during a note;
  - Wavetable 5 (no file) as stock;
  - the project saved and digiemu restarted;
  - the other tracks, and SAMPLE in the second build.
- **What it cannot show:** a file uploaded while it runs, since `ekfsadd` writes only while digiemu is closed, and
  the device's timing.

### 15.7 Tested in digiemu (the maintainer, 2026-10-24)

- **The folder.** It was made in the emulated Cycles with the stock menu of §15.6. The first one came out as
  `Wavetabless`, which the loader does not read (it opens `/Wavetables/NN` only), so a second one, `Wavetables`, was
  made next to it.
- **The files:** the four test tables, written with `ekfsadd.py … --dir Wavetables`, digiemu closed.
- **The build:** `build/model-cycles_OS1.13-chordtables.syx` (`.syx` `e4dafb31…`, MAIN OS `f796d93e…`).
- **The maintainer:** "getestet, funktioniert".
  - Which points of §15.6's list were tried one by one was not said.
  - Not tried in digiemu: the build with SAMPLE (`77a10a97…`).
- **Still for the device (§15.3):**
  - a file uploaded while it runs;
  - the cost of the frames in SDRAM;
  - the official OS afterwards.

### 15.5 Still open

- **W7 after the device:** the card (texts in English and French, guide, release) and the standard's section on
  extensions (draft 0.5). That section fixes the deviations: `machine.stock`, `build.roots` under the schema name
  `cycles-mod/0.1`, the unknown point `chord.waves`.
- **The order numbers** 34 (REFC) and 36 (CHORD Tables) were picked by Claude in the standard's range for machines.
  APPLYING.md §11 leaves them to the maintainer, who confirms them or gives others. **Confirmed by the maintainer
  on 2026-10-24** ("so lassen"). The tweaks model27 inherited from Modded-Cycles and does not offer (MACRO, ACID,
  Model-TG, the Syntakt engines…) stay in the folder, and the numbers stay clear of them.

## 16. SWEEP 0 is a sine on every table (2026-10-24)

The maintainer asked whether the first waveform is always a sine. It was not: decision 2 (§10) gives SWEEP 0 the
file's first frame. The maintainer's decision the same day: **the firmware stays as it is, and the converter gives
every table a sine as its first frame; a web importer tests whether a table's first waveform is a sine and warns.**
The reason should be in the CHORD Wave Bank's README.

### 16.1 The reason, in the CHORD Wave Bank

- **In its README:** "Frame 0, the sine, is shared with other parts of the OS and stays." Its TECHNICAL.md adds
  that CHORD's selector gives any index outside 1–32 the sine at `0x8000eee4`, and that code outside CHORD reads the
  same sine (`0x400a7b4e`, `0x400aa334`). The Wave Bank rewrites the OS's frames in place, so it cannot replace that
  one, and SWEEP 0 is the sine in every set it builds.
- **Its editor** builds on that. Its table has 31 slots on SWEEP 4 to 124 ("SWEEP 0 is a sine"). "Fill gaps"
  starts from the sine. The phase check warns "The volume dips when sweeping into frame …", from the sine into
  frame 1 too (`coherence(SINE_SPEC, …)`). It does not test whether frame 0 is a sine, since its user cannot change
  frame 0.
- **For CHORD Tables** that reason is not technical: its tables are its own buffers, and the OS's sine stays
  untouched either way. What the rule keeps is musical: a sound at SWEEP 0 is the same sine on every table, as on
  the stock CHORD and in every Wave Bank set.

### 16.2 What changed

- **The firmware:** nothing. The loader puts a file's first frame on SWEEP 0 (§2.2). A table from the converter
  therefore starts with the sine, whatever its number of frames, since the spread always maps frame 0 to SWEEP 0.
- **`tools/wavetable.py`:**
  - `sine_frame()`, harmonic 1 in sine phase at full level, goes in front of the input's frames, of which 31 at most
    are kept (`--frames` 1 to 31);
  - a table of 31 frames from the input is then 32 frames, SWEEP 0 the sine and SWEEP 4·k frame k, the stock CHORD's
    layout;
  - `starts_with_sine(table)` is the test a web importer warns with: harmonic 1 in sine phase, DC and every other
    harmonic under 1e-3 of it;
  - `--self-test` ALL OK, 15 checks: the sine in front, the 5 frames of the saw table, a saw, a cosine and a sine
    with harmonic 2 told apart, 31 of 64 frames kept after the sine.
- **`tools/emu/test_chordtables.py`:** file 08, made by the converter, is now the sine and 4 frames, 5 in all. The
  maintainer's run is to be repeated.
- **The test tables for digiemu** (`_scratch/chordtables-digiemu/`, not in the repository), made again: 01 to 03 are
  now the sine and 31 frames, 04 the sine and the organ cycle. Each starts with a sine (`starts_with_sine`). They are
  to be written into `/Wavetables` again with `ekfsadd.py`, replacing the old ones.

### 16.3 The warning, in One-Shot's uploader (2026-10-24)

The maintainer's choice: One-Shot's uploader warns when a file in `Wavetables` does not start with a sine. It lives
in the One-Shot repository (`cycles-one-shot`, `uploader/`), not in model27.

- **`elektron.js`:** `startsWithSine(frames)`, the test of `tools/wavetable.py`:
  - a DFT of the first 256 samples;
  - harmonic 1 above half of full level, in sine phase (±0,05 rad);
  - DC and every other harmonic under a thousandth of it;
  - with `WAVETABLES = "/Wavetables"`.
- **`app.js`:**
  - the conversion now hands back the frames;
  - in `/Wavetables` a file whose first frame fails is still written;
  - its row ends "warning: its first frame is not a sine, so SWEEP 0 plays no sine with CHORD Tables", in a new
    warning colour (light and dark);
  - the status line counts the warnings.
- **Tests,** both green (`make uploader-test`):
  - `test.js`: a sine, a table starting with one, and a sine one step off here and there pass; a cosine, a sine with
    harmonic 2, a saw, a sine with DC and fewer than 256 samples do not;
  - `test-app.js`: `/Wavetables` is made and entered; a table that starts with a sine is written without a warning,
    and the 440 Hz tone is written with one; the status line says "1 with a warning"; no warning outside
    `/Wavetables`.
- **Docs:** README and TECHNICAL §12 of One-Shot. Not committed there.
- **Not done:** not tried in a real browser against the Cycles.

### 16.4 Files CHORD Tables cannot play are not uploaded (2026-10-24)

The maintainer, the same day: a warning for files CHORD Tables cannot play at all, and those are not imported.

- **`elektron.js`:** `tableFrames(frames)`, the loader's rule of `load_one`:
  - 1 to 32 frames of 256 samples, or 0;
  - `TABLE_MAX = 32`;
  - the loader's other rule, mono, the page always meets.
- **`app.js`:**
  - in `/Wavetables` the check runs after the conversion and before the file is opened for writing;
  - a file that fails is not written, and its row reads "failed: CHORD Tables cannot play it: N samples are not 1
    to 32 frames of 256 (a 48 kHz WAV of k × 256 samples, as model27's tools/wavetable.py makes it); not uploaded";
  - the status line adds "N not uploaded: CHORD Tables cannot play it.";
  - a table that passes and does not start with a sine is written with §16.3's warning, as before.
  - A WAV at another rate than 48 kHz is resampled by the browser (§11.4) and usually fails here.
- **Tests,** both green (`make uploader-test`):
  - `test.js`: 1, 2 and 32 frames pass; nothing, 300, 33 frames, 48 000 and 255 samples do not;
  - `test-app.js`: in `/Wavetables` a sine-first table is written without a warning, a saw-first one with it; a
    second of tone (48 000 samples) is refused with its reason, is not on the drive and is never opened for
    writing, while the table uploaded with it is; the status line reads "1 of 2 uploaded to /Wavetables. 1 not
    uploaded: CHORD Tables cannot play it."
- **Docs:** One-Shot's README and TECHNICAL §12. Not committed there.

### 16.5 The fourth run (the maintainer, 2026-10-24)

`test_chordtables.py`, with the converter's sine in front: **ALL OK** for chordtables, chordtables + sampler and
sampler + chordtables `[FAIT en émulation]`.
- P2a builds file 08, made by `tools/wavetable.py` from a 4-frame saw table, as the sine and 4 frames, exactly as
  computed.
- Everything else is as in §15.4: P1, P2 and the cost, +22 instructions per block per voice at Wavetable 0 and −1
  on a table.

## 17. Tested on the Model:Cycles (2026-10-24)

- **The maintainer**, once the steps of §15.3 were handed over: "getestet, funktioniert".
- **What was ready for the test:**
  - the compose builds `build/model-cycles_OS1.13-chordtables.syx` (`e4dafb31…`, MAIN OS `f796d93e…`) and
    `…-sampler+chordtables.syx` (`77a10a97…`, MAIN OS `be21c9a0…`), rebuilt the same day byte for byte;
  - the test tables of §16, the sine in front, and One-Shot's uploader (`d78c8a0`) for `/Wavetables`.
- **Not said:**
  - which of the two builds was flashed;
  - which points of §15.3's list were tried one by one;
  - how the tables got onto the +Drive, and whether the uploader's refusal was tried.
- **From this date** the package's `tests.hardware` holds the test and its status is `tested` (model27's rule 3).
- **Next: W7**, the card in the flasher, the guide and the release in English and French, then the standard's
  section on extensions (draft 0.5).

## 18. The interface lags with tables (2026-10-24)

- **The maintainer's report,** after the device test: now and then the Cycles gets laggy with custom wavetables.
  Asked what: the screen and the knobs react late, the whole interface. The maintainer's reading: the audio load. It
  gets worse with every CHORD track playing a table.
- **Where a table costs more than the stock table** (code reading):
  - the stock frames are in the internal SRAM (`0x80001c5c..`, `0x8000cac0..`): one cycle an access, not cached
    (notes/26 §1, 27 §3.3);
  - a table's frames are in SDRAM (`0x43400000..`). The OS makes `0x40000000..0x47ffffff` cacheable, copyback:
    `movec ACR0` with `0x4007e020` at `0x40000552` `[FAIT]`;
  - the MCF54415 has an 8 KB data cache (512 lines of 16 bytes), and its SDRAM is DDR2 on 8 bits (notes/26 §1).
    With six voices, mixing, effects and the interface, almost every line is read again in every block (notes/26
    §1);
  - a CHORD voice reads two frames of 1 028 bytes a block, about 130 lines: about +0,6 to +1,2 points of the block
    per voice (notes/27 §3.3, 28 §4). Estimated, never measured on a table;
  - `test_chordtables.py` part C counts instructions, and the emulator does not time memory: −1 instruction with a
    table says nothing about this.
- **The loader** runs before the screen's redraw. Every tick it sums the drive's file index, and after any file is
  written or deleted it opens `/Wavetables/01`–`64` again by path, one per tick. That would lag now and then, after a
  save or an upload, not more with every CHORD track. It is not what the maintainer sees.
- **The measurement** `tools/emu/probe_chord_lines.py`, in the real voice loop: the 16-byte lines of SDRAM read or
  written per block (those of a table's frames apart), the same accesses through a model of the data cache (8 KB,
  4 ways, LRU, write allocate, the voice loop alone), and the SRAM lines. Each case is minus the loop with no note:
  - one CHORD track, note 60 and 84, SWEEP still or moving: the stock OS, Wavetable 0, a table;
  - six CHORD tracks, SWEEP still or moving: the stock OS, Wavetable 0, six tables, one table on all six.

  A MAC with a load is run by `emac.py` through `uc.mem_read`, which no Unicorn hook sees. The probe notes its
  address itself.
- **What it decides:** whether the frames read in SDRAM are what the extra lines are. If so, the fix sketched for
  the maintainer: each CHORD track gets its two current frames in SRAM (6 × 2 × 1 028 = 12 336 bytes), copied when
  SWEEP reaches another frame. The room is the stock table's SRAM, read by CHORD alone (notes/27 §3.3), with the stock
  frames copied into the RAM claim at start. Modded-Cycles' Syntakt engines already moved them to SDRAM, and CHORD
  ran as before on the device (notes/28, 29). Not built; to plan after the measurement.
- W7 waits until then.

### 18.1 The measurement (the maintainer, 2026-10-24)

`probe_chord_lines.py`, 22 blocks after the note's first one, minus the loop with no note `[FAIT en émulation]`.
Lines of 16 bytes per block (mean):

| Case | SDRAM lines | of them a table's frames | Cache misses, voice loop alone (write backs) | SRAM lines |
|---|---|---|---|---|
| 1 track, note 60, SWEEP 24: stock OS | 53 | 0 | 0 (0) | 180 |
| the same, Wavetable 0 | 54 | 0 | 0 (0) | 180 |
| the same, a table | 163 | 110 | 6 (0) | 72 |
| 1 track, note 60, SWEEP moving: a table | 163 | 110 | 51 (0) | 72 |
| 1 track, note 84, SWEEP 24: stock OS | 53 | 0 | 0 (0) | 191 |
| the same, a table | 174 | 121 | 6 (0) | 72 |
| 6 tracks, note 60, SWEEP still: stock OS | 277 | 0 | 1 (1) | 722 |
| the same, Wavetable 0 | 279 | 0 | 5 (4) | 722 |
| the same, six tables | 931 | 658 | 941 (246) | 72 |
| the same, one table on all six | 931 | 658 | 914 (228) | 72 |
| 6 tracks, SWEEP moving: stock OS | 295 | 0 | 22 (12) | 692 |
| the same, six tables | 920 | 646 | 929 (246) | 72 |

What it shows:
- **A CHORD track on a table reads 110 to 121 more lines of SDRAM a block** (note 60 to 84), all of them its two
  frames. The stock OS reads the same frames in SRAM: 108 to 119 SRAM lines fewer with a table. A CHORD voice's own
  SDRAM lines (its state, 53) are tripled.
- **Wavetable 0 costs nothing that counts:** +1 or +2 lines (`cw_setup`'s own).
- **Six CHORD tracks on tables:** 277 → 931 lines a block (×3,4). The cache model shows why it is worse than the sum:
  six voices' frames, about 660 lines, are more than the cache's 512. Even with the voice loop alone, every block then
  misses 941 times instead of once, and 246 dirty lines of the voices' state are written back. With mixing, effects
  and the interface between two blocks, the cost lies between the distinct lines (+654) and that (+940 fills, +246
  write backs).
- **The frames are read by MACs with a load:** the same number in every case, per track (19 964 in a run of one
  track, 6 × that with six tracks). `emac.py` runs them through `uc.mem_read`, so only the probe's own note of their
  address shows a table's lines at all.
- **One table shared by six tracks** reads as many lines as six tables, since each track's SWEEP is another frame.
  The probe's check assumed fewer lines: that one FAIL was the probe's fault, not the firmware's. The check now
  asks only that both read their frames in the RAM claim.
- **In time:** the emulator does not time memory, and the time of a line in SDRAM (DDR2 on 8 bits) is not known
  (notes/26 §6). By notes/27 §3.3's estimate, about 130 lines ≈ +0,6 to +1,2 points of the block: about the same per
  CHORD track, and more with six for the cache's sake. It matches the maintainer's lag, growing with every track.

The maintainer's report and this measurement agree: the lag is the frames read in SDRAM. The fix is the one sketched
above (each track's two frames in SRAM), to be planned. With SWEEP moving as in the probe (about one frame a block),
a copy of one frame (65 lines) a block would remain; with SWEEP still, one copy at the note's start.

## 19. Plan: the frames CHORD plays, in SRAM (2026-10-24)

The maintainer's request after §18.1: plan the fix with the frames in SRAM. Code reading of the stock MAIN OS 1.13
(`[FAIT]` unless marked), then the design, its proofs, and the decisions for the maintainer.

### 19.1 How CHORD reads its frames `[FAIT]` (code reading)

- **The selector** `0x400a8060(n)`: `n − 1` unsigned above 31 gives the sine `0x8000eee4`; otherwise entry `n − 1` of
  `0x40118590`. The setup `0x400a8080` takes `i = SWEEP >> 10` (arithmetic: negative for a negative SWEEP),
  `f0 = sel(i)`, `f1 = sel(i + 1)`, the crossfade `(SWEEP & 1023) << 21`, and writes the four sub-voices: `+188` ←
  `+184`, then `+168` f0, `+172` f1, `+156` crossfade, `+184` i.
- **The stock table** `0x40118590`:
  - entry 0 (frame 1) is `0x40118648`, in SDRAM, in the OS's data: stock CHORD already reads it between SWEEP 0
    and 15;
  - entries 1 to 30 are the 30 frames in SRAM, 1 028 bytes apart: 22 in `0x80001c5c..0x800074b4`, 8 in
    `0x8000cac0..0x8000eae0`;
  - entry 31 repeats entry 30 (`0x8000cac0`).
- **The render reads the previous block's frames too.**
  - Before its loop, it compares `+188` with `+184` and the new f0 with `+176`.
  - Index up by one: the block fades from the previous f0 (`+176`) to the new f0. Down by one: from the previous f1
    (`+180`) to the new f1. Another frame: the block plays the previous pair (`+176`, `+180`) while its gains
    `+160`/`+164` move. Otherwise: the usual crossfade of f0 and f1.
  - Then it saves `+168` → `+176` and `+172` → `+180` (`0x400a860c`; the same in the second render,
    `0x400a88d8`).
  - So **in a block where the frame changes, CHORD reads up to four frames**: the two of this block and the two of
    the previous one.
- **The reset** `0x400a7ab8` sets `+168`..`+180` to the sine and clears `+156`, `+160`, `+164`, `+184`, `+188`
  (`0x400a7b52`..`0x400a7bbe`).
- **CHORD's update** `0x400aae88` reaches the setup call at `0x400ab15e` on every path: `cw_setup` runs every
  block, as part C of `test_chordtables.py` counts. After it, the update can switch off a sub-voice whose pitch is
  too high (`clrl a2@(8, d0*4)`, `0x400ab20c`). Such a sub-voice keeps its `+176`/`+180` until it plays again.
- **Other machines** write the same voice offsets with their own values: the sine at `0x400aa342`, `0x4012024c` at
  `0x400aa9da`. They never point into the stock table's SRAM.
- **Who else reads the 30 SRAM frames:** only the selector, through `0x40118590` (notes/27 §3.3). Modded-Cycles'
  Syntakt engines put code and voice states there and CHORD played normally on the device (notes/28, 29 §1).
- **Who else writes there in model27:** the sources of SAMPLE, the shortcut layer and the dispatchers, and the
  registrar's, name no SRAM address but the sound pointers and the targets (`0x800015ae`, `0x800017e4`,
  `0x800017ec`). What SAMPLE reaches through the stock voice chain are the OS's own buffers, outside the table. The
  Syntakt engines' tweaks (not offered) put their SRAM banks there at boot, and the payload already excludes them.

### 19.2 Why two slots per track are not enough

The sketch of §18 gave each track two frames. With §19.1, a block that moves SWEEP to the next frame reads three
frames (the previous f0, the frame shared by both pairs, the new f1), and a jump reads four. Copying the new f1 over
the previous f0 would change what that block plays. A sub-voice switched off for its pitch keeps two more frames in
use. A fixed number per track either wastes SRAM or breaks the identity with the stock OS.

### 19.3 The design: a shared pool of 30 SRAM frames

- **The pool** is the stock table's 30 SRAM frames, at their own addresses (read from `0x40118594..0x40118608` at
  run time, not written into the package). Each slot has a tag: the address of the frame it holds a copy of.
- **The move, once, on the tick** (UI task), before anything else:
  - the 30 frames copied into the RAM claim, as a stock table of 33 pointers (`0x40118648` for frame 1, as in the
    OS);
  - each slot tagged with its own frame's copy, so that a track playing a stock frame keeps the same pointer;
  - then a flag. Until it is set, `cw_setup` works as in 0.1.
- **`cw_setup` after the move**, for every CHORD track and every Wavetable:
  - the sources: for Wavetable 0 the stock selector's rule on the stock table copy, a negative SWEEP and its index
    included (stock semantics, which 0.1 got from the stock function); for a table as in 0.1;
  - each source is mapped to the address the render reads, in this order:
    1. a source in SRAM (the sine): itself;
    2. a slot tagged with it: that slot;
    3. a source one of the six voices still points at (`+168`..`+180` of the four sub-voices): itself;
    4. a slot no voice points at (the oldest used): the source copied in (1 028 bytes, 257 longs), the slot
       tagged;
    5. no such slot: the source itself, in SDRAM, as in 0.1;
  - a fast path: the same two sources as in the previous block keep their two pointers.
- **Why the sound stays the same, sample for sample.**
  - The render reads only `+168`..`+180`, and a slot a voice points at is never written.
  - A source maps to the same pointer as long as some voice points at it, and two sources never share a pointer.
  - So every comparison of the render (`+176` with the new f0) comes out as with the sources' own addresses. That
    is the stock OS at Wavetable 0, and 0.1 with a table.
- **The loader:** a buffer becomes free again only once no latch and no voice pointer reaches into it. When it
  does, the tags of slots holding its frames are cleared before it is built again. This also closes a case 0.1
  leaves open: a sub-voice switched off for its pitch could still point into a reused buffer.
- **Memory:**
  - the stock table copy is one more buffer in the RAM claim (73 × 33 040 + 16 384 bytes, to `0x43650d90`, inside
    `0x43700000`);
  - the 30 tags and the voices' last sources take a few hundred bytes of the package's variables;
  - the SRAM is declared (§19.5).
- **Cost** (to measure with `probe_chord_lines.py`):
  - SWEEP still: the frames are copied once, at the note's start, and then read in SRAM. That is about what the
    stock OS reads, and frame 1 now too.
  - SWEEP moving one frame a block (the probe's case): one frame copied a block, 65 lines, against 110 to 121 now.
  - Shared frames are copied once for every track that plays them.
  - The scan for free slots (96 pointers) runs only when a frame changes.

### 19.4 Proofs and done criteria

- **P1 again, with the move done**, on the OS's own code (`test_chordtables.py`):
  - Wavetable 0 identical to the stock OS, sample for sample, on six CHORD tracks: SWEEP moving, jumping and
    negative, high notes (sub-voices switched off), retrigs, a machine change;
  - tables identical to 0.1, sample for sample, the same scenarios with six tables and one shared;
  - the move while notes play: identical to the stock OS across it.
- **P5, the pool:** a hook on SRAM writes. No slot a voice points at is ever written. After the move, no frame is
  read in SDRAM except through rule 5, which is counted (0 in the proofs' scenarios).
- **P2 again:** the loader, with the reclaim waiting for the voices' pointers and clearing tags.
- **The probe** with 0.2: SDRAM lines per block, against §18.1.
- **The cost** (part C): instructions per block per voice.
- **The device (the maintainer):**
  - six CHORD tracks on tables: does the lag go?
  - Wavetable 0 against the official OS;
  - SAMPLE next to it.

### 19.5 The standard and the claims

- **A use of the OS's own memory** that the stock OS gives a stock machine: new to the standard. A package that
  extends that machine may take it, and must keep the machine's sound. It is to be written in draft 0.5's section on
  extensions (W7), and declared in the manifest:
  - a use `{"point": "memory.sram", "range": …, "takes": "CHORD's frames"}`;
  - its two ranges in the claims' `ram`, which already take any range.
- `compose.py` and `composer.js` must accept the point. `check_package` compares only `memory.ram` with the claims,
  and has to learn `memory.sram` too.

### 19.6 Steps

1. **S1, the code:** CHORD Tables 0.2 (`chordtables.c`: the move, the pool, the stock rule for Wavetable 0, the
   reclaim), the manifest (version, `memory.sram`, claims), the builder's acceptance of the point,
   `gen_chordtables.py`, the committed object and tweak.
2. **S2, the proofs:** P1, P2 and P5 in `test_chordtables.py`, run by the maintainer.
3. **S3, the probe** with 0.2, run by the maintainer.
4. **S4, the device:** the maintainer's load test.
5. **Then W7**, with 0.2: the card, the guide, the release.

### 19.7 Decisions for the maintainer

1. **The pool in the stock table's SRAM** (recommended): only CHORD reads it, and CHORD played normally with it
   taken by the Syntakt engines. The other way, finding 12 to 30 KB of SRAM the stock OS leaves free, needs a
   survey of the whole SRAM first.
2. **Wavetable 0 through the pool too:** the consequence of 1. The proof holds it to the stock OS, sample for
   sample. Frame 1, in SDRAM in the stock OS, then gets an SRAM slot too.
3. **Version 0.2, status back to `experimental`** until the device test (model27's rule 3); W7 offers 0.2.

### 19.8 Decided (2026-10-24)

The maintainer takes the three recommendations of §19.7:
1. the pool is the stock table's 30 SRAM frames;
2. Wavetable 0 goes through the pool too, held to the stock OS sample for sample;
3. CHORD Tables 0.2, `experimental` until the device test; W7 offers 0.2.

Next: S1, the code (§19.6).

## 20. S1 built: CHORD Tables 0.2 (2026-10-24)

### 20.1 What was built

- **`chordtables.c`** (§19.3):
  - `move()`, called by the first tick before anything else:
    - the stock table `0x40118590` read at run time; each of its frames in SRAM copied once into `STOCK`, the
      buffer after the 72 (`0x43648c80`, 33 pointers then the copies), frames in SDRAM kept where they are
      (`0x40118648`, frame 1), the sine at index 0;
    - each SRAM frame becomes slot k of the pool (`ct_pool_addr`), tagged with its copy (`ct_pool_tag`), and the
      KB of SRAM it starts in is noted (`kb_slot`, 64 bytes): an address finds its slot in one look;
    - a frame starting in another's KB, or more than 32, refuses the move for good (`ct_moved` = `0xff`, 0.1's
      way). Otherwise a compiler barrier, then `ct_moved` = 1.
  - `cw_setup`:
    - before the move as in 0.1;
    - after it, Wavetable 0 takes the stock function's work on the copy: `i = SWEEP >> 10` signed, the crossfade,
      `f0 = sel(i)`, `f1 = sel(i + 1)`, with the selector's rule (0 to 32 the copy's pointer, the sine outside), and
      `+184` = i, negative SWEEP included. A table as in 0.1;
    - both sources go through `map()`. Its fast path keeps the last block's two pointers when the sources are the
      same and sub-voice 0 still holds them (`+168`, `+172`); else `remap()`, out of line.
  - `remap()`:
    - rules 1 and 2 by `held()`;
    - one scan of the six voices' 96 pointers (`pinned()`) gives the slots in use and whether a voice points at
      either source;
    - `place()` takes the slot mapped longest ago outside those, copies the 257 longs, tags it. With no such slot
      it reads the source where it is and counts it (`ct_fallback`).
  - `reclaim()`: a retired buffer becomes free only once no latch and no voice pointer reaches into it
    (`pointed_into()`, always, also before the move). Then the tags of the slots holding its frames are cleared.
- **The manifest:**
  - version 0.2;
  - the roots `ct_moved`, `ct_pool_addr`, `ct_pool_tag`, `ct_pool_n`, `ct_fallback` and `ct_tick`, for the proofs
    (`ct_tick` since S2: the voice harness makes the move with it);
  - two `memory.sram` uses (`0x80001c5c..0x800074b4`, `0x8000cac0..0x8000eae0`, "CHORD's frames"), and the same two
    ranges in the claims' `ram`;
  - `tests.emulation` and `tests.hardware` by version: 0.1 as recorded, 0.2 not yet run;
  - status `experimental` (§19.8).
- **The builder:**
  - `compose.load_manifest` refuses `memory.sram` in a package that extends no stock machine;
  - `claims.check_package` counts `memory.sram` with `memory.ram`;
  - `web_package` leaves the point out, as it leaves every use the page does not place. `composer.js` needs no
    change: the claims carry the ranges.
- **Outputs:** `chordtables.o` and `36-chordtables.json` (9 writes, 4 696 bytes added to the image, 269 conflicts
  computed, as in 0.1), `REGISTRY.md` (its size, the two SRAM ranges).

### 20.2 Measured

| | 0.1 | 0.2 |
|---|---|---|
| code | 1 465 bytes | 4 093 bytes |
| variables | 624 bytes | 1 184 bytes |
| added to the image | 2 068 bytes | 4 696 bytes |
| `cw_setup` (the audio's path every block) | — | 666 bytes |
| `remap` (only when a frame changes) | — | 1 542 bytes |

The scan of `remap` is unrolled by GCC (6 × 4 × 4 pointers). It runs only on a frame change and stays out of the
blocks whose frames stay.

### 20.3 Checks (here, no emulation)

- `gen_chordtables.py --check`: up to date.
- `claims.py --check --self-test`, `check_overlaps.py`, `registry.py --check` (regenerated), and
  `gen_flasher_tweaks.py --check` (on the committed card list, the paused W7 card set aside): all OK.
- `webcompose_check.sh` with the official file: `composer.js` places and composes chordtables, chordtables +
  sampler and sampler + chordtables as `compose.py` does, byte for byte (MAIN OS `ddffb376…`, `a9957615…`,
  `a908937b…`, with `ct_tick` exported), and every other build as before.
- `py_compile`: OK.

### 20.4 Not yet proven: S2

`test_chordtables.py` as it is does not prove 0.2, and P2 will stop. Its UI harness maps no SRAM, and the first
tick's move reads the stock frames there. S2 is to:
- map the SRAM in the UI harness, with its boot content as `mcengine.Engine` writes it;
- run the move before P1's cases (the tick, or `move` through its effect: `ct_moved`, `STOCK`, the slots);
- add §19.4's cases: Wavetable 0 against the stock OS and tables against 0.1, sample for sample, on six tracks
  with SWEEP moving, jumping and negative, high notes, retrigs and a machine change, the move while notes play;
- P5, with a hook on SRAM writes;
- P2 again, with the reclaim waiting for the voices' pointers.

## 21. S2 prepared: the proofs of 0.2 (2026-10-24)

`tools/emu/test_chordtables.py` grows the cases of §19.4. The run is the maintainer's (Unicorn stops with SIGILL in
this sandbox). Run here: the pure Python parts. They give the pool's 30 slots from the stock table, in two runs
equal to the manifest's `memory.sram` ranges, and the scenario: 36 notes, 33 negative SWEEP values.

- **The harnesses:**
  - `sram_boot()` maps the SRAM in the UI harness with its two boot images, as `mcengine.Engine` writes them. The
    loader's first tick makes the move there;
  - `Voice.move()` calls the package's own `ct_tick` with the file system's page mapped and zero (not mounted), so
    that the tick does the move and nothing else. `ct_tick` is a root for that (§20.1).
- **P1m:** six CHORD tracks (`Six`), one scenario of 120 blocks the same for every OS (`scenario()`, seed 66):
  - notes now and then, high ones (96 to 120) on tracks 5 and 6;
  - SWEEP creeping, jumping, negative now and then, fast, still and anywhere;
  - the chord shape changed at each note, track 3 to TONE in block 60 and back in 70;
  - with tables: tables 1 to 3 on tracks 1 to 3, track 4 sharing table 3, Wavetable 0 on tracks 5 and 6, and
    track 2 changing to table 5 during a note.

  The cases:
  - a: Wavetable 0, moved before the first note, against the stock OS;
  - b: the tables, moved before the first note, against the same build without the move (0.1's way, which P1a to
    P1e hold to the stock OS and the computed frames), and tracks 5 and 6 against the stock OS;
  - c and d: the same with the move in block 40, while notes play;
  - e: the move itself. The slots in the stock table's order, their tags in the copy and equal to the frames, the
    copy's 33 pointers as the selector's (the sine, frame 1 at `0x40118648`, frame 32 = frame 31).
- **P5,** in each P1m run (`Watch`): a hook on writes into the pool's two runs of SRAM.
  - No slot a voice points at is written, checked at each copy's first word against the six voices' 96 pointers.
  - No write from outside the package.
  - The stock OS never writes there over the scenario.
  - With the move before the first note, after every block every CHORD voice's 16 pointers are in SRAM, and
    `ct_fallback` is 0.
  - Findings: the frames copied per block, and the voice-blocks with a sub-voice switched off.
- **P2h:** the loader's first tick made the move (`ct_moved` 1, the 30 slots).
- **P2i,** in place of P2d's last check:
  - the latch let go while a voice still points into the old buffer (track 3, second sub-voice, `+176`), and a
    slot tagged with one of its frames: the buffer stays retired and the tag stays;
  - the pointer cleared: free at the next tick, the tag cleared.
- **C:** the cost after the move, SWEEP still (the fast path, checked under +200 / +300 instructions against stock
  CHORD). As findings: SWEEP creeping (a frame about every 1,3 blocks), before and after the move, the copies' and
  the scan's price in instructions.

What the maintainer runs:

```sh
../.venv-emu/bin/python3 tools/emu/test_chordtables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

### 21.1 The run (the maintainer, 2026-10-24)

`test_chordtables.py`: **ALL OK** for chordtables, chordtables + sampler and sampler + chordtables
`[FAIT en émulation]`. Every check of P1 to P2 as before; P1m a to e, P5, P2h and P2i new and OK in all three.

- **Identical, sample for sample, over 120 blocks of six CHORD tracks:**
  - Wavetable 0 against the stock OS, with the move before the first note and in block 40;
  - the tables against the same build without the move, both ways;
  - the tables' tracks 5 and 6 (Wavetable 0) against the stock OS.

  The scenario switched sub-voices off in 627 CHORD voice-blocks. The case of §19.1 is covered.
- **P5:**
  - no slot written while a voice pointed at it;
  - no write into the pool but the package's;
  - the stock OS never writes the stock frames;
  - after every block, every CHORD voice's 16 pointers in SRAM;
  - `ct_fallback` 0.
- **Frames copied into the pool over the 120 blocks** (six tracks):

  | Case | Frames copied | per block |
  |---|---|---|
  | a. Wavetable 0 | 37 | 0,31 |
  | b. tables | 497 | 4,14 |
  | c. Wavetable 0, moved in block 40 | 26 | 0,22 |
  | d. tables, moved in block 40 | 357 | 2,98 |

  Wavetable 0 copies little: its frames are in slots tagged since the move. Only frame 1 (in SDRAM in the OS) and
  frames whose slots tables took are copied.
- **The cost** (instructions per block per voice, CHORD alone, minus the loop with no note):

  | | first block | mean | max |
  |---|---|---|---|
  | stock CHORD | 8 737 | 8 292 | 8 300 |
  | Wavetable 0, before the move | 8 782 | 8 318 | 8 326 |
  | a table, before the move | 8 758 | 8 294 | 8 302 |
  | Wavetable 0, moved | 8 885 | 8 333 | 8 341 |
  | a table, moved | 14 906 | 8 327 | 8 335 |

  With SWEEP still, the fast path costs +41 (Wavetable 0) and +35 (a table) against stock CHORD. The note's
  first block costs +6 100 with a table: the two frames copied in, and the scan.
- **SWEEP creeping** (3 a block, a frame about every 1,3 blocks):
  - **a table: 8 285 before the move, 11 902 after it (max 13 065), +3 617 instructions a block;**
  - Wavetable 0: 8 309 → 8 463, since its frames are tagged since the move.

### 21.2 What the run says for the device

- **SWEEP still**, the usual case on a held chord: the frames are read in SRAM (P5) for +35 to +41 instructions a
  block. That is what §18.1's 110 to 121 SDRAM lines a block were.
- **SWEEP moving on a table:** each new frame costs a copy, 65 lines of SDRAM read once, plus about 2 700
  instructions (the scan of 96 pointers, the search of the tags, the copy), +3 617 a block in the probe's
  creeping case. It reads about half the lines 0.1 reads, but adds 44 % to a CHORD voice's instructions.
  - Whether that is a gain depends on the time of a line in SDRAM (DDR2 on 8 bits, notes/26 §1), which no
    emulator here gives.
  - With six tables the cache thrashes (§18.1, 941 misses a block), so lines may cost more than their count. Only
    the device can tell.
- **What could cut that price**, not built:
  - the scan reads only the voice's own 16 pointers and keeps a mask per voice of the slots it may point at;
  - the copy in long moves of 8.

  To weigh after S3 (the lines with 0.2) and the device's word on a table with an LFO on SWEEP.

## 22. The price of a moving SWEEP lowered (2026-10-24)

The maintainer, after §21.2: not committed yet; first lower the price of a moving SWEEP (a mask per voice, a faster
copy).

### 22.1 What changed in `chordtables.c`

- **A mask per voice instead of the scan of 96 pointers.**
  - `pin[t]` holds the slots voice t may point at, and `far[t]` whether it may point at a frame outside SRAM.
  - In its remap a voice reads only its own 16 pointers (`own()`) and adds its two new ones. The other voices' slots
    come from their masks.
  - This holds because a voice's pointers change only in its own setup, in its render (`+168` → `+176`, `+172` →
    `+180`, §19.1) and at the reset (the sine). So a mask taken at a voice's remap covers it until its next one, also
    for an idle voice or a sub-voice switched off.
- **Rule 3 looks only at voices with `far` set.** A frame is read where it is only before the move or for want of a
  slot, so the 96-pointer search is gone from the usual case.
- **The move is handed to the audio.** The tick copies and sets `ct_moved` to 2, ready. The audio's next setup
  (`adopt()`, out of line, once) takes every voice's mask from its pointers and sets 1.
  - Reading the pointers in the audio itself means none can change under the reading. The UI task could be
    interrupted between two voices.
- **Rule 2 looks first where the track had its two sources.** When SWEEP creeps, the new f0 is the old f1, and its
  slot is found at once, its tag checked.
- **The slot taken:** the next free one after the last taken, by `ff1` on the free mask, in place of the
  oldest-used search over 30. `pool_used` and the setup count are gone.
- **The copy:** `copy_frame()`, 32 `movem.l` of 8 longs and the last long, in place of 257 single moves.

### 22.2 Measured here

- **Outputs:** `chordtables.o`, `36-chordtables.json` (9 writes, 5 268 bytes added to the image), `REGISTRY.md`.
- **Sizes:** code 4 665 bytes (4 093 before), variables 1 104 bytes (1 184), `cw_setup` 716 bytes (666),
  `remap` 1 584, `place` 260.
- **The object:** no library call (`nm -u` empty); `__builtin_clz` is the `ff1` instruction.
- **Checks:** `claims`, `check_overlaps`, `registry`, `gen_flasher_tweaks --check` (the W7 card set aside) and
  `webcompose_check` with the official file all OK. `composer.js` is identical to `compose.py`: MAIN OS
  `dd7a94bd…` alone, `37f13bce…` with SAMPLE after, `c814a39d…` with SAMPLE before.
- **The proofs:** P1m e and P2h now expect the hand-over: 2 after the tick, 1 after the audio's first setup with a
  note.
- **Estimate**, to be measured by part C: a remap that copies one frame costs about 500 to 700 instructions instead
  of about 2 700:
  - its own 16 pointers;
  - six masks;
  - the tag search, short when SWEEP creeps;
  - `ff1`;
  - a copy of about 200 instructions.

§21.1's run was on the code before this change: P1m, P5, P2 and the cost are to be run again.

### 22.3 The run of §22's code (the maintainer, 2026-10-24)

`test_chordtables.py`: **ALL OK** in the three builds `[FAIT en émulation]`:
- P1m a to e identical, sample for sample;
- P5: no slot written while in use, every frame in SRAM, `ct_fallback` 0;
- P2a to P2i;
- the hand-over: 2 after the tick, 1 after the audio's first setup.

| Instructions per block per voice | §21.1 | §22 |
|---|---|---|
| a table, moved, SWEEP still (mean) | 8 327 | 8 330 |
| a table, moved, first block | 14 906 | 12 352 |
| Wavetable 0, moved, first block (with the adoption) | 8 885 | 11 472 |
| **a table, SWEEP creeping, after the move** | **11 902** | **9 153** |
| Wavetable 0, SWEEP creeping, after the move | 8 463 | 8 833 |

- **A table with SWEEP creeping:** +864 instructions a block against 0.1's way (8 289), where §21.1 had +3 617.
  The price of a moving SWEEP is cut by three quarters. At about 0,75 copies a block that is about 1 150
  instructions a copied frame, not the 500 to 700 estimated in §22.2.
- **Wavetable 0 with SWEEP creeping got dearer:** +521 against +154.
  - Its frames are found in their slots, so it copies nothing. Each remap now reads the voice's 16 pointers
    (`own()`), which §21's code did only when it placed a frame.
  - The adoption (six voices' 16 pointers, once) is in Wavetable 0's first block.
- Frames copied over the 120 blocks: a 31, b 486, c 19, d 346 (37, 497, 26, 357 before). The slot after the last
  taken keeps a few more frames.

### 22.4 Two more cuts (2026-10-24)

- **`own()` looks up only what differs.** Sub-voices 2 to 4 hold sub-voice 1's four pointers unless one was
  switched off for its pitch, so only their pointers that differ are looked up: 4 lookups and 12 compares in the
  usual case, in place of 16 lookups.
- **Only CHORD voices count** (`chord_voice()`, the machine at `+0`), in the busy slots, in rule 3 and in the
  adoption.
  - Another machine's voice is never read by CHORD's render. It comes back to CHORD only through the reset, its
    pointers the sine (§19.1).
  - Its words at `+168`..`+180` are that machine's own, and are no longer counted as pins or as frames outside SRAM.
- **Outputs:** code 4 835 bytes, 5 436 bytes added to the image, `own` 266 bytes, `cw_setup` 716.
- **Checks:** all OK. `webcompose_check` gives MAIN OS `1abd04c2…`, `d9cc564c…` and `c4af0e27…`.
- **Not run yet:** the proofs.

### 22.5 The run of §22.4's code (the maintainer, 2026-10-24)

`test_chordtables.py`: **ALL OK** in the three builds `[FAIT en émulation]`, every check as in §22.3.

| Instructions per block per voice | §21.1 | §22.3 | §22.5 |
|---|---|---|---|
| a table, moved, SWEEP still (mean) | 8 327 | 8 330 | 8 330 |
| Wavetable 0, moved, SWEEP still (mean) | 8 333 | 8 333 | 8 333 |
| a table, moved, first block | 14 906 | 12 352 | 10 427 |
| Wavetable 0, moved, first block | 8 885 | 11 472 | 9 532 |
| **a table, SWEEP creeping** | **11 902** | 9 153 | **9 024** |
| **Wavetable 0, SWEEP creeping** | **8 463** | 8 833 | **8 692** |

Before the move (0.1's way): a table 8 289 and Wavetable 0 8 312 with SWEEP creeping; stock CHORD 8 292 with SWEEP
still.

- **A table with SWEEP creeping:** +735 instructions a block against 0.1's way, where §21.1 had +3 617. That is
  about 980 a copied frame. In exchange the frames are read in SRAM, and about half the SDRAM lines are no longer
  read (§21.2).
- **Wavetable 0 with SWEEP creeping:** +380 a block, against +154 in §21.1 and +521 in §22.3. It copies nothing,
  since its frames sit in their own slots. What it pays is the remap: its 16 pointers, the tag search for the new
  frame.
  - That is a price stock CHORD users pay for nothing in memory: the stock frames are in SRAM already, frame 1 aside.
  - Left: a direct look-up of a stock frame's own slot (its copy's index is its slot's), not built.
- **SWEEP still:** +38 (a table) and +41 (Wavetable 0) against stock CHORD, as before.
- **Frames copied over the 120 blocks:** a 31, b 490, c 19, d 350.

## 23. S3 prepared: the probe with 0.2 (2026-10-24)

`tools/emu/probe_chord_lines.py` measures 0.2 next to 0.1's way, with §18's method: distinct SDRAM lines per block,
the cache model of the voice loop alone, the SRAM lines, each minus the loop with no note.

- **The 0.2 cases:**
  - every CHORD Tables case again, with the move made by the package's own tick before the first block
    (`Voice.move()`, §21);
  - one track: Wavetable 0 and a table, notes 60 and 84, SWEEP at 24 and moving 3 a block;
  - six tracks: Wavetable 0, six tables and one table on all six, SWEEP still and moving.
- **"In the RAM claim"** is now what the copies into the pool read: a table's frames, or the stock frames' copy. In
  0.1's way it is what the render reads.
- **Checks:**
  - 0.2 adopted (`ct_moved` 1), and no frame read where it is for want of a slot (`ct_fallback` 0);
  - one track: fewer lines in the RAM claim than 0.1's way, and none after the note's first block with SWEEP
    still;
  - six tracks: fewer SDRAM lines than 0.1's way, with six tables and with one shared.
- **Findings:** for each case, 0.2's lines and misses against the stock OS, next to 0.1's way's.

The run is the maintainer's. Unicorn stops with SIGILL in this sandbox.

```sh
../.venv-emu/bin/python3 tools/emu/probe_chord_lines.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

### 23.1 The run (the maintainer, 2026-10-24)

`probe_chord_lines.py` `[FAIT en émulation]`: every 0.1 case as in §18.1. Two FAILs, both the probe's check: with
SWEEP still a table in 0.2 reads 1,0 line a block in the RAM claim, where the check asked for less than one. That line
is the table's pointer list, which `cw_setup` reads for its two sources every block (`ptrs[i]`, `ptrs[i + 1]`;
Wavetable 0 reads the stock copy's the same way). The frames come from SRAM. The check now allows that one line. A
new run would only turn those two lines to OK.

Lines of 16 bytes a block, minus the loop with no note, against the stock OS:

| Case | 0.1's way: SDRAM lines | 0.1: misses (write backs) | 0.2: SDRAM lines | 0.2: misses (write backs) |
|---|---|---|---|---|
| 1 track, note 60, SWEEP still, a table | +111 | +6 | **+6** | **0** |
| 1 track, note 84, SWEEP still, a table | +122 | +6 | **+6** | **0** |
| 1 track, note 60, SWEEP moving, a table | +110 | +51 | **+68** | +51 |
| 1 track, SWEEP still, Wavetable 0 | +2 | 0 | +6 | 0 |
| 1 track, SWEEP moving, Wavetable 0 | +2 | 0 | +13 | +1 |
| 6 tracks, SWEEP still, six tables | +655 | +941 (+245) | **+10** | **+28 (+14)** |
| 6 tracks, SWEEP still, one shared table | +655 | +915 | +10 | +38 |
| 6 tracks, SWEEP still, Wavetable 0 | +3 | +3 | +10 | +15 |
| 6 tracks, SWEEP moving, six tables | +626 | +909 (+234) | **+310** | **+468 (+136)** |
| 6 tracks, SWEEP moving, one shared table | +623 | +890 | +86 | +157 |
| 6 tracks, SWEEP moving, Wavetable 0 | +3 | +4 | **+43** | **+76 (+34)** |

What it shows:
- **SWEEP still, the held chord:** 0.2 does what §19 set out to do. Six tracks on tables read 287 lines a block
  instead of 932, ten more than the stock OS. The cache model misses 29 times instead of 942. With one track, a
  table costs six lines a block: its pointer list and the package's own variables.
- **SWEEP moving on tables:** about half. Six tables 605 lines a block instead of 921, 490 misses instead of 931.
  The copies of new frames read 51 lines a block per track in the RAM claim, about 65 for each new frame. One table
  shared by six tracks gains most (381 lines), since a frame one track copied serves the others.
- **Wavetable 0 with SWEEP moving got worse than the stock OS:** six tracks +43 lines and +76 misses a block, where
  0.1's way had +3 and +4. 0.2 copies frames for it, 38 lines a block in the RAM claim:
  - frame 1, which the stock OS reads where it is (`0x40118648`), gets a slot;
  - that slot is a stock frame's own, so that frame, when SWEEP reaches it, is copied back from the stock copy
    into another slot, and so on.

  That is a price for CHORD users who play no table at all, on top of the +380 instructions a block of §22.5.
- **The cure** (not built):
  - frame 1 and any stock frame outside SRAM read where it is, as the stock OS reads it;
  - a stock frame's copy going back to its own slot when that is free;
  - a table's frame taking first a slot that does not hold its own stock frame.

  Then Wavetable 0 alone copies nothing, and tables leave the stock frames in place while other slots are free.

## 24. The cure for Wavetable 0 (2026-10-24)

The maintainer, after §23.1: build the cure for Wavetable 0.

### 24.1 What changed in `chordtables.c`

1. **A stock frame outside SRAM is read where it is**, as the stock OS reads it (frame 1, `0x40118648`, in the OS's
   data).
   - Rule 1 now takes every source outside SRAM and outside the RAM claim (`IN_CLAIM`). A source maps to itself,
     always: the render's comparisons stay as on the stock OS.
   - `far` now means "may point into the RAM claim" (a table's frame, or the stock copy, read where it is). That is
     the only kind of frame rule 3 has to look for.
2. **A stock frame's copy goes back to its own slot.**
   - `home_of(s)` tells a copy's slot from its address: slot k's copy is at `COPY0 + 1 028 k`, laid out in the
     move's order.
   - `held()` looks there first.
   - `place()` puts a copy into its own slot when that slot is free.
3. **A table's frame takes first a slot not holding its own stock frame.** `home` holds the slots that do: all 30
   after the move, kept by `place()` at each copy. The tags the reclaim clears are a table's, never at home. The
   next free slot after the last taken is used only among the others first.

### 24.2 Measured here

- **Outputs:** code 4 841 bytes, 5 444 bytes added to the image; `remap` 1 220 bytes (1 598), `place` 480, `held`
  306, `cw_setup` 716.
- **The object:** no library call (`nm -u` empty).
- **Checks:** all OK. `webcompose_check` gives MAIN OS `57ac7df5…`, `8e647b9a…` and `0719c706…`.
- **The proofs** (`test_chordtables.py`):
  - P5 accepts frame 1 where the OS has it;
  - P5 now asks that Wavetable 0 alone copies nothing (P1m a and c).
- **Not run yet:** the proofs and the probe.

### 24.3 The probe with the cure (the maintainer, 2026-10-24)

`probe_chord_lines.py`: **ALL OK** `[FAIT en émulation]`. Both FAILs of §23.1 are now OK with the corrected check.
Against the stock OS, per block:

| Case | 0.1's way | 0.2 §23.1 | 0.2 with the cure |
|---|---|---|---|
| 6 tracks, SWEEP moving, Wavetable 0: lines (misses) | +4 (+5) | +43 (+76) | **+25 (+49)** |
| the same: lines in the RAM claim | 0 | 38 | **5** |
| 1 track, SWEEP moving, Wavetable 0: lines | +2 | +13 | +12 |
| 6 tracks, SWEEP moving, six tables: lines (misses) | +627 (+910) | +310 (+468) | +311 (+471) |
| **6 tracks, SWEEP moving, one shared table: lines (misses)** | +624 (+891) | **+86 (+157)** | **+158 (+266)** |
| 6 tracks, SWEEP still, six tables: lines (misses) | +656 (+942) | +10 (+28) | +11 (+32) |
| 1 track, SWEEP still / moving, a table: lines | +111 / +110 | +6 / +68 | +6 / +69 |

- **Wavetable 0 copies nothing any more.** It still reads 5 lines a block in the RAM claim: the stock copy's
  pointer list, one line per track. What is left against the stock OS, +25 lines and +49 misses with six tracks
  moving, is the remap's own data in SDRAM:
  - the tags, the slots' addresses, the KB index, the masks, the last sources;
  - about 10 lines a remap, at 0,75 remaps a block per track.

  The stock function reads only its pointer table.
- **One table shared by six tracks got worse:** +158 lines instead of +86.
  - The cure keeps the stock frames' slots for Wavetable 0 even when no track plays it, so a table's new frame takes
    a slot another track's frame of the same table was in.
  - That frame is copied again when that track gets to it: 156 lines a block in the RAM claim instead of 85.
- **To weigh (not built):** keep the stock frames' slots only while a CHORD track is at Wavetable 0 (its latch 0).
  With every CHORD track on a table, the 30 slots are all theirs again.

### 24.4 The proofs with the cure (the maintainer, 2026-10-24)

`test_chordtables.py`: **ALL OK** in the three builds `[FAIT en émulation]`.
- P1m a to e identical, sample for sample, as before.
- P5 with frame 1 where the OS has it: no other pointer outside SRAM, `ct_fallback` 0.
- **Wavetable 0 alone copies nothing** (P1m a and c: 0 frames). The tables' scenario copies 453 frames over 120
  blocks (b, 490 before) and 318 with the move in block 40 (d, 350).

| Instructions per block per voice, SWEEP creeping | 0.1's way | §22.5 | with the cure |
|---|---|---|---|
| a table | 8 289 | 9 024 (+735) | 9 088 (+799) |
| Wavetable 0 | 8 312 | 8 692 (+380) | 8 646 (+334) |

SWEEP still, unchanged: +41 at Wavetable 0 and +38 with a table, against stock CHORD.

### 24.5 The stock frames' slots kept only while the stock table plays (2026-10-24)

The maintainer, after §24.3: keep the stock frames' slots only while a CHORD track is at Wavetable 0.

- **`stock_played()`:** a CHORD voice (`chord_voice()`) whose latch is 0 plays the stock table. An idle CHORD track
  at Wavetable 0 counts too, so the rule errs on the side of the stock frames.
- **`place()`:** a table's frame takes first a slot not holding its own stock frame only while `stock_played()`.
  Otherwise it takes the next free slot after the last taken, among all 30, as before §24. A stock frame's copy still
  goes back to its own slot when that is free.
- **The sound:** unchanged, whatever slot a frame takes (§19.3).
- **Outputs:** code 4 887 bytes, 5 488 bytes added to the image, `place` 526 bytes.
- **Checks:** all OK. `webcompose_check` gives MAIN OS `86fd59e4…`, `4462636f…` and `4c25070e…`.
- **To run:** the proofs and the probe. The probe's case "one table on all six, SWEEP moving" should come back
  towards §23.1's +86 lines, while P1m b keeps tracks 5 and 6 at Wavetable 0.

### 24.6 The runs of §24.5 (the maintainer, 2026-10-24)

- **The maintainer:** both runs ALL OK (`test_chordtables.py` and `probe_chord_lines.py`) `[FAIT en émulation]`.
- **`test_chordtables.py`'s output** (pasted whole), every check as in §24.4:
  - Wavetable 0 alone copies nothing (P1m a, c: 0 frames);
  - the tables' scenario copies 454 frames (b) and 318 (d), with tracks 5 and 6 at Wavetable 0, so the stock frames'
    slots are still kept there;
  - SWEEP creeping, instructions per block per voice: a table 9 131 (+842 against 0.1's way; +799 with §24's cure,
    the six-voice check of `stock_played()` at each copy), Wavetable 0 8 646 (+334, unchanged); SWEEP still +38 and
    +41 against stock CHORD, unchanged.
- **The probe** (pasted after), against the stock OS per block:

  | Case | 0.1's way | §23.1 | §24.3 (the cure) | §24.6 |
  |---|---|---|---|---|
  | 6 tracks, SWEEP moving, one shared table: lines (misses) | +624 (+891) | +86 (+157) | +158 (+266) | **+88 (+158)** |
  | 6 tracks, SWEEP moving, Wavetable 0: lines (misses) | +4 (+5) | +43 (+76) | +25 (+49) | **+25 (+49)** |
  | 6 tracks, SWEEP moving, six tables: lines (misses) | +627 (+910) | +310 (+468) | +311 (+471) | +312 (+469) |
  | 6 tracks, SWEEP still, six tables: lines (misses) | +656 (+942) | +10 (+28) | +11 (+32) | +11 (+32) |
  | 1 track, SWEEP moving, a table: lines | +110 | +68 | +69 | +70 |

  The shared table is back at §23.1's level, and Wavetable 0 keeps the cure's: neither case pays for the other now.

## 25. S4 prepared: 0.2 on the device (2026-10-24)

### 25.1 The builds

Built with `tools/compose.py` from the official file, into their own folder (git-ignored). 0.1's builds stay in
`build/` (`e4dafb31…`, `77a10a97…`) for a comparison.

| File | .syx SHA-256 | MAIN OS SHA-256 |
|---|---|---|
| `build/chordtables-0.2/model-cycles_OS1.13-chordtables.syx` (897 184 bytes) | `44d7695b…` | `86fd59e4…` |
| `build/chordtables-0.2/model-cycles_OS1.13-sampler+chordtables.syx` (941 088 bytes) | `9066396a…` | `4c25070e…` |

The MAIN OS hashes are those `webcompose_check` gave for `composer.js` (§24.5).

```sh
python3 tools/compose.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --machines chordtables --out build/chordtables-0.2/
python3 tools/compose.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --machines sampler,chordtables --out build/chordtables-0.2/
```

### 25.2 What the maintainer tests

Flashed as 0.1 was (§15.3, §17). The tables stay in `/Wavetables`.
1. **The lag** (§18), on the project or setup where 0.1 lagged:
   1. several CHORD tracks on tables, SWEEP still: the interface should react as on the official OS;
   2. the same with an LFO on SWEEP: less lag than 0.1; some may remain (§21.2, §24.6);
   3. every CHORD track at Wavetable 0 with an LFO on SWEEP: no slower than the official OS.
2. **The sound:**
   - tables as with 0.1, Wavetable 0 as the official OS (emulation: sample for sample);
   - SWEEP moving through a table without clicks.
3. **The start:** right after power-on, play CHORD at once. The move happens at the screen's first redraw and
   should not be heard.
4. **The loader:**
   - a table uploaded while the Cycles runs plays from the next note;
   - a table replaced while a track plays it, no glitch.
5. **With SAMPLE** (the second build): SAMPLE as before, next to CHORD tracks on tables.
6. **For comparison, if wanted:** 0.1's build (`build/model-cycles_OS1.13-chordtables.syx`) on the same project.
7. **Back on the official OS 1.13:** CHORD sounds play the stock table, as with 0.1.

Only the device shows the time of a line in SDRAM, so only the device says whether the lag is gone.

### 25.3 On the device (the maintainer, 2026-10-24)

- **The maintainer:** "besser, aber immer noch laggy. vor allem wenn man control all benutzt und chord mit custom
  wavetables auf allen spuren. habe beide builds ausprobiert". So 0.2 is better than 0.1; the interface still lags,
  most of all with Control All and CHORD on custom tables on every track; both builds of §25.1.
- **Not said:**
  - which knob was turned with Control All;
  - whether the six tracks shared one table;
  - whether an LFO moved SWEEP;
  - whether the same use lags on the official OS, or with every track at Wavetable 0.
- **Why Control All is the worst case for 0.2**, by the code:
  - TRACK held + SWEEP moves SWEEP on all six tracks at once, so every track reaches a new frame in the same
    blocks;
  - each new frame of a table is a copy, 65 lines of SDRAM and about 1 000 to 1 100 instructions (§22.5, §24.6), six
    of them in one block;
  - with six different tables nothing is shared. With one table and the same SWEEP on every track, one copy serves
    all six (rule 2).
  - Turning another knob with Control All changes no frame, and costs 0.2 nothing beyond 0.1.
  - The interface's own work grows with Control All too: six tracks' parameters per knob step.
- **Status:** 0.2 stays `experimental`.
- **The maintainer, asked:** "mit Wavetable 0 hakt es nicht, nur mit eigenen Tabellen". So the lag left is CHORD
  Tables' own, not the stock OS's load.
- **What in 0.2 costs more with a table than at Wavetable 0** (code and §24.6):
  - SWEEP still: nothing that counts. The same fast path, +6 SDRAM lines a block either way (the pointer list), the
    frames in SRAM.
  - A new frame: a copy for a table, none at Wavetable 0. Its frames sit in their own slots.

  So the lag left should come with frames that change: SWEEP turned with Control All, or an LFO on SWEEP.
- **The time of a copy on the device is not known.** 65 lines of DDR2 on 8 bits and about 1 000 instructions. With
  Control All, the six tracks cross a frame in the same blocks, so up to six copies fall into one block.
- **The maintainer, asked which knob:** "sweep und andere, problem überall". It lags with SWEEP and with other knobs
  turned through Control All, as long as the tracks play tables.
  - Another knob changes no frame, so the copies cannot be the whole cause. Nothing in 0.2's audio path that the
    emulation covers costs a table more than Wavetable 0 with SWEEP still (§24.6: the same lines, +38 against +41
    instructions).
  - The cause is outside what the probe and the proofs run: the interface task, the loader on the tick, or the audio
    path under the interface's edits (Control All, six tracks' parameters a step).
  - Next split, cheap: does it lag with the sequencer stopped, no note playing? Yes points at the interface's side
    (the tick, the loader), no at the audio's.
- **The maintainer:** "der lag läuft noch einige sekunden aus (display aktualisiert sich obwohl nicht mehr gedreht
  wird)". The screen keeps catching up for seconds after the knob stops.
  - That is the interface task working off a backlog of knob steps: it gets less time than the steps need. It does
    not say whether the time goes to the audio interrupt or to the interface's own work.
  - What runs on the interface's side is the same with tables and at Wavetable 0: the tick, the loader, the shortcut
    layer's knob hook. So the difference is most likely in the audio's load.
  - The audio costs a table more than Wavetable 0 only when its frames change (a copy each, none at Wavetable 0).
  - Something moving SWEEP all the time, an LFO on SWEEP or another modulation, would make the copies continuous on
    every such track, whichever knob is turned. That fits "problem überall", and only with tables.
  - Test: the same project with the CHORD tracks' LFOs off (or their depth 0). If the lag goes, the copies are the
    cause.
- **The maintainer:** an LFO on SWEEP "auf 2 kanälen, ja". So two tracks change frames all the time, and copy at
  every change.
  - **What a copy costs against 0.1's way** (§23.1, §24.6, by the counts): 65 SDRAM lines and about 1 000
    instructions per new frame, against 110 to 121 lines a block that 0.1 read for the same track. 0.2 reads fewer
    lines as long as a track needs fewer than about 1,5 new frames a block. The instructions come on top. A fast LFO
    at full depth crosses more frames than that (a full sweep of 32 frames in less than about 20 blocks, at 1 500
    blocks a second).
  - **The pool picks the next free slot after the last taken.** With two tables swept by LFOs, 64 frames compete for
    30 slots, so most frames are copied again at every pass. One track sweeping one table, 32 frames in 30 slots, would
    copy only a few frames a cycle.
  - **To know before building anything:**
    - does the lag go with those two LFOs off;
    - the LFOs' speed and depth;
    - whether the two tracks share a table.
  - **What could follow** (not built):
    - keep the frames near each track's position when a slot is taken, instead of the next one after the last
      taken;
    - read a frame where it is instead of copying it, for a track whose frames change faster than a copy pays
      for. That needs the render's frame comparison checked first (§19.1).
- **A measurement on the device** would tell instead of guessing: the load meter of notes/23 §5 (a probe around the
  audio function at `0x40059382`, the DMA timer `0xfc07000c`, "peak/mean" shown as the machines' names). It is part
  of `gen_syntakt_engines.py` today, not a part the composer can add.

## 26. Paused (2026-10-24): where CHORD Tables stands, and how to go on

The maintainer: "egal, lass den stand wie er ist. notiere noch infos falls wir daran weitermachen wollen." The work
stops here. This section is the way back in.

### 26.1 The state

- **The code:** CHORD Tables 0.2, committed in `5e58fa6` (the pool) and `45f0163` (Wavetable 0's cure and the
  refinement), status `experimental`.
- **The builds:** `build/chordtables-0.2/` (git-ignored; §25.1). Alone: `.syx` `44d7695b…`, MAIN OS `86fd59e4…`.
  With SAMPLE: `9066396a…`, `4c25070e…`. 0.1's builds are in `build/`, for comparison: `e4dafb31…` and `77a10a97…`.
- **Proven in emulation** (§24.4, §24.6):
  - Wavetable 0 identical to the stock OS, the tables to 0.1, sample for sample;
  - no slot in use ever written;
  - Wavetable 0 alone copies nothing.
- **On the device** (§25.3, the maintainer, both builds):
  - better than 0.1, still laggy with tables, most of all with Control All;
  - not at Wavetable 0;
  - every knob, and the screen catches up for seconds after the knob stops;
  - an LFO on SWEEP on two of the CHORD tracks.
- **Not asked or not answered:**
  - does the lag go with those two LFOs off;
  - the LFOs' speed and depth;
  - whether the two tracks share a table;
  - does it lag with the sequencer stopped.

### 26.2 What the lag most likely is

1. **Copies under the LFOs** (the leading guess, §25.3).
   - A track whose SWEEP moves needs new frames, and 0.2 copies each one into the pool: 65 SDRAM lines and about
     1 000 instructions.
   - Two tables swept at once are 64 frames for 30 slots. With the pick "the next free slot after the last taken",
     most frames are copied again at every pass.
   - The copies load the audio all the time, so the interface falls behind whichever knob turns.
2. **The time of a line on the device** (DDR2 on 8 bits) is not known. The emulator counts lines and instructions,
   not time. A copy may cost much more than its count says.
3. **Something the probe and the proofs do not run:** the interface task, the tick, Control All's edits. Nothing in
   the code reading says so: everything on the interface's side is the same at Wavetable 0, which does not lag.

### 26.3 How to go on

In this order, each step deciding whether the next is needed:
1. **On the device, two minutes:**
   - the same project with the two LFOs off: does the lag go?
   - the LFOs' speed, multiplier and depth;
   - the tables on those tracks;
   - the sequencer stopped.
2. **The same case in emulation:** a scenario with two tracks on different tables, SWEEP moved like an LFO (a
   triangle of the measured speed), the four others on tables with SWEEP still. In `test_chordtables.py` (the copies
   per block, and the sound still identical) and `probe_chord_lines.py` (lines and misses, against 0.1's way).
3. **A slot pick that keeps the frames near each track's position:**
   - when a frame is placed, store its table and frame number in the slot (`slot_buf`, `slot_frame`; the move sets
     them for the stock frames);
   - the pick then takes, among the free slots, the one whose frame is farthest from every track's frame on that
     table, a slot of a table no track plays first;
   - about 30 × 6 comparisons per copy, against copies that would mostly no longer happen for a swept table;
   - the sound stays the same whatever slot a frame takes (§19.3), so P1m and P5 prove it unchanged.
4. **Reading a fast frame where it is**, for a track whose frames change faster than a copy pays for (above about
   1,5 new frames a block):
   - first in emulation: does the render give the same samples when a frame keeps its content but changes its
     address between two blocks at the same index? That is case C of §19.1 in place of case D;
   - if not identical, a frame must keep its address while a voice points at it (as now), and this way is closed.
5. **A load meter on the device**, if the counts and the device still disagree: the probe of notes/23 §5 (around
   the audio function's call at `0x40059382`, the DMA timer at `0xfc07000c`, 90 112 ticks a block, "peak/mean" as
   the machines' names). It lives today in `gen_syntakt_engines.py` (`--meter`) and would become a part the composer
   adds, proven as `tools/emu/test_meter.py` proves it.
6. **Fewer distinct frames** (only for tables of fewer than 32 frames): keep a file's k frames and crossfade across
   them, instead of the 32 spread frames. Fewer frame changes per sweep. The sound would no longer be 0.1's sample
   for sample (rounding), so the proofs would compare against a computed table.

Unrelated and left as is: the loader's sum of the whole file index on every tick (§18), the same at Wavetable 0.

### 26.4 W7, paused

Three files stay uncommitted in the working tree since W7 was stopped (§17 onwards):
- `tools/gen_flasher_tweaks.py`: the CHORD Tables card (`cat` sound, `status` experimental, credit durchgemacht /
  `durchgemacht/model27`, `license` LICENSE-CHORD-Tables, `package` chordtables) and `OFFERED` with chordtables. Its
  comment still speaks of 0.1's device test.
- `tools/gen_chordtables.py`: copies the package's LICENSE next to the tweaks.
- `tweaks/model-cycles_OS1.13/LICENSE-CHORD-Tables`.

`docs/flasher/tweaks.js` is not regenerated, so `gen_flasher_tweaks.py --check` fails while the card is in
`OFFERED`. The checks of §20 to §24 were run with the card set aside (`git stash push -- tools/gen_flasher_tweaks.py`,
then `git stash pop`).

Still to do for W7:
- the card's texts in `app.js` (en, fr) and `GUIDE_OF`;
- the smoke test's lists;
- the guide section (en, fr);
- the release entry;
- the stamp;
- the README row;
- `ref_mainos.py`;
- the standard's draft 0.5 (extensions of a stock machine, `memory.sram`).

The card offers 0.2 once its lag is settled.

### 26.5 Commands

```sh
../.venv-emu/bin/python3 tools/emu/test_chordtables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
../.venv-emu/bin/python3 tools/emu/probe_chord_lines.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
python3 tools/gen_chordtables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --check
tools/webcompose_check.sh ../model-cycles_OS1/model-cycles_OS1.13.syx
python3 tools/compose.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --machines chordtables --out build/chordtables-0.2/
```

The two Unicorn runs are the maintainer's: Unicorn stops with SIGILL inside the agent's sandbox. They can run side
by side.

## 27. A new way (2026-11-05): one table per pattern, in the stock table's place (plan)

The maintainer, 2026-11-05, after an overview of §26: « warum tauschen wir nicht einfach die tabelle aus die auf dem
tisch liegt? wenn man die pro pattern tauschen könnte würde es ausreichen. es ist nicht nötig durch die wavetables per
lfo zu wechseln ». Nothing built: code and notes read, and a few trial builds in a scratch folder.

### 27.1 The idea, and what is decided

- **Why 0.2 still lags.** 0.2 keeps the frames the tracks play in a pool of 30 SRAM slots. It copies a frame in
  whenever SWEEP reaches one that is not there (§19). With an LFO on SWEEP, that is a copy in most blocks: the lag
  left on the device (§25.3, §26.2).
- **The new way:**
  - the pattern chooses one table, and the whole table takes the stock table's place in SRAM;
  - SWEEP, an LFO on it included, then reads SRAM as on the stock OS, with no copy while the pattern plays;
  - a copy happens only when the table changes: at a pattern change, or when the choice is edited.
- **Decided by the maintainer (2026-11-05):**
  1. every CHORD track of a pattern plays the pattern's table;
  2. the table is global: a CHORD track has no choice of its own any more, and the per-sound Wavetable 0 goes;
  3. a click at a pattern change is accepted at first; a clean change would be nicer. §27.3 shows that the clean
     way is needed anyway for a pattern's first note, and costs little more.
- **What this gives up:** two CHORD tracks cannot play two tables in one pattern.

### 27.2 Read in the code and the notes `[FAIT]`

- **Room in the pattern.**
  - A pattern's header is 64 bytes. The OS saves it whole (`0x4005ba0a`) but loads only bytes 0..28 and 38
    (`0x4005b3b4`). A new header's initializer (`0x40061526`) leaves 28..37 and 39..63 alone (notes/68 §13.2).
  - The effect slots keep bytes 29..31 (notes/68 §14). Chord Keys, which the flasher does not offer, keeps 32..35
    and 40..63 (notes/42).
  - **Free: 36, 37 and 39**, whatever comes back into the flasher. Proposed: 36 for the table (0..64), 37 for a check
    (`0x5a` + byte 36), like the effect slots' byte 31.
- **The loader and the initializer** each need a hook to keep the bytes. Today the effect slots take both:
  `0x4005b4b0` (`fx_load`) and `0x4006155e` (`fx_init`), in `tools/machines/fxslot/entries.S`.
- **The key.**
  - The key map of 2026-10-31 makes PATTERN the pattern's level and leaves "PATTERN + the other knobs" free
    (`_scratch/keymap/keymap-concept.md`, not committed).
  - In the stock OS, PATTERN + a knob disarms the pattern selection, then edits as without PATTERN (`claims.py`,
    the stock list).
  - The effect slots take PATTERN + Delay Time / Reverb Size at `0x4001f886`, in ParameterPageView's encoder
    handler (`fx_keys`). The track filter's `fl_keys` is chained in front of it there.
  - The effect slots also fix PATTERN's release (`fx_release` at `0x40020dca`, notes/68 §23). Any PATTERN + knob
    gesture needs that fix.
- **The knob at that hook** arrives as a descriptor (`d3`). For SWEEP the descriptor depends on the track's
  machine: the machine record's entry `knob − 2`, SWEEP being knob 6 (notes/63 §1.3).
- **The audio reads the playing pattern in every block**, as the effect slots do (`*0x40a7887c`, its number at
  +30706, its object at `*0x40fe4228` + 5192 + 732 n, the header at +60). Proven in emulation and on the device for
  the effect slots (notes/68 §14.5, §14.8).
- **What a copy costs** (§22.5, §24.6): about 1 000 to 1 150 instructions and 65 SDRAM lines a frame. All 30 frames
  in one block come to about 30 000 instructions, more than three CHORD voices (8 292 each, §15.4).
- **What stays as it is:** the stock frames' copy in the RAM claim (0.2's move, on the first tick), and the
  loader's 72 buffers of 33 pointers and 32 frames.
- **Trial builds of today's 0.2** (scratch, nothing in the repository):
  - alone, with SAMPLE, with `--cpu` and with Digital Delay: composed;
  - with Crush: refused by rule R1, because the machine value on MACHINES + SWEEP and the Track FX' values share
    k 28..31.

### 27.3 The design

**The audio side** (`cw_setup`, the same hook at `0x400ab15e`):
- **Each call** reads bytes 36 and 37 of the playing pattern (a few instructions, one or two lines).
  - The target is the table they name, if its file is loaded; otherwise the stock table.
  - A table the loader replaces is a new target: targets are compared by buffer, not by number.
- **The resident table** is the one whose frames sit in the 30 SRAM slots. At start, the stock table.
- **The steady state** (the target is resident):
  - the stock table: the stock function, bit for bit (as 0.2's Wavetable 0 before the move);
  - a file's table: the stock function's work on the resident list of 33 pointers. Positions 2–31 are in SRAM,
    positions 0 and 1 in the table's buffer in SDRAM.
  - The stock OS reads its frame 1 in SDRAM too (§19.1), so the lines come close to the stock OS's. No pool, no
    map, no copy.
- **A change** (the target is not resident), the clean way:
  1. From that call on, the voices read the target's own list, with its frames in SDRAM. That is 0.1's way, +110
     to 121 lines a track a block, for a few blocks. The new table plays from the first block, so from the
     pattern's first note.
  2. Each call then copies one frame into a slot no CHORD sub-voice points at (0.2's `pointed()`, kept).
     - With n CHORD tracks that is n frames a block, so 30 frames take 30/n blocks: one track 30 blocks (20 ms),
       six tracks 5 blocks (3 ms).
     - At most about +1 150 instructions a CHORD track a block.
  3. Once the slots hold the target, the resident list points into them and the target is resident.
     - A slot still pointed at keeps its position in SDRAM until it frees. A sub-voice switched off for its pitch
       keeps its +176/+180 (§19.1).
  4. A new target during a change restarts it. Back to the stock table: the same steps from the stock frames'
     copy, then the stock function.
- **What the render hears.**
  - At step 1 the frames change address and content at once. At step 3, the address alone.
  - The render has its own handling of a frame change (§19.1). Whether it covers a change at the same index is
    §26.3 step 4's question, `[HYP]`, settled by T2.
  - If step 3 does not click, this is the clean way.
  - At step 1 the timbre changes inside a note that sounds across the pattern change. That is the click the
    maintainer accepts.
- **Why not copy over the SRAM frames from the tick:**
  - the tick runs about 30 times a second, so the pattern's first notes would play the old table for up to about
    33 ms;
  - a voice could read a frame half copied;
  - one block of 30 copies is too dear (§27.2).

**The pattern side:**
- **The hooks.** `ct_load` at the loader's hook copies bytes 36 and 37 when the check holds; otherwise it writes 0
  and the check. `ct_init` at the initializer's hook writes 0 and the check. Every write masks the interrupts, as the
  effect slots' do.
- **The gesture.** PATTERN + SWEEP on a CHORD track:
  - steps byte 36 of the shown pattern (0..64, one detent a step) and writes the check;
  - calls the header's notify (as `fx_step`) and shows the number in the popup;
  - then the handler ends as it does after `fx_step`, without editing SWEEP.
  - How the popup can show a number that is no parameter is `[À FAIRE]`: the handler's popup is at
    `0x4001f708..0x4001f76e`; the track filter's display-only descriptor 5 is a model; which descriptor is free in a
    build with the Track FX is still to read.
- **PATTERN's release:** the package carries `fx_release`'s two instructions too, for a build without effects.
- **Shown and playing:** the gesture edits the shown pattern, the audio plays the playing one. The same as the
  effect slots, tested (notes/68 §14.8).

**The loader** stays as it is:
- files `/Wavetables/01`–`64`, k × 256 mono samples, spread over 32 frames;
- 72 buffers in the RAM claim, one file a tick.
- One addition: it waits to reuse a buffer while that buffer is the resident table or the source of a change.

### 27.4 What stays and what goes

| | 0.2 | the new way (0.3) |
|---|---|---|
| The choice | per sound, MACHINES + SWEEP, k 30, record slot 30 | per pattern, PATTERN + SWEEP, header bytes 36–37 |
| The shortcut layer | needed | not needed |
| With the Track FX | refused (R1, k 28–31) | possible: no k claimed |
| SWEEP moving, an LFO | a copy for most new frames | nothing beyond the stock OS |
| A change of table | at the next note, per track | at once, every CHORD track, copied over a few blocks |
| The audio code | pool, tags, pins, map, remap, reclaim | the stock function's work, and a change in a few states |

**What 0.3 keeps from 0.2:** the hook, the loader, the file format, the converter, the uploader's checks, the RAM
claim, the stock frames' copy, `memory.sram`.

**Sounds saved with 0.2** keep a value in k 30 and record slot 30 that 0.3 no longer reads. Only the maintainer's
projects have such sounds. In a build with the Track FX, that value becomes the Track FX' third value on those CHORD
sounds.

### 27.5 The builder

- **The claims.**
  - `saved` "pattern, header +36", 2 bytes.
  - The gesture PATTERN + SWEEP, with `replaces`: the stock disarm and edit.
  - `claims.py` compares saved places as strings (notes/68 §13.4, §14.6). It needs a range check first, so that
    "header +29" (3 bytes) and "header +36" (2 bytes) are compared as ranges.
- **The manifest's points.** None of these is a package point today; they belong to `fxslot`, a part:
  - the pattern header's bytes;
  - the loader's and the initializer's hooks;
  - the encoder handler's hook;
  - PATTERN's release.
- **Two holders at the same sites** (CHORD Tables and the effect slots), after the dispatchers' rule (notes/63 §4)
  and the track filter's chain at `0x4001f886`:
  - a site only one of them takes keeps that one's own entry, so every build that exists stays byte for byte;
  - where both are in a build, CHORD Tables' entry does its part and then runs the next one (the effect slots', or
    the replaced instructions);
  - `compose.py` and `composer.js` do the same, and `webcompose_check` stays identical for every existing build.

### 27.6 Proofs and done criteria

In `tools/emu/test_chordtables.py` (its loader part P2 kept) and `probe_chord_lines.py`:
- **P1 No pattern chooses a table:** every CHORD track plays as on the stock OS, sample for sample, and SRAM is never
  written.
- **P2 A pattern with a table, after the change:** CHORD plays as the stock function does on that table, sample for
  sample, with SWEEP still and moving. The reference is 0.1's way on the same table, as in P1m.
- **P3 The change:**
  - the new table is heard from the new pattern's first block, a note started in that block included;
  - no slot is written while a sub-voice points at it;
  - the number of blocks the change takes;
  - the jump in the output at steps 1 and 3, against the reference;
  - back to the stock table, the same;
  - a change during a change.
- **P4 The pattern,** as `test_fxslot.py` §5 does it (the template of `probe_chord_storage.py`):
  - load, save, init;
  - a whole pattern saved, loaded and copied;
  - an old pattern;
  - with and without the effect slots in the build.
- **P5 The gesture:**
  - PATTERN + SWEEP on a CHORD track writes the shown pattern's bytes and calls its notify;
  - on another track, and without PATTERN, everything as on the stock OS;
  - PATTERN + Delay Time / Reverb Size as before;
  - PATTERN's release.
- **P6 The cost:**
  - the steady state against stock CHORD (STANDARD.md §6), and the blocks of a change;
  - the probe: six CHORD tracks on one table, SWEEP still and moving, lines and misses against the stock OS.
- **On the device**, with the CPU page (`--cpu`, notes/78):
  - the load with six CHORD tracks on a table and LFOs on SWEEP, against the same pattern on the stock table;
  - the pattern change, by ear;
  - a project saved and loaded; a pattern copied and pasted.

### 27.7 Steps

Each step: a diff shown, a commit on the maintainer's word.
- **T1 Reading** `[À FAIRE]`:
  - the popup for the number;
  - a free descriptor next to the Track FX;
  - CHORD's SWEEP descriptor at `0x4001f886`;
  - the order, within a block, of the sequencer's pattern change and the voice loop.
- **T2 Emulation first:** the render's frame change at the same index (§26.3 step 4), in two cases: the same
  content at another address, and another table. It decides whether step 3 of §27.3 is silent.
- **T3 The builder:**
  - the claims' range check;
  - the package points of §27.5, and the chain with `fxslot`;
  - both composers;
  - every existing build byte for byte.
- **T4 CHORD Tables 0.3:** `chordtables.c` (§27.3), the manifest, `gen_chordtables.py`, `36-chordtables.json`.
- **T5 The proofs** of §27.6, run by the maintainer (Unicorn stops with SIGILL in the agent's sandbox).
- **T6 The device**, with a build that has the CPU page; then W7 (§26.4) with 0.3.

### 27.8 Decisions for the maintainer

1. **PATTERN + SWEEP on CHORD tracks only** (recommended):
   - elsewhere PATTERN + SWEEP stays stock;
   - the hook only needs CHORD's SWEEP descriptor.

   Or on every track.
2. **One detent per table**, 0 to 64 (recommended). The effects take four detents a step; here that would be 260.
3. **Own entries, chained with the effect slots' where both are in a build** (recommended): no build that exists
   changes, and the tested effect cards stay as they are. Or one shared pattern part for both, which changes every
   effect build and needs them tested again.
4. **SWEEP 0 stays the file's first frame** (the decision of 2026-10-24): positions 0 and 1 are read in SDRAM. Or
   position 0 becomes the OS's sine, as in the stock table, with one frame in SDRAM.
5. **The per-sound choice goes** (MACHINES + SWEEP, k 30) (recommended): it is what keeps CHORD Tables apart from the
   Track FX.

### 27.9 Status

- **Plan only.** 0.2 stays as committed (`45f0163`, `67091a1`), `experimental`.
- **0.2's device builds** in `build/chordtables-0.2/` still have RETRIG + SWEEP and the shortcut layer from before
  the key map.
- **A fresh build of 0.2** today composes with MACHINES + SWEEP (MAIN OS `8feec2e5…`).

### 27.10 Decided (2026-11-05)

The maintainer: « 2. verstehe ich nicht », « rest wie empfohlen », and on 4 the following.

- **1, 3 and 5 as recommended:**
  - PATTERN + SWEEP on CHORD tracks only;
  - own entries, chained with the effect slots' where both are in a build;
  - the per-sound choice goes.
- **2: two steps per table, on a knob's 0–127.** The maintainer: drop as many tables as needed so that two steps
  switch a table and the choice fills exactly 0–127.
  - 128 values at two steps a table are 64 choices: the stock table and **63 tables, files `01` to `63`**. One fewer
    than 64; `/Wavetables/64` is no longer read.
  - Byte 36 holds the value 0–127, as a knob does. PATTERN + SWEEP adds the handler's step and clamps at 0 and 127,
    and the table is the value ÷ 2. Two steps a table come out of the value itself, so no step counter is needed
    (the effect slots keep one for their four steps).
  - The popup shows the table, 0 (the stock table) to 63, the file's name.
  - To follow in T4 and W7: the loader's `TABLES` 64 → 63 (71 buffers), and the texts that say 01–64 (the
    uploader's checks, the converter's help, the guide).
- **4: the first frame is always a sine.** The maintainer: the first waveform must always be a sine, since the
  system uses it for something else too; the converter already sees to it; an internal check that puts a sine in
  when in doubt would be good.
  - The reason, from the CHORD Wave Bank (§16.1): the OS's sine at `0x8000eee4` is read by other code too. CHORD
    Tables never writes it, so that use is safe either way. The rule keeps SWEEP 0 a sine on every table.
  - **Position 0 is the OS's sine**, read where the OS has it, in SRAM. Position 1 is read in SDRAM, positions 2–31
    in the 30 slots. This is the stock table's own layout (§19.1), and it replaces the "positions 0 and 1 in SDRAM"
    of §27.3: one SDRAM frame, as on the stock OS.
  - **The loader checks a file's first frame** once, when it reads the file (UI task, not the audio):
    - a sine, as `tools/wavetable.py` writes it (`sine_frame`): the file's frames are spread as today, and position
      0 is the OS's sine in place of the file's;
    - anything else: the OS's sine goes in front of the file's k frames, and the k + 1 frames are spread over the 32
      positions. Nothing of the file is lost.
  - The test is `[À FAIRE]`: a comparison with a sine within a few steps, on the model of the uploader's
    `startsWithSine` and the converter's `starts_with_sine`. The OS sine's level and phase against the converter's
    are to read first.
  - **Cost:** none in the audio. Once per file in the tick, about 256 comparisons.
  - The uploader's warning about a table without a sine (§16.3) can become a note ("CHORD Tables puts a sine in
    front"): W7.

## 28. T1: read in the code (2026-11-08)

The maintainer, 2026-11-05: « Ja, T1 starten ». The five readings of §27.7's T1, done in the disassembly of MAIN OS
1.13 (`_scratch/control-all/main.dis`, not committed) and in its image. Nothing built.

### 28.1 CHORD's SWEEP, and the knob at the hook `[FAIT]`

- **The descriptor table `0x4010dce0`, read whole.** It has 76 entries of `0x38` bytes: group at `+0`, k at `+4`, CC
  at `+0x18`, long name at `+0x2c`, group name at `+0x30`, short name at `+0x34`. COLOR, SHAPE, SWEEP and CONTOUR have
  one entry per machine (46–49 for KICK up to 71–74 for CHORD), each machine's four followed by an Amp Decay.
- **CHORD's SWEEP is descriptor 73** ("Chord Sweep", group 5, k 13, default `0x2b00`), and no other machine's. The
  CHORD Wave Bank's TECHNICAL.md gives `0x49` too.
- **At `0x4001f886`:**
  - `d3` holds what the knob lookup returned (`0x4001f6ee`), and `d2` the event;
  - `0x4006f762(d2)` gives the knob number (SWEEP is 6).
- **So `d3` = 73 exactly when SWEEP turns on a CHORD track.**
  - With PATTERN held no MACHINES level applies, so the lookup returns the plain descriptor.
  - FUNC (fine adjust) changes only knobs 14 and 15, so FUNC + SWEEP still gives 73.
  - An added machine's descriptors are 76 + 5 i.
- **The gesture needs no lookup of the track's machine:** PATTERN held and `d3` = 73 is the whole test.

### 28.2 The popup `[FAIT]`

- **The handler sets up its popup before `0x4001f886`** (`0x4001f708..0x4001f76e`), for the descriptor the lookup
  returned:
  - `0x4001ddb2(view, d3)` runs when the (descriptor, track) pair changed;
  - then a timeout of 60 is written at `+568`, and a redraw is asked for.
- **The popup draws** the descriptor row's long name, and the value through the descriptor's interface object
  (`0x40a71754` + 100 d, formatter at `+0x20`; notes/47 §3.3, notes/73 §19.1).
- **So the lookup must return a descriptor of our own** when PATTERN + SWEEP turns on a CHORD track. That is the
  track filter's way for its type, descriptor 5:
  - `fl_knob` returns 5 on RETRIG + PITCH, and `fl_keys` steps on it at `0x4001f886`;
  - `show_type` writes the long name into both tables, the knob's steps at `+0x10`, `fl_fmt_type` at `+0x20`, and
    clears the picture at `+0x2c`.
- **The knob lookup is a vtable entry:** `0x401005a8`, stock `0x4001e814`. Today the shortcut layer takes it
  (`sc_knob`), with the track filter's `fl_knob` in front.
  - CHORD Tables' link: call the next lookup; if it returns 73 while PATTERN is held, return our descriptor instead.
  - That makes a fifth site to share (§27.5).
- **Not proposed:** pointing the popup elsewhere from the keys hook (`+560`, a second call of `0x4001ddb2`). Nothing
  has proven that way.

### 28.3 A free descriptor `[FAIT]`

- **Which entries are free.** The stock table's 0–5 and 10–13 are "Error" entries: group −1, k −1, range 0..0, their
  CC fields leftovers. Group −1 keeps them out of the tables the OS builds at boot, so no CC reaches them (notes/72
  §9). Of those:
  - 1–4 are the shortcut layer's and the Track FX' values, 5 is the Track FX' type;
  - 0 ends the handler (`0x4001f704`).
- **Free: 10, 11, 12 and 13.** No manifest, part or `claims.json` claims them.
- **Proposed: descriptor 10**, written as the track filter writes its 5:
  - group −1, k 0, no CC, the names "Wavetable" / "WAVE";
  - in the stock table, and in the one the OS uses (a copy, in a build with an added machine);
  - its formatter prints the table, 0–63.
  - The claim: `descriptors: [10]`.

### 28.4 The pattern change and the first note `[FAIT, by reading]`

- **The sequencer runs in an interrupt of its own.** Its handler `0x40054c1e` is installed as vector 121
  (`0x400001e4`, at `0x40055ec0`), apart from the audio interrupt (`0x40059382` → `0x4005979e`, voice loop
  `0x4005981e`).
- **That handler writes the playing pattern before it builds the step's events.** The writes are at `0x40054d56`
  (and `0x4005550a`, `0x40055700`; `0x40055c5c` in `0x40055c38`). The events are built at `0x400551a6` →
  `0x400548ce`, which reads the pattern at `0x40054828`.
- **A note starts in the audio block after its trig:** `v + 0x34` is copied to `v + 0x38` at the block's end
  (notes/14 §2, §11.6 above).
- **So in the block where a note of the new pattern starts, `*0x40a7887c` is already the new pattern.** `cw_setup`
  gives that note the new table from its first block.
- **Not read: the two interrupts' priorities.** If the sequencer can preempt a block, the CHORD voices of that one
  block may see the old and the new pattern. A note still starts only at a block's end. P3 proves this on the OS's
  own code.

### 28.5 The OS's sine `[FAIT]`

- **Where it comes from.** SRAM is filled at boot from the image (`0x4000045c`: `0x4019b590..` → `0x80000000`,
  `0x401a2a50..0x401aa140` → `0x80008000`). So the sine at `0x8000eee4` is the image's `0x401a9934`.
- **What it is:**
  - 257 Q31 words, the last equal to the first;
  - full scale: +2³¹ − 1 at index 64, −2³¹ at 192;
  - sine phase: 0 at index 0, then rising;
  - a fit gives amplitude 1,000000 of full scale and phase 0.
- **The converter writes the same wave.** `tools/wavetable.py`'s `sine_frame` is 32 767 · sin(2πm/256) in 16 bits:
  - against the OS's sine >> 16, rounded, at most 1 step apart (the OS reaches 32 768 at its peak, the converter
    32 767);
  - the loader turns a file's sample x into the word x << 16 (`build()`), which is at most 1,37 steps of 16 bits from
    the OS's word.
- **The loader's test** (§27.10):
  - a file's first 256 samples against the OS's sine >> 16, each within a few steps;
  - proposed: 4 steps, which covers the converter's 1 and the uploader's rounding of positive samples (§11.4);
  - 256 integer comparisons, once per file, in the tick.

### 28.6 What follows for the plan

- **T2 (emulation) is next.**
- **T3 gets one more site to share:** the knob lookup (`0x401005a8`), next to the loader's hook, the initializer's,
  the encoder handler's, and PATTERN's release.
- **The gesture:** `d3` = 73 while PATTERN is held, with no machine check. The popup comes from descriptor 10,
  returned by the lookup, and the claims add descriptor 10.
- **The pattern header:** bytes 36, 37 and 39 are still claimed by nothing (2026-11-08, after Transpose).

## 29. T2 prepared: the render at a change of frames (2026-11-08)

The maintainer: « Ja, T2 vorbereiten ». The question of §26.3 step 4 and §27.3: what CHORD's render does when its
frames change address, or content, at the same index between two blocks.

### 29.1 The probe

**`tools/emu/probe_chord_switch.py`** runs the official MAIN OS 1.13 with no package. Between two blocks it rewrites
the stock table's pointers (`0x40118590`), which is what a table change of §27.3 does to the setup: other frames at
the same SWEEP. CHORD plays alone on track 1 (the voice loop, `mcengine`), the note starts from block 1, the switch
comes before block 24.
- **A. The same frames at other addresses.** Copies in free memory from block 24, the stock addresses again from block
  44: steps 1 and 3 of §27.3 with the same content. Compared with the run without a switch, sample for sample, in
  four runs:
  - a1: SWEEP between two frames (a crossfade);
  - a2: SWEEP on a frame;
  - a3: SWEEP creeping;
  - a4: a high note (note 96).
- **B. Another table at the same index** (the stock frames in reverse). Compared with the stock table throughout and
  with the other table throughout:
  - which block hears the new table;
  - what the switch block plays: the old frames, the new ones, or a linear fade across the block;
  - the largest step at the switch, against the waves' own largest step.

  Three runs: b1 SWEEP between two frames, b2 SWEEP creeping, b3 the high note.
- **`--wav DIR`** writes two seconds of CHORD to listen to: four notes, each switching table in its middle (step 1 of
  §27.3, at once), and the same notes without a switch.
- **`--dry`** runs what needs no emulator: the stock table as the image holds it, the copies' place in memory, and
  the analysis on made-up runs.
- **What the probe checks, so that its results can be trusted (a FAIL otherwise):**
  - after the switch, every sub-voice's two frames come from the new pointers;
  - no access falls outside memory;
  - the copies stay unchanged;
  - the runs agree before the switch.
- **Everything else is a "finding":** a measurement for the design, not a pass or a fail.

### 29.2 What the answers decide

- **A identical:** step 3 of §27.3 (from the SDRAM frames to the same frames in SRAM) cannot be heard, and the clean
  change works as planned.
- **A not identical:**
  - a difference of a few steps, far under the note: it cannot be heard, so it is accepted and noted;
  - anything larger: step 3 needs another way, to design then.
- **B shows what step 1 does:**
  - the render fades by itself: a soft change;
  - the render switches at once: a click is likelier.
- **The ear decides from the listening files.** A click is accepted at first (§27.10).

### 29.3 Run here (2026-11-08)

- `py_compile` passes.
- **`--dry`: ALL OK.** The stock table holds entry 0 at frame 1 in the OS's data, 30 distinct frames in SRAM, and entry
  31 repeating entry 30. The 31 + 31 copies sit in mapped memory, apart from everything else. Case B differs from the
  stock table at every entry but the middle one. The analysis' self-test passes.
- **The emulation stops with SIGILL in the agent's sandbox** (exit 132), so the run is the maintainer's:

```sh
../.venv-emu/bin/python3 tools/emu/probe_chord_switch.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx --wav ../_scratch/chordtables-t2
```

### 29.4 The first run (the maintainer, 2026-11-08) `[FAIT en émulation]`

**ALL OK.** Every check of the probe's set-up holds. The findings:

| Case | Differs from the reference in | At most | Equal again from |
|---|---|---|---|
| a1 the same frames moved, SWEEP between two frames | blocks 24–26 and 44–46 | 155 434 920, −5,5 dB under the note's peak | block 27 (47) |
| a2 SWEEP on a frame | the same | 151 231 289, −6,3 dB | block 27 (47) |
| a3 SWEEP creeping | the same | 167 678 548, −5,6 dB | block 27 (47) |
| a4 note 96 | the same | 97 372 381, −0,7 dB | block 27 (47) |

| Case | The switch block, max \|difference\| to: old / new / fade (n + 1)/32 / fade n/32 | Equal to the other table from | Largest step at the switch, against the waves' own |
|---|---|---|---|
| b1 another table, SWEEP between two frames | 155 434 920 / 135 775 582 / 125 066 174 / 125 993 838 | block 27 | 9 036 920 against 40 021 051 (−12,9 dB) |
| b2 SWEEP creeping | 167 678 548 / 206 300 163 / 113 410 431 / 115 020 427 | block 27 | 14 185 094 against 54 537 625 (−11,7 dB) |
| b3 note 96 | 83 265 134 / 91 177 668 / 89 587 861 / 89 057 925 | block 27 | 44 432 247 against 92 661 206 (−6,4 dB) |

**What it shows:**
- **The render has a transition of its own.** When a sub-voice's frames change address at the same index, the render
  treats it as a jump of frame (§19.1, "another frame"). Its output then departs from the plain path for three
  blocks, the switch block and the two after it (about 2 ms), and runs on the new frames from the fourth.
- **Step 1 of §27.3 (another table) is smooth.**
  - In every case the switch's largest step stays under the waves' own largest step, by 6 to 13 dB. The switch
    makes no jump in the wave.
  - The switch block is closest to a linear fade, but not one: the render's transition has a shape of its own.
  - So the click the maintainer accepted (§27.10) may not come at all: the render fades. The listening file
    `chord-switch-at-once.wav` decides by ear.
- **Step 3 of §27.3 (the same frames, at other addresses) is not silent.**
  - The same transition runs although the content is the same, and changes the output by up to about half the
    note's level for those three blocks.
  - So it is not a crossfade between equal waves; the render's gains during the jump do not sum to the plain path's.
    Most likely a dip, `[HYP]`.
  - The clean change as §27.3 planned it would put this transition 3 to 20 ms after the first.

### 29.5 Step 3 without the transition: the previous pair moved too (prepared 2026-11-08)

- **The render decides by comparison.** It compares the new f0 with the previous one (`+176`) and the index with the
  previous index (`+188`, §19.1).
- **At step 3 only the addresses change**, so `cw_setup` can write the previous pair (`+176`, `+180`) at the new
  addresses too, wherever it points at the old copy of a frame. The render then sees no change of frame and takes
  its plain path, on frames of the same content.
- **The probe's new cases a5 to a7** test exactly this: a1, a3 and a4 again, with every sub-voice's previous pair
  moved before the switch block, and moved back before block 44. If each is identical to the run without a switch,
  sample for sample, step 3 is silent with this rule.
- **A third listening file:** `chord-same-frames-moved.wav`, step 3 without the rule, to hear how much the
  transition matters.
- **Here:** `--dry` ALL OK (the move maps each stock frame to its copy and back); the run is the maintainer's, the
  same command as in §29.3.

### 29.6 The second run (the maintainer, 2026-11-08) `[FAIT en émulation]`

**ALL OK.**
- **a1 to a4 and b1 to b3:** the same numbers as in §29.4.
- **a5, a6 and a7 (the previous pair moved too) are each identical to the run without a switch, sample for sample,
  through both switches (blocks 24 and 44):**
  - a5: SWEEP between two frames;
  - a6: SWEEP creeping;
  - a7: note 96, sub-voices switched off for their pitch included.
- **So step 3 of §27.3 is silent with this rule.** When the frames a sub-voice plays only move (the same content,
  other addresses), `cw_setup` writes the new addresses into `+168` / `+172` and into the previous pair `+176` /
  `+180` alike. The render then sees no change of frame. This joins the design of §27.3, steps 1 and 3:
  - **step 1** (another table) writes only `+168` / `+172`, and the render's own transition brings the new table
    in (§29.4);
  - **step 3** (the same table, from SDRAM to SRAM) writes the four pointers.
- **Step 3 needs the right moment.** It must come only once the render has left its transition from step 1, so that
  `+176` / `+180` already hold the new table's SDRAM frames. That is three blocks after step 1, and the copy into
  SRAM takes longer anyway (§27.3: 5 to 30 blocks). P3 proves the whole sequence in T5.
- **T2 is done in emulation.** Open: the maintainer's ear on `chord-switch-at-once.wav` (step 1, the render's
  transition) and `chord-same-frames-moved.wav` (step 3 without the rule, which the design avoids).

## 30. T3: the builder's design (2026-11-08)

The maintainer: « Ja, T3 starten », and asked whether `composer.js` should follow although the web flasher is gone:
« Beide wie bisher ». So `compose.py` and `composer.js` change together, and `webcompose_check` proves them.

### 30.1 What the builder does today at the five sites `[FAIT]`

Read in `tools/compose.py` (`fx_layer`, `fl_layer`, `compose`) and the parts' sources:

| Site | Who takes it today |
|---|---|
| Knob lookup, vtable entry `0x401005a8` | the shortcut layer's `sc_knob`, which calls the stock lookup `0x4001e814` (fixed in `shortcuts.S`); with filters, the filter slot's `fl_knob` in front of it (`knob_next` in its data block = `sc_knob`) |
| `0x4001f886`, the encoder handler's question for TRACK | the effect slots' `fx_keys`; with filters, `fl_keys` in front of it (`keys_next` = `fx_keys`, or 0) |
| `0x40020dca`, PATTERN's release | the effect slots' `fx_release` |
| `0x4005b4b0`, the pattern header's loader | the effect slots' `fx_load` |
| `0x4006155e`, a new header's initializer | the effect slots' `fx_init` |

- **The chains run front to back.** The part in front holds the address of the one behind it in its data block, and
  the composer drops the writes of the part behind at the shared site.
- **The part behind never changes.** So every build without the front part stays byte for byte.
- **The baseline:** `webcompose_check` on today's `main` (`0321e15`): every selection identical between the two
  composers, the fills 6/6. Its log, with each selection's MAIN OS hash, is kept for the comparison after T3
  (`_scratch/chordtables-t2/webcompose_base_2026-11-08.log`, not committed).

### 30.2 The design: a package's entry in front of the chain

- **A chain hook.** A hook or vtable entry in a package's `uses` may name `next`: a symbol the package reads as the
  entry behind it.
  - The composer writes the package's entry at the site, in front of whatever the build would put there: a part's
    entry, or nothing.
  - It resolves `next` to that entry's address, or to 0. At 0 the package does the replaced instructions itself,
    so its entry stands in for the stock code.
  - So no part changes, and a build without the package stays byte for byte.
- **Two placements.** The parts are laid out after the packages, so a package with chain hooks is placed twice:
  first to learn its size, then again after the parts, with the `next` values. Its size cannot change, so neither
  does the layout.
- **Two packages at one site** would each go in front of the one before, in the order given. Nothing needs this yet;
  the composer refuses it until something does.
- **CHORD Tables 0.3's five chain hooks:**
  - the knob lookup (vtable `0x401005a8`, `next`: `fl_knob`, `sc_knob` or the stock lookup);
  - `0x4001f886` (`next`: `fl_keys`, `fx_keys`, or 0);
  - PATTERN's release (`0x40020dca`, `next`: `fx_release`, or 0, when it does the same itself);
  - the loader (`0x4005b4b0`, `next`: `fx_load`, or 0);
  - the initializer (`0x4006155e`, `next`: `fx_init`, or 0).
- **One more patch point kind, `desc_used`:** the descriptor table the OS uses (the stock one, or the copy in a build
  with an added machine), for descriptor 10's row (§28.3). It is known before any placement.
- **Unchanged:** CHORD's call (`0x400ab15e`) and the screen's tick (`0x400075f0`, through the dispatcher next to
  SAMPLE) stay as in 0.2.
- **No longer used by CHORD Tables:** the shortcut and the shortcut layer. So rule R1 no longer stands between CHORD
  Tables and the Track FX.

### 30.3 The claims

- **Saved bytes as ranges.** `claims.py` compares saved places as strings (notes/68 §13.4, §14.6). With CHORD
  Tables' "pattern, header +36" (2 bytes) next to the effect slots' "+29" (3 bytes) and Chord Keys' "+32" (4) and
  "+40" (24), places of the same structure are compared as ranges of bytes. Every other place stays a string.
- **Descriptors.** model27's vocabulary is 1–4 today. It grows to the OS's other unused "Error" entries, 5 and 10–13
  (notes/72 §9, §28.3). The self-test's refused example moves from 5 to 6.
  - This is model27's builder, not the Mod Standard: its text (descriptors 1–4) is not changed, as `machine.stock`
    did not change it either.
- **The gesture:** PATTERN + SWEEP, with `replaces` (the stock disarm of the pattern selection, then the edit).
  CHORD Tables claims descriptor 10, and saved bytes "pattern, header +36", 2 bytes.

### 30.4 T3 alone proves only that nothing changes

- **No package uses a chain hook before CHORD Tables 0.3 (T4).** T3 alone can only show that every existing build
  stays as it was.
- **Proposed:** T3 and T4 as one step, the builder and CHORD Tables 0.3 together. T5 then proves them on the OS's
  code in the builds that matter: alone, with SAMPLE, with the effects, with the filters, with Transpose.
- **No reference package of its own.** REFC proved W2's extension of a stock machine, but a chain hook means
  something only at the sites a real gesture uses.
- **The order of the work:**
  1. the claims;
  2. `compose.py`;
  3. `chordtables.c`, its manifest, `gen_chordtables.py`;
  4. `composer.js`;
  5. the checks without emulation;
  6. T5's proofs, for the maintainer's terminal.

**Decided (the maintainer, 2026-11-08):** « T3 + T4 zusammen », no reference package of its own.

## 31. T3 and T4 built: the chain hooks and CHORD Tables 0.3 (2026-11-08)

Nothing committed. No emulation run yet: the proofs are T5's.

### 31.1 The claims (`tools/claims.py`)

- **Saved places meet as ranges** (`saved_meet`): two places of the same structure with a byte offset ("pattern,
  header +29", 3 bytes, against "pattern, header +36", 2 bytes) meet when their bytes overlap. Any other place meets
  only the same text. A clash between two places reads "saved bytes: A and B".
- **Descriptors:** 1–5 and 10–13 (§30.3).
- **The self-test** grows by four cases (descriptors 5 and 10–13; the same text; overlapping bytes; neighbouring bytes,
  another structure, no offset), and its refused descriptor is 6: all pass.
- **Four FAILs in the self-test are older than this work.** HEAD (`0321e15`) shows the same four: lfo-plus × the
  shortcut layer; SAMPLE × the track filter; SAMPLE's tweak × REF2's; `claim_conflicts` naming the tweak. They are
  not touched here. `claims.py --check` is ALL OK.

### 31.2 The builder (`tools/compose.py`, `docs/flasher/composer.js`, the same in both)

- **A chain hook:** a jsr hook or a vtable entry in a package's `uses` with `"chain": "<symbol>"`.
  - `load_manifest` checks its form.
  - `patch_values` gives the symbol the entry behind it: 0 at the first placement, the composer's value at the second.
- **`chain_sites`** collects them, one package a site. **`chain_next`** finds what the build puts at the site
  without the package: the target of a part's jsr there, or the method a part's vtable write holds. With nothing
  there it is the stock method for a vtable entry, 0 for a hook.
- **The order in `compose`:**
  1. the parts are laid out as before;
  2. their writes at the chained sites are dropped;
  3. the chaining package is placed again at the same addresses with the values. A changed size would stop the
     build; it cannot change.
  4. the chained sites leave the set of sites the parts take, so the package's own writes go there.
- **The package's placement** is one function now (`placement`), used by both placements, with `--compare-ld` as
  before.
- **The patch point kind `desc_used`:** the stock descriptor table, or the copy in a build with an added machine.
- **The shortcut layer** no longer refuses a package's knob lookup or hook at its sites when it is a chain hook.
- **A rule that was missing, found on the way:**
  - `computed_conflicts` had no rule for two payloads appended at the same place of the grown OS (`append.at`, the
    image's end, `0x401aa140` for 148 of the folder's tweaks).
  - Every composed build so far also shared bytes with each of those tweaks, so the gap never showed.
  - CHORD Tables 0.3 shares no bytes with Model-TG, and `check_overlaps.py` stopped on `model-tg+chordtables` and
    `model-tg-st+chordtables`.
  - Both composers now count a payload appended where the build's is as a conflict. `webcompose_synth.py` passes
    the folder's `append.at` along.
- **`webcompose_synth.py`:**
  - the chain symbols are placed with the patch points in part 1;
  - four new selections in part 2: `chordtables+crush`, `sampler+chordtables+digidelay+pots+crush`,
    `chordtables+transpose`, and the full offered set with CHORD Tables.

### 31.3 CHORD Tables 0.3 (`tools/machines/chordtables/`)

- **`chordtables.c` (rewritten):** the pool of 0.2 and its tags, pins and remap are gone.
  - `cw_setup`: before the move, and with the stock table at home, the stock function. Otherwise the stock
    function's work (`sel` of the stock selector) on `ct_list`.
  - Each call reads the playing pattern (`wanted`). A new table gets its list at once (`relist`, step 1).
  - `home_one` moves one position home: the frame copied into its slot once no sub-voice of any voice points at the
    slot (`pointed`), and at once every pointer to the buffer's frame moved to the slot (`move_pointers`, all four
    fields, step 3 of §29.6).
  - Slots: the stock table's own frames 2–31. Position 0 is the OS's sine, position 1 the table's in SDRAM.
  - `ct_tag[i]` says whose frame slot i holds, so a table that comes back finds its homes.
- **The pattern side:** `ct_hdr_load`, `ct_hdr_init` and `ct_step` write bytes 36 and 37 with the interrupts masked;
  `ct_step` calls the header's notify.
  - `ct_knob` gives descriptor 10 on PATTERN + SWEEP over descriptor 73, its rows in both tables written as §28.3
    says. `ct_fmt` prints the shown pattern's table.
- **The loader:**
  - 63 files, 71 buffers;
  - the sine test of §28.5 (`starts_with_sine`, 4 steps); without the sine, the OS's goes in front (`sample`);
  - `buf[0]` is the OS's sine.
  - `reclaim` frees a retired buffer once it is not the table wanted and no voice points into it, and clears the
    tags of its frames.
- **The move:** the stock frames 2–31 copied into `STOCK`, which gets the selector's pointers, every tag `STOCK`.
  A stock table not as expected leaves the stock table for good.
- **`entries.S` (new): `ct_keys`, `ct_release`, `ct_load`, `ct_init`.** An entry behind is reached through the stack
  (its address pushed, then `rts`), so no register changes. `ct_load` and `ct_init` keep `d0`–`d1`/`a0`–`a1`.
- **The manifest:** 0.3, the five chain hooks, the patch point `ct_desc_used`. The claims: saved "pattern, header
  +36" (2 bytes), descriptor 10, the RAM, the gesture PATTERN + SWEEP with `replaces`. No sound or record slot any
  more.
- **Built with `m68k-elf-gcc` 16.2.0** (`-Werror` clean). 4 156 bytes of code (0.2: 4 887), 872 bytes of variables.
  10 writes alone (0.2: 13), 4 156 bytes added to the image (0.2: 7 120). Only R_68K_32 relocations.

### 31.4 Measured here

- **The chains, read in the placed object of each build** (the immediates of `ct_keys`, `ct_release`, `ct_load`,
  `ct_init`, and `ct_knob`'s value):

| Build | knob lookup | `0x4001f886` | release | loader | initializer |
|---|---|---|---|---|---|
| chordtables | stock `0x4001e814` | 0 | 0 | 0 | 0 |
| chordtables + sampler (both orders) | `sc_knob` | 0 | 0 | 0 | 0 |
| chordtables + digidelay | stock | `fx_keys` | `fx_release` | `fx_load` | `fx_init` |
| chordtables + crush | `fl_knob` | `fl_keys` | 0 | 0 | 0 |
| chordtables + transpose | `sc_knob` | 0 | 0 | 0 | 0 |
| sampler, chordtables, digidelay, pots, crush, eq | `fl_knob` | `fl_keys` | `fx_release` | `fx_load` | `fx_init` |
| the full offered set with CHORD Tables, CPU, RESAMPLE, Transpose | `fl_knob` | `fl_keys` | `fx_release` | `fx_load` | `fx_init` |

  In every one, the vtable entry holds `ct_knob` and `0x4001f886` jumps to `ct_keys`. `fl_keys` still calls
  `fx_keys` behind it (its `keys_next`).
- **CHORD Tables now composes with the Track FX.** Rule R1 no longer applies: there is no machine value in k 28..31.
- **`webcompose_check` (part 1 and part 2): every selection identical between the two composers, 63 of them, the
  fills 6/6.**
  - Against the baseline of §30.1, the 55 selections without CHORD Tables are unchanged: writes, conflicts and MAIN
    OS.
  - The four with CHORD Tables changed (alone `0605e510…`, with Digital Delay `3bf4e7f0…`, with SAMPLE before
    `8ad2b4b2…` and after `159b2ab3…`). Four are new: with Crush `78c965dd…`, with Transpose `59ca3059…`, SAMPLE +
    Digital + POTS + Crush `88b064a6…`, the full set `c507555e…`.

### 31.5 Checks without emulation (2026-11-08)

- **All pass:**
  - `gen_chordtables.py --check`, `gen_parts.py --check`, `gen_flasher_tweaks.py --check`;
  - `check_overlaps.py` (CHORD Tables against Model-TG computed now, against lfo-plus no longer: they share no slot
    any more);
  - `registry.py --check` (REGISTRY.md regenerated: k 30 and record slot 30 freed, the header's bytes, the hooks);
  - `claims.py --check`;
  - `ref_mainos.py --check`;
  - `py_compile`.
- **The dry runs:**
  - `test_fxslot.py --dry`: ALL OK.
  - `test_fltslot.py --dry`: ALL OK. Its R1 example is REFC in both orders now, and a new case checks that
    `chordtables + refflt` composes.
  - `test_compose.py --dry`: no FAIL (no CHORD Tables in its selections).
- **`tools/emu/test_chordtables.py` still proves 0.2.** T5 rewrites it for 0.3 (§27.6), and `probe_chord_lines.py`
  measures 0.3.

## 32. T5 prepared: the proofs of 0.3 (2026-11-08)

The maintainer: « Ja, T5 vorbereiten ».

### 32.1 `tools/emu/test_chordtables.py`, rewritten

- **The reference for the sound is the stock OS itself.** Its pointer table `0x40118590` is rewritten in the same
  blocks to point at the table's frames, so a CHORD track plays the table as the stock function plays it.
  - The lists 0.3 gives its voices are the stock selector's own: the sine at 0, frame 1 in SDRAM, frames 2–31 in a
    buffer or a slot.
  - The render decides by comparing pointers. Every pointer 0.3 moves is moved in all four fields at once (§29.6).
  - So 0.3 must sound the same sample for sample, through every change and every copy.
- **Selections:** chordtables; sampler,chordtables; chordtables,digidelay; chordtables,crush. P1–P3 and C for the
  first two, the rest for all four; `--machines` runs everything for what it names.
- **0. The sites and the chains,** read in the built bytes: the six sites and each chain hook's entry behind, as
  measured in §31.4. Also the bootstrap and the boot hook, as before.
- **P1. The stock table**, on six CHORD tracks, the scenario of 0.2's P1m (notes, high notes that switch sub-voices
  off, SWEEP creeping, jumping, negative, fast, a track to TONE and back), 150 blocks.
  - The guises: the patterns unlinked, a pattern choosing an empty slot, one with a wrong check byte, one past 127,
    one at 0.
  - Expected: identical to the stock OS, the stock frames never written, nothing copied, the stock function called
    as often as on the stock OS.
- **P2. A pattern's table**, against the stock OS switched in the same blocks:
  - table 1; table 2 two blocks later (a change during a change); the stock table; table 2 again with frames of it
    still at home;
  - the playing pattern edited; an empty slot; a wrong check; the loader's new buffer for a table;
  - the patterns unlinked, then linked again; the stock table to the end.
  - Expected: the six tracks identical, sample for sample.
  - Then a table chosen before the move: the stock table until the move in block 30, then the table.
- **P3,** in the same run:
  - no slot written while a sub-voice points at it, nothing but the package writing them;
  - a finding: the blocks each change takes to come home;
  - at the end, every position home, each slot holding its stock frame again, the stock function called.
- **P4. The header:** test_fxslot.py's §5 for bytes 36 and 37 (the stock loader and initializer, the build's,
  `keep`, a whole pattern saved, loaded and copied, an old file, every write masked). With the effect slots behind
  the chain, their bytes 29–31 are checked too.
- **P5. The gesture:**
  - `ct_knob`, with the lookup behind it intercepted: descriptor 10 for PATTERN + SWEEP over 73, the lookup's answer
    otherwise; descriptor 10's rows in both tables, and its interface object;
  - `ct_keys`, as the handler calls it: the steps +1, +1, +1, −5, +200, +1, −300 give 1, 2, 3, 0, 127, 127, 0; the
    notify at each step; the shown pattern the one edited;
  - any other turn goes to the entry behind or to isKeyHeld(2);
  - `ct_fmt` prints 3, 0, 63, 10, and 0 for a wrong check;
  - PATTERN's release, by test_fxslot.py's own test.
- **L. The loader**, 0.2's harness:
  - the first tick's move;
  - the scan 01–63, with 64 never opened;
  - the sine in front of files 01, 02, 03, 63 and 11 (one sample 5 steps off), none in front of 08 (the converter's)
    or 10 (within 3 steps);
  - the tables exactly as computed;
  - added, replaced, deleted files; not mounted, locked; no free buffer;
  - a retired buffer kept while it is wanted, then while a voice points into it, then freed with its slot's tag
    cleared.
- **C. The cost** (STANDARD.md §6): 0.3 at the stock table and with a table at home, SWEEP still and creeping,
  against stock CHORD (a check: under +100 and +150 instructions a block a voice); the blocks of a change as a
  finding.
- **`--dry`:** the builds, the sites and the chains, without an emulator. Unicorn cannot even be created inside the
  agent's sandbox (SIGILL).

### 32.2 `tools/emu/probe_chord_lines.py`, for 0.3

- **The cases:** one CHORD track (note 60 and 84) and six, SWEEP still and moving. Each with the stock OS, 0.3 at the
  stock table, and 0.3 with a pattern's table at home.
- **What it reports:** lines of SDRAM, of them in the RAM claim, cache misses, SRAM lines.
- **A check:** at the stock table under 12 lines a block more than the stock OS, with a table at home under 20. 0.1
  added 110 lines a track, 0.2 up to 312.

### 32.3 Run here (2026-11-08)

- **`py_compile` passes.**
- **`--dry`: ALL OK** for the four selections: the sites and the chains as in §31.4.
- **A check of names, by hand** (an AST walk, since pyflakes cannot be installed here): every name defined, and
  every attribute taken from an imported module (`F.HDR_AT`, `t7.STOP`, `compose.gs.DESCN`…) exists.
- **The emulation is the maintainer's:**

```sh
../.venv-emu/bin/python3 tools/emu/test_chordtables.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
../.venv-emu/bin/python3 tools/emu/probe_chord_lines.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx
```

### 32.4 The first run (the maintainer, 2026-11-08) `[FAIT en émulation]`, as far as it went

- **CHORD Tables alone, every check ok up to L:**
  - the bootstrap and the boot hook; the sites and the chains;
  - P1: identical to the stock OS, nothing written into SRAM, 824 calls of the stock function as on the stock OS;
  - P2: identical to the stock OS switched in the same blocks, through every change, and with the move late;
  - P3: no slot written while pointed at, nothing else writing them, every slot back at the end;
  - P4; P5; PATTERN's release.
- **A finding of P3:** 9 changes brought home in 4 to 8 blocks with six CHORD tracks (the first, a change during a
  change, 8; then 4 to 6). 271 frames copied in all.
- **Then L stopped on the proof's own file, not the package:** the "sine within 3 steps" sample went past 32 767 at
  the sine's peak, and `struct.pack` refused it. Its samples are clipped now. The files' building was checked here,
  without the emulator: "within 3 steps" is taken as a sine, "one sample 5 off" gets the sine in front, the
  converter's file is within 1 step. The run again is the maintainer's.

### 32.5 The second run (the maintainer, 2026-11-08) `[FAIT en émulation]`

**ALL OK, for the four selections** (chordtables; sampler,chordtables; chordtables,digidelay; chordtables,crush).

- **0:** the bootstrap, the boot hook, the six sites, and the chains of §31.4 in every build.
- **P1 and P2–P3** (chordtables, sampler,chordtables):
  - every check of §32.4 again;
  - 824 calls of the stock function, as on the stock OS;
  - 9 changes home in 4 to 8 blocks (six CHORD tracks), 271 frames copied;
  - identical in both builds: SAMPLE before CHORD Tables moves its code, not its sound.
- **P4:** in every build.
  - With Digital Delay, the chain to `fx_load` / `fx_init` keeps the effect slots' bytes 29–31 as test_fxslot.py
    wants them, and bytes 36 and 37 as ours.
- **P5:** in every build.
  - The lookup behind `ct_knob`: the stock one; `sc_knob` (`0x4300a6bc`) next to SAMPLE; `fl_knob` (`0x4300281a`)
    with Crush.
  - Descriptor 10's rows in the copy (`0x43034000`) next to SAMPLE.
  - Any other turn goes to `fx_keys` with Digital Delay, to `fl_keys` with Crush, to isKeyHeld(2) alone.
  - PATTERN's release, in every build.
- **L:** in every build: the move, the scan 01–63, the sine put in front as §32.1 lists, every table exact,
  the reclaim.
- **C (STANDARD.md §6, instructions per block per voice, mean of 21 blocks):**

| Case | Mean | Max | Against stock CHORD |
|---|---|---|---|
| stock CHORD | 8 292 | 8 300 | — |
| 0.3 at the stock table | 8 343 | 8 351 | +51 |
| 0.3, a table at home | 8 325 | 8 333 | +33 |
| stock CHORD, SWEEP creeping | 8 283 | 8 300 | — |
| 0.3, a table at home, SWEEP creeping | 8 316 | 8 333 | +33 |

  - With a table at home, a moving SWEEP costs nothing more than a still one. 0.2 paid +842 for it (§24.6) and 0.1
    read 110 lines of SDRAM a track.
  - **A change with one CHORD track:**
    - the first block 10 107, then 9 719 to 9 759 a block for the copy of one frame, its free-slot check and the
      pointers' move;
    - about +1 400 against a table at home, about a sixth of a CHORD voice;
    - 30 blocks for the 30 positions (20 ms).
    - The measured window (19 blocks) is shorter than that, so the finding's "back at the table's own cost" reads
      None, as expected.
  - With six CHORD tracks, six frames a block in 5 blocks (P3).
- **Next:** `probe_chord_lines.py`, then a build for the device.

### 32.6 The lines, measured (the maintainer, 2026-11-08) `[FAIT en émulation]`

`probe_chord_lines.py`: **ALL OK.** SDRAM lines a block in the voice loop (mean of 22 blocks, minus the loop with no
note), cache misses with the voice loop alone:

| Case | stock OS | 0.3 at the stock table | 0.3, a table at home |
|---|---|---|---|
| 1 track, note 60, SWEEP still | 53 | 59 (+6) | 61 (+8) |
| 1 track, note 60, SWEEP moving | 54 | 60 (+6) | 61 (+7) |
| 1 track, note 84, still / moving | 53 / 54 | 59 / 60 | 61 / 61 |
| 6 tracks, SWEEP still | 277, 1 miss | 283, 6 misses | 285, 21 misses |
| 6 tracks, SWEEP moving | 295, 22 misses | 301, 29 misses | 302 (18 in the RAM claim), 23 misses |

- **A table at home costs what the stock table costs:** +7 or +8 lines a block, one track or six, SWEEP still or
  moving. The SRAM lines are the stock OS's exactly (180, 191, 722, 692).
- **For comparison, on six tracks:** 0.1 added 654 lines a block (§18.1: 277 → 931, 941 misses). 0.2 added from 6 (SWEEP
  still) to 312 (six tables with SWEEP moving, §24.6).
- **The +6 at the stock table** are `cw_setup`'s own reads (the playing pattern, its header, the state). The table
  adds 1 or 2 more (its list).
- **The 18 lines in the RAM claim, with six tracks moving,** are frame 1, which a track reads in the table's buffer
  while its SWEEP passes 0 and 1. The stock OS reads its own frame 1 in its data at the same moments, so the lines
  are the same, in another place.
- **A table at home counts more MACs with a load** (347 200 against 319 424). Its notes were already playing from the
  run that brought the table home, so block 0 renders too. The first block's count shows the same (292 instead of
  300).
- **The cause of 0.2's lag on the device** (copies of frames under the LFOs, §26.2) **is gone in the emulator:** with
  a table at home, nothing is copied while the pattern plays. Only the device can say whether the lag is gone.

**Committed `7906bdb`** (§28–§32 with the builder and 0.3; the maintainer: « Ja, committen »).

## 33. 0.3 on the device: prepared (2026-11-08)

The maintainer chose their full build with CHORD Tables (« Dein voller Build »), the case where 0.2 lagged.

### 33.1 The build

```sh
python3 tools/compose.py --cycles ../model-cycles_OS1/model-cycles_OS1.13.syx \
    --machines sampler,chordtables,digidelay,pots,smpfilter,crush,ring,reso,eq --cpu --resample --transpose \
    --with control-all-config,trig-preview,trig-cond-order --tool ../elektron-firmware-tool-main/elektron-firmware-tool \
    --out build/chordtables-0.3/
```

- **The result:** 160 writes, payload `0x43000000..0x43168d18` (below CHORD Tables' RAM claim and SAMPLE's pool),
  137 152 bytes added to the image. MAIN OS `0ec8759c…`.
- **elektron-firmware-tool:** checksums and HMAC ok, the same MAIN OS.
- **Copied as `build/chordtables-0.3/CHORD-Tables-0.3_full-build.syx`** (git-ignored), `.syx` `37e1f3d4…`.
- **The tables:** the four of the digiemu test (`_scratch/chordtables-digiemu/01.wav`–`04.wav`, made by
  `tools/wavetable.py`, each a sine first: three of 32 frames, one of a sine and an organ). On the +Drive in
  `/Wavetables` as `01` to `04`, or the files still there from 0.2's test.

### 33.2 The steps, one after the other

1. **The gesture and a table:**
   - a new project, CHORD on track 1, a note playing;
   - PATTERN held + SWEEP: the popup "Wavetable", the values 0, 1, 2…, two steps of the knob a table;
   - at 1 the table of `01` sounds, at 0 the stock CHORD.
2. **SWEEP through the table:** by hand, then an LFO on SWEEP. No click while it moves.
3. **The load, 0.2's case:**
   - CHORD on all six tracks, each with an LFO on SWEEP, the pattern on a table;
   - TRACK held + SWEEP and other knobs (Control All): does the interface stay quick?
   - the CPU page (SETTINGS → Device Config → CPU), against the same pattern at 0.
4. **Pattern changes while playing:** a pattern on table 1, one on table 2, one at 0. Listen for a click at the change
   (the render's own transition, §29.4).
5. **Saved and loaded:** the project saved, the Cycles off and on, the project loaded: each pattern's table kept.
6. **The rest of the build next to it:**
   - PATTERN + Delay Time still picks the delay's effect;
   - RETRIG + PITCH a Track FX on a CHORD track;
   - MACHINES + TRIG the keyboard;
   - SAMPLE as before.

### 33.3 Step 1 on the device, and a fix: the step is 8.8 (2026-11-08)

- **The maintainer**, with the four tables uploaded into `/Wavetables`: « kann ich pattern+sweep nutze, springt die
  wavertable auswahl von 0 direkt zu 63. keine änderung am sound. gleiches verhalten nach neuststart ».
- **Why** `[FAIT]`:
  - `ct_step` added the handler's step to the value as it came. That step is the interface object's (`0x4006f96a`),
    in 8.8 like the parameters' values: 0x100 a detent, more for a fast turn (notes/70 §2).
  - So one detent gave +256, clamped at 127: table 63.
  - There is no file `63`, so the stock table played: no change of sound.
  - After the restart the pattern still held 127, the same.
  - P5 had stepped by ±1, a step the handler never gives, so the emulation did not see it.
- **The fix:** `ct_step` adds the step / 256, and at least ±1 for a finer step (FUNC). Two detents a table, as
  decided (§27.10). 4 224 bytes of code (+68).
- **P5 now steps as the handler does:** a detent three times, −5 detents, a fast turn of 3, a fine step of 0x40, 64
  twice, a detent, −127. Expected 1, 2, 3, 0, 3, 4, 68, 127, 127, 0. `--dry` ALL OK here.
- **Checks:** `gen_chordtables.py`, `check_overlaps.py`, `registry.py` (regenerated), `claims.py`,
  `gen_flasher_tweaks.py` pass; `webcompose_check` 63/63 identical.
- **The new device build (0.3b), the same selection:** MAIN OS `0e1c33bc…`, `.syx` `59923758…`, the tool's check ok;
  `build/chordtables-0.3/CHORD-Tables-0.3b_full-build.syx`.
- **The proof with the fix** (the maintainer, 2026-11-08, `--machines chordtables`): **ALL OK** `[FAIT en émulation]`.
  P5 gives 1, 2, 3, 0, 3, 4, 68, 127, 127, 0 for the handler's steps, the shown pattern 5 → 7 for two detents. Every
  other part reads as in §32.5.

### 33.4 Step 1 again, with 0.3b (the maintainer, 2026-11-08)

- **The maintainer: « getestet, funktioniert ».** The build 0.3b, a new project, CHORD on track 1.
- **What works:**
  - PATTERN + SWEEP shows "Wavetable", one value every two detents;
  - the tables `01` to `04` sound at 1 to 4;
  - at 0, the stock CHORD.
- **Step 2 (the maintainer, 2026-11-08): « passt ».** Table 1 (saw to square): SWEEP turned by hand through the
  whole range and back, then an LFO on SWEEP at full depth. No click, no dropout.
- **Step 3, the load (the maintainer, 2026-11-08): « passt ».**
  - The case: CHORD on all six tracks, each with an LFO on SWEEP, the pattern on table 1; Control All turning SWEEP
    and other knobs.
  - **The interface stays quick: 0.2's lag (§25.3, §26) is gone on the device**, in the maintainer's full build.
  - Not said: the CPU page's values with table 1 and at 0.
- **Step 4, pattern changes while notes sound (the maintainer, 2026-11-08):** « bro, alter, das ist so geil.
  funktioniert!!!! ».
  - Patterns on table 1, table 2 and 0, changed while playing.
  - No click: the new table comes in through the render's own transition (§29.4).
- **Step 5, saved and loaded (the maintainer, 2026-11-08): « passt ».** The project saved, the Cycles off and on,
  the project loaded: each pattern kept its table (bytes 36 and 37 through the OS's save and `ct_load`).
- **Step 6, the rest of the build (the maintainer, 2026-11-08): « test 6 passt ».** The chain hooks leave everything
  behind them working:
  - PATTERN + DELAY TIME still picks the delay's effect;
  - RETRIG + PITCH a Track FX on a CHORD track, which acts on the chord with its table;
  - MACHINES + TRIG 15/16 moves the keyboard;
  - SAMPLE plays as before;
  - PATTERN released after PATTERN + SWEEP leaves no selection waiting.
- **The six steps of §33.2 all passed on the device**, with the build 0.3b.
- **The optional test 7, files on the +Drive (the maintainer, 2026-11-08): « passt alles. wechsel in punkt 4 ist
  instant ».**
  - A pattern at 5 with no file `05` played the stock table.
  - `05` (one saw wave, no sine in front) uploaded while it played: the table came in, a sine at SWEEP fully left,
    blending into the saw to the right (the sine put in front, §28.5).
  - A pattern at 4 with `04` deleted: back to the stock table at once.
  - The Uploader showed its warning about the missing sine, but in a place easy to miss. Warnings and errors as a
    popup are a later wish of the maintainer's for the Uploader, not this note's.
- **The optional test 8, back to the official OS 1.13 (the maintainer, 2026-11-08): « passt, funktioniert ».** The
  project of steps 4 and 5 (patterns on table 1, table 2 and 0) loads, and CHORD plays the stock table in every
  pattern. The official OS loads only its own fields of the header (§27.2), so bytes 36 and 37 change nothing there.
- **Every test of the sheet passed on the device**, steps 1 to 6 and the optional 7 and 8.

### 33.5 Tested on the Model:Cycles (2026-11-08)

- **CHORD Tables 0.3 is `tested`** (the manifest), with the build 0.3b of §33.3 (`b16309a`).
- **What passed, in the maintainer's full build:**
  - the gesture and the popup;
  - the tables, and SWEEP or an LFO through them;
  - six CHORD tracks with LFOs on SWEEP and Control All, without the lag of 0.2;
  - pattern changes without a click;
  - save and load;
  - the other mods at the shared sites;
  - files uploaded and deleted on the +Drive;
  - the official OS.
- **Not in the web flasher:** there is none online since 2026-11-07. The card of §26.4 (W7) waits for it, together
  with the test sheet for testers (`_scratch/beta-tests/chordtables-0.3.md`).
- **The test sheet** for testers, with these steps and two optional ones (files on the +Drive, back to the official
  OS): `_scratch/beta-tests/chordtables-0.3.md` (not committed; the maintainer's wish of 2026-11-08, for beta releases
  once the flasher is online again).

