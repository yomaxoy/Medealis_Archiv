# src/warehouse/domain/repositories/delivery_repository.py

"""
Delivery Repository Interface für das Warehouse Management System.

ERWEITERT um Domain Object Methoden für Clean Architecture Migration.
Bestehende Methoden bleiben unverändert erhalten.

Definiert spezifische Datenzugriffs-Methoden für Delivery-Entities.
Fokus auf Lieferungsmanagement, Status-Tracking und Workflow-Unterstützung.
"""

from abc import abstractmethod
from typing import List, Optional
from datetime import datetime, date

from warehouse.domain.repositories.base_repository import BaseRepository
from warehouse.domain.entities.delivery import Delivery
from warehouse.domain.enums.delivery_status import DeliveryStatus


class DeliveryRepository(BaseRepository[Delivery]):
    """
    Repository Interface für Delivery-Entities.

    Erweitert BaseRepository um Delivery-spezifische Abfrage-Methoden
    für Lieferungsmanagement und Workflow-Tracking.

    ERWEITERT um Domain Object Methoden für Clean Architecture.
    """

    # === DOMAIN OBJECT METHODS (NEU) ===

    @abstractmethod
    def save_domain(self, delivery: Delivery) -> str:
        """
        Speichert Delivery Domain Entity.

        Args:
            delivery: Delivery Domain Entity

        Returns:
            delivery_number der gespeicherten Delivery
        """

    @abstractmethod
    def find_domain_by_delivery_number(
        self, delivery_number: str
    ) -> Optional[Delivery]:
        """
        Sucht Delivery Domain Entity per Lieferscheinnummer.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            Delivery Domain Entity oder None
        """

    @abstractmethod
    def find_domain_by_supplier(self, supplier_id: str) -> List[Delivery]:
        """
        Sucht alle Delivery Domain Entities eines Lieferanten.

        Args:
            supplier_id: Lieferanten-ID

        Returns:
            Liste von Delivery Domain Entities
        """

    @abstractmethod
    def find_domain_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        """
        Sucht Delivery Domain Entities nach Status.

        Args:
            status: DeliveryStatus Enum

        Returns:
            Liste von Delivery Domain Entities
        """

    @abstractmethod
    def find_domain_all(self) -> List[Delivery]:
        """
        Gibt alle Deliveries als Domain Entities zurück.

        Returns:
            Liste aller Delivery Domain Entities
        """

    @abstractmethod
    def delete_domain(self, delivery_number: str) -> bool:
        """
        Löscht Delivery Domain Entity.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """

    @abstractmethod
    def exists_domain(self, delivery_number: str) -> bool:
        """
        Prüft ob Delivery Domain Entity existiert.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            True wenn existiert
        """

    # === DOMAIN OBJECT CONVENIENCE METHODS ===

    @abstractmethod
    def find_domain_by_employee(self, employee_name: str) -> List[Delivery]:
        """
        Sucht Deliveries eines Mitarbeiters als Domain Entities.

        Args:
            employee_name: Name des Mitarbeiters

        Returns:
            Liste von Delivery Domain Entities
        """

    @abstractmethod
    def find_domain_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Delivery]:
        """
        Sucht Deliveries in Datumsbereich als Domain Entities.

        Args:
            start_date: Startdatum
            end_date: Enddatum

        Returns:
            Liste von Delivery Domain Entities
        """

    @abstractmethod
    def find_domain_pending(self) -> List[Delivery]:
        """
        Sucht alle noch nicht abgeschlossenen Deliveries als Domain Entities.

        Returns:
            Liste von Delivery Domain Entities die noch bearbeitet werden
        """

    # === BESTEHENDE CORE IDENTIFIER QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_delivery_number(self, delivery_number: str) -> Optional[Delivery]:
        """
        Sucht Delivery anhand der Lieferscheinnummer.

        Args:
            delivery_number: Eindeutige Lieferscheinnummer

        Returns:
            Gefundene Delivery oder None
        """

    @abstractmethod
    def delivery_number_exists(self, delivery_number: str) -> bool:
        """
        Prüft, ob eine Lieferscheinnummer bereits existiert.

        Args:
            delivery_number: Zu prüfende Lieferscheinnummer

        Returns:
            True wenn bereits vorhanden, False sonst
        """

    # === BESTEHENDE SUPPLIER-RELATED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_supplier(self, supplier_id: str) -> List[Delivery]:
        """
        Sucht alle Deliveries eines bestimmten Lieferanten.

        Args:
            supplier_id: Lieferanten-ID

        Returns:
            Liste aller Deliveries des Lieferanten
        """

    @abstractmethod
    def find_by_supplier_and_status(
        self, supplier_id: str, status: DeliveryStatus
    ) -> List[Delivery]:
        """
        Sucht Deliveries eines Lieferanten mit bestimmtem Status.

        Args:
            supplier_id: Lieferanten-ID
            status: Gewünschter Delivery-Status

        Returns:
            Liste der gefundenen Deliveries
        """

    @abstractmethod
    def get_supplier_delivery_count(self, supplier_id: str) -> int:
        """
        Zählt Deliveries eines Lieferanten.

        Args:
            supplier_id: Lieferanten-ID

        Returns:
            Anzahl der Deliveries
        """

    # === BESTEHENDE STATUS-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        """
        Sucht Deliveries mit bestimmtem Status.

        Args:
            status: Gewünschter Status

        Returns:
            Liste aller Deliveries mit diesem Status
        """

    @abstractmethod
    def find_pending_deliveries(self) -> List[Delivery]:
        """
        Sucht alle noch nicht abgeschlossenen Deliveries.

        Returns:
            Liste der Deliveries, die noch bearbeitet werden müssen
        """

    @abstractmethod
    def find_completed_deliveries(self) -> List[Delivery]:
        """
        Sucht alle abgeschlossenen Deliveries.

        Returns:
            Liste der abgeschlossenen Deliveries
        """

    @abstractmethod
    def find_deliveries_needing_data_check(self) -> List[Delivery]:
        """
        Sucht Deliveries, die Datenprüfung benötigen.

        Status: EMPFANGEN mit Items, die noch ARTIKEL_ANGELEGT sind

        Returns:
            Liste der Deliveries, die KI-Bestätigung brauchen
        """

    @abstractmethod
    def find_deliveries_in_processing(self) -> List[Delivery]:
        """
        Sucht Deliveries, die gerade bearbeitet werden.

        Status: ERFASST oder IN_BEARBEITUNG

        Returns:
            Liste der Deliveries in Bearbeitung
        """

    # === BESTEHENDE DATE-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_delivery_date(self, delivery_date: date) -> List[Delivery]:
        """
        Sucht Deliveries nach Lieferdatum.

        Args:
            delivery_date: Lieferdatum

        Returns:
            Liste der Deliveries vom Datum
        """

    @abstractmethod
    def find_by_delivery_date_range(
        self, start_date: date, end_date: date
    ) -> List[Delivery]:
        """
        Sucht Deliveries in einem Datumsbereich.

        Args:
            start_date: Startdatum (inklusive)
            end_date: Enddatum (inklusive)

        Returns:
            Liste der Deliveries im Zeitraum
        """

    @abstractmethod
    def find_created_between(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> List[Delivery]:
        """
        Sucht Deliveries, die in einem Zeitraum erstellt wurden.

        Args:
            start_datetime: Start-Zeitpunkt (inklusive)
            end_datetime: End-Zeitpunkt (inklusive)

        Returns:
            Liste der Deliveries im Zeitraum
        """

    @abstractmethod
    def find_completed_between(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> List[Delivery]:
        """
        Sucht Deliveries, die in einem Zeitraum abgeschlossen wurden.

        Args:
            start_datetime: Start-Zeitpunkt (inklusive)
            end_datetime: End-Zeitpunkt (inklusive)

        Returns:
            Liste der abgeschlossenen Deliveries im Zeitraum
        """

    @abstractmethod
    def find_overdue_deliveries(self, days_threshold: int = 7) -> List[Delivery]:
        """
        Sucht überfällige Deliveries.

        Kriterien: Nicht abgeschlossen und älter als Schwellenwert

        Args:
            days_threshold: Anzahl Tage für Überfälligkeit

        Returns:
            Liste der überfälligen Deliveries
        """

    # === BESTEHENDE EMPLOYEE-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_employee(self, employee_name: str) -> List[Delivery]:
        """
        Sucht Deliveries eines bestimmten Mitarbeiters.

        Args:
            employee_name: Name des Mitarbeiters

        Returns:
            Liste aller Deliveries des Mitarbeiters
        """

    @abstractmethod
    def find_by_employee_and_status(
        self, employee_name: str, status: DeliveryStatus
    ) -> List[Delivery]:
        """
        Sucht Deliveries eines Mitarbeiters mit bestimmtem Status.

        Args:
            employee_name: Name des Mitarbeiters
            status: Gewünschter Status

        Returns:
            Liste der gefundenen Deliveries
        """

    # === BESTEHENDE DOCUMENT-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_with_document_path(self) -> List[Delivery]:
        """
        Sucht Deliveries mit hinterlegtem Dokumentenpfad.

        Returns:
            Liste der Deliveries mit gescannten Lieferscheinen
        """

    @abstractmethod
    def find_without_document_path(self) -> List[Delivery]:
        """
        Sucht Deliveries ohne hinterlegten Dokumentenpfad.

        Returns:
            Liste der Deliveries ohne gescannte Lieferscheine
        """

    # === BESTEHENDE ANALYTICS & STATISTICS (UNVERÄNDERT) ===

    @abstractmethod
    def get_status_distribution(self) -> dict:
        """
        Gibt Verteilung der Deliveries nach Status zurück.

        Returns:
            Dictionary mit Status -> Anzahl Deliveries
        """

    @abstractmethod
    def get_supplier_statistics(self) -> dict:
        """
        Gibt Statistiken pro Lieferant zurück.

        Returns:
            Dictionary mit Lieferant -> Delivery-Statistiken
        """

    @abstractmethod
    def get_delivery_volume_by_month(self, year: int) -> dict:
        """
        Gibt monatliche Delivery-Volumina für ein Jahr zurück.

        Args:
            year: Jahr für Statistik

        Returns:
            Dictionary mit Monat -> Anzahl Deliveries
        """

    @abstractmethod
    def get_completion_rate_statistics(self) -> dict:
        """
        Gibt Abschlussraten-Statistiken zurück.

        Returns:
            Dictionary mit verschiedenen Completion-Metriken
        """

    @abstractmethod
    def get_employee_workload_statistics(self) -> dict:
        """
        Gibt Arbeitslasten-Statistiken pro Mitarbeiter zurück.

        Returns:
            Dictionary mit Mitarbeiter -> Delivery-Statistiken
        """

    @abstractmethod
    def get_average_processing_time(self) -> float:
        """
        Berechnet durchschnittliche Bearbeitungszeit für Deliveries.

        Returns:
            Durchschnittliche Zeit in Tagen
        """

    # === BESTEHENDE SEARCH & FILTERING (UNVERÄNDERT) ===

    @abstractmethod
    def search_deliveries(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Delivery]:
        """
        Volltextsuche in Deliveries.

        Args:
            search_term: Suchbegriff
            search_fields: Felder für Suche (None = alle durchsuchbaren Felder)

        Returns:
            Liste der gefundenen Deliveries
        """

    @abstractmethod
    def find_by_advanced_criteria(self, criteria: dict) -> List[Delivery]:
        """
        Erweiterte Suche mit komplexen Kriterien.

        Unterstützt verschachtelte Abfragen für Status, Daten,
        Lieferanten, Mitarbeiter, etc.

        Args:
            criteria: Erweiterte Suchkriterien

        Returns:
            Liste der gefundenen Deliveries
        """

    # === BESTEHENDE WORKFLOW SUPPORT (UNVERÄNDERT) ===

    @abstractmethod
    def find_deliveries_requiring_attention(self) -> List[Delivery]:
        """
        Sucht Deliveries, die Aufmerksamkeit benötigen.

        Kriterien:
        - Überfällig
        - Lange in gleichem Status
        - Mit problematischen Items

        Returns:
            Liste der Deliveries, die Aufmerksamkeit brauchen
        """

    @abstractmethod
    def find_deliveries_ready_for_next_step(self) -> List[Delivery]:
        """
        Sucht Deliveries, die für den nächsten Workflow-Schritt bereit sind.

        Returns:
            Liste der Deliveries, die voranschreiten können
        """

    @abstractmethod
    def find_stalled_deliveries(self, hours_threshold: int = 24) -> List[Delivery]:
        """
        Sucht stagnierende Deliveries.

        Kriterien: Lange keine Aktualisierung

        Args:
            hours_threshold: Stunden ohne Update für "stagnierend"

        Returns:
            Liste der stagnierenden Deliveries
        """
