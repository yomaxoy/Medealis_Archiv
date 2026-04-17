# src/warehouse/application/services/item_service.py

"""
Item Service - Application Layer für das Warehouse Management System.

Orchestriert Item-bezogene Use Cases und verbindet Domain Logic
mit Infrastructure. Verwaltet den kompletten Item-Lebenszyklus.
"""

# Standard library imports
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

# Domain imports
from warehouse.domain.entities.item import InspectionResult
from warehouse.domain.enums.certificate_type import CertificateType
from warehouse.domain.enums.item_status import ItemStatus
from warehouse.domain.enums.priority_level import PriorityLevel
from warehouse.domain.exceptions.item_exceptions import (
    ItemNotEditableException,
    ItemNotFoundException,
)
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.value_objects.batch_number import BatchNumber

# Infrastructure imports
from warehouse.infrastructure.database.repositories.sql_delivery_rep_domain import (
    SQLAlchemyDeliveryRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.sql_item_rep_domain import (
    SQLAlchemyItemRepositoryDomain,
)
from warehouse.infrastructure.database.repositories.item_info_repository import (
    ItemInfoRepository,
)

logger = logging.getLogger(__name__)


class ItemService:
    """
    Application Service für Item-Management.

    Verwaltet den kompletten Lebenszyklus von Artikeln:
    - Status-Übergänge (Datenprüfung, Sichtprüfung, etc.)
    - Qualitätskontrolle und Inspection
    - Zertifikatsverwaltung
    - Prioritäts-Management
    """

    def __init__(self):
        try:
            # Database should already be initialized by Infrastructure Layer
            self.item_repo = SQLAlchemyItemRepositoryDomain()
            self.delivery_repo = SQLAlchemyDeliveryRepositoryDomain()
            self.item_info_repo = ItemInfoRepository()
            logger.info("ItemService erfolgreich initialisiert")
        except (ImportError, AttributeError, ConnectionError) as e:
            logger.error("Fehler bei ItemService Initialisierung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei ItemService Initialisierung: %s", e)
            raise

    # === ITEM RETRIEVAL ===

    def get_item(
        self, article_number: str, batch_number: str, delivery_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Holt einen Artikel mit allen Details.
        Falls Domain-Layer nicht verfügbar ist, fallback auf get_item_by_composite_key.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer

        Returns:
            Dictionary mit Item-Daten oder None
        """
        try:
            # Try domain layer first
            # Erstelle Value Objects für Query
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if item:
                return {
                    "article_number": str(item.article_number),
                    "batch_number": str(item.batch_number),
                    "delivery_number": item.delivery_number,
                    "supplier_id": item.supplier_id,
                    "quantity": item.delivered_quantity,
                    "current_status": (item.get_current_status()),
                    "priority_level": item.priority_level.value,
                    "completion_percentage": (item.get_completion_percentage()),
                    "created_by": item.created_by,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "unique_identifier": item.get_unique_identifier(),
                    "status_summary": item.get_status_summary(),
                    "certificates": {
                        cert_type.value: present
                        for cert_type, present in item.certificates.items()
                    },
                    "inspection_result": self._serialize_inspection_result(
                        item.inspection_result
                    ),
                    "notes": item.notes,
                    "barcode": item.barcode,
                    "storage_location": item.storage_location,
                }

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden des Items: %s", e)
            # Fallback to database layer
            return self.get_item_by_composite_key(
                article_number, batch_number, delivery_number
            )
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden des Items: %s", e)
            # Fallback to database layer
            return self.get_item_by_composite_key(
                article_number, batch_number, delivery_number
            )

    def get_items_by_delivery(self, delivery_number: str) -> List[Dict[str, Any]]:
        """Holt alle Items einer Lieferung."""
        try:
            items = self.item_repo.find_domain_by_delivery(delivery_number)
            return [
                {
                    "article_number": str(item.article_number),
                    "batch_number": str(item.batch_number),
                    "delivery_number": item.delivery_number,
                    "quantity": item.delivered_quantity,
                    "status": item.get_current_status(),
                    "priority": item.priority_level.value,
                    "completion_percentage": (item.get_completion_percentage()),
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

    def get_items_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Holt alle Items mit einem bestimmten Status."""
        try:
            status_enum = ItemStatus(status)
            items = self.item_repo.find_domain_by_status(status_enum)
            return [
                {
                    "article_number": str(item.article_number),
                    "batch_number": str(item.batch_number),
                    "delivery_number": item.delivery_number,
                    "supplier_id": item.supplier_id,
                    "quantity": item.delivered_quantity,
                    "priority": item.priority_level.value,
                    "created_by": item.created_by,
                    "unique_identifier": item.get_unique_identifier(),
                }
                for item in items
            ]
        except ValueError:
            logger.error("Ungültiger Status: %s", status)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden der Items nach Status: %s", e)
            return []

    # === STATUS TRANSITIONS ===

    def complete_data_check(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
    ) -> bool:
        """
        Schließt Datenprüfung für einen Artikel ab.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Domain logic
            item.complete_data_check(employee)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info("Datenprüfung abgeschlossen: %s", item.get_unique_identifier())
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler bei Datenprüfung: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Datenprüfung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Datenprüfung: %s", e)
            raise

    def complete_visual_inspection(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        performed_by: str,
        waste_quantity: int = 0,
        waste_reason: Optional[str] = None,
        quality_notes: Optional[str] = None,
        measurements: Optional[Dict[str, Any]] = None,
        passed: bool = True,
    ) -> bool:
        """
        Schließt Sichtprüfung für einen Artikel ab.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            performed_by: Durchführender Mitarbeiter
            waste_quantity: Ausschussmenge
            waste_reason: Grund für Ausschuss
            quality_notes: Qualitätsnotizen
            measurements: Messwerte
            passed: Prüfung bestanden

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Erstelle InspectionResult
            inspection = InspectionResult(
                performed_at=datetime.now(),
                performed_by=performed_by,
                waste_quantity=waste_quantity,
                waste_reason=waste_reason,
                quality_notes=quality_notes,
                measurements=measurements or {},
                passed=passed,
            )

            # Domain logic
            item.complete_visual_inspection(inspection)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info("Sichtprüfung abgeschlossen: %s", item.get_unique_identifier())
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler bei Sichtprüfung: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Sichtprüfung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Sichtprüfung: %s", e)
            raise

    def complete_document_check(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
        certificates: Dict[str, bool],
    ) -> bool:
        """
        Schließt Dokumentenprüfung ab und setzt Zertifikatsstatus.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter
            certificates: Dictionary mit Zertifikatstypen und Status

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Setze Zertifikate
            for cert_type_str, present in certificates.items():
                try:
                    cert_type = CertificateType(cert_type_str)
                    item.set_certificate_present(cert_type, present)
                except ValueError:
                    logger.warning("Unbekannter Zertifikatstyp: %s", cert_type_str)

            # Domain logic
            item.complete_document_check(employee)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info(
                "Dokumentenprüfung abgeschlossen: %s", item.get_unique_identifier()
            )
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler bei Dokumentenprüfung: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Dokumentenprüfung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Dokumentenprüfung: %s", e)
            raise

    def complete_measurement(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
        measurements: Dict[str, Any],
    ) -> bool:
        """
        Schließt Vermessung ab.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter
            measurements: Messwerte

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Domain logic
            item.complete_measurement(measurements, employee)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info("Vermessung abgeschlossen: %s", item.get_unique_identifier())
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler bei Vermessung: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Vermessung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Vermessung: %s", e)
            raise

    def complete_documents_merge(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
    ) -> bool:
        """
        Schließt Dokumentenzusammenführung ab (Step 5).

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Domain logic
            item.complete_documents_merge(employee)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info(
                "Dokumentenzusammenführung abgeschlossen: %s",
                item.get_unique_identifier(),
            )
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler bei Dokumentenzusammenführung: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Dokumentenzusammenführung: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Dokumentenzusammenführung: %s", e)
            raise

    def complete_item_processing(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
    ) -> bool:
        """
        Schließt die komplette Artikelbearbeitung ab.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Domain logic
            item.complete_processing(employee)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info(
                "Artikelbearbeitung abgeschlossen: %s", item.get_unique_identifier()
            )
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error(
                "Geschäftslogik-Fehler beim Abschließen der Artikelbearbeitung: %s", e
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Abschließen der Artikelbearbeitung: %s", e
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Abschließen der Artikelbearbeitung: %s", e
            )
            raise

    def get_missing_workflow_steps(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
    ) -> List[str]:
        """
        Gibt die Liste fehlender Workflow-Schritte eines Artikels zurück.

        Returns:
            Liste mit Namen der fehlenden Steps (leer = alle abgeschlossen)
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)
            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )
            if not item:
                return []
            return item.get_missing_steps()
        except Exception as e:
            logger.error("Fehler beim Ermitteln fehlender Workflow-Schritte: %s", e)
            return []

    def force_complete_item_processing(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
        reason: str,
        waste_quantity: int = 0,
        waste_reason: Optional[str] = None,
    ) -> bool:
        """
        Schließt Artikelbearbeitung manuell ab – ohne Voraussetzungs-Prüfung.
        Fehlende Schritte werden als 'Extern / {employee}' markiert.
        Für Artikel, deren Dokumentation außerhalb des Systems erstellt wurde.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter
            reason: Begründung für den manuellen Abschluss
            waste_quantity: Anzahl Ausschuss-Teile (0 = kein Ausschuss)
            waste_reason: Ursache des Ausschusses

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            item.force_complete_processing(
                employee=employee,
                reason=reason,
                waste_quantity=waste_quantity,
                waste_reason=waste_reason,
            )
            self.item_repo.save_domain(item)

            logger.info(
                "Artikel manuell eingelagert (extern): %s | Begründung: %s | Ausschuss: %d Stk.",
                item.get_unique_identifier(),
                reason,
                waste_quantity,
            )
            return True

        except (ItemNotFoundException, ItemNotEditableException) as e:
            logger.error(
                "Geschäftslogik-Fehler beim manuellen Einlagern: %s", e
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim manuellen Einlagern: %s", e
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim manuellen Einlagern: %s", e
            )
            raise

    def mark_item_as_waste(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        employee: str,
        reason: str,
    ) -> bool:
        """
        Markiert Artikel als Ausschuss.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            employee: Durchführender Mitarbeiter
            reason: Grund für Ausschuss

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Domain logic
            item.mark_as_waste(reason, employee)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info(
                "Artikel als Ausschuss markiert: %s", item.get_unique_identifier()
            )
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler beim Markieren als Ausschuss: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Markieren als Ausschuss: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Markieren als Ausschuss: %s", e)
            raise

    # === PRIORITY MANAGEMENT ===

    def set_item_priority(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        priority_level: str,
    ) -> bool:
        """
        Setzt Prioritätsstufe für einen Artikel.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            priority_level: Prioritätsstufe (HIGH, MEDIUM, LOW)

        Returns:
            True wenn erfolgreich
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Validiere Priority Level
            priority_enum = PriorityLevel(priority_level)

            # Domain logic
            item.set_priority_level(priority_enum)

            # Persistiere
            self.item_repo.save_domain(item)

            logger.info(
                "Priorität gesetzt: %s -> %s",
                item.get_unique_identifier(),
                priority_level,
            )
            return True

        except ValueError:
            logger.error("Ungültige Prioritätsstufe: %s", priority_level)
            raise
        except (ItemNotFoundException, ItemNotEditableException) as e:
            logger.error("Geschäftslogik-Fehler beim Setzen der Priorität: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Setzen der Priorität: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Setzen der Priorität: %s", e)
            raise

    # === UTILITY METHODS ===

    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Holt alle Items für die GUI-Liste mit ItemInfo-Daten.

        OPTIMIZED: Uses single LEFT JOIN query instead of N+1 queries.

        Performance:
            - Before: 1 + N queries (30 queries for 29 items)
            - After: 1 query (100x faster at scale)

        Returns:
            Liste von Item-Dictionaries inklusive ItemInfo
        """
        try:
            # OPTIMIZED: Load items with info in single query using LEFT JOIN
            items_with_info = self.item_repo.find_all_with_info()

            # Safety check
            if items_with_info is None:
                logger.warning(
                    "find_all_with_info() returned None, returning empty list"
                )
                return []

            item_list = []

            for item, item_info in items_with_info:
                # Basic item data
                item_dict = {
                    "article_number": str(item.article_number),
                    "batch_number": str(item.batch_number),
                    "delivery_number": item.delivery_number,
                    # === DREI MENGENTYPEN ===
                    # Backward compatibility
                    "quantity": item.delivered_quantity,
                    "delivered_quantity": item.delivered_quantity,
                    # ADDED: For context_builder compatibility
                    "delivery_quantity": item.delivered_quantity,
                    "delivery_slip_quantity": getattr(
                        item, "delivery_slip_quantity", None
                    ),
                    "ordered_quantity": getattr(item, "ordered_quantity", None),
                    # ADDED: For context_builder compat
                    "order_quantity": getattr(item, "ordered_quantity", None),
                    # NEU: gibt String zurueck
                    "status": item.get_current_status(),
                    "employee_name": item.created_by,
                    "order_number": getattr(item, "order_number", None),
                    "created_at": item.created_at.isoformat()
                    if hasattr(item, "created_at") and item.created_at
                    else None,
                }

                # Add ItemInfo data (already loaded via JOIN - no extra query!)
                if item_info:
                    item_dict.update(
                        {
                            "designation": item_info.get("designation", ""),
                            "revision_number": item_info.get("revision_number"),
                            "storage_location": item_info.get("storage_location", ""),
                            "hersteller": item_info.get("hersteller", ""),
                            "kompatibilitaet": item_info.get("kompatibilitaet", ""),
                            # order_quantity: nutze Item.ordered_quantity
                        }
                    )
                else:
                    # Default values if no ItemInfo exists
                    item_dict.update(
                        {
                            "designation": "",
                            "revision_number": None,
                            "storage_location": "",
                            "hersteller": "",
                            "kompatibilitaet": "",
                        }
                    )

                # Add certificate data from domain entity
                try:
                    # Convert domain certificates to dict format for UI
                    certificate_data = {}
                    if hasattr(item, "certificates") and item.certificates:
                        from warehouse.domain.enums.certificate_type import (
                            CertificateType,
                        )

                        # Map German domain enums to English UI keys
                        certificate_data = {
                            "material_certificate": item.certificates.get(
                                CertificateType.MATERIALZEUGNIS, False
                            ),
                            "measurement_protocol": item.certificates.get(
                                CertificateType.MESSPROTOKOLL, False
                            ),
                            "coating_certificate": item.certificates.get(
                                CertificateType.BESCHICHTUNGSZEUGNIS, False
                            ),
                            "hardness_certificate": item.certificates.get(
                                CertificateType.HAERTEZEUGNIS, False
                            ),
                            "additional_certificates": item.certificates.get(
                                CertificateType.WEITERE_ZEUGNISSE, False
                            ),
                            # Physical document flags from certificates
                            "label_present": item.certificates.get(
                                CertificateType.ETIKETT, False
                            ),
                            "accompanying_document": item.certificates.get(
                                CertificateType.BEGLEITSCHEIN, False
                            ),
                        }
                    else:
                        # Default values if no certificates
                        certificate_data = {
                            "material_certificate": False,
                            "measurement_protocol": False,
                            "coating_certificate": False,
                            "hardness_certificate": False,
                            "additional_certificates": False,
                            "label_present": False,
                            "accompanying_document": False,
                        }

                    item_dict["certificates"] = certificate_data

                except Exception as e:
                    logger.warning(
                        "Could not fetch certificates" " for %s: %s",
                        item.article_number,
                        e,
                    )
                    # Default certificate values on error
                    item_dict["certificates"] = {
                        "material_certificate": False,
                        "measurement_protocol": False,
                        "coating_certificate": False,
                        "hardness_certificate": False,
                        "additional_certificates": False,
                        "label_present": False,
                        "accompanying_document": False,
                    }

                item_list.append(item_dict)

            return item_list

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Laden aller Items: %s", e)
            return []
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Laden aller Items: %s", e)
            return []

    def get_all_item_infos(self) -> List[Dict[str, Any]]:
        """
        Holt alle ItemInfo-Stammdaten (eine Zeile pro Artikel, ohne Chargen).
        Für die Artikel-Übersicht (nicht für Chargen-Details).

        Returns:
            Liste von Item-Info-Dictionaries mit: article_number, designation,
            kompatibilitaet, hersteller, revision_number, storage_location
        """
        try:
            item_infos = self.item_info_repo.get_all()

            if not item_infos:
                return []

            item_list = []
            for item_info in item_infos:
                item_dict = {
                    "article_number": item_info.article_number,
                    "designation": item_info.designation or "",
                    "kompatibilitaet": item_info.kompatibilitaet or "",
                    "hersteller": item_info.hersteller or "",
                    "revision_number": item_info.revision_number,
                    "storage_location": item_info.storage_location or "",
                    "material_specification": item_info.material_specification or "",
                    "drawing_reference": item_info.drawing_reference or "",
                    "description": item_info.description or "",
                    "created_at": item_info.created_at.isoformat() if item_info.created_at else None,
                }
                item_list.append(item_dict)

            return item_list

        except Exception as e:
            logger.error(f"Fehler beim Laden aller ItemInfos: {e}")
            return []

    def get_item_statistics(self) -> Dict[str, Any]:
        """Holt Item-Statistiken für Dashboard."""
        try:
            stats = self.item_repo.get_repository_statistics()
            return stats
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Laden" " der Item-Statistiken: %s",
                e,
            )
            return {}
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Laden" " der Item-Statistiken: %s",
                e,
            )
            return {}

    def item_exists(
        self, article_number: str, batch_number: str, delivery_number: str
    ) -> bool:
        """Prüft, ob ein Item existiert."""
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)
            return self.item_repo.exists_domain(article_vo, batch_vo, delivery_number)
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler bei Item-Existenzprüfung: %s", e)
            return False
        except Exception as e:
            logger.error("Unerwarteter Fehler bei Item-Existenzprüfung: %s", e)
            return False

    def check_batch_number_change_impact(
        self,
        current_article_number: str,
        current_batch_number: str,
        delivery_number: str,
        new_batch_number: str,
        new_article_number: str = None,
    ) -> dict:
        """
        Prüft die Auswirkungen einer Chargennummer-Änderung.

        Args:
            current_article_number: Aktuelle Artikelnummer
            current_batch_number: Aktuelle Chargennummer
            delivery_number: Lieferscheinnummer
            new_batch_number: Neue Chargennummer
            new_article_number: Neue Artikelnummer (optional)

        Returns:
            Dictionary mit Informationen über mögliche Konflikte:
            {
                'has_conflict': bool,
                'conflict_type': str,  # 'duplicate', 'none'
                'existing_item': dict,  # Existierendes Item falls Duplikat
                'recommendation': str,  # Empfehlung für den Benutzer
                'can_merge': bool,  # Ob Mengen kombiniert werden können
            }
        """
        try:
            # Keine Änderung der Chargennummer
            if new_batch_number == current_batch_number:
                return {
                    "has_conflict": False,
                    "conflict_type": "none",
                    "existing_item": None,
                    "recommendation": "No batch number change detected.",
                    "can_merge": False,
                }

            # Bestimme die zu prüfende Artikelnummer
            check_article = (
                new_article_number if new_article_number else current_article_number
            )

            # Prüfe, ob bereits ein Item mit der neuen Chargennummer existiert
            existing_item = self.get_item(
                check_article, new_batch_number, delivery_number
            )

            if existing_item:
                return {
                    "has_conflict": True,
                    "conflict_type": "duplicate",
                    "existing_item": existing_item,
                    "recommendation": (
                        "Ein Artikel mit Chargennummer"
                        f" '{new_batch_number}' existiert"
                        " bereits fuer Artikel"
                        f" '{check_article}' in Lieferung"
                        f" '{delivery_number}'. Die Mengen"
                        " koennen zusammengefuehrt"
                        " werden, oder waehlen Sie"
                        " eine andere Chargennummer."
                    ),
                    "can_merge": True,
                }

            # Keine Konflikte gefunden
            return {
                "has_conflict": False,
                "conflict_type": "none",
                "existing_item": None,
                "recommendation": (
                    "Chargennummer kann sicher auf"
                    f" '{new_batch_number}'"
                    " geaendert werden."
                ),
                "can_merge": False,
            }

        except Exception as e:
            logger.error("Fehler bei Chargennummer-Konfliktprüfung: %s", e)
            return {
                "has_conflict": True,
                "conflict_type": "error",
                "existing_item": None,
                "recommendation": ("Fehler bei der" f" Konfliktpruefung: {e}"),
                "can_merge": False,
            }

    def _serialize_inspection_result(
        self, inspection: Optional[InspectionResult]
    ) -> Optional[Dict[str, Any]]:
        """Serialisiert InspectionResult für API Response."""
        if not inspection:
            return None

        return {
            "performed_at": inspection.performed_at.isoformat(),
            "performed_by": inspection.performed_by,
            "waste_quantity": inspection.waste_quantity,
            "waste_reason": inspection.waste_reason,
            "quality_notes": inspection.quality_notes,
            "measurements": inspection.measurements,
            "passed": inspection.passed,
        }

    # === ITEM UPDATE & DELETE OPERATIONS ===

    def update_item(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        new_article_number: str = None,
        new_batch_number: str = None,
        new_quantity: int = None,
        employee_name: str = None,
        order_number: str = None,
        delivery_slip_quantity: int = None,
        ordered_quantity: int = None,
        # Certificate parameters
        measurement_protocol: bool = None,
        material_certificate: bool = None,
        coating_certificate: bool = None,
        hardness_certificate: bool = None,
        additional_certificates: bool = None,
        label_present: bool = None,
        accompanying_document: bool = None,
    ) -> bool:
        """
        Aktualisiert ein Item.

        Args:
            article_number: Aktuelle Artikelnummer
            batch_number: Aktuelle Chargennummer
            delivery_number: Lieferscheinnummer
            new_article_number: Neue Artikelnummer
            new_batch_number: Neue Chargennummer
            new_quantity: Neue Quantity
            employee_name: Employee Name
            order_number: Bestellnummer
            measurement_protocol: Messprotokoll-Zertifikat
            material_certificate: Material-Zertifikat
            coating_certificate: Beschichtungs-Zertifikat
            hardness_certificate: Härte-Zertifikat
            additional_certificates: Weitere Zertifikate
            label_present: Etikett vorhanden
            accompanying_document: Begleitschein vorhanden

        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Check for potential duplication when changing batch number
            if new_batch_number and new_batch_number != batch_number:
                # Use the new article number if provided, otherwise the current one
                check_article = (
                    new_article_number if new_article_number else article_number
                )

                # Check if an item with the new batch number already exists
                existing_item = self.item_repo.find_domain_by_composite_key(
                    ArticleNumber(check_article),
                    BatchNumber(new_batch_number),
                    delivery_number,
                )

                if existing_item:
                    # An item with the new batch number already exists
                    if new_quantity is not None:
                        # Merge quantities: add the new quantity to the existing item
                        existing_item.delivered_quantity = (
                            existing_item.delivered_quantity or 0
                        ) + new_quantity  # FIXED

                        # Delete the original item to avoid duplication
                        self.item_repo.delete_domain(
                            article_vo, batch_vo, delivery_number
                        )

                        # Update the existing item with merged data
                        if employee_name:
                            existing_item.employee_name = employee_name

                        # Save the existing item with merged data
                        self.item_repo.save_domain(existing_item)

                        logger.info(
                            "Items merged: %s -> %s (quantity merged: %d)",
                            item.get_unique_identifier(),
                            existing_item.get_unique_identifier(),
                            new_quantity,
                        )
                        return True
                    else:
                        # Cannot change batch number to an existing one without merging
                        raise ValueError(
                            "Item with batch number"
                            f" '{new_batch_number}'"
                            " already exists for"
                            f" article '{check_article}'"
                            " in delivery"
                            f" '{delivery_number}'."
                            " Provide a quantity to"
                            " merge, or use a different"
                            " batch number."
                        )

            # Standard update if no batch number conflict
            # Keep track of original composite key for deletion if batch number changes
            original_article_vo = article_vo
            original_batch_vo = batch_vo
            original_delivery = delivery_number
            batch_number_changed = False
            article_number_changed = False

            if new_article_number:
                item.article_number = ArticleNumber(new_article_number)
                article_number_changed = True
            if new_batch_number:
                item.batch_number = BatchNumber(new_batch_number)
                batch_number_changed = True
            if new_quantity:
                item.delivered_quantity = (
                    new_quantity  # FIXED: quantity → delivered_quantity
                )
            if employee_name:
                item.employee_name = employee_name
            if order_number is not None:
                item.order_number = order_number

            # Update certificate flags if provided
            # Import CertificateType for proper domain mapping
            from warehouse.domain.enums.certificate_type import CertificateType

            certificate_updates = []
            if measurement_protocol is not None:
                item.certificates[CertificateType.MESSPROTOKOLL] = measurement_protocol
                certificate_updates.append(
                    f"measurement_protocol={measurement_protocol}"
                )
            if material_certificate is not None:
                item.certificates[
                    CertificateType.MATERIALZEUGNIS
                ] = material_certificate
                certificate_updates.append(
                    f"material_certificate={material_certificate}"
                )
            if coating_certificate is not None:
                item.certificates[
                    CertificateType.BESCHICHTUNGSZEUGNIS
                ] = coating_certificate
                certificate_updates.append(
                    "coating_certificate=" f"{coating_certificate}"
                )
            if hardness_certificate is not None:
                item.certificates[CertificateType.HAERTEZEUGNIS] = hardness_certificate
                certificate_updates.append(
                    f"hardness_certificate={hardness_certificate}"
                )
            if additional_certificates is not None:
                item.certificates[
                    CertificateType.WEITERE_ZEUGNISSE
                ] = additional_certificates
                certificate_updates.append(
                    f"additional_certificates={additional_certificates}"
                )
            if label_present is not None:
                item.certificates[CertificateType.ETIKETT] = label_present
                certificate_updates.append(f"label_present={label_present}")
            if accompanying_document is not None:
                item.certificates[CertificateType.BEGLEITSCHEIN] = accompanying_document
                certificate_updates.append(
                    f"accompanying_document={accompanying_document}"
                )

            if certificate_updates:
                batch_key = new_batch_number or batch_number
                cert_str = ", ".join(certificate_updates)
                logger.info(
                    "DEBUG CERTIFICATES: Updating item " "%s/%s certificates: %s",
                    article_number,
                    batch_key,
                    cert_str,
                )

            # If batch/article number changed, delete old item
            # first to avoid duplicates
            if batch_number_changed or article_number_changed:
                # Delete the original item with old composite key
                delete_success = self.item_repo.delete_domain(
                    original_article_vo, original_batch_vo, original_delivery
                )
                if delete_success:
                    logger.info(
                        "Original item deleted (key changed): %s_%s_%s",
                        str(original_article_vo),
                        str(original_batch_vo),
                        original_delivery,
                    )
                else:
                    logger.warning(
                        "Could not delete original item: %s_%s_%s",
                        str(original_article_vo),
                        str(original_batch_vo),
                        original_delivery,
                    )

            # Persistiere das Item (mit neuer Chargennummer falls geändert)
            self.item_repo.save_domain(item)

            # FIXED: Update delivery_slip_quantity and
            # ordered_quantity directly in DB (not Domain)
            if delivery_slip_quantity is not None or ordered_quantity is not None:
                from warehouse.infrastructure.database.connection import get_session
                from warehouse.infrastructure.database.models.item_model import (
                    ItemModel,
                )

                with get_session() as session:
                    # Find item in DB with NEW keys if changed
                    db_article = (
                        new_article_number if new_article_number else article_number
                    )
                    db_batch = new_batch_number if new_batch_number else batch_number

                    db_item = (
                        session.query(ItemModel)
                        .filter_by(
                            article_number=db_article,
                            batch_number=db_batch,
                            delivery_number=delivery_number,
                        )
                        .first()
                    )

                    if db_item:
                        if delivery_slip_quantity is not None:
                            db_item.delivery_slip_quantity = delivery_slip_quantity
                            logger.info(
                                "Updated delivery_slip_quantity" " to %s for %s/%s",
                                delivery_slip_quantity,
                                db_article,
                                db_batch,
                            )
                        if ordered_quantity is not None:
                            db_item.ordered_quantity = ordered_quantity
                            logger.info(
                                "Updated ordered_quantity" " to %s for %s/%s",
                                ordered_quantity,
                                db_article,
                                db_batch,
                            )
                        session.commit()

            if batch_number_changed or article_number_changed:
                changes = []
                if article_number_changed:
                    changes.append(
                        f"article: {str(original_article_vo)} -> {item.article_number}"
                    )
                if batch_number_changed:
                    changes.append(
                        f"batch: {str(original_batch_vo)} -> {item.batch_number}"
                    )
                logger.info(
                    "Item key changed (%s): %s_%s_%s -> %s",
                    ", ".join(changes),
                    str(original_article_vo),
                    str(original_batch_vo),
                    original_delivery,
                    item.get_unique_identifier(),
                )
            else:
                logger.info(
                    "Item %s erfolgreich aktualisiert", item.get_unique_identifier()
                )

            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error("Geschäftslogik-Fehler beim Aktualisieren des Items: %s", e)
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Aktualisieren des Items: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Aktualisieren des Items: %s", e)
            raise

    def update_item_notes(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        notes: str,
    ) -> bool:
        """
        Aktualisiert die Notizen eines Items.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            notes: Neue Notizen

        Returns:
            True wenn erfolgreich aktualisiert
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            # Item aus Repository laden
            item = self.item_repo.find_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Notizen aktualisieren
            item.notes = notes

            # Item speichern
            self.item_repo.save_domain(item)

            logger.info(
                "Item-Notizen erfolgreich aktualisiert: %s",
                item.get_unique_identifier(),
            )
            return True

        except (ItemNotFoundException, ItemNotEditableException, ValueError) as e:
            logger.error(
                "Geschäftslogik-Fehler beim Aktualisieren der Item-Notizen: %s", e
            )
            raise
        except (ConnectionError, AttributeError) as e:
            logger.error(
                "Infrastructure-Fehler beim Aktualisieren der Item-Notizen: %s", e
            )
            raise
        except Exception as e:
            logger.error(
                "Unerwarteter Fehler beim Aktualisieren der Item-Notizen: %s", e
            )
            raise

    def delete_item(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
    ) -> bool:
        """
        Löscht ein Item.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer

        Returns:
            True wenn erfolgreich gelöscht
        """
        try:
            article_vo = ArticleNumber(article_number)
            batch_vo = BatchNumber(batch_number)

            # Prüfe, ob Item existiert
            item = self.item_repo.find_domain_by_composite_key(
                article_vo, batch_vo, delivery_number
            )

            if not item:
                raise ItemNotFoundException(
                    article_number, batch_number, delivery_number
                )

            # Lösche über Repository
            success = self.item_repo.delete_domain(
                article_vo, batch_vo, delivery_number
            )

            if success:
                logger.info(
                    "Item %s erfolgreich gelöscht", item.get_unique_identifier()
                )
            else:
                logger.warning(
                    "Item %s konnte nicht gelöscht werden", item.get_unique_identifier()
                )

            return success

        except ItemNotFoundException as e:
            logger.error("Geschäftslogik-Fehler beim Löschen des Items: %s", e)
            return False
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Löschen des Items: %s", e)
            return False
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Löschen des Items: %s", e)
            return False

    def save_item_info(
        self,
        article_number: str,
        designation: str = "",
        revision_number: int = None,
        drawing_reference: str = "",
        storage_location: str = "",
        manufacturer: str = "",
        material_specification: str = "",
        description: str = "",
    ) -> str:
        """
        Speichert oder aktualisiert ItemInfo (Artikel-Stammdaten).

        Args:
            article_number: Artikelnummer
            designation: Bezeichnung
            revision_number: Revisionsnummer
            drawing_reference: Zeichnungsreferenz
            storage_location: Lagerplatz
            manufacturer: Hersteller
            material_specification: Materialspezifikation
            description: Beschreibung

        Returns:
            article_number des gespeicherten ItemInfo
        """
        try:
            return self.item_repo.save_item_info(
                article_number=article_number,
                designation=designation,
                revision_number=revision_number,
                drawing_reference=drawing_reference,
                storage_location=storage_location,
                manufacturer=manufacturer,
                material_specification=material_specification,
                description=description,
            )
        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Speichern der ItemInfo: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Speichern der ItemInfo: %s", e)
            raise

    def create_item(
        self,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        delivered_quantity: int = None,
        delivery_slip_quantity: int = None,
        ordered_quantity: int = None,
        quantity: int = None,  # BACKWARD COMPAT
        order_number: str = "",
        expiry_date=None,
        storage_location: str = "",
        description: str = "",
        status: str = "received",
        employee_name: str = "",
        supplier_id: str = "",
    ) -> str:
        """
        Creates a new Item with the given parameters.
        Compatible with streamlit_app.py create_item calls.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            delivered_quantity: Tatsächlich gelieferte Menge (gezählt)
            delivery_slip_quantity: Lieferscheinmenge (OCR-extrahiert)
            ordered_quantity: Bestellmenge (aus Bestellung)
            quantity: DEPRECATED - nutze delivered_quantity
            order_number: Bestellnummer (optional)
            expiry_date: Ablaufdatum (optional, ignored)
            storage_location: Lagerplatz (optional, ignored)
            description: Beschreibung (optional, ignored)
            status: Status (optional, ignored)
            employee_name: Mitarbeitername (optional, mapped to created_by)
            supplier_id: Lieferant (optional, ignored)

        Returns:
            Unique identifier for created item (composite key)
        """
        try:
            # Direct approach: Create ItemInfo and Item in single transaction
            from warehouse.infrastructure.database.connection import get_session
            from warehouse.infrastructure.database.models.item_model import (
                ItemInfoModel,
                ItemModel,
            )

            logger.info(
                "DEBUG create_item: description" " parameter = '%s'",
                description,
            )

            with get_session() as session:
                # First ensure ItemInfo exists with proper data
                item_info = session.get(ItemInfoModel, article_number)

                if not item_info:
                    # Create ItemInfo with provided description
                    desig = description or (f"Artikel {article_number}")
                    logger.info(
                        "DEBUG: Creating NEW ItemInfo" " with designation='%s'",
                        desig,
                    )
                    item_info = ItemInfoModel(
                        article_number=article_number,
                        designation=desig,
                        description=description
                        or "Automatisch erstellt via Item Creation",
                    )
                    session.add(item_info)
                    session.flush()  # Ensure ItemInfo is created before Item

                    # Set workflow status for newly created ItemInfo
                    self._set_iteminfo_complete_status(session, article_number)
                else:
                    logger.info(
                        "DEBUG: ItemInfo ALREADY EXISTS" " for %s, designation='%s'",
                        article_number,
                        item_info.designation,
                    )
                    # Update designation if we have a better value
                    if description and description.strip():
                        # Only update if designation is empty/generic
                        current_designation = item_info.designation or ""
                        if (
                            not current_designation.strip()
                            or current_designation.startswith("Artikel ")
                            or current_designation == "Claude Import"
                            or current_designation
                            == "Automatisch erstellt via Item Creation"
                        ):
                            logger.info(
                                "DEBUG: Updating ItemInfo"
                                " designation from"
                                " '%s' to '%s'",
                                item_info.designation,
                                description,
                            )
                            item_info.designation = description
                            item_info.description = description
                            session.flush()

                            # Set workflow status for updated ItemInfo
                            self._set_iteminfo_complete_status(session, article_number)

                # Now create the Item
                # Handle order_number: Check if order exists, create if not
                final_order_number = None
                if order_number and order_number.strip():
                    # Check if order exists in database
                    from warehouse.infrastructure.database.models.order_model import (
                        OrderModel,
                    )

                    existing_order = session.get(OrderModel, order_number.strip())
                    if existing_order:
                        final_order_number = order_number.strip()
                    else:
                        # Create new order automatically if it doesn't exist
                        logger.info(
                            "Creating new order %s" " automatically",
                            order_number,
                        )
                        from datetime import date

                        # Ensure AUTO_SUPP supplier exists
                        from warehouse.infrastructure.database.models.supplier_model import (  # noqa: E501
                            SupplierModel,
                        )

                        auto_supplier = session.get(SupplierModel, "AUTO_SUPP")
                        if not auto_supplier:
                            auto_supplier = SupplierModel(
                                supplier_id="AUTO_SUPP",
                                name="Auto-created Supplier",
                                contact_person="System",
                                notes=(
                                    "Automatically created supplier"
                                    " for orders from"
                                    " delivery imports"
                                ),
                            )
                            session.add(auto_supplier)
                            session.flush()

                        new_order = OrderModel(
                            order_number=order_number.strip(),
                            # Default supplier for auto-created
                            # orders (max 10 chars)
                            supplier_id="AUTO_SUPP",
                            employee_name=employee_name or "System",
                            status="open",
                            order_date=date.today(),  # Set current date
                            notes=(
                                "Auto-created from delivery"
                                " import on "
                                + datetime.now().strftime("%Y-%m-%d %H:%M")
                            ),
                        )
                        session.add(new_order)
                        session.flush()  # Ensure order is created before using it
                        final_order_number = order_number.strip()
                        logger.info(
                            "Order %s created successfully",
                            order_number,
                        )

                # === BACKWARD COMPATIBILITY: quantity → delivered_quantity ===
                final_delivered_quantity = (
                    delivered_quantity if delivered_quantity is not None else quantity
                )
                if final_delivered_quantity is None:
                    final_delivered_quantity = (
                        delivery_slip_quantity
                        if delivery_slip_quantity is not None
                        else 1
                    )

                # Laden der supplier_id aus der Delivery, falls nicht angegeben
                final_supplier_id = supplier_id or ""
                if not final_supplier_id:
                    # Versuche supplier_id aus der DeliveryModel zu laden
                    try:
                        from warehouse.infrastructure.database.models.delivery_model import DeliveryModel
                        delivery = session.query(DeliveryModel).filter(
                            DeliveryModel.delivery_number == delivery_number
                        ).first()
                        if delivery:
                            final_supplier_id = delivery.supplier_id
                    except Exception as e:
                        logger.warning(f"Could not load supplier from delivery: {e}")

                item = ItemModel(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    # Tatsaechlich geliefert
                    delivered_quantity=final_delivered_quantity,
                    # Lieferschein (OCR)
                    delivery_slip_quantity=delivery_slip_quantity,
                    # Bestellung (optional)
                    ordered_quantity=ordered_quantity,
                    # NULL instead of empty string
                    order_number=final_order_number,
                    # Lieferant (Denormalisierung für schnellere Abfragen)
                    supplier_id=final_supplier_id or None,
                    employee=employee_name or "System",
                )
                session.add(item)
                session.flush()  # Ensure item is created

                # BACKWARD COMPAT: Fulle alte
                # delivery_quantity Spalte (falls vorhanden)
                try:
                    session.execute(
                        text(
                            "UPDATE items SET"
                            " delivery_quantity = :qty"
                            " WHERE article_number = :art"
                            " AND batch_number = :batch"
                            " AND delivery_number = :del"
                        ),
                        {
                            "qty": final_delivered_quantity,
                            "art": article_number,
                            "batch": batch_number,
                            "del": delivery_number,
                        },
                    )
                except Exception:
                    pass  # Spalte existiert vielleicht nicht mehr

                # Transaction will be committed by context manager
                result = (article_number, batch_number, delivery_number)

            # Result is a tuple (article_number, batch_number, delivery_number)
            # Return a string identifier compatible with streamlit_app.py expectations
            if isinstance(result, tuple) and len(result) >= 3:
                return f"{result[0]}-{result[1]}-{result[2]}"
            else:
                return str(result)

        except (ConnectionError, AttributeError) as e:
            logger.error("Infrastructure-Fehler beim Erstellen des Items: %s", e)
            raise
        except Exception as e:
            logger.error("Unerwarteter Fehler beim Erstellen des Items: %s", e)
            raise

    def get_item_by_composite_key(
        self, article_number: str, batch_number: str, delivery_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Simple method to get item data directly from database.
        Compatible with inspection workflow requirements.

        Args:
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer

        Returns:
            Dictionary with item data including status, or None if not found
        """
        try:
            from warehouse.infrastructure.database.connection import get_session
            from warehouse.infrastructure.database.models.item_model import (
                ItemModel,
                ItemInfoModel,
            )
            from warehouse.infrastructure.database.models.delivery_model import (
                DeliveryModel,
            )

            with get_session() as session:
                # Query the ItemModel directly
                item = (
                    session.query(ItemModel)
                    .filter_by(
                        article_number=article_number,
                        batch_number=batch_number,
                        delivery_number=delivery_number,
                    )
                    .first()
                )

                if not item:
                    logger.warning(
                        "DEBUG CERTIFICATES: Item not" " found in DB: %s/%s/%s",
                        article_number,
                        batch_number,
                        delivery_number,
                    )
                    return None

                # Log raw database certificate values
                logger.info(
                    "DEBUG CERTIFICATES: Raw DB values"
                    " for %s/%s: "
                    "measurement_protocol=%s, "
                    "material_certificate=%s, "
                    "coating_certificate=%s, "
                    "hardness_certificate=%s, "
                    "additional_certificates=%s, "
                    "label_present=%s, "
                    "accompanying_document=%s",
                    article_number,
                    batch_number,
                    item.measurement_protocol,
                    item.material_certificate,
                    item.coating_certificate,
                    item.hardness_certificate,
                    item.additional_certificates,
                    item.label_present,
                    item.accompanying_document,
                )

                # Get additional data from related tables
                item_info = session.get(ItemInfoModel, article_number)
                delivery = session.get(DeliveryModel, delivery_number)

                # Lade Lieferantenname aus suppliers-Tabelle (DeliveryModel hat nur supplier_id FK)
                supplier_id = delivery.supplier_id if delivery else ""
                supplier_name = ""
                if supplier_id:
                    from warehouse.infrastructure.database.models.supplier_model import SupplierModel
                    supplier = session.get(SupplierModel, supplier_id)
                    supplier_name = supplier.name if supplier else supplier_id

                # Return dictionary compatible with UI expectations
                return {
                    "article_number": item.article_number,
                    "batch_number": item.batch_number,
                    "delivery_number": item.delivery_number,
                    # === DREI MENGENTYPEN ===
                    # Tatsaechlich geliefert
                    "delivered_quantity": (item.delivered_quantity),
                    # Lieferschein (OCR)
                    "delivery_slip_quantity": (item.delivery_slip_quantity),
                    # Bestellung
                    "ordered_quantity": item.ordered_quantity,
                    # === BACKWARD COMPATIBILITY ===
                    # Fallback fuer alten Code
                    "quantity": item.delivered_quantity,
                    "delivery_quantity": (item.delivered_quantity),
                    # Default status for newly created items
                    "status": "Artikel angelegt",
                    "employee_name": item.employee or "System",
                    "order_number": item.order_number,
                    "created_at": item.created_at.isoformat()
                    if item.created_at
                    else None,
                    "designation": item_info.designation
                    if item_info
                    else f"Artikel {article_number}",
                    "revision_number": item_info.revision_number if item_info else "",
                    "storage_location": item_info.storage_location if item_info else "",
                    "hersteller": item_info.hersteller if item_info else "",
                    "kompatibilitaet": (item_info.kompatibilitaet if item_info else ""),
                    "supplier_name": supplier_name,
                    "supplier_id": supplier_id,
                    # Certificate data for template
                    # generation and popup pre-filling
                    "certificates": {
                        "measurement_protocol": (item.measurement_protocol or False),
                        "material_certificate": (item.material_certificate or False),
                        "coating_certificate": (item.coating_certificate or False),
                        "hardness_certificate": (item.hardness_certificate or False),
                        "additional_certificates": (
                            item.additional_certificates or False
                        ),
                        "label_present": (item.label_present or False),
                        "accompanying_document": (item.accompanying_document or False),
                    },
                }

        except Exception as e:
            logger.error(
                "Error retrieving item by composite" " key: %s",
                e,
            )
            return None

    def _set_iteminfo_complete_status(self, session, article_number: str) -> None:
        """
        Setzt automatisch den Workflow-Status
        "Artikeldetails vollständig" für alle Items mit
        dieser Artikelnummer.

        Args:
            session: Aktive SQLAlchemy Session
            article_number: Artikelnummer
        """
        try:
            from warehouse.infrastructure.database.models.item_workflow_steps_model import (  # noqa: E501
                ItemWorkflowStepsModel,
            )

            # Finde alle Workflow-Einträge für diese Artikelnummer
            workflow_entries = (
                session.query(ItemWorkflowStepsModel)
                .filter(ItemWorkflowStepsModel.article_number == article_number)
                .all()
            )

            if not workflow_entries:
                logger.debug(
                    "No workflow entries found for" " article %s",
                    article_number,
                )
                return

            # Setze Status für alle gefundenen Einträge
            current_user = (
                "System"  # TODO: Könnte aus session_state kommen falls verfügbar
            )
            current_time = datetime.now()

            for workflow in workflow_entries:
                # Nur setzen wenn noch nicht gesetzt
                if not workflow.iteminfo_complete_at:
                    workflow.iteminfo_complete_by = current_user
                    workflow.iteminfo_complete_at = current_time
                    logger.info(
                        "Workflow status 'Artikeldetails"
                        " vollstaendig' set for"
                        " %s/%s/%s",
                        article_number,
                        workflow.batch_number,
                        workflow.delivery_number,
                    )

            session.flush()

        except Exception as e:
            logger.error(
                "Error setting iteminfo_complete" " status: %s",
                str(e),
            )
            logger.exception("Full traceback:")


# Test-Funktion
if __name__ == "__main__":
    print("Testing ItemService...")
    try:
        service = ItemService()
        print("ItemService erfolgreich erstellt!")
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback

        traceback.print_exc()
