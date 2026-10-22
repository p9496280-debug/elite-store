import os
import json
import time
import secrets
import sqlite3
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template_string,
    request,
    session,
    redirect,
    url_for,
    jsonify,
    Response,
)

from leagues_and_clubs import get_all_leagues, get_club_logo
from classic_players import get_classic_players
from player_stats import PLAYER_STATS_TEMPLATE

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_ehub_master_key_2026")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_EMAIL = "moh99zzhvni893fj7@gmail.com"
ADMIN_PASSWORD = "mohammedaaa222"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_ehub.db")

TELEGRAM_DEV = "https://t.me/Mido_M9do"
TELEGRAM_MAIN = "https://t.me/Midomsn"
TELEGRAM_BOT = "https://t.me/midoassistantAIbot"
TELEGRAM_CODES_CHANNEL = "https://t.me/MidoWorld"


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                verified INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                image_url TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS managers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER DEFAULT 50,
                team TEXT DEFAULT 'Unattached',
                playstyle TEXT NOT NULL,
                affinity INTEGER NOT NULL DEFAULT 85,
                image_url TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS saved_squads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                squad_json TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)

        try:
            db.execute("ALTER TABLE managers ADD COLUMN age INTEGER DEFAULT 50")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE managers ADD COLUMN team TEXT DEFAULT 'Unattached'")
        except Exception:
            pass

        db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                overall_base INTEGER NOT NULL,
                overall_max INTEGER NOT NULL,
                position TEXT NOT NULL,
                team TEXT NOT NULL,
                nationality TEXT DEFAULT '',
                card_type TEXT NOT NULL,
                is_upcoming INTEGER DEFAULT 0,
                image_url TEXT NOT NULL,
                height INTEGER DEFAULT 180,
                weight INTEGER DEFAULT 75,
                age INTEGER DEFAULT 25,
                stamina INTEGER DEFAULT 80,
                stats_json TEXT NOT NULL,
                skills_json TEXT NOT NULL
            )
        """)

        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('custom_banner', '')")
        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('managers_card_img', '')")
        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('total_downloads_count', '1420')")

        cursor_n = db.execute("SELECT COUNT(*) as count FROM news")
        if cursor_n.fetchone()["count"] == 0:
            db.execute("INSERT INTO news (title, content, created_at) VALUES (?, ?, ?)", 
                       ("تحديث صيانة الخميس القادم", "وصول بطاقات Epic جديدة وتسريبات قوية لميسي ورونالدو.", int(time.time())))

        cursor_m = db.execute("SELECT COUNT(*) as count FROM managers")
        if cursor_m.fetchone()["count"] == 0:
            db.execute("INSERT INTO managers (name, age, team, playstyle, affinity, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                       ("Jürgen Klopp", 56, "Germany / Liverpool", "Quick Counter", 88, "https://via.placeholder.com/150/121826/ccff00?text=Klopp"))
            db.execute("INSERT INTO managers (name, age, team, playstyle, affinity, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                       ("Cristian Chivu", 43, "Romania / Inter Milan", "Possession Game", 85, "https://via.placeholder.com/150/121826/ccff00?text=Chivu"))
            db.execute("INSERT INTO managers (name, age, team, playstyle, affinity, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                       ("R. Rodriguez", 48, "Spain / Free Agent", "Out Wide", 83, "https://via.placeholder.com/150/121826/ccff00?text=Rodriguez"))

        cursor_p = db.execute("SELECT COUNT(*) as count FROM players")
        if cursor_p.fetchone()["count"] == 0:
            varane_stats = {"attacking": {"وعي هجومي": 52, "التحكم في الكرة": 66, "المراوغة": 70, "إنهاء الهجمة": 50}, "physical": {"السرعة": 81, "التسارع": 76, "القفز": 78}, "defending": {"وعي دفاعي": 88, "احتكاك دفاعي": 88, "قطع الكرة": 87}}
            seedorf_stats = {"attacking": {"وعي هجومي": 88, "التحكم في الكرة": 92, "التمريرات": 93, "إنهاء الهجمة": 85}, "physical": {"السرعة": 88, "قوة في الركل": 92}, "defending": {"وعي دفاعي": 78, "قطع الكرة": 79}}
            messi_stats = {"attacking": {"وعي هجومي": 96, "التحكم في الكرة": 98, "المراوغة": 99, "إنهاء الهجمة": 96}, "physical": {"السرعة": 92, "التسارع": 95}, "defending": {"وعي دفاعي": 40}}
            ronaldo_stats = {"attacking": {"وعي هجومي": 95, "التحكم في الكرة": 88, "إنهاء الهجمة": 98}, "physical": {"السرعة": 93, "القفز": 98}, "defending": {"وعي دفاعي": 45}}
            neymar_stats = {"attacking": {"وعي هجومي": 90, "المراوغة": 98, "إنهاء الهجمة": 89}, "physical": {"السرعة": 94, "التسارع": 96}, "defending": {"وعي دفاعي": 38}}

            default_players = [
                ("Raphael Varane", 88, 103, "CB", "Manchester United", "Showtime", 0, "https://via.placeholder.com/150/121826/ccff00?text=Varane", 191, 81, 30, 85, json.dumps(varane_stats), json.dumps(["مهارة الرأس", "حصن"])),
                ("Seedorf", 94, 106, "CMF", "AC Milan", "Epic / Big Time", 0, "https://via.placeholder.com/150/121826/ccff00?text=Seedorf", 176, 78, 27, 90, json.dumps(seedorf_stats), json.dumps(["التمرير الموزون"])),
                ("Lionel Messi", 96, 108, "RWF", "Inter Miami", "Epic / Big Time", 0, "https://via.placeholder.com/150/121826/ccff00?text=Messi", 170, 72, 35, 88, json.dumps(messi_stats), json.dumps(["المراوغة السريعة"])),
                ("Cristiano Ronaldo", 95, 107, "ST", "Al Nassr", "Epic / Big Time", 0, "https://via.placeholder.com/150/121826/ccff00?text=Ronaldo", 187, 83, 36, 92, json.dumps(ronaldo_stats), json.dumps(["رأسيات قوية"])),
                ("Neymar Jr", 94, 105, "LWF", "Al Hilal", "Showtime", 1, "https://via.placeholder.com/150/121826/ccff00?text=Neymar", 175, 68, 31, 84, json.dumps(neymar_stats), json.dumps(["المراوغة المزدوجة"]))
            ]
            db.executemany("""
                INSERT INTO players (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, height, weight, age, stamina, stats_json, skills_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_players)
            db.commit()


init_db()


@app.route('/manifest.json')
def manifest():
    data = {
        "short_name": "eHUB 26",
        "name": "NOVA eHUB 26 Database",
        "icons": [
            {"src": "https://via.placeholder.com/192/07090e/ccff00?text=eHUB", "type": "image/png", "sizes": "192x192"},
            {"src": "https://via.placeholder.com/512/07090e/ccff00?text=eHUB", "type": "image/png", "sizes": "512x512"}
        ],
        "start_url": "/",
        "background_color": "#07090e",
        "theme_color": "#ccff00",
        "display": "standalone",
        "orientation": "portrait"
    }
    return jsonify(data)


@app.route('/sw.js')
def service_worker():
    js = "self.addEventListener('install', (e) => { self.skipWaiting(); }); self.addEventListener('fetch', (e) => { e.respondWith(fetch(e.request)); });"
    return Response(js, mimetype='text/javascript')


def send_verification_code_to_channel(email, code):
    try:
        requests.post("https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage", json={
            "chat_id": "@MidoWorld",
            "text": f"🔐 كود تحقق جديد لمنصة NOVA eHUB 26\nالبريد: {email[:3]}***@***\nالكود: {code}"
        }, timeout=2)
    except Exception:
        pass


HOME_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA eHUB 26 | eFootball Database</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#ccff00">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --neon-blue: #00d2ff; --border-color: #1e2638; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; min-height: 100vh; display: flex; flex-direction: column; justify-content: space-between; }
.navbar { background: #090d16; border-bottom: 2px solid var(--neon-green); padding: 12px 4%; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; flex-wrap: wrap; gap: 10px; }
.brand { font-weight: 900; font-size: 22px; color: #fff; text-decoration: none; display: flex; align-items: center; gap: 8px; }
.brand span { color: var(--neon-green); }
.brand-badge { background: var(--neon-green); color: #000; padding: 2px 6px; border-radius: 6px; font-size: 12px; }
.search-box input { width: 220px; padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border-color); background: #141a29; color: #fff; font-family: 'Cairo'; outline: none; }
.search-box input:focus { border-color: var(--neon-green); }
.user-actions { display: flex; gap: 8px; align-items: center; }
.btn-action { padding: 6px 14px; background: #141a29; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; text-decoration: none; font-size: 12px; font-weight: bold; }
.btn-action.primary { background: var(--neon-green); color: #000; border: 0; }
.install-bar { display: none; background: #ccff00; color: #000; padding: 10px 4%; text-align: center; font-weight: 800; font-size: 13px; cursor: pointer; border-bottom: 2px solid #000; }

.custom-banner { width: 100%; background: #000; text-align: center; border-bottom: 2px solid var(--border-color); padding: 10px 0; }
.custom-banner img { max-width: 100%; height: auto; max-height: 400px; object-fit: contain; display: block; margin: 0 auto; }

.squad-builder-card {
  margin: 20px 4%;
  background: linear-gradient(135deg, #091309, #0e1a14);
  border: 2px solid var(--neon-green);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 0 25px rgba(204, 255, 0, 0.15);
}
.squad-info { max-width: 60%; }
.squad-badge { color: var(--neon-green); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.squad-title { font-size: 26px; font-weight: 900; color: #fff; margin: 4px 0; }
.squad-desc { font-size: 12px; color: #94a3b8; margin-bottom: 15px; }
.btn-build { display: inline-block; padding: 10px 22px; background: var(--neon-green); color: #000; border-radius: 25px; font-weight: 900; font-size: 13px; text-decoration: none; box-shadow: 0 0 10px rgba(204,255,0,0.4); }

.managers-section { margin: 25px 4%; }
.sec-title { font-size: 16px; font-weight: 900; color: #fff; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.managers-row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 10px; align-items: center; }

.managers-main-card {
  min-width: 130px;
  height: 140px;
  background: linear-gradient(145deg, #101728, #07090e);
  border: 2px solid var(--neon-blue);
  border-radius: 16px;
  padding: 10px;
  text-align: center;
  cursor: pointer;
  text-decoration: none;
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.2);
  transition: 0.2s;
}
.managers-main-card:hover { transform: scale(1.05); border-color: var(--neon-green); }
.managers-card-img { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid var(--neon-green); margin-bottom: 6px; }

.manager-card { min-width: 120px; background: #0e121d; border: 1px solid var(--border-color); border-radius: 14px; padding: 10px; text-align: center; text-decoration: none; color: inherit; display: block; cursor: pointer; transition: 0.2s; }
.manager-card:hover { border-color: var(--neon-green); transform: translateY(-2px); }
.manager-img { width: 60px; height: 60px; border-radius: 50%; border: 1px solid var(--border-color); object-fit: cover; margin: 0 auto 6px; display: block; }
.manager-name { font-size: 11px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.manager-style { font-size: 9px; color: var(--neon-green); background: #141a29; border-radius: 6px; padding: 2px 5px; margin-top: 4px; display: inline-block; }

.community-news { background: #0e1320; border: 1px solid var(--border-color); border-radius: 14px; padding: 16px; margin: 20px 4%; }
.news-title { font-size: 15px; font-weight: 800; color: var(--neon-green); margin-bottom: 6px; }
.news-item { font-size: 12px; color: #cbd5e1; padding: 6px 0; border-bottom: 1px solid #1e2638; }

.quick-btns { display: flex; gap: 10px; margin: 15px 4%; flex-wrap: wrap; }
.q-btn { padding: 8px 16px; background: #141a29; border: 1px solid var(--border-color); border-radius: 10px; color: #fff; font-size: 12px; font-weight: bold; text-decoration: none; }

.tabs { display: flex; gap: 10px; margin: 20px 4%; flex-wrap: wrap; }
.tab-btn { padding: 8px 18px; background: #141a29; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; cursor: pointer; font-family: 'Cairo'; font-weight: 700; font-size: 13px; }
.tab-btn.active { background: var(--neon-green); color: #000; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 16px; padding: 0 4%; margin-bottom: 40px; }
.player-card { background: linear-gradient(145deg, #121826, #090d16); border: 1px solid var(--border-color); border-radius: 14px; padding: 10px; text-align: center; cursor: pointer; transition: 0.2s; text-decoration: none; color: inherit; }
.player-card:hover { border-color: var(--neon-green); box-shadow: 0 0 15px rgba(204, 255, 0, 0.25); transform: translateY(-3px); }
.card-header { display: flex; justify-content: space-between; font-weight: 900; }
.overall { font-size: 20px; color: var(--neon-green); }
.position { font-size: 11px; background: #1a233a; padding: 2px 6px; border-radius: 4px; color: #00d2ff; }
.player-img { width: 100%; height: 115px; object-fit: cover; margin: 6px 0; background: #121826; border-radius: 8px; }
.player-name { font-size: 13px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.bottom-section { margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 25px; background: #05070c; }
.footer-buttons { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; padding: 0 4%; }
.f-btn { padding: 10px 20px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 12px; }
.f-btn-dev { background: #2563eb; color: #fff; }
.f-btn-main { background: #7c3aed; color: #fff; }
.f-btn-bot { background: #0284c7; color: #fff; }
footer { text-align: center; padding: 15px; color: #64748b; font-size: 11px; }
</style>
</head>
<body>

<div>
  <div class="install-bar" id="installBar" onclick="installApp()">📲 اضغط هنا لتنزيل تطبيق NOVA eHUB 26 على شاشة هاتفك مباشرة!</div>

  <header class="navbar">
    <a href="/" class="brand"><div class="brand-badge">26</div>eHUB <span>NOVA</span></a>
    <div class="search-box"><input type="text" id="searchInput" placeholder="ابحث عن لاعب..." onkeyup="filterCards()"></div>
    <div class="user-actions">
      {% if user %}
        <a href="/account" class="btn-action" style="color:var(--neon-green);">👤 {{ user["name"] }}</a>
        <a href="/logout" class="btn-action" style="color:#fca5a5;">خروج</a>
      {% else %}
        <a href="/login" class="btn-action">دخول</a>
        <a href="/register" class="btn-action primary">حساب جديد</a>
      {% endif %}
      <a href="/admin" class="btn-action" style="background:#7f1d1d;">⚙️ المطور</a>
    </div>
  </header>

  {% if custom_banner %}
  <div class="custom-banner"><img src="{{ custom_banner }}" alt="Main Banner"></div>
  {% endif %}

  <div class="squad-builder-card">
    <div class="squad-info">
      <div class="squad-badge">محدث ⚡</div>
      <div class="squad-title">باني فرقة</div>
      <div class="squad-desc">أنشئ التشكيلة، اضبط تكتيكاتك وشاركها مع أصدقائك.</div>
      <a href="/squad-builder" class="btn-build">+ إنشاء تشكيلة</a>
    </div>
    <div style="font-size:45px;">📋</div>
  </div>

  <div class="managers-section">
    <div class="sec-title">👔 قائمة المدربين الرسمية</div>
    <div class="managers-row">
      <a href="/managers" class="managers-main-card">
        <img class="managers-card-img" src="{{ managers_card_img if managers_card_img else 'https://via.placeholder.com/60/00d2ff/000000?text=ALL' }}" onerror="this.src='https://via.placeholder.com/60/00d2ff/000000?text=ALL'">
        <div style="font-size:12px; font-weight:900; color:var(--neon-green);">قائمة المدربين</div>
        <div style="font-size:9px; color:#8fa0c0;">عرض الكل ➔</div>
      </a>

      {% for m in managers[:3] %}
      <a href="/manager/{{ m['id'] }}" class="manager-card">
        <img class="manager-img" src="{{ m['image_url'] }}" onerror="this.src='https://via.placeholder.com/60/121826/ccff00?text=Coach'">
        <div class="manager-name">{{ m['name'] }}</div>
        <div class="manager-style">{{ m['playstyle'] }}</div>
      </a>
      {% endfor %}
    </div>
  </div>

  <div class="community-news">
    <div class="news-title">📢 أخبار المجتمع وتحديثات كونامي والرسائل</div>
    {% for n in news %}
    <div class="news-item"><b>{{ n['title'] }}</b>: {{ n['content'] }}</div>
    {% endfor %}
  </div>

  <div class="quick-btns">
    <a href="/skills" class="q-btn">⚡ المهارات الجديدة (Skills)</a>
    <a href="#" class="q-btn">📝 منشورات المجتمع (Post to Feed)</a>
  </div>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('all', this)">⚡ جميع اللاعبين والأساطير</button>
    <button class="tab-btn" onclick="switchTab('upcoming', this)">🔮 التسريبات (Upcoming)</button>
  </div>

  <div class="card-grid" id="playersGrid">
    {% for p in players %}
    <a href="/player-stats/{{ p['id'] }}" class="player-card" data-upcoming="{{ p['is_upcoming'] }}">
      <div class="card-header"><span class="overall">{{ p['overall_max'] }}</span><span class="position">{{ p['position'] }}</span></div>
      <img class="player-img" src="{{ p['image_url'] }}" alt="{{ p['name'] }}" onerror="this.src='https://via.placeholder.com/150/121826/ccff00?text=eFootball'">
      <div class="player-name">{{ p['name'] }}</div>
      <div style="font-size:9px; color:#8fa0c0; margin-top:2px;">{{ p['card_type'] }}</div>
    </a>
    {% endfor %}
  </div>
</div>

<div class="bottom-section">
  <div class="footer-buttons">
    <a href="{{ telegram_dev }}" target="_blank" class="f-btn f-btn-dev">👨‍💻 التواصل مع المطور</a>
    <a href="{{ telegram_main }}" target="_blank" class="f-btn f-btn-main">📢 القناة الأساسية</a>
    <a href="{{ telegram_bot }}" target="_blank" class="f-btn f-btn-bot">🤖 البوت الخاص بنا</a>
  </div>
  <footer>
    <p>قناة التنبيهات والأكواد الرسمية: <a href="{{ telegram_codes_channel }}" target="_blank" style="color:var(--neon-green); text-decoration:none;">MidoWorld ✈️</a></p>
    <p style="margin-top:5px;">© 2026 NOVA eHUB - جميع الحقوق محفوظة</p>
  </footer>
</div>

<script>
if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js'); }
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; document.getElementById('installBar').style.display = 'block'; });
function installApp() { if (deferredPrompt) { deferredPrompt.prompt(); deferredPrompt.userChoice.then((c) => { if (c.outcome === 'accepted') { document.getElementById('installBar').style.display = 'none'; } deferredPrompt = null; }); } }
function switchTab(type, btn) { document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active'); document.querySelectorAll('.player-card').forEach(card => { let isUpcoming = card.getAttribute('data-upcoming'); if(type === 'all') card.style.display = 'block'; else if(type === 'upcoming' && isUpcoming === '1') card.style.display = 'block'; else card.style.display = 'none'; }); }
function filterCards() { let query = document.getElementById('searchInput').value.toLowerCase(); document.querySelectorAll('.player-card').forEach(card => { let name = card.querySelector('.player-name').textContent.toLowerCase(); card.style.display = name.includes(query) ? 'block' : 'none'; }); }
</script>
</body>
</html>
"""


MANAGER_DETAIL_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ manager['name'] }} | Manager Profile</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --neon-blue: #00d2ff; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 20px; display: grid; place-items: center; min-height: 100vh; margin: 0; }
.manager-box { background: linear-gradient(145deg, #0e121d, #07090e); border: 2px solid var(--neon-green); border-radius: 20px; padding: 30px; width: 100%; max-width: 480px; text-align: center; box-shadow: 0 0 25px rgba(204,255,0,0.15); }
.manager-img-large { width: 110px; height: 110px; border-radius: 50%; object-fit: cover; border: 3px solid var(--neon-green); margin-bottom: 12px; }
.manager-title { font-size: 24px; font-weight: 900; color: #fff; margin-bottom: 4px; }
.manager-sub { font-size: 12px; color: #94a3b8; margin-bottom: 18px; }
.stats-list { background: #0e1320; border: 1px solid var(--border-color); border-radius: 14px; padding: 15px; text-align: right; margin-bottom: 20px; }
.stat-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1e2638; font-size: 13px; }
.stat-item:last-child { border: 0; }
.back-btn { display: block; width: 100%; padding: 12px; background: var(--neon-green); color: #000; border-radius: 12px; font-weight: 900; text-decoration: none; font-size: 13px; }
</style>
</head>
<body>
<div class="manager-box">
  <img class="manager-img-large" src="{{ manager['image_url'] }}" onerror="this.src='https://via.placeholder.com/110/121826/ccff00?text=Coach'">
  <div class="manager-title">{{ manager['name'] }}</div>
  <div class="manager-sub">👔 بطاقة المدير الفني الرسمي</div>

  <div class="stats-list">
    <div class="stat-item"><span style="color:#94a3b8;">السن / العمر:</span> <b>{{ manager['age'] }} سنة</b></div>
    <div class="stat-item"><span style="color:#94a3b8;">الفريق / الجنسية:</span> <b style="color:var(--neon-blue);">{{ manager['team'] }}</b></div>
    <div class="stat-item"><span style="color:#94a3b8;">أسلوب اللعب المفضل:</span> <b style="color:var(--neon-green);">{{ manager['playstyle'] }}</b></div>
    <div class="stat-item"><span style="color:#94a3b8;">تطوير اللاعبين (Coaching Affinity):</span> <b>{{ manager['affinity'] }}</b></div>
    <div class="stat-item"><span style="color:#94a3b8;">طاقة المهارة التكتيكية:</span> <b style="color:var(--neon-green);">88/100</b></div>
  </div>

  <a href="/" class="back-btn">← العودة للصفحة الرئيسية</a>
</div>
</body>
</html>
"""


SQUAD_BUILDER_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>تكتيك الملعب وباني الفرقة | NOVA eHUB 26</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --neon-blue: #00d2ff; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 15px; }

.squad-controls { max-width: 500px; margin: 0 auto 15px; background: #0e121d; border: 1px solid var(--border-color); border-radius: 14px; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
.control-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
select, input { background: #07090e; border: 1px solid var(--border-color); color: #fff; padding: 8px; border-radius: 8px; font-family: 'Cairo'; font-size: 12px; }

.manager-preview-box { display: flex; align-items: center; gap: 10px; background: #141a29; border: 1px solid var(--neon-blue); border-radius: 10px; padding: 6px 12px; }
.manager-preview-img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid var(--neon-green); display: none; }
.club-preview-img { width: 35px; height: 35px; object-fit: contain; display: none; }

.pitch-container { max-width: 500px; margin: 0 auto; background: linear-gradient(180deg, #0b2512, #051408); border: 2px solid var(--neon-green); border-radius: 20px; padding: 20px 10px; position: relative; min-height: 580px; overflow: hidden; }
.pitch-line { position: absolute; border: 1px solid rgba(204, 255, 0, 0.2); pointer-events: none; }
.line-center { top: 50%; left: 0; right: 0; }
.line-circle { top: 50%; left: 50%; width: 100px; height: 100px; border-radius: 50%; transform: translate(-50%, -50%); }

.tactical-overlay { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:5; }

.pos-slot { width: 68px; height: 88px; background: rgba(14, 18, 29, 0.92); border: 1px dashed var(--neon-green); border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 10px; font-weight: 800; color: var(--neon-green); cursor: move; position: absolute; z-index: 10; transition: border-color 0.2s, box-shadow 0.2s; text-align: center; user-select: none; touch-action: none; }
.pos-slot:active { z-index: 20; border-style: solid; box-shadow: 0 0 15px rgba(204,255,0,0.5); }
.pos-slot img { width: 42px; height: 42px; object-fit: cover; border-radius: 6px; pointer-events: none; }
.delete-btn { position: absolute; top: -5px; right: -5px; background: #ef4444; color: #fff; border-radius: 50%; width: 18px; height: 18px; font-size: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 25; }
.edit-pos-btn { position: absolute; bottom: -5px; left: -5px; background: #00d2ff; color: #000; border-radius: 50%; width: 18px; height: 18px; font-size: 9px; font-weight: bold; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 25; }

.action-buttons-bar { max-width: 500px; margin: 15px auto; display: flex; gap: 10px; justify-content: space-between; }
.action-btn { flex: 1; padding: 10px; border-radius: 12px; font-family: 'Cairo'; font-weight: 900; font-size: 12px; border: 0; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; text-decoration: none; transition: 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.btn-save { background: #10b981; color: #fff; }
.btn-load { background: #3b82f6; color: #fff; }
.btn-share { background: linear-gradient(135deg, #25d366, #128c7e); color: #fff; }
.action-btn:hover { transform: translateY(-2px); opacity: 0.95; }

.tactics-board { max-width: 500px; margin: 20px auto 10px; background: #fdfdfd; color: #000; border-radius: 16px; border: 4px solid #cbd5e1; padding: 18px; box-shadow: 0 0 20px rgba(255,255,255,0.1); font-family: 'Cairo', sans-serif; }
.board-header { font-size: 16px; font-weight: 900; border-bottom: 3px solid #ef4444; padding-bottom: 6px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; color: #0f172a; }
.board-tip-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; background: #f1f5f9; padding: 8px 12px; border-radius: 10px; border-right: 4px solid #10b981; }
.board-tip-title { font-weight: 900; font-size: 13px; color: #0f172a; }
.board-tip-desc { font-size: 11px; color: #475569; margin-top: 2px; }

.modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.85); z-index: 1000; align-items: center; justify-content: center; }
.modal-content { background: #0e121d; border: 2px solid var(--neon-green); border-radius: 16px; padding: 20px; width: 90%; max-width: 400px; max-height: 80vh; overflow-y: auto; }
.search-item { display: flex; align-items: center; justify-content: space-between; background: #141a29; padding: 8px; border-radius: 8px; margin-bottom: 6px; cursor: pointer; }

.back-btn { display: block; text-align: center; margin: 20px auto; max-width: 500px; padding: 12px; background: var(--neon-green); color: #000; font-weight: 900; border-radius: 10px; text-decoration: none; }
</style>
</head>
<body>
<h2 style="text-align:center; color:var(--neon-green); margin-bottom:10px;">⚽ تكتيك الملعب وباني الفرقة</h2>

<div class="squad-controls">
  <div class="control-row">
    <div style="display:flex; flex-direction:column; gap:4px; flex-grow:1;">
      <label style="font-size:12px; font-weight:bold;">👔 اختر المدرب:</label>
      <select id="managerSelect" onchange="updateManagerPreview(); autoSave();">
        <option value="">-- اختر المدرب --</option>
        {% for m in managers %}
        <option value="{{ m['name'] }}" data-img="{{ m['image_url'] }}" data-style="{{ m['playstyle'] }}">{{ m['name'] }} ({{ m['playstyle'] }})</option>
        {% endfor %}
      </select>
    </div>
    <div class="manager-preview-box" id="managerBox">
      <img id="mImg" class="manager-preview-img">
      <div id="mInfo" style="font-size:10px; display:none;">
        <div id="mName" style="font-weight:bold; color:var(--neon-green);"></div>
        <div id="mStyle" style="color:#8fa0c0;"></div>
      </div>
    </div>
  </div>

  <div class="control-row">
    <div style="display:flex; flex-direction:column; gap:4px; flex-grow:1;">
      <label style="font-size:12px; font-weight:bold;">📋 اختر خطة اللعب (Formation):</label>
      <select id="formationSelect" onchange="changeFormation(); autoSave();">
        <option value="4-2-3-1">4-2-3-1 (المتوازنة)</option>
        <option value="3-4-3">3-4-3 (الهجومية الضغط العالي)</option>
        <option value="4-5-1">4-5-1 (التحكم والوسط)</option>
        <option value="4-4-2-diamond">4-4-2 Diamond (الجوهرة)</option>
        <option value="4-3-3">4-3-3 (الكلاسيكية)</option>
        <option value="4-4-1-1">4-4-1-1 (المهاجم الوهمي)</option>
        <option value="3-3-1-3">3-3-1-3 (الهجوم الشامل)</option>
        <option value="4-4-2">4-4-2 (الصلبة)</option>
        <option value="3-5-2">3-5-2 (الأطراف القوية)</option>
      </select>
    </div>
  </div>

  <div class="control-row">
    <div style="display:flex; flex-direction:column; gap:4px; flex-grow:1;">
      <label style="font-size:12px; font-weight:bold;">🏆 الفريق والدوري المفضل:</label>
      <select id="clubSelect" onchange="updateClubPreview(); autoSave();">
        <option value="">-- اختر الفريق --</option>
        {% for league in leagues %}
          <optgroup label="{{ league['name'] }}">
            {% for club in league['clubs'] %}
            <option value="{{ club['name'] }}" data-logo="{{ club['logo_url'] }}">{{ club['name'] }}</option>
            {% endfor %}
          </optgroup>
        {% endfor %}
      </select>
    </div>
    <div style="padding: 4px;">
      <img id="clubLogoImg" class="club-preview-img">
    </div>
  </div>

  <div class="control-row">
    <label style="font-size:12px; font-weight:bold;">❌⭕ التكتيك المفضل:</label>
    <select id="tacticSelect" onchange="updateTacticalOverlayAndBoard(); autoSave();">
      <option value="Possession">الاستحواذ (Possession Game)</option>
      <option value="Quick Counter">المرتدة السريعة (Quick Counter)</option>
      <option value="Out Wide">العرضيات (Out Wide)</option>
      <option value="Long Ball">الكرات الطويلة (Long Ball Counter)</option>
    </select>
  </div>
</div>

<div class="pitch-container" id="pitch">
  <div class="pitch-line line-center"></div>
  <div class="pitch-line line-circle"></div>

  <svg class="tactical-overlay" id="tacticalSvg" viewBox="0 0 100 100" preserveAspectRatio="none">
    <g id="overlayContent"></g>
  </svg>

  <div id="slotsContainer"></div>
</div>

<div class="action-buttons-bar">
  <button class="action-btn btn-save" onclick="saveSquad(true)">💾 حفظ التشكيلة</button>
  <button class="action-btn btn-load" onclick="loadSquad(true)">📥 تنزيل التشكيلة</button>
  <button class="action-btn btn-share" onclick="shareSquad()">🔗 مشاركة التشكيلة</button>
</div>

<div class="tactics-board">
  <div class="board-header">
    <span>📋 نصائح وتعليمات التكتيك (Tactical Tips)</span>
    <span id="boardTacticBadge" style="font-size:11px; background:#10b981; color:#fff; padding:2px 8px; border-radius:6px;">الاستحواذ</span>
  </div>
  <div id="boardTipsList"></div>
</div>

<div class="modal" id="searchModal">
  <div class="modal-content">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
      <h3 style="color:var(--neon-green); font-size:14px;">🔎 البحث عن لاعب</h3>
      <span onclick="closeSearch()" style="cursor:pointer; font-weight:bold;">❌</span>
    </div>
    <input type="text" id="modalSearchInput" placeholder="اكتب اسم اللاعب..." onkeyup="filterModalPlayers()" style="width:100%; margin-bottom:10px;">
    <div id="modalPlayersList"></div>
  </div>
</div>

<div class="modal" id="posModal">
  <div class="modal-content" style="max-width:320px; text-align:center;">
    <h3 style="color:var(--neon-green); font-size:14px; margin-bottom:12px;">⚽ تغيير مركز اللاعب</h3>
    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-bottom:15px;" id="positionsGrid">
      <button onclick="changePosition('CF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">CF</button>
      <button onclick="changePosition('SS')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">SS</button>
      <button onclick="changePosition('LWF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">LWF</button>
      <button onclick="changePosition('RWF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">RWF</button>
      <button onclick="changePosition('AMF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">AMF</button>
      <button onclick="changePosition('CMF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">CMF</button>
      <button onclick="changePosition('DMF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">DMF</button>
      <button onclick="changePosition('LMF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">LMF</button>
      <button onclick="changePosition('RMF')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">RMF</button>
      <button onclick="changePosition('LB')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">LB</button>
      <button onclick="changePosition('CB')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">CB</button>
      <button onclick="changePosition('RB')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold;">RB</button>
      <button onclick="changePosition('GK')" style="padding:8px; background:#141a29; border:1px solid #ccff00; color:#fff; border-radius:8px; cursor:pointer; font-weight:bold; grid-column:span 3;">GK</button>
    </div>
    <button onclick="closePosModal()" style="padding:8px; background:#ef4444; color:#fff; border:0; border-radius:8px; width:100%; font-weight:bold; cursor:pointer;">إلغاء</button>
  </div>
</div>

<a href="/" class="back-btn">← العودة للرئيسية</a>

<script>
let allPlayers = {{ players | tojson }};
let currentSlot = '';
let activePosSlot = '';
let squadPlayersData = {};

const FORMATIONS = {
  "4-2-3-1": [
    {id: "CF", name: "CF", top: "5%", left: "43%"},
    {id: "LWF", name: "LWF", top: "18%", left: "12%"},
    {id: "AMF", name: "AMF", top: "18%", left: "43%"},
    {id: "RWF", name: "RWF", top: "18%", left: "74%"},
    {id: "DMF1", name: "DMF", top: "38%", left: "28%"},
    {id: "DMF2", name: "DMF", top: "38%", left: "58%"},
    {id: "LB", name: "LB", top: "60%", left: "10%"},
    {id: "CB1", name: "CB", top: "62%", left: "33%"},
    {id: "CB2", name: "CB", top: "62%", left: "53%"},
    {id: "RB", name: "RB", top: "60%", left: "76%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "3-4-3": [
    {id: "LW", name: "LWF", top: "5%", left: "15%"},
    {id: "CF", name: "CF", top: "5%", left: "43%"},
    {id: "RW", name: "RWF", top: "5%", left: "71%"},
    {id: "LM", name: "LMF", top: "30%", left: "10%"},
    {id: "CM1", name: "CMF", top: "30%", left: "35%"},
    {id: "CM2", name: "CMF", top: "30%", left: "53%"},
    {id: "RM", name: "RMF", top: "30%", left: "76%"},
    {id: "CB1", name: "CB", top: "60%", left: "20%"},
    {id: "CB2", name: "CB", top: "62%", left: "43%"},
    {id: "CB3", name: "CB", top: "60%", left: "68%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "4-5-1": [
    {id: "CF", name: "CF", top: "5%", left: "43%"},
    {id: "LM", name: "LMF", top: "25%", left: "12%"},
    {id: "CM1", name: "CMF", top: "30%", left: "30%"},
    {id: "AMF", name: "AMF", top: "20%", left: "43%"},
    {id: "CM2", name: "CMF", top: "30%", left: "58%"},
    {id: "RM", name: "RMF", top: "25%", left: "74%"},
    {id: "LB", name: "LB", top: "58%", left: "10%"},
    {id: "CB1", name: "CB", top: "60%", left: "33%"},
    {id: "CB2", name: "CB", top: "60%", left: "53%"},
    {id: "RB", name: "RB", top: "58%", left: "76%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "4-4-2-diamond": [
    {id: "CF1", name: "CF", top: "5%", left: "32%"},
    {id: "CF2", name: "CF", top: "5%", left: "55%"},
    {id: "AMF", name: "AMF", top: "20%", left: "43%"},
    {id: "LM", name: "LMF", top: "38%", left: "15%"},
    {id: "DMF", name: "DMF", top: "38%", left: "43%"},
    {id: "RM", name: "RMF", top: "38%", left: "71%"},
    {id: "LB", name: "LB", top: "60%", left: "10%"},
    {id: "CB1", name: "CB", top: "62%", left: "33%"},
    {id: "CB2", name: "CB", top: "62%", left: "53%"},
    {id: "RB", name: "RB", top: "60%", left: "76%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "4-3-3": [
    {id: "LWF", name: "LWF", top: "5%", left: "15%"},
    {id: "CF", name: "CF", top: "5%", left: "43%"},
    {id: "RWF", name: "RWF", top: "5%", left: "71%"},
    {id: "CM1", name: "CMF", top: "32%", left: "22%"},
    {id: "DMF", name: "DMF", top: "36%", left: "43%"},
    {id: "CM2", name: "CMF", top: "32%", left: "64%"},
    {id: "LB", name: "LB", top: "58%", left: "10%"},
    {id: "CB1", name: "CB", top: "60%", left: "33%"},
    {id: "CB2", name: "CB", top: "60%", left: "53%"},
    {id: "RB", name: "RB", top: "58%", left: "76%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "4-4-1-1": [
    {id: "CF", name: "CF", top: "5%", left: "43%"},
    {id: "SS", name: "SS", top: "18%", left: "43%"},
    {id: "LM", name: "LMF", top: "38%", left: "12%"},
    {id: "CM1", name: "CMF", top: "38%", left: "33%"},
    {id: "CM2", name: "CMF", top: "38%", left: "53%"},
    {id: "RM", name: "RMF", top: "38%", left: "74%"},
    {id: "LB", name: "LB", top: "60%", left: "10%"},
    {id: "CB1", name: "CB", top: "62%", left: "33%"},
    {id: "CB2", name: "CB", top: "62%", left: "53%"},
    {id: "RB", name: "RB", top: "60%", left: "76%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "3-3-1-3": [
    {id: "LWF", name: "LWF", top: "5%", left: "15%"},
    {id: "CF", name: "CF", top: "5%", left: "43%"},
    {id: "RWF", name: "RWF", top: "5%", left: "71%"},
    {id: "AMF", name: "AMF", top: "22%", left: "43%"},
    {id: "CM1", name: "CMF", top: "40%", left: "22%"},
    {id: "DMF", name: "DMF", top: "42%", left: "43%"},
    {id: "CM2", name: "CMF", top: "40%", left: "64%"},
    {id: "CB1", name: "CB", top: "62%", left: "22%"},
    {id: "CB2", name: "CB", top: "64%", left: "43%"},
    {id: "CB3", name: "CB", top: "62%", left: "64%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "4-4-2": [
    {id: "CF1", name: "CF", top: "5%", left: "33%"},
    {id: "CF2", name: "CF", top: "5%", left: "53%"},
    {id: "LM", name: "LMF", top: "35%", left: "10%"},
    {id: "CM1", name: "CMF", top: "38%", left: "33%"},
    {id: "CM2", name: "CMF", top: "38%", left: "53%"},
    {id: "RM", name: "RMF", top: "35%", left: "76%"},
    {id: "LB", name: "LB", top: "60%", left: "10%"},
    {id: "CB1", name: "CB", top: "62%", left: "33%"},
    {id: "CB2", name: "CB", top: "62%", left: "53%"},
    {id: "RB", name: "RB", top: "60%", left: "76%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ],
  "3-5-2": [
    {id: "CF1", name: "CF", top: "5%", left: "33%"},
    {id: "CF2", name: "CF", top: "5%", left: "53%"},
    {id: "AMF", name: "AMF", top: "20%", left: "43%"},
    {id: "LM", name: "LMF", top: "38%", left: "10%"},
    {id: "CM1", name: "CMF", top: "40%", left: "33%"},
    {id: "CM2", name: "CMF", top: "40%", left: "53%"},
    {id: "RM", name: "RMF", top: "38%", left: "76%"},
    {id: "CB1", name: "CB", top: "62%", left: "22%"},
    {id: "CB2", name: "CB", top: "64%", left: "43%"},
    {id: "CB3", name: "CB", top: "62%", left: "64%"},
    {id: "GK", name: "GK", top: "82%", left: "43%"}
  ]
};

function changeFormation() {
  let fSelect = document.getElementById('formationSelect').value;
  let slots = FORMATIONS[fSelect] || FORMATIONS["4-2-3-1"];
  let container = document.getElementById('slotsContainer');
  
  let html = '';
  slots.forEach(s => {
    let saved = squadPlayersData[s.id];
    if(saved) {
      html += `
        <div class="pos-slot" style="top:${s.top}; left:${s.left};" id="slot_${s.id}">
          <div class="delete-btn" onclick="event.stopPropagation(); removePlayer('${s.id}')">🗑️</div>
          <div class="edit-pos-btn" onclick="openPosModal(event, '${s.id}')" title="تغيير المركز">✎</div>
          <img src="${saved.img}">
          <span id="pos_${s.id}" style="font-size:9px; color:#00d2ff; font-weight:bold;">${saved.pos}</span>
          <span style="font-size:9px; color:var(--neon-green);">${saved.overall}</span>
        </div>
      `;
    } else {
      html += `
        <div class="pos-slot" style="top:${s.top}; left:${s.left};" id="slot_${s.id}">
          <span id="pos_${s.id}">${s.name}</span><br>+
        </div>
      `;
    }
  });
  container.innerHTML = html;
  initDraggableSlots();
}

function initDraggableSlots() {
  document.querySelectorAll('.pos-slot').forEach(slot => {
    let isDragging = false;
    let startX, startY, origLeft, origTop;

    const startDrag = (e) => {
      if(e.target.classList.contains('delete-btn') || e.target.classList.contains('edit-pos-btn')) return;
      isDragging = true;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      
      startX = clientX;
      startY = clientY;
      
      const rect = slot.getBoundingClientRect();
      const pitchRect = document.getElementById('pitch').getBoundingClientRect();
      
      origLeft = rect.left - pitchRect.left;
      origTop = rect.top - pitchRect.top;
      
      slot.dataset.hasMoved = 'false';
    };

    const doDrag = (e) => {
      if (!isDragging) return;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      
      const deltaX = clientX - startX;
      const deltaY = clientY - startY;
      
      if (Math.abs(deltaX) > 4 || Math.abs(deltaY) > 4) {
        slot.dataset.hasMoved = 'true';
      }
      
      const pitch = document.getElementById('pitch');
      let newLeft = origLeft + deltaX;
      let newTop = origTop + deltaY;
      
      newLeft = Math.max(0, Math.min(newLeft, pitch.clientWidth - slot.clientWidth));
      newTop = Math.max(0, Math.min(newTop, pitch.clientHeight - slot.clientHeight));
      
      slot.style.left = newLeft + 'px';
      slot.style.top = newTop + 'px';
    };

    const stopDrag = (e) => {
      if (!isDragging) return;
      isDragging = false;
      if (slot.dataset.hasMoved === 'false') {
        openSearch(slot.id.replace('slot_', ''));
      } else {
        autoSave();
      }
    };

    slot.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);

    slot.addEventListener('touchstart', startDrag, {passive: false});
    document.addEventListener('touchmove', doDrag, {passive: false});
    document.addEventListener('touchend', stopDrag);
  });
}

const TACTICAL_CONFIG = {
  "Possession": {
    tips: [
      { title: "✅ Create Angles (خلق زوايا التمرير)", desc: "التحرك في المساحة لاستلام الكرة بوضعية جسم مفتوحة لتسهيل التمرير." },
      { title: "✅ Support Play (المساندة القريبة)", desc: "توفر خيارات تمرير قريبة من حامل الكرة لضمان الاستحواذ وعدم فقدانها." },
      { title: "✅ Find Space Between Lines (المساحات بين الخطوط)", desc: "التحرك في الثغرات بين دفاع ووسط الخصم للاستلام في مناطق خطيرة." },
      { title: "✅ Drop Deep to Collect (النزول للاستلام)", desc: "نزول لاعب الوسط لعمق الدفاع لبناء اللعب وتدوير الكرة من الخلف." }
    ],
    svg: `
      <polygon points="50,22 25,38 75,38" fill="rgba(204,255,0,0.15)" stroke="#ccff00" stroke-width="1.5" stroke-dasharray="3,3"/>
      <path d="M 25 38 Q 50 15 75 38" fill="none" stroke="#00d2ff" stroke-width="2" stroke-dasharray="4,4"/>
      <line x1="50" y1="22" x2="50" y2="10" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="2,2"/>
    `
  },
  "Quick Counter": {
    tips: [
      { title: "⚡ Make Forward Runs (الانطلاق للأمام)", desc: "الركض السريع المباشر وتجاوز خط وسط الخصم فور استعادة الكرة للتسجيل." },
      { title: "⚡ Chase Down Loose Balls (الضغط العالي السريع)", desc: "الضغط على مدافعي الخصم فوراً لاستعادة الكرة في مناطق متقدمة." },
      { title: "⚡ Fast Transitions (التحول السريع)", desc: "نقل الكرة بحد أقصى لمستين للربط السريع مع أجنحة ومهاجم الفريق." }
    ],
    svg: `
      <line x1="20" y1="60" x2="20" y2="12" stroke="#00d2ff" stroke-width="2" stroke-dasharray="3,3"/>
      <line x1="80" y1="60" x2="80" y2="12" stroke="#00d2ff" stroke-width="2" stroke-dasharray="3,3"/>
      <line x1="50" y1="40" x2="50" y2="10" stroke="#ccff00" stroke-width="2.5"/>
    `
  },
  "Out Wide": {
    tips: [
      { title: "📐 Switch Positions & Flanks (تغيير اتجاه اللعب)", desc: "تمرير الكرة للجهة العكسية لخلخلة توازن دفاع الخصم وفتح مساحات." },
      { title: "📐 Overlapping Runs (صعود الأظهيرة)", desc: "تقدم الأظهيرة LB/RB خلف الأجنحة لإرسال عرضيات متقنة للـ CF." }
    ],
    svg: `
      <path d="M 15 65 Q 5 35 20 10" fill="none" stroke="#ccff00" stroke-width="2" stroke-dasharray="3,3"/>
      <path d="M 85 65 Q 95 35 80 10" fill="none" stroke="#ccff00" stroke-width="2" stroke-dasharray="3,3"/>
    `
  },
  "Long Ball": {
    tips: [
      { title: "🚀 Second Ball Control (الكرة الثانية)", desc: "تمركُز لاعبي الوسط AM/CM لقنص الكرات المرتدة من التحامات المهاجم." },
      { title: "🚀 Direct Target Play (المهاجم المحطة)", desc: "إرسال الكرات الطويلة المباشرة للمهاجم CF لتفريغ المساحات للقادمين." }
    ],
    svg: `
      <path d="M 50 85 Q 20 45 50 10" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="4,4"/>
    `
  }
};

function updateTacticalOverlayAndBoard() {
  let tactic = document.getElementById('tacticSelect').value;
  document.getElementById('boardTacticBadge').textContent = tactic;
  
  let config = TACTICAL_CONFIG[tactic] || TACTICAL_CONFIG["Possession"];
  document.getElementById('overlayContent').innerHTML = config.svg;
  
  let html = '';
  config.tips.forEach(item => {
    html += `
      <div class="board-tip-item">
        <div>
          <div class="board-tip-title">${item.title}</div>
          <div class="board-tip-desc">${item.desc}</div>
        </div>
      </div>
    `;
  });
  document.getElementById('boardTipsList').innerHTML = html;
}

updateTacticalOverlayAndBoard();

function updateManagerPreview() {
  let select = document.getElementById('managerSelect');
  let opt = select.options[select.selectedIndex];
  let img = opt.getAttribute('data-img');
  let style = opt.getAttribute('data-style');
  
  if(opt.value) {
    document.getElementById('mImg').src = img;
    document.getElementById('mImg').style.display = 'block';
    document.getElementById('mName').textContent = opt.value;
    document.getElementById('mStyle').textContent = style;
    document.getElementById('mInfo').style.display = 'block';
    if(style && TACTICAL_CONFIG[style]) {
      document.getElementById('tacticSelect').value = style;
      updateTacticalOverlayAndBoard();
    }
  } else {
    document.getElementById('mImg').style.display = 'none';
    document.getElementById('mInfo').style.display = 'none';
  }
}

function updateClubPreview() {
  let select = document.getElementById('clubSelect');
  let opt = select.options[select.selectedIndex];
  let logo = opt.getAttribute('data-logo');
  if(opt.value && logo) {
    document.getElementById('clubLogoImg').src = logo;
    document.getElementById('clubLogoImg').style.display = 'block';
  } else {
    document.getElementById('clubLogoImg').style.display = 'none';
  }
}

function openSearch(slotId) {
  currentSlot = slotId;
  document.getElementById('searchModal').style.display = 'flex';
  renderModalPlayers(allPlayers);
}

function closeSearch() { document.getElementById('searchModal').style.display = 'none'; }

function openPosModal(event, slotId) {
  event.stopPropagation();
  activePosSlot = slotId;
  document.getElementById('posModal').style.display = 'flex';
}

function closePosModal() {
  document.getElementById('posModal').style.display = 'none';
}

function changePosition(newPos) {
  if(activePosSlot) {
    let posSpan = document.getElementById('pos_' + activePosSlot);
    if(posSpan) posSpan.textContent = newPos;
    if(squadPlayersData[activePosSlot]) {
      squadPlayersData[activePosSlot].pos = newPos;
    }
    autoSave();
  }
  closePosModal();
}

function renderModalPlayers(list) {
  let html = '';
  list.forEach(p => {
    html += `
      <div class="search-item" onclick="selectPlayer('${p.name}', '${p.image_url}', '${p.overall_max}', '${p.position}')">
        <div style="display:flex; align-items:center; gap:8px;">
          <img src="${p.image_url}" style="width:30px; height:30px; object-fit:cover; border-radius:4px;">
          <div>
            <div style="font-size:12px; font-weight:bold;">${p.name}</div>
            <div style="font-size:9px; color:#8fa0c0;">${p.position}</div>
          </div>
        </div>
        <div style="color:var(--neon-green); font-weight:bold;">${p.overall_max}</div>
      </div>
    `;
  });
  document.getElementById('modalPlayersList').innerHTML = html || '<div style="font-size:12px; color:#888;">لا يوجد لاعبين</div>';
}

function filterModalPlayers() {
  let q = document.getElementById('modalSearchInput').value.toLowerCase();
  let filtered = allPlayers.filter(p => p.name.toLowerCase().includes(q));
  renderModalPlayers(filtered);
}

function selectPlayer(name, img, overall, defaultPos) {
  squadPlayersData[currentSlot] = {img: img, overall: overall, pos: defaultPos};
  let slot = document.getElementById('slot_' + currentSlot);
  slot.innerHTML = `
    <div class="delete-btn" onclick="event.stopPropagation(); removePlayer('${currentSlot}')">🗑️</div>
    <div class="edit-pos-btn" onclick="openPosModal(event, '${currentSlot}')" title="تغيير المركز">✎</div>
    <img src="${img}">
    <span id="pos_${currentSlot}" style="font-size:9px; color:#00d2ff; font-weight:bold;">${defaultPos}</span>
    <span style="font-size:9px; color:var(--neon-green);">${overall}</span>
  `;
  closeSearch();
  autoSave();
}

function removePlayer(slotId) {
  delete squadPlayersData[slotId];
  let slot = document.getElementById('slot_' + slotId);
  slot.innerHTML = `<span id="pos_${slotId}">${slotId.replace(/[0-9]/g, '')}</span><br>+`;
  autoSave();
}

function autoSave() {
  let squadData = {
    manager: document.getElementById('managerSelect').value,
    formation: document.getElementById('formationSelect').value,
    club: document.getElementById('clubSelect').value,
    tactic: document.getElementById('tacticSelect').value,
    players: squadPlayersData
  };
  let jsonStr = JSON.stringify(squadData);
  localStorage.setItem('nova_saved_squad', jsonStr);

  fetch('/api/save-squad', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: jsonStr
  }).catch(() => {});
}

function saveSquad(showAlert = false) {
  autoSave();
  if(showAlert) alert('💾 تم حفظ التشكيلة بدقة وفي قاعدة البيانات للرجوع إليها دائماً!');
}

function loadSquad(showAlert = false) {
  fetch('/api/get-squad')
    .then(r => r.json())
    .then(data => {
      let squadData = data;
      if(!squadData || !squadData.formation) {
        let saved = localStorage.getItem('nova_saved_squad');
        if(saved) squadData = JSON.parse(saved);
      }
      if(squadData && squadData.formation) {
        if(squadData.manager) document.getElementById('managerSelect').value = squadData.manager;
        if(squadData.formation) document.getElementById('formationSelect').value = squadData.formation;
        if(squadData.club) document.getElementById('clubSelect').value = squadData.club;
        if(squadData.tactic) document.getElementById('tacticSelect').value = squadData.tactic;

        updateManagerPreview();
        updateClubPreview();
        updateTacticalOverlayAndBoard();

        squadPlayersData = squadData.players || {};
        changeFormation();
        if(showAlert) alert('📥 تم تحميل التشكيلة المحفوظة بنجاح!');
      } else if(showAlert) {
        alert('⚠️ لا توجد تشكيلة محفوظة مسبقاً!');
      }
    }).catch(() => {
      let saved = localStorage.getItem('nova_saved_squad');
      if(saved) {
        let squadData = JSON.parse(saved);
        if(squadData.manager) document.getElementById('managerSelect').value = squadData.manager;
        if(squadData.formation) document.getElementById('formationSelect').value = squadData.formation;
        if(squadData.club) document.getElementById('clubSelect').value = squadData.club;
        if(squadData.tactic) document.getElementById('tacticSelect').value = squadData.tactic;
        updateManagerPreview(); updateClubPreview(); updateTacticalOverlayAndBoard();
        squadPlayersData = squadData.players || {};
        changeFormation();
        if(showAlert) alert('📥 تم تحميل التشكيلة المحفوظة بنجاح!');
      }
    });
}

function shareSquad() {
  let formation = document.getElementById('formationSelect').value;
  let manager = document.getElementById('managerSelect').value || 'بدون مدرب';
  let tactic = document.getElementById('tacticSelect').value;
  let text = `⚽ تشكيلتي في لعبة eFootball عبر تطبيق NOVA eHUB 26:\n📋 الخطة: ${formation}\n👔 المدرب: ${manager}\n⚡ التكتيك: ${tactic}\n🔥 أنشئ تشكيلتك الآن وانضم إلينا!`;
  
  if (navigator.share) {
    navigator.share({
      title: 'تشكيلتي في eFootball',
      text: text,
      url: window.location.href
    }).catch(() => {});
  } else {
    let encoded = encodeURIComponent(text);
    let choice = confirm('مشاركة عبر واتساب؟ (اضغط Cancel لتيليجرام)');
    if(choice) {
      window.open(`https://api.whatsapp.com/send?text=${encoded}`, '_blank');
    } else {
      window.open(`https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encoded}`, '_blank');
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  loadSquad(false);
});
</script>
</body>
</html>
"""


ACCOUNT_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>الملف الشخصي | NOVA eHUB 26</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --neon-blue: #00d2ff; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; display: grid; place-items: center; min-height: 100vh; margin: 0; padding: 20px; }
.profile-card { background: linear-gradient(145deg, #0e121d, #07090e); border: 2px solid var(--neon-green); border-radius: 24px; width: 100%; max-width: 440px; padding: 35px 25px; text-align: center; box-shadow: 0 0 30px rgba(204, 255, 0, 0.2); position: relative; }
.avatar-ring { width: 95px; height: 95px; background: #141a29; border: 3px solid var(--neon-green); border-radius: 50%; margin: 0 auto 15px; display: grid; place-items: center; font-size: 40px; color: var(--neon-green); box-shadow: 0 0 15px rgba(204,255,0,0.4); }
.user-name { font-size: 22px; font-weight: 900; color: #fff; margin-bottom: 4px; }
.user-badge { background: #141a29; border: 1px solid var(--neon-blue); color: var(--neon-blue); padding: 3px 12px; border-radius: 12px; font-size: 11px; font-weight: 800; display: inline-block; margin-bottom: 20px; }
.info-box { background: #0e1320; border: 1px solid var(--border-color); border-radius: 14px; padding: 16px; text-align: right; margin-bottom: 20px; }
.info-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1e2638; font-size: 13px; }
.info-item:last-child { border: 0; }
.btn-home { display: block; width: 100%; padding: 12px; background: var(--neon-green); color: #000; border-radius: 12px; font-weight: 900; text-decoration: none; font-size: 13px; margin-bottom: 10px; }
.btn-logout { display: block; width: 100%; padding: 10px; background: #ef4444; color: #fff; border-radius: 12px; font-weight: bold; text-decoration: none; font-size: 12px; }
</style>
</head>
<body>
<div class="profile-card">
  <div class="avatar-ring">👤</div>
  <div class="user-name">{{ user["name"] }}</div>
  <div class="user-badge">⭐ حساب موثق رسمي</div>

  <div class="info-box">
    <div class="info-item"><span style="color:#94a3b8;">البريد الإلكتروني:</span> <b>{{ user["email"] }}</b></div>
    <div class="info-item"><span style="color:#94a3b8;">حالة التوثيق:</span> <b style="color:var(--neon-green);">مفعل ✅</b></div>
    <div class="info-item"><span style="color:#94a3b8;">الرتبة في التطبيق:</span> <b style="color:var(--neon-blue);">عضو مميز VIP</b></div>
  </div>

  <a href="/" class="btn-home">← العودة للصفحة الرئيسية</a>
  <a href="/logout" class="btn-logout">تسجيل الخروج 🚪</a>
</div>
</body>
</html>
"""


MANAGERS_LIST_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>جميع المدربين | NOVA eHUB 26</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 25px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-top: 20px; }
.card { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 16px; padding: 15px; text-align: center; text-decoration: none; color: inherit; display: block; }
.card img { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid var(--neon-green); margin-bottom: 10px; }
.back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 18px; background: #141a29; border: 1px solid var(--border-color); color: #fff; border-radius: 8px; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<a href="/" class="back-btn">← العودة للرئيسية</a>
<h2 style="color:var(--neon-green);">👔 جميع المدربين المتاحين في التطبيق</h2>
<div class="grid">
  {% for m in managers %}
  <a href="/manager/{{ m['id'] }}" class="card">
    <img src="{{ m['image_url'] }}" onerror="this.src='https://via.placeholder.com/90/121826/ccff00?text=Coach'">
    <h3 style="font-size:15px; color:#fff; margin-bottom:4px;">{{ m['name'] }}</h3>
    <p style="font-size:11px; color:#00d2ff;">أسلوب اللعب: {{ m['playstyle'] }}</p>
    <p style="font-size:11px; color:#ccff00; margin-top:4px;">Affinity: {{ m['affinity'] }}</p>
  </a>
  {% endfor %}
</div>
</body>
</html>
"""


PLAYER_DETAIL_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ player['name'] }} | eFHUB Full Stats</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 15px; }
.efhub-layout { max-width: 1000px; margin: auto; display: grid; grid-template-columns: 320px 1fr; gap: 20px; }
@media(max-width: 850px) { .efhub-layout { grid-template-columns: 1fr; } }
.card-box { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 16px; padding: 20px; text-align: center; }
.card-img-large { width: 190px; height: 230px; object-fit: cover; margin: 10px auto; border-radius: 12px; background: #121826; border: 2px solid var(--neon-green); padding: 5px; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.section-box { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 14px; padding: 15px; }
.section-header { font-size: 13px; font-weight: 900; color: #8fa0c0; margin-bottom: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 4px; }
.stat-row-ef { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #141a29; font-size: 12px; font-weight: 700; }
.stat-val-badge { padding: 3px 8px; border-radius: 6px; font-weight: 900; font-size: 13px; min-width: 38px; text-align: center; color: #000; background: #ccff00; }
.skills-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.skill-tag { background: #141a29; border: 1px solid #229ed9; color: #00d2ff; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
.back-btn { display: block; text-align: center; margin-top: 20px; padding: 12px; background: var(--neon-green); color: #000; font-weight: 900; border-radius: 10px; text-decoration: none; grid-column: 1 / -1; }
</style>
</head>
<body>
<div class="efhub-layout">
  <div class="card-box">
    <h2 style="color:var(--neon-green); font-size:24px; font-weight:900;">{{ player['name'] }}</h2>
    <p style="font-size:12px; color:#94a3b8; margin-top:4px;">{{ player['team'] }} | المركز: <b style="color:#00d2ff;">{{ player['position'] }}</b></p>
    <img class="card-img-large" src="{{ player['image_url'] }}" onerror="this.src='https://via.placeholder.com/150/121826/ccff00?text=eFootball'">
    <p style="font-size:11px; color:#38bdf8; margin-top:8px;">نوع البطاقة: {{ player['card_type'] }}</p>
    <p style="font-size:14px; font-weight:bold; margin-top:6px;">Max Overall: <span style="color:var(--neon-green); font-size:18px;">{{ player['overall_max'] }}</span></p>
  </div>
  <div>
    <div class="stats-grid">
      <div class="section-box">
        <div class="section-header">🔥 مهاجمة (Attacking)</div>
        <div id="attackingStats"></div>
      </div>
      <div class="section-box">
        <div class="section-header">🛡️ الدفاع (Defending)</div>
        <div id="defendingStats"></div>
      </div>
    </div>
    <div class="section-box" style="margin-top:15px;">
      <div class="section-header">✨ مهارات اللاعب (Skills)</div>
      <div class="skills-list" id="skillsList"></div>
    </div>
  </div>
  <a href="/" class="back-btn">← العودة للرئيسية</a>
</div>
<script>
let fullStats = {{ player['stats_json'] | safe }};
let skills = {{ player['skills_json'] | safe }};
function renderSection(obj, containerId) {
  let html = '';
  for(let key in obj) {
    let val = obj[key];
    html += `<div class="stat-row-ef"><span style="color:#cbd5e1;">${key}</span><span class="stat-val-badge">${val}</span></div>`;
  }
  document.getElementById(containerId).innerHTML = html || '<div style="font-size:11px;color:#666;">غير متاح</div>';
}
renderSection(fullStats.attacking || {}, 'attackingStats');
renderSection(fullStats.defending || {}, 'defendingStats');
let skillsHtml = '';
if(Array.isArray(skills) && skills.length > 0) { skills.forEach(s => { skillsHtml += `<span class="skill-tag">⚡ ${s}</span>`; }); }
document.getElementById('skillsList').innerHTML = skillsHtml || '<span style="font-size:11px;color:#888;">لا توجد مهارات</span>';
</script>
</body>
</html>
"""


SKILLS_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>المهارات الجديدة | NOVA eHUB 26</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 25px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin-top: 20px; }
.card { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 14px; padding: 15px; text-align: center; }
.card img { width: 60px; height: 60px; object-fit: cover; margin-bottom: 10px; border-radius:8px; }
.back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 16px; background: #141a29; border: 1px solid var(--border-color); color: #fff; border-radius: 8px; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<a href="/" class="back-btn">← العودة للرئيسية</a>
<h2 style="color:var(--neon-green);">⚡ قائمة المهارات الجديدة في eFootball</h2>
<div class="grid">
  {% for s in skills %}
  <div class="card">
    <img src="{{ s['image_url'] }}" onerror="this.src='https://via.placeholder.com/60/121826/ccff00?text=Skill'">
    <h3 style="font-size:14px; color:#fff; margin-bottom:6px;">{{ s['name'] }}</h3>
    <p style="font-size:11px; color:#94a3b8;">{{ s['description'] }}</p>
  </div>
  {% endfor %}
</div>
</body>
</html>
"""


@app.route('/api/save-squad', methods=['POST'])
def api_save_squad():
    email = session.get('user_email', 'guest')
    data = request.get_json(silent=True) or {}
    squad_json = json.dumps(data)
    with get_db() as db:
        db.execute("INSERT INTO saved_squads (user_email, squad_json, updated_at) VALUES (?, ?, ?)",
                   (email, squad_json, int(time.time())))
        db.commit()
    return jsonify({"status": "success"})


@app.route('/api/get-squad')
def api_get_squad():
    email = session.get('user_email', 'guest')
    with get_db() as db:
        res = db.execute("SELECT squad_json FROM saved_squads WHERE user_email = ? ORDER BY id DESC LIMIT 1", (email,)).fetchone()
        if res:
            return Response(res['squad_json'], mimetype='application/json')
    return jsonify({})


@app.route('/squad-builder')
def squad_builder():
    with get_db() as db:
        db_players = [dict(row) for row in db.execute("SELECT name, position, overall_max, image_url FROM players").fetchall()]
        managers = [dict(row) for row in db.execute("SELECT name, playstyle, image_url FROM managers").fetchall()]
    
    classic_players = get_classic_players()
    all_players_combined = db_players + classic_players
    leagues = get_all_leagues()
    return render_template_string(SQUAD_BUILDER_TEMPLATE, players=all_players_combined, managers=managers, leagues=leagues)


@app.route('/managers')
def managers_page():
    with get_db() as db:
        managers = db.execute("SELECT * FROM managers ORDER BY id DESC").fetchall()
    return render_template_string(MANAGERS_LIST_TEMPLATE, managers=managers)


@app.route('/manager/<int:manager_id>')
def manager_detail(manager_id):
    with get_db() as db:
        manager = db.execute("SELECT * FROM managers WHERE id = ?", (manager_id,)).fetchone()
    if not manager: return "المدرب غير موجود", 404
    return render_template_string(MANAGER_DETAIL_TEMPLATE, manager=manager)


@app.route('/player-stats/<int:player_id>')
def player_stats_page(player_id):
    with get_db() as db:
        player = db.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    
    if not player:
        classic_players = get_classic_players()
        for cp in classic_players:
            if cp["id"] == player_id:
                player = cp
                break
                
    if not player: return "اللاعب غير موجود", 404
    return render_template_string(PLAYER_STATS_TEMPLATE, player=player)


@app.route('/player/<int:player_id>')
def player_detail(player_id):
    with get_db() as db:
        player = db.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    
    if not player:
        classic_players = get_classic_players()
        for cp in classic_players:
            if cp["id"] == player_id:
                player = cp
                break
    
    if not player: return "اللاعب غير موجود", 404
    return render_template_string(PLAYER_DETAIL_TEMPLATE, player=player)


@app.route('/skills')
def skills_page():
    with get_db() as db:
        skills = db.execute("SELECT * FROM skills ORDER BY id DESC").fetchall()
    return render_template_string(SKILLS_TEMPLATE, skills=skills)


@app.route('/register', methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if name and email and password:
            with get_db() as db:
                try:
                    code = f"{secrets.randbelow(1000000):06d}"
                    send_verification_code_to_channel(email, code)
                    db.execute("INSERT INTO users (name, email, password_hash, verified, created_at) VALUES (?, ?, ?, 1, ?)", 
                               (name, email, generate_password_hash(password), int(time.time())))
                    db.commit()
                    session["user_email"] = email
                    return redirect(url_for("home"))
                except Exception: error = "البريد الإلكتروني مسجل مسبقاً."
        else: error = "يرجى تعبئة جميع الحقول."
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إنشاء حساب</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#0e121d;padding:30px;border:2px solid #ccff00;border-radius:18px;width:380px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2 style="color:#ccff00;">إنشاء حساب جديد</h2>
    <form method="post"><input name='name' placeholder='الاسم الكامل' required><input type='email' name='email' placeholder='البريد الإلكتروني' required><input type='password' name='password' placeholder='كلمة المرور' required><button type="submit">إنشاء الحساب ودخول التطبيق</button></form>
    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/login" style="color:#00d2ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">تسجيل الدخول</a>
    </div></body></html>
    """


@app.route('/login', methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_email"] = email
            return redirect(url_for("home"))
        error = "بيانات الدخول غير صحيحة."
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>تسجيل الدخول</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#0e121d;padding:30px;border:2px solid #ccff00;border-radius:18px;width:380px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2 style="color:#ccff00;">تسجيل الدخول</h2>
    <form method="post"><input type="email" name="email" placeholder="البريد الإلكتروني" required><input type="password" name="password" placeholder="كلمة المرور" required><button type="submit">دخول</button></form>
    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/register" style="color:#00d2ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">حساب جديد</a>
    </div></body></html>
    """


@app.route('/account')
def account():
    email = session.get("user_email")
    if not email: return redirect(url_for("login"))
    with get_db() as db: user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return render_template_string(ACCOUNT_TEMPLATE, user=user)


@app.route('/logout')
def logout():
    session.pop("user_email", None)
    return redirect(url_for("home"))


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    msg = ""
    if request.method == "POST" and request.form.get("login_admin"):
        if request.form.get("email") == ADMIN_EMAIL and request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
        else: msg = "بيانات دخول المطور غير صحيحة."

    if not session.get("is_admin"):
        return f"""
        <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>دخول المطور</title>
        <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
        .box{{background:#0e121d;padding:30px;border:1px solid #ccff00;border-radius:18px;width:360px;text-align:center;}}
        input{{width:100%;padding:12px;margin:8px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
        button{{width:100%;padding:12px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;}}
        </style></head>
        <body><div class="box">
        <h2>🔐 دخول لوحة المطور المحمية</h2>
        <form method="post"><input type="hidden" name="login_admin" value="1"><input type="email" name="email" placeholder="بريد المطور" required><input type="password" name="password" placeholder="كلمة المرور" required><button type="submit">دخول اللوحة</button></form>
        <p style="color:#ff7777;font-size:12px;">{msg}</p>
        <a href="/" style="color:#ccff00;font-size:12px;text-decoration:none;">← العودة للتطبيق</a>
        </div></body></html>
        """

    with get_db() as db:
        if request.method == "POST":
            action = request.form.get("action")

            if action == "send_news":
                title = request.form.get("title")
                content = request.form.get("content")
                db.execute("INSERT INTO news (title, content, created_at) VALUES (?, ?, ?)", (title, content, int(time.time())))
                db.commit()
                msg = "✅ تم إرسال الرسالة والإشعار بنجاح!"

            elif action == "upload_banner":
                file = request.files.get("banner_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    banner_url = url_for('static', filename=f'uploads/{filename}')
                    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('custom_banner', ?)", (banner_url,))
                    db.commit()
                    msg = "✅ تم تحديث وعرض بانر الصفحة الرئيسية بنجاح!"

            elif action == "upload_managers_card":
                file = request.files.get("card_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img_url = url_for('static', filename=f'uploads/{filename}')
                    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('managers_card_img', ?)", (img_url,))
                    db.commit()
                    msg = "✅ تم تحديث لوجو كارت قائمة المدربين بنجاح!"

            elif action == "add_skill":
                name = request.form.get("name")
                desc = request.form.get("desc")
                img_url = "https://via.placeholder.com/60/121826/ccff00?text=Skill"
                file = request.files.get("skill_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img_url = url_for('static', filename=f'uploads/{filename}')
                db.execute("INSERT INTO skills (name, description, image_url) VALUES (?, ?, ?)", (name, desc, img_url))
                db.commit()
                msg = "✅ تم إضافة المهارة الجديدة بنجاح!"

            elif action == "add_manager":
                name = request.form.get("name")
                age = int(request.form.get("age", 50))
                team = request.form.get("team", "Free Agent")
                style = request.form.get("playstyle")
                affinity = int(request.form.get("affinity", 85))
                file = request.files.get("image_file")
                img_url = "https://via.placeholder.com/90/121826/ccff00?text=Coach"
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img_url = url_for('static', filename=f'uploads/{filename}')
                db.execute("INSERT INTO managers (name, age, team, playstyle, affinity, image_url) VALUES (?, ?, ?, ?, ?, ?)", 
                           (name, age, team, style, affinity, img_url))
                db.commit()
                msg = "✅ تم إضافة المدرب بتفاصيله الكاملة!"

            elif action == "delete_manager":
                m_id = request.form.get("manager_id")
                db.execute("DELETE FROM managers WHERE id = ?", (m_id,))
                db.commit()
                msg = "🗑️ تم حذف المدرب بنجاح!"

            elif action == "add_player":
                name = request.form.get("name")
                overall_base = int(request.form.get("overall_base", 80))
                overall_max = int(request.form.get("overall_max", 90))
                position = request.form.get("position")
                team = request.form.get("team")
                card_type = request.form.get("card_type")
                is_upcoming = 1 if request.form.get("is_upcoming") else 0

                height = int(request.form.get("height", 180))
                weight = int(request.form.get("weight", 75))
                age = int(request.form.get("age", 25))
                stamina = int(request.form.get("stamina", 80))

                image_url = ""
                file = request.files.get("image_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = url_for('static', filename=f'uploads/{filename}')
                else: image_url = "https://via.placeholder.com/150/121826/ccff00?text=eFootball"

                full_stats = {
                    "attacking": {"وعي هجومي": int(request.form.get("att_awareness", 80)), "المراوغة": int(request.form.get("dribbling", 80)), "إنهاء الهجمة": int(request.form.get("finishing", 80))},
                    "physical": {"السرعة": int(request.form.get("speed", 85)), "قوة التحمل": stamina},
                    "defending": {"وعي دفاعي": int(request.form.get("def_awareness", 85)), "قطع الكرة": int(request.form.get("tackling", 85))}
                }
                db.execute("""
                    INSERT INTO players (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, height, weight, age, stamina, stats_json, skills_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, height, weight, age, stamina, json.dumps(full_stats), json.dumps([])))
                db.commit()
                msg = "✅ تم إضافة اللاعب بنجاح!"

            elif action == "delete_player":
                p_id = request.form.get("player_id")
                db.execute("DELETE FROM players WHERE id = ?", (p_id,))
                db.commit()
                msg = "🗑️ تم حذف اللاعب بنجاح!"

            elif action == "update_downloads":
                new_val = request.form.get("downloads_val")
                db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('total_downloads_count', ?)", (new_val,))
                db.commit()
                msg = "📊 تم تحديث عدد تنزيلات وتحميلات التطبيق بنجاح!"

    with get_db() as db:
        users_cnt = db.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
        players_cnt = db.execute("SELECT COUNT(*) as c FROM players").fetchone()['c']
        managers_cnt = db.execute("SELECT COUNT(*) as c FROM managers").fetchone()['c']
        squads_cnt = db.execute("SELECT COUNT(*) as c FROM saved_squads").fetchone()['c']
        downloads_res = db.execute("SELECT value FROM settings WHERE key = 'total_downloads_count'").fetchone()
        downloads_val = downloads_res['value'] if downloads_res else "1420"

        all_players = db.execute("SELECT id, name, position, card_type FROM players ORDER BY id DESC").fetchall()
        all_managers = db.execute("SELECT id, name, playstyle FROM managers ORDER BY id DESC").fetchall()

    players_options = "".join([f"<option value='{p['id']}'>{p['name']} ({p['position']} - {p['card_type']})</option>" for p in all_players])
    managers_options = "".join([f"<option value='{m['id']}'>{m['name']} ({m['playstyle']})</option>" for m in all_managers])

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>لوحة المطور</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;padding:30px;}}
    .box{{background:#0e121d;padding:20px;border:1px solid #ccff00;border-radius:14px;max-width:550px;margin:0 auto 20px;}}
    .stats-grid-admin{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:15px;}}
    .stat-card-admin{{background:#141a29;border:1px solid #00d2ff;border-radius:10px;padding:12px;text-align:center;}}
    input, textarea, select{{width:100%;padding:10px;margin:6px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;font-family:Cairo;}}
    button{{padding:10px 20px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;}}
    </style></head>
    <body><div style="max-width:550px;margin:auto;">
    <h2 style="color:#ccff00;">⚙️ لوحة تحكم المطور الحصرية</h2>
    <p style="color:#35eaa1;font-weight:bold;">{msg}</p>

    <!-- زر وقسم إحصائيات التطبيق والتحميلات -->
    <div class="box" style="border-color:#00d2ff;">
      <h3 style="color:#00d2ff;margin-bottom:12px;">📊 إحصائيات التطبيق والتحميلات الحقيقية</h3>
      <div class="stats-grid-admin">
        <div class="stat-card-admin"><div style="font-size:11px;color:#8fa0c0;">إجمالي المستخدمين</div><div style="font-size:20px;font-weight:bold;color:#ccff00;">{users_cnt}</div></div>
        <div class="stat-card-admin"><div style="font-size:11px;color:#8fa0c0;">إجمالي اللاعبين</div><div style="font-size:20px;font-weight:bold;color:#00d2ff;">{players_cnt}</div></div>
        <div class="stat-card-admin"><div style="font-size:11px;color:#8fa0c0;">إجمالي المدربين</div><div style="font-size:20px;font-weight:bold;color:#ccff00;">{managers_cnt}</div></div>
        <div class="stat-card-admin"><div style="font-size:11px;color:#8fa0c0;">التشكيلات المحفوظة</div><div style="font-size:20px;font-weight:bold;color:#00d2ff;">{squads_cnt}</div></div>
      </div>
      <form method="post" style="margin-top:10px;">
        <input type="hidden" name="action" value="update_downloads">
        <label style="font-size:12px;">📲 عدد التنزيلات/التحميلات الظاهر:</label>
        <input name="downloads_val" value="{downloads_val}" placeholder="عدد التحميلات" required>
        <button type="submit" style="margin-top:6px;width:100%;background:#00d2ff;color:#000;">تحديث عداد التحميلات 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>📢 إرسال رسالة أو إشعار لجميع المستخدمين</h3>
      <form method="post">
        <input type="hidden" name="action" value="send_news">
        <input name="title" placeholder="عنوان الرسالة / التنبيه" required>
        <textarea name="content" placeholder="محتوى الرسالة..." rows="3" required></textarea>
        <button type="submit" style="margin-top:10px;">إرسال للجميع 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>🖼️ رفع وتحديث بانر الصفحة الرئيسية</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload_banner">
        <input type="file" name="banner_file" accept="image/*" required>
        <button type="submit" style="margin-top:10px;">حفظ وعرض البانر 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>🖼️ رفع وتحديث لوجو كارت "قائمة المدربين"</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload_managers_card">
        <input type="file" name="card_file" accept="image/*" required>
        <button type="submit" style="margin-top:10px;">حفظ وتحديث الصورة 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>👔 إضافة مدرب جديد بكامل تفاصيله</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_manager">
        <input name="name" placeholder="اسم المدرب" required>
        <input type="number" name="age" placeholder="السن / العمر" value="50" required>
        <input name="team" placeholder="الفريق / الجنسية (مثال: Germany / Liverpool)" required>
        <input name="playstyle" placeholder="أسلوب اللعب (مثال: Quick Counter)" required>
        <input type="number" name="affinity" placeholder="قوة التوافقية (Affinity)" value="85" required>
        <input type="file" name="image_file" accept="image/*">
        <button type="submit" style="margin-top:10px;">حفظ وإضافة المدرب 🚀</button>
      </form>
    </div>

    <div class="box" style="border-color:#ef4444;">
      <h3 style="color:#ef4444;">🗑️ حذف مدرب من قاعدة البيانات</h3>
      <form method="post">
        <input type="hidden" name="action" value="delete_manager">
        <select name="manager_id" required>
          <option value="">اختر المدرب للحذف...</option>
          {managers_options}
        </select>
        <button type="submit" style="background:#ef4444;color:#fff;margin-top:10px;">حذف المدرب ❌</button>
      </form>
    </div>

    <div class="box">
      <h3>⚡ إضافة مهارة جديدة مع الاسم، الوصف والصورة</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_skill">
        <input name="name" placeholder="اسم المهارة (مثال: Double Touch)" required>
        <textarea name="desc" placeholder="وصف المهارة وكيفية تنفيذها..." rows="2" required></textarea>
        <input type="file" name="skill_file" accept="image/*">
        <button type="submit" style="margin-top:10px;">حفظ وإضافة المهارة 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>⚽ إضافة لاعب جديد مع خصائصه الفيزيائية</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_player">
        <input name="name" placeholder="اسم اللاعب" required>
        <input type="number" name="overall_base" placeholder="الطاقة الأساسية" required>
        <input type="number" name="overall_max" placeholder="الطاقة القصوى" required>
        <input name="position" placeholder="المركز (مثال: CB)" required>
        <input name="team" placeholder="النادي / الفريق" required>
        <div style="display:flex;gap:6px;">
          <input type="number" name="height" placeholder="الطول (سم)" value="180">
          <input type="number" name="weight" placeholder="الوزن (كجم)" value="75">
          <input type="number" name="age" placeholder="العمر" value="25">
        </div>
        <input type="number" name="stamina" placeholder="مستوى اللياقة (%)" value="80">
        <select name="card_type">
          <option value="Epic / Big Time">Epic / Big Time</option>
          <option value="Showtime">Showtime</option>
          <option value="Highlight">Highlight</option>
        </select>
        <label><input type="checkbox" name="is_upcoming" value="1"> لاعب تسريبات (Upcoming)</label>
        <input type="file" name="image_file" accept="image/*">
        <button type="submit" style="margin-top:10px;">حفظ وإضافة اللاعب 🚀</button>
      </form>
    </div>

    <div class="box" style="border-color:#ef4444;">
      <h3 style="color:#ef4444;">🗑️ حذف لاعب من قاعدة البيانات</h3>
      <form method="post">
        <input type="hidden" name="action" value="delete_player">
        <select name="player_id" required>
          <option value="">اختر اللاعب للحذف...</option>
          {players_options}
        </select>
        <button type="submit" style="background:#ef4444;color:#fff;margin-top:10px;">حذف اللاعب نهائياً ❌</button>
      </form>
    </div>

    <a href="/" style="color:#00d2ff;text-decoration:none;">← العودة للتطبيق</a>
    </div></body></html>
    """


@app.route("/")
def home():
    email = session.get("user_email")
    user = None
    if email:
        with get_db() as db: user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    with get_db() as db:
        db_players = [dict(row) for row in db.execute("SELECT * FROM players ORDER BY overall_max DESC").fetchall()]
        news = [dict(row) for row in db.execute("SELECT * FROM news ORDER BY id DESC LIMIT 5").fetchall()]
        managers = [dict(row) for row in db.execute("SELECT * FROM managers ORDER BY id DESC").fetchall()]
        banner_res = db.execute("SELECT value FROM settings WHERE key = 'custom_banner'").fetchone()
        m_card_res = db.execute("SELECT value FROM settings WHERE key = 'managers_card_img'").fetchone()
        
        custom_banner = banner_res["value"] if banner_res else ""
        managers_card_img = m_card_res["value"] if m_card_res else ""

    classic_players = get_classic_players()
    all_players_combined = db_players + classic_players

    return render_template_string(
        HOME_TEMPLATE,
        players=all_players_combined,
        news=news,
        managers=managers,
        custom_banner=custom_banner,
        managers_card_img=managers_card_img,
        user=user,
        telegram_dev=TELEGRAM_DEV,
        telegram_main=TELEGRAM_MAIN,
        telegram_bot=TELEGRAM_BOT,
        telegram_codes_channel=TELEGRAM_CODES_CHANNEL
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
