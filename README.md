# TR Approach Chart Finder

TR Approach Chart Finder is a local web app for finding and reviewing public DHMI AIP approach charts for airports in Türkiye.

This version uses a Python backend, so the project is easier to read, modify, and extend from Python.

## Easy Windows Setup

1. Click the green Code button on GitHub.
2. Select Download ZIP.
3. Extract the ZIP file.
4. Double-click TR-Approach-Chart-Finder-Setup.cmd.

The setup file prepares the required portable Python runtime automatically, creates a desktop shortcut, and starts the app. The user does not need to install Node.js, Python, or extra packages manually.

## How To Use

After setup, double-click the TR Approach Chart Finder shortcut on your desktop.

The app runs locally in your browser at localhost:8787.

## Uninstall

To remove the desktop shortcut and local runtime files, double-click TR-Approach-Chart-Finder-Uninstall.cmd.

After uninstalling, you can delete the project folder if you no longer need it.

## Project Structure

- app/main.py starts the local web server.
- app/data/airports.py stores airport data.
- app/services/charts.py finds and serves chart PDFs.
- app/services/runways.py loads runway data.
- app/services/airport_info.py builds airport notes.
- app/services/assistant.py connects the web app to the assistant engine.
- app/ai/engine.py contains the main assistant logic.
- app/ai/knowledge.py contains aviation topic responses.
- app/ai/daily_talk.py contains Turkish/English everyday conversation behavior.
- app/ai/vocabulary.py loads the Turkish/English vocabulary bank.
- app/ai/trainer.py saves owner-only assistant training data.
- app/ai/language.py contains Turkish/English language detection helpers.
- app/ai/training_data/ contains notes and examples you can edit to shape Ciguli.
- tools/build_ciguli_language_bank.py rebuilds Ciguli's Turkish/English language bank.
- outputs/turkiye-chart-finder.html is the browser interface.
- owner-tools/ contains owner-only development and training tools. Do not include this folder in public customer builds.

## Assistant Direction

The assistant panel is being shaped as the product brain of the app. The assistant character is named **Ciguli**:

- Turkish and English conversation
- Turkish and English everyday small talk
- Expandable Turkish/English vocabulary bank with 3000+ entries per language
- Turkish/English phrase banks for more varied daily conversation
- English phrasal verbs and Turkish idiomatic action phrases such as “göz at”, “üstünden geç”, and “el at”
- Local Turkish daily expressions such as “selamın aleyküm”, “aleyküm selam”, “hacı”, “hoca”, “reis”, and “kral”
- Aviation and simulator-focused personality
- Chart briefing, minimums, missed approach, runway, and airport-awareness help
- Chat-style interface with message history
- Local Python-based Ciguli Core for simple conversation and aviation help
- Local conversation memory so Ciguli can personalize itself over time

Easy setup:

1. Double-click TR-Approach-Chart-Finder-Setup.cmd.
2. The installer prepares Python and creates the desktop shortcut.
3. Start chatting; Ciguli creates its local memory while you use it.

## Ciguli Memory

Ciguli learns user preferences from conversation over time and stores them locally in:

- app/ai/ciguli_memory.local.json

## Ciguli Language Bank

Ciguli's starter language bank is stored in:

- app/ai/training_data/vocabulary_tr.txt
- app/ai/training_data/vocabulary_en.txt
- app/ai/training_data/phrase_bank_tr.json
- app/ai/training_data/phrase_bank_en.json

Current starter target:

- Turkish: 16000+ entries
- English: 16000+ entries

To rebuild the language bank, run tools/build_ciguli_language_bank.py from the project folder.

## Owner Training

The customer-facing app does not show assistant training tools.


## Important Note

This app is for flight simulation, training, and chart-reading support only. Always verify current operational aeronautical information from official sources before real flight use.
