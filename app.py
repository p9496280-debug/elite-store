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
<meta name="google-site-verification" content="-cqasmgepuPXVxFHJ53UtVgI4DdfCiGR_MbwjVIVv0M" />
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#03091b">

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

.nav-badge-game {
  background: linear-gradient(135deg, #ec4899, #8b5cf6) !important;
  color: #fff !important;
  border: none !important;
  font-weight: bold;
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

.product-visual{height:160px;border-radius:10px;background:radial-gradient(circle at 50% 20%,#1b3159,transparent 70%),#07142c;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;margin-bottom:10px;overflow:hidden;}
.product-img{width:100%;height:100%;object-fit:contain;border-radius:10px;}

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

.post-card img {
  width:100%;
  max-height:450px;
  object-fit:contain;
  border-radius:12px;
  margin-bottom:10px;
  border:1px solid #1f3a70;
  background:#03091b;
}

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
  <a href="/game" class="nav-badge-game">
    <span>🎮</span> منطقة الألعاب الترفيهية
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
</nav>

<main class="layout">
  <aside class="sidebar-left">
    <div class="side-card" style="border-color: #ec4899; background: linear-gradient(135deg, #1f072b, #0d041c);">
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
        <span style="font-size: 26px;">🎮</span>
        <div>
          <h4 style="margin: 0; color: #fff;">لعبة الذاكرة الذكية</h4>
          <span style="font-size: 9px; color: #ec4899;">العب مجاناً الآن للترفيه!</span>
        </div>
      </div>
      <p style="font-size: 10px; color: #a8b7d8; margin: 0 0 10px;">طابق كروت الألعاب واختبر سرعتك وذاكرتك مع روبوت NOVA!</p>
      <a href="/game" style="display:block; text-align:center; padding: 10px; background: linear-gradient(110deg, #ec4899, #8b5cf6); color: #fff; font-weight: bold; border-radius: 8px; text-decoration:none; font-size: 11px;">
        🕹️ ابدأ اللعب فوراً
      </a>
    </div>

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

    <div class="side-card">
      <h4>💳 محفظتك الرقمية</h4>
      <div class="wallet-box">
        <span style="font-size:11px;color:#a8b7d8;">الرصيد المتاح</span>
        <h2 style="margin:5px 0;color:#35eaa1;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شحن%20رصيد%20محفظتي%20في%20المتجر" target="_blank" style="display:inline-block;margin-top:8px;padding:6px 14px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;font-weight:bold;font-size:10px;border-radius:6px;text-decoration:none;">＋ شحن الرصيد</a>
      </div>
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

    <div class="hero">
      <div>
        <span style="color:#bca0ff;font-size:11px;font-weight:bold;">عالمك الرقمي الأول</span>
        <h1>شحن بطاقات وأكواد الألعاب بأفضل الأسعار والتسليم الفوري!</h1>
        <p>اختر منتجك المفضل واشترِ الآن باستخدام فودافون كاش أو بطاقة الائتمان.</p>
        <a class="hero-btn" href="#products">تسوق الآن ←</a>
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
  </section>
</main>

<footer id="footer">
  <div>
    <a class="brand" href="/" style="margin-bottom:10px;"><span class="brand-mark" style="width:28px;height:28px;font-size:22px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.7;margin:0 0 12px;">متجرك الرقمي الأول لبطاقات الدفع وأكواد الألعاب بأمان وسرعة.</p>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="/game">🎮 المنطقة الترفيهية</a>
    <a href="/spin">🎡 عجلة الحظ</a>
  </div>
  <div>
    <h4>الدعم والتليجرام</h4>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank">👨‍💻 التواصل مع المطور</a>
  </div>
</footer>

<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');

function renderProducts(items) {
  productGrid.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let visualHtml = p.image_url 
      ? `<img src="${p.image_url}" class="product-img" alt="${p.name}">` 
      : `<span style="color:${p.color};">${p.icon}</span>`;

    card.innerHTML = `
      <div class="product-visual">${visualHtml}</div>
      <h3 style="color:#fff;">${p.name}</h3>
      <p>${p.description}</p>
      <div class="price-row">
        <span class="price">${p.price}</span>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شراء%20${encodeURIComponent(p.name)}" target="_blank" class="add-btn" style="text-decoration:none;">شراء فوري 💳</a>
      </div>`;
    productGrid.appendChild(card);
  });
}
renderProducts(PRODUCTS);
</script>
</body>
</html>
"""

# ==================== اللعبة الترفيهية (Memory Game) ====================
GAME_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لعبة طابق كروت الألعاب الترفيهية | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#1e0836 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;}

.game-header {
  text-align: center;
  margin-bottom: 20px;
}
.game-stats {
  display: flex;
  gap: 20px;
  justify-content: center;
  background: #08152e;
  padding: 8px 20px;
  border-radius: 30px;
  border: 1px solid #315dff;
  margin-top: 10px;
  font-size: 13px;
}

/* شبكة كروت اللعبة */
.memory-grid {
  display: grid;
  grid-template-columns: repeat(4, 75px);
  gap: 12px;
  background: #07132c;
  padding: 15px;
  border-radius: 20px;
  border: 2px solid #8d38ff;
  box-shadow: 0 0 30px #8d38ff44;
}

.card-item {
  width: 75px;
  height: 90px;
  background: linear-gradient(145deg, #0f244a, #09132a);
  border: 2px solid #315dff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  cursor: pointer;
  user-select: none;
  transition: transform 0.4s ease, background 0.3s ease;
  transform-style: preserve-3d;
}

.card-item.flipped {
  background: linear-gradient(145deg, #276bff, #bc5bff);
  border-color: #35eaa1;
  transform: rotateY(180deg);
}

.card-item.matched {
  background: linear-gradient(145deg, #059669, #10b981);
  border-color: #35eaa1;
  cursor: default;
  box-shadow: 0 0 15px #35eaa1aa;
}

.robot-cheer {
  font-size: 45px;
  margin-top: 15px;
  filter: drop-shadow(0 0 10px #38bdf8);
}

.win-modal {
  display: none;
  position: fixed;
  inset: 0;
  background: #03091bee;
  backdrop-filter: blur(10px);
  z-index: 100;
  place-items: center;
}
.win-box {
  background: linear-gradient(145deg, #0b1a3d, #0d2454);
  border: 2px solid #35eaa1;
  border-radius: 20px;
  padding: 30px;
  text-align: center;
  max-width: 340px;
}
</style>
</head>
<body>

<div class="game-header">
  <h1 style="margin:0;font-size:26px;background:linear-gradient(110deg,#ec4899,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎮 لعبة الذاكرة الذكية</h1>
  <p style="margin:5px 0 0;color:#a8b7d8;font-size:12px;">طابق الكروت المتشابهة بأقل عدد حركات للتحدي والترفيه!</p>
  <div class="game-stats">
    <span>⏱️ الوقت: <b id="timer" style="color:#facc15;">0</b>ث</span>
    <span>🎯 المحاولات: <b id="moves" style="color:#38bdf8;">0</b></span>
  </div>
</div>

<div class="robot-cheer" id="robotCheer">🤖</div>

<div class="memory-grid" id="memoryGrid"></div>

<div style="margin-top:20px;display:flex;gap:12px;">
  <button onclick="restartGame()" style="padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;border:0;border-radius:10px;font-weight:bold;cursor:pointer;font-size:12px;">🔄 إعادة اللعب</button>
  <a href="/" style="padding:10px 20px;background:#1e293b;color:white;text-decoration:none;border-radius:10px;font-weight:bold;font-size:12px;">← العودة للمتجر</a>
</div>

<div class="win-modal" id="winModal">
  <div class="win-box">
    <div style="font-size:55px;">🏆</div>
    <h2 style="color:#35eaa1;margin:5px 0;">أحسنت بطل!</h2>
    <p id="winMsg" style="color:#cbd5e1;font-size:13px;line-height:1.6;"></p>
    <button onclick="restartGame()" style="padding:10px 20px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;font-weight:bold;border:0;border-radius:10px;cursor:pointer;width:100%;margin-top:10px;">العب مرة أخرى 🎮</button>
  </div>
</div>

<script>
const emojis = ['🎮', '▶', '👑', '💳', '🪙', '🎁'];
let cards = [...emojis, ...emojis];
let flippedCards = [];
let matchedPairs = 0;
let moves = 0;
let timer = 0;
let timerInterval = null;
let gameStarted = false;

function playFlipSound() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(400, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.1);
  gain.gain.setValueAtTime(0.1, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.1);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 0.1);
}

function playWinSound() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  [523, 659, 783, 1046].forEach((f, i) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = f;
    gain.gain.setValueAtTime(0.1, ctx.currentTime + i * 0.12);
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + i * 0.12 + 0.25);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime + i * 0.12);
    osc.stop(ctx.currentTime + i * 0.12 + 0.25);
  });
}

function shuffle(array) {
  return array.sort(() => Math.random() - 0.5);
}

function initBoard() {
  const grid = document.getElementById('memoryGrid');
  grid.innerHTML = '';
  shuffle(cards).forEach((icon, idx) => {
    const card = document.createElement('div');
    card.className = 'card-item';
    card.dataset.icon = icon;
    card.dataset.index = idx;
    card.innerHTML = '❓';
    card.addEventListener('click', flipCard);
    grid.appendChild(card);
  });
}

function flipCard() {
  if (flippedCards.length >= 2 || this.classList.contains('flipped') || this.classList.contains('matched')) return;

  if (!gameStarted) {
    gameStarted = true;
    timerInterval = setInterval(() => {
      timer++;
      document.getElementById('timer').textContent = timer;
    }, 1000);
  }

  playFlipSound();
  this.classList.add('flipped');
  this.innerHTML = this.dataset.icon;
  flippedCards.push(this);

  if (flippedCards.length === 2) {
    moves++;
    document.getElementById('moves').textContent = moves;
    checkMatch();
  }
}

function checkMatch() {
  const [c1, c2] = flippedCards;
  if (c1.dataset.icon === c2.dataset.icon) {
    c1.classList.add('matched');
    c2.classList.add('matched');
    flippedCards = [];
    matchedPairs++;
    document.getElementById('robotCheer').textContent = '😃';

    if (matchedPairs === emojis.length) {
      clearInterval(timerInterval);
      playWinSound();
      setTimeout(() => {
        document.getElementById('winMsg').textContent = `لقد أنهيت اللعبة بنجاح في ${timer} ثانية بـ ${moves} حركات فقط!`;
        document.getElementById('winModal').style.display = 'grid';
      }, 500);
    }
  } else {
    document.getElementById('robotCheer').textContent = '😅';
    setTimeout(() => {
      c1.classList.remove('flipped');
      c2.classList.remove('flipped');
      c1.innerHTML = '❓';
      c2.innerHTML = '❓';
      flippedCards = [];
      document.getElementById('robotCheer').textContent = '🤖';
    }, 800);
  }
}

function restartGame() {
  clearInterval(timerInterval);
  matchedPairs = 0;
  moves = 0;
  timer = 0;
  gameStarted = false;
  flippedCards = [];
  document.getElementById('timer').textContent = '0';
  document.getElementById('moves').textContent = '0';
  document.getElementById('robotCheer').textContent = '🤖';
  document.getElementById('winModal').style.display = 'none';
  initBoard();
}

initBoard();
</script>
</body>
</html>
"""

# ==================== المسارات واللوجو وملفات الأرشفة ====================

@app.route('/game')
def game():
    return render_template_string(GAME_PAGE)

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
