TR_MARKERS = {
    "merhaba", "selam", "nasıl", "nasil", "nedir", "ne", "şu", "su", "bana",
    "anlat", "yardım", "yardim", "minimum", "pas", "geçme", "gecme",
    "yaklaşma", "yaklasma", "pist", "meydan", "chart", "harita", "uçak", "ucak",
    "abi", "aga", "hacı", "haci", "hoca", "hocam", "reis", "kral", "eyvallah",
    "aleyküm", "aleykum", "sağol", "sagol", "muhabbet", "takılalım", "takilalim",
    "kafam", "karıştı", "karisti", "üstünden", "ustunden", "geç", "gec",
}

EN_MARKERS = {
    "hello", "hi", "what", "how", "explain", "brief", "briefing", "minimums",
    "missed", "approach", "runway", "airport", "chart", "aircraft", "aviation",
    "thanks", "thank", "you", "talk", "chat", "confused", "sort", "figure",
    "phrasal", "verb", "captain", "frequency", "cockpit",
}


def normalize_language(lang: str | None, text: str = "") -> str:
    preferred = "en" if lang == "en" else "tr"
    words = {word.strip(".,!?:;()[]{}\"'").lower() for word in (text or "").split()}
    tr_score = len(words & TR_MARKERS)
    en_score = len(words & EN_MARKERS)
    if tr_score > en_score:
        return "tr"
    if en_score > tr_score:
        return "en"
    return preferred


def is_greeting(text: str) -> bool:
    clean = (text or "").strip().lower()
    words = {word.strip(".,!?:;()[]{}\"'").lower() for word in clean.split()}
    if words & {"sa", "s.a", "selam", "merhaba", "hello", "hi", "hey"}:
        return True
    return any(token in clean for token in ("selamın aleyküm", "selamin aleykum", "good morning", "good evening"))


def is_smalltalk(text: str) -> bool:
    clean = (text or "").strip().lower()
    markers = (
        "nasılsın", "naber", "ne yapıyorsun", "how are you", "what's up",
        "sohbet", "konuş", "talk", "chat",
    )
    return any(marker in clean for marker in markers)
