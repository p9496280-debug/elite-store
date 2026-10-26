from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDO NOVA — Everything in One Place</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body { background-color: #030712; color: #f9fafb; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

        /* Top Header */
        header { background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(16px); padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(56, 189, 248, 0.2); z-index: 20; }
        .logo-area { display: flex; align-items: center; gap: 10px; font-size: 1.3rem; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; }
        .logo-badge { background: linear-gradient(135deg, #059669, #10b981); color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }

        /* Workspace */
        .workspace { display: flex; flex: 1; height: calc(100vh - 120px); position: relative; overflow: hidden; }
        .main-content { flex: 1; position: relative; background: radial-gradient(circle at center, #111827 0%, #030712 100%); overflow-y: auto; padding: 20px; }

        /* Banner */
        .promo-banner { background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .promo-banner h3 { color: #38bdf8; font-size: 1.1rem; margin-bottom: 4px; }
        .promo-banner p { color: #94a3b8; font-size: 0.85rem; }

        /* Search Box */
        .search-box { background: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 12px 18px; display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .search-box input { background: none; border: none; color: #fff; width: 100%; outline: none; font-size: 0.9rem; }

        /* Categories Grid */
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 25px; }
        .dash-card { border-radius: 16px; padding: 18px 14px; display: flex; flex-direction: column; gap: 8px; cursor: pointer; transition: all 0.25s ease; box-shadow: 0 10px 20px rgba(0,0,0,0.4); text-align: right; }
        .dash-card:hover { transform: translateY(-4px); filter: brightness(1.1); }
        .dash-card h4 { font-size: 1.05rem; font-weight: 800; color: #fff; }
        .dash-card p { font-size: 0.75rem; color: rgba(255,255,255,0.8); line-height: 1.3; }
        
        .card-google { background: linear-gradient(135deg, #0284c7, #0369a1); }
        .card-games { background: linear-gradient(135deg, #7c3aed, #5b21b6); }
        .card-digital { background: linear-gradient(135deg, #0d9488, #0f766e); }
        .card-crypto { background: linear-gradient(135deg, #d97706, #b45309); }
        .card-products { background: linear-gradient(135deg, #059669, #047857); }
        .card-wallet { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
        .card-support { background: linear-gradient(135deg, #4f46e5, #3730a3); }
        .card-account { background: linear-gradient(135deg, #dc2626, #991b1b); }

        /* Section Title */
        .section-title { font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }

        /* Offers Grid */
        .offers-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .offer-card { background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 14px; text-align: center; cursor: pointer; transition: 0.2s; }
        .offer-card:hover { border-color: #38bdf8; transform: translateY(-2px); }
        .offer-card h5 { font-size: 0.95rem; color: #fff; margin-top: 6px; }
        .offer-card .price { font-size: 0.85rem; color: #10b981; font-weight: bold; margin-top: 4px; }
        .offer-card .discount { font-size: 0.7rem; background: #059669; color: #fff; padding: 2px 6px; border-radius: 10px; display: inline-block; margin-top: 4px; }

        /* Bottom Navigation */
        nav.bottom-nav { background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(16px); height: 60px; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid rgba(56, 189, 248, 0.2); z-index: 20; }
        .nav-item { display: flex; flex-direction: column; align-items: center; gap: 2px; color: #64748b; font-size: 0.7rem; cursor: pointer; transition: 0.2s; }
        .nav-item.active, .nav-item:hover { color: #38bdf8; }

        /* Modals */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #0f172a; border: 1px solid #38bdf8; width: 92%; max-width: 650px; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.9); max-height: 85vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
        .modal-header h3 { color: #38bdf8; font-size: 1.2rem; }
        .close-btn { background: none; border: none; color: #64748b; font-size: 1.5rem; cursor: pointer; }

        .sub-item { background: #1e293b; border: 1px solid #334155; padding: 14px 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.2s; margin-bottom: 10px; }
        .sub-item:hover { background: #334155; border-color: #38bdf8; }
        .sub-item span { color: #fff; font-weight: 600; font-size: 0.9rem; }
        
        /* Chat Box */
        .chat-box { display: flex; flex-direction: column; gap: 10px; height: 260px; overflow-y: auto; padding: 10px; background: #030712; border-radius: 12px; border: 1px solid #1e293b; }
        .message { padding: 10px 14px; border-radius: 10px; max-width: 80%; font-size: 0.85rem; line-height: 1.4; }
        .message.ai { background: #1e293b; color: #f8fafc; align-self: flex-start; border-right: 3px solid #38bdf8; }
        .message.user { background: #0284c7; color: #fff; align-self: flex-end; }
        .chat-input { display: flex; gap: 10px; margin-top: 10px; }
        .chat-input input { flex: 1; background: #030712; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #fff; outline: none; }
        .chat-input button { background: #0284c7; color: #fff; border: none; padding: 0 18px; border-radius: 8px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

    <header>
        <div class="logo-area"><span>MIDO NOVA</span></div>
        <div class="header-icons"><span class="logo-badge">⚡ متجر شامل</span></div>
    </header>

    <div class="workspace">
        <div class="main-content">
            <div class="promo-banner">
                <div>
                    <h3>بطاقات جوجل بلاي والستور</h3>
                    <p>متوفرة الآن بأسعار مميزة وخصومات تصل إلى 25% 🔥</p>
                </div>
                <div style="font-size: 2.2rem;">🛒</div>
            </div>

            <div class="search-box">
                <span>🔍</span>
                <input type="text" placeholder="ابحث عن منتج، بطاقة، عملة رقمية أو خدمة...">
            </div>

            <div class="section-title"><span>الأقسام الرئيسية</span></div>
            <div class="cards-grid">
                <div class="dash-card card-google" onclick="openModal('googleModal')"><h4>جوجل بلاي</h4><p>بطاقات وشحن خدمات</p></div>
                <div class="dash-card card-games" onclick="openModal('gamesModal')"><h4>الألعاب</h4><p>بطاقات وشحن ألعاب</p></div>
                <div class="dash-card card-digital" onclick="openModal('digitalModal')"><h4>الخدمات الرقمية</h4><p>اشتراكات وبرامج وأدوات</p></div>
                <div class="dash-card card-crypto" onclick="openModal('cryptoModal')"><h4>العملات الرقمية</h4><p>شراء - بيع - محافظ</p></div>
                <div class="dash-card card-products" onclick="openModal('productsModal')"><h4>المنتجات</h4><p>إلكترونيات ومننوعات</p></div>
                <div class="dash-card card-wallet" onclick="openModal('walletModal')"><h4>محفظتي</h4><p>الرصيد وسجل المعاملات</p></div>
                <div class="dash-card card-support" onclick="openModal('aiModal')"><h4>الدعم والمساعدة</h4><p>مساعد ذكي وخدمة عملاء</p></div>
                <div class="dash-card card-account" onclick="openModal('accountModal')"><h4>حسابي</h4><p>البيانات والأمان</p></div>
            </div>

            <div class="section-title"><span>عروض مميزة</span></div>
            <div class="offers-grid">
                <div class="offer-card" onclick="openModal('googleModal')">
                    <div style="font-size: 1.5rem;">🎮</div>
                    <h5>Google Play $10</h5>
                    <div class="price">$7.50</div>
                    <div class="discount">خصم 25%</div>
                </div>
                <div class="offer-card" onclick="openModal('gamesModal')">
                    <div style="font-size: 1.5rem;">🎯</div>
                    <h5>PlayStation $20</h5>
                    <div class="price">$15.90</div>
                    <div class="discount">خصم 20%</div>
                </div>
                <div class="offer-card" onclick="openModal('gamesModal')">
                    <div style="font-size: 1.5rem;">🚀</div>
                    <h5>Xbox Gift Card</h5>
                    <div class="price">$19.90</div>
                    <div class="discount">خصم 20%</div>
                </div>
            </div>
        </div>
    </div>

    <nav class="bottom-nav">
        <div class="nav-item active"><span>🏠</span><span>الرئيسية</span></div>
        <div class="nav-item" onclick="openModal('googleModal')"><span>🛍️</span><span>الأقسام</span></div>
        <div class="nav-item" onclick="openModal('walletModal')"><span>💰</span><span>محفظتي</span></div>
        <div class="nav-item" onclick="openModal('aiModal')"><span>🤖</span><span>الدعم</span></div>
        <div class="nav-item" onclick="openModal('accountModal')"><span>👤</span><span>حسابي</span></div>
    </nav>

    <!-- Modals -->
    <div id="googleModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>Google Play — بطاقات وشحن</h3><button class="close-btn" onclick="closeModal('googleModal')">&times;</button></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>Google Play $10 (سعر: $7.50)</span><span>شراء ➔</span></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>Google Play $25 (سعر: $18.90)</span><span>شراء ➔</span></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>Google Play $50 (سعر: $36.90)</span><span>شراء ➔</span></div>
        </div>
    </div>

    <div id="gamesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>بطاقات وشحن الألعاب</h3><button class="close-btn" onclick="closeModal('gamesModal')">&times;</button></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>Steam Wallet $20 ($14.90)</span><span>شراء ➔</span></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>PlayStation Store $20 ($15.90)</span><span>شراء ➔</span></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>Xbox Gift Card $25 ($19.90)</span><span>شراء ➔</span></div>
            <div class="sub-item" onclick="alert('تمت إضافة المنتج للسلة!')"><span>Roblox Gift Card $25 ($18.50)</span><span>شراء ➔</span></div>
        </div>
    </div>

    <div id="cryptoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>العملات الرقمية (تداول ومعاملات)</h3><button class="close-btn" onclick="closeModal('cryptoModal')">&times;</button></div>
            <div class="sub-item"><span>Bitcoin (BTC) — $67,432.21 (+2.4%)</span><span>تداول ➔</span></div>
            <div class="sub-item"><span>Ethereum (ETH) — $3,248.75 (+1.8%)</span><span>تداول ➔</span></div>
            <div class="sub-item"><span>Tether (USDT) — $1.00 (+0.1%)</span><span>تداول ➔</span></div>
        </div>
    </div>

    <div id="productsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>المنتجات والإلكترونيات</h3><button class="close-btn" onclick="closeModal('productsModal')">&times;</button></div>
            <div class="sub-item"><span>ساعات ذكية أصلية ($49.90)</span><span>طلب ➔</span></div>
            <div class="sub-item"><span>سماعات لاسلكية برو ($29.90)</span><span>طلب ➔</span></div>
            <div class="sub-item"><span>كيورد ألعاب ميكانيكي ($39.90)</span><span>طلب ➔</span></div>
        </div>
    </div>

    <div id="digitalModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>الخدمات الرقمية والاشتراكات</h3><button class="close-btn" onclick="closeModal('digitalModal')">&times;</button></div>
            <div class="sub-item"><span>اشتراك Netflix شهري ($9.99)</span><span>شراء ➔</span></div>
            <div class="sub-item"><span>اشتراك Spotify بريميوم ($4.99)</span><span>شراء ➔</span></div>
        </div>
    </div>

    <div id="walletModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>محفظتي ورصيدك</h3><button class="close-btn" onclick="closeModal('walletModal')">&times;</button></div>
            <div style="background:#1e293b; padding:16px; border-radius:12px; text-align:center;">
                <p style="color:#94a3b8; font-size:0.85rem;">الرصيد الكلي</p>
                <h2 style="color:#10b981; font-size:1.8rem; margin-top:5px;">$ 125.50</h2>
            </div>
            <div class="sub-item" onclick="alert('تم إضافة رصيد تجريبي بنجاح!')"><span>➕ إضافة رصيد جديد للمحفظة</span><span>إيداع ➔</span></div>
            <div class="sub-item"><span>📜 سجل المعاملات السابقة</span><span>عرض ➔</span></div>
        </div>
    </div>

    <div id="aiModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>مساعد MIDO AI الذكي</h3><button class="close-btn" onclick="closeModal('aiModal')">&times;</button></div>
            <div class="chat-box" id="chatBox">
                <div class="message ai">أهلاً بك في MIDO NOVA! أنا مساعدك الذكي، كيف يمكنني مساعدتك في عمليات الشحن أو الخدمات اليوم؟</div>
            </div>
            <div class="chat-input">
                <input type="text" id="userInput" placeholder="اكتب سؤالك هنا..." onkeypress="handleKeyPress(event)">
                <button onclick="sendAiMessage()">إرسال</button>
            </div>
        </div>
    </div>

    <div id="accountModal" class="modal">
        <div class="modal-content">
            <div class="modal-header"><h3>حسابي والأمان</h3><button class="close-btn" onclick="closeModal('accountModal')">&times;</button></div>
            <div class="sub-item"><span>Mido Nova (mido@example.com)</span><span>حساب معتمد 👑</span></div>
            <div class="sub-item"><span>🔒 الأمان والحماية المصرفية</span><span>إدارة ➔</span></div>
            <div class="sub-item"><span>🔔 الإشعارات والتنبيهات</span><span>تخصيص ➔</span></div>
        </div>
    </div>

    <script>
        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }

        function sendAiMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = input.value.trim();
            if(!text) return;
            chatBox.innerHTML += `<div class="message user">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            setTimeout(() => {
                chatBox.innerHTML += `<div class="message ai">مساعد MIDO AI: تم استلام طلبك بنجاح، فريق الدعم الفني جاهز لمساعدتك على مدار الساعة!</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }, 800);
        }
        function handleKeyPress(e) { if(e.key === 'Enter') sendAiMessage(); }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
