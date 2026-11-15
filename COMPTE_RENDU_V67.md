# Compte rendu V67 — lot 61 : sous-menus de combat (Arts secrets et Parchemins)

V67 = V66 + 6 bandes redessinées (`tools/build_v67.py`, table `traduction/combat_sous_menus_lot61_fr.json`),
reconstruit depuis la ROM d'origine (IPS V66 appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Ce que montre l'état de combat (`attaque.state`)
- Texte de combat déjà en français : en-têtes de compétence (« Enchaînement de gifles rapides »), liste (« Double
  gifle », « Brûl. »), inventaire (« Katana de bois », « Signet 1 à 4 »), cible (« Boisé #1 »).
- Restaient en anglais :
  1. les libellés des panneaux de gauche des sous-menus : « Secret Skill », « Health », « Used » (Arts secrets) ;
     « Scrolls », « Tech Used » (Parchemins) — **traités ici** ;
  2. les quatre étiquettes de la roue de commandes (« Attack », « Skills », « Items », « Scrolls ») — **non traitées**.

## Mécanisme des panneaux
Deux bandes de tuiles 2 bits chargées en VRAM 0x7200 : 0x6f2500 (51 tuiles, Arts secrets) et 0x6f2a00 (57 tuiles,
Parchemins). Plages lues dans la carte de tuiles (0xb000, n0 = 288) :

| Panneau | Anglais | Français | Tuiles |
|---|---|---|---|
| Arts secrets | Secret / Skill | Secret / Art (« Secret » est identique) | 32-35 / 36-37 |
| Arts secrets | Health | Vie | 38-41 |
| Arts secrets | Used | Coût | 29-31 |
| Parchemins | Scrolls | Parch. | 44-47 |
| Parchemins | Tech / Used | Coût / tech. | 38-40 / 41-43 |

« Technique » (script, identique en français) et les noms des personnages sont inchangés. Les bandes « Fusion » et
« Separate » (0x6f2a00, tuiles 28-36), non observées en jeu, ne sont pas traitées.

## Vérification
`verification/combat_v67_sous_menus.png` : panneau Arts secrets (Secret / Art / Vie / Coût 2 / Vie 12) et panneau
Parchemins (Parch. / Coût tech. 10 / Technique 0), captures Snes9x sur l'état de combat fourni.

## Roue de commandes (non traitée) — ce qui est établi
`verification/combat_roue_commandes_anglais.png`. Chaque étiquette est faite de deux sprites 16×16 (table OAM lue
dans l'état) : Attack = tuiles 13 et 76, Skills = 78 et 174, Items = 192 et 194, Scrolls = 196 et 198, base d'objets
0xc000 (4 bits, 6 couleurs). Ces tuiles, comme les chiffres et le mot « Failed » affichés en combat, **n'existent pas
en clair dans la ROM** (recherche exacte de chaque tuile 4 bits et 2 bits) : elles sont compressées (SPC7110). Les
traduire demande un décompresseur pour retrouver les flux, puis un compresseur compatible et une relocalisation.
