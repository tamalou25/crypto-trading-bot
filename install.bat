@echo off
echo ========================================
echo   Installation du Crypto Trading Bot
echo ========================================
echo.

echo [1/4] Creation de l'environnement virtuel...
python -m venv venv
call venv\Scripts\activate

echo [2/4] Installation des dependances...
pip install -r requirements.txt

echo [3/4] Creation des dossiers necessaires...
mkdir logs 2>nul
mkdir models 2>nul
mkdir data 2>nul

echo [4/4] Installation terminee!
echo.
echo Pour lancer le bot : double-cliquez sur start.bat
pause
