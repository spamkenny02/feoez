# Compte rendu V60 — lot 54 : écran de sauvegarde

V60 = V59 + 2 bandes redessinées (`tools/build_v60.py`, table
`traduction/ecran_sauvegarde_lot54_fr.json`), reconstruit depuis la ROM d'origine (IPS V59
appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Mécanisme
Le menu de sauvegarde (Sauver et dormir / Dormir / Sauver / Quitter) était déjà en français : le
texte vient du bloc B029, traduit. Les libellés de l'écran « Save File » sont des bandes de tuiles
dans un bloc de 61 tuiles à 0x6d2000 (chargé en VRAM 0x7200). Décodage du bloc mot par mot :
Rank = tuiles 0 à 2, Fresh Start = 3 à 10, Delete All = 11 à 15, Yes/No = 16 à 19, « Is it okay to
delete all the data? » = 20 à 36, Save File = 37 à 41, Restart = 42 à 47, « Delete the broken
file? » = 48 à 61.

## Changements (vérifiés à l'écran)
Save File → Sauver (5 tuiles ; « Sauvegarde » fait 50 px pour 40 disponibles), Rank → Rang
(3 tuiles). Capture : `verification/ecran_sauvegarde_v60.png`.

## Constats hors périmètre
- Sur cet écran, le lieu s'affiche tronqué : « Village de l'Ombre du F… ». Le nom français dépasse
  la zone d'affichage : à raccourcir dans le texte (non traité ici).
- La barre « Total / Cash on Hand » du menu de sauvegarde reste en anglais. Ses tuiles ne
  correspondent à aucune bande de la ROM et le texte est introuvable (ni encodé, ni en indices de
  tuiles, ni en mots de carte de tuiles) : probablement composé par le code. À tracer.

## Non traité (non atteint par la sauvegarde fournie)
Fresh Start, Delete All, Yes/No, « Is it okay to delete all the data? », Restart, « Delete the
broken file? » : plages de tuiles ci-dessus, à traiter avec un état pris sur ces écrans.
