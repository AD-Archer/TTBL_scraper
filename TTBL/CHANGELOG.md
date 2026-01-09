# Changelog

All notable changes to TTBL scraper functionality will be documented in this file.

## [2.2] - 2026-01-09

### Added
- **Graceful Gameday Handling**
  - Script now handles missing gamedays without failing
  - Set `NUM_GAMEDAYS` to high values (e.g., 30) to collect as many gamedays as possible
  - Skipped gamedays are reported with reason (HTTP 404, no matches, network error)
  - Tracks successful vs failed gamedays
- **Data Coverage Documentation** (`docs/DATA_COVERAGE.md`)
  - Complete analysis of real-time data capabilities
  - Scraper can fetch results **as soon as matches finish** (no caching)
  - Comprehensive catalog of 50+ available data fields
  - Point-by-point scoring data with millisecond precision
  - Analysis of missing/not-available data
  - Data quality metrics and recommended filters
- **README Updates**
  - Added data freshness section highlighting real-time capabilities
  - Updated features list to emphasize live data access
  - Added reference to DATA_COVERAGE.md for complete details

### Documented
- **Real-Time Capabilities**
  - API provides live match state tracking (Finished, Live, Inactive)
  - `updateCount` field shows number of scoring updates (e.g., 483 updates per match)
  - `scoringUpdates` array contains every point, set, timeout with timestamps
  - No caching on scraper side - fresh data on every run
- **Available Data**
  - Match-level: ID, state, timestamp, score, attendance, venue
  - Team-level: ID, name, rank, standings, logo, game/set/ball counts
  - Player-level: ID, name, photo, lineup, substitutes
  - Game-level: 5 games per match, set-by-set scores, winner
  - Advanced stats: Points on serve/return, leads, streaks, lucky shots, timeouts
  - Point-by-point: Every point with bwRating, ace, error, lucky/net/edge flags
- **Missing Data**
  - Historical standings (can calculate from results)
  - Player demographics (only name/ID/photo available)
  - Team composition history/transfers
  - Match officials/referees
  - Coaching data
  - Video content (links only)

### Notes
- Season configuration in `scrape_ttbl_enhanced.py` can be changed to scrape past/current/future seasons
- Recommended pattern: Run scraper regularly to get latest finished match results

---

## [2.1] - 2026-01-08

### Added
- **ELO Data Verification** (`verify_elo_data.py`)
  - Python script to verify data quality for ELO rating system
  - Checks player tracking, win/loss data, timestamps, and game completeness
  - Identifies 231 valid games out of 330 total (filtered for quality)
  - Provides detailed statistics and sample data
- **ELO Data Verification Documentation** (`docs/ELO_DATA_VERIFICATION.md`)
  - Complete analysis of data requirements for ELO system
  - Verification of all required fields (players, wins, scores, dates)
  - Quality filtering recommendations
  - Implementation guidance

### Changed
- **Script Execution**: Converted from shell wrapper to direct Python execution
  - Removed `scrape_ttbl_enhanced.sh` wrapper script
  - Updated to `python3 scrape_ttbl_enhanced.py --season 2024-2025` format
  - Simplified project structure (Python-only)
- **Documentation Structure**: Moved CHANGELOG.md to docs/ folder for GitHub
- **README Updates**
  - Updated execution commands for Python-only approach
  - Added project structure with new verification script
  - Added ELO verification documentation reference
  - Updated version to v2.1

### Removed
- **`scrape_ttbl_enhanced.sh`** - Shell wrapper script (replaced with direct Python execution)

---

## [2.0] - 2025-01-08

### Added
- **Enhanced Scraper** (`scrape_ttbl_enhanced.sh`)
  - Discover all 108 matches from 18 gamedays (vs ~12 from homepage)
  - Game-level player win/loss tracking
  - Comprehensive player statistics with win rates
  - Multiple JSON reports and metadata
- **Player Statistics**
  - Individual game results tracking
  - Win/loss counts per player
  - Win rate calculation (sorted descending)
  - Top 20 players report (minimum 5 games)
- **Game Data** (`stats/games_data.json`)
  - Individual game results with player IDs
  - Match metadata (gameday, timestamp)
  - Winner side tracking
- **Match Metadata**
  - Team ranks and game/set wins
  - Venue information
  - Gameday names
  - Timestamps
- **Comprehensive Reports**
  - `player_stats_final.json` - All player stats sorted by win rate
  - `top_players.json` - Top 20 players (5+ games minimum)
  - `match_states.json` - Match state breakdown
  - `metadata.json` - Scrape session metadata
- **Season Parameter**
  - Scrape specific season: `./scrape_ttbl_enhanced.sh 2024-2025`
  - Default: 2025-2026

### Changed
- **Match Discovery**: From homepage UUID extraction → Schedule page gameday iteration
- **Data Structure**: From flat player list → Nested player statistics with game history
- **Output Size**: ~1 MB → ~10-15 MB (more comprehensive data)

### Fixed
- Game player data field names (supports both `homePlayer` and `homeLeaguePlayer`)
- Variable name typo (`NUM_GAME DAYS` → `NUM_GAMEDAYS`)

### Documentation
- Added `ENHANCED_SCRAPER_GUIDE.md` with comprehensive usage guide
- Updated `HOW_TO_SCRAPE.md` to reference enhanced scraper
- Added query examples for all data types
- Added troubleshooting section
- Added data model documentation

---

## [1.0] - Initial Release

### Added
- **Basic Scraper** (`scrape_ttbl.sh`)
  - Homepage match ID discovery
  - Match data fetching
  - Basic player extraction
  - Match summaries
- **Documentation**
  - `HOW_TO_SCRAPE.md`
  - `TTBL_SCRAPING_GUIDE.md`
  - `TTBL_API_CONSOLIDATED.md`
  - `TTBL_API_ENDPOINTS.md`
  - `TTBL_API_AGENT_BRIEF.md`
