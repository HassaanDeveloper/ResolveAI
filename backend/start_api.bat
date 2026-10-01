@echo off
cd /d E:\ResolveAI\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
