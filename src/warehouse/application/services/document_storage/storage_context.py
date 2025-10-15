"""
Storage Context Service - Zentrale Datenkontext-Verwaltung

SINGLE SOURCE OF TRUTH für alle Speicher-Operationen.
Ersetzt inkonsistente item_data vs delivery_data Nutzung in verschiedenen Services.
Holt und bereitet alle benötigten Daten für Storage-Operationen auf.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Domain Repository Imports (Clean Architecture)
from warehouse.domain.repositories import (
    ItemRepository,
    DeliveryRepository,
    SupplierRepository,
)
from warehouse.infrastructure.database.repositories.sql_item_rep_domain import (
    SQLAlchemyItemRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.sql_delivery_rep_domain import (
    SQLAlchemyDeliveryRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.sql_supplier_rep_domain import (
    SQLAlchemySupplierRepositoryDomain,
)

logger = logging.getLogger(__name__)


@dataclass
class StorageContextData:
    """
    Standardisierter Datenkontext für alle Storage-Operationen.
    Stellt sicher, dass alle Services konsistente Daten verwenden.
    """

    # Pflichtfelder
    batch_number: str
    delivery_number: str

    # Artikel-Informationen
    article_number: str = ""
    article_description: str = ""

    # Lieferanten-Informationen
    supplier_name: str = ""
    supplier_normalized: str = ""

    # Hersteller-Informationen (abgeleitet aus article_number)
    manufacturer: str = ""

    # Zusätzliche Kontextdaten
    quantity: int = 0
    unit: str = ""
    employee_name: str = ""
    delivery_date: str = ""
    order_number: str = ""

    # Metadaten
    context_source: str = "unknown"  # database, manual, fallback
    completeness_score: float = 0.0  # 0-1 basierend auf verfügbaren Daten

    def is_complete_for_storage(self) -> bool:
        """
        Prüft ob genug Daten für Storage-Operationen vorhanden sind.

        Returns:
            True wenn Mindestanforderungen erfüllt sind
        """
        required_fields = [
            self.batch_number,
            self.delivery_number,
        ]

        return all(
            field.strip() if isinstance(field, str) else field
            for field in required_fields
        )

    def get_validation_issues(self) -> list[str]:
        """
        Gibt Liste von Validierungsfehlern zurück.

        Returns:
            Liste von Fehlerbeschreibungen
        """
        issues = []

        if not self.batch_number or not self.batch_number.strip():
            issues.append("batch_number ist erforderlich")

        if not self.delivery_number or not self.delivery_number.strip():
            issues.append("delivery_number ist erforderlich")

        if not self.article_number or not self.article_number.strip():
            issues.append("article_number fehlt - kann zu inkonsistenten Pfaden führen")

        if not self.supplier_name or not self.supplier_name.strip():
            issues.append("supplier_name fehlt - verwendet Fallback-Wert")

        return issues


class StorageContext:
    """
    Zentrale Datenkontext-Verwaltung für Storage-Operationen.

    Ersetzt verstreute database_integration Aufrufe und stellt sicher,
    dass alle Services konsistente, vollständige Daten erhalten.
    """

    def __init__(self):
        self.logger = logger

        # Domain Repositories (Clean Architecture)
        try:
            self.item_repository: ItemRepository = SQLAlchemyItemRepositoryDomain()
            self.delivery_repository: DeliveryRepository = (
                SQLAlchemyDeliveryRepositoryDomain()
            )
            self.supplier_repository: SupplierRepository = (
                SQLAlchemySupplierRepositoryDomain()
            )
            self.logger.info("StorageContext initialized with domain repositories")
        except Exception as e:
            self.logger.error(f"Failed to initialize repositories: {e}")
            self.item_repository = None
            self.delivery_repository = None
            self.supplier_repository = None

        # Legacy fallback (will be removed later)
        self._database_integration = None
        # REMOVED: No longer need manufacturer_service - using internal logic

    @property
    def database_integration(self):
        """Lazy loading der database integration."""
        if self._database_integration is None:
            try:
                from warehouse.application.services.data_integration_service import (
                    data_integration_service,
                )

                self._database_integration = data_integration_service
            except ImportError as e:
                self.logger.error(f"Failed to import database_integration: {e}")
                self._database_integration = None
        return self._database_integration

    # REMOVED: No longer need manufacturer_service property - using internal logic

    def get_complete_storage_context(
        self,
        batch_number: str,
        delivery_number: str = "",
        article_number: str = "",
        supplier_name: str = "",
        **additional_kwargs,
    ) -> StorageContextData:
        """
        SINGLE SOURCE OF TRUTH für alle Speicher-Operationen.
        Holt und bereitet alle benötigten Daten auf.

        Args:
            batch_number: Chargennummer (Pflichtfeld)
            delivery_number: Lieferscheinnummer (optional, wird versucht zu finden)
            article_number: Artikelnummer (optional, überschreibt DB-Daten)
            supplier_name: Lieferantenname (optional, überschreibt DB-Daten)
            **additional_kwargs: Zusätzliche Kontextdaten

        Returns:
            Vollständiger StorageContextData mit allen verfügbaren Informationen
        """
        try:
            self.logger.info(
                f"Getting complete storage context for batch: {batch_number}"
            )

            # Versuche zuerst vollständige Daten aus der Datenbank zu holen
            db_context = self._get_database_context(batch_number, delivery_number)

            # Erstelle Basis-Kontext
            context = StorageContextData(
                batch_number=batch_number,
                delivery_number=delivery_number
                or db_context.get("delivery_number", ""),
                article_number=article_number or db_context.get("article_number", ""),
                article_description=db_context.get("article_description", ""),
                supplier_name=supplier_name or db_context.get("supplier_name", ""),
                quantity=db_context.get("quantity", 0),
                unit=db_context.get("unit", ""),
                employee_name=db_context.get("employee_name", ""),
                delivery_date=db_context.get("delivery_date", ""),
                order_number=db_context.get("order_number", ""),
                context_source=db_context.get("source", "database"),
            )

            # Zusätzliche kwargs einarbeiten
            for key, value in additional_kwargs.items():
                if hasattr(context, key) and value:
                    setattr(context, key, value)

            # Lieferanten-Daten normalisieren
            context = self._resolve_supplier_data(context)

            # Hersteller-Daten ableiten
            context = self._resolve_manufacturer_data(context)

            # Completeness Score berechnen
            context.completeness_score = self._calculate_completeness_score(context)

            self.logger.info(
                f"Storage context completed with score: {context.completeness_score:.2f}"
            )
            return context

        except Exception as e:
            self.logger.error(f"Error getting storage context: {e}")
            # Fallback context
            return self._create_fallback_context(
                batch_number, delivery_number, article_number, supplier_name
            )

    def _get_database_context(
        self, batch_number: str, delivery_number: str = ""
    ) -> Dict[str, Any]:
        """
        Holt Daten aus der Datenbank über database_integration.

        Args:
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer (optional)

        Returns:
            Dictionary mit Datenbank-Daten
        """
        try:
            if not self.database_integration:
                self.logger.debug("No database_integration available")
                return {"source": "no_database"}

            # Versuche komplette Lieferungsdaten zu holen
            if delivery_number:
                self.logger.debug(f"Fetching delivery data for: {delivery_number}, batch: {batch_number}")
                delivery_data = self.database_integration.get_complete_delivery_data(
                    delivery_number, batch_number
                )
                if delivery_data:
                    supplier_name = delivery_data.get("supplier_name", "")
                    self.logger.info(f"Database returned supplier_name: '{supplier_name}' for delivery: {delivery_number}")
                    return {
                        "delivery_number": delivery_data.get("delivery_number", ""),
                        "article_number": delivery_data.get("article_number", ""),
                        "article_description": delivery_data.get("description", ""),
                        "supplier_name": supplier_name,
                        "quantity": delivery_data.get("quantity", 0),
                        "unit": delivery_data.get("unit", ""),
                        "employee_name": delivery_data.get("employee_name", ""),
                        "delivery_date": delivery_data.get("delivery_date", ""),
                        "order_number": delivery_data.get("order_number", ""),
                        "source": "database",
                    }
                else:
                    self.logger.warning(f"No delivery data found for: {delivery_number}")

            # Fallback: DataIntegrationService hat keine search_items_by_batch Methode
            # Verwende minimalen Context
            self.logger.debug(f"No delivery_number provided or no data found, using minimal context")
            return {"source": "database_no_batch_search"}

            return {"source": "database_empty"}

        except Exception as e:
            self.logger.warning(f"Database context lookup failed: {e}")
            return {"source": "database_error"}

    def _resolve_supplier_data(self, context: StorageContextData) -> StorageContextData:
        """
        Normalisiert Lieferanten-Daten zu konsistenten Standardschreibweisen.

        Args:
            context: Storage context

        Returns:
            Context mit normalisiertem Lieferantennamen
        """
        try:
            if not context.supplier_name:
                self.logger.warning(f"No supplier_name in context, using fallback 'Unbekannt'. Context source: {context.context_source}")
                context.supplier_name = "Unbekannt"
                context.supplier_normalized = "Unbekannt"
                return context

            self.logger.debug(f"Normalizing supplier_name: '{context.supplier_name}'")

            # FIXED: Use database_integration or internal fallback (no more manufacturer_service)
            if self.database_integration and hasattr(
                self.database_integration, "normalize_supplier_name"
            ):
                context.supplier_normalized = (
                    self.database_integration.normalize_supplier_name(
                        context.supplier_name
                    )
                )
            else:
                # Fallback: Basic normalization
                context.supplier_normalized = self._basic_supplier_normalization(
                    context.supplier_name
                )

            self.logger.debug(f"Supplier normalized to: '{context.supplier_normalized}'")
            return context

        except Exception as e:
            self.logger.warning(f"Supplier normalization failed: {e}")
            context.supplier_normalized = context.supplier_name or "Unbekannt"
            return context

    def _resolve_manufacturer_data(
        self, context: StorageContextData
    ) -> StorageContextData:
        """
        Bestimmt Hersteller basierend auf Artikelnummer.

        Args:
            context: Storage context

        Returns:
            Context mit Hersteller-Information
        """
        try:
            if not context.article_number:
                context.manufacturer = "Standard_Implantate"
                return context

            # FIXED: Always use internal manufacturer determination (no more helper fallback)
            context.manufacturer = self._basic_manufacturer_determination(
                context.article_number
            )

            return context

        except Exception as e:
            self.logger.warning(f"Manufacturer determination failed: {e}")
            context.manufacturer = "Standard_Implantate"
            return context

    def _calculate_completeness_score(self, context: StorageContextData) -> float:
        """
        Berechnet Completeness Score basierend auf verfügbaren Daten.

        Args:
            context: Storage context

        Returns:
            Score zwischen 0.0 und 1.0
        """
        # Gewichtete Felder für Score-Berechnung
        weighted_fields = {
            "batch_number": 0.25,  # Pflichtfeld
            "delivery_number": 0.25,  # Pflichtfeld
            "article_number": 0.20,  # Wichtig für Pfade
            "supplier_name": 0.15,  # Wichtig für Pfade
            "manufacturer": 0.10,  # Abgeleitet
            "quantity": 0.05,  # Optional
        }

        score = 0.0

        for field_name, weight in weighted_fields.items():
            field_value = getattr(context, field_name, None)
            if field_value and (
                isinstance(field_value, str)
                and field_value.strip()
                or isinstance(field_value, (int, float))
                and field_value > 0
            ):
                score += weight

        return min(score, 1.0)  # Cap at 1.0

    def _create_fallback_context(
        self,
        batch_number: str,
        delivery_number: str = "",
        article_number: str = "",
        supplier_name: str = "",
    ) -> StorageContextData:
        """
        Erstellt Fallback-Kontext wenn Datenbank-Lookup fehlschlägt.

        Args:
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            article_number: Artikelnummer
            supplier_name: Lieferantenname

        Returns:
            Minimaler aber funktionaler StorageContextData
        """
        context = StorageContextData(
            batch_number=batch_number,
            delivery_number=delivery_number or "Unbekannt",
            article_number=article_number,
            supplier_name=supplier_name or "Primec",
            context_source="fallback",
        )

        # Basic normalization
        context.supplier_normalized = self._basic_supplier_normalization(
            context.supplier_name
        )
        context.manufacturer = self._basic_manufacturer_determination(
            context.article_number
        )
        context.completeness_score = self._calculate_completeness_score(context)

        return context

    def _basic_supplier_normalization(self, supplier_name: str) -> str:
        """
        Basic Supplier-Normalisierung ohne externe Dependencies.

        Args:
            supplier_name: Original Supplier-Name

        Returns:
            Normalisierter Supplier-Name
        """
        if not supplier_name:
            return "Unbekannt"

        supplier_lower = supplier_name.lower().strip()

        # Basic Mapping-Regeln
        if "primec" in supplier_lower:
            return "Primec GmbH"
        elif "megagen" in supplier_lower:
            return "MEGAGEN"
        elif "ctech" in supplier_lower or "c-tech" in supplier_lower:
            return "C-Tech"
        elif "straumann" in supplier_lower:
            return "Straumann"
        elif "nobel" in supplier_lower:
            return "Nobel Biocare"
        else:
            return supplier_name

    def determine_manufacturer(self, article_number: str) -> str:
        """
        ZENTRALE MANUFACTURER-BESTIMMUNG für alle Services.

        Diese Methode ist jetzt die einzige standardisierte Manufacturer-Logik im System.
        Alle neuen Services sollen diese verwenden statt alte Helper-Dependencies.

        Args:
            article_number: Artikelnummer (z.B. "MG0001", "M12345")

        Returns:
            Hersteller-Name (z.B. "MegaGen", "Medentis")
        """
        return self._basic_manufacturer_determination(article_number)

    def _basic_manufacturer_determination(self, article_number: str) -> str:
        """
        Basic Hersteller-Bestimmung ohne externe Dependencies.

        Args:
            article_number: Artikelnummer

        Returns:
            Hersteller-Name
        """
        if not article_number:
            return "Standard_Implantate"

        article_upper = article_number.upper()

        # FIXED: Prefix-Mapping - LÄNGERE PREFIXES ZUERST!
        # Dictionary wird nach Prefix-Länge sortiert (längste zuerst)
        manufacturer_map = {
            # 2-character prefixes first (to avoid "M" matching "MG")
            "AS": "Astra Dentspy",
            "BR": "Bredent",
            "CT": "C-Tech",
            "DY": "Dyna",
            "MG": "MegaGen",  # CRITICAL: MG before M!
            "NE": "Neodent",
            "SI": "Southern Implants",
            "P4": "General Implants",
            "S4": "General Implants",
            # 1-character prefixes second
            "A": "Zubehör",
            "B": "Bego",
            "C": "Camlog",
            "D": "Dentsply",
            "E": "Zubehör",
            "L": "Lasak",
            "M": "Medentis",  # CRITICAL: M after MG!
            "N": "Nobel Biocare",
            "O": "Osstem",
            "S": "Straumann",
            "Z": "Zimmer Biomet",
        }

        # Sort by prefix length (descending) to check longer prefixes first
        sorted_prefixes = sorted(
            manufacturer_map.items(), key=lambda x: len(x[0]), reverse=True
        )

        for prefix, manufacturer in sorted_prefixes:
            if article_upper.startswith(prefix):
                return manufacturer

        return "Standard_Implantate"

    def validate_storage_context(self, context: StorageContextData) -> Dict[str, Any]:
        """
        Validiert Storage Context für Vollständigkeit und Konsistenz.

        Args:
            context: Storage context zu validieren

        Returns:
            Validierungs-Ergebnis mit Details
        """
        validation_result = {
            "is_valid": context.is_complete_for_storage(),
            "completeness_score": context.completeness_score,
            "issues": context.get_validation_issues(),
            "warnings": [],
            "recommendations": [],
        }

        # Warnungen für niedrige Completeness Score
        if context.completeness_score < 0.7:
            validation_result["warnings"].append(
                f"Niedrige Datenvollständigkeit ({context.completeness_score:.1%})"
            )

        # Empfehlungen basierend auf fehlenden Daten
        if not context.article_number:
            validation_result["recommendations"].append(
                "Artikelnummer hinzufügen für konsistente Pfad-Erstellung"
            )

        if context.context_source == "fallback":
            validation_result["recommendations"].append(
                "Datenbank-Verbindung prüfen für vollständigere Kontextdaten"
            )

        return validation_result


# Global instance - SINGLE POINT OF ACCESS
storage_context = StorageContext()


# CENTRALIZED MANUFACTURER DETERMINATION - Global Access Function
def determine_manufacturer(article_number: str) -> str:
    """
    ZENTRALE MANUFACTURER-BESTIMMUNG für alle Services (Global Access Function).

    Diese Funktion stellt die standardisierte Manufacturer-Logik für das gesamte System bereit.
    Ersetzt alle alten Helper-Dependencies für Manufacturer-Bestimmung.

    Args:
        article_number: Artikelnummer (z.B. "MG0001", "M12345")

    Returns:
        Hersteller-Name (z.B. "MegaGen", "Medentis")

    Examples:
        >>> determine_manufacturer("MG0001")  # "MegaGen"
        >>> determine_manufacturer("M12345")  # "Medentis"
        >>> determine_manufacturer("A1234")   # "Zubehör"
    """
    return storage_context.determine_manufacturer(article_number)
