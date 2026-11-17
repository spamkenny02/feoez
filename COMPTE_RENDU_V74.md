# V74 — derniers textes restants

Base : V73 (cumulatif, à appliquer sur la ROM anglaise d'origine SHA-256 eb07eed4…356e). Construit avec `tools/build_v74.py` (via `tools/feoez_kit.py`).

- ROM V74 SHA-256 : f5ed7f30e8deaf2ef3746ae2eae53f2f32f4e98b490eea3f2ee24b2b93d6283c
- IPS V74 SHA-256 : d8cdb07e558b7115be6c77284929bc935d04503f628d3124e21b45c0c2cc3073
- 65 chaînes modifiées, aucune autre ; aucun octet modifié hors de la zone de textes (hors checksum).

## Visibles en jeu
Faiblesses (Physique, Feu, Eau, Vent, Foudre, Aucune faiblesse, « faiblesse / faiblesse extrême »), « Possédé : », « Équipement »,
« Tous », cri « Ouaaaaargh ! Haaaaaaah ! », messages B032/B033.

## Débogage / tests (non atteignables en jeu normal)
Salle de test (B034), débogage de fenêtres/festival (B036), erreurs (B030/B037/B132), questions du menu de débogage (B183), test d'événement (B252).

## Laissé tel quel volontairement (~810 chaînes « identiques à l'anglais »)
Noms propres (Higan, Subaru, Ninigi, monstres japonais…), onomatopées, identifiants (E007, F001…), « Local 1 », sauts de ligne seuls,
menus de débogage en colonnes (B034-S007/S009/S014, B036-S001, B252-S099/S100) dont l'alignement dépend des espaces,
et « Atramentous Alabaster » (nom du boss final, jeu de mots à décider).

## Non vérifié à l'écran
Largeurs des lignes de faiblesses (variables <04>–<07> de largeur inconnue : l'anglais d'origine avait déjà la même structure).
