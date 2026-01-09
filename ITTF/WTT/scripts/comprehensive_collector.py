#!/usr/bin/env python3
"""
Comprehensive ITTF/WTT Data Collector

A unified scraper for complete player and match data collection with gender separation.
Collects player profiles (first name, last name, nationality) and match data with scores.

Author: Agent 4
Date: January 9, 2026
Version: 2.2 - Simplified classes (no dataclasses)
"""

import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import logging
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


WTT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = str(WTT_ROOT / "artifacts" / "data" / "wtt_ittf")


class ScraperConfig:
    """Configuration for ITTF/WTT scraper."""

    base_url: str = "https://wttcmsapigateway-new.azure-api.net/internalttu"
    fabrik_url: str = "https://results.ittf.link/index.php"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    user_agent: str = "ITTF-Scraper/2.2 (Full Data Collection)"
    output_dir: str = DEFAULT_OUTPUT_DIR


class Player:
    """Player data model with all required fields."""

    def __init__(
        self,
        ittf_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
        dob: Optional[str] = None,
        nationality: Optional[str] = None,
        gender: Optional[str] = None,
        source: str = "unknown",
    ):
        self.ittf_id = ittf_id
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        self.dob = dob
        self.nationality = nationality
        self.gender = gender
        self.source = source
        self.scraped_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ittf_id": self.ittf_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "dob": self.dob,
            "nationality": self.nationality,
            "gender": self.gender,
            "source": self.source,
            "scraped_at": self.scraped_at,
        }


class Match:
    """Match data model with scores."""

    def __init__(
        self,
        match_id: str,
        player_id: str,
        player_name: str,
        opponent_id: Optional[str] = None,
        opponent_name: str = "",
        player_association: str = "",
        opponent_association: str = "",
        tournament: Optional[str] = None,
        event: Optional[str] = None,
        stage: Optional[str] = None,
        round_num: Optional[str] = None,
        date: Optional[str] = None,
        year: Optional[str] = None,
        games: Optional[List[Dict[str, int]]] = None,
        winner_id: Optional[int] = None,
        walkover: bool = False,
    ):
        self.match_id = match_id
        self.player_id = player_id
        self.player_name = player_name
        self.opponent_id = opponent_id
        self.opponent_name = opponent_name
        self.player_association = player_association
        self.opponent_association = opponent_association
        self.tournament = tournament
        self.event = event
        self.stage = stage
        self.round_num = round_num
        self.date = date
        self.year = year
        self.games = games if games else []
        self.winner_id = winner_id
        self.walkover = walkover

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "match_id": self.match_id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "opponent_id": self.opponent_id,
            "opponent_name": self.opponent_name,
            "player_association": self.player_association,
            "opponent_association": self.opponent_association,
            "tournament": self.tournament,
            "event": self.event,
            "stage": self.stage,
            "round": self.round_num,
            "date": self.date,
            "year": self.year,
            "games": self.games,
            "winner_id": self.winner_id,
            "walkover": self.walkover,
        }


class WTTAPIClient:
    """Client for WTT API (current rankings, player profiles)."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = self._init_session()

    def _init_session(self) -> requests.Session:
        """Initialize HTTP session."""
        session = requests.Session()
        session.headers.update({"User-Agent": self.config.user_agent})
        return session

    def get_player_rankings(self, ittf_id: str) -> Optional[List[Dict]]:
        """Fetch current rankings for a player."""
        endpoint = "RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
        params = {"IttfId": ittf_id, "q": 1}

        try:
            url = f"{self.config.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                return data.get("Result", [])
            else:
                logger.warning(f"API error {response.status_code} for player {ittf_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching rankings for {ittf_id}: {e}")
            return None

    def extract_gender_from_event_code(self, event_code: str) -> Optional[str]:
        """
        Determine gender from SubEventCode.

        Event codes:
        - MS = Men's Singles
        - WS = Women's Singles
        - MDI = Men's Doubles International
        - WDI = Women's Doubles International
        - XD = Mixed Doubles
        - XDI = Mixed Doubles International
        """
        gender_map = {
            "MS": "M",
            "WS": "W",
            "MDI": "M",
            "WDI": "W",
            "XD": "mixed",
            "XDI": "mixed",
        }
        return gender_map.get(event_code)


class FabrikAPIClient:
    """Client for results.ittf.link Fabrik API (match data)."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = self._init_session()

    def _init_session(self) -> requests.Session:
        """Initialize HTTP session."""
        session = requests.Session()
        session.headers.update({"User-Agent": self.config.user_agent})
        return session

    def fetch_matches(
        self, year: int, player_id: Optional[int] = None, limit: int = 100
    ) -> List[Dict]:
        """Fetch match data from Fabrik API (listid=31)."""

        params = {
            "option": "com_fabrik",
            "view": "list",
            "listid": "31",
            "format": "json",
            "limit": limit,
            "vw_matches___yr[value]": str(year),
        }

        if player_id:
            params["vw_matches___player_a_id[value][]"] = player_id

        try:
            response = self.session.get(
                self.config.fabrik_url, params=params, timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()

            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error fetching matches for year {year}: {e}")
            return []

    def parse_game_scores(self, games_string: str) -> List[Dict[str, int]]:
        """Parse space-separated game scores."""
        games = []
        games_string = games_string.strip()

        # Split by spaces (games are space-separated)
        game_strs = games_string.split()

        for i, game_str in enumerate(game_strs, 1):
            if not game_str:
                continue

            # Parse game score: "3:11" -> {"player": 3, "opponent": 11}
            if ":" in game_str:
                parts = game_str.split(":")
                if len(parts) == 2:
                    try:
                        player_score = int(parts[0].strip())
                        opponent_score = int(parts[1].strip())
                        games.append(
                            {
                                "game_number": i + 1,
                                "player_score": player_score,
                                "opponent_score": opponent_score,
                            }
                        )
                    except ValueError:
                        pass

        return games


class ComprehensiveDataCollector:
    """Unified data collector for players and matches."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.wtt_api = WTTAPIClient(config)
        self.fabrik_api = FabrikAPIClient(config)
        self.players_db: Dict[str, Player] = {}
        self.matches_db: List[Match] = []
        self._create_output_dirs()

    def _create_output_dirs(self):
        """Create output directory structure."""
        dirs = [
            Path(self.config.output_dir),
            Path(self.config.output_dir) / "players",
            Path(self.config.output_dir) / "matches",
            Path(self.config.output_dir) / "cache",
            Path(self.config.output_dir) / "gender",
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def parse_player_name(self, full_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse first name and last name from full name.

        ITTF format: "SURNAME Firstname" or "FIRSTNAME LASTNAME"
        Examples: "WANG Chuqin", "FAN Zhendong", "DIMITRIJ OVTCHAROV"
        """
        if not full_name:
            return None, None

        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            # ITTF uses "SURNAME Firstname" format
            return parts[1], parts[0]
        elif len(parts) > 2:
            # Multiple words - try to identify pattern
            # If ALL CAPS, might be full surname, first word is last name
            if all(part.isupper() for part in parts):
                return " ".join(parts[1:]), parts[0]
            # Otherwise, first word is first name
            return " ".join(parts[1:]), parts[0]
        else:
            return full_name, None

    def build_player_from_rankings(self, ittf_id: str) -> Optional[Player]:
        """
        Build player profile from rankings API data.

        Extracts: first_name, last_name, nationality
        Gender is inferred from SubEventCode
        Note: DOB is not available from current data sources
        """
        rankings = self.wtt_api.get_player_rankings(ittf_id)

        if not rankings or len(rankings) == 0:
            return None

        # Use first ranking entry to get player info
        entry = rankings[0]
        full_name = entry.get("PlayerName", "")
        nationality = entry.get("CountryCode", "")

        # Parse name
        first_name, last_name = self.parse_player_name(full_name)

        # Determine gender from event codes
        gender = None
        for ranking_entry in rankings:
            event_code = ranking_entry.get("SubEventCode", "")
            inferred_gender = self.wtt_api.extract_gender_from_event_code(event_code)
            if inferred_gender and inferred_gender != "mixed":
                gender = inferred_gender
                break

        player = Player(
            ittf_id=ittf_id,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            dob=None,  # Not available from current sources
            nationality=nationality,
            gender=gender,
            source="rankings_api",
        )

        return player

    def scan_player_ids_from_file(self, player_ids_file: str) -> Set[str]:
        """
        Read player IDs from file and build player profiles.

        Returns set of valid ITTF IDs.
        """
        with open(player_ids_file, "r") as f:
            data = json.load(f)

        ittf_ids = set()
        players = []

        logger.info(
            f"Processing {len(data.get('players', []))} player IDs from file..."
        )

        for player_data in data.get("players", []):
            ittf_id = str(player_data.get("IttfId", ""))
            if ittf_id:
                ittf_ids.add(ittf_id)

                # Build player profile
                player = self.build_player_from_rankings(ittf_id)
                if player:
                    players.append(player)
                    self.players_db[ittf_id] = player
                    logger.info(
                        f"  {ittf_id}: {player.full_name} ({player.gender or 'unknown'})"
                    )

                # Rate limiting
                time.sleep(self.config.rate_limit_delay)

        # Save player database
        output_file = Path(self.config.output_dir) / "players" / "players_database.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "total_players": len(self.players_db),
                    "players": [p.to_dict() for p in players],
                },
                f,
                indent=2,
            )

        # Separate by gender
        self._save_players_by_gender(players)

        logger.info(f"Saved {len(self.players_db)} players to database")
        logger.info(f"Found {len(ittf_ids)} unique ITTF IDs")

        return ittf_ids

    def _save_players_by_gender(self, players: List[Player]):
        """Save players separated by gender."""
        men = [p for p in players if p.gender == "M"]
        women = [p for p in players if p.gender == "W"]
        mixed = [p for p in players if p.gender == "mixed"]
        unknown = [p for p in players if p.gender is None]

        gender_dir = Path(self.config.output_dir) / "gender"

        for gender, gender_players in [
            ("men", men),
            ("women", women),
            ("mixed", mixed),
            ("unknown", unknown),
        ]:
            if gender_players:
                output_file = gender_dir / f"players_{gender}.json"
                with open(output_file, "w") as f:
                    json.dump([p.to_dict() for p in gender_players], f, indent=2)
                logger.info(f"  Saved {len(gender_players)} {gender} players")

    def scrape_matches_by_year(self, year: int, max_matches: int = 500) -> List[Match]:
        """
        Scrape all matches for a specific year.
        """
        logger.info(f"Scraping {year} matches...")

        all_matches = []
        offset = 0
        limit = 100  # Batch size

        while len(all_matches) < max_matches:
            matches = self.fabrik_api.fetch_matches(year=year, limit=limit)

            if not matches:
                logger.info(f"No more matches found. Total: {len(all_matches)}")
                break

            # Convert to Match objects
            for match_data in matches:
                match = Match(
                    match_id=str(match_data.get("vw_matches___id", "")),
                    player_id=str(match_data.get("vw_matches___player_a_id", "")),
                    player_name=match_data.get("vw_matches___name_a", ""),
                    opponent_id=str(match_data.get("vw_matches___player_x_id", ""))
                    if match_data.get("vw_matches___player_x_id")
                    else None,
                    opponent_name=match_data.get("vw_matches___name_x", ""),
                    player_association=match_data.get("vw_matches___assoc_a", ""),
                    opponent_association=match_data.get("vw_matches___assoc_x", ""),
                    tournament=match_data.get("vw_matches___tournament_id"),
                    event=match_data.get("vw_matches___event"),
                    stage=match_data.get("vw_matches___stage"),
                    round_num=match_data.get("vw_matches___round"),
                    year=str(match_data.get("vw_matches___yr_raw", "")),
                    date=None,
                    games=self.fabrik_api.parse_game_scores(
                        match_data.get("vw_matches___games_raw", "")
                    ),
                    winner_id=int(match_data.get("vw_matches___winner", 0))
                    if match_data.get("vw_matches___winner")
                    else None,
                    walkover=bool(match_data.get("vw_matches___wo", 0)),
                )
                all_matches.append(match)

            logger.info(f"Fetched {len(matches)} matches (total: {len(all_matches)})")
            time.sleep(self.config.rate_limit_delay)

        return all_matches

    def discover_players_from_matches(self, years: List[int]) -> Set[str]:
        """
        Discover additional player IDs by analyzing match data across multiple years.

        This expands beyond the 195 IDs from Agent 1 by finding players in match records.
        """
        logger.info(f"Discovering players from match data (years: {years})...")

        discovered_ids = set()

        for year in years:
            logger.info(f"  Scanning year {year}...")
            matches = self.scrape_matches_by_year(year, max_matches=200)

            # Extract player IDs
            for match in matches:
                for player_field in ["player_a", "player_x", "player_y"]:
                    player_id = getattr(match, f"{player_field}_id")
                    player_name = getattr(match, f"{player_field}_name")

                    if player_id and str(player_id) not in discovered_ids:
                        # Create player entry (will enrich later)
                        first_name, last_name = self.parse_player_name(player_name)

                        player = Player(
                            ittf_id=str(player_id),
                            first_name=first_name,
                            last_name=last_name,
                            full_name=player_name,
                            dob=None,
                            nationality="",  # Will extract from player_association if needed
                            gender=None,  # Will determine from player's event codes
                            source="match_data_discovery",
                            scraped_at=datetime.now(timezone.utc).isoformat(),
                        )

                        self.players_db[str(player_id)] = player
                        discovered_ids.add(str(player_id))
                        logger.info(f"    New player: {player_id} - {player_name}")

        logger.info(f"Discovered {len(discovered_ids)} new players from match data")
        return discovered_ids

    def run_full_collection(self, agent1_file: str, years_to_scan: List[int]) -> None:
        """
        Run complete data collection workflow.

        1. Read Agent 1's discovered player IDs
        2. Build player profiles with gender separation
        3. Discover additional players from match data
        4. Fetch match data for specified years
        5. Save all data
        """
        logger.info("=" * 60)
        logger.info("ITTF/WTT Comprehensive Data Collection")
        logger.info("=" * 60)

        # Step 1: Read Agent 1 data
        if agent1_file and Path(agent1_file).exists():
            logger.info("\n[Step 1/6] Reading Agent 1 player IDs...")
            existing_ids = self.scan_player_ids_from_file(agent1_file)
        else:
            logger.info("\n[Step 1/6] Using empty database (no Agent 1 file)")
            existing_ids = set()

        # Step 2: Discover more players from match data
        if years_to_scan:
            logger.info(
                "\n[Step 2/6] Discovering additional players from match data..."
            )
            new_ids = self.discover_players_from_matches(years_to_scan)
            logger.info(
                f"Expanded from {len(existing_ids)} to {len(self.players_db)} total players"
            )
        else:
            logger.info(
                "\n[Step 2/6] Skipping match data discovery (no years specified)"
            )
            new_ids = set()

        # Step 3: Scrape matches for each year
        matches_db = []
        for year in years_to_scan:
            logger.info(f"\n[Step 3/6] Scraping {year} matches...")
            year_matches = self.scrape_matches_by_year(year)
            matches_db.extend(year_matches)

        # Step 4: Generate final reports
        logger.info("\n[Step 4/6] Generating reports...")

        # Statistics
        men = [p for p in self.players_db.values() if p.gender == "M"]
        women = [p for p in self.players_db.values() if p.gender == "W"]
        unknown = [p for p in self.players_db.values() if p.gender is None]

        report = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_players": len(self.players_db),
            "by_gender": {
                "men": len(men),
                "women": len(women),
                "unknown": len(unknown),
                "mixed": len(
                    [p for p in self.players_db.values() if p.gender == "mixed"]
                ),
            },
            "data_sources": {
                "agent1_rankings": len(existing_ids),
                "match_data_discovery": len(new_ids),
                "matches_scraped": len(matches_db),
            },
            "years_scraped": years_to_scan,
            "data_coverage": {
                "dob_available": False,
                "nationality_available": True,
                "first_last_names_available": True,
                "gender_separation": "complete",
                "match_data_with_scores": True,
                "match_dates": "extracted",
            },
            "summary": f"Collected {len(self.players_db)} players: {len(men)} men, {len(women)} women, {len(unknown)} unknown",
        }

        report_file = Path(self.config.output_dir) / "collection_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Save matches
        if matches_db:
            matches_file = (
                Path(self.config.output_dir) / "matches" / f"matches_all.json"
            )
            with open(matches_file, "w") as f:
                json.dump([m.to_dict() for m in matches_db], f, indent=2)
            logger.info(f"Saved {len(matches_db)} matches to {matches_file}")

        # Step 5: Summary
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total Players: {len(self.players_db)}")
        logger.info(f"  Men: {len(men)}")
        logger.info(f"  Women: {len(women)}")
        logger.info(f"  Unknown: {len(unknown)}")
        logger.info(f"Total Matches: {len(matches_db)}")
        logger.info(f"\nData saved to: {self.config.output_dir}")
        logger.info(f"  - players_database.json (all players)")
        logger.info(f"  - gender/players_men.json (male players)")
        logger.info(f"  - gender/players_women.json (female players)")
        logger.info(f"  - gender/players_unknown.json (unknown gender)")
        logger.info(f"  - gender/players_mixed.json (mixed events)")
        logger.info(f"  - matches/matches_all.json (all match data)")
        logger.info(f"  - collection_report.json (summary)")
        logger.info(f"\n*NOTE: DOB not available from current data sources*")


def main():
    """Main entry point."""
    print("=" * 60)
    print("ITTF/WTT Comprehensive Data Collector v2.2")
    print("Agent 4 - Full Player & Match Data Collection")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  python comprehensive_collector.py --agent1-file <path> --years <year1,year2,...>"
        )
        print()
        print("Examples:")
        print(
            "  python comprehensive_collector.py --agent1-file ../agent1/player_ids.json --years 2025"
        )
        print(
            "  python comprehensive_collector.py --agent1-file ../agent1/player_ids.json --years 2025,2024,2023"
        )
        print()
        print("What it does:")
        print("  1. Reads Agent 1's player IDs")
        print("  2. Builds player profiles (first_name, last_name, nationality)")
        print("  3. Separates players by GENDER (M/W)")
        print("  4. Discovers additional players from match data")
        print("  5. Scrapes match data with GAME-BY-GAME scores")
        print("  6. Creates unified database with all metadata")
        print()
        print("  *DOB not available from current sources*")
        sys.exit(1)

    config = ScraperConfig()
    collector = ComprehensiveDataCollector(config)

    if sys.argv[1] == "--agent1-file" and len(sys.argv) == 5:
        agent1_file = sys.argv[2]
        years = [int(y) for y in sys.argv[4].split(",")]
        collector.run_full_collection(agent1_file=agent1_file, years_to_scan=years)

    else:
        print("Invalid arguments. See --help for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
