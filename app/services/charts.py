import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import CACHE_TTL_SECONDS, DHMI_BASE, PDF_SCAN_LIMIT
from app.data.airports import is_valid_icao


PDF_RE = re.compile(r"^LT_AD_2_(LT[A-Z0-9]{2})_IAC_\d{2}_en\.pdf$")
_chart_cache = {}
STATIC_CHART_INDEX = {
    # Fast-path chart/runway index for high-use airports. This prevents the UI
    # from downloading and parsing many PDFs just to answer "which chart is RWY X?".
    "LTAC": {
        1: {"title": "NDB Z RWY 03C", "runways": ["03C"]},
        2: {"title": "ILS Y CAT I or LOC Y RWY 03C", "runways": ["03C"]},
        3: {"title": "ILS W CAT II RWY 03C", "runways": ["03C"]},
        4: {"title": "ILS V CAT I or LOC V RWY 03C", "runways": ["03C"]},
        5: {"title": "ILS U CAT II RWY 03C", "runways": ["03C"]},
        6: {"title": "VOR Z RWY 03C", "runways": ["03C"]},
        7: {"title": "NDB Z RWY 03L", "runways": ["03L"]},
        8: {"title": "VOR Z RWY 03L", "runways": ["03L"]},
        9: {"title": "ILS Z CAT II RWY 03L", "runways": ["03L"]},
        10: {"title": "ILS Y CAT I or LOC Y RWY 03L", "runways": ["03L"]},
        11: {"title": "ILS X CAT I or LOC X RWY 03L", "runways": ["03L"]},
        12: {"title": "ILS U CAT II RWY 03L", "runways": ["03L"]},
        13: {"title": "VOR Z, NDB Z RWY 21R", "runways": ["21R"]},
        14: {"title": "ILS Z CAT I or LOC Z RWY 21R", "runways": ["21R"]},
        15: {"title": "VOR Y RWY 21R", "runways": ["21R"]},
        16: {"title": "VOR Z, NDB Z RWY 21C", "runways": ["21C"]},
        17: {"title": "ILS Z CAT I or LOC Z RWY 21C", "runways": ["21C"]},
        18: {"title": "VOR Y RWY 21C", "runways": ["21C"]},
        19: {"title": "VOR A", "runways": []},
        20: {"title": "VOR Z RWY 03R", "runways": ["03R"]},
        21: {"title": "VOR Z RWY 21L", "runways": ["21L"]},
        22: {"title": "ILS Z CAT I or LOC Z RWY 03R", "runways": ["03R"]},
        23: {"title": "ILS Z CAT I or LOC Z RWY 21L", "runways": ["21L"]},
        24: {"title": "ILS Y CAT I or LOC Y RWY 03R", "runways": ["03R"]},
        25: {"title": "ILS X CAT II RWY 03R", "runways": ["03R"]},
        26: {"title": "ILS Y CAT II RWY 21L", "runways": ["21L"]},
        27: {"title": "ILS W CAT I RWY 03R", "runways": ["03R"]},
        28: {"title": "ILS X CAT I or LOC X RWY 21L", "runways": ["21L"]},
        29: {"title": "ILS V CAT II RWY 03R", "runways": ["03R"]},
    },
    "LTFM": {
        1: {"title": "ILS Z CAT I or LOC Z RWY 16L", "runways": ["16L"]},
        2: {"title": "RNP Z RWY 16L", "runways": ["16L"]},
        3: {"title": "ILS Z CAT I or LOC Z RWY 16R", "runways": ["16R"]},
        4: {"title": "ILS Y CAT II RWY 16R", "runways": ["16R"]},
        5: {"title": "ILS X CAT II RWY 16R", "runways": ["16R"]},
        6: {"title": "RNP Z RWY 16R", "runways": ["16R"]},
        7: {"title": "ILS Z CAT I or LOC Z RWY 17L", "runways": ["17L"]},
        8: {"title": "ILS Y CAT II RWY 17L", "runways": ["17L"]},
        9: {"title": "ILS X CAT II RWY 17L", "runways": ["17L"]},
        10: {"title": "RNP Z RWY 17L", "runways": ["17L"]},
        11: {"title": "ILS Z CAT I or LOC Z RWY 17R", "runways": ["17R"]},
        12: {"title": "ILS Y CAT II RWY 17R", "runways": ["17R"]},
        13: {"title": "ILS X CAT III RWY 17R", "runways": ["17R"]},
        14: {"title": "RNP Z RWY 17R", "runways": ["17R"]},
        15: {"title": "ILS Z CAT I or LOC Z RWY 18", "runways": ["18"]},
        16: {"title": "ILS Y CAT II RWY 18", "runways": ["18"]},
        17: {"title": "ILS X CAT III RWY 18", "runways": ["18"]},
        18: {"title": "RNP Z RWY 18", "runways": ["18"]},
        19: {"title": "ILS Z CAT I or LOC Z RWY 34L", "runways": ["34L"]},
    },
    "LTAI": {
        1: {"title": "NDB Z RWY 36C", "runways": ["36C"]},
        2: {"title": "VOR Z RWY 36C / 36L", "runways": ["36C", "36L"]},
        4: {"title": "ILS Z CAT I or LOC Z RWY 36C", "runways": ["36C"]},
        5: {"title": "ILS Y CAT I RWY 36C", "runways": ["36C"]},
        6: {"title": "VOR Z RWY 18C / 18R", "runways": ["18C", "18R"]},
        7: {"title": "ILS P RWY 36C", "runways": ["36C"]},
        9: {"title": "VOR Z RWY 18L", "runways": ["18L"]},
        10: {"title": "VOR Z RWY 36R", "runways": ["36R"]},
        11: {"title": "VOR Y RWY 36R", "runways": ["36R"]},
        13: {"title": "ILS Z CAT I or LOC Z RWY 36R", "runways": ["36R"]},
        15: {"title": "NDB Z RWY 18L", "runways": ["18L"]},
        16: {"title": "NDB Z RWY 36R", "runways": ["36R"]},
        17: {"title": "NDB Y RWY 36R", "runways": ["36R"]},
        18: {"title": "ILS P RWY 36R", "runways": ["36R"]},
        20: {"title": "NDB Y RWY 36C", "runways": ["36C"]},
        22: {"title": "ILS V CAT I or LOC V RWY 36R", "runways": ["36R"]},
        24: {"title": "ILS S CAT I or LOC S RWY 36R", "runways": ["36R"]},
        27: {"title": "ILS X CAT I or LOC X RWY 18C", "runways": ["18C"]},
        28: {"title": "ILS X CAT I or LOC X RWY 18L", "runways": ["18L"]},
        29: {"title": "ILS W CAT II RWY 36C", "runways": ["36C"]},
        30: {"title": "ILS X CAT II RWY 36R", "runways": ["36R"]},
    },
}
_SSL_CONTEXT = ssl._create_unverified_context()
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TR-Approach-Chart-Finder/1.0",
    "Accept": "application/pdf,text/html,*/*;q=0.8",
}
_SCAN_TIMEOUT = 6
_DOWNLOAD_TIMEOUT = 25
_SCAN_WORKERS = 12


def pdf_name(icao, number):
    return f"LT_AD_2_{icao}_IAC_{number:02d}_en.pdf"


def pdf_url(file_name):
    return f"{DHMI_BASE}/{file_name}"


def chart_entry(icao, number, metadata=None):
    metadata = metadata or {}
    file_name = pdf_name(icao, number)
    source_url = pdf_url(file_name)
    return {
        "id": f"IAC {number:02d}",
        "title": metadata.get("title") or f"Instrument Approach Chart {number:02d}",
        "procedureTitle": metadata.get("title", ""),
        "file": file_name,
        "viewerUrl": f"/api/pdf/{file_name}",
        "sourceUrl": source_url,
        "source": "DHMI public AIP PDF",
        "runways": metadata.get("runways", []),
        "indexed": bool(metadata),
    }


def normalize_runway(value):
    return re.sub(r"[^0-9A-Z]", "", str(value or "").upper().replace("RWY", ""))


def chart_number_from_file(file_name):
    match = re.search(r"_IAC_(\d{2})_", file_name or "")
    return int(match.group(1)) if match else None


def enrich_chart_metadata(icao, chart):
    number = chart_number_from_file(chart.get("file", ""))
    metadata = STATIC_CHART_INDEX.get((icao or "").upper(), {}).get(number)
    if not metadata:
        return chart
    return {
        **chart,
        "title": metadata.get("title", chart.get("title", "")),
        "procedureTitle": metadata.get("title", ""),
        "runways": metadata.get("runways", []),
        "indexed": True,
    }


def indexed_charts_for_runway(icao, charts, runway):
    target = normalize_runway(runway)
    if not target:
        return charts
    return [
        chart
        for chart in charts
        if target in {normalize_runway(value) for value in chart.get("runways", [])}
    ]


def static_charts_for_runway(icao, runway):
    target = normalize_runway(runway)
    if not target:
        return []
    index = STATIC_CHART_INDEX.get((icao or "").upper(), {})
    charts = []
    for number, metadata in sorted(index.items()):
        runways = {normalize_runway(value) for value in metadata.get("runways", [])}
        if target in runways:
            charts.append(chart_entry((icao or "").upper(), number, metadata))
    return charts


def pdf_looks_valid(url):
    request = Request(url, headers={**_HEADERS, "Range": "bytes=0-7"})
    try:
        with urlopen(request, timeout=_SCAN_TIMEOUT, context=_SSL_CONTEXT) as response:
            content_type = response.headers.get("content-type", "").lower()
            signature = response.read(5)
            return signature == b"%PDF-" or "pdf" in content_type
    except (HTTPError, URLError, TimeoutError):
        return False


def discover_charts(icao):
    icao = (icao or "").upper()
    now = time.time()
    cached = _chart_cache.get(icao)
    if cached and now - cached["time"] < CACHE_TTL_SECONDS:
        return cached["charts"]

    found = []
    with ThreadPoolExecutor(max_workers=_SCAN_WORKERS) as executor:
        checks = {}
        for number in range(1, PDF_SCAN_LIMIT + 1):
            file_name = pdf_name(icao, number)
            source_url = pdf_url(file_name)
            checks[executor.submit(pdf_looks_valid, source_url)] = (number, file_name, source_url)
        for future in as_completed(checks):
            number, file_name, source_url = checks[future]
            try:
                is_valid = future.result()
            except Exception:
                is_valid = False
            if is_valid:
                found.append((number, file_name, source_url))

    charts = []
    for number, file_name, source_url in sorted(found):
        charts.append(chart_entry(icao, number))

    charts = [enrich_chart_metadata(icao, chart) for chart in charts]
    _chart_cache[icao] = {"time": now, "charts": charts}
    return charts


def validate_pdf_file(file_name):
    match = PDF_RE.match(file_name or "")
    if not match:
        raise ValueError("Bad PDF path")
    if not is_valid_icao(match.group(1)):
        raise ValueError("Unknown Turkish airport")


def get_pdf_bytes(file_name):
    validate_pdf_file(file_name)
    request = Request(pdf_url(file_name), headers=_HEADERS)
    with urlopen(request, timeout=_DOWNLOAD_TIMEOUT, context=_SSL_CONTEXT) as response:
        content_type = response.headers.get("content-type", "").lower()
        data = response.read()
    if not data.startswith(b"%PDF-") and "pdf" not in content_type:
        raise ValueError("Not a displayable PDF")
    return data
