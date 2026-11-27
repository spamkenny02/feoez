#!/usr/bin/env python3
"""IPS à appliquer sur la ROM JAPONAISE d'origine (5 Mo) -> ROM française (7 Mo, patch anglais + traduction FR comprise).

    python3 tools/make_ips_from_jp.py ROM_JAPONAISE.sfc ROM_FR.sfc SORTIE.ips

La ROM de sortie est celle obtenue en appliquant les IPS cumulatifs sur la ROM anglaise (par ex. V75).
La zone 0x500000-0x6FFFFF (données ajoutées par le patch) est écrite en entier : l'IPS ne dépend donc
d'aucun remplissage implicite du logiciel d'application.
"""
import sys
from pathlib import Path
from sd2snes_compat import preserve_native_calls


def build_ips(jp, target, gap=6):
    n = len(jp)
    recs, i, L = [], 0, len(target)
    while i < min(n, L):                      # zone commune : différences regroupées
        if jp[i] == target[i]:
            i += 1
            continue
        s = i
        last = i
        while i < min(n, L) and (i - last) <= gap:
            if jp[i] != target[i]:
                last = i
            i += 1
        recs.append([s, last + 1])
    if L > n:                                  # zone ajoutée : écrite telle quelle (zéros compris)
        recs.append([n, L])
    out = bytearray(b'PATCH')
    for s, e in recs:
        while s < e:
            a = s
            if a == 0x454F46:                  # adresse réservée au marqueur EOF
                a -= 1
            b = min(e, a + 0xFFFF)
            data = target[a:b]
            out += a.to_bytes(3, 'big') + len(data).to_bytes(2, 'big') + data
            s = b
    return bytes(out + b'EOF')


def apply_ips_any(rom, ips):
    """Applicateur indépendant (avec extension de taille) pour la vérification."""
    assert ips[:5] == b'PATCH'
    out = bytearray(rom)
    p = 5
    while ips[p:p + 3] != b'EOF':
        off = int.from_bytes(ips[p:p + 3], 'big'); size = int.from_bytes(ips[p + 3:p + 5], 'big'); p += 5
        if size == 0:
            raise ValueError('RLE non attendu')
        if off + size > len(out):
            out += bytes(off + size - len(out))
        out[off:off + size] = ips[p:p + size]; p += size
    return bytes(out)


def main():
    jp = Path(sys.argv[1]).read_bytes()
    target = preserve_native_calls(jp, Path(sys.argv[2]).read_bytes())
    ips = build_ips(jp, target)
    assert apply_ips_any(jp, ips) == target, 'relecture KO'
    Path(sys.argv[3]).write_bytes(ips)
    print('IPS : %d octets' % len(ips))


if __name__ == '__main__':
    main()
