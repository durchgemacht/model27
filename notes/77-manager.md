# 77 — The Manager: one project per firmware on the Model:Cycles

The maintainer's request (2026-11-02): changing firmware means making a new project on the Model:Cycles each time,
then flashing; a page should make that simpler and tie projects to firmware builds, for every Model:Cycles owner and
any build, without hosting firmware. Built first as a page of its own (a local repository, not published), tried on
the maintainer's Model:Cycles, then moved into the site as `docs/manager/` (the maintainer's decision: "ganz in
model27", not tied to the flasher, "Manager" in the navigation after Flasher). Release 0.30. No firmware is touched:
the page only sends what the user adds and what the Cycles sent. Addresses: load addresses of the Model:Cycles OS
1.13's main section (base `0x40000400`).

## In short

- **A firmware keeps its project.** The user adds `.syx` files; each is a firmware with its backups (one current),
  its slot and name on the Cycles. **Switch** runs five steps: stop the sequencer, back up the project the Cycles plays
  as the current one of the firmware it runs, flash the other firmware, bring that one's project back (checked), save
  it in its slot. The user's part: stop the sequencer, press YES, save in the slot; about a minute in all.
- **Backup without a key on the Cycles**: request `6F` returns the whole project, byte for byte what CONFIG > BACKUP
  sends (§2).
- **The end of a restore is known and checked**: a settings request (`64`) sent right after a backup is answered once
  the Cycles is through, with the settings just sent (§3).
- **Which firmware runs cannot be read** from the device: a model27 build answers as the official OS does (§5); the
  page keeps track of what it flashed and asks once.
- **A backup holds no name and no slot** (§6): after a restore the Cycles keeps those of the project loaded before,
  and its quick save would overwrite that project. The fifth step says where to save and which name to type.
- Tried on the maintainer's Model:Cycles (2026-11-02, §8): both ways between a model27 build and the official OS
  1.13, each with its own project, also after a power cycle; stopping a flash; USB pulled during a restore; export
  and import.

## 1. Decisions (2026-11-02)

- For every Model:Cycles owner, any `.syx` for the Model:Cycles (official OS, model27, Modded-Cycles, One-Shot, own
  builds). No firmware is hosted; the official OS is named by its SHA-256 (`KNOWN` in `app.js`, the hash of
  `tweaks/model-cycles_OS1.13/device.json`, checked by `tools/manager/flash.test.js`).
- Version 0.1 backs up, flashes and switches. The library lives in the browser (IndexedDB), with export to one ZIP
  and import from it. A firmware remembers its project: a current backup and the older ones as its history.
- English, Chrome, Edge or Opera on a computer (Web MIDI with SysEx). The page's look is the flasher's 1-bit one,
  from a clickable mockup the maintainer approved (2026-11-02).
- The classic path (the raw `.syx` to CONFIG > UPGRADE over a MIDI cable) is left out: the page flashes over USB
  only; recovery stays with the guide.

## 2. A project backup, and request `6F`

**Format** (OS 1.13, checked on every message of the maintainer's backups): 96 messages
`F0 00 20 3C 11 00 50 01 01 <pattern 0–95> <data> <checksum> <length> F7` of 25 762 bytes, then one
`… 54 01 01 00 …` (the settings, 601 bytes). The checksum is the sum of the data bytes (from byte 10) modulo 2¹⁴, the
length the message's length minus 10 modulo 2¹⁴, both as two 7-bit bytes. Data is packed 7 bits per byte as in the
Transfer protocol. Each pattern holds its kit: 70 sound records (`BEEFBACE`, version 2) from decoded offset 14 880;
model27's extras in the sound records (SAMPLE's sample, the Track FX's mark) come back with a restore. Two backups
of the same project are byte for byte the same; about 7 s and 2.4 MB over USB.

**How the OS routes a dump.** A table at `0x401490e0` holds, for message types `0x50`–`0x5F`, the wrapper
`0x40080472` (receiving data), and at `0x40149120`, for `0x60`–`0x6F`, the wrapper `0x40080480`. Both drop the six
header bytes and the F7 (`data += 6`, `len -= 7`) and jump on: the second to `Midi::handleSysexDumpRequest` at
`0x40083602` (named by its lambda's type info at `0x40112bb0`, whose `std::function` manager is `0x40082d1a`). Its
parser (`0x4005e862`, on the message from its type byte on) wants more than 7 bytes, bytes 1 and 2 equal to `01`,
byte 3 an index (`0x00`–`0x7F`), and the checksum (the sum of the bytes from 4 up to the checksum, modulo 2¹⁴); the
length is not checked; a global at `0x40fe4228` must not be 0 (not looked into). It then posts a task "Receive
sysex", which runs `0x40084344`: type minus `0x60` picks a case.

| Request | Answer | Handler | Index |
|---|---|---|---|
| `60` | `50`, one pattern | `0x40083e22` | the pattern, 0–95 |
| `61` | `51` | `0x40083f98` | yes |
| `62` | `52` | `0x40084094` | yes |
| `63` | `53` | `0x40084234` | yes |
| `64` | `54`, the settings | `0x4008419a` | no |
| `68` | `58` | `0x40083ef2` | no |
| `69` | `59` | `0x40084010` | no |
| `6A` | `5A` | `0x4008410c` | no |
| `6B` | `5B` | `0x400842bc` | yes |
| `6F` | the whole project: `50` for patterns 0 to 95, then `54` | `0x40084204` | no |

`65`–`67` and `6C`–`6E` do nothing; what `51`–`53` and `58`–`5B` hold is not looked into. `6F` sends the patterns one
by one through the same routine as `60` and stops at the first that fails; only then the settings. The answer goes
back through the interface the request came in on (`0x40082658` maps it), so over USB to the page. The request:

```
F0 00 20 3C 11 00 6F 01 01 00 00 00 00 05 F7
```

On the Cycles (2026-11-02): the answer to `6F` is byte for byte a backup from CONFIG > BACKUP. `backup.js` checks a
backup whole (96 patterns in order, then the settings, every checksum and length) before keeping it.

## 3. A restore, and when it is through

The Cycles takes a backup back at any time, also sent without pauses, and replaces its active project; it shows
"Received Settings" and goes to the pattern the backup was made on. It sends nothing back, asks nothing and does not
restart. A settings request (`64`) sent right after the last message is answered once the Cycles is through, with
the settings just sent: on the Cycles, 97 messages left the page in 0.4 s and the answer came 11.89 s after the last
one, the same as sent. The page waits for that answer (60 s at most) and compares it: the restore is in and right.
Since the page hands everything over at once and the Cycles says nothing until it is through, the restore's progress
bar follows the time, at about 200 KB a second (`RESTORE_BPS`, from the 11 to 13 s measured for 2.4 MB), and stays
below 100 % until the answer (§8).

While the sequencer plays, a restore stutters and hangs the sound (the maintainer, 2026-11-02): stopping it is the
switch's first step. Elektron Transfer talks to the Cycles while it is open (`00 20 3C 10 00` messages the page did
not ask for), and so does the page open in a second tab: the page shows a warning while such messages come.

## 4. The library

In IndexedDB (`store.js`, stores `builds`, `backups`, `files`, `meta`, each record under `key`), under the page's
origin: the site's library is not the one of a copy opened from another address; an export moves it.

- **Firmware**: `{ key: SHA-256 of the .syx, name, added, bytes, current: backup key | null, notes, slot, slotName }`.
- **Backup**: `{ key: firmware + "/" + SHA-256 of its messages, build, name, made, bytes, messages }`; the same backup
  twice is kept once (the page says which one it equals).
- **Device**: `{ build, sure }`, set by a flash from the page or by the user.
- **Export**: a ZIP without compression (`zip.js`): `library.json` (format `pfm-library`, version 1), `builds/<id>.syx`,
  `backups/<id>.syx`; unzipped, every `.syx` works with any SysEx tool. The page asks the browser to keep its data
  (`navigator.storage.persist()`) and says when it may clear it.

## 5. What the Cycles reports

Identify asks as Elektron Transfer and the flasher do (`xferIdentify`): a ping (`0x01`, device id 27 for the
Model:Cycles, then a name) and the OS version (`0x02`). A model27 build answers `Device id 27 (Model:Cycles), name
"Model Cycles", version "1.13"` (2026-11-02), as the official OS does: builds cannot be told apart on the device.

## 6. The switch, and the slot

Flashing is the flasher's fast path (`upgradeFast` of `docs/flasher/flasher.js`, OS upgrade by 2 KB blocks, notes/37):
the Cycles asks for YES (the maintainer pressed it in every test), writes and restarts; its USB port goes about 15 to
26 s after the last block and comes back 0.3 s later. Stop sending leaves the Cycles in its upgrade screen; turned
off and on, it starts with its old firmware and project (2026-11-02).

A backup holds neither the project's name nor its slot: in all eight backups of the maintainer's library the settings
message is the same byte for byte, and no message holds a project name. After a restore the Cycles keeps the name and
slot of the project loaded before: its project list marks no project or the old one, and its quick save wrote the
restored project into the slot of the other firmware's project (2026-11-02). A restored project survives a power
cycle. Saving it from the project list into the firmware's own slot (Save, “Overwrite?” Yes) asks for a name and
suggests the one held from before; renamed, that slot is marked and named right (2026-11-02). So the switch's fifth step
names the slot and the name to type, from the firmware's `slot` and `slotName` (asked the first time, or in the setup).

## 7. The page

`docs/manager/`: `index.html` (the site's header and footer), `style.css` (the flasher's 1-bit tokens, header,
buttons and footer, and the page's own classes; class names `site.css` also styles are overridden there), `app.js`
(the UI: the Cycles' card, the firmwares as tiles with Switch and a menu, the switch as a dialog with its steps and a
protocol under Details, the history as a drawer, a four-step setup on the first start), and four scripts without page
code: `sysex.js` (split, join, the dump and request messages, SHA-256), `backup.js`, `store.js`, `zip.js`. It loads
`../flasher/flasher.js` for the `.syx` checks and the flashing, and nothing else of the flasher. A button that a
redraw replaces between press and release never gets its click: the dialog keeps its buttons until they change
(found on the Cycles: Stop sending did not respond, 2026-11-02).

## 8. Tests

- **Host**: `tools/webmanager_check.sh` runs `tools/manager/*.test.js` (backup checks on made-up and broken backups,
  the library on a memory backend, export and import, the ZIP against the system's `zip` and `unzip`, the flashing
  core with a stand-in session). `BACKUP_SYX=` and `OS_SYX=` add a real backup and the official OS.
- **Browser**: `tools/manager/fake-cycles.js`, a stand-in Model:Cycles loaded by hand: every flow with real clicks
  (setup, switch both ways, a firmware without a project, Stop sending, "I answered NO", the history, a Cycles that
  does not answer, settings that differ, Transfer's traffic, import; 375 px wide).
- **On the maintainer's Model:Cycles (2026-11-02)**, with the page before it moved:
  - D1: backup and restore from the page.
  - D2/S3: model27 build → official 1.13: backup 2.4 MB in 7.8 s; flash 869 KB, 435 blocks in 24.5 s; YES; gone
    14.6 s and back 14.9 s after the last block; restore checked after 10.8 s. Back: 970 KB in 27.3 s, restore
    checked after 12.6 s. Each project comes back on its firmware, also after a power cycle; saved in slot 03 "M27",
    the slot is marked and the sample plays.
  - D4: an export imported into an empty library: 2 firmwares, 9 backups, the current ones and the firmware on the
    Cycles as before.
  - D5: Stop sending after 119 of 435 blocks (above); USB pulled during a restore: the page says so at once, connects
    again by itself, and the project sent again is checked after 12.8 s.
  - U1, the redone page: model27 build → official, checked, saved in slot 04.
- **On the site's page** (`docs/manager/` served on localhost, 2026-11-02): a switch on the Cycles, "passt". One
  finding: in step 4 the bar stood at 100 % at once and stayed there until the project was in, since it counted the
  messages handed over (0.4 s). It now follows the time (§3); against the stand-in with a real 2.4 MB backup and 12 s
  to take it in, it rose from 3 % to 92 % until the answer after 12.4 s. Still to check: the page on GitHub Pages
  after the push.

## 9. Later

- An empty project to start a new firmware with, instead of making one on the Cycles (a factory backup could not be
  shared).
- Model:Samples, and the Model:Samples on the Cycles OS.
- Showing what a backup holds: the sounds' names, the machines per track, the active pattern.
- The dark theme, with the flasher's.
