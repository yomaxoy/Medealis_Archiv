"""
Item Popups - Admin Presentation Layer
All popup dialogs related to item management.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

from warehouse.presentation.shared.components import render_open_folder_button

logger = logging.getLogger(__name__)


@st.dialog("📦 Item Bestätigung")
def show_item_confirmation_popup(item_data: Dict[str, Any]):
    """Show item confirmation popup with edit functionality."""
    st.write("### 📋 Item Informationen")
    
    # Item information section - editable
    col1, col2 = st.columns(2)
    
    with col1:
        edited_delivery_number = st.text_input(
            "Delivery Number:",
            value=item_data.get('delivery_number', ''),
            key="popup_item_delivery"
        )
        edited_article_number = st.text_input(
            "Article Number:",
            value=item_data.get('article_number', ''),
            key="popup_item_article"
        )
        edited_batch_number = st.text_input(
            "Batch Number:",
            value=item_data.get('batch_number', ''),
            key="popup_item_batch"
        )
    
    with col2:
        edited_quantity = st.number_input(
            "Quantity:",
            value=item_data.get('quantity', 1),
            min_value=1,
            key="popup_item_quantity"
        )
        edited_employee_name = st.text_input(
            "Employee Name:",
            value=item_data.get('employee_name', ''),
            key="popup_item_employee"
        )
        edited_designation = st.text_input(
            "Bezeichnung:",
            value=item_data.get('designation', ''),
            key="popup_item_designation"
        )
    
    # Additional fields
    edited_storage_location = st.text_input(
        "Lagerplatz:",
        value=item_data.get('storage_location', ''),
        key="popup_item_storage"
    )
    
    edited_notes = st.text_area(
        "Notizen:",
        value=item_data.get('notes', ''),
        key="popup_item_notes"
    )
    
    st.write("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Bestätigen", type="primary", use_container_width=True):
            # Update item data with edited values
            updated_item = {
                'delivery_number': edited_delivery_number,
                'article_number': edited_article_number,
                'batch_number': edited_batch_number,
                'quantity': edited_quantity,
                'employee_name': edited_employee_name,
                'designation': edited_designation,
                'storage_location': edited_storage_location,
                'notes': edited_notes
            }
            
            # Store confirmed data in session state
            st.session_state.confirmed_item = updated_item
            st.session_state.popup_action = 'confirm'
            st.rerun()
    
    with col2:
        if st.button("📝 Bearbeiten", use_container_width=True):
            st.info("Sie können die Daten direkt hier bearbeiten und dann bestätigen.")
    
    with col3:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📝 Item bearbeiten")
def show_item_edit_popup(item_data: Dict[str, Any]):
    """Show item edit popup."""
    st.write("### ✏️ Item bearbeiten")

    # Artikelordner-Button oben rechts
    col_header1, col_header2 = st.columns([3, 1])
    with col_header2:
        # Prüfe ob alle benötigten Felder vorhanden sind
        if all(key in item_data for key in ['article_number', 'batch_number', 'delivery_number', 'supplier_name', 'manufacturer']):
            render_open_folder_button(item_data, key_suffix="edit_popup", button_type="secondary")
        elif item_data.get('article_number') and item_data.get('batch_number') and item_data.get('delivery_number'):
            st.caption("📁 Ordner-Button benötigt Lieferanten- und Herstellerdaten")

    # Basic item info
    col1, col2 = st.columns(2)
    
    with col1:
        delivery_number = st.text_input(
            "Delivery Number:",
            value=item_data.get('delivery_number', ''),
            disabled=True,
            help="Delivery Number kann nicht geändert werden"
        )
        article_number = st.text_input(
            "Article Number:",
            value=item_data.get('article_number', ''),
            disabled=True,
            help="Article Number kann nicht geändert werden"
        )
        batch_number = st.text_input(
            "Batch Number:",
            value=item_data.get('batch_number', ''),
            disabled=True,
            help="Batch Number kann nicht geändert werden"
        )
    
    with col2:
        quantity = st.number_input(
            "Quantity:",
            value=item_data.get('quantity', 1),
            min_value=1
        )
        employee_name = st.text_input(
            "Employee Name:",
            value=item_data.get('employee_name', '')
        )
        status = st.selectbox(
            "Status:",
            options=["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"],
            index=0 if not item_data.get('status') else 
                  ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"].index(item_data.get('status', 'PENDING'))
        )
    
    # Extended information
    with st.expander("📝 Erweiterte Informationen", expanded=False):
        col3, col4 = st.columns(2)
        
        with col3:
            designation = st.text_input(
                "Bezeichnung:",
                value=item_data.get('designation', '')
            )
            revision_number = st.text_input(
                "Revision Number:",
                value=str(item_data.get('revision_number', '')) if item_data.get('revision_number') else ''
            )
            drawing_reference = st.text_input(
                "Drawing Reference:",
                value=item_data.get('drawing_reference', '')
            )
        
        with col4:
            storage_location = st.text_input(
                "Lagerplatz:",
                value=item_data.get('storage_location', '')
            )
            manufacturer = st.text_input(
                "Hersteller:",
                value=item_data.get('manufacturer', '')
            )
            material_specification = st.text_input(
                "Material Specification:",
                value=item_data.get('material_specification', '')
            )
    
    # Notes and description
    description = st.text_area(
        "Beschreibung:",
        value=item_data.get('description', '')
    )
    
    notes = st.text_area(
        "Notizen:",
        value=item_data.get('notes', '')
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            updated_data = {
                'delivery_number': delivery_number,
                'article_number': article_number,
                'batch_number': batch_number,
                'quantity': quantity,
                'employee_name': employee_name,
                'status': status,
                'designation': designation,
                'revision_number': revision_number if revision_number else None,
                'drawing_reference': drawing_reference,
                'storage_location': storage_location,
                'manufacturer': manufacturer,
                'material_specification': material_specification,
                'description': description,
                'notes': notes
            }
            st.session_state.edit_item_result = updated_data
            st.session_state.popup_action = 'edit_save'
            st.rerun()
    
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("🗑️ Item löschen")
def show_item_delete_popup(item_data: Dict[str, Any]):
    """Show item delete confirmation popup."""
    st.write("### ⚠️ Item wirklich löschen?")
    
    # Show item details
    st.error(f"**Article Number:** {item_data.get('article_number', 'N/A')}")
    st.write(f"**Batch Number:** {item_data.get('batch_number', 'N/A')}")
    st.write(f"**Delivery Number:** {item_data.get('delivery_number', 'N/A')}")
    st.write(f"**Quantity:** {item_data.get('quantity', 'N/A')}")
    
    if item_data.get('designation'):
        st.write(f"**Bezeichnung:** {item_data.get('designation')}")
    
    if item_data.get('storage_location'):
        st.write(f"**Lagerplatz:** {item_data.get('storage_location')}")
    
    st.warning("⚠️ **Diese Aktion kann nicht rückgängig gemacht werden!**")
    st.write("Das Item wird vollständig aus der Datenbank entfernt.")
    
    # Check for dependencies
    st.info("💡 **Hinweis:** Prüfen Sie ob das Item in anderen Prozessen verwendet wird.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Endgültig löschen", type="primary", use_container_width=True):
            st.session_state.delete_item_confirmed = item_data
            st.session_state.popup_action = 'delete_confirm'
            st.rerun()
    
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📄 Item Details")
def show_item_details_popup(item_data: Dict[str, Any]):
    """Show detailed item information popup."""
    st.write(f"### 📦 {item_data.get('article_number', 'Item Details')}")
    
    # Basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Grunddaten:**")
        st.write(f"**Article Number:** {item_data.get('article_number', 'N/A')}")
        st.write(f"**Batch Number:** {item_data.get('batch_number', 'N/A')}")
        st.write(f"**Delivery Number:** {item_data.get('delivery_number', 'N/A')}")
        st.write(f"**Quantity:** {item_data.get('quantity', 'N/A')}")
        
        if item_data.get('designation'):
            st.write(f"**Bezeichnung:** {item_data.get('designation')}")
    
    with col2:
        st.write("**Status & Bearbeitung:**")
        
        status = item_data.get('status', 'N/A')
        if status in ['COMPLETED', 'DELIVERED']:
            st.success(f"**Status:** {status}")
        elif status in ['PENDING', 'IN_PROGRESS']:
            st.warning(f"**Status:** {status}")
        elif status == 'FAILED':
            st.error(f"**Status:** {status}")
        else:
            st.info(f"**Status:** {status}")
        
        if item_data.get('employee_name'):
            st.write(f"**Bearbeiter:** {item_data.get('employee_name')}")
        
        if item_data.get('created_at'):
            st.write(f"**Erstellt am:** {item_data.get('created_at')}")
    
    # Technical details
    technical_fields = [
        ('revision_number', 'Revision Number'),
        ('drawing_reference', 'Drawing Reference'),
        ('storage_location', 'Lagerplatz'),
        ('manufacturer', 'Hersteller'),
        ('material_specification', 'Material Specification')
    ]
    
    technical_data = [(field, label) for field, label in technical_fields if item_data.get(field)]
    
    if technical_data:
        st.write("**Technische Daten:**")
        for field, label in technical_data:
            st.write(f"**{label}:** {item_data.get(field)}")
    
    # Description
    if item_data.get('description'):
        st.write("**Beschreibung:**")
        st.text_area("", value=item_data.get('description'), disabled=True, height=80)
    
    # Notes
    if item_data.get('notes'):
        st.write("**Notizen:**")
        st.text_area("", value=item_data.get('notes'), disabled=True, height=80)
    
    # Related delivery information
    try:
        services = st.session_state.get('services', {})
        if 'delivery' in services:
            delivery_service = services['delivery']
            if hasattr(delivery_service, 'get_delivery'):
                delivery = delivery_service.get_delivery(item_data.get('delivery_number'))
                if delivery:
                    st.write("---")
                    st.write("**Lieferung Information:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Supplier:** {delivery.get('supplier_id', 'N/A')}")
                    with col2:
                        st.write(f"**Delivery Date:** {delivery.get('delivery_date', 'N/A')}")
                    with col3:
                        delivery_status = delivery.get('status', 'N/A')
                        st.write(f"**Delivery Status:** {delivery_status}")
    
    except Exception as e:
        logger.warning(f"Could not load delivery information: {e}")
    
    # Close button
    if st.button("Schließen", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()


@st.dialog("🔍 Batch Rückverfolgung")
def show_batch_tracking_popup(item_data: Dict[str, Any]):
    """Show batch tracking information."""
    st.write(f"### 🔍 Batch Rückverfolgung: {item_data.get('batch_number', 'N/A')}")
    
    try:
        # Find all items with same batch number
        services = st.session_state.get('services', {})
        if 'item' not in services:
            st.error("Item Service nicht verfügbar")
            return
        
        item_service = services['item']
        if not hasattr(item_service, 'get_all_items'):
            st.error("Item Service Methode nicht verfügbar")
            return
        
        batch_number = item_data.get('batch_number')
        if not batch_number:
            st.error("Keine Batch Number verfügbar")
            return
        
        # Get all items with same batch
        all_items = item_service.get_all_items()
        batch_items = [
            item for item in all_items
            if item.get('batch_number') == batch_number
        ]
        
        if not batch_items:
            st.info("Keine anderen Items mit dieser Batch Number gefunden")
            return
        
        st.write(f"**{len(batch_items)} Items** gefunden mit Batch Number: `{batch_number}`")
        
        # Show batch items
        for i, batch_item in enumerate(batch_items):
            with st.expander(f"Item {i+1}: {batch_item.get('article_number', 'N/A')}", expanded=(i == 0)):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Article:** {batch_item.get('article_number', 'N/A')}")
                    st.write(f"**Delivery:** {batch_item.get('delivery_number', 'N/A')}")
                    st.write(f"**Quantity:** {batch_item.get('quantity', 'N/A')}")
                
                with col2:
                    status = batch_item.get('status', 'N/A')
                    st.write(f"**Status:** {status}")
                    st.write(f"**Employee:** {batch_item.get('employee_name', 'N/A')}")
                    if batch_item.get('storage_location'):
                        st.write(f"**Storage:** {batch_item.get('storage_location')}")
                
                with col3:
                    if batch_item.get('created_at'):
                        st.write(f"**Created:** {batch_item.get('created_at')}")
                    if batch_item.get('updated_at'):
                        st.write(f"**Updated:** {batch_item.get('updated_at')}")
        
        # Summary statistics
        st.write("### 📊 Batch Statistiken")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_quantity = sum(item.get('quantity', 0) for item in batch_items)
            st.metric("Gesamt Menge", total_quantity)
        
        with col2:
            unique_articles = len(set(item.get('article_number') for item in batch_items if item.get('article_number')))
            st.metric("Unique Articles", unique_articles)
        
        with col3:
            unique_deliveries = len(set(item.get('delivery_number') for item in batch_items if item.get('delivery_number')))
            st.metric("Deliveries", unique_deliveries)
        
        with col4:
            completed_items = len([item for item in batch_items if item.get('status') == 'COMPLETED'])
            st.metric("Completed", completed_items)
    
    except Exception as e:
        logger.error(f"Error in batch tracking: {e}")
        st.error(f"Fehler bei der Batch-Rückverfolgung: {e}")
    
    # Close button
    if st.button("Schließen", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()