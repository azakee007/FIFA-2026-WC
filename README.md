# FIFA World Cup 2026 — Group-Stage Prediction Engine

A lean, transparent **Elo + Poisson + Monte Carlo** simulator that predicts every
group-stage match and each team's qualification odds. Built to be an *honest
baseline*: pure team strength, no unproven layers.

## Files
| File | What it is |
|---|---|
| `wc2026_model.py` | The engine (match model + 200k-sim global Monte Carlo). |
| `teams.csv` | **The one file you edit.** 48 teams: group, Elo, host flag, Top5%, age, cohesion_bonus. |
| `predictions.md` | Generated output: every match + qualification odds + advance ranking. |
| `squad-lists.pdf` / `squad-lists.txt` | Official FIFA 26-man squads (9 Jun 2026), for availability/reference. |
| `group-stage-prediction-prompt.md` | The analyst reasoning framework behind the model. |
| `backtest.py` / `tune.py` / `diagnostics.py` | Validation: walk-forward backtest (RPS vs baselines), parameter grid-search, failure diagnostics. |
| `verify_elo.py` / `squad_scan.py` | Pre-kickoff data hygiene: cross-check `teams.csv` Elo vs live `World.tsv` (currently 48/48); scan official squads for absent talismen. |
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
   column in `teams.csv`. Re-run. **Verify with `python3 verify_elo.py`** — flags any team
   whose `teams.csv` Elo has drifted from live `World.tsv`.
2. **Re-run if late injuries/withdrawals** change a team's strength — Elo won't reflect a
   star ruled out the day before. **Spot it with `python3 squad_scan.py`** — confirms each
   contender's 26-man squad and flags missing talismen (cross-check against `squad-lists.pdf`).

## Model parameters (top of `wc2026_model.py`, all tunable)
| Param | Value | Meaning |
|---|---|---|
| `HOME_ADV_ELO` | 100 | Elo bump for host nations (MEX/CAN/USA) at home. |
| `ELO_TO_SUP` | 0.0050 | Elo difference → goal supremacy (200 Elo ≈ 1.0 goal). |
| `BASE_TOTAL` | 2.40 | Baseline total goals in an even game. |
| `MISMATCH_TOTAL` | 0.40 | Extra total goals scaled by mismatch size (blowout calibration). |
| `GOAL_FLOOR` | 0.12 | Minimum expected goals for the underdog. |
| `N_SIMS` | 200000 | Monte Carlo iterations. |

*Values are **backtest-fitted** via `tune.py` (leakage-free temporal holdout, 2006–21 train / 2022–26 test).*

**Tested, not adopted (audit trail):**
- **Dixon-Coles low-score coupling** (`RHO`): ~RPS-neutral (0.1702→0.1700), so previously rejected on RPS alone — but it **does** fix draw-rate calibration (sim draws 20.5%→23.0%, matching reality) and 0-0/1-1 frequency at no RPS cost. Worth adopting **if** `simulate()` is reworked to couple the two Poissons (currently independent). `tune.py`'s `wdl()` already implements the `RHO` term for re-testing.
- **Convex supremacy expansion** (`SUP_CONVEX`): tested and rejected — no GD-MAE or RPS gain. The diagnostics' "+3 predicted → +3.36 actual" gap was a bin-recomposition artifact, not an exploitable bias.

## Deliberate limitations (by design)
- **Elo baseline + one disclosed override.** The quantitative core is pure Elo; squad
  availability, recent form beyond Elo, venue heat/altitude, and matchday-3 rotation are
  **not** modelled. Per the project's methodology, this is the baseline any added layer must
  *beat* in a backtest before being trusted.
- **Cohesion override exists but ships OFF.** The `cohesion_bonus` column is a disclosed
  hand-override mechanism (capped ±20 Elo ≈ ±0.1 goal, flagged `†` in output). It **cannot**
  clear the "beat the backtest" bar — no historical cohesion series exists to validate it —
  so it ships **zeroed**: predictions are pure verified Elo. Enter a value only with a
  citable reason (confirmed injury, managerial upheaval), never on vibes; the backtest
  harness runs it inert regardless (defaults to 0).
- **Elo is a team-strength snapshot** (eloratings.net, Jun 2026); it won't reflect a
  last-minute injury or a squad notably stronger/weaker than its recent results.
- Single flat host advantage; no per-venue (Mexico City altitude, southern-US heat) effects.
