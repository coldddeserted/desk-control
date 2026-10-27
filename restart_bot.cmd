@echo off
taskkill /im pythonw.exe /f >nul 2>&1
timeout /t 1 >nul
cd /d "C:\Users\Daniil\IdeaProjects\desk-control"
start "" ".venv\Scripts\pythonw.exe" bot.py
