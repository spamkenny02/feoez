# Compte rendu V63 — lot 57 : suite des libellés de boutique

V63 = V62 + 18 bandes redessinées (`tools/build_v63.py`, table `traduction/boutique_suite_lot57_fr.json`),
reconstruit depuis la ROM d'origine (IPS V62 appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Découverte : deux blocs de libellés de boutique
- Bloc d'achat : 112 tuiles à 0x6f4700 (traité en partie au lot 52).
- Bloc de vente : 112 tuiles à 0x6d3000, chargé sur l'écran « Sell » (Buy/Sell, What will you sell?,
  Bookmark, Cash on Hand, Type + Items/Weapons/Accessories/Armor, Will this be okay?, Owned).
Les deux blocs partagent les mêmes positions de tuiles pour la partie basse (Type à Owned).

## Contenu
| Anglais | Français | Bloc / vérification |
|---|---|---|
| Defense | Défense | boutique (achat) |
| Speed | Vitesse | boutique (achat) |
| Luck | Chan. | boutique (achat) - déduit du décodage |
| Accessories | Accessoire | boutique (achat) |
| Armor | Armure | boutique (achat) |
| Will this be okay? | Ça te va ? | boutique (achat) - déduit du décodage |
| Buy | Ach | boutique (vente) |
| Sell | Vte | boutique (vente) |
| Welcome! | Salut ! | boutique (vente) |
| What will you sell? | Que vends-tu ? | boutique (vente) |
| Bookmark | Signet | boutique (vente) |
| Cash on Hand | Argent | boutique (vente) |
| Items | Objet | boutique (vente) |
| Weapons | Armes | boutique (vente) |
| Accessories | Accessoire | boutique (vente) |
| Armor | Armure | boutique (vente) |
| Will this be okay? | Ça te va ? | boutique (vente) - déduit du décodage |
| Owned | Stock | boutique (vente) |

## Vérification (Snes9x, sauvegarde en boutique)
Captures : `verification/boutique_v63_armure_accessoire_arme_vente.png` — « Type Armure / Défense 28 »
(Vêt. chanvre), « Type Accessoire / Vitesse 2 » (Sand. de paille), « Type Armes / Attaq. 42 »
(Lance de bois), et l'écran de vente (Ach/Vte, « Que vends-tu ? », Signet 1 à 4, Argent, Armes).

## Limites
- Non vus à l'écran : « Luck » → Chan. (aucun objet de la boutique n'affiche Chance) et
  « Will this be okay? » → « Ça te va ? » (je n'ai pas atteint l'écran de confirmation d'achat).
- « Accessories » devient « Accessoire » (singulier, 48 px pile) faute de place pour le pluriel (53 px).
- Restent en anglais dans les deux blocs : « What will you » (7 tuiles, bloc d'achat) et « Sell? »
  (3 tuiles environ), dont l'usage n'a pas été observé.
