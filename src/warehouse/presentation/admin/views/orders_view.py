"""
Orders View - Admin Presentation Layer
Complete order management interface.
"""

import streamlit as st
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def show_orders_view():
    """Main order management view with all functionality."""
    st.header("📝 Order Management")

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "order" not in services:
        st.error("Order Service nicht verfügbar")
        return

    order_service = services["order"]

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Liste", "➕ Neu erstellen", "📊 Statistiken"])

    with tab1:
        show_orders_list_tab(order_service)

    with tab2:
        show_new_order_tab(order_service)

    with tab3:
        show_orders_statistics_tab(order_service)

    # Handle popup actions
    handle_order_popup_actions(order_service)


def show_orders_list_tab(order_service):
    """Show orders list with management actions."""
    st.subheader("📋 Order Liste")

    try:
        orders_data = (
            order_service.get_all_orders()
            if hasattr(order_service, "get_all_orders")
            else []
        )

        if orders_data:
            # Search and filter
            search_term = st.text_input(
                "🔍 Order suchen:",
                placeholder="Order Number oder Supplier ID eingeben...",
                key="order_search",
            )

            # Filter orders if search term provided
            if search_term:
                filtered_orders = [
                    o
                    for o in orders_data
                    if search_term.lower() in o.get("order_number", "").lower()
                    or search_term.lower() in o.get("supplier_id", "").lower()
                ]
                orders_data = filtered_orders

            # Display orders
            if orders_data:
                # Header row
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
                    [2, 2, 2, 2, 2, 2, 1, 1]
                )
                with col1:
                    st.write("**Order Number**")
                with col2:
                    st.write("**Supplier**")
                with col3:
                    st.write("**Order Date**")
                with col4:
                    st.write("**Expected Delivery**")
                with col5:
                    st.write("**Status**")
                with col6:
                    st.write("**Employee**")
                with col7:
                    st.write("**Edit**")
                with col8:
                    st.write("**Delete**")

                st.divider()

                # Display each order
                for i, order_dict in enumerate(orders_data):
                    render_order_row(order_dict, i, order_service)

                    if i < len(orders_data) - 1:
                        st.divider()
            else:
                st.info("Keine Orders gefunden, die den Suchkriterien entsprechen.")
        else:
            st.info("Keine Orders gefunden")

            # Quick action to create first order
            if st.button("➕ Erste Order erstellen", type="primary"):
                st.session_state.switch_to_create_order_tab = True
                st.rerun()

    except Exception as e:
        logger.error(f"Error loading orders: {e}")
        st.error(f"Fehler beim Laden der Orders: {e}")


def render_order_row(order_dict: Dict[str, Any], index: int, order_service):
    """Render a single order row with actions."""
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
        [2, 2, 2, 2, 2, 2, 1, 1]
    )

    with col1:
        st.write(f"**{order_dict.get('order_number', 'N/A')}**")

    with col2:
        st.write(order_dict.get("supplier_id", "N/A"))

    with col3:
        st.write(str(order_dict.get("order_date", "N/A")))

    with col4:
        st.write(str(order_dict.get("expected_delivery_date", "N/A")))

    with col5:
        st.write(order_dict.get("status", "N/A"))

    with col6:
        employee = order_dict.get("employee_name", "N/A")
        if len(employee) > 15:
            st.write(f"{employee[:12]}...")
        else:
            st.write(employee)

    with col7:
        if st.button("🖊️", key=f"edit_order_{index}", help="Order bearbeiten"):
            show_order_edit_action(order_dict)

    with col8:
        if st.button("🗑️", key=f"delete_order_{index}", help="Order löschen"):
            show_order_delete_action(order_dict)


def show_order_edit_action(order_dict: Dict[str, Any]):
    """Handle order edit action."""
    try:
        from warehouse.presentation.admin.popups.order_view.order_popups import (
            show_order_edit_popup,
        )

        show_order_edit_popup(order_dict)
    except ImportError:
        # Fallback to inline edit
        st.session_state.edit_order = order_dict
        st.rerun()
    except Exception as e:
        logger.error(f"Error in order edit action: {e}")
        st.error(f"Fehler beim Bearbeiten: {e}")


def show_order_delete_action(order_dict: Dict[str, Any]):
    """Handle order delete action."""
    try:
        from warehouse.presentation.admin.popups.order_view.order_popups import (
            show_order_delete_popup,
        )

        show_order_delete_popup(order_dict)
    except ImportError:
        # Simple confirmation
        st.session_state.delete_order = order_dict
        st.warning(f"Order '{order_dict.get('order_number')}' löschen?")
    except Exception as e:
        logger.error(f"Error in order delete action: {e}")
        st.error(f"Fehler beim Löschen: {e}")


def show_new_order_tab(order_service):
    """Show new order creation tab."""
    st.subheader("➕ Neue Order erstellen")

    # Check if switched from list tab
    if st.session_state.get("switch_to_create_order_tab"):
        st.info("✨ Erstellen Sie Ihre erste Order!")
        del st.session_state.switch_to_create_order_tab

    # Order creation form
    with st.form("new_order"):
        col1, col2 = st.columns(2)

        with col1:
            order_number = st.text_input(
                "Order Number*",
                placeholder="ORD-001",
                help="Eindeutige Identifikation für die Order",
            )
            supplier_id = st.text_input(
                "Supplier ID*",
                placeholder="SUP-001",
                help="ID des bestellenden Suppliers",
            )
            employee_name = st.text_input(
                "Employee Name*",
                placeholder="Max Mustermann",
                help="Name des verantwortlichen Mitarbeiters",
            )

        with col2:
            order_date = st.date_input(
                "Order Date*", value=date.today(), help="Datum der Bestellung"
            )
            expected_delivery_date = st.date_input(
                "Expected Delivery Date*",
                value=date.today(),
                help="Erwartetes Lieferdatum",
            )

        # Notes
        notes = st.text_area(
            "Notizen", placeholder="Optionale Notizen zur Bestellung...", height=100
        )

        # Submit button
        submitted = st.form_submit_button("➕ Order erstellen", type="primary")

        if submitted:
            create_new_order(
                order_service,
                order_number,
                supplier_id,
                order_date,
                expected_delivery_date,
                employee_name,
                notes,
            )


def create_new_order(
    order_service,
    order_number,
    supplier_id,
    order_date,
    expected_delivery_date,
    employee_name,
    notes,
):
    """Create new order with validation."""
    try:
        # Validation
        if not order_number or not supplier_id or not employee_name:
            st.error(
                "❌ Unvollständige Angaben: Order Number, Supplier ID und Employee Name sind erforderlich"
            )
            return

        # Create order
        order_service.create_order(
            order_number=order_number,
            supplier_id=supplier_id,
            order_date=order_date,
            expected_delivery_date=expected_delivery_date,
            employee_name=employee_name,
        )

        st.success(f"✅ Order '{order_number}' erfolgreich erstellt!")
        st.rerun()

    except Exception as e:
        logger.error(f"New order creation error: {e}")
        st.error(f"❌ Fehler beim Erstellen der Order: {e}")


def show_orders_statistics_tab(order_service):
    """Show order statistics."""
    st.subheader("📊 Order Statistiken")

    try:
        stats = order_service.get_order_statistics()

        if stats:
            # Basic metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Orders", stats.get("total_orders", 0))
                st.metric("Completed Orders", stats.get("completed_orders", 0))

            with col2:
                st.metric("Open Orders", stats.get("open_orders", 0))
                st.metric("Overdue Orders", stats.get("overdue_orders", 0))

            with col3:
                completion_rate = stats.get("completion_rate", 0)
                st.metric("Completion Rate", f"{completion_rate:.1f}%")

            # Additional statistics
            st.write("### 📈 Detailstatistiken")

            # Status distribution if available
            if "status_distribution" in stats:
                st.write("**Status Verteilung:**")
                for status, count in stats["status_distribution"].items():
                    st.write(f"- {status}: {count}")

            # Recent orders
            if "recent_orders" in stats:
                st.write("**Neueste Orders:**")
                recent_orders = stats["recent_orders"][:5]  # Show last 5
                for order in recent_orders:
                    col_num, col_date, col_supplier = st.columns(3)
                    with col_num:
                        st.write(order.get("order_number", "N/A"))
                    with col_date:
                        st.write(str(order.get("order_date", "N/A"))[:10])
                    with col_supplier:
                        st.write(order.get("supplier_id", "N/A"))

        else:
            st.info("Keine Order-Statistiken verfügbar")

    except Exception as e:
        logger.error(f"Order statistics error: {e}")
        st.error(f"Fehler beim Laden der Order-Statistiken: {e}")


def handle_order_popup_actions(order_service):
    """Handle popup actions and confirmations."""
    try:
        # Handle order update confirmation
        if st.session_state.get("popup_action") == "update" and st.session_state.get(
            "updated_order"
        ):

            order_data = st.session_state.updated_order

            try:
                # Use the new update_order method with proper parameter handling
                success = order_service.update_order(
                    order_number=order_data["order_number"],
                    supplier_id=order_data.get("supplier_id"),
                    order_date=order_data.get("order_date"),
                    expected_delivery_date=order_data.get("expected_delivery_date"),
                    employee_name=order_data.get("employee_name"),
                    notes=order_data.get(
                        "notes"
                    ),  # This parameter now exists in our new method
                )

                if success:
                    st.success(
                        f"✅ Order '{order_data['order_number']}' erfolgreich aktualisiert!"
                    )
                else:
                    st.warning(
                        f"⚠️ Order '{order_data['order_number']}' konnte nicht aktualisiert werden"
                    )

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.updated_order = None
                st.rerun()

            except Exception as e:
                logger.error(f"Error updating order: {e}")
                st.error(f"❌ Fehler beim Aktualisieren der Order: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.updated_order = None

        # Handle order delete confirmation
        elif st.session_state.get("popup_action") == "delete" and st.session_state.get(
            "delete_order_number"
        ):

            order_number = st.session_state.delete_order_number

            try:
                success = order_service.delete_order(order_number)

                if success:
                    st.success(f"✅ Order '{order_number}' erfolgreich gelöscht!")
                else:
                    st.warning(f"⚠️ Order '{order_number}' konnte nicht gelöscht werden")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.delete_order_number = None
                st.rerun()

            except Exception as e:
                st.error(f"❌ Fehler beim Löschen der Order: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.delete_order_number = None

        # Handle popup cancellation
        elif st.session_state.get("popup_action") == "cancel":
            st.session_state.popup_action = None
            st.session_state.updated_order = None
            st.session_state.delete_order_number = None
            st.session_state.edit_order = None
            st.session_state.delete_order = None

        # Handle edit order (inline fallback)
        if st.session_state.get("edit_order"):
            order = st.session_state.edit_order
            st.info(f"Bearbeite Order: {order.get('order_number')}")
            # Implementation would go here
            if st.button("Abbrechen"):
                st.session_state.edit_order = None
                st.rerun()

        # Handle delete confirmation (simple fallback)
        if st.session_state.get("delete_order"):
            order = st.session_state.delete_order
            st.warning(f"Order '{order.get('order_number')}' wirklich löschen?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Löschen bestätigen", type="primary"):
                    try:
                        success = order_service.delete_order(order.get("order_number"))
                        if success:
                            st.success(f"Order '{order.get('order_number')}' gelöscht")
                        else:
                            st.error("Order konnte nicht gelöscht werden")
                    except Exception as e:
                        st.error(f"Fehler beim Löschen: {e}")
                    st.session_state.delete_order = None
                    st.rerun()
            with col2:
                if st.button("❌ Abbrechen"):
                    st.session_state.delete_order = None
                    st.rerun()

    except Exception as e:
        logger.error(f"Error in order popup actions: {e}")
        st.error(f"Popup-Fehler: {e}")
