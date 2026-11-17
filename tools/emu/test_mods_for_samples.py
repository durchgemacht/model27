#!/usr/bin/env python3
"""Preuve de l'OS Cycles AVEC MODS pour Model:Samples (notes/57, tools/mods_for_samples.py, MCBuilder.modsForSamples).

Le firmware est toujours l'OS Cycles (avec mods), quelle que soit la machine ; sur un Model:Samples, il voyage dans le
conteneur officiel du Samples, signé Samples, avec le correctif de 32 octets de notes/41 §3. Ce test reprend les outils
de test_crossflash_samples.py (vrai code de vérification des deux OS, chargeur du bootstrap Samples, dans Unicorn) et
les fait tourner sur des builds avec mods de l'échantillon REF_MAINOS de la page (dont la plus grosse combinaison) :

  1. Aller (Model:Samples sous son OS) : l'OS Samples accepte le fichier _smp-os ; un vrai Model:Cycles le refuse.
  2. MAIN OS installé : le build avec mods sauf les 32 octets de la clé ; les remettre redonne l'entrée de REF_MAINOS.
  3. Démarrage : le bootstrap Samples pose ce MAIN OS en RAM, sans vérification, et la section 3 compressée qu'il lit en
     0x40200000 est au-delà de sa fin.
  4. L'OS installé (avec mods) : accepte le retour à l'OS Samples officiel (--back-samples) et le fichier _cyc-os d'une
     autre combinaison (changer de mods) ; refuse l'OS Cycles officiel et un build Model:Cycles normal (signés Cycles).
  5. Transport : _smp-os en 0x0F / 0x0A, _cyc-os en 0x11 / 0x0C, même conteneur ; tailles sous les limites.
  6. Depuis l'OS Cycles de l'onglet Samples OS (crossflash.py --to samples) : il accepte le fichier _cyc-os.
  7. Sans mods, mods_for_samples redonne octet pour octet crossflash.py --to samples (REF_CYCLES_ON_SAMPLES) ;
     il refuse un fichier déjà emballé pour le Samples.

    python3 tools/emu/test_mods_for_samples.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx

The combinations are the page's of today (17/11/2026, notes/57 §7): SAMPLE alone, two mods without a machine, and every
card at once, the largest of the page's sample; --syntakt is only for an older list that still names the Syntakt
engines.

Environ 1 min (huit vérifications HMAC émulées et un démarrage par combinaison).
"""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import crossflash as X                                               # noqa: E402
import mods_for_samples as M                                         # noqa: E402
import test_crossflash_samples as T                                  # noqa: E402
from mtlib.syx import unwrap                                         # noqa: E402

REPO = HERE.parent.parent
# combinations of the page's REF_MAINOS sample (its keys, in card order), as the flasher offers them on 17/11/2026:
# SAMPLE alone, two mods without a machine, and every card at once (its largest); the first two are tweaks of the
# folder (tools/build.py), the last is composed (tools/compose.py: machines, parts and the mods with them)
FULL = ("control-all-config+trig-preview+sampler+solid+chips+maxsaw+chordtables+digidelay+pots+smpfilter+crush+ring+"
        "reso+eq+cpu+resample+transpose+perform+trig-cond-order")
COMBOS = ["sampler", "control-all-config+trig-preview", FULL]
PARTS = ("cpu", "resample", "transpose", "perform")
check = T.check


def ref_mainos():
    text = (REPO / "docs/flasher/app.js").read_text()
    block = text[text.index("const REF_MAINOS = {"):]
    block = block[:block.index("\n};")]
    return dict(re.findall(r'"([^"]+)": "([0-9a-f]{64})"', block))


def build(cycles, syntakt, key, ref, out):
    """The Model:Cycles build of a page key: tools/build.py for the folder's tweaks, tools/compose.py for every card (the
    machines and parts composed, the other mods with them); either way its MAIN OS is checked against REF_MAINOS
    later (the 32 bytes put back)."""
    ids = key.split("+")
    if key != FULL:
        cmd = [sys.executable, str(REPO / "tools/build.py"), "-i", cycles, "-t", ",".join(ids),
               "--expect-mainos", ref, "-o", str(out)] + (["--syntakt", syntakt] if syntakt else [])
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        return out.read_bytes()
    feats = {f["id"]: f for f in __import__("gen_flasher_tweaks").FEATURES}
    machines = [feats[i]["package"] for i in ids if feats[i].get("package")]
    parts = [i for i in ids if i in PARTS]
    mods = [i for i in ids if not feats[i].get("package") and i not in parts]
    folder = out.parent / "compose"
    subprocess.run([sys.executable, str(REPO / "tools/compose.py"), "--cycles", cycles, "--machines", ",".join(machines),
                    "--with", ",".join(mods), "--out", str(folder)] + [f"--{p}" for p in parts],
                   check=True, stdout=subprocess.DEVNULL)
    return next(folder.glob("*.syx")).read_bytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--samples", required=True)
    ap.add_argument("--syntakt", help="only for a list that still names the Syntakt engines")
    args = ap.parse_args()

    cyc, smp = X.load(args.cycles, "cycles"), X.load(args.samples, "samples")
    cyc_raw, smp_raw = cyc[0]["raw"], smp[0]["raw"]
    cyc_main, smp_main, smp_boot = cyc[3][3], smp[3][3], smp[3][2]
    s_fn, s_power = T.find_verify(smp_main)
    c_fn, c_power = T.VERIFY["cycles"]
    back = X.samples_back(cyc, smp)
    b_back, b_cyc = T.blob_of(back)[0], T.blob_of(cyc_raw)[0]
    page_main = T.main3_of(X.cycles_for_samples(cyc, smp)[0])        # l'OS Cycles de l'onglet Samples OS
    refs = ref_mainos()

    files = {}
    with tempfile.TemporaryDirectory() as tmp:
        for key in COMBOS:
            files[key] = build(args.cycles, args.syntakt, key, refs[key], pathlib.Path(tmp) / "mods.syx")
    other = {k: COMBOS[(i + 1) % len(COMBOS)] for i, k in enumerate(COMBOS)}
    wrapped = {}
    for key in COMBOS:
        blob, main, mods_main, off = M.for_samples(cyc, smp, files[key])
        wrapped[key] = {into: M.pack(blob, into, cyc, smp) for into in ("samples", "cycles")}
        for into, raw in wrapped[key].items():
            M.verify(raw, into, cyc, smp, main, mods_main, off)
        wrapped[key]["main"], wrapped[key]["mods"], wrapped[key]["off"] = main, mods_main, off

    for n, key in enumerate(COMBOS, 1):
        w = wrapped[key]
        main, mods_main, off = w["main"], w["mods"], w["off"]
        b_smp_os, b_cyc_os = T.blob_of(w["samples"])[0], T.blob_of(w["cycles"])[0]
        print(f"{n}. {key}  (MAIN OS {len(main)} o, fin 0x{X.MAIN_BASE + len(main):08x})")
        check(T.verify(smp_main, s_fn, s_power, b_smp_os) == 1, "aller : l'OS Samples accepte le fichier _smp-os")
        check(T.verify(cyc_main, c_fn, c_power, b_smp_os) == 4, "un vrai Model:Cycles le refuse (HMAC)")
        restored = bytearray(main)
        restored[off:off + 32] = mods_main[off:off + 32]
        diff = [i for i in range(len(main)) if main[i] != mods_main[i]]
        check(diff and min(diff) >= off and max(diff) < off + 32 and off == X.CYC_KEY_CONST_VA - X.MAIN_BASE
              and hashlib.sha256(restored).hexdigest() == refs[key],
              f"MAIN OS = build avec mods sauf {len(diff)} octets en 0x{X.CYC_KEY_CONST_VA:08x} ; remis : REF_MAINOS")
        entry, ram, seen = T.boot(smp_boot, b_smp_os)
        check(entry == 0x40000400 and ram[:len(main)] == main and not seen and X.MAIN_BASE + len(main) <= 0x40200000,
              "démarrage : le bootstrap Samples pose ce MAIN OS, sans vérification, sous 0x40200000")
        check(T.verify(main, c_fn, c_power, b_back) == 1, "l'OS installé accepte le retour à l'OS Samples officiel")
        b_next = T.blob_of(wrapped[other[key]]["cycles"])[0]
        check(T.verify(main, c_fn, c_power, b_next) == 1, f"il accepte le _cyc-os de « {other[key]} » (changer de mods)")
        check(T.verify(main, c_fn, c_power, b_cyc) == 4, "il refuse l'OS Cycles officiel (signé Cycles)")
        check(T.verify(main, c_fn, c_power, T.blob_of(files[key])[0]) == 4, "il refuse un build Model:Cycles normal")
        hs, hc = w["samples"][:9], w["cycles"][:9]
        check(hs[4] == 0x0F and hs[8] == 0x0A and hc[4] == 0x11 and hc[8] == 0x0C and b_smp_os == b_cyc_os
              and unwrap(w["cycles"])[1]["product"] == 0x11,
              f"transport : 0x0F/0x0A et 0x11/0x0C, même conteneur ({len(b_smp_os)} o < {M.CONTAINER_MAX} o)")
        check(T.verify(page_main, c_fn, c_power, b_cyc_os) == 1,
              "l'OS Cycles de l'onglet Samples OS accepte le _cyc-os (ajouter des mods)")

    print(f"{len(COMBOS) + 1}. Sans mods, et garde-fous")
    blob, main, mods_main, off = M.for_samples(cyc, smp, cyc_raw)
    raw = M.pack(blob, "samples", cyc, smp)
    check(hashlib.sha256(raw).hexdigest() == hashlib.sha256(X.cycles_for_samples(cyc, smp)[0]).hexdigest(),
          "l'OS Cycles officiel en entrée : octet pour octet crossflash.py --to samples")
    try:
        M.for_samples(cyc, smp, wrapped[COMBOS[0]]["cycles"])
        check(False, "un fichier déjà emballé pour le Samples est refusé")
    except SystemExit as e:                     # refusé dès les sections (horodatage du Samples), sinon par le HMAC
        check(str(e).startswith("!! fichier de mods"), "un fichier déjà emballé pour le Samples est refusé (" + str(e)[3:70] + "…)")

    for key in COMBOS:
        print(f"{key}\n   _smp-os {hashlib.sha256(wrapped[key]['samples']).hexdigest()}"
              f"\n   _cyc-os {hashlib.sha256(wrapped[key]['cycles']).hexdigest()}")
    if T.FAIL:
        print(f"\n{len(T.FAIL)} ECHEC(S)")
        sys.exit(1)
    print("\ntout est ok")


if __name__ == "__main__":
    main()
