@echo off
setlocal
set "HOSTS=%SystemRoot%\System32\drivers\etc\hosts"
set "ENTRY=127.0.0.1 tr-approach-chart-finder.local"

net session >nul 2>&1
if not "%errorlevel%"=="0" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

findstr /C:"tr-approach-chart-finder.local" "%HOSTS%" >nul 2>&1
if "%errorlevel%"=="0" (
  echo Address already exists.
) else (
  echo %ENTRY%>>"%HOSTS%"
  echo Added: %ENTRY%
)

ipconfig /flushdns >nul
echo.
echo Custom address is ready:
echo http://tr-approach-chart-finder.local:8787
echo.
pause
endlocal
