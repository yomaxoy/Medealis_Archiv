# Medealis Warehouse Management System - Dependencies Installation

## System Overview
The Medealis system is built with Clean Architecture and works with core Python dependencies. Additional packages enhance functionality but are optional.

## Core Requirements (Already in requirements.txt)
```bash
pip install -r requirements.txt
```

**Core dependencies include:**
- `streamlit` - Web interface framework
- `sqlalchemy` - Database ORM
- `pillow` - Image processing for barcodes
- `python-barcode` - Barcode generation
- `cryptography` - API key encryption

## Optional Enhanced Features

### For Document Generation (DOCX/PDF)
```bash
pip install python-docx pdfkit
```
- **python-docx**: Enables DOCX template processing
- **pdfkit**: PDF generation (requires wkhtmltopdf)

### For Advanced Data Export
```bash
pip install pandas openpyxl xlsxwriter
```
- **pandas**: Advanced data manipulation for exports
- **openpyxl**: Excel file generation
- **xlsxwriter**: Enhanced Excel formatting

### For Local OCR (DSGVO-compliant)
```bash
pip install -r requirements_local_ocr.txt
```
**Includes:**
- `tesseract-ocr` - OCR engine
- `pytesseract` - Python OCR wrapper
- `pdf2image` - PDF to image conversion
- `poppler-utils` - PDF processing utilities

## Install All Enhanced Features
```bash
pip install python-docx pdfkit pandas openpyxl xlsxwriter
pip install -r requirements_local_ocr.txt
```

## What Works Without Optional Dependencies

### ✅ Core System (Always Available)
- Clean Architecture implementation
- SQLite database with full CRUD operations
- Streamlit admin interface
- Basic barcode generation
- TXT template document generation
- CSV data export

### ✅ With OCR Dependencies
- PDF document processing
- Text extraction from delivery slips
- DSGVO-compliant local processing

### ✅ With Document Dependencies
- DOCX template processing (PDB, Sichtkontrolle)
- PDF document generation
- Advanced formatting

### ✅ With Data Export Dependencies
- Excel export with formatting
- Multi-sheet workbooks
- Advanced data analysis

## Application Startup

### Main Application (Clean Architecture)
```bash
streamlit run src/warehouse/presentation/admin/main_admin_app.py
```

### CLI Tools
```bash
python src/main.py                    # CLI interface
python src/reset_DB.py               # Database reset
python tests/test_clean_architecture.py  # Architecture test
```

## Dependency Verification
The system automatically detects available dependencies and gracefully handles missing packages with appropriate fallbacks. Check the admin interface status indicators for dependency availability.

## Installation Notes
- **Windows Users**: Some OCR dependencies may require additional system-level installations
- **System PATH**: Ensure wkhtmltopdf and tesseract are in system PATH if installed
- **Virtual Environment**: Recommended to use `python -m venv venv` for isolation