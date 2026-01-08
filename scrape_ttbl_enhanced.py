#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import os
import re
from datetime import datetime
from pathlib import Path
import time
from typing import Dict, List, Any
from collections import Counter

BASE_URL = "https://www.ttbl.de"
API_ENDPOINT = f"{BASE_URL}/api/internal/match"
OUTPUT_DIR = Path("./ttbl_data")
SEASON = "2025-2026"
NUM_GAMEDAYS = 18
DELAY = 1


def fetch_url(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "matches").mkdir(exist_ok=True)
(OUTPUT_DIR / "players").mkdir(exist_ok=True)
(OUTPUT_DIR / "stats").mkdir(exist_ok=True)

print("=" * 50)
print("TTBL Enhanced Scraper")
print(f"Season: {SEASON}")
print("=" * 50)
print()

all_match_ids = []
for gameday in range(1, NUM_GAMEDAYS + 1):
    print(f"  Gameday {gameday}/{NUM_GAMEDAYS}...", end="\r")

    schedule_url = f"{BASE_URL}/bundesliga/gameschedule/{SEASON}/{gameday}/all"
    html = fetch_url(schedule_url)

    match_ids = re.findall(r'/bundesliga/gameday/[^"]+', html)
    match_ids = [re.findall(r"[a-f0-9-]{36}$", mid) for mid in match_ids]
    match_ids = [mid[0] for mid in match_ids if mid]

    all_match_ids.extend(match_ids)

    time.sleep(DELAY)

print()
print(f"Discovered {len(all_match_ids)} match IDs across {NUM_GAMEDAYS} gamedays")

all_match_ids = sorted(list(set(all_match_ids)))
print(f"Unique matches: {len(all_match_ids)}")

with open(OUTPUT_DIR / "match_ids.txt", "w") as f:
    f.write("\n".join(all_match_ids))

print()
print("[2/7] Fetching match data and player stats...")

player_stats = {}
games_data = []

for i, match_id in enumerate(all_match_ids):
    print(f"Fetching match ({i + 1}/{len(all_match_ids)}): {match_id}")

    try:
        match_data = json.loads(fetch_url(f"{API_ENDPOINT}/{match_id}"))

        with open(OUTPUT_DIR / "matches" / f"match_{match_id}.json", "w") as f:
            json.dump(match_data, f, indent=2)

        match_state = match_data.get("matchState")
        home_team = match_data.get("homeTeam", {}).get("name", "Unknown")
        away_team = match_data.get("awayTeam", {}).get("name", "Unknown")
        timestamp = match_data.get("timeStamp", 0)
        gameday_name = match_data.get("gameday", {}).get("name", "Unknown")

        print(f"  - {home_team} vs {away_team}")
        print(f"  - State: {match_state}, Gameday: {gameday_name}")

        games = match_data.get("games", [])
        print(f"  - Games: {len(games)}")

        for game in games:
            game_index = game.get("index")
            game_state = game.get("gameState")
            winner_side = game.get("winnerSide")

            home_player = game.get("homePlayer") or game.get("homeLeaguePlayer") or {}
            away_player = game.get("awayPlayer") or game.get("awayLeaguePlayer") or {}

            home_player_id = home_player.get("id") if home_player else None
            away_player_id = away_player.get("id") if away_player else None

            home_player_name = (
                f"{home_player.get('firstName', '')} {home_player.get('lastName', '')}".strip()
                if home_player
                else "Unknown"
            )
            away_player_name = (
                f"{away_player.get('firstName', '')} {away_player.get('lastName', '')}".strip()
                if away_player
                else "Unknown"
            )

            game_record = {
                "matchId": match_id,
                "gameday": gameday_name,
                "timestamp": timestamp,
                "gameIndex": game_index,
                "gameState": game_state,
                "winnerSide": winner_side,
                "homePlayer": {"id": home_player_id, "name": home_player_name},
                "awayPlayer": {"id": away_player_id, "name": away_player_name},
            }
            games_data.append(game_record)

            if game_state == "Finished":
                if home_player_id and home_player_id != "null":
                    if home_player_id not in player_stats:
                        player_stats[home_player_id] = {
                            "id": home_player_id,
                            "name": home_player_name,
                            "gamesPlayed": 0,
                            "wins": 0,
                            "losses": 0,
                            "lastMatch": match_id,
                        }

                    player_stats[home_player_id]["gamesPlayed"] += 1
                    player_stats[home_player_id]["lastMatch"] = match_id

                    if winner_side == "Home":
                        player_stats[home_player_id]["wins"] += 1
                    else:
                        player_stats[home_player_id]["losses"] += 1

                if away_player_id and away_player_id != "null":
                    if away_player_id not in player_stats:
                        player_stats[away_player_id] = {
                            "id": away_player_id,
                            "name": away_player_name,
                            "gamesPlayed": 0,
                            "wins": 0,
                            "losses": 0,
                            "lastMatch": match_id,
                        }

                    player_stats[away_player_id]["gamesPlayed"] += 1
                    player_stats[away_player_id]["lastMatch"] = match_id

                    if winner_side == "Away":
                        player_stats[away_player_id]["wins"] += 1
                    else:
                        player_stats[away_player_id]["losses"] += 1

        time.sleep(DELAY)

    except Exception as e:
        print(f"  Error processing match {match_id}: {e}")
        continue

print()
print("[3/7] Calculating player win rates...")

player_stats_final = []
for player_id, stats in player_stats.items():
    stats_copy = stats.copy()
    if stats_copy["gamesPlayed"] > 0:
        stats_copy["winRate"] = int(
            stats_copy["wins"] / stats_copy["gamesPlayed"] * 100
        )
    else:
        stats_copy["winRate"] = 0
    player_stats_final.append(stats_copy)

player_stats_final.sort(key=lambda x: x["winRate"], reverse=True)

with open(OUTPUT_DIR / "stats" / "player_stats_final.json", "w") as f:
    json.dump(player_stats_final, f, indent=2)

print(f"  Processed {len(player_stats_final)} players")

print()
print("[4/7] Extracting unique players...")

all_players = []
for match_id in all_match_ids:
    match_file = OUTPUT_DIR / "matches" / f"match_{match_id}.json"
    if match_file.exists():
        with open(match_file, "r") as f:
            match_data = json.load(f)

        players_list = [
            match_data.get("homePlayerOne"),
            match_data.get("homePlayerTwo"),
            match_data.get("homePlayerThree"),
            match_data.get("guestPlayerOne"),
            match_data.get("guestPlayerTwo"),
            match_data.get("guestPlayerThree"),
        ]

        for player in players_list:
            if player:
                all_players.append(
                    {
                        "id": player.get("id"),
                        "firstName": player.get("firstName"),
                        "lastName": player.get("lastName"),
                        "imageUrl": player.get("imageUrl"),
                        "matchId": match_id,
                    }
                )

unique_players = {}
for player in all_players:
    if player["id"] and player["id"] not in unique_players:
        unique_players[player["id"]] = player

players_list = list(unique_players.values())

with open(OUTPUT_DIR / "players" / "all_players.json", "w") as f:
    json.dump(all_players, f, indent=2)

with open(OUTPUT_DIR / "players" / "unique_players.json", "w") as f:
    json.dump(players_list, f, indent=2)

print(f"  Found {len(players_list)} unique players")

print()
print("[5/7] Generating match summaries...")

matches_summary = []
for match_id in all_match_ids:
    match_file = OUTPUT_DIR / "matches" / f"match_{match_id}.json"
    if match_file.exists():
        with open(match_file, "r") as f:
            match_data = json.load(f)

        summary = {
            "matchId": match_data.get("id"),
            "matchState": match_data.get("matchState"),
            "gameday": match_data.get("gameday", {}).get("name"),
            "timestamp": match_data.get("timeStamp"),
            "homeTeam": {
                "id": match_data.get("homeTeam", {}).get("id"),
                "name": match_data.get("homeTeam", {}).get("name"),
                "rank": match_data.get("homeTeam", {}).get("rank"),
                "gameWins": match_data.get("homeGameWins"),
                "setWins": match_data.get("homeSetWins"),
            },
            "awayTeam": {
                "id": match_data.get("awayTeam", {}).get("id"),
                "name": match_data.get("awayTeam", {}).get("name"),
                "rank": match_data.get("awayTeam", {}).get("rank"),
                "gameWins": match_data.get("awayGameWins"),
                "setWins": match_data.get("awaySetWins"),
            },
            "gamesCount": len(match_data.get("games", [])),
            "venue": match_data.get("venue", {}).get("name"),
        }
        matches_summary.append(summary)

with open(OUTPUT_DIR / "matches_summary.json", "w") as f:
    json.dump(matches_summary, f, indent=2)

print(f"  Generated {len(matches_summary)} match summaries")

print()
print("[6/7] Creating metadata file...")

metadata = {
    "scrapeDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "season": SEASON,
    "totalMatches": len(all_match_ids),
    "totalGamedays": NUM_GAMEDAYS,
    "uniquePlayers": len(players_list),
    "playersWithStats": len(player_stats_final),
    "totalGamesProcessed": len(games_data),
    "source": "https://www.ttbl.de",
    "version": "3.0-python",
}

with open(OUTPUT_DIR / "stats" / "games_data.json", "w") as f:
    json.dump(games_data, f, indent=2)

with open(OUTPUT_DIR / "metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print()
print("[7/7] Generating reports...")

top_players = [p for p in player_stats_final if p["gamesPlayed"] >= 5][:20]
with open(OUTPUT_DIR / "stats" / "top_players.json", "w") as f:
    json.dump(top_players, f, indent=2)

match_states = Counter(m["matchState"] for m in matches_summary)
match_states_list = [{"state": k, "count": v} for k, v in match_states.items()]

with open(OUTPUT_DIR / "stats" / "match_states.json", "w") as f:
    json.dump(match_states_list, f, indent=2)

print()
print("=" * 50)
print("SCRAPING COMPLETE")
print("=" * 50)
print(json.dumps(metadata, indent=2))
print()
print("=" * 50)
print("FILES CREATED:")
print("=" * 50)
print(f"Data directory: {OUTPUT_DIR}/")
print()
print("Match Data:")
print("  - match_ids.txt - All match IDs discovered")
print("  - matches/ - Individual match JSON files (full data)")
print("  - matches_summary.json - Match summaries with metadata")
print()
print("Player Data:")
print("  - players/all_players.json - All players from all matches")
print("  - players/unique_players.json - Deduplicated player list")
print()
print("Statistics:")
print("  - stats/player_stats_final.json - Player win/loss rates")
print("  - stats/top_players.json - Top 20 players (min 5 games)")
print("  - stats/games_data.json - Individual game results")
print("  - stats/match_states.json - Match state breakdown")
print()
print("Metadata:")
print("  - metadata.json - Scrape session metadata")
