#!/usr/bin/env python3
"""Build V61 = V60 IPS + lot 55 : noms de lieux trop larges raccourcis (remplacement sur place).

La fenetre de lieu de l'ecran de sauvegarde coupe le texte vers 96-98 px : « Village de l'Ombre du F ».
21 noms de lieux francais depassaient 96 px (blocs B014 et B015, copies relogees vers 0x6c4000-0x6c5fff).
Chaque nom est remplace sur place par une forme plus courte, completee par des espaces jusqu'a la
longueur d'origine : le terminateur et la longueur du bloc ne changent pas, donc aucun index de phrase
ni pointeur n'est touche. Toutes les occurrences exactes (delimitees par des 0x00) sont remplacees.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from insert import make_ips, apply_ips  # noqa: E402
from french_font import encode_fr, visible_width  # noqa: E402

SOURCE_SHA = 'eb07eed483f8f79ab64309c50ad0ef19560946b8e28fbd695470552ba68e356e'
V60_SHA = 'e709b16c97e34dee8ea869f725386a1bd22a4dc05d86445339ddfb39e8d3aa95'
PAD = encode_fr(' ')


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
    v60 = apply_ips(source, (ROOT / 'Tengai_Makyou_Zero_FR_V60.ips').read_bytes())
    assert sha(v60) == V60_SHA, 'La ROM V60 reconstruite ne correspond pas'
    rom = bytearray(v60)
    entries = json.loads((ROOT / 'traduction/noms_lieux_lot55_fr.json').read_text(encoding='utf-8'))
    report = []
    for e in entries:
        old = encode_fr(e['french_old'])
        new = encode_fr(e['french_new'])
        assert len(new) <= len(old), e
        padded = new + PAD * (len(old) - len(new))
        hits = [m.start() + 1 for m in re.finditer(re.escape(b'\0' + old + b'\0'), bytes(v60))]
        assert len(hits) >= 2, (e, hits)
        for h in hits:
            assert rom[h:h + len(old)] == old
            rom[h:h + len(old)] = padded
        report.append({'english': e['english'], 'french_old': e['french_old'], 'french_new': e['french_new'],
                       'offsets': [hex(h) for h in hits], 'bytes': len(old)})
    out = bytes(rom)
    ips = make_ips(source, out)
    assert apply_ips(source, ips) == out, 'IPS roundtrip KO'
    a.rom_out.write_bytes(out)
    (ROOT / 'Tengai_Makyou_Zero_FR_V61.ips').write_bytes(ips)
    summary = {'version': 'V61', 'base': 'V60', 'places': len(report),
               'replaced_occurrences': sum(len(r['offsets']) for r in report),
               'ips_sha256': sha(ips), 'rom_sha256': sha(out), 'ips_roundtrip': True,
               'runtime_validation': 'capture Snes9x : verification/lieu_sauvegarde_v61.png'}
    (ROOT / 'verification/build_report_v61.json').write_text(
        json.dumps({**summary, 'entries': report}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
