from flask import Flask, render_template_string

app = Flask(__name__)

PRODUCTS = [
    {
        "name": "Google Play",
        "description": "بطاقات Google Play الرقمية",
        "price": "حسب الفئة",
        "icon": "🎮"
    },
    {
        "name": "Digital Cards",
        "description": "بطاقات رقمية متنوعة",
        "price": "حسب الفئة",
        "icon": "💳"
    },
    {
        "name": "Gaming Cards",
        "description": "بطاقات الألعاب",
        "price": "حسب الفئة",
        "icon": "🕹️"
    }
]

PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport"
 content="width=device-width, initial-scale=1">
<title>ELITE STORE</title>
<style>
* {
    box-sizing: border-box;
}
body {
    margin: 0;
    font-family: Arial, sans-serif;
    color: white;
    background: #090711;
}
header {
    padding: 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #100c1c;
    border-bottom: 1px solid #352052;
}
.logo {
    font-size: 24px;
    font-weight: bold;
    color: #c084fc;
}
.badge {
    color: #d8b4fe;
    border: 1px solid #7540a8;
    border-radius: 20px;
    padding: 8px 12px;
}
.hero {
    text-align: center;
    padding: 65px 20px;
    background:
      radial-gradient(ellipse at top, #42206b, #090711 70%);
}
.hero h1 {
    font-size: 42px;
    margin-bottom: 12px;
}
.hero h1 span {
    color: #c084fc;
}
.hero p {
    color: #c4b5d6;
    line-height: 1.9;
}
.container {
    max-width: 1000px;
    padding: 20px;
    margin: auto;
}
.section-title {
    font-size: 25px;
    margin-bottom: 25px;
}
.products {
    display: grid;
    grid-template-columns:
      repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px;
}
.card {
    background: linear-gradient(145deg, #1b1429, #100d19);
    border: 1px solid #38264f;
    border-radius: 18px;
    padding: 25px;
    transition: .25s;
}
.card:hover {
    transform: translateY(-5px);
    border-color: #bd7aff;
}
.icon {
    font-size: 40px;
}
.card h3 {
    color: #e9d5ff;
}
.card p {
    color: #b8adc8;
    line-height: 1.8;
}
.price {
    color: #c084fc;
    font-weight: bold;
}
button {
    width: 100%;
    border: 0;
    border-radius: 10px;
    padding: 13px;
    margin-top: 12px;
    background: #8b3dce;
    color: white;
    font-size: 16px;
    cursor: pointer;
}
button:hover {
    background: #a855f7;
}
.notice {
    background: #171021;
    border: 1px solid #38264f;
    padding: 18px;
    border-radius: 12px;
    color: #d6c7e7;
    line-height: 1.9;
    margin-top: 30px;
}
footer {
    text-align: center;
    padding: 30px;
    color: #9588a7;
    margin-top: 35px;
    border-top: 1px solid #292034;
}
</style>
</head>
<body>

<header>
    <div class="logo">ELITE STORE</div>
    <div class="badge">متجرك الرقمي</div>
</header>

<section class="hero">
    <h1>Welcome to <span>ELITE</span></h1>
    <p>
        اكتشف عالم البطاقات الرقمية
        بتجربة شراء أنيقة ومميزة.
    </p>
</section>

<main class="container">
    <h2 class="section-title">✦ أقسام المتجر</h2>

    <div class="products">
    {% for product in products %}
        <article class="card">
            <div class="icon">{{ product.icon }}</div>
            <h3>{{ product.name }}</h3>
            <p>{{ product.description }}</p>
            <div class="price">{{ product.price }}</div>
            <button onclick="alert('سيتم تفعيل الطلبات بعد إعداد نظام البيع')">
                استكشف القسم
            </button>
        </article>
    {% endfor %}
    </div>

    <div class="notice">
        <strong>مرحبًا بك في ELITE STORE</strong><br>
        متجر تجريبي للبطاقات الرقمية.
        البيع والدفع وتسليم الأكواد غير مفعّلين
        في هذه النسخة.
    </div>
</main>

<footer>
    ELITE STORE © 2026 — جميع الحقوق محفوظة
</footer>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE, products=PRODUCTS)

if __name__ == "__main__":
    app.run()
