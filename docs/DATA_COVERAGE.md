# TTBL Scraper - Data Coverage & Freshness

## Data Freshness

### Real-Time Capabilities

**The scraper can provide up-to-date results AS SOON as a match ends.**

#### How It Works

1. **Live API Access**: The scraper fetches data directly from TTBL's live API:
   ```
   GET https://www.ttbl.de/api/internal/match/{matchId}
   ```

2. **No Caching**: The scraper does not cache data on its side. Every run fetches fresh data from TTBL's servers.

3. **Match States**: Matches have a `matchState` field:
   - `"Finished"` - Match completed, final results available
   - `"Live"` - Match in progress (live scoring)
   - `"Inactive"` - Scheduled, not yet started
   - `"Cancelled"` - Match cancelled

4. **Immediate Availability**: As soon as TTBL updates a match's state to "Finished", the scraper can fetch the complete results.

#### Real-Time Evidence

The API provides live scoring data with timestamps:

```json
{
  "matchState": "Finished",
  "timeStamp": 1756558800,
  "updateCount": 483,
  "scoringUpdates": [
    {
      "type": "Point",
      "ts": 1756558865712,
      "result": "1:0",
      "playerId": "cb02ef42-dd1b-4be5-826b-4f12b07fbc3d"
    },
    // ... hundreds of more updates with millisecond timestamps
  ]
}
```

- `updateCount: 483` - This match received 483 scoring updates (live point-by-point tracking)
- `scoringUpdates` array - Contains every point, set, timeout, and event with millisecond precision

#### Recommended Usage Pattern

For up-to-date results:

```bash
# Run scraper to get latest data
python3 scrape_ttbl_enhanced.py

# Check which matches are newly finished
jq '[.[] | select(.matchState == "Finished")] | length' ttbl_data/stats/match_states.json
```

#### Limitations

- **No Push Notifications**: Scraper is polling-based, not event-driven. You must run it to check for updates.
- **No Incremental Scraping**: Currently scrapes entire season (can take 4-5 minutes). Future enhancement: only fetch newly finished matches.
- **Rate Limiting**: 1-second delay between requests to respect TTBL servers.

#### Season Support

The scraper can access:
- **Current Season**: Live data as matches are played
- **Past Seasons**: Historical data available via schedule pages
- **Future Seasons**: Once the season starts and schedule is published

**Current Configuration** (see `scrape_ttbl_enhanced.py`):
```python
SEASON = "2024-2025"  # Season to scrape
NUM_GAMEDAYS = 24      # Maximum gamedays to try (script will skip non-existent gamedays)
```

**Tip**: Set `NUM_GAMEDAYS` to a high number (e.g., 30 or 50) to collect as many gamedays as possible. The script will automatically skip any gamedays that don't exist and report which ones were skipped.

---

## Data Available

### Complete Data Coverage

The scraper extracts **comprehensive data** from TTBL's API. Here's everything available:

#### 1. Match-Level Data ✅

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | UUID | Unique match identifier | `"02a8d29b-893c-48ab-8cb5-b642c8d03203"` |
| `matchState` | String | Match status | `"Finished"`, `"Live"`, `"Inactive"` |
| `timeStamp` | Integer | Unix timestamp (seconds) | `1756558800` |
| `updateCount` | Integer | Number of scoring updates | `483` |
| `spectators` | Integer | Live attendance | `310` |
| `homeGames` | Integer | Games won by home team | `3` |
| `awayGames` | Integer | Games won by away team | `2` |
| `homeSets` | Integer | Total sets won by home | `12` |
| `awaySets` | Integer | Total sets won by away | `9` |
| `homeBalls` | Integer | Total points scored by home | `216` |
| `awayBalls` | Integer | Total points scored by away | `193` |
| `livestreamUrl` | String | Live stream link | `"https://www.dyn.sport/..."` |
| `ticketshopUrl` | String | Ticket purchase link | `"https://www.ttbl.de/tickets"` |

#### 2. Team Data ✅

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | UUID | Unique team ID | `"ea835161-88aa-437b-9083-c19e057c0568"` |
| `seasonTeamId` | UUID | Season-specific team ID | `"28793fc1-58eb-4320-9516-188a8d3320c4"` |
| `name` | String | Team name | `"SV Werder Bremen"` |
| `rank` | Integer | League standing | `1` |
| `plusPoints` | Integer | Plus/minus points | `18` |
| `gameWins` | Integer | Total games won in season | `28` |
| `setWins` | Integer | Total sets won in season | `95` |
| `logoPngUrl` | String | Team logo URL | `"/uploads/team/..."` |

#### 3. Player Data ✅

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | UUID | Unique player ID | `"cb02ef42-dd1b-4be5-826b-4f12b07fbc3d"` |
| `firstName` | String | First name | `"Kirill"` |
| `lastName` | String | Last name | `"Gerassimenko"` |
| `imageUrl` | String | Player photo URL | `"/uploads/player/..."` |

**Available for:**
- `homePlayerOne`, `homePlayerTwo`, `homePlayerThree` (starting lineup)
- `guestPlayerOne`, `guestPlayerTwo`, `guestPlayerThree` (starting lineup)
- `homeSubstitutePlayerOne/Two/Three` (substitutes)
- `guestSubstitutePlayerOne/Two/Three` (substitutes)

#### 4. Game-Level Data ✅

Each match has 5 games (singles matches), each with:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `index` | Integer | Game number (1-5) | `1` |
| `gameState` | String | Game status | `"Finished"` |
| `winnerSide` | String | Winner: "Home" or "Away" | `"Away"` |
| `homeSets` | Integer | Sets won by home player | `1` |
| `awaySets` | Integer | Sets won by away player | `3` |
| `set1HomeScore` | Integer | Set 1 home score | `11` |
| `set1AwayScore` | Integer | Set 1 away score | `8` |
| `set2HomeScore` | Integer | Set 2 home score | `14` |
| `set2AwayScore` | Integer | Set 2 away score | `16` |
| `set3HomeScore` | Integer | Set 3 home score | `7` |
| `set3AwayScore` | Integer | Set 3 away score | `11` |
| `set4HomeScore` | Integer | Set 4 home score | `5` |
| `set4AwayScore` | Integer | Set 4 away score | `11` |
| `set5HomeScore` | Integer | Set 5 home score (null if not played) | `null` |
| `set5AwayScore` | Integer | Set 5 away score (null if not played) | `null` |

#### 5. Advanced Game Statistics ✅

Per-game advanced stats (available for finished games):

| Field | Type | Description |
|-------|------|-------------|
| `homePointsOnServe` | Integer | Home player points on serve |
| `awayPointsOnServe` | Integer | Away player points on serve |
| `homePointsOnReturn` | Integer | Home player points on return |
| `awayPointsOnReturn` | Integer | Away player points on return |
| `homeHighestLead` | Integer | Home player's highest lead |
| `awayHighestLead` | Integer | Away player's highest lead |
| `homePointsInARow` | Integer | Home player's longest streak |
| `awayPointsInARow` | Integer | Away player's longest streak |
| `homeLuckyPoints` | Integer | Lucky shots (net rollers, edge balls) |
| `awayLuckyPoints` | Integer | Lucky shots (net rollers, edge balls) |
| `homeMatchPoints` | Integer | Match points (set points) saved |
| `awayMatchPoints` | Integer | Match points (set points) saved |
| `homeTimeoutUsed` | Boolean | Did home player use timeout |
| `awayTimeoutUsed` | Boolean | Did away player use timeout |

#### 6. Point-by-Point Scoring ✅

**Complete play-by-play data** for every game:

```json
{
  "type": "Point",
  "ts": 1756558865712,
  "playerId": "cb02ef42-dd1b-4be5-826b-4f12b07fbc3d",
  "set": 1,
  "result": "1:0",
  "bwRating": 0,
  "isAcePoint": false,
  "isServerErrorPoint": true,
  "isLuckyShot": false,
  "isNetRoller": false,
  "isEdgeBall": false
}
```

**Event Types:**
- `Create` - Game created
- `EventGameStart` - First point about to be served
- `EventSetStart` - New set beginning
- `Point` - Score update
- `EventSetEnd` - Set finished
- `EventGameEnd` - Game finished
- `EventTimeoutStart` - Timeout called

**Point Attributes:**
- `bwRating` - "Beauty & Willingness" rating (0-3)
- `isAcePoint` - Ace serve
- `isServerErrorPoint` - Unforced error
- `isLuckyShot` - Lucky point
- `isNetRoller` - Ball hits net and goes over
- `isEdgeBall` - Ball hits table edge

#### 7. Venue Data ✅

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | String | Venue name | `"Klaus-Dieter-Fischer-Halle"` |
| `adress` | String | Street address | `"Hermine-Berthold-Straße 19/20"` |
| `zipCode` | String | Postal code | `"28205"` |
| `place` | String | City | `"Bremen"` |
| `imageUrl` | String | Venue image URL | `"/uploads/venue/..."` |

#### 8. Gameday Information ✅

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | String | Gameday name | `"1. Spieltag (2025/2026)"` |

---

## Data Still Needed (Not Available via API)

### Missing Data ⚠️

The following data is **NOT available** through TTBL's public API:

#### 1. Historical Standings ❌

**Status**: Not available in match data

**What's Missing:**
- Team standings at specific points in season
- Points tables after each gameday
- Head-to-head team records

**Workaround**:
- Could calculate from match results (needs aggregation logic)
- Or scrape from TTBL's standings pages (if available)

#### 2. Player Demographics ❌

**Status**: Partially available

**What's Missing:**
- Player birthdate/age
- Player nationality
- Player height/weight
- Player ranking history
- Player career statistics

**Available**:
- Player ID, name, photo URL
- Games played, wins, losses, win rate (calculated)

#### 3. Team Composition History ❌

**Status**: Not available

**What's Missing:**
- Team roster changes over time
- Transfer history
- Contract information

#### 4. Match Officials ❌

**Status**: Not available

**What's Missing:**
- Referee names
- Umpire assignments

#### 5. Coaching Data ❌

**Status**: Not available

**What's Missing:**
- Head coach names
- Timeout usage by coaches

#### 6. Attendance History ❌

**Status**: Current match only

**What's Missing:**
- Historical attendance trends
- Season average attendance

**Available**:
- `spectators` field for current match (if live)

#### 7. Weather/Conditions ❌

**Status**: Not available (indoor sport)

#### 8. Video Highlights ❌

**Status**: Links available, but content not scraped

**Available**:
- `livestreamUrl` (external link)
- `followupReport` (if available)

**Not Available**:
- Video content
- Highlight clips

#### 9. Team Financial Data ❌

**Status**: Not available

**What's Missing:**
- Team budget
- Player salaries
- Sponsorship information

#### 10. Advanced Analytics (Calculated) ❌

**Status**: Not available directly, can be calculated

**What's Missing** (but can be derived):
- Player ELO ratings
- Team ELO ratings
- Form trends (last 5 games)
- Home/away performance split
- Head-to-head player records
- Momentum indicators

---

## Data Quality & Completeness

### Quality Metrics

Based on scraped data (2025-2026 season backup):

| Metric | Value |
|--------|-------|
| Total matches scheduled | 108 |
| Matches with complete data | 66 (61%) |
| Matches scheduled (future) | 42 (39%) |
| Unique players | 63 |
| Players with game data | 61 |
| Total games processed | 330 |

### Data Quality Notes

✅ **Good Quality:**
- All finished matches have complete data
- Player IDs are consistent across matches
- Timestamps are accurate
- Point-by-point data is complete for finished games

⚠️ **Known Issues:**
- Scheduled matches have `null` for players (lineups not announced)
- Some matches may have "Unknown" player names (data entry issues)
- Rare edge cases: null `winnerSide` despite "Finished" status

### Recommended Filters for Production

```python
valid_games = [
    game for game in games_data
    if game["gameState"] == "Finished"
    and game.get("winnerSide") is not None
    and game.get("homePlayer", {}).get("name") != "Unknown"
    and game.get("awayPlayer", {}).get("name") != "Unknown"
]
```

---

## API Reference

### Primary Endpoints

#### Match Data
```
GET https://www.ttbl.de/api/internal/match/{matchId}
```
**Authentication**: None required
**Rate Limit**: Be respectful (use 1s delay)
**Returns**: Full match JSON with all fields listed above

#### Schedule Discovery
```
GET https://www.ttbl.de/bundesliga/gameschedule/{season}/{gameday}/all
```
**Returns**: HTML page with match IDs embedded
**Usage**: Parse match IDs to feed into match endpoint

### Season Format

- Current season: `"2025-2026"`
- Past season: `"2024-2025"`
- Future seasons: Once schedule is published

---

## Conclusion

### What This Means for Your Use Case

**For building an ELO rating system:**
✅ **All required data is available**
- Player identification (ID + name)
- Win/loss outcomes
- Game timestamps (for chronological processing)
- Point-by-point scoring (for advanced metrics)

**For live applications:**
✅ **Real-time data available**
- Match state updates
- Live scoring with millisecond precision
- Immediate availability of finished results

**For historical analysis:**
✅ **Complete season data available**
- All matches (past, current, future when available)
- Full game-level detail
- Venue and attendance data

**For advanced analytics:**
⚠️ **Some data missing, but can be calculated**
- ELO ratings (calculate from wins/losses)
- Form trends (calculate from recent results)
- Head-to-head records (calculate from match history)

### Summary

| Category | Status |
|----------|--------|
| Basic match data | ✅ Complete |
| Player statistics | ✅ Complete |
| Point-by-point scoring | ✅ Complete |
| Real-time updates | ✅ Complete |
| Team standings | ❌ Not available |
| Player demographics | ⚠️ Partial |
| Team history | ❌ Not available |
| Advanced analytics | ✅ Can calculate |

---

**Last Updated**: January 9, 2026
**Version**: 1.0
