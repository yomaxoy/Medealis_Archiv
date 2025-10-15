# src/warehouse/domain/value_objects/article_number.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleNumber:
    """Artikelnummer (z.B. A0001, B0002, CT003, NE0001_SI00151)."""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Artikelnummer darf nicht leer sein")

        # Längenvalidierung entfernt - Artikelnummern können unterschiedliche Längen haben

        # Erstes Zeichen muss Buchstabe sein, Rest alphanumerisch oder Unterstrich
        if not self.value[0].isalpha():
            raise ValueError("Artikelnummer muss mit Buchstaben beginnen")

        # Erlaubte Zeichen: Buchstaben, Zahlen, Unterstriche und Bindestriche
        if not all(c.isalnum() or c in '_-' for c in self.value):
            raise ValueError("Artikelnummer darf nur Buchstaben, Zahlen, Unterstriche und Bindestriche enthalten")

    def __str__(self) -> str:
        return self.value
