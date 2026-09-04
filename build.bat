@echo off
setlocal
cd /d "%~dp0"
set "APP_VERSION=1.2.2"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt || exit /b 1
python -m pytest tests || exit /b 1
if exist "dist\ExcelMergerPro.exe" del /q "dist\ExcelMergerPro.exe"
python -m nuitka ^
  --mode=onefile ^
  --enable-plugin=pyside6 ^
  --windows-console-mode=disable ^
  --assume-yes-for-downloads ^
  --include-data-dir=app\resources=app\resources ^
  --output-dir=dist ^
  --output-filename=ExcelMergerPro.exe ^
  main.py || exit /b 1

where iscc >nul 2>nul
if errorlevel 1 (
  echo Protected EXE build completed. Install Inno Setup and add ISCC to PATH to build installer.
  exit /b 0
)
iscc /DAppVersion=%APP_VERSION% installer\installer.iss || exit /b 1
echo Installer created in installer-output.
