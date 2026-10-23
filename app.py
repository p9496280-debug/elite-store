from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaLab 3D — Ultimate Virtual Science & Biology Lab</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body { background-color: #030712; color: #f9fafb; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

        /* Header UI */
        header { background: rgba(17, 24, 39, 0.95); backdrop-filter: blur(16px); padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(56, 189, 248, 0.2); z-index: 20; }
        .logo { font-size: 1.3rem; font-weight: 800; color: #38bdf8; display: flex; align-items: center; gap: 10px; text-shadow: 0 0 12px rgba(56, 189, 248, 0.4); }
        .badge { background: linear-gradient(135deg, #0284c7, #4f46e5); color: #fff; font-size: 0.75rem; padding: 5px 14px; border-radius: 20px; font-weight: 700; }

        /* Workspace */
        .workspace { display: flex; flex: 1; height: calc(100vh - 60px); position: relative; }

        /* Sidebar */
        sidebar { width: 330px; background: #0f172a; padding: 18px; border-left: 1px solid #1e293b; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; z-index: 10; }
        sidebar::-webkit-scrollbar { width: 5px; }
        sidebar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        
        .section-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #38bdf8; margin-top: 10px; letter-spacing: 1px; display: flex; align-items: center; gap: 6px; }

        /* Nav Buttons */
        .nav-btn { background: #1e293b; color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px 14px; text-align: right; border-radius: 12px; cursor: pointer; font-size: 0.88rem; font-weight: 600; transition: all 0.25s ease; display: flex; align-items: center; justify-content: space-between; }
        .nav-btn:hover { background: #334155; color: #fff; transform: translateX(-3px); border-color: rgba(56, 189, 248, 0.4); }
        .nav-btn.active { background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; border-color: #38bdf8; box-shadow: 0 4px 20px rgba(2, 132, 199, 0.4); }
        
        .ai-btn { background: linear-gradient(135deg, #8b5cf6, #6366f1); color: #fff; border: none; font-weight: 700; }
        .table-btn { background: linear-gradient(135deg, #059669, #0d9488); color: #fff; border: none; font-weight: 700; }
        .bio-btn { background: linear-gradient(135deg, #ec4899, #be185d); color: #fff; border: none; font-weight: 700; }

        /* Viewport Canvas */
        main { flex: 1; position: relative; background: radial-gradient(circle at center, #111827 0%, #030712 100%); }
        #viewport { width: 100%; height: 100%; }

        /* Science HUD Panel */
        .hud-panel { position: absolute; top: 20px; right: 20px; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(16px); border: 1px solid rgba(56, 189, 248, 0.3); padding: 20px; border-radius: 16px; max-width: 380px; box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.7); pointer-events: none; }
        .hud-panel h2 { font-size: 1.2rem; color: #38bdf8; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        .hud-panel .equation { background: #090d16; border: 1px solid #1e293b; color: #10b981; padding: 8px 12px; border-radius: 8px; font-family: monospace; font-size: 0.9rem; margin: 8px 0; text-align: center; }
        .hud-panel p { font-size: 0.85rem; line-height: 1.6; color: #94a3b8; }
        
        .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; border-top: 1px solid #1e293b; padding-top: 10px; }
        .data-item { background: rgba(30, 41, 59, 0.5); padding: 6px 10px; border-radius: 8px; }
        .data-item span { display: block; font-size: 0.7rem; color: #64748b; }
        .data-item strong { font-size: 0.8rem; color: #e2e8f0; }

        /* Modals */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #0f172a; border: 1px solid #38bdf8; width: 92%; max-width: 750px; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8); max-height: 85vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
        .modal-header h3 { color: #38bdf8; font-size: 1.25rem; }
        .close-btn { background: none; border: none; color: #64748b; font-size: 1.6rem; cursor: pointer; }

        /* Periodic Table Grid Style */
        .periodic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px; max-height: 400px; overflow-y: auto; padding: 5px; }
        .element-card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .element-card:hover { border-color: #38bdf8; transform: translateY(-3px); background: #2563eb22; }
        .element-card .sym { font-size: 1.2rem; font-weight: bold; color: #38bdf8; }
        .element-card .num { font-size: 0.7rem; color: #94a3b8; }
        .element-card .name { font-size: 0.8rem; color: #f8fafc; margin-top: 4px; }

        /* AI Interactive Chat */
        .chat-box { display: flex; flex-direction: column; gap: 12px; height: 300px; overflow-y: auto; padding: 12px; background: #030712; border-radius: 12px; border: 1px solid #1e293b; }
        .message { padding: 12px 16px; border-radius: 12px; max-width: 82%; font-size: 0.88rem; line-height: 1.5; }
        .message.ai { background: #1e293b; color: #f3f4f6; align-self: flex-start; border-right: 3px solid #38bdf8; }
        .message.user { background: #0284c7; color: #fff; align-self: flex-end; }
        .chat-input-area { display: flex; gap: 10px; }
        .chat-input-area input { flex: 1; background: #030712; border: 1px solid #1e293b; padding: 12px 16px; border-radius: 10px; color: #fff; outline: none; }
        .chat-input-area button { background: #0284c7; color: #fff; border: none; padding: 0 22px; border-radius: 10px; font-weight: bold; cursor: pointer; }

        /* Articles List */
        .article-item { background: #1e293b; padding: 14px; border-radius: 12px; border-left: 4px solid #38bdf8; margin-bottom: 10px; }
        .article-item h4 { color: #38bdf8; margin-bottom: 5px; }
        .article-item p { color: #94a3b8; font-size: 0.85rem; line-height: 1.5; }

        @media (max-width: 768px) {
            .workspace { flex-direction: column-reverse; }
            sidebar { width: 100%; height: 230px; }
            .hud-panel { top: 10px; right: 10px; left: 10px; max-width: none; }
        }
    </style>
</head>
<body>

    <header>
        <div class="logo">
            <span>🔬 NovaLab 3D Ultimate</span>
        </div>
        <div class="badge">Amazon Developer Edition v4.0</div>
    </header>

    <div class="workspace">
        <sidebar>
            <div class="section-title">🧬 قسم الأحياء والعلوم الحيوية</div>
            <button class="nav-btn bio-btn" onclick="switchExperiment('dna_helix', this)">
                <span>🧬 حلزون الحمض النووي (DNA)</span>
                <small style="color:#fbcfe8">وراثة وشفرة</small>
            </button>

            <div class="section-title">📊 قسم العناصر والجدول الدوري</div>
            <button class="nav-btn table-btn" onclick="openModal('periodicModal')">
                <span>🧪 موسوعة العناصر الكيميائية</span>
                <small>جميع العناصر</small>
            </button>

            <div class="section-title">🧪 التجارب الكيميائية والمعادلات</div>
            <button class="nav-btn active" onclick="switchExperiment('sodium_water', this)">
                <span>💥 تفاعل الصوديوم مع الماء</span>
                <small style="color:#ef4444">معادلة حقيقية</small>
            </button>
            <button class="nav-btn" onclick="switchExperiment('acid_base', this)">
                <span>🧪 تفاعل التعادل (حمض+قاعدة)</span>
                <small style="color:#10b981">تغير لون</small>
            </button>
            <button class="nav-btn" onclick="switchExperiment('methane', this)">
                <span>🔥 احتراق الميثان CH₄</span>
                <small style="color:#f59e0b">طاقة حرارية</small>
            </button>
            <button class="nav-btn" onclick="switchExperiment('water', this)">
                <span>💧 تخليق جزيء الماء H₂O</span>
                <small style="color:#38bdf8">روابط تساهمية</small>
            </button>

            <div class="section-title">⚡ الفيزياء وميكانيكا الكم</div>
            <button class="nav-btn" onclick="switchExperiment('atom', this)">
                <span>⚛️ نموذج الذرة والمدارات</span>
                <small style="color:#a855f7">كوانتم</small>
            </button>
            <button class="nav-btn" onclick="switchExperiment('solar', this)">
                <span>🪐 الجاذبية وحركة الأجرام</span>
                <small style="color:#06b6d4">فلك</small>
            </button>

            <div class="section-title">🤖 الذكاء الاصطناعي والمواد</div>
            <button class="nav-btn ai-btn" onclick="openModal('aiModal')">
                <span>🤖 المعلم الذكي (AI Science)</span>
            </button>
            <button class="nav-btn" onclick="openModal('subjectsModal')">
                <span>📖 جميع المواد المقررة</span>
            </button>
            <button class="nav-btn" onclick="openModal('articlesModal')">
                <span>📚 المقالات العلمية</span>
            </button>
            <button class="nav-btn" onclick="openModal('devModal')">
                <span>👨‍💻 المطور والقناة الرسمية</span>
            </button>
        </sidebar>

        <main>
            <div id="viewport"></div>

            <div class="hud-panel">
                <h2 id="exp-title">تفاعل الصوديوم مع الماء</h2>
                <div class="equation" id="exp-eq">2Na + 2H₂O → 2NaOH + H₂ ↑</div>
                <p id="exp-desc">تفاعل شديد الانبعاث للحرارة، يتفاعل فلز الصوديوم مع الماء لينطلق غاز الهيدروجين مع لهب متوهج.</p>
                
                <div class="data-grid">
                    <div class="data-item">
                        <span>نوع التفاعل</span>
                        <strong id="data-type">إحلال أحادي</strong>
                    </div>
                    <div class="data-item">
                        <span>درجة الحرارة</span>
                        <strong id="data-temp">~ 800° C</strong>
                    </div>
                    <div class="data-item">
                        <span>الإنثالبية (ΔH)</span>
                        <strong id="data-dh">-368 kJ/mol</strong>
                    </div>
                    <div class="data-item">
                        <span>مستوى السلامة</span>
                        <strong id="data-hazard" style="color:#ef4444">خطر للغاية ⚠️</strong>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Periodic Table Modal -->
    <div id="periodicModal" class="modal">
        <div class="modal-content" style="max-width: 850px;">
            <div class="modal-header">
                <h3>📊 موسوعة الجدول الدوري الشاملة (العناصر الكيميائية)</h3>
                <button class="close-btn" onclick="closeModal('periodicModal')">&times;</button>
            </div>
            <p style="color: #94a3b8; font-size: 0.88rem;">اضغط على أي عنصر لعرض خصائصه الكاملة، العدد الذري، الكتلة، والتصنيف العلمي:</p>
            <div class="periodic-grid" id="periodicGrid"></div>
            <div id="elementDetailBox" style="background: #1e293b; padding: 16px; border-radius: 12px; border: 1px solid #38bdf8; display: none;">
                <h4 id="elTitle" style="color: #38bdf8; margin-bottom: 6px;"></h4>
                <p id="elInfo" style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.5;"></p>
            </div>
        </div>
    </div>

    <!-- AI Modal -->
    <div id="aiModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>🤖 مساعد العلوم والذكاء الاصطناعي</h3>
                <button class="close-btn" onclick="closeModal('aiModal')">&times;</button>
            </div>
            <div class="chat-box" id="chatBox">
                <div class="message ai">مرحباً بك في المعمل الذكي! اسألني عن الأحياء، الوراثة، العناصر الكيميائية، أو التفاعلات المعملية.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="اسأل عن أي عنصر أو تفاعل..." onkeypress="handleKeyPress(event)">
                <button onclick="sendAiMessage()">إرسال</button>
            </div>
        </div>
    </div>

    <!-- Subjects Modal -->
    <div id="subjectsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📖 قائمة جميع المواد والتجارب المقررة</h3>
                <button class="close-btn" onclick="closeModal('subjectsModal')">&times;</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="background:#1e293b; padding:14px; border-radius:12px;">
                    <h4 style="color:#ec4899;">🧬 قسم الأحياء والوراثة (Biology)</h4>
                    <p style="color:#94a3b8; font-size:0.85rem;">تركيب الخلية الحية، الحمض النووي (DNA)، الوراثة الجزيئية، والتفاعلات الحيوية داخل الكائنات.</p>
                </div>
                <div style="background:#1e293b; padding:14px; border-radius:12px;">
                    <h4 style="color:#38bdf8;">🧪 قسم الكيمياء (Chemistry)</h4>
                    <p style="color:#94a3b8; font-size:0.85rem;">التفاعلات الكيميائية، الجدول الدوري، الروابط التساهمية والأيونية، والكيمياء العضوية.</p>
                </div>
                <div style="background:#1e293b; padding:14px; border-radius:12px;">
                    <h4 style="color:#a855f7;">⚡ قسم الفيزياء (Physics)</h4>
                    <p style="color:#94a3b8; font-size:0.85rem;">الميكانيكا، الحركة الموجية، الذرة والتأين، والدوائر الكهربائية الثلاثية الأبعاد.</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Articles Modal -->
    <div id="articlesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📚 مقالات وروابط علمية متقدمة</h3>
                <button class="close-btn" onclick="closeModal('articlesModal')">&times;</button>
            </div>
            <div class="article-item">
                <h4>1. شفرة الحياة: كيف يعمل الحمض النووي (DNA)</h4>
                <p>تخزين المعلومات الوراثية وتتابع القواعد النيتروجينية (A, T, C, G) في بناء الكائنات الحية.</p>
            </div>
            <div class="article-item">
                <h4>2. الرابطة التساهمية ودورها في تكوين الجزيئات</h4>
                <p>كيف تتشارك الذرات الإلكترونات للوصول إلى حالة الاستقرار الطاقي وكيف نراها في نماذج 3D.</p>
            </div>
            <div class="article-item">
                <h4>3. الجاذبية الفضائية وقوانين الكبلر</h4>
                <p>تفسير حركة الكواكب والأجرام السماوية في الفضاء المفتوح والمدارات الافتراضية.</p>
            </div>
        </div>
    </div>

    <!-- Dev Modal -->
    <div id="devModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>👨‍💻 المطور والمعلومات الرسمية</h3>
                <button class="close-btn" onclick="closeModal('devModal')">&times;</button>
            </div>
            <div style="text-align:center; padding:10px; display:flex; flex-direction:column; gap:12px;">
                <h4 style="color:#38bdf8; font-size:1.3rem;">NOVA eHUB 26 Team</h4>
                <p style="color:#94a3b8;">تطبيق المختبر العلمي ثلاثي الأبعاد المخصص لمنافسات أمازون وتطبيقات Android و Fire OS.</p>
                <button onclick="window.open('https://t.me/', '_blank')" style="background:#0284c7; color:#fff; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📢 القناة الرسمية والبوت علي تلجرام</button>
            </div>
        </div>
    </div>

    <script>
        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }

        const elementsData = [
            {num: 1, sym: "H", name: "هيدروجين", mass: "1.008", cat: "لا فلز", desc: "أخف عناصر الكون وأكثرها وفراً، يدخل في تركيب الماء والهيدروكربونات."},
            {num: 2, sym: "He", name: "هيليوم", mass: "4.003", cat: "غاز نبيل", desc: "غاز خامل وغير سام، خفيف الوزن يستعمل في بالونات الهواء والتبريد."},
            {num: 3, sym: "Li", name: "ليثيوم", mass: "6.94", cat: "فلز قلوي", desc: "أخف الفلزات الصلبة، شديد النشاط، يدخل في صناعة بطاريات أيون الليثيوم."},
            {num: 6, sym: "C", name: "كربون", mass: "12.011", cat: "لا فلز", desc: "أساس الكيمياء العضوية، يتواجد على شكل ألماس وجرافيت."},
            {num: 7, sym: "N", name: "نيتروجين", mass: "14.007", cat: "لا فلز", desc: "يشكل 78% من الغلاف الجوي للأرض، ضروري لتكوين الأحماض الأمينية."},
            {num: 8, sym: "O", name: "أكسجين", mass: "15.999", cat: "لا فلز", desc: "أساس عملية التنفس والاحتراق، يشكل مركبات حيوية مع أغلب العناصر."},
            {num: 11, sym: "Na", name: "صوديوم", mass: "22.990", cat: "فلز قلوي", desc: "فلز نشط جداً، يتفاعل بعنف مع الماء وينتج هيدروكسيد الصوديوم."},
            {num: 12, sym: "Mg", name: "مغنيسيوم", mass: "24.305", cat: "فلز قلوي ترابي", desc: "يحترق بضوء أبيض ساطع، يدخل في السبائك الخفيفة والألعاب النارية."},
            {num: 17, sym: "Cl", name: "كلور", mass: "35.45", cat: "هالوجين", desc: "غاز سام ذو لون أصفر مخضر، يدخل في التعقيم وتكوين ملح الطعام (NaCl)."},
            {num: 26, sym: "Fe", name: "حديد", mass: "55.845", cat: "فلز انتقالي", desc: "أهم الفلزات الهندسية والصناعية، يدخل في الهياكل والدم (الهيموجلوبين)."},
            {num: 29, sym: "Cu", name: "نحاس", mass: "63.546", cat: "فلز انتقالي", desc: "موصل ممتاز للكهرباء والحرارة، ذو لون مميز ومقاوم للتآكل."},
            {num: 79, sym: "Au", name: "ذهب", mass: "196.97", cat: "فلز انتقالي", desc: "فلز ثمين خامل لا يتفاعل بسهولة مع الأحماض، يستخدم في الحلي والإلكترونيات."}
        ];

        function loadPeriodicTable() {
            const grid = document.getElementById('periodicGrid');
            grid.innerHTML = '';
            elementsData.forEach(el => {
                grid.innerHTML += `
                    <div class="element-card" onclick="showElementDetail(${el.num})">
                        <span class="num">${el.num}</span>
                        <div class="sym">${el.sym}</div>
                        <div class="name">${el.name}</div>
                    </div>
                `;
            });
        }

        function showElementDetail(num) {
            const el = elementsData.find(item => item.num === num);
            if(el) {
                const box = document.getElementById('elementDetailBox');
                box.style.display = 'block';
                document.getElementById('elTitle').innerText = `${el.name} (${el.sym}) - العدد الذري: ${el.num}`;
                document.getElementById('elInfo').innerHTML = `<strong>الكتلة الذرية:</strong> ${el.mass} u<br><strong>التصنيف:</strong> ${el.cat}<br><strong>الخصائص والاستخدام:</strong> ${el.desc}`;
            }
        }

        window.addEventListener('DOMContentLoaded', loadPeriodicTable);

        function sendAiMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = input.value.trim();
            if(!text) return;

            chatBox.innerHTML += `<div class="message user">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            setTimeout(() => {
                let reply = "سؤال علمي ممتاز! هذا العنصر أو التفاعل يخضع لقوانين الكيمياء والبيولوجيا الجزيئية.";
                if(text.includes('dna') || text.includes('وراثة') || text.includes('حمض')) {
                    reply = "الحمض النووي (DNA) يتكون من شريطين ملتفين حول بعضهما بشكل حلزوني مزدوج ويرتبط بـ 4 قواعد أساسية (A, T, C, G).";
                } else if(text.includes('صوديوم') || text.includes('Na')) {
                    reply = "الصوديوم (Na) عدد الذري 11، فلز قلوي نشط جداً يتفاعل مع الماء لينتج NaOH وغاز الهيدروجين.";
                }
                chatBox.innerHTML += `<div class="message ai">${reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }, 700);
        }

        function handleKeyPress(e) { if(e.key === 'Enter') sendAiMessage(); }

        // Three.js Science Engine
        let scene, camera, renderer, controls, activeGroup, particleSystem;

        function init() {
            const container = document.getElementById('viewport');
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 2, 8);

            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);

            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;

            scene.add(new THREE.AmbientLight(0xffffff, 0.9));
            const light = new THREE.DirectionalLight(0x38bdf8, 1.2);
            light.position.set(5, 10, 7);
            scene.add(light);

            activeGroup = new THREE.Group();
            scene.add(activeGroup);

            window.addEventListener('resize', onResize);
            buildSodiumWaterExp();
            animate();
        }

        function clearScene() {
            particleSystem = null;
            while (activeGroup.children.length > 0) {
                const obj = activeGroup.children[0];
                if (obj.geometry) obj.geometry.dispose();
                activeGroup.remove(obj);
            }
        }

        function switchExperiment(type, el) {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            if(el) el.classList.add('active');
            clearScene();

            if (type === 'dna_helix') {
                updateHUD("حلزون الحمض النووي (DNA Double Helix)", "A ⟷ T  |  C ⟷ G", "نموذج ثلاثي الأبعاد يمثل بنية الـ DNA الحلزونية المزدوجة التي تحمل الشفرة الوراثية وتوجيه العمليات الحيوية.", "وراثة جزيئية", "37° C (جسم حي)", "N/A", "آمن تماماً 🟢");
                buildDnaModel();
            } else if (type === 'sodium_water') {
                updateHUD("تفاعل الصوديوم مع الماء", "2Na + 2H₂O → 2NaOH + H₂ ↑", "تفاعل شديد الانبعاث للحرارة، يتفاعل فلز الصوديوم مع الماء لينطلق غاز الهيدروجين.", "إحلال أحادي", "~ 800° C", "-368 kJ/mol", "خطر للغاية ⚠️");
                buildSodiumWaterExp();
            } else if (type === 'acid_base') {
                updateHUD("تفاعل التعادل (حمض + قاعدة)", "HCl + NaOH → NaCl + H₂O", "عند إضافة حمض الهيدروكلوريك إلى هيدروكسيد الصوديوم يتكون ملح الطعام والماء.", "تعادل كيميائي", "25° C", "-57.3 kJ/mol", "آمن بحذر 🟢");
                buildAcidBaseExp();
            } else if (type === 'methane') {
                updateHUD("احتراق الميثان (CH₄)", "CH₄ + 2O₂ → CO₂ + 2H₂O", "مركب هيدروكربوني يحترق بوجود الأكسجين ليعطي غاز ثاني أكسيد الكربون وبخار الماء وطاقة هائلة.", "احتراق عضوي", "650° C", "-891 kJ/mol", "قابل للاشتعال 🔥");
                buildMethaneMolecule();
            } else if (type === 'water') {
                updateHUD("جزيء الماء (H₂O)", "2H₂ + O₂ → 2H₂O", "نموذج ثلاثي الأبعاد يوضح الرابطة التساهمية بين الأكسجين والهيدروجين.", "تركيب جزيئي", "20° C", "N/A", "آمن تماماً 🟢");
                buildWaterMolecule();
            } else if (type === 'atom') {
                updateHUD("نموذج الذرة ومدارات الطاقة", "E = hν", "محاكاة كمية للذرة تحتوي على نواة وإلكترونات تدور في مستويات طاقة محددة.", "فيزياء الكوانتم", "0 K", "N/A", "آمن 🟢");
                buildAtomModel();
            } else if (type === 'solar') {
                updateHUD("الجاذبية وحركة الكواكب", "F = G(m1 m2)/r²", "قانون الجاذبية العامة يوضح دوران الكواكب في مدارات حول مركز الكتلة.", "فيزياء فلكية", "متغير", "N/A", "آمن 🟢");
                buildSolarSystem();
            }
        }

        function updateHUD(title, eq, desc, type, temp, dh, hazard) {
            document.getElementById('exp-title').innerText = title;
            document.getElementById('exp-eq').innerText = eq;
            document.getElementById('exp-desc').innerText = desc;
            document.getElementById('data-type').innerText = type;
            document.getElementById('data-temp').innerText = temp;
            document.getElementById('data-dh').innerText = dh;
            document.getElementById('data-hazard').innerText = hazard;
        }

        // --- نموذج DNA ثلاثي الأبعاد ---
        function buildDnaModel() {
            for (let i = -3; i <= 3; i += 0.4) {
                const sphere1 = new THREE.Mesh(
                    new THREE.SphereGeometry(0.22, 16, 16),
                    new THREE.MeshStandardMaterial({ color: 0xec4899, emissive: 0xbe185d })
                );
                sphere1.position.set(Math.sin(i * 1.5) * 1.5, i * 0.5, Math.cos(i * 1.5) * 1.5);
                activeGroup.add(sphere1);

                const sphere2 = new THREE.Mesh(
                    new THREE.SphereGeometry(0.22, 16, 16),
                    new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0284c7 })
                );
                sphere2.position.set(Math.sin(i * 1.5 + Math.PI) * 1.5, i * 0.5, Math.cos(i * 1.5 + Math.PI) * 1.5);
                activeGroup.add(sphere2);
            }
        }

        function buildSodiumWaterExp() {
            const glass = new THREE.Mesh(new THREE.CylinderGeometry(1.8, 1.8, 3, 32, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xffffff, transparent: true, opacity: 0.3, transmission: 0.9 }));
            activeGroup.add(glass);
            const water = new THREE.Mesh(new THREE.CylinderGeometry(1.75, 1.75, 2, 32), new THREE.MeshStandardMaterial({ color: 0x0284c7, transparent: true, opacity: 0.7 }));
            water.position.y = -0.4;
            activeGroup.add(water);
            const sodium = new THREE.Mesh(new THREE.DodecahedronGeometry(0.35), new THREE.MeshStandardMaterial({ color: 0xf97316, emissive: 0xef4444, emissiveIntensity: 0.8 }));
            sodium.position.set(0, 0.5, 0);
            activeGroup.add(sodium);

            const pGeo = new THREE.BufferGeometry();
            const count = 150;
            const pos = new Float32Array(count * 3);
            for(let i=0; i<count*3; i+=3) {
                pos[i] = (Math.random() - 0.5) * 1.2;
                pos[i+1] = Math.random() * 2 + 0.5;
                pos[i+2] = (Math.random() - 0.5) * 1.2;
            }
            pGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
            particleSystem = new THREE.Points(pGeo, new THREE.PointsMaterial({ color: 0xfacc15, size: 0.08, transparent: true, opacity: 0.8 }));
            activeGroup.add(particleSystem);
        }

        function buildAcidBaseExp() {
            const flask = new THREE.Mesh(new THREE.ConeGeometry(2, 3, 32), new THREE.MeshPhysicalMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 }));
            activeGroup.add(flask);
            const liquid = new THREE.Mesh(new THREE.ConeGeometry(1.8, 2.2, 32), new THREE.MeshStandardMaterial({ color: 0xec4899, transparent: true, opacity: 0.8 }));
            liquid.position.y = -0.3;
            activeGroup.add(liquid);
        }

        function buildWaterMolecule() {
            const oxy = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 32), new THREE.MeshStandardMaterial({ color: 0xef4444 }));
            activeGroup.add(oxy);
            const hMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc });
            const h1 = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), hMat); h1.position.set(-1.3, -0.7, 0);
            const h2 = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), hMat); h2.position.set(1.3, -0.7, 0);
            activeGroup.add(h1); activeGroup.add(h2);
        }

        function buildMethaneMolecule() {
            const carbon = new THREE.Mesh(new THREE.SphereGeometry(0.9, 32, 32), new THREE.MeshStandardMaterial({ color: 0x3b82f6 }));
            activeGroup.add(carbon);
            [[1.1, 1.1, 1.1], [-1.1, -1.1, 1.1], [-1.1, 1.1, -1.1], [1.1, -1.1, -1.1]].forEach(pos => {
                const h = new THREE.Mesh(new THREE.SphereGeometry(0.45, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf8fafc }));
                h.position.set(...pos); activeGroup.add(h);
            });
        }

        function buildAtomModel() {
            const nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xd97706 }));
            activeGroup.add(nucleus);
            for (let i = 0; i < 3; i++) {
                const ring = new THREE.Mesh(new THREE.TorusGeometry(1.8 + (i * 0.4), 0.02, 16, 100), new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true }));
                ring.rotation.x = Math.PI / (i + 1); ring.rotation.y = Math.PI / (i + 2);
                activeGroup.add(ring);
            }
        }

        function buildSolarSystem() {
            const sun = new THREE.Mesh(new THREE.SphereGeometry(1.2, 32, 32), new THREE.MeshBasicMaterial({ color: 0xf97316 }));
            activeGroup.add(sun);
            const planet = new THREE.Mesh(new THREE.SphereGeometry(0.4, 32, 32), new THREE.MeshStandardMaterial({ color: 0x06b6d4 }));
            planet.position.x = 2.8;
            activeGroup.add(planet);
        }

        function animate() {
            requestAnimationFrame(animate);
            if (activeGroup) activeGroup.rotation.y += 0.006;
            
            if (particleSystem) {
                const positions = particleSystem.geometry.attributes.position.array;
                for (let i = 1; i < positions.length; i += 3) {
                    positions[i] += 0.02;
                    if (positions[i] > 2.5) positions[i] = 0.5;
                }
                particleSystem.geometry.attributes.position.needsUpdate = true;
            }

            controls.update();
            renderer.render(scene, camera);
        }

        function onResize() {
            const container = document.getElementById('viewport');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }

        window.onload = init;
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
