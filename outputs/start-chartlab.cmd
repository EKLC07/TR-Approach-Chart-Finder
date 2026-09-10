@echo off
setlocal
cd /d "%~dp0.."
set "PORT=8787"
set "PYTHON_EXE=%CD%\.runtime\python\python.exe"
set "PYTHON_ZIP=%CD%\.runtime\python\python312.zip"
set "PYTHON_PTH=%CD%\.runtime\python\python312._pth"

if not exist "%PYTHON_EXE%" goto missing_runtime
if not exist "%PYTHON_ZIP%" goto missing_runtime
if not exist "%PYTHON_PTH%" goto missing_runtime
"%PYTHON_EXE%" -c "import encodings, ssl" >nul 2>nul
if errorlevel 1 goto missing_runtime
goto start_app

:missing_runtime
  where python >nul 2>nul
  if errorlevel 1 (
    echo Required Python runtime is missing or incomplete.
    echo.
    echo Please run TR-Approach-Chart-Finder-Setup.cmd from the main folder first.
    echo.
    pause
    exit /b 1
  )
  set "PYTHON_EXE=python"

:start_app

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  if not "%%P"=="0" taskkill /PID %%P /F >nul 2>nul
)
timeout /t 1 /nobreak >nul

start "TR Approach Chart Finder Server" /min "%PYTHON_EXE%" -m app.main
timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"
endlocal
