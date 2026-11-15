# Compte rendu V70 — lot 64 : mot « Failed » du combat

V70 = V69 + 1 flux compressé réécrit (`tools/build_v70.py`, table `traduction/failed_combat_lot64_fr.json`), reconstruit
depuis la ROM d'origine (IPS V69 appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Où est le mot
Les chiffres de dégâts et « Failed » sont des sprites 4 bits chargés par le jeu **au moment d'une attaque** (ils
n'existent pas dans la VRAM au début d'un combat : mes premières recherches, faites sur un état pris en plein combat
puis sur un début de combat, tombaient à côté). En journalisant les lectures de ROM d'un combat déclenché dans la
grotte (noyau Snes9x instrumenté) puis en cherchant les tuiles de la VRAM parmi les flux chargés, le flux est à
**0x51e200** (mode 2, 29 tuiles) : tuiles paires 0 à 18 = chiffres 0 à 9, tuiles 20 à 25 = « Failed » (24×10 pixels :
rangées 0 à 7 dans les tuiles 20/22/24, rangées 8 et 9 dans 21/23/25), atterrissant aux objets 0 à 12 et 16 à 28
(base 0xc000). Le flux suivant commence 200 octets plus loin.

## Changement
Failed → **Raté**, dessiné dans le style des chiffres (corps blanc, contour sombre sur les 8 voisins, accent aigu sur
le e). Chiffres inchangés. Flux recompressé : 185 octets pour 200 disponibles.

## Vérification en jeu (plus forte que pour la V69)
Un combat joué avec la ROM V70 (état de début de combat + une attaque) a été analysé après le chargement : **la VRAM
d'objets contient, tuile par tuile, exactement les tuiles décompressées du flux V70** (les 26 tuiles testées), les
chiffres étant identiques à la V69 et les 6 tuiles de « Failed » différentes. C'est donc le décompresseur du jeu
lui-même qui a relu mon flux, et non plus seulement mon décodeur.
`verification/combat_failed_raté_comparaison.png` : « Failed » et « Raté » côte à côte avec des chiffres de référence.
`verification/combat_roue_v69_en_jeu.png` : la roue de commandes V69 dans un combat réel déclenché en marchant dans la
grotte (le jeu a décompressé les étiquettes françaises).

## Limites
Je n'ai pas pu faire **afficher** « Failed » en combat (un parchemin de feu, une attaque normale et un combat complet ne
déclenchent pas l'échec) : le rendu à l'écran n'est vu que sous forme de tuiles. Le placement des 3 sprites à
l'écran (24 px de large, comme « Failed ») n'a pas été observé ; « Raté » (23 px) tient dans la même largeur.
