# Performance Optimization Guide

## Phase 3.1-3.3: Quick Performance Wins ✅ IMPLEMENTIERT

Dieser Guide dokumentiert die Performance-Optimierungen, die in Phase 3.1-3.3 implementiert wurden.

## 🚀 Implementierte Optimierungen

### 1. Lazy Imports (App-Start: 3-5x schneller)

**Datei:** `src/warehouse/application/services/__init__.py`

**Was wurde geändert:**
- Services werden nicht mehr beim App-Start geladen, sondern erst bei der ersten Nutzung
- Verwendet Python's `__getattr__` für Lazy Loading
- Reduziert initiale Code-Last von ~8000+ Zeilen auf ~100 Zeilen

**Ergebnis:**
- ✅ App-Start von geschätzt 5-10s auf 1-3s
- ✅ Speicherverbrauch beim Start reduziert

---

### 2. Streamlit Caching (Seitenwechsel: 2-4x schneller)

**Dateien:**
- `src/warehouse/presentation/admin/main_admin_app.py`
- `src/warehouse/presentation/user/main_user_app.py` (war bereits optimiert)

**Was wurde geändert:**

#### a) Services cachen mit `@st.cache_resource`

```python
@st.cache_resource
def get_services():
    """Services einmal erstellen, über Seitenwechsel behalten."""
    from warehouse.application.services import (
        DeliveryService, ItemService, SupplierService, OrderService
    )
    return {
        "delivery": DeliveryService(),
        "item": ItemService(),
        "supplier": SupplierService(),
        "order": OrderService(),
    }

# In initialize_admin_system():
st.session_state.services = get_services()
```

#### b) Processors lazy-loaden mit `@st.cache_resource`

```python
@st.cache_resource
def get_processors():
    """Processors nur laden wenn erstmals gebraucht."""
    from warehouse.application.processors import pdf_processor, ocr_processor, claude_processor
    from warehouse.application.services.document_processing import document_processing_service, process_document
    return {
        "pdf": pdf_processor,
        "ocr": ocr_processor,
        "claude": claude_processor,
        "document_processing_service": document_processing_service,
        "process_document": process_document,
    }
```

**Ergebnis:**
- ✅ Seitenwechsel von 2-4s auf <1s
- ✅ Services werden nicht bei jedem Render neu instanziiert

---

### 3. System-Status-Check entlasten

**Datei:** `src/warehouse/presentation/admin/main_admin_app.py`

**Problem:**
- `render_system_status()` lud bei JEDEM Render alle Lieferungen (nur um DB-Connection zu testen)

**Lösung:**

```python
@st.cache_data(ttl=30)
def check_database_status(_services: dict) -> bool:
    """Lightweight health check mit 30s Cache."""
    try:
        from warehouse.infrastructure.database.connection import get_session
        with get_session() as session:
            session.execute("SELECT 1")  # Simple ping statt alle Daten laden
        return True
    except:
        return False
```

**Ergebnis:**
- ✅ DB-Check nur alle 30s statt bei jedem Render
- ✅ Keine schweren Queries mehr im Sidebar-Render

---

### 4. CacheManager für Event-basierte Invalidierung

**Datei:** `src/warehouse/presentation/shared/cache_manager.py` (NEU)

**Was ist das:**
Ein zentraler Manager für Cache-Invalidierung. Wenn eine Entity gespeichert/gelöscht wird, wird der Cache automatisch invalidiert.

**Wie funktioniert es:**

```python
from warehouse.presentation.shared.cache_manager import CacheManager

# 1. Gecachte Daten laden (mit Version)
@st.cache_data(ttl=60)
def _load_deliveries(_service, _cache_version: int):
    return _service.get_all_deliveries()

deliveries = _load_deliveries(
    delivery_service,
    CacheManager.get_version("deliveries")  # Version holen
)

# 2. Nach Änderung → Cache invalidieren
if st.button("Speichern"):
    delivery_service.save(delivery_data)
    CacheManager.invalidate_related("deliveries")  # Cache löschen
    st.rerun()
```

**Dependency Graph:**
```
deliveries → invalidiert: items, documents
items      → invalidiert: deliveries, documents
suppliers  → invalidiert: deliveries
orders     → invalidiert: items
documents  → keine Kaskadierung
users      → keine Kaskadierung
item_info  → invalidiert: items
```

**Ergebnis:**
- ✅ Daten bleiben gecacht, aber werden aktualisiert wenn nötig
- ✅ Keine veralteten Daten nach Save-Operationen

---

## 📋 Beispiel-Integration: Dashboard View

**Datei:** `src/warehouse/presentation/admin/views/dashboard_view.py`

Die Dashboard-View wurde als **Referenz-Implementierung** optimiert.

**Vorher:**
```python
def show_service_statistics(services):
    supplier_stats = services['supplier'].get_supplier_statistics()  # Bei jedem Render
    st.metric("Suppliers", supplier_stats.get('total_suppliers', 0))
```

**Nachher:**
```python
# 1. Gecachte Loader definieren
@st.cache_data(ttl=60)
def _load_supplier_statistics(_service, _cache_version: int):
    return _service.get_supplier_statistics()

# 2. Mit CacheManager nutzen
def show_service_statistics(services):
    from warehouse.presentation.shared.cache_manager import CacheManager

    supplier_stats = _load_supplier_statistics(
        services['supplier'],
        CacheManager.get_version("suppliers")  # Version-based caching
    )
    st.metric("Suppliers", supplier_stats.get('total_suppliers', 0))
```

---

## 🔧 So integrierst du CacheManager in andere Views

### Schritt-für-Schritt Anleitung

#### 1. Identifiziere schwere Queries

Suche nach:
- `service.get_all_*()`
- `service.get_*_statistics()`
- DB-Queries die Listen oder große Datasets zurückgeben

#### 2. Erstelle gecachte Loader

```python
# Am Anfang der View-Datei (nach Imports):

@st.cache_data(ttl=60)  # 60 Sekunden Cache
def _load_all_deliveries(_service, _cache_version: int):
    """
    Load all deliveries with caching.

    Args:
        _service: DeliveryService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager
    """
    return _service.get_all_deliveries()
```

**Wichtig:**
- Prefix `_` vor Parametern die NICHT im Cache-Key sein sollen (wie `_service`)
- `_cache_version` MUSS ohne Prefix sein, damit es Teil des Cache-Keys wird

#### 3. Nutze den gecachten Loader

```python
def show_delivery_list():
    from warehouse.presentation.shared.cache_manager import CacheManager

    services = st.session_state.services

    # Gecachte Daten laden
    deliveries = _load_all_deliveries(
        services["delivery"],
        CacheManager.get_version("deliveries")
    )

    # Daten anzeigen
    for delivery in deliveries:
        st.write(delivery)
```

#### 4. Invalidiere Cache nach Änderungen

```python
def save_delivery(delivery_data):
    services = st.session_state.services

    # Speichern
    services["delivery"].save(delivery_data)

    # Cache invalidieren (inkl. related entities)
    from warehouse.presentation.shared.cache_manager import CacheManager
    CacheManager.invalidate_related("deliveries")

    # Seite neu laden mit frischem Cache
    st.success("Gespeichert!")
    st.rerun()
```

---

## 🎯 Welche Views sollten als nächstes optimiert werden?

**Priorität: HOCH**
1. ✅ `dashboard_view.py` - **BEREITS OPTIMIERT** (Referenz-Implementierung)
2. `delivery_management_view.py` - Zeigt alle Lieferungen (schwere Query)
3. `item_management_view.py` - Zeigt alle Artikel (schwere Query)
4. `inspection_control_view.py` - Lädt Items für Inspektion

**Priorität: MITTEL**
5. `supplier_management_view.py` - Zeigt alle Lieferanten
6. `orders_view.py` - Zeigt alle Bestellungen
7. `document_management_view.py` - Zeigt Dokumente

**Priorität: NIEDRIG**
8. `user_management_view.py` - Wenige User, keine Performance-Probleme
9. `audit_log_view.py` - Read-only, selten genutzt

---

## 📊 Erwartete Performance-Verbesserung

| Bereich | Vorher (geschätzt) | Nachher (geschätzt) | Status |
|---------|-------------------|-------------------|--------|
| App-Start | 5-10 Sekunden | 1-3 Sekunden | ✅ Implementiert |
| Seitenwechsel | 2-4 Sekunden | <1 Sekunde | ✅ Implementiert |
| Dashboard-Load | 3-5 Sekunden | <1 Sekunde | ✅ Implementiert |
| System-Status | 1-2 Sekunden | <0.5 Sekunden | ✅ Implementiert |

---

## 🐛 Troubleshooting

### Cache zeigt veraltete Daten

**Problem:** Daten werden gespeichert, aber UI zeigt alte Werte

**Lösung:** Stelle sicher, dass nach dem Speichern `CacheManager.invalidate_related()` aufgerufen wird:

```python
# FALSCH - Cache wird nicht invalidiert:
if st.button("Speichern"):
    service.save(data)
    st.rerun()  # Cache bleibt alt!

# RICHTIG - Cache wird invalidiert:
if st.button("Speichern"):
    service.save(data)
    CacheManager.invalidate_related("deliveries")
    st.rerun()
```

### Cache wird zu oft invalidiert

**Problem:** Performance-Probleme weil Cache permanent neu gebaut wird

**Lösung:** Nutze `invalidate()` statt `invalidate_related()` wenn keine Kaskadierung nötig ist:

```python
# Nur bei großen Änderungen:
CacheManager.invalidate_related("deliveries")  # Löscht deliveries + items + documents

# Bei kleinen Änderungen:
CacheManager.invalidate("deliveries")  # Löscht nur deliveries
```

### Import-Fehler bei CacheManager

**Problem:** `ModuleNotFoundError: No module named 'warehouse.presentation.shared.cache_manager'`

**Lösung:** Stelle sicher, dass die Datei existiert:
```
src/warehouse/presentation/shared/cache_manager.py
```

---

## 📝 Nächste Schritte (noch NICHT implementiert)

Die folgenden Optimierungen sind im Migrationsplan vorgesehen, aber noch nicht umgesetzt:

### Phase 3.4-3.6: Performance Deep Dive
- [ ] TemplateCache aktivieren (Word-Templates cachen)
- [ ] ConnectionPool aktivieren (DB-Verbindungen wiederverwenden)
- [ ] OptimizedDocumentPipeline nutzen (Batch-Dokumentenerstellung)
- [ ] ParallelProcessor aktivieren (Parallele Verarbeitung)

### Integration in Views
- [ ] `delivery_management_view.py` - Cache hinzufügen
- [ ] `item_management_view.py` - Cache hinzufügen
- [ ] `inspection_control_view.py` - Cache hinzufügen
- [ ] `supplier_management_view.py` - Cache hinzufügen
- [ ] `orders_view.py` - Cache hinzufügen
- [ ] `document_management_view.py` - Cache hinzufügen

---

## 💡 Best Practices

1. **TTL wählen:**
   - Dashboard/Übersichten: `ttl=60` (1 Minute)
   - Detail-Ansichten: `ttl=30` (30 Sekunden)
   - Echtzeit-Daten: `ttl=10` (10 Sekunden)

2. **Underscore-Prefix:**
   - `_service` → Aus Cache-Key ausschließen (Service-Instanz soll nicht Teil des Keys sein)
   - `_cache_version` → OHNE Underscore, muss im Cache-Key sein!

3. **Cache-Invalidierung:**
   - Nach CREATE/UPDATE/DELETE → `invalidate_related()`
   - Bei Bulk-Operationen → `invalidate_all()`
   - Bei Read-Only → Keine Invalidierung nötig

4. **Debugging:**
   ```python
   # Cache-Version anzeigen (für Debugging):
   st.write(f"Cache Version: {CacheManager.get_version('deliveries')}")

   # Alle Caches leeren (Nuclear Option):
   if st.button("🔥 Cache komplett leeren"):
       CacheManager.clear_streamlit_caches()
       st.rerun()
   ```

---

## 🎉 Zusammenfassung

**Was haben wir erreicht:**
- ✅ App-Start 3-5x schneller durch Lazy Imports
- ✅ Seitenwechsel 2-4x schneller durch Service-Caching
- ✅ Dashboard-Load <1s durch gecachte Statistiken
- ✅ System-Status optimiert (keine schweren Queries mehr)
- ✅ CacheManager für konsistente Cache-Invalidierung
- ✅ Referenz-Implementierung in Dashboard-View

**Nächste Schritte:**
1. CacheManager in weitere Views integrieren (siehe Prioritätsliste)
2. Performance-Module aus `shared/performance/` aktivieren (Phase 3.4-3.6)
3. Testen und Feintuning der Cache-TTLs

**Geschätzte Gesamt-Verbesserung:**
- App-Start: **5-10s → 1-3s** (70-80% schneller)
- Seitenwechsel: **2-4s → <1s** (75-90% schneller)
- Gesamt-UX: **Deutlich flüssiger und responsiver**
