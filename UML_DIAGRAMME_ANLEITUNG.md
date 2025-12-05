# UML-Diagramme Anleitung - Medealis Wareneingang

Dieses Dokument erklärt, wie Sie die UML-Aktivitätsdiagramme für Ihre Dokumentation verwenden können.

---

## 📁 Verfügbare Diagramme

### 1. **Lieferschein-Scan Prozess**
- **Datei**: `UML_ABLAUF_LIEFERSCHEIN_SCAN.md`
- **Fokus**: AI-gestützter Lieferschein-Import
- **Dauer**: ~3-10 Sekunden
- **Komplexität**: Mittel

### 2. **Kompletter Wareneingang-Prozess**
- **Datei**: `UML_ABLAUF_WARENEINGANG_PROZESS.md`
- **Fokus**: Ende-zu-Ende Workflow für einen Artikel
- **Dauer**: ~32-65 Minuten pro Artikel
- **Komplexität**: Hoch

---

## 🎨 Diagramme visualisieren

### **Option 1: PlantUML Online Editor (Einfachste)**

1. Öffnen Sie: https://www.plantuml.com/plantuml/uml/
2. Kopieren Sie den PlantUML-Code aus der `.md` Datei
3. Fügen Sie ihn in den Editor ein
4. Klicken Sie "Submit"
5. Download als PNG/SVG

### **Option 2: PlantUML in VS Code**

1. Installieren Sie VS Code Extension: "PlantUML"
2. Öffnen Sie die `.md` Datei
3. Drücken Sie `Alt+D` (Windows) oder `Opt+D` (Mac)
4. Vorschau erscheint rechts
5. Rechtsklick → "Export Current Diagram"

### **Option 3: PlantUML CLI (Für Batch-Verarbeitung)**

```bash
# Installation (Windows mit Chocolatey)
choco install plantuml

# Installation (Mac mit Homebrew)
brew install plantuml

# Diagramm generieren
plantuml UML_ABLAUF_LIEFERSCHEIN_SCAN.md

# Output: UML_ABLAUF_LIEFERSCHEIN_SCAN.png
```

### **Option 4: Online Tools**

- **PlantText**: https://www.planttext.com/
- **PlantUML QEditor**: https://plantuml-editor.kkeisuke.com/
- **Gravizo**: http://www.gravizo.com/

---

## 📝 Diagramme anpassen

### **Farben ändern**

```plantuml
' Am Anfang des Diagramms hinzufügen:
skinparam backgroundColor #FEFEFE
skinparam activity {
  BackgroundColor<< Good >> LightGreen
  BackgroundColor<< Bad >> Red
  BorderColor DarkSlateGray
}
```

### **Swim Lanes hinzufügen**

```plantuml
|Abteilung 1|
:Aktion 1;

|Abteilung 2|
:Aktion 2;
```

### **Notizen hinzufügen**

```plantuml
:Aktion;
note right
  Zusätzliche Informationen
  zur Aktion
end note
```

### **Parallele Prozesse**

```plantuml
fork
  :Prozess A;
fork again
  :Prozess B;
fork again
  :Prozess C;
end fork
```

---

## 📊 Verwendung in Dokumentation

### **1. Qualitätsmanagement-Handbuch**

Fügen Sie die generierten PNG/SVG Bilder in Ihr QM-Handbuch ein:

```markdown
## 5.2 Wareneingang-Prozess

![Wareneingang Ablauf](UML_ABLAUF_WARENEINGANG_PROZESS.png)

Der Wareneingang-Prozess umfasst 7 Phasen...
```

### **2. Mitarbeiter-Schulungsunterlagen**

Nutzen Sie die Diagramme für:
- Onboarding neuer Mitarbeiter
- Prozess-Schulungen
- SOPs (Standard Operating Procedures)

### **3. ISO-Zertifizierung**

Die Diagramme dokumentieren:
- Prozess-Transparenz
- Verantwortlichkeiten
- Qualitätssicherungs-Schritte
- Nachvollziehbarkeit

### **4. Software-Dokumentation**

Für technische Dokumentation:
- System-Architektur
- Datenfluss
- API-Interaktionen

---

## 🔄 Diagramme aktualisieren

Wenn sich Ihr Prozess ändert:

1. **Öffnen Sie** die entsprechende `.md` Datei
2. **Bearbeiten Sie** den PlantUML-Code
3. **Generieren Sie** das Diagramm neu
4. **Aktualisieren Sie** Ihre Dokumentation

### Beispiel: Neuen Schritt hinzufügen

```plantuml
' Vorher:
:Schritt 1;
:Schritt 3;

' Nachher:
:Schritt 1;
:Schritt 2 (NEU);  # ← Neuer Schritt
note right: Beschreibung
:Schritt 3;
```

---

## 🎓 PlantUML Schnellreferenz

### **Grundelemente**

```plantuml
start               # Start des Prozesses
:Aktion;           # Aktivität
stop               # Ende
```

### **Entscheidungen**

```plantuml
if (Bedingung?) then (ja)
  :Aktion A;
else (nein)
  :Aktion B;
endif
```

### **Schleifen**

```plantuml
repeat
  :Aktion;
repeat while (Weiter?) is (ja) not (nein)
```

### **Partitionen**

```plantuml
partition "Phase 1" {
  :Schritt 1;
  :Schritt 2;
}
```

### **Pfeile mit Label**

```plantuml
:Schritt 1;
-> Erfolg;
:Schritt 2;
```

---

## 📚 Ressourcen

### **PlantUML Dokumentation**
- Official: https://plantuml.com/activity-diagram-beta
- Tutorial: https://plantuml.com/starting

### **Aktivitätsdiagramm Guides**
- UML 2.0: https://www.uml-diagrams.org/activity-diagrams.html
- Best Practices: https://modeling-languages.com/uml-activity-diagram/

### **Tools**
- VS Code Extension: https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml
- IntelliJ Plugin: https://plugins.jetbrains.com/plugin/7017-plantuml-integration

---

## ✅ Checkliste für Ihre Dokumentation

- [ ] PlantUML installiert oder Online-Editor gewählt
- [ ] Beide Diagramme generiert (PNG/SVG)
- [ ] In QM-Handbuch eingefügt
- [ ] Schulungsunterlagen aktualisiert
- [ ] Version und Datum vermerkt
- [ ] Prozess-Verantwortliche informiert

---

## 💡 Tipps

1. **Export-Format**:
   - PNG für einfache Dokumentation
   - SVG für skalierbare Grafiken (z.B. Poster)
   - PDF für offizielle Dokumente

2. **Versionierung**:
   - Speichern Sie die `.md` Dateien in Git
   - Generierte Bilder separat ablegen

3. **Zusammenarbeit**:
   - PlantUML-Code ist Text → einfach zu reviewen
   - Changes sind klar sichtbar in Git Diffs

4. **Automatisierung**:
   - CI/CD Pipeline kann Diagramme automatisch generieren
   - Bei Code-Änderungen Diagramme aktualisieren

---

## 🆘 Häufige Probleme

### **"java.lang.OutOfMemoryError"**
```bash
# Mehr RAM für PlantUML
export JAVA_OPTS="-Xmx2048m"
plantuml diagram.puml
```

### **"Cannot find Graphviz"**
```bash
# Windows (Chocolatey)
choco install graphviz

# Mac (Homebrew)
brew install graphviz
```

### **"Syntax error in PlantUML"**
- Überprüfen Sie fehlende `endif`, `end fork`, etc.
- Verwenden Sie den Online-Editor für Syntax-Highlighting

---

**Erstellt**: 2025-12-04
**Version**: 1.0
**Autor**: Claude (AI-Assistent)
**Projekt**: Medealis Wareneingang-System
