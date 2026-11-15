#!/usr/bin/env python3
"""Build V67 = V66 IPS + lot 61 : sous-menus de combat (Arts secrets et Parchemins).

Les panneaux de gauche des sous-menus de combat sont dessines avec deux bandes de tuiles :
0x6f2500 (51 tuiles, Arts secrets) et 0x6f2a00 (57 tuiles, Parchemins), chargees en VRAM 0x7200. Plages de
tuiles lues dans la carte de tuiles (0xb000, n0 = 288) : Skill = 36-37, Health = 38-41, Used = 29-31
(Arts secrets) ; Scrolls = 44-47, Tech = 38-40, Used = 41-43 (Parchemins).
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from menu_graphics_lot49 import glyph  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V66_SHA = '1cff566ad3867c629e976438731b466a77c5b8817812903ccb0f7b3e72a916ed'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pixels(rom, off, tiles):
    W = tiles * 8
    px = [[0] * W for _ in range(8)]
    for t in range(tiles):
        raw = rom[off + t * 16: off + t * 16 + 16]
        for y in range(8):
            for x in range(8):
                b = 7 - x
                px[y][t * 8 + x] = ((raw[y * 2] >> b) & 1) | (((raw[y * 2 + 1] >> b) & 1) << 1)
    return px


def icon_of(px):
    """Dernier groupe de colonnes portant du corps (valeur 2/3), ombre comprise."""
    W = len(px[0])
    on = [any(px[y][x] & 2 for y in range(8)) for x in range(W)]
    x1 = max(x for x in range(W) if on[x])
    x0 = x1
    while x0 > 0 and on[x0 - 1]:
        x0 -= 1
    return [row[x0:min(W, x1 + 2)] for row in px]


def render(source, text, tiles, align, limit, icon):
    text = text.replace('’', "'").replace('œ', 'oe').replace('Œ', 'OE')
    gs = [glyph(source, c) for c in text]
    width = sum(len(g[0]) + 1 for g in gs) - 1
    W = tiles * 8
    total = width + 1
    x = 0
    if align == 'right':
        x = min(limit, W) - width - 1
    body = [[0] * W for _ in range(8)]
    for g in gs:
        for y in range(8):
            body[y][x:x + len(g[y])] = g[y]
        x += len(g[0]) + 1
    val = [[2 if body[y][xx] else 1 if xx and body[y][xx - 1] else 0 for xx in range(W)] for y in range(8)]
    if icon is not None:
        ix = width + 3
        for y in range(8):
            for k, v in enumerate(icon[y]):
                val[y][ix + k] = v
        total = ix + len(icon[0])
    assert total <= min(limit, W), (text, total, limit)
    out = bytearray(tiles * 16)
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
    v66 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V66.ips').read_bytes())
    assert sha(v66) == V66_SHA, 'La ROM V66 reconstruite ne correspond pas'
    rom = bytearray(v66)
    entries = json.loads((ROOT / 'traduction/combat_sous_menus_lot61_fr.json').read_text(encoding='utf-8'))
    report, spans = [], []
    for e in entries:
        off, n = int(e['offset'], 16), e['tiles'] * 16
        assert v66[off:off + n] == source[off:off + n], e
        assert not any(off < z and off + n > s for s, z in spans), e
        spans.append((off, off + n))
        icon = icon_of(pixels(source, off, e['tiles'])) if e['icon'] else None
        new, px = render(source, e['french'], e['tiles'], e['align'], e['limit_px'], icon)
        rom[off:off + n] = new
        report.append({'offset': e['offset'], 'english': e['english'], 'french': e['french'],
                       'pixels': px, 'limit_px': e['limit_px'], 'screen': e['screen']})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V67.ips').write_bytes(ips)
    summary = {'version': 'V67', 'base': 'V66', 'strips': len(report), 'ips_sha256': sha(ips),
               'rom_sha256': sha(out), 'ips_roundtrip': True,
               'runtime_validation': 'captures Snes9x : verification/combat_v67_*.png'}
    (ROOT / 'verification/build_report_v67.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
