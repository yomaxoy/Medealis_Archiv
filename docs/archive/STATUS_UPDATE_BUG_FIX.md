# Status-Update Bug - Analyse & Fix

## Problem

**Symptom:** Nach dem Speichern im ItemInfo-Dialog (über Main View geöffnet) ändert sich das Icon nicht von 📝 zu ✅, obwohl die Daten korrekt gespeichert werden.

---

## Root Cause Analyse

### 1. Was passiert beim Speichern?

```
User klickt "Speichern" im ItemInfo-Dialog
    ↓
item_info_repository.create_item_info(iteminfo_data)
    ↓
ItemInfo wird in DB gespeichert
    ↓
_set_iteminfo_complete_status() wird aufgerufen
    ↓
Workflow-Status wird gesetzt (iteminfo_complete_by, iteminfo_complete_at)
    ↓
st.rerun() wird aufgerufen
    ↓
Main View lädt Items neu
    ↓
domain_item.is_step_completed("Artikeldetails vollständig") wird geprüft
    ↓
Icon sollte ✅ zeigen
```

### 2. Mögliche Ursachen

**A) Timing-Problem:**
- `st.rerun()` wird aufgerufen BEVOR Session committed wird
- Main View lädt alte Daten aus DB

**B) Session-Isolation:**
- ItemInfo wird in einer Session gespeichert
- Workflow-Status in derselben Session
- Main View lädt in NEUER Session
- Aber: Commit fehlt oder wird zu spät gemacht

**C) Caching:**
- Item-Service cached Items
- Cache wird nicht invalidiert nach ItemInfo-Änderung

---

## Lösung

### Fix 1: Expliziter Commit vor Rerun

**Problem:** `get_session()` Context Manager committed erst am Ende, aber `st.rerun()` passiert vorher.

**Datei:** `src/warehouse/infrastructure/database/repositories/item_info_repository.py`

**Aktueller Code (Zeile 99-109):**
```python
session.add(item_info)
session.flush()

logger.info(f"ItemInfo created for article {item_info_data['article_number']}")

# Automatisch Workflow-Status "Artikeldetails vollständig" setzen
self._set_iteminfo_complete_status(session, item_info_data['article_number'])

# Detach from session
session.expunge(item_info)

return item_info
```

**Fix:**
```python
session.add(item_info)
session.flush()

logger.info(f"ItemInfo created for article {item_info_data['article_number']}")

# Automatisch Workflow-Status "Artikeldetails vollständig" setzen
self._set_iteminfo_complete_status(session, item_info_data['article_number'])

# WICHTIG: Explicit commit BEFORE detach
# Damit Änderungen garantiert in DB sind bevor st.rerun() passiert
session.commit()

# Detach from session
session.expunge(item_info)

return item_info
```

**Gleicher Fix auch in `update_item_info()` (Zeile 146-159):**
```python
session.flush()

logger.info(f"ItemInfo updated for article {article_number}")

# Automatisch Workflow-Status "Artikeldetails vollständig" setzen
self._set_iteminfo_complete_status(session, article_number)

# WICHTIG: Explicit commit
session.commit()

# Detach from session
session.expunge(item_info)

return item_info
```

### Fix 2: Gleicher Fix im ItemService

**Datei:** `src/warehouse/application/services/entity_services/item_service.py`

**Aktueller Code (Zeile 1399-1403):**
```python
session.add(item_info)
session.flush()  # Ensure ItemInfo is created before Item

# Set workflow status for newly created ItemInfo
self._set_iteminfo_complete_status(session, article_number)
```

**Problem:** Kein expliziter Commit, Session wird erst später committed wenn Item gespeichert wird.

**Fix:** In diesem Fall ist es OK, weil die Session später im selben Kontext committed wird. ABER: Wir sollten sicherstellen dass der Status VOR dem Item-Speichern gesetzt wird.

**Keine Änderung nötig** - da alles in derselben Transaktion passiert.

---

## Alternative Lösung: Cache Invalidierung

Falls das Timing-Problem weiterhin besteht, könnten wir einen Cache-Invalidierungs-Mechanismus einbauen:

```python
# item_info_repository.py

def create_item_info(self, item_info_data: Dict[str, Any]) -> Optional[ItemInfoModel]:
    # ... bestehender Code ...

    if result:
        # Invalidiere Item-Cache für diese Artikelnummer
        from warehouse.application.services.entity_services.item_service import item_service
        item_service.invalidate_cache_for_article(article_number)

        return result
```

Aber das ist **NICHT Clean Architecture-konform** (Infrastructure ruft Application auf).

---

## Test-Plan

### Test 1: ItemInfo über Lieferschein-Scan erstellen

1. Lieferschein scannen
2. Artikel werden extrahiert mit automatischer ItemInfo-Erstellung
3. **Erwartung:** Alle Artikel zeigen sofort ✅ in Main View

### Test 2: ItemInfo manuell im Extraction-Popup erstellen

1. Lieferschein scannen
2. Im Extraction-Popup auf 📝 klicken
3. ItemInfo-Dialog ausfüllen und speichern
4. **Erwartung:** Button ändert sich zu ✅ nach Rerun

### Test 3: ItemInfo aus Main View erstellen

1. Artikel existiert (aus Lieferschein)
2. In Main View auf 📝 Button klicken
3. ItemInfo-Dialog ausfüllen und speichern
4. **Erwartung:** Button ändert sich zu ✅ nach Rerun ⚠️ **AKTUELL FEHLERHAFT**

### Test 4: ItemInfo aktualisieren

1. ItemInfo existiert bereits (✅ wird angezeigt)
2. Auf ✅ klicken (Dialog öffnet sich)
3. Daten ändern und speichern
4. **Erwartung:** Button bleibt ✅

---

## Implementierung

### Schritt 1: Fix in item_info_repository.py

```python
# Zeile 99-109 in create_item_info()
session.add(item_info)
session.flush()

logger.info(f"ItemInfo created for article {item_info_data['article_number']}")

# Automatisch Workflow-Status "Artikeldetails vollständig" setzen
self._set_iteminfo_complete_status(session, item_info_data['article_number'])

# EXPLICIT COMMIT before detach to ensure data is in DB before st.rerun()
session.commit()

# Detach from session
session.expunge(item_info)

return item_info
```

```python
# Zeile 146-159 in update_item_info()
session.flush()

logger.info(f"ItemInfo updated for article {article_number}")

# Automatisch Workflow-Status "Artikeldetails vollständig" setzen
self._set_iteminfo_complete_status(session, article_number)

# EXPLICIT COMMIT
session.commit()

# Detach from session
session.expunge(item_info)

return item_info
```

### Schritt 2: Container rebuilden

```bash
docker-compose --env-file .env.migration_test build medealis-user
docker-compose --env-file .env.migration_test up -d
```

### Schritt 3: Testen

1. DB leeren
2. Lieferschein scannen
3. ItemInfo über Main View öffnen und speichern
4. Prüfen ob Icon zu ✅ wechselt

---

## Warum passiert das?

### Context Manager Verhalten

```python
# get_session() Context Manager
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()  # ← Passiert NACH dem yield-Block
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Ablauf OHNE expliziten Commit:

```
1. with get_session() as session:
2.     session.add(item_info)
3.     session.flush()  # Daten in Session, aber NICHT in DB
4.     _set_iteminfo_complete_status(session, ...)  # Status in Session
5.     session.expunge(item_info)
6.     return item_info  # ← Funktion verlässt den with-Block
7. # Jetzt erst: session.commit()  ← DB-Update passiert HIER
```

### Ablauf MIT explizitem Commit:

```
1. with get_session() as session:
2.     session.add(item_info)
3.     session.flush()
4.     _set_iteminfo_complete_status(session, ...)
5.     session.commit()  # ← DB-Update passiert SOFORT
6.     session.expunge(item_info)
7.     return item_info
8. # session.commit() nochmal (idempotent, macht nichts)
```

### Das Problem:

Zwischen Schritt 6 und 7 (OHNE expliziten Commit) passiert `st.rerun()`:

```python
# iteminfo_edit_dialog.py
if result:
    st.success(f"✅ ItemInfo gespeichert!")
    st.session_state.show_iteminfo_edit_dialog = False
    st.rerun()  # ← Passiert BEVOR session.commit() im Context Manager!
```

`st.rerun()` startet die App NEU, lädt Daten aus DB, aber die Änderungen sind noch NICHT committed!

---

## Fazit

**Root Cause:** Timing-Problem zwischen `st.rerun()` und `session.commit()`

**Fix:** Expliziter Commit VOR `return` in Repository-Methoden

**Clean Architecture:** ✅ Fix bleibt in Infrastructure Layer

**Aufwand:** 5 Minuten Code-Änderung + Rebuild

---

## Nächste Schritte

1. ✅ Fix in `item_info_repository.py` implementieren
2. ✅ Container rebuilden
3. ✅ Tests durchführen
4. ✅ Dokumentation aktualisieren
