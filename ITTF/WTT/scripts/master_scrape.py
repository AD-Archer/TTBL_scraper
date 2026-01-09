#!/usr/bin/env python3
"""ITTF/WTT Master Scraper

Goal
----
Produce a single consolidated dataset focused on *as much match/player data as is publicly accessible*.

Current public sources in this repo:
- results.ittf.link Fabrik JSON (match listid=31) -> match results + player IDs + names + associations

Non-goals (for now)
-------------------
- Rankings as an output artifact (we may still use ranking pages later only if needed for enrichment)

Limitations
-----------
- Date of birth and "team" are typically not present in public Fabrik match rows.
  This script records those fields as null unless future public sources are added.

Outputs
-------
Writes JSON under ITTF/WTT/artifacts/data/master/:
- players.json (normalized players keyed by ittf_id)
- matches.json (normalized match list)
- dataset.json (combined)

Usage
-----
python3 ITTF/WTT/scripts/master_scrape.py --years 2025,2024,2023
python3 ITTF/WTT/scripts/master_scrape.py --start-year 2020 --end-year 2025
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


try:
    import requests
except ImportError:
    raise SystemExit("requests not installed; run: pip install requests")


LOG = logging.getLogger("wtt_master")

WTT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = WTT_ROOT / "artifacts" / "data" / "master"

FABRIK_BASE_URL = "https://results.ittf.link/index.php"
DEFAULT_LIST_ID = "31"  # Player matches (Agent 3 discovery)


@dataclass(frozen=True)
class FabrikConfig:
    list_id: str = DEFAULT_LIST_ID
    timeout: int = 30
    rate_limit_delay: float = 0.4
    page_size: int = 500
    max_pages_per_year: int = 500
    user_agent: str = "ITTF-WTT-MasterScraper/1.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_years_arg(years_csv: str) -> List[int]:
    years: List[int] = []
    for part in years_csv.split(","):
        part = part.strip()
        if not part:
            continue
        years.append(int(part))
    return sorted(set(years), reverse=True)


def normalize_name(full_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (first_name, last_name, full_name).

    Heuristic only. Many ITTF names are formatted as: LASTNAME Firstname.
    """

    full_name = (full_name or "").strip()
    if not full_name:
        return None, None, None

    parts = [p for p in full_name.split() if p]
    if len(parts) == 1:
        return None, parts[0], full_name

    # Prefer token(s) that are ALL CAPS as last name
    caps = [p for p in parts if p.isupper() and any(c.isalpha() for c in p)]
    if caps:
        last = caps[0]
        first_parts = [p for p in parts if p != last]
        first = " ".join(first_parts) if first_parts else None
        return first or None, last or None, full_name

    # Fallback: last token is last name
    return " ".join(parts[:-1]) or None, parts[-1] or None, full_name


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(str(value))
    except Exception:
        return None


def parse_games(games_raw: str) -> List[Dict[str, Any]]:
    games_raw = (games_raw or "").strip()
    if not games_raw:
        return []

    games: List[Dict[str, Any]] = []
    for idx, token in enumerate(games_raw.split(), 1):
        if ":" not in token:
            continue
        left, right = token.split(":", 1)
        a = safe_int(left.strip())
        b = safe_int(right.strip())
        if a is None or b is None:
            continue
        games.append({"game_number": idx, "a_points": a, "x_points": b})
    return games


def compute_set_score(games: List[Dict[str, Any]]) -> Tuple[int, int]:
    a_sets = 0
    x_sets = 0
    for g in games:
        a = safe_int(g.get("a_points"))
        x = safe_int(g.get("x_points"))
        if a is None or x is None:
            continue
        if a > x:
            a_sets += 1
        elif x > a:
            x_sets += 1
    return a_sets, x_sets


def fabrik_params(list_id: str, year: int, limit: int, offset: int) -> Dict[str, Any]:
    """Build Fabrik list query params.

    Fabrik pagination commonly uses limitstart<listid>.
    If pagination is unsupported, we still de-duplicate by match id and stop on no-new results.
    """

    params: Dict[str, Any] = {
        "option": "com_fabrik",
        "view": "list",
        "listid": list_id,
        "format": "json",
        "vw_matches___yr[value]": year,
        "limit": limit,
    }

    # Empirically many Fabrik list views use this pattern
    params[f"limitstart{list_id}"] = offset
    return params


def fetch_fabrik_page(session: requests.Session, cfg: FabrikConfig, year: int, offset: int) -> List[Dict[str, Any]]:
    params = fabrik_params(cfg.list_id, year=year, limit=cfg.page_size, offset=offset)
    resp = session.get(FABRIK_BASE_URL, params=params, timeout=cfg.timeout)
    resp.raise_for_status()

    data = resp.json()
    if isinstance(data, list) and data:
        # sometimes API returns [[...]]
        if len(data) == 1 and isinstance(data[0], list):
            return data[0]
        return data
    return []


def iter_fabrik_matches(session: requests.Session, cfg: FabrikConfig, year: int) -> Iterable[Dict[str, Any]]:
    """Iterate match rows for a year with best-effort pagination + de-dupe."""

    seen_ids: Set[str] = set()
    offset = 0
    stagnant_pages = 0

    for page in range(cfg.max_pages_per_year):
        rows = fetch_fabrik_page(session, cfg, year=year, offset=offset)
        if not rows:
            return

        new_count = 0
        for row in rows:
            match_id = str(row.get("vw_matches___id", "")).strip()
            if not match_id:
                continue
            if match_id in seen_ids:
                continue
            seen_ids.add(match_id)
            new_count += 1
            yield row

        if new_count == 0:
            stagnant_pages += 1
        else:
            stagnant_pages = 0

        # Stop if pagination isn't working (we keep getting the same page)
        if stagnant_pages >= 2:
            LOG.info("Year %s: pagination appears stagnant; stopping after %s pages", year, page + 1)
            return

        offset += cfg.page_size
        time.sleep(cfg.rate_limit_delay)


def row_to_match(row: Dict[str, Any]) -> Dict[str, Any]:
    match_id = str(row.get("vw_matches___id", "")).strip()

    a_id = str(row.get("vw_matches___player_a_id", "")).strip() or None
    x_id_raw = row.get("vw_matches___player_x_id")
    x_id = str(x_id_raw).strip() if x_id_raw else None

    a_name = (row.get("vw_matches___name_a") or "").strip()
    x_name = (row.get("vw_matches___name_x") or "").strip()

    a_assoc = (row.get("vw_matches___assoc_a") or "").strip() or None
    x_assoc = (row.get("vw_matches___assoc_x") or "").strip() or None

    games = parse_games(row.get("vw_matches___games_raw") or "")
    a_sets, x_sets = compute_set_score(games)

    walkover = bool(row.get("vw_matches___wo", 0))

    winner_raw = row.get("vw_matches___winner")
    # winner is often 1/2 or similar; we also infer from sets if possible
    winner_id = safe_int(winner_raw)

    inferred_winner: Optional[str] = None
    if a_sets != x_sets and (a_id or x_id):
        inferred_winner = "A" if a_sets > x_sets else "X"

    year = str(row.get("vw_matches___yr_raw") or row.get("vw_matches___yr") or "").strip() or None

    return {
        "match_id": match_id,
        "year": year,
        "tournament": row.get("vw_matches___tournament_id"),
        "event": row.get("vw_matches___event"),
        "stage": row.get("vw_matches___stage"),
        "round": row.get("vw_matches___round"),
        "walkover": walkover,
        "winner_raw": winner_id,
        "winner_inferred": inferred_winner,
        "final_sets": {"a": a_sets, "x": x_sets},
        "games": games,
        "players": {
            "a": {"ittf_id": a_id, "name": a_name or None, "association": a_assoc},
            "x": {"ittf_id": x_id, "name": x_name or None, "association": x_assoc},
        },
        "source": {
            "type": "fabrik_list",
            "base_url": FABRIK_BASE_URL,
            "list_id": DEFAULT_LIST_ID,
        },
    }


def upsert_player(players: Dict[str, Dict[str, Any]], ittf_id: Optional[str], name: Optional[str], association: Optional[str]) -> None:
    if not ittf_id:
        return

    record = players.get(ittf_id)
    if record is None:
        first, last, full = normalize_name(name or "")
        record = {
            "ittf_id": ittf_id,
            "first_name": first,
            "last_name": last,
            "full_name": full,
            "dob": None,
            "nationality": association,
            "team": None,
            "stats": {"matches_played": 0, "wins": 0, "losses": 0},
            "sources": set(),
            "last_seen": utc_now_iso(),
        }
        players[ittf_id] = record

    # Update best-known values
    if association and not record.get("nationality"):
        record["nationality"] = association

    if name and not record.get("full_name"):
        first, last, full = normalize_name(name)
        record["first_name"] = first
        record["last_name"] = last
        record["full_name"] = full

    record["last_seen"] = utc_now_iso()
    record.setdefault("sources", set()).add("fabrik_matches")


def serialize_players(players: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    # Convert sources from set -> sorted list
    out: Dict[str, Any] = {}
    for pid, rec in players.items():
        out[pid] = {
            **{k: v for k, v in rec.items() if k != "sources"},
            "sources": sorted(list(rec.get("sources") or [])),
        }
    return out


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="ITTF/WTT master match+player scraper")
    parser.add_argument("--years", type=str, help="Comma-separated years (e.g. 2025,2024)")
    parser.add_argument("--start-year", type=int, help="Start year (inclusive)")
    parser.add_argument("--end-year", type=int, help="End year (inclusive)")
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--sleep", type=float, default=0.4, help="Delay between page requests")
    parser.add_argument("--out-dir", type=str, default=str(OUTPUT_ROOT))
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.years:
        years = parse_years_arg(args.years)
    else:
        now_year = datetime.now(timezone.utc).year
        start = args.start_year if args.start_year is not None else now_year
        end = args.end_year if args.end_year is not None else now_year
        if start < end:
            start, end = end, start
        years = list(range(start, end - 1, -1))

    out_dir = Path(args.out_dir)

    cfg = FabrikConfig(
        page_size=args.page_size,
        max_pages_per_year=args.max_pages,
        rate_limit_delay=args.sleep,
    )

    session = requests.Session()
    session.headers.update({"User-Agent": cfg.user_agent})

    players: Dict[str, Dict[str, Any]] = {}
    matches: List[Dict[str, Any]] = []
    player_match_index: Dict[str, List[str]] = {}

    for year in years:
        LOG.info("Scraping year=%s from Fabrik listid=%s", year, cfg.list_id)
        count = 0
        for row in iter_fabrik_matches(session, cfg, year=year):
            match = row_to_match(row)
            matches.append(match)

            match_id = match.get("match_id")

            a = match["players"]["a"]
            x = match["players"]["x"]
            upsert_player(players, a.get("ittf_id"), a.get("name"), a.get("association"))
            upsert_player(players, x.get("ittf_id"), x.get("name"), x.get("association"))

            a_id = a.get("ittf_id")
            x_id = x.get("ittf_id")
            if match_id:
                if a_id:
                    player_match_index.setdefault(a_id, []).append(match_id)
                    players[a_id]["stats"]["matches_played"] += 1
                if x_id:
                    player_match_index.setdefault(x_id, []).append(match_id)
                    players[x_id]["stats"]["matches_played"] += 1

                winner = match.get("winner_inferred")
                if winner == "A" and a_id and x_id:
                    players[a_id]["stats"]["wins"] += 1
                    players[x_id]["stats"]["losses"] += 1
                elif winner == "X" and a_id and x_id:
                    players[x_id]["stats"]["wins"] += 1
                    players[a_id]["stats"]["losses"] += 1

            count += 1
            if count % 500 == 0:
                LOG.info("Year %s: collected %s matches so far", year, count)

        LOG.info("Year %s: collected %s matches", year, count)

    dataset = {
        "metadata": {
            "scraped_at": utc_now_iso(),
            "years": years,
            "players": len(players),
            "matches": len(matches),
            "sources": [
                {
                    "type": "fabrik_list",
                    "base_url": FABRIK_BASE_URL,
                    "list_id": cfg.list_id,
                }
            ],
            "notes": [
                "DOB/team generally unavailable from public Fabrik match rows; fields left null.",
                "Winner inferred from per-game points where possible.",
            ],
        },
        "players": serialize_players(players),
        "matches": matches,
        "player_match_index": player_match_index,
    }

    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "players.json", dataset["players"])
    write_json(out_dir / "matches.json", dataset["matches"])
    write_json(out_dir / "player_match_index.json", dataset["player_match_index"])
    write_json(out_dir / "dataset.json", dataset)

    LOG.info("Wrote: %s", out_dir / "dataset.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
