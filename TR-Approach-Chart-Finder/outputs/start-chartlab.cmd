@echo off
setlocal
cd /d "%~dp0.."
set "PORT=8787"
set "PYTHON_EXE=%CD%\.runtime\python\python.exe"

if not exist "%PYTHON_EXE%" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Required Python runtime was not found.
    echo.
    echo Please run TR-Approach-Chart-Finder-Setup.cmd from the main folder first.
    echo.
    pause
    exit /b 1
  )
  set "PYTHON_EXE=python"
)

start "TR Approach Chart Finder Server" /min "%PYTHON_EXE%" -m app.main
timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"
endlocal
