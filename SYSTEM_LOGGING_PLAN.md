# System Logging & Audit Trail - Implementierungsplan

## Übersicht

Zentrales Logging-System für alle Benutzeraktionen und Statusänderungen mit standardisiertem Format.

---

## 1. Anforderungen

### Log-Format

```
Date - Time - MitarbeiterName - Statusänderung - Data
```

**Beispiel:**
```
2025-12-04 - 14:23:15 - Klaus Krüger - Lieferschein gescannt - LS: LS24-077, Lieferant: Primec, Artikel: 3
2025-12-04 - 14:24:30 - Klaus Krüger - ItemInfo erstellt - Artikel: CT0003, Bezeichnung: DL Abutment GH 3,0mm
2025-12-04 - 14:25:12 - Klaus Krüger - Daten bestätigt - Artikel: CT0003, Menge: 10 Stk
2025-12-04 - 14:26:45 - Klaus Krüger - Sichtkontrolle - Artikel: CT0003, Ausschuss: 0, Status: OK
```

---

## 2. Architektur

### Clean Architecture Placement

```
Presentation Layer (Popups)
    ↓ (ruft auf)
Application Layer (AuditService)
    ↓ (schreibt in)
Infrastructure Layer (AuditRepository → Datei/DB)
```

### Speicherorte

1. **Produktiv:** PostgreSQL Tabelle `audit_log`
2. **Backup:** Zusätzliche Textdatei `data/logs/audit_log.txt`

---

## 3. Domain Layer - Audit Events

**Datei:** `src/warehouse/domain/events/audit_events.py`

```python
"""
Domain Events für Audit Logging.

Definiert Ereignisse die geloggt werden sollen.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class AuditAction(Enum):
    """Definierte Aktionen im System."""

    # Lieferschein
    DELIVERY_SCANNED = "Lieferschein gescannt"
    DELIVERY_CONFIRMED = "Lieferschein bestätigt"
    DELIVERY_DELETED = "Lieferschein gelöscht"

    # ItemInfo
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

    # Labels
    LABEL_GENERATED = "Label generiert"
    LABEL_PRINTED = "Label gedruckt"

    # System
    LOGIN = "Benutzer angemeldet"
    LOGOUT = "Benutzer abgemeldet"


@dataclass
class AuditEvent:
    """
    Ein einzelnes Audit-Ereignis.

    Wird von Application Services erstellt und an AuditService übergeben.
    """
    action: AuditAction
    user: str
    timestamp: datetime
    entity_type: str  # "Delivery", "Item", "Order", etc.
    entity_id: str    # Primary Key oder Composite Key
    data: Dict[str, Any]  # Zusätzliche Daten
    notes: Optional[str] = None

    def format_log_line(self) -> str:
        """
        Formatiert Event als Log-Zeile.

        Format: Date - Time - User - Action - Data
        """
        date_str = self.timestamp.strftime("%Y-%m-%d")
        time_str = self.timestamp.strftime("%H:%M:%S")

        # Data formatieren
        data_parts = []
        for key, value in self.data.items():
            if value is not None and str(value).strip():
                data_parts.append(f"{key}: {value}")

        data_str = ", ".join(data_parts)

        # Komplette Zeile
        parts = [
            date_str,
            time_str,
            self.user,
            self.action.value,
            data_str
        ]

        if self.notes:
            parts.append(f"({self.notes})")

        return " - ".join(parts)
```

---

## 4. Infrastructure Layer - Audit Repository

**Datei:** `src/warehouse/infrastructure/database/models/audit_log_model.py`

```python
"""
SQLAlchemy Model für Audit Log.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from datetime import datetime
from warehouse.infrastructure.database.connection import Base


class AuditLogModel(Base):
    """
    Audit Log Tabelle.

    Speichert alle Benutzeraktionen und Statusänderungen.
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    user = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(200), nullable=False, index=True)
    data = Column(JSON, nullable=True)  # Strukturierte Daten
    notes = Column(Text, nullable=True)
    log_line = Column(Text, nullable=False)  # Formatierte Log-Zeile

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user='{self.user}', action='{self.action}')>"
```

**Datei:** `src/warehouse/infrastructure/repositories/audit_repository.py`

```python
"""
Repository für Audit Logging.
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc

from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.audit_log_model import AuditLogModel
from warehouse.domain.events.audit_events import AuditEvent

logger = logging.getLogger(__name__)


class AuditRepository:
    """
    Repository für Audit Log Operationen.

    Speichert Audit Events in:
    1. PostgreSQL Datenbank
    2. Backup-Textdatei
    """

    def __init__(self, backup_file_path: str = "data/logs/audit_log.txt"):
        self.backup_file_path = Path(backup_file_path)
        self._ensure_backup_file_exists()

    def _ensure_backup_file_exists(self):
        """Erstellt Backup-Datei und Verzeichnis falls nicht vorhanden."""
        self.backup_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.backup_file_path.exists():
            self.backup_file_path.touch()
            logger.info(f"Audit log backup file created: {self.backup_file_path}")

    def log_event(self, event: AuditEvent) -> bool:
        """
        Loggt ein Audit-Event in DB und Datei.

        Args:
            event: AuditEvent zu loggen

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Format log line
            log_line = event.format_log_line()

            # 1. In Datenbank speichern
            with get_session() as session:
                audit_entry = AuditLogModel(
                    timestamp=event.timestamp,
                    user=event.user,
                    action=event.action.value,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    data=event.data,
                    notes=event.notes,
                    log_line=log_line
                )
                session.add(audit_entry)
                session.commit()

            # 2. In Textdatei schreiben (Backup)
            with open(self.backup_file_path, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")

            logger.info(f"Audit event logged: {event.action.value} by {event.user}")
            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            logger.exception("Full traceback:")
            return False

    def get_recent_logs(self, limit: int = 100) -> List[AuditLogModel]:
        """
        Lädt die neuesten Audit-Logs.

        Args:
            limit: Maximale Anzahl Einträge

        Returns:
            Liste von AuditLogModel (neueste zuerst)
        """
        try:
            with get_session() as session:
                logs = session.query(AuditLogModel)\
                    .order_by(desc(AuditLogModel.timestamp))\
                    .limit(limit)\
                    .all()

                # Detach from session
                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []

    def get_logs_by_user(self, user: str, days: int = 30) -> List[AuditLogModel]:
        """Lädt Logs für einen bestimmten Benutzer."""
        try:
            since = datetime.now() - timedelta(days=days)

            with get_session() as session:
                logs = session.query(AuditLogModel)\
                    .filter(AuditLogModel.user == user)\
                    .filter(AuditLogModel.timestamp >= since)\
                    .order_by(desc(AuditLogModel.timestamp))\
                    .all()

                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get logs by user: {e}")
            return []

    def get_logs_by_entity(self, entity_type: str, entity_id: str) -> List[AuditLogModel]:
        """Lädt alle Logs für eine bestimmte Entity (z.B. Item)."""
        try:
            with get_session() as session:
                logs = session.query(AuditLogModel)\
                    .filter(AuditLogModel.entity_type == entity_type)\
                    .filter(AuditLogModel.entity_id == entity_id)\
                    .order_by(AuditLogModel.timestamp)\
                    .all()

                for log in logs:
                    session.expunge(log)

                return logs
        except Exception as e:
            logger.error(f"Failed to get logs by entity: {e}")
            return []


# Global instance
audit_repository = AuditRepository()
```

---

## 5. Application Layer - Audit Service

**Datei:** `src/warehouse/application/services/audit_service.py`

```python
"""
Application Service für Audit Logging.

Zentrale Schnittstelle für alle Logging-Operationen.
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

    Wird von allen anderen Services genutzt um Aktionen zu loggen.
    """

    def __init__(self):
        self.repository = audit_repository

    def log_action(
        self,
        action: AuditAction,
        user: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        notes: Optional[str] = None
    ) -> bool:
        """
        Loggt eine Benutzeraktion.

        Args:
            action: Art der Aktion (AuditAction Enum)
            user: Benutzername
            entity_type: Typ der Entity ("Delivery", "Item", etc.)
            entity_id: ID der Entity
            data: Zusätzliche Daten (als Dict)
            notes: Optionale Notizen

        Returns:
            True bei Erfolg
        """
        event = AuditEvent(
            action=action,
            user=user,
            timestamp=datetime.now(),
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            notes=notes
        )

        return self.repository.log_event(event)

    # === Helper Methods für häufige Aktionen ===

    def log_delivery_scanned(
        self,
        user: str,
        delivery_number: str,
        supplier: str,
        item_count: int
    ) -> bool:
        """Loggt Lieferschein-Scan."""
        return self.log_action(
            action=AuditAction.DELIVERY_SCANNED,
            user=user,
            entity_type="Delivery",
            entity_id=delivery_number,
            data={
                "LS": delivery_number,
                "Lieferant": supplier,
                "Artikel": item_count
            }
        )

    def log_iteminfo_created(
        self,
        user: str,
        article_number: str,
        designation: str,
        manufacturer: Optional[str] = None
    ) -> bool:
        """Loggt ItemInfo-Erstellung."""
        data = {
            "Artikel": article_number,
            "Bezeichnung": designation
        }
        if manufacturer:
            data["Hersteller"] = manufacturer

        return self.log_action(
            action=AuditAction.ITEMINFO_CREATED,
            user=user,
            entity_type="ItemInfo",
            entity_id=article_number,
            data=data
        )

    def log_data_confirmed(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        quantity: int
    ) -> bool:
        """Loggt Daten-Bestätigung."""
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.DATA_CONFIRMED,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={
                "Artikel": article_number,
                "Charge": batch_number,
                "Menge": f"{quantity} Stk"
            }
        )

    def log_visual_inspection(
        self,
        user: str,
        article_number: str,
        batch_number: str,
        delivery_number: str,
        waste_quantity: int,
        passed: bool
    ) -> bool:
        """Loggt Sichtkontrolle."""
        entity_id = f"{article_number}#{batch_number}#{delivery_number}"

        return self.log_action(
            action=AuditAction.VISUAL_INSPECTION_DONE,
            user=user,
            entity_type="Item",
            entity_id=entity_id,
            data={
                "Artikel": article_number,
                "Ausschuss": waste_quantity,
                "Status": "OK" if passed else "Ausschuss"
            }
        )

    # ... weitere Helper Methods für andere Aktionen


# Global instance
audit_service = AuditService()
```

---

## 6. Presentation Layer - Integration

### 6.1 User-Kontext aus Session State

**Zentrale Helper-Funktion:**

```python
# src/warehouse/presentation/utils/user_context.py

import streamlit as st

def get_current_user() -> str:
    """
    Holt aktuellen Benutzer aus Session State.

    Returns:
        Username oder "System" als Fallback
    """
    return st.session_state.get("current_user", "System")
```

### 6.2 Integration in Popups

**Beispiel:** `iteminfo_edit_dialog.py`

```python
from warehouse.application.services.audit_service import audit_service
from warehouse.presentation.utils.user_context import get_current_user

@st.dialog("📝 Artikel-Informationen bearbeiten", width="large")
def show_iteminfo_edit_dialog(article_data: Dict[str, Any]):
    # ... bestehender Code ...

    with col_btn2:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            # ... Validierung ...

            # Speichern
            try:
                if existing_iteminfo:
                    result = item_info_repository.update_item_info(article_number, iteminfo_data)
                    action = "aktualisiert"
                else:
                    result = item_info_repository.create_item_info(iteminfo_data)
                    action = "erstellt"

                if result:
                    # AUDIT LOGGING
                    current_user = get_current_user()
                    if action == "erstellt":
                        audit_service.log_iteminfo_created(
                            user=current_user,
                            article_number=article_number,
                            designation=final_designation,
                            manufacturer=manufacturer
                        )
                    else:
                        audit_service.log_action(
                            action=AuditAction.ITEMINFO_UPDATED,
                            user=current_user,
                            entity_type="ItemInfo",
                            entity_id=article_number,
                            data={
                                "Artikel": article_number,
                                "Bezeichnung": final_designation
                            }
                        )

                    st.success(f"✅ ItemInfo gespeichert!")
                    st.session_state.show_iteminfo_edit_dialog = False
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
```

---

## 7. Migration

**Datei:** `migration_scripts/05_create_audit_log_table.py`

```python
"""
Migration: Erstelle audit_log Tabelle
"""

import sys
from pathlib import Path
from sqlalchemy import text

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from warehouse.infrastructure.database.connection import get_session


def create_audit_log_table():
    """Erstellt audit_log Tabelle."""

    with get_session() as session:
        # Prüfe ob Tabelle existiert
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'audit_log'
            );
        """))

        exists = result.scalar()

        if exists:
            print("✓ Tabelle 'audit_log' existiert bereits")
            return

        # Erstelle Tabelle
        session.execute(text("""
            CREATE TABLE audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                "user" VARCHAR(100) NOT NULL,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(200) NOT NULL,
                data JSONB,
                notes TEXT,
                log_line TEXT NOT NULL
            );

            -- Indices für Performance
            CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
            CREATE INDEX idx_audit_user ON audit_log("user");
            CREATE INDEX idx_audit_action ON audit_log(action);
            CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
        """))

        session.commit()
        print("✅ Tabelle 'audit_log' erstellt")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Erstelle audit_log Tabelle")
    print("=" * 60)
    print()

    try:
        create_audit_log_table()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---

## 8. Implementierungsschritte

### Phase 1: Infrastruktur (2h)
1. ✅ Domain Events definieren (`audit_events.py`)
2. ✅ Database Model erstellen (`audit_log_model.py`)
3. ✅ Migration ausführen
4. ✅ Repository implementieren (`audit_repository.py`)

### Phase 2: Application Service (1h)
1. ✅ `AuditService` erstellen
2. ✅ Helper Methods für häufige Aktionen
3. ✅ User-Context Helper

### Phase 3: Integration (3-4h)
1. ✅ Lieferschein-Scan
2. ✅ ItemInfo-Dialoge
3. ✅ Workflow-Popups (Daten, Dokumente, Sichtkontrolle)
4. ✅ Bestellungen, Labels, etc.

### Phase 4: UI für Log-Anzeige (optional, 2h)
1. ✅ Admin-View mit Log-Tabelle
2. ✅ Filter nach User, Datum, Aktion
3. ✅ Export-Funktion

---

## 9. Beispiel-Log-Ausgabe

**audit_log.txt:**
```
2025-12-04 - 14:23:15 - Klaus Krüger - Lieferschein gescannt - LS: LS24-077, Lieferant: Primec, Artikel: 3
2025-12-04 - 14:24:30 - Klaus Krüger - ItemInfo erstellt - Artikel: CT0003, Bezeichnung: DL Abutment für C-Tech Esthetic Line GH 3,0mm, Hersteller: Primec
2025-12-04 - 14:24:35 - Klaus Krüger - ItemInfo erstellt - Artikel: CT0004, Bezeichnung: DL Abutment für C-Tech Esthetic Line GH 4,0mm, Hersteller: Primec
2025-12-04 - 14:24:40 - Klaus Krüger - ItemInfo erstellt - Artikel: MG0001, Bezeichnung: Docklocs Abutment gerade, MEGAGEN, GH1, Hersteller: Primec
2025-12-04 - 14:25:12 - Klaus Krüger - Daten bestätigt - Artikel: CT0003, Charge: P-153520240417, Menge: 10 Stk
2025-12-04 - 14:26:45 - Klaus Krüger - Sichtkontrolle durchgeführt - Artikel: CT0003, Ausschuss: 0, Status: OK
2025-12-04 - 14:27:20 - Klaus Krüger - Artikel abgeschlossen - Artikel: CT0003, Charge: P-153520240417
```

---

## 10. Vorteile

✅ **Vollständige Nachvollziehbarkeit** - Jede Aktion wird geloggt
✅ **Compliance-konform** - Audit Trail für Medizinprodukte
✅ **Fehlersuche** - Nachvollziehen was wann schief ging
✅ **Statistiken** - Wer macht was wie oft
✅ **Backup** - Doppelte Speicherung (DB + Datei)
✅ **Strukturiert** - JSONB für komplexe Queries
✅ **Erweiterbar** - Neue Aktionen einfach hinzufügen

---

## 11. Offene Fragen

1. **User-Authentifizierung:** Wann wird diese implementiert? (Aktuell Fallback "System")
2. **Log-Retention:** Wie lange Logs aufbewahren? (Empfehlung: 7 Jahre für Medizinprodukte)
3. **Performance:** Bei sehr vielen Logs evtl. Partitionierung nach Datum
4. **Datenschutz:** Personenbezogene Daten in Logs? (DSGVO)

---

## 12. Nächste Schritte

Nach Genehmigung:
1. Migration ausführen (`05_create_audit_log_table.py`)
2. Domain Events & Repository implementieren
3. AuditService erstellen
4. Schrittweise in Popups integrieren
5. Dokumentation & Tests
