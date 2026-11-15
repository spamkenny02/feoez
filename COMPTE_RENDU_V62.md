# Compte rendu V62 — lot 56 : suppression et redémarrage de partie

V62 = V61 + 7 bandes redessinées (`tools/build_v62.py`, table
`traduction/suppression_redemarrage_lot56_fr.json`), reconstruit depuis la ROM d'origine (IPS V61
appliqué, SHA-256 vérifié, aller-retour IPS contrôlé).

## Comment atteindre ces écrans
Avec une sauvegarde, le menu titre affiche le choix de fichier : en haut « Fresh Start » et « Delete
All », puis les trois emplacements. Pour les voir sans rejouer le démarrage, j'ai greffé la mémoire
de sauvegarde (SRAM) de la partie fournie dans l'état « title_menu » du scénario de reproduction.
« Delete All » ouvre la confirmation « Is it okay to delete all the data? » avec Yes / No.

## Changements (bloc de 61 tuiles à 0x6d2000, plages de tuiles lues sur la carte de tuiles)
| Anglais | Français | Tuiles | Vu à l'écran |
|---|---|---|---|
| Fresh Start | Nouveau jeu | 3 à 10 | oui |
| Delete All | Effacer | 11 à 15 | oui |
| Yes / No | Oui / Non | 16-17 / 18-19 | oui |
| Is it okay to delete all the data? | Effacer toutes les données ? | 20 à 36 | oui |
| Restart + | Rejouer + (icône « + » conservée) | 42 à 47 | non |
| Delete the broken file? | Effacer fichier abîmé ? | 48 à 60 | non |

Captures : `verification/suppression_v62_titre.png` (choix de fichier, confirmation, sélection de
« Nouveau jeu »).

## Limites
- « Restart + » et « Delete the broken file? » n'ont pas pu être affichés : je n'ai pas réussi à
  provoquer l'écran de fichier endommagé (octets modifiés sans effet) ni à identifier la condition
  d'apparition de « Restart + ». Leurs plages se déduisent du même décodage qui s'est révélé exact
  pour les cinq autres libellés, et la table d'affichage de la ROM le confirme (suite de tuiles 48 à
  60 pour le message, 42 à 47 pour Restart). À contrôler dès qu'un état les montre.
- « Nouvelle partie » (65 px) dépasse la place (64 px) : « Nouveau jeu » retenu.
- « Effacer » seul remplace « Delete All » (« Tout effacer » fait 57 px pour 40) ; la question qui
  suit précise « toutes les données ».
- La ligne « Sauver » et « Rang » de ce bloc a été traitée au lot 54.
