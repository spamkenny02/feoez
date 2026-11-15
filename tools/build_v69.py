#!/usr/bin/env python3
"""Build V69 = V68 IPS + lot 63 : etiquettes de la roue de commandes du combat (sprites compresses SPC7110).

Chaque etiquette (Attack, Skills, Items, Scrolls) est faite de deux sprites 16x16 de 4 tuiles, stockes comme
deux flux SPC7110 de mode 2 (4 bits) de 128 octets decompresses, dans des emplacements de 0x80 octets
(0x505d00, 0x505d80, 0x505f00, 0x505f80, 0x506000, 0x506080, 0x506100, 0x506180). Le build :
 1. verifie que les flux d'origine se decompressent aux donnees attendues (SHA-256 dans la table) ;
 2. dessine le mot francais avec les lettres de la table (corps ; ombre portee et reflets calcules, regles
    retrouvees sur les etiquettes d'origine) sur le motif de fond de la plaque ;
 3. compresse chaque sprite avec tools/spc7110.py (encodeur miroir du decodeur) et l'ecrit dans son emplacement ;
 4. relit chaque flux avec le decodeur et verifie l'identite avec les tuiles voulues, taille <= emplacement.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
import spc7110  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V68_SHA = 'e57fe585068bb1c66cd930ec8f4a26609bd87531437e03e8b3d3ef2440366f12'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def word_body(glyphs, word, gap=1):
    gl = {c: {int(y): r for y, r in g.items()} for c, g in glyphs.items()}
    width = lambda g: max(len(r) for r in g.values())
    x = 0; placed = []
    for ch in word:
        w = width(gl[ch]); placed.append((ch, x, w)); x += w + gap
    total = x - gap
    off = (31 - total) // 2
    body = [[0] * 32 for _ in range(16)]
    for ch, px, w in placed:
        for y, r in gl[ch].items():
            for i, c in enumerate(r):
                if c == '#':
                    body[y][off + px + i] = 1
    return body


def render(body, bg):
    H, W = 16, 32
    b = lambda x, y: body[y][x] if 0 <= x < W and 0 <= y < H else 0
    img = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if b(x, y):
                img[y][x] = 3 if (not b(x, y - 1)) or (not b(x, y + 1)) else 2
            elif b(x - 1, y) or b(x, y - 1) or b(x - 1, y - 1):
                img[y][x] = 1          # ombre portee (regle exacte sur les lettres d'origine, 2 ecarts sur 1254)
            else:
                img[y][x] = bg[x % 16]
    return img


def pack_tile(img, x0, y0):
    raw = bytearray(32)
    for y in range(8):
        p = [0, 0, 0, 0]
        for x in range(8):
            v = img[y0 + y][x0 + x]
            for k in range(4):
                p[k] |= ((v >> k) & 1) << (7 - x)
        raw[y * 2] = p[0]; raw[y * 2 + 1] = p[1]; raw[16 + y * 2] = p[2]; raw[16 + y * 2 + 1] = p[3]
    return bytes(raw)


def sprite_data(img, xo):
    # ordre du flux : haut-gauche, bas-gauche, haut-droite, bas-droite
    return b''.join(pack_tile(img, xo + dx, dy) for dx, dy in ((0, 0), (0, 8), (8, 0), (8, 8)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v68 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V68.ips').read_bytes())
    assert sha(v68) == V68_SHA, 'La ROM V68 reconstruite ne correspond pas'
    table = json.loads((ROOT / 'traduction/etiquettes_combat_lot63_fr.json').read_text(encoding='utf-8'))
    bg = [int(c, 16) for c in table['background']]
    slot = table['slot_bytes']
    rom = bytearray(v68); report = []
    for t in table['tags']:
        l, r = int(t['left_stream'], 16), int(t['right_stream'], 16)
        old = spc7110.decode_mode2(v68, l, 128) + spc7110.decode_mode2(v68, r, 128)
        assert sha(old) == t['old_tiles_sha256'], ('flux d\'origine inattendu', t['english'])
        img = render(word_body(table['glyphs'], t['french']), bg)
        for off, xo in ((l, 0), (r, 16)):
            data = sprite_data(img, xo)
            enc = spc7110.encode_mode2(data)
            assert len(enc) <= slot, (t['french'], len(enc))
            rom[off:off + len(enc)] = enc
            assert spc7110.decode_mode2(bytes(rom), off, 128) == data, ('relecture KO', t['french'], hex(off))
            report.append({'english': t['english'], 'french': t['french'], 'stream': hex(off),
                           'compressed_bytes': len(enc), 'slot_bytes': slot, 'old_stream_bytes': None})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V69.ips').write_bytes(ips)
    summary = {'version': 'V69', 'base': 'V68', 'streams': len(report), 'max_compressed_bytes': max(x['compressed_bytes'] for x in report),
               'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True,
               'runtime_validation': 'tuiles relues avec le decodeur ; rendu charge en VRAM dans verification/combat_roue_v69.png'}
    (ROOT / 'verification/build_report_v69.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
