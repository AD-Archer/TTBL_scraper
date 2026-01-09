#!/usr/bin/env python3
"""
ITTF/WTT Comprehensive Data Scraper
Combines all agent discoveries for complete player and match data collection

Features:
- Fabrik API match data (Agent 3)
- Player extraction with gender separation
- Full metadata collection
- Current rankings integration (Agent 4)
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class ComprehensiveScraperConfig:
    """Configuration for the comprehensive scraper"""

    base_url: str = "https://results.ittf.link/index.php"
    rankings_url: str = "https://wttcmsapigateway-new.azure-api.net/internalttu"
    player_matches_list_id: str = "31"
    timeout: int = 30
    delay: float = 0.5
    output_dir: Path = Path("./ITTF/WTT/data")


class ITTFComprehensiveScraper:
    """Comprehensive scraper combining all agent discoveries"""

    def __init__(self, config: Optional[ComprehensiveScraperConfig] = None):
        self.config = config or ComprehensiveScraperConfig()
        self.session = requests.Session()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Track extracted data
        self.all_players: Dict[str, Dict] = {}
        self.all_matches: List[Dict] = []
        self.player_genders: Dict[str, str] = {}

    def fetch_fabrik_matches(self, year: int, limit: int = 1000) -> List[Dict]:
        """Fetch match data from Fabrik API"""
        params = {
            "option": "com_fabrik",
            "view": "list",
            "listid": self.config.player_matches_list_id,
            "format": "json",
            "vw_matches___yr[value]": year,
            "limit": limit,
        }

        try:
            response = self.session.get(
                self.config.base_url, params=params, timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                # API returns [[matches...]]
                if isinstance(data[0], list):
                    matches = data[0]
                else:
                    matches = data

                print(f"Fetched {len(matches)} matches for {year}")
                return matches
            else:
                print(f"No data returned for {year}")
                return []

        except Exception as e:
            print(f"Error fetching {year} matches: {e}")
            return []

    def extract_player_from_match(
        self, match: Dict, player_suffix: str
    ) -> Optional[Dict]:
        """Extract player info from match data"""
        player_id = match.get(f"vw_matches___player_{player_suffix}_id")
        player_name = match.get(f"vw_matches___name_{player_suffix}")
        player_assoc = match.get(f"vw_matches___assoc_{player_suffix}")

        print(f"Checking {player_suffix}: ID={player_id}, Name={player_name}")

        if not player_id or not player_name:
            return None

        if not player_id or not player_name:
            return None

        # Parse name: "LASTNAME Firstname (Country)" -> separate fields
        name_match = re.match(r"^(.+?)\s+(.+?)\s*\((.+)\)$", player_name.strip())
        if name_match:
            last_name, first_name, country = name_match.groups()
        else:
            # Fallback: assume "Full Name (Country)"
            name_parts = player_name.split(" (")
            if len(name_parts) == 2:
                full_name = name_parts[0].strip()
                country = name_parts[1].rstrip(")")
                # Split full name into first/last (rough approximation)
                name_words = full_name.split()
                first_name = " ".join(name_words[:-1]) if len(name_words) > 1 else ""
                last_name = name_words[-1] if name_words else full_name
            else:
                first_name = ""
                last_name = player_name
                country = player_assoc or ""

        return {
            "id": str(player_id),
            "first_name": first_name,
            "last_name": last_name,
            "full_name": player_name,
            "country": country,
            "association": player_assoc or country,
        }

    def determine_player_gender(self, player_id: str, event_code: str) -> str:
        """Determine player gender from event code"""
        if event_code.startswith("MS") or event_code.startswith("MD"):
            return "male"
        elif event_code.startswith("WS") or event_code.startswith("WD"):
            return "female"
        elif event_code.startswith("XD"):
            return "mixed"  # Mixed doubles
        else:
            return "unknown"

    def parse_game_scores(self, games_string: str) -> List[Dict]:
        """Parse space-separated game scores"""
        games = []
        if not games_string:
            return games

        # Remove trailing whitespace and split by spaces
        games_string = games_string.strip()

        for i, game_str in enumerate(games_string.split()):
            if not game_str or ":" not in game_str:
                continue

            try:
                player_score, opponent_score = game_str.split(":")
                games.append(
                    {
                        "game_number": i + 1,
                        "player_score": int(player_score),
                        "opponent_score": int(opponent_score),
                    }
                )
            except ValueError:
                continue

        return games

    def process_matches(self, matches: List[Dict]):
        """Process match data to extract players and structure matches"""
        print(f"Processing {len(matches)} matches...")
        processed_matches = []

        for match in matches:
            # Extract tournament info
            tournament = match.get("vw_matches___tournament_id", "")
            event = match.get("vw_matches___event_raw", "")
            stage = match.get("vw_matches___stage_raw", "")
            round_info = match.get("vw_matches___round_raw", "")
            year = match.get("vw_matches___yr_raw")

            # Extract players
            players = {}
            for player_suffix in ["a", "x", "y"]:
                player_data = self.extract_player_from_match(match, player_suffix)
                if player_data:
                    player_id = player_data["id"]
                    players[f"player_{player_suffix}"] = player_data
                    print(f"Added player {player_suffix} to match: {player_id}")

                    # Update global players dict
                    if player_id not in self.all_players:
                        self.all_players[player_id] = player_data

                    # Determine and store gender
                    if player_id not in self.player_genders:
                        gender = self.determine_player_gender(player_id, event)
                        self.player_genders[player_id] = gender
                        self.all_players[player_id]["gender"] = gender

            # Parse scores
            result = match.get("vw_matches___res_raw", "")
            games_string = match.get("vw_matches___games_raw", "")
            games = self.parse_game_scores(games_string)

            winner_id = match.get("vw_matches___winner_raw")
            walkover = match.get("vw_matches___wo_raw", 0) == 1

            # Structure match data
            match_data = {
                "match_id": match.get("vw_matches___id_raw"),
                "year": year,
                "tournament": tournament,
                "event": event,
                "stage": stage,
                "round": round_info,
                "players": players,
                "result": result,
                "games": games,
                "winner_id": str(winner_id) if winner_id else None,
                "walkover": walkover,
            }

            processed_matches.append(match_data)

        return processed_matches

    def fetch_current_rankings(self, player_id: str) -> Optional[Dict]:
        """Fetch current rankings for a player"""
        try:
            endpoint = f"{self.config.rankings_url}/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
            params = {"IttfId": player_id, "q": 1}

            response = self.session.get(endpoint, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("Result")
        except Exception as e:
            print(f"Error fetching rankings for {player_id}: {e}")

        return None

    def enrich_players_with_rankings(self):
        """Add current rankings data to player records"""
        print(f"Enriching {len(self.all_players)} players with rankings data...")

        for player_id, player_data in self.all_players.items():
            rankings = self.fetch_current_rankings(player_id)
            if rankings:
                player_data["current_rankings"] = rankings
                print(f"✓ Added rankings for {player_data['full_name']}")
            else:
                player_data["current_rankings"] = []

            time.sleep(self.config.delay)

    def fetch_all_fabrik_matches_for_year(self, year: int) -> List[Dict]:
        """Fetch ALL matches for a year using pagination"""
        all_matches = []
        limit = 100  # Batch size
        start = 0

        while True:
            # Modify the URL to include pagination
            params = {
                "option": "com_fabrik",
                "view": "list",
                "listid": self.config.player_matches_list_id,
                "format": "json",
                "vw_matches___yr[value]": year,
                "limit": limit,
                "start": start,  # Joomla pagination parameter
            }

            try:
                response = self.session.get(
                    self.config.base_url, params=params, timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list):
                        matches = data[0]
                    else:
                        matches = data

                    if not matches:
                        break  # No more matches

                    all_matches.extend(matches)
                    print(
                        f"Fetched {len(matches)} matches (total: {len(all_matches)}) for {year}"
                    )

                    start += limit
                    time.sleep(self.config.delay)
                else:
                    break

            except Exception as e:
                print(f"Error fetching {year} matches at start={start}: {e}")
                break

        return all_matches

    def scrape_comprehensive_data(self, years: Optional[List[int]] = None):
        """Main scraping function - get ALL data"""
        if years is None:
            # Get all years from 2000 to current
            import datetime

            current_year = datetime.datetime.now().year
            years = list(range(2000, current_year + 1))

        print("Starting comprehensive ITTF/WTT data scraping...")
        print(f"Years to scrape: {len(years)} years ({years[0]}-{years[-1]})")

        total_matches = 0
        total_players = 0

        for year in years:
            print(f"\n=== Scraping {year} ===")

            # Fetch ALL match data for this year
            matches = self.fetch_all_fabrik_matches_for_year(year)
            if not matches:
                print(f"No matches found for {year}")
                continue

            # Process matches
            processed_matches = self.process_matches(matches)
            self.all_matches.extend(processed_matches)

            # Update totals
            new_players = len(self.all_players) - total_players
            total_matches += len(processed_matches)
            total_players = len(self.all_players)

            print(
                f"Year {year}: {len(processed_matches)} matches, {new_players} new players"
            )
            print(f"Running total: {total_matches} matches, {total_players} players")

        print("\n=== Processing Complete ===")
        print(f"Total unique players: {len(self.all_players)}")
        print(f"Total matches: {len(self.all_matches)}")

        # Save data
        self.save_all_data()

    def save_all_data(self):
        """Save all collected data"""
        timestamp = datetime.now().isoformat()

        # Save players by gender
        male_players = {
            pid: p for pid, p in self.all_players.items() if p.get("gender") == "male"
        }
        female_players = {
            pid: p for pid, p in self.all_players.items() if p.get("gender") == "female"
        }

        # Players data
        players_data = {
            "metadata": {
                "scraped_at": timestamp,
                "total_players": len(self.all_players),
                "male_players": len(male_players),
                "female_players": len(female_players),
                "source": "fabrik_api_matches",
            },
            "players": {
                "all": self.all_players,
                "male": male_players,
                "female": female_players,
            },
        }

        # Matches data
        matches_data = {
            "metadata": {
                "scraped_at": timestamp,
                "total_matches": len(self.all_matches),
                "source": "fabrik_api_matches",
            },
            "matches": self.all_matches,
        }

        # Save files
        players_file = self.config.output_dir / "players_comprehensive.json"
        matches_file = self.config.output_dir / "matches_comprehensive.json"

        with open(players_file, "w") as f:
            json.dump(players_data, f, indent=2, ensure_ascii=False)

        with open(matches_file, "w") as f:
            json.dump(matches_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(self.all_players)} players to {players_file}")
        print(f"✅ Saved {len(self.all_matches)} matches to {matches_file}")


def main():
    """Main entry point"""
    scraper = ITTFComprehensiveScraper()

    # Scrape recent years
    scraper.scrape_comprehensive_data(years=[2024, 2025, 2026])


if __name__ == "__main__":
    main()
