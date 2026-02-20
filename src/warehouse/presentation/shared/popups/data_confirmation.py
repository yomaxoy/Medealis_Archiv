"""
Data Confirmation Popup - Shared across User & Admin View.

Popup for confirming delivery slip data.
Permission-ready: required_permission="confirm_data"

Author: Medealis
Version: 2.0.0 - Shared Implementation
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
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

logger = logging.getLogger(__name__)


def _get_supplier_id(supplier_name: str) -> str:
    """
    Maps supplier_name to supplier_id for validation.

    Args:
        supplier_name: Name des Lieferanten (z.B. "Primec", "Terrats Medical")

    Returns:
        Supplier ID ("PRIMEC", "TERRATS", or "UNKNOWN")
    """
    if not supplier_name:
        return "UNKNOWN"

    supplier_upper = supplier_name.upper().strip()

    if "PRIMEC" in supplier_upper:
        return "PRIMEC"
    elif "TERRATS" in supplier_upper:
        return "TERRATS"
    else:
        return "UNKNOWN"


class DataConfirmationPopup(InspectionPopup):
    """
    Popup für Datenbestätigung (Schritt 1) - Shared für User & Admin.

    WICHTIG: Ordner werden ERST beim Klick auf einen Action-Button erstellt,
    NICHT beim Öffnen des Popups!
    """

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__(
            title="📋 Daten bestätigen",
            item_data=item_data,
            show_info_box=False,
            info_text=None,
            css_style="compact",  # ← Kompaktes CSS
            required_permission="confirm_data"  # ← Permission-Ready
        )

        # WICHTIG: Beim Initialisieren werden KEINE Ordner erstellt!
        logger.info(f"DataConfirmationPopup initialized for article {self.article_number}, batch {self.batch_number} - NO folders created yet")

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
        """Rendert Formular für Datenbestätigung."""
        form = FormBuilder(columns=2)

        # ===== MITARBEITERNAME GANZ OBEN (PFLICHTFELD) =====
        form.add_section("👤 Mitarbeiter", expanded=True, use_expander=False)

        current_user = get_current_username()
        form.add_text_input(
            "Mitarbeitername: *",
            key="data_employee_name",
            value=current_user if current_user != "System" else "",
            placeholder="Ihr Name",
            help="Name des Mitarbeiters der die Datenbestätigung durchführt (Pflichtfeld)",
        )

        # Sektion 1: Artikeldaten bestätigen
        form.add_section("🔍 Artikeldaten", expanded=True, use_expander=False)

        form.add_text_input(
            "Artikelnummer: *",
            key="data_article_number",
            value=self.article_number,
            help="Artikelnummer vom Lieferschein (Pflichtfeld)",
        )

        form.add_text_input(
            "Chargennummer: *",
            key="data_batch_number",
            value=self.batch_number,
            help="Chargennummer vom Lieferschein (Pflichtfeld)",
        )

        # Sektion 2: Mengenerfassung
        form.add_section("📊 Mengenerfassung", expanded=True, use_expander=False)

        # Lade Mengen aus DB falls vorhanden
        ordered_qty = (
            int(self.item_data.get("ordered_quantity", 0))
            if self.item_data.get("ordered_quantity")
            else 0
        )
        slip_qty = (
            int(self.item_data.get("delivery_slip_quantity", 0))
            if self.item_data.get("delivery_slip_quantity")
            else (self.quantity if self.quantity else 0)
        )
        delivered_qty = (
            int(self.item_data.get("delivered_quantity", 0))
            if self.item_data.get("delivered_quantity")
            else 0
        )

        form.add_number_input(
            "Bestellmenge:",
            key="data_ordered_quantity",
            value=ordered_qty,
            min_value=0,
            help="Ursprünglich bestellte Menge (optional)",
        )

        form.add_number_input(
            "Lieferscheinmenge (OCR): *",
            key="data_slip_quantity",
            value=slip_qty,
            min_value=0,
            help="Vom Lieferschein extrahierte Menge (Pflichtfeld)",
        )

        form.add_number_input(
            "Liefermenge (gezählt):",
            key="data_delivered_quantity",
            value=delivered_qty,
            min_value=0,
            help="Tatsächlich gelieferte und gezählte Menge (optional)",
        )

        # Sektion 3: Zusätzliche Daten
        form.add_section(
            "📦 Zusätzliche Informationen", expanded=True, use_expander=False
        )

        # Lade Lagerplatz aus DB falls vorhanden
        try:
            from warehouse.application.services.data_integration_service import (
                data_integration_service,
            )

            existing_storage = (
                data_integration_service.get_storage_location_from_article(
                    self.article_number
                )
            )
        except Exception:
            existing_storage = self.item_data.get("storage_location", "")

        form.add_text_input(
            "Lagerplatz: *",
            key="data_storage_location",
            value=existing_storage or "",
            placeholder="z.B. 123",
            help="Lagernummer für den Artikel (Pflichtfeld, Integer)",
        )

        # Lade Bestellnummer aus DB - prüfe mehrere mögliche Keys wie im Admin-Popup
        extracted_order_number = (
            self.item_data.get("order_number", "")
            or self.item_data.get("bestellnummer", "")
            or self.item_data.get("purchase_order", "")
            or self.item_data.get("po_number", "")
            or self.item_data.get("order_nr", "")
            or self.item_data.get("bestell_nr", "")
            or self.item_data.get("bestellung", "")
            or self.item_data.get("purchase_order_number", "")
            or ""
        )

        form.add_text_input(
            "Bestellnummer: *",
            key="data_order_number",
            value=extracted_order_number,
            placeholder="Bestellnummer eingeben",
            help="Bestellnummer aus dem Lieferschein (Pflichtfeld)",
        )

        form.add_text_area(
            "Bemerkungen:",
            key="data_notes",
            value="",
            height=40,
            placeholder="Optionale Bemerkungen...",
            help="Zusätzliche Anmerkungen",
        )

        # Render und hole Daten
        form_data = form.render()

        # Pflichtfeld-Hinweis
        st.caption("* Pflichtfelder")

        # Sektion 4: Bestelldokumente hochladen
        st.markdown("---")
        st.write("### 📋 Bestelldokument")

        # File uploader for order document
        uploaded_order_doc = st.file_uploader(
            "Bestelldokument auswählen:",
            type=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'],
            key="data_order_doc_upload",
            help="Bestelldokument wird beim Bestätigen in den Artikelordner gespeichert",
            accept_multiple_files=True
        )

        if uploaded_order_doc:
            # Show uploaded document info
            num_files = len(uploaded_order_doc) if isinstance(uploaded_order_doc, list) else 1
            files_list = uploaded_order_doc if isinstance(uploaded_order_doc, list) else [uploaded_order_doc]

            st.success(f"📄 {num_files} Bestelldokument(e) hochgeladen")

            for idx, doc in enumerate(files_list):
                with st.expander(f"📄 {idx + 1}. {doc.name}", expanded=False):
                    st.write(f"📊 Dateigröße: {doc.size} bytes")
                    st.write(f"📋 Dateityp: {doc.type}")

            # Store in session state to preserve across reruns
            st.session_state['uploaded_order_documents'] = files_list

        # Speichere hochgeladene Dokumente in form_data
        form_data["uploaded_documents"] = st.session_state.get('uploaded_order_documents', None)

        return form_data

    def render_footer(self) -> Optional[str]:
        """Rendert Footer mit zwei Action-Buttons."""
        col1, col2, col3 = st.columns([2, 2, 1])

        action = None

        with col1:
            if st.button("✅ Daten bestätigen", type="primary", use_container_width=True):
                action = "save"

        with col2:
            if st.button("❌ Abbrechen", use_container_width=True):
                action = "cancel"

        return action

    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """
        Speichert bestätigte Daten in die Datenbank und erstellt Artikelordner.

        WICHTIG: Artikelordner werden HIER (beim Button-Klick) erstellt!

        Args:
            form_data: Formulardaten vom Body
        """
        import logging
        from datetime import datetime
        from warehouse.application.services.document_generation.document_generation_service import (
            DocumentGenerationService,
        )

        logger = logging.getLogger(__name__)

        logger.info("🔵 handle_primary_action called - Artikelordner werden JETZT erstellt!")

        try:
            # Extract data
            employee_name = form_data.get("data_employee_name", "").strip()
            confirmed_article = form_data.get("data_article_number", "").strip()
            confirmed_batch = form_data.get("data_batch_number", "").strip()
            confirmed_storage_location = form_data.get(
                "data_storage_location", ""
            ).strip()
            ordered_quantity = form_data.get("data_ordered_quantity", 0)
            delivery_slip_quantity = form_data.get(
                "data_slip_quantity", 0
            )  # FIXED: Correct key!
            delivered_quantity = form_data.get("data_delivered_quantity", 0)
            order_number = form_data.get("data_order_number", "").strip()
            delivery_number = self.item_data.get("delivery_number", "")

            # ===== VALIDATION FIRST =====
            supplier_id = _get_supplier_id(self.supplier_name)

            validation_data = {
                "employee_name": employee_name,
                "article_number": confirmed_article,
                "batch_number": confirmed_batch,
                "order_number": order_number,
                "delivery_number": delivery_number,
                "delivery_slip_quantity": delivery_slip_quantity,
                "storage_location": confirmed_storage_location,
                "ordered_quantity": ordered_quantity,
            }

            validation_result = validation_service.validate_data_confirmation(
                validation_data, supplier_id
            )

            if not validation_result.is_valid:
                st.error("❌ **Validierungsfehler:**")
                st.error(validation_result.get_formatted_errors())
                return  # Stop execution

            # Get services
            item_service = st.session_state.services["item"]

            # 1. Save storage location information
            try:
                st.write("💾 Speichere Lagerplatz-Information...")
                item_service.save_item_info(
                    article_number=confirmed_article,
                    designation="",
                    revision_number=None,
                    drawing_reference="",
                    storage_location=confirmed_storage_location,
                    manufacturer="",
                    material_specification="",
                    description="",
                )
                st.success(f"✅ Lagerplatz für {confirmed_article} gespeichert")
            except Exception as e:
                st.error(f"❌ Fehler beim Speichern der Lagerplatz-Information: {e}")

            # 2. Update item with all data
            original_article = self.item_data.get("article_number", "")
            original_batch = self.item_data.get("batch_number", "")

            # Handle article/batch number changes
            if original_article and original_article != confirmed_article:
                item_service.update_item(
                    article_number=original_article,
                    batch_number=original_batch if original_batch else confirmed_batch,
                    delivery_number=delivery_number,
                    new_article_number=confirmed_article,
                    new_batch_number=confirmed_batch
                    if original_batch and original_batch != confirmed_batch
                    else None,
                    new_quantity=delivered_quantity if delivered_quantity > 0 else None,
                    employee_name=employee_name,
                    order_number=order_number,
                    delivery_slip_quantity=delivery_slip_quantity,
                    ordered_quantity=ordered_quantity,
                )
                st.success(
                    f"✅ Artikelnummer erfolgreich geändert: '{original_article}' → '{confirmed_article}'"
                )

            elif original_batch and original_batch != confirmed_batch:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=original_batch,
                    delivery_number=delivery_number,
                    new_batch_number=confirmed_batch,
                    new_quantity=delivered_quantity if delivered_quantity > 0 else None,
                    employee_name=employee_name,
                    order_number=order_number,
                    delivery_slip_quantity=delivery_slip_quantity,
                    ordered_quantity=ordered_quantity,
                )
                st.success(
                    f"✅ Chargennummer erfolgreich geändert: '{original_batch}' → '{confirmed_batch}'"
                )

            elif delivered_quantity > 0:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=delivery_number,
                    new_quantity=delivered_quantity,
                    employee_name=employee_name,
                    order_number=order_number,
                    delivery_slip_quantity=delivery_slip_quantity,
                    ordered_quantity=ordered_quantity,
                )
                st.success(f"✅ Liefermenge auf {delivered_quantity} aktualisiert!")

            elif order_number:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=delivery_number,
                    employee_name=employee_name,
                    order_number=order_number,
                )
                st.success("📋 Bestellnummer erfolgreich gespeichert!")

            # 3. Bestelldokumente speichern (falls vorhanden)
            # WICHTIG: Ordner werden HIER (beim Button-Klick) erstellt!
            uploaded_docs = form_data.get("uploaded_documents")
            logger.info(f"DEBUG: uploaded_docs = {uploaded_docs}, type = {type(uploaded_docs)}")

            if uploaded_docs and len(uploaded_docs) > 0:
                st.write(f"📤 Speichere {len(uploaded_docs)} Bestelldokument(e)...")
                logger.info(f"🟢 Speichere {len(uploaded_docs)} Bestelldokumente - Ordner wird JETZT erstellt!")
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
                            safe_order_number = (
                                order_number
                                if order_number and order_number.strip()
                                else "UNBEKANNT"
                            )
                            order_doc_filename = (
                                f"Bestellung_{safe_order_number}_{doc.name}"
                            )

                            # Save document to article folder (creates folder if needed)
                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=order_doc_filename,
                                document_type="order",
                                batch_number=confirmed_batch,
                                delivery_number=delivery_number,
                                article_number=confirmed_article,
                                supplier_name="",  # Will be auto-determined
                                create_folders=True  # Explicitly create folders NOW
                            )

                            if save_result.success:
                                st.success(f"✅ Bestelldokument gespeichert: {doc.name}")
                                logger.info(
                                    f"✅ Order document saved: {doc.name} to {save_result.file_path or save_result.storage_folder}"
                                )
                            else:
                                st.error(
                                    f"❌ Fehler beim Speichern von {doc.name}: {save_result.error}"
                                )
                                logger.error(
                                    f"❌ Failed to save order document {doc.name}: {save_result.error}"
                                )

                        except Exception as doc_error:
                            st.error(
                                f"❌ Fehler beim Verarbeiten von {doc.name}: {doc_error}"
                            )
                            logger.error(
                                f"Error processing order document {doc.name}: {doc_error}"
                            )

                except Exception as storage_error:
                    st.error(
                        f"❌ Fehler beim Speichern der Bestelldokumente: {storage_error}"
                    )
                    logger.error(f"Error saving order documents: {storage_error}")

            # 4. Set workflow status
            item_service.complete_data_check(
                article_number=confirmed_article,
                batch_number=confirmed_batch,
                delivery_number=delivery_number,
                employee=employee_name,
            )
            st.success("✅ Datenprüfung abgeschlossen")

            # ===== AUDIT LOGGING =====
            audit_service.log_data_confirmed(
                user=employee_name,
                article_number=confirmed_article,
                batch_number=confirmed_batch,
                delivery_number=delivery_number,
                quantity=delivered_quantity
                if delivered_quantity > 0
                else delivery_slip_quantity,
                notes=f"Lagerplatz: {confirmed_storage_location}, Bestellnummer: {order_number}",
            )

            # 5. Generate documents
            st.info("📄 **Automatische Dokument-Erstellung läuft...**")
            try:
                generation_service = DocumentGenerationService()
                documents_created = []
                generation_errors = []

                # Generate Begleitschein
                try:
                    begleitschein_result = generation_service.generate_document(
                        document_type="begleitschein",
                        batch_number=confirmed_batch,
                        delivery_number=delivery_number,
                        article_number=confirmed_article,
                        supplier_name="",
                        quantity=delivered_quantity,
                        employee_name=employee_name,
                        additional_data={
                            "status": "Daten bestätigt",
                            "order_number": order_number,
                        },
                    )
                    if begleitschein_result.success:
                        documents_created.append("Begleitschein")
                        st.write(
                            f"  ✅ Begleitschein: {begleitschein_result.document_path}"
                        )
                    else:
                        generation_errors.append(
                            f"Begleitschein: {begleitschein_result.error}"
                        )
                except Exception as e:
                    generation_errors.append(f"Begleitschein Fehler: {e}")

                # Generate Wareneingangskontrolle
                try:
                    wareneingang_result = generation_service.generate_document(
                        document_type="wareneingangskontrolle",
                        batch_number=confirmed_batch,
                        delivery_number=delivery_number,
                        article_number=confirmed_article,
                        supplier_name="",
                        quantity=delivered_quantity,
                        employee_name=employee_name,
                        additional_data={
                            "we_date": datetime.now().strftime("%d.%m.%Y"),
                            "artikel": confirmed_article,
                            "charge": confirmed_batch,
                        },
                    )
                    if wareneingang_result.success:
                        documents_created.append("Wareneingangskontrolle")
                        st.write(
                            f"  ✅ Wareneingangskontrolle: {wareneingang_result.document_path}"
                        )
                    else:
                        generation_errors.append(
                            f"Wareneingangskontrolle: {wareneingang_result.error}"
                        )
                except Exception as e:
                    generation_errors.append(f"Wareneingangskontrolle Fehler: {e}")

                # Generate Barcode/Label
                try:
                    barcode_result = generation_service.generate_document(
                        document_type="barcode",
                        batch_number=confirmed_batch,
                        delivery_number=delivery_number,
                        article_number=confirmed_article,
                        supplier_name="",
                        quantity=delivered_quantity,
                        employee_name=employee_name,
                        additional_data={
                            "barcode_type": "CODE128",
                            "filename_prefix": "label",
                            "open_after_creation": False,
                            "storage_location": confirmed_storage_location,
                        },
                    )
                    if barcode_result.success:
                        documents_created.append("Barcode/Label")
                        st.write(f"  ✅ Barcode/Label: {barcode_result.document_path}")
                    else:
                        generation_errors.append(
                            f"Barcode/Label: {barcode_result.error}"
                        )
                except Exception as e:
                    generation_errors.append(f"Barcode/Label Fehler: {e}")

                # Show summary
                if documents_created:
                    st.success(
                        f"📄 {len(documents_created)} Dokument(e) erstellt: {', '.join(documents_created)}"
                    )
                if generation_errors:
                    for error in generation_errors:
                        st.warning(f"⚠️ {error}")

            except Exception as e:
                st.warning(f"⚠️ Dokument-Generierung teilweise fehlgeschlagen: {e}")

            st.success("🎉 **Datenbestätigung abgeschlossen!**")

            # Cleanup session state
            if 'uploaded_order_documents' in st.session_state:
                del st.session_state['uploaded_order_documents']

            st.rerun()

        except Exception as e:
            logger.error(f"Error in data confirmation: {e}", exc_info=True)
            st.error(f"❌ Fehler beim Speichern: {str(e)}")

    def handle_ai_analysis_action(self, form_data: Dict[str, Any]) -> None:
        """
        Führt KI-Analyse durch und speichert dann die Daten.

        Args:
            form_data: Formulardaten vom Body
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Extract data
            employee_name = form_data.get("data_employee_name", "").strip()
            confirmed_article = form_data.get("data_article_number", "").strip()
            confirmed_batch = form_data.get("data_batch_number", "").strip()
            delivery_number = self.item_data.get("delivery_number", "")

            st.info("🤖 **KI-Analyse wird durchgeführt...**")

            # TODO: Implementiere KI-Analyse hier
            # Beispiel: Analysiere hochgeladene Dokumente
            uploaded_docs = form_data.get("uploaded_documents", [])

            if uploaded_docs:
                st.write(f"📄 {len(uploaded_docs)} Dokument(e) werden analysiert...")
                # KI-Analyse-Logik hier einfügen
                st.info("⚠️ KI-Analyse noch nicht implementiert - führe normale Speicherung durch")
            else:
                st.warning("⚠️ Keine Dokumente zum Analysieren hochgeladen")

            # Nach KI-Analyse: Normale Speicherung durchführen
            st.info("💾 Speichere Daten nach KI-Analyse...")
            self.handle_primary_action(form_data)

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}", exc_info=True)
            st.error(f"❌ Fehler bei KI-Analyse: {str(e)}")

    def handle_secondary_action(self, form_data: Dict[str, Any]) -> None:
        """Zurückweisen - markiert Artikel als Ausschuss."""
        # Nicht verwendet für Data Confirmation
        pass


@st.dialog("📋 Daten bestätigen", width="large")
def show_data_confirmation_popup(item_data: Dict[str, Any]) -> None:
    """
    Zeigt Data Confirmation Popup.

    WICHTIG: Artikelordner werden ERST beim Klick auf einen Action-Button erstellt!

    Args:
        item_data: Dictionary mit Item-Informationen
    """
    # WICHTIG: Flag setzen, dass Popup nur am Rendern ist - KEINE Ordner erstellen!
    if "data_confirmation_action_clicked" not in st.session_state:
        st.session_state["data_confirmation_action_clicked"] = False

    logger.info("🟡 show_data_confirmation_popup called - Rendering nur, KEINE Ordner-Erstellung")

    popup = DataConfirmationPopup(item_data)

    # Render Popup
    popup.render_header()
    form_data = popup.render_body()
    action = popup.render_footer()

    # Handle Actions - NUR hier werden Ordner erstellt!
    if action == "save":
        st.session_state["data_confirmation_action_clicked"] = True
        logger.info("🟢 'Daten bestätigen' Button geklickt - Ordner werden JETZT erstellt!")
        popup.handle_primary_action(form_data)
    elif action == "ai_save":
        st.session_state["data_confirmation_action_clicked"] = True
        logger.info("🟢 'KI-Analyse' Button geklickt - Ordner werden JETZT erstellt!")
        popup.handle_ai_analysis_action(form_data)
    elif action == "cancel":
        st.session_state["data_confirmation_action_clicked"] = False
        # Cleanup uploaded documents from session state
        if 'uploaded_order_documents' in st.session_state:
            del st.session_state['uploaded_order_documents']
        logger.info("⚪ 'Abbrechen' Button geklickt - keine Ordner erstellt")
        st.rerun()
