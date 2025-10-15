"""
Data Confirmation Popup
User-facing popup for confirming delivery slip data.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from warehouse.presentation.user.popups.core.base_popup import InspectionPopup
from warehouse.presentation.user.popups.components import (
    render_article_header,
    FormBuilder,
    render_standard_footer,
    render_document_uploader
)

logger = logging.getLogger(__name__)


class DataConfirmationPopup(InspectionPopup):
    """Popup für Datenbestätigung (Schritt 1)."""

    def __init__(self, item_data: Dict[str, Any]):
        super().__init__(
            title="📋 Daten bestätigen",
            item_data=item_data,
            show_info_box=False,
            info_text=None
        )

    def render_header(self) -> None:
        """Rendert kompakten Artikel-Header."""
        # Kompaktes CSS für das gesamte Popup - EXTRA KOMPAKT
        st.markdown("""
        <style>
        /* Reduziere Abstände im Dialog - MINIMAL */
        div[data-testid="stDialog"] section[data-testid="stVerticalBlock"] {
            gap: 0.1rem !important;
        }

        /* Popup-Titel (h1) - minimaler Abstand */
        div[data-testid="stDialog"] h1 {
            margin-top: 0 !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0 !important;
        }

        /* Kompakte Überschriften - H4 für Sektionen */
        div[data-testid="stDialog"] h4 {
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0.2rem !important;
            padding-bottom: 0 !important;
            font-size: 0.95rem !important;
        }

        /* H3 - noch kompakter */
        div[data-testid="stDialog"] h3 {
            margin-top: 0.1rem !important;
            margin-bottom: 0.2rem !important;
            padding: 0 !important;
        }

        /* Kompakte Markdown/Text */
        div[data-testid="stDialog"] p {
            margin-top: 0.1rem !important;
            margin-bottom: 0.1rem !important;
            padding: 0 !important;
        }

        /* Kompakte Input-Felder */
        div[data-testid="stDialog"] .stTextInput > div,
        div[data-testid="stDialog"] .stNumberInput > div,
        div[data-testid="stDialog"] .stTextArea > div {
            margin-bottom: 0.1rem !important;
            margin-top: 0.1rem !important;
        }

        /* Kompakte Labels */
        div[data-testid="stDialog"] label {
            margin-bottom: 0.1rem !important;
            padding-bottom: 0.1rem !important;
        }

        /* Kompakte Info-Boxen */
        div[data-testid="stDialog"] .stAlert {
            padding: 0.3rem !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }

        /* Kompakte Divider */
        div[data-testid="stDialog"] hr {
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }

        /* Kompakte Columns */
        div[data-testid="stDialog"] div[data-testid="column"] {
            gap: 0.1rem !important;
        }

        /* Kompakte Metrics */
        div[data-testid="stDialog"] div[data-testid="metric-container"] {
            padding: 0.2rem !important;
        }

        /* File Uploader kompakter */
        div[data-testid="stDialog"] .stFileUploader {
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }

        /* Expander kompakter */
        div[data-testid="stDialog"] .streamlit-expanderHeader {
            padding: 0.2rem !important;
        }

        div[data-testid="stDialog"] .streamlit-expanderContent {
            padding: 0.2rem !important;
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
        """Rendert Formular für Datenbestätigung."""
        form = FormBuilder(columns=2)

        # Sektion 1: Artikeldaten bestätigen
        form.add_section("🔍 Artikeldaten", expanded=True, use_expander=False)

        form.add_text_input(
            "Artikelnummer:",
            key="data_article_number",
            value=self.article_number,
            help="Artikelnummer vom Lieferschein"
        )

        form.add_text_input(
            "Chargennummer:",
            key="data_batch_number",
            value=self.batch_number,
            help="Chargennummer vom Lieferschein"
        )

        # Sektion 2: Mengenerfassung
        form.add_section("📊 Mengenerfassung", expanded=True, use_expander=False)

        # Lade Mengen aus DB falls vorhanden
        ordered_qty = int(self.item_data.get('ordered_quantity', 0)) if self.item_data.get('ordered_quantity') else 0
        slip_qty = int(self.item_data.get('delivery_slip_quantity', 0)) if self.item_data.get('delivery_slip_quantity') else (self.quantity if self.quantity else 0)
        delivered_qty = int(self.item_data.get('delivered_quantity', 0)) if self.item_data.get('delivered_quantity') else 0

        form.add_number_input(
            "Bestellmenge:",
            key="data_ordered_quantity",
            value=ordered_qty,
            min_value=0,
            help="Ursprünglich bestellte Menge"
        )

        form.add_number_input(
            "Lieferscheinmenge (OCR):",
            key="data_slip_quantity",
            value=slip_qty,
            min_value=0,
            help="Vom Lieferschein extrahierte Menge"
        )

        form.add_number_input(
            "Liefermenge (gezählt):",
            key="data_delivered_quantity",
            value=delivered_qty,
            min_value=0,
            help="Tatsächlich gelieferte und gezählte Menge"
        )

        # Sektion 3: Zusätzliche Daten
        form.add_section("📦 Zusätzliche Informationen", expanded=True, use_expander=False)

        # Lade Lagerplatz aus DB falls vorhanden
        try:
            from warehouse.application.services.data_integration_service import data_integration_service
            existing_storage = data_integration_service.get_storage_location_from_article(
                self.article_number
            )
        except Exception:
            existing_storage = self.item_data.get('storage_location', '')

        form.add_text_input(
            "Lagerplatz:",
            key="data_storage_location",
            value=existing_storage or '',
            placeholder="z.B. A-01-02",
            help="Lagerplatz für den Artikel (wird aus DB geladen falls vorhanden)"
        )

        # Lade Bestellnummer aus DB - prüfe mehrere mögliche Keys wie im Admin-Popup
        extracted_order_number = (
            self.item_data.get('order_number', '') or
            self.item_data.get('bestellnummer', '') or
            self.item_data.get('purchase_order', '') or
            self.item_data.get('po_number', '') or
            self.item_data.get('order_nr', '') or
            self.item_data.get('bestell_nr', '') or
            self.item_data.get('bestellung', '') or
            self.item_data.get('purchase_order_number', '') or
            ''
        )

        form.add_text_input(
            "Bestellnummer:",
            key="data_order_number",
            value=extracted_order_number,
            placeholder="Bestellnummer eingeben",
            help="Bestellnummer aus dem Lieferschein"
        )

        form.add_text_area(
            "Bemerkungen:",
            key="data_notes",
            value="",
            height=40,
            placeholder="Optionale Bemerkungen...",
            help="Zusätzliche Anmerkungen"
        )

        # Render und hole Daten
        form_data = form.render()

        # Sektion 4: Bestelldokumente hochladen
        st.markdown("---")

        uploaded_docs = render_document_uploader(
            label="Bestelldokumente hochladen",
            key="data_order_documents",
            file_types=['pdf', 'png', 'jpg', 'jpeg', 'docx'],
            accept_multiple=True,
            help_text="Laden Sie die Bestelldokumente hoch (z.B. Bestellung, Auftragsbestätigung)"
        )

        # Speichere hochgeladene Dokumente in form_data
        form_data['uploaded_documents'] = uploaded_docs

        return form_data

    def render_footer(self) -> Optional[str]:
        """Rendert Standard-Footer."""
        return render_standard_footer(
            save_label="💾 Daten bestätigen",
            cancel_label="❌ Abbrechen"
        )

    def handle_primary_action(self, form_data: Dict[str, Any]) -> None:
        """
        Speichert bestätigte Daten in die Datenbank.

        Args:
            form_data: Formulardaten vom Body
        """
        import logging
        from datetime import datetime
        from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService

        logger = logging.getLogger(__name__)

        try:

            # Extract and validate data
            confirmed_article = form_data.get('data_article_number', '').strip()
            confirmed_batch = form_data.get('data_batch_number', '').strip()
            confirmed_storage_location = form_data.get('data_storage_location', '').strip()
            ordered_quantity = form_data.get('data_ordered_quantity', 0)
            delivery_slip_quantity = form_data.get('data_slip_quantity', 0)  # FIXED: Correct key!
            delivered_quantity = form_data.get('data_delivered_quantity', 0)
            order_number = form_data.get('data_order_number', '').strip()

            # Validation
            if not confirmed_article:
                st.error("❌ Artikelnummer ist erforderlich!")
                st.stop()

            if not confirmed_batch:
                st.error("❌ Chargennummer ist erforderlich!")
                st.stop()

            # Get services
            item_service = st.session_state.services['item']

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
                    description=""
                )
                st.success(f"✅ Lagerplatz für {confirmed_article} gespeichert")
            except Exception as e:
                st.error(f"❌ Fehler beim Speichern der Lagerplatz-Information: {e}")

            # 2. Update item with all data
            original_article = self.item_data.get('article_number', '')
            original_batch = self.item_data.get('batch_number', '')
            delivery_number = self.item_data.get('delivery_number', '')

            # Handle article/batch number changes
            if original_article and original_article != confirmed_article:
                item_service.update_item(
                    article_number=original_article,
                    batch_number=original_batch if original_batch else confirmed_batch,
                    delivery_number=delivery_number,
                    new_article_number=confirmed_article,
                    new_batch_number=confirmed_batch if original_batch and original_batch != confirmed_batch else None,
                    new_quantity=delivered_quantity if delivered_quantity > 0 else None,
                    employee_name=st.session_state.get('current_user', 'System'),
                    order_number=order_number,
                    delivery_slip_quantity=delivery_slip_quantity,
                    ordered_quantity=ordered_quantity
                )
                st.success(f"✅ Artikelnummer erfolgreich geändert: '{original_article}' → '{confirmed_article}'")

            elif original_batch and original_batch != confirmed_batch:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=original_batch,
                    delivery_number=delivery_number,
                    new_batch_number=confirmed_batch,
                    new_quantity=delivered_quantity if delivered_quantity > 0 else None,
                    employee_name=st.session_state.get('current_user', 'System'),
                    order_number=order_number,
                    delivery_slip_quantity=delivery_slip_quantity,
                    ordered_quantity=ordered_quantity
                )
                st.success(f"✅ Chargennummer erfolgreich geändert: '{original_batch}' → '{confirmed_batch}'")

            elif delivered_quantity > 0:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=delivery_number,
                    new_quantity=delivered_quantity,
                    employee_name=st.session_state.get('current_user', 'System'),
                    order_number=order_number,
                    delivery_slip_quantity=delivery_slip_quantity,
                    ordered_quantity=ordered_quantity
                )
                st.success(f"✅ Liefermenge auf {delivered_quantity} aktualisiert!")

            elif order_number:
                item_service.update_item(
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=delivery_number,
                    employee_name=st.session_state.get('current_user', 'System'),
                    order_number=order_number
                )
                st.success("📋 Bestellnummer erfolgreich gespeichert!")

            # 3. Save uploaded order documents (ADMIN STYLE - MISSING IN USER VIEW!)
            uploaded_docs = form_data.get('uploaded_documents', [])
            if uploaded_docs:
                st.write(f"📤 Speichere {len(uploaded_docs)} Bestelldokument(e)...")
                try:
                    from warehouse.application.services.service_registry import get_document_storage_service
                    storage_service = get_document_storage_service()

                    for doc in uploaded_docs:
                        try:
                            # Read document data
                            document_data = doc.read()

                            # Create filename with prefix
                            safe_order_number = order_number if order_number and order_number.strip() else "UNBEKANNT"
                            order_doc_filename = f"Bestellung_{safe_order_number}_{doc.name}"

                            # Save order document to article folder
                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=order_doc_filename,
                                document_type="order",
                                batch_number=confirmed_batch,
                                delivery_number=delivery_number,
                                article_number=confirmed_article,
                                supplier_name=""  # Will be auto-determined
                            )

                            if save_result.success:
                                st.success(f"✅ Bestelldokument gespeichert: {doc.name}")
                                logger.info(f"✅ Order document saved: {doc.name} to {save_result.path}")
                            else:
                                st.error(f"❌ Fehler beim Speichern von {doc.name}: {save_result.error}")
                                logger.error(f"❌ Failed to save order document {doc.name}: {save_result.error}")

                        except Exception as doc_error:
                            st.error(f"❌ Fehler beim Verarbeiten von {doc.name}: {doc_error}")
                            logger.error(f"Error processing order document {doc.name}: {doc_error}")

                except Exception as storage_error:
                    st.error(f"❌ Fehler beim Speichern der Bestelldokumente: {storage_error}")
                    logger.error(f"Error saving order documents: {storage_error}")

            # 4. Set workflow status
            item_service.complete_data_check(
                article_number=confirmed_article,
                batch_number=confirmed_batch,
                delivery_number=delivery_number,
                employee=st.session_state.get('current_user', 'System')
            )
            st.success("✅ Datenprüfung abgeschlossen")

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
                        employee_name=st.session_state.get('current_user', 'System'),
                        additional_data={
                            'status': 'Daten bestätigt',
                            'order_number': order_number
                        }
                    )
                    if begleitschein_result.success:
                        documents_created.append('Begleitschein')
                        st.write(f"  ✅ Begleitschein: {begleitschein_result.document_path}")
                    else:
                        generation_errors.append(f"Begleitschein: {begleitschein_result.error}")
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
                        employee_name=st.session_state.get('current_user', 'System'),
                        additional_data={
                            'we_date': datetime.now().strftime('%d.%m.%Y'),
                            'artikel': confirmed_article,
                            'charge': confirmed_batch
                        }
                    )
                    if wareneingang_result.success:
                        documents_created.append('Wareneingangskontrolle')
                        st.write(f"  ✅ Wareneingangskontrolle: {wareneingang_result.document_path}")
                    else:
                        generation_errors.append(f"Wareneingangskontrolle: {wareneingang_result.error}")
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
                        employee_name=st.session_state.get('current_user', 'System'),
                        additional_data={
                            'barcode_type': 'CODE128',
                            'filename_prefix': 'label',
                            'open_after_creation': False,
                            'storage_location': confirmed_storage_location
                        }
                    )
                    if barcode_result.success:
                        documents_created.append('Barcode/Label')
                        st.write(f"  ✅ Barcode/Label: {barcode_result.document_path}")
                    else:
                        generation_errors.append(f"Barcode/Label: {barcode_result.error}")
                except Exception as e:
                    generation_errors.append(f"Barcode/Label Fehler: {e}")

                # Show summary
                if documents_created:
                    st.success(f"📄 {len(documents_created)} Dokument(e) erstellt: {', '.join(documents_created)}")
                if generation_errors:
                    for error in generation_errors:
                        st.warning(f"⚠️ {error}")

            except Exception as e:
                st.warning(f"⚠️ Dokument-Generierung teilweise fehlgeschlagen: {e}")

            st.success("🎉 **Datenbestätigung abgeschlossen!**")
            st.rerun()

        except Exception as e:
            logger.error(f"Error in data confirmation: {e}", exc_info=True)
            st.error(f"❌ Fehler beim Speichern: {str(e)}")

    def handle_secondary_action(self, form_data: Dict[str, Any]) -> None:
        """Zurückweisen - markiert Artikel als Ausschuss."""
        # Nicht verwendet für Data Confirmation
        pass


@st.dialog("📋 Daten bestätigen", width="large")
def show_data_confirmation_popup(item_data: Dict[str, Any]) -> None:
    """
    Zeigt Data Confirmation Popup.

    Args:
        item_data: Dictionary mit Item-Informationen
    """
    popup = DataConfirmationPopup(item_data)

    # Render Popup
    popup.render_header()
    form_data = popup.render_body()
    action = popup.render_footer()

    # Handle Actions
    if action == 'save':
        popup.handle_primary_action(form_data)
    elif action == 'cancel':
        st.rerun()
