"""
Migration: Erstelle audit_log Tabelle

Erstellt die Audit Log Tabelle für vollständige Nachvollziehbarkeit
aller Benutzeraktionen im System.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy import text
from warehouse.infrastructure.database.connection import get_session


def create_audit_log_table():
    """Erstellt audit_log Tabelle mit allen Indices."""

    with get_session() as session:
        # Prüfe ob Tabelle existiert
        result = session.execute(
            text(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'audit_log'
            );
        """
            )
        )

        exists = result.scalar()

        if exists:
            print("✓ Tabelle 'audit_log' existiert bereits")
            return

        print("Erstelle Tabelle 'audit_log'...")

        # Erstelle Tabelle
        session.execute(
            text(
                """
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
        """
            )
        )

        print("  ✓ Tabelle erstellt")

        # Erstelle Indices für Performance
        print("Erstelle Indices...")

        session.execute(
            text(
                """
            CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
        """
            )
        )
        print("  ✓ Index auf timestamp")

        session.execute(
            text(
                """
            CREATE INDEX idx_audit_user ON audit_log("user");
        """
            )
        )
        print("  ✓ Index auf user")

        session.execute(
            text(
                """
            CREATE INDEX idx_audit_action ON audit_log(action);
        """
            )
        )
        print("  ✓ Index auf action")

        session.execute(
            text(
                """
            CREATE INDEX idx_audit_entity_type ON audit_log(entity_type);
        """
            )
        )
        print("  ✓ Index auf entity_type")

        session.execute(
            text(
                """
            CREATE INDEX idx_audit_entity_id ON audit_log(entity_id);
        """
            )
        )
        print("  ✓ Index auf entity_id")

        session.execute(
            text(
                """
            CREATE INDEX idx_audit_entity_history ON audit_log(entity_type, entity_id, timestamp);
        """
            )
        )
        print("  ✓ Composite Index für Entity-History")

        session.commit()

        print("\n✅ Tabelle 'audit_log' erfolgreich erstellt!")
        print("   - 6 Indices für optimale Query-Performance")
        print("   - JSONB Spalte für strukturierte Daten")
        print("   - Bereit für Audit Logging")


if __name__ == "__main__":
    print("=" * 70)
    print("Migration: Erstelle audit_log Tabelle")
    print("=" * 70)
    print()

    try:
        create_audit_log_table()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
