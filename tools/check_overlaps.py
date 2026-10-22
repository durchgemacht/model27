#!/usr/bin/env python3
"""Vérifie, sans aucun fichier d'Elektron, que les tweaks se combinent bloc par bloc (notes/49).

Deux tweaks qu'on peut installer ensemble (aucun conflit déclaré entre eux ni entre ce qu'ils demandent par
« requires ») ne doivent jamais écrire aux mêmes octets, sauf dans deux cas prévus par les deux builders :
  - la même écriture entière (même adresse, mêmes octets « old » et « new ») : un pochoir libéré par les deux ;
  - un tweak qui s'applique par-dessus l'autre (« requires », directement ou par une chaîne), comme les moteurs du
    Syntakt de la version combinée sur model-tg-st (notes/31).
Vérifie aussi :
  - chaque écriture : hexadécimal sans espace, « old » et « new » non vides et de même longueur, dans la section 3 ;
  - les ids : uniques, et chaque « requires » nomme un tweak qui existe (un « conflicts » vers un tweak absent, d'une
    autre branche, est seulement signalé) ;
  - les charges utiles ajoutées après l'OS (« append ») de chaque ensemble installable : chacune commence là où finit
    la précédente (« at »), l'ensemble finit sous END_LIMIT, et la mémoire où elles tournent (« dest ») ne se
    chevauche pas.

C'est ce qui permet de vérifier le flasher mod par mod au lieu de chaque combinaison (tools/ref_mainos.py) : si deux
mods qu'on peut cocher ensemble n'écrivent jamais aux mêmes octets (hors des deux cas prévus), le firmware d'une
combinaison est celui de ses mods, posés l'un à côté de l'autre.

    python3 tools/check_overlaps.py                          # tweaks/ du dépôt
    python3 tools/check_overlaps.py --git origin/main --git origin/claude/xyz   # tweaks de branches, réunis (git show)

Avec plusieurs --git, les tweaks des branches sont réunis : un même id dans deux versions différentes devient deux
tweaks incompatibles entre eux (on n'installe jamais les deux versions d'un même mod). Un « conflicts » vers cet id
vaut pour toutes ses versions ; un « requires » vise la version de sa propre source : un mod d'une branche posé sur la
version d'un autre mod changée par une autre branche n'est donc pas vérifié ici, mais par ce script et
tools/ref_mainos.py une fois l'une des deux branches fusionnée dans l'autre.

model27, notes/65 (step C2): the declared claims too (tools/claims.py). Two tweaks that can be installed together
never claim the same saved slot, key combination, descriptor or formatter, unless one applies on top of the other;
and each declared conflict is shown by what proves it: the bytes, the claims, both, or its text only (the pairs
shown by their text only are listed).
"""
import argparse
import collections
import itertools
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import claims as cl              # noqa: E402  (tools/claims.py, notes/65)
ROOT = HERE.parent
DEV = "model-cycles_OS1.13"
BASE = 0x40000400                 # VA du premier octet de la section 3 (tools/build.py)
END_LIMIT = 0x40200000            # fin maximale de l'OS agrandi (tools/build.py)
HEX = re.compile(r"(?:[0-9a-fA-F]{2})+")


def load_dir(root=ROOT):
    """(device.json, [tweaks]) du dépôt de travail."""
    d = root / "tweaks" / DEV
    dev = json.loads((d / "device.json").read_text(encoding="utf-8"))
    return dev, [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("[0-9]*.json"))]


def load_git(ref):
    """(device.json, [tweaks]) d'une branche ou d'un commit, sans la sortir (git show)."""
    def show(path):
        return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{path}"], check=True,
                              capture_output=True, text=True).stdout
    names = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"{ref}:tweaks/{DEV}/"], check=True,
                           capture_output=True, text=True).stdout.split()
    dev = json.loads(show(f"tweaks/{DEV}/device.json"))
    return dev, [json.loads(show(f"tweaks/{DEV}/{n}")) for n in sorted(names) if re.match(r"\d.*\.json$", n)]


def merge(sources):
    """Réunit les tweaks de plusieurs sources [(nom, tweaks)]. Deux versions d'un même id aux mêmes écritures et à la
    même charge utile n'en font qu'une (leurs « conflicts » et « requires » sont réunis : une branche ajoute souvent
    un conflit ou un symbole à un tweak existant). Sinon chaque version devient « id@source », incompatible avec les
    autres ; un « conflicts » vers cet id vaut pour toutes ses versions (un conflit n'est souvent déclaré que d'un
    côté), un « requires » vise la version de sa propre source (sinon la première)."""
    versions = {}                                  # id -> [[noms des sources], tweak]
    for name, tweaks in sources:
        for t in tweaks:
            vs = versions.setdefault(t["id"], [])
            v = next((v for v in vs if (v[1].get("writes"), v[1].get("append")) == (t.get("writes"), t.get("append"))),
                     None)
            if v:
                v[0].append(name)
                for k in ("conflicts", "requires"):
                    if t.get(k) or v[1].get(k):
                        v[1] = dict(v[1], **{k: sorted(set(v[1].get(k, [])) | set(t.get(k, [])))})
            else:
                vs.append([[name], dict(t)])
    out, alias = [], {}                            # alias[(id, source)] = id de la version de cette source
    for tid, vs in versions.items():
        for names, t in vs:
            a = tid if len(vs) == 1 else f"{tid}@{names[0]}"
            for n in names:
                alias[(tid, n)] = a
    for tid, vs in versions.items():
        for names, t in vs:
            src = names[0]
            t = dict(t, id=alias[(tid, src)])
            if t.get("requires"):
                t["requires"] = sorted({alias.get((x, src), alias.get((x, versions[x][0][0][0]))) if x in versions
                                        else x for x in t["requires"]})
            if t.get("conflicts"):
                t["conflicts"] = sorted({a for x in t["conflicts"]
                                         for a in ({alias[(x, n[0])] for n, _ in versions[x]} if x in versions else {x})})
            if len(vs) > 1:                        # deux versions d'un même mod ne s'installent pas ensemble
                t["conflicts"] = sorted(set(t.get("conflicts", [])) |
                                        {alias[(tid, n[0])] for n, _ in vs if n[0] != src})
            out.append(t)
    return out


def check_writes(tweaks, section_len):
    """Écritures bien formées et ids uniques : [message d'erreur]."""
    errs, seen = [], set()
    for t in tweaks:
        if t["id"] in seen:
            errs.append(f"{t['id']} : id en double (build.py et la page garderaient le dernier)")
        seen.add(t["id"])
        for i, w in enumerate(t.get("writes", [])):
            where = f"{t['id']} écriture {i}"
            off, old, new = w.get("off"), w.get("old"), w.get("new")
            if not isinstance(off, int) or isinstance(off, bool) or off < 0:
                errs.append(f"{where} : « off » doit être un entier positif ({off!r})")
                continue
            if not (isinstance(old, str) and HEX.fullmatch(old)) or not (isinstance(new, str) and HEX.fullmatch(new)):
                errs.append(f"{where} @ 0x{off + BASE:08x} : « old » et « new » doivent être de l'hexadécimal "
                            "non vide, deux chiffres par octet, sans espace")
                continue
            if len(old) != len(new):
                errs.append(f"{where} @ 0x{off + BASE:08x} : « old » ({len(old) // 2} o) et « new » "
                            f"({len(new) // 2} o) de longueurs différentes")
            if off + len(old) // 2 > section_len:
                errs.append(f"{where} @ 0x{off + BASE:08x} : dépasse la fin de la section 3 ({section_len} o)")
    return errs


class Graph:
    """Qui s'installe avec qui : les « requires » (fermeture) et les « conflicts » (dans les deux sens)."""

    def __init__(self, tweaks):
        self.by_id = {t["id"]: t for t in tweaks}
        self.errs, self.notes = [], []
        for t in tweaks:
            for x in t.get("requires", []):
                if x not in self.by_id:
                    self.errs.append(f"{t['id']} : « requires » nomme {x}, qui n'existe pas")
            for x in t.get("conflicts", []):
                if x not in self.by_id:               # un mod d'une autre branche : sans effet ici, comme build.py
                    self.notes.append(f"{t['id']} : « conflicts » nomme {x}, absent ici (ignoré)")
        self.bad = {(a["id"], b) for a in tweaks for b in a.get("conflicts", []) if b in self.by_id}
        self.bad |= {(b, a) for a, b in self.bad}
        self._closure = {}

    def closure(self, tid):
        """tid et tout ce qu'il demande, directement ou par une chaîne."""
        if tid not in self._closure:
            out, todo = set(), [tid]
            while todo:
                x = todo.pop()
                if x not in out and x in self.by_id:
                    out.add(x)
                    todo += self.by_id[x].get("requires", [])
            self._closure[tid] = frozenset(out)
        return self._closure[tid]

    def installable(self, ids):
        """Les tweaks ids, plus ce qu'ils demandent, peuvent-ils être construits ensemble (build.check_conflicts) ?"""
        full = set().union(*(self.closure(i) for i in ids))
        return not any((a, b) in self.bad for a, b in itertools.combinations(full, 2))

    def chained(self, a, b):
        """L'un s'applique-t-il par-dessus l'autre ?"""
        return a in self.closure(b) or b in self.closure(a)


def check_overlaps(tweaks, g):
    """Chevauchements d'écritures entre tweaks installables ensemble : ([violations], nombre de cas permis)."""
    spans = sorted((w["off"], w["off"] + len(w["old"]) // 2, t["id"], w["old"], w["new"])
                   for t in tweaks for w in t.get("writes", []))
    errs, allowed, done = [], 0, set()
    active = []                                   # écritures qui couvrent encore la position courante
    for lo, hi, tid, old, new in spans:
        active = [s for s in active if s[1] > lo]
        for alo, ahi, aid, aold, anew in active:
            if aid == tid:
                continue
            pair = tuple(sorted((aid, tid)))
            if not g.installable(pair):
                continue                          # jamais construits ensemble : les conflits les séparent
            if (alo, ahi, aold, anew) == (lo, hi, old, new) or g.chained(aid, tid):
                allowed += 1                      # même écriture entière, ou l'un par-dessus l'autre
                continue
            k = (pair, max(alo, lo))
            if k not in done:
                done.add(k)
                errs.append(f"{pair[0]} et {pair[1]} écrivent tous deux en 0x{max(alo, lo) + BASE:08x}.."
                            f"0x{min(ahi, hi) + BASE - 1:08x} sans conflit déclaré ni « requires » : déclarer "
                            "« conflicts », ou déplacer l'un des deux")
        active.append((lo, hi, tid, old, new))
    return errs, allowed


def chunk_len(ap):
    """Octets qu'une charge utile prend dans l'image (rangée en morceaux « pack », compressée « compress » : sa taille
    rangée « stored », notes/50, ou entière)."""
    if "compress" in ap:
        return ap["stored"]
    return sum(n for _, n in ap["pack"]) if "pack" in ap else ap["size"]


def append_sets(tweaks, g):
    """Tous les ensembles de tweaks « append » qui peuvent être construits ensemble (fermés par « requires »)."""
    apps = sorted((t for t in tweaks if t.get("append")), key=lambda t: (t["order"], t["id"]))
    out = set()

    def grow(cur, start):
        full = frozenset(i for x in cur for i in g.closure(x) if g.by_id[i].get("append"))
        if full:
            out.add(full)
        for k in range(start, len(apps)):
            nxt = cur + [apps[k]["id"]]
            if g.installable(nxt):
                grow(nxt, k + 1)
    grow([], 0)
    return out


def check_appends(tweaks, g, section_len):
    """Chaque ensemble installable de charges utiles s'enchaîne dans l'image et en mémoire : [violations], nombre."""
    errs, sets = [], append_sets(tweaks, g)
    for s in sorted(sets, key=lambda s: sorted(s)):
        chain = sorted((g.by_id[i] for i in s), key=lambda t: (t["order"], t["id"]))
        end = BASE + section_len
        names = "+".join(t["id"] for t in chain)
        if len({t["order"] for t in chain}) < len(chain):   # les builders trient par « order » seulement
            errs.append(f"{names} : deux charges utiles au même « order » : leur place dans l'image dépendrait de "
                        "l'ordre où on les coche")
            continue
        for t in chain:
            ap = t["append"]
            if int(ap["at"], 16) != end:
                errs.append(f"{names} : {t['id']} attend l'image finie en {ap['at']}, elle finit en 0x{end:08x} "
                            "(déclarer « conflicts » ou « requires »)")
                break
            end += chunk_len(ap)
        else:
            if end > END_LIMIT:
                errs.append(f"{names} : l'OS agrandi finirait en 0x{end:08x}, au-delà de 0x{END_LIMIT:08x}")
        runs = sorted((int(t["append"]["dest"], 16), int(t["append"]["dest"], 16) + t["append"]["size"], t["id"])
                      for t in chain)
        for (alo, ahi, a), (blo, bhi, b) in zip(runs, runs[1:]):
            if blo < ahi:
                errs.append(f"{names} : {a} et {b} tournent tous deux en mémoire en 0x{blo:08x}..0x{min(ahi, bhi) - 1:08x}")
    return errs, len(sets)


# model27, Level C (notes/65, C2): the declared claims (tools/claims.py), the second half of this check. Two tweaks
# that can be installed together never claim the same saved slot, key combination, descriptor or formatter, as they
# never write the same bytes; and each declared conflict is shown by what proves it.
def check_claims(tweaks, g, claimed):
    """Two tweaks that can be installed together and whose claims clash, unless one applies on top of the other:
    [violation]."""
    errs = []
    have = sorted(t["id"] for t in tweaks if base(t["id"]) in claimed)
    for a, b in itertools.combinations(have, 2):
        if not g.installable((a, b)) or g.chained(a, b):
            continue
        why = cl.clashes(claimed[base(a)], claimed[base(b)])
        if why:
            errs.append(f"{a} and {b} claim the same ({', '.join(why)}) with no conflict declared: declare "
                        "« conflicts », or change a claim (notes/65)")
    return errs


def base(tid):
    """An id without its source (--git: id@branch), which has the claims of its id."""
    return tid.split("@")[0]


def declared_report(tweaks, g, claimed):
    """How each declared conflict (a pair) is shown (STANDARD.md §9, step 5): by the bytes (other bytes at one
    address, or two payloads at the same place in the image or in memory), by the claims, by both, or by its text
    only. Returns ({kind: number of pairs}, [pairs shown by their text only])."""
    mine = {t["id"]: {w["off"] + i: b for w in t.get("writes", []) for i, b in enumerate(bytes.fromhex(w["new"]))}
            for t in tweaks}
    count, text = collections.Counter(), []
    for a, b in sorted({tuple(sorted(p)) for p in g.bad}):
        small, big = sorted((mine[a], mine[b]), key=len)
        shown = any(big.get(o, v) != v for o, v in small.items())
        pa, pb = g.by_id[a].get("append"), g.by_id[b].get("append")
        if pa and pb and not shown:
            da, db = int(pa["dest"], 16), int(pb["dest"], 16)
            shown = pa["at"] == pb["at"] or (da < db + pb["size"] and db < da + pa["size"])
        by_claims = base(a) in claimed and base(b) in claimed and bool(cl.clashes(claimed[base(a)], claimed[base(b)]))
        kind = "both" if shown and by_claims else "bytes" if shown else "claims" if by_claims else "text"
        count[kind] += 1
        if kind == "text":
            text.append((a, b))
    return count, text


def check(tweaks, section_len):
    """Toutes les vérifications : (erreurs, résumé)."""
    errs = check_writes(tweaks, section_len)
    g = Graph(tweaks)
    errs += g.errs
    for n in sorted(set(g.notes)):
        print("   " + n)
    if errs:                                      # écritures mal formées : on ne va pas plus loin
        return errs, ""
    ov, allowed = check_overlaps(tweaks, g)
    ap, nsets = check_appends(tweaks, g, section_len)
    claimed = cl.tweak_claims()
    cc = check_claims(tweaks, g, claimed)
    count, text = declared_report(tweaks, g, claimed)
    for a, b in text:
        print(f"   declared, shown by its text only: {a} and {b}")
    n = sum(len(t.get("writes", [])) for t in tweaks)
    have = sum(base(t["id"]) in claimed for t in tweaks)
    return ov + ap + cc, (f"{len(tweaks)} tweaks, {n} écritures : aucune écriture partagée entre deux mods "
                          f"installables ensemble, hors {allowed} cas prévus (même écriture, ou mod par-dessus un "
                          f"autre) ; "
                          f"{nsets} ensembles de charges utiles enchaînés ; claims (notes/65): {have} tweaks, no "
                          f"clash between two that can be installed together; declared conflicts: "
                          f"{sum(count.values())} pairs, shown by the bytes {count['bytes']}, by the claims "
                          f"{count['claims']}, by both {count['both']}, by their text only {count['text']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--git", action="append", metavar="REF", help="tweaks d'une branche ou d'un commit (répétable)")
    args = ap.parse_args()
    if args.git:
        loaded = [(ref, *load_git(ref)) for ref in args.git]         # la ref entière : deux refs, deux noms
        section_len = loaded[0][1]["section_len"]
        tweaks = merge([(name, tw) for name, _, tw in loaded])
    else:
        dev, tweaks = load_dir()
        section_len = dev["section_len"]
    errs, summary = check(tweaks, section_len)
    for e in errs:
        print("!! " + e)
    if errs:
        sys.exit(f"!! {len(errs)} probleme(s) : les mods ne se combinent pas bloc par bloc (notes/49)")
    print("ok : " + summary)


if __name__ == "__main__":
    main()
