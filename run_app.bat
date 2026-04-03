@echo off
REM Hotel Compliance Tracker — Windows launcher
REM Double-click this file to start the app and open it in your browser.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Install dependencies if needed
python -m pip install -q -r requirements.txt 2>nul

REM Use port 5050 by default (port 5000 conflicts with macOS AirPlay)
if not defined PORT set PORT=5050

echo Starting Hotel Compliance Tracker...
echo The app will open in your browser at http://localhost:%PORT%
echo Press Ctrl+C to stop the server.
echo.

REM Poll until the server responds, then open browser
start "" cmd /c "for /L %%i in (1,1,50) do (curl -s -o nul http://localhost:%PORT% >nul 2>&1 && start http://localhost:%PORT% && exit /b || timeout /t 1 /nobreak >nul)"

REM Start the Flask app
set PORT=%PORT%
python run.py
