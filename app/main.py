import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from app.config import PORT, STATIC_DIR
from app.data.airports import AIRPORTS, find_airport, is_valid_icao
from app.services.airport_info import airport_info
from app.services.assistant import assist
from app.services.charts import discover_charts, get_pdf_bytes
from app.services.runways import load_runways


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
                    return self.send_json(400, {"error": "Only registered Turkey ICAO codes are supported."})
                return self.send_json(200, airport_info(icao, lang))

            if path == "/api/charts":
                icao = (query.get("icao", [""])[0] or "").upper()
                if not is_valid_icao(icao):
                    return self.send_json(400, {"error": "Only registered Turkey ICAO codes are supported."})
                charts = discover_charts(icao)
                return self.send_json(200, {"airport": find_airport(icao), "charts": charts, "runway": query.get("runway", [None])[0], "source": "public validated PDFs"})

            if path == "/api/runways":
                icao = (query.get("icao", [""])[0] or "").upper()
                if not is_valid_icao(icao):
                    return self.send_json(400, {"error": "Only registered Turkey ICAO codes are supported."})
                return self.send_json(200, {"airport": find_airport(icao), "runways": load_runways().get(icao, []), "source": "OurAirports open data"})

            if path == "/api/coverage":
                rows = []
                for airport in AIRPORTS:
                    charts = discover_charts(airport["icao"])
                    if charts:
                        rows.append({**airport, "charts": len(charts)})
                rows.sort(key=lambda item: (-item["charts"], item["icao"]))
                return self.send_json(200, {"airports": rows})

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
        if parsed.path != "/api/assist":
            return self.send_text(404, "Not found")

        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            lang = "en" if payload.get("lang") == "en" else "tr"
            return self.send_json(200, assist(str(payload.get("file", "")), str(payload.get("question", "")), lang))
        except Exception as exc:
            return self.send_json(400, {"error": str(exc)})

    def serve_static(self, request_path):
        file_path = STATIC_DIR / "turkiye-chart-finder.html" if request_path == "/" else STATIC_DIR / request_path.lstrip("/")
        file_path = file_path.resolve()
        static_root = STATIC_DIR.resolve()
        if not str(file_path).startswith(str(static_root)):
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
