# Contributing to model27

Thanks for wanting to help. model27 keeps its list of mods short on purpose: a new mod gets in when it fits the
project's aims (the README says what they are) and, once it exists, follows the Cycles Mod Standard. Fixes, test
reports and ideas are welcome as issues or pull requests; the issue templates ask for what helps (*Bug report*, *New
machine or mod*).

## License of your contribution

- By opening a pull request, you agree that your contribution is licensed under the [MIT License](LICENSE), like the
  rest of the project.
- A mod folder may carry its own permissive license instead (MIT, BSD, ISC or 0BSD) in a `LICENSE` file next to its
  sources: say so in the pull request. Copyleft code (GPL and the like) cannot go into the web flasher's bundle.
- If your work builds on someone else's code, say where it comes from and under which license, so it can be credited in
  [`tweaks/model-cycles_OS1.13/PROVENANCE.md`](tweaks/model-cycles_OS1.13/PROVENANCE.md) and
  [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md). Do not transcribe or closely paraphrase code whose license
  does not allow it (GPL code into MIT files, code with no license at all).
- Work sent privately (on Discord, as `.syx` files or scripts) is published only after its author has said yes in
  writing, with the credit they want.

## Elektron firmware

Never include Elektron firmware or bytes copied from it, apart from the short `old` bytes a tweak needs to check the
user's own file. Builds always start from the user's own official file. See [`AGENTS.md`](AGENTS.md) for the hard
rules (only the MAIN OS section is touched, every mod is proven in emulation, recovery must stay possible).

## How a mod gets in

1. **Open an issue first**, with the *New machine or mod* template: what it does on the machine, where its code is,
   its license. The maintainer answers whether it fits (for a machine, the Gen 1 rules in the
   [README](README.md#stability-first-gen-1-machines)) and, if it does, gives it its `order`, the number of its tweak
   file. Do not pick one yourself, nor a machine number, a sound slot or a record slot.
2. **A machine comes as a package.** Port it as section 12 of the standard's
   [porting guide](https://github.com/durchgemacht/cycles-mod-standard/blob/main/APPLYING.md#12-porting-a-machine-to-model27s-builder)
   describes, starting from a copy of the second reference machine,
   [`tools/machines/refmachine2/`](tools/machines/refmachine2/); section 12.8 has a prompt if you work with an AI
   assistant. The pull request holds:
   - `tools/machines/<id>/`: the sources, the committed object `<id>.o`, `manifest.json` with its claims, and the
     sources' `LICENSE`;
   - `tools/gen_<id>.py`: writes the object and the machine's tweak alone,
     `tweaks/model-cycles_OS1.13/<order>-<id>.json`; `--check` compares both with the committed files;
   - `tweaks/model-cycles_OS1.13/REGISTRY.md`, regenerated with `python3 tools/registry.py` (no firmware needed);
   - the proofs of section 12.6 under `tools/emu/`, pointed at your machine, and its selections (alone, before and
     after `sampler`) in `SELECTIONS` of `tools/webcompose_synth.py`, which `tools/webcompose_check.sh` composes;
   - optionally, a note `notes/NN-<slug>.md` in English, with its row in `notes/README.md` (the next free number; the
     maintainer renumbers it if two pull requests take the same one);
   - in its description, the result of each check section 12 names, and "not run" with the reason for a check you
     could not run.
3. **Another mod** (not a machine, or a machine that is not a package yet) starts with the inventory of the porting
   guide's sections 1 to 11, without changing its code. The maintainer then decides with you whether it is ported to
   a package, becomes a tweak, or stays a command-line build. A tweak's pull request follows steps 1 to 3 of
   [`AGENTS.md`](AGENTS.md#adding-a-feature-for-users-the-usual-pr) (note, generator, proofs, `REGISTRY.md`); its
   card, guide section, release notes and credit come as in step 4, not in the pull request.
4. **The maintainer takes it from there.** They run the checks again with the official files, the emulation proofs,
   digiemu and their own Model:Cycles. The flasher card, the guide section, the release notes and the credit
   (`PROVENANCE.md`, `THIRD-PARTY-NOTICES.md`) come in a commit of their own after the merge, with the generated
   files of the page: which cards the page offers is the maintainer's call. A new mod ships as *Experimental*; it
   becomes *Tested* only after the maintainer has tried it on their own Model:Cycles.

**Generated files.** Apart from `REGISTRY.md` and the mod's own object and tweak, a pull request leaves the generated
files as they are: `docs/flasher/tweaks.js` and the `REF_MAINOS` and `REF_MODS` blocks of `docs/flasher/app.js`, even
when `gen_flasher_tweaks.py --check` or `ref_mainos.py --check` then fails. The maintainer regenerates them after the
merge, so that two pull requests never clash over them.

A fix to the site, the guide or a mod already offered is one pull request with its note section and proof, as
[`AGENTS.md`](AGENTS.md) describes; its release entry and the generated files come with the maintainer's commit after
the merge, as in step 4.
