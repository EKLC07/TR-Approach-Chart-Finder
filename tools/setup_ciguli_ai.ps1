$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$aiDir = Join-Path $projectRoot "app\ai"

Write-Host ""
Write-Host "Ciguli Local AI Setup" -ForegroundColor Cyan
Write-Host "Ciguli runs locally with its own Python brain." -ForegroundColor Gray
Write-Host "It will personalize itself later by remembering conversations on this computer." -ForegroundColor Gray
Write-Host ""
Write-Host "No API key is required." -ForegroundColor Green
Write-Host "Ciguli memory will be created automatically while the user chats:" -ForegroundColor Green
Write-Host (Join-Path $aiDir "ciguli_memory.local.json")
Write-Host ""
