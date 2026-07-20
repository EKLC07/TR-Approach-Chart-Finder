@echo off
setlocal
cd /d "%~dp0"

echo TR Approach Chart Finder kurulumu
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js bulunamadi.
  echo.
  echo Bu uygulamayi calistirmak icin Node.js LTS kurulu olmali.
  echo Indirme sayfasi aciliyor...
  start "" "https://nodejs.org/"
  echo.
  echo Node.js kurulduktan sonra bu dosyayi tekrar calistirin.
  pause
  exit /b 1
)

set "SHORTCUT=%USERPROFILE%\Desktop\TR Approach Chart Finder.lnk"
set "TARGET=%CD%\outputs\start-chartlab.cmd"
set "ICON=%CD%\outputs\tr-approach-chart-finder.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%CD%\outputs'; $s.IconLocation='%ICON%'; $s.Save()"

echo Masaustune kisayol eklendi:
echo %SHORTCUT%
echo.
echo Uygulama baslatiliyor...
call "%TARGET%"
endlocal
