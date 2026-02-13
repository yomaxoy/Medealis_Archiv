"""
Delivery Scan Popup - User Presentation Layer
Popup für das Hochladen und Scannen von Lieferscheinen im User GUI.
"""

import streamlit as st
import logging
import os
import tempfile
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Session state keys for delivery document handling
SESSION_KEY_ORIGINAL_EXTRACTION = "original_extraction_data"
SESSION_KEY_UPLOADED_FILE_DATA = "uploaded_delivery_file_data"
SESSION_KEY_UPLOADED_FILE_NAME = "uploaded_delivery_file_name"
SESSION_KEY_EXTRACTION_CONFIRMED = "extraction_confirmed"
SESSION_KEY_EXTRACTED_DELIVERY = "extracted_delivery_data"
SESSION_KEY_SHOW_SCAN_POPUP = "show_scan_popup"
SESSION_KEY_SHOW_EXTRACTION_POPUP = "show_extraction_popup"
SESSION_KEY_ITEMS_TO_REMOVE = "items_to_remove"


@st.dialog("📄 Lieferschein scannen", width="large")
def show_delivery_scan_popup():
    """
    Zeigt das Popup zum Hochladen und Scannen von Lieferscheinen.
    Basiert auf der Admin-Implementierung aus delivery_management_view.py
    """
    st.write("### 📄 Lieferschein PDF hochladen und auswerten")
    st.info(
        "🔄 **OCR → Claude-API → JSON → DB Workflow** - Strukturierte Datenextraktion!"
    )

    # System Status Check
    show_system_status_check()

    st.write("---")

    # File upload section
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_pdf = st.file_uploader(
            "📎 PDF-Datei oder Bild auswählen",
            type=["pdf", "png", "jpg", "jpeg", "tiff"],
            help="Laden Sie eine PDF-Datei oder Bild mit Lieferschein-Daten hoch",
            key="user_scan_pdf_upload",
        )

    with col2:
        if uploaded_pdf:
            if st.button(
                "🤖 OCR + Claude Analyse",
                type="primary",
                use_container_width=True,
                key="user_scan_process_btn",
            ):
                # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR Dokumenten-Upload
                from warehouse.presentation.user.popups.components.storage_warning_dialog import (
                    check_and_show_storage_warning,
                )

                # Zeige Warnung wenn Server nicht verfügbar
                can_continue = check_and_show_storage_warning(
                    compact=True  # Kompakte Warnung
                )

                if not can_continue:
                    st.error(
                        "❌ Dokumenten-Upload abgebrochen - keine Speicher-Option verfügbar"
                    )
                else:
                    # Store uploaded file data in session state for later use
                    uploaded_pdf.seek(0)
                    st.session_state[SESSION_KEY_UPLOADED_FILE_DATA] = uploaded_pdf.read()
                    st.session_state[SESSION_KEY_UPLOADED_FILE_NAME] = uploaded_pdf.name
                    uploaded_pdf.seek(0)  # Reset for processing
                    process_uploaded_delivery_file(uploaded_pdf)

    st.write("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Abbrechen", use_container_width=True, key="user_scan_cancel"):
            st.session_state[SESSION_KEY_SHOW_SCAN_POPUP] = False
            # Cleanup uploaded file data
            _cleanup_uploaded_file_data()
            st.rerun()


def _cleanup_uploaded_file_data() -> None:
    """Bereinigt hochgeladene Datei-Daten aus Session State."""
    cleanup_keys = [SESSION_KEY_UPLOADED_FILE_DATA, SESSION_KEY_UPLOADED_FILE_NAME]
    for key in cleanup_keys:
        if key in st.session_state:
            del st.session_state[key]


def show_system_status_check():
    """Zeigt den System-Status für OCR und Claude API."""
    # API Key Check - use EnvironmentConfig to ensure .env is loaded
    from warehouse.shared.config.environment_config import env_config
    api_key_available = bool(env_config.get("ANTHROPIC_API_KEY"))

    col1, col2 = st.columns(2)

    with col1:
        if api_key_available:
            st.success("✅ Claude API-Key verfügbar")
        else:
            st.error("❌ ANTHROPIC_API_KEY nicht gesetzt!")
            with st.expander("🔧 API Key konfigurieren"):
                st.code('$env:ANTHROPIC_API_KEY="sk-ant-api03-ihr-echter-key"')
                st.write(
                    "Setzen Sie den API-Key in Ihrer Umgebung und starten Sie die App neu."
                )

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


def process_uploaded_delivery_file(uploaded_file):
    """
    Verarbeitet eine hochgeladene Lieferschein-Datei.
    Verwendet den gleichen Workflow wie die Admin-Ansicht.
    """
    progress_bar = st.progress(0)
    status_container = st.container()

    try:
        with status_container:
            st.info("🔍 **Schritt 1/4:** Datei verarbeiten...")
        progress_bar.progress(25)

        # Get processors from session state
        processors = st.session_state.get("processors", {})
        if "document_processing_service" not in processors:
            raise Exception("Document processing service nicht verfügbar")

        document_processing_service = processors["document_processing_service"]

        with status_container:
            st.info("🤖 **Schritt 2/4:** AI-Datenextraktion...")
        progress_bar.progress(50)

        # Read uploaded file data
        uploaded_file.seek(0)  # Reset file pointer
        document_data = uploaded_file.read()

        # Process delivery slip using unified document processing
        result = document_processing_service.process_document(
            document_data=document_data,
            document_type="delivery",
            context={"document_data": document_data, "filename": uploaded_file.name},
        )

        with status_container:
            st.info("✅ **Schritt 3/4:** Daten validieren...")
        progress_bar.progress(75)

        if result:
            # Store result in session state for confirmation popup
            st.session_state[SESSION_KEY_EXTRACTED_DELIVERY] = result

            with status_container:
                st.success("🎉 **Schritt 4/4:** Extraktion erfolgreich!")

                # Show storage success if available
                if result.get("storage", {}).get("success"):
                    storage_path = result["storage"].get("relative_path", "Unbekannt")
                    st.info(f"📁 Lieferschein gespeichert: {storage_path}")

                    # Show normalization info if applicable
                    if result.get("supplier_detection", {}).get(
                        "original_name"
                    ) != result.get("supplier_detection", {}).get("normalized_name"):
                        original = result["supplier_detection"]["original_name"]
                        normalized = result["supplier_detection"]["normalized_name"]
                        st.info(f"🏷️ Lieferant normalisiert: {original} → {normalized}")

            progress_bar.progress(100)

            # Show extraction confirmation popup
            st.session_state[SESSION_KEY_SHOW_EXTRACTION_POPUP] = True
            st.session_state[SESSION_KEY_SHOW_SCAN_POPUP] = False  # Close scan popup
            st.rerun()
        else:
            st.error("❌ Keine Daten extrahiert. Bitte prüfen Sie die Datei.")
            progress_bar.progress(0)

    except Exception as e:
        logger.error(f"File processing failed: {e}")
        st.error(f"❌ Verarbeitung fehlgeschlagen: {e}")
        progress_bar.progress(0)
    finally:
        # Clean up progress indicators after a delay
        import time

        time.sleep(2)
        progress_bar.empty()


@st.dialog("✅ Lieferschein-Daten bestätigen", width="large")
def show_extraction_confirmation_popup(extraction_data: Dict[str, Any]):
    """
    Zeigt ein Bestätigungspopup mit den extrahierten Lieferschein-Daten.
    Ermöglicht Bearbeitung vor dem Speichern.
    """
    st.write("### 📋 Extrahierte Lieferschein-Informationen")

    # Extract data from result - handle both formats
    # Format 1: {structured_data: {...}, storage: {...}}
    # Format 2: {delivery_number: ..., items: [...]} (direkt)
    if "structured_data" in extraction_data:
        delivery_data = extraction_data["structured_data"]
    else:
        delivery_data = extraction_data

    items_data = delivery_data.get("items", [])

    # Store original extraction_data in session state for later use (document saving)
    if SESSION_KEY_ORIGINAL_EXTRACTION not in st.session_state:
        st.session_state[SESSION_KEY_ORIGINAL_EXTRACTION] = extraction_data

    # DEBUG: Log what's in the items
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG: items_data count: {len(items_data)}")
    if items_data:
        logger.info(f"DEBUG: First item keys: {items_data[0].keys()}")
        logger.info(
            f"DEBUG: First item description: {items_data[0].get('description', 'NOT FOUND')}"
        )

    # Delivery information section - editable
    col1, col2 = st.columns(2)
    with col1:
        edited_delivery_number = st.text_input(
            "Lieferscheinnummer:",
            value=delivery_data.get("delivery_number", ""),
            key="user_popup_delivery_num",
        )
        edited_supplier_name = st.text_input(
            "Lieferant:",
            value=delivery_data.get("supplier_name", ""),
            key="user_popup_supplier",
        )
        edited_employee_name = st.text_input(
            "Bearbeiter:",
            value=delivery_data.get("employee_name", "User"),
            key="user_popup_employee",
        )

    with col2:
        # Parse delivery_date - handle string format "DD.MM.YYYY" or date object
        delivery_date_value = delivery_data.get("delivery_date")
        if isinstance(delivery_date_value, str):
            # Try to parse German date format "DD.MM.YYYY"
            try:
                from datetime import datetime

                delivery_date_value = datetime.strptime(
                    delivery_date_value, "%d.%m.%Y"
                ).date()
            except (ValueError, TypeError):
                # Fallback to today
                from datetime import date

                delivery_date_value = date.today()
        elif delivery_date_value is None:
            from datetime import date

            delivery_date_value = date.today()

        edited_delivery_date = st.date_input(
            "Lieferdatum:",
            value=delivery_date_value,
            key="user_popup_date",
        )
        edited_notes = st.text_area(
            "Notizen:",
            value=delivery_data.get("notes", ""),
            key="user_popup_notes",
        )

    st.write("### 📦 Enthaltene Artikel")

    # Initialize items_to_remove in session state
    if SESSION_KEY_ITEMS_TO_REMOVE not in st.session_state:
        st.session_state[SESSION_KEY_ITEMS_TO_REMOVE] = set()

    # Items table section - editable
    if items_data:
        # Header row
        col1, col2, col3, col4, col5, col6 = st.columns([3, 4, 2, 2, 1, 1])
        with col1:
            st.write("**Artikelnummer**")
        with col2:
            st.write("**Chargennummer**")
        with col3:
            st.write("**Anzahl**")
        with col4:
            st.write("**Bestellnummer**")
        with col5:
            st.write("")  # ItemInfo button
        with col6:
            st.write("")  # Remove button

        edited_items = []
        for i, item in enumerate(items_data):
            # Skip if marked for removal
            if i in st.session_state[SESSION_KEY_ITEMS_TO_REMOVE]:
                continue

            col1, col2, col3, col4, col5, col6 = st.columns([3, 4, 2, 2, 1, 1])
            with col1:
                edited_article = st.text_input(
                    "Artikelnummer",
                    value=item.get("article_number", ""),
                    key=f"user_popup_article_{i}",
                    label_visibility="collapsed",
                )
            with col2:
                edited_batch = st.text_input(
                    "Chargennummer",
                    value=item.get("batch_number", ""),
                    key=f"user_popup_batch_{i}",
                    label_visibility="collapsed",
                )
            with col3:
                edited_quantity = st.number_input(
                    "Anzahl",
                    value=item.get("quantity", 1),
                    min_value=1,
                    key=f"user_popup_qty_{i}",
                    label_visibility="collapsed",
                )
            with col4:
                edited_order_number = st.text_input(
                    "Bestellnummer",
                    value=item.get("order_number", ""),
                    key=f"user_popup_order_{i}",
                    label_visibility="collapsed",
                    placeholder="Best.-Nr.",
                )
            with col5:
                if st.button(
                    "📝", key=f"user_popup_iteminfo_{i}", help="ItemInfo bearbeiten"
                ):
                    # Speichere aktuellen Artikel für ItemInfo-Dialog
                    st.session_state.edit_iteminfo_article = edited_article
                    st.session_state.edit_iteminfo_item_data = {
                        "article_number": edited_article,
                        "description": item.get("description", ""),
                        "manufacturer": delivery_data.get("supplier_name", ""),
                    }
                    st.session_state.show_iteminfo_edit_dialog = True
                    st.rerun()
            with col6:
                if st.button("🗑️", key=f"user_popup_remove_{i}", help="Item entfernen"):
                    st.session_state[SESSION_KEY_ITEMS_TO_REMOVE].add(i)
                    st.rerun()

            # Keep all original fields from Claude extraction (like description, storage_location, etc.)
            # but update with edited values
            edited_item = item.copy()  # Preserve all original fields
            edited_item.update(
                {
                    "article_number": edited_article,
                    "batch_number": edited_batch,
                    "quantity": edited_quantity,
                    "order_number": edited_order_number,
                }
            )
            edited_items.append(edited_item)

        # DEBUG: Log edited items
        logger.info(f"DEBUG: edited_items count: {len(edited_items)}")
        if edited_items:
            logger.info(f"DEBUG: First edited item keys: {edited_items[0].keys()}")
            logger.info(
                f"DEBUG: First edited item description: {edited_items[0].get('description', 'NOT FOUND')}"
            )

        # Add new item button
        st.write("---")
        if st.button("➕ Neues Item hinzufügen", key="user_add_new_item"):
            # Add empty item to the list with description field
            items_data.append(
                {
                    "article_number": "",
                    "batch_number": "",
                    "quantity": 1,
                    "order_number": "",
                    "description": "",  # Empty description for manually added items
                }
            )
            st.rerun()

        # Summary
        total_items = len(edited_items)
        total_quantity = sum(item["quantity"] for item in edited_items)
        st.info(
            f"📊 **Zusammenfassung:** {total_items} Items, Gesamtmenge: {total_quantity}"
        )
    else:
        st.warning("Keine Items gefunden")
        # Allow adding first item
        if st.button("➕ Erstes Item hinzufügen", key="user_add_first_item"):
            items_data.append(
                {
                    "article_number": "",
                    "batch_number": "",
                    "quantity": 1,
                    "order_number": "",
                }
            )
            st.rerun()

    st.write("---")

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "✅ Bestätigen und Speichern",
            type="primary",
            use_container_width=True,
            key="user_confirm_extraction",
        ):
            # Update extraction data with edited values
            updated_extraction_data = {
                "delivery_number": edited_delivery_number,
                "supplier_name": edited_supplier_name,
                "delivery_date": edited_delivery_date,
                "employee_name": edited_employee_name,
                "notes": edited_notes if edited_notes else None,
                "items": edited_items,
            }

            # Store confirmed data in session state
            st.session_state[SESSION_KEY_EXTRACTION_CONFIRMED] = updated_extraction_data
            st.session_state.popup_action = "extraction_confirm"
            st.session_state[SESSION_KEY_SHOW_EXTRACTION_POPUP] = False
            # Cleanup session state
            if SESSION_KEY_ITEMS_TO_REMOVE in st.session_state:
                del st.session_state[SESSION_KEY_ITEMS_TO_REMOVE]
            st.rerun()

    with col2:
        if st.button(
            "✏️ Bearbeiten",
            use_container_width=True,
            key="user_edit_extraction",
        ):
            st.info("Bearbeiten Sie die Felder oben und bestätigen Sie dann.")

    with col3:
        if st.button(
            "❌ Abbrechen",
            use_container_width=True,
            key="user_cancel_extraction",
        ):
            st.session_state[SESSION_KEY_SHOW_EXTRACTION_POPUP] = False
            # Cleanup session state
            _cleanup_extraction_session_state()
            st.rerun()


def _cleanup_extraction_session_state() -> None:
    """Bereinigt alle Session State Variablen für Extraktion."""
    cleanup_keys = [
        SESSION_KEY_EXTRACTED_DELIVERY,
        SESSION_KEY_ITEMS_TO_REMOVE,
        SESSION_KEY_ORIGINAL_EXTRACTION,
        SESSION_KEY_UPLOADED_FILE_DATA,
        SESSION_KEY_UPLOADED_FILE_NAME,
    ]
    for key in cleanup_keys:
        if key in st.session_state:
            del st.session_state[key]
