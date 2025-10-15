"""
# src/warehouse/domain/exceptions/supplier_exceptions.py
"""

from warehouse.domain.exceptions.base_exceptions import BaseDomainException


class SupplierNotFoundException(BaseDomainException):
    """Supplier wurde nicht gefunden."""

    def __init__(self, supplier_id: str):
        message = f"Supplier {supplier_id} nicht gefunden"
        super().__init__(message)


class SupplierAlreadyExistsException(BaseDomainException):
    """Supplier existiert bereits."""

    def __init__(self, supplier_id: str):
        message = f"Supplier {supplier_id} existiert bereits"
        super().__init__(message)


class SupplierNameNotUniqueException(BaseDomainException):
    """Supplier-Name ist nicht einzigartig."""

    def __init__(self, name: str):
        message = f"Supplier-Name '{name}' ist bereits vergeben"
        super().__init__(message)


class SupplierValidationException(BaseDomainException):
    """Supplier-Validierung fehlgeschlagen."""

    def __init__(self, message: str):
        super().__init__(f"Supplier-Validierung fehlgeschlagen: {message}")