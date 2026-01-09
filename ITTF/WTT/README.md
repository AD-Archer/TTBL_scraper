# ITTF/WTT Data Collection - Agent Coordination

**Last Updated:** January 9, 2026

## Quick Start for Agents

1. Read **`API_DISCOVERY.md`** - Current knowledge about ITTF/WTT API
2. Read **`NEXT_STEPS.md`** - Your specific task and priorities
3. Work in your designated **`research/agents/agentX/`** folder
4. Report findings using **`AGENT_FINDINGS_TEMPLATE.md`**

---

## Quick Start (Single Script)

If you just want to scrape as much *public* match + player data as possible (no rankings), run:

```bash
python3 ITTF/WTT/scripts/master_scrape.py --years 2025,2024,2023
```

Outputs go to `ITTF/WTT/artifacts/data/master/` (gitignored).

---

## Folder Structure (No Conflicts!)

```
ITTF/WTT/
│   ├── API_DISCOVERY.md              # ✅ READ THIS FIRST - Current API knowledge
│   ├── NEXT_STEPS.md                # ✅ READ THIS SECOND - All agent tasks
│   └── AGENT_FINDINGS_TEMPLATE.md   # ✅ Template for your findings
├── research/                        # 📁 Research notes and agent findings
│   └── agents/                      # 📁 All agents save findings here
│       ├── agent1/                  # 📁 Agent 1 ONLY - Player ID discovery
│   │   ├── player_ids.json         # Your collected data
│   │   └── [any files you create]   # No one else touches this folder
│   │
│       ├── agent2/                  # 📁 Agent 2 ONLY - Historical rankings
│   │   ├── findings.md
│   │   ├── historical_endpoints.json
│   │   └── [any files you create]
│   │
│       ├── agent3/                  # 📁 Agent 3 ONLY - Match data access
│   │   ├── findings.md
│   │   ├── match_data_access.json
│   │   └── [any files you create]
│   │
│       └── agent4/                  # 📁 Agent 4 ONLY - Implementation notes
│           ├── findings.md
│           └── [any files you create]
│
├── scripts/                         # 📁 Runnable scrapers/tools
└── artifacts/                       # 📁 Generated outputs (gitignored)
    ├── data/
    └── logs/
```

## Agent Responsibilities

### Agent 1: Player ID Discovery
**Goal:** Find as many valid `IttfId` values as possible

**Work Folder:** `research/agents/agent1/`
**Output Files:**
- `findings.md` - Your report (use template)
- `player_ids.json` - List of all discovered IDs

**Read:** `NEXT_STEPS.md` → Section: Agent 1

**Sources to investigate:**
1. results.ittf.link (scrape for IttfId)
2. ITTF website (rankings, player pages)
3. WTT website (player profiles)
4. API brute force (test IttfId ranges 110000-130000)
5. Tournament/match references

---

### Agent 2: Historical Rankings
**Goal:** Find how to access rankings from previous weeks/months/years

**Work Folder:** `research/agents/agent2/`
**Output Files:**
- `findings.md` - Your report (use template)
- `historical_endpoints.json` - Discovered endpoints

**Read:** `NEXT_STEPS.md` → Section: Agent 2

**Strategies to test:**
1. URL parameter variations (e.g., `/RankingsPreviousWeek/`)
2. Date parameters (`?year=2024&month=12`)
3. Archive endpoints
4. results.ittf.link historical data

---

### Agent 3: Match Data
**Goal:** Find how to access match results, scores, game data

**Work Folder:** `research/agents/agent3/`
**Output Files:**
- `findings.md` - Your report (use template)
- `match_data_access.json` - Discovered endpoints/methods

**Read:** `NEXT_STEPS.md` → Section: Agent 3

**Strategies to test:**
1. Authentication bypass (API keys, headers)
2. API version variations (`/v1/`, `/v2/`)
3. Website reverse engineering (network traffic)
4. Mobile app API discovery
5. Third-party aggregators

**Target endpoints (currently 401):**
- `/PlayerProfile/GetPlayerProfile`
- `/Matches/GetMatches`
- `/HeadToHead/GetHeadToHead`

---

### Agent 4: Scraper Implementation
**Goal:** Build Python scrapers for all discovered data sources

**Work Folder:** `research/agents/agent4/`
**Output Files:**
- `findings.md` - Your report (use template)
- Your runnable scripts go in `scripts/`

**Read:** `NEXT_STEPS.md` → Section: Agent 4

**Can Start Immediately:**
- Rankings scraper (we have working endpoint!)

**Wait For:**
- Agent 1 results → Player ID scraper
- Agent 2 results → Historical rankings scraper
- Agent 3 results → Match scraper

---

## Working in Parallel

### What Can Be Done Simultaneously?
✅ **Yes, work in parallel:**
- Agent 1, 2, 3: All discovery tasks (independent)
- Agent 4: Rankings scraper (no dependencies)

⏸️ **Wait for results:**
- Agent 4 other scrapers: Wait for respective discovery agents

### Communication Between Agents

**No Direct Coordination Needed:**
- Each agent works in their own folder
- No shared files to modify
- No dependencies for initial discovery

**Data Flow:**
```
Agent 1 discovers → Saves to research/agents/agent1/player_ids.json
         ↓
Agent 4 reads → Builds player ID scraper
         ↓
Agent 2 discovers → Saves to research/agents/agent2/historical_endpoints.json
         ↓
Agent 4 reads → Builds historical scraper
         ↓
Agent 3 discovers → Saves to research/agents/agent3/match_data_access.json
         ↓
Agent 4 reads → Builds match scraper
```

### Checking Other Agents' Progress

```bash
# See what Agent 1 has found
cat research/agents/agent1/findings.md | head -50

# Check Agent 2's endpoints
cat research/agents/agent2/historical_endpoints.json | jq '.'

# Verify Agent 3 hasn't finished yet
ls research/agents/agent3/match_data_access.json
# If file exists, Agent 3 is done (or partially done)
```

---

## Reporting Your Findings

### Step 1: Copy Template
```bash
cp docs/AGENT_FINDINGS_TEMPLATE.md research/agents/agentX/findings.md
```

### Step 2: Fill in Template
- Edit `research/agents/agentX/findings.md`
- Replace bracketed placeholders
- Add your actual findings
- Include code examples and JSON samples

### Step 3: Save Data Files
- Player IDs → `research/agents/agent1/player_ids.json`
- Endpoints → `research/agents/agent2/historical_endpoints.json`
- Access methods → `research/agents/agent3/match_data_access.json`
- Scrapers/tools → `scripts/*.py`

### Step 4: Update Status
At the top of your `findings.md`:
```markdown
**Status:** [In Progress / Complete / Blocked]
**Progress:** [e.g., 40% - Found 342 player IDs]
```

---

## Example: Agent 4 Starting Rankings Scraper

Since Agent 4 has no dependencies for the rankings scraper, they can start immediately:

```python
# File: scripts/rankings_scraper.py

import requests
import json
from pathlib import Path

BASE_URL = "https://wttcmsapigateway-new.azure-api.net/internalttu"
RANKINGS_ENDPOINT = f"{BASE_URL}/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"

class RankingsScraper:
    def get_player_rankings(self, ittf_id: str):
        params = {"IttfId": ittf_id, "q": 1}
        response = requests.get(RANKINGS_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("Result", [])

if __name__ == "__main__":
    scraper = RankingsScraper()
    # Test with known player
    rankings = scraper.get_player_rankings("121558")
    print(json.dumps(rankings, indent=2))
```

Run it:
```bash
cd scripts
python3 rankings_scraper.py
```

---

## Success Criteria

### Agent 1 (Player IDs)
- ✅ 100+ unique IttfId values
- ✅ At least 2 discovery methods
- ✅ Data saved to `research/agents/agent1/player_ids.json`

### Agent 2 (Historical Rankings)
- ✅ At least 1 working historical endpoint
- ✅ Earliest date accessible documented
- ✅ Data saved to `research/agents/agent2/historical_endpoints.json`

### Agent 3 (Match Data)
- ✅ At least 1 method to access match data
- ✅ Authentication requirements documented
- ✅ Data saved to `research/agents/agent3/match_data_access.json`

### Agent 4 (Scrapers)
- ✅ Rankings scraper working
- ✅ Code in `scripts/`
- ✅ Documentation in `research/agents/agent4/findings.md`

---

## Troubleshooting

### Agent 1: No player IDs found
- Try API brute force on range 110000-130000
- Check if websites changed structure
- Try different search patterns

### Agent 2: All historical endpoints 401
- Document which patterns failed
- Check if date format matters (YYYY-MM-DD vs YYYYMMDD)
- Look for "archive" or "history" sections on websites

### Agent 3: All match endpoints locked
- Try website reverse engineering (Chrome DevTools)
- Check if mobile apps exist and have public APIs
- Consider web scraping as fallback

### Agent 4: Scraper fails
- Check network connectivity
- Verify endpoint is still working
- Check if API requires `q=1` parameter (it does!)

---

## Timeline

| **Time** | **Agent 1** | **Agent 2** | **Agent 3** | **Agent 4** |
|----------|--------------|--------------|--------------|--------------|
| Hour 0-2 | results.ittf.link scrape | URL variations testing | Auth bypass attempts | Rankings scraper |
| Hour 2-4 | ITTF website scrape | Parameter testing | Version variations | Wait for discoveries |
| Hour 4-6 | API brute force | Archive endpoints | Reverse engineering | Implement other scrapers |
| Hour 6-8 | Compile findings | Compile findings | Compile findings | All scrapers ready |

---

## Important Reminders

✅ **DO:**
- Work in your assigned folder only
- Save all data to JSON files
- Use the findings template for reports
- Test hypotheses systematically
- Document everything (successes AND failures)

❌ **DO NOT:**
- Work in other agents' folders
- Modify shared files unless assigned
- Assume endpoints work - test everything
- Skip documentation
- Ignore rate limiting (add delays!)

---

**Ready to start?**
1. Open `docs/NEXT_STEPS.md`
2. Find your agent section
3. Work in your `research/agents/agentX/` folder
4. Report findings when done

**Questions?**
- Check `docs/API_DISCOVERY.md` for current knowledge
- Check `docs/NEXT_STEPS.md` for your specific tasks
- Look at other agents' findings in `research/agents/agentX/findings.md`

---

**Last Updated:** January 9, 2026
**Status:** Ready for Agent Deployment ✅
