# src/warehouse/domain/exceptions/base.py


class BaseDomainException(Exception):
    """Basis-Exception für alle Domain-spezifischen Fehler."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
