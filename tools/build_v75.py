#!/usr/bin/env python3
"""Build V75 = V74 + libellés des listes de drapeaux de débogage (blocs 21 à 27), 531 chaînes. Base : IPS V74."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import feoez_kit as kit  # noqa: E402
import french_font as ff  # noqa: E402
import debug_labels_fr as dl  # noqa: E402
from insert import make_ips, apply_ips  # noqa: E402
from sd2snes_compat import preserve_native_calls  # noqa: E402

def main():
    src = Path(sys.argv[1]).read_bytes()
    assert kit.sha(src) == kit.EXPECTED
    v74 = apply_ips(src, (ROOT / 'Tengai_Makyou_Zero_FR_V74.ips').read_bytes())
    rows = kit.text_rows(src, v74)
    by = {r['id']: r for r in rows}
    cap = 178   # plus grande largeur des libellés anglais d'origine
    n = 0
    for r in rows:
        if r['cat'] != 'debug':
            continue
        en = kit.unesc(r['en'])
        if not en.strip() or kit.unesc(r['fr']) != en:
            continue
        fr = dl.translate(r['id'], en)
        if fr == en:
            continue
        assert ff.visible_width(fr, src, {5: 32, 6: 32, 7: 32}) <= cap, (r['id'], fr)
        r['fr'] = kit.esc(fr)
        n += 1
    rom, rep = kit.build_rom(src, v74, by, None)
    rom = preserve_native_calls(src, rom)
    ips = make_ips(src, rom)
    assert apply_ips(src, ips) == rom
    (ROOT / 'Tengai_Makyou_Zero_FR_V75.ips').write_bytes(ips)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_bytes(rom)
    print(json.dumps({'version': 'V75', 'strings_translated': n, 'rom_sha256': kit.sha(rom), 'ips_sha256': kit.sha(ips), **rep}, indent=1))

if __name__ == '__main__':
    main()
