"""
Document Types & Template Definitions

Zentrale Definition aller unterstützten Dokument-Typen und deren Template-Konfigurationen.
Basiert auf der Analyse der bestehenden WordTemplateService-Funktionen und verfügbaren Templates.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """
    Alle unterstützten Dokument-Typen.
    Basiert auf den bestehenden WordTemplateService create_*_document() Methoden.
    """
    PDB = "pdb"                                    # Produktdatenblatt (Fo00040)
    BEGLEITSCHEIN = "begleitschein"                # Begleitschein (Fo00057)
    SICHTKONTROLLE = "sichtkontrolle"              # Sichtkontrolle (Fo00141)
    WARENEINGANGSKONTROLLE = "wareneingangskontrolle"  # Wareneingangskontrolle (Fo0113)
    INCOMING_GOODS_INSPECTION = "incoming_goods_inspection"  # EN Checklist (Fo00040_Checklist)
    BARCODE = "barcode"                            # PNG Barcode files
    LIEFERSCHEIN = "lieferschein"                  # Lieferschein (Scanned delivery slips)

    @property
    def display_name(self) -> str:
        """Benutzerfreundlicher Anzeigename."""
        display_names = {
            self.PDB: "Produktdatenblatt",
            self.BEGLEITSCHEIN: "Begleitschein",
            self.SICHTKONTROLLE: "Sichtkontrolle",
            self.WARENEINGANGSKONTROLLE: "Wareneingang",
            self.INCOMING_GOODS_INSPECTION: "Incoming Goods Inspection",
            self.BARCODE: "Barcode",
            self.LIEFERSCHEIN: "Lieferschein"
        }
        return display_names.get(self, self.value)

    @property
    def description(self) -> str:
        """Detaillierte Beschreibung des Dokument-Typs."""
        descriptions = {
            self.PDB: "Produktdatenblatt für medizinische/dentale Komponenten mit vollständigen Spezifikationen",
            self.BEGLEITSCHEIN: "Begleitschein für Lieferungen mit Prüfprotokoll und Checkliste",
            self.SICHTKONTROLLE: "Sichtkontrollprotokoll für visuelle Qualitätsprüfung",
            self.WARENEINGANGSKONTROLLE: "Wareneingangskontrolle mit Prüfkriterien und Dokumentation",
            self.INCOMING_GOODS_INSPECTION: "English checklist for incoming goods inspection procedures",
            self.BARCODE: "PNG Barcode-Dateien für Artikel-, Chargen- und Lieferungsnummern",
            self.LIEFERSCHEIN: "Gescannte Lieferscheine für automatische Speicherung und Verarbeitung"
        }
        return descriptions.get(self, f"Document type: {self.value}")

    @classmethod
    def from_string(cls, type_string: str) -> Optional['DocumentType']:
        """Erstellt DocumentType aus String (case-insensitive)."""
        try:
            type_string = type_string.lower().strip()
            for doc_type in cls:
                if doc_type.value == type_string:
                    return doc_type

            # Aliases für Kompatibilität
            aliases = {
                'produktdatenblatt': cls.PDB,
                'pdb_document': cls.PDB,
                'begleit': cls.BEGLEITSCHEIN,
                'delivery_slip': cls.BEGLEITSCHEIN,
                'sicht': cls.SICHTKONTROLLE,
                'visual': cls.SICHTKONTROLLE,
                'wareneingang': cls.WARENEINGANGSKONTROLLE,
                'goods_receipt': cls.WARENEINGANGSKONTROLLE,
                'inspection': cls.INCOMING_GOODS_INSPECTION,
                'checklist': cls.INCOMING_GOODS_INSPECTION,
                'lieferschein': cls.LIEFERSCHEIN,
                'delivery_note': cls.LIEFERSCHEIN,
                'shipping_slip': cls.LIEFERSCHEIN
            }

            return aliases.get(type_string)

        except Exception as e:
            logger.warning(f"Could not parse document type '{type_string}': {e}")
            return None

    @classmethod
    def get_all_types(cls) -> List['DocumentType']:
        """Gibt alle verfügbaren Document Types zurück."""
        return list(cls)


@dataclass
class TemplateInfo:
    """
    Template-Informationen für einen Dokument-Typ.
    Definiert alle Eigenschaften und Requirements eines Templates.
    """
    # TEMPLATE IDENTIFICATION
    name: str                                      # Benutzerfreundlicher Name
    filename: str                                  # Template-Dateiname (in resources/templates/)
    document_type: DocumentType                    # Zugehöriger Document Type

    # PLACEHOLDER REQUIREMENTS
    required_placeholders: List[str] = field(default_factory=list)  # Muss vorhanden sein
    optional_placeholders: List[str] = field(default_factory=list)  # Kann vorhanden sein

    # TEMPLATE METADATA
    description: str = ""                          # Detaillierte Beschreibung
    version: str = "1.0"                          # Template-Version
    author: str = "Medealis System"               # Template-Autor
    last_modified: str = ""                       # Letzte Änderung

    # OUTPUT OPTIONS
    supported_formats: List[str] = field(default_factory=lambda: ["docx"])  # Unterstützte Ausgabeformate
    default_filename_pattern: str = ""            # Pattern für Dateiname (z.B. "PDB_{article}_{batch}")

    # PROCESSING OPTIONS
    requires_barcode: bool = False                # Benötigt Barcode-Integration
    supports_conditional_content: bool = False   # Unterstützt conditional placeholders
    has_tables: bool = False                      # Enthält Tabellen die befüllt werden
    has_images: bool = False                      # Enthält Bilder/Logos

    def get_all_placeholders(self) -> List[str]:
        """Gibt alle Placeholder (required + optional) zurück."""
        return self.required_placeholders + self.optional_placeholders

    def validate_placeholders(self, available_placeholders: List[str]) -> Dict[str, List[str]]:
        """
        Validiert verfügbare Placeholder gegen Template-Requirements.

        Args:
            available_placeholders: Liste der verfügbaren Placeholder

        Returns:
            Dictionary mit missing_required und missing_optional Listen
        """
        missing_required = [p for p in self.required_placeholders
                          if p not in available_placeholders]
        missing_optional = [p for p in self.optional_placeholders
                          if p not in available_placeholders]

        return {
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'has_all_required': len(missing_required) == 0
        }

    def generate_filename(self, context: Dict[str, Any]) -> str:
        """
        Generiert Dateiname basierend auf Pattern und Context.

        Args:
            context: Generation context data

        Returns:
            Generierter Dateiname
        """
        try:
            if not self.default_filename_pattern:
                # Fallback pattern
                timestamp = context.get('timestamp', 'unknown')
                # Use first supported format as fallback extension
                extension = self.supported_formats[0] if self.supported_formats else "docx"
                return f"{self.document_type.value}_{timestamp}.{extension}"

            # Ersetze Placeholder im Pattern
            filename = self.default_filename_pattern
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in filename:
                    # Bereinige Wert für Dateiname - filesystem-sichere Zeichen
                    safe_value = str(value).replace('/', '-').replace('\\', '-').replace(':', '-').replace('.', '_')
                    filename = filename.replace(placeholder, safe_value)

            # Stelle sicher dass Datei-Extension vorhanden ist
            # Use the first supported format as default extension
            default_extension = self.supported_formats[0] if self.supported_formats else "docx"

            # Check if filename already has a proper extension
            has_valid_extension = any(filename.endswith(f'.{fmt}') for fmt in self.supported_formats)

            if not has_valid_extension:
                filename += f'.{default_extension}'

            return filename

        except Exception as e:
            logger.error(f"Error generating filename: {e}")
            return f"{self.document_type.value}_{self.version}.docx"


# TEMPLATE REGISTRY - Zentrale Definition aller Templates
TEMPLATE_REGISTRY: Dict[DocumentType, TemplateInfo] = {

    DocumentType.PDB: TemplateInfo(
        name="Produktdatenblatt",
        filename="Fo00040_PDB_Template.docx",
        document_type=DocumentType.PDB,
        description="Produktdatenblatt für medizinische/dentale Komponenten mit vollständigen technischen Spezifikationen",
        version="1.0",

        # Placeholder basierend auf WordTemplateService.create_pdb_document() Analyse
        required_placeholders=[
            "artikelno",           # Artikelnummer
            "lotno",               # Chargennummer
            "lieferant",           # Lieferantenname
            "datum",               # Erstellungsdatum
        ],
        optional_placeholders=[
            "qty",                 # Menge
            "menge",               # Deutsche Menge
            "designation",         # Bezeichnung
            "bezeichnung",         # Deutsche Bezeichnung
            "delivery_number",     # Lieferscheinnummer
            "lieferscheinnr",      # Deutsche Lieferscheinnummer
            "supplier_name",       # Lieferantenname (EN)
            "manufacturer",        # Hersteller
            "hersteller",          # Deutscher Hersteller
            "employee_name",       # Mitarbeitername
            "mitarbeitername"      # Deutscher Mitarbeitername
        ],

        default_filename_pattern="PDB_{artikelno}_{lotno}_{datum}",
        supported_formats=["docx", "pdf"],
        has_tables=True,
        supports_conditional_content=True
    ),

    DocumentType.BEGLEITSCHEIN: TemplateInfo(
        name="Begleitschein",
        filename="Fo00057_Begleitschein.docx",
        document_type=DocumentType.BEGLEITSCHEIN,
        description="Begleitschein für Lieferungen mit Prüfprotokoll und Checkliste",
        version="1.0",

        # Placeholder basierend auf WordTemplateService.create_begleitschein_document()
        required_placeholders=[
            "datum",               # Datum
            "LSnr",                # Lieferscheinnummer
            "lieferant",           # Lieferant
        ],
        optional_placeholders=[
            "name",                # Mitarbeitername
            "lieferantnr",         # Lieferantennummer
            "orderdate",           # Bestelldatum
            "itemnr",              # Artikelnummer
            "lotno",               # Chargennummer
            "chargennr",           # Chargennummer (für Dateiname)
            "qty",                 # Menge
            # Prüfkriterien (als X oder leer)
            "VP", "nVP",           # Verpackung OK/nicht OK
            "MZ", "nMZ",           # Materialzeugnis
            "MP", "nMP",           # Mess-Protokoll
            "B", "nB",             # Beschichtung
            "HZ", "nHZ",           # Härtezeugnis
            "WZ", "nWZ",           # Weitere Zeugnisse
            "EDV", "nEDV",         # EDV Nummer
            "BG", "nBG"            # Begleitschein
        ],

        default_filename_pattern="Begleitschein_{chargennr}_{datum}",  # FIXED: Use batch number instead of delivery number to avoid confusion with Lieferschein
        supported_formats=["docx"],
        has_tables=True,
        supports_conditional_content=True
    ),

    DocumentType.SICHTKONTROLLE: TemplateInfo(
        name="Sichtkontrolle",
        filename="Fo00141_Sichtkontrolle.docx",
        document_type=DocumentType.SICHTKONTROLLE,
        description="Sichtkontrollprotokoll für visuelle Qualitätsprüfung von Komponenten",
        version="1.0",

        # Placeholder basierend auf WordTemplateService.create_sichtkontrolle_document()
        required_placeholders=[
            "artikelno",           # Artikelnummer
            "lotno",               # Chargennummer
            "date",                # Datum
            "qty"                  # Menge
        ],
        optional_placeholders=[
            "lieferant",           # Lieferant
            "name",                # Prüfer-Name
            "ausschuss",           # Ausschuss-Menge
            "ausschussquote",      # Ausschussquote
            "delivery_number",     # Lieferscheinnummer
            "designation",         # Bezeichnung
            "unit",                # Einheit
            "supplier_name"        # Lieferantenname
        ],

        default_filename_pattern="Sichtkontrolle_{artikelno}_{lotno}_{date}",
        supported_formats=["docx", "pdf"],
        has_tables=False,
        supports_conditional_content=False
    ),

    DocumentType.WARENEINGANGSKONTROLLE: TemplateInfo(
        name="Wareneingang",
        filename="Fo0113_Wareneingangskontrolle.docx",
        document_type=DocumentType.WARENEINGANGSKONTROLLE,
        description="Wareneingangskontrolle mit Prüfkriterien und Dokumentation",
        version="1.0",

        # Placeholder basierend auf WordTemplateService.create_wareneingangskontrolle_document()
        required_placeholders=[
            "we_date",             # Wareneingangsdatum
            "artikel",             # Artikel
            "charge"               # Charge
        ],
        optional_placeholders=[
            "delivery_number",     # Lieferscheinnummer
            "lieferant",           # Lieferant
            "qty",                 # Menge
            "name",                # Mitarbeitername
            "date",                # Datum
            "datum"                # Deutscher Datum
        ],

        default_filename_pattern="WEK_{charge}",
        supported_formats=["docx"],
        has_tables=True,
        supports_conditional_content=False
    ),

    DocumentType.INCOMING_GOODS_INSPECTION: TemplateInfo(
        name="Incoming Goods Inspection",
        filename="Fo00040_Checklist for incoming goods inspection.docx",
        document_type=DocumentType.INCOMING_GOODS_INSPECTION,
        description="English checklist for incoming goods inspection procedures",
        version="1.0",

        # Placeholder basierend auf WordTemplateService.create_incoming_goods_inspection_document()
        required_placeholders=[
            "artikel",             # Article
            "charge",              # Batch/Charge
            "delivery_number"      # Delivery Number
        ],
        optional_placeholders=[
            "supplier_name",       # Supplier
            "date",                # Date
            "qty",                 # Quantity
            "employee_name",       # Employee
            "artikelno",           # Article Number (alias)
            "lotno",               # Lot Number (alias)
            "lieferant",           # Supplier (German)
            "name"                 # Name (alias)
        ],

        default_filename_pattern="Inspection_Checklist_{artikel}_{charge}_{delivery_number}",
        supported_formats=["docx"],
        has_tables=True,
        supports_conditional_content=False
    ),

    DocumentType.BARCODE: TemplateInfo(
        name="Barcode",
        filename="",  # No template file - PNG generation
        document_type=DocumentType.BARCODE,
        description="PNG Barcode-Dateien für Artikel-, Chargen- und Lieferungsnummern",
        version="1.0",

        # Barcode generation - based on Item.generate_barcode_content()
        required_placeholders=[
            "article_number",      # Artikelnummer
            "batch_number",        # Chargennummer
            "delivery_number",     # Liefernummer
        ],
        optional_placeholders=[
            "barcode_type",        # Barcode type (CODE128, CODE39, etc.)
            "filename_prefix",     # Prefix for filename
            "open_after_creation", # Whether to open after creation
        ],

        default_filename_pattern="barcode_{artikelno}_{lotno}_{delivery_number}_{datum}",
        supported_formats=["png"],
        has_tables=False,
        supports_conditional_content=False
    ),

    DocumentType.LIEFERSCHEIN: TemplateInfo(
        name="Lieferschein",
        filename="",  # No template file - scanned PDF/image storage
        document_type=DocumentType.LIEFERSCHEIN,
        description="Gescannte Lieferscheine für automatische Speicherung nach Lieferant organisiert",
        version="1.0",

        # Required for delivery slip storage and organization
        required_placeholders=[
            "supplier_name",       # Lieferantenname (für Ordner-Struktur)
        ],
        optional_placeholders=[
            "delivery_number",     # Lieferscheinnummer (wenn erkannt)
            "delivery_date",       # Lieferdatum (wenn erkannt)
            "scan_date",           # Datum des Scans
            "original_filename",   # Original-Dateiname
            "file_extension",      # Datei-Extension (.pdf, .jpg, etc.)
            "auto_detected",       # Ob automatisch erkannt oder manuell gesetzt
        ],

        default_filename_pattern="Lieferschein_{delivery_number}_{scan_date}",
        supported_formats=["pdf", "jpg", "jpeg", "png", "tiff"],
        has_tables=False,
        supports_conditional_content=False
    )
}


def get_template_info(document_type: DocumentType) -> Optional[TemplateInfo]:
    """
    Gibt TemplateInfo für DocumentType zurück.

    Args:
        document_type: Document Type

    Returns:
        TemplateInfo oder None wenn nicht gefunden
    """
    return TEMPLATE_REGISTRY.get(document_type)


def get_all_template_info() -> List[TemplateInfo]:
    """Gibt alle verfügbaren TemplateInfo zurück."""
    return list(TEMPLATE_REGISTRY.values())


def get_supported_document_types() -> List[DocumentType]:
    """Gibt alle unterstützten DocumentTypes zurück."""
    return list(TEMPLATE_REGISTRY.keys())


def validate_document_type_support(document_type: DocumentType) -> bool:
    """
    Prüft ob DocumentType unterstützt wird.

    Args:
        document_type: Zu prüfender DocumentType

    Returns:
        True wenn unterstützt
    """
    return document_type in TEMPLATE_REGISTRY


def get_template_requirements_summary() -> Dict[str, Dict[str, Any]]:
    """
    Gibt Übersicht über alle Template-Requirements zurück.
    Nützlich für Dokumentation und Debugging.

    Returns:
        Dictionary mit Template-Requirements für jeden DocumentType
    """
    summary = {}

    for doc_type, template_info in TEMPLATE_REGISTRY.items():
        summary[doc_type.value] = {
            'name': template_info.name,
            'filename': template_info.filename,
            'required_placeholders': template_info.required_placeholders,
            'optional_placeholders': template_info.optional_placeholders,
            'total_placeholders': len(template_info.get_all_placeholders()),
            'supported_formats': template_info.supported_formats,
            'has_tables': template_info.has_tables,
            'supports_conditional_content': template_info.supports_conditional_content
        }

    return summary


# Template Path Helper Functions
def get_template_path(document_type: DocumentType, base_template_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Gibt vollständigen Pfad zum Template zurück.

    Args:
        document_type: Document Type
        base_template_dir: Basis Template-Verzeichnis (optional)

    Returns:
        Path zum Template oder None
    """
    template_info = get_template_info(document_type)
    if not template_info:
        return None

    if base_template_dir is None:
        # Standard Template-Verzeichnis
        base_template_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "templates"

    return base_template_dir / template_info.filename


def check_template_exists(document_type: DocumentType, base_template_dir: Optional[Path] = None) -> bool:
    """
    Prüft ob Template-Datei existiert.

    Args:
        document_type: Document Type
        base_template_dir: Basis Template-Verzeichnis (optional)

    Returns:
        True wenn Template existiert
    """
    template_path = get_template_path(document_type, base_template_dir)
    return template_path is not None and template_path.exists()


def get_missing_templates(base_template_dir: Optional[Path] = None) -> List[DocumentType]:
    """
    Gibt Liste der DocumentTypes zurück deren Templates nicht existieren.

    Args:
        base_template_dir: Basis Template-Verzeichnis (optional)

    Returns:
        Liste der DocumentTypes mit fehlenden Templates
    """
    missing = []

    for doc_type in get_supported_document_types():
        if not check_template_exists(doc_type, base_template_dir):
            missing.append(doc_type)

    return missing