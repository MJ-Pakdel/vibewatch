# 🍿 VibeWatch

A minimal, local-only Retrieval-Augmented Generation (RAG) movie recommender.
Everything lives inside the `vibewatch` Python package so you can
install, prepare data, and run the API without hunting for scripts.

## Quick start

```bash
# 1) Install deps (Python 3.9+ recommended)
python -m venv .venv && source .venv/bin/activate
cd vibewatch
pip install -r requirements.txt

# 2) Set your OpenAI key (anywhere in your env)
export OPENAI_API_KEY="sk-..."


Skip this section unless you mean to update the embeddings
# 3) Download MovieLens data & build embeddings (≈2 min)
# python scripts/download_and_prepare_data.py
# python scripts/build_embeddings.py

# 4) Launch the FastAPI server
uvicorn api.app:app --reload
# → open http://localhost:8000 to try it out
```

## Using the Application

1. **Open your browser** and navigate to `http://localhost:8000`
2. **Describe your mood** in the text area (e.g., "I'm feeling down after work, want something uplifting")
3. **Click "Find My Perfect Movies!"** to get 10 personalized recommendations
4. **Use Ctrl+Enter** as a keyboard shortcut to submit your query

## Endpoints

* **GET /** – serves a beautiful, interactive HTML interface
* **POST /recommend** – body `{ "user_input": "...", "k": 10 }`, returns
  a JSON list of movie recommendations

## How it works

1. **Data** – `download_and_prepare_data` fetches MovieLens, cleans it and
   writes `vibewatch/data/movies_clean.csv`.
2. **Embeddings** – `build_embeddings` embeds each movie (title + overview +
   genres…) with `text-embedding-3-small` and saves a FAISS index locally.
3. **RAG pipeline** – user query → similarity search in FAISS → top-k
   movies passed to GPT-4o via a prompt template → JSON recommendations.

## Example Queries

Try these mood-based queries:
- "I'm home alone feeling down, want something uplifting and light"
- "Saturday night with friends, want something fun and entertaining"
- "Need a thriller to keep me awake during a late night"
- "Watching with kids ages 6-9, something fun for the whole family"
- "Date night, looking for a romantic comedy"

No Docker, no databases, all local files. Perfect for a quick demo! ✨ 