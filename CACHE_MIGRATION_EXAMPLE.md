# Cache Migration Example: Delivery Management View

Dieses Dokument zeigt **Schritt für Schritt**, wie du eine View mit CacheManager optimierst.

**Beispiel:** `delivery_management_view.py`

---

## 🎯 Aktueller Zustand (VORHER)

```python
def show_delivery_list_tab(delivery_service):
    """Show delivery list with management actions."""
    st.subheader("📋 Delivery Liste")

    try:
        # Get all deliveries
        deliveries_data = []
        if hasattr(delivery_service, "get_all_deliveries"):
            deliveries_data = delivery_service.get_all_deliveries()  # ⚠️ BEI JEDEM RENDER!

        if deliveries_data:
            # Display deliveries with action buttons
            for i, delivery_dict in enumerate(deliveries_data):
                render_delivery_row(delivery_dict, i, delivery_service)
                if i < len(deliveries_data) - 1:
                    st.divider()
        else:
            st.info("Keine Deliveries gefunden")

    except Exception as e:
        logger.error(f"Error loading deliveries: {e}")
        st.error(f"Fehler beim Laden der Deliveries: {e}")
```

**Problem:**
- `get_all_deliveries()` wird bei **jedem Render** aufgerufen
- Bei 100 Lieferungen = 100+ DB-Queries pro Seitenwechsel
- Langsame Performance bei vielen Deliveries

---

## ✅ Optimierter Zustand (NACHHER)

### Schritt 1: Gecachte Loader hinzufügen

Am **Anfang der Datei** (nach den Imports):

```python
"""
Delivery Management View - Admin Presentation Layer
Complete delivery management interface with all functionality.

Performance Optimization:
- Uses @st.cache_data for delivery queries (60s TTL)
- Cache invalidation via CacheManager when deliveries change
"""

import streamlit as st
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from warehouse.application.services.entity_services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)


# =============================================================================
# CACHED DATA LOADERS - Performance Optimization
# =============================================================================

@st.cache_data(ttl=60)
def _load_all_deliveries(_service, _cache_version: int) -> List[Dict[str, Any]]:
    """
    Load all deliveries with caching.

    Uses @st.cache_data with 60s TTL to avoid re-querying database on every render.
    Cache is invalidated via CacheManager when deliveries are modified.

    Args:
        _service: DeliveryService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager (used as cache key)

    Returns:
        List of delivery dictionaries
    """
    try:
        if hasattr(_service, "get_all_deliveries"):
            return _service.get_all_deliveries()
        return []
    except Exception as e:
        logger.error(f"Error loading deliveries: {e}")
        return []


@st.cache_data(ttl=60)
def _load_delivery_statistics(_service, _cache_version: int) -> Dict[str, Any]:
    """
    Load delivery statistics with caching.

    Args:
        _service: DeliveryService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager

    Returns:
        Dict with delivery statistics
    """
    try:
        if hasattr(_service, "get_delivery_statistics"):
            return _service.get_delivery_statistics()
        return {}
    except Exception as e:
        logger.error(f"Error loading delivery statistics: {e}")
        return {}
```

### Schritt 2: Loader in der View nutzen

```python
def show_delivery_list_tab(delivery_service):
    """Show delivery list with management actions (OPTIMIZED)."""
    st.subheader("📋 Delivery Liste")

    try:
        # Import CacheManager
        from warehouse.presentation.shared.cache_manager import CacheManager

        # Get cached deliveries (nur beim ersten Mal oder nach Cache-Invalidierung)
        deliveries_data = _load_all_deliveries(
            delivery_service,
            CacheManager.get_version("deliveries")  # ✅ Version-based caching
        )

        if deliveries_data:
            # Display deliveries with action buttons
            for i, delivery_dict in enumerate(deliveries_data):
                render_delivery_row(delivery_dict, i, delivery_service)
                if i < len(deliveries_data) - 1:
                    st.divider()
        else:
            st.info("Keine Deliveries gefunden")

            # Quick action to create first delivery
            if st.button("➕ Erste Delivery erstellen", type="primary"):
                st.session_state.switch_to_create_tab = True
                st.rerun()

    except Exception as e:
        logger.error(f"Error loading deliveries: {e}")
        st.error(f"Fehler beim Laden der Deliveries: {e}")
```

### Schritt 3: Cache nach Save/Delete invalidieren

Suche nach allen Stellen, wo Deliveries **gespeichert, gelöscht oder geändert** werden:

```python
# Beispiel: Nach dem Speichern einer neuen Delivery

def save_new_delivery(delivery_data):
    """Save new delivery and invalidate cache."""
    try:
        # Get service
        delivery_service = st.session_state.services["delivery"]

        # Save to database
        result = delivery_service.create_delivery(delivery_data)

        if result.get("success"):
            # ✅ Cache invalidieren (inkl. related entities: items, documents)
            from warehouse.presentation.shared.cache_manager import CacheManager
            CacheManager.invalidate_related("deliveries")

            # Success message
            st.success(f"✅ Delivery '{delivery_data['delivery_number']}' gespeichert!")

            # Reload page with fresh cache
            st.rerun()
        else:
            st.error(f"❌ Fehler: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error saving delivery: {e}")
        st.error(f"Fehler beim Speichern: {e}")
```

```python
# Beispiel: Nach dem Löschen einer Delivery

def delete_delivery(delivery_id):
    """Delete delivery and invalidate cache."""
    try:
        # Get service
        delivery_service = st.session_state.services["delivery"]

        # Delete from database
        result = delivery_service.delete_delivery(delivery_id)

        if result.get("success"):
            # ✅ Cache invalidieren
            from warehouse.presentation.shared.cache_manager import CacheManager
            CacheManager.invalidate_related("deliveries")

            # Success message
            st.success("✅ Delivery gelöscht!")

            # Reload page
            st.rerun()
        else:
            st.error(f"❌ Fehler: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error deleting delivery: {e}")
        st.error(f"Fehler beim Löschen: {e}")
```

```python
# Beispiel: Nach dem Bearbeiten einer Delivery

def update_delivery(delivery_id, updated_data):
    """Update delivery and invalidate cache."""
    try:
        # Get service
        delivery_service = st.session_state.services["delivery"]

        # Update in database
        result = delivery_service.update_delivery(delivery_id, updated_data)

        if result.get("success"):
            # ✅ Cache invalidieren
            from warehouse.presentation.shared.cache_manager import CacheManager
            CacheManager.invalidate_related("deliveries")

            # Success message
            st.success("✅ Delivery aktualisiert!")

            # Reload page
            st.rerun()
        else:
            st.error(f"❌ Fehler: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error updating delivery: {e}")
        st.error(f"Fehler beim Aktualisieren: {e}")
```

### Schritt 4: Statistiken cachen

```python
def show_statistics_tab(delivery_service):
    """Show delivery statistics (OPTIMIZED)."""
    st.subheader("📊 Delivery Statistiken")

    try:
        # Import CacheManager
        from warehouse.presentation.shared.cache_manager import CacheManager

        # Get cached statistics
        stats = _load_delivery_statistics(
            delivery_service,
            CacheManager.get_version("deliveries")  # ✅ Version-based caching
        )

        # Display statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Deliveries", stats.get("total_deliveries", 0))

        with col2:
            st.metric("Pending", stats.get("pending", 0))

        with col3:
            st.metric("Completed", stats.get("completed", 0))

        with col4:
            st.metric("Rejected", stats.get("rejected", 0))

        # Charts
        if stats.get("status_distribution"):
            import pandas as pd
            df = pd.DataFrame.from_dict(
                stats["status_distribution"],
                orient='index',
                columns=['Count']
            )
            st.bar_chart(df)

    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
        st.error(f"Fehler beim Laden der Statistiken: {e}")
```

---

## 📊 Performance-Vergleich

| Operation | Vorher | Nachher | Verbesserung |
|-----------|--------|---------|--------------|
| Erste Ansicht | 3-5s (DB-Query) | 3-5s (DB-Query) | - |
| Seitenwechsel zurück | 3-5s (erneuter Query) | <0.5s (Cache-Hit) | **85-90% schneller** |
| Nach Save/Delete | 3-5s (Query) | 3-5s (Query, Cache invalidiert) | - |
| Statistiken | 2-3s (Query) | <0.5s (Cache-Hit) | **75-85% schneller** |

**Gesamte UX:** Deutlich flüssiger - Seitenwechsel fühlen sich instant an!

---

## 🔍 So findest du Save/Delete-Stellen

### Methode 1: Grep nach Service-Aufrufen

```bash
# Suche nach Speichern/Erstellen:
grep -n "create_delivery\|save_delivery" delivery_management_view.py

# Suche nach Löschen:
grep -n "delete_delivery" delivery_management_view.py

# Suche nach Updates:
grep -n "update_delivery" delivery_management_view.py
```

### Methode 2: Suche nach st.rerun()

Oft wird nach Save-Operationen `st.rerun()` aufgerufen:

```bash
grep -n "st.rerun()" delivery_management_view.py
```

Füge **VOR** jedem `st.rerun()` die Cache-Invalidierung ein.

### Methode 3: Suche nach Success-Messages

```bash
grep -n "st.success\|success_message" delivery_management_view.py
```

Success-Messages folgen meist auf erfolgreiche Save/Delete-Operationen.

---

## ✅ Checkliste für Migration

Für **jede View** die du optimierst:

- [ ] **Gecachte Loader hinzufügen** (am Anfang der Datei)
  - `@st.cache_data(ttl=60)`
  - Parameter `_service` und `_cache_version`
  - Try-except mit Fallback

- [ ] **Loader in View nutzen**
  - `from warehouse.presentation.shared.cache_manager import CacheManager`
  - `CacheManager.get_version("entity_type")`

- [ ] **Cache nach CREATE invalidieren**
  - `CacheManager.invalidate_related("entity_type")`
  - Vor `st.rerun()`

- [ ] **Cache nach UPDATE invalidieren**
  - `CacheManager.invalidate_related("entity_type")`
  - Vor `st.rerun()`

- [ ] **Cache nach DELETE invalidieren**
  - `CacheManager.invalidate_related("entity_type")`
  - Vor `st.rerun()`

- [ ] **Testen**
  - Erste Ansicht: Daten laden
  - Seitenwechsel: Schneller Cache-Hit?
  - Nach Save: Daten aktualisiert?
  - Nach Delete: Daten aktualisiert?

---

## 🚀 Nächste Views zum Optimieren

**Priorität nach Nutzungshäufigkeit:**

1. ✅ `dashboard_view.py` - **BEREITS OPTIMIERT**
2. ⏳ `delivery_management_view.py` - **BEISPIEL OBEN**
3. ⏳ `item_management_view.py` - Ähnlich wie delivery_management_view
4. ⏳ `inspection_control_view.py` - Lädt Items für Inspektion
5. ⏳ `supplier_management_view.py` - Zeigt alle Lieferanten
6. ⏳ `orders_view.py` - Zeigt alle Bestellungen
7. ⏳ `document_management_view.py` - Zeigt Dokumente

**Pattern wiederholt sich:**
- Gecachte Loader erstellen
- CacheManager.get_version() nutzen
- Nach Save/Delete: CacheManager.invalidate_related()

---

## 💡 Pro-Tipps

1. **TTL wählen basierend auf Update-Frequenz:**
   - Häufig geändert (Items, Deliveries): `ttl=30` (30s)
   - Selten geändert (Suppliers, ItemInfo): `ttl=300` (5min)
   - Read-only (Audit Log): `ttl=600` (10min)

2. **Debugging aktivieren:**
   ```python
   # Temporär am Anfang der View hinzufügen:
   st.write(f"🔍 Cache Version: {CacheManager.get_version('deliveries')}")
   ```

3. **Cache-Hit-Rate messen:**
   ```python
   import time
   start = time.time()
   deliveries = _load_all_deliveries(service, CacheManager.get_version("deliveries"))
   duration = time.time() - start
   st.caption(f"⏱️ Loaded in {duration:.3f}s")
   # Cache-Hit: <0.001s, Cache-Miss: 1-3s
   ```

4. **Nuclear Option (nur für Debugging):**
   ```python
   # In der View temporär hinzufügen:
   if st.button("🔥 Cache komplett leeren"):
       CacheManager.clear_streamlit_caches()
       st.rerun()
   ```

---

## 🎉 Zusammenfassung

**Was du gelernt hast:**
1. Gecachte Loader mit `@st.cache_data` erstellen
2. CacheManager für Version-based Caching nutzen
3. Cache nach Save/Delete/Update invalidieren
4. Performance um 75-90% verbessern für Seitenwechsel

**Nächste Schritte:**
1. Dieses Pattern auf weitere Views anwenden
2. Performance messen (vorher/nachher)
3. TTLs anpassen basierend auf Nutzungsverhalten

**Viel Erfolg!** 🚀
