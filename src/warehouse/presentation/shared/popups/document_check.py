"""
Document Check Popup - Shared across User & Admin View.

Popup for checking certificates and documents.
Permission-ready: required_permission="check_documents"

PERFORMANCE: Nutzt gecachten DocumentGenerationService

Author: Medealis
Version: 2.0.0 - Shared Implementation
"""

import streamlit as st
from typing import Dict, Any, Optional
from warehouse.presentation.shared.inspection_popup import InspectionPopup
from warehouse.presentation.shared.components import (  # noqa: F401
    render_article_header,
    FormBuilder,
    render_standard_footer,
    render_document_uploader,
)
from warehouse.presentation.shared.popup_styles import apply_document_check_highlights
from warehouse.domain.enums.certificate_type import CertificateType
from warehouse.application.services.validation_service import validation_service
from warehouse.application.services.audit_service import audit_service

# Session State Keys die vom DocumentCheck-Dialog verwendet werden.
_DOC_CHECK_FORM_KEYS = [
    "doc_inspector_name",
    "doc_accompanying_documents",
    "doc_materialzeugnis",
    "doc_messprotokolle",
    "doc_beschichtung",
    "doc_haerte",
    "doc_weitere",
    "doc_label_attached",
    "doc_slip_attached",
    "doc_notes",
]


def _cleanup_doc_check_session_state() -> None:
    """Entfernt alle Form-Widget-Keys aus dem Session State."""
    for key in _DOC_CHECK_FORM_KEYS:
        st.session_state.pop(key, None)
    st.session_state.pop("_dcc_item_key", None)


# PERFORMANCE: Cache DocumentGenerationService als Singleton
@st.cache_resource
def get_document_generation_service():
    """
    Get cached DocumentGenerationService singleton.

    Uses @st.cache_resource to create service ONCE and reuse it.
    This allows TemplateCache to persist across document generations.
    """
    from warehouse.application.services.document_generation import (
        DocumentGenerationService,
    )

    return DocumentGenerationService()


class DocumentCheckPopup(InspectionPopup):
    """Popup für Dokumentenprüfung (Schritt 2) - Shared für User & Admin."""

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__(
            title="📄 Dokumente prüfen",
            item_data=item_data,
            show_info_box=False,
            info_text=None,
            css_style="compact",  # ← Kompaktes CSS
            required_permission="check_documents",  # ← Permission-Ready
        )

    def render_header(self) -> None:
        """Rendert kompakten Artikel-Header."""
        # CSS wird automatisch von Base Class angewendet!
        # Zusätzlich: Spezielle Highlights für wichtige Checkboxen
        apply_document_check_highlights()

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
        """Rendert Formular für Dokumentenprüfung."""
        # Prüfer-Eingabe DIREKT ohne FormBuilder
        employee_name = st.text_input(
            "👤 Name des durchführenden Mitarbeiters:",
            key="doc_inspector_name",
            value=self.get_current_user(),
            placeholder="Vollständiger Name für PDB-Dokument",
            help="Wird für die Nachvollziehbarkeit benötigt",
        )

        form_data = {"doc_inspector_name": employee_name}

        st.markdown("---")

        uploaded_docs = render_document_uploader(
            label="Begleitdokumente hochladen",
            key="doc_accompanying_documents",
            file_types=["pdf", "png", "jpg", "jpeg", "docx"],
            accept_multiple=True,
            help_text="Laden Sie Begleitdokumente hoch (z.B. Materialzeugnis, Messprotokoll)",  # noqa: E501
        )

        # Speichere hochgeladene Dokumente
        form_data["uploaded_documents"] = uploaded_docs

        st.markdown("---")

        # Sektion 3: Welche Begleitdokumente liegen vor?
        st.markdown("**📄 Welche Begleitdokumente liegen der Lieferung bei?**")

        # Lade existierende Zertifikate aus DB
        certificates = self.item_data.get("certificates", {})

        col1, col2 = st.columns(2)

        with col1:
            materialzeugnis = st.checkbox(
                "📋 Materialzeugnis",
                key="doc_materialzeugnis",
                value=certificates.get("material_certificate", False),
                help="Materialprüfzeugnis liegt vor",
            )
            messprotokolle = st.checkbox(
                "📊 Messprotokolle",
                key="doc_messprotokolle",
                value=certificates.get("measurement_protocol", False),
                help="Messprotokoll liegt vor",
            )
            beschichtungszeugnis = st.checkbox(
                "🎨 Beschichtungszeugnis",
                key="doc_beschichtung",
                value=certificates.get("coating_certificate", False),
                help="Beschichtungszeugnis liegt vor",
            )

        with col2:
            haertezeugnis = st.checkbox(
                "🔨 Härtezeugnis",
                key="doc_haerte",
                value=certificates.get("hardness_certificate", False),
                help="Härteprüfzeugnis liegt vor",
            )
            weitere_zeugnisse = st.text_input(
                "📝 Weitere Zeugnisse:",
                key="doc_weitere",
                placeholder="z.B. Kalibrierungszeugnis...",
                help="Sonstige Zeugnisse",
            )

        # Speichere Zertifikat-Checkboxen
        st.session_state._temp_materialzeugnis = materialzeugnis
        st.session_state._temp_messprotokolle = messprotokolle
        st.session_state._temp_beschichtungszeugnis = beschichtungszeugnis
        st.session_state._temp_haertezeugnis = haertezeugnis
        st.session_state._temp_weitere_zeugnisse = weitere_zeugnisse

        st.markdown("---")

        # Sektion 4: Physische Dokumente - HERVORGEHOBEN
        st.markdown("**📋 Physische Dokumente und Label Verifikation**")
        st.caption(
            "*Bestätigen Sie, dass die erstellten Dokumente korrekt angebracht bzw. beigelegt wurden:*"  # noqa: E501
        )

        col3, col4 = st.columns(2)

        with col3:
            label_attached = st.checkbox(
                "🏷️ Label geprüft und angebracht *",
                key="doc_label_attached",
                value=certificates.get("label_present", False),
                help="Das gedruckte Label wurde überprüft und am Artikel angebracht (PFLICHTFELD)",  # noqa: E501
            )

        with col4:
            slip_attached = st.checkbox(
                "📋 Begleitschein beigelegt *",
                key="doc_slip_attached",
                value=certificates.get("accompanying_document", False),
                help="Der gedruckte Begleitschein wurde überprüft und der Lieferung beigelegt (PFLICHTFELD)",  # noqa: E501
            )

        # Speichere physische Dokument-Checkboxen
        st.session_state._temp_label_attached = label_attached
        st.session_state._temp_slip_attached = slip_attached

        st.markdown("---")

        # Sektion 5: Bemerkungen
        st.markdown("**📝 Bemerkungen**")

        notes = st.text_area(
            "Anmerkungen zur Dokumentenprüfung:",
            key="doc_notes",
            value="",
            height=40,
            placeholder="Optionale Bemerkungen...",
            help="Zusätzliche Anmerkungen",
            label_visibility="collapsed",
        )

        # Füge alle Werte zu form_data hinzu
        form_data["materialzeugnis"] = st.session_state.get(
            "_temp_materialzeugnis", False
        )
        form_data["messprotokolle"] = st.session_state.get(
            "_temp_messprotokolle", False
        )
        form_data["beschichtungszeugnis"] = st.session_state.get(
            "_temp_beschichtungszeugnis", False
        )
        form_data["haertezeugnis"] = st.session_state.get("_temp_haertezeugnis", False)
        form_data["weitere_zeugnisse"] = st.session_state.get(
            "_temp_weitere_zeugnisse", ""
        )
        form_data["label_attached"] = st.session_state.get(
            "_temp_label_attached", False
        )
        form_data["slip_attached"] = st.session_state.get("_temp_slip_attached", False)
        form_data["notes"] = notes

        # Pflichtfeld-Hinweis
        st.caption("* Pflichtfelder")

        # Validierungshinweise
        if not label_attached or not slip_attached:
            st.warning(
                "⚠️ Bitte bestätigen Sie, dass Label und Begleitschein angebracht/beigelegt wurden (Pflicht)."  # noqa: E501
            )

        return form_data

    def render_footer(self) -> Optional[str]:
        """Rendert Standard-Footer."""
        return render_standard_footer(
            save_label="✅ Dokumente bestätigen", cancel_label="❌ Abbrechen"
        )

    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """
        Speichert Dokumentenprüfung in die Datenbank.

        Args:
            form_data: Formulardaten vom Body
        """
        import logging
        from datetime import datetime
        from warehouse.application.services.document_generation.document_generation_service import (  # noqa: E501, F401
            DocumentGenerationService,
        )

        logger = logging.getLogger(__name__)

        try:
            # Extract data (employee_name from form_data, NOT session_state!)
            employee_name = form_data.get("doc_inspector_name", "").strip()
            article_number = self.item_data.get("article_number", "")
            batch_number = self.item_data.get("batch_number", "")
            delivery_number = self.item_data.get("delivery_number", "")

            logger.info(
                f"🔥 USER POPUP: Employee name from form_data: '{employee_name}'"
            )

            # ===== VALIDATION FIRST =====
            label_present = st.session_state.get("doc_label_attached", False)
            qr_code_present = st.session_state.get(
                "doc_slip_attached", False
            )  # Using slip as proxy for QR presence

            validation_data = {
                "employee_name": employee_name,
                "label_present": label_present,
                "qr_code_present": qr_code_present,
            }

            validation_result = validation_service.validate_document_check(
                validation_data
            )

            if not validation_result.is_valid:
                st.error("❌ **Validierungsfehler:**")
                st.error(validation_result.get_formatted_errors())
                return  # Stop execution

            # Collect certificate information from session_state (CORRECT KEYS!)
            documents_found = {
                "materialzeugnis": st.session_state.get("doc_materialzeugnis", False),
                "messprotokolle": st.session_state.get("doc_messprotokolle", False),
                "beschichtungszeugnis": st.session_state.get("doc_beschichtung", False),
                "haertezeugnis": st.session_state.get("doc_haerte", False),
                "weitere_zeugnisse": st.session_state.get("doc_weitere", "").strip(),
            }

            label_attached = st.session_state.get("doc_label_attached", False)
            accompanying_document_attached = st.session_state.get(
                "doc_slip_attached", False
            )

            # Log for debugging (ADMIN STYLE)
            logger.info(f"🔍 STEP 2 DEBUG: Documents found: {documents_found}")
            logger.info(
                f"🔍 STEP 2 DEBUG: Physical documents: Label={label_attached}, Begleitschein={accompanying_document_attached}"  # noqa: E501
            )

            # 1. Save certificate and document flags (ADMIN STYLE)
            try:
                item_service = st.session_state.services["item"]
                st.write("🔥 Saving certificates and document flags...")

                # Log the exact parameters being sent (ADMIN STYLE)
                save_params = {
                    "article_number": article_number,
                    "batch_number": batch_number,
                    "delivery_number": delivery_number,
                    "employee_name": employee_name,  # Already validated - no fallback to 'System'  # noqa: E501
                    "measurement_protocol": documents_found.get(
                        "messprotokolle", False
                    ),
                    "material_certificate": documents_found.get(
                        "materialzeugnis", False
                    ),
                    "coating_certificate": documents_found.get(
                        "beschichtungszeugnis", False
                    ),
                    "hardness_certificate": documents_found.get("haertezeugnis", False),
                    "additional_certificates": bool(
                        documents_found.get("weitere_zeugnisse", "").strip()
                    ),
                    "label_present": label_attached,
                    "accompanying_document": accompanying_document_attached,
                }
                logger.info(f"🔥 STEP 2 SAVE: Parameters being sent: {save_params}")

                item_service.update_item(**save_params)
                logger.info(
                    "🔥 STEP 2 SAVE: SUCCESS - Certificates and document flags saved!"
                )
                st.success("🔥 Certificates and document flags saved!")

            except Exception as e:
                logger.error(f"🔥 STEP 2 SAVE ERROR: {e}")
                import traceback

                logger.error(f"🔥 STEP 2 SAVE Traceback: {traceback.format_exc()}")
                st.error(f"❌ Error saving certificates and document flags: {e}")
                return

            # 1.5 Save uploaded documents
            uploaded_docs = form_data.get("uploaded_documents", [])
            logger.info(
                f"🔍 DEBUG: uploaded_docs = {uploaded_docs}, type = {type(uploaded_docs)}"  # noqa: E501
            )
            if uploaded_docs:
                st.write(
                    f"📤 Speichere {len(uploaded_docs)} hochgeladene Dokument(e)..."
                )
                try:
                    from warehouse.application.services.service_registry import (
                        get_document_storage_service,
                    )

                    storage_service = get_document_storage_service()

                    for doc in uploaded_docs:
                        try:
                            # Read document data
                            document_data = doc.read()

                            # Create filename with prefix
                            begleitpapiere_filename = (
                                f"Begleitpapiere_{article_number}_{doc.name}"
                            )

                            # Save document to article folder
                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=begleitpapiere_filename,
                                document_type="begleitdokument",
                                batch_number=batch_number,
                                delivery_number=delivery_number,
                                article_number=article_number,
                                supplier_name=self.item_data.get("supplier_name", ""),
                            )

                            if save_result.success:
                                st.success(f"✅ Dokument gespeichert: {doc.name}")
                                logger.info(
                                    f"✅ Document saved: {doc.name} to {save_result.file_path or save_result.storage_folder}"  # noqa: E501
                                )
                            else:
                                st.error(
                                    f"❌ Fehler beim Speichern von {doc.name}: {save_result.error}"  # noqa: E501
                                )
                                logger.error(
                                    f"❌ Failed to save {doc.name}: {save_result.error}"
                                )

                        except Exception as doc_error:
                            st.error(
                                f"❌ Fehler beim Verarbeiten von {doc.name}: {doc_error}"
                            )
                            logger.error(
                                f"Error processing document {doc.name}: {doc_error}"
                            )

                except Exception as storage_error:
                    st.error(f"❌ Fehler beim Speichern der Dokumente: {storage_error}")
                    logger.error(f"Error saving documents: {storage_error}")

            # 2. Generate PDB with certificate information (ADMIN STYLE)
            try:
                st.write(
                    "✨ **Neue Generation Service**: Erstelle PDB mit Zertifikatsinformationen..."  # noqa: E501
                )
                # PERFORMANCE: Use cached service instead of creating new one
                generation_service = get_document_generation_service()

                # Prepare certificate data for PDB generation (ADMIN STYLE)
                certificate_data = {
                    # Certificate flags
                    "materialzeugnis": "X"
                    if documents_found.get("materialzeugnis")
                    else "",
                    "messprotokolle": "X"
                    if documents_found.get("messprotokolle")
                    else "",
                    "beschichtungszeugnis": "X"
                    if documents_found.get("beschichtungszeugnis")
                    else "",
                    "haertezeugnis": "X"
                    if documents_found.get("haertezeugnis")
                    else "",
                    "weitere_zeugnisse": documents_found.get("weitere_zeugnisse", ""),
                    # Physical document flags
                    "label_attached": "X" if label_attached else "",
                    "accompanying_document": "X"
                    if accompanying_document_attached
                    else "",
                    # Status and timestamps
                    "status": "Dokumente geprüft",
                    "inspection_date": datetime.now().strftime("%d.%m.%Y"),
                    "inspection_time": datetime.now().strftime("%H:%M"),
                    # Document counts for summary
                    "certificate_count": sum(
                        1
                        for flag in [
                            documents_found.get("materialzeugnis"),
                            documents_found.get("messprotokolle"),
                            documents_found.get("beschichtungszeugnis"),
                            documents_found.get("haertezeugnis"),
                        ]
                        if flag
                    ),
                }

                # CRITICAL FIX: Reload fresh item data from DB before PDB generation (ADMIN STYLE)  # noqa: E501
                # Problem: item_data parameter may contain stale data from before Step1 updates  # noqa: E501
                # Solution: Always get fresh data from database
                fresh_item_data = item_service.get_item_by_composite_key(
                    article_number, batch_number, delivery_number
                )

                # Use fresh data if available, otherwise fall back to passed data (ADMIN STYLE)  # noqa: E501
                item_data_for_pdb = (
                    fresh_item_data if fresh_item_data else self.item_data
                )

                # Generate PDB document with certificate data (DOCX + PDF + SharePoint Upload) (ADMIN STYLE)  # noqa: E501
                # Neue robuste Implementierung mit DocumentOperationResult
                from pathlib import Path
                from warehouse.application.services.document_storage.document_storage_service import (
                    DocumentOperationResult,
                    StorageResult,
                )

                operation_result = DocumentOperationResult(
                    operation_type="Dokumentenprüfung (PDB)"
                )

                pdb_result = generation_service.generate_document(
                    document_type="pdb",
                    batch_number=batch_number,
                    delivery_number=item_data_for_pdb.get("delivery_number", ""),
                    article_number=article_number,
                    supplier_name=item_data_for_pdb.get("supplier_name", ""),
                    quantity=item_data_for_pdb.get("quantity", 0),
                    employee_name=employee_name,  # Already validated - no fallback
                    additional_data=certificate_data,
                )

                if pdb_result.success:
                    # DOCX
                    storage_result = StorageResult(
                        success=True,
                        file_path=str(pdb_result.document_path) if pdb_result.document_path else None,
                        filename=Path(pdb_result.document_path).name if pdb_result.document_path else None,
                        storage_folder=str(Path(pdb_result.document_path).parent) if pdb_result.document_path else None,
                        document_type="PDB (DOCX)",
                    )
                    operation_result.add_document(storage_result)

                    # PDF (falls vorhanden)
                    if hasattr(pdb_result, "pdf_path") and pdb_result.pdf_path:
                        pdf_storage = StorageResult(
                            success=True,
                            file_path=str(pdb_result.pdf_path),
                            filename=Path(pdb_result.pdf_path).name,
                            storage_folder=str(Path(pdb_result.pdf_path).parent),
                            document_type="PDB (PDF)",
                        )
                        operation_result.add_document(pdf_storage)
                else:
                    operation_result.add_error(f"PDB-Erstellung fehlgeschlagen: {pdb_result.error}")

            except Exception as e:
                logger.error(f"Error generating PDB: {e}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                st.error(f"❌ PDB-Generierung fehlgeschlagen: {e}")

            # 3. Complete workflow - WITH certificates parameter mapped to CertificateType enums  # noqa: E501
            try:
                # Build certificates dictionary with CertificateType enum keys
                certificates_dict = {
                    CertificateType.MATERIALZEUGNIS.value: documents_found.get(
                        "materialzeugnis", False
                    ),
                    CertificateType.MESSPROTOKOLL.value: documents_found.get(
                        "messprotokolle", False
                    ),
                    CertificateType.BESCHICHTUNGSZEUGNIS.value: documents_found.get(
                        "beschichtungszeugnis", False
                    ),
                    CertificateType.HAERTEZEUGNIS.value: documents_found.get(
                        "haertezeugnis", False
                    ),
                    CertificateType.WEITERE_ZEUGNISSE.value: bool(
                        documents_found.get("weitere_zeugnisse", "").strip()
                    ),
                    CertificateType.ETIKETT.value: label_attached,
                    CertificateType.BEGLEITSCHEIN.value: accompanying_document_attached,
                }

                logger.info(
                    f"🔥 WORKFLOW COMPLETE: Certificates dict: {certificates_dict}"
                )

                item_service.complete_document_check(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    employee=employee_name,  # Already validated - no fallback
                    certificates=certificates_dict,
                )
                st.success("✅ Dokumentenprüfung abgeschlossen")

                # ===== AUDIT LOGGING =====
                # Build certificates dict for audit log
                certificates_for_audit = {
                    "materialzeugnis": documents_found.get("materialzeugnis", False),
                    "messprotokolle": documents_found.get("messprotokolle", False),
                    "beschichtungszeugnis": documents_found.get(
                        "beschichtungszeugnis", False
                    ),
                    "haertezeugnis": documents_found.get("haertezeugnis", False),
                    "weitere_zeugnisse": bool(
                        documents_found.get("weitere_zeugnisse", "").strip()
                    ),
                    "label": label_attached,
                    "begleitschein": accompanying_document_attached,
                }

                audit_service.log_documents_checked(
                    user=employee_name,
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    certificates=certificates_for_audit,
                    notes=None,  # Die Methode baut die Notes selbst aus den Zertifikaten  # noqa: E501
                )

            except Exception as e:
                logger.error(f"Error completing document check: {e}")
                import traceback

                logger.error(f"🔥 WORKFLOW ERROR Traceback: {traceback.format_exc()}")
                st.error(f"❌ Fehler beim Abschließen der Dokumentenprüfung: {e}")
                return

            # Speichere Result in Session State für Deferred Dialog
            if operation_result.has_documents() or operation_result.errors:
                st.session_state["pending_doc_confirmation"] = operation_result

            st.success("🎉 **Dokumentenprüfung erfolgreich bestätigt!**")
            st.rerun()

        except Exception as e:
            logger.error(f"Error in document check: {e}", exc_info=True)
            st.error(f"❌ Fehler beim Speichern: {str(e)}")

    def handle_secondary_action(self, form_data: Dict[str, Any]) -> None:
        """Nicht verwendet für Document Check."""
        pass


@st.dialog("📄 Dokumente prüfen", width="large")
def show_document_check_popup(item_data: Dict[str, Any]) -> None:
    """
    Zeigt Document Check Popup.

    Args:
        item_data: Dictionary mit Item-Informationen
    """
    # Stale Form-Keys vom vorherigen Dialog bereinigen, aber NUR wenn sich
    # der Artikel geaendert hat (sonst wuerden User-Eingaben zurueckgesetzt)
    _current_item_key = (
        f"{item_data.get('article_number')}"
        f"_{item_data.get('batch_number')}"
        f"_{item_data.get('delivery_number')}"
    )
    if st.session_state.get("_dcc_item_key") != _current_item_key:
        _cleanup_doc_check_session_state()
        st.session_state["_dcc_item_key"] = _current_item_key

    popup = DocumentCheckPopup(item_data)
    popup._apply_css()  # CSS anwenden für kompakte Abstände

    # Render Popup
    popup.render_header()
    form_data = popup.render_body()
    action = popup.render_footer()

    # Handle Actions
    if action == "save":
        popup.handle_primary_action(form_data)
    elif action == "cancel":
        _cleanup_doc_check_session_state()
        st.rerun()
