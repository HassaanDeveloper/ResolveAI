@echo off
cd /d E:\ResolveAI\frontend
rd /s /q .next 2>nul
npx next dev --port 3000
