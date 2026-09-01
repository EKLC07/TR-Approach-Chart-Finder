from pathlib import Path
import os


PORT = int(os.environ.get("PORT", "8787"))
ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "outputs"
WORK_DIR = ROOT_DIR / "work"

DHMI_BASE = "https://www.dhmi.gov.tr/AIPDocuments"
OURAIRPORTS_RUNWAYS_CSV = "https://davidmegginson.github.io/ourairports-data/runways.csv"

PDF_SCAN_LIMIT = 80
CACHE_TTL_SECONDS = 60 * 60 * 6
