# src/warehouse/infrastructure/database/models/__init__.py

"""
Database Models Package.
WICHTIG: Alle Models müssen hier importiert werden,
damit SQLAlchemy sie bei create_tables() registriert!
"""

from .base_model import BaseModel
from .item_model import ItemInfoModel, ItemModel
from .item_workflow_steps_model import ItemWorkflowStepsModel
from .delivery_model import DeliveryModel
from .supplier_model import SupplierModel
from .order_model import OrderModel, OrderItemModel

# Diese Imports registrieren die Models bei SQLAlchemy Base
__all__ = [
    "BaseModel",
    "ItemInfoModel",
    "ItemModel",
    "ItemWorkflowStepsModel",
    "DeliveryModel",
    "SupplierModel",
    "OrderModel",
    "OrderItemModel",
]
