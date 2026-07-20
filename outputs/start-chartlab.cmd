@echo off
setlocal
cd /d "%~dp0"
set "NODE_EXE=C:\Users\Enes\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
set "PORT=8787"
start "TR Approach Chart Finder Server" /min "%NODE_EXE%" server.js
timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"
endlocal
