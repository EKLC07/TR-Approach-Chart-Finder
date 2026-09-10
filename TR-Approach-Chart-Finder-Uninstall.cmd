@echo off
setlocal
cd /d "%~dp0"

echo TR Approach Chart Finder uninstall
echo.

set "SHORTCUT=%USERPROFILE%\Desktop\TR Approach Chart Finder.lnk"

if exist "%SHORTCUT%" (
  del "%SHORTCUT%" >nul 2>nul
  echo Desktop shortcut removed.
) else (
  echo Desktop shortcut was not found.
)

echo Checking local app processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=(Resolve-Path '.').Path; Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like ('*' + $root + '*app.main*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

if exist "%CD%\.runtime" (
  rmdir /s /q "%CD%\.runtime"
  echo Local runtime removed.
)

if exist "%CD%\work" (
  rmdir /s /q "%CD%\work"
  echo Local cache removed.
)

echo.
echo Uninstall complete.
echo You can delete this project folder manually if you no longer need it.
pause
endlocal
