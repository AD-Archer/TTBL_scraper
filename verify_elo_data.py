#!/usr/bin/env python3

import json
import os
from datetime import datetime
from pathlib import Path


def verify_elo_data():
    data_dir = Path("ttbl_data")
    games_file = data_dir / "stats" / "games_data.json"

    if not games_file.exists():
        print(f"ERROR: {games_file} not found!")
        return False

    with open(games_file) as f:
        games = json.load(f)

    print()
    print("9. Valid games for ELO calculation:")
    valid_elo_games = [
        g
        for g in games
        if g["gameState"] == "Finished"
        and g.get("winnerSide") is not None
        and g["homePlayer"].get("name") != "Unknown"
        and g["awayPlayer"].get("name") != "Unknown"
    ]
    print(f"   - Valid for ELO: {len(valid_elo_games)}")
    print(f"   - Total in dataset: {len(games)}")
    print(
        f"   - Excluded (inactive/unknown/winner-null): {len(games) - len(valid_elo_games)}"
    )
    print()

    print("=" * 64)
    if len(valid_elo_games) > 0:
        print("STATUS: ELO data is ready!")
        print(f"   {len(valid_elo_games)} valid games available for calculation")
    else:
        print("STATUS: No valid games for ELO!")
    print("=" * 64)
    return True


if __name__ == "__main__":
    verify_elo_data()
