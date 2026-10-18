import os
import hmac
import time
import secrets
import sqlite3
import smtplib

from email.message import EmailMessage
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask,
    render_template_string,
    request,
    session,
    redirect,
    url_for,
    flash,
)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
# إعدادات حسابات المستخدمين
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")


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
                verified INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS email_codes (
                email TEXT PRIMARY KEY,
                code_hash TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_sent INTEGER NOT NULL
            )
        """)


def send_verification_email(email, code):
    if not all([MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER]):
        raise RuntimeError("إعدادات البريد الإلكتروني غير مكتملة.")

    message = EmailMessage()
    message["Subject"] = "كود التحقق - NOVA STORE"
    message["From"] = MAIL_DEFAULT_SENDER
    message["To"] = email

    message.set_content(
        f"""مرحبًا بك في NOVA STORE!

كود التحقق الخاص بك هو: {code}

صلاحية الكود 10 دقائق.
لا تشارك هذا الكود مع أي شخص.

إذا لم تطلب إنشاء حساب، يمكنك تجاهل الرسالة.
"""
    )

    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=15) as server:
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(message)


init_db()
# أقسام المتجر التجريبية. يمكن تعديلها أو ربطها بقاعدة بيانات لاحقًا.
PRODUCTS = [
    {
        "name": "Google Play",
        "description": "بطاقات Google Play الرقمية",
        "price": "حسب الفئة",
        "icon": "▶",
        "category": "بطاقات الألعاب",
        "color": "#35eaa1",
    },
    {
        "name": "PlayStation",
        "description": "بطاقات واشتراكات PlayStation",
        "price": "حسب الفئة",
        "icon": "PS",
        "category": "بطاقات الألعاب",
        "color": "#62a0ff",
    },
    {
        "name": "Steam",
        "description": "أكواد ومحافظ Steam",
        "price": "حسب الفئة",
        "icon": "◉",
        "category": "بطاقات الألعاب",
        "color": "#9bb8ff",
    },
    {
        "name": "Xbox",
        "description": "بطاقات واشتراكات Xbox",
        "price": "حسب الفئة",
        "icon": "ⓧ",
        "category": "بطاقات الألعاب",
        "color": "#5dff9c",
    },
    {
        "name": "Digital Cards",
        "description": "بطاقات رقمية متنوعة",
        "price": "حسب الفئة",
        "icon": "▰",
        "category": "بطاقات الدفع",
        "color": "#c49bff",
    },
]

PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#050b20">
<title>NOVA STORE | متجرك الرقمي</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
:root{--bg:#03091b;--panel:#07132c;--line:#1b315c;--muted:#a8b7d8;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',Arial,sans-serif}a{color:inherit;text-decoration:none}button,input{font:inherit}button{cursor:pointer;color:inherit}
.topbar{min-height:78px;display:flex;align-items:center;gap:22px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:5}
.brand{display:flex;align-items:center;gap:10px;white-space:nowrap;font-family:Arial,sans-serif;font-size:24px;font-weight:800;letter-spacing:.4px}.brand b{color:#754bff}.brand-mark{width:39px;height:39px;display:grid;place-items:center;font-size:33px;font-weight:900;font-style:italic;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.search{height:44px;max-width:470px;flex:1;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:30px;padding:0 17px;background:#09132b}.search span{font-size:24px;color:#7185b5}.search input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:13px}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}.header-actions button,.nav a,.cart{background:none;border:0;font-size:13px}.lang{border-radius:25px!important;background:#0b1734!important;padding:10px 14px}.primary{border:0;border-radius:14px;background:linear-gradient(110deg,#9b37ff,#315dff);box-shadow:0 7px 24px #593bff44;color:#fff;font-weight:700}.small{padding:11px 17px;border-radius:12px}.login{color:#d8e2ff}
.nav{min-height:46px;padding:0 5%;display:flex;align-items:center;gap:34px;border-bottom:1px solid #18284a;color:#c4cde3;font-size:13px}.nav a{min-height:46px;display:flex;align-items:center}.nav a.active{color:#7f9dff;border-bottom:2px solid #6953ff}.cart{margin-right:auto;font-size:19px!important}.cart span{background:#2777ff;border-radius:20px;padding:1px 7px;font-size:11px}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:20px;padding:22px 3.2% 30px}.main-column{min-width:0}
.hero{min-height:290px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b)}.hero:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,#080b2555);pointer-events:none}.hero-copy{padding:28px 32px;z-index:1}.eyebrow{color:#bca0ff;font-size:12px;font-weight:700}.hero h1{font-size:clamp(22px,2.2vw,31px);line-height:1.65;margin:8px 0;font-weight:800}.hero p{color:#c4cce2;font-size:13px;line-height:1.9;max-width:470px;margin:0 0 15px}.hero-btn{display:inline-flex;align-items:center;gap:20px;padding:11px 22px;border-radius:30px;font-size:13px}.trust-row{display:flex;gap:15px;margin-top:20px;color:#dce5ff;font-size:11px;flex-wrap:wrap}
.hero-art{position:relative;min-height:285px;display:flex;align-items:center;justify-content:center;perspective:700px}.glow{position:absolute;width:260px;height:190px;background:#5533ff;filter:blur(80px);opacity:.6}.gift-card{position:absolute;width:112px;height:158px;border:1px solid #66bfff;border-radius:13px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:15px;box-shadow:0 0 26px #168dff66;font-family:Arial,sans-serif;font-size:12px;transform:rotate(-9deg);background:linear-gradient(145deg,#063c9e,#09132e)}.gift-card span{font-size:36px}.gift-card.google{right:40%;z-index:2;transform:rotate(-15deg);background:linear-gradient(145deg,#113e83,#11153c)}.gplay{color:#35eaa1}.gift-card.playstation{right:23%;top:24px;transform:rotate(8deg);background:linear-gradient(145deg,#0759dd,#111342)}.gift-card.steam{right:6%;top:31px;transform:rotate(13deg);background:linear-gradient(145deg,#122b54,#050b1c)}.gift-card.xbox{right:0;top:83px;transform:rotate(19deg);background:linear-gradient(145deg,#076b38,#09271f);width:96px;height:140px}.gift-card.xbox span{color:#64ff99}.controller{position:absolute;bottom:8px;right:42%;font-size:52px;filter:drop-shadow(0 0 15px #5a53ff)}
.categories{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:11px;margin:18px 0 27px}.category{min-height:112px;border:1px solid #172d53;border-radius:13px;background:linear-gradient(150deg,#07152e,#050d20);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:5px;transition:.2s}.category:hover,.category.active{border-color:#5a54ff;transform:translateY(-2px);background:linear-gradient(150deg,#111d4c,#081126)}.category>span{font-size:25px;color:#65baff;text-shadow:0 0 14px #168dff}.category .c-google{color:#35eaa1}.category .c-xbox{color:#5dff9c}.category b{font-size:12px}.category small{font-size:10px;color:#9eafd0}
.section-heading{display:flex;align-items:center;justify-content:space-between;margin:0 5px 13px}.section-heading>div{display:flex;align-items:center;gap:9px}.section-heading h2{font-size:20px;margin:0}.section-heading a{font-size:12px;color:#8198ff}.fire{color:#ff9a6b;font-size:24px}
.product-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:13px;padding:10px;min-width:0;transition:.2s}.product-card:hover{border-color:#5c52ff;transform:translateY(-3px)}.product-visual{height:105px;border-radius:10px;background:radial-gradient(circle at 50% 20%,var(--product-glow),transparent 60%),#07142c;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}.product-visual .logo{font-size:39px;font-weight:800;color:var(--product-color);text-shadow:0 0 20px var(--product-glow)}.product-visual .product-brand{position:absolute;bottom:10px;font:700 12px Arial,sans-serif}.product-card h3{font-size:12px;margin:10px 0 3px}.product-card p{font-size:10px;color:#8fa1c4;margin:0 0 9px}.price{font-size:14px;font-weight:800;color:#fff;margin-bottom:8px}.add-btn{width:100%;padding:9px 4px;border:0;border-radius:9px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700}
.ai-panel{border:1px solid #344b88;border-radius:18px;padding:17px;height:max-content;min-height:420px;background:linear-gradient(155deg,#081735,#060d22);position:sticky;top:145px}.ai-heading{display:flex;align-items:center;gap:12px;margin-bottom:15px}.bot-avatar{width:57px;height:57px;display:grid;place-items:center;border-radius:50%;font-size:30px;color:#b8caff;background:radial-gradient(circle at 35% 25%,#2c8cff,#11175a 65%);border:1px solid #466bff;box-shadow:0 0 24px #2458ff55}.ai-heading h3{margin:0 0 3px;font-size:15px;color:#a99bff}.ai-heading span{font-size:10px;color:#a7b9dc}.ai-heading i{display:inline-block;width:6px;height:6px;border-radius:50%;background:#2fe19a}.ai-message{border:1px solid #1e3c75;border-radius:13px;background:#0a1b42;padding:13px;font-size:12px;line-height:1.9}.ai-message p{color:#c4d1ed;margin:4px 0 0}.ai-quick{display:grid;gap:9px;margin-top:15px}.ai-quick button{border:1px solid #244b91;border-radius:10px;background:#0b2050;padding:10px;font-size:11px;text-align:right}.ai-quick button:hover{background:#132d68}.ai-input{display:flex;gap:7px;align-items:center;border:1px solid #294b91;border-radius:25px;padding:5px;margin-top:22px;background:#081a3c}.ai-input input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:white;padding:6px;font-size:11px}.ai-input button{width:32px;height:32px;border:0;border-radius:50%;background:#4d55ff}.ai-note{font-size:9px;color:#8194ba;line-height:1.6}
footer{border-top:1px solid #192b4e;padding:28px 4.2%;display:grid;grid-template-columns:1.5fr 1fr 1fr 1.4fr;gap:30px;color:#aab9d8;font-size:12px}footer h4{color:#f4f7ff;margin:0 0 12px;font-size:13px}footer>div>a:not(.brand){display:block;margin:6px 0}footer .brand{font-size:21px;color:#fff}footer .brand-mark{width:32px;height:32px;font-size:26px}footer p{line-height:1.8}.socials{display:flex;gap:12px;font-size:20px;color:#7d9bff;margin:10px 0 20px}
.telegram-section {
min-width: 0;
}

.telegram-section > p {
color: #aab9d8;
line-height: 1.8;
}

.telegram-btn {
display: flex !important;
align-items: center;
justify-content: center;
gap: 8px;
width: 100%;
margin: 10px 0 !important;
padding: 12px 10px;
border: 1px solid #315dff;
border-radius: 12px;
color: #fff !important;
font-size: 12px;
font-weight: 700;
transition: transform .2s, box-shadow .2s;
}

.telegram-btn:hover {
transform: translateY(-3px);
box-shadow: 0 7px 20px #315dff44;
}

.bot-btn {
background: linear-gradient(110deg, #168de5, #315dff);
}

.channel-btn {
background: linear-gradient(110deg, #087fba, #1647a5);
}

.socials a {
color: #8baaff;
font-size: 12px;
}

@media (max-width: 650px) {
.telegram-section {
grid-column: 1 / -1;
}

.telegram-btn {
padding: 14px;
font-size: 13px;
}
}
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
  <a class="login" href="/login">تسجيل الدخول</a>
  <a class="primary small" href="/register">إنشاء حساب</a>
</div> 
</header>
<nav class="nav">
  <a class="active" href="#">الرئيسية</a><a href="#categories">المنتجات</a><a href="#products">العروض</a><a href="#footer">من نحن</a><a href="#footer">الدعم</a>
  <button class="cart" id="cartBtn" aria-label="سلة المشتريات">🛒 <span id="cartCount">0</span></button>
</nav>
<main class="layout">
<section class="main-column">
  <section class="hero">
    <div class="hero-copy"><span class="eyebrow">عالمك الرقمي في مكان واحد</span><h1>كل ما تحتاجه من بطاقات الدفع<br>وأكواد الألعاب في مكان واحد!</h1><p>بطاقات رقمية آمنة وسريعة، شحن الألعاب، أكواد المتاجر العالمية والمزيد من المنتجات الرقمية المميزة.</p><a class="primary hero-btn" href="#products">تسوّق الآن <span>←</span></a><div class="trust-row"><span>♧ دفع آمن</span><span>◷ تسليم سريع</span><span>✓ دعم على مدار الساعة</span></div></div>
    <div class="hero-art" aria-label="بطاقات ألعاب رقمية"><div class="glow"></div><div class="gift-card google"><span class="gplay">▶</span><b>Google Play</b></div><div class="gift-card playstation"><span>ＰＳ</span><b>PlayStation</b></div><div class="gift-card steam"><span>◉</span><b>STEAM</b></div><div class="gift-card xbox"><span>ⓧ</span><b>XBOX</b></div><div class="controller">🎮</div></div>
  </section>
  <section class="categories" id="categories">
    <button class="category active" data-category="الكل"><span>▦</span><b>كل المنتجات</b><small>اكتشف المزيد</small></button>
    <button class="category" data-category="Google Play"><span class="c-google">▶</span><b>Google Play</b><small>أكواد جوجل بلاي</small></button>
    <button class="category" data-category="PlayStation"><span>ＰＳ</span><b>PlayStation</b><small>بطاقات واشتراكات</small></button>
    <button class="category" data-category="Xbox"><span class="c-xbox">ⓧ</span><b>Xbox</b><small>بطاقات واشتراكات</small></button>
    <button class="category" data-category="Steam"><span>◉</span><b>Steam</b><small>أكواد ومحافظ ستيم</small></button>
    <button class="category" data-category="بطاقات الدفع"><span>▰</span><b>بطاقات الدفع</b><small>بطاقات مسبقة الدفع</small></button>
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
      notify(`تمت إضافة ${p.name} للسلة (طلب تجريبي).`);
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
  const summary = cart.map((item, i) => `${i+1}. ${item.name}`).join('\\n');
  alert(`محتويات السلة (تجريبي):\\n${summary}\\n\\nالدفع غير مفعّل في هذه النسخة.`);
});
document.getElementById('loginBtn').addEventListener('click', () => notify('تسجيل الدخول سيتم تفعيله عند إضافة نظام الحسابات.'));
document.getElementById('signupBtn').addEventListener('click', () => notify('إنشاء الحساب سيتم تفعيله عند إضافة نظام الحسابات.'));
document.getElementById('langBtn').addEventListener('click', () => notify('الواجهة الحالية باللغة العربية.'));
function answerAssistant(message) {
  const msg = message.trim().toLowerCase();
  if (!msg) return;
  const box = document.getElementById('aiMessages');
  const userLine = document.createElement('p');
  userLine.style.cssText = 'margin-top:12px;padding:8px;background:#102957;border-radius:8px;color:#fff';
  userLine.textContent = 'أنت: ' + message;
  box.appendChild(userLine);
  let answer = 'أقدر أساعدك في معرفة الأقسام والبحث عن المنتجات. جرّب زر «عرض المنتجات المتاحة».';
  if (msg.includes('منتج') || msg.includes('متاح') || msg.includes('قسم')) {
    answer = 'الأقسام المتاحة: Google Play وPlayStation وXbox وSteam وبطاقات الدفع. استخدم مربعات الأقسام لتصفية المنتجات.';
  } else if (msg.includes('شراء') || msg.includes('سلة') || msg.includes('دفع')) {
    answer = 'للتجربة، اضغط «أضف للسلة» تحت المنتج ثم أيقونة السلة. الدفع الحقيقي غير مفعّل بعد.';
  } else if (msg.includes('دعم') || msg.includes('تواصل') || msg.includes('مساعدة')) {
    answer = 'يمكنك استخدام قسم الدعم أسفل الصفحة. لم تتم إضافة وسيلة تواصل فعلية بعد.';
  } else if (msg.includes('سعر') || msg.includes('اسعار')) {
    answer = 'الأسعار غير محددة في النسخة التجريبية؛ تظهر المنتجات بعبارة «حسب الفئة».';
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
</script>
</body>
</html>
"""
@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or len(name) > 80:
            error = "اكتب اسمًا صحيحًا لا يتجاوز 80 حرفًا."
        elif len(email) > 254 or "@" not in email:
            error = "اكتب بريدًا إلكترونيًا صحيحًا."
        elif len(password) < 10:
            error = "كلمة المرور يجب أن تكون 10 أحرف على الأقل."
        else:
            with get_db() as db:
                existing = db.execute(
                    "SELECT id, verified FROM users WHERE email = ?",
                    (email,)
                ).fetchone()

                if existing and existing["verified"]:
                    error = "هذا البريد مسجل بالفعل. سجّل الدخول."
                else:
                    now = int(time.time())

                    pending = db.execute(
                        "SELECT last_sent FROM email_codes WHERE email = ?",
                        (email,)
                    ).fetchone()

                    if pending and now - pending["last_sent"] < 60:
                        error = "انتظر دقيقة قبل طلب كود جديد."
                    else:
                        code = f"{secrets.randbelow(1000000):06d}"
                        code_hash = generate_password_hash(code)

                        try:
                            send_verification_email(email, code)

                            db.execute("""
                                INSERT INTO users
                                    (name, email, password_hash, verified, created_at)
                                VALUES (?, ?, ?, 0, ?)
                                ON CONFLICT(email) DO UPDATE SET
                                    name = excluded.name,
                                    password_hash = excluded.password_hash
                                WHERE users.verified = 0
                            """, (
                                name,
                                email,
                                generate_password_hash(password),
                                now
                            ))

                            db.execute("""
                                INSERT INTO email_codes
                                    (email, code_hash, expires_at, attempts, last_sent)
                                VALUES (?, ?, ?, 0, ?)
                                ON CONFLICT(email) DO UPDATE SET
                                    code_hash = excluded.code_hash,
                                    expires_at = excluded.expires_at,
                                    attempts = 0,
                                    last_sent = excluded.last_sent
                            """, (email, code_hash, now + 600, now))

                            session["pending_email"] = email
                            return redirect(url_for("verify_email"))

                        except Exception:
                            app.logger.exception("فشل إرسال كود التحقق")
                            error = (
                                "تعذر إرسال كود التحقق. "
                                "راجع إعدادات البريد وحاول لاحقًا."
                            )

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>إنشاء حساب | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;
           min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:400px;box-sizing:border-box;background:#07132c;
           padding:25px;border:1px solid #315dff;border-radius:18px}
      h1{color:#9b83ff;text-align:center}
      label{display:block;margin-top:15px}
      input{box-sizing:border-box;width:100%;padding:12px;margin-top:7px;
            background:#03091b;border:1px solid #263d70;border-radius:9px;color:white}
      button{width:100%;padding:13px;margin-top:20px;border:0;border-radius:10px;
             background:linear-gradient(110deg,#9b37ff,#315dff);color:white;
             font-weight:bold}
      p{color:#ff9999;line-height:1.7}
      a{color:#9db4ff}
    </style>
    <form method="post">
      <h1>NOVA STORE</h1>
      <h3>إنشاء حساب جديد</h3>
      <label>الاسم</label>
      <input name="name" maxlength="80" required autocomplete="name">
      <label>البريد الإلكتروني</label>
      <input type="email" name="email" required autocomplete="email">
      <label>كلمة المرور (10 أحرف على الأقل)</label>
      <input type="password" name="password" minlength="10"
             required autocomplete="new-password">
      <button type="submit">إرسال كود التحقق</button>
      {% if error %}<p>{{ error }}</p>{% endif %}
      <p><a href="{{ url_for('login') }}">لديك حساب؟ تسجيل الدخول</a></p>
      <a href="/">العودة إلى المتجر</a>
    </form>
    </html>
    """, error=error)


@app.route("/verify", methods=["GET", "POST"])
def verify_email():
    email = session.get("pending_email")

    if not email:
        return redirect(url_for("register"))

    error = ""

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        now = int(time.time())

        with get_db() as db:
            record = db.execute(
                "SELECT * FROM email_codes WHERE email = ?",
                (email,)
            ).fetchone()

            if not record or now > record["expires_at"]:
                error = "انتهت صلاحية الكود. ابدأ التسجيل من جديد."
            elif record["attempts"] >= 5:
                error = "تجاوزت عدد المحاولات المسموح بها."
            else:
                db.execute(
                    "UPDATE email_codes SET attempts = attempts + 1 WHERE email = ?",
                    (email,)
                )

                if (
                    len(code) == 6
                    and code.isdigit()
                    and check_password_hash(record["code_hash"], code)
                ):
                    db.execute(
                        "UPDATE users SET verified = 1 WHERE email = ?",
                        (email,)
                    )
                    db.execute(
                        "DELETE FROM email_codes WHERE email = ?",
                        (email,)
                    )

                    session.pop("pending_email", None)
                    session["user_email"] = email
                    return redirect(url_for("account"))

                error = "كود التحقق غير صحيح."

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>التحقق من البريد | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;
           min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:380px;box-sizing:border-box;background:#07132c;
           padding:25px;border:1px solid #315dff;border-radius:18px;text-align:center}
      input{box-sizing:border-box;width:100%;padding:14px;margin-top:15px;
            background:#03091b;border:1px solid #263d70;border-radius:9px;
            color:white;text-align:center;font-size:24px;letter-spacing:8px}
      button{width:100%;padding:13px;margin-top:18px;border:0;border-radius:10px;
             background:linear-gradient(110deg,#9b37ff,#315dff);color:white}
      p{color:#ff9999}
    </style>
    <form method="post">
      <h1>تأكيد بريدك الإلكتروني 📧</h1>
      <p>أدخل الكود المكون من 6 أرقام الذي أرسلناه إلى بريدك.</p>
      <input name="code" inputmode="numeric" pattern="[0-9]{6}"
             minlength="6" maxlength="6" required autocomplete="one-time-code">
      <button type="submit">تأكيد الحساب</button>
      {% if error %}<p>{{ error }}</p>{% endif %}
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
            user = db.execute(
                "SELECT * FROM users WHERE email = ? AND verified = 1",
                (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_email"] = email
            return redirect(url_for("account"))

        error = "بيانات الدخول غير صحيحة أو لم يتم تأكيد البريد."

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>تسجيل الدخول | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;
           min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:400px;box-sizing:border-box;background:#07132c;
           padding:25px;border:1px solid #315dff;border-radius:18px}
      input{box-sizing:border-box;width:100%;padding:12px;margin:9px 0 15px;
            background:#03091b;border:1px solid #263d70;border-radius:9px;color:white}
      button{width:100%;padding:13px;border:0;border-radius:10px;
             background:linear-gradient(110deg,#9b37ff,#315dff);color:white}
      a{display:inline-block;margin-top:15px;color:#9db4ff}
      p{color:#ff9999}
    </style>
    <form method="post">
      <h1>NOVA STORE</h1>
      <h3>تسجيل الدخول</h3>
      <label>البريد الإلكتروني</label>
      <input type="email" name="email" required autocomplete="email">
      <label>كلمة المرور</label>
      <input type="password" name="password" required autocomplete="current-password">
      <button type="submit">دخول</button>
      {% if error %}<p>{{ error }}</p>{% endif %}
      <a href="{{ url_for('register') }}">إنشاء حساب جديد</a><br>
      <a href="/">العودة إلى المتجر</a>
    </form>
    </html>
    """, error=error)


@app.route("/account")
def account():
    email = session.get("user_email")

    if not email:
        return redirect(url_for("login"))

    with get_db() as db:
        user = db.execute(
            "SELECT name, email FROM users WHERE email = ? AND verified = 1",
            (email,)
        ).fetchone()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>حسابي | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;
           min-height:100vh;display:grid;place-items:center;padding:20px}
      main{width:100%;max-width:500px;box-sizing:border-box;background:#07132c;
           padding:25px;border:1px solid #315dff;border-radius:18px}
      p{color:#a8b7d8;overflow-wrap:anywhere}
      a{display:inline-block;margin:10px 10px 0 0;color:#9db4ff}
    </style>
    <main>
      <h1>👤 حسابي في NOVA STORE</h1>
      <h2>مرحبًا {{ user["name"] }}</h2>
      <p>البريد الإلكتروني: {{ user["email"] }}</p>
      <p>حالة الحساب: تم التحقق ✅</p>
      <a href="/">العودة إلى المتجر</a>
      <a href="{{ url_for('logout') }}">تسجيل الخروج</a>
    </main>
    </html>
    """, user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route("/")
def home():
    return render_template_string(PAGE, products=PRODUCTS)
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not ADMIN_USERNAME or not ADMIN_PASSWORD:
            error = "إعدادات المدير غير مكتملة على السيرفر."
        elif (
            hmac.compare_digest(username, ADMIN_USERNAME)
            and hmac.compare_digest(password, ADMIN_PASSWORD)
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة."

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>NOVA STORE | تسجيل الدخول</title>
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                display: grid;
                place-items: center;
                padding: 20px;
                background: #03091b;
                color: white;
                font-family: Arial, sans-serif;
            }
            .box {
                width: 100%;
                max-width: 400px;
                padding: 28px;
                background: #07132c;
                border: 1px solid #315dff;
                border-radius: 20px;
            }
            h1 { color: #8d70ff; text-align: center; }
            p { color: #a8b7d8; text-align: center; }
            label { display: block; margin-top: 18px; }
            input {
                width: 100%;
                margin-top: 8px;
                padding: 13px;
                border: 1px solid #263d70;
                border-radius: 10px;
                background: #03091b;
                color: white;
            }
            button {
                width: 100%;
                margin-top: 22px;
                padding: 13px;
                border: 0;
                border-radius: 10px;
                background: linear-gradient(110deg,#9b37ff,#315dff);
                color: white;
                font-weight: bold;
                cursor: pointer;
            }
            .error { color: #ff7777; margin-top: 15px; }
        </style>
    </head>
    <body>
        <form class="box" method="POST">
            <h1>NOVA STORE</h1>
            <p>تسجيل دخول لوحة الإدارة 🔐</p>

            <label>اسم المستخدم</label>
            <input name="username" required autocomplete="username">

            <label>كلمة المرور</label>
            <input type="password" name="password"
                   required autocomplete="current-password">

            <button type="submit">تسجيل الدخول</button>

            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
        </form>
    </body>
    </html>
    """, error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))
@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>NOVA STORE | لوحة الإدارة</title>
        <style>
            body {
                margin: 0;
                background: #03091b;
                color: white;
                font-family: Arial, sans-serif;
                padding: 30px;
            }
            .panel {
                max-width: 700px;
                margin: 40px auto;
                padding: 25px;
                background: #07132c;
                border: 1px solid #315dff;
                border-radius: 20px;
            }
            h1 { color: #8d70ff; }
            .card {
                background: #0d1c3b;
                padding: 18px;
                margin: 15px 0;
                border-radius: 12px;
            }
            a {
                display: inline-block;
                margin-top: 15px;
                color: #8baaff;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="panel">
            <h1>⚡ NOVA STORE</h1>
            <h2>لوحة الإدارة</h2>
            <div class="card">
                <h3>🛍️ إدارة المتجر</h3>
                <p>عدد المنتجات التجريبية: 5</p>
            </div>
            <div class="card">
                <h3>💳 إعدادات الدفع</h3>
                <p>وسيلة الدفع المخططة: فودافون كاش</p>
                <p>الدفع الإلكتروني غير مفعّل بعد.</p>
            </div>
            <div class="card">
                <h3>📊 حالة النظام</h3>
                <p>الموقع يعمل في الوضع التجريبي.</p>
            </div>
            <a href="/">← العودة إلى المتجر</a>
            <a href="/admin/logout">تسجيل الخروج 🔒</a>
        </div>
    </body>
    </html>
    """
if __name__ == "__main__":
    # host=0.0.0.0 يسمح بالوصول إلى التطبيق من الشبكة عند الحاجة.
    app.run(host="0.0.0.0", port=5000, debug=False)
