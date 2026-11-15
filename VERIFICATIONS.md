# Passe de vérification des points « non vérifiés / en suspens » (V56 à V66)

Résultat de la vérification à l'écran avec Snes9x (noyau compilé au commit 1bcc369e), sauvegardes fournies et
sauvegarde greffée dans l'état du menu titre.

| Point | Résultat | Preuve |
|---|---|---|
| 20 noms de lieux sur 21 non vus | **Vérifiés** : les 87 noms du jeu capturés à l'écran (octet 0x244 de la SRAM = index du lieu). 8 noms coupés trouvés et corrigés (V65) | `lieux_v64_valeurs_*.png`, `lieux_v65_cas_limites.png` |
| Barre « Total / Cash on Hand » | **Résolu** (V66) : copie de la bande à 0x6f0a00, 12 premières tuiles de la VRAM identiques à la ROM d'origine | `barre_sauvegarde_v66.png` |
| « Chan. » (Luck) | Rendu **vérifié** dans sa plage (tuiles 45-47) par affichage forcé ; usage en jeu non observé | `affichage_force_chan_catevas_restart_fichier.png` |
| « Ça te va ? » (Will this be okay?) | **Vérifié en jeu** (état de vente fourni) : après avoir retiré l'équipement (menu Équip. → Sans équip.), vendu le katana (44 ryo) puis choisi un Kusa dango à l'achat, la confirmation de quantité affiche « Ça te va ? » en bas de la fenêtre de droite (Total 8 ryo, Stock 0, Type Objet) | `boutique_confirmation_achat_cate_va.png` |
| « Rejouer + » (Restart +) | Rendu **vérifié** dans sa plage (tuiles 42-47), icône « + » incluse ; condition d'apparition en jeu non trouvée | idem |
| « Effacer fichier abîmé ? » | Rendu **vérifié** dans sa plage (tuiles 48-60, texte entier sans coupure) ; condition d'apparition non trouvée (corruptions de SRAM testées : réinitialisation de la date ou données aberrantes) | idem |
| « What will you » / « Sell? » (bloc d'achat) | Toujours en anglais et **non observés** malgré les flux d'achat et de vente complets (la vente n'a pas d'écran de confirmation : on valide la quantité et l'objet part ; l'achat confirme par « Ça te va ? »). Probablement des reliquats : « What will you sell? » existe déjà en une seule bande (10 tuiles) dans le bloc de vente | `boutique_vente_objet_vendable.png` |
| « Ach » / « Vte » | Vus en jeu (V58) ; contrainte de 2 tuiles par libellé | `boutique_v58_liste_et_arme.png` |

## Limites de la méthode d'« affichage forcé »
Elle remplace des mots de la carte de tuiles d'un état de jeu par les tuiles de la bande testée. Elle prouve que
le dessin tient dans sa plage et se lit bien en jeu (palette, ombre, icône), pas que le jeu emploie ce libellé à
cet endroit : l'usage repose sur le décodage des bandes et sur les tables d'affichage de la ROM, déjà exact pour
tous les libellés observés en jeu.

## Complément : flux de vente et d'achat réels (état `vente.state`)
Un objet n'est vendable que s'il n'est pas équipé : dans l'état fourni, tout l'équipement était équipé (objets grisés,
A sans effet). En le retirant par le menu Équip. (« Sans équip. »), le katana devient vendable : sélection → quantité →
validation, et la vente se fait sans confirmation (Argent 0 → 44 ryo). Cet argent permet ensuite d'acheter et de voir la
confirmation « Ça te va ? ».
