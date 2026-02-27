@echo off
echo ================================================================================
echo TESSERACT OCR INSTALLATION GUIDE
echo ================================================================================
echo.
echo This script will guide you through installing Tesseract OCR on Windows.
echo.
echo STEP 1: Download Tesseract
echo --------------------------------------------------------------------------------
echo Please download Tesseract from:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo Recommended: tesseract-ocr-w64-setup-5.3.3.20231005.exe (or latest)
echo.
pause

echo.
echo STEP 2: Install with German Language Pack
echo --------------------------------------------------------------------------------
echo IMPORTANT: During installation, make sure to:
echo   [X] Select "German" language pack (deu.traineddata)
echo   [X] Add Tesseract to PATH
echo.
pause

echo.
echo STEP 3: Install Python Package
echo --------------------------------------------------------------------------------
echo Now installing pytesseract Python package...
python -m pip install pytesseract pillow
echo.

echo.
echo STEP 4: Verify Installation
echo --------------------------------------------------------------------------------
echo Checking if Tesseract is available...
where tesseract >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tesseract found in PATH
    tesseract --version
    echo.
    echo [SUCCESS] Installation complete!
) else (
    echo [ERROR] Tesseract NOT found in PATH
    echo Please restart your computer and run this script again.
)
echo.
pause
