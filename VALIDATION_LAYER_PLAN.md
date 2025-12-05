# Validation Layer - Implementierungsplan

## Übersicht

Zentrales Validierungs-System für alle Datenbank-Operationen mit standardisierten Fehlerbehandlung und Rückmeldungen.

---

## 1. Architektur

### Clean Architecture Placement

```
Presentation Layer (Streamlit Popups)
    ↓ (ruft auf)
Application Layer (Services + Validators)
    ↓ (nutzt)
Domain Layer (Validation Rules)
    ↓ (keine Abhängigkeiten)
Infrastructure Layer (Repositories)
```

### Komponenten

1. **Domain Validation Rules** (`src/warehouse/domain/validation/`)
   - Value Object Validierung (bereits vorhanden)
   - Business Rule Validierung (neu)

2. **Application Validators** (`src/warehouse/application/validators/`)
   - Popup-spezifische Validatoren
   - Zentrale Orchestrierung

3. **Validation Result Objects**
   - Standardisierte Rückgabewerte
   - Fehler-Details mit Kontext

---

## 2. Domain Layer - Validation Rules

### 2.1 Neue Domain-Validatoren

**Datei:** `src/warehouse/domain/validation/item_validation_rules.py`

```python
"""
Domain Validation Rules für Items.

Enthält Business-Logik für Item-Validierung unabhängig von Use Cases.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class ValidationError:
    """Einzelner Validierungsfehler."""
    field: str
    message: str
    code: str
    severity: str = "error"  # "error", "warning", "info"


@dataclass
class ValidationResult:
    """Ergebnis einer Validierung."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ItemInfoValidationRules:
    """Business Rules für ItemInfo-Validierung."""

    @staticmethod
    def validate_designation(designation: str) -> ValidationResult:
        """Validiert Artikelbezeichnung."""
        errors = []
        warnings = []

        if not designation or not designation.strip():
            errors.append(ValidationError(
                field="designation",
                message="Bezeichnung darf nicht leer sein",
                code="DESIGNATION_EMPTY"
            ))

        if designation and len(designation) < 3:
            warnings.append(ValidationError(
                field="designation",
                message="Sehr kurze Bezeichnung (< 3 Zeichen)",
                code="DESIGNATION_TOO_SHORT",
                severity="warning"
            ))

        if designation and len(designation) > 200:
            errors.append(ValidationError(
                field="designation",
                message="Bezeichnung zu lang (max 200 Zeichen)",
                code="DESIGNATION_TOO_LONG"
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_manufacturer(manufacturer: Optional[str]) -> ValidationResult:
        """Validiert Hersteller-Namen."""
        errors = []
        warnings = []

        if manufacturer and len(manufacturer) > 100:
            errors.append(ValidationError(
                field="manufacturer",
                message="Herstellername zu lang (max 100 Zeichen)",
                code="MANUFACTURER_TOO_LONG"
            ))

        # Mehrere Hersteller erlaubt (kommagetrennt)
        if manufacturer and "," in manufacturer:
            manufacturers = [m.strip() for m in manufacturer.split(",")]
            if any(len(m) < 2 for m in manufacturers):
                warnings.append(ValidationError(
                    field="manufacturer",
                    message="Einige Herstellernamen sind sehr kurz",
                    code="MANUFACTURER_NAME_SHORT",
                    severity="warning"
                ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_qr_code(qr_data: Optional[bytes], filename: Optional[str]) -> ValidationResult:
        """Validiert QR-Code Upload."""
        errors = []
        warnings = []

        if qr_data:
            # Größe prüfen (max 5MB)
            size_mb = len(qr_data) / (1024 * 1024)
            if size_mb > 5:
                errors.append(ValidationError(
                    field="qr_code",
                    message=f"QR-Code zu groß: {size_mb:.2f} MB (max 5 MB)",
                    code="QR_CODE_TOO_LARGE"
                ))

            # Dateiformat prüfen
            if filename:
                valid_extensions = ['.png', '.jpg', '.jpeg']
                if not any(filename.lower().endswith(ext) for ext in valid_extensions):
                    errors.append(ValidationError(
                        field="qr_code",
                        message=f"Ungültiges Format: {filename} (nur PNG/JPG erlaubt)",
                        code="QR_CODE_INVALID_FORMAT"
                    ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class ItemWorkflowValidationRules:
    """Business Rules für Workflow-Validierung."""

    @staticmethod
    def validate_data_confirmation(
        ordered_quantity: Optional[int],
        delivery_slip_quantity: Optional[int],
        delivered_quantity: int
    ) -> ValidationResult:
        """Validiert Daten-Bestätigung."""
        errors = []
        warnings = []

        # Gelieferte Menge muss positiv sein
        if delivered_quantity <= 0:
            errors.append(ValidationError(
                field="delivered_quantity",
                message="Gelieferte Menge muss größer als 0 sein",
                code="DELIVERED_QUANTITY_INVALID"
            ))

        # Warnung bei Abweichungen
        if delivery_slip_quantity and delivered_quantity != delivery_slip_quantity:
            warnings.append(ValidationError(
                field="delivered_quantity",
                message=f"Abweichung zum Lieferschein: {delivery_slip_quantity} → {delivered_quantity}",
                code="QUANTITY_MISMATCH_DELIVERY",
                severity="warning"
            ))

        if ordered_quantity and delivered_quantity != ordered_quantity:
            warnings.append(ValidationError(
                field="delivered_quantity",
                message=f"Abweichung zur Bestellung: {ordered_quantity} → {delivered_quantity}",
                code="QUANTITY_MISMATCH_ORDER",
                severity="warning"
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_inspection(
        delivered_quantity: int,
        waste_quantity: int
    ) -> ValidationResult:
        """Validiert Sichtkontrolle."""
        errors = []
        warnings = []

        if waste_quantity < 0:
            errors.append(ValidationError(
                field="waste_quantity",
                message="Ausschussmenge kann nicht negativ sein",
                code="WASTE_QUANTITY_NEGATIVE"
            ))

        if waste_quantity > delivered_quantity:
            errors.append(ValidationError(
                field="waste_quantity",
                message=f"Ausschussmenge ({waste_quantity}) größer als gelieferte Menge ({delivered_quantity})",
                code="WASTE_EXCEEDS_DELIVERED"
            ))

        if waste_quantity == delivered_quantity:
            warnings.append(ValidationError(
                field="waste_quantity",
                message="100% Ausschuss - Komplette Lieferung abgelehnt",
                code="FULL_WASTE",
                severity="warning"
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

---

## 3. Application Layer - Validators

### 3.1 Popup-Validatoren

**Datei:** `src/warehouse/application/validators/popup_validators.py`

```python
"""
Application Layer Validators für Popup-Operationen.

Orchestriert Domain Validation Rules und fügt Use-Case-spezifische Validierung hinzu.
"""

import logging
from typing import Dict, Any, List
from warehouse.domain.validation.item_validation_rules import (
    ItemInfoValidationRules,
    ItemWorkflowValidationRules,
    ValidationResult,
    ValidationError
)

logger = logging.getLogger(__name__)


class ItemInfoPopupValidator:
    """Validator für ItemInfo-Dialog."""

    def __init__(self):
        self.rules = ItemInfoValidationRules()

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert alle ItemInfo-Felder.

        Args:
            data: {
                "article_number": str,
                "designation": str,
                "manufacturer": str (optional),
                "qr_code_image": bytes (optional),
                "qr_code_filename": str (optional),
                ...
            }

        Returns:
            ValidationResult mit allen Fehlern und Warnungen
        """
        all_errors = []
        all_warnings = []

        # Artikelnummer (Pflichtfeld)
        if not data.get("article_number"):
            all_errors.append(ValidationError(
                field="article_number",
                message="Artikelnummer fehlt",
                code="ARTICLE_NUMBER_MISSING"
            ))

        # Bezeichnung
        designation_result = self.rules.validate_designation(
            data.get("designation", "")
        )
        all_errors.extend(designation_result.errors)
        all_warnings.extend(designation_result.warnings)

        # Hersteller
        manufacturer_result = self.rules.validate_manufacturer(
            data.get("manufacturer")
        )
        all_errors.extend(manufacturer_result.errors)
        all_warnings.extend(manufacturer_result.warnings)

        # QR-Code
        if data.get("qr_code_image"):
            qr_result = self.rules.validate_qr_code(
                data.get("qr_code_image"),
                data.get("qr_code_filename")
            )
            all_errors.extend(qr_result.errors)
            all_warnings.extend(qr_result.warnings)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )


class DataConfirmationPopupValidator:
    """Validator für Daten-Bestätigung Dialog."""

    def __init__(self):
        self.rules = ItemWorkflowValidationRules()

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validiert Daten-Bestätigung."""
        return self.rules.validate_data_confirmation(
            ordered_quantity=data.get("ordered_quantity"),
            delivery_slip_quantity=data.get("delivery_slip_quantity"),
            delivered_quantity=data.get("delivered_quantity", 0)
        )


class InspectionPopupValidator:
    """Validator für Sichtkontrolle Dialog."""

    def __init__(self):
        self.rules = ItemWorkflowValidationRules()

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validiert Sichtkontrolle."""
        return self.rules.validate_inspection(
            delivered_quantity=data.get("delivered_quantity", 0),
            waste_quantity=data.get("waste_quantity", 0)
        )
```

---

## 4. Presentation Layer - Integration

### 4.1 Validierung in Popups

**Beispiel:** `iteminfo_edit_dialog.py`

```python
from warehouse.application.validators.popup_validators import ItemInfoPopupValidator

@st.dialog("📝 Artikel-Informationen bearbeiten", width="large")
def show_iteminfo_edit_dialog(article_data: Dict[str, Any]):
    # ... bestehender Code ...

    with col_btn2:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            # Prepare data
            iteminfo_data = {
                "article_number": article_number,
                "designation": designation,
                "manufacturer": manufacturer,
                "qr_code_image": st.session_state.get("edit_qr_data"),
                "qr_code_filename": st.session_state.get("edit_qr_filename"),
                # ...
            }

            # VALIDIERUNG
            validator = ItemInfoPopupValidator()
            validation_result = validator.validate(iteminfo_data)

            # Fehler anzeigen
            if validation_result.has_errors:
                st.error("❌ Validierungsfehler:")
                for error in validation_result.errors:
                    st.error(f"  • {error.field}: {error.message}")
                return

            # Warnungen anzeigen (aber weitermachen)
            if validation_result.has_warnings:
                st.warning("⚠️ Hinweise:")
                for warning in validation_result.warnings:
                    st.warning(f"  • {warning.field}: {warning.message}")

            # Speichern
            try:
                if existing_iteminfo:
                    result = item_info_repository.update_item_info(article_number, iteminfo_data)
                else:
                    result = item_info_repository.create_item_info(iteminfo_data)

                if result:
                    st.success(f"✅ ItemInfo gespeichert!")
                    st.session_state.show_iteminfo_edit_dialog = False
                    st.rerun()
                else:
                    st.error("❌ Fehler beim Speichern!")
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
```

---

## 5. Implementierungsschritte

### Phase 1: Domain Validation Rules (2-3h)
1. ✅ Erstelle `ValidationError` und `ValidationResult` Dataclasses
2. ✅ Implementiere `ItemInfoValidationRules`
3. ✅ Implementiere `ItemWorkflowValidationRules`
4. ✅ Unit Tests für alle Rules

### Phase 2: Application Validators (1-2h)
1. ✅ Erstelle `ItemInfoPopupValidator`
2. ✅ Erstelle `DataConfirmationPopupValidator`
3. ✅ Erstelle `InspectionPopupValidator`
4. ✅ Integration Tests

### Phase 3: Presentation Integration (2-3h)
1. ✅ Integration in `iteminfo_edit_dialog.py`
2. ✅ Integration in `data_confirmation.py`
3. ✅ Integration in `visual_inspection.py`
4. ✅ Integration in alle anderen Popups

### Phase 4: Error Handling (1h)
1. ✅ Standardisierte Fehleranzeige in UI
2. ✅ Logging aller Validierungsfehler
3. ✅ User-friendly Error Messages

---

## 6. Erweiterbarkeit

### Neue Validatoren hinzufügen

```python
# 1. Domain Rule definieren
class MyNewValidationRules:
    @staticmethod
    def validate_something(value: str) -> ValidationResult:
        # ...

# 2. Application Validator erstellen
class MyNewPopupValidator:
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        # ...

# 3. In Popup integrieren
validator = MyNewPopupValidator()
result = validator.validate(popup_data)
if not result.is_valid:
    # Fehler anzeigen
```

---

## 7. Vorteile

✅ **Clean Architecture konform** - Klare Schichten-Trennung
✅ **Wiederverwendbar** - Rules können mehrfach genutzt werden
✅ **Testbar** - Domain Rules isoliert testbar
✅ **Erweiterbar** - Neue Validatoren einfach hinzufügen
✅ **Konsistent** - Standardisierte Fehlerbehandlung
✅ **User-friendly** - Klare Fehlermeldungen

---

## 8. Nächste Schritte

Nach Genehmigung:
1. Domain Validation Rules implementieren
2. Application Validators implementieren
3. Schrittweise in bestehende Popups integrieren
4. Tests schreiben
5. Dokumentation erstellen
