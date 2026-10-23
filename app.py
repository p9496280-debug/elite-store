from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaLab 3D — Ultimate Science Lab & AI</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background-color: #0b0f19; color: #f1f5f9; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        
        /* Header */
        header { background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(12px); padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(56, 189, 248, 0.2); z-index: 10; }
        .logo { font-size: 1.3rem; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 10px; }
        .badge { background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; font-size: 0.75rem; padding: 4px 12px; border-radius: 20px; font-weight: 600; }

        /* Workspace */
        .workspace { display: flex; flex: 1; height: calc(100vh - 60px); position: relative; }
        
        /* Sidebar */
        sidebar { width: 290px; background: #0f172a; padding: 16px; border-left: 1px solid #1e293b; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; z-index: 5; }
        sidebar h3 { font-size: 0.8rem; text-transform: uppercase; color: #64748b; margin-top: 6px; letter-spacing: 1px; }
        
        .nav-btn { background: #1e293b; color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px 14px; text-align: right; border-radius: 10px; cursor: pointer; font-size: 0.9rem; font-weight: 600; transition: all 0.25s ease; display: flex; align-items: center; gap: 10px; }
        .nav-btn:hover { background: #334155; color: #fff; transform: translateX(-3px); }
        .nav-btn.active { background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; border-color: #38bdf8; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3); }
        .ai-btn { background: linear-gradient(135deg, #7c3aed, #4f46e5); color: #fff; border: none; }
        .ai-btn:hover { background: linear-gradient(135deg, #8b5cf6, #6366f1); }
        .dev-btn { background: #1e293b; color: #38bdf8; border: 1px dashed #38bdf8; }

        /* Viewport */
        main { flex: 1; position: relative; background: radial-gradient(circle at center, #1e293b 0%, #020617 100%); }
        #viewport { width: 100%; height: 100%; }

        /* Info Card */
        .info-card { position: absolute; top: 20px; right: 20px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(56, 189, 248, 0.3); padding: 18px 22px; border-radius: 14px; max-width: 340px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); pointer-events: none; }
        .info-card h2 { font-size: 1.15rem; color: #38bdf8; margin-bottom: 6px; }
        .info-card p { font-size: 0.88rem; line-height: 1.5; color: #94a3b8; }

        /* Modals (AI, Articles, Dev) */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #1e293b; border: 1px solid #38bdf8; width: 90%; max-width: 600px; border-radius: 16px; padding: 24px; display: flex; flex-direction: column; gap: 15px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); max-height: 80vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .modal-header h3 { color: #38bdf8; font-size: 1.2rem; }
        .close-btn { background: none; border: none; color: #94a3b8; font-size: 1.5rem; cursor: pointer; }
        
        /* AI Chat Box Styles */
        .chat-box { display: flex; flex-direction: column; gap: 10px; height: 300px; overflow-y: auto; padding: 10px; background: #0f172a; border-radius: 10px; border: 1px solid #334155; }
        .message { padding: 10px 14px; border-radius: 10px; max-width: 80%; font-size: 0.9rem; line-height: 1.4; }
        .message.ai { background: #334155; color: #f8fafc; align-self: flex-start; }
        .message.user { background: #0284c7; color: #fff; align-self: flex-end; }
        .chat-input-area { display: flex; gap: 10px; }
        .chat-input-area input { flex: 1; background: #0f172a; border: 1px solid #334155; padding: 10px 14px; border-radius: 8px; color: #fff; outline: none; }
        .chat-input-area button { background: #0284c7; color: #fff; border: none; padding: 0 20px; border-radius: 8px; font-weight: bold; cursor: pointer; }

        /* Articles list */
        .article-item { background: #0f172a; padding: 14px; border-radius: 10px; border-left: 4px solid #38bdf8; margin-bottom: 10px; }
        .article-item h4 { color: #38bdf8; margin-bottom: 5px; }
        .article-item p { color: #94a3b8; font-size: 0.85srem; }

        @media (max-width: 768px) {
            .workspace { flex-direction: column-reverse; }
            sidebar { width: 100%; height: 170px; }
            .info-card { top: 10px; right: 10px; left: 10px; max-width: none; }
        }
    </style>
</head>
<body>

    <header>
        <div class="logo"><span>🔬 NovaLab 3D</span></div>
        <div class="badge">Amazon Developer Edition</div>
    </header>

    <div class="workspace">
        <!-- القائمة الجانبية المحدثة بالكامل -->
        <sidebar>
            <h3>المختبر الثلاثي</h3>
            <button class="nav-btn active" onclick="switchExperiment('water', this)">🧪 جزيء الماء H₂O</button>
            <button class="nav-btn" onclick="switchExperiment('methane', this)">🔥 جزيء الميثان CH₄</button>
            <button class="nav-btn" onclick="switchExperiment('atom', this)">⚡ نموذج الذرة والمدارات</button>
            <button class="nav-btn" onclick="switchExperiment('solar', this)">🪐 الجاذبية والفلك</button>

            <h3>المميزات والذكاء الاصطناعي</h3>
            <button class="nav-btn ai-btn" onclick="openModal('aiModal')">🤖 مساعد الذكاء الاصطناعي</button>
            <button class="nav-btn" onclick="openModal('articlesModal')">📚 المقالات العلمية</button>

            <h3>الروابط والمجتمع</h3>
            <button class="nav-btn" onclick="window.open('https://t.me/', '_blank')">📢 القناة الرسمية والبوت</button>
            <button class="nav-btn dev-btn" onclick="openModal('devModal')">👨‍💻 زر المطور</button>
        </sidebar>

        <main>
            <div id="viewport"></div>
            
            <div class="info-card">
                <h2 id="title">جزيء الماء (H₂O)</h2>
                <p id="description">نموذج ثلاثي الأبعاد تفاعلي يوضح الرابطة التساهمية بين ذرة الأكسجين والهنيدروجين.</p>
            </div>
        </main>
    </div>

    <!-- نافذة الذكاء الاصطناعي (AI Modal) -->
    <div id="aiModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>🤖 مساعد العلوم والذكاء الاصطناعي</h3>
                <button class="close-btn" onclick="closeModal('aiModal')">&times;</button>
            </div>
            <p style="color: #94a3b8; font-size: 0.85rem;">اسأل المساعد الذكي عن أي تجربة فيزياء أو كيمياء أو تفاعل جزيئي داخل المختبر!</p>
            <div class="chat-box" id="chatBox">
                <div class="message ai">أهلاً بك! أنا مساعدك الذكي في NovaLab 3D. كيف يمكنني مساعدتك علمياً اليوم؟</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="اكتب سؤالك العلمي هنا..." onkeypress="handleKeyPress(event)">
                <button onclick="sendAiMessage()">إرسال</button>
            </div>
        </div>
    </div>

    <!-- نافذة المقالات العلمية (Articles Modal) -->
    <div id="articlesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📚 مقالات وروابط علمية متقدمة</h3>
                <button class="close-btn" onclick="closeModal('articlesModal')">&times;</button>
            </div>
            <div class="article-item">
                <h4>1. الرابطة التساهمية ودورها في تكوين الجزيئات</h4>
                <p>كيف تتشارك الذرات الإلكترونات للوصول إلى حالة الاستقرار الطاقي وكيف نراها في نماذج 3D.</p>
            </div>
            <div class="article-item">
                <h4>2. ميكانيكا الكم وتوزيع الإلكترونات في المدارات</h4>
                <p>شرح مبسط لكيفية دوران الإلكترونات حول النواة ومستويات الطاقة المختلفة.</p>
            </div>
            <div class="article-item">
                <h4>3. الجاذبية الفضائية وقوانين الكبلر</h4>
                <p>تفسير حركة الكواكب والأجرام السماوية في الفضاء المفتوح والمدارات الافتراضية.</p>
            </div>
        </div>
    </div>

    <!-- نافذة المطور (Developer Modal) -->
    <div id="devModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>👨‍💻 معلومات المطور</h3>
                <button class="close-btn" onclick="closeModal('devModal')">&times;</button>
            </div>
            <div style="text-align: center; padding: 20px; display: flex; flex-direction: column; gap: 10px;">
                <h4 style="color: #38bdf8; font-size: 1.2rem;">NOVA eHUB 26 Team</h4>
                <p style="color: #94a3b8;">تطبيق مختبر العلوم ثلاثي الأبعاد المخصص لمتجر أمازون ومنافسات الهاكاثون.</p>
                <p style="color: #cbd5e1; font-weight: bold; margin-top: 10px;">✨ البرمجيات المستخدمة: Flask, Three.js, WebGL, Python</p>
            </div>
        </div>
    </div>

    <script>
        // التحكم في النوافذ المنتقلة (Modals)
        function openModal(modalId) {
            document.getElementById(modalId).style.display = 'flex';
        }
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        // محاكاة نظام الذكاء الاصطناعي التفاعلي
        function sendAiMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = input.value.trim();
            if(!text) return;

            // إضافة رسالة المستخدم
            chatBox.innerHTML += `<div class="message user">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            // الرد الذكي التلقائي
            setTimeout(() => {
                let reply = "سؤال ممتاز! في مختبر NovaLab 3D، نتيح لك استكشاف هذه الظاهرة بصرياً عبر تحريك النموذج ثلاثي الأبعاد.";
                if(text.includes('ماء') || text.includes('H2O')) {
                    reply = "جزيء الماء يتكون من ذرة أكسجين مركزية وذرتي هيدروجين بزاوية تقارب 104.5 درجة لضمان الاستقرار الكيميائي.";
                } else if(text.includes('ذرة') || text.includes('إلكترون')) {
                    reply = "الذرة تحتوي على نواة كثيفة موجبة الشحنة وإلكترونات تدور بسرعة هائلة في مدارات طاقة محددة.";
                }
                chatBox.innerHTML += `<div class="message ai">${reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }, 800);
        }

        function handleKeyPress(e) {
            if(e.key === 'Enter') sendAiMessage();
        }

        // محرك Three.js ثلاثي الأبعاد
        let scene, camera, renderer, controls, activeGroup;
        function init() {
            const container = document.getElementById('viewport');
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 0, 8);
            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            scene.add(new THREE.AmbientLight(0xffffff, 0.8));
            const dirLight = new THREE.DirectionalLight(0x38bdf8, 1);
            dirLight.position.set(5, 10, 7);
            scene.add(dirLight);
            activeGroup = new THREE.Group();
            scene.add(activeGroup);
            window.addEventListener('resize', onResize);
            buildWaterMolecule();
            animate();
        }

        function clearScene() {
            while (activeGroup.children.length > 0) {
                const obj = activeGroup.children[0];
                if (obj.geometry) obj.geometry.dispose();
                activeGroup.remove(obj);
            }
        }

        function switchExperiment(type, element) {
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            if (element) element.classList.add('active');
            clearScene();
            if (type === 'water') {
                document.getElementById('title').innerText = "جزيء الماء (H₂O)";
                document.getElementById('description').innerText = "نموذج ثلاثي الأبعاد تفاعلي يوضح الرابطة التساهمية بين ذرة الأكسجين (أحمر) وذرتي الهيدروجين (أبيض).";
                buildWaterMolecule();
            } else if (type === 'methane') {
                document.getElementById('title').innerText = "جزيء الميثان (CH₄)";
                document.getElementById('description').innerText = "تمثيل جزيئي ثلاثي الأبعاد لمركب الميثان العضوي: ذرة كربون مرتبطة بأربع ذرات هيدروجين.";
                buildMethaneMolecule();
            } else if (type === 'atom') {
                document.getElementById('title').innerText = "نموذج الذرة والتأين";
                document.getElementById('description').innerText = "محاكاة ثلاثية الأبعاد لنواة الذرة ومدارات الإلكترونات السريعة التي تدور حولها في مجالات الطاقة.";
                buildAtomModel();
            } else if (type === 'solar') {
                document.getElementById('title').innerText = "الجاذبية وحركة الأجرام";
                document.getElementById('description').innerText = "نموذج فيزيائي يوضح مدار الجاذبية الدائرية للكواكب حول مركز الكتلة في الفضاء.";
                buildSolarSystem();
            }
        }

        function buildWaterMolecule() {
            const oxy = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 32), new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.3 }));
            activeGroup.add(oxy);
            const hMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 });
            const h1 = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), hMat); h1.position.set(-1.3, -0.7, 0);
            const h2 = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), hMat); h2.position.set(1.3, -0.7, 0);
            activeGroup.add(h1); activeGroup.add(h2);
        }

        function buildMethaneMolecule() {
            const carbon = new THREE.Mesh(new THREE.SphereGeometry(0.9, 32, 32), new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.3 }));
            activeGroup.add(carbon);
            [[1.1, 1.1, 1.1], [-1.1, -1.1, 1.1], [-1.1, 1.1, -1.1], [1.1, -1.1, -1.1]].forEach(pos => {
                const h = new THREE.Mesh(new THREE.SphereGeometry(0.45, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf8fafc }));
                h.position.set(...pos); activeGroup.add(h);
            });
        }

        function buildAtomModel() {
            const nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xd97706, emissiveIntensity: 0.5 }));
            activeGroup.add(nucleus);
            for (let i = 0; i < 3; i++) {
                const ring = new THREE.Mesh(new THREE.TorusGeometry(1.8 + (i * 0.4), 0.02, 16, 100), new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true }));
                ring.rotation.x = Math.PI / (i + 1); ring.rotation.y = Math.PI / (i + 2);
                activeGroup.add(ring);
            }
        }

        function buildSolarSystem() {
            const center = new THREE.Mesh(new THREE.SphereGeometry(1.1, 32, 32), new THREE.MeshBasicMaterial({ color: 0xf97316 }));
            activeGroup.add(center);
            const orbiter = new THREE.Mesh(new THREE.SphereGeometry(0.4, 32, 32), new THREE.MeshStandardMaterial({ color: 0x06b6d4 }));
            orbiter.position.x = 2.8; activeGroup.add(orbiter);
        }

        function animate() {
            requestAnimationFrame(animate);
            if (activeGroup) activeGroup.rotation.y += 0.008;
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
