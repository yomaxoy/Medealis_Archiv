# Medealis Archiv - PowerShell Startskript
Write-Host "Starte Medealis Archiv Admin App..." -ForegroundColor Green
Write-Host ""

# Verwende das .venv Virtual Environment
.\.venv\Scripts\streamlit.exe run src\warehouse\presentation\admin\main_admin_app.py --server.port=8502
