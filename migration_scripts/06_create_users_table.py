"""
Migration: Erstelle users Tabelle

Erstellt die Users Tabelle für Authentifizierung und Autorisierung.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy import text  # noqa: E402
from warehouse.infrastructure.database.connection import get_session  # noqa: E402
from warehouse.infrastructure.security.password_hasher import (  # noqa: E402
    PasswordHasher,
)


def create_users_table():
    """Erstellt users Tabelle mit allen Indices."""

    with get_session() as session:
        # Prüfe ob Tabelle existiert
        result = session.execute(
            text(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'users'
            );
        """
            )
        )

        exists = result.scalar()

        if exists:
            print("✓ Tabelle 'users' existiert bereits")
            return

        print("Erstelle Tabelle 'users'...")

        # Erstelle Tabelle
        session.execute(
            text(
                """
            CREATE TABLE users (
                user_id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
                full_name VARCHAR(255),
                last_login TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                created_by VARCHAR(50)
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
            CREATE INDEX idx_users_username ON users(username);
        """
            )
        )
        print("  ✓ Index auf username")

        session.execute(
            text(
                """
            CREATE INDEX idx_users_email ON users(email);
        """
            )
        )
        print("  ✓ Index auf email")

        session.execute(
            text(
                """
            CREATE INDEX idx_users_role ON users(role);
        """
            )
        )
        print("  ✓ Index auf role")

        session.execute(
            text(
                """
            CREATE INDEX idx_users_is_active ON users(is_active);
        """
            )
        )
        print("  ✓ Index auf is_active")

        session.commit()

        print("\n✅ Tabelle 'users' erfolgreich erstellt!")
        print("   - 4 Indices für optimale Query-Performance")
        print("   - Username und Email mit UNIQUE Constraint")
        print("   - Bereit für User-Management")


def create_default_admin():
    """Erstellt Standard-Admin-Benutzer wenn noch keine User existieren."""

    with get_session() as session:
        # Prüfe ob bereits User existieren
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()

        if count > 0:
            print("\n✓ User existieren bereits, überspringe Admin-Erstellung")
            return

        print("\nErstelle Standard-Admin-Benutzer...")

        # Default-Admin-Daten
        import uuid

        user_id = str(uuid.uuid4())
        username = "admin"
        email = "admin@medealis.local"
        password = "Admin123!"  # WICHTIG: Nach erstem Login ändern!
        role = "admin"
        full_name = "System Administrator"

        # Hash Passwort
        password_hasher = PasswordHasher()
        password_hash = password_hasher.hash_password(password)

        # Erstelle User
        insert_query = """
            INSERT INTO users (
                user_id, username, email, password_hash,
                role, is_active, must_change_password, full_name
            )
            VALUES (
                :user_id, :username, :email, :password_hash,
                :role, TRUE, TRUE, :full_name
            )
        """
        session.execute(
            text(insert_query),
            {
                "user_id": user_id,
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "full_name": full_name,
            },
        )

        session.commit()

        print("\n✅ Standard-Admin erstellt!")
        print(f"   Username: {username}")
        print(f"   Passwort: {password}")
        print("   ⚠️  WICHTIG: Bitte ändern Sie das Passwort nach dem ersten Login!")


if __name__ == "__main__":
    print("=" * 70)
    print("Migration: Erstelle users Tabelle")
    print("=" * 70)
    print()

    try:
        create_users_table()
        create_default_admin()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
