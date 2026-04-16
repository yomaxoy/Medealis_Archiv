"""
migrate_qr_codes_to_db.py

Liest QR-Code-Dateien aus den bekannten Dateisystem-Ordnern (Server → lokal)
und speichert sie in der Datenbank (item_info.qr_code_image) –
nur für Artikel, bei denen noch kein QR-Code in der DB hinterlegt ist.

Ausführung:
    python migrate_qr_codes_to_db.py

Optionen:
    --dry-run   Nur anzeigen was migriert würde, nichts schreiben
    --overwrite Auch bereits vorhandene DB-Einträge ersetzen
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Projektpfad einbinden
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def find_qr_file_for_article(article_number: str, search_paths: list) -> Path | None:
    """Sucht QR-Code-Datei für eine Artikelnummer in den angegebenen Pfaden."""
    for source_name, base_path in search_paths:
        # Glob-Suche: Datei beginnt mit Artikelnummer
        for match in base_path.glob(f"{article_number}*.png"):
            logger.debug("Gefunden (%s): %s", source_name, match)
            return match
        # Exakte Suche
        exact = base_path / f"{article_number}.png"
        if exact.exists():
            logger.debug("Gefunden exakt (%s): %s", source_name, exact)
            return exact
    return None


def build_search_paths() -> list:
    """Gibt verfügbare QR-Code-Verzeichnisse zurück (Server → lokal)."""
    paths = []

    server_path = Path(
        r"\\10.190.140.10\Allgemein"
        r"\Qualitätsmanagement\QM_MEDEALIS"
        r"\03. Produkte\Produktprüfung"
        r"\Keyence_Messprogramme\A QR-Codes"
    )
    if server_path.exists():
        paths.append(("Server", server_path))
        logger.info("Server-Pfad verfügbar: %s", server_path)
    else:
        logger.warning("Server-Pfad nicht erreichbar: %s", server_path)

    local_path = Path.home() / "Medealis" / "Wareneingang" / "QR-Codes Messprogramme"
    if local_path.exists():
        paths.append(("Lokal", local_path))
        logger.info("Lokaler Pfad verfügbar: %s", local_path)
    else:
        logger.warning("Lokaler Pfad nicht vorhanden: %s", local_path)

    return paths


def run_migration(dry_run: bool = False, overwrite: bool = False) -> None:
    from warehouse.infrastructure.database.repositories.item_info_repository import (
        item_info_repository,
    )

    search_paths = build_search_paths()
    if not search_paths:
        logger.error("Kein QR-Code-Verzeichnis erreichbar. Abbruch.")
        sys.exit(1)

    all_items = item_info_repository.get_all()
    logger.info("Artikel in Datenbank: %d", len(all_items))

    stats = {"migrated": 0, "skipped_existing": 0, "not_found": 0, "errors": 0}

    for item in all_items:
        article_number = item.article_number
        has_qr_in_db = bool(item.qr_code_image)

        if has_qr_in_db and not overwrite:
            logger.debug("Übersprungen (DB vorhanden): %s", article_number)
            stats["skipped_existing"] += 1
            continue

        qr_file = find_qr_file_for_article(article_number, search_paths)

        if not qr_file:
            logger.info("Kein QR-Code gefunden: %s", article_number)
            stats["not_found"] += 1
            continue

        action = "Würde schreiben" if dry_run else "Schreibe"
        logger.info(
            "%s QR-Code für %s  ← %s (%.1f KB)",
            action,
            article_number,
            qr_file.name,
            qr_file.stat().st_size / 1024,
        )

        if not dry_run:
            try:
                image_bytes = qr_file.read_bytes()
                success = item_info_repository.update_qr_code(
                    article_number=article_number,
                    qr_image=image_bytes,
                    qr_filename=qr_file.name,
                )
                if success:
                    stats["migrated"] += 1
                else:
                    logger.error("Fehler beim Schreiben: %s", article_number)
                    stats["errors"] += 1
            except Exception as e:
                logger.error("Fehler für %s: %s", article_number, e)
                stats["errors"] += 1
        else:
            stats["migrated"] += 1

    print()
    print("=" * 50)
    print(f"  Migriert:              {stats['migrated']}")
    print(f"  Bereits in DB:         {stats['skipped_existing']}")
    print(f"  Kein Dateisystem-Fund: {stats['not_found']}")
    print(f"  Fehler:                {stats['errors']}")
    if dry_run:
        print("  [DRY-RUN – nichts wurde geschrieben]")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QR-Codes vom Dateisystem in DB migrieren")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nichts schreiben",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Vorhandene DB-Einträge überschreiben",
    )
    args = parser.parse_args()

    run_migration(dry_run=args.dry_run, overwrite=args.overwrite)
