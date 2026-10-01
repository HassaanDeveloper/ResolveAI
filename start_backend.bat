@echo off
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul
cd /d E:\ResolveAI\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
