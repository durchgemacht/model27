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

