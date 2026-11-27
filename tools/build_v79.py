"""V79: rename the battle reward and matching status statistic."""
from pathlib import Path
import argparse

from build_v76 import JP_SHA256, sha
from build_v69 import pack_tile
from cpu65816_probe import CPU
from french_font import encode_fr, visible_width
from make_ips_from_jp import apply_ips_any, build_ips
from menu_full_labels import raster_label

ROOT = Path(__file__).resolve().parents[1]
XP_FONT = (
    '111 100 110 100 111', '000 101 010 010 101',
    '000 110 101 110 100 100', '001 010 111 110 100 111',
    '000 110 101 100 100', '1 0 1 1 1',
    '000 000 111 110 100 111', '000 110 101 101 101',
    '000 111 100 100 111', '000 000 111 110 100 111',
)


def status_label():
    # 31 body columns including spacing, plus one shadow column.
    image = [[0] * 32 for _ in range(8)]
    x = 0
    for index, shape in enumerate(XP_FONT):
        rows = shape.split()
        top = 1 if index == 3 else 7 - len(rows)
        for y, row in enumerate(rows, top):
            for dx, pixel in enumerate(row):
                if pixel == '1':
                    image[y][x + dx] = 2
        x += len(rows[0]) + (index not in (1, 2, 4, 5, 6, 8, 9))
    assert x <= 31
    for row in image:
        for x in range(31, 0, -1):
            if row[x] == 0 and row[x - 1] == 2:
                row[x] = 1
    return b''.join(pack_tile(image, x, 0)[:16] for x in range(0, 32, 8))


def patch(rom):
    out = bytearray(rom)
    start, padding_end = 0x622141, 0x622190
    old = encode_fr('Vertu gagnée : <04>.') + b'\0'
    new = encode_fr('Expérience gagnée : <04>.') + b'\0'
    assert rom[start:start + len(old)] == old
    delta = len(new) - len(old)
    assert rom[padding_end - delta:padding_end] == bytes(delta)
    out[start:padding_end] = new + rom[start + len(old):padding_end - delta]
    out[0x6f3800:0x6f3840] = status_label()
    # Both status rows use the first three tiles, but the requirement row
    # skips tile 63, which is now the final tile of Expérience.
    at = 0xef50
    assert rom[at:at + 8] == bytes.fromhex('6061626465666768')
    out[at:at + 8] = bytes.fromhex('6061626364656667')
    tail, _ = raster_label(rom, ' requise', 4, space_width=2)
    out[0x6f3840:0x6f3880] = tail
    checksum = sum(out) & 0xffff
    out[0xffdc:0xffe0] = (checksum ^ 0xffff).to_bytes(2, 'little') + checksum.to_bytes(2, 'little')
    for i in range(1, 9):
        before, after = CPU(rom), CPU(out)
        for cpu in (before, after):
            cpu.load_block(43)
            cpu.select(i)
        assert after.string() == (new[:-1] if i == 2 else before.string())
    assert visible_width('Expérience gagnée : <04>.', out, {4: 64}) <= 216
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('japanese_rom', type=Path)
    parser.add_argument('--ips-out', type=Path, required=True)
    parser.add_argument('--rom-out', type=Path)
    args = parser.parse_args()
    source = args.japanese_rom.read_bytes()
    if sha(source) != JP_SHA256:
        parser.error('Expected the original Japanese ROM')
    base = (ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V78.ips').read_bytes()
    assert sha(base) == 'd1d6e59e250498491437848d4656fc51163e59b8c8e657ec582758c9e976f605'
    target = patch(apply_ips_any(source, base))
    ips = build_ips(source, target)
    assert apply_ips_any(source, ips) == target
    args.ips_out.write_bytes(ips)
    if args.rom_out:
        args.rom_out.write_bytes(target)
    print(sha(ips))


if __name__ == '__main__':
    main()
