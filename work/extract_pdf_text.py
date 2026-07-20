import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pypdf import PdfReader
reader = PdfReader(sys.argv[1])
parts = []
for page in reader.pages[:2]:
    parts.append(page.extract_text() or '')
print('\n'.join(parts)[:12000])