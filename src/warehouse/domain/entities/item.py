# src/warehouse/domain/entities/item.py

"""
Item Entity mit Workflow-Steps Status-System.

Dieses Modul enthält die Kern-Entity für Artikel im Warehouse Management System.
Implementiert ein Workflow-basiertes Status-System für Medizinprodukte-Rückverfolgbarkeit.

Workflow-Reihenfolge:
1. Daten prüfen
2. Dokumente prüfen
3. Vermessen
4. Sichtkontrolle
5. Dokumente zusammenführen
6. Abschließen

Status = Erster nicht-erfüllter Schritt

Classes:
    InspectionResult: Value Object für Prüfungsergebnisse
    Item: Hauptentity für Artikel mit Workflow-Steps Management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

from warehouse.domain.enums.item_status import ItemStatus
from warehouse.domain.enums.certificate_type import CertificateType
from warehouse.domain.enums.priority_level import PriorityLevel
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber
from warehouse.domain.exceptions.item_exceptions import ItemNotEditableException


@dataclass
class InspectionResult:
    """Value Object für Prüfungsergebnisse."""

    performed_at: datetime
    performed_by: str
    waste_quantity: int = 0
    waste_reason: Optional[str] = None
    quality_notes: Optional[str] = None
    measurements: Dict[str, Any] = field(default_factory=dict)
    passed: bool = True

    def calculate_waste_percentage(self, total_quantity: int) -> Decimal:
        """Berechnet Ausschussquote."""
        if total_quantity <= 0:
            return Decimal("0")
        return Decimal(self.waste_quantity) / Decimal(total_quantity) * Decimal("100")


class Item:
    """
    Kern-Entity für Artikel im Warehouse Management System.

    Repräsentiert einen einzelnen Artikel einer Lieferung mit vollständiger
    Rückverfolgbarkeit und Compliance-Dokumentation für Medizinprodukte.

    Status-System:
    - Workflow-Steps Tabelle trackt Fortschritt
    - Status wird berechnet als "Erster nicht-erfüllter Schritt"
    - Jeder Step speichert: Wer + Wann
    """

    def __init__(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
        supplier_id: str,
        delivered_quantity: int,
        employee_name: Optional[str] = None,
        priority_level: PriorityLevel = PriorityLevel.MEDIUM,
        order_number: Optional[str] = None,
        delivery_slip_quantity: Optional[int] = None,
        ordered_quantity: Optional[int] = None,
    ):
        # === RÜCKVERFOLGBARKEIT (Kern-Identifikatoren) ===
        self.article_number = article_number
        self.batch_number = batch_number
        self.delivery_number = delivery_number
        self.supplier_id = supplier_id
        self.order_number = order_number

        # === MENGEN-TRACKING ===
        self.delivered_quantity = delivered_quantity
        self.delivery_slip_quantity = delivery_slip_quantity
        self.ordered_quantity = ordered_quantity

        # === BASIS-INFORMATIONEN ===
        self.created_by = employee_name
        self.priority_level = priority_level

        # === WORKFLOW STEPS (von DB geladen, initial alle None) ===
        # Step 0: Artikeldetails vollständig (ItemInfo erstellt)
        self.iteminfo_complete_by: Optional[str] = None
        self.iteminfo_complete_at: Optional[datetime] = None

        # Step 1: Daten prüfen
        self.data_checked_by: Optional[str] = None
        self.data_checked_at: Optional[datetime] = None

        # Step 2: Dokumente prüfen
        self.documents_checked_by: Optional[str] = None
        self.documents_checked_at: Optional[datetime] = None

        # Step 3: Vermessen
        self.measured_by: Optional[str] = None
        self.measured_at: Optional[datetime] = None

        # Step 4: Sichtkontrolle
        self.visually_inspected_by: Optional[str] = None
        self.visually_inspected_at: Optional[datetime] = None

        # Step 5: Dokumente zusammenführen
        self.documents_merged_by: Optional[str] = None
        self.documents_merged_at: Optional[datetime] = None

        # Finale Status
        self.completed_by: Optional[str] = None
        self.completed_at: Optional[datetime] = None

        self.rejected_by: Optional[str] = None
        self.rejected_at: Optional[datetime] = None
        self.rejection_reason: Optional[str] = None

        # === LIFECYCLE ===
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # === ZERTIFIKATE (Manual Dialog) ===
        self.certificates: Dict[CertificateType, bool] = {}
        self._initialize_certificate_flags()

        # === PRÜFUNG UND QUALITÄT ===
        self.inspection_result: Optional[InspectionResult] = None

        # === ZUSÄTZLICHE METADATEN ===
        self.notes: str = ""
        self.barcode: Optional[str] = None
        self.storage_location: Optional[str] = None

    def _initialize_certificate_flags(self):
        """Initialisiert Zertifikats-Flags für manuellen Dialog."""
        standard_certificates = [
            CertificateType.MATERIALZEUGNIS,
            CertificateType.MESSPROTOKOLL,
            CertificateType.HAERTEZEUGNIS,
            CertificateType.BESCHICHTUNGSZEUGNIS,
            CertificateType.WEITERE_ZEUGNISSE,
        ]

        for cert_type in standard_certificates:
            self.certificates[cert_type] = False

    # === WORKFLOW METHODS ===

    def is_step_completed(self, step) -> bool:
        """
        Prüft ob ein Workflow-Schritt abgeschlossen ist.

        Unterstützt sowohl alte ItemStatus Enum-Werte als auch neue String-Namen.

        Args:
            step: Kann sein:
                - ItemStatus Enum (z.B. ItemStatus.DATEN_GEPRUEFT) - für Backward Compatibility
                - String (z.B. "Daten prüfen", "Dokumente prüfen")

        Returns:
            True wenn der Schritt abgeschlossen ist
        """
        from warehouse.domain.enums.item_status import ItemStatus

        # Mapping: Alte ItemStatus Enum → Neue Workflow-Step-Felder
        step_mapping = {
            ItemStatus.DATEN_GEPRUEFT: self.data_checked_by,
            ItemStatus.DOKUMENTE_GEPRUEFT: self.documents_checked_by,
            ItemStatus.VERMESSEN: self.measured_by,
            ItemStatus.SICHT_GEPRUEFT: self.visually_inspected_by,
            # DOKUMENTE_ZUSAMMENGEFUEHRT gibt es nicht im alten Enum, aber hier für Vollständigkeit:
            "Dokumente zusammenführen": self.documents_merged_by,
        }

        # String-basierte Prüfung
        string_mapping = {
            "Artikeldetails vollständig": self.iteminfo_complete_by,
            "Daten prüfen": self.data_checked_by,
            "Dokumente prüfen": self.documents_checked_by,
            "Vermessen": self.measured_by,
            "Sichtkontrolle": self.visually_inspected_by,
            "Dokumente zusammenführen": self.documents_merged_by,
        }

        # Prüfe ob step ein Enum ist
        if hasattr(step, "value"):
            # ItemStatus Enum
            return step_mapping.get(step) is not None
        else:
            # String
            return string_mapping.get(str(step)) is not None

    def complete_data_check(self, employee: str) -> None:
        """
        Schließt Datenprüfung ab (Step 1).
        Prüfung von: Artikelnummer, Chargennummer, Liefermenge.
        """
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        self.data_checked_by = employee
        self.data_checked_at = datetime.now()
        self._update_timestamp()

    def complete_document_check(self, employee: str) -> None:
        """
        Schließt Dokumentenprüfung ab (Step 2).
        Prüfung von: Zertifikaten, Begleitpapieren.
        """
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        self.documents_checked_by = employee
        self.documents_checked_at = datetime.now()
        self._update_timestamp()

    def complete_measurement(self, measurements: Dict[str, Any], employee: str) -> None:
        """
        Schließt Vermessung ab (Step 3).
        Speichert Messwerte im InspectionResult.
        """
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        if not self.inspection_result:
            # Erstelle InspectionResult falls nicht vorhanden
            self.inspection_result = InspectionResult(
                performed_at=datetime.now(), performed_by=employee
            )

        self.inspection_result.measurements.update(measurements)
        self.measured_by = employee
        self.measured_at = datetime.now()
        self._update_timestamp()

    def complete_visual_inspection(self, inspection: InspectionResult) -> None:
        """
        Schließt Sichtkontrolle ab (Step 4).
        Speichert visuelle Prüfungsergebnisse.
        """
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        self.inspection_result = inspection
        self.visually_inspected_by = inspection.performed_by
        self.visually_inspected_at = datetime.now()
        self._update_timestamp()

    def complete_documents_merge(self, employee: str) -> None:
        """
        Schließt Dokumentenzusammenführung ab (Step 5).
        Alle Dokumente (PDB, Begleitschein, etc.) werden generiert/zusammengeführt.
        """
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        self.documents_merged_by = employee
        self.documents_merged_at = datetime.now()
        self._update_timestamp()

    def complete_processing(self, employee: str) -> None:
        """
        Schließt Artikelbearbeitung ab (Final).
        Nur möglich wenn ALLE Workflow-Steps abgeschlossen sind.
        """
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        # Prüfe ob alle Steps done
        missing_steps = self.get_missing_steps()
        if missing_steps:
            raise ValueError(
                f"Folgende Schritte fehlen noch: {', '.join(missing_steps)}"
            )

        self.completed_by = employee
        self.completed_at = datetime.now()
        self._update_timestamp()

    def mark_as_rejected(self, reason: str, employee: str) -> None:
        """Markiert Artikel als Ausschuss (Final)."""
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        self.rejected_by = employee
        self.rejected_at = datetime.now()
        self.rejection_reason = reason
        self.notes = f"AUSSCHUSS: {reason}"
        self._update_timestamp()

    # === STATUS QUERIES ===

    def get_current_status(self) -> str:
        """
        Berechnet aktuellen Status = Erster nicht-erfüllter Schritt.

        Workflow-Reihenfolge (fest):
        1. Daten prüfen
        2. Dokumente prüfen
        3. Vermessen
        4. Sichtkontrolle
        5. Dokumente zusammenführen
        6. Abschließen

        Returns:
            Status als String für UI-Anzeige
        """
        # Finale Status haben Vorrang
        if self.completed_by:
            return "Abgeschlossen"
        if self.rejected_by:
            return "Ausschuss"

        # Workflow-Reihenfolge (fest definiert)
        if not self.data_checked_by:
            return "Daten prüfen"

        if not self.documents_checked_by:
            return "Dokumente prüfen"

        if not self.measured_by:
            return "Vermessen"

        if not self.visually_inspected_by:
            return "Sichtkontrolle"

        if not self.documents_merged_by:
            return "Dokumente zusammenführen"

        # Alle Steps erledigt
        return "Bereit zum Abschluss"

    @property
    def status(self) -> str:
        """
        Status-Property für Kompatibilität.
        Gibt aktuellen Status als String zurück.
        """
        return self.get_current_status()

    def get_missing_steps(self) -> List[str]:
        """
        Gibt Liste fehlender Workflow-Steps zurück.

        Returns:
            Liste mit Namen der fehlenden Steps
        """
        missing = []

        if not self.data_checked_by:
            missing.append("Datenprüfung")
        if not self.documents_checked_by:
            missing.append("Dokumentenprüfung")
        if not self.measured_by:
            missing.append("Vermessung")
        if not self.visually_inspected_by:
            missing.append("Sichtkontrolle")
        if not self.documents_merged_by:
            missing.append("Dokumentenzusammenführung")

        return missing

    def get_completion_percentage(self) -> float:
        """
        Berechnet Fortschritt in Prozent.

        Returns:
            Prozentsatz (0-100)
        """
        total_steps = 5  # data, documents, measurement, visual, merge
        completed_steps = sum(
            [
                bool(self.data_checked_by),
                bool(self.documents_checked_by),
                bool(self.measured_by),
                bool(self.visually_inspected_by),
                bool(self.documents_merged_by),
            ]
        )

        return (completed_steps / total_steps) * 100

    def is_final_status(self) -> bool:
        """Prüft ob Item in Finalstatus (Abgeschlossen oder Ausschuss)."""
        return bool(self.completed_by or self.rejected_by)

    def can_be_edited(self) -> bool:
        """Prüft ob Item editierbar ist (nicht im Finalstatus)."""
        return not self.is_final_status()

    def is_ready_for_completion(self) -> bool:
        """Prüft ob Item bereit zum Abschließen ist (alle Steps done)."""
        return not self.get_missing_steps() and not self.is_final_status()

    def get_workflow_summary(self) -> Dict[str, Any]:
        """
        Gibt vollständige Workflow-Übersicht zurück.

        Returns:
            Dictionary mit aktuellem Status und Step-Details
        """
        return {
            "current_status": self.get_current_status(),
            "completion_percentage": self.get_completion_percentage(),
            "missing_steps": self.get_missing_steps(),
            "is_final": self.is_final_status(),
            "is_ready_for_completion": self.is_ready_for_completion(),
            "steps": {
                "data_checked": {
                    "completed": bool(self.data_checked_by),
                    "by": self.data_checked_by,
                    "at": self.data_checked_at.isoformat()
                    if self.data_checked_at
                    else None,
                },
                "documents_checked": {
                    "completed": bool(self.documents_checked_by),
                    "by": self.documents_checked_by,
                    "at": self.documents_checked_at.isoformat()
                    if self.documents_checked_at
                    else None,
                },
                "measured": {
                    "completed": bool(self.measured_by),
                    "by": self.measured_by,
                    "at": self.measured_at.isoformat() if self.measured_at else None,
                },
                "visually_inspected": {
                    "completed": bool(self.visually_inspected_by),
                    "by": self.visually_inspected_by,
                    "at": self.visually_inspected_at.isoformat()
                    if self.visually_inspected_at
                    else None,
                },
                "documents_merged": {
                    "completed": bool(self.documents_merged_by),
                    "by": self.documents_merged_by,
                    "at": self.documents_merged_at.isoformat()
                    if self.documents_merged_at
                    else None,
                },
            },
        }

    # === PRIORITY MANAGEMENT ===

    def set_priority_level(self, priority_level: PriorityLevel) -> None:
        """Setzt neues Priority Level."""
        if self.is_final_status():
            raise ItemNotEditableException(self.get_current_status())

        self.priority_level = priority_level
        self._update_timestamp()

    def get_priority_display_color(self) -> str:
        """Gibt Farbe für UI-Anzeige der Priorität zurück."""
        return self.priority_level.get_display_color()

    # === CERTIFICATE MANAGEMENT ===

    def set_certificate_present(
        self, certificate_type: CertificateType, present: bool
    ) -> None:
        """Setzt Flag ob Zertifikat vorhanden ist."""
        self.certificates[certificate_type] = present
        self._update_timestamp()

    def get_missing_certificates(self) -> List[CertificateType]:
        """Gibt Liste fehlender Zertifikate zurück."""
        return [cert for cert, present in self.certificates.items() if not present]

    def has_required_certificates(self) -> bool:
        """Prüft ob alle erforderlichen Zertifikate vorhanden sind."""
        # Mindestens Materialzeugnis erforderlich
        return self.certificates.get(CertificateType.MATERIALZEUGNIS, False)

    # === QUANTITY CALCULATIONS (Business Logic) ===

    def get_good_quantity(self) -> int:
        """
        Berechnet verwertbare Menge (Geliefert - Ausschuss).

        Returns:
            Gutmenge
        """
        waste = 0
        if self.inspection_result:
            waste = self.inspection_result.waste_quantity
        return max(0, self.delivered_quantity - waste)

    def get_waste_percentage(self) -> Decimal:
        """
        Berechnet Ausschussquote.

        Returns:
            Prozentsatz des Ausschusses
        """
        if self.delivered_quantity <= 0:
            return Decimal("0")

        waste = 0
        if self.inspection_result:
            waste = self.inspection_result.waste_quantity

        return Decimal(waste) / Decimal(self.delivered_quantity) * Decimal("100")

    def has_delivery_slip_discrepancy(self) -> bool:
        """
        Prüft ob Lieferschein und tatsächliche Lieferung abweichen.

        Returns:
            True wenn Abweichung existiert
        """
        if self.delivery_slip_quantity is None:
            return False
        return self.delivered_quantity != self.delivery_slip_quantity

    def has_order_discrepancy(self) -> bool:
        """
        Prüft ob Bestellung und Lieferung abweichen.

        Returns:
            True wenn Abweichung existiert
        """
        if self.ordered_quantity is None:
            return False
        return self.delivered_quantity != self.ordered_quantity

    def get_slip_difference(self) -> int:
        """
        Berechnet Differenz: Geliefert - Lieferschein.

        Returns:
            Differenz (positiv = mehr geliefert, negativ = weniger geliefert)
        """
        if self.delivery_slip_quantity is None:
            return 0
        return self.delivered_quantity - self.delivery_slip_quantity

    def get_order_difference(self) -> int:
        """
        Berechnet Differenz: Geliefert - Bestellt.

        Returns:
            Differenz (positiv = mehr geliefert, negativ = weniger geliefert)
        """
        if self.ordered_quantity is None:
            return 0
        return self.delivered_quantity - self.ordered_quantity

    def get_quantity_report(self) -> Dict[str, Any]:
        """
        Gibt vollständigen Mengenbericht zurück.

        Returns:
            Dictionary mit allen Mengenangaben und Abweichungen
        """
        waste = 0
        if self.inspection_result:
            waste = self.inspection_result.waste_quantity

        return {
            "ordered": self.ordered_quantity,
            "delivery_slip": self.delivery_slip_quantity,
            "delivered": self.delivered_quantity,
            "slip_discrepancy": self.get_slip_difference(),
            "order_discrepancy": self.get_order_difference(),
            "waste": waste,
            "good_quantity": self.get_good_quantity(),
            "waste_percentage": float(self.get_waste_percentage()),
        }

    # === UTILITY METHODS ===

    def generate_barcode_content(self) -> str:
        """
        Generiert Barcode-Inhalt für diesen Artikel.

        Returns:
            Barcode-String
        """
        return f"{self.article_number}-{self.batch_number}-{self.delivery_number}"

    def _update_timestamp(self):
        """Aktualisiert updated_at Timestamp."""
        self.updated_at = datetime.now()

    def get_unique_identifier(self) -> str:
        """
        Gibt eindeutige ID für Rückverfolgbarkeit zurück.

        Returns:
            Composite Key als String
        """
        return f"{self.article_number}#{self.batch_number}#{self.delivery_number}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialisiert Item zu Dictionary für API/UI.

        Returns:
            Dictionary-Repräsentation des Items
        """
        return {
            # Identität
            "article_number": str(self.article_number),
            "batch_number": str(self.batch_number),
            "delivery_number": self.delivery_number,
            "supplier_id": self.supplier_id,
            "order_number": self.order_number,
            "unique_identifier": self.get_unique_identifier(),
            # Mengen
            "delivered_quantity": self.delivered_quantity,
            "delivery_slip_quantity": self.delivery_slip_quantity,
            "ordered_quantity": self.ordered_quantity,
            "good_quantity": self.get_good_quantity(),
            # Status & Workflow
            "current_status": self.get_current_status(),
            "completion_percentage": self.get_completion_percentage(),
            "missing_steps": self.get_missing_steps(),
            "is_final": self.is_final_status(),
            # Workflow Steps
            "workflow": self.get_workflow_summary(),
            # Zertifikate
            "certificates": {
                cert.value: present for cert, present in self.certificates.items()
            },
            "missing_certificates": [
                cert.value for cert in self.get_missing_certificates()
            ],
            # Prüfung
            "inspection_result": self._serialize_inspection_result(),
            # Metadaten
            "priority_level": self.priority_level.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
            "barcode": self.generate_barcode_content(),
            "storage_location": self.storage_location,
        }

    def _serialize_inspection_result(self) -> Optional[Dict[str, Any]]:
        """Serialisiert InspectionResult zu Dictionary."""
        if not self.inspection_result:
            return None

        return {
            "performed_at": self.inspection_result.performed_at.isoformat(),
            "performed_by": self.inspection_result.performed_by,
            "waste_quantity": self.inspection_result.waste_quantity,
            "waste_reason": self.inspection_result.waste_reason,
            "quality_notes": self.inspection_result.quality_notes,
            "measurements": self.inspection_result.measurements,
            "passed": self.inspection_result.passed,
        }

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        return f"Item({self.article_number}, {self.batch_number}, {self.get_current_status()})"

    def __repr__(self) -> str:
        """Debug-Repräsentation."""
        return (
            f"Item(article_number={self.article_number}, "
            f"batch_number={self.batch_number}, "
            f"delivery_number='{self.delivery_number}', "
            f"status='{self.get_current_status()}')"
        )
