# Compte rendu V65 — lot 59 : noms de lieux encore coupés (vérification à l'écran)

V65 = V64 + 8 noms de lieux révisés sur place (`tools/build_v65.py`, table
`traduction/noms_lieux_revision_lot59_fr.json`), reconstruit depuis la ROM d'origine (IPS V64 appliqué,
SHA-256 vérifié, aller-retour IPS contrôlé).

## Méthode de vérification (nouvelle)
L'octet 0x244 de la mémoire de sauvegarde (SRAM, offset de l'emplacement 1) est l'index du lieu affiché au
choix de fichier (valeur d'origine 2 = Village Ombre-Feu). En le faisant varier de 0 à 95 sur l'état du menu
titre (SRAM greffée), j'ai capturé à l'écran les 87 noms du jeu :
`verification/lieux_v64_valeurs_0_47.png` et `verification/lieux_v64_valeurs_48_95.png`.

## Constats
- Les 21 noms raccourcis au lot 55 s'affichent en entier (Village Ombre-Feu, Village Pointe-Feu, Sanct. de la
  Flamme, Château Croc-Glace, Labo d'Akamaru, Takamagahara, Int. château Dragon…).
- La fenêtre coupe à 96 px réels. La police du moteur de texte est plus large que l'alphabet des bandes de
  tuiles : mes largeurs prévues (96 px) sous-estimaient certains noms. 8 noms touchaient la limite : 3 déjà
  raccourcis au lot 55 et 5 jamais touchés.

## Corrections (remplacement sur place, complété par des espaces ; 16 occurrences)
| Anglais | Avant | Après |
|---|---|---|
| Luck Luck Village | Village Double-Chance | Village Chanceux |
| Crane and Turtle Crossing | Passage Grue-Tortue | Pont Grue-Tortue |
| Head Mt. Village | Village du Mont-Tête | Village Mont-Tête |
| Cryptic Arbor Castle | Château Arbre-Énigme | Ch. Arbre-Énigme |
| Dragon Mouth Village | Village Gueule-Dragon | Bourg Gueule-Dragon |
| Dragon Ears Village | Village Oreilles-Dragon | Bourg Oreille-Dragon |
| Royal Dragon Town | Ville royale du Dragon | Ville Dragon royal |
| Crab-Crab Cavern | Caverne Crabe-Crabe | Grotte Crabe-Crabe |

## Vérification
Les 8 noms sont recapturés à l'écran : tous s'affichent en entier (largeur visible 72 à 94 px).
`verification/lieux_v65_cas_limites.png` : Bourg Gueule-Dragon, Bourg Oreille-Dragon, Grotte Crabe-Crabe.
Un premier essai « Bourg Oreilles-Dragon » perdait son « n » final (95 px visibles) : d'où le singulier.

## Limites
Les noms entre 90 et 95 px visibles sont proches de la coupure : à surveiller si un nom est encore modifié.
Seul l'emplacement 1 du choix de fichier a été testé ; les mêmes noms servent ailleurs (autres fenêtres,
Almanach) sans avoir été revus.
