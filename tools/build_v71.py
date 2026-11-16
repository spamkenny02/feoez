#!/usr/bin/env python3
"""Build V71 = V70 IPS + lot 65 : recentrage de « Almanach » dans la barre de selection du menu principal.

La bande « Almanach » (0x6f0f90, 6 tuiles) est placee une tuile a gauche des autres libelles de la 2e colonne ;
le texte commençait 4 px avant la barre bleue de selection. On le decale de 7 px vers la droite (largeur du
texte 38 px, bande de 48 px) pour le centrer dans la barre.
"""
import argparse, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from menu_graphics_lot49 import glyph, raster  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V70_SHA = '54d86dbccff7000df7da14a595ed4706dd311e9981fc601518c3208d526e45c1'
OFFSET, TILES, TEXT, XOFF = 0x6f0f90, 6, "Almanach", 7


def sha(b):
    return hashlib.sha256(b).hexdigest()


def render(source, text, tiles, xoff):
    gs = [glyph(source, c) for c in text]
    W = tiles * 8
    width = sum(len(g[0]) + 1 for g in gs) - 1
    assert xoff + width + 1 <= W
    body = [[0] * W for _ in range(8)]
    x = xoff
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
    return bytes(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v70 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V70.ips').read_bytes())
    assert sha(v70) == V70_SHA, 'La ROM V70 reconstruite ne correspond pas'
    n = TILES * 16
    assert v70[OFFSET:OFFSET + n] == raster(source, TEXT, TILES)[0], 'bande differente du lot 49'
    assert render(source, TEXT, TILES, 0) == v70[OFFSET:OFFSET + n], 'rendu de reference different'
    rom = bytearray(v70)
    rom[OFFSET:OFFSET + n] = render(source, TEXT, TILES, XOFF)
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V71.ips').write_bytes(ips)
    print({'version': 'V71', 'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True})


if __name__ == '__main__':
    main()
