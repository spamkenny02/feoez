# Compte rendu V68 — lot 62 : nommage de l'animal

V68 = V67 + 2 bandes redessinées (`tools/build_v68.py`, table `traduction/nommage_animal_lot62_fr.json`),
reconstruit depuis la ROM d'origine (IPS V67 appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Où est l'écran
Aucun état n'était disponible : l'écran a été localisé par la ROM. Le bloc à 0x6d4200 contient, décodé mot par mot :
titre « Give your new pet a name! » (tuiles 64 à 76, 104 px), « End » (tuiles 94-95), puis les majuscules A à Z (une
lettre par tuile, tuiles 96 à 121), un symbole (122), les minuscules a à z (128 à 153) et des pictogrammes (192 et
suivantes). Le décodage a donné la bonne plage de tuiles pour tous les libellés vérifiés en jeu jusqu'ici.

## Changements
| Anglais | Français | Tuiles |
|---|---|---|
| Give your new pet a name! | Nomme ton animal ! | 64 à 77 (texte ≤ 104 px) |
| End | Fin | 94-95 |

La 14e tuile du titre n'efface que l'ombre d'un pixel du « ! » d'origine. Les lettres A à Z et a à z sont identiques
en français et sont laissées telles quelles. « Nomme ton nouvel animal ! » (112 px) aurait gardé « nouvel » mais dépasse
les 104 px du texte d'origine.

## Vérification et limites
Vérifié : rendu des deux bandes avant/après dans `verification/nommage_animal_v68_avant_apres.png`.
**Non vérifié en jeu** : l'écran n'a pas pu être atteint (pas d'état fourni). Le nombre de tuiles dessinées par le jeu
pour le titre n'est pas lu sur une carte de tuiles, il est déduit du décodage ; un titre plus court que prévu serait
tronqué. À contrôler dès qu'un état de cet écran existe. Les pictogrammes (tuiles 192+) n'ont pas été examinés.
