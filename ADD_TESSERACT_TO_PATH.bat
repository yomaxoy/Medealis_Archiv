@echo off
echo ================================================================================
echo ADD TESSERACT TO PATH
echo ================================================================================
echo.

echo Searching for Tesseract installation...
echo.

REM Check common installation paths
set TESSERACT_PATH=

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set TESSERACT_PATH=C:\Program Files\Tesseract-OCR
)

if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set TESSERACT_PATH=C:\Program Files (x86)\Tesseract-OCR
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe" (
    set TESSERACT_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR
)

if "%TESSERACT_PATH%"=="" (
    echo [ERROR] Tesseract installation not found!
    echo.
    echo Please check if Tesseract is installed in one of these locations:
    echo   - C:\Program Files\Tesseract-OCR
    echo   - C:\Program Files (x86)\Tesseract-OCR
    echo   - C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR
    echo.
    echo Or manually enter the path below.
    echo.
    set /p TESSERACT_PATH="Enter Tesseract installation path (or press Enter to cancel): "

    if "%TESSERACT_PATH%"=="" (
        echo Cancelled.
        pause
        exit /b
    )
)

echo.
echo [OK] Found Tesseract at: %TESSERACT_PATH%
echo.

REM Add to User PATH
echo Adding to PATH...
setx PATH "%PATH%;%TESSERACT_PATH%"

echo.
echo ================================================================================
echo SUCCESS
echo ================================================================================
echo.
echo Tesseract has been added to your PATH.
echo.
echo IMPORTANT: Please close this terminal and open a new one for changes to take effect.
echo.
echo Then verify by running:
echo   tesseract --version
echo.
pause
