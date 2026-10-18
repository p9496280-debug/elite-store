import os
import hmac
import time
import secrets
import sqlite3
import requests

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

# 👨‍💻 بريد المطور/الأدمن المخصص للدخول
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

# 📱 ضع رقم فودافون كاش الخاص بك هنا
ADMIN_VODAFONE_NUMBER = os.environ.get("VODAFONE_NUMBER", "01011541698")

# 🤖 ضع توكن بوت تيليجرام الخاص بك هنا
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")


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
                color TEXT NOT NULL
            )
        """)

        # إنشاء حساب الأدمن التلقائي إذا لم يكن موجوداً
        admin_exists = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_exists:
            db.execute("""
                INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, created_at)
                VALUES (?, ?, ?, ?, 999999.0, 1, ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), "000000", int(time.time())))

        # إضافة منتجات افتراضية عند تشغيل القاعدة لأول مرة
        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("Google Play", "بطاقات Google Play الرقمية", 100, "100 جنيه", "GPLAY-9876-XXXX", "▶", "بطاقات الألعاب", "#35eaa1"),
                ("PlayStation", "بطاقات واشتراكات PlayStation", 250, "250 جنيه", "PSN-5432-XXXX", "PS", "بطاقات الألعاب", "#62a0ff"),
                ("Steam", "أكواد ومحافظ Steam", 150, "150 جنيه", "STEAM-1122-XXXX", "◉", "بطاقات الألعاب", "#9bb8ff"),
                ("Xbox", "بطاقات وااشتراكات Xbox", 200, "200 جنيه", "XBOX-3344-XXXX", "ⓧ", "بطاقات الألعاب", "#5dff9c"),
                ("Google Accounts", "حسابات جوجل جاهزة وموثقة", 50, "50 جنيه", "acc_google_2026@gmail.com : Pass123", "G", "حسابات جوجل", "#ffc107"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, category, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)


init_db()


def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in rows]


PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#03091b">
<link rel="manifest" href="/manifest.json">
<title>NOVA STORE | متجرك الرقمي</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
:root{--bg:#03091b;--panel:#07132c;--line:#1b315c;--muted:#a8b7d8;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',Arial,sans-serif}a{color:inherit;text-decoration:none}button,input{font:inherit}button{cursor:pointer;color:inherit}
.topbar{min-height:78px;display:flex;align-items:center;gap:22px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:5}
.brand{display:flex;align-items:center;gap:10px;white-space:nowrap;font-family:Arial,sans-serif;font-size:24px;font-weight:800;letter-spacing:.4px}.brand b{color:#754bff}.brand-mark{width:39px;height:39px;display:grid;place-items:center;font-size:33px;font-weight:900;font-style:italic;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.search{height:44px;max-width:470px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:30px;padding:0 17px;background:#09132b}.search span{font-size:24px;color:#7185b5}.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:13px}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.header-actions button,.nav a,.cart{background:none;border:0;font-size:13px}
.lang{border-radius:25px!important;background:#0b1734!important;padding:10px 14px}
.primary{border:0;border-radius:14px;background:linear-gradient(110deg,#9b37ff,#315dff);box-shadow:0 7px 24px #593bff44;color:#fff;font-weight:700}
.small{padding:11px 17px;border-radius:12px}
.login{color:#d8e2ff}
.user-profile-badge {display: flex; align-items: center; gap: 10px; background: #0b1734; border: 1px solid #263d70; padding: 6px 14px; border-radius: 30px; text-decoration: none; transition: 0.2s;}
.user-profile-badge:hover { border-color: #315dff; }
.user-avatar { width: 34px; height: 34px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-weight: bold; color: white; font-size: 15px; }
.user-info { display: flex; flex-direction: column; text-align: right; }
.user-name { font-size: 12px; font-weight: bold; color: #f4f7ff; }
.user-status { font-size: 10px; color: #35eaa1; display: flex; align-items: center; gap: 4px; }
.user-status::before { content: ""; width: 6px; height: 6px; background: #35eaa1; border-radius: 50%; display: inline-block; }

.nav{min-height:46px;padding:0 5%;display:flex;align-items:center;gap:28px;border-bottom:1px solid #18284a;color:#c4cde3;font-size:13px}.nav a{min-height:46px;display:flex;align-items:center}.nav a.active{color:#7f9dff;border-bottom:2px solid #6953ff}.cart{margin-right:auto;font-size:19px!important}.cart span{background:#2777ff;border-radius:20px;padding:1px 7px;font-size:11px}
.spin-link{color:#ffc107!important;font-weight:bold;background:#1a1708;padding:4px 12px;border-radius:15px;border:1px solid #ffc10744}
.admin-link{color:#ff5555!important;font-weight:bold;background:#380b0b;padding:4px 12px;border-radius:15px;border:1px solid #ff555544}

.layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:20px;padding:22px 3.2% 30px}.main-column{min-width:0}
.hero{min-height:290px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b)}.hero:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,#080b2555);pointer-events:none}.hero-copy{padding:28px 32px;z-index:1}.eyebrow{color:#bca0ff;font-size:12px;font-weight:700}.hero h1{font-size:clamp(22px,2.2vw,31px);line-height:1.65;margin:8px 0;font-weight:800}.hero p{color:#c4cce2;font-size:13px;line-height:1.9;max-width:470px;margin:0 0 15px}.hero-btn{display:inline-flex;align-items:center;gap:20px;padding:11px 22px;border-radius:30px;font-size:13px}.trust-row{display:flex;gap:15px;margin-top:20px;color:#dce5ff;font-size:11px;flex-wrap:wrap}
.hero-art{position:relative;min-height:285px;display:flex;align-items:center;justify-content:center;perspective:700px}.glow{position:absolute;width:260px;height:190px;background:#5533ff;filter:blur(80px);opacity:.6}.gift-card{position:absolute;width:112px;height:158px;border:1px solid #66bfff;border-radius:13px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:15px;box-shadow:0 0 26px #168dff66;font-family:Arial,sans-serif;font-size:12px;transform:rotate(-9deg);background:linear-gradient(145deg,#063c9e,#09132e)}.gift-card span{font-size:36px}.gift-card.google{right:40%;z-index:2;transform:rotate(-15deg);background:linear-gradient(145deg,#113e83,#11153c)}.gplay{color:#35eaa1}.gift-card.playstation{right:23%;top:24px;transform:rotate(8deg);background:linear-gradient(145deg,#0759dd,#111342)}.gift-card.steam{right:6%;top:31px;transform:rotate(13deg);background:linear-gradient(145deg,#122b54,#050b1c)}.gift-card.xbox{right:0;top:83px;transform:rotate(19deg);background:linear-gradient(145deg,#076b38,#09271f);width:96px;height:140px}.gift-card.xbox span{color:#64ff99}.controller{position:absolute;bottom:8px;right:42%;font-size:52px;filter:drop-shadow(0 0 15px #5a53ff)}
.categories{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:11px;margin:18px 0 27px}.category{min-height:112px;border:1px solid #172d53;border-radius:13px;background:linear-gradient(150deg,#07152e,#050d20);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:5px;transition:.2s}.category:hover,.category.active{border-color:#5a54ff;transform:translateY(-2px);background:linear-gradient(150deg,#111d4c,#081126)}.category>span{font-size:25px;color:#65baff;text-shadow:0 0 14px #168dff}.category .c-google{color:#35eaa1}.category .c-xbox{color:#5dff9c}.category b{font-size:12px}.category small{font-size:10px;color:#9eafd0}
.section-heading{display:flex;align-items:center;justify-content:space-between;margin:0 5px 13px}.section-heading>div{display:flex;align-items:center;gap:9px}.section-heading h2{font-size:20px;margin:0}.section-heading a{font-size:12px;color:#8198ff}.fire{color:#ff9a6b;font-size:24px}
.product-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:13px;padding:10px;min-width:0;transition:.2s}.product-card:hover{border-color:#5c52ff;transform:translateY(-3px)}.product-visual{height:105px;border-radius:10px;background:radial-gradient(circle at 50% 20%,var(--product-glow),transparent 60%),#07142c;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}.product-visual .logo{font-size:39px;font-weight:800;color:var(--product-color);text-shadow:0 0 20px var(--product-glow)}.product-visual .product-brand{position:absolute;bottom:10px;font:700 12px Arial,sans-serif}.product-card h3{font-size:12px;margin:10px 0 3px}.product-card p{font-size:10px;color:#8fa1c4;margin:0 0 9px}.price{font-size:14px;font-weight:800;color:#fff;margin-bottom:8px}.add-btn{width:100%;padding:9px 4px;border:0;border-radius:9px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700}
.ai-panel{border:1px solid #344b88;border-radius:18px;padding:17px;height:max-content;min-height:420px;background:linear-gradient(155deg,#081735,#060d22);position:sticky;top:145px}.ai-heading{display:flex;align-items:center;gap:12px;margin-bottom:15px}.bot-avatar{width:57px;height:57px;display:grid;place-items:center;border-radius:50%;font-size:30px;color:#b8caff;background:radial-gradient(circle at 35% 25%,#2c8cff,#11175a 65%);border:1px solid #466bff;box-shadow:0 0 24px #2458ff55}.ai-heading h3{margin:0 0 3px;font-size:15px;color:#a99bff}.ai-heading span{font-size:10px;color:#a7b9dc}.ai-heading i{display:inline-block;width:6px;height:6px;border-radius:50%;background:#2fe19a}.ai-message{border:1px solid #1e3c75;border-radius:13px;background:#0a1b42;padding:13px;font-size:12px;line-height:1.9}.ai-message p{color:#c4d1ed;margin:4px 0 0}.ai-quick{display:grid;gap:9px;margin-top:15px}.ai-quick button{border:1px solid #244b91;border-radius:10px;background:#0b2050;padding:10px;font-size:11px;text-align:right}.ai-quick button:hover{background:#132d68}.ai-input{display:flex;gap:7px;align-items:center;border:1px solid #294b91;border-radius:25px;padding:5px;margin-top:22px;background:#081a3c}.ai-input input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:white;padding:6px;font-size:11px}.ai-input button{width:32px;height:32px;border:0;border-radius:50%;background:#4d55ff}.ai-note{font-size:9px;color:#8194ba;line-height:1.6}
footer{border-top:1px solid #192b4e;padding:28px 4.2%;display:grid;grid-template-columns:1.5fr 1fr 1fr 1.4fr;gap:30px;color:#aab9d8;font-size:12px}footer h4{color:#f4f7ff;margin:0 0 12px;font-size:13px}footer>div>a:not(.brand){display:block;margin:6px 0}footer .brand{font-size:21px;color:#fff}footer .brand-mark{width:32px;height:32px;font-size:26px}footer p{line-height:1.8}.socials{display:flex;gap:12px;font-size:20px;color:#7d9bff;margin:10px 0 20px}
.telegram-section { min-width: 0; }
.telegram-section > p { color: #aab9d8; line-height: 1.8; }
.telegram-btn { display: flex !important; align-items: center; justify-content: center; gap: 8px; width: 100%; margin: 10px 0 !important; padding: 12px 10px; border: 1px solid #315dff; border-radius: 12px; color: #fff !important; font-size: 12px; font-weight: 700; transition: transform .2s, box-shadow .2s; }
.telegram-btn:hover { transform: translateY(-3px); box-shadow: 0 7px 20px #315dff44; }
.bot-btn { background: linear-gradient(110deg, #168de5, #315dff); }
.channel-btn { background: linear-gradient(110deg, #087fba, #1647a5); }
.socials a { color: #8baaff; font-size: 12px; }

.install-banner { display: none; position: fixed; bottom: 20px; right: 20px; left: 20px; max-width: 460px; margin: 0 auto; background: linear-gradient(135deg, #07132c, #0b1e47); border: 1px solid #315dff; border-radius: 16px; padding: 14px 18px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7); z-index: 9999; align-items: center; justify-content: space-between; gap: 12px; }
.install-banner-text { display: flex; align-items: center; gap: 12px; }
.install-banner-text div h4 { margin: 0; font-size: 13px; color: #fff; }
.install-banner-text div p { margin: 2px 0 0; font-size: 11px; color: #a8b7d8; }
.install-banner-actions { display: flex; align-items: center; gap: 8px; }
.install-banner-btn { background: linear-gradient(110deg, #9b37ff, #315dff); border: 0; padding: 8px 16px; border-radius: 10px; color: #fff; font-weight: bold; font-size: 12px; cursor: pointer; }
.install-banner-close { background: transparent; border: 0; color: #a8b7d8; font-size: 16px; cursor: pointer; padding: 4px; }

.toast{position:fixed;bottom:22px;left:22px;z-index:10;background:#102957;border:1px solid #496cff;padding:12px 18px;border-radius:12px;box-shadow:0 8px 30px #0008;opacity:0;transform:translateY(10px);transition:.25s;pointer-events:none;font-size:13px}.toast.show{opacity:1;transform:translateY(0)}
@media(max-width:1100px){.topbar{gap:13px;padding:12px 2%}.brand{font-size:20px}.header-actions{gap:7px}.layout{grid-template-columns:1fr}.ai-panel{position:static;min-height:auto}.ai-quick{grid-template-columns:repeat(3,1fr)}.product-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.categories{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:650px){.topbar{min-height:0;padding:12px 4%;gap:10px}.brand{font-size:18px}.brand-mark{width:32px;height:32px;font-size:27px}.search{order:3;flex-basis:100%;max-width:none}.header-actions .login,.header-actions .lang{display:none}.small{padding:9px 11px;font-size:10px}.nav{gap:19px;overflow:auto;padding:0 4%;white-space:nowrap}.nav a{font-size:12px}.layout{padding:13px 3%;gap:15px}.hero{grid-template-columns:1fr}.hero-copy{padding:21px}.hero h1{font-size:22px}.hero-art{min-height:220px;grid-row:1}.gift-card{width:87px;height:124px;font-size:10px}.gift-card span{font-size:29px}.gift-card.google{right:37%}.gift-card.playstation{right:21%;top:15px}.gift-card.steam{right:4%;top:23px}.gift-card.xbox{right:0;top:68px;width:77px;height:112px}.controller{font-size:40px;right:40%}.trust-row{gap:9px}.categories{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.category{min-height:98px}.product-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.product-visual{height:95px}footer{grid-template-columns:1fr 1fr;gap:22px;padding:24px 5%}.footer-brand{grid-column:1/-1}.ai-quick{grid-template-columns:1fr 1fr}.section-heading h2{font-size:17px}}
</style>
</head>
<body>
<header class="topbar">
  <a class="brand" href="#"><span class="brand-mark">N</span><span>NOVA <b>STORE</b></span></a>
  <label class="search"><span>⌕</span><input id="searchInput" type="search" placeholder="ابحث عن أي منتج..." aria-label="بحث عن المنتجات"></label>
  
  <div class="header-actions">
    <button class="lang" id="langBtn">AR ◉</button>
    {% if user %}
      <a href="/account" class="user-profile-badge">
        <div class="user-avatar">{{ user["name"][:1] }}</div>
        <div class="user-info">
          <span class="user-name">{{ user["name"] }}</span>
          <span class="user-status">{{ user["balance"] }} جـ (رصيدك)</span>
        </div>
      </a>
    {% else %}
      <a class="login" href="/login">تسجيل الدخول</a>
      <a class="primary small" href="/register">إنشاء حساب</a>
    {% endif %}
  </div> 
</header>

<nav class="nav">
  <a class="active" href="#">الرئيسية</a>
  <a href="/spin" class="spin-link">🎡 عجلة الحظ</a>
  {% if is_admin %}
    <!-- هذا الزر يظهر حصراً وخاصة للمطور والأدمن فقط -->
    <a href="/admin/dashboard" class="admin-link">⚙️ لوحة المطور</a>
  {% endif %}
  <a href="#categories">المنتجات</a>
  <a href="#products">العروض</a>
  <a href="#footer">من نحن</a>
  <a href="#footer">الدعم</a>
  <button class="cart" id="cartBtn" aria-label="سلة المشتريات">🛒 <span id="cartCount">0</span></button>
</nav>

<main class="layout">
<section class="main-column">
  <section class="hero">
    <div class="hero-copy"><span class="eyebrow">عالمك الرقمي في مكان واحد</span><h1>كل ما تحتاجه من بطاقات الدفع<br>وأكواد الألعاب في مكان واحد!</h1><p>بطاقات رقمية آمنة وسريعة، شحن الألعاب، أكواد المتاجر العالمية والحسابات الرقمية المميزة.</p><a class="primary hero-btn" href="#products">تسوّق الآن <span>←</span></a><div class="trust-row"><span>♧ دفع آمن</span><span>◷ تسليم سريع</span><span>✓ دعم على مدار الساعة</span></div></div>
    <div class="hero-art" aria-label="بطاقات ألعاب رقمية"><div class="glow"></div><div class="gift-card google"><span class="gplay">▶</span><b>Google Play</b></div><div class="gift-card playstation"><span>ＰＳ</span><b>PlayStation</b></div><div class="gift-card steam"><span>◉</span><b>STEAM</b></div><div class="gift-card xbox"><span>ⓧ</span><b>XBOX</b></div><div class="controller">🎮</div></div>
  </section>
  <section class="categories" id="categories">
    <button class="category active" data-category="الكل"><span>▦</span><b>كل المنتجات</b><small>اكتشف المزيد</small></button>
    <button class="category" data-category="Google Play"><span class="c-google">▶</span><b>Google Play</b><small>أكواد جوجل بلاي</small></button>
    <button class="category" data-category="PlayStation"><span>ＰＳ</span><b>PlayStation</b><small>بطاقات وااشتراكات</small></button>
    <button class="category" data-category="Xbox"><span class="c-xbox">ⓧ</span><b>Xbox</b><small>بطاقات وااشتراكات</small></button>
    <button class="category" data-category="Steam"><span>◉</span><b>Steam</b><small>أكواد ومحافظ ستيم</small></button>
    <button class="category" data-category="حسابات جوجل"><span>🌐</span><b>حسابات جوجل</b><small>حسابات جاهزة وموثقة</small></button>
  </section>
  <section class="products-section" id="products"><div class="section-heading"><div><span class="fire">✦</span><h2>أحدث المنتجات</h2></div><a href="#products" id="showAll">عرض الكل ←</a></div><div class="product-grid" id="productGrid"></div></section>
</section>
<aside class="ai-panel">
  <div class="ai-heading"><div class="bot-avatar">✦</div><div><h3>مساعد NOVA AI</h3><span><i></i> مساعد تجريبي</span></div></div>
  <div class="ai-message" id="aiMessages"><b>مرحبًا! 👋</b><p>أنا مساعد NOVA التجريبي. اسألني عن الأقسام أو كيفية استخدام المتجر.</p></div>
  <div class="ai-quick"><button data-prompt="عرض المنتجات المتاحة">عرض المنتجات المتاحة</button><button data-prompt="مساعدة في الشراء">مساعدة في الشراء</button><button data-prompt="كيف أتواصل مع الدعم؟">التواصل مع الدعم</button></div>
  <form class="ai-input" id="aiForm"><input id="aiText" placeholder="اكتب رسالتك هنا..." autocomplete="off" aria-label="رسالة المساعد"><button aria-label="إرسال">➤</button></form><p class="ai-note">مساعد تجريبي بقواعد محلية؛ لا ينفذ عمليات شراء أو دفع.</p>
</aside>
</main>
<footer id="footer">
  <div class="footer-brand">
    <a class="brand" href="/">
      <span class="brand-mark">N</span>
      <span>NOVA <b>STORE</b></span>
    </a>
    <p>متجرك الرقمي لبطاقات الدفع وأكواد الألعاب.</p>
    <p>نحن هنا لمساعدتك والإجابة عن استفساراتك.</p>
  </div>  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="#products">المنتجات</a>
    <a href="#categories">الأقسام</a>
    <a href="/spin">🎡 عجلة الحظ</a>
  </div>  <div>
    <h4>الدعم والمساعدة</h4>
    <a href="https://t.me/Mido_M9do" target="_blank" rel="noopener noreferrer">
      🛟 التواصل مع الدعم
    </a>
    <a href="https://t.me/Mido_M9do" target="_blank" rel="noopener noreferrer">
      👨‍💻 التواصل مع المطوّر
    </a>
  </div>  <div class="telegram-section">
    <h4>مجتمع NOVA STORE</h4>
    <p>تابع قناتنا واستخدم البوت للتواصل معنا.</p><a class="telegram-btn bot-btn"
   href="https://t.me/midoassistantAIbot"
   target="_blank" rel="noopener noreferrer">
  🤖 تشغيل بوت تيليجرام
</a>

<a class="telegram-btn channel-btn"
   href="https://t.me/Midomsn"
   target="_blank" rel="noopener noreferrer">
  📢 الانضمام إلى القناة
</a>

<div class="socials">
  <a href="https://t.me/Mido_M9do"
     target="_blank" rel="noopener noreferrer"
     aria-label="التواصل مع المطور">✈️ تيليجرام</a>
</div>

<small>© 2026 NOVA STORE — جميع الحقوق محفوظة</small>

  </div>
</footer>

<div class="install-banner" id="pwaBanner">
  <div class="install-banner-text">
    <div style="font-size:26px;background:linear-gradient(140deg,#bc5bff,#276bff);width:40px;height:40px;display:grid;place-items:center;border-radius:10px;font-weight:bold;color:#fff;">N</div>
    <div>
      <h4>تطبيق NOVA STORE</h4>
      <p>نزّل التطبيق لتصفح أسرع وتجربة أفضل</p>
    </div>
  </div>
  <div class="install-banner-actions">
    <button class="install-banner-btn" id="pwaBtn">تنزيل</button>
    <button class="install-banner-close" id="pwaClose">✕</button>
  </div>
</div>

<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');
const searchInput = document.getElementById('searchInput');
const cartCount = document.getElementById('cartCount');
const toast = document.getElementById('toast');
let activeCategory = 'الكل';
let cart = [];

function notify(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(notify.timer);
  notify.timer = setTimeout(() => toast.classList.remove('show'), 2600);
}
function renderProducts() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = PRODUCTS.filter(p => {
    const matchesQuery = `${p.name} ${p.description} ${p.category}`.toLowerCase().includes(query);
    const matchesCategory = activeCategory === 'الكل' || p.name === activeCategory || p.category === activeCategory;
    return matchesQuery && matchesCategory;
  });
  productGrid.innerHTML = '';
  if (!filtered.length) {
    productGrid.innerHTML = '<p style="grid-column:1/-1;color:#a8b7d8;text-align:center;padding:30px">لا توجد منتجات مطابقة لبحثك.</p>';
    return;
  }
  filtered.forEach((p, index) => {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.innerHTML = `
      <div class="product-visual" style="--product-color:${p.color};--product-glow:${p.color}55">
        <span class="logo">${p.icon}</span><span class="product-brand">${p.name}</span>
      </div>
      <h3>${p.name}</h3><p>${p.description}</p><div class="price">${p.price}</div>
      <button class="add-btn" type="button" data-add="${index}">＋ أضف للسلة</button>`;
    card.querySelector('[data-add]').addEventListener('click', () => {
      cart.push(p);
      cartCount.textContent = cart.length;
      notify(`تمت إضافة ${p.name} للسلة.`);
    });
    productGrid.appendChild(card);
  });
}
searchInput.addEventListener('input', renderProducts);
document.querySelectorAll('.category').forEach(button => button.addEventListener('click', () => {
  activeCategory = button.dataset.category;
  document.querySelectorAll('.category').forEach(item => item.classList.toggle('active', item === button));
  renderProducts();
  document.getElementById('products').scrollIntoView({behavior:'smooth',block:'start'});
}));
document.getElementById('showAll').addEventListener('click', event => {
  event.preventDefault();
  activeCategory = 'الكل';
  searchInput.value = '';
  document.querySelectorAll('.category').forEach(item => item.classList.toggle('active', item.dataset.category === 'الكل'));
  renderProducts();
});
document.getElementById('cartBtn').addEventListener('click', () => {
  if (!cart.length) return notify('السلة فارغة حاليًا.');
  window.location.href = '/checkout';
});
document.getElementById('langBtn').addEventListener('click', () => notify('الواجهة الحالية باللغة العربية.'));
function answerAssistant(message) {
  const msg = message.trim().toLowerCase();
  if (!msg) return;
  const box = document.getElementById('aiMessages');
  const userLine = document.createElement('p');
  userLine.style.cssText = 'margin-top:12px;padding:8px;background:#102957;border-radius:8px;color:#fff';
  userLine.textContent = 'أنت: ' + message;
  box.appendChild(userLine);
  let answer = 'أقدر أساعدك في معرفة الأقسام والبحث عن المنتجات.';
  if (msg.includes('منتج') || msg.includes('متاح') || msg.includes('قسم')) {
    answer = 'الأقسام المتاحة: Google Play وPlayStation وXbox وSteam وحسابات جوجل وبطاقات الدفع.';
  } else if (msg.includes('شراء') || msg.includes('سلة') || msg.includes('دفع')) {
    answer = 'اضغط «أضف للسلة» تحت المنتج ثم أيقونة السلة للانتقال لصفحة الدفع والشحن.';
  }
  const reply = document.createElement('p');
  reply.style.cssText = 'margin-top:8px;padding:10px;background:#0a1b42;border:1px solid #244b91;border-radius:9px;color:#cbd8f5';
  reply.textContent = 'NOVA AI: ' + answer;
  box.appendChild(reply);
  document.getElementById('aiText').value = '';
  box.scrollTop = box.scrollHeight;
}
document.getElementById('aiForm').addEventListener('submit', event => {
  event.preventDefault();
  answerAssistant(document.getElementById('aiText').value);
});
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => answerAssistant(button.dataset.prompt)));
renderProducts();

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

let deferredPrompt;
const pwaBanner = document.getElementById('pwaBanner');
const pwaBtn = document.getElementById('pwaBtn');
const pwaClose = document.getElementById('pwaClose');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  pwaBanner.style.display = 'flex';
});

pwaBtn.addEventListener('click', () => {
  pwaBanner.style.display = 'none';
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(() => {
      deferredPrompt = null;
    });
  }
});

pwaClose.addEventListener('click', () => {
  pwaBanner.style.display = 'none';
});
</script>
</body>
</html>
"""

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
body{
  margin:0;
  background: radial-gradient(ellipse at center, #0f1c3f 0%, #03091b 100%);
  color:#fff;
  font-family:'Cairo',sans-serif;
  min-height:100vh;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  padding:20px;
  overflow-x:hidden;
}

.spin-header{text-align:center;margin-bottom:20px}
.spin-header h1{font-size:28px;margin:0;background:linear-gradient(110deg,#bc5bff,#315dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:900}
.spin-header p{color:#a8b7d8;font-size:13px;margin-top:5px}

.wheel-container{
  position:relative;
  width:340px;
  height:340px;
  display:flex;
  align-items:center;
  justify-content:center;
  margin:20px 0;
}

.wheel-outer-ring{
  position:absolute;
  inset:-12px;
  border-radius:50%;
  border:4px solid #315dff;
  box-shadow:0 0 35px #8d38ffaa, inset 0 0 20px #315dffaa;
  pointer-events:none;
  z-index:2;
}

.pointer{
  position:absolute;
  top:-22px;
  left:50%;
  transform:translateX(-50%);
  width:0;
  height:0;
  border-left:16px solid transparent;
  border-right:16px solid transparent;
  border-top:28px solid #ff3b3b;
  filter:drop-shadow(0 4px 10px #ff3b3b88);
  z-index:10;
}

canvas{
  width:100%;
  height:100%;
  border-radius:50%;
  transition: transform 5s cubic-bezier(0.15, 0.99, 0.24, 0.99);
}

.spin-btn{
  position:absolute;
  width:75px;
  height:75px;
  border-radius:50%;
  background:radial-gradient(circle, #9b37ff, #315dff);
  border:3px solid #fff;
  color:#fff;
  font-weight:900;
  font-size:16px;
  cursor:pointer;
  box-shadow:0 0 25px #9b37ffbb;
  z-index:5;
  display:grid;
  place-items:center;
  transition:transform .2s, box-shadow .2s;
}
.spin-btn:hover:not(:disabled){transform:scale(1.08);box-shadow:0 0 35px #9b37ff}
.spin-btn:disabled{opacity:0.6;cursor:not-allowed}

.modal{
  display:none;
  position:fixed;
  inset:0;
  background:#03091bee;
  backdrop-filter:blur(10px);
  z-index:100;
  place-items:center;
  padding:20px;
}
.modal-content{
  background:linear-gradient(145deg, #07132c, #0b1e47);
  border:2px solid #35eaa1;
  border-radius:20px;
  padding:30px;
  text-align:center;
  max-width:360px;
  width:100%;
  box-shadow:0 10px 40px #35eaa144;
  animation:pop .4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes pop{from{transform:scale(0.5);opacity:0}to{transform:scale(1);opacity:1}}
.modal-content h2{color:#35eaa1;margin:0 0 10px;font-size:24px}
.modal-content p{color:#a8b7d8;font-size:14px;line-height:1.6}
.modal-btn{margin-top:20px;padding:12px 25px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:12px;color:white;font-weight:bold;cursor:pointer}

.back-link{margin-top:25px;color:#8198ff;text-decoration:none;font-size:13px}
#confettiCanvas{position:fixed;inset:0;pointer-events:none;z-index:99}
</style>
</head>
<body>

<canvas id="confettiCanvas"></canvas>

<div class="spin-header">
  <h1>🎡 عجلة الحظ اليومية</h1>
  <p>أدر العجلة واكسب رصيداً فورياً في محفظتك أو جوائز حصرية!</p>
</div>

<div class="wheel-container">
  <div class="pointer"></div>
  <div class="wheel-outer-ring"></div>
  <canvas id="wheel" width="500" height="500"></canvas>
  <button class="spin-btn" id="spinBtn">أَدِرْ!</button>
</div>

<a href="/" class="back-link">← العودة للمتجر الرئيسية</a>

<div class="modal" id="resultModal">
  <div class="modal-content">
    <div style="font-size:50px;">🎁</div>
    <h2 id="prizeTitle">مبروك!</h2>
    <p id="prizeDesc"></p>
    <button class="modal-btn" onclick="location.href='/'">استلام والعودة للمتجر</button>
  </div>
</div>

<script>
const canvas = document.getElementById('wheel');
const ctx = canvas.getContext('2d');
const spinBtn = document.getElementById('spinBtn');
const resultModal = document.getElementById('resultModal');

const items = [
  { label: '5 جنيه 💰', color: '#8d38ff', type: 'balance', amount: 5 },
  { label: 'حظ أوفر 😅', color: '#1b2a4a', type: 'none', amount: 0 },
  { label: '10 جنيه 💳', color: '#315dff', type: 'balance', amount: 10 },
  { label: 'خصم 20% 🏷️', color: '#00c853', type: 'discount', amount: 0 },
  { label: '50 جنيه 🎁', color: '#ff9100', type: 'balance', amount: 50 },
  { label: 'حساب جوجل 🌐', color: '#ff1744', type: 'account', amount: 0 }
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
    ctx.strokeStyle = '#03091b';
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.save();
    ctx.translate(radius, radius);
    ctx.rotate(angle + arc / 2);
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 22px Cairo";
    ctx.shadowColor = "#000";
    ctx.shadowBlur = 8;
    ctx.fillText(items[i].label, radius - 35, 8);
    ctx.restore();
  }
}

drawWheel();

const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playClickSound() {
  if (audioCtx.state === 'suspended') audioCtx.resume();
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(600, audioCtx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(120, audioCtx.currentTime + 0.04);
  gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
  gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.04);
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.start();
  osc.stop(audioCtx.currentTime + 0.04);
}

function playWinSound() {
  if (audioCtx.state === 'suspended') audioCtx.resume();
  const notes = [261.63, 329.63, 392.00, 523.25];
  notes.forEach((freq, idx) => {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime + idx * 0.12);
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime + idx * 0.12);
    gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + idx * 0.12 + 0.3);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(audioCtx.currentTime + idx * 0.12);
    osc.stop(audioCtx.currentTime + idx * 0.12 + 0.3);
  });
}

function startConfetti() {
  const c = document.getElementById('confettiCanvas');
  const cx = c.getContext('2d');
  c.width = window.innerWidth;
  c.height = window.innerHeight;
  const particles = Array.from({length: 80}, () => ({
    x: Math.random() * c.width,
    y: Math.random() * c.height - c.height,
    r: Math.random() * 6 + 4,
    d: Math.random() * 2 + 1,
    color: ['#bc5bff', '#315dff', '#35eaa1', '#ffc107', '#ff3b3b'][Math.floor(Math.random()*5)]
  }));
  let timer = setInterval(() => {
    cx.clearRect(0, 0, c.width, c.height);
    particles.forEach(p => {
      p.y += p.d * 3;
      cx.beginPath();
      cx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      cx.fillStyle = p.color;
      cx.fill();
    });
  }, 20);
  setTimeout(() => clearInterval(timer), 4000);
}

let isSpinning = false;

spinBtn.addEventListener('click', () => {
  if (isSpinning) return;
  isSpinning = true;
  spinBtn.disabled = true;

  const selectedIndex = Math.floor(Math.random() * numItems);
  const prize = items[selectedIndex];

  const degreesPerItem = 360 / numItems;
  const targetDegree = (360 - (selectedIndex * degreesPerItem) - (degreesPerItem / 2)) + (360 * 5);
  
  let clicks = 0;
  const soundInterval = setInterval(() => {
    playClickSound();
    clicks++;
    if (clicks > 25) clearInterval(soundInterval);
  }, 180);

  canvas.style.transform = `rotate(${targetDegree}deg)`;

  setTimeout(() => {
    isSpinning = false;
    clearInterval(soundInterval);

    if (prize.type !== 'none') {
      playWinSound();
      startConfetti();
    }
    
    fetch('/spin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        prize: prize.label,
        type: prize.type,
        amount: prize.amount
      })
    }).then(() => {
      document.getElementById('prizeTitle').textContent = prize.type === 'none' ? 'للأسف!' : '🎉 مبروك!';
      document.getElementById('prizeDesc').textContent = prize.type === 'none' 
        ? 'حاول مرة أخرى في المرة القادمة.' 
        : `لقد فزت بـ (${prize.label})! تمت إضافة الجائزة إلى محفظتك أو حسابك.`;
      resultModal.style.display = 'grid';
    });

  }, 5000);
});
</script>
</body>
</html>
"""

# ==================== لوحة تحكم الإدارة (Admin Panel) ====================

ADMIN_DASHBOARD_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة التحكم | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{box-sizing:border-box}
body{margin:0;background:#03091b;color:#f4f7ff;font-family:'Cairo',sans-serif;padding:20px}
header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #1b315c;padding-bottom:15px;margin-bottom:25px}
h1{margin:0;font-size:22px;color:#bc5bff}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:30px}
.stat-card{background:#07132c;border:1px solid #263d70;border-radius:14px;padding:18px;text-align:center}
.stat-card h3{margin:0;font-size:13px;color:#a8b7d8}
.stat-card b{font-size:26px;color:#35eaa1;display:block;margin-top:8px}

.section{background:#07132c;border:1px solid #263d70;border-radius:16px;padding:20px;margin-bottom:25px}
.section h2{margin-top:0;font-size:18px;color:#8d38ff;border-bottom:1px solid #1b315c;padding-bottom:10px}

table{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px}
th,td{padding:12px;text-align:right;border-bottom:1px solid #1b315c}
th{color:#a8b7d8;background:#050d20}
input,select{padding:8px 12px;background:#03091b;border:1px solid #263d70;border-radius:8px;color:white;font-size:12px}
.btn{padding:8px 14px;border:0;border-radius:8px;background:#315dff;color:white;font-weight:bold;cursor:pointer;font-size:12px}
.btn-danger{background:#ff3b3b}
</style>
</head>
<body>
<header>
  <h1>⚙️ لوحة تحكم المطور والمدير</h1>
  <a href="/" class="btn">← العودة للمتجر الرئيسية</a>
</header>

<div class="stats">
  <div class="stat-card"><h3>إجمالي المسجلين</h3><b>{{ users|length }}</b></div>
  <div class="stat-card"><h3>إجمالي المنتجات</h3><b>{{ products|length }}</b></div>
  <div class="stat-card"><h3>رقم التحويل الحالي</h3><b style="font-size:18px; color:#ffc107;">{{ vodafone_num }}</b></div>
</div>

<div class="section">
  <h2>👥 إدارة حسابات المستخدمين والمحفظة</h2>
  <table>
    <thead>
      <tr>
        <th>الاسم</th>
        <th>البريد الإلكتروني</th>
        <th>تليجرام ID</th>
        <th>الرصيد الحالي</th>
        <th>تعديل الرصيد</th>
      </tr>
    </thead>
    <tbody>
      {% for u in users %}
      <tr>
        <td><b>{{ u['name'] }}</b></td>
        <td>{{ u['email'] }}</td>
        <td>{{ u['telegram_id'] }}</td>
        <td style="color:#35eaa1; font-weight:bold;">{{ u['balance'] }} جـ</td>
        <td>
          <form method="post" action="/admin/update_balance" style="display:flex; gap:6px;">
            <input type="hidden" name="user_id" value="{{ u['id'] }}">
            <input type="number" step="0.5" name="new_balance" placeholder="الرصيد الجديد" value="{{ u['balance'] }}" style="width:90px;" required>
            <button type="submit" class="btn">حفظ</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div class="section">
  <h2>➕ إضافة منتج جديد</h2>
  <form method="post" action="/admin/add_product" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px;">
    <input name="name" placeholder="اسم المنتج (مثال: جوجل بلاي)" required>
    <input name="description" placeholder="الوصف" required>
    <input type="number" step="1" name="price_val" placeholder="السعر بالجنيه" required>
    <input name="code" placeholder="الكود أو الحساب" required>
    <input name="icon" placeholder="الأيقونة (مثال: ▶)" required>
    <input name="category" placeholder="القسم" required>
    <input name="color" placeholder="كود اللون (مثال: #35eaa1)" value="#315dff" required>
    <button type="submit" class="btn" style="grid-column:1/-1;">حفظ المنتج الجديد</button>
  </form>
</div>

<div class="section">
  <h2>🛒 قائمة المنتجات الحالية</h2>
  <table>
    <thead>
      <tr>
        <th>الاسم</th>
        <th>الوصف</th>
        <th>السعر</th>
        <th>الكود/الحساب</th>
        <th>القسم</th>
        <th>حذف</th>
      </tr>
    </thead>
    <tbody>
      {% for p in products %}
      <tr>
        <td><b>{{ p['name'] }}</b></td>
        <td>{{ p['description'] }}</td>
        <td style="color:#35eaa1;">{{ p['price'] }}</td>
        <td><code>{{ p['code'] }}</code></td>
        <td>{{ p['category'] }}</td>
        <td>
          <a href="/admin/delete_product/{{ p['id'] }}" class="btn btn-danger" onclick="return confirm('هل تريد حذف المنتج؟')">حذف</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
</body>
</html>
"""

# حماية لوحة التحكم: تفتح فقط للمطور/الأدمن
@app.route("/admin/dashboard")
def admin_dashboard():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))

    with get_db() as db:
        users = db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()

    return render_template_string(
        ADMIN_DASHBOARD_PAGE, 
        users=users, 
        products=products, 
        vodafone_num=ADMIN_VODAFONE_NUMBER
    )

@app.route("/admin/update_balance", methods=["POST"])
def admin_update_balance():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))

    user_id = request.form.get("user_id")
    new_balance = request.form.get("new_balance")

    with get_db() as db:
        db.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add_product", methods=["POST"])
def admin_add_product():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))

    name = request.form.get("name")
    description = request.form.get("description")
    price_val = float(request.form.get("price_val", 0))
    price = f"{int(price_val)} جنيه"
    code = request.form.get("code")
    icon = request.form.get("icon")
    category = request.form.get("category")
    color = request.form.get("color")

    with get_db() as db:
        db.execute("""
            INSERT INTO products (name, description, price_val, price, code, icon, category, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price_val, price, code, icon, category, color))

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_product/<int:product_id>")
def admin_delete_product(product_id):
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))

    with get_db() as db:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))

    return redirect(url_for("admin_dashboard"))


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/json")

@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory("static", "sw.js"))
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
                    code = f"{secrets.randbelow(1000000):06d}"
                    now = int(time.time())

                    db.execute("""
                        INSERT OR REPLACE INTO users (name, email, password_hash, telegram_id, balance, verified, created_at)
                        VALUES (?, ?, ?, ?, 0.0, 0, ?)
                    """, (name, email, generate_password_hash(password), telegram_id, now))

                    db.execute("""
                        INSERT OR REPLACE INTO email_codes (email, code, expires_at)
                        VALUES (?, ?, ?)
                    """, (email, code, now + 600))

                    if TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
                        try:
                            msg = f"مرحباً {name}!\n\nكود التحقق الخاص بك لتسجيل الدخول في NOVA STORE هو:\n`{code}`"
                            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                            requests.post(url, json={"chat_id": telegram_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
                        except Exception as e:
                            app.logger.error("فشل إرسال الكود عبر تيليجرام: %s", e)

                    session["verify_email"] = email
                    return redirect(url_for("verify"))

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>إنشاء حساب | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:400px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;box-sizing:border-box}
      h1{color:#9b83ff;text-align:center}
      label{display:block;margin-top:12px;color:#a8b7d8;font-size:13px}
      input{box-sizing:border-box;width:100%;padding:11px;margin-top:5px;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white}
      button{width:100%;padding:13px;margin-top:20px;border:0;border-radius:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;cursor:pointer}
      p{color:#ff9999;text-align:center;font-size:13px}
      a{color:#9db4ff;display:block;text-align:center;margin-top:12px;font-size:12px}
    </style>
    <form method="post">
      <h1>NOVA STORE</h1>
      <h3>إنشاء حساب جديد</h3>
      <label>الاسم</label>
      <input name="name" required>
      <label>البريد الإلكتروني</label>
      <input type="email" name="email" required>
      <label>كلمة المرور</label>
      <input type="password" name="password" required>
      <label>معرف تيليجرام (Telegram Chat ID)</label>
      <input name="telegram_id" placeholder="مثال: 123456789" required>
      <button type="submit">إرسال الكود إلى تيليجرام</button>
      {% if error %}<p>{{ error }}</p>{% endif %}
      <a href="{{ url_for('login') }}">تسجيل الدخول</a>
      <a href="/">العودة للمتجر</a>
    </form>
    </html>
    """, error=error)

@app.route("/verify", methods=["GET", "POST"])
def verify():
    email = session.get("verify_email")
    if not email:
        return redirect(url_for("register"))

    error = ""
    if request.method == "POST":
        entered_code = request.form.get("code", "").strip()
        now = int(time.time())

        with get_db() as db:
            record = db.execute("SELECT * FROM email_codes WHERE email = ?", (email,)).fetchone()
            if record and record["code"] == entered_code and now <= record["expires_at"]:
                db.execute("UPDATE users SET verified = 1 WHERE email = ?", (email,))
                db.execute("DELETE FROM email_codes WHERE email = ?", (email,))
                session.pop("verify_email", None)
                session["user_email"] = email
                return redirect(url_for("account"))
            else:
                error = "كود التحقق غير صحيح أو انتهت صلاحيته."

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>تأكيد الكود | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:380px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;box-sizing:border-box;text-align:center}
      h1{color:#35eaa1;font-size:22px}
      p{color:#a8b7d8;font-size:13px;line-height:1.6}
      input{width:100%;padding:14px;margin-top:15px;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;text-align:center;font-size:24px;letter-spacing:8px;box-sizing:border-box}
      button{width:100%;padding:13px;margin-top:18px;border:0;border-radius:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;cursor:pointer}
      .err{color:#ff9999;margin-top:10px;font-size:13px}
    </style>
    <form method="post">
      <h1>تم إرسال الكود 🤖</h1>
      <p>تفقد بوت تيليجرام الخاص بك، لقد أرسلنا لك كود مكون من 6 أرقام.</p>
      <input name="code" maxlength="6" required autocomplete="one-time-code">
      <button type="submit">تأكيد الحساب</button>
      {% if error %}<div class="err">{{ error }}</div>{% endif %}
    </form>
    </html>
    """, error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ? AND verified = 1", (email,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_email"] = email
            return redirect(url_for("account"))
        error = "بيانات الدخول غير صحيحة أو لم يتم تأكيد الحساب."

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>تسجيل الدخول | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:400px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;box-sizing:border-box}
      h1{color:#9b83ff;text-align:center}
      label{display:block;margin-top:12px;color:#a8b7d8;font-size:13px}
      input{box-sizing:border-box;width:100%;padding:11px;margin-top:5px;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white}
      button{width:100%;padding:13px;margin-top:20px;border:0;border-radius:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;cursor:pointer}
      p{color:#ff9999;text-align:center;font-size:13px}
      a{color:#9db4ff;display:block;text-align:center;margin-top:12px;font-size:12px}
    </style>
    <form method="post">
      <h1>NOVA STORE</h1>
      <h3>تسجيل الدخول</h3>
      <label>البريد الإلكتروني</label>
      <input type="email" name="email" required>
      <label>كلمة المرور</label>
      <input type="password" name="password" required>
      <button type="submit">دخول</button>
      {% if error %}<p>{{ error }}</p>{% endif %}
      <a href="{{ url_for('register') }}">إنشاء حساب جديد</a>
      <a href="/">العودة للمتجر</a>
    </form>
    </html>
    """, error=error)

@app.route("/account")
def account():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    is_admin = (email == ADMIN_EMAIL)

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>حسابي والمحفظة | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      main{width:100%;max-width:450px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;box-sizing:border-box;text-align:center;}
      .profile-avatar { width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-size: 30px; font-weight: bold; color: white; margin: 0 auto 15px; border: 2px solid #35eaa1; }
      h2 { color: #f4f7ff; margin: 5px 0; }
      p{color:#a8b7d8;word-break:break-all;font-size:13px;margin:8px 0;}
      .wallet-box { background: #0b1734; border: 1px solid #315dff; border-radius: 12px; padding: 15px; margin: 15px 0; }
      .wallet-box h3 { color: #35eaa1; margin: 0 0 5px; font-size: 18px; }
      a{display:inline-block;margin-top:10px;color:#9db4ff;text-decoration:none;margin-left:5px;padding:8px 14px;background:#0b1734;border:1px solid #263d70;border-radius:10px;font-size:13px;}
      .logout-btn { background: #571010; border-color: #ff5555; color: #ffcccc; }
      .admin-btn { background: #380b0b; border-color: #ff5555; color: #ff7777; font-weight: bold; }
    </style>
    <main>
      <div class="profile-avatar">{{ user["name"][:1] }}</div>
      <h2>{{ user["name"] }}</h2>
      <p>البريد الإلكتروني: {{ user["email"] }}</p>
      
      <div class="wallet-box">
        <h3>رصيد محفظتك: {{ user["balance"] }} جنيه</h3>
        <p>استخدم رصيدك لشراء الأكواد والحسابات فوراً دون انتظار.</p>
        <a href="/deposit" style="background:#315dff; color:white; border:0;">شحن الرصيد (فودافون كاش)</a>
      </div>

      <div>
        {% if is_admin %}
          <a class="admin-btn" href="/admin/dashboard">⚙️ لوحة المطور الخاصة بيك</a>
        {% endif %}
        <a href="/spin" style="color:#ffc107; font-weight:bold;">🎡 عجلة الحظ</a>
        <a href="/">العودة للمتجر</a>
        <a class="logout-btn" href="/logout">تسجيل الخروج</a>
      </div>
    </main>
    </html>
    """, user=user, is_admin=is_admin)

@app.route("/spin", methods=["GET", "POST"])
def spin():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if request.method == "POST":
        data = request.get_json() or {}
        prize = data.get("prize", "")
        reward_type = data.get("type", "none")
        amount = float(data.get("amount", 0))

        if reward_type == "balance" and amount > 0:
            with get_db() as db:
                db.execute("UPDATE users SET balance = balance + ? WHERE email = ?", (amount, email))

            if user["telegram_id"] and TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
                try:
                    msg = f"🎉 مبروك يا {user['name']}!\n\nلقد ربحت {prize} من عجلة الحظ وتمت إضافة المبلغ إلى محفظتك بنجاح! 💰"
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    requests.post(url, json={"chat_id": user["telegram_id"], "text": msg}, timeout=5)
                except Exception as e:
                    app.logger.error("خطأ تيليجرام: %s", e)

        return jsonify({"status": "success", "new_balance": user["balance"] + amount})

    return render_template_string(SPIN_PAGE, user=user)

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            amount_sent = float(request.form.get("amount", 0))
        except ValueError:
            amount_sent = 0

        fee_percentage = 0.30 
        net_amount = amount_sent * (1 - fee_percentage)

        return render_template_string("""
        <!doctype html>
        <html lang="ar" dir="rtl">
        <head><meta charset="utf-8"><title>طلب شحن | NOVA STORE</title></head>
        <body style="background:#03091b;color:white;text-align:center;padding:50px;font-family:Arial;">
            <div style="background:#07132c;padding:30px;border:1px solid #315dff;border-radius:15px;max-width:400px;margin:auto;">
                <h2 style="color:#35eaa1;">تم إرسال طلب الشحن! 🚀</h2>
                <p>المبلغ المحول: <b>{{ amount_sent }} جنيه</b></p>
                <p style="color:#ffc107;">الرصيد الصافي الذي سيضاف لمحفظتك بعد خصم الرسوم: <br><b style="font-size:22px; color:#35eaa1;">{{ net_amount }} جنيه</b></p>
                <hr style="border-color:#1b315c;">
                <p>يرجى تحويل المبلغ المطلوب إلى رقم فودافون كاش التالي:</p>
                <h2 style="color:#ff3b3b; background:#03091b; padding:10px; border-radius:10px; border:1px solid #ff3b3b55;">{{ vodafone_number }}</h2>
                <p style="font-size:12px; color:#a8b7d8;">سيتم إضافة الرصيد لحسابك فور تأكيد التحويل.</p>
                <a href="/account" style="color:#9db4ff; text-decoration:none;">العودة للحساب</a>
            </div>
        </body>
        </html>
        """, amount_sent=amount_sent, net_amount=net_amount, vodafone_number=ADMIN_VODAFONE_NUMBER)

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <title>شحن المحفظة | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:380px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;box-sizing:border-box}
      input{width:100%;padding:12px;margin:10px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;}
      button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;}
      .number-box{background:#03091b; border:1px solid #ff3b3b; border-radius:10px; padding:12px; text-align:center; margin:10px 0; font-weight:bold; font-size:18px; color:#ff5555;}
      .notice{background:#180f2d; border:1px solid #754bff; border-radius:9px; padding:10px; font-size:11px; color:#d0c2ff; margin-bottom:15px; text-align:center;}
    </style>
    <form method="POST">
      Describe <h2>شحن رصيد المحفظة 💳</h2>
      <div class="notice">💡 تنبيه: يتم خصم رسوم تحويل بسيطة، الشحن بقيمة 10 جـ يمنحك 7 جـ صافي في المحفظة.</div>
      <p style="font-size:13px; color:#a8b7d8;">حول المبلغ لرقم فودافون كاش التالي:</p>
      <div class="number-box">{{ vodafone_number }}</div>
      
      <label>المبلغ المراد تحويله (بالجنيه)</label>
      <input type="number" name="amount" required placeholder="مثال: 10">
      <label>رقم فودافون كاش المحول منه</label>
      <input type="text" name="phone" required placeholder="01xxxxxxxx">
      <button type="submit">تأكيد طلب الشحن</button>
      <a href="/account" style="display:block;text-align:center;margin-top:15px;color:#9db4ff;font-size:13px;text-decoration:none;">العودة للحساب</a>
    </form>
    </html>
    """, vodafone_number=ADMIN_VODAFONE_NUMBER)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    email = session.get("user_email")
    if not email:
        return redirect(url_for("login"))

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if request.method == "POST":
        if user["balance"] >= 50:
            with get_db() as db:
                db.execute("UPDATE users SET balance = balance - 50 WHERE email = ?", (email,))
            
            if user["telegram_id"] and TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
                try:
                    msg = "تم خصم المبلغ من محفظتك بنجاح!\n\n🎟️ الكود الخاص بك:\n`GPLAY-CODE-9988`"
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    requests.post(url, json={"chat_id": user["telegram_id"], "text": msg, "parse_mode": "Markdown"}, timeout=5)
                except Exception as e:
                    app.logger.error("خطأ التيليجرام: %s", e)

            return render_template_string("""
            <body style="background:#03091b;color:white;text-align:center;padding:50px;font-family:Arial;">
                <div style="background:#07132c;padding:30px;border:1px solid #315dff;border-radius:15px;max-width:400px;margin:auto;">
                    <h1 style="color:#35eaa1;">تم الشراء بنجاح! 🚀</h1>
                    <p>تم خصم الثمن من رصيدك وإرسال الكود مباشرة إلى <b>بوت تيليجرام</b>.</p>
                    <a href="/" style="color:#9db4ff;">العودة للمتجر</a>
                </div>
            </body>
            """)
        else:
            return render_template_string("""
            <body style="background:#03091b;color:white;text-align:center;padding:50px;font-family:Arial;">
                <div style="background:#07132c;padding:30px;border:1px solid #ff5555;border-radius:15px;max-width:400px;margin:auto;">
                    <h2 style="color:#ff7777;">عذراً، رصيدك غير كافٍ!</h2>
                    <p>يرجى شحن محفظتك أولاً لتتمكن من إتمام الشراء.</p>
                    <a href="/deposit" style="color:#35eaa1;">شحن الرصيد الآن</a> | <a href="/" style="color:#9db4ff;">الرئيسية</a>
                </div>
            </body>
            """)

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head><meta charset="utf-8"><title>تأكيد الطلب</title></head>
    <body style="background:#03091b;color:white;text-align:center;padding:50px;font-family:Arial;">
        <form method="POST" style="background:#07132c;padding:30px;border:1px solid #315dff;border-radius:15px;max-width:400px;margin:auto;">
            <h2>تأكيد عملية الشراء</h2>
            <p>رصيدك الحالي: <b>{{ user["balance"] }} جنيه</b></p>
            <button type="submit" style="width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;">خصم من الرصيد واستلام الكود بالبوت</button>
            <a href="/" style="display:block;margin-top:15px;color:#9db4ff;">إلغاء والعودة للمتجر</a>
        </form>
    </body>
    </html>
    """, user=user)

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
    return render_template_string(PAGE, products=products, user=user, is_admin=is_admin)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
