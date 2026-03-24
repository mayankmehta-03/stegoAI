@echo off
REM ============================================
REM StegoAI Web Interface - Quick Start Script
REM ============================================

echo.
echo ╔════════════════════════════════════════════╗
echo ║     StegoAI - Web Interface Setup           ║
echo ║   Advanced Steganography Platform           ║
echo ╚════════════════════════════════════════════╝
echo.

REM Verify virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ✗ Virtual environment not found!
    echo.
    echo Creating virtual environment...
    python -m venv .venv
    echo ✓ Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ✗ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated
echo.

REM Install requirements
echo Installing dependencies from requirements_web.txt...
pip install -r requirements_web.txt --quiet
if errorlevel 1 (
    echo ✗ Failed to install dependencies
    echo Please run: pip install -r requirements_web.txt
    pause
    exit /b 1
)
echo ✓ Dependencies installed successfully
echo.

REM Verify model files
echo Checking for model files...
if not exist "models\hide.h5" (
    echo ✗ Missing: models\hide.h5
    echo ✗ Please train the model first or copy it to the models folder
    echo.
    pause
    exit /b 1
)
if not exist "models\reveal.h5" (
    echo ✗ Missing: models\reveal.h5
    echo ✗ Please train the model first or copy it to the models folder
    echo.
    pause
    exit /b 1
)
echo ✓ Model files found
echo.

REM Create necessary directories
if not exist "uploads\" mkdir uploads
if not exist "output\" mkdir output
echo ✓ Directories ready
echo.

REM Display startup message
echo ╔════════════════════════════════════════════╗
echo ║   Starting StegoAI Web Server...            ║
echo ║                                            ║
echo ║   Open your browser and go to:             ║
echo ║   http://localhost:5000                    ║
echo ║                                            ║
echo ║   Press Ctrl+C to stop the server          ║
echo ╚════════════════════════════════════════════╝
echo.

REM Start Flask app
python app.py

pause
