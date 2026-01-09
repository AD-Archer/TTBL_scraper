# ITTF/WTT Data Collection - Agent Task Assignments

**Date:** January 9, 2026
**Status:** Planning Phase

## Overview

We have 4 AI agents working in parallel to discover and build a complete ITTF/WTT data scraping solution. The goal is to collect:

1. **All Players**: Complete database of ITTF players with their IDs
2. **Historical Data**: Rankings and matches from past years
3. **Match Results**: Complete match history with scores
4. **Python Scrapers**: Automated scrapers to fetch and store all data

---

## Agent 1: Player ID Discovery

**Goal:** Find as many valid `IttfId` values as possible through various sources.

### Priority Sources (In Order)

#### 1. results.ittf.link Scraping
```bash
# Target URLs to investigate:
- https://results.ittf.link/
- Search for IttfId in page source
- Look for player profile pages
- Check for AJAX/API calls on player pages
```

**Actions:**
- [ ] Scrape main page for IttfId references
- [ ] Look for player list endpoints
- [ ] Check for Fabrik list views that expose player data
- [ ] Find player profile URLs (e.g., `/player/{id}`)

#### 2. ITTF Official Website
```bash
# Target URLs:
- https://www.ittf.com/rankings/
- https://www.ittf.com/players/
- Search for player directory or search functionality
```

**Actions:**
- [ ] Inspect rankings pages for IttfId in HTML/JS
- [ ] Check player search functionality for API calls
- [ ] Look for pagination - can we enumerate all players?
- [ ] Check network traffic for API endpoints

#### 3. WTT Official Website
```bash
# Target URLs:
- https://www.worldtabletennis.com/
- https://www.worldtabletennis.com/players/
- https://www.worldtabletennis.com/rankings/
```

**Actions:**
- [ ] Search for player directory
- [ ] Check for player profile pages
- [ ] Inspect API calls on rankings pages
- [ ] Look for player search endpoints

#### 4. API Enumeration & Brute Force
```python
# Try sequential IttfId values (100000-200000)
# Use the known working endpoint to test validity

import requests

def test_ittf_id(ittf_id):
    url = "https://wttcmsapigateway-new.azure-api.net/internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
    params = {"IttfId": ittf_id, "q": 1}
    resp = requests.get(url, params=params)
    data = resp.json()
    return data.get("Result") is not None and len(data.get("Result")) > 0
```

**Actions:**
- [ ] Test IttfId range 100000-200000
- [ ] Test IttfId range 110000-130000 (more likely active range)
- [ ] Test random high values (200000-300000)
- [ **CAUTION:** Rate limiting - add delays between requests

#### 5. Tournament & Match References
```bash
# If we find any tournament pages:
- Extract player IDs from match listings
- Check for player roster pages
- Look for team lineup pages
```

**Actions:**
- [ ] Find tournament pages
- [ ] Extract IttfId from match listings
- [ ] Look for team/player rosters

### Expected Output

```json
{
  "players": [
    {
      "IttfId": "121558",
      "name": "WANG Chuqin",
      "country": "CHN",
      "source": "API",
      "verified": true
    }
  ],
  "discovery_methods": {
    "api_brute_force": 150,
    "ittf_website": 80,
    "wtt_website": 120,
    "results_ittf_link": 45
  },
  "total_unique_ids": 395
}
```

---

## Agent 2: Historical Rankings Data

**Goal:** Access rankings data from previous weeks, months, and years.

### Hypothesis Testing

#### Hypothesis 1: URL Parameter Variation
```bash
# Try different URL patterns for historical data

# Current URL (known to work):
https://wttcmsapigateway-new.azure-api.net/internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals

# Variations to test:
- .../RankingsPreviousWeek/
- .../RankingsCurrentMonth/
- .../RankingsPreviousMonth/
- .../Rankings2024/
- .../Rankings2025/
- .../Rankings/2025/12/  # Year/Month pattern
- .../RankingsWeek/52/     # Week number pattern
```

**Actions:**
- [ ] Test 20+ URL pattern variations
- [ ] Test with date parameters (e.g., `?date=2024-12-31`)
- [ ] Test with year/month parameters (e.g., `?year=2024&month=12`)
- [ ] Check for pagination parameters (`?page=2`, `?offset=100`)

#### Hypothesis 2: Endpoint Parameter Variation
```bash
# Add extra parameters to existing endpoint

?IttfId=121558&q=1&year=2024
?IttfId=121558&q=1&month=12
?IttfId=121558&q=1&week=52
?IttfId=121558&q=1&date=2024-12-31
?IttfId=121558&q=1&historical=true
?IttfId=121558&q=1&includeHistory=true
```

**Actions:**
- [ ] Test 15+ parameter combinations
- [ ] Document which parameters are accepted vs ignored
- [ ] Check for different `q` values (`q=2`, `q=3`)

#### Hypothesis 3: Archive/Public Endpoints
```bash
# Look for alternative API endpoints

# Possible paths:
- .../RankingsArchive/
- .../HistoricalRankings/
- .../RankingsHistory/
- .../api/v1/rankings/history
- .../internalttf/rankings/archive
```

**Actions:**
- [ ] Enumerate subdirectories under `/internalttu/`
- [ ] Try common archive/history URL patterns
- [ ] Check for documentation or API spec URLs

#### Hypothesis 4: results.ittf.link Historical Data
```bash
# Check if the Joomla site has historical data

- Look for archives or history sections
- Check for Fabrik lists with historical rankings
- Look for year/month navigation
```

**Actions:**
- [ ] Search for "archive", "history", "past" keywords
- [ ] Check Fabrik lists for time-based data
- [ ] Look for date filter functionality

### Expected Output

```json
{
  "historical_data_available": {
    "by_week": true,
    "by_month": true,
    "by_year": true,
    "earliest_date": "2018-01-01",
    "latest_date": "2026-01-09"
  },
  "endpoints_discovered": {
    "current_week": "https://.../RankingsCurrentWeek/...",
    "previous_week": "https://.../RankingsPreviousWeek/...",
    "archive": "https://.../RankingsArchive/..."
  },
  "sample_data": [
    {
      "IttfId": "121558",
      "date": "2025-12-31",
      "rank": 1,
      "points": 9850
    }
  ]
}
```

---

## Agent 3: Match Data Discovery

**Goal:** Find how to access match results, scores, and game-by-game data.

### Primary Target: Find Authenticated Endpoints

#### Strategy 1: Authentication Bypass or Discovery
```bash
# Check if endpoints require API key or session token

# Try common auth patterns:
- ?apiKey=...
- ?key=...
- ?api_key=...
- ?token=...
- ?X-API-Key=...
- Header: Authorization: Bearer ...
- Header: X-API-Key: ...
```

**Actions:**
- [ ] Test 10+ authentication methods
- [ ] Check for public API key registration
- [ ] Look for developer/API documentation
- [ ] Search for "API key" or "developer" on ITTF/WTT sites

#### Strategy 2: API Version Bypass
```bash
# Try different API versions/paths

Known 401 endpoints:
- /PlayerProfile/GetPlayerProfile
- /Matches/GetMatches
- /HeadToHead/GetHeadToHead

Try variations:
- /internalttu/v1/...
- /internalttu/v2/...
- /public/...
- /api/...
- /publicapi/...
```

**Actions:**
- [ ] Test 15+ path variations
- [ ] Check for version-specific endpoints
- [ ] Look for public vs private endpoint separation

#### Strategy 3: Website Reverse Engineering
```bash
# Inspect ITTF/WTT website for API calls

# Tools: Chrome DevTools, curl, mitmproxy
# Look for:
- Network tab: XHR/Fetch requests
- API base URLs
- Authentication headers
- Request/response formats
```

**Actions:**
- [ ] Load ITTF rankings page, inspect network
- [ ] Load WTT player profile page, inspect network
- [ ] Load match result page, inspect network
- [ ] Document all API calls found

#### Strategy 4: Mobile App API
```bash
# If ITTF/WTT has mobile apps, they may have APIs

# Check app stores for:
- ITTF Results app
- WTT Results app
- Table Tennis official apps

# Reverse engineer app API calls using:
- mitmproxy (proxy traffic)
- Frida (dynamic instrumentation)
```

**Actions:**
- [ ] Search for ITTF/WTT mobile apps
- [ ] Document app API endpoints (if found)
- [ ] Test if mobile endpoints are public

#### Strategy 5: Third-Party Aggregators
```bash
# Sites that aggregate ITTF data may use different APIs

- results.ittf.link (already investigated - API locked)
- tabletennisdaily.com
- tennistable.com
- sports data providers (SportDevs, etc.)
```

**Actions:**
- [ ] Identify 5+ data aggregator sites
- [ ] Check if they expose ITTF player IDs
- [ ] Check if they provide match data
- [ ] Document data sources and reliability

### Secondary Target: Find Alternative Data Sources

#### Option A: Web Scraping (Last Resort)
```python
# If APIs fail, scrape HTML pages

# Targets:
- ITTF match result pages
- WTT match pages
- results.ittf.link match listings
```

**Actions:**
- [ ] Identify HTML structure of match pages
- [ ] Check for anti-scraping measures
- [ ] Evaluate data quality vs API
- [ ] Implement scraper (if viable)

### Expected Output

```json
{
  "match_data_access": {
    "authenticated_endpoints": {
      "status": "locked",
      "auth_method": "unknown",
      "documentation_available": false
    },
    "public_alternatives": {
      "website_scraping": "feasible",
      "mobile_api": "not_found",
      "third_party": "limited"
    }
  },
  "endpoints_found": [
    {
      "url": ".../Matches/GetMatches",
      "status": "requires_auth",
      "auth_required": true
    }
  ],
  "scraping_strategy": {
    "recommended": "website_scraping",
    "confidence": 0.7,
    "notes": "ITTF match pages contain detailed scores"
  }
}
```

---

## Agent 4: Scraper Implementation

**Goal:** Build Python scrapers for all discovered endpoints and data sources.

### Phase 1: Rankings Scraper (Immediate)

**Status:** Can implement now (we have working endpoint)

```python
# File: scrapers/rankings_scraper.py

import requests
import json
from typing import List, Dict
from pathlib import Path

BASE_URL = "https://wttcmsapigateway-new.azure-api.net/internalttu"
RANKINGS_ENDPOINT = f"{BASE_URL}/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"

class RankingsScraper:
    def __init__(self, output_dir: str = "./data/rankings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def get_player_rankings(self, ittf_id: str) -> List[Dict]:
        """Fetch rankings for a single player."""
        params = {"IttfId": ittf_id, "q": 1}
        response = self.session.get(RANKINGS_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("Result", [])

    def batch_fetch(self, ittf_ids: List[str], delay: float = 1.0):
        """Fetch rankings for multiple players."""
        results = {}
        for i, ittf_id in enumerate(ittf_ids, 1):
            try:
                rankings = self.get_player_rankings(ittf_id)
                results[ittf_id] = rankings
                print(f"[{i}/{len(ittf_ids)}] Fetched {ittf_id}")
            except Exception as e:
                print(f"Error fetching {ittf_id}: {e}")
                results[ittf_id] = None
            time.sleep(delay)
        return results

    def save_rankings(self, data: Dict, filename: str = "rankings_current.json"):
        """Save rankings to file."""
        output_file = self.output_dir / filename
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {output_file}")

# Usage
if __name__ == "__main__":
    scraper = RankingsScraper()
    ids = ["121558", "101919", "105649"]
    data = scraper.batch_fetch(ids)
    scraper.save_rankings(data)
```

**Actions:**
- [ ] Implement `rankings_scraper.py`
- [ ] Add error handling and retry logic
- [ ] Add rate limiting
- [ ] Test with 10 known player IDs
- [ ] Add command-line interface

### Phase 2: Player ID Scraper (After Agent 1)

```python
# File: scrapers/players_scraper.py

class PlayersScraper:
    def __init__(self):
        self.known_ids = set()

    def brute_force_ids(self, start: int, end: int):
        """Test sequential IttfId values."""
        valid_ids = []
        for ittf_id in range(start, end + 1):
            if self.test_id(str(ittf_id)):
                valid_ids.append(ittf_id)
                print(f"Found valid ID: {ittf_id}")
            time.sleep(0.5)  # Respect rate limits
        return valid_ids

    def test_id(self, ittf_id: str) -> bool:
        """Test if IttfId exists."""
        # Use RankingsScraper to test
        scraper = RankingsScraper()
        try:
            result = scraper.get_player_rankings(ittf_id)
            return result is not None and len(result) > 0
        except:
            return False
```

**Actions:**
- [ ] Implement `players_scraper.py` (depends on Agent 1 results)
- [ ] Add multi-source ID discovery (website scraping + API)
- [ ] Merge results from different discovery methods
- [ ] Deduplicate and validate IDs

### Phase 3: Historical Rankings Scraper (After Agent 2)

```python
# File: scrapers/historical_rankings_scraper.py

class HistoricalRankingsScraper:
    def __init__(self):
        self.session = requests.Session()

    def fetch_historical_week(self, week_number: int, year: int):
        """Fetch rankings for a specific historical week."""
        # Implementation depends on Agent 2 findings
        pass

    def fetch_year_range(self, start_year: int, end_year: int):
        """Fetch all rankings for a year range."""
        pass

    def save_historical_data(self, data: List[Dict]):
        """Save historical rankings to database/JSON."""
        pass
```

**Actions:**
- [ ] Implement after Agent 2 discovers endpoints
- [ ] Handle pagination (if applicable)
- [ ] Store data with timestamps
- [ ] Create database schema for historical data

### Phase 4: Match Scraper (After Agent 3)

```python
# File: scrapers/matches_scraper.py

class MatchesScraper:
    def __init__(self):
        self.session = requests.Session()

    def get_player_matches(self, ittf_id: str) -> List[Dict]:
        """Fetch all matches for a player."""
        # Implementation depends on Agent 3 findings
        pass

    def get_match_details(self, match_id: str) -> Dict:
        """Fetch detailed match data (scores, games)."""
        pass

    def extract_game_scores(self, match_data: Dict) -> List[Dict]:
        """Extract game-by-game scores from match data."""
        pass
```

**Actions:**
- [ ] Implement after Agent 3 discovers match data access
- [ ] Handle game-by-game scoring data
- [ ] Calculate player statistics (wins, losses, win rates)
- [ ] Store match data with full details

### Phase 5: Integration & CLI

```python
# File: scrapers/main.py

import argparse
from rankings_scraper import RankingsScraper
from players_scraper import PlayersScraper
from matches_scraper import MatchesScraper

def main():
    parser = argparse.ArgumentParser(description="ITTF/WTT Data Scraper")
    parser.add_argument("--discover-players", action="store_true")
    parser.add_argument("--fetch-rankings", action="store_true")
    parser.add_argument("--fetch-matches", action="store_true")
    parser.add_argument("--player-id", type=str, help="Single player ID")
    args = parser.parse_args()

    if args.discover_players:
        scraper = PlayersScraper()
        ids = scraper.brute_force_ids(100000, 130000)
        print(f"Found {len(ids)} players")

    if args.fetch_rankings:
        scraper = RankingsScraper()
        rankings = scraper.get_player_rankings(args.player_id)
        print(rankings)

    if args.fetch_matches:
        scraper = MatchesScraper()
        matches = scraper.get_player_matches(args.player_id)
        print(matches)

if __name__ == "__main__":
    main()
```

**Actions:**
- [ ] Create unified CLI interface
- [ ] Add configuration file support
- [ ] Add logging system
- [ ] Add progress bars (tqdm)
- [ ] Create Docker container for easy deployment

### Expected Output

**File Structure:**
```
ITTF/WTT/
├── scrapers/
│   ├── __init__.py
│   ├── main.py                  # CLI entry point
│   ├── rankings_scraper.py       # ✅ Ready to implement
│   ├── players_scraper.py        # ⏳ Waiting for Agent 1
│   ├── historical_scraper.py     # ⏳ Waiting for Agent 2
│   ├── matches_scraper.py        # ⏳ Waiting for Agent 3
│   └── utils.py                # Shared utilities
├── data/
│   ├── players.json              # Player database
│   ├── rankings_current.json     # Current rankings
│   ├── rankings_historical/     # Historical rankings by date
│   └── matches/                # Match data by player
├── logs/
│   └── scraper.log
└── config.json                  # Scraper configuration
```

**Configuration File:**
```json
{
  "api": {
    "base_url": "https://wttcmsapigateway-new.azure-api.net/internalttu",
    "timeout": 30,
    "rate_limit_delay": 1.0
  },
  "scraper": {
    "max_retries": 3,
    "user_agent": "ITTF-Scraper/1.0",
    "log_level": "INFO"
  },
  "output": {
    "format": "json",
    "compress": true,
    "backup": true
  }
}
```

---

## Agent Coordination

### Dependency Graph

```
Agent 1 (Player Discovery)
    ↓ (provides: player_ids.json)
    ↓
Agent 4 (Scraper: Player ID)
    ↓ (uses: player_ids.json)
    ↓
Agent 2 (Historical Rankings)
    ↓ (provides: historical_endpoints.json)
    ↓
Agent 4 (Scraper: Historical)
    ↓ (uses: historical_endpoints.json)
    ↓
Agent 3 (Match Data)
    ↓ (provides: match_data_access.json)
    ↓
Agent 4 (Scraper: Matches)
    ↓ (uses: match_data_access.json)
    ↓
Complete System ✅
```

### Parallel Work

**Can Work in Parallel:**
- Agent 1, 2, 3: All discovery tasks
- Agent 4: Rankings scraper (no dependencies)

**Sequential Dependencies:**
- Agent 4 other scrapers: Wait for respective discovery agents

### Communication

**Required Shared Files:**
- `research/agents/agent1/player_ids.json` (Agent 1 output)
- `research/agents/agent2/historical_endpoints.json` (Agent 2 output)
- `research/agents/agent3/match_data_access.json` (Agent 3 output)
- `scripts/` (Runnable scrapers/tools)

**Update Frequency:**
- Discovery agents: Report progress every 30 minutes
- Scraper agent: Report when each scraper is ready

---

## Success Criteria

### Minimum Viable System

1. **Player Database**: 100+ unique IttfId values
2. **Current Rankings**: Can fetch rankings for any player
3. **Historical Data**: Can fetch at least 1 year of rankings
4. **Match Data**: Can fetch match results for at least 10 players
5. **Python Scrapers**: All scrapers working and documented

### Complete System

1. **Player Database**: 1000+ unique IttfId values
2. **Historical Rankings**: 5+ years of historical data
3. **Complete Match History**: All matches for top 100 players
4. **Game-by-Game Scores**: Detailed scoring data available
5. **Automated Pipeline**: Run with single command

---

## Timeline Estimates

| **Task** | **Agent** | **Duration** | **Priority** |
|-----------|-----------|--------------|--------------|
| Player ID Discovery | Agent 1 | 4-6 hours | 🔴 Critical |
| Historical Rankings Discovery | Agent 2 | 2-4 hours | 🟡 High |
| Match Data Discovery | Agent 3 | 4-8 hours | 🔴 Critical |
| Rankings Scraper | Agent 4 | 1-2 hours | 🟢 Low |
| Other Scrapers | Agent 4 | 2-4 hours each | 🟡 High |

**Total Estimated Time:** 14-26 hours across all agents

---

## Next Actions for Each Agent

### Agent 1
1. Start with results.ittf.link player discovery
2. Move to ITTF/WTT website scraping
3. Try API brute force on IttfId 110000-130000
4. Document all findings in `research/agents/agent1/player_ids.json`

### Agent 2
1. Test URL pattern variations for historical data
2. Try parameter variations on existing endpoint
3. Check results.ittf.link for archives
4. Document findings in `research/agents/agent2/historical_endpoints.json`

### Agent 3
1. Try authentication bypass methods
2. Test API version variations
3. Inspect ITTF/WTT website network traffic
4. Check for mobile app APIs
5. Document findings in `research/agents/agent3/match_data_access.json`

### Agent 4
1. Implement rankings scraper (can start immediately)
2. Wait for Agent 1 results → implement player ID scraper
3. Wait for Agent 2 results → implement historical scraper
4. Wait for Agent 3 results → implement match scraper
5. Create unified CLI and documentation

---

**Last Updated:** January 9, 2026
**Version:** 1.0
**Status:** Ready for Agent Deployment
