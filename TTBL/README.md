# TTBL Scraper

A web scraper for the German Table Tennis League (TTBL) that extracts match data, player statistics, and game results from the TTBL website.

## Features

- **Real-time data access** - Scrapes live data from TTBL API; results available as soon as matches finish
- Scrapes all matches from the TTBL Bundesliga
- Extracts player information and statistics
- Tracks win/loss rates per player
- Stores data in structured JSON format
- Multiple query examples for data analysis
- Point-by-point scoring data with millisecond precision

## Quick Start

### Run Enhanced Scraper
```bash
# Scrape current season
python3 scrape_ttbl_enhanced.py

# Edit script to change season
# Modify SEASON and NUM_GAMEDAYS in scrape_ttbl_enhanced.py
# SEASON = "2024-2025"
# NUM_GAMEDAYS = 24  # Set high (e.g., 30) - script skips non-existent gamedays
```

**Time:** ~4-5 minutes for full season

### Check Results
```bash
# View metadata
cat ttbl_data/metadata.json | jq '.'

# Get top 10 players by win rate
jq '.[0:10] | .[] | {name, gamesPlayed, wins, losses, winRate}' ttbl_data/stats/player_stats_final.json

# Verify data for ELO system
python3 verify_elo_data.py
```

## Project Structure

```
.
├── scrape_ttbl_enhanced.py      # Python scraper script
├── verify_elo_data.py           # Data verification for ELO system
├── README.md                     # This file
├── .gitignore                    # Git ignore patterns
├── docs/                         # Documentation
│   ├── CHANGELOG.md             # Version history
│   ├── ELO_DATA_VERIFICATION.md # ELO system data verification
│   └── ENHANCED_SCRAPER_GUIDE.md # Detailed guide
└── ttbl_data/                    # Output data folder
    ├── metadata.json             # Scrape session metadata
    ├── match_ids.txt            # All match IDs
    ├── matches/                  # Individual match JSON files
    ├── players/                  # Player data
    └── stats/                    # Player statistics and game results
```

## Requirements

- Python 3.x
- `requests` library
- `jq` (for JSON querying, optional but recommended)

### Install dependencies
```bash
pip install requests
```

### Install jq (Linux)
```bash
sudo apt install jq  # Debian/Ubuntu
sudo dnf install jq  # Fedora
```

## Data Output

### Enhanced Scraper creates:
- `metadata.json` - Scrape session metadata
- `match_ids.txt` - All 108 match IDs
- `matches/match_{uuid}.json` - Full match data for each match
- `players/all_players.json` - All players with duplicates
- `players/unique_players.json` - Deduplicated player list
- `stats/player_stats_final.json` - Player stats sorted by win rate
- `stats/top_players.json` - Top 20 players (min 5 games)
- `stats/games_data.json` - Individual game results
- `stats/match_states.json` - Match state breakdown
- `matches_summary.json` - Match summaries with metadata

## Player Statistics Example

```json
{
  "id": "bf29638f-9165-4203-982a-6a25f36452be",
  "name": "Bastian Steger",
  "gamesPlayed": 15,
  "wins": 12,
  "losses": 3,
  "winRate": 80,
  "lastMatch": "95c232f8-7ac8-4d66-ad27-1e3cb6205d34"
}
```

## Documentation

- **[`docs/DATA_COVERAGE.md`](docs/DATA_COVERAGE.md)** - **Data freshness, complete data catalog, and what's missing**
- **[`docs/ENHANCED_SCRAPER_GUIDE.md`](docs/ENHANCED_SCRAPER_GUIDE.md)** - Complete guide with data models, query examples, and troubleshooting
- **[`docs/ELO_DATA_VERIFICATION.md`](docs/ELO_DATA_VERIFICATION.md)** - Data verification for ELO rating system implementation
- **[`docs/CHANGELOG.md`](docs/CHANGELOG.md)** - Version history and changes

## API Endpoints

The scraper uses the following TTBL endpoints (no authentication required):

```
Match Data:  GET https://www.ttbl.de/api/internal/match/{matchId}
Schedule:    https://www.ttbl.de/bundesliga/gameschedule/{season}/{gameday}/all
```

## Rate Limiting

- Default: 1 second delay between requests
- Be respectful to the server
- If rate limited: Increase `DELAY` variable in the script

## Troubleshooting

### Data Quality Issues?
Run the verification script:
```bash
python3 verify_elo_data.py
```

### No matches found?
Check if schedule page structure changed:
```bash
curl -sL "https://www.ttbl.de/bundesliga/gameschedule/2025-2026/1/all" | head -50
```

### Player names missing?
- Scheduled matches have `null` players (lineups not announced)
- Only "Finished" games count for stats

## Data Freshness & Real-Time Capabilities

The scraper provides **up-to-date results as soon as matches finish**. Since it fetches data directly from TTBL's live API, there's no caching delay - when TTBL marks a match as "Finished", the scraper can immediately retrieve complete results.

**Key Points:**
- ✅ No caching - fresh data on every run
- ✅ Live match state tracking (Finished, Live, Inactive)
- ✅ Point-by-point scoring with millisecond timestamps
- ⚠️ Polling-based (run scraper to check for updates)
- ⚠️ No incremental scraping yet (fetches entire season, ~4-5 min)

**For complete details**, see **[`docs/DATA_COVERAGE.md`](docs/DATA_COVERAGE.md)** for:
- Real-time data capabilities
- Complete data catalog (50+ fields available)
- Missing data analysis
- Data quality metrics

## License

This project is for educational purposes only. Please respect the TTBL website's terms of service.

---

**Last Updated:** January 9, 2026
**Version:** Enhanced Scraper v2.1
