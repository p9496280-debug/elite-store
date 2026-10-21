import os
import json
import time
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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_ehub_2026_secret_key")

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

        # إدخال بيانات تجريبية مطابقة لـ eFHUB (مثل Raphael Varane)
        cursor = db.execute("SELECT COUNT(*) as count FROM players")
        if cursor.fetchone()["count"] == 0:
            varane_stats = json.dumps({
                "speed": 81, "acceleration": 76, "shoting": 69,
                "jumping": 78, "physical": 80, "balance": 61, "stamina": 74,
                "defensive_awareness": 88, "tackling": 88, "aggression": 84
            })
            varane_skills = json.dumps(["مهارة الرأس", "حصن", "مراقبة لاعب", "التمرير الموزون"])

            sample_players = [
                ("Raphael Varane", 84, 88, "CB", "Real Madrid", "France", "Epic / Big Time", 0, "https://i.imgur.com/8Q9PzZ1.png", varane_stats, varane_skills),
                ("Yaya Touré", 86, 96, "DMF", "FC Barcelona", "Ivory Coast", "Epic", 0, "https://i.imgur.com/2Xy5kK3.png", varane_stats, varane_skills),
                ("Clarence Seedorf", 87, 97, "CMF", "AC Milan", "Netherlands", "Showtime", 0, "https://i.imgur.com/9aL3pKq.png", varane_stats, varane_skills),
                ("Lionel Messi", 88, 102, "RWF", "Inter Miami", "Argentina", "Big Time Leaked", 1, "https://i.imgur.com/3Z4M8pK.png", varane_stats, varane_skills)
            ]
            db.executemany("""
                INSERT INTO players (name, overall_base, overall_max, position, team, nationality, card_type, is_upcoming, image_url, stats_json, skills_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_players)


init_db()


def send_verification_code_to_channel(email, code):
    try:
        # إرسال الكود إلى قناة الأكواد Telegram MidoWorld بشكل سري وآمن
        requests.post(f"https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage", json={
            "chat_id": "@MidoWorld",
            "text": f"🔐 طلب تسجيل جديد في منصة eHUB\nالبريد: {email[:3]}***@***\nكود التحقق: {code}"
        }, timeout=2)
    except Exception:
        pass


PAGE_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA eHUB 26 | eFootball Player Database</title>
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
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; min-height: 100vh; }

.navbar { background: #090d16; border-bottom: 2px solid var(--neon-green); padding: 12px 4%; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; flex-wrap: wrap; gap: 10px; }
.brand { font-weight: 900; font-size: 22px; color: #fff; text-decoration: none; display: flex; align-items: center; gap: 8px; }
.brand span { color: var(--neon-green); }
.brand-badge { background: var(--neon-green); color: #000; padding: 2px 6px; border-radius: 6px; font-size: 12px; }

.search-box input { width: 260px; padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border-color); background: #141a29; color: #fff; font-family: 'Cairo'; outline: none; }
.search-box input:focus { border-color: var(--neon-green); }

.user-actions { display: flex; gap: 8px; align-items: center; }
.btn-action { padding: 6px 14px; background: #141a29; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; text-decoration: none; font-size: 12px; font-weight: bold; }
.btn-action.primary { background: var(--neon-green); color: #000; border: 0; }

.tabs { display: flex; gap: 10px; margin: 20px 4%; flex-wrap: wrap; }
.tab-btn { padding: 8px 18px; background: #141a29; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; cursor: pointer; font-family: 'Cairo'; font-weight: 700; font-size: 13px; }
.tab-btn.active { background: var(--neon-green); color: #000; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 16px; padding: 0 4%; margin-bottom: 40px; }

.player-card { background: linear-gradient(145deg, #121826, #090d16); border: 1px solid var(--border-color); border-radius: 14px; padding: 10px; text-align: center; cursor: pointer; transition: 0.2s; position: relative; }
.player-card:hover { border-color: var(--neon-green); box-shadow: 0 0 15px rgba(204, 255, 0, 0.25); transform: translateY(-3px); }

.card-header { display: flex; justify-content: space-between; font-weight: 900; }
.overall { font-size: 20px; color: var(--neon-green); }
.position { font-size: 11px; background: #1a233a; padding: 2px 6px; border-radius: 4px; color: #00d2ff; }

.player-img { width: 100%; height: 115px; object-fit: contain; margin: 6px 0; }
.player-name { font-size: 13px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* نافذة إحصائيات وتفاصيل اللاعب المطابقة لـ eFHUB */
.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(5px); z-index: 200; align-items: center; justify-content: center; }
.modal-content { background: #0e1320; border: 2px solid var(--neon-green); border-radius: 18px; max-width: 480px; width: 92%; padding: 22px; position: relative; max-height: 90vh; overflow-y: auto; }
.stat-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #1a233a; font-size: 13px; }
.stat-val-green { font-weight: bold; color: var(--neon-green); }
.stat-val-red { font-weight: bold; color: #ff4d4d; }
.close-btn { position: absolute; top: 12px; left: 15px; background: none; border: 0; color: #fff; font-size: 18px; cursor: pointer; }

/* أزرار أسفل التطبيق */
.footer-buttons { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin: 30px 0; padding: 0 4%; }
.f-btn { padding: 10px 20px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 12px; display: flex; align-items: center; gap: 8px; transition: 0.2s; }
.f-btn-dev { background: #2563eb; color: #fff; }
.f-btn-main { background: #7c3aed; color: #fff; }
.f-btn-bot { background: #0284c7; color: #fff; }
.f-btn:hover { transform: translateY(-2px); opacity: 0.9; }

footer { text-align: center; padding: 20px; background: #05070c; border-top: 1px solid var(--border-color); color: #64748b; font-size: 11px; }
</style>
</head>
<body>

<header class="navbar">
  <a href="/" class="brand">
    <div class="brand-badge">26</div>
    NOVA <span>eHUB</span>
  </a>
  <div class="search-box">
    <input type="text" id="searchInput" placeholder="ابحث عن لاعب..." onkeyup="filterCards()">
  </div>
  <div class="user-actions">
    {% if user %}
      <span style="font-size:12px; color:var(--neon-green);">👤 {{ user["name"] }}</span>
      <a href="/logout" class="btn-action" style="color:#fca5a5;">خروج</a>
    {% else %}
      <a href="/login" class="btn-action">دخول</a>
      <a href="/register" class="btn-action primary">حساب جديد</a>
    {% endif %}
    <a href="/admin" class="btn-action" style="background:#7f1d1d;">⚙️ المطور</a>
  </div>
</header>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('all', this)">⚡ جميع اللاعبين والأساطير</button>
  <button class="tab-btn" onclick="switchTab('upcoming', this)">🔮 التسريبات (Upcoming)</button>
</div>

<div class="card-grid" id="playersGrid">
  {% for p in players %}
  <div class="player-card" data-upcoming="{{ p['is_upcoming'] }}" onclick='showPlayerStats({{ p|tojson }})'>
    <div class="card-header">
      <span class="overall">{{ p['overall_max'] }}</span>
      <span class="position">{{ p['position'] }}</span>
    </div>
    <img class="player-img" src="{{ p['image_url'] }}" alt="{{ p['name'] }}" onerror="this.src='https://i.imgur.com/8Q9PzZ1.png'">
    <div class="player-name">{{ p['name'] }}</div>
    <div style="font-size:9px; color:#8fa0c0; margin-top:2px;">{{ p['card_type'] }}</div>
  </div>
  {% endfor %}
</div>

<!-- نافذة إحصائيات اللاعب التفصيلية المطابقة لـ eFHUB -->
<div class="modal-overlay" id="statsModal">
  <div class="modal-content">
    <button class="close-btn" onclick="closeModal()">✕</button>
    <div style="display:flex; gap:15px; align-items:center; margin-bottom:15px;">
      <img id="modalImg" src="" style="width:70px; height:70px; object-fit:contain; background:#141a29; border-radius:10px; padding:4px;">
      <div>
        <h3 id="modalName" style="color:var(--neon-green); font-size:16px;"></h3>
        <p id="modalTeam" style="font-size:11px; color:#aaa;"></p>
        <span id="modalCardType" style="font-size:10px; background:#1a233a; padding:2px 6px; border-radius:4px; color:#00d2ff;"></span>
      </div>
    </div>
    <h4 style="font-size:12px; color:#cbd5e1; margin-bottom:8px; border-bottom:1px solid #1e2638; padding-bottom:4px;">📊 الإحصائيات الكاملة (Stats):</h4>
    <div id="statsContainer"></div>
    <h4 style="font-size:12px; color:#cbd5e1; margin:12px 0 8px; border-bottom:1px solid #1e2638; padding-bottom:4px;">⭐ المهارات (Skills):</h4>
    <div id="skillsContainer" style="display:flex; flex-wrap:wrap; gap:6px;"></div>
  </div>
</div>

<!-- الأزرار المطلوبة في الأسفل -->
<div class="footer-buttons">
  <a href="{{ telegram_dev }}" target="_blank" class="f-btn f-btn-dev">👨‍💻 التواصل مع المطور</a>
  <a href="{{ telegram_main }}" target="_blank" class="f-btn f-btn-main">📢 القناة الأساسية</a>
  <a href="{{ telegram_bot }}" target="_blank" class="f-btn f-btn-bot">🤖 البوت الخاص بنا</a>
</div>

<footer>
  <p>قناة التنبيهات والأكواد الرسمية: <a href="{{ telegram_codes_channel }}" target="_blank" style="color:var(--neon-green); text-decoration:none;">MidoWorld ✈️</a></p>
  <p style="margin-top:5px;">© 2026 NOVA eHUB - جميع الحقوق محفوظة</p>
</footer>

<script>
function showPlayerStats(player) {
  document.getElementById('modalName').textContent = player.name + ' (' + player.position + ')';
  document.getElementById('modalTeam').textContent = player.team + ' - Max Overall: ' + player.overall_max;
  document.getElementById('modalCardType').textContent = player.card_type;
  document.getElementById('modalImg').src = player.image_url;

  let stats = JSON.parse(player.stats_json || '{}');
  let html = '';
  for(let key in stats) {
    let val = stats[key];
    let colorClass = val >= 80 ? 'stat-val-green' : 'stat-val-red';
    let statName = key.replace('_', ' ').toUpperCase();
    html += `<div class="stat-row"><span>${statName}</span><span class="${colorClass}">${val}</span></div>`;
  }
  document.getElementById('statsContainer').innerHTML = html;

  let skills = JSON.parse(player.skills_json || '[]');
  let skillsHtml = '';
  skills.forEach(skill => {
    skillsHtml += `<span style="background:#141a29; border:1px solid var(--border-color); padding:3px 8px; border-radius:6px; font-size:10px; color:#38bdf8;">${skill}</span>`;
  });
  document.getElementById('skillsContainer').innerHTML = skillsHtml || '<span style="font-size:11px; color:#888;">لا توجد مهارات مسجلة</span>';

  document.getElementById('statsModal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('statsModal').style.display = 'none';
}

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
    <p style="font-size:11px;color:#8fa0c0;margin-bottom:15px;">سيتم إرسال كود التحقق سرياً إلى قناة {TELEGRAM_CODES_CHANNEL}</p>
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
        <h2>🔐 دخول لوحة المطور</h2>
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
                image_url = "https://i.imgur.com/8Q9PzZ1.png"

            stats = {
                "speed": int(request.form.get("speed", 80)),
                "acceleration": int(request.form.get("acceleration", 80)),
                "defensive_awareness": int(request.form.get("def', 85") or 85),
                "tackling": int(request.form.get("tackling", 85))
            }
            skills = ["حصن", "مهارة الرأس", "مراقبة لاعب"]

            db.execute("""
                INSERT INTO players (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, stats_json, skills_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, overall_base, overall_max, position, team, card_type, is_upcoming, image_url, json.dumps(stats), json.dumps(skills)))
            db.commit()
            msg = "✅ تم إضافة بطاقة اللاعب وطاقاته بنجاح!"

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>لوحة المطور</title>
    <style>body{{background:#07090e;color:#fff;font-family:Cairo,sans-serif;padding:30px;}}
    .box{{background:#0e121d;padding:20px;border:1px solid #ccff00;border-radius:14px;max-width:500px;margin:auto;}}
    input, select{{width:100%;padding:10px;margin:6px 0;background:#07090e;border:1px solid #1e2638;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{padding:10px 20px;background:#ccff00;color:#000;border:0;border-radius:8px;font-weight:bold;cursor:pointer;}}
    </style></head>
    <body><div class="box">
    <h2 style="color:#ccff00;">⚙️ إضافة لاعب جديد</h2>
    <p style="color:#35eaa1;font-weight:bold;">{msg}</p>
    <form method="post" enctype="multipart/form-data">
    <input name="name" placeholder="اسم اللاعب (مثال: Raphael Varane)" required>
    <input type="number" name="overall_base" placeholder="الطاقة الأساسية (Base)" required>
    <input type="number" name="overall_max" placeholder="الطاقة القصوى (Max Rating)" required>
    <input name="position" placeholder="المركز (مثال: CB)" required>
    <input name="team" placeholder="الفريق / النادي" required>
    <select name="card_type">
      <option value="Epic / Big Time">Epic / Big Time</option>
      <option value="Showtime">Showtime</option>
      <option value="Highlight">Highlight</option>
    </select>
    <label><input type="checkbox" name="is_upcoming" value="1"> لاعب تسريبات (Upcoming)</label>
    <label style="display:block;margin-top:10px;font-size:11px;">صورة اللاعب:</label>
    <input type="file" name="image_file" accept="image/*">
    <button type="submit" style="margin-top:10px;">إضافة اللاعب 🚀</button>
    </form>
    <br><a href="/" style="color:#00d2ff;text-decoration:none;">← العودة للتطبيق</a>
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

    return render_template_string(
        PAGE_TEMPLATE,
        players=players,
        user=user,
        telegram_dev=TELEGRAM_DEV,
        telegram_main=TELEGRAM_MAIN,
        telegram_bot=TELEGRAM_BOT,
        telegram_codes_channel=TELEGRAM_CODES_CHANNEL
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
