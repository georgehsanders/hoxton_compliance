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
pip install -q -r requirements.txt 2>nul

echo Starting Hotel Compliance Tracker...
echo The app will open in your browser at http://localhost:5000
echo Press Ctrl+C to stop the server.
echo.

REM Open browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

REM Start the Flask app
python run.py
