# Admin views
from .dashboard_view import show_dashboard_view
from .orders_view import show_orders_view
from .supplier_management_view import show_supplier_management_view
from .item_management_view import show_item_management_view
from .delivery_management_view import show_delivery_management_view
from .inspection_control_view import show_inspection_control_view
from .user_management_view import show_user_management_view

__all__ = [
    'show_dashboard_view',
    'show_orders_view',
    'show_supplier_management_view',
    'show_item_management_view',
    'show_delivery_management_view',
    'show_inspection_control_view',
    'show_user_management_view',
]