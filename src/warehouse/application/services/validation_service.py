# src/warehouse/application/services/validation_service.py

"""
Validation Service - Application Layer.

Zentrale Facade für alle Validierungen im System.
Wird von den Popups aufgerufen um Daten zu validieren.
"""

import logging
from typing import Dict, Any, Optional

from warehouse.domain.validation.validation_result import ValidationResult
from warehouse.domain.validation.popup_validators import (
    ItemInfoValidator,
    DataConfirmationValidator,
    DocumentCheckValidator,
    MeasurementValidator,
    VisualInspectionValidator,
    DocumentMergeValidator,
)

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Zentrale Validation Service.

    Provides standardized validation methods for all popups.
    """

    def __init__(self):
        """Initialize validation service."""
        pass

    # ============================================================================
    # POPUP 1 - ItemInfo
    # ============================================================================

    def validate_iteminfo(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert ItemInfo-Daten (Popup 1).

        Args:
            data: {
                designation: str,
                storage_location: str (wird zu Int konvertiert),
                manufacturer: str,
                revision_number: int,
                drawing_reference: str (optional)
            }

        Returns:
            ValidationResult

        Example:
            ```python
            from warehouse.application.services.validation_service import validation_service

            data = {
                "designation": "Schraubendreher",
                "storage_location": "123",
                "manufacturer": "Primec",
                "revision_number": 5
            }

            result = validation_service.validate_iteminfo(data)
            if not result.is_valid:
                st.error(result.get_formatted_errors())
            ```
        """
        try:
            logger.debug(f"Validating ItemInfo data: {data}")
            result = ItemInfoValidator.validate(data)

            if result.is_valid:
                logger.info("ItemInfo validation successful")
            else:
                logger.warning(
                    f"ItemInfo validation failed: {result.get_error_messages()}"
                )

            return result

        except Exception as e:
            logger.error(f"Error during ItemInfo validation: {str(e)}")
            logger.exception("Full traceback:")
            return ValidationResult.failure(
                "validation", f"Validierungsfehler: {str(e)}"
            )

    # ============================================================================
    # POPUP 2 - Daten bestätigen
    # ============================================================================

    def validate_data_confirmation(
        self, data: Dict[str, Any], supplier_id: str
    ) -> ValidationResult:
        """
        Validiert Daten-Bestätigung (Popup 2).

        Args:
            data: {
                employee_name: str,
                article_number: str,
                batch_number: str,
                order_number: str,
                delivery_number: str,
                delivery_slip_quantity: int,
                storage_location: int,
                ordered_quantity: int (optional)
            }
            supplier_id: "PRIMEC" oder "TERRATS" (für Lot-Format-Validierung)

        Returns:
            ValidationResult

        Example:
            ```python
            data = {
                "employee_name": "Klaus Krüger",
                "article_number": "12345",
                "batch_number": "P-123456789012/-1234/5",
                "order_number": "ORD-001",
                "delivery_number": "LS24-077",
                "delivery_slip_quantity": 100,
                "storage_location": 42,
                "ordered_quantity": 100
            }

            result = validation_service.validate_data_confirmation(data, "PRIMEC")
            ```
        """
        try:
            logger.debug(
                f"Validating data confirmation for supplier {supplier_id}: {data}"
            )
            result = DataConfirmationValidator.validate(data, supplier_id)

            if result.is_valid:
                logger.info("Data confirmation validation successful")
            else:
                logger.warning(
                    f"Data confirmation validation failed: {result.get_error_messages()}"
                )

            return result

        except Exception as e:
            logger.error(f"Error during data confirmation validation: {str(e)}")
            logger.exception("Full traceback:")
            return ValidationResult.failure(
                "validation", f"Validierungsfehler: {str(e)}"
            )

    # ============================================================================
    # POPUP 3 - Dokumente bestätigen
    # ============================================================================

    def validate_document_check(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Dokumenten-Check (Popup 3).

        Args:
            data: {
                label_present: bool,
                qr_code_present: bool
            }

        Returns:
            ValidationResult

        Example:
            ```python
            data = {
                "label_present": True,
                "qr_code_present": True
            }

            result = validation_service.validate_document_check(data)
            ```
        """
        try:
            logger.debug(f"Validating document check: {data}")
            result = DocumentCheckValidator.validate(data)

            if result.is_valid:
                logger.info("Document check validation successful")
            else:
                logger.warning(
                    f"Document check validation failed: {result.get_error_messages()}"
                )

            return result

        except Exception as e:
            logger.error(f"Error during document check validation: {str(e)}")
            logger.exception("Full traceback:")
            return ValidationResult.failure(
                "validation", f"Validierungsfehler: {str(e)}"
            )

    # ============================================================================
    # POPUP 4 - Vermessen
    # ============================================================================

    def validate_measurement(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Vermessung (Popup 4).

        Args:
            data: {
                measured: bool,
                inspector_name: str
            }

        Returns:
            ValidationResult

        Example:
            ```python
            data = {
                "measured": True,
                "inspector_name": "Klaus Krüger"
            }

            result = validation_service.validate_measurement(data)
            ```
        """
        try:
            logger.debug(f"Validating measurement: {data}")
            result = MeasurementValidator.validate(data)

            if result.is_valid:
                logger.info("Measurement validation successful")
            else:
                logger.warning(
                    f"Measurement validation failed: {result.get_error_messages()}"
                )

            return result

        except Exception as e:
            logger.error(f"Error during measurement validation: {str(e)}")
            logger.exception("Full traceback:")
            return ValidationResult.failure(
                "validation", f"Validierungsfehler: {str(e)}"
            )

    # ============================================================================
    # POPUP 5 - Sichtkontrolle
    # ============================================================================

    def validate_visual_inspection(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Sichtkontrolle (Popup 5).

        Args:
            data: {
                inspector_name: str,
                waste_quantity: int
            }

        Returns:
            ValidationResult

        Example:
            ```python
            data = {
                "inspector_name": "Klaus Krüger",
                "waste_quantity": 5
            }

            result = validation_service.validate_visual_inspection(data)
            ```
        """
        try:
            logger.debug(f"Validating visual inspection: {data}")
            result = VisualInspectionValidator.validate(data)

            if result.is_valid:
                logger.info("Visual inspection validation successful")
            else:
                logger.warning(
                    f"Visual inspection validation failed: {result.get_error_messages()}"
                )

            return result

        except Exception as e:
            logger.error(f"Error during visual inspection validation: {str(e)}")
            logger.exception("Full traceback:")
            return ValidationResult.failure(
                "validation", f"Validierungsfehler: {str(e)}"
            )

    # ============================================================================
    # POPUP 6 - Dokumente mergen
    # ============================================================================

    def validate_document_merge(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validiert Dokumenten-Merge (Popup 6).

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

        Example:
            ```python
            data = {
                "pdb_available": True,
                "measurement_protocol_available": True,
                "visual_inspection_available": True,
                "order_document_available": True,
                "delivery_slip_available": True,
                "accompanying_documents_available": True
            }

            result = validation_service.validate_document_merge(data)
            ```
        """
        try:
            logger.debug(f"Validating document merge: {data}")
            result = DocumentMergeValidator.validate(data)

            if result.is_valid:
                logger.info("Document merge validation successful")
            else:
                logger.warning(
                    f"Document merge validation failed: {result.get_error_messages()}"
                )

            return result

        except Exception as e:
            logger.error(f"Error during document merge validation: {str(e)}")
            logger.exception("Full traceback:")
            return ValidationResult.failure(
                "validation", f"Validierungsfehler: {str(e)}"
            )


# ============================================================================
# GLOBAL SINGLETON INSTANCE
# ============================================================================

validation_service = ValidationService()
