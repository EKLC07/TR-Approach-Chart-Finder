from app.ai.ciguli_core import answer as ciguli_answer
from app.ai.language import normalize_language
from app.ai.memory import load_conversation_memory, load_training_notes, load_user_profile, save_conversation_turn
from app.ai.vocabulary import vocabulary_status
from app.data.airports import find_airport
from app.services.airport_info import airport_info
from app.services.chart_analysis import analyze_chart


PRODUCT_NAME = "Approvaq"
ASSISTANT_NAME = "Ciguli"


def _chart_context(file_name: str, lang: str, airport_override: str = "") -> dict:
    parts = (file_name or "").split("_")
    airport = (airport_override or "").upper()
    if not airport:
        airport = parts[3] if len(parts) > 3 else ""
    chart = file_name.split("IAC_")[-1].split("_")[0].split(".")[0] if "IAC_" in file_name else "?"
    info = airport_info(airport, lang) or {}
    return {"airport": airport, "chart": chart, "info": info, "airport_meta": find_airport(airport) or {}}


def _clean_history(history: list | None) -> list[dict]:
    clean = []
    for item in (history or [])[-8:]:
        if not isinstance(item, dict):
            continue
        role = "assistant" if item.get("role") == "ai" else "user"
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        clean.append({"role": role, "content": text[:1200]})
    return clean


def assist(file_name: str, question: str = "", lang: str = "en", airport: str = "", history: list | None = None) -> dict:
    question = (question or "").strip()
    lang = normalize_language(lang, question)
    context = _chart_context(file_name, lang, airport)
    context["history"] = _clean_history(history)
    if file_name:
        try:
            context["analysis"] = analyze_chart(file_name, airport, lang)
        except Exception:
            context["analysis"] = {}
    memory = load_conversation_memory()
    local_answer = ciguli_answer(question, lang, context, memory)
    save_conversation_turn(question, local_answer, lang)
    return {
        "answer": local_answer,
        "language": lang,
        "mode": "ciguli-brain",
        "suggestions": [],
        "mood": "local-aviation-companion",
        "extractedTextPreview": "",
    }


def capabilities() -> dict:
    return {
        "name": PRODUCT_NAME,
        "assistantName": ASSISTANT_NAME,
        "onlineRequired": False,
        "onlineModelConfigured": False,
        "localModelConfigured": True,
        "aiMode": "ciguli-brain",
        "userProfile": load_user_profile(),
        "conversationMemory": load_conversation_memory(),
        "languages": ["tr", "en"],
        "currentFileReading": "Selected DHMI PDF context through file name and airport metadata.",
        "plannedFileReading": ["PDF text extraction", "JPG/PNG OCR", "vision model chart interpretation"],
        "trainingDataFolder": str((__import__("pathlib").Path(__file__).resolve().parent / "training_data")),
        "trainingNotesPreview": load_training_notes(1200),
        "vocabulary": vocabulary_status(),
    }
