"""
Placeholder Engine - Einheitliches Placeholder-System

Zentralisiert die Placeholder-Ersetzungslogik aus WordTemplateService.
Unterstützt verschiedene Placeholder-Formate und Formatierungs-Optionen.
"""

import logging
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Callable, Pattern
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PlaceholderMatch:
    """
    Repräsentiert einen gefundenen Placeholder im Template.
    """
    full_match: str          # Vollständiger Match (z.B. "[[datum]]" oder "{{qty|number}}")
    placeholder_name: str    # Name des Placeholders (z.B. "datum", "qty")
    format_spec: str = ""    # Format-Spezifikation (z.B. "number", "DD.MM.YYYY")
    start_pos: int = 0       # Start-Position im Text
    end_pos: int = 0         # End-Position im Text


class PlaceholderEngine:
    """
    Einheitliches Placeholder-Ersetzungssystem für alle DOCX-Templates.

    Ersetzt die verstreute Placeholder-Logic aus WordTemplateService mit einem
    zentralen, konfigurierbaren System.

    UNTERSTÜTZTE PLACEHOLDER-FORMATE:
    - [[placeholder]] - Einfacher Placeholder (Kompatibilität mit bestehenden Templates)
    - {{placeholder}} - Einfacher Placeholder (moderne Syntax)
    - {{placeholder|format}} - Placeholder mit Formatierung
    - {% if condition %}content{% endif %} - Conditional Content (zukünftig)
    """

    def __init__(self):
        """Initialize placeholder engine with patterns and formatters."""

        # PLACEHOLDER PATTERNS (in Prioritäts-Reihenfolge)
        self.patterns = {
            # Legacy Format für Kompatibilität mit bestehenden Templates
            'legacy_brackets': re.compile(r'\[\[([A-Za-z_][A-Za-z0-9_]*)\]\]'),

            # Moderne Formate
            'simple_braces': re.compile(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}'),
            'formatted_braces': re.compile(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\|([^}]+)\}\}'),

            # Conditional (für zukünftige Erweiterung)
            'conditional': re.compile(r'\{\%\s*if\s+([A-Za-z_][A-Za-z0-9_]*)\s*\%\}(.*?)\{\%\s*endif\s*\%\}', re.DOTALL)
        }

        # FORMAT FUNCTIONS REGISTRY
        self.formatters: Dict[str, Callable[[Any, str], str]] = {
            # Datum-Formatierung
            'date': self._format_date,
            'datum': self._format_date,
            'DD.MM.YYYY': self._format_date_german,
            'YYYY-MM-DD': self._format_date_iso,

            # Zahlen-Formatierung
            'number': self._format_number,
            'zahl': self._format_number,
            'currency': self._format_currency,
            'decimal': self._format_decimal,
            'integer': self._format_integer,

            # Text-Formatierung
            'upper': self._format_upper,
            'lower': self._format_lower,
            'title': self._format_title,
            'capitalize': self._format_capitalize,

            # Boolean-Formatierung
            'checkbox': self._format_checkbox,
            'yesno': self._format_yesno,
            'jain': self._format_jain,
            'x': self._format_x_mark,

            # Spezial-Formatierung
            'truncate': self._format_truncate,
            'pad': self._format_pad
        }

        # STATISTICS
        self.stats = {
            'total_replacements': 0,
            'successful_replacements': 0,
            'failed_replacements': 0,
            'missing_placeholders': []
        }

    def replace_placeholders(
        self,
        text: str,
        context: Dict[str, Any],
        strict_mode: bool = False
    ) -> str:
        """
        Ersetzt alle Placeholder in Text mit Context-Werten.

        Args:
            text: Text mit Placeholdern
            context: Dictionary mit Placeholder-Werten
            strict_mode: Wenn True, werden unbekannte Placeholder als Fehler behandelt

        Returns:
            Text mit ersetzten Placeholdern
        """
        try:
            if not text or not isinstance(text, str):
                return str(text) if text is not None else ""

            if not context:
                context = {}

            # Reset Statistics
            self._reset_stats()

            result_text = text
            all_matches = []

            # SCHRITT 1: Sammle alle Placeholder-Matches
            for pattern_name, pattern in self.patterns.items():
                matches = self._find_placeholder_matches(result_text, pattern, pattern_name)
                all_matches.extend(matches)

            # Sortiere Matches nach Position (rückwärts für korrekte Ersetzung)
            all_matches.sort(key=lambda m: m.start_pos, reverse=True)

            # SCHRITT 2: Ersetze Placeholder (rückwärts um Positionen beizubehalten)
            for match in all_matches:
                try:
                    replacement_value = self._get_replacement_value(
                        match.placeholder_name,
                        context,
                        match.format_spec
                    )

                    if replacement_value is not None:
                        # Ersetze im Text
                        result_text = (
                            result_text[:match.start_pos] +
                            str(replacement_value) +
                            result_text[match.end_pos:]
                        )
                        self.stats['successful_replacements'] += 1

                    else:
                        # Placeholder nicht gefunden
                        self._handle_missing_placeholder(match, strict_mode)

                    self.stats['total_replacements'] += 1

                except Exception as e:
                    logger.error(f"Error replacing placeholder '{match.placeholder_name}': {e}")
                    self.stats['failed_replacements'] += 1

                    if strict_mode:
                        raise

            # SCHRITT 3: Conditional Content (falls vorhanden)
            result_text = self._process_conditional_content(result_text, context)

            # SCHRITT 4: Cleanup - entferne unverarbeitete Placeholder falls gewünscht
            if not strict_mode:
                result_text = self._cleanup_unprocessed_placeholders(result_text)

            logger.debug(f"Placeholder replacement completed: {self.stats['successful_replacements']}/{self.stats['total_replacements']} successful")

            return result_text

        except Exception as e:
            logger.error(f"Error in placeholder replacement: {e}")
            if strict_mode:
                raise
            return text  # Return original text on error

    def _find_placeholder_matches(
        self,
        text: str,
        pattern: Pattern[str],
        pattern_name: str
    ) -> List[PlaceholderMatch]:
        """Findet alle Placeholder-Matches für ein Pattern."""
        matches = []

        try:
            for match in pattern.finditer(text):
                if pattern_name in ['formatted_braces']:
                    # Pattern mit Format: {{placeholder|format}}
                    placeholder_match = PlaceholderMatch(
                        full_match=match.group(0),
                        placeholder_name=match.group(1),
                        format_spec=match.group(2) if len(match.groups()) > 1 else "",
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                else:
                    # Einfache Patterns: [[placeholder]], {{placeholder}}
                    placeholder_match = PlaceholderMatch(
                        full_match=match.group(0),
                        placeholder_name=match.group(1),
                        format_spec="",
                        start_pos=match.start(),
                        end_pos=match.end()
                    )

                matches.append(placeholder_match)

        except Exception as e:
            logger.error(f"Error finding matches for pattern {pattern_name}: {e}")

        return matches

    def _get_replacement_value(
        self,
        placeholder_name: str,
        context: Dict[str, Any],
        format_spec: str = ""
    ) -> Optional[str]:
        """
        Holt Replacement-Wert für einen Placeholder aus Context.

        Args:
            placeholder_name: Name des Placeholders
            context: Context Dictionary
            format_spec: Format-Spezifikation

        Returns:
            Formatierter String oder None wenn nicht gefunden
        """
        try:
            # SCHRITT 1: Wert aus Context holen (case-insensitive)
            value = None

            # Exakte Übereinstimmung
            if placeholder_name in context:
                value = context[placeholder_name]
            else:
                # Case-insensitive Suche
                for key, val in context.items():
                    if key.lower() == placeholder_name.lower():
                        value = val
                        break

            if value is None:
                return None

            # SCHRITT 2: Formatierung anwenden
            if format_spec and format_spec in self.formatters:
                try:
                    formatted_value = self.formatters[format_spec](value, format_spec)
                    return formatted_value
                except Exception as e:
                    logger.warning(f"Error formatting value '{value}' with format '{format_spec}': {e}")
                    # Fallback to default formatting

            # SCHRITT 3: Standard-Formatierung
            return self._format_default(value)

        except Exception as e:
            logger.error(f"Error getting replacement value for '{placeholder_name}': {e}")
            return None

    def _format_default(self, value: Any) -> str:
        """Standard-Formatierung für Werte ohne spezifisches Format."""
        try:
            if value is None:
                return ""
            elif isinstance(value, bool):
                return "X" if value else ""  # Checkbox-Format als Default
            elif isinstance(value, (datetime, date)):
                return value.strftime("%d.%m.%Y")  # Deutsche Datumsformat
            elif isinstance(value, (int, float, Decimal)):
                return str(value)
            else:
                return str(value)

        except Exception as e:
            logger.error(f"Error in default formatting: {e}")
            return str(value) if value is not None else ""

    def _handle_missing_placeholder(self, match: PlaceholderMatch, strict_mode: bool):
        """Behandelt fehlende Placeholder."""
        missing_info = f"{match.placeholder_name} (at position {match.start_pos})"
        self.stats['missing_placeholders'].append(missing_info)

        if strict_mode:
            raise ValueError(f"Missing required placeholder: {match.placeholder_name}")
        else:
            logger.debug(f"Missing placeholder: {match.placeholder_name}")

    def _process_conditional_content(self, text: str, context: Dict[str, Any]) -> str:
        """
        Verarbeitet conditional content (zukünftige Funktion).
        Syntax: {% if condition %}content{% endif %}
        """
        # Placeholder für zukünftige Implementierung
        return text

    def _cleanup_unprocessed_placeholders(self, text: str) -> str:
        """Entfernt unverarbeitete Placeholder aus dem Text."""
        try:
            # Entferne alle verbliebenen Placeholder-Patterns
            for pattern in self.patterns.values():
                text = pattern.sub("", text)

            return text

        except Exception as e:
            logger.error(f"Error cleaning unprocessed placeholders: {e}")
            return text

    def _reset_stats(self):
        """Setzt Statistiken zurück."""
        self.stats = {
            'total_replacements': 0,
            'successful_replacements': 0,
            'failed_replacements': 0,
            'missing_placeholders': []
        }

    # === FORMAT FUNCTIONS ===

    def _format_date(self, value: Any, format_spec: str) -> str:
        """Allgemeine Datum-Formatierung."""
        try:
            if isinstance(value, str):
                # Parse String zu datetime
                try:
                    # Verschiedene Formate probieren
                    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            value = datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue
                except ValueError:
                    return str(value)  # Kann nicht geparst werden

            if isinstance(value, (datetime, date)):
                if "DD.MM.YYYY" in format_spec:
                    return value.strftime("%d.%m.%Y")
                elif "YYYY-MM-DD" in format_spec:
                    return value.strftime("%Y-%m-%d")
                else:
                    return value.strftime("%d.%m.%Y")  # Default: German format

            return str(value)

        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return str(value)

    def _format_date_german(self, value: Any, format_spec: str) -> str:
        """Deutsche Datumsformatierung (DD.MM.YYYY)."""
        return self._format_date(value, "DD.MM.YYYY")

    def _format_date_iso(self, value: Any, format_spec: str) -> str:
        """ISO Datumsformatierung (YYYY-MM-DD)."""
        return self._format_date(value, "YYYY-MM-DD")

    def _format_number(self, value: Any, format_spec: str) -> str:
        """Zahlen-Formatierung."""
        try:
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    return str(value)

            if isinstance(value, (int, float, Decimal)):
                if isinstance(value, float):
                    # Entferne trailing zeros
                    if value.is_integer():
                        return str(int(value))
                    else:
                        return f"{value:.2f}"
                return str(value)

            return str(value)

        except Exception as e:
            logger.error(f"Error formatting number: {e}")
            return str(value)

    def _format_currency(self, value: Any, format_spec: str) -> str:
        """Währungs-Formatierung."""
        try:
            number_str = self._format_number(value, format_spec)
            if number_str and number_str != str(value):
                return f"{number_str} €"
            return str(value)

        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return str(value)

    def _format_decimal(self, value: Any, format_spec: str) -> str:
        """Dezimal-Formatierung mit festen Nachkommastellen."""
        try:
            if isinstance(value, str):
                value = float(value)

            if isinstance(value, (int, float, Decimal)):
                return f"{float(value):.2f}"

            return str(value)

        except Exception as e:
            logger.error(f"Error formatting decimal: {e}")
            return str(value)

    def _format_integer(self, value: Any, format_spec: str) -> str:
        """Integer-Formatierung."""
        try:
            if isinstance(value, str):
                value = float(value)

            if isinstance(value, (int, float, Decimal)):
                return str(int(value))

            return str(value)

        except Exception as e:
            logger.error(f"Error formatting integer: {e}")
            return str(value)

    def _format_upper(self, value: Any, format_spec: str) -> str:
        """Großbuchstaben."""
        return str(value).upper()

    def _format_lower(self, value: Any, format_spec: str) -> str:
        """Kleinbuchstaben."""
        return str(value).lower()

    def _format_title(self, value: Any, format_spec: str) -> str:
        """Title Case."""
        return str(value).title()

    def _format_capitalize(self, value: Any, format_spec: str) -> str:
        """Ersten Buchstaben groß."""
        return str(value).capitalize()

    def _format_checkbox(self, value: Any, format_spec: str) -> str:
        """Checkbox-Formatierung (X für True, leer für False)."""
        if isinstance(value, bool):
            return "X" if value else ""
        elif isinstance(value, str):
            return "X" if value.lower() in ['true', '1', 'yes', 'ja', 'x'] else ""
        elif isinstance(value, (int, float)):
            return "X" if value != 0 else ""
        return str(value)

    def _format_yesno(self, value: Any, format_spec: str) -> str:
        """Yes/No Formatierung."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, str):
            return "Yes" if value.lower() in ['true', '1', 'yes', 'ja', 'x'] else "No"
        elif isinstance(value, (int, float)):
            return "Yes" if value != 0 else "No"
        return str(value)

    def _format_jain(self, value: Any, format_spec: str) -> str:
        """Ja/Nein Formatierung."""
        if isinstance(value, bool):
            return "Ja" if value else "Nein"
        elif isinstance(value, str):
            return "Ja" if value.lower() in ['true', '1', 'yes', 'ja', 'x'] else "Nein"
        elif isinstance(value, (int, float)):
            return "Ja" if value != 0 else "Nein"
        return str(value)

    def _format_x_mark(self, value: Any, format_spec: str) -> str:
        """X-Mark Formatierung (alias für checkbox)."""
        return self._format_checkbox(value, format_spec)

    def _format_truncate(self, value: Any, format_spec: str) -> str:
        """Text kürzen. Format: truncate:20"""
        try:
            text = str(value)
            if ':' in format_spec:
                length = int(format_spec.split(':')[1])
                if len(text) > length:
                    return text[:length] + "..."
            return text

        except Exception as e:
            logger.error(f"Error truncating text: {e}")
            return str(value)

    def _format_pad(self, value: Any, format_spec: str) -> str:
        """Text padding. Format: pad:10 oder pad:10:0"""
        try:
            text = str(value)
            if ':' in format_spec:
                parts = format_spec.split(':')
                length = int(parts[1])
                fill_char = parts[2] if len(parts) > 2 else ' '
                return text.ljust(length, fill_char)
            return text

        except Exception as e:
            logger.error(f"Error padding text: {e}")
            return str(value)

    # === PUBLIC UTILITY METHODS ===

    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken der letzten Placeholder-Ersetzung zurück."""
        return self.stats.copy()

    def find_placeholders_in_text(self, text: str) -> List[str]:
        """
        Findet alle Placeholder in einem Text.

        Args:
            text: Text zum durchsuchen

        Returns:
            Liste der gefundenen Placeholder-Namen
        """
        try:
            found_placeholders = []

            for pattern in self.patterns.values():
                matches = pattern.findall(text)
                for match in matches:
                    if isinstance(match, tuple):
                        # Formatted placeholders return tuple (name, format)
                        found_placeholders.append(match[0])
                    else:
                        # Simple placeholders return string
                        found_placeholders.append(match)

            return list(set(found_placeholders))  # Remove duplicates

        except Exception as e:
            logger.error(f"Error finding placeholders: {e}")
            return []

    def validate_context_completeness(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validiert ob Context alle Placeholder im Text abdeckt.

        Args:
            text: Text mit Placeholdern
            context: Context Dictionary

        Returns:
            Validierungs-Ergebnis
        """
        try:
            required_placeholders = self.find_placeholders_in_text(text)
            available_placeholders = list(context.keys())

            missing_placeholders = [
                p for p in required_placeholders
                if p not in available_placeholders and
                   p.lower() not in [k.lower() for k in available_placeholders]
            ]

            return {
                'is_complete': len(missing_placeholders) == 0,
                'required_placeholders': required_placeholders,
                'available_placeholders': available_placeholders,
                'missing_placeholders': missing_placeholders,
                'completeness_score': 1.0 - (len(missing_placeholders) / max(len(required_placeholders), 1))
            }

        except Exception as e:
            logger.error(f"Error validating context completeness: {e}")
            return {
                'is_complete': False,
                'error': str(e)
            }

    def _count_placeholders_in_text(self, text: str) -> int:
        """
        Zählt die Anzahl der Placeholder in einem Text.

        Args:
            text: Text zum durchsuchen

        Returns:
            Anzahl der gefundenen Placeholder
        """
        try:
            if not text or not isinstance(text, str):
                return 0

            placeholder_count = 0

            # Zähle Placeholder für jedes Pattern
            for pattern in self.patterns.values():
                matches = pattern.findall(text)
                placeholder_count += len(matches)

            return placeholder_count

        except Exception as e:
            logger.error(f"Error counting placeholders: {e}")
            return 0