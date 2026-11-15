#!/usr/bin/env python3
"""Build V64 = V63 IPS + lot 58 : revision de noms d'objets raccourcis (relecture).

Reecrit 9 bandes de noms d'objets deja redessinees au lot 51 par une forme plus naturelle (meme
largeur maximale de 64 px, icone comprise). Chaque bande est verifiee identique au rendu du lot 51
avant d'etre remplacee ; la table du lot 51 reste inchangee (historique).
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from build_v57 import render, icon_of, pixels  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V63_SHA = '13ecfc60220559de4d0845a989d1e5f57ba5790b2eaf587b13cf61e7c892fb15'


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
    v63 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V63.ips').read_bytes())
    assert sha(v63) == V63_SHA, 'La ROM V63 reconstruite ne correspond pas'
    rom = bytearray(v63)
    entries = json.loads((ROOT / 'traduction/noms_objets_revision_lot58_fr.json').read_text(encoding='utf-8'))
    report = []
    for e in entries:
        off = int(e['offset'], 16)
        icon = icon_of(pixels(source, off)) if e['icon'] else None
        old, _ = render(source, e['french_old'], icon)
        assert v63[off:off + 128] == old, ('bande differente du lot 51', e)
        new, px = render(source, e['french'], icon)
        rom[off:off + 128] = new
        report.append({'index': e['index'], 'offset': e['offset'], 'english': e['english'],
                       'french_old': e['french_old'], 'french': e['french'], 'pixels': px})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V64.ips').write_bytes(ips)
    summary = {'version': 'V64', 'base': 'V63', 'revised_names': len(report), 'ips_sha256': sha(ips),
               'rom_sha256': sha(out), 'ips_roundtrip': True}
    (ROOT / 'verification/build_report_v64.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
