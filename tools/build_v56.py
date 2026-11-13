#!/usr/bin/env python3
"""Build V56 = V55 IPS + lot graphique 50 (ecran Strategie).

Part de la ROM anglaise d'origine (SHA-256 verifie), applique l'IPS V55
publie (SHA-256 de la ROM V55 verifie), puis remplace les bandes de tuiles 2 bits
listees dans traduction/menu_graphics_lot50_fr.json. Ni la ROM source ni la ROM
produite ne sont distribuees : seul l'IPS V56 l'est.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from menu_graphics_lot49 import raster  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V55_SHA = '2631d90bd0f2b0ed927055143117525517d06f15f29511439d6e76acdc371e4c'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--rom-out', type=Path, required=True)
    a = p.parse_args()
    if a.source.resolve() == a.rom_out.resolve():
        p.error('Cannot overwrite source ROM')
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA, 'ROM source inattendue'
    v55 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V55.ips').read_bytes())
    assert sha(v55) == V55_SHA, 'La ROM V55 reconstruite ne correspond pas'
    rom = bytearray(v55)
    entries = json.loads((ROOT / 'traduction/menu_graphics_lot50_fr.json').read_text(encoding='utf-8'))
    changed = 0
    for e in entries:
        off = int(e['offset'], 16)
        n = e['tiles']
        # La zone doit etre identique a la ROM d'origine (aucun lot precedent n'y touche).
        assert v55[off:off + 16 * n] == source[off:off + 16 * n], e
        new = b'\0' * (16 * n) if e['french'] == '' else raster(source, e['french'], n)[0]
        assert len(new) == 16 * n, e
        rom[off:off + 16 * n] = new
        changed += 1
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V56.ips').write_bytes(ips)
    report = {
        'version': 'V56',
        'base': 'V55',
        'graphics_entries': changed,
        'ips_sha256': sha(ips),
        'rom_sha256': sha(out),
        'ips_roundtrip': True,
        'runtime_validation': 'captures Snes9x : verification/ecran_strategie_v56.png',
    }
    (ROOT / 'verification/build_report_v56.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
