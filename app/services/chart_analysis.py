from __future__ import annotations

import io
import re
import sys
import zlib
from functools import lru_cache
from pathlib import Path

from app.services.airport_info import airport_info
from app.services.charts import get_pdf_bytes


def analyze_chart(file_name: str, airport: str = "", lang: str = "tr") -> dict:
    lang = "en" if lang == "en" else "tr"
    icao = (airport or _airport_from_file(file_name)).upper()
    chart_no = _chart_number(file_name)
    info = airport_info(icao, lang) or {}

    try:
      text = _pdf_text(file_name)
    except ImportError:
      return _missing_extractor_response(file_name, icao, chart_no, lang, info)
    except Exception as exc:
      return _failed_extraction_response(file_name, icao, chart_no, lang, info, exc)

    facts = _extract_facts(text, icao, chart_no)
    sections = _sections_from_facts(facts, info, lang)
    summary = _summary(facts, lang)
    return {
        "airport": icao,
        "chart": f"IAC {chart_no}" if chart_no else "IAC",
        "file": file_name,
        "status": "extracted" if facts["has_any_value"] else "text-found",
        "summary": summary,
        "sections": sections,
        "nextStep": _next_step(facts, lang),
        "rawTextChars": len(text),
    }


@lru_cache(maxsize=128)
def chart_runways(file_name: str, airport: str = "") -> list[str]:
    """Return runway identifiers detected from an approach chart PDF.

    This is intentionally small and cacheable because `/api/charts?runway=...`
    needs a reliable runway filter before the frontend opens the first result.
    If the runway cannot be read, return an empty list instead of guessing.
    """
    icao = (airport or _airport_from_file(file_name)).upper()
    chart_no = _chart_number(file_name)
    text = _pdf_text(file_name)
    facts = _extract_facts(text, icao, chart_no)

    runways = []
    primary = facts.get("procedure", {}).get("runway", "")
    if primary:
        runways.append(primary)

    # Header/title text is the safest source, but keep a small fallback for
    # charts whose title is split by the PDF text layer.
    for value in re.findall(r"\bRWY\s*([0-3]\d[LRCT]?)\b", text, re.I):
        runways.append(value)

    return _unique([_normalize_runway(value) for value in runways if _normalize_runway(value)])


def chart_matches_runway(file_name: str, runway: str, airport: str = "") -> bool:
    target = _normalize_runway(runway)
    if not target:
        return True
    return target in chart_runways(file_name, airport)


@lru_cache(maxsize=96)
def _pdf_text(file_name: str) -> str:
    data = get_pdf_bytes(file_name)

    vendor_dir = Path(__file__).resolve().parents[1] / "vendor"
    if vendor_dir.exists() and str(vendor_dir) not in sys.path:
        sys.path.insert(0, str(vendor_dir))

    try:
        from pypdf import PdfReader
    except Exception:
        return _clean_text(_pdf_text_from_streams(data))

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return _clean_text("\n".join(pages))


def _pdf_text_from_streams(data: bytes) -> str:
    """Small dependency-free PDF text fallback for DHMI-style text streams.

    It is not a full PDF engine. It extracts readable text tokens from page
    streams so the analysis panel can still find chart titles, frequencies,
    elevations, runway labels, minimum samples, and missed-approach text when
    the optional pypdf package is not installed.
    """
    chunks = []
    for match in re.finditer(rb"(?s)(<<.*?>>)\s*stream\r?\n(.*?)\r?\nendstream", data):
        dictionary, stream = match.groups()
        decoded = _decode_pdf_stream(dictionary, stream)
        if not decoded:
            continue
        text = _strings_from_pdf_content(decoded)
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def _decode_pdf_stream(dictionary: bytes, stream: bytes) -> bytes:
    if b"/FlateDecode" not in dictionary:
        return stream

    for candidate in (stream, stream.strip()):
        try:
            return zlib.decompress(candidate)
        except Exception:
            continue
    return b""


def _strings_from_pdf_content(content: bytes) -> str:
    values = []
    for token in re.findall(rb"\((?:\\.|[^\\()])*\)", content):
        decoded = _decode_pdf_literal(token[1:-1])
        if decoded:
            values.append(decoded)
            shifted = _decode_shifted_font_text(decoded)
            if shifted:
                values.append(shifted)

    for token in re.findall(rb"<([0-9A-Fa-f]{4,})>", content):
        decoded = _decode_pdf_hex(token)
        if decoded:
            values.append(decoded)
            shifted = _decode_shifted_font_text(decoded)
            if shifted:
                values.append(shifted)

    return "\n".join(values)


def _decode_pdf_literal(raw: bytes) -> str:
    output = bytearray()
    index = 0
    while index < len(raw):
        char = raw[index]
        if char != 92:
            output.append(char)
            index += 1
            continue

        index += 1
        if index >= len(raw):
            break

        escaped = raw[index]
        if escaped in b"nrtbf":
            mapping = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}
            output.append(mapping.get(escaped, escaped))
            index += 1
        elif escaped in b"()\\":
            output.append(escaped)
            index += 1
        elif 48 <= escaped <= 55:
            octal = bytes([escaped])
            index += 1
            for _ in range(2):
                if index < len(raw) and 48 <= raw[index] <= 55:
                    octal += bytes([raw[index]])
                    index += 1
                else:
                    break
            output.append(int(octal, 8) & 0xFF)
        else:
            output.append(escaped)
            index += 1

    return _decode_bytes(bytes(output))


def _decode_pdf_hex(raw: bytes) -> str:
    try:
        data = bytes.fromhex(raw.decode("ascii"))
    except Exception:
        return ""

    if len(data) >= 2 and data[0:2] in (b"\xfe\xff", b"\xff\xfe"):
        return _decode_bytes(data)

    if len(data) % 2 == 0 and data[0] == 0:
        return _decode_bytes(data)

    return _decode_bytes(data)


def _decode_bytes(data: bytes) -> str:
    for encoding in ("utf-16-be", "utf-8", "cp1254", "latin-1"):
        try:
            text = data.decode(encoding)
        except Exception:
            continue
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        if re.search(r"[A-Za-z0-9ÇĞİÖŞÜçğıöşü]", text):
            return text.strip()
    return ""


def _decode_shifted_font_text(text: str) -> str:
    shifted = []
    changed = 0
    for char in text:
        code = ord(char)
        if 33 <= code <= 93:
            shifted.append(chr(code + 29))
            changed += 1
        else:
            shifted.append(char)

    candidate = "".join(shifted).strip()
    if not candidate or candidate == text:
        return ""

    letter_count = len(re.findall(r"[A-Z]", candidate))
    source_symbol_count = len(re.findall(r"[^A-Za-z\s]", text))
    if letter_count >= 2 and source_symbol_count >= 1 and changed >= 2:
        return candidate
    return ""


def _extract_facts(text: str, icao: str, chart_no: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    joined = "\n".join(lines)

    procedure = _procedure(lines, joined, icao, chart_no)
    frequencies = _frequencies(joined)
    nav_aids = _nav_aids(lines)
    elevations = _elevations(joined)
    holding = _holding(lines)
    descent = _descent_profile(lines, joined)
    minimums = _minimums(lines)
    missed = _missed_approach(lines)
    courses = _courses(joined, procedure.get("runway"), missed)
    restrictions = _restrictions(lines)

    groups = (procedure, frequencies, nav_aids, elevations, holding, descent, courses, minimums, missed, restrictions)
    return {
        "procedure": procedure,
        "frequencies": frequencies,
        "nav_aids": nav_aids,
        "elevations": elevations,
        "holding": holding,
        "descent": descent,
        "courses": courses,
        "minimums": minimums,
        "missed": missed,
        "restrictions": restrictions,
        "has_any_value": any(group for group in groups),
    }


def _procedure(lines: list[str], joined: str, icao: str, chart_no: str) -> dict:
    runway = _first_match(r"\bRWY\s+([0-3]\d[LRCT]?)\b", joined)
    if not runway:
        runway = _runway_from_fallback_text(joined)
    approach_type = _first_match(r"\b(ILS|RNP|RNAV|VOR|NDB|LOC|LDA)\s+(?:Z|Y|X|W)?\b", joined)
    if approach_type == "NDB" and re.search(r"\bNDB\s*Z\b|\bNDBZ\b", joined, re.I):
        approach_type = "NDB Z"
    variant = _first_match(r"\b(ILS|RNP|RNAV|VOR|NDB|LOC|LDA)\s+([A-Z])\b", joined)
    if variant:
        approach_type = " ".join(variant)
    airport_name = _airport_title(lines, icao)
    effective = _first_match(r"\b(\d{2}\s+[A-Z]{3}\s+\d{2})\b", joined)
    aip_ref = _first_match(r"\b(AD\s*2\s+LT[A-Z0-9]{2}\s+IAC\s*-\s*\d+)\b", joined)
    return _drop_empty({
        "airport_name": airport_name,
        "chart": f"IAC {chart_no}" if chart_no else "",
        "aip_ref": _space(aip_ref),
        "approach": approach_type,
        "runway": runway,
        "effective": effective,
    })


def _frequencies(joined: str) -> dict:
    compact = re.sub(r"\s+", " ", joined)
    result = {}
    for key in ("APP", "TWR", "ATIS", "GND", "ATC"):
        match = re.search(rf"\b{key}\s+((?:\d{{3}}\.\d(?:\s*-\s*)?)+)", compact)
        if match:
            result[key] = _space(match.group(1))
    if result:
        return result

    comm_values = []
    for raw in re.findall(r"(?<!\d)\d{3}\.\d(?:\s*-\s*\d{3}\.\d)?", compact):
        numbers = [float(value) for value in re.findall(r"\d{3}\.\d", raw)]
        if any(118 <= number <= 137 or 225 <= number <= 400 for number in numbers):
            comm_values.append(_space(raw))
    comm_values = _unique(comm_values)

    if "APP" in compact and "TWR" in compact and "ATIS" in compact and len(comm_values) >= 3:
        app = next((value for value in comm_values if value.startswith("119")), comm_values[-1])
        twr = next((value for value in comm_values if "257" in value or value.startswith("118")), comm_values[0])
        atis = next((value for value in comm_values if value.startswith("123")), "")
        return _drop_empty({"APP": app, "TWR": twr, "ATIS": atis})

    for index, value in enumerate(comm_values[:6], start=1):
        result[f"COM {index}"] = value
    return result


def _nav_aids(lines: list[str]) -> list[str]:
    aids = []
    pattern = re.compile(r"\b(?:(VOR|NDB)\s+(\d{3}(?:\.\d)?)\s+([A-Z0-9]{2,5})|CH\s*(\d{2,3}X))\b")
    for line in lines:
        for match in pattern.finditer(line):
            if match.group(1):
                aids.append(f"{match.group(3)} {match.group(1)} {match.group(2)}")
            elif match.group(4):
                aids.append(f"DME {match.group(4)}")
    return _unique(aids)


def _elevations(joined: str) -> dict:
    result = {}
    compact = re.sub(r"\s+", " ", joined)
    ad_elev = _first_match(r"\bAD\s+ELEV(?:\s+[A-Z]+){0,5}\s+(\d[\d\s]*\s*FT)\b", compact)
    transition = _first_match(r"\bTRANSITION\s+ALTITUDE\s*(\d[\d\s]*\s*FT)\b", compact)
    if not transition:
        transition = _first_match(r"\b(\d[\d\s]*\s*FT)\s+TRANSITION\s+ALTITUDE", compact)
    threshold = _first_match(r"\bRWY\s+([0-3]\d[LRCT]?)\s+THR\s+ELEV\s+(\d[\d\s]*\s*FT)\b", compact)
    if ad_elev:
        result["AD ELEV"] = _space(ad_elev)
    if transition:
        result["Transition altitude"] = _space(transition)
    if threshold:
        result[f"RWY {threshold[0]} THR ELEV"] = _space(threshold[1])
    return result


def _holding(lines: list[str]) -> dict:
    result = {}
    for index, line in enumerate(lines):
        if "MAX HOLDING SPEED" not in line.upper():
            continue

        window = " ".join(lines[max(0, index - 4): min(len(lines), index + 5)])
        speed = _first_match(r"\bIAS\s*(\d{2,3})\s*KT\b", window)
        if speed:
            result["max_holding_speed"] = f"IAS {speed} KT"
            break
    return result


def _descent_profile(lines: list[str], joined: str) -> dict:
    result = {}
    joined_clean = re.sub(r"\s+", " ", joined)

    angle = _first_match(r"\b([23]\.\d{1,2})\s*°", joined_clean)
    if angle:
        result["descent_angle"] = f"{angle}°"
    elif "3°" in joined or "030°" in joined:
        result["descent_angle"] = "3° profil"

    map_index = next((index for index, line in enumerate(lines) if re.search(r"\bMAPt\b", line, re.I)), -1)
    if map_index >= 0:
        result["mapt"] = _space(lines[map_index - 1] if map_index > 0 and re.search(r"\bD\d+(?:\.\d+)?", lines[map_index - 1]) else "MAPt")

        window = lines[max(0, map_index - 12): min(len(lines), map_index + 14)]
        fixes = _unique(re.findall(r"\bD\d+(?:\.\d+)?\s*\(CH\d{2,3}X\)", "\n".join(window), re.I))
        altitudes = _profile_altitudes(window)

        after_altitudes = _profile_altitudes(lines[map_index + 1: min(len(lines), map_index + 8)])
        if after_altitudes:
            result["descent_start_altitude"] = after_altitudes[0]
            if len(after_altitudes) > 1:
                result["mapt_altitude"] = after_altitudes[1]
        elif altitudes:
            window_start = max(0, map_index - 12)
            mapt_alt = _nearest_profile_altitude(window, map_index - window_start)
            if mapt_alt:
                result["mapt_altitude"] = mapt_alt

            candidates = [alt for alt in altitudes if alt != mapt_alt and _altitude_number(alt) > _altitude_number(mapt_alt)]
            if candidates:
                result["descent_start_altitude"] = candidates[0]

        if fixes:
            descent_fix = next((fix for fix in fixes if "D3.0" not in fix.upper()), "")
            if descent_fix:
                result["descent_start_fix"] = descent_fix

    fap = _first_match(r"\b(?:FAF|FAP)\s+([A-Z0-9./() -]{1,28})", joined_clean)
    if fap:
        result.setdefault("descent_start_fix", _space(fap))

    return result


def _courses(joined: str, runway: str | None, missed: str = "") -> dict:
    result = {}
    if runway:
        result["final_course"] = f"{runway[:2]}0°"

    missed_heading = _first_match(r"\bon\s+([0-3]\d{2})°", missed or joined)
    if missed_heading and missed_heading != result.get("final_course"):
        result["missed_track"] = f"{missed_heading}°"

    inbound = _first_match(r"\b(?:INBD|INBOUND|CRS|COURSE)\s*([0-3]\d{2})°", joined)
    if inbound and inbound not in result.values():
        result["published_course"] = f"{inbound}°"

    return result


def _minimums(lines: list[str]) -> dict:
    result = {}
    joined = "\n".join(lines)
    if "OCA" in joined or "OCH" in joined:
        result["minimums_table"] = "Tespit edildi; kategori sütunları görsel OCR ile doğrulanmalı."

    altitude_pairs = _unique([
        f"{value}' ({height}')"
        for value, height in re.findall(r"\b(\d{3,5})'\s*\(\s*(\d{2,5})'\s*\)", joined)
    ])
    if altitude_pairs:
        result["oca_och_sample"] = ", ".join(altitude_pairs[:4])

    for line in lines:
        clean = _space(line)
        upper = clean.upper()
        if len(clean) > 110 or upper.startswith("CHANGE:"):
            continue
        if "RVR" in upper or re.search(r"\bVIS\b", upper):
            result.setdefault("visibility", clean)
        if re.search(r"\bCAT\s*[A-D]\b", upper):
            result.setdefault("aircraft_category", clean)
    return result


def _missed_approach(lines: list[str]) -> str:
    indexes = [index for index, line in enumerate(lines) if "MISSED APPROACH" in line.upper()]
    if not indexes:
        return ""

    index = indexes[0]
    window = lines[max(0, index - 7): min(len(lines), index + 8)]
    useful = []
    for line in window:
        if line.upper() == "MISSED APPROACH":
            continue
        if re.search(r"\b(climb|climbing|proceed|turn|hold|cross|FT|VOR|NDB|DME|RWY)\b", line, re.I):
            useful.append(_space(line))
    return ". ".join(_unique(useful))[:520]


def _restrictions(lines: list[str]) -> list[str]:
    result = []
    joined = "\n".join(lines)
    for line in lines:
        if re.search(r"\b(DME REQUIRED|VAR\s+\d)", line, re.I):
            result.append(_space(line))
    return _unique(result)[:10]


def _sections_from_facts(facts: dict, info: dict, lang: str) -> list[dict]:
    sections = []

    def add(title_tr: str, title_en: str, values, source_tr: str, source_en: str, confidence: str = "pdf", list_label_tr: str = "Değer", list_label_en: str = "Value"):
        if not values:
            return
        title = title_en if lang == "en" else title_tr
        items = _list_items(values, list_label_en if lang == "en" else list_label_tr, lang) if isinstance(values, list) else _dict_items(values, lang)
        sections.append(_section(title, "", "", confidence, items))

    key_values = _drop_empty({
        key: facts["procedure"].get(key)
        for key in ("airport_name", "chart", "approach", "runway", "effective")
    })
    add(
        "Prosedür",
        "Procedure",
        key_values,
        "Chart başlığı ve üst bilgi alanından okundu.",
        "Read from the chart title/header.",
    )
    add(
        "Frekanslar",
        "Frequencies",
        facts["frequencies"],
        "APP/TWR/ATIS/GND bloklarından okundu.",
        "Read from APP/TWR/ATIS/GND blocks.",
    )
    add(
        "VOR / NDB / DME",
        "VOR / NDB / DME",
        facts["nav_aids"],
        "Navigasyon yardımcı etiketlerinden okundu.",
        "Read from navigation aid labels.",
        list_label_tr="Yardımcı",
        list_label_en="Aid",
    )
    runway_values = _drop_empty({
        "runway": facts["procedure"].get("runway"),
        **facts["elevations"],
    })
    add(
        "Pist / rakım",
        "Runway / elevation",
        runway_values,
        "Pist, AD ELEV, THR ELEV ve transition altitude alanlarından okundu.",
        "Read from runway, AD ELEV, THR ELEV, and transition altitude areas.",
    )
    add(
        "Holding",
        "Holding",
        facts["holding"],
        "Holding kutusu ve hız limitinden okundu.",
        "Read from holding box and speed limit.",
    )
    add(
        "Alçalma başlangıcı",
        "Descent start",
        facts["descent"],
        "FAF/FAP, MAPt, DME ve profil irtifası alanlarından çıkarıldı.",
        "Derived from FAF/FAP, MAPt, DME, and profile altitude areas.",
        "needs-ocr",
    )
    add(
        "Course / baş",
        "Course / headings",
        facts["courses"],
        "Final course ve missed approach track gibi operasyonel başlar.",
        "Operational headings such as final course and missed approach track.",
    )
    add(
        "Minimumlar",
        "Minimums",
        facts["minimums"],
        "OCA(H), DA/DH, MDA/MDH, RVR/VIS bölgesinden okundu.",
        "Read from OCA(H), DA/DH, MDA/MDH, RVR/VIS area.",
        "needs-ocr",
    )
    add(
        "Kısıtlar",
        "Restrictions",
        facts["restrictions"],
        "DME REQUIRED, speed limit ve özel saha notlarından okundu.",
        "Read from DME REQUIRED, speed limit, and special chart notes.",
        list_label_tr="Kısıt",
        list_label_en="Restriction",
    )

    if facts["missed"]:
        sections.append(_section(
            "Pas geçme prosedürü" if lang == "tr" else "Missed approach",
            _localized_missed_approach(facts["missed"], lang),
            "",
            "pdf",
        ))

    if sections:
        return sections

    return [
        _section(
            "Analiz verisi okunamadı" if lang == "tr" else "No analysis values read",
            "Bu PDF metin katmanından güvenilir operasyonel değer çıkarılamadı; OCR katmanı gerekir." if lang == "tr" else "No reliable operational values could be extracted from this PDF text layer; OCR is needed.",
            "PDF text layer.",
            "warning",
        )
    ]

def _legacy_sections_from_facts(facts: dict, info: dict, lang: str) -> list[dict]:
    if lang == "en":
        return [
            _section("Procedure", _empty(facts["procedure"], "No procedure title value was readable."), "Read from the chart title/header.", "pdf", _dict_items(facts["procedure"], lang)),
            _section("Frequencies", _empty(facts["frequencies"], "No frequency values were readable."), "APP/TWR/ATIS blocks.", "pdf", _dict_items(facts["frequencies"], lang)),
            _section("Elevation / transition", _empty(facts["elevations"], "No elevation values were readable."), "AD ELEV / THR ELEV / transition altitude.", "pdf", _dict_items(facts["elevations"], lang)),
            _section("Navigation aids", _empty(facts["nav_aids"], "No navigation aids were readable."), "VOR/NDB/DME labels.", "pdf", _list_items(facts["nav_aids"], "Nav aid")),
            _section("Courses / headings", _empty(facts["courses"], "No course values were readable."), "Only operationally meaningful headings are shown.", "pdf", _dict_items(facts["courses"], lang)),
            _section("Minimums", _empty(facts["minimums"], "Minimums table text was detected poorly; visual OCR pass may be needed."), "OCA(H), DA/DH, MDA/MDH, RVR/VIS area.", "needs-ocr", _dict_items(facts["minimums"], lang)),
            _section("Missed approach", facts["missed"] or "Missed approach text was not readable from the PDF text layer.", "Missed approach block.", "pdf"),
            _section("Notes / restrictions", _empty(facts["restrictions"], "No special notes were readable."), "Chart notes and restricted-area labels.", "pdf", _list_items(facts["restrictions"], "Note")),
        ]

    return [
        _section("Prosedür", _empty(facts["procedure"], "Prosedür başlığından okunabilir değer alınamadı."), "Chart başlık/üst bilgi alanından okundu.", "pdf", _dict_items(facts["procedure"], lang)),
        _section("Frekanslar", _empty(facts["frequencies"], "Frekans değeri okunamadı."), "APP/TWR/ATIS bloklarından okundu.", "pdf", _dict_items(facts["frequencies"], lang)),
        _section("İrtifa / geçiş", _empty(facts["elevations"], "İrtifa değeri okunamadı."), "AD ELEV / THR ELEV / transition altitude alanından okundu.", "pdf", _dict_items(facts["elevations"], lang)),
        _section("Navigasyon yardımcıları", _empty(facts["nav_aids"], "Navigasyon yardımcısı okunamadı."), "VOR/NDB/DME etiketlerinden okundu.", "pdf", _list_items(facts["nav_aids"], "Yardımcı")),
        _section("Course / baş", _empty(facts["courses"], "Course/baş değeri okunamadı."), "Sadece operasyonel anlamlı baş değerleri gösterilir.", "pdf", _dict_items(facts["courses"], lang)),
        _section("Minimumlar", _empty(facts["minimums"], "Minimum tablosu metin katmanından zayıf okunuyor; görsel OCR geçişi gerekebilir."), "OCA(H), DA/DH, MDA/MDH, RVR/VIS bölgesinden okundu.", "needs-ocr", _dict_items(facts["minimums"], lang)),
        _section("Missed approach", facts["missed"] or "Missed approach metni PDF text layer üzerinden okunamadı.", "Missed approach kutusundan okundu.", "pdf"),
        _section("Notlar / kısıtlar", _empty(facts["restrictions"], "Özel not veya kısıt okunamadı."), "Chart notları ve saha etiketlerinden okundu.", "pdf", _list_items(facts["restrictions"], "Not")),
    ]


def _summary(facts: dict, lang: str) -> str:
    procedure = facts["procedure"]
    runway = procedure.get("runway", "")
    approach = procedure.get("approach", "")
    found = []
    if approach:
        found.append(approach)
    if runway:
        found.append(f"RWY {runway}")
    if facts["frequencies"]:
        found.append("frekanslar" if lang == "tr" else "frequencies")
    if facts["elevations"]:
        found.append("irtifalar" if lang == "tr" else "altitudes")
    if facts["holding"]:
        found.append("azami holding hızı" if lang == "tr" else "max holding speed")
    if facts["descent"]:
        found.append("alçalma başlangıcı" if lang == "tr" else "descent start")
    if facts["courses"]:
        found.append("course/baş" if lang == "tr" else "courses/headings")
    if facts["minimums"]:
        found.append("minimumlar" if lang == "tr" else "minimums")
    if facts["missed"]:
        found.append("pas geçme" if lang == "tr" else "missed approach")

    if lang == "en":
        return "Operational chart analysis ready: " + (", ".join(found) if found else "limited values found.")
    return "Operasyonel chart analizi hazır: " + (", ".join(found) if found else "sınırlı değer bulundu.")


def _missing_extractor_response(file_name: str, icao: str, chart_no: str, lang: str, info: dict) -> dict:
    if lang == "en":
        summary = "The advanced PDF reader is not available, so Ciguli is using the built-in chart text reader."
        sections = [_section("Built-in PDF reader", "The app can still extract readable chart values. Some dense tables may need OCR verification later.", "Local fallback reader.", "warning")]
    else:
        summary = "Gelişmiş PDF okuyucu yok; Ciguli dahili chart metin okuyucusunu kullanıyor."
        sections = [_section("Dahili PDF okuyucu", "Uygulama okunabilir chart değerlerini yine çıkarabilir. Yoğun tablolar için ileride OCR doğrulaması gerekebilir.", "Yerel fallback okuyucu.", "warning")]
    sections.append(_section("Meydan farkındalığı" if lang == "tr" else "Airport awareness", info.get("terrain", ""), "Airport profile.", "local"))
    return {
        "airport": icao,
        "chart": f"IAC {chart_no}" if chart_no else "IAC",
        "file": file_name,
        "status": "extractor-missing",
        "summary": summary,
        "sections": sections,
        "nextStep": summary,
    }


def _failed_extraction_response(file_name: str, icao: str, chart_no: str, lang: str, info: dict, exc: Exception) -> dict:
    if lang == "en":
        summary = "Ciguli could not read this PDF text layer yet. A visual OCR pass may be needed."
        sections = [_section("Extraction failed", str(exc), "PDF text layer.", "warning")]
    else:
        summary = "Ciguli bu PDF metin katmanını okuyamadı. Görsel OCR geçişi gerekebilir."
        sections = [_section("Okuma başarısız", str(exc), "PDF metin katmanı.", "warning")]
    sections.append(_section("Meydan farkındalığı" if lang == "tr" else "Airport awareness", info.get("terrain", ""), "Airport profile.", "local"))
    return {
        "airport": icao,
        "chart": f"IAC {chart_no}" if chart_no else "IAC",
        "file": file_name,
        "status": "extract-failed",
        "summary": summary,
        "sections": sections,
        "nextStep": summary,
    }


def _section(title: str, value: str, source: str, confidence: str = "extracted", items: list[dict] | None = None) -> dict:
    section = {
        "title": title,
        "value": value,
        "source": source,
        "confidence": confidence,
    }
    if items:
        section["items"] = items
    return section


def _airport_from_file(file_name: str) -> str:
    match = re.search(r"LT_AD_2_(LT[A-Z0-9]{2})_IAC_", file_name or "")
    return match.group(1) if match else ""


def _chart_number(file_name: str) -> str:
    match = re.search(r"_IAC_(\d{2})_", file_name or "")
    return match.group(1) if match else ""


def _airport_title(lines: list[str], icao: str) -> str:
    for line in lines:
        upper = line.upper()
        blocked = ("NDB/DME", "VOR", "NDB", "DME", "PROCEED", "CLIMB", "TURN", "HOLD")
        if "/" in line and icao.replace("LT", "") not in line and not any(word in upper for word in blocked):
            cleaned = _space(line)
            if _clean_airport_title_candidate(cleaned):
                return cleaned

    blocked_words = {
        "MISSED", "APPROACH", "INSTRUMENT", "CHART", "AIP", "AIRAC", "AMDT",
        "CHANGE", "SCALE", "TURKIYE", "TÜRKİYE", "DHMI", "ANKNDB", "VORESB",
    }
    clean_words = []
    for line in lines:
        cleaned = _space(line).upper()
        if (
            3 <= len(cleaned) <= 24
            and cleaned not in blocked_words
            and re.fullmatch(r"[A-ZÇĞİÖŞÜ]+", cleaned)
        ):
            clean_words.append(cleaned)

    for index, word in enumerate(clean_words[:-1]):
        nxt = clean_words[index + 1]
        if word != nxt and word not in blocked_words and nxt not in blocked_words:
            if word in {"ANKARA", "ISTANBUL", "IZMIR", "ANTALYA", "MUGLA", "KAYSERI", "TRABZON"}:
                return f"{word}/{nxt}"
    return ""


def _clean_airport_title_candidate(cleaned: str) -> bool:
    if len(cleaned) > 80 or cleaned != cleaned.upper():
        return False
    if not re.search(r"[A-ZÇĞİÖŞÜ]{3,}", cleaned):
        return False

    non_space = re.sub(r"\s+", "", cleaned)
    letters = re.findall(r"[A-ZÇĞİÖŞÜ]", cleaned)
    return bool(non_space) and len(letters) / len(non_space) >= 0.68


def _runway_from_fallback_text(joined: str) -> str:
    compact = re.sub(r"\s+", "", joined.upper())
    for suffix in ("L", "R", "C", "T"):
        if f"RWY{suffix}" not in compact:
            continue
        headings = _unique([f"{value}°" for value in re.findall(r"\b([0-3]\d0)°", joined)])
        for heading in headings:
            value = heading.replace("°", "")
            if value and value[:2].isdigit():
                return f"{value[:2]}{suffix}"
    return ""


def _normalize_runway(value: str) -> str:
    return re.sub(r"[^0-9A-Z]", "", str(value or "").upper().replace("RWY", ""))


def _profile_altitudes(lines: list[str]) -> list[str]:
    values = []
    joined = "\n".join(lines)
    for value in re.findall(r"\b(\d{3,5})'", joined):
        number = int(value)
        if 200 <= number <= 25000:
            values.append(f"{number}'")
    return _unique(values)


def _nearest_profile_altitude(lines: list[str], index: int) -> str:
    best = ""
    best_distance = 999
    for line_index, line in enumerate(lines):
        for value in re.findall(r"\b(\d{3,5})'", line):
            number = int(value)
            if number < 200 or number > 25000:
                continue
            distance = abs(line_index - index)
            if distance < best_distance:
                best = f"{number}'"
                best_distance = distance
    return best


def _altitude_number(value: str) -> int:
    match = re.search(r"\d{3,5}", value or "")
    return int(match.group(0)) if match else 0


def _first_match(pattern: str, text: str):
    match = re.search(pattern, text, re.I)
    if not match:
        return ""
    groups = match.groups()
    if len(groups) > 1:
        return tuple(group for group in groups if group is not None)
    return groups[0]


def _empty(values, empty: str) -> str:
    return "" if values else empty


def _dict_items(values: dict, lang: str = "tr") -> list[dict]:
    if not values:
        return []
    return [{"label": _label(key, lang), "value": _format_value(key, value, lang)} for key, value in values.items()]


def _list_items(values: list[str], label: str, lang: str = "tr") -> list[dict]:
    return [
        {"label": f"{label} {index}", "value": _translate_short_chart_value(value) if lang == "tr" else value}
        for index, value in enumerate(values, start=1)
    ]


def _format_value(key: str, value, lang: str) -> str:
    if key == "airport_name":
        return str(value).replace("/", " / ")
    if key == "runway":
        return f"RWY {value}"
    if key == "minimums_table":
        return "Detected; exact category columns should be verified with visual OCR." if lang == "en" else str(value)
    if lang == "tr":
        return _translate_short_chart_value(str(value))
    return str(value)


def _localized_missed_approach(value: str, lang: str) -> str:
    if lang != "tr":
        return value
    return _translate_missed_approach(value)


def _translate_missed_approach(value: str) -> str:
    value = re.sub(
        r"([A-Z0-9]+)\s+then turn\s+(left|right)\s+climbing to\.\s*climbing to\s+(\d{3,5})\s*FT\s+on\s+([0-3]\d{2})°\s+from",
        r"\1 then turn \2 climbing to \3 FT on \4° from",
        value or "",
        flags=re.I,
    )
    sentences = [part.strip() for part in re.split(r"\.\s*", value or "") if part.strip()]
    translated = []

    for sentence in sentences:
        clean = _space(sentence)
        upper = clean.upper()
        if upper in {"VOR/DME", "VOR", "DME", "NDB"}:
            continue

        match = re.search(r"^(\d{3,5})\s*FT\s+proceed to\s+([A-Z0-9]+)\s+and hold$", clean, re.I)
        if match:
            translated.append(f"{match.group(1)} FT'e tırmanarak {match.group(2)} fixine ilerle ve holding'e gir.")
            continue

        match = re.search(r"^([A-Z0-9]+)\s+then turn\s+(left|right)\s+climbing to$", clean, re.I)
        if match:
            direction = "sola" if match.group(2).lower() == "left" else "sağa"
            translated.append(f"{match.group(1)} sonrası {direction} dönüşle tırmanmaya devam et.")
            continue

        match = re.search(r"^([A-Z0-9]+)\s+then turn\s+(left|right)\s+climbing to\s+(\d{3,5})\s*FT\s+on\s+([0-3]\d{2})°\s+from$", clean, re.I)
        if match:
            direction = "sola" if match.group(2).lower() == "left" else "sağa"
            translated.append(f"{match.group(1)} sonrası {direction} dönüşle {match.group(4)}° hattında {match.group(3)} FT'e tırman.")
            continue

        match = re.search(r"^climbing to\s+(\d{3,5})\s*FT\s+on\s+([0-3]\d{2})°\s+from$", clean, re.I)
        if match:
            translated.append(f"{match.group(2)}° hattında {match.group(1)} FT'e tırman.")
            continue

        match = re.search(r"^(\d{3,5})\s*FT\s+or above then continue$", clean, re.I)
        if match:
            translated.append(f"{match.group(1)} FT veya üzerinde devam et.")
            continue

        match = re.search(r"^Proceed to\s+(.+?)\s+cross$", clean, re.I)
        if match:
            translated.append(f"{_translate_short_chart_value(match.group(1))} üzerinden geç.")
            continue

        translated.append(_translate_short_chart_value(clean))

    return " ".join(translated) if translated else value


def _translate_short_chart_value(value: str) -> str:
    replacements = [
        (r"\bDME REQUIRED\b", "DME gerekli"),
        (r"\bMAX HOLDING SPEED\b", "Azami holding hızı"),
        (r"\bIAS\s+(\d{2,3})\s+KT\b", r"IAS \1 KT"),
        (r"\bproceed to\b", "ilerle"),
        (r"\band hold\b", "ve holding'e gir"),
        (r"\bturn left\b", "sola dön"),
        (r"\bturn right\b", "sağa dön"),
        (r"\bclimbing to\b", "tırman"),
        (r"\bthen continue\b", "sonra devam et"),
        (r"\bor above\b", "veya üzerinde"),
        (r"\bcross\b", "üzerinden geç"),
    ]
    result = value
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.I)
    return _space(result)


def _label(key: str, lang: str) -> str:
    labels = {
        "tr": {
            "airport_name": "Meydan",
            "chart": "Chart",
            "aip_ref": "AIP referansı",
            "approach": "Yaklaşma",
            "runway": "Pist",
            "effective": "Yürürlük tarihi",
            "max_holding_speed": "Max holding speed",
            "descent_angle": "Alçalma açısı",
            "descent_start_fix": "Başlama noktası",
            "descent_start_altitude": "Başlama irtifası",
            "mapt": "MAPt",
            "mapt_altitude": "MAPt irtifası",
            "final_course": "Final baş",
            "missed_track": "Pas geçme başı",
            "published_course": "Yayınlı course",
            "minimums_table": "Minimum tablosu",
            "oca_och_sample": "OCA/OCH örneği",
            "visibility": "RVR / VIS",
            "aircraft_category": "Uçak kategorisi",
            "Transition altitude": "Transition altitude",
        },
        "en": {
            "airport_name": "Airport",
            "chart": "Chart",
            "aip_ref": "AIP reference",
            "approach": "Approach",
            "runway": "Runway",
            "effective": "Effective date",
            "max_holding_speed": "Max holding speed",
            "descent_angle": "Descent angle",
            "descent_start_fix": "Start fix",
            "descent_start_altitude": "Start altitude",
            "mapt": "MAPt",
            "mapt_altitude": "MAPt altitude",
            "final_course": "Final course",
            "missed_track": "Missed track",
            "published_course": "Published course",
            "minimums_table": "Minimums table",
            "oca_och_sample": "OCA/OCH sample",
            "visibility": "RVR / VIS",
            "aircraft_category": "Aircraft category",
            "Transition altitude": "Transition altitude",
        },
    }
    return labels.get(lang, labels["tr"]).get(key, key)


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = _space(value)
        key = cleaned.upper()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _drop_empty(values: dict) -> dict:
    return {key: value for key, value in values.items() if value}


def _space(value) -> str:
    if isinstance(value, tuple):
        return " ".join(_space(item) for item in value if item)
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_text(text: str) -> str:
    return text.replace("\u2212", "-").replace("\u00a0", " ")


def _next_step(facts: dict, lang: str) -> str:
    if facts["minimums"] and facts["missed"]:
        return "Minimum tablosu için hassas OCR doğrulaması sonraki kalite adımı." if lang == "tr" else "Visual OCR verification of the minimums table is the next quality step."
    return "Eksik kalan yoğun tablolar için sonraki adım OCR doğrulaması." if lang == "tr" else "OCR verification is the next step for dense table areas."
