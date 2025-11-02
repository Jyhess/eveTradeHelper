@echo off
echo ====================================
echo Configuration de l'environnement
echo ====================================
echo.

echo [1/3] Création de l'environnement virtuel Python...
python -m venv .venv
if errorlevel 1 (
    echo ERREUR: Impossible de créer l'environnement virtuel
    pause
    exit /b 1
)

echo.
echo [2/3] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo [3/3] Installation des dépendances Python...
pip install --upgrade pip
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERREUR: Impossible d'installer les dépendances
    pause
    exit /b 1
)

echo.
echo [4/4] Installation des dépendances Node.js...
cd frontend
call npm install
if errorlevel 1 (
    echo ERREUR: Impossible d'installer les dépendances Node.js
    pause
    exit /b 1
)
cd ..

echo.
echo ====================================
echo Configuration terminée avec succes!
echo ====================================
echo.
echo Pour activer l'environnement virtuel:
echo   .venv\Scripts\activate
echo.
pause

