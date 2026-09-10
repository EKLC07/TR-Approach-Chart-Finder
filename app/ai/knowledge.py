import re


AVIATION_TOPICS = {
    "minimums": {
        "tr": "Minimumlar bölümünde yaklaşma kategorisi, DA/DH veya MDA/MDH, OCA/OCH, RVR/VIS ve chart notları birlikte okunur.",
        "en": "In the minimums section, read the approach category, DA/DH or MDA/MDH, OCA/OCH, RVR/VIS, and chart notes together.",
    },
    "missed": {
        "tr": "Pas geçmede ilk tırmanış, dönüş yönü, hedef fix/holding, irtifa kısıtı ve varsa DME koşulu ayrı ayrı yakalanmalıdır.",
        "en": "For missed approach, identify the initial climb, turn direction, target fix/holding, altitude restriction, and any DME condition separately.",
    },
    "briefing": {
        "tr": "İyi bir chart briefing sırası: meydan/pist, yaklaşma tipi, frekanslar, plan view, profile view, minimumlar, missed approach ve tehditlerdir.",
        "en": "A good chart briefing flow is: airport/runway, approach type, frequencies, plan view, profile view, minimums, missed approach, and threats.",
    },
    "files": {
        "tr": "PDF/JPG yorumlama için dosya okuma katmanı hazır tutulur; gerçek görsel yorumlama için lokal vision model veya bulut AI bağlantısı gerekir.",
        "en": "PDF/JPG interpretation needs a file-reading layer plus either a local vision model or a cloud AI connection for real visual reasoning.",
    },
    "frequencies": {
        "tr": "Frekans sorularında APP, TWR, ATIS, GND ve navigasyon yardımcı frekansları birbirinden ayrı okunmalıdır.",
        "en": "For frequency questions, APP, TWR, ATIS, GND, and navigation-aid frequencies should be read separately.",
    },
    "holding": {
        "tr": "Holding bilgisinde fix, inbound/outbound course, dönüş yönü, irtifa ve azami holding hızı beraber değerlendirilir.",
        "en": "For holding, read the fix, inbound/outbound course, turn direction, altitude, and max holding speed together.",
    },
    "descent": {
        "tr": "Alçalma başlangıcında FAF/FAP, DME mesafesi, profil irtifası ve yaklaşık 3° süzülüş yolu birlikte kontrol edilir.",
        "en": "For descent start, check FAF/FAP, DME distance, profile altitude, and the approximate 3° descent path together.",
    },
    "course": {
        "tr": "Course/baş değerleri final hattı, published course, missed approach track ve varsa holding yönü olarak ayrılmalıdır.",
        "en": "Course/heading values should be separated as final course, published course, missed approach track, and holding direction when available.",
    },
}


def detect_topic(text: str) -> str:
    q = (text or "").lower()
    if _has_any(q, ("minimum", "da/dh", "mda", "rvr", "vis")):
        return "minimums"
    if _has_any(q, ("alçal", "alcal", "3 derece", "3°", "glide", "faf", "fap", "mapt", "app e", "app'e", "app’e", "approach mode")):
        return "descent"
    if _has_any(q, ("frekans", "frequency", "atis", "twr", "tower", "kule")):
        return "frequencies"
    if _has_any(q, ("holding", "hold", "bekleme", "max holding")):
        return "holding"
    if _has_any(q, ("course", "heading", "track", "inbound", "baş", "bas", "crs")):
        return "course"
    if _has_any(q, ("missed", "pas geç", "pas gec", "go around", "holding", "tırmanış", "tirmanis", "climb")):
        return "missed"
    if _has_any(q, ("pdf", "jpg", "jpeg", "dosya", "file", "image", "görsel", "gorsel")):
        return "files"
    if _has_any(q, ("brief", "briefing", "brifing", "chart", "harita", "yaklaşma", "yaklasma", "approach", "ils", "rnav", "vor")):
        return "briefing"
    return None


def topic_answer(topic: str, lang: str) -> str:
    return AVIATION_TOPICS.get(topic, AVIATION_TOPICS["briefing"]).get(lang, AVIATION_TOPICS["briefing"]["en"])


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    for marker in markers:
        marker = marker.lower()
        if " " in marker or "'" in marker or "’" in marker or "°" in marker or "/" in marker:
            if marker in text:
                return True
            continue
        if len(marker) <= 4:
            if re.search(rf"(?<!\w){re.escape(marker)}(?!\w)", text):
                return True
            continue
        if marker in text:
            return True
    return False
