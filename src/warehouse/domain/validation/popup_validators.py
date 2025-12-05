# src/warehouse/domain/validation/popup_validators.py

"""
Popup Validators - Domain Layer.

Spezifische Validatoren für die verschiedenen Popups.
"""

from typing import Dict, Any, Optional
from .validation_result import ValidationResult
from .field_validators import FieldValidator


class ItemInfoValidator:
    """
    Validator für Popup 1 - ItemInfo.

    Pflichtfelder:
    - Bezeichnung (Str/Char50)
    - LagerNo (Int)
    - Hersteller (Str/Char50)
    - Ref (Int)
    """

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert ItemInfo-Daten.

        Args:
            data: {
                designation: str,
                storage_location: str,
                manufacturer: str,
                revision_number: int
            }

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Bezeichnung (Pflicht, max 50 Zeichen)
        designation = data.get("designation")
        result.merge(
            FieldValidator.validate_required(designation, "designation", "Bezeichnung")
        )
        result.merge(
            FieldValidator.validate_string_length(
                designation, "designation", 50, "Bezeichnung"
            )
        )

        # LagerNo (Pflicht, Integer)
        storage_location = data.get("storage_location")
        result.merge(
            FieldValidator.validate_required(
                storage_location, "storage_location", "Lagerort"
            )
        )
        result.merge(
            FieldValidator.validate_integer(
                storage_location, "storage_location", "Lagerort"
            )
        )

        # Hersteller (Pflicht, max 50 Zeichen)
        manufacturer = data.get("manufacturer")
        result.merge(
            FieldValidator.validate_required(manufacturer, "manufacturer", "Hersteller")
        )
        result.merge(
            FieldValidator.validate_string_length(
                manufacturer, "manufacturer", 50, "Hersteller"
            )
        )

        # Ref / Revision Number (Pflicht, Integer)
        revision_number = data.get("revision_number")
        result.merge(
            FieldValidator.validate_required(
                revision_number, "revision_number", "Zeichnungsreferenz"
            )
        )
        result.merge(
            FieldValidator.validate_integer(
                revision_number, "revision_number", "Zeichnungsreferenz"
            )
        )

        return result


class DataConfirmationValidator:
    """
    Validator für Popup 2 - Daten bestätigen.

    Pflichtfelder:
    - Name (oben im Popup)
    - Artikelnummer
    - Lot-Nummer (Format abhängig von Lieferant)
    - Bestellnummer (Int)
    - Liefernummer
    - Lieferscheinmenge
    - LagerNo (Int)
    - OrderNo (Str)
    """

    # Regex-Patterns für Lot-Nummern
    # PRIMEC: Erlaubt P-xxxxxxxxxxxx, P-xxxxxxxxxxxx-xxxx, P-xxxxxxxxxxxx-xxxxx
    PRIMEC_LOT_PATTERN = r"^P-\d{12}(-\d{4,5})?$"
    TERRATS_LOT_PATTERN = r"^.+$"  # Beliebiger String

    @staticmethod
    def validate(data: Dict[str, Any], supplier_id: str) -> ValidationResult:
        """
        Validiert Daten-Bestätigung.

        Args:
            data: {
                employee_name: str,
                article_number: str,
                batch_number: str,
                order_number: str,
                delivery_number: str,
                delivery_slip_quantity: int,
                storage_location: int,
                ordered_quantity: int
            }
            supplier_id: "PRIMEC" oder "TERRATS"

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Name (Pflicht)
        employee_name = data.get("employee_name")
        result.merge(
            FieldValidator.validate_required(
                employee_name, "employee_name", "Mitarbeitername"
            )
        )

        # Artikelnummer (Pflicht)
        article_number = data.get("article_number")
        result.merge(
            FieldValidator.validate_required(
                article_number, "article_number", "Artikelnummer"
            )
        )

        # Lot-Nummer (Pflicht, Format abhängig von Lieferant)
        batch_number = data.get("batch_number")
        result.merge(
            FieldValidator.validate_required(batch_number, "batch_number", "Lot-Nummer")
        )

        # Format-Validierung abhängig von Lieferant
        if batch_number:
            if supplier_id == "PRIMEC":
                lot_result = FieldValidator.validate_regex(
                    batch_number,
                    "batch_number",
                    DataConfirmationValidator.PRIMEC_LOT_PATTERN,
                    "Format muss P-xxxxxxxxxxxx, P-xxxxxxxxxxxx-xxxx oder P-xxxxxxxxxxxx-xxxxx sein (z.B. P-123456789012, P-123456789012-1234 oder P-123456789012-12345)",
                    "Lot-Nummer",
                )
                result.merge(lot_result)
            elif supplier_id == "TERRATS":
                # Beliebiger String erlaubt, aber nicht leer (already checked by required)
                pass
            else:
                # Unbekannter Lieferant - Warning
                result.add_warning(
                    f"Unbekannter Lieferant '{supplier_id}' - Lot-Format wird nicht validiert"
                )

        # Bestellnummer (Pflicht, Int)
        order_number = data.get("order_number")
        result.merge(
            FieldValidator.validate_required(
                order_number, "order_number", "Bestellnummer"
            )
        )
        # Note: order_number könnte auch String sein (OrderNo), prüfe beide Fälle

        # Liefernummer (Pflicht)
        delivery_number = data.get("delivery_number")
        result.merge(
            FieldValidator.validate_required(
                delivery_number, "delivery_number", "Liefernummer"
            )
        )

        # Lieferscheinmenge (Pflicht, Int > 0)
        delivery_slip_quantity = data.get("delivery_slip_quantity")
        result.merge(
            FieldValidator.validate_required(
                delivery_slip_quantity, "delivery_slip_quantity", "Lieferscheinmenge"
            )
        )
        result.merge(
            FieldValidator.validate_integer(
                delivery_slip_quantity,
                "delivery_slip_quantity",
                "Lieferscheinmenge",
                min_value=1,
            )
        )

        # LagerNo (Pflicht, Int)
        storage_location = data.get("storage_location")
        result.merge(
            FieldValidator.validate_required(
                storage_location, "storage_location", "Lagerort"
            )
        )
        result.merge(
            FieldValidator.validate_integer(
                storage_location, "storage_location", "Lagerort"
            )
        )

        # Bestellmenge (optional, aber wenn vorhanden: Int > 0)
        ordered_quantity = data.get("ordered_quantity")
        if ordered_quantity:
            result.merge(
                FieldValidator.validate_integer(
                    ordered_quantity, "ordered_quantity", "Bestellmenge", min_value=1
                )
            )

        return result


class DocumentCheckValidator:
    """
    Validator für Popup 3 - Dokumente bestätigen.

    Pflichtfelder:
    - Label muss aktiviert sein
    - QR-Code muss aktiviert sein
    """

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Dokumenten-Check.

        Args:
            data: {
                employee_name: str,
                label_present: bool,
                qr_code_present: bool
            }

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Mitarbeitername (Pflicht, min 2 Zeichen)
        employee_name = data.get("employee_name")
        result.merge(
            FieldValidator.validate_required(
                employee_name, "employee_name", "Mitarbeitername"
            )
        )
        if employee_name:
            result.merge(
                FieldValidator.validate_string_length(
                    employee_name,
                    "employee_name",
                    50,
                    "Mitarbeitername",
                    min_length=2,
                )
            )

        # Label muss aktiviert sein
        label_present = data.get("label_present", False)
        result.merge(
            FieldValidator.validate_boolean_true(
                label_present,
                "label_present",
                "Label muss vorhanden sein (Checkbox aktivieren)",
                "Label vorhanden",
            )
        )

        # QR-Code muss aktiviert sein
        qr_code_present = data.get("qr_code_present", False)
        result.merge(
            FieldValidator.validate_boolean_true(
                qr_code_present,
                "qr_code_present",
                "QR-Code muss vorhanden sein (Checkbox aktivieren)",
                "QR-Code vorhanden",
            )
        )

        return result


class MeasurementValidator:
    """
    Validator für Popup 4 - Vermessen.

    Pflichtfelder:
    - Vermessen durchgeführt (Checkbox aktiviert)
    - Prüfername
    """

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Vermessung.

        Args:
            data: {
                measured: bool,
                inspector_name: str
            }

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Vermessen durchgeführt (Checkbox)
        measured = data.get("measured", False)
        result.merge(
            FieldValidator.validate_boolean_true(
                measured,
                "measured",
                "Vermessung muss durchgeführt werden (Checkbox aktivieren)",
                "Vermessen",
            )
        )

        # Prüfername (Pflicht)
        inspector_name = data.get("inspector_name")
        result.merge(
            FieldValidator.validate_required(
                inspector_name, "inspector_name", "Prüfername"
            )
        )

        return result


class VisualInspectionValidator:
    """
    Validator für Popup 5 - Sichtkontrolle.

    Pflichtfelder:
    - Name (oben im Popup)
    - Ausschussmenge
    """

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Sichtkontrolle.

        Args:
            data: {
                inspector_name: str,
                waste_quantity: int
            }

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Prüfername (Pflicht)
        inspector_name = data.get("inspector_name")
        result.merge(
            FieldValidator.validate_required(
                inspector_name, "inspector_name", "Prüfername"
            )
        )

        # Ausschussmenge (Pflicht, Int >= 0)
        waste_quantity = data.get("waste_quantity")
        result.merge(
            FieldValidator.validate_required(
                waste_quantity, "waste_quantity", "Ausschussmenge"
            )
        )
        result.merge(
            FieldValidator.validate_integer(
                waste_quantity, "waste_quantity", "Ausschussmenge", min_value=0
            )
        )

        return result


class DocumentMergeValidator:
    """
    Validator für Popup 6 - Dokumente mergen.

    Pflichtfelder (alle Dokumente):
    - PDB
    - Vermessungsprotokoll
    - Sichtprüfung
    - Orderdokument
    - Lieferschein
    - Begleitpapiere
    """

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Dokumenten-Merge.

        Args:
            data: {
                pdb_available: bool,
                measurement_protocol_available: bool,
                visual_inspection_available: bool,
                order_document_available: bool,
                delivery_slip_available: bool,
                accompanying_documents_available: bool
            }

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Alle Dokumente sind Pflicht
        required_docs = [
            ("pdb_available", "PDB (Produktdatenblatt)"),
            ("measurement_protocol_available", "Vermessungsprotokoll"),
            ("visual_inspection_available", "Sichtprüfung"),
            ("order_document_available", "Orderdokument"),
            ("delivery_slip_available", "Lieferschein"),
            ("accompanying_documents_available", "Begleitpapiere"),
        ]

        for field_name, label in required_docs:
            doc_available = data.get(field_name, False)
            result.merge(
                FieldValidator.validate_boolean_true(
                    doc_available, field_name, f"{label} muss vorhanden sein", label
                )
            )

        return result
