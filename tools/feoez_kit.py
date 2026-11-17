#!/usr/bin/env python3
"""feoez_kit : boîte à outils pour (re)traduire Far East of Eden Zero depuis la ROM ANGLAISE d'origine.

ROM attendue : SHA-256 eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e (7 340 032 octets).

Commandes (python3 tools/feoez_kit.py <commande> -h pour le détail) :

  texts    ROM [--fr-ips X.ips] [--out DIR]   exporte TOUS les textes (673 groupes, ~11 000 chaînes) en TSV,
                                              + un TSV par catégorie (objets, techniques, bestiaire, lieux...)
  graphics ROM [--fr-ips X.ips] [--out DIR]   exporte les bandes de tuiles contenant du texte anglais
                                              (menus, noms d'objets, boutiques, étiquettes de combat) en TSV + PNG
  build    ROM --texts T.tsv [--graphics G.tsv] [--base X.ips] --ips-out OUT.ips [--rom-out OUT.sfc]
                                              reconstruit la ROM traduite et écrit l'IPS (relu et vérifié)
  check    ROM --texts T.tsv                  contrôle largeurs (216 px), caractères, codes de contrôle
  tiles    ROM OFFSET [--tiles N] [--bpp 2|4] [--png out.png]     exporte des tuiles brutes en PNG
  tiles-import ROM PNG OFFSET [--bpp 2|4] --ips-out X.ips         réimporte un PNG (4 couleurs / 16 couleurs)
  sheet    ROM START END --png out.png [--bpp 2|4] [--cols 32]    planche de tuiles pour CHERCHER du texte
                                              dessiné dans la ROM (enseignes, décors...)
  spc      ROM OFFSET --bytes N --png out.png                      décompresse un flux SPC7110 mode 2 (4 bpp)
  spc-import ROM PNG OFFSET --bytes N --slot S --ips-out X.ips     recompresse un PNG dans un emplacement de S octets

Principe : la ROM anglaise n'est jamais modifiée ; tout est écrit sous forme d'IPS.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from extract import EXPECTED  # noqa: E402
from pointers import analyze, MASTER, COUNT, FREE_START, FREE_END, cpu_to_file  # noqa: E402
from block_storage import store_blocks  # noqa: E402
from insert import make_ips, apply_ips  # noqa: E402
import french_font as ff  # noqa: E402

TEXT_END = 0x6D0000          # fin de la zone de textes (pool + zone libre de relocalisation)
TEXT_START = 0x600000
LIMIT_PX = 216
CATEGORIES = {1: 'commandes', 2: 'objets', 3: 'objets', 4: 'techniques', 5: 'techniques', 6: 'techniques',
              7: 'techniques', 8: 'objets', 9: 'objets', 10: 'techniques', 11: 'techniques', 12: 'personnages',
              13: 'menus', 14: 'lieux', 15: 'lieux', 16: 'combat', 17: 'calendrier', 18: 'calendrier',
              19: 'techniques', 20: 'bestiaire', 29: 'boutique'}
for _i in range(21, 29):
    CATEGORIES[_i] = 'debug'
EXPORT_CATS = ['objets', 'techniques', 'bestiaire', 'lieux', 'personnages', 'menus', 'combat', 'boutique',
               'commandes', 'calendrier']
TEXT_COLS = ['id', 'cat', 'offset', 'en', 'fr', 'px', 'statut']
GFX_COLS = ['id', 'kind', 'offset', 'tiles', 'align', 'limit_px', 'icon', 'screen', 'en', 'fr', 'fr_ref']

# Catalogues de bandes graphiques 2 bpp déjà identifiées : (fichier, écran par défaut)
STRIP_CATALOGS = [
    ('menu_graphics_lot49_fr', 'menu'), ('menu_graphics_lot50_fr', 'stratégie'),
    ('interface_boutique_lot52_fr', 'boutique'), ('boutique_suite_lot57_fr', 'boutique'),
    ('panneau_personnage_lot53_fr', 'équipement'), ('ecran_sauvegarde_lot54_fr', 'sauvegarde'),
    ('suppression_redemarrage_lot56_fr', 'titre'), ('barre_sauvegarde_lot60_fr', 'sauvegarde'),
    ('combat_sous_menus_lot61_fr', 'combat'), ('nommage_animal_lot62_fr', 'animal'),
]


# --------------------------------------------------------------------------- utilitaires
def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_rom(path):
    rom = Path(path).read_bytes()
    if sha(rom) != EXPECTED:
        sys.exit("ROM inattendue : il faut la ROM anglaise d'origine (SHA-256 %s)" % EXPECTED)
    return rom


def with_ips(rom, ips):
    return apply_ips(rom, Path(ips).read_bytes()) if ips else None


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')


def unesc(s):
    return re.sub(r'\\(.)', lambda m: {'n': '\n', 't': '\t', '\\': '\\'}.get(m[1], m[0]), s)


def read_tsv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write_tsv(path, rows, cols):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter='\t', extrasaction='ignore', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def checksum(data):
    data = bytearray(data)
    v = sum(data) & 65535
    data[0xFFDC:0xFFDE] = (v ^ 65535).to_bytes(2, 'little')
    data[0xFFDE:0xFFE0] = v.to_bytes(2, 'little')
    return bytes(data)


# --------------------------------------------------------------------------- textes : lecture
def split_groups(rom, block):
    """Chaînes (bytes) de chaque groupe d'un bloc du pool principal de la ROM anglaise."""
    end = int(block['end_exclusive'], 16)
    t = [int(x, 16) for x in block['group_targets']] + [end]
    groups = []
    for i in range(len(t) - 1):
        parts = rom[t[i]:t[i + 1]].split(b'\0')
        assert parts[-1] == b'', 'groupe sans terminateur final'
        groups.append(parts[:-1])
    return groups


def main_blocks(rom):
    audit = analyze(rom)
    out = []
    for b in audit['blocks']:
        if not b['main_text_pool']:
            continue
        out.append({'block': b, 'id': b['block_ids'][0], 'source': int(b['offset'], 16),
                    'groups': split_groups(rom, b)})
    out.sort(key=lambda x: x['id'])
    return out


def read_by_directory(rom, first_id, counts):
    """Relit les chaînes d'un bloc d'après le répertoire d'UNE ROM (ex. patchée), groupe par groupe."""
    slot = MASTER + 3 * (first_id - 1)
    base = cpu_to_file(int.from_bytes(rom[slot:slot + 3], 'little'))
    ng = int.from_bytes(rom[base:base + 2], 'little') // 2
    assert ng == len(counts), ('nombre de groupes différent', first_id)
    groups = []
    for g in range(ng):
        p = base + int.from_bytes(rom[base + 2 * g:base + 2 * g + 2], 'little')
        strings = []
        for _ in range(counts[g]):
            q = rom.index(b'\0', p)
            strings.append(rom[p:q])
            p = q + 1
        groups.append(strings)
    return groups


def str_id(block_id, g, k):
    return 'B%03d-S%03d' % (block_id, g * 16 + k + 1)


def text_width(text, limit=LIMIT_PX):
    """Plus grande largeur de ligne en pixels (<04> compté 96 px, <05>-<07> comptés 32 px : estimation). None si non mesurable."""
    try:
        return max(ff.visible_width(line, ROM_FOR_WIDTH, {5: 32, 6: 32, 7: 32}) for line in text.split('\n'))
    except Exception:
        return None


ROM_FOR_WIDTH = None


def text_rows(rom, fr_rom=None):
    """Toutes les chaînes du jeu sous forme de lignes (dict) ; fr pré-rempli d'après fr_rom (ROM française) si fournie."""
    global ROM_FOR_WIDTH
    ROM_FOR_WIDTH = rom
    rows = []
    for blk in main_blocks(rom):
        counts = [len(g) for g in blk['groups']]
        fr_groups = read_by_directory(fr_rom, blk['id'], counts) if fr_rom else None
        starts = [int(x, 16) for x in blk['block']['group_targets']]
        for g, strings in enumerate(blk['groups']):
            off = starts[g]
            for k, raw in enumerate(strings):
                en = ff.decode_fr(raw)
                fr = ff.decode_fr(fr_groups[g][k]) if fr_groups else ''
                if fr_groups and fr == '' and en != '':
                    fr = '<VIDE>'          # chaîne volontairement vide (une cellule vide = garder l'anglais)
                width = text_width(fr) if fr else None
                status = ''
                if fr:
                    status = 'identique' if fr == en else ''
                    if width is not None and width > LIMIT_PX and blk['id'] not in (1, 13) and CATEGORIES.get(blk['id']) not in ('objets',):
                        status = 'TROP LARGE'
                rows.append({'id': str_id(blk['id'], g, k), 'cat': CATEGORIES.get(blk['id'], 'dialogues'),
                             'offset': '0x%06X' % off, 'en': esc(en), 'fr': esc(fr),
                             'px': '' if width is None else width, 'statut': status})
                off += len(raw) + 1
    return rows


def cmd_texts(a):
    rom = load_rom(a.rom)
    fr_rom = with_ips(rom, a.fr_ips)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = text_rows(rom, fr_rom)
    write_tsv(out / 'textes.tsv', rows, TEXT_COLS)
    summary = {'textes.tsv': len(rows)}
    for cat in EXPORT_CATS:
        sub = [r for r in rows if r['cat'] == cat]
        if sub:
            write_tsv(out / ('%s.tsv' % cat), sub, TEXT_COLS)
            summary['%s.tsv' % cat] = len(sub)
    (out / 'LISEZMOI.txt').write_text(
        "textes.tsv : un texte par ligne (id = Bbloc-Schaîne, la même numérotation que le jeu).\n"
        "Colonnes à éditer : fr. Une cellule fr VIDE = texte anglais conservé.\n"
        "\\n = saut de ligne, <04> = nom du joueur, <05>-<07> = variables, <09> <6E> = coeur rouge, etc.\n"
        "Les fichiers par catégorie (objets.tsv, bestiaire.tsv...) sont des VUES de textes.tsv :\n"
        "pour construire, passer textes.tsv (ou concaténer vos vues) à la commande build.\n"
        "Variante : 'build' accepte plusieurs --texts ; une ligne d'une vue remplace celle de même id.\n",
        encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=1))


# --------------------------------------------------------------------------- textes : build
def load_text_rows(paths):
    """Fusionne plusieurs TSV : la dernière ligne portant un id donné l'emporte."""
    merged = {}
    for p in paths:
        for r in read_tsv(p):
            merged[r['id']] = r
    return merged


def rebuild_texts(rom, merged, rom0):
    """rom doit contenir les textes ORIGINAUX (zone libre à zéro). Retourne (rom, rapport)."""
    items = []
    changed_strings = 0
    for blk in main_blocks(rom0):
        new_groups = []
        for g, strings in enumerate(blk['groups']):
            ng = []
            for k, raw in enumerate(strings):
                r = merged.get(str_id(blk['id'], g, k))
                fr = unesc(r['fr']) if r and r.get('fr', '') != '' else None
                if fr == '<VIDE>':
                    fr = ''
                if fr is None or (fr == ff.decode_fr(raw)):
                    ng.append(raw)
                else:
                    ng.append(ff.encode_fr(fr))
                    changed_strings += 1
            new_groups.append(ng)
        if new_groups == blk['groups']:
            continue
        body = [b''.join(s + b'\0' for s in ng) for ng in new_groups]
        table_len = 2 * len(body)
        rel, pos = [], table_len
        for b in body:
            rel.append(pos)
            pos += len(b)
        payload = b''.join(x.to_bytes(2, 'little') for x in rel) + b''.join(body)
        source = blk['source']
        old = rom[source:int(blk['block']['end_exclusive'], 16)]
        items.append({'block': blk['block'], 'source': source, 'old': old, 'payload': payload, 'relative': rel})
    if not items:
        return rom, {'changed_strings': 0, 'blocks_rebuilt': 0}
    out, info = store_blocks(rom, items)
    info.update(changed_strings=changed_strings, blocks_rebuilt=len(items))
    return out, info


def cmd_check(a):
    global ROM_FOR_WIDTH
    rom = load_rom(a.rom)
    ROM_FOR_WIDTH = rom
    merged = load_text_rows(a.texts)
    problems = 0
    for r in merged.values():
        fr = unesc(r.get('fr', ''))
        if fr == '':
            continue
        try:
            ff.encode_fr(fr)
        except Exception as e:
            print('%s  caractère/code non supporté : %s' % (r['id'], e))
            problems += 1
            continue
        if r['cat'] in ('dialogues', 'bestiaire', 'personnages', 'boutique', 'combat'):
            for n, line in enumerate(fr.split('\n'), 1):
                try:
                    w = ff.visible_width(line, rom, {5: 32, 6: 32, 7: 32})
                except Exception as e:
                    print('%s  ligne %d non mesurable : %s' % (r['id'], n, e))
                    problems += 1
                    continue
                if w > LIMIT_PX:
                    print('%s  ligne %d : %d px > %d  « %s »' % (r['id'], n, w, LIMIT_PX, line))
                    problems += 1
    print('%d problème(s)' % problems)
    return 1 if problems else 0


# --------------------------------------------------------------------------- graphiques 2 bpp
from menu_graphics_lot49 import glyph  # noqa: E402


def strip_pixels(rom, off, tiles):
    w = tiles * 8
    px = [[0] * w for _ in range(8)]
    for t in range(tiles):
        raw = rom[off + t * 16: off + t * 16 + 16]
        for y in range(8):
            for x in range(8):
                b = 7 - x
                px[y][t * 8 + x] = ((raw[y * 2] >> b) & 1) | (((raw[y * 2 + 1] >> b) & 1) << 1)
    return px


def icon_of(px):
    w = len(px[0])
    on = [any(px[y][x] & 2 for y in range(8)) for x in range(w)]
    x1 = max(x for x in range(w) if on[x])
    x0 = x1
    while x0 > 0 and on[x0 - 1]:
        x0 -= 1
    return [row[x0:min(w, x1 + 2)] for row in px]


def render_strip(src, text, tiles, align, limit, icon):
    """Dessine un libellé avec l'alphabet natif 8 px (corps = 2, ombre = 1). Retourne (octets, largeur px)."""
    text = text.replace('’', "'").replace('œ', 'oe').replace('Œ', 'OE')
    gs = [glyph(src, c) for c in text]
    width = sum(len(g[0]) + 1 for g in gs) - 1
    w = tiles * 8
    total = width + 1
    x = (min(limit, w) - width - 1) if align == 'right' else 0
    body = [[0] * w for _ in range(8)]
    for g in gs:
        for y in range(8):
            body[y][x:x + len(g[y])] = g[y]
        x += len(g[0]) + 1
    val = [[2 if body[y][xx] else 1 if xx and body[y][xx - 1] else 0 for xx in range(w)] for y in range(8)]
    if icon is not None:
        ix = width + 3
        for y in range(8):
            for k, v in enumerate(icon[y]):
                val[y][ix + k] = v
        total = ix + len(icon[0])
    if total > min(limit, w):
        raise ValueError('« %s » : %d px > %d px disponibles' % (text, total, min(limit, w)))
    out = bytearray(tiles * 16)
    for xx in range(w):
        for y in range(8):
            v = val[y][xx]
            p = (xx // 8) * 16 + y * 2
            bit = 128 >> (xx % 8)
            if v & 1:
                out[p] |= bit
            if v & 2:
                out[p + 1] |= bit
    return bytes(out), total


def catalog_rows():
    rows = []
    for name, screen in STRIP_CATALOGS:
        for e in json.loads((ROOT / 'traduction' / (name + '.json')).read_text(encoding='utf-8')):
            rows.append({'id': 'G-%06X' % int(e['offset'], 16), 'kind': 'bande2bpp', 'offset': e['offset'],
                         'tiles': e['tiles'], 'align': e.get('align', 'left'),
                         'limit_px': e.get('limit_px', e['tiles'] * 8), 'icon': int(bool(e.get('icon'))),
                         'screen': (e.get('screen') or screen)[:70], 'en': e['english'], 'fr': e['french']})
    items = json.loads((ROOT / 'traduction/noms_objets_lot51_fr.json').read_text(encoding='utf-8'))
    rev = {e['index']: e['french'] for e in json.loads(
        (ROOT / 'traduction/noms_objets_revision_lot58_fr.json').read_text(encoding='utf-8'))}
    for e in items:
        rows.append({'id': 'G-%06X' % int(e['offset'], 16), 'kind': 'bande2bpp', 'offset': e['offset'],
                     'tiles': 8, 'align': 'left', 'limit_px': 64, 'icon': int(bool(e['icon'])),
                     'screen': 'nom d\'objet #%d (boutique/équipement)' % e['index'], 'en': e['english'],
                     'fr': rev.get(e['index'], e['french'])})
    seen, out = set(), []
    for r in rows:                      # une même bande ne figure qu'une fois (la dernière définition gagne)
        seen.add(r['id'])
    last = {}
    for r in rows:
        last[r['id']] = r
    for k in sorted(last):
        out.append(last[k])
    return out


def battle_tags():
    """Étiquettes de la roue de commandes du combat (sprites 16x16 en flux SPC7110 mode 2)."""
    glyphs, tags, bg = {}, [], None
    for name in ('etiquettes_combat_lot63_fr', 'etiquettes_combat_suite_lot67_fr'):
        d = json.loads((ROOT / 'traduction' / (name + '.json')).read_text(encoding='utf-8'))
        glyphs.update(d['glyphs'])
        bg = bg or [int(c, 16) for c in d['background']]
        tags += d['tags']
    return glyphs, tags, bg


def save_strip_png(path, strips, scale=3):
    """Planche PNG : une ligne par bande (libellé + dessin agrandi)."""
    from PIL import Image, ImageDraw
    pal = [(24, 24, 40), (90, 90, 120), (240, 240, 240), (255, 200, 60)]
    rowh = 8 * scale + 6
    width = max(len(px[0]) for _, px in strips) * scale + 260
    img = Image.new('RGB', (width, rowh * len(strips)), (50, 50, 70))
    d = ImageDraw.Draw(img)
    for i, (label, px) in enumerate(strips):
        d.text((2, i * rowh + 2), label, fill=(200, 255, 200))
        for y, line in enumerate(px):
            for x, v in enumerate(line):
                if v:
                    d.rectangle([260 + x * scale, i * rowh + 3 + y * scale, 260 + (x + 1) * scale - 1,
                                 i * rowh + 3 + (y + 1) * scale - 1], fill=pal[v])
    img.save(path)


def gfx_rows(rom, fr_rom=None):
    """Bandes 2 bpp + étiquettes de combat. Sans fr_rom, fr est vide ; avec, fr = fr_ref = catalogue V73."""
    rows = catalog_rows()
    for r in rows:
        r['fr_ref'] = r['fr'] if fr_rom else ''
        if not fr_rom:
            r['fr'] = ''
    glyphs, tags, bg = battle_tags()
    for t in tags:
        rows.append({'id': 'B-%06X' % int(t['left_stream'], 16), 'kind': 'combat(spc7110)',
                     'offset': t['left_stream'], 'tiles': '2x(16x16)', 'align': 'centre', 'limit_px': 31, 'icon': 0,
                     'screen': 'roue de commandes du combat (alphabet restreint : %s)' % ''.join(sorted(glyphs)),
                     'en': t['english'], 'fr': t['french'] if fr_rom else '', 'fr_ref': t['french'] if fr_rom else ''})
    return rows


def cmd_graphics(a):
    rom = load_rom(a.rom)
    fr_rom = with_ips(rom, a.fr_ips)
    out = Path(a.out)
    (out / 'png').mkdir(parents=True, exist_ok=True)
    rows = gfx_rows(rom, fr_rom)
    sheets = {}
    for r in rows:
        if r['kind'] != 'bande2bpp':
            continue
        key = 'objets' if r['screen'].startswith("nom d'objet") else 'menus'
        sheets.setdefault(key, []).append(('%s %s' % (r['offset'], r['en']), strip_pixels(rom, int(r['offset'], 16), int(r['tiles']))))
    write_tsv(out / 'graphiques.tsv', rows, GFX_COLS)
    for key, strips in sheets.items():
        for n in range(0, len(strips), 60):
            save_strip_png(out / 'png' / ('%s_%02d.png' % (key, n // 60)), strips[n:n + 60])
    print('%d bandes 2bpp + %d étiquettes de combat -> %s' % (len(sheets['objets']) + len(sheets['menus']), len(rows) - len(sheets['objets']) - len(sheets['menus']), out))


def pad_tiles_to_png(path, rom, off, ntiles, bpp, cols=16, scale=3):
    from PIL import Image
    tsz = 8 * bpp
    pal2 = [(0, 0, 0), (110, 110, 140), (230, 230, 230), (255, 190, 60)]
    pal4 = [(i * 17, i * 17, i * 17) for i in range(16)]
    pal = pal2 if bpp == 2 else pal4
    rows = (ntiles + cols - 1) // cols
    img = Image.new('RGB', (cols * 8, rows * 8))
    px = img.load()
    for t in range(ntiles):
        base = off + t * tsz
        if base + tsz > len(rom):
            break
        for y in range(8):
            planes = [rom[base + (p // 2) * 16 + y * 2 + (p % 2)] if bpp == 4 else rom[base + y * 2 + p]
                      for p in range(bpp)]
            for x in range(8):
                v = sum(((planes[p] >> (7 - x)) & 1) << p for p in range(bpp))
                px[(t % cols) * 8 + x, (t // cols) * 8 + y] = pal[v]
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(path)


def png_to_tiles(path, bpp, cols=16, scale=3):
    from PIL import Image
    img = Image.open(path).convert('RGB')
    img = img.resize((img.width // scale, img.height // scale), Image.NEAREST)
    pal2 = [(0, 0, 0), (110, 110, 140), (230, 230, 230), (255, 190, 60)]
    pal = pal2 if bpp == 2 else [(i * 17, i * 17, i * 17) for i in range(16)]

    def idx(c):
        return min(range(len(pal)), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i], c)))
    ntiles = (img.height // 8) * (img.width // 8)
    cw = img.width // 8
    out = bytearray()
    for t in range(ntiles):
        tile = bytearray(8 * bpp)
        for y in range(8):
            for x in range(8):
                v = idx(img.getpixel(((t % cw) * 8 + x, (t // cw) * 8 + y)))
                for p in range(bpp):
                    if (v >> p) & 1:
                        pos = (p // 2) * 16 + y * 2 + (p % 2) if bpp == 4 else y * 2 + p
                        tile[pos] |= 128 >> x
        out += tile
    return bytes(out)


def render_combat(fr, glyphs, bg):
    import build_v69 as b69
    import spc7110
    missing = sorted(set(fr) - set(glyphs))
    if missing:
        raise ValueError('étiquette « %s » : lettres sans dessin dans le catalogue : %s' % (fr, missing))
    img = b69.render(b69.word_body(glyphs, fr), bg)
    out = []
    for xo in (0, 16):
        d = b69.sprite_data(img, xo)
        enc = spc7110.encode_mode2(d)
        if len(enc) > 128:
            raise ValueError('étiquette « %s » : flux de %d octets > 128' % (fr, len(enc)))
        out.append((d, enc))
    return img, out


def build_rom(rom0, base, text_by_id=None, gfx=None):
    """rom0 = ROM anglaise ; base = ROM de base (ex. française) ou None ; retourne (rom, rapport)."""
    global ROM_FOR_WIDTH
    ROM_FOR_WIDTH = rom0
    if base:
        rom = bytearray(base)                       # on repart de la ROM de base, puis on remet les textes d'origine
        rom[TEXT_START:TEXT_END] = rom0[TEXT_START:TEXT_END]
        rom[MASTER:MASTER + 3 * COUNT] = rom0[MASTER:MASTER + 3 * COUNT]
        rom = bytes(rom)
    else:
        rom, _ = ff.patch_font(rom0)
    report = {}
    if text_by_id:
        rom, info = rebuild_texts(rom, text_by_id, rom0)
        report['textes'] = info
    if gfx:
        import spc7110
        glyphs, tags, bg = battle_tags()
        done, new = 0, bytearray(rom)
        for r in gfx:
            fr = r['fr'].strip()
            if not fr or fr == r['en'] and not base:
                continue
            if base and fr == r['fr_ref'].strip():
                continue                            # déjà présent dans la ROM de base
            off = int(r['offset'], 16)
            if r['kind'] == 'bande2bpp':
                tiles = int(r['tiles'])
                icon = icon_of(strip_pixels(rom0, off, tiles)) if int(r['icon']) else None
                data, px = render_strip(rom0, fr, tiles, r['align'], int(r['limit_px']), icon)
                new[off:off + tiles * 16] = data
            else:
                t = next(x for x in tags if int(x['left_stream'], 16) == off)
                _, parts = render_combat(fr, glyphs, bg)
                for o, (d, enc) in zip((int(t['left_stream'], 16), int(t['right_stream'], 16)), parts):
                    new[o:o + len(enc)] = enc
                    assert spc7110.decode_mode2(bytes(new), o, 128) == d
            done += 1
        rom = bytes(new)
        report['graphiques'] = done
    return checksum(rom), report


def cmd_build(a):
    rom0 = load_rom(a.rom)
    base = with_ips(rom0, a.base)
    rom, report = build_rom(rom0, base, load_text_rows(a.texts) if a.texts else None,
                            read_tsv(a.graphics) if a.graphics else None)
    ips = make_ips(rom0, rom)
    assert apply_ips(rom0, ips) == rom, 'relecture IPS KO'
    Path(a.ips_out).write_bytes(ips)
    if a.rom_out:
        Path(a.rom_out).write_bytes(rom)
    report.update(ips=str(a.ips_out), ips_octets=len(ips), rom_sha256=sha(rom))
    print(json.dumps(report, ensure_ascii=False, indent=1))


# --------------------------------------------------------------------------- tuiles brutes / SPC7110
def cmd_tiles(a):
    rom = load_rom(a.rom)
    pad_tiles_to_png(a.png, rom, int(a.offset, 0), a.tiles, a.bpp, cols=a.cols)
    print('%s : %d tuiles %d bpp depuis %s' % (a.png, a.tiles, a.bpp, a.offset))


def cmd_sheet(a):
    rom = load_rom(a.rom)
    s, e = int(a.start, 0), int(a.end, 0)
    n = (e - s) // (8 * a.bpp)
    pad_tiles_to_png(a.png, rom, s, n, a.bpp, cols=a.cols, scale=2)
    print('%s : %d tuiles de %s à %s (une ligne = %d tuiles = 0x%X octets)' % (
        a.png, n, a.start, a.end, a.cols, a.cols * 8 * a.bpp))


def cmd_tiles_import(a):
    rom0 = load_rom(a.rom)
    data = png_to_tiles(a.png, a.bpp, scale=a.scale)
    off = int(a.offset, 0)
    rom = bytearray(rom0)
    rom[off:off + len(data)] = data
    ips = make_ips(rom0, checksum(bytes(rom)))
    Path(a.ips_out).write_bytes(ips)
    print('%d octets écrits en %s -> %s' % (len(data), a.offset, a.ips_out))


def spc_png(path, rom, off, nbytes):
    import spc7110
    data = spc7110.decode_mode2(rom, off, nbytes)
    tmp = Path(path).with_suffix('.raw')
    tmp.write_bytes(data)
    pad_tiles_to_png(path, data, 0, len(data) // 32, 4, cols=a_cols(len(data) // 32))
    return data


def a_cols(n):
    return min(16, n)


def cmd_spc(a):
    rom = load_rom(a.rom)
    spc_png(a.png, rom, int(a.offset, 0), a.bytes)
    print('%s : %d octets décompressés (%d tuiles 4 bpp)' % (a.png, a.bytes, a.bytes // 32))


def cmd_spc_import(a):
    import spc7110
    rom0 = load_rom(a.rom)
    nbytes = a.bytes
    data = png_to_tiles(a.png, 4, scale=a.scale)
    assert len(data) == nbytes, 'le PNG doit contenir exactement %d tuiles (%d octets)' % (nbytes // 32, nbytes)
    enc = spc7110.encode_mode2(data)
    if len(enc) > a.slot:
        sys.exit('flux compressé trop gros : %d > %d octets (simplifier le dessin)' % (len(enc), a.slot))
    off = int(a.offset, 0)
    rom = bytearray(rom0)
    rom[off:off + len(enc)] = enc
    assert spc7110.decode_mode2(bytes(rom), off, nbytes) == data
    Path(a.ips_out).write_bytes(make_ips(rom0, checksum(bytes(rom))))
    print('flux de %d octets (emplacement %d) -> %s' % (len(enc), a.slot, a.ips_out))


# --------------------------------------------------------------------------- CLI
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('texts')
    s.add_argument('rom'); s.add_argument('--fr-ips', help="IPS français existant pour pré-remplir la colonne fr")
    s.add_argument('--out', default='retraduction'); s.set_defaults(f=cmd_texts)

    s = sub.add_parser('graphics')
    s.add_argument('rom'); s.add_argument('--fr-ips'); s.add_argument('--out', default='retraduction')
    s.set_defaults(f=cmd_graphics)

    s = sub.add_parser('build')
    s.add_argument('rom'); s.add_argument('--texts', nargs='*'); s.add_argument('--graphics')
    s.add_argument('--base', help="IPS de base (corrections moteur, graphismes...) ; ses textes sont remplacés par le TSV")
    s.add_argument('--ips-out', required=True); s.add_argument('--rom-out'); s.set_defaults(f=cmd_build)

    s = sub.add_parser('check')
    s.add_argument('rom'); s.add_argument('--texts', nargs='+', required=True); s.set_defaults(f=cmd_check)

    s = sub.add_parser('tiles')
    s.add_argument('rom'); s.add_argument('offset'); s.add_argument('--tiles', type=int, default=64)
    s.add_argument('--bpp', type=int, choices=(2, 4), default=2); s.add_argument('--cols', type=int, default=16)
    s.add_argument('--png', default='tiles.png'); s.set_defaults(f=cmd_tiles)

    s = sub.add_parser('sheet')
    s.add_argument('rom'); s.add_argument('start'); s.add_argument('end')
    s.add_argument('--bpp', type=int, choices=(2, 4), default=2); s.add_argument('--cols', type=int, default=32)
    s.add_argument('--png', default='sheet.png'); s.set_defaults(f=cmd_sheet)

    s = sub.add_parser('tiles-import')
    s.add_argument('rom'); s.add_argument('png'); s.add_argument('offset')
    s.add_argument('--bpp', type=int, choices=(2, 4), default=2); s.add_argument('--scale', type=int, default=3)
    s.add_argument('--ips-out', required=True); s.set_defaults(f=cmd_tiles_import)

    s = sub.add_parser('spc')
    s.add_argument('rom'); s.add_argument('offset'); s.add_argument('--bytes', type=int, default=128)
    s.add_argument('--png', default='spc.png'); s.set_defaults(f=cmd_spc)

    s = sub.add_parser('spc-import')
    s.add_argument('rom'); s.add_argument('png'); s.add_argument('offset')
    s.add_argument('--bytes', type=int, default=128); s.add_argument('--slot', type=int, default=128)
    s.add_argument('--scale', type=int, default=3); s.add_argument('--ips-out', required=True)
    s.set_defaults(f=cmd_spc_import)

    a = p.parse_args()
    try:
        sys.exit(a.f(a) or 0)
    except (ValueError, AssertionError) as e:
        sys.exit('ERREUR : %s' % e)


if __name__ == '__main__':
    main()
