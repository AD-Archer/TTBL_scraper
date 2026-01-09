# TTBL Enhanced Scraper - Complete Guide

## Overview

The enhanced TTBL scraper discovers **all matches** across the entire Bundesliga season (108 matches total, 18 gamedays × 6 matches each) and generates **comprehensive player statistics** including win/loss rates, match metadata, and game-level tracking.

---

## What's New vs Original Scraper

| Feature | Original | Enhanced |
|---------|----------|----------|
| Match Discovery | Homepage only (~12 matches) | All gamedays (108 matches) |
| Player Stats | Basic player list | Complete win/loss tracking with rates |
| Game-Level Data | None | Individual game results per player |
| Statistics | No aggregation | Top players, win rates sorted |
| Metadata | Basic | Comprehensive with timestamps, venues, ranks |
| Reports | None | Multiple JSON reports |

---

## Quick Start

```bash
# Scrape current season (2025-2026)
./scrape_ttbl_enhanced.sh

# Scrape specific season
./scrape_ttbl_enhanced.sh 2024-2025
```

---

## Output Structure

```
ttbl_data/
├── metadata.json                      # Scrape session metadata
├── match_ids.txt                    # All match IDs discovered
├── matches/
│   ├── match_{uuid}.json           # Full match data (108 files)
│   └── ...
├── players/
│   ├── all_players.json            # All players from all matches (with duplicates)
│   └── unique_players.json        # Deduplicated player list
├── stats/
│   ├── player_stats_final.json    # Complete player stats sorted by win rate
│   ├── top_players.json          # Top 20 players (min 5 games)
│   ├── games_data.json          # Individual game results with players
│   └── match_states.json       # Match state breakdown
└── matches_summary.json            # Match summaries with metadata
```

---

## Data Models

### Player Statistics (`stats/player_stats_final.json`)

```json
[
  {
    "id": "bf29638f-9165-4203-982a-6a25f36452be",
    "name": "Bastian Steger",
    "gamesPlayed": 15,
    "wins": 12,
    "losses": 3,
    "winRate": 80,
    "lastMatch": "95c232f8-7ac8-4d66-ad27-1e3cb6205d34"
  }
]
```

**Key Fields:**
- `id`: Player UUID
- `name`: Full name (firstName + lastName)
- `gamesPlayed`: Total games played
- `wins`: Games won
- `losses`: Games lost
- `winRate`: Win percentage (0-100), sorted descending
- `lastMatch`: Last match ID played

### Game Data (`stats/games_data.json`)

```json
[
  {
    "matchId": "95c232f8-7ac8-4d66-ad27-1e3cb6205d34",
    "gameday": "12. Spieltag (2025/2026)",
    "timestamp": 1766239200,
    "gameIndex": 1,
    "gameState": "Finished",
    "winnerSide": "Home",
    "homePlayer": {
      "id": "bf29638f-9165-4203-982a-6a25f36452be",
      "name": "Bastian Steger"
    },
    "awayPlayer": {
      "id": "27279bd6-081a-4869-8b1f-be450c6fcf26",
      "name": "Kristian Karlsson"
    }
  }
]
```

### Match Summary (`matches_summary.json`)

```json
[
  {
    "matchId": "95c232f8-7ac8-4d66-ad27-1e3cb6205d34",
    "matchState": "Finished",
    "gameday": "12. Spieltag (2025/2026)",
    "timestamp": 1766239200,
    "homeTeam": {
      "id": "49d8a280-badc-4fc4-b29b-3047fe1c907c",
      "name": "TSV Bad Königshofen",
      "rank": 7,
      "gameWins": 3,
      "setWins": 10
    },
    "awayTeam": {
      "id": "e01acf29-dd87-45df-99da-1fc0de3e95a7",
      "name": "BV Borussia 09 Dortmund",
      "rank": 4,
      "gameWins": 2,
      "setWins": 8
    },
    "gamesCount": 5,
    "venue": "Sportzentrum Oestertal"
  }
]
```

### Metadata (`metadata.json`)

```json
{
  "scrapeDate": "2025-01-08T19:45:00Z",
  "season": "2025-2026",
  "totalMatches": 108,
  "totalGamedays": 18,
  "uniquePlayers": 72,
  "playersWithStats": 68,
  "totalGamesProcessed": 540,
  "source": "https://www.ttbl.de",
  "version": "2.0"
}
```

---

## Query Examples

### Get Top 10 Players by Win Rate
```bash
jq '.[0:10] | .[] | {name, gamesPlayed, wins, losses, winRate}' ttbl_data/stats/player_stats_final.json
```

### Find All Games for a Player
```bash
PLAYER_ID="bf29638f-9165-4203-982a-6a25f36452be"
jq "[.[] | select(.homePlayer.id == \"$PLAYER_ID\" or .awayPlayer.id == \"$PLAYER_ID\")]" ttbl_data/stats/games_data.json
```

### Get Player Win/Loss Breakdown
```bash
PLAYER_NAME="Bastian Steger"
jq ".[] | select(.name == \"$PLAYER_NAME\") | {name, gamesPlayed, wins, losses, winRate}" ttbl_data/stats/player_stats_final.json
```

### Count Finished vs Scheduled Matches
```bash
jq 'group_by(.matchState) | map({state: .[0].matchState, count: length})' ttbl_data/stats/match_states.json
```

### Get All Matches by Team
```bash
TEAM_NAME="TSV Bad Königshofen"
jq "[.[] | select(.homeTeam.name == \"$TEAM_NAME\" or .awayTeam.name == \"$TEAM_NAME\")]" ttbl_data/matches_summary.json
```

### Get Matches by Date Range
```bash
START_TIME=1766000000
END_TIME=1766500000
jq "[.[] | select(.timestamp >= $START_TIME and .timestamp <= $END_TIME)]" ttbl_data/matches_summary.json
```

### Calculate Player's Win Rate Manually
```bash
PLAYER_NAME="Bastian Steger"
stats=$(jq ".[] | select(.name == \"$PLAYER_NAME\")" ttbl_data/stats/player_stats_final.json)
echo "$stats" | jq '{name, winRate: (.wins / .gamesPlayed * 100 | floor)}'
```

---

## Win/Loss Tracking Logic

### Game-Level Tracking

Each game in a match contributes to player statistics:

- **Game state**: Must be "Finished" (no stats for "Scheduled" or "Live")
- **Home player**: Gets win if `winnerSide == "Home"`, loss otherwise
- **Away player**: Gets win if `winnerSide == "Away"`, loss otherwise
- **Null players**: Games with `null` players are skipped

### Example Match Flow

```
Match: TSV Bad Königshofen vs BV Borussia Dortmund
  Game 1: Bastian Steger (Home) vs Kristian Karlsson (Away) → Winner: Home
    → Steger: +1 win, +1 game
    → Karlsson: +1 loss, +1 game

  Game 2: Daniel Habesohn (Home) vs Anders Lind (Away) → Winner: Away
    → Habesohn: +1 loss, +1 game
    → Lind: +1 win, +1 game

  Game 3: Filip Zeljko (Home) vs Adam Szudi (Away) → Winner: Away
    → Zeljko: +1 loss, +1 game
    → Szudi: +1 win, +1 game

Final Player Stats:
  Steger: 1 game, 1 win, 0 losses, 100% win rate
  Karlsson: 1 game, 0 wins, 1 loss, 0% win rate
  Habesohn: 1 game, 0 wins, 1 loss, 0% win rate
  Lind: 1 game, 1 win, 0 losses, 100% win rate
  Zeljko: 1 game, 0 wins, 1 loss, 0% win rate
  Szudi: 1 game, 1 win, 0 losses, 100% win rate
```

---

## Performance & Rate Limiting

### Scrape Time Estimates

| Matches | Gamedays | Est. Time* |
|---------|-----------|-------------|
| 6 (single gameday) | 1 | ~15 seconds |
| 108 (full season) | 18 | ~4-5 minutes |

\*With 1-second delay between match requests

### Rate Limiting

- Default delay: **1 second** between match requests
- Respect server limits - increase `DELAY` if experiencing issues
- Recommended: scrape during off-peak hours

---

## Troubleshooting

### No Matches Found
```bash
# Check if schedule page structure changed
curl -sL "https://www.ttbl.de/bundesliga/gameschedule/2025-2026/12/all" | head -50

# Test match ID extraction manually
curl -sL "https://www.ttbl.de/bundesliga/gameschedule/2025-2026/12/all" | grep -oP '/bundesliga/gameday/[^"]+'
```

### Missing Player Names
- Scheduled matches may have `null` for players (lineups not announced)
- Check game state - only "Finished" games contribute to stats

### Win Rate Seems Incorrect
- Minimum games filter: `top_players.json` requires 5+ games
- Check `player_stats_final.json` for unfiltered data
- Verify game state is "Finished" (not "Live" or "Scheduled")

### Script Hangs/Fails
```bash
# Verify required tools
which curl jq

# Test API endpoint manually
curl -s "https://www.ttbl.de/api/internal/match/95c232f8-7ac8-4d66-ad27-1e3cb6205d34" | jq '.matchState'
```

---

## Data Freshness & Updates

### Keeping Data Up-to-Date

The scraper doesn't track what's already scraped. To update:

```bash
# Option 1: Scrape entire season (overwrites existing)
./scrape_ttbl_enhanced.sh

# Option 2: Backup old data, scrape new, compare
mv ttbl_data ttbl_data_backup_$(date +%Y%m%d)
./scrape_ttbl_enhanced.sh
diff ttbl_data_backup_20250108 ttbl_data
```

### Season Transition

When season changes (e.g., 2025-2026 → 2026-2027):

```bash
# Archive current season data
mkdir -p archive/2025-2026
mv ttbl_data/* archive/2025-2026/

# Scrape new season
./scrape_ttbl_enhanced.sh 2026-2027
```

---

## Advanced Usage

### Custom Season Scraping

```bash
# Scrape last season
./scrape_ttbl_enhanced.sh 2024-2025

# Scrape custom season (if format matches)
./scrape_ttbl_enhanced.sh 2023-2024
```

### Data Analysis Pipeline

```bash
#!/bin/bash
# Example: Generate weekly player reports

SEASON="2025-2026"
./scrape_ttbl_enhanced.sh "$SEASON"

# Get top 5 players
jq '.[0:5]' ttbl_data/stats/player_stats_final.json > top5.json

# Generate HTML report
cat > report.html << EOF
<!DOCTYPE html>
<html>
<head><title>TTBL Player Stats</title></head>
<body>
<h1>Top 5 Players - $SEASON</h1>
<table>
  <tr><th>Name</th><th>Games</th><th>Wins</th><th>Losses</th><th>Win Rate</th></tr>
$(cat top5.json | jq -r '.[] | "<tr><td>\(.name)</td><td>\(.gamesPlayed)</td><td>\(.wins)</td><td>\(.losses)</td><td>\(.winRate)%</td></tr>"')
</table>
</body>
</html>
EOF
```

---

## Comparison: Original vs Enhanced

### Original Scraper (`scrape_ttbl.sh`)

**Pros:**
- Simple, fast (fewer matches)
- Basic player extraction

**Cons:**
- Homepage-only (~12 matches)
- No win/loss tracking
- No game-level data
- Limited metadata

### Enhanced Scraper (`scrape_ttbl_enhanced.sh`)

**Pros:**
- All season matches (108)
- Complete player statistics
- Game-level tracking
- Multiple report formats
- Comprehensive metadata

**Cons:**
- Slower (more data to fetch)
- Larger storage requirements (~10-15 MB vs ~1 MB)

---

## API Endpoint Reference

### Match Data Endpoint

```
GET https://www.ttbl.de/api/internal/match/{matchId}
```

**No authentication required**

### Schedule Pattern

```
https://www.ttbl.de/bundesliga/gameschedule/{season}/{gameday}/all
```

Examples:
- Current season, gameday 12: `/bundesliga/gameschedule/current/current/all`
- Specific season, gameday 1: `/bundesliga/gameschedule/2025-2026/1/all`

---

## Known Limitations

1. **No historical data**: Only current season available via schedule pages
2. **No live updates**: Scraping is point-in-time snapshot
3. **Missing players**: Scheduled/inactive matches have `null` players
4. **No team stats**: Only individual player stats, not team standings
5. **Manual deduplication**: Script doesn't track already-scraped matches

---

## Future Enhancements

Potential improvements:

- [ ] Incremental scraping (only new matches)
- [ ] Historical season support (if available)
- [ ] Team win/loss statistics
- [ ] Head-to-head player matchups
- [ ] Performance trends over time
- [ ] Database export (SQLite, PostgreSQL)
- [ ] Real-time monitoring (polling for live matches)
- [ ] Cup competition support (Pokal matches)

---

## Changelog

### Version 2.0 (Enhanced Scraper)

- Discover all 108 matches from 18 gamedays
- Game-level player win/loss tracking
- Comprehensive metadata extraction
- Multiple statistical reports
- Sorted player rankings by win rate
- Top 20 players report (min 5 games)
- Match state breakdown

### Version 1.0 (Original Scraper)

- Basic homepage scraping
- Match ID validation
- Simple player extraction
- Match summaries
