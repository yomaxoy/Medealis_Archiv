# Server-Storage Anleitung

## 📋 Übersicht

Das Medealis-System wurde um **Server-Storage-Funktionalität** erweitert. Dokumente können jetzt zentral auf dem Firmenserver (Netzlaufwerk `A:\`) gespeichert werden.

---

## 🎯 Neue Funktionalität

### **Hinzugefügte Methoden im `PathResolver`:**

1. **`server_storage_path`** (Property)
   - Basis-Pfad auf Server: `A:\Qualitätsmanagement\QM_Medealis\03. Produkte\Chargenverwaltung\Produktionsunterlagen\`
   - Automatische Validierung ob Laufwerk `A:\` verfügbar ist

2. **`resolve_server_storage_path(context, create_folders=True)`**
   - Erstellt vollständigen Server-Pfad für Dokumente
   - Identische Struktur wie lokale Speicherung
   - Pfad: `{Server-Basis}\{Lieferant}\{Hersteller}\{Artikelnummer}\{Chargennummer}\{Lieferscheinnummer}\`

3. **`resolve_server_delivery_slip_path(supplier_name, create_folders=True)`**
   - Spezielle Methode für Lieferscheine auf Server
   - Flache Struktur: `{Server-Basis}\{Lieferant}\Lieferscheine\`

---

## 🔧 Voraussetzungen

### **Netzlaufwerk einrichten:**

Das Netzlaufwerk `A:\` muss auf allen Rechnern verbunden sein:

```bash
# Windows CMD/PowerShell (als Administrator):
net use A: \\10.190.140.10\Allgemein /persistent:yes
```

**Hinweise:**
- `/persistent:yes` sorgt dafür, dass die Verbindung nach Neustart erhalten bleibt
- Bei Domain-Computern erfolgt Authentifizierung automatisch
- Bei Workgroup-Rechnern: Benutzername/Passwort ggf. eingeben

### **Verfügbarkeit prüfen:**

```bash
# Teste ob Laufwerk verfügbar ist:
dir A:\

# Oder in Python:
python -c "from pathlib import Path; print('OK' if Path('A:\\').exists() else 'FEHLER')"
```

---

## 📝 Verwendung im Code

### **Beispiel 1: Dokument auf Server speichern**

```python
from warehouse.application.services.document_storage.path_resolver import path_resolver
from warehouse.application.services.document_storage.storage_context import StorageContextData

# 1. Storage-Context erstellen
context = StorageContextData(
    batch_number="20240415-1234",
    delivery_number="LS24-077",
    article_number="MG0001",
    supplier_name="Primec GmbH",
    supplier_normalized="Primec_GmbH",
    manufacturer="MegaGen"
)

# 2. Server-Pfad auflösen (mit automatischer Ordner-Erstellung)
result = path_resolver.resolve_server_storage_path(
    context,
    create_folders=True
)

if result.success:
    # 3. Dokument speichern
    document_path = result.path / "PDB_MG0001_20240415-1234.pdf"

    with open(document_path, 'wb') as f:
        f.write(document_data)

    print(f"✅ Dokument gespeichert: {document_path}")
else:
    print(f"❌ Fehler: {result.error}")
```

**Ergebnis:**
```
A:\Qualitätsmanagement\QM_Medealis\03. Produkte\Chargenverwaltung\Produktionsunterlagen\
  └── Primec_GmbH\
      └── MegaGen\
          └── MG0001\
              └── 20240415-1234\
                  └── LS24-077\
                      └── PDB_MG0001_20240415-1234.pdf
```

---

### **Beispiel 2: Lieferschein auf Server speichern**

```python
from warehouse.application.services.document_storage.path_resolver import path_resolver

# 1. Server-Lieferschein-Pfad auflösen
result = path_resolver.resolve_server_delivery_slip_path(
    supplier_name="Primec GmbH",
    create_folders=True
)

if result.success:
    # 2. Lieferschein speichern
    lieferschein_path = result.path / "Lieferschein_Primec_LS24-077_2024-04-15.pdf"

    with open(lieferschein_path, 'wb') as f:
        f.write(lieferschein_data)

    print(f"✅ Lieferschein gespeichert: {lieferschein_path}")
else:
    print(f"❌ Fehler: {result.error}")
```

**Ergebnis:**
```
A:\Qualitätsmanagement\QM_Medealis\03. Produkte\Chargenverwaltung\Produktionsunterlagen\
  └── Primec_GmbH\
      └── Lieferscheine\
          └── Lieferschein_Primec_LS24-077_2024-04-15.pdf
```

---

### **Beispiel 3: Fehlerbehandlung**

```python
from warehouse.application.services.document_storage.path_resolver import path_resolver
from pathlib import Path

# Prüfe Server-Verfügbarkeit VOR dem Speichern
if not Path("A:\\").exists():
    print("❌ Server-Laufwerk A:\ nicht verfügbar!")
    print("   Bitte IT-Support kontaktieren oder Netzlaufwerk verbinden.")
    # Fallback: Lokale Speicherung verwenden
    result = path_resolver.resolve_storage_path(context, create_folders=True)
else:
    # Server verfügbar: Server-Speicherung verwenden
    result = path_resolver.resolve_server_storage_path(context, create_folders=True)

# Speichern
if result.success:
    document_path = result.path / filename
    with open(document_path, 'wb') as f:
        f.write(document_data)
else:
    print(f"❌ Speichern fehlgeschlagen: {result.error}")
```

---

## 🧪 Testing

### **Test-Script ausführen:**

```bash
# Im Projekt-Root:
python test_server_storage.py
```

**Das Script testet:**
1. ✅ Server-Laufwerk Verfügbarkeit (`A:\`)
2. ✅ Server-Basis-Pfad Erstellung
3. ✅ Server-Storage-Pfad-Auflösung
4. ✅ Server-Lieferschein-Pfad-Auflösung
5. ✅ Schreibrechte auf Server
6. ✅ Vergleich lokale vs. Server-Struktur

---

## 📊 Pfad-Struktur-Vergleich

| Aspekt | Lokal | Server | SharePoint |
|--------|-------|--------|------------|
| **Basis-Pfad** | `C:\Users\{user}\Medealis\Wareneingang\` | `A:\Qualitätsmanagement\...\Produktionsunterlagen\` | `QM_System_Neu/.../Produktionsunterlagen/` |
| **Struktur** | `{Lieferant}\{Hersteller}\{Artikel}\{Charge}\{LS}` | `{Lieferant}\{Hersteller}\{Artikel}\{Charge}\{LS}` | `{Lieferant}/{Hersteller}/{Artikel}/{Charge}/{LS}` |
| **Lieferscheine** | `{Lieferant}\Lieferscheine\` | `{Lieferant}\Lieferscheine\` | `{Lieferant}/Lieferscheine/` |
| **Verfügbarkeit** | Immer | Nur im Netzwerk | Nur mit Internet |
| **Performance** | Schnell | Mittel (Netzwerk) | Langsam (API) |
| **Backup** | Manuell | Server-Backup | Cloud-Backup |

---

## 🔄 Migration: SharePoint → Server

### **Schritt-für-Schritt:**

#### **1. SharePoint deaktivieren**

Bearbeite `.env` Datei:
```bash
# SharePoint deaktivieren
USE_SHAREPOINT=false
```

#### **2. Code anpassen (in Services die Dokumente speichern)**

**VORHER (SharePoint/Lokal):**
```python
# Alte Methode
path_result = path_resolver.resolve_storage_path(context, create_folders=True)
```

**NACHHER (Server als Standard):**
```python
# Neue Methode für Server
path_result = path_resolver.resolve_server_storage_path(context, create_folders=True)
```

#### **3. Mit Fallback (empfohlen während Übergangsphase):**

```python
from pathlib import Path

# Prüfe Server-Verfügbarkeit
if Path("A:\\").exists():
    # SERVER: Primär-Speicherort
    path_result = path_resolver.resolve_server_storage_path(context, create_folders=True)
    storage_mode = "server"
else:
    # LOKAL: Fallback wenn Server nicht verfügbar
    path_result = path_resolver.resolve_storage_path(context, create_folders=True)
    storage_mode = "local"
    logger.warning("Server nicht verfügbar, speichere lokal als Fallback")

logger.info(f"Speicher-Modus: {storage_mode}")
```

---

## ⚙️ Integration in DocumentStorageService

Der `DocumentStorageService` kann erweitert werden, um Server-Storage als Standard zu nutzen:

```python
# In document_storage_service.py

class DocumentStorageService:

    def __init__(self, use_server_storage: bool = True):
        # ...
        self.use_server_storage = use_server_storage

    def save_document(self, ...):
        # ...

        # 5. PATH RESOLUTION - MIT SERVER-UNTERSTÜTZUNG
        if self.use_server_storage and Path("A:\\").exists():
            # Server-Speicherung (NEU)
            path_result = self.path_resolver.resolve_server_storage_path(
                context, create_folders=True
            )
            storage_location = "server"
        else:
            # Lokale Speicherung (Fallback)
            path_result = self.path_resolver.resolve_storage_path(
                context, create_folders=True
            )
            storage_location = "local"

        # ...

        result.metadata['storage_location'] = storage_location
```

---

## 🚨 Troubleshooting

### **Problem: "Server-Laufwerk A:\ nicht verfügbar"**

**Lösung:**
```bash
# Prüfe Laufwerk-Verbindung:
net use

# Wenn nicht verbunden, verbinde neu:
net use A: \\10.190.140.10\Allgemein /persistent:yes

# Teste Zugriff:
dir A:\
```

### **Problem: "Keine Berechtigung zum Erstellen"**

**Lösung:**
- Kontaktiere IT-Administrator für Schreibrechte auf `A:\Qualitätsmanagement\...`
- Prüfe ob Benutzer zur richtigen Active Directory Gruppe gehört
- Teste mit: `echo test > A:\test.txt`

### **Problem: "Pfad zu lang" (Windows MAX_PATH)**

**Lösung:**
- Windows hat 260-Zeichen-Limit für Pfade
- Server-Pfad ist kürzer als lokaler Pfad (`A:\` vs. `C:\Users\{user}\...`)
- Falls Problem auftritt: Artikelnummern/Chargennummern kürzen

---

## 📈 Vorteile Server-Storage

✅ **Zentrale Verwaltung:** Alle Dokumente an einem Ort
✅ **Backup:** Automatisches Server-Backup
✅ **Zugriff:** Von allen Rechnern im Netzwerk
✅ **Konsistenz:** Gleiche Ordnerstruktur wie bisher
✅ **Performance:** Schneller als SharePoint
✅ **Offline:** Funktioniert auch ohne Internet

---

## 📞 Support

Bei Problemen:
1. Test-Script ausführen: `python test_server_storage.py`
2. Log-Ausgaben prüfen
3. IT-Support kontaktieren für Netzwerk-/Berechtigungs-Probleme

---

**Stand:** 2025-01-13
**Version:** 1.0
**Status:** Produktionsreif ✅
