#!/usr/bin/env python3
"""Build V73 = V72 IPS + lot 67 : etiquettes Defend et Flee de la roue de commandes du combat.

Meme mecanisme que le lot 63 (tools/build_v69.py) : deux flux SPC7110 de mode 2 (4 bits) de 128 octets
decompresses par etiquette, dans des emplacements de 0x80 octets : Defend = 0x505e00 / 0x505e80,
Flee = 0x506200 / 0x506280. Defend -> Garde, Flee -> Fuite. Les etiquettes 0x506300 a 0x506600 sont « Plan A »
a « Plan D » (identiques en francais) et ne sont pas modifiees.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
import spc7110  # noqa: E402
from build_v69 import word_body, render, sprite_data  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V72_SHA = 'afde0b6c9757e80b4907cc2623f5712e7fb63881f2380be5158fd0334b2c9781'


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
    v72 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V72.ips').read_bytes())
    assert sha(v72) == V72_SHA, 'La ROM V72 reconstruite ne correspond pas'
    table = json.loads((ROOT / 'traduction/etiquettes_combat_suite_lot67_fr.json').read_text(encoding='utf-8'))
    bg = [int(c, 16) for c in table['background']]
    slot = table['slot_bytes']
    rom = bytearray(v72); report = []
    for t in table['tags']:
        l, r = int(t['left_stream'], 16), int(t['right_stream'], 16)
        old = spc7110.decode_mode2(v72, l, 128) + spc7110.decode_mode2(v72, r, 128)
        assert sha(old) == t['old_tiles_sha256'], ('flux d\'origine inattendu', t['english'])
        img = render(word_body(table['glyphs'], t['french']), bg)
        for off, xo in ((l, 0), (r, 16)):
            data = sprite_data(img, xo)
            enc = spc7110.encode_mode2(data)
            assert len(enc) <= slot, (t['french'], len(enc))
            rom[off:off + len(enc)] = enc
            assert spc7110.decode_mode2(bytes(rom), off, 128) == data, ('relecture KO', t['french'], hex(off))
            report.append({'english': t['english'], 'french': t['french'], 'stream': hex(off),
                           'compressed_bytes': len(enc), 'slot_bytes': slot})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V73.ips').write_bytes(ips)
    summary = {'version': 'V73', 'base': 'V72', 'streams': len(report), 'max_compressed_bytes': max(x['compressed_bytes'] for x in report),
               'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True}
    (ROOT / 'verification/build_report_v73.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
