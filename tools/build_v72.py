#!/usr/bin/env python3
"""Build V72 = V71 IPS + lot 66 : alignement des coeurs du texte sur la grille de tuiles.

Corrige le coeur « moitie rouge, moitie blanc » (et le « ! » qui devient rouge) : voir tools/heart_align.py et
COMPTE_RENDU_V72.md. Pour chaque coeur de chaine francaise (<09><6E>...<08>), l'espace qui le precede est recode en
un blanc de largeur adaptee pour que le coeur commence a 0 ou 1 px d'une frontiere de tuile (8 px). Six codes de
police inutilises par les textes (glyphe vide, largeur 1, 2, 4, 5, 6, 7) servent de blancs ; la largeur 3 est
l'espace normal. Le nombre d'octets de chaque chaine ne change pas.
"""
import argparse, collections, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
import french_font as ff  # noqa: E402
import heart_align as H  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V71_SHA = 'af6d3a2a344c6528caf4a0317c4f078536b8f36bd5c429b685a9b8c5369d10c1'
BLANK_CODE = {1: 0xb4, 2: 0xbf, 4: 0xd4, 5: 0xca, 6: 0xbc, 7: 0xd9}   # largeur -> code ; 3 = espace (0x20)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v71 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V71.ips').read_bytes())
    assert sha(v71) == V71_SHA, 'La ROM V71 reconstruite ne correspond pas'
    rom = bytearray(v71)
    # 1. police : blancs de largeur 1, 2, 4, 5, 6, 7
    for w, code in BLANK_CODE.items():
        assert v71[ff.FONT + code * 32:ff.FONT + code * 32 + 32] != b'\x00' * 32
        rom[ff.FONT + code * 32:ff.FONT + code * 32 + 32] = b'\x00' * 32
        rom[ff.WIDTHS + code] = w
    # 2. textes
    plan, skipped = H.analyse(v71)
    report, unresolved = [], []
    for pl0 in sorted(plan, key=lambda d: d['pos']):
        cur = bytes(rom)
        pl = H.heart_info(cur, pl0['pos'], pl0['ls'], pl0['e'])      # position tenant compte des coeurs deja traites
        assign, mode = H.solve(cur, pl)
        if assign is None:
            assign, mode = H.solve(cur, pl, limit=222)      # reprise : tolere 6 px dans la marge de la boite
            mode = (mode + ' (limite 222)') if assign is not None else mode
        if assign is None:
            unresolved.append({'pos': hex(pl['pos']), 'x': pl['x'], 'raison': mode}); continue
        if not assign:
            continue
        for q, w in assign.items():
            assert rom[q] in (0x20,) + tuple(BLANK_CODE.values())
            rom[q] = 0x20 if w == 3 else BLANK_CODE[w]
        report.append({'pos': hex(pl['pos']), 'x_avant': pl['x'], 'mode': mode,
                       'modifs': {hex(q): w for q, w in sorted(assign.items())}})
    out = bytes(rom)
    # 3. contrôle : relire le plan sur la ROM modifiée
    plan2, _ = H.analyse(out)
    bad = [pl for pl in plan2 if pl['x'] % 8 not in (0, 1)]
    assert len(bad) == len(unresolved), (len(bad), len(unresolved), [hex(x['pos']) for x in bad])
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V72.ips').write_bytes(ips)
    summary = {'version': 'V72', 'base': 'V71', 'hearts_total': len(plan), 'hearts_fixed': len(report),
               'hearts_already_ok': len(plan) - len(report) - len(unresolved), 'hearts_unresolved': len(unresolved),
               'bytes_changed': sum(len(r['modifs']) for r in report), 'blank_codes': {str(k): hex(v) for k, v in BLANK_CODE.items()},
               'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True}
    (ROOT / 'verification/build_report_v72.json').write_text(
        json.dumps({**summary, 'unresolved': unresolved, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('non résolus :', unresolved)


if __name__ == '__main__':
    main()
