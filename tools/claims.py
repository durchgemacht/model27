#!/usr/bin/env python3
"""The declared claims of model27's mods, read and checked (notes/65, step C1).

A claim is what a mod takes that no write shows: the sound slots k and the record slots it keeps its values in, other
saved bytes, the key combinations it answers, the OS's unused descriptors 1-4, an interface object's formatter, the
p-lock rows of k >= 23, MIDI numbers, RAM, the views it draws on. Three kinds of holder give them in one shape:

  - a package: `claims` in tools/machines/<id>/manifest.json; scope: its own machine's tracks and sounds;
  - a part of the builder: `claims` in tools/machines/<id>/part.json; scope: every track and sound;
  - a tweak of the folder: an entry of tweaks/model-cycles_OS1.13/claims/claims.json, with the note that shows it;
    scope: every track and sound. The file sits in a subfolder because a dozen tools read every *.json of the tweak
    folder as a tweak.

A claim may name another scope: "all", "machine" (a package's own), or "machine:<NAME>" (a stock machine, MACRO or
ACID, or a package id). A key combination is written as the standard's tables write it, the held keys then one action
joined by "+" ("TRACK + TRIG 1-6", "MACHINES + COLOR/SHAPE/SWEEP/CONTOUR"), on the vocabulary below. The tools compare
its atoms, one set of held keys and one action each, in a situation ("params", "grid", "keys", "page:LFO",
"menu:RETRIG"; "any" by default).

This step reads and checks the data: the claim types and their values, the words, the ids, and that a manifest's or a
part's claims agree with what it uses. The conflicts computed from the claims (rules 2 and 3 of the Cycles Mod
Standard, notes/65 §5) come with step C2.

    python3 tools/claims.py --check        # the data; exit 1 on an error
    python3 tools/claims.py --list         # each holder's claims, a combination with its number of atoms
    python3 tools/claims.py --self-test    # the parser and the checks on synthetic claims
"""
import argparse
import fnmatch
import itertools
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
MACHINES_DIR = HERE / "machines"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
CLAIMS_FILE = DEV / "claims" / "claims.json"
SCHEMA = "model27-claims/0.1"

# --- the vocabulary -------------------------------------------------------------------------------------------------

# Keys, by isKeyHeld's logical code (0x4007faf4, notes/63 §1.1); None for a key whose code is not traced yet.
KEYS = {"FUNC": 1, "TRACK": 2, "RETRIG": 4, "MACHINES": 5, "PUNCH": 6, "LFO": 8, "RECORD": 9, "PLAY": 10, "STOP": 11,
        "GATE": None, "PAGE": None, "PATTERN": None}
TRIGS = 16                          # TRIG 1-16, codes 16 to 31
# Knobs, by their number in the knob -> descriptor lookup 0x4001e814 (notes/63 §1.2); DATA is LEVEL/DATA, not traced.
KNOBS = {"PITCH": 2, "DECAY": 3, "COLOR": 4, "SHAPE": 5, "SWEEP": 6, "CONTOUR": 7, "DATA": None}
# Actions that are neither a key press nor a knob turn.
OTHER = {"NOTES": "notes played, on the pads or on the TRIG keys in keyboard mode",
         "DATA-PRESS": "a press on the LEVEL/DATA knob"}
SITUATIONS = ("any", "params", "grid", "keys")     # params: the parameter pages, where a knob edits the sound
PAGES = ("LFO",)
MENUS = ("RETRIG", "TRACK-SETUP", "MIDI-PORTS")
STOCK_MACHINES = ("KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD")
TWEAK_MACHINES = ("MACRO", "ACID")  # the machines the folder's tweaks add (notes/43, notes/54)

# The stock OS's own combinations, as far as they are read. A mod that takes one says what it replaces ("replaces");
# step C2 refuses a claim on one without it (notes/65 §11). hyp: not read in the code.
KNOB_LIST = "PITCH/DECAY/COLOR/SHAPE/SWEEP/CONTOUR"
STOCK = (
    {"combo": f"FUNC + {KNOB_LIST}", "situation": "params", "meaning": "fine adjust", "source": "notes/63 §1.2"},
    {"combo": f"TRACK + {KNOB_LIST}", "situation": "params", "meaning": "Control All", "source": "notes/63 §1.2"},
    {"combo": f"LFO + {KNOB_LIST}", "situation": "params", "meaning": "the parameter becomes the LFO's destination",
     "source": "notes/63 §1.2"},
    {"combo": f"TRIG 1-16 + {KNOB_LIST}", "situation": "params", "meaning": "parameter lock",
     "source": "notes/63 §1.3"},
    {"combo": "TRACK + PUNCH/GATE", "meaning": "Control All of PUNCH and GATE", "source": "STANDARD.md §5.4"},
    {"combo": "FUNC + TRACK", "meaning": "the Track Setup menu", "source": "STANDARD.md §5.4"},
    {"combo": "FUNC + MACHINES", "meaning": "the PRESET browser", "source": "STANDARD.md §5.4"},
    {"combo": "FUNC + RETRIG", "meaning": "the retrig menu", "source": "notes/63 §1.2"},
    {"combo": "TRACK + RECORD/PLAY/STOP", "meaning": "copy, clear, paste", "source": "notes/58 §2"},
    {"combo": "RETRIG + NOTES", "meaning": "the retrig", "source": "notes/63 §1.2, notes/32"},
    {"combo": "TRIG 1-16 + PAGE", "situation": "grid", "meaning": "PAGE turns the page", "source": "notes/34"},
    {"combo": "LFO", "situation": "page:LFO", "meaning": "closes the LFO page", "source": "notes/65 §3.2",
     "hyp": True},
)

# --- the claim types ------------------------------------------------------------------------------------------------

CLAIM_TYPES = ("sound_slots", "record_slots", "saved", "descriptors", "formatters", "plock_rows", "midi", "gestures",
               "ram", "views")
SOUND_SLOTS = range(0, 33)          # k 0-32 (STANDARD.md §5.2)
RECORD_SLOTS = range(0, 32)         # the record's 16-bit slots at +28 + 2 * slot, as far as read (STANDARD.md §5.3)
DESCRIPTORS = range(1, 5)           # the OS's unused descriptors, "Error" (STANDARD.md §3.1)
VIEWS = ("main", "knob")

_ALT = re.compile(r"([A-Z][A-Z-]*)(?: (\d+)(?:-(\d+))?)?")


def _words(part, held, text):
    """The alternatives of one part of a combination, as words ("TRIG 3" for a TRIG key)."""
    out = []
    for alt in (a.strip() for a in part.split("/")):
        m = _ALT.fullmatch(alt)
        if not m:
            raise ValueError(f"{text!r}: cannot read {alt!r}")
        word, lo, hi = m.groups()
        if word == "TRIG":
            if lo is None:
                raise ValueError(f"{text!r}: TRIG needs a number or a range, as TRIG 1-16")
            a, b = int(lo), int(hi or lo)
            if not 1 <= a <= b <= TRIGS:
                raise ValueError(f"{text!r}: {alt} is not within TRIG 1-{TRIGS}")
            out += [f"TRIG {n}" for n in range(a, b + 1)]
        elif lo is not None:
            raise ValueError(f"{text!r}: only TRIG takes a number")
        elif word in KEYS or (not held and (word in KNOBS or word in OTHER)):
            out.append(word)
        elif word in KNOBS or word in OTHER:
            raise ValueError(f"{text!r}: {word} cannot be held")
        else:
            raise ValueError(f"{text!r}: {word} is not in the vocabulary")
    return out


def atoms(text):
    """The atoms of a combination: (held keys, action) pairs, sorted. "TRACK + TRIG 1-6" gives six."""
    parts = [p.strip() for p in text.split("+")]
    if any(not p for p in parts):
        raise ValueError(f"{text!r}: an empty part")
    out = set()
    for pick in itertools.product(*(_words(p, i < len(parts) - 1, text) for i, p in enumerate(parts))):
        if len(set(pick)) != len(pick):
            raise ValueError(f"{text!r}: a key twice")
        out.add((frozenset(pick[:-1]), pick[-1]))
    return sorted(out, key=lambda a: (sorted(a[0]), a[1]))


def check_situation(s):
    kind, _, name = s.partition(":")
    if s not in SITUATIONS and not ((kind == "page" and name in PAGES) or (kind == "menu" and name in MENUS)):
        raise ValueError(f"situation {s!r} is not in the vocabulary")


def check_scope(s, kind, packages):
    pre, _, name = s.partition(":")
    if s == "all" or (s == "machine" and kind == "package") or (
            pre == "machine" and name in STOCK_MACHINES + TWEAK_MACHINES + tuple(packages)):
        return
    raise ValueError(f"scope {s!r}: all, machine (a package's own) or machine:<NAME>")


def _fields(item, allowed, required, what):
    if not isinstance(item, dict):
        raise ValueError(f"{what} {item!r} is not an object")
    if set(item) - set(allowed) or set(required) - set(item):
        raise ValueError(f"{what} {item!r}: fields {sorted(required)} needed, {sorted(allowed)} allowed")


def normalize(claims, kind, packages=()):
    """A holder's claims in one form, each with its scope (a package's own machine by default, every track and
    sound otherwise). Returns (claims, errors)."""
    default = "machine" if kind == "package" else "all"
    out, errors = {}, []
    if not isinstance(claims, dict):
        return out, [f"claims {claims!r} is not an object"]

    def scope(item):
        s = item.get("scope", default) if isinstance(item, dict) else default
        check_scope(s, kind, packages)
        return s

    def numbers(value, allowed, what, objects):
        got = []
        for item in value:
            if isinstance(item, int) and not isinstance(item, bool):
                nums = [item]
            elif objects and isinstance(item, dict):
                _fields(item, ("slots", "scope"), ("slots",), what)
                a, b = item["slots"]
                if a > b:
                    raise ValueError(f"{what} {item!r}: the first slot after the last")
                nums = range(a, b + 1)
            else:
                also = ' nor {"slots": [first, last]}' if objects else ""
                raise ValueError(f"{what} {item!r} is not a number{also}")
            for n in nums:
                if n not in allowed:
                    raise ValueError(f"{what} {n} is outside {allowed.start}-{allowed.stop - 1}")
                got.append((n, scope(item)))
        return got

    for key, value in claims.items():
        try:
            if key not in CLAIM_TYPES:
                raise ValueError(f"unknown claim type {key!r}")
            if key == "plock_rows":
                if not isinstance(value, bool):
                    raise ValueError("plock_rows is true or false")
                out[key] = value
                continue
            if key == "midi":
                _fields(value, ("cc", "nrpn"), (), "midi")
                cc = [c for c in value.get("cc", []) if isinstance(c, int) and 0 <= c <= 127]
                nrpn = [n for n in value.get("nrpn", [])
                        if isinstance(n, str) and re.fullmatch(r"\d+:\d+", n)
                        and all(0 <= int(x) <= 127 for x in n.split(":"))]
                if len(cc) != len(value.get("cc", [])) or len(nrpn) != len(value.get("nrpn", [])):
                    raise ValueError(f"midi {value!r}: CC 0-127, NRPN as \"MSB:LSB\" with both 0-127")
                out[key] = {"cc": cc, "nrpn": nrpn}
                continue
            if not isinstance(value, list):
                raise ValueError(f"{key} is a list")
            if key == "sound_slots":
                out[key] = numbers(value, SOUND_SLOTS, "sound slot k", True)
            elif key == "record_slots":
                out[key] = numbers(value, RECORD_SLOTS, "record slot", True)
            elif key == "descriptors":
                out[key] = numbers(value, DESCRIPTORS, "descriptor", False)
            elif key == "saved":
                for item in value:
                    _fields(item, ("where", "bytes", "scope"), ("where", "bytes"), "saved")
                    if not item["where"] or not isinstance(item["bytes"], int) or item["bytes"] < 1:
                        raise ValueError(f"saved {item!r}: a place and a number of bytes")
                out[key] = [(item["where"], item["bytes"], scope(item)) for item in value]
            elif key == "formatters":
                for item in value:
                    _fields(item, ("knob", "object", "replaces", "scope", "why"), ("knob", "object", "replaces"),
                            "formatter")
                    if not isinstance(item["object"], int) or item["object"] < 0:
                        raise ValueError(f"formatter {item!r}: object is an interface object's number")
                    int(item["replaces"], 16)
                out[key] = [(item["object"], scope(item), item["knob"]) for item in value]
            elif key == "ram":
                got = []
                for item in value:
                    lo, hi = (int(x, 16) for x in item)
                    if lo >= hi:
                        raise ValueError(f"ram {item!r}: [first, end) with first < end")
                    got.append((lo, hi))
                out[key] = got
            elif key == "views":
                got = []
                for item in value:
                    item = {"view": item} if isinstance(item, str) else item
                    _fields(item, ("view", "scope", "how"), ("view",), "view")
                    if item["view"] not in VIEWS:
                        raise ValueError(f"view {item['view']!r}: one of {', '.join(VIEWS)}")
                    got.append((item["view"], scope(item), item.get("how", "")))
                out[key] = got
            elif key == "gestures":
                got = []
                for item in value:
                    item = {"combo": item} if isinstance(item, str) else item
                    _fields(item, ("combo", "situation", "scope", "meaning", "replaces"), ("combo",), "gesture")
                    situation = item.get("situation", "any")
                    check_situation(situation)
                    got.append({"combo": item["combo"], "atoms": atoms(item["combo"]), "situation": situation,
                                "scope": scope(item), "meaning": item.get("meaning", ""),
                                "replaces": item.get("replaces")})
                out[key] = got
        except (ValueError, TypeError, KeyError) as e:
            errors.append(f"{key}: {e}")
    return out, errors


# --- the holders ----------------------------------------------------------------------------------------------------

def folder_ids():
    """The ids of the folder's tweaks."""
    return sorted(json.loads(f.read_text(encoding="utf-8"))["id"] for f in DEV.glob("[0-9]*.json"))


def packages():
    """{id: manifest} of the packages under tools/machines/."""
    out = {}
    for f in sorted(MACHINES_DIR.glob("*/manifest.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        out[m["id"]] = m
    return out


def parts():
    """{id: part.json} of the builder's parts under tools/machines/."""
    out = {}
    for f in sorted(MACHINES_DIR.glob("*/part.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        out[p["id"]] = p
    return out


def holders():
    """Every holder of claims, as dicts: kind (package, part, tweak), name, ids (the tweak ids it stands for),
    source, claims as written, open (what is still to be read), data (the manifest, part.json or entry)."""
    out = []
    for pid, m in packages().items():
        out.append({"kind": "package", "name": pid, "ids": [pid], "source": f"tools/machines/{pid}/manifest.json",
                    "claims": m.get("claims", {}), "open": [], "data": m})
    for pid, p in parts().items():
        out.append({"kind": "part", "name": pid, "ids": [], "source": f"tools/machines/{pid}/part.json",
                    "claims": p.get("claims", {}), "open": [], "data": p})
    data = json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))
    ids = folder_ids()
    for n, e in enumerate(data.get("entries", [])):
        pats = e.get("ids", [])
        out.append({"kind": "tweak", "name": ", ".join(pats) or f"entry {n + 1}", "patterns": pats,
                    "ids": sorted({i for p in pats for i in fnmatch.filter(ids, p)}), "source": e.get("source", ""),
                    "claims": e.get("claims", {}), "open": e.get("open", []), "data": e})
    return out


# --- the checks -----------------------------------------------------------------------------------------------------

def check_file(data, ids, pkgs):
    """claims.json itself: its schema, its fields, each pattern naming tweaks of the folder, no tweak twice, no
    package (a package's claims are in its manifest)."""
    errors = []
    if data.get("schema") != SCHEMA:
        errors.append(f"claims.json: schema {data.get('schema')!r}, {SCHEMA!r} expected")
    if set(data) - {"schema", "about", "entries"}:
        errors.append(f"claims.json: unknown fields {sorted(set(data) - {'schema', 'about', 'entries'})}")
    seen = {}
    for n, e in enumerate(data.get("entries", [])):
        name = ", ".join(e.get("ids", [])) or f"entry {n + 1}"
        if set(e) - {"ids", "source", "claims", "open"} or not e.get("ids") or not e.get("source"):
            errors.append(f"{name}: an entry has ids, source, claims and maybe open, nothing else")
        if not isinstance(e.get("open", []), list) or not all(isinstance(o, str) for o in e.get("open", [])):
            errors.append(f"{name}: open is a list of texts")
        for pat in e.get("ids", []):
            hit = fnmatch.filter(ids, pat)
            if not hit:
                errors.append(f"{name}: {pat!r} names no tweak of the folder")
            for i in hit:
                if i in pkgs:
                    errors.append(f"{name}: {i} is a package, its claims are in its manifest")
                if i in seen and seen[i] != name:
                    errors.append(f"{i} is in two entries: {seen[i]} and {name}")
                seen[i] = name
    return errors


def check_package(m, claims, shortcut_part):
    """A manifest's claims against its uses: the RAM of memory.ram, the views of view.*, and for each shortcut its
    key combination, sound slot and record slot (the part's list gives the slot of each knob)."""
    errors = []
    uses = m.get("uses", [])
    ram = sorted((int(a, 16), int(b, 16)) for u in uses if u.get("point") == "memory.ram" for a, b in [u["range"]])
    if ram != sorted(claims.get("ram", [])):
        errors.append("claims.ram is not the RAM of its uses (memory.ram)")
    views = sorted(u["point"][5:] for u in uses if u.get("point") in ("view.main", "view.knob"))
    if views != sorted(v for v, _s, _h in claims.get("views", [])):
        errors.append("claims.views are not the views of its uses (view.main, view.knob)")
    sc = shortcut_part["shortcut"] if shortcut_part else None
    for u in (u for u in uses if u.get("point") == "shortcut"):
        if not sc or u["knob"] not in sc["knobs"] or u["key"] != sc["key"]:
            errors.append(f"shortcut {u.get('key')} + {u.get('knob')} is not on the builder's list")
            continue
        i = sc["knobs"].index(u["knob"])
        want = set(atoms(f"{u['key']} + {u['knob']}"))
        if not any(want <= set(g["atoms"]) for g in claims.get("gestures", [])):
            errors.append(f"shortcut {u['key']} + {u['knob']}: no gesture claims it")
        if sc["sound_slots"][i] not in {n for n, _s in claims.get("sound_slots", [])}:
            errors.append(f"shortcut {u['key']} + {u['knob']}: k {sc['sound_slots'][i]} is not claimed")
        if sc["record_slots"][i] not in {n for n, _s in claims.get("record_slots", [])}:
            errors.append(f"shortcut {u['key']} + {u['knob']}: record slot {sc['record_slots'][i]} is not claimed")
    return errors


def check_shortcut_part(p, claims):
    """The shortcut layer's claims against its own list: its slots, descriptors and combinations."""
    sc, errors = p["shortcut"], []
    for key, want in (("sound_slots", sc["sound_slots"]), ("record_slots", sc["record_slots"]),
                      ("descriptors", sc["descriptors"])):
        if sorted(n for n, _s in claims.get(key, [])) != sorted(want):
            errors.append(f"claims.{key} are not the layer's {key} {want}")
    want = {a for k in sc["knobs"] for a in atoms(f"{sc['key']} + {k}")}
    if not want <= {a for g in claims.get("gestures", []) for a in g["atoms"]}:
        errors.append(f"claims.gestures do not hold {sc['key']} + each of {', '.join(sc['knobs'])}")
    return errors


def check():
    """claims.json, the stock list and every holder's claims. Returns [(ok, line)]."""
    out = []
    ids, pkgs, prts = folder_ids(), packages(), parts()
    data = json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))
    errs = check_file(data, ids, pkgs)
    named = {i for e in data.get("entries", []) for p in e.get("ids", []) for i in fnmatch.filter(ids, p)}
    out += [(False, e) for e in errs] or [(True, f"claims.json: {len(data.get('entries', []))} entries for "
                                                 f"{len(named)} of the folder's {len(ids)} tweaks")]
    errs = []
    for s in STOCK:
        try:
            atoms(s["combo"])
            check_situation(s.get("situation", "any"))
        except ValueError as e:
            errs.append(f"stock list: {e}")
    out += [(False, e) for e in errs] or [(True, f"stock list: {len(STOCK)} combinations, "
                                                 f"{sum(len(atoms(s['combo'])) for s in STOCK)} atoms")]
    for h in holders():
        claims, errs = normalize(h["claims"], h["kind"], pkgs)
        if h["kind"] == "package":
            errs += check_package(h["data"], claims, prts.get("shortcuts"))
        elif h["kind"] == "part" and "shortcut" in h["data"]:
            errs += check_shortcut_part(h["data"], claims)
        n = sum(len(v) if isinstance(v, list) else 1 for v in claims.values())
        line = f"{h['kind']} {h['name']}: {n} claim(s)"
        line += f" for {len(h['ids'])} tweak(s)" if h["kind"] == "tweak" else ""
        line += f", {len(h['open'])} open" if h["open"] else ""
        out += [(False, f"{h['kind']} {h['name']}: {e}") for e in errs] or [(True, line)]
    return out


# --- the listing ----------------------------------------------------------------------------------------------------

def _ranges(nums):
    nums, out = sorted(set(nums)), []
    for n in nums:
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in out)


def describe(h, pkgs):
    """One holder's claims, one line each."""
    claims, _ = normalize(h["claims"], h["kind"], pkgs)
    out = []
    for key, label in (("sound_slots", "k"), ("record_slots", "record slots"), ("descriptors", "descriptors")):
        for s in sorted({s for _n, s in claims.get(key, [])}):
            out.append(f"{label} {_ranges(n for n, t in claims[key] if t == s)} ({s})")
    out += [f"saved: {w}, {b} byte(s) ({s})" for w, b, s in claims.get("saved", [])]
    out += [f"formatter of interface object {o}, {k} ({s})" for o, s, k in claims.get("formatters", [])]
    if claims.get("plock_rows"):
        out.append("the p-lock rows of k >= 23")
    if claims.get("midi"):
        out.append(f"MIDI CC {', '.join(map(str, claims['midi']['cc']))}; NRPN {', '.join(claims['midi']['nrpn'])}")
    out += [f"RAM {lo:#x}-{hi:#x}" for lo, hi in claims.get("ram", [])]
    out += [f"view {v} ({s})" + (f": {how}" if how else "") for v, s, how in claims.get("views", [])]
    for g in claims.get("gestures", []):
        out.append(f"{g['combo']}: {len(g['atoms'])} atom(s) in {g['situation']} ({g['scope']})"
                   + (f", replaces {g['replaces']}" if g["replaces"] else ""))
    return out


# --- the self-test --------------------------------------------------------------------------------------------------

def self_test():
    """The parser and the checks on synthetic claims. Returns the number of failures."""
    fails = 0

    def case(name, ok):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        fails += not ok

    def raises(f, *a):
        try:
            f(*a)
        except ValueError:
            return True
        return False

    a = atoms("TRACK + TRIG 1-6")
    case("TRACK + TRIG 1-6: six atoms, TRACK held", len(a) == 6 and all(h == {"TRACK"} for h, _ in a)
         and [x for _, x in a] == [f"TRIG {n}" for n in range(1, 7)])
    case("MACHINES + COLOR/SHAPE/SWEEP/CONTOUR: four atoms", len(atoms("MACHINES + COLOR/SHAPE/SWEEP/CONTOUR")) == 4)
    a = atoms("TRIG 1-16 + PAGE")
    case("TRIG 1-16 + PAGE: sixteen atoms, one TRIG held each", len(a) == 16 and all(len(h) == 1 for h, _ in a))
    case("LFO alone: one atom, nothing held", atoms("LFO") == [(frozenset(), "LFO")])
    case("FUNC + TRACK + PUNCH/GATE: two keys held, two atoms",
         [h for h, _ in atoms("FUNC + TRACK + PUNCH/GATE")] == [frozenset({"FUNC", "TRACK"})] * 2)
    for bad in ("TRACK + TRIG 0-3", "TRACK + TRIG 3-1", "TRACK + TRIG 1-17", "TRACK + TRIG", "TRACK + FOO",
                "COLOR + TRACK", "TRACK + TRACK", "TRACK +", "FUNC + PITCH 2", "track + TRIG 1"):
        case(f"refused: {bad!r}", raises(atoms, bad))
    for s in ("any", "params", "grid", "keys", "page:LFO", "menu:RETRIG", "menu:MIDI-PORTS"):
        case(f"situation {s}", not raises(check_situation, s))
    for s in ("page:FOO", "menu:", "everywhere"):
        case(f"refused situation {s!r}", raises(check_situation, s))
    good = {"sound_slots": [28, {"slots": [29, 31], "scope": "all"}], "record_slots": [30, 31],
            "saved": [{"where": "pattern, track +512", "bytes": 1}], "descriptors": [1, 2], "plock_rows": True,
            "formatters": [{"knob": "Cutoff", "object": 53, "replaces": "0x400456c8", "scope": "all"}],
            "midi": {"cc": [74], "nrpn": ["1:20"]}, "ram": [["0x4233f000", "0x4233f49c"]],
            "views": ["main", {"view": "knob", "how": "a hook"}],
            "gestures": ["RETRIG + COLOR", {"combo": "FUNC + PITCH", "situation": "params", "scope": "machine:MACRO",
                                            "replaces": "FINE"}]}
    claims, errs = normalize(good, "package", ("sampler",))
    case("a package's full set of claims passes", not errs)
    case("a package's default scope is its machine", claims["sound_slots"][0] == (28, "machine")
         and claims["sound_slots"][1] == (29, "all"))
    case("a tweak's default scope is every track", normalize({"sound_slots": [28]}, "tweak")[0]["sound_slots"]
         == [(28, "all")])
    for bad in ({"sound_slot": [28]}, {"sound_slots": [33]}, {"record_slots": [32]}, {"descriptors": [5]},
                {"descriptors": [{"slots": [1, 2]}]}, {"sound_slots": [{"slots": [30, 28]}]},
                {"plock_rows": "yes"}, {"midi": {"cc": [128]}}, {"midi": {"nrpn": ["1:200"]}},
                {"ram": [["0x2000", "0x1000"]]}, {"views": ["browser"]}, {"saved": [{"where": "x", "bytes": 0}]},
                {"gestures": [{"combo": "LFO", "situation": "page:FOO"}]}, {"gestures": [{"combo": "LFO", "why": 1}]},
                {"formatters": [{"knob": "Cutoff", "object": 53}]}):
        case(f"refused: {json.dumps(bad)}", bool(normalize(bad, "package", ("sampler",))[1]))
    case("refused: scope machine in a tweak", bool(normalize({"sound_slots": [{"slots": [28, 28], "scope": "machine"}]},
                                                             "tweak")[1]))
    case("refused: scope machine:FOO",
         bool(normalize({"views": [{"view": "main", "scope": "machine:FOO"}]}, "tweak")[1]))
    case("scope machine:CHORD, machine:MACRO, machine:sampler", not any(
        normalize({"views": [{"view": "main", "scope": f"machine:{n}"}]}, "tweak", ("sampler",))[1]
        for n in ("CHORD", "MACRO", "sampler")))
    ids, pkgs = ["arp", "macro", "macro-tg", "sampler"], {"sampler": {}}
    case("claims.json: a pattern names its tweaks", not check_file(
        {"schema": SCHEMA, "entries": [{"ids": ["macro*"], "source": "notes/55", "claims": {}}]}, ids, pkgs))
    for name, data in (("a pattern that names nothing", {"ids": ["acid"]}), ("a package", {"ids": ["sampler"]}),
                       ("no source", {"ids": ["arp"], "source": ""}), ("an unknown field", {"ids": ["arp"], "x": 1})):
        e = {"source": "notes/32", "claims": {}, **data}
        case(f"claims.json refused: {name}", bool(check_file({"schema": SCHEMA, "entries": [e]}, ids, pkgs)))
    twice = [{"ids": ["macro"], "source": "a", "claims": {}}, {"ids": ["macro*"], "source": "b", "claims": {}}]
    case("claims.json refused: a tweak in two entries",
         bool(check_file({"schema": SCHEMA, "entries": twice}, ids, pkgs)))
    sc = {"shortcut": {"key": "RETRIG", "knobs": ["COLOR", "SHAPE", "SWEEP", "CONTOUR"], "descriptors": [1, 2, 3, 4],
                       "sound_slots": [28, 29, 30, 31], "record_slots": [28, 29, 30, 31]}}
    m = {"uses": [{"point": "shortcut", "key": "RETRIG", "knob": "COLOR"}, {"point": "view.main"}]}
    c = normalize({"sound_slots": [28], "record_slots": [28], "gestures": ["RETRIG + COLOR"], "views": ["main"]},
                  "package")[0]
    case("a shortcut with its combination and slots passes", not check_package(m, c, sc))
    c2 = normalize({"sound_slots": [28], "record_slots": [29], "gestures": [], "views": []}, "package")[0]
    case("a shortcut without its combination, record slot and view is refused", len(check_package(m, c2, sc)) == 3)
    return fails


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="check the data; exit 1 on an error")
    ap.add_argument("--list", action="store_true", help="print each holder's claims")
    ap.add_argument("--self-test", action="store_true", help="the parser and the checks on synthetic claims")
    args = ap.parse_args()
    if not (args.check or args.list or args.self_test):
        ap.error("--check, --list or --self-test")
    status = 0
    if args.self_test:
        fails = self_test()
        print(f"self-test: {'ALL OK' if not fails else f'{fails} FAILED'}")
        status |= bool(fails)
    if args.list:
        pkgs = packages()
        for h in holders():
            print(f"{h['kind']} {h['name']}" + (f" ({len(h['ids'])} tweaks)" if h["kind"] == "tweak" else "")
                  + f": {h['source']}")
            for line in describe(h, pkgs):
                print(f"    {line}")
            for line in h["open"]:
                print(f"    open: {line}")
    if args.check:
        results = check()
        for ok, line in results:
            print(f"  {'ok  ' if ok else 'FAIL'}  {line}")
        fails = sum(not ok for ok, _ in results)
        print("claims: " + ("ALL OK" if not fails else f"{fails} error(s)"))
        status |= bool(fails)
    sys.exit(status)


if __name__ == "__main__":
    main()
