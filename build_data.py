#!/usr/bin/env python3
"""Generate wc_site/data.js for the predictions webpage.
Pulls everything from the model: deterministic group standings + scorelines
(median scoreline per match), best-third resolution, sim-based advance odds,
champion odds (champion.md), and a transparent top-scorer projection."""
import json, math, random, re, os
import numpy as np
from collections import defaultdict
from wc2026_model import (load_teams, build, match_analytics, simulate, CONFIG)

HERE = os.path.dirname(os.path.abspath(__file__))
GRID = CONFIG['GRID']

# ---- knockout bracket (for expected tournament goals -> scorer projection) ----
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
    M = {}
    def aug(slot, vis):
        for L in SLOT_ALLOWED[slot]:
            if L in quali and L not in vis:
                vis.add(L)
                if L not in M or aug(M[L], vis): M[L] = slot; return True
        return False
    for slot in SLOT_ALLOWED: aug(slot, set())
    return {s: L for L, s in M.items()}

def pois(lam):
    L = math.exp(-lam); k = 0; p = 1.0
    while True:
        k += 1; p *= random.random()
        if p <= L: return k - 1

def expected_goals_per_team(teams, groups, fixtures, N=15000):
    """Expected goals scored per team across the whole tournament (group + KO)."""
    HA=CONFIG['HOME_ADV_ELO']; SUP=CONFIG['ELO_TO_SUP']
    BASE=CONFIG['BASE_TOTAL']; MIS=CONFIG['MISMATCH_TOTAL']; FLOOR=CONFIG['GOAL_FLOOR']
    names=list(teams); idx={n:i for i,n in enumerate(names)}
    elo=[teams[n]['elo'] for n in names]; host=[teams[n]['host'] for n in names]
    T=len(names); rng=np.random.default_rng(7); GL=sorted(groups); random.seed(7)
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
    goals=gf.sum(1).astype(float)
    def play(a,b):
        sup=(elo[a]-elo[b])*SUP; tot=BASE+MIS*min(abs(sup),3.0)
        c=tot-2*FLOOR; sup=max(-c,min(c,sup))
        ga=pois((tot+sup)/2); gb=pois((tot-sup)/2)
        goals[a]+=ga; goals[b]+=gb
        if ga>gb: return a,b
        if gb>ga: return b,a
        return (a,b) if random.random()<1/(1+10**((elo[b]-elo[a])/400)) else (b,a)
    for s in range(N):
        slot={}
        for g in GL: slot['W_'+g]=Wl[g][s]; slot['R_'+g]=Rl[g][s]
        for sid,Lg in match_thirds({GL[i] for i in range(12) if ql[i][s]}).items():
            slot[sid]=Tl[Lg][s]
        win={}; lose={}
        for mid,l,r in R32: win[mid],lose[mid]=play(slot[l],slot[r])
        for mid,l,r in LATER: win[mid],lose[mid]=play(win[l],win[r])
        play(lose[101],lose[102])
    return {names[i]: goals[i]/N for i in range(T)}

# transparent striker map: team -> (display name, share of team goals)
STRIKER = {
    'France':('Kylian Mbappé',0.46),'Norway':('Erling Haaland',0.56),'England':('Harry Kane',0.44),
    'Argentina':('Lautaro Martínez',0.38),'Egypt':('Mohamed Salah',0.52),'Belgium':('Romelu Lukaku',0.44),
    'Spain':('Lamine Yamal',0.34),'Portugal':('Cristiano Ronaldo',0.40),'Brazil':('Vinícius Júnior',0.34),
    'Colombia':('Luis Díaz',0.40),'Netherlands':('Cody Gakpo',0.34),'Uruguay':('Darwin Núñez',0.42),
    'Germany':('Florian Wirtz',0.28),'Ecuador':('Enner Valencia',0.42),'Mexico':('Raúl Jiménez',0.40),
    'Croatia':('Andrej Kramarić',0.30),'Switzerland':('Breel Embolo',0.34),'Japan':('Kaoru Mitoma',0.26),
    'Morocco':('Youssef En-Nesyri',0.40),'USA':('Folarin Balogun',0.34),'Senegal':('Nicolas Jackson',0.36),
    'Iran':('Mehdi Taremi',0.46),'Canada':('Jonathan David',0.44),'Uzbekistan':('Eldor Shomurodov',0.42),
}
RESULT_RANK = {'Q':0,'Q3':1,'OUT':2}

def main():
    teams = load_teams(os.path.join(HERE,'teams.csv'))
    groups, fixtures = build(teams)
    res, simstats = simulate(teams, groups, fixtures, CONFIG)

    gdata = {}; draws = tot = ngames = 0
    for g in sorted(groups):
        tally = {t: dict(team=t,p=0,w=0,d=0,l=0,gf=0,ga=0,pts=0) for t in groups[g]}
        fx = []
        for fixture in [x for x in fixtures if x[0]==g]:
            _,A,B,md,lamA,lamB = fixture[:6]
            date = fixture[6] if len(fixture)>6 else ''
            (i,j),(pA,pD,pB),_ = match_analytics(lamA,lamB,GRID)
            i,j = int(i),int(j)
            fx.append(dict(md=md,date=date[5:] if date else '',home=A,away=B,hs=i,as_=j,
                           wp=round(pA*100),dp=round(pD*100),lp=round(pB*100),
                           xgh=round(lamA,1),xga=round(lamB,1)))
            for T,gfv,gav in ((A,i,j),(B,j,i)):
                tally[T]['p']+=1; tally[T]['gf']+=gfv; tally[T]['ga']+=gav
            if i>j:   tally[A]['w']+=1; tally[A]['pts']+=3; tally[B]['l']+=1
            elif j>i: tally[B]['w']+=1; tally[B]['pts']+=3; tally[A]['l']+=1
            else:     tally[A]['d']+=1; tally[B]['d']+=1; tally[A]['pts']+=1; tally[B]['pts']+=1
            draws += (i==j); tot += i+j; ngames += 1
        standings = list(tally.values())
        for d in standings:
            d['gd']=d['gf']-d['ga']; d['padv']=round(res[d['team']]['padv']*100)
        standings.sort(key=lambda d:(-d['pts'],-d['gd'],-d['gf'],-res[d['team']]['padv']))
        gdata[g] = dict(standings=standings, fixtures=fx)

    # best-third resolution across the 12 groups
    thirds = [(g, gdata[g]['standings'][2]) for g in sorted(groups)]
    thirds.sort(key=lambda gs:(-gs[1]['pts'],-gs[1]['gd'],-gs[1]['gf'],-res[gs[1]['team']]['padv']))
    adv = {g for g,_ in thirds[:8]}
    for g in sorted(groups):
        for pos,d in enumerate(gdata[g]['standings']):
            d['pos']=pos+1
            d['result']='Q' if pos<2 else ('Q3' if (pos==2 and g in adv) else 'OUT')

    # champion odds from champion.md
    champ_rows=[]
    cpath=os.path.join(HERE,'champion.md'); sigma=None
    if os.path.exists(cpath):
        for line in open(cpath, encoding='utf-8'):
            ms=re.search(r'sigma=(\d+)', line)
            if ms: sigma=int(ms.group(1))
            m=re.match(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)%\s*\|',line)
            if m: champ_rows.append(dict(rank=int(m.group(1)),team=m.group(2).strip(),
                  champ=float(m.group(3)),final=float(m.group(4)),semi=float(m.group(5))))

    # scorer projection: team expected tournament goals x striker share, scaled to a
    # realistic golden-boot range (leader ~7). Transparent heuristic, not a fitted model.
    eg = expected_goals_per_team(teams, groups, fixtures)
    proj=[]
    for team,(player,share) in STRIKER.items():
        proj.append(dict(player=player,team=team,share=share,raw=eg[team]*share))
    proj.sort(key=lambda p:-p['raw'])
    scale = 7.0/proj[0]['raw']
    for p in proj: p['goals']=round(p['raw']*scale,1)
    scorers=[dict(rank=k+1,player=p['player'],team=p['team'],goals=p['goals'],
                  share=round(p['share']*100)) for k,p in enumerate(proj[:6])]

    DATA = dict(
        champion=champ_rows[0] if champ_rows else None,
        titleRace=champ_rows[:8],
        scorers=scorers,
        groups=gdata,
        meta=dict(sims=CONFIG['N_SIMS'], champSigma=sigma,
                  draws=draws, ngames=ngames, goalsPerGame=round(tot/ngames,2),
                  simDraw=round(simstats['draw']*100), simGoals=round(simstats['goals'],2)),
    )
    os.makedirs(os.path.join(HERE,'wc_site'), exist_ok=True)
    with open(os.path.join(HERE,'wc_site','data.js'),'w',encoding='utf-8') as f:
        f.write('window.WC = ' + json.dumps(DATA, ensure_ascii=False, indent=1) + ';\n')
    print(f"champion: {DATA['champion']['team']} {DATA['champion']['champ']}%  (sigma={sigma})")
    print("top scorer:", scorers[0]['player'], scorers[0]['goals'])
    print("groups:", len(gdata), "| wrote wc_site/data.js")

if __name__ == '__main__':
    main()
