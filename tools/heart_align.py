"""Alignement des cœurs du texte sur la grille de tuiles de 8 px.

Mécanisme (établi par des tests dans Snes9x, voir COMPTE_RENDU_V72.md) : le moteur de texte compose les
glyphes dans des tuiles de 8 px ; la couleur (blanc ou rouge pour le cœur, mode 09 ... 08) est portée par la
TUILE. Le cœur (glyphe 0x6E, largeur 8 px, colonnes de pixels 1 à 7) est donc rouge en entier seulement s'il
commence à 0 ou 1 px de la frontière d'une tuile (x mod 8 in {0, 1}). Sinon la partie qui tombe dans la tuile
suivante devient blanche (le glyphe qui suit, même un espace, recolore cette tuile), et un caractère visible
juste avant le cœur dans la même tuile devient rouge. La position x se calcule en additionnant les largeurs de
la table de largeurs de la police depuis le début de la ligne (le code 01 remet x à 0 ; le code 0D est une
pause qui ne remet pas x à 0). Le texte commence sur une frontière de tuile.

Correction : l'espace qui précède <09> est remplacé par un blanc de largeur adaptée (même nombre d'octets).
"""
import re, collections, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import french_font as ff  # noqa: E402

LO, HI = 0x600000, 0x6c9400


def _accents():
    return set(ff.CHAR_TO_BYTE[c] for c in 'éèêëàâäçùûüôöîïœÉÈÊÀÂÇÔ' if c in ff.CHAR_TO_BYTE)


def analyse(rom):
    W = lambda b: rom[ff.WIDTHS + b]
    textset = set(ff.CHAR_TO_BYTE.values()) | set(range(0x10)) | {0x6e, 0x17, 0x18, 0x13, 0x19, 0x2d}
    acc = _accents()
    plan, skipped = [], collections.Counter()
    for m in re.finditer(b'\x09\x6e', rom[LO:HI]):
        p = LO + m.start()
        s = p
        while s > LO and rom[s - 1] != 0:
            s -= 1
        e = p
        while e < HI and rom[e] != 0:
            e += 1
        seg = rom[s:e]
        if sum(1 for b in seg if b not in textset) > 2:
            skipped['non texte'] += 1; continue
        if not (any(b in acc for b in seg) or b'\x20\x21' in seg or b'\x20\x3f' in seg):
            skipped['anglais'] += 1; continue
        ls = s
        for q in range(p - 1, s - 1, -1):
            if rom[q] == 1:
                ls = q + 1; break
        if 4 in rom[ls:p]:
            skipped['nom dynamique'] += 1; continue
        plan.append(heart_info(rom, p, ls, e))
    return plan, skipped


def heart_info(rom, p, ls=None, e=None):
    """Position x (px depuis le début de la ligne) et nombre d'espaces ordinaires avant le cœur situé à l'octet p."""
    if ls is None:
        s = p
        while s > LO and rom[s - 1] != 0:
            s -= 1
        ls = s
        for q in range(p - 1, s - 1, -1):
            if rom[q] == 1:
                ls = q + 1
                break
    if e is None:
        e = p
        while e < HI and rom[e] != 0:
            e += 1
    x = 0
    for q in range(ls, p):
        if rom[q] >= 0x10:
            x += rom[ff.WIDTHS + rom[q]]
    k = 0
    while p - 1 - k >= ls and rom[p - 1 - k] == 0x20:
        k += 1
    return {'pos': p, 'x': x, 'k': k, 'ls': ls, 'e': e}


def line_width(rom, ls, e, widths=None):
    widths = widths or {}
    x = 0
    q = ls
    while q < e and rom[q] != 1:
        b = rom[q]
        if b >= 0x10:
            x += widths.get(q, rom[ff.WIDTHS + b])
        q += 1
    return x


def solve(rom, pl, limit=216):
    """Retourne ({position_octet: largeur}, mode) ; ({}, 'ok') si déjà bien placé ; (None, raison) sinon."""
    p, xh, k, ls, e = pl['pos'], pl['x'], pl['k'], pl['ls'], pl['e']
    if xh % 8 in (0, 1):
        return {}, 'ok'
    lw0 = line_width(rom, ls, e)
    if lw0 > limit + 8:
        return None, 'ligne déjà hors limite'
    # espaces ordinaires de la ligne avant le cœur, hors la série juste avant <09>
    run = list(range(p - k, p))
    others = [q for q in range(ls, p - k) if rom[q] == 0x20]
    best = None

    def consider(cost, assign, d_total, xnew):
        nonlocal best
        if best is None or cost < best[0]:
            best = (cost, assign)

    if k >= 1:
        import itertools
        cand = others[::-1][:5]
        combos = [()] + [(a,) for a in cand] + list(itertools.combinations(cand[:4], 2))
        for S in range(k, 11 * k + 1):
            dS = S - 3 * k
            for extras in combos:
                for ws in itertools.product((1, 2), repeat=len(extras)):
                    dE = sum(w - 3 for w in ws)
                    xnew = xh + dS + dE
                    if xnew % 8 not in (0, 1):
                        continue
                    if lw0 + dS + dE > limit and dS + dE > 0:
                        continue
                    base, rem = divmod(S, k)
                    assign = {run[i]: base + (1 if i < rem else 0) for i in range(k)}
                    for q, w in zip(extras, ws):
                        assign[q] = w
                    consider(abs(dS) + abs(dE) + len(extras), assign, dS + dE, xnew)
        return (best[1], 'run' if len(best[1]) == k else 'run+espaces') if best else (None, 'ligne trop large')
    # k = 0 : le cœur suit directement un caractère ; il doit commencer sur la frontière (x mod 8 == 0)
    for q in others[::-1][:3]:
        for w in range(1, 12):
            d = w - 3
            if (xh + d) % 8 == 0 and not (lw0 + d > limit and d > 0):
                consider(abs(d), {q: w}, d, xh + d)
    return (best[1], 'espace antérieur') if best else (None, 'aucun espace utilisable')
