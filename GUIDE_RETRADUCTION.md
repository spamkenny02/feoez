# Reprendre la traduction depuis la ROM anglaise — `tools/feoez_kit.py`

Dépôt cloné + Python 3 + Pillow (`pip install pillow`). ROM : la ROM anglaise d'origine (SHA-256 `eb07eed4…356e`).
La ROM n'est jamais modifiée : tout sort en IPS (relu et vérifié à la construction).

## 1. Textes (dialogues, objets, techniques, bestiaire, lieux…)
```
python3 tools/feoez_kit.py texts ROM.sfc --out retraduction            # colonne fr vide (repartir de zéro)
python3 tools/feoez_kit.py texts ROM.sfc --fr-ips Tengai_Makyou_Zero_FR_V73.ips --out retraduction   # fr pré-rempli
```
- `textes.tsv` : 9 041 chaînes, id `Bbloc-Schaîne` (même numérotation que le jeu), catégorie, offset, `en`, `fr`, largeur `px`, statut.
- Vues par catégorie : `objets.tsv` (noms+descriptions), `techniques.tsv`, `bestiaire.tsv` (bloc 20, noms des monstres),
  `lieux.tsv`, `personnages.tsv`, `menus.tsv`, `combat.tsv`, `boutique.tsv`, `commandes.tsv`, `calendrier.tsv`.
  Ce sont des *vues* : `--texts` accepte plusieurs fichiers, la dernière ligne portant un id l'emporte.
- Cellule `fr` vide = anglais conservé ; `<VIDE>` = chaîne volontairement vide ; `\n` = saut de ligne ;
  `<04>` nom du joueur ; `<05>`–`<07>` variables ; `<0D>` pause ; `<09> <6E>` cœur rouge (codes à recopier tels quels).
- Éditer dans LibreOffice/Excel (UTF-8, séparateur tabulation), puis :
```
python3 tools/feoez_kit.py check ROM.sfc --texts retraduction/textes.tsv     # caractères et lignes > 216 px
```
(`<04>` = 96 px, `<05>`–`<07>` = 32 px : estimations, des alertes sur ces lignes peuvent être sans objet.)

## 2. Graphismes contenant du texte anglais
```
python3 tools/feoez_kit.py graphics ROM.sfc --fr-ips Tengai_Makyou_Zero_FR_V73.ips --out retraduction
```
- `graphiques.tsv` : 454 bandes 2 bpp (noms d'objets ×303, noms de boutiques, menus, sauvegarde, titre, stratégie, nommage de l'animal…)
  + 6 étiquettes de combat (roue de commandes, flux SPC7110). Colonnes : offset, tuiles, alignement, limite en px, `en`, `fr`, `fr_ref`.
- `retraduction/png/*.png` : planches de toutes les bandes (version anglaise) pour repérer ce qui reste.
- Le texte est redessiné avec l'alphabet natif 8 px (corps/ombre), icône finale conservée pour les objets ; dépassement = erreur explicite.
- Étiquettes de combat : seules les lettres déjà dessinées dans `traduction/etiquettes_combat*_fr.json` sont disponibles
  (p, q, etc. manquantes : ajouter le glyphe 16 px dans le catalogue, l'outil le signale).

## 3. Construire l'IPS
```
python3 tools/feoez_kit.py build ROM.sfc --texts retraduction/textes.tsv --graphics retraduction/graphiques.tsv \
        --base Tengai_Makyou_Zero_FR_V73.ips --ips-out MonPatch.ips --rom-out MaRom.sfc
```
- `--base` conserve tout le reste de V73 (cœurs, calendrier, Almanach centré, correctifs moteur…) ; seuls les textes du TSV sont
  réinjectés (répertoire + relocalisation automatique dans la zone libre 0x6B0000–0x6D0000, checksum recalculé) et seules
  les bandes dont `fr` ≠ `fr_ref` sont redessinées.
- Sans `--base` : ROM anglaise + police française + vos TSV (les correctifs moteur/affichage de V73 ne sont alors pas repris ;
  3 bandes diffèrent de V73 : Almanach centré, queues « Virtue »).
- Test fait : texte V73 → TSV → build avec `--base` = V73 à l'identique (0 octet différent hors checksum).

## 4. Chercher/éditer d'autres tuiles (enseignes « Inn », décors…)
```
python3 tools/feoez_kit.py sheet ROM.sfc 0x6D0000 0x6E0000 --png planche.png            # planche 2 bpp pour repérer du texte
python3 tools/feoez_kit.py tiles ROM.sfc 0x6F6000 --tiles 64 --bpp 2 --png t.png      # export ; retouche en 4 teintes
python3 tools/feoez_kit.py tiles-import ROM.sfc t.png 0x6F6000 --ips-out retouche.ips    # réimport
python3 tools/feoez_kit.py spc ROM.sfc 0x505D00 --bytes 128 --png s.png                 # flux SPC7110 (4 bpp) décompressé
python3 tools/feoez_kit.py spc-import ROM.sfc s.png 0x505D00 --bytes 128 --slot 128 --ips-out s.ips
```
Les enseignes de maisons sont probablement dans des flux SPC7110 de décor : il faut d'abord repérer le décor en jeu (savestate
devant l'enseigne) pour retrouver le flux, puis `spc` → retouche → `spc-import` (refusé si le flux recompressé dépasse l'emplacement).

## 5. Interface graphique (le plus simple)
```
python3 tools/feoez_gui.py
```
S'ouvre dans le navigateur (rien à installer, serveur local 127.0.0.1). Charger la **ROM anglaise** (obligatoire) puis,
si on veut, la **ROM ou l'IPS français** (pré-remplit les traductions existantes et sert de base pour garder les correctifs).
- **Textes** : filtre par catégorie (bestiaire, objets, techniques, lieux…), recherche, « à traduire », « trop larges » ;
  éditeur anglais/français, largeur en px par ligne, aperçu avec la vraie police du jeu.
- **Graphismes** : bandes de menus/boutiques/noms d'objets et étiquettes de combat, aperçu du rendu en direct (erreur si trop large).
- **Tuiles** : navigateur de tuiles 2/4 bpp ou flux SPC7110 pour repérer du texte dessiné (enseignes…), clic = copie l'offset.
- **Construire** : télécharge l'IPS et la ROM. Les modifications sont sauvegardées en continu dans `projet_feoez/modifs.json`.
