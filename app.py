import os
import json
import time
import sqlite3
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "efootball_hub_2026_secret")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "efootball_hub.db")

def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_db() as db:
        # جدول اللاعبين
        db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                overall INTEGER NOT NULL,
                position TEXT NOT NULL,
                team TEXT NOT NULL,
                card_type TEXT NOT NULL,
                image_url TEXT NOT NULL,
                stars INTEGER DEFAULT 5,
                stats JSON
            )
        """)

        # جدول المدربين
        db.execute("""
            CREATE TABLE IF NOT EXISTS managers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                coaching_style TEXT NOT NULL,
                image_url TEXT NOT NULL,
                affinity TEXT DEFAULT '100%'
            )
        """)

        # إضافة بيانات تجريبية لمحاكاة تحديثات كونامي الأسبوعية (KONAMI Weekly Drops)
        cursor = db.execute("SELECT COUNT(*) as count FROM players")
        if cursor.fetchone()["count"] == 0:
            default_players = [
                ("Yaya Touré", 86, "DMF", "FC Barcelona", "Epic / Big Time", "https://i.imgur.com/8Q9PzZ1.png", 5),
                ("Xabi Alonso", 86, "DMF", "Real Madrid", "Epic", "https://i.imgur.com/2Xy5kK3.png", 5),
                ("Clarence Seedorf", 87, "CMF", "AC Milan", "Showtime", "https://i.imgur.com/9aL3pKq.png", 5),
                ("Micky van de Ven", 85, "CB", "Tottenham", "Highlight", "https://i.imgur.com/v1K8mLX.png", 5),
                ("Thibaut Courtois", 86, "GK", "Real Madrid", "Highlight", "https://i.imgur.com/k9L2PzA.png", 5),
                ("Ricardo Quaresma", 85, "RWF", "Beşiktaş", "Epic", "https://i.imgur.com/7M8zQxX.png", 5),
                ("Mohamed Salah", 83, "AMF", "Liverpool", "Super-Featured", "https://i.imgur.com/3Z4M8pK.png", 5),
                ("Mitchell Bakker", 82, "CF", "Atalanta", "Featured", "https://i.imgur.com/5N7xL2k.png", 4),
            ]
            db.executemany("""
                INSERT INTO players (name, overall, position, team, card_type, image_url, stars)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, default_players)

        cursor_m = db.execute("SELECT COUNT(*) as count FROM managers")
        if cursor_m.fetchone()["count"] == 0:
            default_managers = [
                ("Jürgen Klopp", "Quick Counter", "https://i.imgur.com/z4M2x1A.png", "88"),
                ("Cristian Chivu", "Possession Game", "https://i.imgur.com/b8K5x2K.png", "85"),
                ("R. Rodríguez", "Out-side", "https://i.imgur.com/9L3M2pK.png", "83"),
                ("José Mourinho", "Long Ball Counter", "https://i.imgur.com/1N5xK3P.png", "88"),
            ]
            db.executemany("""
                INSERT INTO managers (name, coaching_style, image_url, affinity)
                VALUES (?, ?, ?, ?)
            """, default_managers)

init_db()

PAGE_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA eHUB 26 | eFootball Player Database & Community</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root {
  --bg-dark: #07090e;
  --panel-bg: #0e121d;
  --neon-green: #ccff00;
  --neon-blue: #00d2ff;
  --neon-purple: #9d00ff;
  --border-color: #1e2638;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: var(--bg-dark);
  color: #fff;
  font-family: 'Cairo', sans-serif;
  min-height: 100vh;
}

/* Header & Navigation Bar */
.navbar {
  background: #090d16;
  border-bottom: 2px solid var(--neon-green);
  padding: 12px 4%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  font-weight: 900;
  font-size: 24px;
  color: #fff;
}
.brand span { color: var(--neon-green); }
.brand-badge {
  background: var(--neon-green);
  color: #000;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 900;
}

.search-box {
  position: relative;
  width: 40%;
  max-width: 500px;
}
.search-box input {
  width: 100%;
  padding: 10px 18px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: #141a29;
  color: #fff;
  font-family: 'Cairo';
  font-size: 13px;
  outline: none;
}
.search-box input:focus {
  border-color: var(--neon-green);
  box-shadow: 0 0 10px rgba(204, 255, 0, 0.3);
}

.nav-links {
  display: flex;
  gap: 15px;
}
.nav-links a {
  color: #a0aec0;
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 8px;
  transition: 0.2s;
}
.nav-links a:hover, .nav-links a.active {
  color: var(--neon-green);
  background: #141a29;
}

/* Container */
.container {
  padding: 25px 4%;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 18px;
  color: #fff;
  border-right: 4px solid var(--neon-green);
  padding-right: 10px;
}

/* Cards Grid Layout */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 35px;
}

/* eFootball Player Card */
.player-card {
  background: linear-gradient(145deg, #121826, #090d16);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 10px;
  text-align: center;
  position: relative;
  transition: transform 0.25s, border-color 0.25s, box-shadow 0.25s;
  cursor: pointer;
  overflow: hidden;
}
.player-card:hover {
  transform: translateY(-5px);
  border-color: var(--neon-green);
  box-shadow: 0 0 20px rgba(204, 255, 0, 0.25);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 5px;
}
.overall-rating {
  font-size: 22px;
  font-weight: 900;
  color: #fff;
  line-height: 1;
}
.position {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  background: #1a233a;
  color: var(--neon-green);
}

.player-img {
  width: 100%;
  height: 120px;
  object-fit: contain;
  margin: 5px 0;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.6));
}

.player-name {
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 4px;
}

.player-team {
  font-size: 10px;
  color: #8fa0c0;
}

.stars {
  color: var(--neon-green);
  font-size: 10px;
  margin-top: 4px;
}

/* Manager Card */
.manager-card {
  background: #0e1320;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 12px;
  text-align: center;
  transition: 0.2s;
}
.manager-card:hover {
  border-color: var(--neon-blue);
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.2);
}
.manager-img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--neon-blue);
  margin-bottom: 8px;
}

.btn-more {
  display: block;
  width: fit-content;
  margin: 0 auto 30px;
  padding: 10px 28px;
  background: var(--neon-green);
  color: #000;
  font-weight: 800;
  font-size: 13px;
  border-radius: 25px;
  text-decoration: none;
  box-shadow: 0 0 15px rgba(204, 255, 0, 0.3);
  transition: 0.2s;
}
.btn-more:hover {
  transform: scale(1.05);
}

footer {
  text-align: center;
  padding: 20px;
  background: #05070c;
  border-top: 1px solid var(--border-color);
  color: #64748b;
  font-size: 11px;
}
</style>
</head>
<body>

<header class="navbar">
  <a href="/" class="brand">
    <div class="brand-badge">26</div>
    NOVA <span>eHUB</span>
  </a>

  <div class="search-box">
    <input type="text" id="searchInput" placeholder="ابحث عن لاعب أو مدرب في eFootball..." onkeyup="searchCards()">
  </div>

  <nav class="nav-links">
    <a href="/" class="active">⚽ اللاعبون</a>
    <a href="#">👔 المدربون</a>
    <a href="#">📊 باني الخطة (Squad)</a>
  </nav>
</header>

<main class="container">
  
  <div class="section-title">⚡ أحدث بطاقات اللاعبين (KONAMI Drops)</div>
  
  <div class="card-grid" id="playersGrid">
    {% for p in players %}
    <div class="player-card">
      <div class="card-header">
        <span class="overall-rating">{{ p['overall'] }}</span>
        <span class="position">{{ p['position'] }}</span>
      </div>
      <img class="player-img" src="{{ p['image_url'] }}" alt="{{ p['name'] }}" onerror="this.src='https://i.imgur.com/8Q9PzZ1.png'">
      <div class="player-name">{{ p['name'] }}</div>
      <div class="player-team">{{ p['team'] }}</div>
      <div class="stars">★★★★★</div>
    </div>
    {% endfor %}
  </div>

  <a href="#" class="btn-more">عرض كافة اللاعبين الجدد ←</a>

  <div class="section-title">👔 أحدث المدربين (Managers)</div>

  <div class="card-grid" id="managersGrid">
    {% for m in managers %}
    <div class="manager-card">
      <img class="manager-img" src="{{ m['image_url'] }}" alt="{{ m['name'] }}" onerror="this.src='https://i.imgur.com/z4M2x1A.png'">
      <div class="player-name">{{ m['name'] }}</div>
      <div class="player-team" style="color: var(--neon-blue);">{{ m['coaching_style'] }}</div>
      <div style="font-size: 10px; color: #aaa; margin-top: 4px;">كفاءة التدريب: <b>{{ m['affinity'] }}</b></div>
    </div>
    {% endfor %}
  </div>

</main>

<footer>
  <p>© 2026 NOVA eHUB - منصة وقاعدة بيانات لاعبي eFootball المعتمدة</p>
</footer>

<script>
function searchCards() {
  let query = document.getElementById('searchInput').value.toLowerCase();
  let cards = document.querySelectorAll('.player-card, .manager-card');
  cards.forEach(card => {
    let name = card.querySelector('.player-name').textContent.toLowerCase();
    if(name.includes(query)) card.style.display = 'block';
    else card.style.display = 'none';
  });
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    with get_db() as db:
        players = [dict(row) for row in db.execute("SELECT * FROM players ORDER BY id DESC").fetchall()]
        managers = [dict(row) for row in db.execute("SELECT * FROM managers ORDER BY id DESC").fetchall()]
    return render_template_string(PAGE_TEMPLATE, players=players, managers=managers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
