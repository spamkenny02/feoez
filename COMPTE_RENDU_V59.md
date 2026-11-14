# Compte rendu V59 — lot 53 : « Rank » / « Health » des panneaux de personnage

V59 = V58 + 3 bandes redessinées (`tools/build_v59.py`, table
`traduction/panneau_personnage_lot53_fr.json`), reconstruit depuis la ROM d'origine (IPS V58
appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Pourquoi ils restaient en anglais
Ces libellés ne sont pas dans la bande de menu principal déjà traduite (lot 49, 0x6f11a0)
mais dans deux copies propres aux sous-écrans :
- écran Équip. : bloc de 109 tuiles à 0x6f4000, « Rank » = tuiles 29 à 31 ;
- écran Parchemins : bloc de 58 tuiles à 0x6f2000, « Rank » = tuiles 44 à 46, « Health » =
  tuiles 48 à 51.
Plages lues dans la carte de tuiles de chaque écran (Snes9x), après avoir ouvert réellement
chaque sous-écran (mes premières recherches portaient sur le menu principal).

## Changements
Rank → Rang (2 bandes, 3 tuiles), Health → Vie (4 tuiles). « Technique », identique en
français, est laissé inchangé (bande à pictogramme à 0x6f2340).

## Vérification
`verification/panneau_personnage_v59_equip_parch.png` : Équip. (Rang 4) et Parchemins
(Rang 4, Vie 28/28, Technique 21/21).

## Reste dans la même famille
Bandes de sauvegarde/suppression, « Use it on whom? », nommage de l'animal, et libellés de
boutique non encore atteints (voir COMPTE_RENDU_V58.md).
