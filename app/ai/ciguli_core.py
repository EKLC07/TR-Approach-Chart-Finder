from app.ai.brain import Thought, think
from app.ai.daily_talk import daily_answer, detect_daily_intent
from app.ai.knowledge import detect_topic, topic_answer
from app.ai.language import is_greeting, is_smalltalk
import re


def _upper_first(char: str, lang: str) -> str:
    if lang == "tr" and char == "i":
        return "İ"
    return char.upper()


def _polish_answer(text: str, lang: str) -> str:
    """Give every Ciguli answer a presentable sentence shape.

    The local brain can generate short conversational fragments. Before they
    reach the UI, this pass fixes obvious vitrine issues: first letters,
    sentence starts, bullet starts, and missing final punctuation.
    """
    raw = str(text or "").strip()
    if not raw:
        return raw

    result = []
    should_capitalize = True
    opening_marks = set(" \t\r\n\"'“”‘’([{*-•")
    end_marks = set(".!?…")

    for index, char in enumerate(raw):
        if should_capitalize and char.isalpha():
            result.append(_upper_first(char, lang))
            should_capitalize = False
            continue
        result.append(char)
        if char in end_marks:
            should_capitalize = True
        elif char == "\n":
            should_capitalize = True
        elif should_capitalize and char not in opening_marks:
            should_capitalize = False

    polished = "".join(result).strip()
    if polished and polished[-1] not in ".!?…:;":
        polished += "."
    return polished


def _remembered_name(memory: dict) -> str:
    facts = memory.get("facts", {}) if isinstance(memory, dict) else {}
    name = str(facts.get("display_name", "")).strip()
    return name if 1 < len(name) < 32 else ""


def _memory_line(memory: dict, lang: str) -> str:
    facts = memory.get("facts", {}) if isinstance(memory, dict) else {}
    parts = []
    if facts.get("display_name"):
        parts.append(str(facts["display_name"]))
    if facts.get("simulator"):
        parts.append(str(facts["simulator"]))
    if facts.get("aircraft"):
        parts.append(str(facts["aircraft"]))
    if facts.get("skill_level"):
        parts.append(str(facts["skill_level"]))
    if facts.get("interests"):
        parts.append(", ".join(map(str, facts["interests"][:4])))
    if not parts:
        return ""
    if lang == "tr":
        return "Seni böyle hatırlıyorum: " + " · ".join(parts)
    return "Here is what I remember about you: " + " · ".join(parts)


def _smalltalk_answer(question: str, lang: str, memory: dict) -> str:
    name = _remembered_name(memory)
    facts = memory.get("facts", {}) if isinstance(memory, dict) else {}
    sim = facts.get("simulator")
    level = facts.get("skill_level")

    if lang == "tr":
        greeting = f"İyiyim {name}, " if name else "İyiyim kaptan, "
        lines = [
            greeting + "radarım açık, kahvem hayali ama frekans temiz.",
            "İstersen muhabbet ederiz; istersen bir yaklaşma chartını beraber sakin sakin sökeriz.",
        ]
        if sim or level:
            detail = []
            if sim:
                detail.append(f"{sim} uçtuğunu")
            if level:
                detail.append(f"seviyeni {level} olarak")
            lines.append("Bu arada seni " + " ve ".join(detail) + " hatırlıyorum; cevaplarımı ona göre ayarlayacağım.")
        return "\n\n".join(lines)

    greeting = f"I am good, {name}. " if name else "I am good, captain. "
    lines = [
        greeting + "Radar is alive, imaginary coffee is hot, frequency is clean.",
        "We can just chat, or we can calmly break down an approach chart together.",
    ]
    if sim or level:
        detail = []
        if sim:
            detail.append(f"you fly {sim}")
        if level:
            detail.append(f"your level is {level}")
        lines.append("I remember that " + " and ".join(detail) + ", so I will tune my answers around that.")
    return "\n\n".join(lines)


def _identity_answer(lang: str) -> str:
    if lang == "tr":
        return (
            "Ben Ciguli; Approvaq içindeki yerel havacılık asistanıyım.\n\n"
            "Şu an dışarıdaki bir AI servisine bağlanmadan çalışıyorum. Basit sohbet edebilirim, "
            "havacılık konularında yardımcı olurum, chart bağlamını kullanırım ve konuştukça bazı tercihlerini yerel hafızaya yazarım."
        )
    return (
        "I am Ciguli, the local aviation assistant inside Approvaq.\n\n"
        "Right now I run without connecting to an outside AI service. I can handle simple conversation, "
        "help with aviation topics, use chart context, and remember some preferences locally as we talk."
    )


def _is_self_disclosure(question: str) -> bool:
    clean = (question or "").lower()
    markers = (
        "ben ", "benim ", "kullanıyorum", "kullaniyorum", "seviyorum", "severim",
        "yeniyim", "orta seviy", "ileri seviy", "i use", "i fly", "i like",
        "i love", "i am new", "i'm new", "my simulator",
    )
    return any(marker in clean for marker in markers)


def _learning_answer(question: str, lang: str) -> str:
    clean = (question or "").lower()
    detected = []
    if "msfs" in clean or "microsoft flight simulator" in clean:
        detected.append("MSFS")
    if "x-plane" in clean or "x plane" in clean or "xp12" in clean:
        detected.append("X-Plane")
    if "ifr" in clean:
        detected.append("IFR")
    if "airbus" in clean or "a320" in clean or "a321" in clean:
        detected.append("Airbus")
    if "boeing" in clean or "737" in clean:
        detected.append("Boeing")

    if lang == "tr":
        if detected:
            return (
                "Tamam kaptan, bunu hafızama alıyorum: " + ", ".join(detected) + ".\n\n"
                "Bundan sonra cevap verirken bunları hesaba katarım. Mesela IFR’da yeniysen fazla teknik boğmadan, "
                "MSFS uçuyorsan da sim tarafına uygun örneklerle anlatırım."
            )
        return (
            "Tamam kaptan, bunu hafızama not ediyorum.\n\n"
            "Ciguli konuştukça seni tanıyacak; sim tercihlerin, seviyen ve sevdiğin uçak/konular cevap tarzımı şekillendirecek."
        )

    if detected:
        return (
            "Got it, captain. I am saving this to memory: " + ", ".join(detected) + ".\n\n"
            "From now on I will adapt my answers around that. If you are new to IFR, I will keep explanations clearer; "
            "if you fly MSFS, I will lean into sim-friendly examples."
        )
    return (
        "Got it, captain. I am saving that to memory.\n\n"
        "As we talk, Ciguli will learn your simulator, skill level, and aviation interests, then adapt the way it explains things."
    )


def _tone_prefix(question: str, lang: str) -> str:
    if lang == "tr":
        if is_greeting(question) or is_smalltalk(question):
            return "Buradayım kaptan. Bugün ister sakin sakin havacılık muhabbeti yaparız, ister seçili chartı parçalara ayırırız."
        return ""
    if is_greeting(question) or is_smalltalk(question):
        return "I am here, captain. We can keep it casual or break the selected chart down like a cockpit briefing."
    return ""


def _practical_aviation_answer(question: str, lang: str, memory: dict) -> str:
    clean = (question or "").lower()

    if lang == "tr":
        if any(marker in clean for marker in ("app", "approach mode", "yaklaşma modu", "yaklasma modu", "glide", "gs", "localizer", "loc")):
            return (
                "APP modunu rastgele basma kaptan. ILS tarafında frekans/course hazır olmalı, yaklaşma izni alınmalı, localizer canlı ya da yakalanmış olmalı; glide slope yukarıdan gelirken APP arm edilir.\n\n"
                "Seçili chart varsa FAF/FAP, DME ve profil irtifasına bakıp “şu noktada hazır olman lazım” diye net söylerim."
            )

        if any(marker in clean for marker in ("iniş", "inis", "landing", "flare", "touchdown")):
            return (
                "İnişte ana iş stabil yaklaşma kaptan: doğru konfigürasyon, doğru hız, doğru alçalma oranı ve pist hattı. Son anda düzeltmeye çalışmak yerine 1000 FT civarında tablo bozuksa pas geçmek daha temiz karar."
            )

        if any(marker in clean for marker in ("kalkış", "kalkis", "takeoff", "rotate", "v1", "vr", "v2")):
            return (
                "Kalkışta sırayı sade tut: thrust set, speed alive, V1 karar, VR rotate, positive climb sonrası gear up. Sonrası uçak tipine göre acceleration altitude ve flap toplama akışı gelir."
            )

        if any(marker in clean for marker in ("hız", "hiz", "speed", "ias", "kt", "knot")):
            return (
                "Hız tarafında tek rakama kilitlenme kaptan; uçak ağırlığı, konfigürasyon, rüzgâr ve yaklaşma tipine göre değişir. Charttaki limitler ayrı, uçağın VAPP/VREF değeri ayrı okunmalı."
            )

        return (
            "Bunu net cevaplamam için bir detay lazım kaptan: kalkış mı, cruise mı, yaklaşma mı, iniş mi konuşuyoruz?"
        )

    if any(marker in clean for marker in ("app", "approach mode", "glide", "gs", "localizer", "loc")):
        return (
            "Do not press APP randomly, captain. For an ILS, frequency/course should be set, approach clearance should be received, and the localizer should be alive or captured; arm APP as the glide slope comes from above.\n\n"
            "With a selected chart, I can point to the FAF/FAP, DME, and profile altitude for the exact setup point."
        )

    if any(marker in clean for marker in ("landing", "flare", "touchdown")):
        return (
            "For landing, the key is a stable approach: correct configuration, speed, descent rate, and runway alignment. If the picture is bad around 1000 FT, a go-around is the cleaner decision."
        )

    if any(marker in clean for marker in ("takeoff", "rotate", "v1", "vr", "v2")):
        return (
            "For takeoff, keep the flow clean: thrust set, speed alive, V1 decision, VR rotate, positive climb, gear up. After that come acceleration altitude and flap retraction depending on aircraft type."
        )

    if any(marker in clean for marker in ("speed", "ias", "kt", "knot")):
        return (
            "Do not lock onto one generic speed. Weight, configuration, wind, and approach type matter. Chart limits and aircraft VAPP/VREF are separate values."
        )

    return (
        "I need one detail to answer cleanly, captain: are we talking takeoff, cruise, approach, or landing?"
    )


def _natural_answer(question: str, lang: str, memory: dict, thought: Thought) -> str:
    name = _remembered_name(memory)

    if lang == "tr":
        prefix = f"{name}, " if name else ""
        if thought.mode == "general_question":
            lines = [
                f"{prefix}anladım kaptan.",
                "Bunu biraz daha açarsan net ve kısa cevaplayayım.",
            ]
        elif thought.mode == "aviation":
            return _practical_aviation_answer(question, lang, memory)
        else:
            lines = [
                f"{prefix}tamam kaptan, buradayım.",
                "Devam et; neye bakıyorsak oradan yürüyelim.",
            ]
        return "\n\n".join(lines)

    prefix = f"{name}, " if name else ""
    if thought.mode == "general_question":
        lines = [
            f"{prefix}got it, captain.",
            "Give me a little more context and I will answer it cleanly.",
        ]
    elif thought.mode == "aviation":
        return _practical_aviation_answer(question, lang, memory)
    else:
        lines = [
            f"{prefix}alright captain, I am here.",
            "Go on; I will follow your lead.",
        ]
    return "\n\n".join(lines)


def _requested_chart_data_topic(question: str) -> str:
    clean = (question or "").lower()
    checks = [
        ("minimums", ("minimum", "minima", "da/dh", "mda", "mdh", "oca", "och", "rvr", "vis", "görüş", "gorus")),
        ("descent", ("alçal", "alcal", "3 derece", "3°", "glide", "süzül", "suzul", "başlama", "baslama", "faf", "fap", "mapt", "app e", "app'e", "app’e", "appe", "approach mode")),
        ("frequencies", ("frekans", "atis", "twr", "tower", "kule", "frequency", "frequencies")),
        ("holding", ("holding", "hold", "bekleme", "max holding")),
        ("missed", ("missed", "pas geç", "pas gec", "go around", "go-around", "tırman", "tirman")),
        ("runway", ("pist", "runway", "rakım", "rakim", "elev", "threshold", "transition")),
        ("course", ("course", "baş", "bas", "heading", "track", "inbound", "crs")),
        ("procedure", ("prosedür", "prosedur", "procedure", "yaklaşma tipi", "yaklasma tipi", "approach type")),
        ("summary", ("özet", "ozet", "analiz", "brief", "brifing", "briefing", "bu chart", "chartta ne", "ne var")),
    ]
    for topic, markers in checks:
        if _has_marker(clean, markers):
            return topic
    return ""


def _requested_context_topic(question: str) -> str:
    clean = (question or "").lower()
    checks = [
        ("city", ("hangi şehir", "hangi sehir", "şehir neresi", "sehir neresi", "neresi burası", "neresi burasi", "which city", "what city")),
        ("airport", ("hangi meydan", "hangi havalimanı", "hangi havalimani", "meydan neresi", "airport name", "which airport", "what airport")),
        ("runway_direction", ("pist yön", "pist yon", "pist kaç derece", "pist kac derece", "runway direction", "pist heading", "runway heading", "hangi yöne", "hangi yone", "ne yönlü", "ne yonlu")),
        ("runway", ("hangi pist", "pist ne", "pist hangisi", "hangi pistteyiz", "which runway", "what runway", "which runway are we on", "runway ne")),
        ("location", ("nerede", "konum", "location", "where is", "where are we")),
    ]
    for topic, markers in checks:
        if _has_marker(clean, markers):
            return topic
    return ""


def _has_marker(text: str, markers: tuple[str, ...]) -> bool:
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


def _analysis_value(context: dict, titles: tuple[str, ...], labels: tuple[str, ...]) -> str:
    titles = tuple(title.lower() for title in titles)
    labels = tuple(label.lower() for label in labels)
    for section in _analysis_sections(context):
        title = str(section.get("title", "")).lower()
        if titles and not any(key in title for key in titles):
            continue
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).lower()
            value = str(item.get("value", "")).strip()
            if value and any(key in label for key in labels):
                return value
    return ""


def _runway_from_context(context: dict) -> str:
    runway = _analysis_value(
        context,
        ("prosedür", "procedure", "pist", "runway"),
        ("pist", "runway"),
    )
    match = re.search(r"\bRWY\s*([0-3]\d[LRCT]?)\b", runway, re.I)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b([0-3]\d[LRCT]?)\b", runway, re.I)
    return match.group(1).upper() if match else ""


def _runway_direction(runway: str, lang: str) -> str:
    match = re.match(r"([0-3]\d)([LRCT]?)", runway or "", re.I)
    if not match:
        return ""
    heading = int(match.group(1)) * 10
    reciprocal = (heading + 180) % 360
    if reciprocal == 0:
        reciprocal = 360
    suffix = match.group(2).upper()
    side_tr = {"L": "sol pist", "R": "sağ pist", "C": "merkez pist", "T": "özel pist"}.get(suffix, "")
    side_en = {"L": "left runway", "R": "right runway", "C": "center runway", "T": "special runway"}.get(suffix, "")
    if lang == "tr":
        return f"{heading:03d}° manyetik baş · karşı yön {reciprocal:03d}°" + (f" · {side_tr}" if side_tr else "")
    return f"{heading:03d}° magnetic heading · reciprocal {reciprocal:03d}°" + (f" · {side_en}" if side_en else "")


def _context_answer(question: str, lang: str, context: dict) -> str:
    topic = _requested_context_topic(question)
    if not topic:
        return ""

    airport = context.get("airport") or ""
    meta = context.get("airport_meta") or {}
    city = str(meta.get("city", "")).strip()
    name = str(meta.get("name", "")).strip()
    iata = str(meta.get("iata", "")).strip()
    runway = _runway_from_context(context)
    chart = context.get("chart") or "?"

    if topic in {"city", "location"}:
        if not airport and not city:
            return "Önce bir meydan seç kaptan; sonra şehir/konum bilgisini direkt söylerim." if lang == "tr" else "Select an airport first, captain; then I can give the city/location directly."
        if lang == "tr":
            return f"Burası {city or 'şehir bilgisi yok'}; meydan {airport} {f'({iata}) ' if iata else ''}{name}.".strip()
        return f"This is {city or 'unknown city'}; airport {airport} {f'({iata}) ' if iata else ''}{name}.".strip()

    if topic == "airport":
        if not airport:
            return "Şu an aktif meydan göremiyorum kaptan; soldan bir meydan seçersen adını direkt söylerim." if lang == "tr" else "I cannot see an active airport right now, captain; select one and I will name it directly."
        if lang == "tr":
            return f"Meydan {airport} {f'({iata}) ' if iata else ''}{name}; şehir {city}.".strip()
        return f"The airport is {airport} {f'({iata}) ' if iata else ''}{name}; city {city}.".strip()

    if topic == "runway":
        if runway:
            if lang == "tr":
                return f"Bu chart RWY {runway} için. Chart no: IAC {chart}." if chart != "?" else f"Bu chart RWY {runway} için."
            return f"This chart is for RWY {runway}. Chart: IAC {chart}." if chart != "?" else f"This chart is for RWY {runway}."
        return "Seçili charttan pist bilgisini net okuyamadım kaptan; PDF üst başlığından veya analiz panelinden kontrol edelim." if lang == "tr" else "I could not read the runway clearly from the selected chart; check the PDF header or analysis panel."

    if topic == "runway_direction":
        if runway:
            direction = _runway_direction(runway, lang)
            if lang == "tr":
                return f"RWY {runway} yönü yaklaşık {direction}. Gerçek published course farklıysa charttaki course değeri esas alınır."
            return f"RWY {runway} points approximately {direction}. If the published course differs, use the chart course."
        return "Pist yönünü söylemem için seçili charttan RWY bilgisini görmem lazım kaptan." if lang == "tr" else "I need the selected chart runway before I can give the runway direction."

    return ""


def _analysis_sections(context: dict) -> list[dict]:
    analysis = context.get("analysis") or {}
    sections = analysis.get("sections") or []
    return sections if isinstance(sections, list) else []


def _find_analysis_sections(context: dict, topic: str) -> list[dict]:
    sections = _analysis_sections(context)
    title_keys = {
        "procedure": ("prosedür", "procedure"),
        "frequencies": ("frekans", "frequency"),
        "runway": ("pist", "rakım", "runway", "elevation"),
        "holding": ("holding",),
        "descent": ("alçalma", "descent"),
        "course": ("course", "heading", "baş"),
        "minimums": ("minimum",),
        "missed": ("pas geçme", "missed"),
        "summary": ("prosedür", "frequency", "frekans", "pist", "runway", "holding", "alçalma", "descent", "course", "minimum", "pas geçme", "missed"),
    }
    keys = title_keys.get(topic, ())
    found = []
    for section in sections:
        title = str(section.get("title", "")).lower()
        if any(key in title for key in keys):
            found.append(section)
    return found


def _section_lines(section: dict, lang: str, limit: int = 8) -> list[str]:
    lines: list[str] = []
    items = section.get("items") or []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()
            value = str(item.get("value", "")).strip()
            if value:
                lines.append(f"{label}: {value}" if label else value)
    value = str(section.get("value", "")).strip()
    if value and not lines:
        lines.extend(part.strip() for part in value.split("\n") if part.strip())
    return lines[:limit]


def _chart_data_answer(question: str, lang: str, context: dict) -> str:
    topic = _requested_chart_data_topic(question)
    if not topic:
        return ""

    analysis = context.get("analysis") or {}
    sections = _find_analysis_sections(context, topic)
    if topic == "summary" and sections:
        sections = sections[:6]

    if not sections:
        if not analysis:
            return ""
        if lang == "tr":
            return (
                "Kaptan, seçili chart bağlamını görüyorum ama bu değeri metin katmanından net çekemedim.\n\n"
                "Şimdilik PDF üzerinde manuel doğrulamak en sağlıklısı; OCR katmanını güçlendirdikçe bunu otomatik yakalayacağız."
            )
        return (
            "Captain, I can see the selected chart context, but I could not read that value reliably from the text layer.\n\n"
            "For now it should be verified visually in the PDF; once OCR is stronger, Ciguli can pull it automatically."
        )

    if lang == "tr":
        intro_by_topic = {
            "frequencies": "Seçili charttan okuduğum frekanslar:",
            "minimums": "Minimumlar tarafında gördüğüm değerler:",
            "holding": "Holding/hız tarafında okuduğum değer:",
            "descent": "Alçalma başlangıcı ve profil tarafında okuduğum değerler:",
            "missed": "Pas geçme prosedürü şöyle okunuyor:",
            "runway": "Pist/rakım tarafında gördüğüm değerler:",
            "course": "Course/baş tarafında gördüğüm değerler:",
            "procedure": "Prosedür başlığından okuduğum bilgiler:",
            "summary": "Kaptan, seçili charttan operasyonel olarak şunları yakaladım:",
        }
        lines = [intro_by_topic.get(topic, "Seçili charttan okuduğum değerler:")]
    else:
        intro_by_topic = {
            "frequencies": "Frequencies read from the selected chart:",
            "minimums": "Minimums-related values I can see:",
            "holding": "Holding/speed value I can read:",
            "descent": "Descent-start and profile values I can read:",
            "missed": "Missed approach reads like this:",
            "runway": "Runway/elevation values I can see:",
            "course": "Course/heading values I can see:",
            "procedure": "Procedure header values I can read:",
            "summary": "Captain, I picked up these operational items from the selected chart:",
        }
        lines = [intro_by_topic.get(topic, "Values read from the selected chart:")]

    for section in sections:
        title = str(section.get("title", "")).strip()
        section_values = _section_lines(section, lang, 7 if topic == "summary" else 10)
        if not section_values:
            continue
        if topic == "summary":
            lines.append(f"- {title}: " + "; ".join(section_values[:3]))
        else:
            lines.extend(f"- {value}" for value in section_values)

    if len(lines) == 1:
        return ""
    if lang == "tr":
        lines.append("Bunları yine de sim/gerçek operasyon ayrımıyla, resmi chart üzerinden kontrol ederek kullanmak gerekir.")
    else:
        lines.append("Use these with sim/real-world separation and verify against the official chart.")
    return "\n".join(lines)


def _continuation_answer(question: str, lang: str, context: dict) -> str:
    clean = (question or "").strip().lower()
    if clean not in {"evet", "tamam", "olur", "devam", "aynen", "yes", "ok", "okay", "sure", "continue"}:
        return ""
    history = context.get("history") or []
    last_assistant = ""
    for item in reversed(history):
        if item.get("role") == "assistant":
            last_assistant = str(item.get("content", "")).lower()
            break
    if not last_assistant:
        return ""
    if any(marker in last_assistant for marker in ("üç şeyi söyle", "three things", "departure airport", "nereden kalkıyoruz")):
        if lang == "tr":
            return "Süper kaptan. O zaman kalkış meydanı, varış meydanı ve uçak tipini yaz; ben sana kısa ve düzgün bir uçuş planı çıkarayım."
        return "Perfect, captain. Send departure airport, arrival airport, and aircraft type; I will build a clean short flight plan."
    if any(marker in last_assistant for marker in ("chart", "briefing", "brifing")):
        if lang == "tr":
            return "Tamam kaptan. Seçili chart üzerinden ilerleyeyim: önce prosedür/pist, sonra frekanslar, profil, minimumlar ve pas geçmeyi sırayla ele alırız."
        return "Alright captain. I will continue from the selected chart: procedure/runway, frequencies, profile, minimums, then missed approach."
    return ""


def _topic_without_chart_answer(topic: str, lang: str) -> str:
    if lang == "tr":
        answers = {
            "frequencies": "Frekanslarda haberleşme ve navigasyon değerlerini karıştırmamak lazım: APP/TWR/ATIS konuşma içindir; VOR/NDB/LOC/DME ise uçağın navigasyon tarafını besler. Chart seçiliyse değerleri tek tek oradan okurum.",
            "holding": "Max holding speed normal yaklaşma hızı değildir; holding bölgesinde izin verilen üst hız limitidir. Chart seçiliyse fix ve hız limitini doğrudan ayırırım.",
            "descent": "APP/glide için genel mantık şu: frekans/course hazır, yaklaşma izni alınmış, localizer canlı veya yakalanmış, glide slope yukarıdan geliyor olmalı. Exact başlangıç noktası charttaki FAF/FAP, DME ve profil irtifasından çıkar.",
            "course": "Course değeri önemlidir; pist başıyla her zaman birebir aynı kabul edilmez. Autopilot ve navaid takibi için charttaki published course esas alınır.",
            "minimums": "Minimumlarda uçak kategorisi, DA/DH veya MDA/MDH, OCA/OCH ve RVR/VIS birlikte okunur. Tek rakam yetmez; kategori ve yaklaşma tipiyle beraber anlam kazanır.",
            "missed": "Pas geçme tek cümle gibi ezberlenmez: ilk tırmanış, dönüş yönü, hedef fix/holding ve irtifa kısıtı ayrı ayrı uygulanır.",
            "briefing": "Chart briefing kısa ve operasyonel olmalı: pist, yaklaşma tipi, frekanslar, profil, minimumlar ve pas geçme. Gereksiz metin değil, karar noktaları önemli.",
        }
        return answers.get(topic, "")

    answers = {
        "frequencies": "Keep communication and navigation values separate: APP/TWR/ATIS are for radio communication; VOR/NDB/LOC/DME feed navigation. With a selected chart, I can read them one by one.",
        "holding": "Max holding speed is not normal approach speed; it is the upper speed limit for the published holding pattern. With a selected chart, I can separate the fix and speed limit directly.",
        "descent": "For APP/glide capture: frequency/course set, approach clearance received, localizer alive or captured, and glide slope coming from above. The exact start point comes from FAF/FAP, DME, and profile altitude on the chart.",
        "course": "Course matters; runway heading and published course are not always identical. For navaid/autopilot tracking, use the published course on the chart.",
        "minimums": "For minimums, aircraft category, DA/DH or MDA/MDH, OCA/OCH, and RVR/VIS must be read together. One number alone is not enough.",
        "missed": "Missed approach is a command chain: initial climb, turn direction, target fix/holding, and altitude restriction.",
        "briefing": "A chart briefing should stay operational: runway, procedure type, frequencies, profile, minimums, and missed approach. Decision points matter more than long text.",
    }
    return answers.get(topic, "")


def _chart_answer(question: str, lang: str, context: dict, memory: dict, thought: Thought) -> str:
    topic = thought.topic or detect_topic(question) or "briefing"
    if not context.get("airport") and (context.get("chart") or "?") == "?":
        direct = _topic_without_chart_answer(topic, lang)
        if direct:
            return direct

    lines = [
        _tone_prefix(question, lang),
        _chart_line(context, lang),
        topic_answer(topic, lang),
    ]
    steps = _reasoning_steps(topic, lang)
    lines.extend(f"- {step}" for step in steps)
    return "\n\n".join(line for line in lines if line)


def _chart_line(context: dict, lang: str) -> str:
    airport = context.get("airport") or ""
    chart = context.get("chart") or "?"
    info = context.get("info") or {}
    awareness = " ".join(filter(None, [info.get("terrain", ""), info.get("approach", "")])).strip()

    if not airport and chart == "?":
        return ""

    if lang == "tr":
        base = f"Seçili bağlam: {airport}"
        if chart != "?":
            base += f" · IAC {chart}"
        if awareness:
            base += f"\nMeydan farkındalığı: {awareness}"
        return base

    base = f"Selected context: {airport}"
    if chart != "?":
        base += f" · IAC {chart}"
    if awareness:
        base += f"\nAirport awareness: {awareness}"
    return base


def _reasoning_steps(topic: str, lang: str) -> list[str]:
    if lang == "tr":
        steps = {
            "minimums": [
                "Önce yaklaşma tipini ve pist yönünü netleştiririm.",
                "Sonra kategori satırından DA/DH veya MDA/MDH değerini okurum.",
                "En sonda notlar, RVR/VIS ve missed approach bağlantısını kontrol ederim.",
            ],
            "missed": [
                "Missed kısmını tek cümle gibi değil, komut zinciri gibi okurum.",
                "İlk tırmanış, dönüş, fix/holding ve irtifa kısıtı ayrı ayrı yakalanmalı.",
                "Simde en iyi çalışma şekli: finalde stabilize bozup go-around senaryosu denemek.",
            ],
            "files": [
                "PDF/JPG yorumlamak için önce dosyadan metin veya görüntü almamız gerekir.",
                "Sonra chart üzerindeki başlık, plan view, profil ve minimumlar ayrı bölge gibi işlenir.",
                "Bu katmanı Python içinde parça parça kurabiliriz.",
            ],
            "frequencies": [
                "Önce bunun haberleşme frekansı mı navigasyon yardımcısı mı olduğunu ayırırım.",
                "APP/TWR/ATIS değerleri üst bilgi bloğundan; VOR/NDB/DME değerleri plan view üzerindeki etiketlerden okunur.",
                "Cevapta sadece ilgili frekansı veririm; gereksiz briefing basmam.",
            ],
            "holding": [
                "Holding için önce fix veya navaid adını, sonra varsa published hız limitini kontrol ederim.",
                "Azami holding speed ayrı bir operasyonel limit olduğu için minimumlardan bağımsız okunur.",
                "Chartta değer okunmuşsa doğrudan onu söylerim; okunmamışsa PDF üzerinde doğrulama isterim.",
            ],
            "descent": [
                "3° profil için FAF/FAP veya DME noktasını ve profil irtifasını beraber ararım.",
                "MAPt noktası ile alçalma başlangıcını karıştırmam; ikisini ayrı okurum.",
                "APP/glide yakalama sorusunda kullanıcıya karar noktası gibi anlatırım.",
            ],
            "course": [
                "Final course, published course ve missed approach track aynı şey değildir; ayrı ayrı kontrol ederim.",
                "Pist yönünden tahmin yapılabilir ama chartta published course varsa onu esas alırım.",
                "Cevabı kısa tutup sadece işe yarayan baş/track değerini öne çıkarırım.",
            ],
            "briefing": [
                "Briefing akışını meydan, pist, yaklaşma tipi, frekans/fix, profil, minimum ve missed olarak kurarım.",
                "Yeni başlayan kullanıcıda basit anlatırım; tecrübeli kullanıcıda tehdit ve karar noktalarına inerim.",
                "Ama gerçek uçuş için resmi ve güncel kaynak doğrulaması şarttır.",
            ],
        }
    else:
        steps = {
            "minimums": [
                "First I confirm the procedure type and runway.",
                "Then I read the category line and DA/DH or MDA/MDH.",
                "Finally I connect notes, RVR/VIS, and missed approach requirements.",
            ],
            "missed": [
                "I read missed approach as a command chain, not as one sentence.",
                "Initial climb, turn, fix/holding, and altitude restrictions should be separated.",
                "In the simulator, it is best practiced as a go-around scenario from final.",
            ],
            "files": [
                "For PDF/JPG reasoning, we first need to extract text or chart image regions.",
                "Then title, plan view, profile view, and minimums can be processed separately.",
                "We can build that layer step by step in Python.",
            ],
            "frequencies": [
                "First I separate communication frequencies from navigation-aid frequencies.",
                "APP/TWR/ATIS are read from the header; VOR/NDB/DME are read from plan-view labels.",
                "I answer only the requested frequency instead of dumping a full briefing.",
            ],
            "holding": [
                "For holding, I first look for the fix or navaid, then the published speed limit.",
                "Max holding speed is an operational limit and should be read separately from minimums.",
                "If the chart value is readable, I give it directly; otherwise I ask for visual verification.",
            ],
            "descent": [
                "For a 3° profile, I connect the FAF/FAP or DME point with the profile altitude.",
                "I keep MAPt separate from descent start; they are not the same thing.",
                "For APP/glide capture questions, I explain it like a decision point.",
            ],
            "course": [
                "Final course, published course, and missed-approach track are not the same value.",
                "Runway direction can help, but the published course on the chart wins.",
                "I keep the answer focused on the useful heading/track value.",
            ],
            "briefing": [
                "I structure the briefing around airport, runway, procedure type, frequencies/fixes, profile, minimums, and missed approach.",
                "For beginners I keep it simple; for advanced users I focus on threats and decision points.",
                "For real-world operations, current official sources must still be verified.",
            ],
        }
    return steps.get(topic, steps["briefing"])


def answer(question: str, lang: str, context: dict, memory: dict) -> str:
    lower = (question or "").lower()
    thought = think(question, lang, memory)
    if any(token in lower for token in ("kimsin", "sen nesin", "who are you", "what are you")):
        return _polish_answer(_identity_answer(lang), lang)

    if _is_self_disclosure(question):
        return _polish_answer(_learning_answer(question, lang), lang)

    continuation = _continuation_answer(question, lang, context)
    if continuation:
        return _polish_answer(continuation, lang)

    context_answer = _context_answer(question, lang, context)
    if context_answer:
        return _polish_answer(context_answer, lang)

    chart_data = _chart_data_answer(question, lang, context)
    if chart_data:
        return _polish_answer(chart_data, lang)

    daily_intent = detect_daily_intent(question)
    if daily_intent:
        return _polish_answer(daily_answer(daily_intent, lang, memory, question), lang)

    if is_greeting(question) or is_smalltalk(question):
        return _polish_answer(_smalltalk_answer(question, lang, memory), lang)

    if thought.mode == "chart":
        return _polish_answer(_chart_answer(question, lang, context, memory, thought), lang)

    return _polish_answer(_natural_answer(question, lang, memory, thought), lang)
