# AGENTS.md — tools/

The Python build, one generator per mod, the ColdFire sources, and the emulation proofs. Read the root
[`AGENTS.md`](../AGENTS.md) first. Method and safety rules in full: [`notes/05-methode-patch.md`](../notes/05-methode-patch.md);
platform and ISA pitfalls: [`notes/03-plateforme-coldfire.md`](../notes/03-plateforme-coldfire.md).

## Conventions

- Python 3, standard library for everything that builds or flashes (`build.py`, `mtlib/`, `gen_flasher_tweaks.py`,
  `ref_mainos.py`): users run them without installing anything. Only the generators of code mods and the proofs
  under `emu/` may need `unicorn`, `numpy` and the m68k toolchain.
- Docstrings and comments in **French**, like the rest of the folder. The module docstring explains what the mod does,
  where its code lives, the note it comes from, and the command line to run it.
- Addresses are ColdFire VAs of OS 1.13. Section 3 offset = `VA - 0x40000400` (`build.BASE`).
- `compose.py` and `relocate.py` (Level B) have a JavaScript twin, `docs/flasher/composer.js`, which composes the
  machine cards in the page (notes/61): a change to how a package is placed, registered (`frame`, `fill`) or its
  conflicts computed goes into both in the same commit, and `tools/webcompose_check.sh model-cycles_OS1.13.syx`
  must pass. A change to `registrar.S` or to `frame()` regenerates `frame.json` (`gen_registrar.py --cycles`).
  This holds for the builder's parts too (notes/63, B4e): the shortcut layer and the dispatchers
  (`compose.shortcut_layer`, `compose.dispatch_layer`, parts built by `gen_parts.py`) have their twins
  (`shortcutLayer`, `dispatchLayer`), the page gets the parts laid out once (`compose.web_part`, embedded in
  `tweaks.js`), and `webcompose_synth.py` composes REF2, which needs both, among its selections.
- Detect the cross toolchain as the existing generators do:
  `next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "gcc")), "m68k-linux-gnu-")`.
  Compiled code is built with `-mcpu=54418`. Pin the compiler version used in the note when output bytes depend on it.
  Without Homebrew, m68k-elf GCC 16.2.0 and binutils 2.47 build from Ubuntu's source tarballs
  (`gcc-16_16.2.0.orig.tar.gz`, `binutils_2.47.orig.tar.xz`, configure lines in notes/42 §16); that build reproduces
  `45-chord-keys.json` and the SD VINTAGE JSONs byte for byte.

## A generator: `gen_<mod>.py`

Copy the shape of `gen_tempo_max.py` (data only) or `gen_trig_hold.py` (assembled code in a freed sprite mask):

- `--cycles model-cycles_OS1.13.syx` (and `--syntakt Syntakt_OS1.42.syx` if needed); refuse a file whose section 3
  SHA-256 differs from `device.json`.
- Read the stock bytes and **check them** before producing each write; the `old` bytes always come from the official
  image, never typed by hand.
- Write `../tweaks/model-cycles_OS1.13/NN-<id>.json` with `json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"`.
- `--check` regenerates in memory and compares with the committed file (exit 1 if different). Every generated file in
  the repo must pass `--check`.
- Apply the result with `build.apply_writes` before writing it, so a bad `old` fails here and not in the build.

## Where code can live

Free space is scarce and every byte of it is accounted for in a note. Before taking any, read the notes that use it
and check the writes of **every** other tweak for overlaps.

- **Freed sprite masks** (`sprites.py`, notes/14 §5, notes/32 §11, notes/52): a sprite is redirected to an identical
  mask (`sprites.redirect_write`), freeing its own. `sprites.GROUPS` lists the 10 groups of identical masks (164
  freeable masks, 104 to 1024 bytes each, about 36 KB); **`tweaks/model-cycles_OS1.13/REGISTRY.md` says which are
  taken and which are free**, with the bytes each mod writes. Take a free one, then run `python3 tools/registry.py`
  and commit the regenerated file; `python3 tools/registry.py --git <branch>` shows what the open PRs have taken.
  Several mods may share a mask only if they never write the same bytes when built together (trig-hold in front of
  6ch-usbup's stubs in `0x4015c044`), or can never be built together (sample-preview and chord-keys): that is what
  `check_overlaps.py` checks. `registry.py` refuses a write into a mask whose sprite the tweak (or a tweak it
  `requires`) does not redirect, and any write into a kept copy.
- **Payload appended to the image** and copied at boot to SDRAM (`0x43000000`, notes/17; Model-TG uses
  `0x46700000`, notes/31): for large code, at the cost of a boot hook shared with the Syntakt engines.
- **In place**: rewrite the function you change when the new code fits (tempo-max's LFO loop, trig-preview's 3 bytes).
  Prefer this whenever possible.
- Mod settings that must survive a save go in unused bytes of the pattern or project structures, proven unused
  (the arpeggiator uses byte +512 of the pattern track, notes/32 §4).
- Two tweaks may write the same bytes only if they write them **identically**; otherwise declare `conflicts`.

## Safety rules for code in the firmware

- Hook with a detour (`jmp stub`, `nop` padding); the stub replays exactly what the moved instructions did and
  returns with the registers the following code expects. Document that contract at the top of the `.S`.
- No branch, jump or stored pointer may target the inside of a hook's padding (frozen logo / `VEC:04`).
- Code reachable from an interrupt or re-entrantly must not keep its state in a single global; save and restore every
  register it touches; no waits or blocking calls.
- The audio interrupt is the tight spot: the stock OS already spends about 77 % of each 0.67 ms audio block there
  (notes/23). Measure the cost of anything added to the voice loop or the audio path, keep it out of there when you
  can, and check the load governor (notes/25, 30, 36) with `emu/test_governor.py`.
- USB audio timing is fixed by `usb_steady.py` (notes/35); Model-TG and the Syntakt engines share it. Reuse the shared
  writers (`usb_steady.py`, `voice_loop.py`, `gov_asm.py`, `sprites.py`) instead of copying their bytes.

## Proofs: `emu/test_<mod>.py`

- Run the **OS's own code** in Unicorn (`emu/mcengine.py` for the voice loop, `emu/emac.py` for exact EMAC, existing
  tests for event loops, keys, MIDI, USB), on the stock MAIN OS **and** the patched one, and show the difference the
  mod makes and that nothing else changes.
- Check the writes against the stock bytes and against all other tweaks (no overlap), then run with the other mods
  applied: `--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max --syntakt …`.
- Print one line per check (`ok` / `FAIL`) and exit non-zero on any failure. State the run time in the docstring if it
  is long.
- When a proof finds the stock OS misbehaving (as tempo-max's LFO above 351.6 BPM), keep that check: it documents why
  the patch exists.

## Shared scripts you will regenerate

- `gen_flasher_tweaks.py`: the `FEATURES` list (cards of the web flasher). Add the new mod there, then run it; `--check`
  in validation. Card `status` is `"experimental"` until Maxime tests it.
- `check_overlaps.py [--git REF …]`: no firmware needed. Two tweaks that can be installed together never write the
  same bytes (except the same whole write, or one applied on top of the other through `requires`), every write is
  well formed, and the payloads of every installable set chain up (`at`, `END_LIMIT`, `dest`). With `--git` it reads
  branches and checks them together (the open PRs). This is what lets the flasher check mods one by one (notes/49).
  Since notes/65 (C2) the declared claims too: two tweaks that can be installed together never claim the same saved
  slot, key combination, descriptor or formatter; and it says how each declared conflict is shown (by the bytes, the
  claims, both, or its text only).
- `claims.py [--check] [--list] [--self-test]` (notes/65): no firmware needed. Reads and checks the declared claims:
  a package's `claims` in its manifest, a part's in its `part.json`, the tweaks' in
  `tweaks/model-cycles_OS1.13/claims/claims.json`. A mod that keeps values in a sound or a pattern, answers a key
  combination, or takes a descriptor, a formatter, MIDI numbers, RAM or a view declares it there; the words of a
  combination are the vocabulary at the top of `claims.py`. `--check` in validation. Its rules (`clashes`) compute
  conflicts in `compose.py`, in `check_overlaps.py` and, as `claimClashes`, in `docs/flasher/composer.js`: a change
  to them goes into both composers in the same commit, as for the rest of the composer.
- `registry.py [--check] [--git REF …] [--cycles SYX]`: no firmware needed. Rewrites
  `tweaks/model-cycles_OS1.13/REGISTRY.md`, the registry of free space and hook points built from the tweak writes
  (notes/52): freed masks taken and free, 0xFF caves, payload chains, OS detours, rewritten pointers, what each mod
  touches. `--check` in validation; `--git` adds branches (to the screen); `--cycles` also verifies the mask survey on
  the official OS. Saved-structure bytes a mod claims (the arpeggiator's pattern byte +512) go in its `DECLARED` table.
- `ref_mainos.py --cycles … --syntakt … [--check]`: rewrites `REF_MODS` (each tweak's writes and payload hashes) and
  `REF_MAINOS` (the MAIN OS of a sample: each card alone, every pair, the largest combinations) in
  `docs/flasher/app.js`. Rerun after any change to a tweak or to `FEATURES`; it reads the card rules like `app.js`.
- `webflash_smoke.js`: asserts the list and order of tweaks and cards and their tags; update it with the new card.
- Adding a Syntakt engine: `CATALOG` in `gen_syntakt_engines.py`, then `--all` and `--all --tg`,
  `gen_flasher_tweaks.py`, `check_overlaps.py`, `ref_mainos.py`, and a proof per new tweak (see BUILD.md).
