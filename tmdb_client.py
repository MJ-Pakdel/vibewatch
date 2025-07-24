# TMDB client helper to fetch poster URLs.

import os
import requests
from typing import Optional

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
# Base URL for TMDB poster images – see https://developer.themoviedb.org/reference/configuration-details
POSTER_BASE = "https://image.tmdb.org/t/p/w342"


def fetch_poster_url(title: str) -> Optional[str]:
    """Return a poster image URL for a movie title via TMDB search API.

    If the TMDB_API_KEY env var is missing or no poster is found,
    returns None so the caller can fall back to a placeholder.
    """
    if not TMDB_API_KEY:
        return None

    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": title,
                "include_adult": "false",
                "language": "en-US",
            },
            timeout=5,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results")
        if not results:
            return None
        poster_path = results[0].get("poster_path")
        if poster_path:
            return f"{POSTER_BASE}{poster_path}"
    except requests.RequestException:
        pass
    return None 