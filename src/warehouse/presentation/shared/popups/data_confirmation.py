"""
Data Confirmation Popup - Shared across User & Admin View.

Popup for confirming delivery slip data.
Permission-ready: required_permission="confirm_data"

Author: Medealis
Version: 2.0.0 - Shared Implementation
"""

import streamlit as st
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from warehouse.presentation.shared.inspection_popup import InspectionPopup
from warehouse.presentation.shared.components import (
    render_article_header,
    FormBuilder,
)
from warehouse.application.services.validation_service import validation_service
from warehouse.application.services.audit_service import audit_service
from warehouse.presentation.utils.user_context import get_current_username

logger = logging.getLogger(__name__)

# Session State Keys die vom DataConfirmation-Dialog verwendet werden.
# Muessen beim Oeffnen/Schliessen bereinigt werden, damit keine stale
# Werte vom vorherigen Dialog in den naechsten uebernommen werden.
_DATA_CONFIRMATION_FORM_KEYS = [
    "data_employee_name",
    "data_article_number",
    "data_batch_number",
    "data_ordered_quantity",
    "data_slip_quantity",
    "data_delivered_quantity",
    "data_storage_location",
    "data_order_number",
    "data_notes",
    "data_order_doc_upload",
    "uploaded_order_documents",
    "data_confirmation_action_clicked",
]


def _cleanup_form_session_state() -> None:
    """Entfernt alle Form-Widget-Keys aus dem Session State."""
    for key in _DATA_CONFIRMATION_FORM_KEYS:
        st.session_state.pop(key, None)
    st.session_state.pop("_dc_item_key", None)


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
            required_permission="confirm_data",  # ← Permission-Ready
        )

        # WICHTIG: Beim Initialisieren werden KEINE Ordner erstellt!
        logger.info(
            "DataConfirmationPopup initialized for"
            " article %s, batch %s"
            " - NO folders created yet",
            self.article_number,
            self.batch_number,
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
        """Rendert Formular für Datenbestätigung."""
        form = FormBuilder(columns=2)

        # ===== MITARBEITERNAME GANZ OBEN (PFLICHTFELD) =====
        form.add_section("👤 Mitarbeiter", expanded=True, use_expander=False)

        current_user = get_current_username()
        form.add_text_input(
            "Mitarbeitername:",
            key="data_employee_name",
            value=current_user if current_user != "System" else "",
            placeholder="Ihr Name",
            help=(
                "Name des Mitarbeiters der die"
                " Datenbestaetigung durchfuehrt"
            ),
        )

        # Sektion 1: Artikeldaten bestätigen
        form.add_section("🔍 Artikeldaten", expanded=True, use_expander=False)

        form.add_text_input(
            "Artikelnummer:",
            key="data_article_number",
            value=self.article_number,
            help="Artikelnummer vom Lieferschein",
        )

        _batch_override_key = f"batch_override_{self.delivery_number}"
        _batch_override = st.session_state.pop(_batch_override_key, None)
        if _batch_override is not None:
            # Widget-State löschen BEVOR Widget gerendert wird,
            # damit der neue value-Parameter übernommen wird
            st.session_state.pop("data_batch_number", None)
            _batch_prefill = _batch_override
        else:
            _batch_prefill = self.batch_number
        form.add_text_input(
            "Chargennummer:",
            key="data_batch_number",
            value=_batch_prefill,
            help="Chargennummer vom Lieferschein",
        )

        # Batch-Abgleich: Eingabe vs. DB-Wert anzeigen
        _current_batch = st.session_state.get("data_batch_number", "")
        if (
            self.batch_number
            and _current_batch
            and str(_current_batch).strip() != str(self.batch_number).strip()
        ):
            st.warning(
                "⚠️ **Chargen-Abweichung erkannt:**"
                "\n\n"
                f"- **Eingabe:** `{_current_batch}`"
                "\n"
                "- **DB-Wert:**"
                f" `{self.batch_number}`\n\n"
                "Beim Bestaetigen wird die"
                " eingegebene Chargennummer"
                " uebernommen."
            )
        elif self.batch_number and _current_batch:
            st.success(
                "✅ Chargennummer stimmt mit DB" f" ueberein: `{self.batch_number}`"
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
            "Lieferscheinmenge (OCR):",
            key="data_slip_quantity",
            value=slip_qty,
            min_value=0,
            help="Vom Lieferschein extrahierte Menge",
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
            "Lagerplatz:",
            key="data_storage_location",
            value=existing_storage or "",
            placeholder="z.B. 123",
            help="Lagernummer für den Artikel (Integer)",
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
            "Bestellnummer:",
            key="data_order_number",
            value=extracted_order_number,
            placeholder="Bestellnummer eingeben",
            help="Bestellnummer aus dem Lieferschein",
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

        # Sektion 4: Bestelldokumente hochladen
        st.markdown("---")
        st.write("### 📋 Bestelldokument")

        # File uploader for order document
        uploaded_order_doc = st.file_uploader(
            "Bestelldokument auswählen:",
            type=[
                "pdf",
                "doc",
                "docx",
                "txt",
                "jpg",
                "jpeg",
                "png",
            ],
            key="data_order_doc_upload",
            help=(
                "Bestelldokument wird beim"
                " Bestaetigen in den"
                " Artikelordner gespeichert"
            ),
            accept_multiple_files=True,
        )

        if uploaded_order_doc:
            # Show uploaded document info
            num_files = (
                len(uploaded_order_doc) if isinstance(uploaded_order_doc, list) else 1
            )
            files_list = (
                uploaded_order_doc
                if isinstance(uploaded_order_doc, list)
                else [uploaded_order_doc]
            )

            st.success(f"📄 {num_files} Bestelldokument(e) hochgeladen")

            for idx, doc in enumerate(files_list):
                with st.expander(f"📄 {idx + 1}. {doc.name}", expanded=False):
                    st.write(f"📊 Dateigröße: {doc.size} bytes")
                    st.write(f"📋 Dateityp: {doc.type}")

            # Store in session state to preserve across reruns
            st.session_state["uploaded_order_documents"] = files_list

        # Speichere hochgeladene Dokumente in form_data
        form_data["uploaded_documents"] = st.session_state.get(
            "uploaded_order_documents", None
        )

        return form_data

    def render_footer(self) -> Optional[str]:
        """Rendert Footer mit zwei Action-Buttons."""
        col1, col2, col3 = st.columns([2, 2, 1])

        action = None

        with col1:
            if st.button(
                "✅ Daten bestätigen", type="primary", use_container_width=True
            ):
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
        from warehouse.application.services.document_generation.document_generation_service import (  # noqa: E501
            DocumentGenerationService,
        )

        logger = logging.getLogger(__name__)

        logger.info("handle_primary_action called - Daten werden gespeichert")

        try:
            # Extract data - mit None-Safety
            employee_name = (form_data.get("data_employee_name") or "").strip()
            confirmed_article = (form_data.get("data_article_number") or "").strip()
            confirmed_batch = (form_data.get("data_batch_number") or "").strip()
            confirmed_storage_location = (
                form_data.get("data_storage_location") or ""
            ).strip()
            ordered_quantity = form_data.get("data_ordered_quantity", 0) or 0
            delivery_slip_quantity = form_data.get("data_slip_quantity", 0) or 0
            delivered_quantity = form_data.get("data_delivered_quantity", 0) or 0
            order_number = (form_data.get("data_order_number") or "").strip()
            delivery_number = self.item_data.get("delivery_number", "")

            # Batch-Mismatch: Nur loggen, NICHT blockieren
            original_batch = self.batch_number
            if (
                original_batch
                and confirmed_batch
                and confirmed_batch.strip() != original_batch.strip()
            ):
                logger.info(
                    "Batch abweichend - Form: '%s'," " DB: '%s'",
                    confirmed_batch,
                    original_batch,
                )

            # ===== VALIDATION =====
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

            logger.info(
                "Running validation with" " supplier_id=%s",
                supplier_id,
            )

            validation_result = validation_service.validate_data_confirmation(
                validation_data, supplier_id
            )

            if not validation_result.is_valid:
                logger.warning(
                    "Validation failed: %s",
                    validation_result.get_formatted_errors(),
                )
                st.error("❌ **Validierungsfehler:**")
                st.error(validation_result.get_formatted_errors())
                return  # Stop execution

            logger.info("Validation passed - starting saves...")

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
                st.success("✅ Lagerplatz fuer" f" {confirmed_article}" " gespeichert")
            except Exception as e:
                st.error("❌ Fehler beim Speichern der" f" Lagerplatz-Information: {e}")

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
                    "✅ Artikelnummer erfolgreich"
                    " geaendert:"
                    f" '{original_article}'"
                    f" -> '{confirmed_article}'"
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
                    "✅ Chargennummer erfolgreich"
                    " geaendert:"
                    f" '{original_batch}'"
                    f" -> '{confirmed_batch}'"
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
                st.success(
                    "✅ Liefermenge auf" f" {delivered_quantity}" " aktualisiert!"
                )

            elif order_number:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=delivery_number,
                    employee_name=employee_name,
                    order_number=order_number,
                )
                st.success("📋 Bestellnummer erfolgreich" " gespeichert!")

            # 3. Lieferschein in Artikelordner kopieren (falls vorhanden)
            # WICHTIG: Hier wird der Artikelordner erstellt!
            # Der Lieferschein wurde bereits im "Lieferscheine" Ordner gespeichert
            # und wird jetzt in den spezifischen Artikelordner kopiert
            self._save_delivery_slip_to_article_folder(
                confirmed_article, confirmed_batch, delivery_number
            )

            # 4. Bestelldokumente speichern (falls vorhanden)
            uploaded_docs = form_data.get("uploaded_documents")
            logger.info(
                "DEBUG: uploaded_docs = %s," " type = %s",
                uploaded_docs,
                type(uploaded_docs),
            )

            if uploaded_docs and len(uploaded_docs) > 0:
                st.write(f"📤 Speichere {len(uploaded_docs)}" " Bestelldokument(e)...")
                logger.info(
                    "Speichere %s Bestelldokumente" " - Ordner wird JETZT erstellt!",
                    len(uploaded_docs),
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
                            safe_order_number = (
                                order_number
                                if order_number and order_number.strip()
                                else "UNBEKANNT"
                            )
                            order_doc_filename = (
                                f"Bestellung_{safe_order_number}_{doc.name}"
                            )

                            # Save doc to article folder
                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=order_doc_filename,
                                document_type="order",
                                batch_number=confirmed_batch,
                                delivery_number=delivery_number,
                                article_number=confirmed_article,
                                supplier_name="",  # Will be auto-determined
                                create_folders=True,
                            )

                            if save_result.success:
                                st.success(
                                    "✅ Bestelldokument" f" gespeichert: {doc.name}"
                                )
                                logger.info(
                                    "Order document saved:" " %s to %s",
                                    doc.name,
                                    save_result.file_path or save_result.storage_folder,
                                )
                            else:
                                st.error(
                                    "❌ Fehler beim"
                                    " Speichern von"
                                    f" {doc.name}:"
                                    f" {save_result.error}"
                                )
                                logger.error(
                                    "Failed to save order" " document %s: %s",
                                    doc.name,
                                    save_result.error,
                                )

                        except Exception as doc_error:
                            st.error(
                                "❌ Fehler beim"
                                " Verarbeiten von"
                                f" {doc.name}:"
                                f" {doc_error}"
                            )
                            logger.error(
                                "Error processing order" " document %s: %s",
                                doc.name,
                                doc_error,
                            )

                except Exception as storage_error:
                    st.error(
                        "❌ Fehler beim Speichern der"
                        " Bestelldokumente:"
                        f" {storage_error}"
                    )
                    logger.error(
                        "Error saving order" " documents: %s",
                        storage_error,
                    )

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
                notes=(
                    "Lagerplatz:"
                    f" {confirmed_storage_location},"
                    " Bestellnummer:"
                    f" {order_number}"
                ),
            )

            # 5. Generate documents (Begleitschein, Wareneingangskontrolle, Barcode)
            st.info("📄 **Automatische" " Dokument-Erstellung laeuft...**")

            # Neue robuste Dokumentenerstellung mit DocumentOperationResult
            from warehouse.application.services.document_storage.document_storage_service import (
                DocumentOperationResult,
                StorageResult,
            )

            operation_result = DocumentOperationResult(
                operation_type="Datenbestätigung",
                auto_open=True,  # Dokumente zur Kontrolle öffnen
            )

            try:
                generation_service = DocumentGenerationService()

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
                        storage_result = StorageResult(
                            success=True,
                            file_path=begleitschein_result.document_path,
                            filename=Path(begleitschein_result.document_path).name if begleitschein_result.document_path else None,
                            storage_folder=Path(begleitschein_result.document_path).parent.as_posix() if begleitschein_result.document_path else None,
                            document_type="Begleitschein",
                        )
                        operation_result.add_document(storage_result)
                    else:
                        operation_result.add_error(f"Begleitschein: {begleitschein_result.error}")
                except Exception as e:
                    operation_result.add_error(f"Begleitschein Fehler: {e}")
                    logger.exception("Begleitschein generation failed")

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
                        },
                    )
                    if wareneingang_result.success:
                        storage_result = StorageResult(
                            success=True,
                            file_path=wareneingang_result.document_path,
                            filename=Path(wareneingang_result.document_path).name if wareneingang_result.document_path else None,
                            storage_folder=Path(wareneingang_result.document_path).parent.as_posix() if wareneingang_result.document_path else None,
                            document_type="Wareneingangskontrolle",
                        )
                        operation_result.add_document(storage_result)
                    else:
                        operation_result.add_error(f"Wareneingangskontrolle: {wareneingang_result.error}")
                except Exception as e:
                    operation_result.add_error(f"Wareneingangskontrolle Fehler: {e}")
                    logger.exception("Wareneingangskontrolle generation failed")

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
                            "open_after_creation": True,
                            "storage_location": confirmed_storage_location,
                        },
                    )
                    if barcode_result.success:
                        storage_result = StorageResult(
                            success=True,
                            file_path=barcode_result.document_path,
                            filename=Path(barcode_result.document_path).name if barcode_result.document_path else None,
                            storage_folder=Path(barcode_result.document_path).parent.as_posix() if barcode_result.document_path else None,
                            document_type="Barcode/Label",
                        )
                        operation_result.add_document(storage_result)
                    else:
                        operation_result.add_error(f"Barcode/Label: {barcode_result.error}")
                except Exception as e:
                    operation_result.add_error(f"Barcode/Label Fehler: {e}")
                    logger.exception("Barcode generation failed")

            except Exception as e:
                operation_result.add_error(f"Dokument-Generierung fehlgeschlagen: {e}")
                logger.exception("Document generation failed")

            logger.info(
                "Datenbestaetigung abgeschlossen"
                " - alle Daten gespeichert,"
                " Dokumente erstellt"
            )

            # Cleanup: Alle Form-Keys bereinigen damit der naechste Dialog
            # frische Werte bekommt (verhindert stale data in PDFs)
            _cleanup_form_session_state()

            # WICHTIG: Speichere Result in Session State für Deferred Dialog
            # Main View wird nach Rerun das Document Confirmation Popup öffnen
            if operation_result.has_documents() or operation_result.errors:
                st.session_state["pending_doc_confirmation"] = operation_result
            else:
                # Fallback falls keine Dokumente erstellt wurden
                st.warning("⚠️ Keine Dokumente erstellt.")

            # Erfolgs-Toast anzeigen (überlebt den Rerun)
            st.toast("🎉 Datenbestätigung abgeschlossen!", icon="✅")

            # Dialog schließen durch Rerun
            # Nach Rerun wird Main View den pending_doc_confirmation Dialog öffnen
            import time

            time.sleep(0.5)  # Kurz warten damit Toast sichtbar wird
            st.rerun()

        except Exception as e:
            logger.error(
                "Error in data confirmation: %s",
                e,
                exc_info=True,
            )
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
            st.info("🤖 **KI-Analyse wird durchgeführt...**")

            # TODO: Implementiere KI-Analyse hier
            # Beispiel: Analysiere hochgeladene Dokumente
            uploaded_docs = form_data.get("uploaded_documents", [])

            if uploaded_docs:
                st.write(f"📄 {len(uploaded_docs)} Dokument(e) werden analysiert...")
                # KI-Analyse-Logik hier einfügen
                st.info(
                    "⚠️ KI-Analyse noch nicht"
                    " implementiert - fuehre normale"
                    " Speicherung durch"
                )
            else:
                st.warning("⚠️ Keine Dokumente zum Analysieren hochgeladen")

            # Nach KI-Analyse: Normale Speicherung durchführen
            st.info("💾 Speichere Daten nach KI-Analyse...")
            self.handle_primary_action(form_data)

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}", exc_info=True)
            st.error(f"❌ Fehler bei KI-Analyse: {str(e)}")

    def _save_delivery_slip_to_article_folder(
        self, article_number: str, batch_number: str, delivery_number: str
    ) -> None:
        """
        Speichert den Lieferschein in den Artikelordner.

        Diese Methode wird beim Klick auf
        "Daten bestaetigen" aufgerufen und kopiert
        den Lieferschein vom zentralen "Lieferscheine"
        Ordner in den spezifischen Artikelordner.
        Dies ist der zentrale Punkt wo der
        Artikelordner erstellt wird!

        Args:
            article_number: Bestätigte Artikelnummer
            batch_number: Bestätigte Chargennummer
            delivery_number: Lieferscheinnummer

        Returns:
            None. Zeigt Erfolgs-/Fehlermeldungen in der UI an.
        """
        import streamlit as st

        try:
            # Lade Lieferschein direkt aus Supplier/Lieferscheine/ Ordner
            # (wird beim Upload dort bereits gespeichert)
            document_data, filename = self._load_delivery_slip_from_disk(
                delivery_number
            )

            if not document_data:
                logger.warning(
                    "Could not find delivery slip in Lieferscheine/ folder"
                    " - skipping save to article folder"
                )
                st.info(
                    "ℹ️ Lieferschein nicht gefunden - "
                    "wurde ggf. schon im Artikelordner gespeichert"
                )
                return

            logger.info(
                "Saving delivery slip to article folder: %s / %s (%s)",
                article_number,
                batch_number,
                filename,
            )

            # Get document storage service
            from warehouse.application.services.service_registry import (
                get_document_storage_service,
            )

            storage_service = get_document_storage_service()

            if not storage_service:
                st.warning("⚠️ Document Storage Service nicht verfügbar")
                return

            # Save delivery slip to article folder
            # WICHTIG: create_folders=True erstellt
            # den Artikelordner!
            save_result = storage_service.save_document(
                document_data=document_data,
                document_name=filename,
                document_type="delivery_slip",
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=self.supplier_name,
                create_folders=True,
            )

            if save_result.success:
                st.success("✅ Lieferschein in" " Artikelordner gespeichert")
                logger.info(
                    "Delivery slip saved to article" " folder: %s",
                    save_result.storage_folder,
                )
            else:
                st.warning(
                    "⚠️ Lieferschein konnte nicht"
                    " im Artikelordner gespeichert"
                    f" werden: {save_result.error}"
                )
                logger.error(
                    "Failed to save delivery slip" " to article folder: %s",
                    save_result.error,
                )

        except Exception as e:
            logger.error(
                "Error saving delivery slip to" " article folder: %s",
                e,
                exc_info=True,
            )
            st.warning(
                "⚠️ Fehler beim Speichern des"
                " Lieferscheins im"
                f" Artikelordner: {e}"
            )

    def _load_delivery_slip_from_disk(
        self, delivery_number: str
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Lädt Lieferschein aus dem zentralen Lieferscheine/ Ordner.

        Der Lieferschein wird beim Upload in Supplier/Lieferscheine/ gespeichert
        und wird von hier beim "Daten bestätigen" in den Artikelordner kopiert.

        Sucht im Lieferscheine/ Ordner nach PDFs die delivery_number enthalten.

        Args:
            delivery_number: Lieferscheinnummer zum Suchen

        Returns:
            Tuple[document_data, filename] oder (None, None) wenn nicht gefunden
        """
        try:
            from warehouse.application.services.document_storage.path_resolver import (
                path_resolver,
            )

            # Hole Supplier aus item_data
            supplier_name = self.item_data.get("supplier_name", "")
            if not supplier_name:
                logger.warning(
                    "Cannot load delivery slip - no supplier name available"
                )
                return None, None

            # Resolve Lieferschein-Pfad
            path_result = path_resolver.resolve_delivery_slip_path(
                supplier_name=supplier_name,
                create_folders=False,  # Nur lesen, nicht erstellen
            )

            if not path_result.success or not path_result.path.exists():
                logger.warning(
                    f"Delivery slip folder does not exist: {path_result.path}"
                )
                return None, None

            # Suche nach PDF-Datei mit delivery_number im Namen
            delivery_slip_folder = path_result.path
            logger.info(
                f"Searching for delivery slip in: {delivery_slip_folder}"
            )

            # Pattern-Matching: Suche nach Dateien die delivery_number enthalten
            matching_files = []
            for pdf_file in delivery_slip_folder.glob("*.pdf"):
                if delivery_number.lower() in pdf_file.name.lower():
                    matching_files.append(pdf_file)

            if not matching_files:
                logger.warning(
                    f"No delivery slip found for {delivery_number} "
                    f"in {delivery_slip_folder}"
                )
                return None, None

            # Wenn mehrere gefunden: Nimm neueste Datei
            if len(matching_files) > 1:
                logger.warning(
                    f"Multiple delivery slips found for {delivery_number}, "
                    f"using newest: {[f.name for f in matching_files]}"
                )
                matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            delivery_slip_file = matching_files[0]
            logger.info(f"Loading delivery slip from disk: {delivery_slip_file}")

            # Lese Datei als bytes
            document_data = delivery_slip_file.read_bytes()
            filename = delivery_slip_file.name

            return document_data, filename

        except Exception as e:
            logger.error(
                f"Error loading delivery slip from disk: {e}",
                exc_info=True,
            )
            return None, None

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
    # Stale Form-Keys vom vorherigen Dialog bereinigen, aber NUR wenn sich
    # der Artikel geaendert hat (sonst wuerden User-Eingaben bei jedem
    # Rerun innerhalb des Dialogs zurueckgesetzt)
    _current_item_key = (
        f"{item_data.get('article_number')}"
        f"_{item_data.get('batch_number')}"
        f"_{item_data.get('delivery_number')}"
    )
    if st.session_state.get("_dc_item_key") != _current_item_key:
        _cleanup_form_session_state()
        st.session_state["_dc_item_key"] = _current_item_key

    # Flag setzen, dass Popup nur am Rendern ist - KEINE Ordner erstellen!
    st.session_state["data_confirmation_action_clicked"] = False

    logger.info(
        "show_data_confirmation_popup called"
        " - Rendering nur, KEINE"
        " Ordner-Erstellung"
    )

    popup = DataConfirmationPopup(item_data)
    popup._apply_css()  # CSS anwenden für kompakte Abstände

    # Render Popup
    popup.render_header()
    form_data = popup.render_body()
    action = popup.render_footer()

    # Handle Actions - direkt und einfach
    if action == "save":
        logger.info("'Daten bestätigen' Button geklickt")
        popup.handle_primary_action(form_data)
    elif action == "ai_save":
        popup.handle_ai_analysis_action(form_data)
    elif action == "cancel":
        _cleanup_form_session_state()
        st.rerun()
