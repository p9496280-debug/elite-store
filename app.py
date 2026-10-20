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

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "moh99zzhvni893fj7@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "mohammedaaa222")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")
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


def get_promo_codes():
    with get_db() as db:
        rows = db.execute("SELECT * FROM promo_codes ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def get_setting(key, default=""):
    with get_db() as db:
        row = db.execute("SELECT value FROM store_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


# ==================== الصفحة الرئيسية للمتجر ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل لبطاقات الألعاب والدفع</title>
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
.nav a { color: #c4cde3; text-decoration: none; padding: 8px 16px; border-radius: 12px; font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); white-space: nowrap; }
.nav a.active { background: linear-gradient(110deg, #9b37ff, #315dff); color: #ffffff; border-color: transparent; }

.layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:22px;padding:22px 4%}
@media (max-width:850px){ .layout{grid-template-columns:1fr;} }
.main-column{min-width:0}

.hero{min-height:280px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b);padding:25px;align-items:center;}
.hero h1{font-size:clamp(20px,2vw,28px);line-height:1.6;margin:0 0 10px;font-weight:800}
.hero p{color:#c4cce2;font-size:12px;line-height:1.8;margin:0 0 15px}
.hero-btn{display:inline-flex;align-items:center;gap:10px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;cursor:pointer;}

.categories{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin:20px 0}
.category{border:1px solid #172d53;border-radius:12px;background:linear-gradient(150deg,#07152e,#050d20);padding:14px 8px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;cursor:pointer;}
.category span{font-size:22px;color:#65baff}
.category b{font-size:11px}

.section-heading{display:flex;align-items:center;justify-content:space-between;margin:25px 0 12px}
.section-heading h2{font-size:18px;margin:0;display:flex;align-items:center;gap:8px}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:14px;padding:12px;position:relative;}
.product-visual{height:160px;border-radius:10px;background:radial-gradient(circle at 50% 20%,#1b3159,transparent 70%),#07142c;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;margin-bottom:10px;overflow:hidden;}
.product-img{width:100%;height:100%;object-fit:contain;border-radius:10px;}
.price{font-size:13.5px;font-weight:800;color:#35eaa1}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;cursor:pointer}

.side-card{border:1px solid #243e75;border-radius:18px;padding:16px;background:linear-gradient(155deg,#081735,#060d22);margin-bottom:18px;}
.side-card h4{margin:0 0 10px;font-size:13px;color:#fff;display:flex;align-items:center;gap:8px;}
.wallet-box{background:linear-gradient(135deg,#0e234e,#180b3d);border:1px solid #35eaa166;border-radius:14px;padding:14px;text-align:center;}

.reviews-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:15px;}
.review-card {background:#071635;border:1px solid #1e3a6e;padding:12px;border-radius:12px;}

/* تصميم نافذة الدفع واختيار الطرق الشيك */
.checkout-modal{display:none;position:fixed;inset:0;background:rgba(3,9,27,0.85);backdrop-filter:blur(8px);z-index:200;place-items:center;padding:20px;}
.checkout-box{background:linear-gradient(145deg,#07132c,#0a1a3f);border:1px solid #315dff;border-radius:18px;padding:25px;width:100%;max-width:420px;text-align:center;max-height:90vh;overflow-y:auto;}
.payment-tabs{display:flex;gap:10px;margin:15px 0;}
.pay-tab{flex:1;padding:12px;background:#03091b;border:1px solid #263d70;border-radius:10px;color:#a8b7d8;font-size:12px;font-weight:bold;cursor:pointer;transition:0.2s;}
.pay-tab.active{border-color:#35eaa1;background:#0d2340;color:#35eaa1;box-shadow:0 0 10px rgba(53,234,161,0.3);}

/* زر المطور الشيك جداً في الأسفل */
.developer-footer-banner {
  background: linear-gradient(135deg, #120c2e, #060e24);
  border: 1px solid #9b37ff;
  border-radius: 20px;
  padding: 25px;
  text-align: center;
  margin-top: 50px;
  box-shadow: 0 0 25px rgba(155, 55, 255, 0.25);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.dev-btn-stylish {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 30px;
  background: linear-gradient(110deg, #9b37ff, #315dff);
  color: white;
  font-weight: 800;
  border-radius: 35px;
  text-decoration: none;
  font-size: 14px;
  box-shadow: 0 4px 20px rgba(155, 55, 255, 0.4);
  transition: all 0.3s ease;
}
.dev-btn-stylish:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 25px rgba(49, 93, 255, 0.6);
}

footer{border-top:1px solid #192b4e;padding:30px 4%;margin-top:30px;background:#030714;text-align:center;color:#aab9d8;font-size:11px;}
</style>
</head>
<body>

<header class="topbar">
  <a class="brand" href="/"><span class="brand-mark">N</span><span>NOVA <b>STORE</b></span></a>
  <label class="search"><span>⌕</span><input id="searchInput" type="search" placeholder="ابحث عن أي منتج..." onkeyup="filterProducts()"></label>
  <div class="header-actions">
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

<nav class="nav">
  <a href="/" class="active"><span>🏠</span> الرئيسية</a>
  <a href="/game" style="background:linear-gradient(135deg,#ec4899,#8b5cf6);color:#fff;"><span>🎮</span> الألعاب الترفيهية</a>
  <a href="/spin" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;"><span>🎡</span> عجلة الحظ</a>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank" style="color:#38bdf8;"><span>💬</span> الدعم والمطور</a>
  <a href="{{ telegram_channel }}" target="_blank" style="color:#a855f7;"><span>📢</span> القناة الرسمية</a>
</nav>

<main class="layout">
  <aside class="sidebar-left">
    <div class="side-card">
      <h4>💳 محفظتك الرقمية</h4>
      <div class="wallet-box">
        <span style="font-size:11px;color:#a8b7d8;">الرصيد المتاح</span>
        <h2 style="margin:5px 0;color:#35eaa1;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شحن%20رصيد%20محفظتي" target="_blank" style="display:inline-block;margin-top:8px;padding:6px 14px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;font-weight:bold;font-size:10px;border-radius:6px;text-decoration:none;">＋ شحن الرصيد</a>
      </div>
    </div>

    <!-- بطاقة تقييم التطبيق والخدمة -->
    <div class="side-card" style="border-color:#35eaa1;">
      <h4>⭐ تقييم التطبيق والخدمة</h4>
      <p style="font-size:11px;color:#a8b7d8;margin:0 0 10px;">شاركونا رأيكم لتطوير خدماتنا باستمرار!</p>
      <form action="/add_review" method="POST">
        <input type="text" name="user_name" placeholder="اسمك الكريم" required style="width:100%;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;font-size:11px;margin-bottom:8px;">
        <select name="rating" style="width:100%;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;font-size:11px;margin-bottom:8px;">
          <option value="5">⭐⭐⭐⭐⭐ (ممتاز جداً)</option>
          <option value="4">⭐⭐⭐⭐ (جيد جداً)</option>
          <option value="3">⭐⭐⭐ (مقبول)</option>
        </select>
        <textarea name="comment" placeholder="اكتب تقييمك عن الخدمة والتطبيق..." required style="width:100%;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;font-size:11px;height:60px;margin-bottom:8px;resize:none;"></textarea>
        <button type="submit" style="width:100%;padding:8px;background:#35eaa1;color:#03091b;border:0;border-radius:8px;font-weight:bold;cursor:pointer;font-size:11px;">إرسال التقييم 🚀</button>
      </form>
    </div>
  </aside>

  <section class="main-column">
    <div class="hero">
      <div>
        <span style="color:#bca0ff;font-size:11px;font-weight:bold;">عالمك الرقمي الأول</span>
        <h1>شحن بطاقات وأكواد الألعاب بأفضل الأسعار والتسليم الفوري!</h1>
        <p>اختر منتجك المفضل واستخدم كود الخصم لشراء فوري وآمن عبر فودافون كاش أو بطاقات الدفع.</p>
        <a class="hero-btn" href="#products">تسوق الآن ←</a>
      </div>
      <div></div>
    </div>

    <div class="section-heading" id="products">
      <h2><span>🔥</span> أحدث المنتجات</h2>
    </div>

    <div class="product-grid" id="productGrid"></div>

    <!-- تقييمات العملاء السابقة -->
    <div style="margin-top:35px;" id="reviews">
      <div class="section-heading">
        <h2><span>⭐️</span> آراء وتقييمات العملاء</h2>
      </div>
      <div class="reviews-grid">
        {% for rev in reviews %}
        <div class="review-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <b style="font-size:12px;color:#35eaa1;">{{ rev['user_name'] }}</b>
            <span style="color:#facc15;font-size:11px;">{{ '⭐' * rev['rating'] }}</span>
          </div>
          <p style="font-size:11px;color:#cbd5e1;margin:0;">{{ rev['comment'] }}</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </section>
</main>

<!-- نافذة إتمام الشراء مع طرق الدفع وأكواد الخصم -->
<div class="checkout-modal" id="checkoutModal">
  <div class="checkout-box">
    <h3 id="modalProductName">اسم المنتج</h3>
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

    <!-- خانة كود الخصم الشيك -->
    <div style="display:flex;gap:8px;margin-bottom:15px;">
      <input type="text" id="promoInput" placeholder="أدخل كود الخصم (مثال: MIDO2026)" style="flex:1;padding:10px;background:#03091b;border:1px solid #315dff;border-radius:8px;color:#fff;font-size:11px;">
      <button onclick="applyPromoCode()" style="padding:10px 16px;background:linear-gradient(110deg,#9b37ff,#315dff);color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;font-size:11px;">تطبيق الكود 🏷️</button>
    </div>
    <p id="promoMsg" style="font-size:11px;margin:0 0 15px;text-align:right;"></p>

    <!-- اختيار طريقة الدفع -->
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
<div style="padding: 0 4%;">
  <div class="developer-footer-banner">
    <div style="font-size:32px;">👑</div>
    <h3 style="margin:0;color:#38bdf8;font-size:18px;">المطور والمسؤول عن المنصة</h3>
    <p style="margin:0;color:#aab9d8;font-size:12px;max-width:450px;line-height:1.6;">تم تصميم وتطوير هذا المتجر الذكي بواسطة المطور الاحترافي لتقديم أفضل تجربة شحن وأمان رقمي.</p>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="dev-btn-stylish">
      <span>💬</span> تواصل مباشرة مع المطور (Mido)
    </a>
  </div>
</div>

<footer>
  <p>© 2026 NOVA STORE - جميع الحقوق محفوظة | الأكواد ترسل تلقائياً إلى جروب MidoWorld</p>
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
    card.innerHTML = `
      <div class="product-visual">${visualHtml}</div>
      <h3 style="color:#fff;font-size:13px;margin:5px 0;">${p.name}</h3>
      <p style="font-size:10px;color:#8fa1c4;">${p.description}</p>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
        <span class="price">${p.price}</span>
        <button onclick="openCheckout(${p.price_val}, '${p.name}', '${p.description}')" class="add-btn">شراء فوري 💳</button>
      </div>`;
    productGrid.appendChild(card);
  });
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
    msg.textContent = '❌ كود الخصم غير صحيح أو منتهي الصلاحية.';
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

function filterProducts() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  renderProducts(PRODUCTS.filter(x => x.name.toLowerCase().includes(query)));
}

renderProducts(PRODUCTS);
</script>
</body>
</html>
"""

# ==================== المسارات والروابط المطلوبة ====================

@app.route('/game')
def game():
    return render_template_string(GAME_PAGE)

@app.route('/add_review', methods=["POST"])
def add_review():
    user_name = request.form.get("user_name", "").strip()
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()
    if user_name and comment:
        with get_db() as db:
            db.execute("INSERT INTO reviews (user_name, rating, comment, created_at) VALUES (?, ?, ?, ?)", (user_name, rating, comment, int(time.time())))
    return redirect(url_for("home"))

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
    posts = get_posts()
    flash_msg = get_setting("flash_msg", "عروض الساعات المحدودة!")

    return render_template_string(
        PAGE, 
        products=products, 
        reviews=reviews,
        posts=posts,
        flash_msg=flash_msg,
        user=user, 
        is_admin=is_admin, 
        admin_telegram=ADMIN_TELEGRAM_USERNAME, 
        telegram_bot=TELEGRAM_BOT_USERNAME,
        telegram_channel=TELEGRAM_CHANNEL_LINK
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
