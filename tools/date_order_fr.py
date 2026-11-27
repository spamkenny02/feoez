"""French numeric dates; preserve the game's year/month/day storage and RTC API."""
from french_font import encode_fr


def patch_date_order(rom):
    out = bytearray(rom)
    edits = []

    def replace(offset, old, new, purpose):
        if len(old) != len(new) or rom[offset:offset + len(old)] != old:
            raise ValueError(f'Unexpected V75 date data at {offset:#x}: {purpose}')
        out[offset:offset + len(new)] = new
        edits.append({'offset': hex(offset), 'before': old.hex(),
                      'after': new.hex(), 'purpose': purpose})

    # Rendering loops over internal fields year, month, day, hour, minute.
    # Move day to the left and month to the middle without moving stored data.
    replace(0xEB91, bytes.fromhex('09 01 04 0c 0f'),
            bytes.fromhex('09 04 01 0c 0f'), 'Birthday and clock render positions')
    # Editing loops over screen positions. The original wrapper maps these
    # positions to internal fields and then uses their own native min/max bounds.
    replace(0x6D25F0, bytes([1, 2, 0, 3, 4]), bytes([2, 1, 0, 3, 4]),
            'Edit day, month, year, hour, minute')
    # Existing Almanac formatter rearranges YYYY-MM-DD into MM-DD-YYYY.
    # Swap its month/day source words, leaving its year and weekday handling alone.
    replace(0x6F1783, bytes.fromhex('ad 35 1d'), bytes.fromhex('ad 38 1d'),
            'Almanac: day first')
    replace(0x6F1789, bytes.fromhex('ad 38 1d'), bytes.fromhex('ad 35 1d'),
            'Almanac: month second')
    # V72 repurposed native digits D4 (1) and D9 (6) as blank heart spacers.
    # Remap only the ten date bytes to the equivalent normal-font digits.
    # Extend the existing wrapper into verified zero padding, preserving A/X/P.
    remap = bytes.fromhex('08 48 da a2 09 bd 30 1d c9 d4 d0 04 a9 2f 80 06 '
                          'c9 d9 d0 05 a9 25 9d 30 1d ca 10 e9 fa 68 28 6b')
    replace(0x6F17A1, b'\x6b' + bytes(len(remap) - 1), remap,
            'Almanac: render digits 1 and 6 without changing heart spacer glyphs')
    for offset, old, new in (
        (0xF1D4, 'Date de naissance (mois-jour-an)', 'Date de naissance (jour-mois-an)'),
        (0x6D2536, '(Mois, jour, année ; heure AM/PM)', '(Jour, mois, année ; heure AM/PM)'),
    ):
        def menu_text(text):
            return encode_fr(text.replace('(', '<17>').replace(')', '<18>').replace('/', '<1E>'))
        replace(offset, menu_text(old), menu_text(new), 'Date order instructions')
    return bytes(out), edits
