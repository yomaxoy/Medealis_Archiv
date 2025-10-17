"""
Document Validator - Schema-basierte Validierung für alle Dokumenttypen
Einfache Validierung ohne Over-Engineering
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class DocumentValidator:
    """
    Einfache Schema-basierte Validierung.
    Keine komplexen Pydantic Models - bewusst einfach gehalten.
    """

    def __init__(self):
        self.logger = logger

    def validate_document_data(
        self,
        data: Dict[str, Any],
        document_type: str,
        context: Dict[str, Any] = None
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validiert Dokument-Daten gegen erwartete Struktur.

        Args:
            data: Claude API Response
            document_type: "delivery", "order", "accompanying"
            context: Zusätzlicher Kontext

        Returns:
            (is_valid, cleaned_data, errors)
        """
        if context is None:
            context = {}

        errors = []
        is_valid = True

        try:
            # Basis-Validierung: Ist es ein Dictionary?
            if not isinstance(data, dict):
                errors.append("Response ist kein gültiges JSON-Objekt")
                return False, {}, errors

            # Dokumenttyp-spezifische Validierung
            if document_type == "delivery":
                is_valid, cleaned_data, validation_errors = self._validate_delivery_data(data)
            elif document_type == "order":
                is_valid, cleaned_data, validation_errors = self._validate_order_data(data)
            elif document_type == "accompanying":
                is_valid, cleaned_data, validation_errors = self._validate_accompanying_data(data)
            else:
                errors.append(f"Unbekannter Dokumenttyp: {document_type}")
                return False, {}, errors

            errors.extend(validation_errors)

            # Verbessere validation_status basierend auf gefundenen Fehlern
            cleaned_data = self._enhance_validation_status(cleaned_data, errors)

            return is_valid, cleaned_data, errors

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            errors.append(f"Validation failed: {str(e)}")
            return False, {}, errors

    def _validate_delivery_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validiert Lieferschein-Daten (neue flache Struktur)."""
        errors = []
        is_valid = True

        # Neue flache Struktur - keine verschachtelte "delivery" Sektion mehr
        if "items" not in data:
            errors.append("'items' Sektion fehlt")
            is_valid = False
            data["items"] = []

        # Delivery-Pflichtfelder prüfen (direkt auf oberster Ebene)
        required_delivery_fields = ["delivery_number", "supplier_name"]

        for field in required_delivery_fields:
            if not data.get(field):
                errors.append(f"Pflichtfeld fehlt: {field}")
                is_valid = False

        # Standardwerte für leere Felder setzen
        data.setdefault("supplier_id", "")
        data.setdefault("order_number", "")
        data.setdefault("employee_name", "Automatischer Import")
        data.setdefault("notes", "Importiert via Claude API")

        # Items validieren
        items = data.get("items", [])
        if not items:
            errors.append("Keine Items gefunden")
            is_valid = False
        else:
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"Item {i+1} ist kein gültiges Objekt")
                    continue

                # Item-Pflichtfelder
                required_item_fields = ["article_number", "batch_number"]
                for field in required_item_fields:
                    if not item.get(field):
                        errors.append(f"Item {i+1}: Pflichtfeld fehlt: {field}")
                        is_valid = False

                # Quantity validieren
                quantity = item.get("quantity")
                if quantity is not None:
                    try:
                        quantity_int = int(quantity)
                        if quantity_int <= 0:
                            errors.append(f"Item {i+1}: Quantity muss > 0 sein")
                            is_valid = False
                        item["quantity"] = quantity_int
                    except (ValueError, TypeError):
                        errors.append(f"Item {i+1}: Quantity ist keine gültige Zahl")
                        is_valid = False

        # total_items automatisch berechnen
        data["total_items"] = len(items)

        return is_valid, data, errors

    def _validate_order_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validiert Bestellungs-Daten."""
        errors = []
        is_valid = True

        # Erwartete Felder prüfen
        required_fields = ["order_number"]
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Pflichtfeld fehlt: {field}")
                is_valid = False

        # Articles validieren
        articles = data.get("articles", [])
        if not articles:
            errors.append("Keine Artikel gefunden")
            is_valid = False
        else:
            for i, article in enumerate(articles):
                if not isinstance(article, dict):
                    errors.append(f"Artikel {i+1} ist kein gültiges Objekt")
                    continue

                # Artikel-Pflichtfelder
                required_article_fields = ["article_number"]
                for field in required_article_fields:
                    if not article.get(field):
                        errors.append(f"Artikel {i+1}: Pflichtfeld fehlt: {field}")
                        is_valid = False

                # Quantity validieren
                quantity = article.get("quantity")
                if quantity is not None:
                    try:
                        quantity_int = int(quantity)
                        if quantity_int <= 0:
                            errors.append(f"Artikel {i+1}: Quantity muss > 0 sein")
                            is_valid = False
                        article["quantity"] = quantity_int
                    except (ValueError, TypeError):
                        errors.append(f"Artikel {i+1}: Quantity ist keine gültige Zahl")
                        is_valid = False

        return is_valid, data, errors

    def _validate_accompanying_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validiert Begleitpapiere-Daten."""
        errors = []
        is_valid = True

        # Erwartete Struktur prüfen
        expected_sections = ["article_search", "batch_search", "document_analysis"]

        for section in expected_sections:
            if section not in data:
                errors.append(f"'{section}' Sektion fehlt")
                is_valid = False

        # Article Search validieren
        article_search = data.get("article_search", {})
        if not isinstance(article_search, dict):
            errors.append("article_search ist kein gültiges Objekt")
            is_valid = False

        # Batch Search validieren
        batch_search = data.get("batch_search", {})
        if not isinstance(batch_search, dict):
            errors.append("batch_search ist kein gültiges Objekt")
            is_valid = False

        # Document Analysis validieren
        doc_analysis = data.get("document_analysis", {})
        if not isinstance(doc_analysis, dict):
            errors.append("document_analysis ist kein gültiges Objekt")
            is_valid = False
        else:
            # Types sollte ein Array sein
            types = doc_analysis.get("types", [])
            if not isinstance(types, list):
                errors.append("document_analysis.types sollte ein Array sein")
                is_valid = False

        return is_valid, data, errors

    def _enhance_validation_status(self, data: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """
        Verbessert validation_status basierend auf gefundenen Fehlern.
        """
        try:
            # Bestehenden validation_status holen oder erstellen
            validation_status = data.get("validation_status", {})

            # Completeness Score anpassen basierend auf Fehlern
            current_score = validation_status.get("completeness_score", 100)

            # Score reduzieren basierend auf Anzahl Fehler
            if errors:
                # Pro Fehler 10% abziehen, minimum 0%
                error_penalty = min(len(errors) * 10, current_score)
                adjusted_score = max(0, current_score - error_penalty)
                validation_status["completeness_score"] = adjusted_score

                # Fehler zu missing_critical_fields hinzufügen
                missing_fields = validation_status.get("missing_critical_fields", [])
                for error in errors:
                    if "Pflichtfeld fehlt" in error:
                        field_name = error.split(":")[-1].strip()
                        if field_name not in missing_fields:
                            missing_fields.append(field_name)

                validation_status["missing_critical_fields"] = missing_fields

                # Manual Review nötig wenn Score sehr niedrig
                if adjusted_score < 50:
                    validation_status["manual_review_needed"] = True

                # User Guidance erweitern
                existing_guidance = validation_status.get("user_guidance", "")
                error_summary = f"Validierungsfehler gefunden: {len(errors)} Problem(e). "
                if existing_guidance:
                    validation_status["user_guidance"] = existing_guidance + " " + error_summary
                else:
                    validation_status["user_guidance"] = error_summary

            data["validation_status"] = validation_status
            return data

        except Exception as e:
            self.logger.error(f"Error enhancing validation status: {e}")
            return data

    def validate_against_expected_values(
        self,
        raw_extraction: Dict[str, Any],
        expected_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 2 Validation: Validiert Extraction gegen erwartete Werte.

        Diese Methode wird für die Live-Validation von expected_* values verwendet
        und ist bewusst nicht gecacht.

        Args:
            raw_extraction: Raw extraction result von Claude API
            expected_values: Dict mit expected_* keys

        Returns:
            Validation result dict für validation_status
        """
        validation_result = {
            "expected_values_validation": {},
            "validation_confidence": "medium",
            "manual_review_suggested": False
        }

        try:
            for expected_key, expected_value in expected_values.items():
                if not expected_value:  # Skip empty expected values
                    continue

                # Remove "expected_" prefix für field matching
                field_name = expected_key.replace("expected_", "")

                # Validation per field type
                if field_name == "order_number":
                    result = self._validate_order_number_match(raw_extraction, expected_value)
                    validation_result["expected_values_validation"]["order_number"] = result

                elif field_name == "article_number":
                    result = self._validate_article_number_match(raw_extraction, expected_value)
                    validation_result["expected_values_validation"]["article_number"] = result

                else:
                    # Generic validation für andere expected values
                    result = self._validate_generic_field_match(
                        raw_extraction, field_name, expected_value
                    )
                    validation_result["expected_values_validation"][field_name] = result

            # Overall validation confidence basierend auf Matches
            validation_results = validation_result["expected_values_validation"]
            match_count = sum(1 for r in validation_results.values() if r.get("match", False))
            total_count = len(validation_results)

            if total_count > 0:
                confidence_ratio = match_count / total_count
                if confidence_ratio >= 0.8:
                    validation_result["validation_confidence"] = "high"
                elif confidence_ratio >= 0.5:
                    validation_result["validation_confidence"] = "medium"
                else:
                    validation_result["validation_confidence"] = "low"
                    validation_result["manual_review_suggested"] = True

            self.logger.debug(f"Expected values validation: {match_count}/{total_count} matches")

        except Exception as e:
            self.logger.error(f"Error in expected values validation: {e}")
            validation_result["validation_confidence"] = "low"
            validation_result["error"] = str(e)

        return validation_result

    def _validate_order_number_match(
        self,
        raw_extraction: Dict[str, Any],
        expected_order: str
    ) -> Dict[str, Any]:
        """Validiert Order Number Match."""
        result = {"match": False, "found_value": None, "confidence": "low"}

        try:
            # Check order_number field directly
            extracted_order = raw_extraction.get("order_number")
            if extracted_order:
                result["found_value"] = extracted_order
                result["match"] = str(extracted_order).strip() == str(expected_order).strip()
                result["confidence"] = "high" if result["match"] else "medium"
                return result

            # Check in items array
            items = raw_extraction.get("items", [])
            if items and isinstance(items, list):
                for item in items:
                    item_order = item.get("order_number")
                    if item_order and str(item_order).strip() == str(expected_order).strip():
                        result["found_value"] = item_order
                        result["match"] = True
                        result["confidence"] = "high"
                        return result

            result["confidence"] = "medium"  # Not found but no error

        except Exception as e:
            result["error"] = str(e)
            result["confidence"] = "low"

        return result

    def _validate_article_number_match(
        self,
        raw_extraction: Dict[str, Any],
        expected_article: str
    ) -> Dict[str, Any]:
        """Validiert Article Number Match."""
        result = {"match": False, "found_articles": [], "confidence": "low"}

        try:
            # Check items array for article numbers
            items = raw_extraction.get("items", [])
            if items and isinstance(items, list):
                found_articles = []
                for item in items:
                    article_number = item.get("article_number")
                    if article_number:
                        found_articles.append(article_number)
                        if str(article_number).strip() == str(expected_article).strip():
                            result["match"] = True
                            result["confidence"] = "high"

                result["found_articles"] = found_articles

            if not result["match"] and result["found_articles"]:
                result["confidence"] = "medium"  # Articles found but no match
            elif result["found_articles"]:
                result["confidence"] = "high"  # Articles found, processing successful

        except Exception as e:
            result["error"] = str(e)
            result["confidence"] = "low"

        return result

    def _validate_generic_field_match(
        self,
        raw_extraction: Dict[str, Any],
        field_name: str,
        expected_value: str
    ) -> Dict[str, Any]:
        """Generic validation für beliebige fields."""
        result = {"match": False, "found_value": None, "confidence": "medium"}

        try:
            # Direct field lookup
            found_value = raw_extraction.get(field_name)
            if found_value:
                result["found_value"] = found_value
                result["match"] = str(found_value).strip() == str(expected_value).strip()
                result["confidence"] = "high" if result["match"] else "medium"

        except Exception as e:
            result["error"] = str(e)
            result["confidence"] = "low"

        return result


# Global instance
document_validator = DocumentValidator()