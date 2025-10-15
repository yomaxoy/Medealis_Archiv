"""
# src/warehouse/domain/exceptions/item_exceptions.py
"""

from warehouse.domain.exceptions.base_exceptions import BaseDomainException


class ItemNotFoundException(BaseDomainException):
    """Artikel wurde nicht gefunden."""

    def __init__(self, article_number: str, batch_number: str, delivery_number: str = None):
        if delivery_number:
            message = f"Artikel {article_number} mit Charge {batch_number} in Lieferung {delivery_number} nicht gefunden"
        else:
            message = f"Artikel {article_number} mit Charge {batch_number} nicht gefunden"
        super().__init__(message)


class InvalidStatusTransitionException(BaseDomainException):
    """Ungültiger Statusübergang."""

    def __init__(self, current_status: str, target_status: str):
        message = (
            f"Ungültiger Statusübergang von '{current_status}' zu '{target_status}'"
        )
        super().__init__(message)


class ItemAlreadyExistsException(BaseDomainException):
    """Artikel existiert bereits."""

    def __init__(self, article_number: str, batch_number: str):
        message = (
            f"Artikel {article_number} mit Charge {batch_number} existiert bereits"
        )
        super().__init__(message)


class ItemNotEditableException(BaseDomainException):
    """Artikel kann in diesem Status nicht bearbeitet werden."""

    def __init__(self, status: str):
        message = f"Artikel kann im Status '{status}' nicht bearbeitet werden"
        super().__init__(message)
