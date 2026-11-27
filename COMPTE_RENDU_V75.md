# V75 — libellés des listes de drapeaux de débogage

Base : V74 (cumulatif, à appliquer sur la ROM anglaise d'origine). Construit par `tools/build_v75.py` ; vocabulaire dans `tools/debug_labels_fr.py`.

- ROM V75 historique avec redirections (ne décrit pas la variante SD2SNES) SHA-256 : 23838549a81d81c87283203ae1cd1a88b8f52b7462a82ee9e33b8122273c8bcf
- IPS V75 historique avec redirections SHA-256 : 0e977a8eb0415886f67e1b3f30a4d3c5dce5272cc791a8c1578fde2e33d99595
- 518 libellés traduits (blocs 21 à 27 : drapeaux d'événements, trésors, villages, objets), aucune autre chaîne ni octet modifié.
- Noms de lieux et d'objets repris du jeu déjà traduit ; largeur ≤ 178 px (plus grand libellé anglais d'origine).
- Codes d'événements (E007, F001, D013…) et numéros conservés. Ces listes ne sont visibles que dans les menus de débogage.
- Zone libre de relocalisation restante : ~17 Ko (0x6B0000–0x6D0000).

## Variante SD2SNES retenue

La variante fournie par l'utilisateur est la référence fonctionnelle sur SD2SNES.
Le patch JP publié est une copie exacte de ce fichier ; le patch sur base anglaise
omet les mêmes deux enregistrements de trois octets.

- JP → FR V75 : 2 194 010 octets, SHA-256 `26e4f1fd94387f7e39f6d10c8fc24a7975b57325c1e5906025ea3bdc10783364`.
- EN → FR V75 : 907 542 octets, SHA-256 `90652822a1f4d3137a31b896b7c15a0b575cf10b983fbc6fb7e614477696d645`.
- `0x006F59–0x006F5B` : suppression de `D0 94 4C`, destination JSL du menu des parchemins.
- `0x037029–0x03702B` : suppression de `F0 94 4C`, destination JSL de correction du générique.

Les emplacements omis conservent les octets de la ROM source. Les routines à
`0x6C94D0` et `0x6C94F0`, leurs données, et tous les autres octets du patch sont
conservés. La désactivation peut réintroduire les défauts d'affichage que ces
routines corrigeaient ; ces écrans restent à contrôler sur matériel.

`tools/build_v75.py` conserve désormais les destinations natives après la
construction, via `tools/sd2snes_compat.py`. `tools/make_ips_from_jp.py` applique
la même politique lors de la conversion JP. Le checksum reste volontairement
celui du fichier testé : le recalcul changerait la référence validée. Sa validité
arithmétique et l'empreinte de la ROM finale restent à vérifier avec la ROM source.

Validation effectuée : comparaison des écritures IPS, reconstruction exacte du
fichier fourni en supprimant uniquement les deux enregistrements, cohérence des
patches JP et EN, contrôle de la politique de génération sur ROM synthétique.
La compilation complète et les essais en émulateur/matériel n'ont pas été exécutés,
faute de ROM source dans ce travail. Le constat SD2SNES vient de l'utilisateur.
