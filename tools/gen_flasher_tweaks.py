#!/usr/bin/env python3
"""Embarque les tables de patchs dans docs/flasher/tweaks.js pour le flasher web.

Le flasher web (docs/flasher/) construit le .syx dans le navigateur ; il lui
faut les tweaks. Plutot que de les lire par fetch (chemins fragiles sous GitHub
Pages, ne marche pas en file://), on les embarque dans un petit .js genere ici,
a partir des JSON canoniques de tweaks/. Source unique : ce script recopie, il
n'invente rien.

    python3 tools/gen_flasher_tweaks.py           # (re)genere docs/flasher/tweaks.js
    python3 tools/gen_flasher_tweaks.py --check    # verifie qu'il est a jour (CI)

model27, Level B (notes/61 §5): a machine card names its package instead of tweaks. tweaks.js then embeds the
package as the page composes it (compose.web_package: the manifest's fields and the committed object laid out once)
and the registrar's frame (tools/machines/registrar/frame.json), and no longer the machine's own tweak; the page
composes the ticked machines into one tweak (docs/flasher/composer.js). Still the standard library only, no firmware.
"""
import argparse
import collections
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEV_DIR = ROOT / "tweaks" / "model-cycles_OS1.13"
OUT = ROOT / "docs" / "flasher" / "tweaks.js"

# Fonctionnalites proposees dans le flasher web, en cases a cocher. Une fonctionnalite peut
# avoir plusieurs variantes mutuellement exclusives : elles s'affichent en sous-choix quand la
# case est cochee. Chaque variante pointe vers un tweak de tweaks/.
# Le flasher web n'envoie que par USB (CONFIG > UPGRADE) : il ne propose que des tweaks qui gardent
# cette mise a jour par USB. 6ch-multiout (la casse) et sdvintage-snare restent dans build.py.
# Vrais moteurs du Syntakt ("engines") : une case par moteur du catalogue de gen_syntakt_engines.py ;
# chaque combinaison cochee pointe vers son tweak syntakt-<moteurs> ; la carte est « testee » si au moins une
# combinaison l'est (HW_TESTED de gen_syntakt_engines.py).
# excludes : cartes qu'on ne peut pas cocher ensemble (cocher l'une decoche l'autre).
# includes : tweaks deja contenus dans cette fonctionnalite ; ils s'en excluent comme avec excludes, et le flasher
# les affiche coches et verrouilles, « inclus avec … », tant qu'elle est cochee.
# requires : carte sans laquelle celle-ci ne marche pas (un ajout a Model-TG). La cocher coche aussi l'autre (avec
# les exclusions de l'autre, comme si on l'avait cochee) ; decocher l'autre la decoche. ref_mainos.py ne compte que
# les combinaisons ou l'autre carte est cochee. Elle a les memes cles « with » que l'autre carte, et chacun de ses
# tweaks demande (« requires » de son JSON) le tweak correspondant de l'autre : check_requires le verifie.
# Les moteurs s'ajoutent en machines supplementaires : sdvintage-exact (a la place de SNARE) reste dans build.py.
# status : "tested" (flashe sur un vrai Model:Cycles) ou "experimental".
# credit : auteur du travail d'origine, affiche sur la carte (voir aussi les credits de la page) ; sans « repo »
# (un mod recu sans depot public), la carte dit « d'apres un mod de … », sans lien.
# license : fichier de licence (dans tweaks/model-cycles_OS1.13/) du code tiers que la carte embarque ; servi a cote
# de la page (docs/flasher/<license>.txt) et lie depuis la carte.
# cat : rubrique du flasher, une de CATS (meme liste que CATS dans docs/flasher/app.js, plus « other »). Sans cat,
# la carte s'affiche a la fin, dans « Autres mods » (avertissement ici). L'ordre de FEATURES reste l'ordre du build
# (cles de REF_MAINOS), quel que soit l'ordre d'affichage par rubriques.
# joins : cartes qui contiennent deja cette fonctionnalite quand elles sont cochees aussi, dans l'ordre des machines
# (MACRO avec les moteurs du Syntakt, notes/50 ; ACID avec eux et avec MACRO, notes/54 §11). La premiere cochee (la
# racine) construit la version qui porte toutes les cartes cochees qui la rejoignent ; ces cartes n'ajoutent alors
# aucun tweak. Cle de la version : leurs id, dans l'ordre de FEATURES, joints par « + » (macro, acid, macro+acid).
# Une carte de moteurs porte combo[<cle>] (id, tg, tested, tg_tested, comme la combinaison elle-meme) ; une carte a
# variante (MACRO) porte versions[<cle>] (fichier, fichier avec Model-TG). Les deux listent leurs cles dans joined.
# Pour ajouter une fonctionnalite : ecrire son tweak JSON, puis l'ajouter ici.
# package (model27, notes/61): an added machine composed in the page, by its package id under tools/machines/, in
# place of variants. Its excludes are not written here: they are computed from its committed tweak alone (the
# package's own generator writes it, its "conflicts") against the other cards offered, so they cannot drift.
CATS = ("pack", "sound", "seq", "live", "screen", "io")
ALL_FEATURES = [
    {
        "id": "usb6",
        "cat": "io",
        "label": "Sortie USB 6 canaux separes",
        "desc": "Chaque piste sort sur son propre canal USB (48 kHz / 32 bits). Le mix stereo "
                "n'est plus envoye en USB : tu melanges les 6 pistes dans ton logiciel.",
        "status": "tested",
        "credit": {"kind": "based", "who": "scottmetoyer", "repo": "scottmetoyer/ms-multi-output"},
        "license": "LICENSE-ms-multi-output",
        "variants": [
            {"file": "11-6ch-usbup", "label": None},
        ],
    },
    {
        "id": "model-tg",
        "cat": "pack",
        "label": "Model-TG",
        "desc": "Machine Sampler, reechantillonnage, retrig et effets master, et plus.",
        "status": "experimental",
        "credit": {"kind": "by", "who": "TinyGregAudio", "repo": "TinyGregAudio/Model-TG"},
        # Model-TG contient deja les tweaks de drumkilla : le flasher les affiche coches et verrouilles
        # (« inclus avec Model-TG ») tant que Model-TG est coche, sans les ajouter au build
        "includes": ["latching-mute", "trig-preview", "browser-scroll"],
        "license": "LICENSE-Model-TG",
        "variants": [
            {"file": "30-model-tg", "label": None},
        ],
        # avec les moteurs du Syntakt : la base de la version combinee (notes/31), et pour chaque combinaison de
        # moteurs son tweak syntakt-tg-<moteurs> (« tg » des combinaisons de la carte des moteurs) ; de meme avec
        # la machine MACRO (notes/43), qui prend alors macro-tg
        "with": {"syntakt": "30-model-tg-st", "macro": "30-model-tg-st", "acid": "30-model-tg-st"},
    },
    {
        "id": "sample-preview",
        "cat": "screen",
        "label": "Ecoute des samples (Model-TG)",
        "desc": "Sur une piste Sampler, dans le navigateur de samples, le pad de la piste (ou ses touches en mode "
                "clavier) joue le sample sous le curseur, comme pour les presets. Un sample pas encore en memoire "
                "se charge au premier appui. Demande Model-TG.",
        "status": "tested",
        "credit": {"kind": "based", "who": "TinyGregAudio", "repo": "TinyGregAudio/Model-TG"},
        "license": "LICENSE-Model-TG",          # pv_parse reprend un passage de son pool_store_hook
        "requires": "model-tg",
        "variants": [
            {"file": "33-sample-preview", "label": None},
        ],
        # avec les moteurs du Syntakt, Model-TG devient model-tg-st : l'ecoute prend la version faite pour lui
        "with": {"syntakt": "33-sample-preview-st", "macro": "33-sample-preview-st",
                 "acid": "33-sample-preview-st"},
    },
    {
        "id": "latching-mute",
        "cat": "live",
        "label": "Mode mute verrouille",
        "desc": "Maintiens TRK et tape FUNC : le mode mute reste actif, tu mutes les pistes sans tenir FUNC. "
                "Un appui court sur FUNC en sort.",
        "status": "tested",
        "credit": {"kind": "by", "who": "drumkilla", "repo": "drumkilla/elektron-model-tweaks"},
        "license": "LICENSE-elektron-model-tweaks",
        "variants": [
            {"file": "01-latching-mute", "label": None},
        ],
    },
    {
        "id": "control-all-config",
        "cat": "live",
        "label": "Control All : choix des pistes",
        "desc": "TRACK + TRIG 1-6 retire une piste de Control All (TRACK tenu + potard) ou l'y remet ; TRACK tenu, "
                "les TRIG 1-6 montrent les pistes qui suivent. La piste active suit toujours. Choix en RAM.",
        # tested on the Model:Cycles on 2026-10-22, flashed from model27's page alone and with SAMPLE (notes/58 §9)
        "status": "tested",
        "credit": {"kind": "by", "who": "durchgemacht", "repo": "durchgemacht/cycles-control-all-config"},
        "license": "LICENSE-Control-All-Config",
        "variants": [
            {"file": "49-control-all-config", "label": None},
        ],
    },
    {
        "id": "trig-preview",
        "cat": "seq",
        "label": "Ecoute d'un pas (TRIG + PAGE)",
        "desc": "Sequenceur a l'arret (ou en pause), maintiens un pas et appuie sur PAGE : le pas joue avec sa note, "
                "sa longueur et ses p-locks.",
        "status": "tested",
        "credit": {"kind": "by", "who": "drumkilla", "repo": "drumkilla/elektron-model-tweaks"},
        "license": "LICENSE-elektron-model-tweaks",
        "variants": [
            {"file": "02-trig-preview", "label": None},
        ],
    },
    {
        "id": "browser-scroll",
        "cat": "screen",
        "label": "Defilement des noms longs",
        "desc": "Dans le navigateur de sons, un nom trop long pour l'ecran defile.",
        "status": "tested",
        "credit": {"kind": "by", "who": "drumkilla", "repo": "drumkilla/elektron-model-tweaks"},
        "license": "LICENSE-elektron-model-tweaks",
        "variants": [
            {"file": "03-browser-scroll", "label": None},
        ],
    },
    {
        "id": "trig-hold",
        "cat": "seq",
        "label": "Effacer un trig plus facilement",
        "desc": "Un appui sur une touche de pas qui porte deja un trig l'efface si tu relaches en moins d'une "
                "demi-seconde (0,2 s avec l'OS d'origine). Tenu plus longtemps, le trig reste et ses reglages s'affichent.",
        "status": "tested",
        "credit": None,
        "variants": [
            {"file": "41-trig-hold", "label": None},
        ],
    },
    {
        "id": "arp",
        "cat": "seq",
        "label": "Arpegiateur",
        "desc": "Le retrig devient un arpegiateur : plusieurs notes tenues avec RETRIG (ou A.On) se jouent l'une "
                "apres l'autre. FUNC + RETRIG : sens (Arp) et octaves (Oct), enregistres avec le pattern. "
                "En live rec, les notes jouees par l'arpege sont enregistrees une a une.",
        "status": "tested",
        "credit": None,
        "variants": [
            {"file": "40-arp", "label": None},
        ],
    },
    {
        "id": "tempo-max",
        "cat": "seq",
        "label": "Tempo jusqu'a 546 BPM",
        "desc": "Le tempo monte jusqu'a 546 BPM au lieu de 300 (molette, tap tempo, horloge MIDI recue). "
                "546 est le plafond du format des projets.",
        "status": "tested",
        "credit": None,
        "variants": [
            {"file": "42-tempo-max", "label": None},
        ],
    },
    {
        "id": "boot-anim",
        "cat": "screen",
        "label": "Animation de demarrage modded-cycles",
        "desc": "Au demarrage, les quatre carres du logo apparaissent un par un puis modded-cycles s'ecrit "
                "dessous, a la place des carreaux qui clignotent. Meme duree qu'a l'origine.",
        "status": "tested",
        "credit": None,
        "variants": [
            {"file": "43-boot-anim", "label": None},
        ],
    },
    {
        "id": "multiline-browser",
        "cat": "screen",
        "label": "Navigateur sur plusieurs lignes",
        "desc": "Le navigateur de sons, de dossiers et d'echantillons affiche 3 noms a la fois, en petite police, "
                "au lieu d'un seul en gros caracteres. > devant le nom sous le curseur ; le son charge reste inverse.",
        "status": "tested",
        "credit": None,                  # idee : un script d'un membre de la communaute (notes/40), nom a venir
        "variants": [
            {"file": "44-multiline-browser", "label": None},
        ],
    },
    {
        "id": "level-pan-values",
        "cat": "screen",
        "label": "Volume et pan en chiffres",
        "desc": "Sur l'ecran principal, LEVEL/DATA affiche le volume de la piste (0 a 127) en chiffres, FUNC + "
                "LEVEL/DATA son pan (-64 a 63), pendant 3 s. LEVEL/DATA y avance de 1 par cran au lieu de 2.",
        "status": "tested",
        "credit": {"kind": "based", "who": "djd_oz"},
        "variants": [
            {"file": "46-level-pan-values", "label": None},
        ],
    },
    {
        "id": "trigless-dim",
        "cat": "seq",
        "label": "Trigless trigs attenues",
        "desc": "Une touche de pas qui porte un trigless trig (FUNC + touche) s'allume attenuee au lieu de pleine "
                "lumiere : on la distingue d'un trig de note. Elle garde son clignotement habituel.",
        "status": "tested",
        "credit": {"kind": "based", "who": "djd_oz"},
        "variants": [
            {"file": "47-trigless-dim", "label": None},
        ],
    },
    {
        "id": "midi-both",
        "cat": "io",
        "label": "MIDI OUT pendant THRU",
        "desc": "Avec THR choisi dans CONFIG > MIDI > PORTS > OUT/THRU, le Cycles relaie le MIDI recu et envoie aussi "
                "son horloge, ses notes et ses parametres. OUT ne change pas, le menu non plus.",
        "status": "tested",                # par AveyCole, sur sa machine (notes/53 §9)
        "credit": {"kind": "by", "who": "AveyCole", "repo": "AveyCole/Modded-Cycles"},
        "excludes": ["midi-live-both"],
        "variants": [
            {"file": "50-midi-both", "label": None},
        ],
    },
    {
        "id": "midi-live-both",
        "cat": "io",
        "label": "Basculer MIDI OUT + THRU en direct",
        "desc": "Sur la ligne OUT/THRU qui affiche THR, FUNC + appui sur le potard LEVEL/DATA ajoute au relais l'envoi "
                "de l'horloge, des notes et des parametres du Cycles, ou le retire. L'ecran reste sur THR.",
        "status": "tested",                # par AveyCole, sur sa machine (notes/53 §9)
        "credit": {"kind": "by", "who": "AveyCole", "repo": "AveyCole/Modded-Cycles"},
        "excludes": ["midi-both"],
        "variants": [
            {"file": "51-midi-live-both", "label": None},
        ],
    },
    {
        "id": "macro",
        "cat": "sound",
        "label": "Machine MACRO",
        "desc": "Une machine ajoutee apres Chord (apres le Sampler avec Model-TG, apres les moteurs du Syntakt s'ils "
                "sont coches aussi) : les 47 modeles du code libre "
                "de Braids d'Emilie Gillet. SHAPE choisit le modele, COLOR et SWEEP le reglent, CONTOUR ouvre le "
                "timbre avec l'enveloppe, FUNC + PITCH donne le lo-fi (RATE a gauche, BITS a droite).",
        # 13 modeles a 48 kHz (notes/55) : testes sur la machine le 11/10/2026 ; le lo-fi par FUNC + PITCH et son
        # affichage (notes/55 §8, 1.54) : testes sur la machine le 12/10/2026
        "status": "tested",
        "credit": {"kind": "based", "who": "Émilie Gillet", "repo": "pichenettes/eurorack"},
        "license": "LICENSE-Braids",
        # avec les moteurs du Syntakt : la combinaison de moteurs prend sa version avec MACRO (notes/50)
        "joins": ["syntakt"],
        "variants": [
            {"file": "25-macro", "label": None},
        ],
        # avec Model-TG : la version qui s'ajoute apres model-tg-st (Model-TG prend cette base, « with » ci-dessus)
        "with": {"model-tg": "32-macro-tg"},
        # avec ACID, sans les moteurs : MACRO puis ACID (notes/54 §11 ; « tested » : gen_acid_combos.HW_TESTED)
        "versions": {"acid": {"file": "25-macro-acid", "tg": "32-macro-acid-tg"}},
    },
    {
        "id": "acid",
        "cat": "sound",
        "label": "Machine ACID",
        "desc": "Une machine ajoutee apres Chord (apres le Sampler avec Model-TG, puis les moteurs du Syntakt et "
                "MACRO s'ils sont coches aussi : toujours la derniere) : une basse acide a la maniere de la TB-303, "
                "d'apres le modele libre d'Open303. COLOR = cutoff, SHAPE = resonance, SWEEP = env mod, "
                "CONTOUR = saturation (drive), PUNCH = scie ou carre ; une LEN plus longue que l'ecart au trig "
                "suivant fait glisser la note.",
        "status": "tested",
        "credit": {"kind": "based", "who": "Robin Schmidt", "repo": "RobinSchmidt/Open303"},
        "license": "LICENSE-Open303",
        # meme place et meme mecanique que MACRO et les moteurs du Syntakt (notes/54 §7) : avec eux, leurs versions
        # avec ACID en derniere machine (gen_acid_combos.py, notes/54 §11)
        "joins": ["syntakt", "macro"],
        "variants": [
            {"file": "26-acid", "label": None},
        ],
        # avec Model-TG : la version qui s'ajoute apres model-tg-st (Model-TG prend cette base, « with » ci-dessus)
        "with": {"model-tg": "35-acid-tg"},
    },
    {
        "id": "sampler",
        "cat": "sound",
        "label": "SAMPLE machine (Cycles One-Shot)",
        "desc": "One extra machine after Chord: a one-shot sampler for samples on the +Drive. Pick the sample in the "
                "PRESET browser (FUNC + MACHINE); it is saved with the sound. COLOR = Start, SHAPE = Length, "
                "SWEEP = the Model:Samples' filter (lowpass / off / highpass), CONTOUR = Reso; the main screen "
                "shows the waveform with the start and end marked.",
        # tested on the Model:Cycles on 2026-10-22, flashed from this page alone and from the command line next to
        # the reference machine (notes/60 §12-13)
        "status": "tested",
        "credit": {"kind": "by", "who": "durchgemacht", "repo": "durchgemacht/cycles-one-shot"},
        "license": "LICENSE-One-Shot",
        # composed in the page from its package (notes/61): alone it gives 27-sampler.json byte for byte. Its
        # excludes come from that tweak's conflicts (tools/gen_sampler.py): the payload window of the other added
        # machines, the sound record functions of Model-TG and the track filter, the browser of sample preview
        "package": "sampler",
    },
    {
        "id": "digidelay",
        "cat": "sound",
        "label": "Digital Delay (effect)",
        "desc": "A second delay for the delay slot: bright and clean, up to 5.4 s, each repeat a little thinner in the "
                "lows. Hold TRACK and turn Delay Time to switch the pattern's delay between the stock Delay and "
                "Digital; Time and Fdbk keep their knobs.",
        # PPPCCC's digital delay (2.0.0) ported to an effect package, their sound bit for bit in emulation; tested
        # on the Model:Cycles on 2026-10-27 from the command line, then flashed from this page alone and with SAMPLE
        # (notes/68 §18, §19)
        "status": "tested",
        "credit": {"kind": "based", "who": "gialloinfuso", "repo": "gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods"},
        "license": "LICENSE-PPPCCC",
        # an effect composed in the page from its package (notes/68 §19), with the machines ticked: alone it gives
        # 39-digidelay.json byte for byte, whose conflicts give its excludes
        "package": "digidelay",
    },
    {
        "id": "pots",
        "cat": "sound",
        "label": "POTS (effect)",
        "desc": "A delay whose repeats go down an old telephone line: each pass darker and narrower, a little out of "
                "tune, fading and now and then dropping out, with a coarse grain on the tail. Hold TRACK and turn "
                "Delay Time to switch the pattern's delay between the stock Delay, Digital and POTS; Time and Fdbk "
                "keep their knobs.",
        # model27's own (notes/69), its sound settled in a float prototype; bit for bit its host build in emulation;
        # the 24 kHz build tested on the Model:Cycles (notes/69 §18, §22.5); the loop at 12 kHz of §23, lighter for a
        # busy pattern, tested too: flashed from this page on 2026-10-29, the project that lagged without lag (§23.6)
        "status": "tested",
        "credit": None,
        # an effect composed in the page from its package (notes/69 §19), with the machines and Digital ticked:
        # alone it gives 70-pots.json byte for byte, whose conflicts give its excludes
        "package": "pots",
    },
    {
        "id": "trig-cond-order",
        "cat": "seq",
        "label": "Trig conditions, A:B before the percentages",
        "desc": "A trig held + CHANCE goes FILL ... !1st, then 1:2 ... 8:8, then 1% ... 99%, and the five dots under the "
                "value follow that order. A trig keeps the same condition as on the stock OS.",
        # model27's own (notes/70); tested on the Model:Cycles from the command line on 2026-10-30, the order and the
        # five dots (notes/70 §9); experimental here until flashed from this page
        "status": "experimental",
        "credit": None,
        "variants": [
            {"file": "80-trig-cond-order", "label": None},
        ],
    },
    {
        "id": "chord-keys",
        "cat": "live",
        "label": "Accords de gamme sur TRIG 1–16",
        "desc": "Une piste CHORD, sept modes et une extension par degré. TRIG 1–7 jouent I–VII, "
                "8–14 une octave plus haut, 15–16 I–II deux octaves plus haut. T1–T6 gardent leurs fonctions. "
                "Réglages dans FUNC + RETRIG, sauvés avec le pattern.",
        "status": "tested",
        "credit": {"kind": "by", "who": "Nico Heuser", "repo": "byNicoHeuser"},
        "excludes": ["model-tg"],
        "variants": [{"file": "45-chord-keys", "label": None}],
    },
    {
        "id": "track-filter",
        "cat": "sound",
        "label": "Filtre par piste (LP / OFF / HP)",
        "desc": "MACHINES tenu + SWEEP : un filtre par piste, passe-bas a gauche, rien au centre, passe-haut a droite. "
                "CONTOUR : resonance ; COLOR et SHAPE : enveloppe du filtre (quantite, decay). P-locks, LFO, CC 74 / 71.",
        "status": "tested",
        "credit": None,
        # meme geste que le filtre de Model-TG (MACHINES + SWEEP / CONTOUR) : pas ensemble pour l'instant (notes/47 §7, §11)
        "excludes": ["model-tg"],
        "variants": [
            {"file": "48-track-filter", "label": None},
        ],
    },
    {
        "id": "lfo-plus",
        "cat": "sound",
        "label": "LFO 2, 3, 4",
        "desc": "Trois LFO de plus par piste : sur la page LFO, chaque nouvel appui sur [LFO] passe a LFO 2, 3, 4. "
                "Vitesse, multiplicateur, forme, destination et profondeur propres ; fondu, phase et mode communs "
                "avec LFO 1. LFO 2 est sauve avec le son et se p-locke, LFO 3 et 4 servent au live. Avec ou sans "
                "Model-TG.",
        "status": "tested",
        "credit": {"kind": "based", "who": "DavidCaruso"},
        "excludes": ["track-filter"],   # memes k 28..31 et octets +88..+91 du son (notes/56 §3.6)
        "variants": [
            {"file": "60-lfo-plus", "label": None},
        ],
    },
    {
        "id": "syntakt",
        "cat": "sound",
        "label": "Vrais moteurs du Syntakt",
        "desc": "Les moteurs du Syntakt, extraits de TON fichier Syntakt_OS1.42.syx (a deposer a l'etape 2), "
                "en machines supplementaires apres les 6 d'origine : coche ceux que tu veux. "
                "Identiques au Syntakt en emulation.",
        "status": "tested",
        "credit": None,
        "needs": "syntakt",
        "engines": True,
    },
]

# model27 offers a short list of cards. The other definitions above stay as they are, for the command-line build
# (every tweak of tweaks/ is still built by tools/build.py) and so that merges from upstream apply cleanly; a card
# comes back into the flasher by adding its id here, once it has been reviewed against the Cycles Mod Standard.
OFFERED = ("sampler", "digidelay", "pots", "control-all-config", "trig-cond-order")
FEATURES = [f for f in ALL_FEATURES if f["id"] in OFFERED]
_missing = set(OFFERED) - {f["id"] for f in FEATURES}
if _missing:
    sys.exit(f"!! OFFERED names cards that do not exist: {sorted(_missing)}")


def hosts(f):
    return list(f.get("joins") or [])


def join_keys(f):
    """Cles des versions d'une carte hote : ses cartes jointes (joins), chaque ensemble non vide, dans l'ordre de
    FEATURES, joint par « + »."""
    joined = [g["id"] for g in FEATURES if f["id"] in hosts(g)]
    return ["+".join(x for x in joined if k >> joined.index(x) & 1) for k in range(1, 1 << len(joined))]


def engine_versions():
    """Versions d'une combinaison de moteurs avec les cartes jointes : cle -> (codes, tg) -> (id, teste)."""
    import gen_acid_combos as gac
    import gen_macro_syntakt as gms
    return {
        "macro": lambda codes, tg: (gms.tweak_id(codes, tg=tg), tuple(codes) in (gms.HW_TESTED_TG if tg else gms.HW_TESTED)),
        "acid": lambda codes, tg: (gac.tweak_id(codes, tg, macro=False),
                                   (tuple(codes), False) in (gac.HW_TESTED_TG if tg else gac.HW_TESTED)),
        "macro+acid": lambda codes, tg: (gac.tweak_id(codes, tg, macro=True),
                                         (tuple(codes), True) in (gac.HW_TESTED_TG if tg else gac.HW_TESTED)),
    }


def engine_feature(f, load):
    """Carte des vrais moteurs du Syntakt : les moteurs du catalogue et le tweak de chaque combinaison, seule et avec
    les cartes jointes (joins)."""
    import gen_syntakt_engines as gs
    engines = [{"code": c, "name": m["name"], "label": m["label"]} for c, m in gs.CATALOG.items()]
    keys, known = join_keys(f), engine_versions()
    if set(keys) - set(known):
        sys.exit(f"!! {f['id']} : pas de version des moteurs pour {sorted(set(keys) - set(known))} (joins)")
    combos = []
    for codes in gs.subsets():
        t = load(gs.subset_id(codes))
        c = {"id": t["id"], "engines": codes, "tested": tuple(codes) in gs.HW_TESTED,
             "label": ", ".join(gs.CATALOG[c]["name"] for c in codes),
             "tg": load(gs.tweak_id(codes, tg=True))["id"],      # avec Model-TG (notes/31)
             "tg_tested": tuple(codes) in gs.HW_TESTED_TG}
        for k in keys:                                           # avec MACRO (notes/50), ACID (notes/54 §11)
            (tid, ok), (tid_tg, ok_tg) = known[k](codes, False), known[k](codes, True)
            c[k] = {"id": load(tid)["id"], "tg": load(tid_tg)["id"], "tested": ok, "tg_tested": ok_tg}
        combos.append(c)
    return engines, combos, keys


SHARED_MIN = 2048      # valeurs partagees : chaines ou listes d'au moins 2 Ko en JSON compact


def share(tweaks):
    """Valeurs repetees d'un tweak a l'autre (le code de MACRO dans chaque combinaison avec les moteurs du Syntakt,
    notes/50) : rangees une seule fois dans "shared" et remplacees par {"$shared": k}. tweaks.js les remet en place
    au chargement (HYDRATE), read_js() de meme en Python : les tweaks lus sont ceux de tweaks/, a l'identique."""
    def key(v):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    count = collections.Counter()

    def walk(v):
        if isinstance(v, (str, list)) and len(k := key(v)) >= SHARED_MIN:
            count[k] += 1
        for x in v if isinstance(v, list) else v.values() if isinstance(v, dict) else ():
            walk(x)
    for t in tweaks:
        walk(t)
    shared, index = [], {}

    def sub(v):
        if isinstance(v, (str, list)) and count[k := key(v)] > 1:
            if k not in index:
                index[k] = len(shared)
                shared.append(v)
            return {"$shared": index[k]}
        if isinstance(v, list):
            return [sub(x) for x in v]
        if isinstance(v, dict):
            return {a: sub(x) for a, x in v.items()}
        return v
    return [sub(t) for t in tweaks], shared


# remet les valeurs partagees en place (share) ; une liste partagee est recopiee pour chaque tweak, une chaine non
HYDRATE = (
    "(function (tw) {\n"
    "  const s = tw.shared || [];\n"
    "  delete tw.shared;\n"
    "  const h = (v) => Array.isArray(v) ? v.map(h) : v && typeof v === \"object\"\n"
    "    ? (\"$shared\" in v ? (Array.isArray(s[v.$shared]) ? JSON.parse(JSON.stringify(s[v.$shared])) : s[v.$shared])\n"
    "      : Object.fromEntries(Object.entries(v).map(([k, x]) => [k, h(x)]))) : v;\n"
    "  tw.tweaks = tw.tweaks.map(h);\n"
    "})(window.MC_TWEAKS);\n"
)


def read_js(text):
    """Contenu de tweaks.js (window.MC_TWEAKS), valeurs partagees remises en place comme dans la page."""
    start = text.index("window.MC_TWEAKS = ") + len("window.MC_TWEAKS = ")
    tw = json.JSONDecoder().raw_decode(text, start)[0]
    s = tw.pop("shared", [])

    def h(v):
        if isinstance(v, list):
            return [h(x) for x in v]
        if isinstance(v, dict):
            return copy.deepcopy(s[v["$shared"]]) if "$shared" in v else {k: h(x) for k, x in v.items()}
        return v
    tw["tweaks"] = [h(t) for t in tw["tweaks"]]
    return tw
def check_requires(features, by_id):
    """Cartes « requires » : la carte demandee existe (carte a variantes, pas les moteurs), et chaque tweak de
    l'ajout demande (champ « requires » de son JSON) le tweak correspondant de cette carte : une variante, une des
    variantes de l'autre carte ; le tweak « with » d'une autre carte, le tweak « with » de l'autre carte pour la
    meme. Les deux cartes ont donc les memes cles « with ». Sinon le flasher proposerait un build que build.py et
    builder.js refusent (ou un ajout pose sur la mauvaise version de l'autre carte)."""
    cards = {f["id"]: f for f in features}
    for f in features:
        rid = f.get("requires")
        if not rid:
            continue
        need = cards.get(rid)
        if rid == f["id"]:
            raise SystemExit(f"!! FEATURES : la carte {f['id']} se demande elle-meme (requires)")
        if need is None:
            raise SystemExit(f"!! FEATURES : la carte {f['id']} demande (requires) la carte {rid!r}, qui n'existe pas")
        if f.get("engines") or need.get("engines"):
            raise SystemExit(f"!! FEATURES : requires de {f['id']} vers {rid} : seulement entre cartes a variantes, "
                             "pas avec la carte des moteurs")
        base = [v["id"] for v in need["variants"]]
        for v in f["variants"]:
            if not set(base) & set(by_id[v["id"]].get("requires", [])):
                raise SystemExit(f"!! FEATURES : la carte {f['id']} demande {rid}, mais le tweak {v['id']} ne demande "
                                 f"aucun de {', '.join(base)} (champ « requires » de son JSON)")
        w, nw = f.get("with", {}), need.get("with", {})
        if set(w) != set(nw):
            raise SystemExit(f"!! FEATURES : la carte {f['id']} doit avoir les memes cles « with » que {rid} "
                             f"({', '.join(sorted(w)) or 'aucune'} contre {', '.join(sorted(nw)) or 'aucune'})")
        for g, tid in w.items():
            if nw[g] not in by_id[tid].get("requires", []):
                raise SystemExit(f"!! FEATURES : avec {g}, la carte {f['id']} prend {tid} et {rid} prend {nw[g]}, "
                                 f"mais {tid} ne demande pas {nw[g]} (champ « requires » de son JSON)")


def card_tweaks(feat):
    """The tweak ids a card of the page can build: its variants, its tweak with another card (with), its versions with
    the cards it holds, each engine combination alone, with Model-TG and with the cards that join it."""
    ids = [v["id"] for v in feat.get("variants", [])] + list(feat.get("with", {}).values())
    for v in feat.get("versions", {}).values():
        ids += [v["id"], v["tg"]]
    for c in feat.get("combos", []):
        ids += [c["id"], c["tg"]] + [x for k in feat.get("joined", []) for x in (c[k]["id"], c[k]["tg"])]
    return ids


def machine_excludes(features, by_id):
    """A machine card's excludes (notes/61 §5): the other cards offered that build a tweak its committed tweak alone
    conflicts with. Machine cards never exclude each other: the page composes them together."""
    for feat in features:
        if not feat.get("package"):
            continue
        alone = by_id.get(feat["package"])
        if not alone:
            sys.exit(f"!! {feat['id']}: no tweak {feat['package']!r} in tweaks/ (the package's generator writes it alone)")
        clash = set(alone.get("conflicts", []))
        ex = [g["id"] for g in features if not g.get("package") and clash & set(card_tweaks(g))]
        if ex:
            feat["excludes"] = ex


def render():
    from crossflash import OFFICIAL            # empreintes des OS officiels, source unique (tools/crossflash.py)
    device = json.loads((DEV_DIR / "device.json").read_text(encoding="utf-8"))
    tweaks, seen, features, packages = [], {}, [], {}
    by_id = {}
    for p in sorted(DEV_DIR.glob("*.json")):
        if p.name != "device.json":
            t = json.loads(p.read_text(encoding="utf-8"))
            by_id[t["id"]] = t

    def load(tid):
        t = by_id[tid]
        if tid not in seen:
            seen[tid] = True
            tweaks.append(t)
        return t
    for f in FEATURES:
        feat = {"id": f["id"], "label": f["label"], "desc": f["desc"], "status": f["status"], "credit": f["credit"]}
        if f.get("cat"):                        # rubrique de la carte dans le flasher
            if f["cat"] not in CATS:
                sys.exit(f"!! {f['id']} : cat {f['cat']!r} inconnue (une de {', '.join(CATS)})")
            feat["cat"] = f["cat"]
        else:
            print(f"attention : {f['id']} n'a pas de cat, il ira dans « Autres mods »", file=sys.stderr)
        if f.get("requires"):                   # carte qui doit etre cochee aussi (verifiee par check_requires)
            feat["requires"] = f["requires"]
        if f.get("package"):                    # an added machine, composed in the page (notes/61)
            import compose
            bad = [k for k in ("variants", "excludes", "includes", "requires", "with", "joins", "versions", "engines")
                   if f.get(k)]
            if bad:
                sys.exit(f"!! {f['id']}: a machine card takes no {', '.join(bad)} (its excludes are computed)")
            feat["package"] = f["package"]
            packages[f["package"]] = compose.web_package(f["package"])
        elif f.get("engines"):
            feat["engines"], feat["combos"], keys = engine_feature(f, load)
            if keys:
                feat["joined"] = keys
            feat["status"] = "tested" if any(c["tested"] or c["tg_tested"] for c in feat["combos"]) else "experimental"
        else:
            by_file = {json.loads((DEV_DIR / f"{v['file']}.json").read_text(encoding="utf-8"))["id"]: v for v in f["variants"]}
            feat["variants"] = [{"id": load(tid)["id"], "label": v["label"]} for tid, v in by_file.items()]
        if f.get("needs"):
            feat["needs"] = f["needs"]
        if f.get("excludes"):
            feat["excludes"] = f["excludes"]
        if f.get("includes"):
            feat["includes"] = f["includes"]
        if f.get("joins"):                      # contenue dans les versions de ces cartes (racine : la 1re cochee)
            ids = [g["id"] for g in FEATURES]
            for i, h in enumerate(hosts(f)):
                g = next((x for x in FEATURES if x["id"] == h), None)
                if not g or not (g.get("engines") or g.get("versions")):
                    sys.exit(f"!! {f['id']} : joins {h!r} n'est ni une carte de moteurs ni une carte a versions")
                # les hotes d'un hote viennent avant lui : la 1re cochee est toujours la racine
                if any(x not in hosts(f)[:i] for x in hosts(g)) or ids.index(h) > ids.index(f["id"]) and not g.get("engines"):
                    sys.exit(f"!! {f['id']} : joins {hosts(f)} dans le mauvais ordre")
            feat["joins"] = hosts(f)
        if f.get("with"):                       # autre tweak quand une autre carte est cochee aussi
            feat["with"] = {g: load(json.loads((DEV_DIR / f"{v}.json").read_text(encoding="utf-8"))["id"])["id"]
                            for g, v in f["with"].items()}
        if f.get("versions"):                   # carte a variante qui en heberge d'autres (MACRO avec ACID)
            import gen_acid_combos as gac
            if sorted(f["versions"]) != sorted(join_keys(f)):
                sys.exit(f"!! {f['id']} : versions {sorted(f['versions'])} au lieu de {join_keys(f)}")
            fid = lambda v: json.loads((DEV_DIR / f"{v}.json").read_text(encoding="utf-8"))["id"]
            feat["versions"] = {k: {"id": load(fid(v["file"]))["id"], "tg": load(fid(v["tg"]))["id"],
                                    "tested": ((), True) in gac.HW_TESTED, "tg_tested": ((), True) in gac.HW_TESTED_TG}
                                for k, v in f["versions"].items()}
            feat["joined"] = join_keys(f)
        if f.get("license"):                    # texte de la licence, servi a cote de la page (licenses())
            feat["license"] = f["license"] + ".txt"
        features.append(feat)
    check_requires(features, by_id)
    machine_excludes(features, by_id)
    tweaks, shared = share(tweaks)
    cl = __import__("claims")
    claimed = cl.tweak_claims()

    def card_claims(feat):                  # every tweak the card can build, its package's for a machine card
        out = {}
        for tid in ([feat["package"]] if feat.get("package") else []) + card_tweaks(feat):
            if tid in claimed:
                out = cl.merge(out, claimed[tid])
        return out
    by_feat = {f["id"]: f for f in features}
    reasons = {f"{f['id']}|{g}": kinds for f in features for g in f.get("excludes", []) if g in by_feat
               for kinds in [cl.clash_kinds(card_claims(f), card_claims(by_feat[g]))] if kinds}
    payload = {
        "device": {k: device[k] for k in ("device", "os", "section_sha256", "stock_syx_sha256", "cave_refs_ok")
                   if k in device},
        "tweaks": tweaks,
        "features": features,
        # model27, Level B (notes/61): the packages of the machine cards and the registrar's frame they are composed in
        "packages": packages,
        "registrar": json.loads((HERE / "machines" / "registrar" / "frame.json").read_text(encoding="utf-8"))
        if packages else None,
        # model27, Level B (notes/63, B4e): the builder's parts, which the machines' shortcuts and shared points need
        "parts": {pid: __import__("compose").web_part(pid) for pid in ("shortcuts", "dispatch", "fxslot")}
        if packages else None,
        # model27, Level C (notes/65, C2): the declared claims of the offered tweaks, which the machine cards are
        # composed against (tools/claims.py's to_json form)
        "claims": {t["id"]: claimed[t["id"]] for t in tweaks if t["id"] in claimed} if packages else None,
        # model27, Level C (notes/65, C4): for two cards that exclude each other, the kinds of clash their claims
        # show ("<card>|<card>": [[kind, combination]]); the page says the first where no hand-written reason exists
        "clash_reasons": reasons,
        # onglet « OS Samples » : l'OS Model:Samples officiel, mis dans le conteneur du Cycles (crossflash)
        "samples": {"syx_sha256": OFFICIAL["samples"]["syx"], "main_sha256": OFFICIAL["samples"]["main"],
                    "download": "https://www.elektron.se/support-downloads/modelsamples"},
        # fonctionnalités « needs: syntakt » : le fichier officiel Syntakt_OS1.42.syx de l'utilisateur
        "syntakt": {"download": "https://www.elektron.se/support-downloads/syntakt"},
        "shared": shared,                       # valeurs repetees d'un tweak a l'autre (share, HYDRATE)
    }
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    text = (
        "/* Genere par tools/gen_flasher_tweaks.py depuis tweaks/model-cycles_OS1.13/.\n"
        " * NE PAS editer a la main : relance le script apres avoir change un tweak. */\n"
        "window.MC_TWEAKS = " + body + ";\n" + HYDRATE
    )
    if read_js(text)["tweaks"] != [by_id[t["id"]] for t in tweaks]:
        sys.exit("!! valeurs partagees : tweaks.js ne redonne pas les tweaks de tweaks/")
    return text


# Licences du code tiers que la page embarque hors des cartes : builder.js est un portage de mtlib (drumkilla),
# lui-meme fonde sur elektron-firmware-tool (Marcel Bierling). Voir THIRD-PARTY-NOTICES.md.
PAGE_LICENSES = {
    "LICENSE-elektron-model-tweaks": DEV_DIR / "LICENSE-elektron-model-tweaks",
    "LICENSE-elektron-firmware-tool": ROOT / "tools" / "mtlib" / "LICENSE-elektron-firmware-tool",
}


def licenses():
    """Licences a publier avec la page (code tiers embarque dans tweaks.js et builder.js) : {fichier servi : texte}."""
    out = {OUT.parent / (f["license"] + ".txt"): (DEV_DIR / f["license"]).read_text(encoding="utf-8")
           for f in FEATURES if f.get("license")}
    out.update({OUT.parent / (name + ".txt"): src.read_text(encoding="utf-8") for name, src in PAGE_LICENSES.items()})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verifie sans ecrire")
    args = ap.parse_args()
    text = render()
    if args.check:
        stale = [p.name for p, t in licenses().items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text or stale:
            sys.exit("!! docs/flasher/tweaks.js (ou une licence) n'est pas a jour : relance tools/gen_flasher_tweaks.py")
        print("docs/flasher/tweaks.js est a jour")
        return
    for p, t in licenses().items():
        p.write_text(t, encoding="utf-8")
    OUT.write_text(text, encoding="utf-8")
    print(f"ecrit : {OUT.relative_to(ROOT)} ({len(text)} o, {len(FEATURES)} fonctionnalites)")


if __name__ == "__main__":
    main()
