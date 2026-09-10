import json
import mimetypes
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from app.config import OWNER_TOOLS_DIR, PORT, STATIC_DIR
from app.data.airports import AIRPORTS, find_airport, is_valid_icao
from app.services.airport_info import airport_info
from app.services.assistant import assist, capabilities
from app.services.chart_analysis import analyze_chart, chart_runways
from app.services.charts import discover_charts, get_pdf_bytes, static_charts_for_runway
from app.services.runways import load_runways
from app.ai.trainer import add_training_item, train_from_chat, training_overview


def owner_training_enabled():
    return (OWNER_TOOLS_DIR / ".owner-mode").exists()


def normalize_runway(value):
    return re.sub(r"[^0-9A-Z]", "", str(value or "").upper().replace("RWY", ""))


def filter_charts_by_runway(charts, runway, airport):
    target = normalize_runway(runway)
    if not target:
        return charts

    filtered = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        checks = {
            executor.submit(chart_runways, chart.get("file", ""), airport): chart
            for chart in charts
        }
        for future in as_completed(checks):
            chart = checks[future]
            try:
                runways = future.result()
            except Exception:
                runways = []
            chart = {**chart, "runways": runways}
            if target in {normalize_runway(value) for value in runways}:
                filtered.append(chart)

    return sorted(filtered, key=lambda item: item.get("id", ""))


def first_chart_for_runway(charts, runway, airport):
    target = normalize_runway(runway)
    if not target:
        return charts[0] if charts else None

    ordered = sorted(charts, key=lambda item: item.get("id", ""))
    chunk_size = 6
    for start in range(0, len(ordered), chunk_size):
        chunk = ordered[start:start + chunk_size]
        with ThreadPoolExecutor(max_workers=chunk_size) as executor:
            checks = {
                executor.submit(chart_runways, chart.get("file", ""), airport): index
                for index, chart in enumerate(chunk)
            }
            runways_by_index = {}
            for future in as_completed(checks):
                index = checks[future]
                try:
                    runways_by_index[index] = future.result()
                except Exception:
                    runways_by_index[index] = []

        for index, chart in enumerate(chunk):
            runways = runways_by_index.get(index, [])
            if target in {normalize_runway(value) for value in runways}:
                return {**chart, "runways": runways}

    return None


class ChartFinderHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, status, text):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/plain; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = unquote(parsed.path)

        try:
            if path == "/api/airports":
                return self.send_json(200, {"airports": AIRPORTS, "sources": ["DHMI public AIP PDF", "Direct public PDF validation"]})

            if path == "/api/airport-info":
                icao = (query.get("icao", [""])[0] or "").upper()
                lang = "en" if query.get("lang", ["tr"])[0] == "en" else "tr"
                if not is_valid_icao(icao):
                    return self.send_json(400, {"error": "Only registered Türkiye ICAO codes are supported."})
                return self.send_json(200, airport_info(icao, lang))

            if path == "/api/charts":
                icao = (query.get("icao", [""])[0] or "").upper()
                runway = normalize_runway(query.get("runway", [""])[0])
                if not is_valid_icao(icao):
                    return self.send_json(400, {"error": "Only registered Türkiye ICAO codes are supported."})
                charts = discover_charts(icao)
                if runway:
                    charts = static_charts_for_runway(icao, runway) or filter_charts_by_runway(charts, runway, icao)
                return self.send_json(200, {"airport": find_airport(icao), "charts": charts, "runway": runway or None, "source": "public validated PDFs"})

            if path == "/api/chart-match":
                icao = (query.get("icao", [""])[0] or "").upper()
                runway = normalize_runway(query.get("runway", [""])[0])
                if not is_valid_icao(icao):
                    return self.send_json(400, {"error": "Only registered Türkiye ICAO codes are supported."})
                if not runway:
                    return self.send_json(400, {"error": "Runway is required."})
                indexed = static_charts_for_runway(icao, runway)
                if indexed:
                    chart = indexed[0]
                else:
                    charts = discover_charts(icao)
                    chart = first_chart_for_runway(charts, runway, icao)
                return self.send_json(200, {
                    "airport": find_airport(icao),
                    "chart": chart,
                    "charts": [chart] if chart else [],
                    "runway": runway,
                    "source": "public validated PDFs",
                })

            if path == "/api/runways":
                icao = (query.get("icao", [""])[0] or "").upper()
                if not is_valid_icao(icao):
                    return self.send_json(400, {"error": "Only registered Türkiye ICAO codes are supported."})
                return self.send_json(200, {"airport": find_airport(icao), "runways": load_runways().get(icao, []), "source": "OurAirports open data"})

            if path == "/api/coverage":
                rows = []
                for airport in AIRPORTS:
                    charts = discover_charts(airport["icao"])
                    if charts:
                        rows.append({**airport, "charts": len(charts)})
                rows.sort(key=lambda item: (-item["charts"], item["icao"]))
                return self.send_json(200, {"airports": rows})

            if path == "/api/assistant/capabilities":
                return self.send_json(200, capabilities())

            if path == "/api/training/overview":
                if not owner_training_enabled():
                    return self.send_text(404, "Not found")
                return self.send_json(200, training_overview())

            if path == "/api/chart-analysis":
                file_name = query.get("file", [""])[0]
                airport = query.get("airport", [""])[0]
                lang = "en" if query.get("lang", ["tr"])[0] == "en" else "tr"
                return self.send_json(200, analyze_chart(file_name, airport, lang))

            if path.startswith("/api/pdf/"):
                file_name = path.removeprefix("/api/pdf/")
                data = get_pdf_bytes(file_name)
                self.send_response(200)
                self.send_header("content-type", "application/pdf")
                self.send_header("content-disposition", f'inline; filename="{file_name}"')
                self.send_header("cache-control", "public, max-age=21600")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            return self.serve_static(path)
        except Exception as exc:
            return self.send_json(500, {"error": str(exc)})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/assist", "/api/training/add", "/api/training/chat"}:
            return self.send_text(404, "Not found")

        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")

            if parsed.path == "/api/training/add":
                if not owner_training_enabled():
                    return self.send_text(404, "Not found")
                return self.send_json(200, add_training_item(
                    str(payload.get("kind", "")),
                    str(payload.get("lang", "")),
                    str(payload.get("text", "")),
                    str(payload.get("intent", "")),
                ))

            if parsed.path == "/api/training/chat":
                if not owner_training_enabled():
                    return self.send_text(404, "Not found")
                return self.send_json(200, train_from_chat(
                    str(payload.get("message", "")),
                    str(payload.get("lang", "auto")),
                ))

            lang = "en" if payload.get("lang") == "en" else "tr"
            return self.send_json(200, assist(
                str(payload.get("file", "")),
                str(payload.get("question", "")),
                lang,
                str(payload.get("airport", "")),
                payload.get("history", []),
            ))
        except Exception as exc:
            return self.send_json(400, {"error": str(exc)})

    def serve_static(self, request_path):
        if request_path == "/":
            file_path = STATIC_DIR / "turkiye-chart-finder.html"
        elif request_path in {"/ciguli-trainer", "/ciguli-trainer/"}:
            if not owner_training_enabled():
                return self.send_text(404, "Not found")
            file_path = OWNER_TOOLS_DIR / "ciguli-trainer.html"
        else:
            file_path = STATIC_DIR / request_path.lstrip("/")
        file_path = file_path.resolve()
        static_root = STATIC_DIR.resolve()
        owner_root = OWNER_TOOLS_DIR.resolve()
        if not (str(file_path).startswith(str(static_root)) or str(file_path).startswith(str(owner_root))):
            return self.send_text(403, "Forbidden")
        if not file_path.exists() or not file_path.is_file():
            return self.send_text(404, "Not found")

        data = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), ChartFinderHandler)
    print(f"TR Approach Chart Finder running at http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
