# Wind Forecast Portal - PowerShell Launch Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting Wind Forecast Portal (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"

Write-Host "Launching Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; .\.venv\Scripts\uvicorn windportal.main:app --reload --port 8000"

Write-Host "Launching Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm run dev"

Write-Host ""
Write-Host "Servers launched in separate PowerShell windows!" -ForegroundColor Yellow
Write-Host "- Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/api/docs)"
Write-Host "- Frontend: http://localhost:5173"
Write-Host "========================================================" -ForegroundColor Cyan
