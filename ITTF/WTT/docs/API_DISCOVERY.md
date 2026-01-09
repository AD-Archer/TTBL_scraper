# ITTF/WTT API Discovery Report

**Date:** January 9, 2026
**Status:** Initial Discovery Phase

## Executive Summary

We discovered a working ITTF/WTT API endpoint for retrieving player rankings. This is the first step in building a comprehensive data scraping solution for ITTF/WTT matches, historical data, and player statistics.

## Working Endpoint

### GET Player Rankings

**Endpoint:**
```
https://wttcmsapigateway-new.azure-api.net/internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals
```

**Required Parameters:**
- `IttfId` (string/integer): Player ITTF ID
- `q=1` (integer): Query parameter (must be `1`)

**Example Request:**
```bash
curl -s "https://wttcmsapigateway-new.azure-api.net/internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals?IttfId=121558&q=1"
```

**Example Response:**
```json
{
  "Version": "0.1.0",
  "Source": "ITTF/WTT",
  "System": "Table tennis Sports Data API",
  "StatusCode": 200,
  "RequestId": "9fb96b24-e256-415b-80c4-d90b87a57a41",
  "ResponseDate": "01/09/2026",
  "ResponseTime": "21:35:17",
  "Result": [
    {
      "IttfId": "121558",
      "PlayerName": "WANG Chuqin",
      "CountryCode": "CHN",
      "CountryName": "China",
      "AssociationCountryCode": "CHN",
      "AssociationCountryName": "China",
      "CategoryCode": "SEN",
      "AgeCategoryCode": "SEN",
      "SubEventCode": "MDI",
      "RankingYear": "2026",
      "RankingMonth": "1",
      "RankingWeek": "2",
      "RankingPointsCareer": null,
      "RankingPointsYTD": "4700",
      "RankingPosition": "1",
      "CurrentRank": "3",
      "PreviousRank": "3",
      "RankingDifference": "0",
      "PublishDate": "01/05/2026 00:00:00"
    },
    {
      "IttfId": "121558",
      "PlayerName": "WANG Chuqin",
      "CountryCode": "CHN",
      "CountryName": "China",
      "AssociationCountryCode": "CHN",
      "AssociationCountryName": "China",
      "CategoryCode": "SEN",
      "AgeCategoryCode": "SEN",
      "SubEventCode": "MS",
      "RankingYear": "2026",
      "RankingMonth": "1",
      "RankingWeek": "2",
      "RankingPointsCareer": null,
      "RankingPointsYTD": "9925",
      "RankingPosition": "1",
      "CurrentRank": "1",
      "PreviousRank": "1",
      "RankingDifference": "0",
      "PublishDate": "01/05/2026 00:00:00"
    },
    {
      "IttfId": "121558",
      "PlayerName": "WANG Chuqin",
      "CountryCode": "CHN",
      "CountryName": "China",
      "AssociationCountryCode": "CHN",
      "AssociationCountryName": "China",
      "CategoryCode": "SEN",
      "AgeCategoryCode": "SEN",
      "SubEventCode": "XDI",
      "RankingYear": "2026",
      "RankingMonth": "1",
      "RankingWeek": "2",
      "RankingPointsCareer": null,
      "RankingPointsYTD": "5561",
      "RankingPosition": "1",
      "CurrentRank": "5",
      "PreviousRank": "5",
      "RankingDifference": "0",
      "PublishDate": "01/05/2026 00:00:00"
    }
  ]
}
```

## SubEvent Codes

The API returns multiple entries per player, one for each event category:

| **Code** | **Event Type** | **Description** |
|----------|---------------|-----------------|
| MS | Men's Singles | Individual men's ranking |
| WS | Women's Singles | Individual women's ranking |
| MDI | Men's Doubles International | Doubles ranking |
| WDI | Women's Doubles International | Doubles ranking |
| XD | Mixed Doubles International | Mixed doubles ranking |
| XDI | Mixed Doubles International | Alternative mixed doubles code |

## Authenticated Endpoints (Not Accessible)

The following endpoints exist but return 401 Unauthorized:

| **Endpoint** | **Purpose** | **Status** |
|--------------|-------------|-------------|
| `/PlayerProfile/GetPlayerProfile` | Player profile data | 🔒 Requires auth |
| `/Matches/GetMatches` | Player match history | 🔒 Requires auth |
| `/HeadToHead/GetHeadToHead` | Head-to-head stats | 🔒 Requires auth |
| `/GetRankingTeams` | Team rankings | 🔒 Requires auth |

## Known Player ITTF IDs

These IDs were discovered during testing:

| **IttfId** | **Player Name** | **Country** |
|------------|-----------------|-------------|
| 121558 | WANG Chuqin | China (CHN) |
| 112001 | FAN Zhendong | China (CHN) [unconfirmed] |
| 101919 | FAN Zhendong | China (CHN) [unconfirmed] |
| 105649 | MA Long | China (CHN) [unconfirmed] |
| 119580 | SUN Yingsha | China (CHN) [unconfirmed] |

## API Behavior

### Successful Request
- **HTTP Status:** 200
- **Response Format:** JSON
- **Result Field:** Array of ranking entries (one per event category)

### Failed Requests
- **Invalid IttfId:** Returns `{"Result": null}`
- **Missing `q` parameter:** Returns 401 Unauthorized
- **`q=0` or `q=2`:** Returns empty result
- **Root `/internalttu/`:** Returns 401 Unauthorized

### Rate Limiting
- No rate limiting observed during testing
- Standard HTTP/HTTPS client should work
- No authentication required for ranking endpoint

## Unknowns & Next Steps

### Critical Unknowns
1. **Player Discovery:** How to find all valid `IttfId` values?
2. **Historical Data:** How to access rankings from previous weeks/months/years?
3. **Match Data:** How to get match results, scores, and game-by-game data?
4. **Authentication:** Can we obtain API keys for authenticated endpoints?

### Potential Discovery Paths
1. **results.ittf.link Analysis** - Site may contain player ID references
2. **ITTF Website Scraping** - Player profiles may contain ITTF IDs
3. **WTT Website Scraping** - Match pages may link to API
4. **API Enumeration** - Try different URL patterns and parameters
5. **Reverse Engineering** - Inspect network traffic from ITTF/WTT websites

## Data Model

### Ranking Entry
```typescript
interface RankingEntry {
  IttfId: string;
  PlayerName: string;
  CountryCode: string;
  CountryName: string;
  AssociationCountryCode: string;
  AssociationCountryName: string;
  CategoryCode: string;      // SEN = Senior, JUN = Junior, etc.
  AgeCategoryCode: string;
  SubEventCode: string;      // MS, WS, MDI, etc.
  RankingYear: string;
  RankingMonth: string;
  RankingWeek: string;
  RankingPointsCareer: string | null;
  RankingPointsYTD: string;
  RankingPosition: string;
  CurrentRank: string;
  PreviousRank: string;
  RankingDifference: string;
  PublishDate: string;
}
```

## Tools & Libraries

### Recommended Python Setup
```python
import requests
import json
from typing import List, Dict, Any

def get_player_rankings(ittf_id: str) -> List[Dict]:
    url = "https://wttcmsapigateway-new.azure-api.net/internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
    params = {
        "IttfId": ittf_id,
        "q": 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("Result", [])
```

## Project Structure

```
ITTF/WTT/
├── docs/
│   ├── API_DISCOVERY.md           # This file
│   ├── NEXT_STEPS.md             # Agent task assignments
│   ├── PLAYER_DISCOVERY.md        # Player ID discovery strategies
│   └── DATA_MODEL.md             # Complete data schema
├── scrapers/
│   ├── rankings_scraper.py       # Rankings data scraper
│   ├── matches_scraper.py        # Match data scraper (TBD)
│   └── players_scraper.py       # Player profile scraper (TBD)
├── data/
│   ├── rankings/                 # Ranking data by week/month
│   ├── players/                 # Player profiles
│   └── matches/                 # Match results
└── logs/
    └── scrape_log.txt            # Scraping logs
```

## References

- **Old ITTF API:** http://api.ittf.com (DEAD - domain doesn't exist)
- **Old Documentation:** https://arcnovus.github.io/ittf-api/ (Outdated - 2014)
- **TTBL Scraper:** ../TTBL/ (Separate project - German league)
- **results.ittf.link:** https://results.ittf.link (Joomla-based site, API locked)

---

**Last Updated:** January 9, 2026
**Version:** 1.0
