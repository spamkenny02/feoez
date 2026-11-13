#!/usr/bin/env python3
"""Build V57 = V56 IPS + lot 51 : noms d'objets (bandes graphiques 8 tuiles).

Les noms d'objets des boutiques et de l'ecran Equip. sont des bandes de 8 tuiles
2 bits (64 px) rangees dans l'ordre des objets a partir de 0x6f6000 (128 octets
par objet). Chaque bande est redessinee avec l'alphabet natif ; l'icone finale
(lettre, epee, katana, armure, kimono, pierre...) est conservee telle quelle.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from menu_graphics_lot49 import glyph  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V56_SHA = '0c2908b76b5681e8d00be64f2126152c1292c8b8ab4846ada6671a89c6a8eddd'
TILES = 8
W = TILES * 8


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pixels(rom, off):
    """Matrice 8 x W de valeurs 2 bits (0-3) d'une bande."""
    px = [[0] * W for _ in range(8)]
    for t in range(TILES):
        raw = rom[off + t * 16: off + t * 16 + 16]
        for y in range(8):
            for x in range(8):
                b = 7 - x
                px[y][t * 8 + x] = ((raw[y * 2] >> b) & 1) | (((raw[y * 2 + 1] >> b) & 1) << 1)
    return px


def icon_of(px):
    """Dernier groupe de colonnes portant des pixels de corps (valeur 2/3), ombre comprise."""
    on = [any(px[y][x] & 2 for y in range(8)) for x in range(W)]
    x1 = max(x for x in range(W) if on[x])
    x0 = x1
    while x0 > 0 and on[x0 - 1]:
        x0 -= 1
    x2 = min(W, x1 + 2)
    return [row[x0:x2] for row in px]


def render(source, text, icon):
    text = text.replace('’', "'").replace('œ', 'oe').replace('Œ', 'OE')
    gs = [glyph(source, c) for c in text]
    width = sum(len(g[0]) + 1 for g in gs) - 1
    body = [[0] * W for _ in range(8)]
    x = 0
    for g in gs:
        assert x + len(g[0]) <= W, text
        for y in range(8):
            body[y][x:x + len(g[y])] = g[y]
        x += len(g[0]) + 1
    val = [[2 if body[y][xx] else 1 if xx and body[y][xx - 1] else 0 for xx in range(W)] for y in range(8)]
    total = width + 1
    if icon is not None:
        ix = width + 3
        assert ix + len(icon[0]) <= W, (text, ix + len(icon[0]))
        for y in range(8):
            for k, v in enumerate(icon[y]):
                val[y][ix + k] = v
        total = ix + len(icon[0])
    assert total <= W, (text, total)
    out = bytearray(TILES * 16)
    for xx in range(W):
        for y in range(8):
            v = val[y][xx]
            p = (xx // 8) * 16 + y * 2
            bit = 128 >> (xx % 8)
            if v & 1:
                out[p] |= bit
            if v & 2:
                out[p + 1] |= bit
    return bytes(out), total


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v56 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V56.ips').read_bytes())
    assert sha(v56) == V56_SHA, 'La ROM V56 reconstruite ne correspond pas'
    rom = bytearray(v56)
    entries = json.loads((ROOT / 'traduction/noms_objets_lot51_fr.json').read_text(encoding='utf-8'))
    report = []
    for e in entries:
        off = int(e['offset'], 16)
        assert v56[off:off + 128] == source[off:off + 128], e
        icon = icon_of(pixels(source, off)) if e['icon'] else None
        new, px = render(source, e['french'], icon)
        assert px <= W
        rom[off:off + 128] = new
        report.append({'index': e['index'], 'offset': e['offset'], 'english': e['english'],
                       'french': e['french'], 'pixels': px})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V57.ips').write_bytes(ips)
    summary = {
        'version': 'V57', 'base': 'V56', 'object_name_strips': len(report),
        'max_pixels': max(r['pixels'] for r in report), 'width_limit': W,
        'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True,
        'runtime_validation': 'captures Snes9x : verification/boutique_v57.png, equip_v57.png',
    }
    (ROOT / 'verification/build_report_v57.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
