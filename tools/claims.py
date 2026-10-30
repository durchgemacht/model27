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

Step C1 reads and checks the data: the claim types and their values, the words, the ids, and that a manifest's or a
part's claims agree with what it uses. Step C2 adds the rules (rules 2 and 3 of the Cycles Mod Standard, notes/65 §5):
what one holder may not claim (the OS's own slots, a stock combination without "replaces"), and why two holders cannot
go together (clashes). tools/compose.py adds the tweaks a build clashes with to its conflicts and refuses a build whose
own packages clash; tools/check_overlaps.py refuses two tweaks that can be ticked together and clash; the web
flasher's composer applies the same rules to the same data (to_json).

    python3 tools/claims.py --check        # the data and what each holder may not claim; exit 1 on an error
    python3 tools/claims.py --list         # each holder's claims, a combination with its number of atoms
    python3 tools/claims.py --self-test    # the parser, the checks and the rules, on synthetic and real claims
"""
import argparse
import collections
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
KEYS = {"FUNC": 1, "TRACK": 2, "RETRIG": 4, "MACHINES": 5, "PUNCH": 6, "GATE": 7, "LFO": 8, "RECORD": 9, "PLAY": 10,
        "STOP": 11, "PAGE": None, "PATTERN": None}
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
    {"combo": "PUNCH/GATE", "meaning": "switches PUNCH or GATE on the selected track; a held RETRIG is not read",
     "source": "notes/63 §15.1"},
    {"combo": "FUNC + PUNCH/GATE", "meaning": "opens a view", "source": "notes/63 §15.1"},
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
VIEWS = ("main", "knob", "note")      # MainScreenView, the knob view, NoteVelocityView (STANDARD.md §3.1)

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


# --- the rules (step C2) --------------------------------------------------------------------------------------------
#
# The rules read the claims in one JSON form (to_json), the form the web flasher carries too: docs/flasher/composer.js
# applies the same rules to the same data (claimClashes, buildHolders, claimConflicts), and webcompose_check.sh
# compares the conflicts both give.

OS_SOUND = range(0, 23)                         # k 0-22: the stock parameters
OS_RECORD = set(range(0, 24)) - {18}            # record slots 0-23, but 18, which the OS saves into k 0 and drops


def to_json(c):
    """normalize()'s claims as lists of lists; an atom as [held keys joined by "+", action]; empty types left out."""
    out = {}
    for key in ("sound_slots", "record_slots", "descriptors"):
        if c.get(key):
            out[key] = [[n, s] for n, s in c[key]]
    if c.get("saved"):
        out["saved"] = [[w, b, s] for w, b, s in c["saved"]]
    if c.get("formatters"):
        out["formatters"] = [[o, s, k] for o, s, k in c["formatters"]]
    if c.get("plock_rows"):
        out["plock_rows"] = True
    if c.get("midi") and (c["midi"]["cc"] or c["midi"]["nrpn"]):
        out["midi"] = {"cc": list(c["midi"]["cc"]), "nrpn": list(c["midi"]["nrpn"])}
    if c.get("ram"):
        out["ram"] = [[lo, hi] for lo, hi in c["ram"]]
    if c.get("views"):
        out["views"] = [[v, s, h] for v, s, h in c["views"]]
    if c.get("gestures"):
        out["gestures"] = [{"combo": g["combo"], "atoms": [["+".join(sorted(h)), a] for h, a in g["atoms"]],
                            "situation": g["situation"], "scope": g["scope"], "meaning": g["meaning"],
                            "replaces": g["replaces"]} for g in c["gestures"]]
    return out


def checked(claims, kind, name, pkgs):
    """normalize() then to_json(), or stop on an error (claims.py --check names it)."""
    c, errors = normalize(claims, kind, pkgs)
    if errors:
        sys.exit(f"!! {kind} {name}: {'; '.join(errors)} (python3 tools/claims.py --check)")
    return to_json(c)


def own_scope(m):
    """The machine a package's scope "machine" names: its id for an added machine; for an extension of a stock
    machine ("machine.stock", notes/66 §3), that machine (machine:CHORD)."""
    stock = next((u for u in m.get("uses", []) if u.get("point") == "machine.stock"), None)
    return stock["machine"] if stock else m["id"]


def resolve(c, pid):
    """A package's claims with its machine named: the scope "machine" becomes "machine:<id>" (pid: own_scope())."""
    def s(x):
        return f"machine:{pid}" if x == "machine" else x
    out = dict(c)
    for key in ("sound_slots", "record_slots", "descriptors"):
        if key in c:
            out[key] = [[n, s(t)] for n, t in c[key]]
    if "saved" in c:
        out["saved"] = [[w, b, s(t)] for w, b, t in c["saved"]]
    if "formatters" in c:
        out["formatters"] = [[o, s(t), k] for o, t, k in c["formatters"]]
    if "views" in c:
        out["views"] = [[v, s(t), h] for v, t, h in c["views"]]
    if "gestures" in c:
        out["gestures"] = [dict(g, scope=s(g["scope"])) for g in c["gestures"]]
    return out


def merge(a, b):
    """The claims of two holders together, as one tweak carries them (a package and the shortcut layer)."""
    out = {k: list(a.get(k, [])) + list(b.get(k, [])) for k in set(a) | set(b) if k not in ("plock_rows", "midi")}
    if a.get("plock_rows") or b.get("plock_rows"):
        out["plock_rows"] = True
    if a.get("midi") or b.get("midi"):
        ma, mb = a.get("midi", {}), b.get("midi", {})
        out["midi"] = {"cc": ma.get("cc", []) + mb.get("cc", []), "nrpn": ma.get("nrpn", []) + mb.get("nrpn", [])}
    return out


def meet(s, t):
    """Do two scopes share a track: all meets everything, a machine meets itself."""
    return s == "all" or t == "all" or s == t


def situations_meet(s, t):
    return s == "any" or t == "any" or s == t


def clash_items(a, b):
    """Why two holders' claims (to_json, resolved) cannot be installed together, by notes/65 §5: the same sound
    slot, record slot, saved bytes or descriptor in scopes that meet; the same interface object's formatter, whatever
    the scopes (one pointer per object, §12.2); both re-numbering the p-lock rows; the same CC or NRPN; RAM that
    overlaps; a shared atom in situations and scopes that meet, with another meaning. As (kind, text, the shared
    atoms or None); empty when they can."""
    out = []
    for key, label, kind in (("sound_slots", "k", "slots"), ("record_slots", "record slots", "slots"),
                             ("descriptors", "descriptors", "descriptors")):
        hit = sorted({n for n, s in a.get(key, []) for m, t in b.get(key, []) if n == m and meet(s, t)})
        if hit:
            out.append((kind, f"{label} {_ranges(hit)}", None))
    for w in sorted({w for w, _n, s in a.get("saved", []) for w2, _m, t in b.get("saved", [])
                     if w == w2 and meet(s, t)}):
        out.append(("saved", f"saved bytes: {w}", None))
    for o in sorted({o for o, _s, _k in a.get("formatters", []) for o2, _t, _l in b.get("formatters", []) if o == o2}):
        out.append(("formatter", f"the formatter of interface object {o}", None))
    if a.get("plock_rows") and b.get("plock_rows"):
        out.append(("plock", "the p-lock rows of k >= 23", None))
    ma, mb = a.get("midi", {}), b.get("midi", {})
    cc = sorted(set(ma.get("cc", [])) & set(mb.get("cc", [])))
    nrpn = sorted(set(ma.get("nrpn", [])) & set(mb.get("nrpn", [])))
    if cc:
        out.append(("midi", "CC " + ", ".join(map(str, cc)), None))
    if nrpn:
        out.append(("midi", "NRPN " + ", ".join(nrpn), None))
    for lo, hi in a.get("ram", []):
        for lo2, hi2 in b.get("ram", []):
            if lo < hi2 and lo2 < hi:
                out.append(("ram", f"RAM {max(lo, lo2):#x}..{min(hi, hi2):#x}", None))
    for g in a.get("gestures", []):
        for h in b.get("gestures", []):
            if not (meet(g["scope"], h["scope"]) and situations_meet(g["situation"], h["situation"])):
                continue
            if g["meaning"] and g["meaning"] == h["meaning"]:
                continue                        # the same claim twice is allowed (STANDARD.md §3.2)
            shared = {tuple(x) for x in g["atoms"]} & {tuple(x) for x in h["atoms"]}
            if shared:
                out.append(("combo", f"{g['combo']} against {h['combo']}", shared))
    return out


def clashes(a, b):
    """clash_items() as texts, for the tools' messages and reports."""
    return [text for _kind, text, _atoms in clash_items(a, b)]


def combo_text(atoms_):
    """Atoms (to_json form) as a combination the way the tables write it: "MACHINES + SWEEP/CONTOUR",
    "TRACK + TRIG 1-6", "TRIG 1-16 + PAGE"."""
    order = {w: i for i, w in enumerate([*KNOBS, *KEYS, *OTHER])}     # knobs as on the panel, then keys

    def trigs(words):                       # TRIG 1, TRIG 2, TRIG 3 -> TRIG 1-3
        nums = sorted(int(w[5:]) for w in words if w.startswith("TRIG "))
        rest = sorted((w for w in words if not w.startswith("TRIG ")), key=lambda w: (order.get(w, 99), w))
        return rest + ([f"TRIG {r}" for r in _ranges(nums).split(", ")] if nums else [])
    by_held = collections.defaultdict(set)
    for held, action in atoms_:
        by_held[held].add(action)
    by_actions = collections.defaultdict(set)   # the same actions under several held keys: one part
    for held, actions in by_held.items():
        by_actions["/".join(trigs(actions))].add(held)
    parts = []
    for actions, helds in sorted(by_actions.items()):
        if helds == {""}:
            parts.append(actions)
            continue
        singles = [h for h in helds if "+" not in h]
        multi = sorted(h for h in helds if "+" in h)
        if singles:
            parts.append(" + ".join(["/".join(trigs(singles)), actions]))
        parts += [" + ".join(h.split("+") + [actions]) for h in multi]
    return ", ".join(parts)


def clash_kinds(a, b):
    """The kinds of clash between two holders, each once and in order, for the web flasher's computed reasons
    (notes/65, step C4): [kind, the shared combination or ""], kind one of slots, saved, descriptors, formatter,
    plock, midi, ram, combo."""
    out, seen = [], set()
    for kind, _text, shared in clash_items(a, b):
        if kind not in seen:
            seen.add(kind)
            out.append([kind, combo_text(shared) if shared else ""])
    return out


def view_warnings(a, b):
    """Views both draw in scopes that meet, outside the dispatchers: a warning, not a conflict (notes/65 §5.4)."""
    return sorted({f"view {v}" for v, s, _h in a.get("views", []) for w, t, _i in b.get("views", [])
                   if v == w and meet(s, t)})


def stock_atoms():
    """The stock list as (combination, meaning, situation, set of atoms in the to_json form)."""
    return [(s["combo"], s["meaning"], s.get("situation", "any"),
             {("+".join(sorted(h)), a) for h, a in atoms(s["combo"])}) for s in STOCK]


def own_errors(c):
    """What one holder may not claim: the OS's own slots, and a stock combination without "replaces"."""
    errors = []
    k = sorted({n for n, _s in c.get("sound_slots", []) if n in OS_SOUND})
    if k:
        errors.append(f"k {_ranges(k)}: the OS's own")
    r = sorted({n for n, _s in c.get("record_slots", []) if n in OS_RECORD})
    if r:
        errors.append(f"record slots {_ranges(r)}: the OS's own")
    for g in c.get("gestures", []):
        if g["replaces"]:
            continue
        for combo, meaning, situation, stock in stock_atoms():
            if situations_meet(g["situation"], situation) and {tuple(x) for x in g["atoms"]} & stock:
                errors.append(f"{g['combo']} takes the stock {combo} ({meaning}) without saying what it replaces")
                break
    return errors


def package_claims(m, pkgs=None):
    """A package's claims, to_json, the scope "machine" not yet named."""
    return checked(m.get("claims", {}), "package", m["id"], packages() if pkgs is None else pkgs)


def part_claims(p):
    return checked(p.get("claims", {}), "part", p["id"], ())


def beyond_shortcuts(c, m, part):
    """A package's claims without what its shortcuts take through the shortcut layer: the knob's slot k, its record
    slot and its combination; for a switch (notes/63 §16) k 32, record slot 18 and its combination. Those are the
    layer's claims narrowed to the machine (notes/65 §5.5), so they are not compared with the layer."""
    sc = part["shortcut"]
    ks, rs, own = set(), set(), set()
    for u in m["uses"]:
        if u["point"] == "shortcut" and u.get("knob") in sc["knobs"]:
            i = sc["knobs"].index(u["knob"])
            ks.add(sc["sound_slots"][i])
            rs.add(sc["record_slots"][i])
            own.add((u["key"], u["knob"]))
        elif u["point"] == "shortcut" and u.get("press") in sc.get("presses", ()):
            ks.add(sc["press_sound_slot"])
            rs.add(sc["press_record_slot"])
            own.add((u["key"], u["press"]))
    out = dict(c)
    if "sound_slots" in c:
        out["sound_slots"] = [x for x in c["sound_slots"] if x[0] not in ks]
    if "record_slots" in c:
        out["record_slots"] = [x for x in c["record_slots"] if x[0] not in rs]
    if "gestures" in c:
        out["gestures"] = [g for g in c["gestures"] if not all(tuple(x) in own for x in g["atoms"])]
    return out


def build_holders(mans, part=None):
    """The holders of one build's claims: each package with its machine named, then the shortcut layer when the
    build carries it. Each as (name, claims, claims to compare with the parts, is a part)."""
    out = []
    pkgs = packages()
    for m in mans:
        c = resolve(package_claims(m, pkgs), own_scope(m))
        out.append((m["id"], c, beyond_shortcuts(c, m, part) if part else c, False))
    if part:
        c = part_claims(part)
        out.append((part["id"], c, c, True))
    return out


def check_build(holders):
    """Two holders of one build that clash: [reason]. A package meets a part with its claims beyond the part's."""
    out = []
    for (a, ca, xa, pa), (b, cb, xb, pb) in itertools.combinations(holders, 2):
        why = clashes(xa if pb else ca, xb if pa else cb)
        if why:
            out.append(f"{a} and {b}: {', '.join(why)}")
    return out


def claim_conflicts(holders, against):
    """{tweak id: reasons} for the tweaks of against ({id: claims}) whose claims clash with a holder of the build."""
    out = {}
    for tid, tc in against.items():
        why = [w for _n, c, _x, _p in holders for w in clashes(c, tc)]
        if why:
            out[tid] = why
    return out


def claim_views(holders, against):
    """{tweak id: views} the build and a tweak both draw, a warning."""
    out = {}
    for tid, tc in against.items():
        why = sorted({w for _n, c, _x, _p in holders for w in view_warnings(c, tc)})
        if why:
            out[tid] = why
    return out


def tweak_claims():
    """{id: claims} (to_json, resolved) of the folder's tweaks that claim something: the entries of claims.json, and
    each package's own tweak, with the shortcut layer's claims when the package declares a shortcut (its committed
    tweak carries the layer)."""
    ids, pkgs = folder_ids(), packages()
    out = {}
    for e in json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))["entries"]:
        c = checked(e["claims"], "tweak", ", ".join(e["ids"]), pkgs)
        for pat in e["ids"]:
            for i in fnmatch.filter(ids, pat):
                out[i] = c
    part = parts().get("shortcuts")
    for pid, m in pkgs.items():
        if pid in ids:
            c = resolve(package_claims(m, pkgs), own_scope(m))
            if part and any(u["point"] == "shortcut" for u in m["uses"]):
                c = merge(c, part_claims(part))
            if c:
                out[pid] = c
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
    """A manifest's claims against its uses: the RAM of memory.ram and memory.sram (the OS's SRAM a stock machine's
    extension takes from it, notes/66 §19.5), the views of view.*, and for each shortcut its key combination, sound
    slot and record slot (the part's list gives the slot of each knob)."""
    errors = []
    uses = m.get("uses", [])
    ram = sorted((int(a, 16), int(b, 16)) for u in uses if u.get("point") in ("memory.ram", "memory.sram")
                 for a, b in [u["range"]])
    if ram != sorted(claims.get("ram", [])):
        errors.append("claims.ram is not the RAM of its uses (memory.ram, memory.sram)")
    views = sorted(u["point"][5:] for u in uses if u.get("point") in ("view.main", "view.knob", "view.note"))
    if views != sorted(v for v, _s, _h in claims.get("views", [])):
        errors.append("claims.views are not the views of its uses (view.main, view.knob, view.note)")
    sc = shortcut_part["shortcut"] if shortcut_part else None
    for u in (u for u in uses if u.get("point") == "shortcut"):
        what = u.get("press", u.get("knob"))
        if "press" in u:                     # a switch (notes/63 §16): k 32 and record slot 18 for both presses
            on_list = sc and u["press"] in sc.get("presses", ()) and "knob" not in u
            slots = (sc["press_sound_slot"], sc["press_record_slot"]) if on_list else None
        else:
            on_list = sc and u.get("knob") in sc["knobs"]
            slots = (sc["sound_slots"][sc["knobs"].index(u["knob"])],
                     sc["record_slots"][sc["knobs"].index(u["knob"])]) if on_list else None
        if not on_list or u.get("key") != sc["key"]:
            errors.append(f"shortcut {u.get('key')} + {what} is not on the builder's list")
            continue
        want = set(atoms(f"{u['key']} + {what}"))
        if not any(want <= set(g["atoms"]) for g in claims.get("gestures", [])):
            errors.append(f"shortcut {u['key']} + {what}: no gesture claims it")
        if slots[0] not in {n for n, _s in claims.get("sound_slots", [])}:
            errors.append(f"shortcut {u['key']} + {what}: k {slots[0]} is not claimed")
        if slots[1] not in {n for n, _s in claims.get("record_slots", [])}:
            errors.append(f"shortcut {u['key']} + {what}: record slot {slots[1]} is not claimed")
    return errors


def check_shortcut_part(p, claims):
    """The shortcut layer's claims against its own list: its slots, descriptors and combinations, the switches' too
    (notes/63 §16)."""
    sc, errors = p["shortcut"], []
    presses = sc.get("presses", [])
    for key, want in (("sound_slots", sc["sound_slots"] + ([sc["press_sound_slot"]] if presses else [])),
                      ("record_slots", sc["record_slots"] + ([sc["press_record_slot"]] if presses else [])),
                      ("descriptors", sc["descriptors"])):
        if sorted(n for n, _s in claims.get(key, [])) != sorted(want):
            errors.append(f"claims.{key} are not the layer's {key} {sorted(want)}")
    want = {a for k in sc["knobs"] + presses for a in atoms(f"{sc['key']} + {k}")}
    if not want <= {a for g in claims.get("gestures", []) for a in g["atoms"]}:
        errors.append(f"claims.gestures do not hold {sc['key']} + each of {', '.join(sc['knobs'] + presses)}")
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
        errs += own_errors(to_json(claims))
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
    sc["shortcut"].update(presses=["PUNCH", "GATE"], press_sound_slot=32, press_record_slot=18)
    mp = {"uses": [{"point": "shortcut", "key": "RETRIG", "press": "GATE"}]}
    cp = normalize({"sound_slots": [32], "record_slots": [18], "gestures": ["RETRIG + GATE"]}, "package")[0]
    case("a switch with its combination, k 32 and record slot 18 passes", not check_package(mp, cp, sc))
    case("a switch claiming RETRIG + PUNCH instead of GATE is refused",
         len(check_package(mp, normalize({"sound_slots": [32], "record_slots": [18], "gestures": ["RETRIG + PUNCH"]},
                                         "package")[0], sc)) == 1)
    case("a press off the list (RETRIG + LFO) is refused",
         check_package({"uses": [{"point": "shortcut", "key": "RETRIG", "press": "LFO"}]}, cp, sc)
         == ["shortcut RETRIG + LFO is not on the builder's list"])
    case("a press with a knob is refused",
         len(check_package({"uses": [{"point": "shortcut", "key": "RETRIG", "press": "GATE", "knob": "COLOR"}]},
                           cp, sc)) == 1)
    case("GATE is key 7 (notes/63 §15.1), RETRIG + PUNCH/GATE two atoms held by RETRIG",
         KEYS["GATE"] == 7 and atoms("RETRIG + PUNCH/GATE") == [(frozenset({"RETRIG"}), "GATE"),
                                                                (frozenset({"RETRIG"}), "PUNCH")])

    # --- the rules (C2): the cases of notes/65 §2 and §7 on the folder's real claims, then synthetic ones
    def j(claims, kind="tweak"):
        return to_json(normalize(claims, kind, ("sampler",))[0])
    real, pkgs, sc_part = tweak_claims(), packages(), parts()["shortcuts"]
    layer = part_claims(sc_part)
    case("lfo-plus × the track filter: k 28-31, record slots 30-31, the p-lock rows",
         clashes(real["lfo-plus"], real["track-filter"]) == ["k 28-31", "record slots 30-31",
                                                              "the p-lock rows of k >= 23"])
    case("lfo-plus × the shortcut layer: k 28-32 (k 32 since the switches), record slots 30-31",
         clashes(real["lfo-plus"], layer) == ["k 28-32", "record slots 30-31"])
    case("the track filter × the shortcut layer: record slot 18 too, since the switches",
         "record slots 18, 30-31" in clashes(real["track-filter"], layer))
    case("lfo-plus × REF2's tweak, which carries the layer: a clash",
         bool(clashes(real["lfo-plus"], real["refmachine2"])))
    probe = j({"gestures": [{"combo": "TRACK + TRIG 3", "situation": "keys", "meaning": "a probe"}]})
    case("control-all-config × TRACK + TRIG 3 in keys: a clash", bool(clashes(real["control-all-config"], probe)))
    case("the track filter × Model-TG: record slot 27, MACHINES + SWEEP and + CONTOUR",
         clashes(real["track-filter"], real["model-tg"]) == [
             "record slots 27", "MACHINES + COLOR/SHAPE/SWEEP/CONTOUR against MACHINES + DECAY/SWEEP/CONTOUR"])
    case("SAMPLE × Model-TG: k 25-27, record slots 24-27",
         clashes(real["sampler"], real["model-tg"]) == ["k 25-27", "record slots 24-27"])
    case("SAMPLE × the track filter: record slot 27",
         clashes(real["sampler"], real["track-filter"]) == ["record slots 27"])
    case("REF2 × arp: no clash (RETRIG + NOTES is another atom)", not clashes(real["refmachine2"], real["arp"]))
    case("SAMPLE × REF2: no clash", not clashes(real["sampler"], real["refmachine2"]))
    octave, tune = (j({"gestures": [{"combo": "RETRIG + COLOR", "situation": "params", "meaning": x}]}, "package")
                    for x in ("Octave", "Tune"))
    case("two machines' RETRIG + COLOR do not clash", not clashes(resolve(octave, "a"), resolve(tune, "b")))
    case("one machine's two meanings of RETRIG + COLOR do", bool(clashes(resolve(octave, "a"), resolve(tune, "a"))))
    lofi = j({"gestures": [{"combo": "FUNC + PITCH", "situation": "params", "meaning": "lo-fi", "replaces": "FINE"}]})
    case("the same claim twice is allowed", not clashes(lofi, lofi))
    fa, fb = (resolve(j({"formatters": [{"knob": "X", "object": 53, "replaces": "0x400456c8"}]}, "package"), x)
              for x in ("a", "b"))
    case("two formatters on one interface object clash, whatever their scopes", bool(clashes(fa, fb)))
    chord = j({"sound_slots": [{"slots": [25, 25], "scope": "machine:CHORD"}]})
    case("k 25 on CHORD's tracks × SAMPLE's k 25: no clash", not clashes(chord, real["sampler"]))
    menu = j({"gestures": [{"combo": "RETRIG + COLOR", "situation": "menu:RETRIG", "meaning": "a probe"}]})
    case("RETRIG + COLOR in menu:RETRIG × the layer's in params: no clash", not clashes(menu, layer))
    va, vb = j({"views": ["main"]}), j({"views": [{"view": "main", "how": "a probe"}]})
    case("two drawings of one view: a warning, not a clash",
         not clashes(va, vb) and view_warnings(va, vb) == ["view main"])
    case("refused: k 22 and record slot 5, the OS's; record slot 18 allowed",
         own_errors(j({"sound_slots": [22], "record_slots": [5, 18]})) == ["k 22: the OS's own",
                                                                           "record slots 5: the OS's own"])
    case("refused: FUNC + PITCH without replaces",
         bool(own_errors(j({"gestures": [{"combo": "FUNC + PITCH", "situation": "params"}]}))))
    case("FUNC + PITCH with replaces: allowed", not own_errors(lofi))
    case("FUNC + PITCH in menu:RETRIG: not the stock one", not own_errors(
        j({"gestures": [{"combo": "FUNC + PITCH", "situation": "menu:RETRIG"}]})))
    ref2 = pkgs["refmachine2"]
    case("a build of REF2 and the layer: no clash", not check_build(build_holders([ref2], sc_part)))
    case("a build of SAMPLE, REF2 and the layer: no clash",
         not check_build(build_holders([pkgs["sampler"], ref2], sc_part)))
    x30 = {"id": "x", "uses": [{"point": "shortcut", "key": "RETRIG", "knob": "COLOR"}],
           "claims": {"sound_slots": [28, 30], "record_slots": [28]}}
    case("a package's own k 30 next to its shortcut on COLOR: a clash with the layer",
         check_build(build_holders([x30], sc_part)) == ["x and shortcuts: k 30"])
    case("the kinds of lfo-plus × the track filter: slots, p-lock rows",
         clash_kinds(real["lfo-plus"], real["track-filter"]) == [["slots", ""], ["plock", ""]])
    case("the kinds of the track filter × Model-TG: slots, the shared MACHINES + SWEEP/CONTOUR",
         clash_kinds(real["track-filter"], real["model-tg"]) == [["slots", ""],
                                                               ["combo", "MACHINES + SWEEP/CONTOUR"]])
    texts = [combo_text({("+".join(sorted(h)), x) for h, x in atoms(c)})
             for c in ("TRACK + TRIG 2-4", "TRIG 1-16 + PAGE", "LFO")]
    case("combo_text: TRACK + TRIG 2-4, TRIG 1-16 + PAGE, LFO",
         texts == ["TRACK + TRIG 2-4", "TRIG 1-16 + PAGE", "LFO"])
    case("claim_conflicts names the tweak and its reasons",
         claim_conflicts(build_holders([ref2], sc_part), {"lfo-plus": real["lfo-plus"], "arp": real["arp"]})
         == {"lfo-plus": ["k 28, 32", "k 28-32", "record slots 30-31"]})
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
