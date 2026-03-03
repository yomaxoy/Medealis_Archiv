"""
Dashboard View - Admin Presentation Layer
Main dashboard interface with system overview and statistics.

Performance Optimization:
- Uses @st.cache_data for statistics queries (60s TTL)
- Cache invalidation via CacheManager when entities change
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CACHED DATA LOADERS
# =============================================================================

@st.cache_data(ttl=60)
def _load_supplier_statistics(_service, _cache_version: int) -> Dict[str, Any]:
    """
    Load supplier statistics with caching.

    Args:
        _service: SupplierService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager

    Returns:
        Dict with supplier statistics
    """
    try:
        return _service.get_supplier_statistics()
    except Exception as e:
        logger.warning(f"Error loading supplier statistics: {e}")
        return {}


@st.cache_data(ttl=60)
def _load_delivery_statistics(_service, _cache_version: int) -> Dict[str, Any]:
    """
    Load delivery statistics with caching.

    Args:
        _service: DeliveryService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager

    Returns:
        Dict with delivery statistics
    """
    try:
        return _service.get_delivery_statistics()
    except Exception as e:
        logger.warning(f"Error loading delivery statistics: {e}")
        return {}


@st.cache_data(ttl=60)
def _load_item_statistics(_service, _cache_version: int) -> Dict[str, Any]:
    """
    Load item statistics with caching.

    Args:
        _service: ItemService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager

    Returns:
        Dict with item statistics
    """
    try:
        return _service.get_item_statistics()
    except Exception as e:
        logger.warning(f"Error loading item statistics: {e}")
        return {}


@st.cache_data(ttl=60)
def _load_order_statistics(_service, _cache_version: int) -> Dict[str, Any]:
    """
    Load order statistics with caching.

    Args:
        _service: OrderService (underscore = exclude from cache key)
        _cache_version: Cache version from CacheManager

    Returns:
        Dict with order statistics
    """
    try:
        return _service.get_order_statistics()
    except Exception as e:
        logger.warning(f"Error loading order statistics: {e}")
        return {}


def show_dashboard_view():
    """Show main dashboard with system overview and statistics."""
    st.header("📊 Dashboard")

    # Check system initialization
    if not st.session_state.get('system_initialized'):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get('services', {})
    if not services:
        st.error("Services nicht verfügbar")
        return

    # System status metrics
    show_system_status()

    # Service statistics
    show_service_statistics(services)

    # Delivery status visualization
    show_delivery_charts(services)

    # AI features warning
    show_ai_warning()


def show_system_status():
    """Display system status metrics."""
    col1, col2, col3, col4 = st.columns(4)

    try:
        # Import settings
        try:
            from config.settings import settings
            app_version = settings.APP_VERSION
        except ImportError:
            app_version = "2.0.0"

        with col1:
            st.metric("System Version", app_version)

        with col2:
            st.metric("Database", "✅ Connected")

        with col3:
            services = st.session_state.get('services', {})
            services_count = len([s for s in services.values() if s is not None])
            total_services = max(len(services), 4)  # Expected services count
            st.metric("Services", f"{services_count}/{total_services} Active")

        with col4:
            st.metric("Status", "🟢 Online")

    except Exception as e:
        logger.error(f"Error displaying system status: {e}")
        st.error(f"Fehler beim Laden des System-Status: {e}")


def show_service_statistics(services: Dict[str, Any]):
    """Display statistics from all services with caching."""
    try:
        # Import CacheManager for versioned caching
        from warehouse.presentation.shared.cache_manager import CacheManager

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if 'supplier' in services and services['supplier']:
                supplier_stats = _load_supplier_statistics(
                    services['supplier'],
                    CacheManager.get_version("suppliers")
                )
                st.metric("Suppliers", supplier_stats.get('total_suppliers', 0))
            else:
                st.metric("Suppliers", "N/A")

        with col2:
            if 'delivery' in services and services['delivery']:
                delivery_stats = _load_delivery_statistics(
                    services['delivery'],
                    CacheManager.get_version("deliveries")
                )
                st.metric("Deliveries", delivery_stats.get('total_deliveries', 0))
            else:
                st.metric("Deliveries", "N/A")

        with col3:
            if 'item' in services and services['item']:
                item_stats = _load_item_statistics(
                    services['item'],
                    CacheManager.get_version("items")
                )
                st.metric("Items", item_stats.get('total_items', 0))
            else:
                st.metric("Items", "N/A")

        with col4:
            if 'order' in services and services['order']:
                order_stats = _load_order_statistics(
                    services['order'],
                    CacheManager.get_version("orders")
                )
                st.metric("Orders", order_stats.get('total_orders', 0))
            else:
                st.metric("Orders", "N/A")

    except Exception as e:
        logger.error(f"Error displaying service statistics: {e}")
        st.error(f"Fehler beim Laden der Service-Statistiken: {e}")


def show_delivery_charts(services: Dict[str, Any]):
    """Display delivery status charts with caching."""
    st.subheader("📈 Delivery Status Overview")

    try:
        # Import CacheManager for versioned caching
        from warehouse.presentation.shared.cache_manager import CacheManager

        if 'delivery' in services and services['delivery']:
            delivery_stats = _load_delivery_statistics(
                services['delivery'],
                CacheManager.get_version("deliveries")
            )

            if delivery_stats and 'status_distribution' in delivery_stats:
                status_df = pd.DataFrame.from_dict(
                    delivery_stats['status_distribution'],
                    orient='index',
                    columns=['Count']
                )
                st.bar_chart(status_df)
            else:
                st.info("Keine Delivery-Daten verfügbar")
        else:
            st.info("Delivery Service nicht verfügbar")

    except Exception as e:
        logger.error(f"Error displaying delivery charts: {e}")
        st.error(f"Fehler beim Laden der Delivery-Charts: {e}")


def show_ai_warning():
    """Display warning about disabled AI features."""
    st.markdown("---")
    st.warning("⚠️ **AI-Features deaktiviert:** Claude halluziniert falsche Daten - verwenden Sie zuverlässige OCR-Extraktion.")