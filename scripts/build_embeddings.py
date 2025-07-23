import json
from pathlib import Path

import pandas as pd
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MOVIES_CSV = DATA_DIR / "movies_clean.csv"
INDEX_DIR = DATA_DIR / "faiss_index"

EMBED_MODEL = "text-embedding-3-small"


def load_movies() -> pd.DataFrame:
    if not MOVIES_CSV.exists():
        raise FileNotFoundError("movies_clean.csv not found. Run download_and_prepare_data.py first.")
    return pd.read_csv(MOVIES_CSV)


def create_documents(df: pd.DataFrame):
    docs = []
    for _, row in df.iterrows():
        text_parts = [
            str(row.get("title", "")),
            str(row.get("overview", "")),
            str(row.get("genres", "")),
            str(row.get("cast", "")),
            str(row.get("director", "")),
        ]
        text = " \n".join([p for p in text_parts if p and p != "nan"])
        metadata = {
            "id": int(row["id"]),
            "title": row["title"],
            "genres": row["genres"],
            "overview": row["overview"],
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