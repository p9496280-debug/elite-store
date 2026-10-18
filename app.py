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
    make_response,
    jsonify,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")
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
                ("كود جوجل بلاي (10$)", "الولايات المتحدة", 10.00, "$10.00", "GPLAY-9876-XXXX", "▶", "بطاقات الألعاب", "#35eaa1", "الأكثر مبيعاً"),
                ("كود بلايستيشن (20$)", "الولايات المتحدة", 20.00, "$20.00", "PSN-5432-XXXX", "PS", "بطاقات الألعاب", "#62a0ff", "مميز"),
                ("كود إكس بوكس (25$)", "الولايات المتحدة", 25.00, "$25.00", "XBOX-3344-XXXX", "ⓧ", "بطاقات الألعاب", "#5dff9c", None),
                ("كود ستيم (20$)", "الولايات المتحدة", 20.00, "$20.00", "STEAM-1122-XXXX", "◉", "بطاقات الألعاب", "#9bb8ff", None),
                ("كود آيتونز (15$)", "الولايات المتحدة", 15.00, "$15.00", "ITUNES-7788-XXXX", "", "بطاقات الهدايا", "#ffc107", None),
                ("بطاقة دفع مسبقة (50$)", "عالمية", 50.00, "$50.00", "VISA-5544-XXXX", "💳", "بطاقات الدفع", "#ff3b3b", "شائع"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, category, color, badge)
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


# ==================== صفحة المتجر الرئيسية الأصلية تماماً + وضع الصيانة ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | متجرك الرقمي</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
:root{--bg:#03091b;--panel:#07132c;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff;--border:#1b315c}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.topbar{min-height:78px;display:flex;align-items:center;gap:20px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:10}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white}.brand b{color:#754bff}.brand-mark{width:39px;height:39px;display:grid;place-items:center;font-size:33px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.search{height:44px;max-width:420px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:30px;padding:0 17px;background:#09132b}
.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:13px}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.user-profile-badge {display: flex; align-items: center; gap: 10px; background: #0b1734; border: 1px solid #263d70; padding: 6px 14px; border-radius: 30px; text-decoration: none;}
.user-avatar { width: 34px; height: 34px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-weight: bold; color: white; }
.nav{min-height:46px;padding:0 4%;display:flex;align-items:center;gap:28px;border-bottom:1px solid #18284a;font-size:13px}
.nav a{color:#c4cde3;text-decoration:none;cursor:pointer}.nav a:hover{color:#7f9dff}
.admin-badge { background: #570f0f; color: #ff7777; border: 1px solid #ff5555; padding: 6px 14px; border-radius: 12px; font-weight: bold; text-decoration:none;}

.layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:22px;padding:22px 4%}
.main-column{min-width:0}

/* Hero Section */
.hero{min-height:290px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b);padding:25px;align-items:center;}
.hero h1{font-size:clamp(20px,2vw,28px);line-height:1.6;margin:0 0 10px;font-weight:800}
.hero p{color:#c4cce2;font-size:12px;line-height:1.8;margin:0 0 15px}
.hero-btn{display:inline-flex;align-items:center;gap:10px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;cursor:pointer;}
.trust-row{display:flex;gap:15px;margin-top:15px;color:#dce5ff;font-size:10px}
.hero-art{position:relative;height:240px;display:flex;align-items:center;justify-content:center}
.gift-card{position:absolute;width:95px;height:135px;border:1px solid #66bfff;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;font-size:11px;background:linear-gradient(145deg,#063c9e,#09132e);box-shadow:0 0 20px #168dff55;cursor:pointer;}
.gift-card.google{right:45%;transform:rotate(-12deg);background:linear-gradient(145deg,#113e83,#11153c);border-color:#35eaa1}
.gift-card.playstation{right:28%;top:20px;transform:rotate(6deg);background:linear-gradient(145deg,#0759dd,#111342)}
.gift-card.steam{right:10%;top:30px;transform:rotate(12deg);background:linear-gradient(125deg,#122b54,#050c1c)}
.gift-card.xbox{right:0;top:70px;transform:rotate(18deg);background:linear-gradient(145deg,#076b38,#09271f);width:85px;height:120px}

/* Categories Grid */
.categories{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;margin:20px 0}
.category{border:1px solid #172d53;border-radius:12px;background:linear-gradient(150deg,#07152e,#050d20);padding:14px 8px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;cursor:pointer;transition:0.2s}
.category:hover{border-color:#5a54ff;transform:translateY(-2px)}
.category span{font-size:22px;color:#65baff}
.category b{font-size:11px}
.category small{font-size:9px;color:#9eafd0}

/* Products Section */
.section-heading{display:flex;align-items:center;justify-content:space-between;margin:25px 0 12px}
.section-heading h2{font-size:18px;margin:0;display:flex;align-items:center;gap:8px}
.product-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:14px;padding:12px;position:relative;transition:0.2s}
.product-card:hover{border-color:#5c52ff;transform:translateY(-3px)}
.product-visual{height:100px;border-radius:10px;background:radial-gradient(circle at 50% 20%,#1b3159,transparent 70%),#07142c;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;margin-bottom:10px;cursor:pointer;}
.badge-tag{position:absolute;top:8px;right:8px;background:#ff3b3b;color:white;font-size:9px;padding:2px 8px;border-radius:6px;font-weight:bold}
.badge-tag.memo{background:#315dff}
.product-card h3{font-size:13px;margin:5px 0 2px;cursor:pointer;}
.product-card p{font-size:10px;color:#8fa1c4;margin:0 0 10px}
.price-row{display:flex;align-items:center;justify-content:space-between;margin-top:8px}
.price{font-size:14px;font-weight:800;color:#fff}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;cursor:pointer}

/* AI Assistant Panel */
.ai-panel{border:1px solid #344b88;border-radius:18px;padding:16px;height:max-content;background:linear-gradient(155deg,#081735,#060d22);position:sticky;top:95px}
.ai-heading{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.bot-avatar{width:46px;height:46px;display:grid;place-items:center;border-radius:50%;font-size:22px;background:radial-gradient(circle at 35% 25%,#2c8cff,#11175a 65%);border:1px solid #466bff}
.ai-message{border:1px solid #1e3c75;border-radius:12px;background:#0a1b42;padding:12px;font-size:11px;line-height:1.7;color:#c4d1ed}
.ai-quick{display:grid;gap:7px;margin-top:12px}
.ai-quick button{border:1px solid #244b91;border-radius:9px;background:#0b2050;padding:8px;font-size:10px;text-align:right;color:#fff;cursor:pointer}
.ai-input{display:flex;gap:6px;align-items:center;border:1px solid #294b91;border-radius:25px;padding:4px 10px;margin-top:15px;background:#081a3c}
.ai-input input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:11px}
.ai-input button{width:28px;height:28px;border:0;border-radius:50%;background:#4d55ff;color:white;cursor:pointer}

/* Toast Maintenance */
.maintenance-toast{position:fixed;bottom:25px;left:50%;transform:translateX(-50%) translateY(100px);background:linear-gradient(135deg,#07132c,#1b0b3d);border:2px solid #ff9100;color:white;padding:14px 26px;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,0.8);z-index:1000;transition:0.3s;display:flex;align-items:center;gap:12px;font-size:13px;opacity:0;}
.maintenance-toast.show{transform:translateX(-50%) translateY(0);opacity:1;}

/* Footer */
footer{border-top:1px solid #192b4e;padding:25px 4%;display:grid;grid-template-columns:1.5fr 1fr 1fr 1.4fr;gap:20px;color:#aab9d8;font-size:11px;margin-top:40px;background:#030714}
footer h4{color:#f4f7ff;margin:0 0 10px;font-size:12px}footer a{display:block;margin:5px 0;color:#aab8d0;text-decoration:none;cursor:pointer}
</style>
</head>
<body>
<div class="maintenance-toast" id="maintToast">
  <span style="font-size:22px;">🛠️</span>
  <div>
    <b>عذراً عزيزي المستخدم!</b>
    <div style="font-size:11px;color:#cbd5e1;margin-top:2px;">المتجر وأقسامه في حالة صيانة وتحديث حالياً. عودوا قريباً!</div>
  </div>
</div>

<header class="topbar">
  <a class="brand" href="/"><span class="brand-mark">N</span><span>NOVA <b>STORE</b></span></a>
  <label class="search"><span>⌕</span><input id="searchInput" type="search" placeholder="ابحث عن أي منتج..." onfocus="showMaintenance()"></label>
  <div class="header-actions">
    {% if is_admin %}
      <a href="/admin" class="admin-badge">⚙️ لوحة المطور</a>
    {% endif %}
    {% if user %}
      <a href="/account" class="user-profile-badge">
        <div class="user-avatar">{{ user["name"][:1] }}</div>
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
  <a href="/" style="color:#7f9dff;font-weight:bold;">الرئيسية</a>
  <a href="/spin" style="color:#ffc107;font-weight:bold;">🎡 عجلة الحظ (لفة يومياً)</a>
  <a onclick="showMaintenance()">المنتجات</a>
  <a onclick="showMaintenance()">من نحن</a>
  <a onclick="showMaintenance()">الدعم</a>
</nav>

<main class="layout">
  <section class="main-column">
    <div class="hero">
      <div>
        <span style="color:#bca0ff;font-size:11px;font-weight:bold;">عالمك الرقمي في مكان واحد</span>
        <h1>كل ما تحتاجه من بطاقات الدفع وأكواد الألعاب في مكان واحد!</h1>
        <p>بطاقات رقمية آمنة وسريعة. شحن الألعاب، أكواد المتاجر العالمية والمزيد من المتجات الرقمية المميزة.</p>
        <a class="hero-btn" onclick="showMaintenance()">تسوق الآن ←</a>
        <div class="trust-row"><span>♧ دفع آمن 100%</span><span>◷ تسليم سريع</span><span>دعم على مدار الساعة</span></div>
      </div>
      <div class="hero-art">
        <div class="gift-card google" onclick="showMaintenance()"><span style="color:#35eaa1;font-size:26px;">▶</span><b>Google Play</b></div>
        <div class="gift-card playstation" onclick="showMaintenance()"><span style="color:#62a0ff;font-size:22px;">PSN</span><b>PlayStation</b></div>
        <div class="gift-card steam" onclick="showMaintenance()"><span style="color:#9bb8ff;font-size:22px;">◉</span><b>STEAM</b></div>
        <div class="gift-card xbox" onclick="showMaintenance()"><span style="color:#5dff9c;font-size:22px;">ⓧ</span><b>Xbox</b></div>
      </div>
    </div>

    <div class="categories">
      <div class="category" onclick="showMaintenance()"><span>▦</span><b>المنتجات الرقمية</b><small>المزيد من الخدمات</small></div>
      <div class="category" onclick="showMaintenance()"><span style="color:#35eaa1;">▶</span><b>Google Play</b><small>أكواد جوجل بلاي</small></div>
      <div class="category" onclick="showMaintenance()"><span style="color:#62a0ff;">▤</span><b>PlayStation</b><small>بطاقات وإاشتراكات</small></div>
      <div class="category" onclick="showMaintenance()"><span style="color:#5dff9c;">ⓧ</span><b>Xbox</b><small>بطاقات وإاشتراكات</small></div>
      <div class="category" onclick="showMaintenance()"><span style="color:#9bb8ff;">◉</span><b>Steam</b><small>أكواد ومحافظ ستيم</small></div>
      <div class="category" onclick="showMaintenance()"><span style="color:#ffc107;">💳</span><b>بطاقات الدفع</b><small>بطاقات مسبقة الدفع</small></div>
      <div class="category" onclick="showMaintenance()"><span style="color:#bc5bff;">🎁</span><b>بطاقات الهدايا</b><small>هدايا رقمية مميزة</small></div>
    </div>

    <div class="section-heading" id="products">
      <h2><span>🔥</span> أحدث المنتجات</h2>
      <a onclick="showMaintenance()" style="font-size:11px;color:#8198ff;cursor:pointer;">عرض الكل ←</a>
    </div>

    <div class="product-grid" id="productGrid"></div>
  </section>

  <aside class="ai-panel">
    <div class="ai-heading">
      <div class="bot-avatar">✦</div>
      <div>
        <h3 style="margin:0 0 2px;font-size:13px;color:#a99bff;">مساعد NOVA AI</h3>
        <span style="font-size:9px;color:#2fe19a;display:flex;align-items:center;gap:4px;"><i style="width:5px;height:5px;background:#2fe19a;border-radius:50%;display:inline-block;"></i> متصل الآن</span>
      </div>
    </div>
    <div class="ai-message">
      <b>مرحباً! 👋</b>
      <p style="margin:4px 0 0;">أنا مساعد NOVA AI. يمكنني مساعدتك في البحث عن المنتجات والإجابة على استفساراتك.</p>
    </div>
    <div class="ai-quick">
      <button onclick="showMaintenance()">📦 عرض المنتجات المتاحة</button>
      <button onclick="showMaintenance()">💳 مساعدة في الشراء</button>
      <button onclick="showMaintenance()">📞 معلومات عن المتجر</button>
    </div>
    <div class="ai-input">
      <input placeholder="اكتب رسالتك هنا..." autocomplete="off" onfocus="showMaintenance()">
      <button onclick="showMaintenance()">➤</button>
    </div>
  </aside>
</main>

<footer id="footer">
  <div>
    <a class="brand" href="/" style="margin-bottom:10px;"><span class="brand-mark" style="width:28px;height:28px;font-size:22px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.7;margin:0;">متجرك الرقمي الأول لبطاقات الدفع وأكواد الألعاب.</p>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a onclick="showMaintenance()">الرئيسية</a>
    <a href="/spin">عجلة الحظ</a>
    <a onclick="showMaintenance()">المنتجات</a>
  </div>
  <div>
    <h4>الدعم والمساعدة</h4>
    <a onclick="showMaintenance()">مركز المساعدة</a>
    <a onclick="showMaintenance()">سياسة الخصوصية</a>
    <a onclick="showMaintenance()">تواصل معنا</a>
  </div>
  <div>
    <h4>وسائل الدفع المتاحة</h4>
    <div style="font-size:22px;margin-top:10px;letter-spacing:8px;">💳 🅿 🟡 🅕</div>
    <small style="display:block;margin-top:15px;color:#8194ba;">© 2026 NOVA STORE جميع الحقوق محفوظة</small>
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
function renderProducts() {
  productGrid.innerHTML = '';
  PRODUCTS.forEach(p => {
    const card = document.createElement('article');
    card.className = 'product-card';
    let badgeHtml = p.badge ? `<span class="badge-tag ${p.badge==='مميز'?'memo':''}" >${p.badge}</span>` : '';
    card.innerHTML = `
      ${badgeHtml}
      <div class="product-visual" style="color:${p.color};" onclick="showMaintenance()">${p.icon}</div>
      <h3 style="color:#fff;" onclick="showMaintenance()">${p.name}</h3>
      <p onclick="showMaintenance()">${p.description}</p>
      <div class="price-row">
        <span class="price">${p.price}</span>
        <button class="add-btn" onclick="showMaintenance()">＋ أضف للسلة</button>
      </div>`;
    productGrid.appendChild(card);
  });
}
renderProducts();

if ('serviceWorker' in navigator && 'PushManager' in window) {
  navigator.serviceWorker.register('/sw.js').then(reg => {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: '{{ vapid_public_key }}' }).then(sub => {
          fetch('/subscribe_push', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ subscription: sub }) });
        });
      }
    });
  });
}
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
<title>لوحة المطور | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;padding:30px}
.box{background:#07132c;border:1px solid #315dff;border-radius:15px;padding:25px;max-width:550px;margin:20px auto;}
input, textarea {width:100%;padding:12px;margin:10px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;}
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
    <input name="name" placeholder="اسم المنتج (مثال: كود جوجل بلاي)" required>
    <input name="description" placeholder="الوصف (مثال: الولايات المتحدة)" required>
    <input type="number" step="0.01" name="price_val" placeholder="السعر (مثال: 10)" required>
    <input name="price" placeholder="نص السعر (مثال: $10.00)" required>
    <input name="code" placeholder="الكود الرقمي" required>
    <input name="icon" placeholder="الأيقونة (مثال: ▶)" required>
    <input name="category" placeholder="القسم" required>
    <input name="badge" placeholder="الشارة (مثال: الأكثر مبيعاً أو فارغ)">
    <button type="submit">إضافة المنتج للمتجر</button>
  </form>
</div>

<div class="box">
  <h3>📢 إرسال إشعار عام لهواتف المستخدمين</h3>
  <form method="POST" action="/admin/send_announcement">
    <input name="title" placeholder="عنوان الإشعار (مثال: عروض حصرية!)" required>
    <textarea name="message" placeholder="اكتب تفاصيل الإشعار هنا..." rows="3" required></textarea>
    <button type="submit" style="background:linear-gradient(110deg,#ff9100,#ff3b3b);">إرسال الإشعار الآن</button>
  </form>
</div>
</body>
</html>
"""

# ==================== صفحة عجلة الحظ النيون ====================
SPIN_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>عجلة الحظ اليومية | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at center,#0f1c3f 0%,#03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;}
.wheel-container{position:relative;width:340px;height:340px;display:flex;align-items:center;justify-content:center;margin:20px 0;}
.wheel-outer-ring{position:absolute;inset:-12px;border-radius:50%;border:4px solid #315dff;box-shadow:0 0 35px #8d38ffaa;pointer-events:none;z-index:2;}
.pointer{position:absolute;top:-22px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:16px solid transparent;border-right:16px solid transparent;border-top:28px solid #ff3b3b;z-index:10;}
canvas{width:100%;height:100%;border-radius:50%;transition: transform 5s cubic-bezier(0.15, 0.99, 0.24, 0.99);}
.spin-btn{position:absolute;width:75px;height:75px;border-radius:50%;background:radial-gradient(circle,#9b37ff,#315dff);border:3px solid #fff;color:#fff;font-weight:900;font-size:16px;cursor:pointer;z-index:5;}
.modal{display:none;position:fixed;inset:0;background:#03091bee;backdrop-filter:blur(10px);z-index:100;place-items:center;padding:20px;}
.modal-content{background:linear-gradient(145deg,#07132c,#0b1e47);border:2px solid #35eaa1;border-radius:20px;padding:30px;text-align:center;max-width:360px;width:100%;}
</style>
</head>
<body>
<div style="text-align:center;margin-bottom:15px;">
  <h1 style="font-size:26px;margin:0;background:linear-gradient(110deg,#bc5bff,#315dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎡 عجلة الحظ النيون</h1>
  <p style="color:#a8b7d8;font-size:12px;">متاحة مرة واحدة فقط كل يوم!</p>
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
    const targetDegree = (360 - (selectedIndex * (360 / numItems)) - ((360 / numItems) / 2)) + (360 * 5);
    
    canvas.style.transform = `rotate(${targetDegree}deg)`;

    setTimeout(() => {
      isSpinning = false;
      document.getElementById('prizeTitle').textContent = prize.amount > 0 ? '🎉 مبروك!' : '😅 حظ أوفر!';
      document.getElementById('prizeDesc').textContent = data.msg;
      resultModal.style.display = 'grid';
    }, 5000);
  });
});
</script>
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

    with get_db() as db:
        db.execute("""
            INSERT INTO products (name, description, price_val, price, code, icon, category, color, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?, '#315dff', ?)
        """, (name, description, price_val, price, code, icon, category, badge))

    return redirect(url_for("admin_panel"))

@app.route("/admin/send_announcement", methods=["POST"])
def admin_send_announcement():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))

    title = request.form.get("title")
    message = request.form.get("message")
    
    broadcast_push_notification(title, message)
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
            return jsonify({"status": "error", "message": "لقد استخدمت محاولتك اليومية لعجلة الحظ! عُد غداً للفة جديدة 🎁"})

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

        msg = f"لقد فزت بـ ({prize['label']}) وتمت إضافة المبلغ لمحفظتك!" if prize['amount'] > 0 else "حاول مرة أخرى في المرة القادمة."
        return jsonify({"status": "success", "index": selectedIndex, "msg": msg})

    return render_template_string(SPIN_PAGE)


@app.route("/sw.js")
def service_worker():
    sw_code = """
    self.addEventListener('push', function(event) {
        const data = event.data ? event.data.json() : { title: 'NOVA STORE', body: 'إشعار جديد!' };
        event.waitUntil(
            self.registration.showNotification(data.title, { body: data.body, icon: data.icon || '/static/icon.png' })
        );
    });
    """
    response = make_response(sw_code)
    response.headers["Content-Type"] = "application/javascript"
    return response


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
    <body style="background:#03091b;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;">
      <form method="post" style="background:#07132c;padding:25px;border:1px solid #315dff;border-radius:15px;width:320px;">
        <h2>إنشاء حساب</h2>
        <input name="name" placeholder="الاسم" required style="width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;color:white;">
        <input type="email" name="email" placeholder="البريد الإلكتروني" required style="width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;color:white;">
        <input type="password" name="password" placeholder="كلمة المرور" required style="width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;color:white;">
        <input name="telegram_id" placeholder="Telegram Chat ID" required style="width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;color:white;">
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
    <body style="background:#03091b;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;">
      <form method="post" style="background:#07132c;padding:25px;border:1px solid #315dff;border-radius:15px;width:320px;">
        <h2>تسجيل الدخول</h2>
        <input type="email" name="email" placeholder="البريد الإلكتروني" required style="width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;color:white;">
        <input type="password" name="password" placeholder="كلمة المرور" required style="width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;color:white;">
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
    <body style="background:#03091b;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;">
      <div style="background:#07132c;padding:30px;border:1px solid #315dff;border-radius:15px;text-align:center;width:350px;">
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
