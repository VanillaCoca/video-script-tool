@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d %~dp0

echo [1/5] Checking Python...
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Please install Python 3.10+ and add it to PATH.
  pause
  exit /b 1
)

echo [2/5] Creating virtual environment...
if not exist .venv (
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo Failed to activate virtual environment.
  pause
  exit /b 1
)

echo [3/5] Installing dependencies...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
python -m pip install -r requirements_build.txt
if errorlevel 1 goto :fail

echo [4/5] Building single-file exe...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm --clean --windowed --onefile --name BiliTranscriptTool app.py
if errorlevel 1 goto :fail

echo [5/5] Done.
if exist dist\BiliTranscriptTool.exe (
  echo Main executable: %cd%\dist\BiliTranscriptTool.exe
  explorer dist
) else (
  echo Build finished, but exe was not found where expected.
)

echo.
echo Note: onefile starts slower than onedir because it extracts itself at runtime.
pause
exit /b 0

:fail
echo Build failed.
pause
exit /b 1
