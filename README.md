# model27

**New machines, effects and workflow mods for the Model:Cycles. Focused on performance and stability.**

Tick what you want in the [web flasher](https://durchgemacht.github.io/model27/flasher/), drop your official OS file,
flash over USB. Every card goes with every other card, and the firmware is built in your browser from your own copy of
the official OS.

## Features

### Machines

- **SAMPLE**: plays samples from the +Drive, once or in a loop,
  forwards or backwards, through a DJ-style filter. The pad and the TRIG keys play the sample under the browser's
  cursor.
- **SOLID**: plays struck sounds: a string, drum skin, marimba, metal bar, bell or glass.
- **CHIPS**: plays chiptune: a square wave that arpeggiates a chord, with a pitch sweep and a bass. Based on
  [Plaits](https://github.com/pichenettes/eurorack) by Émilie Gillet.
- **MAXSAW**: plays a huge, wide sawtooth sound, with a sub two octaves down. Based on
  [Adam Szabo](https://www.adamszabo.com/internet/adam_szabo_how_to_emulate_the_super_saw.pdf)'s analysis of the
  supersaw.
- **TERRA**: plays wave terrain synthesis: a circle runs over one of eight surfaces, from soft tones to sharp ones.
  Based on [Plaits](https://github.com/pichenettes/eurorack) by Émilie Gillet.
- **VOSIM**: plays two vocal formants that start again on every period of the note, from soft vowels to buzzing
  tones. Based on [Braids](https://github.com/pichenettes/eurorack) by Émilie Gillet.

### Effects

- **Digital Delay**: a bright, clean delay, the opposite of the dark stock one: each repeat a little thinner. Based on
  [gialloinfuso's PPPCCC mods](https://github.com/gialloinfuso/PPPCCC-M-S-Mods).
- **POTS**: a lo-fi delay like an old phone line: each repeat darker, narrower and grainier.

Both take the delay slot, chosen per pattern with PATTERN + Delay Time.

### Track FX

One per sound, after Volume + Dist, on SWEEP, CONTOUR, COLOR and SHAPE (MIDI CC 74, 71, 75, 76).

- **LP/HP Filter**: a DJ-style filter: lowpass, off or highpass on one knob, with resonance.
- **Crush**: makes a track grainy and lo-fi: a lower sample rate and fewer bits.
- **Ring**: a ring modulator, from a fast chop to bell-like, metallic sounds.
- **Reso**: a tuned resonator: noise and hits ring at a pitch you set.
- **EQ**: a three-band EQ: a Mid band you can sweep, a Low and a High shelf, each up to 12 dB either way.

### Workflow

- **Perform Kit**: change patterns without changing the sound: the next pattern's trigs play on the sounds you have
  right now.
- **RESAMPLE**: records a track, the main mix or the USB input and saves it as a sample on the +Drive, ready for
  SAMPLE.
- **Control All Config**: choose which tracks Control All changes.
- **Trig Preview**: hear a step without starting the sequencer. By
  [drumkilla](https://github.com/drumkilla/elektron-model-tweaks).
- **CHORD Tables**: CHORD plays your own wavetables from the +Drive, one for each pattern.
- **CPU Page**: shows in SETTINGS how much of the Model:Cycles' processor the sound takes.
- **Transpose**: plays the TRIG keys in other octaves and makes a track jump a fourth or a fifth.
- **Trig Condition Order**: on CHANCE, the A:B conditions come before the percentages.

### In the browser

- **[Uploader](https://durchgemacht.github.io/model27/uploader/)**: puts audio files and whole folders on the +Drive
  over USB, as 48 kHz mono samples for SAMPLE. Works with the official OS too.
- **[Manager](https://durchgemacht.github.io/model27/manager/)**: keeps one project per firmware: backs up the
  project, flashes the other firmware and brings its project back, in one go over USB.
- **[Wavetables](https://durchgemacht.github.io/model27/wavetables/)**: makes a wavetable for CHORD from the waves of
  Plaits and Braids or your own WAV files, and builds it into the official OS 1.13 or a model27 build.

The [guide](https://durchgemacht.github.io/model27/guide/) explains every card. What changed in each release is in
[CHANGELOG.md](CHANGELOG.md).

> [!IMPORTANT]
> **No Elektron firmware is included in this repository**, original or modified. You bring the official OS
> file from [elektron.se](https://www.elektron.se/support-downloads/modelcycles); the mods are applied to it on your
> computer. This is an independent project, not affiliated with or endorsed by Elektron. model27 is its own fork, so
> please bring questions and bug reports about it to this repository rather than to the Modded-Cycles maintainers.
> Flashing a modified OS is **at your own risk** and may void your warranty.

## Install from the browser

1. **Open the [web flasher](https://durchgemacht.github.io/model27/flasher/)** in Chrome, Edge or Opera on a desktop
   computer (it needs Web MIDI).
2. **Tick the cards you want.**
3. **Drop your official OS file**, `model-cycles_OS1.13.syx`, from the
   [Elektron download](https://www.elektron.se/support-downloads/modelcycles) (unzip it first).
4. **Connect the Model:Cycles over USB and press Flash.** Close Elektron Transfer first and leave the machine on its
   usual screen. The transfer takes about 30 seconds, then the Model:Cycles asks you to confirm with **YES**.

Everything runs in your browser: your files are never uploaded anywhere. **Before you flash**, back up your projects
and samples with Elektron Transfer.

## Switching firmware

A project belongs to the firmware it was made on: on another firmware its tracks can play other machines, and saving
it there can lose what that firmware doesn't know. Save the project you work on before you flash, and after the flash
load a project made on the new firmware, or start a new one, before you play or save anything. The
[Manager](https://durchgemacht.github.io/model27/manager/) does this for you.

<details>
<summary><b>Going back to the official firmware</b></summary>

Build nothing: send your official OS file the way you installed it. Before that, set any track that uses an added
machine (MACRO, ACID, a Syntakt engine, SAMPLE, SOLID, CHIPS, MAXSAW, TERRA, VOSIM or the Model-TG Sampler) back to
one of the six original machines: a project that still names a machine the official OS does not have can freeze its
MACHINES page.

</details>

<details>
<summary><b>If something goes wrong</b></summary>

If a Model:Cycles ever fails to start, it can always be recovered from its startup menu (`FUNC` + power on, then
`TRIG 4`). That menu only listens to the **MIDI IN** port, so you need a USB-MIDI interface and the scripts described
in [`FLASH.md`](FLASH.md). Only the MAIN OS section of the firmware is ever changed; the bootloader and the updater
stay as Elektron shipped them.

</details>

## At a glance

| | |
|---|---|
| **Device** | Elektron Model:Cycles |
| **Needs** | the official OS 1.13 file from Elektron |
| **Install** | in the browser, Chrome, Edge or Opera on a desktop computer (Web MIDI), over USB |
| **Status** | beta, release 0.75 |
| **Price** | free |
| **License** | MIT |
| **Based on** | [Modded-Cycles](https://github.com/18nelli18/Modded-Cycles) 1.55 |
| **Links** | [flasher](https://durchgemacht.github.io/model27/flasher/), [guide](https://durchgemacht.github.io/model27/guide/), [changelog](CHANGELOG.md) |

## Building from the command line

The build is Modded-Cycles' pure-Python toolchain: no compiler and no firmware in the repository.

```sh
python3 tools/build.py --list                       # every mod the repository holds today
python3 tools/build.py -i model-cycles_OS1.13.syx -t control-all-config,latching-mute,trig-preview
./flash.sh                                           # macOS / Linux  (flash.bat on Windows)
```

Details in [`BUILD.md`](BUILD.md) and [`FLASH.md`](FLASH.md) (both in French, inherited from Modded-Cycles). The
other Modded-Cycles 1.55 mods stay buildable from the command line.

## Writing mods for model27

How machines are packaged, which shortcuts they get, what the builder checks and how mods by other authors get in:
[MAKING-MODS.md](MAKING-MODS.md).

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
Much of model27's code and documentation is written together with Claude, an AI.

## License

The code, tweak files, website and notes are under the [MIT License](LICENSE): Modded-Cycles' copyright for what
comes from there, model27's for its changes. Third-party code keeps its own license, see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). No Elektron firmware is included or licensed here; Elektron,
Model:Cycles, Model:Samples and Syntakt are trademarks of Elektron Music Machines MAV AB. To contribute, see
[CONTRIBUTING.md](CONTRIBUTING.md).
