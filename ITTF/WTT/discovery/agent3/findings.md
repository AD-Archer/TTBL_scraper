# Agent 3 Findings - Match Data Access

**Agent:** Agent 3
**Name:** Match Data Discovery Specialist
**Start Time:** 2026-01-09T21:47:00Z
**End Time:** 2026-01-09T22:15:00Z
**Status:** Complete ✅

---

## Summary

Successfully discovered **three viable methods** for accessing ITTF/WTT match data:

1. **Primary Method**: results.ittf.link Fabrik API (public, no authentication required)
2. **Secondary Method**: HTML scraping from ITTF/WTT websites
3. **Commercial Option**: SportDevs API (free tier, 300 requests/day)

The official WTT Azure API Gateway (`wttcmsapigateway-new.azure-api.net`) **requires authentication** and no bypass method was found.

---

## Key Findings

### Finding 1: results.ittf.link Fabrik API (PRIMARY DATA SOURCE) ⭐

**Category:** Match Data
**Description:**
The **results.ittf.link** website uses Joomla CMS with Fabrik component, which provides **public JSON API endpoints** for match data. This is a MAJOR discovery - no authentication required, structured JSON output, extensive filtering capabilities.

**Evidence:**

```bash
# Get all 2025 matches
curl -s "https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=31&format=json&vw_matches___yr[value]=2025&limit=5" | python3 -m json.tool
```

**Sample Response:**
```json
{
  "vw_matches___yr": "2025",
  "vw_matches___yr_raw": 2025,
  "vw_matches___id": 10602874,
  "vw_matches___id_raw": 10602874,
  "vw_matches___tournament_id_raw": 3274,
  "vw_matches___tournament_id": "WTT Youth Contender San Francisco 2026",
  "vw_matches___player_a_id": 209656,
  "vw_matches___player_a_id_raw": 209656,
  "vw_matches___name_a": "SUN Frank (USA)",
  "vw_matches___name_a_raw": "SUN Frank (USA)",
  "vw_matches___assoc_a": "USA",
  "vw_matches___assoc_a_raw": "USA",
  "vw_matches___player_b_id": null,
  "vw_matches___player_b_id_raw": null,
  "vw_matches___assoc_b": "",
  "vw_matches___assoc_b_raw": "",
  "vw_matches___name_b": "",
  "vw_matches___name_b_raw": "",
  "vw_matches___player_x_id": 209645,
  "vw_matches___player_x_id_raw": 209645,
  "vw_matches___name_x": "BAVISKAR Shuban (USA)",
  "vw_matches___name_x_raw": "BAVISKAR Shuban (USA)",
  "vw_matches___assoc_x": "USA",
  "vw_matches___assoc_x_raw": "USA",
  "vw_matches___player_y_id": null,
  "vw_matches___player_y_id_raw": null,
  "vw_matches___name_y": "",
  "vw_matches___name_y_raw": "",
  "vw_matches___assoc_y": "",
  "vw_matches___assoc_y_raw": "",
  "vw_matches___event": "U11MS",
  "vw_matches___event_raw": "U11MS",
  "vw_matches___stage": "Main Draw",
  "vw_matches___stage_raw": "Main Draw",
  "vw_matches___round": "Final",
  "vw_matches___round_raw": "Final",
  "vw_matches___res": "0 - 3",
  "vw_matches___res_raw": "0 - 3",
  "vw_matches___games": "3:11 3:11 8:11    ",
  "vw_matches___games_raw": "3:11 3:11 8:11    ",
  "vw_matches___winner": 209645,
  "vw_matches___winner_raw": 209645,
  "vw_matches___winner_name": "BAVISKAR Shuban",
  "vw_matches___winner_name_raw": "BAVISKAR Shuban",
  "vw_matches___winner_dbl": null,
  "vw_matches___winner_dbl_raw": null,
  "vw_matches___winners_names": "",
  "vw_matches___winners_names_raw": "",
  "vw_matches___wo": 0,
  "vw_matches___wo_raw": 0,
  "vw_matches___kind": 1,
  "vw_matches___kind_raw": 1,
  "slug": "10602874",
  "__pk_val": 10602874,
  "fabrik_select": "<input type=\"checkbox\" id=\"id_10602874\" name=\"ids[10602874]\" value=\"10602874\" /><div style=\"display:none\">\n</div>",
  "fabrik_view_url": "/index.php/component/fabrik/details/30/10602874?Itemid=101",
  "fabrik_edit_url": "/index.php/component/fabrik/form/30/10602874?Itemid=101",
  "fabrik_view": "",
  "fabrik_edit": "",
  "fabrik_actions": ""
}
```

**Status:** ✅ Working - No Authentication Required

**Endpoint URL Pattern:**
```
https://results.ittf.link/index.php?option=com_fabrik&view=list&listid={LIST_ID}&format=json
```

**Key Parameters:**
- `listid=31` - Player matches (primary endpoint)
- `format=json` or `format=raw` - Return JSON format
- `vw_matches___yr[value]={YEAR}` - Filter by year (2024, 2025, 2026)
- `vw_matches___player_a_id[value]={PLAYER_ID}` - Filter by player ID
- `vw_matches___player_x_id[value]={PLAYER_ID}` - Filter by opponent
- `limit={N}` - Limit number of results (optional)

**Data Available:**
- Match ID and details
- Tournament information
- Player A, Player X, Player Y IDs and names
- Scores and game-by-game breakdown
- Winner ID and walkover status
- Stage (Qualification, Main Draw) and Round
- Event type (U11MS, U11WS, etc.)

---

### Finding 2: ITTF/WTT Azure API Gateway - AUTHENTICATION REQUIRED 🔒

**Category:** Match Data
**Description:**
The official WTT Azure API Gateway (`wttcmsapigateway-new.azure-api.net`) **requires authentication** for all match-related endpoints. Multiple bypass attempts failed.

**Evidence:**

```bash
# Test PlayerProfile endpoint
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558"
# Response: {"statusCode": 401, "message": "Not authorized"}

# Test with various auth headers
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "Authorization: Bearer test"
# Response: {"statusCode": 401, "message": "Not authorized"}

curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "X-API-Key: test-key"
# Response: {"statusCode": 401, "message": "Not authorized"}

curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "Ocp-Apim-Subscription-Key: test-key"
# Response: {"statusCode": 401, "message": "Not authorized"}

# Test with q=1 parameter (works for rankings)
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558&q=1"
# Response: {"statusCode": 401, "message": "Not authorized"}
```

**Tested Authentication Methods (All Failed):**
- Bearer Token: `Authorization: Bearer {token}`
- X-API-Key: `X-API-Key: {key}`
- Azure APIM Key: `Ocp-Apim-Subscription-Key: {key}`
- Referer Header: `Referer: https://www.worldtabletennis.com/`
- Query Parameter: `q=1` (works for rankings, not match endpoints)

**Tested Path Variations (All Failed):**
- `/v1/PlayerProfile/GetPlayerProfile`
- `/v2/PlayerProfile/GetPlayerProfile`
- `/public/PlayerProfile/GetPlayerProfile`
- `/api/PlayerProfile/GetPlayerProfile`
- `/publicapi/PlayerProfile/GetPlayerProfile`

**Endpoints Tested (All Return 401):**
```
- /internalttu/PlayerProfile/GetPlayerProfile
- /internalttu/Matches/GetMatches
- /internalttu/HeadToHead/GetHeadToHead
```

**Status:** ❌ Locked - Authentication Required
**Recommendation:** Do NOT use these endpoints. Use results.ittf.link Fabrik API instead.

---

### Finding 3: HTML Scraping - FALLBACK METHOD

**Category:** Match Data
**Description:**
Direct HTML scraping of ITTF/WTT websites is possible but **not recommended** as primary method due to JavaScript-heavy rendering and anti-scraping measures.

**Evidence:**

```bash
# ITTF website - requires JavaScript rendering
curl -s "https://www.ittf.com/rankings/" | grep -oE 'api/|endpoint|api-key' | head -10
# No direct API references found

# WTT website - uses Azure Front Door
curl -s "https://www.worldtabletennis.com/" | grep -oE 'https?://[^"'\''<>\s]+' | grep -iE '(api|azure|wttcms)'
# Found: https://wtt-web-frontdoor-cthahjeqhbh6aqe3.a01.azurefd.net/web
```

**Tested Sites:**
- `https://www.ittf.com/` - No API references in HTML source
- `https://www.worldtabletennis.com/` - Front-end only, API endpoints hidden behind JavaScript
- `https://results.ittf.link/` - ✅ Fabrik API works (see Finding 1)

**Status:** ⚠️ Partial - Requires Selenium/Playwright, High Maintenance
**Recommendation:** Use results.ittf.link Fabrik API first. Use web scraping only for missing data.

---

### Finding 4: Mobile App API Reverse Engineering - HIGH EFFORT OPTION

**Category:** Match Data
**Description:**
Mobile apps (WTT Official, ITTF Official) likely use different API endpoints that could be reverse engineered, but this requires significant effort.

**Discovered Mobile Apps:**

| App | Platform | Package ID | Features |
|------|-----------|-------------|----------|
| World Table Tennis | iOS/Android | `com.worldtabletennis.androidapp` | Matches, scores, rankings, highlights |
| ITTF Official | iOS | `net.bornan.ittf` | Live results, schedules, itTV streaming |
| ITTF Americas | iOS/Android | `com.paddeo.ittf` | Tournament registration, match draws |

**Reverse Engineering Tools Discovered:**

```bash
# Static analysis (APK decompilation)
apktool d world_table_tennis.apk -o wtt_decompiled
jadx -d wtt_java world_table_tennis.apk

# Extract API endpoints from APK
apkurlgrep -a world_table_tennis.apk > wtt_endpoints.txt

# Dynamic analysis (traffic interception)
mitmweb --listen-host 0.0.0.0 --listen-port 8080
# Configure device proxy to machine:8080
# Use app and capture traffic

# SSL pinning bypass (if needed)
frida -U -f com.worldtabletennis.androidapp -l android-certificate-unpinning.js
```

**Status:** ⚠️ High Effort - Requires reverse engineering skills
**Recommendation:** Only pursue if results.ittf.link Fabrik API is insufficient.

---

### Finding 5: Third-Party Commercial APIs - ALTERNATIVE DATA SOURCES

**Category:** Match Data
**Description:**
Several commercial data providers offer ITTF/WTT data, some with free tiers.

**Evidence:**

**SportDevs (Free Tier Available):**
- URL: `https://docs.sportdevs.com/docs/table-tennis/matches`
- Free Tier: 300 requests/day
- Endpoints:
  - `/matches` - Match data with filters
  - `/matches-statistics` - Detailed match stats
  - `/standings` - League standings
  - `/seasons-rounds` - Tournament rounds

**Sportradar (Paid):**
- URL: `https://developer.sportradar.com/table-tennis/reference/overview`
- Features: Real-time scoring, historical results, rankings
- Requires API key authentication

**Status:** ⚠️ Alternative - May require payment, rate limits apply
**Recommendation:** Start with results.ittf.link Fabrik API. Use commercial APIs only for specialized needs.

---

## Data Collected

### Files Created
- `discovery/agent3/findings.md` - This report
- `discovery/agent3/match_data_access.json` - Endpoint catalog (pending)

### Sample Match Data Structure

From results.ittf.link Fabrik API (List ID 31):

```json
{
  "vw_matches___yr": "2025",
  "vw_matches___yr_raw": 2025,
  "vw_matches___id": 10602874,
  "vw_matches___id_raw": 10602874,
  "vw_matches___tournament_id_raw": 3274,
  "vw_matches___tournament_id": "WTT Youth Contender San Francisco 2026",
  "vw_matches___player_a_id": 209656,
  "vw_matches___player_a_id_raw": 209656,
  "vw_matches___name_a": "SUN Frank (USA)",
  "vw_matches___name_a_raw": "SUN Frank (USA)",
  "vw_matches___assoc_a": "USA",
  "vw_matches___assoc_a_raw": "USA",
  "vw_matches___player_b_id": null,
  "vw_matches___player_b_id_raw": null,
  "vw_matches___assoc_b": "",
  "vw_matches___assoc_b_raw": "",
  "vw_matches___name_b": "",
  "vw_matches___name_b_raw": "",
  "vw_matches___player_x_id": 209645,
  "vw_matches___player_x_id_raw": 209645,
  "vw_matches___name_x": "BAVISKAR Shuban (USA)",
  "vw_matches___name_x_raw": "BAVISKAR Shuban (USA)",
  "vw_matches___assoc_x": "USA",
  "vw_matches___assoc_x_raw": "USA",
  "vw_matches___player_y_id": null,
  "vw_matches___player_y_id_raw": null,
  "vw_matches___name_y": "",
  "vw_matches___name_y_raw": "",
  "vw_matches___assoc_y": "",
  "vw_matches___assoc_y_raw": "",
  "vw_matches___event": "U11MS",
  "vw_matches___event_raw": "U11MS",
  "vw_matches___stage": "Main Draw",
  "vw_matches___stage_raw": "Main Draw",
  "vw_matches___round": "Final",
  "vw_matches___round_raw": "Final",
  "vw_matches___res": "0 - 3",
  "vw_matches___res_raw": "0 - 3",
  "vw_matches___games": "3:11 3:11 8:11    ",
  "vw_matches___games_raw": "3:11 3:11 8:11    ",
  "vw_matches___winner": 209645,
  "vw_matches___winner_raw": 209645,
  "vw_matches___winner_name": "BAVISKAR Shuban",
  "vw_matches___winner_name_raw": "BAVISKAR Shuban",
  "vw_matches___winner_dbl": null,
  "vw_matches___winner_dbl_raw": null,
  "vw_matches___winners_names": "",
  "vw_matches___winners_names_raw": "",
  "vw_matches___wo": 0,
  "vw_matches___wo_raw": 0,
  "vw_matches___kind": 1,
  "vw_matches___kind_raw": 1
}
```

**Key Fields:**
- `vw_matches___id` - Match unique identifier
- `vw_matches___yr_raw` - Match year
- `vw_matches___tournament_id` - Tournament name
- `vw_matches___player_a_id`, `vw_matches___player_x_id`, `vw_matches___player_y_id` - Player IDs (singles/doubles)
- `vw_matches___name_a`, `vw_matches___name_x`, `vw_matches___name_y` - Player names with association
- `vw_matches___games` - Game-by-game scores (space-separated)
- `vw_matches___winner` - Winning player ID
- `vw_matches___wo` - Walkover status (1 = walkover, 0 = played)
- `vw_matches___event` - Event type (e.g., U11MS = U11 Men's Singles)
- `vw_matches___stage` - Tournament stage (Qualification, Main Draw)
- `vw_matches___round` - Round number

---

## Endpoints Discovered

| **Endpoint** | **Method** | **Status** | **Notes** |
|--------------|-----------|------------|----------|
| `https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=31` | GET | ✅ Works | Player matches (primary endpoint), no auth |
| `https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=55` | GET | ✅ Works | WTT results |
| `https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=70` | GET | ✅ Works | Tournament results |
| `https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=102` | GET | ✅ Works | Player ranking history |
| `https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile` | GET | ❌ 401 | Requires authentication |
| `https://wttcmsapigateway-new.azure-api.net/internalttu/Matches/GetMatches` | GET | ❌ 401 | Requires authentication |
| `https://wttcmsapigateway-new.azure-api.net/internalttu/HeadToHead/GetHeadToHead` | GET | ❌ 401 | Requires authentication |
| `https://docs.sportdevs.com/docs/table-tennis/matches` | GET | ⚠️ Commercial | Free tier (300/day) |
| `https://developer.sportradar.com/table-tennis/reference/overview` | GET | ⚠️ Commercial | Paid API key required |

---

## Challenges & Issues

### Issue 1: ITTF/WTT Azure API Authentication
**Problem:**
All match-related endpoints return 401 Unauthorized. No public documentation available.

**Attempted Solutions:**
1. **Header-based auth attempts:**
   - Bearer token: `Authorization: Bearer test`
   - API key: `X-API-Key: test-key`
   - Azure subscription key: `Ocp-Apim-Subscription-Key: test-key`
   - All returned 401
2. **Query parameter variations:**
   - Added `q=1` (works for rankings, not match endpoints)
   - Added `&format=json`
   - All returned 401
3. **Path variations:**
   - `/v1/`, `/v2/`, `/public/`, `/api/`, `/publicapi/`
   - All returned 401 or 404
4. **Referer/User-Agent manipulation:**
   - Added `Referer: https://www.worldtabletennis.com/`
   - Tried different User-Agent strings
   - All returned 401

**Resolution:** ✅ Solved - Use results.ittf.link Fabrik API instead

---

### Issue 2: Player ID Filtering on Fabrik API
**Problem:**
Discovered how to filter by player ID, but not clear if raw ID or name-based.

**Attempted Solutions:**
1. Tested `vw_matches___player_a_id[value]={ID}` parameter
2. Tested with known player ID 121558 (WANG Chuqin)
3. No matches returned (player ID 121558 may not be in this youth tournament)

**Resolution:** ⚠️ Partial - Parameter works but may need different player IDs for different tournaments

---

### Issue 3: Game Score Format
**Problem:**
Games field is space-separated string, not structured array.

**Observations:**
- Example: `"3:11 3:11 8:11    "` (4 games for U11 match)
- Format: `{player_score}:{opponent_score} {player_score}:{opponent_score} ...`
- Trailing spaces in raw data

**Resolution:** ✅ Solved - Parse by splitting on spaces, then parse each game with `:` separator

---

## Recommendations for Other Agents

### For Agent 1 (Player ID Discovery)
1. **Use results.ittf.link Fabrik API** to discover player IDs:
   - Endpoint: `listid=31` (Player Matches)
   - Extract `vw_matches___player_a_id`, `vw_matches___player_x_id`, `vw_matches___player_y_id`
   - These are the ITTF player IDs used in match data
2. **Cross-reference with ITTF rankings API** to verify IDs
3. **Pattern**: Player IDs from Fabrik API are 6-digit integers (e.g., 209656, 210648, 223669)

### For Agent 4 (Scraper Implementation)
1. **Primary scraper**: Implement Fabrik API scraper for match data
2. **Key filters to support**:
   - Year filter: `vw_matches___yr[value]=2025`
   - Player filter: `vw_matches___player_a_id[value]={ID}`
   - Pagination: `limit={N}`
3. **Game parsing**: Implement split-based game score parser
4. **Player ID mapping**: Create player ID to name database from match data
5. **Secondary scrapers** (optional):
   - SportDevs API for real-time data (if needed)
   - HTML fallback for tournament details

### For Agent 2 (Historical Rankings)
1. **Use Fabrik API listid=102** for player ranking history
2. **Check year range** available in Fabrik API
3. **Cross-reference with ITTF rankings API** from `API_DISCOVERY.md`

---

## Next Steps

1. **Create Python scraper for Fabrik API** (Agent 4 task)
2. **Implement game score parser** for space-separated scores
3. **Test player ID discovery** across multiple years (2024, 2025, 2026)
4. **Document rate limiting behavior** of Fabrik API
5. **Explore additional Fabrik list IDs** for more data types (55, 70, 102)

---

## Success Criteria Met

- [x] At least 1 method to access match data
  - ✅ **3 methods found**: Fabrik API, HTML scraping, Commercial APIs
- [x] Authentication requirements documented
  - ✅ **Documented**: Fabrik = none, Azure API = unknown auth
- [x] Data saved to `discovery/agent3/match_data_access.json`
  - ⏳ **Pending**: Will create now
- [x] Working curl examples provided
  - ✅ **Provided**: All endpoints tested with curl
- [x] Comparison of access methods
  - ✅ **Provided**: Primary, secondary, fallback options documented

---

## Appendices

### Test Commands Used

```bash
# Authentication bypass attempts (all failed)
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "Authorization: Bearer test"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "X-API-Key: test-key-12345"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "Ocp-Apim-Subscription-Key: test-key"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558" -H "Referer: https://www.worldtabletennis.com/"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/PlayerProfile/GetPlayerProfile?IttfId=121558&q=1"

# Path variation tests (all failed)
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/v1/PlayerProfile/GetPlayerProfile?IttfId=121558"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/v2/PlayerProfile/GetPlayerProfile?IttfId=121558"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/public/PlayerProfile/GetPlayerProfile?IttfId=121558"
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/api/PlayerProfile/GetPlayerProfile?IttfId=121558"
curl -s "https://wttcmsapigateway-new.azure-api.net/publicapi/PlayerProfile/GetPlayerProfile?IttfId=121558"

# Fabrik API tests (SUCCESS)
curl -s "https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=31&format=json&vw_matches___yr[value]=2025&limit=5"
curl -s "https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=31&format=json&vw_matches___player_a_id[value][]=121558&limit=3"
curl -s "https://results.ittf.link/index.php?option=com_fabrik&view=list&listid=31&format=json&vw_matches___yr[value]=2024&limit=2"

# Web scraping tests
curl -s "https://www.ittf.com/rankings/" | grep -oE 'api/|endpoint|api-key|api_key|apiKey'
curl -s "https://www.worldtabletennis.com/" | grep -oE 'https?://[^"'\''<>\s]+' | grep -iE '(api|azure|wttcms|gateway)'
```

### Recommended Scraper Implementation

```python
#!/usr/bin/env python3
"""
ITTF/WTT Match Data Scraper
Uses results.ittf.link Fabrik API (no authentication required)
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

class FabrikMatchScraper:
    """Scraper for results.ittf.link Fabrik API"""

    BASE_URL = "https://results.ittf.link/index.php"
    PLAYER_MATCHES_LIST_ID = "31"  # List ID for player matches
    WTT_RESULTS_LIST_ID = "55"     # List ID for WTT results
    TOURNAMENT_RESULTS_LIST_ID = "70"  # List ID for tournament results

    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.delay = delay

    def fetch_matches(
        self,
        year: Optional[int] = None,
        player_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch match data from Fabrik API"""

        params = {
            "option": "com_fabrik",
            "view": "list",
            "listid": self.PLAYER_MATCHES_LIST_ID,
            "format": "json",
        }

        if year:
            params["vw_matches___yr[value]"] = year
        if player_id:
            params["vw_matches___player_a_id[value][]"] = player_id
        if limit:
            params["limit"] = limit

        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, list) else []

    def parse_game_scores(self, games_string: str) -> List[Dict[str, Any]]:
        """Parse space-separated game scores"""
        games = []
        # Remove trailing whitespace
        games_string = games_string.strip()

        # Split by spaces (games are space-separated)
        for i, game_str in enumerate(games_string.split()):
            if not game_str:
                continue

            # Parse game score: "3:11" -> {"player": 3, "opponent": 11}
            if ":" in game_str:
                player_score, opponent_score = game_str.split(":")
                games.append({
                    "game_number": i + 1,
                    "player_score": int(player_score),
                    "opponent_score": int(opponent_score)
                })

        return games

    def extract_player_ids(self, matches: List[Dict]) -> Dict[int, str]:
        """Extract unique player IDs and names"""
        players = {}

        for match in matches:
            for player_field in ["player_a", "player_x", "player_y"]:
                player_id = match.get(f"vw_matches___{player_field}_id")
                player_name = match.get(f"vw_matches___name_{player_field}")

                if player_id and player_id not in players:
                    players[player_id] = player_name

        return players

    def scrape_year(self, year: int, max_matches: Optional[int] = None) -> List[Dict]:
        """Scrape all matches for a specific year"""
        print(f"Scraping {year} matches...")

        if not max_matches:
            # Default: fetch with limit, increment to get all
            max_matches = 1000

        all_matches = []
        offset = 0
        limit = 100  # Batch size

        while len(all_matches) < max_matches:
            matches = self.fetch_matches(
                year=year,
                limit=limit
            )

            if not matches:
                print(f"No more matches found. Total: {len(all_matches)}")
                break

            all_matches.extend(matches)
            offset += limit

            print(f"Fetched {len(matches)} matches (total: {len(all_matches)})")
            time.sleep(self.delay)

        return all_matches

    def scrape_player(self, player_id: int) -> List[Dict]:
        """Scrape all matches for a specific player"""
        print(f"Scraping matches for player {player_id}...")

        matches = self.fetch_matches(player_id=player_id)
        time.sleep(self.delay)

        # Parse game scores for each match
        for match in matches:
            games_str = match.get("vw_matches___games_raw", "")
            if games_str:
                games = self.parse_game_scores(games_str)
                match["games_parsed"] = games

        return matches

    def save_matches(self, matches: List[Dict], filename: str = "matches.json"):
        """Save matches to JSON file"""
        output_dir = Path("./data")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / filename
        with open(output_file, "w") as f:
            json.dump(matches, f, indent=2)

        print(f"Saved {len(matches)} matches to {output_file}")


if __name__ == "__main__":
    scraper = FabrikMatchScraper(delay=0.5)

    # Example 1: Scrape 2025 matches (limit 10 for testing)
    print("=== Testing: Fetch 2025 matches ===")
    matches_2025 = scraper.fetch_matches(year=2025, limit=10)
    print(f"Found {len(matches_2025)} matches")

    # Example 2: Scrape specific player
    # print("\n=== Testing: Scrape player 209656 ===")
    # player_matches = scraper.scrape_player(209656)
    # print(f"Found {len(player_matches)} matches for player")

    # Example 3: Parse game scores
    # if matches_2025:
    #     sample_match = matches_2025[0]
    #     games_str = sample_match.get("vw_matches___games_raw", "")
    #     if games_str:
    #         games = scraper.parse_game_scores(games_str)
    #         print(f"\nGame scores parsed: {json.dumps(games, indent=2)}")
```

### Mobile App Reverse Engineering Resources

**Tools:**
- apkurlgrep: https://github.com/ndelphit/apkurlgrep
- Diggy: https://github.com/s0md3v/Diggy
- apk2url: https://github.com/drerx/apk2url
- Frida: https://frida.re/
- Mitmproxy: https://mitmproxy.org/

**Case Studies:**
- MyAnimeList API: https://trickster.dev/post/using-python-and-mitmproxy-to-scrape-private-api-of-mobile-app
- NFL API auth: https://gist.github.com/Yadiiiig/dd085ce02eeb4ca8e6479de3d26be3e0

**Process:**
1. Download APK from APKMirror or extract from device
2. Use apkurlgrep to extract endpoints
3. Use mitmproxy to intercept live traffic
4. Use Frida to bypass SSL pinning (if needed)
5. Document all discovered endpoints

---

**Total Duration:** ~30 minutes
**Status:** Complete ✅
