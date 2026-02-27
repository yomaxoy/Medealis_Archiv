@echo off
echo ================================================================================
echo MEDEALIS SYSTEM DIAGNOSTICS
echo ================================================================================
echo.

echo 1. PYTHON VERSION:
echo --------------------------------------------------------------------------------
python --version
echo.

echo 2. CURRENT DIRECTORY:
echo --------------------------------------------------------------------------------
cd
echo.

echo 3. .ENV FILE CHECK:
echo --------------------------------------------------------------------------------
if exist ".env" (
    echo [OK] .env file found in current directory
    echo File size:
    dir /s .env | find ".env"
) else (
    echo [ERROR] .env file NOT found in current directory!
)
echo.

echo 4. ENVIRONMENT VARIABLES:
echo --------------------------------------------------------------------------------
echo USE_SERVER_STORAGE = %USE_SERVER_STORAGE%
echo ANTHROPIC_API_KEY = %ANTHROPIC_API_KEY:~0,20%...
echo.

echo 5. TESSERACT OCR CHECK:
echo --------------------------------------------------------------------------------
where tesseract >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tesseract found in PATH
    tesseract --version 2>&1 | findstr "tesseract"
) else (
    echo [ERROR] Tesseract NOT found in PATH
)
echo.

echo 6. PYTHON PACKAGES:
echo --------------------------------------------------------------------------------
echo Checking python-dotenv:
python -c "import dotenv; print('[OK] python-dotenv version:', dotenv.__version__)" 2>nul || echo [ERROR] python-dotenv not installed

echo Checking pytesseract:
python -c "import pytesseract; print('[OK] pytesseract installed')" 2>nul || echo [ERROR] pytesseract not installed

echo Checking anthropic:
python -c "import anthropic; print('[OK] anthropic installed')" 2>nul || echo [ERROR] anthropic not installed
echo.

echo 7. DATABASE PATH TEST:
echo --------------------------------------------------------------------------------
python -c "import os; from pathlib import Path; from dotenv import load_dotenv; load_dotenv('.env'); from config.settings import Settings; print('DB Path:', Settings._get_database_path())" 2>nul
echo.

echo 8. API KEY LOAD TEST:
echo --------------------------------------------------------------------------------
python -c "import os; from pathlib import Path; from dotenv import load_dotenv; env_file = Path('.env'); result = load_dotenv(env_file, override=True); api_key = os.getenv('ANTHROPIC_API_KEY'); print('API Key loaded:', 'YES' if api_key else 'NO'); print('API Key starts with:', api_key[:20] + '...' if api_key else 'N/A')"
echo.

echo ================================================================================
echo DIAGNOSTICS COMPLETE
echo ================================================================================
echo.
echo Please run this script on BOTH computers and compare the output!
echo.
pause
