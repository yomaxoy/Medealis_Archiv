# src/warehouse/application/services/delivery_service.py

"""
Delivery Service - Application Layer für das Warehouse Management System.

Orchestriert Delivery-bezogene Use Cases und verbindet Domain Logic
mit Infrastructure. Angepasst an deine exakte Projektstruktur.
"""

# Standard library imports
import logging
from datetime import date
from typing import Dict, Any, List, Optional

# Domain imports
from warehouse.domain.entities.delivery import Delivery
from warehouse.domain.entities.supplier import Supplier
from warehouse.domain.exceptions.delivery_exceptions import (
    DeliveryAlreadyExistsException,
    DeliveryNotFoundException,
)
from warehouse.domain.exceptions.item_exceptions import ItemAlreadyExistsException
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber

# Infrastructure imports
from warehouse.infrastructure.database.repositories.sql_delivery_rep_domain import (
    SQLAlchemyDeliveryRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.sql_item_rep_domain import (
    SQLAlchemyItemRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.sql_supplier_rep_domain import (
    SQLAlchemySupplierRepositoryDomain,
)

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Application Service für Delivery-Management.

    Verwaltet den kompletten Lebenszyklus von Lieferungen:
    - Erstellung neuer Lieferungen
    - Hinzufügen von Artikeln
    - Status-Übergänge
    - Workflow-Orchestrierung
    """

    def __init__(self):
        try:
            # Database should already be initialized by Infrastructure Layer
            self.delivery_repo = SQLAlchemyDeliveryRepositoryDomain()
            self.item_repo = SQLAlchemyItemRepositoryDomain()
            self.supplier_repo = SQLAlchemySupplierRepositoryDomain()
            logger.info("DeliveryService erfolgreich initialisiert")
        except (ImportError, AttributeError, ConnectionError) as e:
            logger.error("Fehler bei DeliveryService Initialisierung: %s", e)
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler bei DeliveryService Initialisierung: %s", e
            )
            raise

    # === SUPPLIER MAPPING & MANAGEMENT ===

    def map_supplier_name_to_id(self, supplier_name: str) -> str:
        """
        Mappt Supplier-Namen zu Supplier-IDs für Claude API Integration.

        Args:
            supplier_name: Supplier-Name aus Claude API

        Returns:
            Supplier-ID für Datenbank
        """
        if not supplier_name or not supplier_name.strip():
            return ""

        supplier_name_clean = supplier_name.strip()

        # 1. Exakte Suche in Datenbank
        try:
            existing_supplier = self.supplier_repo.find_domain_by_name(
                supplier_name_clean
            )
            if existing_supplier:
                logger.info(
                    f"Found existing supplier: {supplier_name_clean} -> {existing_supplier.supplier_id}"
                )
                return existing_supplier.supplier_id
        except Exception as e:
            logger.debug(
                f"Database search failed for supplier {supplier_name_clean}: {e}"
            )

        # 2. Mapping-Tabelle für bekannte Supplier (nur echte physische Lieferanten)
        # WICHTIG: Implantatmarken (BEGO, CAMLOG, STRAUMANN etc.) sind KEINE Lieferanten!
        # Sie stehen in item_info.kompatibilitaet und werden aus Artikelnummer-Präfix abgeleitet.
        supplier_name_mapping = {
            "primec GmbH": "10006",
            "PRIMEC": "10006",
            "primec": "10006",
            "Primec": "10006",
            "Terrats Medical": "10031",
            "TERRATS MEDICAL SL": "10031",
            "TERRATS MEDICAL": "10031",
            "Terrats": "10031",
            "TERRATS": "10031",
            "terrats": "10031",
            "terrats medical": "10031",
            "Terrats Medical GmbH": "10031",
            "Fleima-Plastic GmbH": "10005",
            "Fleima": "10005",
            "FLEIMA": "10005",
            "fleima": "10005",
            "KSP": "10004",
            # MEGAGEN / C-TECH: Lieferantennummern noch nicht bekannt
            # "MEGAGEN": "10XXX",
            # "C-Tech": "10XXX",
            # Weitere Mappings können hier hinzugefügt werden
        }

        # Exakte Übereinstimmung
        if supplier_name_clean in supplier_name_mapping:
            mapped_id = supplier_name_mapping[supplier_name_clean]
            logger.info(f"Mapped supplier name: {supplier_name_clean} -> {mapped_id}")
            return mapped_id

        # 3. Fuzzy Matching für ähnliche Namen
        supplier_name_lower = supplier_name_clean.lower()
        for name_variant, supplier_id in supplier_name_mapping.items():
            if (
                name_variant.lower() in supplier_name_lower
                or supplier_name_lower in name_variant.lower()
            ):
                logger.info(
                    f"Fuzzy matched supplier: {supplier_name_clean} -> {supplier_id} (via {name_variant})"
                )
                return supplier_id

        # 4. Fallback: Kein Auto-Generieren - Lieferant muss manuell angelegt werden
        logger.warning(
            f"Unbekannter Lieferant '{supplier_name_clean}'. "
            "Bitte im Supplier Management manuell anlegen (5-stellige Lieferantennummer)."
        )
        return ""

    def _generate_auto_supplier_id(self, supplier_name: str) -> str:
        """
        Generiert automatische Supplier-ID aus dem Namen.
        """
        # Bereinige den Namen
        import re

        name_clean = re.sub(r"[^A-Za-z0-9\s]", "", supplier_name)

        # Nimm die ersten Buchstaben von Wörtern
        words = name_clean.split()
        if len(words) == 1:
            # Ein Wort: Nimm die ersten 6 Zeichen
            auto_id = words[0][:6].upper()
        else:
            # Mehrere Wörter: Nimm die ersten 2-3 Buchstaben pro Wort
            auto_id = "".join(word[:2].upper() for word in words[:3])

        # Stelle sicher, dass ID nicht leer ist
        if not auto_id:
            auto_id = "UNKNOWN"

        return auto_id

    # === DELIVERY CREATION & MANAGEMENT ===

    def create_delivery(
        self,
        delivery_number: str,
        supplier_id: str,
        delivery_date: date,
        employee_name: str,
        document_path: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Erstellt eine neue Lieferung.

        Args:
            delivery_number: Eindeutige Lieferscheinnummer
            supplier_id: Lieferanten-ID
            delivery_date: Lieferdatum
            employee_name: Bearbeitender Mitarbeiter
            document_path: Pfad zum gescannten Lieferschein (optional)

        Returns:
            Lieferscheinnummer der erstellten Lieferung
        """
        try:
            logger.info("Erstelle neue Lieferung: %s", delivery_number)

            # Prüfe, ob Lieferung bereits existiert
            if self.delivery_repo.exists_domain(delivery_number):
                raise DeliveryAlreadyExistsException(delivery_number)

            # Prüfe, ob Supplier existiert
            supplier = self.supplier_repo.find_domain_by_supplier_id(supplier_id)
            if not supplier:
                logger.warning(
                    "Supplier %s nicht gefunden - erstelle automatisch", supplier_id
                )
                # Erstelle Basic Supplier falls nicht vorhanden
                new_supplier = Supplier(
                    supplier_id=supplier_id, name=f"Supplier {supplier_id}"
                )
                self.supplier_repo.save_domain(new_supplier)

            # Erstelle Delivery Domain Entity
            delivery = Delivery(
                delivery_number=delivery_number,
                supplier_id=supplier_id,
                delivery_date=delivery_date,
                employee_name=employee_name,
                document_path=document_path,
                notes=notes,
            )

            # Persistiere in Database
            saved_delivery_number = self.delivery_repo.save_domain(delivery)

            logger.info("Lieferung %s erfolgreich erstellt", delivery_number)
            return saved_delivery_number

        except (DeliveryAlreadyExistsException, ValueError) as e:
            logger.error(
                "Geschäftslogik-Fehler beim Erstellen der Lieferung %s: %s",
                delivery_number,
                e,
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Erstellen der Lieferung %s: %s",
                delivery_number,
                e,
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Erstellen der Lieferung %s: %s",
                delivery_number,
                e,
            )
            raise

    def create_delivery_with_items(
        self,
        delivery_number: str,
        supplier_id: str,
        delivery_date: date,
        employee_name: str,
        items: List[Dict[str, Any]],
        document_path: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Erstellt eine neue Lieferung mit Items in einer Transaktion.

        Args:
            delivery_number: Eindeutige Lieferscheinnummer
            supplier_id: Lieferanten-ID
            delivery_date: Lieferdatum
            employee_name: Name des verarbeitenden Mitarbeiters
            items: Liste von Items mit format: [{"article_number": "A0001", "batch_number": "P-123...", "quantity": 5}, ...]
            document_path: Optional - Pfad zum Lieferschein-Dokument
            notes: Optionale Notizen

        Returns:
            Lieferscheinnummer der erstellten Lieferung

        Raises:
            DeliveryAlreadyExistsException: Wenn Lieferung bereits existiert
            ValueError: Bei ungültigen Eingabedaten
        """
        try:
            logger.info(
                "Erstelle Lieferung %s mit %d Items", delivery_number, len(items)
            )

            # 1. Erstelle zunächst die Lieferung
            created_delivery_number = self.create_delivery(
                delivery_number=delivery_number,
                supplier_id=supplier_id,
                delivery_date=delivery_date,
                employee_name=employee_name,
                document_path=document_path,
                notes=notes,
            )

            # 2. Füge alle Items zur Lieferung hinzu
            added_items = 0
            for item in items:
                try:
                    article_number = item.get("article_number", "").strip()
                    batch_number = item.get("batch_number", "").strip()
                    quantity = int(item.get("quantity", 0))

                    if not article_number or not batch_number or quantity <= 0:
                        logger.warning("Überspringe ungültiges Item: %s", item)
                        continue

                    self.add_item_to_delivery(
                        delivery_number=delivery_number,
                        article_number=article_number,
                        batch_number=batch_number,
                        quantity=quantity,
                        employee_name=employee_name,
                    )
                    added_items += 1
                    logger.debug(
                        "Item %s/%s erfolgreich hinzugefügt",
                        article_number,
                        batch_number,
                    )

                except Exception as item_error:
                    logger.warning(
                        "Fehler beim Hinzufügen von Item %s: %s", item, item_error
                    )
                    continue

            logger.info(
                "Lieferung %s mit %d/%d Items erfolgreich erstellt",
                delivery_number,
                added_items,
                len(items),
            )
            return created_delivery_number

        except Exception as e:
            logger.error(
                "Fehler beim Erstellen der Lieferung mit Items %s: %s",
                delivery_number,
                e,
            )
            raise

    def add_item_to_delivery(
        self,
        delivery_number: str,
        article_number: str,
        batch_number: str,
        quantity: int,
        employee_name: Optional[str] = None,
    ) -> bool:
        """
        Fügt einen Artikel zu einer Lieferung hinzu.

        Args:
            delivery_number: Lieferscheinnummer
            article_number: Artikelnummer (z.B. "A0001")
            batch_number: Chargennummer (z.B. "P-123456789012-1234")
            quantity: Liefermenge
            employee_name: Bearbeitender Mitarbeiter (optional)

        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            logger.info(
                "Füge Artikel %s/%s zu Lieferung %s hinzu",
                article_number,
                batch_number,
                delivery_number,
            )

            # Lade Delivery
            delivery = self.delivery_repo.find_domain_by_delivery_number(
                delivery_number
            )
            if not delivery:
                raise DeliveryNotFoundException(delivery_number)

            # Erstelle Value Objects (mit Validierung)
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            # Füge Item über Domain Logic hinzu
            item = delivery.add_item(
                article_number=article_vo,
                batch_number=batch_vo,
                quantity=quantity,
                employee_name=employee_name or delivery.employee_name,
            )

            # Persistiere Delivery (mit Items)
            self.delivery_repo.save_domain(delivery)

            # Persistiere Item separat (wegen Composite Key)
            self.item_repo.save_domain(item)

            logger.info(
                "Artikel %s/%s erfolgreich hinzugefügt", article_number, batch_number
            )
            return True

        except (DeliveryNotFoundException, ItemAlreadyExistsException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler beim Hinzufügen des Artikels: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Hinzufügen des Artikels: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Hinzufügen des Artikels: %s", e)
            raise

    def get_delivery(self, delivery_number: str) -> Optional[Dict[str, Any]]:
        """
        Holt eine Lieferung mit allen Details.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            Dictionary mit Delivery-Daten oder None
        """
        try:
            delivery = self.delivery_repo.find_domain_by_delivery_number(
                delivery_number
            )
            if not delivery:
                return None

            return {
                "delivery_number": delivery.delivery_number,
                "supplier_id": delivery.supplier_id,
                "delivery_date": delivery.delivery_date.isoformat(),
                "employee_name": delivery.employee_name,
                "status": delivery.status.value,
                "document_path": delivery.document_path,
                "total_items": delivery.get_total_item_count(),
                "total_quantity": delivery.get_total_quantity(),
                "completion_percentage": delivery.get_completion_percentage(),
                "created_at": delivery.created_at.isoformat(),
                "updated_at": delivery.updated_at.isoformat(),
                "notes": delivery.notes,
                "summary": delivery.get_summary(),
            }

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Lieferung %s: %s",
                delivery_number,
                e,
            )
            return None
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der Lieferung %s: %s",
                delivery_number,
                e,
            )
            return None

    def get_delivery_items(self, delivery_number: str) -> List[Dict[str, Any]]:
        """
        Holt alle Items einer Lieferung.

        Args:
            delivery_number: Lieferscheinnummer

        Returns:
            Liste von Item-Dictionaries
        """
        try:
            items = self.item_repo.find_domain_by_delivery(delivery_number)
            return [
                {
                    "article_number": str(item.article_number),
                    "batch_number": str(item.batch_number),
                    "delivery_number": item.delivery_number,
                    "quantity": item.delivered_quantity,  # Backward compatibility
                    "delivered_quantity": item.delivered_quantity,
                    "delivery_slip_quantity": getattr(item, 'delivery_slip_quantity', None),
                    "ordered_quantity": getattr(item, 'ordered_quantity', None),
                    "status": item.get_current_status().value,
                    "completion_percentage": item.get_completion_percentage(),
                    "created_by": item.created_by,
                    "unique_identifier": item.get_unique_identifier(),
                }
                for item in items
            ]

        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Items für Lieferung %s: %s",
                delivery_number,
                e,
            )
            return []
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der Items für Lieferung %s: %s",
                delivery_number,
                e,
            )
            return []

    def get_recent_deliveries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Holt die neuesten Lieferungen."""
        try:
            deliveries = self.delivery_repo.find_domain_recent(limit)
            return [delivery.get_summary() for delivery in deliveries]
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der aktuellen Lieferungen: %s", e
            )
            return []
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der aktuellen Lieferungen: %s", e
            )
            return []

    def delivery_exists(self, delivery_number: str) -> bool:
        """Prüft, ob eine Lieferung existiert."""
        return self.delivery_repo.exists_domain(delivery_number)

    def get_all_deliveries(self) -> List[Dict[str, Any]]:
        """
        Holt alle Deliveries für die GUI-Liste.

        Returns:
            Liste von Delivery-Dictionaries
        """
        try:
            deliveries = self.delivery_repo.find_domain_all()
            delivery_list = []

            for delivery in deliveries:
                # Look up supplier name from supplier_id
                supplier_name = "Unbekannt"
                if delivery.supplier_id:
                    try:
                        supplier = self.supplier_repo.find_by_id(delivery.supplier_id)
                        if supplier and hasattr(supplier, 'name'):
                            supplier_name = supplier.name
                            logger.debug(f"Supplier gefunden für {delivery.delivery_number}: {supplier_name} (ID: {delivery.supplier_id})")
                        else:
                            logger.warning(f"Supplier nicht gefunden für Delivery {delivery.delivery_number}, supplier_id: {delivery.supplier_id}")
                    except Exception as e:
                        logger.warning(f"Fehler beim Laden des Suppliers {delivery.supplier_id}: {e}")

                delivery_dict = {
                    "delivery_number": delivery.delivery_number,
                    "supplier_id": delivery.supplier_id,
                    "supplier_name": supplier_name,  # Add supplier_name field
                    "delivery_date": (
                        delivery.delivery_date.isoformat()
                        if delivery.delivery_date
                        else None
                    ),
                    "status": (
                        delivery.status.value
                        if hasattr(delivery.status, "value")
                        else str(delivery.status)
                    ),
                    "employee_name": delivery.employee_name,
                    "items_count": len(delivery.items) if delivery.items else 0,
                    "created_at": (
                        delivery.created_at.isoformat() if delivery.created_at else None
                    ),
                }
                delivery_list.append(delivery_dict)

            return delivery_list

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden aller Deliveries: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden aller Deliveries: %s", e)
            return []

    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Holt Delivery-Statistiken für Dashboard."""
        try:
            stats = self.delivery_repo.get_repository_statistics()
            return stats
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden der Delivery-Statistiken: %s", e
            )
            return {}
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden der Delivery-Statistiken: %s", e
            )
            return {}

    def create_delivery_from_extraction(
        self, delivery_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Erstellt eine Lieferung aus KI-Extraktion (migrated from database_helpers.py).

        Args:
            delivery_data: Dictionary mit extrahierten Lieferungsdaten

        Returns:
            Dict mit success, message, delivery_number, etc.
        """
        try:
            logger.info("Creating delivery from AI extraction data")

            # Initialize required services
            from .supplier_service import SupplierService
            from .item_service import ItemService

            supplier_service = SupplierService()
            item_service = ItemService()

            # 1. Handle Supplier - create or find existing with intelligent mapping
            supplier_name = delivery_data.get("supplier_name", "").strip()
            supplier_id_input = delivery_data.get("supplier_id", "").strip()

            logger.debug(
                "Supplier mapping: name='%s', id='%s'", supplier_name, supplier_id_input
            )

            # Intelligent Supplier mapping when supplier_name exists but supplier_id is empty
            if supplier_name and not supplier_id_input:
                try:
                    mapped_supplier_id = self.map_supplier_name_to_id(supplier_name)
                    if mapped_supplier_id:
                        supplier_id_input = mapped_supplier_id
                        logger.info(
                            "Mapped supplier: '%s' -> '%s'",
                            supplier_name,
                            mapped_supplier_id,
                        )
                    else:
                        logger.warning(
                            "No mapping found for: '%s', will create new", supplier_name
                        )
                except Exception as e:
                    logger.warning(
                        "Supplier mapping failed: %s, will fallback to manual search", e
                    )

            # Use supplier_id if provided (including mapped), otherwise use supplier_name
            supplier_lookup_value = (
                supplier_id_input if supplier_id_input else supplier_name
            )

            if not supplier_lookup_value:
                return {
                    "success": False,
                    "error": "Lieferantenname oder Supplier ID ist erforderlich",
                }

            # Find existing supplier by name or ID
            existing_suppliers = supplier_service.get_all_suppliers()
            found_supplier = None

            logger.debug("Looking for supplier with value: '%s'", supplier_lookup_value)

            # First try by ID (if supplier_lookup_value looks like an ID)
            for supplier in existing_suppliers:
                supplier_id = supplier.get("id") or supplier.get("supplier_id")
                if str(supplier_id) == supplier_lookup_value:
                    found_supplier = supplier
                    logger.info(
                        "Found supplier by ID: %s (ID: %s)",
                        supplier.get("name"),
                        supplier_id,
                    )
                    break

            # If not found by ID, try by name (contains-match, case-insensitive)
            if not found_supplier:
                lookup_lower = supplier_lookup_value.lower()
                for supplier in existing_suppliers:
                    db_name = supplier.get("name", "").lower()
                    if db_name == lookup_lower or lookup_lower in db_name or db_name in lookup_lower:
                        found_supplier = supplier
                        logger.info(
                            "Found supplier by name: %s (ID: %s)",
                            supplier.get("name"),
                            supplier.get("id"),
                        )
                        break

            # Last resort: try explicit name→ID mapping before creating a new supplier
            if not found_supplier:
                fallback_id = self.map_supplier_name_to_id(supplier_lookup_value) or (
                    self.map_supplier_name_to_id(supplier_name) if supplier_name else None
                )
                if fallback_id:
                    for supplier in existing_suppliers:
                        sid = supplier.get("id") or supplier.get("supplier_id")
                        if str(sid) == fallback_id:
                            found_supplier = supplier
                            logger.info(
                                "Found supplier via name mapping: %s -> %s",
                                supplier_lookup_value,
                                fallback_id,
                            )
                            break

            if found_supplier:
                final_supplier_id = found_supplier.get("id") or found_supplier.get(
                    "supplier_id"
                )
                logger.info("Using existing supplier ID: %s", final_supplier_id)
            else:
                # Create new supplier - use name if available, otherwise use lookup value
                new_supplier_name = (
                    supplier_name if supplier_name else supplier_lookup_value
                )
                logger.info("Creating new supplier: %s", new_supplier_name)
                # Generate supplier ID from name
                import re

                supplier_id = re.sub(r"[^A-Za-z0-9]", "", new_supplier_name)[
                    :10
                ].upper()
                if not supplier_id:
                    supplier_id = "AUTO_SUP"

                supplier_result = supplier_service.create_supplier(
                    supplier_id=supplier_id,
                    name=new_supplier_name,
                    notes="Automatisch erstellt via Claude Import",
                )
                # SupplierService.create_supplier returns string (supplier_id), not dict
                supplier_result = {"success": True, "supplier_id": supplier_result}
                if supplier_result.get("success"):
                    final_supplier_id = supplier_result.get("supplier_id")
                    logger.info("Created new supplier with ID: %s", final_supplier_id)
                else:
                    error_msg = f'Fehler beim Erstellen des Lieferanten: {supplier_result.get("error")}'
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}

            # 2. Create Delivery
            delivery_number = delivery_data.get("delivery_number", "").strip()
            if not delivery_number:
                from datetime import datetime

                delivery_number = f"CLAUDE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Parse delivery_date string to date object
            from datetime import datetime, date

            delivery_date_str = delivery_data.get("delivery_date", str(date.today()))
            try:
                if isinstance(delivery_date_str, str):
                    # Try different date formats
                    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"]:
                        try:
                            delivery_date_obj = datetime.strptime(
                                delivery_date_str, fmt
                            ).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format worked, use today
                        delivery_date_obj = date.today()
                else:
                    delivery_date_obj = (
                        delivery_date_str  # Assume it's already a date object
                    )
            except:
                delivery_date_obj = date.today()

            logger.info(
                "Delivery date: %s (from: %s)", delivery_date_obj, delivery_date_str
            )

            # Create delivery using service method
            delivery_result = self.create_delivery(
                delivery_number=delivery_number,
                supplier_id=str(final_supplier_id),
                delivery_date=delivery_date_obj,
                employee_name=delivery_data.get("employee_name", "Claude-Import"),
                document_path=None,
                notes=delivery_data.get("notes", "Imported via Claude AI"),
            )

            if not delivery_result or not isinstance(delivery_result, str):
                error_msg = f"Delivery creation failed: {delivery_result}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            logger.info(
                "Delivery created successfully: %s (ID: %s)",
                delivery_number,
                delivery_result,
            )

            # 3. Create Items
            items_created = 0
            items_failed = 0
            error_messages = []

            items = delivery_data.get("items", [])
            logger.info("Processing %d items...", len(items))

            for i, item in enumerate(items):
                try:
                    # Extract item data
                    article_number = item.get("article_number", "").strip()
                    batch_number = item.get("batch_number", "").strip()
                    quantity = item.get("quantity", 1)

                    if not article_number:
                        article_number = f"ITEM-{i+1:03d}"
                        logger.warning("No article number, using: %s", article_number)

                    if not batch_number:
                        batch_number = f"BATCH-{delivery_number}-{i+1:03d}"
                        logger.warning("No batch number, using: %s", batch_number)

                    # Convert quantity to int
                    try:
                        quantity = int(quantity)
                    except (ValueError, TypeError):
                        quantity = 1
                        logger.warning("Invalid quantity, using: %s", quantity)

                    # Parse expiry date if available
                    expiry_date = None
                    if item.get("expiry_date"):
                        try:
                            expiry_date_str = item.get("expiry_date")
                            for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"]:
                                try:
                                    expiry_date = datetime.strptime(
                                        expiry_date_str, fmt
                                    ).date()
                                    break
                                except ValueError:
                                    continue
                        except:
                            expiry_date = None

                    item_create_data = {
                        "article_number": article_number,
                        "batch_number": batch_number,
                        "quantity": quantity,
                        "delivery_number": delivery_number,
                        "order_number": item.get("order_number", ""),
                        "expiry_date": expiry_date,
                        "storage_location": item.get("storage_location", ""),
                        "description": item.get("description", ""),  # Use empty string, not delivery notes
                        "status": "received",
                    }

                    logger.info(
                        "Creating item %d/%d: %s", i + 1, len(items), article_number
                    )
                    logger.info(
                        "DEBUG: item description from extraction: '%s'", item.get("description", "NOT FOUND")
                    )

                    item_result = item_service.create_item(**item_create_data)

                    # Handle both string (item_id) and dict return types
                    if item_result:
                        if isinstance(item_result, str):
                            # ItemService returns string (item_id) on success
                            items_created += 1
                            logger.info(
                                "Item %d created successfully (ID: %s)",
                                i + 1,
                                item_result,
                            )
                        elif isinstance(item_result, dict) and item_result.get(
                            "success"
                        ):
                            # Dict format with success flag
                            items_created += 1
                            logger.info("Item %d created successfully", i + 1)
                        else:
                            items_failed += 1
                            error_msg = (
                                item_result.get("error", "Unknown error")
                                if isinstance(item_result, dict)
                                else str(item_result)
                            )
                            error_messages.append(
                                f"Item {i+1} ({article_number}): {error_msg}"
                            )
                            logger.error("Item %d failed: %s", i + 1, error_msg)
                    else:
                        items_failed += 1
                        error_messages.append(
                            f"Item {i+1} ({article_number}): No result returned"
                        )
                        logger.error("Item %d failed: No result returned", i + 1)

                except Exception as e:
                    items_failed += 1
                    error_messages.append(f"Item {i+1}: {str(e)}")
                    logger.error("Item %d exception: %s", i + 1, e)

            # 4. Return results
            success_message = (
                f"Delivery '{delivery_number}' created with {items_created} items"
            )
            if items_failed > 0:
                success_message += f" ({items_failed} items failed)"

            result = {
                "success": True,
                "message": success_message,
                "delivery_number": delivery_number,
                "items_created": items_created,
                "items_failed": items_failed,
                "errors": error_messages if error_messages else None,
            }

            logger.info("Delivery from extraction completed: %s", result)
            return result

        except Exception as e:
            error_msg = f"Database save error: {str(e)}"
            logger.error("Error creating delivery from extraction: %s", e)
            return {"success": False, "error": error_msg}

    # === DELIVERY UPDATE & DELETE OPERATIONS ===

    def update_delivery(
        self,
        delivery_number: str,
        supplier_id: str = None,
        delivery_date=None,
        employee_name: str = None,
        notes: str = None,
    ) -> bool:
        """
        Aktualisiert eine Delivery.

        Args:
            delivery_number: Delivery Number (unveränderlich)
            supplier_id: Neuer Supplier ID
            delivery_date: Neues Delivery Date
            employee_name: Neuer Employee Name
            notes: Neue Notizen

        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            logger.info("Aktualisiere Delivery: %s", delivery_number)

            # Lade Delivery
            delivery = self.delivery_repo.find_domain_by_delivery_number(
                delivery_number
            )
            if not delivery:
                raise DeliveryNotFoundException(delivery_number)

            # Update fields if provided
            if supplier_id:
                delivery.supplier_id = supplier_id
            if delivery_date:
                delivery.delivery_date = delivery_date
            if employee_name:
                delivery.employee_name = employee_name
            if notes is not None:
                delivery.notes = notes

            # Persistiere
            self.delivery_repo.save_domain(delivery)

            logger.info("Delivery %s erfolgreich aktualisiert", delivery_number)
            return True

        except DeliveryNotFoundException as e:
            logger.error("Geschäftslogik-Fehler beim Aktualisieren der Delivery: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Aktualisieren der Delivery: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Aktualisieren der Delivery: %s", e)
            raise

    def delete_delivery(self, delivery_number: str) -> bool:
        """
        Löscht eine Delivery und alle zugehörigen Items in einer einzigen Transaktion.

        Args:
            delivery_number: Delivery Number

        Returns:
            True wenn erfolgreich gelöscht
        """
        try:
            logger.info("Lösche Delivery: %s", delivery_number)

            # Prüfe, ob Delivery existiert
            if not self.delivery_repo.exists_domain(delivery_number):
                raise DeliveryNotFoundException(delivery_number)

            # LÖSUNG: Eine einzige Transaktion für Items UND Delivery
            from ....infrastructure.database.connection import get_session
            from ....infrastructure.database.models.item_model import ItemModel
            from ....infrastructure.database.models.delivery_model import DeliveryModel

            with get_session() as session:
                try:
                    # Schritt 1: Finde und lösche Items
                    items = (
                        session.query(ItemModel)
                        .filter(ItemModel.delivery_number == delivery_number)
                        .all()
                    )
                    logger.info(
                        "DEBUG: Gefunden %d Items für Delivery %s",
                        len(items),
                        delivery_number,
                    )

                    deleted_items_count = 0
                    if items:
                        deleted_items_count = (
                            session.query(ItemModel)
                            .filter(ItemModel.delivery_number == delivery_number)
                            .delete(synchronize_session=False)
                        )
                        logger.info("DEBUG: %d Items gelöscht", deleted_items_count)

                    # Schritt 2: Lösche Delivery (in derselben Transaction)
                    delivery_model = (
                        session.query(DeliveryModel)
                        .filter(DeliveryModel.delivery_number == delivery_number)
                        .first()
                    )

                    if delivery_model:
                        session.delete(delivery_model)
                        logger.info("DEBUG: Delivery model zum Löschen markiert")
                    else:
                        logger.warning("DEBUG: Delivery model nicht gefunden")
                        return False

                    # Beide Operationen werden hier committed (oder beide rollen zurück)
                    session.commit()
                    logger.info(
                        "DEBUG: Single Transaction committed - Items und Delivery gelöscht"
                    )

                    logger.info(
                        "Delivery %s erfolgreich gelöscht (%d Items)",
                        delivery_number,
                        deleted_items_count,
                    )
                    return True

                except Exception as e:
                    logger.error("DEBUG: Fehler in Single Transaction: %s", e)
                    import traceback

                    logger.error("DEBUG: Traceback: %s", traceback.format_exc())
                    # Session rollback wird automatisch von get_session() context manager gemacht
                    raise

        except DeliveryNotFoundException as e:
            logger.error("Geschäftslogik-Fehler beim Löschen der Delivery: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Löschen der Delivery: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Löschen der Delivery: %s", e)
            raise


# Test-Funktion
if __name__ == "__main__":
    print("Testing DeliveryService...")
    try:
        service = DeliveryService()
        print("✅ DeliveryService erfolgreich erstellt!")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
