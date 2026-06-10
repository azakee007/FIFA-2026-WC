#!/usr/bin/env python3
"""Verify teams.csv Elo column against live World.tsv (eloratings.net).
Reuses backtest.py's name->code->elo mapping. Reports every mismatch."""
import csv
from backtest import norm

# manual aliases for teams whose teams.csv name doesn't normalise to an en.teams.tsv name
ALIAS = {
    'turkiye': 'turkey', 'czechia': 'czechrepublic', 'southkorea': 'korearepublic',
    'usa': 'unitedstates', 'congodr': 'drcongo', 'ivorycoast': 'cotedivoire',
    'capeverde': 'caboverde', 'bosnia': 'bosniaandherzegovina',
    'curacao': 'curacao', 'iran': 'iran',
}

def load_name2code():
    n2c = {}
    for line in open('en.teams.tsv', encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        for nm in p[1:]:
            if nm:
                n2c.setdefault(norm(nm), p[0])
    return n2c

def load_code2elo():
    c2e = {}
    for line in open('World.tsv', encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) > 3 and f[2]:
            try:
                c2e[f[2]] = int(f[3])
            except ValueError:
                pass
    return c2e

def main():
    n2c, c2e = load_name2code(), load_code2elo()
    rows = list(csv.DictReader(open('teams.csv', encoding='utf-8')))
    out = []
    unmatched = []
    for r in rows:
        team, stated = r['team'], int(r['elo'])
        key = norm(team)
        code = n2c.get(key) or n2c.get(ALIAS.get(key, ''))
        if not code or code not in c2e:
            unmatched.append(team)
            continue
        live = c2e[code]
        out.append((stated - live, team, stated, live, code))

    out.sort(key=lambda x: -abs(x[0]))
    print(f"{'team':<16}{'csv':>6}{'live':>6}{'diff':>7}  code")
    print("-" * 45)
    for diff, team, stated, live, code in out:
        flag = '  <-- MISMATCH' if abs(diff) >= 1 else ''
        print(f"{team:<16}{stated:>6}{live:>6}{diff:>+7}  {code}{flag}")
    mism = [o for o in out if abs(o[0]) >= 1]
    print(f"\nmatched {len(out)}/48 | mismatches {len(mism)} | "
          f"max |diff| {max((abs(o[0]) for o in out), default=0)}")
    if unmatched:
        print(f"UNMATCHED (name lookup failed): {unmatched}")

if __name__ == '__main__':
    main()
