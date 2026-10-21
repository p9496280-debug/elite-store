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
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_ehub_pro_2026")

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

        cursor = db.execute("SELECT COUNT(*) as count FROM news")
        if cursor.fetchone()["count"] == 0:
            db.execute("INSERT INTO news (title, content, created_at) VALUES (?, ?, ?)", 
                       ("تحديث صيانة الخميس القادم", "وصول بطاقات Epic جديدة وتسريبات قوية لميسي ورونالدو.", int(time.time())))


init_db()


def send_verification_code_to_channel(email, code):
    try:
        requests.post("https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage", json={
            "chat_id": "@MidoWorld",
            "text": f"🔐 كود تحقق جديد لمنصة eHUB\nالبريد: {email[:3]}***@***\nالكود: {code}"
        }, timeout=2)
    except Exception:
        pass


# الصفحة الرئيسية
HOME_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA eHUB 26 | eFootball Database</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root {
  --bg-dark: #07090e;
  --panel-bg: #0e121d;
  --neon-green: #ccff00;
  --neon-blue: #00d2ff;
  --border-color: #1e2638;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; min-height: 100vh; display: flex; flex-direction: column; justify-content: space-between; }
.navbar { background: #090d16; border-bottom: 2px solid var(--neon-green); padding: 12px 4%; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; flex-wrap: wrap; gap: 10px; }
.brand { font-weight: 900; font-size: 22px; color: #fff; text-decoration: none; display: flex; align-items: center; gap: 8px; }
.brand span { color: var(--neon-green); }
.brand-badge { background: var(--neon-green); color: #000; padding: 2px 6px; border-radius: 6px; font-size: 12px; }
.search-box input { width: 240px; padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border-color); background: #141a29; color: #fff; font-family: 'Cairo'; outline: none; }
.search-box input:focus { border-color: var(--neon-green); }
.user-actions { display: flex; gap: 8px; align-items: center; }
.btn-action { padding: 6px 14px; background: #141a29; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; text-decoration: none; font-size: 12px; font-weight: bold; }
.btn-action.primary { background: var(--neon-green); color: #000; border: 0; }
.custom-banner { width: 100%; background: #000; text-align: center; border-bottom: 2px solid var(--border-color); padding: 10px 0; }
.custom-banner img { max-width: 100%; height: auto; max-height: 400px; object-fit: contain; display: block; margin: 0 auto; }
.community-news { background: #0e1320; border: 1px solid var(--border-color); border-radius: 14px; padding: 16px; margin: 20px 4%; }
.news-title { font-size: 15px; font-weight: 800; color: var(--neon-green); margin-bottom: 6px; }
.news-item { font-size: 12px; color: #cbd5e1; padding: 6px 0; border-bottom: 1px solid #1e2638; }
.quick-btns { display: flex; gap: 10px; margin: 15px 4%; flex-wrap: wrap; }
.q-btn { padding: 8px 16px; background: #141a29; border: 1px solid var(--border-color); border-radius: 10px; color: #fff; font-size: 12px; font-weight: bold; text-decoration: none; display: flex; align-items: center; gap: 6px; transition: 0.2s; }
.q-btn:hover { border-color: var(--neon-green); color: var(--neon-green); }
.tabs { display: flex; gap: 10px; margin: 20px 4%; flex-wrap: wrap; }
.tab-btn { padding: 8px 18px; background: #141a29; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; cursor: pointer; font-family: 'Cairo'; font-weight: 700; font-size: 13px; }
.tab-btn.active { background: var(--neon-green); color: #000; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 16px; padding: 0 4%; margin-bottom: 40px; }
.player-card { background: linear-gradient(145deg, #121826, #090d16); border: 1px solid var(--border-color); border-radius: 14px; padding: 10px; text-align: center; cursor: pointer; transition: 0.2s; position: relative; text-decoration: none; display: block; color: inherit; }
.player-card:hover { border-color: var(--neon-green); box-shadow: 0 0 15px rgba(204, 255, 0, 0.25); transform: translateY(-3px); }
.card-header { display: flex; justify-content: space-between; font-weight: 900; }
.overall { font-size: 20px; color: var(--neon-green); }
.position { font-size: 11px; background: #1a233a; padding: 2px 6px; border-radius: 4px; color: #00d2ff; }
.player-img { width: 100%; height: 115px; object-fit: contain; margin: 6px 0; background:#07090e; border-radius:8px; }
.player-name { font-size: 13px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bottom-section { margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 25px; background: #05070c; }
.footer-buttons { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; padding: 0 4%; }
.f-btn { padding: 10px 20px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 12px; display: flex; align-items: center; gap: 8px; transition: 0.2s; }
.f-btn-dev { background: #2563eb; color: #fff; }
.f-btn-main { background: #7c3aed; color: #fff; }
.f-btn-bot { background: #0284c7; color: #fff; }
.f-btn:hover { transform: translateY(-2px); opacity: 0.9; }
footer { text-align: center; padding: 15px; color: #64748b; font-size: 11px; }
</style>
</head>
<body>

<div>
  <header class="navbar">
    <a href="/" class="brand">
      <div class="brand-badge">26</div>
      eHUB <span>NOVA</span>
    </a>
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="ابحث عن لاعب..." onkeyup="filterCards()">
    </div>
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
  <div class="custom-banner">
    <img src="{{ custom_banner }}" alt="Main Banner">
  </div>
  {% endif %}

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
      <div class="card-header">
        <span class="overall">{{ p['overall_max'] }}</span>
        <span class="position">{{ p['position'] }}</span>
      </div>
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
function switchTab(type, btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.player-card').forEach(card => {
    let isUpcoming = card.getAttribute('data-upcoming');
    if(type === 'all') card.style.display = 'block';
    else if(type === 'upcoming' && isUpcoming === '1') card.style.display = 'block';
    else card.style.display = 'none';
  });
}
function filterCards() {
  let query = document.getElementById('searchInput').value.toLowerCase();
  document.querySelectorAll('.player-card').forEach(card => {
    let name = card.querySelector('.player-name').textContent.toLowerCase();
    card.style.display = name.includes(query) ? 'block' : 'none';
  });
}
</script>
</body>
</html>
"""


# لوحة اللاعب الفخمة والكاملة
PLAYER_DETAIL_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ player['name'] }} | eHUB 26</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 20px; }
.container { max-width: 600px; margin: auto; background: var(--panel-bg); border: 2px solid var(--neon-green); border-radius: 20px; padding: 25px; box-shadow: 0 0 25px rgba(204,255,0,0.2); }
.header { display: flex; gap: 20px; align-items: center; border-bottom: 2px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px; }
.p-img { width: 110px; height: 110px; object-fit: contain; background: #07090e; border-radius: 12px; padding: 6px; border: 1px solid var(--neon-green); }
.stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1e2638; font-size: 14px; }
.stat-val { font-weight: bold; color: var(--neon-green); }
.back-btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background: var(--neon-green); color: #000; font-weight: bold; border-radius: 10px; text-decoration: none; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <img class="p-img" src="{{ player['image_url'] }}" onerror="this.src='https://via.placeholder.com/150/121826/ccff00?text=eFootball'">
    <div>
      <h2 style="color:var(--neon-green);">{{ player['name'] }}</h2>
      <p style="font-size:13px; color:#aaa;">{{ player['team'] }} | المركز: <b>{{ player['position'] }}</b></p>
      <p style="font-size:12px; color:#00d2ff; margin-top:4px;">نوع البطاقة: {{ player['card_type'] }} | Max Overall: <b>{{ player['overall_max'] }}</b></p>
    </div>
  </div>
  <h3 style="font-size:15px; margin-bottom:12px; color:#cbd5e1;">📊 الإحصائيات الكاملة (Stats):</h3>
  <div id="statsBox"></div>
  <a href="/" class="back-btn">← العودة للرئيسية</a>
</div>
<script>
let stats = {{ player['stats_json'] | safe }};
let html = '';
for(let key in stats) {
  let sName = key.replace('_', ' ').toUpperCase();
  html += `<div class="stat-row"><span>${sName}</span><span class="stat-val">${stats[key]}</span></div>`;
}
document.getElementById('statsBox').innerHTML = html;
</script>
</body>
</html>
"""


# صفحة المهارات الجديدة
SKILLS_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>المهارات الجديدة | eHUB 26</title>
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


@app.route('/player/<int:player_id>')
def player_detail(player_id):
    with get_db() as db:
        player = db.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    if not player:
        return "اللاعب غير موجود", 404
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
                except Exception:
                    error = "البريد الإلكتروني مسجل مسبقاً."
        else:
            error = "يرجى تعبئة جميع الحقول."
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إنشاء حساب</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#0e121d;padding:30px;border:1px solid #ccff00;border-radius:18px;width:360px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2>إنشاء حساب جديد</h2>
    <form method="post">
    <input name='name' placeholder='الاسم الكامل' required>
    <input type='email' name='email' placeholder='البريد الإلكتروني' required>
    <input type='password' name='password' placeholder='كلمة المرور' required>
    <button type="submit">إنشاء الحساب</button>
    </form>
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
    .box{{background:#0e121d;padding:30px;border:1px solid #ccff00;border-radius:18px;width:360px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2>تسجيل الدخول</h2>
    <form method="post">
    <input type="email" name="email" placeholder="البريد الإلكتروني" required>
    <input type="password" name="password" placeholder="كلمة المرور" required>
    <button type="submit">دخول</button>
    </form>
    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/register" style="color:#00d2ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">إنشاء حساب جديد</a>
    </div></body></html>
    """


@app.route('/account')
def account():
    email = session.get("user_email")
    if not email: return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>الملف الشخصي</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#0e121d;padding:30px;border:2px solid #ccff00;border-radius:18px;width:400px;text-align:center;}}
    .info{{background:#141a29;padding:12px;border-radius:8px;margin:15px 0;font-size:13px;text-align:right;}}
    </style></head>
    <body><div class="box">
      <h2 style="color:#ccff00;">👤 الملف الشخصي للمستخدم</h2>
      <div class="info">
        <p><b>الاسم:</b> {user["name"]}</p>
        <p><b>البريد الإلكتروني:</b> {user["email"]}</p>
        <p><b>حالة الحساب:</b> <span style="color:#ccff00;">موثق ✅</span></p>
      </div>
      <a href="/" style="color:#00d2ff;display:block;margin-top:15px;text-decoration:none;font-weight:bold;">← العودة للرئيسية</a>
      <a href="/logout" style="color:#ef4444;display:block;margin-top:10px;text-decoration:none;">تسجيل الخروج</a>
    </div></body></html>
    """


@app.route('/logout')
def logout():
    session.pop("user_email", None)
    return redirect(url_for("home"))


# لوحة تحكم المطور الحصرية والآمنة
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    msg = ""
    if request.method == "POST" and request.form.get("login_admin"):
        if request.form.get("email") == ADMIN_EMAIL and request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
        else:
            msg = "بيانات دخول المطور غير صحيحة."

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
        <form method="post">
        <input type="hidden" name="login_admin" value="1">
        <input type="email" name="email" placeholder="بريد المطور" required>
        <input type="password" name="password" placeholder="كلمة المرور" required>
        <button type="submit">دخول اللوحة</button>
        </form>
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
                    msg = "✅ تم تحديث وعرض الصورة بالكامل بنجاح!"

            elif action == "add_news":
                title = request.form.get("title")
                content = request.form.get("content")
                db.execute("INSERT INTO news (title, content, created_at) VALUES (?, ?, ?)", (title, content, int(time.time())))
                db.commit()
                msg = "✅ تم إضافة خبر المجتمع بنجاح!"

            elif action == "add_skill":
                name = request.form.get("name")
                desc = request.form.get("desc")
                img_url = ""
                file = request.files.get("skill_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img_url = url_for('static', filename=f'uploads/{filename}')
                db.execute("INSERT INTO skills (name, description, image_url) VALUES (?, ?, ?)", (name, desc, img_url))
                db.commit()
                msg = "✅ تم إضافة المهارة الجديدة بنجاح!"

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
                else:
                    image_url = "https://via.placeholder.com/150/121826/ccff00?text=eFootball"

                stats = {
                    "speed": int(request.form.get("speed", 85)),
                    "acceleration": int(request.form.get("acceleration", 85)),
                    "dribbling": int(request.form.get("dribbling", 85)),
                    "finishing": int(request.form.get("finishing", 85)),
                    "passing": int(request.form.get("passing", 80)),
                    "defensive_awareness": int(request.form.get("def_awareness", 50))
                }
                db.execute("""
                    INSERT INTO players (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, stats_json, skills_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, json.dumps(stats), json.dumps([])))
                db.commit()
                msg = "✅ تم إضافة اللاعب وطاقاته بنجاح!"

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
    input, textarea, select{{width:100%;padding:10px;margin:6px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;font-family:Cairo;}}
    button{{padding:10px 20px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;}}
    </style></head>
    <body><div style="max-width:550px;margin:auto;">
    <h2 style="color:#ccff00;">⚙️ لوحة تحكم المطور الحصرية</h2>
    <p style="color:#35eaa1;font-weight:bold;">{msg}</p>
    <a href="/" style="color:#00d2ff;text-decoration:none;display:block;margin-bottom:15px;">← العودة للتطبيق</a>

    <div class="box">
      <h3>🖼️ رفع وعرض الصورة كاملة في الواجهة</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload_banner">
        <input type="file" name="banner_file" accept="image/*" required>
        <button type="submit" style="margin-top:10px;">عرض الصورة بالكامل 🚀</button>
      </form>
    </div>

    <div class="box">
      <h3>⚡ إضافة مهارة جديدة مع صورتها</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_skill">
        <input name="name" placeholder="اسم المهارة (مثال: Double Touch)" required>
        <textarea name="desc" placeholder="وصف المهارة..." rows="2" required></textarea>
        <label style="font-size:11px;">صورة المهارة:</label>
        <input type="file" name="skill_file" accept="image/*">
        <button type="submit" style="margin-top:10px;">إضافة المهارة</button>
      </form>
    </div>

    <div class="box">
      <h3>⚽ إضافة لاعب جديد بالكامل</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_player">
        <input name="name" placeholder="اسم اللاعب" required>
        <input type="number" name="overall_base" placeholder="الطاقة الأساسية (Base)" required>
        <input type="number" name="overall_max" placeholder="الطاقة القصوى (Max)" required>
        <input name="position" placeholder="المركز (مثال: CMF)" required>
        <input name="team" placeholder="النادي / الفريق" required>
        <select name="card_type">
          <option value="Epic / Big Time">Epic / Big Time</option>
          <option value="Showtime">Showtime</option>
          <option value="Highlight">Highlight</option>
        </select>
        <label><input type="checkbox" name="is_upcoming" value="1"> لاعب تسريبات (Upcoming)</label>
        <label style="font-size:11px;display:block;margin-top:6px;">صورة بطاقة اللاعب:</label>
        <input type="file" name="image_file" accept="image/*">
        
        <h4 style="margin-top:10px;font-size:13px;color:#ccff00;">الطاقات التفصيلية:</h4>
        <input type="number" name="speed" placeholder="السرعة Speed" value="85">
        <input type="number" name="acceleration" placeholder="التسارع Acceleration" value="85">
        <input type="number" name="dribbling" placeholder="المراوغة Dribbling" value="85">
        <input type="number" name="finishing" placeholder="الإنهاء Finishing" value="80">
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
    </div></body></html>
    """


@app.route("/")
def home():
    email = session.get("user_email")
    user = None
    if email:
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    with get_db() as db:
        players = [dict(row) for row in db.execute("SELECT * FROM players ORDER BY overall_max DESC").fetchall()]
        news = [dict(row) for row in db.execute("SELECT * FROM news ORDER BY id DESC LIMIT 3").fetchall()]
        banner_res = db.execute("SELECT value FROM settings WHERE key = 'custom_banner'").fetchone()
        custom_banner = banner_res["value"] if banner_res else ""

    return render_template_string(
        HOME_TEMPLATE,
        players=players,
        news=news,
        user=user,
        custom_banner=custom_banner,
        telegram_dev=TELEGRAM_DEV,
        telegram_main=TELEGRAM_MAIN,
        telegram_bot=TELEGRAM_BOT,
        telegram_codes_channel=TELEGRAM_CODES_CHANNEL
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
