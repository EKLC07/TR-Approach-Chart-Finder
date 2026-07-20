# TR Approach Chart Finder

Turkey approach chart finder and training helper for publicly available DHMI AIP PDF charts.

The app runs a local Node.js server, scans public DHMI approach chart PDFs for Turkish airports, shows validated charts in the browser, and provides chart-reading prompts for training use.

## Features

- Search Turkish airports by ICAO/IATA, city, or airport name
- Discover public approach chart PDFs from DHMI AIP documents
- View selected PDFs in the browser
- Show runway data from OurAirports
- Provide training-oriented chart briefing help
- Optional local address: `http://tr-approach-chart-finder.local:8787`

## Requirements

- Node.js 18 or newer
- Internet access for DHMI AIP PDFs and OurAirports runway data
- Optional: Python with `pypdf` if you want the PDF text extraction helper paths to work outside the original Codex runtime

## Windows Install

1. Click the green `Code` button on GitHub.
2. Click `Download ZIP`.
3. Extract the ZIP file.
4. Double-click `install-windows.cmd`.

The installer checks for Node.js, creates a desktop shortcut, and starts the app.

## Run

From the project folder:

```powershell
npm start
```

Then open:

```text
http://localhost:8787
```

On Windows, you can also run:

```powershell
.\outputs\start-chartlab.cmd
```

## Project Structure

```text
outputs/
  server.js
  turkiye-chart-finder.html
  start-chartlab.cmd
  setup-custom-address-admin.cmd
  tr-approach-chart-finder.ico
```

`work/` is used for local cache files, downloaded temporary PDFs, and logs. It is intentionally ignored by Git.

## Notes

This tool is for training and chart-reading assistance. Always verify current operational aeronautical information from official sources before flight use.
