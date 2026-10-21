import os
import json
import time
import secrets
import sqlite3

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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_key_9988")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

ADMIN_TELEGRAM_USERNAME = "Mido_M9do"
TELEGRAM_PRIMARY_CHANNEL = "https://t.me/Midomsn"
TELEGRAM_WORLD_CHANNEL = "https://t.me/MidoWorld"
TELEGRAM_BOT_URL = "https://t.me/midoassistantAIbot"
VODAFONE_CASH_NUMBER = "01011541698"


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
                balance REAL NOT NULL DEFAULT 0.0,
                verified INTEGER NOT NULL DEFAULT 1,
                avatar TEXT DEFAULT '⚡',
                rank TEXT DEFAULT 'عضو ماسي 💎',
                points INTEGER DEFAULT 150,
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
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                discount REAL NOT NULL
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

        admin_user = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, balance, verified, avatar, rank, points, created_at)
                VALUES (?, ?, ?, 999999.0, 1, '👑', 'المطور الرئيسي 🚀', 5000, ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), int(time.time())))

        db.execute("INSERT OR IGNORE INTO promo_codes (code, discount) VALUES ('MIDO2026', 10.0)")

        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("شحن فودافون كاش فوري", f"حول على رقمنا: {VODAFONE_CASH_NUMBER}", 100.00, "100 جـ", "VOD-01", "📱", "", "فودافون كاش", "#ef4444", "الأكثر مبيعا"),
                ("بطاقة ائتمان (Visa / Master)", "حول من بطاقتك وتصل إلى فودافون كاش فوراً", 50.00, "$50.00", "CC-02", "💳", "", "بطاقات الائتمان", "#38bdf8", "مميز"),
                ("كود جوجل بلاي (10$)", "الولايات المتحدة الأمريكية", 10.00, "$10.00", "GPLAY-10", "▶", "", "Google Play", "#35eaa1", None),
                ("كود بلايستيشن (20$)", "متجر الولايات المتحدة", 20.00, "$20.00", "PSN-20", "PS", "", "PlayStation", "#62a0ff", None),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)

        cursor_rev = db.execute("SELECT COUNT(*) as count FROM reviews")
        if cursor_rev.fetchone()["count"] == 0:
            db.execute("INSERT INTO reviews (user_name, rating, comment, created_at) VALUES ('محمود علي', 5, 'متجر رائع جداً وسرعة في تسليم الأكواد والتحويل!', ?)", (int(time.time()),))


init_db()


def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def get_reviews():
    with get_db() as db:
        rows = db.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 5").fetchall()
        return [dict(row) for row in rows]


# ==================== الواجهة الرئيسية ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--border:#1b315c;--accent:#315dff;--teal:#35eaa1}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#f4f7ff;font-family:'Cairo',sans-serif;min-height:100vh;}

.topbar{height:76px;display:flex;align-items:center;justify-content:space-between;padding:0 3%;background:#040a1bed;border-bottom:1px solid #18284a;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white;}
.brand b{color:#754bff}
.brand-mark{width:38px;height:38px;display:grid;place-items:center;font-size:30px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}

.search-bar{height:42px;width:320px;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:25px;padding:0 16px;background:#09132b;}
.search-bar input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:12px;font-family:'Cairo';}

.top-actions{display:flex;align-items:center;gap:10px;}
.cart-btn{position:relative;background:#0b1734;border:1px solid #263d70;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;color:#fff;text-decoration:none;}
.cart-badge{position:absolute;top:-4px;right:-4px;background:#315dff;color:#fff;font-size:9px;width:18px;height:18px;border-radius:50%;display:grid;place-items:center;font-weight:bold;}

.btn-reg{padding:8px 16px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;}
.btn-login{color:#d8e2ff;text-decoration:none;font-size:12px;padding:8px 10px;}

.nav-bar{height:54px;padding:0 3%;display:flex;align-items:center;gap:15px;border-bottom:1px solid #18284a;background:#050d22;font-size:13px;font-weight:700;overflow-x:auto;}
.nav-bar::-webkit-scrollbar{display:none;}
.nav-bar a{text-decoration:none;padding:6px 12px;border-radius:10px;transition:0.2s;white-space:nowrap;}
.nav-main{color:#38bdf8;background:#38bdf815;border:1px solid #38bdf844;}
.nav-games{color:#35eaa1;background:#35eaa115;border:1px solid #35eaa144;}
.nav-spin{color:#facc15;background:#facc1515;border:1px solid #facc1544;}
.nav-support{color:#a855f7;background:#a855f715;border:1px solid #a855f744;}

.layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;padding:20px 3%;}
@media (max-width:1000px){.layout{grid-template-columns:1fr;}.ai-sidebar{display:none;}}

.hero{background:radial-gradient(circle at 75% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 60%,#100a3b);border:1px solid #263f77;border-radius:20px;padding:25px;display:grid;grid-template-columns:1.2fr 1fr;align-items:center;margin-bottom:20px;}
.hero h1{font-size:clamp(18px,2vw,24px);line-height:1.6;margin:0 0 10px;font-weight:800;}
.hero p{color:#c4cce2;font-size:11.5px;line-height:1.7;margin:0 0 15px;}
.hero-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;border-radius:30px;font-size:12px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;text-decoration:none;font-weight:bold;}

.promo-box-main{background:linear-gradient(135deg,#07132c,#0a1b3d);border:1px solid #315dff;border-radius:14px;padding:15px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;gap:15px;}
.promo-input{background:#03091b;border:1px solid #263d70;padding:8px 12px;border-radius:8px;color:#fff;font-size:12px;width:200px;}
.promo-apply-btn{background:linear-gradient(110deg,#10b981,#059669);color:#fff;border:0;padding:8px 16px;border-radius:8px;font-weight:bold;cursor:pointer;font-size:12px;}

.cat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:25px;}
.cat-card{background:linear-gradient(150deg,#07152e,#050d20);border:1px solid #1a2d54;border-radius:14px;padding:12px 6px;text-align:center;cursor:pointer;transition:0.2s;}
.cat-card:hover{border-color:#315dff;transform:translateY(-2px);}
.cat-card span{font-size:24px;display:block;margin-bottom:6px;}
.cat-card b{font-size:10.5px;color:#fff;display:block;}
.cat-card p{font-size:8.5px;color:#8fa1c4;margin:2px 0 0;}

.sec-title{display:flex;align-items:center;justify-content:space-between;margin:20px 0 12px;}
.sec-title h2{font-size:17px;margin:0;display:flex;align-items:center;gap:8px;}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px;}
.product-card{background:linear-gradient(150deg,#08152e,#050c1e);border:1px solid #1b3159;border-radius:16px;padding:12px;position:relative;transition:0.2s;}
.product-card:hover{border-color:#35eaa1;transform:translateY(-3px);}
.product-visual{height:130px;background:#03091b;border-radius:12px;display:grid;place-items:center;font-size:36px;margin-bottom:10px;position:relative;}
.badge{position:absolute;top:8px;right:8px;background:#ef4444;color:white;font-size:9px;padding:2px 8px;border-radius:6px;font-weight:bold;}
.product-card h3{font-size:12px;margin:4px 0 2px;color:#fff;}
.product-card p{font-size:9.5px;color:#8fa1c4;margin:0 0 10px;}
.price-row{display:flex;align-items:center;justify-content:space-between;}
.price{font-size:12.5px;font-weight:800;color:#35eaa1;}
.add-btn{padding:6px 10px;background:linear-gradient(100deg,#933aff,#315dff);border:0;border-radius:8px;font-size:10px;font-weight:700;color:white;cursor:pointer;}

.ai-sidebar{background:#07132c;border:1px solid #1b3159;border-radius:18px;padding:16px;height:fit-content;position:sticky;top:90px;}
.ai-header{display:flex;align-items:center;gap:10px;margin-bottom:12px;border-bottom:1px solid #18284a;padding-bottom:10px;}
.ai-avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#38bdf8,#315dff);display:grid;place-items:center;font-size:20px;border:2px solid #35eaa1;}
.ai-msg-box{background:#03091b;border:1px solid #1b3159;border-radius:12px;padding:10px;font-size:10.5px;line-height:1.6;color:#c4cde3;margin-bottom:10px;}
.ai-action-btn{display:block;width:100%;padding:8px;background:#0b1734;border:1px solid #263d70;border-radius:8px;color:#cbd5e1;font-size:10.5px;text-align:right;margin-bottom:5px;cursor:pointer;}
.ai-input-box{display:flex;align-items:center;background:#03091b;border:1px solid #263d70;border-radius:20px;padding:4px 4px 4px 12px;margin-top:8px;}
.ai-input-box input{flex:1;background:transparent;border:0;outline:0;color:#fff;font-size:11px;font-family:'Cairo';}
.ai-send-btn{width:30px;height:30px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:50%;color:white;display:grid;place-items:center;cursor:pointer;}

footer{border-top:1px solid #192b4e;padding:35px 3%;background:#030714;display:grid;grid-template-columns:1.5fr 1fr 1.2fr;gap:25px;color:#aab9d8;font-size:11px;margin-top:40px;}
@media (max-width:850px){footer{grid-template-columns:1fr;}}
.footer-btn-group{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;}
.footer-btn{padding:8px 14px;border-radius:10px;font-weight:bold;text-decoration:none;font-size:11px;display:inline-flex;align-items:center;gap:6px;}
.btn-primary-channel{background:#229ED9;color:#fff;}
.btn-world-channel{background:#8b5cf6;color:#fff;}
.btn-bot{background:#10b981;color:#000;}
.btn-dev{background:#1e293b;border:1px solid #475569;color:#fff;}
</style>
</head>
<body>

<header class="topbar">
  <a class="brand" href="/">
    <div class="brand-mark">N</div>
    <span>NOVA <b>STORE</b></span>
  </a>

  <div class="search-bar">
    <span>⌕</span>
    <input id="searchInput" type="search" placeholder="ابحث عن أي منتج..." onkeyup="filterProducts()">
  </div>

  <div class="top-actions">
    <a href="/cart" class="cart-btn">
      <span>🛒</span>
      <span class="cart-badge" id="cartCount">0</span>
    </a>
    {% if is_admin %}
      <a href="/admin" class="btn-reg" style="background:#7f1d1d;border:1px solid #ef4444;">⚙️ لوحة المطور</a>
    {% endif %}
    {% if user %}
      <a href="/account" class="btn-reg" style="background:#0b1734;border:1px solid #315dff;display:flex;align-items:center;gap:6px;">
        <span>{{ user["avatar"] }}</span>
        <span>{{ user["name"] }}</span>
      </a>
    {% else %}
      <div style="display:flex;gap:6px;">
        <a href="/login" class="btn-login">تسجيل الدخول</a>
        <a href="/register" class="btn-reg">إنشاء حساب</a>
      </div>
    {% endif %}
  </div>
</header>

<nav class="nav-bar">
  <a href="/" class="nav-main">🏠 الرئيسية</a>
  <a href="/game" class="nav-games">🎮 الألعاب الترفيهية</a>
  <a href="/spin" class="nav-spin">🎡 عجلة الحظ السحرية</a>
  <a href="#products" onclick="filterCat('فودافون كاش')">📱 فودافون كاش ({{ vodafone_num }})</a>
  <a href="#products" onclick="filterCat('بطاقات الائتمان')">💳 بطاقات الائتمان</a>
  <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="nav-support">🎧 الدعم والمطور</a>
</nav>

<div class="layout">
  <main>
    <div class="hero">
      <div>
        <h1>كل ما تحتاجه من بطاقات الدفع وشحن فودافون كاش والألعاب!</h1>
        <p>حول الآن على محفظتنا: <b>{{ vodafone_num }}</b> أو استخدم بطاقة الائتمان الخاصة بك لتصل المحفظة فوراً.</p>
        <a class="hero-btn" href="#products">تسوق الآن ←</a>
      </div>
      <div style="display:grid;place-items:center;font-size:55px;">
        💳🔥
      </div>
    </div>

    <div class="promo-box-main">
      <div>
        <b style="font-size:13px;color:#fff;display:block;">🎟️ هل تمتلك كود خصم؟</b>
        <span style="font-size:10px;color:#94a3b8;">أدخل الكود أدناه لتطبيق الخصم فوراً على سلة طلباتك</span>
      </div>
      <div style="display:flex;gap:8px;">
        <input type="text" id="userPromoInput" class="promo-input" placeholder="أدخل الكود (مثال: MIDO2026)">
        <button class="promo-apply-btn" onclick="applyPromoCode()">تفعيل الكود ⚡</button>
      </div>
    </div>

    <div class="cat-grid">
      <div class="cat-card" onclick="filterCat('فودافون كاش')">
        <span style="color:#ef4444;">📱</span>
        <b>فودافون كاش</b>
        <p>{{ vodafone_num }}</p>
      </div>
      <div class="cat-card" onclick="filterCat('بطاقات الائتمان')">
        <span style="color:#38bdf8;">💳</span>
        <b>بطاقات الائتمان</b>
        <p>تحويل آمن للمحفظة</p>
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
      <div class="cat-card" onclick="filterCat('الكل')">
        <span style="color:#bc5bff;">✨</span>
        <b>جميع المنتجات</b>
        <p>عرض الكل</p>
      </div>
    </div>

    <div class="sec-title" id="products">
      <h2><span>🔥</span> أحدث المنتجات وطرق الدفع</h2>
    </div>

    <div class="product-grid" id="productGrid"></div>

    <div style="margin-top:35px;">
      <div class="sec-title">
        <h2><span>⭐️</span> آراء وتقييمات العملاء</h2>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:12px;">
        {% for rev in reviews %}
        <div style="background:#071635;border:1px solid #1e3a6e;padding:12px;border-radius:12px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <b style="font-size:11px;color:#35eaa1;">{{ rev['user_name'] }}</b>
            <span style="color:#facc15;font-size:10px;">{{ '⭐' * rev['rating'] }}</span>
          </div>
          <p style="font-size:10.5px;color:#cbd5e1;margin:0;">{{ rev['comment'] }}</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </main>

  <aside class="ai-sidebar">
    <div class="ai-header">
      <div class="ai-avatar">🤖</div>
      <div>
        <b style="font-size:12px;color:#fff;display:block;">مساعد NOVA AI</b>
        <span style="font-size:8.5px;color:#35eaa1;">● متصل الآن</span>
      </div>
    </div>

    <div class="ai-msg-box">
      مرحباً بك! للتحويل عبر فودافون كاش حول على الرقم: <b>{{ vodafone_num }}</b> وأرسل إيصال التحويل للمطور فوراً.
    </div>

    <button class="ai-action-btn" onclick="aiQuery('رقم فودافون كاش للتحويل')">📱 رقم فودافون كاش</button>
    <button class="ai-action-btn" onclick="aiQuery('طريقة الدفع بالبطاقة')">💳 الدفع بالبطاقة الائتمانية</button>

    <div class="ai-input-box">
      <input type="text" id="aiInput" placeholder="اكتب سؤالك هنا...">
      <button class="ai-send-btn" onclick="sendAiMsg()">➤</button>
    </div>
  </aside>
</div>

<footer>
  <div>
    <a class="brand" href="/" style="margin-bottom:10px;"><span class="brand-mark" style="width:26px;height:26px;font-size:18px;">N</span><span>NOVA <b>STORE</b></span></a>
    <p style="line-height:1.7;margin:0 0 12px;">فودافون كاش التحويل المباشر: <b>{{ vodafone_num }}</b></p>
    
    <div class="footer-btn-group">
      <a href="{{ primary_channel }}" target="_blank" class="footer-btn btn-primary-channel">📢 القناة الأساسية (Midomsn)</a>
      <a href="{{ world_channel }}" target="_blank" class="footer-btn btn-world-channel">🌐 قناة MidoWorld</a>
      <a href="{{ bot_url }}" target="_blank" class="footer-btn btn-bot">🤖 بوت التليجرام</a>
      <a href="https://t.me/{{ admin_telegram }}" target="_blank" class="footer-btn btn-dev">👨‍💻 تواصل مع المطور</a>
    </div>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="/game">🎮 الألعاب الترفيهية</a>
    <a href="/spin">🎡 عجلة الحظ السحرية</a>
    <a href="/cart">🛒 سلة الطلبات</a>
  </div>
  <div>
    <h4>طرق الدفع والتحويل</h4>
    <a href="#">فودافون كاش: {{ vodafone_num }}</a>
    <a href="#">بطاقات الائتمان (تحويل للمحفظة)</a>
    <p style="margin-top:15px;font-size:9.5px;color:#64748b;">© 2026 NOVA STORE محفوظة.</p>
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
    let badge = p.badge ? `<span class="badge">${p.badge}</span>` : '';
    let visual = p.image_url ? `<img src="${p.image_url}" style="width:100%;height:100%;object-fit:cover;border-radius:10px;">` : `<span style="color:${p.color};">${p.icon}</span>`;

    card.innerHTML = `
      ${badge}
      <div class="product-visual">${visual}</div>
      <h3>${p.name}</h3>
      <p>${p.description}</p>
      <div class="price-row">
        <span class="price">${p.price}</span>
        <button class="add-btn" onclick="addToCart('${p.name}', '${p.price}')">طلب وشحن 🛒</button>
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
  alert('تمت إضافة ' + name + ' إلى سلة الطلبات! يجدر التحويل على رقم فودافون كاش: {{ vodafone_num }} وإرسال الإيصال للتأكيد.');
}

function applyPromoCode() {
  const code = document.getElementById('userPromoInput').value.trim();
  if(!code) { alert('الرجاء إدخال كود الخصم أولاً'); return; }
  
  fetch('/api/apply_promo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({code: code})
  })
  .then(res => res.json())
  .then(data => {
    if(data.success) {
      alert('🎉 تم تطبيق كود الخصم بنجاح! نسبة الخصم: ' + data.discount + '%');
    } else {
      alert('❌ الكود غير صحيح أو منتهي الصلاحية.');
    }
  });
}

function aiQuery(text) {
  document.getElementById('aiInput').value = text;
}

function sendAiMsg() {
  const input = document.getElementById('aiInput');
  if(!input.value.trim()) return;
  alert('مساعد NOVA AI: للتحويل الفوري يرجى الإرسال على رقم فودافون كاش: {{ vodafone_num }} والتواصل مع المطور عبر التليجرام.');
  input.value = '';
}

updateCartBadge();
renderProducts(PRODUCTS);
</script>
</body>
</html>
"""


# ==================== صفحة البروفايل الشيك والمجهزة للجيمنج ====================
@app.route('/account')
def account():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>البروفايل الشخصي | NOVA STORE</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    body{background:#020617;color:#fff;font-family:'Cairo',sans-serif;margin:0;padding:20px;min-height:100vh;display:grid;place-items:center;}
    .profile-card{background:linear-gradient(145deg,#07132c,#0a1d42);border:2px solid #315dff;border-radius:24px;max-width:500px;width:100%;padding:30px;box-shadow:0 0 50px rgba(49,93,255,0.25);position:relative;overflow:hidden;}
    .profile-banner{height:90px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:16px;margin:-30px -30px 20px -30px;position:relative;}
    .profile-avatar{width:80px;height:80px;border-radius:50%;background:#03091b;border:4px solid #35eaa1;display:grid;place-items:center;font-size:40px;position:absolute;bottom:-40px;right:30px;box-shadow:0 0 20px rgba(53,234,161,0.4);}
    .user-info{margin-top:25px;}
    .user-name{font-size:22px;font-weight:900;margin:0;color:#fff;display:flex;align-items:center;gap:8px;}
    .user-rank{background:#315dff22;border:1px solid #315dff;color:#38bdf8;padding:2px 10px;border-radius:12px;font-size:10px;font-weight:bold;}
    .stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:20px 0;}
    .stat-box{background:#03091b;border:1px solid #1b3159;padding:12px;border-radius:14px;text-align:center;}
    .stat-val{font-size:16px;font-weight:bold;color:#35eaa1;display:block;}
    .stat-lbl{font-size:9.5px;color:#94a3b8;margin-top:2px;display:block;}
    .btn-action{display:block;width:100%;padding:10px;text-align:center;border-radius:12px;font-weight:bold;text-decoration:none;font-size:12px;margin-top:10px;}
    .btn-logout{background:#7f1d1d;color:#fca5a5;border:1px solid #ef4444;}
    .btn-home{background:#1e293b;color:#38bdf8;border:1px solid #38bdf8;}
    </style>
    </head>
    <body>

    <div class="profile-card">
      <div class="profile-banner">
        <div class="profile-avatar">{{ user['avatar'] }}</div>
      </div>

      <div class="user-info">
        <div class="user-name">
          {{ user['name'] }}
          <span class="user-rank">{{ user['rank'] }}</span>
        </div>
        <span style="font-size:11px;color:#94a3b8;">{{ user['email'] }}</span>
      </div>

      <div class="stats-grid">
        <div class="stat-box">
          <span class="stat-val">{{ user['balance'] }} جـ</span>
          <span class="stat-lbl">رصيد المحفظة</span>
        </div>
        <div class="stat-box">
          <span class="stat-val">{{ user['points'] }} 🌟</span>
          <span class="stat-lbl">نقاط الجيمنج</span>
        </div>
        <div class="stat-box">
          <span class="stat-val">نشط ✅</span>
          <span class="stat-lbl">حالة الحساب</span>
        </div>
      </div>

      <div style="background:#03091b;border:1px solid #1b3159;padding:12px;border-radius:14px;margin-bottom:15px;font-size:11px;line-height:1.6;">
        <b style="color:#38bdf8;display:block;margin-bottom:4px;">📱 بيانات التحويل الفوري:</b>
        محفظة فودافون كاش المعتمدة: <b style="color:#35eaa1;">01011541698</b>
      </div>

      <a href="/" class="btn-action btn-home">🏠 العودة للمتجر الرئيسي</a>
      <a href="/logout" class="btn-action btn-logout">تسجيل الخروج 🚪</a>
    </div>

    </body>
    </html>
    """, user=user)


# ==================== عجلة الحظ السينمائية ====================
@app.route('/spin')
def spin_page():
    return """
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>عجلة الحظ الواقعية | NOVA STORE</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    body{background:#020617;color:#fff;font-family:'Cairo',sans-serif;text-align:center;padding:20px;margin:0;min-height:100vh;display:grid;place-items:center;}
    .spin-container{background:linear-gradient(145deg,#07132c,#0a1b3d);border:2px solid #facc15;border-radius:24px;padding:30px;max-width:480px;width:100%;box-shadow:0 0 45px rgba(250,204,21,0.25);position:relative;}
    .wheel-wrapper{position:relative;width:260px;height:260px;margin:20px auto;}
    .wheel{width:100%;height:100%;border-radius:50%;border:8px solid #facc15;transition:transform 4s cubic-bezier(0.15, 0.95, 0.12, 1);background:conic-gradient(#315dff 0deg 60deg, #933aff 60deg 120deg, #10b981 120deg 180deg, #ef4444 180deg 240deg, #f59e0b 240deg 300deg, #38bdf8 300deg 360deg);box-shadow:0 0 30px rgba(0,0,0,0.8);}
    .pointer{width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-bottom:28px solid #facc15;position:absolute;top:-14px;left:50%;transform:translateX(-50%);z-index:20;}
    .robot-avatar{font-size:50px;animation:pulse 2s infinite;}
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
    .btn-spin{padding:12px 32px;background:linear-gradient(110deg,#facc15,#f59e0b);color:#000;border:0;border-radius:30px;font-weight:900;font-size:16px;cursor:pointer;box-shadow:0 0 20px rgba(250,204,21,0.4);margin-top:15px;}
    </style>
    </head>
    <body>
    <div class="spin-container">
      <div class="robot-avatar">🤖⚡</div>
      <h2 style="color:#facc15;margin:10px 0 5px;">عجلة الحظ السحرية الواقعية</h2>
      <p style="font-size:12px;color:#cbd5e1;">أنا مساعدك الآلي! قم بتدوير العجلة الآن واحصل على هدايا وأكواد فورية.</p>

      <div class="wheel-wrapper">
        <div class="pointer"></div>
        <div class="wheel" id="wheel"></div>
      </div>

      <button class="btn-spin" onclick="startRealisticSpin()">تدوير العجلة الآن 🎰</button>
      <div id="spinResult" style="margin-top:15px;font-weight:bold;font-size:14px;color:#35eaa1;"></div>
      
      <br><a href="/" style="color:#38bdf8;font-size:12px;text-decoration:none;">← العودة للمتجر الرئيسي</a>
    </div>

    <script>
    function startRealisticSpin() {
      const wheel = document.getElementById('wheel');
      const resultDiv = document.getElementById('spinResult');
      resultDiv.textContent = '🎲 جاري تدوير العجلة بواقعية... ترقب الجائزة!';
      
      const randomDeg = 2160 + Math.floor(Math.random() * 360);
      wheel.style.transform = `rotate(${randomDeg}deg)`;

      setTimeout(() => {
        resultDiv.textContent = '🎉 مبروك! ربحت كود خصم خاص 20% (استخدمه في المتجر)';
      }, 4200);
    }
    </script>
    </body>
    </html>
    """


# ==================== الألعاب الترفيهية ====================
@app.route('/game')
def game_page():
    return """
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>منطقة الألعاب الترفيهية | NOVA STORE</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    body{background:#020617;color:#fff;font-family:'Cairo',sans-serif;text-align:center;padding:30px;margin:0;min-height:100vh;display:grid;place-items:center;}
    .game-card{background:linear-gradient(145deg,#07132c,#0a1b3d);border:2px solid #35eaa1;border-radius:24px;padding:30px;max-width:480px;width:100%;box-shadow:0 0 40px rgba(53,234,161,0.2);}
    .btn-action{padding:10px 24px;background:linear-gradient(110deg,#35eaa1,#10b981);color:#000;border:0;border-radius:20px;font-weight:bold;cursor:pointer;margin-top:15px;font-size:13px;}
    </style>
    </head>
    <body>
    <div class="game-card">
      <div style="font-size:50px;">🎮✨</div>
      <h2 style="color:#35eaa1;margin:10px 0;">تحدي الذاكرة والأكواد السريعة</h2>
      <p style="font-size:12px;color:#cbd5e1;">اختبر سرعة بديهتك واجمع نقاطاً يمكنك استبدالها برصيد فودافون كاش أو بطاقات!</p>
      
      <div id="gameArea" style="margin:20px 0;font-size:14px;background:#03091b;padding:15px;border-radius:12px;border:1px solid #1b3159;">
        اضغط على الزر أدناه لبدء التحدي وسحب الكود السريع!
      </div>

      <button class="btn-action" onclick="playGame()">بدء التحدي الآن 🚀</button>
      <br><br><a href="/" style="color:#38bdf8;font-size:12px;text-decoration:none;">← العودة للمتجر الرئيسي</a>
    </div>

    <script>
    function playGame() {
      const codes = ['NOVA-WIN-77', 'MIDO-GIFT-99', 'FODAFONE-CASH-50', 'VIP-CODE-2026'];
      const won = codes[Math.floor(Math.random() * codes.length)];
      document.getElementById('gameArea').innerHTML = `🎉 <b>تهانينا! لقد ربحت كود سري:</b><br><span style="color:#facc15;font-size:16px;font-weight:bold;display:block;margin-top:8px;">${won}</span>`;
    }
    </script>
    </body>
    </html>
    """


# ==================== API تفعيل كود الخصم ====================
@app.route('/api/apply_promo', methods=['POST'])
def apply_promo():
    data = request.json or {}
    code = data.get("code", "").strip()
    with get_db() as db:
        res = db.execute("SELECT discount FROM promo_codes WHERE code = ?", (code,)).fetchone()
        if res:
            return jsonify({"success": True, "discount": res["discount"]})
    return jsonify({"success": False})


# ==================== سلة الطلبات ====================
@app.route('/cart')
def cart_page():
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>سلة الطلبات | NOVA STORE</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;padding:30px;text-align:center;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;max-width:450px;margin:auto;}}</style></head>
    <body>
    <div class="box">
      <h2>🛒 سلة الطلبات والأدوات</h2>
      <p style="font-size:13px;color:#cbd5e1;">لإتمام الشراء وشحن الحسابات، يجدر التحويل على رقم فودافون كاش:</p>
      <div style="background:#03091b;color:#35eaa1;font-size:18px;font-weight:bold;padding:12px;border-radius:10px;border:1px solid #35eaa1;margin:15px 0;">{VODAFONE_CASH_NUMBER}</div>
      <p style="font-size:11px;color:#94a3b8;">أو استخدم بطاقتك الائتمانية لتصل إلى المحفظة مباشرة.</p>
      <a href="https://t.me/{ADMIN_TELEGRAM_USERNAME}" target="_blank" style="padding:12px 24px;background:#229ED9;color:#fff;border-radius:10px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:10px;">💬 تواصل مع المطور لتأكيد الإيصال</a>
      <br><br><a href="/" style="color:#38bdf8;font-size:13px;text-decoration:none;">← العودة للمتجر الرئيسي</a>
    </div>
    </body></html>
    """


# ==================== لوحة المطور الشاملة ====================
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))

    msg = ""
    with get_db() as db:
        if request.method == "POST":
            action = request.form.get("action")
            
            if action == "add_product":
                name = request.form.get("name")
                desc = request.form.get("desc")
                price_val = float(request.form.get("price_val", 0))
                price = request.form.get("price")
                code = request.form.get("code")
                category = request.form.get("category")
                color = request.form.get("color", "#38bdf8")
                badge = request.form.get("badge", "")

                image_url = ""
                file = request.files.get("image_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = url_for('static', filename=f'uploads/{filename}')

                db.execute("""
                    INSERT INTO products (name, description, price_val, price, code, icon, image_url, category, color, badge)
                    VALUES (?, ?, ?, ?, ?, '📦', ?, ?, ?, ?)
                """, (name, desc, price_val, price, code, image_url, category, color, badge))
                db.commit()
                msg = "✅ تم إنشاء المنتج/الكود ورفع الصورة من الهاتف بنجاح!"

            elif action == "add_promo":
                p_code = request.form.get("p_code")
                p_disc = float(request.form.get("p_disc", 10))
                db.execute("INSERT OR REPLACE INTO promo_codes (code, discount) VALUES (?, ?)", (p_code, p_disc))
                db.commit()
                msg = f"🎟️ تم إنشاء كود الخصم ({p_code}) بنسبة {p_disc}% بنجاح!"

            elif action == "broadcast":
                title = request.form.get("b_title")
                b_msg = request.form.get("b_msg")
                try:
                    import requests
                    requests.post(f"https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage", json={
                        "chat_id": "@MidoWorld",
                        "text": f"🚨 **{title}**\n\n{b_msg}\n\n📱 فودافون كاش: {VODAFONE_CASH_NUMBER}\n🔗 متجر NOVA STORE"
                    }, timeout=3)
                except Exception:
                    pass
                msg = "🚀 تم إرسال البث إلى قناة التليجرام بنجاح وبسرية تامة!"

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>لوحة التحكم الشاملة</title>
    <style>
    body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;padding:30px;}}
    .box{{background:#07132c;padding:20px;border:1px solid #315dff;border-radius:14px;margin-bottom:20px;}}
    input, textarea, select{{width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;font-family:Cairo;}}
    button{{padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;}}
    </style></head>
    <body>
    <h1>⚙️ لوحة تحكم المطور الشاملة</h1>
    <p style="color:#35eaa1;font-weight:bold;">{msg}</p>
    <a href="/" style="color:#38bdf8;display:block;margin-bottom:20px;">← العودة للمتجر الرئيسي</a>

    <div class="box">
      <h3>📦 إضافة منتج / كود جديد (مع رفع الصور من الهاتف)</h3>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="add_product">
        <input name="name" placeholder="اسم المنتج أو الكود (مثال: كود فري فاير)" required>
        <input name="desc" placeholder="وصف المنتج أو تعليمات الشحن" required>
        <input type="number" step="0.01" name="price_val" placeholder="القيمة الرقمية (مثال: 100)" required>
        <input name="price" placeholder="السعر المعروض (مثال: 100 جـ)" required>
        <input name="code" placeholder="الكود الفريد للمنتج" required>
        <select name="category">
          <option value="فودافون كاش">فودافون كاش</option>
          <option value="بطاقات الائتمان">بطاقات الائتمان</option>
          <option value="Google Play">Google Play</option>
          <option value="PlayStation">PlayStation</option>
        </select>
        <input name="badge" placeholder="الشارة (مثال: الأكثر مبيعا)">
        <label style="font-size:11px;color:#cbd5e1;display:block;margin-top:5px;">ارفع صورة المنتج من الهاتف:</label>
        <input type="file" name="image_file" accept="image/*">
        <button type="submit" style="margin-top:10px;">إضافة المنتج ورفع الصورة</button>
      </form>
    </div>

    <div class="box">
      <h3>🎟️ إنشاء كود خصم جديد للمتجر</h3>
      <form method="post">
        <input type="hidden" name="action" value="add_promo">
        <input name="p_code" placeholder="كود الخصم (مثال: SAVE20)" required>
        <input type="number" step="0.5" name="p_disc" placeholder="نسبة الخصم مئوية (مثال: 15)" required>
        <button type="submit" style="background:#10b981;margin-top:10px;">إنشاء الكود وتفعيله</button>
      </form>
    </div>

    <div class="box">
      <h3>📢 إذاعة رسالة / بث في قناة التليجرام (بدون بيانات مستخدم)</h3>
      <form method="post">
        <input type="hidden" name="action" value="broadcast">
        <input name="b_title" placeholder="عنوان البث (مثال: عروض فودافون كاش)" required>
        <textarea name="b_msg" placeholder="نص الرسالة أو العرض..." rows="4" required></textarea>
        <button type="submit" style="background:#229ED9;margin-top:10px;">إرسال البث الفوري إلى القناة 🚀</button>
      </form>
    </div>

    </body></html>
    """


# ==================== التسجيل والدخول ====================
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
                    db.commit()
                    session["user_email"] = email
                    return redirect(url_for("home"))
                except Exception:
                    error = "البريد الإلكتروني مسجل مسبقاً."
        else:
            error = "يرجى تعبئة جميع الحقول."

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إنشاء حساب</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;margin-top:10px;}}
    .google-btn{{width:100%;padding:12px;background:#ea4335;color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:10px;display:flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;font-size:13px;}}
    </style></head>
    <body><div class="box">
    <h2>إنشاء حساب جديد</h2>
    <form method="post">
    <input name='name' placeholder='الاسم الكامل' required>
    <input type='email' name='email' placeholder='البريد الإلكتروني' required>
    <input type='password' name='password' placeholder='كلمة المرور' required>
    <button type="submit">إنشاء الحساب</button>
    </form>
    
    <a href="/login/google" class="google-btn">🌐 التسجيل بواسطة حساب جوجل (Google)</a>

    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/login" style="color:#8198ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">تسجيل الدخول</a>
    </div></body></html>
    """


@app.route('/login/google')
def google_login():
    google_email = "google_user_" + secrets.token_hex(3) + "@gmail.com"
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (google_email,)).fetchone()
        if not user:
            db.execute("INSERT INTO users (name, email, password_hash, verified, created_at) VALUES (?, ?, ?, 1, ?)", 
                       ("مستخدم Google", google_email, generate_password_hash("google123"), int(time.time())))
            db.commit()
    session["user_email"] = google_email
    return redirect(url_for("home"))


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
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;margin-top:10px;}}
    .google-btn{{width:100%;padding:12px;background:#ea4335;color:#fff;border:0;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:10px;display:flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;font-size:13px;}}
    </style></head>
    <body><div class="box">
    <h2>تسجيل الدخول</h2>
    <form method="post">
    <input type="email" name="email" placeholder="البريد الإلكتروني" required>
    <input type="password" name="password" placeholder="كلمة المرور" required>
    <button type="submit">دخول</button>
    </form>

    <a href="/login/google" class="google-btn">🌐 الدخول بواسطة حساب جوجل (Google)</a>

    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/register" style="color:#8198ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">إنشاء حساب جديد</a>
    </div></body></html>
    """


@app.route('/logout')
def logout():
    session.pop("user_email", None)
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
    reviews = get_reviews()

    return render_template_string(
        PAGE, 
        products=products, 
        reviews=reviews,
        user=user, 
        is_admin=is_admin,
        admin_telegram=ADMIN_TELEGRAM_USERNAME,
        primary_channel=TELEGRAM_PRIMARY_CHANNEL,
        world_channel=TELEGRAM_WORLD_CHANNEL,
        bot_url=TELEGRAM_BOT_URL,
        vodafone_num=VODAFONE_CASH_NUMBER
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
