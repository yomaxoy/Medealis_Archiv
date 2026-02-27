@echo off
echo ================================================================================
echo MEDEALIS - COMPUTER SETUP SCRIPT
echo ================================================================================
echo.
echo This script will install all required Python packages on this computer.
echo.
pause

echo.
echo STEP 1: Installing Python packages
echo --------------------------------------------------------------------------------
echo Installing core dependencies...
python -m pip install --upgrade pip
python -m pip install python-dotenv anthropic httpx
echo.

echo Installing document processing...
python -m pip install pytesseract pillow PyPDF2 python-docx reportlab
echo.

echo Installing streamlit and dependencies...
python -m pip install streamlit pandas openpyxl
echo.

echo Installing database...
python -m pip install sqlalchemy
echo.

echo Installing barcode generation...
python -m pip install python-barcode
echo.

echo.
echo STEP 2: Verify Installation
echo --------------------------------------------------------------------------------
python -c "import dotenv; print('[OK] python-dotenv installed')"
python -c "import anthropic; print('[OK] anthropic installed')"
python -c "import pytesseract; print('[OK] pytesseract installed')"
python -c "import streamlit; print('[OK] streamlit installed')"
echo.

echo.
echo STEP 3: Tesseract OCR Check
echo --------------------------------------------------------------------------------
where tesseract >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tesseract OCR already installed
    tesseract --version
) else (
    echo [WARNING] Tesseract OCR not found!
    echo.
    echo Please install Tesseract manually:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Run: tesseract-ocr-w64-setup-5.3.3.20231005.exe
    echo 3. During installation:
    echo    - Check "Add to PATH"
    echo    - Select "German language pack"
    echo.
)

echo.
echo ================================================================================
echo SETUP COMPLETE
echo ================================================================================
echo.
echo You can now run the application with:
echo   streamlit run src\warehouse\presentation\admin\main_admin_app.py --server.port 8501
echo.
pause
