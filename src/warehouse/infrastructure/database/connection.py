# src/warehouse/infrastructure/database/connection.py

"""
SQLAlchemy Database Connection für das Warehouse Management System.
Folgt der vorgegebenen Clean Architecture Struktur.
ERWEITERT um Foreign Key Constraints für SQLite.
"""

from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Base Class für alle Models
Base = declarative_base()

# Globale Variablen
_engine = None
_session_factory = None


def initialize_database(database_path: str = None) -> None:
    """
    Initialisiert die Database Engine und Session Factory.

    Args:
        database_path: Optionaler Pfad zur Database-Datei
    """
    global _engine, _session_factory

    # Skip if already initialized (prevents double initialization)
    if _engine is not None and _session_factory is not None:
        return

    if database_path is None:
        # Standard-Pfad aus config
        try:
            from config.settings import settings
            database_path = settings.DATABASE_PATH
        except ImportError:
            # Fallback wenn config nicht verfügbar
            db_dir = Path.home() / ".medealis"
            db_dir.mkdir(parents=True, exist_ok=True)
            database_path = db_dir / "warehouse_new.db"

    # SQLite Connection String
    database_url = f"sqlite:///{database_path}"

    # Engine erstellen
    _engine = create_engine(
        database_url,
        echo=False,  # Setze auf True für SQL Debug-Output
        pool_pre_ping=True,  # Überprüft Connection vor Verwendung
        poolclass=None,  # Disable connection pooling for SQLite
    )

    # WICHTIG: Foreign Key Constraints und WAL-Mode für SQLite aktivieren
    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """
        Aktiviert Foreign Key Constraints und WAL-Mode für SQLite.

        WAL (Write-Ahead Logging) ermöglicht:
        - Mehrere gleichzeitige Leser
        - Ein Schreiber kann parallel zu Lesern arbeiten
        - Bessere Concurrency für Multi-User Umgebungen
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging für Multi-User
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance zwischen Sicherheit und Performance
        cursor.execute("PRAGMA busy_timeout=5000")  # 5 Sekunden Timeout bei Locks
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB Cache
        cursor.close()

    # Session Factory
    _session_factory = sessionmaker(bind=_engine)

    print(f"Database initialisiert: {database_path}")
    print("Foreign Key Constraints aktiviert")


@contextmanager
def get_session():
    """
    Context Manager für Database Sessions.
    Automatisches Commit/Rollback und Session-Cleanup.
    Auto-initialisiert die Datenbank falls noch nicht geschehen.

    Yields:
        SQLAlchemy Session
    """
    global _session_factory

    # Auto-initialize if not yet done (handles Streamlit reruns)
    if _session_factory is None:
        initialize_database()

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """Erstellt alle Tabellen basierend auf den Models."""
    if _engine is None:
        raise RuntimeError("Database nicht initialisiert.")

    Base.metadata.create_all(bind=_engine)
    print("Database-Tabellen erstellt.")


def drop_tables() -> None:
    """Löscht alle Tabellen (für Tests)."""
    if _engine is None:
        raise RuntimeError("Database nicht initialisiert.")

    Base.metadata.drop_all(bind=_engine)
    print("Database-Tabellen gelöscht.")


def test_connection() -> bool:
    """
    Testet die Database-Verbindung.

    Returns:
        True wenn Connection erfolgreich
    """
    try:
        from sqlalchemy import text

        with get_session() as session:
            # Teste Connection
            result = session.execute(text("SELECT 1")).scalar()

            # Teste Foreign Key Constraints
            fk_result = session.execute(text("PRAGMA foreign_keys")).scalar()
            print(f"Foreign Keys Status: {fk_result}")

            return result == 1
    except SQLAlchemyError as e:
        print(f"Database Connection Test fehlgeschlagen: {e}")
        return False


def get_engine():
    """Gibt die aktuelle Database Engine zurück."""
    if _engine is None:
        raise RuntimeError("Database nicht initialisiert.")
    return _engine


def is_initialized() -> bool:
    """Prüft, ob Database initialisiert ist."""
    return _engine is not None and _session_factory is not None
