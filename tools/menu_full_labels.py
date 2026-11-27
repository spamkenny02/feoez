"""Complete menu bitmap labels with the native 8-pixel alphabet and 2bpp palette.

Repack existing atlases/descriptor padding. Two uploads gain one verified spare
tile each; executable hooks, windows and selection logic are left intact.
"""
from menu_graphics_lot49 import glyph


def raster_label(rom, text, tiles, gap=1, space_width=3, max_width=None,
                 allow_shadow_crop=False):
    gs = [glyph(rom, ch) if ch != ' ' else [[0] * space_width for _ in range(8)]
          for ch in text]
    gaps = [gap] * (len(gs) - 1)
    limit = min(tiles * 8, max_width or tiles * 8)
    # Remove the least visually connected letter gaps first; retain all body
    # pixels and leave word spaces intact. No horizontal bitmap rescaling.
    pairs = sorted(range(len(gaps)), key=lambda i: (
        text[i] == ' ' or text[i + 1] == ' ',
        sum(gs[i][y][-1] and gs[i + 1][y][0] for y in range(8)), i))
    body_width = sum(len(g[0]) for g in gs) + sum(gaps)
    for i in pairs:
        if body_width + 1 <= limit:
            break
        body_width -= gaps[i]
        gaps[i] = 0
    crop = body_width + 1 > limit
    if body_width > limit or crop and not allow_shadow_crop:
        raise ValueError(f'{text!r}: body {body_width}px, limit {limit}px')
    width = tiles * 8
    body = [[0] * width for _ in range(8)]
    x = 0
    for i, g in enumerate(gs):
        for y in range(8):
            body[y][x:x + len(g[y])] = g[y]
        x += len(g[0]) + (gaps[i] if i < len(gaps) else 0)
    out = bytearray(tiles * 16)
    for x in range(width):
        for y in range(8):
            value = 2 if body[y][x] else 1 if x and body[y][x - 1] else 0
            at = (x // 8) * 16 + y * 2
            bit = 128 >> (x % 8)
            if value & 1:
                out[at] |= bit
            if value & 2:
                out[at + 1] |= bit
    return bytes(out), {'text': text, 'tiles': tiles, 'body_pixels': body_width,
                        'pixels_with_shadow': body_width + 1, 'limit_pixels': limit,
                        'letter_gaps': gaps, 'space_pixels': space_width,
                        'rightmost_shadow_cropped': crop}


def patch_menu_labels(rom):
    out = bytearray(rom)
    spans, entries, data_edits = [], [], []

    def write(start, data):
        end = start + len(data)
        if any(start < z and a < end for a, z in spans):
            raise ValueError(f'Overlapping menu writes at {start:#x}')
        spans.append((start, end))
        out[start:end] = data

    def replace(start, old, new, purpose):
        if len(old) != len(new) or rom[start:start + len(old)] != old:
            raise ValueError(f'Unexpected V76 data at {start:#x}: {purpose}')
        write(start, new)
        data_edits.append({'offset': hex(start), 'before': old.hex(),
                           'after': new.hex(), 'purpose': purpose})

    def place(text, parts, **kwargs):
        data, entry = raster_label(rom, text, sum(n for _, n in parts), **kwargs)
        cursor = 0
        for start, n in parts:
            write(start, data[cursor:cursor + n * 16])
            cursor += n * 16
        entry['rom_tiles'] = [hex(start + i * 16) for start, n in parts for i in range(n)]
        entries.append(entry)

    # Keep the actor's Rank/Health/Technique resources at their old addresses.
    main = [('Parchemins', 6), ('Stratégie', 5), ('Inventaire', 6),
            ('Réglages', 5), ('Équipement', 6), ('Almanach', 5), ('État', 3),
            ('Horloge', 4), ('Date/heure', 7), ('Temps de jeu', 7), ('Argent', 4)]
    locations, at = {}, 0x6F0E00
    for text, n in main:
        options = {'space_width': 2} if text == 'Temps de jeu' else {}
        if text in ('Parchemins', 'Équipement'):
            options['max_width'] = 45  # separates columns and fits the highlight
        place(text, [(at, n)], **options)
        locations[text] = ((at - 0x6F0E00) // 16 + 0x140, n)
        at += n * 16
    assert at == 0x6F11A0
    stream = bytearray(rom[0xE092:0xE0A2])  # four existing window descriptors

    def row(x, y, parts):
        stream.extend([x, y])
        base = 0
        for part in parts:
            if isinstance(part, int):
                stream.extend([0x20] * part)
                continue
            tile, n = locations[part]
            for t in range(tile, tile + n):
                if t >= 0x170 and not base:
                    stream.append(3)  # native tile-page selector
                    base = 0x20
                code = t - 0xF0 - base
                assert 0x30 <= code < 0x80
                stream.append(code)
        stream.append(0)

    for y, parts in ((3, ['Parchemins', 'Stratégie']), (5, ['Inventaire', 'Réglages']),
                     (7, ['Équipement', 'Almanach']), (9, ['État', 3, 'Horloge'])):
        row(2, y, parts)
    stream.extend(rom[0xE0D8:0xE0F1])  # native weekday/time and date fields
    row(2, 12, ['Date/heure'])
    row(2, 18, ['Temps de jeu'])
    stream.extend(rom[0xE104:0xE10A])  # playtime value position
    row(2, 23, ['Argent'])
    stream.append(0xFF)
    assert len(stream) == 0xE116 - 0xE092
    replace(0xE092, rom[0xE092:0xE116], stream, 'Main menu atlas tile references')

    # Scroll actions: reuse the padding token after Use. Modifier's last tile
    # goes into one spare tile immediately after the original DMA resource.
    assert not any(rom[0x6F23A0:0x6F23B0])
    place('Utiliser', [(0x6F2200, 3)])
    place('Modifier', [(0x6F2230, 3), (0x6F23A0, 1)])
    place('Coût technique', [(0x6F2260, 6)], space_width=1,
          allow_shadow_crop=True)
    for old, new, purpose in (
        ('01035051df00', '010350515200', 'Scroll Use full label'),
        ('01055253545500', '01055354556a00', 'Scroll Modifier fourth tile'),
    ):
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        start = rom.find(old, 0xE16A, 0xE1A1)
        assert start >= 0
        replace(start, old, new, purpose)
    replace(0x6F23CF, bytes.fromhex('a003'), bytes.fromhex('b003'),
            'Scroll graphics upload: add one spare tile')

    # Inventory action spacing already reserves six columns per action.
    # Jeter frees a tile for Trier; Remplacer uses one verified DMA tail tile.
    assert not any(rom[0x6F34D0:0x6F34E0])
    place('Utiliser', [(0x6F3240, 3)])
    place('Trier', [(0x6F3270, 2), (0x6F3300, 1)])
    place('Remplacer', [(0x6F3290, 4), (0x6F34D0, 1)])
    place('Jeter', [(0x6F32D0, 3)])
    old = bytes.fromhex('0503545520202020565758202020595a5b5c20205d5e5f6000')
    new = bytes.fromhex('0503545556202020575860202020595a5b5c7d205d5e5f2000')
    start = rom.find(old, 0xE1E0, 0xE230)
    assert start >= 0
    replace(start, old, new, 'Inventory actions full labels and padding')
    for start in (0x6D800F, 0x6F2E15, 0x6F3F4F):
        replace(start, bytes.fromhex('d004'), bytes.fromhex('e004'),
                'Inventory graphics upload: add one spare tile')
    place('Objets', [(0x6F33B0, 3)])

    # Settings: grow Music into Stereo's first tile, tighten Stereo, and put
    # the cursor-memory tail in two columns no longer used by the Fond bitmap.
    place('Vitesse du texte', [(0x6F1860, 8)], space_width=2)
    place('Vitesse de marche', [(0x6F1990, 8)], space_width=2)
    place('Musique', [(0x6F1A50, 4)])
    place('Stéréo', [(0x6F1A90, 3)])
    place('Mémoire du curseur', [(0x6F1AF0, 8), (0x6F1BE0, 1)], space_width=2)
    place('Fond', [(0x6F1BB0, 3)])
    place('Forme du cadre', [(0x6F1C00, 7)], space_width=2)
    place('Couleur du cadre', [(0x6F1C70, 7)], space_width=1)
    old = rom[0x36327:0x36340]
    assert old == bytes.fromhex('040f555657202020202020202020202058595a5b205c5d5e00')
    new = bytes.fromhex('040f55565758') + bytes([0x20]) * 10 + bytes.fromhex('595a5b20205c5d5e00')
    replace(0x36327, old, new, 'Music and Stereo tile references')
    replace(0x36342, bytes.fromhex('5f6061626364656620'),
            bytes.fromhex('5f606162636465666e'), 'Cursor memory extra tile uses padding')
    replace(0x3635A, bytes.fromhex('6b6c6d6e6f'), bytes.fromhex('6b6c6d2020'),
            'Fond tail tile reused for cursor memory')

    # Status/equipment retain every original slot and menu window.
    for start in (0x6F3700, 0x6F4200):
        place('Attaque', [(start, 4)])
    for start in (0x6F37D0, 0x6F42D0):
        place('Chance', [(start, 3)], allow_shadow_crop=True)
    place('rang suivant', [(0x6F3890, 6)])
    place('Équipement', [(0x6F4300, 6)])
    place('Automatique', [(0x6F4360, 6)])
    place('Sans équipement', [(0x6F4400, 7)], space_width=2)
    # The status heading is native text rather than a bitmap strip. Its leading
    # padding space provides the extra byte required by the complete word.
    from french_font import encode_fr
    old = encode_fr(' Équip.').ljust(10, b' ')
    replace(0xEF92, old, encode_fr('Équipement'), 'Status equipment heading')
    return bytes(out), {'entries': entries, 'data_edits': data_edits,
                        'spans': [[hex(a), hex(z)] for a, z in spans],
                        'scope': 'Native 8px bitmap labels; no glyph body pixels clipped or rescaled.'}
