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
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🍿 VibeWatch - Your Movie Mood Matcher</title>
<style>
body { 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    max-width: 800px; 
    margin: 0 auto; 
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.container {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
}

h1 { 
    text-align: center;
    color: #2c3e50;
    font-size: 2.5em;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.subtitle {
    text-align: center;
    color: #7f8c8d;
    font-size: 1.2em;
    margin-bottom: 30px;
}

textarea { 
    width: 100%; 
    height: 120px; 
    border: 3px solid #3498db;
    border-radius: 15px;
    padding: 15px;
    font-size: 16px;
    font-family: inherit;
    resize: vertical;
    transition: all 0.3s ease;
    box-sizing: border-box;
}

textarea:focus {
    outline: none;
    border-color: #e74c3c;
    box-shadow: 0 0 20px rgba(231, 76, 60, 0.3);
    transform: scale(1.02);
}

.button-container {
    text-align: center;
    margin: 25px 0;
}

button { 
    background: linear-gradient(45deg, #e74c3c, #f39c12);
    color: white;
    border: none;
    padding: 15px 40px;
    font-size: 18px;
    font-weight: bold;
    border-radius: 50px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
}

button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(231, 76, 60, 0.6);
    background: linear-gradient(45deg, #c0392b, #d68910);
}

button:active {
    transform: translateY(-1px);
}

#results { 
    background: #f8f9fa;
    border-radius: 15px;
    padding: 20px;
    margin-top: 25px;
    border-left: 5px solid #3498db;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
    white-space: pre-wrap;
    font-family: 'Courier New', monospace;
    max-height: 500px;
    overflow-y: auto;
}

.loading {
    text-align: center;
    color: #e74c3c;
    font-size: 18px;
    font-weight: bold;
}

.movie-card {
    background: white;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border-left: 4px solid #e74c3c;
}

.movie-title {
    font-size: 18px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 8px;
}

.movie-reason {
    color: #555;
    font-style: italic;
    line-height: 1.4;
}

.emoji {
    font-size: 1.2em;
}
</style>
</head>
<body>
<div class="container">
    <h1>🍿 VibeWatch</h1>
    <p class="subtitle">Your AI-powered movie mood matcher! ✨</p>
    
    <textarea id="user_input" placeholder="Tell me about your vibe! Are you feeling adventurous? Want to laugh? Need something to watch with the family? Describe your mood, who you're with, or what kind of night you're having... 🎬"></textarea>
    
    <div class="button-container">
        <button onclick="submit()">🎯 Find My Perfect Movies!</button>
    </div>
    
    <div id="results"></div>
</div>

<script>
async function submit() {
  const user_input = document.getElementById('user_input').value.trim();
  const resArea = document.getElementById('results');
  
  if (!user_input) {
    resArea.innerHTML = '<div style="color: #e74c3c; text-align: center;">Please describe your mood or viewing context first! 😊</div>';
    return;
  }
  
  resArea.innerHTML = '<div class="loading">🎬 Finding your perfect movies... ✨</div>';
  
  try {
    const resp = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input, k: 10 })
    });
    
    if (!resp.ok) {
      throw new Error(resp.statusText);
    }
    
    const data = await resp.json();
    
    if (Array.isArray(data) && data.length > 0) {
      let html = '<h3 style="color: #2c3e50; margin-bottom: 20px;">🎭 Your Personalized Movie Recommendations:</h3>';
      data.forEach((movie, index) => {
        html += `
          <div class="movie-card">
            <div class="movie-title">${index + 1}. 🎬 ${movie.title}</div>
            <div class="movie-reason">${movie.reason}</div>
          </div>
        `;
      });
      resArea.innerHTML = html;
    } else {
      resArea.innerHTML = '<div style="color: #e74c3c;">No recommendations found. Try describing your mood differently! 🤔</div>';
    }
    
  } catch (error) {
    resArea.innerHTML = `<div style="color: #e74c3c;">Error: ${error.message} 😞</div>`;
  }
}

// Allow Enter key to submit
document.getElementById('user_input').addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && e.ctrlKey) {
    submit();
  }
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_PAGE 