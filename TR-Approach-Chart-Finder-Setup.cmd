@echo off
setlocal
cd /d "%~dp0"

echo TR Approach Chart Finder setup
echo.

set "PORT=8787"
set "PYTHON_EXE=%CD%\.runtime\python\python.exe"
set "PYTHON_ZIP=%CD%\.runtime\python\python312.zip"
set "PYTHON_PTH=%CD%\.runtime\python\python312._pth"

echo Closing old app server if it is still running...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  if not "%%P"=="0" taskkill /PID %%P /F >nul 2>nul
)
echo.

if not exist "%PYTHON_EXE%" goto prepare_runtime
if not exist "%PYTHON_ZIP%" goto prepare_runtime
if not exist "%PYTHON_PTH%" goto prepare_runtime
"%PYTHON_EXE%" -c "import encodings, ssl" >nul 2>nul
if errorlevel 1 goto prepare_runtime
goto runtime_ready

:prepare_runtime
  echo Preparing required portable Python runtime...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $runtime=Join-Path $root '.runtime'; $pythonDir=Join-Path $runtime 'python'; $zip=Join-Path $env:TEMP 'tr-approach-python.zip'; New-Item -ItemType Directory -Force -Path $runtime | Out-Null; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $url='https://www.python.org/ftp/python/3.12.5/python-3.12.5-embed-amd64.zip'; Invoke-WebRequest -Uri $url -OutFile $zip; if(Test-Path -LiteralPath $pythonDir){ Remove-Item -LiteralPath $pythonDir -Recurse -Force }; New-Item -ItemType Directory -Force -Path $pythonDir | Out-Null; Expand-Archive -LiteralPath $zip -DestinationPath $pythonDir -Force; $pth=Get-ChildItem -LiteralPath $pythonDir -Filter 'python*._pth' | Select-Object -First 1; if($pth){ $zipName=(Get-ChildItem -LiteralPath $pythonDir -Filter 'python*.zip' | Select-Object -First 1).Name; Set-Content -LiteralPath $pth.FullName -Encoding ASCII -Value @($zipName,'.','..\..','import site') }; Remove-Item -LiteralPath $zip -Force"
  if errorlevel 1 (
    echo.
    echo Automatic setup failed.
    echo Check your internet connection and run this file again.
    pause
    exit /b 1
  )

:runtime_ready

echo Repairing portable Python path...
set "EMBED_ZIP="
for %%Z in ("%CD%\.runtime\python\python*.zip") do set "EMBED_ZIP=%%~nxZ"
set "EMBED_PTH="
for %%P in ("%CD%\.runtime\python\python*._pth") do set "EMBED_PTH=%%~fP"
if defined EMBED_ZIP if defined EMBED_PTH (
  > "%EMBED_PTH%" echo %EMBED_ZIP%
  >> "%EMBED_PTH%" echo .
  >> "%EMBED_PTH%" echo ..\..
  >> "%EMBED_PTH%" echo import site
)
echo.

echo Verifying app modules...
if not exist "%CD%\app\services\chart_analysis.py" (
  echo.
  echo App files were not found in this folder.
  echo Open the extracted project folder that contains app, outputs and this setup file.
  pause
  exit /b 1
)
set "VERIFY_LOG=%TEMP%\tr-chartlab-verify-error.txt"
"%PYTHON_EXE%" -c "from app.services.chart_analysis import analyze_chart; print('ok')" >nul 2>"%VERIFY_LOG%"
if errorlevel 1 (
  echo.
  echo App module verification failed.
  echo Details:
  type "%VERIFY_LOG%"
  echo.
  echo Please run this setup from the extracted project folder that contains app and outputs.
  pause
  exit /b 1
)

set "SHORTCUT=%USERPROFILE%\Desktop\TR Approach Chart Finder.lnk"
set "TARGET=%CD%\outputs\start-chartlab.cmd"
set "ICON=%CD%\outputs\tr-approach-chart-finder.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%CD%'; $s.IconLocation='%ICON%'; $s.Save()"

echo Desktop shortcut created:
echo %SHORTCUT%
echo.

echo Starting app...
call "%TARGET%"
endlocal
