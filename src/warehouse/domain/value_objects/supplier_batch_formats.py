# src/warehouse/domain/value_objects/supplier_batch_formats.py

"""
Zentrale Registry für lieferanten-spezifische Chargennummern-Formate.

Einzige Quelle der Wahrheit für alle Lieferanten-Patterns.
Neue Lieferanten hier eintragen; keine weiteren Code-Änderungen nötig.
"""

from typing import Optional

# Regex-Patterns pro Lieferant (Schlüssel: Lieferanten-ID in Großbuchstaben)
SUPPLIER_BATCH_FORMATS: dict[str, str] = {
    # Primec: P-XXXXXXXXXXXX-XXXX oder P-XXXXXXXXXXXX-XXXXX
    "PRIMEC": r"^P-\d{12}(-\d{4,5})?$",
    # Terrats Medical: genau 6 Ziffern
    "TERRATS": r"^\d{6}$",
    # Fleima: 2 Ziffern + "FL" + 6-8 Ziffern (z.B. 26FL007400, 25FL4901200)
    "FLEIMA": r"^\d{2}FL\d{6,8}$",
}


def get_pattern(supplier_id: Optional[str]) -> Optional[str]:
    """
    Gibt das Regex-Pattern für einen Lieferanten zurück.

    Args:
        supplier_id: Lieferanten-ID (case-insensitive)

    Returns:
        Regex-Pattern oder None wenn kein spezifisches Pattern definiert ist
        (in diesem Fall greift die generische Validierung)
    """
    if not supplier_id:
        return None
    return SUPPLIER_BATCH_FORMATS.get(supplier_id.upper())


def get_format_description(supplier_id: Optional[str]) -> str:
    """
    Gibt eine lesbare Beschreibung des erwarteten Formats zurück.

    Args:
        supplier_id: Lieferanten-ID

    Returns:
        Formatbeschreibung für Fehlermeldungen
    """
    descriptions: dict[str, str] = {
        "PRIMEC": "P-XXXXXXXXXXXX-XXXX oder P-XXXXXXXXXXXX-XXXXX",
        "TERRATS": "genau 6 Ziffern (z.B. 123456)",
        "FLEIMA": "2 Ziffern + FL + 6-8 Ziffern (z.B. 26FL007400)",
    }
    if not supplier_id:
        return "alphanumerisch"
    return descriptions.get(supplier_id.upper(), f"spezifisches Format für {supplier_id}")
