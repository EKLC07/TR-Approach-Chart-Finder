@echo off
setlocal
cd /d "%~dp0"

echo TR Approach Chart Finder kaldirma araci
echo.

set "SHORTCUT=%USERPROFILE%\Desktop\TR Approach Chart Finder.lnk"

if exist "%SHORTCUT%" (
  del "%SHORTCUT%" >nul 2>nul
  echo Masaustu kisayolu kaldirildi.
) else (
  echo Masaustu kisayolu bulunamadi.
)

echo Calisan yerel uygulama surecleri kontrol ediliyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=(Resolve-Path '.').Path; Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -like ('*' + $root + '*server.js*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

if exist "%CD%\.runtime" (
  rmdir /s /q "%CD%\.runtime"
  echo Yerel calisma motoru kaldirildi.
)

if exist "%CD%\work" (
  rmdir /s /q "%CD%\work"
  echo Gecici cache dosyalari kaldirildi.
)

echo.
echo Kaldirma tamamlandi.
echo Proje klasorunu tamamen silmek isterseniz bu klasoru manuel silebilirsiniz.
pause
endlocal
