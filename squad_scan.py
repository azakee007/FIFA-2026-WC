#!/usr/bin/env python3
"""Robustly scan squad-lists.txt (null-byte / accent noise) for marquee players.
A talisman absent here is exactly what Elo can't see -> a real strength flag."""
import re, unicodedata

def deaccent(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).upper()

# distinctive ASCII stems that survive accent-stripping
WATCH = {
    'France':      ['MBAPP', 'DEMBELE', 'SALIBA', 'TCHOUAMENI'],
    'England':     ['BELLINGHAM', 'KANE', 'SAKA', 'FODEN'],
    'Spain':       ['YAMAL', 'PEDRI', 'RODRI'],
    'Argentina':   ['MESSI', 'MARTINEZ', 'ALVAREZ'],
    'Brazil':      ['VINICIUS', 'RAPHINHA', 'RODRYGO'],
    'Portugal':    ['RONALDO', 'FERNANDES', 'LEAO'],
    'Norway':      ['HAALAND', 'DEGAARD'],
    'Belgium':     ['BRUYNE', 'DOKU', 'LUKAKU'],
    'Netherlands': ['DIJK', 'GAKPO', 'DEPAY'],
    'Germany':     ['MUSIALA', 'WIRTZ', 'KIMMICH'],
    'Egypt':       ['SALAH'],
    'Colombia':    ['DIAZ', 'RODRIGUEZ'],
    'Ecuador':     ['CAICEDO', 'VALENCIA'],
}

def main():
    raw = open('squad-lists.txt', 'rb').read().replace(b'\x00', b'')
    text = raw.decode('utf-8', 'ignore')
    lines = text.split('\n')

    # split into team sections by "TeamName (XYZ)" headers (allow accented names)
    hdr = re.compile(r'^(.+?) \([A-Z]{3}\)\s*$')
    sections, cur, name = {}, [], None
    for ln in lines:
        m = hdr.match(ln.strip())
        if m:
            if name:
                sections[name] = cur
            name, cur = m.group(1), []
        else:
            cur.append(ln)
    if name:
        sections[name] = cur

    print(f"Parsed {len(sections)} team sections\n")
    print(f"{'team':<13}{'squad#':>7}  talisman check")
    print("-" * 60)
    for team, stems in WATCH.items():
        block = None
        for sec in sections:
            if deaccent(sec) == deaccent(team):
                block = sections[sec]
                break
        if block is None:
            print(f"{team:<13}{'??':>7}  (section not found)")
            continue
        blob = deaccent(' '.join(block))
        n_players = sum(1 for l in block if re.match(r'\s*(GK|DF|MF|FW)', l))
        marks = []
        for s in stems:
            marks.append(('✅' if s in blob else '❌') + s)
        print(f"{team:<13}{n_players:>7}  {' '.join(marks)}")

if __name__ == '__main__':
    main()
