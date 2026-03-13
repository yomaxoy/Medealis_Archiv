"""
Generation Models - Datenklassen für Document Generation

Definiert alle Datenstrukturen für den Document Generation Workflow:
- GenerationContext: Einheitlicher Context für alle Dokument-Generierung
- GenerationResult: Ergebnisse von Generierungs-Operationen
- BatchGenerationResult: Ergebnisse von Batch-Operationen
- ProcessingOptions: Konfiguration für Dokument-Verarbeitung
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProcessingOptions:
    """
    Verarbeitungs-Optionen für Dokument-Generation.
    Steuert wie Dokumente verarbeitet und gespeichert werden.
    """

    output_format: str = "docx"  # docx, pdf (zukünftig)
    open_after_creation: bool = False  # Dokument nach Erstellung öffnen
    save_to_folder: bool = True  # In Ordnerstruktur speichern
    custom_filename: Optional[str] = None  # Benutzerdefinierter Dateiname
    custom_output_path: Optional[Path] = None  # Benutzerdefinierter Ausgabepfad
    overwrite_existing: bool = False  # Bestehende Dateien überschreiben

    # Template-spezifische Optionen
    template_version: str = "latest"  # Template-Version verwenden
    include_metadata: bool = True  # Metadaten in Dokument einbetten

    # Validierungs-Optionen
    strict_validation: bool = False  # Strenge Validierung der Eingaben
    require_all_placeholders: bool = False  # Alle Placeholder müssen gefüllt sein


@dataclass
class GenerationContext:
    """
    Einheitlicher Context für Dokument-Generation.

    Kombiniert StorageContext-Daten mit generation-spezifischen Informationen.
    Stellt alle benötigten Daten für Template-Verarbeitung bereit.
    """

    # PFLICHT-IDENTIFIKATION (von StorageContext übernommen)
    batch_number: str
    delivery_number: str
    article_number: str = ""

    # SUPPLIER, HERSTELLER & KOMPATIBILITÄT
    supplier_name: str = ""
    supplier_normalized: str = ""
    hersteller: str = ""  # Verantwortlicher Hersteller des Abutments
    kompatibilitaet: str = ""  # Kompatible Implantatmarke (aus Artikelnummer)

    # ITEM DETAILS
    quantity: int = 0
    unit: str = ""
    description: str = ""

    # DELIVERY INFORMATION
    delivery_date: str = ""
    order_number: str = ""
    employee_name: str = ""

    # GENERATION-SPEZIFISCHE DATEN
    document_type: "DocumentType" = None  # noqa: F821
    generation_timestamp: datetime = field(default_factory=datetime.now)
    template_version: str = "1.0"

    # FLEXIBLE DATEN
    placeholders: Dict[str, Any] = field(
        default_factory=dict
    )  # Zusätzliche Placeholder
    custom_data: Dict[str, Any] = field(
        default_factory=dict
    )  # Dokument-spezifische Daten

    # METADATEN
    context_source: str = "generation"  # Quelle der Context-Daten
    completeness_score: float = 0.0  # Vollständigkeit der Daten (0-1)

    def to_placeholder_dict(self) -> Dict[str, str]:
        """
        Konvertiert GenerationContext zu Placeholder-Dictionary.
        Wird von PlaceholderEngine für Template-Ersetzung verwendet.

        Returns:
            Dictionary mit allen verfügbaren Placeholder-Werten
        """
        try:
            # Basis-Placeholder aus Context-Feldern
            placeholder_dict = {
                # Standard-Placeholder (kompatibel mit bestehenden Templates)
                "artikelno": self.article_number,
                "artikelnr": self.article_number,  # Für Begleitschein Template
                "itemnr": self.article_number,  # Für Begleitschein Template
                # Added for barcode template compatibility
                "article_number": self.article_number,
                "lotno": self.batch_number,
                "lotnr": self.batch_number,  # Für Begleitschein Template
                "chargennr": self.batch_number,  # Für Begleitschein Dateiname
                # Added for barcode template compatibility
                "batch_number": self.batch_number,
                # Kombinierte Placeholders für
                # Wareneingangskontrolle
                "artikel": (
                    f"{self.article_number}_{self.batch_number}"
                    if self.article_number and self.batch_number
                    else self.article_number
                ),
                "charge": self.batch_number,  # Chargennummer separat
                "lieferant": self.supplier_name,
                "datum": self.generation_timestamp.strftime("%d.%m.%Y"),
                "date": self.generation_timestamp.strftime("%d.%m.%Y"),
                "qty": str(self.quantity),
                "menge": str(self.quantity),
                "einheit": self.unit,
                "unit": self.unit,
                "designation": self.description,
                "bezeichnung": self.description,
                # Delivery-Placeholder
                "LSnr": self.delivery_number,
                "delivery_number": self.delivery_number,
                "lieferscheinnr": self.delivery_number,
                "lieferdatum": self.delivery_date,
                "delivery_date": self.delivery_date,
                "bestellnummer": self.order_number,
                "order_number": self.order_number,
                "ordernr": self.order_number,  # Für Begleitschein Template
                # Für Begleitschein Template (fallback)
                "orderdate": self.delivery_date,
                # Supplier, Hersteller & Kompatibilität
                "supplier_name": self.supplier_name,
                "lieferantenname": self.supplier_name,
                "hersteller": self.hersteller,
                "kompatibilitaet": self.kompatibilitaet,
                # Backward-Compat: manufacturer zeigt Kompatibilitätsmarke
                "manufacturer": self.kompatibilitaet,
                "lieferantnr": self.supplier_normalized or "",  # Lieferantennummer
                "itemnrL": ".-",  # Artikelnummer Lieferant (Standard: .-)
                # Employee & Timestamps
                "name": self.employee_name,
                "mitarbeitername": self.employee_name,
                "employee_name": self.employee_name,
                "erstellungsdatum": self.generation_timestamp.strftime("%d.%m.%Y"),
                "erstellungszeit": self.generation_timestamp.strftime("%H:%M:%S"),
                "timestamp": self.generation_timestamp.strftime("%d.%m.%Y %H:%M:%S"),
                # Metadaten
                "template_version": self.template_version,
                "document_type": self.document_type.value if self.document_type else "",
                # Zertifikat-Platzhalter (Standard: leer,
                # werden durch custom_data überschrieben)
                "VP": "",  # Verpackung in Ordnung
                "nVP": "X",  # Verpackung nicht in Ordnung (Standard)
                "MZ": "",  # Materialzeugnis
                "nMZ": "X",  # Materialzeugnis nicht vorhanden
                "MP": "",  # Mess-Protokoll
                "nMP": "X",  # Mess-Protokoll nicht vorhanden
                "B": "",  # Beschichtung
                "nB": "X",  # Beschichtung nicht vorhanden
                "HZ": "",  # Härtezeugnis
                "nHZ": "X",  # Härtezeugnis nicht vorhanden
                "WZ": "",  # weitere Zeugnisse
                "nWZ": "X",  # weitere Zeugnisse nicht vorhanden
                "EDV": "",  # EDV Nummer
                "nEDV": "X",  # EDV Nummer nicht vorhanden
                "BG": "",  # Begleitschein beigefügt
                "nBG": "X",  # Begleitschein nicht beigefügt
                # Sichtkontrolle-spezifische Platzhalter
                "ausschuss": "0",  # Ausschussmenge
                "ausschussquote": "0%",  # Ausschussquote
                # PDB-spezifische Mengen-Platzhalter
                # (Standard-Werte, überschrieben via
                # custom_data)
                "orderq": "-",  # FIXED: "-" statt '0' wenn keine Bestellmenge
                "deliveryq": str(self.quantity)
                if self.quantity
                else "-",  # FIXED: "-" wenn keine Liefermenge
                "order_quantity": "-",  # FIXED: "-" statt '0'
                "delivery_quantity": str(self.quantity)
                if self.quantity
                else "-",  # FIXED: "-" wenn keine Liefermenge
                "ordered_quantity": "-",  # FIXED: "-" statt '0'
                "delivery_slip_quantity": "-",  # FIXED: "-" statt '0'
                "LSQ": "-",  # FIXED: "-" statt '0' (PDB Template Placeholder [[LSQ]])
            }

            # Füge custom placeholders hinzu (überschreibt Standard-Werte)
            if self.placeholders:
                placeholder_dict.update(
                    {k: str(v) for k, v in self.placeholders.items()}
                )

            # Füge custom_data als placeholders hinzu
            if self.custom_data:
                for key, value in self.custom_data.items():
                    # Konvertiere zu String für Template-Verwendung
                    if isinstance(value, bool):
                        placeholder_dict[key] = "X" if value else ""
                    elif isinstance(value, (datetime,)):
                        placeholder_dict[key] = (
                            value.strftime("%d.%m.%Y")
                            if hasattr(value, "strftime")
                            else str(value)
                        )
                    else:
                        placeholder_dict[key] = (
                            str(value) if value is not None else "-"
                        )  # FIXED: "-" statt ""

            # Spezial-Fall: qty sollte delivery_quantity entsprechen, falls verfügbar
            if (
                "delivery_quantity" in placeholder_dict
                and placeholder_dict["delivery_quantity"] != "0"
            ):
                placeholder_dict["qty"] = placeholder_dict["delivery_quantity"]
                placeholder_dict["menge"] = placeholder_dict["delivery_quantity"]

            return placeholder_dict

        except Exception as e:
            logger.error(f"Error creating placeholder dictionary: {e}")
            # Fallback: Return minimal placeholder dict
            return {
                "artikelno": self.article_number,
                "lotno": self.batch_number,
                "datum": datetime.now().strftime("%d.%m.%Y"),
                "error": f"Context conversion error: {str(e)}",
            }

    def validate_for_document_type(
        self, document_type: "DocumentType"  # noqa: F821
    ) -> "ValidationResult":
        """
        Validiert Context für spezifischen Document Type.

        Args:
            document_type: Document Type für den validiert wird

        Returns:
            ValidationResult mit Validierungs-Status
        """
        from .validation_models import ValidationResult

        validation_result = ValidationResult(is_valid=True)

        try:
            # Basis-Validierung für alle Document Types
            if not self.batch_number:
                validation_result.add_error("batch_number ist erforderlich")

            if not self.delivery_number:
                validation_result.add_error("delivery_number ist erforderlich")

            # Document-spezifische Validierung
            if document_type:
                required_fields = self._get_required_fields_for_document_type(
                    document_type
                )

                for field_name in required_fields:
                    field_value = getattr(self, field_name, None)
                    if not field_value or (
                        isinstance(field_value, str) and not field_value.strip()
                    ):
                        validation_result.add_error(
                            f"{field_name} ist erforderlich für {document_type.value}"
                        )

            # Completeness Score Warnung
            if self.completeness_score < 0.7:
                validation_result.add_warning(
                    f"Niedrige Datenqualität ({self.completeness_score:.1%})"
                )

            return validation_result

        except Exception as e:
            validation_result.add_error(f"Context validation failed: {str(e)}")
            return validation_result

    def _get_required_fields_for_document_type(
        self, document_type: "DocumentType"  # noqa: F821
    ) -> List[str]:
        """Gibt erforderliche Felder für Document Type zurück."""
        # Import hier um Circular Import zu vermeiden
        from .document_types import DocumentType

        field_requirements = {
            DocumentType.PDB: ["article_number", "batch_number", "supplier_name"],
            DocumentType.BEGLEITSCHEIN: ["delivery_number", "supplier_name"],
            DocumentType.SICHTKONTROLLE: ["article_number", "batch_number", "quantity"],
            DocumentType.WARENEINGANGSKONTROLLE: [
                "article_number",
                "batch_number",
                "delivery_date",
            ],
            DocumentType.INCOMING_GOODS_INSPECTION: [
                "article_number",
                "batch_number",
                "delivery_number",
            ],
        }

        return field_requirements.get(
            document_type, ["batch_number", "delivery_number"]
        )

    def merge_with_storage_context(
        self, storage_context: "StorageContextData"  # noqa: F821
    ) -> "GenerationContext":
        """
        Merged mit StorageContext aus Phase 1 Storage System.

        Args:
            storage_context: StorageContextData aus Phase 1

        Returns:
            Neuer GenerationContext mit kombinierten Daten
        """
        try:
            # Erstelle neuen Context mit Storage-Daten
            merged_context = GenerationContext(
                # Übernehme Storage-Context Daten
                batch_number=storage_context.batch_number,
                delivery_number=storage_context.delivery_number,
                article_number=storage_context.article_number,
                supplier_name=storage_context.supplier_name,
                supplier_normalized=storage_context.supplier_normalized,
                hersteller=storage_context.hersteller,
                kompatibilitaet=storage_context.kompatibilitaet,
                quantity=storage_context.quantity,
                unit=storage_context.unit,
                description=storage_context.article_description,
                delivery_date=storage_context.delivery_date,
                order_number=storage_context.order_number,
                employee_name=storage_context.employee_name,
                # Behalte Generation-spezifische Daten
                document_type=self.document_type,
                generation_timestamp=self.generation_timestamp,
                template_version=self.template_version,
                placeholders=self.placeholders.copy(),
                custom_data=self.custom_data.copy(),
                # Metadaten
                context_source="merged",
                completeness_score=max(
                    self.completeness_score, storage_context.completeness_score
                ),
            )

            return merged_context

        except Exception as e:
            logger.error(f"Error merging with storage context: {e}")
            return self  # Return original context on error


@dataclass
class GenerationResult:
    """
    Ergebnis einer einzelnen Dokument-Generation.

    Enthält alle Informationen über eine erfolgreiche oder fehlgeschlagene
    Dokument-Generierung.
    """

    success: bool
    document_path: Optional[Path] = None
    document_type: Optional["DocumentType"] = None  # noqa: F821
    template_used: str = ""
    generation_time: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Zusätzliche Ergebnis-Informationen
    template_version: str = ""
    placeholder_count: int = 0
    context_completeness: float = 0.0
    file_size: int = 0

    # PDF-Conversion Support (wird von WordConverter gesetzt)
    pdf_path: Optional[Path] = None
    conversion_method: Optional[str] = None
    pdf_conversion_time: float = 0.0

    def __post_init__(self):
        """Post-init processing für GenerationResult."""
        if self.document_path and isinstance(self.document_path, str):
            self.document_path = Path(self.document_path)

        # PDF path auch konvertieren wenn String
        if self.pdf_path and isinstance(self.pdf_path, str):
            self.pdf_path = Path(self.pdf_path)

        # Berechne file_size falls Pfad existiert
        if self.document_path and self.document_path.exists():
            try:
                self.file_size = self.document_path.stat().st_size
            except Exception:
                self.file_size = 0

    def add_warning(self, message: str):
        """Fügt Warnung hinzu."""
        self.warnings.append(message)
        logger.warning(f"Generation warning: {message}")

    def set_error(self, error_message: str):
        """Setzt Fehler und markiert als nicht erfolgreich."""
        self.error = error_message
        self.success = False
        logger.error(f"Generation error: {error_message}")

    def get_summary(self) -> str:
        """Gibt kurze Zusammenfassung des Ergebnisses zurück."""
        if self.success:
            size_mb = self.file_size / (1024 * 1024) if self.file_size > 0 else 0
            return (
                f"✅ {self.document_type.value if self.document_type else 'Document'} "
                f"generated in {self.generation_time:.2f}s "
                f"({size_mb:.1f}MB)"
            )
        else:
            return f"❌ Generation failed: {self.error}"


@dataclass
class BatchGenerationResult:
    """
    Ergebnis einer Batch-Generation (mehrere Dokumente).

    Fasst die Ergebnisse mehrerer Dokument-Generierungen zusammen.
    """

    overall_success: bool
    results: List[GenerationResult] = field(default_factory=list)
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_generation_time: float = 0.0
    batch_errors: List[str] = field(default_factory=list)

    # Batch-spezifische Metadaten
    batch_id: str = ""
    batch_timestamp: datetime = field(default_factory=datetime.now)
    requested_document_types: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-init processing für BatchGenerationResult."""
        # Berechne Statistiken aus Results
        self.total_documents = len(self.results)
        self.successful_documents = sum(1 for r in self.results if r.success)
        self.failed_documents = self.total_documents - self.successful_documents
        self.total_generation_time = sum(r.generation_time for r in self.results)

        # Overall success nur wenn alle erfolgreich
        self.overall_success = self.failed_documents == 0 and self.total_documents > 0

    def add_result(self, result: GenerationResult):
        """Fügt Einzel-Ergebnis hinzu und aktualisiert Statistiken."""
        self.results.append(result)
        self.__post_init__()  # Neuberechnung der Statistiken

    def add_batch_error(self, error_message: str):
        """Fügt Batch-Level Fehler hinzu."""
        self.batch_errors.append(error_message)
        self.overall_success = False
        logger.error(f"Batch error: {error_message}")

    def get_successful_results(self) -> List[GenerationResult]:
        """Gibt nur erfolgreiche Ergebnisse zurück."""
        return [r for r in self.results if r.success]

    def get_failed_results(self) -> List[GenerationResult]:
        """Gibt nur fehlgeschlagene Ergebnisse zurück."""
        return [r for r in self.results if not r.success]

    def get_summary(self) -> str:
        """Gibt detaillierte Zusammenfassung zurück."""
        if self.overall_success:
            return (
                f"Batch completed: "
                f"{self.successful_documents}"
                f"/{self.total_documents} "
                f"documents in "
                f"{self.total_generation_time:.2f}s"
            )
        else:
            return (
                f"⚠️ Batch partial: {self.successful_documents}/{self.total_documents} "
                f"successful, {self.failed_documents} failed"
            )

    def get_detailed_report(self) -> Dict[str, Any]:
        """Gibt detaillierten Report für Logging/Debugging zurück."""
        return {
            "batch_summary": self.get_summary(),
            "overall_success": self.overall_success,
            "statistics": {
                "total_documents": self.total_documents,
                "successful_documents": self.successful_documents,
                "failed_documents": self.failed_documents,
                "success_rate": self.successful_documents
                / max(self.total_documents, 1),
                "total_generation_time": self.total_generation_time,
                "average_generation_time": self.total_generation_time
                / max(self.total_documents, 1),
            },
            "successful_documents": [
                {
                    "type": r.document_type.value if r.document_type else "unknown",
                    "path": str(r.document_path),
                    "time": r.generation_time,
                }
                for r in self.get_successful_results()
            ],
            "failed_documents": [
                {
                    "type": r.document_type.value if r.document_type else "unknown",
                    "error": r.error,
                }
                for r in self.get_failed_results()
            ],
            "batch_errors": self.batch_errors,
            "batch_timestamp": self.batch_timestamp.isoformat(),
        }


# Separate Validation Models to avoid circular imports
@dataclass
class ValidationResult:
    """
    Ergebnis einer Validierungs-Operation.
    Separate Klasse um Circular Imports zu vermeiden.
    """

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Fügt Fehler hinzu und setzt is_valid auf False."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Fügt Warnung hinzu."""
        self.warnings.append(message)
