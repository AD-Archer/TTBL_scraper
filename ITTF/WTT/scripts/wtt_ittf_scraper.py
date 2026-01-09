#!/usr/bin/env python3
"""
ITTF/WTT Data Scraper

A comprehensive scraper for ITTF (International Table Tennis Federation) and WTT (World Table Tennis)
rankings, players, and match data.

Author: Agent 4
Date: January 9, 2026
Version: 1.0
"""

import json
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

# Import requests as primary library
try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


WTT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = WTT_ROOT / "artifacts" / "data" / "wtt_ittf"


@dataclass
class ScraperConfig:
    """Configuration for ITTF/WTT scraper."""

    base_url: str = "https://wttcmsapigateway-new.azure-api.net/internalttu"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    user_agent: str = "ITTF-Scraper/1.0 (Data Collection)"
    output_dir: Path = DEFAULT_OUTPUT_DIR

    def __post_init__(self):
        """Ensure output_dir is a Path object."""
        self.output_dir = Path(self.output_dir)


class WTTRestScraper:
    """
    REST API client for ITTF/WTT data.

    Uses exponential backoff for rate limiting and implements retry logic.
    """

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = self._init_session()
        self._create_output_dirs()

        logger.info("Using requests for HTTP requests")

    def _init_session(self) -> requests.Session:
        """Initialize HTTP session with proper configuration."""
        session = requests.Session()
        session.headers.update({"User-Agent": self.config.user_agent})
        return session

    def _create_output_dirs(self):
        """Create output directory structure."""
        dirs = [
            self.config.output_dir,
            self.config.output_dir / "rankings",
            self.config.output_dir / "players",
            self.config.output_dir / "matches",
            self.config.output_dir / "cache",
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def _request_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Optional[Dict]:
        """
        Make HTTP request with retry logic and exponential backoff.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            method: HTTP method (GET or POST)

        Returns:
            JSON response data or None on failure
        """
        url = f"{self.config.base_url}/{endpoint}"
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(
                    f"Request: {method} {url} (attempt {attempt + 1}/{self.config.max_retries})"
                )

                response = self.session.request(
                    method, url, params=params, timeout=self.config.timeout
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    wait_time = retry_after * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Rate limited. Waiting {wait_time}s before retry..."
                    )
                    time.sleep(wait_time)
                    continue

                # Handle success
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        return None

                # Handle other errors
                if response.status_code in [401, 403, 404]:
                    logger.error(f"HTTP {response.status_code}: {response.text[:200]}")
                    return None

                # Retry on server errors
                if 500 <= response.status_code < 600:
                    raise requests.HTTPError(f"Server error: {response.status_code}")

                # Other status codes - don't retry
                logger.warning(f"HTTP {response.status_code}: {response.text[:200]}")
                return None

            except requests.RequestException as e:
                last_error = e
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

        logger.error(f"All retries exhausted. Last error: {last_error}")
        return None

    def get_player_rankings(self, ittf_id: str) -> Optional[List[Dict]]:
        """
        Fetch current rankings for a specific player.

        Args:
            ittf_id: Player's ITTF ID

        Returns:
            List of ranking entries or None if failed
        """
        endpoint = "RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
        params: Dict[str, Any] = {"IttfId": ittf_id, "q": 1}

        data = self._request_with_retry(endpoint, params=params)

        if data and "Result" in data:
            return data["Result"]

        return None

    def test_ittf_id(self, ittf_id: str) -> tuple[bool, Optional[str]]:
        """
        Test if an ITTF ID exists by checking rankings API.

        Args:
            ittf_id: ITTF ID to test

        Returns:
            Tuple of (is_valid, player_name)
        """
        rankings = self.get_player_rankings(ittf_id)

        if rankings and len(rankings) > 0:
            player_name = rankings[0].get("PlayerName", "Unknown")
            return True, player_name

        return False, None

    def batch_fetch_rankings(
        self, ittf_ids: List[str], delay: Optional[float] = None
    ) -> Dict[str, Optional[List[Dict]]]:
        """
        Fetch rankings for multiple players with rate limiting.

        Args:
            ittf_ids: List of ITTF IDs
            delay: Delay between requests (defaults to config.rate_limit_delay)

        Returns:
            Dictionary mapping ITTF ID to rankings
        """
        if delay is None:
            delay = self.config.rate_limit_delay

        results: Dict[str, Optional[List[Dict]]] = {}
        total = len(ittf_ids)

        for i, ittf_id in enumerate(ittf_ids, 1):
            logger.info(f"Fetching {ittf_id} ({i}/{total})...")

            try:
                rankings = self.get_player_rankings(ittf_id)
                results[ittf_id] = rankings

                if rankings:
                    player_name = rankings[0].get("PlayerName", "Unknown")
                    logger.info(f"  ✓ Found: {player_name}")

                # Rate limiting
                if i < total:
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                results[ittf_id] = None

        return results

    def discover_player_ids_brute_force(
        self, start: int, end: int, delay: float = 0.5
    ) -> List[Dict]:
        """
        Discover valid ITTF IDs by brute force testing a range.

        Args:
            start: Starting ITTF ID
            end: Ending ITTF ID
            delay: Delay between requests

        Returns:
            List of discovered players
        """
        logger.info(f"Starting brute force discovery: {start}-{end}")
        discovered = []

        for ittf_id in range(start, end + 1):
            valid, name = self.test_ittf_id(str(ittf_id))

            if valid:
                discovered.append(
                    {"IttfId": str(ittf_id), "name": name, "source": "API_brute_force"}
                )
                logger.info(f"✓ Found: {name} (ID: {ittf_id})")

            # Rate limiting
            time.sleep(delay)

        return discovered


class WTTHTMLScraper:
    """
    HTML-based scraper for results.ittf.link and other sources.

    Falls back to HTML parsing when APIs are unavailable.
    """

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None


class WTTRankingScraper(WTTRestScraper):
    """Specialized scraper for rankings data."""

    def save_rankings(
        self, data: Dict[str, Optional[List[Dict]]], filename: Optional[str] = None
    ) -> Path:
        """Save rankings data to JSON file."""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"rankings_{timestamp}.json"

        output_file = self.config.output_dir / "rankings" / filename

        metadata = {
            "scraped_at": datetime.utcnow().isoformat() + "Z",
            "total_players": len(data),
            "successful": sum(1 for v in data.values() if v is not None),
            "failed": sum(1 for v in data.values() if v is None),
            "rankings": data,
        }

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved rankings to {output_file}")
        return output_file

    def get_all_rankings(
        self, ittf_ids: List[str], delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Fetch rankings for all players and generate summary statistics.

        Args:
            ittf_ids: List of ITTF IDs
            delay: Delay between requests

        Returns:
            Complete rankings data with statistics
        """
        rankings_data = self.batch_fetch_rankings(ittf_ids, delay)

        # Analyze rankings
        event_types: Dict[str, int] = {}
        all_entries: List[Dict] = []

        for ittf_id, rankings in rankings_data.items():
            if rankings:
                for entry in rankings:
                    event_code = entry.get("SubEventCode", "Unknown")
                    event_types[event_code] = event_types.get(event_code, 0) + 1
                    all_entries.append(entry)

        stats = {
            "total_players": len(ittf_ids),
            "players_with_rankings": sum(
                1 for v in rankings_data.values() if v is not None
            ),
            "total_ranking_entries": len(all_entries),
            "event_types": event_types,
            "scraped_at": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(f"Rankings summary:")
        logger.info(
            f"  Players with rankings: {stats['players_with_rankings']}/{stats['total_players']}"
        )
        logger.info(f"  Total ranking entries: {stats['total_ranking_entries']}")
        logger.info(f"  Event types: {list(event_types.keys())}")

        return {"metadata": stats, "rankings": rankings_data}


class WTTCli:
    """Command-line interface for scraper."""

    @staticmethod
    def print_banner():
        """Print welcome banner."""
        print("=" * 60)
        print("ITTF/WTT Data Scraper v1.0")
        print("Agent 4 - ITTF/WTT API Discovery & Implementation")
        print("=" * 60)
        print()

    @staticmethod
    def scrape_single_player(ittf_id: str, config: ScraperConfig):
        """Scrape rankings for a single player."""
        scraper = WTTRankingScraper(config)
        rankings = scraper.get_player_rankings(ittf_id)

        if rankings:
            print(f"\nRankings for ITTF ID {ittf_id}:")
            print(json.dumps(rankings, indent=2))
        else:
            print(f"\nNo rankings found for ITTF ID {ittf_id}")

    @staticmethod
    def scrape_multiple_players(ittf_ids: List[str], config: ScraperConfig):
        """Scrape rankings for multiple players."""
        scraper = WTTRankingScraper(config)
        data = scraper.batch_fetch_rankings(ittf_ids, delay=1.0)
        scraper.save_rankings(data)

        print(f"\nScraped {len(data)} players")
        print(f"Successful: {sum(1 for v in data.values() if v is not None)}")
        print(f"Failed: {sum(1 for v in data.values() if v is None)}")

    @staticmethod
    def discover_ids(start: int, end: int, config: ScraperConfig):
        """Discover player IDs via brute force."""
        scraper = WTTRankingScraper(config)
        players = scraper.discover_player_ids_brute_force(start, end)

        output_file = config.output_dir / "players" / "discovered_players.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(
                {
                    "players": players,
                    "total_found": len(players),
                    "range_tested": f"{start}-{end}",
                    "discovered_at": datetime.utcnow().isoformat() + "Z",
                },
                f,
                indent=2,
            )

        print(f"\nDiscovered {len(players)} players")
        print(f"Saved to {output_file}")


def main():
    """Main entry point."""
    WTTCli.print_banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python wtt_ittf_scraper.py --player <ITTF_ID>")
        print("  python wtt_ittf_scraper.py --batch <ID1,ID2,ID3>")
        print("  python wtt_ittf_scraper.py --discover <START_ID> <END_ID>")
        print()
        print("Examples:")
        print("  python wtt_ittf_scraper.py --player 121558")
        print("  python wtt_ittf_scraper.py --batch 121558,101919,105649")
        print("  python wtt_ittf_scraper.py --discover 110000 111000")
        sys.exit(1)

    config = ScraperConfig()

    if sys.argv[1] == "--player" and len(sys.argv) == 3:
        WTTCli.scrape_single_player(sys.argv[2], config)

    elif sys.argv[1] == "--batch" and len(sys.argv) == 3:
        ittf_ids = sys.argv[2].split(",")
        WTTCli.scrape_multiple_players(ittf_ids, config)

    elif sys.argv[1] == "--discover" and len(sys.argv) == 4:
        start = int(sys.argv[2])
        end = int(sys.argv[3])
        WTTCli.discover_ids(start, end, config)

    else:
        print("Invalid arguments. See --help for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
