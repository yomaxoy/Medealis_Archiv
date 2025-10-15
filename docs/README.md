# 📚 Medealis Warehouse Management - Dokumentation

Willkommen zur Dokumentation des Medealis Warehouse Management Systems!

---

## 📖 Dokumentations-Übersicht

### 🚀 [Setup & Installation](setup/)

Anleitungen zur Installation und Einrichtung des Systems:

- **[INSTALL_DEPENDENCIES.md](setup/INSTALL_DEPENDENCIES.md)** - Python-Abhängigkeiten installieren
- **[LOCAL_OCR_SETUP.md](setup/LOCAL_OCR_SETUP.md)** - Tesseract OCR einrichten (für Lieferschein-Scanning)
- **[LOCAL_PC_DEPLOYMENT.md](setup/LOCAL_PC_DEPLOYMENT.md)** - Lokale Installation auf Windows PC
- **[SERVER_DEPLOYMENT_GUIDE.md](setup/SERVER_DEPLOYMENT_GUIDE.md)** - Server-Deployment als Windows Service

### 🏗️ [Architektur](architecture/)

Technische Architektur und Design-Entscheidungen:

- **[ARCHITECTURE_EXPLANATION.md](architecture/ARCHITECTURE_EXPLANATION.md)** - Clean Architecture Übersicht
- **[DOKUMENTEN_SPEICHERUNG_ARCHITEKTUR.md](architecture/DOKUMENTEN_SPEICHERUNG_ARCHITEKTUR.md)** - Storage-Architektur
- **[DEVELOPMENT_NOTES.md](architecture/DEVELOPMENT_NOTES.md)** - Entwicklungsnotizen & Problem-Fixes

### 📘 [Benutzer-Guides](guides/)

Anleitungen für Administratoren und Entwickler:

- **[DEPLOYMENT_GUIDE.md](guides/DEPLOYMENT_GUIDE.md)** - Allgemeiner Deployment-Guide
- **[DOCUMENT_GENERATION_INSTRUCTIONS.md](guides/DOCUMENT_GENERATION_INSTRUCTIONS.md)** - Template-System
- **[SERVER_STORAGE_ANLEITUNG.md](guides/SERVER_STORAGE_ANLEITUNG.md)** - Storage-Konfiguration

---

## 🔍 Schnellzugriff

### Ich möchte...

**...das System installieren:**
1. Start: [INSTALL_DEPENDENCIES.md](setup/INSTALL_DEPENDENCIES.md)
2. Lokal: [LOCAL_PC_DEPLOYMENT.md](setup/LOCAL_PC_DEPLOYMENT.md)
3. Server: [SERVER_DEPLOYMENT_GUIDE.md](setup/SERVER_DEPLOYMENT_GUIDE.md)

**...die Architektur verstehen:**
1. Überblick: [ARCHITECTURE_EXPLANATION.md](architecture/ARCHITECTURE_EXPLANATION.md)
2. Storage: [DOKUMENTEN_SPEICHERUNG_ARCHITEKTUR.md](architecture/DOKUMENTEN_SPEICHERUNG_ARCHITEKTUR.md)

**...OCR für Lieferscheine einrichten:**
→ [LOCAL_OCR_SETUP.md](setup/LOCAL_OCR_SETUP.md)

**...Dokumente generieren:**
→ [DOCUMENT_GENERATION_INSTRUCTIONS.md](guides/DOCUMENT_GENERATION_INSTRUCTIONS.md)

---

## 🛠️ Entwickler-Ressourcen

### Tests & Tools
- **Tests:** `tests/` - Test-Suite mit pytest
- **Tools:** `tests/tools/` - Hilfs-Skripte (Architektur-Check, Performance-Tests)

### Service-Management
- **Windows Service:** `service/` - Windows Service für Produktiv-Betrieb
- **README:** `service/README.md` - Service-Dokumentation

---

## 📞 Support & Weitere Informationen

- **Haupt-README:** [../README.md](../README.md) - Projekt-Übersicht
- **Architektur-Details:** [architecture/](architecture/) - Technische Details
- **Problem-Fixes:** [architecture/DEVELOPMENT_NOTES.md](architecture/DEVELOPMENT_NOTES.md) - Bekannte Probleme & Lösungen

---

**Version:** 1.0.0
**Letzte Aktualisierung:** 2025-10-14
