# Passe de vérification des points « non vérifiés / en suspens » (V56 à V66)

Résultat de la vérification à l'écran avec Snes9x (noyau compilé au commit 1bcc369e), sauvegardes fournies et
sauvegarde greffée dans l'état du menu titre.

| Point | Résultat | Preuve |
|---|---|---|
| 20 noms de lieux sur 21 non vus | **Vérifiés** : les 87 noms du jeu capturés à l'écran (octet 0x244 de la SRAM = index du lieu). 8 noms coupés trouvés et corrigés (V65) | `lieux_v64_valeurs_*.png`, `lieux_v65_cas_limites.png` |
| Barre « Total / Cash on Hand » | **Résolu** (V66) : copie de la bande à 0x6f0a00, 12 premières tuiles de la VRAM identiques à la ROM d'origine | `barre_sauvegarde_v66.png` |
| « Chan. » (Luck) | Rendu **vérifié** dans sa plage (tuiles 45-47) par affichage forcé ; usage en jeu non observé | `affichage_force_chan_catevas_restart_fichier.png` |
| « Ça te va ? » (Will this be okay?) | Rendu **vérifié** dans sa plage (tuiles 90-98) par affichage forcé ; l'écran de confirmation d'achat/de vente est inatteignable avec la sauvegarde fournie (0 ryo, tout l'équipement est équipé donc invendable) | idem |
| « Rejouer + » (Restart +) | Rendu **vérifié** dans sa plage (tuiles 42-47), icône « + » incluse ; condition d'apparition en jeu non trouvée | idem |
| « Effacer fichier abîmé ? » | Rendu **vérifié** dans sa plage (tuiles 48-60, texte entier sans coupure) ; condition d'apparition non trouvée (corruptions de SRAM testées : réinitialisation de la date ou données aberrantes) | idem |
| « What will you » / « Sell? » (bloc d'achat) | Toujours en anglais : usage non observé | — |
| « Ach » / « Vte » | Vus en jeu (V58) ; contrainte de 2 tuiles par libellé | `boutique_v58_liste_et_arme.png` |

## Limites de la méthode d'« affichage forcé »
Elle remplace des mots de la carte de tuiles d'un état de jeu par les tuiles de la bande testée. Elle prouve que
le dessin tient dans sa plage et se lit bien en jeu (palette, ombre, icône), pas que le jeu emploie ce libellé à
cet endroit : l'usage repose sur le décodage des bandes et sur les tables d'affichage de la ROM, déjà exact pour
tous les libellés observés en jeu.
