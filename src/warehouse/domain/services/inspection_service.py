# src/warehouse/domain/services/inspection_service.py

"""
Inspection Service für das Warehouse Management System.

Kapselt die Geschäftslogik für Warenprüfungen und Qualitätskontrolle.
Koordiniert Item-Prüfungen und stellt Analysefunktionen bereit.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

from warehouse.domain.entities.item import Item, InspectionResult
from warehouse.domain.enums.item_status import ItemStatus

# from warehouse.domain.enums.priority_level import PriorityLevel
from warehouse.domain.exceptions.item_exceptions import ItemNotEditableException
from warehouse.domain.exceptions.validation_exceptions import ValidationException


class InspectionService:
    """
    Domain Service für Artikel-Prüfungen und Qualitätskontrolle.

    Koordiniert Prüfworkflows und stellt Analysefunktionen für
    Ausschuss-Statistiken und Prioritätsverwaltung bereit.
    """

    def perform_visual_inspection(
        self,
        item: Item,
        inspector_name: str,
        waste_quantity: int = 0,
        waste_reason: Optional[str] = None,
        quality_notes: Optional[str] = None,
        measurements: Optional[Dict[str, Any]] = None,
    ) -> InspectionResult:
        """
        Führt eine Sichtprüfung durch und erstellt Prüfungsergebnis.

        Args:
            item: Zu prüfender Artikel
            inspector_name: Name des Prüfers
            waste_quantity: Ausschussmenge
            waste_reason: Grund für Ausschuss
            quality_notes: Qualitätsnotizen
            measurements: Optionale Messwerte

        Returns:
            InspectionResult mit Prüfungsergebnis

        Raises:
            ItemNotEditableException: Item kann nicht bearbeitet werden
            ValidationException: Ungültige Prüfparameter
        """
        self._validate_item_for_inspection(item)
        self._validate_inspection_parameters(item, waste_quantity, waste_reason)

        # Erstelle Prüfungsergebnis
        inspection_result = InspectionResult(
            performed_at=datetime.now(),
            performed_by=inspector_name,
            waste_quantity=waste_quantity,
            waste_reason=waste_reason,
            quality_notes=quality_notes,
            measurements=measurements or {},
            passed=waste_quantity == 0,  # Einfache Logik: 0 Ausschuss = bestanden
        )

        # Führe Prüfung am Item durch
        item.complete_visual_inspection(inspection_result)

        return inspection_result

    def calculate_waste_statistics(self, items: List[Item]) -> Dict[str, Any]:
        """
        Berechnet Ausschuss-Statistiken für eine Liste von Artikeln.

        Args:
            items: Liste der zu analysierenden Artikel

        Returns:
            Dictionary mit detaillierten Ausschuss-Statistiken
        """
        total_items = len(items)
        items_with_waste = 0
        total_quantity = 0
        total_waste = 0
        waste_by_reason: Dict[str, Dict[str, Any]] = {}
        waste_by_supplier: Dict[str, Dict[str, Any]] = {}
        waste_by_article: Dict[str, Dict[str, Any]] = {}

        for item in items:
            total_quantity += item.delivered_quantity

            if item.inspection_result and item.inspection_result.waste_quantity > 0:
                items_with_waste += 1
                waste_quantity = item.inspection_result.waste_quantity
                total_waste += waste_quantity

                # Gruppiere nach Ausschussgrund
                reason = item.inspection_result.waste_reason or "Unbekannt"
                if reason not in waste_by_reason:
                    waste_by_reason[reason] = {"count": 0, "total_waste": 0}
                waste_by_reason[reason]["count"] += 1
                waste_by_reason[reason]["total_waste"] += waste_quantity

                # Gruppiere nach Lieferant
                supplier = item.supplier_id
                if supplier not in waste_by_supplier:
                    waste_by_supplier[supplier] = {
                        "count": 0,
                        "total_waste": 0,
                        "total_quantity": 0,
                    }
                waste_by_supplier[supplier]["count"] += 1
                waste_by_supplier[supplier]["total_waste"] += waste_quantity
                waste_by_supplier[supplier]["total_quantity"] += item.delivered_quantity

                # Gruppiere nach Artikelnummer
                article_key = str(item.article_number)
                if article_key not in waste_by_article:
                    waste_by_article[article_key] = {
                        "count": 0,
                        "total_waste": 0,
                        "total_quantity": 0,
                    }
                waste_by_article[article_key]["count"] += 1
                waste_by_article[article_key]["total_waste"] += waste_quantity
                waste_by_article[article_key]["total_quantity"] += item.delivered_quantity
            else:
                # Auch Items ohne Ausschuss für Supplier/Article Statistiken erfassen
                supplier = item.supplier_id
                if supplier not in waste_by_supplier:
                    waste_by_supplier[supplier] = {
                        "count": 0,
                        "total_waste": 0,
                        "total_quantity": 0,
                    }
                waste_by_supplier[supplier]["total_quantity"] += item.delivered_quantity

                article_key = str(item.article_number)
                if article_key not in waste_by_article:
                    waste_by_article[article_key] = {
                        "count": 0,
                        "total_waste": 0,
                        "total_quantity": 0,
                    }
                waste_by_article[article_key]["total_quantity"] += item.delivered_quantity

        # Berechne Prozentsätze
        overall_waste_percentage = (
            Decimal(total_waste) / Decimal(total_quantity) * Decimal("100")
            if total_quantity > 0
            else Decimal("0")
        )

        items_with_waste_percentage = (
            (items_with_waste / total_items) * 100 if total_items > 0 else 0
        )

        # Berechne Ausschussquoten pro Lieferant
        for supplier_data in waste_by_supplier.values():
            if supplier_data["total_quantity"] > 0:
                supplier_data["waste_percentage"] = float(
                    Decimal(supplier_data["total_waste"])
                    / Decimal(supplier_data["total_quantity"])
                    * Decimal("100")
                )
            else:
                supplier_data["waste_percentage"] = 0.0

        # Berechne Ausschussquoten pro Artikel
        for article_data in waste_by_article.values():
            if article_data["total_quantity"] > 0:
                article_data["waste_percentage"] = float(
                    Decimal(article_data["total_waste"])
                    / Decimal(article_data["total_quantity"])
                    * Decimal("100")
                )
            else:
                article_data["waste_percentage"] = 0.0

        return {
            "summary": {
                "total_items": total_items,
                "items_with_waste": items_with_waste,
                "items_with_waste_percentage": items_with_waste_percentage,
                "total_quantity": total_quantity,
                "total_waste": total_waste,
                "overall_waste_percentage": float(overall_waste_percentage),
            },
            "waste_by_reason": waste_by_reason,
            "waste_by_supplier": waste_by_supplier,
            "waste_by_article": waste_by_article,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def recommend_inspection_priority(self, items: List[Item]) -> List[Dict[str, Any]]:
        """
        Empfiehlt Prüfungs-Prioritäten basierend auf Priority Level.

        Args:
            items: Liste der zu priorisierenden Artikel

        Returns:
            Nach Priorität sortierte Liste mit Empfehlungen
        """
        prioritized_items = []

        for item in items:
            # Überspringe finale Items
            if item.is_final_status():
                continue

            # Erstelle Priority-Eintrag
            priority_item = {
                "item": item,
                "article_number": str(item.article_number),
                "batch_number": str(item.batch_number),
                "delivery_number": item.delivery_number,
                "supplier_id": item.supplier_id,
                "current_status": item.get_current_status().value,
                "priority_level": item.priority_level.value,
                "priority_numeric": item.priority_level.numeric_value,
                "priority_color": item.priority_level.get_display_color(),
                "quantity": item.delivered_quantity,  # Backward compatibility
                "delivered_quantity": item.delivered_quantity,
                "completion_percentage": item.get_completion_percentage(),
                "days_since_creation": (datetime.now() - item.created_at).days,
                "recommended_action": self._get_next_recommended_action(item),
            }

            prioritized_items.append(priority_item)

        # Sortiere nach Priority Level (höchste Priorität zuerst)
        # Bei gleicher Priorität: ältere Items zuerst
        prioritized_items.sort(
            key=lambda x: (x["priority_numeric"], x["days_since_creation"]),
            reverse=True,
        )

        return prioritized_items

    # === PRIVATE HELPER METHODS ===

    def _validate_item_for_inspection(self, item: Item) -> None:
        """Validiert, ob Item für Prüfung geeignet ist."""
        if item.is_final_status():
            raise ItemNotEditableException(item.get_current_status().value)

        if not item.is_step_completed(ItemStatus.DATEN_GEPRUEFT):
            raise ValidationException(
                "inspection", "Datenprüfung muss vor Sichtprüfung abgeschlossen werden"
            )

    def _validate_inspection_parameters(
        self, item: Item, waste_quantity: int, waste_reason: Optional[str]
    ) -> None:
        """Validiert Prüfungsparameter."""
        if waste_quantity < 0:
            raise ValidationException(
                "waste_quantity", "Ausschussmenge kann nicht negativ sein"
            )

        if waste_quantity > item.delivered_quantity:
            raise ValidationException(
                "waste_quantity",
                f"Ausschussmenge ({waste_quantity}) kann nicht größer als Gesamtmenge ({item.delivered_quantity}) sein",
            )

        if waste_quantity > 0 and not waste_reason:
            raise ValidationException(
                "waste_reason", "Ausschussgrund ist erforderlich bei Ausschussmenge > 0"
            )

    def _get_next_recommended_action(self, item: Item) -> str:
        """Empfiehlt nächste Aktion basierend auf Item-Status (IST-Zustand)."""
        current_status = item.get_current_status()

        # Mapping: IST-Zustand → Nächste SOLL-Aktion
        action_mapping = {
            ItemStatus.ARTIKEL_ANGELEGT: "Datenprüfung durchführen",
            ItemStatus.DATEN_GEPRUEFT: "Dokumentenprüfung durchführen",
            ItemStatus.DOKUMENTE_GEPRUEFT: "Vermessung durchführen",
            ItemStatus.VERMESSEN: "Sichtkontrolle durchführen",
            ItemStatus.SICHTKONTROLLE_DURCHGEFUEHRT: "Dokumente zusammenführen",
            ItemStatus.DOKUMENTE_ZUSAMMENGEFUEHRT: "Waren einlagern",
            ItemStatus.WAREN_EINGELAGERT: "Keine Aktion erforderlich (abgeschlossen)",
            ItemStatus.AUSSCHUSS: "Keine Aktion erforderlich (Ausschuss)",
        }

        return action_mapping.get(current_status, "Keine Aktion erforderlich")
