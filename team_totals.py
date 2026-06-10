#!/usr/bin/env python3
"""Expected games played and goals scored per team across the WHOLE tournament
(group + full knockout bracket with simulated scorelines)."""
import math, random
import numpy as np
from wc2026_model import load_teams, build, CONFIG

N = 80000
random.seed(7)
HA=CONFIG['HOME_ADV_ELO']; SUP=CONFIG['ELO_TO_SUP']
BASE=CONFIG['BASE_TOTAL']; MIS=CONFIG['MISMATCH_TOTAL']; FLOOR=CONFIG['GOAL_FLOOR']

SLOT_ALLOWED={'T74':set('ABCDF'),'T77':set('CDFGH'),'T79':set('CEFHI'),'T80':set('EHIJK'),
              'T81':set('BEFIJ'),'T82':set('AEHIJ'),'T85':set('EFGIJ'),'T87':set('DEIJL')}
R32=[(73,'R_A','R_B'),(74,'W_E','T74'),(75,'W_F','R_C'),(76,'W_C','R_F'),
     (77,'W_I','T77'),(78,'R_E','R_I'),(79,'W_A','T79'),(80,'W_L','T80'),
     (81,'W_D','T81'),(82,'W_G','T82'),(83,'R_K','R_L'),(84,'W_H','R_J'),
     (85,'W_B','T85'),(86,'W_J','R_H'),(87,'W_K','T87'),(88,'R_D','R_G')]
LATER=[(89,74,77),(90,73,75),(91,76,78),(92,79,80),(93,83,84),(94,81,82),
       (95,86,88),(96,85,87),(97,89,90),(98,93,94),(99,91,92),(100,95,96),
       (101,97,98),(102,99,100),(104,101,102)]
RND={**{m:'R32' for m in range(73,89)},**{m:'R16' for m in range(89,97)},
     **{m:'QF' for m in range(97,101)},101:'SF',102:'SF',104:'F'}

def match_thirds(quali):
    M={}
    def aug(slot,vis):
        for L in SLOT_ALLOWED[slot]:
            if L in quali and L not in vis:
                vis.add(L)
                if L not in M or aug(M[L],vis): M[L]=slot; return True
        return False
    for slot in SLOT_ALLOWED: aug(slot,set())
    return {s:L for L,s in M.items()}

def pois(lam):                                   # Knuth, fast for small lambda
    L=math.exp(-lam); k=0; p=1.0
    while True:
        k+=1; p*=random.random()
        if p<=L: return k-1

def main():
    teams=load_teams('teams.csv'); groups,fixtures=build(teams)
    names=list(teams); idx={n:i for i,n in enumerate(names)}
    elo=[teams[n]['elo'] for n in names]; host=[teams[n]['host'] for n in names]
    T=len(names); rng=np.random.default_rng(7); GL=sorted(groups)

    # ---- group stage (vectorised) ----
    pts=np.zeros((T,N)); gd=np.zeros((T,N)); gf=np.zeros((T,N))
    for fix in fixtures:
        ai,bi=idx[fix[1]],idx[fix[2]]
        ga=rng.poisson(fix[4],N); gb=rng.poisson(fix[5],N)
        pts[ai]+=3*(ga>gb)+(ga==gb); pts[bi]+=3*(gb>ga)+(ga==gb)
        gd[ai]+=ga-gb; gd[bi]+=gb-ga; gf[ai]+=ga; gf[bi]+=gb
    ar=np.arange(N); W={};Rk={};Th={};TK={}
    for g in GL:
        ids=np.array([idx[n] for n in groups[g]])
        keys=np.stack([pts[i]*1e6+(gd[i]+100)*1e3+gf[i]+rng.random(N) for i in ids])
        o=np.argsort(-keys,axis=0); W[g]=ids[o[0]];Rk[g]=ids[o[1]];Th[g]=ids[o[2]]
        t=Th[g]; TK[g]=pts[t,ar]*1e6+(gd[t,ar]+100)*1e3+gf[t,ar]+rng.random(N)*0.4
    TKs=np.stack([TK[g] for g in GL]); qual=np.stack([(TKs>TKs[i]).sum(0)<8 for i in range(12)])
    Wl={g:W[g].astype(int).tolist() for g in GL}; Rl={g:Rk[g].astype(int).tolist() for g in GL}
    Tl={g:Th[g].astype(int).tolist() for g in GL}; ql=[qual[i].tolist() for i in range(12)]

    goals=gf.sum(1).astype(float)              # group goals per team (summed over sims)
    games=np.full(T,3.0*N)                     # everyone plays 3 group games
    reach={r:np.zeros(T) for r in ('R32','R16','QF','SF','F')}

    def play(a,b):                             # knockout: scores count, ties -> Elo
        eA=elo[a]; eB=elo[b]; sup=(eA-eB)*SUP
        tot=BASE+MIS*min(abs(sup),3.0); c=tot-2*FLOOR; sup=max(-c,min(c,sup))
        ga=pois((tot+sup)/2); gb=pois((tot-sup)/2)
        goals[a]+=ga; goals[b]+=gb; games[a]+=1; games[b]+=1
        if ga>gb: return a,b
        if gb>ga: return b,a
        return (a,b) if random.random()<1/(1+10**((eB-eA)/400)) else (b,a)

    for s in range(N):
        slot={}
        for g in GL: slot['W_'+g]=Wl[g][s]; slot['R_'+g]=Rl[g][s]
        for sid,Lg in match_thirds({GL[i] for i in range(12) if ql[i][s]}).items():
            slot[sid]=Tl[Lg][s]
        win={}; lose={}
        for mid,l,r in R32:
            a,b=slot[l],slot[r]; reach['R32'][a]+=1; reach['R32'][b]+=1
            win[mid],lose[mid]=play(a,b)
        for mid,l,r in LATER:
            a,b=win[l],win[r]; reach[RND[mid]][a]+=1; reach[RND[mid]][b]+=1
            win[mid],lose[mid]=play(a,b)
        # 3rd-place playoff (SF losers) — counts as a real game/goals
        play(lose[101],lose[102])

    eg=goals/N; egames=games/N
    def row(n):
        i=idx[n]
        return (f"{n:<13} games {egames[i]:.2f}  goals {eg[i]:.2f} | "
                f"reach R16 {reach['R16'][i]/N*100:.0f}%  QF {reach['QF'][i]/N*100:.0f}%  "
                f"SF {reach['SF'][i]/N*100:.0f}%  Final {reach['F'][i]/N*100:.0f}%")
    print(f"Expected games & goals per team ({N:,} sims, full tournament)\n")
    print("--- Norway (Haaland) ---"); print(row('Norway'))
    print("\n--- context ---")
    for n in ['Spain','Argentina','France','England','Brazil','Portugal']:
        print(row(n))
    # Norway group-only goals check
    print(f"\nNorway group-stage goals only: {gf[idx['Norway']].mean():.2f} "
          f"(over {3} games); knockout adds {eg[idx['Norway']]-gf[idx['Norway']].mean():.2f}")

if __name__=='__main__':
    main()
