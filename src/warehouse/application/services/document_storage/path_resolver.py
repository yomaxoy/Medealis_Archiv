"""
Path Resolver Service - Einheitliche Pfad-Auflösung

EINZIGE Pfad-Erstellung im System.
Ersetzt PathManager/DocumentPathService/enhanced_document_service Pfad-Aufrufe.
Verwendet StorageContext für konsistente Datenbereitstellung.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

from .storage_context import StorageContextData
from ..document_generation.document_types import DocumentType

logger = logging.getLogger(__name__)


@dataclass
class PathResult:
    """
    Ergebnis einer Pfad-Auflösung.
    Enthält Pfad und Metadaten über die Erstellung.
    """

    path: Path
    created: bool = False
    existed: bool = False
    error: Optional[str] = None
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    @property
    def success(self) -> bool:
        """True wenn Pfad erfolgreich aufgelöst wurde."""
        return self.error is None

    def add_warning(self, message: str):
        """Fügt Warnung hinzu."""
        self.warnings.append(message)
        logger.warning(message)


class PathResolver:
    """
    Einheitliche Pfad-Auflösung für alle Storage-Operationen.

    KRITISCHES DESIGN-PRINZIP:
    - EINZIGE Klasse die Pfade erstellt
    - Alle anderen Services nutzen nur PathResolver
    - Konsistente Ordnerstruktur systemweit
    - Basiert auf StorageContext für Daten-Konsistenz
    """

    def __init__(self):
        self.logger = logger

        # Konfigurierbare Basis-Pfade (lokal)
        self._base_storage_path = None
        self._document_output_path = None
        self._temp_path = None

        # Server-Pfade (UNC: \\10.190.140.10\Allgemein)
        self._server_storage_path = None

        # SharePoint Basis-Pfade
        self._sharepoint_qm_base = (
            "QM_System_Neu/08_Messung_Analyse/06_Überwachung_Produkte"
        )

    @property
    def base_storage_path(self) -> Path:
        """Basis-Pfad für alle Dokument-Storage Operationen."""
        if self._base_storage_path is None:
            self._base_storage_path = Path.home() / "Medealis" / "Wareneingang"
        return self._base_storage_path

    @property
    def document_output_path(self) -> Path:
        """Basis-Pfad für generierte Dokumente."""
        if self._document_output_path is None:
            self._document_output_path = Path.home() / ".medealis" / "documents"
        return self._document_output_path

    @property
    def temp_path(self) -> Path:
        """Basis-Pfad für temporäre Dateien."""
        if self._temp_path is None:
            self._temp_path = Path.home() / ".medealis" / "temp"
        return self._temp_path

    @property
    def sharepoint_qm_base(self) -> str:
        """SharePoint QM System Basis-Pfad."""
        return self._sharepoint_qm_base

    @property
    def sharepoint_produktionsunterlagen(self) -> str:
        """SharePoint Produktionsunterlagen Basis-Pfad."""
        return f"{self._sharepoint_qm_base}/Produktionsunterlagen"

    @property
    def sharepoint_qr_codes(self) -> str:
        """SharePoint QR-Codes Pfad."""
        return f"{self._sharepoint_qm_base}/Keyence_QR-Codes_Messprogramme"

    @property
    def server_qr_code_path(self) -> Path:
        r"""
        Server-Pfad für QR-Code-Vorlagen (Keyence Messprogramme).

        PRIMÄRE Quelle für QR-Codes die in Labels eingefügt werden.

        Verwendet DIREKT den UNC-Pfad statt gemapptem Laufwerk A:\.

        Struktur:
        \\\\10.190.140.10\\Allgemein\\QM_MEDEALIS\\
        03. Produkte\\Produktprüfung\\
        Keyence_Messprogramme\\A QR-Codes\\

        Returns:
            Path zum Server QR-Code-Verzeichnis
        """
        qr_path = Path(
            r"\\10.190.140.10\Allgemein"
            r"\Qualitätsmanagement\QM_MEDEALIS"
            r"\03. Produkte\Produktprüfung"
            r"\Keyence_Messprogramme\A QR-Codes"
        )

        # Validiere dass Server erreichbar ist
        if not qr_path.exists():
            self.logger.warning("Server QR-Code-Pfad nicht " f"verfügbar: {qr_path}")

        return qr_path

    @property
    def local_qr_code_path(self) -> Path:
        r"""
        FALLBACK: Lokaler Pfad für QR-Code-Vorlagen.

        Wird verwendet wenn Server-Pfad nicht verfügbar ist.

        Returns:
            Path zum lokalen QR-Code-Verzeichnis
        """
        return Path.home() / "Medealis" / "Wareneingang" / "QR-Codes Messprogramme"

    @property
    def server_storage_path(self) -> Path:
        r"""
        Basis-Pfad für SERVER-Speicherung (Netzlaufwerk).

        DIES IST DER NEUE STANDARD für Produktiv-Speicherung!

        Verwendet DIREKT den UNC-Pfad
        (\\\\10.190.140.10\\Allgemein) statt gemapptem
        Laufwerk A:\\, da gemappte Laufwerke nicht
        immer in Python-Prozessen sichtbar sind.

        Struktur:
        \\\\10.190.140.10\\Allgemein\\QM_Medealis\\
        03. Produkte\\Chargenverwaltung\\
        Produktionsunterlagen\\

        Returns:
            Path zum Server-Basis-Verzeichnis
        """
        if self._server_storage_path is None:
            # DIREKT UNC-Pfad verwenden (robuster als gemappter Laufwerksbuchstabe)
            self._server_storage_path = Path(
                r"\\10.190.140.10\Allgemein\Qualitätsmanagement\QM_Medealis"
                r"\03. Produkte\Chargenverwaltung\Produktionsunterlagen"
            )

            # Validiere dass Server erreichbar ist
            try:
                if not self._server_storage_path.exists():
                    self.logger.warning(
                        f"Server-Pfad nicht erreichbar: {self._server_storage_path}"
                    )
            except (OSError, PermissionError) as e:
                self.logger.warning(
                    f"Server-Pfad nicht verfügbar: {self._server_storage_path} ({e})"
                )

        return self._server_storage_path

    def resolve_storage_path(
        self, context: StorageContextData, create_folders: bool = True
    ) -> PathResult:
        """
        EINZIGE Methode für Storage-Pfad-Erstellung.
        Verwendet von allen Services für konsistente Pfad-Struktur.

        Args:
            context: Vollständiger Storage-Kontext
            create_folders: Ob Ordnerstruktur erstellt werden soll

        Returns:
            PathResult mit aufgelöstem Pfad und Metadaten
        """
        try:
            self.logger.info(
                f"Resolving storage path for batch: {context.batch_number}"
            )

            # Validiere Kontext
            validation_issues = context.get_validation_issues()
            if not context.is_complete_for_storage():
                error_msg = (
                    f"Incomplete storage context: {', '.join(validation_issues)}"
                )
                return PathResult(path=Path(), error=error_msg)

            # Erstelle Pfad-Komponenten (bereinigt für Dateisystem)
            clean_supplier = self._clean_path_component(context.supplier_normalized)
            clean_kompatibilitaet = self._clean_path_component(context.kompatibilitaet)
            clean_article = self._clean_path_component(context.article_number)
            clean_batch = self._clean_path_component(context.batch_number)
            clean_delivery = self._clean_path_component(context.delivery_number)

            # SPEZIALFALL: Wenn Lieferant = Kompatibilitätsmarke,
            # überspringe den Ordner
            # (z.B. Terrats Medical ist gleichzeitig Lieferant
            # UND Kompatibilitätsmarke)
            # Vermeidet Duplikationen wie
            # TERRATS_Medical/Terrats_Medical/
            supplier_is_kompatibilitaet = clean_supplier.lower().replace(
                "_", ""
            ).replace("-", "") == clean_kompatibilitaet.lower().replace(
                "_", ""
            ).replace(
                "-", ""
            )

            # Baue Pfad-Struktur auf:
            # Normal: Base/Supplier/Kompatibilität/
            #   Article/Batch/Delivery
            # Spezial (Supplier=Kompatibilität):
            #   Base/Supplier/Article/Batch/Delivery
            if supplier_is_kompatibilitaet:
                self.logger.info(
                    "Supplier equals Kompatibilität "
                    f"({clean_supplier}), skipping folder"
                )
                storage_path = (
                    self.base_storage_path
                    / clean_supplier
                    / clean_article
                    / clean_batch
                    / clean_delivery
                )
            else:
                storage_path = (
                    self.base_storage_path
                    / clean_supplier
                    / clean_kompatibilitaet
                    / clean_article
                    / clean_batch
                    / clean_delivery
                )

            # Erstelle Pfad-Ergebnis
            result = PathResult(path=storage_path)

            # Prüfe ob Pfad bereits existiert
            result.existed = storage_path.exists()

            # Erstelle Ordnerstruktur falls gewünscht
            if create_folders:
                folder_result = self.create_folder_structure(storage_path)
                result.created = folder_result.success and not result.existed
                if folder_result.error:
                    result.error = folder_result.error
                    return result
                result.warnings.extend(folder_result.warnings)

            # Warnungen für niedrige Datenqualität
            if context.completeness_score < 0.8:
                result.add_warning(
                    "Storage path created with low data "
                    "completeness "
                    f"({context.completeness_score:.1%})"
                )

            if context.context_source == "fallback":
                result.add_warning(
                    "Storage path created with fallback " "data - verify accuracy"
                )

            self.logger.info(f"Storage path resolved successfully: {storage_path}")
            return result

        except Exception as e:
            error_msg = f"Failed to resolve storage path: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def resolve_server_storage_path(
        self, context: StorageContextData, create_folders: bool = True
    ) -> PathResult:
        r"""
        STANDARD-METHODE für Server-Speicherung
        (UNC-Pfad).

        Erstellt Pfad auf dem Firmenserver für
        zentrale Dokumentenverwaltung.
        Verwendet direkt UNC-Pfad
        (\\10.190.140.10\Allgemein).

        Pfad-Struktur (identisch zur lokalen):
        \\10.190.140.10\...\Produktionsunterlagen\
        {Lieferant}\{Hersteller}\{Artikelnummer}\
        {Chargennummer}\{Lieferscheinnummer}\

        Args:
            context: Vollständiger Storage-Kontext
            create_folders: Ob Ordnerstruktur erstellt
                werden soll (default: True)

        Returns:
            PathResult mit Server-Pfad und Metadaten

        Example:
            >>> ctx = StorageContextData(
            ...     batch_number="20240415-1234",
            ...     delivery_number="LS24-077",
            ...     article_number="MG0001",
            ...     supplier_normalized="Primec",
            ...     manufacturer="MegaGen"
            ... )
            >>> r = path_resolver\
            ...     .resolve_server_storage_path(ctx)
            >>> print(r.path)
        """
        try:
            self.logger.info(
                f"Resolving SERVER storage path for batch: {context.batch_number}"
            )

            # Validiere Kontext
            validation_issues = context.get_validation_issues()
            if not context.is_complete_for_storage():
                error_msg = (
                    f"Incomplete storage context: {', '.join(validation_issues)}"
                )
                return PathResult(path=Path(), error=error_msg)

            # Validiere dass Server verfügbar ist (prüfe direkt den UNC-Pfad)
            server_available = self.server_storage_path.exists()
            self.logger.info(
                f"DEBUG path_resolver: Server storage available = {server_available}"
            )

            if not server_available:
                srv = self.server_storage_path
                error_msg = (
                    "Server-Speicherpfad nicht "
                    f"verfügbar: {srv}\n"
                    "Bitte Netzwerkverbindung "
                    "prüfen oder IT-Support "
                    "kontaktieren."
                )
                self.logger.error(error_msg)
                return PathResult(path=Path(), error=error_msg)

            # Erstelle Pfad-Komponenten (bereinigt für Dateisystem)
            clean_supplier = self._clean_path_component(context.supplier_normalized)
            clean_kompatibilitaet = self._clean_path_component(context.kompatibilitaet)
            clean_article = self._clean_path_component(context.article_number)
            clean_batch = self._clean_path_component(context.batch_number)
            clean_delivery = self._clean_path_component(context.delivery_number)

            # SPEZIALFALL: Wenn Lieferant = Kompatibilitätsmarke,
            # überspringe den Ordner
            # (z.B. Terrats Medical ist gleichzeitig Lieferant
            # UND Kompatibilitätsmarke)
            # Vermeidet Duplikationen wie
            # TERRATS_Medical/Terrats_Medical/
            supplier_is_kompatibilitaet = clean_supplier.lower().replace(
                "_", ""
            ).replace("-", "") == clean_kompatibilitaet.lower().replace(
                "_", ""
            ).replace(
                "-", ""
            )

            # Baue Server-Pfad-Struktur auf
            # (IDENTISCH zur lokalen Struktur):
            # Normal: Server/Supplier/Kompatibilität/
            #   Article/Batch/Delivery
            # Spezial (Supplier=Kompatibilität):
            #   Server/Supplier/Article/Batch/Delivery
            if supplier_is_kompatibilitaet:
                self.logger.info(
                    "Supplier equals Kompatibilität "
                    f"({clean_supplier}), skipping folder"
                )
                server_path = (
                    self.server_storage_path
                    / clean_supplier
                    / clean_article
                    / clean_batch
                    / clean_delivery
                )
            else:
                server_path = (
                    self.server_storage_path
                    / clean_supplier
                    / clean_kompatibilitaet
                    / clean_article
                    / clean_batch
                    / clean_delivery
                )

            # Erstelle Pfad-Ergebnis
            result = PathResult(path=server_path)

            # Prüfe ob Pfad bereits existiert
            result.existed = server_path.exists()

            # Erstelle Ordnerstruktur falls gewünscht
            if create_folders:
                folder_result = self.create_folder_structure(server_path)
                result.created = folder_result.success and not result.existed
                if folder_result.error:
                    result.error = folder_result.error
                    return result
                result.warnings.extend(folder_result.warnings)

            # Warnungen für niedrige Datenqualität
            if context.completeness_score < 0.8:
                score = context.completeness_score
                result.add_warning(
                    "Server path created with low "
                    "data completeness "
                    f"({score:.1%})"
                )

            if context.context_source == "fallback":
                result.add_warning(
                    "Server path created with fallback data - verify accuracy"
                )

            self.logger.info(
                f"Server storage path resolved successfully: {server_path}"
            )
            return result

        except Exception as e:
            error_msg = f"Failed to resolve server storage path: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def resolve_document_output_path(self, filename: str) -> PathResult:
        """
        Löst Pfad für generierte Dokument-Outputs auf.

        Args:
            filename: Dateiname für das Dokument

        Returns:
            PathResult mit Dokument-Output-Pfad
        """
        try:
            clean_filename = self._clean_filename(filename)
            document_path = self.document_output_path / clean_filename

            # Stelle sicher dass Output-Verzeichnis existiert
            folder_result = self.create_folder_structure(self.document_output_path)

            result = PathResult(path=document_path)
            result.existed = document_path.exists()
            result.created = folder_result.success

            if folder_result.error:
                result.error = folder_result.error

            return result

        except Exception as e:
            error_msg = f"Failed to resolve document output path: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def resolve_temp_path(self, filename: str) -> PathResult:
        """
        Löst temporären Pfad für Dateiverarbeitung auf.

        Args:
            filename: Temporärer Dateiname

        Returns:
            PathResult mit temporärem Pfad
        """
        try:
            clean_filename = self._clean_filename(filename)
            temp_file_path = self.temp_path / clean_filename

            # Stelle sicher dass Temp-Verzeichnis existiert
            folder_result = self.create_folder_structure(self.temp_path)

            result = PathResult(path=temp_file_path)
            result.existed = temp_file_path.exists()
            result.created = folder_result.success

            if folder_result.error:
                result.error = folder_result.error

            return result

        except Exception as e:
            error_msg = f"Failed to resolve temp path: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def create_folder_structure(self, path: Path, max_retries: int = 3) -> PathResult:
        """
        Erstellt Ordnerstruktur für gegebenen Pfad mit Retry-Logik.

        Diese Methode ist die EINZIGE die Ordner erstellen sollte.
        Verwendet Retry-Mechanismus für transiente Fehler (z.B. temporäre Locks).

        Args:
            path: Pfad für den Ordner erstellt werden sollen
            max_retries: Maximale Anzahl Wiederholungsversuche (default: 3)

        Returns:
            PathResult mit Erstellungs-Status
        """
        import time

        try:
            if path.exists():
                return PathResult(path=path, existed=True)

            # Retry-Logik für transiente Fehler
            last_error = None
            for attempt in range(max_retries):
                try:
                    # Erstelle Ordner mit parents=True
                    path.mkdir(parents=True, exist_ok=True)

                    self.logger.debug(f"Created folder structure: {path}")

                    result = PathResult(path=path, created=True)
                    if attempt > 0:
                        result.add_warning(
                            f"Folder created after {attempt + 1} attempts"
                        )
                    return result

                except OSError as e:
                    last_error = e
                    # Bei transientem Fehler: kurz warten und retry
                    if attempt < max_retries - 1:
                        self.logger.warning(
                            f"Attempt {attempt + 1}"
                            f"/{max_retries} failed: "
                            f"{e}, retrying..."
                        )
                        time.sleep(
                            0.1 * (attempt + 1)
                        )  # Exponential backoff: 0.1s, 0.2s, 0.3s
                        continue
                    # Letzter Versuch fehlgeschlagen
                    break

            # Alle Versuche fehlgeschlagen
            if isinstance(last_error, PermissionError):
                error_msg = (
                    f"Permission denied creating folder {path}: {str(last_error)}"
                )
                self.logger.error(error_msg)
                return PathResult(path=path, error=error_msg)
            else:
                error_msg = (
                    f"Failed to create folder {path} "
                    f"after {max_retries} attempts: "
                    f"{str(last_error)}"
                )
                self.logger.error(error_msg)
                return PathResult(path=path, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error creating folder {path}: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=path, error=error_msg)

    def move_file(
        self, source_path: Path, target_context: StorageContextData, filename: str
    ) -> PathResult:
        """
        Verschiebt Datei von temporärem Pfad zum finalen Storage-Pfad.

        Args:
            source_path: Quell-Pfad der Datei
            target_context: Storage-Kontext für Ziel-Pfad
            filename: Dateiname im Zielpfad

        Returns:
            PathResult mit finalem Pfad
        """
        try:
            import shutil

            # Löse Ziel-Pfad auf
            storage_result = self.resolve_storage_path(
                target_context, create_folders=True
            )
            if not storage_result.success:
                return PathResult(
                    path=Path(),
                    error=f"Cannot resolve target path: {storage_result.error}",
                )

            # Bereite Ziel-Datei vor
            clean_filename = self._clean_filename(filename)
            target_path = storage_result.path / clean_filename

            # Prüfe Quell-Datei
            if not source_path.exists():
                return PathResult(
                    path=target_path, error=f"Source file does not exist: {source_path}"
                )

            # Verschiebe Datei
            shutil.move(str(source_path), str(target_path))

            self.logger.info(f"File moved successfully: {source_path} -> {target_path}")
            return PathResult(path=target_path, created=True)

        except Exception as e:
            error_msg = f"Failed to move file {source_path}: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Räumt alte temporäre Dateien auf.

        Args:
            max_age_hours: Maximales Alter in Stunden

        Returns:
            Cleanup-Statistiken
        """
        try:
            import time

            if not self.temp_path.exists():
                return {"cleaned_files": 0, "errors": []}

            current_time = time.time()
            cutoff_time = current_time - (max_age_hours * 3600)

            cleaned_files = []
            errors = []

            for temp_file in self.temp_path.rglob("*"):
                if temp_file.is_file():
                    try:
                        if temp_file.stat().st_mtime < cutoff_time:
                            temp_file.unlink()
                            cleaned_files.append(str(temp_file))
                            self.logger.debug(f"Cleaned temp file: {temp_file}")
                    except Exception as e:
                        error_msg = f"Failed to clean {temp_file}: {str(e)}"
                        errors.append(error_msg)
                        self.logger.warning(error_msg)

            self.logger.info(
                f"Temp cleanup completed: {len(cleaned_files)} files cleaned"
            )
            return {
                "cleaned_files": len(cleaned_files),
                "cleaned_paths": cleaned_files,
                "errors": errors,
            }

        except Exception as e:
            error_msg = f"Temp cleanup failed: {str(e)}"
            self.logger.error(error_msg)
            return {"cleaned_files": 0, "errors": [error_msg]}

    def _clean_path_component(self, component: str) -> str:
        """
        Bereinigt Pfad-Komponente für Dateisystem-Kompatibilität.

        Args:
            component: Original Pfad-Komponente

        Returns:
            Bereinigte Pfad-Komponente
        """
        if not component or not isinstance(component, str):
            return "Unknown"

        # Ersetze NUR problematische Zeichen für Windows-Dateisystem
        # Umlaute (ä, ö, ü, ß) BLEIBEN ERHALTEN - NTFS unterstützt Unicode!
        replacements = {
            " ": "_",
            "/": "-",
            "\\": "-",
            ":": "-",
            "*": "",
            "?": "",
            '"': "",
            "<": "",
            ">": "",
            "|": "-",
        }

        cleaned = component
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        # Entferne aufeinanderfolgende Unterstriche/Bindestriche
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        while "--" in cleaned:
            cleaned = cleaned.replace("--", "-")

        # Entferne führende/trailing Zeichen
        cleaned = cleaned.strip("_-. ")

        # Fallback wenn komplett leer
        return cleaned if cleaned else "Unknown"

    def _clean_filename(self, filename: str) -> str:
        """
        Bereinigt Dateiname für Dateisystem-Sicherheit.

        Args:
            filename: Original Dateiname

        Returns:
            Bereinigter Dateiname
        """
        if not filename or not isinstance(filename, str):
            from datetime import datetime

            return f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Separiere Name und Extension
        path_obj = Path(filename)
        name_part = path_obj.stem
        extension = path_obj.suffix

        # Bereinige Name-Teil
        cleaned_name = self._clean_path_component(name_part)

        # Stelle sicher dass Extension sicher ist
        if extension:
            # Entferne potentiell gefährliche Zeichen aus Extension
            clean_extension = "".join(c for c in extension if c.isalnum() or c == ".")
        else:
            clean_extension = ""

        return f"{cleaned_name}{clean_extension}"

    def get_path_preview(self, context: StorageContextData) -> str:
        """
        Erstellt Pfad-Preview ohne Ordner zu erstellen.
        Nützlich für UI-Anzeigen.

        Args:
            context: Storage-Kontext

        Returns:
            Pfad als String für Preview
        """
        try:
            # Verwende resolve_storage_path ohne create_folders
            result = self.resolve_storage_path(context, create_folders=False)
            return (
                str(result.path)
                if result.success
                else "Fehler: Pfad konnte nicht bestimmt werden"
            )

        except Exception as e:
            self.logger.warning(f"Path preview failed: {e}")
            return f"Fehler: {str(e)}"

    def validate_path_safety(self, path: Path) -> Dict[str, Any]:
        """
        Validiert Pfad-Sicherheit gegen Directory Traversal etc.

        Args:
            path: Zu validierender Pfad

        Returns:
            Validierungs-Ergebnis
        """
        try:
            # Löse Pfad auf und normalisiere
            resolved_path = path.resolve()
            base_resolved = self.base_storage_path.resolve()

            # Prüfe dass Pfad innerhalb der Basis liegt
            try:
                resolved_path.relative_to(base_resolved)
                is_safe = True
                safety_issue = None
            except ValueError:
                is_safe = False
                safety_issue = "Path escapes base storage directory"

            return {
                "is_safe": is_safe,
                "resolved_path": str(resolved_path),
                "safety_issue": safety_issue,
                "warnings": [],
            }

        except Exception as e:
            return {
                "is_safe": False,
                "resolved_path": str(path),
                "safety_issue": f"Path validation error: {str(e)}",
                "warnings": ["Path validation failed"],
            }

    def resolve_delivery_slip_path(
        self,
        supplier_name: str,
        document_type: DocumentType = DocumentType.LIEFERSCHEIN,
        create_folders: bool = True,
    ) -> PathResult:
        """
        Spezielle Pfad-Auflösung für Lieferscheine.

        Erstellt FLACHE Pfad-Struktur: Base / Supplier / Lieferscheine
        Beispiel: C:/Users/krueg/Medealis/Wareneingang/Primec/Lieferscheine/

        VORTEIL: Alle Lieferscheine eines Lieferanten in einem Ordner
        → Löst Zeitfenster-Problem beim Merge

        Args:
            supplier_name: Name des Lieferanten
            document_type: Dokument-Typ (sollte LIEFERSCHEIN sein)
            create_folders: Ob Ordnerstruktur erstellt werden soll

        Returns:
            PathResult mit Lieferschein-Pfad
        """
        try:
            self.logger.info(
                "DEBUG: Resolving delivery slip path "
                f"for supplier: '{supplier_name}'"
            )

            # Validiere Eingaben
            if not supplier_name or not isinstance(supplier_name, str):
                return PathResult(
                    path=Path(),
                    error="Invalid supplier name provided",
                )

            # NUTZE STORAGE_CONTEXT NORMALISIERUNG
            # Die Normalisierung gibt bereits
            # dateisystem-sichere Namen zurück
            from .storage_context import storage_context

            normalized_supplier = storage_context._basic_supplier_normalization(
                supplier_name
            )
            self.logger.info(
                "DEBUG: Normalized supplier: "
                f"'{supplier_name}' -> "
                f"'{normalized_supplier}'"
            )

            # Baue FLACHEN Lieferschein-Pfad
            delivery_slip_path = (
                self.base_storage_path / normalized_supplier / "Lieferscheine"
            )

            self.logger.info("DEBUG: FLAT delivery slip path: " f"{delivery_slip_path}")

            # Erstelle Pfad-Ergebnis
            result = PathResult(path=delivery_slip_path)
            result.existed = delivery_slip_path.exists()

            # Erstelle Ordnerstruktur falls gewünscht
            if create_folders:
                folder_result = self.create_folder_structure(delivery_slip_path)
                result.created = folder_result.success and not result.existed
                if folder_result.error:
                    result.error = folder_result.error
                    return result
                result.warnings.extend(folder_result.warnings)

            self.logger.info(f"Delivery slip path resolved: {delivery_slip_path}")
            return result

        except Exception as e:
            error_msg = f"Failed to resolve delivery slip path: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def resolve_server_delivery_slip_path(
        self,
        supplier_name: str,
        document_type: DocumentType = DocumentType.LIEFERSCHEIN,
        create_folders: bool = True,
    ) -> PathResult:
        r"""
        SERVER-Version der Lieferschein-Pfad-Auflösung
        (UNC-Pfad).

        Erstellt FLACHE Pfad-Struktur auf Server:
        \\10.190.140.10\...\{Supplier}\Lieferscheine

        VORTEIL: Zentrale Server-Speicherung
        IDENTISCH zur lokalen Struktur

        Args:
            supplier_name: Name des Lieferanten
            document_type: Dokument-Typ (sollte LIEFERSCHEIN sein)
            create_folders: Ob Ordnerstruktur erstellt werden soll

        Returns:
            PathResult mit Server-Lieferschein-Pfad
        """
        try:
            self.logger.info(
                f"Resolving SERVER delivery slip path for supplier: '{supplier_name}'"
            )

            # Validiere Eingaben
            if not supplier_name or not isinstance(supplier_name, str):
                return PathResult(path=Path(), error="Invalid supplier name provided")

            # Validiere dass Server verfügbar ist (prüfe direkt den UNC-Pfad)
            if not self.server_storage_path.exists():
                srv = self.server_storage_path
                error_msg = (
                    "Server-Speicherpfad nicht "
                    f"verfügbar: {srv}\n"
                    "Bitte Netzwerkverbindung "
                    "prüfen oder IT-Support "
                    "kontaktieren."
                )
                self.logger.error(error_msg)
                return PathResult(path=Path(), error=error_msg)

            # NUTZE STORAGE_CONTEXT NORMALISIERUNG
            # Die Normalisierung gibt bereits
            # dateisystem-sichere Namen zurück
            from .storage_context import storage_context

            normalized_supplier = storage_context._basic_supplier_normalization(
                supplier_name
            )
            self.logger.info(
                f"Normalized supplier: '{supplier_name}' → '{normalized_supplier}'"
            )

            # Baue FLACHEN Server-Lieferschein-Pfad (OHNE Jahr/Monat!)
            server_delivery_slip_path = (
                self.server_storage_path / normalized_supplier / "Lieferscheine"
            )

            self.logger.info(f"Server delivery slip path: {server_delivery_slip_path}")

            # Erstelle Pfad-Ergebnis
            result = PathResult(path=server_delivery_slip_path)
            result.existed = server_delivery_slip_path.exists()

            # Erstelle Ordnerstruktur falls gewünscht
            if create_folders:
                folder_result = self.create_folder_structure(server_delivery_slip_path)
                result.created = folder_result.success and not result.existed
                if folder_result.error:
                    result.error = folder_result.error
                    return result
                result.warnings.extend(folder_result.warnings)

            self.logger.info(
                f"Server delivery slip path resolved: {server_delivery_slip_path}"
            )
            return result

        except Exception as e:
            error_msg = f"Failed to resolve server delivery slip path: {str(e)}"
            self.logger.error(error_msg)
            return PathResult(path=Path(), error=error_msg)

    def generate_delivery_slip_filename(
        self,
        supplier_name: str,
        delivery_number: Optional[str] = None,
        delivery_date: Optional[str] = None,
        original_filename: Optional[str] = None,
        file_extension: Optional[str] = None,
    ) -> str:
        """
        Generiert standardisierten Dateinamen für Lieferscheine.

        Args:
            supplier_name: Lieferantenname
            delivery_number: Lieferscheinnummer (wenn erkannt)
            delivery_date: Lieferdatum (wenn erkannt)
            original_filename: Original-Dateiname
            file_extension: Datei-Extension

        Returns:
            Generierter Dateiname
        """
        try:
            from datetime import datetime

            # Basis-Komponenten
            components = ["Lieferschein"]

            # Lieferant hinzufügen (gekürzt)
            if supplier_name:
                clean_supplier = self._clean_path_component(supplier_name)
                # Kürze langen Lieferanten-Namen
                if len(clean_supplier) > 15:
                    clean_supplier = clean_supplier[:15]
                components.append(clean_supplier)

            # Lieferscheinnummer wenn verfügbar
            if delivery_number:
                clean_delivery = self._clean_path_component(delivery_number)
                components.append(clean_delivery)

            # Datum - verwende Lieferdatum oder heutiges Datum
            if delivery_date:
                components.append(delivery_date)
            else:
                components.append(datetime.now().strftime("%Y-%m-%d"))

            # Original-Dateiname als Referenz (optional)
            if original_filename and len(components) < 4:
                # Entferne Extension und kürze
                base_name = Path(original_filename).stem
                clean_base = self._clean_path_component(base_name)
                if len(clean_base) > 20:
                    clean_base = clean_base[:20]
                components.append(clean_base)

            # Füge Komponenten zusammen
            filename = "_".join(components)

            # Extension hinzufügen
            if not file_extension:
                file_extension = ".pdf"  # Standard für Lieferscheine
            elif not file_extension.startswith("."):
                file_extension = "." + file_extension

            return self._clean_filename(filename + file_extension)

        except Exception as e:
            self.logger.error(f"Error generating delivery slip filename: {e}")
            # Fallback-Name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"Lieferschein_{timestamp}.pdf"

    def resolve_sharepoint_path(
        self, document_type: Union[str, DocumentType], context: StorageContextData
    ) -> str:
        """
        Löst SharePoint-Pfad für Dokument-Typ auf.

        EINZIGE Methode für SharePoint-Pfad-Erstellung.
        Verwendet konsistente Pfad-Struktur basierend auf DocumentType.

        Args:
            document_type: Dokument-Typ (string oder DocumentType enum)
            context: Storage Kontext mit Supplier, Article, Batch etc.

        Returns:
            SharePoint-Pfad als String (mit forward slashes)

        Pfad-Struktur:
            - Lieferscheine: .../Produktionsunterlagen/
              {Supplier}/Lieferscheine
            - Alle anderen Docs (inkl. Barcodes):
              .../{Supplier}/{Manufacturer}/{Article}/
              {Batch}/{Delivery}

        Hinweis:
            - Keyence_QR-Codes_Messprogramme/ ist die
              QUELLE für QR-Code-Bilder
            - Barcode-Labels werden NICHT dort
              gespeichert, sondern im Artikel-Ordner!
        """
        try:
            # Konvertiere zu DocumentType falls String
            if isinstance(document_type, str):
                doc_type = DocumentType.from_string(document_type)
                if doc_type is None:
                    self.logger.warning(
                        f"Unknown document type '{document_type}', using default path"
                    )
                    doc_type = DocumentType.PDB  # Fallback
            else:
                doc_type = document_type

            # Hole Pfad-Komponenten aus Kontext
            supplier = (
                context.supplier_normalized
                if context.supplier_normalized
                else "Unknown"
            )
            kompatibilitaet = (
                context.kompatibilitaet if context.kompatibilitaet else "Unknown"
            )
            article = context.article_number if context.article_number else "Unknown"
            batch = context.batch_number if context.batch_number else "Unknown"
            delivery = context.delivery_number if context.delivery_number else "Unknown"

            # Bereinige Komponenten für SharePoint (Umlaute bleiben erhalten!)
            # Nur problematische Zeichen ersetzen: Leerzeichen, Slashes
            clean_supplier = (
                supplier.replace(" ", "_").replace("/", "-").replace("\\", "-")
            )
            clean_manufacturer = (
                kompatibilitaet.replace(" ", "_").replace("/", "-").replace("\\", "-")
            )
            clean_article = (
                article.replace(" ", "_").replace("/", "-").replace("\\", "-")
            )
            clean_batch = batch.replace(" ", "_").replace("/", "-").replace("\\", "-")
            clean_delivery = (
                delivery.replace(" ", "_").replace("/", "-").replace("\\", "-")
            )

            # Pfad-Mapping basierend auf Dokument-Typ
            if doc_type == DocumentType.LIEFERSCHEIN:
                # Lieferscheine unter Produktionsunterlagen/{Supplier}/Lieferscheine
                # (Flache Struktur für Lieferscheine)
                return (
                    f"{self.sharepoint_produktionsunterlagen}"
                    f"/{clean_supplier}/Lieferscheine"
                )

            else:
                # Alle anderen Dokumente (PDB, Begleitschein, Sichtkontrolle, etc.)
                # Vollständige Pfad-Hierarchie:
                # {Supplier}/{Manufacturer}/{Article}/
                # {Batch}/{Delivery}
                return (
                    f"{self.sharepoint_produktionsunterlagen}/"
                    f"{clean_supplier}/"
                    f"{clean_manufacturer}/"
                    f"{clean_article}/"
                    f"{clean_batch}/"
                    f"{clean_delivery}"
                )

        except Exception as e:
            error_msg = f"Failed to resolve SharePoint path: {str(e)}"
            self.logger.error(error_msg)
            # Fallback zu Produktionsunterlagen
            return self.sharepoint_produktionsunterlagen


# Global instance - SINGLE POINT OF ACCESS
path_resolver = PathResolver()
