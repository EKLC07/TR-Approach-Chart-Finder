AIRPORTS_RAW = [
    ("LTAC", "ESB", "Ankara", "Esenboga"),
    ("LTAD", "ANK", "Ankara", "Murted / Akinci"),
    ("LTAE", "ANK", "Ankara", "Akinci"),
    ("LTAF", "ADA", "Adana", "Sakirpasa"),
    ("LTAH", "AFY", "Afyon", "Afyon"),
    ("LTAI", "AYT", "Antalya", "Antalya"),
    ("LTAJ", "GZT", "Gaziantep", "Oguzeli"),
    ("LTAL", "KFS", "Kastamonu", "Kastamonu"),
    ("LTAN", "KYA", "Konya", "Konya"),
    ("LTAO", "N/A", "Turkey", "LTAO"),
    ("LTAP", "MZH", "Amasya", "Merzifon"),
    ("LTAR", "VAS", "Sivas", "Nuri Demirag"),
    ("LTAS", "ONQ", "Zonguldak", "Caycuma"),
    ("LTAT", "MLX", "Malatya", "Erhac"),
    ("LTAU", "ASR", "Kayseri", "Erkilet"),
    ("LTAW", "TJK", "Tokat", "Tokat"),
    ("LTAY", "DNZ", "Denizli", "Cardak"),
    ("LTAZ", "NAV", "Nevsehir", "Kapadokya"),
    ("LTBA", "ISL", "Istanbul", "Ataturk"),
    ("LTBJ", "ADB", "Izmir", "Adnan Menderes"),
    ("LTBS", "DLM", "Mugla", "Dalaman"),
    ("LTFE", "BJV", "Mugla", "Milas-Bodrum"),
    ("LTFJ", "SAW", "Istanbul", "Sabiha Gokcen"),
    ("LTFM", "IST", "Istanbul", "Istanbul"),
    ("LTCC", "DIY", "Diyarbakir", "Diyarbakir"),
    ("LTCD", "ERC", "Erzincan", "Yildirim Akbulut"),
    ("LTCE", "ERZ", "Erzurum", "Erzurum"),
    ("LTCF", "KSY", "Kars", "Harakani"),
    ("LTCG", "TZX", "Trabzon", "Trabzon"),
    ("LTCI", "VAN", "Van", "Ferit Melen"),
    ("LTCJ", "BAL", "Batman", "Batman"),
    ("LTCK", "MSR", "Mus", "Sultan Alparslan"),
    ("LTCL", "SXZ", "Siirt", "Siirt"),
    ("LTCM", "NOP", "Sinop", "Sinop"),
    ("LTCN", "KCM", "Kahramanmaras", "Kahramanmaras"),
    ("LTCO", "AJI", "Agri", "Ahmed-i Hani"),
    ("LTCP", "ADF", "Adiyaman", "Adiyaman"),
    ("LTCR", "MQM", "Mardin", "Aziz Sancar"),
    ("LTCS", "GNY", "Sanliurfa", "GAP"),
    ("LTCT", "IGD", "Igdir", "Sehit Bulent Aydin"),
    ("LTCU", "BGG", "Bingol", "Bingol"),
    ("LTCV", "NKT", "Sirnak", "Serafettin Elci"),
    ("LTCW", "YKO", "Hakkari", "Yuksekova Selahaddin Eyyubi"),
    ("LTDA", "HTY", "Hatay", "Hatay"),
    ("LTDB", "N/A", "Turkey", "LTDB"),
    ("LTFA", "N/A", "Izmir", "Cigli"),
    ("LTFB", "N/A", "Izmir", "Selcuk Efes"),
    ("LTFC", "ISE", "Isparta", "Suleyman Demirel"),
    ("LTFD", "EDO", "Balikesir", "Koca Seyit"),
    ("LTFG", "GZP", "Antalya", "Gazipasa-Alanya"),
    ("LTFH", "SZF", "Samsun", "Carsamba"),
    ("LTBO", "USQ", "Usak", "Usak"),
    ("LTBQ", "KCO", "Kocaeli", "Cengiz Topel"),
    ("LTBR", "YEI", "Bursa", "Yenisehir"),
    ("LTBU", "TEQ", "Tekirdag", "Corlu Ataturk"),
    ("LTBZ", "KZR", "Kutahya", "Zafer"),
    ("LTCA", "EZS", "Elazig", "Elazig"),
]

AIRPORT_COORDS = {
    "LTAC": (40.128, 32.995), "LTAD": (40.079, 32.565), "LTAE": (40.078, 32.565),
    "LTAF": (36.982, 35.280), "LTAH": (38.726, 30.601), "LTAI": (36.898, 30.800),
    "LTAJ": (36.948, 37.479), "LTAL": (41.315, 33.795), "LTAN": (37.979, 32.562),
    "LTAO": (38.353, 38.253), "LTAP": (40.829, 35.522), "LTAR": (39.813, 36.903),
    "LTAS": (41.506, 32.089), "LTAT": (38.435, 38.091), "LTAU": (38.770, 35.495),
    "LTAW": (40.307, 36.367), "LTAY": (37.785, 29.701), "LTAZ": (38.771, 34.534),
    "LTBA": (40.976, 28.814), "LTBJ": (38.292, 27.157), "LTBS": (36.713, 28.793),
    "LTFE": (37.250, 27.664), "LTFJ": (40.898, 29.309), "LTFM": (41.275, 28.752),
    "LTCC": (37.894, 40.201), "LTCD": (39.711, 39.527), "LTCE": (39.956, 41.170),
    "LTCF": (40.562, 43.115), "LTCG": (40.995, 39.789), "LTCI": (38.469, 43.332),
    "LTCJ": (37.929, 41.116), "LTCK": (38.747, 41.661), "LTCL": (37.979, 41.840),
    "LTCM": (42.015, 35.066), "LTCN": (37.539, 36.953), "LTCO": (39.654, 43.026),
    "LTCP": (37.731, 38.469), "LTCR": (37.223, 40.631), "LTCS": (37.445, 38.895),
    "LTCT": (39.976, 43.876), "LTCU": (38.859, 40.592), "LTCV": (37.364, 42.059),
    "LTCW": (37.550, 44.238), "LTDA": (36.362, 36.282), "LTDB": (38.319, 27.160),
    "LTFA": (38.514, 27.010), "LTFB": (37.950, 27.329), "LTFC": (37.855, 30.368),
    "LTFD": (39.619, 27.926), "LTFG": (36.299, 32.301), "LTFH": (41.254, 36.567),
    "LTBO": (38.682, 29.471), "LTBQ": (40.735, 30.083), "LTBR": (40.255, 29.562),
    "LTBU": (41.138, 27.919), "LTBZ": (39.111, 30.129), "LTCA": (38.606, 39.291),
}


def build_airports():
    airports = []
    for icao, iata, city, name in AIRPORTS_RAW:
        airport = {"icao": icao, "iata": iata, "city": city, "name": name}
        if icao in AIRPORT_COORDS:
            airport["lat"], airport["lon"] = AIRPORT_COORDS[icao]
        airports.append(airport)
    return sorted(airports, key=lambda item: item["icao"])


AIRPORTS = build_airports()
ALLOWED_ICAOS = {airport["icao"] for airport in AIRPORTS}


def find_airport(icao):
    icao = (icao or "").strip().upper()
    return next((airport for airport in AIRPORTS if airport["icao"] == icao), None)


def is_valid_icao(icao):
    return (icao or "").strip().upper() in ALLOWED_ICAOS
