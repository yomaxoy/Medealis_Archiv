"""
Measurement Popup
User-facing popup for measurement inspections.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import date
from warehouse.presentation.user.popups.core.base_popup import InspectionPopup
from warehouse.presentation.user.popups.components import (
    render_article_header,
    FormBuilder,
    render_standard_footer,
    render_document_uploader
)


class MeasurementPopup(InspectionPopup):
    """Popup für Vermessung mit Ausschuss-Option."""

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__(
            title="📏 Vermessung durchführen",
            item_data=item_data,
            show_info_box=False,
            info_text=None
        )

    def render_header(self) -> None:
        """Rendert kompakten Artikel-Header."""
        # Kompaktes CSS für das gesamte Popup
        st.markdown("""
        <style>
        /* Reduziere Abstände im Dialog */
        div[data-testid="stDialog"] section[data-testid="stVerticalBlock"] {
            gap: 0.2rem !important;
        }

        /* Popup-Titel (h1) - minimaler Abstand */
        div[data-testid="stDialog"] h1 {
            margin-top: 0 !important;
            margin-bottom: 0.3rem !important;
            padding-top: 0 !important;
        }

        /* Kompakte Überschriften */
        div[data-testid="stDialog"] h4 {
            margin-top: 0.5rem !important;
            margin-bottom: 0.3rem !important;
            font-size: 1rem !important;
        }

        div[data-testid="stDialog"] h3 {
            margin-top: 0.2rem !important;
            margin-bottom: 0.3rem !important;
        }

        /* Kompakte Markdown/Text */
        div[data-testid="stDialog"] p {
            margin-bottom: 0.3rem !important;
        }

        /* Kompakte Input-Felder */
        div[data-testid="stDialog"] .stTextInput > div,
        div[data-testid="stDialog"] .stNumberInput > div,
        div[data-testid="stDialog"] .stTextArea > div {
            margin-bottom: 0.2rem !important;
        }

        /* Kompakte Labels */
        div[data-testid="stDialog"] label {
            margin-bottom: 0.2rem !important;
        }

        /* Kompakte Info-Boxen */
        div[data-testid="stDialog"] .stAlert {
            padding: 0.4rem !important;
            margin-top: 0.3rem !important;
            margin-bottom: 0.3rem !important;
        }

        /* Kompakte Divider */
        div[data-testid="stDialog"] hr {
            margin-top: 0.3rem !important;
            margin-bottom: 0.3rem !important;
        }

        /* Kompakte Columns */
        div[data-testid="stDialog"] div[data-testid="column"] {
            gap: 0.2rem !important;
        }

        /* Kompakte Metrics */
        div[data-testid="stDialog"] div[data-testid="metric-container"] {
            padding: 0.3rem !important;
        }
        </style>
        """, unsafe_allow_html=True)

        render_article_header(
            article_number=self.article_number,
            batch_number=self.batch_number,
            delivery_number=self.delivery_number,
            quantity=self.quantity,
            status=self.status,
            show_info_box=self.show_info_box,
            info_text=self.info_text
        )

    def render_body(self) -> Dict[str, Any]:
        """Rendert Formular für Vermessung."""
        form = FormBuilder(columns=2)

        # Vermessungsstatus - OHNE Überschrift
        col1, col2 = st.columns(2)
        with col1:
            measurement_performed = st.selectbox(
                "Vermessung durchgeführt:",
                ["Ja", "Nein"],
                index=0,
                key="measurement_performed",
                help="Wurde die Vermessung durchgeführt?"
            )

        with col2:
            measurement_date = st.date_input(
                "Vermessungsdatum:",
                value=date.today(),
                key="measurement_date",
                help="Datum der Vermessung"
            )

        # Speichere in form_data für Rückgabe
        st.session_state._temp_measurement_performed = measurement_performed
        st.session_state._temp_measurement_date = measurement_date

        # Sektion 1: Bemerkungen
        form.add_section("📝 Bemerkungen", expanded=True, use_expander=False)

        form.add_text_area(
            "Vermessungsnotizen:",
            key="measurement_notes",
            value="",
            height=60,
            placeholder="Bemerkungen zur Vermessung...",
            help="Zusätzliche Anmerkungen"
        )

        # Sektion 2: Prüfer
        form.add_section("👤 Prüfer", expanded=True, use_expander=False)

        form.add_text_input(
            "Vermessen durch:",
            key="measurement_inspector_name",
            value=self.get_current_user(),
            placeholder="Vollständiger Name des Mitarbeiters",
            help="Wird für die Nachvollziehbarkeit benötigt"
        )

        # Render und hole Daten
        form_data = form.render()

        # Füge zusätzliche Felder hinzu
        form_data['measurement_performed'] = st.session_state.get('_temp_measurement_performed', 'Ja')
        form_data['measurement_date'] = st.session_state.get('_temp_measurement_date', date.today())

        # Sektion 3: Vermessungsprotokolle hochladen
        st.markdown("---")

        uploaded_docs = render_document_uploader(
            label="Vermessungsprotokolle hochladen",
            key="measurement_protocols",
            file_types=['pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'],
            accept_multiple=True,
            help_text="Laden Sie die Vermessungsprotokolle hoch (mehrere Dateien möglich)"
        )

        # Speichere hochgeladene Dokumente in form_data
        form_data['uploaded_documents'] = uploaded_docs

        return form_data

    def render_footer(self) -> Optional[str]:
        """Rendert Standard-Footer."""
        return render_standard_footer(
            save_label="✅ Vermessung bestätigen",
            cancel_label="🚫 Abbrechen"
        )

    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """
        Speichert Vermessungsdaten in die Datenbank.

        Args:
            form_data: Formulardaten vom Body
        """
        import logging
        from warehouse.application.services.document_storage.document_storage_service import DocumentStorageService

        logger = logging.getLogger(__name__)

        try:

            # Extract data
            measurement_performed = form_data.get('measurement_performed', 'Ja')
            measured_by = form_data.get('measurement_inspector_name', '').strip()
            measurement_date = form_data.get('measurement_date')
            measurement_notes = form_data.get('measurement_notes', '').strip()
            uploaded_docs = form_data.get('uploaded_documents', [])

            article_number = self.item_data.get('article_number', '')
            batch_number = self.item_data.get('batch_number', '')
            delivery_number = self.item_data.get('delivery_number', '')

            # Validation
            if measurement_performed == "Ja" and not measured_by:
                st.error("⚠️ Bitte geben Sie den Namen des Bearbeiters ein!")
                return

            # 1. Save uploaded measurement protocols
            if uploaded_docs:
                try:
                    storage_service = DocumentStorageService()
                    successful_saves = []
                    failed_saves = []

                    st.write("💾 Speichere Vermessungsprotokolle...")

                    for uploaded_file in uploaded_docs:
                        try:
                            document_data = uploaded_file.read()
                            uploaded_file.seek(0)

                            measurement_filename = f"Vermessungsprotokoll_{article_number}_{uploaded_file.name}"

                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=measurement_filename,
                                document_type="vermessungsprotokoll",
                                batch_number=batch_number,
                                delivery_number=delivery_number,
                                article_number=article_number,
                                supplier_name=''
                            )

                            if save_result.success:
                                successful_saves.append(uploaded_file.name)
                                st.info(f"✅ {uploaded_file.name} → {save_result.file_path}")
                            else:
                                failed_saves.append(f"{uploaded_file.name}: {save_result.error}")

                        except Exception as file_error:
                            failed_saves.append(f"{uploaded_file.name}: {str(file_error)}")

                    if successful_saves:
                        st.success(f"✅ {len(successful_saves)} Vermessungsprotokoll{'e' if len(successful_saves) > 1 else ''} gespeichert!")

                    if failed_saves:
                        st.error(f"❌ Fehler beim Speichern einiger Dateien:")
                        for fail in failed_saves:
                            st.error(f"  • {fail}")

                except Exception as e:
                    logger.error(f"Error saving measurement protocols: {e}")
                    st.warning(f"⚠️ Fehler beim Speichern der Protokolle: {e}")

            # 2. Save measurement to database
            if measurement_performed == "Ja":
                try:
                    item_service = st.session_state.services['item']

                    measurements_dict = {
                        'date': measurement_date.strftime('%Y-%m-%d') if measurement_date else '',
                        'notes': measurement_notes
                    }

                    success = item_service.complete_measurement(
                        article_number=article_number,
                        batch_number=batch_number,
                        delivery_number=delivery_number,
                        employee=measured_by,
                        measurements=measurements_dict
                    )

                    if not success:
                        st.error("❌ Fehler beim Speichern der Vermessung in DB")
                        return

                    st.success("✅ Vermessung erfolgreich abgeschlossen!")
                    logger.info(f"Measurement completed: {article_number}#{batch_number}#{delivery_number}")

                except Exception as e:
                    logger.error(f"Error saving measurement: {e}", exc_info=True)
                    st.error(f"❌ Fehler beim Speichern: {e}")
                    return

            else:
                st.info("ℹ️ Vermessung nicht durchgeführt - Status bleibt unverändert")

            st.success("🎉 **Vermessung erfolgreich bestätigt!**")
            st.rerun()

        except Exception as e:
            logger.error(f"Error in measurement: {e}", exc_info=True)
            st.error(f"❌ Fehler beim Speichern: {str(e)}")

    def handle_secondary_action(self, form_data: Dict[str, Any]) -> None:
        """Nicht verwendet für Measurement."""
        pass


@st.dialog("📏 Vermessung durchführen", width="large")
def show_measurement_popup(item_data: Dict[str, Any]) -> None:
    """
    Zeigt Measurement Popup.

    Args:
        item_data: Dictionary mit Item-Informationen
    """
    popup = MeasurementPopup(item_data)

    # Render Popup
    popup.render_header()
    form_data = popup.render_body()
    action = popup.render_footer()

    # Handle Actions
    if action == 'save':
        popup.handle_primary_action(form_data)
    elif action == 'cancel':
        st.rerun()
