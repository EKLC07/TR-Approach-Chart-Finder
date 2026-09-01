# TR Approach Chart Finder

TR Approach Chart Finder is a local web app for finding and reviewing public DHMI AIP approach charts for airports in Turkey.

This version uses a Python backend, so the project is easier to read, modify, and extend from Python.

## Easy Windows Setup

1. Click the green Code button on GitHub.
2. Select Download ZIP.
3. Extract the ZIP file.
4. Double-click TR-Approach-Chart-Finder-Setup.cmd.

The setup file prepares the required portable Python runtime automatically, creates a desktop shortcut, and starts the app.

## How To Use

After setup, double-click the TR Approach Chart Finder shortcut on your desktop.

The app runs locally in your browser.

## Uninstall

To remove the desktop shortcut and local runtime files, double-click TR-Approach-Chart-Finder-Uninstall.cmd.

After uninstalling, you can delete the project folder if you no longer need it.

## Project Structure

- app/main.py starts the local web server.
- app/data/airports.py stores airport data.
- app/services/charts.py finds and serves chart PDFs.
- app/services/runways.py loads runway data.
- app/services/airport_info.py builds airport notes.
- app/services/assistant.py builds chart-reading help.
- outputs/turkiye-chart-finder.html is the browser interface.

## Important Note

This app is for flight simulation, training, and chart-reading support only. Always verify current operational aeronautical information from official sources before real flight use.
