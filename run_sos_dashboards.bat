@echo off
setlocal enabledelayedexpansion
title TerraTwin SOS — Archived Disaster Dispatch System

echo ======================================================================
echo   TerraTwin SOS — Archived Multi-Hazard Digital Twin & Dispatch HUD
echo   [Status: Archived Hackathon Project ^| Read-Only Local Server]
echo ======================================================================
echo.

:: 1. Navigate to script directory
cd /d "%~dp0"

:: 2. Resolve Conda Python or Local Virtual Environment
set "PYTHON_EXE="

if exist "%~dp0envs\digital-twin\python.exe" (
    set "PYTHON_EXE=%~dp0envs\digital-twin\python.exe"
    echo [*] Found dedicated local environment: envs\digital-twin\python.exe
) else (
    :: Fallback: Try system conda activation
    call conda activate digital-twin >nul 2>&1
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%i in ('where python') do (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
        )
        echo [*] Activated Conda environment: digital-twin
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] Python environment 'digital-twin' was not found!
    echo Please verify that envs\digital-twin\ exists or Conda is initialized.
    pause
    exit /b 1
)

:: 3. Verify Archive Directory
if not exist "%~dp0terratwin_sos_archive\server.py" (
    echo [ERROR] Archived server script not found at terratwin_sos_archive\server.py!
    pause
    exit /b 1
)

:: 4. Launch Browser to Twin Explorer
echo [*] Launching browser to http://localhost:8000/index.html ...
start "" "http://localhost:8000/index.html"

:: 5. Launch FastAPI Backend Server
echo [*] Starting FastAPI backend on http://0.0.0.0:8000 ...
echo [*] Available Endpoints:
echo       - 3D Twin Explorer: http://localhost:8000/index.html
echo       - Citizen SOS Beacon: http://localhost:8000/sos.html
echo       - Rescuer HUD:        http://localhost:8000/receiver.html
echo       - API Health:         http://localhost:8000/api/health
echo.
echo Press Ctrl+C in this window to stop the server.
echo ======================================================================
echo.

cd /d "%~dp0terratwin_sos_archive"
"%PYTHON_EXE%" server.py --port 8000 --host 0.0.0.0

pause
