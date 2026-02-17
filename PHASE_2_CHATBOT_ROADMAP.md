# Phase 2: In-App QMS-Chatbot mit Tool Use

**Erstellt:** 2026-02-12
**Status:** Geplant
**Vorgaenger:** Phase 1 (KI-Abstraktion + MCP-Server) - abgeschlossen
**Ziel:** KI-Chatbot in der Streamlit-App, der ueber Tool Use auf DB, NAS und SharePoint zugreift

---

## Ueberblick

### Was aendert sich gegenueber der urspruenglichen Roadmap?

| Aspekt | Roadmap v1 (alt) | Phase 2 v2 (neu) |
|--------|-------------------|-------------------|
| KI-Interface | MCP-Server fuer Claude Code CLI | In-App Chatbot in Streamlit |
| Zielgruppe | Entwickler | Alle Benutzer (QMB, Operator, Admin) |
| Datenzugriff | Neue MCP-Server (NAS, SharePoint) | Tool Use ueber bestehende Services |
| Schreibzugriff | Separate Approval-Queue | Direkt im Chat-Flow mit Bestaetigung |
| NAS/SP | Eigene MCP-Server bauen | Bestehenden Programmzugriff nutzen |

### Architektur-Entscheidung

```
User (Streamlit UI)
  |
  v
ChatView (st.chat_message / st.chat_input)
  |
  v
ChatService (Konversationslogik)
  |-- Nachrichten-Historie (Session State)
  |-- Tool-Execution-Loop
  |-- Audit-Logging
  |
  v
AIClient.chat() [NEU] --> ClaudeProvider.chat() [NEU]
  |                           |
  |                           v
  |                     Anthropic API (messages.create mit tools=[...])
  |                           |
  |                           v
  |                     Response: text ODER tool_use
  |
  v
ToolRegistry [NEU]
  |-- get_suppliers()        --> SupplierService (bestehend)
  |-- get_deliveries()       --> DeliveryService (bestehend)
  |-- get_items()            --> ItemService (bestehend)
  |-- get_orders()           --> OrderService (bestehend)
  |-- query_database()       --> SQLAlchemy Session (bestehend)
  |-- search_nas_files()     --> pathlib/os (bestehender NAS-Zugriff)
  |-- read_nas_file()        --> pathlib/os (bestehender NAS-Zugriff)
  |-- search_sharepoint()    --> SP-Client (bestehender Zugriff)
  |
  v
AuditService.log_chat_interaction() [NEU]
```

---

## Implementierungsplan

### Block 1: Tool Use im Provider (Woche 1)

**Ziel:** AIProvider und ClaudeProvider um Tool-Use-Faehigkeit erweitern.

**Was fehlt aktuell:**
- `AIProvider.generate()` akzeptiert nur `prompt` + `system_prompt`
- `ClaudeProvider._call_with_fallback()` uebergibt kein `tools`-Argument
- `AIResponse` hat kein Feld fuer `tool_use` Blocks
- Keine Multi-Turn-Konversation (nur einzelne `messages=[{"role": "user", ...}]`)

**Aenderungen:**

#### 1.1 `src/ai_service/providers/base.py`

```python
@dataclass
class ToolCall:
    """Ein Tool-Aufruf aus der KI-Antwort."""
    id: str              # tool_use ID (fuer tool_result)
    name: str            # Tool-Name (z.B. "get_suppliers")
    input: dict          # Tool-Parameter

@dataclass
class AIResponse:
    text: str
    model_used: str
    provider: ProviderType
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None
    tool_calls: Optional[list[ToolCall]] = None  # NEU
    stop_reason: Optional[str] = None            # NEU: "end_turn" oder "tool_use"

class AIProvider(ABC):
    # Bestehende Methoden bleiben

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,      # NEU
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> AIResponse:
        """Multi-Turn Chat mit optionalem Tool Use."""
        ...
```

#### 1.2 `src/ai_service/providers/claude_provider.py`

```python
def chat(
    self,
    messages: list[dict],
    system_prompt: Optional[str] = None,
    tools: Optional[list[dict]] = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> AIResponse:
    """Multi-Turn Chat mit Tool Use Support."""
    kwargs = {
        "model": self.default_model,  # mit Fallback
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    if tools:
        kwargs["tools"] = tools

    response = self.client.messages.create(**kwargs)

    # Tool-Calls extrahieren
    tool_calls = []
    text_parts = []
    for block in response.content:
        if block.type == "tool_use":
            tool_calls.append(ToolCall(
                id=block.id,
                name=block.name,
                input=block.input,
            ))
        elif block.type == "text":
            text_parts.append(block.text)

    return AIResponse(
        text="\n".join(text_parts),
        model_used=model,
        provider=ProviderType.CLAUDE,
        usage={...},
        tool_calls=tool_calls or None,
        stop_reason=response.stop_reason,
    )
```

#### 1.3 `src/ai_service/ai_client.py`

```python
def chat(
    self,
    messages: list[dict],
    system_prompt: Optional[str] = None,
    tools: Optional[list[dict]] = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> AIResponse:
    """Multi-Turn Chat mit optionalem Tool Use."""
    self._ensure_available()
    return self._provider.chat(
        messages=messages,
        system_prompt=system_prompt,
        tools=tools,
        max_tokens=max_tokens,
        temperature=temperature,
    )
```

**Dateien betroffen:**
- `src/ai_service/providers/base.py` (ToolCall Dataclass, chat() in ABC)
- `src/ai_service/providers/claude_provider.py` (chat() Implementierung)
- `src/ai_service/ai_client.py` (chat() Durchreichung)

**Abwaertskompatibel:** Ja -- bestehende generate() Methoden bleiben unveraendert.

---

### Block 2: Tool Registry + Tool Definitionen (Woche 1-2)

**Ziel:** Bestehende Services als Claude-Tools exponieren.

#### 2.1 Neues Modul: `src/ai_service/tools/`

```
src/ai_service/tools/
├── __init__.py
├── registry.py         # ToolRegistry: Tool-Schema + Executor-Mapping
├── definitions.py      # Claude-API Tool-Schemas (JSON)
└── executors.py        # Funktionen die die echten Services aufrufen
```

#### 2.2 Tool-Schema Beispiel (definitions.py)

Tools werden im Anthropic-Format definiert:

```python
TOOL_GET_SUPPLIERS = {
    "name": "get_suppliers",
    "description": (
        "Listet alle Lieferanten auf. Optional mit Filter nach "
        "supplier_id oder Name. Gibt Stammdaten zurueck."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "supplier_id": {
                "type": "string",
                "description": "Lieferanten-ID (z.B. 'BEGO'). Leer fuer alle.",
            },
        },
        "required": [],
    },
}

TOOL_GET_DELIVERIES = {
    "name": "get_deliveries",
    "description": (
        "Gibt Lieferungen/Wareneingaenge zurueck. "
        "Optional gefiltert nach Lieferant oder Zeitraum."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "supplier_id": {"type": "string", "description": "Lieferanten-ID"},
            "limit": {"type": "integer", "description": "Max. Ergebnisse", "default": 20},
        },
        "required": [],
    },
}

TOOL_GET_ITEMS = {
    "name": "get_items",
    "description": (
        "Gibt Items/Chargen zurueck inkl. Workflow-Status. "
        "Gefiltert nach Artikelnummer, Lieferscheinnummer oder Charge."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "article_number": {"type": "string"},
            "delivery_number": {"type": "string"},
            "batch_number": {"type": "string"},
        },
        "required": [],
    },
}

TOOL_QUERY_DATABASE = {
    "name": "query_database",
    "description": (
        "Fuehrt eine Read-Only SQL-Query gegen die Datenbank aus. "
        "Nur SELECT erlaubt. Tabellen: suppliers, deliveries, items, "
        "item_info, orders, order_items, item_workflow_steps."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "SQL SELECT-Query"},
        },
        "required": ["sql"],
    },
}

TOOL_SEARCH_NAS = {
    "name": "search_nas_files",
    "description": (
        "Durchsucht das QMS-Dateisystem (NAS) nach Dateien. "
        "Sucht in der QM-Dokumentenstruktur nach Dateinamen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Suchmuster (z.B. '*Bewertung*.pdf')"},
            "base_path": {"type": "string", "description": "Startverzeichnis (optional)"},
        },
        "required": ["pattern"],
    },
}

TOOL_READ_NAS_FILE = {
    "name": "read_nas_file",
    "description": (
        "Liest eine Textdatei vom QMS-Dateisystem (NAS). "
        "Unterstuetzt .txt, .csv, .json, .md Dateien."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Vollstaendiger Dateipfad"},
        },
        "required": ["file_path"],
    },
}

# Alle Tools als Liste
ALL_TOOLS = [
    TOOL_GET_SUPPLIERS,
    TOOL_GET_DELIVERIES,
    TOOL_GET_ITEMS,
    TOOL_QUERY_DATABASE,
    TOOL_SEARCH_NAS,
    TOOL_READ_NAS_FILE,
]
```

#### 2.3 Tool-Executor (executors.py)

Jeder Executor ruft den **bestehenden Service** auf und gibt ein serialisierbares Ergebnis zurueck:

```python
def execute_get_suppliers(supplier_id: str = "") -> str:
    """Wrapper um SupplierService."""
    from warehouse.application.services import supplier_service
    if supplier_id:
        supplier = supplier_service.get_supplier(supplier_id)
        return json.dumps(supplier.to_dict() if supplier else {"error": "Nicht gefunden"})
    else:
        suppliers = supplier_service.list_suppliers()
        return json.dumps([s.to_dict() for s in suppliers])

def execute_query_database(sql: str) -> str:
    """Read-Only SQL mit Validierung (wie MCP-Server)."""
    # Gleiche Validierungslogik wie im MCP-Server
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return json.dumps({"error": error})

    with get_session() as session:
        result = session.execute(text(sql))
        rows = [dict(row._mapping) for row in result.fetchmany(100)]
        return json.dumps(rows, default=str)

def execute_search_nas(pattern: str, base_path: str = "") -> str:
    """Dateien auf NAS suchen (bestehender Zugriff)."""
    nas_root = Path(r"\\10.190.140.10\Allgemein\Qualitaetsmanagement\...")
    search_root = nas_root / base_path if base_path else nas_root
    matches = list(search_root.rglob(pattern))[:50]
    return json.dumps([str(m) for m in matches])
```

#### 2.4 Tool Registry (registry.py)

```python
class ToolRegistry:
    """Zentrale Registry: Tool-Schema <-> Executor Mapping."""

    def __init__(self):
        self._tools: dict[str, dict] = {}        # name -> schema
        self._executors: dict[str, Callable] = {} # name -> executor function

    def register(self, schema: dict, executor: Callable):
        self._tools[schema["name"]] = schema
        self._executors[schema["name"]] = executor

    def get_tool_schemas(self) -> list[dict]:
        """Alle Tool-Schemas fuer die Claude API."""
        return list(self._tools.values())

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """Fuehrt ein Tool aus und gibt das Ergebnis als String zurueck."""
        executor = self._executors.get(tool_name)
        if not executor:
            return json.dumps({"error": f"Unbekanntes Tool: {tool_name}"})
        try:
            return executor(**tool_input)
        except Exception as e:
            return json.dumps({"error": str(e)})

# Singleton mit registrierten Tools
tool_registry = ToolRegistry()
tool_registry.register(TOOL_GET_SUPPLIERS, execute_get_suppliers)
tool_registry.register(TOOL_GET_DELIVERIES, execute_get_deliveries)
# ... etc
```

---

### Block 3: ChatService -- Konversationslogik (Woche 2-3)

**Ziel:** Die zentrale Engine, die Multi-Turn Konversation mit Tool-Execution-Loop steuert.

#### 3.1 Neues Modul: `src/ai_service/chat_service.py`

```python
class ChatService:
    """
    Steuert Multi-Turn Chat mit Tool Use.

    Verwaltet:
    - Nachrichten-Historie
    - Tool-Execution-Loop (max 5 Roundtrips)
    - System-Prompt (QMS-Kontext)
    - Audit-Logging aller Interaktionen
    """

    MAX_TOOL_ROUNDS = 5  # Schutz vor Endlosschleifen

    def __init__(self, ai_client: AIClient, tool_registry: ToolRegistry):
        self.ai_client = ai_client
        self.tool_registry = tool_registry

    def process_message(
        self,
        user_message: str,
        conversation_history: list[dict],
        user_id: str,
    ) -> tuple[str, list[dict]]:
        """
        Verarbeitet eine User-Nachricht.

        1. Haengt User-Nachricht an Historie
        2. Ruft Claude API mit Tools
        3. Falls tool_use: Tool ausfuehren, Ergebnis zurueckfuettern
        4. Wiederholen bis end_turn oder MAX_TOOL_ROUNDS
        5. Finale Textantwort zurueckgeben

        Returns:
            (antwort_text, aktualisierte_history)
        """
        # User-Nachricht anhaengen
        conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        system_prompt = self._build_system_prompt(user_id)
        tools = self.tool_registry.get_tool_schemas()

        for round_num in range(self.MAX_TOOL_ROUNDS):
            response = self.ai_client.chat(
                messages=conversation_history,
                system_prompt=system_prompt,
                tools=tools,
            )

            if response.stop_reason == "tool_use" and response.tool_calls:
                # Assistant-Nachricht (mit tool_use Blocks) an Historie
                conversation_history.append({
                    "role": "assistant",
                    "content": response.raw_response.content,
                    # ^ Wichtig: Original content Blocks (text + tool_use)
                })

                # Tools ausfuehren und Ergebnisse als tool_result anhaengen
                tool_results = []
                for tc in response.tool_calls:
                    result = self.tool_registry.execute(tc.name, tc.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result,
                    })

                    # Audit-Log
                    audit_service.log_action(
                        action="chatbot_tool_call",
                        user=user_id,
                        entity_type="tool",
                        entity_id=tc.name,
                        data={"input": tc.input, "result_length": len(result)},
                    )

                conversation_history.append({
                    "role": "user",
                    "content": tool_results,
                })

            else:
                # Finale Textantwort
                conversation_history.append({
                    "role": "assistant",
                    "content": response.text,
                })

                # Audit-Log
                audit_service.log_action(
                    action="chatbot_response",
                    user=user_id,
                    entity_type="chat",
                    entity_id="",
                    data={
                        "user_message": user_message,
                        "response_length": len(response.text),
                        "tool_rounds": round_num,
                        "model": response.model_used,
                        "tokens": response.usage,
                    },
                )

                return response.text, conversation_history

        # Fallback wenn MAX_TOOL_ROUNDS erreicht
        return (
            "Entschuldigung, die Anfrage war zu komplex. "
            "Bitte versuche es mit einer spezifischeren Frage.",
            conversation_history,
        )

    def _build_system_prompt(self, user_id: str) -> str:
        """Baut den QMS-System-Prompt fuer den Chatbot."""
        return (
            "Du bist der Medealis QMS-Assistent fuer ein "
            "Medizinprodukte-Qualitaetsmanagementsystem.\n\n"
            "Produkte: Dental Locator Abutments (Klasse IIa, MDR 2017/745).\n\n"
            "Du hast Zugriff auf die Warehouse-Datenbank und das "
            "QMS-Dateisystem (NAS). Nutze die verfuegbaren Tools um "
            "Fragen praezise mit echten Daten zu beantworten.\n\n"
            "Regeln:\n"
            "- Antworte auf Deutsch\n"
            "- Nenne immer die Datenquelle\n"
            "- Bei Unsicherheit nachfragen statt raten\n"
            "- Keine Daten erfinden -- nur was die Tools liefern\n"
            f"- Aktueller Benutzer: {user_id}\n"
        )
```

**Kernkonzept -- Tool-Execution-Loop:**
```
User: "Wie viele Lieferungen hatte BEGO?"
  |
  v
Claude: tool_use(get_deliveries, {supplier_id: "BEGO"})
  |
  v
ChatService: fuehrt get_deliveries("BEGO") aus
  |           gibt Ergebnis als tool_result zurueck
  v
Claude: "BEGO hatte 3 Lieferungen im aktuellen Zeitraum: ..."
  |
  v
ChatService: gibt Textantwort an UI zurueck
```

---

### Block 4: Streamlit Chat-UI (Woche 3-4)

**Ziel:** Chat-Interface in der Streamlit-App.

#### 4.1 Neue View: `src/warehouse/presentation/shared/chat_view.py`

```python
import streamlit as st
from ai_service.chat_service import ChatService

def render_chat_view(user_id: str):
    """Chat-Interface fuer den QMS-Assistenten."""

    st.subheader("QMS-Assistent")

    # Session State initialisieren
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []      # Fuer UI-Anzeige
    if "conversation" not in st.session_state:
        st.session_state.conversation = []      # Fuer Claude API

    # Chat-Historie anzeigen
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User-Input
    if prompt := st.chat_input("Frage zum QMS stellen..."):
        # User-Nachricht anzeigen
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append(
            {"role": "user", "content": prompt}
        )

        # Antwort generieren
        with st.chat_message("assistant"):
            with st.spinner("Denke nach..."):
                chat_service = _get_chat_service()
                response_text, updated_conv = chat_service.process_message(
                    user_message=prompt,
                    conversation_history=st.session_state.conversation,
                    user_id=user_id,
                )
                st.session_state.conversation = updated_conv
                st.markdown(response_text)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response_text}
        )

@st.cache_resource
def _get_chat_service() -> ChatService:
    from ai_service import ai_client
    from ai_service.tools import tool_registry
    return ChatService(ai_client, tool_registry)
```

#### 4.2 Integration in Admin-App und User-App

**Option A -- Eigene Seite in der Sidebar:**
```python
# In main_admin_app.py / main_user_app.py
pages = {
    "Dashboard": dashboard_view,
    "Wareneingang": delivery_view,
    # ...
    "QMS-Assistent": chat_view,  # NEU
}
```

**Option B -- Floating Chat-Widget (Expander unten rechts):**
```python
# Am Ende jeder Seite
with st.expander("QMS-Assistent", expanded=False):
    render_chat_view(current_user.user_id)
```

Empfehlung: **Option A** (eigene Seite) fuer Phase 2, Option B spaeter.

---

### Block 5: Chat-Audit-Logging (Woche 3)

**Ziel:** Jede Chat-Interaktion vollstaendig protokollieren (MDR-Compliance).

#### 5.1 Erweiterung AuditService

Neue Audit-Actions:
- `chatbot_message` -- User-Nachricht
- `chatbot_tool_call` -- Tool aufgerufen (welches, mit welchen Parametern)
- `chatbot_response` -- KI-Antwort (Laenge, Model, Token-Verbrauch)
- `chatbot_error` -- Fehler waehrend Chat

#### 5.2 Was geloggt wird

| Feld | Beschreibung |
|------|-------------|
| timestamp | Zeitpunkt |
| user_id | Wer hat gefragt |
| action | chatbot_message / chatbot_tool_call / chatbot_response |
| data.user_message | Die gestellte Frage |
| data.tool_name | Welches Tool aufgerufen wurde |
| data.tool_input | Parameter des Tool-Aufrufs |
| data.response_length | Laenge der Antwort |
| data.model | Verwendetes KI-Modell |
| data.tokens | Input/Output Token-Verbrauch |
| data.tool_rounds | Anzahl Tool-Aufrufe pro Nachricht |

---

### Block 6: Testen + Feinschliff (Woche 4)

**6.1 Manuelle Test-Szenarien:**

| # | User-Frage | Erwartetes Verhalten |
|---|-----------|---------------------|
| 1 | "Welche Lieferanten gibt es?" | Tool: get_suppliers → Liste |
| 2 | "Zeig mir die Lieferungen von BEGO" | Tool: get_deliveries(BEGO) → Tabelle |
| 3 | "Wie viele Items haben wir insgesamt?" | Tool: query_database(SELECT COUNT...) |
| 4 | "Finde Dokumente zu Lieferantenbewertung" | Tool: search_nas_files |
| 5 | "Was ist der Workflow-Status von CT0003?" | Tool: get_items(CT0003) |
| 6 | "Hallo" | Kein Tool, nur Begruessungstext |
| 7 | "Loesche alle Daten" | Kein Tool, Ablehnung |

**6.2 Edge Cases:**
- KI-API nicht erreichbar → Fehlermeldung im Chat
- Tool wirft Exception → Graceful Error im Chat
- Sehr lange Konversation → Context-Limit-Handling
- Kein ANTHROPIC_API_KEY → Chat-Feature deaktiviert
- Nutzer ohne Berechtigung → Chat nicht sichtbar

---

## Zeitplan

| Woche | Block | Deliverables |
|-------|-------|-------------|
| 1 | Tool Use im Provider | chat() in AIProvider, ClaudeProvider, AIClient |
| 1-2 | Tool Registry | Tool-Schemas, Executors, Registry |
| 2-3 | ChatService | Konversationslogik, Tool-Loop, Audit |
| 3-4 | Streamlit Chat-UI | Chat-View, Integration in Apps |
| 4 | Testing + Feinschliff | Testszenarien, Edge Cases, Bugfixes |

**Gesamtdauer:** 4 Wochen

---

## Abgrenzung: Was gehoert NICHT zu Phase 2

- SharePoint-Integration (spaeter, wenn Bedarf konkret wird)
- KI-generierte Dokumente automatisch auf NAS schreiben (Phase 3: Approval)
- Spezialisierte Agents (CAPA, PMS, Supplier Evaluation) (Phase 3)
- FastAPI-Migration (Phase 3+)
- Kosten-Tracking/Budget-Limits (Phase 3)

Phase 2 baut die **Grundlage**: Chat + Tool Use + Audit.
Phase 3 baut darauf **Spezialisten** und **Schreiboperationen**.

---

## Dateien-Uebersicht (Neu + Geaendert)

### Neue Dateien
```
src/ai_service/tools/
├── __init__.py
├── registry.py              # ToolRegistry Klasse
├── definitions.py           # Tool-Schemas (Anthropic-Format)
└── executors.py             # Wrapper um bestehende Services

src/ai_service/chat_service.py   # Konversationslogik + Tool-Loop

src/warehouse/presentation/
└── shared/
    └── chat_view.py         # Streamlit Chat-UI
```

### Geaenderte Dateien
```
src/ai_service/providers/base.py           # ToolCall Dataclass, chat() ABC
src/ai_service/providers/claude_provider.py # chat() mit tools=
src/ai_service/ai_client.py                # chat() Durchreichung
src/ai_service/__init__.py                 # Exports aktualisieren

src/warehouse/presentation/admin/main_admin_app.py  # Chat-Seite hinzufuegen
src/warehouse/presentation/user/main_user_app.py    # Chat-Seite hinzufuegen
```

---

## Risiken und Mitigationen

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| API-Kosten zu hoch | Mittel | Token-Tracking im Audit, Budget-Alert |
| Halluzinationen bei QMS-Daten | Mittel | Tool Use erzwingt echte Daten, System-Prompt "keine Daten erfinden" |
| Langsame Antworten (>10s) | Mittel | Spinner-UI, ggf. Haiku fuer einfache Fragen |
| Context-Limit bei langer Konversation | Niedrig | Historie-Truncation nach N Nachrichten |
| NAS nicht erreichbar | Niedrig | Graceful Error, NAS-Tools optional |

---

## Erfolgskriterien

Phase 2 ist abgeschlossen wenn:
1. Chatbot in der Streamlit-App verfuegbar ist (Admin + User)
2. Mindestens 5 Tools funktionieren (Suppliers, Deliveries, Items, SQL, NAS-Suche)
3. Tool-Execution-Loop korrekt funktioniert (Multi-Step Queries)
4. Jede Interaktion im Audit-Log erscheint
5. Fehlerbehandlung robust ist (API-Ausfall, ungueltige Fragen)
6. Nur authentifizierte Benutzer Zugriff haben
