# FIFA 2026 World Cup Prediction Model — Claude Context

## Project Summary

Elo + Poisson + Monte Carlo prediction engine for the 2026 FIFA World Cup (48 teams, 12 groups, full knockout bracket). A premium dark-themed predictions webpage is deployed publicly via Vercel.

- **GitHub repo**: https://github.com/azakee007/FIFA-2026-WC
- **Local site**: run `python3 serve.py` → http://127.0.0.1:8000
- **Vercel deployment**: Connect repo at vercel.com/new (reads `vercel.json` automatically)

---

## Core Methodology Rule

> **Backtest-first**: any new predictive layer MUST beat the leakage-free RPS backtest before being trusted. Layers that can't be backtested must be explicitly disclosed as analyst priors with a `†` marker.

Run the backtest: `python3 backtest.py`

Current result: **+25.4% overall** (padded by friendlies). **On major-tournament finals only (626 games), skill is +18.9%**. This is the honest WC-like number.

---

## File Map

| File | Purpose |
|---|---|
| `wc2026_model.py` | Core engine: load_teams, expected_goals, match_analytics, simulate |
| `teams.csv` | 48 teams: elo, group, host, cohesion_bonus (all zeros = baseline) |
| `backtest.py` | Leakage-free RPS validation harness |
| `build_data.py` | Generates `wc_site/data.js` — run this to refresh the website |
| `champion.py` | Runs KO bracket sim → `champion.md` |
| `tune.py` | CONFIG parameter search (temporal holdout 2006-21) |
| `verify_elo.py` | Cross-checks all 48 Elos vs live `World.tsv` |
| `squad_scan.py` | Scans `squad-lists.txt` for talisman presence (binary read, accent-safe) |
| `wc_site/index.html` | Premium predictions webpage (~23KB, no build step) |
| `wc_site/data.js` | Generated data for the page; regenerate with `build_data.py` |
| `serve.py` | Local dev server (`python3 serve.py [port]`, defaults 8000) |
| `vercel.json` | Static deploy config (`cp -r wc_site/. dist`, `outputDirectory: dist`) |
| `World.tsv` | Live eloratings.net data (re-download to refresh Elos) |

---

## CONFIG (wc2026_model.py)

```python
CONFIG = dict(
    HOME_ADV_ELO   = 100,    # Elo bump for host nations (MEX/CAN/USA)
    ELO_TO_SUP     = 0.0050, # Elo diff -> goal supremacy (200 Elo ≈ 1.0 goal)
    BASE_TOTAL     = 2.40,   # baseline total goals in an even game
    MISMATCH_TOTAL = 0.40,   # extra total goals scaled by |supremacy|
    MISMATCH_CAP   = 3.0,    # ceiling on supremacy->total-goals term
    SUP_CONVEX     = 0.0,    # TESTED & REJECTED (no GD-MAE/RPS gain) — keep 0
    GOAL_FLOOR     = 0.12,   # min expected goals for the underdog
    GRID           = 10,     # max goals per side for the analytic PMF grid
    N_SIMS         = 200000, # Monte Carlo iterations
    SEED           = 42,
)
```

---

## Current Predictions (as of June 10, 2026)

### Champion odds (top 8)
| Rank | Team | Champion | Final | Semi |
|---|---|---|---|---|
| 1 | Spain | 22.1% | 33.2% | 46.4% |
| 2 | Argentina | 15.7% | 25.9% | 38.6% |
| 3 | France | 10.6% | 18.9% | 34.0% |
| 4 | England | 7.1% | 13.9% | 25.7% |
| 5 | Brazil | 5.1% | 10.3% | 20.9% |
| 6 | Portugal | 4.9% | 10.4% | 19.2% |
| 7 | Colombia | 4.8% | 10.0% | 18.5% |
| 8 | Netherlands | 3.3% | 7.4% | 16.7% |

### Top scorers (expected goals, raw — no scaling) — 3-channel attack model †
| Rank | Player | Team | Proj. Goals | open play + set pieces |
|---|---|---|---|---|
| 1 | Kylian Mbappé | France | 5.0 | 3.6 + 1.4 (PK+FK) |
| 2 | Harry Kane | England | 4.7 | 3.6 + 1.1 (PK) |
| 3 | Erling Haaland | Norway | 3.8 | 3.1 + 0.7 (PK) |
| 4 | Lamine Yamal | Spain | 3.7 | 3.5 + 0.2 (FK) |
| 5 | Lionel Messi | Argentina | 3.6 | 2.0 + 1.6 (PK+FK) |
| 6 | Lautaro Martínez | Argentina | 3.5 | 3.5 + 0.0 |
| 7 | Enner Valencia | Ecuador | 3.5 | 2.5 + 0.9 (PK) |

*Each team's expected goals are split into open play (~88.5%, spread across its attackers by role), penalties (10%) and direct free kicks (1.5%); the set-piece pools are concentrated on the designated taker. Messi now ranks #5 (was #7) because he takes Argentina's penalties **and** free kicks — 1.5 of his 3.6 goals are set pieces, vs Lautaro's pure open-play 3.5. This is an **analyst prior** (`†`): the match-RPS backtest scores results, not individual goals, so it cannot validate the player split. See "3-channel top-scorer model" below.*

### P(win Golden Boot) — Monte-Carlo order statistic
| Rank | Player | Team | P(win) |
|---|---|---|---|
| 1 | Kylian Mbappé | France | 18% |
| 2 | Harry Kane | England | 15% |
| 3 | Erling Haaland | Norway | 9% |
| 4 | Lamine Yamal | Spain | 6% |
| 5 | Lionel Messi | Argentina | 6% |

*Projected **winning total ~8.3 goals** (median 8; P(≥7)=86%, P(≥8)=63%) — above any single expected tally because the Boot goes to whoever runs hottest over the expanded 8-game path to the title (3 group + R32/R16/QF/SF/F). Favourite: Mbappé ~18%, Kane ~15%, Haaland ~9%. Built via `simulate_golden_boot()`.*

---

## Key Design Decisions & Audit Trail

### 3-channel top-scorer model (`build_data.py`)
- **Status: ADOPTED**. Replaced the old single opaque `share` per player (which bundled open play + penalties + free kicks into one hand-tuned number).
- Each team's expected tournament goals `eg[team]` is split into three channels with different player allocation:
  - **open play** — `1 − PEN_FRAC − FK_FRAC ≈ 88.5%`, **spread** across the named attackers by their `op` share (strikers high, wingers moderate; per-team shares sum to <1, remainder = squad/defenders/own goals).
  - **penalties** — `PEN_FRAC = 0.10` of team goals, **concentrated** on the designated `pen` taker (VAR-era WC prior; eg is already realised goals so conversion is baked in).
  - **direct free kicks** — `FK_FRAC = 0.015`, **concentrated** on the `fk` specialist.
- `player_goals = op_share·eg + (pen? PEN_FRAC·eg) + (fk? FK_FRAC·eg)`. See `project_scorers()`.
- **Why**: concentration of set-piece duty is the real reason pen/FK takers (Kane, Salah, Mbappé, Messi) win Golden Boots — the old flat share could only fake it by inflating one number. The new structure is auditable (per-channel breakdown shown on the page) and role-aware.
- **Disclosure**: the player split (roles + taker assignments) is an **analyst prior** marked `†` — the leakage-free match-RPS backtest scores results, not individual goals, so it cannot validate it. The team-level `eg`, match, and champion models remain pure verified Elo.
- **Taker assignments are priors** — set in the `SCORERS` dict (`pen=`/`fk=` keys). Update them when designated takers change (e.g. retirements, form). `pen` accepts a `[(player, weight), ...]` list to split a primary/backup.
- **Golden-Boot probability sim (BUILT)**: `expected_goals_per_team()` now returns the per-sim `(T, N)` team-goal matrix `tg`; `simulate_golden_boot()` allocates each team's *actual* goals in each sim among its scorers via a sequential-binomial (= multinomial) draw, so teammates **compete for the same goals**, and crowns the per-sim leader. This yields each player's **P(win Golden Boot)** (an order statistic — rewards a high ceiling, not just the mean) and the projected **winning total** (`bootExp`/`bootMedian`), which runs above any single expected value. Ties split the credit. Current: winning total ~8.3 (median 8) over the 8-game path; favourite Mbappé ~18%, Kane ~15%, Haaland ~9%.

### Cohesion bonus
- **Status: ZEROED (reference-only)**. Column `cohesion_bonus` exists in `teams.csv` with all values `0`.
- Infrastructure preserved: `†` marker in output, `.get('cohesion', 0)` defensive read in `expected_goals()`.
- Reason zeroed: no backtest data to validate it; all 48/48 Elo values verified clean against live `World.tsv`.
- If you add nonzero values, you must disclose as an analyst prior (unbacktestable) and mark with `†`.

### Dixon-Coles low-score coupling
- **Status: DOCUMENTED, NOT ADOPTED**. Fixes draw calibration (20.5% → 23.0%) at zero RPS cost.
- Requires reworking `simulate()`'s independent Poisson draws. Good future work.

### SUP_CONVEX (convex blowout expansion)
- **Status: TESTED & REJECTED**. Swept 5 settings (0.02–0.20). GD-MAE rose at every setting, RPS flat.
- Keep `SUP_CONVEX = 0.0` in CONFIG. The "+3 bin gap" was a recomposition artifact.

### Elo verification
- All 48/48 team Elos verified against live `World.tsv` — max diff 0. Run `verify_elo.py` after any `World.tsv` refresh.
- ALIAS dict in `verify_elo.py` handles naming variants: Türkiye→Turkey, Czechia→czechrepublic, South Korea→korearepublic, USA→unitedstates, Congo DR→drcongo, Ivory Coast→cotedivoire, Cape Verde→caboverde, Bosnia→bosniaandherzegovina.

### Squad verification
- `squad_scan.py` scans `squad-lists.txt` (binary read to handle null bytes, accent-normalized).
- 48/48 sections parsed. Missing: Foden (England, squad depth), Rodrygo (Brazil, 9-deep attack) — neither warrants Elo adjustment.

---

## Website Architecture

**`wc_site/index.html`** — single static file, no build step needed.

- **Fonts**: Bricolage Grotesque (headings) + Hanken Grotesk (body) + IBM Plex Mono (stats)
- **Palette**: `--bg:#070a0f`, `--gold:#e9c66a`, `--green:#46d99a` (qualified), `--amber:#f0b24a` (Q3), `--crimson:#ff5b6a`
- **Sections**: sticky nav → hero champion card → title race (animated bars) → golden boot → 12 group cards → methodology footer
- **Group cards**: Table/Scores toggle via `data-v` attribute
- **Animations**: IntersectionObserver stagger-reveal, `prefers-reduced-motion` respected
- **Film grain**: SVG `feTurbulence` in `::after` overlay

**To refresh the page data** after model changes:
```bash
python3 champion.py        # regenerates champion.md
python3 build_data.py      # regenerates wc_site/data.js
```

---

## Deployment

### Local
```bash
python3 serve.py           # serves on :8000
python3 serve.py 8001      # custom port
```

### Vercel (public)
- `vercel.json` is already configured: copies `wc_site/` into `dist/`, static output.
- Connect at vercel.com/new → import `azakee007/FIFA-2026-WC` → click Deploy. No manual settings needed.
- `.vercelignore` excludes Python files, PDFs, TSVs, backtest outputs.

---

## Pre-Kickoff Workflow (run before each matchday)
```bash
# 1. Download fresh Elos
curl -o World.tsv "https://www.eloratings.net/World.tsv"

# 2. Verify all 48 teams still match
python3 verify_elo.py

# 3. Update teams.csv if any Elos changed, then regenerate
python3 champion.py
python3 build_data.py

# 4. Commit & push → Vercel auto-deploys
git add wc_site/data.js champion.md teams.csv
git commit -m "Update predictions: <date>"
git push
```

---

## Known Bugs Fixed (don't reintroduce)
1. **`KeyError: 'cohesion'`** in backtest — fixed by using `.get('cohesion', 0)` in `expected_goals()`.
2. **CSS Cyrillic typo** `--emerald:#42dд9a` — removed duplicate/malformed `--emerald` declarations.
3. **Top scorer logic** — originally a single-striker-per-team dict; then a flat per-player `share`; now a **3-channel model** (open play + penalties + free kicks) so set-piece takers are modelled explicitly, not faked via an inflated share. See "3-channel top-scorer model" above. Goals are still raw expected goals (no scaling).
4. **squad_scan.py null bytes** — `grep` failed on `squad-lists.txt`. Fixed: binary read + `.replace(b'\x00', b'')`.
5. **squad_scan.py parsed only 45/48** — regex failed on accented names. Fixed: changed to `r'^(.+?) \([A-Z]{3}\)\s*'`.
