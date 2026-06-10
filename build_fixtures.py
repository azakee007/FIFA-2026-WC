#!/usr/bin/env python3
"""Extract the real 72 group-stage fixtures (date, venue, matchday) into fixtures.csv."""
import csv
from collections import defaultdict
from altitude import VENUE_ALT

R2MINE = {'Bosnia and Herzegovina':'Bosnia','Curaçao':'Curacao','Czech Republic':'Czechia',
          'Turkey':'Turkiye','United States':'USA','DR Congo':'Congo DR'}
def mine(n): return R2MINE.get(n, n)

group = {r['team']: r['group'] for r in csv.DictReader(open('teams.csv', encoding='utf-8'))}

rows = [r for r in csv.DictReader(open('results.csv', encoding='utf-8'))
        if r['date'] >= '2026-06-01' and r['tournament'] == 'FIFA World Cup']
assert len(rows) == 72, len(rows)

fx = []
for r in rows:
    h, a = mine(r['home_team']), mine(r['away_team'])
    g = group[h]
    assert group[a] == g, f"{h}/{a} groups differ"
    fx.append(dict(group=g, date=r['date'], home=h, away=a,
                   venue=r['city'], venue_alt=VENUE_ALT[r['city']]))

# assign matchday by date order within each group
for g in set(f['group'] for f in fx):
    dates = sorted(set(f['date'] for f in fx if f['group'] == g))
    md = {d: i+1 for i, d in enumerate(dates)}
    for f in fx:
        if f['group'] == g:
            f['matchday'] = md[f['date']]

fx.sort(key=lambda f: (f['group'], f['matchday'], f['date']))
cols = ['group', 'matchday', 'date', 'home', 'away', 'venue', 'venue_alt']
w = csv.DictWriter(open('fixtures.csv', 'w', newline='', encoding='utf-8'), fieldnames=cols)
w.writeheader(); w.writerows(fx)
print(f"wrote fixtures.csv ({len(fx)} fixtures)")
print("\nGroup A (real schedule order):")
for f in fx:
    if f['group'] == 'A':
        print(f"  MD{f['matchday']} {f['date']}  {f['home']} vs {f['away']}  @ {f['venue']} ({f['venue_alt']}m)")
