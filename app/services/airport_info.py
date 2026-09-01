from app.data.airports import find_airport


MILITARY_LIKE = {"LTAD", "LTAE", "LTAH", "LTAO", "LTAP", "LTAT", "LTFA", "LTDB"}


def geography_profile(airport, lang="en"):
    lat = airport.get("lat", 0)
    lon = airport.get("lon", 0)
    city = airport.get("city", "")

    if lang == "tr":
        if lon > 39.5 and lat > 38.5:
            return "Dogu veya Kuzeydogu Anadolu karakteri; yuksek rakim, daglik cevre, kis kosullari ve buzlanma farkindaligi onemlidir."
        if lon > 39.0 and lat <= 38.5:
            return "Guneydogu Anadolu platosu etkisi; yaz sicaklari, gorus/toz ve sicak hava performansi yaklasma brifinginde dusunulmelidir."
        if lat > 40.7 and lon > 32:
            return "Karadeniz kusagina yakin; nem, yagis, dusuk bulut tabani ve kiyi-dag gecisleri yaklasma farkindaligi yaratir."
        if lon < 30.5 and lat < 39.5:
            return "Ege veya Akdeniz kiyi etkilerine yakin; deniz meltemi, yaz sicaklari ve cevredeki tepelik arazi dikkate alinir."
        if lon < 31.5 and lat >= 39.5:
            return "Marmara/Ege gecis bolgesi; deniz etkili hava, sehirlesme ve tepelik arazi birlikte degerlendirilebilir."
        if city == "Istanbul":
            return "Marmara havzasi karakteri; deniz etkili hava ve yogun terminal sahasi one cikar."
        if city in {"Antalya", "Mugla"}:
            return "Akdeniz/Ege turizm kiyisina yakin; deniz etkisi, daglik cevre ve yaz sicakligi birlikte degerlendirilir."
        return "Ic Anadolu veya gecis kusagi karakteri; genis plato, rakim, mevsimsel ruzgar ve kis sartlari onemlidir."

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
    if city == "Istanbul":
        return "Located in the Marmara basin, where maritime weather and a dense terminal environment are prominent."
    if city in {"Antalya", "Mugla"}:
        return "Near the Mediterranean/Aegean tourism coast; maritime influence, mountainous surroundings, and summer heat should be considered together."
    return "Interior Anatolian or transition-zone profile; broad plateau terrain, elevation, seasonal winds, and winter conditions are relevant to approach awareness."


def airport_profile(icao, lang="en"):
    airport = find_airport(icao)
    if not airport:
        return None

    if lang == "tr":
        traffic = "Sivil yolcu trafigi sinirli veya askeri/ozel kullanim karakteri baskindir." if icao in MILITARY_LIKE else "Bolgesel yolcu trafigi agirliklidir; ic hat baglantilari ve yerel talep belirleyicidir."
        return {
            "nameOrigin": f"Adi hizmet verdigi {airport['city']} bolgesiyle iliskilidir.",
            "traffic": traffic,
            "geography": geography_profile(airport, "tr"),
            "statsSource": "Guncel kesin yolcu sayilari icin resmi DHMI istatistikleri kontrol edilmelidir.",
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
            "approach": "Yaklasma brifinginde chart basligi, procedure tipi, IAF/IF/FAF, profil irtifalari, minimumlar ve missed approach sirayla okunmalidir.",
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
