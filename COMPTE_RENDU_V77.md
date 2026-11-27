# V77 — libellés complets des menus

Le patch cumulatif s'applique directement à la ROM japonaise originale sans en-tête
(5 242 880 octets), sans appliquer V75 ou V76 auparavant. La sortie fait 7 340 032 octets.

Les graphismes utilisent l'alphabet natif 8 pixels, avec un espacement resserré
lorsque nécessaire. Aucun pixel du corps des lettres n'est réduit ou coupé.
Les cadres, commandes et logiques de sélection restent ceux de V76.

Libellés complétés : Parchemins, Équipement, Horloge, Temps de jeu, Utiliser,
Modifier, Coût technique, Remplacer, Objets, Attaque, Chance, rang suivant,
Sans équipement, Musique, Mémoire du curseur, Vitesse du texte,
Vitesse de marche, Forme du cadre et Couleur du cadre.
« Équip. auto » devient « Automatique » dans le menu Équipement.
Le titre textuel Équip. de l'écran État devient également Équipement.

Les atlas sont réorganisés dans leurs plages existantes. Les commandes Parchemins
et Inventaire chargent chacune une tuile supplémentaire dans un emplacement nul
vérifié. Les références des descripteurs de menu sont ajustées. Pour Coût technique
et Chance, seule l'ombre à droite peut être rognée ; les lettres restent entières.
Les glyphes natifs et le pool des dialogues restent identiques à V76.
Les deux appels natifs conservés pour SD2SNES restent inchangés.

Construction :

```bash
python tools/build_v77.py "Tengai Makyou Zero (Japan).sfc" --rom-out fr_v77.sfc
```

SHA-256 source JP : `8620203da71d32d017bb21f542864c1d90705b87eb67815d06b43f09120318aa`.
SHA-256 IPS V77 : `a07ea65afc08e4fee836de42ea416f7df270c3610b3e512479ba01a934f8c5db`.
SHA-256 ROM V77 : `f07747fd3bfeebcd1bd566d43d7e39fad17e52e413e1d05374f4cb6628f3f8a6`.
Checksum : `0xe76e` ; aller-retour IPS exact.
Nombre d'octets différents de V76 : 2153.

Vérifications : écritures bornées aux plages du rapport, allocations sans
chevauchement, tuiles bornées, corps des lettres entier, police/dialogues préservés.
Les 8 423 cas natifs de date V76 passent aussi sur V77.
Captures en émulation des menus principal, parchemins, réglages, inventaire,
actions, équipement, état, horloge et stratégie ; revue visuelle des libellés.
Le démarrage et le parcours jusqu'au terrain sont exécutés avec la ROM finale.
Aucune nouvelle validation SD2SNES : un essai matériel V77 reste nécessaire.

Reproduction des captures depuis le field_verified.state du scénario complet
exécuté sur la même ROM :

```bash
python verification/reproduction/run_menu_labels_v77.py --core snes9x_libretro.dll --rom fr_v77.sfc --state field_verified.state --out captures_v77
```

Voir `verification/build_report_v77.json` pour chaque libellé, tuile, largeur,
espacement et modification de descripteur. Les anciennes tables de traduction
sont conservées pour reproduire les versions historiques ; V77 utilise
`tools/menu_full_labels.py`.
