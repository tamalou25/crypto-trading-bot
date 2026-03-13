@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo Demarrage du Crypto Trading Bot...
call venv\Scripts\activate.bat
python bot.py
pause
