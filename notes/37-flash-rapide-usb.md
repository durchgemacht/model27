# 37 · Flash rapide en USB : le protocole d'Elektron Transfer dans le flasher web

Remarque reçue sur Reddit : « pourquoi passer par System > Upgrade (SysEx lent) au lieu de produire un `.syx` qu'on glisse
dans Transfer ? […] le protocole de Transfer est décrypté, https://github.com/dagargo/elektroid ». Vérifié par
l'utilisateur : glisser le `.syx` préparé par la page sur la fenêtre d'Elektron Transfer, Model:Cycles branché en USB,
installe le firmware, **beaucoup plus vite**. Le flasher web parle maintenant ce protocole lui-même.

## 1. Pourquoi l'ancienne méthode est lente

`CONFIG › UPGRADE` attend le `.syx` brut, envoyé sans retour : rien ne dit à l'ordinateur que la machine a traité un
paquet. Le flasher le cadençait donc comme un fil MIDI DIN (31 250 bauds, 3 125 o/s) avec une marge de 1,4 : un
firmware de 1,2 Mo met 9 minutes, l'OS d'origine (890 Ko) 7 minutes, même si l'USB irait bien plus vite.

## 2. Le protocole (Elektroid, `src/connectors/elektron.c`)

Source lue : dépôt `dagargo/elektroid`, commit `7806ecaf` (29/09/2026). Les noms entre parenthèses sont ceux du C.

- **Trame** : `F0 00 20 3C 10 00` (`MSG_HEADER`), la charge utile empaquetée sur 7 bits, `F7`. Empaquetage
  (`elektron_encode_payload`) : par groupe de 7 octets, un octet qui porte leurs bits de poids fort (celui du premier en
  bit 6), puis les 7 octets sans ce bit ; le dernier groupe peut être plus court.
- **Charge utile décodée** : `[0..1]` numéro de séquence (big-endian, +1 à chaque requête, 0 au ping), `[2..3]` 0 dans
  une requête et, dans la réponse, la séquence de la requête, `[4]` la commande (réponse : commande | 0x80), puis le
  corps. Une réponse dont la séquence ne correspond pas est ignorée (`elektron_tx_and_rx_timeout`).
- **Qui est là** (`elektron_handshake`) : ping `01`, réponse `[5]` = identifiant de la machine (27 Model:Cycles,
  25 Model:Samples, `res/elektron/devices.json`), nom à `[7 + [6]]` ; version `02`, chaîne à `[10]`. Délai 1 s pour le
  ping (`ELEKTRON_HANDSHAKE_TIMEOUT_MS`), 5 s ensuite (`BE_SYSEX_TIMEOUT_MS`), 50 ms de pause entre messages
  (`BE_REST_TIME_US`).
- **Mise à jour d'OS** (`elektron_upgrade_os`, commande de la CLI `elektroid-cli upgrade fichier.syx N`) : les octets
  du `.syx` **tel quel**, sans rien enlever.
  - départ `50` + taille (4 octets, **little-endian** : `memcpy` d'un `guint32` sur un PC) + `"sysex\0"` + `01` ;
    réponse `D0`, `[5]` = 0 si accepté, sinon un message à `[6]` ;
  - blocs de `0x800` octets (`OS_TRANSF_BLOCK_BYTES`) : `51` + CRC (big-endian) + longueur (big-endian) + position
    (big-endian) + les octets ; CRC = `crc32(0xffffffff, bloc)` de zlib (`elektron_crc`), soit `zlib.crc32(bloc, 0xffffffff)`
    en Python ; réponse `D1`, `[9]` = 0 continuer, 1 terminé, plus de 1 erreur (lu signé, comme dans le C) ; 50 ms
    de pause après chaque bloc.
  - La machine vérifie chaque bloc ; à la fin elle demande sur son écran de confirmer la mise à jour, l'écrit et redémarre.

## 3. Ce que fait la page

`docs/flasher/flasher.js` : `encode7` / `decode7`, `crc32`, `xferOpen` (une requête à la fois sur une paire entrée +
sortie Web MIDI), `xferIdentify` (ping + version), `upgradeFast` (départ + blocs), à l'octet près comme Elektroid.
Deux écarts, sans effet sur ce qui part sur le câble :
- une réponse au bon numéro mais d'un autre type est ignorée (Elektroid abandonne) : seul un autre programme qui parle
  à la machine en même temps (macOS partage les ports) peut en produire ; le délai attrape toujours une machine muette ;
- 8 s d'attente par réponse au lieu de 5.

`docs/flasher/app.js` :
- **Étape 3, deux méthodes** : *Rapide (USB)* par défaut (machine allumée normalement, aucun menu, Elektron Transfer
  fermé : il occupe le port, et sous Windows il le bloque) et *Classique (CONFIG › UPGRADE)*, inchangée, en secours.
  Le choix est retenu (`localStorage`).
- **La page demande qui répond** dès que le port est choisi : « Model:Cycles trouvé : OS 1.13 ». Elle apparie l'entrée
  MIDI à la sortie par le nom. Elle **refuse** d'envoyer un firmware Model:Cycles (produit `0x11` dans le `.syx`) à une
  machine qui répond 25, Model:Samples : l'OS Samples (le retour passe par le MIDI IN), ou Model-TG avec
  *Device Config › Transfer* sur SMP (sa doc interdit d'y accepter un OS). Avant l'envoi, elle redemande, pour le cas
  où la machine a changé entre-temps.
- **Pendant l'envoi** : progression bloc par bloc, temps restant mesuré, bouton Stop. Estimation affichée avant :
  blocs × (50 ms + 15 ms pour le message et la réponse), soit environ 38 s pour 1,2 Mo (587 blocs) ; mesuré : 33 s (§5).
- **Après** : « confirmez sur l'écran du Model:Cycles » ; quand le port disparaît, « écrit le firmware et redémarre » ;
  quand il revient, la page attend 2,5 s, redemande la version (4 essais, 2 s d'écart) et l'affiche.
- **Étape 4** : bouton *Télécharger le .syx*, à glisser sur Elektron Transfer (le même protocole, la même confirmation).
- Le mode *OS Samples* (OS Model:Samples dans le conteneur Model:Cycles) part aussi en rapide : c'est un fichier
  Model:Cycles, envoyé à une machine qui tourne encore l'OS Cycles (c'est ce que décrivait le message Reddit).

## 4. Vérifié sans matériel

- `python3 tools/webxfer_check.py` : transcription Python ligne à ligne des fonctions C d'Elektroid ; l'empaquetage dans
  les deux sens, le CRC, et **chaque octet** des messages d'une mise à jour (départ + 4 blocs dont un court) sont
  identiques à ceux de la page.
- `tools/webflash_smoke.sh` : un faux Model:Cycles, écrit à part (son propre décodeur, le CRC de zlib), répond au ping,
  à la version, au départ et aux blocs, et garde ce qu'il reçoit. Le firmware de test (2,5 Mo, 1 215 blocs) arrive
  **octet pour octet**, CRC vérifié à chaque bloc ; machine muette (1 s), entrée MIDI absente, port occupé,
  départ refusé (message affiché), bloc refusé (arrêt sur ce bloc), machine qui répond Model:Samples (rien n'est envoyé),
  Stop, redémarrage suivi jusqu'à la nouvelle version ; puis la méthode classique comme avant.
- Rendu vérifié dans Chromium (étapes 3 et 4, envoi, fin).

## 5. Testé sur la machine (04/10/2026)

- La page sur un vrai Model:Cycles, depuis un firmware modifié (régulateur v2 de la [note 36](36-regulateur-sans-coupures-inutiles.md)) :
  machine trouvée, **33 s** pour la barre de progression, puis la machine demande de confirmer avec **YES** ou **NO** ;
  après YES, elle installe le firmware et redémarre, et tout fonctionne. L'estimation affichée avant l'envoi passe à
  65 ms par bloc (50 ms de pause + 15 ms) au lieu de 80.
- Le gestionnaire de Transfer de l'OS répond donc aussi sous nos mods ; Model-TG n'y touche qu'en mode SMP
  (`vendor/Model-TG/docs/INTERNALS.md`).

## 6. Pas encore vérifié

- **Le retour depuis l'OS Samples** reste au MIDI IN. Le message Reddit suggérait un fichier « croisé » glissé dans
  Transfer ; mais un conteneur Model:Samples remplace aussi le menu de démarrage du Model:Cycles (§ avertissements de
  l'onglet OS Samples), donc pas proposé tant que ce n'est pas étudié.

## 7. Rappel

Aucun firmware n'est fourni : la page envoie le fichier construit sur l'ordinateur à partir de l'OS officiel de
l'utilisateur. La récupération d'une machine qui ne démarre plus passe toujours par le menu de démarrage et le MIDI IN
([FLASH.md](../FLASH.md), [06](06-flash-et-recuperation.md)).

## 8. Un second essai automatique (18/11/2026)

Rapport d'un testeur (Model:Samples, 18/11/2026) : avec cette page comme avec tous les autres flashers, qui reprennent
tous ce protocole de Modded-Cycles, le premier envoi reste bloqué à 0 ou 1 %, le second marche toujours. La cause n'est
pas établie (`[HYP]` : la première réponse après la réouverture des ports se perd sous macOS/Chrome, ou la machine met
plus longtemps à répondre au premier départ). La page n'attend jamais plus de 8 s une réponse (`XFER_TIMEOUT_MS`).

Désormais, quand l'envoi s'arrête faute de réponse (`timeout`), la page attend 2 s, rouvre les ports, refait
l'identification et renvoie tout le fichier, **une fois** (`flash()` dans `app.js`, texte `retry_try`). Sans risque :
la machine n'écrit rien avant qu'on confirme sur son écran, un envoi interrompu ne laisse rien. Le smoke test simule un
premier départ sans réponse (`muteStarts` du faux appareil). Pas encore vu sur une machine qui bloque.
