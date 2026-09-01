import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import CACHE_TTL_SECONDS, DHMI_BASE, PDF_SCAN_LIMIT
from app.data.airports import is_valid_icao


PDF_RE = re.compile(r"^LT_AD_2_(LT[A-Z0-9]{2})_IAC_\d{2}_en\.pdf$")
_chart_cache = {}


def pdf_name(icao, number):
    return f"LT_AD_2_{icao}_IAC_{number:02d}_en.pdf"


def pdf_url(file_name):
    return f"{DHMI_BASE}/{file_name}"


def pdf_looks_valid(url):
    request = Request(url, headers={"Range": "bytes=0-7", "User-Agent": "TR-Approach-Chart-Finder"})
    try:
        with urlopen(request, timeout=12) as response:
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

    charts = []
    for number in range(1, PDF_SCAN_LIMIT + 1):
        file_name = pdf_name(icao, number)
        source_url = pdf_url(file_name)
        if not pdf_looks_valid(source_url):
            continue
        charts.append({
            "id": f"IAC {number:02d}",
            "title": f"Instrument Approach Chart {number:02d}",
            "file": file_name,
            "viewerUrl": f"/api/pdf/{file_name}",
            "sourceUrl": source_url,
            "source": "DHMI public AIP PDF",
            "runways": [],
        })

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
    request = Request(pdf_url(file_name), headers={"User-Agent": "TR-Approach-Chart-Finder"})
    with urlopen(request, timeout=25) as response:
        content_type = response.headers.get("content-type", "").lower()
        data = response.read()
    if not data.startswith(b"%PDF-") and "pdf" not in content_type:
        raise ValueError("Not a displayable PDF")
    return data
