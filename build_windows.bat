@echo off
REM AMI Build Script for Windows
REM Builds AMI.exe from source

echo ============================================================
echo AMI - Active Monitor of Internet
echo Windows Build Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python non trovato!
    echo.
    echo Installa Python da: https://www.python.org/downloads/
    echo Assicurati di spuntare "Add Python to PATH"
    pause
    exit /b 1
)

echo Step 1: Installazione dipendenze...
echo.
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-build.txt

if errorlevel 1 (
    echo.
    echo ERROR: Installazione dipendenze fallita!
    pause
    exit /b 1
)

echo.
echo Step 2: Generazione icone...
echo.
python tools\generate_icons.py

if errorlevel 1 (
    echo.
    echo WARNING: Generazione icone fallita, continuo...
)

echo.
echo Step 3: Build eseguibile...
echo.
python build.py

if errorlevel 1 (
    echo.
    echo ERROR: Build fallito!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build completato con successo!
echo ============================================================
echo.
echo L'eseguibile si trova in: dist\AMI-Package\AMI.exe
echo.
echo Per testare:
echo   cd dist\AMI-Package
echo   AMI.exe
echo.
pause
