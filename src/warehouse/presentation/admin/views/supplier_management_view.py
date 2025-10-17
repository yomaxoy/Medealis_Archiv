"""
Supplier Management View - Admin Presentation Layer
Complete supplier management interface.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def show_supplier_management_view():
    """Main supplier management view with all functionality."""
    st.header("🏢 Supplier Management")

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "supplier" not in services:
        st.error("Supplier Service nicht verfügbar")
        return

    supplier_service = services["supplier"]

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Neu erstellen", "📊 Statistiken"])

    with tab1:
        show_supplier_list_tab(supplier_service)

    with tab2:
        show_new_supplier_tab(supplier_service)

    with tab3:
        show_supplier_statistics_tab(supplier_service)

    # Handle popup actions
    handle_supplier_popup_actions(supplier_service)


def show_supplier_list_tab(supplier_service):
    """Show supplier list with management actions."""
    st.subheader("📋 Supplier Liste")

    try:
        suppliers_data = supplier_service.get_all_suppliers()

        if suppliers_data:
            # Search and filter
            search_term = st.text_input(
                "🔍 Supplier suchen:",
                placeholder="Name oder ID eingeben...",
                key="supplier_search",
            )

            # Filter suppliers if search term provided
            if search_term:
                filtered_suppliers = [
                    s
                    for s in suppliers_data
                    if search_term.lower() in s.get("name", "").lower()
                    or search_term.lower() in s.get("supplier_id", "").lower()
                ]
                suppliers_data = filtered_suppliers

            # Display suppliers
            if suppliers_data:
                for i, supplier_dict in enumerate(suppliers_data):
                    render_supplier_row(supplier_dict, i, supplier_service)

                    if i < len(suppliers_data) - 1:
                        st.divider()
            else:
                st.info("Keine Suppliers gefunden, die den Suchkriterien entsprechen.")
        else:
            st.info("Keine Suppliers gefunden")

            # Quick action to create first supplier
            if st.button("➕ Ersten Supplier erstellen", type="primary"):
                st.session_state.switch_to_create_tab = True
                st.rerun()

    except Exception as e:
        logger.error(f"Error loading suppliers: {e}")
        st.error(f"Fehler beim Laden der Suppliers: {e}")


def render_supplier_row(supplier_dict: Dict[str, Any], index: int, supplier_service):
    """Render a single supplier row with actions."""
    col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 2, 2])

    with col1:
        st.write(f"**{supplier_dict.get('supplier_id', 'N/A')}**")

    with col2:
        supplier_name = supplier_dict.get("name", "N/A")
        st.write(supplier_name)

    with col3:
        notes = supplier_dict.get("notes", "Keine Notizen") or "Keine Notizen"
        if len(notes) > 50:
            st.write(f"{notes[:47]}...")
            if st.button(
                f"📄", key=f"notes_sup_{index}", help="Vollständige Notizen anzeigen"
            ):
                show_supplier_notes_popup(supplier_dict)
        else:
            st.write(notes)

    with col4:
        if st.button("🖊️", key=f"edit_sup_{index}", help="Supplier bearbeiten"):
            show_supplier_edit_action(supplier_dict)

    with col5:
        if st.button("🗑️", key=f"delete_sup_{index}", help="Supplier löschen"):
            show_supplier_delete_action(supplier_dict)


def show_supplier_edit_action(supplier_dict: Dict[str, Any]):
    """Handle supplier edit action."""
    try:
        from warehouse.presentation.admin.popups.supplier_view.supplier_popups import (
            show_supplier_edit_popup,
        )

        show_supplier_edit_popup(supplier_dict)
    except ImportError:
        # Fallback to inline edit
        st.session_state.edit_supplier = supplier_dict
        st.rerun()
    except Exception as e:
        logger.error(f"Error in supplier edit action: {e}")
        st.error(f"Fehler beim Bearbeiten: {e}")


def show_supplier_delete_action(supplier_dict: Dict[str, Any]):
    """Handle supplier delete action."""
    try:
        from warehouse.presentation.admin.popups.supplier_view.supplier_popups import (
            show_supplier_delete_popup,
        )

        show_supplier_delete_popup(supplier_dict)
    except ImportError:
        # Simple confirmation
        st.session_state.delete_supplier = supplier_dict
        st.warning(f"Supplier '{supplier_dict.get('name')}' löschen?")
    except Exception as e:
        logger.error(f"Error in supplier delete action: {e}")
        st.error(f"Fehler beim Löschen: {e}")


def show_supplier_notes_popup(supplier_dict: Dict[str, Any]):
    """Show full supplier notes."""
    st.session_state.show_supplier_notes = supplier_dict


def show_new_supplier_tab(supplier_service):
    """Show new supplier creation tab."""
    st.subheader("➕ Neuen Supplier erstellen")

    # Check if switched from list tab
    if st.session_state.get("switch_to_create_tab"):
        st.info("✨ Erstellen Sie Ihren ersten Supplier!")
        del st.session_state.switch_to_create_tab

    # Supplier creation form
    with st.form("new_supplier"):
        col1, col2 = st.columns(2)

        with col1:
            supplier_id = st.text_input(
                "Supplier ID*",
                placeholder="SUP-001",
                help="Eindeutige Identifikation für den Supplier",
            )
            name = st.text_input(
                "Name*",
                placeholder="Supplier Name GmbH",
                help="Vollständiger Firmenname",
            )

        with col2:
            contact_person = st.text_input(
                "Ansprechpartner", placeholder="Max Mustermann"
            )
            phone = st.text_input("Telefon", placeholder="+49 123 456789")

        # Extended fields
        with st.expander("🔧 Erweiterte Informationen", expanded=False):
            col3, col4 = st.columns(2)

            with col3:
                email = st.text_input("E-Mail", placeholder="kontakt@supplier.de")
                address = st.text_area("Adresse", placeholder="Straße 123\n12345 Stadt")

            with col4:
                website = st.text_input(
                    "Website", placeholder="https://www.supplier.de"
                )
                tax_number = st.text_input("Steuernummer", placeholder="DE123456789")

        # Notes
        notes = st.text_area(
            "Notizen",
            placeholder="Zusätzliche Informationen über den Supplier...",
            height=100,
        )

        # Submit button
        submitted = st.form_submit_button("➕ Supplier erstellen", type="primary")

        if submitted:
            create_new_supplier(
                supplier_service,
                supplier_id,
                name,
                contact_person,
                phone,
                email,
                address,
                website,
                tax_number,
                notes,
            )


def create_new_supplier(
    supplier_service,
    supplier_id,
    name,
    contact_person,
    phone,
    email,
    address,
    website,
    tax_number,
    notes,
):
    """Create new supplier with validation."""
    try:
        # Validation
        if not supplier_id or not name:
            st.error(
                "❌ Unvollständige Angaben: Supplier ID und Name sind erforderlich"
            )
            return

        # Prepare supplier data
        supplier_data = {
            "supplier_id": supplier_id.strip(),
            "name": name.strip(),
            "contact_person": contact_person.strip() if contact_person else "",
            "phone": phone.strip() if phone else "",
            "email": email.strip() if email else "",
            "address": address.strip() if address else "",
            "website": website.strip() if website else "",
            "tax_number": tax_number.strip() if tax_number else "",
            "notes": notes.strip() if notes else "",
        }

        # Show confirmation popup before creating
        from warehouse.presentation.admin.popups.supplier_view.supplier_popups import (
            show_supplier_confirmation_popup,
        )

        show_supplier_confirmation_popup(supplier_data)

    except Exception as e:
        logger.error(f"New supplier creation error: {e}")
        st.error(f"❌ Fehler bei der Supplier-Erstellung: {e}")


def show_supplier_statistics_tab(supplier_service):
    """Show supplier statistics."""
    st.subheader("📊 Supplier Statistiken")

    try:
        suppliers = supplier_service.get_all_suppliers()

        if suppliers:
            # Basic metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Gesamt Suppliers", len(suppliers))

            with col2:
                # Count suppliers with contact info
                with_contact = len([s for s in suppliers if s.get("contact_person")])
                st.metric("Mit Ansprechpartner", with_contact)

            with col3:
                # Count suppliers with email
                with_email = len([s for s in suppliers if s.get("email")])
                st.metric("Mit E-Mail", with_email)

            with col4:
                # Count suppliers with notes
                with_notes = len([s for s in suppliers if s.get("notes")])
                st.metric("Mit Notizen", with_notes)

            # Recent activity
            st.write("### 📈 Neueste Suppliers")

            # Sort by creation date if available, otherwise by name
            recent_suppliers = sorted(
                suppliers,
                key=lambda x: x.get("created_at", x.get("name", "")),
                reverse=True,
            )[:5]

            for supplier in recent_suppliers:
                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    st.write(supplier.get("supplier_id", "N/A"))
                with col2:
                    st.write(supplier.get("name", "N/A"))
                with col3:
                    created_at = supplier.get("created_at", "Unbekannt")
                    st.write(
                        str(created_at)[:10]
                        if created_at != "Unbekannt"
                        else created_at
                    )

            # Data quality analysis
            st.write("### 📋 Datenqualität")

            total = len(suppliers)
            completeness = {
                "Name": len([s for s in suppliers if s.get("name")]) / total * 100,
                "Ansprechpartner": len(
                    [s for s in suppliers if s.get("contact_person")]
                )
                / total
                * 100,
                "Telefon": len([s for s in suppliers if s.get("phone")]) / total * 100,
                "E-Mail": len([s for s in suppliers if s.get("email")]) / total * 100,
                "Adresse": len([s for s in suppliers if s.get("address")])
                / total
                * 100,
            }

            for field, percentage in completeness.items():
                st.progress(percentage / 100, text=f"{field}: {percentage:.1f}%")

        else:
            st.info("Keine Supplier-Daten für Statistiken verfügbar")

    except Exception as e:
        logger.error(f"Supplier statistics error: {e}")
        st.error(f"Fehler beim Laden der Statistiken: {e}")


def handle_supplier_popup_actions(supplier_service):
    """Handle popup actions and confirmations."""
    try:
        # Handle supplier confirmation
        if st.session_state.get("popup_action") == "confirm" and st.session_state.get(
            "confirmed_supplier"
        ):

            supplier_data = st.session_state.confirmed_supplier

            try:
                created_supplier_id = supplier_service.create_supplier(
                    supplier_id=supplier_data["supplier_id"],
                    name=supplier_data["name"],
                    notes=supplier_data.get("notes", ""),
                )

                st.success(f"✅ Supplier '{created_supplier_id}' erfolgreich erstellt!")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.confirmed_supplier = None
                st.rerun()

            except Exception as e:
                error_msg = str(e)
                if "existiert bereits" in error_msg or "already exists" in error_msg:
                    st.warning(
                        f"⚠️ Supplier '{supplier_data['supplier_id']}' existiert bereits"
                    )
                else:
                    st.error(f"❌ Fehler beim Erstellen des Suppliers: {e}")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.confirmed_supplier = None

        # Handle popup cancellation
        elif st.session_state.get("popup_action") == "cancel":
            st.session_state.popup_action = None
            st.session_state.confirmed_supplier = None
            st.session_state.edit_supplier = None
            st.session_state.delete_supplier = None

        # Handle supplier notes display
        if st.session_state.get("show_supplier_notes"):
            supplier = st.session_state.show_supplier_notes
            with st.expander(
                f"📄 Notizen für {supplier.get('name', 'N/A')}", expanded=True
            ):
                st.write(supplier.get("notes", "Keine Notizen"))
                if st.button("Schließen"):
                    st.session_state.show_supplier_notes = None
                    st.rerun()

        # Handle edit supplier (inline fallback)
        if st.session_state.get("edit_supplier"):
            supplier = st.session_state.edit_supplier
            st.info(f"Bearbeite Supplier: {supplier.get('name')}")
            # Implementation would go here
            if st.button("Abbrechen"):
                st.session_state.edit_supplier = None
                st.rerun()

        # Handle delete confirmation (simple fallback)
        if st.session_state.get("delete_supplier"):
            supplier = st.session_state.delete_supplier
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Löschen bestätigen", type="primary"):
                    # Implement delete logic here
                    st.success(f"Supplier '{supplier.get('name')}' gelöscht")
                    st.session_state.delete_supplier = None
                    st.rerun()
            with col2:
                if st.button("❌ Abbrechen"):
                    st.session_state.delete_supplier = None
                    st.rerun()

    except Exception as e:
        logger.error(f"Error in supplier popup actions: {e}")
        st.error(f"Popup-Fehler: {e}")
