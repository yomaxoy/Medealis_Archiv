"""
Measurement Popup - Shared across User & Admin View.

Popup for measurement inspections.
Permission-ready: required_permission="perform_measurement"

Author: Medealis
Version: 2.0.0 - Shared Implementation
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import date
from PIL import Image
import io
from warehouse.presentation.shared.inspection_popup import InspectionPopup
from warehouse.presentation.shared.components import (
    render_article_header,
    FormBuilder,
    render_standard_footer,
    render_document_uploader,
)
from warehouse.application.services.validation_service import validation_service
from warehouse.application.services.audit_service import audit_service
from warehouse.presentation.utils.user_context import get_current_username


class MeasurementPopup(InspectionPopup):
    """Popup für Vermessung mit Ausschuss-Option."""

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__(
            title="📏 Vermessung durchführen",
            item_data=item_data,
            show_info_box=False,
            info_text=None,
            css_style="compact",  # ← Kompaktes CSS
            required_permission="perform_measurement"  # ← Permission-Ready
        )

    def render_header(self) -> None:
        """Rendert kompakten Artikel-Header."""
        # CSS wird automatisch von Base Class angewendet!
        render_article_header(
            article_number=self.article_number,
            batch_number=self.batch_number,
            delivery_number=self.delivery_number,
            quantity=self.quantity,
            status=self.status,
            show_info_box=self.show_info_box,
            info_text=self.info_text,
        )

    def render_body(self) -> Dict[str, Any]:
        """Rendert Formular für Vermessung."""
        # ===== PRÜFERNAME DIREKT ohne FormBuilder =====
        current_user = get_current_username()
        inspector_name = st.text_input(
            "👤 Prüfername: *",
            key="measurement_inspector_name",
            value=current_user if current_user != "System" else "",
            placeholder="Vollständiger Name des Mitarbeiters",
            help="Name des Mitarbeiters der die Vermessung durchführt (Pflichtfeld)",
        )

        form_data = {"measurement_inspector_name": inspector_name}

        st.markdown("---")

        # ===== QR-CODE VISUALISIERUNG (falls vorhanden) =====
        try:
            from warehouse.infrastructure.database.repositories.item_info_repository import (
                item_info_repository,
            )

            item_info = item_info_repository.get_item_info_by_article_number(
                self.article_number
            )

            if item_info and item_info.qr_code_image:
                st.markdown("**📸 QR-Code für diesen Artikel**")
                try:
                    qr_image = Image.open(io.BytesIO(item_info.qr_code_image))
                    col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                    with col_qr2:
                        st.image(
                            qr_image,
                            caption=f"QR-Code: {item_info.qr_code_filename}",
                            width=300,
                        )
                except Exception as img_error:
                    st.warning(f"⚠️ QR-Code konnte nicht angezeigt werden: {img_error}")

                st.markdown("---")
        except Exception as e:
            # Kein QR-Code vorhanden oder Fehler - einfach überspringen
            pass

        # ===== VERMESSUNG DURCHGEFÜHRT (CHECKBOX STATT SELECTBOX) =====
        st.markdown("**📏 Vermessungsstatus**")

        col1, col2 = st.columns(2)
        with col1:
            measurement_performed = st.checkbox(
                "Vermessung durchgeführt *",
                value=False,
                key="measurement_performed",
                help="Bestätigen Sie, dass die Vermessung durchgeführt wurde (Pflichtfeld)",
            )

        with col2:
            measurement_date = st.date_input(
                "Vermessungsdatum:",
                value=date.today(),
                key="measurement_date",
                help="Datum der Vermessung",
            )

        # Speichere in form_data für Rückgabe
        form_data["measurement_performed"] = measurement_performed
        form_data["measurement_date"] = measurement_date

        st.markdown("---")

        # ===== BEMERKUNGEN =====
        st.markdown("**📝 Bemerkungen**")

        measurement_notes = st.text_area(
            "Vermessungsnotizen:",
            key="measurement_notes",
            value="",
            height=60,
            placeholder="Optionale Bemerkungen zur Vermessung...",
            help="Zusätzliche Anmerkungen",
            label_visibility="collapsed",
        )

        form_data["measurement_notes"] = measurement_notes

        # Pflichtfeld-Hinweis
        st.caption("* Pflichtfelder")

        # Sektion 3: Vermessungsprotokolle hochladen
        st.markdown("---")

        uploaded_docs = render_document_uploader(
            label="Vermessungsprotokolle hochladen",
            key="measurement_protocols",
            file_types=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"],
            accept_multiple=True,
            help_text="Laden Sie die Vermessungsprotokolle hoch (mehrere Dateien möglich)",
        )

        # Speichere hochgeladene Dokumente in form_data
        form_data["uploaded_documents"] = uploaded_docs

        return form_data

    def render_footer(self) -> Optional[str]:
        """Rendert Standard-Footer."""
        return render_standard_footer(
            save_label="✅ Vermessung bestätigen", cancel_label="🚫 Abbrechen"
        )

    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """
        Speichert Vermessungsdaten in die Datenbank.

        Args:
            form_data: Formulardaten vom Body
        """
        import logging
        from warehouse.application.services.document_storage.document_storage_service import (
            DocumentStorageService,
        )

        logger = logging.getLogger(__name__)

        try:
            # Extract data
            measurement_performed = form_data.get(
                "measurement_performed", False
            )  # Now boolean from checkbox
            measured_by = form_data.get("measurement_inspector_name", "").strip()
            measurement_date = form_data.get("measurement_date")
            measurement_notes = form_data.get("measurement_notes", "").strip()
            uploaded_docs = form_data.get("uploaded_documents", [])

            article_number = self.item_data.get("article_number", "")
            batch_number = self.item_data.get("batch_number", "")
            delivery_number = self.item_data.get("delivery_number", "")

            # ===== VALIDATION FIRST =====
            validation_data = {
                "measured": measurement_performed,
                "inspector_name": measured_by,
            }

            validation_result = validation_service.validate_measurement(validation_data)

            if not validation_result.is_valid:
                st.error("❌ **Validierungsfehler:**")
                st.error(validation_result.get_formatted_errors())
                return  # Stop execution

            # 1. Save uploaded measurement protocols
            # Neue robuste Implementierung mit DocumentOperationResult
            from warehouse.application.services.document_storage.document_storage_service import (
                DocumentOperationResult,
            )

            operation_result = DocumentOperationResult(
                operation_type="Vermessungsprüfung",
                auto_open=True,  # Dokumente zur Kontrolle öffnen
            )

            if uploaded_docs:
                try:
                    storage_service = DocumentStorageService()
                    st.write("💾 Speichere Vermessungsprotokolle...")

                    for uploaded_file in uploaded_docs:
                        try:
                            document_data = uploaded_file.read()
                            uploaded_file.seek(0)

                            measurement_filename = f"Messprotokoll-{uploaded_file.name}"

                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=measurement_filename,
                                document_type="messprotokoll",
                                batch_number=batch_number,
                                delivery_number=delivery_number,
                                article_number=article_number,
                                supplier_name="",
                            )

                            if save_result.success:
                                operation_result.add_document(save_result)
                            else:
                                operation_result.add_error(
                                    f"{uploaded_file.name}: {save_result.error}"
                                )

                        except Exception as file_error:
                            operation_result.add_error(
                                f"{uploaded_file.name}: {str(file_error)}"
                            )
                            logger.exception(f"Error processing {uploaded_file.name}")

                except Exception as e:
                    logger.exception("Error saving measurement protocols")
                    operation_result.add_error(f"Fehler beim Speichern der Protokolle: {e}")

            # 2. Save measurement to database
            if measurement_performed:  # Now boolean
                try:
                    item_service = st.session_state.services["item"]

                    measurements_dict = {
                        "date": measurement_date.strftime("%Y-%m-%d")
                        if measurement_date
                        else "",
                        "notes": measurement_notes,
                    }

                    success = item_service.complete_measurement(
                        article_number=article_number,
                        batch_number=batch_number,
                        delivery_number=delivery_number,
                        employee=measured_by,
                        measurements=measurements_dict,
                    )

                    if not success:
                        st.error("❌ Fehler beim Speichern der Vermessung in DB")
                        return

                    st.success("✅ Vermessung erfolgreich abgeschlossen!")
                    logger.info(
                        f"Measurement completed: {article_number}#{batch_number}#{delivery_number}"
                    )

                    # ===== AUDIT LOGGING =====
                    audit_service.log_measurement_done(
                        user=measured_by,
                        article_number=article_number,
                        batch_number=batch_number,
                        delivery_number=delivery_number,
                        notes=f"Datum: {measurement_date.strftime('%d.%m.%Y') if measurement_date else 'N/A'}. {measurement_notes if measurement_notes else ''}",
                    )

                except Exception as e:
                    logger.error(f"Error saving measurement: {e}", exc_info=True)
                    st.error(f"❌ Fehler beim Speichern: {e}")
                    return

            else:
                st.info("ℹ️ Vermessung nicht durchgeführt - Status bleibt unverändert")

            # Speichere Result in Session State für Deferred Dialog
            if operation_result.has_documents() or operation_result.errors:
                st.session_state["pending_doc_confirmation"] = operation_result

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
    popup._apply_css()  # CSS anwenden für kompakte Abstände

    # Render Popup
    popup.render_header()
    form_data = popup.render_body()
    action = popup.render_footer()

    # Handle Actions
    if action == "save":
        popup.handle_primary_action(form_data)
    elif action == "cancel":
        st.rerun()
