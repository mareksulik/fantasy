# Fantasy TdF Helper - Claude Context

## Project Overview
Web application to help users select better riders for Tour de France fantasy league (https://fantasybytissot.letour.fr).

## Current Status
- ✅ Fantasy rider data scraped (261 riders in `all_tour_de_france_riders.csv`)
- ✅ PCS scraper with advanced name matching (`simple-pcs-script.py`)
- ✅ 100% data integration - all riders matched with PCS data
- ✅ Updated to final TdF 2025 roster - 184 riders (`update_tdf_roster.py`)
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