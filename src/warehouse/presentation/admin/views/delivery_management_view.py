"""
Delivery Management View - Admin Presentation Layer
Complete delivery management interface with all functionality.
"""

import streamlit as st
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from warehouse.application.services.entity_services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)


def show_delivery_management_view():
    """Main delivery management view with all tabs and functionality."""
    st.header("🚚 Delivery Management")

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "delivery" not in services:
        st.error("Delivery Service nicht verfügbar")
        return

    delivery_service = services["delivery"]

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Delivery Liste", "➕ Neu erstellen", "📊 Statistiken", "📄 Dokumente"]
    )

    with tab1:
        show_delivery_list_tab(delivery_service)

    with tab2:
        show_new_delivery_tab(delivery_service)

    with tab3:
        show_statistics_tab(delivery_service)

    with tab4:
        show_documents_tab()

    # Handle extraction popup
    if st.session_state.get("show_extraction_popup") and st.session_state.get(
        "extracted_delivery_data"
    ):
        from warehouse.presentation.admin.popups.delivery_view.delivery_popups import (
            show_extraction_confirmation_popup,
        )

        show_extraction_confirmation_popup(st.session_state.extracted_delivery_data)

    # Handle popup actions
    if st.session_state.get("popup_action"):
        action = st.session_state.popup_action

        if action == "extraction_confirm":
            # User confirmed extraction data - save to database using working implementation
            extraction_data = st.session_state.extraction_confirmed

            try:
                # Use the DeliveryService.create_delivery_from_extraction method
                delivery_service = DeliveryService()
                result = delivery_service.create_delivery_from_extraction(extraction_data)

                # Store result info for popup display
                st.session_state.save_result = result

                if result.get("success"):
                    success_message = f"Lieferung '{extraction_data.get('delivery_number')}' erfolgreich gespeichert!"
                    if result.get("items_created", 0) > 0:
                        success_message += (
                            f" {result.get('items_created')} Items erstellt."
                        )
                    if result.get("items_failed", 0) > 0:
                        success_message += (
                            f" {result.get('items_failed')} Items fehlgeschlagen."
                        )

                    # Show success popup
                    st.session_state.show_success_popup = True
                    st.session_state.success_message = success_message

                    # Clean up session state
                    if "extracted_delivery_data" in st.session_state:
                        del st.session_state.extracted_delivery_data
                else:
                    # Show error popup
                    st.session_state.show_error_popup = True
                    st.session_state.error_message = f"Fehler beim Speichern: {result.get('error', 'Unbekannter Fehler')}"

            except Exception as e:
                logger.error(f"Database save error: {e}")
                # Show error popup for exceptions
                st.session_state.show_error_popup = True
                st.session_state.error_message = f"Fehler beim Speichern: {e}"

            st.session_state.confirmed_extraction = extraction_data

        elif action == "extraction_edit":
            # User wants to edit extraction data
            st.info("📝 Bearbeitung noch nicht implementiert")

        elif action == "extraction_discard":
            # User discarded extraction data
            st.warning("❌ Daten wurden verworfen")

        elif action == "delete_confirm":
            # User confirmed delivery deletion
            delivery_to_delete = st.session_state.get("delete_delivery_confirmed")
            if delivery_to_delete:
                try:
                    # Get delivery number from the confirmed data
                    delivery_number = delivery_to_delete.get("delivery_number")
                    if delivery_number:
                        success = delivery_service.delete_delivery(delivery_number)
                        if success:
                            st.success(
                                f"✅ Delivery '{delivery_number}' erfolgreich gelöscht!"
                            )

                            # Clear any related item status updates from session state for Wareneingangskontrolle
                            keys_to_remove = [
                                key
                                for key in st.session_state.keys()
                                if key.startswith("item_status_")
                                and delivery_number in key
                            ]
                            for key in keys_to_remove:
                                del st.session_state[key]
                        else:
                            st.warning(
                                f"⚠️ Delivery '{delivery_number}' konnte nicht gelöscht werden"
                            )
                    else:
                        st.error("❌ Delivery-Nummer nicht gefunden")

                    # Clear session state
                    if "delete_delivery_confirmed" in st.session_state:
                        del st.session_state.delete_delivery_confirmed

                except Exception as e:
                    logger.error(f"Delivery deletion error: {e}")
                    st.error(f"❌ Fehler beim Löschen der Delivery: {e}")
                    # Clear session state even on error
                    if "delete_delivery_confirmed" in st.session_state:
                        del st.session_state.delete_delivery_confirmed

        elif action == "close":
            # Close popup
            pass

        # Clear popup state
        st.session_state.popup_action = None
        st.session_state.show_extraction_popup = False
        if action != "close":
            st.rerun()

    # Handle success popup
    if st.session_state.get("show_success_popup"):
        from warehouse.presentation.admin.popups.delivery_view.delivery_popups import (
            show_delivery_success_popup,
        )

        show_delivery_success_popup(
            st.session_state.get(
                "success_message", "Vorgang erfolgreich abgeschlossen!"
            )
        )
        st.session_state.show_success_popup = False
        st.balloons()

    # Handle error popup
    if st.session_state.get("show_error_popup"):
        from warehouse.presentation.admin.popups.delivery_view.delivery_popups import (
            show_delivery_error_popup,
        )

        show_delivery_error_popup(
            st.session_state.get("error_message", "Ein Fehler ist aufgetreten!")
        )
        st.session_state.show_error_popup = False


def show_inspection_tab():
    """Show quality inspection tab."""
    try:
        # Import inspection view from presentation layer
        from warehouse.presentation.admin.views.inspection_control_view import (
            show_inspection_control_view,
        )

        show_inspection_control_view()
    except ImportError:
        # Fallback: show placeholder with title
        st.subheader("🔍 Wareneingangskontrolle")
        st.info("Wareneingangskontrolle wird aus streamlit_app.py migriert...")
        st.write("Diese Funktion ist in Entwicklung.")


def show_delivery_list_tab(delivery_service):
    """Show delivery list with management actions."""
    st.subheader("📋 Delivery Liste")

    try:
        # Get all deliveries
        deliveries_data = []
        if hasattr(delivery_service, "get_all_deliveries"):
            deliveries_data = delivery_service.get_all_deliveries()

        if deliveries_data:
            # Display deliveries with action buttons
            for i, delivery_dict in enumerate(deliveries_data):
                render_delivery_row(delivery_dict, i, delivery_service)

                if i < len(deliveries_data) - 1:
                    st.divider()
        else:
            st.info("Keine Deliveries gefunden")

            # Quick action to create first delivery
            if st.button("➕ Erste Delivery erstellen", type="primary"):
                st.session_state.switch_to_create_tab = True
                st.rerun()

    except Exception as e:
        logger.error(f"Error loading deliveries: {e}")
        st.error(f"Fehler beim Laden der Deliveries: {e}")


def render_delivery_row(delivery_dict: Dict[str, Any], index: int, delivery_service):
    """Render a single delivery row with actions."""
    # Extract status and convert to string if needed
    status = delivery_dict.get("status", "N/A")
    if hasattr(status, "value"):
        status = status.value
    elif hasattr(status, "__str__"):
        status = str(status)

    # Create columns for delivery data
    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2, 1, 1])

    with col1:
        st.write(f"**{delivery_dict.get('delivery_number', 'N/A')}**")
    with col2:
        st.write(delivery_dict.get("supplier_id", "N/A"))
    with col3:
        st.write(str(delivery_dict.get("delivery_date", "N/A")))
    with col4:
        # Status with color
        if status in ["COMPLETED", "DELIVERED"]:
            st.success(status)
        elif status in ["PENDING", "IN_PROGRESS"]:
            st.warning(status)
        else:
            st.info(status)
    with col5:
        items_count = delivery_dict.get("items_count", 0)
        st.write(f"{items_count} Items")

        # Show additional info on click
        if st.button(f"ℹ️", key=f"info_del_{index}", help="Details anzeigen"):
            show_delivery_details_popup(delivery_dict, delivery_service)

    with col6:
        if st.button("🖊️", key=f"edit_del_{index}", help="Delivery bearbeiten"):
            show_delivery_edit_action(delivery_dict, delivery_service)

    with col7:
        if st.button("🗑️", key=f"delete_del_{index}", help="Delivery löschen"):
            show_delivery_delete_action(delivery_dict)


def show_delivery_edit_action(delivery_dict: Dict[str, Any], delivery_service):
    """Handle delivery edit action."""
    try:
        # Try to get delivery items
        delivery_items = []
        if hasattr(delivery_service, "get_delivery_items"):
            delivery_items = delivery_service.get_delivery_items(
                delivery_dict["delivery_number"]
            )

        # Import and show edit popup
        from warehouse.presentation.admin.popups.delivery_view.delivery_popups import (
            show_delivery_edit_popup,
        )

        show_delivery_edit_popup(delivery_dict, delivery_items)

    except Exception as e:
        logger.error(f"Error in delivery edit action: {e}")
        st.error(f"Fehler beim Bearbeiten: {e}")


def show_delivery_delete_action(delivery_dict: Dict[str, Any]):
    """Handle delivery delete action."""
    try:
        from warehouse.presentation.admin.popups.delivery_view.delivery_popups import (
            show_delivery_delete_popup,
        )

        show_delivery_delete_popup(delivery_dict)
    except Exception as e:
        logger.error(f"Error in delivery delete action: {e}")
        st.error(f"Fehler beim Löschen: {e}")


def show_delivery_details_popup(delivery_dict: Dict[str, Any], delivery_service):
    """Show delivery details in popup."""
    st.session_state.selected_delivery = delivery_dict
    st.session_state.show_delivery_details = True


def show_new_delivery_tab(delivery_service):
    """Show new delivery creation tab."""
    st.subheader("➕ Neue Delivery mit Items erstellen")

    # Check if switched from list tab
    if st.session_state.get("switch_to_create_tab"):
        st.info("✨ Erstellen Sie Ihre erste Delivery!")
        del st.session_state.switch_to_create_tab

    # OCR + Claude API Workflow Section
    show_ocr_claude_workflow(delivery_service)

    st.write("---")

    # Manual delivery creation section
    show_manual_delivery_creation(delivery_service)


def show_ocr_claude_workflow(delivery_service):
    """Show OCR + Claude API workflow for delivery creation."""
    st.write("### 📄 Lieferschein PDF hochladen und auswerten")
    st.info(
        "🔄 **OCR → Claude-API → JSON → DB Workflow** - Strukturierte Datenextraktion!"
    )

    # System status check
    show_system_status_check()

    # File upload and processing
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_pdf = st.file_uploader(
            "📎 PDF-Datei auswählen",
            type=["pdf", "png", "jpg", "jpeg", "tiff"],
            help="Laden Sie eine PDF-Datei oder Bild mit Lieferschein-Daten hoch",
            key="ocr_pdf_upload",
        )

    with col2:
        if uploaded_pdf:
            if st.button(
                "🤖 OCR + Claude Analyse", type="primary", use_container_width=True
            ):
                process_uploaded_delivery_file(uploaded_pdf, delivery_service)


def show_system_status_check():
    """Show system status for OCR and Claude API."""
    # API Key Check
    api_key_available = bool(os.getenv("ANTHROPIC_API_KEY"))

    col1, col2 = st.columns(2)

    with col1:
        if api_key_available:
            st.success("✅ Claude API-Key verfügbar")
        else:
            st.error("❌ ANTHROPIC_API_KEY nicht gesetzt!")
            with st.expander("🔧 API Key konfigurieren"):
                st.code('$env:ANTHROPIC_API_KEY="sk-ant-api03-ihr-echter-key"')

    with col2:
        # Check OCR availability
        processors = st.session_state.get("processors", {})
        if "ocr" in processors:
            ocr_available = processors["ocr"].is_ocr_available()
            if ocr_available:
                st.success("✅ Tesseract OCR verfügbar")
            else:
                st.warning("⚠️ Tesseract OCR nicht verfügbar")
                with st.expander("🔧 Tesseract installieren"):
                    st.markdown(
                        """
                    **Windows:**
                    1. Download: [Tesseract Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)
                    2. Mit German Language Pack installieren ✓
                    3. Streamlit App neu starten
                    """
                    )


def process_uploaded_delivery_file(uploaded_file, delivery_service):
    """Process uploaded file using delivery workflow."""
    progress_bar = st.progress(0)
    status_container = st.container()

    try:
        with status_container:
            st.info("🔍 **Schritt 1/4:** Datei verarbeiten...")
        progress_bar.progress(25)

        # OLD: Use delivery processing workflow
        # processors = st.session_state.get("processors", {})
        # if "delivery_workflow" not in processors:
        #     raise Exception("Delivery workflow not available")
        # workflow = processors["delivery_workflow"]

        # NEW: Use hybrid system (System B → A) for delivery slip processing
        processors = st.session_state.get("processors", {})
        if "document_processing_service" not in processors:
            raise Exception("Document processing service not available")

        document_processing_service = processors["document_processing_service"]

        with status_container:
            st.info("🤖 **Schritt 2/4:** AI-Datenextraktion...")
        progress_bar.progress(50)

        # OLD: Process file with workflow
        # result = workflow.process_uploaded_file(
        #     uploaded_file,

        # NEW: Process file with unified service
        # Read uploaded file data
        uploaded_file.seek(0)  # Reset file pointer
        document_data = uploaded_file.read()

        # Process delivery slip using unified document processing
        st.info(f"🔧 DEBUG: About to call process_document() with {len(document_data)} bytes")

        result = document_processing_service.process_document(
            document_data=document_data,
            document_type="delivery",
            context={
                'document_data': document_data,
                'filename': uploaded_file.name
            }
        )

        st.info(f"🔧 DEBUG: process_document() returned: {result.get('success', 'unknown')}")

        with status_container:
            st.info("✅ **Schritt 3/4:** Daten validieren...")
        progress_bar.progress(75)

        if result:
            # Store result in session state for confirmation popup
            st.session_state.extracted_delivery_data = result

            with status_container:
                st.success("🎉 **Schritt 4/4:** Extraktion erfolgreich!")

                # Show storage success if available
                if result.get('storage', {}).get('success'):
                    storage_path = result['storage'].get('relative_path', 'Unbekannt')
                    st.info(f"📁 Lieferschein gespeichert: {storage_path}")

                    # Show normalization info if applicable
                    if result.get('supplier_detection', {}).get('original_name') != result.get('supplier_detection', {}).get('normalized_name'):
                        original = result['supplier_detection']['original_name']
                        normalized = result['supplier_detection']['normalized_name']
                        st.info(f"🏷️ Lieferant normalisiert: {original} → {normalized}")

            progress_bar.progress(100)

            # Show extraction confirmation popup
            st.session_state.extracted_delivery_data = result
            st.session_state.show_extraction_popup = True
            st.rerun()
        else:
            st.error("❌ Keine Daten extrahiert. Bitte prüfen Sie die Datei.")

    except Exception as e:
        logger.error(f"File processing failed: {e}")
        st.error(f"❌ Verarbeitung fehlgeschlagen: {e}")
    finally:
        progress_bar.empty()
        status_container.empty()


def show_manual_delivery_creation(delivery_service):
    """Show manual delivery creation form."""
    st.write("### ✏️ Manuelle Delivery-Erstellung")

    with st.form("manual_delivery_form"):
        col1, col2 = st.columns(2)

        with col1:
            delivery_number = st.text_input(
                "Lieferscheinnummer*", placeholder="LS-2024-001"
            )
            supplier_name = st.text_input("Lieferant*", placeholder="Lieferantenname")
            delivery_date = st.date_input("Lieferdatum", value=datetime.now().date())

        with col2:
            employee_name = st.text_input(
                "Bearbeiter", placeholder="Mitarbeitername", value="Manual Entry"
            )
            notes = st.text_area("Notizen", placeholder="Zusätzliche Informationen...")

        # Items section
        st.write("**Items hinzufügen:**")

        # Simple item entry
        item_col1, item_col2, item_col3 = st.columns(3)
        with item_col1:
            article_number = st.text_input("Artikelnummer", placeholder="A0001")
        with item_col2:
            batch_number = st.text_input("Chargennummer", placeholder="B-12345")
        with item_col3:
            quantity = st.number_input("Menge", min_value=1, value=1)

        # Submit button
        if st.form_submit_button("➕ Delivery erstellen", type="primary"):
            create_manual_delivery(
                delivery_service,
                delivery_number,
                supplier_name,
                delivery_date,
                employee_name,
                notes,
                article_number,
                batch_number,
                quantity,
            )


def create_manual_delivery(
    delivery_service,
    delivery_number,
    supplier_name,
    delivery_date,
    employee_name,
    notes,
    article_number,
    batch_number,
    quantity,
):
    """Create delivery manually."""
    try:
        # Validation
        if not delivery_number or not supplier_name:
            st.error("❌ Lieferscheinnummer und Lieferant sind erforderlich!")
            return

        # Prepare delivery data
        items = []
        if article_number:
            items.append(
                {
                    "article_number": article_number,
                    "batch_number": batch_number
                    or f"AUTO-{datetime.now().strftime('%Y%m%d')}",
                    "quantity": quantity,
                }
            )

        # Create delivery using service
        if hasattr(delivery_service, "create_delivery_with_items") and items:
            result = delivery_service.create_delivery_with_items(
                delivery_number=delivery_number,
                supplier_id=supplier_name,  # Will be converted to ID by service
                delivery_date=delivery_date,
                employee_name=employee_name,
                items=items,
                notes=notes,
            )

            if result:
                st.success(f"✅ Delivery '{result}' erfolgreich erstellt!")
                st.rerun()
            else:
                st.error("❌ Delivery-Erstellung fehlgeschlagen")
        else:
            st.warning("⚠️ Service-Methode nicht verfügbar oder keine Items")

    except Exception as e:
        logger.error(f"Manual delivery creation failed: {e}")
        st.error(f"❌ Fehler beim Erstellen: {e}")


def show_statistics_tab(delivery_service):
    """Show delivery statistics."""
    st.subheader("📊 Statistiken")

    try:
        # Get basic statistics
        deliveries = (
            delivery_service.get_all_deliveries()
            if hasattr(delivery_service, "get_all_deliveries")
            else []
        )

        if deliveries:
            # Basic metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Gesamt Deliveries", len(deliveries))

            with col2:
                total_items = sum(d.get("items_count", 0) for d in deliveries)
                st.metric("Gesamt Items", total_items)

            with col3:
                # Count unique suppliers
                unique_suppliers = len(
                    set(
                        d.get("supplier_id") for d in deliveries if d.get("supplier_id")
                    )
                )
                st.metric("Lieferanten", unique_suppliers)

            with col4:
                # Latest delivery date
                dates = [
                    d.get("delivery_date") for d in deliveries if d.get("delivery_date")
                ]
                if dates:
                    latest_date = max(dates)
                    st.metric("Letzte Delivery", str(latest_date))

            # Chart placeholder
            st.write("### 📈 Entwicklung")
            st.info("Statistik-Charts werden implementiert...")
        else:
            st.info("Keine Daten für Statistiken verfügbar")

    except Exception as e:
        logger.error(f"Statistics error: {e}")
        st.error(f"Fehler beim Laden der Statistiken: {e}")


def show_documents_tab():
    """Show documents management."""
    st.subheader("📄 Lieferschein-Dokumente")
    st.write(
        "Hier können Sie Lieferscheine und Prüfprotokolle für Deliveries generieren."
    )

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "delivery" not in services:
        st.error("Delivery Service nicht verfügbar")
        return

    delivery_service = services["delivery"]

    try:
        # Delivery selection for document generation
        deliveries_data = (
            delivery_service.get_all_deliveries()
            if hasattr(delivery_service, "get_all_deliveries")
            else []
        )

        if deliveries_data:
            delivery_options = {
                f"{d['delivery_number']} ({d['supplier_id']})": d["delivery_number"]
                for d in deliveries_data
            }
            selected_delivery_display = st.selectbox(
                "Delivery für Dokumenterstellung auswählen:",
                options=list(delivery_options.keys()),
                key="doc_delivery_select",
            )

            if selected_delivery_display:
                selected_delivery_number = delivery_options[selected_delivery_display]

                # Enhanced document generation section
                st.write("### 📄 Dokumentenerstellung")
                st.write(
                    "Integriert Datenbankdaten und erstellt organisierte Ordnerstruktur."
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(
                        "🚀 Vollständige Lieferung erstellen",
                        use_container_width=True,
                        type="primary",
                    ):
                        with st.spinner("Erstelle vollständige Dokumentation..."):
                            try:
                                # FIXED: Use standardized services instead of enhanced_document_service
                                from warehouse.application.services.delivery_workflow_service import DeliveryWorkflowService

                                workflow_service = DeliveryWorkflowService()
                                results = workflow_service.create_delivery_documents(
                                    delivery_number=selected_delivery_number,
                                    open_documents=True,
                                    create_folder=True
                                )

                                if results["success"]:
                                    st.success(
                                        f"✅ Dokumentation erstellt: {len(results['documents_created'])} Dokumente"
                                    )
                                    if results["folder_path"]:
                                        st.info(
                                            f"📁 Ordner erstellt: {results['folder_path']}"
                                        )

                                    # Show created documents
                                    for doc in results["documents_created"]:
                                        st.write(
                                            f"📄 {doc['type']}: `{doc['path'].name}`"
                                        )
                                else:
                                    st.error("❌ Fehler bei der Dokumenterstellung")
                                    for error in results["errors"]:
                                        st.error(f"• {error}")

                            except Exception as e:
                                st.error(f"❌ Fehler: {e}")
                                logger.error(f"Document generation error: {e}")

                with col2:
                    if st.button("📋 Einfacher Bericht", use_container_width=True):
                        st.info("Erstelle einfachen Lieferschein-Bericht...")
                        # Basic report implementation can be added here

                with col3:
                    if st.button("📊 Lieferstatistiken", use_container_width=True):
                        st.info("Zeige Statistiken für diese Lieferung...")
                        # Show statistics for selected delivery
                        selected_delivery = next(
                            (
                                d
                                for d in deliveries_data
                                if d["delivery_number"] == selected_delivery_number
                            ),
                            None,
                        )
                        if selected_delivery:
                            st.write(
                                f"**Lieferung:** {selected_delivery['delivery_number']}"
                            )
                            st.write(
                                f"**Lieferant:** {selected_delivery.get('supplier_id', 'N/A')}"
                            )
                            st.write(
                                f"**Datum:** {selected_delivery.get('delivery_date', 'N/A')}"
                            )
                            st.write(
                                f"**Items:** {selected_delivery.get('items_count', 0)}"
                            )

        else:
            st.info("Keine Deliveries für Dokumenterstellung gefunden")
            st.write("Erstellen Sie zunächst eine Delivery im Tab 'Neu erstellen'.")

    except Exception as e:
        logger.error(f"Documents tab error: {e}")
        st.error(f"Fehler beim Laden des Dokument-Bereichs: {e}")
