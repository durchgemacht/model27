#!/usr/bin/env python3
"""Empreintes de référence du flasher web : REF_MODS et REF_MAINOS dans docs/flasher/app.js (notes/49).

REF_MODS : pour chaque tweak que la page embarque, l'empreinte de ses écritures (« w ») et, s'il ajoute du code
après l'OS, celle de cette charge utile telle qu'elle va dans l'image (« p »), calculées comme tools/build.py. La page
les vérifie à chaque build : chaque mod coché est, octet pour octet, celui de l'outil Python, quelle que soit la
combinaison.

REF_MAINOS : le SHA-256 du MAIN OS modifié d'un échantillon de combinaisons, construites en entier comme
tools/build.py (conflits, zones 0xFF, charges utiles enchaînées) :
  - chaque carte seule (chaque variante ; pour les vrais moteurs du Syntakt, chaque combinaison de moteurs) ;
  - chaque paire de cartes que la page laisse cocher ensemble ;
  - les plus grandes combinaisons : toutes les cartes compatibles cochées, à partir de chaque carte, dans l'ordre des
    cartes puis dans l'ordre inverse, avec et sans les cartes qui demandent un autre fichier (les moteurs du Syntakt),
    et sans chaque ensemble des cartes qui en rejoignent d'autres (MACRO, ACID : chaque version des moteurs).
La page compare le MAIN OS de ces combinaisons à leur empreinte et refuse s'il diffère. Avec tools/check_overlaps.py
(deux mods qu'on peut cocher ensemble n'écrivent jamais aux mêmes octets, sauf écriture identique ou mod posé par-dessus
l'autre), cet échantillon suffit : il grandit d'une quarantaine d'entrées par nouvelle carte, au lieu de doubler. Les
cartes suivent les règles de app.js : « excludes » et « includes » (jamais cochées ensemble), « with » (un autre tweak
quand une autre carte est cochée), « requires » (une carte qui ne va qu'avec une autre : la page coche l'autre avec
elle, l'aperçu des samples avec Model-TG), « joins » (une carte qui, cochée avec une de ses cartes hôtes, n'ajoute
rien : la première hôte cochée construit sa version avec toutes les cartes qu'elle porte ; MACRO et ACID avec les
moteurs du Syntakt, notes/50 et notes/54 §11, ACID avec MACRO), et Model-TG avec les moteurs du Syntakt (leur
version « tg »). Une sélection dont un tweak n'a pas le tweak qu'il demande (« requires » du tweak)
est laissée de côté, car les deux builds la refusent.

model27, Level B (notes/61 §5): the machine cards (« package ») have no tweak in tweaks.js; nor have the CPU page's,
RESAMPLE's and Transpose's cards (« part », notes/78 to 80), composed with them, their ids last (« cpu », « sampler+cpu »,
« sampler+cpu+resample+transpose »); the page composes the
ticked ones into one tweak, placed where the first of them is, its id their packages' ids joined by « + ». Here each
non-empty set of them, in card order, is composed by tools/compose.py: REF_MODS gets one entry per set, so whatever
the page composes is checked against the Python composer, and the sample's combinations are built with them.

    python3 tools/ref_mainos.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--check]
"""
import argparse
import contextlib
import functools
import hashlib
import io
import itertools
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import compose                     # noqa: E402
import gen_flasher_tweaks          # noqa: E402

ROOT = HERE.parent
TWEAKS_JS = ROOT / "docs" / "flasher" / "tweaks.js"
APP_JS = ROOT / "docs" / "flasher" / "app.js"
# le bloc : « const NOM = { », ses lignes (chacune précédée d'un saut de ligne ; aucune s'il est vide), « \n}; »
BLOCKS = {name: re.compile(r"(const " + name + r" = \{)((?:\n  .*)*)(\n\};\n)") for name in ("REF_MAINOS", "REF_MODS")}


def mc_tweaks():
    return gen_flasher_tweaks.read_js(TWEAKS_JS.read_text(encoding="utf-8"))


def main_os(cycles):
    """MAIN OS décompressé du .syx officiel, comme tools/build.py."""
    c = build.container.parse(build.unwrap(pathlib.Path(cycles).read_bytes())[0])
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    return build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]


def writes_bytes(t):
    """Les écritures d'un tweak, à la suite : off (4 o), len(old) (4 o), old, len(new) (4 o), new.
    Même calcul que writesBytes() de docs/flasher/builder.js."""
    out = bytearray()
    for w in t["writes"]:
        old, new = bytes.fromhex(w["old"]), bytes.fromhex(w["new"])
        out += w["off"].to_bytes(4, "big") + len(old).to_bytes(4, "big") + old + len(new).to_bytes(4, "big") + new
    return bytes(out)


# --- les cartes de la page (docs/flasher/app.js : excludes(), includedBy(), chosenTweaks()) ---------------------
class Cards:
    def __init__(self, features, tweaks):
        self.features = features
        self.by_id = {f["id"]: f for f in features}
        self.tweaks = {t["id"]: t for t in tweaks}

    def options(self, f):
        """Choix d'une carte : ses variantes (ids de tweaks), ses combinaisons de moteurs, ou son paquet (a machine
        card, notes/61)."""
        if f.get("package") or f.get("part"):
            return [f.get("package") or f.get("part")]
        return list(f["combos"]) if f.get("engines") else [v["id"] for v in f["variants"]]

    def biggest(self, f):
        """Choix par défaut d'une carte ajoutée à une grande combinaison : la 1re variante, ou le plus de moteurs."""
        opts = self.options(f)
        return max(opts, key=lambda c: len(c["engines"])) if f.get("engines") else opts[0]

    def excludes(self, f, g):
        no = lambda a, b: b["id"] in (a.get("excludes") or []) or b["id"] in (a.get("includes") or [])  # noqa: E731
        return no(f, g) or no(g, f)

    def needs(self, f):
        """Cartes qu'une carte demande (son « requires ») : la page les coche avec elle, l'échantillon aussi."""
        r = f.get("requires") or []
        return [r] if isinstance(r, str) else list(r)

    def valid(self, sel):
        """Une sélection que la page laisse cocher et que les deux builds acceptent."""
        on = [self.by_id[i] for i in sel]
        if any(self.excludes(f, g) for f, g in itertools.combinations(on, 2)):
            return False
        ids = self.ids(sel)
        return all(n in ids for i in ids for n in self.tweaks[i].get("requires") or [])

    def close(self, sel):
        """La sélection et les cartes qu'elle demande (au choix par défaut)."""
        sel, todo = dict(sel), list(sel)
        while todo:
            for n in self.needs(self.by_id[todo.pop()]):
                if n not in sel:
                    sel[n] = self.options(self.by_id[n])[0]
                    todo.append(n)
        return sel

    def hosts(self, f):
        j = f.get("joins") or []
        return [j] if isinstance(j, str) else list(j)

    def root(self, f, sel):
        """La carte qui porte f dans sa version (la 1re cochée de ses « joins »), ou None."""
        return next((h for h in self.hosts(f) if h in sel), None)

    def key(self, f, sel):
        """Clé de la version d'une carte hôte : les cartes cochées qu'elle porte, dans l'ordre des cartes, jointes par
        « + » (macro, acid, macro+acid), ou ""."""
        return "+".join(g["id"] for g in self.features if g["id"] in sel and self.root(g, sel) == f["id"])

    def ids(self, sel):
        """Tweaks construits pour une sélection {carte: choix}, dans l'ordre des cartes (la clé de REF_MAINOS)."""
        out = []
        machines = [f["package"] for f in self.features if f["id"] in sel and f.get("package")]
        cpu = ["cpu"] if any(f.get("part") == "cpu" for f in self.features if f["id"] in sel) else []
        cpu += ["resample"] if any(f.get("part") == "resample" for f in self.features if f["id"] in sel) else []
        cpu += ["transpose"] if any(f.get("part") == "transpose" for f in self.features if f["id"] in sel) else []
        first = next((f for f in self.features if f["id"] in sel and (f.get("package") or f.get("part"))), None)
        for f in self.features:
            if f["id"] not in sel or self.root(f, sel):        # « joins » : dans la version de sa carte hôte
                continue
            if f.get("package") or f.get("part"):              # the machines, the CPU page and RESAMPLE: one
                if f is first:                                 # composed tweak, where the first is
                    out.append("+".join(machines + cpu))
                continue
            o, k = sel[f["id"]], self.key(f, sel)
            if f.get("engines"):                               # avec MACRO, ACID : leur version (notes/50, 54 §11)
                o = o[k] if k else o
                tid = o["tg"] if "model-tg" in sel else o["id"]
            elif k and f.get("versions"):                      # MACRO avec ACID, sans les moteurs
                v = f["versions"][k]
                out.append(v["tg"] if "model-tg" in sel else v["id"])
                continue
            else:
                tid = o
            for g, alt in (f.get("with") or {}).items():
                if g in sel:
                    tid = alt
            out.append(tid)
        return out

    def sample(self):
        """[(groupe, sélection)] : chaque carte seule, chaque paire, les plus grandes combinaisons."""
        picks = [(f["id"], o) for f in self.features for o in self.options(f)]
        out = [("single", {c: o}) for c, o in picks]
        out += [("pair", {c: o, d: p}) for (c, o), (d, p) in itertools.combinations(picks, 2) if c != d]
        plain = [f for f in self.features if not f.get("needs")]     # sans les cartes qui demandent un autre fichier
        joiners = [f["id"] for f in self.features if self.hosts(f)]
        skips = [set(x) for r in range(len(joiners) + 1) for x in itertools.combinations(joiners, r)]
        for c, o in picks:
            for skip, order in itertools.product(skips, (self.features, self.features[::-1], plain, plain[::-1])):
                if c in skip:
                    continue
                sel = self.close({c: o})
                if not self.valid(sel):
                    continue
                for g in order:
                    if g["id"] not in sel and g["id"] not in skip:
                        trial = self.close(dict(sel, **{g["id"]: self.biggest(g)}))
                        if self.valid(trial):
                            sel = trial
                out.append(("largest", sel))
        res = []
        for group, sel in out:
            sel = self.close(sel)
            if self.valid(sel):
                res.append((group, sel))
        return res


GROUPS = {
    "single": "each card alone: each variant, each combination of real Syntakt engines",
    "pair": "every pair of cards the page lets you tick together",
    "largest": "the largest combinations: every compatible card ticked, from each card, both ways, with and without "
               "the Syntakt engines, with and without each of the machines that join them",
}


def blocks(cycles, syntakt):
    """(texte de REF_MAINOS, texte de REF_MODS, nombre de combinaisons)."""
    tw = mc_tweaks()
    by_id = {t["id"]: t for t in tw["tweaks"]}
    stock = main_os(cycles)
    if build.sha(stock) != tw["device"]["section_sha256"]:      # jamais depuis un build déjà modifié (règle 2)
        raise SystemExit("!! --cycles : ce n'est pas le MAIN OS officiel 1.13 : il faut model-cycles_OS1.13.syx "
                         "d'elektron.se")
    st_img = None
    if any("syntakt" in (t.get("append") or {}) for t in tw["tweaks"]):
        import syntakt as st                                # tools/emu/syntakt.py : vérifie le .syx et sa section 7
        st.dsp_image = functools.lru_cache(maxsize=None)(st.dsp_image)   # lu une fois (build_payload le relit)
        st_img = st.dsp_image(syntakt)
    known = tw["device"].get("cave_refs_ok")

    # the machine cards: each non-empty set of them, in card order, composed as the page composes them (notes/61), and
    # each with the CPU page, with RESAMPLE and with Transpose when the page offers them (notes/78 to 80), and those
    # alone
    machines = [f["package"] for f in tw["features"] if f.get("package")]
    cpus = (False, True) if any(f.get("part") == "cpu" for f in tw["features"]) else (False,)
    rsms = (False, True) if any(f.get("part") == "resample" for f in tw["features"]) else (False,)
    trss = (False, True) if any(f.get("part") == "transpose" for f in tw["features"]) else (False,)
    composed = []
    for r in range(0, len(machines) + 1):
        for ids in itertools.combinations(machines, r):
            for cpu in cpus:
                for rsm in rsms:
                    for trs in trss:
                        if ids or cpu or rsm or trs:
                            with contextlib.redirect_stdout(io.StringIO()):
                                composed.append(compose.compose(stock, list(ids), cpu=cpu, resample=rsm,
                                                                transpose=trs)[0])
    by_id.update({t["id"]: t for t in composed})

    mods = []
    for t in tw["tweaks"] + composed:
        ref = {"w": hashlib.sha256(writes_bytes(t)).hexdigest()}
        if t.get("append"):
            ref["p"] = hashlib.sha256(build.payload_image(t, build.payload_runtime(t, stock, st_img))).hexdigest()
        mods.append(f'  "{t["id"]}": {json.dumps(ref, separators=(", ", ": "))},')

    cards = Cards(tw["features"], tw["tweaks"] + composed)
    lines, seen, payloads = [], set(), {}
    last_group = None
    for group, sel in cards.sample():
        ids = cards.ids(sel)
        key = "+".join(ids)
        if key in seen:
            continue
        seen.add(key)
        if group != last_group:
            lines.append(f"  // {GROUPS[group]}")
            last_group = group
        chosen = sorted((by_id[i] for i in ids), key=lambda t: t["order"])
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                build.check_conflicts(chosen)
                patched, dirty = build.apply_writes(stock, chosen)
                build.check_caves(stock, chosen, False, dirty, patched, known)
                apps = tuple(t["id"] for t in chosen if t.get("append"))
                if apps not in payloads:
                    payloads[apps] = build.build_payload([by_id[i] for i in apps], stock, syntakt)[0] if apps else b""
        except SystemExit as e:
            raise SystemExit(f"!! la page propose {key}, que tools/build.py refuse : {e}")
        lines.append(f'  "{key}": "{build.sha(bytes(patched) + payloads[apps])}",')
    return "\n".join(lines), "\n".join(mods), len(seen)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que app.js est à jour")
    args = ap.parse_args()
    ref, mods, n = blocks(args.cycles, args.syntakt)
    app = APP_JS.read_text(encoding="utf-8")
    want = {"REF_MAINOS": "\n" + ref, "REF_MODS": "\n" + mods}
    found = {k: BLOCKS[k].search(app) for k in want}
    for k, m in found.items():
        if not m:
            raise SystemExit(f"!! bloc {k} introuvable dans app.js")
    nm = mods.count("\n") + 1
    if args.check:
        stale = [k for k in want if found[k].group(2) != want[k]]
        if stale:
            raise SystemExit(f"!! {', '.join(stale)} de app.js pas à jour ({n} combinaisons, {nm} mods) : "
                             "relance tools/ref_mainos.py")
        print(f"REF_MAINOS et REF_MODS sont à jour ({n} combinaisons, {nm} mods)")
        return
    for k in sorted(want, key=lambda k: -found[k].start()):   # de la fin vers le début : les positions restent justes
        m = found[k]
        app = app[:m.start(2)] + want[k] + app[m.end(2):]
    APP_JS.write_text(app, encoding="utf-8")
    print(f"écrit : REF_MAINOS ({n} combinaisons) et REF_MODS ({nm} mods) de {APP_JS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
