# src/warehouse/domain/exceptions/delivery_exceptions.py

from warehouse.domain.exceptions.base_exceptions import BaseDomainException


class DeliveryNotFoundException(BaseDomainException):
    """Lieferung wurde nicht gefunden."""

    def __init__(self, delivery_number: str):
        message = f"Lieferung {delivery_number} nicht gefunden"
        super().__init__(message)


class DeliveryAlreadyCompletedException(BaseDomainException):
    """Lieferung ist bereits abgeschlossen."""

    def __init__(self, delivery_number: str):
        message = f"Lieferung {delivery_number} ist bereits abgeschlossen"
        super().__init__(message)


class DeliveryAlreadyExistsException(BaseDomainException):
    """Lieferung existiert bereits."""

    def __init__(self, delivery_number: str):
        message = f"Lieferung {delivery_number} existiert bereits"
        super().__init__(message)


class EmptyDeliveryException(BaseDomainException):
    """Lieferung enthält keine Artikel."""

    def __init__(self, delivery_number: str):
        message = f"Lieferung {delivery_number} enthält keine Artikel"
        super().__init__(message)
