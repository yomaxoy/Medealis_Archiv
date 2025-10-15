"""
# src/warehouse/domain/exceptions/order_exceptions.py
"""

from warehouse.domain.exceptions.base_exceptions import BaseDomainException


class OrderNotFoundException(BaseDomainException):
    """Order wurde nicht gefunden."""

    def __init__(self, order_number: str):
        message = f"Order {order_number} nicht gefunden"
        super().__init__(message)


class OrderAlreadyExistsException(BaseDomainException):
    """Order existiert bereits."""

    def __init__(self, order_number: str):
        message = f"Order {order_number} existiert bereits"
        super().__init__(message)


class OrderAlreadyCompletedException(BaseDomainException):
    """Order ist bereits abgeschlossen."""

    def __init__(self, order_number: str):
        message = f"Order {order_number} ist bereits abgeschlossen"
        super().__init__(message)


class OrderNotCompletedException(BaseDomainException):
    """Order ist nicht abgeschlossen."""

    def __init__(self, order_number: str):
        message = f"Order {order_number} ist nicht abgeschlossen"
        super().__init__(message)


class EmptyOrderException(BaseDomainException):
    """Order enthält keine Artikel."""

    def __init__(self, order_number: str):
        message = f"Order {order_number} enthält keine Artikel"
        super().__init__(message)


class OrderItemAlreadyExistsException(BaseDomainException):
    """OrderItem existiert bereits."""

    def __init__(self, order_number: str, article_number: str):
        message = f"Artikel {article_number} ist bereits in Order {order_number} enthalten"
        super().__init__(message)


class OrderItemNotFoundException(BaseDomainException):
    """OrderItem wurde nicht gefunden."""

    def __init__(self, order_number: str, article_number: str):
        message = f"Artikel {article_number} wurde in Order {order_number} nicht gefunden"
        super().__init__(message)


class OrderValidationException(BaseDomainException):
    """Order-Validierung fehlgeschlagen."""

    def __init__(self, message: str):
        super().__init__(f"Order-Validierung fehlgeschlagen: {message}")