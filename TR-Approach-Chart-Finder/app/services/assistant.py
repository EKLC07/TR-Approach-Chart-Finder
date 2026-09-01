from app.services.airport_info import airport_info


def assist(file_name, question="", lang="en"):
    parts = file_name.split("_")
    airport = parts[3] if len(parts) > 3 else ""
    chart = file_name.split("IAC_")[-1].split("_")[0].split(".")[0] if "IAC_" in file_name else "?"
    context = airport_info(airport, lang) or {}
    q = (question or "").upper()

    if lang == "tr":
        lines = [
            f"{airport} IAC {chart} - egitim amacli chart okuma yardimi",
            f"Meydan farkindaligi: {context.get('terrain', '')} {context.get('approach', '')}",
        ]
        if "MIN" in q or "DA" in q or "MDA" in q:
            lines.append("Minimum okurken approach category, DA/DH veya MDA/MDH, OCA/OCH, RVR/VIS ve chart notlarini birlikte kontrol et.")
        elif "MISSED" in q:
            lines.append("Missed approach icin ilk tirmanis, donus yonu, hedef fix/holding, altitude ve varsa DME kosullarini ayri ayri oku.")
        else:
            lines.append("Genel okuma sirasi: chart basligi, plan view, profile view, minimumlar ve missed approach.")
        lines.append("Uyari: Bu asistan sadece simulasyon ve egitim amaclidir.")
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
