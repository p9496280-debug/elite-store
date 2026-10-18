import os
import json
import time
import secrets
import sqlite3
import requests

from pywebpush import webpush, WebPushException
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask,
    render_template_string,
    request,
    session,
    redirect,
    url_for,
    send_from_directory,
    make_response,
    jsonify,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")
ADMIN_VODAFONE_NUMBER = os.environ.get("VODAFONE_NUMBER", "010XXXXXXXX")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "BEl62iUYgUivxIkv69yViEuiBIa45fMplTfdM35C5m_9JffA9R2E1j8bQ2y_6f40_8gR")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "A1B2C3D4E5F6G7H8I9J0")


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
                last_spin_date TEXT,
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
                category TEXT NOT NULL,
                badge TEXT,
                rating TEXT
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                subscription_info TEXT NOT NULL UNIQUE,
                created_at INTEGER NOT NULL
            )
        """)

        admin_user = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, created_at)
                VALUES (?, ?, ?, ?, 999999.0, 1, ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "000000", int(time.time())))
        else:
            db.execute("""
                UPDATE users SET password_hash = ?, verified = 1 WHERE email = ?
            """, (generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL))

        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("VPN Pro", "تصفح الإنترنت بأمان وخصوصية كاملة", 8.00, "$8.00", "VPN-1111", "🛡️", "أدوات", "الأكثر مبيعاَ", "4.8 (2.4K)"),
                ("ترجمة فورية", "ترجمة النصوص والمحادثات بدقة", 5.00, "$5.00", "TRN-2222", "🔤", "أدوات", None, "4.7 (1.8K)"),
                ("ChatGPT Plus", "الوصول إلى GPT-4 بخيارات متقدمة", 12.00, "$12.00", "AI-3333", "🤖", "الذكاء الاصطناعي", "مميز", "4.9 (3.1K)"),
                ("تطبيقات مايكروسوفت", "Word - Excel - PowerPoint", 10.00, "$10.00", "MS-4444", "📊", "أدوات", None, "4.6 (980)"),
                ("YouTube Premium", "بدون إعلانات + تحميل خلفي", 10.00, "$10.00", "YT-5555", "▶️", "ترفيه", None, "4.8 (2.8K)"),
                ("PUBG Mobile", "شحن شدات وبطاقات الألعاب", 15.00, "$15.00", "PUBG-1", "🎮", "ألعاب", "الأكثر شعبية", "4.7"),
                ("Fortnite", "شحن V-Bucks وأزياء نادرة", 20.00, "$20.00", "FORT-2", "🎯", "ألعاب", "ألعاب", "4.6"),
                ("eFootball 2025", "شحن كوينز وحزم الأندية", 15.00, "$15.00", "PES-3", "⚽", "ألعاب", "ألعاب", "4.5"),
                ("Brawl Stars", "شحن جواهر وصناديق", 10.00, "$10.00", "BS-4", "⭐", "ألعاب", "ألعاب", "4.8"),
                ("Minecraft", "شحن عملات Minecoins الأصلية", 12.00, "$12.00", "MC-5", "🧱", "ألعاب", "ألعاب", "4.9"),
                ("Roblox", "شحن Robux أونلاين فوراً", 10.00, "$10.00", "RBX-6", "🕹️", "ألعاب", "ألعاب", "4.6")
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, category, badge, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)


init_db()


def broadcast_push_notification(title, body):
    with get_db() as db:
        subs = db.execute("SELECT subscription_info FROM push_subscriptions").fetchall()
    
    payload = json.dumps({"title": title, "body": body, "icon": "/static/icon.png"})
    for s in subs:
        try:
            sub_info = json.loads(s["subscription_info"])
            webpush(
                subscription_info=sub_info,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": "mailto:admin@novastore.com"}
            )
        except Exception:
            pass


def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in rows]


@app.route("/subscribe_push", methods=["POST"])
def subscribe_push():
    data = request.get_json() or {}
    sub_info = json.dumps(data.get("subscription"))
    email = session.get("user_email")
    if sub_info:
        with get_db() as db:
            db.execute("""
                INSERT OR REPLACE INTO push_subscriptions (user_email, subscription_info, created_at)
                VALUES (?, ?, ?)
            """, (email, sub_info, int(time.time())))
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400


# ==================== قالب المتجر الاحترافي المتطابق مع الصورة تماماً + وضع الصيانة ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | متجرك الرقمي الشامل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#030712;--panel:#071022;--text:#f4f7ff;--blue:#315dff;--purple:#7d2bff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.topbar{min-height:72px;display:flex;align-items:center;gap:15px;padding:0 2.5%;border-bottom:1px solid #14213d;position:sticky;top:0;background:#030712f5;backdrop-filter:blur(16px);z-index:10}
.brand{display:flex;align-items:center;gap:10px;font-size:22px;font-weight:900;text-decoration:none;color:white}.brand b{color:#7d2bff}.brand-mark{width:36px;height:36px;display:grid;place-items:center;font-size:26px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.brand-sub{font-size:7.5px;color:#8fa1c4;letter-spacing:0.5px;display:block;margin-top:-3px}
.search{height:40px;max-width:380px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #1f335f;border-radius:30px;padding:0 16px;background:#060e22}
.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:11.5px}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.lang-btn{background:#09142c;border:1px solid #1f335f;padding:5px 12px;border-radius:20px;font-size:11px;color:#c4cde3;display:flex;align-items:center;gap:5px;cursor:pointer;}
.admin-btn{background:linear-gradient(110deg,#9b37ff,#315dff);color:white;border:0;padding:7px 16px;border-radius:20px;font-weight:bold;font-size:11.5px;text-decoration:none;display:flex;align-items:center;gap:6px;box-shadow:0 4px 15px #315dff44}
.user-profile-badge {display: flex; align-items: center; gap: 8px; background: #071024; border: 1px solid #1f335f; padding: 4px 10px; border-radius: 30px; text-decoration: none;}
.user-avatar { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-weight: bold; color: white; font-size: 11px; }

/* Layout with Sidebar */
.layout-container{display:grid;grid-template-columns:230px minmax(0,1fr) 280px;padding:15px 2.5%;gap:20px}

/* Sidebar */
.sidebar{background:#060e22;border:1px solid #14213d;border-radius:18px;padding:12px;height:max-content;position:sticky;top:85px}
.sidebar-item{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:12px;color:#aab8d0;text-decoration:none;font-size:11.5px;margin-bottom:3px;transition:0.2s;cursor:pointer}
.sidebar-item:hover, .sidebar-item.active{background:linear-gradient(110deg,#315dff22,#7d2bff33);color:#fff;border-right:3px solid #315dff}
.sidebar-item span{font-size:16px}

/* VIP Card Box */
.vip-box{background:linear-gradient(145deg,#0a1736,#110b2c);border:1px solid #7d2bff66;border-radius:15px;padding:15px;text-align:center;margin-top:15px;}
.vip-btn{width:100%;margin-top:10px;padding:8px;background:linear-gradient(110deg,#facc15,#f97316);border:0;border-radius:10px;color:#030712;font-weight:900;font-size:11px;cursor:pointer;}

/* Main Column */
.main-column{min-width:0}

/* Hero Banner */
.hero{border:1px solid #233c70;border-radius:18px;overflow:hidden;display:grid;grid-template-columns:1.2fr 1fr;position:relative;background:radial-gradient(ellipse at 75% 50%,#43148a 0,transparent 55%),linear-gradient(110deg,#050d26,#070d28 65%,#12083b);padding:22px;align-items:center;}
.hero h1{font-size:clamp(16px,1.7vw,24px);line-height:1.5;margin:6px 0 8px;font-weight:800}
.hero p{color:#b6c2db;font-size:10.5px;line-height:1.6;margin:0 0 12px}
.hero-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 18px;border-radius:25px;font-size:11px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;cursor:pointer;}
.trust-bar{display:flex;gap:10px;margin-top:12px;padding-top:10px;border-top:1px solid #1b2f5c;color:#cbd5e1;font-size:9px}

.hero-art{position:relative;height:180px;display:flex;align-items:center;justify-content:center}
.ai-mascot{width:110px;height:110px;background:radial-gradient(circle,#2c8cff,#0d134d);border-radius:50%;display:grid;place-items:center;font-size:50px;box-shadow:0 0 30px #315dffaa;border:2px solid #62a0ff}

/* Categories Grid */
.categories{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;margin:15px 0}
.category{border:1px solid #172d53;border-radius:10px;background:linear-gradient(150deg,#07142c,#050c1a);padding:10px 4px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;cursor:pointer;transition:0.2s;text-decoration:none;color:white;text-align:center}
.category:hover{border-color:#635bff;transform:translateY(-2px)}
.category span{font-size:16px;color:#65baff}
.category b{font-size:9px}
.category small{font-size:7px;color:#8fa1c4}

/* Section Heading */
.section-heading{display:flex;align-items:center;justify-content:space-between;margin:18px 0 10px}
.section-heading h2{font-size:15px;margin:0;display:flex;align-items:center;gap:6px}

/* Product Grid */
.product-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.product-card{border:1px solid #1a3059;background:linear-gradient(150deg,#07142e,#040a1b);border-radius:12px;padding:10px;position:relative;transition:0.2s}
.product-card:hover{border-color:#635bff;transform:translateY(-3px)}

.product-visual{height:85px;border-radius:9px;background:#050d20;display:flex;align-items:center;justify-content:center;position:relative;margin-bottom:8px;font-size:32px;border:1px solid rgba(255,255,255,0.06);cursor:pointer;}
.badge-tag{position:absolute;top:7px;right:7px;background:#ff3b3b;color:white;font-size:8px;padding:2px 6px;border-radius:5px;font-weight:bold;z-index:2}
.badge-tag.memo{background:#315dff}
.badge-tag.hot{background:#00c853}
.product-card h3{font-size:11.5px;margin:4px 0 2px;cursor:pointer;}
.product-card p{font-size:9px;color:#8fa1c4;margin:0 0 8px}
.price-row{display:flex;align-items:center;justify-content:space-between;margin-top:6px}
.price{font-size:12.5px;font-weight:800;color:#fff}
.add-btn{padding:5px 9px;border:0;border-radius:7px;background:linear-gradient(100deg,#933aff,#315dff);font-size:9.5px;font-weight:700;color:white;cursor:pointer}

/* Right Panel (User Card & Quick Services) */
.right-panel{display:grid;gap:15px;height:max-content;position:sticky;top:85px}
.user-dash-card{background:linear-gradient(145deg,#071022,#0b193d);border:1px solid #233c70;border-radius:18px;padding:15px;}
.dash-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:12px}
.stat-box{background:#040c1e;border:1px solid #172d53;border-radius:10px;padding:8px;text-align:center;font-size:10px;color:#9bb2d9}
.stat-box b{display:block;font-size:13px;color:#35eaa1;margin-top:2px}

.quick-box{background:linear-gradient(145deg,#071022,#0b193d);border:1px solid #233c70;border-radius:18px;padding:15px;}
.quick-btn{display:flex;align-items:center;gap:10px;width:100%;background:#040c1e;border:1px solid #172d53;padding:8px 12px;border-radius:10px;color:white;font-size:10px;margin-bottom:6px;cursor:pointer;text-decoration:none;transition:0.2s}
.quick-btn:hover{border-color:#315dff;background:#081738}

/* Toast Message for Maintenance */
.maintenance-toast{position:fixed;bottom:25px;left:50%;transform:translateX(-50%) translateY(100px);background:linear-gradient(135deg,#071024,#160b2e);border:2px solid #ff9100;color:white;padding:14px 24px;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,0.8);z-index:1000;transition:0.3s;display:flex;align-items:center;gap:12px;font-size:13px;opacity:0;}
.maintenance-toast.show{transform:translateX(-50%) translateY(0);opacity:1;}

/* Footer */
footer{border-top:1px solid #17284a;padding:22px 3%;display:grid;grid-template-columns:1.4fr 1fr 1fr 1.3fr;gap:18px;color:#9fb0d2;font-size:10.5px;margin-top:35px;background:#02050f}
footer h4{color:#f4f7ff;margin:0 0 10px;font-size:11.5px}footer a{display:block;margin:4px 0;color:#9fb0d2;text-decoration:none}
</style>
</head>
<body>
<div class="maintenance-toast" id="maintToast">
  <span style="font-size:22px;">🛠️</span>
  <div>
    <b>عذراً عزيزي المستخدم!</b>
    <div style="font-size:11px;color:#cbd5e1;margin-top:2px;">التطبيق في حالة صيانة وتحديث حالياً لتقديم أفضل تجربة. 🚀</div>
  </div>
</div>

<header class="topbar">
  <a class="brand" href="/">
    <span class="brand-mark">N</span>
    <div>
      <span>NOVA <b>STORE</b></span>
      <span class="brand-sub">More Apps &nbsp;·&nbsp; More Fun &nbsp;·&nbsp; More Freedom</span>
    </div>
  </a>
  <label class="search"><span>⌕</span><input id="searchInput" type="search" placeholder="ابحث عن أي تطبيق أو خدمة..." onfocus="showMaintenance()"></label>
  <div class="header-actions">
    <button class="lang-btn" onclick="showMaintenance()">🌐 AR ▾</button>
    {% if is_admin %}
      <a href="/admin" class="admin-btn">⚙️ لوحة التحكم</a>
    {% endif %}
    {% if user %}
      <a href="/account" class="user-profile-badge">
        <div class="user-avatar">{{ user["name"][:1] }}</div>
        <div>
          <span style="font-size:10px;font-weight:bold;display:block;">{{ user["name"] }}</span>
          <span style="font-size:8px;color:#35eaa1;">{{ user["balance"] }} جـ</span>
        </div>
      </a>
    {% else %}
      <a href="/login" style="color:#d8e2ff;text-decoration:none;font-size:11px;">تسجيل الدخول</a>
      <a href="/register" style="padding:6px 12px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:11.5px;">إنشاء حساب</a>
    {% endif %}
  </div> 
</header>

<div class="layout-container">
  <!-- Sidebar -->
  <aside class="sidebar">
    <a class="sidebar-item active" onclick="showMaintenance()"><span>🏠</span> الرئيسية</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>📱</span> جميع التطبيقات</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🎮</span> الألعاب</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🤖</span> الذكاء الاصطناعي</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🔧</span> أدوات احترافية</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🌐</span> خدمات الإنترنت</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>💬</span> التواصل الاجتماعي</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🎬</span> تعديل الصور والفيديو</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>💳</span> المال والدفع</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🎁</span> الترفيه</a>
    <hr style="border:0;border-top:1px solid #14213d;margin:8px 0;">
    <a class="sidebar-item" onclick="showMaintenance()"><span>⭐</span> المميزين</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>❤️</span> المفضلة</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>🎧</span> الدعم الفني</a>
    <a class="sidebar-item" onclick="showMaintenance()"><span>⚙️</span> الإعدادات</a>

    <div class="vip-box">
      <div style="font-size:20px;">👑</div>
      <b style="font-size:10.5px;display:block;margin:4px 0;color:#facc15;">احصل على عضوية VIP</b>
      <p style="font-size:8px;color:#9bb2d9;margin:0 0 6px;">مزايا أكثر .. أسعار أفضل</p>
      <button class="vip-btn" onclick="showMaintenance()">تفعيل الآن</button>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="main-column">
    <div class="hero">
      <div>
        <span style="color:#35eaa1;font-size:10px;font-weight:bold;background:rgba(53,234,161,0.1);padding:3px 10px;border-radius:10px;border:1px solid rgba(53,234,161,0.2)">🚀 أفضل التطبيقات</span>
        <h1>كل ما تحتاجه في مكان واحد! تطبيقات، ألعاب، أدوات، وخدمات مميزة.</h1>
        <p>تطبيقات رقمية آمنة وسريعة. شحن الألعاب، أكواد المتاجر العالمية والمزيد من الخدمات الحصرية.</p>
        <a class="hero-btn" onclick="showMaintenance()">تصفح الآن →</a>
        <div class="trust-bar"><span>⚡ تحميل سريع</span><span>🛡️ آمن 100%</span><span>🎧 دعم فني 24/7</span></div>
      </div>
      <div class="hero-art">
        <div class="ai-mascot" onclick="showMaintenance()">🤖</div>
      </div>
    </div>

    <div class="categories">
      <a onclick="showMaintenance()" class="category"><span>🎁</span><b>بطاقات الهدايا</b><small>شحن الألعاب</small></a>
      <a onclick="showMaintenance()" class="category"><span style="color:#35eaa1;">🎮</span><b>الألعاب</b><small>أحدث الألعاب</small></a>
      <a onclick="showMaintenance()" class="category"><span style="color:#62a0ff;">🤖</span><b>الذكاء الاصطناعي</b><small>أدوات ذكية</small></a>
      <a onclick="showMaintenance()" class="category"><span style="color:#ffc107;">🔧</span><b>أدوات احترافية</b><small>أدوات قوية</small></a>
      <a onclick="showMaintenance()" class="category"><span style="color:#9bb8ff;">🌐</span><b>خدمات الإنترنت</b><small>VPN ومتصفحات</small></a>
      <a onclick="showMaintenance()" class="category"><span style="color:#bc5bff;">💬</span><b>تواصل اجتماعي</b><small>حماية حسابات</small></a>
      <a onclick="showMaintenance()" class="category"><span style="color:#ff3b3b;">▶️</span><b>الترفيه</b><small>أفلام وموسيقى</small></a>
    </div>

    <div class="section-heading" id="products">
      <h2><span>🔥</span> أحدث الإضافات</h2>
      <a onclick="showMaintenance()" style="font-size:10px;color:#8198ff;cursor:pointer;">عرض الكل ←</a>
    </div>

    <div class="product-grid" id="productGrid"></div>

    <div class="section-heading" id="games" style="margin-top:25px;">
      <h2><span>🎮</span> الأكثر طلباً</h2>
      <a onclick="showMaintenance()" style="font-size:10px;color:#8198ff;cursor:pointer;">عرض الكل ←</a>
    </div>

    <div class="product-grid" id="gamesGrid"></div>
  </main>

  <!-- Right Panel -->
  <aside class="right-panel">
    <div class="user-dash-card">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:38px;height:38px;border-radius:50%;background:radial-gradient(circle,#2c8cff,#0d134d);display:grid;place-items:center;font-size:18px;border:1px solid #466bff">🤖</div>
        <div>
          <h3 style="margin:0 0 2px;font-size:11.5px;color:#f4f7ff;">مرحباً بك</h3>
          <span style="font-size:8px;color:#35eaa1;">المستخدم المميز 👑</span>
        </div>
      </div>
      <div class="dash-stats">
        <div class="stat-box">نجومك <b>1,250</b></div>
        <div class="stat-box">المستوى <b>مميز</b></div>
        <div class="stat-box">الأصدقاء <b>12</b></div>
        <div class="stat-box">الطلبات <b>8</b></div>
      </div>
      <button onclick="showMaintenance()" style="width:100%;margin-top:12px;padding:8px;background:linear-gradient(110deg,#315dff,#7d2bff);border:0;border-radius:10px;color:white;font-weight:bold;font-size:10.5px;cursor:pointer;">انضم إلى قناتنا ✈️</button>
    </div>

    <div class="quick-box">
      <h4 style="margin:0 0 8px;font-size:11px;color:#f4f7ff;">خدمات سريعة ⚡</h4>
      <a onclick="showMaintenance()" class="quick-btn"><span>🛡️</span> تفعيل VPN</a>
      <a onclick="showMaintenance()" class="quick-btn"><span>💳</span> شحن الرصيد</a>
      <a onclick="showMaintenance()" class="quick-btn"><span>🔒</span> تغيير كلمة المرور</a>
      <a onclick="showMaintenance()" class="quick-btn"><span>🎧</span> تواصل معنا</a>
      <a onclick="showMaintenance()" class="quick-btn"><span>❤️</span> المفضلة</a>
      <a onclick="showMaintenance()" class="quick-btn"><span>📋</span> سجل الطلبات</a>
    </div>
  </aside>
</div>

<footer id="footer">
  <div>
    <a class="brand" href="/" style="margin-bottom:8px;"><span class="brand-mark" style="width:24px;height:24px;font-size:18px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.6;margin:0;font-size:9.5px;">عالمك الرقمي الشامل</p>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a onclick="showMaintenance()" style="cursor:pointer;">الرئيسية</a>
    <a onclick="showMaintenance()" style="cursor:pointer;">التطبيقات</a>
    <a onclick="showMaintenance()" style="cursor:pointer;">الألعاب</a>
  </div>
  <div>
    <h4>الدعم والمساعدة</h4>
    <a onclick="showMaintenance()" style="cursor:pointer;">مركز المساعدة</a>
    <a onclick="showMaintenance()" style="cursor:pointer;">سياسة الخصوصية</a>
    <a onclick="showMaintenance()" style="cursor:pointer;">تواصل معنا</a>
  </div>
  <div>
    <h4>وسائل الدفع المتاحة</h4>
    <div style="font-size:16px;margin-top:6px;letter-spacing:5px;">💳 🅿 🟡 🅕</div>
    <small style="display:block;margin-top:10px;color:#788db8;font-size:8px;">2026 NOVA STORE جميع الحقوق محفوظة</small>
  </div>
</footer>

<script>
function showMaintenance() {
  const toast = document.getElementById('maintToast');
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');
const gamesGrid = document.getElementById('gamesGrid');

function renderProducts() {
  productGrid.innerHTML = '';
  gamesGrid.innerHTML = '';
  
  PRODUCTS.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let badgeClass = p.badge === 'مميز' ? 'memo' : (p.badge === 'الأكثر مبيعاَ' || p.badge === 'الأكثر شعبية' ? 'hot' : '');
    let badgeHtml = p.badge ? `<span class="badge-tag ${badgeClass}">${p.badge}</span>` : '';
    
    card.innerHTML = `
      ${badgeHtml}
      <div class="product-visual" onclick="showMaintenance()">${p.icon}</div>
      <h3 style="color:#fff;" onclick="showMaintenance()">${p.name}</h3>
      <p>${p.description}</p>
      <div style="font-size:9px;color:#facc15;margin-bottom:6px;">⭐ ${p.rating}</div>
      <div class="price-row">
        <span class="price">${p.price}</span>
        <button class="add-btn" onclick="showMaintenance()">${p.category === 'ألعاب' ? 'تثبيت الآن' : 'شراء الآن'}</button>
      </div>`;

    if(p.category === 'ألعاب') {
      gamesGrid.appendChild(card);
    } else {
      productGrid.appendChild(card);
    }
  });
}
renderProducts();
</script>
</body>
</html>
"""

# ==================== صفحة لوحة المطور ====================
ADMIN_PANEL_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة التحكم | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#030712;color:white;font-family:'Cairo',sans-serif;padding:30px}
.box{background:#071024;border:1px solid #315dff;border-radius:15px;padding:25px;max-width:550px;margin:20px auto;}
input, textarea {width:100%;padding:12px;margin:10px 0;background:#030712;border:1px solid #1f335f;border-radius:9px;color:white;box-sizing:border-box;}
button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;}
</style>
</head>
<body>
<div style="max-width:550px;margin:auto;display:flex;justify-content:space-between;align-items:center;">
  <h2>⚙️ لوحة تحكم المطور</h2>
  <a href="/" style="color:#8198ff;text-decoration:none;">← العودة للمتجر</a>
</div>

<div class="box">
  <h3>➕ إضافة تطبيق أو لعبة جديدة</h3>
  <form method="POST" action="/admin/add_product">
    <input name="name" placeholder="اسم التطبيق أو اللعبة (مثال: VPN Pro)" required>
    <input name="description" placeholder="الوصف المختصر" required>
    <input type="number" step="0.01" name="price_val" placeholder="السعر الرقمي (مثال: 8)" required>
    <input name="price" placeholder="نص السعر (مثال: $8.00)" required>
    <input name="code" placeholder="الكود الرقمي" required>
    <input name="icon" placeholder="رمز الأيقونة (مثال: 🛡️ أو 🎮)" required>
    <input name="category" placeholder="القسم (أدوات أو ألعاب)" required>
    <input name="badge" placeholder="الشارة (مثال: مميز أو الأكثر مبيعاَ)">
    <input name="rating" placeholder="التقييم (مثال: 4.8)" required>
    <button type="submit">إضافة للمتجر</button>
  </form>
</div>
</body>
</html>
"""

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
    rating = request.form.get("rating")

    with get_db() as db:
        db.execute("""
            INSERT INTO products (name, description, price_val, price, code, icon, category, badge, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price_val, price, code, icon, category, badge, rating))

    return redirect(url_for("admin_panel"))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
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
                    db.execute("""
                        INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, created_at)
                        VALUES (?, ?, ?, ?, 0.0, 1, ?)
                    """, (name, email, generate_password_hash(password), telegram_id, int(time.time())))
                    session["user_email"] = email
                    return redirect(url_for("account"))
    return render_template_string("""
    <body style="background:#030712;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;">
      <form method="post" style="background:#071024;padding:25px;border:1px solid #315dff;border-radius:15px;width:320px;">
        <h2>إنشاء حساب</h2>
        <input name="name" placeholder="الاسم" required style="width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1f335f;color:white;">
        <input type="email" name="email" placeholder="البريد الإلكتروني" required style="width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1f335f;color:white;">
        <input type="password" name="password" placeholder="كلمة المرور" required style="width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1f335f;color:white;">
        <input name="telegram_id" placeholder="Telegram Chat ID" required style="width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1f335f;color:white;">
        <button style="width:100%;padding:12px;background:#315dff;color:white;border:0;border-radius:8px;font-weight:bold;">تسجيل</button>
        {% if error %}<p style="color:#ff7777;">{{ error }}</p>{% endif %}
      </form>
    </body>
    """, error=error)


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
    return render_template_string("""
    <body style="background:#030712;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;">
      <form method="post" style="background:#071024;padding:25px;border:1px solid #315dff;border-radius:15px;width:320px;">
        <h2>تسجيل الدخول</h2>
        <input type="email" name="email" placeholder="البريد الإلكتروني" required style="width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1f335f;color:white;">
        <input type="password" name="password" placeholder="كلمة المرور" required style="width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1f335f;color:white;">
        <button style="width:100%;padding:12px;background:#315dff;color:white;border:0;border-radius:8px;font-weight:bold;">دخول</button>
        {% if error %}<p style="color:#ff7777;">{{ error }}</p>{% endif %}
      </form>
    </body>
    """, error=error)


@app.route("/account")
def account():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return render_template_string("""
    <body style="background:#030712;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;">
      <div style="background:#071024;padding:30px;border:1px solid #315dff;border-radius:15px;text-align:center;width:350px;">
        <h2>{{ user["name"] }}</h2>
        <p style="color:#35eaa1;font-weight:bold;">الرصيد: {{ user["balance"] }} جنيه</p>
        <a href="/" style="color:#9db4ff;display:block;margin:10px;text-decoration:none;">الرئيسية</a>
        <a href="/logout" style="color:#ff7777;display:block;margin:10px;text-decoration:none;">تسجيل الخروج</a>
      </div>
    </body>
    """, user=user)


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
    return render_template_string(PAGE, products=products, user=user, is_admin=is_admin, vapid_public_key=VAPID_PUBLIC_KEY)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
