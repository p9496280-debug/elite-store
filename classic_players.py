# classic_players.py
# ملف خاص بقاعدة بيانات الكروت القديمة وأساطير بيس التاريخية

import json

def get_classic_players():
    # قائمة الكروت القديمة والأساطير التاريخية لبيس
    classic_list = [
        {
            "id": 101,
            "name": "Diego Maradona",
            "overall_base": 97,
            "overall_max": 109,
            "position": "AMF",
            "team": "Barcelona / Legend",
            "card_type": "Classic Epic / Icon",
            "is_upcoming": 0,
            "image_url": "https://via.placeholder.com/150/121826/ccff00?text=Maradona",
            "stats_json": json.dumps({
                "attacking": {"وعي هجومي": 98, "التحكم في الكرة": 99, "المراوغة": 99, "إنهاء الهجمة": 95},
                "physical": {"السرعة": 90, "التسارع": 96},
                "defending": {"وعي دفاعي": 35}
            }),
            "skills_json": json.dumps(["المراوغة الأسطورية", "تمرير قاتل", "دقة التسديد"])
        },
        {
            "id": 102,
            "name": "Johan Cruyff",
            "overall_base": 96,
            "overall_max": 108,
            "position": "SS",
            "team": "Barcelona / Icon",
            "card_type": "Classic Epic / Icon",
            "is_upcoming": 0,
            "image_url": "https://via.placeholder.com/150/121826/ccff00?text=Cruyff",
            "stats_json": json.dumps({
                "attacking": {"وعي هجومي": 97, "التحكم في الكرة": 97, "المراوغة": 96, "إنهاء الهجمة": 94},
                "physical": {"السرعة": 91, "التسارع": 93},
                "defending": {"وعي دفاعي": 40}
            }),
            "skills_json": json.dumps(["التحكم بالكرة", "تمرير ذكي"])
        },
        {
            "id": 103,
            "name": "Paolo Maldini",
            "overall_base": 95,
            "overall_max": 107,
            "position": "CB",
            "team": "AC Milan / Legend",
            "card_type": "Classic Epic / Icon",
            "is_upcoming": 0,
            "image_url": "https://via.placeholder.com/150/121826/ccff00?text=Maldini",
            "stats_json": json.dumps({
                "attacking": {"وعي هجومي": 60, "التحكم في الكرة": 75},
                "physical": {"السرعة": 89, "التسارع": 88, "القفز": 92},
                "defending": {"وعي دفاعي": 99, "احتكاك دفاعي": 98, "قطع الكرة": 99}
            }),
            "skills_json": json.dumps(["اعتراض ممتاز", "قيادة خط الدفاع"])
        }
    ]
    return classic_list
