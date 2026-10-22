#!/usr/bin/env python3
"""Registre de la place libre et des points d'accroche des mods (notes/52).

Construit tweaks/model-cycles_OS1.13/REGISTRY.md à partir des tweaks eux-mêmes (leurs écritures), sans aucun fichier
d'Elektron : qui utilise quel masque de sprite libéré (tools/sprites.py), quelle zone 0xFF, quelle charge utile
ajoutée après l'OS, quel crochet de l'OS et quel pointeur réécrit ; et ce qui reste libre. C'est ce qu'un auteur de
mod consulte avant de prendre de la place, et ce que tools/check_overlaps.py (notes/49) ne dit pas : lui refuse deux
écritures aux mêmes octets, ici on voit les zones et ce qui reste.

Vérifie en même temps, et refuse (exit 1) :
  - une écriture dans un masque libérable sans l'écriture qui redirige son sprite (sprites.redirect_write), dans le
    même tweak ou dans un tweak qu'il demande (« requires ») : le sprite afficherait le code du mod ;
  - une écriture dans la copie gardée d'un groupe de masques : tous les sprites redirigés la lisent ;
  - une redirection qui ne vise pas la copie gardée.
Signale (sans refuser) une redirection sans écriture dans le masque.

    python3 tools/registry.py                         # réécrit REGISTRY.md
    python3 tools/registry.py --check                 # REGISTRY.md est-il à jour ? (validation avant push)
    python3 tools/registry.py --git origin/claude/x   # à l'écran, avec les tweaks d'autres branches (répétable)
    python3 tools/registry.py --cycles firmware/model-cycles_OS1.13.syx
                                                      # vérifie aussi le relevé des masques sur l'OS officiel :
                                                      # copies identiques, une seule référence (la constante), 0xFF

Avec --git, les tweaks du dépôt et des branches sont réunis comme dans check_overlaps.py (deux versions d'un même id
deviennent id@source) ; le registre montre alors qui, parmi les branches ouvertes, a pris quelle zone.

Le classement d'une écriture se lit dans ses octets : redirection (la constante d'un sprite passe à la copie gardée),
masque (dans un masque libérable), cave (octets 0xFF d'origine), crochet (jsr, jmp, bsr.l ou bra.l remplace les
instructions de l'OS), pointeur (constante 32 bits vers le code d'un mod), patch (tout le reste).

model27, notes/65 (step C3): §6 (the saved data) and §8 to §10 (the key combinations; the descriptors, formatters,
p-lock rows and MIDI numbers; the views) come from the declared claims (tools/claims.py: the packages' manifests, the
parts' part.json, the tweaks' claims/claims.json), which replace the table DECLARED this script kept.
"""
import argparse
import collections
import fnmatch
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_overlaps as co          # noqa: E402
import claims as cl                   # noqa: E402
import sprites                       # noqa: E402

ROOT = co.ROOT
BASE = co.BASE
END_LIMIT = co.END_LIMIT
OUT = ROOT / "tweaks" / co.DEV / "REGISTRY.md"
DETOURS = {0x4EB9: "jsr", 0x4EF9: "jmp", 0x61FF: "bsr.l", 0x60FF: "bra.l"}
ENGINE = re.compile(r"^(syntakt-(?:tg-)?)(?:sd|cp|toy|bits|swarm|meter|profile)(?:-(?:sd|cp|toy|bits|swarm))*"
                    r"((?:-macro)?(?:-acid)?)$")



def fmt(n):
    """Nombre avec séparateur des milliers à la française."""
    return f"{n:,}".replace(",", " ")


def family(tid):
    """Les combinaisons de moteurs du Syntakt se résument à huit familles : syntakt-*, syntakt-tg-* et, avec la
    machine MACRO (notes/50), ACID (notes/54 §11) ou les deux, syntakt-*-macro, -acid, -macro-acid et leurs -tg."""
    m = ENGINE.match(tid)
    return m[1] + "*" + (m[2] or "") if m else tid


def names(ids, by_id, extra=None):
    """Liste de mods lisible : les familles de moteurs regroupées (présents/total), avec un détail par mod (extra[id])
    résumé en plage pour une famille."""
    fams = collections.defaultdict(list)
    for i in ids:
        fams[family(i)].append(i)
    out = []
    for f in sorted(fams):
        ms = sorted(fams[f])
        if "*" in f:
            total = sum(1 for i in by_id if family(i) == f)
            s = f"{f} ({len(ms)}/{total}"
            if extra:
                vs = sorted(extra[i] for i in ms)
                s += f", {vs[0]} o" if vs[0] == vs[-1] else f", {vs[0]}–{vs[-1]} o"
            out.append(s + ")")
        else:
            out.append(f"{ms[0]} ({extra[ms[0]]} o)" if extra else ms[0])
    return ", ".join(out)


# model27, Level C (notes/65, step C3): the claims' sections of the registry.

def claim_holders(by_id):
    """The holders of declared claims among these tweaks, as (label, claims in claims.to_json form, source): the
    entries of claims/claims.json, each package whose tweak is here, and the shortcut layer, which the builds whose
    machines declare a shortcut carry."""
    pkgs = cl.packages()
    out = []
    for e in json.loads(cl.CLAIMS_FILE.read_text(encoding="utf-8"))["entries"]:
        ids = sorted({i for pat in e["ids"] for i in fnmatch.filter(list(by_id), pat)})
        if ids:
            out.append((names(ids, by_id), cl.checked(e["claims"], "tweak", ", ".join(e["ids"]), pkgs), e["source"]))
    for pid, m in pkgs.items():
        c = cl.resolve(cl.package_claims(m, pkgs), pid) if pid in by_id else None
        if c:                                            # a package that claims something
            out.append((pid, c, f"tools/machines/{pid}/manifest.json"))
    part = cl.parts().get("shortcuts")
    if part and part.get("claims"):
        out.append(("shortcuts (part)", cl.part_claims(part), "tools/machines/shortcuts/part.json"))
    return sorted(out)


def scope_text(s, what):
    """A claim's scope in the tables: nothing for every track, " (SAMPLE's sounds)" for a machine's."""
    if s == "all":
        return ""
    name = s.split(":", 1)[1]
    m = cl.packages().get(name)
    if m:
        name = next(u["name"] for u in m["uses"] if u["point"] == "machine")
    return f" ({name}'s {what})"


def merged_rows(by_n):
    """[(numbers, holders)] from {number: [holder]}: consecutive numbers with the same holders in one row."""
    rows = []
    for n in sorted(by_n):
        hs = "; ".join(sorted(set(by_n[n])))
        if rows and rows[-1][2] == hs and rows[-1][1] == n - 1:
            rows[-1][1] = n
        else:
            rows.append([n, n, hs])
    return [(f"{a}" if a == b else f"{a}–{b}", hs) for a, b, hs in rows]


def claims_lines(holders):
    """§6 (the saved data) and §8 to §10 (the key combinations; the descriptors, formatters, p-lock rows and MIDI;
    the views) of the registry, from the declared claims: (lines of §6, lines of §8 to §10)."""
    six, rest = [], []
    p = six.append
    p("## 6. Saved data (declared claims, notes/65)")
    p("")
    p("What the writes do not show: where each mod keeps its values, in a sound's parameters (k), in a sound's record "
      "and elsewhere in the saved structures. From the declared claims (`tools/claims.py`: a package's manifest, a "
      "part's `part.json`, the tweaks' `claims/claims.json`): a mod that keeps a value adds its claim there, with its "
      "note. A value scoped to a machine is kept on that machine's sounds only. Two mods that can be ticked together "
      "never share a number in scopes that meet (`tools/check_overlaps.py`). The RAM where payloads run is in §3; the "
      "state mods keep in their masks, in §1.")
    p("")
    record = "Record slots (`+28 + 2 · slot` of a sound's record)"
    for key, title, head, os_numbers in (("sound_slots", "Sound parameters k", "k", range(0, 23)),
                                          ("record_slots", record, "slot", sorted(cl.OS_RECORD))):
        by_n = {n: ["the OS"] for n in os_numbers}
        for label, c, _src in holders:
            for n, s in c.get(key, []):
                by_n.setdefault(n, []).append(label + scope_text(s, "sounds"))
        p(f"### {title}")
        p("")
        p(f"| {head} | held by |")
        p("|---|---|")
        for ns, hs in merged_rows(by_n):
            p(f"| {ns} | {hs} |")
        p("")
    p("### Other saved bytes, and RAM outside the payloads")
    p("")
    p("| mod | what | source |")
    p("|---|---|---|")
    for label, c, src in holders:
        for w, b, s in c.get("saved", []):
            p(f"| {label}{scope_text(s, 'tracks')} | {w}: {b} byte{'s' if b > 1 else ''} | {src} |")
        for lo, hi in c.get("ram", []):
            p(f"| {label} | RAM `{lo:#x}`..`{hi:#x}` | {src} |")
    p("")

    p = rest.append
    p("## 8. Key combinations (declared claims, notes/65)")
    p("")
    p("The combinations each mod answers: the held keys, then one action, in the words `tools/claims.py` lists. Two "
      "mods that can be ticked together never take one combination with another meaning in situations and scopes that "
      "meet (`tools/check_overlaps.py`). A mod that takes a stock combination (the second table) says what it "
      "replaces, or `tools/claims.py --check` refuses it.")
    p("")
    p("| combination | situation | held by | meaning | replaces |")
    p("|---|---|---|---|---|")
    for row in sorted((g["combo"], g["situation"], label + scope_text(g["scope"], "tracks"), g["meaning"],
                       g["replaces"] or "") for label, c, _src in holders for g in c.get("gestures", [])):
        p("| " + " | ".join(row) + " |")
    p("")
    p("The stock combinations, as far as they are read:")
    p("")
    p("| combination | situation | meaning | source |")
    p("|---|---|---|---|")
    for st in cl.STOCK:
        p(f"| {st['combo']} | {st.get('situation', 'any')} | {st['meaning']}"
          f"{' (a hypothesis)' if st.get('hyp') else ''} | {st['source']} |")
    p("")
    p("## 9. Descriptors, formatters, p-lock rows and MIDI (declared claims, notes/65)")
    p("")
    p("Two mods that can be ticked together never share one of these in scopes that meet; a formatter belongs to its "
      "interface object, whatever the scopes (notes/65 §12.2). The stock CC and NRPN map is not collected "
      "(STANDARD.md §5.5): a MIDI claim is checked against the other mods only.")
    p("")
    p("| claim | held by |")
    p("|---|---|")
    desc = collections.defaultdict(list)
    for label, c, _src in holders:
        for n, s in c.get("descriptors", []):
            desc[n].append(label + scope_text(s, "tracks"))
    for ns, hs in merged_rows(desc):
        p(f"| descriptors {ns} | {hs} |")
    fmts = collections.defaultdict(list)
    for label, c, _src in holders:
        for o, _s, knob in c.get("formatters", []):
            fmts[o].append(f"{label} ({knob})")
    for o in sorted(fmts):
        p(f"| the formatter of interface object {o} | {'; '.join(sorted(fmts[o]))} |")
    plock = [label for label, c, _src in holders if c.get("plock_rows")]
    if plock:
        p(f"| the p-lock rows of k ≥ 23 | {'; '.join(plock)} |")
    for kind, order in (("cc", int), ("nrpn", lambda x: tuple(map(int, x.split(":"))))):
        groups = collections.defaultdict(set)
        for label, c, _src in holders:
            for x in c.get("midi", {}).get(kind, []):
                groups[x].add(label)
        rows = collections.defaultdict(list)
        for x, labels in groups.items():
            rows["; ".join(sorted(labels))].append(x)
        for hs, xs in sorted(rows.items()):
            p(f"| {kind.upper()} {', '.join(str(x) for x in sorted(xs, key=order))} | {hs} |")
    p("")
    p("## 10. Views (declared claims, notes/65)")
    p("")
    p("A machine draws on its own tracks; when two machines are built together, their draws go through the "
      "dispatchers (notes/63 §4). A draw on every track next to a machine's is a warning, not a conflict (notes/65 "
      "§5.4): only a look on the device tells whether they share the screen well.")
    p("")
    p("| view | drawn by |")
    p("|---|---|")
    views = collections.defaultdict(list)
    for label, c, _src in holders:
        for v, s, how in c.get("views", []):
            views[v].append(label + (scope_text(s, "tracks") or " (every track)") + (f": {how}" if how else ""))
    for v in sorted(views):
        p(f"| {v} | {'; '.join(sorted(views[v]))} |")
    p("")
    return six, rest


def note_of(t):
    """La note que nomme la description du tweak (sa dernière ligne, par convention)."""
    d = t.get("description", "")
    d = " ".join(d) if isinstance(d, list) else d
    m = re.findall(r"notes/\d+", d)
    return m[-1] if m else ""


class Zones:
    """Les zones connues (masques de sprites.MASKS, copies gardées, charges utiles) et où tombe une adresse."""

    def __init__(self, tweaks):
        self.masks = sprites.MASKS
        self.kept = {sprites.SHARED_MASK: 1040}            # va gardée -> taille
        for (_w, _h), (size, kept, _rows) in sprites.GROUPS.items():
            self.kept[kept] = size
        self.consts = {c: va for va, (_s, c, *_r) in self.masks.items()}
        self.payloads = []                                 # (lo, hi, id, "image"/"mémoire")
        for t in tweaks:
            ap = t.get("append")
            if ap:
                at, dest = int(ap["at"], 16), int(ap["dest"], 16)
                self.payloads.append((at, at + co.chunk_len(ap), t["id"], "image"))
                self.payloads.append((dest, dest + ap["size"], t["id"], "mémoire"))
        self.caves = set()                                 # (lo, hi) des écritures dans des octets 0xFF

    def mask_of(self, va):
        for m, (size, *_r) in self.masks.items():
            if m <= va < m + size:
                return m
        return None

    def kept_of(self, va):
        for k, size in self.kept.items():
            if k <= va < k + size:
                return k
        return None

    def place(self, va, tid=None):
        """Où tombe une adresse visée : (genre, zone, décalage). genre : mask, payload, cave, os, ram."""
        m = self.mask_of(va)
        if m is not None:
            return "mask", f"masque `{m:#x}`", va - m
        for lo, hi, pid, kind in self.payloads:
            if lo <= va < hi and (tid is None or pid == tid or family(pid) == family(tid)):
                return "payload", f"charge utile ({kind})", va - lo
        for lo, hi in self.caves:
            if lo <= va < hi:
                return "cave", f"cave `{lo:#x}`", va - lo
        if BASE <= va < END_LIMIT:
            return "os", "OS", va
        return "ram", "mémoire", va


def classify(t, zones):
    """Chaque écriture du tweak : dict(kind, va, old, new, n, ...). Les pointeurs vers les caves sont revus ensuite."""
    out = []
    for w in t["writes"]:
        old, new = bytes.fromhex(w["old"]), bytes.fromhex(w["new"])
        va = w["off"] + BASE
        r = {"va": va, "old": old, "new": new, "n": len(old)}
        if va in zones.consts and len(old) == 4 and int.from_bytes(old, "big") == zones.consts[va]:
            r.update(kind="redirect", mask=zones.consts[va], to=int.from_bytes(new, "big"))
        elif zones.mask_of(va) is not None:
            r.update(kind="mask", mask=zones.mask_of(va))
        elif zones.kept_of(va) is not None:
            r.update(kind="kept", mask=zones.kept_of(va))
        elif len(old) >= 2 and old.count(0xFF) == len(old):
            r.update(kind="cave")
        elif len(new) >= 6 and int.from_bytes(new[:2], "big") in DETOURS:
            op = int.from_bytes(new[:2], "big")
            x = int.from_bytes(new[2:6], "big")
            target = x if op in (0x4EB9, 0x4EF9) else va + 2 + (x - (1 << 32) if x >> 31 else x)
            r.update(kind="hook", op=DETOURS[op], target=target)
        elif len(new) == 4 and zones.place(int.from_bytes(new, "big"), t["id"])[0] in ("mask", "payload"):
            r.update(kind="pointer", target=int.from_bytes(new, "big"))
        else:
            r.update(kind="patch")
        out.append(r)
    return out


def analyse(tweaks):
    """(zones, {id: [écritures classées]}, erreurs, avertissements, graphe requires/conflicts)."""
    zones = Zones(tweaks)
    g = co.Graph(tweaks)
    rows = {t["id"]: classify(t, zones) for t in tweaks}
    zones.caves = {(r["va"], r["va"] + r["n"]) for rs in rows.values() for r in rs if r["kind"] == "cave"}
    for rs in rows.values():                               # un pointeur peut viser la cave d'un autre mod
        for r in rs:
            if r["kind"] == "patch" and r["n"] == 4 and zones.place(int.from_bytes(r["new"], "big"))[0] == "cave":
                r.update(kind="pointer", target=int.from_bytes(r["new"], "big"))
    errs, warns = [], []
    masks_written = {tid: {r["mask"] for r in rs if r["kind"] == "mask"} for tid, rs in rows.items()}
    redirected = {tid: {r["mask"] for r in rs if r["kind"] == "redirect"} for tid, rs in rows.items()}
    for tid, rs in rows.items():
        chain = set().union(*(redirected.get(i, set()) for i in g.closure(tid)))
        for m in sorted(masks_written[tid] - chain):
            errs.append(f"{tid} : écrit dans le masque {m:#x} sans rediriger son sprite (sprites.redirect_write) : "
                        "le sprite afficherait le code")
        dependants = {i for i in rows if tid in g.closure(i)}
        used_by_chain = set().union(*(masks_written[i] for i in dependants))
        for m in sorted(redirected[tid] - used_by_chain):
            warns.append(f"{tid} : redirige le sprite du masque {m:#x} sans écrire dedans")
        for r in rs:
            if r["kind"] == "kept":
                errs.append(f"{tid} : écrit en {r['va']:#x}, dans la copie gardée {r['mask']:#x} que lisent tous les "
                            "sprites redirigés")
            if r["kind"] == "redirect" and r["to"] != sprites.kept_of(r["mask"]):
                errs.append(f"{tid} : la redirection du masque {r['mask']:#x} vise {r['to']:#x}, pas la copie gardée "
                            f"{sprites.kept_of(r['mask']):#x}")
    return zones, rows, errs, warns, g


def verify_inventory(stock):
    """Avec l'OS officiel : chaque masque de GROUPS est identique à la copie gardée de son groupe, sa constante le
    désigne (pea ou move.l #imm,(sp)) et c'est la seule référence 32 bits alignée vers lui dans l'image. Les trois
    masques 0xFF de MASKS : tout à 0xFF, même contrôle de la constante. Renvoie (erreurs, masques vérifiés)."""
    errs, words = [], collections.defaultdict(list)
    for i in range(0, len(stock) - 3, 2):
        words[int.from_bytes(stock[i:i + 4], "big")].append(i + BASE)

    def const_ok(va, const, what):
        if int.from_bytes(stock[const - BASE:const - BASE + 4], "big") != va:
            errs.append(f"{what} {va:#x} : la constante en {const:#x} ne le désigne pas")
        if int.from_bytes(stock[const - BASE - 2:const - BASE], "big") not in (0x4879, 0x2EBC):
            errs.append(f"{what} {va:#x} : ni pea ni move.l #imm,(sp) devant la constante {const:#x}")
        if words.get(va, []) != [const]:
            errs.append(f"{what} {va:#x} : références 32 bits alignées {[hex(r) for r in words.get(va, [])]}, "
                        f"attendu [{const:#x}]")
    n = 0
    for (w, h), (size, kept, rows) in sprites.GROUPS.items():
        k = stock[kept - BASE:kept - BASE + size]
        for va, const in rows:
            n += 1
            if stock[va - BASE:va - BASE + size] != k:
                errs.append(f"masque {va:#x} ({w}x{h}) : pas identique à la copie gardée {kept:#x}")
            const_ok(va, const, f"masque {w}x{h}")
    for va, (size, const, _d, *shared) in sprites.MASKS.items():
        if not shared:
            n += 1
            if stock[va - BASE:va - BASE + size].count(0xFF) != size:
                errs.append(f"masque 0xFF {va:#x} : pas entièrement à 0xFF")
            const_ok(va, const, "masque 0xFF")
    if stock[sprites.SHARED_MASK - BASE:sprites.SHARED_MASK - BASE + 1040].count(0xFF) != 1040:
        errs.append(f"la copie gardée {sprites.SHARED_MASK:#x} n'est pas à 0xFF")
    return errs, n


def render(tweaks, zones, rows, warns):
    by_id = {t["id"]: t for t in tweaks}
    holders = claim_holders(by_id)                       # notes/65: the declared claims
    L = []
    p = L.append
    users = collections.defaultdict(dict)                  # masque -> {id: octets écrits}
    cover = collections.defaultdict(set)                   # masque -> octets écrits par au moins un mod
    caves = collections.defaultdict(dict)                  # (va, n) -> {id: n}
    hooks = collections.defaultdict(lambda: (set(), set()))      # (va, old, op, genre, zone) -> (ids, cibles)
    ptrs = collections.defaultdict(lambda: (set(), set()))       # (va, old, genre, zone) -> (ids, valeurs)
    for tid, rs in rows.items():
        for r in rs:
            if r["kind"] == "mask":
                users[r["mask"]][tid] = users[r["mask"]].get(tid, 0) + r["n"]
                cover[r["mask"]] |= set(range(r["va"] - r["mask"], r["va"] - r["mask"] + r["n"]))
            elif r["kind"] == "cave":
                caves[(r["va"], r["n"])][tid] = r["n"]
            elif r["kind"] == "hook":
                kind, zone, off = zones.place(r["target"], tid)
                ids, tg = hooks[(r["va"], r["old"], r["op"], kind, zone)]
                ids.add(tid)
                tg.add(r["target"] if kind in ("os", "ram") else off)
            elif r["kind"] == "pointer":
                kind, zone, off = zones.place(r["target"], tid)
                ids, vs = ptrs[(r["va"], r["old"], kind, zone)]
                ids.add(tid)
                vs.add(off)
    free_masks = [m for m in zones.masks if m not in users]
    taken_b = sum(zones.masks[m][0] for m in users)
    free_b = sum(zones.masks[m][0] for m in free_masks)
    apps = sorted((t for t in tweaks if t.get("append")), key=lambda t: (t["order"], t["id"]))
    shared_hooks = sum(1 for ids, _ in hooks.values() if len({family(i) for i in ids}) > 1)

    def state(m):
        size, used = zones.masks[m][0], len(cover[m])
        return f"pris ({used}/{size} o)" if used < size else "pris (plein)"

    def sym_of(ids, target):
        for i in sorted(ids):
            s = {int(v, 16): k for k, v in by_id[i].get("symbols", {}).items()}
            if target in s:
                return f" `{s[target]}`"
        return ""

    p("# Registre de la place libre et des points d'accroche — Model:Cycles OS 1.13")
    p("")
    p("Généré par `tools/registry.py` à partir des tweaks de ce dossier (notes/52) : ne pas éditer à la main. "
      "`python3 tools/registry.py` le régénère, `--check` vérifie qu'il est à jour, `--git <branche>` y ajoute à "
      "l'écran les mods d'autres branches, `--cycles <OS officiel>` vérifie le relevé des masques sur l'image.")
    p("")
    p("Adresses : VA de l'OS 1.13 (la section 3 commence en `0x40000400`). Un mod qui veut de la place prend un masque "
      "marqué *libre* au §1 (`sprites.redirect_write`, voir `tools/AGENTS.md`), régénère ce fichier et le commet "
      "avec son tweak. `tools/check_overlaps.py` refuse deux mods installables ensemble aux mêmes octets ; ce "
      "registre refuse une écriture dans un masque dont le sprite n'est pas redirigé.")
    p("")
    p("## En bref")
    p("")
    p(f"- {len(tweaks)} tweaks, {fmt(sum(len(t['writes']) for t in tweaks))} écritures.")
    p(f"- Masques de sprites libérables : {len(zones.masks)} ({fmt(taken_b + free_b)} o), dont {len(users)} pris "
      f"({fmt(taken_b)} o) et **{len(free_masks)} libres ({fmt(free_b)} o)**.")
    p(f"- Crochets sur l'OS : {len({k[0] for k in hooks})} adresses détournées, dont {shared_hooks} à l'identique par "
      "des mods de familles différentes.")
    p(f"- Pointeurs réécrits : {len({k[0] for k in ptrs})} adresses. Écritures dans des octets 0xFF hors masques : "
      f"{len(caves)} zones.")
    p(f"- Charges utiles ajoutées après l'OS : {len(apps)} tweaks ; place restante au §3.")
    p(f"- Declared claims (notes/65): {len(holders)} holders; the saved data in §6, the key combinations in §8, the "
      "descriptors, formatters, p-lock rows and MIDI in §9, the views in §10.")
    p("")
    # §1
    p("## 1. Masques de sprites libérés")
    p("")
    p("Les masques d'un groupe sont identiques octet pour octet et chacun n'est désigné que par la constante 32 bits "
      "de son constructeur (notes/14 §5, notes/32 §11, notes/52). Faire pointer cette constante sur la copie gardée "
      "libère le masque : le rendu ne change pas et l'OS, chargé en SDRAM, n'y lit plus rien. Règles : un mod qui "
      "écrit dans un masque le redirige dans le même tweak (ou dans un tweak qu'il demande) ; personne n'écrit dans "
      "une copie gardée ; deux mods ne partagent un masque que s'ils ne s'installent jamais ensemble, ou l'un "
      "par-dessus l'autre.")
    p("")
    for (w, h), (size, kept, grows) in sprites.GROUPS.items():
        ms = [va for va, _c in grows if va != kept]
        taken = [m for m in ms if m in users]
        p(f"### {w}×{h} : {len(ms)} masques de {size} o (copie gardée `{kept:#x}`) : {len(taken)} pris, "
          f"{len(ms) - len(taken)} libres ({fmt((len(ms) - len(taken)) * size)} o)")
        p("")
        p("| masque | constante | état | mods (octets écrits) |")
        p("|---|---|---|---|")
        for va, const in grows:
            if va == kept:
                continue
            if va in users:
                p(f"| `{va:#x}` | `{const:#x}` | {state(va)} | {names(users[va], by_id, users[va])} |")
            else:
                p(f"| `{va:#x}` | `{const:#x}` | libre | |")
        p("")
    p(f"### Masques 0xFF redirigés vers `{sprites.SHARED_MASK:#x}` (notes/14 §5)")
    p("")
    p("Trois masques entièrement à 0xFF, les plus grands ; plusieurs mods s'y partagent la place (`check_overlaps.py` "
      "garantit qu'ils n'écrivent pas les mêmes octets, ou à l'identique).")
    p("")
    p("| masque | taille | constante | état | mods (octets écrits) |")
    p("|---|---|---|---|---|")
    for va, (size, const, _desc, *shared) in sprites.MASKS.items():
        if shared:
            continue
        p(f"| `{va:#x}` | {size} o | `{const:#x}` | {state(va) if va in users else 'libre'} | "
          f"{names(users.get(va, {}), by_id, users.get(va, {})) if va in users else ''} |")
    p("")
    # §2
    p("## 2. Autres écritures dans des octets 0xFF (caves)")
    p("")
    p("Octets à 0xFF dans l'OS d'origine, hors des masques ci-dessus (tables à trous, fins de blocs). `build.py` refuse "
      "d'y écrire si l'image d'origine pointe dedans, sauf référence vérifiée à la main (`device.json`, "
      "`cave_refs_ok`).")
    p("")
    p("| adresse | octets | mods |")
    p("|---|---|---|")
    for (va, n), who in sorted(caves.items()):
        p(f"| `{va:#x}` | {n} | {names(who, by_id)} |")
    p("")
    # §3
    p("## 3. Charges utiles ajoutées après l'OS")
    p("")
    p("Code trop gros pour un masque, ajouté à la fin de l'image (`at`) et copié au démarrage en mémoire (`dest`) ; "
      "les charges d'un même firmware s'enchaînent dans l'ordre `order` (notes/17, 31), ce que `check_overlaps.py` "
      f"vérifie pour chaque ensemble installable. L'image ne peut pas dépasser `{END_LIMIT:#x}`.")
    p("")
    p("| mod | order | dans l'image (`at`) | octets | fin | en mémoire (`dest`) | octets | demande |")
    p("|---|---|---|---|---|---|---|---|")
    hi_end = 0
    for t in apps:
        ap = t["append"]
        at, n = int(ap["at"], 16), co.chunk_len(ap)
        hi_end = max(hi_end, at + n)
        p(f"| {t['id']} | {t['order']} | `{at:#x}` | {fmt(n)} | `{at + n:#x}` | `{int(ap['dest'], 16):#x}` | "
          f"{fmt(ap['size'])} | {', '.join(t.get('requires', []))} |")
    p("")
    if apps:
        p(f"Fin la plus haute : `{hi_end:#x}`, soit {fmt(END_LIMIT - hi_end)} o avant la limite (une charge posée sur "
          "une autre, comme les moteurs du Syntakt sur Model-TG, est déjà comptée à sa place dans la chaîne).")
        p("")
    # §4
    p("## 4. Points d'accroche (crochets) sur l'OS")
    p("")
    p("Instructions de l'OS remplacées par un détour (`jsr`, `jmp`, `bsr.l`, `bra.l`) vers le code d'un mod, ou vers une "
      "autre fonction de l'OS. Deux mods installables ensemble ne peuvent détourner la même adresse qu'avec les mêmes "
      "octets (`check_overlaps.py`) ; sinon ils se déclarent `conflicts`. Les combinaisons de moteurs du Syntakt "
      "visent des décalages différents dans leur charge utile : une ligne par adresse et par zone visée, avec le "
      "nombre de cibles (moteurs résumés en familles : présents/total). Le rôle de chaque crochet est dans la note du mod.")
    p("")
    p("| adresse | origine (hex) | détour | vers | mods | notes |")
    p("|---|---|---|---|---|---|")
    for (va, old, op, kind, zone), (ids, tg) in sorted(hooks.items(), key=lambda kv: (kv[0][0], sorted(kv[1][0]))):
        if len(tg) == 1:
            t0 = next(iter(tg))
            if kind in ("os", "ram"):
                where = f"{zone} `{t0:#x}`" + sym_of(ids, t0)
            else:
                where = f"{zone} +{t0:#x}"
                if kind == "mask":
                    where += sym_of(ids, int(zone.split("`")[1], 16) + t0)
        else:
            where = f"{zone}, {len(tg)} cibles selon la combinaison"
        notes = ", ".join(sorted({note_of(by_id[i]) for i in ids if note_of(by_id[i])}))
        old_hex = old.hex() if len(old) <= 10 else old[:10].hex() + "…"
        p(f"| `{va:#x}` | `{old_hex}` | {op} | {where} | {names(ids, by_id)} | {notes} |")
    p("")
    # §5
    p("## 5. Pointeurs réécrits")
    p("")
    p("Constantes 32 bits de l'OS (tables de fonctions, données) qui pointent maintenant vers le code ou les données "
      "d'un mod. Même regroupement qu'au §4.")
    p("")
    p("| adresse | ancien | vers | mods |")
    p("|---|---|---|---|")
    for (va, old, kind, zone), (ids, vs) in sorted(ptrs.items(), key=lambda kv: (kv[0][0], sorted(kv[1][0]))):
        where = f"{zone} +{next(iter(vs)):#x}" if len(vs) == 1 else f"{zone}, {len(vs)} valeurs selon la combinaison"
        p(f"| `{va:#x}` | `{old.hex()}` | {where} | {names(ids, by_id)} |")
    p("")
    # §6, and §8 to §10 after §7: from the declared claims (notes/65)
    six, rest = claims_lines(holders)
    L.extend(six)
    # §7
    p("## 7. Ce que chaque mod touche")
    p("")
    p("Nombre d'écritures de chaque sorte (une plage pour une famille de moteurs).")
    p("")
    p("| mod | écritures | patchs | crochets | pointeurs | masques | redirections | caves | charge utile (image) | note |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    fams = collections.defaultdict(list)
    for t in tweaks:
        fams[family(t["id"])].append(t)

    def span(vs):
        vs = sorted(vs)
        return str(vs[0]) if vs[0] == vs[-1] else f"{vs[0]}–{vs[-1]}"
    for fam in sorted(fams, key=lambda f: (min(t["order"] for t in fams[f]), f)):
        ts = fams[fam]
        c = [collections.Counter(r["kind"] for r in rows[t["id"]]) for t in ts]
        ap = [co.chunk_len(t["append"]) for t in ts if t.get("append")]
        apc = "" if not ap else (fmt(min(ap)) + " o" if min(ap) == max(ap) else f"{fmt(min(ap))}–{fmt(max(ap))} o")
        label = fam if len(ts) == 1 else f"{fam} ({len(ts)} tweaks)"
        p(f"| {label} | {span(len(t['writes']) for t in ts)} | {span(x['patch'] for x in c)} | "
          f"{span(x['hook'] for x in c)} | {span(x['pointer'] for x in c)} | {span(x['mask'] for x in c)} | "
          f"{span(x['redirect'] for x in c)} | {span(x['cave'] for x in c)} | {apc} | "
          f"{', '.join(sorted({note_of(t) for t in ts if note_of(t)}))} |")
    p("")
    L.extend(rest)
    if warns:
        p("## Remarques")
        p("")
        for w in warns:
            p(f"- {w}")
        p("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="vérifie que REGISTRY.md est à jour (exit 1 sinon)")
    ap.add_argument("--git", action="append", default=[], metavar="REF",
                    help="ajoute les tweaks d'une branche ou d'un commit (répétable) ; résultat à l'écran")
    ap.add_argument("--cycles", metavar="SYX", help="OS officiel : vérifie aussi le relevé des masques sur l'image")
    ap.add_argument("--out", help="écrit le registre dans ce fichier (défaut : REGISTRY.md, ou l'écran avec --git)")
    args = ap.parse_args()

    dev, tweaks = co.load_dir()
    if args.git:
        tweaks = co.merge([("dépôt", tweaks)] + [(ref, co.load_git(ref)[1]) for ref in args.git])
    zones, rows, errs, warns, _g = analyse(tweaks)
    n_inv = 0
    if args.cycles:
        import build                 # noqa: E402  (mtlib : lecture du .syx)
        import ref_mainos            # noqa: E402
        stock = ref_mainos.main_os(args.cycles)
        if build.sha(stock) != dev["section_sha256"]:
            raise SystemExit("!! --cycles : ce n'est pas le MAIN OS officiel 1.13 (SHA-256 de la section 3 différent)")
        e, n_inv = verify_inventory(stock)
        errs += e
    text = render(tweaks, zones, rows, warns) + "\n"
    for w in warns:
        print(f"  ? {w}")
    for e in errs:
        print(f"!! {e}")
    if errs:
        raise SystemExit(f"!! {len(errs)} erreur(s)")
    if args.cycles:
        print(f"ok : relevé des masques vérifié sur l'OS officiel ({n_inv} masques : copies identiques, une seule "
              "référence chacun)")
    if args.git and not args.out:
        print(text)
        return
    out = pathlib.Path(args.out) if args.out else OUT
    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    free = sum(1 for m in zones.masks if not any(r["kind"] == "mask" and r["mask"] == m
                                                 for rs in rows.values() for r in rs))
    if args.check:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            raise SystemExit(f"!! {shown} n'est pas à jour : python3 tools/registry.py")
        print(f"ok : {shown} à jour ({len(tweaks)} tweaks, {len(zones.masks)} masques libérables, {free} libres)")
        return
    out.write_text(text, encoding="utf-8")
    print(f"{shown} : {len(tweaks)} tweaks, {len(zones.masks)} masques libérables, {free} libres")


if __name__ == "__main__":
    main()
