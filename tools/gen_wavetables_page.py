#!/usr/bin/env python3
"""Writes docs/wavetables/index.html, the site's Wavetables page, from the CHORD Wave Editor.

The editor is CHORD Wave Bank's (by durchgemacht and Claude, MIT): one HTML file, `editor/chordwave-editor.html` of
that repository, with the Braids and Plaits wave tables in it and both license texts in a comment at its top. It
builds a wavetable for CHORD into the official OS 1.13 or into a model27 build, in the browser. The page here is that
file as it is, plus what makes it one of the site's pages: its title and icon, the site's header and nav, a footer
with model27's version, and release.js and site.js with the site's version stamp (window.MC_BUILD of
flasher/index.html). Edit the editor, then run this again; never edit the page by hand.

    python3 tools/gen_wavetables_page.py --editor ../cycles-chordwave/editor/chordwave-editor.html
    python3 tools/gen_wavetables_page.py --editor … --check

--check exits 1 when the page is not what the editor gives (the ?v= stamp and the version shown before site.js
runs aside, which the next release changes on every page) or when the pages of the site do not have the same nav.
Standard library only.
"""
import argparse
import pathlib
import posixpath
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "wavetables" / "index.html"
# the pages with the site's nav, by folder ("" = the home page)
PAGES = ["", "flasher", "manager", "uploader", "wavetables", "guide"]

TITLE = """<title>Wavetables · model27</title>
<meta name="description" content="Make a wavetable for CHORD on the Elektron Model:Cycles from the waves of Plaits and Braids or your own WAV files, hear it, and build it into the official OS 1.13 or a model27 build. Your files stay in your browser.">
<link rel="icon" href="../assets/icon.svg" type="image/svg+xml">"""

# the header of the other pages (site.css with ../uploader/style.css on it), under class names the editor does not
# use: it has a .brand of its own
CSS = """
/* model27's header and nav, added by model27's tools/gen_wavetables_page.py: the other pages' (site.css with
   ../uploader/style.css on it), aligned with this page's columns */
.site-top { max-width: 1280px; margin: 0 auto; padding: 24px 24px 0; display: flex; flex-wrap: wrap; align-items: center; gap: 10px 20px; }
.site-brand { margin-right: auto; font: 700 20px/1 var(--body); text-transform: uppercase; text-decoration: none; }
.site-top nav { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 16px; font: 700 14px/1 var(--body); text-transform: uppercase; }
.site-top nav a { text-decoration: none; }
.site-top nav a:hover, .site-top nav a[aria-current="page"] { text-decoration: underline; text-decoration-thickness: 3px; text-underline-offset: .3em; }
@media (max-width: 560px) { .site-top { padding-inline: 16px; } }
"""

HEADER = """<header class="site-top">
  <a class="site-brand" href="../">model27</a>
  <nav aria-label="Site">
    <a href="../flasher/">Flasher</a>
    <a href="../manager/">Manager</a>
    <a href="../uploader/">Uploader</a>
    <a href="./" aria-current="page">Wavetables</a>
    <a href="../guide/">Guide</a>
    <a href="https://github.com/durchgemacht/model27" target="_blank" rel="noopener">GitHub</a>
  </nav>
</header>
"""

FOOTER = """<footer><div class="foot-in">
    <p>Your OS file and your waves stay in this browser. The preview models the waves and CHORD's crossfade, not its envelopes, COLOR or the rest of the signal path.</p>
    <p>The editor of CHORD Wave Bank, MIT license. Wave tables of Braids and Plaits by Emilie Gillet, MIT license, from pichenettes/eurorack (commit 08460a6). Not affiliated with Elektron; contains no Elektron firmware.</p>
    <p>model27 <span data-rel="version">{version}</span> · <a href="../#version">what's new</a> · <a href="../guide/">guide</a></p>
</div></footer>"""

SCRIPTS = """
<!-- ?v= : the site's version stamp, as on the other pages -->
<script src="../assets/release.js?v={stamp}"></script>
<script src="../assets/site.js?v={stamp}"></script>
"""

MARK = ("<!-- model27's Wavetables page, written by tools/gen_wavetables_page.py from the CHORD Wave Editor: change "
        "the editor and run it again, never this file. -->")


def once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit(f"!! the editor has {n} × {what}, expected one: is it the CHORD Wave Editor?")
    return text.replace(old, new)


def page(editor, stamp, version):
    t = editor
    if not t.startswith("<!doctype html>\n"):
        sys.exit("!! the editor does not start with <!doctype html>")
    if "gen_wavetables_page.py" in t:
        sys.exit("!! that is this page, not the editor")
    t = "<!doctype html>\n" + MARK + "\n" + t[len("<!doctype html>\n"):]
    t = once(t, "<title>CHORD Wave Editor</title>", TITLE, "its <title>")
    t = once(t, "</style>", CSS + "</style>", "</style>")
    t = once(t, '<main class="app">', HEADER + '\n<main class="app">', '<main class="app">')
    feet = re.findall(r'<footer><div class="foot-in">.*?</div></footer>', t, re.S)
    if len(feet) != 1:
        sys.exit(f"!! the editor has {len(feet)} footers, expected one")
    t = t.replace(feet[0], FOOTER.format(version=version))
    if not t.endswith("</script>\n"):
        sys.exit("!! the editor does not end with its script")
    return t + SCRIPTS.format(stamp=stamp)


def site_stamp():
    m = re.search(r'window\.MC_BUILD = "([0-9-]+)"', (DOCS / "flasher" / "index.html").read_text(encoding="utf-8"))
    if not m:
        sys.exit("!! no window.MC_BUILD in docs/flasher/index.html")
    return m.group(1)


def site_version():
    # the first entry of MC_RELEASES (the comment above it has an example with a version too)
    m = re.search(r'MC_RELEASES = \[\s*\{ version: "([0-9.]+)"', (DOCS / "assets" / "release.js").read_text(encoding="utf-8"))
    if not m:
        sys.exit("!! no version in docs/assets/release.js")
    return m.group(1)


def unstamped(t):
    t = re.sub(r"\?v=[0-9-]+", "?v=", t)
    return re.sub(r'<span data-rel="version">[^<]*</span>', '<span data-rel="version"></span>', t)


def nav_of(folder):
    """The site nav of a page: (where each link goes, its text) in order, and where its aria-current link goes."""
    path = DOCS / folder / "index.html" if folder else DOCS / "index.html"
    m = re.search(r'<nav aria-label="Site">(.*?)</nav>', path.read_text(encoding="utf-8"), re.S)
    if not m:
        return None, None
    links, current = [], None
    for a in re.finditer(r'<a href="([^"]*)"([^>]*)>([^<]*)</a>', m.group(1)):
        href, attrs, label = a.groups()
        if not href.startswith("https://"):
            href = posixpath.normpath(posixpath.join(folder, href))
            href = "" if href == "." else href
        links.append((href, label.strip()))
        if 'aria-current="page"' in attrs:
            current = href
    return links, current


def check_navs():
    ok = True
    first = None
    for folder in PAGES:
        links, current = nav_of(folder)
        name = (folder or "home") + " page"
        if links is None:
            print(f"!! {name}: no <nav aria-label=\"Site\">")
            ok = False
            continue
        if first is None:
            first = (name, links)
        elif links != first[1]:
            print(f"!! {name}: its nav is not the {first[0]}'s:\n   {links}\n   {first[1]}")
            ok = False
        if folder and current != folder:
            print(f"!! {name}: aria-current is on {current!r}, not on its own link")
            ok = False
    if ok:
        print(f"ok: the {len(PAGES)} pages have the same nav ({', '.join(label for _, label in first[1])})")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--editor", required=True, type=pathlib.Path,
                    help="CHORD Wave Bank's editor/chordwave-editor.html (a fresh build of its template)")
    ap.add_argument("--check", action="store_true", help="check the page and the navs, write nothing")
    args = ap.parse_args()
    want = page(args.editor.read_text(encoding="utf-8"), site_stamp(), site_version())
    if args.check:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        same = unstamped(have) == unstamped(want)
        print("ok: docs/wavetables/index.html is the editor's" if same else
              "!! docs/wavetables/index.html is not what this editor gives: run without --check")
        navs = check_navs()
        sys.exit(0 if same and navs else 1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(want, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(want.encode())} bytes, stamp {site_stamp()}, version {site_version()})")
    check_navs()


if __name__ == "__main__":
    main()
