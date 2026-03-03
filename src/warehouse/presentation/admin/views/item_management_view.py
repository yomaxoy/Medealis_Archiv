"""
Item Management View - Admin Presentation Layer
Complete item management interface.

Performance: Uses @st.cache_data for get_all_items() (60s TTL)
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CACHED DATA LOADERS
# =============================================================================

@st.cache_data(ttl=60)
def _load_all_items(_service, _cache_version: int) -> List[Dict[str, Any]]:
    """Load all items with caching (60s TTL)."""
    try:
        if hasattr(_service, "get_all_items"):
            return _service.get_all_items() or []
        return []
    except Exception as e:
        logger.error(f"Error loading items: {e}")
        return []


def show_item_management_view():
    """Main item management view with all functionality."""
    st.header("📦 Item Management")

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "item" not in services or "delivery" not in services:
        st.error("Item oder Delivery Service nicht verfügbar")
        return

    item_service = services["item"]
    delivery_service = services["delivery"]

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Liste", "➕ Item zu Delivery hinzufügen", "📊 Statistiken", "📄 Dokumente"]
    )

    with tab1:
        show_item_list_tab(item_service)

    with tab2:
        show_add_item_tab(delivery_service)

    with tab3:
        show_item_statistics_tab(item_service)

    with tab4:
        show_item_documents_tab()

    # Handle popup actions
    handle_item_popup_actions(item_service, delivery_service)


def show_item_list_tab(item_service):
    """Show item list with management actions."""
    st.subheader("📋 Item Liste")

    try:
        from warehouse.presentation.shared.cache_manager import CacheManager

        # Get all items (cached)
        items_data = _load_all_items(
            item_service,
            CacheManager.get_version("items")
        )

        if items_data and len(items_data) > 0:
            # Search and filter controls
            show_item_search_filters()

            # Apply filters
            filtered_items = apply_item_filters(items_data)

            if filtered_items:
                # Show items table
                render_items_table(filtered_items)
            else:
                st.info("Keine Items entsprechen den Filterkriterien.")
        else:
            st.info("Keine Items gefunden")

            # Quick action to add first item
            if st.button("➕ Erstes Item hinzufügen", type="primary"):
                st.session_state.switch_to_add_tab = True
                st.rerun()

    except Exception as e:
        import traceback
        logger.error(f"Error loading items: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        st.error(f"Fehler beim Laden der Items: {e}")
        st.code(traceback.format_exc())


def show_item_search_filters():
    """Show search and filter controls."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search_article = st.text_input(
            "🔍 Artikelnummer:", placeholder="A0001...", key="item_search_article"
        )

    with col2:
        search_batch = st.text_input(
            "🔍 Chargennummer:", placeholder="P-123...", key="item_search_batch"
        )

    with col3:
        search_delivery = st.text_input(
            "🔍 Lieferung:", placeholder="DEL-001...", key="item_search_delivery"
        )

    with col4:
        status_filter = st.selectbox(
            "Status Filter:",
            options=["Alle", "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"],
            key="item_status_filter",
        )


def apply_item_filters(items_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply search filters to items."""
    # Safety check: ensure items_data is not None
    if items_data is None:
        logger.warning("apply_item_filters received None items_data")
        return []

    filtered_items = items_data

    # Article number filter with safe get
    search_article = st.session_state.get("item_search_article", "") or ""
    if isinstance(search_article, str):
        search_article = search_article.strip()
    else:
        search_article = ""

    if search_article and filtered_items:
        filtered_items = [
            item
            for item in filtered_items
            if item and search_article.lower() in item.get("article_number", "").lower()
        ]

    # Batch number filter with safe get
    search_batch = st.session_state.get("item_search_batch", "") or ""
    if isinstance(search_batch, str):
        search_batch = search_batch.strip()
    else:
        search_batch = ""

    if search_batch and filtered_items:
        filtered_items = [
            item
            for item in filtered_items
            if item and search_batch.lower() in item.get("batch_number", "").lower()
        ]

    # Delivery filter with safe get
    search_delivery = st.session_state.get("item_search_delivery", "") or ""
    if isinstance(search_delivery, str):
        search_delivery = search_delivery.strip()
    else:
        search_delivery = ""

    if search_delivery and filtered_items:
        filtered_items = [
            item
            for item in filtered_items
            if item and search_delivery.lower() in item.get("delivery_number", "").lower()
        ]

    # Status filter with safe get
    status_filter = st.session_state.get("item_status_filter", "Alle") or "Alle"
    if status_filter != "Alle" and filtered_items:
        filtered_items = [
            item for item in filtered_items if item and item.get("status") == status_filter
        ]

    # Ensure we return a list, never None
    result = filtered_items if filtered_items is not None else []
    logger.debug(f"apply_item_filters returning {type(result)} with {len(result) if result else 0} items")
    return result


def render_items_table(items_data: List[Dict[str, Any]]):
    """Render items table with actions and certificate flags."""
    # Safety check: ensure items_data is not None
    if not items_data:
        st.info("Keine Items zum Anzeigen vorhanden")
        return

    # Header row with certificate columns
    header_cols = st.columns(
        [1.5, 2.5, 1.5, 0.8, 1.5, 1.5, 1.5, 0.8, 1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
    )
    headers = [
        "Artikel",
        "Chargennummer",
        "Lieferung",
        "Menge",
        "Status",
        "Bearbeiter",
        "Bezeichnung",
        "Rev.",
        "Lagerplatz",
        "📋",
        "📊",
        "🎨",
        "🔨",
        "📝",
        "Edit",
        "Delete",
    ]

    for col, header in zip(header_cols, headers):
        with col:
            st.write(f"**{header}**")

    st.divider()

    # Data rows
    for i, item_dict in enumerate(items_data):
        if item_dict:  # Safety check for None items
            render_item_row(item_dict, i)

            if i < len(items_data) - 1:
                st.divider()


def render_item_row(item_dict: Dict[str, Any], index: int):
    """Render a single item row with certificate flags."""
    cols = st.columns(
        [1.5, 2.5, 1.5, 0.8, 1.5, 1.5, 1.5, 0.8, 1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
    )

    with cols[0]:  # Article Number
        article_num = item_dict.get("article_number", "N/A")
        st.write(f"**{article_num}**")

    with cols[1]:  # Batch Number
        batch = item_dict.get("batch_number", "N/A") or "N/A"
        # Ensure batch is a string before checking length
        if batch and isinstance(batch, str) and len(batch) > 20:
            st.write(f"{batch[:17]}...")
        else:
            st.write(batch)

    with cols[2]:  # Delivery Number
        st.write(item_dict.get("delivery_number", "N/A"))

    with cols[3]:  # Quantity
        st.write(str(item_dict.get("quantity", 0)))

    with cols[4]:  # Status
        status = item_dict.get("status", "N/A")
        if status in ["COMPLETED", "DELIVERED"]:
            st.success(status)
        elif status in ["PENDING", "IN_PROGRESS"]:
            st.warning(status)
        elif status == "FAILED":
            st.error(status)
        else:
            st.info(status)

    with cols[5]:  # Employee
        employee = item_dict.get("employee_name", "N/A") or "N/A"
        # Ensure employee is a string before checking length
        if employee and isinstance(employee, str) and len(employee) > 15:
            st.write(f"{employee[:12]}...")
        else:
            st.write(employee)

    with cols[6]:  # Designation
        designation = item_dict.get("designation", "") or ""
        # Ensure designation is a string before checking length
        if designation and isinstance(designation, str) and len(designation) > 20:
            st.write(f"{designation[:17]}...")
        else:
            st.write(designation if designation else "N/A")

    with cols[7]:  # Revision
        revision = item_dict.get("revision_number")
        st.write(str(revision) if revision is not None else "N/A")

    with cols[8]:  # Storage Location
        storage = item_dict.get("storage_location", "") or ""
        st.write(storage if storage else "N/A")

    # Certificate flags - extract from item data
    certificates = item_dict.get("certificates", {})

    with cols[9]:  # Materialzeugnis 📋
        material_cert = certificates.get("material_certificate", False)
        st.write("✅" if material_cert else "❌")

    with cols[10]:  # Messprotokolle 📊
        measurement_cert = certificates.get("measurement_protocol", False)
        st.write("✅" if measurement_cert else "❌")

    with cols[11]:  # Beschichtungszeugnis 🎨
        coating_cert = certificates.get("coating_certificate", False)
        st.write("✅" if coating_cert else "❌")

    with cols[12]:  # Härtezeugnis 🔨
        hardness_cert = certificates.get("hardness_certificate", False)
        st.write("✅" if hardness_cert else "❌")

    with cols[13]:  # Weitere Zeugnisse 📝
        additional_cert = certificates.get("additional_certificates", False)
        st.write("✅" if additional_cert else "❌")

    with cols[14]:  # Edit button
        if st.button("🖊️", key=f"edit_item_{index}", help="Item bearbeiten"):
            show_item_edit_action(item_dict)

    with cols[15]:  # Delete button
        if st.button("🗑️", key=f"delete_item_{index}", help="Item löschen"):
            show_item_delete_action(item_dict)


def show_item_edit_action(item_dict: Dict[str, Any]):
    """Handle item edit action."""
    try:
        from warehouse.presentation.admin.popups.item_view.item_popups import (
            show_item_edit_popup,
        )

        show_item_edit_popup(item_dict)
    except ImportError:
        # Fallback
        st.session_state.edit_item = item_dict
        st.rerun()
    except Exception as e:
        logger.error(f"Error in item edit action: {e}")
        st.error(f"Fehler beim Bearbeiten: {e}")


def show_item_delete_action(item_dict: Dict[str, Any]):
    """Handle item delete action."""
    try:
        from warehouse.presentation.admin.popups.item_view.item_popups import (
            show_item_delete_popup,
        )

        show_item_delete_popup(item_dict)
    except ImportError:
        # Fallback
        st.session_state.delete_item = item_dict
        st.rerun()
    except Exception as e:
        logger.error(f"Error in item delete action: {e}")
        st.error(f"Fehler beim Löschen: {e}")


def show_add_item_tab(delivery_service):
    """Show add item to delivery tab."""
    st.subheader("➕ Item zu Delivery hinzufügen")

    # Check if switched from list tab
    if st.session_state.get("switch_to_add_tab"):
        st.info("✨ Fügen Sie Ihr erstes Item hinzu!")
        del st.session_state.switch_to_add_tab

    # Item addition form
    with st.form("add_item_to_delivery"):
        col1, col2 = st.columns(2)

        with col1:
            delivery_number = st.text_input(
                "Delivery Number*",
                placeholder="DEL-001",
                help="Lieferscheinnummer zu der das Item hinzugefügt werden soll",
            )
            article_number = st.text_input(
                "Article Number*", placeholder="A0001", help="Eindeutige Artikelnummer"
            )
            batch_number = st.text_input(
                "Batch Number*",
                placeholder="P-123456789012-1234",
                help="Chargennummer für Rückverfolgbarkeit",
            )

        with col2:
            quantity = st.number_input(
                "Quantity*", min_value=1, value=1, help="Anzahl der Items"
            )
            employee_name = st.text_input(
                "Employee Name*",
                placeholder="Max Mustermann",
                help="Name des bearbeitenden Mitarbeiters",
            )

            # Additional optional fields
            with st.expander("🔧 Erweiterte Felder", expanded=False):
                designation = st.text_input(
                    "Bezeichnung", placeholder="Artikel-Bezeichnung"
                )
                storage_location = st.text_input("Lagerplatz", placeholder="A1-B2-C3")
                notes = st.text_area(
                    "Notizen", placeholder="Zusätzliche Informationen..."
                )

        submitted = st.form_submit_button("➕ Item hinzufügen", type="primary")

        if submitted:
            create_new_item(
                delivery_service,
                delivery_number,
                article_number,
                batch_number,
                quantity,
                employee_name,
                designation,
                storage_location,
                notes,
            )


def create_new_item(
    delivery_service,
    delivery_number,
    article_number,
    batch_number,
    quantity,
    employee_name,
    designation,
    storage_location,
    notes,
):
    """Create new item with validation."""
    try:
        # Validation
        if not all([delivery_number, article_number, batch_number, employee_name]):
            st.error("❌ Alle Pflichtfelder sind erforderlich")
            return

        # Prepare item data
        item_data = {
            "delivery_number": delivery_number.strip(),
            "article_number": article_number.strip(),
            "batch_number": batch_number.strip(),
            "quantity": quantity,
            "employee_name": employee_name.strip(),
            "designation": designation.strip() if designation else "",
            "storage_location": storage_location.strip() if storage_location else "",
            "notes": notes.strip() if notes else "",
        }

        # Show confirmation popup
        from warehouse.presentation.admin.popups.item_view.item_popups import (
            show_item_confirmation_popup,
        )

        show_item_confirmation_popup(item_data)

    except Exception as e:
        logger.error(f"New item creation error: {e}")
        st.error(f"❌ Fehler bei der Item-Erstellung: {e}")


def show_item_statistics_tab(item_service):
    """Show item statistics."""
    st.subheader("📊 Item Statistiken")

    try:
        from warehouse.presentation.shared.cache_manager import CacheManager

        # Get all items (cached)
        items = _load_all_items(
            item_service,
            CacheManager.get_version("items")
        )

        if items and len(items) > 0:
            # Basic metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Gesamt Items", len(items))

            with col2:
                total_quantity = sum(item.get("quantity", 0) for item in items)
                st.metric("Gesamt Menge", total_quantity)

            with col3:
                unique_articles = len(
                    set(
                        item.get("article_number")
                        for item in items
                        if item.get("article_number")
                    )
                )
                st.metric("Unique Artikel", unique_articles)

            with col4:
                unique_deliveries = len(
                    set(
                        item.get("delivery_number")
                        for item in items
                        if item.get("delivery_number")
                    )
                )
                st.metric("Deliveries", unique_deliveries)

            # Status distribution
            st.write("### 📊 Status Verteilung")

            status_counts = {}
            for item in items:
                status = item.get("status", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1

            if status_counts:
                for status, count in status_counts.items():
                    percentage = (count / len(items)) * 100
                    st.progress(
                        percentage / 100, text=f"{status}: {count} ({percentage:.1f}%)"
                    )

            # Top articles
            st.write("### 🔝 Top Artikel (nach Menge)")

            article_quantities = {}
            for item in items:
                article = item.get("article_number", "UNKNOWN")
                quantity = item.get("quantity", 0)
                article_quantities[article] = (
                    article_quantities.get(article, 0) + quantity
                )

            # Sort by quantity and show top 10
            top_articles = sorted(
                article_quantities.items(), key=lambda x: x[1], reverse=True
            )[:10]

            for article, total_qty in top_articles:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(article)
                with col2:
                    st.write(f"{total_qty}")

            # Storage locations
            st.write("### 📦 Lagerplätze")

            storage_counts = {}
            for item in items:
                storage = item.get("storage_location", "Unbekannt")
                if not storage:
                    storage = "Unbekannt"
                storage_counts[storage] = storage_counts.get(storage, 0) + 1

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Lagerplatz**")
            with col2:
                st.write("**Anzahl Items**")

            for storage, count in sorted(storage_counts.items()):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(storage)
                with col2:
                    st.write(count)

        else:
            st.info("Keine Item-Daten für Statistiken verfügbar")

    except Exception as e:
        logger.error(f"Item statistics error: {e}")
        st.error(f"Fehler beim Laden der Statistiken: {e}")


def show_item_documents_tab():
    """Show item documents management."""
    st.subheader("📄 Item Dokumente")

    st.info("Dokumenten-Management für Items wird implementiert...")

    # Placeholder for future document features
    st.write("**Geplante Features:**")
    st.write("- 📎 Artikel-spezifische Dokumente")
    st.write("- 🖨️ Item-Listen exportieren")
    st.write("- 📋 Qualitätszertifikate")
    st.write("- 🔍 Batch-Rückverfolgung")
    st.write("- 📊 Item-Berichte")


def handle_item_popup_actions(item_service, delivery_service):
    """Handle popup actions and confirmations."""
    try:
        # Handle item confirmation
        if st.session_state.get("popup_action") == "confirm" and st.session_state.get(
            "confirmed_item"
        ):

            item_data = st.session_state.confirmed_item

            try:
                success = delivery_service.add_item_to_delivery(
                    delivery_number=item_data["delivery_number"],
                    article_number=item_data["article_number"],
                    batch_number=item_data["batch_number"],
                    quantity=item_data["quantity"],
                    employee_name=item_data["employee_name"],
                )

                if success:
                    st.success(
                        f"✅ Item '{item_data['article_number']}' erfolgreich zur Delivery hinzugefügt!"
                    )
                else:
                    st.error("❌ Item konnte nicht hinzugefügt werden")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.confirmed_item = None
                st.rerun()

            except Exception as e:
                st.error(f"❌ Fehler beim Hinzufügen des Items: {e}")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.confirmed_item = None

        # Handle item update confirmation
        elif st.session_state.get("popup_action") == "update" and st.session_state.get(
            "updated_item"
        ):

            item_data = st.session_state.updated_item

            try:
                # Use ItemService to update item
                from warehouse.presentation.shared.cache_manager import CacheManager
                success = item_service.update_item(
                    delivery_number=item_data.get("delivery_number"),
                    article_number=item_data.get("article_number"),
                    batch_number=item_data.get("batch_number"),
                    quantity=item_data.get("quantity"),
                    employee_name=item_data.get("employee_name"),
                    designation=item_data.get("designation"),
                )

                if success:
                    CacheManager.invalidate_related("items")
                    st.success(
                        f"✅ Item '{item_data.get('article_number')}' erfolgreich aktualisiert!"
                    )
                else:
                    st.warning(
                        f"⚠️ Item '{item_data.get('article_number')}' konnte nicht aktualisiert werden"
                    )

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.updated_item = None
                st.rerun()

            except Exception as e:
                logger.error(f"Error updating item: {e}")
                st.error(f"❌ Fehler beim Aktualisieren des Items: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.updated_item = None

        # Handle item delete confirmation (from popup)
        elif st.session_state.get("popup_action") == "delete_confirm" and st.session_state.get(
            "delete_item_confirmed"
        ):

            item_data = st.session_state.delete_item_confirmed

            try:
                # Extract composite key from item_data
                delivery_number = item_data.get("delivery_number")
                article_number = item_data.get("article_number")
                batch_number = item_data.get("batch_number")

                if not all([delivery_number, article_number, batch_number]):
                    st.error("❌ Unvollständige Item-Daten zum Löschen")
                    st.session_state.popup_action = None
                    st.session_state.delete_item_confirmed = None
                    return

                success = item_service.delete_item(
                    delivery_number=delivery_number,
                    article_number=article_number,
                    batch_number=batch_number,
                )

                if success:
                    from warehouse.presentation.shared.cache_manager import CacheManager
                    CacheManager.invalidate_related("items")
                    st.success(f"✅ Item '{article_number}' erfolgreich gelöscht!")
                else:
                    st.warning(
                        f"⚠️ Item '{article_number}' konnte nicht gelöscht werden"
                    )

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.delete_item_confirmed = None
                st.rerun()

            except Exception as e:
                logger.error(f"Error deleting item: {e}")
                st.error(f"❌ Fehler beim Löschen des Items: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.delete_item_confirmed = None

        # Handle popup cancellation
        elif st.session_state.get("popup_action") == "cancel":
            st.session_state.popup_action = None
            st.session_state.confirmed_item = None
            st.session_state.updated_item = None
            st.session_state.delete_item_id = None
            st.session_state.edit_item = None
            st.session_state.delete_item = None

        # Handle edit item (inline fallback)
        if st.session_state.get("edit_item"):
            item = st.session_state.edit_item
            st.info(f"Bearbeite Item: {item.get('article_number')}")
            if st.button("Abbrechen"):
                st.session_state.edit_item = None
                st.rerun()

        # Handle delete confirmation (simple fallback)
        if st.session_state.get("delete_item"):
            item = st.session_state.delete_item
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Löschen bestätigen", type="primary"):
                    st.success(f"Item '{item.get('article_number')}' gelöscht")
                    st.session_state.delete_item = None
                    st.rerun()
            with col2:
                if st.button("❌ Abbrechen"):
                    st.session_state.delete_item = None
                    st.rerun()

    except Exception as e:
        logger.error(f"Error in item popup actions: {e}")
        st.error(f"Popup-Fehler: {e}")
