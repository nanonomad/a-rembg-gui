@echo off
REM build.bat - Build script for rembg GUI

echo ============================================
echo Building rembg GUI Executable
echo ============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install "rembg[gpu,cli]" pillow opencv-python psutil numpy
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__

REM Build with PyInstaller
echo Building executable...
pyinstaller rembg_gui.spec

REM Check if build was successful
if exist "dist\rembg_gui\rembg_gui.exe" (
    echo.
    echo ============================================
    echo Build completed successfully!
    echo Executable location: dist\rembg_gui\rembg_gui.exe
    echo ============================================
    echo.
    echo You can now distribute the entire 'dist\rembg_gui' folder
) else (
    echo.
    echo ============================================
    echo Build failed! Check the output above for errors.
    echo ============================================
)

pause
