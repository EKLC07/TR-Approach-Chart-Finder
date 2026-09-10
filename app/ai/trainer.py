from __future__ import annotations

import json
import re
from pathlib import Path

from app.ai.language import normalize_language
from app.ai.vocabulary import vocabulary_status


TRAINING_DIR = Path(__file__).resolve().parent / "training_data"

TEXT_TARGETS = {
    "vocabulary": {
        "tr": "vocabulary_tr.txt",
        "en": "vocabulary_en.txt",
    },
    "daily": {
        "tr": "daily_talk_tr.md",
        "en": "daily_talk_en.md",
    },
    "aviation": {
        "tr": "aviation_notes_tr.md",
        "en": "aviation_notes_en.md",
    },
    "conversation": {
        "tr": "conversation_examples.md",
        "en": "conversation_examples.md",
    },
    "chart_rules": {
        "tr": "chart_reading_rules.md",
        "en": "chart_reading_rules.md",
    },
}


def training_overview() -> dict:
    files = []
    for path in sorted(TRAINING_DIR.glob("*")):
        if path.is_file():
            files.append({
                "name": path.name,
                "size": path.stat().st_size,
                "path": str(path),
            })
    return {
        "trainingDir": str(TRAINING_DIR),
        "vocabulary": vocabulary_status(),
        "files": files,
        "acceptedKinds": sorted([*TEXT_TARGETS, "phrase"]),
    }


def add_training_item(kind: str, lang: str, text: str, intent: str = "") -> dict:
    kind = (kind or "").strip().lower()
    text = (text or "").strip()
    lang = normalize_language(lang, text) if lang == "auto" else ("en" if lang == "en" else "tr")
    intent = (intent or "").strip().lower()

    if not text:
        raise ValueError("Training text cannot be empty.")
    if kind not in TEXT_TARGETS and kind != "phrase":
        raise ValueError("Unsupported training kind.")

    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    if kind == "phrase":
        path = TRAINING_DIR / f"phrase_bank_{lang}.json"
        _add_phrase(path, intent or "casual_chat", text)
    else:
        path = TRAINING_DIR / TEXT_TARGETS[kind][lang]
        _append_unique_line(path, text)
        if kind in {"vocabulary", "daily"} and intent:
            _add_phrase(TRAINING_DIR / f"intent_patterns_{lang}.json", intent, text)

    return {
        "saved": True,
        "kind": kind,
        "lang": lang,
        "intent": intent,
        "file": str(path),
        "overview": training_overview(),
    }


def train_from_chat(message: str, lang: str = "auto") -> dict:
    message = (message or "").strip()
    if not message:
        raise ValueError("Training message cannot be empty.")

    detected_lang = normalize_language(lang, message) if lang == "auto" else ("en" if lang == "en" else "tr")
    intent = _infer_intent(message)
    kind = _infer_kind(message, intent)
    training_text = _extract_training_text(message)
    if kind == "vocabulary":
        intent = ""

    saved = add_training_item(kind, detected_lang, training_text, intent)
    saved["trainerReply"] = _trainer_reply(kind, detected_lang, training_text, intent)
    saved["sourceMessage"] = message
    return saved


def _append_unique_line(path: Path, text: str) -> None:
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    normalized_lines = {line.strip().lower() for line in existing.splitlines()}
    if text.lower() in normalized_lines:
        return
    with path.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(text + "\n")


def _add_phrase(path: Path, intent: str, text: str) -> None:
    data = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except json.JSONDecodeError:
            data = {}

    phrases = data.setdefault(intent, [])
    if text not in phrases:
        phrases.append(text)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _infer_intent(text: str) -> str:
    clean = text.lower()
    intent_markers = {
        "greeting": [
            "selam", "merhaba", "aleyküm", "aleykum", "günaydın", "gunaydin",
            "hello", "hi ", "hey", "good morning", "good evening",
        ],
        "casual_chat": [
            "muhabbet", "sohbet", "takıl", "takil", "havadan sudan", "lafla",
            "casual", "small talk", "hang out", "chill", "talk for a bit",
        ],
        "confused": [
            "anlamadım", "anlamadim", "kafam karıştı", "kafam karisti", "çözemedim", "cozemedim",
            "confused", "don't get", "dont get", "sort out", "figure out", "break down",
        ],
        "thanks": [
            "teşekkür", "tesekkur", "sağ ol", "sag ol", "eyvallah", "eline sağlık", "eline saglik",
            "thanks", "thank you", "appreciate",
        ],
        "motivation": [
            "gaz ver", "motivasyon", "moral", "hevesim", "toparla",
            "motivate", "hype", "push me", "keep going",
        ],
        "briefing": [
            "briefing", "brifing", "brief", "chartı oku", "chart oku", "üstünden geç", "ustunden gec",
            "walk me through", "go over the chart",
        ],
        "minimums": [
            "minimum", "minimumlar", "da/dh", "mda", "rvr", "visibility", "görüş", "gorus",
        ],
        "missed": [
            "missed", "pas geç", "pas gec", "go-around", "go around", "holding",
        ],
    }
    explicit = {
        "greeting": ["greeting", "selamlaşma", "selamlasma"],
        "casual_chat": ["casual_chat", "muhabbet"],
        "confused": ["confused", "anlamadı", "anlamadi"],
        "thanks": ["thanks", "teşekkür", "tesekkur"],
        "motivation": ["motivation", "motivasyon"],
        "briefing": ["briefing", "brifing"],
        "minimums": ["minimums", "minimumlar"],
        "missed": ["missed", "pas geçme", "pas gecme"],
    }
    for intent, markers in explicit.items():
        if any(marker in clean for marker in markers):
            return intent
    for intent, markers in intent_markers.items():
        if any(marker in clean for marker in markers):
            return intent
    return ""


def _infer_kind(text: str, intent: str) -> str:
    clean = text.lower()
    if any(marker in clean for marker in ("kelime", "dağarc", "dagarc", "vocabulary", "phrasal", "deyim", "kalıp", "kalip")):
        return "vocabulary"
    if any(marker in clean for marker in ("cevap", "yanıt", "yanit", "reply", "answer", "böyle desin", "boyle desin")):
        return "phrase"
    if intent in {"greeting", "casual_chat", "confused", "thanks", "motivation"}:
        return "daily"
    if intent in {"briefing", "minimums", "missed"}:
        return "chart_rules"
    if any(marker in clean for marker in ("havacılık", "havacilik", "aviation", "uçak", "ucak", "pilot", "simülasyon", "simulation")):
        return "aviation"
    return "conversation"


def _extract_training_text(text: str) -> str:
    stripped = text.strip()
    quoted = re.findall(r"[\"'“‘](.*?)[\"'”’]", stripped)
    if quoted:
        return max((item.strip() for item in quoted), key=len)

    patterns = [
        r"(?:ciguli,?\s*)?(.+?)\s+(?:cümlesini|cumlesini|ifadesini|kalıbını|kalibini|phrasal verbini)\b",
        r"(?:ciguli,?\s*)?(.+?)\s+(?:olarak öğren|olarak ogren|diye öğren|diye ogren)\b",
        r"(?:ciguli,?\s*)?(.+?)\s+(?:kelime dağarcığına|kelime dagarcigina|vocabulary bank)",
    ]
    for pattern in patterns:
        match = re.search(pattern, stripped, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,:;")
            candidate = re.sub(r"^ciguli,?\s*", "", candidate, flags=re.IGNORECASE).strip(" .,:;")
            if len(candidate) >= 2:
                return candidate

    separators = [":", "->", "=>", " öğren ", " ogren ", " ekle ", " add ", " learn "]
    for separator in separators:
        if separator in stripped:
            candidate = stripped.split(separator)[-1].strip(" .:-")
            if len(candidate) >= 2:
                return candidate
    return stripped


def _trainer_reply(kind: str, lang: str, text: str, intent: str) -> str:
    if lang == "tr":
        target = {
            "vocabulary": "kelime/ifade dağarcığına",
            "phrase": "cevap kalıbına",
            "daily": "günlük konuşma algısına",
            "aviation": "havacılık notlarına",
            "conversation": "konuşma örneklerine",
            "chart_rules": "chart okuma kurallarına",
        }.get(kind, "eğitim havuzuna")
        intent_part = f" Intent: {intent}." if intent else ""
        return f"Tamam kaptan, bunu Ciguli'nin {target} işledim.{intent_part}\nÖğrenilen metin: {text}"

    target = {
        "vocabulary": "vocabulary bank",
        "phrase": "reply phrase bank",
        "daily": "daily conversation detector",
        "aviation": "aviation notes",
        "conversation": "conversation examples",
        "chart_rules": "chart-reading rules",
    }.get(kind, "training pool")
    intent_part = f" Intent: {intent}." if intent else ""
    return f"Done captain, I saved this into Ciguli's {target}.{intent_part}\nLearned text: {text}"
