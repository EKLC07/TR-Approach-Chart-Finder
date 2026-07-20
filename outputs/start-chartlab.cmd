@echo off
setlocal
cd /d "%~dp0"
set "PORT=8787"

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js bulunamadi.
  echo.
  echo Lutfen once Node.js LTS surumunu kurun:
  echo https://nodejs.org/
  echo.
  pause
  exit /b 1
)

start "TR Approach Chart Finder Server" /min node server.js
timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"
endlocal
