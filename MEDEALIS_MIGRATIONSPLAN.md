# Medealis Archiv – Migrationsplan

## Zusammenfassung

Basierend auf der Code-Analyse (58.600 Zeilen Python, 203 Dateien) und deinen Anforderungen.

**Prioritätsreihenfolge:**
1. Artikelordner öffnen
2. Drucker ansteuern (QuickLabel Etiketten + Konica Dokumente)
3. Performance verbessern (App-Start, Seitenwechsel, Dokumentgenerierung)
4. Programm aufräumen & refactoren
5. Service-Optimierung (Lazy Loading statt Always-On)

---

## Phase 1: Artikelordner öffnen
**Aufwand: ~2-3 Tage | Risiko: Niedrig**

### Ist-Zustand
- `DocumentOpeningService` existiert bereits (`document_operations/document_opening_service.py`)
- `PathResolver` kann Server-Pfade auflösen (`\\10.190.140.10\...\Supplier\Manufacturer\Article\Batch\Delivery`)
- Ordner-Öffnen-Button existiert nur im `document_workflow_handler.py` (nach Dokumenterstellung)
- **Problem:** Der Button fehlt überall dort, wo Artikel angezeigt werden

### Maßnahmen

#### 1.1 Shared Component: "Ordner öffnen"-Button
**Neue Datei:** `src/warehouse/presentation/shared/components/folder_button.py`

```python
def render_open_folder_button(item_data: Dict, key_suffix: str = ""):
    """
    Wiederverwendbarer 'Artikelordner öffnen'-Button.
    Überall einsetzbar wo Artikeldaten vorhanden sind.
    
    Löst Pfad auf via PathResolver → öffnet im Windows Explorer.
    Zeigt Fallback-Meldung wenn Server nicht erreichbar.
    """
```

Benötigt aus `item_data`:
- `article_number`, `batch_number`, `delivery_number`
- `supplier_name`, `manufacturer` (für Pfad-Auflösung)

#### 1.2 Integration in alle Views

| View | Datei | Wo einfügen |
|------|-------|-------------|
| Artikel-Liste | `item_management_view.py` | Pro Zeile in der Tabelle (Icon-Button) |
| Artikel-Detail | `item_management_view.py` | In der Detailansicht oben |
| Wareneingangskontrolle | `inspection_control_view.py` | Pro Artikel im Prüfworkflow |
| Lieferungen-Detail | `delivery_management_view.py` | Pro Artikel in der Lieferung |
| User-View | `main_user_view.py` | In der Artikelübersicht |
| Dokument-Management | `document_management_view.py` | Neben Dokumenten-Aktionen |

#### 1.3 Fallback-Logik
```
1. Versuche Server-Pfad (PathResolver.resolve_server_storage_path)
2. Falls Server nicht erreichbar → Versuche lokalen Pfad (resolve_storage_path)  
3. Falls Ordner nicht existiert → Frage: "Ordner erstellen?"
4. Öffne im Windows Explorer (subprocess.run(['explorer', path]))
```

#### 1.4 Streamlit-Einschränkung beachten
**Wichtig:** Streamlit läuft im Browser – `subprocess.run(['explorer', ...])` funktioniert nur wenn der Streamlit-Server auf derselben Windows-Maschine läuft wie der Browser. Das ist bei euch der Fall (lokaler Server auf :8501/:8502).

Falls ihr das mal auf einem Remote-Server deployen wollt, braucht es einen anderen Ansatz (z.B. Clipboard-Link oder `file://`-Link).

---

## Phase 2: Drucker ansteuern
**Aufwand: ~3-5 Tage | Risiko: Mittel**

### Ist-Zustand
- Barcode-Generierung existiert (`barcode_generator.py`, 765 Zeilen) – erzeugt PNG-Dateien
- Drucken nur über `os.startfile(path, "print")` → öffnet Windows-Druckdialog
- Kein direktes Ansteuern von QuickLabel oder Konica

### Maßnahmen

#### 2.1 Neuer PrinterService
**Neue Datei:** `src/warehouse/application/services/printing/printer_service.py`

```
printing/
├── __init__.py
├── printer_service.py          # Orchestrierung
├── printer_registry.py         # Drucker-Erkennung & Konfiguration
├── label_printer_adapter.py    # QuickLabel-spezifisch
└── document_printer_adapter.py # Konica/Standard-Drucker
```

#### 2.2 QuickLabel-Integration (Etiketten)

**Option A: Über QuickLabel SDK/CLI** (bevorzugt, falls vorhanden)
- Prüfe ob QuickLabel eine API/CLI hat zum direkten Drucken
- Viele QuickLabel-Drucker unterstützen Druck über Druckertreiber mit `win32print`

**Option B: Über Windows-Druckertreiber (`win32print`)**
```python
import win32print
import win32api

class LabelPrinterAdapter:
    def __init__(self, printer_name: str = None):
        # Auto-detect QuickLabel-Drucker oder aus Config laden
        self.printer_name = printer_name or self._find_quicklabel_printer()
    
    def print_label(self, image_path: Path, copies: int = 1):
        """Druckt Barcode-Label direkt auf QuickLabel."""
        # Setzt QuickLabel als Drucker, sendet PNG/PDF
```

**Option C: Über QuickLabel-Templating**
- Falls QuickLabel eine eigene Template-Engine hat:
  Labels dort als Template definieren, aus Python nur Daten übergeben

#### 2.3 Konica-Integration (Dokumente)
```python
class DocumentPrinterAdapter:
    def __init__(self, printer_name: str = None):
        self.printer_name = printer_name or self._find_konica_printer()
    
    def print_document(self, document_path: Path, copies: int = 1):
        """Druckt Dokument auf Konica."""
        # Für DOCX/PDF: win32api.ShellExecute mit spezifischem Drucker
```

#### 2.4 Drucker-Konfiguration
**Neue Config in `.env`:**
```env
LABEL_PRINTER_NAME=QuickLabel Kiaro!
DOCUMENT_PRINTER_NAME=KONICA MINOLTA bizhub
LABEL_PRINTER_ENABLED=true
AUTO_PRINT_LABELS=false
AUTO_PRINT_DOCUMENTS=false
```

#### 2.5 UI-Integration
- **Barcode-Generierung:** Nach Erstellung → Button "🖨️ Etikett drucken" (direkt an QuickLabel)
- **Dokumenterstellung:** Nach Erstellung → Button "🖨️ Drucken" mit Dropdown (Konica oder Standard)
- **Einstellungen-Seite:** Drucker auswählen, Testdruck, Auto-Print konfigurieren

#### 2.6 Dependencies
```
pip install pywin32  # win32print, win32api (vermutlich schon installiert)
```

**Offene Frage:** Welches genaue QuickLabel-Modell nutzt ihr? (Kiaro!, QL-120, etc.) Das bestimmt ob ZPL, ESC/POS oder Druckertreiber der beste Ansatz ist.

---

## Phase 3: Performance verbessern
**Aufwand: ~5-8 Tage | Risiko: Mittel**

### Ist-Zustand — Probleme identifiziert

#### Problem 1: Langsamer App-Start
**Ursache:** `application/services/__init__.py` importiert ALLE Services sofort beim Start:
```python
# ALLES wird sofort geladen (Zeile 25-34):
from .entity_services.delivery_service import DeliveryService    # 1074 Zeilen
from .entity_services.item_service import ItemService            # 1727 Zeilen
from .entity_services.supplier_service import SupplierService
from .entity_services.order_service import OrderService          # 844 Zeilen
from .document_storage import DocumentStorageService             # 1208 Zeilen
from .document_generation import DocumentGenerationService       # 916 Zeilen
from .delivery_workflow_service import DeliveryWorkflowService
from .document_operations import DocumentOpeningService, PDFMergeService
```
→ **~8.000+ Zeilen Code** werden bei jedem Neustart geparst und initialisiert, inkl. aller Imports der Infrastruktur-Layer.

Zusätzlich in `main_admin_app.py` (Zeile 87-117): Processors werden alle sofort geladen (PDF, OCR, Claude).

#### Problem 2: Träge Seitenwechsel
**Ursache:** Kein `@st.cache_data` oder `@st.cache_resource` in der Admin-App (nur 1x in User-App).
→ Bei JEDEM Seitenwechsel werden DB-Queries neu ausgeführt, Services neu instanziiert.

#### Problem 3: Langsame Dokument-Generierung
**Ursache:** Word-Templates werden bei jeder Generation neu geladen. Performance-Module existieren (`shared/performance/`) aber werden NICHT genutzt:
- `TemplateCache` → existiert, nicht verwendet
- `ConnectionPool` → existiert, nicht verwendet
- `ParallelProcessor` → existiert, nicht verwendet

### Maßnahmen

#### 3.1 Lazy Imports (App-Start: geschätzt 3-5x schneller)
**Datei:** `application/services/__init__.py` → Umbauen auf Lazy Loading

```python
# VORHER: Alles sofort importieren
from .entity_services.delivery_service import DeliveryService

# NACHHER: Lazy Import
def __getattr__(name):
    """Lazy-load services nur wenn tatsächlich gebraucht."""
    if name == "DeliveryService":
        from .entity_services.delivery_service import DeliveryService
        return DeliveryService
    # ... etc.
    raise AttributeError(f"module has no attribute {name}")
```

#### 3.2 Streamlit Caching einführen (Seitenwechsel: geschätzt 2-4x schneller)
```python
# In main_admin_app.py:
@st.cache_resource
def get_services():
    """Services einmal erstellen, über Seitenwechsel behalten."""
    return {
        "delivery": DeliveryService(),
        "item": ItemService(),
        "supplier": SupplierService(),
        "order": OrderService(),
    }

@st.cache_data(ttl=30)  # 30 Sekunden Cache
def get_all_deliveries():
    """Lieferungen cachen für schnelle Seitenwechsel."""
    return services["delivery"].get_all_deliveries()
```

#### 3.3 Streamlit Cache gezielt invalidieren (Cache-Aktualität)
**Problem:** Caching bringt nur etwas, wenn die Daten auch aktualisiert werden, wenn sich etwas ändert. Sonst sieht der User veraltete Daten nach dem Speichern.

**Strategie: Event-basierte Cache-Invalidierung**

Jede Schreiboperation (Create/Update/Delete) muss den betroffenen Cache leeren. Dafür gibt es drei Mechanismen:

**A) `st.cache_data.clear()` – Alles leeren (einfachste Variante)**
```python
# Nach jeder Schreiboperation im Service:
def save_delivery(self, delivery_data):
    result = self._repository.save(delivery_data)
    st.cache_data.clear()  # Alle @st.cache_data Caches leeren
    return result
```
→ Einfach, aber löscht ALLE Caches. Für den Anfang ausreichend.

**B) Gezielte Invalidierung mit Cache-Keys (bevorzugt)**
```python
# Cache-Wrapper mit manuellem Invalidieren:
def get_all_deliveries(_service, cache_version: int = 0):
    """cache_version ändert den Key → Cache wird neu gebaut."""
    return _service.get_all_deliveries()

# In session_state einen Counter pro Entität mitführen:
if "cache_version_deliveries" not in st.session_state:
    st.session_state.cache_version_deliveries = 0

# Beim Lesen:
deliveries = get_all_deliveries(
    delivery_service,
    cache_version=st.session_state.cache_version_deliveries
)

# Nach dem Schreiben → Counter erhöhen:
def on_delivery_saved():
    st.session_state.cache_version_deliveries += 1
```

**C) Zentraler CacheManager (langfristig sauberste Lösung)**

**Neue Datei:** `src/warehouse/presentation/shared/cache_manager.py`
```python
class CacheManager:
    """
    Zentraler Cache-Manager für Streamlit.
    Verwaltet Cache-Versionen pro Entität und stellt sicher,
    dass nach Schreiboperationen die richtigen Caches invalidiert werden.
    """
    ENTITIES = ["deliveries", "items", "suppliers", "orders", "documents"]
    
    @staticmethod
    def get_version(entity: str) -> int:
        key = f"_cache_v_{entity}"
        if key not in st.session_state:
            st.session_state[key] = 0
        return st.session_state[key]
    
    @staticmethod
    def invalidate(entity: str):
        """Invalidiert Cache für eine Entität."""
        key = f"_cache_v_{entity}"
        st.session_state[key] = st.session_state.get(key, 0) + 1
    
    @staticmethod
    def invalidate_all():
        """Invalidiert alle Caches (z.B. nach Bulk-Import)."""
        for entity in CacheManager.ENTITIES:
            CacheManager.invalidate(entity)
    
    @staticmethod
    def invalidate_related(entity: str):
        """Invalidiert verwandte Caches.
        Z.B. neue Lieferung → auch Artikel-Cache leeren."""
        relations = {
            "deliveries": ["items", "documents"],
            "items": ["deliveries", "documents"],
            "suppliers": ["deliveries"],
        }
        CacheManager.invalidate(entity)
        for related in relations.get(entity, []):
            CacheManager.invalidate(related)
```

**Verwendung in Views:**
```python
from warehouse.presentation.shared.cache_manager import CacheManager

# Gecachte Abfrage – Version im Key stellt Aktualität sicher:
@st.cache_data(ttl=60)
def _load_deliveries(_service, _version):
    return _service.get_all_deliveries()

deliveries = _load_deliveries(
    delivery_service,
    CacheManager.get_version("deliveries")
)

# Nach Speichern/Löschen:
if save_button_clicked:
    delivery_service.save(data)
    CacheManager.invalidate_related("deliveries")
    st.rerun()  # Seite neu laden mit frischem Cache
```

**Integration in den Workflow:**

| Aktion | Cache-Invalidierung |
|--------|-------------------|
| Neue Lieferung erstellt | `invalidate_related("deliveries")` → leert deliveries + items + documents |
| Artikel bearbeitet | `invalidate_related("items")` → leert items + deliveries + documents |
| Lieferant bearbeitet | `invalidate_related("suppliers")` → leert suppliers + deliveries |
| Dokument generiert | `invalidate("documents")` |
| Sichtprüfung abgeschlossen | `invalidate_related("items")` |
| Bulk-Import | `invalidate_all()` |

**Empfehlung:** Starte mit Variante A (`st.cache_data.clear()`) für schnellen Effekt. Wenn das zu viele Caches löscht und die App dadurch bei häufigen Schreiboperationen wieder langsam wird, auf Variante C (CacheManager) umsteigen.

#### 3.4 Vorhandene Performance-Module aktivieren
Die Module in `shared/performance/` sind **bereits fertig geschrieben** aber nicht eingebunden:

| Modul | Was es tut | Wo einbinden |
|-------|-----------|--------------|
| `TemplateCache` | Word-Templates im Speicher halten | `document_generation_service.py` |
| `ConnectionPool` | DB-Verbindungen wiederverwenden | `connection.py` |
| `OptimizedDocumentPipeline` | Batch-Dokumentenerstellung | `delivery_workflow_service.py` |
| `ParallelProcessor` | Parallele Verarbeitung | `document_generation_service.py` |

#### 3.5 Processor-Initialisierung verschieben
```python
# VORHER (main_admin_app.py Zeile 101-117): ALLES sofort laden
from warehouse.application.processors import pdf_processor, ocr_processor, claude_processor

# NACHHER: Nur laden wenn gebraucht
@st.cache_resource
def get_processors():
    """Processors nur laden wenn erstmals gebraucht."""
    from warehouse.application.processors import pdf_processor, ocr_processor, claude_processor
    return {"pdf": pdf_processor, "ocr": ocr_processor, "claude": claude_processor}
```

#### 3.6 System-Status-Check entlasten
`render_system_status()` (Zeile 261-291) führt bei JEDEM Render einen vollen DB-Query aus:
```python
services["delivery"].get_all_deliveries()  # ALLE Lieferungen laden nur für Status-Check!
```
→ Ersetzen durch `SELECT 1` oder leichtgewichtigen Health-Check.

#### 3.7 Erwartete Verbesserung

| Bereich | Vorher (geschätzt) | Nachher (geschätzt) |
|---------|-------------------|-------------------|
| App-Start | 5-10 Sekunden | 1-3 Sekunden |
| Seitenwechsel | 2-4 Sekunden | <1 Sekunde |
| Dokument-Generierung | 3-8 Sekunden | 1-3 Sekunden |

---

## Phase 4: Programm aufräumen & refactoren
**Aufwand: ~5-10 Tage | Risiko: Mittel-Hoch**

### Ist-Zustand — Hauptprobleme
- 15 Dateien über 700 Zeilen (größte: `item_service.py` mit 1.727 Zeilen)
- Backup-Dateien im Repo (`inspection_control_view.py.backup`)
- Duplizierter Code zwischen Admin- und User-Presentation
- `shared/performance/` Module fertig aber ungenutzt
- Import-Spaghetti: Presentation importiert teilweise direkt aus Infrastructure

### Maßnahmen

#### 4.1 Große Dateien aufteilen

| Datei | Zeilen | Aufteilen in |
|-------|--------|-------------|
| `item_service.py` | 1.727 | `item_crud_service.py` + `item_inspection_service.py` + `item_query_service.py` |
| `document_storage_service.py` | 1.208 | `storage_orchestrator.py` + `storage_operations.py` + `storage_validators.py` |
| `document_management_view.py` | 1.084 | `document_list_view.py` + `document_actions_view.py` + `document_upload_view.py` |
| `merge_check_popup.py` | 1.083 | `merge_popup_ui.py` + `merge_popup_logic.py` |
| `delivery_service.py` | 1.074 | `delivery_crud_service.py` + `delivery_workflow_service.py` (existiert schon!) |
| `path_resolver.py` | 1.038 | `local_path_resolver.py` + `server_path_resolver.py` + `sharepoint_path_resolver.py` |

#### 4.2 Dead Code & Backup entfernen
```bash
# Sofort löschbar:
rm src/warehouse/presentation/admin/views/inspection_control_view.py.backup
# Prüfen ob noch referenziert:
# - update_template.py / update_template_v2.py (root-level)
# - check_items_db.py, check_users.py, debug_*.py (root-level)
# → In /scripts/ verschieben oder entfernen
```

#### 4.3 Shared Components stärken
Code der in Admin UND User identisch ist, in `presentation/shared/` konsolidieren:
- Ordner-Öffnen (Phase 1)
- Drucken (Phase 2)
- Artikel-Anzeige-Komponenten
- Lieferschein-Scan-Popup (schon teilweise geteilt)

#### 4.4 Import-Hygiene
- Alle Presentation-Layer-Imports dürfen NUR Application-Layer nutzen (nie Infrastructure)
- `from warehouse.infrastructure.database...` in Presentation-Dateien finden und über Services wrappen

---

## Phase 5: Service-Optimierung
**Aufwand: ~1-2 Tage | Risiko: Niedrig**

### Ist-Zustand
Der Windows-Service (`service/medealis_service.py`) startet BEIDE Streamlit-Apps permanent und überwacht sie in einer Endlosschleife mit 5-Sekunden-Polling. Wenn eine App crasht, wird sie sofort neu gestartet.

### Maßnahmen

#### 5.1 Lazy-Service-Start (nicht empfohlen)
On-Demand-Start würde 5-10 Sekunden Wartezeit beim ersten Zugriff bedeuten. **Nicht sinnvoll** – besser die App schneller machen (Phase 3).

#### 5.2 Stattdessen: Service optimieren
- **Health-Check statt Polling:** Statt alle 5 Sekunden den Prozess-Status zu checken, einen leichtgewichtigen HTTP-Check auf `/healthz` machen
- **Graceful Restart:** Bei Crash nicht sofort neustarten sondern 10s warten (verhindert Restart-Loops)
- **Memory-Limit:** Streamlit-Prozesse neustarten wenn RAM-Verbrauch >500MB

#### 5.3 Fazit
Die App schneller machen (Phase 3) bringt mehr als den Service-Start zu verzögern. Der Always-On-Service ist für ein Produktivsystem im Firmen-LAN die richtige Architektur.

---

## Umsetzungsreihenfolge (Timeline)

```
Woche 1-2:  Phase 1 (Artikelordner öffnen)
            └── Shared Component + Integration in alle 6 Views

Woche 2-3:  Phase 3.1-3.3 (Quick Performance Wins)
            └── Lazy Imports + Streamlit Caching
            └── Cache-Invalidierung (CacheManager)
            └── System-Status-Check entlasten
            → Sofort spürbare Verbesserung

Woche 3-4:  Phase 2 (Drucker ansteuern)
            └── PrinterService + QuickLabel-Adapter
            └── Konica-Adapter + UI-Integration

Woche 5-6:  Phase 3.4-3.6 (Performance Deep Dive)
            └── TemplateCache aktivieren
            └── ConnectionPool aktivieren
            └── Processor-Lazy-Loading

Woche 6-8:  Phase 4 (Refactoring)
            └── Große Dateien aufteilen
            └── Dead Code entfernen
            └── Import-Hygiene

Woche 8:    Phase 5 (Service-Optimierung)
            └── Health-Check + Graceful Restart
```

---

## Risiken & Hinweise

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|-----------|
| QuickLabel hat keine API/SDK | Mittel | Fallback auf `win32print` über Treiber |
| Refactoring bricht bestehende Funktionen | Mittel | Tests VORHER schreiben, schrittweise migrieren |
| Streamlit-Caching führt zu Stale Data | Niedrig | CacheManager mit Event-basierter Invalidierung (3.3) |
| `subprocess.run(['explorer'])` bei Remote-Deployment | Niedrig | Aktuell kein Problem (lokaler Server) |

---

## Nächster Schritt

Ich empfehle, mit **Phase 1 (Artikelordner öffnen)** zu starten – das ist der schnellste Nutzen mit geringstem Risiko. Soll ich direkt mit dem Code anfangen?
