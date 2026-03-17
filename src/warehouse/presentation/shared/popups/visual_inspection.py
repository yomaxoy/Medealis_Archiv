"""
Visual Inspection Popup - Shared across User & Admin View.

Sichtkontrolle mit Ausschusserfassung.
Permission-ready: required_permission="perform_visual_inspection"

Author: Medealis
Version: 2.0.0 - Shared Implementation
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from warehouse.presentation.shared.inspection_popup import InspectionPopup
from warehouse.presentation.shared.components import (
    render_article_header,
    FormBuilder,
    render_quality_footer,
)
from warehouse.application.services.validation_service import validation_service
from warehouse.application.services.audit_service import audit_service
from warehouse.presentation.utils.user_context import get_current_username

logger = logging.getLogger(__name__)


class VisualInspectionPopup(InspectionPopup):
    """
    Sichtkontrolle Popup - Shared für User & Admin.

    Features:
    - Ausschussmenge erfassen
    - Qualitätsnotizen
    - Prüfer-Name
    - Artikel zurückweisen (100% Ausschuss)
    - Dokument-Generierung
    """

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__(
            title="👁️ Sichtkontrolle durchführen",
            item_data=item_data,
            show_info_box=False,
            info_text=None,
            css_style="compact",  # ← Kompaktes CSS
            required_permission="perform_visual_inspection"  # ← Permission-Ready
        )

    def render_header(self) -> None:
        """Rendert Artikel-Header mit Infos."""
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
        """Rendert Formular für Sichtkontrolle."""
        form = FormBuilder(columns=2)

        # ===== PRÜFERNAME GANZ OBEN (PFLICHTFELD) =====
        current_user = get_current_username()
        form.add_text_input(
            "👤 Name des Prüfers: *",
            key="visual_inspector_name",
            value=current_user if current_user != "System" else "",
            placeholder="Vollständiger Name des durchführenden Mitarbeiters",
            help="Wird für die Nachvollziehbarkeit benötigt (Pflichtfeld)",
        )

        # Ausschusserfassung (ohne Section-Header)
        form.add_number_input(
            "📊 Ausschussmenge: *",
            key="visual_waste_quantity",
            value=0,
            min_value=0,
            max_value=self.quantity if self.quantity else None,
            help=f"Menge des nicht verwendbaren Materials (Pflichtfeld, max. {self.quantity})",
        )

        # Qualitätsbewertung (ohne Section-Header)
        form.add_text_area(
            "📝 Bemerkungen zur Qualitätskontrolle:",
            key="visual_quality_notes",
            value="",
            height=60,
            placeholder="Optionale Bemerkungen zur Inspektion...",
            help="Beschreiben Sie eventuelle Mängel (optional)",
        )

        # Render und hole Daten
        form_data = form.render()

        # Pflichtfeld-Hinweis
        st.caption("* Pflichtfelder")

        # Zeige Berechnungen
        self._render_waste_calculations(form_data["visual_waste_quantity"])

        return form_data

    def _render_waste_calculations(self, waste_quantity: int) -> None:
        """Zeigt Berechnungen für Ausschuss an."""
        if waste_quantity > 0:
            effective_quantity = max(0, self.quantity - waste_quantity)
            waste_percentage = (
                (waste_quantity / self.quantity * 100) if self.quantity > 0 else 0
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Gesamtmenge", f"{self.quantity}", delta=None)

            with col2:
                st.metric(
                    "Ausschuss",
                    f"{waste_quantity}",
                    delta=f"-{waste_percentage:.1f}%",
                    delta_color="inverse",
                )

            with col3:
                st.metric("Verwendbar", f"{effective_quantity}", delta=None)

            if waste_percentage >= 50:
                st.error(
                    f"⚠️ **Hoher Ausschuss:** {waste_percentage:.1f}% - Bitte Lieferanten kontaktieren!"
                )
            elif waste_percentage >= 10:
                st.warning(f"⚠️ **Erhöhter Ausschuss:** {waste_percentage:.1f}%")

    def render_footer(self) -> Optional[str]:
        """Rendert Quality-Footer mit Ausschuss-Option."""
        return render_quality_footer(
            confirm_label="✅ Prüfung bestätigen",
            reject_label="🗑️ Artikel zurückweisen",
            cancel_label="🚫 Abbrechen",
        )

    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """Wird nicht direkt verwendet - Custom Action Handling."""
        pass

    def handle_confirm_action(self, form_data: Dict[str, Any]) -> None:
        """Verarbeitet Prüfung bestätigen."""
        inspector_name = form_data["visual_inspector_name"].strip()
        waste_quantity = form_data["visual_waste_quantity"]
        quality_notes = form_data["visual_quality_notes"].strip()

        # ===== VALIDATION FIRST =====
        validation_data = {
            "inspector_name": inspector_name,
            "waste_quantity": waste_quantity,
            "total_quantity": self.quantity,  # Business logic validation
            "quality_notes": quality_notes,
            "is_rejection": False,  # Normal inspection, not rejection
        }

        validation_result = validation_service.validate_visual_inspection(
            validation_data
        )

        if not validation_result.is_valid:
            st.error("❌ **Validierungsfehler:**")
            st.error(validation_result.get_formatted_errors())
            return  # Stop execution

        try:
            # Speichere in DB
            from warehouse.application.services.entity_services.item_service import (
                ItemService,
            )

            item_service = ItemService()
            success = item_service.complete_visual_inspection(
                article_number=self.article_number,
                batch_number=self.batch_number,
                delivery_number=self.delivery_number,
                performed_by=inspector_name,
                waste_quantity=waste_quantity,
                quality_notes=quality_notes,
                passed=True,
            )

            if not success:
                self.show_error("Fehler beim Speichern der Sichtkontrolle")
                return

            # Generiere Dokument
            operation_result = self._generate_inspection_document(
                waste_quantity, quality_notes, inspector_name
            )

            # ===== AUDIT LOGGING =====
            audit_service.log_visual_inspection(
                user=inspector_name,
                article_number=self.article_number,
                batch_number=self.batch_number,
                delivery_number=self.delivery_number,
                waste_quantity=waste_quantity,
                passed=True,  # Bei handle_confirm_action ist die Prüfung bestanden
                notes=quality_notes if quality_notes else "Keine Mängel",
            )

            # Speichere Result in Session State für Deferred Dialog
            if operation_result.has_documents() or operation_result.errors:
                st.session_state["pending_doc_confirmation"] = operation_result

            # Erfolg
            self.show_success(
                "✅ Sichtkontrolle erfolgreich abgeschlossen!", with_balloons=True
            )
            self.cleanup_session_state()
            st.rerun()

        except Exception as e:
            logger.error(f"Visual inspection failed: {e}", exc_info=True)
            self.show_error(f"Fehler beim Speichern: {e}")

    def handle_reject_action(self, form_data: Dict[str, Any]) -> None:
        """Verarbeitet Artikel zurückweisen (100% Ausschuss)."""
        inspector_name = form_data["visual_inspector_name"].strip()
        quality_notes = form_data["visual_quality_notes"].strip()

        # ===== VALIDATION FIRST =====
        validation_data = {
            "inspector_name": inspector_name,
            "waste_quantity": self.quantity,  # 100% Ausschuss bei Zurückweisung
            "total_quantity": self.quantity,
            "quality_notes": quality_notes,
            "is_rejection": True,  # Zurückweisung erfordert ausführliche Begründung
        }

        validation_result = validation_service.validate_visual_inspection(
            validation_data
        )

        if not validation_result.is_valid:
            st.error("❌ **Validierungsfehler:**")
            st.error(validation_result.get_formatted_errors())
            return  # Stop execution

        # Bestätigungsdialog
        st.warning("⚠️ **Achtung:** Der gesamte Artikel wird als Ausschuss markiert!")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "🗑️ Ja, zurückweisen",
                type="primary",
                use_container_width=True,
                key="confirm_reject",
            ):
                try:
                    from warehouse.application.services.entity_services.item_service import (
                        ItemService,
                    )

                    item_service = ItemService()
                    success = item_service.mark_item_as_waste(
                        article_number=self.article_number,
                        batch_number=self.batch_number,
                        delivery_number=self.delivery_number,
                        reason=quality_notes,
                        employee=inspector_name,
                    )

                    if not success:
                        self.show_error("Fehler beim Markieren als Ausschuss")
                        return

                    # Generiere Rejection-Dokument
                    operation_result = self._generate_inspection_document(
                        waste_quantity=self.quantity,  # 100% Ausschuss
                        quality_notes=quality_notes,
                        inspector_name=inspector_name,
                        is_rejection=True,
                    )

                    # ===== AUDIT LOGGING =====
                    audit_service.log_visual_inspection(
                        user=inspector_name,
                        article_number=self.article_number,
                        batch_number=self.batch_number,
                        delivery_number=self.delivery_number,
                        waste_quantity=self.quantity,  # 100% Ausschuss bei Zurückweisung
                        passed=False,  # Bei Zurückweisung ist die Prüfung nicht bestanden
                        notes=f"ZURÜCKGEWIESEN: {quality_notes}",
                    )

                    # Speichere Result in Session State für Deferred Dialog
                    if operation_result.has_documents() or operation_result.errors:
                        st.session_state["pending_doc_confirmation"] = operation_result

                    self.show_error("❌ Artikel wurde zurückgewiesen!")
                    self.cleanup_session_state()
                    st.rerun()

                except Exception as e:
                    logger.error(f"Rejection failed: {e}", exc_info=True)
                    self.show_error(f"Fehler: {e}")

        with col2:
            if st.button("↩️ Zurück", use_container_width=True, key="cancel_reject"):
                st.rerun()

    def _generate_inspection_document(
        self,
        waste_quantity: int,
        quality_notes: str,
        inspector_name: str,
        is_rejection: bool = False,
    ) -> "DocumentOperationResult":
        """
        Generiert Sichtkontrolle-Dokument.

        Returns:
            DocumentOperationResult mit allen erstellten Dokumenten
        """
        from pathlib import Path
        from warehouse.application.services.document_generation import (
            DocumentGenerationService,
            DocumentType,
        )
        from warehouse.application.services.document_storage.document_storage_service import (
            DocumentOperationResult,
            StorageResult,
        )

        operation_result = DocumentOperationResult(
            operation_type="Sichtkontrolle" if not is_rejection else "Zurückweisung"
        )

        try:
            with st.spinner("📋 Erstelle Sichtkontrolle-Dokument..."):
                doc_service = DocumentGenerationService()

                # Berechne Ausschussquote
                total_quantity = int(self.quantity)
                if total_quantity > 0:
                    waste_percentage = (waste_quantity / total_quantity) * 100
                    ausschussquote = f"{waste_percentage:.1f}%"
                else:
                    ausschussquote = "0%"

                # Zusatzdaten
                additional_data = {
                    "ausschuss": str(waste_quantity),
                    "ausschussquote": ausschussquote,
                    "name": inspector_name,
                    "qty": str(total_quantity),
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "time": datetime.now().strftime("%H:%M"),
                    "waste_quantity": waste_quantity,
                    "effective_quantity": max(0, total_quantity - waste_quantity),
                    "quality_notes": quality_notes,
                    "status": "Zurückgewiesen" if is_rejection else "Sichtgeprüft",
                    "is_rejection": is_rejection,
                }

                # Generiere Dokument
                result = doc_service.generate_document(
                    document_type=DocumentType.SICHTKONTROLLE,
                    batch_number=self.batch_number,
                    delivery_number=self.delivery_number,
                    article_number=self.article_number,
                    supplier_name=self.supplier_name,
                    quantity=total_quantity,
                    employee_name=inspector_name,
                    additional_data=additional_data,
                )

                if result.success:
                    # DOCX
                    storage_result = StorageResult(
                        success=True,
                        file_path=str(result.document_path) if result.document_path else None,
                        filename=result.document_path.name if result.document_path else None,
                        storage_folder=str(result.document_path.parent) if result.document_path else None,
                        document_type="Sichtkontrolle (DOCX)",
                    )
                    operation_result.add_document(storage_result)

                    # PDF (falls vorhanden)
                    if hasattr(result, "pdf_path") and result.pdf_path:
                        pdf_storage = StorageResult(
                            success=True,
                            file_path=str(result.pdf_path),
                            filename=Path(result.pdf_path).name,
                            storage_folder=str(Path(result.pdf_path).parent),
                            document_type="Sichtkontrolle (PDF)",
                        )
                        operation_result.add_document(pdf_storage)

                    # Zusätzliche Info bei Ausschuss
                    if waste_quantity > 0:
                        operation_result.add_warning(
                            f"Ausschuss dokumentiert: {waste_quantity} Stück ({ausschussquote})"
                        )
                else:
                    operation_result.add_error(f"Dokumentenerstellung fehlgeschlagen: {result.error}")
                    logger.error(f"Document generation failed: {result.error}")

        except Exception as e:
            logger.exception("Document generation error")
            operation_result.add_error(f"Fehler bei Dokumentenerstellung: {e}")

        return operation_result

    def render(self):
        """Override render für Custom Action Handling."""
        try:
            # Header
            self.render_header()

            # Body
            form_data = self.render_body()

            # Footer (Custom mit 3 Buttons)
            action = self.render_footer()

            # Custom Action Handler
            if action == "confirm":
                self.handle_confirm_action(form_data)
            elif action == "reject":
                self.handle_reject_action(form_data)
            elif action == "cancel":
                self.cleanup_session_state()
                st.session_state["popup_action"] = "cancel"
                st.rerun()

        except Exception as e:
            logger.error(f"Visual inspection popup error: {e}", exc_info=True)
            self.show_error(f"Fehler im Popup: {e}")


# ============== Public API ==============


@st.dialog("👁️ Sichtkontrolle durchführen", width="large")
def show_visual_inspection_popup(item_data: Dict[str, Any]):
    """
    Zeigt Visual Inspection Popup.

    Args:
        item_data: Dict mit Artikeldaten:
            {
                'article_number': str,
                'batch_number': str,
                'delivery_number': str,
                'quantity': int,
                'status': str,
                'supplier_name': str (optional)
            }

    Beispiel:
        ```python
        if st.button("Sichtkontrolle"):
            show_visual_inspection_popup({
                'article_number': 'MG0001',
                'batch_number': 'BATCH-123',
                'delivery_number': 'LS-001',
                'quantity': 100,
                'status': 'Pending'
            })
        ```
    """
    popup = VisualInspectionPopup(item_data)
    popup._apply_css()  # CSS anwenden für kompakte Abstände
    popup.render()
