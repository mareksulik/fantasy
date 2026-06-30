# Fantasy TdF Helper - Claude Context

## Project Overview
Web application to help users select better riders for Tour de France fantasy league (https://fantasybytissot.letour.fr).

## Current Status (TdF 2026)
- ✅ Updated to **Tour de France 2026** — 197 selectable riders, 23 teams
- ✅ Fantasy rider data scraped via `fantasy_scraper.js` (now count-agnostic pagination) → `all_tour_de_france_riders.csv`
- ✅ PCS scraper with advanced name matching (`simple-pcs-script.py`); live 2026-season points
- ✅ Data integration: 194/197 matched (157 manual map + 37 fuzzy, all verified); 3 unmatched domestiques outside PCS top-1500 (Allegaert, Riesebeek, Eekhoff → 0 pts)
- Note: source startlist `doc.pdf` is a *provisional* 129-rider list; the fantasy CSV (197) is the authoritative selectable universe, so no hard-filter is applied
- JSON key `pcs_points_2025` retained as the "current-season points" field (referenced ~12× in app.py + templates — do not rename)
- ✅ **Value model in `value_utils.py`** (single source, imported by scraper + app.py): `value_points = 0.8·2026 season pts + 0.2·12-month pts` (2026 primary, 12m small helper); `points_per_credit = value_points/price`; `value_category` = **global** percentile tiers across the whole field (PCS pts already aggregate GC+stages+one-day, so categories aren't siloed; gives absolute anchor so a decent rider isn't "Poor" for being the weakest leader). Fields added: `pcs_points_12m`, `value_points`. 12-month ranking scraped from PCS `p=me` (cols name=4/team=5/pts=6), cached in `pcs_riders_12m.csv`. riders table = 2 PCS columns (2026, 12m); PCS-rank badge for top 100.
- ✅ Flask web application with rider listing and filtering
- ✅ Rider comparison tool implemented
- ✅ Team builder with budget optimization and team constraints
- ✅ Statistics page with charts and insights
- ✅ All text converted to English
- ✅ 5-tier value system (Excellent/Great/Good/Average/Poor)
- ✅ Team filtering functionality
- ✅ Automatic daily PCS points updates at 2 AM
- ✅ Complete functional web application ready

## Data Sources
1. **Fantasy Data** (`all_tour_de_france_riders.csv`):
   - Rider name, team, category (Leaders/Sprinters/Climbers/All-rounders), price (credits)

2. **PCS Data** (ProCyclingStats API):
   - 2025 season points, 12-month points, specialization stats
   - Career history, team changes, race results

## Required Output Format
- Rider name, team name, 2025 points, 12-month points
- Additional value metrics: points/price ratio, form trends

## Tech Stack
- **Backend**: Python (Flask/FastAPI)
- **Data Processing**: pandas, requests, BeautifulSoup
- **PCS Integration**: procyclingstats library
- **Frontend**: HTML templates + Bootstrap/Tailwind

## Key Features Implemented
1. ✅ Rider data integration (fantasy + PCS) - 100% match rate
2. ✅ Filtering/sorting by category, team, price, points
3. ✅ Rider comparison tool with side-by-side stats
4. ✅ Team builder with 120-credit budget constraint and team limits
5. ✅ Value analysis with 5-tier rating system
6. ✅ Statistics dashboard with charts and insights
7. ✅ Responsive UI with Bootstrap styling
8. ✅ Team optimization algorithms (value/points/balanced strategies)
9. ✅ Automatic daily PCS points updates (2 AM) with API endpoints

## Development Commands
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run PCS data collection (REQUIRED FIRST)
python simple-pcs-script.py

# Update to final TdF 2025 roster (184 riders)
python update_tdf_roster.py

# Start web application (use nohup for background)
source venv/bin/activate && nohup python app.py > app.log 2>&1 &
# Then visit: http://localhost:8086

# API endpoints for manual updates:
# POST /api/update-pcs-points - manually trigger PCS update
# GET /api/update-status - check last update time
```

## Deployment (Vercel + GitHub)
- **Live:** https://fantasy.mareksulik.sk (alias) + https://fantasy-tdf.vercel.app. Vercel project `fantasy-tdf` (Hobby account `mareksulik`), git-connected to `mareksulik/fantasy`, production branch `main`. DNS for the custom domain is at WebSupport: `CNAME fantasy → cname.vercel-dns.com`. SSO protection disabled (public).
- **Serverless config:** `vercel.json` serves Flask via `@vercel/python` (`includeFiles: templates/**, *.json`). `app.py` `os.chdir(dirname(__file__))` (relative data paths) and skips the scheduler thread when `os.environ['VERCEL']` is set.
- **Update workflow:** refresh data locally (`python simple-pcs-script.py` → `python scrape_wins_2026.py`), then `git commit && git push origin main` → Vercel auto-deploys. The in-app daily scheduler does NOT run on Vercel.
- **⚠️ CRITICAL git gotcha:** Vercel Hobby BLOCKS git deploys whose commit committer email isn't linked to a GitHub user ("could not associate the committer with a GitHub user"); the deploy goes to `BLOCKED` and production silently keeps the old build. The repo originally had NO `user.email` set → git auto-generated an unrecognized email → all git deploys blocked. Fixed: `git config user.email "marek.sulik@gmail.com"` / `user.name "mareksulik"`. Always keep a GitHub-verified committer email.
- **Manual/emergency deploy** (bypasses the committer block by removing git metadata): `mv .git /tmp/dotgit && vercel deploy --prod --yes; mv /tmp/dotgit .git`. Vercel auth token: `~/Library/Application Support/com.vercel.cli/auth.json`.

## File Structure
```
/fantasy/
├── all_tour_de_france_riders.csv    # Fantasy rider data (261 riders)
├── combined_riders_data.json        # Integrated dataset (184 riders)
├── pcs_riders_data.csv              # PCS rankings data
├── simple-pcs-script.py             # PCS data scraper
├── manual_mapping_complete.py       # Name mapping database
├── update_tdf_roster.py             # Update to final TdF 2025 roster
├── fantasy_scraper.js               # Original fantasy website scraper
├── app.py                           # Flask web application with auto-updates
├── requirements.txt                 # Python dependencies
└── templates/                       # HTML templates
    ├── base.html                    # Base template with navigation
    ├── index.html                   # Home page
    ├── riders.html                  # Rider browsing with filters
    ├── compare.html                 # Rider comparison tool
    ├── team_builder.html            # Team building with budget
    └── stats.html                   # Statistics and analytics
```