#!/usr/bin/env python3
"""Build V70 = V69 IPS + lot 64 : mot « Failed » du combat (sprites compresses SPC7110).

Le flux de mode 2 a 0x51e200 decompresse 29 tuiles : chiffres 0 a 9 (tuiles paires 0 a 18) puis « Failed »
(tuiles 20 a 25, 24x10 pixels : rangees 0 a 7 dans les tuiles paires 20/22/24, rangees 8 et 9 dans les tuiles
impaires 21/23/25). Le mot francais « Rate » (avec accent) est dessine dans le meme style (corps blanc,
contour sombre calcule sur les 8 voisins), les autres tuiles sont conservees, le flux est recompresse avec
tools/spc7110.py et releve avec le decodeur. Taille controlee : le flux suivant commence 200 octets plus loin.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
import spc7110  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V69_SHA = '1a7cb12d38b3c6b516ad29d75228808e6e2acfe0eadb4a90a6adf09e86b14c04'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def body_mask(t):
    H, W = 10, 24
    body = [[0] * W for _ in range(H)]
    gl = t['glyphs']

    def put(rows, x, ybottom):
        y0 = ybottom - len(rows) + 1
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                if c == '#':
                    body[y0 + j][x + i] = 1
        return len(rows[0])

    x = t['x0']
    word = t['french']
    letters = [c for c in word.replace('é', 'e')]
    xe = None
    for k, ch in enumerate(letters):
        if ch == 'e':
            xe = x
        x += put(gl[ch], x, 8) + (t['gaps'][k] if k < len(t['gaps']) else 0)
    # accent aigu (le seul accent du mot) : pixels (rangee, colonne relative au e)
    for dy, dx in t['accent']['pixels']:
        body[dy][xe + dx] = 1
    return body


def render(body):
    H, W = 10, 24
    b = lambda x, y: body[y][x] if 0 <= x < W and 0 <= y < H else 0
    img = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if b(x, y):
                img[y][x] = 15
            elif any(b(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
                img[y][x] = 1
    return img


def pack(px8):
    raw = bytearray(32)
    for y in range(8):
        p = [0, 0, 0, 0]
        for x in range(8):
            v = px8[y][x]
            for k in range(4):
                p[k] |= ((v >> k) & 1) << (7 - x)
        raw[y * 2] = p[0]; raw[y * 2 + 1] = p[1]; raw[16 + y * 2] = p[2]; raw[16 + y * 2 + 1] = p[3]
    return bytes(raw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v69 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V69.ips').read_bytes())
    assert sha(v69) == V69_SHA, 'La ROM V69 reconstruite ne correspond pas'
    t = json.loads((ROOT / 'traduction/failed_combat_lot64_fr.json').read_text(encoding='utf-8'))
    off, n = int(t['stream'], 16), t['tiles']
    old = spc7110.decode_mode2(v69, off, n * 32)
    assert sha(old) == t['old_stream_tiles_sha256'], 'flux d\'origine inattendu'
    img = render(body_mask(t))
    new = bytearray(old)
    for j in range(3):
        top = [[img[y][j * 8 + x] for x in range(8)] for y in range(8)]
        bot = [[img[8 + y][j * 8 + x] for x in range(8)] if y < 2 else [0] * 8 for y in range(8)]
        new[(20 + 2 * j) * 32:(21 + 2 * j) * 32] = pack(top)
        new[(21 + 2 * j) * 32:(22 + 2 * j) * 32] = pack(bot)
    enc = spc7110.encode_mode2(bytes(new))
    assert len(enc) <= t['max_stream_bytes'], len(enc)
    rom = bytearray(v69)
    rom[off:off + len(enc)] = enc
    assert spc7110.decode_mode2(bytes(rom), off, n * 32) == bytes(new), 'relecture KO'
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V70.ips').write_bytes(ips)
    summary = {'version': 'V70', 'base': 'V69', 'stream': t['stream'], 'compressed_bytes': len(enc),
               'max_stream_bytes': t['max_stream_bytes'], 'ips_sha256': sha(ips), 'rom_sha256': sha(out),
               'ips_roundtrip': True, 'runtime_validation': 'tuiles relues dans la VRAM d\'un combat (voir COMPTE_RENDU_V70.md)'}
    (ROOT / 'verification/build_report_v70.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
