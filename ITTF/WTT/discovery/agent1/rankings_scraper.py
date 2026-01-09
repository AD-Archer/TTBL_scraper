import requests
import json
import re
from pathlib import Path


def extract_player_ids_from_page(url):
    """Extract all player_id_raw values from a rankings page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Find all player_id_raw=NUMBER patterns
        pattern = r"player_id_raw=(\d+)"
        matches = re.findall(pattern, response.text)

        # Convert to unique sorted list
        player_ids = sorted(list(set(matches)))

        return player_ids
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def scrape_all_rankings():
    """Scrape player IDs from all ITTF rankings pages."""

    rankings_pages = [
        "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-men-singles",
        "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-women-singles",
        "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-boys-singles",
        "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-girls-singles",
        "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-boys-singles-2",  # Check if there's a second page
        "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-girls-singles-2",
    ]

    all_player_ids = set()

    for url in rankings_pages:
        print(f"Scraping {url}...")
        ids = extract_player_ids_from_page(url)
        print(f"Found {len(ids)} player IDs")
        all_player_ids.update(ids)

    # Convert to sorted list
    unique_ids = sorted(list(all_player_ids))

    # Also check the main page for any additional IDs
    print("Scraping main page...")
    main_page_ids = extract_player_ids_from_page("https://results.ittf.link/")
    all_player_ids.update(main_page_ids)

    unique_ids = sorted(list(all_player_ids))

    return unique_ids


def validate_player_ids(player_ids):
    """Validate player IDs by checking the API (sample only, not all)."""
    BASE_URL = "https://wttcmsapigateway-new.azure-api.net/internalttu"
    RANKINGS_ENDPOINT = (
        f"{BASE_URL}/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
    )

    validated_players = []

    # Only validate first 10 for speed
    sample_ids = player_ids[:10]

    for ittf_id in sample_ids:
        try:
            params = {"IttfId": ittf_id, "q": 1}
            response = requests.get(RANKINGS_ENDPOINT, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data.get("Result", [])
                if result:
                    player_name = result[0].get("PlayerName", "Unknown")
                    validated_players.append(
                        {
                            "IttfId": ittf_id,
                            "name": player_name,
                            "source": "rankings_page",
                            "verified": True,
                        }
                    )
                else:
                    validated_players.append(
                        {
                            "IttfId": ittf_id,
                            "name": "Unknown",
                            "source": "rankings_page",
                            "verified": False,
                        }
                    )
        except Exception as e:
            print(f"Error validating {ittf_id}: {e}")
            validated_players.append(
                {
                    "IttfId": ittf_id,
                    "name": "Unknown",
                    "source": "rankings_page",
                    "verified": False,
                }
            )

    return validated_players


if __name__ == "__main__":
    print("Starting player ID discovery from ITTF rankings pages...")

    # Scrape all rankings pages
    all_ids = scrape_all_rankings()
    print(f"Total unique player IDs found: {len(all_ids)}")

    # Validate a sample
    print("Validating sample of player IDs...")
    validated_sample = validate_player_ids(all_ids)

    # Save results
    output_file = Path("player_ids.json")

    result = {
        "players": [{"IttfId": pid, "source": "rankings_page"} for pid in all_ids],
        "discovery_methods": {
            "men_singles_rankings": len(
                extract_player_ids_from_page(
                    "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-men-singles"
                )
            ),
            "women_singles_rankings": len(
                extract_player_ids_from_page(
                    "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-women-singles"
                )
            ),
            "boys_singles_rankings": len(
                extract_player_ids_from_page(
                    "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-boys-singles"
                )
            ),
            "girls_singles_rankings": len(
                extract_player_ids_from_page(
                    "https://results.ittf.link/index.php/ittf-rankings/ittf-ranking-girls-singles"
                )
            ),
            "main_page": len(
                extract_player_ids_from_page("https://results.ittf.link/")
            ),
        },
        "total_unique_ids": len(all_ids),
        "sample_validated": validated_sample,
    }

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Saved {len(all_ids)} player IDs to {output_file}")
