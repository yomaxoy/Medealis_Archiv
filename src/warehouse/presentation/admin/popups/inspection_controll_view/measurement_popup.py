"""
Measurement Popup
Popup for measurement inspections of items.
"""

import streamlit as st


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

        # Simple save button (no AI analysis needed)
        if st.button("💾 Alle Protokolle speichern", key="save_measurement_doc_btn", use_container_width=True, type="primary"):
            # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR Dokumenten-Upload
            from warehouse.presentation.user.popups.components.storage_warning_dialog import (
                check_and_show_storage_warning
            )

            # Zeige Warnung wenn Server nicht verfügbar
            can_continue = check_and_show_storage_warning(
                batch_number=item_data.get('batch_number', ''),
                delivery_number=item_data.get('delivery_number', ''),
                article_number=item_data.get('article_number', ''),
                supplier_name=item_data.get('supplier_name', ''),
                compact=True  # Kompakte Warnung
            )

            if not can_continue:
                st.error("❌ Dokumenten-Upload abgebrochen - keine Speicher-Option verfügbar")
            else:
                try:
                    # Import new document storage service
                    from warehouse.application.services.document_storage.document_storage_service import DocumentStorageService

                    storage_service = DocumentStorageService()

                    # Track results
                    successful_saves = []
                    failed_saves = []
                    all_warnings = []

                    # Process each uploaded file
                    for uploaded_file in uploaded_measurement_doc:
                        try:
                            # Read document data
                            document_data = uploaded_file.read()
                            uploaded_file.seek(0)  # Reset file pointer

                            # Create safe filename for measurement protocol
                            measurement_filename = f"Vermessungsprotokoll_{item_data.get('article_number', 'UNKNOWN')}_{uploaded_file.name}"

                            # Use new DocumentStorageService to save document
                            save_result = storage_service.save_document(
                                document_data=document_data,
                                document_name=measurement_filename,
                                document_type="vermessungsprotokoll",
                                batch_number=item_data.get('batch_number', ''),
                                delivery_number=item_data.get('delivery_number', ''),
                                article_number=item_data.get('article_number', ''),
                                supplier_name=''  # Will be resolved by storage service
                            )

                            if save_result.success:
                                successful_saves.append({
                                    'filename': uploaded_file.name,
                                    'path': save_result.file_path
                                })

                                # Collect warnings
                                if save_result.warnings:
                                    all_warnings.extend(save_result.warnings)
                            else:
                                failed_saves.append({
                                    'filename': uploaded_file.name,
                                    'error': save_result.error
                                })

                                # Collect warnings
                                if save_result.warnings:
                                    all_warnings.extend(save_result.warnings)

                        except Exception as file_error:
                            failed_saves.append({
                                'filename': uploaded_file.name,
                                'error': str(file_error)
                            })

                    # Show results summary
                    if successful_saves:
                        st.success(f"✅ {len(successful_saves)} von {len(uploaded_measurement_doc)} Vermessungsprotokoll{'en' if len(uploaded_measurement_doc) > 1 else ''} erfolgreich gespeichert!")

                        # Show each successful save
                        for save_info in successful_saves:
                            st.info(f"📁 {save_info['filename']} → {save_info['path']}")

                        # Store success info in session state
                        st.session_state.measurement_document_saved = True
                        st.session_state.measurement_document_paths = [s['path'] for s in successful_saves]

                    if failed_saves:
                        st.error(f"❌ {len(failed_saves)} Datei{'en' if len(failed_saves) > 1 else ''} konnte{'n' if len(failed_saves) > 1 else ''} nicht gespeichert werden:")
                        for fail_info in failed_saves:
                            st.error(f"  • {fail_info['filename']}: {fail_info['error']}")

                    # Show any warnings
                    if all_warnings:
                        for warning in set(all_warnings):  # Remove duplicates
                            st.warning(f"⚠️ {warning}")

                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern der Vermessungsprotokolle: {e}")
                    import traceback
                    st.error(f"Debug: {traceback.format_exc()}")

        # Clear document button
        st.write("")  # spacer
        if st.button("❌ Protokoll entfernen", key="remove_measurement_doc_btn", use_container_width=False):
            # Clear the uploaded document but keep popup open
            if 'measurement_document_saved' in st.session_state:
                del st.session_state['measurement_document_saved']
            if 'measurement_document_path' in st.session_state:
                del st.session_state['measurement_document_path']
            # Don't rerun to keep popup open, just clear the file

        # Show success message if document was saved (but no uploaded file currently)
        if st.session_state.get('measurement_document_saved', False) and not uploaded_measurement_doc:
            st.success("✅ Vermessungsprotokoll wurde erfolgreich im Artikelordner gespeichert!")
            # Reset the upload area for another document
            if st.button("📊 Weiteres Protokoll hochladen", key="upload_another_measurement_btn"):
                st.session_state.measurement_document_saved = False
                # Upload area stays visible, no rerun needed

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
            # Validierung
            if measurement_performed == "Ja" and not measured_by.strip():
                st.error("⚠️ Bitte geben Sie den Namen des Bearbeiters ein!")
                st.stop()

            # Save measurement to database (ALWAYS if performed)
            if measurement_performed == "Ja":
                try:
                    from warehouse.application.services.entity_services.item_service import ItemService
                    import logging

                    logger = logging.getLogger(__name__)
                    item_service = ItemService()

                    # Prepare measurements dict (currently simple, can be extended later)
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

            # Clean up session state (fallback if needed)
            cleanup_keys = [
                'measurement_document_saved',
                'measurement_document_path',
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