# Compte rendu V58 — lot 52 : boutiques (noms et interface d'achat)

V58 = V57 + 40 bandes de tuiles redessinées (`tools/build_v58.py`, table
`traduction/interface_boutique_lot52_fr.json`). Construit depuis la ROM d'origine : IPS V57
appliqué (SHA-256 vérifié), puis bandes réécrites avec l'alphabet natif, sans chevauchement.

## Noms de boutiques (31 bandes de 16 tuiles à 0x6d0000, pas 0x100)
Affichés sur 10 tuiles (80 px, lu dans la carte de tuiles), donc toutes ≤ 80 px.
Exemples : Odds and Ends → Bric-à-brac, Item Shop → Magasin d'objets, Weapon Shop →
Boutique d'armes, Great Weapon Shop → Grande armurerie, Bakuzan's Shop → Chez Bakuzan,
Imada's Shop → Chez Imada. « Ring & Ring » (jeu de mots à pictogramme) est laissé intact.

## Interface d'achat (sous-bandes de 0x6f4700, plages de tuiles lues à l'écran)
Buy → Ach, Sell → Vte (2 tuiles = 16 px chacune), Welcome! → Salut !, How can I help
you? → Je peux t'aider ?, Cash on Hand → Argent, Owned → Stock, Items → Objet et
Weapons → Armes (alignés à droite comme l'original), Attack → Attaq.
« Total » et « Type » sont identiques en français : inchangés.

## Vérification
Reconstruction, aller-retour IPS, et captures Snes9x (liste d'achat + fiche d'arme) :
`verification/boutique_v58_liste_et_arme.png`.

## Limites / à relire
- « Ach » et « Vte » sont contraints par les 2 tuiles de la carte de tuiles (« Ach. » ferait 18 px).
- Non encore vérifiés à l'écran (boutiques non atteignables avec la sauvegarde fournie) :
  les autres noms de boutiques et les libellés Defense/Speed/Luck, Accessories, Armor,
  « What will you… », « Will this be okay? », « Sell? ».
- Reste dans la même zone d'interface : bandes de sauvegarde/suppression, « Use it on whom? »,
  « Rank/Health » des panneaux de personnage, nommage de l'animal.
