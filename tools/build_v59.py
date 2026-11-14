#!/usr/bin/env python3
"""Build V59 = V58 IPS + lot 53 : libelles Rank/Health des panneaux de personnage.

Bandes de 3 a 4 tuiles redessinees avec l'alphabet natif : Rank -> Rang (bloc 0x6f4000, ecran
Equip., et bloc 0x6f2000, ecran Parchemins) et Health -> Vie (bloc 0x6f2000). Plages de tuiles lues
dans la carte de tuiles de chaque ecran ; « Technique » est identique en francais : inchange.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from menu_graphics_lot49 import glyph  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V58_SHA = '5b95a9e8af112f988526e4ae110ce874286b9422d57a336a662a8f838be231ab'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def render(source, text, tiles, align, limit):
    text = text.replace('’', "'").replace('œ', 'oe').replace('Œ', 'OE')
    gs = [glyph(source, c) for c in text]
    width = sum(len(g[0]) + 1 for g in gs) - 1
    W = tiles * 8
    assert width + 1 <= min(limit, W), (text, width + 1, limit)
    x = (min(limit, W) - width - 1) if align == 'right' else 0
    body = [[0] * W for _ in range(8)]
    for g in gs:
        for y in range(8):
            body[y][x:x + len(g[y])] = g[y]
        x += len(g[0]) + 1
    out = bytearray(tiles * 16)
    for xx in range(W):
        for y in range(8):
            v = 2 if body[y][xx] else 1 if xx and body[y][xx - 1] else 0
            p = (xx // 8) * 16 + y * 2
            bit = 128 >> (xx % 8)
            if v & 1:
                out[p] |= bit
            if v & 2:
                out[p + 1] |= bit
    return bytes(out), width + 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v58 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V58.ips').read_bytes())
    assert sha(v58) == V58_SHA, 'La ROM V58 reconstruite ne correspond pas'
    rom = bytearray(v58)
    entries = json.loads((ROOT / 'traduction/panneau_personnage_lot53_fr.json').read_text(encoding='utf-8'))
    report, spans = [], []
    for e in entries:
        off = int(e['offset'], 16)
        n = e['tiles'] * 16
        assert v58[off:off + n] == source[off:off + n], e
        assert not any(off < z and off + n > s for s, z in spans), e
        spans.append((off, off + n))
        new, px = render(source, e['french'], e['tiles'], e['align'], e['limit_px'])
        rom[off:off + n] = new
        report.append({'offset': e['offset'], 'english': e['english'], 'french': e['french'],
                       'pixels': px, 'limit_px': e['limit_px'], 'screen': e['screen']})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V59.ips').write_bytes(ips)
    summary = {'version': 'V59', 'base': 'V58', 'strips': len(report), 'ips_sha256': sha(ips),
               'rom_sha256': sha(out), 'ips_roundtrip': True,
               'runtime_validation': 'captures Snes9x : verification/panneau_personnage_v59_*.png'}
    (ROOT / 'verification/build_report_v59.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
