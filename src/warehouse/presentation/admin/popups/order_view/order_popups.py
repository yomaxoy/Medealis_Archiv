"""
Order Popups - Admin Presentation Layer
Order management popup dialogs with CRUD operations.
"""

import streamlit as st
import logging
from datetime import date, datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@st.dialog("📝 Order bearbeiten")
def show_order_edit_popup(order_data: Dict[str, Any]):
    """Show order edit popup with pre-filled data."""

    # Pre-filled order information - editable
    col1, col2 = st.columns(2)
    with col1:
        edited_order_number = st.text_input("Order Number:", value=order_data['order_number'], key="edit_order_num", disabled=True)
        edited_supplier_id = st.text_input("Supplier ID:", value=order_data['supplier_id'], key="edit_order_sup")
        edited_employee_name = st.text_input("Bearbeiter:", value=order_data['employee_name'], key="edit_order_emp")

    with col2:
        edited_order_date = st.date_input("Order Date:", value=order_data['order_date'], key="edit_order_date")
        edited_expected_delivery_date = st.date_input("Expected Delivery:", value=order_data['expected_delivery_date'], key="edit_order_exp_date")
        edited_notes = st.text_area("Notizen:", value=order_data.get('notes', ''), key="edit_order_notes")

    st.write("---")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Änderungen speichern", type="primary", use_container_width=True):
            updated_order = {
                'order_number': order_data['order_number'],  # Keep original
                'supplier_id': edited_supplier_id,
                'order_date': edited_order_date,
                'expected_delivery_date': edited_expected_delivery_date,
                'employee_name': edited_employee_name,
                'notes': edited_notes if edited_notes else None
            }

            st.session_state.updated_order = updated_order
            st.session_state.popup_action = 'update'
            st.rerun()

    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("⚠️ Order löschen?")
def show_order_delete_popup(order_data: Dict[str, Any]):
    """Show order delete confirmation popup."""

    st.warning("Diese Aktion kann nicht rückgängig gemacht werden!")

    # Show order details
    st.write("**Zu löschende Order:**")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Order Number:** {order_data['order_number']}")
        st.write(f"**Supplier ID:** {order_data['supplier_id']}")
        st.write(f"**Bearbeiter:** {order_data['employee_name']}")
    with col2:
        st.write(f"**Order Date:** {order_data['order_date']}")
        st.write(f"**Expected Delivery:** {order_data['expected_delivery_date']}")
        if order_data.get('notes'):
            st.write(f"**Notizen:** {order_data['notes']}")

    st.write("---")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Endgültig löschen", type="primary", use_container_width=True):
            st.session_state.delete_order_number = order_data['order_number']
            st.session_state.popup_action = 'delete'
            st.rerun()

    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("📋 Order Details")
def show_order_details_popup(order_data: Dict[str, Any]):
    """Show detailed order information popup."""

    # Order basic information
    st.write("### 📋 Order Informationen")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Order Number:** {order_data['order_number']}")
        st.write(f"**Supplier ID:** {order_data['supplier_id']}")
        st.write(f"**Bearbeiter:** {order_data['employee_name']}")
    with col2:
        st.write(f"**Order Date:** {order_data['order_date']}")
        st.write(f"**Expected Delivery:** {order_data['expected_delivery_date']}")
        st.write(f"**Status:** {order_data.get('status', 'N/A')}")

    # Notes if available
    if order_data.get('notes'):
        st.write("### 📝 Notizen")
        st.info(order_data['notes'])

    # Order items if available
    if 'order_items' in order_data and order_data['order_items']:
        st.write("### 📦 Bestellpositionen")
        for i, item in enumerate(order_data['order_items'], 1):
            with st.expander(f"Position {i}: {item.get('article_number', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Artikelnummer:** {item.get('article_number', 'N/A')}")
                    st.write(f"**Bestellmenge:** {item.get('ordered_quantity', 'N/A')}")
                with col2:
                    st.write(f"**Einheit:** {item.get('unit_description', 'N/A')}")
                    if item.get('expected_delivery_date'):
                        st.write(f"**Erwartetes Lieferdatum:** {item['expected_delivery_date']}")
                if item.get('notes'):
                    st.write(f"**Notizen:** {item['notes']}")

    # Summary statistics
    if 'order_items' in order_data and order_data['order_items']:
        st.write("### 📊 Zusammenfassung")
        total_items = len(order_data['order_items'])
        total_quantity = sum(item.get('ordered_quantity', 0) for item in order_data['order_items'])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Anzahl Positionen", total_items)
        with col2:
            st.metric("Gesamtmenge", total_quantity)

    # Close button
    if st.button("✅ Schließen", type="primary", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()


@st.dialog("📊 Order Statistiken")
def show_order_statistics_popup(order_data: Dict[str, Any]):
    """Show order statistics popup."""

    st.write("### 📊 Order Statistiken")
    st.write(f"**Order:** {order_data['order_number']}")

    # Basic metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_items = len(order_data.get('order_items', []))
        st.metric("Positionen", total_items)

    with col2:
        total_quantity = sum(item.get('ordered_quantity', 0) for item in order_data.get('order_items', []))
        st.metric("Gesamtmenge", total_quantity)

    with col3:
        status = "Abgeschlossen" if order_data.get('is_completed') else "Offen"
        st.metric("Status", status)

    # Timeline information
    st.write("### ⏰ Zeitlinie")
    col1, col2 = st.columns(2)

    with col1:
        if order_data.get('order_date'):
            st.write(f"**Bestellt am:** {order_data['order_date']}")
        if order_data.get('created_at'):
            st.write(f"**Erstellt am:** {order_data['created_at']}")

    with col2:
        if order_data.get('expected_delivery_date'):
            st.write(f"**Erwartete Lieferung:** {order_data['expected_delivery_date']}")
        if order_data.get('updated_at'):
            st.write(f"**Letzte Änderung:** {order_data['updated_at']}")

    # Days until delivery
    if order_data.get('expected_delivery_date'):
        try:
            if isinstance(order_data['expected_delivery_date'], str):
                expected_date = datetime.fromisoformat(order_data['expected_delivery_date']).date()
            else:
                expected_date = order_data['expected_delivery_date']

            today = date.today()
            days_diff = (expected_date - today).days

            if days_diff > 0:
                st.info(f"⏰ Noch {days_diff} Tage bis zur erwarteten Lieferung")
            elif days_diff == 0:
                st.warning("📅 Lieferung heute erwartet")
            else:
                st.error(f"⚠️ Lieferung {abs(days_diff)} Tage überfällig")

        except Exception as e:
            logger.error(f"Error calculating delivery days: {e}")
            st.write("Lieferdatum-Berechnung nicht verfügbar")

    # Close button
    if st.button("✅ Schließen", type="primary", use_container_width=True):
        st.session_state.popup_action = 'close'
        st.rerun()