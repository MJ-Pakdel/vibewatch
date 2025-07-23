import zipfile
import io
import requests
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MOVIES_CSV = DATA_DIR / "movies_clean.csv"

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"


def download_movielens() -> bytes:
    """Download the MovieLens latest-small zip and return bytes content."""
    print("Downloading MovieLens dataset ...")
    r = requests.get(MOVIELENS_URL, timeout=60)
    r.raise_for_status()
    print("Download complete.")
    return r.content


def prepare_movies_df(zip_bytes: bytes) -> pd.DataFrame:
    """Extract movies.csv from zip bytes and return cleaned DataFrame."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open("ml-latest-small/movies.csv") as f:
            df = pd.read_csv(f)

    # Clean title (remove year if present)
    df["title"] = df["title"].str.replace(r" \(\d{4}\)$", "", regex=True)

    # Handle genres
    df["genres"] = df["genres"].replace("(no genres listed)", "").fillna("")

    # Synthesize overview if missing
    df["overview"] = df.apply(
        lambda row: f"A {row['genres'].replace('|', ', ')} movie titled {row['title']}.", axis=1
    )

    # Additional empty columns for future enrichment
    df["cast"] = ""
    df["director"] = ""
    df["runtime"] = pd.NA
    df["language"] = ""
    df["rating"] = pd.NA

    df = df.rename(columns={"movieId": "id"})[
        [
            "id",
            "title",
            "genres",
            "overview",
            "cast",
            "director",
            "runtime",
            "language",
            "rating",
        ]
    ]
    return df


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if MOVIES_CSV.exists():
        print(f"{MOVIES_CSV} already exists. Skipping download.")
        return

    zip_bytes = download_movielens()
    df = prepare_movies_df(zip_bytes)
    df.to_csv(MOVIES_CSV, index=False)
    print(f"Saved cleaned movie data to {MOVIES_CSV}")


if __name__ == "__main__":
    main() 