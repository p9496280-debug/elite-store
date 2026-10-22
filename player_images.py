# player_images.py
# مكتبة كاملة ومنفصلة لصور جميع اللاعبين والأساطير في تطبيق NOVA eHUB 26

PLAYER_IMAGES_DATABASE = {
    # الأساطير والبطاقات الكلاسيكية
    "Lionel Messi": "https://via.placeholder.com/150/121826/ccff00?text=Messi",
    "Cristiano Ronaldo": "https://via.placeholder.com/150/121826/ccff00?text=Ronaldo",
    "Neymar Jr": "https://via.placeholder.com/150/121826/ccff00?text=Neymar",
    "Raphael Varane": "https://via.placeholder.com/150/121826/ccff00?text=Varane",
    "Seedorf": "https://via.placeholder.com/150/121826/ccff00?text=Seedorf",
    "Diego Maradona": "https://via.placeholder.com/150/121826/ccff00?text=Maradona",
    "Pelé": "https://via.placeholder.com/150/121826/ccff00?text=Pele",
    "Ronaldinho": "https://via.placeholder.com/150/121826/ccff00?text=Ronaldinho",
    "Zinedine Zidane": "https://via.placeholder.com/150/121826/ccff00?text=Zidane",
    "Ronaldo Nazario": "https://via.placeholder.com/150/121826/ccff00?text=R9",
    "Thierry Henry": "https://via.placeholder.com/150/121826/ccff00?text=Henry",
    "Paolo Maldini": "https://via.placeholder.com/150/121826/ccff00?text=Maldini",
    "Roberto Carlos": "https://via.placeholder.com/150/121826/ccff00?text=R.+Carlos",
    "Kaka": "https://via.placeholder.com/150/121826/ccff00?text=Kaka",
    "Steven Gerrard": "https://via.placeholder.com/150/121826/ccff00?text=Gerrard",
    "Frank Lampard": "https://via.placeholder.com/150/121826/ccff00?text=Lampard",
    "David Beckham": "https://via.placeholder.com/150/121826/ccff00?text=Beckham",
    "Patrick Vieira": "https://via.placeholder.com/150/121826/ccff00?text=Vieira",
    "Oliver Kahn": "https://via.placeholder.com/150/121826/ccff00?text=Kahn",
    "Iker Casillas": "https://via.placeholder.com/150/121826/ccff00?text=Casillas",

    # نجوم كرة القدم المحدثين
    "Kylian Mbappé": "https://via.placeholder.com/150/121826/ccff00?text=Mbappe",
    "Erling Haaland": "https://via.placeholder.com/150/121826/ccff00?text=Haaland",
    "Jude Bellingham": "https://via.placeholder.com/150/121826/ccff00?text=Bellingham",
    "Vinicius Jr": "https://via.placeholder.com/150/121826/ccff00?text=Vinicius",
    "Mohamed Salah": "https://via.placeholder.com/150/121826/ccff00?text=Salah",
    "Kevin De Bruyne": "https://via.placeholder.com/150/121826/ccff00?text=De+Bruyne",
    "Luka Modric": "https://via.placeholder.com/150/121826/ccff00?text=Modric",
    "Robert Lewandowski": "https://via.placeholder.com/150/121826/ccff00?text=Lewandowski",
    "Harry Kane": "https://via.placeholder.com/150/121826/ccff00?text=Kane",
    "Virgil van Dijk": "https://via.placeholder.com/150/121826/ccff00?text=Van+Dijk",
}

DEFAULT_PLAYER_IMAGE = "https://via.placeholder.com/150/121826/ccff00?text=eFootball"


def get_player_image(player_name: str) -> str:
    """
    دالة للحصول على رابط صورة اللاعب بناءً على اسمه.
    في حال عدم وجود صورة مخصصة للاعب يتم إرجاع الصورة الافتراضية.
    """
    return PLAYER_IMAGES_DATABASE.get(player_name, DEFAULT_PLAYER_IMAGE)


def get_all_player_images() -> dict:
    """
    دالة لاسترجاع قاموس جميع الصور المسجلة.
    """
    return PLAYER_IMAGES_DATABASE
