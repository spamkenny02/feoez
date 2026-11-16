# Compte rendu V72 — lot 66 : cœurs « moitié rouge, moitié blanc » (alignement sur la grille de tuiles)

Signalé par une vidéo de test (réplique « Toutes celles du village passent leur temps à glousser, "Ooh, Higan !" ♥
Il est trop mignon ! ») : le cœur apparaît rouge, puis sa moitié droite devient blanche quand le texte continue.

## Cause (établie par des tests dans Snes9x, avec la réplique exacte reproduite)
Le moteur de texte compose les glyphes dans des **tuiles de 8 px** et la **couleur est portée par la tuile** (code `09` =
mode rouge, `08` = retour au blanc). Le cœur (glyphe 0x6E, 8 px de large, pixels aux colonnes 1 à 7) est rouge en entier
seulement s'il commence à 0 ou 1 px de la frontière d'une tuile (x mod 8 dans {0, 1}). Sinon la partie qui tombe dans la
tuile suivante est recolorée en blanc par le glyphe suivant (même un espace dessiné après `08`), et un caractère visible
juste avant le cœur dans la même tuile devient rouge (le « ! » rouge d'un de mes essais). x se calcule avec la table de
largeurs de la police : `01` remet x à 0, `0D` (pause) ne le remet pas, le texte démarre sur une frontière de tuile.
Campagne de 90 variantes : le résultat ne dépend que de x mod 8 (r = 0, 1 : cœur entier ; r = 2 : 3 px blancs ; r = 4 :
14 px ; r = 6 : 22 px), pas du nombre d'espaces après le cœur. L'anglais avait deux espaces de chaque côté ; la
traduction n'en gardait qu'un, ce qui change x mod 8 au hasard : 270 des 374 cœurs des chaînes françaises étaient
mal placés (72 %).

## Correction (`tools/heart_align.py`, `tools/build_v72.py`)
L'espace qui précède `<09>` est **recodé en un blanc de largeur adaptée** (même nombre d'octets : aucun texte ne
grandit, aucun pointeur ne bouge) pour amener le cœur à x mod 8 dans {0, 1}, avec l'écart de largeur minimal (en général
−2 à +5 px). Pour les lignes déjà pleines, un espace ordinaire de la ligne est réduit de 1 ou 2 px en compensation
(limite de ligne 216 px ; 6 px de tolérance dans la marge de la boîte pour 3 lignes). Les cœurs consécutifs
(`<6E><6E><6E>`) sont traités ensemble ; les cœurs d'une même ligne sont traités dans l'ordre.
Six codes de police inutilisés par les textes deviennent des blancs de largeur 1, 2, 4, 5, 6 et 7 px
(glyphe vide) : 1 px = 0xb4, 2 px = 0xbf, 4 px = 0xd4, 5 px = 0xca, 6 px = 0xbc, 7 px = 0xd9 ; la largeur 3 est l'espace normal. (Le code 0xf2, essayé d'abord pour 1 px, fait
disparaître la fin du texte : il doit être spécial.)

## Résultat
- 374 cœurs dans des chaînes françaises : 104 déjà bien placés, **269 corrigés** (333 octets d'espaces
  recodés), 1 non traité (voir plus bas). Relecture de la ROM modifiée : tous les cœurs traités sont à
  x mod 8 dans {0, 1}.
- Vérification dans le jeu : réplique de la vidéo reproduite (cœur moitié blanc avant, entier après :
  `verification/coeur_avant_apres_v72.png`) puis échantillon de 26 vraies répliques (lignes plantées dans le dialogue du
  marchand, même géométrie de boîte : texte à x = 24). Sur les 23 lignes mesurables : **cœur entier et rouge 23/23
  après correction, 13/23 avant**. Les 3 autres lignes commencent par un code de début de scène (`0C`) qui change le
  déroulé du dialogue dans mon banc d'essai : non mesurables, avant comme après.

## Limites
- 1 cœur non traité : 0x6a4bbf (ligne qui commence par des codes de contrôle inhabituels et dont la largeur calculée
  dépasse déjà la boîte).
- 127 cœurs de chaînes encore en anglais (copies restées dans la ROM, non traduites) ne sont pas touchés.
- Le cœur est maintenant parfois plus près du « ! » qui le précède (jusqu'à 1 px d'écart au lieu de 3) : c'est le prix
  d'un alignement sur la tuile sans ajouter d'octets.
- Les lignes contenant un nom de personnage variable (`<04>`) ont été laissées de côté (aucun cas dans les chaînes
  françaises).
