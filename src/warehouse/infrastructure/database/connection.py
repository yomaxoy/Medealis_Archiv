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
                from config.settings import settings

                settings.DATABASE_DIR = None
                settings.DATABASE_PATH = None
                settings.ensure_directories()
                database_path = settings.get_database_path()
                database_url = f"sqlite:///{database_path}"
                print("⚠️  Fallback: Verwende SQLite-Datenbank")
            except ImportError:
                # Letzter Fallback
                db_dir = Path.home() / ".medealis"
                db_dir.mkdir(parents=True, exist_ok=True)
                database_path = db_dir / "warehouse_new.db"
                database_url = f"sqlite:///{database_path}"
                print(
                    "⚠️  Fallback: Verwende SQLite-Datenbank (config nicht verfügbar)"
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
        print(f"✅ PostgreSQL initialisiert")
        print(f"   Connection Pool: 10 (max overflow: 20)")

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

        print(f"✅ SQLite initialisiert: {database_url}")

    else:
        raise ValueError(f"Unsupported database URL: {database_url}")

    # Session Factory
    _session_factory = sessionmaker(bind=_engine)

    print("✅ Database Session Factory erstellt")


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

            if result == 1:
                print("✅ Database Connection Test erfolgreich")
                return True
            else:
                print(
                    "❌ Database Connection Test fehlgeschlagen: Unerwartetes Ergebnis"
                )
                return False

    except SQLAlchemyError as e:
        print(f"❌ Database Connection Test fehlgeschlagen: {e}")
        return False


def get_engine():
    """Gibt die aktuelle Database Engine zurück."""
    if _engine is None:
        raise RuntimeError("Database nicht initialisiert.")
    return _engine


def is_initialized() -> bool:
    """Prüft, ob Database initialisiert ist."""
    return _engine is not None and _session_factory is not None
