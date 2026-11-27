#!/usr/bin/env python3
"""Execute V76's native date rendering and editing wrappers on calendar cases."""
import argparse
import calendar
import json
from pathlib import Path

from build_v76 import build, sha
from numeric65816_probe import NumericCPU


class AtFont(Exception):
    pass


class DateCPU(NumericCPU):
    allowed_ranges = ((0xC0BD69, 0xC0BDDB), (0xC0BE31, 0xC0BE3E),
                      (0x4D25E0, 0x4D25EC), (0x4D2680, 0x4D26A7),
                      (0x4F177B, 0x4F17C1), (0xC17702, 0xC17703))

    def mapped(self, address):
        if address >> 16 in (0, 0x80) and address & 0xFFFF >= 0x8000:
            return address & 0xFFFF
        return super().mapped(address)

    def fetch(self, n=1):
        if self.PC == 0xC17702:
            raise AtFont()
        return super().fetch(n)


def display(rom, year, month, day, hour=12, minute=0):
    cpu = DateCPU(rom)
    cpu.ram[0x1E39:0x1E3E] = bytes([year - 1900, month, day, hour, minute])
    try:
        cpu.run(0xC0BD69)
    except AtFont:
        pass
    else:
        raise AssertionError('Native renderer did not reach its font call')
    result = bytes(cpu.ram[0x1D30:0x1D48])
    numeric = lambda value: bytes(0xE1 + int(digit) for digit in f'{value:02}')
    assert result[1:3] == numeric(day)
    assert result[4:6] == numeric(month)
    assert result[7:11] == numeric(year // 100) + numeric(year % 100)
    assert result[12:14] == numeric((hour % 12) or 12)
    assert result[15:17] == numeric(minute)
    assert result[18] == (0x30 if hour < 12 else 0x3F)
    assert result[23] == 0
    assert cpu.ram[0x1E39:0x1E3E] == bytes([year - 1900, month, day, hour, minute])


def verify(rom):
    # The replacement digits have exactly the widths of the native date digits.
    for old, new in ((0xD4, 0x2F), (0xD9, 0x25)):
        assert rom[0x2F7200 + old] == rom[0x2F7200 + new]
    rendered = 0
    for year in (1995, 1996, 2000, 2001, 2099):
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                display(rom, year, month, day)
                rendered += 1
    for hour in range(24):
        for minute in range(60):
            display(rom, 2000, 2, 29, hour, minute)
            rendered += 1
    edits = 0
    # Actual editing wrapper: display cursor -> native field -> arithmetic.
    for position, field in enumerate((2, 1, 0, 3, 4)):
        for value in range(256):
            for delta in (1, 255, 10, 246):
                cpu = DateCPU(rom)
                cpu.X = position
                cpu.ram[0x1E39:0x1E3E] = bytes([95, 12, 22, 12, 30])
                cpu.ram[0x1E39 + field] = value
                before = bytes(cpu.ram[0x1E39:0x1E3E])
                result = cpu.run(0x4D25E0, delta)
                assert cpu.X == field and result == (value + delta) & 255
                assert bytes(cpu.ram[0x1E39:0x1E3E]) == before
                assert cpu.S == 0x1FF
                edits += 1
    # Execute the existing Almanac word rearrangement, including its stack work.
    for year in (1995, 2000, 2099):
        for month in range(1, 13):
            day = calendar.monthrange(year, month)[1]
            cpu = DateCPU(rom)
            cpu.P = 0x10  # 16-bit accumulator, 8-bit indexes at this routine entry.
            digits = lambda value: bytes(0xD3 + int(d) for d in f'{value:02}')
            cpu.ram[0x1D30:0x1D3A] = digits(year // 100) + digits(year % 100) + b'\x1C' + digits(month) + b'\x1C' + digits(day)
            cpu.run(0x4F177B)
            expected = digits(day) + b'\x1C' + digits(month) + b'\x1C' + digits(year // 100) + digits(year % 100)
            assert cpu.ram[0x1D30:0x1D3A] == expected.replace(b'\xD4', b'\x2F').replace(b'\xD9', b'\x25')
            assert cpu.S == 0x1FF and cpu.X == 0 and cpu.P == 0x30 and cpu.A & 255 == 0x1C
    return {'native_input_display_cases': rendered, 'native_edit_wrapper_cases': edits,
            'native_almanac_reorder_cases': 36,
            'date_storage_preserved': True,
            'scope': 'Actual 65816 date formatter and wrappers; no PPU, RTC or full event simulation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('japanese_rom', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rom, _, _ = build(args.japanese_rom.read_bytes())
    report = {'rom_sha256': sha(rom), **verify(rom)}
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
