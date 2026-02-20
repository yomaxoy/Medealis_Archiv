"""
Zentrale CSS-Styles für Popups.

Verhindert Code-Duplikation und ermöglicht konsistentes Design.
Alle Popups (User & Admin) nutzen diese zentralen Styles.

Author: Medealis
Version: 1.0.0
"""

# ===== KOMPAKTES LAYOUT (Standard für User & Admin) =====
COMPACT_POPUP_CSS = """
<style>
/* Reduziere Abstände im Dialog - EXTREM MINIMAL */
div[data-testid="stDialog"] section[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

div[data-testid="stDialog"] section[data-testid="stVerticalBlock"] > div {
    margin: 0 !important;
    padding: 0 !important;
}

/* Popup-Titel (h1) - kein Abstand */
div[data-testid="stDialog"] h1 {
    margin: 0 !important;
    padding: 0 0 0.1rem 0 !important;
}

/* Alle Überschriften - MINIMAL */
div[data-testid="stDialog"] h2,
div[data-testid="stDialog"] h3,
div[data-testid="stDialog"] h4,
div[data-testid="stDialog"] h5,
div[data-testid="stDialog"] h6 {
    margin: 0 !important;
    padding: 0.05rem 0 !important;
}

/* Kompakte Markdown/Text */
div[data-testid="stDialog"] p {
    margin: 0 !important;
    padding: 0 !important;
}

/* Kompakte Input-Felder - KEIN Abstand */
div[data-testid="stDialog"] .stTextInput,
div[data-testid="stDialog"] .stNumberInput,
div[data-testid="stDialog"] .stTextArea,
div[data-testid="stDialog"] .stCheckbox,
div[data-testid="stDialog"] .stSelectbox,
div[data-testid="stDialog"] .stDateInput {
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stDialog"] .stTextInput > div,
div[data-testid="stDialog"] .stNumberInput > div,
div[data-testid="stDialog"] .stTextArea > div,
div[data-testid="stDialog"] .stCheckbox > div,
div[data-testid="stDialog"] .stSelectbox > div,
div[data-testid="stDialog"] .stDateInput > div {
    margin: 0 !important;
    padding: 0 !important;
}

/* Kompakte Labels */
div[data-testid="stDialog"] label {
    margin: 0 !important;
    padding: 0 0 0.05rem 0 !important;
}

/* Kompakte Info-Boxen */
div[data-testid="stDialog"] .stAlert {
    padding: 0.2rem !important;
    margin: 0.1rem 0 !important;
}

/* Kompakte Divider - MINIMAL */
div[data-testid="stDialog"] hr {
    margin: 0.15rem 0 !important;
}

/* Markdown-Container (enthält oft hr) */
div[data-testid="stDialog"] div[data-testid="stMarkdown"] {
    margin: 0 !important;
    padding: 0 !important;
}

/* Expander (FormBuilder Sections) - KEIN ABSTAND */
div[data-testid="stDialog"] details {
    margin: 0 !important;
    padding: 0 !important;
}

/* Expander Summary (Titel) */
div[data-testid="stDialog"] details summary {
    padding: 0.05rem 0 !important;
    margin: 0 !important;
}

/* Kompakte Columns */
div[data-testid="stDialog"] div[data-testid="column"] {
    gap: 0 !important;
    padding: 0 !important;
}

/* Kompakte Metrics */
div[data-testid="stDialog"] div[data-testid="metric-container"] {
    padding: 0 !important;
    margin: 0 !important;
}

/* File Uploader kompakter */
div[data-testid="stDialog"] .stFileUploader {
    margin: 0 !important;
    padding: 0 !important;
}

/* Buttons kompakter */
div[data-testid="stDialog"] .stButton {
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stDialog"] .stButton > button {
    margin: 0 !important;
}

/* Expander kompakter */
div[data-testid="stDialog"] .streamlit-expanderHeader {
    padding: 0.2rem !important;
}

div[data-testid="stDialog"] .streamlit-expanderContent {
    padding: 0.2rem !important;
}

/* Kompakte Selectbox */
div[data-testid="stDialog"] .stSelectbox > div {
    margin-bottom: 0.1rem !important;
    margin-top: 0.1rem !important;
}

/* Kompakte Date Input */
div[data-testid="stDialog"] .stDateInput > div {
    margin-bottom: 0.1rem !important;
    margin-top: 0.1rem !important;
}
</style>
"""


# ===== STANDARD LAYOUT (Streamlit-ähnlich, mehr Luft) =====
STANDARD_POPUP_CSS = """
<style>
/* Standard Abstände im Dialog */
div[data-testid="stDialog"] section[data-testid="stVerticalBlock"] {
    gap: 0.5rem !important;
}

/* Standard Titel */
div[data-testid="stDialog"] h1 {
    margin-bottom: 0.5rem !important;
}

/* Standard Überschriften */
div[data-testid="stDialog"] h4 {
    margin-top: 0.5rem !important;
    margin-bottom: 0.4rem !important;
}

div[data-testid="stDialog"] h3 {
    margin-top: 0.4rem !important;
    margin-bottom: 0.3rem !important;
}

/* Standard Input-Felder */
div[data-testid="stDialog"] .stTextInput > div,
div[data-testid="stDialog"] .stNumberInput > div,
div[data-testid="stDialog"] .stTextArea > div {
    margin-bottom: 0.5rem !important;
}

/* Standard Info-Boxen */
div[data-testid="stDialog"] .stAlert {
    padding: 0.5rem !important;
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Standard Divider */
div[data-testid="stDialog"] hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}
</style>
"""


# ===== WIDE LAYOUT (Große Bildschirme, breitere Popups) =====
WIDE_POPUP_CSS = """
<style>
/* Breitere Popups für große Monitore */
div[data-testid="stDialog"] {
    max-width: 1200px !important;
}

/* Normale Abstände */
div[data-testid="stDialog"] section[data-testid="stVerticalBlock"] {
    gap: 0.8rem !important;
}

/* Mehr Padding */
div[data-testid="stDialog"] .stTextInput > div,
div[data-testid="stDialog"] .stNumberInput > div {
    margin-bottom: 0.8rem !important;
}
</style>
"""


# ===== DOCUMENT CHECK SPEZIAL-CSS (Hervorgehobene Checkboxen) =====
DOCUMENT_CHECK_HIGHLIGHTS_CSS = """
<style>
/* Hervorgehobene Checkboxen für wichtige Bestätigungen */
div[data-testid="stDialog"] div[data-testid="stCheckbox"]:has(label:contains("Label")) {
    background-color: #fff3cd !important;
    padding: 0.5rem !important;
    border-radius: 0.3rem !important;
    border-left: 3px solid #ffc107 !important;
}

div[data-testid="stDialog"] div[data-testid="stCheckbox"]:has(label:contains("Begleitschein")) {
    background-color: #d1ecf1 !important;
    padding: 0.5rem !important;
    border-radius: 0.3rem !important;
    border-left: 3px solid #0dcaf0 !important;
}
</style>
"""


# ===== HELPER FUNCTIONS =====
def get_popup_css(style: str = "compact") -> str:
    """
    Gibt CSS-String für gewünschten Popup-Style zurück.

    Args:
        style: "compact", "standard", oder "wide"

    Returns:
        CSS-String zum Einfügen via st.markdown()

    Beispiel:
        >>> import streamlit as st
        >>> from warehouse.presentation.shared.popup_styles import get_popup_css
        >>> st.markdown(get_popup_css("compact"), unsafe_allow_html=True)
    """
    styles = {
        "compact": COMPACT_POPUP_CSS,
        "standard": STANDARD_POPUP_CSS,
        "wide": WIDE_POPUP_CSS,
    }

    return styles.get(style, COMPACT_POPUP_CSS)


def apply_compact_css() -> None:
    """
    Wendet kompaktes CSS an (Shortcut für direkte Nutzung).

    Beispiel:
        >>> from warehouse.presentation.shared.popup_styles import apply_compact_css
        >>> apply_compact_css()
    """
    import streamlit as st
    st.markdown(COMPACT_POPUP_CSS, unsafe_allow_html=True)


def apply_standard_css() -> None:
    """
    Wendet Standard-CSS an (Shortcut für direkte Nutzung).

    Beispiel:
        >>> from warehouse.presentation.shared.popup_styles import apply_standard_css
        >>> apply_standard_css()
    """
    import streamlit as st
    st.markdown(STANDARD_POPUP_CSS, unsafe_allow_html=True)


def apply_wide_css() -> None:
    """
    Wendet Wide-CSS an (Shortcut für direkte Nutzung).

    Beispiel:
        >>> from warehouse.presentation.shared.popup_styles import apply_wide_css
        >>> apply_wide_css()
    """
    import streamlit as st
    st.markdown(WIDE_POPUP_CSS, unsafe_allow_html=True)


def apply_document_check_highlights() -> None:
    """
    Wendet spezielle CSS-Highlights für Document Check Popup an.

    Hebt Label- und Begleitschein-Checkboxen visuell hervor.
    Sollte zusätzlich zum Standard-CSS verwendet werden.

    Beispiel:
        >>> apply_compact_css()
        >>> apply_document_check_highlights()
    """
    import streamlit as st
    st.markdown(DOCUMENT_CHECK_HIGHLIGHTS_CSS, unsafe_allow_html=True)
