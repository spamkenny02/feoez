#!/usr/bin/env python3
"""Build V65 = V64 IPS + lot 59 : noms de lieux encore coupes (revision).

Mesure a l'ecran (Snes9x, 96 valeurs de l'octet de lieu de la sauvegarde, 0x240+4) : la fenetre coupe a
96 px reels, et la police du moteur de texte est plus large que l'alphabet des bandes (largeurs
prevues sous-estimees). 8 noms atteignaient la limite (5 jamais touches, 3 deja raccourcis au lot 55).
Chaque nom est remplace sur place, complete par des espaces jusqu'a la longueur d'origine.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from french_font import encode_fr, visible_width  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V64_SHA = 'ff1a87de78a34c0cd34e5bb268b7dfef336cc045ce723470a419d8be0e517905'
PAD = encode_fr(' ')


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
    v64 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V64.ips').read_bytes())
    assert sha(v64) == V64_SHA, 'La ROM V64 reconstruite ne correspond pas'
    rom = bytearray(v64)
    entries = json.loads((ROOT / 'traduction/noms_lieux_revision_lot59_fr.json').read_text(encoding='utf-8'))
    report = []
    for e in entries:
        size = len(encode_fr(e['french_original']))
        cur = encode_fr(e['french_current'])
        new = encode_fr(e['french_new'])
        assert len(new) <= size and len(cur) <= size, e
        cur_p = cur + PAD * (size - len(cur))
        padded = new + PAD * (size - len(new))
        hits = [m.start() + 1 for m in re.finditer(re.escape(b'\0' + cur_p + b'\0'), bytes(v64))]
        assert len(hits) >= 2, (e, hits)
        for h in hits:
            assert rom[h:h + size] == cur_p
            rom[h:h + size] = padded
        report.append({'english': e['english'], 'french_current': e['french_current'], 'french_new': e['french_new'],
                       'offsets': [hex(h) for h in hits], 'bytes': size})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V65.ips').write_bytes(ips)
    summary = {'version': 'V65', 'base': 'V64', 'places': len(report),
               'replaced_occurrences': sum(len(r['offsets']) for r in report),
               'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True,
               'runtime_validation': 'capture Snes9x : verification/lieux_v65_*.png'}
    (ROOT / 'verification/build_report_v65.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
