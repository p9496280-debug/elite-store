import os
import json
import time
import secrets
import sqlite3
import math
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template_string,
    request,
    session,
    redirect,
    url_for,
    make_response,
    jsonify,
    send_from_directory,
    Response,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key_2026")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
AVATARS_FOLDER = os.path.join(app.root_path, 'static', 'avatars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATARS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AVATARS_FOLDER'] = AVATARS_FOLDER

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")
ADMIN_TELEGRAM_USERNAME = "Mido_M9do"
TELEGRAM_BOT_USERNAME = "midoassistantAIbot"
TELEGRAM_CHANNEL_LINK = "https://t.me/Midomsn"

SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "p9496280@gmail.com")
SUPPORT_EMAIL_PASSWORD = os.environ.get("SUPPORT_EMAIL_PASSWORD", "")


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
                telegram_id TEXT DEFAULT '',
                balance REAL NOT NULL DEFAULT 0.0,
                verified INTEGER NOT NULL DEFAULT 0,
                avatar TEXT DEFAULT '🤖',
                status_title TEXT DEFAULT 'عضو مميز',
                ref_code TEXT UNIQUE,
                referred_by TEXT,
                last_spin_date TEXT,
                spin_count INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS email_codes (
                email TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price_val REAL NOT NULL,
                price TEXT NOT NULL,
                code TEXT NOT NULL,
                icon TEXT NOT NULL,
                image_url TEXT DEFAULT '',
                category TEXT NOT NULL,
                color TEXT NOT NULL,
                badge TEXT
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                image_url TEXT DEFAULT '',
                link_url TEXT DEFAULT '',
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS store_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        db.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('flash_msg', 'عروض الساعات المحدودة! خصومات خاصة تنتهي قريباً')")
        db.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('vodafone_number', '01000000000')")

        admin_user = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, avatar, status_title, ref_code, created_at)
                VALUES (?, ?, ?, ?, 999999.0, 1, '👑', 'المطور الرئيسي', 'ADMINREF', ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "000000", int(time.time())))

        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("كود جوجل بلاي (10$)", "الولايات المتحدة", 500.00, "500 جـ", "GPLAY-9876", "▶", "", "بطاقات الألعاب", "#35eaa1", "عروض سريعة 🔥"),
                ("كود بلايستيشن (20$)", "الولايات المتحدة", 1000.00, "1000 جـ", "PSN-5432", "PS", "", "بطاقات الألعاب", "#62a0ff", "مميز"),
                ("كود إكس بوكس (25$)", "الولايات المتحدة", 1250.00, "1250 جـ", "XBOX-3344", "ⓧ", "", "بطاقات الألعاب", "#5dff9c", None),
                ("شحن ببجي 660 شدة", "شحن فوري عن طريق الايدي", 350.00, "350 جـ", "PUBG-660", "🎮", "", "ألعاب", "#ff3b3b", "شائع 🔥"),
                ("10 دولار USDT (TRC20)", "تحويل فوري لمحفظتك الرقمية", 500.00, "500 جـ", "USDT-10", "🪙", "", "عملات رقمية ودولارات", "#facc15", "جديد 🔥"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)

init_db()


def send_email_code(to_email, code):
    if not SUPPORT_EMAIL_PASSWORD:
        return False
    msg = MIMEMultipart()
    msg['From'] = f"NOVA STORE Support <{SUPPORT_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = "🔐 رمز التحقق الخاص بك لحساب NOVA STORE"

    html_content = f"""
    <div dir="rtl" style="font-family:'Cairo',sans-serif; background:#03091b; color:#fff; padding:30px; border-radius:16px; border:1px solid #315dff;">
      <h2 style="color:#35eaa1; margin-top:0;">🛡️ NOVA STORE - التحقق الرسمي</h2>
      <p style="color:#cbd5e1; font-size:14px;">مرحباً بك! كود التحقق الخاص بك هو:</p>
      <div style="background:#07132c; border:1px solid #35eaa1; padding:15px; text-align:center; border-radius:12px; margin:20px 0;">
        <h1 style="color:#35eaa1; font-size:32px; letter-spacing:4px; margin:5px 0;">{code}</h1>
      </div>
    </div>
    """
    msg.attach(MIMEText(html_content, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
        server.starttls()
        server.login(SUPPORT_EMAIL, SUPPORT_EMAIL_PASSWORD)
        server.sendmail(SUPPORT_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


def get_products():
    with get_db() as db:
        return [dict(row) for row in db.execute("SELECT * FROM products").fetchall()]


def get_posts():
    with get_db() as db:
        return [dict(row) for row in db.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()]


# ==================== الصفحة الرئيسية ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff;}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.topbar{min-height:78px;display:flex;align-items:center;gap:20px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:10}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white}.brand b{color:#754bff}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.nav{min-height:58px;padding:0 4%;display:flex;align-items:center;gap:12px;border-bottom:1px solid #1a2d54;background:#07122b;overflow-x:auto;}
.nav::-webkit-scrollbar{display:none}
.nav a{color:#c4cde3;text-decoration:none;padding:8px 16px;border-radius:12px;font-size:12.5px;font-weight:600;display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.03);white-space:nowrap;}
.layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:22px;padding:22px 4%}
@media (max-width:850px){.layout{grid-template-columns:1fr;}}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:#050c1e;border-radius:14px;padding:12px;}
.product-img{width:100%;height:150px;object-fit:contain;border-radius:10px;background:#03091b;}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;text-decoration:none;display:inline-block;}
.admin-badge{background:#570f0f;color:#ff7777;border:1px solid #ff5555;padding:6px 14px;border-radius:12px;font-weight:bold;text-decoration:none;}
.post-card {background:linear-gradient(145deg,#0b1938,#07122b);border:1px solid #315dff;border-radius:16px;padding:16px;margin-bottom:15px;}
.post-card img {width:100%;max-height:450px;object-fit:contain;border-radius:12px;margin-top:10px;background:#03091b;}
</style>
</head>
<body>

<header class="topbar">
  <a class="brand" href="/"><span>NOVA <b>STORE</b></span></a>
  <div class="header-actions">
    {% if is_admin %}
      <a href="/admin" class="admin-badge">⚙️ لوحة المطور</a>
    {% endif %}
    {% if user %}
      <span style="color:#35eaa1;font-size:12px;font-weight:bold;">{{ user["name"] }} ({{ user["balance"] }} جـ)</span>
      <a href="/logout" style="color:#ff7777;font-size:11px;text-decoration:none;margin-right:10px;">خروج</a>
    {% else %}
      <a href="/login" style="color:#d8e2ff;text-decoration:none;font-size:12px;">تسجيل الدخول</a>
      <a href="/register" style="padding:8px 14px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;">إنشاء حساب</a>
    {% endif %}
  </div> 
</header>

<nav class="nav">
  <a href="/" style="background:linear-gradient(110deg,#9b37ff,#315dff);color:#fff;"><span>🏠</span> الرئيسية</a>
  <a href="/game" style="background:linear-gradient(135deg,#ec4899,#8b5cf6);color:#fff;"><span>🎮</span> لعبة الذاكرة والروبوت</a>
  <a href="/spin" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;"><span>🎡</span> عجلة الحظ السينمائية</a>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank"><span>💬</span> الدعم والمطور</a>
</nav>

<main class="layout">
  <aside>
    <div style="background:#07132c;border:1px solid #315dff;border-radius:18px;padding:16px;">
      <h4 style="margin:0 0 10px;">💳 رصيدك الحالي</h4>
      <h2 style="color:#35eaa1;margin:0;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
    </div>
  </aside>

  <section>
    {% if posts %}
    <div style="margin-bottom:25px;">
      <h2><span>📢</span> أخبار وإعلانات المتجر</h2>
      {% for post in posts %}
      <div class="post-card">
        <h3 style="color:#38bdf8;margin:0 0 5px;">{{ post["title"] }}</h3>
        <p style="font-size:12px;color:#cbd5e1;margin:0;">{{ post["content"] }}</p>
        {% if post["image_url"] %}
          <img src="{{ post['image_url'] }}">
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <h2>🔥 أحدث المنتجات</h2>
    <div class="product-grid">
      {% for p in products %}
      <div class="product-card">
        {% if p["image_url"] %}
          <img src="{{ p['image_url'] }}" class="product-img">
        {% else %}
          <div style="height:150px;display:grid;place-items:center;font-size:35px;background:#03091b;border-radius:10px;">{{ p["icon"] }}</div>
        {% endif %}
        <h3 style="margin:8px 0 4px;font-size:13px;">{{ p["name"] }}</h3>
        <p style="font-size:10px;color:#a8b7d8;margin:0 0 8px;">{{ p["description"] }}</p>
        <span style="color:#35eaa1;font-weight:bold;display:block;margin-bottom:8px;">{{ p["price"] }}</span>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شراء%20${encodeURIComponent(p['name'])}" target="_blank" class="add-btn">شراء فوري 💳</a>
      </div>
      {% endfor %}
    </div>
  </section>
</main>
</body>
</html>
"""

# ==================== عجلة الحظ السينمائية والسينما ====================
SPIN_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>عجلة الحظ التفاعلية السينمائية | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#0f1c3f 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;overflow:hidden;}
.stage-box { position: relative; width: 360px; display: flex; flex-direction: column; align-items: center; }
.robot-head { font-size: 65px; filter: drop-shadow(0 0 20px #38bdf8); transition: all 0.3s ease; margin-bottom: 5px; z-index: 5; }
.robot-arm { position: absolute; top: 70px; right: 20px; width: 100px; height: 18px; background: linear-gradient(90deg, #38bdf8, #315dff); border-radius: 10px; transform-origin: right center; transform: rotate(20deg); transition: transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 0 15px #315dff88; z-index: 8; }
.robot-arm::before { content: '🦾'; position: absolute; left: -15px; top: -10px; font-size: 28px; }
.robot-arm.pulling { transform: rotate(-55deg) scale(1.15); }
.wheel-container{position:relative;width:310px;height:310px;display:flex;align-items:center;justify-content:center;margin-top:10px;}
.pointer{position:absolute;top:-18px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:16px solid transparent;border-right:16px solid transparent;border-top:28px solid #ff3b3b;z-index:10;filter:drop-shadow(0 0 10px #ff3b3b);}
canvas{width:100%;height:100%;border-radius:50%;transition: transform 5s cubic-bezier(0.15, 0.9, 0.15, 1); border: 4px solid #315dff; box-shadow: 0 0 35px rgba(49,93,255,0.6);}
.spin-btn{position:absolute;width:75px;height:75px;border-radius:50%;background:radial-gradient(circle,#9b37ff,#315dff);border:3px solid #fff;color:#fff;font-weight:900;font-size:15px;cursor:pointer;z-index:5;box-shadow:0 0 20px #9b37ff;}
.modal{display:none;position:fixed;inset:0;background:#03091bee;backdrop-filter:blur(12px);z-index:100;place-items:center;padding:20px;}
.modal-content{background:linear-gradient(145deg,#07132c,#0b1e47);border:2px solid #35eaa1;border-radius:20px;padding:25px;text-align:center;max-width:360px;width:100%;box-shadow:0 0 30px #35eaa166;}
</style>
</head>
<body>
<div style="text-align:center;margin-bottom:10px;">
  <h1 style="font-size:24px;margin:0;color:#38bdf8;">🤖 الروبوت نُوفا يُدير عجلة الحظ</h1>
  <p style="color:#a8b7d8;font-size:12px;">شاهد الروبوت ينفذ الحركة السينمائية لسحب العجلة!</p>
</div>
<div class="stage-box">
  <div class="robot-head" id="robotHead">🤖</div>
  <div class="robot-arm" id="robotArm"></div>
  <div class="wheel-container">
    <div class="pointer"></div>
    <canvas id="wheel" width="500" height="500"></canvas>
    <button class="spin-btn" id="spinBtn">أَدِرْ!</button>
  </div>
</div>
<a href="/" style="color:#8198ff;text-decoration:none;margin-top:20px;font-size:13px;font-weight:bold;">← العودة للمتجر الرئيسي</a>
<div class="modal" id="resultModal">
  <div class="modal-content">
    <div style="font-size:55px;" id="modalEmoji">😃</div>
    <h2 id="prizeTitle" style="color:#35eaa1;margin:5px 0;">مبروك!</h2>
    <p id="prizeDesc" style="color:#a8b7d8;font-size:13px;"></p>
    <button onclick="location.href='/'" style="margin-top:15px;padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;width:100%;">استلام الهدية وتصفح المتجر 🚀</button>
  </div>
</div>
<script>
function playSound(type) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(120, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(400, ctx.currentTime + 3);
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 3);
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(); osc.stop(ctx.currentTime + 3);
  } catch(e){}
}
const canvas = document.getElementById('wheel');
const ctx = canvas.getContext('2d');
const spinBtn = document.getElementById('spinBtn');
const robotHead = document.getElementById('robotHead');
const robotArm = document.getElementById('robotArm');
const items = [
  { label: '5 جنيه 💰', color: '#8d38ff' },
  { label: 'حظ أوفر 😅', color: '#1b2a4a' },
  { label: '10 جنيه 💳', color: '#315dff' },
  { label: 'خصم 20% 🏷️', color: '#00c853' },
  { label: '20 جنيه 🎁', color: '#ff9100' },
  { label: 'حظ أوفر 😅', color: '#263d70' }
];
const numItems = items.length;
const arc = (2 * Math.PI) / numItems;
function drawWheel() {
  const radius = canvas.width / 2;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < numItems; i++) {
    const angle = i * arc;
    ctx.beginPath();
    ctx.fillStyle = items[i].color;
    ctx.moveTo(radius, radius);
    ctx.arc(radius, radius, radius - 8, angle, angle + arc);
    ctx.lineTo(radius, radius);
    ctx.fill();
    ctx.save();
    ctx.translate(radius, radius);
    ctx.rotate(angle + arc / 2);
    ctx.textAlign = "right";
    ctx.fillStyle = "#fff";
    ctx.font = "bold 22px Cairo";
    ctx.fillText(items[i].label, radius - 35, 8);
    ctx.restore();
  }
}
drawWheel();
let isSpinning = false;
spinBtn.addEventListener('click', () => {
  if (isSpinning) return;
  isSpinning = true;
  robotHead.textContent = '⚙️';
  robotArm.classList.add('pulling');
  playSound('spin');
  setTimeout(() => { robotArm.classList.remove('pulling'); robotHead.textContent = '🤖'; }, 700);
  fetch('/spin', {method: 'POST'}).then(res => res.json()).then(data => {
    if (data.status === 'error') { isSpinning = false; alert(data.message); return; }
    const targetDegree = (360 - (data.index * (360 / numItems)) - ((360 / numItems) / 2)) + (360 * 5);
    canvas.style.transform = `rotate(${targetDegree}deg)`;
    setTimeout(() => {
      isSpinning = false;
      robotHead.textContent = '😃';
      document.getElementById('prizeTitle').textContent = 'نتيجة عجلة الحظ!';
      document.getElementById('prizeDesc').textContent = data.msg;
      document.getElementById('resultModal').style.display = 'grid';
    }, 5000);
  });
});
</script>
</body>
</html>
"""

# ==================== لعبة الذاكرة والروبوت ====================
GAME_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لعبة الذاكرة التفاعلية | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#1e0836 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;}
.robot-companion { display: flex; align-items: center; gap: 15px; background: #07132c; border: 1px solid #315dff; padding: 12px 20px; border-radius: 18px; margin-bottom: 15px; }
.memory-grid { display: grid; grid-template-columns: repeat(4, 75px); gap: 12px; background: #07132c; padding: 15px; border-radius: 20px; border: 2px solid #8d38ff; }
.card-item { width: 75px; height: 90px; background: linear-gradient(145deg, #0f244a, #09132a); border: 2px solid #315dff; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 32px; cursor: pointer; transition: 0.3s; }
.card-item.flipped { background: linear-gradient(145deg, #276bff, #bc5bff); }
.card-item.matched { background: linear-gradient(145deg, #059669, #10b981); cursor: default; }
</style>
</head>
<body>
<div class="robot-companion">
  <div id="gameRobotAvatar" style="font-size:40px;">🤖</div>
  <div id="robotSpeech" style="font-size:13px;color:#35eaa1;font-weight:bold;">مرحباً بك! طابق الكروت لأظهر لك مهاراتي.</div>
</div>
<div class="memory-grid" id="memoryGrid"></div>
<a href="/" style="margin-top:20px;padding:10px 20px;background:#1e293b;color:white;text-decoration:none;border-radius:10px;font-weight:bold;font-size:12px;">← العودة للمتجر الرئيسية</a>
<script>
const emojis = ['🎮', '▶', '👑', '💳', '🪙', '🎁'];
let cards = [...emojis, ...emojis].sort(() => Math.random() - 0.5);
let flippedCards = [], matchedPairs = 0;
const grid = document.getElementById('memoryGrid');
const speech = document.getElementById('robotSpeech');
const avatar = document.getElementById('gameRobotAvatar');
cards.forEach((icon) => {
  const card = document.createElement('div');
  card.className = 'card-item';
  card.dataset.icon = icon;
  card.innerHTML = '❓';
  card.onclick = function() {
    if (flippedCards.length >= 2 || this.classList.contains('flipped') || this.classList.contains('matched')) return;
    this.classList.add('flipped');
    this.innerHTML = this.dataset.icon;
    flippedCards.push(this);
    if (flippedCards.length === 2) {
      if (flippedCards[0].dataset.icon === flippedCards[1].dataset.icon) {
        flippedCards[0].classList.add('matched');
        flippedCards[1].classList.add('matched');
        flippedCards = [];
        matchedPairs++;
        avatar.textContent = '😃';
        speech.textContent = 'أحسنت! مطابقة رائعة! 👏';
        if (matchedPairs === emojis.length) { avatar.textContent = '👑'; speech.textContent = '🏆 مبروك! أنت بطل اللعبة!'; }
      } else {
        avatar.textContent = '🤔';
        speech.textContent = 'حاول مرة أخرى.. ركز!';
        setTimeout(() => {
          flippedCards[0].classList.remove('flipped');
          flippedCards[1].classList.remove('flipped');
          flippedCards[0].innerHTML = '❓';
          flippedCards[1].innerHTML = '❓';
          flippedCards = [];
          avatar.textContent = '🤖';
        }, 700);
      }
    }
  };
  grid.appendChild(card);
});
</script>
</body>
</html>
"""

# ==================== صفحة التسجيل والتحقق الفورية ====================
REGISTER_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>إنشاء حساب جديد | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;display:grid;place-items:center;min-height:100vh;}
.box{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:380px;box-shadow:0 10px 30px rgba(49,93,255,0.2);}
input, select{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;font-size:12px;}
button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;margin-top:10px;font-size:13px;}
</style>
</head>
<body>
<div class="box">
  <div style="text-align:center;margin-bottom:15px;">
    <h2 style="margin:0 0 5px;color:#35eaa1;">🛡️ إنشاء حساب جديد</h2>
  </div>

  {% if step == 1 %}
  <form method="post">
    <input name="name" placeholder="الاسم الكامل" required>
    <input type="email" name="email" placeholder="البريد الإلكتروني" required>
    <input type="password" name="password" placeholder="كلمة المرور (6 أحرف فأكثر)" required>
    
    <label style="font-size:11.5px;color:#cbd5e1;display:block;margin-top:8px;">طريقة استلام الكود:</label>
    <select name="method" style="margin-bottom:10px;">
      <option value="email">📧 البريد الإلكتروني</option>
      <option value="telegram">🤖 بوت التليجرام</option>
    </select>

    <button type="submit">إرسال كود التحقق 🔐</button>
  </form>
  {% else %}
  <form method="post">
    <div style="background:#03091b;padding:12px;border-radius:10px;border:1px solid #35eaa1;margin-bottom:15px;text-align:center;">
      <span style="font-size:12px;color:#35eaa1;display:block;">تم توليد كود التحقق!</span>
      {% if auto_code %}
        <p style="font-size:15px;color:#facc15;font-weight:bold;margin:8px 0 0;background:#07132c;padding:6px;border-radius:6px;border:1px dashed #35eaa1;">🔑 كود التحقق الخاص بك: {{ auto_code }}</p>
      {% endif %}
    </div>
    <input name="code" placeholder="أدخل كود التحقق المكون من 6 أرقام" required style="text-align:center;font-size:16px;letter-spacing:2px;">
    <button type="submit">تأكيد الحساب والدخول 🚀</button>
  </form>
  {% endif %}

  {% if error %}<p style="color:#ff7777;font-size:12px;margin-top:10px;text-align:center;">{{ error }}</p>{% endif %}
  <a href="/login" style="color:#8198ff;display:block;margin-top:15px;text-align:center;font-size:12px;text-decoration:none;">لديك حساب بالفعل؟ تسجيل الدخول</a>
</div>
</body>
</html>
"""

LOGIN_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>تسجيل الدخول | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;display:grid;place-items:center;min-height:100vh;}
.box{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:15px;width:360px;}
input{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;}
button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;margin-top:10px;}
</style>
</head>
<body>
<div class="box">
  <h2>تسجيل الدخول</h2>
  <form method="post">
    <input type="email" name="email" placeholder="البريد الإلكتروني" required>
    <input type="password" name="password" placeholder="كلمة المرور" required>
    <button type="submit">دخول</button>
  </form>
  {% if error %}<p style="color:#ff7777;font-size:12px;margin-top:10px;">{{ error }}</p>{% endif %}
  <a href="/register" style="color:#8198ff;display:block;margin-top:15px;text-align:center;font-size:12px;text-decoration:none;">إنشاء حساب جديد</a>
</div>
</body>
</html>
"""

ADMIN_PANEL_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لوحة التحكم | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;padding:20px;}
.admin-container{max-width:900px;margin:auto;}
.box{background:#07132c;border:1px solid #315dff;border-radius:15px;padding:20px;margin-bottom:20px;}
h3{margin-top:0;color:#35eaa1;}
input, textarea{width:100%;padding:10px;margin:4px 0 10px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:white;box-sizing:border-box;}
button{width:100%;padding:11px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:white;font-weight:bold;cursor:pointer;}
</style>
</head>
<body>
<div class="admin-container">
  <h2>⚙️ لوحة تحكم المطور</h2>
  <div class="box">
    <h3>📢 نشر خبر / إعلان جديد</h3>
    <form method="POST" action="/admin/add_post" enctype="multipart/form-data">
      <input name="title" placeholder="عنوان المنشور" required>
      <textarea name="content" placeholder="محتوى الإعلان" required style="height:60px;"></textarea>
      <input type="file" name="image_file" accept="image/*" style="background:#0a1a3f;padding:8px;">
      <button type="submit">نشر المنشور</button>
    </form>
  </div>
  <div class="box">
    <h3>📦 إضافة منتج جديد</h3>
    <form method="POST" action="/admin/add_product" enctype="multipart/form-data">
      <input name="name" placeholder="اسم المنتج" required>
      <input name="description" placeholder="الوصف" required>
      <input type="number" step="0.01" name="price_val" placeholder="السعر الرقمي" required>
      <input name="price" placeholder="السعر النصي (مثال: 500 جـ)" required>
      <input name="code" placeholder="الكود" required>
      <input type="file" name="image_file" accept="image/*" style="background:#0a1a3f;padding:8px;">
      <input name="icon" placeholder="الأيقونة (مثال: ▶)" required>
      <input name="category" placeholder="القسم" required>
      <button type="submit">إضافة المنتج</button>
    </form>
  </div>
  <a href="/" style="color:#8198ff;text-decoration:none;font-weight:bold;">← العودة للمتجر</a>
</div>
</body>
</html>
"""

# ==================== المسارات والروابط ====================

@app.route('/game')
def game():
    return render_template_string(GAME_PAGE)

@app.route('/spin', methods=["GET", "POST"])
def spin():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    today_str = time.strftime("%Y-%m-%d")
    if request.method == "POST":
        if user["last_spin_date"] == today_str:
            return jsonify({"status": "error", "message": "استخدمت فرتك اليومية! عد غداً 🎁"})
        selectedIndex = secrets.randbelow(6)
        prizes = [{'label': '5 جنيه 💰', 'amount': 5}, {'label': 'حظ أوفر 😅', 'amount': 0}, {'label': '10 جنيه 💳', 'amount': 10}, {'label': 'خصم 20% 🏷️', 'amount': 0}, {'label': '20 جنيه 🎁', 'amount': 20}, {'label': 'حظ أوفر 😅', 'amount': 0}]
        prize = prizes[selectedIndex]
        with get_db() as db:
            db.execute("UPDATE users SET balance = balance + ?, last_spin_date = ? WHERE email = ?", (prize['amount'], today_str, email))
        msg = f"فزت بـ ({prize['label']})!" if prize['amount'] > 0 else "حظ أفضل المرة القادمة!"
        return jsonify({"status": "success", "index": selectedIndex, "msg": msg})
    return render_template_string(SPIN_PAGE)

@app.route('/register', methods=["GET", "POST"])
def register():
    error = ""
    step = 1
    auto_code = ""
    if request.method == "POST":
        if "code" not in request.form:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or "@" not in email or len(password) < 6:
                error = "يرجى كتابة البيانات كاملة (كلمة المرور 6 أحرف على الأقل)."
            else:
                with get_db() as db:
                    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                    if existing:
                        error = "هذا البريد مسجل مسبقاً."
                    else:
                        code = str(secrets.randbelow(900000) + 100000)
                        db.execute("INSERT OR REPLACE INTO email_codes (email, code, expires_at) VALUES (?, ?, ?)", (email, code, int(time.time()) + 300))
                        send_email_code(email, code)
                        auto_code = code  # تظهر مباشرة على الشاشة لحل المشكلة نهائياً
                        session["temp_reg"] = {"name": name, "email": email, "password": generate_password_hash(password)}
                        step = 2
        else:
            entered_code = request.form.get("code", "").strip()
            temp = session.get("temp_reg")
            if not temp:
                return redirect(url_for("register"))
            with get_db() as db:
                record = db.execute("SELECT * FROM email_codes WHERE email = ?", (temp["email"],)).fetchone()
                if record and record["code"] == entered_code:
                    my_ref = "REF" + str(secrets.randbelow(899999) + 100000)
                    db.execute("INSERT INTO users (name, email, password_hash, balance, verified, ref_code, created_at) VALUES (?, ?, ?, 0.0, 1, ?, ?)", (temp["name"], temp["email"], temp["password"], my_ref, int(time.time())))
                    session["user_email"] = temp["email"]
                    session.pop("temp_reg", None)
                    return redirect(url_for("home"))
                else:
                    error = "كود التحقق غير صحيح."
                    step = 2
    return render_template_string(REGISTER_PAGE, error=error, step=step, auto_code=auto_code)

@app.route("/login", methods=["GET", "POST"])
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
    return render_template_string(LOGIN_PAGE, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
def admin_panel():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    return render_template_string(ADMIN_PANEL_PAGE)

@app.route("/admin/add_post", methods=["POST"])
def admin_add_post():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    image_url = ""
    file = request.files.get("image_file")
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_name = f"post_{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
        image_url = f"/static/uploads/{unique_name}"
    if title and content:
        with get_db() as db:
            db.execute("INSERT INTO posts (title, content, image_url, created_at) VALUES (?, ?, ?, ?)", (title, content, image_url, int(time.time())))
    return redirect(url_for("admin_panel"))

@app.route("/admin/add_product", methods=["POST"])
def admin_add_product():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    name = request.form.get("name")
    description = request.form.get("description")
    price_val = float(request.form.get("price_val", 0))
    price = request.form.get("price")
    code = request.form.get("code")
    icon = request.form.get("icon", "▶")
    category = request.form.get("category")
    image_url = ""
    file = request.files.get("image_file")
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_name = f"{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
        image_url = f"/static/uploads/{unique_name}"
    with get_db() as db:
        db.execute("INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '#315dff', 'جديد')", (name, description, price_val, price, code, icon, image_url, category))
    return redirect(url_for("admin_panel"))

@app.route("/")
def home():
    email = session.get("user_email")
    user = None
    is_admin = False
    if email:
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        is_admin = (email == ADMIN_EMAIL)
    products = get_products()
    posts = get_posts()
    return render_template_string(PAGE, products=products, posts=posts, user=user, is_admin=is_admin, admin_telegram=ADMIN_TELEGRAM_USERNAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
