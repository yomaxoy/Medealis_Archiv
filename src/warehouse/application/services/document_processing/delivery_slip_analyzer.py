"""
Delivery Slip Analyzer - KI-basierte Lieferschein-Analyse

Analysiert gescannte Lieferscheine und extrahiert:
- Lieferanten-Name
- Lieferscheinnummer
- Lieferdatum
- Artikel-Informationen
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ....shared.caching import ttl_cache

logger = logging.getLogger(__name__)


@dataclass
class DeliverySlipAnalysisResult:
    """Ergebnis der Lieferschein-Analyse."""
    success: bool
    supplier_name: Optional[str] = None
    supplier_confidence: float = 0.0
    delivery_number: Optional[str] = None
    delivery_date: Optional[str] = None
    article_numbers: List[str] = None
    detected_items: List[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.article_numbers is None:
            self.article_numbers = []
        if self.detected_items is None:
            self.detected_items = []
        if self.warnings is None:
            self.warnings = []


class DeliverySlipAnalyzer:
    """
    KI-basierte Analyse von Lieferscheinen.

    Nutzt Claude API für intelligente Texterkennung und -extraktion.
    """

    def __init__(self):
        self.logger = logger
        self._claude_client = None

    def _get_claude_client(self):
        """Lazy loading des Claude API Clients."""
        if self._claude_client is None:
            try:
                from .claude_api_client import ClaudeAPIClient
                self._claude_client = ClaudeAPIClient()
            except ImportError:
                self.logger.error("Claude API Client not available")
                raise

        return self._claude_client

    @ttl_cache(seconds=300, maxsize=64, key_prefix="delivery_slip_analysis")
    def analyze_delivery_slip(
        self,
        document_data: bytes,
        filename: str,
        hint_supplier: Optional[str] = None
    ) -> DeliverySlipAnalysisResult:
        """
        Analysiert Lieferschein und extrahiert relevante Informationen.

        Args:
            document_data: Binärdaten des Lieferscheins
            filename: Original-Dateiname
            hint_supplier: Optional Hinweis auf Lieferant

        Returns:
            DeliverySlipAnalysisResult mit extrahierten Daten
        """
        try:
            self.logger.info(f"Analyzing delivery slip: {filename}")

            # 1. KI-ANALYSE - Create temporary file for Claude API
            import tempfile
            import os

            claude_client = self._get_claude_client()
            analysis_prompt = self._build_analysis_prompt(hint_supplier)

            # Create temporary file for Claude API (expects file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(document_data)
                temp_file_path = temp_file.name

            try:
                claude_result = claude_client.analyze_document(
                    document_path=temp_file_path,
                    prompt=analysis_prompt,
                    debug=False
                )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            if not claude_result or claude_result.get("error"):
                return DeliverySlipAnalysisResult(
                    success=False,
                    error=f"Claude analysis failed: {claude_result.get('error', 'Unknown error')}"
                )

            # 2. EXTRAHIERE STRUKTURIERTE DATEN
            result = self._extract_structured_data(claude_result, filename)

            # 3. VALIDIERUNG UND CONFIDENCE SCORING
            self._validate_and_score_results(result, hint_supplier)

            self.logger.info(f"Delivery slip analysis completed: {result.supplier_name} ({result.supplier_confidence:.1%})")
            return result

        except Exception as e:
            error_msg = f"Delivery slip analysis failed: {str(e)}"
            self.logger.error(error_msg)
            return DeliverySlipAnalysisResult(success=False, error=error_msg)

    def _build_analysis_prompt(self, hint_supplier: Optional[str] = None) -> str:
        """Erstellt KI-Prompt für Lieferschein-Analyse."""
        base_prompt = """
Analysiere diesen Lieferschein und extrahiere folgende Informationen:

HAUPTZIEL: Lieferanten-Identifikation
1. **Lieferanten-Name**: Vollständiger Firmenname des Absenders
2. **Lieferschein-Nummer**: Eindeutige Lieferschein-ID
3. **Lieferdatum**: Datum der Lieferung
4. **Artikel-Nummern**: Liste aller gelieferten Artikel
5. **Mengen**: Gelieferte Stückzahlen pro Artikel

ANTWORT-FORMAT (JSON):
```json
{
    "processing_status": "success|error",
    "supplier_detection": {
        "found": true|false,
        "name": "Vollständiger Lieferantenname",
        "confidence": 0.0-1.0,
        "location": "Wo im Dokument gefunden",
        "alternative_names": ["Andere gefundene Namen"]
    },
    "delivery_info": {
        "delivery_number": "Lieferscheinnummer",
        "delivery_date": "YYYY-MM-DD",
        "order_number": "Bestellnummer (falls vorhanden)"
    },
    "items": [
        {
            "article_number": "Artikelnummer",
            "description": "Artikelbeschreibung",
            "quantity": "Menge",
            "unit": "Einheit"
        }
    ],
    "document_quality": {
        "text_clarity": "good|medium|poor",
        "completeness": "complete|partial|incomplete"
    },
    "raw_text_sample": "Erste 500 Zeichen des erkannten Texts"
}
```

WICHTIGE HINWEISE:
- Suche nach Firmenlogos, Briefköpfen, Absender-Informationen
- Achte auf typische Lieferschein-Felder wie "Lieferant:", "Von:", "Absender:"
- Berücksichtige deutsche und englische Begriffe
- Gib realistische Confidence-Werte (0.8+ nur bei sehr klarer Erkennung)
"""

        if hint_supplier:
            base_prompt += f"""
ZUSÄTZLICHER HINWEIS: Der Lieferant könnte "{hint_supplier}" sein.
Prüfe dies, aber lass dich nicht davon beeinflussen falls der Text etwas anderes zeigt.
"""

        return base_prompt

    def _extract_structured_data(
        self,
        claude_result: Dict[str, Any],
        filename: str
    ) -> DeliverySlipAnalysisResult:
        """Extrahiert strukturierte Daten aus Claude-Antwort."""
        try:
            # Basis-Result
            result = DeliverySlipAnalysisResult(success=True)

            # Handle ACTUAL Claude Response Format (direct fields)
            # Supplier Info (direct fields)
            result.supplier_name = claude_result.get("supplier_name")
            if result.supplier_name:
                result.supplier_confidence = 0.9  # High confidence if supplier found

            # Delivery Info (direct fields)
            result.delivery_number = claude_result.get("delivery_number")
            result.delivery_date = claude_result.get("delivery_date")

            # Items (direct field)
            items = claude_result.get("items", [])
            result.detected_items = items
            result.article_numbers = [item.get("article_number") for item in items if item.get("article_number")]

            # Fallback: Try nested format for backward compatibility
            if not result.supplier_name:
                supplier_info = claude_result.get("supplier_detection", {})
                if supplier_info.get("found"):
                    result.supplier_name = supplier_info.get("name")
                    result.supplier_confidence = float(supplier_info.get("confidence", 0.0))

            if not result.delivery_number:
                delivery_info = claude_result.get("delivery_info", {})
                result.delivery_number = delivery_info.get("delivery_number")
                result.delivery_date = delivery_info.get("delivery_date")

            # Raw Text
            result.raw_text = claude_result.get("raw_text_sample", "")

            # Document Quality Warnings
            doc_quality = claude_result.get("document_quality", {})
            if doc_quality.get("text_clarity") == "poor":
                result.warnings.append("Schlechte Textqualität - Ergebnisse können ungenau sein")
            if doc_quality.get("completeness") == "incomplete":
                result.warnings.append("Dokument scheint unvollständig zu sein")

            self.logger.info(f"🔧 DEBUG: Extracted {len(result.detected_items)} items from Claude response")
            return result

        except Exception as e:
            self.logger.error(f"Error extracting structured data: {e}")
            return DeliverySlipAnalysisResult(
                success=False,
                error=f"Data extraction failed: {str(e)}"
            )

    def _validate_and_score_results(
        self,
        result: DeliverySlipAnalysisResult,
        hint_supplier: Optional[str] = None
    ):
        """Validiert und bewertet Analyse-Ergebnisse."""
        try:
            # Supplier Name Validation
            if result.supplier_name:
                # Bereinige Supplier Name
                result.supplier_name = self._clean_supplier_name(result.supplier_name)

                # Confidence Adjustment basierend auf Hint
                if hint_supplier and hint_supplier.lower() in result.supplier_name.lower():
                    result.supplier_confidence = min(result.supplier_confidence + 0.2, 1.0)
                    result.warnings.append("Confidence erhöht durch Lieferanten-Hinweis")

                # Minimum Confidence Check
                if result.supplier_confidence < 0.3:
                    result.warnings.append("Niedrige Confidence bei Lieferanten-Erkennung")

            # Delivery Number Validation
            if result.delivery_number:
                result.delivery_number = self._clean_delivery_number(result.delivery_number)

            # Date Validation
            if result.delivery_date:
                result.delivery_date = self._validate_date_format(result.delivery_date)

        except Exception as e:
            self.logger.warning(f"Validation failed: {e}")
            result.warnings.append(f"Validation warning: {str(e)}")

    def _clean_supplier_name(self, supplier_name: str) -> str:
        """Bereinigt Lieferanten-Namen."""
        if not supplier_name:
            return ""

        # Entferne common Prefixes/Suffixes
        cleaned = supplier_name.strip()

        # Entferne Adressen, Email etc.
        lines = cleaned.split('\n')
        if lines:
            # Nimm erste Zeile als Firmenname
            cleaned = lines[0].strip()

        # Entferne Email/Website Pattern
        cleaned = re.sub(r'\S+@\S+', '', cleaned)
        cleaned = re.sub(r'www\.\S+', '', cleaned)

        # Bereinige multiple Leerzeichen
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def _clean_delivery_number(self, delivery_number: str) -> str:
        """Bereinigt Lieferscheinnummer."""
        if not delivery_number:
            return ""

        # Entferne Whitespace und Sonderzeichen
        cleaned = delivery_number.strip()

        # Standardisiere Format (z.B. LS25-219)
        # Behalte Alphanumerisch + Bindestriche
        cleaned = re.sub(r'[^\w\-]', '', cleaned)

        return cleaned

    def _validate_date_format(self, date_string: str) -> str:
        """Validiert und normalisiert Datumsformat."""
        if not date_string:
            return ""

        try:
            # Versuche verschiedene Formate zu parsen
            date_formats = [
                "%Y-%m-%d",
                "%d.%m.%Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d"
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string, fmt)
                    # Gib im Standard-Format zurück
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # Falls Parsing fehlschlägt, gib Original zurück
            self.logger.warning(f"Could not parse date: {date_string}")
            return date_string

        except Exception as e:
            self.logger.warning(f"Date validation failed: {e}")
            return date_string

    def get_known_suppliers(self) -> List[str]:
        """
        Gibt Liste bekannter Lieferanten zurück.

        Returns:
            Liste von bekannten Lieferanten-Namen
        """
        try:
            # Hole bekannte Lieferanten aus Database
            from ...entity_services.supplier_service import SupplierService

            supplier_service = SupplierService()
            suppliers = supplier_service.get_all_suppliers()

            return [supplier.get("name", "") for supplier in suppliers if supplier.get("name")]

        except Exception as e:
            self.logger.warning(f"Could not load known suppliers: {e}")
            # Fallback zu häufigen Lieferanten
            return [
                "Primec",
                "PRIMEC",
                "Terrats Medical",
                "TERRATS",
                "Medealis",
                "Standard Implants",
                "Dental Implants"
            ]

    def suggest_supplier_from_filename(self, filename: str) -> Optional[str]:
        """
        Schlägt Lieferant basierend auf Dateiname vor.

        Args:
            filename: Dateiname

        Returns:
            Vorgeschlagener Lieferant oder None
        """
        try:
            filename_lower = filename.lower()

            # Häufige Patterns
            if "primec" in filename_lower:
                return "Primec"
            elif "medealis" in filename_lower:
                return "Medealis"
            elif "dental" in filename_lower:
                return "Dental Implants"
            elif "implant" in filename_lower:
                return "Standard Implants"

            return None

        except Exception as e:
            self.logger.debug(f"Filename suggestion failed: {e}")
            return None


# Global instance
delivery_slip_analyzer = DeliverySlipAnalyzer()