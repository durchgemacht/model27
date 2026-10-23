# model27

**The Model:Cycles with added machines you can combine freely, built in your browser from your own copy of the
official OS.**

- **Machines combine freely.** Up to six added machines for now, a limit that will be raised soon, in any
  combination, put together when you build. Nothing is pre-built, and no machine rules out another.
- **What goes together is checked.** Every mod declares what it touches; the builder checks each build and stops one
  that would write the same bytes or use the same memory, instead of making a firmware.
- **It still plays like a Model:Cycles.** Extra values sit on one fixed set of shortcuts, RETRIG + a knob, the same on
  every machine and saved with the sound.
- **Tested means played on a real Model:Cycles.** Before a mod reaches the flasher, it runs in an emulator on the
  Model:Cycles' own code. Its card says Experimental until it has been played on the device, and Tested after.
- **Your files stay yours.** The firmware is built in your browser from your own official OS file, nothing is
  uploaded, and only the main OS is changed, so you can always go back to the official firmware.
- **Easy to write for.** A machine is one package, its code and a manifest; the builder gives it its slot, its memory
  and its place in the OS. Two reference machines in the repository show how, by hand or with an AI.

model27 is a downstream fork of [Modded-Cycles](https://github.com/18nelli18/Modded-Cycles), started from its
release 1.55, the last one with a mod picker, plus the Control All Config mod. It keeps the picker: you tick what
you want, the page builds the firmware from **your own copy** of the official OS in your browser and sends it to the
Model:Cycles over USB. Modded-Cycles has since moved to a single OS with 2.0; model27 works on how mods are put
together, so that a new machine fits next to the others. The rules a mod follows for that are the
**[Cycles Mod Standard](https://github.com/durchgemacht/cycles-mod-standard)** (draft 0.4), written alongside.

**Status: beta, release 0.4.** The [web flasher](https://durchgemacht.github.io/model27/flasher/) offers two cards,
both tested on a Model:Cycles as the page builds them: the **SAMPLE** machine of
[Cycles One-Shot](https://github.com/durchgemacht/cycles-one-shot), a one-shot sampler for samples on the +Drive,
and [Control All Config](https://github.com/durchgemacht/cycles-control-all-config). The
[guide](https://durchgemacht.github.io/model27/guide/) explains them. Combining machines is proven with two internal
reference machines: SAMPLE with the first one on a Model:Cycles; the second one, with a shortcut, and sharing the
main screen, the knob view, the screen's tick and the browser with SAMPLE, in emulation so far, composed by the page
as by the command line. The next machine card is the first that users will combine. The other Modded-Cycles 1.55
mods stay buildable from the command line.

> [!IMPORTANT]
> **No Elektron firmware is included in this repository**, original or modified. You bring the official OS
> file from [elektron.se](https://www.elektron.se/support-downloads/modelcycles); the mods are applied to it on your
> computer. This is an independent project, not affiliated with or endorsed by Elektron. model27 is its own fork, so
> please bring questions and bug reports about it to this repository rather than to the Modded-Cycles maintainers.
> Flashing a modified OS is **at your own risk** and may void your warranty.

## Stability first: Gen 1 machines

model27 is curated: each mod is chosen with care and made to work reliably alongside the others. Making machines
work together takes a few ground rules. Some of them will probably loosen over time, but for now they define which
machines get in. These are **Gen 1 machines**, as the
[Cycles Mod Standard](https://github.com/durchgemacht/cycles-mod-standard) describes them today:

- four knobs of their own, with DECAY, GATE and PUNCH working as on the stock machines;
- up to four extra parameters, all on the same fixed shortcuts (RETRIG held + COLOR, SHAPE, SWEEP or CONTOUR),
  identical on every machine and saved with the sound;
- they only hook into the parts of the OS the builder already knows how to share.

The result still plays like a Model:Cycles. This is all at an early stage, and it will keep evolving. If more
shortcuts are added one day, machines could get a few more controls, and those might become Gen 2. Whatever comes
next, the focus stays the same: stability, and staying true to the Elektron spirit.

## What gets easier

In Modded-Cycles 1.55, an added machine is a tweak whose place in the OS is fixed when it is generated, so two
machines go together only as a combination built in advance. In model27 a machine is a **package**, its code plus a
manifest that says what it touches, and the builder composes the packages you tick each time it builds.

| | One tweak per combination (Modded-Cycles 1.55) | One package per machine (model27) |
|---|---|---|
| **Machines ticked together** | only the combinations built in advance: 283 tweak files at the fork, 252 of them combinations of the Syntakt engines | any combination, up to six for now (to be raised soon) next to the six original machines |
| **A new machine** | a new file for every combination with the machines already there | one package; the others stay as they are |
| **Its slot, its place in memory, its registration in the OS** | fixed by its own generator | assigned by the builder at each build |
| **Extra controls** | each machine picks its own key combinations | a fixed list of shortcuts, handled by the builder |

## Shortcuts are predefined

A machine does not choose its own key combinations. model27 gives a fixed list, today **RETRIG held + COLOR, SHAPE,
SWEEP or CONTOUR**: up to four extra values on the machine's tracks. The machine declares each one's name, range
and default in its manifest; the builder handles the keys, shows the value and saves it with the sound, and the
machine only reads it. Each machine gives a shortcut its own meaning, so two machines can use the same one without
meeting. The list will probably grow, most likely by FUNC + the same four knobs. For now shortcut values cannot be
p-locked or used as LFO destinations, and no card on the page uses a shortcut yet.

## The conditions, roughly

- **The machine is a package** that follows the standard. The machines Modded-Cycles ships pre-built (MACRO, ACID,
  the Syntakt engines, Model-TG's Sampler) are not packages and do not go with the packages.
- **Where two machines use the same place in the OS**, such as the main screen or the knob view, the builder adds a
  small dispatcher that passes it on to the right machine. Where no dispatcher exists yet, the build stops with a
  message instead of making a firmware.
- **Two machines never share memory.** A machine that needs RAM of its own, as SAMPLE does for its samples, claims it
  in its manifest; a build where two claims overlap stops with a message.
- **Other mods go with the machines** unless they write the same bytes or use the same memory. The builder computes
  that from the manifests and the mods themselves.
- **The processor is shared and not measured by the builder.** How many heavy machines run on six tracks at once is
  a matter of listening.
- **One project per build.** A track remembers a machine's slot, not the machine itself, and the added machines take
  their slots in the order they are ticked. For easy, hassle-free experimenting with different combinations, make a
  separate project on the Model:Cycles for each build ([notes/64](notes/64-projects-and-machines.md)).

## What goes in first

- The maintainer's own mods: the **SAMPLE** machine of [Cycles One-Shot](https://github.com/durchgemacht/cycles-one-shot)
  (a one-shot sampler for samples on the +Drive) and
  [Control All Config](https://github.com/durchgemacht/cycles-control-all-config), which is already here.
- Then mods by other authors, with their agreement and full credit. If you have built a machine for the Cycles, or
  would like to, the standard's
  [porting guide](https://github.com/durchgemacht/cycles-mod-standard/blob/main/APPLYING.md#12-porting-a-machine-to-model27s-builder)
  and the two reference machines in this repository show the way.
- Everything else that Modded-Cycles 1.55 ships stays buildable from the command line until it is decided, mod by
  mod, what the beta offers. Modded-Cycles' startup animation, which shows the Modded-Cycles name and logo, is that
  project's own branding and will not be offered here.

## Install from the browser

1. **Open the [web flasher](https://durchgemacht.github.io/model27/flasher/)** in Chrome, Edge or Opera on a desktop computer (it needs Web MIDI).
2. **Tick SAMPLE.**
3. **Drop your official OS file**, `model-cycles_OS1.13.syx`, from the
   [Elektron download](https://www.elektron.se/support-downloads/modelcycles) (unzip it first).
4. **Connect the Model:Cycles over USB and press Flash.** Close Elektron Transfer first and leave the machine on its
   usual screen. The transfer takes about 30 seconds, then the Model:Cycles asks you to confirm with **YES**.

Everything runs in your browser: your files are never uploaded anywhere. **Before you flash**, back up your projects
and samples with Elektron Transfer.

## Building from the command line

The build is Modded-Cycles' pure-Python toolchain: no compiler and no firmware in the repository.

```sh
python3 tools/build.py --list                       # every mod the repository holds today
python3 tools/build.py -i model-cycles_OS1.13.syx -t control-all-config,latching-mute,trig-preview
./flash.sh                                           # macOS / Linux  (flash.bat on Windows)
```

Details in [`BUILD.md`](BUILD.md) and [`FLASH.md`](FLASH.md) (both in French, inherited from Modded-Cycles).

<details>
<summary><b>Going back to the official firmware</b></summary>

Build nothing: send your official OS file the way you installed it. Before that, set any track that uses an added
machine (MACRO, ACID, a Syntakt engine, SAMPLE or the Model-TG Sampler) back to one of the six original machines:
a project that still names a machine the official OS does not have can freeze its MACHINES page.

</details>

<details>
<summary><b>If something goes wrong</b></summary>

If a Model:Cycles ever fails to start, it can always be recovered from its startup menu (`FUNC` + power on, then
`TRIG 4`). That menu only listens to the **MIDI IN** port, so you need a USB-MIDI interface and the scripts described
in [`FLASH.md`](FLASH.md). Only the MAIN OS section of the firmware is ever changed; the bootloader and the updater
stay as Elektron shipped them.

</details>

## How it is made

Every mod is checked in an emulator that runs the Model:Cycles' own code, then on a real Model:Cycles before it is
marked *Tested*. The tools, the emulation proofs and the technical notes are Modded-Cycles' (the
[notes](notes/README.md) are in French); model27 adds its own notes in English as it goes. Much of model27's code
and documentation is written together with Claude, an AI.

## Credits

model27 is Modded-Cycles' work with a different aim. Everything here starts from:

- **[18nelli18/Modded-Cycles](https://github.com/18nelli18/Modded-Cycles)** (MIT), by 18nelli18 and its contributors:
  the tools, the generators, the emulation, the web flasher, the notes and the mods. Thanks also to the testers and
  bug reporters credited in its release notes.

And, through Modded-Cycles, on:

- **[mischa85/elektron-firmware-tool](https://github.com/mischa85/elektron-firmware-tool)** (MIT): the firmware container format and its signature, on which `mtlib` is based.
- **[drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks)** (MIT): latching mute, trig preview, scrolling names, and the `mtlib` toolkit and tweak format used by the build.
- **[scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output)** (MIT): the original 6-channel USB mod.
- **[dagargo/elektroid](https://github.com/dagargo/elektroid)** (GPL-3.0): the Elektron Transfer update protocol behind fast USB flashing.
- **[Unicorn](https://www.unicorn-engine.org/)** (GPL-2.0): the CPU emulator every emulation proof runs on, imported and not included here.
- **[TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG)** (MIT): the Sampler machine and everything that comes with it ([license](tweaks/model-cycles_OS1.13/LICENSE-Model-TG)).
- **[pichenettes/eurorack](https://github.com/pichenettes/eurorack)** (MIT): Émilie Gillet's Braids code, compiled as is for the synthesis models of the MACRO machine ([license](tweaks/model-cycles_OS1.13/LICENSE-Braids)).
- **[RobinSchmidt/Open303](https://github.com/RobinSchmidt/Open303)** (MIT): Robin Schmidt's TB-303 model, rewritten in fixed point for the ACID machine ([license](tweaks/model-cycles_OS1.13/LICENSE-Open303)).
- **[mxldyn/octamax](https://github.com/mxldyn/octamax)** and **[bryantysinger/octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt)**: reverse-engineering and patching methods (ideas only, no code).

And the tools around it, none of whose code is in this repository:

- **[irpina/elekloader](https://github.com/irpina/elekloader)**: applies mods to Elektron firmware right in the browser.
- **[irpina/digiemu](https://github.com/irpina/digiemu)**: runs the Model:Cycles' own firmware on a computer, where mods can be tried before they reach a real one.
- **[m-dwyer/digikit](https://github.com/m-dwyer/digikit)**: the emulator digiemu grew from.

The authors of the individual mods are named in the mod table of the flasher, in
[`PROVENANCE.md`](tweaks/model-cycles_OS1.13/PROVENANCE.md) and in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## License

The code, tweak files, website and notes are under the [MIT License](LICENSE): Modded-Cycles' copyright for what
comes from there, model27's for its changes. Third-party code keeps its own license, see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). No Elektron firmware is included or licensed here; Elektron,
Model:Cycles, Model:Samples and Syntakt are trademarks of Elektron Music Machines MAV AB. To contribute, see
[CONTRIBUTING.md](CONTRIBUTING.md).
