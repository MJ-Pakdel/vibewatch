#!/usr/bin/env python3
"""
Fetch full Hulu & Disney+ catalogs (US) from TMDB and save to CSV.

Usage:
    python get_tmdb_catalog.py --out catalog.csv

Requirements:
    pip install requests pandas tqdm tenacity pyyaml
"""

import os
import json
import time
import argparse
from typing import Dict, Any, Iterable, List
import requests
import pandas as pd
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE = "https://api.themoviedb.org/3"

# TMDB provider IDs (US)
PROVIDERS = {
    "Disney+": 337,
    "Hulu": 15,
}

APPEND_TO_RESPONSE = ",".join([
    "external_ids",
    "watch/providers",
    "keywords",
    "credits",
    "release_dates",       # movie only
    "content_ratings",     # tv only
    "videos",
    "images",
    "translations",
])

# --- HTTP Helpers ------------------------------------------------------------

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def tmdb_get(path: str, **params) -> Dict[str, Any]:
    """GET wrapper with retry/backoff."""
    if TMDB_API_KEY is None:
        raise RuntimeError("TMDB_API_KEY not set in env vars.")
    params["api_key"] = TMDB_API_KEY
    r = requests.get(f"{BASE}{path}", params=params, timeout=30)
    if r.status_code == 429:
        # Rate limited—sleep a bit and retry
        reset = int(r.headers.get("Retry-After", 2))
        time.sleep(reset)
        raise RuntimeError("Rate limited, retrying...")
    r.raise_for_status()
    return r.json()

def discover_ids(media_type: str, provider_id: int, region: str = "US") -> List[int]:
    """
    Page through /discover/{movie|tv} to get all TMDB IDs for a provider in a region.
    """
    ids = []
    page = 1
    total_pages = None
    pbar = tqdm(desc=f"Discover {media_type} ({provider_id})", unit="page")
    while True:
        data = tmdb_get(
            f"/discover/{media_type}",
            with_watch_providers=str(provider_id),
            watch_region=region,
            include_adult="false",
            language="en-US",
            sort_by="popularity.desc",
            page=page,
        )
        if total_pages is None:
            total_pages = data.get("total_pages", 1)
            pbar.total = total_pages
        results = data.get("results", [])
        ids.extend([item["id"] for item in results])
        pbar.update(1)
        if page >= total_pages:
            break
        page += 1
        # gentle throttle to avoid 429
        time.sleep(0.2)
    pbar.close()
    return ids

def chunked(iterable: Iterable[Any], size: int) -> Iterable[List[Any]]:
    """Yield lists of length 'size' from iterable."""
    buf = []
    for item in iterable:
        buf.append(item)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf

def fetch_details(media_type: str, tmdb_id: int) -> Dict[str, Any]:
    """
    Fetch detail object + append_to_response fields.
    Handles missing endpoints gracefully.
    """
    detail = tmdb_get(
        f"/{media_type}/{tmdb_id}",
        append_to_response=APPEND_TO_RESPONSE
    )
    detail["_media_type"] = media_type
    return detail

def flatten_record(
    d: Dict[str, Any],
    service: str,
) -> Dict[str, Any]:
    """
    Flatten nested TMDB dict into a single-row dict.
    - Keep most scalar fields
    - Dump lists/dicts as JSON strings
    """
    row = {
        "service": service,
        "media_type": d.get("_media_type"),
        "tmdb_id": d.get("id"),
    }

    # Simple scalar fields
    scalar_keys = [
        "title",
        "name",
        "original_title",
        "original_name",
        "overview",
        "tagline",
        "status",
        "release_date",
        "first_air_date",
        "last_air_date",
        "runtime",
        "episode_run_time",
        "number_of_seasons",
        "number_of_episodes",
        "in_production",
        "original_language",
        "homepage",
        "popularity",
        "vote_average",
        "vote_count",
        "budget",
        "revenue",
    ]
    for k in scalar_keys:
        row[k] = d.get(k)

    # Genres as list
    row["genres"] = json.dumps(d.get("genres", []), ensure_ascii=False)

    # Spoken languages, production companies, countries
    for k in [
        "spoken_languages",
        "production_companies",
        "production_countries",
        "origin_country",
        "languages",
    ]:
        row[k] = json.dumps(d.get(k, []), ensure_ascii=False)

    # External IDs (imdb_id, tvdb_id, etc.)
    row["external_ids"] = json.dumps(d.get("external_ids", {}), ensure_ascii=False)

    # Keywords
    kw = d.get("keywords", {})
    # TV sends {"results": [...]} ; Movie sends {"keywords": [...]}
    kw_list = kw.get("results") if "results" in kw else kw.get("keywords")
    row["keywords"] = json.dumps(kw_list if kw_list is not None else kw, ensure_ascii=False)

    # Watch providers (all regions)
    row["watch_providers"] = json.dumps(d.get("watch/providers", {}), ensure_ascii=False)

    # Credits
    row["credits"] = json.dumps(d.get("credits", {}), ensure_ascii=False)

    # Videos, images, translations
    for k in ["videos", "images", "translations"]:
        row[k] = json.dumps(d.get(k, {}), ensure_ascii=False)

    # Ratings
    row["release_dates"] = json.dumps(d.get("release_dates", {}), ensure_ascii=False)
    row["content_ratings"] = json.dumps(d.get("content_ratings", {}), ensure_ascii=False)

    return row

# --- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="hulu_disneyplus_us.csv", help="CSV output path")
    parser.add_argument("--region", default="US")
    parser.add_argument("--sleep", type=float, default=0.15, help="sleep between detail calls")
    parser.add_argument("--chunk", type=int, default=50, help="flush to CSV every N records")
    args = parser.parse_args()

    if TMDB_API_KEY is None:
        raise SystemExit("Please set TMDB_API_KEY env var.")

    rows = []
    total_written = 0

    for service, provider_id in PROVIDERS.items():
        for media_type in ["movie", "tv"]:
            ids = discover_ids(media_type, provider_id, args.region)
            for tmdb_id in tqdm(ids, desc=f"Fetch {media_type} details for {service}", unit="title"):
                try:
                    detail = fetch_details(media_type, tmdb_id)
                    row = flatten_record(detail, service)
                    rows.append(row)
                except Exception as e:
                    print(f"Error on {media_type} {tmdb_id}: {e}")
                time.sleep(args.sleep)

                # Periodically flush to disk
                if len(rows) >= args.chunk:
                    df = pd.DataFrame(rows)
                    mode = "a" if total_written > 0 else "w"
                    header = total_written == 0
                    df.to_csv(args.out, index=False, mode=mode, header=header)
                    total_written += len(rows)
                    rows.clear()

    # Final flush
    if rows:
        df = pd.DataFrame(rows)
        mode = "a" if total_written > 0 else "w"
        header = total_written == 0
        df.to_csv(args.out, index=False, mode=mode, header=header)
        total_written += len(rows)
        rows.clear()

    print(f"Done. Wrote {total_written} rows to {args.out}")

if __name__ == "__main__":
    main() 