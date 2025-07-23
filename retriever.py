import json
from pathlib import Path
from typing import List, Dict

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

DATA_DIR = Path(__file__).resolve().parent / "data"
INDEX_DIR = DATA_DIR / "faiss_index"
EMBED_MODEL = "text-embedding-3-small"

_embeddings = None
_vectorstore = None
_metadata = None


def _load_vectorstore():
    global _embeddings, _vectorstore, _metadata
    if _vectorstore is not None:
        return

    if not INDEX_DIR.exists():
        raise FileNotFoundError("FAISS index not found. Run build_embeddings.py first.")

    _embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    _vectorstore = FAISS.load_local(str(INDEX_DIR), embeddings=_embeddings, allow_dangerous_deserialization=True)

    meta_path = INDEX_DIR / "metadata.json"
    if meta_path.exists():
        _metadata = {int(item["id"]): item for item in json.loads(meta_path.read_text())}
    else:
        _metadata = {}


def retrieve(query: str, k: int = 5) -> List[Dict]:
    """Return top-k movie metadata dicts for the query."""
    _load_vectorstore()
    docs = _vectorstore.similarity_search(query, k=k)
    results = [doc.metadata for doc in docs]
    return results 