from pathlib import Path
import json
from datetime import datetime, timezone


TRAINING_DIR = Path(__file__).resolve().parent / "training_data"
PROFILE_PATH = Path(__file__).resolve().parent / "user_profile.local.json"
MEMORY_PATH = Path(__file__).resolve().parent / "ciguli_memory.local.json"


def load_training_notes(max_chars: int = 5000) -> str:
    chunks = []
    for path in sorted(TRAINING_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            chunks.append(f"## {path.name}\n{text}")
    joined = "\n\n".join(chunks)
    return joined[:max_chars]


def load_user_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {}
    try:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return profile if isinstance(profile, dict) else {}


def load_conversation_memory() -> dict:
    if not MEMORY_PATH.exists():
        return {"facts": {}, "turns": []}
    try:
        memory = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"facts": {}, "turns": []}
    if not isinstance(memory, dict):
        return {"facts": {}, "turns": []}
    memory.setdefault("facts", {})
    memory.setdefault("turns", [])
    return memory


def save_conversation_turn(user_text: str, assistant_text: str, lang: str) -> None:
    user_text = (user_text or "").strip()
    assistant_text = (assistant_text or "").strip()
    if not user_text:
        return

    memory = load_conversation_memory()
    facts = memory.setdefault("facts", {})
    turns = memory.setdefault("turns", [])

    _update_facts(facts, user_text, lang)
    turns.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "lang": lang,
        "user": user_text[:1200],
        "assistant": assistant_text[:1200],
    })
    memory["turns"] = turns[-80:]
    MEMORY_PATH.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_facts(facts: dict, user_text: str, lang: str) -> None:
    clean = user_text.lower()
    facts["preferred_language"] = lang

    if "msfs" in clean or "microsoft flight simulator" in clean:
        facts["simulator"] = "MSFS"
    elif "x-plane" in clean or "x plane" in clean or "xp12" in clean:
        facts["simulator"] = "X-Plane"
    elif "p3d" in clean or "prepar3d" in clean:
        facts["simulator"] = "Prepar3D"

    if any(word in clean for word in ("hacı", "haci", "kral", "reis", "hoca", "hocam", "abi")):
        facts["preferred_tone"] = "samimi"

    if any(word in clean for word in ("türkçe", "turkce", "tr konuş", "tr konus")):
        facts["preferred_language"] = "tr"
    elif any(word in clean for word in ("english", "ingilizce", "en konuş", "en konus")):
        facts["preferred_language"] = "en"

    if any(word in clean for word in ("yeniyim", "başlangıç", "beginner", "new pilot")):
        facts["skill_level"] = "beginner"
    elif any(word in clean for word in ("orta", "intermediate")):
        facts["skill_level"] = "intermediate"
    elif any(word in clean for word in ("ileri", "advanced", "pro")):
        facts["skill_level"] = "advanced"

    interests = set(facts.get("interests", []))
    for keyword in (
        "ifr", "vfr", "airliner", "boeing", "airbus", "ils", "rnav", "vor",
        "chart", "approach", "aircraft", "uçak", "ucak", "havacılık", "havacilik",
        "thy", "pegasus", "737", "a320", "a321", "a330", "a350",
    ):
        if keyword in clean:
            interests.add(keyword.upper() if keyword in {"ifr", "vfr", "ils", "rnav", "vor"} else keyword)
    if interests:
        facts["interests"] = sorted(interests)

    aircraft_markers = {
        "a320": "Airbus A320",
        "a321": "Airbus A321",
        "a330": "Airbus A330",
        "a350": "Airbus A350",
        "b737": "Boeing 737",
        "737": "Boeing 737",
        "b738": "Boeing 737-800",
        "777": "Boeing 777",
        "787": "Boeing 787",
        "cessna": "Cessna",
        "c172": "Cessna 172",
    }
    for marker, aircraft in aircraft_markers.items():
        if marker in clean:
            facts["aircraft"] = aircraft
            break

    for marker in ("adım ", "adim ", "benim adım ", "benim adim ", "my name is ", "call me "):
        if marker in clean:
            raw = user_text[clean.index(marker) + len(marker):].strip()
            name = raw.split()[0].strip(".,!?:;")
            if 1 < len(name) < 32:
                facts["display_name"] = name
            break

    if any(marker in clean for marker in ("seviyorum", "severim", "ilgimi çekiyor", "ilgimi cekiyor", "i like", "i love")):
        facts["likes_detected"] = True
