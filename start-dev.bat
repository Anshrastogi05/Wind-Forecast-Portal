@echo off
title Wind Forecast Portal Launcher
echo ========================================================
echo   Starting Wind Forecast Portal (Backend + Frontend)
echo ========================================================

REM Start Backend server in a new window
echo Starting FastAPI Backend on port 8000...
start "Wind Forecast - Backend" cmd /k "cd /d "%~dp0backend" && .\.venv\Scripts\uvicorn windportal.main:app --reload --port 8000"

REM Start Frontend dev server in a new window
echo Starting Vite Frontend on port 5173...
start "Wind Forecast - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are launching in separate windows!
echo - Backend API:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/api/docs)
echo - Frontend UI:  http://localhost:5173
echo ========================================================
pause
