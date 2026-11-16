# Compte rendu V73 — lot 67 : étiquettes « Defend » et « Flee » du combat

Signalé par une capture de test : la roue de commandes d'un personnage montrait encore « Defend » (haut) et « Flee »
(bas) à la place de « Attack » et « Scrolls ». J'avais traité 4 étiquettes sur 6.

## Où elles sont
Même format que le lot 63 : une étiquette = deux flux SPC7110 de mode 2 (128 octets décompressés = un sprite 16×16),
dans des emplacements de 0x80 octets. En décompressant toute la zone 0x505b00-0x506400 :
| Étiquette | Flux gauche / droit | Traitement |
|---|---|---|
| Attack, Scrolls, Skills, Items | 0x505d00, 0x505f00, 0x506000, 0x506100 (+0x80) | V69 |
| **Defend** | 0x505e00 / 0x505e80 | **Garde** (cette version) |
| **Flee** | 0x506200 / 0x506280 | **Fuite** (cette version) |
| « Plan A » à « Plan D » | 0x506300, 0x506400, 0x506500, 0x506600 (+0x80) | identiques en français, inchangés |

## Changements (`tools/build_v73.py`, `traduction/etiquettes_combat_suite_lot67_fr.json`)
Defend → **Garde**, Flee → **Fuite** (cohérents avec « Garder » de l'écran Stratégie et « Fuite » courant). Lettres a, r,
e, t déjà extraites au lot 63 ; d (de « Defend »), F (de « Flee ») et i (de « Skills ») extraits ; **G et u dessinés** dans
le même style. Flux de 52 à 61 octets pour 128 disponibles ; relecture avec le décodeur, aller-retour IPS contrôlé.

## Vérification
`verification/combat_roue_garde_fuite_v73.png` : les flux de la ROM V73 sont décompressés (décodeur C transcrit de
Snes9x, validé en combat réel sur les flux V69/V70) et chargés dans les emplacements d'objets du haut (13/76) et du
bas (196/198) de la roue, étiquette sélectionnée et non sélectionnée.
**Limite** : je n'ai pas pu faire afficher la variante « Defend / Flee » dans un vrai combat (les trois personnages du
combat de test ont « Attaq. / Arts / Objet / Parch. » ; la condition qui donne « Defend / Flee » — peut-être un
personnage sans arme — n'a pas été reproduite). Les emplacements d'objets de cette variante sont donc supposés
identiques à ceux de la roue standard, d'après la position des étiquettes sur la capture fournie.
