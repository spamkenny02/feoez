#!/usr/bin/env python3
"""Build complete French V77 (full menu labels) from the original Japanese ROM."""
import argparse
import json
from pathlib import Path

from build_v76 import JP_SHA256, sha
from make_ips_from_jp import apply_ips_any, build_ips
from menu_full_labels import patch_menu_labels
from sd2snes_compat import DISABLED_HOOK_SPANS

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA256 = 'bac055b448ad5689510f0d7c9372cb8cfbdf5a90d016f1092c60ee9447e98b4f'


def build(source):
    if len(source) != 0x500000 or sha(source) != JP_SHA256:
        raise ValueError('Expected original unheadered Japanese ROM: ' + JP_SHA256)
    patch = (ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V76.ips').read_bytes()
    if sha(patch) != BASE_SHA256:
        raise ValueError('V76 baseline IPS has changed')
    baseline = apply_ips_any(source, patch)
    target, graphics = patch_menu_labels(baseline)
    out = bytearray(target)
    checksum = sum(out) & 0xFFFF
    out[0xFFDC:0xFFE0] = (checksum ^ 0xFFFF).to_bytes(2, 'little') + checksum.to_bytes(2, 'little')
    target = bytes(out)
    assert sum(target) & 0xFFFF == checksum
    allowed = [(int(a, 16), int(z, 16)) for a, z in graphics['spans']] + [(0xFFDC, 0xFFE0)]
    changed = [i for i, (a, b) in enumerate(zip(baseline, target)) if a != b]
    assert all(any(a <= i < z for a, z in allowed) for i in changed)
    assert target[0x2F5200:0x2F7300] == baseline[0x2F5200:0x2F7300]
    assert target[0x600000:0x6D0000] == baseline[0x600000:0x6D0000]
    for a, z in DISABLED_HOOK_SPANS:
        assert target[a:z] == source[a:z]
    ips = build_ips(source, target)
    assert apply_ips_any(source, ips) == target
    return target, ips, {'version': 'V77', 'source_sha256': sha(source),
                         'source_bytes': len(source), 'baseline_ips_sha256': sha(patch),
                         'rom_sha256': sha(target), 'rom_bytes': len(target),
                         'ips_sha256': sha(ips), 'ips_bytes': len(ips),
                         'checksum': hex(checksum), 'ips_roundtrip': True,
                         'changed_bytes_from_v76': len(changed),
                         'outside_documented_spans_preserved': True,
                         'dialogue_font_and_pool_preserved': True,
                         'sd2snes_native_calls_preserved': True, 'menu_graphics': graphics,
                         'hardware_validation': 'V77 requires a fresh SD2SNES test.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('japanese_rom', type=Path)
    parser.add_argument('--rom-out', type=Path)
    args = parser.parse_args()
    ips_path = ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V77.ips'
    report_path = ROOT / 'verification/build_report_v77.json'
    protected = {args.japanese_rom.resolve(), (ROOT / 'Tengai_Makyou_Zero_JP_vers_FR_V76.ips').resolve(),
                 ips_path.resolve(), report_path.resolve()}
    if args.rom_out and args.rom_out.resolve() in protected:
        parser.error('--rom-out must not overwrite a source, IPS or report')
    rom, ips, report = build(args.japanese_rom.read_bytes())
    ips_path.write_bytes(ips)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.rom_out:
        args.rom_out.write_bytes(rom)
    print(json.dumps({k: v for k, v in report.items() if k != 'menu_graphics'}, indent=2))


if __name__ == '__main__':
    main()
