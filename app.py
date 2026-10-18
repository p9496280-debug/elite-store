import os
import time
import secrets
import sqlite3
import threading
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

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@novastore.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "nova_store.db")

# 📱 رقم فودافون كاش الخاص بك
ADMIN_VODAFONE_NUMBER = os.environ.get("VODAFONE_NUMBER", "01011541698")

# 🤖 بيانات بوت تيليجرام والمطور
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4")
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", "6110549529")


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

        db.execute("""
            CREATE TABLE IF NOT EXISTS deposit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                amount REAL NOT NULL,
                net_amount REAL NOT NULL,
                phone TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at INTEGER NOT NULL
            )
        """)

        # إنشاء أو تفعيل حساب الأدمن المطور تلقائياً
        admin_user = db.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        if not admin_user:
            db.execute("""
                INSERT INTO users (name, email, password_hash, telegram_id, balance, verified, created_at)
                VALUES (?, ?, ?, ?, 999999.0, 1, ?)
            """, ("المطور (ADMIN)", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), str(ADMIN_TELEGRAM_ID), int(time.time())))
        else:
            db.execute("""
                UPDATE users SET password_hash = ?, verified = 1 WHERE email = ?
            """, (generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL))

        cursor = db.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            default_products = [
                ("Google Play", "بطاقات Google Play الرقمية", 100, "100 جنيه", "GPLAY-9876-XXXX", "▶", "بطاقات الألعاب", "#35eaa1"),
                ("PlayStation", "بطاقات وااشتراكات PlayStation", 250, "250 جنيه", "PSN-5432-XXXX", "PS", "بطاقات الألعاب", "#62a0ff"),
                ("Steam", "أكواد ومحافظ Steam", 150, "150 جنيه", "STEAM-1122-XXXX", "◉", "بطاقات الألعاب", "#9bb8ff"),
                ("Xbox", "بطاقات وااشتراكات Xbox", 200, "200 جنيه", "XBOX-3344-XXXX", "ⓧ", "بطاقات الألعاب", "#5dff9c"),
                ("Google Accounts", "حسابات جوجل جاهزة وموثقة", 50, "50 جنيه", "acc_google_2026@gmail.com : Pass123", "G", "حسابات جوجل", "#ffc107"),
            ]
            db.executemany("""
                INSERT INTO products (name, description, price_val, price, code, icon, category, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, default_products)


init_db()


def send_telegram_msg(chat_id, text, reply_markup=None):
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        app.logger.error("خطأ إرسال رسالة تيليجرام: %s", e)


# ==================== نظام بوت تيليجرام لوحة الإدارة ====================

def run_telegram_bot_polling():
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    
    offset = 0
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

    while True:
        try:
            res = requests.get(base_url + f"getUpdates?offset={offset}&timeout=20", timeout=25)
            data = res.json()
            if not data.get("ok"):
                time.sleep(3)
                continue

            for result in data.get("result", []):
                offset = result["update_id"] + 1

                # 1. التعامل مع الرسائل
                if "message" in result:
                    msg = result["message"]
                    chat_id = str(msg["chat"]["id"])
                    text = msg.get("text", "").strip()

                    if chat_id == str(ADMIN_TELEGRAM_ID):
                        if text in ["/start", "/admin", "لوحة التحكم"]:
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📊 الإحصائيات العامة", "callback_data": "admin_stats"}],
                                    [{"text": "👥 قائمة المستخدمين", "callback_data": "admin_users"}],
                                    [{"text": "💳 طلبات الشحن المعلقة", "callback_data": "admin_deposits"}],
                                    [{"text": "🛒 عرض المنتجات", "callback_data": "admin_products"}]
                                ]
                            }
                            send_telegram_msg(chat_id, "⚙️ *أهلاً بك في لوحة إدارة NOVA STORE المدمجة!*\n\nاختر العملية المطلوبة من القائمة التالية:", keyboard)

                # 2. التعامل مع الضغط على الأزرار (Callback Queries)
                elif "callback_query" in result:
                    cb = result["callback_query"]
                    cb_id = cb["id"]
                    from_id = str(cb["from"]["id"])
                    cb_data = cb.get("data", "")

                    if from_id == str(ADMIN_TELEGRAM_ID):
                        # إحصائيات
                        if cb_data == "admin_stats":
                            with get_db() as db:
                                u_cnt = db.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
                                p_cnt = db.execute("SELECT COUNT(*) as count FROM products").fetchone()["count"]
                                d_cnt = db.execute("SELECT COUNT(*) as count FROM deposit_requests WHERE status='PENDING'").fetchone()["count"]
                            
                            msg_text = f"📊 *إحصائيات المتجر الفورية:*\n\n" \
                                       f"👤 إجمالي عدد المسجلين: `{u_cnt}`\n" \
                                       f"📦 عدد المنتجات المتاحة: `{p_cnt}`\n" \
                                       f"⏳ طلبات الشحن المعلقة: `{d_cnt}`"
                            send_telegram_msg(from_id, msg_text)

                        # قائمة المستخدمين
                        elif cb_data == "admin_users":
                            with get_db() as db:
                                users = db.execute("SELECT name, email, balance FROM users ORDER BY id DESC LIMIT 10").fetchall()
                            txt = "👥 *أحدث 10 مستخدمين مسجلين:*\n\n"
                            for u in users:
                                txt += f"• *{u['name']}* ({u['email']})\n  الرصيد: `{u['balance']} جنيه`\n"
                            send_telegram_msg(from_id, txt)

                        # طلبات الشحن المعلقة
                        elif cb_data == "admin_deposits":
                            with get_db() as db:
                                deps = db.execute("SELECT * FROM deposit_requests WHERE status='PENDING'").fetchall()
                            if not deps:
                                send_telegram_msg(from_id, "✅ لا توجد طلبات شحن معلقة حالياً.")
                            else:
                                for d in deps:
                                    kb = {"inline_keyboard": [[{"text": "✅ إتمام الشحن وإضافة الرصيد", "callback_data": f"approve_dep_{d['id']}"}]]}
                                    m = f"💳 *طلب شحن جديد #DEP-{d['id']}*\n" \
                                        f"👤 البريد: `{d['user_email']}`\n" \
                                        f"💰 المبلغ المحول: `{d['amount']} جنيه`\n" \
                                        f"✨ الصافي للمحفظة: `{d['net_amount']} جنيه`\n" \
                                        f"📞 رقم التحويل: `{d['phone']}`"
                                    send_telegram_msg(from_id, m, kb)

                        # عرض المنتجات
                        elif cb_data == "admin_products":
                            with get_db() as db:
                                prods = db.execute("SELECT name, price FROM products").fetchall()
                            txt = "🛒 *المنتجات المتاحة حالياً:*\n\n"
                            for p in prods:
                                txt += f"• *{p['name']}* — {p['price']}\n"
                            send_telegram_msg(from_id, txt)

                        # الموافقة على شحن الرصيد
                        elif cb_data.startswith("approve_dep_"):
                            dep_id = cb_data.replace("approve_dep_", "")
                            with get_db() as db:
                                dep = db.execute("SELECT * FROM deposit_requests WHERE id = ? AND status = 'PENDING'", (dep_id,)).fetchone()
                                if dep:
                                    db.execute("UPDATE users SET balance = balance + ? WHERE email = ?", (dep["net_amount"], dep["user_email"]))
                                    db.execute("UPDATE deposit_requests SET status = 'APPROVED' WHERE id = ?", (dep_id,))
                                    
                                    # إشعار العميل
                                    u = db.execute("SELECT telegram_id, name FROM users WHERE email = ?", (dep["user_email"],)).fetchone()
                                    if u and u["telegram_id"]:
                                        send_telegram_msg(u["telegram_id"], f"🎉 مبروك يا {u['name']}!\n\nتمت الموافقة على طلب الشحن وإضافة `{dep['net_amount']} جنيه` إلى محفظتك بنجاح! 💰")
                                    
                                    send_telegram_msg(from_id, f"✅ تم تفعيل طلب الشحن #{dep_id} بنجاح وإضافة الرصيد للعميل!")

                        # إغلاق التنبيه
                        requests.post(base_url + "answerCallbackQuery", json={"callback_query_id": cb_id})

        except Exception as e:
            time.sleep(3)


# تشغيل البوت في background thread
threading.Thread(target=run_telegram_bot_polling, daemon=True).start()


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

.layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:20px;padding:22px 3.2% 30px}.main-column{min-width:0}
.hero{min-height:290px;border:1px solid #263f77;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;position:relative;background:radial-gradient(ellipse at 70% 50%,#351174 0,transparent 50%),linear-gradient(110deg,#06102b,#080c2c 65%,#100a3b)}.hero:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,#080b2555);pointer-events:none}.hero-copy{padding:28px 32px;z-index:1}.eyebrow{color:#bca0ff;font-size:12px;font-weight:700}.hero h1{font-size:clamp(22px,2.2vw,31px);line-height:1.65;margin:8px 0;font-weight:800}.hero p{color:#c4cce2;font-size:13px;line-height:1.9;max-width:470px;margin:0 0 15px}.hero-btn{display:inline-flex;align-items:center;gap:20px;padding:11px 22px;border-radius:30px;font-size:13px}.trust-row{display:flex;gap:15px;margin-top:20px;color:#dce5ff;font-size:11px;flex-wrap:wrap}
.hero-art{position:relative;min-height:285px;display:flex;align-items:center;justify-content:center;perspective:700px}.glow{position:absolute;width:260px;height:190px;background:#5533ff;filter:blur(80px);opacity:.6}.gift-card{position:absolute;width:112px;height:158px;border:1px solid #66bfff;border-radius:13px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:15px;box-shadow:0 0 26px #168dff66;font-family:Arial,sans-serif;font-size:12px;transform:rotate(-9deg);background:linear-gradient(145deg,#063c9e,#09132e)}.gift-card span{font-size:36px}.gift-card.google{right:40%;z-index:2;transform:rotate(-15deg);background:linear-gradient(145deg,#113e83,#11153c)}.gplay{color:#35eaa1}.gift-card.playstation{right:23%;top:24px;transform:rotate(8deg);background:linear-gradient(145deg,#0759dd,#111342)}.gift-card.steam{right:6%;top:31px;transform:rotate(13deg);background:linear-gradient(145deg,#122b54,#050b1c)}.gift-card.xbox{right:0;top:83px;transform:rotate(19deg);background:linear-gradient(145deg,#076b38,#09271f);width:96px;height:140px}.gift-card.xbox span{color:#64ff99}.controller{position:absolute;bottom:8px;right:42%;font-size:52px;filter:drop-shadow(0 0 15px #5a53ff)}
.categories{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:11px;margin:18px 0 27px}.category{min-height:112px;border:1px solid #172d53;border-radius:13px;background:linear-gradient(150deg,#07152e,#050d20);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:5px;transition:.2s}.category:hover,.category.active{border-color:#5a54ff;transform:translateY(-2px);background:linear-gradient(150deg,#111d4c,#081126)}.category>span{font-size:25px;color:#65baff;text-shadow:0 0 14px #168dff}.category .c-google{color:#35eaa1}.category .c-xbox{color:#5dff9c}.category b{font-size:12px}.category small{font-size:10px;color:#9eafd0}
.section-heading{display:flex;align-items:center;justify-content:space-between;margin:0 5px 13px}.section-heading>div{display:flex;align-items:center;gap:9px}.section-heading h2{font-size:20px;margin:0}.section-heading a{font-size:12px;color:#8198ff}.fire{color:#ff9a6b;font-size:24px}
.product-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.product-card{border:1px solid #1b3159;background:linear-gradient(150deg,#08152e,#050c1e);border-radius:13px;padding:10px;min-width:0;transition:.2s}.product-card:hover{border-color:#5c52ff;transform:translateY(-3px)}.product-visual{height:105px;border-radius:10px;background:radial-gradient(circle at 50% 20%,var(--product-glow),transparent 60%),#07142c;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}.product-visual .logo{font-size:39px;font-weight:800;color:var(--product-color);text-shadow:0 0 20px var(--product-glow)}.product-visual .product-brand{position:absolute;bottom:10px;font:700 12px Arial,sans-serif}.product-card h3{font-size:12px;margin:10px 0 3px}.product-card p{font-size:10px;color:#8fa1c4;margin:0 0 9px}.price{font-size:14px;font-weight:800;color:#fff;margin-bottom:8px}.add-btn{width:100%;padding:9px 4px;border:0;border-radius:9px;background:linear-gradient(100deg,#933aff,#315dff);font-size:11px;font-weight:700}
.ai-panel{border:1px solid #344b88;border-radius:18px;padding:17px;height:max-content;min-height:420px;background:linear-gradient(155deg,#081735,#060d22);position:sticky;top:145px}.ai-heading{display:flex;align-items:center;gap:12px;margin-bottom:15px}.bot-avatar{width:57px;height:57px;display:grid;place-items:center;border-radius:50%;font-size:30px;color:#b8caff;background:radial-gradient(circle at 35% 25%,#2c8cff,#11175a 65%);border:1px solid #466bff;box-shadow:0 0 24px #2458ff55}.ai-heading h3{margin:0 0 3px;font-size:15px;color:#a99bff}.ai-heading span{font-size:10px;color:#a7b9dc}.ai-heading i{display:inline-block;width:6px;height:6px;border-radius:50%;background:#2fe19a}.ai-message{border:1px solid #1e3c75;border-radius:13px;background:#0a1b42;padding:13px;font-size:12px;line-height:1.9}.ai-message p{color:#c4d1ed;margin:4px 0 0}.ai-quick{display:grid;gap:9px;margin-top:15px}.ai-quick button{border:1px solid #244b91;border-radius:10px;background:#0b2050;padding:10px;font-size:11px;text-align:right}.ai-quick button:hover{background:#132d68}.ai-input{display:flex;gap:7px;align-items:center;border:1px solid #294b91;border-radius:25px;padding:5px;margin-top:22px;background:#081a3c}.ai-input input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:white;padding:6px;font-size:11px}.ai-input button{width:32px;height:32px;border:0;border-radius:50%;background:#4d55ff}.ai-note{font-size:9px;color:#8194ba;line-height:1.6}
footer{border-top:1px solid #192b4e;padding:28px 4.2%;display:grid;grid-template-columns:1.5fr 1fr 1fr 1.4fr;gap:30px;color:#aab9d8;font-size:12px}footer h4{color:#f4f7ff;margin:0 0 12px;font-size:13px}footer>div>a:not(.brand){display:block;margin:6px 0}footer .brand{font-size:21px;color:#fff}footer .brand-mark{width:32px;height:32px;font-size:26px}footer p{line-height:1.8}.socials{display:flex;gap:12px;font-size:20px;color:#7d9bff;margin:10px 0 20px}
.toast{position:fixed;bottom:22px;left:22px;z-index:10;background:#102957;border:1px solid #496cff;padding:12px 18px;border-radius:12px;box-shadow:0 8px 30px #0008;opacity:0;transform:translateY(10px);transition:.25s;pointer-events:none;font-size:13px}.toast.show{opacity:1;transform:translateY(0)}
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
  <form class="ai-input" id="aiForm"><input id="aiText" placeholder="اكتب رسالتك هنا..." autocomplete="off"><button>➤</button></form><p class="ai-note">مساعد تجريبي بقواعد محلية؛ لا ينفذ عمليات شراء أو دفع.</p>
</aside>
</main>
<footer id="footer">
  <div>
    <a class="brand" href="/"><span class="brand-mark">N</span><span>NOVA <b>STORE</b></span></a>
    <p>متجرك الرقمي لبطاقات الدفع وأكواد الألعاب.</p>
  </div>
  <div>
    <h4>روابط سريعة</h4>
    <a href="/">الرئيسية</a>
    <a href="/spin">🎡 عجلة الحظ</a>
  </div>
  <div>
    <small>© 2026 NOVA STORE — جميع الحقوق محفوظة</small>
  </div>
</footer>
<div class="toast" id="toast"></div>
<script>
const PRODUCTS = {{ products|tojson }};
const productGrid = document.getElementById('productGrid');
const searchInput = document.getElementById('searchInput');
const cartCount = document.getElementById('cartCount');
const toast = document.getElementById('toast');
let activeCategory = 'الكل';
let cart = [];

function notify(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2600);
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
}));
renderProducts();
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
body{margin:0;background:radial-gradient(ellipse at center, #0f1c3f 0%, #03091b 100%);color:#fff;font-family:'Cairo',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;overflow-x:hidden;}
.spin-header{text-align:center;margin-bottom:20px}
.spin-header h1{font-size:28px;margin:0;background:linear-gradient(110deg,#bc5bff,#315dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:900}
.wheel-container{position:relative;width:340px;height:340px;display:flex;align-items:center;justify-content:center;margin:20px 0;}
.wheel-outer-ring{position:absolute;inset:-12px;border-radius:50%;border:4px solid #315dff;box-shadow:0 0 35px #8d38ffaa;pointer-events:none;z-index:2;}
.pointer{position:absolute;top:-22px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:16px solid transparent;border-right:16px solid transparent;border-top:28px solid #ff3b3b;z-index:10;}
canvas{width:100%;height:100%;border-radius:50%;transition: transform 5s cubic-bezier(0.15, 0.99, 0.24, 0.99);}
.spin-btn{position:absolute;width:75px;height:75px;border-radius:50%;background:radial-gradient(circle, #9b37ff, #315dff);border:3px solid #fff;color:#fff;font-weight:900;font-size:16px;cursor:pointer;z-index:5;}
.modal{display:none;position:fixed;inset:0;background:#03091bee;backdrop-filter:blur(10px);z-index:100;place-items:center;padding:20px;}
.modal-content{background:linear-gradient(145deg, #07132c, #0b1e47);border:2px solid #35eaa1;border-radius:20px;padding:30px;text-align:center;max-width:360px;width:100%;}
.modal-btn{margin-top:20px;padding:12px 25px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:12px;color:white;font-weight:bold;cursor:pointer}
#confettiCanvas{position:fixed;inset:0;pointer-events:none;z-index:99}
</style>
</head>
<body>
<canvas id="confettiCanvas"></canvas>
<div class="spin-header"><h1>🎡 عجلة الحظ اليومية</h1><p>أدر العجلة واكسب رصيداً فورياً في محفظتك!</p></div>
<div class="wheel-container">
  <div class="pointer"></div>
  <div class="wheel-outer-ring"></div>
  <canvas id="wheel" width="500" height="500"></canvas>
  <button class="spin-btn" id="spinBtn">أَدِرْ!</button>
</div>
<a href="/" style="color:#8198ff;text-decoration:none;margin-top:20px;">← العودة للمتجر الرئيسية</a>

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
    ctx.save();
    ctx.translate(radius, radius);
    ctx.rotate(angle + arc / 2);
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 22px Cairo";
    ctx.fillText(items[i].label, radius - 35, 8);
    ctx.restore();
  }
}
drawWheel();

let isSpinning = false;
spinBtn.addEventListener('click', () => {
  if (isSpinning) return;
  isSpinning = true;
  spinBtn.disabled = true;

  const selectedIndex = Math.floor(Math.random() * numItems);
  const prize = items[selectedIndex];
  const targetDegree = (360 - (selectedIndex * (360 / numItems)) - ((360 / numItems) / 2)) + (360 * 5);
  
  canvas.style.transform = `rotate(${targetDegree}deg)`;

  setTimeout(() => {
    isSpinning = false;
    fetch('/spin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ prize: prize.label, type: prize.type, amount: prize.amount })
    }).then(() => {
      document.getElementById('prizeTitle').textContent = prize.type === 'none' ? 'للأسف!' : '🎉 مبروك!';
      document.getElementById('prizeDesc').textContent = prize.type === 'none' ? 'حاول مرة أخرى.' : `لقد فزت بـ (${prize.label})! تمت إضافة المبلغ لمحفظتك.`;
      resultModal.style.display = 'grid';
    });
  }, 5000);
});
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

                    msg = f"مرحباً {name}!\n\nكود التحقق الخاص بك لتسجيل الدخول في NOVA STORE هو:\n`{code}`"
                    send_telegram_msg(telegram_id, msg)

                    session["verify_email"] = email
                    return redirect(url_for("verify"))

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <title>إنشاء حساب | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:400px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;box-sizing:border-box}
      label{display:block;margin-top:12px;color:#a8b7d8;font-size:13px}
      input{box-sizing:border-box;width:100%;padding:11px;margin-top:5px;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white}
      button{width:100%;padding:13px;margin-top:20px;border:0;border-radius:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;cursor:pointer}
    </style>
    <form method="post">
      <h2 style="text-align:center;">إنشاء حساب جديد</h2>
      <label>الاسم</label><input name="name" required>
      <label>البريد الإلكتروني</label><input type="email" name="email" required>
      <label>كلمة المرور</label><input type="password" name="password" required>
      <label>معرف تيليجرام (Telegram Chat ID)</label><input name="telegram_id" required placeholder="مثال: 123456789">
      <button type="submit">إرسال كود التفعيل لتيليجرام</button>
      {% if error %}<p style="color:#ff7777;text-align:center;">{{ error }}</p>{% endif %}
      <a href="/login" style="color:#9db4ff;display:block;text-align:center;margin-top:10px;">تسجيل الدخول</a>
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
    <title>تأكيد الكود | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:380px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;text-align:center}
      input{width:100%;padding:14px;margin-top:15px;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;text-align:center;font-size:24px;letter-spacing:8px;}
      button{width:100%;padding:13px;margin-top:18px;border:0;border-radius:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;cursor:pointer}
    </style>
    <form method="post">
      <h2>تم إرسال الكود 🤖</h2>
      <p style="color:#a8b7d8;font-size:13px;">افتح بوت تيليجرام الخاص بك للحصول على الكود المكون من 6 أرقام.</p>
      <input name="code" maxlength="6" required autocomplete="off">
      <button type="submit">تأكيد الحساب</button>
      {% if error %}<p style="color:#ff7777;">{{ error }}</p>{% endif %}
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
    <title>تسجيل الدخول | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:400px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;}
      label{display:block;margin-top:12px;color:#a8b7d8;font-size:13px}
      input{box-sizing:border-box;width:100%;padding:11px;margin-top:5px;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white}
      button{width:100%;padding:13px;margin-top:20px;border:0;border-radius:10px;background:linear-gradient(110deg,#9b37ff,#315dff);color:white;font-weight:bold;cursor:pointer}
    </style>
    <form method="post">
      <h2 style="text-align:center;">تسجيل الدخول</h2>
      <label>البريد الإلكتروني</label><input type="email" name="email" required>
      <label>كلمة المرور</label><input type="password" name="password" required>
      <button type="submit">دخول</button>
      {% if error %}<p style="color:#ff7777;text-align:center;">{{ error }}</p>{% endif %}
      <a href="/register" style="color:#9db4ff;display:block;text-align:center;margin-top:10px;">إنشاء حساب جديد</a>
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

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <title>حسابي والمحفظة | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      main{width:100%;max-width:450px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;text-align:center;}
      .profile-avatar { width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #9b37ff, #315dff); display: grid; place-items: center; font-size: 30px; font-weight: bold; margin: 0 auto 15px; border: 2px solid #35eaa1; }
      .wallet-box { background: #0b1734; border: 1px solid #315dff; border-radius: 12px; padding: 15px; margin: 15px 0; }
      a{display:inline-block;margin-top:10px;color:#9db4ff;text-decoration:none;padding:8px 14px;background:#0b1734;border:1px solid #263d70;border-radius:10px;}
    </style>
    <main>
      <div class="profile-avatar">{{ user["name"][:1] }}</div>
      <h2>{{ user["name"] }}</h2>
      <p style="color:#a8b7d8;">{{ user["email"] }}</p>
      
      <div class="wallet-box">
        <h3 style="color:#35eaa1;margin:0 0 5px;">رصيد محفظتك: {{ user["balance"] }} جنيه</h3>
        <a href="/deposit" style="background:#315dff; color:white; border:0;">شحن الرصيد (فودافون كاش)</a>
      </div>

      <div>
        <a href="/spin" style="color:#ffc107;">🎡 عجلة الحظ</a>
        <a href="/">العودة للمتجر</a>
        <a href="/logout" style="background:#571010; border-color:#ff5555; color:#ffcccc;">تسجيل الخروج</a>
      </div>
    </main>
    </html>
    """, user=user)

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

        phone = request.form.get("phone", "").strip()
        net_amount = amount_sent * 0.70

        with get_db() as db:
            cursor = db.execute("""
                INSERT INTO deposit_requests (user_email, amount, net_amount, phone, status, created_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?)
            """, (email, amount_sent, net_amount, phone, int(time.time())))
            dep_id = cursor.lastrowid

        # إرسال إشعار للمطور عبر البوت
        kb = {"inline_keyboard": [[{"text": "✅ إتمام الشحن والتفعيل", "callback_data": f"approve_dep_{dep_id}"}]]}
        msg_text = f"🚨 *طلب شحن جديد بانتظار موافقتك!*\n\n" \
                   f"👤 العميل: `{email}`\n" \
                   f"💰 المبلغ: `{amount_sent} جنيه`\n" \
                   f"✨ الصافي للمحفظة: `{net_amount} جنيه`\n" \
                   f"📞 رقم فودافون كاش: `{phone}`"
        send_telegram_msg(ADMIN_TELEGRAM_ID, msg_text, kb)

        return render_template_string("""
        <!doctype html>
        <html lang="ar" dir="rtl">
        <head><meta charset="utf-8"><title>طلب شحن | NOVA STORE</title></head>
        <body style="background:#03091b;color:white;text-align:center;padding:50px;font-family:Arial;">
            <div style="background:#07132c;padding:30px;border:1px solid #315dff;border-radius:15px;max-width:400px;margin:auto;">
                <h2 style="color:#35eaa1;">تم إرسال طلب الشحن بنجاح! 🚀</h2>
                <p>تم إرسال الإشعار للإدارة، وسيتم إضافة <b>{{ net_amount }} جنيه</b> صافي لمستحقات محفظتك فور التأكيد.</p>
                <a href="/account" style="color:#9db4ff; text-decoration:none;">العودة للحساب</a>
            </div>
        </body>
        </html>
        """, net_amount=net_amount)

    return render_template_string("""
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta charset="utf-8">
    <title>شحن المحفظة | NOVA STORE</title>
    <style>
      body{margin:0;background:#03091b;color:white;font-family:Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
      form{width:100%;max-width:380px;background:#07132c;padding:25px;border:1px solid #315dff;border-radius:18px;}
      input{width:100%;padding:12px;margin:10px 0;background:#03091b;border:1px solid #263d70;border-radius:9px;color:white;box-sizing:border-box;}
      button{width:100%;padding:13px;background:linear-gradient(110deg,#9b37ff,#315dff);border:0;border-radius:10px;color:white;font-weight:bold;cursor:pointer;}
    </style>
    <form method="POST">
      <h2>شحن رصيد المحفظة 💳</h2>
      <p style="font-size:12px; color:#a8b7d8;">حول المبلغ لرقم فودافون كاش التالي:</p>
      <div style="background:#03091b; border:1px solid #ff3b3b; padding:12px; text-align:center; color:#ff5555; font-weight:bold;">{{ vodafone_number }}</div>
      
      <label style="display:block;margin-top:10px;font-size:12px;">المبلغ المراد تحويله</label>
      <input type="number" name="amount" required placeholder="مثال: 10">
      <label style="display:block;font-size:12px;">رقم فودافون كاش المحول منه</label>
      <input type="text" name="phone" required placeholder="01xxxxxxxx">
      <button type="submit">إرسال طلب الشحن</button>
      <a href="/account" style="display:block;text-align:center;margin-top:15px;color:#9db4ff;text-decoration:none;">إلغاء</a>
    </form>
    </html>
    """, vodafone_number=ADMIN_VODAFONE_NUMBER)

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

            if user["telegram_id"]:
                msg = f"🎉 مبروك يا {user['name']}!\n\nلقد ربحت {prize} من عجلة الحظ وتمت إضافة المبلغ إلى محفظتك بنجاح! 💰"
                send_telegram_msg(user["telegram_id"], msg)

        return jsonify({"status": "success", "new_balance": user["balance"] + amount})

    return render_template_string(SPIN_PAGE, user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/")
def home():
    email = session.get("user_email")
    user = None
    if email:
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    products = get_products()
    return render_template_string(PAGE, products=products, user=user)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
