from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os

from generator import VibeWatchRecommender

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY_HERE"

app = FastAPI(title="VibeWatch Recommender")


class RecommendRequest(BaseModel):
    user_input: str
    k: int = 10


@app.on_event("startup")
async def startup_event():
    global recommender
    if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
        print("WARNING: OPENAI_API_KEY not set. Recommender will likely fail.")
    recommender = VibeWatchRecommender(openai_api_key=OPENAI_API_KEY)


@app.post("/recommend")
async def recommend(req: RecommendRequest):
    try:
        recs = recommender.recommend(req.user_input, k=req.k)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VibeWatch – Movie Mood Matcher</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #141414;
      --card-bg: #1f1f1f;
      --accent: #e50914;
      --text: #f5f5f5;
      --muted: #b3b3b3;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      padding: 24px 32px;
      font-size: 1.8rem;
      font-weight: 600;
      color: var(--accent);
      letter-spacing: -0.5px;
    }
    main {
      width: 100%;
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 16px 40px;
      flex: 1;
    }
    #queryBox {
      width: 100%;
      height: 80px;
      padding: 16px;
      font-size: 1rem;
      border: none;
      border-radius: 8px;
      resize: vertical;
      margin-bottom: 12px;
    }
    #submitBtn {
      background: var(--accent);
      color: white;
      border: none;
      padding: 14px 28px;
      font-weight: 600;
      font-size: 1rem;
      border-radius: 6px;
      cursor: pointer;
      transition: opacity .2s ease;
    }
    #submitBtn:hover { opacity: .9; }
    #resultsGrid {
      margin-top: 32px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 24px;
    }
    .movie-card {
      background: var(--card-bg);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    .movie-card img {
      width: 100%;
      aspect-ratio: 2/3;
      object-fit: cover;
      background: #333;
    }
    .movie-info {
      padding: 12px 14px;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .movie-title {
      font-size: .95rem;
      font-weight: 600;
      margin-bottom: 6px;
      line-height: 1.2;
    }
    .movie-reason {
      font-size: .8rem;
      color: var(--muted);
      line-height: 1.3;
    }
    .loading {
      text-align: center;
      margin-top: 40px;
      color: var(--accent);
      font-weight: 600;
    }
  </style>
</head>
<body>
  <header>🍿 VibeWatch</header>
  <main>
    <textarea id="queryBox" placeholder="Describe your vibe…"></textarea>
    <button id="submitBtn" onclick="submit()">Find Movies</button>
    <div id="resultsGrid"></div>
    <div id="loading" class="loading" style="display:none;">Searching…</div>
  </main>
  <script>
    async function submit() {
      const user_input = document.getElementById('queryBox').value.trim();
      if (!user_input) {
        alert('Please describe your mood first!');
        return;
      }
      const grid = document.getElementById('resultsGrid');
      const loading = document.getElementById('loading');
      grid.innerHTML = '';
      loading.style.display = 'block';
      try {
        const resp = await fetch('/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_input, k: 20 })
        });
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        loading.style.display = 'none';
        if (Array.isArray(data) && data.length) {
          data.forEach((movie, idx) => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            const img = document.createElement('img');
            img.src = 'https://via.placeholder.com/300x450/000000/FFFFFF/?text=' + encodeURIComponent(movie.title);
            card.appendChild(img);
            const info = document.createElement('div');
            info.className = 'movie-info';
            info.innerHTML = `<div class="movie-title">${idx + 1}. ${movie.title}</div><div class="movie-reason">${movie.reason}</div>`;
            card.appendChild(info);
            grid.appendChild(card);
          });
        } else {
          grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;">No recommendations found.</div>';
        }
      } catch (e) {
        loading.style.display = 'none';
        grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--accent);">Error: ${e.message}</div>`;
      }
    }
    document.getElementById('queryBox').addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.ctrlKey) submit();
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_PAGE 