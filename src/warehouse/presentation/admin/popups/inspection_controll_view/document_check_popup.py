"""
Document Check Popup
Popup for document checking and verification.
"""

import streamlit as st
from datetime import datetime


@st.dialog("📋 Dokumentenprüfung", width="large")
def show_document_check_popup(item_data):
    """
    Document check popup
    """
    st.write("### 📋 Dokumentenprüfung")

    # Item information
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Artikel-Nr:** {item_data.get('article_number', 'N/A')}")
        st.write(f"**Chargen-Nr:** {item_data.get('batch_number', 'N/A')}")
    with col2:
        st.write(f"**Menge:** {item_data.get('quantity', 'N/A')}")
        st.write(f"**LS-Nr:** {item_data.get('delivery_number', 'N/A')}")

    st.divider()

    with st.form("document_check_form"):
        # Document checklist
        st.write("**Erforderliche Dokumente:**")

        col1, col2 = st.columns(2)

        with col1:
            lieferschein = st.selectbox("Lieferschein:", ["✅ Vorhanden", "❌ Fehlend", "⚠️ Unvollständig"])
            rechnung = st.selectbox("Rechnung:", ["✅ Vorhanden", "❌ Fehlend", "⚠️ Unvollständig"])
            zertifikat = st.selectbox("Prüfzertifikat:", ["✅ Vorhanden", "❌ Fehlend", "⚠️ Nicht erforderlich"])

        with col2:
            datenblatt = st.selectbox("Datenblatt:", ["✅ Vorhanden", "❌ Fehlend", "⚠️ Nicht erforderlich"])
            konformitaet = st.selectbox("Konformitätserklärung:", ["✅ Vorhanden", "❌ Fehlend", "⚠️ Nicht erforderlich"])
            sicherheitsdatenblatt = st.selectbox("Sicherheitsdatenblatt:", ["✅ Vorhanden", "❌ Fehlend", "⚠️ Nicht erforderlich"])

        # Data verification
        st.write("**Datenabgleich:**")
        col_data1, col_data2 = st.columns(2)

        with col_data1:
            artikelnummer_ok = st.selectbox("Artikel-Nr. korrekt:", ["✅ Ja", "❌ Nein"])
            menge_ok = st.selectbox("Menge korrekt:", ["✅ Ja", "❌ Nein"])

        with col_data2:
            datum_ok = st.selectbox("Datum korrekt:", ["✅ Ja", "❌ Nein"])
            lieferant_ok = st.selectbox("Lieferant korrekt:", ["✅ Ja", "❌ Nein"])

        # Overall assessment
        st.write("**Gesamtbewertung:**")
        bewertung = st.radio("Dokumentenprüfung:", ["✅ Vollständig", "❌ Unvollständig", "⚠️ Nacharbeit erforderlich"])

        anmerkungen = st.text_area("Anmerkungen:", height=100)

        # Action buttons
        col_save, col_cancel = st.columns(2)

        with col_save:
            if st.form_submit_button("💾 Prüfung speichern", use_container_width=True, type="primary"):
                # Save document check results
                check_data = {
                    'timestamp': datetime.now().isoformat(),
                    'lieferschein': lieferschein,
                    'rechnung': rechnung,
                    'zertifikat': zertifikat,
                    'datenblatt': datenblatt,
                    'konformitaet': konformitaet,
                    'sicherheitsdatenblatt': sicherheitsdatenblatt,
                    'artikelnummer_ok': artikelnummer_ok,
                    'menge_ok': menge_ok,
                    'datum_ok': datum_ok,
                    'lieferant_ok': lieferant_ok,
                    'bewertung': bewertung,
                    'anmerkungen': anmerkungen,
                    'article_number': item_data.get('article_number'),
                    'batch_number': item_data.get('batch_number'),
                    'delivery_number': item_data.get('delivery_number')
                }

                # Store in session state
                if 'document_checks' not in st.session_state:
                    st.session_state.document_checks = {}

                key = f"{item_data.get('article_number')}_{item_data.get('batch_number')}_{item_data.get('delivery_number')}"
                st.session_state.document_checks[key] = check_data

                # Set flags to close popup and trigger main view refresh
                st.session_state.popup_action = 'close_and_refresh'
                st.session_state.show_success_message = "✅ Dokumentenprüfung erfolgreich gespeichert!"
                st.session_state.document_check_saved = True

                st.success("✅ Dokumentenprüfung gespeichert!")
                st.rerun()

        with col_cancel:
            if st.form_submit_button("❌ Abbrechen", use_container_width=True):
                # Set flag to close popup without saving
                st.session_state.popup_action = 'close'
                st.rerun()