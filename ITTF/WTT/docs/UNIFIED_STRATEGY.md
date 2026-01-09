# Unified ITTF/WTT Data Collection Strategy

**Date:** January 9, 2026
**Status:** All Agents Completed - Ready for Implementation

---

## Executive Summary

All 4 agents have completed their discovery phase. We now have a clear path to achieve the unified goal:

### Goal: Collect comprehensive player data with:
- ✅ First name & Last name (split from combined names)
- ✅ Date of Birth (DOB)
- ✅ Nationality
- ✅ All metadata (matches, scores, dates)
- ✅ Separation by gender

---

## Current State Assessment

### What We Have (✅):

1. **195 Player IDs** (Agent 1)
   - Range: 100696 - 146307
   - Source: results.ittf.link rankings pages
   - Categories: Men's Singles, Women's Singles, Boys' Singles, Girls' Singles
   - **Status**: Validated against WTT API

2. **Working Current Rankings API** (Agent 4)
   - Endpoint: `/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals`
   - Provides: PlayerName, Country, Rankings, Points
   - **Status**: Fully functional, no authentication required
   - **Limitation**: Returns combined name (e.g., "WANG Chuqin")

3. **Match Data Discovery** (Agent 3)
   - Found results.ittf.link Fabrik API
   - **Status**: Returns HTML (not JSON) - requires browser automation
   - Endpoint: `listid=31` (Player matches)
   - Provides: Match IDs, Player IDs, Names, Game Scores, Winners

### What We Don't Have (❌):

1. **Player Profile Data**
   - ❌ Date of Birth (DOB)
   - ❌ First name & Last name (separated)
   - ❌ Nationality (separate from country code)
   - **Status**: WTT API endpoints (`/PlayerProfile/GetPlayerProfile`) return 401 Unauthorized

2. **Comprehensive Match Database**
   - ❌ Match data for all players (only sample data)
   - ❌ Historical matches
   - ❌ Game-by-game scores for all matches
   - **Status**: Fabrik API returns HTML, not JSON - needs scraping

3. **Gender-Separated Player List**
   - ❌ 195 IDs are from rankings but not gender-identified
   - **Status**: Need to map player IDs to gender based on event codes

4. **Historical Rankings**
   - ❌ No public historical API
   - ❌ HTML files blocked by Cloudflare
   - **Status**: Requires browser automation (Playwright/Selenium)

---

## Unified Data Collection Strategy

### Phase 1: Player Database Foundation (Priority 1)

**Objective**: Build comprehensive player database with metadata and gender separation

**Steps**:

#### 1.1 Validate All 195 Player IDs with WTT API
```bash
# Use Agent 4's rankings scraper
cd ITTF/WTT/scripts
python3 wtt_ittf_scraper.py --batch <all 195 IDs from agent1>
```

**Output**: For each IttfId, collect:
- PlayerName (combined)
- CountryCode
- AssociationCountryCode
- **SubEventCode** (MS=Men's Singles, WS=Women's Singles)
- Ranking points and position

**Gender Classification**:
```
Men's Singles (MS): Men
Women's Singles (WS): Women
Men's Doubles (MDI): Men (doubles)
Women's Doubles (WDI): Women (doubles)
Mixed Doubles (XD/XDI): Mixed
```

#### 1.2 Map 195 IDs to Event Types (Gender Separation)

Using WTT rankings data, create player metadata file:

```json
{
  "players": {
    "121558": {
      "ittf_id": "121558",
      "name_combined": "WANG Chuqin",
      "country_code": "CHN",
      "nationality": "China",
      "gender": "male",
      "event_types": ["MS", "MDI", "XDI"],
      "source": "rankings_validation"
    }
  }
}
```

**Implementation**: Script to batch query rankings API and classify gender based on SubEventCode

---

### Phase 2: Match Data Collection (Priority 2)

**Objective**: Collect all match data with scores and dates

**Challenge**: Fabrik API returns HTML, not JSON

**Solution A**: Web Scraping Approach
```python
# Use browser automation (Playwright recommended)
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_player_matches(player_id):
    url = "https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=31&format=json&vw_matches___player_a_id[value]={player_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Required for JavaScript
        page = browser.new_page()
        page.goto(url)

        # Wait for page load and JavaScript execution
        page.wait_for_timeout(5000)

        # Extract match data from table structure
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # Parse matches table
        matches = parse_fabrik_table(soup)

        browser.close()
        return matches
```

**Solution B**: Agent 4's Fabrik Scraper (from Agent 3 findings)
```python
# File: scripts/fabrik_match_scraper.py
# Agent 3 recommended implementation
# Extract player IDs and match data from Fabrik lists
```

**Data to Collect**:
- Match ID
- Tournament ID and Name
- Date/Year of match
- Player A ID, Name, Association
- Player X ID, Name, Association
- Player Y ID, Name, Association (doubles)
- Game scores (space-separated, parseable)
- Winner ID and Name
- Event Type (U11MS, U11WS, etc.)
- Stage (Qualification, Main Draw, etc.)
- Round

---

### Phase 3: Player Profile Enrichment (Priority 3)

**Objective**: Collect DOB and split names

**Challenge**: WTT PlayerProfile API requires authentication (401)

**Strategies**:

#### Strategy A: Scrape ITTF Player Profile Pages
```bash
# Pattern: https://www.ittf.com/players/{PLAYER_NAME}
# Example from rankings: "WANG Chuqin"
# URL might be: https://www.ittf.com/players/wang-chuqin
```

#### Strategy B: Extract from Results HTML
```python
# Match HTML contains player names with associations
# Extract association codes and map to nationalities
nationality_map = {
  "CHN": "China",
  "JPN": "Japan",
  "USA": "United States",
  "GER": "Germany",
  # ... map all association codes
}
```

#### Strategy C: Web Search Fallback
```python
# For top 100 players, search DOB
# Use Google or Wikipedia to find birth dates
# Time-intensive but accurate for key players
```

**Data Model for Player Profiles**:
```json
{
  "player": {
    "ittf_id": "121558",
    "first_name": "Chuqin",
    "last_name": "Wang",
    "name_combined": "WANG Chuqin",
    "dob": "2000-05-23",  # To be discovered
    "nationality": "China",
    "country_code": "CHN",
    "gender": "male",
    "height": null,
    "weight": null,  # Available on some pages
    "playing_style": "Right-handed",  # Available on some pages
    "rankings": {
      "current_ms_rank": 1,
      "current_ws_rank": 5,
      "highest_ms_rank": 1
    },
    "matches_count": 0  # To be populated
  }
}
```

---

### Phase 4: Historical Data Collection (Priority 4)

**Objective**: Access historical rankings and match data

**Challenge**: No public API, HTML files blocked by Cloudflare

**Strategy A**: Browser Automation for HTML Files
```python
from playwright.sync_api import sync_playwright

def scrape_historical_rankings(year, month, week, event_type):
    url = f"https://www.ittf.com/wp-content/uploads/{year:04d}/{month:02d}/{year}_{week:02d}_SEN_{event_type}.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Required for Cloudflare
        page = browser.new_page()
        page.goto(url)

        # Wait for Cloudflare challenge and page load
        page.wait_for_timeout(10000)

        html = page.content()
        # Parse table structure
        rankings = parse_rankings_table(html)

        browser.close()
        return rankings

# Usage:
# Scrape 2024 rankings (men's singles)
rankings_2024 = scrape_historical_rankings(2024, 12, 52, "MS")
```

**Coverage**: Weekly rankings available since January 2001 (per Agent 2 findings)

**Rate Limiting**: Add 2-5 second delays between requests to avoid Cloudflare blocking

---

## Data Model Specifications

### Final Player Record Structure
```json
{
  "players": [
    {
      "ittf_id": "121558",
      "first_name": "Chuqin",
      "last_name": "Wang",
      "name_combined": "WANG Chuqin",
      "dob": "2000-05-23",
      "gender": "male",
      "nationality": "China",
      "country_code": "CHN",
      "country_name": "China",
      "association_country_code": "CHN",
      "association_country_name": "China",
      "category_code": "SEN",
      "age_category_code": "SEN",
      "height_cm": null,
      "weight_kg": null,
      "playing_hand": null,
      "equipment": null,
      "rankings": {
        "current_ms": {"year": 2026, "week": 2, "rank": 1, "points": 9925},
        "current_ws": {"year": 2026, "week": 2, "rank": 5, "points": 5561},
        "current_mdi": {"year": 2026, "week": 2, "rank": 3, "points": 4700},
        "career_high_ms": 1,
        "career_high_ws": null
      },
      "matches": [
        {
          "match_id": "10602874",
          "tournament_id": "3274",
          "tournament_name": "WTT Youth Contender San Francisco 2026",
          "date": "2026-06-15",
          "stage": "Main Draw",
          "round": "Final",
          "player_a": {"ittf_id": 209656, "name": "SUN Frank (USA)", "association": "USA"},
          "player_b": {"ittf_id": 209645, "name": "BAVISKAR Shuban (USA)", "association": "USA"},
          "player_x": {"ittf_id": 209645, "name": "BAVISKAR Shuban (USA)", "association": "USA"},
          "player_y": null,
          "games": [
            {"game": 1, "score_a": 11, "score_b": 3},
            {"game": 2, "score_a": 11, "score_b": 3},
            {"game": 3, "score_a": 8, "score_b": 11},
            {"game": 4, "score_a": 11, "score_b": 8}
          ],
          "winner_id": 209645,
          "winner_name": "BAVISKAR Shuban",
          "walkover": false
        }
      ]
    }
  ]
}
```

### File Structure
```
data/
├── players/
│   ├── players_raw.json           # All 195 players with basic info
│   ├── players_enriched.json     # Full profiles with DOB, names split, etc.
│   ├── players_gender_classified.json  # Men and Women separated
│   └── players_active.json         # Players with recent match data
├── matches/
│   ├── matches_2025.json
│   ├── matches_2024.json
│   └── matches_historical/          # Backfill 2018-2025
├── rankings/
│   ├── rankings_current.json       # Current week rankings
│   └── rankings_historical/        # Weekly historical rankings
└── metadata/
    ├── scrape_session.json           # Session tracking
    └── data_quality_report.json      # Completeness metrics
```

---

## Implementation Priority Order

### Immediate (Can Start Now):
1. ✅ **Validate all 195 player IDs** with WTT rankings API
2. ✅ **Extract gender** from SubEventCode in rankings data
3. ✅ **Create player database** with metadata
4. ✅ **Build Fabrik web scraper** for match data

### Secondary (Requires Research):
5. ⏳ **Discover DOB** via player profile scraping or web search
6. ⏳ **Split names** into first/last (parse combined names)
7. ⏳ **Scrape player profiles** for height, weight, playing style

### Tertiary (After 1-2 Complete):
8. ⏳ **Collect match data** for top 50 players
9. ⏳ **Collect match data** for all 195 players (with rate limiting)
10. ⏳ **Historical rankings backfill** via browser automation

---

## Agent-Specific Tasks

### Agent 1 (Player ID Discovery) - ✅ Complete
- [x] Discovered 195 unique player IDs
- [x] Validated against WTT API
- [x] Covered multiple ranking categories

### Agent 2 (Historical Rankings) - ✅ Complete
- [x] Confirmed no public historical API
- [x] Identified HTML file pattern (blocked by Cloudflare)
- [x] Found third-party alternatives (SportDevs, Sportradar)
- **Next Step**: Agent 4 to implement browser automation for historical data

### Agent 3 (Match Data) - ✅ Complete
- [x] Discovered Fabrik API (primary source)
- [x] Found 5 data access methods
- [x] WTT Azure API endpoints locked (401)
- [x] Provided sample Fabrik data structure
- **Next Step**: Agent 4 to implement Fabrik scraper with browser automation

### Agent 4 (Scraper Implementation) - ✅ Complete
- [x] Implemented working rankings scraper
- [x] Ready to expand for match data
- [x] CLI interface with batch support
- **Next Step**: Implement Fabrik scraper and browser automation

---

## Key Technical Challenges & Solutions

| Challenge | Impact | Solution |
|------------|--------|-----------|
| **WTT API Authentication** | Cannot get player profiles or historical rankings | Use Fabrik HTML scraping with Playwright/Selenium |
| **Cloudflare Protection** | Blocks direct HTML access | Browser automation (headless=False) with timeouts |
| **Fabrik API HTML Output** | Returns HTML, not JSON | BeautifulSoup parsing with table extraction |
| **Player Name Format** | Combined "WANG Chuqin" | Parse on space: "WANG" + " " + "Chuqin" |
| **Gender Classification** | 195 IDs not separated | Map SubEventCode to gender (MS=male, WS=female) |
| **Rate Limiting** | Unknown limits | Add 2-5 second delays between requests |
| **Data Volume** | Thousands of matches | Batch processing with progress tracking |

---

## Success Criteria

### Minimum Viable Product:
- [ ] 195 players with IttfId, Name, Country, Gender
- [ ] 50+ players with DOB, First Name, Last Name
- [ ] Match data for 50+ players
- [ ] Game-by-game scores for all matches
- [ ] Current rankings for all players
- [ ] Historical rankings for at least 1 year

### Complete Product:
- [ ] 195 players with full profiles
- [ ] Match data for all players
- [ ] Historical rankings for 2018-2025
- [ ] Gender-separated player databases
- [ ] Unified JSON structure for all data types

---

## Next Immediate Actions

1. **Create batch validation script**
   - Script to query WTT API for all 195 player IDs
   - Extract SubEventCode for gender classification
   - Save to `data/players/players_raw.json`

2. **Implement Fabrik web scraper**
   - Based on Agent 3's findings
   - Use Playwright for JavaScript rendering
   - Extract match data from HTML tables
   - Parse game scores from space-separated strings

3. **Create name parser**
   - Split combined names (e.g., "WANG Chuqin" → first: "WANG", last: "Chuqin")
   - Handle international naming conventions

4. **Implement historical rankings scraper**
   - Browser automation for ITTF HTML files
   - Weekly backfill for desired year range
   - Cloudflare challenge handling with retries

5. **Create unified data pipeline**
   - Master script to coordinate all scrapers
   - Progress tracking and error handling
   - Data quality validation and deduplication

---

**Total Duration**: All agents completed in ~45-60 minutes
**Status**: Discovery Complete ✅ | Ready for Implementation ⚡
**Priority**: Start with Player Validation and Match Data Collection

---

## File References

- Agent 1: `/ITTF/WTT/research/agents/agent1/findings.md`
- Agent 1: `/ITTF/WTT/research/agents/agent1/player_ids.json`
- Agent 2: `/ITTF/WTT/research/agents/agent2/findings.md`
- Agent 2: `/ITTF/WTT/research/agents/agent2/historical_endpoints.json`
- Agent 3: `/ITTF/WTT/research/agents/agent3/findings.md`
- Agent 3: `/ITTF/WTT/research/agents/agent3/match_data_access.json`
- Agent 4: `/ITTF/WTT/research/agents/agent4/findings.md`
- Agent 4: `/ITTF/WTT/scripts/wtt_ittf_scraper.py`

---

## End of Unified Strategy
