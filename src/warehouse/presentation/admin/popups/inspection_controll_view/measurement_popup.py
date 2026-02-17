"""
Measurement Popup
Popup for measurement inspections of items.
"""

import streamlit as st
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


def _save_measurement_protocols(
    uploaded_files: List[Any],
    item_data: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
    """
    Speichert hochgeladene Vermessungsprotokolle in den Artikelordner.

    Args:
        uploaded_files: Liste der hochgeladenen Dateien
        item_data: Item-Informationen (article_number, batch_number, etc.)

    Returns:
        Tuple (successful_saves, failed_saves)
    """
    from warehouse.application.services.document_storage.document_storage_service import DocumentStorageService

    storage_service = DocumentStorageService()
    successful_saves = []
    failed_saves = []

    for uploaded_file in uploaded_files:
        try:
            document_data = uploaded_file.read()
            uploaded_file.seek(0)

            measurement_filename = f"Vermessungsprotokoll_{item_data.get('article_number', 'UNKNOWN')}_{uploaded_file.name}"

            save_result = storage_service.save_document(
                document_data=document_data,
                document_name=measurement_filename,
                document_type="vermessungsprotokoll",
                batch_number=item_data.get('batch_number', ''),
                delivery_number=item_data.get('delivery_number', ''),
                article_number=item_data.get('article_number', ''),
                supplier_name=''
            )

            if save_result.success:
                successful_saves.append(uploaded_file.name)
                logger.info(f"Saved measurement protocol: {uploaded_file.name} to {save_result.file_path}")
            else:
                failed_saves.append(f"{uploaded_file.name}: {save_result.error}")
                logger.error(f"Failed to save {uploaded_file.name}: {save_result.error}")

        except Exception as file_error:
            failed_saves.append(f"{uploaded_file.name}: {str(file_error)}")
            logger.error(f"Error saving {uploaded_file.name}: {file_error}")

    return successful_saves, failed_saves


@st.dialog("📏 Vermessung durchführen")
def show_measurement_popup(item_data):
    """Show measurement popup with confirmation and future functionality buttons."""
    st.write("### 📏 Vermessung durchführen")
    st.write(f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}")
    st.write(f"**Lieferung:** {item_data['delivery_number']} | **Menge:** {item_data['quantity']}")

    st.write("---")

    # Vermessung bestätigen
    st.write("### ✅ Vermessung bestätigen")

    col1, col2 = st.columns(2)

    with col1:
        measurement_performed = st.selectbox(
            "📏 Vermessung durchgeführt:",
            ["Ja", "Nein"],
            index=0,
            key="measurement_performed",
            help="Wurde die Vermessung für diesen Artikel durchgeführt?"
        )

    with col2:
        measurement_date = st.date_input(
            "📅 Vermessungsdatum:",
            value=__import__('datetime').date.today(),
            key="measurement_date",
            help="Datum der Vermessung"
        )

    # Prüfer/Bearbeiter
    st.write("---")
    col_worker1, col_worker2 = st.columns(2)

    with col_worker1:
        measured_by = st.text_input(
            "👤 Vermessen durch:",
            value=st.session_state.get('current_user', ''),
            key="measured_by",
            help="Name des Mitarbeiters, der die Vermessung durchgeführt hat"
        )

    with col_worker2:
        measurement_notes = st.text_area(
            "📝 Vermessungsnotizen:",
            value="",
            key="measurement_notes",
            height=100,
            help="Zusätzliche Bemerkungen zur Vermessung (optional)"
        )

    st.write("---")

    # === ARTIKEL ORDNER ===
    st.write("**📁 Artikel-Ordner zum Speichern des Vermessungsprotokolls:**")

    # Zeige Artikel-Ordner Pfad und Button zum Öffnen
    try:
        from warehouse.application.services.document_storage.document_storage_service import DocumentStorageService

        # Use new DocumentStorageService to get folder path
        storage_service = DocumentStorageService()
        folder_path, warnings = storage_service.get_document_path(
            batch_number=item_data.get('batch_number', ''),
            delivery_number=item_data.get('delivery_number', ''),
            article_number=item_data.get('article_number', ''),
            supplier_name='',  # Will be resolved by storage service
            create_folders=False  # Don't create yet, just get path
        )

        # Show any warnings from path resolution
        if warnings:
            for warning in warnings:
                st.warning(f"⚠️ {warning}")

        col_path, col_open = st.columns([3, 1])
        with col_path:
            st.code(str(folder_path), language=None)
        with col_open:
            if st.button("📂 Ordner öffnen", key="measurement_open_folder_btn"):
                try:
                    # Erstelle Ordner falls nicht vorhanden
                    folder_path.mkdir(parents=True, exist_ok=True)

                    # Öffne Ordner im Explorer
                    import subprocess
                    import platform

                    if platform.system() == "Windows":
                        subprocess.run(['explorer', str(folder_path)], check=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(['open', str(folder_path)], check=True)
                    else:  # Linux
                        subprocess.run(['xdg-open', str(folder_path)], check=True)

                    st.success("📂 Ordner für Vermessungsprotokoll geöffnet!")
                except Exception as e:
                    st.error(f"❌ Fehler beim Öffnen des Ordners: {e}")

    except Exception as e:
        st.warning(f"⚠️ Ordner-Pfad konnte nicht ermittelt werden: {e}")

    # === VERMESSUNGSPROTOKOLL UPLOAD ===
    st.write("---")
    st.write("**📊 Vermessungsprotokoll hochladen:**")

    # File uploader for measurement protocol (always visible) - supports multiple files
    uploaded_measurement_doc = st.file_uploader(
        "Vermessungsprotokoll auswählen (Mehrfachauswahl möglich):",
        type=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'xlsx', 'xls'],
        key="popup_measurement_doc_upload",
        help="Vermessungsprotokolle werden in den Artikelordner gespeichert. Sie können mehrere Dateien gleichzeitig auswählen oder per Drag & Drop hochladen.",
        accept_multiple_files=True
    )

    if uploaded_measurement_doc:
        # Show uploaded documents info (multiple files)
        num_files = len(uploaded_measurement_doc)
        st.success(f"📊 {num_files} Vermessungsprotokoll{'e' if num_files > 1 else ''} hochgeladen")

        # Show details for each file
        for idx, uploaded_file in enumerate(uploaded_measurement_doc, 1):
            with st.expander(f"📄 {idx}. {uploaded_file.name}", expanded=False):
                st.write(f"📊 Dateigröße: {uploaded_file.size} bytes")
                st.write(f"📋 Dateityp: {uploaded_file.type}")

        st.info("ℹ️ Die Protokolle werden automatisch beim Klicken auf 'Vermessung bestätigen' gespeichert.")

    st.write("---")

    # Status Information
    if measurement_performed == "Ja":
        st.success("✅ Artikel wird als 'Vermessen' markiert")
    else:
        st.warning("⚠️ Artikel bleibt im aktuellen Status")

    # Aktions-Buttons
    st.write("### 🔧 Aktionen")

    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

    with col_btn1:
        if st.button("✅ Vermessung bestätigen", type="primary", use_container_width=True):
            """
            Bestätigt die Vermessung und speichert:
            1. Hochgeladene Vermessungsprotokolle (automatisch)
            2. Vermessungsstatus in der Datenbank
            """
            # Validierung
            if measurement_performed == "Ja" and not measured_by.strip():
                st.error("⚠️ Bitte geben Sie den Namen des Bearbeiters ein!")
                st.stop()

            # 1. Save uploaded measurement protocols FIRST (if any)
            if uploaded_measurement_doc:
                # Storage-Verfügbarkeits-Check VOR Dokumenten-Upload
                from warehouse.presentation.user.popups.components.storage_warning_dialog import (
                    check_and_show_storage_warning
                )

                can_continue = check_and_show_storage_warning(
                    batch_number=item_data.get('batch_number', ''),
                    delivery_number=item_data.get('delivery_number', ''),
                    article_number=item_data.get('article_number', ''),
                    supplier_name=item_data.get('supplier_name', ''),
                    compact=True
                )

                if not can_continue:
                    st.error("❌ Dokumenten-Upload abgebrochen - keine Speicher-Option verfügbar")
                    st.stop()

                try:
                    st.write("💾 Speichere Vermessungsprotokolle...")

                    # Use helper function to save protocols
                    successful_saves, failed_saves = _save_measurement_protocols(
                        uploaded_measurement_doc, item_data
                    )

                    if successful_saves:
                        st.success(f"✅ {len(successful_saves)} Vermessungsprotokoll{'e' if len(successful_saves) > 1 else ''} gespeichert!")
                        for filename in successful_saves:
                            st.info(f"  📄 {filename}")

                    if failed_saves:
                        st.error(f"❌ Fehler beim Speichern einiger Dateien:")
                        for fail in failed_saves:
                            st.error(f"  • {fail}")
                        # Don't stop - continue with measurement save

                except Exception as e:
                    logger.error(f"Error saving measurement protocols: {e}", exc_info=True)
                    st.warning(f"⚠️ Fehler beim Speichern der Protokolle: {e}")
                    # Don't stop - continue with measurement save

            # 2. Save measurement to database (if performed)
            if measurement_performed == "Ja":
                try:
                    from warehouse.application.services.entity_services.item_service import ItemService
                    import logging

                    logger = logging.getLogger(__name__)
                    item_service = ItemService()

                    # Prepare measurements dict
                    measurements_dict = {
                        'date': measurement_date.strftime('%Y-%m-%d'),
                        'notes': measurement_notes.strip() if measurement_notes else ''
                    }

                    # Call service to complete measurement
                    success = item_service.complete_measurement(
                        article_number=item_data['article_number'],
                        batch_number=item_data['batch_number'],
                        delivery_number=item_data['delivery_number'],
                        employee=measured_by.strip(),
                        measurements=measurements_dict
                    )

                    if not success:
                        st.error("❌ Fehler beim Speichern der Vermessung in DB")
                        return

                    st.success("✅ Vermessung erfolgreich abgeschlossen!")
                    logger.info(f"Measurement completed: {item_data['article_number']}#{item_data['batch_number']}#{item_data['delivery_number']}")

                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern: {e}")
                    import logging
                    logging.getLogger(__name__).error(f"Error saving measurement: {e}", exc_info=True)
                    return

            else:
                # Measurement not performed - just close popup
                st.info("ℹ️ Vermessung nicht durchgeführt - Status bleibt unverändert")

            # Clean up session state
            cleanup_keys = [
                'measurement_document_saved',
                'measurement_document_path',
                'measurement_document_paths',
                'confirmed_measurement_item',
                'popup_action'
            ]
            for key in cleanup_keys:
                if key in st.session_state:
                    del st.session_state[key]

            st.rerun()

    with col_btn2:
        if st.button("🏷️ QR-Code Drucken", use_container_width=True):
            st.info("🚧 QR-Code Druckfunktion wird später implementiert")
            st.write("**Geplante Funktionen:**")
            st.write("• QR-Code für Artikelverfolgung generieren")
            st.write("• Etiketten-Layout auswählen")
            st.write("• An Drucker senden")

    with col_btn3:
        if st.button("📊 Protokoll erstellen", use_container_width=True):
            st.info("🚧 Automatische Protokollerstellung wird später implementiert")
            st.write("**Geplante Funktionen:**")
            st.write("• Vermessungsprotokoll generieren")
            st.write("• PDF automatisch erstellen")
            st.write("• Im Artikel-Ordner speichern")

    with col_btn4:
        if st.button("❌ Abbrechen", use_container_width=True):
            # Clean up any uploaded files and states
            cleanup_keys = [
                'measurement_document_saved',
                'measurement_document_path'
            ]
            for key in cleanup_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()