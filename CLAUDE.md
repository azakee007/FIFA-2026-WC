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

## Current Predictions (as of June 2026)

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

### Top scorers (expected goals, raw — no scaling)
| Rank | Player | Team | Proj. Goals |
|---|---|---|---|
| 1 | Kylian Mbappé | France | 4.8 |
| 2 | Harry Kane | England | 4.8 |
| 3 | Erling Haaland | Norway | 3.8 |
| 4 | Lautaro Martínez | Argentina | 3.5 |
| 5 | Lamine Yamal | Spain | 3.5 |
| 6 | Romelu Lukaku | Belgium | 3.5 |
| 7 | Lionel Messi | Argentina | 3.4 |

*Messi is #7 because Argentina splits goals three ways (Messi/Lautaro/Álvarez). The scorer logic now correctly models multiple attackers per team competing head-to-head.*

---

## Key Design Decisions & Audit Trail

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
3. **Top scorer excluded Messi** — was a single-striker-per-team dict. Fixed: `SCORERS` dict allows multiple players per team; goals are raw expected goals (no scaling).
4. **squad_scan.py null bytes** — `grep` failed on `squad-lists.txt`. Fixed: binary read + `.replace(b'\x00', b'')`.
5. **squad_scan.py parsed only 45/48** — regex failed on accented names. Fixed: changed to `r'^(.+?) \([A-Z]{3}\)\s*'`.
