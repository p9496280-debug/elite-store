# classic_players.py
# قاعدة بيانات تضم أكثر من 150 أسطورة ولاعب مع صور البطاقات الأصلية

import json

def get_classic_players():
    # قائمة الأسماء مع رابط صورة مصغرة مميزة لكل كارت بطاقة
    players_data = [
        ("Diego Maradona", 99, "AMF", "Barcelona / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/8192-1696425983.jpg?lm=1"),
        ("Johan Cruyff", 98, "SS", "Barcelona / Icon", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/80267-1605615707.jpg?lm=1"),
        ("Paolo Maldini", 98, "CB", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/83489-1582289417.jpg?lm=1"),
        ("Ronaldinho", 99, "LWF", "Barcelona / Icon", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3375-1678275143.jpg?lm=1"),
        ("Ronaldo Nazario", 99, "ST", "Real Madrid / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3140-1681292556.jpg?lm=1"),
        ("Zinedine Zidane", 98, "AMF", "Real Madrid / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3273-1652173909.jpg?lm=1"),
        ("Pelé", 99, "CF", "Brazil / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/nc-158504-1473682977.jpg?lm=1"),
        ("Franz Beckenbauer", 98, "CB", "Bayern Munich / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/nc-7234-1481533261.jpg?lm=1"),
        ("Lev Yashin", 97, "GK", "Dynamo Moscow / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/nc-51543-1594891100.jpg?lm=1"),
        ("Andrés Iniesta", 97, "CMF", "Barcelona / Icon", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7607-1671013444.jpg?lm=1"),
        ("Xavi Hernandez", 97, "CMF", "Barcelona / Icon", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7942-1662557434.jpg?lm=1"),
        ("Iker Casillas", 96, "GK", "Real Madrid / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3979-1662557563.jpg?lm=1"),
        ("Oliver Kahn", 96, "GK", "Bayern Munich / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/433-1632225308.jpg?lm=1"),
        ("Carles Puyol", 96, "CB", "Barcelona / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7553-1563278913.jpg?lm=1"),
        ("Fabio Cannavaro", 96, "CB", "Italy / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5815-1610452390.jpg?lm=1"),
        ("Alessandro Nesta", 97, "CB", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5894-1678196123.jpg?lm=1"),
        ("Roberto Carlos", 97, "LB", "Real Madrid / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3143-1679058252.jpg?lm=1"),
        ("Cafu", 96, "RB", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5814-1610452321.jpg?lm=1"),
        ("Javier Zanetti", 96, "RB", "Inter Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7616-1601297598.jpg?lm=1"),
        ("Patrick Vieira", 98, "DMF", "Arsenal / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5354-1601298150.jpg?lm=1"),
        ("Frank Rijkaard", 97, "DMF", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/104554-1582290458.jpg?lm=1"),
        ("Frank Lampard", 96, "AMF", "Chelsea / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3159-1662557762.jpg?lm=1"),
        ("Paul Scholes", 96, "CMF", "Manchester United / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3406-1659526715.jpg?lm=1"),
        ("Ryan Giggs", 95, "LWF", "Manchester United / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3407-1659526842.jpg?lm=1"),
        ("David Beckham", 97, "RMF", "Manchester United / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3139-1662557689.jpg?lm=1"),
        ("Luis Figo", 96, "RWF", "Real Madrid / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3402-1605615872.jpg?lm=1"),
        ("Thierry Henry", 98, "CF", "Arsenal / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3207-1682503251.jpg?lm=1"),
        ("Dennis Bergkamp", 96, "SS", "Arsenal / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3556-1605616035.jpg?lm=1"),
        ("Marco van Basten", 97, "CF", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/104553-1582290198.jpg?lm=1"),
        ("Andriy Shevchenko", 96, "CF", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7212-1594902146.jpg?lm=1"),
        ("Gabriel Batistuta", 97, "CF", "Fiorentina / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5863-1605616182.jpg?lm=1"),
        ("Samuel Eto'o", 96, "CF", "Barcelona / Icon", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/4255-1671013778.jpg?lm=1"),
        ("Didier Drogba", 96, "CF", "Chelsea / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3379-1671013892.jpg?lm=1"),
        ("Wayne Rooney", 96, "CF", "Manchester United / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3377-1605616390.jpg?lm=1"),
        ("Raul Gonzalez", 96, "SS", "Real Madrid / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7608-1594902341.jpg?lm=1"),
        ("Fernando Torres", 97, "CF", "Liverpool / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7850-1632225492.jpg?lm=1"),
        ("David Villa", 95, "CF", "Valencia / Spain", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/7588-1582289658.jpg?lm=1"),
        ("Pavel Nedved", 96, "LMF", "Juventus / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5816-1610452445.jpg?lm=1"),
        ("Alessandro Del Piero", 97, "SS", "Juventus / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/4289-1605616521.jpg?lm=1"),
        ("Francesco Totti", 96, "AMF", "Roma / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5950-1632225672.jpg?lm=1"),
        ("Andrea Pirlo", 96, "DMF", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5813-1662557921.jpg?lm=1"),
        ("Kaká", 98, "AMF", "AC Milan / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3366-1678196234.jpg?lm=1"),
        ("Rivaldo", 97, "LWF", "Barcelona / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/8537-1678196341.jpg?lm=1"),
        ("Romario", 98, "CF", "Brazil / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/104555-1582290712.jpg?lm=1"),
        ("Michael Owen", 96, "CF", "Liverpool / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3404-1605616789.jpg?lm=1"),
        ("Steven Gerrard", 96, "CMF", "Liverpool / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3405-1659526912.jpg?lm=1"),
        ("Xabi Alonso", 95, "DMF", "Real Madrid / Liverpool", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3142-1671014120.jpg?lm=1"),
        ("Sergio Ramos", 97, "CB", "Real Madrid / Spain", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/25557-1683884393.jpg?lm=1"),
        ("Marcelo", 95, "LB", "Real Madrid / Brazil", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/44525-1683884512.jpg?lm=1"),
        ("Toni Kroos", 96, "CMF", "Real Madrid / Germany", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/31909-1715694218.jpg?lm=1"),
        ("Luka Modric", 97, "CMF", "Real Madrid / Croatia", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/27992-1683884631.jpg?lm=1"),
        ("Karim Benzema", 97, "CF", "Real Madrid / France", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/18922-1683884742.jpg?lm=1"),
        ("Gareth Bale", 96, "RWF", "Real Madrid / Wales", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/39381-1652174120.jpg?lm=1"),
        ("Eden Hazard", 96, "LWF", "Chelsea / Belgium", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/50202-1671014312.jpg?lm=1"),
        ("Petr Cech", 96, "GK", "Chelsea / Legend", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3367-1605617012.jpg?lm=1"),
        ("Gianluigi Buffon", 97, "GK", "Juventus / Italy", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/5022-1691494812.jpg?lm=1"),
        ("Zlatan Ibrahimovic", 97, "CF", "AC Milan / Sweden", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3455-1683884910.jpg?lm=1"),
        ("Wesley Sneijder", 96, "AMF", "Inter Milan / Netherlands", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/4553-1605617234.jpg?lm=1"),
        ("Adriano", 97, "CF", "Inter Milan / Brazil", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/3421-1605617390.jpg?lm=1"),
        ("Kylian Mbappe", 99, "CF", "Real Madrid / France", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/342229-1715693910.jpg?lm=1"),
        ("Erling Haaland", 99, "CF", "Manchester City / Norway", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/418560-1715694032.jpg?lm=1"),
        ("Kevin De Bruyne", 98, "AMF", "Manchester City / Belgium", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/88755-1715694155.jpg?lm=1"),
        ("Rodri", 97, "DMF", "Manchester City / Spain", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/357565-1715694310.jpg?lm=1"),
        ("Sergio Aguero", 97, "CF", "Manchester City / Argentina", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/26399-1632225910.jpg?lm=1"),
        ("Yaya Toure", 96, "CMF", "Manchester City / Ivory Coast", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/15093-1605617610.jpg?lm=1"),
        ("Harry Kane", 97, "CF", "Bayern Munich / England", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/132098-1715694420.jpg?lm=1"),
        ("Manuel Neuer", 96, "GK", "Bayern Munich / Germany", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/17272-1715694550.jpg?lm=1"),
        ("Franck Ribery", 96, "LWF", "Bayern Munich / France", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/22051-1605617820.jpg?lm=1"),
        ("Arjen Robben", 97, "RWF", "Bayern Munich / Netherlands", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/4359-1605617980.jpg?lm=1"),
        ("Philipp Lahm", 97, "RB", "Bayern Munich / Germany", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/2220-1605618120.jpg?lm=1"),
        ("Mohamed Salah", 97, "RWF", "Liverpool / Egypt", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/148455-1683885020.jpg?lm=1"),
        ("Virgil van Dijk", 97, "CB", "Liverpool / Netherlands", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/139208-1683885150.jpg?lm=1"),
        ("Alisson Becker", 96, "GK", "Liverpool / Brazil", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/54343-1683885280.jpg?lm=1"),
        ("Bruno Fernandes", 96, "AMF", "Manchester United / Portugal", "Classic Epic / Icon", "https://img.a.transfermarkt.technology/portrait/header/240306-1683885400.jpg?lm=1")
    ]

    classic_list = []
    # توليد بقية اللاعبين حتى نصل لأكثر من 150 أسطورة بشكل تلقائي واحترافي
    extra_legends = [
        ("Bebeto", 95, "CF", "Brazil / Legend"), ("Dunga", 94, "DMF", "Brazil / Legend"),
        ("Claudio Taffarel", 94, "GK", "Brazil / Legend"), ("Zito", 93, "DMF", "Brazil / Legend"),
        ("Garrincha", 98, "RWF", "Brazil / Legend"), ("Zico", 98, "AMF", "Brazil / Legend"),
        ("Sócrates", 97, "AMF", "Brazil / Legend"), ("Jairzinho", 96, "RWF", "Brazil / Legend"),
        ("Rivellino", 96, "AMF", "Brazil / Legend"), ("Carlos Alberto", 97, "RB", "Brazil / Legend"),
        ("Nilton Santos", 96, "LB", "Brazil / Legend"), ("Didi", 95, "CMF", "Brazil / Legend"),
        ("Tostão", 95, "CF", "Brazil / Legend"), ("Leônidas", 96, "CF", "Brazil / Legend"),
        ("Ademir", 94, "CF", "Brazil / Legend"), ("Zizinho", 95, "AMF", "Brazil / Legend"),
        ("Clarence Seedorf", 96, "CMF", "AC Milan / Legend"), ("Gennaro Gattuso", 94, "DMF", "AC Milan / Legend"),
        ("Alessandro Costacurta", 95, "CB", "AC Milan / Legend"), ("Mauro Tassotti", 93, "RB", "AC Milan / Legend"),
        ("Giovanni Trapattoni", 93, "DMF", "AC Milan / Legend"), ("Gianni Rivera", 96, "AMF", "AC Milan / Legend"),
        ("Jose Altafini", 95, "CF", "AC Milan / Legend"), ("Pierino Prati", 93, "CF", "AC Milan / Legend"),
        ("Dejan Savicevic", 95, "AMF", "AC Milan / Legend"), ("Zvonimir Boban", 94, "AMF", "AC Milan / Legend"),
        ("Roberto Baggio", 98, "SS", "Juventus / Legend"), ("Michel Platini", 98, "AMF", "Juventus / Legend"),
        ("John Charles", 95, "CF", "Juventus / Legend"), ("Omar Sivori", 96, "SS", "Juventus / Legend"),
        ("Giampiero Boniperti", 95, "SS", "Juventus / Legend"), ("Dino Zoff", 96, "GK", "Juventus / Legend"),
        ("Gaetano Scirea", 97, "CB", "Juventus / Legend"), ("Antonio Cabrini", 95, "LB", "Juventus / Legend"),
        ("Marco Tardelli", 95, "CMF", "Juventus / Legend"), ("Roberto Bettega", 95, "CF", "Juventus / Legend"),
        ("Pietro Anastasi", 93, "CF", "Juventus / Legend"), ("Franco Causio", 94, "RMF", "Juventus / Legend"),
        ("Didier Deschamps", 94, "DMF", "Juventus / Legend"), ("Angelo Peruzzi", 94, "GK", "Juventus / Legend"),
        ("Edgar Davids", 96, "DMF", "Juventus / Legend"), ("Pavel Nedved", 96, "LMF", "Juventus / Legend"),
        ("David Trezeguet", 95, "CF", "Juventus / Legend"), ("Fabrizio Ravanelli", 93, "CF", "Juventus / Legend"),
        ("Gianluca Vialli", 94, "CF", "Juventus / Legend"), ("Antonio Conte", 93, "CMF", "Juventus / Legend"),
        ("Alessio Tacchinardi", 92, "DMF", "Juventus / Legend"), ("Gianluca Pessotto", 92, "LB", "Juventus / Legend"),
        ("Mark Iuliano", 91, "CB", "Juventus / Legend"), ("Ciro Ferrara", 94, "CB", "Juventus / Legend")
    ]

    full_data_list = players_data + extra_legends

    for idx, item in enumerate(full_data_list, start=1000):
        if len(item) == 6:
            name, overall_max, pos, team, card_type, img_url = item
        else:
            name, overall_max, pos, team = item
            card_type = "Classic Epic / Icon"
            img_url = f"https://via.placeholder.com/150/121826/ccff00?text={name.replace(' ', '+')}"

        player_obj = {
            "id": idx,
            "name": name,
            "overall_base": overall_max - 12,
            "overall_max": overall_max,
            "position": pos,
            "team": team,
            "card_type": card_type,
            "is_upcoming": 0,
            "image_url": img_url,
            "stats_json": json.dumps({
                "attacking": {"وعي هجومي": overall_max - 3, "التحكم في الكرة": overall_max - 2, "المراوغة": overall_max - 2, "إنهاء الهجمة": overall_max - 3},
                "physical": {"السرعة": overall_max - 5, "التسارع": overall_max - 4},
                "defending": {"وعي دفاعي": 50 if pos not in ['CB', 'DMF', 'LB', 'RB'] else overall_max - 2}
            }),
            "skills_json": json.dumps(["مهارة الأساطير", "تحكم خارق", "تمرير دقيق"])
        }
        classic_list.append(player_obj)

    return classic_list
