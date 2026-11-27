"""Translate the four compressed SPC7110 scroll badges in the Japanese IPS."""
import argparse
from pathlib import Path

from build_v76 import JP_SHA256, sha
from make_ips_from_jp import apply_ips_any, build_ips
from menu_graphics_lot49 import glyph
from spc7110 import decode_mode2, encode_mode2

ROOT = Path(__file__).resolve().parents[1]
START, END = 0x3A9FD2, 0x3AA293
ART_SHA = '53a7e2ae890636cd8af75d1ef9e71423eb239204fa6295383ede9a27fba26e16'
BADGES = (
    ('Feu', 17, 33, 9, 17, 15),
    ('Eau', 14, 33, 11, 17, 15),
    ('Vent', 16, 33, 11, 17, 15),
    ('Foudre', 16, 32, 11, 17, 15),
)


def patch_badges(rom):
    original = decode_mode2(rom, START, 60 * 32)
    if sha(original) != ART_SHA:
        raise ValueError('Unexpected scroll graphics')
    tiles = bytearray(original)
    for badge, (word, left, right, top, bottom, background) in enumerate(BADGES):
        def address(x, y):
            return (badge * 15 + y // 8 * 5 + x // 8) * 32 + 2 * (y % 8), 128 >> (x % 8)

        def read(x, y):
            pos, bit = address(x, y)
            return sum(bool(original[pos + plane // 2 * 16 + plane % 2] & bit) << plane
                       for plane in range(4))

        def write(x, y, color):
            pos, bit = address(x, y)
            for plane in range(4):
                at = pos + plane // 2 * 16 + plane % 2
                tiles[at] = (tiles[at] & ~bit) | (bit if color & (1 << plane) else 0)

        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                if read(x, y) in (0, 13):
                    write(x, y, background)
        letters = [glyph(rom, ch) for ch in word]
        gap = 1
        if word == 'Foudre':
            # A compact 3x5 alphabet leaves room for a solid field behind the
            # transparent lettering, clear of the lightning at the edges.
            compact = ('111100110100100', '000000111101111',
                       '000000101101111', '001001111101111',
                       '000000110101100', '000111111100111')
            letters = [[[int(pixel) for pixel in g[i:i + 3]]
                        for i in range(0, 15, 3)] for g in compact]
            for y in range(10, 18):
                for x in range(12 if 10 < y < 17 else 14, 36 if 10 < y < 17 else 34):
                    write(x, y, 15)
        width = sum(len(letter[0]) for letter in letters) + gap * (len(letters) - 1)
        assert width <= 28
        x = 10 + (28 - width) // 2
        for letter in letters:
            for y, row in enumerate(letter):
                for dx, ink in enumerate(row):
                    if ink:
                        write(x + dx, y + (11 if word == 'Foudre' else 9), 0)
            x += len(letter[0]) + gap

    encoded = encode_mode2(tiles)
    if len(encoded) > END - START:
        raise ValueError('Translated graphics exceed the original compressed slot')
    out = bytearray(rom)
    out[START:START + len(encoded)] = encoded
    assert decode_mode2(out, START, len(tiles)) == tiles
    return out, len(encoded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('japanese_rom', type=Path)
    parser.add_argument('--ips-out', type=Path, required=True)
    parser.add_argument('--rom-out', type=Path)
    args = parser.parse_args()
    source = args.japanese_rom.read_bytes()
    if sha(source) != JP_SHA256:
        parser.error('Expected the original Japanese ROM without a copier header')
    base_path = ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V77.ips'
    target, size = patch_badges(apply_ips_any(source, base_path.read_bytes()))
    checksum = sum(target) & 0xffff
    target[0xffdc:0xffe0] = (checksum ^ 0xffff).to_bytes(2, 'little') + checksum.to_bytes(2, 'little')
    ips = build_ips(source, target)
    assert apply_ips_any(source, ips) == target
    args.ips_out.write_bytes(ips)
    if args.rom_out:
        args.rom_out.write_bytes(target)
    print(f'{size}/{END - START} compressed bytes, IPS SHA-256 {sha(ips)}')


if __name__ == '__main__':
    main()
