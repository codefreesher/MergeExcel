@echo off
setlocal
cd /d "%~dp0"
set "APP_VERSION=1.0.0"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt || exit /b 1
python -m pytest tests || exit /b 1
python -m PyInstaller --clean --noconfirm ExcelMergerPro.spec || exit /b 1

where iscc >nul 2>nul
if errorlevel 1 (
  echo Build EXE completed. Install Inno Setup and add ISCC to PATH to build installer.
  exit /b 0
)
iscc /DAppVersion=%APP_VERSION% installer\installer.iss || exit /b 1
echo Installer created in installer-output.

