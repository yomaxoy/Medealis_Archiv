"""
Prompt Template Manager - Verwaltet alle Claude API Prompts
Extrahiert und standardisiert die Prompts aus den bestehenden Services
"""

import logging
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    DELIVERY = "delivery"
    ORDER = "order"
    ACCOMPANYING = "accompanying"


class PromptTemplateManager:
    """
    Verwaltet alle Claude API Prompts mit Self-Validation.
    Prompts basieren auf den bestehenden Implementierungen.
    """

    def __init__(self):
        self.logger = logger
        self.templates = self._load_templates()

    def get_prompt(
        self, document_type: DocumentType, context: Dict[str, Any] = None
    ) -> str:
        """
        Generiert vollständigen Prompt für Dokumenttyp.

        Args:
            document_type: Typ des Dokuments
            context: Kontext-Daten für Template-Substitution

        Returns:
            Vollständiger Prompt mit Self-Validation
        """
        if context is None:
            context = {}

        template_key = document_type.value
        base_template = self.templates.get(template_key, "")

        if not base_template:
            raise ValueError(f"No template found for document type: {document_type}")

        # Format template with context
        # Convert DocumentType enum to string if needed
        doc_type_str = (
            document_type.value
            if hasattr(document_type, "value")
            else str(document_type)
        )

        if doc_type_str in ["delivery", "order"]:
            # Delivery and Order templates don't use variables
            formatted_prompt = base_template
        else:
            # Accompanying documents use template variables
            try:
                formatted_prompt = base_template.format(**context)
            except (KeyError, ValueError, IndexError) as e:
                self.logger.warning(
                    f"Template formatting failed for {document_type}: {e}"
                )
                # Return unformatted template if formatting fails
                formatted_prompt = base_template

        return formatted_prompt

    def _load_templates(self) -> Dict[str, str]:
        """Lädt alle Prompt-Templates."""
        return {
            "delivery": self._get_delivery_template(),
            "order": self._get_order_template(),
            "accompanying": self._get_accompanying_template(),
        }

    def _get_delivery_template(self) -> str:
        """
        Lieferschein-Prompt mit Self-Validation.
        Detaillierter Prompt für Lieferschein-Analyse.
        """
        return """Du bist ein spezialisierter Lieferschein-Analyser für medizinische/dental Komponenten.
Analysiere diesen Lieferschein systematisch und extrahiere Informationen mit höchster Präzision.
Verwende deutsche Datumsformate (DD.MM.YYYY).

GEWÜNSCHTES JSON-FORMAT (FLACHE STRUKTUR):
{{
    "delivery_number": "Lieferscheinnummer",
    "delivery_date": "DD.MM.YYYY",
    "supplier_name": "Name des Lieferanten",
    "supplier_id": "",
    "employee_name": "Name des Mitarbeiters (falls verfügbar, sonst 'Automatischer Import')",
    "notes": "Zusätzliche Notizen (falls vorhanden, sonst 'Importiert via Claude API')",
    "order_number": "",
    "items": [
        {{
            "article_number": "Artikelnummer",
            "batch_number": "Chargennummer",
            "quantity": 0,
            "description": "Artikelbezeichnung",
            "unit": "Einheit",
            "order_number": "Bestellnummer für diesen Artikel"
        }}
    ],
    "total_items": 0,
    "validation_status": {{
        "completeness_score": 85,
        "missing_critical_fields": ["array", "of", "missing", "fields"],
        "uncertain_extractions": ["field.path.if.unsure"],
        "user_guidance": "Konkrete Hilfestellung für den User",
        "document_quality": "gut|mittel|schlecht",
        "extraction_confidence": "hoch|mittel|niedrig",
        "manual_review_needed": false
    }}
}}

LIEFERANTEN-NORMALISIERUNG (KRITISCH - IMMER ANWENDEN):
Erkenne und normalisiere Lieferantennamen zu konsistenten Standardschreibweisen:

PRIMEC Variationen → "Primec":
- "primec", "Primec", "PRIMEC", "primec gmbh", "Primec gmbh", "PRIMEC GMBH"
- "primec GmbH", "PRIMEC GmbH", "Primec GmbH" → alle zu "Primec"

TERRATS MEDICAL Variationen → "Terrats Medical":
- "terrats", "Terrats", "TERRATS", "terrats medical", "Terrats Medical", "TERRATS MEDICAL"
- "Terrats Medical GmbH", "TERRATS MEDICAL GmbH", "Terrats Medical GmbH" → alle zu "Terrats Medical"

MEGAGEN Variationen → "MEGAGEN":
- "megagen", "Megagen", "MEGAGEN"
- "Megagen GmbH", "MEGAGEN GmbH" → alle zu "MEGAGEN"

C-TECH Variationen → "C-Tech":
- "ctech", "C-tech", "C-Tech", "CTECH", "C-TECH"
- "C-Tech GmbH", "CTECH GmbH" → alle zu "C-Tech"

STRAUMANN Variationen → "Straumann":
- "straumann", "Straumann", "STRAUMANN"
- "Straumann GmbH", "STRAUMANN AG" → alle zu "Straumann"

NOBEL Variationen → "Nobel Biocare":
- "nobel", "Nobel", "NOBEL", "nobel biocare", "Nobel Biocare", "NOBEL BIOCARE"

Beispiel: Wenn du "primec" oder "PRIMEC" erkennst → IMMER ausgeben als "Primec"
Beispiel: Wenn du "terrats medical" oder "TERRATS" erkennst → IMMER ausgeben als "Terrats Medical"

CHARGENNUMMER-OPTIMIERUNG (ERWEITERTE SUCHE):
Suche nach Chargennummern mit folgenden Strategien:

Standard-Formate:
- Primec: P-YYYYMMDDHHMMSS-XXXX (z.B. "P-293520240528-1234")
- Terrats Medical: 6-stellige Ziffern (z.B. "123456") - Spalte "Lot-Nummer" oder "Lot"
- Standard: Buchstabe + Zahlen (z.B. "B123456", "CH789")
- Nur Zahlen mit 6+ Stellen (z.B. "240417")

Erweiterte Suche bei fehlender Chargennummer:
- Prüfe Spalten "Charge", "Batch", "Lot", "Lot-Nummer", "Serial"
- Suche in Artikel-Beschreibung nach Mustern
- Prüfe Datum-ähnliche Zahlenfolgen
- Fallback: "BATCH-[ARTIKEL]-[DATUM]" wenn nichts gefunden

BESTELLNUMMERN-EXTRAKTION - LIEFERANTEN-SPEZIFISCH:
🔥 WICHTIG: Erkenne AUTOMATISCH das Layout-Muster des Lieferanten!

═══════════════════════════════════════════════════════════════════
PRIMEC LAYOUT (Block-basierte Struktur):
═══════════════════════════════════════════════════════════════════
Mehrere Bestellungen pro Lieferschein möglich, zwischen Artikel-Blöcken.

SCHRITT 1: DOKUMENT IN ARTIKEL-BLÖCKE TEILEN
BLOCK 1 = Alles von Dokumentstart bis zur ERSTEN "Bestellnummer:"
BLOCK 2 = Alles von ERSTER "Bestellnummer:" bis zur ZWEITEN "Bestellnummer:"
BLOCK 3 = Alles von ZWEITER "Bestellnummer:" bis Dokumentende

SCHRITT 2: BESTELLNUMMER-TRENNER (Primec)
Suche nach: "Bestellnummer: \\d{5} vom \\d{2}\\.\\d{2}\\.\\d{4}"

SCHRITT 3: ARTIKEL-ZUORDNUNG (Primec Block-Struktur)
┌─ BLOCK 1 (bis erste Bestellnummer)
│  ├─ CT0003 (Pos 1.1) ← Artikel OHNE direkte Bestellnummer
│  └─ Ende bei "Bestellnummer: 10170"
├─ BLOCK 2 (zwischen den Bestellnummern)
│  ├─ CT0004 (Pos 1.2) ← Artikel bekommt 10170
│  └─ Ende bei "Bestellnummer: 10172"
└─ BLOCK 3 (nach zweiter Bestellnummer)
   └─ MG0001 (Pos 2.1) ← Artikel bekommt 10172

═══════════════════════════════════════════════════════════════════
TERRATS MEDICAL LAYOUT (Einfache Tabellen-Struktur):
═══════════════════════════════════════════════════════════════════
NUR EINE Bestellung pro Lieferschein, Bestellnummer UNTERHALB der Tabelle.

ERKENNUNGS-MERKMALE (Terrats Medical):
✓ Artikelnummern beginnen mit "71000" (z.B. 7100001-1)
✓ Tabelle mit Spalten: Artikelnr | [LEER] | Beschreibung | Lot-Nummer | Menge | ...
✓ "Lot-Nummer" Spalte mit 6-stelligen Zahlen
✓ Bestellnummer NACH/UNTERHALB der Tabelle: "Purchase Order: XXXXX"

SCHRITT 1: ERKENNE TERRATS MEDICAL LAYOUT
Wenn Artikelnummern 71000XX-X Format haben → TERRATS MEDICAL Layout!

SCHRITT 2: SUCHE BESTELLNUMMER UNTERHALB DER TABELLE
Suche nach: "Purchase Order: \\d{5}" NACH der Artikel-Tabelle

SCHRITT 3: ALLE ARTIKEL BEKOMMEN DIESELBE BESTELLNUMMER
Für TERRATS MEDICAL:
- Finde "Purchase Order: 12345" unterhalb der Tabelle
- ALLE Artikel in der Tabelle bekommen order_number: "12345"
- KEINE Block-Logik nötig - nur EINE Bestellung!

Beispiel (Terrats Medical):
Tabelle:
7100001-1 | | Dental Implantat | 123456 | 10
7100002-5 | | Abutment       | 789012 | 5

Unterhalb: "Purchase Order: 12345"

Ergebnis:
{{
  "items": [
    {{"article_number": "7100001-1", "batch_number": "123456", "order_number": "12345"}},
    {{"article_number": "7100002-5", "batch_number": "789012", "order_number": "12345"}}
  ],
  "order_number": "12345"
}}

SCHRITT 4: EXPLIZITE ZUORDNUNGSLOGIK (PSEUDO-CODE)
blocks = split_document_by_order_numbers()
for block in blocks:
    if block.has_order_number():
        order_num = block.get_order_number()
        for article in block.get_articles():
            article.order_number = order_num
    else:
        # Erster Block ohne Bestellnummer - Forward-Looking Regel
        next_order = find_next_order_number()
        for article in block.get_articles():
            article.order_number = next_order  # NICHT null!

SCHRITT 5: ANTI-PATTERN VERMEIDUNG (KRITISCH)
🚫 FALSCH: "CT0004 ist näher zu 10172" ❌
✅ RICHTIG: "CT0004 steht im 10170-Block" ✅
🚫 FALSCH: Visuelle Nähe bewerten ❌
✅ RICHTIG: Block-Zugehörigkeit prüfen ✅
🚫 FALSCH: Artikel vor erster Bestellnummer = null ❌
✅ RICHTIG: Forward-Looking zur nächsten Bestellnummer ✅

ZUORDNUNGS-MATRIX (ZWINGEND BEFOLGEN):
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Artikel-Position    │ Steht zwischen      │ Bekommt Bestellnr.  │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ CT0003 (Pos 1.1)    │ Dokumentstart-10170 │ "10170" (Forward)   │
│ CT0004 (Pos 1.2)    │ "10170" und "10172" │ "10170" (Block-2)   │
│ MG0001 (Pos 2.1)    │ "10172"-Dokumentende│ "10172" (Block-3)   │
└─────────────────────┴─────────────────────┴─────────────────────┘

DEBUG-PROTOKOLL (MENTAL DURCHFÜHREN):
1. 📍 Finde erste Bestellnummer: "10170 vom XX.XX.XXXX" bei Zeile/Position X
2. 📍 Finde zweite Bestellnummer: "10172 vom XX.XX.XXXX" bei Zeile/Position Y
3. 🔍 CT0003 steht vor Position X → Block 1 → order_number: "10170" (Forward)
4. 🔍 CT0004 steht zwischen X und Y → Block 2 → order_number: "10170" (Block-Regel)
5. 🔍 MG0001 steht nach Position Y → Block 3 → order_number: "10172" (Block-Regel)

ABSOLUTE ERFOLGSREGEL:
🎯 ALLE ARTIKEL MÜSSEN BESTELLNUMMERN BEKOMMEN:
- CT0003 = "10170" (Forward-Looking zur nächsten Bestellung)
- CT0004 = "10170" (Block-2: zwischen 10170 und 10172)
- MG0001 = "10172" (Block-3: nach 10172)

NIEMALS order_number: null verwenden! Forward-Looking anwenden!

DOKUMENT-LAYOUT ANALYSE (NEUE STRATEGIE):
Erkenne systematisch das Lieferschein-Layout:

1. KOPFBEREICH (Lieferschein-Info):
   - Lieferscheinnummer: meist in oberer Hälfte, oft mit "LS", "DN", "Lieferschein"
   - Lieferant: Absender-Information, oft mit Logo oder Briefkopf
   - Datum: meist als "Lieferdatum", "Datum", oder DD.MM.YYYY Format

2. TABELLENBEREICH (Artikel-Info):
   - Spalten: Art.Nr., Bezeichnung, Menge, Charge/Batch, Bestell-Nr.
   - Mehrere Artikel untereinander in Tabellenform
   - Bestellnummern oft gruppiert (eine für mehrere Artikel)

3. FUSSBEREICH:
   - Zusätzliche Notizen, Unterschriften, Stempel

QUALITY-SCORING ENHANCED:
- 90-100%: Alle Pflichtfelder + alle Chargennummern
- 80-89%: Alle Pflichtfelder + 80%+ Chargennummern
- 70-79%: Alle Pflichtfelder + 50%+ Chargennummern
- 60-69%: Alle Pflichtfelder, wenige Chargennummern
- <60%: Fehlende Pflichtfelder

SELBST-VALIDIERUNGS-REGELN (ERWEITERT):
✅ completeness_score = (gefundene_kritische_felder / alle_kritischen_felder) * 100
✅ Wenn delivery_number fehlt: "Die Lieferscheinnummer konnte nicht gefunden werden. Bitte prüfen Sie die Kopfzeile des Dokuments."
✅ Wenn items leer: "Keine Artikel erkannt. Möglicherweise ist das Dokument eine andere Dokumentart oder die Tabelle ist nicht lesbar."
✅ Bei OCR-Problemen: "Dokumentqualität ist niedrig. Einige Zahlen könnten falsch erkannt worden sein."
✅ Wenn Chargennummer fehlt: "Chargennummer für Artikel [X] nicht gefunden. Prüfen Sie Spalten Charge/Batch/Lot."
✅ Wenn Supplier normalisiert: "Lieferant wurde standardisiert: [alt] → [neu]"

FINALE VERARBEITUNGSREGELN:
1. PFLICHTFELDER (müssen vorhanden sein):
   - delivery_number: Lieferscheinnummer (KRITISCH)
   - supplier_name: Normalisierter Lieferantenname (KRITISCH)
   - items: Mindestens 1 Artikel (KRITISCH)
   - items[].article_number: Artikelnummer pro Item (KRITISCH)
   - items[].quantity: Menge als Integer > 0 (KRITISCH)

2. EMPFOHLENE FELDER (versuche zu finden):
   - delivery_date: Lieferdatum im Format DD.MM.YYYY
   - items[].batch_number: Chargennummer (verwende erweiterte Suche)
   - items[].description: Artikelbeschreibung
   - items[].order_number: Bestellnummer pro Artikel

3. AUTOMATISCHE FELDER:
   - supplier_id: IMMER leer lassen ("") - wird vom System gemappt
   - order_number: IMMER leer lassen ("") außer eindeutig bestimmbar
   - total_items: Anzahl der Items im Array
   - employee_name: "Automatischer Import" wenn nicht gefunden

4. DATENTYP-REGELN:
   - Quantity: Integer > 0, nie String oder Decimal
   - Dates: String im Format "DD.MM.YYYY"
   - Null-Werte: null, nicht "", nicht "N/A"

5. OUTPUT-FORMAT (KOMPATIBILITÄT ERHALTEN):
   - NUR JSON zurückgeben, keine Markdown-Blöcke ```json
   - Keine Erklärungen oder Zusatztext
   - Flache Struktur (kein "delivery": {...} Wrapper)
   - KRITISCH: JSON-Format MUSS identisch zum bestehenden System bleiben!
   - items[].order_number MUSS String sein, nie null (verwende Forward-Looking)

BEISPIEL KORREKTE AUSGABE (BLOCK-ANALYSE ANGEWENDET):
{{
    "delivery_number": "LS24-077",
    "supplier_name": "Primec",
    "delivery_date": "11.06.2024",
    "employee_name": "Automatischer Import",
    "supplier_id": "",
    "order_number": "",
    "total_items": 3,
    "items": [
        {{
            "article_number": "CT0003",
            "batch_number": "P-153520240417",
            "quantity": 107,
            "description": "DL Abutment für C-Tech Esthetic Line GH 3,0mm",
            "unit": "Stück",
            "order_number": "10170"
        }},
        {{
            "article_number": "CT0004",
            "batch_number": "P-180020240417",
            "quantity": 58,
            "description": "DL Abutment für C-Tech Esthetic Line GH 4,0mm",
            "unit": "Stück",
            "order_number": "10170"
        }},
        {{
            "article_number": "MG0001",
            "batch_number": "P-181820240415",
            "quantity": 109,
            "description": "Docklocs Abutment gerade, MEGAGEN, GH1",
            "unit": "Stück",
            "order_number": "10172"
        }}
    ],
    "validation_status": {{
        "completeness_score": 95,
        "missing_critical_fields": [],
        "uncertain_extractions": [],
        "user_guidance": "BLOCK-ANALYSE durchgeführt: CT0003+CT0004→10170, MG0001→10172",
        "document_quality": "gut",
        "extraction_confidence": "hoch",
        "manual_review_needed": false
    }}
}}"""

    def _get_order_template(self) -> str:
        """
        Bestellung-Prompt mit Self-Validation.
        """
        return """Analysiere dieses Bestelldokument und extrahiere folgende Informationen im JSON-Format:

GEWÜNSCHTES JSON-FORMAT:
{{
    "order_number": "Bestellnummer",
    "order_date": "Bestelldatum (YYYY-MM-DD)",
    "supplier": "Lieferant/Hersteller",
    "customer": "Kunde/Besteller",
    "articles": [
        {{
            "article_number": "Artikelnummer",
            "description": "Artikelbeschreibung",
            "quantity": 999,
            "unit": "Einheit (Stück, kg, m, etc.)",
            "unit_price": 99.99,
            "total_price": 999.99
        }}
    ],
    "total_amount": 9999.99,
    "currency": "EUR",
    "delivery_address": "Lieferadresse",
    "payment_terms": "Zahlungsbedingungen",

    "validation_status": {{
        "completeness_score": 85,
        "missing_critical_fields": ["array", "of", "missing", "fields"],
        "uncertain_extractions": ["field.path.if.unsure"],
        "user_guidance": "Konkrete Hilfestellung für den User",
        "document_quality": "gut|mittel|schlecht",
        "extraction_confidence": "hoch|mittel|niedrig",
        "manual_review_needed": false
    }}
}}

SELBST-VALIDIERUNGS-REGELN:
✅ completeness_score = (gefundene_kritische_felder / alle_kritischen_felder) * 100
✅ Wenn order_number fehlt: "Die Bestellnummer konnte nicht gefunden werden. Bitte prüfen Sie die Kopfzeile des Dokuments."
✅ Wenn articles leer: "Keine Artikel erkannt. Möglicherweise ist das Dokument eine andere Dokumentart oder die Tabelle ist nicht lesbar."
✅ Bei unklaren Mengen: "Artikelmengen sind unklar. Bitte prüfen Sie die Mengenspalte in der Bestelltabelle."

Wichtige Regeln:
- Extrahiere ALLE Artikel aus der Bestellung
- Zahlen als Numbers, nicht als Strings
- Artikelnummern EXAKT wie im Dokument (mit Bindestrichen, Punkten etc.)
- Bestellnummer vollständig und korrekt
- Mengen als Integer-Zahlen
- Preise als Decimal-Zahlen
- Datum im Format YYYY-MM-DD
- Wenn Informationen fehlen, verwende null"""

    def _get_accompanying_template(self) -> str:
        """
        Begleitpapiere-Prompt mit verbesserter intensiver Suche und Validierung.
        """
        return """Du bist ein Experte für die Analyse technischer Begleitdokumente. Analysiere das bereitgestellte Dokument systematisch und präzise.

AUFGABE:
Identifiziere Dokumenttypen basierend auf spezifischen Indikatoren und ordne sie den standardisierten Kategorien zu.

1. DOKUMENTTYPEN-MAPPING

Verwende diese spezifischen Mapping-Regeln für type_indicators:

MESSPROTOKOLL:
- Erkenne durch: "Prüfprotokoll mit Messwerten", "Messwerte", "Prüfbericht", "Dimensionsprüfung"
- Zusätzliche Indikatoren: Messergebnisse, Prüfdaten, Toleranzprüfungen, Qualitätsmessungen, Maßprüfung
- Englisch: "Test Report", "Measurement Protocol", "Inspection Report"

MATERIALZEUGNIS:
- Erkenne durch: "Certificate of Test", "Certificate of Test for Titanium Products", "Materialprüfzeugnis", "Werkstoffzeugnis"
- Zusätzliche Indikatoren: Materialeigenschaften, Zusammensetzung, mechanische Werte, Werkstoffanalyse, Chemische Analyse
- Englisch: "Material Certificate", "Mill Certificate", "Material Test Certificate"

HÄRTEZEUGNIS:
- Erkenne durch: "Rockwelltest", "Härtemessungen", "Bestimmung der Schichtdicke", "Härteprüfung"
- Zusätzliche Indikatoren: HRC, HV, HB Werte, Härteprüfverfahren, Vickers, Brinell
- Englisch: "Hardness Test", "Hardness Certificate", "Rockwell Test"

BESCHICHTUNGSZEUGNIS:
- Erkenne durch: "Beschichtung", Schichtwerkstoffe (z.B. "ZrCN", "TiN", "TiAlN"), Oberflächenbehandlung
- Zusätzliche Indikatoren: Beschichtungsverfahren, Schichtdicke, Oberflächeneigenschaften, PVD, CVD
- Englisch: "Coating Certificate", "Surface Treatment", "Coating Report"

2. INTENSIVE NUMMERNSUCHE

KRITISCH: Führe eine SEHR GRÜNDLICHE Suche durch!

Artikelnummer: "{article_number}"
PRIMÄRE Suchstrategie (HÖCHSTE PRIORITÄT):
- Seite 2, zweite Spalte von links, zweite Zeile
- Suche auch nach leichten Variationen: 0/O Vertauschung berücksichtigen

SEKUNDÄRE Suchstrategie (VOLLSTÄNDIGE DURCHSUCHUNG):
- ALLE Seiten systematisch durchsuchen
- Tabellen, Kopfzeilen, Fußzeilen, Seitenränder
- Ähnliche Nummern: alle Nummern die mindestens 70% Übereinstimmung haben
- Auch nach Teilnummern suchen (erste 4-6 Zeichen)

Chargennummer: "{batch_number}"
PRIMÄRE Suchstrategie (HÖCHSTE PRIORITÄT):
- Deckblatt (Seite 1), oft im oberen Bereich
- Exakt nach "{batch_number}" suchen
- Format: P-xxxxxxxxxxxx (OHNE Suffix nach Bindestrich)

SEKUNDÄRE Suchstrategie (VOLLSTÄNDIGE DURCHSUCHUNG):
- ALLE Seiten durchsuchen
- Variationen: "Charge:", "Batch:", "Los:", "Lot:", "Heat No:", "Schmelze:"
- Teilübereinstimmungen: P-Nummern die ersten 8-10 Zeichen übereinstimmen
- Auch ohne "P-" Präfix suchen

WICHTIG:
- Begleitdokumente enthalten nur den P-xxxxxxxxxxxx Teil
- System verwendet P-xxxxxxxxxxxx-xxxx, aber Suffix nach Bindestrich erscheint NICHT auf Dokumenten
- Bei OCR-Fehlern: 0/O, 1/I/l, 5/S verwechslung berücksichtigen

3. STRENGE VALIDIERUNG

Artikelnummer gefunden = true NUR wenn:
- Exakte Übereinstimmung ODER
- Mindestens 90% Übereinstimmung mit maximal 1-2 Zeichen Unterschied

Chargennummer gefunden = true NUR wenn:
- P-Format erkannt ODER
- Eindeutige Chargennummer-Kennzeichnung gefunden

4. KONFIDENZ-BEWERTUNG

HOCH:
- Beide Nummern eindeutig gefunden mit hoher Übereinstimmung
- Dokumenttyp durch spezifische Mapping-Indikatoren identifiziert
- Gute Bildqualität

MITTEL:
- Eine Nummer unsicher oder nur Teilübereinstimmung
- Dokumenttyp erkennbar, aber nicht alle Mapping-Kriterien erfüllt
- Moderate Bildqualität

NIEDRIG:
- Mehrere Unsicherheiten bei Nummern
- Mapping-Indikatoren unklar
- Schlechte Bildqualität

5. AUSGABEFORMAT

Antworte ausschließlich mit diesem JSON-Format:

{{
    "processing_status": "success",
    "article_search": {{
        "found": true,
        "detected_number": "exakte gefundene Nummer oder null",
        "location": "detaillierte Fundort-Beschreibung",
        "similar_numbers": ["alle ähnlichen Nummern mit Übereinstimmungsgrad"]
    }},
    "batch_search": {{
        "found": true,
        "detected_number": "exakte gefundene Chargennummer oder null",
        "location": "detaillierte Fundort-Beschreibung",
        "partial_matches": ["alle Teilübereinstimmungen"]
    }},
    "document_analysis": {{
        "types": ["Array der gemappten Standardkategorien"],
        "primary_type": "Hauptdokumenttyp aus Standardkategorien",
        "type_indicators": ["Spezifische Begriffe die zur Kategorisierung führten"],
        "mapping_applied": {{
            "Messprotokoll": ["Liste der gefundenen Messprotokoll-Indikatoren"],
            "Materialzeugnis": ["Liste der gefundenen Materialzeugnis-Indikatoren"],
            "Härtezeugnis": ["Liste der gefundenen Härtezeugnis-Indikatoren"],
            "Beschichtungszeugnis": ["Liste der gefundenen Beschichtungszeugnis-Indikatoren"]
        }}
    }},
    "confidence": {{
        "level": "hoch",
        "reasoning": "Detaillierte Begründung basierend auf gefundenen Indikatoren",
        "limitations": ["Faktoren die Analyse erschwerten"]
    }},
    "additional_findings": {{
        "notes": "Relevante zusätzliche Beobachtungen",
        "recommendations": "Empfehlungen für weitere Schritte"
    }},
    "errors": []
}}

WICHTIGE HINWEISE:
- Verwende ausschließlich die vier Standardkategorien: Messprotokoll, Materialzeugnis, Härtezeugnis, Beschichtungszeugnis
- Dokumentiere im mapping_applied Feld nur die tatsächlich gefundenen Indikatoren
- Bei mehreren Dokumenttypen in einem Dokument: alle zutreffenden Kategorien auflisten
- Transparenz bei der Zuordnung: Begründe das Mapping durch konkrete Textstellen
- Bei Unsicherheit lieber found: false setzen als falsche Treffer melden

QUALITÄTSKONTROLLE:
1. Wurde INTENSIVE Suche nach beiden Nummern durchgeführt?
2. Sind die Mapping-Kriterien korrekt angewendet?
3. JSON-Syntax validiert?
4. Sind alle type_indicators aus dem Dokument entnommen?"""

    def _get_base_validation_template(self) -> str:
        """Basis Self-Validation Schema für alle Prompts."""
        return """
    "validation_status": {{
        "completeness_score": 0-100,
        "missing_critical_fields": ["array", "of", "missing", "fields"],
        "uncertain_extractions": ["field.path.if.unsure"],
        "user_guidance": "Konkrete Hilfestellung für den User",
        "document_quality": "gut|mittel|schlecht",
        "extraction_confidence": "hoch|mittel|niedrig",
        "manual_review_needed": false
    }}
        """


# Global instance
prompt_manager = PromptTemplateManager()
