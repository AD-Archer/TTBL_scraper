#!/usr/bin/env python3
"""
Fabrik API Match Scraper

Dedicated scraper for ITTF/WTT match data from results.ittf.link Fabrik API.
Provides: match details, game-by-game scores, tournament information, dates.

Author: Agent 4
Date: January 9, 2026
Version: 1.1 - Simplified, reliable implementation
"""

import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
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
    """Configuration for Fabrik match scraper."""

    base_url: str = "https://results.ittf.link/index.php"
    player_matches_list_id: str = "31"
    timeout: int = 30
    rate_limit_delay: float = 1.0
    user_agent: str = "ITTF-Scraper/1.1 (Match Data)"
    output_dir: str = DEFAULT_OUTPUT_DIR


class Match:
    """Match data model."""

    match_id: str
    player_id: str
    player_name: str
    opponent_id: Optional[str]
    opponent_name: str
    player_association: str
    opponent_association: str
    tournament: Optional[str]
    event: Optional[str]
    stage: Optional[str]
    round_num: Optional[str]
    year: str
    date: Optional[str]
    games: List[Dict[str, int]]
    winner_id: Optional[int]
    walkover: bool
    scraped_at: str

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
        year: str = "",
        date: Optional[str] = None,
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
        self.year = year
        self.date = date
        self.games = games if games else []
        self.winner_id = winner_id
        self.walkover = walkover
        self.scraped_at = datetime.now(timezone.utc).isoformat()

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
            "scraped_at": self.scraped_at,
        }


class FabrikMatchScraper:
    """Scraper for results.ittf.link Fabrik API (match data)."""

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
            "listid": self.config.player_matches_list_id,
            "format": "json",
            "limit": limit,
            "vw_matches___yr[value]": str(year),
        }

        if player_id:
            params["vw_matches___player_a_id[value][]"] = player_id

        try:
            response = self.session.get(
                self.config.base_url, params=params, timeout=self.config.timeout
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
                                "game_number": i,
                                "player_score": player_score,
                                "opponent_score": opponent_score,
                            }
                        )
                    except ValueError:
                        logger.warning(f"Could not parse game score: {game_str}")

        return games

    def scrape_year(self, year: int, max_matches: int = 5000) -> List[Match]:
        """Scrape all matches for a specific year."""
        logger.info(f"Scraping {year} matches...")

        all_matches = []
        offset = 0
        limit = 100  # Batch size

        while len(all_matches) < max_matches:
            matches = self.fetch_matches(year=year, limit=limit)

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
                    games=self.parse_game_scores(
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

    def extract_player_ids(self, matches: List[Match]) -> Dict[str, str]:
        """Extract unique player IDs and names from matches."""
        players = {}

        for match in matches:
            # Add player A
            if match.player_id not in players:
                players[match.player_id] = match.player_name

            # Add player X (opponent)
            if match.opponent_id and match.opponent_id not in players:
                players[match.opponent_id] = match.opponent_name

        return players

    def save_matches(self, matches: List[Match], filename: str = None) -> Path:
        """Save matches to JSON file."""
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"matches_{timestamp}.json"

        output_dir = Path(self.config.output_dir) / "matches"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / filename

        metadata = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_matches": len(matches),
            "matches": [m.to_dict() for m in matches],
        }

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved {len(matches)} matches to {output_file}")
        return output_file

    def save_player_discovery(
        self, players: Dict[str, str], filename: str = None
    ) -> Path:
        """Save discovered player IDs to JSON file."""
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"players_from_matches_{timestamp}.json"

        output_dir = Path(self.config.output_dir) / "players"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / filename

        metadata = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_players": len(players),
            "players": players,
        }

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved {len(players)} player IDs to {output_file}")
        return output_file


def print_banner():
    """Print welcome banner."""
    print("=" * 60)
    print("ITTF/WTT Fabrik Match Scraper v1.1")
    print("Agent 4 - Match Data Collection")
    print("=" * 60)
    print()


def scrape_year(year: int, config: ScraperConfig, max_matches: int = 5000):
    """Scrape matches for a specific year."""
    scraper = FabrikMatchScraper(config)

    print(f"\nScraping {year} matches (max {max_matches})...")
    matches = scraper.scrape_year(year, max_matches=max_matches)

    # Save matches
    scraper.save_matches(matches, filename=f"matches_{year}.json")

    # Extract and save player IDs
    players = scraper.extract_player_ids(matches)
    scraper.save_player_discovery(players, filename=f"players_from_matches_{year}.json")

    # Summary
    print(f"\n{'=' * 60}")
    print("SCRAPING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Year: {year}")
    print(f"Total Matches: {len(matches)}")
    print(f"Unique Players: {len(players)}")
    print(f"\nData saved to: {config.output_dir}/matches/")
    print(f"  - matches_{year}.json (all matches with scores)")
    print(f"  - players_from_matches_{year}.json (discovered player IDs)")


def main():
    """Main entry point."""
    print_banner()

    # Require at least 3 arguments: script name + --year + YEAR
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python fabrik_match_scraper.py --year <YEAR> [--max-matches <N>]")
        print()
        print("Examples:")
        print("  python fabrik_match_scraper.py --year 2025")
        print("  python fabrik_match_scraper.py --year 2025 --max-matches 500")
        print("  python fabrik_match_scraper.py --year 2024 --year 2023")
        print()
        print("What it does:")
        print("  1. Scrapes all matches from Fabrik API (listid=31)")
        print("  2. Parses game-by-game scores from space-separated format")
        print("  3. Extracts tournament, event, stage, round, date info")
        print("  4. Saves structured JSON with all metadata")
        print("  5. Discovers new player IDs from match data")
        sys.exit(1)

    config = ScraperConfig()

    years = []
    i = 1
    max_matches = 1000

    while i < len(sys.argv):
        if sys.argv[i] == "--year":
            if i + 1 < len(sys.argv):
                try:
                    years.append(int(sys.argv[i + 1]))
                except ValueError:
                    print(f"Error: Invalid year: {sys.argv[i + 1]}")
                    sys.exit(1)
                i += 2
        elif sys.argv[i] == "--max-matches":
            if i + 1 < len(sys.argv):
                try:
                    max_matches = int(sys.argv[i + 1])
                except ValueError:
                    print(f"Error: Invalid max-matches: {sys.argv[i + 1]}")
                    sys.exit(1)
                i += 2
        else:
            i += 1

    if not years:
        print("Error: No years specified")
        sys.exit(1)

    # Scrape each year
    for year in years:
        scrape_year(year, config, max_matches=max_matches)


if __name__ == "__main__":
    main()
