from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaLab 3D Ultimate — Ultimate Science & Biology Lab</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body { background-color: #030712; color: #f9fafb; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

        /* Top Header */
        header { background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(16px); padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(56, 189, 248, 0.2); z-index: 20; }
        .logo-area { display: flex; align-items: center; gap: 10px; font-size: 1.3rem; font-weight: 800; color: #38bdf8; }
        .header-icons { display: flex; gap: 12px; align-items: center; }
        .crown-badge { background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }

        /* Main Workspace */
        .workspace { display: flex; flex: 1; height: calc(100vh - 120px); position: relative; overflow: hidden; }

        /* 3D Viewport / Dashboard Container */
        .main-content { flex: 1; position: relative; background: radial-gradient(circle at center, #111827 0%, #030712 100%); overflow-y: auto; padding: 20px; }
        #viewport-container { width: 100%; height: 280px; background: rgba(15, 23, 42, 0.6); border-radius: 16px; border: 1px solid rgba(56, 189, 248, 0.3); position: relative; overflow: hidden; margin-bottom: 20px; }
        #viewport { width: 100%; height: 100%; }

        /* AI Greeting Banner */
        .ai-banner { background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .ai-banner h3 { color: #38bdf8; font-size: 1.1rem; margin-bottom: 4px; }
        .ai-banner p { color: #94a3b8; font-size: 0.85rem; }

        /* Search Bar */
        .search-box { background: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 12px 18px; display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .search-box input { background: none; border: none; color: #fff; width: 100%; outline: none; font-size: 0.9rem; }

        /* 8 Dashboard Cards Grid (Matching the image exactly) */
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 20px; }
        .dash-card { border-radius: 16px; padding: 18px 14px; display: flex; flex-direction: column; gap: 8px; cursor: pointer; transition: all 0.25s ease; box-shadow: 0 10px 20px rgba(0,0,0,0.4); text-align: right; }
        .dash-card:hover { transform: translateY(-4px); filter: brightness(1.1); }
        .dash-card h4 { font-size: 1.05rem; font-weight: 800; color: #fff; }
        .dash-card p { font-size: 0.75rem; color: rgba(255,255,255,0.8); line-height: 1.3; }
        
        /* Card Colors */
        .card-bio { background: linear-gradient(135deg, #059669, #047857); }
        .card-phy { background: linear-gradient(135deg, #0284c7, #0369a1); }
        .card-chem { background: linear-gradient(135deg, #d97706, #b45309); }
        .card-eq { background: linear-gradient(135deg, #7c3aed, #5b21b6); }
        .card-info { background: linear-gradient(135deg, #0d9488, #0f766e); }
        .card-anat { background: linear-gradient(135deg, #dc2626, #991b1b); }
        .card-ai { background: linear-gradient(135deg, #4f46e5, #3730a3); }
        .card-lib { background: linear-gradient(135deg, #2563eb, #1d4ed8); }

        /* Bottom Navigation Bar */
        nav.bottom-nav { background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(16px); height: 60px; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid rgba(56, 189, 248, 0.2); z-index: 20; }
        .nav-item { display: flex; flex-direction: column; align-items: center; gap: 2px; color: #64748b; font-size: 0.7rem; cursor: pointer; transition: 0.2s; }
        .nav-item.active, .nav-item:hover { color: #38bdf8; }
        .nav-item svg { width: 22px; height: 22px; fill: currentColor; }

        /* Modals */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #0f172a; border: 1px solid #38bdf8; width: 92%; max-width: 650px; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.9); max-height: 85vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
        .modal-header h3 { color: #38bdf8; font-size: 1.2rem; }
        .close-btn { background: none; border: none; color: #64748b; font-size: 1.5rem; cursor: pointer; }

        /* Sub-menu items inside modals */
        .sub-item { background: #1e293b; border: 1px solid #334155; padding: 12px 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.2s; margin-bottom: 8px; }
        .sub-item:hover { background: #334155; border-color: #38bdf8; }
        .sub-item span { color: #fff; font-weight: 600; font-size: 0.9rem; }
        
        /* Real Image Preview box */
        .preview-box { border-radius: 12px; overflow: hidden; border: 1px solid #334155; height: 180px; margin-bottom: 12px; position: relative; }
        .preview-box img { width: 100%; height: 100%; object-fit: cover; }
        .preview-label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(3, 7, 18, 0.85); font-size: 0.75rem; color: #38bdf8; padding: 6px 12px; text-align: center; }

        /* AI Chat Box */
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
        <div class="logo-area">
            <span>🔬 NovaLab 3D</span>
        </div>
        <div class="header-icons">
            <span class="crown-badge">👑 النسخة الاحترافية</span>
        </div>
    </header>

    <div class="workspace">
        <div class="main-content">
            
            <!-- AI Greeting Banner -->
            <div class="ai-banner">
                <div>
                    <h3>مرحباً بك في NovaLab 3D Ultimate</h3>
                    <p>رحلتك نحو التفوق والابتكار العلمي تبدأ من هنا 🚀</p>
                </div>
                <div style="font-size: 2.2rem;">🤖</div>
            </div>

            <!-- Search Bar -->
            <div class="search-box">
                <span>🔍</span>
                <input type="text" placeholder="ابحث عن أي موضوع، تجربة، عنصر أو قانون علمي...">
            </div>

            <!-- 8 Main Dashboard Cards (Exact Match to Image 1775.png) -->
            <div class="cards-grid">
                <div class="dash-card card-bio" onclick="openModal('bioModal')">
                    <h4>🌱 أحياء</h4>
                    <p>كل ما يخص علم الأحياء والخلية</p>
                </div>
                <div class="dash-card card-phy" onclick="openModal('phyModal')">
                    <h4>⚡ فيزياء</h4>
                    <p>قوانين - مسائل - شرح مفصل</p>
                </div>
                <div class="dash-card card-chem" onclick="openModal('chemModal')">
                    <h4>🧪 كيمياء</h4>
                    <p>تفاعلات - معادلات - دروس</p>
                </div>
                <div class="dash-card card-eq" onclick="openModal('eqModal')">
                    <h4>📊 معادلات</h4>
                    <p>حل المعادلات خطوة بخطوة</p>
                </div>
                <div class="dash-card card-info" onclick="openModal('infoModal')">
                    <h4>💡 معلومات</h4>
                    <p>تقنية - برمجة - حاسوب</p>
                </div>
                <div class="dash-card card-anat" onclick="openModal('anatModal')">
                    <h4>❤️ تشريح</h4>
                    <p>جسم الإنسان - الأعضاء الحيوية</p>
                </div>
                <div class="dash-card card-ai" onclick="openModal('aiModal')">
                    <h4>🤖 مساعد الذكاء الاصطناعي</h4>
                    <p>اسأل - واحصل على إجابة فورية</p>
                </div>
                <div class="dash-card card-lib" onclick="openModal('libModal')">
                    <h4>📚 مكتبة شاملة</h4>
                    <p>ملفات - ملخصات - اختبارات</p>
                </div>
            </div>

            <!-- 3D Viewport Section -->
            <div id="viewport-container">
                <div id="viewport"></div>
            </div>

        </div>
    </div>

    <!-- Bottom Navigation Bar -->
    <nav class="bottom-nav">
        <div class="nav-item active" onclick="switchNav('home')">
            <span>🏠</span>
            <span>الرئيسية</span>
        </div>
        <div class="nav-item" onclick="openModal('libModal')">
            <span>📚</span>
            <span>المكتبة</span>
        </div>
        <div class="nav-item" onclick="openModal('aiModal')">
            <span>🤖</span>
            <span>الذكاء الاصطناعي</span>
        </div>
        <div class="nav-item" onclick="openModal('devModal')">
            <span>⚙️</span>
            <span>الإعدادات</span>
        </div>
    </nav>

    <!-- Modals for Each Section -->
    
    <!-- الأحياء Modal -->
    <div id="bioModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>🌱 قسم الأحياء وعلوم الحياة</h3>
                <button class="close-btn" onclick="closeModal('bioModal')">&times;</button>
            </div>
            <div class="preview-box">
                <img src="https://images.unsplash.com/photo-1530497610245-94d3c16cda28?auto=format&fit=crop&w=600&q=80" alt="DNA">
                <div class="preview-label">صورة حقيقية لتركيب الحمض النووي (DNA) والمجهر الإلكتروني</div>
            </div>
            <div class="sub-item" onclick="loadModel('dna'); closeModal('bioModal')"><span>🧬 حلزون الحمض النووي (DNA)</span><span>عرض 3D ➔</span></div>
            <div class="sub-item" onclick="closeModal('bioModal')"><span>🦠 الخلية الحية وأجزاؤها</span><span>دروس ➔</span></div>
            <div class="sub-item" onclick="closeModal('bioModal')"><span>🩸 الجهاز الدوري والقلب</span><span>صور ➔</span></div>
            <div class="sub-item" onclick="closeModal('bioModal')"><span>🫁 الجهاز التنفسي</span><span>اختبارات ➔</span></div>
        </div>
    </div>

    <!-- الفيزياء Modal -->
    <div id="phyModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>⚡ قسم الفيزياء وميكانيكا الكم</h3>
                <button class="close-btn" onclick="closeModal('phyModal')">&times;</button>
            </div>
            <div class="preview-box">
                <img src="https://images.unsplash.com/photo-1635070041078-e363dbe005cb?auto=format&fit=crop&w=600&q=80" alt="Physics">
                <div class="preview-label">محاكاة فيزيائية حقيقية للحقول والجسيمات</div>
            </div>
            <div class="sub-item" onclick="loadModel('atom'); closeModal('phyModal')"><span>⚛️ الذرة ومستويات الطاقة</span><span>عرض 3D ➔</span></div>
            <div class="sub-item" onclick="loadModel('solar'); closeModal('phyModal')"><span>🪐 الجاذبية وحركة الكواكب</span><span>عرض 3D ➔</span></div>
            <div class="sub-item" onclick="closeModal('phyModal')"><span>🧲 الكهرباء والمغناطيسية</span><span>دروس ➔</span></div>
            <div class="sub-item" onclick="closeModal('phyModal')"><span>💡 دوائر الطاقة الحديثة</span><span>مسائل ➔</span></div>
        </div>
    </div>

    <!-- الكيمياء Modal -->
    <div id="chemModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>🧪 قسم الكيمياء والمعامل التفاعلية</h3>
                <button class="close-btn" onclick="closeModal('chemModal')">&times;</button>
            </div>
            <div class="preview-box">
                <img src="https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=600&q=80" alt="Chemistry">
                <div class="preview-label">معمل كيميائي حقيقي وتفاعلات عناصر الجدول الدوري</div>
            </div>
            <div class="sub-item" onclick="loadModel('sodium'); closeModal('chemModal')"><span>💥 تفاعل الصوديوم مع الماء (2Na + 2H₂O)</span><span>تفاعل 3D ➔</span></div>
            <div class="sub-item" onclick="loadModel('water'); closeModal('chemModal')"><span>💧 جزيء الماء التساهمي (H₂O)</span><span>عرض 3D ➔</span></div>
            <div class="sub-item" onclick="loadModel('methane'); closeModal('chemModal')"><span>🔥 احتراق الميثان (CH₄)</span><span>تفاعل ➔</span></div>
            <div class="sub-item" onclick="closeModal('chemModal')"><span>📊 موسوعة الجدول الدوري الشاملة</span><span>تصفح ➔</span></div>
        </div>
    </div>

    <!-- المعادلات Modal -->
    <div id="eqModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📊 قسم المعادلات وحل المسائل</h3>
                <button class="close-btn" onclick="closeModal('eqModal')">&times;</button>
            </div>
            <div class="sub-item" onclick="closeModal('eqModal')"><span>📈 المعادلات الخطية (Linear Equations)</span><span>حل خطوة بخطوة ➔</span></div>
            <div class="sub-item" onclick="closeModal('eqModal')"><span>📐 المعادلات التربيعية (Quadratic)</span><span>أمثلة ➔</span></div>
            <div class="sub-item" onclick="closeModal('eqModal')"><span>➗ المعادلات الكسرية</span><span>شرح ➔</span></div>
            <div class="sub-item" onclick="closeModal('eqModal')"><span>📐 المعادلات المثلثية</span><span>اختبارات ➔</span></div>
        </div>
    </div>

    <!-- معلومات Modal -->
    <div id="infoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>💡 قسم المعلومات والتقنية</h3>
                <button class="close-btn" onclick="closeModal('infoModal')">&times;</button>
            </div>
            <div class="sub-item" onclick="closeModal('infoModal')"><span>💻 أساسيات البرمجة وعلوم الحاسوب</span><span>مقال ➔</span></div>
            <div class="sub-item" onclick="closeModal('infoModal')"><span>🧠 الذكاء الاصطناعي وتطبيقاته</span><span>شرح ➔</span></div>
            <div class="sub-item" onclick="closeModal('infoModal')"><span>🌐 شبكات الإنترنت وأنظمة التشغيل</span><span>دليل ➔</span></div>
        </div>
    </div>

    <!-- تشريح Modal -->
    <div id="anatModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>❤️ قسم تشريح جسم الإنسان</h3>
                <button class="close-btn" onclick="closeModal('anatModal')">&times;</button>
            </div>
            <div class="preview-box">
                <img src="https://images.unsplash.com/photo-1559757148-5c350d0d3c56?auto=format&fit=crop&w=600&q=80" alt="Anatomy">
                <div class="preview-label">تشريح الأعضاء الحيوية ووظائفها في جسم الإنسان</div>
            </div>
            <div class="sub-item" onclick="closeModal('anatModal')"><span>🫀 الجهاز الدوري والقلب</span><span>تفاصيل ➔</span></div>
            <div class="sub-item" onclick="closeModal('anatModal')"><span>🧠 الجهاز العصبي والدماغ</span><span>تشريح ➔</span></div>
            <div class="sub-item" onclick="closeModal('anatModal')"><span>🦴 الهيكل العظمي والعضلات</span><span>أعضاء ➔</span></div>
        </div>
    </div>

    <!-- مساعد الذكاء الاصطناعي Modal -->
    <div id="aiModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>🤖 مساعد الذكاء الاصطناعي (Nova AI)</h3>
                <button class="close-btn" onclick="closeModal('aiModal')">&times;</button>
            </div>
            <div class="chat-box" id="chatBox">
                <div class="message ai">مرحباً! أنا مساعدك الذكي في NovaLab 3D. اسألني عن أي قانون فيزياء، تفاعل كيميائي، أو مسألة علمية وسأجيبك فوراً!</div>
            </div>
            <div class="chat-input">
                <input type="text" id="userInput" placeholder="اكتب سؤالك العلمي هنا..." onkeypress="handleKeyPress(event)">
                <button onclick="sendAiMessage()">إرسال</button>
            </div>
        </div>
    </div>

    <!-- المكتبة Modal -->
    <div id="libModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📚 المكتبة الشاملة والملفات</h3>
                <button class="close-btn" onclick="closeModal('libModal')">&times;</button>
            </div>
            <div class="sub-item" onclick="closeModal('libModal')"><span>📄 ملفات PDF التعليمية</span><span>تحميل ➔</span></div>
            <div class="sub-item" onclick="closeModal('libModal')"><span>📝 ملخصات الدروس والأساسيات</span><span>استعراض ➔</span></div>
            <div class="sub-item" onclick="closeModal('libModal')"><span>📋 الامتحانات السابقة ونماذج الإجابة</span><span>اختبارات ➔</span></div>
        </div>
    </div>

    <!-- الإعدادات والمطور Modal -->
    <div id="devModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>⚙️ إعدادات التطبيق ومعلومات المطور</h3>
                <button class="close-btn" onclick="closeModal('devModal')">&times;</button>
            </div>
            <div style="text-align:center; padding:15px; display:flex; flex-direction:column; gap:12px;">
                <h4 style="color:#38bdf8; font-size:1.3rem;">NOVA eHUB 26 Team</h4>
                <p style="color:#94a3b8; font-size:0.88rem;">مختبر العلوم ثلاثي الأبعاد الاحترافي المخصص لمتجر أمازون وتطبيقات Android و Fire OS.</p>
                <button onclick="window.open('https://t.me/', '_blank')" style="background:#0284c7; color:#fff; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📢 القناة الرسمية والبوت على تلجرام</button>
            </div>
        </div>
    </div>

    <script>
        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }
        function switchNav(tab) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
        }

        function sendAiMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = input.value.trim();
            if(!text) return;

            chatBox.innerHTML += `<div class="message user">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            setTimeout(() => {
                let reply = "إجابة ذكية: هذا الموضوع يعتمد على المبادئ الأساسية للعلوم التجريبية في مختبر NovaLab 3D.";
                if(text.includes('فيزياء') || text.includes('قانون')) {
                    reply = "القوانين الفيزيائية تحكم حركة الأجسام وتوزيع الطاقة في الكون وفقاً للمعادلات القياسية.";
                } else if(text.includes('كيمياء') || text.includes('تفاعل')) {
                    reply = "التفاعلات الكيميائية تتم عبر كسر الروابط وتكوين روابط جديدة باستهلاك أو انبعاث طاقة حرارية.";
                }
                chatBox.innerHTML += `<div class="message ai">${reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }, 800);
        }

        function handleKeyPress(e) { if(e.key === 'Enter') sendAiMessage(); }

        // Three.js 3D Engine Setup
        let scene, camera, renderer, controls, activeGroup;

        function init3D() {
            const container = document.getElementById('viewport');
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 0, 7);

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

            window.addEventListener('resize', onResize3D);
            loadModel('sodium');
            animate3D();
        }

        function clearScene() {
            while (activeGroup.children.length > 0) {
                const obj = activeGroup.children[0];
                if (obj.geometry) obj.geometry.dispose();
                activeGroup.remove(obj);
            }
        }

        function loadModel(type) {
            clearScene();
            if (type === 'sodium') {
                const glass = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 2.5, 32, 1, true), new THREE.MeshPhysicalMaterial({ color: 0xffffff, transparent: true, opacity: 0.3, transmission: 0.9 }));
                activeGroup.add(glass);
                const water = new THREE.Mesh(new THREE.CylinderGeometry(1.45, 1.45, 1.8, 32), new THREE.MeshStandardMaterial({ color: 0x0284c7, transparent: true, opacity: 0.7 }));
                water.position.y = -0.3;
                activeGroup.add(water);
                const sodium = new THREE.Mesh(new THREE.DodecahedronGeometry(0.3), new THREE.MeshStandardMaterial({ color: 0xf97316, emissive: 0xef4444 }));
                sodium.position.set(0, 0.4, 0);
                activeGroup.add(sodium);
            } else if (type === 'dna') {
                for (let i = -2.5; i <= 2.5; i += 0.35) {
                    const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 16), new THREE.MeshStandardMaterial({ color: 0xec4899 }));
                    s1.position.set(Math.sin(i * 1.5) * 1.3, i * 0.4, Math.cos(i * 1.5) * 1.3);
                    activeGroup.add(s1);
                    const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 16), new THREE.MeshStandardMaterial({ color: 0x38bdf8 }));
                    s2.position.set(Math.sin(i * 1.5 + Math.PI) * 1.3, i * 0.4, Math.cos(i * 1.5 + Math.PI) * 1.3);
                    activeGroup.add(s2);
                }
            } else if (type === 'atom') {
                const nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.6, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xd97706 }));
                activeGroup.add(nucleus);
                for (let i = 0; i < 3; i++) {
                    const ring = new THREE.Mesh(new THREE.TorusGeometry(1.6 + (i * 0.35), 0.02, 16, 100), new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true }));
                    ring.rotation.x = Math.PI / (i + 1); ring.rotation.y = Math.PI / (i + 2);
                    activeGroup.add(ring);
                }
            } else if (type === 'solar') {
                const sun = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 32), new THREE.MeshBasicMaterial({ color: 0xf97316 }));
                activeGroup.add(sun);
                const planet = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 32), new THREE.MeshStandardMaterial({ color: 0x06b6d4 }));
                planet.position.x = 2.5;
                activeGroup.add(planet);
            } else if (type === 'water') {
                const oxy = new THREE.Mesh(new THREE.SphereGeometry(0.9, 32, 32), new THREE.MeshStandardMaterial({ color: 0xef4444 }));
                activeGroup.add(oxy);
                const hMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc });
                const h1 = new THREE.Mesh(new THREE.SphereGeometry(0.45, 32, 32), hMat); h1.position.set(-1.2, -0.6, 0);
                const h2 = new THREE.Mesh(new THREE.SphereGeometry(0.45, 32, 32), hMat); h2.position.set(1.2, -0.6, 0);
                activeGroup.add(h1); activeGroup.add(h2);
            } else if (type === 'methane') {
                const carbon = new THREE.Mesh(new THREE.SphereGeometry(0.8, 32, 32), new THREE.MeshStandardMaterial({ color: 0x3b82f6 }));
                activeGroup.add(carbon);
                [[1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]].forEach(pos => {
                    const h = new THREE.Mesh(new THREE.SphereGeometry(0.4, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf8fafc }));
                    h.position.set(...pos); activeGroup.add(h);
                });
            }
        }

        function animate3D() {
            requestAnimationFrame(animate3D);
            if (activeGroup) activeGroup.rotation.y += 0.007;
            controls.update();
            renderer.render(scene, camera);
        }

        function onResize3D() {
            const container = document.getElementById('viewport');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }

        window.onload = init3D;
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
