"""
Delivery Popups - Admin Presentation Layer
All popup dialogs related to delivery management.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def show_delivery_confirmation_popup(delivery_data: Dict[str, Any], items_data: List[Dict[str, Any]]):
    """Show delivery confirmation popup with edit functionality."""
    st.write("### 📋 Lieferschein Informationen")
    
    # Delivery information section - editable
    col1, col2 = st.columns(2)
    with col1:
        edited_delivery_number = st.text_input("Lieferscheinnummer:", value=delivery_data['delivery_number'], key="popup_delivery_num")
        edited_supplier_id = st.text_input("Lieferant:", value=delivery_data['supplier_id'], key="popup_supplier")
        edited_employee_name = st.text_input("Bearbeiter:", value=delivery_data['employee_name'], key="popup_employee")
    
    with col2:
        edited_delivery_date = st.date_input("Lieferdatum:", value=delivery_data['delivery_date'], key="popup_date")
        edited_notes = st.text_area("Notizen:", value=delivery_data.get('notes', ''), key="popup_notes")
    
    st.write("### 📦 Enthaltene Artikel")
    
    # Items table section - editable
    if items_data:
        # Header row for better clarity
        col1, col2, col3, col4, col5 = st.columns([3, 4, 2, 2, 1])
        with col1:
            st.write("**Artikelnummer**")
        with col2:
            st.write("**Chargennummer**")
        with col3:
            st.write("**Anzahl**")
        with col4:
            st.write("**Bestellnummer**")
        with col5:
            st.write("")  # Remove column
        
        edited_items = []
        for i, item in enumerate(items_data):
            col1, col2, col3, col4, col5 = st.columns([3, 4, 2, 2, 1])
            with col1:
                edited_article = st.text_input("Artikelnummer", value=item['article_number'], key=f"popup_article_{i}", label_visibility="collapsed")
            with col2:
                edited_batch = st.text_input("Chargennummer", value=item['batch_number'], key=f"popup_batch_{i}", label_visibility="collapsed")
            with col3:
                edited_quantity = st.number_input("Anzahl", value=item['quantity'], min_value=1, key=f"popup_qty_{i}", label_visibility="collapsed")
            with col4:
                # Get order_number from item, fallback to empty string
                item_order_number = item.get('order_number', '') or ''
                edited_order_number = st.text_input("Bestellnummer", value=item_order_number, key=f"popup_order_{i}", label_visibility="collapsed", placeholder="Best.-Nr.")
            with col5:
                if st.button("🗑️", key=f"popup_remove_{i}", help="Item entfernen"):
                    continue  # Skip this item
            
            edited_items.append({
                'article_number': edited_article,
                'batch_number': edited_batch, 
                'quantity': edited_quantity,
                'order_number': edited_order_number
            })
        
        items_data = edited_items
        
        # Summary
        total_items = len(items_data)
        total_quantity = sum(item['quantity'] for item in items_data)
        st.info(f"📊 **Zusammenfassung:** {total_items} Items, Gesamtmenge: {total_quantity}")
    else:
        st.warning("Keine Items gefunden")
    
    st.write("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Bestätigen", type="primary", use_container_width=True):
            # Update delivery data with edited values
            updated_delivery = {
                'delivery_number': edited_delivery_number,
                'supplier_id': edited_supplier_id,
                'delivery_date': edited_delivery_date,
                'employee_name': edited_employee_name,
                'notes': edited_notes if edited_notes else None
            }
            
            # Store confirmed data in session state
            st.session_state.confirmed_delivery = updated_delivery
            st.session_state.confirmed_items = items_data
            st.session_state.popup_action = 'confirm'
            st.rerun()
    
    with col2:
        if st.button("📝 Bearbeiten", use_container_width=True):
            st.info("Sie können die Daten direkt hier bearbeiten und dann bestätigen.")
    
    with col3:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📝 Lieferung bearbeiten")
def show_delivery_edit_popup(delivery_data: Dict[str, Any], items_data: Optional[List[Dict[str, Any]]] = None):
    """Show delivery edit popup."""
    st.write("### ✏️ Lieferung bearbeiten")
    
    # Basic delivery info
    delivery_number = st.text_input("Lieferscheinnummer:", value=delivery_data.get('delivery_number', ''))
    supplier_name = st.text_input("Lieferant:", value=delivery_data.get('supplier_name', ''))
    
    col1, col2 = st.columns(2)
    with col1:
        delivery_date = st.date_input("Lieferdatum:", value=delivery_data.get('delivery_date'))
    with col2:
        employee_name = st.text_input("Bearbeiter:", value=delivery_data.get('employee_name', ''))
    
    notes = st.text_area("Notizen:", value=delivery_data.get('notes', ''))
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            updated_data = {
                'delivery_number': delivery_number,
                'supplier_name': supplier_name,
                'delivery_date': delivery_date,
                'employee_name': employee_name,
                'notes': notes
            }
            st.session_state.edit_delivery_result = updated_data
            st.session_state.popup_action = 'edit_save'
            st.rerun()
    
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("🗑️ Lieferung löschen")
def show_delivery_delete_popup(delivery_data: Dict[str, Any]):
    """Show delivery delete confirmation popup."""
    st.write("### ⚠️ Lieferung wirklich löschen?")
    
    st.error(f"**Lieferscheinnummer:** {delivery_data.get('delivery_number', 'N/A')}")
    st.write(f"**Lieferant:** {delivery_data.get('supplier_name', 'N/A')}")
    st.write(f"**Datum:** {delivery_data.get('delivery_date', 'N/A')}")
    
    st.warning("⚠️ **Diese Aktion kann nicht rückgängig gemacht werden!**")
    st.write("Alle zugehörigen Items werden ebenfalls gelöscht.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Endgültig löschen", type="primary", use_container_width=True):
            st.session_state.delete_delivery_confirmed = delivery_data
            st.session_state.popup_action = 'delete_confirm'
            st.rerun()
    
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📄 Lieferschein scannen")
def show_scan_delivery_slip_popup():
    """Show delivery slip scanning popup."""
    st.write("### 📷 Lieferschein-Datei hochladen")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Wählen Sie eine Datei aus:",
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'docx'],
        help="Unterstützte Formate: PDF, Bilder (PNG, JPG, TIFF), DOCX"
    )
    
    if uploaded_file:
        st.success(f"✅ Datei ausgewählt: {uploaded_file.name}")
        
        # Processing options
        st.write("### 🔧 Verarbeitungsoptionen")
        
        col1, col2 = st.columns(2)
        with col1:
            ocr_language = st.selectbox(
                "OCR Sprache:",
                options=['deu', 'eng', 'deu+eng'],
                index=0,
                help="Deutsche OCR für beste Ergebnisse"
            )
        
        with col2:
            ai_extraction = st.checkbox(
                "AI-basierte Datenextraktion",
                value=True,
                help="Claude API für strukturierte Datenextraktion verwenden"
            )
        
        quality_enhancement = st.checkbox(
            "Bildqualität verbessern",
            value=True,
            help="Optimiert OCR-Ergebnisse bei schlechter Bildqualität"
        )
        
        # Process button
        if st.button("🚀 Verarbeiten", type="primary", use_container_width=True):
            st.session_state.scan_file_to_process = uploaded_file
            st.session_state.scan_options = {
                'ocr_language': ocr_language,
                'ai_extraction': ai_extraction,
                'quality_enhancement': quality_enhancement
            }
            st.session_state.popup_action = 'scan_process'
            st.rerun()
    
    # Cancel button
    if st.button("❌ Abbrechen", use_container_width=True):
        st.session_state.popup_action = 'cancel'
        st.rerun()


@st.dialog("✅ Erfolgreich")
def show_delivery_success_popup(message: str = "Vorgang erfolgreich abgeschlossen!"):
    """Show success popup for delivery operations."""
    st.success(f"✅ {message}")
    
    if st.button("OK", type="primary", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()


@st.dialog("❌ Fehler")
def show_delivery_error_popup(error_message: str = "Ein Fehler ist aufgetreten!"):
    """Show error popup for delivery operations."""
    st.error(f"❌ {error_message}")

    if st.button("OK", type="primary", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()


@st.dialog("📄 Datenextraktion erfolgreich")
def show_extraction_confirmation_popup(extraction_result: Dict[str, Any]):
    """Show extraction confirmation popup with extracted data."""
    st.write("### ✅ Datenextraktion abgeschlossen")

    if extraction_result:
        # Show extracted delivery information
        st.write("#### 📋 Extrahierte Lieferschein-Daten")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Lieferscheinnummer:** {extraction_result.get('delivery_number', 'Nicht gefunden')}")
            st.info(f"**Lieferant:** {extraction_result.get('supplier_name', 'Nicht gefunden')}")

        with col2:
            st.info(f"**Datum:** {extraction_result.get('delivery_date', 'Nicht gefunden')}")
            st.info(f"**Bearbeiter:** {extraction_result.get('employee_name', 'Nicht gefunden')}")

        # Show extracted items if available
        if 'items' in extraction_result and extraction_result['items']:
            st.write("#### 📦 Extrahierte Artikel")

            for i, item in enumerate(extraction_result['items']):
                with st.expander(f"Artikel {i+1}: {item.get('article_number', 'N/A')}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Artikel:** {item.get('article_number', 'N/A')}")
                        st.write(f"**Menge:** {item.get('quantity', 'N/A')}")
                    with col2:
                        st.write(f"**Charge:** {item.get('batch_number', 'N/A')}")
                        st.write(f"**Bestellung:** {item.get('order_number', 'N/A')}")
                    with col3:
                        if item.get('expiry_date'):
                            st.write(f"**Ablaufdatum:** {item.get('expiry_date', 'N/A')}")
                        if item.get('storage_location'):
                            st.write(f"**Lagerplatz:** {item.get('storage_location', 'N/A')}")

            # Summary
            total_items = len(extraction_result['items'])
            total_quantity = sum(int(item.get('quantity', 0) or 0) for item in extraction_result['items'])
            st.success(f"📊 **Zusammenfassung:** {total_items} Artikel, Gesamtmenge: {total_quantity}")

        else:
            st.warning("⚠️ Keine Artikel-Informationen extrahiert")

        # Show confidence/quality info if available
        if 'confidence' in extraction_result:
            confidence = extraction_result['confidence']
            if confidence >= 0.8:
                st.success(f"🎯 **Extraktion Qualität:** Hoch ({confidence:.1%})")
            elif confidence >= 0.6:
                st.warning(f"⚠️ **Extraktion Qualität:** Mittel ({confidence:.1%})")
            else:
                st.error(f"⚠️ **Extraktion Qualität:** Niedrig ({confidence:.1%})")

        # Show raw data option
        with st.expander("🔍 Rohdaten anzeigen"):
            st.json(extraction_result)

        st.write("---")

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Daten übernehmen", type="primary", use_container_width=True):
                # Structure data like streamlit_app.py does before saving
                final_delivery_data = {
                    'delivery_number': extraction_result.get('delivery_number', '').strip(),
                    'supplier_name': extraction_result.get('supplier_name', '').strip(),
                    'supplier_id': extraction_result.get('supplier_id', '').strip() or extraction_result.get('supplier_name', '').strip(),
                    'delivery_date': str(extraction_result.get('delivery_date', '')),
                    'employee_name': extraction_result.get('employee_name', '').strip() or "Claude-Import",
                    'order_number': extraction_result.get('order_number', '').strip() or '',
                    'notes': extraction_result.get('notes', '').strip() or "Importiert via Claude API",
                    'items': extraction_result.get('items', [])  # Keep items as-is
                }

                st.session_state.extraction_confirmed = final_delivery_data
                st.session_state.popup_action = 'extraction_confirm'
                st.rerun()

        with col2:
            if st.button("📝 Bearbeiten", use_container_width=True):
                st.session_state.extraction_to_edit = extraction_result
                st.session_state.popup_action = 'extraction_edit'
                st.rerun()

        with col3:
            if st.button("❌ Verwerfen", use_container_width=True):
                st.session_state.popup_action = 'extraction_discard'
                st.rerun()

    else:
        st.error("❌ Keine Daten extrahiert")

        if st.button("OK", type="primary", use_container_width=True):
            st.session_state.popup_action = 'close'
            st.rerun()