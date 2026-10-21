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
                playstyle TEXT NOT NULL,
                affinity INTEGER NOT NULL DEFAULT 85,
                image_url TEXT NOT NULL
            )
        """)

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
                stats_json TEXT NOT NULL,
                skills_json TEXT NOT NULL
            )
        """)

        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('custom_banner', '')")
        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('managers_card_img', '')")

        # إضافة أخبار افتراضية
        cursor_n = db.execute("SELECT COUNT(*) as count FROM news")
        if cursor_n.fetchone()["count"] == 0:
            db.execute("INSERT INTO news (title, content, created_at) VALUES (?, ?, ?)", 
                       ("تحديث صيانة الخميس القادم", "وصول بطاقات Epic جديدة وتسريبات قوية لميسي ورونالدو.", int(time.time())))

        # إضافة مدربين افتراضيين
        cursor_m = db.execute("SELECT COUNT(*) as count FROM managers")
        if cursor_m.fetchone()["count"] == 0:
            db.execute("INSERT INTO managers (name, playstyle, affinity, image_url) VALUES (?, ?, ?, ?)",
                       ("Jürgen Klopp", "Quick Counter", 88, "https://via.placeholder.com/150/121826/ccff00?text=Klopp"))
            db.execute("INSERT INTO managers (name, playstyle, affinity, image_url) VALUES (?, ?, ?, ?)",
                       ("Cristian Chivu", "Possession Game", 85, "https://via.placeholder.com/150/121826/ccff00?text=Chivu"))
            db.execute("INSERT INTO managers (name, playstyle, affinity, image_url) VALUES (?, ?, ?, ?)",
                       ("R. Rodriguez", "Out Wide", 83, "https://via.placeholder.com/150/121826/ccff00?text=Rodriguez"))

        # إضافة لاعبي الأساطير بالكامل مع الطاقات المفصلة
        cursor_p = db.execute("SELECT COUNT(*) as count FROM players")
        if cursor_p.fetchone()["count"] == 0:
            varane_stats = {
                "attacking": {"وعي هجومي": 52, "التحكم في الكرة": 66, "المراوغة": 70, "إنهاء الهجمة": 50, "مهارة الرأس": 79},
                "physical": {"السرعة": 81, "التسارع": 76, "القفز": 78, "الالتحام الجسدي": 80, "قوة التحمل": 74},
                "defending": {"وعي دفاعي": 88, "احتكاك دفاعي": 88, "قطع الكرة": 87, "الشراسة": 84}
            }
            seedorf_stats = {
                "attacking": {"وعي هجومي": 88, "التحكم في الكرة": 92, "المراوغة": 90, "التمريرات المنخفضة": 93, "إنهاء الهجمة": 85},
                "physical": {"السرعة": 88, "التسارع": 85, "قوة في الركل": 92, "قوة التحمل": 90},
                "defending": {"وعي دفاعي": 78, "احتكاك دفاعي": 80, "قطع الكرة": 79}
            }
            messi_stats = {
                "attacking": {"وعي هجومي": 96, "التحكم في الكرة": 98, "المراوغة": 99, "التمريرات": 94, "إنهاء الهجمة": 96},
                "physical": {"السرعة": 92, "التسارع": 95, "توازن": 98, "قوة التحمل": 85},
                "defending": {"وعي دفاعي": 40, "قطع الكرة": 45}
            }
            ronaldo_stats = {
                "attacking": {"وعي هجومي": 95, "التحكم في الكرة": 88, "المراوغة": 88, "إنهاء الهجمة": 98, "مهارة الرأس": 95},
                "physical": {"السرعة": 93, "التسارع": 90, "القفز": 98, "قوة التحمل": 88},
                "defending": {"وعي دفاعي": 45, "قطع الكرة": 40}
            }
            neymar_stats = {
                "attacking": {"وعي هجومي": 90, "التحكم في الكرة": 97, "المراوغة": 98, "إنهاء الهجمة": 89, "التمريرات": 90},
                "physical": {"السرعة": 94, "التسارع": 96, "توازن": 95, "قوة التحمل": 82},
                "defending": {"وعي دفاعي": 38, "قطع الكرة": 35}
            }

            default_players = [
                ("Raphael Varane", 88, 103, "CB", "Manchester United", "Showtime", 0, "https://via.placeholder.com/150/121826/ccff00?text=Varane", json.dumps(varane_stats), json.dumps(["مهارة الرأس", "حصن", "مراقبة لاعب"])),
                ("Seedorf", 94, 106, "CM", "AC Milan", "Epic / Big Time", 0, "https://via.placeholder.com/150/121826/ccff00?text=Seedorf", json.dumps(seedorf_stats), json.dumps(["التمرير الموزون", "تسديدات بعيدة"])),
                ("Lionel Messi", 96, 108, "RWF", "Inter Miami", "Epic / Big Time", 0, "https://via.placeholder.com/150/121826/ccff00?text=Messi", json.dumps(messi_stats), json.dumps(["المراوغة السريعة", "إنهاء فائق"])),
                ("Cristiano Ronaldo", 95, 107, "ST", "Al Nassr", "Epic / Big Time", 0, "https://via.placeholder.com/150/121826/ccff00?text=Ronaldo", json.dumps(ronaldo_stats), json.dumps(["رأسيات قوية", "تسديدات بعيدة"])),
                ("Neymar Jr", 94, 105, "LWF", "Al Hilal", "Showtime", 1, "https://via.placeholder.com/150/121826/ccff00?text=Neymar", json.dumps(neymar_stats), json.dumps(["المراوغة المزدوجة", "لمسة سحرية"]))
            ]
            db.executemany("""
                INSERT INTO players (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, stats_json, skills_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

/* قسم باني الفرقة المحدث */
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
.squad-info { max-width: 55%; }
.squad-badge { color: var(--neon-green); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.squad-title { font-size: 26px; font-weight: 900; color: #fff; margin: 4px 0; }
.squad-desc { font-size: 12px; color: #94a3b8; margin-bottom: 15px; }
.btn-build { display: inline-block; padding: 10px 22px; background: var(--neon-green); color: #000; border-radius: 25px; font-weight: 900; font-size: 13px; text-decoration: none; box-shadow: 0 0 10px rgba(204,255,0,0.4); }

/* قسم المدربين المحدث كلياً ببطاقة الصورة المصغرة القابلة للضغط */
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

.manager-card { min-width: 120px; background: #0e121d; border: 1px solid var(--border-color); border-radius: 14px; padding: 10px; text-align: center; }
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
.player-img { width: 100%; height: 115px; object-fit: contain; margin: 6px 0; background:#07090e; border-radius:8px; }
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

  <!-- بطاقة باني الفرقة -->
  <div class="squad-builder-card">
    <div class="squad-info">
      <div class="squad-badge">محدث ⚡</div>
      <div class="squad-title">باني فرقة</div>
      <div class="squad-desc">أنشئ التشكيلة، اضبط تكتيكاتك وشاركها مع أصدقائك.</div>
      <a href="/squad-builder" class="btn-build">+ إنشاء تشكيلة</a>
    </div>
    <div style="font-size:45px;">📋</div>
  </div>

  <!-- قسم قائمة المدربين الرسمية مع الصورة المصغرة المضيئة -->
  <div class="managers-section">
    <div class="sec-title">👔 قائمة المدربين الرسمية</div>
    <div class="managers-row">
      <!-- كارت القائمة المصغر الذي يفتح كل المدربين -->
      <a href="/managers" class="managers-main-card">
        <img class="managers-card-img" src="{{ managers_card_img if managers_card_img else 'https://via.placeholder.com/60/00d2ff/000000?text=ALL' }}" onerror="this.src='https://via.placeholder.com/60/00d2ff/000000?text=ALL'">
        <div style="font-size:12px; font-weight:900; color:var(--neon-green);">قائمة المدربين</div>
        <div style="font-size:9px; color:#8fa0c0;">عرض الكل ➔</div>
      </a>

      {% for m in managers[:3] %}
      <div class="manager-card">
        <img class="manager-img" src="{{ m['image_url'] }}" onerror="this.src='https://via.placeholder.com/60/121826/ccff00?text=Coach'">
        <div class="manager-name">{{ m['name'] }}</div>
        <div class="manager-style">{{ m['playstyle'] }}</div>
      </div>
      {% endfor %}
    </div>
  </div>

  <div class="community-news">
    <div class="news-title">📢 أخبار المجتمع وتحديثات كونامي</div>
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
    <a href="/player/{{ p['id'] }}" class="player-card" data-upcoming="{{ p['is_upcoming'] }}">
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


# صفحة عرض جميع المدربين عند الضغط على الصورة المصغرة
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
.card { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 16px; padding: 15px; text-align: center; }
.card img { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid var(--neon-green); margin-bottom: 10px; }
.back-btn { display: inline-block; margin-bottom: 20px; padding: 8px 18px; background: #141a29; border: 1px solid var(--border-color); color: #fff; border-radius: 8px; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<a href="/" class="back-btn">← العودة للرئيسية</a>
<h2 style="color:var(--neon-green);">👔 جميع المدربين المتاحين في التطبيق</h2>
<div class="grid">
  {% for m in managers %}
  <div class="card">
    <img src="{{ m['image_url'] }}" onerror="this.src='https://via.placeholder.com/90/121826/ccff00?text=Coach'">
    <h3 style="font-size:15px; color:#fff; margin-bottom:4px;">{{ m['name'] }}</h3>
    <p style="font-size:11px; color:#00d2ff;">أسلوب اللعب: {{ m['playstyle'] }}</p>
    <p style="font-size:11px; color:#ccff00; margin-top:4px;">Affinity: {{ m['affinity'] }}</p>
  </div>
  {% endfor %}
</div>
</body>
</html>
"""


# صفحة تفاصيل اللاعب المطابقة لـ eFHUB بالكامل
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
.card-img-large { width: 190px; height: 230px; object-fit: contain; margin: 10px auto; border-radius: 12px; background: #05070c; border: 2px solid var(--neon-green); padding: 5px; }

.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
@media(max-width: 600px) { .stats-grid { grid-template-columns: 1fr; } }

.section-box { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 14px; padding: 15px; }
.section-header { font-size: 13px; font-weight: 900; color: #8fa0c0; margin-bottom: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 4px; }

.stat-row-ef { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #141a29; font-size: 12px; font-weight: 700; }
.stat-val-badge { padding: 3px 8px; border-radius: 6px; font-weight: 900; font-size: 13px; min-width: 38px; text-align: center; color: #000; }

.val-green { background: #ccff00; }
.val-yellow { background: #facc15; }
.val-orange { background: #fb923c; }
.val-red { background: #ef4444; color: #fff; }

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
        <div class="section-header">⚡ القدرة البدنية (Physical)</div>
        <div id="physicalStats"></div>
      </div>

      <div class="section-box" style="grid-column: 1 / -1;">
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

function getBadgeClass(val) {
  if(val >= 85) return 'val-green';
  if(val >= 75) return 'val-yellow';
  if(val >= 60) return 'val-orange';
  return 'val-red';
}

function renderSection(obj, containerId) {
  let html = '';
  for(let key in obj) {
    let val = obj[key];
    html += `
      <div class="stat-row-ef">
        <span style="color:#cbd5e1;">${key}</span>
        <span class="stat-val-badge ${getBadgeClass(val)}">${val}</span>
      </div>
    `;
  }
  document.getElementById(containerId).innerHTML = html || '<div style="font-size:11px;color:#666;">غير متاح</div>';
}

renderSection(fullStats.attacking || {}, 'attackingStats');
renderSection(fullStats.physical || {}, 'physicalStats');
renderSection(fullStats.defending || {}, 'defendingStats');

let skillsHtml = '';
if(Array.isArray(skills) && skills.length > 0) {
  skills.forEach(s => { skillsHtml += `<span class="skill-tag">⚡ ${s}</span>`; });
} else {
  skillsHtml = '<span style="font-size:11px;color:#888;">لا توجد مهارات مسجلة</span>';
}
document.getElementById('skillsList').innerHTML = skillsHtml;
</script>
</body>
</html>
"""


SQUAD_BUILDER_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>باني الفرقة | NOVA eHUB 26</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 15px; }
.pitch-container { max-width: 500px; margin: 0 auto; background: linear-gradient(180deg, #0b2512, #051408); border: 2px solid var(--neon-green); border-radius: 20px; padding: 20px 10px; position: relative; min-height: 600px; display: flex; flex-direction: column; justify-content: space-between; }
.pitch-line { position: absolute; border: 1px solid rgba(204, 255, 0, 0.2); pointer-events: none; }
.line-center { top: 50%; left: 0; right: 0; }
.line-circle { top: 50%; left: 50%; width: 100px; height: 100px; border-radius: 50%; transform: translate(-50%, -50%); }

.field-row { display: flex; justify-content: space-around; width: 100%; margin: 15px 0; z-index: 10; }
.pos-slot { width: 65px; height: 85px; background: rgba(14, 18, 29, 0.85); border: 1px dashed var(--neon-green); border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 10px; font-weight: 800; color: var(--neon-green); cursor: pointer; transition: 0.2s; }
.pos-slot:hover { background: var(--neon-green); color: #000; }
.back-btn { display: block; text-align: center; margin: 20px auto; max-width: 500px; padding: 12px; background: var(--neon-green); color: #000; font-weight: 900; border-radius: 10px; text-decoration: none; }
</style>
</head>
<body>
<h2 style="text-align:center; color:var(--neon-green); margin-bottom:15px;">⚽ تكتيك الملعب وباني الفرقة</h2>

<div class="pitch-container">
  <div class="pitch-line line-center"></div>
  <div class="pitch-line line-circle"></div>

  <!-- هجوم -->
  <div class="field-row">
    <div class="pos-slot">LWF<br>+</div>
    <div class="pos-slot">CF<br>+</div>
    <div class="pos-slot">RWF<br>+</div>
  </div>

  <!-- خط وسط -->
  <div class="field-row">
    <div class="pos-slot">CMF<br>+</div>
    <div class="pos-slot">AMF<br>+</div>
    <div class="pos-slot">CMF<br>+</div>
  </div>

  <!-- دفاع -->
  <div class="field-row">
    <div class="pos-slot">LB<br>+</div>
    <div class="pos-slot">CB<br>+</div>
    <div class="pos-slot">CB<br>+</div>
    <div class="pos-slot">RB<br>+</div>
  </div>

  <!-- حارس -->
  <div class="field-row" style="justify-content: center;">
    <div class="pos-slot">GK<br>+</div>
  </div>
</div>

<a href="/" class="back-btn">← العودة للرئيسية</a>
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
.card img { width: 60px; height: 60px; object-fit: contain; margin-bottom: 10px; }
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


@app.route('/managers')
def managers_page():
    with get_db() as db:
        managers = db.execute("SELECT * FROM managers ORDER BY id DESC").fetchall()
    return render_template_string(MANAGERS_LIST_TEMPLATE, managers=managers)


@app.route('/squad-builder')
def squad_builder():
    return render_template_string(SQUAD_BUILDER_TEMPLATE)


@app.route('/player/<int:player_id>')
def player_detail(player_id):
    with get_db() as db:
        player = db.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
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
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>الملف الشخصي</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#0e121d;padding:35px;border:2px solid #ccff00;border-radius:20px;width:420px;text-align:center;}}
    </style></head>
    <body><div class="box">
      <h2 style="color:#ccff00;">الملف الشخصي</h2>
      <p><b>الاسم:</b> {user["name"]}</p>
      <p><b>البريد:</b> {user["email"]}</p>
      <a href="/" style="color:#00d2ff;display:block;margin-top:15px;text-decoration:none;">← العودة للرئيسية</a>
    </div></body></html>
    """


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

            if action == "upload_banner":
                file = request.files.get("banner_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    banner_url = url_for('static', filename=f'uploads/{filename}')
                    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('custom_banner', ?)", (banner_url,))
                    db.commit()
                    msg = "✅ تم تحديث وعرض البانر بنجاح!"

            elif action == "upload_managers_card":
                file = request.files.get("card_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img_url = url_for('static', filename=f'uploads/{filename}')
                    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('managers_card_img', ?)", (img_url,))
                    db.commit()
                    msg = "✅ تم تحديث الصورة المصغرة لقائمة المدربين!"

            elif action == "add_manager":
                name = request.form.get("name")
                style = request.form.get("playstyle")
                file = request.files.get("image_file")
                img_url = "https://via.placeholder.com/90/121826/ccff00?text=Coach"
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img_url = url_for('static', filename=f'uploads/{filename}')
                db.execute("INSERT INTO managers (name, playstyle, image_url) VALUES (?, ?, ?)", (name, style, img_url))
                db.commit()
                msg = "✅ تم إضافة المدرب بنجاح!"

            elif action == "add_player":
                name = request.form.get("name")
                overall_base = int(request.form.get("overall_base", 80))
                overall_max = int(request.form.get("overall_max", 90))
                position = request.form.get("position")
                team = request.form.get("team")
                card_type = request.form.get("card_type")
                is_upcoming = 1 if request.form.get("is_upcoming") else 0

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
                    "physical": {"السرعة": int(request.form.get("speed", 85)), "قوة التحمل": int(request.form.get("stamina", 80))},
                    "defending": {"وعي دفاعي": int(request.form.get("def_awareness", 85)), "قطع الكرة": int(request.form.get("tackling", 85))}
                }
                db.execute("""
                    INSERT INTO players (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, stats_json, skills_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, json.dumps(full_stats), json.dumps([])))
                db.commit()
                msg = "✅ تم إضافة اللاعب بنجاح!"

            elif action == "delete_player":
                p_id = request.form.get("player_id")
                db.execute("DELETE FROM players WHERE id = ?", (p_id,))
                db.commit()
                msg = "🗑️ تم حذف اللاعب بنجاح!"

    with get_db() as db:
        all_players = db.execute("SELECT id, name, position, card_type FROM players ORDER BY id DESC").fetchall()

    players_options = "".join([f"<option value='{p['id']}'>{p['name']} ({p['position']} - {p['card_type']})</option>" for p in all_players])

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>لوحة المطور</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;padding:30px;}}
    .box{{background:#0e121d;padding:20px;border:1px solid #ccff00;border-radius:14px;max-width:550px;margin:0 auto 20px;}}
    input, select{{width:100%;padding:10px;margin:6px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{padding:10px 20px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;}}
    </style></head>
    <body><div style="max-width:550px;margin:auto;">
    <h2 style="color:#ccff00;">⚙️ لوحة تحكم المطور الحصرية</h2>
    <p style="color:#35eaa1;font-weight:bold;">{msg}</p>

    <div class="box">
      <h3>🖼️ رفع البانر الرئيسي للموقع</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload_banner">
        <input type="file" name="banner_file" accept="image/*" required>
        <button type="submit" style="margin-top:10px;">عرض البانر الرئيسي 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>🖼️ رفع الصورة المصغرة لكارت قائمة المدربين</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload_managers_card">
        <input type="file" name="card_file" accept="image/*" required>
        <button type="submit" style="margin-top:10px;">حفظ وتحديث الصورة المصغرة 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>👔 إضافة مدرب جديد</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_manager">
        <input name="name" placeholder="اسم المدرب" required>
        <input name="playstyle" placeholder="أسلوب اللعب (مثال: Quick Counter)" required>
        <input type="file" name="image_file" accept="image/*">
        <button type="submit" style="margin-top:10px;">إضافة المدرب</button>
      </form>
    </div>

    <div class="box">
      <h3>⚽ إضافة لاعب جديد بالكامل</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_player">
        <input name="name" placeholder="اسم اللاعب" required>
        <input type="number" name="overall_base" placeholder="الطاقة الأساسية" required>
        <input type="number" name="overall_max" placeholder="الطاقة القصوى" required>
        <input name="position" placeholder="المركز (مثال: CB)" required>
        <input name="team" placeholder="النادي / الفريق" required>
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
        players = [dict(row) for row in db.execute("SELECT * FROM players ORDER BY overall_max DESC").fetchall()]
        news = [dict(row) for row in db.execute("SELECT * FROM news ORDER BY id DESC LIMIT 3").fetchall()]
        managers = [dict(row) for row in db.execute("SELECT * FROM managers ORDER BY id DESC").fetchall()]
        banner_res = db.execute("SELECT value FROM settings WHERE key = 'custom_banner'").fetchone()
        m_card_res = db.execute("SELECT value FROM settings WHERE key = 'managers_card_img'").fetchone()
        
        custom_banner = banner_res["value"] if banner_res else ""
        managers_card_img = m_card_res["value"] if m_card_res else ""

    return render_template_string(
        HOME_TEMPLATE,
        players=players,
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
