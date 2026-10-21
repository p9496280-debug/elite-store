import os
import hmac
import time
import secrets
import sqlite3
import smtplib
from email.message import EmailMessage
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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "nova_store_secret_9988")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_EMAIL = "moh99zzhvni893fj7@gmail.com"
ADMIN_PASSWORD = "mohammedaaa222"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")
VODAFONE_CASH_NUMBER = "01011541698"
TELEGRAM_CHANNEL = "https://t.me/MidoWorld"

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", ADMIN_EMAIL)

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

        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                price_text TEXT NOT NULL,
                icon TEXT NOT NULL,
                image_url TEXT DEFAULT '',
                category TEXT NOT NULL,
                color TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                discount REAL NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS site_announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)

        # إضافة منتجات افتراضية إذا كانت الجدول فارغاً
        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            defaults = [
                ("شحن فودافون كاش", f"التحويل الفوري على رقم: {VODAFONE_CASH_NUMBER}", 100.0, "100 جـ", "📱", "فودافون كاش", "#ef4444"),
                ("Google Play (10$)", "أكواد جوجل بلاي أمريكي فوريّة", 10.0, "$10.00", "▶", "Google Play", "#35eaa1"),
                ("PlayStation (20$)", "بطاقات المتجر السعودي والأمريكي", 20.0, "$20.00", "PS", "PlayStation", "#62a0ff"),
                ("Xbox Game Pass", "اشتراك شهر كامل فوري", 15.0, "$15.00", "ⓧ", "Xbox", "#5dff9c")
            ]
            db.executemany("INSERT INTO products (name, description, price, price_text, icon, category, color) VALUES (?, ?, ?, ?, ?, ?, ?)", defaults)

        db.execute("INSERT OR IGNORE INTO promo_codes (code, discount) VALUES ('MIDO2026', 15.0)")

init_db()

def send_verification_email(email, code):
    # إرسال الكود عبر البريد أو التنبيه في قناة تليجرام MidoWorld بشكل سري بدون بيانات مستخدم
    try:
        import requests
        requests.post("https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage", json={
            "chat_id": "@MidoWorld",
            "text": f"🔐 طلب كود تحقق جديد لمنصة NOVA STORE\nالبريد: {email[:3]}***@***\nالكود: {code}"
        }, timeout=2)
    except Exception:
        pass

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        return  # تجاوز في حالة عدم ضبط سيرفر البريد واستخدام تليجرام البديل

    message = EmailMessage()
    message["Subject"] = "كود التحقق - NOVA STORE"
    message["From"] = MAIL_DEFAULT_SENDER
    message["To"] = email
    message.set_content(f"مرحبًا بك في NOVA STORE!\n\nkود التحقق الخاص بك هو: {code}\n\nصلاحية الكود 10 دقائق.")
    
    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=15) as server:
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(message)

# واجهة المتجر الرئيسية مع دعم السلة وعجلة الحظ والأكواد
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
:root{--bg:#03091b;--panel:#07132c;--accent:#315dff;--teal:#35eaa1}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#f4f7ff;font-family:'Cairo',sans-serif;min-height:100vh;}
.topbar{height:76px;display:flex;align-items:center;justify-content:space-between;padding:0 3%;background:#040a1bed;border-bottom:1px solid #18284a;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white;}
.brand b{color:#754bff}
.brand-mark{width:38px;height:38px;display:grid;place-items:center;font-size:30px;background:linear-gradient(140deg,#bc5bff,#276bff);color:white;clip-path:polygon(0 0,75% 0,100% 20%,100% 100%,27% 100%,0 78%)}
.search-bar{height:42px;width:300px;display:flex;align-items:center;gap:10px;border:1px solid #263d70;border-radius:25px;padding:0 16px;background:#09132b;}
.search-bar input{width:100%;border:0;outline:0;background:transparent;color:white;font-size:12px;font-family:'Cairo';}
.actions{display:flex;align-items:center;gap:10px;}
.btn-reg{padding:8px 16px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;}
.btn-login{color:#d8e2ff;text-decoration:none;font-size:12px;padding:8px;}
.cart-badge{background:#315dff;color:#fff;border-radius:50%;padding:2px 7px;font-size:11px;}
.announcement-bar{background:linear-gradient(90deg,#7c3aed,#2563eb);color:#fff;text-align:center;padding:10px;font-size:13px;font-weight:bold;}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;padding:20px 3%;}
@media(max-width:900px){.layout{grid-template-columns:1fr;}.ai-panel{display:none;}}
.hero{background:radial-gradient(circle at 75% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c);border:1px solid #263f77;border-radius:20px;padding:25px;margin-bottom:20px;}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px;}
.product-card{background:linear-gradient(150deg,#08152e,#050c1e);border:1px solid #1b3159;border-radius:16px;padding:12px;position:relative;}
.product-visual{height:120px;background:#03091b;border-radius:12px;display:grid;place-items:center;font-size:36px;margin-bottom:10px;overflow:hidden;}
.add-btn{width:100%;padding:8px;background:linear-gradient(100deg,#933aff,#315dff);border:0;border-radius:8px;font-size:11px;font-weight:700;color:white;cursor:pointer;margin-top:8px;}
.ai-panel{background:#07132c;border:1px solid #1b3159;border-radius:18px;padding:16px;height:fit-content;position:sticky;top:90px;}
.cart-modal{background:#071635;border:1px solid #315dff;border-radius:16px;padding:15px;margin-bottom:20px;}
</style>
</head>
<body>

{% if latest_announcement %}
<div class="announcement-bar">📢 إعلان الإدارة: {{ latest_announcement }}</div>
{% endif %}

<header class="topbar">
  <a class="brand" href="/">
    <div class="brand-mark">N</div>
    <span>NOVA <b>STORE</b></span>
  </a>
  <div class="search-bar">
    <span>⌕</span>
    <input id="searchInput" type="search" placeholder="ابحث عن منتج..." onkeyup="filterProducts()">
  </div>
  <div class="actions">
    <a href="/spin" class="btn-reg" style="background:#f59e0b;color:#000;">🎡 عجلة الحظ</a>
    {% if user %}
      <a href="/account" class="btn-reg" style="background:#0b1734;border:1px solid #315dff;">👤 {{ user["name"] }}</a>
      <a href="/logout" class="btn-login" style="color:#fca5a5;">خروج</a>
    {% else %}
      <a href="/login" class="btn-login">دخول</a>
      <a href="/register" class="btn-reg">حساب جديد</a>
    {% endif %}
  </div>
</header>

<div class="layout">
  <main>
    <div class="hero">
      <h2>مرحباً بك في متجر NOVA STORE الرقمي ⚡</h2>
      <p>اشحن بطاقاتك، تواصل عبر تليجرام، وحول بسهولة عبر فودافون كاش على الرقم المعتمد: <b style="color:#35eaa1;">{{ vodafone_num }}</b></p>
      <div style="margin-top:12px;">
        <a href="/spin" style="background:#facc15;color:#000;padding:8px 16px;border-radius:20px;font-weight:bold;text-decoration:none;font-size:12px;">🎡 جرب عجلة الحظ الآن وارفح خصماً!</a>
      </div>
    </div>

    <!-- قسم سلة المشتريات والخصومات -->
    <div class="cart-modal">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <h3 style="margin:0 0 10px;font-size:15px;color:#35eaa1;">🛒 سلة المشتريات الخاصة بك</h3>
        <button onclick="clearCart()" style="background:#ef4444;color:#fff;border:0;padding:4px 10px;border-radius:6px;font-size:10px;cursor:pointer;">🗑️ تفريغ السلة</button>
      </div>
      <div id="cartItemsList" style="font-size:12px;color:#cbd5e1;margin-bottom:10px;">السلة فارغة حالياً.</div>
      <div style="display:flex;gap:10px;align-items:center;margin-top:10px;">
        <input type="text" id="promoInput" placeholder="أدخل كود الخصم (مثال: MIDO2026)" style="background:#03091b;border:1px solid #263d70;padding:6px 10px;border-radius:6px;color:#fff;font-size:11px;flex:1;">
        <button onclick="applyPromo()" style="background:#10b981;color:#fff;border:0;padding:6px 12px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;">تطبيق الخصم 🎟️</button>
      </div>
      <div id="cartTotal" style="margin-top:10px;font-weight:bold;font-size:13px;color:#facc15;">المجموع الإجمالي: 0 جـ</div>
    </div>

    <h3 style="margin:20px 0 10px;font-size:16px;">🔥 المنتجات المتوفرة</h3>
    <div class="product-grid" id="productGrid"></div>
  </main>

  <aside class="ai-panel">
    <h3 style="margin-top:0;color:#38bdf8;font-size:14px;">🤖 مساعدة ودعم فوري</h3>
    <p style="font-size:11px;color:#94a3b8;line-height:1.6;">للتحويل عبر فودافون كاش يرجى التحويل على الرقم: <b style="color:#35eaa1;">{{ vodafone_num }}</b> ثم إرسال الإيصال للمطور عبر تليجرام.</p>
    <a href="{{ telegram_channel }}" target="_blank" style="display:block;text-align:center;background:#229ED9;color:#fff;padding:8px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:11px;margin-top:10px;">📢 قناة تليجرام الرسمية</a>
  </aside>
</div>

<script>
const PRODUCTS = {{ products|tojson }};
let cart = JSON.parse(localStorage.getItem('nova_cart') || '[]');
let currentDiscount = 0;

function renderProducts(items) {
  const grid = document.getElementById('productGrid');
  grid.innerHTML = '';
  items.forEach(p => {
    let card = document.createElement('div');
    card.className = 'product-card';
    let visual = p.image_url ? `<img src="${p.image_url}" style="width:100%;height:100%;object-fit:cover;">` : `<span style="color:${p.color};">${p.icon}</span>`;
    card.innerHTML = `
      <div class="product-visual">${visual}</div>
      <h4 style="margin:0 0 4px;font-size:12px;color:#fff;">${p.name}</h4>
      <p style="margin:0 0 8px;font-size:9.5px;color:#8fa1c4;">${p.description}</p>
      <div style="font-size:13px;font-weight:bold;color:#35eaa1;margin-bottom:6px;">${p.price_text}</div>
      <button class="add-btn" onclick="addToCart('${p.name}', ${p.price}, '${p.price_text}')">أضف للسلة 🛒</button>
    `;
    grid.appendChild(card);
  });
}

function addToCart(name, price, price_text) {
  cart.push({name, price, price_text});
  localStorage.setItem('nova_cart', JSON.stringify(cart));
  updateCartView();
  alert('تمت إضافة المنتج للسلة بنجاح!');
}

function clearCart() {
  cart = [];
  localStorage.removeItem('nova_cart');
  currentDiscount = 0;
  updateCartView();
  alert('تم تفريغ سلة المشتريات بالكامل.');
}

function updateCartView() {
  const list = document.getElementById('cartItemsList');
  const totalDiv = document.getElementById('cartTotal');
  if(cart.length === 0) {
    list.innerHTML = 'السلة فارغة حالياً.';
    totalDiv.innerHTML = 'المجموع الإجمالي: 0 جـ';
    return;
  }
  let html = '<ul style="margin:0;padding-right:15px;">';
  let total = 0;
  cart.forEach((item, idx) => {
    html += `<li>${item.name} - ${item.price_text}</li>`;
    total += item.price;
  });
  html += '</ul>';
  list.innerHTML = html;

  let finalTotal = total - (total * (currentDiscount / 100));
  totalDiv.innerHTML = currentDiscount > 0 ? `المجموع الأصلي: ${total} جـ | بعد خصم (${currentDiscount}%): <span style="color:#10b981;">${finalTotal.toFixed(2)} جـ</span>` : `المجموع الإجمالي: ${total} جـ`;
}

function applyPromo() {
  const code = document.getElementById('promoInput').value.trim();
  if(!code) return alert('أدخل كود الخصم أولاً');
  fetch('/api/apply_promo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({code})
  }).then(res => res.json()).then(data => {
    if(data.success) {
      currentDiscount = data.discount;
      updateCartView();
      alert('🎉 تم تطبيق كود الخصم بنجاح بنسبة: ' + data.discount + '%');
    } else {
      alert('❌ كود الخصم غير صحيح أو منتهي الصلاحية.');
    }
  });
}

function filterProducts() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  renderProducts(PRODUCTS.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q)));
}

updateCartView();
renderProducts(PRODUCTS);
</script>
</body>
</html>
"""

# صفحة عجلة الحظ التفاعلية
@app.route('/spin')
def spin_page():
    return """
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>عجلة الحظ التفاعلية | NOVA STORE</title>
    <style>
    body{background:#03091b;color:#fff;font-family:'Cairo',sans-serif;text-align:center;padding:30px;margin:0;min-height:100vh;display:grid;place-items:center;}
    .box{background:#07132c;border:2px solid #facc15;border-radius:24px;padding:30px;max-width:450px;width:100%;box-shadow:0 0 30px rgba(250,204,21,0.2);}
    .wheel{width:220px;height:220px;border-radius:50%;border:8px solid #facc15;margin:20px auto;background:conic-gradient(#315dff 0deg 90deg, #10b981 90deg 180deg, #ef4444 180deg 270deg, #f59e0b 270deg 360deg);transition:transform 4s ease-out;}
    .btn{padding:12px 24px;background:#facc15;color:#000;border:0;border-radius:25px;font-weight:900;cursor:pointer;font-size:14px;}
    </style>
    </head>
    <body>
    <div class="box">
      <h2>🎡 عجلة الحظ التفاعلية</h2>
      <p style="font-size:12px;color:#cbd5e1;">تدور العجلة وتربح مكافآت وأكواد خصم فورية للمتجر!</p>
      <div class="wheel" id="wheel"></div>
      <button class="btn" onclick="spinWheel()">تدوير العجلة الآن 🎰</button>
      <div id="result" style="margin-top:15px;font-weight:bold;color:#35eaa1;font-size:13px;"></div>
      <br><a href="/" style="color:#38bdf8;font-size:12px;text-decoration:none;">← العودة للمتجر الرئيسي</a>
    </div>
    <script>
    function spinWheel() {
      const wheel = document.getElementById('wheel');
      const res = document.getElementById('result');
      res.textContent = '🎲 جاري تدوير العجلة...';
      const deg = 1800 + Math.floor(Math.random() * 360);
      wheel.style.transform = `rotate(${deg}deg)`;
      setTimeout(() => {
        res.textContent = '🎉 مبروك! ربحت كود الخصم: MIDO2026 (15% خصم)';
      }, 4000);
    }
    </script>
    </body>
    </html>
    """

@app.route('/api/apply_promo', methods=['POST'])
def apply_promo():
    data = request.json or {}
    code = data.get("code", "").strip()
    with get_db() as db:
        res = db.execute("SELECT discount FROM promo_codes WHERE code = ?", (code,)).fetchone()
        if res:
            return jsonify({"success": True, "discount": res["discount"]})
    return jsonify({"success": False})

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
                    code = f"{secrets.randbelow(1000000):06d}"
                    send_verification_email(email, code)
                    db.execute("INSERT INTO users (name, email, password_hash, verified, created_at) VALUES (?, ?, ?, 1, ?)", 
                               (name, email, generate_password_hash(password), int(time.time())))
                    db.commit()
                    session["user_email"] = email
                    return redirect(url_for("account"))
                except Exception as e:
                    error = "البريد الإلكتروني مسجل مسبقاً أو حدث خطأ."
        else:
            error = "يرجى تعبئة جميع الحقول."
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إنشاء حساب</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;text-align:center;}}
    input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
    button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;margin-top:10px;}}
    </style></head>
    <body><div class="box">
    <h2>إنشاء حساب جديد</h2>
    <form method="post">
    <input name='name' placeholder='الاسم الكامل' required>
    <input type='email' name='email' placeholder='البريد الإلكتروني' required>
    <input type='password' name='password' placeholder='كلمة المرور' required>
    <button type="submit">إنشاء الحساب والتسجيل</button>
    </form>
    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/login" style="color:#8198ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">تسجيل الدخول</a>
    </div></body></html>
    """

@app.route('/login', methods=["GET", "POST"])
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
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>تسجيل الدخول</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;text-align:center;}}
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
    <p style="color:#ff7777;font-size:12px;margin-top:10px;">{error}</p>
    <a href="/register" style="color:#8198ff;display:block;margin-top:10px;font-size:12px;text-decoration:none;">إنشاء حساب جديد</a>
    </div></body></html>
    """

@app.route('/account')
def account():
    email = session.get("user_email")
    if not email: return redirect(url_for("login"))
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>حسابي</title>
    <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
    .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:400px;text-align:center;}}</style></head>
    <body><div class="box">
      <h2>👤 مرحباً {user["name"]}</h2>
      <p style="color:#cbd5e1;">البريد الإلكتروني: {user["email"]}</p>
      <div style="background:#03091b;padding:10px;border-radius:8px;margin:15px 0;font-size:12px;">
        رقم فودافون كاش المعتمد للتحويل الفوري: <b style="color:#35eaa1;">{VODAFONE_CASH_NUMBER}</b>
      </div>
      <a href="/" style="color:#38bdf8;display:block;margin-top:10px;text-decoration:none;">← العودة للمتجر الرئيسي</a>
      <a href="/logout" style="color:#ef4444;display:block;margin-top:10px;text-decoration:none;">تسجيل الخروج</a>
    </div></body></html>
    """

@app.route('/logout')
def logout():
    session.pop("user_email", None)
    return redirect(url_for("home"))

# لوحة تحكم المطور الشاملة
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    msg = ""
    # التحقق البسيط من دخول المطور بالبريد والباسورد المحددين
    if request.method == "POST" and request.form.get("login_admin"):
        if request.form.get("email") == ADMIN_EMAIL and request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
        else:
            msg = "بيانات دخول المطور غير صحيحة."

    if not session.get("is_admin"):
        return f"""
        <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>دخول المطور</title>
        <style>body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;}}
        .box{{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:360px;text-align:center;}}
        input{{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;}}
        button{{width:100%;padding:12px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;}}
        </style></head>
        <body><div class="box">
        <h2>🔐 دخول لوحة المطور</h2>
        <form method="post">
        <input type="hidden" name="login_admin" value="1">
        <input type="email" name="email" placeholder="بريد المطور" required>
        <input type="password" name="password" placeholder="كلمة المرور" required>
        <button type="submit">دخول اللوحة</button>
        </form>
        <p style="color:#ff7777;font-size:12px;">{msg}</p>
        <a href="/" style="color:#38bdf8;font-size:12px;text-decoration:none;">← العودة للمتجر</a>
        </div></body></html>
        """

    with get_db() as db:
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add_product":
                name = request.form.get("name")
                desc = request.form.get("desc")
                price = float(request.form.get("price", 0))
                price_text = request.form.get("price_text")
                category = request.form.get("category")
                color = request.form.get("color", "#38bdf8")

                image_url = ""
                file = request.files.get("image_file")
                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = url_for('static', filename=f'uploads/{filename}')

                db.execute("INSERT INTO products (name, description, price, price_text, icon, image_url, category, color) VALUES (?, ?, ?, ?, '📦', ?, ?, ?)",
                           (name, desc, price, price_text, image_url, category, color))
                db.commit()
                msg = "✅ تم إضافة المنتج ورفع الصورة من الهاتف بنجاح!"

            elif action == "add_promo":
                p_code = request.form.get("p_code")
                p_disc = float(request.form.get("p_disc", 10))
                db.execute("INSERT OR REPLACE INTO promo_codes (code, discount) VALUES (?, ?)", (p_code, p_disc))
                db.commit()
                msg = f"🎟️ تم إنشاء كود الخصم ({p_code}) بنسبة {p_disc}% بنجاح!"

            elif action == "announcement":
                ann_msg = request.form.get("ann_msg")
                db.execute("INSERT INTO site_announcements (message, created_at) VALUES (?, ?)", (ann_msg, int(time.time())))
                db.commit()
                msg = "📢 تم نشر الرسالة وإظهارها للمستخدمين على التطبيق بنجاح!"

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>لوحة تحكم المطور</title>
    <style>
    body{{background:#03091b;color:#fff;font-family:Cairo,sans-serif;padding:30px;}}
    .box{{background:#07132c;padding:20px;border:1px solid #315dff;border-radius:14px;margin-bottom:20px;max-width:600px;margin-left:auto;margin-right:auto;}}
    input, textarea, select{{width:100%;padding:10px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:8px;color:#fff;box-sizing:border-box;font-family:Cairo;}}
    button{{padding:10px 20px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:8px;color:#fff;font-weight:bold;cursor:pointer;}}
    </style></head>
    <body>
    <div style="max-width:600px;margin:auto;">
      <h1>⚙️ لوحة تحكم المطور الشاملة</h1>
      <p style="color:#35eaa1;font-weight:bold;">{msg}</p>
      <a href="/" style="color:#38bdf8;display:block;margin-bottom:20px;">← العودة للمتجر الرئيسي</a>

      <div class="box">
        <h3>📦 إضافة منتج جديد (مع رفع صورة من التليفون)</h3>
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="action" value="add_product">
          <input name="name" placeholder="اسم المنتج" required>
          <input name="desc" placeholder="وصف المنتج" required>
          <input type="number" step="0.01" name="price" placeholder="القيمة الرقمية (مثال: 50)" required>
          <input name="price_text" placeholder="السعر المعروض (مثال: 50 جـ)" required>
          <select name="category">
            <option value="Google Play">Google Play</option>
            <option value="PlayStation">PlayStation</option>
            <option value="Xbox">Xbox</option>
            <option value="فودافون كاش">فودافون كاش</option>
          </select>
          <label style="font-size:11px;color:#cbd5e1;">اختر صورة المنتج من الجهاز أو الهاتف:</label>
          <input type="file" name="image_file" accept="image/*">
          <button type="submit" style="margin-top:10px;">إضافة المنتج 🚀</button>
        </form>
      </div>

      <div class="box">
        <h3>🎟️ إضافة وتعديل أكواد الخصم</h3>
        <form method="post">
          <input type="hidden" name="action" value="add_promo">
          <input name="p_code" placeholder="كود الخصم (مثال: SALE50)" required>
          <input type="number" step="0.5" name="p_disc" placeholder="نسبة الخصم بالمائة (%)" required>
          <button type="submit" style="background:#10b981;margin-top:10px;">حفظ وتفعيل الكود</button>
        </form>
      </div>

      <div class="box">
        <h3>📢 إرسال رسالة إعلانية للمستخدمين على التطبيق</h3>
        <form method="post">
          <input type="hidden" name="action" value="announcement">
          <textarea name="ann_msg" placeholder="نص الرسالة التي ستظهر في أعلى التطبيق..." rows="3" required></textarea>
          <button type="submit" style="background:#229ED9;margin-top:10px;">نشر الإعلان فوراً</button>
        </form>
      </div>
    </div>
    </body></html>
    """

@app.route("/")
def home():
    email = session.get("user_email")
    user = None
    if email:
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    with get_db() as db:
        products = [dict(row) for row in db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()]
        ann = db.execute("SELECT message FROM site_announcements ORDER BY id DESC LIMIT 1").fetchone()
        latest_announcement = ann["message"] if ann else ""

    return render_template_string(
        PAGE,
        products=products,
        user=user,
        latest_announcement=latest_announcement,
        vodafone_num=VODAFONE_CASH_NUMBER,
        telegram_channel=TELEGRAM_CHANNEL
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
