"""
Application Service für Audit Logging.

Zentraler Service für alle Logging-Operationen im System.
Wird von allen Popups und Services verwendet um Aktionen zu loggen.

Design Pattern: Facade Pattern - vereinfacht Logging für andere Services.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from warehouse.domain.events.audit_events import AuditEvent, AuditAction
from warehouse.infrastructure.repositories.audit_repository import audit_repository

logger = logging.getLogger(__name__)


class AuditService:
    """
    Zentraler Service für Audit Logging.

    Verwendung:
        # In Popups nach dem Speichern:
        from warehouse.application.services.audit_service import audit_service

        audit_service.log_iteminfo_created(
            user=current_user,
            article_number="CT0003",
            designation="DL Abutment GH 3,0mm",
            manufacturer="Primec"
        )

    Alle Methods folgen dem Pattern:
    - Nehmen relevante Parameter entgegen
    - Erstellen AuditEvent
    - Loggen via Repository
    - Return bool (Success/Failure)
    """

    def __init__(self):
        """Initialisiert Service mit Repository."""
        self.repository = audit_repository

    def log_action(
        self,
        action: AuditAction,
        user: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> bool:
        """
        Generische Methode zum Loggen einer Aktion.

        Args:
            action: Art der Aktion (AuditAction Enum)
            user: Benutzername
            entity_type: Typ der Entity ("Delivery", "Item", "ItemInfo", "Order", etc.)
            entity_id: Eindeutige ID der Entity
            data: Zusätzliche Daten (wird als JSONB gespeichert
                + in Log-Zeile formatiert)
            notes: Optionale Freitext-Notizen

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            event = AuditEvent(
                action=action,
                user=user,
                timestamp=datetime.now(),
                entity_type=entity_type,
                entity_id=entity_id,
                data=data,
                notes=notes,
            )

            return self.repository.log_event(event)

        except Exception as e:
            logger.error(f"Failed to create audit event: {e}")
            logger.exception("Full traceback:")
            return False

    # === LIEFERSCHEIN AKTIONEN ===

    def log_delivery_scanned(
        self,
        user: str,
        delivery_number: str,
        supplier: str,
        item_count: int,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Loggt Lieferschein-Scan.

        Args:
            user: Benutzername
            delivery_number: Lieferscheinnummer
            supplier: Lieferantenname
            item_count: Anzahl extrahierter Artikel
            notes: Optionale Notizen

        Returns:
            True bei Erfolg
        """
        return self.log_action(
            action=AuditAction.DELIVERY_SCANNED,
            user=user,
            entity_type="Delivery",
            entity_id=delivery_number,
            data={"LS": delivery_number, "Lieferant": supplier, "Artikel": item_count},
            notes=notes,
        )

    def log_delivery_confirmed(
        self,
        user: str,
        delivery_number: str,
        item_count: int,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Lieferschein-Bestätigung (Speichern im Extraction-Popup)."""
        return self.log_action(
            action=AuditAction.DELIVERY_CONFIRMED,
            user=user,
            entity_type="Delivery",
            entity_id=delivery_number,
            data={"LS": delivery_number, "Artikel": item_count},
            notes=notes,
        )

    # === ITEMINFO AKTIONEN ===

    def log_iteminfo_created(
        self,
        user: str,
        article_number: str,
        designation: str,
        hersteller: Optional[str] = None,
        kompatibilitaet: Optional[str] = None,
        manufacturer: Optional[str] = None,  # Backward-Compat-Alias
        notes: Optional[str] = None,
    ) -> bool:
        """
        Loggt ItemInfo-Erstellung.

        Args:
            user: Benutzername
            article_number: Artikelnummer
            designation: Artikelbezeichnung
            hersteller: Verantwortlicher Hersteller (optional)
            kompatibilitaet: Kompatible Implantatmarke (optional)
            notes: Optionale Notizen

        Returns:
            True bei Erfolg
        """
        data = {"Artikel": article_number, "Bezeichnung": designation}
        if hersteller:
            data["Hersteller"] = hersteller
        elif manufacturer:
            data["Hersteller"] = manufacturer  # Backward-Compat
        if kompatibilitaet:
            data["Kompatibilität"] = kompatibilitaet

        return self.log_action(
            action=AuditAction.ITEMINFO_CREATED,
            user=user,
            entity_type="ItemInfo",
            entity_id=article_number,
            data=data,
            notes=notes,
        )

    def log_iteminfo_updated(
        self,
        user: str,
        article_number: str,
        designation: str,
        hersteller: Optional[str] = None,
        kompatibilitaet: Optional[str] = None,
        manufacturer: Optional[str] = None,  # Backward-Compat-Alias
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt ItemInfo-Aktualisierung."""
        data = {"Artikel": article_number, "Bezeichnung": designation}
        if hersteller:
            data["Hersteller"] = hersteller
        elif manufacturer:
            data["Hersteller"] = manufacturer  # Backward-Compat
        if kompatibilitaet:
            data["Kompatibilität"] = kompatibilitaet

        return self.log_action(
            action=AuditAction.ITEMINFO_UPDATED,
            user=user,
            entity_type="ItemInfo",
            entity_id=article_number,
            data=data,
            notes=notes,
        )

    def log_qr_uploaded(
        self, user: str, article_number: str, filename: str, notes: Optional[str] = None
    ) -> bool:
        """Loggt QR-Code Upload."""
        return self.log_action(
            action=AuditAction.ITEMINFO_QR_UPLOADED,
            user=user,
            entity_type="ItemInfo",
            entity_id=article_number,
            data={"Artikel": article_number, "Datei": filename},
            notes=notes,
        )

    # === WORKFLOW AKTIONEN ===

    def log_data_confirmed(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        quantity: int,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Loggt Daten-Bestätigung (Workflow-Step 1).

        Args:
            user: Benutzername
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            quantity: Gelieferte Menge
            notes: Optionale Notizen

        Returns:
            True bei Erfolg
        """
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.DATA_CONFIRMED,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={
                "Artikel": article_number,
                "Charge": batch_number,
                "Menge": f"{quantity} Stk",
            },
            notes=notes,
        )

    def log_documents_checked(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        certificates: Dict[str, bool],
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Dokumentenprüfung (Workflow-Step 2)."""
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        # Formatiere Zertifikate für Log
        cert_list = [name for name, present in certificates.items() if present]
        cert_str = ", ".join(cert_list) if cert_list else "keine"

        return self.log_action(
            action=AuditAction.DOCUMENTS_CHECKED,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={"Artikel": article_number, "Zertifikate": cert_str},
            notes=notes,
        )

    def log_measurement_done(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Vermessung (Workflow-Step 3)."""
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.MEASUREMENT_DONE,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={"Artikel": article_number, "Charge": batch_number},
            notes=notes,
        )

    def log_visual_inspection(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        waste_quantity: int,
        passed: bool,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Loggt Sichtkontrolle (Workflow-Step 4).

        Args:
            user: Benutzername
            article_number: Artikelnummer
            batch_number: Chargennummer
            delivery_number: Lieferscheinnummer
            waste_quantity: Ausschussmenge
            passed: True wenn bestanden, False wenn abgelehnt
            notes: Optionale Notizen

        Returns:
            True bei Erfolg
        """
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.VISUAL_INSPECTION_DONE,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={
                "Artikel": article_number,
                "Ausschuss": waste_quantity,
                "Status": "OK" if passed else "Ausschuss",
            },
            notes=notes,
        )

    def log_item_completed(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Artikel-Abschluss."""
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.ITEM_COMPLETED,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={"Artikel": article_number, "Charge": batch_number},
            notes=notes,
        )

    def log_item_rejected(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        reason: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Artikel-Ausschuss."""
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.ITEM_REJECTED,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={"Artikel": article_number, "Charge": batch_number, "Grund": reason},
            notes=notes,
        )

    # === BESTELLUNG AKTIONEN ===

    def log_order_created(
        self,
        user: str,
        order_number: str,
        supplier: str,
        item_count: int,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Bestellung-Erstellung."""
        return self.log_action(
            action=AuditAction.ORDER_CREATED,
            user=user,
            entity_type="Order",
            entity_id=order_number,
            data={
                "Bestellung": order_number,
                "Lieferant": supplier,
                "Artikel": item_count,
            },
            notes=notes,
        )

    # === LABEL/DOKUMENT AKTIONEN ===

    def log_label_generated(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Label-Generierung."""
        entity_id = f"{article_number}#{batch_number}"

        return self.log_action(
            action=AuditAction.LABEL_GENERATED,
            user=user,
            entity_type="Label",
            entity_id=entity_id,
            data={"Artikel": article_number, "Charge": batch_number},
            notes=notes,
        )

    # === LOGIN/LOGOUT AKTIONEN ===

    def log_login(self, user: str, notes: Optional[str] = None) -> bool:
        """Loggt erfolgreichen Login."""
        return self.log_action(
            action=AuditAction.LOGIN,
            user=user,
            entity_type="User",
            entity_id=user,
            data={"Benutzer": user},
            notes=notes,
        )

    def log_logout(self, user: str, notes: Optional[str] = None) -> bool:
        """Loggt Logout."""
        return self.log_action(
            action=AuditAction.LOGOUT,
            user=user,
            entity_type="User",
            entity_id=user,
            data={"Benutzer": user},
            notes=notes,
        )

    # === BENUTZERVERWALTUNG AKTIONEN ===

    def log_user_created(
        self, actor: str, username: str, role: str, notes: Optional[str] = None
    ) -> bool:
        """Loggt Benutzer-Erstellung (keine sensiblen Daten)."""
        return self.log_action(
            action=AuditAction.USER_CREATED,
            user=actor,
            entity_type="User",
            entity_id=username,
            data={"Benutzer": username, "Rolle": role},
            notes=notes,
        )

    def log_user_role_changed(
        self,
        actor: str,
        username: str,
        old_role: str,
        new_role: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Loggt Rollenänderung."""
        return self.log_action(
            action=AuditAction.USER_ROLE_CHANGED,
            user=actor,
            entity_type="User",
            entity_id=username,
            data={
                "Benutzer": username,
                "Alte Rolle": old_role,
                "Neue Rolle": new_role,
            },
            notes=notes,
        )

    def log_user_password_reset(
        self, actor: str, username: str, notes: Optional[str] = None
    ) -> bool:
        """Loggt Passwort-Reset (NICHT das Passwort selbst!)."""
        return self.log_action(
            action=AuditAction.USER_PASSWORD_RESET,
            user=actor,
            entity_type="User",
            entity_id=username,
            data={"Benutzer": username},
            notes=notes,
        )

    def log_user_password_changed(self, user: str, notes: Optional[str] = None) -> bool:
        """Loggt Passwort-Änderung durch den User selbst (NICHT das Passwort!)."""
        return self.log_action(
            action=AuditAction.USER_PASSWORD_CHANGED,
            user=user,
            entity_type="User",
            entity_id=user,
            data={"Benutzer": user},
            notes=notes,
        )

    def log_user_activated(
        self, actor: str, username: str, notes: Optional[str] = None
    ) -> bool:
        """Loggt Benutzer-Aktivierung."""
        return self.log_action(
            action=AuditAction.USER_ACTIVATED,
            user=actor,
            entity_type="User",
            entity_id=username,
            data={"Benutzer": username},
            notes=notes,
        )

    def log_user_deactivated(
        self, actor: str, username: str, notes: Optional[str] = None
    ) -> bool:
        """Loggt Benutzer-Deaktivierung."""
        return self.log_action(
            action=AuditAction.USER_DEACTIVATED,
            user=actor,
            entity_type="User",
            entity_id=username,
            data={"Benutzer": username},
            notes=notes,
        )

    # === QUERY METHODS (delegiert an Repository) ===

    def get_recent_logs(self, limit: int = 100):
        """Lädt neueste Logs."""
        return self.repository.get_recent_logs(limit)

    def get_logs_by_user(self, user: str, days: int = 30):
        """Lädt Logs für einen User."""
        return self.repository.get_logs_by_user(user, days)

    def get_entity_history(self, entity_type: str, entity_id: str):
        """Lädt vollständige Historie für eine Entity."""
        return self.repository.get_logs_by_entity(entity_type, entity_id)

    def search_logs(self, search_term: str, limit: int = 200):
        """Durchsucht Logs nach Freitext."""
        return self.repository.search_logs(search_term, limit)


# Global instance (Singleton pattern)
audit_service = AuditService()
