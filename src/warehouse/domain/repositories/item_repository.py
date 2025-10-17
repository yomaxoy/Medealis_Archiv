# src/warehouse/domain/repositories/item_repository.py

"""
Item Repository Interface für das Warehouse Management System.

ERWEITERT um Domain Object Methoden für Clean Architecture Migration.
Bestehende Methoden bleiben unverändert erhalten.

Definiert spezifische Datenzugriffs-Methoden für Item-Entities.
Fokus auf Rückverfolgbarkeit und Medizinprodukte-spezifische Abfragen.
"""

from abc import abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime, date

from warehouse.domain.repositories.base_repository import BaseRepository
from warehouse.domain.entities.item import Item
from warehouse.domain.enums.item_status import ItemStatus
from warehouse.domain.enums.certificate_type import CertificateType
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber

# Composite Key Type für Items
ItemId = Tuple[str, str, str]  # (article_number, batch_number, delivery_number)


class ItemRepository(BaseRepository[Item]):
    """
    Repository Interface für Item-Entities.

    Erweitert BaseRepository um Item-spezifische Abfrage-Methoden
    für Rückverfolgbarkeit, Status-Management und Compliance.

    ERWEITERT um Domain Object Methoden für Clean Architecture.
    """

    # === DOMAIN OBJECT METHODS (NEU) ===

    @abstractmethod
    def save_domain(self, item: Item) -> ItemId:
        """
        Speichert Item Domain Entity.

        Args:
            item: Item Domain Entity

        Returns:
            Composite Key (article_number, batch_number, delivery_number)
        """

    @abstractmethod
    def find_domain_by_composite_key(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
    ) -> Optional[Item]:
        """
        Sucht Item Domain Entity per Composite Key.

        Args:
            article_number: ArticleNumber Value Object
            batch_number: BatchNumber Value Object
            delivery_number: Lieferscheinnummer

        Returns:
            Item Domain Entity oder None
        """

    @abstractmethod
    def find_domain_by_delivery(self, delivery_number: str) -> List[Item]:
        """
        Sucht alle Item Domain Entities einer Lieferung.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            Liste von Item Domain Entities
        """

    @abstractmethod
    def find_domain_all(self) -> List[Item]:
        """
        Gibt alle Items als Domain Entities zurück.

        Returns:
            Liste aller Item Domain Entities
        """

    @abstractmethod
    def delete_domain(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
    ) -> bool:
        """
        Löscht Item Domain Entity.

        Args:
            article_number: ArticleNumber Value Object
            batch_number: BatchNumber Value Object
            delivery_number: Lieferscheinnummer

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """

    @abstractmethod
    def exists_domain(
        self,
        article_number: ArticleNumber,
        batch_number: BatchNumber,
        delivery_number: str,
    ) -> bool:
        """
        Prüft ob Item Domain Entity existiert.

        Args:
            article_number: ArticleNumber Value Object
            batch_number: BatchNumber Value Object
            delivery_number: Lieferscheinnummer

        Returns:
            True wenn existiert
        """

    # === DOMAIN OBJECT CONVENIENCE METHODS ===

    @abstractmethod
    def find_domain_by_article_number(
        self, article_number: ArticleNumber
    ) -> List[Item]:
        """
        Sucht alle Items eines Artikels als Domain Entities.

        Args:
            article_number: ArticleNumber Value Object

        Returns:
            Liste von Item Domain Entities
        """

    @abstractmethod
    def find_domain_by_status(self, status: ItemStatus) -> List[Item]:
        """
        Sucht Items nach Status als Domain Entities.

        Args:
            status: ItemStatus Enum

        Returns:
            Liste von Item Domain Entities
        """

    @abstractmethod
    def find_domain_by_order_number(self, order_number: str) -> List[Item]:
        """
        Sucht Items einer Bestellung als Domain Entities.

        Args:
            order_number: Bestellnummer

        Returns:
            Liste von Item Domain Entities
        """

    # === BESTEHENDE CORE IDENTIFIER QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_article_and_batch(
        self, article_number: ArticleNumber, batch_number: BatchNumber
    ) -> Optional[Item]:
        """
        Sucht Item anhand Artikelnummer und Chargennummer.

        Wichtig für Rückverfolgbarkeit und Duplikatsprüfung.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer

        Returns:
            Gefundenes Item oder None
        """

    @abstractmethod
    def find_by_unique_identifier(self, unique_id: str) -> Optional[Item]:
        """
        Sucht Item anhand des eindeutigen Identifiers.

        Format: "ArticleNumber#BatchNumber#DeliveryNumber"

        Args:
            unique_id: Eindeutiger Identifier

        Returns:
            Gefundenes Item oder None
        """

    @abstractmethod
    def find_by_barcode(self, barcode: str) -> Optional[Item]:
        """
        Sucht Item anhand des generierten Barcodes.

        Args:
            barcode: Barcode-String

        Returns:
            Gefundenes Item oder None
        """

    # === BESTEHENDE DELIVERY-RELATED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_delivery_number(self, delivery_number: str) -> List[Item]:
        """
        Sucht alle Items einer bestimmten Lieferung.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            Liste aller Items der Lieferung
        """

    @abstractmethod
    def find_by_supplier(self, supplier_id: str) -> List[Item]:
        """
        Sucht alle Items eines bestimmten Lieferanten.

        Args:
            supplier_id: Lieferanten-ID

        Returns:
            Liste aller Items des Lieferanten
        """

    # === BESTEHENDE STATUS-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_current_status(self, status: ItemStatus) -> List[Item]:
        """
        Sucht Items basierend auf ihrem aktuellen Status.

        Args:
            status: Gewünschter Status

        Returns:
            Liste aller Items mit diesem Status
        """

    @abstractmethod
    def find_items_needing_attention(self) -> List[Item]:
        """
        Sucht Items, die Aufmerksamkeit benötigen.

        Kriterien:
        - Nicht final (ABGESCHLOSSEN/AUSSCHUSS)
        - Haben fehlende Schritte

        Returns:
            Liste der Items, die bearbeitet werden müssen
        """

    @abstractmethod
    def find_by_completed_step(self, step: ItemStatus) -> List[Item]:
        """
        Sucht Items, die einen bestimmten Schritt abgeschlossen haben.

        Args:
            step: Bearbeitungsschritt

        Returns:
            Liste der Items mit abgeschlossenem Schritt
        """

    @abstractmethod
    def find_by_missing_step(self, step: ItemStatus) -> List[Item]:
        """
        Sucht Items, denen ein bestimmter Schritt fehlt.

        Args:
            step: Fehlender Bearbeitungsschritt

        Returns:
            Liste der Items ohne diesen Schritt
        """

    @abstractmethod
    def find_ready_for_completion(self) -> List[Item]:
        """
        Sucht Items, die bereit für Abschluss sind.

        Returns:
            Liste der Items mit allen abgeschlossenen Schritten
        """

    # === BESTEHENDE CERTIFICATE QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_certificate_status(
        self, certificate_type: CertificateType, present: bool
    ) -> List[Item]:
        """
        Sucht Items basierend auf Zertifikatsstatus.

        Args:
            certificate_type: Typ des Zertifikats
            present: True = Zertifikat vorhanden, False = fehlend

        Returns:
            Liste der Items mit entsprechendem Zertifikatsstatus
        """

    @abstractmethod
    def find_with_missing_certificates(self) -> List[Item]:
        """
        Sucht Items mit fehlenden Zertifikaten.

        Returns:
            Liste der Items ohne erforderliche Zertifikate
        """

    @abstractmethod
    def find_with_complete_certificates(self) -> List[Item]:
        """
        Sucht Items mit vollständigen Zertifikaten.

        Returns:
            Liste der Items mit allen erforderlichen Zertifikaten
        """

    # === BESTEHENDE INSPECTION & QUALITY QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_with_inspection_results(self) -> List[Item]:
        """
        Sucht Items mit vorhandenen Prüfungsergebnissen.

        Returns:
            Liste der Items mit InspectionResult
        """

    @abstractmethod
    def find_with_waste(self) -> List[Item]:
        """
        Sucht Items mit Ausschuss.

        Returns:
            Liste der Items mit Ausschussmengen > 0
        """

    @abstractmethod
    def find_by_quality_status(self, passed: bool) -> List[Item]:
        """
        Sucht Items basierend auf Qualitätsprüfung.

        Args:
            passed: True = bestanden, False = nicht bestanden

        Returns:
            Liste der Items mit entsprechendem Qualitätsstatus
        """

    # === BESTEHENDE DATE-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_created_between(
        self, start_date: datetime, end_date: datetime
    ) -> List[Item]:
        """
        Sucht Items, die in einem Zeitraum erstellt wurden.

        Args:
            start_date: Startdatum (inklusive)
            end_date: Enddatum (inklusive)

        Returns:
            Liste der Items im Zeitraum
        """

    @abstractmethod
    def find_updated_since(self, since_date: datetime) -> List[Item]:
        """
        Sucht Items, die seit einem Datum aktualisiert wurden.

        Args:
            since_date: Stichtag

        Returns:
            Liste der seitdem aktualisierten Items
        """

    @abstractmethod
    def find_by_step_completion_date(
        self, step: ItemStatus, completion_date: date
    ) -> List[Item]:
        """
        Sucht Items, bei denen ein Schritt an einem bestimmten Tag abgeschlossen wurde.

        Args:
            step: Bearbeitungsschritt
            completion_date: Datum des Abschlusses

        Returns:
            Liste der Items mit Schritt-Abschluss am Datum
        """

    # === BESTEHENDE EMPLOYEE-BASED QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def find_by_employee(self, employee_name: str) -> List[Item]:
        """
        Sucht Items, die von einem bestimmten Mitarbeiter bearbeitet wurden.

        Args:
            employee_name: Name des Mitarbeiters

        Returns:
            Liste aller Items des Mitarbeiters
        """

    @abstractmethod
    def find_by_step_employee(self, step: ItemStatus, employee_name: str) -> List[Item]:
        """
        Sucht Items, bei denen ein bestimmter Schritt von einem Mitarbeiter durchgeführt wurde.

        Args:
            step: Bearbeitungsschritt
            employee_name: Name des Mitarbeiters

        Returns:
            Liste der Items mit Mitarbeiter-Schritt
        """

    # === BESTEHENDE ADVANCED ANALYTICS QUERIES (UNVERÄNDERT) ===

    @abstractmethod
    def get_status_distribution(self) -> dict:
        """
        Gibt Verteilung der Items nach aktuellem Status zurück.

        Returns:
            Dictionary mit Status -> Anzahl Items
        """

    @abstractmethod
    def get_completion_statistics(self) -> dict:
        """
        Gibt Statistiken zum Bearbeitungsfortschritt zurück.

        Returns:
            Dictionary mit verschiedenen Completion-Metriken
        """

    @abstractmethod
    def get_waste_statistics(self) -> dict:
        """
        Gibt Ausschuss-Statistiken zurück.

        Returns:
            Dictionary mit Ausschuss-Metriken nach Artikel/Lieferant
        """

    @abstractmethod
    def get_employee_workload(self) -> dict:
        """
        Gibt Arbeitslasten-Statistiken pro Mitarbeiter zurück.

        Returns:
            Dictionary mit Mitarbeiter -> bearbeitete Items
        """

    # === BESTEHENDE SEARCH & FILTERING (UNVERÄNDERT) ===

    @abstractmethod
    def search_items(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Item]:
        """
        Volltextsuche in Items.

        Args:
            search_term: Suchbegriff
            search_fields: Felder für Suche (None = alle durchsuchbaren Felder)

        Returns:
            Liste der gefundenen Items
        """

    @abstractmethod
    def find_by_advanced_criteria(self, criteria: dict) -> List[Item]:
        """
        Erweiterte Suche mit komplexen Kriterien.

        Unterstützt verschachtelte Abfragen für Status, Zertifikate,
        Daten, Mitarbeiter, etc.

        Args:
            criteria: Erweiterte Suchkriterien

        Returns:
            Liste der gefundenen Items
        """
