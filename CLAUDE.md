# Fantasy TdF Helper - Claude Context

## Project Overview
Web application to help users select better riders for Tour de France fantasy league (https://fantasybytissot.letour.fr).

## Current Status
- ✅ Fantasy rider data scraped (261 riders in `all_tour_de_france_riders.csv`)
- ✅ PCS scraper with advanced name matching (`simple-pcs-script.py`)
- ✅ 100% data integration - all 261 riders matched with PCS data
- ✅ Flask web application with rider listing and filtering
- ✅ Rider comparison tool implemented
- ✅ Team builder with budget optimization
- ✅ Statistics page with charts and insights
- ✅ All text converted to English
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

## Key Features to Implement
1. Rider data integration (fantasy + PCS)
2. Filtering/sorting by category, price, points
3. Rider comparison tool
4. Team builder with 100-credit budget constraint
5. Value analysis and recommendations

## Development Commands
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install requests beautifulsoup4 pandas flask

# Run PCS data collection (REQUIRED FIRST)
python simple-pcs-script.py

# Start web application (use nohup for background)
source venv/bin/activate && nohup python app.py > app.log 2>&1 &
# Then visit: http://localhost:8085
```

## File Structure
```
/fantasy/
├── all_tour_de_france_riders.csv    # Fantasy rider data
├── simple-pcs-script.py             # PCS scraper
├── fantasy_scraper.js               # Original fantasy scraper
├── app.py                           # Flask web application
├── combined_riders_data.json        # Integrated dataset
└── templates/                       # HTML templates
    ├── base.html                    # Base template with navigation
    ├── index.html                   # Home page
    ├── riders.html                  # Rider browsing with filters
    ├── compare.html                 # Rider comparison tool
    ├── team_builder.html            # Team building with budget
    └── stats.html                   # Statistics and analytics
```