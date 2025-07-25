from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import tempfile
from openai import OpenAI

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
    global openai_client
    recommender = VibeWatchRecommender(openai_api_key=OPENAI_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)


@app.post("/recommend")
async def recommend(req: RecommendRequest):
    try:
        recs = recommender.recommend(req.user_input, k=req.k)
        # Note: poster URLs are now included in the metadata from our embedding system
        # No need to fetch from external TMDB API anymore
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Voice-based recommendation endpoint


@app.post("/recommend_voice")
async def recommend_voice(file: UploadFile = File(...), k: int = Form(10)):
    """Accepts an audio file, transcribes it with Whisper, then returns movie recommendations."""
    try:
        # Save uploaded audio to a temporary file
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(contents)
            tmp.flush()
            tmp_path = tmp.name

        # Transcribe using OpenAI Whisper via new SDK
        resp = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp_path, "rb")
        )
        query_text = resp.text

        # Fetch recommendations via existing pipeline
        recs = recommender.recommend(query_text, k=k)
        # Note: poster URLs are now included in the metadata from our embedding system
        return {"query": query_text, "recs": recs}
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
      display: flex;
      align-items: center;
      gap: 12px;
    }
    header .logo { height: 36px; }
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
    #micBtn {
      background: var(--accent);
      color: white;
      border: none;
      padding: 14px 20px;
      font-weight: 600;
      font-size: 1rem;
      border-radius: 6px;
      cursor: pointer;
      transition: opacity .2s ease;
      margin-left: 8px;
    }
    #micBtn.rec {
      background: #1db954;
    }
    #submitBtn:hover, #micBtn:hover { opacity: .9; }
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
    #moodContainer {
      display: flex;
      justify-content: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 20px;
    }
    /* Unified knob styles (mood + age) */
    .knob-btn {
      background: var(--card-bg);
      border: 1px solid var(--muted);
      color: var(--text);
      padding: 8px 16px;
      border-radius: 999px;
      cursor: pointer;
      font-size: .85rem;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background .2s ease, border .2s ease, box-shadow .2s ease, transform .15s ease;
    }
    .knob-btn:hover {
      background: #2d2d2d;
      transform: translateY(-2px);
      box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    }
    .knob-btn.selected {
      border-color: var(--accent);
      background: linear-gradient(135deg, var(--accent) 0%, #ff7d1a 100%);
      color: #fff;
      box-shadow: 0 0 10px rgba(229,9,20,0.6);
    }

    /* Specific tweaks */
    .mood-btn { font-size: .9rem; }
    .age-btn  { font-size: .8rem; }
    .mood-btn span.emoji { font-size: 1.1rem; }
    /* Age selector styles */
    #ageSection {
      display: none;
      margin-top: 16px;
      text-align: center;
    }
    .age-hint {
      color: var(--muted);
      font-size: .9rem;
      margin-bottom: 8px;
    }
    #ageContainer {
      display: flex;
      justify-content: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .age-btn { padding: 6px 14px; }
    #moodSection {
      display: none;
      margin-top: 24px;
      text-align: center;
    }
    .mood-hint {
      color: var(--muted);
      font-size: .9rem;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <header><img src="https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg" class="logo" alt="Disney+ logo"/> VibeWatch</header>
  <main>
    <textarea id="queryBox" placeholder="Describe your vibe…"></textarea>
    <button id="submitBtn" onclick="submit()">Find Movies</button>
    <button id="micBtn">🎤 Speak</button>
    <div id="moodSection">
      <p class="mood-hint">Fine-tune your vibe — pick a mood below and we’ll refresh the list:</p>
      <div id="moodContainer" class="mood-container">
        <button class="mood-btn" data-mood="happy">😊 Happy</button>
        <button class="mood-btn" data-mood="sad">😢 Sad</button>
        <button class="mood-btn" data-mood="tired">😴 Tired</button>
        <button class="mood-btn" data-mood="intense">🤯 Intense</button>
        <button class="mood-btn" data-mood="thoughtful">🧠 Thoughtful</button>
        <button class="mood-btn" data-mood="romantic">💖 Romantic</button>
      </div>
    </div>

    <div id="ageSection">
      <p class="age-hint">Select the age group of your audience to refine further:</p>
      <div id="ageContainer">
        <button class="age-btn" data-age="Kids (0–7)">Kids</button>
        <button class="age-btn" data-age="Tweens (8–12)">Tweens</button>
        <button class="age-btn" data-age="Teens (13–17)">Teens</button>
        <button class="age-btn" data-age="Adults (18+)">Adults</button>
        <button class="age-btn" data-age="Seniors">Seniors</button>
        <button class="age-btn" data-age="Mixed Family">Mixed&nbsp;Family</button>
      </div>
    </div>
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
      originalQuery = user_input;
      selectedMood = '';
      selectedAge = '';
      document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
      document.querySelectorAll('.age-btn').forEach(b => b.classList.remove('selected'));
      document.getElementById('moodSection').style.display = 'none';
      document.getElementById('ageSection').style.display = 'none';
      fetchRecommendations(buildFinalQuery());
    }
    document.getElementById('queryBox').addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.ctrlKey) submit();
    });

    const micBtn = document.getElementById('micBtn');
    let mediaRecorder, audioChunks = [];

    micBtn.addEventListener('click', async () => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];
          mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
          mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            sendVoice(blob);
            stream.getTracks().forEach(t => t.stop());
          };
          mediaRecorder.start();
          micBtn.textContent = '⏹️ Stop';
          micBtn.classList.add('rec');
        } catch (err) {
          alert('Microphone access denied');
        }
      } else if (mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        micBtn.textContent = '🎤 Speak';
        micBtn.classList.remove('rec');
      }
    });

    async function sendVoice(blob) {
      const grid = document.getElementById('resultsGrid');
      const loading = document.getElementById('loading');
      grid.innerHTML = '';
      loading.style.display = 'block';
      try {
        const fd = new FormData();
        fd.append('file', blob, 'voice.webm');
        fd.append('k', '20');
        const resp = await fetch('/recommend_voice', { method: 'POST', body: fd });
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        loading.style.display = 'none';

        originalQuery = data.query || '';
        document.getElementById('queryBox').value = originalQuery;
        renderResults(data.recs || []);
      } catch (e) {
        loading.style.display = 'none';
        grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--accent);">Error: ${e.message}</div>`;
      }
    }

    let originalQuery = '';
    let selectedMood = '';
    let selectedAge = '';

    function buildFinalQuery() {
      let query = originalQuery;
      if (selectedMood) query += ' that matches a ' + selectedMood + ' mood';
      if (selectedAge) query += ' and is suitable for ' + selectedAge.toLowerCase();
      return query;
    }

    async function fetchRecommendations(queryText) {
      const grid = document.getElementById('resultsGrid');
      const loading = document.getElementById('loading');
      grid.innerHTML = '';
      loading.style.display = 'block';
      try {
        const resp = await fetch('/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_input: queryText, k: 20 })
        });
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        loading.style.display = 'none';
        renderResults(data);
      } catch (e) {
        loading.style.display = 'none';
        grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--accent);">Error: ${e.message}</div>`;
      }
    }

    function renderResults(recs) {
      const grid = document.getElementById('resultsGrid');
      if (Array.isArray(recs) && recs.length) {
        grid.innerHTML = '';
        recs.forEach((movie, idx) => {
          const card = document.createElement('div');
          card.className = 'movie-card';
          const img = document.createElement('img');
          img.src = movie.poster || 'https://via.placeholder.com/300x450/000000/FFFFFF/?text=' + encodeURIComponent(movie.title);
          card.appendChild(img);
          const info = document.createElement('div');
          info.className = 'movie-info';
          info.innerHTML = `<div class="movie-title">${idx + 1}. ${movie.title}</div><div class="movie-reason">${movie.reason}</div>`;
          card.appendChild(info);
          grid.appendChild(card);
        });
        document.getElementById('moodSection').style.display = 'block';
        document.getElementById('ageSection').style.display = 'block';
      } else {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;">No recommendations found.</div>';
      }
    }
  </script>
  <!-- Mood button handling -->
  <script>
    document.querySelectorAll('.mood-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!originalQuery) return; // need an initial query first
        document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedMood = btn.dataset.mood;
        fetchRecommendations(buildFinalQuery());
      });
    });
  </script>
  <!-- Age button handling -->
  <script>
    document.querySelectorAll('.age-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!originalQuery) return;
        document.querySelectorAll('.age-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedAge = btn.dataset.age;
        fetchRecommendations(buildFinalQuery());
      });
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_PAGE 