# Fantasy TdF Helper

A comprehensive web application to help users select better riders for the Tour de France fantasy league at [Fantasy by Tissot](https://fantasybytissot.letour.fr).

## Features

### 🚴‍♂️ Rider Database
- Complete database of 261 Tour de France riders
- 100% integration with ProCyclingStats (PCS) data
- Real-time 2025 season points and rankings
- 5-tier value rating system (Excellent/Great/Good/Average/Poor)

### 🔍 Advanced Filtering
- Filter by category (Leaders/Sprinters/Climbers/All-rounders)
- Filter by team (22 professional cycling teams)
- Price range filtering (5-27 credits)
- Multiple sorting options (value, points, price, name)

### ⚖️ Rider Comparison
- Side-by-side comparison of multiple riders
- Detailed statistics including PCS points, rankings, and value ratings
- Easy addition/removal of riders from comparison

### 🏆 Team Builder
- Intelligent team optimization with multiple strategies
- Budget constraint enforcement (100 credits max)
- Team limit rules (max 3 riders per team, exactly 8 riders total)
- Manual team building with real-time validation
- Team export functionality

### 📊 Statistics Dashboard
- Comprehensive analytics and insights
- Interactive charts showing price distribution and value categories
- Category-wise performance statistics
- Team and rider performance metrics

## Technology Stack

- **Backend**: Python Flask
- **Data Processing**: pandas, requests, BeautifulSoup
- **Frontend**: Bootstrap 5, Chart.js
- **Data Sources**: Fantasy TdF + ProCyclingStats

## Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fantasy
```

2. Set up virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

3. Install dependencies:
```bash
pip install requests beautifulsoup4 pandas flask
```

4. Run the application:
```bash
source venv/bin/activate && nohup python app.py > app.log 2>&1 &
```

5. Open your browser and visit:
```
http://localhost:8085
```

## Usage

### Browsing Riders
1. Visit the **Riders** page to browse all available riders
2. Use filters to narrow down your search by category, team, or price
3. Sort riders by value (points per credit), total points, price, or name
4. Click "Compare" to add riders to comparison view

### Comparing Riders
1. Select multiple riders from the main list
2. View side-by-side comparison with detailed statistics
3. Add or remove riders from the comparison dynamically

### Building Teams
1. Go to **Team Builder** page
2. Use **Optimize Team** for automated team selection with different strategies:
   - **Best Value**: Maximizes points per credit ratio
   - **Highest Points**: Selects riders with most PCS points
   - **Balanced**: Combines value and points considerations
3. Or manually build your team by adding riders from each category
4. Export your final team as JSON

### Viewing Statistics
1. Check the **Statistics** page for comprehensive analytics
2. View category breakdowns, price distributions, and performance insights
3. Use charts to understand value distribution across riders

## File Structure

```
/fantasy/
├── app.py                           # Main Flask application
├── simple-pcs-script.py             # PCS data scraper
├── all_tour_de_france_riders.csv    # Original fantasy rider data
├── pcs_riders_data.csv              # PCS data for all riders
├── combined_riders_data.json        # Integrated dataset
├── combined_riders_data.csv         # Integrated dataset (CSV)
├── templates/                       # HTML templates
│   ├── base.html                    # Base template with navigation
│   ├── index.html                   # Home page
│   ├── riders.html                  # Rider browsing with filters
│   ├── compare.html                 # Rider comparison tool
│   ├── team_builder.html            # Team building interface
│   └── stats.html                   # Statistics dashboard
├── venv/                            # Virtual environment
├── app.log                          # Application logs
├── CLAUDE.md                        # Development context
└── README.md                        # This file
```

## Data Integration

The application integrates two main data sources:

1. **Fantasy Data**: Rider names, teams, categories, and prices from the official fantasy league
2. **PCS Data**: Real performance data including 2025 season points, rankings, and detailed statistics

All 261 riders have been successfully matched between these sources, providing complete and accurate data for analysis.

## Team Building Rules

Fantasy TdF has specific constraints that the application enforces:

- **Budget**: Maximum 100 credits total
- **Team Size**: Exactly 8 riders required
- **Team Limit**: Maximum 3 riders from any single professional team
- **Categories**: Riders from Leaders, Sprinters, Climbers, and All-rounders

## Value Rating System

Riders are automatically classified into 5 value tiers based on their points-per-credit ratio:

- **Excellent**: >50 points per credit (green)
- **Great**: 35-50 points per credit (light green)
- **Good**: 20-35 points per credit (blue)
- **Average**: 10-20 points per credit (yellow)
- **Poor**: <10 points per credit (red)

## Contributing

This project was developed to provide better insights for fantasy cycling enthusiasts. Feel free to suggest improvements or report issues.

## License

This project is for educational and personal use. All rider data is sourced from publicly available information.