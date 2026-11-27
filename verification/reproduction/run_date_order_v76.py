#!/usr/bin/env python3
"""Fresh V76 startup and controller-only day/month editing regression replay."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--dll-dir', type=Path)
    args = parser.parse_args()
    expected = json.loads((ROOT / 'verification/build_report_v76.json').read_text())['rom_sha256']
    assert hashlib.sha256(args.rom.read_bytes()).hexdigest() == expected
    args.out.mkdir(parents=True, exist_ok=False)
    commands = []
    for original in json.loads((HERE / 'scenario.json').read_text()):
        c = {k: v for k, v in original.items() if k in ('frames', 'buttons', 'reset', 'screenshot')}
        if c.get('screenshot') in ('date_setup', 'birth_step3'):
            c['save'] = c['screenshot']
        commands.append(c)
        if c.get('screenshot') == 'birth_step3':
            break

    def capture(name):
        commands.append({'frames': 120, 'screenshot': name, 'dump_ram': name, 'dump_persistent': name})

    def press(key, name=None):
        commands.extend([{'frames': 12, 'buttons': [key]}, {'frames': 60}])
        if name:
            capture(name)

    def load(name):
        commands.append({'load': '@RUN_DIR@/' + name + '.state', 'frames': 120})

    load('date_setup')
    capture('rtc_day_first')
    press('Up', 'rtc_day_23')
    press('A'); press('Up', 'rtc_month_01')
    press('A'); press('Up', 'rtc_year_1996')
    press('A'); press('Up')
    press('A'); press('Up')
    press('A', 'rtc_confirmation')
    press('Left'); press('A', 'rtc_accepted')
    load('birth_step3')
    press('A', 'birth_edit_day')
    press('Up', 'birth_day_23')
    press('A'); press('Up', 'birth_month_01')
    press('A'); press('Down', 'birth_year_1994')
    press('A', 'birth_confirmation')
    press('Left'); press('A', 'birth_accepted')
    load('date_setup')
    for _ in range(9): press('Up')
    press('A'); press('Up'); press('Up')
    for _ in range(4): press('A')
    capture('invalid_31_feb_confirmation')
    press('Left'); press('A', 'invalid_31_feb_rejected')
    press('Up', 'invalid_back_to_day')
    load('date_setup')
    press('A'); press('Left'); press('Up', 'backtracking_to_day')
    commands.append({'quit': True})
    (args.out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n', encoding='utf-8')
    resolved = json.loads(json.dumps(commands).replace('@RUN_DIR@', args.out.resolve().as_posix()))
    cmd = [sys.executable, str(HERE / 'libretro_runner.py'), '--core', str(args.core.resolve()),
           '--rom', str(args.rom.resolve()), '--out', str(args.out.resolve())]
    if args.dll_dir: cmd += ['--dll-dir', str(args.dll_dir.resolve())]
    with (args.out / 'console.log').open('w', encoding='utf-8') as log:
        subprocess.run(cmd, input=''.join(json.dumps(c) + '\n' for c in resolved),
                       text=True, stdout=log, stderr=subprocess.STDOUT, check=True)
    ram = lambda name: (args.out / (name + '.wram')).read_bytes()
    for name, fields in (
        ('rtc_day_23', (95, 12, 23, 12, 0)),
        ('rtc_month_01', (95, 1, 23, 12, 0)),
        ('rtc_year_1996', (96, 1, 23, 12, 0)),
        ('birth_accepted', (94, 1, 23, 12, 0)),
        ('invalid_31_feb_rejected', (95, 2, 31, 12, 0)),
        ('invalid_back_to_day', (95, 2, 1, 12, 0)),
        ('backtracking_to_day', (95, 12, 23, 12, 0)),
    ):
        assert ram(name)[0x1E39:0x1E3E] == bytes(fields), name
    assert ram('birth_accepted')[0x4D1:0x4D4] == bytes([94, 1, 23])
    rtc = (args.out / 'rtc_accepted.rtc').read_bytes()
    assert rtc[2:12] == bytes([1, 0, 3, 1, 3, 2, 1, 0, 6, 9]), rtc.hex()
    assert ram('backtracking_to_day')[0x1E15] == 0
    report = {'version': 'V76', 'rom_sha256': expected,
              'core_sha256': hashlib.sha256(args.core.read_bytes()).hexdigest(),
              'controller_only': True, 'states_created_from_same_rom': True,
              'rtc_persisted': '1996-01-23 13:01', 'birthday_stored': '1994-01-23',
              'invalid_february_31_rejected': True, 'backtracking_to_day': True,
              'visual_review': 'pending', 'hardware_validation': 'pending',
              'screenshots': [p.name for p in sorted(args.out.glob('*.png'))
                              if p.stem.startswith(('rtc_', 'invalid_', 'backtracking_'))
                              or p.stem in ('birth_edit_day', 'birth_day_23', 'birth_month_01',
                                            'birth_year_1994', 'birth_confirmation', 'birth_accepted')]}
    (args.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
