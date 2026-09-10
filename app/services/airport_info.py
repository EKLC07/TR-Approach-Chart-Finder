from app.data.airports import find_airport


MILITARY_LIKE = {"LTAD", "LTAE", "LTAH", "LTAO", "LTAP", "LTAT", "LTFA", "LTDB"}


def geography_profile(airport, lang="en"):
    lat = airport.get("lat", 0)
    lon = airport.get("lon", 0)
    city = airport.get("city", "")

    if lang == "tr":
        if lon > 39.5 and lat > 38.5:
            return "Doğu veya Kuzeydoğu Anadolu karakteri; yüksek rakım, dağlık çevre, kış koşulları ve buzlanma farkındalığı önemlidir."
        if lon > 39.0 and lat <= 38.5:
            return "Güneydoğu Anadolu platosu etkisi; yaz sıcakları, görüş/toz ve sıcak hava performansı yaklaşma brifinginde düşünülmelidir."
        if lat > 40.7 and lon > 32:
            return "Karadeniz kuşağına yakın; nem, yağış, düsük bulut tabanı ve kıyı-dağ geçişleri yaklaşma farkındalığı yaratır."
        if lon < 30.5 and lat < 39.5:
            return "Ege ve Akdeniz kıyı etkilerine yakın; deniz meltemi, yaz sıcakları ve çevredeki tepelik arazi dikkate alınır."
        if lon < 31.5 and lat >= 39.5:
            return "Marmara/Ege geçiş bölgesi; deniz etkili hava, şehirleşme ve tepelik arazi birlikte değerlendirilebilir."
        if city == "İstanbul":
            return "Marmara havzası karakteri; deniz etkili hava ve yoğun terminal sahası öne çıkar."
        if city in {"Antalya", "Muğla"}:
            return "Akdeniz/Ege turizm kıyısına yakın; deniz etkisi, dağlık çevre ve yaz sıcaklığı birlikte değerlendirilir."
        return "İç Anadolu veya geciş kuşağı karakteri; geniş plato, rakım, mevsimsel rüzgar ve kış şartları önemlidir."

    if lon > 39.5 and lat > 38.5:
        return "Eastern or Northeastern Anatolian terrain profile; high elevation, surrounding mountains, winter weather, and icing awareness are important."
    if lon > 39.0 and lat <= 38.5:
        return "Southeastern Anatolian plateau influence; summer heat, visibility or dust, and high-temperature performance should be considered during approach briefing."
    if lat > 40.7 and lon > 32:
        return "Near the Black Sea belt; humidity, precipitation, low cloud bases, and coastal-to-mountain transitions can affect approach awareness."
    if lon < 30.5 and lat < 39.5:
        return "Close to Aegean or Mediterranean coastal influences; sea breeze, summer heat, and nearby hilly terrain should be considered."
    if lon < 31.5 and lat >= 39.5:
        return "Located in the Marmara/Aegean transition region; maritime weather, urban areas, and hilly terrain may all be relevant."
    if city == "İstanbul":
        return "Located in the Marmara basin, where maritime weather and a dense terminal environment are prominent."
    if city in {"Antalya", "Muğla"}:
        return "Near the Mediterranean/Aegean tourism coast; maritime influence, mountainous surroundings, and summer heat should be considered together."
    return "Interior Anatolian or transition-zone profile; broad plateau terrain, elevation, seasonal winds, and winter conditions are relevant to approach awareness."


def airport_profile(icao, lang="en"):
    airport = find_airport(icao)
    if not airport:
        return None

    if lang == "tr":
        traffic = "Sivil yolcu trafiği sınırlı veya askeri/özel kullanım karakteri baskındır." if icao in MILITARY_LIKE else "Bölgesel yolcu trafiği ağırlıklıdır; iç hat bağlantıları ve yerel talep belirleyicidir."
        return {
            "nameOrigin": f"Adı hizmet verdiği {airport['city']} bölgesiyle ilişkilidir.",
            "traffic": traffic,
            "geography": geography_profile(airport, "tr"),
            "statsSource": "Güncel kesin yolcu sayıları için resmi DHMI istatistikleri kontrol edilmelidir.",
        }

    traffic = "Civil passenger traffic is limited or the airport has a military/special-use character." if icao in MILITARY_LIKE else "Regional passenger traffic is the main profile; domestic links and local demand are usually the key drivers."
    return {
        "nameOrigin": f"The airport name is associated with the {airport['city']} region or its local identity.",
        "traffic": traffic,
        "geography": geography_profile(airport, "en"),
        "statsSource": "Use official DHMI statistics for exact current passenger figures.",
    }


def airport_info(icao, lang="en"):
    airport = find_airport(icao)
    profile = airport_profile(icao, lang)
    if not airport or not profile:
        return None

    if lang == "tr":
        return {
            "airport": airport,
            "terrain": geography_profile(airport, "tr"),
            "approach": "Yaklaşma brifinginde chart başlığı, prosedür tipi, IAF/IF/FAF, profil irtifaları, minimumlar ve pas geçme sırayla okunmalıdır.",
            "culture": profile["nameOrigin"],
            "profile": profile,
        }

    return {
        "airport": airport,
        "terrain": geography_profile(airport, "en"),
        "approach": "For approach briefing, read the chart title, procedure type, IAF/IF/FAF, profile altitudes, minimums, and missed approach section in order.",
        "culture": profile["nameOrigin"],
        "profile": profile,
    }
