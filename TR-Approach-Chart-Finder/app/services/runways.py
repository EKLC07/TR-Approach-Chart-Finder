import csv
from io import StringIO
from urllib.request import urlopen

from app.config import OURAIRPORTS_RUNWAYS_CSV
from app.data.airports import ALLOWED_ICAOS


_runway_cache = None


def as_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_runways():
    global _runway_cache
    if _runway_cache is not None:
        return _runway_cache

    with urlopen(OURAIRPORTS_RUNWAYS_CSV, timeout=20) as response:
        text = response.read().decode("utf-8", errors="replace")

    by_airport = {}
    for row in csv.DictReader(StringIO(text)):
        icao = row.get("airport_ident", "")
        if icao not in ALLOWED_ICAOS:
            continue

        le_heading = as_number(row.get("le_heading_degT") or row.get("le_heading_deg"))
        he_heading = as_number(row.get("he_heading_degT") or row.get("he_heading_deg"))
        runway = {
            "ident": f"{row.get('le_ident')}/{row.get('he_ident')}" if row.get("le_ident") and row.get("he_ident") else row.get("le_ident") or row.get("he_ident") or "RWY",
            "le": row.get("le_ident") or "",
            "he": row.get("he_ident") or "",
            "heading": le_heading if le_heading is not None else ((he_heading + 180) % 360 if he_heading is not None else None),
            "reciprocalHeading": he_heading if he_heading is not None else ((le_heading + 180) % 360 if le_heading is not None else None),
            "lengthFt": as_number(row.get("length_ft")),
            "widthFt": as_number(row.get("width_ft")),
            "surface": row.get("surface") or "",
            "lighted": row.get("lighted") == "1",
        }
        by_airport.setdefault(icao, []).append(runway)

    _runway_cache = by_airport
    return by_airport
