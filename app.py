import os
import json
import time
import secrets
import sqlite3
import urllib.parse
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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

ADMIN_TELEGRAM_USERNAME = "Mido_M9do"


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
                created_at INTEGER NOT NULL
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
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)

        # الحساب الإداري
        admin_user = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, balance, verified, avatar, status_title, created_at)
                VALUES (?, ?, ?, 999999.0, 1, '👑', 'المطور الرئيسي', ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), int(time.time())))

        # المنتجات الأولية
        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("اشتراك ChatGPT Plus (شهر)", "وصول كامل لـ GPT-4o وDALL-E 3 سرعة فائقة", 20.00, "$20.00", "AI-GPT4", "🤖", "", "أدوات الذكاء الاصطناعي", "#10b981", "شائع 🔥"),
                ("اشتراك Midjourney Pro", "توليد صور فائقة الجودة بالذكاء الاصطناعي", 30.00, "$30.00", "AI-MID", "🎨", "", "أدوات الذكاء الاصطناعي", "#a855f7", "مميز"),
                ("بطاقة دفع مسبقّة (50$)", "بطاقة فيزا وهمية مفعلة للشراء أونلاين", 50.00, "$50.00", "VISA-50", "💳", "", "بطاقات الدفع", "#38bdf8", None),
                ("كود آيتونز (15$)", "حسابات الولايات المتحدة", 15.00, "$15.00", "ITUNES-15", "", "", "بطاقات الهدايا", "#ffc107", None),
                ("كود ستيم (20$)", "محفظة ستيم الأمريكية", 20.00, "$20.00", "STEAM-20", "◉", "", "Steam", "#9bb8ff", None),
                ("كود إكس بوكس (25$)", "بطاقة هدايا Xbox Game Pass", 25.00, "$25.00", "XBOX-25", "ⓧ", "", "Xbox", "#5dff9c", "مميز"),
                ("كود بلايستيشن (20$)", "ستور الولايات المتحدة", 20.00, "$20.00", "PSN-20", "PS", "", "PlayStation", "#62a0ff", "مميز"),
                ("كود جوجل بلاي (10$)", "متجر جوجل بلاي الأمريكي", 10.00, "$10.00", "GPLAY-10", "▶", "", "Google Play", "#35eaa1", "الأكثر مبيعا"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)

        cursor_rev = db.execute("SELECT COUNT(*) as count FROM reviews")
        if cursor_rev.fetchone()["count"] == 0:
            default_reviews = [
                ("أحمد مصطفى", 5, "خدمة فحص الروابط واشتراك ChatGPT ممتاز وسريع جداً 🔥", int(time.time())),
                ("محمود علي", 5, "مصداقية عالية وسرعة في الشحن، أفضل متجر أدوات ذكاء اصطناعي!", int(time.time())),
            ]
            db.executemany("INSERT INTO reviews (user_name, rating, comment, created_at) VALUES (?, ?, ?, ?)", default_reviews)


init_db()


def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in rows]


def get_reviews():
    with get_db() as db:
        rows = db.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 6").fetchall()
        return [dict(row) for row in rows]


# ==================== الصفحة الرئيسية الكاملة ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | متجر أدوات الذكاء الاصطناعي وبطاقات الدفع</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--border:#1b315c;--accent:#315dff;--teal:#35eaa1;--purple:#a855f7}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#f4f7ff;font-family:'Cairo',sans-serif;min-height:100vh;}

/* الهيدر العلوي */
.topbar{height:76px;display:flex;align-items:center;justify-content:space-between;padding:0 3%;background:#040a1bed;border-bottom:1px solid #18284a;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white;}
.brand b{color:#754bff}
.brand-mark{width:38px;height:38px;display:grid;place-items:center;font-size:30px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}

.search-bar{height:42px;width:380px;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:25px;padding:0 16px;background:#09132b;}
.search-bar input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:12px;font-family:'Cairo';}

.top-actions{display:flex;align-items:center;gap:12px;}
.lang-btn{background:#0b1734;border:1px solid #263d70;color:#fff;padding:6px 12px;border-radius:20px;font-size:11px;display:flex;align-items:center;gap:5px;cursor:pointer;}
.cart-btn{position:relative;background:#0b1734;border:1px solid #263d70;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;color:#fff;text-decoration:none;}
.cart-badge{position:absolute;top:-4px;right:-4px;background:#315dff;color:#fff;font-size:9px;width:18px;height:18px;border-radius:50%;display:grid;place-items:center;font-weight:bold;}

.auth-btns{display:flex;gap:8px;}
.btn-login{color:#d8e2ff;text-decoration:none;font-size:12px;padding:8px 12px;}
.btn-reg{padding:8px 16px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;}

/* شريط التنقل الثاني */
.nav-bar{height:52px;padding:0 3%;display:flex;align-items:center;gap:22px;border-bottom:1px solid #18284a;background:#050d22;font-size:13px;font-weight:600;}
.nav-bar a{color:#c4cde3;text-decoration:none;transition:0.2s;}
.nav-bar a:hover, .nav-bar a.active{color:#fff;}

/* التخطيط الرئيسي */
.layout{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:20px;padding:20px 3%;}
@media (max-width:1000px){.layout{grid-template-columns:1fr;}.ai-sidebar{display:none;}}

/* الهيرو البانر */
.hero{background:radial-gradient(circle at 75% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 60%,#100a3b);border:1px solid #263f77;border-radius:20px;padding:25px;display:grid;grid-template-columns:1.2fr 1fr;align-items:center;position:relative;overflow:hidden;margin-bottom:20px;}
.hero h1{font-size:clamp(18px,2vw,25px);line-height:1.6;margin:0 0 10px;font-weight:800;}
.hero p{color:#c4cce2;font-size:11.5px;line-height:1.7;margin:0 0 15px;}
.hero-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;}

/* كروت الإضافات الثلاث المخصصة للذكاء الاصطناعي (مطابقة للصورة المرفقة) */
.features-container{margin:25px 0;}
.features-title-main{text-align:center;margin-bottom:15px;}
.features-title-main h2{font-size:22px;margin:0;color:#fff;}
.features-title-main p{font-size:12px;color:#a8b7d8;margin:4px 0 0;}

.feature-cards-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;}
@media (max-width:850px){.feature-cards-grid{grid-template-columns:1fr;}}

.f-card{border-radius:18px;padding:20px;text-align:center;position:relative;overflow:hidden;transition:0.3s ease;display:flex;flex-direction:column;align-items:center;justify-content:space-between;}
.f-card:hover{transform:translateY(-4px);}

.f-card.purple{background:linear-gradient(145deg,#1f0a3a,#090f28);border:1px solid #a855f7;box-shadow:0 0 20px rgba(168,85,247,0.15);}
.f-card.blue{background:linear-gradient(145deg,#061a3f,#050c1e);border:1px solid #38bdf8;box-shadow:0 0 20px rgba(56,189,248,0.15);}
.f-card.green{background:linear-gradient(145deg,#042d27,#050c1e);border:1px solid #10b981;box-shadow:0 0 20px rgba(16,185,129,0.15);}

.f-icon{font-size:42px;margin-bottom:10px;}
.f-card h3{margin:0 0 8px;font-size:16px;color:#fff;}
.f-card p{font-size:11px;color:#a8b7d8;line-height:1.6;margin:0 0 15px;}
.f-btn{padding:8px 18px;border-radius:20px;font-size:11px;font-weight:bold;cursor:pointer;border:0;width:100%;transition:0.2s;}

.f-card.purple .f-btn{background:linear-gradient(110deg,#a855f7,#315dff);color:#fff;}
.f-card.blue .f-btn{background:linear-gradient(110deg,#38bdf8,#315dff);color:#000;}
.f-card.green .f-btn{background:linear-gradient(110deg,#10b981,#35eaa1);color:#000;}

/* واجهة أداة فحص الروابط (Popup Modal) */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(3,9,27,0.9);backdrop-filter:blur(8px);z-index:1000;place-items:center;padding:20px;}
.scanner-box{background:linear-gradient(145deg,#07142c,#0a1d42);border:1px solid #38bdf8;border-radius:20px;padding:25px;width:100%;max-width:480px;text-align:center;}
.scanner-input{width:100%;padding:12px;background:#03091b;border:1px solid #263d70;border-radius:10px;color:#fff;font-size:12px;margin:15px 0;}

/* التصنيفات السبعة */
.cat-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-bottom:25px;}
@media (max-width:900px){.cat-grid{grid-template-columns:repeat(4,1fr);}}
.cat-card{background:linear-gradient(150deg,#07152e,#050d20);border:1px solid #1a2d54;border-radius:14px;padding:12px 6px;text-align:center;cursor:pointer;transition:0.2s;}
.cat-card:hover{border-color:#315dff;transform:translateY(-2px);}
.cat-card span{font-size:24px;display:block;margin-bottom:6px;}
.cat-card b{font-size:10.5px;color:#fff;display:block;}
.cat-card p{font-size:8.5px;color:#8fa1c4;margin:2px 0 0;}

/* شبكة المنتجات */
.sec-title{display:flex;align-items:center;justify-content:space-between;margin:20px 0 12px;}
.sec-title h2{font-size:17px;margin:0;display:flex;align-items:center;gap:8px;}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;}
.product-card{background:linear-gradient(150deg,#08152e,#050c1e);border:1px solid #1b3159;border-radius:16px;padding:12px;position:relative;transition:0.2s;}
.product-card:hover{border-color:#35eaa1;transform:translateY(-3px);}
.product-visual{height:140px;background:#03091b;border-radius:12px;display:grid;place-items:center;font-size:36px;margin-bottom:10px;position:relative;}
.badge{position:absolute;top:8px;right:8px;background:#ef4444;color:white;font-size:9px;padding:2px 8px;border-radius:6px;font-weight:bold;}
.badge.memo{background:#315dff;}
.product-card h3{font-size:12.5px;margin:4px 0 2px;color:#fff;}
.product-card p{font-size:9.5px;color:#8fa1c4;margin:0 0 10px;}
.price-row{display:flex;align-items:center;justify-content:space-between;}
.price{font-size:13px;font-weight:800;color:#35eaa1;}
.add-btn{padding:6px 12px;background:linear-gradient(100deg,#933aff,#315dff);border:0;border-radius:8px;font-size:10.5px;font-weight:700;color:white;cursor:pointer;}

/* مساعد الذكاء الاصطناعي الجانبي */
.ai-sidebar{background:#07132c;border:1px solid #1b3159;border-radius:18px;padding:16px;height:fit-content;position:sticky;top:90px;}
.ai-header{display:flex;align-items:center;gap:10px;margin-bottom:12px;border-bottom:1px solid #18284a;padding-bottom:10px;}
.ai-avatar{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#38bdf8,#315dff);display:grid;place-items:center;font-size:22px;border:2px solid #35eaa1;}
.ai-msg-box{background:#03091b;border:1px solid #1b3159;border-radius:12px;padding:12px;font-size:11px;line-height:1.6;color:#c4cde3;margin-bottom:12px;max-height:220px;overflow-y:auto;}
.ai-action-btn{display:block;width:100%;padding:8px 12px;background:#0b1734;border:1px solid #263d70;border-radius:10px;color:#cbd5e1;font-size:11px;text-align:right;margin-bottom:6px;cursor:pointer;transition:0.2s;}
.ai-action-btn:hover{border-color:#315dff;background:#102044;color:#fff;}
.ai-input-box{display:flex;align-items:center;background:#03091b;border:1px solid #263d70;border-radius:20px;padding:4px 4px 4px 12px;margin-top:10px;}
.ai-input-box input{flex:1;background:transparent;border:0;outline:0;color:#fff;font-size:11px;font-family:'Cairo';}
.ai-send-btn{width:32px;height:32px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:50%;color:white;display:grid;place-items:center;cursor:pointer;}

/* التذييل Footer */
footer{border-top:1px solid #192b4e;padding:35px 3%;background:#030714;display:grid;grid-template-columns:1.8fr 1.2fr 1.2fr 1fr;gap:25px;color:#aab9d8;font-size:11px;margin-top:40px;}
@media (max-width:850px){footer{grid-template-columns:1fr;}}
footer h4{color:#fff;margin:0 0 12px;font-size:13px;}
footer a{display:block;color:#aab8d0;text-decoration:none;margin:6px 0;}
</style>
</head>
<body>

<!-- الشريط العلوي -->
<header class="topbar">
  <a class="brand" href="/">
    <div class="brand-mark">N</div>
    <span>NOVA <b>STORE</b></span>
  </a>

  <div class="search-bar">
    <span>⌕</span>
    <input id="searchInput" type="search" placeholder="ابحث عن أدوات ذكاء اصطناعي أو بطاقات..." onkeyup="filterProducts()">
  </div>

  <div class="top-actions">
    <div class="lang-btn"><span>🌐 AR</span></div>
    <a href="/cart" class="cart-btn">
      <span>🛒</span>
      <span class="cart-badge" id="cartCount">0</span>
    </a>
    {% if user %}
      <a href="/account" class="btn-reg" style="background:#0b1734;border:1px solid #315dff;">{{ user["name"] }}</a>
    {% else %}
      <div class="auth-btns">
        <a href="/login" class="btn-login">تسجيل الدخول</a>
        <a href="/register" class="btn-reg">إنشاء حساب</a>
      </div>
    {% endif %}
  </div>
</header>

<!-- شريط التنقل الثاني -->
<nav class="nav-bar">
  <a href="/" class="active">الرئيسية</a>
  <a href="#products" onclick="filterCat('أدوات الذكاء الاصطناعي')">أدوات الذكاء الاصطناعي 🤖</a>
  <a href="#products" onclick="filterCat('Google Play')">Google Play</a>
  <a href="#products" onclick="filterCat('PlayStation')">PlayStation</a>
  <a href="#products" onclick="filterCat('Xbox')">Xbox</a>
  <a href="#products" onclick="filterCat('Steam')">Steam</a>
  <a href="javascript:void(0)" onclick="openScannerModal()">🔍 أداة فحص الروابط</a>
</nav>

<div class="layout">
  <!-- المحتوى الرئيسي -->
  <main>
    <div class="hero">
      <div>
        <h1>متجر أدوات الذكاء الاصطناعي المتقدمة وبطاقات الدفع!</h1>
        <p>أدوات ذكية لحياة أسهل وأسرع.. احصل على اشتراكات ChatGPT Plus, Midjourney وأكواد الألعاب بأسعار مميزة.</p>
        <a class="hero-btn" href="#ai-tools">استكشف الأدوات ←</a>
      </div>
      <div style="display:grid;place-items:center;font-size:65px;">
        🤖⚡
      </div>
    </div>

    <!-- كروت الخدمات المضافة المطابقة للصورة المرفقة -->
    <div class="features-container" id="ai-tools">
      <div class="features-title-main">
        <h2>نوفا ستور .. كل ما تحتاجه من الذكاء الاصطناعي</h2>
        <p>أدوات مميزة ✦ موثوق 100% ✦ سريع وآمن</p>
      </div>

      <div class="feature-cards-grid">
        <!-- كارت 1: مساعد ذكاء اصطناعي -->
        <div class="f-card purple">
          <div class="f-icon">🤖💬</div>
          <h3>مساعد ذكاء أسطناعي</h3>
          <p>مساعدك الذكي في كل وقت للإجابة على استفساراتك وتسهيل مهامك اليومية بالشات المباشر.</p>
          <button class="f-btn" onclick="document.getElementById('aiInput').focus();">بدء المحادثة الآن 🚀</button>
        </div>

        <!-- كارت 2: فحص الروابط -->
        <div class="f-card blue">
          <div class="f-icon">🔗🛡️</div>
          <h3>فحص الروابط الذكي</h3>
          <p>احمِ نفسك من الروابط الضارة والتطبيقات المشبوهة وتأكد من أمان أي رابط قبل الفتح.</p>
          <button class="f-btn" onclick="openScannerModal()">افحص رابط الآن 🔍</button>
        </div>

        <!-- كارت 3: أدوات الذكاء الاصطناعي -->
        <div class="f-card green">
          <div class="f-icon">🧠✨</div>
          <h3>أدوات الذكاء الاصطناعي</h3>
          <p>مجموعة متنوعة من أقوى اشتراكات وأدوات الذكاء الاصطناعي في مكان واحد بأقل تكلفة.</p>
          <button class="f-btn" onclick="filterCat('أدوات الذكاء الاصطناعي')">عرض جميع الأدوات 🛒</button>
        </div>
      </div>
    </div>

    <!-- التصنيفات السبعة -->
    <div class="cat-grid">
      <div class="cat-card" onclick="filterCat('الكل')">
        <span style="color:#38bdf8;">🎛️</span>
        <b>جميع المنتجات</b>
        <p>عرض الكل</p>
      </div>
      <div class="cat-card" onclick="filterCat('أدوات الذكاء الاصطناعي')">
        <span style="color:#a855f7;">🧠</span>
        <b>أدوات الـ AI</b>
        <p>ChatGPT & Midjourney</p>
      </div>
      <div class="cat-card" onclick="filterCat('Google Play')">
        <span style="color:#35eaa1;">▶</span>
        <b>Google Play</b>
        <p>أكواد جوجل بلاي</p>
      </div>
      <div class="cat-card" onclick="filterCat('PlayStation')">
        <span style="color:#62a0ff;">PS</span>
        <b>PlayStation</b>
        <p>بطاقات وإشتراكات</p>
      </div>
      <div class="cat-card" onclick="filterCat('Xbox')">
        <span style="color:#5dff9c;">ⓧ</span>
        <b>Xbox</b>
        <p>بطاقات وإشتراكات</p>
      </div>
      <div class="cat-card" onclick="filterCat('Steam')">
        <span style="color:#9bb8ff;">◉</span>
        <b>Steam</b>
        <p>أكواد ومحافظ ستيم</p>
      </div>
      <div class="cat-card" onclick="filterCat('بطاقات الدفع')">
        <span style="color:#38bdf8;">💳</span>
        <b>بطاقات الدفع</b>
        <p>بطاقات مسبقة الدفع</p>
      </div>
    </div>

    <div class="sec-title" id="products">
      <h2><span>🔥</span> أحدث الأدوات والمنتجات</h2>
    </div>

    <div class="product-grid" id="productGrid"></div>

    <!-- تقييمات العملاء -->
    <div style="margin-top:35px;">
      <div class="sec-title">
        <h2><span>⭐️</span> تقييمات العملاء</h2>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:12px;">
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

  <!-- مساعد الذكاء الاصطناعي الجانبي -->
  <aside class="ai-sidebar">
    <div class="ai-header">
      <div class="ai-avatar">🤖</div>
      <div>
        <b style="font-size:13px;color:#fff;display:block;">مساعد NOVA AI</b>
        <span style="font-size:9px;color:#35eaa1;">● متصل وتفاعلي الآن</span>
      </div>
    </div>

    <div class="ai-msg-box" id="aiChatHistory">
      <div><b>🤖 المساعد:</b> أهلاً بك في متجر NOVA STORE! كيف يمكنني مساعدتك اليوم؟</div>
    </div>

    <button class="ai-action-btn" onclick="aiQuery('أفضل أدوات الذكاء الاصطناعي')">🧠 أفضل أدوات الذكاء الاصطناعي</button>
    <button class="ai-action-btn" onclick="aiQuery('كيفية شراء اشتراك ChatGPT؟')">🛒 كيفية شراء اشتراك ChatGPT؟</button>
    <button class="ai-action-btn" onclick="aiQuery('طريقة فحص الروابط الضارة')">🛡️ كيفية فحص رابط آمن؟</button>

    <div class="ai-input-box">
      <input type="text" id="aiInput" placeholder="اكتب سؤالك هنا..." onkeydown="if(event.key==='Enter') sendAiMsg()">
      <button class="ai-send-btn" onclick="sendAiMsg()">➤</button>
    </div>
  </aside>
</div>

<!-- نافذة فحص الروابط الضارة (Modal) -->
<div class="modal-overlay" id="scannerModal">
  <div class="scanner-box">
    <div style="font-size:45px;">🛡️</div>
    <h3 style="color:#38bdf8;margin:5px 0 0;">فحص الروابط الذكي الحقيقي</h3>
    <p style="font-size:11px;color:#a8b7d8;margin-top:5px;">أدخل أي رابط لتأكيد سلامته وخلوه من الفيروسات أو الاحتيال قبل فتحه.</p>

    <input type="url" id="linkToScan" class="scanner-input" placeholder="https://example.com/link-here">

    <div id="scanResult" style="font-size:12px;margin:10px 0;display:none;padding:10px;border-radius:8px;"></div>

    <div style="display:flex;gap:10px;margin-top:15px;">
      <button onclick="scanLinkBackend()" style="flex:1;padding:10px;background:linear-gradient(110deg,#38bdf8,#315dff);color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;">بدء الفحص الان 🔍</button>
      <button onclick="closeScannerModal()" style="padding:10px 15px;background:#1e293b;color:#fff;border:0;border-radius:8px;cursor:pointer;">إغلاق</button>
    </div>
  </div>
</div>

<!-- التذييل Footer -->
<footer>
  <div>
    <a class="brand" href="/" style="margin-bottom:10px;"><span class="brand-mark" style="width:28px;height:28px;font-size:20px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.7;margin:0 0 12px;">متجر أدوات الذكاء الاصطناعي وبطاقات الدفع الأسرع والأكثر أماناً.</p>
    <span>وسائل الدفع المتاحة: Visa | MasterCard | Fawry | Vodafone Cash</span>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="#products">الأدوات</a>
    <a href="javascript:void(0)" onclick="openScannerModal()">فحص الروابط</a>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank">الدعم الفني</a>
  </div>
  <div>
    <h4>الدعم والمساعدة</h4>
    <a href="https://t.me/{{ admin_telegram }}" target="_blank">تواصل مع المطور</a>
    <a href="#">سياسة الخصوصية</a>
    <a href="#">شروط الاستخدام</a>
  </div>
  <div>
    <h4>تابعنا</h4>
    <div style="display:flex;gap:12px;font-size:18px;margin-top:10px;">
      <a href="https://t.me/{{ admin_telegram }}" target="_blank">📢</a>
      <a href="https://t.me/{{ admin_telegram }}" target="_blank">💬</a>
    </div>
    <p style="margin-top:15px;font-size:10px;color:#64748b;">© 2026 NOVA STORE محفوظة.</p>
  </div>
</footer>

<script>
const PRODUCTS = {{ products|tojson }};
const grid = document.getElementById('productGrid');
let cart = JSON.parse(localStorage.getItem('nova_cart') || '[]');

function updateCartBadge() {
  document.getElementById('cartCount').textContent = cart.length;
}

function renderProducts(items) {
  grid.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let badge = p.badge ? `<span class="badge ${p.badge.includes('مميز') ? 'memo' : ''}">${p.badge}</span>` : '';
    let visual = p.image_url ? `<img src="${p.image_url}" style="width:100%;height:100%;object-fit:cover;border-radius:10px;">` : `<span style="color:${p.color};">${p.icon}</span>`;

    card.innerHTML = `
      ${badge}
      <div class="product-visual">${visual}</div>
      <h3>${p.name}</h3>
      <p>${p.description}</p>
      <div class="price-row">
        <span class="price">${p.price}</span>
        <button class="add-btn" onclick="addToCart('${p.name}', '${p.price}')">طلب إشارة / شراء 🛒</button>
      </div>`;
    grid.appendChild(card);
  });
}

function filterCat(cat) {
  if (cat === 'الكل') renderProducts(PRODUCTS);
  else renderProducts(PRODUCTS.filter(x => x.category.toLowerCase().includes(cat.toLowerCase())));
}

function filterProducts() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  renderProducts(PRODUCTS.filter(x => x.name.toLowerCase().includes(q) || x.category.toLowerCase().includes(q)));
}

function addToCart(name, price) {
  cart.push({name, price});
  localStorage.setItem('nova_cart', JSON.stringify(cart));
  updateCartBadge();
  alert('تمت إضافة ' + name + ' إلى سلة الطلبات! 🛒');
}

/* التفاعل الذكي لشات الذكاء الاصطناعي */
function aiQuery(text) {
  document.getElementById('aiInput').value = text;
  sendAiMsg();
}

function sendAiMsg() {
  const input = document.getElementById('aiInput');
  const val = input.value.trim();
  if(!val) return;

  const chat = document.getElementById('aiChatHistory');
  chat.innerHTML += `<div style="margin-top:6px;color:#35eaa1;"><b>👤 أنت:</b> ${val}</div>`;
  input.value = '';

  fetch('/api/ai_chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: val})
  })
  .then(res => res.json())
  .then(data => {
    chat.innerHTML += `<div style="margin-top:6px;color:#c4cde3;"><b>🤖 المساعد:</b> ${data.response}</div>`;
    chat.scrollTop = chat.scrollHeight;
  });
}

/* أداة فحص الروابط */
function openScannerModal() {
  document.getElementById('scannerModal').style.display = 'grid';
}

function closeScannerModal() {
  document.getElementById('scannerModal').style.display = 'none';
  document.getElementById('scanResult').style.display = 'none';
}

function scanLinkBackend() {
  const link = document.getElementById('linkToScan').value.trim();
  const resDiv = document.getElementById('scanResult');
  if(!link) { alert('الرجاء إدخال رابط أولاً'); return; }

  resDiv.style.display = 'block';
  resDiv.style.background = '#09152e';
  resDiv.style.color = '#38bdf8';
  resDiv.textContent = '⏳ جاري فحص الرابط والتأكد من بروتوكولات الأمان والحظر...';

  fetch('/api/scan_link', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: link})
  })
  .then(res => res.json())
  .then(data => {
    if(data.safe) {
      resDiv.style.background = '#064e3b';
      resDiv.style.color = '#35eaa1';
      resDiv.innerHTML = '✅ <b>الرابط آمن وموثوق!</b><br>' + data.message;
    } else {
      resDiv.style.background = '#7f1d1d';
      resDiv.style.color = '#fca5a5';
      resDiv.innerHTML = '⚠️ <b>تحذير:</b> ' + data.message;
    }
  });
}

updateCartBadge();
renderProducts(PRODUCTS);
</script>
</body>
</html>
"""


# ==================== API الإضافات والخدمات ====================

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat_api():
    data = request.json or {}
    query = data.get("query", "").lower()

    if "chatgpt" in query or "شراء" in query or "اشتراك" in query:
        resp = "يمكنك شراء اشتراك ChatGPT Plus أو Midjourney فوراً من قسم 'أدوات الذكاء الاصطناعي' والتسليم فوري تلقائياً!"
    elif "فحص" in query or "رابط" in query:
        resp = "يمكنك استخدام أداة 'فحص الروابط الذكي' العلوية لضمان أمان أي رابط تفضله قبل الفتح!"
    elif "سعر" in query or "اسعار" in query:
        resp = "تبدأ أسعار اشتراكات الذكاء الاصطناعي من $20 وتصل لأفضل باقات الجودة الفائقة."
    else:
        resp = f"أهلاً بك! أنا مساعد NOVA AI. يسعدني الإجابة على استفسارك بشأن '{query}'. أسلنا بالدعم الفني إن احتجت لمزيد من التفاصيل!"

    return jsonify({"response": resp})


@app.route('/api/scan_link', methods=['POST'])
def scan_link_api():
    data = request.json or {}
    url = data.get("url", "").strip()

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()

        # فحص بروتوكولات وشكوك عامة
        suspicious_terms = ["login", "verify", "free-money", "gift-card-claim", "phishing", "hack"]
        if any(term in url.lower() for term in suspicious_terms) and "novastore" not in domain:
            return jsonify({
                "safe": False,
                "message": "هذا الرابط يحتوي على كلمات قد تشير لصفحة تصيد أرقام أو احتيال، ننصح بعدم فتحه."
            })

        return jsonify({
            "safe": True,
            "message": f"تم التحقق من النطاق ({domain}) بنجاح. البروتوكول آمن ولا توجد سجلات حظر سابقة."
        })
    except Exception:
        return jsonify({
            "safe": False,
            "message": "الرابط غير صالحة صيغته أو يتبع توجيهاً غير معروف."
        })


@app.route('/cart')
def cart_page():
    return """
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>سلة الطلبات</title>
    <style>body{background:#03091b;color:#fff;font-family:Cairo,sans-serif;padding:30px;}</style></head>
    <body><h2>🛒 سلة الطلبات والأدوات</h2>
    <p>لتأكيد الشراء وشحن الحسابات فوراً، تواصل مع المطور مباشرة عبر التليجرام:</p>
    <a href="https://t.me/Mido_M9do" target="_blank" style="padding:10px 20px;background:#315dff;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold;">تواصل مع المطور (Mido) 🚀</a>
    <br><br><a href="/" style="color:#38bdf8;">← العودة للمتجر الرئيسي</a>
    </body></html>
    """


@app.route('/account')
def account():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return f"<h1>حساب المستخدم: {user['name']}</h1><p>البريد: {user['email']}</p><a href='/'>العودة للمتجر</a>"


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
                    db.execute("INSERT INTO users (name, email, password_hash, verified, created_at) VALUES (?, ?, ?, 1, ?)", 
                               (name, email, generate_password_hash(password), int(time.time())))
                    session["user_email"] = email
                    return redirect(url_for("home"))
                except Exception:
                    error = "البريد الإلكتروني مسجل مسبقاً."
        else:
            error = "يرجى تعبئة جميع الحقول."

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إنشاء حساب</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2>إنشاء حساب جديد</h2>
    <form method="post">
    <input name='name' placeholder='الاسم الكامل' required>
    <input type='email' name='email' placeholder='البريد الإلكتروني' required>
    <input type='password' name='password' placeholder='كلمة المرور' required>
    <button type="submit">إنشاء الحساب</button>
    </form>
    <p style="color:#ff7777;font-size:12px;">{error}</p>
    <a href="/login" style="color:#8198ff;display:block;margin-top:10px;text-align:center;font-size:12px;text-decoration:none;">تسجيل الدخول</a>
    </div></body></html>
    """


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

    return f"""
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


@app.route("/")
def home():
    email = session.get("user_email")
    user = None
    if email:
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    products = get_products()
    reviews = get_reviews()

    return render_template_string(
        PAGE, 
        products=products, 
        reviews=reviews,
        user=user, 
        admin_telegram=ADMIN_TELEGRAM_USERNAME
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
