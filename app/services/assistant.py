from app.services.airport_info import airport_info


def assist(file_name, question="", lang="en"):
    parts = file_name.split("_")
    airport = parts[3] if len(parts) > 3 else ""
    chart = file_name.split("IAC_")[-1].split("_")[0].split(".")[0] if "IAC_" in file_name else "?"
    context = airport_info(airport, lang) or {}
    q = (question or "").upper()

    if lang == "tr":
        lines = [
            f"{airport} IAC {chart} - eğitim amaçlı yaklaşma kartı okuma yardımı",
            f"Meydan farkındalığı: {context.get('terrain', '')} {context.get('approach', '')}",
        ]
        if "MIN" in q or "DA" in q or "MDA" in q:
            lines.append("Minimumlar okunurken yaklaşma kategorisi, DA/DH veya MDA/MDH, OCA/OCH, RVR/VIS ve yaklaşma kartı notlarını birlikte kontrol ediniz.")
        elif "MISSED" in q:
            lines.append("Pas geçme icin ilk tırmanış, dönüş yönü, hedef fix/holding, altitude ve varsa DME koşullarını ayrı ayrı okuyunuz.")
        else:
            lines.append("Genel okuma sırası: yaklaşma kartı başlığı, plan view, profile view, minimumlar ve pas geçme.")
        lines.append("Uyarı: Bu asistan sadece simülasyon ve eğitim amaçlıdır.")
        return {"answer": "\n\n".join(lines), "extractedTextPreview": ""}

    lines = [
        f"{airport} IAC {chart} - training-oriented chart reading help",
        f"Airport awareness: {context.get('terrain', '')} {context.get('approach', '')}",
    ]
    if "MIN" in q or "DA" in q or "MDA" in q:
        lines.append("When reading minimums, check approach category, DA/DH or MDA/MDH, OCA/OCH, RVR/VIS, and related notes together.")
    elif "MISSED" in q:
        lines.append("For missed approach, separate the initial climb, turn direction, target fix/holding, altitude, and any DME conditions.")
    else:
        lines.append("General reading flow: chart title, plan view, profile view, minimums, and missed approach.")
    lines.append("Warning: This assistant is for simulation and training only.")
    return {"answer": "\n\n".join(lines), "extractedTextPreview": ""}
