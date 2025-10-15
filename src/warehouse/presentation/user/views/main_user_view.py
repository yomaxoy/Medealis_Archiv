"""
Main User View - User Presentation Layer
Simplified main page for warehouse users focusing on ease of use.
"""

import streamlit as st
import logging
from typing import Dict, Any, List

# Import popups
from warehouse.presentation.user.popups.visual_inspection import show_visual_inspection_popup
from warehouse.presentation.user.popups.data_confirmation import show_data_confirmation_popup
from warehouse.presentation.user.popups.measurement import show_measurement_popup
from warehouse.presentation.user.popups.document_check import show_document_check_popup
from warehouse.presentation.user.popups.document_merge import show_document_merge_popup
from warehouse.presentation.user.popups.delivery_scan import (
    show_delivery_scan_popup,
    show_extraction_confirmation_popup,
)

logger = logging.getLogger(__name__)


def show_main_user_view():
    """
    Show simplified main user view with left menu and item table.
    Focus: Easy to use, clean interface without verbose status messages.
    """
    # Title and Scan button in header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📦 Wareneingangskontrolle")
    with col2:
        st.write("")  # Spacing
        if st.button("📄 Lieferschein scannen", type="primary", use_container_width=True, key="scan_button_header"):
            st.session_state.show_scan_popup = True
            st.rerun()

    # Check system initialization
    if not st.session_state.get("system_initialized"):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get("services", {})
    if "item" not in services:
        st.error("Item Service nicht verfügbar")
        return

    # Handle Lieferschein-Scan Popup
    if st.session_state.get("show_scan_popup"):
        show_delivery_scan_popup()

    # Handle Extraction Confirmation Popup
    if st.session_state.get("show_extraction_popup") and st.session_state.get(
        "extracted_delivery_data"
    ):
        show_extraction_confirmation_popup(st.session_state.extracted_delivery_data)

    # Handle popup actions (extraction confirm)
    if st.session_state.get("popup_action") == "extraction_confirm":
        handle_extraction_confirmation(services)

    # Main content: Item table
    show_item_table(services)


def show_item_table(services):
    """Show item table with latest items at the bottom."""
    # Compact table CSS for reduced row height
    st.markdown("""
        <style>
        /* Reduce vertical padding in table cells */
        div[data-testid="stVerticalBlock"] > div:has(div.row-widget) {
            gap: 0.2rem !important;
        }

        /* Compact text elements */
        .stMarkdown p {
            margin-bottom: 0.2rem !important;
        }

        /* Compact buttons */
        div[data-testid="column"] button {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            min-height: 2rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Simple filter section
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        filter_delivery = st.text_input(
            "🔍 Lieferschein-Nr:",
            value=st.session_state.get("user_filter_delivery", ""),
            key="user_filter_delivery",
            placeholder="Filter nach LS-Nr...",
        )

    with col2:
        filter_article = st.text_input(
            "🔍 Artikel-Nr:",
            value=st.session_state.get("user_filter_article", ""),
            key="user_filter_article",
            placeholder="Filter nach Artikel-Nr...",
        )

    with col3:
        if st.button("🔄 Zurücksetzen", use_container_width=True):
            if "user_filter_delivery" in st.session_state:
                del st.session_state.user_filter_delivery
            if "user_filter_article" in st.session_state:
                del st.session_state.user_filter_article
            if "user_filter_status" in st.session_state:
                del st.session_state.user_filter_status
            st.rerun()

    # Status filter buttons
    st.write("**📊 Status-Filter:**")
    status_col1, status_col2, status_col3, status_col4, status_col5, status_col6 = st.columns(6)

    # Get current filter status
    current_status_filter = st.session_state.get("user_filter_status", None)

    with status_col1:
        button_type = "primary" if current_status_filter is None else "secondary"
        if st.button("Alle", use_container_width=True, type=button_type, key="status_all"):
            st.session_state.user_filter_status = None
            st.rerun()

    with status_col2:
        button_type = "primary" if current_status_filter == "Daten prüfen" else "secondary"
        if st.button("📋 Daten prüfen", use_container_width=True, type=button_type, key="status_data"):
            st.session_state.user_filter_status = "Daten prüfen"
            st.rerun()

    with status_col3:
        button_type = "primary" if current_status_filter == "Dokumente prüfen" else "secondary"
        if st.button("📄 Dokumente", use_container_width=True, type=button_type, key="status_docs"):
            st.session_state.user_filter_status = "Dokumente prüfen"
            st.rerun()

    with status_col4:
        button_type = "primary" if current_status_filter == "Vermessen" else "secondary"
        if st.button("📏 Vermessen", use_container_width=True, type=button_type, key="status_measure"):
            st.session_state.user_filter_status = "Vermessen"
            st.rerun()

    with status_col5:
        button_type = "primary" if current_status_filter == "Sichtkontrolle" else "secondary"
        if st.button("👁️ Sichtkontrolle", use_container_width=True, type=button_type, key="status_visual"):
            st.session_state.user_filter_status = "Sichtkontrolle"
            st.rerun()

    with status_col6:
        button_type = "primary" if current_status_filter == "Freigegeben" else "secondary"
        if st.button("✅ Freigegeben", use_container_width=True, type=button_type, key="status_approved"):
            st.session_state.user_filter_status = "Freigegeben"
            st.rerun()

    st.write("---")

    # Load items from database
    all_items = []
    try:
        delivery_service = services.get("delivery")
        item_service = services["item"]

        # Get all deliveries and items
        deliveries_data = (
            delivery_service.get_all_deliveries()
            if delivery_service and hasattr(delivery_service, "get_all_deliveries")
            else []
        )
        items_data = (
            item_service.get_all_items()
            if hasattr(item_service, "get_all_items")
            else []
        )

        # Combine delivery and item data
        for item in items_data:
            # Find matching delivery
            matching_delivery = None
            for delivery in deliveries_data:
                if item.get("delivery_number") == delivery.get("delivery_number"):
                    matching_delivery = delivery
                    break

            # Create item entry - include ALL fields from database
            item_entry = {
                "delivery_number": item.get("delivery_number", "N/A"),
                "article_number": item.get("article_number", "N/A"),
                "batch_number": item.get("batch_number", "N/A"),
                "quantity": str(item.get("quantity", "N/A")),
                "delivery_date": (
                    matching_delivery.get("delivery_date", "N/A")
                    if matching_delivery
                    else "N/A"
                ),
                "supplier": (
                    matching_delivery.get("supplier_name", "Unbekannt")
                    if matching_delivery
                    else "Unbekannt"
                ),
                # Use 'designation' from DB, fallback to 'description', then article_number
                "description": (
                    item.get("designation", "") or
                    item.get("description", "") or
                    f"Artikel {item.get('article_number', 'N/A')}"
                ),
                # Additional fields for popups - directly from DB (avoid None values)
                "order_number": item.get("order_number") or "",
                "storage_location": item.get("storage_location") or "",
                "ordered_quantity": item.get("ordered_quantity") or 0,
                "delivery_slip_quantity": item.get("delivery_slip_quantity") or 0,
                "delivered_quantity": item.get("delivered_quantity") or 0,
                "status": item.get("status") or "Pending",
            }
            all_items.append(item_entry)

    except Exception as e:
        logger.error(f"Error loading items: {e}")
        st.error(f"Fehler beim Laden der Artikel: {e}")
        return

    # Apply filters
    filtered_items = all_items.copy()

    if filter_delivery:
        filtered_items = [
            item for item in filtered_items
            if filter_delivery.upper() in item["delivery_number"].upper()
        ]

    if filter_article:
        filtered_items = [
            item for item in filtered_items
            if filter_article.upper() in item["article_number"].upper()
        ]

    # Apply status filter
    filter_status = st.session_state.get("user_filter_status", None)
    if filter_status:
        filtered_items = [
            item for item in filtered_items
            if filter_status.lower() in item["status"].lower()
        ]

    # Show results - only show item count with filter status
    active_filters = []
    if filter_delivery:
        active_filters.append(f"LS: '{filter_delivery}'")
    if filter_article:
        active_filters.append(f"Artikel: '{filter_article}'")
    if filter_status:
        active_filters.append(f"Status: '{filter_status}'")

    if active_filters:
        st.info(f"📊 {len(filtered_items)} Artikel gefunden | Filter: {' | '.join(active_filters)}")
    else:
        st.info(f"📊 {len(filtered_items)} Artikel gefunden (keine Filter aktiv)")

    # Display table
    if filtered_items:
        # Table header with Status column after Chargen-Nr
        header_cols = st.columns([1.2, 1.5, 2.0, 0.8, 1.2, 1.5, 1.8, 3.0])
        header_labels = [
            "LS-Nr",
            "Artikel-Nr",
            "Chargen-Nr",
            "Menge",
            "WE-Datum",
            "Lieferant",
            "Status",
            "Aktionen",
        ]

        for col, label in zip(header_cols, header_labels):
            with col:
                st.markdown(f"**{label}**")

        st.divider()

        # Table rows - oldest first, newest last (as requested)
        for i, item in enumerate(filtered_items):
            row_cols = st.columns([1.2, 1.5, 2.0, 0.8, 1.2, 1.5, 1.8, 3.0])

            with row_cols[0]:
                st.markdown(f"`{item['delivery_number']}`")
            with row_cols[1]:
                st.markdown(f"`{item['article_number']}`")
            with row_cols[2]:
                # Truncate long batch numbers for compact display
                batch = item['batch_number']
                if len(batch) > 15:
                    st.markdown(f"`{batch[:12]}...`")
                else:
                    st.markdown(f"`{batch}`")
            with row_cols[3]:
                st.markdown(f"**{item['quantity']}**")
            with row_cols[4]:
                st.markdown(item['delivery_date'])
            with row_cols[5]:
                st.markdown(item['supplier'])
            with row_cols[6]:
                st.markdown(item['status'])

            # Action buttons column - 5 buttons wie in Admin-View
            with row_cols[7]:
                action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns(5)

                # Get individual step completion status from domain entity
                article_number = item.get("article_number")
                batch_number = item.get("batch_number")
                delivery_number = item.get("delivery_number")

                try:
                    from warehouse.domain.value_objects.article_number import ArticleNumber
                    from warehouse.domain.value_objects.batch_number import BatchNumber

                    item_service = st.session_state.services["item"]
                    article_vo = ArticleNumber(article_number)
                    batch_vo = BatchNumber(batch_number)

                    domain_item = item_service.item_repo.find_domain_by_composite_key(
                        article_vo, batch_vo, delivery_number
                    )

                    if domain_item:
                        data_completed = domain_item.is_step_completed("Daten prüfen")
                        docs_completed = domain_item.is_step_completed("Dokumente prüfen")
                        visual_completed = domain_item.is_step_completed("Sichtkontrolle")
                        measurement_completed = domain_item.is_step_completed("Vermessen")
                    else:
                        # Fallback wenn Item nicht gefunden
                        data_completed = False
                        docs_completed = False
                        visual_completed = False
                        measurement_completed = False

                except Exception as e:
                    # Fallback bei Fehler
                    data_completed = False
                    docs_completed = False
                    visual_completed = False
                    measurement_completed = False

                # Button 1: Daten bestätigen
                with action_col1:
                    if data_completed:
                        step1_emoji = "✅"
                        step1_help = "Daten bestätigt ✓"
                    else:
                        step1_emoji = "📋"
                        step1_help = "Daten bestätigen"

                    if st.button(step1_emoji, key=f"step1_{i}", help=step1_help, use_container_width=True):
                        # Prepare item data for popup - include all relevant fields
                        item_data = {
                            'article_number': item['article_number'],
                            'batch_number': item['batch_number'],
                            'delivery_number': item['delivery_number'],
                            'quantity': int(item['quantity']) if item['quantity'] != 'N/A' else 0,
                            'status': item.get('status', 'Pending'),
                            'supplier_name': item['supplier'],
                            'order_number': item.get('order_number', ''),
                            'storage_location': item.get('storage_location', ''),
                            'ordered_quantity': item.get('ordered_quantity', 0),
                            'delivery_slip_quantity': item.get('delivery_slip_quantity', 0),
                            'delivered_quantity': item.get('delivered_quantity', 0)
                        }
                        show_data_confirmation_popup(item_data)

                # Button 2: Dokumente prüfen
                with action_col2:
                    step2_enabled = data_completed

                    if docs_completed:
                        step2_emoji = "✅"
                        step2_help = "Dokumente geprüft ✓"
                        step2_disabled = False
                    elif step2_enabled:
                        step2_emoji = "📄"
                        step2_help = "Dokumente prüfen"
                        step2_disabled = False
                    else:
                        step2_emoji = "⏸️"
                        step2_help = "Warten auf Datenprüfung"
                        step2_disabled = True

                    if st.button(step2_emoji, key=f"step2_{i}", help=step2_help, use_container_width=True, disabled=step2_disabled):
                        # Load complete item data with certificates from database
                        item_service = services['item']
                        full_item_data = item_service.get_item(
                            item['article_number'],
                            item['batch_number'],
                            item['delivery_number']
                        )

                        # Prepare item data for popup with all fields including certificates
                        item_data = full_item_data if full_item_data else {
                            'article_number': item['article_number'],
                            'batch_number': item['batch_number'],
                            'delivery_number': item['delivery_number'],
                            'quantity': int(item['quantity']) if item['quantity'] != 'N/A' else 0,
                            'status': item.get('status', 'Pending'),
                            'supplier_name': item['supplier'],
                            'certificates': {}
                        }
                        # Ensure supplier_name is included (might be missing from get_item)
                        if 'supplier_name' not in item_data:
                            item_data['supplier_name'] = item['supplier']

                        show_document_check_popup(item_data)

                # Button 3: Vermessen
                with action_col3:
                    if measurement_completed:
                        measurement_emoji = "✅"
                        measurement_help = "Vermessung abgeschlossen ✓"
                    else:
                        measurement_emoji = "📏"
                        measurement_help = "Vermessung durchführen"

                    if st.button(measurement_emoji, key=f"measurement_{i}", help=measurement_help, use_container_width=True):
                        # Prepare item data for popup
                        item_data = {
                            'article_number': item['article_number'],
                            'batch_number': item['batch_number'],
                            'delivery_number': item['delivery_number'],
                            'quantity': int(item['quantity']) if item['quantity'] != 'N/A' else 0,
                            'status': item.get('status', 'Pending'),
                            'supplier_name': item['supplier']
                        }
                        show_measurement_popup(item_data)

                # Button 4: Sichtkontrolle
                with action_col4:
                    if visual_completed:
                        visual_emoji = "✅"
                        visual_help = "Sichtprüfung abgeschlossen ✓"
                    else:
                        visual_emoji = "👁️"
                        visual_help = "Sichtprüfung durchführen"

                    if st.button(visual_emoji, key=f"visual_check_{i}", help=visual_help, use_container_width=True):
                        # Prepare item data for popup
                        item_data = {
                            'article_number': item['article_number'],
                            'batch_number': item['batch_number'],
                            'delivery_number': item['delivery_number'],
                            'quantity': int(item['quantity']) if item['quantity'] != 'N/A' else 0,
                            'status': item.get('status', 'Pending'),
                            'supplier_name': item['supplier']
                        }
                        show_visual_inspection_popup(item_data)

                # Button 5: Dokumente zusammenführen
                with action_col5:
                    if st.button("📁", key=f"doc_merge_{i}", help="Dokumente zusammenführen", use_container_width=True):
                        # Prepare item data for popup
                        item_data = {
                            'article_number': item['article_number'],
                            'batch_number': item['batch_number'],
                            'delivery_number': item['delivery_number'],
                            'quantity': int(item['quantity']) if item['quantity'] != 'N/A' else 0,
                            'status': item.get('status', 'Pending'),
                            'supplier_name': item['supplier']
                        }
                        show_document_merge_popup(item_data)

    else:
        st.info("ℹ️ Keine Artikel gefunden.")


def handle_extraction_confirmation(services):
    """
    Verarbeitet die bestätigten Lieferschein-Daten und speichert sie in der Datenbank.
    """
    try:
        extraction_data = st.session_state.get("extraction_confirmed")
        if not extraction_data:
            st.error("Keine Extraktionsdaten gefunden")
            return

        # Get delivery service
        delivery_service = services.get("delivery")
        if not delivery_service:
            st.error("Delivery Service nicht verfügbar")
            return

        # Use the DeliveryService.create_delivery_from_extraction method
        result = delivery_service.create_delivery_from_extraction(extraction_data)

        if result.get("success"):
            success_message = f"Lieferung '{extraction_data.get('delivery_number')}' erfolgreich gespeichert!"
            if result.get("items_created", 0) > 0:
                success_message += f" {result.get('items_created')} Items erstellt."
            if result.get("items_failed", 0) > 0:
                success_message += f" {result.get('items_failed')} Items fehlgeschlagen."

            st.success(success_message)

            # Clean up session state
            st.session_state.popup_action = None
            if "extraction_confirmed" in st.session_state:
                del st.session_state.extraction_confirmed
            if "extracted_delivery_data" in st.session_state:
                del st.session_state.extracted_delivery_data

            # Rerun to update the item table
            st.rerun()
        else:
            st.error(
                f"Fehler beim Speichern: {result.get('error', 'Unbekannter Fehler')}"
            )

    except Exception as e:
        logger.error(f"Error handling extraction confirmation: {e}")
        st.error(f"Fehler beim Verarbeiten der Daten: {e}")
    finally:
        # Always clean up popup action
        if "popup_action" in st.session_state:
            st.session_state.popup_action = None
