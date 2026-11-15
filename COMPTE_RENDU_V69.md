# Compte rendu V69 — lot 63 : roue de commandes du combat (outil de compression SPC7110)

V69 = V68 + 8 flux compressés réécrits (`tools/build_v69.py`, table `traduction/etiquettes_combat_lot63_fr.json`,
outil `tools/spc7110.py`), reconstruit depuis la ROM d'origine (IPS V68 appliqué, SHA-256 vérifié, aller-retour IPS
contrôlé).

## L'outil de compression (`tools/spc7110.py`)
Les sprites de combat (étiquettes, chiffres, « Failed »…) sont stockés compressés en SPC7110. Le module contient :
- un **décompresseur** Python (modes 4 bits utilisés ici), transcription de la logique de byuu/neviksti publiée dans
  Snes9x (contextes adaptatifs, ordre de pixels par « move-to-front », conversion Morton) ;
- un **compresseur** : miroir exact du décodeur (même modèle de contextes et d'évolution des probabilités,
  intervalle arithmétique tenu en entiers Python à précision arbitraire, puis choix dans l'intervalle final de la
  valeur aux octets de fin minimaux). Les bits qui suivent le flux n'influencent jamais le décodage.
Validation : les 8 flux d'origine, décompressés puis recompressés, se relisent identiques, et mes octets coïncident
avec ceux d'origine jusqu'aux 1-2 derniers (choix du point final de l'intervalle). Le décodeur Python est identique
à un décodeur C transcrit du code Snes9x sur les 8 flux, et ce dernier a retrouvé dans la ROM les flux qui produisent
les tuiles lues dans la VRAM de l'état de combat (3 963 flux candidats balayés).

## Où sont les étiquettes
Chaque étiquette est faite de 2 sprites 16×16 (table OAM de l'état) ; chaque sprite = 4 tuiles 4 bits = un flux de
mode 2 de 128 octets décompressés, dans un emplacement de 0x80 octets :
| Étiquette | Flux gauche / droit |
|---|---|
| Attack | 0x505d00 / 0x505d80 |
| Skills | 0x506000 / 0x506080 |
| Items | 0x506100 / 0x506180 |
| Scrolls | 0x505f00 / 0x505f80 |
(base d'objets 0xc000 ; tuiles OBJ 13/76, 78/174, 192/194, 196/198.)

## Changements
Attack → **Attaq.**, Skills → **Arts**, Items → **Objet**, Scrolls → **Parch.** (mots cohérents avec l'écran Stratégie).
- Style : lettres en corps (indices 2/3) avec ombre portée (règle gauche/haut/haut-gauche, exacte à 2 pixels près sur
  1 254 pixels d'origine) et reflets sur les bords haut et bas (85 %), sur le motif de fond de la plaque `c4c848c4848c4c48`.
  Les lettres A, t, a, c, r, s, e, o sont extraites des étiquettes d'origine ; **q, j, h, b, O, P et le point sont
  dessinés** dans le même style (aucune lettre n'a de jambage : la hauteur du sprite l'interdit).
- Taille : 52 à 61 octets compressés pour 128 disponibles par emplacement.

## Vérification
`verification/combat_roue_v69.png` : les flux de la ROM V69 sont décompressés avec le décodeur C et chargés dans la
VRAM de l'état de combat fourni, aux adresses d'objets d'origine (c'est ce que fait le jeu au début du combat) ; les
quatre positions de la roue (Attaq. / Arts / Objet / Parch., sélectionné et non sélectionné) sont capturées.
**Limite** : la décompression n'est pas exécutée par le jeu lui-même (l'état est pris en plein combat, après le
chargement des sprites) ; elle s'appuie sur le décodeur transcrit du code Snes9x, validé sur les flux d'origine.

## Reste en anglais en combat
Le mot « Failed » et les chiffres de dégâts (sprites compressés eux aussi) : à traiter avec le même outil.
