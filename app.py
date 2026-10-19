import os
import json
import time
import secrets
import sqlite3
import math
import requests

from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask,
    render_template_string,
    request,
    session,
    redirect,
    url_for,
    make_response,
    jsonify,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "moh99zzhvni893fj7@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "mohammedaaa222")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

# بيانات التليجرام وفودافون كاش الحقيقية المحدثة
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")
ADMIN_TELEGRAM_USERNAME = "Mido_M9do"
TELEGRAM_BOT_USERNAME = "midoassistantAIbot"
TELEGRAM_CHANNEL_LINK = "https://t.me/Midomsn"
VODAFONE_NUMBER = os.environ.get("VODAFONE_NUMBER", "01011541698")


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
                ("كود جوجل بلاي (10$)", "الولايات المتحدة", 500.00, "500 جـ", "GPLAY-9876", "▶", "بطاقات الألعاب", "#35eaa1", "عروض سريعة 🔥"),
                ("كود بلايستيشن (20$)", "الولايات المتحدة", 1000.00, "1000 جـ", "PSN-5432", "PS", "بطاقات الألعاب", "#62a0ff", "مميز"),
                ("كود إكس بوكس (25$)", "الولايات المتحدة", 1250.00, "1250 جـ", "XBOX-3344", "ⓧ", "بطاقات الألعاب", "#5dff9c", None),
                ("كود ستيم (20$)", "الولايات المتحدة", 1000.00, "1000 جـ", "STEAM-1122", "◉", "بطاقات الألعاب", "#9bb8ff", "عرض خاص"),
                ("كود آيتونز (15$)", "الولايات المتحدة", 750.00, "750 جـ", "ITUNES-7788", "", "بطاقات الهدايا", "#ffc107", None),
                ("شحن ببجي 660 شدة", "شحن فوري عن طريق الايدي", 350.00, "350 جـ", "PUBG-660", "🎮", "ألعاب", "#ff3b3b", "شائع 🔥"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, category, color, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)

        # كود خصم تجريبي مضاف
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


# ==================== القالب الرئيسي للمتجر ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff;--border:#1b315c}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.topbar{min-height:78px;display:flex;align-items:center;gap:20px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:10}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white}.brand b{color:#754bff}.brand-mark{width:39px;height:39px;display:grid;place-items:center;font-size:33px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.search{height:44px;max-width:420px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:30px;padding:0 17px;background:#09132b}
.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:13px}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.user-profile-badge {display: flex; align-items: center; gap: 10px; background: #0b1734; border: 1px solid #263d70; padding: 6px 14px; border-radius: 30px; text-decoration: none;}
.user-avatar { width: 34px; height: 34px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-weight: bold; color: white; }
.nav{min-height:50px;padding:0 4%;display:flex;align-items:center;gap:20px;border-bottom:1px solid #18284a;font-size:13px;background:#061028;overflow-x:auto;}
.nav a{color:#c4cde3;text-decoration:none;padding:6px 14px;border-radius:10px;transition:0.2s;white-space:nowrap;display:flex;align-items:center;gap:6px;}
.nav a:hover, .nav a.active{background:#1a2f5a;color:#fff}
.admin-badge { background: #570f0f; color: #ff7777; border: 1px solid #ff5555; padding: 6px 14px; border-radius: 12px; font-weight: bold; text-decoration:none;}

.layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:22px;padding:22px 4%}
.main-column{min-width:0}

/* Hero Section */
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

/* Categories Grid */
.categories{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin:20px 0}
.category{border:1px solid #172d53;border-radius:12px;background:linear-gradient(150deg,#07152e,#050d20);padding:14px 8px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;cursor:pointer;transition:0.2s}
.category:hover{border-color:#5a54ff;transform:translateY(-2px)}
.category span{font-size:22px;color:#65baff}
.category b{font-size:11px}

/* Products Section */
.section-heading{display:flex;align-items:center;justify-content:space-between;margin:25px 0 12px}
.section-heading h2{font-size:18px;margin:0;display:flex;align-items:center;gap:8px}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:14px;padding:12px;position:relative;transition:0.2s}
.product-card:hover{border-color:#5c52ff;transform:translateY(-3px)}
.product-visual{height:100px;border-radius:10px;background:radial-gradient(circle at 50% 20%,#1b3159,transparent 70%),#07142c;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;margin-bottom:10px;}
.badge-tag{position:absolute;top:8px;right:8px;background:#ff3b3b;color:white;font-size:9px;padding:2px 8px;border-radius:6px;font-weight:bold}
.badge-tag.memo{background:#315dff}
.product-card h3{font-size:13px;margin:5px 0 2px;}
.product-card p{font-size:10px;color:#8fa1c4;margin:0 0 10px}
.price-row{display:flex;align-items:center;justify-content:space-between;margin-top:8px}
.price{font-size:13.5px;font-weight:800;color:#35eaa1}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;cursor:pointer}

/* Sidebar Left */
.sidebar-left{display:flex;flex-direction:column;gap:18px;}
.side-card{border:1px solid #243e75;border-radius:18px;padding:16px;background:linear-gradient(155deg,#081735,#060d22);}
.side-card h4{margin:0 0 10px;font-size:13px;color:#fff;display:flex;align-items:center;gap:8px;}
.quick-link-btn{display:flex;align-items:center;gap:10px;width:100%;padding:10px 12px;background:#091a3e;border:1px solid #1f3769;border-radius:10px;color:#cde0ff;font-size:11px;text-decoration:none;margin-bottom:8px;transition:0.2s;}
.quick-link-btn:hover{background:#12295a;border-color:#315dff;color:#fff;}
.wallet-box{background:linear-gradient(135deg,#0e234e,#180b3d);border:1px solid #35eaa166;border-radius:14px;padding:14px;text-align:center;}

/* Flash Deals Box ⚡ (إضافة ربحية 1) */
.flash-box{background:linear-gradient(135deg,#5e0a0a,#2b0808);border:1px solid #ff3b3b;border-radius:14px;padding:12px;margin-bottom:15px;display:flex;align-items:center;justify-content:space-between;}
.timer{font-size:14px;font-weight:bold;color:#facc15;background:#03091b;padding:4px 10px;border-radius:8px;}

/* Promo Box (إضافة ربحية 2) */
.promo-input-group{display:flex;gap:6px;margin-top:8px;}
.promo-input-group input{flex:1;padding:8px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;font-size:11px;}
.promo-input-group button{padding:8px 12px;background:#315dff;color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;font-size:11px;}

/* Modal Checkout */
.checkout-modal{display:none;position:fixed;inset:0;background:rgba(3,9,27,0.85);backdrop-filter:blur(8px);z-index:200;place-items:center;padding:20px;}
.checkout-box{background:linear-gradient(145deg,#07132c,#0a1a3f);border:1px solid #315dff;border-radius:18px;padding:25px;width:100%;max-width:400px;text-align:center;}
.checkout-box h3{margin-top:0;color:#fff;}
.vodafone-card{background:#e11d48;color:white;padding:12px;border-radius:10px;margin:15px 0;font-weight:bold;font-size:13px;}

/* Footer */
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
            <img src="{{ user['avatar'] }}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">
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
  <a href="/" class="active">🏠 الرئيسية</a>
  <a href="/spin" style="color:#ffc107;font-weight:bold;">🎡 عجلة الحظ</a>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank" style="color:#38bdf8;">💬 التواصل مع المطور والدعم</a>
  <a href="{{ telegram_channel }}" target="_blank" style="color:#a855f7;">📢 قناة التليجرام</a>
</nav>

<main class="layout">
  <!-- الجانب الأيسر المطور -->
  <aside class="sidebar-left">
    <!-- 1. مساعد الذكاء الاصطناعي -->
    <div class="side-card">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        <div style="width:40px;height:40px;border-radius:50%;background:radial-gradient(circle,#2c8cff,#11175a);display:grid;place-items:center;font-size:20px;">✦</div>
        <div>
          <h4 style="margin:0;">مساعد NOVA AI</h4>
          <span style="font-size:9px;color:#2fe19a;">● متصل الآن</span>
        </div>
      </div>
      <p style="font-size:11px;color:#c4d1ed;line-height:1.6;margin:0;">اختر منتجك واشترِ فوراً بفودافون كاش بكل سهولة وسرعة!</p>
    </div>

    <!-- 2. بطاقة المحفظة والرصيد -->
    <div class="side-card">
      <h4>💳 محفظتك الرقمية</h4>
      <div class="wallet-box">
        <span style="font-size:11px;color:#a8b7d8;">الرصيد المتاح</span>
        <h2 style="margin:5px 0;color:#35eaa1;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شحن%20رصيد%20محفظتي%20في%20المتجر" target="_blank" style="display:inline-block;margin-top:8px;padding:6px 14px;background:linear-gradient(110deg,#35eaa1,#00b894);color:#03091b;font-weight:bold;font-size:10px;border-radius:6px;text-decoration:none;">＋ شحن الرصيد</a>
      </div>
    </div>

    <!-- 3. نظام الإحالة والربح "شارك واكسب" (إضافة 1) -->
    <div class="side-card" style="border-color:#315dff;">
      <h4 style="color:#60a5fa;">🎁 شارك واكسب رصيد!</h4>
      <p style="font-size:10px;color:#a8b7d8;margin:0 0 8px;">ادعُ أصدقاءك للشراء من المتجر واكسب 10 جنيه رصيد مجاني!</p>
      {% if user %}
        <input readonly value="{{ request.host_url }}register?ref={{ user['ref_code'] }}" style="width:100%;padding:6px;background:#03091b;border:1px solid #1f3769;color:#35eaa1;border-radius:6px;font-size:9px;" onclick="this.select();document.execCommand('copy');alert('تم نسخ رابط الإحالة الخاص بك!')">
        <small style="display:block;margin-top:4px;color:#94a3b8;font-size:8px;text-align:center;">اضغط على الرابط للنسخ والمشاركة 📲</small>
      {% else %}
        <a href="/login" style="font-size:10px;color:#38bdf8;text-decoration:none;display:block;text-align:center;">قم بتسجيل الدخول للحصول على رابطك الخاص</a>
      {% endif %}
    </div>

    <!-- 4. كود الخصم والبروموكود (إضافة 2) -->
    <div class="side-card">
      <h4>🏷️ هل لديك كود خصم؟</h4>
      <div class="promo-input-group">
        <input id="promoCodeInput" placeholder="أدخل كود الخصم">
        <button onclick="applyPromo()">تطبيق</button>
      </div>
      <small id="promoMsg" style="display:block;margin-top:6px;font-size:10px;"></small>
    </div>

    <!-- 5. روابط سريعة -->
    <div class="side-card">
      <h4>⚡ خدمات سريعة</h4>
      <a href="/account" class="quick-link-btn"><span>👤</span> تعديل الحساب واللوجو</a>
      <a href="/spin" class="quick-link-btn"><span>🎡</span> تجربة عجلة الحظ</a>
      <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="quick-link-btn"><span>💬</span> الدعم والمساعدة الفورية</a>
      <a href="{{ telegram_channel }}" target="_blank" class="quick-link-btn"><span>📢</span> انضم لقناتنا على تليجرام</a>
    </div>
  </aside>

  <!-- الجزء الأيمن المحتوي على المنتجات والعروض -->
  <section class="main-column">
    <!-- العداد التنازلي للعروض السريعة (إضافة 3) -->
    <div class="flash-box">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:20px;">⚡</span>
        <div>
          <b style="font-size:12px;color:#fff;display:block;">عروض الساعات المحدودة!</b>
          <span style="font-size:10px;color:#fca5a5;">خصومات خاصة تنتهي قريباً</span>
        </div>
      </div>
      <div class="timer" id="flashTimer">02:45:18</div>
    </div>

    <div class="hero">
      <div>
        <span style="color:#bca0ff;font-size:11px;font-weight:bold;">عالمك الرقمي الأول</span>
        <h1>شحن بطاقات وأكواد الألعاب بأفضل الأسعار والتسليم الفوري!</h1>
        <p>اختر منتجك المفضل واشترِ الآن باستخدام فودافون كاش بسهولة وأمان.</p>
        <a class="hero-btn" href="#products">تسوق الآن ←</a>
        <div class="trust-row"><span>♧ دفع آمن 100%</span><span>◷ تسليم سريع</span><span>دعم 24/7</span></div>
      </div>
      <div class="hero-art">
        <div class="gift-card google"><span style="color:#35eaa1;font-size:26px;">▶</span><b>Google Play</b></div>
        <div class="gift-card playstation"><span style="color:#62a0ff;font-size:22px;">PSN</span><b>PlayStation</b></div>
        <div class="gift-card steam"><span style="color:#9bb8ff;font-size:22px;">◉</span><b>STEAM</b></div>
      </div>
    </div>

    <div class="categories">
      <div class="category" onclick="filterCat('الكل')"><span>▦</span><b>الكل</b></div>
      <div class="category" onclick="filterCat('بطاقات الألعاب')"><span style="color:#35eaa1;">▶</span><b>بطاقات الألعاب</b></div>
      <div class="category" onclick="filterCat('بطاقات الهدايا')"><span style="color:#bc5bff;">🎁</span><b>بطاقات الهدايا</b></div>
      <div class="category" onclick="filterCat('ألعاب')"><span style="color:#ff3b3b;">🎮</span><b>الألعاب والشحن</b></div>
    </div>

    <div class="section-heading" id="products">
      <h2><span>🔥</span> أحدث المنتجات</h2>
    </div>

    <div class="product-grid" id="productGrid"></div>
  </section>
</main>

<!-- نافذة الدفع والشراء بفودافون كاش -->
<div class="checkout-modal" id="checkoutModal">
  <div class="checkout-box">
    <h3 id="modalProdName">شراء المنتج</h3>
    <p style="font-size:12px;color:#a8b7d8;" id="modalProdDesc"></p>
    
    <div class="vodafone-card">
      📲 رقم تحويل فودافون كاش:<br>
      <span style="font-size:18px;letter-spacing:1px;">{{ vodafone_number }}</span>
    </div>

    <div style="background:#03091b;padding:12px;border-radius:10px;text-align:right;font-size:12px;margin-bottom:15px;line-height:1.8;">
      <div>سعر المنتج الأصلي: <b id="basePrice" style="color:#fff;">0</b> جـ</div>
      <div>رسوم التحويل (3 جـ لكل 10 جـ): <b id="feePrice" style="color:#ff7777;">0</b> جـ</div>
      <div id="discountRow" style="display:none;color:#35eaa1;">خصم الكود التطبيقي: <b id="discountVal">0</b> جـ</div>
      <hr style="border-color:#1b315c;margin:6px 0;">
      <div>المبلغ الإجمالي المطلوب تحويله: <b id="totalPrice" style="color:#35eaa1;font-size:15px;">0</b> جـ</div>
    </div>

    <p style="font-size:11px;color:#cbd5e1;margin-bottom:15px;">قم بتحويل المبلغ الإجمالي إلى الرقم أعلاه ثم تواصل مع المطور لاستلام كود الشحن فوراً!</p>

    <div style="display:flex;gap:10px;">
      <a id="teleBuyBtn" target="_blank" style="flex:1;padding:10px;background:#2563eb;color:white;border-radius:8px;text-decoration:none;font-weight:bold;font-size:12px;">إرسال تأكيد التحويل 💬</a>
      <button onclick="closeCheckout()" style="padding:10px;background:#334155;color:white;border:0;border-radius:8px;cursor:pointer;font-size:12px;">إلغاء</button>
    </div>
  </div>
</div>

<!-- الفوتر المطور المحتوي على الروابط والروابط الحقيقية -->
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
    <h4>وسائل الدفع</h4>
    <div style="font-size:18px;margin-top:8px;color:#35eaa1;font-weight:bold;">📱 فودافون كاش</div>
    <small style="display:block;margin-top:15px;color:#8194ba;">© 2026 NOVA STORE جميع الحقوق محفوظة</small>
  </div>
</footer>

<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');
const adminTelegram = "{{ admin_telegram }}";
let activeDiscountPercent = 0;

function renderProducts(items) {
  productGrid.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let badgeHtml = p.badge ? `<span class="badge-tag ${p.badge==='مميز'?'memo':''}">${p.badge}</span>` : '';
    card.innerHTML = `
      ${badgeHtml}
      <div class="product-visual" style="color:${p.color};">${p.icon}</div>
      <h3 style="color:#fff;">${p.name}</h3>
      <p>${p.description}</p>
      <div class="price-row">
        <span class="price">${p.price}</span>
        <button class="add-btn" onclick="openCheckout(${p.id})">شراء بفودافون كاش</button>
      </div>`;
    productGrid.appendChild(card);
  });
}

function openCheckout(prodId) {
  const p = PRODUCTS.find(x => x.id === prodId);
  if (!p) return;
  
  let basePrice = p.price_val;
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

  document.getElementById('modalProdName').textContent = p.name;
  document.getElementById('modalProdDesc').textContent = p.description;
  document.getElementById('basePrice').textContent = p.price_val;
  document.getElementById('feePrice').textContent = fee;
  document.getElementById('totalPrice').textContent = total.toFixed(1);

  const msg = encodeURIComponent(`مرحباً، أود شراء المنتج: (${p.name})\nالمبلغ المحول شامل الرسوم: ${total.toFixed(1)} جنيه على رقم فودافون كاش.`);
  document.getElementById('teleBuyBtn').href = `https://t.me/${adminTelegram}?text=${msg}`;

  document.getElementById('checkoutModal').style.display = 'grid';
}

function closeCheckout() {
  document.getElementById('checkoutModal').style.display = 'none';
}

function applyPromo() {
  const code = document.getElementById('promoCodeInput').value.trim().toUpperCase();
  const msg = document.getElementById('promoMsg');
  if (code === 'MIDO2026') {
    activeDiscountPercent = 10;
    msg.style.color = '#35eaa1';
    msg.textContent = '🎉 تم تطبيق كود الخصم 10% بنجاح!';
  } else {
    msg.style.color = '#ff7777';
    msg.textContent = '❌ كود الخصم غير صحيح أو منتهي.';
  }
}

// عداد العروض التنازلي
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

# ==================== باقي المسارات والصفحات ====================
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

ACCOUNT_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>حسابي | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;display:grid;place-items:center;min-height:100vh;padding:20px;}
.box{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;text-align:center;width:400px;}
input{width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:white;box-sizing:border-box;}
button{padding:10px 20px;background:#315dff;border:0;border-radius:8px;color:white;font-weight:bold;cursor:pointer;margin-top:10px;}
.avatar-preview{width:70px;height:70px;border-radius:50%;margin:0 auto 10px;background:linear-gradient(135deg,#9b37ff,#315dff);display:grid;place-items:center;font-size:28px;overflow:hidden;border:2px solid #35eaa1;}
</style>
</head>
<body>
<div class="box">
  <div class="avatar-preview">
    {% if user["avatar"].startswith('http') or user["avatar"].startswith('/') %}
      <img src="{{ user['avatar'] }}" style="width:100%;height:100%;object-fit:cover;">
    {% else %}
      {{ user["avatar"] }}
    {% endif %}
  </div>
  <h2>{{ user["name"] }}</h2>
  <p style="color:#35eaa1;font-weight:bold;margin:5px 0;">الحالة: {{ user["status_title"] }} | الرصيد: {{ user["balance"] }} جـ</p>
  
  <form method="POST" action="/update_profile" style="margin-top:20px;text-align:right;">
    <label style="font-size:11px;color:#a8b7d8;">تعديل اللوجو / رابط الصورة:</label>
    <input name="avatar" value="{{ user['avatar'] }}" placeholder="أدخل رابط صورة أو إيموجي" required>
    <label style="font-size:11px;color:#a8b7d8;">تعديل حالة الحساب:</label>
    <input name="status_title" value="{{ user['status_title'] }}" placeholder="مثال: VIP / عضو ممتاز" required>
    <button type="submit" style="width:100%;">حفظ التعديلات</button>
  </form>

  <div style="margin-top:20px;display:flex;justify-content:space-between;">
    <a href="/" style="color:#9db4ff;text-decoration:none;font-size:12px;">← الرئيسية</a>
    <a href="/logout" style="color:#ff7777;text-decoration:none;font-size:12px;">تسجيل الخروج</a>
  </div>
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
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;padding:30px}
.box{background:#07132c;border:1px solid #315dff;border-radius:15px;padding:25px;max-width:550px;margin:20px auto;}
input{width:100%;padding:12px;margin:10px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;}
button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;}
</style>
</head>
<body>
<div style="max-width:550px;margin:auto;display:flex;justify-content:space-between;align-items:center;">
  <h2>⚙️ لوحة تحكم المطور</h2>
  <a href="/" style="color:#8198ff;text-decoration:none;">← العودة للمتجر</a>
</div>

<div class="box">
  <h3>➕ إضافة منتج جديد</h3>
  <form method="POST" action="/admin/add_product">
    <input name="name" placeholder="اسم المنتج" required>
    <input name="description" placeholder="الوصف" required>
    <input type="number" step="0.01" name="price_val" placeholder="السعر بالجنيه (مثال: 500)" required>
    <input name="price" placeholder="نص السعر (مثال: 500 جـ)" required>
    <input name="code" placeholder="الكود الرقمي" required>
    <input name="icon" placeholder="الأيقونة (مثال: ▶ أو 🎮)" required>
    <input name="category" placeholder="القسم (بطاقات الألعاب / بطاقات الهدايا / ألعاب)" required>
    <input name="badge" placeholder="الشارة (اختياري)">
    <button type="submit">إضافة المنتج</button>
  </form>
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
    <button onclick="location.reload()" style="margin-top:15px;padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;">حسناً</button>
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
  { label: '5 جنيه 💰', color: '#8d38ff', amount: 5 },
  { label: 'حظ أوفر 😅', color: '#1b2a4a', amount: 0 },
  { label: '10 جنيه 💳', color: '#315dff', amount: 10 },
  { label: 'خصم 20% 🏷️', color: '#00c853', amount: 0 },
  { label: '20 جنيه 🎁', color: '#ff9100', amount: 20 },
  { label: 'حظ أوفر 😅', color: '#263d70', amount: 0 }
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
      document.getElementById('prizeTitle').textContent = prize.amount > 0 ? '🎉 مبروك!' : '😅 حظ أوفر!';
      document.getElementById('prizeDesc').textContent = data.msg;
      resultModal.style.display = 'grid';
    }, 6000);
  });
});
</script>
</body>
</html>
"""

# ==================== المسارات العامة ====================

@app.route("/admin")
def admin_panel():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    return render_template_string(ADMIN_PANEL_PAGE)

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

    with get_db() as db:
        db.execute("""
            INSERT INTO products (name, description, price_val, price, code, icon, category, color, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?, '#315dff', ?)
        """, (name, description, price_val, price, code, icon, category, badge))

    return redirect(url_for("admin_panel"))


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
            {'label': '5 جنيه 💰', 'amount': 5},
            {'label': 'حظ أوفر 😅', 'amount': 0},
            {'label': '10 جنيه 💳', 'amount': 10},
            {'label': 'خصم 20% 🏷️', 'amount': 0},
            {'label': '20 جنيه 🎁', 'amount': 20},
            {'label': 'حظ أوفر 😅', 'amount': 0}
        ]
        prize = prizes[selectedIndex]

        with get_db() as db:
            if prize['amount'] > 0:
                db.execute("UPDATE users SET balance = balance + ?, last_spin_date = ? WHERE email = ?", (prize['amount'], today_str, email))
            else:
                db.execute("UPDATE users SET last_spin_date = ? WHERE email = ?", (today_str, email))

        msg = f"مبروك! فزت بـ ({prize['label']}) وأضيفت لمحفظتك." if prize['amount'] > 0 else "حاول مجدداً غداً."
        return jsonify({"status": "success", "index": selectedIndex, "msg": msg})

    return render_template_string(SPIN_PAGE)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    step = 1
    ref = request.args.get("ref", "")
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
                        
                        session["temp_reg"] = {
                            "name": name, "email": email, "password": generate_password_hash(password), "telegram_id": telegram_id, "ref": ref
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
                        INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, ref_code, referred_by, created_at)
                        VALUES (?, ?, ?, ?, 0.0, 1, ?, ?, ?)
                    """, (temp["name"], temp["email"], temp["password"], temp["telegram_id"], my_ref, temp.get("ref"), int(time.time())))
                    
                    # مكافأة دعوة الأصدقاء
                    if temp.get("ref"):
                        db.execute("UPDATE users SET balance = balance + 10.0 WHERE ref_code = ?", (temp.get("ref"),))

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


@app.route("/login_google")
def login_google():
    google_email = "google_user_" + str(secrets.randbelow(10000)) + "@gmail.com"
    my_ref = "REF" + str(secrets.randbelow(899999) + 100000)
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (google_email,)).fetchone()
        if not user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, avatar, status_title, ref_code, created_at)
                VALUES (?, ?, ?, 'google_user', 0.0, 1, '🌐', 'عضو جوجل', ?, ?)
            """, ("مستخدم جوجل", google_email, generate_password_hash("google123"), my_ref, int(time.time())))
    session["user_email"] = google_email
    return redirect(url_for("account"))


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
    avatar = request.form.get("avatar", "🤖").strip()
    status_title = request.form.get("status_title", "عضو مميز").strip()
    with get_db() as db:
        db.execute("UPDATE users SET avatar = ?, status_title = ? WHERE email = ?", (avatar, status_title, email))
    return redirect(url_for("account"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


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
    return render_template_string(
        PAGE, 
        products=products, 
        user=user, 
        is_admin=is_admin, 
        admin_telegram=ADMIN_TELEGRAM_USERNAME, 
        telegram_bot=TELEGRAM_BOT_USERNAME,
        telegram_channel=TELEGRAM_CHANNEL_LINK,
        vodafone_number=VODAFONE_NUMBER
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
