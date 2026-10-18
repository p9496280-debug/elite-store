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
                created_at INTEGER NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL,
                icon TEXT NOT NULL,
                category TEXT NOT NULL,
                badge TEXT
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
                ("VPN Pro", "تصفح آمن وسريع", "$8.00", "🛡️", "أدوات", "الأكثر مبيعاَ"),
                ("ChatGPT Plus", "الوصول إلى الذكاء الاصطناعي المتقدم", "$12.00", "🤖", "الذكاء الاصطناعي", "مميز"),
                ("YouTube Premium", "بدون إعلانات نهائياً", "$10.00", "▶️", "ترفيه", None),
                ("PUBG Mobile", "شحن شدات فورية", "$15.00", "🎮", "ألعاب", "شائع"),
                ("Roblox", "شحن Robux أونلاين", "$10.00", "🕹️", "ألعاب", None)
            ]
            db.executemany("""
                INSERT INTO products (name, description, price, icon, category, badge)
                VALUES (?, ?, ?, ?, ?, ?)
            """, default_products)


init_db()


def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in rows]


# ==================== تصميم عصري وبسيط (Minimal & Clean) ====================
PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA STORE | المتجر الرقمي</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
:root{--bg:#030712;--panel:#0b132b;--text:#f3f4f6;--primary:#3b82f6;--border:#1e293b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:'Cairo',sans-serif}
.header{height:70px;padding:0 5%;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);background:#030712cc;backdrop-filter:blur(10px);position:sticky;top:0;z-index:10}
.logo{font-size:20px;font-weight:700;color:#fff;text-decoration:none;display:flex;align-items:center;gap:8px}
.logo span{color:var(--primary)}
.nav-links{display:flex;gap:20px;font-size:13px;align-items:center}
.nav-links a{color:#9ca3af;text-decoration:none;cursor:pointer;transition:0.2s}
.nav-links a:hover{color:#fff}
.container{max-width:1100px;margin:30px auto;padding:0 20px}
.hero-clean{background:linear-gradient(135deg,#0b132b,#0f172a);border:1px solid var(--border);border-radius:16px;padding:40px;text-align:center;margin-bottom:30px}
.hero-clean h1{font-size:24px;margin:0 0 10px;color:#fff}
.hero-clean p{color:#9ca3af;font-size:13px;margin:0 0 20px}
.btn-main{padding:10px 24px;background:var(--primary);color:#fff;border:0;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer;text-decoration:none;display:inline-block}
.section-title{font-size:16px;margin-bottom:15px;color:#fff;border-right:3px solid var(--primary);padding-right:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:15px;text-align:center;transition:0.2s;position:relative}
.card:hover{border-color:var(--primary);transform:translateY(-2px)}
.card-icon{font-size:32px;margin-bottom:10px;cursor:pointer}
.card h3{font-size:13px;margin:5px 0;color:#fff;cursor:pointer}
.card p{font-size:11px;color:#9ca3af;margin:0 0 12px}
.card-footer{display:flex;align-items:center;justify-content:space-between;margin-top:10px;border-top:1px solid var(--border);padding-top:10px}
.price{font-size:13px;font-weight:700;color:#34d399}
.buy-btn{padding:5px 12px;background:#2563eb;color:#fff;border:0;border-radius:6px;font-size:11px;cursor:pointer}
.badge{position:absolute;top:10px;left:10px;background:#ef4444;color:#fff;font-size:9px;padding:2px 6px;border-radius:4px}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(80px);background:#1e293b;border:1px solid #3b82f6;color:#fff;padding:12px 20px;border-radius:8px;font-size:12px;transition:0.3s;opacity:0;z-index:100}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
footer{text-align:center;padding:25px;border-top:1px solid var(--border);color:#6b7280;font-size:11px;margin-top:50px}
</style>
</head>
<body>

<div class="toast" id="maintToast">🛠️ عذراً، المتجر في حالة صيانة وتحديث حالياً. عودوا قريباً!</div>

<header class="header">
  <a href="/" class="logo">NOVA <span>STORE</span></a>
  <nav class="nav-links">
    <a onclick="showMaint()">الرئيسية</a>
    <a onclick="showMaint()">الخدمات</a>
    <a onclick="showMaint()">الألعاب</a>
    <a onclick="showMaint()">الدعم</a>
    {% if is_admin %}
      <a href="/admin" style="color:#f59e0b;font-weight:600;">لوحة التحكم</a>
    {% endif %}
  </nav>
</header>

<div class="container">
  <div class="hero-clean">
    <h1>متجرك الرقمي البسيط والموثوق</h1>
    <p>أفضل الخدمات، التطبيقات، وأكواد الألعاب بأسعار مميزة وتسليم فوري.</p>
    <a class="btn-main" onclick="showMaint()">تصفح المنتجات</a>
  </div>

  <div class="section-title">أحدث المنتجات والخدمات</div>
  <div class="grid" id="productGrid"></div>
</div>

<footer>
  2026 NOVA STORE - جميع الحقوق محفوظة
</footer>

<script>
function showMaint() {
  const t = document.getElementById('maintToast');
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

const PRODUCTS = {{ products|tojson }};
const grid = document.getElementById('productGrid');

PRODUCTS.forEach(p => {
  const card = document.createElement('div');
  card.className = 'card';
  const badgeHtml = p.badge ? `<span class="badge">${p.badge}</span>` : '';
  card.innerHTML = `
    ${badgeHtml}
    <div class="card-icon" onclick="showMaint()">${p.icon}</div>
    <h3 onclick="showMaint()">${p.name}</h3>
    <p>${p.description}</p>
    <div class="card-footer">
      <span class="price">${p.price}</span>
      <button class="buy-btn" onclick="showMaint()">طلب الآن</button>
    </div>
  `;
  grid.appendChild(card);
});
</script>
</body>
</html>
"""

# ==================== لوحة التحكم المبسطة للمطور ====================
ADMIN_PAGE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لوحة التحكم | NOVA STORE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600&display=swap');
body{margin:0;background:#030712;color:#fff;font-family:'Cairo',sans-serif;padding:30px}
.box{background:#0b132b;border:1px solid #1e293b;border-radius:12px;padding:20px;max-width:450px;margin:auto}
input{width:100%;padding:10px;margin:8px 0;background:#030712;border:1px solid #1e293b;border-radius:6px;color:#fff;box-sizing:border-box}
button{width:100%;padding:11px;background:#2563eb;color:#fff;border:0;border-radius:6px;font-weight:600;cursor:pointer}
</style>
</head>
<body>
<div style="max-width:450px;margin:auto;display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
  <h3>⚙️ لوحة المطور البسيطة</h3>
  <a href="/" style="color:#60a5fa;text-decoration:none;font-size:12px;">← المتجر</a>
</div>
<div class="box">
  <form method="POST">
    <input name="name" placeholder="اسم المنتج" required>
    <input name="description" placeholder="الوصف" required>
    <input name="price" placeholder="السعر (مثال: $10.00)" required>
    <input name="icon" placeholder="الأيقونة (Emoji مثل 🎮)" required>
    <input name="category" placeholder="القسم" required>
    <input name="badge" placeholder="الشارة (اختياري)">
    <button type="submit">إضافة المنتج</button>
  </form>
</div>
</body>
</html>
"""

@app.route("/admin", methods=["GET", "POST"])
def admin():
    email = session.get("user_email")
    if not email or email != ADMIN_EMAIL:
        return redirect(url_for("home"))
    
    if request.method == "POST":
        name = request.form.get("name")
        desc = request.form.get("description")
        price = request.form.get("price")
        icon = request.form.get("icon")
        cat = request.form.get("category")
        badge = request.form.get("badge")
        
        with get_db() as db:
            db.execute("INSERT INTO products (name, description, price, icon, category, badge) VALUES (?, ?, ?, ?, ?, ?)",
                       (name, desc, price, icon, cat, badge))
        return redirect(url_for("admin"))
        
    return render_template_string(ADMIN_PAGE)

@app.route("/")
def home():
    email = session.get("user_email")
    is_admin = (email == ADMIN_EMAIL)
    products = get_products()
    return render_template_string(PAGE, products=products, is_admin=is_admin)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
