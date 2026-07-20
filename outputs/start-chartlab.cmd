@echo off
setlocal
cd /d "%~dp0"
set "PORT=8787"
set "NODE_EXE=%~dp0..\.runtime\node\node.exe"

if not exist "%NODE_EXE%" (
  where node >nul 2>nul
  if errorlevel 1 (
    echo Calisma motoru bulunamadi.
    echo.
    echo Lutfen once ana klasordeki install-windows.cmd dosyasini calistirin.
    echo.
    pause
    exit /b 1
  )
  set "NODE_EXE=node"
)

start "TR Approach Chart Finder Server" /min "%NODE_EXE%" server.js
timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"
endlocal
