#!/usr/bin/env python3
"""
Grid-search the match-model parameters on a leakage-free temporal holdout,
INCLUDING the altitude term (does acclimatisation beat the baseline?).

  TRAIN: competitive (non-friendly) internationals 2006-2021
  TEST : competitive internationals 2022-2026

Other 5 params are held at their prior backtest fit; we search HOME_ADV x ALT_COEF
(they interact: altitude was partly absorbed into home advantage before).
Selection: min TRAIN RPS, GD-MAE tiebreak. Then OLD vs NEW on held-out TEST,
with an altitude-affected subset to isolate the effect.
"""
import numpy as np, math, itertools
from backtest import run
from altitude import home_alt

G = 8; K = np.arange(G + 1); FACT = np.array([math.factorial(k) for k in K], float)
OLD   = dict(HA=100, SUP=0.0050, BASE=2.40, MIS=0.40, FLOOR=0.12, RHO=0.0, ALT=0.0)
FIXED = dict(SUP=0.0050, BASE=2.40, MIS=0.40, FLOOR=0.12, RHO=0.0)

def is_major(t):
    t = t.lower()
    return ('qual' not in t) and any(x in t for x in
            ('world cup', 'copa am', 'african cup', 'asian cup', 'uefa euro'))

def prep(data):
    EH = np.array([e[0] for e in data]); EA = np.array([e[1] for e in data])
    NEU = np.array([e[2] for e in data])
    HS = np.array([e[3] for e in data]); AS = np.array([e[4] for e in data])
    dd = []
    for e in data:
        ah, aa = home_alt(e[7]), home_alt(e[8])
        v = ah if not e[2] else 0                      # venue alt: home's, or 0 if neutral
        dd.append(max(0, v - aa) - max(0, v - ah))     # disadv_away - disadv_home
    return (EH, EA, NEU, HS, AS, (HS>AS).astype(float),
            (HS==AS).astype(float), (HS-AS).astype(float), np.array(dd, float))

def lambdas(arr, P):
    EH, EA, NEU, *_, DD = arr
    eh = EH + np.where(NEU, 0.0, P['HA'])
    sup_raw = (eh - EA) * P['SUP'] + P['ALT'] * DD
    total = P['BASE'] + P['MIS'] * np.minimum(np.abs(sup_raw), 3.0)
    cap = total - 2 * P['FLOOR']
    sup = np.clip(sup_raw, -cap, cap)
    return (total + sup) / 2, (total - sup) / 2

def wdl(lamA, lamB, rho):
    A = lamA[:, None]; B = lamB[:, None]
    pa = np.exp(-A) * A ** K / FACT; pb = np.exp(-B) * B ** K / FACT
    pH0 = (pa * (np.cumsum(pb,1)-pb)).sum(1); pA0 = (pb * (np.cumsum(pa,1)-pa)).sum(1)
    pD0 = (pa * pb).sum(1)
    c00,c01,c10,c11 = pa[:,0]*pb[:,0],pa[:,0]*pb[:,1],pa[:,1]*pb[:,0],pa[:,1]*pb[:,1]
    d00=c00*(1-lamA*lamB*rho);d01=c01*(1+lamA*rho);d10=c10*(1+lamB*rho);d11=c11*(1-rho)
    Z = 1+(d00-c00)+(d01-c01)+(d10-c10)+(d11-c11)
    return (pH0-c10+d10)/Z, (pD0-c00-c11+d00+d11)/Z, (pA0-c01+d01)/Z

def evaluate(arr, P):
    oH, oD, gd = arr[5], arr[6], arr[7]
    lamA, lamB = lambdas(arr, P); pH, pD, pA = wdl(lamA, lamB, P['RHO'])
    c1 = pH-oH; c2 = (pH+pD)-(oH+oD)
    rps = 0.5*(c1*c1+c2*c2)
    acc = (np.stack([pH,pD,pA]).argmax(0) == np.where(oH==1,0,np.where(oD==1,1,2)))
    gdmae = np.abs((np.floor(lamA+0.5)-np.floor(lamB+0.5)) - gd)
    return rps.mean(), gdmae.mean(), acc.mean()

def baserate(arr):
    oH, oD = arr[5], arr[6]; fH, fD = oH.mean(), oD.mean()
    c1 = fH-oH; c2 = (fH+fD)-(oH+oD); return (0.5*(c1*c1+c2*c2)).mean()

def main():
    _, snaps = run('2006-01-01')
    comp = lambda e: 'friendly' not in e[5].lower()
    train = prep([e for e in snaps if e[6] < '2022-01-01' and comp(e)])
    test  = prep([e for e in snaps if e[6] >= '2022-01-01' and comp(e)])
    tlist = [e for e in snaps if e[6] >= '2022-01-01' and comp(e)]
    majors = prep([e for e in tlist if is_major(e[5])])
    print(f"train={train[0].size:,}  test={test[0].size:,}  majors={majors[0].size:,}")

    best = None
    for HA, ALT in itertools.product([90,100,110], [0,5e-5,1e-4,1.5e-4,2e-4,3e-4]):
        P = dict(FIXED, HA=HA, ALT=ALT)
        rps, gdmae, _ = evaluate(train, P)
        if best is None or (rps, gdmae) < best[:2]: best = (rps, gdmae, P)
    bestP = best[2]
    print(f"\nBEST: HA={bestP['HA']}  ALT_COEF={bestP['ALT']:.5f}  (train RPS {best[0]:.4f})")

    # altitude-affected subset of TEST (elevated home vs lower-altitude away)
    DD = test[8]; mask = DD >= 800
    asub = tuple(a[mask] if hasattr(a,'__len__') and a.size==DD.size else a for a in test)
    print("\n=== OLD (no altitude) vs NEW on held-out TEST ===")
    for name, arr in [("ALL TEST", test), ("MAJOR FINALS", majors),
                      (f"ALTITUDE games (DD>=800m, n={mask.sum()})", asub)]:
        br = baserate(arr)
        print(f"\n{name} (n={arr[0].size:,}, base RPS {br:.4f}):")
        for tag, P in [("OLD", OLD), ("NEW", bestP)]:
            rps, gdmae, acc = evaluate(arr, P)
            print(f"  {tag}: RPS {rps:.4f} (skill {(1-rps/br)*100:+.1f}%) | "
                  f"acc {acc*100:.1f}% | GD-MAE {gdmae:.3f}")

if __name__ == '__main__':
    main()
