# src/warehouse/domain/value_objects/article_number.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleNumber:
    """5-stellige Artikelnummer (z.B. A0001, B0002, CT003)."""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Artikelnummer darf nicht leer sein")

        if len(self.value) != 5:
            if len(self.value) != 6:
                raise ValueError("Artikelnummer muss genau 5 oder 6 Zeichen lang sein")

        # Erstes Zeichen muss Buchstabe sein, Rest alphanumerisch
        if not self.value[0].isalpha():
            raise ValueError("Artikelnummer muss mit Buchstaben beginnen")

        if not self.value.isalnum():
            raise ValueError("Artikelnummer darf nur Buchstaben und Zahlen enthalten")

    def __str__(self) -> str:
        return self.value
