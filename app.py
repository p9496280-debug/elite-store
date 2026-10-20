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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
AVATARS_FOLDER = os.path.join(app.root_path, 'static', 'avatars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATARS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AVATARS_FOLDER'] = AVATARS_FOLDER

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "moh99zzhvni893fj7@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "mohammedaaa222")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")
ADMIN_TELEGRAM_USERNAME = "Mido_M9do"
TELEGRAM_BOT_USERNAME = "midoassistantAIbot"
TELEGRAM_CHANNEL_LINK = "https://t.me/Midomsn"

# البريد الإلكتروني المعتمد للدعم وإرسال الأكواد
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
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_percent REAL NOT NULL,
                active INTEGER DEFAULT 1
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
        else:
            db.execute("""
                UPDATE users SET password_hash = ?, verified = 1 WHERE email = ?
            """, (generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL))

        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("كود جوجل بلاي (10$)", "الولايات المتحدة", 500.00, "500 جـ", "GPLAY-9876", "▶", "", "بطاقات الألعاب", "#35eaa1", "عروض سريعة 🔥"),
                ("كود بلايستيشن (20$)", "الولايات المتحدة", 1000.00, "1000 جـ", "PSN-5432", "PS", "", "بطاقات الألعاب", "#62a0ff", "مميز"),
                ("كود إكس بوكس (25$)", "الولايات المتحدة", 1250.00, "1250 جـ", "XBOX-3344", "ⓧ", "", "بطاقات الألعاب", "#5dff9c", None),
                ("كود ستيم (20$)", "الولايات المتحدة", 1000.00, "1000 جـ", "STEAM-1122", "◉", "", "بطاقات الألعاب", "#9bb8ff", "عرض خاص"),
                ("كود آيتونز (15$)", "الولايات المتحدة", 750.00, "750 جـ", "ITUNES-7788", "", "", "بطاقات الهدايا", "#ffc107", None),
                ("شحن ببجي 660 شدة", "شحن فوري عن طريق الايدي", 350.00, "350 جـ", "PUBG-660", "🎮", "", "ألعاب", "#ff3b3b", "شائع 🔥"),
                ("10 دولار USDT (TRC20)", "تحويل فوري لمحفظتك الرقمية", 500.00, "500 جـ", "USDT-10", "🪙", "", "عملات رقمية ودولارات", "#facc15", "جديد 🔥"),
                ("بطاقة فيزا وهمية $10 (كارت افتراضي)", "صالحة لتفعيل الحسابات للشراء أونلاين", 550.00, "550 جـ", "VISA-10", "💳", "", "بطاقات الدفع", "#38bdf8", "الأكثر طلباً"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)

        cursor_rev = db.execute("SELECT COUNT(*) as count FROM reviews")
        if cursor_rev.fetchone()["count"] == 0:
            default_reviews = [
                ("أحمد مصطفى", 5, "متجر ممتاز جداً والتسليم فور تسليم التحويل أنصح بالتعامل معه 🔥", int(time.time())),
                ("محمود علي", 5, "مصداقية عالية وسرعة في الشحن شكراً للمطور!", int(time.time())),
            ]
            db.executemany("INSERT INTO reviews (user_name, rating, comment, created_at) VALUES (?, ?, ?, ?)", default_reviews)

        db.execute("INSERT OR IGNORE INTO promo_codes (code, discount_percent) VALUES ('MIDO2026', 10.0)")


init_db()


@app.after_request
def add_header(response):
    response.headers['X-Robots-Tag'] = 'index, follow, max-image-preview:large'
    return response


def send_telegram_code(chat_id, code):
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"🔐 كود التحقق الرسمي من NOVA STORE هو: {code}\nصالح لمدة 5 دقائق فقط."
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass


def send_email_code(to_email, code):
    msg = MIMEMultipart()
    msg['From'] = f"NOVA STORE Support <{SUPPORT_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = "🔐 رمز التحقق الخاص بك لحساب NOVA STORE"

    html_content = f"""
    <div dir="rtl" style="font-family:'Cairo',sans-serif; background:#03091b; color:#fff; padding:30px; border-radius:16px; border:1px solid #315dff;">
      <h2 style="color:#35eaa1; margin-top:0;">🛡️ NOVA STORE - التحقق الرسمي</h2>
      <p style="color:#cbd5e1; font-size:14px;">مرحباً بك! لقد طلبت إنشاء حساب جديد في متجرنا الرقمي.</p>
      <div style="background:#07132c; border:1px solid #35eaa1; padding:15px; text-align:center; border-radius:12px; margin:20px 0;">
        <span style="font-size:12px; color:#a8b7d8; display:block;">كود التحقق الخاص بك:</span>
        <h1 style="color:#35eaa1; font-size:32px; letter-spacing:4px; margin:5px 0;">{code}</h1>
      </div>
      <p style="font-size:11px; color:#8194ba;">هذا الكود صالح لمدة 5 دقائق فقط. إذا لم تقم بطلب هذا الكود، يرجى تجاهل هذه الرسالة.</p>
      <hr style="border-color:#1b315c; margin:20px 0;">
      <small style="color:#557099;">© 2026 NOVA STORE - جميع الحقوق محفوظة ({SUPPORT_EMAIL})</small>
    </div>
    """
    msg.attach(MIMEText(html_content, 'html'))

    if SUPPORT_EMAIL_PASSWORD:
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SUPPORT_EMAIL, SUPPORT_EMAIL_PASSWORD)
            server.sendmail(SUPPORT_EMAIL, to_email, msg.as_string())
            server.quit()
        except Exception:
            pass


def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in rows]


def get_reviews():
    with get_db() as db:
        rows = db.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 6").fetchall()
        return [dict(row) for row in rows]


def get_posts():
    with get_db() as db:
        rows = db.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def get_promo_codes():
    with get_db() as db:
        rows = db.execute("SELECT * FROM promo_codes ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def get_setting(key, default=""):
    with get_db() as db:
        row = db.execute("SELECT value FROM store_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


# ==================== الواجهة الرئيسية للمتجر ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="-cqasmgepuPXVxFHJ53UtVgI4DdfCiGR_MbwjVIVv0M" />
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#03091b">

<title>NOVA STORE | المتجر الرقمي الشامل لبطاقات الألعاب والدفع</title>
<meta name="description" content="متجر NOVA STORE هو متجرك الرقمي الأول لشحن بطاقات جوجل بلاي، بلايستيشن، إكس بوكس، العملات الرقمية وبطاقات الفيزا والدفع عبر فودافون كاش.">
<meta property="og:site_name" content="NOVA STORE">
<meta property="og:title" content="NOVA STORE | المتجر الرقمي الشامل">
<meta property="og:description" content="متجر NOVA STORE لشحن الألعاب والبطاقات الرقمية والدفع الآمن.">
<meta property="og:image" content="/logo.svg">
<link rel="icon" type="image/svg+xml" href="/logo.svg">

<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff;--border:#1b315c}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.topbar{min-height:78px;display:flex;align-items:center;gap:20px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:10}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white}.brand b{color:#754bff}.brand-mark{width:39px;height:39px;display:grid;place-items:center;font-size:33px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.search{height:44px;max-width:420px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:30px;padding:0 17px;background:#09132b}
.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:13px}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.user-profile-badge {display: flex; align-items: center; gap: 10px; background: #0b1734; border: 1px solid #315dff; padding: 6px 14px; border-radius: 30px; text-decoration: none; box-shadow: 0 0 10px rgba(49,93,255,0.3);}
.user-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-weight: bold; color: white; border: 2px solid #35eaa1; box-shadow: 0 0 8px #35eaa188; overflow:hidden;}

.nav { min-height: 58px; padding: 0 4%; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #1a2d54; background: linear-gradient(180deg, #07122b 0%, #040a1b 100%); overflow-x: auto; scrollbar-width: none; }
.nav::-webkit-scrollbar { display: none; }
.nav a { color: #c4cde3; text-decoration: none; padding: 8px 16px; border-radius: 12px; font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); }
.nav a.active { background: linear-gradient(110deg, #9b37ff, #315dff); color: #ffffff; border-color: transparent; }
.nav-badge-game { background: linear-gradient(135deg, #ec4899, #8b5cf6) !important; color: #fff !important; font-weight: bold; }
.nav-badge-spin { background: linear-gradient(135deg, #f59e0b, #d97706) !important; color: #fff !important; font-weight: bold; }
.admin-badge { background: #570f0f; color: #ff7777; border: 1px solid #ff5555; padding: 6px 14px; border-radius: 12px; font-weight: bold; text-decoration:none;}

.layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:22px;padding:22px 4%}
@media (max-width:850px){ .layout{grid-template-columns:1fr;} }
.main-column{min-width:0}

.hero{min-height:280px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b);padding:25px;align-items:center;}
.hero h1{font-size:clamp(20px,2vw,28px);line-height:1.6;margin:0 0 10px;font-weight:800}
.hero p{color:#c4cce2;font-size:12px;line-height:1.8;margin:0 0 15px}
.hero-btn{display:inline-flex;align-items:center;gap:10px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;cursor:pointer;}

.categories{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin:20px 0}
.category{border:1px solid #172d53;border-radius:12px;background:linear-gradient(150deg,#07152e,#050d20);padding:14px 8px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;cursor:pointer;transition:0.2s}
.category span{font-size:22px;color:#65baff}
.category b{font-size:11px}

.section-heading{display:flex;align-items:center;justify-content:space-between;margin:25px 0 12px}
.section-heading h2{font-size:18px;margin:0;display:flex;align-items:center;gap:8px}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:14px;padding:12px;position:relative;transition:0.2s}
.product-visual{height:160px;border-radius:10px;background:radial-gradient(circle at 50% 20%,#1b3159,transparent 70%),#07142c;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;margin-bottom:10px;overflow:hidden;}
.product-img{width:100%;height:100%;object-fit:contain;border-radius:10px;}
.price{font-size:13.5px;font-weight:800;color:#35eaa1}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;cursor:pointer;text-decoration:none;}

/* أبعاد صور المنشورات المحدثة لتظهر بالكامل */
.posts-feed {display:flex;flex-direction:column;gap:15px;margin-bottom:25px;}
.post-card {background:linear-gradient(145deg,#0b1938,#07122b);border:1px solid #315dff;border-radius:16px;padding:16px;box-shadow:0 4px 20px rgba(49,93,255,0.15);}
.post-card h3 {margin:0 0 8px;font-size:15px;color:#38bdf8;display:flex;align-items:center;gap:8px;}
.post-card p {font-size:12px;color:#cbd5e1;line-height:1.7;margin:0 0 10px;}
.post-card img {
  width:100%;
  max-height:450px;
  object-fit:contain;
  border-radius:12px;
  margin-bottom:10px;
  border:1px solid #1f3a70;
  background:#03091b;
}

footer{border-top:1px solid #192b4e;padding:30px 4%;background:#030714;margin-top:40px;color:#aab9d8;font-size:11px;text-align:center;}
</style>
</head>
<body>

<header class="topbar">
  <a class="brand" href="/"><span class="brand-mark">N</span><span>NOVA <b>STORE</b></span></a>
  <div class="search"><span>⌕</span><input id="searchInput" type="search" placeholder="ابحث عن أي منتج..." onkeyup="filterProducts()"></div>
  <div class="header-actions">
    {% if is_admin %}
      <a href="/admin" class="admin-badge">⚙️ لوحة المطور</a>
    {% endif %}
    {% if user %}
      <a href="/account" class="user-profile-badge">
        <div class="user-avatar">
          {% if user["avatar"].startswith('http') or user["avatar"].startswith('/') %}
            <img src="{{ user['avatar'] }}" style="width:100%;height:100%;object-fit:cover;">
          {% else %}
            {{ user["avatar"] }}
          {% endif %}
        </div>
        <div>
          <span style="font-size:11px;font-weight:bold;display:block;">{{ user["name"] }}</span>
          <span style="font-size:9px;color:#35eaa1;">{{ user["status_title"] }} | {{ user["balance"] }} جـ</span>
        </div>
      </a>
    {% else %}
      <a href="/login" style="color:#d8e2ff;text-decoration:none;font-size:12px;">تسجيل الدخول</a>
      <a href="/register" style="padding:8px 14px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;">إنشاء حساب</a>
    {% endif %}
  </div> 
</header>

<nav class="nav">
  <a href="/" class="active"><span>🏠</span> الرئيسية</a>
  <a href="/game" class="nav-badge-game"><span>🎮</span> الألعاب الترفيهية</a>
  <a href="/spin" class="nav-badge-spin"><span>🎡</span> عجلة الحظ اليومية</a>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank"><span>💬</span> الدعم والمطور</a>
  <a href="{{ telegram_channel }}" target="_blank"><span>📢</span> القناة الرسمية</a>
</nav>

<main class="layout">
  <aside class="sidebar-left">
    <div style="background:#07132c;border:1px solid #315dff;border-radius:18px;padding:16px;margin-bottom:15px;">
      <h4 style="margin:0 0 10px;color:#fff;">💳 محفظتك الرقمية</h4>
      <div style="background:#03091b;padding:12px;border-radius:12px;text-align:center;">
        <span style="font-size:11px;color:#a8b7d8;">الرصيد المتاح</span>
        <h2 style="margin:5px 0;color:#35eaa1;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
      </div>
    </div>

    <div style="background:linear-gradient(135deg, #1f072b, #0d041c);border:1px solid #ec4899;border-radius:18px;padding:16px;">
      <h4 style="margin:0 0 8px;color:#fff;">🎮 لعبة الذاكرة</h4>
      <p style="font-size:10px;color:#a8b7d8;margin:0 0 10px;">اختبر ذاكرتك وسرعتك مجاناً الآن للترفيه!</p>
      <a href="/game" style="display:block;text-align:center;padding:8px;background:linear-gradient(110deg,#ec4899,#8b5cf6);color:#fff;border-radius:8px;text-decoration:none;font-size:11px;font-weight:bold;">🕹️ ابدأ اللعب فوراً</a>
    </div>
  </aside>

  <section class="main-column">
    <div class="hero">
      <div>
        <span style="color:#bca0ff;font-size:11px;font-weight:bold;">عالمك الرقمي الأول</span>
        <h1>شحن بطاقات وأكواد الألعاب بأفضل الأسعار والتسليم الفوري!</h1>
        <p>اختر منتجك المفضل واشترِ الآن باستخدام فودافون كاش أو بطاقة الائتمان.</p>
        <a class="hero-btn" href="#products">تسوق الآن ←</a>
      </div>
      <div></div>
    </div>

    {% if posts %}
    <div style="margin-top:25px;">
      <div class="section-heading">
        <h2><span>📢</span> أخبار وإعلانات المطور المباشرة</h2>
      </div>
      <div class="posts-feed">
        {% for post in posts %}
        <div class="post-card">
          <h3>👑 {{ post['title'] }}</h3>
          <p>{{ post['content'] }}</p>
          {% if post['image_url'] %}
            <img src="{{ post['image_url'] }}" alt="Post image">
          {% endif %}
          {% if post['link_url'] %}
            <a href="{{ post['link_url'] }}" target="_blank" style="display:inline-block;padding:6px 14px;background:#315dff;color:#fff;border-radius:8px;font-size:11px;font-weight:bold;text-decoration:none;">🔗 اضغط هنا للانتقال للرابط المرفق</a>
          {% endif %}
        </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    <div class="categories">
      <div class="category" onclick="filterCat('الكل')"><span>▦</span><b>الكل</b></div>
      <div class="category" onclick="filterCat('بطاقات الألعاب')"><span style="color:#35eaa1;">▶</span><b>بطاقات الألعاب</b></div>
      <div class="category" onclick="filterCat('بطاقات الهدايا')"><span style="color:#bc5bff;">🎁</span><b>بطاقات الهدايا</b></div>
      <div class="category" onclick="filterCat('ألعاب')"><span style="color:#ff3b3b;">🎮</span><b>الألعاب والشحن</b></div>
      <div class="category" onclick="filterCat('عملات رقمية ودولارات')"><span style="color:#facc15;">🪙</span><b>عملات رقمية ودولارات</b></div>
      <div class="category" onclick="filterCat('بطاقات الدفع')"><span style="color:#38bdf8;">💳</span><b>بطاقات الدفع</b></div>
    </div>

    <div class="section-heading" id="products">
      <h2><span>🔥</span> أحدث المنتجات</h2>
    </div>
    <div class="product-grid" id="productGrid"></div>
  </section>
</main>

<footer>
  <p>© 2026 NOVA STORE - جميع الحقوق محفوظة | البريد المعتمد والدعم: {{ support_email }}</p>
</footer>

<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');

function renderProducts(items) {
  productGrid.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let visualHtml = p.image_url ? `<img src="${p.image_url}" class="product-img">` : `<span style="color:${p.color};">${p.icon}</span>`;
    card.innerHTML = `
      <div class="product-visual">${visualHtml}</div>
      <h3 style="color:#fff;font-size:13px;margin:5px 0;">${p.name}</h3>
      <p style="font-size:10px;color:#8fa1c4;">${p.description}</p>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
        <span class="price">${p.price}</span>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شراء%20${encodeURIComponent(p.name)}" target="_blank" class="add-btn">شراء فوري 💳</a>
      </div>`;
    productGrid.appendChild(card);
  });
}

function filterCat(cat) {
  if (cat === 'الكل') renderProducts(PRODUCTS);
  else renderProducts(PRODUCTS.filter(x => x.category === cat));
}

function filterProducts() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  renderProducts(PRODUCTS.filter(x => x.name.toLowerCase().includes(query)));
}

renderProducts(PRODUCTS);
</script>
</body>
</html>
"""

# ==================== عجلة الحظ السينمائية التفاعلية ====================
SPIN_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>عجلة الحظ التفاعلية مع الروبوت | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#0f1c3f 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;overflow:hidden;}

.spin-stage { position: relative; width: 360px; height: 440px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.robot-head { font-size: 50px; filter: drop-shadow(0 0 15px #38bdf8); transition: transform 0.3s ease; margin-bottom: 5px; z-index: 5; }
.robot-arm { position: absolute; top: 45px; left: -20px; width: 90px; height: 20px; background: linear-gradient(90deg, #38bdf8, #315dff); border-radius: 10px; transform-origin: left center; transform: rotate(-30deg); transition: transform 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55); box-shadow: 0 0 15px #315dff88; z-index: 8; }
.robot-arm::after { content: '🦾'; position: absolute; right: -15px; top: -10px; font-size: 26px; }
.robot-arm.pulling { transform: rotate(45deg) scale(1.1); }

.wheel-container{position:relative;width:320px;height:320px;display:flex;align-items:center;justify-content:center;}
.wheel-outer-ring{position:absolute;inset:-12px;border-radius:50%;border:5px dashed #315dff;box-shadow:0 0 40px #8d38ff;pointer-events:none;z-index:2;}
.pointer{position:absolute;top:-20px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:16px solid transparent;border-right:16px solid transparent;border-top:30px solid #ff3b3b;z-index:10;filter:drop-shadow(0 0 8px #ff3b3b);}
canvas{width:100%;height:100%;border-radius:50%;transition: transform 6s cubic-bezier(0.1, 0.9, 0.1, 1);}
.spin-btn{position:absolute;width:75px;height:75px;border-radius:50%;background:radial-gradient(circle,#9b37ff,#315dff);border:4px solid #fff;color:#fff;font-weight:900;font-size:15px;cursor:pointer;z-index:5;box-shadow:0 0 20px #9b37ff;}

.modal{display:none;position:fixed;inset:0;background:#03091bee;backdrop-filter:blur(12px);z-index:100;place-items:center;padding:20px;}
.modal-content{background:linear-gradient(145deg,#07132c,#0b1e47);border:2px solid #35eaa1;border-radius:20px;padding:25px;text-align:center;max-width:360px;width:100%;box-shadow:0 0 30px #35eaa166;}
</style>
</head>
<body>
<div style="text-align:center;margin-bottom:10px;">
  <h1 style="font-size:26px;margin:0;background:linear-gradient(110deg,#bc5bff,#315dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎡 عجلة الحظ السينمائية</h1>
  <p style="color:#a8b7d8;font-size:12px;margin:3px 0 0;">الروبوت نُوفا جاهز لإدارة العجلة لك!</p>
</div>

<div class="spin-stage">
  <div class="robot-head" id="robotAvatar">🤖</div>
  <div class="robot-arm" id="robotArm"></div>

  <div class="wheel-container">
    <div class="pointer"></div>
    <div class="wheel-outer-ring"></div>
    <canvas id="wheel" width="500" height="500"></canvas>
    <button class="spin-btn" id="spinBtn">أَدِرْ!</button>
  </div>
</div>

<a href="/" style="color:#8198ff;text-decoration:none;margin-top:15px;font-size:13px;font-weight:bold;">← العودة للمتجر الرئيسية</a>

<div class="modal" id="resultModal">
  <div class="modal-content">
    <div style="font-size:55px;" id="modalRobotEmoji">😃</div>
    <h2 id="prizeTitle" style="color:#35eaa1;margin:5px 0;">مبروك!</h2>
    <p id="prizeDesc" style="color:#a8b7d8;font-size:13px;line-height:1.6;"></p>
    <button onclick="location.href='/'" style="margin-top:15px;padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;width:100%;">التوجه للمتجر للشراء بالخصم 🔥</button>
  </div>
</div>

<script>
function playSpinSound() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = 'sawtooth';
  osc.frequency.setValueAtTime(150, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(600, ctx.currentTime + 3);
  osc.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 6);
  gain.gain.setValueAtTime(0.12, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 6);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 6);
}

function playWinSound() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.15, ctx.currentTime + idx * 0.12);
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + idx * 0.12 + 0.3);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime + idx * 0.12);
    osc.stop(ctx.currentTime + idx * 0.12 + 0.3);
  });
}

function speakRobot(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ar-SA';
    utterance.pitch = 1.2;
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

const canvas = document.getElementById('wheel');
const ctx = canvas.getContext('2d');
const spinBtn = document.getElementById('spinBtn');
const resultModal = document.getElementById('resultModal');
const robotAvatar = document.getElementById('robotAvatar');
const robotArm = document.getElementById('robotArm');

const items = [
  { label: '5 جنيه 💰', color: '#8d38ff', amount: 5, discount: 0 },
  { label: 'حظ أوفر 😅', color: '#1b2a4a', amount: 0, discount: 0 },
  { label: '10 جنيه 💳', color: '#315dff', amount: 10, discount: 0 },
  { label: 'خصم 20% 🏷️', color: '#00c853', amount: 0, discount: 20 },
  { label: '20 جنيه 🎁', color: '#ff9100', amount: 20, discount: 0 },
  { label: 'حظ أوفر 😅', color: '#263d70', amount: 0, discount: 0 }
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
    ctx.arc(radius, radius, radius - 10, angle, angle + arc);
    ctx.lineTo(radius, radius);
    ctx.fill();
    ctx.save();
    ctx.translate(radius, radius);
    ctx.rotate(angle + arc / 2);
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 20px Cairo";
    ctx.fillText(items[i].label, radius - 40, 8);
    ctx.restore();
  }
}
drawWheel();

let isSpinning = false;
spinBtn.addEventListener('click', () => {
  if (isSpinning) return;
  isSpinning = true;
  spinBtn.disabled = true;

  robotAvatar.textContent = '⚙️';
  robotArm.classList.add('pulling');
  playSpinSound();

  setTimeout(() => {
    robotArm.classList.remove('pulling');
  }, 800);

  fetch('/spin', {method: 'POST'}).then(res => res.json()).then(data => {
    if (data.status === 'error') {
      isSpinning = false;
      spinBtn.disabled = false;
      robotAvatar.textContent = '🤖';
      document.getElementById('prizeTitle').textContent = 'عذراً!';
      document.getElementById('prizeDesc').textContent = data.message;
      document.getElementById('modalRobotEmoji').textContent = '😅';
      resultModal.style.display = 'grid';
      return;
    }

    const selectedIndex = data.index;
    const prize = items[selectedIndex];
    const targetDegree = (360 - (selectedIndex * (360 / numItems)) - ((360 / numItems) / 2)) + (360 * 6);
    canvas.style.transform = `rotate(${targetDegree}deg)`;

    setTimeout(() => {
      isSpinning = false;
      const isWin = (prize.amount > 0 || prize.discount > 0);
      
      if (isWin) {
        robotAvatar.textContent = '😃';
        document.getElementById('modalRobotEmoji').textContent = '😃';
        document.getElementById('prizeTitle').textContent = '🎉 مبروك الفوز!';
        playWinSound();
        speakRobot(`مبروك! ${data.msg}`);
      } else {
        robotAvatar.textContent = '😅';
        document.getElementById('modalRobotEmoji').textContent = '😅';
        document.getElementById('prizeTitle').textContent = 'حظ أفضل المرة القادمة!';
        speakRobot("حظ أفضل في المرة القادمة!");
      }

      document.getElementById('prizeDesc').textContent = data.msg;
      resultModal.style.display = 'grid';
    }, 6000);
  });
});
</script>
</body>
</html>
"""

# ==================== لعبة الذاكرة الترفيهية ====================
GAME_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لعبة الذاكرة الترفيهية | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#1e0836 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;}
.memory-grid { display: grid; grid-template-columns: repeat(4, 75px); gap: 12px; background: #07132c; padding: 15px; border-radius: 20px; border: 2px solid #8d38ff; box-shadow: 0 0 30px #8d38ff44; margin-top:15px; }
.card-item { width: 75px; height: 90px; background: linear-gradient(145deg, #0f244a, #09132a); border: 2px solid #315dff; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 32px; cursor: pointer; user-select: none; transition: 0.3s; }
.card-item.flipped { background: linear-gradient(145deg, #276bff, #bc5bff); border-color: #35eaa1; }
.card-item.matched { background: linear-gradient(145deg, #059669, #10b981); border-color: #35eaa1; cursor: default; }
</style>
</head>
<body>
<div style="text-align:center;">
  <h1 style="margin:0;font-size:26px;color:#ec4899;">🎮 لعبة الذاكرة الترفيهية</h1>
  <p style="color:#a8b7d8;font-size:12px;">طابق الكروت للاستمتاع وقضاء وقت ممتع!</p>
</div>
<div class="memory-grid" id="memoryGrid"></div>
<a href="/" style="margin-top:20px;padding:10px 20px;background:#1e293b;color:white;text-decoration:none;border-radius:10px;font-weight:bold;font-size:12px;">← العودة للمتجر الرئيسية</a>

<script>
const emojis = ['🎮', '▶', '👑', '💳', '🪙', '🎁'];
let cards = [...emojis, ...emojis].sort(() => Math.random() - 0.5);
let flippedCards = [], matchedPairs = 0;
const grid = document.getElementById('memoryGrid');

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
        if (matchedPairs === emojis.length) alert('🏆 مبروك! أنهيت اللعبة بنجاح.');
      } else {
        setTimeout(() => {
          flippedCards[0].classList.remove('flipped');
          flippedCards[1].classList.remove('flipped');
          flippedCards[0].innerHTML = '❓';
          flippedCards[1].innerHTML = '❓';
          flippedCards = [];
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

# ==================== صفحة التسجيل والتوثيق المعتمدة ====================
REGISTER_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>إنشاء حساب موثوق | NOVA STORE</title>
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
    <p style="font-size:11px;color:#a8b7d8;margin:0;">اختر الطريقة المفضلة لديك لاستلام كود التحقق</p>
  </div>

  {% if step == 1 %}
  <form method="post">
    <input name="name" placeholder="الاسم الكامل" required>
    <input type="email" name="email" placeholder="البريد الإلكتروني الشخصي" required>
    <input type="password" name="password" placeholder="كلمة المرور (6 أحرف على الأقل)" required>
    
    <label style="font-size:11.5px;color:#cbd5e1;display:block;margin-top:8px;">طريقة استلام كود التحقق:</label>
    <select name="method" id="methodSelect" onchange="toggleField()" style="margin-bottom:10px;">
      <option value="email">📧 البريد الإلكتروني الرسمي ({{ support_email }})</option>
      <option value="telegram">🤖 عبر بوت التليجرام الرسمي</option>
    </select>

    <div id="telegramField" style="display:none;">
      <input name="telegram_id" placeholder="Telegram Chat ID (مثل: 123456789)">
    </div>

    <button type="submit">إرسال كود التحقق 🔐</button>
  </form>
  {% else %}
  <form method="post">
    <div style="background:#03091b;padding:12px;border-radius:10px;border:1px solid #35eaa1;margin-bottom:15px;text-align:center;">
      <span style="font-size:12px;color:#35eaa1;display:block;">تم إرسال كود التحقق بنجاح!</span>
      <p style="font-size:10.5px;color:#a8b7d8;margin:5px 0 0;">تفقد البريد الإلكتروني أو بوت التليجرام الخاص بك.</p>
    </div>
    <input name="code" placeholder="أدخل كود التحقق المكون من 6 أرقام" required style="text-align:center;font-size:16px;letter-spacing:2px;">
    <button type="submit">تأكيد الحساب والدخول 🚀</button>
  </form>
  {% endif %}

  {% if error %}<p style="color:#ff7777;font-size:12px;margin-top:10px;text-align:center;">{{ error }}</p>{% endif %}
  <a href="/login" style="color:#8198ff;display:block;margin-top:15px;text-align:center;font-size:12px;text-decoration:none;">لديك حساب بالفعل؟ تسجيل الدخول</a>
</div>

<script>
function toggleField() {
  const method = document.getElementById('methodSelect').value;
  const teleField = document.getElementById('telegramField');
  if (method === 'telegram') {
    teleField.style.display = 'block';
  } else {
    teleField.style.display = 'none';
  }
}
</script>
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
<title>لوحة التحكم الشاملة | NOVA STORE</title>
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
      <input name="link_url" placeholder="رابط توجيه خارجي (اختياري)">
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
      <input name="icon" placeholder="الأيقونة الاحتياطية (مثال: ▶)" required>
      <input name="category" placeholder="القسم" required>
      <button type="submit">إضافة المنتج</button>
    </form>
  </div>
  <a href="/" style="color:#8198ff;text-decoration:none;font-weight:bold;">← العودة للمتجر</a>
</div>
</body>
</html>
"""

# ==================== المسارات والروابط العامة واللوجو والأرشفة ====================

@app.route('/logo.svg')
@app.route('/favicon.ico')
def serve_logo():
    svg_logo = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#03091b"/>
      <stop offset="100%" stop-color="#081738"/>
    </linearGradient>
    <linearGradient id="nGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#bc5bff"/>
      <stop offset="50%" stop-color="#315dff"/>
      <stop offset="100%" stop-color="#35eaa1"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="120" fill="url(#bgGrad)"/>
  <path d="M 120 120 L 200 120 L 312 312 L 312 120 L 392 120 L 392 392 L 312 392 L 200 200 L 200 392 L 120 392 Z" fill="url(#nGrad)"/>
</svg>"""
    return Response(svg_logo, mimetype='image/svg+xml')

@app.route('/robots.txt')
def robots():
    robots_content = """User-agent: *
Allow: /

Sitemap: https://elite-store-ug21.onrender.com/sitemap.xml
"""
    return Response(robots_content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://elite-store-ug21.onrender.com/</loc>
    <lastmod>2026-10-20</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/game')
def game():
    return render_template_string(GAME_PAGE)

@app.route("/spin", methods=["GET", "POST"])
def spin():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    today_str = time.strftime("%Y-%m-%d")
    if request.method == "POST":
        if user["last_spin_date"] == today_str:
            return jsonify({"status": "error", "message": "لقد استخدمت محاولتك اليومية! عُد غداً لفرصة جديدة 🎁"})

        selectedIndex = secrets.randbelow(6)
        prizes = [
            {'label': '5 جنيه 💰', 'amount': 5, 'discount': 0},
            {'label': 'حظ أوفر 😅', 'amount': 0, 'discount': 0},
            {'label': '10 جنيه 💳', 'amount': 10, 'discount': 0},
            {'label': 'خصم 20% 🏷️', 'amount': 0, 'discount': 20},
            {'label': '20 جنيه 🎁', 'amount': 20, 'discount': 0},
            {'label': 'حظ أوفر 😅', 'amount': 0, 'discount': 0}
        ]
        prize = prizes[selectedIndex]

        with get_db() as db:
            if prize['amount'] > 0:
                db.execute("UPDATE users SET balance = balance + ?, last_spin_date = ?, spin_count = spin_count + 1 WHERE email = ?", (prize['amount'], today_str, email))
            else:
                db.execute("UPDATE users SET last_spin_date = ?, spin_count = spin_count + 1 WHERE email = ?", (today_str, email))

        if prize['discount'] > 0:
            session['active_discount'] = prize['discount']
            msg = f"فزت بـ ({prize['label']}) وتم خفض جميع أسعار المتجر فوراً بنسبة {prize['discount']}%!"
        elif prize['amount'] > 0:
            msg = f"فزت بـ ({prize['label']}) وأضيفت لمحفظتك بنجاح."
        else:
            msg = "حاول مجدداً غداً."

        return jsonify({"status": "success", "index": selectedIndex, "msg": msg})

    return render_template_string(SPIN_PAGE)

@app.route('/register', methods=["GET", "POST"])
def register():
    error = ""
    step = 1
    if request.method == "POST":
        if "code" not in request.form:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            method = request.form.get("method", "email")
            telegram_id = request.form.get("telegram_id", "").strip()

            if not name or "@" not in email or len(password) < 6:
                error = "يرجى ملء جميع البيانات بشكل صحيح (كلمة المرور 6 أحرف على الأقل)."
            else:
                with get_db() as db:
                    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                    if existing:
                        error = "هذا البريد مسجل مسبقاً."
                    else:
                        code = str(secrets.randbelow(900000) + 100000)
                        db.execute("INSERT OR REPLACE INTO email_codes (email, code, expires_at) VALUES (?, ?, ?)",
                                   (email, code, int(time.time()) + 300))
                        
                        if method == "telegram":
                            send_telegram_code(telegram_id, code)
                        else:
                            send_email_code(email, code)

                        session["temp_reg"] = {
                            "name": name, 
                            "email": email, 
                            "password": generate_password_hash(password), 
                            "telegram_id": telegram_id
                        }
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
                    db.execute("""
                        INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, ref_code, created_at)
                        VALUES (?, ?, ?, ?, 0.0, 1, ?, ?)
                    """, (temp["name"], temp["email"], temp["password"], temp["telegram_id"], my_ref, int(time.time())))
                    session["user_email"] = temp["email"]
                    session.pop("temp_reg", None)
                    return redirect(url_for("home"))
                else:
                    error = "كود التحقق غير صحيح."
                    step = 2
    return render_template_string(REGISTER_PAGE, error=error, step=step, support_email=SUPPORT_EMAIL)

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

@app.route("/account")
def account():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return render_template_string("""
    <div dir="rtl" style="font-family:'Cairo',sans-serif; background:#03091b; color:#fff; min-height:100vh; display:grid; place-items:center; padding:20px;">
      <div style="background:#07132c; border:1px solid #315dff; border-radius:20px; padding:30px; text-align:center; max-width:400px; width:100%;">
        <h2>👤 مرحبًا، {{ user["name"] }}</h2>
        <p style="color:#35eaa1;">الرصيد: {{ user["balance"] }} جـ</p>
        <a href="/" style="display:block; margin-top:15px; color:#8198ff; text-decoration:none;">← العودة للمتجر</a>
        <a href="/logout" style="display:block; margin-top:10px; color:#ff7777; text-decoration:none;">تسجيل الخروج</a>
      </div>
    </div>
    """, user=user)

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
    link_url = request.form.get("link_url", "").strip()

    image_url = ""
    file = request.files.get("image_file")
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_filename = f"post_{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        image_url = f"/static/uploads/{unique_filename}"

    if title and content:
        with get_db() as db:
            db.execute("""
                INSERT INTO posts (title, content, image_url, link_url, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, content, image_url, link_url, int(time.time())))

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
        unique_filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        image_url = f"/static/uploads/{unique_filename}"

    with get_db() as db:
        db.execute("""
            INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '#315dff', 'جديد')
        """, (name, description, price_val, price, code, icon, image_url, category))

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

    return render_template_string(
        PAGE, 
        products=products, 
        posts=posts,
        user=user, 
        is_admin=is_admin, 
        admin_telegram=ADMIN_TELEGRAM_USERNAME,
        telegram_channel=TELEGRAM_CHANNEL_LINK,
        support_email=SUPPORT_EMAIL
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
