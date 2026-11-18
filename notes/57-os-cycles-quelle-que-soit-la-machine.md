# 53 — L'OS Cycles avec mods, quelle que soit la machine (Model:Cycles ou Model:Samples)

Demande de DaftMaple (10/10/2026, contributeur, possède un Model:Samples) : intégrer au dépôt le flasher d'origine de
**RDS (AIM)** (Discord, 10/10/2026, « Modded Cycles OS on a Model:Samples », `mods_for_samples.py`), et laisser choisir dans l'onglet Mods du flasher la machine
qu'on flashe. C'est la « piste, PR séparée » de [41 §8](41-os-cycles-sur-samples.md).
Outil : `tools/mods_for_samples.py` ; portage JS `MCBuilder.modsForSamples` (`docs/flasher/builder.js`).
Preuve : `tools/emu/test_mods_for_samples.py`. Adresses : VA de l'OS 1.13.

## Décision : toujours l'OS du Model:Cycles

**Le flasher (onglet Mods) installe toujours l'OS du Model:Cycles, avec les mods cochés, quelle que soit la machine.**
Décision de DaftMaple, 10/10/2026 : sur un Model:Samples, le sampling vient de **Model-TG** (machine Sampler,
samples par Elektron Transfer, [31](31-model-tg.md)), pas de l'OS Samples. On n'entretient donc qu'un OS et qu'une liste
de mods ; aucun mod ne se construit sur l'OS Samples.

À retenir pour la suite :
- un nouveau mod se construit, se prouve et se vérifie (`REF_MAINOS`, `REF_MODS`) **une seule fois**, sur l'OS Cycles ; il
  vaut pour les deux machines sans travail de plus ;
- le choix de la machine ne change **que l'emballage** (conteneur, signature, transport SysEx, §2), jamais le MAIN OS à
  part les 32 octets de la clé de vérification ([41 §3](41-os-cycles-sur-samples.md)) ;
- l'onglet *Samples OS* reste pour ce qui n'est pas un OS Cycles avec mods : l'OS Samples sur un Model:Cycles, l'OS Cycles
  sans mod sur un Model:Samples et le retour à l'OS Samples.

## En bref

- Un build avec mods (onglet Mods, `build.py`) est mis tel quel, MAIN OS compris, dans le **conteneur officiel du
  Model:Samples** (bootstrap, updater, horodatage, signature Samples), avec le **correctif de 32 octets** de
  [41 §3](41-os-cycles-sur-samples.md) **toujours appliqué** : l'OS installé vérifie les mises à jour avec la clé du
  Samples. L'option `--no-keyfix` du script d'origine n'est pas reprise.
- Deux emballages, selon l'OS **qui tourne** (c'est lui seul qui vérifie la mise à jour, [41 §1](41-os-cycles-sur-samples.md)) :
  `_smp-os` (Model:Samples sous son OS, transport `0x0F`) et `_cyc-os` (Model:Samples déjà sous un OS Cycles de la page,
  transport `0x11`) : c'est ce second fichier qui permet de **changer de mods plus tard**.
- Le retour à l'OS Samples ne change pas : *Model:Samples : retour à son OS* (onglet Samples OS).
- `[FAIT en émulation]` sur quatre combinaisons de l'échantillon `REF_MAINOS`, dont la plus grosse (§5) ; **testé sur un
  Model:Samples le 11/10/2026** (DaftMaple), les deux choix (§6).

## 1. Ce qui est construit

1. Le build Model:Cycles habituel (`MCBuilder.build` / `build.py`), vérifié comme toujours : chaque mod contre `REF_MODS`,
   le MAIN OS contre `REF_MAINOS` quand la combinaison est dans l'échantillon ([49](49-verification-mod-par-mod.md)).
2. Son MAIN OS décompressé ; les 32 octets en `0x401296b2` remplacés par `C' = cléSamples ^ SHA-256("REVERB SEND") ^
   SHA-256("DNES BREVER")`, après les mêmes contrôles que `crossflash.cycles_key_write` (code en `0x4005275c` et
   `0x400527c0`, chaîne, ancienne constante = clé Cycles). Aucun tweak ne touche ces octets ni la vérification `0x4005a0e4`
   (`check_overlaps.py`, et la preuve le refait sur chaque combinaison) : `C'` est le même pour toutes.
3. Recompression avec `aplib.repack` (seuls les 32 octets deviennent des littéraux), relue.
4. Conteneur officiel du Samples avec cette section 3, signé avec la clé Samples (tirée du `.syx` officiel de
   l'utilisateur, jamais stockée).
5. Emballage SysEx selon l'OS qui tourne (§2), puis relecture complète : paquets, octet appareil, checksum de contenu,
   en-tête et sections 2/4/5 = Samples officiel, MAIN OS = build avec mods hors des 32 octets, HMAC Samples valide et
   HMAC Cycles invalide, clé dérivée par l'OS installé = clé Samples.

Limites vérifiées : MAIN OS sous `0x40200000` (le bootstrap y copie la section 3 compressée), conteneur sous `0x1c0000`
octets (écrit en flash `0x20000`, doit finir avant `0x1e0000`, [41 §8](41-os-cycles-sur-samples.md)).

## 2. Les trois machines du flasher

| Choix (onglet Mods) | Ce qui tourne | Fichier envoyé | La page n'envoie que si la machine répond |
|---|---|---|---|
| *Model:Cycles* | OS Cycles (officiel ou avec mods) | build habituel, signé Cycles | Model:Cycles |
| *Model:Samples, sous son OS* | OS Samples officiel | `_smp-os` : conteneur Samples, produit `0x0F`, appareil `0x0A` | Model:Samples |
| *Model:Samples, déjà sous l'OS Cycles* | OS Cycles de la page (clé Samples) | `_cyc-os` : même conteneur, produit `0x11`, appareil `0x0C` | Model:Cycles |

Le second fichier est la « nouvelle sorte de fichier » prévue en [41 §8](41-os-cycles-sur-samples.md) : un conteneur
signé Samples dans le transport du Cycles. Les deux emballages portent le **même conteneur**.

Ce que la page ne peut pas distinguer (même raisonnement que [41 §6](41-os-cycles-sur-samples.md)) :
- *Model:Cycles* choisi pour un Model:Samples sous l'OS Cycles de la page : il répond Model:Cycles, la page envoie, l'OS
  refuse (HMAC, clé Samples) : rien n'est écrit. La carte dit de choisir *déjà sous l'OS Cycles*.
- *sous son OS* choisi pour un **Model:Cycles sous l'OS Samples** : il répond Model:Samples et accepte (clé Samples) ;
  son bootstrap Cycles démarre alors l'OS Cycles de la page, qui refuse ensuite les firmwares Model:Cycles. D'où
  « seulement pour un vrai Model:Samples » (`mach_w4`), comme `cos_w5`.
- *déjà sous l'OS Cycles* sur un OS Cycles installé **par un autre outil** (clé Cycles, comme akrism) : refusé (HMAC),
  rien n'est écrit. Retour à l'OS Samples par le premier choix de l'onglet Samples OS (`--to cycles`, groupe 7 de
  `test_crossflash_samples.py`), puis *sous son OS* (`mach_w5`).
- Model-TG en identité Transfer SMP : la machine répond Model:Samples alors qu'elle tourne sous l'OS Cycles ; la page
  refuse `_cyc-os` et dit de remettre l'identité sur CYC (`dev_mach_cos_on_samples`).

## 3. Dans le flasher

- Onglet Mods, en tête : *Votre machine* (`mach-cyc`, `mach-smp`, `mach-cos`), retenu par le navigateur
  (`mc-machine`). Pour un Model:Samples, un encadré **Testé** (d'abord **Expérimental**) (ce qui est installé, quel choix pour quel état, la
  sauvegarde, le retour, le redémarrage difficile) et une case de sauvegarde ; l'étape 2 demande aussi l'OS officiel du
  Samples (même zone que l'onglet Samples OS).
- `prepareFirmware` : le build Model:Cycles (mis en cache sous sa clé habituelle), puis `MCBuilder.modsForSamples` ; la
  page vérifie que le MAIN OS emballé, hors des 32 octets, est celui du build (`modsSha`).
- Méthode rapide : `devProblem` compare le produit du fichier à celui qui répond (`dev_mach_smp_on_cycles`,
  `dev_mach_cos_on_samples`) ; méthode classique : le transport suffit (l'OS qui tourne ignore un autre produit).
- Nom du fichier téléchargé : `model-cycles_OS1.13_<mods>_for-samples_smp-os.syx` / `_cyc-os.syx`.
- Étape 3 (11/10/2026, remarque de DaftMaple : avec *déjà sous l'OS Cycles*, la page disait « The Model:Cycles doesn't
  appear over USB ») : les textes de connexion nomment la machine qu'on flashe, `{dev}` (`deviceName`) : Model:Samples
  pour les deux choix Model:Samples de l'onglet Mods et les deux derniers de l'onglet Samples OS, Model:Cycles sinon ;
  et le port d'après l'OS qui tourne, `{port}` (`portName`) : « Model:Samples » seulement sous son propre OS. Les
  consignes fixes de l'étape 3 suivent le choix (`refreshDevTexts`). Accroche de la page : « Model:Cycles or
  Model:Samples ». Vérifié par `tools/webflash_smoke.js` §7b-bis (les cinq choix, en anglais et en français).
- `tools/webflash_smoke.js` §7c : le parcours complet, et les deux fichiers de la page identiques octet pour octet à ceux
  de `tools/mods_for_samples.py` pour Model-TG.

## 4. L'outil en ligne de commande

`tools/mods_for_samples.py` reprend le script de RDS (AIM) : même sortie octet pour octet (vérifié sur la plus grosse
combinaison du guide, MAIN OS `65b186a9…`), commentaires en français, fonctions `for_samples` / `pack` / `verify`
réutilisées par la preuve, sans `--no-keyfix`, et deux contrôles de taille en plus. Sans mods (l'OS Cycles officiel en
`--mods`), `_smp-os` est octet pour octet `crossflash.py --to samples`. Commandes et empreintes : `BUILD.md`.

## 5. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_mods_for_samples.py` (42 contrôles, environ 1 min) reprend les outils de `test_crossflash_samples.py` :
vraie vérification des mises à jour des deux OS (`0x4005a0e4` et son équivalent Samples) et chargeur du bootstrap Samples
(`0x80000820`), sur `model-tg`, `6ch-usbup+model-tg`, `model-tg-st+sample-preview-st+macro-tg` et la plus grosse
combinaison de l'échantillon (`6ch-usbup+model-tg-st+sample-preview-st+trig-hold+arp+tempo-max+boot-anim+multiline-browser+level-pan-values+trigless-dim+midi-both+syntakt-tg-sd-cp-toy-bits-swarm-macro`,
MAIN OS de 2 073 997 octets, fin `0x401fa98d`, conteneur de 1 039 552 octets) :

| Fichier | OS Samples d'origine | OS Cycles d'origine | OS Cycles avec mods installé | OS Cycles de l'onglet Samples OS |
|---|---|---|---|---|
| `_smp-os` | **accepte** | refuse (4) | — | — |
| `_cyc-os` d'une autre combinaison | — | — | **accepte** (changer de mods) | **accepte** (ajouter des mods) |
| OS Samples officiel, transport Cycles (retour) | — | — | **accepte** | accepte ([41](41-os-cycles-sur-samples.md)) |
| OS Cycles officiel | — | accepte | **refuse (4)** | refuse (4) |
| build Model:Cycles normal (mêmes mods) | — | — | **refuse (4)** | — |

Et pour chaque combinaison : MAIN OS installé = build avec mods sauf 32 octets en `0x401296b2`, et les remettre redonne
l'entrée de `REF_MAINOS` ; le bootstrap Samples pose ce MAIN OS en RAM sans vérification, sous `0x40200000` ; transports
`0x0F`/`0x0A` et `0x11`/`0x0C`, même conteneur. Sans mods : octet pour octet `--to samples` ; un fichier déjà emballé pour
le Samples est refusé.

Non émulé, comme en [41 §5](41-os-cycles-sur-samples.md) : la réception USB elle-même, l'écriture en flash et le
démarrage des mods sur le matériel du Samples. Le bootstrap et l'initialisation de la mémoire sont les mêmes que sur le
Model:Cycles, au produit près ([41 §1](41-os-cycles-sur-samples.md), `crossflash.py`), et akrism a rapporté Model-TG et
l'audio USB 6 canaux en marche sur son Model:Samples ([41 §8](41-os-cycles-sur-samples.md)).

## 6. Essais sur la machine

Sur un vrai Model:Samples (DaftMaple en a un), sauvegarde Transfer d'abord :
1. *Model:Samples, sous son OS*, Model-TG et quelques mods, méthode rapide : la machine redémarre en Model:Cycles avec
   les mods (Sampler de Model-TG, samples par Transfer en identité SMP) ;
2. *déjà sous l'OS Cycles*, une autre combinaison : changement de mods par USB ;
3. onglet Samples OS, *retour à son OS* : retour au Model:Samples, samples et projets présents ;
4. en secours : menu de démarrage du Samples et l'OS Samples officiel par le MIDI IN.

**Testé sur la machine (11/10/2026)** par DaftMaple, sur son Model:Samples : les essais 1 (*sous son OS*) et 2 (*déjà sous
l'OS Cycles*, changement de mods) marchent ; l'encadré du flasher passe de **Expérimental** à **Testé**. Les essais 3
et 4 n'ont pas été rapportés. Les cartes de mods gardent leur propre statut, établi sur un Model:Cycles.

## 7. Une seule question dans le flasher (17/11/2026)

Demande du mainteneur : rendre le Model:Samples de nouveau visible dans le flasher, mais plus simple ; ce ne doit pas
être la première chose à décider. Le passage d'un Model:Cycles à l'OS Samples ne l'intéresse pas (« personne ne veut
ça ») : la page ne s'adresse plus qu'aux vrais Model:Samples qui veulent les mods.

- **Page 1** : les cartes, comme avant. Plus d'onglets (Mods / Official firmware / Samples OS), plus de
  `flasher/?samples` (`SAMPLES_UI` supprimé). Il reste deux chemins vers l'écran d'installation : *Install n mods* et la
  ligne *Back to the official firmware* (`st.intent` : `"mods"` | `"restore"`).
- **Écran d'installation, étape 1 « Your machine »** (`#step-machine`, `renderOwn()`) : *Which device do you own?*
  (`own-cyc` / `own-smp`, l'appareil physique) et, pour un Model:Samples, *Already installed mods on it?*
  (`modded-no` / `modded-yes`). Retenu par le navigateur (`mc-own` : `cyc`, `smp`, `smp+mods`). À droite, une phrase qui
  dit ce qui va se passer, et *Good to know* replié. La liste des mods passe à l'étape 4 (*You install*).
- `applyOwn()` traduit les réponses en états que la page connaissait déjà, donc en fichiers déjà construits et
  vérifiés :

| Cartes | Appareil | Mods déjà ? | État | Fichier |
|---|---|---|---|---|
| mods | Model:Cycles | — | `mods`, `machine "cyc"` | build habituel |
| mods | Model:Samples | non | `mods`, `machine "smp"` | `_smp-os` (§2) |
| mods | Model:Samples | oui | `mods`, `machine "cos"` | `_cyc-os` (§2) |
| officiel | Model:Cycles | — | `restore` | l'OS officiel inchangé |
| officiel | Model:Samples | oui | `samples`, `smpDir "back"` | retour `--back-samples` (41), Expérimental |
| officiel | Model:Samples | non | rien à envoyer (`ownStop()`) | étapes 2 à 4 masquées |

- Plus de cases à cocher propres au Model:Samples (`mach-ack`, `cos-ack`, `samples-ack`) : la seule case est celle de
  l'étape 4 (sauvegarde). Les messages de l'étape 3 renvoient à la réponse de l'étape 1 (« answer “Yes” / “No” in
  step 1 »).
- Restent dans le code, hors de la page, et le smoke test les parcourt toujours : l'OS Samples sur un Model:Cycles
  (`smpDir "cyc"`) et l'OS Cycles sans mods sur un Model:Samples (`smpDir "smp"`), les onglets et l'ancien sélecteur.
- **Ce qui n'a pas changé** : les emballages (§1, §2) et la clé de 32 octets ([41](41-os-cycles-sur-samples.md) §3).
  Une piste plus simple a été discutée le même jour, sans rien construire : d'après [41 §1](41-os-cycles-sur-samples.md),
  seule l'OS qui tourne vérifie une mise à jour, avec sa propre clé ; un OS Cycles **sans** les 32 octets, dans le
  conteneur Samples, accepterait alors les builds Model:Cycles ordinaires, et le retour se ferait par le conteneur
  Cycles avec l'OS Samples (`--to cycles`), sans fichier `_cyc-os` ni `--back-samples`. Non retenue pour l'instant :
  jamais essayée sur un vrai Model:Samples, et les machines déjà sous l'OS de la page (clé Samples) n'accepteraient
  plus que les fichiers signés Samples.

**Preuve remise à jour (17/11/2026)** : `tools/emu/test_mods_for_samples.py` construisait encore des combinaisons de
Modded-Cycles (Model-TG, moteurs du Syntakt) que la page n'offre plus. Il prend maintenant celles d'aujourd'hui : SAMPLE
seul, Control All Config + Trig Preview, et toutes les cartes (`tools/compose.py`, la plus grosse de l'échantillon) ;
`--syntakt` devient facultatif. Les trois MAIN OS égalent REF_MAINOS, et tous les groupes passent dans Unicorn (« tout
est ok », lancé par le mainteneur) : aller, démarrage, changement de mods, retour à l'OS Samples, refus des fichiers
signés Cycles.

**Second retour, automatique (17/11/2026, demande du mainteneur).** Un Model:Samples dont l'OS Cycles vérifie avec la
clé du **Cycles** (posé à la main, ou par un outil sans le correctif de 32 octets) refuse le retour habituel
(`--back-samples`, signé Samples) : rien n'est écrit. Les flashers connus qui proposent le Model:Samples (Modded-Cycles,
Supermodel, PPPCCC, lus le 17/11/2026) appliquent tous le correctif ; la Techno Edition ne fait que le Model:Cycles.
Pour les autres, la page envoie alors d'elle-même, une fois, l'OS Samples dans le conteneur du Cycles
(`crossflash.py --to cycles`, `REF_SAMPLES_ON_CYCLES`) : un tel OS l'accepte et le bootstrap du Samples le démarre
(groupe 7 de `test_crossflash_samples.py`). Déclencheurs : un départ refusé ou une erreur de bloc (`refused`, `write`)
en méthode rapide ; la page garde ensuite ce fichier (`st.sbackAlt`, `makeSbackAlt()`, `useSbackAlt()`) jusqu'à une
nouvelle réponse à l'étape 1. **Ce que la machine répond exactement sur l'USB quand la clé ne va pas n'est pas
établi** (on suppose une erreur au dernier bloc, comme le contrôle porte sur tout le fichier) : le smoke test simule ce
cas (`accept` du faux appareil, §7b-ter), pas la machine.

**Retour testé sur un vrai Model:Samples (18/11/2026)** par un testeur connu du mainteneur : Model:Samples avec mods →
« Back to the official firmware », Model:Samples + Yes → il redémarre sous son OS Samples. L'étiquette Expérimental du
retour disparaît (étape 1, guide §22, release 0.74). Le second retour automatique (clé Cycles) n'est pas essayé sur une
machine. Le même testeur signale un premier envoi bloqué à 0–1 % avec tous les flashers (notes/37 §8).
