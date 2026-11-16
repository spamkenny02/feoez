# Compte rendu V71 — lot 65 : « Almanach » centré dans la barre de sélection

Signalé par une capture d'écran de test : dans le menu principal, « Almanach » commençait avant la barre bleue de
sélection (et non centré dedans), contrairement aux autres libellés.

## Cause
La bande « Almanach » (0x6f0f90, 6 tuiles) est posée une tuile à gauche des autres libellés de la 2e colonne. Le texte
français (38 px) est plus court que l'anglais (41 px) mais restait calé à x = 0 de la bande : il débordait de 4 px à
gauche de la barre de sélection (44 px de large, barre commençant à x = 60).

## Correction
Texte décalé de 7 px vers la droite dans sa bande (7 + 38 + 1 = 46 ≤ 48 px). Mesure à l'écran (barre visible) pour
des décalages de 4 à 8 px : marge gauche / droite = 0/6, 1/5, 2/4, **3/3**, 4/2 ; 7 px donne exactement 3 px de chaque côté.
`tools/build_v71.py` vérifie que la bande de départ est bien celle du lot 49 avant de la remplacer.

## Vérification
`verification/menu_almanach_recentre_v71.png` : avant (V70, à gauche) et après (V71, à droite), curseur sur Almanach.
