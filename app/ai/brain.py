from __future__ import annotations

from dataclasses import dataclass

from app.ai.daily_talk import detect_daily_intent
from app.ai.knowledge import detect_topic
from app.ai.language import is_greeting, is_smalltalk, normalize_language
from app.ai.vocabulary import known_words_in_text


@dataclass
class Thought:
    lang: str
    mode: str
    intent: str
    topic: str | None
    confidence: float
    tone: str
    signals: list[str]
    known_terms: list[str]


CHART_MARKERS = {
    "chart", "harita", "approach", "yaklaşma", "yaklasma", "ils", "rnav", "vor",
    "minimum", "minimums", "missed", "pas geç", "pas gec", "brifing", "briefing",
    "pist", "runway", "fix", "dme", "ndb", "localizer", "glide", "profile",
    "tırmanış", "tirmanis", "climb", "pdf", "jpg", "dosya", "görsel", "gorsel",
    "holding", "hold", "course", "heading", "track", "frekans", "frequency",
    "atis", "twr", "kule", "rakım", "rakim", "elev", "transition",
}

CHART_ACTION_MARKERS = {
    "oku", "açıkla", "acikla", "anlat", "çıkar", "cikar", "ayır", "ayir",
    "analiz", "analysis", "analyze", "incele", "bak", "göster", "goster",
    "üstünden geç", "ustunden gec", "üzerinden geç", "uzerinden gec",
    "brief", "briefing", "brifing", "go over", "walk me through", "explain",
    "read", "separate", "check", "show", "minimum", "minimums", "missed",
    "pas geç", "pas gec", "pdf", "jpg", "dosya", "file",
}

AVIATION_MARKERS = {
    "uçak", "ucak", "uçuş", "ucus", "pilot", "kokpit", "sim", "msfs", "x-plane",
    "xplane", "vatsim", "ivao", "airbus", "boeing", "flap", "gear", "autopilot",
    "fmc", "mcdu", "airport", "flight", "aircraft", "cockpit", "simulator",
    "iniş", "inis", "landing", "kalkış", "kalkis", "takeoff", "hız", "hiz",
    "speed", "app", "localizer", "glide", "ils",
}

QUESTION_MARKERS_TR = ("ne", "nasıl", "nasil", "neden", "niye", "kaç", "kac", "mi", "mı", "mu", "mü", "anlat", "açıkla", "acikla")
QUESTION_MARKERS_EN = ("what", "how", "why", "can", "could", "explain", "tell", "show")


def think(question: str, lang: str, memory: dict) -> Thought:
    text = (question or "").strip()
    detected_lang = normalize_language(lang, text)
    clean = text.lower()
    known_terms = known_words_in_text(text, detected_lang)[:12]
    signals: list[str] = []

    daily_intent = detect_daily_intent(text)
    if daily_intent:
        signals.append(f"daily:{daily_intent}")

    chart_score = sum(1 for marker in CHART_MARKERS if marker in clean)
    aviation_score = sum(1 for marker in AVIATION_MARKERS if marker in clean)
    chart_action_score = sum(1 for marker in CHART_ACTION_MARKERS if marker in clean)
    if chart_score:
        signals.append(f"chart_score:{chart_score}")
    if chart_action_score:
        signals.append(f"chart_action:{chart_action_score}")
    if aviation_score:
        signals.append(f"aviation_score:{aviation_score}")

    is_question = _looks_like_question(clean, detected_lang)
    if is_question:
        signals.append("question")
    if is_greeting(text):
        signals.append("greeting")
    if is_smalltalk(text):
        signals.append("smalltalk")

    topic = detect_topic(text)
    if daily_intent:
        return Thought(detected_lang, "daily", daily_intent, None, 0.92, "natural", signals, known_terms)
    if chart_score and (chart_action_score or is_question or (topic in {"minimums", "missed", "files"})):
        return Thought(detected_lang, "chart", topic or "briefing", topic or "briefing", min(0.95, 0.55 + chart_score * 0.12), "briefing", signals, known_terms)
    if aviation_score:
        return Thought(detected_lang, "aviation", "aviation_chat", topic, min(0.9, 0.5 + aviation_score * 0.12), "aviation", signals, known_terms)
    if is_question:
        return Thought(detected_lang, "general_question", "general_question", None, 0.66, "natural", signals, known_terms)
    if len(clean) <= 80:
        return Thought(detected_lang, "casual", "casual_chat", None, 0.7, "natural", signals, known_terms)
    return Thought(detected_lang, "general", "general", None, 0.62, "natural", signals, known_terms)


def _looks_like_question(clean: str, lang: str) -> bool:
    if "?" in clean:
        return True
    markers = QUESTION_MARKERS_EN if lang == "en" else QUESTION_MARKERS_TR
    words = {word.strip(".,!?:;()[]{}\"'").lower() for word in clean.split()}
    return bool(words & set(markers))
