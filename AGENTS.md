# AGENTS.md — model27

Guidance for coding agents working on this repository. Read this file first, then the `AGENTS.md` of every folder
you touch:

| Folder | Read before you change |
|---|---|
| [`tools/AGENTS.md`](tools/AGENTS.md) | generators, the Python build, ColdFire code, emulation proofs |
| [`tweaks/AGENTS.md`](tweaks/AGENTS.md) | the tweak JSON files and `PROVENANCE.md` |
| [`docs/AGENTS.md`](docs/AGENTS.md) | the website, the web flasher, the guide, the release notes |
| [`notes/AGENTS.md`](notes/AGENTS.md) | the technical notes |

## What this project is

**model27** is a downstream fork of [Modded-Cycles](https://github.com/18nelli18/Modded-Cycles), started from its
release 1.55 (the last one with a mod picker) plus the Control All Config mod. It keeps the mod picker and aims at a
short, curated list of mods, four-knob machines and the
[Cycles Mod Standard](https://github.com/durchgemacht/cycles-mod-standard) (a companion draft, 0.2):
every mod declares what it touches, and what can be ticked together is computed from that. Everything below about the
build, the proofs and the licenses is inherited from Modded-Cycles and still applies.

Firmware mods for the **Elektron Model:Cycles, OS 1.13** (ColdFire MCF54415, big-endian m68k). A mod is a *tweak*: a
table of byte writes (`old` → `new`) applied to section 3 (the MAIN OS) of the user's **own** official `.syx`, plus,
for some mods, code compiled or assembled into free space. Users pick mods in a web flasher
(`docs/flasher/`, served by GitHub Pages at <https://durchgemacht.github.io/model27/>), which builds the firmware in
the browser and sends it over USB. A pure-Python toolchain (`tools/build.py`) does the same build on the command line.

**Always the Model:Cycles OS, whatever the machine** (decision of 10/10/2026, notes/57). The Mods tab also flashes a
Model:Samples, but what it installs is still the Model:Cycles OS with the mods (sampling comes from Model-TG): the machine
picker only changes the packing (official Model:Samples container and signature, the 32-byte key change of notes/41,
transport `0x0F` or `0x11`; `tools/mods_for_samples.py`, `MCBuilder.modsForSamples`). Build, prove and reference a mod
once, on the Model:Cycles OS; never add a mod built on the Samples OS.

Maintainer: durchgemacht. They test every firmware change on their own Model:Cycles. Upstream Modded-Cycles is
maintained by 18nelli18; model27 is not affiliated with it, and never speaks for it.

## Hard rules

1. **Never commit an Elektron firmware image**, original or modified, or anything extracted from one (no `.syx`,
   `.zip`, extracted sections, dumps, copied routines). `.gitignore` covers `firmware/`, `*.syx`, `*.zip`, `build/`,
   `vendor/`, `*.wav`. A tweak carries only its own writes and the short `old` bytes that check the user's file; code
   taken from the Syntakt OS is extracted **at build time** from the user's file (recipes and relocation tables only,
   see notes/17). Never write that a file holds "no Elektron bytes" when it carries `old` bytes.
2. **Build from the official image only**, never on top of a previous build. Every write carries its `old` bytes and
   the build refuses a mismatch. Stock hashes are in `tweaks/model-cycles_OS1.13/device.json`.
3. **Hardware testing is the maintainer's.** A new mod ships as `"status": "experimental"`. Only after the maintainer
   reports that it works on their Model:Cycles does it become `"tested"`, in a separate commit ("… tested on the
   Model:Cycles"). Never mark anything tested yourself, never claim a hardware result you did not get from them.
4. **One user-visible change, one commit series**, with its docs, guide, release notes and note. Commit only when the
   maintainer asks, never on your own. Every commit message ends with the trailer `Co-Authored-By: Claude` (the
   maintainer's choice for the mod repositories). The maintainer decides what lands, after testing on the hardware.
5. **Prove it in emulation first.** Every mod has a generator with `--check` and a proof under `tools/emu/` that runs
   the OS's own code (Unicorn), stock vs patched. Unproven code does not go in the flasher.
6. **Recovery must stay possible.** Only section 3 is touched; the bootloader and updater stay identical, so the
   STARTUP MENU (MIDI IN) can always bring back the official OS. The web flasher only offers tweaks that keep
   `CONFIG › UPGRADE` over USB working.
7. **Respect the licenses and credit authors.** The project is MIT (`LICENSE`); the scope and every third-party
   license are in `THIRD-PARTY-NOTICES.md`: drumkilla's tweaks and `tools/mtlib/` (MIT), elektron-firmware-tool by
   Marcel Bierling (MIT), Model-TG by TinyGregAudio (MIT, `LICENSE-Model-TG`), ms-multi-output by scottmetoyer (MIT,
   `LICENSE-ms-multi-output`), Braids by Émilie Gillet (MIT, `LICENSE-Braids`, compiled unchanged for MACRO), Open303
   by Robin Schmidt (MIT, `LICENSE-Open303`, the model rewritten for ACID), and `tools/webxfer_check.py`, transcribed
   from Elektroid (GPL-3.0-or-later). Never
   transcribe or closely paraphrase code whose license does not allow it into the repo (GPL code into MIT files, code
   with no license); check an upstream's license before porting from it, and keep its notice next to the copy. Record
   the origin and license of every tweak in `tweaks/model-cycles_OS1.13/PROVENANCE.md` (and outside code in
   `THIRD-PARTY-NOTICES.md`), set `credit` on its flasher card, and serve its MIT text with the page (`license` in
   `FEATURES`). Outside contributions are merged only under the terms of `CONTRIBUTING.md`: work sent privately needs
   its author's written OK.

## Languages

- **Talk to the maintainer in German.**
- **English** for everything new: notes, generators, tweak `name`/`description`, comments and docstrings, `README.md`,
  commit messages, the code of the web pages.
- **French** stays where Modded-Cycles wrote it (`notes/`, `BUILD.md`, `FLASH.md`, `dossier-technique.md`,
  `PROVENANCE.md`, the existing tweaks and tools) until a file is rewritten for another reason; do not translate
  files just to translate them.
- **Both, side by side**: everything users see on the site (flasher cards, guide, release notes, home page), as
  `en`/`fr` pairs or `data-l="en"`/`data-l="fr"` spans. Never add one language without the other.
- User-facing text speaks to musicians: what the mod does on the machine, which buttons to press, its limits. No
  addresses or jargon there; those belong in the notes.

## Repository map

```
tweaks/model-cycles_OS1.13/   tweak JSON files (generated), device.json, PROVENANCE.md
tools/build.py                Python build: applies tweaks, checks caves, repacks and re-signs (mtlib)
tools/gen_*.py                one generator per mod: writes its tweak JSON, --check verifies it is up to date
tools/machines/<mod>/         C and assembly sources compiled into the firmware
tools/machines/<id>/manifest.json   a machine as a package (Cycles Mod Standard, notes/59): sources, flags, patch points,
                              hooks; tools/compose.py composes the chosen packages into one tweak at build time
tools/compose.py              Level B: lays packages out, places their committed objects (relocate.py), registers them
                              together through the registrar runtime, computes the conflicts, builds the .syx with
                              python3 alone (notes/59, notes/60); --registrar b1 / --relocator ld keep the toolchain paths;
                              frame() per number of machines, fill() per build, web_package() for the web flasher (B3b)
tools/relocate.py             Level B, increment B2a: places a package's committed object (m68k ELF, only R_68K_32)
                              at its address without the toolchain; compose.py uses it by default (notes/60); layout()
                              once, apply() per build, bundle() for the web flasher (B3a, notes/61)
tools/machines/<id>/<id>.o    the package's committed object (ld -r of its sources), written and checked by its generator
tools/gen_registrar.py        Level B, increments B2b and B2c: assembles the boot stub (a template with the offsets of its
                              immediates) and the registrar runtime (registrar.S) once, and commits both (notes/60 §4, §5);
                              with --cycles, also the registrar's frame for 1 to 6 machines (B3b, notes/61 §3)
tools/machines/registrar/     registrar.S, the runtime: the detours of the added machines reading a parameter block the
                              composer fills per build; registrar.json, its committed code, entries and the stub template;
                              frame.json, what every build of n machines writes, filled per build by composer.js
tools/gen_parts.py            Level B, steps B4b and B4c: builds the builder's parts (tools/machines/<id>/part.json) into
                              their committed objects, --check compares (notes/63 §3 to §5)
tools/machines/shortcuts/     the shortcut layer, a part (notes/63 §3): RETRIG + COLOR / SHAPE / SWEEP / CONTOUR on an
                              added machine's tracks, saved with the sound; compose.py adds it only to the builds whose
                              machines declare a shortcut, and chains a package's record wrapper (SAMPLE's) behind it
tools/machines/dispatch/      the dispatchers, a part (notes/63 §4): a vtable entry or hook two packages take (the main
                              screen's and the knob view's draws, the screen's tick, the browser's open) goes to a
                              dispatcher that calls the right machine's method, or every machine's tick; compose.py adds
                              only the dispatchers a build needs
tools/machines/refmachine/    the reference machine: the smallest added machine, proves the composer, never offered
tools/machines/refmachine2/   the second reference machine (notes/63): grows into the template that uses every point a
                              machine may use (its shortcut, Octave on RETRIG + COLOR, since B4b; its main screen label
                              and knob view, since B4c; a tick that blinks the label's dot and a browser hook that shows
                              the opened file's name, since B4d; through the dispatchers next to SAMPLE); never offered
tools/emu/                    Unicorn emulation of the OS: test_<mod>.py proofs, mcengine.py, emac.py, syntakt.py
tools/gen_flasher_tweaks.py   FEATURES list -> docs/flasher/tweaks.js (generated); a machine card embeds its package and
                              the registrar's frame, composed in the page (notes/61)
tools/crossflash.py, tools/mods_for_samples.py   one OS in the other machine's container (notes/41, 57): Samples OS tab,
                              and the mods for a Model:Samples
tools/check_overlaps.py       no firmware needed: mods that can be ticked together never write the same bytes, except
                              the same whole write or a mod applied on top of another (`requires`) (notes/49)
tools/registry.py             no firmware needed: builds tweaks/model-cycles_OS1.13/REGISTRY.md from the tweaks, the
                              registry of free space (freed sprite masks, caves, payloads) and OS hooks (notes/52)
tools/ref_mainos.py           reference hashes in docs/flasher/app.js: each mod (REF_MODS) and a sample of combinations
                              (REF_MAINOS: each card alone, every pair, the largest ones)
tools/web*_check.*, webflash_smoke.*   checks of the web flasher against the Python build (node, jsdom)
docs/                         GitHub Pages site: index.html, flasher/, guide/, assets/release.js
notes/                        numbered technical notes (French), index in notes/README.md
BUILD.md, FLASH.md            command-line build and flashing (French)
README.md                     English overview for Model:Cycles owners (mod table)
LICENSE, THIRD-PARTY-NOTICES.md   MIT for the project; what it does not cover; every third-party license
CONTRIBUTING.md               terms for outside contributions
```

## Adding a feature for users (the usual PR)

Follow the shape of the last ones (tempo-max: commits `5997b4a`, `14fb9fa`, `6e592bc`; trig-hold, arp). In order:

1. **Investigate and write the note.** New file `notes/NN-<slug>.md` (next free number; 64 is the last) with the
   user's request and its source, the OS code involved (addresses, `[FAIT]`/`[HYP]`), the design, free space used and
   conflicts with other tweaks. Add a row to `notes/README.md`. See `notes/AGENTS.md`.
2. **Write the generator** `tools/gen_<mod>.py` (and sources under `tools/machines/<mod>/` if it has code). It reads
   the official `.syx`, checks the stock bytes, and writes `tweaks/model-cycles_OS1.13/NN-<id>.json`; `--check`
   compares with the committed file. See `tools/AGENTS.md` and `tweaks/AGENTS.md`.
3. **Prove it**: `tools/emu/test_<mod>.py`, stock vs patched, on the OS's own code, alone and with the other mods
   (`--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,… --syntakt Syntakt_OS1.42.syx`).
   `tools/check_overlaps.py` must pass: its writes overlap no tweak it can be installed with (run it with `--git` on
   the open branches too), or it declares `conflicts`. Code goes in a mask marked free in
   `tweaks/model-cycles_OS1.13/REGISTRY.md`; `python3 tools/registry.py` regenerates that file (commit it) and refuses
   a write in a mask whose sprite is not redirected.
4. **Register it**: `tweaks/model-cycles_OS1.13/PROVENANCE.md` row; `BUILD.md` section with the commands and the
   MAIN OS SHA-256 of the main combinations.
5. **Put it in the flasher**: add it to `FEATURES` in `tools/gen_flasher_tweaks.py` (`"status": "experimental"`, and
   its section `cat`), regenerate `docs/flasher/tweaks.js`, regenerate `REF_MAINOS` and `REF_MODS` with
   `tools/ref_mainos.py`, add its row texts (`FEAT` en + fr: `label`, `short`, `desc`) and guide anchor (`GUIDE_OF`) in
   `docs/flasher/app.js`, update the lists checked by `tools/webflash_smoke.js`. See `docs/AGENTS.md`.
6. **Document it for users**: a guide section in `docs/guide/index.html` (en + fr, buttons to press, limits), a new
   release at the top of `docs/assets/release.js` (en + fr), bump the `MC_BUILD` / `?v=` stamp on the pages, a row
   in the mod table of `README.md`.
7. **Validate** (below), then propose the commit and tell the maintainer what to test on the machine.
8. **After their test**: a small follow-up commit flips the status to `tested` (generator `FEATURES`, `tweaks.js`,
   guide, release notes, README, note: "Tested on the Model:Cycles (YYYY-MM-DD)"). If they report a problem, record it
   in the note, fix, and bump the release.

A fix to an existing mod follows the same path, minus the new files: note section, generator, proof, regenerated
JSON/`tweaks.js`/`REF_MAINOS`, release entry.

## Validation before pushing

Without firmware (always possible, run them all):

```sh
python3 tools/gen_flasher_tweaks.py --check      # tweaks.js matches tweaks/
python3 tools/check_overlaps.py                  # mods ticked together never write the same bytes (notes/49), except the
                                                 # same whole write or a mod on top of another (`requires`)
python3 tools/registry.py --check                # REGISTRY.md (free space and hooks, notes/52) matches tweaks/
python3 tools/relocate_6ch.py --check            # needs m68k binutils (below)
tools/webbuild_check.sh                          # builder.js == build.py, byte for byte (node)
tools/webcompose_check.sh                        # composer.js places packages as relocate.py, byte for byte (node)
tools/webflash_check.sh                          # flasher.js validates .syx like mtlib (node)
tools/webflash_smoke.sh                          # the flasher page in jsdom (node, npm, network)
python3 -m py_compile tools/*.py tools/emu/*.py
```

With the official files (download them from elektron.se into `firmware/`, which is git-ignored:
`model-cycles_OS1.13.syx`, SHA-256 `44fe5862…9800640c`; `Syntakt_OS1.42.syx` for the Syntakt engines):

```sh
python3 tools/gen_<mod>.py --cycles firmware/model-cycles_OS1.13.syx --check
python3 tools/emu/test_<mod>.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/emu/test_compose.py --cycles firmware/model-cycles_OS1.13.syx   # Level B: the composed machines
python3 tools/gen_registrar.py --cycles firmware/model-cycles_OS1.13.syx --check   # registrar.json and frame.json
tools/webcompose_check.sh firmware/model-cycles_OS1.13.syx    # composer.js composes as compose.py: tweaks, MAIN OS
python3 tools/ref_mainos.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx --check
tools/webflash_smoke.sh firmware/model-cycles_OS1.13.syx firmware/model-samples_OS1.13.syx   # the REF_MAINOS sample,
                                                                     # each mod checked, and the Model:Samples flows
```

Emulation needs `pip install unicorn numpy` (wheels for Python 3.14 since Unicorn 2.1.4); Unicorn's JIT stops with
SIGILL in a sandbox that forbids generated code, so an agent in such a sandbox hands the proof's command to the
maintainer for a normal terminal. Code mods need the m68k toolchain (`m68k-linux-gnu-*` from the Debian/Ubuntu
packages `binutils-m68k-linux-gnu gcc-m68k-linux-gnu`, or `m68k-elf-*`); some committed outputs were compiled with a
specific GCC (SD VINTAGE v2 with `m68k-elf-gcc` 16.2, notes/16 §6), so `--check` can differ with another compiler.
If a check cannot run (no network, no toolchain), say so instead of skipping it silently.

## Commits

- Commit messages in English: a short subject saying what the user gets ("Tempo up to 546 BPM (tempo-max tweak,
  notes/38)"), a body with the why, the bullets of what changed, and how it was proven, then the trailer
  `Co-Authored-By: Claude`.
- Merge `main` into a feature branch rather than rebasing shared branches; regenerate `tweaks.js` and `REF_MAINOS`/`REF_MODS`
  after a merge instead of resolving their conflicts by hand.
- Before proposing a commit, say what the user sees before and after, how it was proven, and **what the maintainer
  should test on the machine** (which mods ticked, which buttons, what to listen or look for).
