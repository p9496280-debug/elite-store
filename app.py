import os
import sqlite3
import secrets
import random
import json
import urllib.parse
import urllib.request
from email.message import EmailMessage
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

# =========================================================
# MIDO NOVA | Digital Store
# Run: python app.py
# Optional environment variables:
#   SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD, PORT
# Telegram OTP token is configured in TELEGRAM_BOT_TOKEN below.
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
DB_PATH = os.environ.get("DATABASE_PATH", "mido_nova.db")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "moh99zzhvni893fj7@gmail.com").lower()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "mohammedaaa222")
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
# ضع توكن البوت الذي أنشأته من BotFather هنا بين علامتي الاقتباس.
# لا تشارك هذا الملف علنًا بعد وضع التوكن الحقيقي بداخله.
TELEGRAM_BOT_TOKEN = "8377094717:AAEb-H7GhAZ7qBcKXDtg6QLehJRlN5264-4"
# اسم القناة العامة أو رقم Chat ID، والبوت لازم يكون مشرفًا فيها.
TELEGRAM_CHAT_ID = "@MidoWorld"
VODAFONE_CASH_NUMBER = os.environ.get("VODAFONE_CASH_NUMBER", "01011541698")


CATEGORIES = [
    ("all", "كل المنتجات", "✦"),
    ("google", "Google Play", "▶"),
    ("games", "الألعاب", "🎮"),
    ("digital", "الخدمات الرقمية", "☁"),
    ("products", "المنتجات", "▣"),
    ("crypto", "العملات الرقمية", "₿"),
]

SEED_PRODUCTS = [
    ("Google Play $10", "google", "بطاقة رقمية", 499, "▶", "الأكثر طلبًا", "بطاقات Google Play حسب المنطقة والتوفر."),
    ("Google Play $25", "google", "بطاقة رقمية", 1199, "▶", "عرض مميز", "بطاقات Google Play حسب المنطقة والتوفر."),
    ("Steam Wallet $20", "games", "بطاقة ألعاب", 999, "◉", "للجيمرز", "اشحن محفظة Steam بكود صالح للمنطقة المحددة."),
    ("PlayStation Store $20", "games", "بطاقة ألعاب", 999, "△", "", "بطاقات متجر PlayStation حسب المنطقة والتوفر."),
    ("Xbox Gift Card $25", "games", "بطاقة ألعاب", 1249, "✕", "", "بطاقات Xbox الرقمية حسب المنطقة والتوفر."),
    ("اشتراك أدوات رقمية", "digital", "خدمة رقمية", 299, "✧", "جديد", "خدمات رقمية يتم توضيح تفاصيلها قبل الشراء."),
    ("سماعة لاسلكية", "products", "منتج فعلي", 1499, "♫", "", "منتج تجريبي للعرض — حدّث التفاصيل والمخزون قبل البيع."),
    ("لوحة مفاتيح Gaming", "products", "منتج فعلي", 2199, "⌨", "", "منتج تجريبي للعرض — حدّث التفاصيل والمخزون قبل البيع."),
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            category TEXT NOT NULL, kind TEXT NOT NULL, price INTEGER NOT NULL,
            icon TEXT DEFAULT '✦', badge TEXT DEFAULT '', description TEXT DEFAULT '',
            active INTEGER DEFAULT 1)""")
        con.execute("""CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1,
            total INTEGER NOT NULL, status TEXT DEFAULT 'قيد المراجعة',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'خبر', image TEXT DEFAULT '', active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS discount_codes(
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
            percent INTEGER NOT NULL, uses_left INTEGER NOT NULL DEFAULT 100,
            active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS otp_codes(
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, code_hash TEXT NOT NULL,
            purpose TEXT NOT NULL, payload TEXT DEFAULT '', expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        # Additive migrations for databases created by an earlier version.
        for column, definition in [
            ("payment_method", "TEXT DEFAULT 'غير محدد'"),
            ("payment_reference", "TEXT DEFAULT ''"),
            ("discount_code", "TEXT DEFAULT ''"),
            ("discount_amount", "INTEGER DEFAULT 0")
        ]:
            try:
                con.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError:
                pass
        count = con.execute("SELECT COUNT(*) n FROM products").fetchone()["n"]
        if count == 0:
            con.executemany("""INSERT INTO products(name,category,kind,price,icon,badge,description)
                VALUES(?,?,?,?,?,?,?)""", SEED_PRODUCTS)
        # Admin account is created from environment settings; change defaults in production.
        admin = con.execute("SELECT id FROM users WHERE email=?", (ADMIN_EMAIL,)).fetchone()
        if not admin:
            con.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                        ("Mido ADMIN", ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD)))

init_db()

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with db() as con:
        return con.execute("SELECT id,name,email FROM users WHERE id=?", (uid,)).fetchone()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user["email"].lower() != ADMIN_EMAIL:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

def send_otp_email(to_email, code, purpose="تأكيد الحساب"):
    """Send OTP through Resend HTTP API (avoids outbound SMTP restrictions on hosting)."""
    if not RESEND_API_KEY:
        raise RuntimeError("إعداد RESEND_API_KEY غير موجود في Environment على Render.")

    payload = {
        "from": f"MIDO NOVA <{RESEND_FROM_EMAIL}>",
        "to": [to_email],
        "subject": f"MIDO NOVA | {purpose}",
        "text": (
            f"مرحبًا بك في MIDO NOVA\n\n"
            f"رمز التحقق الخاص بك هو: {code}\n\n"
            "ينتهي الرمز خلال 10 دقائق. لا تشاركه مع أي شخص.\n"
            "إذا لم تطلب هذا الرمز، يمكنك تجاهل الرسالة."
        ),
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f"Resend returned HTTP {response.status}")
            response.read()
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[:500]
        app.logger.error("Resend email API rejected request: HTTP %s: %s", exc.code, details)
        raise RuntimeError(f"Resend رفض إرسال البريد (HTTP {exc.code}). راجع إعدادات المرسل والدومين.") from exc
    except urllib.error.URLError as exc:
        app.logger.error("Cannot reach Resend email API: %s", exc.reason)
        raise RuntimeError("تعذر الاتصال بخدمة Resend API من الاستضافة.") from exc


def send_telegram_message(message):
    """Send a message directly through Telegram Bot API from this app.py."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("ضع توكن البوت الحقيقي في متغير TELEGRAM_BOT_TOKEN داخل app.py.")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("حدد قناة تيليجرام في TELEGRAM_CHAT_ID.")
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status != 200 or not result.get("ok"):
                raise RuntimeError("Telegram API لم يقبل رسالة كود التحقق.")
            return result
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[:250]
        app.logger.error("Telegram API HTTP %s: %s", exc.code, details)
        raise RuntimeError("فشل إرسال الرسالة إلى تيليجرام. تأكد من التوكن وصلاحيات البوت في القناة.") from exc
    except urllib.error.URLError as exc:
        app.logger.error("Cannot reach Telegram API: %s", exc.reason)
        raise RuntimeError("الاستضافة لا تستطيع الاتصال بتيليجرام حاليًا.") from exc


def request_telegram_otp(name, email):
    """Generate a one-time signup code and publish it to the configured channel."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    message = (
        "🔐 كود تأكيد حساب جديد | MIDO NOVA\n\n"
        f"👤 الاسم: {name}\n"
        f"📧 البريد: {email}\n"
        f"🔢 كود التحقق: {code}\n\n"
        "⏳ صلاحية الكود 10 دقائق، ويُستخدم مرة واحدة فقط."
    )
    send_telegram_message(message)
    return code, 600


def notify_telegram(message):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return False
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception:
        app.logger.exception("Telegram notification failed")
        return False

BASE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#07110f">
<title>{{ title }} | MIDO NOVA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#07100f;--panel:#0d1917;--panel2:#10211e;--line:#1d3933;--mint:#39edbd;--mint2:#12b98b;--text:#f1fbf7;--muted:#91aaa1;--gold:#d9ff72;--danger:#ff7373}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% -10%,#124b3b66,transparent 42%),radial-gradient(ellipse at 0% 40%,#0d2825,transparent 34%),var(--bg);color:var(--text);font-family:'Cairo',sans-serif;min-height:100vh}
a{color:inherit;text-decoration:none}button,input,select{font:inherit}.wrap{max-width:1190px;margin:auto;padding:0 20px}
.topbar{position:sticky;top:0;z-index:20;background:#07100feF;border-bottom:1px solid #1b302b;backdrop-filter:blur(18px)}
.nav{height:78px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{display:flex;align-items:center;gap:11px;font-weight:900;font-size:23px;letter-spacing:-.5px}.mark{width:43px;height:43px;border:1px solid #46f5c5;border-radius:15px;display:grid;place-items:center;color:var(--mint);font-size:24px;font-weight:900;background:linear-gradient(145deg,#1b5545,#0a1513);box-shadow:0 0 24px #2be5b21c}.brand span{color:var(--mint)}.navlinks{display:flex;gap:22px;color:#b8cbc4;font-size:13px}.navlinks a:hover{color:var(--mint)}.navactions{display:flex;align-items:center;gap:9px}.btn{border:1px solid var(--line);background:#11221e;color:var(--text);border-radius:13px;padding:10px 15px;cursor:pointer;display:inline-flex;justify-content:center;align-items:center;gap:7px;font-weight:700;transition:.2s}.btn:hover{transform:translateY(-2px);border-color:#3ce3b3}.btn.primary{background:linear-gradient(120deg,#46f3c0,#12b78a);color:#042219;border:0;box-shadow:0 8px 25px #20c79522}.btn.small{font-size:12px;padding:8px 12px}.menu-toggle{display:none}
.hero{padding:53px 0 28px;display:grid;grid-template-columns:1.15fr .85fr;gap:28px;align-items:center}.eyebrow{display:inline-flex;gap:8px;align-items:center;color:var(--mint);border:1px solid #245748;background:#0b211b;border-radius:99px;padding:6px 13px;font-size:12px;font-weight:800}.dot{width:7px;height:7px;border-radius:50%;background:var(--mint);box-shadow:0 0 12px var(--mint)}h1{font-size:clamp(35px,5vw,58px);line-height:1.25;margin:17px 0 12px;font-weight:900;letter-spacing:-1.5px}.gradient{background:linear-gradient(90deg,#f5fff9,#4af2c0 75%);background-clip:text;color:transparent}.hero p{color:#9bb5ab;line-height:2;font-size:15px;max-width:590px}.hero-ctas{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}.trust{display:flex;gap:18px;flex-wrap:wrap;color:#8fa69d;font-size:12px}.trust b{color:#e5fff5}.showcase{position:relative;min-height:315px;border:1px solid #255347;border-radius:28px;padding:22px;background:linear-gradient(140deg,#102b24,#0b1514 68%);overflow:hidden;box-shadow:inset 0 1px #ffffff08,0 20px 70px #0005}.showcase:before{content:"";position:absolute;width:270px;height:270px;background:#20e2a422;filter:blur(70px);border-radius:50%;top:0;left:10%}.showtop{display:flex;justify-content:space-between;align-items:center;color:#92b8aa;font-size:12px;position:relative}.bigcoin{position:relative;margin:24px auto 20px;width:142px;height:142px;border-radius:42px;display:grid;place-items:center;font-size:74px;color:#caffee;border:1px solid #4af4c2;background:linear-gradient(145deg,#174c3e,#091512);box-shadow:0 0 65px #23dba52b;transform:rotate(-7deg)}.showfoot{position:relative;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #24443a;padding-top:16px}.showfoot strong{font-size:20px}.pill{background:#133a2e;color:#6df6c9;border:1px solid #24624d;border-radius:50px;padding:5px 10px;font-size:11px}
.section{padding:28px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:15px;margin-bottom:18px}.section-head h2{margin:0;font-size:25px}.section-head p{color:var(--muted);margin:3px 0 0;font-size:12px}.categories{display:grid;grid-template-columns:repeat(6,1fr);gap:11px}.cat{padding:17px 12px;background:linear-gradient(145deg,#10211d,#0a1513);border:1px solid var(--line);border-radius:18px;text-align:center;transition:.2s}.cat:hover{border-color:#3bdcae;transform:translateY(-3px)}.cat-icon{margin:0 auto 9px;width:47px;height:47px;display:grid;place-items:center;border-radius:15px;background:#17372d;color:var(--mint);font-size:24px}.cat strong{display:block;font-size:13px}.cat small{color:#7e9b90;font-size:10px}
.toolbar{display:flex;gap:10px;margin:18px 0;flex-wrap:wrap}.search{flex:1;min-width:190px;background:#0d1b18;border:1px solid #234039;color:white;padding:12px 15px;border-radius:14px;outline:none}.search:focus{border-color:var(--mint)}.filter{background:#0d1b18;color:#bcd0c7;border:1px solid #234039;border-radius:13px;padding:10px 13px}
.products{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.product{border:1px solid #1d3831;background:linear-gradient(145deg,#10201c,#0b1513);border-radius:19px;padding:14px;transition:.2s;position:relative;overflow:hidden}.product:hover{transform:translateY(-4px);border-color:#337b61;box-shadow:0 15px 30px #0002}.prodvisual{height:123px;border-radius:14px;background:radial-gradient(circle at 50% 20%,#24654c,#102a22 55%,#0b1714);display:grid;place-items:center;font-size:53px;color:#7cfbd0;position:relative}.badge{position:absolute;top:10px;right:10px;border-radius:30px;padding:3px 8px;background:#caff72;color:#152513;font-size:10px;font-weight:900}.prodtype{font-size:10px;color:#79b6a0;margin:13px 0 2px}.product h3{font-size:15px;margin:0 0 5px}.product p{font-size:11px;color:#89a59a;min-height:40px;line-height:1.8;margin:0 0 13px}.prodfoot{display:flex;justify-content:space-between;align-items:center;gap:6px;border-top:1px solid #203830;padding-top:12px}.price{font-size:17px;font-weight:900;color:#e8fff5}.price small{font-size:10px;color:#91a99f;font-weight:500}.empty{grid-column:1/-1;padding:35px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:18px}
.benefits{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.benefit{border:1px solid var(--line);background:#0c1916;border-radius:17px;padding:19px;display:flex;gap:13px}.benefit i{font-style:normal;font-size:23px;color:var(--mint)}.benefit b{font-size:13px}.benefit p{font-size:11px;color:var(--muted);margin:4px 0 0;line-height:1.8}
.footer{margin-top:45px;border-top:1px solid #1b302b;padding:26px 0;color:#779188;font-size:11px}.footerinner{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}.flash{margin:12px auto;padding:12px 15px;border:1px solid #286b51;background:#10271f;border-radius:12px;color:#9effd5;font-size:13px}.notice{font-size:11px;line-height:1.9;color:#7e9a90;border:1px solid #1b3930;background:#0b1714;border-radius:14px;padding:13px;margin-top:18px}
.formcard{max-width:510px;margin:48px auto;background:#0d1a17;border:1px solid var(--line);border-radius:22px;padding:25px}.formcard h1{font-size:27px;margin:0 0 8px}.formcard p{color:var(--muted);font-size:13px}.field{display:block;margin:14px 0;color:#a9c0b7;font-size:12px}.field input,.field select{display:block;width:100%;margin-top:7px;border:1px solid #29463d;background:#08120f;color:#fff;padding:12px;border-radius:12px;outline:none}.field input:focus{border-color:var(--mint)}.formcard .btn{width:100%;margin-top:10px}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:15px}table{width:100%;border-collapse:collapse;min-width:650px}th,td{text-align:right;padding:13px;border-bottom:1px solid #1b322b;font-size:12px}th{color:var(--mint);background:#10211c}td{color:#d9e9e2}.status{color:#baffdf}
@media(max-width:900px){.hero{grid-template-columns:1fr}.showcase{min-height:270px}.categories{grid-template-columns:repeat(3,1fr)}.products{grid-template-columns:repeat(2,1fr)}.navlinks{display:none}.benefits{grid-template-columns:1fr}}
@media(max-width:520px){.wrap{padding:0 13px}.nav{height:67px}.brand{font-size:19px}.mark{width:38px;height:38px}.navactions .btn{padding:8px 10px;font-size:11px}.hero{padding-top:32px}h1{font-size:37px}.showcase{min-height:255px}.categories{gap:8px}.cat{padding:13px 5px}.cat strong{font-size:11px}.products{gap:9px}.product{padding:9px}.prodvisual{height:95px;font-size:43px}.product h3{font-size:13px}.product p{font-size:10px}.prodfoot{align-items:flex-start;flex-direction:column}.prodfoot .btn{width:100%}.section-head h2{font-size:21px}}
</style>
</head>
<body>
<header class="topbar"><div class="wrap nav">
<a class="brand" href="{{ url_for('home') }}"><div class="mark">M</div><div>MIDO <span>NOVA</span></div></a>
<nav class="navlinks"><a href="{{ url_for('home') }}">الرئيسية</a><a href="{{ url_for('home') }}#categories">الأقسام</a><a href="{{ url_for('home') }}#products">المتجر</a><a href="{{ url_for('my_orders') }}">طلباتي</a></nav>
<div class="navactions">
{% if user %}<a class="btn small" href="{{ url_for('my_orders') }}">طلباتي</a><a class="btn primary small" href="{{ url_for('logout') }}">خروج</a>
{% else %}<a class="btn small" href="{{ url_for('login') }}">دخول</a><a class="btn primary small" href="{{ url_for('register') }}">حساب جديد</a>{% endif %}
</div>
</div></header>
<main class="wrap">
{% for msg in get_flashed_messages() %}<div class="flash">{{ msg }}</div>{% endfor %}
{{ body|safe }}
</main>
<footer class="footer"><div class="wrap footerinner"><div>© {{ year }} MIDO NOVA — كل احتياجاتك الرقمية في مكان واحد.</div><div style="display:flex;gap:14px;flex-wrap:wrap"><a href="https://t.me/Mido_M9do" target="_blank" rel="noopener">✦ المطور</a><a href="https://t.me/Midomsn" target="_blank" rel="noopener">◉ القناة الرسمية</a><a href="https://t.me/midoassistantAIbot" target="_blank" rel="noopener">✧ البوت</a></div></div></footer>
</body></html>
"""

HOME = r"""
<section class="hero">
<div>
<div class="eyebrow"><span class="dot"></span> وجهتك الرقمية الجديدة</div>
<h1>كل اللي تحتاجه<br><span class="gradient">في مكان واحد.</span></h1>
<p>اكتشف البطاقات الرقمية، وشحن الألعاب، والخدمات، والمنتجات — بتجربة شراء مرتبة وسهلة من MIDO NOVA.</p>
<div class="hero-ctas"><a class="btn primary" href="#products">اكتشف المتجر <span>←</span></a><a class="btn" href="#categories">تصفح الأقسام ◈</a></div>
<div class="trust"><span>✦ <b>واجهة سهلة</b></span><span>◉ <b>تفاصيل واضحة</b></span><span>⌁ <b>متابعة الطلبات</b></span></div>
</div>
<div class="showcase"><div class="showtop"><span>✦ MIDO NOVA</span><span class="pill">متجرك الرقمي</span></div><div class="bigcoin">M</div><div class="showfoot"><div><small style="color:#8aa99b">EVERYTHING IN ONE PLACE</small><br><strong>ابدأ اكتشافك</strong></div><span class="pill">آمن • بسيط • أنيق</span></div></div>
</section>
<section class="section" id="categories"><div class="section-head"><div><h2>تصفح الأقسام</h2><p>اختار القسم اللي يناسبك</p></div></div>
<div class="categories">{% for key,name,icon in categories %}{% if key != 'all' %}<a class="cat" href="#products" onclick="pickCategory('{{key}}')"><div class="cat-icon">{{icon}}</div><strong>{{name}}</strong><small>اكتشف المزيد ←</small></a>{% endif %}{% endfor %}</div></section>
{% if posts %}<section class="section" id="news"><div class="section-head"><div><h2>الأخبار والتحديثات <span style="color:var(--mint)">✦</span></h2><p>آخر أخبار MIDO NOVA</p></div></div><div class="products">{% for post in posts %}<article class="product">{% if post.image %}<img src="{{post.image}}" alt="" style="width:100%;height:120px;object-fit:cover;border-radius:12px">{% else %}<div class="prodvisual">✧</div>{% endif %}<div class="prodtype">{{post.kind}}</div><h3>{{post.title}}</h3><p style="white-space:pre-line">{{post.body}}</p></article>{% endfor %}</div></section>{% endif %}
<section class="section" id="products"><div class="section-head"><div><h2>اختيارات مميزة <span style="color:var(--mint)">✦</span></h2><p>منتجات وخدمات متنوعة في انتظارك</p></div><span class="pill">{{ products|length }} منتج</span></div>
<div class="toolbar"><input class="search" id="searchBox" placeholder="ابحث عن منتج أو خدمة..." oninput="filterProducts()"><select class="filter" id="categoryFilter" onchange="filterProducts()">{% for key,name,icon in categories %}<option value="{{key}}">{{name}}</option>{% endfor %}</select></div>
<div class="products" id="productGrid">
{% for p in products %}<article class="product" data-name="{{p.name|lower}}" data-category="{{p.category}}">
<div class="prodvisual">{% if p.badge %}<span class="badge">{{p.badge}}</span>{% endif %}{{p.icon}}</div><div class="prodtype">{{p.kind}}</div><h3>{{p.name}}</h3><p>{{p.description}}</p><div class="prodfoot"><div class="price">{{ '{:,.0f}'.format(p.price/100) }} <small>ج.م</small></div><form method="post" action="{{url_for('order_product', product_id=p.id)}}" style="display:grid;gap:5px"><input name="discount_code" placeholder="كود الخصم (اختياري)" style="width:100%;min-width:0;background:#08120f;color:white;border:1px solid #29463d;border-radius:9px;padding:7px;font-size:10px"><input name="payment_reference" placeholder="مرجع التحويل (بعد الدفع)" style="width:100%;min-width:0;background:#08120f;color:white;border:1px solid #29463d;border-radius:9px;padding:7px;font-size:10px"><button class="btn primary small" type="submit">اطلب عبر فودافون كاش +</button></form></div>
</article>{% else %}<div class="empty">لا توجد منتجات حاليًا.</div>{% endfor %}
</div>
<div class="notice">الدفع اليدوي: فودافون كاش على الرقم {{vodafone_number}}. المنتجات المعروضة بيانات تجريبية قابلة للتعديل. لا يتم تنفيذ دفع إلكتروني أو تسليم أكواد تلقائيًا في هذا الإصدار. تأكد من السعر والمنطقة وشروط المنتج قبل إتمام أي عملية. العملات الرقمية هنا قسم تعريفي فقط وليست خدمة تداول.</div>
</section>
<section class="section"><div class="section-head"><div><h2>تجربة معمولة ليك</h2><p>كل حاجة واضحة من أول خطوة</p></div></div><div class="benefits">
<div class="benefit"><i>◈</i><div><b>تنظيم ذكي</b><p>أقسام واضحة تساعدك توصل للي بتدور عليه بسرعة.</p></div></div>
<div class="benefit"><i>↗</i><div><b>متابعة طلباتك</b><p>راجع طلباتك وحالتها من حسابك في أي وقت.</p></div></div>
<div class="benefit"><i>♧</i><div><b>تجربة شفافة</b><p>تفاصيل وأسعار واضحة، مع تطوير بوابات الدفع لاحقًا.</p></div></div>
</div></section>
<script>
function filterProducts(){const q=document.getElementById('searchBox').value.toLowerCase().trim(),c=document.getElementById('categoryFilter').value;let shown=0;document.querySelectorAll('.product').forEach(p=>{const ok=(c==='all'||p.dataset.category===c)&&p.dataset.name.includes(q);p.style.display=ok?'':'none';if(ok)shown++});let e=document.getElementById('noProducts');if(!shown){if(!e){e=document.createElement('div');e.id='noProducts';e.className='empty';e.textContent='مفيش نتائج مطابقة لبحثك.';document.getElementById('productGrid').appendChild(e)}}else if(e)e.remove()}
function pickCategory(c){document.getElementById('categoryFilter').value=c;filterProducts()}
</script>
"""

def page(title, body, **kwargs):
    user = current_user()
    rendered_body = render_template_string(body, user=user, categories=CATEGORIES, vodafone_number=VODAFONE_CASH_NUMBER, **kwargs)
    return render_template_string(BASE, title=title, body=rendered_body, user=user,
                                 year=__import__("datetime").datetime.now().year,
                                 vodafone_number=VODAFONE_CASH_NUMBER)

@app.route("/")
def home():
    category = request.args.get("category", "all")
    with db() as con:
        products = con.execute("SELECT * FROM products WHERE active=1 ORDER BY id DESC").fetchall()
        posts = con.execute("SELECT * FROM posts WHERE active=1 ORDER BY id DESC LIMIT 6").fetchall()
    return page("الرئيسية", HOME, products=products, posts=posts)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:70]
        email = request.form.get("email", "").strip().lower()[:160]
        password = request.form.get("password", "")
        if not name or "@" not in email or len(password) < 8:
            flash("اكتب بيانات صحيحة، وكلمة مرور 8 أحرف على الأقل.")
        else:
            new_uid = None
            try:
                with db() as con:
                    cur = con.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                                      (name, email, generate_password_hash(password)))
                    new_uid = cur.lastrowid
                # Generate the OTP here and publish it directly to Telegram from this app.py.
                code, ttl = request_telegram_otp(name, email)
                payload = json.dumps({"method": "telegram_channel"}, ensure_ascii=False)
                with db() as con:
                    con.execute("INSERT INTO otp_codes(email,code_hash,purpose,payload,expires_at) VALUES(?,?,?,?,?)",
                        (email, generate_password_hash(code), "تأكيد إنشاء الحساب", payload,
                         (datetime.utcnow()+timedelta(seconds=ttl)).isoformat()))
                session.clear()
                session["otp_email"] = email
                session["pending_auth_uid"] = new_uid
                session["otp_method"] = "telegram"
                flash("طلبنا كود التحقق من بوت تيليجرام. افتح قناة MidoWorld واكتب الكود هنا.")
                return redirect(url_for("verify_otp"))
            except sqlite3.IntegrityError:
                flash("البريد الإلكتروني مستخدم بالفعل.")
            except Exception as exc:
                app.logger.exception("Registration Telegram OTP failed")
                if new_uid:
                    with db() as con:
                        con.execute("DELETE FROM otp_codes WHERE email=? AND purpose=? AND used=0",
                                    (email, "تأكيد إنشاء الحساب"))
                        con.execute("DELETE FROM users WHERE id=?", (new_uid,))
                flash(f"لم نقدرش نبعت كود التحقق عبر تيليجرام: {str(exc)[:180]}")
    body = r"""
    <section class="formcard"><h1>انضم إلى <span class="gradient">MIDO NOVA</span></h1><p>أنشئ حسابك وابدأ اكتشاف المتجر.</p>
    <form method="post"><label class="field">الاسم<input name="name" maxlength="70" required autocomplete="name"></label>
    <label class="field">البريد الإلكتروني<input type="email" name="email" required autocomplete="email"></label>
    <label class="field">كلمة المرور<input type="password" name="password" minlength="8" required autocomplete="new-password"></label>
    <button class="btn primary" type="submit">إنشاء الحساب</button></form><a class="btn" style="width:100%;margin-top:8px" href="{{url_for('google_login')}}">◉ التسجيل باستخدام Google</a><p>كود التسجيل هيظهر في قناة <a style="color:var(--mint)" href="https://t.me/MidoWorld" target="_blank" rel="noopener">MidoWorld</a>.</p><p>عندك حساب؟ <a style="color:var(--mint)" href="{{url_for('login')}}">سجل دخولك</a></p></section>"""
    return page("حساب جديد", body)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            code = f"{random.randint(0, 999999):06d}"
            with db() as con:
                con.execute("INSERT INTO otp_codes(email,code_hash,purpose,payload,expires_at) VALUES(?,?,?,?,?)",
                    (email, generate_password_hash(code), "كود تسجيل الدخول", "{}", (datetime.utcnow()+timedelta(minutes=10)).isoformat()))
            try:
                send_otp_email(email, code, "كود تسجيل الدخول")
                session.clear()
                session["otp_email"] = email
                session["pending_auth_uid"] = user["id"]
                flash("تم التحقق من كلمة المرور. أدخل كود الأمان الذي أرسلناه لبريدك.")
                return redirect(url_for("verify_otp"))
            except Exception:
                app.logger.exception("Login OTP email failed")
                flash("تعذر إرسال كود الأمان إلى بريدك. راجع سجل التشغيل وRESEND_API_KEY وبيانات المرسل في Render، ثم حاول مجددًا.")
        else:
            flash("بيانات الدخول غير صحيحة.")
    body = r"""
    <section class="formcard"><h1>أهلًا بعودتك</h1><p>سجل دخولك إلى حسابك.</p>
    <form method="post"><label class="field">البريد الإلكتروني<input type="email" name="email" required autocomplete="email"></label>
    <label class="field">كلمة المرور<input type="password" name="password" required autocomplete="current-password"></label>
    <button class="btn primary" type="submit">دخول</button></form><a class="btn" style="width:100%;margin-top:8px" href="{{url_for('google_login')}}">◉ المتابعة باستخدام Google</a><p>لسه جديد؟ <a style="color:var(--mint)" href="{{url_for('register')}}">اعمل حساب</a></p></section>"""
    return page("تسجيل الدخول", body)

@app.route("/login/google")
def google_login():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        flash("تسجيل Google يحتاج ضبط GOOGLE_CLIENT_ID وGOOGLE_CLIENT_SECRET من إعدادات Google Cloud.")
        return redirect(url_for("login"))
    try:
        from authlib.integrations.flask_client import OAuth
        if not hasattr(app, "_oauth_google"):
            oauth = OAuth(app)
            oauth.register(name="google", client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"})
            app._oauth_google = oauth.create_client("google")
        return app._oauth_google.authorize_redirect(url_for("google_callback", _external=True))
    except ImportError:
        flash("ثبت مكتبة authlib أولًا: pip install authlib")
        return redirect(url_for("login"))

@app.route("/login/google/callback")
def google_callback():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return redirect(url_for("login"))
    try:
        client = app._oauth_google
        token = client.authorize_access_token()
        info = token.get("userinfo") or client.userinfo()
        email = (info.get("email") or "").lower()
        name = info.get("name") or email.split("@")[0]
        if not email or not info.get("email_verified", False):
            flash("تعذر التحقق من بريد Google.")
            return redirect(url_for("login"))
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not user:
                cur = con.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                    (name[:70], email, generate_password_hash(secrets.token_urlsafe(32))))
                uid = cur.lastrowid
            else:
                uid = user["id"]
        session.clear()
        session["user_id"] = uid
        flash("تم تسجيل الدخول باستخدام Google.")
        return redirect(url_for("home"))
    except Exception:
        app.logger.exception("Google OAuth failed")
        flash("تعذر تسجيل الدخول عبر Google. راجع إعدادات OAuth.")
        return redirect(url_for("login"))

@app.route("/send-otp", methods=["GET", "POST"])
def send_otp():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()[:160]
        purpose = request.form.get("purpose", "تأكيد الحساب")[:60]
        if "@" not in email:
            flash("اكتب بريدًا إلكترونيًا صحيحًا.")
            return redirect(url_for("send_otp"))
        code = f"{random.randint(0, 999999):06d}"
        payload = json.dumps({"name": request.form.get("name", "").strip()[:70],
                              "password": request.form.get("password", "")})
        with db() as con:
            con.execute("INSERT INTO otp_codes(email,code_hash,purpose,payload,expires_at) VALUES(?,?,?,?,?)",
                (email, generate_password_hash(code), purpose, payload, (datetime.utcnow()+timedelta(minutes=10)).isoformat()))
        try:
            send_otp_email(email, code, purpose)
            session["otp_email"] = email
            flash("أرسلنا كود التحقق إلى بريدك الإلكتروني.")
            return redirect(url_for("verify_otp"))
        except Exception as exc:
            app.logger.warning("OTP email unavailable: %s", exc)
            flash("تعذر إرسال البريد. راجع RESEND_API_KEY وبيانات المرسل في Render.")
    body = r"""<section class="formcard"><h1>التحقق بالبريد</h1><p>أرسل كود أمان مكونًا من 6 أرقام إلى بريدك.</p><form method="post"><label class="field">البريد الإلكتروني<input name="email" type="email" required></label><label class="field">الغرض<input name="purpose" value="تأكيد الحساب" required></label><button class="btn primary">إرسال كود التحقق</button></form></section>"""
    return page("التحقق بالبريد", body)

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        email = session.get("otp_email", "")
        code = request.form.get("code", "").strip()
        with db() as con:
            records = con.execute("SELECT * FROM otp_codes WHERE email=? AND used=0 ORDER BY id DESC LIMIT 5", (email,)).fetchall()
            match = None
            for row in records:
                try:
                    payload = json.loads(row["payload"] or "{}")
                except (TypeError, json.JSONDecodeError):
                    payload = {}
                if datetime.fromisoformat(row["expires_at"]) > datetime.utcnow() and check_password_hash(row["code_hash"], code):
                    match = row
                    break
            if match:
                con.execute("UPDATE otp_codes SET used=1 WHERE id=?", (match["id"],))
                flash("تم التحقق من كود الأمان بنجاح.")
                pending_uid = session.pop("pending_auth_uid", None)
                session.pop("otp_email", None)
                session.pop("otp_method", None)
                if pending_uid:
                    session.clear()
                    session["user_id"] = pending_uid
                    user = current_user()
                    return redirect(url_for("admin") if user and user["email"].lower() == ADMIN_EMAIL else url_for("home"))
                return redirect(url_for("login"))
        flash("الكود غير صحيح أو انتهت صلاحيته، تأكد من إدخاله كما ظهر في القناة.")
    body = r"""<section class="formcard"><h1>اكتب كود التحقق</h1><p>افتح قناة <a href="https://t.me/MidoWorld" target="_blank" rel="noopener">MidoWorld</a>، وأدخل كود التحقق المكوّن من 6 أرقام.</p><form method="post"><label class="field">كود OTP<input name="code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" required autocomplete="one-time-code"></label><button class="btn primary">تحقق</button></form></section>"""
    return page("كود التحقق", body)

@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج.")
    return redirect(url_for("home"))

@app.route("/order/<int:product_id>", methods=["POST"])
def order_product(product_id):
    user = current_user()
    if not user:
        flash("سجل دخولك الأول عشان تقدر تسجل طلب.")
        return redirect(url_for("login"))
    with db() as con:
        product = con.execute("SELECT * FROM products WHERE id=? AND active=1", (product_id,)).fetchone()
        if not product:
            abort(404)
        code = request.form.get("discount_code", "").strip().upper()
        discount = 0
        if code:
            coupon = con.execute("SELECT * FROM discount_codes WHERE code=? AND active=1 AND uses_left>0", (code,)).fetchone()
            if not coupon:
                flash("كود الخصم غير صالح أو انتهى استخدامه.")
                return redirect(url_for("home"))
            discount = product["price"] * coupon["percent"] // 100
            con.execute("UPDATE discount_codes SET uses_left=uses_left-1 WHERE id=?", (coupon["id"],))
        total = product["price"] - discount
        reference = request.form.get("payment_reference", "").strip()[:120]
        cur = con.execute("""INSERT INTO orders(user_id,product_id,quantity,total,status,payment_method,payment_reference,discount_code,discount_amount)
            VALUES(?,?,1,?,'بانتظار مراجعة التحويل','Vodafone Cash',?,?,?)""",
            (user["id"], product_id, total, reference, code, discount))
        order_id = cur.lastrowid
    notify_telegram(f"🛒 طلب جديد في MIDO NOVA\\nرقم الطلب: #{order_id}\\nالعميل: {user['name']} ({user['email']})\\nالمنتج: {product['name']}\\nالإجمالي: {total/100:.2f} ج.م\\nطريقة الدفع: Vodafone Cash\\nرقم مرجع التحويل: {reference or 'لم يرسل'}")
    flash(f"تم تسجيل الطلب #{order_id}. حوّل المبلغ إلى فودافون كاش ثم أرسل رقم مرجع التحويل؛ الطلب ينتظر مراجعة الإدارة.")
    return redirect(url_for("my_orders"))

@app.route("/my-orders")
def my_orders():
    user = current_user()
    if not user:
        flash("سجل دخولك لمتابعة طلباتك.")
        return redirect(url_for("login"))
    with db() as con:
        orders = con.execute("""SELECT o.*,p.name product_name FROM orders o
            JOIN products p ON p.id=o.product_id WHERE o.user_id=? ORDER BY o.id DESC""",
            (user["id"],)).fetchall()
    body = r"""
    <section class="section"><div class="section-head"><div><h2>طلباتي</h2><p>طلباتك المسجلة وحالتها الحالية</p></div><a class="btn small" href="{{url_for('home')}}">رجوع للمتجر</a></div>
    {% if orders %}<div class="tablewrap"><table><thead><tr><th>رقم الطلب</th><th>المنتج</th><th>الإجمالي</th><th>الحالة</th><th>التاريخ</th></tr></thead><tbody>
    {% for o in orders %}<tr><td>#{{o.id}}</td><td>{{o.product_name}}</td><td>{{'{:,.2f}'.format(o.total/100)}} ج.م</td><td class="status">{{o.status}}</td><td>{{o.created_at}}</td></tr>{% endfor %}
    </tbody></table></div>{% else %}<div class="empty">لسه معندكش طلبات. <a style="color:var(--mint)" href="{{url_for('home')}}">تصفح المتجر</a></div>{% endif %}
    </section>"""
    return page("طلباتي", body, orders=orders)

@app.route("/admin")
@admin_required
def admin():
    with db() as con:
        orders = con.execute("""SELECT o.*,u.name user_name,u.email,p.name product_name
            FROM orders o JOIN users u ON u.id=o.user_id JOIN products p ON p.id=o.product_id
            ORDER BY o.id DESC LIMIT 250""").fetchall()
        products = con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        posts = con.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
        coupons = con.execute("SELECT * FROM discount_codes ORDER BY id DESC").fetchall()
    body = r"""
    <section class="section"><div class="section-head"><div><h2>لوحة الإدارة</h2><p>إدارة المنتجات ومراجعة الطلبات</p></div><a class="btn small" href="{{url_for('home')}}">عرض المتجر</a></div>
    <div class="formcard" style="max-width:none;margin:15px 0"><h2 style="margin-top:0">إضافة منتج</h2>
    <form method="post" action="{{url_for('admin_add_product')}}" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px">
    <label class="field">اسم المنتج<input name="name" required maxlength="100"></label>
    <label class="field">القسم<select name="category">{% for k,n,i in categories if k!='all' and k!='crypto' %}<option value="{{k}}">{{n}}</option>{% endfor %}</select></label>
    <label class="field">النوع<input name="kind" value="منتج رقمي" required></label>
    <label class="field">السعر بالجنيه<input name="price" type="number" min="0.01" step="0.01" required></label>
    <label class="field">أيقونة<input name="icon" value="✦" maxlength="8"></label>
    <label class="field">شارة<input name="badge" maxlength="30"></label>
    <label class="field" style="grid-column:1/-1">الوصف<input name="description" maxlength="250"></label>
    <button class="btn primary" type="submit">+ إضافة المنتج</button></form></div>
    <h2>المنتجات</h2><div class="tablewrap"><table><thead><tr><th>#</th><th>المنتج</th><th>القسم</th><th>السعر</th><th>الحالة</th><th>إجراء</th></tr></thead><tbody>
    {% for p in products %}<tr><td>{{p.id}}</td><td>{{p.name}}</td><td>{{p.category}}</td><td>{{'{:,.2f}'.format(p.price/100)}} ج.م</td><td>{{'ظاهر' if p.active else 'مخفي'}}</td><td><form method="post" action="{{url_for('admin_toggle_product',product_id=p.id)}}"><button class="btn small" type="submit">{{'إخفاء' if p.active else 'إظهار'}}</button></form></td></tr>{% endfor %}
    </tbody></table></div>
    <h2 style="margin-top:30px">آخر الطلبات</h2><div class="tablewrap"><table><thead><tr><th>رقم</th><th>العميل</th><th>المنتج</th><th>الإجمالي</th><th>الحالة</th><th>تحديث</th></tr></thead><tbody>
    {% for o in orders %}<tr><td>#{{o.id}}</td><td>{{o.user_name}}<br>{{o.email}}</td><td>{{o.product_name}}</td><td>{{'{:,.2f}'.format(o.total/100)}} ج.م</td><td>{{o.status}}</td><td><form method="post" action="{{url_for('admin_order_status',order_id=o.id)}}" style="display:flex;gap:5px"><select name="status"><option>قيد المراجعة</option><option>تم التأكيد</option><option>تم التسليم</option><option>ملغي</option></select><button class="btn small" type="submit">حفظ</button></form></td></tr>{% else %}<tr><td colspan="6">لا توجد طلبات بعد.</td></tr>{% endfor %}
    </tbody></table></div>
    <h2 style="margin-top:30px">المنشورات والأخبار والتحديثات</h2>
    <div class="formcard" style="max-width:none;margin:12px 0"><form method="post" action="{{url_for('admin_add_post')}}" enctype="multipart/form-data" style="display:grid;gap:8px">
    <label class="field">العنوان<input name="title" required maxlength="140"></label>
    <label class="field">النوع<select name="kind"><option>خبر</option><option>تحديث</option><option>إعلان</option><option>منشور</option></select></label>
    <label class="field">المحتوى<input name="body" required maxlength="3000"></label>
    <label class="field">صورة (اختياري)<input type="file" name="image" accept="image/png,image/jpeg,image/webp,image/gif"></label>
    <button class="btn primary" type="submit">نشر المحتوى</button></form>
    <div class="tablewrap" style="margin-top:12px"><table><thead><tr><th>العنوان</th><th>النوع</th><th>إجراء</th></tr></thead><tbody>{% for post in posts %}<tr><td>{{post.title}}</td><td>{{post.kind}}</td><td><form method="post" action="{{url_for('admin_toggle_post',post_id=post.id)}}"><button class="btn small">{{'إخفاء' if post.active else 'إظهار'}}</button></form></td></tr>{% endfor %}</tbody></table></div></div>
    <h2 style="margin-top:30px">أكواد الخصم</h2>
    <div class="formcard" style="max-width:none;margin:12px 0"><form method="post" action="{{url_for('admin_add_coupon')}}" style="display:flex;gap:10px;flex-wrap:wrap;align-items:end">
    <label class="field">الكود<input name="code" required maxlength="30" placeholder="MIDO10"></label>
    <label class="field">نسبة الخصم %<input name="percent" type="number" min="1" max="90" required></label>
    <label class="field">عدد الاستخدامات<input name="uses_left" type="number" min="1" max="100000" value="100" required></label>
    <button class="btn primary" type="submit">إنشاء الكود</button></form>
    <div class="tablewrap"><table><thead><tr><th>الكود</th><th>الخصم</th><th>المتبقي</th><th>الحالة</th></tr></thead><tbody>{% for c in coupons %}<tr><td>{{c.code}}</td><td>{{c.percent}}%</td><td>{{c.uses_left}}</td><td>{{'فعال' if c.active else 'موقوف'}}</td></tr>{% endfor %}</tbody></table></div></div>
    <div class="notice">تنبيه أمني: غيّر كلمة مرور الإدارة الافتراضية وإعداد SECRET_KEY قبل النشر. أضف حماية CSRF وتحديد معدل المحاولات وربط بوابة دفع موثوقة قبل استقبال مدفوعات حقيقية.</div></section>"""
    return page("لوحة الإدارة", body, orders=orders, products=products, posts=posts, coupons=coupons)

@app.route("/admin/product/add", methods=["POST"])
@admin_required
def admin_add_product():
    name = request.form.get("name", "").strip()[:100]
    category = request.form.get("category", "digital")
    kind = request.form.get("kind", "منتج").strip()[:60]
    icon = request.form.get("icon", "✦").strip()[:8] or "✦"
    badge = request.form.get("badge", "").strip()[:30]
    description = request.form.get("description", "").strip()[:250]
    try:
        price = round(float(request.form.get("price", "0")) * 100)
    except ValueError:
        price = 0
    allowed = {"google", "games", "digital", "products"}
    if not name or category not in allowed or price <= 0:
        flash("راجع اسم المنتج والقسم والسعر.")
    else:
        with db() as con:
            con.execute("""INSERT INTO products(name,category,kind,price,icon,badge,description)
                VALUES(?,?,?,?,?,?,?)""", (name, category, kind, price, icon, badge, description))
        flash("تمت إضافة المنتج.")
    return redirect(url_for("admin"))

@app.route("/admin/product/<int:product_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_product(product_id):
    with db() as con:
        p = con.execute("SELECT active FROM products WHERE id=?", (product_id,)).fetchone()
        if p:
            con.execute("UPDATE products SET active=? WHERE id=?", (0 if p["active"] else 1, product_id))
            flash("تم تحديث ظهور المنتج.")
    return redirect(url_for("admin"))

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    status = request.form.get("status", "")
    allowed = {"قيد المراجعة", "تم التأكيد", "تم التسليم", "ملغي"}
    if status not in allowed:
        abort(400)
    with db() as con:
        con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    flash("تم تحديث حالة الطلب.")
    return redirect(url_for("admin"))

@app.route("/admin/post/add", methods=["POST"])
@admin_required
def admin_add_post():
    title = request.form.get("title", "").strip()[:140]
    body = request.form.get("body", "").strip()[:3000]
    kind = request.form.get("kind", "خبر")[:30]
    image = request.files.get("image")
    image_path = ""
    if image and image.filename:
        if image.mimetype not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
            flash("نوع الصورة غير مدعوم.")
            return redirect(url_for("admin"))
        ext = os.path.splitext(secure_filename(image.filename))[1].lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            flash("امتداد الصورة غير مدعوم.")
            return redirect(url_for("admin"))
        filename = secrets.token_hex(16) + ext
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = "/static/uploads/" + filename
    if not title or not body:
        flash("اكتب عنوان ومحتوى المنشور.")
    else:
        with db() as con:
            con.execute("INSERT INTO posts(title,body,kind,image) VALUES(?,?,?,?)", (title, body, kind, image_path))
        flash("تم نشر المحتوى.")
    return redirect(url_for("admin"))

@app.route("/admin/post/<int:post_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_post(post_id):
    with db() as con:
        post = con.execute("SELECT active FROM posts WHERE id=?", (post_id,)).fetchone()
        if post:
            con.execute("UPDATE posts SET active=? WHERE id=?", (0 if post["active"] else 1, post_id))
            flash("تم تحديث المنشور.")
    return redirect(url_for("admin"))

@app.route("/admin/coupon/add", methods=["POST"])
@admin_required
def admin_add_coupon():
    code = "".join(ch for ch in request.form.get("code", "").upper().strip() if ch.isalnum() or ch in "-_")[:30]
    try:
        percent = int(request.form.get("percent", "0"))
        uses = int(request.form.get("uses_left", "100"))
    except ValueError:
        percent, uses = 0, 0
    if not code or not 1 <= percent <= 90 or not 1 <= uses <= 100000:
        flash("راجع بيانات كود الخصم.")
    else:
        try:
            with db() as con:
                con.execute("INSERT INTO discount_codes(code,percent,uses_left) VALUES(?,?,?)", (code, percent, uses))
            flash("تم إنشاء كود الخصم.")
        except sqlite3.IntegrityError:
            flash("الكود موجود بالفعل.")
    return redirect(url_for("admin"))

@app.errorhandler(403)
def forbidden(_):
    return page("غير مسموح", '<section class="formcard"><h1>مش مسموح بالدخول</h1><p>الصفحة دي للإدارة فقط.</p><a class="btn primary" href="/">العودة للرئيسية</a></section>'), 403

@app.errorhandler(404)
def not_found(_):
    return page("الصفحة غير موجودة", '<section class="formcard"><h1>الصفحة مش موجودة</h1><p>الرابط اللي فتحته غير صحيح.</p><a class="btn primary" href="/">العودة للرئيسية</a></section>'), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
