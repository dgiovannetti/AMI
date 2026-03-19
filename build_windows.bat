@echo off
REM AMI 3.x — build Windows executable from 3.0/ (PyInstaller onedir → dist\AMI-Package\AMI.exe)
setlocal
cd /d "%~dp0"

echo ============================================================
echo AMI 3.x - Active Monitor of Internet
echo Windows build (cartella 3.0)
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python non trovato. Installa da https://www.python.org/downloads/
    echo Assicurati di spuntare "Add Python to PATH"
    pause
    exit /b 1
)

echo Step 1: Icone in resources (root) - opzionale...
if exist "tools\generate_icons.py" (
    python tools\generate_icons.py
    if errorlevel 1 echo WARNING: generate_icons fallito, continuo...
) else (
    echo Nessun tools\generate_icons.py, salto.
)

echo.
echo Step 2: Dipendenze AMI 3.0...
set "REPO_ROOT=%~dp0"
cd /d "%REPO_ROOT%3.0"
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: pip install fallito
    cd /d "%~dp0"
    pause
    exit /b 1
)

echo.
echo Step 3: PyInstaller build...
python build.py
if errorlevel 1 (
    echo ERROR: build.py fallito
    cd /d "%~dp0"
    pause
    exit /b 1
)

cd /d "%~dp0"
echo.
echo ============================================================
echo Build completato.
echo ============================================================
echo Eseguibile: 3.0\dist\AMI-Package\AMI.exe
echo.
echo Per testare:
echo   cd 3.0\dist\AMI-Package
echo   AMI.exe
echo.
pause
