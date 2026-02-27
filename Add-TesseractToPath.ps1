Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "ADD TESSERACT TO PATH" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Searching for Tesseract installation..." -ForegroundColor Yellow
Write-Host ""

# Check common installation paths
$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR",
    "C:\Program Files (x86)\Tesseract-OCR",
    "$env:LOCALAPPDATA\Programs\Tesseract-OCR",
    "$env:USERPROFILE\AppData\Local\Programs\Tesseract-OCR"
)

$tesseractPath = $null

foreach ($path in $tesseractPaths) {
    if (Test-Path "$path\tesseract.exe") {
        $tesseractPath = $path
        break
    }
}

if (-not $tesseractPath) {
    Write-Host "[ERROR] Tesseract installation not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Checked these locations:"
    foreach ($path in $tesseractPaths) {
        Write-Host "  - $path"
    }
    Write-Host ""

    # Search entire C: drive (may take a while)
    Write-Host "Searching entire C: drive for tesseract.exe..." -ForegroundColor Yellow
    $found = Get-ChildItem -Path "C:\" -Filter "tesseract.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($found) {
        $tesseractPath = $found.DirectoryName
        Write-Host "[OK] Found at: $tesseractPath" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Could not find Tesseract!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install Tesseract from:"
        Write-Host "https://github.com/UB-Mannheim/tesseract/wiki"
        Write-Host ""
        pause
        exit
    }
}

Write-Host "[OK] Found Tesseract at: $tesseractPath" -ForegroundColor Green
Write-Host ""

# Check if already in PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -like "*$tesseractPath*") {
    Write-Host "[INFO] Tesseract is already in your PATH!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please restart your terminal and try:"
    Write-Host "  tesseract --version"
    Write-Host ""
    pause
    exit
}

# Add to User PATH
Write-Host "Adding to PATH..." -ForegroundColor Yellow

try {
    $newPath = $currentPath + ";" + $tesseractPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "SUCCESS" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tesseract has been added to your PATH." -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Please close this terminal and open a new one." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Then verify by running:" -ForegroundColor Cyan
    Write-Host "  tesseract --version" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "[ERROR] Failed to add to PATH: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please add manually via System Settings:" -ForegroundColor Yellow
    Write-Host "  1. Win + Pause -> Advanced System Settings"
    Write-Host "  2. Environment Variables"
    Write-Host "  3. Edit 'Path' under User variables"
    Write-Host "  4. Add: $tesseractPath"
    Write-Host ""
}

pause
