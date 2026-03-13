@echo off
echo ========================================
echo   Demarrage du Crypto Trading Bot
echo ========================================
echo.
call venv\Scripts\activate.bat
echo Environnement virtuel active!
echo.
python bot.py
pause
