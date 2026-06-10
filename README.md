# FIFA World Cup 2026 — Group-Stage Prediction Engine

A lean, transparent **Elo + Poisson + Monte Carlo** simulator that predicts every
group-stage match and each team's qualification odds. Built to be an *honest
baseline*: pure team strength, no unproven layers.

## Files
| File | What it is |
|---|---|
| `wc2026_model.py` | The engine (match model + 30k-sim global Monte Carlo). |
| `teams.csv` | **The one file you edit.** 48 teams: group, Elo, host flag, Top5%, age. |
| `predictions.md` | Generated output: every match + qualification odds + advance ranking. |
| `squad-lists.pdf` / `squad-lists.txt` | Official FIFA 26-man squads (9 Jun 2026), for availability/reference. |
| `group-stage-prediction-prompt.md` | The analyst reasoning framework behind the model. |
| `backtest.py` / `tune.py` / `diagnostics.py` | Validation: walk-forward backtest (RPS vs baselines), parameter grid-search, failure diagnostics. |
| `results.csv` / `World.tsv` / `en.teams.tsv` | Data sources: 1872–2026 match history + live Elo. |

## Run it
```bash
python3 -m pip install --user numpy   # one-time
python3 wc2026_model.py               # writes predictions.md + prints a summary
```

## How to read `predictions.md`
- **Per match:** `Score` = model's best scoreline (per-team median of expected goals);
  `xG` = expected goals each side; `A/Draw/B win` = outcome probabilities.
- **Per group:** `xPts` expected points, `Win grp`, `Top 2`, and `Advance` %
  (Advance includes the 8-best-third-place path).
- **Calibration audit:** distinguishes the *point-prediction* draw rate (~17%, correctly
  low) from the model's *actual* simulated draw rate (~21%) — the real calibration check.

## How to make it more accurate (in priority order)
1. **Refresh Elo before kickoff.** All 48 teams already use live eloratings.net data
   (`World.tsv`, fetched Jun 2026). To refresh: re-download `World.tsv` + `en.teams.tsv`
   from `eloratings.net/scripts/`, re-map codes→ratings, or just hand-edit the `elo`
   column in `teams.csv`. Re-run.
2. **Re-run if late injuries/withdrawals** change a team's strength — Elo won't reflect a
   star ruled out the day before (cross-check against `squad-lists.pdf`).

## Model parameters (top of `wc2026_model.py`, all tunable)
| Param | Value | Meaning |
|---|---|---|
| `HOME_ADV_ELO` | 100 | Elo bump for host nations (MEX/CAN/USA) at home. |
| `ELO_TO_SUP` | 0.0050 | Elo difference → goal supremacy (200 Elo ≈ 1.0 goal). |
| `BASE_TOTAL` | 2.40 | Baseline total goals in an even game. |
| `MISMATCH_TOTAL` | 0.40 | Extra total goals scaled by mismatch size (blowout calibration). |
| `GOAL_FLOOR` | 0.12 | Minimum expected goals for the underdog. |
| `N_SIMS` | 30000 | Monte Carlo iterations. |

*Values are **backtest-fitted** via `tune.py` (leakage-free temporal holdout, 2006–21 train / 2022–26 test). Dixon-Coles low-score correlation was tested and **rejected** — no RPS gain.*

## Deliberate limitations (by design)
- **Pure-Elo baseline.** Squad availability, recent form beyond Elo, venue heat/altitude,
  and matchday-3 rotation are **not** modelled. Per the project's methodology, this is the
  baseline any added layer must *beat* in a backtest before being trusted.
- **Elo is a team-strength snapshot** (eloratings.net, Jun 2026); it won't reflect a
  last-minute injury or a squad notably stronger/weaker than its recent results.
- Single flat host advantage; no per-venue (Mexico City altitude, southern-US heat) effects.
