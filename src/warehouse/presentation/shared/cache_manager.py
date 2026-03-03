"""
Cache Manager - Event-based Cache Invalidation for Streamlit

This module provides centralized cache management for the Medealis Warehouse System.
It ensures data consistency by invalidating caches when entities are modified.

Usage:
    from warehouse.presentation.shared.cache_manager import CacheManager

    # In view - load data with cache versioning:
    @st.cache_data(ttl=60)
    def _load_deliveries(_service, _version):
        return _service.get_all_deliveries()

    deliveries = _load_deliveries(
        delivery_service,
        CacheManager.get_version("deliveries")
    )

    # After save/delete - invalidate related caches:
    if save_button_clicked:
        delivery_service.save(data)
        CacheManager.invalidate_related("deliveries")
        st.rerun()
"""

import streamlit as st
import logging
from typing import Literal, List

logger = logging.getLogger(__name__)

EntityType = Literal[
    "deliveries",
    "items",
    "suppliers",
    "orders",
    "documents",
    "users",
    "item_info",
]


class CacheManager:
    """
    Centralized cache manager for Streamlit caching with event-based invalidation.

    This class manages cache versions per entity type and provides methods to
    invalidate caches when entities are modified (create/update/delete).

    Cache versioning works by incrementing a version number in session_state
    whenever an entity is modified. Since the version is part of the cache key,
    incrementing it forces Streamlit to rebuild the cache.

    Architecture:
        - Each entity type has a version counter in session_state
        - Cached functions include the version in their cache key
        - Modifying an entity increments its version → cache is invalidated
        - Related entities (e.g., items when deliveries change) are also invalidated
    """

    # Entity types and their dependencies
    ENTITIES: List[EntityType] = [
        "deliveries",
        "items",
        "suppliers",
        "orders",
        "documents",
        "users",
        "item_info",
    ]

    # Dependency graph: which entities to invalidate when an entity changes
    RELATIONS = {
        "deliveries": ["items", "documents"],  # Delivery change → items/docs change
        "items": ["deliveries", "documents"],  # Item change → delivery/docs change
        "suppliers": ["deliveries"],  # Supplier change → deliveries change
        "orders": ["items"],  # Order change → items might change
        "documents": [],  # Document change → no cascading invalidation
        "users": [],  # User change → no cascading invalidation
        "item_info": ["items"],  # ItemInfo change → items change
    }

    @staticmethod
    def get_version(entity: EntityType) -> int:
        """
        Get current cache version for an entity type.

        Args:
            entity: Entity type (deliveries, items, suppliers, etc.)

        Returns:
            int: Current version number (0 if not yet set)

        Example:
            >>> version = CacheManager.get_version("deliveries")
            >>> deliveries = load_deliveries_cached(service, version)
        """
        key = f"_cache_v_{entity}"
        if key not in st.session_state:
            st.session_state[key] = 0
        return st.session_state[key]

    @staticmethod
    def invalidate(entity: EntityType):
        """
        Invalidate cache for a single entity type.

        Increments the version counter, forcing cached functions that use
        this version to rebuild their cache.

        Args:
            entity: Entity type to invalidate

        Example:
            >>> CacheManager.invalidate("deliveries")
            # All @st.cache_data functions using get_version("deliveries")
            # will rebuild their cache on next access
        """
        key = f"_cache_v_{entity}"
        current_version = st.session_state.get(key, 0)
        st.session_state[key] = current_version + 1
        logger.debug(f"Cache invalidated: {entity} (version {current_version} → {current_version + 1})")

    @staticmethod
    def invalidate_related(entity: EntityType):
        """
        Invalidate cache for an entity AND all related entities.

        This is the recommended method to call after modifying an entity,
        as it ensures data consistency across dependent entities.

        Example:
            - New delivery created → invalidate deliveries + items + documents
            - Item edited → invalidate items + deliveries + documents
            - Supplier edited → invalidate suppliers + deliveries

        Args:
            entity: Entity type that was modified

        Example:
            >>> # After saving a new delivery:
            >>> delivery_service.save(delivery_data)
            >>> CacheManager.invalidate_related("deliveries")
            >>> st.rerun()  # Reload page with fresh cache
        """
        # Invalidate the entity itself
        CacheManager.invalidate(entity)

        # Invalidate all related entities
        related = CacheManager.RELATIONS.get(entity, [])
        for related_entity in related:
            CacheManager.invalidate(related_entity)

        if related:
            logger.debug(f"Cache invalidation cascade: {entity} → {related}")

    @staticmethod
    def invalidate_all():
        """
        Invalidate ALL entity caches.

        Use this sparingly - only when necessary (e.g., bulk import, system reset).
        Prefer invalidate_related() for specific entity changes.

        Example:
            >>> # After bulk import of deliveries:
            >>> import_service.bulk_import(csv_data)
            >>> CacheManager.invalidate_all()
            >>> st.rerun()
        """
        for entity in CacheManager.ENTITIES:
            CacheManager.invalidate(entity)
        logger.info("All caches invalidated (global invalidation)")

    @staticmethod
    def clear_streamlit_caches():
        """
        Clear all Streamlit built-in caches (@st.cache_data and @st.cache_resource).

        This is a more aggressive approach than version-based invalidation.
        Use only when version-based invalidation doesn't work (e.g., debugging).

        Example:
            >>> # Emergency cache clear:
            >>> CacheManager.clear_streamlit_caches()
            >>> st.rerun()
        """
        st.cache_data.clear()
        st.cache_resource.clear()
        logger.warning("All Streamlit caches cleared (nuclear option)")


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def _example_usage():
    """
    Example usage patterns for CacheManager.

    This function is not called - it's documentation showing how to use CacheManager.
    """

    # Example 1: Cached data loading
    @st.cache_data(ttl=60)
    def _load_deliveries(_service, _version: int):
        """
        Load all deliveries with cache versioning.

        Args:
            _service: DeliveryService instance (underscore = exclude from cache key)
            _version: Cache version (from CacheManager.get_version("deliveries"))
        """
        return _service.get_all_deliveries()

    # In your view:
    # services = st.session_state.services
    # deliveries = _load_deliveries(
    #     services["delivery"],
    #     CacheManager.get_version("deliveries")
    # )

    # Example 2: After saving/creating
    # if st.button("Speichern"):
    #     delivery_service.save(delivery_data)
    #     CacheManager.invalidate_related("deliveries")
    #     st.success("Gespeichert!")
    #     st.rerun()

    # Example 3: After deleting
    # if st.button("Löschen"):
    #     delivery_service.delete(delivery_id)
    #     CacheManager.invalidate_related("deliveries")
    #     st.success("Gelöscht!")
    #     st.rerun()

    # Example 4: After bulk import
    # if st.button("Import"):
    #     import_service.bulk_import(csv_data)
    #     CacheManager.invalidate_all()  # Many entities changed
    #     st.success("Importiert!")
    #     st.rerun()

    pass
