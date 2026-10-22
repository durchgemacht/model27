# 64 — Projects and machines: what to know (draft for the guide)

**Status: draft, 2026-10-22, written for users; not on the site yet.** The maintainer asked for one place that says how
projects and sounds behave when the machines of a build change, the happy accidents included, so that it can go into
the guide later. Each point says what happens, why it is not a fault, and what to do; the sources are the notes.
Points from code reading are marked as such: they have not been tried on the device.

## In short

- **To keep the same sounds after a new build, keep one project per build on the device.** Save it under a name that
  says which build it belongs to.
- Today model27 offers one machine card, SAMPLE, which always sits in slot 6: points 1 and 3 matter once a second
  machine card is offered.

## 1. A track remembers a machine slot, not a machine

- The Model:Cycles stores each track's machine as a number, a slot. The added machines take slots 6, 7, … in the order
  of the cards ticked for that build.
- Flash a build with other machines ticked, and a track saved on slot 7 plays whatever machine is in slot 7 now, with
  the same knob values. That is a happy accident, not a fault: the sound is still there, played by another machine.
- To get the original sound back, flash the build with the same machines ticked again, or keep one project per build.
- Source: [notes/62](62-level-b4-stable-machine-ids.md) §1 and §9.

## 2. A machine that is not in the build

- A track whose slot is not in the current model27 build plays CHORD, and the MACHINES page shows "Error".
- Nothing breaks in a model27 build: the registrar gives that slot KICK's knobs and record, so the OS never reads past
  its tables. Ticking that machine again brings the sound back.
- Source: notes/62 §1.2 and §9 (code reading).

## 3. Shortcut values stay with the track (planned)

- Machines will be able to offer up to four extra values on RETRIG + COLOR, SHAPE, SWEEP or CONTOUR. When a track
  changes machine, these values stay, and the new machine reads them its own way: another happy accident.
- These values cannot be p-locked or used as LFO destinations, for now. Holding a trig or LFO keeps the knob on its
  usual parameter.
- Status: planned in [notes/63](63-level-b4-shortcuts-dispatchers.md) (§9), not built yet.

## 4. Back on the official OS

- A project made with added machines plays CHORD on those tracks on the official OS, and the MACHINES page shows
  "Error": the voice loop and the page check the slot. Whether every screen copes with such a track there, turning
  its knobs for one, has not been checked, since the official OS has no registrar to catch it.
- The official OS does not keep the extra settings of added machines, such as SAMPLE's sample choice and, later,
  shortcut values.
  - Loaded there, a sound comes without them, and saving the sound or the project erases them for good: the official
    save keeps only the stock parameters.
  - Do not save a model27 project on the official OS, or keep a copy of it first.
- Source: [notes/47](47-filtre-piste.md) §4.1: the save clears the record's 32 slots and writes the stock parameters
  only, and the load clears the sound's parameters and reads slots 0 to 23 back. Code reading, not tried on the
  device.

## 5. For the guide, later

- A short section, "Projects and machines", near the SAMPLE section, in English and French, as every page of the site.
- In musicians' words, without addresses: the four points above and the advice in short.
- Points 1 and 3 belong there once a second machine card and the shortcuts exist; points 2 and 4 already hold for
  SAMPLE.
