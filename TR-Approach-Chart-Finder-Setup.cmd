@echo off
setlocal
cd /d "%~dp0"

echo TR Approach Chart Finder setup
echo.

set "PYTHON_EXE=%CD%\.runtime\python\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Preparing required portable Python runtime...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $runtime=Join-Path $root '.runtime'; $pythonDir=Join-Path $runtime 'python'; $zip=Join-Path $env:TEMP 'tr-approach-python.zip'; New-Item -ItemType Directory -Force -Path $runtime | Out-Null; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $url='https://www.python.org/ftp/python/3.12.5/python-3.12.5-embed-amd64.zip'; Invoke-WebRequest -Uri $url -OutFile $zip; if(Test-Path -LiteralPath $pythonDir){ Remove-Item -LiteralPath $pythonDir -Recurse -Force }; New-Item -ItemType Directory -Force -Path $pythonDir | Out-Null; Expand-Archive -LiteralPath $zip -DestinationPath $pythonDir -Force; $pth=Get-ChildItem -LiteralPath $pythonDir -Filter 'python*._pth' | Select-Object -First 1; if($pth){ Add-Content -LiteralPath $pth.FullName -Value '..\..' }; Remove-Item -LiteralPath $zip -Force"
  if errorlevel 1 (
    echo.
    echo Automatic setup failed.
    echo Check your internet connection and run this file again.
    pause
    exit /b 1
  )
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
