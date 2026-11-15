# Compte rendu V66 — lot 60 : barre « Total / Cash on Hand » du menu de sauvegarde

V66 = V65 + 1 bande redessinée (`tools/build_v66.py`, table `traduction/barre_sauvegarde_lot60_fr.json`),
reconstruit depuis la ROM d'origine (IPS V65 appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Source trouvée
« Cash on Hand » existe en quatre copies identiques dans la ROM d'origine : 0x6d3240 (bloc de vente, lot 57),
0x6f1130 (menu principal, lot 49), 0x6f4c30 (bloc d'achat, lot 52) et **0x6f0a30**, restée anglaise. La barre du
menu de sauvegarde est dessinée avec cette dernière : dans l'état fourni, les 12 premières tuiles de VRAM 0x7d00
sont octet pour octet celles de la ROM d'origine à 0x6f0a00, et la carte de tuiles de l'écran (carte à 0xb800,
rangée 20) place « Total » sur les tuiles 0 à 2, « Cash on Hand » sur 3 à 9 et « ryo » sur 10-11, deux fois.
Les recherches précédentes échouaient parce que je comparais la VRAM à la ROM déjà traduite.

## Changement
Cash on Hand → Argent (7 tuiles, 30 px sur 56). « Total » est identique en français, « ryo » inchangé.

## Vérification
`verification/barre_sauvegarde_v66.png` : barre « Total 0ryo Argent 0ryo ». La capture est obtenue en rechargeant
dans l'état de sauvegarde les tuiles de la bande depuis la ROM V66 (comme le fait le chargement du jeu) : la
sauvegarde fournie contient déjà les anciennes tuiles en VRAM. Le texte des options (« Save and Stay ») reste
anglais sur cette image pour la même raison ; en jeu il est déjà en français (bloc B029).
