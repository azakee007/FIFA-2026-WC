# WC2026 Engine — Backtest Report

**Reconstruction validation** (my Elo vs live eloratings, 231 teams): correlation **0.928**, mean abs error **173 Elo**.
  → high correlation = the rebuilt ratings are on the same scale the model predicts on.

**Test set:** 8,081 internationals since 2018-01-01. Base rates H/D/A = 48/23/29%.

## Headline — does the model beat climatology?

- **RPS (model): 0.1702**  vs  base-rate 0.2281  → **skill score +25.4%** (positive = adds value; lower RPS is better)
  - ⚠️ That figure is padded by easy friendlies/qualifiers. On **major-tournament finals only** (626 games — the WC-like population), skill is **+18.9%**: the honest number for World Cup expectations.
- **Outcome accuracy (3-way): 60.2%**  vs  higher-Elo-wins 60.2%
- Goal-difference sign correct: 57.2%  |  GD mean-abs-error: 1.33
- Exact-scoreline hit rate: 10.3%  (≈10-12% is strong for football)
- Goals/game — predicted 2.84 vs actual 2.73  (model goal calibration)

## Probability calibration (confidence vs reality)

| Predicted confidence | Matches | Actual hit rate |
|---|---|---|
| 30-40% | 696 | 36% |
| 40-50% | 1802 | 44% |
| 50-60% | 1629 | 52% |
| 60-70% | 1439 | 63% |
| 70-80% | 1196 | 75% |
| 80-90% | 855 | 86% |
| 90-100% | 464 | 94% |