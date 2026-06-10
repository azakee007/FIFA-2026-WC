#!/usr/bin/env python3
"""
Champion predictor with RATING UNCERTAINTY.

Each simulation samples every team's "true" strength once, as Elo + N(0, sigma),
held FIXED across that team's whole tournament (group + knockout). This injects
the correlated uncertainty the single-match model can't see ("is this team really
this good?"), which pulls favourites toward the field and matches market realism.
The per-match Elo expectancy still handles independent single-game variance.

sigma is the one judgement knob; we sweep it and anchor to the betting-market
consensus for the favourite (~16-18%).
"""
import math, random
import numpy as np
from wc2026_model import load_teams, build, CONFIG

N = 60000
HA = CONFIG['HOME_ADV_ELO']; SUP = CONFIG['ELO_TO_SUP']
BASE = CONFIG['BASE_TOTAL']; MIS = CONFIG['MISMATCH_TOTAL']; FLOOR = CONFIG['GOAL_FLOOR']

SLOT_ALLOWED = {'T74':set('ABCDF'),'T77':set('CDFGH'),'T79':set('CEFHI'),'T80':set('EHIJK'),
                'T81':set('BEFIJ'),'T82':set('AEHIJ'),'T85':set('EFGIJ'),'T87':set('DEIJL')}
R32 = [(73,'R_A','R_B'),(74,'W_E','T74'),(75,'W_F','R_C'),(76,'W_C','R_F'),
       (77,'W_I','T77'),(78,'R_E','R_I'),(79,'W_A','T79'),(80,'W_L','T80'),
       (81,'W_D','T81'),(82,'W_G','T82'),(83,'R_K','R_L'),(84,'W_H','R_J'),
       (85,'W_B','T85'),(86,'W_J','R_H'),(87,'W_K','T87'),(88,'R_D','R_G')]
LATER = [(89,74,77),(90,73,75),(91,76,78),(92,79,80),(93,83,84),(94,81,82),
         (95,86,88),(96,85,87),(97,89,90),(98,93,94),(99,91,92),(100,95,96),
         (101,97,98),(102,99,100),(104,101,102)]

def match_thirds(quali):
    matchL = {}
    def aug(slot, vis):
        for L in SLOT_ALLOWED[slot]:
            if L in quali and L not in vis:
                vis.add(L)
                if L not in matchL or aug(matchL[L], vis):
                    matchL[L] = slot; return True
        return False
    for slot in SLOT_ALLOWED:
        aug(slot, set())
    return {slot: L for L, slot in matchL.items()}

def run(sigma, teams, groups, fixtures, names, idx, elo, host, seed=7):
    T = len(names); rng = np.random.default_rng(seed); GL = sorted(groups)
    offset = rng.normal(0, sigma, (T, N)) if sigma > 0 else np.zeros((T, N))
    ee = elo[:, None] + offset                                   # (T,N) true strength

    pts = np.zeros((T, N)); gd = np.zeros((T, N)); gf = np.zeros((T, N))
    for fix in fixtures:
        ai, bi = idx[fix[1]], idx[fix[2]]
        eh = ee[ai] + (HA if host[ai] else 0); ea = ee[bi] + (HA if host[bi] else 0)
        sup = (eh - ea) * SUP
        total = BASE + MIS * np.minimum(np.abs(sup), 3.0)
        sup = np.clip(sup, -(total-2*FLOOR), total-2*FLOOR)
        ga = rng.poisson((total+sup)/2); gb = rng.poisson((total-sup)/2)
        pts[ai]+=3*(ga>gb)+(ga==gb); pts[bi]+=3*(gb>ga)+(ga==gb)
        gd[ai]+=ga-gb; gd[bi]+=gb-ga; gf[ai]+=ga; gf[bi]+=gb

    ar = np.arange(N); W={}; Rk={}; Th={}; TK={}
    for g in GL:
        ids = np.array([idx[n] for n in groups[g]])
        keys = np.stack([pts[i]*1e6+(gd[i]+100)*1e3+gf[i]+rng.random(N) for i in ids])
        o = np.argsort(-keys, axis=0)
        W[g]=ids[o[0]]; Rk[g]=ids[o[1]]; Th[g]=ids[o[2]]
        t = Th[g]; TK[g] = pts[t,ar]*1e6+(gd[t,ar]+100)*1e3+gf[t,ar]+rng.random(N)*0.4
    TKs = np.stack([TK[g] for g in GL])
    qual = np.stack([(TKs > TKs[i]).sum(0) < 8 for i in range(12)])

    Wl={g:W[g].astype(int).tolist() for g in GL}; Rl={g:Rk[g].astype(int).tolist() for g in GL}
    Tl={g:Th[g].astype(int).tolist() for g in GL}; ql=[qual[i].tolist() for i in range(12)]
    EE = ee.T.tolist()                                            # (N,T) per-sim strengths
    champ=[0]*T; final=[0]*T; semi=[0]*T
    for s in range(N):
        e = EE[s]
        def ko(a, b):
            return a if random.random() < 1.0/(1.0+10**((e[b]-e[a])/400)) else b
        slot = {}
        for g in GL: slot['W_'+g]=Wl[g][s]; slot['R_'+g]=Rl[g][s]
        for sid, Lg in match_thirds({GL[i] for i in range(12) if ql[i][s]}).items():
            slot[sid] = Tl[Lg][s]
        win = {}
        for mid,l,r in R32:   win[mid]=ko(slot[l], slot[r])
        for mid,l,r in LATER: win[mid]=ko(win[l], win[r])
        champ[win[104]]+=1; final[win[101]]+=1; final[win[102]]+=1
        for m in (97,98,99,100): semi[win[m]]+=1
    return (np.array(champ)/N, np.array(final)/N, np.array(semi)/N)

def main():
    random.seed(7)
    teams = load_teams('teams.csv'); groups, fixtures = build(teams)
    names = list(teams); idx = {n:i for i,n in enumerate(names)}
    elo = np.array([teams[n]['elo'] for n in names]); host = np.array([teams[n]['host'] for n in names])
    args = (teams, groups, fixtures, names, idx, elo, host)

    sigmas = [0, 40, 60, 80, 100]
    res = {sg: run(sg, *args) for sg in sigmas}
    fav = idx[max(names, key=lambda n: elo[idx[n]])]              # highest-Elo team
    top = sorted(range(len(names)), key=lambda i: -res[0][0][i])[:12]

    print(f"Rating-uncertainty sweep ({N:,} sims). Champion % by sigma (Elo points):\n")
    print(f"{'Team':<13}" + "".join(f"σ={s:<5}" for s in sigmas))
    print("-"*52)
    for i in top:
        print(f"{names[i]:<13}" + "".join(f"{res[s][0][i]*100:>6.1f}" for s in sigmas))
    print("\nFavourite (%s) by sigma: " % names[fav]
          + ", ".join(f"σ{s}:{res[s][0][fav]*100:.1f}%" for s in sigmas))

    # anchor: pick sigma whose favourite is closest to 17% (market consensus)
    pick = min(sigmas, key=lambda s: abs(res[s][0][fav]-0.17))
    champ, final, semi = res[pick]
    order = sorted(range(len(names)), key=lambda i:-champ[i])
    print(f"\n=== Anchored to market: sigma={pick} (favourite {champ[fav]*100:.1f}%) ===\n")
    print(f"{'Team':<14}{'Champion':>10}{'Final':>9}{'Semi':>8}")
    for i in order[:16]:
        if champ[i] < 0.002: break
        print(f"{names[i]:<14}{champ[i]*100:>9.1f}%{final[i]*100:>8.1f}%{semi[i]*100:>7.1f}%")

    out = ["# FIFA World Cup 2026 - Champion Prediction (with rating uncertainty)",
           f"*Real-bracket knockout Monte Carlo, {N:,} sims. Rating uncertainty "
           f"sigma={pick} Elo (anchored to market). Neutral knockout venues.*\n",
           "| Rank | Team | Champion | Reach Final | Reach Semi |", "|---|---|---|---|---|"]
    for k,i in enumerate(order[:24],1):
        if champ[i] < 0.002: break
        out.append(f"| {k} | {names[i]} | {champ[i]*100:.1f}% | {final[i]*100:.1f}% | {semi[i]*100:.1f}% |")
    open('champion.md','w').write("\n".join(out))
    print("\nWrote champion.md")

if __name__ == '__main__':
    main()
