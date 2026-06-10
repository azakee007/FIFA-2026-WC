#!/usr/bin/env python3
"""
Backtest for the WC2026 Elo+Poisson engine.

Method (leakage-free):
  1. Reconstruct World-Football-Elo chronologically over ALL real internationals
     (1872->today). Each match is predicted using ONLY pre-match ratings, then the
     ratings update. No lookahead by construction.
  2. Validate: compare reconstructed current Elo vs eloratings.net's live World.tsv
     for the WC teams -> confirms the rebuild is on the right scale.
  3. Score the production model (imported expected_goals/match_analytics) on a recent
     window using Ranked Probability Score (the football-standard metric), outcome
     accuracy, exact-score hit, and probability calibration -- vs honest baselines.

A model that can't beat the base-rate (climatology) forecast is adding noise.
"""
import csv, math, unicodedata
from collections import defaultdict
from wc2026_model import expected_goals, match_analytics, CONFIG

EVAL_FROM = "2018-01-01"     # score matches on/after this date
ELO_HOME_ADV = 100           # home advantage used INSIDE the Elo rating system
INIT = 1500

def is_major(t):
    """Major-tournament FINALS (not qualifiers) — the WC-like population."""
    t = t.lower()
    return 'qual' not in t and any(x in t for x in
        ('world cup', 'copa am', 'african cup', 'asian cup', 'uefa euro'))

# ---------- Elo reconstruction ----------
def k_factor(tour):
    t = tour.lower()
    if 'friendly' in t:                              return 20
    if 'world cup' in t and 'qual' not in t:         return 60
    if 'qualif' in t:                                return 40
    if 'nations league' in t:                        return 40
    if any(x in t for x in ('euro', 'copa am', 'african cup', 'asian cup',
                            'gold cup', 'confederations')) and 'qual' not in t:
        return 50
    return 30

def gd_mult(d):
    if d <= 1:  return 1.0
    if d == 2:  return 1.5
    if d == 3:  return 1.75
    return 1.75 + (d - 3) / 8.0

def rps(pH, pD, pA, outcome):
    oH, oD, _ = (1,0,0) if outcome=='H' else (0,1,0) if outcome=='D' else (0,0,1)
    c1 = pH - oH; c2 = (pH+pD) - (oH+oD)
    return (c1*c1 + c2*c2) / 2.0

def run(eval_from=EVAL_FROM):
    rows = [r for r in csv.DictReader(open('results.csv', encoding='utf-8'))
            if r['home_score'] not in ('', 'NA')]
    elo = defaultdict(lambda: INIT)
    evals = []                                   # pre-match snapshots for scoring
    for r in rows:
        h, a = r['home_team'], r['away_team']
        try: hs, as_ = int(r['home_score']), int(r['away_score'])
        except ValueError: continue
        neutral = r['neutral'].strip().upper() == 'TRUE'
        eh, ea = elo[h], elo[a]
        if r['date'] >= eval_from:
            evals.append((eh, ea, neutral, hs, as_, r['tournament'], r['date'], h, a))
        # --- Elo update (uses pre-match eh/ea) ---
        dr = (eh + (0 if neutral else ELO_HOME_ADV)) - ea
        We = 1.0 / (10 ** (-dr / 400.0) + 1.0)
        W = 1.0 if hs > as_ else 0.5 if hs == as_ else 0.0
        K = k_factor(r['tournament']) * gd_mult(abs(hs - as_))
        delta = K * (W - We)
        elo[h] = eh + delta; elo[a] = ea - delta
    return elo, evals

# ---------- validation vs live eloratings ----------
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode()
    return ''.join(c for c in s.lower() if c.isalnum())

def validate(elo):
    name2code = {}
    for line in open('en.teams.tsv', encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        for nm in p[1:]:
            if nm: name2code.setdefault(norm(nm), p[0])
    code2elo = {}
    for line in open('World.tsv', encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) > 3 and f[2]:
            try: code2elo[f[2]] = int(f[3])
            except: pass
    pairs = []
    for team, my in elo.items():
        c = name2code.get(norm(team))
        if c in code2elo: pairs.append((my, code2elo[c]))
    n = len(pairs)
    mx = sum(x for x,_ in pairs)/n; my_ = sum(y for _,y in pairs)/n
    cov = sum((x-mx)*(y-my_) for x,y in pairs)
    sx = math.sqrt(sum((x-mx)**2 for x,_ in pairs)); sy = math.sqrt(sum((y-my_)**2 for _,y in pairs))
    corr = cov/(sx*sy)
    mae = sum(abs(x-y) for x,y in pairs)/n
    return n, corr, mae

# ---------- score the model ----------
def score(evals):
    n = len(evals)
    # base-rate (climatology) probabilities from the eval set itself
    fH = sum(1 for e in evals if e[3] > e[4]) / n
    fD = sum(1 for e in evals if e[3] == e[4]) / n
    fA = 1 - fH - fD
    m = dict(rps=0, base_rps=0, acc=0, naive_acc=0, exact=0, gd_mae=0,
             sign=0, pgoals=0, agoals=0)
    cal = defaultdict(lambda: [0,0])             # confidence bin -> [hits, n]
    for eh, ea, neutral, hs, as_, tour, date, h, a in evals:
        ta = {'elo': eh, 'host': 0 if neutral else 1}
        tb = {'elo': ea, 'host': 0}
        lamH, lamA = expected_goals(ta, tb, CONFIG)
        (pi, pj), (pH, pD, pA), _ = match_analytics(lamH, lamA, CONFIG['GRID'])
        outcome = 'H' if hs > as_ else 'D' if hs == as_ else 'A'
        m['rps']      += rps(pH, pD, pA, outcome)
        m['base_rps'] += rps(fH, fD, fA, outcome)
        pred = 'H' if pH==max(pH,pD,pA) else 'D' if pD==max(pH,pD,pA) else 'A'
        m['acc']   += (pred == outcome)
        m['naive_acc'] += (('H' if (eh+(0 if neutral else ELO_HOME_ADV))>=ea else 'A') == outcome)
        m['exact'] += (pi == hs and pj == as_)
        m['gd_mae']+= abs((pi-pj) - (hs-as_))
        m['sign']  += ((pi-pj>0)==(hs-as_>0) and (pi-pj<0)==(hs-as_<0)) or (pi==pj and hs==as_)
        m['pgoals']+= lamH+lamA; m['agoals'] += hs+as_
        pf = max(pH,pD,pA); b = min(int(pf*10),9); cal[b][0]+= (pred==outcome); cal[b][1]+=1
    for k in m: m[k] = m[k]/n if k not in ('rps','base_rps','gd_mae','pgoals','agoals') else m[k]/n
    return n, m, (fH,fD,fA), cal

def main():
    elo, evals = run()
    vN, corr, mae = validate(elo)
    n, m, base, cal = score(evals)
    skill = 1 - m['rps']/m['base_rps']
    majors = [e for e in evals if is_major(e[5])]
    nM, mM, _, _ = score(majors)
    skillM = 1 - mM['rps']/mM['base_rps']
    L = []
    P = lambda s: (print(s), L.append(s))
    P("# WC2026 Engine — Backtest Report\n")
    P(f"**Reconstruction validation** (my Elo vs live eloratings, {vN} teams): "
      f"correlation **{corr:.3f}**, mean abs error **{mae:.0f} Elo**.")
    P(f"  → high correlation = the rebuilt ratings are on the same scale the model predicts on.\n")
    P(f"**Test set:** {n:,} internationals since {EVAL_FROM}. "
      f"Base rates H/D/A = {base[0]*100:.0f}/{base[1]*100:.0f}/{base[2]*100:.0f}%.\n")
    P("## Headline — does the model beat climatology?\n")
    P(f"- **RPS (model): {m['rps']:.4f}**  vs  base-rate {m['base_rps']:.4f}  "
      f"→ **skill score {skill*100:+.1f}%** (positive = adds value; lower RPS is better)")
    P(f"  - ⚠️ That figure is padded by easy friendlies/qualifiers. On **major-tournament "
      f"finals only** ({nM:,} games — the WC-like population), skill is **{skillM*100:+.1f}%**: "
      f"the honest number for World Cup expectations.")
    P(f"- **Outcome accuracy (3-way): {m['acc']*100:.1f}%**  vs  higher-Elo-wins {m['naive_acc']*100:.1f}%")
    P(f"- Goal-difference sign correct: {m['sign']*100:.1f}%  |  GD mean-abs-error: {m['gd_mae']:.2f}")
    P(f"- Exact-scoreline hit rate: {m['exact']*100:.1f}%  (≈10-12% is strong for football)")
    P(f"- Goals/game — predicted {m['pgoals']:.2f} vs actual {m['agoals']:.2f}  (model goal calibration)\n")
    P("## Probability calibration (confidence vs reality)\n")
    P("| Predicted confidence | Matches | Actual hit rate |")
    P("|---|---|---|")
    for b in range(3,10):
        hits,c = cal[b]
        if c: P(f"| {b*10}-{b*10+10}% | {c} | {hits/c*100:.0f}% |")
    open('backtest.md','w',encoding='utf-8').write("\n".join(L))
    print("\nWrote backtest.md")

if __name__ == '__main__':
    main()
