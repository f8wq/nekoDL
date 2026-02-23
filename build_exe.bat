@echo off
setlocal

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher ^(py^) not found in PATH.
  exit /b 1
)

py -3 -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b 1

py -3 -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name nekoDL ^
  --icon app.ico ^
  --add-data "assets;assets" ^
  --add-data "app.ico;." ^
  app.py

if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\nekoDL.exe
