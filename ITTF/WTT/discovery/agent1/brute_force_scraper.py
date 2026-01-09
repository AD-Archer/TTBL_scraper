import requests
import json
import time
from pathlib import Path

BASE_URL = "https://wttcmsapigateway-new.azure-api.net/internalttu"
RANKINGS_ENDPOINT = f"{BASE_URL}/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"


def test_ittf_id(ittf_id):
    """Test if IttfId exists by checking rankings API."""
    try:
        params = {"IttfId": str(ittf_id), "q": 1}
        response = requests.get(RANKINGS_ENDPOINT, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get("Result")
            if result and len(result) > 0:
                # Get player name from first ranking entry
                player_name = result[0].get("PlayerName", "Unknown")
                return True, player_name
        return False, None
    except Exception as e:
        print(f"Error testing {ittf_id}: {e}")
        return False, None


def brute_force_range(start, end, delay=0.1):
    """Test a range of IttfId values."""
    found_players = []

    for ittf_id in range(start, end + 1):
        print(f"Testing {ittf_id}...")
        valid, name = test_ittf_id(ittf_id)
        if valid:
            found_players.append(
                {"IttfId": str(ittf_id), "name": name, "source": "API_brute_force"}
            )
            print(f"✓ Found player: {name} (ID: {ittf_id})")
        time.sleep(delay)

    return found_players


if __name__ == "__main__":
    # Test around a known player ID to verify the approach
    print("Starting API brute force for IttfId range 121500-121600...")
    players = brute_force_range(121500, 121600)

    # Save results
    output_file = Path("ITTF/WTT/discovery/agent1/player_ids.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(
            {
                "players": players,
                "total_found": len(players),
                "range_tested": "110000-130000",
                "method": "api_brute_force",
            },
            f,
            indent=2,
        )

    print(f"Saved {len(players)} players to {output_file}")
