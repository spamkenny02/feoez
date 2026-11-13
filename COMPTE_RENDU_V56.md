# Compte rendu V56 — lot graphique 50 (écran Stratégie)

V56 = V55 + remplacement de 33 tuiles 2 bits à 0x6d4000 (bloc de libellés de la
liste de commandes de l'écran Stratégie). Construit par `tools/build_v56.py`
depuis la ROM anglaise d'origine : l'IPS V55 est appliqué (SHA-256 de la ROM V55
vérifié), puis les bandes de `traduction/menu_graphics_lot50_fr.json` sont
redessinées avec l'alphabet natif de `tools/menu_graphics_lot49.py`.

| Anglais | Français | Tuiles | Offset |
|---|---|---|---|
| Attack | Attaq. | 4 | 0x6d4000 |
| Items | Objet | 3 | 0x6d4040 |
| Scrolls | Parch. | 4 | 0x6d4070 |
| Manual | Manuel | 4 | 0x6d40b0 |
| Secret Skills | Arts secr. | 7 | 0x6d40f0 |
| Defend | Garder | 4 | 0x6d4160 |
| Set (de « Set Strategy ») | (vide) | 2 | 0x6d41a0 |
| Strategy | Stratégie | 5 | 0x6d41c0 |

Choix et limites :
- Le titre de l'écran et l'en-tête surligné partagent les tuiles de « Strategy » :
  l'en-tête affiche donc « Stratégie » (« Set » est vidé, faute de place pour un
  verbe dans 2 tuiles).
- « Arts secrets » (58 px) ne tient pas dans 7 tuiles (56 px) : forme courte
  « Arts secr. » (46 px). « Garder » reprend le libellé natif du menu de combat.
- « Plan A à D » (police script) est déjà compatible avec le français.

Vérification : reconstruction depuis la ROM d'origine, aller-retour IPS, et
capture Snes9x (commit 1bcc369e, noyau compilé localement) : voir
`verification/ecran_strategie_v56.png`. Le reste des libellés anglais
(écrans d'état, technique, boutique, nommage de l'animal) reste à traiter.
