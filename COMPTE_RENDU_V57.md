# Compte rendu V57 — lot 51 : noms d'objets (bandes graphiques)

V57 = V56 + redessin de 303 bandes de noms d'objets. `tools/build_v57.py` part de la ROM
anglaise d'origine, applique l'IPS V56 (SHA-256 vérifié), puis réécrit chaque bande
avec l'alphabet natif.

## Mécanisme (trouvé avec Snes9x + comparaison VRAM/ROM)
Les noms affichés en boutique, sur l'écran Équip. et dans l'Inventaire ne sont pas du
texte : ce sont des bandes de 8 tuiles 2 bits (64 px), 128 octets par objet, rangées
dans l'ordre des objets à partir de 0x6f6000. Elles étaient donc invisibles pour les
lots de texte (blocs 2/3/9 déjà traduits). Une bande se relit avec l'alphabet natif ;
la dernière forme (lettre, épée, katana, armure, kimono, pierre, cœur, bracelet) est
une icône qui remplace un nom générique et est conservée telle quelle.

## Contenu
- 303 noms (indices 0 à 302 de `traduction/noms_objets_lot51_fr.json`), tous ≤ 64 px
  (icône et espace compris) ; rapport complet dans `verification/build_report_v57.json`.
- 78 noms français du catalogue tiennent tels quels ; les autres sont des formes courtes
  (« Pil. » pilule, « Brev. » breuvage, « Ess. » essence, « Croq. » croquettes,
  « Talis. », « Pend. », « Brac. », « Sand. », « Chauss. », « Mant. », « Vêt. »,
  « Arm. », « Cap. », « Casq. »). Les noms contenant une icône n'écrivent que le mot
  distinctif (ex. « Ours de feu » + icône épée).
- Les bandes 303 à 309 de la zone ne sont pas des noms (graphiques divers) : intactes.

## Vérification
Reconstruction depuis la ROM d'origine, aller-retour IPS, captures Snes9x :
`verification/boutique_v57.png` (liste d'achat) et `verification/equip_v57.png` (Équip.).
Le noyau d'émulation est compilé localement (commit 1bcc369e), non publié.

## À relire / limites
Les formes courtes sont un premier jet éditorial : elles respectent la largeur mais
certaines (ex. « Anneau sort », « Savates nulles », « Cap. mauve ») méritent un avis.
Reste en anglais dans la boutique : nom de la boutique (bandes de 16 tuiles à 0x6d0000),
Buy/Sell/Welcome, Cash on Hand/Total/Owned/Type (bande de 112 tuiles à 0x6f4700), et
« Rank/Health » des panneaux de personnage.
