# src/warehouse/infrastructure/database/mappers/order_mapper.py

"""
Order Mapper - Domain Objects Implementation.
Schlanke Implementierung für Order Entity ↔ OrderModel Mapping.
"""

from datetime import datetime, date
from typing import Optional, List

from warehouse.domain.entities.order import Order, OrderItem
from warehouse.infrastructure.database.models.order_model import (
    OrderModel,
    OrderItemModel,
)
from .base_mapper import BaseMapper


class OrderMapper(BaseMapper):
    """Mapper zwischen Order Domain Entity und OrderModel."""

    def to_domain(self, model: OrderModel) -> Order:
        """Konvertiert OrderModel zu Order Domain Entity."""
        try:
            # Order Entity erstellen
            order = Order(
                order_number=model.order_number,
                supplier_id=model.supplier_id,
                order_date=model.order_date,
                employee_name=model.employee_name,
                expected_delivery_date=model.expected_delivery_date,
            )

            # Status und Metadaten
            order.notes = model.notes or ""
            order.created_at = model.created_at or datetime.now()
            order.updated_at = model.updated_at or datetime.now()

            # Completion Status
            if model.status == "Abgeschlossen":
                order.is_completed = True
                # completed_at wird in der Order Entity automatisch gesetzt

            # Order Items laden (falls vorhanden)
            if hasattr(model, "order_items") and model.order_items:
                order.order_items = self._convert_order_items_to_domain(
                    model.order_items
                )

            return order

        except Exception as e:
            print(f"Warning: Error in order to_domain mapping: {e}")
            # Fallback
            return self._create_fallback_order(model)

    def to_model(self, entity: Order) -> OrderModel:
        """Konvertiert Order Entity zu OrderModel."""
        model = OrderModel(
            order_number=entity.order_number,
            supplier_id=entity.supplier_id,
            order_date=entity.order_date,
            employee_name=entity.employee_name,
            expected_delivery_date=entity.expected_delivery_date,
            status="Abgeschlossen" if entity.is_completed else "Offen",
            notes=entity.notes or "",
        )

        return model

    def update_model(self, model: OrderModel, entity: Order) -> None:
        """Aktualisiert OrderModel mit Entity-Daten."""
        model.supplier_id = entity.supplier_id
        model.order_date = entity.order_date
        model.employee_name = entity.employee_name
        model.expected_delivery_date = entity.expected_delivery_date
        model.status = "Abgeschlossen" if entity.is_completed else "Offen"
        model.notes = entity.notes or ""

    def _convert_order_items_to_domain(
        self, order_item_models: List[OrderItemModel]
    ) -> List[OrderItem]:
        """Konvertiert OrderItemModels zu OrderItem Domain Objects."""
        order_items = []

        for item_model in order_item_models:
            try:
                order_item = OrderItem(
                    article_number=item_model.article_number,
                    ordered_quantity=item_model.ordered_quantity,
                    expected_delivery_date=None,  # Wird vom Order übernommen
                    unit_description=item_model.unit_description,
                    notes=item_model.notes,
                )
                order_items.append(order_item)
            except Exception as e:
                print(f"Warning: Could not convert OrderItem {item_model.id}: {e}")
                continue

        return order_items

    def _create_fallback_order(self, model: OrderModel) -> Order:
        """Erstellt Fallback-Order bei Mapping-Fehlern."""
        try:
            return Order(
                order_number=model.order_number or "ORD000",
                supplier_id=model.supplier_id or "UNKNOWN",
                order_date=model.order_date or date.today(),
                employee_name=model.employee_name or "Unknown",
                expected_delivery_date=model.expected_delivery_date,
            )
        except Exception:
            raise ValueError(f"Kritischer Order-Mapping-Fehler für Model: {model}")


class OrderItemMapper:
    """Separate Mapper für OrderItem Domain Objects."""

    def to_domain(self, model: OrderItemModel) -> OrderItem:
        """Konvertiert OrderItemModel zu OrderItem Domain Object."""
        return OrderItem(
            article_number=model.article_number,
            ordered_quantity=model.ordered_quantity,
            expected_delivery_date=None,  # Wird vom Parent Order übernommen
            unit_description=model.unit_description,
            notes=model.notes,
        )

    def to_model(self, entity: OrderItem, order_number: str) -> OrderItemModel:
        """Konvertiert OrderItem zu OrderItemModel."""
        return OrderItemModel(
            order_number=order_number,
            article_number=entity.article_number,
            ordered_quantity=entity.ordered_quantity,
            unit_description=entity.unit_description,
            notes=entity.notes,
        )
