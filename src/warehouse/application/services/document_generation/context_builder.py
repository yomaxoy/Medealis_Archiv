"""
Context Builder - Generation Context Management

Zentrale Komponente für das Aufbauen und Verwalten von GenerationContext-Objekten.
Integriert mit dem Phase 1 Storage System und bietet intelligente Context-Erstellung
aus verschiedenen Datenquellen.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import asdict

# Internal imports
from .generation_models import GenerationContext
from .document_types import DocumentType, get_template_info

logger = logging.getLogger(__name__)

# Import Storage System (Phase 1) - mit Error Handling
try:
    from ..document_storage.storage_context import StorageContextData, StorageContext

    STORAGE_SYSTEM_AVAILABLE = True
except ImportError:
    logger.warning(
        "Phase 1 Storage System not available - using minimal context building"
    )
    STORAGE_SYSTEM_AVAILABLE = False


class ContextBuilder:
    """
    Zentrale Context-Builder-Klasse für Document Generation.

    Erstellt GenerationContext aus verschiedenen Datenquellen:
    - Phase 1 StorageContextData
    - Direkte Parameter
    - Warehouse Domain Entities (Items, Deliveries, etc.)
    - Bestehende Context-Daten
    """

    def __init__(self):
        """Initialize Context Builder."""
        self.storage_context_service = None

        # Setup Storage System Integration
        if STORAGE_SYSTEM_AVAILABLE:
            try:
                self.storage_context_service = StorageContext()
                logger.info(
                    "ContextBuilder initialized with "
                    "Phase 1 Storage System integration"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Storage System " f"integration: {e}"
                )
                self.storage_context_service = None

        # Statistics
        self.stats = {
            "contexts_built": 0,
            "storage_integrations": 0,
            "validation_failures": 0,
            "data_quality_warnings": 0,
        }

    def build_from_storage_context(
        self,
        storage_context: "StorageContextData",
        document_type: DocumentType,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> GenerationContext:
        """
        Erstellt GenerationContext aus Phase 1 StorageContextData.

        Args:
            storage_context: StorageContextData aus Phase 1
            document_type: Document Type für Generation
            additional_data: Zusätzliche Daten für Context

        Returns:
            Vollständiger GenerationContext
        """
        try:
            # Basis Context aus Storage-Daten erstellen
            generation_context = GenerationContext(
                # Pflicht-Felder aus Storage
                batch_number=storage_context.batch_number,
                delivery_number=storage_context.delivery_number,
                article_number=storage_context.article_number,
                # Supplier, Hersteller & Kompatibilität
                supplier_name=storage_context.supplier_name,
                supplier_normalized=storage_context.supplier_normalized,
                hersteller=storage_context.hersteller,
                kompatibilitaet=storage_context.kompatibilitaet,
                # Item Details
                quantity=storage_context.quantity,
                unit=storage_context.unit,
                description=storage_context.article_description,
                # Delivery Information
                delivery_date=storage_context.delivery_date,
                order_number=storage_context.order_number,
                employee_name=storage_context.employee_name,
                # Generation-spezifische Daten
                document_type=document_type,
                generation_timestamp=datetime.now(),
                template_version="1.0",
                # Metadaten
                context_source="storage_system",
                completeness_score=storage_context.completeness_score,
            )

            # Zusätzliche Daten integrieren
            if additional_data:
                generation_context.custom_data.update(additional_data)

            self.stats["contexts_built"] += 1
            self.stats["storage_integrations"] += 1

            logger.info(
                f"GenerationContext built from StorageContext"
                f" - Completeness: "
                f"{storage_context.completeness_score:.1%}"
            )

            return generation_context

        except Exception as e:
            error_msg = f"Error building context from storage: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def build_from_parameters(
        self,
        batch_number: str,
        delivery_number: str,
        document_type: DocumentType,
        article_number: str = "",
        supplier_name: str = "",
        quantity: int = 0,
        employee_name: str = "",
        additional_placeholders: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> GenerationContext:
        """
        Erstellt GenerationContext aus direkten Parametern.

        Args:
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            document_type: Document Type
            article_number: Artikelnummer (optional)
            supplier_name: Lieferantenname (optional)
            quantity: Menge (optional)
            employee_name: Mitarbeitername (optional)
            additional_placeholders: Zusätzliche Placeholder
            **kwargs: Weitere optionale Parameter

        Returns:
            GenerationContext
        """
        try:
            # Basis Context erstellen
            generation_context = GenerationContext(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=supplier_name,
                quantity=quantity,
                employee_name=employee_name,
                document_type=document_type,
                generation_timestamp=datetime.now(),
                context_source="parameters",
            )

            # Zusätzliche Parameter aus kwargs
            for key, value in kwargs.items():
                if hasattr(generation_context, key):
                    setattr(generation_context, key, value)
                else:
                    generation_context.custom_data[key] = value

            # Zusätzliche Placeholder
            if additional_placeholders:
                generation_context.placeholders.update(additional_placeholders)

            # Versuche Item-Daten aus Datenbank zu laden für Zertifikatsinformationen
            try:
                from warehouse.application.services.entity_services.item_service import (  # noqa: E501
                    ItemService,
                )

                item_service = ItemService()

                # Hole Item-Daten mit Zertifikaten
                item_data = item_service.get_item_by_composite_key(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                )

                if item_data:
                    logger.debug(
                        "Item data found, integrating "
                        "certificate and quantity information"
                    )

                    # Aktualisiere Context mit Item-Daten
                    if item_data.get("designation"):
                        generation_context.description = item_data["designation"]
                    if item_data.get("kompatibilitaet"):
                        generation_context.kompatibilitaet = item_data[
                            "kompatibilitaet"
                        ]
                    elif item_data.get("manufacturer"):  # Backward-Compat
                        generation_context.kompatibilitaet = item_data["manufacturer"]
                    if item_data.get("supplier_name"):
                        generation_context.supplier_name = item_data["supplier_name"]
                    # DB-Wert nur übernehmen wenn kein Parameter gesetzt ist
                    # Parameter hat immer Vorrang vor DB-Wert
                    if not generation_context.employee_name and item_data.get(
                        "employee_name"
                    ):
                        generation_context.employee_name = item_data["employee_name"]

                    # FIX: Hole supplier_id (Lieferantennummer) von Item-Daten
                    if item_data.get("supplier_id"):
                        generation_context.supplier_normalized = item_data["supplier_id"]

                    # Aktualisiere Bestellnummer aus Item-Daten
                    if item_data.get("order_number"):
                        generation_context.order_number = item_data["order_number"]

                    # Aktualisiere Mengen-Daten für PDB
                    # Verwende die beste verfügbare Menge
                    best_quantity = (
                        item_data.get("delivery_quantity")
                        or item_data.get("quantity")
                        or generation_context.quantity
                        or 0
                    )
                    generation_context.quantity = best_quantity

                    # Füge PDB-spezifische Daten hinzu (Mengen und Bestellnummer)
                    pdb_data = {
                        # Mengen-Platzhalter
                        "orderq": item_data.get("order_quantity")
                        or item_data.get("ordered_quantity")
                        or "-",  # FIXED: "-" statt 0
                        "deliveryq": item_data.get("delivery_quantity")
                        or item_data.get("quantity")
                        or "-",  # FIXED: "-" statt 0
                        "delivery_slip_quantity": item_data.get(
                            "delivery_slip_quantity"
                        )
                        or "-",  # FIXED: "-" statt 0
                        "LSQ": item_data.get("delivery_slip_quantity")
                        or "-",  # FIXED: "-" statt 0
                        # Alternative Namen für Kompatibilität
                        "order_quantity": item_data.get("order_quantity")
                        or item_data.get("ordered_quantity")
                        or "-",  # FIXED
                        "delivery_quantity": item_data.get("delivery_quantity")
                        or item_data.get("quantity")
                        or "-",  # FIXED
                        "ordered_quantity": item_data.get("ordered_quantity")
                        or "-",  # FIXED
                        # Bestellnummer-Platzhalter
                        "ordernr": item_data.get("order_number")
                        or "",  # PDB Template verwendet [[ordernr]]
                        "order_number": item_data.get("order_number")
                        or "",  # Vollständiger Name
                    }

                    generation_context.custom_data.update(pdb_data)
                    logger.info(
                        f"DEBUG PDB QUANTITIES - Raw "
                        f"item_data: ordered="
                        f"{item_data.get('ordered_quantity')}"
                        f", slip="
                        f"{item_data.get('delivery_slip_quantity')}"
                        f", delivered="
                        f"{item_data.get('delivered_quantity')}"
                    )
                    logger.info(
                        f"DEBUG PDB QUANTITIES - " f"Final pdb_data: {pdb_data}"
                    )

                    # Integriere Zertifikatsdaten in custom_data
                    certificates = item_data.get("certificates", {})
                    if certificates:
                        logger.debug(f"Integrating certificate data: {certificates}")

                        # Mappa Zertifikate zu Template-Platzhaltern
                        cert_mapping = {
                            # Positive Zertifikate (X wenn vorhanden)
                            "VP": "X"
                            if certificates.get("measurement_protocol")
                            else "",
                            "MZ": "X"
                            if certificates.get("material_certificate")
                            else "",
                            "MP": "X"
                            if certificates.get("measurement_protocol")
                            else "",
                            "B": "X" if certificates.get("coating_certificate") else "",
                            "HZ": "X"
                            if certificates.get("hardness_certificate")
                            else "",
                            "WZ": "X"
                            if certificates.get("additional_certificates")
                            else "",
                            "EDV": "X" if certificates.get("label_present") else "",
                            "BG": "X"
                            if certificates.get("accompanying_document")
                            else "",
                            # Negative Zertifikate (X wenn NICHT vorhanden)
                            "nVP": ""
                            if certificates.get("measurement_protocol")
                            else "X",
                            "nMZ": ""
                            if certificates.get("material_certificate")
                            else "X",
                            "nMP": ""
                            if certificates.get("measurement_protocol")
                            else "X",
                            "nB": ""
                            if certificates.get("coating_certificate")
                            else "X",
                            "nHZ": ""
                            if certificates.get("hardness_certificate")
                            else "X",
                            "nWZ": ""
                            if certificates.get("additional_certificates")
                            else "X",
                            "nEDV": "" if certificates.get("label_present") else "X",
                            "nBG": ""
                            if certificates.get("accompanying_document")
                            else "X",
                        }

                        generation_context.custom_data.update(cert_mapping)
                        logger.debug(
                            "Certificate placeholders " "integrated into context"
                        )

            except Exception as item_error:
                logger.warning(
                    f"Could not enhance context with Item data: {item_error}"
                )

            # FIX: Fallback - Hole supplier_id (Lieferantennummer) direkt von Delivery
            # (Falls Item-Daten keine supplier_id enthalten)
            if not generation_context.supplier_normalized and delivery_number:
                try:
                    from warehouse.application.services.entity_services.delivery_service import (  # noqa: E501
                        DeliveryService,
                    )

                    delivery_service = DeliveryService()
                    delivery_data = delivery_service.get_delivery(delivery_number)

                    if delivery_data and delivery_data.get("supplier_id"):
                        generation_context.supplier_normalized = delivery_data[
                            "supplier_id"
                        ]
                        logger.debug(
                            f"supplier_normalized loaded from Delivery: "
                            f"{generation_context.supplier_normalized}"
                        )
                except Exception as delivery_error:
                    logger.warning(
                        f"Could not load supplier_id from Delivery: {delivery_error}"
                    )

            # Versuche Storage System Integration für vollständigere Daten
            if STORAGE_SYSTEM_AVAILABLE and self.storage_context_service:
                try:
                    storage_context = (
                        self.storage_context_service.get_complete_storage_context(
                            batch_number=batch_number,
                            delivery_number=delivery_number,
                            article_number=article_number,
                            supplier_name=supplier_name,
                        )
                    )

                    # Merge mit Storage-Daten falls verfügbar
                    if (
                        storage_context.completeness_score
                        > generation_context.completeness_score
                    ):
                        # Parameter-Werte vor Merge sichern
                        # (haben Vorrang vor Storage-Werten)
                        original_employee_name = (
                            generation_context.employee_name if employee_name else None
                        )

                        generation_context = (
                            generation_context.merge_with_storage_context(
                                storage_context
                            )
                        )

                        # Parameter-Werte nach Merge wiederherstellen
                        if original_employee_name:
                            generation_context.employee_name = original_employee_name

                        logger.debug("Context enhanced with Storage System data")

                except Exception as storage_error:
                    logger.warning(
                        "Could not enhance context with "
                        f"Storage System: {storage_error}"
                    )

            # Berechne Completeness Score
            generation_context.completeness_score = self._calculate_completeness_score(
                generation_context
            )

            self.stats["contexts_built"] += 1

            logger.info(
                f"GenerationContext built from parameters"
                f" - Completeness: "
                f"{generation_context.completeness_score:.1%}"
            )

            return generation_context

        except Exception as e:
            error_msg = f"Error building context from parameters: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def build_from_warehouse_entities(
        self,
        item_entity: Optional[Any] = None,
        delivery_entity: Optional[Any] = None,
        order_entity: Optional[Any] = None,
        document_type: DocumentType = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> GenerationContext:
        """
        Erstellt GenerationContext aus Warehouse Domain Entities.

        Args:
            item_entity: Item Domain Entity (optional)
            delivery_entity: Delivery Domain Entity (optional)
            order_entity: Order Domain Entity (optional)
            document_type: Document Type
            additional_data: Zusätzliche Daten

        Returns:
            GenerationContext
        """
        try:
            # Extrahiere Daten aus Entities
            context_data = self._extract_data_from_entities(
                item_entity, delivery_entity, order_entity
            )

            # Erstelle Context mit extrahierten Daten
            generation_context = GenerationContext(
                batch_number=context_data.get("batch_number", ""),
                delivery_number=context_data.get("delivery_number", ""),
                article_number=context_data.get("article_number", ""),
                supplier_name=context_data.get("supplier_name", ""),
                quantity=context_data.get("quantity", 0),
                description=context_data.get("description", ""),
                document_type=document_type,
                generation_timestamp=datetime.now(),
                context_source="warehouse_entities",
            )

            # Zusätzliche Entity-Daten als custom_data
            generation_context.custom_data.update(context_data.get("custom_data", {}))

            # Zusätzliche Daten integrieren
            if additional_data:
                generation_context.custom_data.update(additional_data)

            # Completeness Score berechnen
            generation_context.completeness_score = self._calculate_completeness_score(
                generation_context
            )

            self.stats["contexts_built"] += 1

            logger.info(
                f"GenerationContext built from entities"
                f" - Completeness: "
                f"{generation_context.completeness_score:.1%}"
            )

            return generation_context

        except Exception as e:
            error_msg = f"Error building context from entities: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def enhance_context_for_document_type(
        self, context: GenerationContext, document_type: DocumentType
    ) -> GenerationContext:
        """
        Erweitert bestehenden Context für spezifischen Document Type.

        Args:
            context: Bestehender GenerationContext
            document_type: Ziel Document Type

        Returns:
            Erweiterter GenerationContext
        """
        try:
            # Template-Info für Document Type holen
            template_info = get_template_info(document_type)
            if not template_info:
                logger.warning(f"No template info found for {document_type.value}")
                return context

            # Context für Document Type anpassen
            enhanced_context = GenerationContext(
                # Kopiere alle bestehenden Daten
                **asdict(context),
                # Update Document Type
                document_type=document_type,
                template_version=template_info.version,
            )

            # Document-spezifische Placeholder hinzufügen
            document_placeholders = self._get_document_type_placeholders(
                document_type, enhanced_context
            )
            enhanced_context.placeholders.update(document_placeholders)

            # Validiere für Document Type
            validation_result = enhanced_context.validate_for_document_type(
                document_type
            )
            if not validation_result.is_valid:
                self.stats["validation_failures"] += 1
                logger.warning(
                    f"Context validation warnings for "
                    f"{document_type.value}: "
                    f"{validation_result.warnings}"
                )

                if validation_result.errors:
                    error_msg = f"Context validation failed: {validation_result.errors}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.debug(f"Context enhanced for {document_type.value}")

            return enhanced_context

        except Exception as e:
            error_msg = f"Error enhancing context for {document_type.value}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def validate_context_completeness(
        self, context: GenerationContext, required_completeness: float = 0.7
    ) -> Dict[str, Any]:
        """
        Validiert Context-Vollständigkeit für Document Generation.

        Args:
            context: Zu validierender Context
            required_completeness: Mindest-Vollständigkeit (0-1)

        Returns:
            Validierungsergebnis mit Details
        """
        try:
            validation_result = {
                "is_complete": context.completeness_score >= required_completeness,
                "completeness_score": context.completeness_score,
                "required_score": required_completeness,
                "missing_fields": [],
                "data_quality_issues": [],
                "recommendations": [],
            }

            # Pflicht-Felder prüfen
            required_fields = ["batch_number", "delivery_number"]
            for field in required_fields:
                value = getattr(context, field, None)
                if not value or (isinstance(value, str) and not value.strip()):
                    validation_result["missing_fields"].append(field)

            # Data Quality Issues identifizieren
            if not context.article_number:
                validation_result["data_quality_issues"].append(
                    "article_number missing"
                )

            if not context.supplier_name:
                validation_result["data_quality_issues"].append("supplier_name missing")

            if context.quantity <= 0:
                validation_result["data_quality_issues"].append(
                    "quantity not specified"
                )

            # Recommendations generieren
            if context.completeness_score < 0.5:
                validation_result["recommendations"].append(
                    "Consider using Storage System integration for better data quality"
                )

            if validation_result["missing_fields"]:
                missing = ", ".join(validation_result["missing_fields"])
                validation_result["recommendations"].append(
                    f"Required fields missing: {missing}"
                )

            # Statistics
            if not validation_result["is_complete"]:
                self.stats["data_quality_warnings"] += 1

            return validation_result

        except Exception as e:
            logger.error(f"Error validating context completeness: {e}")
            return {"is_complete": False, "error": str(e), "completeness_score": 0.0}

    def _extract_data_from_entities(
        self,
        item_entity: Optional[Any],
        delivery_entity: Optional[Any],
        order_entity: Optional[Any],
    ) -> Dict[str, Any]:
        """Extrahiert Daten aus Warehouse Domain Entities."""
        extracted_data = {
            "batch_number": "",
            "delivery_number": "",
            "article_number": "",
            "supplier_name": "",
            "quantity": 0,
            "description": "",
            "custom_data": {},
        }

        try:
            # Item Entity Daten
            if item_entity:
                if hasattr(item_entity, "batch_number"):
                    extracted_data["batch_number"] = str(item_entity.batch_number)
                if hasattr(item_entity, "article_number"):
                    extracted_data["article_number"] = str(item_entity.article_number)
                if hasattr(item_entity, "quantity"):
                    extracted_data["quantity"] = int(item_entity.quantity)
                if hasattr(item_entity, "description"):
                    extracted_data["description"] = str(item_entity.description)

                # Zusätzliche Item-Daten
                item_attrs = ["unit", "status", "location", "expiry_date"]
                for attr in item_attrs:
                    if hasattr(item_entity, attr):
                        extracted_data["custom_data"][attr] = getattr(item_entity, attr)

            # Delivery Entity Daten
            if delivery_entity:
                if hasattr(delivery_entity, "delivery_number"):
                    extracted_data["delivery_number"] = str(
                        delivery_entity.delivery_number
                    )
                if hasattr(delivery_entity, "supplier_name"):
                    extracted_data["supplier_name"] = str(delivery_entity.supplier_name)

                # Zusätzliche Delivery-Daten
                delivery_attrs = ["delivery_date", "order_number", "status"]
                for attr in delivery_attrs:
                    if hasattr(delivery_entity, attr):
                        extracted_data["custom_data"][attr] = getattr(
                            delivery_entity, attr
                        )

            # Order Entity Daten
            if order_entity:
                order_attrs = ["order_number", "order_date", "priority"]
                for attr in order_attrs:
                    if hasattr(order_entity, attr):
                        extracted_data["custom_data"][attr] = getattr(
                            order_entity, attr
                        )

        except Exception as e:
            logger.warning(f"Error extracting data from entities: {e}")

        return extracted_data

    def _calculate_completeness_score(self, context: GenerationContext) -> float:
        """Berechnet Completeness Score für GenerationContext."""
        try:
            # Pflicht-Felder (Gewichtung: 2x)
            required_fields = {
                "batch_number": 2,
                "delivery_number": 2,
                "article_number": 1,
                "supplier_name": 1,
                "quantity": 1,
                "description": 1,
                "employee_name": 1,
                "kompatibilitaet": 1,
                "unit": 1,
                "delivery_date": 1,
            }

            total_weight = sum(required_fields.values())
            current_weight = 0

            for field, weight in required_fields.items():
                value = getattr(context, field, None)
                if value and (not isinstance(value, str) or value.strip()):
                    if isinstance(value, int) and value > 0:
                        current_weight += weight
                    elif not isinstance(value, int):
                        current_weight += weight

            # Basis Score
            score = current_weight / total_weight

            # Bonus für zusätzliche Daten
            if context.custom_data:
                score += 0.05  # 5% Bonus
            if context.placeholders:
                score += 0.05  # 5% Bonus

            return min(1.0, score)  # Cap at 1.0

        except Exception as e:
            logger.error(f"Error calculating completeness score: {e}")
            return 0.5  # Default fallback

    def _get_document_type_placeholders(
        self, document_type: DocumentType, context: GenerationContext
    ) -> Dict[str, str]:
        """Generiert Document-Type spezifische Placeholder."""
        placeholders = {}

        try:
            # Import hier um Circular Import zu vermeiden
            from .document_types import DocumentType as DT

            # Document-spezifische Placeholder Logic
            if document_type == DT.PDB:
                placeholders.update(
                    {"document_title": "Produktdatenblatt", "document_code": "Fo00040"}
                )
            elif document_type == DT.BEGLEITSCHEIN:
                placeholders.update(
                    {"document_title": "Begleitschein", "document_code": "Fo00057"}
                )
            elif document_type == DT.SICHTKONTROLLE:
                placeholders.update(
                    {"document_title": "Sichtkontrolle", "document_code": "Fo00141"}
                )

            # Allgemeine Metadaten
            placeholders.update(
                {
                    "generation_date": context.generation_timestamp.strftime(
                        "%d.%m.%Y"
                    ),
                    "generation_time": context.generation_timestamp.strftime(
                        "%H:%M:%S"
                    ),
                    "document_type": document_type.value,
                    "template_version": context.template_version,
                }
            )

        except Exception as e:
            logger.warning(f"Error generating document type placeholders: {e}")

        return placeholders

    def build_generation_context(
        self,
        document_type: DocumentType,
        batch_number: str,
        delivery_number: str,
        article_number: str = "",
        supplier_name: str = "",
        quantity: int = 0,
        employee_name: str = "",
        **kwargs,
    ) -> GenerationContext:
        """
        Wrapper-Methode für build_from_parameters - für Kompatibilität.

        Args:
            document_type: Document Type für Generation
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            article_number: Artikelnummer (optional)
            supplier_name: Lieferantenname (optional)
            quantity: Menge (optional)
            employee_name: Mitarbeitername (optional)
            **kwargs: Weitere Parameter

        Returns:
            GenerationContext
        """
        return self.build_from_parameters(
            batch_number=batch_number,
            delivery_number=delivery_number,
            document_type=document_type,
            article_number=article_number,
            supplier_name=supplier_name,
            quantity=quantity,
            employee_name=employee_name,
            **kwargs,
        )

    def get_builder_statistics(self) -> Dict[str, Any]:
        """Gibt Context Builder Statistiken zurück."""
        return {
            "contexts_built": self.stats["contexts_built"],
            "storage_integrations": self.stats["storage_integrations"],
            "validation_failures": self.stats["validation_failures"],
            "data_quality_warnings": self.stats["data_quality_warnings"],
            "storage_system_available": STORAGE_SYSTEM_AVAILABLE,
            "storage_service_initialized": self.storage_context_service is not None,
        }

    def reset_statistics(self):
        """Setzt Statistiken zurück."""
        for key in self.stats:
            self.stats[key] = 0
        logger.info("ContextBuilder statistics reset")


# Convenience Functions für einfache Context-Erstellung


def create_context_from_storage(
    storage_context: "StorageContextData",
    document_type: DocumentType,
    additional_data: Optional[Dict[str, Any]] = None,
) -> GenerationContext:
    """
    Convenience Function: Erstellt Context aus StorageContextData.

    Args:
        storage_context: Phase 1 StorageContextData
        document_type: Document Type
        additional_data: Zusätzliche Daten

    Returns:
        GenerationContext
    """
    builder = ContextBuilder()
    return builder.build_from_storage_context(
        storage_context, document_type, additional_data
    )


def create_context_from_parameters(
    batch_number: str, delivery_number: str, document_type: DocumentType, **kwargs
) -> GenerationContext:
    """
    Convenience Function: Erstellt Context aus Parametern.

    Args:
        batch_number: Chargennummer
        delivery_number: Lieferscheinnummer
        document_type: Document Type
        **kwargs: Weitere Parameter

    Returns:
        GenerationContext
    """
    builder = ContextBuilder()
    return builder.build_from_parameters(
        batch_number=batch_number,
        delivery_number=delivery_number,
        document_type=document_type,
        **kwargs,
    )


def validate_context_quality(
    context: GenerationContext, required_completeness: float = 0.7
) -> Dict[str, Any]:
    """
    Convenience Function: Validiert Context Qualität.

    Args:
        context: Zu validierender Context
        required_completeness: Mindest-Vollständigkeit

    Returns:
        Validierungsergebnis
    """
    builder = ContextBuilder()
    return builder.validate_context_completeness(context, required_completeness)
