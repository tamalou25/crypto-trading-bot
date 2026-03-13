@echo off
echo ========================================
echo   Installation du Crypto Trading Bot
echo ========================================
echo.

echo [1/5] Verification de Python...
python --version
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe!
    echo Telecharge Python sur https://python.org/downloads
    pause
    exit
)

echo [2/5] Creation de l'environnement virtuel...
python -m venv venv

echo [3/5] Activation du venv et installation des dependances...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo [4/5] Creation des dossiers necessaires...
mkdir logs 2>nul
mkdir models 2>nul
mkdir data 2>nul

echo [5/5] Installation terminee avec succes!
echo.
echo Lance start.bat pour demarrer le bot
pause
