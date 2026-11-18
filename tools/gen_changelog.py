#!/usr/bin/env python3
"""Writes CHANGELOG.md, model27's releases for the repository, from docs/assets/release.js.

release.js (window.MC_RELEASES) is where a release is written: the home page and the flasher show it. CHANGELOG.md
is the same text as Markdown, model27's own releases only (0.x): the entries from 1.56 down are Modded-Cycles' and
stay on the site. Add the release to release.js, then run this again; never edit CHANGELOG.md by hand.

    python3 tools/gen_changelog.py
    python3 tools/gen_changelog.py --check

--check exits 1 when CHANGELOG.md is not what release.js gives. Standard library only.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "assets" / "release.js"
OUT = ROOT / "CHANGELOG.md"

HEAD = """# Changelog

model27's releases, newest first, as the [flasher](https://durchgemacht.github.io/model27/flasher/) shows them.
The releases from 1.56 down are [Modded-Cycles](https://github.com/18nelli18/Modded-Cycles)' own; model27 starts
from its release 1.55.

This file is written by `tools/gen_changelog.py` from `docs/assets/release.js`.
"""

ENTRY = re.compile(r'\{\s*version:\s*"([^"]+)",\s*date:\s*"([^"]+)",\s*changes:\s*\[')
CHANGE = re.compile(r'\ben:\s*"((?:[^"\\]|\\.)*)"')


def releases(text):
    """(version, date, [changes]) per entry, in the file's order: each entry's changes are the en strings between
    its head and the next entry's. The file's comments go first: its head comment shows an entry as an example."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    heads = list(ENTRY.finditer(text))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        changes = [json.loads('"' + s + '"').strip() for s in CHANGE.findall(text, m.end(), end)]
        out.append((m.group(1), m.group(2), changes))
    return out


def render(text):
    own = [r for r in releases(text) if r[0].startswith("0.")]
    if not own:
        sys.exit("gen_changelog: no 0.x release found in " + str(SRC))
    lines = [HEAD]
    for version, date, changes in own:
        lines.append(f"\n## {version} ({date})\n\n")
        for c in changes or ["No notes."]:
            lines.append("- " + c + ("" if c[-1:] in ".!?)" else ".") + "\n")
    return "".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="compare with CHANGELOG.md instead of writing it")
    args = ap.parse_args()
    new = render(SRC.read_text(encoding="utf-8"))
    if args.check:
        old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if old != new:
            print("CHANGELOG.md is not up to date: run python3 tools/gen_changelog.py")
            return 1
        print("CHANGELOG.md ok")
        return 0
    OUT.write_text(new, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
