# Changelog

model27's releases, newest first, as the [flasher](https://durchgemacht.github.io/model27/flasher/) shows them.
The releases from 1.56 down are [Modded-Cycles](https://github.com/18nelli18/Modded-Cycles)' own; model27 starts
from its release 1.55.

This file is written by `tools/gen_changelog.py` from `docs/assets/release.js`.

## 0.75 (2026-11-18)

- A new machine, VOSIM, plays two vocal formants that start again on every period of the note, from soft vowels to buzzing tones. COLOR and SHAPE set the two formants, SWEEP lets them follow the note, CONTOUR makes them fade within each period.
- Every machine card can now be ticked together: SAMPLE, SOLID, CHIPS, MAXSAW, TERRA and VOSIM with CHORD Tables and all the other cards.
- Based on the VOSIM model of Mutable Instruments' Braids, carried over to the Model:Cycles. Goes with every other card. Checked in an emulator on the OS's own code, and tried on a Model:Cycles from the command line in a build with every other card (2026-11-18). Experimental until it is flashed from this page.

## 0.74 (2026-11-18)

- Back to the official firmware on a Model:Samples with mods is no longer marked Experimental: it was tried on a real Model:Samples by a tester the maintainer knows (2026-11-18), and the machine started as a Model:Samples again. The second way back, for a Cycles OS put on by hand, is not tried on a machine yet.

## 0.73 (2026-11-18)

- Installing over USB: if the machine stops answering during the send, the page now waits a moment and sends the firmware once more by itself. Some machines got stuck at 0 or 1 % on the first try, with every flasher, and always worked on the second. Nothing is written before you confirm on the machine's screen, so a send that stops halfway leaves nothing behind.
- Checked with a simulated machine (2026-11-18); not yet seen on a machine that gets stuck.

## 0.72 (2026-11-17)

- A new machine, TERRA, plays wave terrain synthesis: a point circles over a surface, and the height under it is the sound. COLOR chooses one of eight surfaces, fading from one into the next, SHAPE the size of the circle, from almost a sine wave to a rich sound, SWEEP moves it sideways over the surface, and CONTOUR mixes in a second sound, a sine wave that the surface bends.
- Surfaces 1 to 5 are smooth, 6 to 8 are made of Plaits' wavetables and sound brighter. A new trig on a track that still sounds doesn't cut it.
- Based on the wave terrain model of Mutable Instruments' Plaits, written anew for the Model:Cycles, with its wavetables. Goes with every other card. Checked in an emulator on the OS's own code, and tested on a Model:Cycles (2026-11-17): from the command line, then flashed from this page with every other card.

## 0.71 (2026-11-17)

- Back to the official firmware on a Model:Samples now also works when its Model:Cycles OS was put on by hand or by an older tool. If the machine refuses the usual way back, nothing is written, and the page sends the other way back by itself.
- Mods put on a Model:Samples by Modded-Cycles, Supermodel or PPPCCC already go back the usual way. Checked in an emulator on the Model:Samples' own code and with a simulated machine (2026-11-17), not yet on a real Model:Samples.

## 0.70 (2026-11-17)

- A Model:Samples can get the mods again from the main flasher page. After Install, step 1 asks which device you own; for a Model:Samples, it also asks whether you already installed mods on it. One sentence says what will happen, the rest is folded under Good to know.
- Back to the official firmware works on a Model:Samples too: answer Yes, and it gets its own OS back. In step 2, a green light in the drop zone shows a file the page took; only problems are written out. The list of what you install is now in step 4, next to the one box to tick, without the line that repeated it. The tabs and the separate flasher/?samples page are gone, and so is the Samples OS for a Model:Cycles.
- The firmware files are the same as before, byte for byte. Checked in a browser on a computer and at phone width (2026-11-17)

## 0.69 (2026-11-16)

- A new machine, MAXSAW, plays a huge, wide sawtooth sound: seven sawtooths detuned around the note. COLOR spreads them, SHAPE mixes the middle one with the six others, SWEEP takes away low end below the note, and CONTOUR sets how they start at each trig, from a random point each to all at once for a hard attack.
- Press and hold MACHINES and press PUNCH for a soft sub two octaves down, which adds low end without a buzz. A step can lock it.
- Based on Adam Szabo's analysis of the supersaw, written anew for the Model:Cycles; the flasher's receipt and credits now name him, linked to his thesis. Goes with every other card. Checked in an emulator on the OS's own code, and tested on a Model:Cycles (2026-11-16): from the command line, then flashed from this page with every other card.

## 0.68 (2026-11-16)

- A new machine, CHIPS, plays chiptune: a square wave that runs through a chord as a fast arpeggio inside each note. SHAPE chooses the chord (OCT plays the note alone), CONTOUR how fast the arpeggio runs, from 1/4 to 1/32 with the tempo or 16 to 64 notes a second, COLOR the shape of the square wave and SWEEP a pitch sweep at every trig.
- Press and hold MACHINES and press PUNCH for a stepped triangle bass an octave below, or GATE for an arpeggio up and down. A step can lock either. The screen names the chords (OCT, 5, SUS, m …) and the speeds (1/16, 1/16T, 35HZ …) instead of numbers.
- Based on the chiptune model of Mutable Instruments' Plaits, written anew for the Model:Cycles. Goes with every other card. Checked in an emulator on the OS's own code, and tested on a Model:Cycles (2026-11-16): from the command line, then flashed from this page with all other cards.

## 0.67 (2026-11-15)

- The flasher, the uploader and the Wavetables page look quieter. Lines are thinner and say what they are: a frame, a control, a divider. What explains (a card's sentence, hints, sizes, credits) is in a softer tone than names and titles. The ink is a dark blue-grey instead of black, the typeface is IBM Plex Mono, and a card's shadow is a fine checkerboard.
- Buttons have slightly rounded corners and normal writing, and nothing jumps under the pointer. Fields and checkboxes sit on a lighter ground, so you see where to type or tick. On the Wavetables page, Undo, Sort by brightness, Preview and the other underlined words are now framed buttons, dashed while they cannot be used, as on the uploader. The uploader's two lists name their columns.
- The firmware and what the pages do are unchanged. Checked in a browser on a computer and at phone width (2026-11-15)

## 0.66 (2026-11-15)

- SAMPLE (Cycles One-Shot 0.18): a sample you play from the PRESET menu ends when you let go. With GATE on, a note played on the pad or a TRIG key while the cursor rests on a sample now sounds for as long as you hold the pad or the key, then fades with DECAY. Before, it played the whole sample, however short the press.
- The sequencer is unchanged: the track's trigs keep playing while you hold the pad or a key, and letting go cuts none of them.
- Checked on the host, in an emulator on the OS's own code and in digiemu with every card (2026-11-15), then flashed from this page onto a Model:Cycles the same day: with GATE on and a short DECAY, the pad and a TRIG key tapped stay short, held they sound until you let go.

## 0.65 (2026-11-14)

- The flasher page has a new footer: links to the site's pages and to the project, and a receipt that names the people whose work model27 is built on, from the reverse-engineering of the firmware to the sound of MACRO and ACID. model27 takes no money: every name on the receipt links to that person's GitHub.
- The credits below it are now called Credits & licenses, otherwise unchanged. The firmware is unchanged.
- Checked in a browser on a computer and at phone width (2026-11-14)

## 0.64 (2026-11-14)

- SOLID and SAMPLE have their own pictures. On the MACHINES page, SOLID shows its own card and a ball behind a pillar instead of Perc's, SAMPLE its own card and a waveform instead of Tone's. The main screen and the preset dialogs show them too. The sound is unchanged.
- Checked in an emulator on the OS's own code and in digiemu with every card (2026-11-14): the MACHINES page, the main screen and the SAVE PRESET and RENAME PRESET windows. Then on a Model:Cycles from the command line with every card the same day: the MACHINES page.

## 0.63 (2026-11-14)

- New card, Perform Kit: press and hold SETTINGS and press PATTERN, and a pattern change no longer changes the sound. Only the sequence changes: the next pattern's trigs and locks play on the sounds you have right now. A checkered stripe at the left edge of the screen shows that the mode is on.
- Nothing is kept unless you save the pattern (FUNC + SETTINGS held): switching the mode off, Save Project and switching the Model:Cycles off leave every pattern with the sound it had before the mode. Which delay and reverb a pattern uses and its CHORD wavetable still change with the pattern.
- Checked in an emulator on the OS's own code, then on a Model:Cycles from the command line, alone and with every card, then flashed from this page (2026-11-14)

## 0.62 (2026-11-13)

- SAMPLE (Cycles One-Shot 0.17): the previewed sample follows the knobs. While a sample is marked in the PRESET menu, the copy of the track's sound that the pad and the TRIG keys play takes the knobs' values as you turn them (Start, Length, the filter, DECAY, Loop and Reverse too); before, it kept the values from the moment the sample was marked, so a knob turned with the menu open did nothing for the next note.
- Checked on the host and in an emulator on the OS's own code, then on a Model:Cycles from the command line with every card (2026-11-13): a note after SHAPE turned is short, after SWEEP turned filtered, the held pad's trigs follow the knob at once. Then flashed from this page with every card the same day.

## 0.61 (2026-11-11)

- SAMPLE (Cycles One-Shot 0.16): while the cursor in the PRESET menu rests on a sample, the track's pad plays it, as it plays a preset there, and outside GRID RECORDING mode the TRIG keys too. It plays with the track's settings, as on the Model:Samples, and the sequencer keeps playing the track's own sample, also while a TRIG key is held; its next trig cuts the key's note.
- Hold the pad, and the track's trigs play that sample too, with their notes and parameter locks; steps with their own sample keep it. Let go, and a trig that plays it goes back to the track's sample at once, at the same place, as on the Model:Samples; the pad's own note plays out.
- A sample loads while the cursor rests on it and goes again when the cursor moves on or the menu closes. Until it has loaded it stays silent, a long one for a moment.
- Checked in an emulator on the OS's own code, in digiemu and on a Model:Cycles from the command line with every card (2026-11-12): a long stereo sample silent for a moment, then played; the pad, the TRIG keys, the held pad's trigs, the let-go, a locked step, the browser closed with the pad held; the CPU page as before. Then flashed from this page with every card the same day.

## 0.60 (2026-11-11)

- The Track FX settings on COLOR and SHAPE respond to MIDI CC 75 and 76 (NRPN 1:22 and 1:23), as the ones on SWEEP and CONTOUR do to CC 74 and 71: Ring's Wave, Reso's Tone and Decay, EQ's Low Gain and High Gain. With MOUT on in TRACK SETUP, turning them sends those CCs.
- Checked in an emulator on the OS's own code: CC 75 and 76 reach those settings on all six tracks and with every machine, and nothing else changes. Builds with only Samples or Crush stay as they were. Tested on a Model:Cycles (2026-11-11) from the command line, with Reso and EQ: the CCs and NRPNs in, on a track's channel and on the AUTO channel, and the CCs out. Then flashed from this page with every card, the same day.

## 0.59 (2026-11-11)

- A new machine, SOLID, plays struck sounds: a string, a drum skin, a marimba bar, a metal bar, a bell or glass, and everything in between. SHAPE chooses the body, CONTOUR what strikes it (a mallet, a burst of noise or noise that goes on), COLOR how bright it rings and SWEEP where you hear it. DECAY sets how long it rings, and GATE damps it when the note ends.
- The popup shows each knob's name on two lines, Solid over Bright, Body, Pickup and Exciter. Six SOLID tracks in a busy pattern, each with a Track FX, and POTS on the delay take about 60 % on the CPU Page, with peaks up to 75 %.
- Goes with every other card. Checked in an emulator on the OS's own code, and tested on a Model:Cycles (2026-11-11): from the command line with all other cards, then flashed from this page.

## 0.58 (2026-11-10)

- When the Cycles will not delete a sample, the Uploader's window says why and lists the steps: once a track uses a sample, the Cycles locks it, and a restart unlocks it only if no track uses it anymore.
- Deleting goes on past a locked sample: the others are deleted, and the window names every sample the Cycles kept. More than three fold into a list that opens with Show, in the windows for uploads too.
- Corrects 0.57, which said a restart unlocks a sample: on a Model:Cycles with one SAMPLE track, a sample that a track still used stayed locked after a restart.

## 0.57 (2026-11-10)

- The Uploader takes AIFF files. Chrome, Edge and Opera cannot open them, so the Uploader reads them itself and hands the browser the same sound as a WAV; a WAV of 64-bit floats goes the same way. A file saved as AIFF with a .wav name works too.
- When a file is not uploaded, the Uploader says why and what to do: compressed (and how), empty, too long, possibly damaged, or moved or changed after you added it. Before, each of them said that the browser cannot read the audio file. A WAV or AIFF too long for SAMPLE is turned away before it is converted.
- When the Cycles will not delete a sample, the Uploader says what to do: a sample loaded on a track stays in use until the Cycles restarts, even after the track gets another one. Load another sample on every track that uses it, save the pattern, restart the Cycles, then delete it again.
- Checked on files made by macOS in every kind of AIFF it writes: in Chromium the same samples arrive as from a WAV of the same sound. On a Model:Cycles an AIFF named .wav arrived and played in SAMPLE, and a sample that was in use could be deleted after the steps above.

## 0.56 (2026-11-09)

- The Wavetables page saves your wavetable as a file for CHORD Tables: press Save…, choose the wavetable's number under CHORD Tables, then press Save .wav. Put the file on the +Drive with the Uploader, in the folder Wavetables. With CHORD Tables on your Model:Cycles, a new wavetable needs no new firmware.
- The file holds a sine and your 31 waves, at 48 kHz and 16 bits, its name starting with the number, such as 07 my-wavetable.wav. Checked on the files: the Uploader writes it as it is, without a warning, and CHORD Tables plays your waves as the page made them, at 16 bits. Not yet tried on a Model:Cycles.

## 0.55 (2026-11-09)

- A new page, Wavetables, gives CHORD a wavetable of your own: drag waves of Plaits and Braids, or your own WAV files, onto its 31 frames, hear them with SWEEP and an LFO, and save the wavetable into your firmware. SWEEP then moves through your waves instead of CHORD's.
- It goes into the official OS 1.13 or into a build from this site, which keeps all its cards: download the build's .syx in the flasher's last step and drop it on the page. Your OS file and your waves stay in your browser. It is the editor of CHORD Wave Bank, in the site's look.
- Tested on a Model:Cycles (2026-11-08): a build with every card but CHORD Tables, with a wavetable from this editor in it, installed and played. Checked on the files: into the official OS and into a build with all fifteen cards, nothing changes but the wavetable. With CHORD Tables, 0 plays your wavetable; not yet tried on a Model:Cycles.
- CHORD Tables is tested as this page builds it: flashed from here onto a Model:Cycles (2026-11-09), after the tests from the command line. Its card no longer says Experimental.

## 0.54 (2026-11-09)

- CHORD Tables reads wavetables with names: start the name with the wavetable's number, 01 to 63, and add what you like. 07 Glass Pad is wavetable 7, and 07 alone still is. Of two files with the same number, the one whose name comes first alphabetically plays. A renamed file is read within about two seconds.
- The Uploader warns, in Wavetables, when a name does not start with 01 to 63 and when a number is already taken, saying which file plays. The files are uploaded all the same.
- Checked in an emulator on the OS's own code: the names, two files with one number, renaming, adding, replacing and deleting files, 63 files at once. Tested on a Model:Cycles (2026-11-09), from the command line with all fourteen other cards: a name after the number, a name without one, two files with one number and a delete, and six CHORD tracks under load; then flashed from this page.

## 0.53 (2026-11-09)

- The Uploader shows a warning or a problem in a window over the page, which stays until you press OK. After an upload it names each file that was skipped, not uploaded or uploaded with a warning, and why. The line under the title still says what happened last.
- A wavetable in Wavetables whose first waveform is not a sine still uploads, and its warning now says what CHORD Tables does with it: it puts a sine in front, which SWEEP plays at the far left. Checked against a stand-in Model:Cycles in the browser.

## 0.52 (2026-11-08)

- A new card, CHORD Tables: CHORD plays your own wavetables from the +Drive, one for each pattern. Put them on the +Drive with the Uploader, in a folder Wavetables, named 01 to 63. Hold PATTERN on a CHORD track and turn SWEEP to choose the pattern's wavetable: 0 is CHORD's own, 1 to 63 the files, two steps of the knob each. Every CHORD track in the pattern plays it, and SWEEP moves through its waveforms as through CHORD's own.
- The wavetable is saved with the pattern and comes in at once when the pattern changes, also on notes that still sound, without a click. It plays from the same fast memory as CHORD's own, so six CHORD tracks with LFOs on SWEEP cost about what they cost with CHORD's own sound. A wavetable uploaded or deleted while the Model:Cycles runs is read within about two seconds.
- Checked in an emulator on the OS's own code: every CHORD track sample for sample like the stock OS switched to the same wavetable, and like the stock OS at 0. Tested on a Model:Cycles (2026-11-08), from the command line with all fourteen other cards; not yet flashed from this page.

## 0.51 (2026-11-06)

- A new card, Transpose: hold MACHINES and press TRIG 15 or 16 to move the notes of the TRIG keys an octave down or up, two at most. TRIG 8, 9, 11 and 12 make the active track jump 7 or 5 semitones down, or 5 or 7 up, at once, also while the pattern plays. Press the key again to go back. A new pattern brings everything back; a temporary reload or a reload from the project (FUNC + PATTERN) brings the pitch back and keeps the octave.
- With MACHINES held, the six keys light up dim, half or full to show the octave and the jump. With this card, MACHINES opens the MACHINES menu when you let go of it, unless you used one of these keys.
- Checked in an emulator on the OS's own code: every other key as on the stock OS, the jumps sample for sample like turning PITCH on every stock machine, the lights in the panel's own interrupt. Tested on a Model:Cycles (2026-11-06), from the command line with SAMPLE and with all fourteen cards: the keys, the octaves, the jumps on a running pattern, the lights at every LED setting, MACHINES, GRID RECORDING, and both ways of reloading the pattern; then flashed from this page.

## 0.50 (2026-11-06)

- SAMPLE locks Loop and Reverse on single steps: hold one or more TRIG keys and MACHINES, then press PUNCH or GATE. Those steps play it the other way round from the track, saved with the pattern; press it again and they follow the track again.
- While you hold a TRIG key on a SAMPLE track, the right half of the screen shows that step's LOOP and REV, lit when it plays them, and with MACHINES held the PUNCH and GATE lights show the same. A TRIG key held with MACHINES alone opens the PRESET menu when you let go of MACHINES.
- The column on the left of SAMPLE's screen shows T1 to T6 with the track's pan under it. FUNC + LEVEL turns the pan 2 a step as before; from an odd value, such as 63 at the right end, it now lands on the even value next to it, so 0 can always be reached again.
- Tested on a Model:Cycles (2026-11-05), flashed over USB, step by step: locks on and off, saved and loaded, next to a Track FX, and the other machines' tracks as before. SAMPLE is Cycles One-Shot 0.15.

## 0.49 (2026-11-05)

- A new page, the Uploader, puts audio files on your Model:Cycles' +Drive over USB, for SAMPLE. Drop files and whole folders on the left, open a folder of the Cycles on the right, press Upload: each file becomes a 48 kHz mono sample, and the folders are made on the Cycles too. It works with the official OS too.
- On the left, make folders, drag rows into them and rename them; what is not audio is left out. Drag rows onto a folder on the right to upload them there. On the Cycles' side, a click opens a folder; Select puts a box on each row, to pick samples and folders and delete them in one go. A name already in a folder is skipped, not replaced.
- It is One-Shot's upload page, moved here in the site's look; the old address leads here. Checked against a stand-in Model:Cycles in the browser; a folder with a folder in it, uploaded from this page, arrived on a Model:Cycles (2026-11-05)

## 0.48 (2026-11-04)

- A card's Details open in a window over the page, like the sections' How to use: the cards no longer move. The window ends with a link to the card's part of the guide.
- The sections show only their title and the How to use button: the line under the title is gone, the window says it all.

## 0.47 (2026-11-04)

- SAMPLE, the CPU page, RESAMPLE, Control All Config, Trig Preview and Trig Condition Order are rewritten like the other cards: a block for each key, knob or setting on the page, in the Model:Cycles manual's words. RESAMPLE now explains THRESH and STEREO too.
- The Machines window says what happens when you flash other machines: a track plays whichever machine now has its place, and its own again once you flash the same machines; if you saved the project in between, pick the sample of a SAMPLE track again.

## 0.46 (2026-11-04)

- Digital Delay and POTS are rewritten like the Track FX cards: their Details say only what differs from the stock delay. The cards' short texts now describe the sound, and the Details no longer repeat them.
- The Effects and Track FX windows say what happens on a firmware without the effect or the Track FX, another model27 build or the official one: the pattern plays the stock delay, the preset plays without it, and flashing it again brings it back.

## 0.45 (2026-11-04)

- The Track FX cards are rewritten: each card's Details has a block per knob, with what it sets and what you hear, and the name the screen shows starts the card's text (SMP, CRU, RNG, RES). What all Track FX share is in the section's How to use window.

## 0.44 (2026-11-04)

- SAMPLE is now Cycles One-Shot 0.14. Turn SWEEP or CONTOUR on a SAMPLE track: the screen shows the Model:Samples' own pictures of its filter, not SNARE's. They are already in the Model:Cycles' firmware, so SAMPLE adds only what draws them.
- Checked in an emulator on the OS's own code. Tested in One-Shot's own firmware in the digiemu emulator and on a Model:Cycles, and this page's build of SAMPLE, the same file, on a Model:Cycles (2026-11-04)

## 0.43 (2026-11-04)

- The Machines, Effects and Track FX sections have a How to use button. It opens a window with what all their cards share: how to select a machine, an effect or a Track FX, and how to set, lock and save it. Keys show as boxes, knobs with a dashed underline.
- A Track FX parameter lock as the window describes it (a held trig, then RETRIG, then the knob) was tried on a Model:Cycles (2026-11-04)

## 0.42 (2026-11-04)

- POTS and the CPU page are tested: flashed from this page and played on a Model:Cycles (2026-11-04). Every card on this page is now tested.

## 0.41 (2026-11-04)

- The EQ Track FX takes less of the Model:Cycles' time: about a seventh less where it is heaviest (every value moving at once with High boosted, or the block a track comes to EQ), about a tenth less while it holds its settings. The sound is the same, bit for bit, checked in an emulator on the OS's own code. Tried on a Model:Cycles (2026-11-04)

## 0.40 (2026-11-04)

- The Reso Track FX takes less of the Model:Cycles' time: about a fifth less where it is heaviest (the block a track comes to Reso, and its values all moving at once), about a tenth less while it rings. The sound is the same, bit for bit, checked in an emulator on the OS's own code; only a ringing tail far under hearing (-90 dB) may be let go a block sooner or later. Tried on a Model:Cycles (2026-11-04)

## 0.39 (2026-11-04)

- A new card, RESAMPLE: hold SETTINGS and press RECORD, and a page records a track, the main mix or what comes in over USB. The take starts when you press RECORD, or after it with the track's next trig or when the sound gets loud enough, and stops when it dies away, after a length you set, or on RECORD. The stock name editor then names it, REC-001 and on, and it is saved as a sample in /recordings: as loud as you heard it, or raised to just under full scale with NORM. TO Tn puts it straight on the selected SAMPLE track. It goes with every other card.
- Checked in an emulator on the OS's own code: the sound bit for bit the same with the recorder, the take, the keys, the page, the save, and the level of a track's take. Tested on a Model:Cycles (2026-11-04) with the file this page builds with SAMPLE, Trig Preview and RESAMPLE: a track by Trig Preview and by LEVEL, TO Tn at the level heard, the main mix in stereo with NORM, and USB in stereo.

## 0.38 (2026-11-03)

- POTS takes about a third of the Model:Cycles' time it took: its telephone line now runs at 6 kHz instead of 12 kHz, with simpler parts. The idea stays the same: a narrow, lo-fi line, each repeat darker and grainier, moving up a little in pitch.
- It sounds a little different: a little more low-mid in the first repeats, a slightly duller echo, a faint fizz from bright sounds such as hats, and a hot beat breaks up a bit more. Its decays are as before.
- Checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-03): the CPU page shows a much smaller effects share with POTS playing, and it sounds good. The POTS card is Experimental until it is flashed from this page.

## 0.37 (2026-11-03)

- A new card, the CPU page (experimental): press SETTINGS, go to the list with USB mode, LCD, LED and Contrast and press its last row, CPU. The page shows how much of the Model:Cycles' time the sound takes over the last half second, with a mark at 85 %, where the screen and the knobs start to lag, the peak since you opened it, and the shares of the Track FX and of the effects. It updates twice a second; Return closes it. It goes with every other card.
- Checked in an emulator on the OS's own code: with the page the sound is bit for bit the same, and the measure, the row and the page do what they should. Tried on a Model:Cycles from the command line (2026-11-03), with POTS and Crush as this page builds them.
- Digital Delay and POTS now time themselves for the CPU page: a few instructions more a block, the sound the same.

## 0.36 (2026-11-03)

- The Ring Track FX takes about a third less of the Model:Cycles' time. Its carrier now comes from a finer table read without steps in between: the difference lies about 60 dB under the sound, and side by side the two sound the same. Checked in an emulator on the OS's own code, and tried on a Model:Cycles (2026-11-04)
- Ring Shape is now called Ring Wave (WAVE on the LFO's list), so that it is not taken for the SHAPE knob next to COLOR. It stays on RETRIG + COLOR, and the sounds you saved keep it.

## 0.35 (2026-11-03)

- The Samples Track FX takes a little less of the Model:Cycles' time: about a twelfth less while it filters, and almost nothing with Cutoff at 0. The sound is the same, bit for bit, checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-03)

## 0.34 (2026-11-03)

- Crush takes less of the Model:Cycles' time: about a quarter less in its heaviest settings, and more than half less with Rate to the right and Bits turned down. The sound is the same, bit for bit, checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-03)

## 0.33 (2026-11-02)

- SAMPLE now comes from Cycles One-Shot 0.13: Start and Length act on the note that plays. Turn SHAPE, or let an LFO move it, and the note ends where Length now puts it, its short fade-out whole; COLOR waits for the next trig, so an LFO on Start still gives each trig a start of its own. On a loop SHAPE moves the end at once and COLOR moves where the next time round starts, as on the Model:Samples, with the same hard seam.
- Tested in the digiemu emulator and on a Model:Cycles (2026-11-02) with the very file this page builds for SAMPLE alone, flashed over USB. The SAMPLE card now names MACHINES + PUNCH and GATE for Loop and Reverse, as the guide does.

## 0.32 (2026-11-02)

- Track FX: a knob the sound's Track FX doesn't use now says so. Hold RETRIG and turn it: the popup shows that Track FX's short name over ---, CRU --- on Crush for example, and Track FX OFF on a sound with no Track FX. Such a knob changes nothing, also with a trig, TRACK or LFO held. Before, it showed the name of another ticked Track FX, Ring Shape on a Crush track for example, and changed a value you couldn't hear.
- The sound of every Track FX is the same as before, checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-02)

## 0.31 (2026-11-02)

- Manager: a browser without Web MIDI (Safari, for example) now says so at the top of the page, since the Manager only works over USB from the page. The buttons that need the Cycles wait, and the setup no longer starts there; adding firmwares, Export and Import still work.

## 0.30 (2026-11-02)

- New page: the Manager, next to the Flasher. Each firmware keeps its own project: Switch backs up the project your Model:Cycles plays, flashes the other firmware over USB, brings that firmware's project back and checks it, then says which slot to save it in. You stop the sequencer and press YES on the Cycles; the rest takes about a minute.
- It works with any firmware for the Model:Cycles: the official OS, the builds you download from the Flasher, others. The firmware files and every backup stay in your browser, with a history per firmware; Export puts them all in one file, to keep or to move to another computer.
- Tried on a Model:Cycles (2026-11-02): switches between a model27 build and the official OS 1.13 both ways, each with its own project, also after turning it off and on. Chrome, Edge or Opera on a computer, with Elektron Transfer closed. The Cycles cannot tell which firmware it runs: the page keeps track of what it flashed and asks once at the start.

## 0.29 (2026-11-01)

- Ring, Reso and EQ are tested as this page builds them: flashed from this page and played on a Model:Cycles (2026-11-01). Their cards now show Tested.

## 0.28 (2026-11-01)

- Three new cards in Track FX, model27's own. Ring, a ring modulator: RETRIG + SWEEP is Freq, the carrier's note; RETRIG + CONTOUR is Mix, 0 dry; RETRIG + COLOR is Shape, from sine to square. Reso, a tuned resonator that makes hats, noise and hits ring at a pitch: RETRIG + SWEEP is Pitch, the MIDI note; RETRIG + CONTOUR is Amount, 0 off; RETRIG + COLOR is Tone; RETRIG + SHAPE is Decay, 20 ms to 10 s. EQ, a three-band equalizer: RETRIG + SWEEP is the Mid's frequency, RETRIG + CONTOUR its gain, RETRIG + COLOR the lows, RETRIG + SHAPE the highs, each 12 dB either way.
- All five Track FX can be ticked together; RETRIG + PITCH steps through them in the order of the cards, and each starts where it leaves the sound untouched. Every value works on every machine like any parameter: lock it on a trig, make it the LFO's destination, set it on all tracks with TRACK; CC 74 and 71 on SWEEP and CONTOUR.
- Ring, Reso and EQ are checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01); experimental here until flashed from this page. Samples and Crush sound as before.

## 0.27 (2026-11-01)

- Crush is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-11-01). Its card now shows Tested.

## 0.26 (2026-11-01)

- The Filters section is now called Track FX: filters and effects that sit on a track, after Volume + Dist. Each sound chooses one of them with RETRIG + PITCH, whose popup now reads Track FX. A firmware can hold four.
- New card in Track FX, Crush: a lower sample rate and fewer bits on any track. RETRIG + SWEEP is Rate: off at 0, a hard hold to the right (bright, metallic), a softer one to the left. RETRIG + CONTOUR is Bits: off at 127, fewer bits to the left, a single bit at 0. Both work together and on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71.
- Each Track FX starts at its own values: switching to Crush gives Rate 0 and Bits 127, so it starts off; switching between two Track FX starts the new one at its start values, switching to OFF and back keeps them.
- Crush is checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01); experimental here until flashed from this page. Samples sounds as before.

## 0.25 (2026-11-01)

- Samples is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-11-01). Its card now shows Tested.

## 0.24 (2026-11-01)

- Samples' Cutoff reads -64 to 63, as on SAMPLE: below 0 a lowpass, 0 off, above 0 a highpass. It read L64 … OFF … H63 before, which looked too much like Pan. As the LFO's destination it now reads CUTO instead of FREQ.
- Only the display changes; the sound is the same, checked in an emulator. Samples stays experimental until flashed from this page.

## 0.23 (2026-11-01)

- New card, Samples, in a new section, Filters: the Model:Samples' filter on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give the track's sound the filter, then RETRIG + SWEEP for Cutoff (lowpass to the left, off in the middle, highpass to the right) and RETRIG + CONTOUR for Reso. Both work on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71. Each sound keeps its own filter.
- Samples is SAMPLE's filter from Cycles One-Shot, unchanged, checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01), six filtered tracks with Control All included; experimental here until flashed from this page. Goes with every other card.
- Each held key now has one job. PATTERN + Delay Time chooses the pattern's delay (it was TRACK + Delay Time), and TRACK + Delay Time edits as on the stock OS again. SAMPLE's Loop and Reverse are on MACHINES + PUNCH and GATE (they were on RETRIG), and a tap on MACHINES still opens the machine list. RETRIG is the filter's. Played on a Model:Cycles with every card (2026-10-31)

## 0.22 (2026-10-31)

- The flasher is simpler: cards in three sections, Machines, Effects and Mods; tick what you want and press Install under the cards, and the install steps follow on their own page. Only the exceptions carry a tag (Experimental); every card's Details still say how it was tested.
- The page installs over USB the fast way only. If it doesn't find the Model:Cycles, download the .syx in step 4 and install it with Elektron Transfer. The Model:Samples choices and the Samples OS tab are on their own page, linked from the guide.
- In a browser without Web MIDI (Firefox, Safari), the page no longer shows a warning: it skips the connection step and offers the .syx to download, for Elektron Transfer.
- Shorter cards: each one has just its name and one plain sentence, and its Details are a few short paragraphs.
- The whole site, flasher, guide and this page, is in English only now.
- Nothing changes in the firmware: the same builds, checked against the same references.

## 0.21 (2026-10-30)

- Trig preview is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-30). Its card now shows Tested.

## 0.20 (2026-10-30)

- Trig preview is back (under Sequencer): with the sequencer stopped or paused, hold a trig and press PAGE, and the step sounds as the sequencer would play it, with its note, length, p-locks and sound lock, whatever its condition. While the sequencer plays, PAGE turns the page as before.
- drumkilla's trig preview 1.2.0, unchanged, checked in an emulator on the OS's own code and tested on a Model:Cycles (2026-10-04) with the same code inside Model-TG; experimental here until flashed from this page. Goes with SAMPLE, Digital Delay, POTS, Trig conditions and Control All Config.

## 0.19 (2026-10-30)

- Trig conditions, A:B before the percentages, is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-30). Its card now shows Tested.

## 0.18 (2026-10-30)

- New card, Trig conditions, A:B before the percentages (under Sequencer): hold a trig and turn CHANCE, and the conditions come as FILL … !1st, then 1:2 … 8:8, then 1% … 99%; the five dots under the value follow that order. A trig keeps the same condition as on the stock OS, so patterns are the same with and without it.
- model27's own, checked in an emulator on the OS's own code, and tested on a Model:Cycles from the command line (2026-10-30), the order and the dots; experimental here until flashed from this page. Goes with SAMPLE, Digital Delay, POTS and Control All Config.

## 0.17 (2026-10-30)

- SAMPLE now comes from Cycles One-Shot 0.12: hold a trig on a SAMPLE track and turn COLOR or SHAPE, and the whole screen shows that trig's waveform at full width, the lines on its Start and Length locks; a sample lock shows its own sample and name. The trig's note, velocity and length come back once the value goes; just holding a trig shows them as before.
- One-Shot 0.12 was played in its own build in the digiemu emulator and on a Model:Cycles (2026-10-30); as this page builds it, not yet on the machine.

## 0.16 (2026-10-29)

- Digital Delay and POTS leave the machines more time: the stock delay and reverb now start reading their lines before the voices play, instead of the mixer waiting for that read afterwards, which Model-TG measured at about 4.5 % of every block. Model-TG's idea (TinyGregAudio, MIT). The same sound, checked block for block in an emulator, and played on a Model:Cycles from this page (2026-10-29): a busy project runs and sounds the same.

## 0.15 (2026-10-29)

- POTS is tested again as this page builds it: its 12 kHz build flashed from this page and played on a Model:Cycles (2026-10-29), where a busy project that lagged with the 24 kHz build plays without lag. Its card shows Tested again.

## 0.14 (2026-10-29)

- POTS runs its telephone line at 12 kHz with an 8-bit codec, as a real phone does, instead of 24 kHz: about a fifth lighter on the processor, which a busy pattern needed. The sound stays the same, as measured on a computer. Experimental again until this build has been on the machine.

## 0.13 (2026-10-29)

- POTS is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-29), low notes and a kick in the send keeping their tone. Its card now shows Tested.

## 0.12 (2026-10-29)

- New card, POTS (under Sounds & machines), the second effect: a delay whose repeats go down an old telephone line, each pass darker and narrower (about 350 Hz to 3 kHz), a little further out of tune, fading and now and then dropping out, with a coarse grain on the tail. Hold TRACK and turn Delay Time to step the pattern from the stock Delay to Digital (when ticked) and on to POTS; the choice is saved with the pattern.
- model27's own, checked in an emulator on the OS's own code. Played on a Model:Cycles from the command line (2026-10-28), six tracks at once included; experimental here until flashed from this page. Goes with SAMPLE, Digital Delay and Control All Config.
- Since it was played, POTS holds a hot send (a loud sample, several tracks on the delay) at the level its sound was tuned at, so low notes and a kick keep their tone instead of turning to noise, and it needs about a fifth less processing. This build has not been on the machine yet.

## 0.11 (2026-10-27)

- Digital Delay is tested as this page builds it: flashed from this page alone and with SAMPLE and played on a Model:Cycles (2026-10-27). Its card now shows Tested.

## 0.10 (2026-10-27)

- New card, Digital Delay (under Sounds & machines), the first effect: a second delay for the delay slot, bright and clean, up to 5.4 s, each repeat a little thinner in the lows. Hold TRACK and turn Delay Time to switch the pattern between the stock Delay and Digital; the choice is saved with the pattern.
- Based on the digital delay of gialloinfuso's PPPCCC mods (MIT), its sound bit for bit, checked in an emulator against their own code. The same build played on a Model:Cycles from the command line (2026-10-27); experimental here until flashed from this page. Goes with SAMPLE and Control All Config.
- Effects are packages like the machines: each one plays in the delay or the reverb slot, the pattern chooses which, and more can come from other authors.

## 0.9 (2026-10-26)

- SAMPLE from Cycles One-Shot 0.11 is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-26): Loop and Reverse with their LEDs and letters, a single cycle looped, a trig cutting a sounding note, the switches kept by a saved project.

## 0.8 (2026-10-26)

- SAMPLE now comes from Cycles One-Shot 0.11 and loops and plays in reverse: on a SAMPLE track, hold RETRIG and press PUNCH for Loop, GATE for Reverse. Loop plays from Start to the end again and again with a hard seam, as on the Model:Samples, so a single-cycle waveform loops without a step; Reverse plays backwards from the next trig. Both are saved with the sound, the LEDs of PUNCH and GATE show them while RETRIG is held, and the sample's name ends with L and R while they are on. TRACK + PUNCH or GATE stays Control All.
- A trig that cuts a SAMPLE note still sounding brings the new one in over 0.67 ms, as the Model:Samples does, so a looped waveform or a sample played in reverse does not click on every trig.
- Tested as this page builds it in the digiemu emulator (2026-10-26), not yet on a Model:Cycles. SAMPLE no longer goes with LFO 2, 3, 4, a mod built from the command line and not on this page, which keeps LFO 2 where SAMPLE saves its switches.

## 0.7 (2026-10-25)

- SAMPLE from Cycles One-Shot 0.10 is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-25)

## 0.6 (2026-10-25)

- SAMPLE now comes from Cycles One-Shot 0.10: a narrow column on the left of its screen shows the current pattern's number, TRAK with the track's number, and the track's level as a bar that moves while you turn LEVEL. The sample's name and the waveform sit to its right. Sound, knobs and saved projects are as in 0.9.
- One-Shot 0.10 is tested in its own build in the emulator and on a Model:Cycles (2026-10-25); the build this page makes of it differs only in how the machine is registered, as before, and has not been flashed from here yet.

## 0.5 (2026-10-24)

- SAMPLE now comes from Cycles One-Shot 0.9: above the waveform, the current pattern's number (A01 to F16) sits on the left and the sample's name on the right, each in a box of its own. Nothing else changes: sound, knobs and saved projects are as in 0.8.
- One-Shot 0.9 is tested in its own build in the emulator and on a Model:Cycles (2026-10-24); the build this page makes of it differs only in how the machine is registered, as before, and has not been flashed from here yet.

## 0.4 (2026-10-22)

- Control All Config is tested as this page builds it: flashed from this page and tried on a Model:Cycles, alone and with SAMPLE (2026-10-22). Its card now shows Tested.

## 0.3 (2026-10-22)

- Control All Config is back (under Live playing): hold TRACK and press TRIG 1–6 to leave that track out of Control All (TRACK held + knob), or to put it back. While TRACK is held, TRIG 1–6 light for the tracks that follow; the active track always follows. Not saved: after power-on every track follows again.
- By durchgemacht (MIT), the version of Modded-Cycles 1.56; goes with SAMPLE. Experimental here until flashed from this page. Known limit: TRACK + LEVEL/DATA (volume, pan) still moves all six tracks.

## 0.2 (2026-10-22)

- The SAMPLE machine is tested as this page builds it: flashed from this page and played on a Model:Cycles, and run in the emulator (2026-10-22). Its card now shows Tested.
- SAMPLE now comes from Cycles One-Shot 0.8, the same sampler as 0.7, built the way every further machine will be: model27 places its code and registers it in the firmware when it builds, so machines can be added one by one instead of as pre-built combinations. Nothing changes in how SAMPLE plays; tested on a Model:Cycles next to a second test machine too.

## 0.1 (2026-10-21)

- model27 begins: a downstream fork of Modded-Cycles 1.55, the last release with a mod picker, aimed at a short list of mods that work together, four-knob machines and the Cycles Mod Standard. The entries below this one are Modded-Cycles' own releases. The first public beta.
- First card: the SAMPLE machine, Cycles One-Shot 0.7 by durchgemacht (MIT): a one-shot sampler for samples on the +Drive, picked in the PRESET browser and saved with the sound, with the Model:Samples' filter and a waveform view. Tested on a Model:Cycles (2026-10-21); experimental here until flashed from this page.
- Only the cards on a short list are offered; the other Modded-Cycles 1.55 mods stay buildable from the command line, with their authors' credits, and come back one by one, once reviewed against the standard. The Official firmware and Samples OS tabs are unchanged.
