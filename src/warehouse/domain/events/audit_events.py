"""
Domain Events für Audit Logging.

Definiert Ereignisse die im System geloggt werden sollen.
Clean Architecture: Domain Layer - keine Abhängigkeiten nach außen.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class AuditAction(Enum):
    """
    Definierte Aktionen im System.

    Naming Convention: ENTITY_ACTION
    """

    # Lieferschein
    DELIVERY_SCANNED = "Lieferschein gescannt"
    DELIVERY_CONFIRMED = "Lieferschein bestätigt"
    DELIVERY_DELETED = "Lieferschein gelöscht"

    # ItemInfo (Stammdaten)
    ITEMINFO_CREATED = "ItemInfo erstellt"
    ITEMINFO_UPDATED = "ItemInfo aktualisiert"
    ITEMINFO_QR_UPLOADED = "QR-Code hochgeladen"
    ITEMINFO_QR_DELETED = "QR-Code gelöscht"

    # Workflow Steps
    DATA_CONFIRMED = "Daten bestätigt"
    DOCUMENTS_CHECKED = "Dokumente geprüft"
    MEASUREMENT_DONE = "Vermessen"
    VISUAL_INSPECTION_DONE = "Sichtkontrolle durchgeführt"
    DOCUMENTS_MERGED = "Dokumente zusammengeführt"
    ITEM_COMPLETED = "Artikel abgeschlossen"
    ITEM_REJECTED = "Artikel ausgeschossen"

    # Bestellungen
    ORDER_CREATED = "Bestellung erstellt"
    ORDER_UPDATED = "Bestellung aktualisiert"
    ORDER_DELETED = "Bestellung gelöscht"

    # Labels & Dokumente
    LABEL_GENERATED = "Label generiert"
    LABEL_PRINTED = "Label gedruckt"
    DOCUMENT_GENERATED = "Dokument generiert"
    DOCUMENT_MERGED = "Dokumente zusammengeführt"

    # Benutzerverwaltung
    USER_CREATED = "Benutzer erstellt"
    USER_ROLE_CHANGED = "Benutzerrolle geändert"
    USER_PASSWORD_RESET = "Passwort zurückgesetzt"
    USER_ACTIVATED = "Benutzer aktiviert"
    USER_DEACTIVATED = "Benutzer deaktiviert"
    USER_PASSWORD_CHANGED = "Passwort geändert"

    # System
    LOGIN = "Benutzer angemeldet"
    LOGOUT = "Benutzer abgemeldet"
    SYSTEM_ERROR = "Systemfehler"


@dataclass
class AuditEvent:
    """
    Ein einzelnes Audit-Ereignis.

    Wird von Application Services erstellt und an AuditService übergeben.
    Immutable nach Erstellung.

    Attributes:
        action: Art der Aktion (aus AuditAction Enum)
        user: Benutzername des Handelnden
        timestamp: Zeitpunkt der Aktion
        entity_type: Typ der betroffenen Entity ("Delivery", "Item", "Order", etc.)
        entity_id: Eindeutige ID der Entity (Primary Key oder Composite Key)
        data: Zusätzliche strukturierte Daten (wird als JSONB gespeichert)
        notes: Optionale Freitext-Notizen
    """

    action: AuditAction
    user: str
    timestamp: datetime
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    notes: Optional[str] = None

    def __post_init__(self):
        """Validierung nach Erstellung."""
        if not self.user or not self.user.strip():
            raise ValueError("User darf nicht leer sein")

        if not self.entity_type or not self.entity_type.strip():
            raise ValueError("Entity type darf nicht leer sein")

        if not self.entity_id or not self.entity_id.strip():
            raise ValueError("Entity ID darf nicht leer sein")

    def format_log_line(self) -> str:
        """
        Formatiert Event als menschenlesbare Log-Zeile.

        Format: Date - Time - User - Action - Data

        Beispiel:
            2025-12-04 - 14:23:15 - Klaus Krüger - Lieferschein gescannt - LS: LS24-077, Lieferant: Primec, Artikel: 3

        Returns:
            Formatierte Log-Zeile als String
        """
        date_str = self.timestamp.strftime("%Y-%m-%d")
        time_str = self.timestamp.strftime("%H:%M:%S")

        # Data formatieren: Nur nicht-leere Werte
        data_parts = []
        for key, value in self.data.items():
            if value is not None and str(value).strip():
                data_parts.append(f"{key}: {value}")

        data_str = ", ".join(data_parts)

        # Komplette Zeile zusammenbauen
        parts = [date_str, time_str, self.user, self.action.value, data_str]

        # Optionale Notizen anhängen
        if self.notes and self.notes.strip():
            parts.append(f"({self.notes})")

        return " - ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert Event zu Dictionary (für JSON-Serialisierung).

        Returns:
            Dictionary-Repräsentation des Events
        """
        return {
            "action": self.action.value,
            "user": self.user,
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "data": self.data,
            "notes": self.notes,
        }
