# src/warehouse/infrastructure/database/repositories/__init__.py

"""
Database Repositories Package.
Exportiert alle Repository-Implementierungen.
"""

# REMOVED: Legacy dictionary-based repositories
# from .sql_item_repository import SQLItemRepository
# from .sql_delivery_repository import SQLDeliveryRepository
# from .sql_supplier_repository import SQLSupplierRepository
# from .sql_order_repository import SQLOrderRepository

# Domain-based repositories (new standard)
from .sql_item_rep_domain import SQLAlchemyItemRepositoryDomain
from .sql_delivery_rep_domain import SQLAlchemyDeliveryRepositoryDomain
from .sql_supplier_rep_domain import SQLAlchemySupplierRepositoryDomain
from .sql_order_rep_domain import SQLAlchemyOrderRepositoryDomain

__all__ = [
    # "SQLItemRepository",  # REMOVED - use SQLAlchemyItemRepositoryDomain
    # "SQLDeliveryRepository",  # REMOVED - use SQLAlchemyDeliveryRepositoryDomain
    # "SQLSupplierRepository",  # REMOVED - use SQLAlchemySupplierRepositoryDomain
    # "SQLOrderRepository",  # REMOVED - use SQLAlchemyOrderRepositoryDomain
    "SQLAlchemyItemRepositoryDomain",
    "SQLAlchemyDeliveryRepositoryDomain",
    "SQLAlchemySupplierRepositoryDomain",
    "SQLAlchemyOrderRepositoryDomain",
]
