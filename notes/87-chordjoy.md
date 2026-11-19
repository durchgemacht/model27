# 87 — Chord Joy: chords of a key on TRIG 1-8, their colour on TRIG 9-16, in CHORD+ (2026-11-19, English)

The maintainer's request (2026-11-19): Chord Keys (Tweak 45, Nico Heuser, notes/42) is "much too big" and does far
more than needed; they wanted a slim way to play chords on the CHORD machine, after a small hardware chord device:
seven buttons for the degrees of a key, a stick that changes the held chord's character. Everything here is model27's
own code; the idea of playing CHORD's chords from the TRIG keys comes from Chord Keys, none of its code. The working
title is Chord Joy. At the maintainer's wish (the same day) it is no card of its own: it went into CHORD Tables'
package, chordtables 0.5, and the card is now called **CHORD+** (CHORD Tables and Chord Joy).

Code `tools/machines/chordtables/chord_joy.c` (next to `chordtables.c`, one package, one object), built by
`tools/gen_chordtables.py` into `tweaks/model-cycles_OS1.13/36-chordtables.json`; proof
`tools/emu/test_chordjoy.py`.

Adresses : VA de l'OS 1.13.

## 1. In short

- **Switch:** MACHINES + PUNCH, per sound: bit 8 of k 32, the shortcut layer's switch, saved with the sound (the
  maintainer asked for "not remembered"; a switch of the layer lives in the sound, said to them). While MACHINES is
  held the PUNCH LED shows it. The maintainer would like the state on the screen as SAMPLE shows Loop / Reverse:
  [À FAIRE], the layer's switches have no name to show.
- **TRIG 1-7:** the degrees I ii iii IV V vi vii° of the major scale, **TRIG 8** I an octave up. TRIG 1 plays what it
  plays on the stock keyboard (the track's note, KBT, Transpose's octave): the key. Each press sets SHAPE to the
  degree's chord (major, minor, diminished: rows 4, 3, 19), then plays the root.
- **TRIG 9-16 with a degree held:** eight colours, in the device's "default" order: 9 up-left Aug (dreamy), 10 up Flip
  (major ↔ minor), 11 up-right Dom7 (bluesy), 12 left Dark, 13 right Jazzy, 14 down-left Sweet (6th), 15 down Open
  (sus4), 16 down-right Lush (9th). A press releases the root, sets SHAPE, plays the root again (the maintainer's
  choice: strike again). Released, SHAPE goes back to the degree's chord, no note, no lock. Without a degree held
  they are taken and do nothing.
- **Recording:** only with REC + PLAY, as the stock keyboard records a note, plus a SHAPE lock: SHAPE is set as a knob
  turned with recording on. New live steps replace old ones, as on the stock OS (the maintainer tried it on the
  machine, 2026-11-19).
- **Unchanged:** Chord Joy off (every sound saved before), other machines, FUNC / TRACK / PATTERN / MACHINES held, grid
  mode, the pattern selection: the stock keyboard (or Transpose) gets the event as it came.

## 2. The OS code it uses

| What | Address | Role |
|---|---|---|
| KeyboardView's key handler | slot `0x400ff9cc` (vtable +8), stock `0x4001a0d2` | TRIG n = code 15 + n; note = (code − 16) + 34 + KBT, play `0x40019f44`, release `0x40019d00(view, key)` [FAIT] |
| Event | +12 code, +16 flags | bit 1 press, `0x28` repeat / long press [FAIT] |
| Parameter object of a track | `{0x400fd134, project + 212 + 68 t}`, set `0x4000ba7a(obj, desc, value, t, rec)` | SHAPE = descriptor 72, value row << 8 [FAIT] |
| Recording path | `0x4000f4b8` → live rec? `0x4006ba76` → step `0x4000cfcc`, trigless `0x40017bb0`, lock `0x4001646a` | with rec set, a lock on the current step [FAIT] |
| Sound of a track | holder vtable +40 → sound; machine +38 (CHORD = 5), k 32 at +84 | the switch, bit 8 [FAIT] |
| CHORD's SHAPE rows | 3 to 37 (list `tools/emu/probe_chord_keys.py:50`) | 3 minor, 4 Major, 5 sus2, 6 sus4, 7 m7, 8 M7 (dom7), 10 Maj7, 12 dim7, 13 madd9, 14 Madd9, 15 m6, 16 M6, 19 mb5, 21 m7b5, 23 M#5, 27 m9no5 [FAIT] |

## 3. The design

`cj_keys` plays nothing itself. It hands the entry behind (`cj_next_keys`: Transpose's `tr_keys` when that part is in
the build, else the stock handler) a 32-byte copy of the event with the code of the degree's root key
(`16 + ROOT[degree − 1]`, ROOT = 0 2 4 5 7 9 11 12), after setting SHAPE. So velocity, retrig, live recording, the
release, KBT and Transpose's octave stay the stock keyboard's. The colour table, per quality (major, minor,
diminished), plain chord first:

```
major       4  23  3  8  3 10 16  6 14
minor       3  23  4  8 19  7 15  6 13
diminished 19  23  3  8 12 21  5  6 27
```

State in the package's variables (8 bytes): the held degree, the colour, the track, the sounding root, which presses
were taken (so that their release and repeats are taken too).

The guard (`joy_track()`): FUNC, TRACK, PATTERN and MACHINES not held, not grid mode nor the selection, a project,
track 0 to 5, its sound CHORD with bit 8 of k 32.

## 4. In the package

chordtables 0.5: the sources `chordtables.c`, `entries.S`, `chord_joy.c`; root `cj_keys`; uses `shortcut`
(MACHINES / PUNCH) and `keys.keyboard` (vtable `0x400ff9cc`, chain `cj_next_keys`); claims sound slot 32, record slot
18, the gestures MACHINES + PUNCH and TRIG 1-16 (scope machine:CHORD). Chord Joy's code: 1 455 bytes, 6 bytes of
variables, only R_68K_32 relocations. Two packages that extend the same stock machine cannot be composed (compose.py,
composer.js); that is why Chord Joy is in CHORD Tables' package rather than a card of its own (a first version as
package `chordjoy`, card 88, was dropped the same day). `tools/gen_flasher_tweaks.py` now also excludes two such
cards from each other, should one come.

## 5. Proof in emulation

`tools/emu/test_chordjoy.py`: (1) the builds, chordtables alone, with Transpose, with the effects and Track FX:
the slot holds `cj_keys`, the entry behind is `tr_keys` or the stock handler [FAIT]; (2) the keys through the slot,
the stock handler running behind, against the same build without the package: 576 events with Chord Joy off, on
another machine, with keys held, in grid mode or the selection give the same d0 and calls; TRIG 1-8 set SHAPE
(72, row << 8, track, rec 1) then the stock play of the root; TRIG 9-16 release, SHAPE, play; released, SHAPE back
with rec 0; alone, taken with nothing done. Run by the maintainer on 0.1 as package `chordjoy`: the first run had 8
failures, all in the proof (the release's two arguments compared as four; the Transpose builds compared with the
stock OS instead of the build without it); after the fix "all ok" (2026-11-19) [FAIT en émulation]. In CHORD+
(chordtables 0.5) the maintainer ran both proofs again the same day: `test_chordjoy.py` "all ok",
`test_chordtables.py` ALL OK, no failure [FAIT en émulation]. With the fix of §7 the maintainer ran `test_chordjoy.py`
again: "all ok" (2026-11-19) [FAIT en émulation].

MAIN OS: chordtables 0.5 alone `6fc17ea5…`, with every card of the page (release 0.76) `10ca0b0b…` (with the fix of §7) (BUILD.md).

## 6. Left to check

- [FAIT] On the machine (§8): the build with the fix of §7, "gerätetest ok"; which points the maintainer tried, not
  said one by one.
- [À FAIRE] The switch's state on the screen, like SAMPLE's Loop / Reverse.

## 7. First test on the machine (19/11/2026) and the fix

The maintainer flashed the full build of release 0.76 (MAIN OS `b96ab75a…`): "grundsätzlich funktioniert es und es
macht spaß", but some chords sound broken, a degree held and TRIG 9-16 pressed, and TRIG 1-8 alone too, most of all
TRIG 6-8: first the held chord, then a jump to the new one. Their answers: also with the keys played one after the
other, not overlapped; one change, not a run through chords; SHAPE turned by hand between quarter-note trigs plays
the trig's chord cleanly.

- **The cause** `[FAIT, read in the OS 1.13]`: `0x4000ba7a` writes the word into the sound and notifies its
  observers; `0x4000e2ec` hands it to `0x40059534(value, track, k)`, which writes the voice's target
  `0x800015ae + 66 t + 2 k` at once. But the audio side smooths every target each block (`0x40058474`: a one-pole,
  0x03d7 / 0x7c29, state long `0x800011e8 + 4 j`, j = 7 + 33 t + k, the word in its high half), and CHORD reads the
  smoothed word. The OS snaps the state to the targets only when a note brings another sound (`0x40058a0a` →
  `0x400582d0`); a live note on the track's own sound keeps the glide, so the note starts on the old chord and
  slides to the new one within a few blocks: heard as one jump, worst where the rows lie far apart (degree 7's
  diminished is row 19, its neighbours 3 and 4). A knob turned long before a trig has settled; a lock is put by the
  sequencer at the trig.
- **SHAPE is k 12** (descriptor 72 in the table `0x4010dce0`, 56 bytes an entry, k at +4).
- **The fix** `[FAIT en émulation, FAIT sur la machine §8]`: every SHAPE set by Chord Joy also writes the state long of
  (t, k 12) to the new word << 16, before the note's event, as `0x400582d0` does. One aligned long, written from
  the UI task, which the audio interrupt never splits.
- **A second fault, found reading the code:** a degree pressed while another is held released the new degree's
  root instead of the one sounding, so the old note went on with the new chord. `S.sounding` now keeps the degree
  whose root sounds.
- **The proof** checks both: the state long after every degree and direction, and three overlapped pairs (6 → 7,
  7 → 8, 1 → 6): the sounding root released, the new one played, the first key's release taken without a call.

## 8. Tested on the machine (19/11/2026)

The maintainer flashed the full build of release 0.76 with the fix of §7 (MAIN OS `10ca0b0b…`, from the command line)
and ran `test_chordjoy.py` in Unicorn: "all ok. gerätetest ok". The card CHORD+ is tested again (no tag in the
flasher); BUILD.md, the guide, the release entry and the manifest (`tests.hardware` 0.5) say so.
