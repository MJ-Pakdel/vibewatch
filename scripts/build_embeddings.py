import json
from pathlib import Path

import pandas as pd
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MOVIES_CSV = DATA_DIR / "movies_disney_hulu.csv"
INDEX_DIR = DATA_DIR / "faiss_index"

EMBED_MODEL = "text-embedding-3-small"


def load_movies() -> pd.DataFrame:
    if not MOVIES_CSV.exists():
        raise FileNotFoundError("movies_disney_hulu.csv not found.")
    return pd.read_csv(MOVIES_CSV)


def extract_poster_url(images_data):
    """Extract poster URL from the images JSON data"""
    if not images_data or pd.isna(images_data):
        return None
    
    try:
        # Handle different possible formats
        images_str = str(images_data).strip()
        
        # Skip empty or 'nan' strings
        if not images_str or images_str.lower() in ['nan', 'none', '']:
            return None
            
        # Parse the JSON string
        import ast, json
        
        # Try json.loads first (proper JSON)
        try:
            images_dict = json.loads(images_str)
        except:
            # Fall back to ast.literal_eval (Python literal)
            images_dict = ast.literal_eval(images_str)
        
        # Get posters array
        posters = images_dict.get("posters", [])
        if posters and isinstance(posters, list) and len(posters) > 0:
            # Return the full_url from the first poster
            poster_url = posters[0].get("full_url")
            if poster_url:
                print(f"DEBUG: Extracted poster URL: {poster_url}")
                return poster_url
    except Exception as e:
        print(f"DEBUG: Failed to parse images data: {e}")
        print(f"DEBUG: Images data was: {repr(images_data)}")
    
    return None


def create_documents(df: pd.DataFrame):
    docs = []
    for idx, row in df.iterrows():
        # Map new columns to expected format
        # Use 'name' if 'title' is empty, otherwise use 'title'
        title_raw = row.get("title", "") or row.get("name", "")
        
        # Handle NaN/None values and convert to string safely
        if pd.isna(title_raw) or not title_raw or str(title_raw).strip() in ['nan', 'None', '']:
            print(f"DEBUG: Skipping movie at index {idx} - no valid title (title_raw: {repr(title_raw)})")
            continue  # Skip movies without valid titles
            
        title = str(title_raw).strip()
        
        # Extract genres from JSON-like string format
        genres_raw = row.get("genres", "")
        if isinstance(genres_raw, str) and genres_raw.startswith("["):
            try:
                # Parse JSON-like genres format
                import ast
                genres_list = ast.literal_eval(genres_raw)
                if isinstance(genres_list, list):
                    genres = ", ".join([g.get("name", "") for g in genres_list if isinstance(g, dict)])
                else:
                    genres = str(genres_raw)
            except:
                genres = str(genres_raw)
        else:
            genres = str(genres_raw) if genres_raw else ""
        
        # Extract poster URL from images data
        poster_url = extract_poster_url(row.get("images", ""))
        
        # Create text content for embedding - safely handle NaN values
        def safe_str(value):
            if pd.isna(value) or value is None:
                return ""
            str_val = str(value).strip()
            return str_val if str_val not in ['nan', 'None'] else ""
        
        text_parts = [
            safe_str(title),
            safe_str(row.get("overview", "")),
            safe_str(genres),
            safe_str(row.get("tagline", "")),
        ]
        text = " \n".join([p for p in text_parts if p and p.strip()])
        
        # Create metadata
        metadata = {
            "id": idx,  # Use row index as ID since there's no explicit ID column
            "title": title,
            "genres": genres,
            "overview": safe_str(row.get("overview", "")),
            "poster": poster_url,  # Add poster URL to metadata
        }
        docs.append(Document(page_content=text, metadata=metadata))
    return docs


def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    df = load_movies()
    docs = create_documents(df)

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    print(f"Computing embeddings for {len(docs)} documents ...")
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    vectorstore.save_local(str(INDEX_DIR))

    # Save metadata for quick lookup
    meta_path = INDEX_DIR / "metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump([d.metadata for d in docs], f, ensure_ascii=False, indent=2)
    print(f"Saved FAISS index and metadata to {INDEX_DIR}")


if __name__ == "__main__":
    main() 