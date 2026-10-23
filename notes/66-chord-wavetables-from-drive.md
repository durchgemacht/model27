# 66 — CHORD plays wavetables from the +Drive, chosen with RETRIG + a knob (plan)

**Status: plan, 2026-10-23; the maintainer's decisions the same day: the six recommendations of §8 (§10). W1
prepared the same day (§11): three facts read in the code and one measured; the probe of the trig block,
`tools/emu/probe_chord_tables.py`, run by the maintainer: the sites and the event loop ok, the voice loop corrected
(§11.6: a note starts in the block with `v + 0x38` set, k 30 comes from the sound object); the second run ALL OK
(§11.7). W1 done. Nothing built.**

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
