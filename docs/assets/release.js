/* model27 versions, newest first. Shown on the home page and in the flasher.
 * New version: add an entry at the top, with what changed since the previous one:
 *   { version: "0.2", date: "2026-11-01", changes: [{ en: "…" }] }
 * English only (the site dropped French on 2026-10-31).
 * The entries from 1.56 down are Modded-Cycles' own releases, kept as they were: model27 starts from
 * release 1.55 (plus Control All Config, their 1.56), and those notes name the authors, testers and reporters
 * of everything model27 builds on.
 */
window.MC_RELEASES = [
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
