# Making mods for model27

How model27 puts mods together, what a machine has to follow to get in, and what the builder checks. For what the
mods do on the Model:Cycles, see the [README](README.md) and the [guide](https://durchgemacht.github.io/model27/guide/).

The rules a mod follows are the **[Cycles Mod Standard](https://github.com/durchgemacht/cycles-mod-standard)**
(draft 0.5), written alongside model27. Its
[porting guide](https://github.com/durchgemacht/cycles-mod-standard/blob/main/APPLYING.md#12-porting-a-machine-to-model27s-builder)
and the two reference machines in this repository (`tools/machines/refmachine/`, `tools/machines/refmachine2/`) show
how to write one, by hand or with an AI. The terms for outside contributions are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Where model27 comes from

model27 is a downstream fork of [Modded-Cycles](https://github.com/18nelli18/Modded-Cycles), started from its
release 1.55, the last one with a mod picker, plus the Control All Config mod. It keeps the picker: you tick what
you want, the page builds the firmware from your own copy of the official OS in your browser and sends it to the
Model:Cycles over USB. Modded-Cycles has since moved to a single OS with 2.0; model27 works on how mods are put
together, so that a new machine fits next to the others.

## A machine is a package

In Modded-Cycles 1.55, an added machine is a tweak whose place in the OS is fixed when it is generated, so two
machines go together only as a combination built in advance. In model27 a machine is a **package**, its code plus a
manifest that says what it touches, and the builder composes the packages you tick each time it builds.

| | One tweak per combination (Modded-Cycles 1.55) | One package per machine (model27) |
|---|---|---|
| **Machines ticked together** | only the combinations built in advance: 283 tweak files at the fork, 252 of them combinations of the Syntakt engines | any combination, next to the six original machines |
| **A new machine** | a new file for every combination with the machines already there | one package; the others stay as they are |
| **Its slot, its place in memory, its registration in the OS** | fixed by its own generator | assigned by the builder at each build |
| **Extra controls** | each machine picks its own key combinations | a fixed list of shortcuts, handled by the builder |

## Gen 1 machines

model27 is curated: each mod is chosen with care and made to work reliably alongside the others. Making machines
work together takes a few ground rules. Some of them will probably loosen over time, but for now they define which
machines get in. These are **Gen 1 machines**, as the Cycles Mod Standard describes them today:

- four knobs of their own, with DECAY, GATE and PUNCH working as on the stock machines;
- up to two on/off switches (MACHINES held + PUNCH or GATE), identical on every machine and saved with the sound;
- they only hook into the parts of the OS the builder already knows how to share.

The result still plays like a Model:Cycles. This is all at an early stage, and it will keep evolving. If more
shortcuts are added one day, machines could get a few more controls, and those might become Gen 2. Whatever comes
next, the focus stays the same: stability, and staying true to the Elektron spirit.

## Shortcuts are predefined

A machine does not choose its own key combinations. model27 gives a fixed list, today **MACHINES held + PUNCH or
GATE**: up to two switches, on or off. A switch flips on the press, instead of PUNCH or GATE on that machine's tracks;
while MACHINES is held, PUNCH's and GATE's lights show the switches, and the machine shows them on the screen if it
wants. On such a machine's tracks MACHINES is a held key: a tap still opens the machine list, when you let go of it,
and holding it for a shortcut leaves the list closed. Each machine gives a shortcut its own meaning, so two machines
can use the same one without meeting. A switch can be locked on single steps: hold the steps' TRIG keys and MACHINES,
then press PUNCH or GATE. For now switches cannot be LFO destinations.

The held key says what a combination works on: **PATTERN** the pattern (PATTERN + Delay Time / Reverb Size chooses its
effects), **MACHINES** the track's machine (its switches above), **RETRIG** the track's filter or Track FX. No mod gets
a held key of its own ([notes/72](notes/72-track-filters.md)).

## What the builder checks

- **The machine is a package** that follows the standard. The machines Modded-Cycles ships pre-built (MACRO, ACID,
  the Syntakt engines, Model-TG's Sampler) are not packages and do not go with the packages.
- **Every mod declares what it touches**; the builder checks each build and stops one that would write the same
  bytes or use the same memory, instead of making a firmware.
- **Where two machines use the same place in the OS**, such as the main screen or the knob view, the builder adds a
  small dispatcher that passes it on to the right machine. Where no dispatcher exists yet, the build stops with a
  message instead of making a firmware.
- **Two machines never share memory.** A machine that needs RAM of its own, as SAMPLE does for its samples, claims it
  in its manifest; a build where two claims overlap stops with a message.
- **Other mods go with the machines** unless they write the same bytes or use the same memory. The builder computes
  that from the manifests and the mods themselves.
- **Only the main OS is changed**, so the official firmware can always be put back.

## A project for each set of machines

A track remembers a machine's slot, not the machine itself, and the added machines take their slots in the order of
the cards. With other machine cards ticked, a track plays whichever machine now has its slot, with the same knob
values; a slot no machine has plays CHORD. To keep your sounds as they are, keep projects on the Model:Cycles for each
set of machine cards, as many as you like. Effects, Track FX and the other mods can come and go in the same project:
an effect, a Track FX or a CHORD Tables wavetable keeps its number in every build, a build without it plays the stock
effect, no Track FX or CHORD's own wavetable, and the other mods keep nothing in the project
([notes/64](notes/64-projects-and-machines.md)).

## How mods get in

- The maintainer's own mods first, such as the **SAMPLE** machine of
  [Cycles One-Shot](https://github.com/durchgemacht/cycles-one-shot) and
  [Control All Config](https://github.com/durchgemacht/cycles-control-all-config).
- Then mods by other authors, with their agreement and full credit. If you have built a machine for the Cycles, or
  would like to, the standard's porting guide and the reference machines show the way.
- Everything else that Modded-Cycles 1.55 ships stays buildable from the command line until it is decided, mod by
  mod, what the beta offers. Modded-Cycles' startup animation, which shows the Modded-Cycles name and logo, is that
  project's own branding and will not be offered here.

## How it is made

Every mod is checked in an emulator that runs the Model:Cycles' own code, then played on a real Model:Cycles before it
reaches users. The tools, the emulation proofs and the technical notes are Modded-Cycles' (the
[notes](notes/README.md) are in French); model27 adds its own notes in English as it goes. The command-line build is
in [`BUILD.md`](BUILD.md) and [`FLASH.md`](FLASH.md). Much of model27's code and documentation is written together
with Claude, an AI.
