import os
import json
import time
import secrets
import sqlite3
import math
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

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_TELEGRAM_USERNAME = "Mido_M9do"
TELEGRAM_BOT_USERNAME = "midoassistantAIbot"
TELEGRAM_CHANNEL_LINK = "https://t.me/Midomsn"
TELEGRAM_GROUP_CHAT_ID = os.environ.get("TELEGRAM_GROUP_CHAT_ID", "@MidoWorld")


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
                status_title TEXT DEFAULT 'المستخدم المميز',
                stars INTEGER DEFAULT 1250,
                friends_count INTEGER DEFAULT 12,
                total_orders INTEGER DEFAULT 8,
                ref_code TEXT UNIQUE,
                referred_by TEXT,
                last_spin_date TEXT,
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
                badge TEXT,
                rating REAL DEFAULT 4.8,
                reviews_count INTEGER DEFAULT 120
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

        db.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('flash_msg', 'عروض التطبيقات والألعاب المحدودة! خصومات خاصة تنتهي قريباً')")
        db.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('vodafone_number', '01000000000')")

        admin_user = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, avatar, status_title, stars, ref_code, created_at)
                VALUES (?, ?, ?, ?, 999999.0, 1, '👑', 'المطور الرئيسي', 5000, 'ADMINREF', ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "000000", int(time.time())))
        else:
            db.execute("""
                UPDATE users SET password_hash = ?, verified = 1 WHERE email = ?
            """, (generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL))

        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("VPN Pro", "تصفح الإنترنت بأمان وخصوصية كاملة", 240.00, "$8.00", "VPN-01", "🛡️", "", "خدمات الإنترنت", "#38bdf8", "الأكثر مبيعا", 4.8, 2400),
                ("ترجمة فورية", "ترجمة النصوص والمحادثات بدقة", 150.00, "$5.00", "TR-02", "🌐", "", "الأدوات الاحترافية", "#315dff", None, 4.7, 1800),
                ("ChatGPT Plus", "الوصول إلى GPT-4 بخيارات متقدمة", 360.00, "$12.00", "AI-03", "🤖", "", "الذكاء الاصطناعي", "#10b981", "مميز", 4.9, 3100),
                ("تطبيقات مايكروسوفت", "Word - Excel - PowerPoint", 300.00, "$10.00", "MS-04", "🪟", "", "الأدوات الاحترافية", "#f59e0b", None, 4.6, 980),
                ("YouTube Premium", "بدون إعلانات + تحميل خلفي", 300.00, "$10.00", "YT-05", "▶️", "", "الترفيه", "#ef4444", None, 4.8, 2800),
                ("PUBG Mobile", "شحن فوري بالآيدي والأكواد الرسمية", 150.00, "$10.00", "PUBG-06", "🎮", "", "الألعاب", "#f97316", "الأكثر مبيعا", 4.7, 5400),
                ("Fortnite", "شحنV-Bucks وأكواد الأبطال", 200.00, "$12.00", "FORT-07", "🎯", "", "الألعاب", "#8b5cf6", "ألعاب", 4.6, 2100),
                ("eFootball 2025", "شحن كوينز وفريقي المفضل", 180.00, "$9.00", "PES-08", "⚽", "", "الألعاب", "#3b82f6", "ألعاب", 4.5, 1900),
                ("Brawl Stars", "شحن جواهر وباقات حصرية", 220.00, "$11.00", "BRAWL-09", "⭐", "", "الألعاب", "#eab308", "ألعاب", 4.8, 3300),
                ("Minecraft", "كود اللعبة الأصلي وباقات السيرفرات", 250.00, "$14.00", "MINE-10", "🧱", "", "الألعاب", "#10b981", "ألعاب", 4.9, 4100),
                ("Roblox", "شحن روبوكس فوري وآمن", 210.00, "$10.00", "ROBLOX-11", "🎲", "", "الألعاب", "#64748b", "ألعاب", 4.6, 3800),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge, rating, reviews_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"🔐 كود التحقق الخاص بك في متجر NOVA STORE هو: {code}\nصالح لمدة 5 دقائق فقط."
    }
    try:
        requests.post(url, json=payload, timeout=5)
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


# ==================== القالب الرئيسي المطابق للصورة تماماً ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل لتطبيقات وألعاب</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff;--border:#1b315c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:'Cairo',sans-serif;min-height:100vh;}

/* شريط التنقل العلوي */
.topbar{min-height:78px;display:flex;align-items:center;gap:20px;padding:12px 2%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:100}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white}
.brand b{color:#754bff}
.brand-sub{font-size:10px;color:#8fa1c4;margin-top:-6px;display:block;}
.brand-mark{width:39px;height:39px;display:grid;place-items:center;font-size:33px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}

.search{height:44px;max-width:420px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:30px;padding:0 17px;background:#09132b}
.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:13px}

.header-actions{display:flex;align-items:center;gap:15px;margin-right:auto}
.lang-badge{display:flex;align-items:center;gap:6px;background:#0b1734;border:1px solid #263d70;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer;}
.notif-badge{position:relative;background:#0b1734;border:1px solid #263d70;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;cursor:pointer;}
.notif-badge span{position:absolute;top:-4px;right:-4px;background:#ef4444;color:white;font-size:9px;width:18px;height:18px;border-radius:50%;display:grid;place-items:center;font-weight:bold;}

.user-profile-badge {display: flex; align-items: center; gap: 10px; background: #0b1734; border: 1px solid #315dff; padding: 6px 14px; border-radius: 30px; text-decoration: none; box-shadow: 0 0 10px rgba(49,93,255,0.3);}
.user-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-weight: bold; color: white; border: 2px solid #35eaa1; overflow:hidden;}
.admin-badge { background: #570f0f; color: #ff7777; border: 1px solid #ff5555; padding: 6px 14px; border-radius: 12px; font-weight: bold; text-decoration:none;}

/* هيكل الصفحة الثلاثي الأعمدة (قائمة جانبية + المحتوى الرئيسي + اللوحة اليمنى) */
.layout{display:grid;grid-template-columns:260px minmax(0,1fr) 280px;gap:20px;padding:20px 2%;}
@media (max-width:1200px){.layout{grid-template-columns:240px minmax(0,1fr);}.right-sidebar{display:none;}}
@media (max-width:850px){.layout{grid-template-columns:1fr;}.left-sidebar{display:none;}}

/* القائمة الجانبية اليسرى */
.left-sidebar {background:#07132c;border:1px solid #1b3159;border-radius:18px;padding:15px;height:fit-content;position:sticky;top:95px;}
.sidebar-link {display:flex;align-items:center;gap:12px;padding:11px 14px;color:#c4cde3;text-decoration:none;border-radius:12px;font-size:12.5px;font-weight:600;margin-bottom:4px;transition:0.2s;}
.sidebar-link:hover, .sidebar-link.active {background:linear-gradient(110deg,#9b37ff,#315dff);color:white;}
.sidebar-divider {height:1px;background:#18284a;margin:12px 0;}

.vip-box {background:linear-gradient(145deg,#201035,#07132c);border:1px solid #9b37ff;border-radius:16px;padding:15px;text-align:center;margin-top:15px;}

/* المحتوى الرئيسي */
.main-content {min-width:0;}
.hero-banner {background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 60%),linear-gradient(120deg,#06102b,#080c2c 60%,#13093b);border:1px solid #263f77;border-radius:22px;padding:25px;display:grid;grid-template-columns:1.2fr 1fr;align-items:center;position:relative;overflow:hidden;margin-bottom:20px;}
.hero-banner h1{font-size:clamp(18px,1.8vw,26px);line-height:1.6;margin:0 0 10px;font-weight:800}
.hero-banner p{color:#c4cce2;font-size:11.5px;line-height:1.7;margin:0 0 15px;}
.hero-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;text-decoration:none;font-weight:bold;}
.trust-badges{display:flex;gap:15px;margin-top:15px;font-size:10px;color:#cbd5e1;}

/* التصنيفات الملونة الأفقية */
.cat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(115px,1fr));gap:10px;margin-bottom:25px;}
.cat-card{background:linear-gradient(145deg,#081735,#050d22);border:1px solid #1b3159;border-radius:16px;padding:14px 8px;text-align:center;cursor:pointer;transition:0.2s;}
.cat-card:hover{border-color:#315dff;transform:translateY(-2px);}
.cat-icon{font-size:26px;margin-bottom:6px;display:block;}
.cat-name{font-size:11px;font-weight:bold;color:#f4f7ff;}
.cat-desc{font-size:9px;color:#8fa1c4;margin-top:2px;}

/* شبكة المنتجات والألعاب */
.section-title{display:flex;align-items:center;justify-content:space-between;margin:20px 0 12px;}
.section-title h2{font-size:17px;margin:0;display:flex;align-items:center;gap:8px;}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px;}
.product-card{background:linear-gradient(150deg,#08152e,#050c1e);border:1px solid #1b3159;border-radius:16px;padding:12px;position:relative;transition:0.2s;}
.product-card:hover{border-color:#35eaa1;transform:translateY(-3px);}
.product-visual{height:140px;background:#03091b;border-radius:12px;display:grid;place-items:center;font-size:40px;margin-bottom:10px;position:relative;overflow:hidden;}
.badge-tag{position:absolute;top:8px;right:8px;background:#ef4444;color:white;font-size:9px;padding:2px 8px;border-radius:6px;font-weight:bold;}
.badge-tag.memo{background:#315dff;}
.badge-tag.green{background:#10b981;}

.action-btn{width:100%;padding:8px;background:linear-gradient(100deg,#933aff,#315dff);border:0;border-radius:8px;font-size:11px;font-weight:bold;color:white;cursor:pointer;margin-top:8px;}

/* اللوحة الجانبية اليمنى (الملف الشخصي والخدمات) */
.right-sidebar {display:flex;flex-direction:column;gap:18px;}
.profile-card {background:linear-gradient(145deg,#07142c,#0a1b3f);border:1px solid #315dff;border-radius:18px;padding:18px;text-align:center;}
.profile-avatar-large {width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,#9b37ff,#315dff);display:grid;place-items:center;font-size:32px;margin:0 auto 10px;border:3px solid #35eaa1;box-shadow:0 0 15px rgba(53,234,161,0.4);}
.stats-row {display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:12px;}
.stat-box {background:#03091b;border:1px solid #1c325c;padding:8px;border-radius:10px;font-size:11px;}

.service-grid {display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:10px;}
.service-btn {background:#091530;border:1px solid #1c325c;padding:10px;border-radius:12px;text-align:center;cursor:pointer;transition:0.2s;text-decoration:none;color:#fff;font-size:11px;display:flex;flex-direction:column;align-items:center;gap:6px;}
.service-btn:hover{border-color:#35eaa1;background:#0d2242;}

/* نافذة الدفع والشراء */
.checkout-modal{display:none;position:fixed;inset:0;background:rgba(3,9,27,0.88);backdrop-filter:blur(8px);z-index:200;place-items:center;padding:20px;}
.checkout-box{background:linear-gradient(145deg,#07132c,#0a1a3f);border:1px solid #315dff;border-radius:18px;padding:25px;width:100%;max-width:420px;text-align:center;}
.payment-tabs{display:flex;gap:10px;margin:15px 0;}
.pay-tab{flex:1;padding:12px;background:#03091b;border:1px solid #263d70;border-radius:10px;color:#a8b7d8;font-size:12px;font-weight:bold;cursor:pointer;}
.pay-tab.active{border-color:#35eaa1;background:#0d2340;color:#35eaa1;}

/* تذييل الصفحة */
footer{border-top:1px solid #192b4e;padding:30px 4%;margin-top:40px;background:#030714;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:20px;font-size:11px;color:#aab9d8;}
@media (max-width:850px){footer{grid-template-columns:1fr;}}
footer h4{color:#fff;margin:0 0 10px;font-size:13px;}
footer a{display:block;color:#aab8d0;text-decoration:none;margin:6px 0;}
.dev-banner {background:linear-gradient(135deg,#150930,#060d24);border:1px solid #9b37ff;border-radius:18px;padding:20px;text-align:center;margin:30px 2%;box-shadow:0 0 25px rgba(155,55,255,0.25);}
</style>
</head>
<body>

<!-- الشريط العلوي -->
<header class="topbar">
  <a class="brand" href="/">
    <span class="brand-mark">N</span>
    <div>
      <span>NOVA <b>STORE</b></span>
      <span class="brand-sub">More Apps · More Fun · More Freedom</span>
    </div>
  </a>
  <label class="search"><span>⌕</span><input id="searchInput" type="search" placeholder="ابحث عن أي تطبيق أو خدمة..." onkeyup="filterProducts()"></label>
  
  <div class="header-actions">
    <div class="lang-badge"><span>🌐 AR</span></div>
    <div class="notif-badge"><span>🔔</span><span>3</span></div>
    {% if is_admin %}
      <a href="/admin" class="admin-badge">⚙️ لوحة المطور</a>
    {% endif %}
    {% if user %}
      <a href="/account" class="user-profile-badge">
        <div class="user-avatar">{{ user["avatar"] }}</div>
        <div>
          <span style="font-size:11px;font-weight:bold;display:block;">{{ user["name"] }}</span>
          <span style="font-size:9px;color:#35eaa1;">{{ user["balance"] }} جـ</span>
        </div>
      </a>
    {% else %}
      <a href="/login" style="color:#d8e2ff;text-decoration:none;font-size:12px;">تسجيل الدخول</a>
      <a href="/register" style="padding:8px 14px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;">إنشاء حساب</a>
    {% endif %}
  </div>
</header>

<div class="layout">
  <!-- القائمة الجانبية اليسرى -->
  <aside class="left-sidebar">
    <a href="/" class="sidebar-link active"><span>🏠</span> الرئيسية</a>
    <div class="sidebar-divider"></div>
    <a href="#products" class="sidebar-link" onclick="filterCat('الكل')"><span>📦</span> جميع التطبيقات</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('الألعاب')"><span>🎮</span> الألعاب</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('الذكاء الاصطناعي')"><span>🤖</span> الذكاء الاصطناعي</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('الأدوات الاحترافية')"><span>🛠️</span> أدوات احترافية</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('خدمات الإنترنت')"><span>🌐</span> خدمات الإنترنت</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('التواصل الاجتماعي')"><span>💬</span> التواصل الاجتماعي</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('الأدوات')"><span>🎨</span> تعديل الصور والفيديو</a>
    <a href="#products" class="sidebar-link" onclick="filterCat('الدفع')"><span>💳</span> المال والدفع</a>
    <a href="/game" class="sidebar-link"><span>🎯</span> الترفيه والألعاب</a>
    <div class="sidebar-divider"></div>
    <a href="/account" class="sidebar-link"><span>👑</span> المميزين</a>
    <a href="/account" class="sidebar-link"><span>❤️</span> المفضلة</a>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="sidebar-link"><span>🎧</span> الدعم الفني</a>
    <a href="/account" class="sidebar-link"><span>⚙️</span> الإعدادات</a>

    <div class="vip-box">
      <div style="font-size:28px;">👑</div>
      <h4 style="margin:5px 0;color:#f59e0b;font-size:12px;">احصل على عضوية VIP</h4>
      <p style="font-size:10px;color:#a8b7d8;margin:0 0 10px;">مزايا أكثر .. أسعار أفضل!</p>
      <a href="https://t.me/{{ admin_telegram }}?text=أريد%20الاشتراك%20في%20عضوية%20VIP" target="_blank" style="display:block;padding:8px;background:linear-gradient(110deg,#f59e0b,#d97706);color:#fff;border-radius:8px;text-decoration:none;font-weight:bold;font-size:11px;">تفعيل الآن</a>
    </div>
  </aside>

  <!-- المحتوى الرئيسي للمتجر -->
  <main class="main-content">
    <div class="hero-banner">
      <div>
        <span style="background:rgba(53,234,161,0.15);color:#35eaa1;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:bold;border:1px solid #35eaa133;">أفضل التطبيقات ✦</span>
        <h1>كل ما تحتاجه في مكان واحد!<br>تطبيقات، ألعاب، أدوات، وخدمات مميزة</h1>
        <p>بطاقات رقمية آمنة وسريعة. شحن الألعاب، أكواد المتاجر العالمية، والمزيد من المتجر الرقمي المميز.</p>
        <a class="hero-btn" href="#products">تصفح الآن ←</a>
        <div class="trust-badges">
          <span>🛡️ دفع أمن 100%</span>
          <span>⚡ تسليم سريع</span>
          <span>🎧 دعم فني 24/7</span>
        </div>
      </div>
      <div style="display:grid;place-items:center;font-size:65px;">
        🤖✨
      </div>
    </div>

    <!-- التصنيفات الملونة الأفقية -->
    <div class="cat-grid">
      <div class="cat-card" onclick="filterCat('بطاقات الهدايا')">
        <span class="cat-icon" style="color:#bc5bff;">🎁</span>
        <b class="cat-name">بطاقات الهدايا</b>
        <div class="cat-desc">شحن الألعاب والخدمات</div>
      </div>
      <div class="cat-card" onclick="filterCat('الألعاب')">
        <span class="cat-icon" style="color:#10b981;">🎮</span>
        <b class="cat-name">الألعاب</b>
        <div class="cat-desc">أحدث الألعاب والعمليات</div>
      </div>
      <div class="cat-card" onclick="filterCat('الذكاء الاصطناعي')">
        <span class="cat-icon" style="color:#38bdf8;">🤖</span>
        <b class="cat-name">الذكاء الاصطناعي</b>
        <div class="cat-desc">أدوات مميزة وذكية</div>
      </div>
      <div class="cat-card" onclick="filterCat('الأدوات الاحترافية')">
        <span class="cat-icon" style="color:#f59e0b;">🛠️</span>
        <b class="cat-name">الأدوات الاحترافية</b>
        <div class="cat-desc">أدوات قوية ومفيدة</div>
      </div>
      <div class="cat-card" onclick="filterCat('خدمات الإنترنت')">
        <span class="cat-icon" style="color:#315dff;">🌐</span>
        <b class="cat-name">خدمات الإنترنت</b>
        <div class="cat-desc">VPN - متصفحات - أدوات</div>
      </div>
      <div class="cat-card" onclick="filterCat('التواصل الاجتماعي')">
        <span class="cat-icon" style="color:#a855f7;">💬</span>
        <b class="cat-name">التواصل الاجتماعي</b>
        <div class="cat-desc">تطوير وحماية الحسابات</div>
      </div>
      <div class="cat-card" onclick="filterCat('الترفيه')">
        <span class="cat-icon" style="color:#ef4444;">▶️</span>
        <b class="cat-name">الترفيه</b>
        <div class="cat-desc">أفلام وموسيقى</div>
      </div>
      <div class="cat-card" onclick="filterCat('الكل')">
        <span class="cat-icon" style="color:#64748b;">🎛️</span>
        <b class="cat-name">المزيد</b>
        <div class="cat-desc">المزيد من الخدمات</div>
      </div>
    </div>

    <!-- شبكة المنتجات -->
    <div class="section-title" id="products">
      <h2><span>🔥</span> أحدث المنتجات والتطبيقات</h2>
    </div>

    <div class="product-grid" id="productGrid"></div>

    <!-- قسم تقييمات العملاء -->
    <div style="margin-top:35px;" id="reviews">
      <div class="section-title">
        <h2><span>⭐️</span> آراء وتقييمات العملاء</h2>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:15px;">
        {% for rev in reviews %}
        <div style="background:#071635;border:1px solid #1e3a6e;padding:12px;border-radius:12px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <b style="font-size:12px;color:#35eaa1;">{{ rev['user_name'] }}</b>
            <span style="color:#facc15;font-size:11px;">{{ '⭐' * rev['rating'] }}</span>
          </div>
          <p style="font-size:11px;color:#cbd5e1;margin:0;">{{ rev['comment'] }}</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </main>

  <!-- اللوحة الجانبية اليمنى (الملف الشخصي والخدمات) -->
  <aside class="right-sidebar">
    <div class="profile-card">
      <div class="profile-avatar-large">{% if user %}{{ user["avatar"] }}{% else %}🤖{% endif %}</div>
      <h3 style="margin:0 0 4px;font-size:14px;color:#fff;">{% if user %}{{ user["name"] }}{% else %}مرحباً بك{% endif %}</h3>
      <span style="font-size:10px;color:#35eaa1;">{{ user["status_title"] if user else "المستخدم المميز" }} 👑</span>
      
      <div class="stats-row">
        <div class="stat-box">
          <span style="color:#facc15;font-size:12px;">⭐ {% if user %}{{ user["stars"] }}{% else %}1,250{% endif %}</span>
          <span style="display:block;font-size:9px;color:#a8b7d8;">نجومك</span>
        </div>
        <div class="stat-box">
          <span style="color:#38bdf8;font-size:12px;">👥 {% if user %}{{ user["friends_count"] }}{% else %}12{% endif %}</span>
          <span style="display:block;font-size:9px;color:#a8b7d8;">الأصدقاء</span>
        </div>
      </div>
    </div>

    <!-- زر الانضمام للقناة -->
    <a href="{{ telegram_channel }}" target="_blank" style="background:linear-gradient(135deg,#315dff,#8d38ff);border-radius:16px;padding:15px;color:#fff;text-decoration:none;display:block;text-align:center;box-shadow:0 4px 15px rgba(49,93,255,0.3);">
      <div style="font-size:24px;margin-bottom:5px;">📢</div>
      <b style="font-size:13px;display:block;">انضم إلى قناتنا</b>
      <span style="font-size:10px;color:#e2e8f0;">للحصول على أحدث العروض</span>
    </a>

    <!-- قسم خدمات سريعة -->
    <div style="background:#07132c;border:1px solid #1b3159;border-radius:18px;padding:15px;">
      <h4 style="margin:0 0 10px;font-size:12px;color:#fff;">⚡ خدمات سريعة</h4>
      <div class="service-grid">
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20تفعيل%20VPN" target="_blank" class="service-btn"><span>🛡️</span> تفعيل VPN</a>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شحن%20رصيد" target="_blank" class="service-btn"><span>💳</span> شحن الرصيد</a>
        <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="service-btn"><span>💬</span> تواصل معنا</a>
        <a href="/account" class="service-btn"><span>❤️</span> المفضلة</a>
      </div>
    </div>
  </aside>
</div>

<!-- نافذة إتمام الشراء والدفع -->
<div class="checkout-modal" id="checkoutModal">
  <div class="checkout-box">
    <h3 id="modalProductName" style="margin-top:0;color:#fff;">اسم المنتج</h3>
    <p style="font-size:12px;color:#a8b7d8;margin:5px 0 15px;" id="modalProductDesc">وصف المنتج</p>
    
    <div style="background:#03091b;padding:12px;border-radius:12px;border:1px solid #263d70;margin-bottom:15px;text-align:right;">
      <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px;">
        <span>السعر الأساسي:</span>
        <b id="basePriceText" style="color:#fff;">0 جـ</b>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px;display:none;" id="discountRow">
        <span style="color:#35eaa1;">قيمة الخصم:</span>
        <b id="discountText" style="color:#35eaa1;">-0 جـ</b>
      </div>
      <hr style="border-color:#1b315c;margin:8px 0;">
      <div style="display:flex;justify-content:space-between;font-size:14px;">
        <span>السعر الإجمالي النهائي:</span>
        <strong id="finalPriceText" style="color:#35eaa1;">0 جـ</strong>
      </div>
    </div>

    <!-- كود الخصم -->
    <div style="display:flex;gap:8px;margin-bottom:15px;">
      <input type="text" id="promoInput" placeholder="أدخل كود الخصم (مثال: MIDO2026)" style="flex:1;padding:10px;background:#03091b;border:1px solid #315dff;border-radius:8px;color:#fff;font-size:11px;">
      <button onclick="applyPromoCode()" style="padding:10px 16px;background:linear-gradient(110deg,#9b37ff,#315dff);color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;font-size:11px;">تطبيق الكود 🏷️</button>
    </div>
    <p id="promoMsg" style="font-size:11px;margin:0 0 15px;text-align:right;"></p>

    <p style="font-size:12px;text-align:right;margin:0 0 5px;color:#fff;font-weight:bold;">اختر طريقة الدفع:</p>
    <div class="payment-tabs">
      <div class="pay-tab active" id="tabVodafone" onclick="selectPayment('vodafone')">📱 فودافون كاش</div>
      <div class="pay-tab" id="tabCard" onclick="selectPayment('card')">💳 بطاقة الدفع</div>
    </div>

    <div id="vodafoneDetails" style="background:#091632;padding:12px;border-radius:10px;border:1px solid #e11d48;margin-bottom:15px;text-align:right;">
      <span style="font-size:11px;color:#ff7777;display:block;margin-bottom:4px;">تحويل المبلغ إلى رقم فودافون كاش التالي:</span>
      <b style="font-size:14px;color:#fff;letter-spacing:1px;">01000000000</b>
    </div>

    <div id="cardDetails" style="display:none;background:#091632;padding:12px;border-radius:10px;border:1px solid #315dff;margin-bottom:15px;text-align:right;">
      <input type="text" placeholder="رقم البطاقة (16 رقم)" style="width:100%;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;margin-bottom:6px;">
      <div style="display:flex;gap:6px;">
        <input type="text" placeholder="MM/YY" style="width:50%;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;">
        <input type="text" placeholder="CVV" style="width:50%;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;">
      </div>
    </div>

    <div style="display:flex;gap:10px;">
      <a id="confirmBuyBtn" href="#" target="_blank" style="flex:1;padding:12px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;border-radius:10px;font-weight:bold;text-decoration:none;font-size:12px;text-align:center;">تأكيد ودفع الطلب 🚀</a>
      <button onclick="closeCheckout()" style="padding:12px 16px;background:#1b2a4a;color:#fff;border:0;border-radius:10px;cursor:pointer;font-size:12px;">إلغاء</button>
    </div>
  </div>
</div>

<!-- زر المطور الشيك في الأسفل -->
<div class="dev-banner">
  <div style="font-size:30px;">👑</div>
  <h3 style="margin:5px 0;color:#38bdf8;font-size:17px;">المطور والمسؤول عن المنصة (Mido)</h3>
  <p style="margin:0 auto 12px;color:#aab9d8;font-size:11.5px;max-width:450px;">تم تصميم وتطوير هذا المتجر المتكامل خصيصاً لتقديم أفضل تجربة شحن ألعاب وأمان رقمي.</p>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank" style="display:inline-flex;align-items:center;gap:8px;padding:10px 25px;background:linear-gradient(110deg,#9b37ff,#315dff);color:#fff;border-radius:30px;font-weight:bold;text-decoration:none;font-size:12px;box-shadow:0 4px 15px rgba(155,55,255,0.4);">
    <span>💬</span> تواصل مباشرة مع المطور
  </a>
</div>

<!-- تذييل الصفحة (Footer) -->
<footer>
  <div>
    <a class="brand" href="/" style="margin-bottom:10px;"><span class="brand-mark" style="width:28px;height:28px;font-size:20px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.7;margin:0 0 12px;">المتجر الرقمي الأول لبطاقات الدفع وأكواد الألعاب والتطبيقات بأمان وسرعة.</p>
    <div style="display:flex;gap:10px;font-size:16px;">
      <span>💳 Visa</span>
      <span>💳 MasterCard</span>
      <span>🟡 Fawry</span>
      <span>🅿️ PayPal</span>
    </div>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="/game">🎮 المنطقة الترفيهية</a>
    <a href="/spin">🎡 عجلة الحظ</a>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank">الدعم الفني</a>
  </div>
  <div>
    <h4>الدعم والمساعدة</h4>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank">مركز المساعدة</a>
    <a href="#">سياسة الخصوصية</a>
    <a href="#">شروط الاستخدام</a>
  </div>
  <div>
    <h4>تابعنا</h4>
    <div style="display:flex;gap:12px;font-size:18px;margin-top:10px;">
      <a href="{{ telegram_channel }}" target="_blank">📢</a>
      <a href="https://t.me/{{ admin_telegram }}" target="_blank">💬</a>
    </div>
    <p style="margin-top:15px;font-size:10px;color:#64748b;">© 2026 NOVA STORE. جميع الحقوق محفوظة.</p>
  </div>
</footer>

<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');
let currentProduct = null;
let currentPriceVal = 0;
let discountPercent = 0;

function renderProducts(items) {
  productGrid.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let visualHtml = p.image_url ? `<img src="${p.image_url}" class="product-img">` : `<span style="color:${p.color};">${p.icon}</span>`;
    let badgeHtml = p.badge ? `<span class="badge-tag">${p.badge}</span>` : '';
    
    card.innerHTML = `
      ${badgeHtml}
      <div class="product-visual">${visualHtml}</div>
      <h3 style="color:#fff;font-size:13px;margin:4px 0;">${p.name}</h3>
      <p style="font-size:10px;color:#8fa1c4;margin:0 0 8px;">${p.description}</p>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
        <div>
          <span style="font-size:13px;font-weight:bold;color:#35eaa1;">${p.price}</span>
          <span style="font-size:9px;color:#facc15;margin-right:5px;">⭐ ${p.rating}</span>
        </div>
        <button onclick="openCheckout(${p.price_val}, '${p.name}', '${p.description}')" class="action-btn" style="width:auto;padding:6px 12px;">شراء 💳</button>
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

function openCheckout(priceVal, name, desc) {
  currentProduct = name;
  currentPriceVal = priceVal;
  discountPercent = 0;
  document.getElementById('modalProductName').textContent = name;
  document.getElementById('modalProductDesc').textContent = desc;
  document.getElementById('basePriceText').textContent = priceVal + ' جـ';
  document.getElementById('discountRow').style.display = 'none';
  document.getElementById('finalPriceText').textContent = priceVal + ' جـ';
  document.getElementById('promoInput').value = '';
  document.getElementById('promoMsg').textContent = '';
  updateConfirmLink();
  document.getElementById('checkoutModal').style.display = 'grid';
}

function closeCheckout() {
  document.getElementById('checkoutModal').style.display = 'none';
}

function applyPromoCode() {
  const code = document.getElementById('promoInput').value.trim().toUpperCase();
  const msg = document.getElementById('promoMsg');
  if (code === 'MIDO2026') {
    discountPercent = 10;
    const discountVal = (currentPriceVal * discountPercent) / 100;
    const finalVal = currentPriceVal - discountVal;
    document.getElementById('discountRow').style.display = 'flex';
    document.getElementById('discountText').textContent = '-' + discountVal.toFixed(1) + ' جـ (10%)';
    document.getElementById('finalPriceText').textContent = finalVal.toFixed(1) + ' جـ';
    msg.style.color = '#35eaa1';
    msg.textContent = '✅ تم تطبيق كود الخصم (10%) بنجاح!';
  } else {
    discountPercent = 0;
    document.getElementById('discountRow').style.display = 'none';
    document.getElementById('finalPriceText').textContent = currentPriceVal + ' جـ';
    msg.style.color = '#ff7777';
    msg.textContent = '❌ كود الخصم غير صحيح.';
  }
  updateConfirmLink();
}

function selectPayment(type) {
  if (type === 'vodafone') {
    document.getElementById('tabVodafone').classList.add('active');
    document.getElementById('tabCard').classList.remove('active');
    document.getElementById('vodafoneDetails').style.display = 'block';
    document.getElementById('cardDetails').style.display = 'none';
  } else {
    document.getElementById('tabCard').classList.add('active');
    document.getElementById('tabVodafone').classList.remove('active');
    document.getElementById('cardDetails').style.display = 'block';
    document.getElementById('vodafoneDetails').style.display = 'none';
  }
}

function updateConfirmLink() {
  const finalPrice = document.getElementById('finalPriceText').textContent;
  const text = `أريد شراء المنتج: ${currentProduct} | السعر النهائي: ${finalPrice}`;
  document.getElementById('confirmBuyBtn').href = `https://t.me/{{ admin_telegram }}?text=${encodeURIComponent(text)}`;
}

renderProducts(PRODUCTS);
</script>
</body>
</html>
"""

# ==================== المسارات والروابط المطلوبة ====================

@app.route('/game')
def game():
    return "<h1>منطقة الألعاب الترفيهية قيد التشغيل</h1><a href='/'>العودة للرئيسية</a>"

@app.route('/account')
def account():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return f"<h1>حساب المستخدم: {user['name']}</h1><p>الرصيد: {user['balance']} جـ</p><a href='/'>العودة</a>"

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
                        send_telegram_code(TELEGRAM_GROUP_CHAT_ID, code)
                        auto_code = code
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
    
    register_html = f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إنشاء حساب</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2>إنشاء حساب جديد</h2>
    <form method="post">
    {"<input name='name' placeholder='الاسم الكامل' required><input type='email' name='email' placeholder='البريد الإلكتروني' required><input type='password' name='password' placeholder='كلمة المرور' required>" if step == 1 else f"<p style='color:#35eaa1;'>تم إرسال كود التحقق لجروب التليجرام. الكود الاحتياطي: <b>{auto_code}</b></p><input name='code' placeholder='أدخل كود التحقق' required>"}
    <button type="submit">{"إرسال الكود" if step == 1 else "تأكيد الحساب"}</button>
    </form>
    <p style="color:#ff7777;font-size:12px;">{error}</p>
    <a href="/login" style="color:#8198ff;display:block;margin-top:10px;text-align:center;font-size:12px;text-decoration:none;">تسجيل الدخول</a>
    </div></body></html>
    """
    return register_html

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
    
    login_html = f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>تسجيل الدخول</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2>تسجيل الدخول</h2>
    <form method="post">
    <input type="email" name="email" placeholder="البريد الإلكتروني" required>
    <input type="password" name="password" placeholder="كلمة المرور" required>
    <button type="submit">دخول</button>
    </form>
    <p style="color:#ff7777;font-size:12px;">{error}</p>
    <a href="/register" style="color:#8198ff;display:block;margin-top:10px;text-align:center;font-size:12px;text-decoration:none;">إنشاء حساب جديد</a>
    </div></body></html>
    """
    return login_html

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
    reviews = get_reviews()

    return render_template_string(
        PAGE, 
        products=products, 
        reviews=reviews,
        user=user, 
        is_admin=is_admin, 
        admin_telegram=ADMIN_TELEGRAM_USERNAME, 
        telegram_channel=TELEGRAM_CHANNEL_LINK
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
