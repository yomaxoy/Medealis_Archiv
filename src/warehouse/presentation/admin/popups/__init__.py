# Admin popups

# Core CRUD Popups
# Temporarily commented out due to import-time @st.dialog decorator issues
# from .order_view.order_popups import (
#     show_order_edit_popup,
#     show_order_delete_popup,
#     show_order_details_popup,
#     show_order_statistics_popup,
# )
from .supplier_view.supplier_popups import (
    show_supplier_confirmation_popup,
    show_supplier_edit_popup,
    show_supplier_delete_popup,
    show_supplier_details_popup,
    show_supplier_statistics_popup,
)
from .item_view.item_popups import (
    show_item_confirmation_popup,
    show_item_edit_popup,
    show_item_delete_popup,
    show_item_details_popup,
    show_batch_tracking_popup,
)
from .delivery_view.delivery_popups import (
    show_delivery_confirmation_popup,
    show_delivery_edit_popup,
    show_delivery_delete_popup,
    show_scan_delivery_slip_popup,
    show_delivery_success_popup,
    show_delivery_error_popup,
    show_extraction_confirmation_popup,
)

# Workflow Popups
from .view_independent.workflow_popups import (
    show_ls_data_confirmation_popup,
    show_ls_confirmation_popup,
    show_finalize_popup,
    handle_workflow_popup_actions,
)

# Inspection and Quality Control Popups
from .inspection_controll_view.enhanced_document_check_popup import (
    show_document_check_popup_new,
    handle_document_check_popup_actions,
)
from .inspection_controll_view.document_check_popup import show_document_check_popup
from .inspection_controll_view.visual_inspection_popup import show_visual_inspection_popup
from .inspection_controll_view.measurement_popup import show_measurement_popup
from .inspection_controll_view.document_merge_popup import show_document_merge_popup
from .inspection_controll_view.data_confirmation_step1_popup import (
    show_data_confirmation_step1_popup,
)
from .inspection_controll_view.document_confirmation_step2_popup import (
    show_document_confirmation_step2_popup,
)

# Utility and System Popups
from .view_independent.utility_popups import (
    show_success_popup,
    show_error_popup,
    show_debug_information,
    handle_utility_popup_actions,
)

__all__ = [
    # Order popups - temporarily disabled due to import issues
    # "show_order_edit_popup",
    # "show_order_delete_popup",
    # "show_order_details_popup",
    # "show_order_statistics_popup",
    # Supplier popups
    "show_supplier_confirmation_popup",
    "show_supplier_edit_popup",
    "show_supplier_delete_popup",
    "show_supplier_details_popup",
    "show_supplier_statistics_popup",
    # Item popups
    "show_item_confirmation_popup",
    "show_item_edit_popup",
    "show_item_delete_popup",
    "show_item_details_popup",
    "show_batch_tracking_popup",
    # Delivery popups
    "show_delivery_confirmation_popup",
    "show_delivery_edit_popup",
    "show_delivery_delete_popup",
    "show_scan_delivery_slip_popup",
    "show_delivery_success_popup",
    "show_delivery_error_popup",
    "show_extraction_confirmation_popup",
    # Workflow popups
    "show_ls_data_confirmation_popup",
    "show_ls_confirmation_popup",
    "show_finalize_popup",
    "handle_workflow_popup_actions",
    # Inspection popups
    "show_document_check_popup_new",
    "handle_document_check_popup_actions",
    "show_document_check_popup",
    "show_visual_inspection_popup",
    "show_measurement_popup",
    "show_document_merge_popup",
    "show_data_confirmation_step1_popup",
    "show_document_confirmation_step2_popup",
    # Utility popups
    "show_success_popup",
    "show_error_popup",
    "show_debug_information",
    "handle_utility_popup_actions",
]
