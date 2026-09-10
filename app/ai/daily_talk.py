import json
import re
from pathlib import Path


TRAINING_DIR = Path(__file__).resolve().parent / "training_data"


DAILY_INTENTS = {
    "greeting": {
        "tr": [
            "selam", "merhaba", "sa", "s.a", "selamın aleyküm", "selamin aleykum",
            "selamun aleykum", "selamün aleyküm", "aleykümselam", "aleykum selam",
            "aleyküm selam", "günaydın", "gunaydin", "iyi akşamlar", "iyi aksamlar",
        ],
        "en": ["hello", "hi", "hey", "good morning", "good evening"],
    },
    "how_are_you": {
        "tr": ["nasılsın", "nasilsin", "naber", "ne haber", "napıyorsun", "napiyorsun", "ne yapıyorsun", "iyi misin"],
        "en": ["how are you", "what's up", "whats up", "how is it going", "you good", "what are you doing"],
    },
    "thanks": {
        "tr": ["teşekkür", "tesekkur", "sağ ol", "sag ol", "sağolasın", "sagolasin", "eyvallah", "eline sağlık", "eline saglik", "adamsın", "adamsin", "kralsın", "kralsin"],
        "en": ["thanks", "thank you", "appreciate it", "cheers", "nice one", "good catch"],
    },
    "bye": {
        "tr": ["görüşürüz", "gorusuruz", "bay bay", "bye", "kendine iyi bak", "çıkıyorum", "cikiyorum", "kaçtım", "kactim", "kaçıyorum", "kaciyorum", "ben kaçtım", "hadi eyvallah", "iyi geceler", "sağlıcakla", "saglicakla"],
        "en": ["bye", "see you", "see ya", "take care", "good night", "later", "catch you later", "i am off", "gotta go"],
    },
    "flight_request": {
        "tr": ["uçuş yapalım", "ucus yapalim", "uçalım", "ucalim", "uçuş atalım", "ucus atalim", "rota yapalım", "rota yapalim", "bir uçuş yapayım", "bir ucus yapayim", "uçuş planlayalım", "ucus planlayalim"],
        "en": ["let's fly", "lets fly", "fly together", "do a flight", "plan a flight", "let's plan a flight", "lets plan a flight"],
    },
    "bored": {
        "tr": ["canım sıkıldı", "canim sikildi", "sıkıldım", "sikildim", "moralim bozuk"],
        "en": ["i am bored", "i'm bored", "feeling bored", "bad mood"],
    },
    "motivation": {
        "tr": ["motivasyon", "gaz ver", "hevesim kaçtı", "hevesim kacti"],
        "en": ["motivate me", "motivation", "hype me up"],
    },
    "casual_chat": {
        "tr": ["ne yapalım", "ne yapalim", "bugün ne yapalım", "bugun ne yapalim", "takılalım", "takilalim", "laflayalım", "laflayalim", "boş yapalım", "bos yapalim", "muhabbet edelim", "hacı", "haci", "hoca", "reis", "kral"],
        "en": ["hang out", "chill", "let's talk", "lets talk", "small talk", "what is going on", "what's going on"],
    },
    "confused": {
        "tr": ["anlamadım", "kafam karıştı", "karışık geldi", "çözemedim", "cozemedim"],
        "en": ["i don't get it", "i dont get it", "i am confused", "i'm confused", "figure it out", "sort it out"],
    },
    "agreement": {
        "tr": ["evet", "aynen", "tamam", "olur", "devam", "hadi", "başlayalım", "baslayalim"],
        "en": ["yes", "yeah", "yep", "okay", "ok", "sure", "continue", "go on", "let's start", "lets start"],
    },
    "disagreement": {
        "tr": ["hayır", "hayir", "yok", "olmadı", "olmadi", "değil", "degil", "istemiyorum"],
        "en": ["no", "nope", "not really", "not that", "i don't want", "i dont want"],
    },
}


def _intent_patterns(lang: str) -> dict:
    suffix = "en" if lang == "en" else "tr"
    path = TRAINING_DIR / f"intent_patterns_{suffix}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _phrase_bank(lang: str) -> dict:
    suffix = "en" if lang == "en" else "tr"
    path = TRAINING_DIR / f"phrase_bank_{suffix}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _pick_variant(intent: str, lang: str, memory: dict) -> str | None:
    if intent in {"greeting", "bye", "thanks", "how_are_you", "flight_request", "casual_chat", "confused", "motivation", "agreement", "disagreement"}:
        return None
    bank = _phrase_bank(lang)
    phrases = bank.get(intent) or []
    if not phrases:
        return None
    turns = memory.get("turns", []) if isinstance(memory, dict) else []
    facts = memory.get("facts", {}) if isinstance(memory, dict) else {}
    index_seed = len(turns) + len(str(facts.get("simulator", ""))) + len(str(facts.get("skill_level", "")))
    phrase = phrases[index_seed % len(phrases)]
    return phrase.replace("ciguli", "Ciguli")


def _contextual_greeting(question: str, lang: str, prefix: str) -> str:
    clean = (question or "").strip().lower()

    if lang == "tr":
        islamic_openers = (
            "selamın aleyküm", "selamin aleykum", "selamun aleykum", "selamün aleyküm",
            "s.a", "sa",
        )
        islamic_replies = ("aleykümselam", "aleyküm selam", "aleykum selam", "as")
        if any(item == clean or clean.startswith(item + " ") for item in islamic_openers):
            return f"{prefix}aleyküm selam kaptan. Ciguli hatta, frekans temiz."
        if any(item in clean for item in islamic_replies):
            return f"{prefix}hoş geldin kaptan. Frekans açık, ben buradayım."
        if "günaydın" in clean or "gunaydin" in clean:
            return f"{prefix}günaydın kaptan. Kokpit sakin, güne başlayabiliriz."
        if "iyi akşamlar" in clean or "iyi aksamlar" in clean:
            return f"{prefix}iyi akşamlar kaptan. Frekans açık, neye bakıyoruz?"
        if "merhaba" in clean:
            return f"{prefix}merhaba kaptan. Ciguli burada, nasıl yardımcı olayım?"
        return f"{prefix}selam kaptan. Ciguli hatta, ne yapıyoruz?"

    if "good morning" in clean:
        return f"{prefix}good morning, captain. Ciguli is on frequency."
    if "good evening" in clean:
        return f"{prefix}good evening, captain. Frequency is open."
    if clean in {"hi", "hello", "hey"} or clean.startswith(("hi ", "hello ", "hey ")):
        return f"{prefix}hello captain. Ciguli is here; what are we doing today?"
    return f"{prefix}hello captain. Ciguli is on frequency."


def _contextual_bye(question: str, lang: str, prefix: str) -> str:
    clean = (question or "").strip().lower()
    if lang == "tr":
        if "iyi geceler" in clean:
            return f"{prefix}iyi geceler kaptan. Frekansı kapatıyorum; yarın yine buradayım."
        if "kendine iyi bak" in clean or "sağlıcakla" in clean or "saglicakla" in clean:
            return f"{prefix}sen de kendine iyi bak kaptan. Bir sonraki uçuşta görüşürüz."
        if "hadi eyvallah" in clean or "eyv" in clean:
            return f"{prefix}eyvallah kaptan. Frekans kapanıyor, iyi uçuşlar."
        if "kaçtım" in clean or "kactim" in clean or "kaçıyorum" in clean or "kaciyorum" in clean:
            return f"{prefix}tamam kaptan, seni tutmayayım. Görüşürüz."
        return f"{prefix}görüşürüz kaptan. Ciguli sağ koltukta bekler."

    if "good night" in clean:
        return f"{prefix}good night, captain. Frequency closing; I will be here next time."
    if "take care" in clean:
        return f"{prefix}you too, captain. Take care and see you on the next flight."
    if "later" in clean or "see ya" in clean:
        return f"{prefix}see ya, captain. Good flights."
    return f"{prefix}see you, captain. Ciguli will stay in the right seat."


def _contextual_thanks(question: str, lang: str, prefix: str) -> str:
    clean = (question or "").strip().lower()
    if lang == "tr":
        if "eyvallah" in clean:
            return f"{prefix}eyvallah kaptan, her zaman."
        if "eline sağlık" in clean or "eline saglik" in clean:
            return f"{prefix}sağ ol kaptan, işimiz kokpiti temiz tutmak."
        if "adamsın" in clean or "adamsin" in clean or "kralsın" in clean or "kralsin" in clean:
            return f"{prefix}var ol kaptan. Beraber daha iyisini kurarız."
        return f"{prefix}rica ederim kaptan, ne zaman istersen buradayım."

    if "cheers" in clean:
        return f"{prefix}cheers, captain. Anytime."
    if "appreciate" in clean:
        return f"{prefix}I appreciate that, captain. Always here to help."
    return f"{prefix}you are welcome, captain. Right seat is ready."


def _contextual_how_are_you(question: str, lang: str, prefix: str) -> str:
    clean = (question or "").strip().lower()
    if lang == "tr":
        if "naber" in clean or "ne haber" in clean:
            return f"{prefix}iyidir kaptan, frekans açık. Sende ne var ne yok?"
        if "ne yapıyorsun" in clean or "napıyorsun" in clean or "napiyorsun" in clean:
            return f"{prefix}buradayım kaptan, paneli izliyorum. İstersen muhabbet, istersen uçuş planı yaparız."
        return f"{prefix}iyiyim kaptan. Kokpit sakin, mod iyi. Sen nasılsın?"

    if "what are you doing" in clean:
        return f"{prefix}I am here, captain, watching the panel. We can chat or plan a flight."
    if "what's up" in clean or "whats up" in clean:
        return f"{prefix}all good, captain. Frequency is open. What is up with you?"
    return f"{prefix}I am good, captain. Cockpit is calm. How are you?"


def _contextual_flight_request(question: str, lang: str, prefix: str, memory: dict) -> str:
    facts = memory.get("facts", {}) if isinstance(memory, dict) else {}
    sim = facts.get("simulator", "")
    if lang == "tr":
        sim_line = f" {sim} tarafına göre düşünürüz." if sim else ""
        return (
            f"{prefix}yapalım kaptan, güzel fikir.{sim_line}\n\n"
            "Bana üç şeyi söyle, sana düzgün bir mini uçuş çıkarayım:\n"
            "- Nereden kalkıyoruz?\n"
            "- Nereye iniyoruz?\n"
            "- Uçak ne olsun?\n\n"
            "İstersen ben de öneririm: kısa IFR, sakin VFR turu ya da zorlu yaklaşma senaryosu."
        )

    sim_line = f" We can tune it for {sim}." if sim else ""
    return (
        f"{prefix}let's do it, captain.{sim_line}\n\n"
        "Give me three things and I will build a clean mini flight:\n"
        "- Departure airport\n"
        "- Arrival airport\n"
        "- Aircraft\n\n"
        "Or I can suggest one: short IFR, relaxed VFR tour, or a challenging approach scenario."
    )


def detect_daily_intent(text: str) -> str | None:
    clean = (text or "").lower()
    compact_words = clean.replace("?", " ").replace("!", " ").split()
    priority = [
        "confused",
        "flight_request",
        "how_are_you",
        "bye",
        "thanks",
        "bored",
        "motivation",
        "disagreement",
        "greeting",
        "agreement",
        "casual_chat",
    ]
    for lang in ("tr", "en"):
        learned = _intent_patterns(lang)
        ordered_intents = [intent for intent in priority if intent in learned]
        ordered_intents.extend(intent for intent in learned if intent not in ordered_intents)
        for intent in ordered_intents:
            if intent in {"agreement", "disagreement"} and len(compact_words) > 4:
                continue
            phrases = learned.get(intent) or []
            if any(_phrase_matches(str(phrase).lower(), clean) for phrase in phrases):
                return intent
    for intent in priority:
        if intent in {"agreement", "disagreement"} and len(compact_words) > 4:
            continue
        languages = DAILY_INTENTS.get(intent, {})
        for phrases in languages.values():
            if any(_phrase_matches(phrase, clean) for phrase in phrases):
                return intent
    return None


def _phrase_matches(phrase: str, clean: str) -> bool:
    phrase = (phrase or "").strip().lower()
    if not phrase:
        return False
    compact = phrase.replace(".", "")
    if len(compact) <= 3 and compact.isalpha():
        return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", clean))
    return phrase in clean


def daily_answer(intent: str, lang: str, memory: dict, question: str = "") -> str:
    facts = memory.get("facts", {}) if isinstance(memory, dict) else {}
    name = facts.get("display_name", "")
    sim = facts.get("simulator", "")
    level = facts.get("skill_level", "")
    variant = _pick_variant(intent, lang, memory)

    if lang == "tr":
        prefix = f"{name}, " if name else ""
        answers = {
            "greeting": _contextual_greeting(question, lang, prefix),
            "how_are_you": _contextual_how_are_you(question, lang, prefix),
            "thanks": _contextual_thanks(question, lang, prefix),
            "bye": _contextual_bye(question, lang, prefix),
            "flight_request": _contextual_flight_request(question, lang, prefix, memory),
            "bored": f"{prefix}o zaman ufak bir görev atalım: sevdiğin bir meydanı seç, birlikte 3 dakikalık mini IFR brifing çıkaralım.",
            "motivation": f"{prefix}bu iş yürür kaptan. Küçük küçük kuracağız; bugün panel, yarın hafıza, sonra premium kokpit hissi. Pist bizde.",
            "agreement": f"{prefix}tamam kaptan, devam. Konuyu bozmayayım; neyin üstünden gidiyorsak oradan sürdürüyorum.",
            "disagreement": f"{prefix}tamam kaptan, o yolu kapatıyorum. Ne istemediğini aldım; şimdi daha doğru tarafa çevirelim.",
            "casual_chat": f"{prefix}olur kaptan, biraz muhabbet döndürelim. İstersen havacılıktan gireriz, istersen tamamen gündelik takılırız.",
            "confused": f"{prefix}sorun yok, burayı beraber sadeleştirelim. Önce nerede takıldığını bulalım, sonra adım adım açarım.",
        }
        if variant:
            answers[intent] = f"{prefix}{variant}"
        if intent not in answers:
            return f"{prefix}anladım kaptan. Bunu doğal muhabbet olarak aldım; devam edebiliriz."
        extra = []
        if sim:
            extra.append(f"{sim} tarafına göre konuşurum")
        if level:
            extra.append(f"seviyeni {level} kabul ederim")
        if extra and intent in {"bored", "motivation"}:
            return answers[intent] + "\n\n" + "Ayrıca seni hatırlıyorum: " + ", ".join(extra) + "."
        return answers[intent]

    prefix = f"{name}, " if name else ""
    answers = {
        "greeting": _contextual_greeting(question, lang, prefix),
        "how_are_you": _contextual_how_are_you(question, lang, prefix),
        "thanks": _contextual_thanks(question, lang, prefix),
        "bye": _contextual_bye(question, lang, prefix),
        "flight_request": _contextual_flight_request(question, lang, prefix, memory),
        "bored": f"{prefix}let's make it useful: pick an airport you like and we can build a three-minute IFR mini briefing.",
        "motivation": f"{prefix}this can absolutely grow. Small steps: panel, memory, premium cockpit feel, then deeper chart intelligence. Runway is ours.",
        "agreement": f"{prefix}okay captain, continuing. I will keep the current thread and move it forward.",
        "disagreement": f"{prefix}got it, captain. I am closing that path and adjusting course.",
        "casual_chat": f"{prefix}sure, we can hang out for a bit. We can keep it casual or drift into aviation whenever you want.",
        "confused": f"{prefix}no worries, let's sort it out. Tell me which part feels messy and I will break it down cleanly.",
    }
    if variant:
        answers[intent] = f"{prefix}{variant}"
    if intent not in answers:
        return f"{prefix}got it, captain. I am taking this as natural conversation; we can continue."
    extra = []
    if sim:
        extra.append(f"you fly {sim}")
    if level:
        extra.append(f"I should treat your level as {level}")
    if extra and intent in {"bored", "motivation"}:
        return answers[intent] + "\n\n" + "I also remember: " + ", ".join(extra) + "."
    return answers[intent]
