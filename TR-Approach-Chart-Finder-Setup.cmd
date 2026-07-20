@echo off
setlocal
cd /d "%~dp0"

echo TR Approach Chart Finder kurulumu
echo.

set "NODE_EXE=%CD%\.runtime\node\node.exe"

if not exist "%NODE_EXE%" (
  echo Gerekli calisma motoru hazirlaniyor...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $runtime=Join-Path $root '.runtime'; $zip=Join-Path $env:TEMP 'tr-approach-node.zip'; New-Item -ItemType Directory -Force -Path $runtime | Out-Null; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $versions=Invoke-RestMethod 'https://nodejs.org/dist/index.json'; $v=$versions | Where-Object { $_.lts -and ($_.files -contains 'win-x64-zip') } | Select-Object -First 1; if(-not $v){ throw 'Node.js LTS win-x64 paketi bulunamadi.' }; $url='https://nodejs.org/dist/' + $v.version + '/node-' + $v.version + '-win-x64.zip'; Invoke-WebRequest -Uri $url -OutFile $zip; Expand-Archive -LiteralPath $zip -DestinationPath $runtime -Force; $dir=Get-ChildItem -LiteralPath $runtime -Directory -Filter 'node-*-win-x64' | Select-Object -First 1; if(Test-Path -LiteralPath (Join-Path $runtime 'node')){ Remove-Item -LiteralPath (Join-Path $runtime 'node') -Recurse -Force }; Move-Item -LiteralPath $dir.FullName -Destination (Join-Path $runtime 'node'); Remove-Item -LiteralPath $zip -Force"
  if errorlevel 1 (
    echo.
    echo Otomatik kurulum tamamlanamadi.
    echo Internet baglantinizi kontrol edip tekrar deneyin.
    pause
    exit /b 1
  )
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
