# Document Generation System - Instructions

## ✅ **System Status: CLEAN ARCHITECTURE IMPLEMENTATION**

The document generation system is fully integrated into the Clean Architecture implementation of the Medealis Warehouse Management System.

## **What's Working**

### 1. **Clean Architecture Template System**
- ✅ Template loading from `resources/templates/`
- ✅ Placeholder replacement with `[[variable]]` pattern
- ✅ Multiple output formats (TXT, DOCX, PDF*)
- ✅ Automatic file naming with timestamps
- ✅ Domain-driven document generation through Application Services

### 2. **Document Types Available**
- **PDB (Prüfdatenblatt)** - from `Fo00040_PDB_Template.docx`
- **Begleitschein** (Delivery Slip) - from `Begleitschein.txt`
- **Sichtkontrolle** (Visual Inspection) - from `Fo00141_Sichtkontrolle.docx`
- **Wareneingangskontrolle** - from `Fo0113_Wareneingangskontrolle.docx`

### 3. **Clean Architecture Services**
- ✅ **DocumentService** - Template-based document generation
- ✅ **ExportService** - Excel/CSV export functionality
- ✅ **ReportingService** - Unified reporting API
- ✅ Integration with Domain Entities (Item, Delivery, Supplier)

### 4. **Streamlit Admin Interface**
- ✅ Integrated into Clean Architecture Presentation Layer
- ✅ Document generation through UI views and popups
- ✅ Real-time feedback and error handling

## **How to Use**

### Option 1: Via Clean Architecture Admin Interface (Recommended)
```bash
cd "C:\Users\krueg\OneDrive\Dokumente\Medealis\neu_Medealis_Archiv"
streamlit run src/warehouse/presentation/admin/main_admin_app.py
```

1. Navigate to **Lieferverwaltung** or **Artikelverwaltung**
2. Use the document generation popups and views
3. Select items/deliveries and generate documents through the UI
4. Available document types:
   - **PDB erstellen** - Creates inspection data sheet
   - **Begleitschein erstellen** - Creates delivery slip
   - **Sichtkontrolle erstellen** - Creates visual inspection report

### Option 2: Test Clean Architecture Integration
```bash
cd "C:\Users\krueg\OneDrive\Dokumente\Medealis\neu_Medealis_Archiv"
python tests/test_clean_architecture.py
```

## **Output Locations**

Documents are automatically saved to:
- **Documents**: `C:\Users\[user]\.medealis\documents\`
- **Excel Exports**: `C:\Users\[user]\.medealis\exports\`
- **Test Documents**: `C:\Users\[user]\.medealis\test_documents\`

## **File Naming Convention**

Generated files use this pattern:
- `Lieferschein_[DELIVERY_NUMBER]_[TIMESTAMP].[format]`
- `Pruefcheckliste_[DELIVERY_NUMBER]_[TIMESTAMP].[format]`
- `Sichtkontrolle_[ARTICLE]_[BATCH]_[TIMESTAMP].[format]`

Example: `Lieferschein_DEL-001_20250829_001530.docx`

## **Dependencies (Optional)**

For full functionality, install these packages:
```bash
pip install pandas python-docx pdfkit openpyxl
```

**Note**: The system works without these dependencies, but will:
- Only create TXT format documents (not DOCX/PDF)
- Skip Excel export functionality
- Show warnings (which can be ignored)

## **Template Customization**

Templates are located in `resources/templates/` and use this placeholder format:
- `[[variable]]` - Will be replaced with actual data
- Example: `[[datum]]` becomes `29.08.2025`

## **Troubleshooting**

### If you see encoding errors:
- The system has been updated to handle German umlauts properly
- All encoding issues have been fixed

### If templates are missing:
- Check that `resources/templates/` directory exists
- Verify template files are present and readable

### If directories don't exist:
- The system automatically creates output directories
- Check permissions if creation fails

## **Clean Architecture Integration**

The document generation follows Clean Architecture principles:

### **Application Layer**
- **DocumentService** - Core template handling and document generation
- **ExportService** - Excel/CSV export functionality
- **ReportingService** - Unified API coordinating all services

### **Domain Layer**
- Document generation driven by Domain Entities (Item, Delivery, Supplier)
- Business rules enforced through domain logic

### **Infrastructure Layer**
- File system operations for template loading and document saving
- Database integration for data retrieval

### **Presentation Layer**
- Streamlit admin interface with integrated document generation
- Modal popups and views for user interaction

## **Success Verification**

✅ Clean Architecture implementation complete
✅ Template system integrated with domain entities
✅ Document services working through application layer
✅ Streamlit admin interface fully functional
✅ Output directories and file handling operational
✅ All encoding issues resolved

The document generation system is fully integrated into the Clean Architecture and ready for production use!

---

*Generated: 2025-08-29 | Claude Code Assistant*