@echo off
taskkill /im pythonw.exe /f >nul 2>&1
echo Bot stopped
timeout /t 2 >nul
