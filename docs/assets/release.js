/* model27 versions, newest first. Shown on the home page and in the flasher.
 * New version: add an entry at the top, with what changed since the previous one:
 *   { version: "0.2", date: "2026-11-01", changes: [{ en: "…" }] }
 * English only (the site dropped French on 2026-10-31).
 * The entries from 1.56 down are Modded-Cycles' own releases, kept as they were: model27 starts from
 * release 1.55 (plus Control All Config, their 1.56), and those notes name the authors, testers and reporters
 * of everything model27 builds on.
 */
window.MC_RELEASES = [
  { version: "0.54", date: "2026-11-09", changes: [
    { en: "CHORD Tables reads wavetables with names: start the name with the wavetable's number, 01 to 63, and add what you like. 07 Glass Pad is wavetable 7, and 07 alone still is. Of two files with the same number, the one whose name comes first alphabetically plays. A renamed file is read within about two seconds" },
    { en: "The Uploader warns, in Wavetables, when a name does not start with 01 to 63 and when a number is already taken, saying which file plays. The files are uploaded all the same" },
    { en: "Checked in an emulator on the OS's own code: the names, two files with one number, renaming, adding, replacing and deleting files, 63 files at once. Tested on a Model:Cycles (2026-11-09), from the command line with all fourteen other cards: a name after the number, a name without one, two files with one number and a delete, and six CHORD tracks under load; not yet flashed from this page" },
  ] },
  { version: "0.53", date: "2026-11-09", changes: [
    { en: "The Uploader shows a warning or a problem in a window over the page, which stays until you press OK. After an upload it names each file that was skipped, not uploaded or uploaded with a warning, and why. The line under the title still says what happened last" },
    { en: "A wavetable in Wavetables whose first waveform is not a sine still uploads, and its warning now says what CHORD Tables does with it: it puts a sine in front, which SWEEP plays at the far left. Checked against a stand-in Model:Cycles in the browser" },
  ] },
  { version: "0.52", date: "2026-11-08", changes: [
    { en: "A new card, CHORD Tables: CHORD plays your own wavetables from the +Drive, one for each pattern. Put them on the +Drive with the Uploader, in a folder Wavetables, named 01 to 63. Hold PATTERN on a CHORD track and turn SWEEP to choose the pattern's wavetable: 0 is CHORD's own, 1 to 63 the files, two steps of the knob each. Every CHORD track in the pattern plays it, and SWEEP moves through its waveforms as through CHORD's own" },
    { en: "The wavetable is saved with the pattern and comes in at once when the pattern changes, also on notes that still sound, without a click. It plays from the same fast memory as CHORD's own, so six CHORD tracks with LFOs on SWEEP cost about what they cost with CHORD's own sound. A wavetable uploaded or deleted while the Model:Cycles runs is read within about two seconds" },
    { en: "Checked in an emulator on the OS's own code: every CHORD track sample for sample like the stock OS switched to the same wavetable, and like the stock OS at 0. Tested on a Model:Cycles (2026-11-08), from the command line with all fourteen other cards; not yet flashed from this page" },
  ] },
  { version: "0.51", date: "2026-11-06", changes: [
    { en: "A new card, Transpose: hold MACHINES and press TRIG 15 or 16 to move the notes of the TRIG keys an octave down or up, two at most. TRIG 8, 9, 11 and 12 make the active track jump 7 or 5 semitones down, or 5 or 7 up, at once, also while the pattern plays. Press the key again to go back. A new pattern brings everything back; a temporary reload or a reload from the project (FUNC + PATTERN) brings the pitch back and keeps the octave" },
    { en: "With MACHINES held, the six keys light up dim, half or full to show the octave and the jump. With this card, MACHINES opens the MACHINES menu when you let go of it, unless you used one of these keys" },
    { en: "Checked in an emulator on the OS's own code: every other key as on the stock OS, the jumps sample for sample like turning PITCH on every stock machine, the lights in the panel's own interrupt. Tested on a Model:Cycles (2026-11-06), from the command line with SAMPLE and with all fourteen cards: the keys, the octaves, the jumps on a running pattern, the lights at every LED setting, MACHINES, GRID RECORDING, and both ways of reloading the pattern; then flashed from this page" },
  ] },
  { version: "0.50", date: "2026-11-06", changes: [
    { en: "SAMPLE locks Loop and Reverse on single steps: hold one or more TRIG keys and MACHINES, then press PUNCH or GATE. Those steps play it the other way round from the track, saved with the pattern; press it again and they follow the track again" },
    { en: "While you hold a TRIG key on a SAMPLE track, the right half of the screen shows that step's LOOP and REV, lit when it plays them, and with MACHINES held the PUNCH and GATE lights show the same. A TRIG key held with MACHINES alone opens the PRESET menu when you let go of MACHINES" },
    { en: "The column on the left of SAMPLE's screen shows T1 to T6 with the track's pan under it. FUNC + LEVEL turns the pan 2 a step as before; from an odd value, such as 63 at the right end, it now lands on the even value next to it, so 0 can always be reached again" },
    { en: "Tested on a Model:Cycles (2026-11-05), flashed over USB, step by step: locks on and off, saved and loaded, next to a Track FX, and the other machines' tracks as before. SAMPLE is Cycles One-Shot 0.15" },
  ] },
  { version: "0.49", date: "2026-11-05", changes: [
    { en: "A new page, the Uploader, puts audio files on your Model:Cycles' +Drive over USB, for SAMPLE. Drop files and whole folders on the left, open a folder of the Cycles on the right, press Upload: each file becomes a 48 kHz mono sample, and the folders are made on the Cycles too. It works with the official OS too" },
    { en: "On the left, make folders, drag rows into them and rename them; what is not audio is left out. Drag rows onto a folder on the right to upload them there. On the Cycles' side, a click opens a folder; Select puts a box on each row, to pick samples and folders and delete them in one go. A name already in a folder is skipped, not replaced" },
    { en: "It is One-Shot's upload page, moved here in the site's look; the old address leads here. Checked against a stand-in Model:Cycles in the browser; a folder with a folder in it, uploaded from this page, arrived on a Model:Cycles (2026-11-05)" },
  ] },
  { version: "0.48", date: "2026-11-04", changes: [
    { en: "A card's Details open in a window over the page, like the sections' How to use: the cards no longer move. The window ends with a link to the card's part of the guide" },
    { en: "The sections show only their title and the How to use button: the line under the title is gone, the window says it all" },
  ] },
  { version: "0.47", date: "2026-11-04", changes: [
    { en: "SAMPLE, the CPU page, RESAMPLE, Control All Config, Trig Preview and Trig Condition Order are rewritten like the other cards: a block for each key, knob or setting on the page, in the Model:Cycles manual's words. RESAMPLE now explains THRESH and STEREO too" },
    { en: "The Machines window says what happens when you flash other machines: a track plays whichever machine now has its place, and its own again once you flash the same machines; if you saved the project in between, pick the sample of a SAMPLE track again" },
  ] },
  { version: "0.46", date: "2026-11-04", changes: [
    { en: "Digital Delay and POTS are rewritten like the Track FX cards: their Details say only what differs from the stock delay. The cards' short texts now describe the sound, and the Details no longer repeat them" },
    { en: "The Effects and Track FX windows say what happens on a firmware without the effect or the Track FX, another model27 build or the official one: the pattern plays the stock delay, the preset plays without it, and flashing it again brings it back" },
  ] },
  { version: "0.45", date: "2026-11-04", changes: [
    { en: "The Track FX cards are rewritten: each card's Details has a block per knob, with what it sets and what you hear, and the name the screen shows starts the card's text (SMP, CRU, RNG, RES). What all Track FX share is in the section's How to use window" },
  ] },
  { version: "0.44", date: "2026-11-04", changes: [
    { en: "SAMPLE is now Cycles One-Shot 0.14. Turn SWEEP or CONTOUR on a SAMPLE track: the screen shows the Model:Samples' own pictures of its filter, not SNARE's. They are already in the Model:Cycles' firmware, so SAMPLE adds only what draws them" },
    { en: "Checked in an emulator on the OS's own code. Tested in One-Shot's own firmware in the digiemu emulator and on a Model:Cycles, and this page's build of SAMPLE, the same file, on a Model:Cycles (2026-11-04)" },
  ] },
  { version: "0.43", date: "2026-11-04", changes: [
    { en: "The Machines, Effects and Track FX sections have a How to use button. It opens a window with what all their cards share: how to select a machine, an effect or a Track FX, and how to set, lock and save it. Keys show as boxes, knobs with a dashed underline" },
    { en: "A Track FX parameter lock as the window describes it (a held trig, then RETRIG, then the knob) was tried on a Model:Cycles (2026-11-04)" },
  ] },
  { version: "0.42", date: "2026-11-04", changes: [
    { en: "POTS and the CPU page are tested: flashed from this page and played on a Model:Cycles (2026-11-04). Every card on this page is now tested" },
  ] },
  { version: "0.41", date: "2026-11-04", changes: [
    { en: "The EQ Track FX takes less of the Model:Cycles' time: about a seventh less where it is heaviest (every value moving at once with High boosted, or the block a track comes to EQ), about a tenth less while it holds its settings. The sound is the same, bit for bit, checked in an emulator on the OS's own code. Tried on a Model:Cycles (2026-11-04)" },
  ] },
  { version: "0.40", date: "2026-11-04", changes: [
    { en: "The Reso Track FX takes less of the Model:Cycles' time: about a fifth less where it is heaviest (the block a track comes to Reso, and its values all moving at once), about a tenth less while it rings. The sound is the same, bit for bit, checked in an emulator on the OS's own code; only a ringing tail far under hearing (-90 dB) may be let go a block sooner or later. Tried on a Model:Cycles (2026-11-04)" },
  ] },
  { version: "0.39", date: "2026-11-04", changes: [
    { en: "A new card, RESAMPLE: hold SETTINGS and press RECORD, and a page records a track, the main mix or what comes in over USB. The take starts when you press RECORD, or after it with the track's next trig or when the sound gets loud enough, and stops when it dies away, after a length you set, or on RECORD. The stock name editor then names it, REC-001 and on, and it is saved as a sample in /recordings: as loud as you heard it, or raised to just under full scale with NORM. TO Tn puts it straight on the selected SAMPLE track. It goes with every other card" },
    { en: "Checked in an emulator on the OS's own code: the sound bit for bit the same with the recorder, the take, the keys, the page, the save, and the level of a track's take. Tested on a Model:Cycles (2026-11-04) with the file this page builds with SAMPLE, Trig Preview and RESAMPLE: a track by Trig Preview and by LEVEL, TO Tn at the level heard, the main mix in stereo with NORM, and USB in stereo" },
  ] },
  { version: "0.38", date: "2026-11-03", changes: [
    { en: "POTS takes about a third of the Model:Cycles' time it took: its telephone line now runs at 6 kHz instead of 12 kHz, with simpler parts. The idea stays the same: a narrow, lo-fi line, each repeat darker and grainier, moving up a little in pitch" },
    { en: "It sounds a little different: a little more low-mid in the first repeats, a slightly duller echo, a faint fizz from bright sounds such as hats, and a hot beat breaks up a bit more. Its decays are as before" },
    { en: "Checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-03): the CPU page shows a much smaller effects share with POTS playing, and it sounds good. The POTS card is Experimental until it is flashed from this page" },
  ] },
  { version: "0.37", date: "2026-11-03", changes: [
    { en: "A new card, the CPU page (experimental): press SETTINGS, go to the list with USB mode, LCD, LED and Contrast and press its last row, CPU. The page shows how much of the Model:Cycles' time the sound takes over the last half second, with a mark at 85 %, where the screen and the knobs start to lag, the peak since you opened it, and the shares of the Track FX and of the effects. It updates twice a second; Return closes it. It goes with every other card" },
    { en: "Checked in an emulator on the OS's own code: with the page the sound is bit for bit the same, and the measure, the row and the page do what they should. Tried on a Model:Cycles from the command line (2026-11-03), with POTS and Crush as this page builds them" },
    { en: "Digital Delay and POTS now time themselves for the CPU page: a few instructions more a block, the sound the same" },
  ] },
  { version: "0.36", date: "2026-11-03", changes: [
    { en: "The Ring Track FX takes about a third less of the Model:Cycles' time. Its carrier now comes from a finer table read without steps in between: the difference lies about 60 dB under the sound, and side by side the two sound the same. Checked in an emulator on the OS's own code, and tried on a Model:Cycles (2026-11-04)" },
    { en: "Ring Shape is now called Ring Wave (WAVE on the LFO's list), so that it is not taken for the SHAPE knob next to COLOR. It stays on RETRIG + COLOR, and the sounds you saved keep it" },
  ] },
  { version: "0.35", date: "2026-11-03", changes: [
    { en: "The Samples Track FX takes a little less of the Model:Cycles' time: about a twelfth less while it filters, and almost nothing with Cutoff at 0. The sound is the same, bit for bit, checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-03)" },
  ] },
  { version: "0.34", date: "2026-11-03", changes: [
    { en: "Crush takes less of the Model:Cycles' time: about a quarter less in its heaviest settings, and more than half less with Rate to the right and Bits turned down. The sound is the same, bit for bit, checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-03)" },
  ] },
  { version: "0.33", date: "2026-11-02", changes: [
    { en: "SAMPLE now comes from Cycles One-Shot 0.13: Start and Length act on the note that plays. Turn SHAPE, or let an LFO move it, and the note ends where Length now puts it, its short fade-out whole; COLOR waits for the next trig, so an LFO on Start still gives each trig a start of its own. On a loop SHAPE moves the end at once and COLOR moves where the next time round starts, as on the Model:Samples, with the same hard seam" },
    { en: "Tested in the digiemu emulator and on a Model:Cycles (2026-11-02) with the very file this page builds for SAMPLE alone, flashed over USB. The SAMPLE card now names MACHINES + PUNCH and GATE for Loop and Reverse, as the guide does" },
  ] },
  { version: "0.32", date: "2026-11-02", changes: [
    { en: "Track FX: a knob the sound's Track FX doesn't use now says so. Hold RETRIG and turn it: the popup shows that Track FX's short name over ---, CRU --- on Crush for example, and Track FX OFF on a sound with no Track FX. Such a knob changes nothing, also with a trig, TRACK or LFO held. Before, it showed the name of another ticked Track FX, Ring Shape on a Crush track for example, and changed a value you couldn't hear" },
    { en: "The sound of every Track FX is the same as before, checked in an emulator on the OS's own code. Tried on a Model:Cycles from the command line (2026-11-02)" },
  ] },
  { version: "0.31", date: "2026-11-02", changes: [
    { en: "Manager: a browser without Web MIDI (Safari, for example) now says so at the top of the page, since the Manager only works over USB from the page. The buttons that need the Cycles wait, and the setup no longer starts there; adding firmwares, Export and Import still work" },
  ] },
  { version: "0.30", date: "2026-11-02", changes: [
    { en: "New page: the Manager, next to the Flasher. Each firmware keeps its own project: Switch backs up the project your Model:Cycles plays, flashes the other firmware over USB, brings that firmware's project back and checks it, then says which slot to save it in. You stop the sequencer and press YES on the Cycles; the rest takes about a minute" },
    { en: "It works with any firmware for the Model:Cycles: the official OS, the builds you download from the Flasher, others. The firmware files and every backup stay in your browser, with a history per firmware; Export puts them all in one file, to keep or to move to another computer" },
    { en: "Tried on a Model:Cycles (2026-11-02): switches between a model27 build and the official OS 1.13 both ways, each with its own project, also after turning it off and on. Chrome, Edge or Opera on a computer, with Elektron Transfer closed. The Cycles cannot tell which firmware it runs: the page keeps track of what it flashed and asks once at the start" },
  ] },
  { version: "0.29", date: "2026-11-01", changes: [
    { en: "Ring, Reso and EQ are tested as this page builds them: flashed from this page and played on a Model:Cycles (2026-11-01). Their cards now show Tested" },
  ] },
  { version: "0.28", date: "2026-11-01", changes: [
    { en: "Three new cards in Track FX, model27's own. Ring, a ring modulator: RETRIG + SWEEP is Freq, the carrier's note; RETRIG + CONTOUR is Mix, 0 dry; RETRIG + COLOR is Shape, from sine to square. Reso, a tuned resonator that makes hats, noise and hits ring at a pitch: RETRIG + SWEEP is Pitch, the MIDI note; RETRIG + CONTOUR is Amount, 0 off; RETRIG + COLOR is Tone; RETRIG + SHAPE is Decay, 20 ms to 10 s. EQ, a three-band equalizer: RETRIG + SWEEP is the Mid's frequency, RETRIG + CONTOUR its gain, RETRIG + COLOR the lows, RETRIG + SHAPE the highs, each 12 dB either way" },
    { en: "All five Track FX can be ticked together; RETRIG + PITCH steps through them in the order of the cards, and each starts where it leaves the sound untouched. Every value works on every machine like any parameter: lock it on a trig, make it the LFO's destination, set it on all tracks with TRACK; CC 74 and 71 on SWEEP and CONTOUR" },
    { en: "Ring, Reso and EQ are checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01); experimental here until flashed from this page. Samples and Crush sound as before" },
  ] },
  { version: "0.27", date: "2026-11-01", changes: [
    { en: "Crush is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-11-01). Its card now shows Tested" },
  ] },
  { version: "0.26", date: "2026-11-01", changes: [
    { en: "The Filters section is now called Track FX: filters and effects that sit on a track, after Volume + Dist. Each sound chooses one of them with RETRIG + PITCH, whose popup now reads Track FX. A firmware can hold four" },
    { en: "New card in Track FX, Crush: a lower sample rate and fewer bits on any track. RETRIG + SWEEP is Rate: off at 0, a hard hold to the right (bright, metallic), a softer one to the left. RETRIG + CONTOUR is Bits: off at 127, fewer bits to the left, a single bit at 0. Both work together and on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71" },
    { en: "Each Track FX starts at its own values: switching to Crush gives Rate 0 and Bits 127, so it starts off; switching between two Track FX starts the new one at its start values, switching to OFF and back keeps them" },
    { en: "Crush is checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01); experimental here until flashed from this page. Samples sounds as before" },
  ] },
  { version: "0.25", date: "2026-11-01", changes: [
    { en: "Samples is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-11-01). Its card now shows Tested" },
  ] },
  { version: "0.24", date: "2026-11-01", changes: [
    { en: "Samples' Cutoff reads -64 to 63, as on SAMPLE: below 0 a lowpass, 0 off, above 0 a highpass. It read L64 … OFF … H63 before, which looked too much like Pan. As the LFO's destination it now reads CUTO instead of FREQ" },
    { en: "Only the display changes; the sound is the same, checked in an emulator. Samples stays experimental until flashed from this page" },
  ] },
  { version: "0.23", date: "2026-11-01", changes: [
    { en: "New card, Samples, in a new section, Filters: the Model:Samples' filter on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give the track's sound the filter, then RETRIG + SWEEP for Cutoff (lowpass to the left, off in the middle, highpass to the right) and RETRIG + CONTOUR for Reso. Both work on every machine like any parameter: lock them on a trig, make them the LFO's destination, set them on all tracks with TRACK, or send CC 74 and 71. Each sound keeps its own filter" },
    { en: "Samples is SAMPLE's filter from Cycles One-Shot, unchanged, checked bit for bit in an emulator and played on a Model:Cycles from the command line (2026-11-01), six filtered tracks with Control All included; experimental here until flashed from this page. Goes with every other card" },
    { en: "Each held key now has one job. PATTERN + Delay Time chooses the pattern's delay (it was TRACK + Delay Time), and TRACK + Delay Time edits as on the stock OS again. SAMPLE's Loop and Reverse are on MACHINES + PUNCH and GATE (they were on RETRIG), and a tap on MACHINES still opens the machine list. RETRIG is the filter's. Played on a Model:Cycles with every card (2026-10-31)" },
  ] },
  { version: "0.22", date: "2026-10-31", changes: [
    { en: "The flasher is simpler: cards in three sections, Machines, Effects and Mods; tick what you want and press Install under the cards, and the install steps follow on their own page. Only the exceptions carry a tag (Experimental); every card's Details still say how it was tested" },
    { en: "The page installs over USB the fast way only. If it doesn't find the Model:Cycles, download the .syx in step 4 and install it with Elektron Transfer. The Model:Samples choices and the Samples OS tab are on their own page, linked from the guide" },
    { en: "In a browser without Web MIDI (Firefox, Safari), the page no longer shows a warning: it skips the connection step and offers the .syx to download, for Elektron Transfer" },
    { en: "Shorter cards: each one has just its name and one plain sentence, and its Details are a few short paragraphs" },
    { en: "The whole site, flasher, guide and this page, is in English only now" },
    { en: "Nothing changes in the firmware: the same builds, checked against the same references" },
  ] },
  { version: "0.21", date: "2026-10-30", changes: [
    { en: "Trig preview is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-30). Its card now shows Tested" },
  ] },
  { version: "0.20", date: "2026-10-30", changes: [
    { en: "Trig preview is back (under Sequencer): with the sequencer stopped or paused, hold a trig and press PAGE, and the step sounds as the sequencer would play it, with its note, length, p-locks and sound lock, whatever its condition. While the sequencer plays, PAGE turns the page as before" },
    { en: "drumkilla's trig preview 1.2.0, unchanged, checked in an emulator on the OS's own code and tested on a Model:Cycles (2026-10-04) with the same code inside Model-TG; experimental here until flashed from this page. Goes with SAMPLE, Digital Delay, POTS, Trig conditions and Control All Config" },
  ] },
  { version: "0.19", date: "2026-10-30", changes: [
    { en: "Trig conditions, A:B before the percentages, is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-30). Its card now shows Tested" },
  ] },
  { version: "0.18", date: "2026-10-30", changes: [
    { en: "New card, Trig conditions, A:B before the percentages (under Sequencer): hold a trig and turn CHANCE, and the conditions come as FILL … !1st, then 1:2 … 8:8, then 1% … 99%; the five dots under the value follow that order. A trig keeps the same condition as on the stock OS, so patterns are the same with and without it" },
    { en: "model27's own, checked in an emulator on the OS's own code, and tested on a Model:Cycles from the command line (2026-10-30), the order and the dots; experimental here until flashed from this page. Goes with SAMPLE, Digital Delay, POTS and Control All Config" },
  ] },
  { version: "0.17", date: "2026-10-30", changes: [
    { en: "SAMPLE now comes from Cycles One-Shot 0.12: hold a trig on a SAMPLE track and turn COLOR or SHAPE, and the whole screen shows that trig's waveform at full width, the lines on its Start and Length locks; a sample lock shows its own sample and name. The trig's note, velocity and length come back once the value goes; just holding a trig shows them as before" },
    { en: "One-Shot 0.12 was played in its own build in the digiemu emulator and on a Model:Cycles (2026-10-30); as this page builds it, not yet on the machine" },
  ] },
  { version: "0.16", date: "2026-10-29", changes: [
    { en: "Digital Delay and POTS leave the machines more time: the stock delay and reverb now start reading their lines before the voices play, instead of the mixer waiting for that read afterwards, which Model-TG measured at about 4.5 % of every block. Model-TG's idea (TinyGregAudio, MIT). The same sound, checked block for block in an emulator, and played on a Model:Cycles from this page (2026-10-29): a busy project runs and sounds the same" },
  ] },
  { version: "0.15", date: "2026-10-29", changes: [
    { en: "POTS is tested again as this page builds it: its 12 kHz build flashed from this page and played on a Model:Cycles (2026-10-29), where a busy project that lagged with the 24 kHz build plays without lag. Its card shows Tested again" },
  ] },
  { version: "0.14", date: "2026-10-29", changes: [
    { en: "POTS runs its telephone line at 12 kHz with an 8-bit codec, as a real phone does, instead of 24 kHz: about a fifth lighter on the processor, which a busy pattern needed. The sound stays the same, as measured on a computer. Experimental again until this build has been on the machine" },
  ] },
  { version: "0.13", date: "2026-10-29", changes: [
    { en: "POTS is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-29), low notes and a kick in the send keeping their tone. Its card now shows Tested" },
  ] },
  { version: "0.12", date: "2026-10-29", changes: [
    { en: "New card, POTS (under Sounds & machines), the second effect: a delay whose repeats go down an old telephone line, each pass darker and narrower (about 350 Hz to 3 kHz), a little further out of tune, fading and now and then dropping out, with a coarse grain on the tail. Hold TRACK and turn Delay Time to step the pattern from the stock Delay to Digital (when ticked) and on to POTS; the choice is saved with the pattern" },
    { en: "model27's own, checked in an emulator on the OS's own code. Played on a Model:Cycles from the command line (2026-10-28), six tracks at once included; experimental here until flashed from this page. Goes with SAMPLE, Digital Delay and Control All Config" },
    { en: "Since it was played, POTS holds a hot send (a loud sample, several tracks on the delay) at the level its sound was tuned at, so low notes and a kick keep their tone instead of turning to noise, and it needs about a fifth less processing. This build has not been on the machine yet" },
  ] },
  { version: "0.11", date: "2026-10-27", changes: [
    { en: "Digital Delay is tested as this page builds it: flashed from this page alone and with SAMPLE and played on a Model:Cycles (2026-10-27). Its card now shows Tested" },
  ] },
  { version: "0.10", date: "2026-10-27", changes: [
    { en: "New card, Digital Delay (under Sounds & machines), the first effect: a second delay for the delay slot, bright and clean, up to 5.4 s, each repeat a little thinner in the lows. Hold TRACK and turn Delay Time to switch the pattern between the stock Delay and Digital; the choice is saved with the pattern" },
    { en: "Based on the digital delay of gialloinfuso's PPPCCC mods (MIT), its sound bit for bit, checked in an emulator against their own code. The same build played on a Model:Cycles from the command line (2026-10-27); experimental here until flashed from this page. Goes with SAMPLE and Control All Config" },
    { en: "Effects are packages like the machines: each one plays in the delay or the reverb slot, the pattern chooses which, and more can come from other authors" },
  ] },
  { version: "0.9", date: "2026-10-26", changes: [
    { en: "SAMPLE from Cycles One-Shot 0.11 is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-26): Loop and Reverse with their LEDs and letters, a single cycle looped, a trig cutting a sounding note, the switches kept by a saved project" },
  ] },
  { version: "0.8", date: "2026-10-26", changes: [
    { en: "SAMPLE now comes from Cycles One-Shot 0.11 and loops and plays in reverse: on a SAMPLE track, hold RETRIG and press PUNCH for Loop, GATE for Reverse. Loop plays from Start to the end again and again with a hard seam, as on the Model:Samples, so a single-cycle waveform loops without a step; Reverse plays backwards from the next trig. Both are saved with the sound, the LEDs of PUNCH and GATE show them while RETRIG is held, and the sample's name ends with L and R while they are on. TRACK + PUNCH or GATE stays Control All" },
    { en: "A trig that cuts a SAMPLE note still sounding brings the new one in over 0.67 ms, as the Model:Samples does, so a looped waveform or a sample played in reverse does not click on every trig" },
    { en: "Tested as this page builds it in the digiemu emulator (2026-10-26), not yet on a Model:Cycles. SAMPLE no longer goes with LFO 2, 3, 4, a mod built from the command line and not on this page, which keeps LFO 2 where SAMPLE saves its switches" },
  ] },
  { version: "0.7", date: "2026-10-25", changes: [
    { en: "SAMPLE from Cycles One-Shot 0.10 is tested as this page builds it: flashed from this page and played on a Model:Cycles (2026-10-25)" },
  ] },
  { version: "0.6", date: "2026-10-25", changes: [
    { en: "SAMPLE now comes from Cycles One-Shot 0.10: a narrow column on the left of its screen shows the current pattern's number, TRAK with the track's number, and the track's level as a bar that moves while you turn LEVEL. The sample's name and the waveform sit to its right. Sound, knobs and saved projects are as in 0.9" },
    { en: "One-Shot 0.10 is tested in its own build in the emulator and on a Model:Cycles (2026-10-25); the build this page makes of it differs only in how the machine is registered, as before, and has not been flashed from here yet" },
  ] },
  { version: "0.5", date: "2026-10-24", changes: [
    { en: "SAMPLE now comes from Cycles One-Shot 0.9: above the waveform, the current pattern's number (A01 to F16) sits on the left and the sample's name on the right, each in a box of its own. Nothing else changes: sound, knobs and saved projects are as in 0.8" },
    { en: "One-Shot 0.9 is tested in its own build in the emulator and on a Model:Cycles (2026-10-24); the build this page makes of it differs only in how the machine is registered, as before, and has not been flashed from here yet" },
  ] },
  { version: "0.4", date: "2026-10-22", changes: [
    { en: "Control All Config is tested as this page builds it: flashed from this page and tried on a Model:Cycles, alone and with SAMPLE (2026-10-22). Its card now shows Tested" },
  ] },
  { version: "0.3", date: "2026-10-22", changes: [
    { en: "Control All Config is back (under Live playing): hold TRACK and press TRIG 1–6 to leave that track out of Control All (TRACK held + knob), or to put it back. While TRACK is held, TRIG 1–6 light for the tracks that follow; the active track always follows. Not saved: after power-on every track follows again" },
    { en: "By durchgemacht (MIT), the version of Modded-Cycles 1.56; goes with SAMPLE. Experimental here until flashed from this page. Known limit: TRACK + LEVEL/DATA (volume, pan) still moves all six tracks" },
  ] },
  { version: "0.2", date: "2026-10-22", changes: [
    { en: "The SAMPLE machine is tested as this page builds it: flashed from this page and played on a Model:Cycles, and run in the emulator (2026-10-22). Its card now shows Tested" },
    { en: "SAMPLE now comes from Cycles One-Shot 0.8, the same sampler as 0.7, built the way every further machine will be: model27 places its code and registers it in the firmware when it builds, so machines can be added one by one instead of as pre-built combinations. Nothing changes in how SAMPLE plays; tested on a Model:Cycles next to a second test machine too" },
  ] },
  { version: "0.1", date: "2026-10-21", changes: [
    { en: "model27 begins: a downstream fork of Modded-Cycles 1.55, the last release with a mod picker, aimed at a short list of mods that work together, four-knob machines and the Cycles Mod Standard. The entries below this one are Modded-Cycles' own releases. The first public beta" },
    { en: "First card: the SAMPLE machine, Cycles One-Shot 0.7 by durchgemacht (MIT): a one-shot sampler for samples on the +Drive, picked in the PRESET browser and saved with the sound, with the Model:Samples' filter and a waveform view. Tested on a Model:Cycles (2026-10-21); experimental here until flashed from this page" },
    { en: "Only the cards on a short list are offered; the other Modded-Cycles 1.55 mods stay buildable from the command line, with their authors' credits, and come back one by one, once reviewed against the standard. The Official firmware and Samples OS tabs are unchanged" },
  ] },
  { version: "1.56", date: "2026-10-19", changes: [
    { en: "New mod, Control All, your choice of tracks (under Live playing): hold TRACK and press TRIG 1–6 to leave that track out of Control All (TRACK held + knob), or to put it back. While TRACK is held, TRIG 1–6 light for the tracks that follow. The active track always follows, as on the Digitakt and Digitone; left-out tracks also keep their machine, LFO destination and PUNCH/GATE. The choice is not saved: after power-on every track follows again" },
    { en: "Control All Config 1.0 by durchgemacht (MIT), tested by its author on a Model:Cycles, placed here in four free sprite masks so that it goes with every other mod. Experimental until tested on Maxime's machine. Known limit: TRACK + LEVEL/DATA (volume, pan) still moves all six tracks" },
  ] },
  { version: "1.55", date: "2026-10-18", changes: [
    { en: "ACID machine, no more click at the start of notes: each new note now fades in over less than a millisecond, too short to hear as an attack, so the bass line stays punchy without the tick. Slides are unchanged" },
    { en: "Tested on a Model:Cycles with the five Syntakt engines and MACRO, and checked in the emulator on the OS's own code with the real sequencer: only the first moment of each new note changes. Applies to every version of ACID (alone, with Model-TG, with MACRO and the Syntakt engines)" },
  ] },
  { version: "1.54", date: "2026-10-12", changes: [
    { en: "MACRO machine, lo-fi fixed: on a MACRO track, hold FUNC and turn PITCH to really set the lo-fi. In 1.46 this still changed the note by semitones, and the lo-fi could not be reached from the knobs. The screen now shows OFF in the middle, the sample rate on the left (46K down to 4K, in kHz) and the bit depth on the right (12B down to 2B, in bits), in large letters, one step per click of the knob" },
    { en: "PITCH alone still tunes MACRO, and on the other machines FUNC + PITCH still changes the note by semitones. Checked in the emulator on the OS's own knob and screen code, alone, with Model-TG, with the Syntakt engines and with the other mods, and tested on a Model:Cycles. The versions of MACRO with ACID (1.53) get the same fix, checked in the emulator. Thanks to RICARDOPABLO909 and amok_san for the report" },
  ] },
  { version: "1.53", date: "2026-10-12", changes: [
    { en: "New mod, ACID machine: one extra machine after Chord (after the Sampler with Model-TG), an acid bass in the style of the TB-303, from Robin Schmidt's open-source Open303 model. COLOR is the cutoff, SHAPE the resonance, SWEEP the env mod, CONTOUR the drive (from clean to fuzz, at about the same volume) and DECAY the decay; PUNCH switches the wave from saw to square" },
    { en: "Slides come from your trigs: a trig whose length (LEN) runs past the next trig slides into the next note instead of playing it again. Played live, a note played while another is held slides too" },
    { en: "Tested on a Model:Cycles, drive included, and checked in the emulator on the OS's own code with the real sequencer, alone and with Model-TG" },
    { en: "ACID also plays alongside the MACRO machine and the Syntakt engines: tick them together and ACID comes last, after them. The engines' load governor looks after ACID too: under a very heavy load it can fade an ACID note out, and the track's next trig then plays afresh. Tested on a Model:Cycles with all five engines, MACRO and ACID, with and without Model-TG; other choices are checked in the emulator and stay experimental" },
  ] },
  { version: "1.48", date: "2026-10-12", changes: [
    { en: "New mod, LFO 2, 3, 4: three more LFOs on every track, under Sounds & machines. On the LFO page, press [LFO] again: a big 2, then 3, then 4 shows in the left box, and the fifth press closes the page. Each extra LFO has its own speed, multiplier, waveform, destination and depth; fade, start phase and mode stay shared with LFO 1" },
    { en: "LFO 2 is saved with the sound and can be p-locked; LFO 3 and 4 are for live play (one setting per track, not saved). Works with or without Model-TG, and with Model-TG it also fixes the Attack, Filter and Resonance p-locks that came back on other parameters after reloading a pattern" },
    { en: "Based on a mod by DavidCaruso (his Model-TG-VA-DR-v1), rewritten for this project. Tested on a Model:Cycles, and checked in the emulator on the OS's own code, alone and with the other mods. It goes with every other mod except the Per-track filter for now, as both keep their settings in the same place of the sound" },
  ] },
  { version: "1.47", date: "2026-10-12", changes: [
    { en: "Mods on a Model:Samples: the Mods tab now asks which machine you are flashing. Choose “Model:Samples, on its own OS” and the page installs the Model:Cycles OS with the mods you tick, packed inside your Model:Samples firmware; Model-TG's Sampler keeps your samples playing. Step 2 asks for the official Model:Samples OS file too" },
    { en: "To change mods later, choose “Model:Samples, already on the Cycles OS”. The page only sends to a machine that answers as expected, and the way back to the Model:Samples OS stays in the Samples OS tab, over USB. Whatever the machine, the flasher always installs the Model:Cycles OS" },
    { en: "Tested on a Model:Samples, both choices (on its own OS, and already on the Cycles OS), and checked in the emulator on both OSes' own update checks and on the Model:Samples startup code, up to the largest set of mods. Nothing changes for a Model:Cycles. Original flasher by RDS (AIM), integrated into Modded Cycles by DaftMaple" },
    { en: "Step 3 now names the machine you are flashing: with a Model:Samples choice, its messages and instructions say Model:Samples (for example “The Model:Samples doesn't appear over USB”), and the port to pick is the one named after the OS it runs. The flasher's tagline now says Model:Cycles or Model:Samples" },
  ] },
  { version: "1.46", date: "2026-10-11", changes: [
    { en: "MACRO machine, lo-fi: on a MACRO track, hold FUNC and turn PITCH (the fine tune). In the middle, its default, nothing changes. Turn left for RATE: the sample rate drops step by step from 48 kHz to about 4 kHz, for a grainy, aliased sound. Turn right for BITS: from 12 bits down to 2, for a crushed, 8-bit style sound. It can be locked on a step. On MACRO tracks, FUNC + PITCH no longer fine-tunes the note" },
    { en: "MACRO is lighter: 13 models whose sound only follows the note (CSAW, SAW/SQUARE, SQUARE SUB, SAW SUB, the TRIPLE waves except RING MOD, the four wavetable models and DIGITAL MODULATION) are now computed at 48 kHz instead of 96 kHz, for about half the computing and the same spectrum to within about 1 dB. They include the heaviest ones: WAVE MAP goes from 3.5 to 1.8 times an original voice. With RATE, these models are really computed at the lower rate, which lightens them further" },
    { en: "Tested on a Model:Cycles (the 48 kHz models; the lo-fi could only be reached from 1.54 on), and checked in the emulator: MACRO gives exactly the samples of the original code rendered this way, alone, with Model-TG, with the Syntakt engines and with the other mods. The other 34 models sound exactly as before" },
  ] },
  { version: "1.45", date: "2026-10-11", changes: [
    { en: "New mod, Per-track filter: hold MACHINES and turn SWEEP for a filter on the track, low-pass to the left, off in the centre, high-pass to the right, like a DJ mixer, with the Model:Samples' range (5 Hz to 20 kHz). CONTOUR sets the resonance, COLOR and SHAPE a filter envelope (amount up or down, decay) restarted by each note" },
    { en: "Four real parameters on every machine, Syntakt engines included: p-locks, LFO and velocity, MIDI CC 74 and 71, saved with the sound and the pattern. At OFF the track is exactly as before, and old projects open with the filter OFF" },
    { en: "Tested on a Model:Cycles, and checked in the emulator on the OS's own code. It can't be ticked together with Model-TG for now, as both use MACHINES + SWEEP / CONTOUR: Model-TG's filter will make way for this one. It goes with every other mod" },
  ] },
  { version: "1.41", date: "2026-10-11", changes: [
    { en: "Two new MIDI mods by AveyCole, under USB & MIDI. With THR selected (SETTINGS, CONFIG › MIDI › PORTS › OUT/THRU), the Model:Cycles forwards what arrives on its MIDI IN and also sends its own clock, notes and parameter changes. MIDI OUT while in THRU does it all the time; Live MIDI OUT + THRU toggle switches it on and off with FUNC + a press on the LEVEL/DATA knob, the screen staying on THR" },
    { en: "Pick one of the two; each goes with every other mod. The original OUT/THR menu doesn't change, and OUT works as before. Best when only the Cycles or only the device on its MIDI IN plays notes: the Cycles passes on what it receives as it comes in, so notes sent by both can get mixed up (see the guide)" },
    { en: "Tested on a Model:Cycles by AveyCole, and checked here in the emulator on the OS's own MIDI code, alone and with the other mods" },
  ] },
  { version: "1.40", date: "2026-10-10", changes: [
    { en: "New mod by Nico Heuser, Chord Keys: on a CHORD track, the sixteen lower TRIG buttons play the chords of a scale. 1–7 play degrees I to VII, 8–14 the same one octave higher, 15–16 I and II two octaves higher. T1–T6 keep their usual controls" },
    { en: "FUNC + RETRIG gains Keys, Root, Scale (seven modes) and a triad, 7th, 9th, 11th or 13th for each degree, saved per track and pattern. SHAPE picks the voicing (BASE, close or open positions) and COLOR the balance of the voices. Four voices maximum; 9ths, 11ths and 13ths omit the fifth" },
    { en: "Checked in emulation on the OS's own code. Tested on a Model:Cycles, alone and with other mods, including the fix for a note that could stay stuck (TRIG let go while PATTERN was held). Cannot be combined with Model-TG" },
  ] },
  { version: "1.38", date: "2026-10-10", changes: [
    { en: "New mod by djd_oz, Volume and pan as numbers: on the main screen, turning LEVEL/DATA shows the selected track's volume (0 to 127) in small digits in place of the loudspeaker; with FUNC held, its pan (-64 to 63) in place of the “R” of the pan bar. The number goes away 3 to 4 seconds after you stop turning. On the main screen, LEVEL/DATA now moves in steps of 1 instead of 2, so the number goes through every value" },
    { en: "New mod by djd_oz, Dimmed trigless trigs: a trig key that holds a trigless trig (FUNC + trig key) lights dimmed instead of at full brightness, so you can tell it from a note trig. It keeps its usual blink. The key is lit for one millisecond out of every three, 333 times a second, so it looks steady" },
    { en: "Both are rewritten for the flasher so that they go with every other mod, Model-TG and the Syntakt engines included. Tested on a Model:Cycles, together with Model-TG, the 5 Syntakt engines, 6-channel audio, trig removal, the arpeggiator, 546 BPM and the startup animation (even with all 16 trig keys holding trigless trigs), and checked in the emulator on the OS's own code" },
  ] },
  { version: "1.37", date: "2026-10-10", changes: [
    { en: "New mod, Multi-line browser: the preset browser shows three names at once in a small font, instead of one in big letters. A > marks the name under the cursor, the sound loaded on the track stays highlighted, and folders get a small mark before their name. From an idea and a script by a community member" },
    { en: "It works for sounds, folders and the Model-TG Sampler's samples. With Scrolling names or Model-TG, only the name under the cursor scrolls; the others stay put" },
    { en: "Tested on a Model:Cycles, and checked in the emulator on the OS's own drawing code and fonts. It goes with every other mod, Model-TG and the Syntakt engines included" },
  ] },
  { version: "1.36", date: "2026-10-10", changes: [
    { en: "MACRO and the Syntakt engines together: the flasher now lets you tick both cards. MACRO comes last, right after the engines you tick (after the Sampler and the engines with Model-TG: with all five engines, MACRO is the 13th machine)" },
    { en: "In this combination, the engines' load governor looks after MACRO tracks too. To fit in the firmware, the added code is stored compressed and unpacked when the machine starts" },
    { en: "Tested on a Model:Cycles with Model-TG and all five engines (with 6-channel audio, sample preview, trig removal, the arpeggiator, the tempo and the startup animation); the first test file froze at startup, which is fixed. Other combinations are checked in the emulator only (the engines and MACRO play exactly as each one alone, alone and with Model-TG). MACRO alone and the engines alone are unchanged" },
  ] },
  { version: "1.33", date: "2026-10-10", changes: [
    { en: "Every mod you tick is now checked against its reference build, whatever the combination. Until now the page carried the expected result of each of the 10,559 possible combinations and checked only those; that list doubled with every new mod. It now keeps one reference per mod, plus a sample of 464 combinations checked whole (each mod alone, every pair, the largest ones)" },
    { en: "The page is lighter (about 1.3 MB less to load) and ready for many more mods. Nothing changes on the machine: for the same choice of mods, the firmware built and sent is exactly the same as before, as checked by rebuilding and comparing every combination of the previous version" },
  ] },
  { version: "1.32", date: "2026-10-07", changes: [
    { en: "New mod, Sample preview (with Model-TG): on a Sampler track, press FUNC + MACHINES (preset menu) and move the cursor onto a sample: the track's pad (or its trig keys in keyboard mode) plays it, the way the original OS lets you hear a preset before you pick it. Nothing plays while you scroll. It has its own row in the flasher, under Screen & browsing; ticking it ticks Model-TG too" },
    { en: "A sample that isn't in memory yet loads on the first press (a short wait), into free memory or in place of samples your project doesn't use; the next presses usually play at once. If there isn't enough free memory (a preview keeps room for recording and never removes a sample your project uses), or while Model-TG is resampling, the press plays nothing" },
    { en: "The track keeps its own sample: its trigs still play it, and so does its pad once you leave the menu. Sampler presets that remember their sample should also play that sample instead of the track's" },
    { en: "Tested on a Model:Cycles, alone with Model-TG and with the other mods, and checked in the emulator on the OS's and Model-TG's own code, from the preset menu to the Sampler's voice; with the new MACRO machine, it is checked in the emulator only. Without it, Model-TG firmwares stay exactly the same" },
  ] },
  { version: "1.31", date: "2026-10-07", changes: [
    { en: "New mod, MACRO machine: one extra machine with the 47 synthesis models of Braids, Émilie Gillet's open-source macro-oscillator, compiled from her own code (MIT license). SHAPE picks the model (0 to 46), COLOR and SWEEP shape it, CONTOUR lets the amp envelope open the timbre; DECAY, GATE and PUNCH work as on Tone" },
    { en: "MACRO is the 7th machine, or the 8th with Model-TG. Tested on a Model:Cycles, and checked in the emulator: all 47 models give exactly the samples of the original code" },
    { en: "A MACRO voice computes about twice as much as an original voice (less for the noises, up to 3.5 times for the wave maps), and there is no load governor yet: several MACRO tracks playing at once can make the sound crackle, so start with one or two. It goes with every mod except the Syntakt engines" },
  ] },
  { version: "1.28", date: "2026-10-07", changes: [
    { en: "A tidier list of mods in the flasher: they are sorted into sections (Packs, Sounds & machines, Sequencer, Live playing, Screen & browsing, USB & MIDI), with one short line each. The buttons at the top jump to a section and light up when it holds a ticked mod; a section folds away with a click on its title" },
    { en: "Details opens the full description of a mod, how it was tested and its guide link. A Your selection bar stays at the bottom of the screen with the ticked mods, the experimental ones, an × to untick each and a button to step 2. When two mods can't go together, the row says so before you tick, and Undo puts things back" },
    { en: "Display only: for the same choice of mods, the firmware built and sent is exactly the same as before (checked on every combination)" },
  ] },
  { version: "1.22", date: "2026-10-07", changes: [
    { en: "Samples OS tab, the other way round (experimental): a Model:Samples can now start as a Model:Cycles. Choose “Model:Samples → Cycles OS”: the page puts the official Model:Cycles OS inside your Model:Samples firmware, whose startup menu, updater and signature stay in place, and sends it over USB" },
    { en: "The way back works over USB too, no MIDI interface needed: “Model:Samples: back to its OS” sends the official Model:Samples OS, unchanged. The Model:Cycles OS put on by the page checks updates with the Model:Samples signature (a 32-byte change); an unmodified one would refuse it, which is why going back used to need the MIDI IN" },
    { en: "Checked in the emulator on the update checks of both OSes and on the Model:Samples startup code that loads the new OS (way there, way back, and the firmwares they must refuse); not yet tried on a real Model:Samples. The existing choice, the Samples OS on a Model:Cycles, is unchanged" },
  ] },
  { version: "1.21", date: "2026-10-05", changes: [
    { en: "New mod, Startup animation: when the Model:Cycles starts, the four rounded squares of the modded-cycles logo pop in one by one, the top right one hollows out, then “modded-cycles” types itself underneath, instead of the original tile animation" },
    { en: "It lasts as long as the original animation, so startup is not slower. Tested on a Model:Cycles, and checked in the emulator on the OS's own screen code, image by image. It goes with every other mod" },
  ] },
  { version: "1.20", date: "2026-10-05", changes: [
    { en: "Clearer Model-TG card: Model-TG already holds drumkilla's three tweaks (latching mute, trig preview, scrolling names), so ticking it now shows them ticked and locked, “included with Model-TG”, instead of unticking them. Unticking Model-TG frees them again" },
    { en: "Display only: for the same choice of mods, the firmware built and sent is exactly the same as before" },
  ] },
  { version: "1.19", date: "2026-10-04", changes: [
    { en: "New mod, Tempo up to 546 BPM: the TEMPO knob, tap tempo, incoming MIDI clock and saved projects go beyond 300, up to 546.0 BPM. 546 is the ceiling of the project format (the tempo is saved in 1/120 of a BPM on 16 bits); the sequencer itself would keep up far beyond" },
    { en: "It also fixes the original OS's tempo-synced LFO, which left its cycle above 351.6 BPM at its highest speed and multiplier. Above 300 BPM, the processor may struggle to keep up with busy patterns: push it knowingly. A project saved above 300 BPM reopens at 120 BPM on the original OS" },
    { en: "Tested on a Model:Cycles, and checked in the emulator on the OS's own code (knob, tap tempo, MIDI clock, project loading, LFOs). It goes with every other mod" },
  ] },
  { version: "1.18", date: "2026-10-04", changes: [
    { en: "Fast flashing over USB: about 30 seconds instead of 5 to 10 minutes. The flasher now speaks the update protocol of Elektron Transfer (worked out by Elektroid): the Model:Cycles stays on its usual screen, checks every block as it arrives, then asks you to confirm the update" },
    { en: "Before sending, the page asks the machine who it is and shows its OS version; it refuses to send a Model:Cycles firmware to a machine that answers as a Model:Samples (Samples OS, or Model-TG with Transfer on SMP). After the update, it follows the restart and reads the new version" },
    { en: "The classic method (CONFIG › UPGRADE) stays one click away, as the fallback. A Download button in step 4 gives the prepared .syx, to drop onto Elektron Transfer if you prefer" },
    { en: "Tested on a real Model:Cycles: 33 seconds for the transfer, then YES on the machine, which installs the firmware and restarts. Every byte the page sends also matches Elektroid's code" },
  ] },
  { version: "1.17", date: "2026-10-04", changes: [
    { en: "Syntakt engines, fewer cut notes: the load governor no longer reacts to a single heavy block (a busy step, or the screen redrawing), which is already over when it is measured; only load that lasts two blocks, or a sustained load, fades a voice out" },
    { en: "When a voice must go, it is the one heard least in the mix (its level times its mixer volume and sends; a muted track goes first), the oldest note on a tie; it used to be the quietest voice before the mixer, so often the same track" },
    { en: "The sustained-load rule (fade a voice out when the load stays above 86 % for a fraction of a second, so the screen and knobs keep enough time) never actually ran: its slow average could not rise, a rounding issue. It now works, without a chain of cuts: it also looks at the recent load and counts the voices it has just stopped" },
    { en: "Lighter on the processor, same sound: the per-voice bookkeeping of the governor with Model-TG, and the original OS's scaling of each track (6-channel audio, Model-TG and the Syntakt engines)" },
    { en: "Checked in the emulator: same sound and same voice stops as before at normal load, then the new rules under overload" },
  ] },
  { version: "1.16", date: "2026-10-04", changes: [
    { en: "USB audio: no more dropouts when the processor load changes (Model-TG, muted tracks, effects turning off). The stock OS sends each block to the computer right after computing it, so the moment moved with the load, and the 6-channel mod's buffer only tolerated 0.2 ms of it; each block now leaves at the start of the next one, always at the same moment (0.67 ms more latency), and the 6-channel buffer gains a slot" },
    { en: "6-channel audio with Model-TG: a muted track's stem is no longer cut off (its note rings out, as without Model-TG) and no longer restarts frozen when unmuted" },
    { en: "6-channel audio: the copy of the six tracks to USB is lighter on the processor (same bytes)" },
    { en: "Checked in the emulator, with the original OS's USB driver, and tested on a real Model:Cycles" },
  ] },
  { version: "1.15", date: "2026-10-04", changes: [
    { en: "Trig preview, fix: it also works with the sequencer paused. A MIDI Stop (from the computer on USB, for instance when the DAW stops) pauses the sequencer even when stopped, and PAGE then turned the page instead of playing the step, until a restart" },
    { en: "The same fix inside Model-TG, which includes the trig preview. Tested on a real Model:Cycles" },
  ] },
  { version: "1.14", date: "2026-10-04", changes: [
    { en: "Arpeggiator, fix: in live recording, the notes the arpeggiator plays are recorded one by one, each on its step with its length; the pattern only kept one of the notes, repeated (the retrig of the last key pressed)" },
    { en: "A single held note on 1 octave is still recorded as one trig with retrig, as with the original retrig. Tested on a real Model:Cycles" },
    { en: "Guide: live recording, in the Arpeggiator section" },
  ] },
  { version: "1.13", date: "2026-10-03", changes: [
    { en: "New: easier trig removal. On the stock OS, a press on a trig longer than 0.2 s counts as a hold and the trig stays, so the soft keys often needed a second press; with this mod, letting go within half a second removes it" },
    { en: "Tested on a real Model:Cycles, with Model-TG, the 5 Syntakt engines, 6-channel audio and the arpeggiator" },
    { en: "Guide: a Removing trigs section, with a key to try the delay" },
  ] },
  { version: "1.12", date: "2026-10-03", changes: [
    { en: "New: an arpeggiator in place of the retrig. Hold several notes with RETRIG (or A.On) and they play one after another; FUNC + RETRIG gains Arp (direction) and Oct (1 to 4 octaves), saved with the pattern" },
    { en: "Tested on a real Model:Cycles: the arpeggiator, and Model-TG 1.1 with the 5 Syntakt engines and 6-channel audio" },
    { en: "Model-TG: in mute mode (held or latched), each track key mutes at once, as with the latching mute alone; Model-TG queued them until you left the mode" },
    { en: "Guide: an Arpeggiator section" },
  ] },
  { version: "1.11", date: "2026-10-03", changes: [
    { en: "Model-TG updated to its version 1.1: slide trigs (hold SETTINGS and press a trig key) glide the parameters from one trig to the next, on every machine, the Syntakt engines included" },
    { en: "Model-TG 1.1 with the 5 Syntakt engines worked on a real Model:Cycles; its choices stay marked experimental until a firmware built by this page is tried" },
    { en: "Guide: how to use slide trigs, in the Model-TG section" },
  ] },
  { version: "1.10", date: "2026-10-03", changes: [
    { en: "Guide: a Model-TG section (loading samples, playback modes, Attack and Filter, shortcuts)" },
  ] },
  { version: "1.9", date: "2026-10-02", changes: [
    { en: "Model-TG with the 5 Syntakt engines is now tested on a real Model:Cycles" },
  ] },
  { version: "1.8", date: "2026-10-02", changes: [
    { en: "MACHINES screen: with more than 7 machines, the position dots go on two rows instead of running over the machine picture" },
  ] },
  { version: "1.8", date: "2026-10-02", changes: [
    { en: "Syntakt engines: the flasher takes Syntakt OS 1.42, the version now on elektron.se (1.41 still works: same engines, same firmware)" },
  ] },
  { version: "1.7", date: "2026-10-02", changes: [
    { en: "Model-TG with the Syntakt engines: a little lighter on the CPU (our busiest code in the fast internal memory, silent tails of the original machines stopped sooner under heavy load)" },
  ] },
  { version: "1.6", date: "2026-10-01", changes: [
    { en: "Model-TG together with the Syntakt engines: the Sampler stays the 7th machine, the engines follow it (checked in the emulator)" },
  ] },
  { version: "1.5", date: "2026-10-01", changes: [
    { en: "Model-TG by TinyGregAudio: a Sampler machine, resampling, retrig and master FX (on its own for now)" },
  ] },
  { version: "1.4", date: "2026-10-01", changes: [
    { en: "Fewer cut notes when Syntakt voices play together: only sustained load or a really long block cuts a voice" },
  ] },
  { version: "1.3", date: "2026-10-01", changes: [
    { en: "Syntakt voices keep their state in the fast internal memory too" },
  ] },
  { version: "1.2", date: "2026-10-01", changes: [
    { en: "Syntakt engines even lighter: their code now runs from the fast internal memory" },
  ] },
  { version: "1.1", date: "2026-10-01", changes: [
    { en: "Syntakt engines lighter on the CPU: their work buffers now use the fast internal memory" },
  ] },
  { version: "1.0", date: "2026-10-01", changes: [] },
];
