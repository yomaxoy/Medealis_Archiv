"""
Supplier Popups - Admin Presentation Layer
All popup dialogs related to supplier management.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@st.dialog("🏢 Supplier Bestätigung")
def show_supplier_confirmation_popup(supplier_data: Dict[str, Any]):
    """Show supplier confirmation popup with edit functionality."""
    st.write("### 📋 Supplier Informationen")
    
    # Display supplier information for confirmation
    col1, col2 = st.columns(2)
    
    with col1:
        edited_supplier_id = st.text_input(
            "Supplier ID:",
            value=supplier_data.get('supplier_id', ''),
            key="popup_supplier_id"
        )
        edited_name = st.text_input(
            "Name:",
            value=supplier_data.get('name', ''),
            key="popup_supplier_name"
        )
        edited_contact = st.text_input(
            "Ansprechpartner:",
            value=supplier_data.get('contact_person', ''),
            key="popup_supplier_contact"
        )
    
    with col2:
        edited_phone = st.text_input(
            "Telefon:",
            value=supplier_data.get('phone', ''),
            key="popup_supplier_phone"
        )
        edited_email = st.text_input(
            "E-Mail:",
            value=supplier_data.get('email', ''),
            key="popup_supplier_email"
        )
        edited_website = st.text_input(
            "Website:",
            value=supplier_data.get('website', ''),
            key="popup_supplier_website"
        )
    
    # Address and tax number
    edited_address = st.text_area(
        "Adresse:",
        value=supplier_data.get('address', ''),
        key="popup_supplier_address"
    )
    
    col3, col4 = st.columns(2)
    with col3:
        edited_tax_number = st.text_input(
            "Steuernummer:",
            value=supplier_data.get('tax_number', ''),
            key="popup_supplier_tax"
        )
    
    with col4:
        pass  # Empty column for spacing
    
    # Notes
    edited_notes = st.text_area(
        "Notizen:",
        value=supplier_data.get('notes', ''),
        key="popup_supplier_notes"
    )
    
    st.write("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Bestätigen", type="primary", use_container_width=True):
            # Update supplier data with edited values
            updated_supplier = {
                'supplier_id': edited_supplier_id,
                'name': edited_name,
                'contact_person': edited_contact,
                'phone': edited_phone,
                'email': edited_email,
                'website': edited_website,
                'address': edited_address,
                'tax_number': edited_tax_number,
                'notes': edited_notes
            }
            
            # Store confirmed data in session state
            st.session_state.confirmed_supplier = updated_supplier
            st.session_state.popup_action = 'confirm'
            st.rerun()
    
    with col2:
        if st.button("📝 Bearbeiten", use_container_width=True):
            st.info("Sie können die Daten direkt hier bearbeiten und dann bestätigen.")
    
    with col3:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📝 Supplier bearbeiten")
def show_supplier_edit_popup(supplier_data: Dict[str, Any]):
    """Show supplier edit popup."""
    st.write("### ✏️ Supplier bearbeiten")
    
    # Basic supplier info
    col1, col2 = st.columns(2)
    
    with col1:
        supplier_id = st.text_input(
            "Supplier ID:",
            value=supplier_data.get('supplier_id', ''),
            disabled=True,  # ID shouldn't be editable
            help="Supplier ID kann nicht geändert werden"
        )
        name = st.text_input(
            "Name:",
            value=supplier_data.get('name', '')
        )
        contact_person = st.text_input(
            "Ansprechpartner:",
            value=supplier_data.get('contact_person', '')
        )
    
    with col2:
        phone = st.text_input(
            "Telefon:",
            value=supplier_data.get('phone', '')
        )
        email = st.text_input(
            "E-Mail:",
            value=supplier_data.get('email', '')
        )
        website = st.text_input(
            "Website:",
            value=supplier_data.get('website', '')
        )
    
    # Address
    address = st.text_area(
        "Adresse:",
        value=supplier_data.get('address', '')
    )
    
    col3, col4 = st.columns(2)
    with col3:
        tax_number = st.text_input(
            "Steuernummer:",
            value=supplier_data.get('tax_number', '')
        )
    
    # Notes
    notes = st.text_area(
        "Notizen:",
        value=supplier_data.get('notes', '')
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            updated_data = {
                'supplier_id': supplier_id,
                'name': name,
                'contact_person': contact_person,
                'phone': phone,
                'email': email,
                'website': website,
                'address': address,
                'tax_number': tax_number,
                'notes': notes
            }
            st.session_state.edit_supplier_result = updated_data
            st.session_state.popup_action = 'edit_save'
            st.rerun()
    
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("🗑️ Supplier löschen")
def show_supplier_delete_popup(supplier_data: Dict[str, Any]):
    """Show supplier delete confirmation popup."""
    st.write("### ⚠️ Supplier wirklich löschen?")
    
    # Show supplier details
    st.error(f"**Supplier ID:** {supplier_data.get('supplier_id', 'N/A')}")
    st.write(f"**Name:** {supplier_data.get('name', 'N/A')}")
    
    if supplier_data.get('contact_person'):
        st.write(f"**Ansprechpartner:** {supplier_data.get('contact_person')}")
    
    if supplier_data.get('phone'):
        st.write(f"**Telefon:** {supplier_data.get('phone')}")
    
    if supplier_data.get('email'):
        st.write(f"**E-Mail:** {supplier_data.get('email')}")
    
    st.warning("⚠️ **Diese Aktion kann nicht rückgängig gemacht werden!**")
    st.write("Alle Referenzen auf diesen Supplier in Deliveries bleiben bestehen, " +
             "aber der Supplier kann nicht mehr bearbeitet werden.")
    
    # Check for existing deliveries
    try:
        services = st.session_state.get('services', {})
        if 'delivery' in services:
            delivery_service = services['delivery']
            if hasattr(delivery_service, 'get_all_deliveries'):
                deliveries = delivery_service.get_all_deliveries()
                supplier_deliveries = [
                    d for d in deliveries 
                    if d.get('supplier_id') == supplier_data.get('supplier_id')
                ]
                
                if supplier_deliveries:
                    st.warning(f"⚠️ **{len(supplier_deliveries)} Deliveries** sind mit diesem Supplier verknüpft!")
                    
                    with st.expander("📋 Verknüpfte Deliveries anzeigen"):
                        for delivery in supplier_deliveries:
                            st.write(f"- {delivery.get('delivery_number', 'N/A')} ({delivery.get('delivery_date', 'N/A')})")
    except Exception as e:
        logger.warning(f"Could not check delivery references: {e}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Endgültig löschen", type="primary", use_container_width=True):
            st.session_state.delete_supplier_confirmed = supplier_data
            st.session_state.popup_action = 'delete_confirm'
            st.rerun()
    
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📄 Supplier Details")
def show_supplier_details_popup(supplier_data: Dict[str, Any]):
    """Show detailed supplier information popup."""
    st.write(f"### 📋 {supplier_data.get('name', 'Supplier Details')}")
    
    # Basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Grunddaten:**")
        st.write(f"**ID:** {supplier_data.get('supplier_id', 'N/A')}")
        st.write(f"**Name:** {supplier_data.get('name', 'N/A')}")
        
        if supplier_data.get('contact_person'):
            st.write(f"**Ansprechpartner:** {supplier_data.get('contact_person')}")
        
        if supplier_data.get('created_at'):
            st.write(f"**Erstellt am:** {supplier_data.get('created_at')}")
    
    with col2:
        st.write("**Kontaktdaten:**")
        
        if supplier_data.get('phone'):
            st.write(f"**Telefon:** {supplier_data.get('phone')}")
        
        if supplier_data.get('email'):
            st.write(f"**E-Mail:** {supplier_data.get('email')}")
        
        if supplier_data.get('website'):
            st.write(f"**Website:** {supplier_data.get('website')}")
    
    # Address
    if supplier_data.get('address'):
        st.write("**Adresse:**")
        st.text(supplier_data.get('address'))
    
    # Tax information
    if supplier_data.get('tax_number'):
        st.write(f"**Steuernummer:** {supplier_data.get('tax_number')}")
    
    # Notes
    if supplier_data.get('notes'):
        st.write("**Notizen:**")
        st.text_area("", value=supplier_data.get('notes'), disabled=True, height=100)
    
    # Statistics
    try:
        services = st.session_state.get('services', {})
        if 'delivery' in services:
            delivery_service = services['delivery']
            if hasattr(delivery_service, 'get_all_deliveries'):
                deliveries = delivery_service.get_all_deliveries()
                supplier_deliveries = [
                    d for d in deliveries 
                    if d.get('supplier_id') == supplier_data.get('supplier_id')
                ]
                
                st.write("---")
                st.write("**Statistiken:**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Deliveries", len(supplier_deliveries))
                
                with col2:
                    total_items = sum(d.get('items_count', 0) for d in supplier_deliveries)
                    st.metric("Gesamt Items", total_items)
                
                with col3:
                    if supplier_deliveries:
                        latest_delivery = max(supplier_deliveries, key=lambda x: x.get('delivery_date', ''))
                        st.metric("Letzte Delivery", str(latest_delivery.get('delivery_date', 'N/A')))
                
    except Exception as e:
        logger.warning(f"Could not load supplier statistics: {e}")
    
    # Close button
    if st.button("Schließen", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()


@st.dialog("📊 Supplier Statistiken")
def show_supplier_statistics_popup(supplier_data: Dict[str, Any]):
    """Show detailed supplier statistics."""
    st.write(f"### 📊 Statistiken für {supplier_data.get('name', 'Supplier')}")
    
    try:
        services = st.session_state.get('services', {})
        if 'delivery' not in services:
            st.error("Delivery Service nicht verfügbar")
            return
        
        delivery_service = services['delivery']
        if not hasattr(delivery_service, 'get_all_deliveries'):
            st.error("Delivery Service Methode nicht verfügbar")
            return
        
        # Get all deliveries for this supplier
        all_deliveries = delivery_service.get_all_deliveries()
        supplier_deliveries = [
            d for d in all_deliveries 
            if d.get('supplier_id') == supplier_data.get('supplier_id')
        ]
        
        if not supplier_deliveries:
            st.info("Keine Deliveries für diesen Supplier gefunden")
            return
        
        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gesamt Deliveries", len(supplier_deliveries))
        
        with col2:
            total_items = sum(d.get('items_count', 0) for d in supplier_deliveries)
            st.metric("Gesamt Items", total_items)
        
        with col3:
            # Calculate average items per delivery
            avg_items = total_items / len(supplier_deliveries) if supplier_deliveries else 0
            st.metric("⌀ Items/Delivery", f"{avg_items:.1f}")
        
        with col4:
            # Latest delivery date
            latest_date = max(d.get('delivery_date') for d in supplier_deliveries if d.get('delivery_date'))
            st.metric("Letzte Delivery", str(latest_date))
        
        # Timeline
        st.write("### 📈 Delivery Timeline")
        
        # Sort deliveries by date
        sorted_deliveries = sorted(
            supplier_deliveries,
            key=lambda x: x.get('delivery_date', ''),
            reverse=True
        )
        
        # Show recent deliveries
        for delivery in sorted_deliveries[:10]:  # Last 10 deliveries
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.write(delivery.get('delivery_number', 'N/A'))
            with col2:
                st.write(str(delivery.get('delivery_date', 'N/A')))
            with col3:
                status = delivery.get('status', 'N/A')
                if hasattr(status, 'value'):
                    status = status.value
                st.write(str(status))
            with col4:
                st.write(f"{delivery.get('items_count', 0)} Items")
        
        if len(supplier_deliveries) > 10:
            st.info(f"... und {len(supplier_deliveries) - 10} weitere Deliveries")
    
    except Exception as e:
        logger.error(f"Error loading supplier statistics: {e}")
        st.error(f"Fehler beim Laden der Statistiken: {e}")
    
    # Close button
    if st.button("Schließen", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()