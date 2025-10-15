# src/warehouse/domain/entities/delivery.py

from datetime import datetime, date
from typing import List, Optional, Dict, Any

# from dataclasses import dataclass, field

from warehouse.domain.enums.delivery_status import DeliveryStatus
from warehouse.domain.enums.item_status import ItemStatus
from warehouse.domain.entities.item import Item
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber
from warehouse.domain.exceptions.delivery_exceptions import (
    DeliveryAlreadyCompletedException,
    #    EmptyDeliveryException,
    #    DeliveryAlreadyExistsException,
)
from warehouse.domain.exceptions.item_exceptions import ItemAlreadyExistsException


class Delivery:
    """
    Delivery Aggregate Root für das Warehouse Management System.

    Verwaltet eine komplette Lieferung mit allen enthaltenen Artikeln.
    Zentrale Entity für Rückverfolgbarkeit und Workflow-Management.
    """

    def __init__(
        self,
        delivery_number: str,
        supplier_id: str,
        delivery_date: date,
        employee_name: str,
        document_path: Optional[str] = None,
        notes: Optional[str] = None,
    ):

        # === VALIDIERUNG (NEU) ===
        if not delivery_number or not delivery_number.strip():
            raise ValueError("Lieferscheinnummer darf nicht leer sein")

        if not supplier_id or not supplier_id.strip():
            raise ValueError("Supplier ID darf nicht leer sein")

        if not employee_name or not employee_name.strip():
            raise ValueError("Mitarbeitername darf nicht leer sein")

        if not delivery_date:
            raise ValueError("Lieferdatum ist erforderlich")

        # === KERN-IDENTIFIKATOREN ===
        self.delivery_number = delivery_number
        self.supplier_id = supplier_id
        self.delivery_date = delivery_date

        # === VERARBEITUNG ===
        self.employee_name = employee_name
        self.document_path = document_path  # Pfad zum gescannten Lieferschein

        # === STATUS UND LIFECYCLE ===
        self.status = DeliveryStatus.EMPFANGEN
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # === ARTIKEL-VERWALTUNG ===
        self.items: List[Item] = []

        # === METADATEN ===
        self.notes: str = notes or ""
        self.completed_at: Optional[datetime] = None

    # === ARTIKEL-MANAGEMENT ===

    def add_item(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivered_quantity: int,
        employee_name: Optional[str] = None,
        delivery_slip_quantity: Optional[int] = None,
        ordered_quantity: Optional[int] = None,
    ) -> Item:
        """Fügt einen neuen Artikel zur Lieferung hinzu."""
        if self.status.is_final_status:
            raise DeliveryAlreadyCompletedException(self.delivery_number)

        # Prüfe auf Duplikate
        existing_item = self.find_item(article_number, batch_number)
        if existing_item:
            raise ItemAlreadyExistsException(str(article_number), str(batch_number))

        # Erstelle neuen Artikel
        new_item = Item(
            article_number=article_number,
            batch_number=batch_number,
            delivery_number=self.delivery_number,
            supplier_id=self.supplier_id,
            delivered_quantity=delivered_quantity,
            delivery_slip_quantity=delivery_slip_quantity,
            ordered_quantity=ordered_quantity,
            employee_name=employee_name or self.employee_name,
        )

        self.items.append(new_item)
        self._update_delivery_status()
        self._update_timestamp()

        return new_item

    def find_item(
        self, article_number: ArticleNumber, batch_number: BatchNumber
    ) -> Optional[Item]:
        """Sucht einen Artikel anhand von Artikelnummer und Chargennummer."""
        for item in self.items:
            if (
                item.article_number == article_number
                and item.batch_number == batch_number
            ):
                return item
        return None

    def get_items_by_status(self, status: str) -> List[Item]:
        """
        Gibt alle Artikel mit einem bestimmten Status zurück.

        NEU: Status ist String, nicht ItemStatus Enum.
        Beispiele: "Daten prüfen", "Vermessen", "Abgeschlossen"
        """
        return [item for item in self.items if item.get_current_status() == status]

    def remove_item(
        self, article_number: ArticleNumber, batch_number: BatchNumber
    ) -> bool:
        """Entfernt einen Artikel aus der Lieferung."""
        if self.status.is_final_status:
            raise DeliveryAlreadyCompletedException(self.delivery_number)

        item_to_remove = self.find_item(article_number, batch_number)
        if item_to_remove:
            self.items.remove(item_to_remove)
            self._update_delivery_status()
            self._update_timestamp()
            return True
        return False

    # === STATUS-MANAGEMENT (Automatische Aktualisierung) ===

    def complete_delivery(self, completed_by: str) -> None:
        """
        Schließt die Lieferung manuell ab.
        Prüft, ob alle Artikel abgeschlossen oder Ausschuss sind.
        """
        if self.status.is_final_status:
            raise DeliveryAlreadyCompletedException(self.delivery_number)

        # Prüfe, ob alle Artikel final sind (abgeschlossen oder Ausschuss)
        if not self.all_items_final():
            incomplete_items = self.get_non_final_items()
            item_list = [
                f"{item.article_number}/{item.batch_number} ({item.status.value})"
                for item in incomplete_items
            ]
            raise ValueError(
                f"Folgende Artikel sind noch nicht abgeschlossen: {', '.join(item_list)}"
            )

        self.status = DeliveryStatus.ABGESCHLOSSEN
        self.completed_at = datetime.now()
        self.employee_name = completed_by
        self._update_timestamp()

    def _update_delivery_status(self) -> None:
        """
        Aktualisiert den Lieferungsstatus automatisch basierend auf Artikel-Status.

        Status-Logik:
        1. EMPFANGEN: Keine Artikel oder alle Artikel haben Status ARTIKEL_ANGELEGT
        2. ERFASST: Alle Artikel haben mindestens Status DATEN_GEPRUEFT
        3. IN_BEARBEITUNG: Mindestens ein Artikel hat Status über DATEN_GEPRUEFT
        4. ABGESCHLOSSEN: Alle Artikel haben Status ABGESCHLOSSEN oder AUSSCHUSS
        """
        if not self.items:
            self.status = DeliveryStatus.EMPFANGEN
            return

        # NEU: Status ist jetzt String, nicht Enum
        item_statuses = [item.get_current_status() for item in self.items]

        # Helper: Check if status is final
        def is_final_status(status_str: str) -> bool:
            return status_str in ["Abgeschlossen", "Ausschuss"]

        # 4. ABGESCHLOSSEN: Alle Artikel final (ABGESCHLOSSEN oder AUSSCHUSS)
        if all(is_final_status(status) for status in item_statuses):
            if self.status != DeliveryStatus.ABGESCHLOSSEN:
                self.status = DeliveryStatus.ABGESCHLOSSEN
                self.completed_at = datetime.now()

        # 3. IN_BEARBEITUNG: Mindestens ein Artikel über DATEN_GEPRUEFT
        # NEU: String-basierte Status
        elif any(
            status in ["Vermessen", "Sichtkontrolle", "Dokumente zusammenführen", "Bereit zum Abschluss"]
            for status in item_statuses
        ):
            self.status = DeliveryStatus.IN_BEARBEITUNG

        # 2. ERFASST: Alle Artikel mindestens DATEN_GEPRUEFT (haben "Daten prüfen" abgeschlossen)
        elif all(status != "Daten prüfen" for status in item_statuses):
            self.status = DeliveryStatus.ERFASST

        # 1. EMPFANGEN: Default (alle oder einige Artikel noch bei "Daten prüfen")
        else:
            self.status = DeliveryStatus.EMPFANGEN

    # === BUSINESS LOGIC ===

    def get_total_item_count(self) -> int:
        """Gesamtzahl aller Artikel in der Lieferung."""
        return len(self.items)

    def get_total_quantity(self) -> int:
        """Gesamtmenge aller Artikel in der Lieferung (tatsächlich geliefert)."""
        return sum(item.delivered_quantity for item in self.items)

    def get_completion_percentage(self) -> float:
        """Bearbeitungsfortschritt in Prozent (basierend auf finalen Artikeln)."""
        if not self.items:
            return 0.0

        # NEU: Status ist String
        final_items = len([
            item for item in self.items
            if item.get_current_status() in ["Abgeschlossen", "Ausschuss"]
        ])
        return (final_items / len(self.items)) * 100

    def all_items_final(self) -> bool:
        """Prüft, ob alle Artikel final sind (ABGESCHLOSSEN oder AUSSCHUSS)."""
        # NEU: Status ist String
        return all(
            item.get_current_status() in ["Abgeschlossen", "Ausschuss"]
            for item in self.items
        )

    def all_items_data_checked(self) -> bool:
        """Prüft, ob alle Artikel mindestens Status DATEN_GEPRUEFT haben."""
        # NEU: Status ist String - "Daten prüfen" ist der erste Schritt
        return all(item.get_current_status() != "Daten prüfen" for item in self.items)

    def get_non_final_items(self) -> List[Item]:
        """Gibt alle nicht-finalen Artikel zurück."""
        # NEU: Status ist String
        return [
            item for item in self.items
            if item.get_current_status() not in ["Abgeschlossen", "Ausschuss"]
        ]

    def get_items_needing_data_check(self) -> List[Item]:
        """Gibt Artikel zurück, die noch Datenprüfung benötigen."""
        # NEU: Status ist String
        return [
            item for item in self.items if item.get_current_status() == "Daten prüfen"
        ]

    def has_items_in_processing(self) -> bool:
        """Prüft, ob Artikel in Bearbeitung sind (über DATEN_GEPRUEFT hinaus)."""
        # NEU: Status ist String
        processing_statuses = [
            "Dokumente prüfen",
            "Vermessen",
            "Sichtkontrolle",
            "Dokumente zusammenführen",
            "Bereit zum Abschluss"
        ]
        return any(
            item.get_current_status() in processing_statuses
            for item in self.items
        )

    def _old_has_items_in_processing(self) -> bool:
        """ALTE VERSION - KANN GELÖSCHT WERDEN."""
        processing_statuses = [
            ItemStatus.SICHT_GEPRUEFT,
            ItemStatus.DOKUMENTE_GEPRUEFT,
            ItemStatus.VERMESSEN,
        ]
        return any(item.status in processing_statuses for item in self.items)

    def get_delivery_progress_summary(self) -> Dict[str, Any]:
        """Gibt detaillierte Fortschritts-Übersicht zurück."""
        if not self.items:
            return {
                "total_items": 0,
                "status_distribution": {},
                "current_phase": "Keine Artikel",
            }

        status_counts = {}
        for status in ItemStatus:
            count = len(self.get_items_by_status(status))
            if count > 0:
                status_counts[status.value] = count

        return {
            "total_items": len(self.items),
            "status_distribution": status_counts,
            "current_phase": self._get_current_phase_description(),
            "completion_percentage": self.get_completion_percentage(),
            "items_needing_attention": len(self.get_items_needing_data_check()),
        }

    def _get_current_phase_description(self) -> str:
        """Gibt benutzerfreundliche Beschreibung der aktuellen Phase zurück."""
        if self.status == DeliveryStatus.EMPFANGEN:
            return "Warten auf Datenprüfung"
        elif self.status == DeliveryStatus.ERFASST:
            return "Bereit für Qualitätsprüfung"
        elif self.status == DeliveryStatus.IN_BEARBEITUNG:
            return "Artikel werden bearbeitet"
        elif self.status == DeliveryStatus.ABGESCHLOSSEN:
            return "Lieferung vollständig abgeschlossen"
        else:
            return "Unbekannter Status"

    # === VALIDATION ===

    def can_be_edited(self) -> bool:
        """Prüft, ob Lieferung noch bearbeitet werden kann."""
        return not self.status.is_final_status()

    def validate_for_completion(self) -> List[str]:
        """Validiert Lieferung für Abschluss und gibt Fehlerliste zurück."""
        errors = []

        if not self.items:
            errors.append("Lieferung enthält keine Artikel")

        non_final_items = self.get_non_final_items()
        if non_final_items:
            for item in non_final_items:
                errors.append(
                    f"Artikel {item.article_number}/{item.batch_number} "
                    f"ist nicht final ({item.status.value})"
                )

        return errors

    def can_advance_to_erfasst(self) -> bool:
        """Prüft, ob Lieferung zu ERFASST wechseln kann."""
        return (
            len(self.items) > 0
            and self.all_items_data_checked()
            and self.status == DeliveryStatus.EMPFANGEN
        )

    def can_advance_to_in_bearbeitung(self) -> bool:
        """Prüft, ob Lieferung zu IN_BEARBEITUNG wechseln kann."""
        return self.status == DeliveryStatus.ERFASST and self.has_items_in_processing()

    def can_complete(self) -> bool:
        """Prüft, ob Lieferung abgeschlossen werden kann."""
        return (
            not self.status.is_final_status
            and len(self.items) > 0
            and self.all_items_final()
        )

    # === UTILITY METHODS ===

    def _update_timestamp(self):
        """Aktualisiert den Timestamp bei Änderungen."""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für Persistierung."""
        return {
            "delivery_number": self.delivery_number,
            "supplier_id": self.supplier_id,
            "delivery_date": self.delivery_date.isoformat(),
            "employee_name": self.employee_name,
            "document_path": self.document_path,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
        }

    def get_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Lieferung zurück."""
        # NEU: Status ist String, nicht Enum
        # Sammle alle Status-Strings und zähle Items pro Status
        status_counts = {}
        for item in self.items:
            status = item.get_current_status()
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "delivery_number": self.delivery_number,
            "supplier_id": self.supplier_id,
            "delivery_date": self.delivery_date,
            "status": self.status.value,
            "total_items": len(self.items),
            "total_quantity": sum(item.delivered_quantity for item in self.items),  # NEU: delivered_quantity
            "completion_percentage": self.get_completion_percentage(),
            "items_by_status": status_counts,  # NEU: String-basierte Status
            "phase_description": self._get_current_phase_description(),
        }

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        return f"Delivery({self.delivery_number}, {self.status.value}, {len(self.items)} items)"

    def __repr__(self) -> str:
        """Debug-Repräsentation."""
        return (
            f"Delivery(delivery_number='{self.delivery_number}', "
            f"supplier_id='{self.supplier_id}', "
            f"status={self.status}, "
            f"items_count={len(self.items)})"
        )
