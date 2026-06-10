#!/usr/bin/env python3
"""Diagnostics to locate where the model measurably fails (grounds the critique)."""
from backtest import run, rps
from wc2026_model import expected_goals, match_analytics, CONFIG, pois_pmf

def is_major(t):
    t = t.lower()
    if 'qual' in t: return False
    return any(x in t for x in ('world cup', 'copa am', 'african cup',
                                'asian cup', 'uefa euro'))

def predict(eh, ea, neutral):
    ta = {'elo': eh, 'host': 0 if neutral else 1}; tb = {'elo': ea, 'host': 0}
    lamH, lamA = expected_goals(ta, tb, CONFIG)
    (pi, pj), (pH, pD, pA), _ = match_analytics(lamH, lamA, CONFIG['GRID'])
    return lamH, lamA, pi, pj, pH, pD, pA

def main():
    elo, evals = run()

    # ---- 1. ALL internationals vs MAJOR tournament finals (the real population) ----
    print("=== Skill by population (is +25% real on hard games?) ===")
    for label, sub in [("ALL internationals", evals),
                       ("MAJOR tournament finals only", [e for e in evals if is_major(e[5])])]:
        n = len(sub)
        fH = sum(1 for e in sub if e[3] > e[4]) / n
        fD = sum(1 for e in sub if e[3] == e[4]) / n
        fA = 1 - fH - fD
        mr = br = acc = pdraw = adraw = 0.0
        for eh, ea, neu, hs, as_, *_ in sub:
            _, _, pi, pj, pH, pD, pA = predict(eh, ea, neu)
            oc = 'H' if hs>as_ else 'D' if hs==as_ else 'A'
            mr += rps(pH,pD,pA,oc); br += rps(fH,fD,fA,oc)
            pred = 'H' if pH==max(pH,pD,pA) else 'D' if pD==max(pH,pD,pA) else 'A'
            acc += (pred==oc); pdraw += pD; adraw += (hs==as_)
        mr/=n; br/=n; acc/=n; pdraw/=n; adraw/=n
        print(f"\n{label}: n={n:,}")
        print(f"  RPS {mr:.4f} vs base {br:.4f}  -> skill {(1-mr/br)*100:+.1f}%")
        print(f"  3-way accuracy {acc*100:.1f}%")
        print(f"  draws: model predicts {pdraw*100:.1f}% vs actual {adraw*100:.1f}%  "
              f"(gap {(pdraw-adraw)*100:+.1f} pp)")

    # ---- 2. Draw-probability calibration (independence/Dixon-Coles check) ----
    print("\n=== Draw calibration (independent-Poisson weakness) ===")
    bins = {}
    for eh, ea, neu, hs, as_, *_ in evals:
        _, _, _, _, _, pD, _ = predict(eh, ea, neu)
        b = min(int(pD*20), 6)                       # 5%-wide bins up to 30%+
        d = bins.setdefault(b, [0,0,0.0]); d[0]+= (hs==as_); d[1]+=1; d[2]+=pD
    print("| pred P(draw) bin | matches | model avg | actual draw % |")
    for b in sorted(bins):
        hit,c,sp = bins[b]
        print(f"| {b*5}-{b*5+5}% | {c} | {sp/c*100:.1f}% | {hit/c*100:.1f}% |")

    # ---- 3. Specific low scores: independent Poisson under-predicts 0-0 / 1-1 ----
    print("\n=== Low-score frequency: predicted vs actual (Dixon-Coles target) ===")
    n = len(evals); p00=p11=p10=a00=a11=a10=0.0
    for eh, ea, neu, hs, as_, *_ in evals:
        lamH, lamA, *_ = predict(eh, ea, neu)
        pa = pois_pmf(lamH, 8); pb = pois_pmf(lamA, 8)
        p00 += pa[0]*pb[0]; p11 += pa[1]*pb[1]; p10 += pa[1]*pb[0]+pa[0]*pb[1]
        a00 += (hs==0 and as_==0); a11 += (hs==1 and as_==1)
        a10 += ((hs==1 and as_==0) or (hs==0 and as_==1))
    for nm,p,a in [("0-0",p00,a00),("1-1",p11,a11),("1-0/0-1",p10,a10)]:
        print(f"  {nm:8} predicted {p/n*100:.1f}%  vs actual {a/n*100:.1f}%  ({(p-a)/n*100:+.1f} pp)")

    # ---- 4. Goal-supremacy calibration (is the Elo->goals mapping right?) ----
    print("\n=== Supremacy calibration (Elo->goal-diff mapping) ===")
    sb = {}
    for eh, ea, neu, hs, as_, *_ in evals:
        lamH, lamA, *_ = predict(eh, ea, neu)
        b = round(lamH - lamA)
        d = sb.setdefault(b, [0,0.0,0.0]); d[0]+=1; d[1]+=(lamH-lamA); d[2]+=(hs-as_)
    print("| predicted supremacy | matches | model mean | actual mean GD |")
    for b in sorted(sb):
        c,ps,ag = sb[b]
        if c>=50: print(f"| ~{b:+d} | {c} | {ps/c:+.2f} | {ag/c:+.2f} |")

if __name__ == '__main__':
    main()
