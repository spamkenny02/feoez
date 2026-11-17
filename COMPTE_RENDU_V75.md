# V75 — libellés des listes de drapeaux de débogage

Base : V74 (cumulatif, à appliquer sur la ROM anglaise d'origine). Construit par `tools/build_v75.py` ; vocabulaire dans `tools/debug_labels_fr.py`.

- ROM V75 SHA-256 : 23838549a81d81c87283203ae1cd1a88b8f52b7462a82ee9e33b8122273c8bcf
- IPS V75 SHA-256 : 0e977a8eb0415886f67e1b3f30a4d3c5dce5272cc791a8c1578fde2e33d99595
- 518 libellés traduits (blocs 21 à 27 : drapeaux d'événements, trésors, villages, objets), aucune autre chaîne ni octet modifié.
- Noms de lieux et d'objets repris du jeu déjà traduit ; largeur ≤ 178 px (plus grand libellé anglais d'origine).
- Codes d'événements (E007, F001, D013…) et numéros conservés. Ces listes ne sont visibles que dans les menus de débogage.
- Zone libre de relocalisation restante : ~17 Ko (0x6B0000–0x6D0000).
