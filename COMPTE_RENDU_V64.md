# Compte rendu V64 — lot 58 : relecture des noms d'objets raccourcis

V64 = V63 + 9 bandes de noms d'objets révisées (`tools/build_v64.py`, table
`traduction/noms_objets_revision_lot58_fr.json`), reconstruit depuis la ROM d'origine (IPS V63
appliqué, SHA-256 vérifié, aller-retour IPS contrôlé). Chaque bande remplacée est d'abord vérifiée
identique au rendu du lot 51 ; la table du lot 51 reste inchangée.

## Relecture des 303 noms (lot 51)
Les noms ≤ 64 px (icône comprise) sont tous gardés. J'ai remplacé ceux où une abréviation moche ou
une casse incohérente avait une meilleure alternative de même largeur :

| Anglais | Avant | Après | px |
|---|---|---|---|
| Soft Pill | Pilule Souple | Pilule souple | 52 |
| Dozing Powder | Pdre sommeil | Poudre sieste | 60 |
| Peacock Tear | Larme du Paon | Larme de paon | 64 |
| Fool Pill | Pilule du Sot | Pilule du sot | 53 |
| Almighty Knife | Cout. suprême | Couteau divin | 57 |
| Fortune Ring | Anneau sort | Anneau destin | 61 |
| Willful Armor | Arm. obstinée | Armure têtue | 59 |
| Purple Hood | Cap. mauve | Cagoule mauve | 62 |
| Disaster Hood | Cap. désastre | Capuche chaos | 64 |

## Compromis conservés (la largeur interdit mieux)
« Pil. », « Brev. », « Ess. », « Croq. », « Talis. », « Pend. », « Brac. », « Sand. », « Chauss. »,
« Mant. », « Vêt. », « Arm. », « Casq. » (mots courants abrégés de façon régulière) ;
« Drag. rouge » / « Drag. royal » (le mot entier fait 69 et 66 px avec icône) ;
« Miroir Temps » (« Miroir du Temps » : 70 px) ; « Anneau juge », « Anneau envie », « Anneau doute »
(variantes plus fidèles : 66 à 74 px) ; « Escarp. reine » (« princier » : 70 px) ;
« Arm. étain » (perd « rouge ») ; « Pot d'or » (perd « poudre »).
Une alternative serait d'élargir les bandes à 10 tuiles, mais cela demande de modifier les
cartes de tuiles de chaque écran concerné : hors périmètre.

## Vérification
Les 9 bandes sont décodées depuis la ROM construite (texte attendu retrouvé à l'identique) et la
liste d'achat est contrôlée à l'écran : `verification/boutique_v64_controle.png`.
