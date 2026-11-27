#!/usr/bin/env python3
"""Build the complete V76 French IPS directly from the pinned Japanese ROM."""
import argparse
import hashlib
import json
from pathlib import Path

from date_order_fr import patch_date_order
from make_ips_from_jp import apply_ips_any, build_ips
from sd2snes_compat import DISABLED_HOOK_SPANS

ROOT = Path(__file__).resolve().parents[1]
JP_SHA256 = '8620203da71d32d017bb21f542864c1d90705b87eb67815d06b43f09120318aa'
BASE_SHA256 = '26e4f1fd94387f7e39f6d10c8fc24a7975b57325c1e5906025ea3bdc10783364'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(source):
    if len(source) != 0x500000 or sha(source) != JP_SHA256:
        raise ValueError('Expected the original unheadered Japanese ROM: ' + JP_SHA256)
    base_patch = (ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V75.ips').read_bytes()
    if sha(base_patch) != BASE_SHA256:
        raise ValueError('V75 SD2SNES reference patch has changed')
    baseline = apply_ips_any(source, base_patch)
    target, edits = patch_date_order(baseline)
    out = bytearray(target)
    # Same raw 7 MiB sum convention used by the existing translation tools.
    # Each checksum/complement pair sums to 0x1FE, so replacing it is stable.
    checksum = sum(out) & 0xFFFF
    out[0xFFDC:0xFFE0] = (checksum ^ 0xFFFF).to_bytes(2, 'little') + checksum.to_bytes(2, 'little')
    target = bytes(out)
    assert sum(target) & 0xFFFF == checksum
    allowed = [(int(edit['offset'], 16), int(edit['offset'], 16) + len(bytes.fromhex(edit['before']))) for edit in edits]
    allowed.append((0xFFDC, 0xFFE0))
    changed = [offset for offset, (old, new) in enumerate(zip(baseline, target)) if old != new]
    assert all(any(start <= offset < end for start, end in allowed) for offset in changed)
    assert target[0x2F5200:0x2F7300] == baseline[0x2F5200:0x2F7300]
    assert target[0x600000:0x6D0000] == baseline[0x600000:0x6D0000]
    for start, end in DISABLED_HOOK_SPANS:
        assert target[start:end] == source[start:end]
    ips = build_ips(source, target)
    assert apply_ips_any(source, ips) == target
    report = {'version': 'V76', 'source_sha256': sha(source),
              'source_bytes': len(source), 'baseline_ips_sha256': sha(base_patch),
              'baseline_rom_sha256': sha(baseline), 'rom_sha256': sha(target),
              'rom_bytes': len(target), 'ips_sha256': sha(ips), 'ips_bytes': len(ips),
              'checksum': hex(checksum), 'ips_roundtrip': True,
              'sd2snes_native_calls_preserved': True, 'date_edits': edits,
              'changed_bytes_from_v75': len(changed),
              'outside_documented_spans_preserved': True, 'font_and_dialogue_pool_preserved': True,
              'scope': 'Clock, birthday input/confirmation and shared Almanac numeric display; internal date storage unchanged.',
              'hardware_validation': 'V75 baseline reported working by user; V76 requires a new SD2SNES test.'}
    return target, ips, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('japanese_rom', type=Path)
    parser.add_argument('--rom-out', type=Path)
    args = parser.parse_args()
    ips_path = ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V76.ips'
    report_path = ROOT / 'verification/build_report_v76.json'
    inputs = {args.japanese_rom.resolve(), (ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V75.ips').resolve()}
    if args.rom_out and (args.rom_out.resolve() in inputs or args.rom_out.resolve() in {ips_path.resolve(), report_path.resolve()}):
        parser.error('--rom-out must not overwrite an input, IPS or report')
    target, ips, report = build(args.japanese_rom.read_bytes())
    ips_path.write_bytes(ips)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.rom_out:
        args.rom_out.write_bytes(target)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
