#!/usr/bin/env python3
"""Build V74 = V73 + derniers textes visibles non traduits (faiblesses, possession, onomatopée)
+ phrases des menus de débogage / tests. Utilise tools/feoez_kit.py (base = V73)."""
import csv, sys, json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import feoez_kit as kit  # noqa: E402
from insert import make_ips, apply_ips  # noqa: E402

EDITS = {
 # --- visibles en jeu
 'B041-S110': "Ouaaaaargh !<0D> Haaaaaaah !",
 'B041-S145': "Possédé : ", 'B041-S146': "Équipement", 'B041-S147': "Possédé : ",
 'B043-S007': "Tous",
 'B044-S001': "Physique", 'B044-S002': "Feu", 'B044-S003': "Eau", 'B044-S004': "Vent", 'B044-S005': "Foudre",
 'B044-S007': "Aucune faiblesse",
 'B044-S008': "<04>-<05>-<06>-<07> : faiblesse extrême",
 'B044-S009': "<04>-<05>-<06>-<07> : faiblesse",
 'B032-S002': "<17>Il n'y a aucun message ici !<18>x5",
 'B032-S003': "Tu ne peux pas entrer ici !",
 'B033-S001': "<17>Impossible de l'utiliser sur le terrain !\nErreur !<18>x5",
 # --- salle de test / menus de débogage
 'B030-S006': "Erreur", 'B030-S007': "Erreur", 'B030-S008': "Erreur",
 'B034-S001': "Entrez donc !<0E>", 'B034-S002': "Revenez nous voir !",
 'B034-S003': "Vous voulez loger gratis, hein ?", 'B034-S004': "Ne vous fatiguez pas trop, je vous en prie !",
 'B034-S005': "Vers le combat de robots !", 'B034-S006': "Vers le tir !", 'B034-S008': "Vers le générique<0E>",
 'B034-S010': "groupe", 'B034-S012': "Personnes",
 'B036-S002': "50 000 ryo ajoutés.\nActiver le drapeau de la fête ?",
 'B036-S003': "Ceci est le débogage des fenêtres.\nTu travailles dur, hein ? Continue comme ça !",
 'B037-S036': "Ceci est une erreur. Où suis-je ? Y a-t-il\nun panneau ici ?",
 'B037-S051': "Ceci est une erreur. Où est-ce ? Y a-t-il un\npanneau ici ?",
 'B132-S059': "Erreur aléatoire", 'B132-S122': "Erreur du kiosque. Article indéterminé !",
 'B183-S001': "Higan pétrifié ?", 'B183-S002': "Subaru pétrifié ?", 'B183-S003': "Tenjin pétrifié ?", 'B183-S004': "Mizuki pétrifiée ?",
 'B183-S005': "Aller au sanctuaire de la Tortue ?", 'B183-S006': "Le sanctuaire de la Tortue avant sa libération ?",
 'B183-S007': "Aller au village de la Tête de montagne ?", 'B183-S008': "Aller au village du Lac bleu ?",
 'B183-S009': "Aller au village du Lac bleu avant\nsa libération ?",
 'B183-S010': "Aller en Forêt 1 ?", 'B183-S011': "Aller en Forêt 2 ?", 'B183-S012': "Aller en Forêt 3 ?",
 'B183-S013': "Aller au jardin fleuri de Juri ?",
 'B183-S014': "Activer l'événement D011 ?", 'B183-S016': "Activer l'événement D012 ?", 'B183-S018': "Activer l'événement D013 ?",
 'B183-S020': "Activer l'événement D014 ?", 'B183-S022': "Activer l'événement D015 ?", 'B183-S024': "Activer l'événement D016 ?",
 'B183-S026': "Aller au château de l'Arbre-Énigme ?", 'B183-S027': "Aller au château de la Tortue ?",
 'B183-S028': "Aller au grenier du château de la Tortue ?", 'B183-S029': "Aller au pont Grue-Tortue ?",
 'B183-S030': "Voir l'épilogue 2 ?", 'B183-S031': "Voir l'événement F015 ?", 'B183-S032': "Aller à l'arche ?",
 'B183-S033': "Faire arracher la carte ?", 'B183-S034': "Démo Mizuki ?", 'B183-S035': "Démo Crabe ?",
 'B252-S098': "Lancer le test d'événement ?", 'B252-S101': "Cet événement mène toujours à un Game Over.<0E>",
}

def main():
    src = Path(sys.argv[1]).read_bytes()
    assert kit.sha(src) == kit.EXPECTED
    v73 = apply_ips(src, (ROOT / 'Tengai_Makyou_Zero_FR_V73.ips').read_bytes())
    rows = kit.text_rows(src, v73)
    by = {r['id']: r for r in rows}
    for k, v in EDITS.items():
        assert k in by, k
        by[k]['fr'] = kit.esc(v)
    rom, rep = kit.build_rom(src, v73, by, None)
    ips = make_ips(src, rom)
    assert apply_ips(src, ips) == rom
    (ROOT / 'Tengai_Makyou_Zero_FR_V74.ips').write_bytes(ips)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_bytes(rom)
    print(json.dumps({'version': 'V74', 'strings_edited': len(EDITS), 'rom_sha256': kit.sha(rom), 'ips_sha256': kit.sha(ips), **rep}, indent=1))

if __name__ == '__main__':
    main()
