from pathlib import Path


TRAINING_DIR = Path(__file__).resolve().parent / "training_data"
TARGET_WORDS_PER_LANGUAGE = 16000


def _word_file(lang: str) -> Path:
    suffix = "en" if lang == "en" else "tr"
    return TRAINING_DIR / f"vocabulary_{suffix}.txt"


def load_vocabulary(lang: str) -> set[str]:
    path = _word_file(lang)
    if not path.exists():
        return set()
    words = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip().lower()
        if clean and not clean.startswith("#"):
            words.add(clean)
    return words


def vocabulary_status() -> dict:
    tr_words = load_vocabulary("tr")
    en_words = load_vocabulary("en")
    return {
        "targetPerLanguage": TARGET_WORDS_PER_LANGUAGE,
        "turkishWords": len(tr_words),
        "englishWords": len(en_words),
        "turkishRemaining": max(0, TARGET_WORDS_PER_LANGUAGE - len(tr_words)),
        "englishRemaining": max(0, TARGET_WORDS_PER_LANGUAGE - len(en_words)),
        "files": {
            "tr": str(_word_file("tr")),
            "en": str(_word_file("en")),
        },
    }


def known_words_in_text(text: str, lang: str) -> list[str]:
    vocabulary = load_vocabulary(lang)
    found = []
    clean_text = (text or "").lower()
    for expression in vocabulary:
        if " " in expression and expression in clean_text:
            found.append(expression)
    for raw in (text or "").split():
        word = raw.strip(".,!?:;()[]{}\"'").lower()
        if word in vocabulary:
            found.append(word)
    return sorted(set(found))
