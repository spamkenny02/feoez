# Tengai Makyou Zero — V76 : dates françaises

Appliquer **Tengai_Makyou_Zero_JP_vers_FR_V76.ips** directement à la ROM
**japonaise originale sans en-tête (5 242 880 octets)**. Le patch est cumulatif :
il inclut la traduction V75 et produit une ROM de 7 340 032 octets.
Ne pas l'appliquer sur une ROM anglaise ou déjà patchée.

- SHA-256 source JP : `8620203da71d32d017bb21f542864c1d90705b87eb67815d06b43f09120318aa`.
- SHA-256 ROM V76 : `71d3eccf11ce58d3f689c3b97f80ed19890d1d96d2665562f0cc769111212937`.
- Horloge et naissance : saisie, affichage et confirmation **jour-mois-an**.
- Almanach : date numérique jour-mois-an, chiffres 1 et 6 visibles.
- Les deux redirections retirées dans la variante V75 validée sur SD2SNES restent désactivées.

Construction à partir de la seule ROM japonaise :

```bash
python tools/build_v76.py "Tengai Makyou Zero (Japan).sfc" --rom-out fr_v76.sfc
python tools/verify_date_order_v76.py "Tengai Makyou Zero (Japan).sfc" --out verification/date_order_v76_checks.json
```

Voir [bilan V76](COMPTE_RENDU_V76.md) et [rapport de saisie](verification/date_order_v76_runtime/report.json).
Les contrôles natifs et le parcours Snes9x ont réussi ; **V76 reste à tester sur SD2SNES**.
Les anciens patches et scripts EN sont conservés comme historique. Les nouvelles
versions publiées partent de la ROM japonaise uniquement.

---

# Tengai Makyou Zero — Traduction française V55

**Lot49 complet :400 nouveaux textes distincts, phase1.**
231 sources bornées,114 du générique,51 graphiques et4 natives.
Les6534 occurrences V54 sont préservées ;total6769 occurrences bornées.
25 abréviations d’affichage corrigées, sans recompter les noms complets.

## Installation

Appliquer **Tengai_Makyou_Zero_FR_V55.ips** directement à la ROM anglaise
originale sans en-tête,7340032 octets, sans cumuler les patches.
SHA256 source :`eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e`.
SHA256 ROM V55 :`2631d90bd0f2b0ed927055143117525517d06f15f29511439d6e76acdc371e4c`.
Ni ROM, ni noyau, ni état, ni dump mémoire ne sont distribués.

## Construction et essais

```bash
python tools/build_v55.py /chemin/original.sfc --rom-out /chemin/emulator/fr_v55.sfc
python tools/verify_storage.py /chemin/original.sfc --version V55 --built-rom /chemin/emulator/fr_v55.sfc --build-report verification/build_report.json
python tools/audit_new_sources_lot49.py
python tools/audit_prior_sources_lot49.py
```

[Reproduction des essais](verification/reproduction/REPRODUIRE_V55.md).
7602 lectures natives,235 copies/largeurs de bandeaux,629 copies du générique,
24 cas du nettoyage de glyphes et36 paires de noms abrégés/complets.
Démarrage A/reset/B et navigation ;235+235 rendus ciblés,466 captures relues
sur30 planches. Générique complet en fixture :122 occurrences traduites
comparées aux pixels natifs et relues sur8 planches. Menus réels, grilles
synthétiques, premier combat naturel et Almanach22/12/1995 contrôlés.

## Couverture et limites

**La traduction complète du jeu n’est pas achevée.** Phase1 reste ouverte ;
recherche exhaustive des oublis et relecture globale restent à faire.
Le compteur borné comprend menus, vides et debug ;il ne mesure pas le jeu.
Des commandes de Stratégie et noms d’objets anglais restent visibles.
Le bloc42 non borné, les autres graphismes, fins/branches/dates, sélecteurs et
synchronisation des chansons restent à contrôler. Les fixtures n’établissent
ni la fin naturelle ni tous les déclenchements de combat.

[Suivi](SUIVI_FEOE.md) · [Bilan V55](COMPTE_RENDU_V55.md) ·
[Glossaire](glossaire_et_style.md) · [Couverture](verification/coverage_v55.json)
