"""
Storage Validator Service - Validierung und Sicherheit für Dokument-Speicherung

Zentraler Validator für alle Storage-Operationen.
Prüft Daten-Integrität, Pfad-Sicherheit, Dateiformate und Berechtigungen.
"""

import logging
import mimetypes
import hashlib
import os
import stat
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from .storage_context import StorageContextData

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validierungs-Stufen für verschiedene Anwendungsfälle."""
    STRICT = "strict"       # Maximale Sicherheit, alle Prüfungen
    STANDARD = "standard"   # Standard-Prüfungen für normale Operationen
    PERMISSIVE = "permissive"  # Minimale Prüfungen für Kompatibilität


class SecurityRisk(Enum):
    """Sicherheitsrisiko-Kategorien."""
    CRITICAL = "critical"   # Sofort blockieren
    HIGH = "high"          # Warnung, aber erlauben
    MEDIUM = "medium"      # Info-Warnung
    LOW = "low"           # Debug-Info


@dataclass
class ValidationResult:
    """
    Ergebnis einer Validierungs-Operation.
    Enthält Status, Fehler, Warnungen und Sicherheits-Informationen.
    """
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    security_risks: List[Tuple[SecurityRisk, str]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.security_risks is None:
            self.security_risks = []
        if self.metadata is None:
            self.metadata = {}

    def add_error(self, message: str):
        """Fügt Fehler hinzu und setzt is_valid auf False."""
        self.errors.append(message)
        self.is_valid = False
        logger.error(f"Validation error: {message}")

    def add_warning(self, message: str):
        """Fügt Warnung hinzu."""
        self.warnings.append(message)
        logger.warning(f"Validation warning: {message}")

    def add_security_risk(self, risk_level: SecurityRisk, message: str):
        """Fügt Sicherheitsrisiko hinzu."""
        self.security_risks.append((risk_level, message))
        if risk_level == SecurityRisk.CRITICAL:
            self.add_error(f"Critical security risk: {message}")
        else:
            logger.warning(f"Security risk ({risk_level.value}): {message}")

    @property
    def has_critical_risks(self) -> bool:
        """True wenn kritische Sicherheitsrisiken vorliegen."""
        return any(risk[0] == SecurityRisk.CRITICAL for risk in self.security_risks)


class StorageValidator:
    """
    Zentraler Validator für alle Storage-Operationen.

    Führt umfassende Validierungen durch:
    - Datenintegrität und Vollständigkeit
    - Pfad-Sicherheit (Directory Traversal etc.)
    - Dateiformat und -größe Prüfungen
    - Berechtigung-Validierung
    - Malware-Scanning (Basic)
    """

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.logger = logger
        self.validation_level = validation_level

        # Konfigurierbare Limits
        self.max_file_size = 100 * 1024 * 1024  # 100MB default
        self.max_filename_length = 255
        self.max_path_length = 1000

        # Erlaubte Dateitypen (MIME types)
        self.allowed_mime_types = {
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
            'application/msword',  # .doc
            'text/plain',
            'image/png',
            'image/jpeg',
            'image/gif',
            'application/vnd.ms-excel',  # .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/zip'  # für komprimierte Dokumente
        }

        # Gefährliche Datei-Extensions
        self.dangerous_extensions = {
            '.exe', '.scr', '.com', '.bat', '.cmd', '.pif', '.vbs', '.js',
            '.jar', '.msi', '.dll', '.sys', '.bin', '.run', '.app', '.deb', '.rpm'
        }

    def validate_document_data(
        self,
        document_data: Union[bytes, memoryview],
        filename: str,
        expected_mime_type: Optional[str] = None
    ) -> ValidationResult:
        """
        Validiert Dokument-Daten vor Speicherung.

        Args:
            document_data: Binärdaten des Dokuments
            filename: Dateiname
            expected_mime_type: Erwarteter MIME-Type (optional)

        Returns:
            ValidationResult mit Prüfungsergebnissen
        """
        result = ValidationResult(is_valid=True)

        try:
            # Convert to bytes if needed for consistent processing
            if isinstance(document_data, memoryview):
                document_data_bytes = bytes(document_data)
            elif isinstance(document_data, bytes):
                document_data_bytes = document_data
            else:
                document_data_bytes = bytes(document_data)

            # Basic Validierungen
            if not document_data_bytes:
                result.add_error("Document data is empty")
                return result

            if not filename:
                result.add_error("Filename is required")
                return result

            # Dateigröße prüfen
            file_size = len(document_data_bytes)
            if file_size > self.max_file_size:
                result.add_error(f"File size ({file_size} bytes) exceeds limit ({self.max_file_size} bytes)")

            if file_size == 0:
                result.add_error("File is empty (0 bytes)")

            # MIME Type Validierung
            mime_result = self._validate_mime_type(document_data_bytes, filename, expected_mime_type)
            if not mime_result.is_valid:
                result.errors.extend(mime_result.errors)
                result.warnings.extend(mime_result.warnings)

            # Dateiname Validierung
            filename_result = self._validate_filename(filename)
            if not filename_result.is_valid:
                result.errors.extend(filename_result.errors)
                result.warnings.extend(filename_result.warnings)

            # Malware-Scanning (Basic)
            if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.STANDARD]:
                malware_result = self._basic_malware_scan(document_data_bytes, filename)
                result.security_risks.extend(malware_result.security_risks)

            # Metadaten hinzufügen
            result.metadata.update({
                'file_size': file_size,
                'detected_mime_type': self._detect_mime_type(document_data_bytes, filename),
                'file_hash': self._calculate_file_hash(document_data_bytes),
                'validation_level': self.validation_level.value
            })

            return result

        except Exception as e:
            result.add_error(f"Document validation failed: {str(e)}")
            return result

    def validate_storage_permissions(self, path: Path) -> ValidationResult:
        """
        Prüft Storage-Berechtigungen für Pfad.

        Args:
            path: Zu prüfender Pfad

        Returns:
            ValidationResult mit Berechtigungs-Status
        """
        result = ValidationResult(is_valid=True)

        try:
            # Erstelle Test-Verzeichnis falls es nicht existiert
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    result.add_warning("Created directory for permission testing")
                except PermissionError:
                    result.add_error(f"Cannot create directory: {path}")
                    return result

            # Prüfe Schreibberechtigung
            if not os.access(path, os.W_OK):
                result.add_error(f"No write permission for: {path}")

            # Prüfe Leseberechtigung
            if not os.access(path, os.R_OK):
                result.add_error(f"No read permission for: {path}")

            # Prüfe ob Pfad ein Verzeichnis ist
            if path.exists() and not path.is_dir():
                result.add_error(f"Path is not a directory: {path}")

            # Test-Datei Schreibversuch (nur bei STRICT)
            if self.validation_level == ValidationLevel.STRICT:
                test_result = self._test_file_operations(path)
                if not test_result.is_valid:
                    result.errors.extend(test_result.errors)

            result.metadata['path'] = str(path)
            result.metadata['exists'] = path.exists()
            result.metadata['is_directory'] = path.is_dir() if path.exists() else None

            return result

        except Exception as e:
            result.add_error(f"Permission validation failed: {str(e)}")
            return result

    def sanitize_filename(self, filename: str) -> Tuple[str, List[str]]:
        """
        Bereinigt Dateiname für sichere Speicherung.

        Args:
            filename: Original Dateiname

        Returns:
            Tuple von (bereinigter_name, warnungen)
        """
        warnings = []

        if not filename:
            return "document_unknown.pdf", ["Empty filename provided"]

        original_filename = filename

        # Dateiname-Länge prüfen
        if len(filename) > self.max_filename_length:
            filename = filename[:self.max_filename_length]
            warnings.append(f"Filename truncated to {self.max_filename_length} characters")

        # Gefährliche Zeichen entfernen
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in dangerous_chars:
            if char in filename:
                filename = filename.replace(char, '_')
                warnings.append(f"Replaced dangerous character '{char}' with '_'")

        # Control characters entfernen
        filename = ''.join(char for char in filename if ord(char) >= 32)

        # Mehrfache Punkte reduzieren (außer vor Extension)
        parts = filename.split('.')
        if len(parts) > 2:
            # Behalte nur den letzten Punkt für Extension
            base_name = '_'.join(parts[:-1])
            extension = parts[-1]
            filename = f"{base_name}.{extension}"
            warnings.append("Reduced multiple dots in filename")

        # Prüfe auf gefährliche Extensions
        extension = Path(filename).suffix.lower()
        if extension in self.dangerous_extensions:
            filename = filename[:-len(extension)] + '.txt'
            warnings.append(f"Changed dangerous extension {extension} to .txt")

        # Fallback falls Dateiname leer wird
        if not filename.strip() or filename.strip() == '.':
            from datetime import datetime
            filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            warnings.append("Generated fallback filename")

        if filename != original_filename:
            warnings.append(f"Filename sanitized: '{original_filename}' -> '{filename}'")

        return filename, warnings

    def validate_storage_context(self, context: StorageContextData) -> ValidationResult:
        """
        Validiert Storage-Kontext für Vollständigkeit und Konsistenz.

        Args:
            context: Storage-Kontext zu validieren

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        try:
            # Basis-Validierung
            if not context.is_complete_for_storage():
                issues = context.get_validation_issues()
                for issue in issues:
                    if "erforderlich" in issue.lower():
                        result.add_error(issue)
                    else:
                        result.add_warning(issue)

            # Datenqualität prüfen
            if context.completeness_score < 0.5:
                result.add_error(f"Storage context completeness too low: {context.completeness_score:.1%}")
            elif context.completeness_score < 0.8:
                result.add_warning(f"Low storage context completeness: {context.completeness_score:.1%}")

            # Konsistenz-Prüfungen
            consistency_result = self._validate_context_consistency(context)
            result.errors.extend(consistency_result.errors)
            result.warnings.extend(consistency_result.warnings)

            # Sicherheits-Prüfungen für Context-Daten
            security_result = self._validate_context_security(context)
            result.security_risks.extend(security_result.security_risks)

            result.metadata.update({
                'completeness_score': context.completeness_score,
                'context_source': context.context_source,
                'validation_timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord('', 0, '', 0, '', (), None)) if logger.handlers else 'unknown'
            })

            return result

        except Exception as e:
            result.add_error(f"Context validation failed: {str(e)}")
            return result

    def _validate_mime_type(
        self,
        document_data: bytes,
        filename: str,
        expected_mime_type: Optional[str] = None
    ) -> ValidationResult:
        """Validiert MIME-Type von Dokumentdaten."""
        result = ValidationResult(is_valid=True)

        try:
            detected_mime = self._detect_mime_type(document_data, filename)

            if not detected_mime:
                result.add_warning("Could not detect MIME type")
                return result

            # Prüfe gegen erlaubte Types
            if detected_mime not in self.allowed_mime_types:
                if self.validation_level == ValidationLevel.STRICT:
                    result.add_error(f"MIME type not allowed: {detected_mime}")
                else:
                    result.add_warning(f"Potentially unsafe MIME type: {detected_mime}")

            # Prüfe gegen erwarteten Type
            if expected_mime_type and detected_mime != expected_mime_type:
                result.add_warning(f"MIME type mismatch: expected {expected_mime_type}, got {detected_mime}")

            result.metadata['detected_mime_type'] = detected_mime

            return result

        except Exception as e:
            result.add_error(f"MIME type validation failed: {str(e)}")
            return result

    def _validate_filename(self, filename: str) -> ValidationResult:
        """Validiert Dateiname auf Sicherheit."""
        result = ValidationResult(is_valid=True)

        try:
            if len(filename) > self.max_filename_length:
                result.add_error(f"Filename too long: {len(filename)} > {self.max_filename_length}")

            # Prüfe auf gefährliche Zeichen
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            found_dangerous = [char for char in dangerous_chars if char in filename]
            if found_dangerous:
                result.add_security_risk(
                    SecurityRisk.MEDIUM,
                    f"Dangerous characters in filename: {found_dangerous}"
                )

            # Prüfe auf Directory Traversal
            if '..' in filename or filename.startswith('/') or ':' in filename:
                result.add_security_risk(
                    SecurityRisk.HIGH,
                    "Potential directory traversal in filename"
                )

            # Prüfe Extension
            extension = Path(filename).suffix.lower()
            if extension in self.dangerous_extensions:
                result.add_security_risk(
                    SecurityRisk.CRITICAL,
                    f"Dangerous file extension: {extension}"
                )

            return result

        except Exception as e:
            result.add_error(f"Filename validation failed: {str(e)}")
            return result

    def _basic_malware_scan(self, document_data: Union[bytes, memoryview], filename: str) -> ValidationResult:
        """Basis Malware-Scanning (einfache Heuristiken)."""
        result = ValidationResult(is_valid=True)

        try:
            # Handle different data types (bytes, memoryview, etc.)
            if isinstance(document_data, memoryview):
                document_data_bytes = bytes(document_data)
            elif isinstance(document_data, bytes):
                document_data_bytes = document_data
            else:
                document_data_bytes = bytes(document_data)

            # PE Header Check (Windows executables)
            if document_data_bytes[:2] == b'MZ':
                result.add_security_risk(
                    SecurityRisk.CRITICAL,
                    "File appears to be a Windows executable"
                )

            # Script-Content Check
            script_indicators = [b'<script', b'javascript:', b'vbscript:', b'powershell']

            # Convert document_data to lowercase bytes for comparison
            try:
                # Convert to lowercase for case-insensitive search
                document_lower = document_data_bytes.lower()

                for indicator in script_indicators:
                    indicator_lower = indicator.lower()
                    if indicator_lower in document_lower:
                        result.add_security_risk(
                            SecurityRisk.HIGH,
                            f"Potentially malicious script content detected: {indicator.decode('utf-8', errors='ignore')}"
                        )

            except Exception as e:
                logger.warning(f"Malware scan failed: {e}")
                # Continue without malware check rather than failing completely

            # Archive Bombs Check (einfach)
            if len(document_data_bytes) < 1000 and filename.lower().endswith('.zip'):
                result.add_security_risk(
                    SecurityRisk.MEDIUM,
                    "Suspiciously small ZIP file - potential zip bomb"
                )

            return result

        except Exception as e:
            result.add_warning(f"Malware scan failed: {str(e)}")
            return result

    def _validate_context_consistency(self, context: StorageContextData) -> ValidationResult:
        """Validiert interne Konsistenz des Storage-Kontexts."""
        result = ValidationResult(is_valid=True)

        # Batch-Number Format Check
        if context.batch_number and not context.batch_number.startswith('P-'):
            if len(context.batch_number) < 6:
                result.add_warning("Batch number appears too short")

        # Article-Number Consistency
        if context.article_number and context.manufacturer:
            # Prüfe ob Article-Number zum Manufacturer passt
            article_upper = context.article_number.upper()
            if context.manufacturer == "C-Tech" and not article_upper.startswith('CT'):
                result.add_warning("Article number doesn't match manufacturer pattern")

        return result

    def _validate_context_security(self, context: StorageContextData) -> ValidationResult:
        """Prüft Storage-Kontext auf Sicherheitsrisiken."""
        result = ValidationResult(is_valid=True)

        # Injection-Versuche in Strings prüfen
        string_fields = [
            context.batch_number, context.delivery_number, context.article_number,
            context.supplier_name, context.manufacturer
        ]

        for field_value in string_fields:
            if field_value and isinstance(field_value, str):
                if any(dangerous in field_value.lower() for dangerous in ['../', '..\\', 'script', 'exec']):
                    result.add_security_risk(
                        SecurityRisk.HIGH,
                        f"Potentially dangerous content in context field: {field_value[:50]}..."
                    )

        return result

    def _test_file_operations(self, path: Path) -> ValidationResult:
        """Testet tatsächliche Datei-Operationen."""
        result = ValidationResult(is_valid=True)

        try:
            import tempfile
            import os

            # Test-Datei erstellen
            test_file = path / f"test_permissions_{os.getpid()}.tmp"

            try:
                with open(test_file, 'w') as f:
                    f.write("permission test")

                # Test-Datei lesen
                with open(test_file, 'r') as f:
                    content = f.read()
                    if content != "permission test":
                        result.add_error("File read/write test failed")

                # Test-Datei löschen
                test_file.unlink()

            except Exception as e:
                result.add_error(f"File operations test failed: {str(e)}")
                # Cleanup bei Fehler
                if test_file.exists():
                    try:
                        test_file.unlink()
                    except:
                        pass

            return result

        except Exception as e:
            result.add_error(f"Permission test setup failed: {str(e)}")
            return result

    def _detect_mime_type(self, document_data: bytes, filename: str) -> Optional[str]:
        """Erkennt MIME-Type aus Dateidaten und Name."""
        try:
            # Versuche MIME-Type aus Daten zu erkennen
            import magic
            detected_mime = magic.from_buffer(document_data, mime=True)
            return detected_mime
        except ImportError:
            # Fallback: Nur Dateiendung verwenden
            mime_type, _ = mimetypes.guess_type(filename)
            return mime_type
        except Exception:
            return None

    def _calculate_file_hash(self, document_data: bytes) -> str:
        """Berechnet SHA-256 Hash der Datei."""
        return hashlib.sha256(document_data).hexdigest()


# Global instance - SINGLE POINT OF ACCESS
storage_validator = StorageValidator()