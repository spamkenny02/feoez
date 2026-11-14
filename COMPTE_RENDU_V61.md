# Compte rendu V61 — lot 55 : noms de lieux trop larges

V61 = V60 + 21 noms de lieux raccourcis (`tools/build_v61.py`, table
`traduction/noms_lieux_lot55_fr.json`), reconstruit depuis la ROM d'origine (IPS V60 appliqué,
SHA-256 vérifié, aller-retour IPS contrôlé).

## Problème
La fenêtre de lieu de l'écran de sauvegarde coupe le texte vers 96-98 px : « Village de l'Ombre du
F… ». Les noms de lieux français des blocs B014 et B015 (87 noms distincts, copies relogées vers
0x6c4000-0x6c5fff) étaient souvent plus larges que l'anglais : 21 dépassaient 96 px.

## Correction
Chaque nom large est remplacé sur place par une forme plus courte (≤ 96 px, largeur mesurée avec
l'alphabet natif), complétée par des espaces jusqu'à la longueur d'origine. Le terminateur et la
longueur du bloc ne changent pas : aucun index de phrase ni pointeur n'est touché. Toutes les
occurrences exactes (délimitées par des 0x00) sont remplacées : 43 au total (deux copies de chaque
nom, B014 et B015, plus une troisième occurrence de « Takamagahara »).

| Avant | Après |
|---|---|
| Village de l’Ombre du Feu | Village Ombre-Feu |
| Village de la Pointe du Feu | Village Pointe-Feu |
| Sanctuaire de la Flamme | Sanct. de la Flamme |
| Sanctuaire de l’Ours de Feu | Sanct. Ours de Feu |
| Village du Mont de Glace | Village Mont-Glace |
| Château du Croc de Glace | Château Croc-Glace |
| Source de la Tentation | Source Tentation |
| Village du Temple de la Pluie | Village Temple-Pluie |
| Sanctuaire de la Tortue | Sanct. de la Tortue |
| Château de l’Arbre mystérieux | Château Arbre-Énigme |
| Village des Paillettes d’Or | Village Poudre d’Or |
| Labo Or et Argent d’Akamaru | Labo d’Akamaru |
| Village de la Gueule du Dragon | Village Gueule-Dragon |
| Village des Yeux du Dragon | Village Yeux-Dragon |
| Village des Oreilles du Dragon | Village Oreilles-Dragon |
| Château royal du Dragon | Château Dragon royal |
| Takamagahara, les Cieux | Takamagahara |
| Grand sanctuaire des Cieux | Grand sanct. Cieux |
| Village de la Conception | Village Conception |
| Caverne de la Tension | Caverne Tension |
| Intérieur du château du Dragon | Int. château Dragon |

## Vérification
Reconstruction, aller-retour IPS, capture Snes9x de l'écran Save File :
`verification/lieu_sauvegarde_v61.png` (« Village Ombre-Feu » en entier).

## Limites
- Seul « Village Ombre-Feu » est vérifié à l'écran (la sauvegarde fournie est dans ce village).
  Les autres noms respectent la même largeur mesurée mais ne sont pas vus dans le jeu.
- Raccourcis éditoriaux à relire : « Château Arbre-Énigme » et « Village Oreilles-Dragon »
  mesurent exactement 96 px (limite) ; « Takamagahara » seul abandonne « les Cieux » ;
  « Labo d'Akamaru » abandonne « Or et Argent ».
- La limite exacte de la fenêtre (96 ou 98 px) n'a pas été isolée : elle est déduite de la coupure
  observée sur « Village de l'Ombre du F ».
