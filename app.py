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

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")
ADMIN_TELEGRAM_USERNAME = "Mido_M9do"
TELEGRAM_BOT_USERNAME = "midoassistantAIbot"
TELEGRAM_CHANNEL_LINK = "https://t.me/Midomsn"
# معرف أو رابط جروب التليجرام الخاص بك لاستقبال الأكواد
TELEGRAM_GROUP_CHAT_ID = os.environ.get("TELEGRAM_GROUP_CHAT_ID", "@MidoWorld")


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


def send_telegram_code(chat_id, code, user_email=""):
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    
    target_chat = chat_id if chat_id else TELEGRAM_GROUP_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": f"🛡️ **طلب تحقق جديد في متجر NOVA STORE**\n\n👤 البريد: `{user_email}`\n🔑 كود التحقق: `{code}`\n\nصالح لمدة 5 دقائق فقط."
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


def get_setting(key, default=""):
    with get_db() as db:
        row = db.execute("SELECT value FROM store_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


# ==================== صفحة التسجيل والتوثيق عبر التليجرام ====================
REGISTER_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>إنشاء حساب جديد | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
body{margin:0;background:#03091b;color:white;font-family:'Cairo',sans-serif;display:grid;place-items:center;min-height:100vh;}
.box{background:#07132c;padding:30px;border:1px solid #315dff;border-radius:18px;width:380px;box-shadow:0 10px 30px rgba(49,93,255,0.2);}
input, select{width:100%;padding:12px;margin:8px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;font-size:12px;}
button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;margin-top:10px;font-size:13px;}
</style>
</head>
<body>
<div class="box">
  <div style="text-align:center;margin-bottom:15px;">
    <h2 style="margin:0 0 5px;color:#35eaa1;">🛡️ إنشاء حساب جديد</h2>
    <p style="font-size:11px;color:#a8b7d8;margin:0;">سيتم إرسال كود التحقق إلى جروب التليجرام الرسمي <a href="https://t.me/MidoWorld" target="_blank" style="color:#38bdf8;">MidoWorld</a></p>
  </div>

  {% if step == 1 %}
  <form method="post">
    <input name="name" placeholder="الاسم الكامل" required>
    <input type="email" name="email" placeholder="البريد الإلكتروني الشخصي" required>
    <input type="password" name="password" placeholder="كلمة المرور (6 أحرف على الأقل)" required>
    <button type="submit">إرسال كود التحقق إلى الجروب 🔐</button>
  </form>
  {% else %}
  <form method="post">
    <div style="background:#03091b;padding:12px;border-radius:10px;border:1px solid #35eaa1;margin-bottom:15px;text-align:center;">
      <span style="font-size:12px;color:#35eaa1;display:block;">تم إرسال كود التحقق إلى الجروب بنجاح!</span>
      <a href="https://t.me/MidoWorld" target="_blank" style="display:inline-block;margin-top:8px;padding:6px 14px;background:#315dff;color:#fff;border-radius:6px;text-decoration:none;font-size:11px;font-weight:bold;">🔗 اضغط هنا لفتح جروب التليجرام وجلب الكود</a>
      {% if auto_code %}
        <p style="font-size:13px;color:#facc15;margin-top:8px;">كودك الاحتياطي (إن لم تجده بالجروب): <b>{{ auto_code }}</b></p>
      {% endif %}
    </div>
    <input name="code" placeholder="أدخل كود التحقق المكون من 6 أرقام" required style="text-align:center;font-size:16px;letter-spacing:2px;">
    <button type="submit">تأكيد الحساب والدخول 🚀</button>
  </form>
  {% endif %}

  {% if error %}<p style="color:#ff7777;font-size:12px;margin-top:10px;text-align:center;">{{ error }}</p>{% endif %}
  <a href="/login" style="color:#8198ff;display:block;margin-top:15px;text-align:center;font-size:12px;text-decoration:none;">لديك حساب بالفعل؟ تسجيل الدخول</a>
</div>
</body>
</html>
"""

# ==================== الصفحة الرئيسية للمتجر ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي الشامل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#03091b;--panel:#07132c;--text:#f4f7ff;--blue:#315dff;--purple:#8d38ff;}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% 0%,#10133e 0,transparent 36%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.topbar{min-height:78px;display:flex;align-items:center;gap:20px;padding:12px 4%;border-bottom:1px solid #18284a;position:sticky;top:0;background:#040a1bed;backdrop-filter:blur(16px);z-index:10}
.brand{display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800;text-decoration:none;color:white}.brand b{color:#754bff}
.header-actions{display:flex;align-items:center;gap:10px;margin-right:auto}
.nav{min-height:58px;padding:0 4%;display:flex;align-items:center;gap:12px;border-bottom:1px solid #1a2d54;background:#07122b;overflow-x:auto;}
.nav::-webkit-scrollbar{display:none}
.nav a{color:#c4cde3;text-decoration:none;padding:8px 16px;border-radius:12px;font-size:12.5px;font-weight:600;display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.03);white-space:nowrap;}
.layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:22px;padding:22px 4%}
@media (max-width:850px){.layout{grid-template-columns:1fr;}}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.product-card{border:1px solid #1b3159;background:#050c1e;border-radius:14px;padding:12px;}
.product-img{width:100%;height:150px;object-fit:contain;border-radius:10px;background:#03091b;}
.add-btn{padding:7px 12px;border:0;border-radius:8px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700;color:white;text-decoration:none;display:inline-block;}
.admin-badge{background:#570f0f;color:#ff7777;border:1px solid #ff5555;padding:6px 14px;border-radius:12px;font-weight:bold;text-decoration:none;}
</style>
</head>
<body>

<header class="topbar">
  <a class="brand" href="/"><span>NOVA <b>STORE</b></span></a>
  <div class="header-actions">
    {% if is_admin %}
      <a href="/admin" class="admin-badge">⚙️ لوحة المطور</a>
    {% endif %}
    {% if user %}
      <span style="color:#35eaa1;font-size:12px;font-weight:bold;">{{ user["name"] }} ({{ user["balance"] }} جـ)</span>
      <a href="/logout" style="color:#ff7777;font-size:11px;text-decoration:none;margin-right:10px;">خروج</a>
    {% else %}
      <a href="/login" style="color:#d8e2ff;text-decoration:none;font-size:12px;">تسجيل الدخول</a>
      <a href="/register" style="padding:8px 14px;background:linear-gradient(110deg,#9b37ff,#315dff);border-radius:10px;font-weight:bold;color:white;text-decoration:none;font-size:12px;">إنشاء حساب</a>
    {% endif %}
  </div> 
</header>

<nav class="nav">
  <a href="/" style="background:linear-gradient(110deg,#9b37ff,#315dff);color:#fff;"><span>🏠</span> الرئيسية</a>
  <a href="/game" style="background:linear-gradient(135deg,#ec4899,#8b5cf6);color:#fff;"><span>🎮</span> لعبة الذاكرة والروبوت</a>
  <a href="/spin" style="background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;"><span>🎡</span> عجلة الحظ السينمائية</a>
  <a href="https://t.me/MidoWorld" target="_blank" style="background:linear-gradient(135deg,#38bdf8,#315dff);color:#fff;"><span>📢</span> جروب التليجرام</a>
</nav>

<main class="layout">
  <aside>
    <div style="background:#07132c;border:1px solid #315dff;border-radius:18px;padding:16px;">
      <h4 style="margin:0 0 10px;">💳 رصيدك الحالي</h4>
      <h2 style="color:#35eaa1;margin:0;">{% if user %}{{ user["balance"] }}{% else %}0.0{% endif %} جـ</h2>
    </div>
  </aside>

  <section>
    <h2>🔥 أحدث المنتجات</h2>
    <div class="product-grid">
      {% for p in products %}
      <div class="product-card">
        {% if p["image_url"] %}
          <img src="{{ p['image_url'] }}" class="product-img">
        {% else %}
          <div style="height:150px;display:grid;place-items:center;font-size:35px;background:#03091b;border-radius:10px;">{{ p["icon"] }}</div>
        {% endif %}
        <h3 style="margin:8px 0 4px;font-size:13px;">{{ p["name"] }}</h3>
        <p style="font-size:10px;color:#a8b7d8;margin:0 0 8px;">{{ p["description"] }}</p>
        <span style="color:#35eaa1;font-weight:bold;display:block;margin-bottom:8px;">{{ p["price"] }}</span>
        <a href="https://t.me/{{ admin_telegram }}?text=أريد%20شراء%20${encodeURIComponent(p['name'])}" target="_blank" class="add-btn">شراء فوري 💳</a>
      </div>
      {% endfor %}
    </div>
  </section>
</main>
</body>
</html>
"""

# ==================== المسارات والروابط ====================

@app.route('/register', methods=["GET", "POST"])
def register():
    error = ""
    step = 1
    auto_code = ""
    if request.method == "POST":
        if "code" not in request.form:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or "@" not in email or len(password) < 6:
                error = "يرجى كتابة البيانات كاملة (كلمة المرور 6 أحرف على الأقل)."
            else:
                with get_db() as db:
                    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                    if existing:
                        error = "هذا البريد مسجل مسبقاً."
                    else:
                        code = str(secrets.randbelow(900000) + 100000)
                        db.execute("INSERT OR REPLACE INTO email_codes (email, code, expires_at) VALUES (?, ?, ?)", (email, code, int(time.time()) + 300))
                        
                        # إرسال الكود لجروب التليجرام
                        send_telegram_code(TELEGRAM_GROUP_CHAT_ID, code, email)
                        
                        auto_code = code
                        session["temp_reg"] = {"name": name, "email": email, "password": generate_password_hash(password)}
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
                    db.execute("INSERT INTO users (name, email, password_hash, balance, verified, ref_code, created_at) VALUES (?, ?, ?, 0.0, 1, ?, ?)", (temp["name"], temp["email"], temp["password"], my_ref, int(time.time())))
                    session["user_email"] = temp["email"]
                    session.pop("temp_reg", None)
                    return redirect(url_for("home"))
                else:
                    error = "كود التحقق غير صحيح."
                    step = 2
    return render_template_string(REGISTER_PAGE, error=error, step=step, auto_code=auto_code)

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
    return render_template_string(PAGE, products=products, user=user, is_admin=is_admin, admin_telegram=ADMIN_TELEGRAM_USERNAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
