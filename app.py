from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaLab 3D Ultimate — Virtual Science & Real Lab</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body { background-color: #030712; color: #f9fafb; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

        /* Header */
        header { background: rgba(17, 24, 39, 0.95); backdrop-filter: blur(16px); padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(56, 189, 248, 0.2); z-index: 20; }
        .logo { font-size: 1.3rem; font-weight: 800; color: #38bdf8; display: flex; align-items: center; gap: 10px; }
        .badge { background: linear-gradient(135deg, #0284c7, #4f46e5); color: #fff; font-size: 0.75rem; padding: 5px 14px; border-radius: 20px; font-weight: 700; }

        /* Main Layout */
        .workspace { display: flex; flex: 1; height: calc(100vh - 60px); position: relative; }

        /* Sidebar Navigation Cards */
        sidebar { width: 340px; background: #0f172a; padding: 16px; border-left: 1px solid #1e293b; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; z-index: 10; }
        sidebar::-webkit-scrollbar { width: 5px; }
        sidebar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        
        .menu-category { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #38bdf8; margin-top: 8px; letter-spacing: 1px; }

        .menu-card { background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px 14px; border-radius: 12px; cursor: pointer; transition: all 0.25s ease; display: flex; flex-direction: column; gap: 4px; }
        .menu-card:hover { background: #334155; border-color: #38bdf8; transform: translateX(-3px); }
        .menu-card.active { background: linear-gradient(135deg, #0284c7, #0369a1); border-color: #38bdf8; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4); }
        
        .menu-card-title { font-size: 0.9rem; font-weight: 700; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .menu-card-desc { font-size: 0.75rem; color: #94a3b8; line-height: 1.3; }
        .menu-card.active .menu-card-desc { color: #e2e8f0; }

        /* Viewport Canvas */
        main { flex: 1; position: relative; background: radial-gradient(circle at center, #111827 0%, #030712 100%); }
        #viewport { width: 100%; height: 100%; }

        /* HUD Panel */
        .hud-panel { position: absolute; top: 20px; right: 20px; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(16px); border: 1px solid rgba(56, 189, 248, 0.3); padding: 20px; border-radius: 16px; max-width: 400px; box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.8); pointer-events: auto; }
        .hud-panel h2 { font-size: 1.15rem; color: #38bdf8; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
        .hud-panel .equation { background: #090d16; border: 1px solid #1e293b; color: #10b981; padding: 6px 10px; border-radius: 8px; font-family: monospace; font-size: 0.85rem; margin: 6px 0; text-align: center; }
        .hud-panel p { font-size: 0.82rem; line-height: 1.5; color: #94a3b8; }
        
        /* Real Lab Photo Preview in HUD */
        .real-photo-box { margin-top: 10px; border-radius: 10px; overflow: hidden; border: 1px solid #334155; height: 120px; position: relative; }
        .real-photo-box img { width: 100%; height: 100%; object-fit: cover; }
        .real-photo-label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(3, 7, 18, 0.8); font-size: 0.7rem; color: #38bdf8; padding: 3px 8px; text-align: center; }

        .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 10px; border-top: 1px solid #1e293b; padding-top: 8px; }
        .data-item { background: rgba(30, 41, 59, 0.5); padding: 6px 8px; border-radius: 8px; }
        .data-item span { display: block; font-size: 0.68rem; color: #64748b; }
        .data-item strong { font-size: 0.78rem; color: #e2e8f0; }

        /* Modals */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #0f172a; border: 1px solid #38bdf8; width: 92%; max-width: 800px; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.9); max-height: 85vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
        .modal-header h3 { color: #38bdf8; font-size: 1.25rem; }
        .close-btn { background: none; border: none; color: #64748b; font-size: 1.6rem; cursor: pointer; }

        /* Periodic Table */
        .periodic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(105px, 1fr)); gap: 10px; max-height: 400px; overflow-y: auto; padding: 5px; }
        .element-card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .element-card:hover { border-color: #38bdf8; transform: translateY(-3px); background: #2563eb22; }
        .element-card .sym { font-size: 1.2rem; font-weight: bold; color: #38bdf8; }
        .element-card .num { font-size: 0.7rem; color: #94a3b8; }
        .element-card .name { font-size: 0.8rem; color: #f8fafc; margin-top: 4px; }

        /* AI Chat */
        .chat-box { display: flex; flex-direction: column; gap: 12px; height: 300px; overflow-y: auto; padding: 12px; background: #030712; border-radius: 12px; border: 1px solid #1e293b; }
        .message { padding: 12px 16px; border-radius: 12px; max-width: 82%; font-size: 0.88rem; line-height: 1.5; }
        .message.ai { background: #1e293b; color: #f3f4f6; align-self: flex-start; border-right: 3px solid #38bdf8; }
        .message.user { background: #0284c7; color: #fff; align-self: flex-end; }
        .chat-input-area { display: flex; gap: 10px; }
        .chat-input-area input { flex: 1; background: #030712; border: 1px solid #1e293b; padding: 12px 16px; border-radius: 10px; color: #fff; outline: none; }
        .chat-input-area button { background: #0284c7; color: #fff; border: none; padding: 0 22px; border-radius: 10px; font-weight: bold; cursor: pointer; }

        @media (max-width: 768px) {
            .workspace { flex-direction: column-reverse; }
            sidebar { width: 100%; height: 240px; }
            .hud-panel { top: 10px; right: 10px; left: 10px; max-width: none; }
        }
    </style>
</head>
<body>

    <header>
        <div class="logo"><span>🔬 NovaLab 3D Ultimate</span></div>
        <div class="badge">Amazon Developer Edition v5.0</div>
    </header>

    <div class="workspace">
        <sidebar>
            <div class="menu-category">🧬 الأحياء والوراثة الحيوية</div>
            <div class="menu-card" onclick="switchExperiment('dna_helix', this)">
                <div class="menu-card-title">حلزون الحمض النووي (DNA) <span>🧬</span></div>
                <div class="menu-card-desc">بنية الـ DNA وشفرة الحياة والقواعد النيتروجينية الحقيقية.</div>
            </div>

            <div class="menu-category">📊 الكيمياء والجدول الدوري</div>
            <div class="menu-card" onclick="openModal('periodicModal')">
                <div class="menu-card-title">موسوعة الجدول الدوري الشاملة <span>📊</span></div>
                <div class="menu-card-desc">جميع العناصر، العدد الذري، الكتلة، والخصائص والصور الحقيقية.</div>
            </div>

            <div class="menu-category">💥 المعمل والتجارب الحقيقية</div>
            <div class="menu-card active" onclick="switchExperiment('sodium_water', this)">
                <div class="menu-card-title">تفاعل الصوديوم مع الماء <span>💥</span></div>
                <div class="menu-card-desc">محاكاة تفاعل فلز نشط مع الماء وانبعاث غاز الهيدروجين والحرارة.</div>
            </div>
            <div class="menu-card" onclick="switchExperiment('acid_base', this)">
                <div class="menu-card-title">تفاعل التعادل (حمض + قاعدة) <span>🧪</span></div>
                <div class="menu-card-desc">إضافة حمض الهيدروكلوريك إلى هيدروكسيد الصوديوم وتغير اللون.</div>
            </div>
            <div class="menu-card" onclick="switchExperiment('methane', this)">
                <div class="menu-card-title">احتراق الميثان العضوي (CH₄) <span>🔥</span></div>
                <div class="menu-card-desc">التفاعل الطارد للحرارة وتكوين ثاني أكسيد الكربون وبخار الماء.</div>
            </div>
            <div class="menu-card" onclick="switchExperiment('water', this)">
                <div class="menu-card-title">تخليق جزيء الماء (H₂O) <span>💧</span></div>
                <div class="menu-card-desc">الروابط التساهمية بين ذرة الأكسجين وذرتي الهيدروجين.</div>
            </div>

            <div class="menu-category">⚡ الفيزياء وميكانيكا الكم</div>
            <div class="menu-card" onclick="switchExperiment('atom', this)">
                <div class="menu-card-title">نموذج الذرة والمدارات <span>⚛️</span></div>
                <div class="menu-card-desc">النواة الكثيفة ومستويات الطاقة ودوران الإلكترونات.</div>
            </div>
            <div class="menu-card" onclick="switchExperiment('solar', this)">
                <div class="menu-card-title">الجاذبية وحركة الأجرام <span>🪐</span></div>
                <div class="menu-card-desc">قانون الجاذبية العامة ومدارات الكواكب الفلكية.</div>
            </div>

            <div class="menu-category">🤖 الذكاء الاصطناعي والمطور</div>
            <div class="menu-card" style="background: linear-gradient(135deg, #7c3aed, #4f46e5);" onclick="openModal('aiModal')">
                <div class="menu-card-title">المعلم الذكي (AI Science) <span>🤖</span></div>
                <div class="menu-card-desc">مساعدك الذكي للإجابة عن أي استفسار معملي أو علمي.</div>
            </div>
            <div class="menu-card" onclick="openModal('devModal')">
                <div class="menu-card-title">المطور والقناة الرسمية <span>👨‍💻</span></div>
                <div class="menu-card-desc">معلومات فريق العمل وقناة التلجرام الرسمية والبوت.</div>
            </div>
        </sidebar>

        <main>
            <div id="viewport"></div>

            <div class="hud-panel">
                <h2 id="exp-title">تفاعل الصوديوم مع الماء</h2>
                <div class="equation" id="exp-eq">2Na + 2H₂O → 2NaOH + H₂ ↑</div>
                <p id="exp-desc">تفاعل شديد الانبعاث للحرارة، يتفاعل فلز الصوديوم مع الماء لينطلق غاز الهيدروجين مع لهب متوهج.</p>
                
                <div class="real-photo-box">
                    <img id="real-img" src="https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=600&q=80" alt="تجربة معملية حقيقية">
                    <div class="real-photo-label" id="real-label">صورة حقيقية من داخل المعمل الكيميائي</div>
                </div>

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
            <p style="color: #94a3b8; font-size: 0.88rem;">اضغط على أي عنصر لعرض خصائصه الكاملة، العدد الذري، الكتلة، وصورته الحقيقية:</p>
            <div class="periodic-grid" id="periodicGrid"></div>
            <div id="elementDetailBox" style="background: #1e293b; padding: 16px; border-radius: 12px; border: 1px solid #38bdf8; display: none; display: flex; gap: 15px; align-items: center;">
                <img id="elImg" src="" style="width: 120px; height: 90px; object-fit: cover; border-radius: 8px; border: 1px solid #334155;">
                <div>
                    <h4 id="elTitle" style="color: #38bdf8; margin-bottom: 4px;"></h4>
                    <p id="elInfo" style="color: #cbd5e1; font-size: 0.85rem; line-height: 1.4;"></p>
                </div>
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
                <div class="message ai">مرحباً بك في المعمل الذكي! اسألني عن أي تفاعل معملي، عنصر، أو شفرة DNA.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="اسأل عن أي تفاعل أو عنصر..." onkeypress="handleKeyPress(event)">
                <button onclick="sendAiMessage()">إرسال</button>
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
            {num: 1, sym: "H", name: "هيدروجين", mass: "1.008", cat: "لا فلز", desc: "أخف عناصر الكون، يدخل في تركيب الماء.", img: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=300&q=80"},
            {num: 2, sym: "He", name: "هيليوم", mass: "4.003", cat: "غاز نبيل", desc: "غاز خامل خفيف الوزن يستعمل في التبريد والبالونات.", img: "https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?auto=format&fit=crop&w=300&q=80"},
            {num: 3, sym: "Li", name: "ليثيوم", mass: "6.94", cat: "فلز قلوي", desc: "أخف الفلزات الصلبة، يدخل في بطاريات أيون الليثيوم.", img: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=300&q=80"},
            {num: 6, sym: "C", name: "كربون", mass: "12.011", cat: "لا فلز", desc: "أساس الكيمياء العضوية، يتواجد على شكل ألماس وجرافيت.", img: "https://images.unsplash.com/photo-1603398938378-e54eab446dde?auto=format&fit=crop&w=300&q=80"},
            {num: 8, sym: "O", name: "أكسجين", mass: "15.999", cat: "لا فلز", desc: "أساس عملية التنفس والاحتراق في الطبيعة.", img: "https://images.unsplash.com/photo-1576086213369-97a306d36557?auto=format&fit=crop&w=300&q=80"},
            {num: 11, sym: "Na", name: "صوديوم", mass: "22.990", cat: "فلز قلوي", desc: "فلز نشط جداً يتفاعل بعنف مع الماء.", img: "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=300&q=80"},
            {num: 17, sym: "Cl", name: "كلور", mass: "35.45", cat: "هالوجين", desc: "غاز ذو لون أصفر مخضر يستخدم في التعقيم وتكوين ملح الطعام.", img: "https://images.unsplash.com/photo-1579154341154-e67213f88f08?auto=format&fit=crop&w=300&q=80"},
            {num: 26, sym: "Fe", name: "حديد", mass: "55.845", cat: "فلز انتقالي", desc: "أهم الفلزات الهندسية والصناعية والهيموجلوبين في الدم.", img: "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=300&q=80"},
            {num: 79, sym: "Au", name: "ذهب", mass: "196.97", cat: "فلز انتقالي", desc: "فلز ثمين خامل لا يتفاعل بسهولة مع الأحماض.", img: "https://images.unsplash.com/photo-1610375461246-83df859d849d?auto=format&fit=crop&w=300&q=80"}
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
                box.style.display = 'flex';
                document.getElementById('elTitle').innerText = `${el.name} (${el.sym}) - العدد الذري: ${el.num}`;
                document.getElementById('elInfo').innerHTML = `<strong>الكتلة الذرية:</strong> ${el.mass} u<br><strong>التصنيف:</strong> ${el.cat}<br><strong>الخصائص:</strong> ${el.desc}`;
                document.getElementById('elImg').src = el.img;
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
                let reply = "سؤال علمي ممتاز! هذا التفاعل يوضح بدقة قوانين الكيمياء الفيزيائية.";
                if(text.includes('صوديوم') || text.includes('Na')) {
                    reply = "الصوديوم (Na) فلز قلوي يتفاعل مع الماء لينطلق غاز الهيدروجين وينتج هيدروكسيد الصوديوم.";
                } else if(text.includes('dna') || text.includes('وراثة')) {
                    reply = "الحمض النووي (DNA) يتكون من شريطين ملتفين في هيكل حلزوني مزدوج يحمل الشفرة الوراثية.";
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
            document.querySelectorAll('.menu-card').forEach(b => b.classList.remove('active'));
            if(el) el.classList.add('active');
            clearScene();

            if (type === 'dna_helix') {
                updateHUD("حلزون الحمض النووي (DNA)", "A ⟷ T  |  C ⟷ G", "نموذج ثلاثي الأبعاد يمثل بنية الـ DNA الحلزونية المزدوجة التي تحمل الشفرة الوراثية.", "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?auto=format&fit=crop&w=600&q=80", "صورة حقيقية لتركيب المادة الوراثية والمجهر الإلكتروني", "وراثة جزيئية", "37° C", "N/A", "آمن تماماً 🟢");
                buildDnaModel();
            } else if (type === 'sodium_water') {
                updateHUD("تفاعل الصوديوم مع الماء", "2Na + 2H₂O → 2NaOH + H₂ ↑", "تفاعل شديد الانبعاث للحرارة، يتفاعل فلز الصوديوم مع الماء لينطلق غاز الهيدروجين.", "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=600&q=80", "صورة حقيقية من داخل المعمل الكيميائي", "إحلال أحادي", "~ 800° C", "-368 kJ/mol", "خطر للغاية ⚠️");
                buildSodiumWaterExp();
            } else if (type === 'acid_base') {
                updateHUD("تفاعل التعادل (حمض + قاعدة)", "HCl + NaOH → NaCl + H₂O", "عند إضافة حمض الهيدروكلوريك إلى هيدروكسيد الصوديوم يتكون ملح الطعام والماء.", "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?auto=format&fit=crop&w=600&q=80", "اختبار التفاعل وتغير لون الكواشف المعملية", "تعادل كيميائي", "25° C", "-57.3 kJ/mol", "آمن بحذر 🟢");
                buildAcidBaseExp();
            } else if (type === 'methane') {
                updateHUD("احتراق الميثان (CH₄)", "CH₄ + 2O₂ → CO₂ + 2H₂O", "مركب هيدروكربوني يحترق بوجود الأكسجين ليعطي غاز ثاني أكسيد الكربون وبخار الماء.", "https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&w=600&q=80", "احتراق المواد العضوية في المختبر", "احتراق عضوي", "650° C", "-891 kJ/mol", "قابل للاشتعال 🔥");
                buildMethaneMolecule();
            } else if (type === 'water') {
                updateHUD("جزيء الماء (H₂O)", "2H₂ + O₂ → 2H₂O", "نموذج ثلاثي الأبعاد يوضح الرابطة التساهمية بين الأكسجين والهيدروجين.", "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&w=600&q=80", "عينات المياه النقية وتحليل الروابط", "تركيب جزيئي", "20° C", "N/A", "آمن تماماً 🟢");
                buildWaterMolecule();
            } else if (type === 'atom') {
                updateHUD("نموذج الذرة ومدارات الطاقة", "E = hν", "محاكاة كمية للذرة تحتوي على نواة وإلكترونات تدور في مستويات طاقة.", "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?auto=format&fit=crop&w=600&q=80", "نموذج فيزيائي كمي للذرة", "فيزياء الكوانتم", "0 K", "N/A", "آمن 🟢");
                buildAtomModel();
            } else if (type === 'solar') {
                updateHUD("الجاذبية وحركة الكواكب", "F = G(m1 m2)/r²", "قانون الجاذبية العامة يوضح دوران الكواكب في مدارات حول مركز الكتلة.", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80", "محاكاة الفلك والجاذبية الكونية", "فيزياء فلكية", "متغير", "N/A", "آمن 🟢");
                buildSolarSystem();
            }
        }

        function updateHUD(title, eq, desc, imgSrc, imgLabel, type, temp, dh, hazard) {
            document.getElementById('exp-title').innerText = title;
            document.getElementById('exp-eq').innerText = eq;
            document.getElementById('exp-desc').innerText = desc;
            document.getElementById('real-img').src = imgSrc;
            document.getElementById('real-label').innerText = imgLabel;
            document.getElementById('data-type').innerText = type;
            document.getElementById('data-temp').innerText = temp;
            document.getElementById('data-dh').innerText = dh;
            document.getElementById('data-hazard').innerText = hazard;
        }

        function buildDnaModel() {
            for (let i = -3; i <= 3; i += 0.4) {
                const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 16), new THREE.MeshStandardMaterial({ color: 0xec4899, emissive: 0xbe185d }));
                s1.position.set(Math.sin(i * 1.5) * 1.5, i * 0.5, Math.cos(i * 1.5) * 1.5);
                activeGroup.add(s1);
                const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 16), new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0284c7 }));
                s2.position.set(Math.sin(i * 1.5 + Math.PI) * 1.5, i * 0.5, Math.cos(i * 1.5 + Math.PI) * 1.5);
                activeGroup.add(s2);
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
