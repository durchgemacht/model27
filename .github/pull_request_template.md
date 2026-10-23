<!-- See CONTRIBUTING.md. A new machine or mod starts with an issue; link it below. Do not attach firmware (.syx). -->

## What it does

<!-- On the machine: which buttons, what you hear or see, its limits. -->

Issue: #

## Kind

- [ ] A machine as a package (`tools/machines/<id>/`, the porting guide's section 12)
- [ ] A fix to a mod already offered
- [ ] The site, the guide or the docs
- [ ] Other

## Checks

<!-- For a machine: the result line of each check, or "not run" and why.
Other changes: the checks AGENTS.md names for them. -->

- `python3 tools/claims.py --check --self-test`:
- `python3 tools/check_overlaps.py`:
- `python3 tools/registry.py --check`:
- `python3 tools/relocate.py tools/machines/<id>/<id>.o`:
- `python3 tools/gen_<id>.py --cycles <official file> --check`:
- `python3 tools/compose.py --cycles <official file> --machines <id> --compare-ld`:
- the same with `--machines sampler,<id>` and `--machines <id>,sampler`:
- `python3 tools/emu/test_compose.py --cycles <official file> --machines <id>`:
- `test_shortcuts.py` (with a shortcut), `test_views.py` (with a view, the tick or the browser):
- `tools/webcompose_check.sh <official file>`:

## Tried on

<!-- digiemu, your own Model:Cycles: date, what you tried. The card stays Experimental until the maintainer has played
it on theirs. -->

## License and credit

- [ ] My contribution is under the MIT License, or its folder carries its own MIT, BSD, ISC or 0BSD `LICENSE`.
- [ ] Code by others is named with where it comes from and its license.
- [ ] No Elektron firmware or bytes copied from it, apart from a tweak's `old` bytes.

Credit as:
