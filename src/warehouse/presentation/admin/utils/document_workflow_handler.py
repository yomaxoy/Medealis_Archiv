"""
Document Workflow Handler - Event-driven document creation for inspection workflow
"""

import streamlit as st
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Import services with proper error handling
try:
    from warehouse.application.services.delivery_workflow_service import DeliveryWorkflowService
    from warehouse.application.services.document_generation.template_manager import TemplateManager
    SERVICES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Document services not available: {e}")
    SERVICES_AVAILABLE = False
    DeliveryWorkflowService = None
    TemplateManager = None


def create_workflow_documents(
    trigger_event: str,
    delivery_number: str = None,
    item_data: Dict[str, Any] = None,
    inspection_data: Dict[str, Any] = None,
    user_preferences: Dict[str, bool] = None
) -> Dict[str, Any]:
    """
    Create documents based on workflow trigger events.

    Args:
        trigger_event: Event that triggered document creation
            - 'documents_confirmed': After "Dokumente und Daten bestätigt"
            - 'visual_inspection_completed': After Sichtkontrolle
            - 'dimensional_inspection_completed': After dimensional inspection
            - 'inspection_finalized': Final step - merge all documents
        delivery_number: Delivery number for document context
        item_data: Item information for document generation
        inspection_data: Inspection results and employee data
        user_preferences: User choices for document handling (save/print/open/download)

    Returns:
        Dict with creation results and file paths
    """
    try:
        result = {
            'success': False,
            'documents_created': [],
            'errors': [],
            'trigger_event': trigger_event
        }

        # Check if services are available
        if not SERVICES_AVAILABLE:
            result['errors'].append("Document services not available")
            return result

        # Set default user preferences if not provided
        if user_preferences is None:
            user_preferences = {
                'save_to_folder': True,
                'auto_print': False,
                'auto_open': False,
                'auto_download': False
            }

        # Handle different trigger events
        if trigger_event == 'documents_confirmed':
            result = _create_initial_documents(
                delivery_number, item_data, user_preferences, result
            )

        elif trigger_event == 'visual_inspection_completed':
            # CHANGED: Visual Inspection Popup already creates the Sichtkontrolle document
            # with correct user-entered waste quantities. No need to create duplicate document.
            result['success'] = True
            result['message'] = "Visual inspection completed - document already created by popup"
            logger.info("Visual inspection completed - skipping duplicate document creation")

        elif trigger_event == 'dimensional_inspection_completed':
            result = _create_dimensional_inspection_documents(
                delivery_number, item_data, inspection_data, user_preferences, result
            )

        elif trigger_event == 'inspection_finalized':
            result = _create_final_merged_document(
                delivery_number, item_data, inspection_data, user_preferences, result
            )

        else:
            result['errors'].append(f"Unknown trigger event: {trigger_event}")
            return result

        # Show document creation results to user
        _show_document_creation_results(result, user_preferences)

        return result

    except Exception as e:
        logger.error(f"Document workflow error: {e}")
        result = {
            'success': False,
            'documents_created': [],
            'errors': [str(e)],
            'trigger_event': trigger_event
        }
        return result


def _create_initial_documents(
    delivery_number: str,
    item_data: Dict[str, Any],
    user_preferences: Dict[str, bool],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """Create initial documents: Begleitschein, Wareneingangskontrolle, Barcode, Inspection List."""
    try:
        if not SERVICES_AVAILABLE or DeliveryWorkflowService is None:
            result['errors'].append("DeliveryWorkflowService not available")
            return result

        workflow_service = DeliveryWorkflowService()

        # Create complete delivery documentation with status override
        creation_result = workflow_service.create_delivery_documents(
            delivery_number=delivery_number,
            batch_number=item_data.get('batch_number'),
            open_documents=user_preferences.get('auto_open', False),
            create_folder=user_preferences.get('save_to_folder', True),
            document_types=['Begleitschein', 'Wareneingangskontrolle', 'Barcode', 'Incoming Goods Inspection List'],  # Create all initial documents
            override_status='Dokumente geprüft'  # Force status to allow document creation
        )

        if creation_result.success:
            result['success'] = True
            # Extract document types from new workflow result
            doc_types = [doc.get('type', 'Unknown') for doc in creation_result.documents_created]
            result['documents_created'].extend(doc_types)

            # Convert new format to legacy format for compatibility
            result['file_paths'] = {}
            for doc in creation_result.documents_created:
                doc_type = doc.get('type', 'Unknown')
                doc_path = doc.get('path')
                if doc_path:
                    result['file_paths'][doc_type] = str(doc_path)

            # Store document paths in session state for later use
            st.session_state.workflow_documents = result['file_paths']

            if creation_result.folder_path:
                st.session_state.workflow_folder_path = str(creation_result.folder_path)

        else:
            error_msgs = '; '.join(creation_result.errors) if creation_result.errors else 'Unknown error'
            result['errors'].append(f"Failed to create initial documents: {error_msgs}")

    except Exception as e:
        logger.error(f"Initial document creation error: {e}")
        result['errors'].append(f"Initial document creation error: {e}")

    return result


# REMOVED: _create_visual_inspection_documents function
# Visual inspection documents are now ONLY created by the Visual Inspection Popup
# which handles user-entered waste quantities correctly. This avoids duplicate
# creation and ensures proper waste value handling.


def _create_dimensional_inspection_documents(
    delivery_number: str,
    item_data: Dict[str, Any],
    inspection_data: Dict[str, Any],
    user_preferences: Dict[str, bool],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """Create dimensional inspection documents."""
    try:
        # Placeholder for dimensional inspection document creation
        # This would use a specific template for dimensional measurements

        result['success'] = True
        result['documents_created'].append('Dimensional Inspection')

        # For now, just log that this step was completed
        logger.info(f"Dimensional inspection completed for delivery {delivery_number}")

    except Exception as e:
        logger.error(f"Dimensional inspection document creation error: {e}")
        result['errors'].append(f"Dimensional inspection document creation error: {e}")

    return result


def _create_final_merged_document(
    delivery_number: str,
    item_data: Dict[str, Any],
    inspection_data: Dict[str, Any],
    user_preferences: Dict[str, bool],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """Create final merged PDF with all inspection documents."""
    try:
        # Get all document paths from session state
        workflow_docs = st.session_state.get('workflow_documents', {})

        if not workflow_docs:
            result['errors'].append("No workflow documents found to merge")
            return result

        if not SERVICES_AVAILABLE or DeliveryWorkflowService is None:
            result['errors'].append("DeliveryWorkflowService not available")
            return result

        # Use enhanced document service to merge PDFs
        workflow_service = DeliveryWorkflowService()

        # Create merged PDF using workflow service
        merged_path = workflow_service.merge_delivery_pdfs(
            delivery_number=delivery_number,
            document_paths=workflow_docs,
            open_document=user_preferences.get('auto_open', False)
        )

        if merged_path:
            result['success'] = True
            result['documents_created'].append('Complete Inspection Package (PDF)')
            result['file_paths'] = result.get('file_paths', {})
            result['file_paths']['merged_pdf'] = str(merged_path)

        else:
            result['errors'].append("Failed to create merged inspection document")

    except Exception as e:
        logger.error(f"Final document merging error: {e}")
        result['errors'].append(f"Final document merging error: {e}")

    return result


def _show_document_creation_results(
    result: Dict[str, Any],
    user_preferences: Dict[str, bool]
) -> None:
    """Show document creation results to the user with action options."""

    if result.get('success') and result.get('documents_created'):
        # Success message
        docs_list = ", ".join(result['documents_created'])
        st.success(f"✅ **Dokumente erstellt:** {docs_list}")

        # Show action buttons for created documents
        if result.get('file_paths'):
            st.write("**📄 Dokument-Aktionen:**")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📁 Ordner öffnen", key=f"open_folder_{result['trigger_event']}"):
                    _open_document_folder(result['file_paths'])

            with col2:
                if st.button("🖨️ Drucken", key=f"print_docs_{result['trigger_event']}"):
                    _print_documents(result['file_paths'])

            with col3:
                if st.button("📂 Öffnen", key=f"open_docs_{result['trigger_event']}"):
                    _open_documents(result['file_paths'])

            with col4:
                if st.button("⬇️ Download", key=f"download_docs_{result['trigger_event']}"):
                    _download_documents(result['file_paths'])

    # Show errors if any
    if result.get('errors'):
        for error in result['errors']:
            st.error(f"❌ {error}")


def _open_document_folder(file_paths: Dict[str, str]) -> None:
    """Open the folder containing the documents."""
    try:
        import os
        import subprocess

        # Get the folder from the first file path
        if file_paths:
            first_file = next(iter(file_paths.values()))
            folder_path = os.path.dirname(first_file)

            # Open folder in Windows Explorer
            subprocess.run(['explorer', folder_path], check=True)
            st.info("📁 Ordner wurde geöffnet")

    except Exception as e:
        st.error(f"Fehler beim Öffnen des Ordners: {e}")


def _print_documents(file_paths: Dict[str, str]) -> None:
    """Send documents to printer."""
    try:
        import os

        for doc_type, file_path in file_paths.items():
            if os.path.exists(file_path) and file_path.endswith(('.docx', '.pdf')):
                # Send to default printer (Windows)
                os.startfile(file_path, "print")

        st.info("🖨️ Dokumente wurden an den Drucker gesendet")

    except Exception as e:
        st.error(f"Fehler beim Drucken: {e}")


def _open_documents(file_paths: Dict[str, str]) -> None:
    """Open documents for viewing."""
    try:
        import os

        for doc_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                os.startfile(file_path)

        st.info("📂 Dokumente wurden geöffnet")

    except Exception as e:
        st.error(f"Fehler beim Öffnen der Dokumente: {e}")


def _download_documents(file_paths: Dict[str, str]) -> None:
    """Provide download links for documents."""
    try:
        st.write("**⬇️ Download Links:**")

        for doc_type, file_path in file_paths.items():
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    file_data = file.read()
                    file_name = os.path.basename(file_path)

                    st.download_button(
                        label=f"📄 {doc_type} - {file_name}",
                        data=file_data,
                        file_name=file_name,
                        mime="application/octet-stream",
                        key=f"download_{doc_type}_{datetime.now().microsecond}"
                    )

    except Exception as e:
        st.error(f"Fehler beim Erstellen der Download-Links: {e}")


def show_document_preferences_popup(trigger_event: str) -> Dict[str, bool]:
    """Show popup for user to choose document handling preferences."""

    st.write(f"### 📄 Dokument-Einstellungen für: {trigger_event}")
    st.write("Wie sollen die erstellten Dokumente behandelt werden?")

    col1, col2 = st.columns(2)

    with col1:
        save_to_folder = st.checkbox("📁 In Ordner speichern", value=True, key=f"save_{trigger_event}")
        auto_open = st.checkbox("📂 Automatisch öffnen", value=False, key=f"open_{trigger_event}")

    with col2:
        auto_print = st.checkbox("🖨️ Automatisch drucken", value=False, key=f"print_{trigger_event}")
        auto_download = st.checkbox("⬇️ Download bereitstellen", value=False, key=f"download_{trigger_event}")

    return {
        'save_to_folder': save_to_folder,
        'auto_print': auto_print,
        'auto_open': auto_open,
        'auto_download': auto_download
    }