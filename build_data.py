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
    """Expected goals per team across the whole tournament (group + KO).
    Returns (eg, tg, idx): eg = {team: mean tournament goals}, tg = the per-sim
    (T, N) goal matrix (so the Golden-Boot sim can see each team's actual output
    in each simulated run, not just the mean), idx = {team: row in tg}."""
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
    tg=gf.copy()                       # (T, N) total tournament goals per team per sim
    def play(a,b,s):
        sup=(elo[a]-elo[b])*SUP; tot=BASE+MIS*min(abs(sup),3.0)
        c=tot-2*FLOOR; sup=max(-c,min(c,sup))
        ga=pois((tot+sup)/2); gb=pois((tot-sup)/2)
        tg[a,s]+=ga; tg[b,s]+=gb
        if ga>gb: return a,b
        if gb>ga: return b,a
        return (a,b) if random.random()<1/(1+10**((elo[b]-elo[a])/400)) else (b,a)
    for s in range(N):
        slot={}
        for g in GL: slot['W_'+g]=Wl[g][s]; slot['R_'+g]=Rl[g][s]
        for sid,Lg in match_thirds({GL[i] for i in range(12) if ql[i][s]}).items():
            slot[sid]=Tl[Lg][s]
        win={}; lose={}
        for mid,l,r in R32: win[mid],lose[mid]=play(slot[l],slot[r],s)
        for mid,l,r in LATER: win[mid],lose[mid]=play(win[l],win[r],s)
        play(lose[101],lose[102],s)
    return {names[i]: tg[i].mean() for i in range(T)}, tg, idx

# ---- 3-channel attack model -------------------------------------------------
# A team's expected goals split into three sources that distribute very
# differently among players:
#   * open play  -> SPREAD across the named attackers by role (op-share below).
#   * penalties  -> CONCENTRATED on the one designated taker.
#   * direct FKs -> CONCENTRATED on the one designated free-kick specialist.
# That concentration is exactly why penalty/FK takers (Kane, Salah, Messi...)
# out-score equally good strikers who don't take them.
#
# Channel fractions are VAR-era World Cup priors (penalties ~8-12% of goals,
# direct FKs ~1.5-2%). eg[team] is already realised goals, so conversion is
# baked in -- these are shares of GOALS, not of attempts.
PEN_FRAC = 0.10    # share of a team's goals scored from the penalty spot
FK_FRAC  = 0.015   # share scored from direct free kicks

# team -> dict(op=[(player, open-play share of team goals), ...] (sums <1; the
#              remainder is non-talisman squad goals + own goals),
#              pen = penalty taker  (str, or [(player, weight), ...] to split),
#              fk  = free-kick taker (str, or None)).
# op-shares + the set-piece fractions assigned sum to <1 per team.
# ROLE / TAKER ASSIGNMENTS ARE ANALYST PRIORS -- the match-RPS backtest cannot
# see individual goals -- so the page discloses the scorer block with a '†'.
SCORERS = {
 'France':dict(op=[('Kylian Mbappé',0.30),('Marcus Thuram',0.16),('Michael Olise',0.12),('Ousmane Dembélé',0.10)],
               pen='Kylian Mbappé', fk='Kylian Mbappé'),
 'Argentina':dict(op=[('Lautaro Martínez',0.26),('Lionel Messi',0.15),('Julián Álvarez',0.19)],
               pen='Lionel Messi', fk='Lionel Messi'),
 'Spain':dict(op=[('Lamine Yamal',0.22),('Mikel Oyarzabal',0.11),('Dani Olmo',0.16),('Álvaro Morata',0.12)],
               pen='Mikel Oyarzabal', fk='Lamine Yamal'),
 'England':dict(op=[('Harry Kane',0.32),('Jude Bellingham',0.15),('Bukayo Saka',0.14)],
               pen='Harry Kane', fk='Bukayo Saka'),
 'Brazil':dict(op=[('Vinícius Júnior',0.26),('Raphinha',0.10),('Matheus Cunha',0.15),('Endrick',0.12)],
               pen='Raphinha', fk='Raphinha'),
 'Portugal':dict(op=[('Cristiano Ronaldo',0.21),('Rafael Leão',0.17),('Bruno Fernandes',0.15)],
               pen='Cristiano Ronaldo', fk='Cristiano Ronaldo'),
 'Norway':dict(op=[('Erling Haaland',0.44),('Martin Ødegaard',0.14)],
               pen='Erling Haaland', fk='Martin Ødegaard'),
 'Netherlands':dict(op=[('Cody Gakpo',0.25),('Memphis Depay',0.11),('Donyell Malen',0.13)],
               pen='Memphis Depay', fk='Memphis Depay'),
 'Belgium':dict(op=[('Romelu Lukaku',0.30),('Kevin De Bruyne',0.105),('Jérémy Doku',0.13)],
               pen='Kevin De Bruyne', fk='Kevin De Bruyne'),
 'Colombia':dict(op=[('Luis Díaz',0.30),('Rafael Santos Borré',0.18),('James Rodríguez',0.10)],
               pen='James Rodríguez', fk='James Rodríguez'),
 'Germany':dict(op=[('Kai Havertz',0.18),('Florian Wirtz',0.18),('Jamal Musiala',0.18)],
               pen='Kai Havertz', fk='Florian Wirtz'),
 'Uruguay':dict(op=[('Darwin Núñez',0.32),('Facundo Pellistri',0.13)],
               pen='Darwin Núñez', fk=None),
 'Egypt':dict(op=[('Mohamed Salah',0.385),('Omar Marmoush',0.18)],
               pen='Mohamed Salah', fk='Mohamed Salah'),
 'Ecuador':dict(op=[('Enner Valencia',0.27),('Kendry Páez',0.12)],
               pen='Enner Valencia', fk=None),
 'Croatia':dict(op=[('Andrej Kramarić',0.15),('Ante Budimir',0.22)],
               pen='Andrej Kramarić', fk=None),
 'Morocco':dict(op=[('Youssef En-Nesyri',0.26),('Brahim Díaz',0.16)],
               pen='Youssef En-Nesyri', fk=None),
 'Mexico':dict(op=[('Raúl Jiménez',0.24),('Santiago Giménez',0.22)],
               pen='Raúl Jiménez', fk='Raúl Jiménez'),
 'Japan':dict(op=[('Ayase Ueda',0.14),('Kaoru Mitoma',0.20)],
               pen='Ayase Ueda', fk=None),
 'Switzerland':dict(op=[('Breel Embolo',0.24),('Dan Ndoye',0.16)],
               pen='Breel Embolo', fk=None),
 'Senegal':dict(op=[('Nicolas Jackson',0.20),('Ismaïla Sarr',0.18)],
               pen='Nicolas Jackson', fk=None),
 'Turkiye':dict(op=[('Kerem Aktürkoğlu',0.14),('Arda Güler',0.20)],
               pen='Kerem Aktürkoğlu', fk='Arda Güler'),
 'USA':dict(op=[('Folarin Balogun',0.28),('Christian Pulisic',0.105)],
               pen='Christian Pulisic', fk='Christian Pulisic'),
}

def project_scorers(eg):
    """Project per-player tournament goals from the 3-channel attack model.
    Returns a list of dicts (sorted desc by goals) with the open-play (op),
    penalty (pen) and free-kick (fk) goal components broken out."""
    proj = {}                                    # (team, player) -> components
    def add(team, player, key, val):
        d = proj.setdefault((team, player),
                            dict(team=team, player=player, op=0.0, pen=0.0, fk=0.0))
        d[key] += val
    for team, cfg in SCORERS.items():
        g = eg[team]
        for player, sh in cfg.get('op', []):
            add(team, player, 'op', sh * g)
        for chan, frac in (('pen', PEN_FRAC), ('fk', FK_FRAC)):
            taker = cfg.get(chan)
            if not taker:
                continue
            takers = taker if isinstance(taker, list) else [(taker, 1.0)]
            for player, w in takers:
                add(team, player, chan, w * frac * g)
    out = []
    for d in proj.values():
        d['goals'] = d['op'] + d['pen'] + d['fk']
        out.append(d)
    out.sort(key=lambda d: -d['goals'])
    return out

def _split_team_goals(total, shares, rng):
    """Allocate each sim's integer team goal count among its scorers so they
    COMPETE for the same goals (sequential-binomial = multinomial draw, fully
    vectorised over sims). `total` is the (N,) per-sim team goals; `shares` the
    players' total goal-shares (sum <1, remainder = squad). Returns one (N,)
    goal array per share."""
    remaining = total.astype(np.int64).copy(); rem_p = 1.0; out = []
    for sh in shares:
        p = min(sh / rem_p, 1.0) if rem_p > 1e-9 else 0.0
        g = rng.binomial(remaining, p)
        out.append(g); remaining = remaining - g; rem_p -= sh
    return out

def simulate_golden_boot(proj, eg, tg, idx, rng):
    """Monte-Carlo Golden Boot from the per-sim team-goal matrix. In every
    simulated tournament each player's goals are a (competed-for) share of their
    team's ACTUAL goals that run, so the distribution carries both deep-run and
    finishing variance. The winner is the per-sim leader -> P(win Golden Boot),
    which (unlike the mean) rewards a high ceiling. Ties split the credit."""
    byteam = defaultdict(list)
    for d in proj: byteam[d['team']].append(d)
    players = []; arrays = []
    for team, lst in byteam.items():
        shares = [d['goals'] / eg[team] if eg[team] > 0 else 0.0 for d in lst]
        for d, g in zip(lst, _split_team_goals(tg[idx[team]], shares, rng)):
            players.append((d['player'], d['team'])); arrays.append(g)
    G = np.array(arrays)                       # (P, N) integer goals per sim
    N = G.shape[1]
    topval = G.max(0)                          # winning total in each sim
    is_top = (G == topval)
    credit = (is_top.astype(float) / is_top.sum(0)).sum(1)   # split ties
    pwin = {players[i]: credit[i] / N for i in range(len(players))}
    boot = dict(exp=float(topval.mean()), median=float(np.median(topval)),
                p_ge7=float((topval >= 7).mean()), p_ge8=float((topval >= 8).mean()))
    return pwin, boot

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

    # scorer projection (3-channel attack model): each player's EXPECTED goals =
    # open-play share x team eg  +  (penalty pool if taker)  +  (FK pool if taker).
    # eg[team] is the team's expected tournament goals (group + simulated KO run).
    # Raw expected goals -- no scaling. Set-piece pools are concentrated on one
    # taker, which is why pen/FK takers out-score equal open-play strikers.
    eg, tg, idx = expected_goals_per_team(teams, groups, fixtures)
    proj = project_scorers(eg)
    # Golden-Boot sim: P(win) is an order statistic (the per-sim leader), so it
    # rewards a high ceiling, not just a high mean -- and the typical WINNING
    # total runs above any single player's expected goals.
    pwin, boot = simulate_golden_boot(proj, eg, tg, idx, np.random.default_rng(11))
    def sptag(d):
        t = (['PK'] if d['pen'] > 0 else []) + (['FK'] if d['fk'] > 0 else [])
        return '+'.join(t)
    scorers=[dict(rank=k+1, player=d['player'], team=d['team'],
                  goals=round(d['goals'],1),
                  share=round(d['goals']/eg[d['team']]*100),
                  op=round(d['op'],1), sp=round(d['pen']+d['fk'],1), tag=sptag(d),
                  pwin=round(pwin.get((d['player'],d['team']),0)*100))
             for k,d in enumerate(proj[:6])]
    # verification print: expected-goals top-12 + the P(win Golden Boot) ranking
    print("scorer ranking (expected goals, 3-channel):")
    for k,d in enumerate(proj[:12],1):
        print(f"  {k:2} {d['player']:<20} {d['team']:<11} {d['goals']:.1f}"
              f"  (op {d['op']:.1f} + set-piece {d['pen']+d['fk']:.1f})"
              f"  P(win) {pwin.get((d['player'],d['team']),0)*100:.1f}%")
    print(f"  Golden Boot winning total: mean {boot['exp']:.1f}, median {boot['median']:.0f}"
          f"  | P(>=7) {boot['p_ge7']*100:.0f}%  P(>=8) {boot['p_ge8']*100:.0f}%")
    gb = sorted(((p,t,w) for (p,t),w in pwin.items()), key=lambda x:-x[2])[:8]
    print("  most likely Golden Boot winner:")
    for p,t,w in gb: print(f"     {p:<20} {t:<11} {w*100:.1f}%")

    DATA = dict(
        champion=champ_rows[0] if champ_rows else None,
        titleRace=champ_rows[:8],
        scorers=scorers,
        groups=gdata,
        meta=dict(sims=CONFIG['N_SIMS'], champSigma=sigma,
                  draws=draws, ngames=ngames, goalsPerGame=round(tot/ngames,2),
                  simDraw=round(simstats['draw']*100), simGoals=round(simstats['goals'],2),
                  bootExp=round(boot['exp'],1), bootMedian=round(boot['median']),
                  bootFav=gb[0][0], bootFavPct=round(gb[0][2]*100)),
    )
    os.makedirs(os.path.join(HERE,'wc_site'), exist_ok=True)
    with open(os.path.join(HERE,'wc_site','data.js'),'w',encoding='utf-8') as f:
        f.write('window.WC = ' + json.dumps(DATA, ensure_ascii=False, indent=1) + ';\n')
    print(f"champion: {DATA['champion']['team']} {DATA['champion']['champ']}%  (sigma={sigma})")
    print("top scorer:", scorers[0]['player'], scorers[0]['goals'])
    print("groups:", len(gdata), "| wrote wc_site/data.js")

if __name__ == '__main__':
    main()
