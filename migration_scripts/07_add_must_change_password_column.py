"""
Migration: Fügt must_change_password Spalte zur users Tabelle hinzu.

Für bestehende Datenbanken, die mit 06_create_users_table.py
erstellt wurden (ohne must_change_password Spalte).
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy import text  # noqa: E402
from warehouse.infrastructure.database.connection import get_session  # noqa: E402


def add_must_change_password_column():
    """Fügt must_change_password Spalte hinzu falls nicht vorhanden."""

    with get_session() as session:
        # Prüfe ob Spalte bereits existiert
        result = session.execute(
            text(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'users'
                AND column_name = 'must_change_password'
            );
        """
            )
        )

        exists = result.scalar()

        if exists:
            print("  Spalte 'must_change_password' existiert bereits")
            return

        print("Füge Spalte 'must_change_password' hinzu...")

        session.execute(
            text(
                """
            ALTER TABLE users
            ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT FALSE;
        """
            )
        )

        # Setze Flag für den Default-Admin (User mit username='admin')
        session.execute(
            text(
                """
            UPDATE users
            SET must_change_password = TRUE
            WHERE username = 'admin'
            AND last_login IS NULL;
        """
            )
        )

        session.commit()

        print("  Spalte 'must_change_password' hinzugefügt")
        print("  Default-Admin (falls noch nie eingeloggt) markiert für Passwortwechsel")


if __name__ == "__main__":
    print("=" * 70)
    print("Migration: must_change_password Spalte")
    print("=" * 70)
    print()

    try:
        add_must_change_password_column()
        print("\nMigration erfolgreich!")
    except Exception as e:
        print(f"\nFehler: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
