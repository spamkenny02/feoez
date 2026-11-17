#!/usr/bin/env python3
"""feoez_gui : atelier graphique de traduction pour Far East of Eden Zero (s'ouvre dans le navigateur).

    python3 tools/feoez_gui.py            # puis charger la ROM anglaise (obligatoire) et la ROM/IPS française (facultative)

- Aucun module à installer (bibliothèque standard uniquement) ; le serveur n'écoute que sur 127.0.0.1.
- Vos modifications sont enregistrées en continu dans  projet_feoez/modifs.json  (reprises au prochain lancement).
- La ROM anglaise n'est jamais modifiée : « Construire » produit un IPS (et une ROM) à télécharger.
"""
import argparse
import base64
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import feoez_kit as kit  # noqa: E402
import french_font as ff  # noqa: E402
import spc7110  # noqa: E402
from insert import make_ips, apply_ips  # noqa: E402

PROJECT = Path('projet_feoez')
S = {'en': None, 'fr': None, 'fr_name': '', 'texts': [], 'gfx': [], 'edits': {'text': {}, 'gfx': {}},
     'last': {}, 'lock': threading.Lock()}


def load_edits():
    f = PROJECT / 'modifs.json'
    if f.exists():
        try:
            S['edits'] = json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            pass


def save_edits():
    PROJECT.mkdir(exist_ok=True)
    (PROJECT / 'modifs.json').write_text(json.dumps(S['edits'], ensure_ascii=False, indent=0), encoding='utf-8')


def compute_rows():
    S['texts'] = kit.text_rows(S['en'], S['fr'])
    S['gfx'] = kit.gfx_rows(S['en'], S['fr'])
    for r in S['texts']:
        if r['id'] in S['edits']['text']:
            r['fr'] = S['edits']['text'][r['id']]
    for r in S['gfx']:
        if r['id'] in S['edits']['gfx']:
            r['fr'] = S['edits']['gfx'][r['id']]


def digits(px):
    return [''.join('%x' % v for v in row) for row in px]


def unpack4(data):
    """128 octets de tuiles 4 bpp (ordre du flux : HG, BG, HD, BD) -> image 16x16 (valeurs 0-15)."""
    img = [[0] * 16 for _ in range(16)]
    for t, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
        raw = data[t * 32:(t + 1) * 32]
        for y in range(8):
            for x in range(8):
                v = 0
                for k in range(4):
                    byte = raw[(k // 2) * 16 + y * 2 + (k % 2)]
                    v |= ((byte >> (7 - x)) & 1) << k
                img[dy + y][dx + x] = v
    return img


def combat_english(row):
    glyphs, tags, bg = kit.battle_tags()
    t = next(x for x in tags if int(x['left_stream'], 16) == int(row['offset'], 16))
    left = unpack4(spc7110.decode_mode2(S['en'], int(t['left_stream'], 16), 128))
    right = unpack4(spc7110.decode_mode2(S['en'], int(t['right_stream'], 16), 128))
    return [l + r for l, r in zip(left, right)]


def gfx_payload():
    out = []
    for r in S['gfx']:
        d = dict(r)
        d['px'] = (digits(kit.strip_pixels(S['en'], int(r['offset'], 16), int(r['tiles'])))
                   if r['kind'] == 'bande2bpp' else digits(combat_english(r)))
        out.append(d)
    return out


def gfx_preview(row_id, fr):
    r = next(x for x in S['gfx'] if x['id'] == row_id)
    if r['kind'] == 'bande2bpp':
        tiles = int(r['tiles'])
        off = int(r['offset'], 16)
        icon = kit.icon_of(kit.strip_pixels(S['en'], off, tiles)) if int(r['icon']) else None
        data, px = kit.render_strip(S['en'], fr, tiles, r['align'], int(r['limit_px']), icon)
        return {'px': digits(kit.strip_pixels(data, 0, tiles)), 'width': px}
    glyphs, tags, bg = kit.battle_tags()
    img, parts = kit.render_combat(fr, glyphs, bg)
    return {'px': digits(img), 'width': max(len(e) for _, e in parts), 'unit': 'octets (max 128)'}


def tiles_view(src, offset, n, bpp, cols, spc, nbytes):
    rom = S['fr'] if src == 'fr' and S['fr'] else S['en']
    if spc:
        rom = spc7110.decode_mode2(rom, offset, nbytes)
        offset = 0
        n = len(rom) // (8 * bpp)
    rows = (n + cols - 1) // cols
    px = [[0] * (cols * 8) for _ in range(rows * 8)]
    tsz = 8 * bpp
    for t in range(n):
        base = offset + t * tsz
        if base + tsz > len(rom):
            break
        for y in range(8):
            planes = [rom[base + (p // 2) * 16 + y * 2 + (p % 2)] if bpp == 4 else rom[base + y * 2 + p]
                      for p in range(bpp)]
            for x in range(8):
                px[(t // cols) * 8 + y][(t % cols) * 8 + x] = sum(((planes[p] >> (7 - x)) & 1) << p for p in range(bpp))
    return {'px': digits(px), 'w': cols * 8, 'h': rows * 8}


def font_payload():
    rom = S['en']
    cmap = {c: b for c, b in ff.CHAR_TO_BYTE.items()}
    return {'widths': list(rom[ff.WIDTHS:ff.WIDTHS + 256]),
            'glyphs': base64.b64encode(rom[ff.FONT:ff.FONT + 256 * 32]).decode(),
            'map': cmap, 'aliases': ff.ALIASES, 'limit': kit.LIMIT_PX}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, data, ctype='application/json', code=200, headers=None):
        if not isinstance(data, (bytes, bytearray)):
            data = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype + ('; charset=utf-8' if ctype.startswith('text') or ctype == 'application/json' else ''))
        self.send_header('Content-Length', str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        return self.rfile.read(int(self.headers.get('Content-Length') or 0))

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == '/':
                return self.send(PAGE.encode(), 'text/html')
            if u.path == '/api/state':
                return self.send({'en': S['en'] is not None, 'fr': S['fr'] is not None, 'fr_name': S['fr_name'],
                                  'texts': len(S['texts']), 'gfx': len(S['gfx']),
                                  'edits': len(S['edits']['text']) + len(S['edits']['gfx'])})
            if S['en'] is None:
                return self.send({'error': "Chargez d'abord la ROM anglaise"}, code=400)
            if u.path == '/api/texts':
                return self.send([[r['id'], r['cat'], r['offset'], kit.unesc(r['en']), kit.unesc(r['fr'])] for r in S['texts']])
            if u.path == '/api/font':
                return self.send(font_payload())
            if u.path == '/api/gfx':
                return self.send(gfx_payload())
            if u.path == '/api/tiles':
                return self.send(tiles_view(q.get('src', 'en'), int(q['offset'], 0), int(q.get('n', 512)), int(q.get('bpp', 2)),
                                            int(q.get('cols', 32)), q.get('spc') == '1', int(q.get('bytes', 128))))
            if u.path == '/api/download':
                what = q['what']
                if what not in S['last']:
                    return self.send({'error': "Rien à télécharger : lancez d'abord la construction"}, code=400)
                name = {'ips': 'traduction.ips', 'rom': 'traduction.sfc'}[what]
                return self.send(S['last'][what], 'application/octet-stream',
                                 headers={'Content-Disposition': 'attachment; filename="%s"' % name})
            if u.path == '/api/export':
                import io
                import csv
                rows = S['texts'] if q['what'] == 'textes' else S['gfx']
                cols = kit.TEXT_COLS if q['what'] == 'textes' else kit.GFX_COLS
                buf = io.StringIO()
                w = csv.DictWriter(buf, fieldnames=cols, delimiter='\t', extrasaction='ignore', lineterminator='\n')
                w.writeheader()
                w.writerows(rows)
                return self.send(('﻿' + buf.getvalue()).encode(), 'text/tab-separated-values',
                                 headers={'Content-Disposition': 'attachment; filename="%s.tsv"' % q['what']})
            self.send({'error': 'inconnu'}, code=404)
        except Exception as e:
            self.send({'error': str(e)}, code=400)

    def do_POST(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            data = self.body()
            with S['lock']:
                if u.path == '/api/upload':
                    return self.upload(q['kind'], data, q.get('name', ''))
                if S['en'] is None:
                    return self.send({'error': "Chargez d'abord la ROM anglaise"}, code=400)
                j = json.loads(data or b'{}')
                if u.path == '/api/text':
                    r = next(x for x in S['texts'] if x['id'] == j['id'])
                    r['fr'] = kit.esc(j['fr'])
                    S['edits']['text'][r['id']] = r['fr']
                    save_edits()
                    return self.send({'ok': True})
                if u.path == '/api/gfx_set':
                    r = next(x for x in S['gfx'] if x['id'] == j['id'])
                    r['fr'] = j['fr']
                    S['edits']['gfx'][r['id']] = j['fr']
                    save_edits()
                    return self.send({'ok': True})
                if u.path == '/api/gfx_preview':
                    try:
                        return self.send(gfx_preview(j['id'], j['fr']))
                    except Exception as e:
                        return self.send({'error': str(e)})
                if u.path == '/api/forget':
                    S['edits'] = {'text': {}, 'gfx': {}}
                    save_edits()
                    compute_rows()
                    return self.send({'ok': True})
                if u.path == '/api/build':
                    return self.build(bool(j.get('use_base')))
            self.send({'error': 'inconnu'}, code=404)
        except Exception as e:
            self.send({'error': str(e)}, code=400)

    def upload(self, kind, data, name):
        if kind == 'en':
            if kit.sha(data) != kit.EXPECTED:
                return self.send({'error': "Ce n'est pas la ROM anglaise d'origine (SHA-256 attendu %s...). "
                                           "Chargez la ROM anglaise non modifiée ici ; la ROM française va dans l'autre case." % kit.EXPECTED[:12]}, code=400)
            S['en'] = data
            S['fr'] = None
            S['fr_name'] = ''
        elif kind == 'fr':
            if S['en'] is None:
                return self.send({'error': "Chargez d'abord la ROM anglaise"}, code=400)
            if data.startswith(b'PATCH'):
                S['fr'] = apply_ips(S['en'], data)
            elif len(data) == len(S['en']):
                S['fr'] = data
            else:
                return self.send({'error': 'Fichier incompatible : ni IPS, ni ROM de %d octets (reçu %d)' % (len(S['en']), len(data))}, code=400)
            S['fr_name'] = name
        elif kind == 'clearfr':
            S['fr'] = None
            S['fr_name'] = ''
        compute_rows()
        self.send({'ok': True, 'texts': len(S['texts']), 'gfx': len(S['gfx'])})

    def build(self, use_base):
        base = S['fr'] if use_base and S['fr'] else None
        rom, report = kit.build_rom(S['en'], base, {r['id']: r for r in S['texts']}, S['gfx'])
        ips = make_ips(S['en'], rom)
        assert apply_ips(S['en'], ips) == rom, 'relecture IPS KO'
        S['last'] = {'ips': ips, 'rom': rom}
        PROJECT.mkdir(exist_ok=True)
        (PROJECT / 'traduction.ips').write_bytes(ips)
        report.update(ips_octets=len(ips), rom_sha256=kit.sha(rom), base='ROM française chargée' if base else 'aucune (ROM anglaise + police)')
        self.send(report)


PAGE = r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atelier FEOEZ</title>
<style>
:root{--bg:#14161c;--pn:#1d2029;--pn2:#262a36;--tx:#e6e8ee;--mu:#9aa1b2;--ac:#6ab0ff;--ok:#5fd38d;--ko:#ff6b6b;--bd:#343949}
@media (prefers-color-scheme:light){:root{--bg:#f2f3f7;--pn:#fff;--pn2:#e9ebf2;--tx:#1b1e27;--mu:#5d6475;--ac:#1565c0;--ok:#1b8f4d;--ko:#c62828;--bd:#cfd3de}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.4 system-ui,Segoe UI,sans-serif;height:100vh;display:flex;flex-direction:column}
header{background:var(--pn);border-bottom:1px solid var(--bd);padding:8px 14px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}
h1{font-size:16px;margin:0}.chip{padding:2px 9px;border-radius:99px;background:var(--pn2);font-size:12px;color:var(--mu)}.chip.on{color:var(--ok)}
label.file{background:var(--pn2);border:1px solid var(--bd);border-radius:6px;padding:5px 10px;cursor:pointer;font-size:13px}label.file:hover{border-color:var(--ac)}
input[type=file]{display:none}nav{display:flex;gap:2px;background:var(--pn);padding:0 10px;border-bottom:1px solid var(--bd)}
nav button{background:none;border:0;color:var(--mu);padding:9px 14px;cursor:pointer;font-size:14px;border-bottom:2px solid transparent}nav button.act{color:var(--tx);border-color:var(--ac)}
main{flex:1;min-height:0;display:flex}.tab{display:none;flex:1;min-width:0}.tab.act{display:flex}
.side{width:380px;border-right:1px solid var(--bd);display:flex;flex-direction:column;background:var(--pn)}
.tools{padding:8px;display:flex;gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--bd)}
select,input[type=text],input[type=number],textarea{background:var(--pn2);color:var(--tx);border:1px solid var(--bd);border-radius:5px;padding:5px 7px;font:inherit}
textarea{width:100%;font-family:ui-monospace,Consolas,monospace;font-size:13px;resize:vertical}
.list{flex:1;overflow:auto}.row{padding:5px 9px;border-bottom:1px solid var(--bd);cursor:pointer;display:flex;gap:8px}.row:hover{background:var(--pn2)}.row.sel{background:var(--pn2);box-shadow:inset 3px 0 var(--ac)}
.row small{color:var(--mu);min-width:72px;font-family:ui-monospace,monospace}.row span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}.row .fr{color:var(--ok)}.row .nofr{color:var(--ko)}
.edit{flex:1;padding:14px;overflow:auto;min-width:0}h3{margin:14px 0 5px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mu)}
button.b{background:var(--ac);color:#fff;border:0;border-radius:6px;padding:7px 14px;cursor:pointer;font-size:14px}button.g{background:var(--pn2);color:var(--tx);border:1px solid var(--bd);border-radius:6px;padding:6px 11px;cursor:pointer}
button:disabled{opacity:.4;cursor:default}canvas{background:#0b0d12;image-rendering:pixelated;border:1px solid var(--bd);max-width:100%}
.meter{height:6px;background:var(--pn2);border-radius:3px;margin:3px 0 8px;overflow:hidden}.meter i{display:block;height:100%;background:var(--ok)}.meter i.over{background:var(--ko)}
.lines div{font-family:ui-monospace,monospace;font-size:12px;color:var(--mu)}.lines .over{color:var(--ko)}.err{color:var(--ko)}.ok{color:var(--ok)}.mu{color:var(--mu)}
.pad{padding:18px;overflow:auto;flex:1}.box{background:var(--pn);border:1px solid var(--bd);border-radius:8px;padding:14px;margin-bottom:14px;max-width:760px}
pre{background:var(--pn2);padding:10px;border-radius:6px;overflow:auto;font-size:12px}
</style></head><body>
<header><h1>Atelier de traduction — Far East of Eden Zero</h1>
<label class="file">ROM anglaise (obligatoire)<input type="file" id="fEn" accept=".sfc,.smc,.bin"></label><span class="chip" id="cEn">non chargée</span>
<label class="file">ROM ou IPS français (facultatif)<input type="file" id="fFr" accept=".sfc,.smc,.bin,.ips"></label><span class="chip" id="cFr">aucun</span>
<span class="chip" id="cEd"></span><span id="msg" class="err"></span></header>
<nav id="nav"><button data-t="tTexts" class="act">Textes</button><button data-t="tGfx">Graphismes</button><button data-t="tTiles">Tuiles</button><button data-t="tBuild">Construire</button></nav>
<main>
<section class="tab act" id="tTexts"><div class="side"><div class="tools">
<select id="cat"></select><input type="text" id="q" placeholder="Rechercher (id, anglais, français)" style="flex:1;min-width:140px">
<label class="mu"><input type="checkbox" id="onlyTodo"> à traduire</label><label class="mu"><input type="checkbox" id="onlyOver"> trop larges</label></div>
<div class="mu" style="padding:4px 9px" id="count"></div><div class="list" id="list"></div></div>
<div class="edit" id="ed"><p class="mu">Chargez la ROM anglaise (en haut) pour commencer. Ajoutez la ROM ou l'IPS français pour pré-remplir les traductions existantes.</p></div></section>

<section class="tab" id="tGfx"><div class="side"><div class="tools"><select id="gcat"><option value="">Tous</option><option value="obj">Noms d'objets</option><option value="menu">Menus / boutiques / titre</option><option value="cmb">Étiquettes de combat</option></select>
<input type="text" id="gq" placeholder="Rechercher" style="flex:1"></div><div class="mu" style="padding:4px 9px" id="gcount"></div><div class="list" id="glist"></div></div>
<div class="edit" id="ged"></div></section>

<section class="tab" id="tTiles"><div class="edit">
<div class="tools" style="border:0;padding:0 0 10px"><select id="tsrc"><option value="en">ROM anglaise</option><option value="fr">ROM française</option></select>
Offset <input type="text" id="toff" value="0x6D0000" size="10"> Tuiles <select id="tbpp"><option value="2">2 bpp</option><option value="4">4 bpp</option></select>
Colonnes <input type="number" id="tcols" value="32" min="4" max="64" style="width:62px"> Tuiles/page <input type="number" id="tn" value="512" min="16" max="2048" style="width:72px">
<label><input type="checkbox" id="tspc"> flux SPC7110 (mode 2) — octets <input type="number" id="tbytes" value="128" step="32" style="width:72px"></label>
<button class="g" id="tprev">◀</button><button class="g" id="tnext">▶</button><button class="b" id="tgo">Afficher</button></div>
<div class="mu" id="tinfo">Survolez : offset de la tuile ; clic : copie l'offset. Sert à repérer du texte dessiné (enseignes, décors).</div><canvas id="tc"></canvas></div></section>

<section class="tab" id="tBuild"><div class="pad">
<div class="box"><h3 style="margin-top:0">Construire le patch</h3>
<label><input type="checkbox" id="useBase" checked> Conserver les correctifs de la ROM/IPS française chargée (cœurs, calendrier, moteur…) — recommandé</label>
<p class="mu">Les textes et graphismes affichés (y compris vos modifications) sont réinjectés dans la ROM anglaise. Décochez la case pour partir de la ROM anglaise seule + police française.</p>
<button class="b" id="build">Construire</button> <span id="bmsg" class="mu"></span><pre id="blog" hidden></pre>
<p id="dl" hidden><a href="/api/download?what=ips"><button class="g">Télécharger l'IPS</button></a> <a href="/api/download?what=rom"><button class="g">Télécharger la ROM (.sfc)</button></a></p></div>
<div class="box"><h3 style="margin-top:0">Fichiers</h3>
<a href="/api/export?what=textes"><button class="g">Exporter textes.tsv</button></a> <a href="/api/export?what=graphiques"><button class="g">Exporter graphiques.tsv</button></a>
<p class="mu">Vos modifications sont enregistrées automatiquement dans <code>projet_feoez/modifs.json</code>.</p>
<button class="g" id="forget">Oublier toutes mes modifications</button></div></div></section>
</main>
<script>
const $=s=>document.querySelector(s);const J=async(u,o)=>{const r=await fetch(u,o);const j=await r.json();if(j.error)throw new Error(j.error);return j};
let T=[],G=[],F=null,sel=-1,view=[],gsel=-1,gview=[];const catNames={};
const PAL=['#181828','#5a5a78','#f0f0f0','#ffc83c'];
function msg(t){$('#msg').textContent=t||''}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button,.tab').forEach(x=>x.classList.remove('act'));b.classList.add('act');$('#'+b.dataset.t).classList.add('act')});
async function up(kind,file){msg('');try{$('#cEn').textContent='chargement…';const r=await fetch('/api/upload?kind='+kind+'&name='+encodeURIComponent(file.name),{method:'POST',body:await file.arrayBuffer()});const j=await r.json();if(j.error)throw new Error(j.error);await refresh()}catch(e){msg(e.message);await state()}}
$('#fEn').onchange=e=>e.target.files[0]&&up('en',e.target.files[0]);$('#fFr').onchange=e=>e.target.files[0]&&up('fr',e.target.files[0]);
async function state(){const s=await J('/api/state');$('#cEn').textContent=s.en?'chargée ('+s.texts+' textes, '+s.gfx+' graphismes)':'non chargée';$('#cEn').className='chip'+(s.en?' on':'');
$('#cFr').textContent=s.fr?s.fr_name||'chargé':'aucun';$('#cFr').className='chip'+(s.fr?' on':'');$('#cEd').textContent=s.edits?s.edits+' modification(s) enregistrée(s)':'';return s}
async function refresh(){const s=await state();if(!s.en)return;F=await J('/api/font');F.glyphs=Uint8Array.from(atob(F.glyphs),c=>c.charCodeAt(0));T=await J('/api/texts');G=await J('/api/gfx');
const cats={};T.forEach(r=>cats[r[1]]=(cats[r[1]]||0)+1);$('#cat').innerHTML='<option value="">Toutes catégories ('+T.length+')</option>'+Object.entries(cats).map(([k,v])=>`<option value="${k}">${k} (${v})</option>`).join('');
sel=-1;gsel=-1;filter();gfilter();$('#ed').innerHTML='<p class="mu">Choisissez un texte dans la liste.</p>'}
// ---------- polices / largeurs
const CTRL0=new Set([1,8,9,10,11,12,13,14]);
function codes(t){const out=[];t=t.normalize('NFC');for(const[k,v]of Object.entries(F.aliases))t=t.split(k).join(v);for(let i=0;i<t.length;){if(t[i]==='<'&&/^<[0-9A-F]{2}>/.test(t.slice(i,i+4))){out.push(parseInt(t.slice(i+1,i+3),16));i+=4}else if(t[i]==='\n'){out.push(1);i++}else{const c=F.map[t[i]];out.push(c===undefined?-1:c);i++}}return out}
function adv(c){if(c===4)return 96;if(c>=5&&c<=7)return 32;if(CTRL0.has(c))return 0;return F.widths[c]}
function lineWidths(t){return t.split('\n').map(l=>{let w=0,bad=[];for(const c of codes(l)){if(c<0){bad.push(c);continue}w+=adv(c)}return{w,bad:bad.length}})}
function drawText(cv,t,scale){const cs=codes(t),lines=[[]];for(const c of cs){if(c===1)lines.push([]);else lines[lines.length-1].push(c)}
const wd=lines.map(l=>l.reduce((a,c)=>a+(c<0?6:c===4?96:c>=5&&c<=7?32:CTRL0.has(c)?0:F.widths[c]),0));const W=Math.max(F.limit,...wd)+16,H=lines.length*18+8;cv.width=W;cv.height=H;cv.style.width=W*scale+'px';const g=cv.getContext('2d');g.fillStyle='#0b0d12';g.fillRect(0,0,W,H);g.strokeStyle='#3a2430';g.beginPath();g.moveTo(8+F.limit+.5,0);g.lineTo(8+F.limit+.5,H);g.stroke();
lines.forEach((ln,li)=>{let x=8;for(const c of ln){if(c===4){g.fillStyle='#2a3a55';g.fillRect(x,li*18+6,96,12);x+=96;continue}if(c>=5&&c<=7){g.fillStyle='#2a3a55';g.fillRect(x,li*18+6,32,12);x+=32;continue}if(c<0){g.fillStyle='#ff6b6b';g.fillRect(x,li*18+6,6,12);x+=6;continue}if(CTRL0.has(c))continue;
const o=c*32;g.fillStyle='#f4f4f4';for(let y=0;y<16;y++){const a=F.glyphs[o+y*2],b=F.glyphs[o+y*2+1];for(let k=0;k<8;k++){if(a&(128>>k))g.fillRect(x+k,li*18+4+y,1,1);if(b&(128>>k))g.fillRect(x+8+k,li*18+4+y,1,1)}}x+=F.widths[c]}})}
// ---------- textes
function untranslated(r){return r[4]===''||r[4]===r[3]}
function filter(){if(!T.length)return;const cat=$('#cat').value,q=$('#q').value.toLowerCase(),todo=$('#onlyTodo').checked,over=$('#onlyOver').checked;
view=[];for(let i=0;i<T.length&&view.length<5000;i++){const r=T[i];if(cat&&r[1]!==cat)continue;if(q&&!(r[0].toLowerCase().includes(q)||r[3].toLowerCase().includes(q)||r[4].toLowerCase().includes(q)))continue;if(todo&&!(untranslated(r)&&r[3].trim()!==''))continue;
if(over){if(r[1]==='objets'||r[1]==='menus'||r[1]==='commandes')continue;if(!lineWidths(r[4]).some(l=>l.w>F.limit))continue}view.push(i)}
$('#count').textContent=view.length+' texte(s)'+(view.length>=5000?' (affichage limité)':'');const sh=view.slice(0,400);
$('#list').innerHTML=sh.map((i,n)=>{const r=T[i];return `<div class="row${i===sel?' sel':''}" data-i="${i}"><small>${r[0]}</small><span class="${untranslated(r)?'nofr':'fr'}">${esc((r[4]||r[3]).replace(/\n/g,' ⏎ '))}</span></div>`}).join('')+(view.length>400?'<div class="mu" style="padding:8px">… affinez la recherche ('+(view.length-400)+' de plus)</div>':'');
document.querySelectorAll('#list .row').forEach(d=>d.onclick=()=>pick(+d.dataset.i))}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
let tmr=null;
function pick(i){sel=i;const r=T[i];document.querySelectorAll('#list .row').forEach(d=>d.classList.toggle('sel',+d.dataset.i===i));
$('#ed').innerHTML=`<div class="mu">${r[0]} · ${r[1]} · ${r[2]}</div><h3>Anglais</h3><textarea id="en" rows="4" readonly></textarea><canvas id="cen"></canvas>
<h3>Français <span class="mu" style="text-transform:none">(saut de ligne = Entrée ; codes &lt;XX&gt; à recopier tels quels)</span></h3><textarea id="fr" rows="5" spellcheck="true"></textarea>
<div class="meter"><i id="mt"></i></div><div class="lines" id="ln"></div><h3>Aperçu en jeu (police du jeu, ligne rouge = 216 px)</h3><canvas id="cfr"></canvas>
<p><button class="g" id="cp">Copier EN → FR</button> <button class="g" id="cl">Vider (garder l'anglais)</button> <button class="g" id="pv">◀ Précédent</button> <button class="g" id="nx">Suivant ▶</button></p>`;
$('#en').value=r[3];$('#fr').value=r[4]==='<VIDE>'?'<VIDE>':r[4];drawText($('#cen'),r[3],2);upd();
$('#fr').oninput=()=>{r[4]=$('#fr').value;upd();clearTimeout(tmr);tmr=setTimeout(async()=>{try{await J('/api/text',{method:'POST',body:JSON.stringify({id:r[0],fr:r[4]})});state()}catch(e){msg(e.message)}},400)};
$('#cp').onclick=()=>{$('#fr').value=r[3];$('#fr').oninput()};$('#cl').onclick=()=>{$('#fr').value='';$('#fr').oninput()};
const step=d=>{const p=view.indexOf(sel);if(p>=0&&view[p+d]!==undefined){pick(view[p+d]);document.querySelector('#list .row.sel')?.scrollIntoView({block:'nearest'})}};$('#pv').onclick=()=>step(-1);$('#nx').onclick=()=>step(1);$('#fr').focus()}
function upd(){const t=$('#fr').value,ws=lineWidths(t==='<VIDE>'?'':t);const mx=Math.max(...ws.map(l=>l.w));$('#mt').style.width=Math.min(100,mx/F.limit*100)+'%';$('#mt').className=mx>F.limit?'over':'';
$('#ln').innerHTML=ws.map((l,n)=>`<div class="${l.w>F.limit?'over':''}">ligne ${n+1} : ${l.w} px${l.w>F.limit?' (> '+F.limit+')':''}${l.bad?' — '+l.bad+' caractère(s) non supporté(s)':''}</div>`).join('');drawText($('#cfr'),t==='<VIDE>'?'':t,2)}
$('#cat').onchange=$('#q').oninput=$('#onlyTodo').onchange=$('#onlyOver').onchange=filter;
document.addEventListener('keydown',e=>{if(e.altKey&&(e.key==='ArrowDown'||e.key==='ArrowUp')&&$('#tTexts').classList.contains('act')){e.preventDefault();$(e.key==='ArrowDown'?'#nx':'#pv')?.click()}});
// ---------- graphismes
function gType(r){return r.kind!=='bande2bpp'?'cmb':r.screen.startsWith("nom d'objet")?'obj':'menu'}
function gfilter(){const c=$('#gcat').value,q=$('#gq').value.toLowerCase();gview=[];G.forEach((r,i)=>{if(c&&gType(r)!==c)return;if(q&&!(r.en.toLowerCase().includes(q)||r.fr.toLowerCase().includes(q)||r.offset.includes(q)))return;gview.push(i)});
$('#gcount').textContent=gview.length+' élément(s)';$('#glist').innerHTML=gview.slice(0,500).map(i=>{const r=G[i];return `<div class="row${i===gsel?' sel':''}" data-i="${i}"><small>${r.offset}</small><span>${esc(r.en)} → <b class="${r.fr?'fr':'nofr'}">${esc(r.fr||'—')}</b></span></div>`}).join('');
document.querySelectorAll('#glist .row').forEach(d=>d.onclick=()=>gpick(+d.dataset.i))}
function drawPx(cv,px,scale,pal){const h=px.length,w=px[0].length;cv.width=w;cv.height=h;cv.style.width=w*scale+'px';const g=cv.getContext('2d');for(let y=0;y<h;y++)for(let x=0;x<w;x++){const v=parseInt(px[y][x],16);g.fillStyle=pal(v);g.fillRect(x,y,1,1)}}
const pal2=v=>PAL[v&3],pal4=v=>`rgb(${v*17},${v*17},${v*17})`;
function gpick(i){gsel=i;const r=G[i];document.querySelectorAll('#glist .row').forEach(d=>d.classList.toggle('sel',+d.dataset.i===i));const cmb=r.kind!=='bande2bpp';
$('#ged').innerHTML=`<div class="mu">${r.id} · ${r.kind} · ${r.screen}</div><h3>Anglais (${r.en})</h3><canvas id="gen"></canvas><h3>Français</h3><input type="text" id="gfr" style="width:100%;font-size:16px" value="${esc(r.fr).replace(/"/g,'&quot;')}">
<p id="ginfo" class="mu"></p><h3>Rendu</h3><canvas id="gout"></canvas><p class="mu">${cmb?'Étiquette de combat : lettres limitées au catalogue ; aperçu en niveaux de gris (la palette réelle vient du jeu).':'Limite : '+r.limit_px+' px ('+r.tiles+' tuiles)'+(r.align==='right'?', aligné à droite':'')+(+r.icon?', icône finale conservée':'')+'.'}</p>
<button class="g" id="grev">Rétablir la référence (« ${esc(r.fr_ref||'—')} »)</button>`;drawPx($('#gen'),r.px,cmb?10:6,cmb?pal4:pal2);let t=null;
const run=async()=>{const v=$('#gfr').value;r.fr=v;try{await J('/api/gfx_set',{method:'POST',body:JSON.stringify({id:r.id,fr:v})});state()}catch(e){}
if(!v.trim()){$('#ginfo').textContent='Vide : bande inchangée (anglais).';$('#gout').getContext('2d').clearRect(0,0,999,999);return}
try{const p=await J('/api/gfx_preview',{method:'POST',body:JSON.stringify({id:r.id,fr:v})});drawPx($('#gout'),p.px,cmb?10:6,cmb?pal4:pal2);$('#ginfo').innerHTML='<span class="ok">'+p.width+' '+(p.unit||'px')+'</span>'}catch(e){$('#ginfo').innerHTML='<span class="err">'+esc(e.message)+'</span>'}
document.querySelectorAll('#glist .row').forEach(d=>{if(+d.dataset.i===i)d.querySelector('span').innerHTML=esc(r.en)+' → <b class="'+(v?'fr':'nofr')+'">'+esc(v||'—')+'</b>'})};
$('#gfr').oninput=()=>{clearTimeout(t);t=setTimeout(run,250)};$('#grev').onclick=()=>{$('#gfr').value=r.fr_ref;run()};run()}
$('#gcat').onchange=$('#gq').oninput=gfilter;
// ---------- tuiles
let toff=0;
async function tshow(){try{const bpp=+$('#tbpp').value,cols=+$('#tcols').value,spc=$('#tspc').checked;toff=parseInt($('#toff').value,0);
const p=await J(`/api/tiles?src=${$('#tsrc').value}&offset=${toff}&n=${$('#tn').value}&bpp=${bpp}&cols=${cols}&spc=${spc?1:0}&bytes=${$('#tbytes').value}`);
drawPx($('#tc'),p.px,3,bpp===2?pal2:pal4);$('#tc').dataset.cols=cols;$('#tc').dataset.bpp=bpp;$('#tc').dataset.spc=spc?1:0;msg('')}catch(e){msg(e.message)}}
$('#tgo').onclick=tshow;$('#toff').onkeydown=e=>e.key==='Enter'&&tshow();
const tpage=d=>{const s=$('#tspc').checked?+$('#tbytes').value:(+$('#tn').value)*8*(+$('#tbpp').value);$('#toff').value='0x'+Math.max(0,toff+d*s).toString(16).toUpperCase();tshow()};
$('#tprev').onclick=()=>tpage(-1);$('#tnext').onclick=()=>tpage(1);
function tpos(e){const cv=$('#tc'),r=cv.getBoundingClientRect(),sc=r.width/cv.width,x=Math.floor((e.clientX-r.left)/sc/8),y=Math.floor((e.clientY-r.top)/sc/8),cols=+cv.dataset.cols,bpp=+cv.dataset.bpp;return{t:y*cols+x,off:toff+(y*cols+x)*8*bpp}}
$('#tc').onmousemove=e=>{if($('#tc').dataset.spc==='1')return;const p=tpos(e);$('#tinfo').textContent='tuile '+p.t+' · offset 0x'+p.off.toString(16).toUpperCase()};
$('#tc').onclick=e=>{if($('#tc').dataset.spc==='1')return;const p=tpos(e),h='0x'+p.off.toString(16).toUpperCase();navigator.clipboard?.writeText(h);$('#tinfo').textContent='copié : '+h};
// ---------- construire
$('#build').onclick=async()=>{$('#bmsg').textContent='construction…';$('#blog').hidden=true;$('#dl').hidden=true;try{const j=await J('/api/build',{method:'POST',body:JSON.stringify({use_base:$('#useBase').checked})});$('#bmsg').innerHTML='<span class="ok">Terminé</span>';$('#blog').hidden=false;$('#blog').textContent=JSON.stringify(j,null,1);$('#dl').hidden=false}catch(e){$('#bmsg').innerHTML='<span class="err">'+esc(e.message)+'</span>'}};
$('#forget').onclick=async()=>{if(!confirm('Effacer toutes vos modifications et revenir au pré-remplissage ?'))return;await J('/api/forget',{method:'POST',body:'{}'});await refresh()};
state().then(s=>s.en&&refresh());
</script></body></html>'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--no-browser', action='store_true')
    ap.add_argument('--en', help="ROM anglaise à charger au démarrage (facultatif)")
    ap.add_argument('--fr', help="ROM ou IPS français à charger au démarrage (facultatif)")
    a = ap.parse_args()
    load_edits()
    if a.en:
        S['en'] = kit.load_rom(a.en)
        if a.fr:
            d = Path(a.fr).read_bytes()
            S['fr'] = apply_ips(S['en'], d) if d.startswith(b'PATCH') else d
            S['fr_name'] = Path(a.fr).name
        compute_rows()
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    url = 'http://127.0.0.1:%d/' % a.port
    print('Atelier FEOEZ : %s  (Ctrl+C pour quitter)' % url)
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
