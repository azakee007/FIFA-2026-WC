# FIFA World Cup 2026 - Group Stage Predictions
*Lean Elo + Poisson + Monte Carlo engine. 200,000 sims. Verified-Elo baseline.*

> Elo: live World Football Elo (eloratings.net `World.tsv`, Jun 2026) for all 48 teams.

> **Cohesion:** the `cohesion_bonus` override column is **zeroed (reference-only)** — no unvalidated judgment is applied; these predictions are pure **verified Elo** (48/48 vs live `World.tsv`). Add a value in `teams.csv` only with a citable reason (confirmed injury, managerial change); it renders with a `†` flag.


## Group A

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-11 | Mexico vs South Africa | **3-1** | 2.8-0.5 | 84% | 11% | 4% |
| MD1 06-11 | South Korea vs Czechia | **1-1** | 1.3-1.2 | 38% | 27% | 34% |
| MD2 06-18 | Czechia vs South Africa | **2-1** | 2.0-0.9 | 63% | 21% | 16% |
| MD2 06-18 | Mexico vs South Korea | **2-1** | 2.0-0.9 | 63% | 21% | 16% |
| MD3 06-24 | Mexico vs Czechia | **2-1** | 2.0-0.8 | 65% | 20% | 15% |
| MD3 06-24 | South Africa vs South Korea | **1-2** | 0.8-2.0 | 15% | 20% | 65% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Mexico | 6.88 | 70% | 91% | 98% |
| South Korea | 4.28 | 15% | 53% | 78% |
| Czechia | 4.06 | 13% | 47% | 74% |
| South Africa | 1.56 | 1% | 9% | 20% |

## Group B

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-12 | Canada vs Bosnia | **2-1** | 2.2-0.8 | 71% | 18% | 11% |
| MD2 06-13 | Qatar vs Switzerland | **0-3** | 0.5-2.8 | 4% | 11% | 85% |
| MD3 06-18 | Switzerland vs Bosnia | **2-1** | 2.2-0.8 | 71% | 18% | 11% |
| MD3 06-18 | Canada vs Qatar | **3-0** | 2.8-0.5 | 85% | 11% | 4% |
| MD4 06-24 | Canada vs Switzerland | **1-1** | 1.2-1.2 | 36% | 28% | 37% |
| MD4 06-24 | Bosnia vs Qatar | **2-1** | 1.8-0.9 | 58% | 23% | 19% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Switzerland | 6.34 | 48% | 88% | 97% |
| Canada | 6.32 | 47% | 88% | 97% |
| Bosnia | 3.00 | 4% | 20% | 54% |
| Qatar | 1.27 | 1% | 4% | 14% |

## Group C

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-13 | Brazil vs Morocco | **2-1** | 1.8-1.0 | 57% | 23% | 20% |
| MD1 06-13 | Haiti vs Scotland | **1-2** | 0.8-2.0 | 15% | 20% | 65% |
| MD2 06-19 | Scotland vs Morocco | **1-1** | 1.1-1.4 | 31% | 27% | 42% |
| MD2 06-19 | Brazil vs Haiti | **3-1** | 2.8-0.5 | 83% | 12% | 5% |
| MD3 06-24 | Scotland vs Brazil | **1-2** | 0.9-1.9 | 17% | 22% | 62% |
| MD3 06-24 | Morocco vs Haiti | **2-1** | 2.2-0.8 | 69% | 19% | 12% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Brazil | 6.63 | 64% | 88% | 97% |
| Morocco | 4.63 | 21% | 59% | 83% |
| Scotland | 4.06 | 14% | 46% | 74% |
| Haiti | 1.46 | 1% | 7% | 18% |

## Group D

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-12 | USA vs Paraguay | **1-1** | 1.2-1.2 | 35% | 28% | 37% |
| MD2 06-13 | Australia vs Turkiye | **1-2** | 1.0-1.7 | 23% | 24% | 53% |
| MD3 06-19 | USA vs Australia | **1-1** | 1.4-1.1 | 42% | 27% | 31% |
| MD3 06-19 | Turkiye vs Paraguay | **1-1** | 1.5-1.1 | 46% | 26% | 28% |
| MD4 06-25 | USA vs Turkiye | **1-1** | 1.1-1.5 | 27% | 26% | 47% |
| MD4 06-25 | Paraguay vs Australia | **1-1** | 1.4-1.1 | 43% | 27% | 30% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Turkiye | 5.13 | 41% | 68% | 84% |
| Paraguay | 4.05 | 23% | 49% | 69% |
| USA | 3.95 | 21% | 47% | 67% |
| Australia | 3.29 | 14% | 35% | 55% |

## Group E

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-14 | Germany vs Curacao | **3-0** | 2.9-0.5 | 87% | 10% | 3% |
| MD1 06-14 | Ivory Coast vs Ecuador | **1-2** | 0.8-2.1 | 14% | 20% | 66% |
| MD2 06-20 | Germany vs Ivory Coast | **2-1** | 2.0-0.8 | 65% | 20% | 15% |
| MD2 06-20 | Ecuador vs Curacao | **3-0** | 3.0-0.4 | 87% | 9% | 3% |
| MD3 06-25 | Curacao vs Ivory Coast | **1-2** | 0.8-2.1 | 13% | 19% | 67% |
| MD3 06-25 | Ecuador vs Germany | **1-1** | 1.2-1.2 | 37% | 28% | 35% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Ecuador | 6.27 | 47% | 86% | 97% |
| Germany | 6.21 | 45% | 85% | 97% |
| Ivory Coast | 3.48 | 7% | 27% | 66% |
| Curacao | 0.98 | 0% | 2% | 9% |

## Group F

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-14 | Netherlands vs Japan | **1-1** | 1.3-1.1 | 42% | 27% | 32% |
| MD1 06-14 | Sweden vs Tunisia | **1-1** | 1.5-1.1 | 47% | 26% | 27% |
| MD2 06-20 | Netherlands vs Sweden | **2-1** | 2.0-0.8 | 65% | 20% | 15% |
| MD2 06-20 | Tunisia vs Japan | **1-2** | 0.8-2.2 | 12% | 19% | 69% |
| MD3 06-25 | Japan vs Sweden | **2-1** | 1.9-0.9 | 60% | 22% | 18% |
| MD3 06-25 | Tunisia vs Netherlands | **1-2** | 0.7-2.3 | 10% | 17% | 73% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Netherlands | 6.03 | 51% | 83% | 94% |
| Japan | 5.51 | 38% | 76% | 90% |
| Sweden | 3.07 | 8% | 27% | 54% |
| Tunisia | 2.08 | 3% | 14% | 31% |

## Group G

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-15 | Belgium vs Egypt | **2-1** | 1.9-0.9 | 61% | 22% | 18% |
| MD1 06-15 | Iran vs New Zealand | **2-1** | 1.9-0.9 | 62% | 21% | 17% |
| MD2 06-21 | Belgium vs Iran | **2-1** | 1.6-1.0 | 51% | 25% | 24% |
| MD2 06-21 | New Zealand vs Egypt | **1-2** | 1.0-1.7 | 23% | 24% | 53% |
| MD3 06-26 | Egypt vs Iran | **1-1** | 1.1-1.5 | 28% | 26% | 46% |
| MD3 06-26 | New Zealand vs Belgium | **1-2** | 0.7-2.4 | 9% | 16% | 74% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Belgium | 6.23 | 58% | 84% | 94% |
| Iran | 4.67 | 25% | 61% | 81% |
| Egypt | 3.68 | 13% | 40% | 66% |
| New Zealand | 2.07 | 4% | 15% | 30% |

## Group H

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-15 | Spain vs Cape Verde | **3-0** | 3.2-0.3 | 91% | 7% | 2% |
| MD1 06-15 | Saudi Arabia vs Uruguay | **1-2** | 0.7-2.3 | 10% | 17% | 74% |
| MD2 06-21 | Spain vs Saudi Arabia | **3-0** | 3.3-0.3 | 92% | 7% | 2% |
| MD2 06-21 | Uruguay vs Cape Verde | **2-1** | 2.3-0.7 | 73% | 17% | 10% |
| MD3 06-26 | Cape Verde vs Saudi Arabia | **1-1** | 1.2-1.2 | 37% | 28% | 35% |
| MD3 06-26 | Uruguay vs Spain | **1-2** | 0.8-2.1 | 13% | 19% | 68% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Spain | 7.86 | 83% | 99% | 100% |
| Uruguay | 5.31 | 16% | 82% | 92% |
| Cape Verde | 1.99 | 1% | 10% | 28% |
| Saudi Arabia | 1.91 | 1% | 9% | 26% |

## Group I

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-16 | France vs Senegal | **2-1** | 1.9-0.9 | 60% | 22% | 18% |
| MD1 06-16 | Iraq vs Norway | **1-2** | 0.8-2.2 | 11% | 18% | 71% |
| MD2 06-22 | France vs Iraq | **3-1** | 2.8-0.5 | 84% | 12% | 5% |
| MD2 06-22 | Norway vs Senegal | **1-1** | 1.4-1.1 | 42% | 27% | 31% |
| MD3 06-26 | Norway vs France | **1-2** | 1.0-1.7 | 21% | 24% | 55% |
| MD3 06-26 | Senegal vs Iraq | **2-1** | 2.1-0.8 | 66% | 20% | 14% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| France | 6.54 | 62% | 87% | 97% |
| Norway | 4.72 | 22% | 60% | 84% |
| Senegal | 4.13 | 15% | 46% | 76% |
| Iraq | 1.39 | 1% | 7% | 16% |

## Group J

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-16 | Argentina vs Algeria | **2-1** | 2.4-0.7 | 76% | 15% | 8% |
| MD1 06-16 | Austria vs Jordan | **2-1** | 1.7-1.0 | 55% | 24% | 21% |
| MD2 06-22 | Argentina vs Austria | **2-1** | 2.2-0.8 | 70% | 18% | 12% |
| MD2 06-22 | Jordan vs Algeria | **1-1** | 1.1-1.5 | 28% | 26% | 46% |
| MD3 06-27 | Algeria vs Austria | **1-1** | 1.1-1.4 | 29% | 26% | 45% |
| MD3 06-27 | Jordan vs Argentina | **1-3** | 0.5-2.7 | 5% | 12% | 83% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Argentina | 7.33 | 80% | 95% | 99% |
| Austria | 4.04 | 11% | 53% | 73% |
| Algeria | 3.17 | 6% | 33% | 56% |
| Jordan | 2.24 | 3% | 18% | 35% |

## Group K

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-17 | Portugal vs Congo DR | **2-1** | 2.4-0.7 | 75% | 16% | 9% |
| MD1 06-17 | Uzbekistan vs Colombia | **1-2** | 0.8-2.1 | 13% | 19% | 68% |
| MD2 06-23 | Portugal vs Uzbekistan | **2-1** | 2.2-0.8 | 69% | 19% | 13% |
| MD2 06-23 | Colombia vs Congo DR | **2-1** | 2.4-0.7 | 74% | 16% | 9% |
| MD3 06-27 | Colombia vs Portugal | **1-1** | 1.2-1.2 | 36% | 28% | 37% |
| MD3 06-27 | Congo DR vs Uzbekistan | **1-1** | 1.1-1.4 | 29% | 26% | 44% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| Portugal | 6.03 | 47% | 84% | 94% |
| Colombia | 5.98 | 46% | 84% | 94% |
| Uzbekistan | 2.72 | 5% | 20% | 46% |
| Congo DR | 2.02 | 3% | 12% | 30% |

## Group L

| Matchday | Match | Score | xG | Win % | Draw % | Loss % |
|---|---|---|---|---|---|---|
| MD1 06-17 | England vs Croatia | **2-1** | 1.6-1.0 | 50% | 25% | 25% |
| MD1 06-17 | Ghana vs Panama | **1-2** | 0.9-2.0 | 16% | 21% | 63% |
| MD2 06-23 | England vs Ghana | **3-0** | 3.0-0.4 | 88% | 9% | 3% |
| MD2 06-23 | Panama vs Croatia | **1-2** | 0.9-1.8 | 19% | 23% | 59% |
| MD3 06-27 | Panama vs England | **1-2** | 0.8-2.2 | 11% | 18% | 71% |
| MD3 06-27 | Croatia vs Ghana | **3-1** | 2.6-0.6 | 80% | 13% | 6% |

*Qualification odds:*

| Team | xPts | Win grp | Top 2 | Advance |
|---|---|---|---|---|
| England | 6.78 | 62% | 91% | 98% |
| Croatia | 5.52 | 30% | 77% | 93% |
| Panama | 3.42 | 7% | 28% | 64% |
| Ghana | 1.19 | 1% | 4% | 13% |

---
## Slate calibration audit

*Point-prediction slate (the headline scorelines):*
- Predicted as draws: **18/72 = 25%** (point slates correctly show fewer draws than actually occur)
- Avg goals/game: **2.82** (target ~2.5-2.8)
- Games with 4+ goals: **5/72**

*True model belief (from the Monte Carlo) — the real calibration check:*
- Actual draw rate: **20%** (target ~25-30%)
- Avg goals/game: **2.86** (target ~2.5-2.8)

## Most likely to advance (top 32 by P(advance))

| # | Team | Grp | Advance % |
|---|---|---|---|
| 1 | Spain | H | 100% |
| 2 | Argentina | J | 99% |
| 3 | England | L | 98% |
| 4 | Mexico | A | 98% |
| 5 | Switzerland | B | 97% |
| 6 | Brazil | C | 97% |
| 7 | Ecuador | E | 97% |
| 8 | Canada | B | 97% |
| 9 | Germany | E | 97% |
| 10 | France | I | 97% |
| 11 | Portugal | K | 94% |
| 12 | Belgium | G | 94% |
| 13 | Colombia | K | 94% |
| 14 | Netherlands | F | 94% |
| 15 | Croatia | L | 93% |
| 16 | Uruguay | H | 92% |
| 17 | Japan | F | 90% |
| 18 | Norway | I | 84% |
| 19 | Turkiye | D | 84% |
| 20 | Morocco | C | 83% |
| 21 | Iran | G | 81% |
| 22 | South Korea | A | 78% |
| 23 | Senegal | I | 76% |
| 24 | Scotland | C | 74% |
| 25 | Czechia | A | 74% |
| 26 | Austria | J | 73% |
| 27 | Paraguay | D | 69% |
| 28 | USA | D | 67% |
| 29 | Ivory Coast | E | 66% |
| 30 | Egypt | G | 66% |
| 31 | Panama | L | 64% |
| 32 | Algeria | J | 56% |