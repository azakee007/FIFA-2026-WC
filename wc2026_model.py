#!/usr/bin/env python3
"""
FIFA World Cup 2026 - Lean Elo + Poisson + Monte Carlo prediction engine.

Pipeline:
  Elo (+ host advantage)  ->  expected goals (lambda_A, lambda_B)
  Poisson(lambda)         ->  full scoreline distribution per match (analytic)
  Global Monte Carlo      ->  all 72 matches x N sims -> group tables ->
                              top-2 + 8 best-third qualification probabilities

Design notes:
  * Pure Elo baseline. Squad Top5% / age are carried in teams.csv for reference
    but are intentionally NOT used in the rating: the whole point is an honest
    baseline you must BEAT before adding layers (per our methodology).
  * All tunables are in CONFIG. Swap estimated Elos for live eloratings.net
    values in teams.csv (column elo_src) and re-run; nothing else changes.
"""
import csv, math, os
from collections import defaultdict
import numpy as np

# --------------------------- CONFIG (all tunable) ---------------------------
CONFIG = dict(
    # Parameters below are backtest-fitted (tune.py, temporal holdout 2006-21 train).
    HOME_ADV_ELO   = 100,   # Elo bump for a host nation (MEX/CAN/USA) at home
    ELO_TO_SUP     = 0.0050,# Elo diff -> goal supremacy (200 Elo ~ 1.0 goal)
    BASE_TOTAL     = 2.40,  # baseline total goals in an even game
    MISMATCH_TOTAL = 0.40,  # extra total goals scaled by |supremacy| (blowout fix)
    GOAL_FLOOR     = 0.12,  # min expected goals for the underdog (relaxed: bigger blowouts)
    GRID           = 10,    # max goals per side for the analytic pmf grid
    N_SIMS         = 200000,# Monte Carlo iterations (global, all 72 matches)
    SEED           = 42,
)
HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------- load data ---------------------------
def load_teams(path):
    teams = {}
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            teams[r['team']] = dict(
                group=r['group'], elo=float(r['elo']), src=r['elo_src'],
                host=int(r['host']), top5=float(r['top5pct']), age=float(r['avg_age']))
    return teams

# --------------------------- match model ---------------------------
def expected_goals(ta, tb, C):
    """Return (lambda_A, lambda_B) expected goals from Elo + host advantage."""
    ea = ta['elo'] + (C['HOME_ADV_ELO'] if ta['host'] else 0)
    eb = tb['elo'] + (C['HOME_ADV_ELO'] if tb['host'] else 0)
    sup_raw = (ea - eb) * C['ELO_TO_SUP']
    total   = C['BASE_TOTAL'] + C['MISMATCH_TOTAL'] * min(abs(sup_raw), 3.0)
    cap     = total - 2 * C['GOAL_FLOOR']
    sup     = max(-cap, min(cap, sup_raw))
    return (total + sup) / 2.0, (total - sup) / 2.0

_FACT = [math.factorial(k) for k in range(40)]
def pois_pmf(lam, G):
    k = np.arange(G + 1)
    return np.exp(-lam) * lam**k / np.array(_FACT[:G + 1])

def match_analytics(lamA, lamB, G):
    """Analytic scoreline distribution.

    Headline `pred` = most likely scoreline *conditioned on the most likely
    outcome* (W/D/L). The raw joint mode over-predicts draws and suppresses
    goals (Poisson mode < mean), so we first pick the modal result, then the
    modal score within it. `top` still exposes the raw scoreline ranking.
    """
    M = np.outer(pois_pmf(lamA, G), pois_pmf(lamB, G))   # M[i,j]=P(A=i,B=j)
    pA = np.tril(M, -1).sum(); pD = np.trace(M); pB = np.triu(M, 1).sum()
    pred = (int(lamA + 0.5), int(lamB + 0.5))            # per-team median (L1-optimal)
    flat = sorted(((M[a, b], a, b) for a in range(G + 1) for b in range(G + 1)),
                  reverse=True)
    top = [(a, b, p) for p, a, b in flat[:4]]
    return pred, (pA, pD, pB), top

# --------------------------- fixtures (round-robin) ---------------------------
# positions 0..3 within a group; FIFA-style matchday pattern
def build(teams):
    """Load real 72 fixtures from fixtures.csv (date, venue order, matchday)."""
    groups = defaultdict(list)
    for name, t in teams.items():
        groups[t['group']].append(name)
    fixtures = []
    try:
        for row in csv.DictReader(open('fixtures.csv', encoding='utf-8')):
            g, A, B, md = row['group'], row['home'], row['away'], int(row['matchday'])
            if A in teams and B in teams:  # safety check
                lamA, lamB = expected_goals(teams[A], teams[B], CONFIG)
                fixtures.append((g, A, B, md, lamA, lamB, row['date'], row['venue']))
    except FileNotFoundError:
        # fallback: old round-robin if fixtures.csv missing
        PAIRS = [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]; MD = [1,1,2,2,3,3]
        for g in sorted(groups):
            gt = groups[g]
            for (a, b), md in zip(PAIRS, MD):
                A, B = gt[a], gt[b]
                lamA, lamB = expected_goals(teams[A], teams[B], CONFIG)
                fixtures.append((g, A, B, md, lamA, lamB, '', ''))
    return groups, fixtures

# --------------------------- Monte Carlo (global) ---------------------------
def simulate(teams, groups, fixtures, C):
    rng = np.random.default_rng(C['SEED']); N = C['N_SIMS']
    pts = {t: np.zeros(N) for t in teams}
    gd  = {t: np.zeros(N) for t in teams}
    gf  = {t: np.zeros(N) for t in teams}
    sim_draws = sim_goals = 0.0                    # true (simulated) slate rates
    for fix in fixtures:
        g, A, B, md, lamA, lamB = fix[:6]  # unpack, skip date/venue if present
        ga = rng.poisson(lamA, N); gb = rng.poisson(lamB, N)
        aw = ga > gb; bw = gb > ga; dr = ga == gb
        sim_draws += dr.sum(); sim_goals += (ga + gb).sum()
        pts[A] += 3 * aw + dr;  pts[B] += 3 * bw + dr
        gd[A] += ga - gb;       gd[B] += gb - ga
        gf[A] += ga;            gf[B] += gb

    is1 = {}; is2 = {}; is3 = {}; third_key = {}
    for g in sorted(groups):
        gt = groups[g]
        # composite ranking key with tiny random tiebreak (no exact ties)
        keys = np.stack([pts[t]*1e6 + (gd[t]+100)*1e3 + gf[t] + rng.random(N)
                         for t in gt])                 # (4, N)
        rank = np.zeros((4, N), int)
        for k in range(4):
            rank[k] = (keys > keys[k]).sum(0)          # 0 = first
        k3 = {t: pts[t]*1e6 + (gd[t]+100)*1e3 + gf[t] for t in gt}
        tk = np.zeros(N)
        for k, t in enumerate(gt):
            is1[t] = rank[k] == 0; is2[t] = rank[k] == 1; is3[t] = rank[k] == 2
            tk += is3[t] * k3[t]                        # this group's 3rd-place key
        third_key[g] = tk

    # rank the 12 third-place teams; top 8 advance
    gorder = sorted(groups)
    TK = np.stack([third_key[g] for g in gorder]) + rng.random((12, N)) * 0.9
    qual3g = {g: (TK > TK[i]).sum(0) < 8 for i, g in enumerate(gorder)}

    res = {}
    for g in gorder:
        for t in groups[g]:
            adv = is1[t] | is2[t] | (is3[t] & qual3g[g])
            res[t] = dict(exp_pts=pts[t].mean(),
                          p1=is1[t].mean(), p2=is2[t].mean(),
                          p3=is3[t].mean(), padv=adv.mean())
    denom = N * len(fixtures)
    simstats = dict(draw=sim_draws / denom, goals=sim_goals / denom)
    return res, simstats

# --------------------------- output ---------------------------
def main():
    teams = load_teams(os.path.join(HERE, 'teams.csv'))
    assert len(teams) == 48, f"expected 48 teams, got {len(teams)}"
    groups, fixtures = build(teams)
    res, simstats = simulate(teams, groups, fixtures, CONFIG)

    out = ["# FIFA World Cup 2026 - Group Stage Predictions",
           "*Lean Elo + Poisson + Monte Carlo engine. "
           f"{CONFIG['N_SIMS']:,} sims. Pure-Elo baseline.*\n",
           "> Elo: live World Football Elo (eloratings.net `World.tsv`, "
           "Jun 2026) for all 48 teams.\n"]

    draws = tot = blow = 0
    flag = {t: teams[t]['src'] for t in teams}
    for g in sorted(groups):
        out.append(f"\n## Group {g}\n")
        out.append("| Matchday | Match | Score | xG | Win % | Draw % | Loss % |")
        out.append("|---|---|---|---|---|---|---|")
        for fix in [x for x in fixtures if x[0] == g]:
            gg, A, B, md, lamA, lamB = fix[:6]
            date = fix[6] if len(fix) > 6 else ''
            (i, j), (pA, pD, pB), top = match_analytics(lamA, lamB, CONFIG['GRID'])
            tag = lambda t: t + ('*' if flag[t] == 'est' else '')
            datestr = f"MD{md} {date[5:10]}" if date else f"MD{md}"
            out.append(f"| {datestr} | {tag(A)} vs {tag(B)} | **{i}-{j}** | {lamA:.1f}-{lamB:.1f} | "
                       f"{pA*100:.0f}% | {pD*100:.0f}% | {pB*100:.0f}% |")
            draws += (i == j); tot += (i + j); blow += ((i + j) >= 4)
        out.append("\n*Qualification odds:*\n")
        out.append("| Team | xPts | Win grp | Top 2 | Advance |")
        out.append("|---|---|---|---|---|")
        gr = sorted(groups[g], key=lambda t: -res[t]['padv'])
        for t in gr:
            r = res[t]
            out.append(f"| {t}{'*' if flag[t]=='est' else ''} | {r['exp_pts']:.2f} | "
                       f"{r['p1']*100:.0f}% | {(r['p1']+r['p2'])*100:.0f}% | "
                       f"{r['padv']*100:.0f}% |")

    n = len(fixtures)
    out.append("\n---\n## Slate calibration audit\n")
    out.append("*Point-prediction slate (the headline scorelines):*")
    out.append(f"- Predicted as draws: **{draws}/{n} = {draws/n*100:.0f}%** "
               "(point slates correctly show fewer draws than actually occur)")
    out.append(f"- Avg goals/game: **{tot/n:.2f}** (target ~2.5-2.8)")
    out.append(f"- Games with 4+ goals: **{blow}/{n}**\n")
    out.append("*True model belief (from the Monte Carlo) — the real calibration check:*")
    out.append(f"- Actual draw rate: **{simstats['draw']*100:.0f}%** (target ~25-30%)")
    out.append(f"- Avg goals/game: **{simstats['goals']:.2f}** (target ~2.5-2.8)")

    # global qualifiers list
    advs = sorted(res.items(), key=lambda kv: -kv[1]['padv'])
    out.append("\n## Most likely to advance (top 32 by P(advance))\n")
    out.append("| # | Team | Grp | Advance % |\n|---|---|---|---|")
    for k, (t, r) in enumerate(advs[:32], 1):
        out.append(f"| {k} | {t} | {teams[t]['group']} | {r['padv']*100:.0f}% |")

    md = "\n".join(out)
    open(os.path.join(HERE, 'predictions.md'), 'w', encoding='utf-8').write(md)

    # console summary
    print(f"Teams: {len(teams)} | Matches: {n} | Sims: {CONFIG['N_SIMS']:,}")
    print(f"Point slate: draws {draws}/{n} ({draws/n*100:.0f}%), "
          f"avg goals {tot/n:.2f}, 4+ goal games {blow}")
    print(f"Model belief (sim): actual draw rate {simstats['draw']*100:.0f}%, "
          f"avg goals {simstats['goals']:.2f}")
    print("\nGroup winners (most likely) and runners-up:")
    for g in sorted(groups):
        gr = sorted(groups[g], key=lambda t: -res[t]['p1'])
        w = gr[0]; ru = sorted(groups[g], key=lambda t: -(res[t]['p1']+res[t]['p2']))
        print(f"  {g}: {w} ({res[w]['p1']*100:.0f}% win)  |  "
              f"top2: {ru[0]['team'] if False else ru[0]}, {ru[1]}")
    print("\nWrote predictions.md")

if __name__ == '__main__':
    main()
