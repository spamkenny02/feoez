# V76 — dates françaises, base japonaise uniquement

## Résultat

La date de l'horloge, celle de naissance et leurs confirmations passent de
mois-jour-an à jour-mois-an. L'Almanach utilise également jour-mois-an.
Exemple contrôlé à l'écran : **22-12-1995**.
Le stockage interne année/mois/jour et l'interface RTC ne sont pas réordonnés.
Les événements et les sauvegardes conservent donc leur convention native.
Le format horaire AM/PM reste celui de V75.

La base est exactement le patch V75 « sans hooks » fourni par l'utilisateur et
validé par lui sur SD2SNES. Les appels natifs aux offsets 0x006F59 et 0x037029
restent identiques à ceux de la ROM japonaise. Les autres routines existantes
sont conservées, notamment celles de l'horloge et de l'Almanach.

## Changements techniques

- 0x00EB91 : positions de rendu du jour et du mois échangées pour horloge/naissance.
- 0x6D25F0 : correspondance du curseur vers les champs internes : jour, mois, année, heure, minute.
- 0x6F1783 et 0x6F1789 : mots jour/mois échangés dans la routine existante de l'Almanach.
- 0x6F17A1–0x6F17C0 : prolongement de cette routine dans une zone nulle vérifiée.
  Remappage des chiffres natifs D4 et D9 vers les chiffres normaux 2F et 25,
  uniquement dans les dix octets de date. A, X et P sont préservés.
- 0x00F1D4 et 0x6D2536 : consignes de format de date mises à jour.
- Checksum et complément recalculés selon la convention de somme brute du projet.

V72 avait réutilisé D4 (1) et D9 (6) comme espaces pour aligner les cœurs.
Leur restauration globale aurait perturbé ces textes. Le remappage dans la date
de l'Almanach garde les glyphes et largeurs de la police inchangés.
Les autres affichages numériques utilisant ces glyphes, par exemple l'année
historique dans l'Almanach, ne sont pas corrigés par ce remappage ciblé.

Seulement **54 octets** de la ROM résultante diffèrent de la V75 SD2SNES.
Aucune ROM anglaise n'est lue ou nécessaire pour construire V76.
Le script applique en mémoire le patch JP V75 épinglé, puis les changements V76,
et génère un unique IPS cumulatif à appliquer à la ROM japonaise d'origine.
Les ROM et dumps de test ne sont pas distribués.

## Empreintes

- ROM JP (5 242 880 octets) : `8620203da71d32d017bb21f542864c1d90705b87eb67815d06b43f09120318aa`.
- Base IPS JP V75 : `26e4f1fd94387f7e39f6d10c8fc24a7975b57325c1e5906025ea3bdc10783364`.
- IPS JP V76 (2194010 octets) : `bac055b448ad5689510f0d7c9372cb8cfbdf5a90d016f1092c60ee9447e98b4f`.
- ROM V76 (7 340 032 octets) : `71d3eccf11ce58d3f689c3b97f80ed19890d1d96d2665562f0cc769111212937`.
- Checksum : `0x7e8c` ; complément vérifié, aller-retour IPS exact.

## Validation

- 3 267 exécutions du rendu natif : toutes les dates de 1995, 1996, 2000, 2001
  et 2099, puis toutes les combinaisons heure/minute sur le 29 février 2000.
- 5 120 exécutions de la routine native de modification : cinq champs,
  256 valeurs, incréments/décréments de 1 et 10 ; pile et stockage préservés.
- 36 dates dans la routine native de réordonnancement de l'Almanach ; chiffres
  1/6 lisibles via leurs codes normaux, largeurs équivalentes et A/X/P préservés.
- Snes9x 1.63 : démarrage neuf A/reset/B, saisie et confirmation de l'horloge
  **23-01-1996 13:01**, registres RTC vérifiés ; naissance **23-01-1994**
  enregistrée dans les champs natifs ; **31-02-1995 refusé**, retour au jour et
  bouclage 31→1 ; retour du mois au jour avec Gauche vérifié.
- Parcours complet de démarrage puis ouverture de l'Almanach avec les boutons,
  à partir d'un état créé avec la ROM V76 finale : **22-12-1995** lisible.
- Les deux appels natifs SD2SNES sont conservés ; la police et le pool des
  dialogues ne changent pas. Les modifications sont bornées aux spans documentés.

Le noyau récent téléchargé a échoué aux tests RTC de démarrage aussi sur la ROM
japonaise intacte ; le contrôle a donc utilisé le noyau local Snes9x 1.63 qui
réussit cette initialisation. Son empreinte figure dans le rapport. Seuls ses
noms d'import CRT Windows ont été adaptés au chargement ; la logique d'émulation
n'a pas été modifiée pour V76.

**Validation matérielle V76 en attente.** La compatibilité SD2SNES confirmée par
l'utilisateur porte sur V75 ; les tests d'émulation ne remplacent pas ce nouvel essai.

## Reproduction

```bash
python tools/build_v76.py "Tengai Makyou Zero (Japan).sfc" --rom-out fr_v76.sfc
python tools/verify_date_order_v76.py "Tengai Makyou Zero (Japan).sfc" --out verification/date_order_v76_checks.json
python verification/reproduction/run_date_order_v76.py --core snes9x_libretro.dll --rom fr_v76.sfc --out nouveau_dossier_tests
```

Pour le parcours complet : utiliser `verification/reproduction/scenario.json`
avec `libretro_runner.py`, résoudre `@RUN_DIR@` vers le dossier de test, puis
ouvrir l'Almanach avec `verification/calendar_lot46_checkpoint/commands.json`
en remplaçant son état initial par le `field_verified.state` du même parcours.
La ROM et les états doivent provenir de la même construction V76.

Rapports : [construction](verification/build_report_v76.json),
[exécution native](verification/date_order_v76_checks.json),
[parcours et captures](verification/date_order_v76_runtime/report.json).
