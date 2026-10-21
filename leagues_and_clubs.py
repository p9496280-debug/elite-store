# leagues_and_clubs.py
# ملف قاعدة بيانات شامل لجميع الدوريات العالمية والعربية والأندية بشعاراتها الرسمية

LEAGUES_DATA = [
    {
        "id": "premier_league",
        "name": "الدوري الإنجليزي الممتاز (Premier League)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg",
        "clubs": [
            {"name": "Manchester City", "logo_url": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg"},
            {"name": "Arsenal", "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg"},
            {"name": "Liverpool", "logo_url": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg"},
            {"name": "Manchester United", "logo_url": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg"},
            {"name": "Chelsea", "logo_url": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg"},
            {"name": "Tottenham Hotspur", "logo_url": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg"},
            {"name": "Aston Villa", "logo_url": "https://upload.wikimedia.org/wikipedia/en/9/9f/Aston_Villa_logo.svg"},
            {"name": "Newcastle United", "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg"}
        ]
    },
    {
        "id": "la_liga",
        "name": "الدوري الإسباني (La Liga)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/0/0f/LaLiga_EA_Sports_2023_Logo.svg",
        "clubs": [
            {"name": "Real Madrid", "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg"},
            {"name": "FC Barcelona", "logo_url": "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg"},
            {"name": "Atletico Madrid", "logo_url": "https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_Madrid_2017_logo.svg"},
            {"name": "Girona FC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/9/90/Girona_FC.svg"},
            {"name": "Sevilla FC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/3/3b/Sevilla_FC_logo.svg"},
            {"name": "Real Betis", "logo_url": "https://upload.wikimedia.org/wikipedia/en/1/13/Real_betis_logo.svg"}
        ]
    },
    {
        "id": "serie_a",
        "name": "الدوري الإيطالي (Serie A)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/e/e9/Serie_A_logo_2022.svg",
        "clubs": [
            {"name": "Inter Milan", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg"},
            {"name": "AC Milan", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg"},
            {"name": "Juventus", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/b/bc/Juventus_FC_2017_icon_%28black%29.svg"},
            {"name": "AS Roma", "logo_url": "https://upload.wikimedia.org/wikipedia/en/f/f7/AS_Roma_logo_%282017%29.svg"},
            {"name": "SSC Napoli", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/2/28/SSC_Napoli_2020.svg"},
            {"name": "Atalanta", "logo_url": "https://upload.wikimedia.org/wikipedia/en/6/66/AtalantaBC.svg"}
        ]
    },
    {
        "id": "egyptian_league",
        "name": "الدوري المصري الممتاز (Egyptian Premier League)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/d/d9/Egyptian_Premier_League_logo.png",
        "clubs": [
            {"name": "Al Ahly SC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/8/8c/Al_Ahly_SC_logo.svg"},
            {"name": "Zamalek SC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/0/04/ZamalekSC.scarf.svg"},
            {"name": "Pyramids FC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/a2/Pyramids_FC_logo.svg"},
            {"name": "Al Masry SC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/c/c8/Al-Masry_Club_logo.png"},
            {"name": "Al Ittihad Alexandria", "logo_url": "https://upload.wikimedia.org/wikipedia/en/7/75/Al_Ittihad_Alexandria_Club_logo.png"},
            {"name": "Future FC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/5a/Modern_Future_FC_Logo.png"}
        ]
    },
    {
        "id": "saudi_pro_league",
        "name": "دوري روشن السعودي (Saudi Pro League)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/a2/Saudi_Pro_League_logo.svg",
        "clubs": [
            {"name": "Al Hilal", "logo_url": "https://upload.wikimedia.org/wikipedia/en/2/23/Al_Hilal_SFC_logo.svg"},
            {"name": "Al Nassr", "logo_url": "https://upload.wikimedia.org/wikipedia/en/c/c5/Al_Nassr_FC.svg"},
            {"name": "Al Ittihad", "logo_url": "https://upload.wikimedia.org/wikipedia/en/0/08/Al_Ittihad_Jeddah_logo.svg"},
            {"name": "Al Ahli", "logo_url": "https://upload.wikimedia.org/wikipedia/en/b/b3/Al-Ahli_Saudi_FC_logo.svg"},
            {"name": "Al Shabab", "logo_url": "https://upload.wikimedia.org/wikipedia/en/1/1a/Al-Shabab_FC_%28Riyadh%29_logo.svg"},
            {"name": "Al Ettifaq", "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/ab/Al-Ettifaq_FC_logo.svg"}
        ]
    },
    {
        "id": "ligue_1",
        "name": "الدوري الفرنسي (Ligue 1)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/d/d8/Ligue1_McDonald%27s_logo.svg",
        "clubs": [
            {"name": "Paris Saint-Germain", "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg"},
            {"name": "AS Monaco", "logo_url": "https://upload.wikimedia.org/wikipedia/en/b/ba/AS_Monaco_FC.svg"},
            {"name": "Olympique Marseille", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/d/d8/Olympique_Marseille_logo.svg"},
            {"name": "Olympique Lyonnais", "logo_url": "https://upload.wikimedia.org/wikipedia/en/c/c6/Olympique_Lyonnais_logo.svg"},
            {"name": "Lille OSC", "logo_url": "https://upload.wikimedia.org/wikipedia/en/6/6f/Lille_OSC_logo.svg"}
        ]
    },
    {
        "id": "bundesliga",
        "name": "الدوري الألماني (Bundesliga)",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/d/df/Bundesliga_logo_%282017%29.svg",
        "clubs": [
            {"name": "Bayern Munich", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg"},
            {"name": "Bayer Leverkusen", "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/59/Bayer_04_Leverkusen_logo.svg"},
            {"name": "Borussia Dortmund", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg"},
            {"name": "RB Leipzig", "logo_url": "https://upload.wikimedia.org/wikipedia/en/0/04/RB_Leipzig_2014_logo.svg"},
            {"name": "Eintracht Frankfurt", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/0/04/Eintracht_Frankfurt_Logo.svg"}
        ]
    },
    {
        "id": "efootball_teams",
        "name": "أندية وفرق eFootball الخاصة",
        "logo_url": "https://via.placeholder.com/60/00d2ff/000000?text=eFHUB",
        "clubs": [
            {"name": "eHUB All-Stars", "logo_url": "https://via.placeholder.com/60/ccff00/000000?text=eHUB"},
            {"name": "Epic Legends FC", "logo_url": "https://via.placeholder.com/60/ff0055/ffffff?text=Epic"}
        ]
    }
]


def get_all_leagues():
    """إرجاع جميع الدوريات والأندية الكاملة بشعاراتها"""
    return LEAGUES_DATA


def get_club_logo(club_name):
    """البحث المباشر عن شعار نادٍ معين بالاسم"""
    for league in LEAGUES_DATA:
        for club in league["clubs"]:
            if club["name"].lower() == club_name.lower():
                return club["logo_url"]
    return "https://via.placeholder.com/60/121826/ccff00?text=Club"
