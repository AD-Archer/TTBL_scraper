#!/usr/bin/env python3
"""
Complete ITTF/WTT Player Database Scraper
Scrapes ALL rankings pages to get every single player
"""

import requests
import json
import time
from typing import List, Dict, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


WTT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = WTT_ROOT / "artifacts" / "data"


class CompletePlayerScraper:
    """Scrape all players from ITTF rankings pages"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://results.ittf.link/index.php/ittf-rankings"
        self.all_player_ids: Set[str] = set()

        # Rankings categories to scrape with their list IDs
        self.categories = {
            "ittf-ranking-men-singles": "57",  # 1141 players
            "ittf-ranking-women-singles": "58",  # 918 players
            "ittf-ranking-boys-singles": "63",  # 2704 players
            "ittf-ranking-girls-singles": "64",  # 1994 players
        }

    def scrape_ranking_page(
        self, category: str, list_id: str, limitstart: int
    ) -> List[str]:
        """Scrape a single ranking page for player IDs"""
        url = f"{self.base_url}/{category}/list/{list_id}?limitstart{list_id}={limitstart}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Extract player IDs
            import re

            pattern = r"player_id_raw=(\d+)"
            matches = re.findall(pattern, response.text)

            print(f"Offset {limitstart} ({category}): {len(matches)} players")
            return matches

        except Exception as e:
            print(f"Error scraping {category} offset {limitstart}: {e}")
            return []

    def find_max_pages(self, category: str) -> int:
        """Find the maximum number of pages for a category"""
        # Start with a high number and work backwards to find the last valid page
        max_attempts = 100  # Safety limit

        for page in range(100, 0, -1):
            try:
                url = f"{self.base_url}/{category}/list/{page}"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    # Check if page has players
                    import re

                    if re.search(r"player_id_raw=\d+", response.text):
                        return page

            except Exception:
                continue

            time.sleep(0.1)  # Small delay

        return 1  # Fallback

    def scrape_category(self, category: str, list_id: str) -> Set[str]:
        """Scrape all pages for a category"""
        print(f"\n=== Scraping {category} (List ID: {list_id}) ===")

        category_ids = set()

        # Start with offset 0, then 50, 100, 150, etc.
        offset = 0
        page_size = 50  # Based on what I saw

        while True:
            page_ids = self.scrape_ranking_page(category, list_id, offset)
            if not page_ids:
                # No more players
                break

            category_ids.update(page_ids)
            print(f"Total so far: {len(category_ids)} unique players")

            offset += page_size
            time.sleep(0.2)  # Rate limiting

            # Safety: stop if we get too many pages (unlimited players for now)
            if offset > 10000:  # Max ~200 pages
                break

        print(f"Completed {category}: {len(category_ids)} unique players")
        return category_ids

    def scrape_all_rankings(self) -> Dict[str, Set[str]]:
        """Scrape all rankings categories"""
        print("Starting comprehensive player ID collection...")

        results = {}

        for category, list_id in self.categories.items():
            category_ids = self.scrape_category(category, list_id)
            results[category] = category_ids
            self.all_player_ids.update(category_ids)

        return results

    def save_player_database(self, results: Dict[str, Set[str]]):
        """Save the complete player database"""
        output_dir = DEFAULT_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        # Categorize by gender
        men_ids = set()
        women_ids = set()

        # Men's categories
        men_ids.update(results.get("ittf-ranking-men-singles", set()))
        men_ids.update(results.get("ittf-ranking-boys-singles", set()))

        # Women's categories
        women_ids.update(results.get("ittf-ranking-women-singles", set()))
        women_ids.update(results.get("ittf-ranking-girls-singles", set()))

        # Create player records
        players_data = {
            "metadata": {
                "scraped_at": "2026-01-09",
                "source": "ittf_rankings_pages",
                "categories_scraped": self.categories,
                "total_unique_players": len(self.all_player_ids),
                "men_players": len(men_ids),
                "women_players": len(women_ids),
                "notes": "Complete player database from all ITTF rankings pages",
            },
            "players": {
                "all_ids": sorted(list(self.all_player_ids)),
                "men_ids": sorted(list(men_ids)),
                "women_ids": sorted(list(women_ids)),
            },
        }

        output_file = output_dir / "complete_player_database.json"
        with open(output_file, "w") as f:
            json.dump(players_data, f, indent=2)

        print(f"✅ Saved complete player database: {len(self.all_player_ids)} players")
        print(f"   - Men: {len(men_ids)}")
        print(f"   - Women: {len(women_ids)}")
        print(f"   - File: {output_file}")

        return players_data


def main():
    scraper = CompletePlayerScraper()
    results = scraper.scrape_all_rankings()
    scraper.save_player_database(results)


if __name__ == "__main__":
    main()
