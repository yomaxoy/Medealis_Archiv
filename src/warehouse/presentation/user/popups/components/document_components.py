"""
Document Components
Components for document upload, folder management, and AI analysis.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def render_document_uploader(
    label: str,
    key: str,
    file_types: Optional[List[str]] = None,
    accept_multiple: bool = False,
    help_text: Optional[str] = None,
    show_ai_analysis: bool = False,
    ai_analysis_callback: Optional[Callable] = None
) -> Optional[List]:
    """
    Rendert einen standardisierten Dokumenten-Uploader.

    Args:
        label: Label für den Uploader
        key: Unique key für Session-State
        file_types: Erlaubte Dateitypen (default: ['pdf', 'png', 'jpg', 'docx'])
        accept_multiple: Mehrfachauswahl erlauben
        help_text: Hilfetext
        show_ai_analysis: Zeigt KI-Analyse-Button
        ai_analysis_callback: Callback-Funktion für KI-Analyse (file, index) -> None

    Returns:
        Liste der hochgeladenen Dateien oder None

    Beispiel:
        ```python
        def analyze_document(file, idx):
            st.info(f"Analysiere {file.name}...")
            # KI-Analyse-Logik hier

        files = render_document_uploader(
            label="Vermessungsprotokoll hochladen",
            key="measurement_upload",
            accept_multiple=True,
            show_ai_analysis=True,
            ai_analysis_callback=analyze_document
        )
        ```
    """
    if file_types is None:
        file_types = ['pdf', 'png', 'jpg', 'jpeg', 'docx']

    st.markdown(f"#### 📤 {label}")

    uploaded_files = st.file_uploader(
        label,
        type=file_types,
        accept_multiple_files=accept_multiple,
        key=key,
        help=help_text or f"Unterstützte Formate: {', '.join(file_types.upper())}",
        label_visibility="collapsed"
    )

    if not uploaded_files:
        return None

    # Konvertiere zu Liste (auch wenn nur eine Datei)
    files_list = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]

    # Erfolgs-Meldung
    num_files = len(files_list)
    st.success(f"📄 {num_files} Dokument{'e' if num_files > 1 else ''} hochgeladen")

    # Zeige Datei-Details
    for idx, file in enumerate(files_list):
        with st.expander(f"📄 {idx + 1}. {file.name}", expanded=False):
            st.write(f"**Größe:** {_format_file_size(file.size)}")
            st.write(f"**Typ:** {file.type}")

            # KI-Analyse Button (optional)
            if show_ai_analysis and ai_analysis_callback:
                if st.button(
                    "🤖 KI-Analyse starten",
                    key=f"{key}_ai_analysis_{idx}",
                    type="primary",
                    use_container_width=True
                ):
                    try:
                        ai_analysis_callback(file, idx)
                    except Exception as e:
                        st.error(f"❌ Fehler bei KI-Analyse: {e}")
                        logger.error(f"AI analysis failed: {e}", exc_info=True)

    return files_list


def render_folder_path(
    article_number: str,
    batch_number: str,
    delivery_number: str,
    show_open_button: bool = True,
    create_if_missing: bool = True
) -> Optional[str]:
    """
    Rendert Ordner-Pfad mit "Ordner öffnen"-Button.

    Args:
        article_number: Artikelnummer
        batch_number: Chargennummer
        delivery_number: Lieferscheinnummer
        show_open_button: Zeigt "Ordner öffnen" Button
        create_if_missing: Erstellt Ordner falls nicht vorhanden

    Returns:
        Ordner-Pfad als String oder None bei Fehler

    Beispiel:
        ```python
        folder = render_folder_path(
            article_number="MG0001",
            batch_number="BATCH-123",
            delivery_number="LS-001"
        )
        ```
    """
    try:
        from warehouse.application.services.service_registry import get_document_storage_service

        st.markdown("#### 📁 Artikel-Ordner")

        storage_service = get_document_storage_service()
        folder_path, warnings = storage_service.get_document_path(
            batch_number=batch_number,
            delivery_number=delivery_number,
            article_number=article_number,
            create_folders=create_if_missing
        )

        # Zeige Warnings
        for warning in warnings:
            st.caption(f"⚠️ {warning}")

        # Layout: Pfad + Button
        col_path, col_button = st.columns([3, 1])

        with col_path:
            st.code(str(folder_path), language=None)

        with col_button:
            if show_open_button:
                if st.button(
                    "📂 Öffnen",
                    key=f"open_folder_{article_number}_{batch_number}",
                    use_container_width=True
                ):
                    _open_folder_in_explorer(folder_path)

        return str(folder_path)

    except Exception as e:
        st.warning(f"⚠️ Ordner-Pfad konnte nicht ermittelt werden: {e}")
        logger.error(f"Failed to get folder path: {e}", exc_info=True)
        return None


def render_document_list(
    documents: List[Dict[str, Any]],
    show_actions: bool = True,
    on_delete: Optional[Callable[[int], None]] = None,
    on_download: Optional[Callable[[int], None]] = None
) -> None:
    """
    Rendert eine Liste von Dokumenten mit optionalen Actions.

    Args:
        documents: Liste von Dokumenten [{name, type, size, path}]
        show_actions: Zeigt Action-Buttons (Löschen, Download)
        on_delete: Callback für Löschen (index) -> None
        on_download: Callback für Download (index) -> None

    Beispiel:
        ```python
        docs = [
            {"name": "doc1.pdf", "type": "PDF", "size": 12345, "path": "/path/to/doc1.pdf"},
            {"name": "doc2.docx", "type": "DOCX", "size": 67890, "path": "/path/to/doc2.docx"}
        ]

        render_document_list(
            documents=docs,
            on_delete=lambda idx: delete_document(docs[idx])
        )
        ```
    """
    if not documents:
        st.info("📄 Keine Dokumente vorhanden")
        return

    st.markdown(f"#### 📄 Dokumente ({len(documents)})")

    for idx, doc in enumerate(documents):
        with st.container():
            col_icon, col_name, col_info, col_actions = st.columns([1, 4, 2, 2])

            with col_icon:
                icon = _get_document_icon(doc.get('type', ''))
                st.write(icon)

            with col_name:
                st.write(f"**{doc['name']}**")

            with col_info:
                size_str = _format_file_size(doc.get('size', 0))
                st.caption(f"{doc.get('type', 'Unknown')} • {size_str}")

            with col_actions:
                if show_actions:
                    col_del, col_down = st.columns(2)

                    with col_del:
                        if on_delete and st.button(
                            "🗑️",
                            key=f"delete_doc_{idx}",
                            help="Dokument löschen"
                        ):
                            on_delete(idx)

                    with col_down:
                        if on_download and st.button(
                            "⬇️",
                            key=f"download_doc_{idx}",
                            help="Dokument herunterladen"
                        ):
                            on_download(idx)

            st.divider()


# ============== Helper Functions ==============

def _open_folder_in_explorer(folder_path: Any) -> None:
    """
    Öffnet Ordner im System-Explorer.

    Args:
        folder_path: Pfad zum Ordner (str oder Path)
    """
    import platform
    import subprocess

    try:
        path_obj = Path(folder_path)
        path_obj.mkdir(parents=True, exist_ok=True)

        if platform.system() == "Windows":
            subprocess.run(['explorer', str(path_obj)], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(['open', str(path_obj)], check=True)
        else:  # Linux
            subprocess.run(['xdg-open', str(path_obj)], check=True)

        st.success("📂 Ordner geöffnet!")

    except Exception as e:
        st.error(f"❌ Fehler beim Öffnen: {e}")
        logger.error(f"Failed to open folder: {e}", exc_info=True)


def _format_file_size(size_bytes: int) -> str:
    """
    Formatiert Dateigröße in lesbares Format.

    Args:
        size_bytes: Größe in Bytes

    Returns:
        Formatierte Größe (z.B. "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def _get_document_icon(doc_type: str) -> str:
    """
    Gibt passendes Icon für Dokumenttyp zurück.

    Args:
        doc_type: Dokumenttyp (z.B. 'PDF', 'DOCX')

    Returns:
        Emoji-Icon
    """
    doc_type_lower = doc_type.lower()

    icon_map = {
        'pdf': '📕',
        'docx': '📘',
        'doc': '📘',
        'xlsx': '📗',
        'xls': '📗',
        'pptx': '📙',
        'ppt': '📙',
        'txt': '📄',
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'gif': '🖼️',
    }

    return icon_map.get(doc_type_lower, '📄')


def save_uploaded_document(
    uploaded_file: Any,
    article_number: str,
    batch_number: str,
    delivery_number: str,
    document_type: str = "generic",
    filename_prefix: str = ""
) -> Dict[str, Any]:
    """
    Speichert hochgeladenes Dokument mit DocumentStorageService.

    Args:
        uploaded_file: Streamlit UploadedFile
        article_number: Artikelnummer
        batch_number: Chargennummer
        delivery_number: Lieferscheinnummer
        document_type: Typ des Dokuments (z.B. 'vermessungsprotokoll')
        filename_prefix: Prefix für Dateiname (optional)

    Returns:
        Dict mit Save-Result: {success: bool, file_path: str, error: str}

    Beispiel:
        ```python
        result = save_uploaded_document(
            uploaded_file=file,
            article_number="MG0001",
            batch_number="BATCH-123",
            delivery_number="LS-001",
            document_type="vermessungsprotokoll",
            filename_prefix="Vermessungsprotokoll"
        )

        if result['success']:
            st.success(f"Gespeichert: {result['file_path']}")
        else:
            st.error(result['error'])
        ```
    """
    try:
        from warehouse.application.services.service_registry import get_document_storage_service

        storage_service = get_document_storage_service()

        # Read document data
        document_data = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer

        # Create filename
        if filename_prefix:
            filename = f"{filename_prefix}_{article_number}_{uploaded_file.name}"
        else:
            filename = f"{document_type}_{article_number}_{uploaded_file.name}"

        # Save document
        save_result = storage_service.save_document(
            document_data=document_data,
            document_name=filename,
            document_type=document_type,
            batch_number=batch_number,
            delivery_number=delivery_number,
            article_number=article_number,
            supplier_name=""  # Will be resolved by storage service
        )

        if save_result.success:
            return {
                'success': True,
                'file_path': str(save_result.file_path),
                'error': None
            }
        else:
            return {
                'success': False,
                'file_path': None,
                'error': save_result.error
            }

    except Exception as e:
        logger.error(f"Failed to save document: {e}", exc_info=True)
        return {
            'success': False,
            'file_path': None,
            'error': str(e)
        }
