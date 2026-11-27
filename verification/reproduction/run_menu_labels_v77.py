#!/usr/bin/env python3
"""Controller-only menu captures from a field state made with the same ROM."""
from pathlib import Path
import json,subprocess,sys
import argparse
p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
cases={'main':[],'scrolls':['A','A'],'settings':['Right','Down','A'],'inventory':['Down','A'],'inventory_actions':['Down','A','A'],'equip':['Down','Down','A','A'],'status':['Down','Down','Down','A','A'],'clock':['Right','Down','Down','Down','A'],'strategy':['Right','A']}
for name,buttons in cases.items():
 out=a.out/name;out.mkdir(parents=True,exist_ok=True)
 cmds=[{'load':str(a.state.resolve()),'frames':60},{'buttons':['X'],'frames':12},{'frames':80}]
 for key in buttons:cmds +=[{'buttons':[key],'frames':12},{'frames':60}]
 cmds +=[{'screenshot':'view','save':'view','dump_ram':'view','dump_vram':'view'},{'quit':True}]
 with (out/'console.log').open('w') as log:subprocess.run([sys.executable,str(Path(__file__).with_name('libretro_runner.py')),'--core',str(a.core.resolve()),'--rom',str(a.rom.resolve()),'--out',str(out.resolve())],input=''.join(json.dumps(c)+'\n' for c in cmds),text=True,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(name)
