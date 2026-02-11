# Validation & UI Improvement Implementation Plan

## Status: IN PROGRESS

## ✅ PHASE 1: Foundation (COMPLETED)

### Domain Layer
- ✅ Created `validation_result.py` - ValidationResult, ValidationError value objects
- ✅ Created `field_validators.py` - Basic field validators (required, string_length, integer, regex, choice, boolean_true)
- ✅ Created `popup_validators.py` - Popup-specific validators (ItemInfo, DataConfirmation, DocumentCheck, Measurement, VisualInspection, DocumentMerge)

### Application Layer
- ✅ Created `validation_service.py` - Centralized validation facade with helper methods

### Presentation Layer
- ✅ Integrated validation in `iteminfo_edit_dialog.py` (Popup 1)
  - ✅ Added required field markers (*)
  - ✅ Changed fields to match requirements (LagerNo = number_input, Ref = number_input)
  - ✅ Added validation before save
  - ✅ Display formatted validation errors

## 🔄 PHASE 2: Popup Integration (IN PROGRESS)

### Popup 2 - Daten bestätigen ([data_confirmation.py](src/warehouse/presentation/user/popups/data_confirmation.py))

**Requirements:**
- ✅ Validation rules defined in `DataConfirmationValidator`
  - Name (Pflicht) - Mitarbeitername field
  - Artikelnummer (Pflicht)
  - Lot-Nummer (Pflicht, conditional format based on supplier)
    - PRIMEC: P-xxxxxxxxxxxx/-xxxx/x
    - TERRATS: beliebiger String
  - Bestellnummer (Pflicht, Int)
  - Liefernummer (Pflicht)
  - Lieferscheinmenge (Pflicht, Int > 0)
  - LagerNo (Pflicht, Int)
  - OrderNo (Str)

**UI Improvements:**
- ⏳ Move Mitarbeitername field to TOP of popup (before all other fields)
- ⏳ Add required field markers (*)
- ⏳ Add validation call in `handle_primary_action` (line 264)
- ⏳ Replace existing validation (lines 288-295) with validation_service call
- ⏳ Add audit logging after successful save

**Technical Notes:**
- Uses `FormBuilder` component-based architecture
- Complex form with 4 sections (Artikeldaten, Mengenerfassung, Zusätzliche Informationen, Bestelldokumente)
- Handles article/batch number changes
- Generates 3 documents automatically (Begleitschein, Wareneingangskontrolle, Barcode)
- Supplier ID needs to be passed to validator for Lot format validation

### Popup 3 - Doc bestätigen ([document_check.py](src/warehouse/presentation/user/popups/document_check.py))

**Requirements:**
- ✅ Validation rules defined in `DocumentCheckValidator`
  - Label vorhanden (must be TRUE)
  - QR-Code vorhanden (must be TRUE)

**UI Improvements:**
- ⏳ Read current implementation
- ⏳ Add validation call before save
- ⏳ Add audit logging

### Popup 4 - Vermessen ([measurement.py](src/warehouse/presentation/user/popups/measurement.py))

**Requirements:**
- ✅ Validation rules defined in `MeasurementValidator`
  - Vermessen durchgeführt (checkbox, must be TRUE)
  - Prüfername (Pflicht)

**UI Improvements:**
- ⏳ Move Prüfername field to TOP of popup
- ⏳ Visualize QR-Code if present (from ItemInfo)
- ⏳ Replace combobox with checkbox for "Vermessen durchgeführt"
- ⏳ Add validation call before save
- ⏳ Add audit logging

**Technical Notes:**
- Need to load QR-Code from ItemInfo repository
- Display QR-Code image if exists
- Change measurement field from selectbox/combobox to checkbox

### Popup 5 - Sichtkontrolle ([visual_inspection.py](src/warehouse/presentation/user/popups/visual_inspection.py))

**Requirements:**
- ✅ Validation rules defined in `VisualInspectionValidator`
  - Prüfername (Pflicht)
  - Ausschussmenge (Pflicht, Int >= 0)

**UI Improvements:**
- ⏳ Move Prüfername/Name field to TOP of popup
- ⏳ Add validation call before save
- ⏳ Add audit logging

### Popup 6 - Mergen ([document_merge.py](src/warehouse/presentation/user/popups/document_merge.py))

**Requirements:**
- ✅ Validation rules defined in `DocumentMergeValidator`
  - PDB (must be TRUE)
  - Vermessungsprotokoll (must be TRUE)
  - Sichtprüfung (must be TRUE)
  - Orderdokument (must be TRUE)
  - Lieferschein (must be TRUE)
  - Begleitpapiere (must be TRUE)

**UI Improvements:**
- ⏳ Read current implementation
- ⏳ Add validation call before save
- ⏳ Potentially add auto-generation for missing PDB
- ⏳ Add audit logging

## 📋 PHASE 3: Global UI Improvements (PENDING)

### Name/Prüfer Field Positioning
- ⏳ Create reusable component for Name input field at top of popups
- ⏳ Consider: Should Prüfername be in HEADER of all popups? (User question pending)

### Deckblatt Customization
- ⏳ TODO for later (marked in backlog)

## 🧪 PHASE 4: Testing & Validation (PENDING)

### Manual Testing Checklist
- ⏳ Test Popup 1 (ItemInfo) validation
  - Test required fields (all empty → should fail)
  - Test max length (Bezeichnung, Hersteller > 50 chars → should fail)
  - Test integer fields (non-numeric input → should fail)
  - Test successful save with valid data
- ⏳ Test Popup 2 (Daten bestätigen) validation
  - Test PRIMEC Lot format (invalid format → should fail)
  - Test TERRATS Lot format (any string → should pass)
  - Test all required fields
- ⏳ Test Popup 3 (Doc bestätigen) validation
  - Test with Label unchecked → should fail
  - Test with QR-Code unchecked → should fail
- ⏳ Test Popup 4 (Vermessen) validation
  - Test checkbox not checked → should fail
  - Test empty Prüfername → should fail
  - Test QR-Code visualization
- ⏳ Test Popup 5 (Sichtkontrolle) validation
  - Test empty Name → should fail
  - Test negative Ausschussmenge → should fail
- ⏳ Test Popup 6 (Mergen) validation
  - Test with any document missing → should fail
  - Test with all documents → should pass

### Integration Testing
- ⏳ Test complete workflow from delivery scan to merge
- ⏳ Verify audit logging for all actions
- ⏳ Verify validation errors display correctly in UI

## 📝 Implementation Notes

### Pattern for Popup Integration

```python
# 1. Add imports
from warehouse.application.services.validation_service import validation_service
from warehouse.application.services.audit_service import audit_service
from warehouse.presentation.utils.user_context import get_current_user

# 2. In handle_primary_action (before save):
validation_data = {
    "field1": value1,
    "field2": value2,
    # ...
}

validation_result = validation_service.validate_xxx(validation_data)

if not validation_result.is_valid:
    st.error("❌ **Validierungsfehler:**")
    st.error(validation_result.get_formatted_errors())
    return  # Stop execution

# 3. After successful save:
current_user = get_current_user()
audit_service.log_xxx_action(
    user=current_user,
    # ... action-specific parameters
)

# 4. Add st.rerun() at end if needed
```

### Supplier ID Determination for Lot Validation

For Popup 2 (Daten bestätigen), we need supplier_id to validate Lot format:
- Load from `item_data.get('supplier_id')` or
- Determine from delivery_number lookup or
- Use supplier service to get from article metadata

## 🎯 Next Steps

1. ✅ Complete Popup 1 (ItemInfo) - DONE
2. ⏳ Integrate Popup 2 (Daten bestätigen)
3. ⏳ Integrate Popup 3 (Doc bestätigen)
4. ⏳ Integrate Popup 4 (Vermessen) + QR visualization + checkbox
5. ⏳ Integrate Popup 5 (Sichtkontrolle)
6. ⏳ Integrate Popup 6 (Mergen)
7. ⏳ Testing phase
8. ⏳ User acceptance testing

## ❓ Open Questions

1. **Name in Header**: Should Prüfername be in the header of ALL popups instead of in the form? (User question)
2. **Supplier ID Source**: Best way to determine supplier_id for Lot validation in Popup 2?
3. **PDB Auto-Generation**: Should we auto-generate PDB if missing in Popup 6 or just fail validation?
