# src/warehouse/infrastructure/database/connection.py

"""
SQLAlchemy Database Connection für das Warehouse Management System.
Folgt der vorgegebenen Clean Architecture Struktur.
MIGRIERT: Unterstützt PostgreSQL und SQLite
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Base Class für alle Models
Base = declarative_base()

# Globale Variablen
_engine = None
_session_factory = None


def initialize_database(database_url: str = None) -> None:
    """
    Initialisiert die Database Engine und Session Factory.

    Unterstützt PostgreSQL (primär) und SQLite (fallback).

    Args:
        database_url: Optionale Database URL (z.B. postgresql://user:pass@host/db)
                     Falls None, wird aus Environment Variable DATABASE_URL gelesen
    """
    global _engine, _session_factory

    # Skip if already initialized (prevents double initialization)
    if _engine is not None and _session_factory is not None:
        return

    # Hole Database URL
    if database_url is None:
        # Primär: Environment Variable DATABASE_URL
        database_url = os.getenv("DATABASE_URL")

        if database_url is None:
            # Fallback: SQLite aus config
            try:
                import sys
                from pathlib import Path as ConfigPath

                # Add project root to path to import config
                project_root = ConfigPath(__file__).parent.parent.parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))

                from config.settings import Settings

                Settings.DATABASE_DIR = None
                Settings.DATABASE_PATH = None
                Settings.ensure_directories()
                database_path = Settings.get_database_path()
                database_url = f"sqlite:///{database_path}"
                print(f"Server storage configured: {database_url}")
            except (ImportError, Exception) as e:
                # Letzter Fallback
                print(f"WARNING: Could not load config.settings: {e}")
                db_dir = Path.home() / ".medealis"
                db_dir.mkdir(parents=True, exist_ok=True)
                database_path = db_dir / "warehouse_new.db"
                database_url = f"sqlite:///{database_path}"
                print(
                    "WARNING: Fallback - Using SQLite database (config not available)"
                )

    # Erkenne Datenbank-Typ
    is_postgresql = database_url.startswith("postgresql://") or database_url.startswith(
        "postgres://"
    )
    is_sqlite = database_url.startswith("sqlite:///")

    # Engine Configuration basierend auf DB-Typ
    if is_postgresql:
        # PostgreSQL: Connection Pooling aktiviert
        _engine = create_engine(
            database_url,
            echo=False,  # Setze auf True für SQL Debug-Output
            pool_pre_ping=True,  # Health Check vor Connection-Nutzung
            pool_size=10,  # Connection Pool Size
            max_overflow=20,  # Max zusätzliche Connections
            pool_recycle=3600,  # Recycle Connections nach 1h
            connect_args={
                "connect_timeout": 10,  # 10s Timeout
                "options": "-c timezone=Europe/Berlin",  # Timezone setzen
            },
        )
        print("PostgreSQL initialized")
        print("   Connection Pool: 10 (max overflow: 20)")

    elif is_sqlite:
        # SQLite: Kein Pooling (nicht sinnvoll für SQLite)
        _engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            poolclass=None,  # Disable connection pooling
        )

        # SQLite PRAGMAs aktivieren (nur für SQLite)
        from sqlalchemy import event

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Aktiviert SQLite-spezifische Optimierungen."""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.close()

        print(f"SQLite initialized: {database_url}")

    else:
        raise ValueError(f"Unsupported database URL: {database_url}")

    # Session Factory
    _session_factory = sessionmaker(bind=_engine)

    print("Database Session Factory created")


@contextmanager
def get_session():
    """
    Context Manager für Database Sessions.
    Automatisches Commit/Rollback und Session-Cleanup.
    Auto-initialisiert die Datenbank falls noch nicht geschehen.

    Yields:
        SQLAlchemy Session
    """
    global _session_factory, _engine

    # Auto-initialize if not yet done (handles Streamlit reruns)
    if _session_factory is None:
        initialize_database()

    session = _session_factory()
    try:
        yield session
        session.commit()

        # CRITICAL FIX: Force WAL checkpoint for SQLite to ensure immediate visibility
        # This fixes the issue where newly inserted items are not immediately visible
        # in subsequent queries due to SQLite WAL (Write-Ahead Logging) isolation
        if _engine and str(_engine.url).startswith("sqlite"):
            from sqlalchemy import text
            try:
                session.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
                session.commit()
            except Exception:
                pass  # Ignore if WAL is not enabled or checkpoint fails

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

            if result == 1:
                print("Database Connection Test successful")
                return True
            else:
                print("Database Connection Test failed: Unexpected result")
                return False

    except SQLAlchemyError as e:
        print(f"Database Connection Test failed: {e}")
        return False


def get_engine():
    """Gibt die aktuelle Database Engine zurück."""
    if _engine is None:
        raise RuntimeError("Database nicht initialisiert.")
    return _engine


def is_initialized() -> bool:
    """Prüft, ob Database initialisiert ist."""
    return _engine is not None and _session_factory is not None
