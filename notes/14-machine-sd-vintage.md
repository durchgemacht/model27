# 14 · Machine SD VINTAGE : un moteur de caisse claire en plus sur le Model:Cycles

Demande : ajouter au Model:Cycles une reproduction, la plus fidèle possible, d'un moteur de caisse claire du Syntakt.
« SD CRACK » n'existe pas au catalogue du Syntakt ; la machine retenue avec toi est **SD VINTAGE**, une machine numérique.
Intégration **par étapes** :
1. remplacer le moteur d'une machine existante, pour valider le son sur le matériel ;
2. puis en faire une vraie 7ᵉ machine.

## 0. En bref

| | État |
|---|---|
| Architecture des machines du M:C (descripteurs, voix, tables, briques DSP) | `[FAIT]` décodée sur l'OS 1.13 (§2) |
| Moteur SD VINTAGE (C, clean-room) | `[FAIT]` écrit, compilé pour le ColdFire, 828 + 560 octets (§3) |
| **v2** : moteur recalé sur le vrai SD VINTAGE du Syntakt, potards au sens du Syntakt | `[FAIT]` en émulation ([16 §6](16-moteur-syntakt.md)), à réécouter sur la machine |
| **Étape 1** : tweak `sdvintage-snare` (SD VINTAGE à la place de SNARE) | `[FAIT]` build CLI, validé dans le vrai moteur émulé (§6), puis **sur le matériel le 29/09/2026** (« elle marche parfait »). Retiré du flasher web pour l'instant, à la demande de l'utilisateur : reste disponible avec `build.py`. |
| Banc d'émulation du moteur audio (Unicorn + EMAC exacte) | `[FAIT]` `tools/emu/` (§4) |
| Place libre : les grosses « caves » 0xFF sont des masques de sprites | `[FAIT]` partage de masques ; `6ch-usbup` corrigé (§5) |
| **Étape 2** : 7ᵉ machine (SNARE conservé) | `[À FAIRE]` plan et adresses en §8, après validation matérielle de l'étape 1 |

## 1. Ce qu'est — et n'est pas — cette « reproduction »

- **Sources.** Le manuel du Syntakt, Elektronauts (fil « Syntakt Science Lab #25: SD Vintage »), les sites de revendeurs et de presse sont **bloqués** par le proxy de cet environnement.
  Les seules informations obtenues viennent d'extraits de moteurs de recherche :
  - les machines numériques du Syntakt sont « à base de FM, dérivées de celles du Model:Cycles », avec plus de contrôle ;
  - SD VINTAGE en fait partie.
- **Pas de référence audio** (tu n'en avais pas), et pas de firmware Syntakt : rien n'a été décompilé côté Syntakt.
- **Donc** SD VINTAGE est ici une **interprétation clean-room** : une caisse claire de boîte à rythmes « vintage », construite dans les conventions du M:C.
  - Topologie classique des caisses claires analogiques : corps accordé + bruit « snappy ».
  - Même accord, même enveloppe DECAY/GATE et même PUNCH que les machines d'origine.

  Ce n'est **pas** l'algorithme du Syntakt, que personne ici n'a pu entendre ni lire.
- **Pour s'en rapprocher** : quelques enregistrements du SD VINTAGE d'un Syntakt (réglages notés) suffiraient à caler les constantes.
  Même accord, balayage, balance corps/bruit, filtre, durées. Tout l'outillage de mesure est prêt (§4, §6).

## 2. Architecture des machines du M:C (OS 1.13)

### 2.1 Descripteurs de paramètres `[FAIT]`

- Table à `0x4010dce0`, entrées de `0x38` octets, référencée par une trentaine de sites (UI, MIDI, sons).
- Champs (mots 32 bits) :

  | Offset | Champ | Offset | Champ |
  |---|---|---|---|
  | +0x00 | machine (0..5 ; 7 = toutes ; 0x11 LFO ; 0x12 trig…) | +0x1c | NRPN / autre |
  | +0x04 | slot (index du paramètre) | +0x20 | index |
  | +0x08 | minimum (8.8) | +0x24 | drapeaux |
  | +0x0c | maximum (8.8) | +0x28 | clé de tri |
  | +0x10 | **défaut** (8.8) | +0x2c | nom long |
  | +0x14 | drapeau | +0x30 | groupe (« Drum », « Amp »…) |
  | +0x18 | CC (poids fort) | +0x34 | nom court |
- Les 6 machines partagent PITCH, DECAY, PUNCH, GATE et FINE. COLOR, SHAPE, SWEEP et CONTOUR ont **une entrée par machine**, chacune avec ses propres défauts.
  - Exemples : « Kick Color » `0x4010e718`…, « Snare Color » `0x4010e834`…
  - Les noms courts (COLR, SHPE, SWEP, CONT) sont communs.

| Slot | Paramètre | Plage | CC (table) | Remarque |
|---|---|---|---|---|
| 0x09 | MACHINE (« Algorithm », ALG) | 0..5 | 70 | max au champ `0x4010e5e4` |
| 0x0a | PITCH | 40..88 (défaut 64) | 65 | 1 demi-ton par pas |
| 0x0b | COLOR | 0..127 | 16 | défaut propre à chaque machine |
| 0x0c | SHAPE | 0..127 | 17 | idem |
| 0x0d | SWEEP | 0..127 | 18 | idem |
| 0x0e | CONTOUR | 0..127 | 19 | idem |
| 0x0f | PUNCH | 0..1 | 66 | |
| 0x10 | GATE | 0..1 | 67 | |
| 0x11 | FINE | 0..127 (défaut 64) | — | ±2 demi-tons |
| 0x12 | DECAY | 0..127 | 80 | défaut propre à chaque machine |

- Défauts SNARE d'origine : COLOR 0, SHAPE 127, SWEEP 8, CONTOUR 0, DECAY 40.
  - Champs « défaut » : `0x4010e818`, `0x4010e850`, `0x4010e888`, `0x4010e8c0` et `0x4010e8f8`.

### 2.2 Paramètres d'une piste `[FAIT]`

- Pendant le rendu, les paramètres (modulés par le LFO) d'une piste sont des **mots 8.8** à `p + 2·slot`.
- Machine en `p+0x12` (octet fort), PITCH `+0x14`, COLOR `+0x16`, SHAPE `+0x18`, SWEEP `+0x1a`, CONTOUR `+0x1c`, PUNCH `+0x1e`, GATE `+0x20`, FINE `+0x22`, DECAY `+0x24` (octet fort).
- Une structure par piste, pas de `0x42` octets.

### 2.3 La boucle des voix et le dispatch des machines `[FAIT]`

- `0x400a7d4a(out = 0x80001858, params, trig_mask, release_mask)`, appelée par bloc de 32 trames (1500 blocs/s).
- `MACSR = 0xa0` (EMAC fractionnaire signé, saturé) pendant la boucle, `0x20` après.
- Pour chacune des 6 voix :
  1. Si le bloc précédent a déclenché une note, l'index de machine est lu et borné à 0..5 (`moveq #5` en `0x400a7dba` et `0x400a7dc0`), puis passe par la table d'octets `0x40118640` (`00 01 02 03 04 05 00 00`).
  2. Si la machine change, la voix est remise à zéro (`0x400a7ab8`).
  3. `update[m](pmod, voix, params)` : table **`0x40118628`**. Puis `render[m](out_piste, voix)` : table **`0x40118610`**. Garde : `moveq #5` en `0x400a7df4`.
  4. La sortie de la piste est divisée par 2.

| Machine | `update` (réglages → moteur) | `render` (DSP) |
|---|---|---|
| 0 KICK | `0x400aa08c` | `0x400aa3c4` |
| 1 SNARE | `0x400ab3b0` | `0x400ab6e8` |
| 2 METAL | `0x400aa49c` | `0x400aa712` |
| 3 PERC | `0x400aa998` | `0x400aacc2` |
| 4 TONE | `0x400aa7b8` | `0x400aa930` |
| 5 CHORD | `0x400aae88` | `0x400ab24c` |

- **Déclenchement.** `trig_mask` met `voix+0x34`, recopié en `voix+0x38` à la fin du bloc. Les `update` initialisent leurs enveloppes quand `voix+0x38 ≠ 0`.
  - Le VCA (`0x400a9430`) coupe le bloc où `+0x34` est posé : 0,67 ms de silence avant l'attaque, sans clic.
- **Hauteur.** `pmod = 0x80001830[piste]` = note du trig en demi-tons << 16, écrite par le séquenceur.
  - Toutes les machines calculent : note = PITCH − 64 + note du trig + FINE, bornée à 0..127, puis 440 Hz à 69.
  - Mesuré : KICK au défaut = C2 (65,4 Hz).

### 2.4 La voix `[FAIT]`

- `0x31c` octets par voix, à `0x42308828 + piste·0x31c` ; privée au moteur (seules la boucle et l'init l'adressent).
  - `+0` machine courante, `+4` précédente, `+0x34` / `+0x38` / `+0x3c` drapeaux trig / bloc de trig / fin de note.
  - `+0x40` / `+0x44` : mise à l'échelle de la hauteur.
  - 4 opérateurs FM à `+i·0x78`, champs `+0x6c..+0xc4` : phase, incréments, enveloppe, pointeurs d'entrée et de sortie.
  - Enveloppe d'ampli : `+0x230..+0x250` (niveau, attaque `+0x248`, décroissance `+0x250`, gate `+0x24c`).
  - PUNCH : `+0x274..+0x2a4`, `+0x48`.
  - 2ᵉ enveloppe : `+0x2a8..+0x2c0`.
  - Filtres : `+0x2dc`, `+0x2f0`.
  - `+0x318` pointe vers un petit tampon SRAM.
- **Init** (`0x4005974c`) : remise à zéro des 6 voix et `+0x318 = 0x8000bd98 + 0x30·piste`.
- Au boot (`0x4000045c`), l'image recopie `0x4019b590..0x401aa140` en SRAM `0x80000000` / `0x80008000`. C'est là que sont les tables d'onde : **sinus 256+1 points Q31 à `0x8000eee4`**.

### 2.5 Briques DSP partagées (le « moteur FM ») `[FAIT]`

| Adresse | Rôle |
|---|---|
| `0x400a9120` | enveloppes des 4 opérateurs (par bloc) |
| `0x400a8204` / `0x400a8adc` / `0x400a835e` / `0x400a8722` / `0x400a8fc2` | opérateurs (sinus table + FM, rétroaction…) : 32 échantillons |
| `0x400a9884` | mélange de 2 opérateurs avec gains interpolés |
| `0x400a9d4e`, `0x400a9cf6` | filtres |
| `0x400a9302` + `0x400a9504` | 2ᵉ enveloppe + VCA |
| `0x400a9252` | **enveloppe d'ampli** (DECAY, GATE) |
| `0x400a9430` | **VCA** (interpolé) |
| `0x400a967a` | **PUNCH** (gain x4 saturé + enveloppe type compresseur) |
| `0x400a7e6c` | fin commune des `update` : hauteur → incréments des 4 opérateurs |

- **La forme d'onde de chaque opérateur** (opérateur j à `voix + 120 j`) est lue par son pointeur `+168` ; les cinq
  opérateurs ci-dessus le lisent tous. La remise à zéro `0x400a7ab8` (au boot et à chaque changement de machine) le
  met sur le **sinus `0x8000eee4`** pour les quatre. Seuls KICK (op2 `0x8000eae0`), METAL (op1 et op3 `0x8000f2e8`),
  PERC (op0 `0x4012024c`, en DDR) et CHORD (ses frames) en posent un autre : SNARE et TONE ne jouent que le sinus.
  `[FAIT]`, lecture du code 2026-11-12, détail et adresses dans notes/66 §37.1.

- Le **SNARE d'origine** chaîne ces briques ainsi : op1 module op2 et op3 ; op0 (rétroaction, bruit) module op3.
  - op2 passe par un filtre puis la 2ᵉ enveloppe ; op3 par un filtre puis l'enveloppe d'ampli.
  - Mélange, puis PUNCH.
  - Chaque machine est bien un *mapping* différent du même moteur, comme le dit Elektron.

## 3. Le moteur SD VINTAGE

Source : [`tools/machines/sdvintage/sdvintage.c`](../tools/machines/sdvintage/sdvintage.c). C autonome, virgule fixe Q31 sur l'EMAC, aucun appel à la libc.

```
 note ─► f0 ─┬─► sinus f0 ──────────────┐
  SWEEP ─► ×(1+D·env_s)                 ├─► × env_corps (CONTOUR) ─┐
             └─► sinus 1,62·f0 × env ───┘                          ├─► enveloppe d'ampli d'origine (DECAY, GATE)
 bruit blanc ─► passe-haut 480 Hz ─► 2 passe-bas 1 pôle (SHAPE) ─► × COLOR ┘      ─► VCA ─► PUNCH d'origine
```

| Potard | Rôle dans SD VINTAGE | Plage (mesurée en émulation, §6) |
|---|---|---|
| **PITCH** | accord du corps, comme les autres machines (note du trig, FINE, LFO) | PITCH 64, note 60 → **196 Hz** (G3) ; 1 demi-ton par pas |
| **DECAY** | longueur globale = queue du bruit, par l'enveloppe d'ampli **d'origine** | même courbe que les 6 machines (LUT `0x4012228c`) |
| **COLOR** | « snappy » : dose de bruit (corps légèrement réduit) | centroïde 230 Hz (0) → 6,5 kHz (127) |
| **SHAPE** | « tone » : brillance du bruit, passe-bas 1,2 → 14 kHz | centroïde 2,6 / 6,2 / 10,5 kHz à 0 / 64 / 127 |
| **SWEEP** | profondeur du balayage de hauteur du corps (jusqu'à +1,7 octave), durée 4 → 45 ms | |
| **CONTOUR** | durée du corps, 12 → 650 ms (T60) : du « tac » sec au fût qui sonne | |
| PUNCH, GATE | chaîne d'ampli d'origine | identiques à SNARE |

- **Défauts** (réécrits dans les descripteurs SNARE à l'étape 1) : COLOR 60, SHAPE 64, SWEEP 40, CONTOUR 40, DECAY 40.
- **État** dans la voix : `+0x70..+0xab`, zone des opérateurs, inutilisée par ce moteur. Elle évite les champs que `0x400a7d16` remet à zéro au déclenchement.
  - Tous les accès mémoire sont bornés quel que soit l'état : paramètres bornés à 0..0x7f00, index de LUT bornés, table sinus indexée sur 8 bits (+1).
- **Coût CPU** (boucle des voix comprise, voix seule) : **5 549 instructions par bloc**, contre **8 790** pour le SNARE d'origine. 6 pistes en SD VINTAGE coûtent donc moins que 6 SNARE.
- **Compilation** : `m68k-linux-gnu-gcc -mcpu=54418` (le CPU du M:C), `-Os` pour `update` (1 fois par bloc) et `-O2` pour `render`.
  - `.data` et `.bss` sont interdits.
  - Lien à adresse fixe dans deux zones libérées (§5).
  - `tools/gen_sdvintage.py` compile et écrit le tweak ; `--check` vérifie le JSON versionné (testé avec GCC 13.3).

## 4. Banc d'émulation du moteur (`tools/emu/`)

- `mcengine.py` charge **ton** MAIN OS (patché ou non) dans Unicorn et rejoue :
  - l'init du boot (copie ROM → SRAM, init des voix) ;
  - la **vraie boucle des 6 voix**, bloc par bloc, avec les paramètres et la note de ton choix.

  Pas d'UI, de séquenceur, de mixeur ni d'effets : seulement le moteur de synthèse.
- **Piège trouvé** : l'EMAC d'Unicorn (QEMU) est **fausse en fractionnaire signé**, justement le mode du moteur.
  - Symptôme : −1,0 × −0,9947 y donne +0,50. Les enveloppes s'effondrent de moitié à chaque bloc et tous les sons meurent en 5 ms.
  - Correctif : `emac.py` intercepte chaque instruction EMAC (décodée par `m68k-linux-gnu-objdump`) et l'exécute en Python. Produit signé exact, précision de l'accumulateur, saturation, MAC avec chargement parallèle.
  - Avec ce correctif, les 6 machines d'origine sonnent de façon cohérente : hauteurs, décroissances, niveaux.
- Dépendances : `pip install unicorn numpy`, paquet `binutils-m68k-linux-gnu`.

## 5. Place libre : les caves 0xFF étaient des masques de sprites

- Le contrôle des caves de `build.py` a refusé les deux blocs de 1 Ko d'abord choisis. En remontant les références :
  - Les quatre grands blocs `0xFF` de l'image (720 à 1040 o) sont les **masques** de sprites. Constructeur `Bitmap` `0x40070172` : image en `+0x10`, masque en `+0x14`, deux plans de même taille.
  - Les images, elles, contiennent du vrai dessin : damiers de test d'écran, un cadre, une bande de glyphes.
  - Les masques sont entièrement à `0xFF` (opaques), donc **identiques**.
- **Conséquence pour `6ch-usbup`** (déjà publiée, jamais flashée) : ses stubs étaient dans le masque du sprite 32×260 (`0x40154ae4`).
  - Le code n'était pas réécrit (sprite en lecture seule), mais ce sprite aurait eu des trous à l'écran.
  - Et son build exigeait `--force-cave`.
- **Solution, sans aucun effet visible** : on garde intact le masque le plus grand (`0x40154ae4`) et on y fait pointer les trois autres sprites. On réécrit pour cela la constante passée au constructeur (`tools/sprites.py`). Les octets lus sont les mêmes, et les trois plans deviennent réellement libres.

| Masque libéré | Taille | Sprite | Constante réécrite | Utilisé par |
|---|---|---|---|---|
| `0x4015c044` | 720 o | 64×90 (cadre) | `0x400b6434` | `6ch-usbup` (stubs, 154 o) ; `trig-hold` (le début, 166 o, [note 33](33-effacer-un-trig.md)) |
| `0x4016cae8` | 1024 o | 64×128 (damier) | `0x400b1106` | `sdvintage-snare` (`update`, 828 o) |
| `0x4018a788` | 1024 o | 64×128 (damier inverse) | `0x400ad1aa` | `sdvintage-snare` (`render`, 560 o) |

- **Règle des caves** (`build.py` et `builder.js`, même verdict, testés) :
  - La zone contrôlée va du début du bloc `0xFF` à la **fin des octets écrits**. Un objet qui commence après n'est pas touché, même si son 1er octet vaut `0xFF` : c'est le cas du plan image qui suit chaque masque.
  - Une référence dont les octets sont **réécrits par les tweaks choisis** n'existe plus dans l'image patchée : elle est listée comme « neutralisée » et ne bloque pas.
  - Sauf si la nouvelle constante pointe encore dans la zone (réécriture sans effet) : elle reste bloquante.
  - Les trois cas sont testés (`tools/webbuild_check.sh`).
- Les petites zones `0xFF` (≤ 396 o, `0x40144bc8..0x401489fa`) n'ont pas été touchées : les tweaks de drumkilla y écrivent.

## 6. Validation (émulation, OS 1.13 réel)

`python3 tools/emu/test_sdvintage.py -i model-cycles_OS1.13.syx` applique le tweak au MAIN OS, puis fait jouer la voix SNARE, c'est-à-dire SD VINTAGE, dans la boucle d'origine :

```
[1] sortie finie et bornée ; crête SD VINTAGE / SNARE d'origine = 0.84
    instructions par bloc (voix seule) : 5549 contre 8790 pour SNARE
[2] PITCH 64, note 60 : 196.3 Hz ; PITCH +12 : x1.996 ; note +12 : x1.996
[3] centroïde COLOR 0 -> 127 : 228 -> 6498 Hz ; SHAPE 0/64/127 : 2625 / 6156 / 10476 Hz
[4] corps (< 500 Hz) entre 60 et 150 ms : CONTOUR 0 -> 127 multiplié ; SWEEP 0 -> 127 : 151 -> 604 Hz au début
[5] queue 150-300 ms, DECAY 10/40/90 : croissante
[6] 500 blocs modulés (hors plage exprès), 14 retrigs, PUNCH : aucun accès hors zone, crête 6.3e8
TOUT OK
```

- **Chaîne de build** : le `.syx` produit (CLI et navigateur) redonne, une fois dépaqueté, le MAIN OS patché attendu.
  - `sdvintage-snare` seul : `80b7b2bd003f2695…`.
  - Avec `6ch-usbup` : `38754937b06e3815…`.
  - `6ch-usbup` seule : `db3d26cc3a48d115…`.
- **`6ch-usbup` déplacée** : les 4 stubs émulés à `0x4015c116..` donnent registres et mémoire identiques à l'origine (`emu_stubs`, modèle ANY).
- **Non vérifiable ici** : le son réel sur la machine, l'UI (libellés, écran), la charge CPU réelle avec séquenceur et effets. D'où le test matériel ci-dessous.

## 7. Étape 1 : build et test sur le matériel `[FAIT]`

> **29/09/2026** : flashée sur un vrai Model:Cycles. Test d'écoute à COLOR 0 (plus de bruit, seulement la note du corps),
> puis « elle marche parfait » selon l'utilisateur. Les points 3 et 4 ci-dessous (charge longue durée) n'ont pas été rapportés en détail.

**Build** :
- CLI : `python3 tools/build.py -i model-cycles_OS1.13.syx -t sdvintage-snare`.
  - On peut combiner : `-t 6ch-usbup,sdvintage-snare`.
- Navigateur (flasher web) : cocher la fonctionnalité « Machine SD VINTAGE » (combinable avec la sortie 6 canaux).

**Test** (interface MIDI et OS officiel à portée, comme toujours) :
1. Démarrage normal ; écrans et sprites habituels intacts (le partage de masques ne doit rien changer à l'affichage).
2. Une piste en machine **SNARE** : un trig doit donner SD VINTAGE. Tourner chaque potard et comparer au tableau §3.
3. PUNCH, GATE, LFO vers COLOR/SHAPE/SWEEP/CONTOUR/PITCH, trigs rapides, p-lock de machine (SNARE ↔ KICK par pas).
4. **Charge** : les 6 pistes en SNARE, pattern dense, effets à fond. Écouter les craquements, longue durée (≥ 30 min).
5. Retour : reflasher l'OS officiel par le MIDI IN (ou `CONFIG > UPGRADE` par USB, hors variante `6ch-multiout`).

## 8. Étape 2 : en faire une 7ᵉ machine (plan) `[FAIT → note 18]`

> Fait avec le vrai moteur du Syntakt : voir [18-septieme-machine.md](18-septieme-machine.md) (inventaire complet, descripteurs propres, preuve en émulation). Le plan ci-dessous est la première version.

**Moteur** (simple, adresses vérifiées) :
- Bornes : `moveq #5` → `#6` en `0x400a7dba`, `0x400a7dc0` et `0x400a7df4`. Octet `0x40118646` = `06`.
- Tables `render` / `update` à 7 entrées : elles ne tiennent pas en place, car elles sont contiguës.
  - Les recopier dans la fin libre d'un masque libéré (il reste 196 et 464 o).
  - Réécrire les constantes `0x400a7d6c` (update) et `0x400a7e16` (render).
- Plage du paramètre MACHINE : max `0x500` → `0x600`, champ `0x4010e5e4`.

**UI** (le vrai travail) :
- Écran de choix de machine (`DrumSelect`, `0x400a25e0`) :
  - borne `moveq #5` ;
  - table de 6 noms `0x401177e4` à recopier avec un 7ᵉ nom ;
  - icône à faire pointer sur celle de SNARE.
  - Aujourd'hui, une valeur > 5 affiche « Error », sans planter.
- Descripteurs de potards : COLOR, SHAPE, SWEEP et CONTOUR ont une entrée par machine (0..5). Le plus sûr : faire lire à la recherche de descripteurs l'entrée de la machine 1 (SNARE) quand la machine vaut 6. SD VINTAGE partage alors libellés, plages et CC de SNARE. Reste à trouver la fonction de recherche parmi les ~30 sites qui lisent `0x4010dce0`.
- À vérifier ensuite : navigateur de sons (catégories), chargement des défauts au changement de machine, Transfer/Overbridge.

**Compatibilité** : un son enregistré avec la machine 6, relu sur l'OS officiel, sera borné à 5 par la boucle des voix : il jouera en CHORD.

**Pourquoi après l'étape 1** : chaque point d'UI se valide à l'œil sur la machine, et l'étape 1 aura déjà prouvé moteur, place mémoire et chaîne de build.

## 9. Fichiers

| Fichier | Rôle |
|---|---|
| `tools/machines/sdvintage/sdvintage.c`, `link.ld` | moteur SD VINTAGE (source) et placement |
| `tools/gen_sdvintage.py` | compile, écrit `tweaks/model-cycles_OS1.13/20-sdvintage-snare.json` (`--check`) |
| `tools/sprites.py` | masques de sprites partageables (§5) |
| `tools/emu/mcengine.py`, `emac.py`, `test_sdvintage.py` | banc d'émulation du moteur et validation |
| `tools/relocate_6ch.py` | `6ch-usbup` désormais dans le masque `0x4015c044` |
