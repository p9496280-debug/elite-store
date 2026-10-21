# player_stats.py
# ملف تصميم واجهة إحصائيات اللاعب التفصيلية والمطابقة لـ eFHUB

PLAYER_STATS_TEMPLATE = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ player['name'] }} | إحصائيات البرنامج الشاملة</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
:root { --bg-dark: #07090e; --panel-bg: #0e121d; --neon-green: #ccff00; --neon-blue: #00d2ff; --border-color: #1e2638; }
body { background-color: var(--bg-dark); color: #fff; font-family: 'Cairo', sans-serif; padding: 15px; margin: 0; }
.header-title { text-align: center; font-weight: 900; font-size: 20px; color: #fff; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; gap: 8px; }
.header-title span { color: var(--neon-blue); }

.efhub-dashboard { max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: 280px 1fr 1fr; gap: 15px; }
@media(max-width: 900px) { .efhub-dashboard { grid-template-columns: 1fr; } }

.box-card { background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 16px; padding: 15px; margin-bottom: 15px; }
.section-title { font-size: 13px; font-weight: 900; color: #fff; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 6px; }

.overall-circle { width: 110px; height: 110px; border: 4px solid var(--neon-blue); border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 auto 15px; box-shadow: 0 0 20px rgba(0,210,255,0.2); }
.overall-num { font-size: 32px; font-weight: 900; color: #fff; line-height: 1; }
.overall-label { font-size: 11px; color: #94a3b8; margin-top: 4px; }

.info-row { display: flex; justify-content: space-between; align-items: center; background: #141a29; padding: 8px 12px; border-radius: 10px; margin-bottom: 8px; font-size: 12px; }
.st-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid #141a29; font-size: 12px; }
.st-badge { padding: 2px 8px; border-radius: 6px; font-weight: 900; font-size: 12px; min-width: 32px; text-align: center; color: #000; }
.bg-green { background: #10b981; color: #fff; }
.bg-yellow { background: #eab308; color: #000; }
.bg-red { background: #ef4444; color: #fff; }
.bg-blue { background: #3b82f6; color: #fff; }

.skills-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.skill-box { background: #141a29; border: 1px solid var(--border-color); border-radius: 10px; padding: 8px; text-align: center; }
.skill-val { font-size: 15px; font-weight: 900; color: var(--neon-green); margin-top: 2px; }

.progress-bar-container { background: #141a29; border-radius: 6px; height: 8px; width: 100%; margin-top: 4px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #ccff00); border-radius: 6px; }

.back-btn { display: block; text-align: center; margin: 20px auto; max-width: 300px; padding: 12px; background: var(--neon-green); color: #000; font-weight: 900; border-radius: 12px; text-decoration: none; }
</style>
</head>
<body>

<div class="header-title">
  📊 إحصائيات البرنامج <span>الشاملة</span>
  <div style="font-size:11px; color:#94a3b8; font-weight:normal;">تفاصيل شاملة لأداء {{ player['name'] }}</div>
</div>

<div class="efhub-dashboard">
  <!-- العمود الأيمن: التقييم العام والمعلومات البدنية -->
  <div>
    <div class="box-card" style="text-align:center;">
      <div class="overall-circle">
        <div class="overall-num">{{ player['overall_max'] }}</div>
        <div class="overall-label">التقييم العام</div>
      </div>
      <div class="info-row"><span>الطول</span><b>183 سم</b></div>
      <div class="info-row"><span>الوزن</span><b>76 كجم</b></div>
      <div class="info-row"><span>العمر</span><b>25 سنة</b></div>
      <div style="margin-top:12px; text-align:right;">
        <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">مستوى اللياقة (70%)</div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width:70%;"></div></div>
      </div>
    </div>

    <div class="box-card">
      <div class="section-title"><span>⭐ المهارات الأساسية</span></div>
      <div class="skills-grid">
        <div class="skill-box"><div style="font-size:10px; color:#94a3b8;">تحكم بالكرة</div><div class="skill-val">87</div></div>
        <div class="skill-box"><div style="font-size:10px; color:#94a3b8;">مراوغة</div><div class="skill-val">86</div></div>
        <div class="skill-box"><div style="font-size:10px; color:#94a3b8;">التسديد</div><div class="skill-val">82</div></div>
        <div class="skill-box"><div style="font-size:10px; color:#94a3b8;">التمرير</div><div class="skill-val">84</div></div>
        <div class="skill-box"><div style="font-size:10px; color:#94a3b8;">السرعة</div><div class="skill-val">82</div></div>
        <div class="skill-box"><div style="font-size:10px; color:#94a3b8;">القدرة البدنية</div><div class="skill-val">82</div></div>
      </div>
    </div>
  </div>

  <!-- العمود الأوسط: القدرات الهجومية والدفاعية والبدنية -->
  <div>
    <div class="box-card">
      <div class="section-title"><span style="color:var(--neon-green);">⚽ القدرات الأساسية (الهجوم)</span></div>
      <div class="st-row"><span>الوعي الهجومي</span><span class="st-badge bg-green">89</span></div>
      <div class="st-row"><span>التحكم في الكرة</span><span class="st-badge bg-green">86</span></div>
      <div class="st-row"><span>التمريرات القصيرة</span><span class="st-badge bg-yellow">72</span></div>
      <div class="st-row"><span>التمريرات المتوسطة</span><span class="st-badge bg-yellow">72</span></div>
      <div class="st-row"><span>إنهاء الهجمة</span><span class="st-badge bg-red">50</span></div>
      <div class="st-row"><span>مهارة الرأس</span><span class="st-badge bg-green">79</span></div>
    </div>

    <div class="box-card">
      <div class="section-title"><span style="color:var(--neon-blue);">🛡️ القدرات الدفاعية</span></div>
      <div class="st-row"><span>وعي دفاعي</span><span class="st-badge bg-green">88</span></div>
      <div class="st-row"><span>الافتكاكات</span><span class="st-badge bg-green">88</span></div>
      <div class="st-row"><span>قطع الكرة</span><span class="st-badge bg-green">87</span></div>
      <div class="st-row"><span>الالتفهام</span><span class="st-badge bg-green">84</span></div>
    </div>
  </div>

  <!-- العمود الأيسر: الإحصائيات العامة ومعلومات إضافية -->
  <div>
    <div class="box-card">
      <div class="section-title"><span>📊 الإحصائيات العامة</span></div>
      <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">التسديد (187.8)</div>
      <div class="progress-bar-container" style="margin-bottom:10px;"><div class="progress-bar-fill" style="width:85%;"></div></div>
      <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">التمرير (173.8)</div>
      <div class="progress-bar-container" style="margin-bottom:10px;"><div class="progress-bar-fill" style="width:75%;"></div></div>
      <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">المراوغة (272.4)</div>
      <div class="progress-bar-container" style="margin-bottom:10px;"><div class="progress-bar-fill" style="width:95%;"></div></div>
      <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">التحكم في الكرة (197)</div>
      <div class="progress-bar-container"><div class="progress-bar-fill" style="width:80%;"></div></div>
    </div>

    <div class="box-card">
      <div class="section-title"><span>ℹ️ معلومات إضافية</span></div>
      <div class="info-row"><span>المنصب المفضل</span><b>{{ player['position'] }}</b></div>
      <div class="info-row"><span>نوع القدم</span><b>القدم اليمني</b></div>
      <div class="info-row"><span>النادي</span><b style="color:var(--neon-green);">{{ player['team'] }}</b></div>
      <div class="info-row"><span>نوع البطاقة</span><b style="color:var(--neon-blue);">{{ player['card_type'] }}</b></div>
    </div>
  </div>
</div>

<a href="/" class="back-btn">← العودة للصفحة الرئيسية</a>

</body>
</html>
"""
