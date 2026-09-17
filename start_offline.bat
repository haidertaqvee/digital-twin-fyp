@echo off
title TerraTwin SOS - Offline Local Server
echo ========================================================
echo   TerraTwin SOS ? Offline Local Server & Digital Twin
echo ========================================================
echo.
echo Starting local backend server on http://localhost:8000...
echo.
cd /d "%~dp0"
start "" "http://localhost:8000/index.html"
.\envs\digital-twin\python.exe src\server.py --port 8000 --host 0.0.0.0
pause
