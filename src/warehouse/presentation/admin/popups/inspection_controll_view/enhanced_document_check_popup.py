"""
Enhanced Document Check Popup - Admin Presentation Layer
Advanced document checking popup with upload and validation functionality.
"""

import streamlit as st
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import subprocess
import platform

logger = logging.getLogger(__name__)


@st.dialog("📋 Wareneingangsdokumentation prüfen")
def show_document_check_popup_new(item_data: Dict[str, Any]):
    """Show document check popup with upload and validation functionality."""
    st.write(f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}")
    st.write(f"**Lieferung:** {item_data['delivery_number']} | **Menge:** {item_data['quantity']}")

    st.write("---")

    # Ordnerpfad anzeigen
    folder_path = None
    try:
        from warehouse.application.services import determine_manufacturer
        from warehouse.application.services.document_storage import DocumentStorageService

        # Bestimme Hersteller für Pfad
        manufacturer = determine_manufacturer(item_data['article_number'])
        supplier_name = "Primec"  # Default, später aus DB holen

        storage_service = DocumentStorageService()
        folder_path = storage_service.get_delivery_folder_path(
            supplier_name=supplier_name,
            manufacturer=manufacturer,
            article_number=item_data['article_number'],
            batch_number=item_data['batch_number'],
            delivery_number=item_data['delivery_number']
        )

        st.write(f"**📂 Dokumentenordner:** `{folder_path}`")

        # Prüfe ob Ordner existiert
        if folder_path.exists():
            # Zeige Inhalt des Ordners
            files = list(folder_path.glob('*'))
            document_files = [f for f in files if f.is_file()]

            if document_files:
                st.write(f"**📄 {len(document_files)} Datei(en) gefunden:**")
                for file in sorted(document_files):
                    file_size = file.stat().st_size
                    size_str = f"({file_size:,} bytes)" if file_size < 1024 else f"({file_size/1024:.1f} KB)"
                    st.write(f"• {file.name} {size_str}")
            else:
                st.info("📁 Ordner existiert, aber keine Dateien gefunden")
        else:
            st.warning("❌ Dokumentenordner existiert noch nicht")

    except Exception as e:
        st.error(f"❌ Fehler beim Laden des Ordnerpfads: {e}")
        folder_path = None

    st.write("---")

    # Dokumentenstatus
    st.write("### 📊 Dokumentenstatus")

    col_status1, col_status2 = st.columns(2)

    with col_status1:
        if folder_path and folder_path.exists():
            files = list(folder_path.glob('*'))
            document_files = [f for f in files if f.is_file()]
            st.metric("Dateien im Ordner", len(document_files))
        else:
            st.metric("Dateien im Ordner", 0)

    with col_status2:
        # Zeige letzten Upload-Zeitpunkt (falls verfügbar)
        if folder_path and folder_path.exists():
            try:
                folder_mod_time = folder_path.stat().st_mtime
                mod_datetime = datetime.fromtimestamp(folder_mod_time)
                st.metric("Letzter Upload", mod_datetime.strftime("%Y-%m-%d %H:%M"))
            except:
                st.metric("Letzter Upload", "Unbekannt")
        else:
            st.metric("Letzter Upload", "Kein Ordner")

    st.write("---")

    # Aktions-Buttons
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

    with col_btn1:
        if st.button("📤 Dokumente hochladen", use_container_width=True):
            # Ordner öffnen für Upload-Zwecke
            if folder_path and folder_path.exists():
                try:
                    _open_folder_in_explorer(folder_path)
                    st.success("✅ Ordner für Upload geöffnet!")
                    st.info("💡 Ziehen Sie die Dokumente in den geöffneten Ordner und klicken Sie dann 'Aktualisieren'")
                except Exception as e:
                    st.error(f"❌ Fehler beim Öffnen: {e}")
            else:
                # Erstelle Ordner falls nicht vorhanden
                try:
                    if folder_path:
                        folder_path.mkdir(parents=True, exist_ok=True)
                        _open_folder_in_explorer(folder_path)
                        st.success("✅ Ordner erstellt und für Upload geöffnet!")
                        st.info("💡 Ziehen Sie die Dokumente in den geöffneten Ordner und klicken Sie dann 'Aktualisieren'")
                    else:
                        st.error("❌ Ordnerpfad konnte nicht bestimmt werden!")
                except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen/Öffnen des Ordners: {e}")

    with col_btn2:
        if st.button("🔍 Dokumente prüfen", use_container_width=True):
            if folder_path and folder_path.exists():
                try:
                    # Perform document validation
                    validation_result = _validate_documents(folder_path, item_data)

                    st.write("### 🔍 Dokumentenprüfung")

                    if validation_result['valid']:
                        st.success("✅ Alle Dokumente sind gültig!")
                    else:
                        st.warning("⚠️ Einige Probleme gefunden:")
                        for issue in validation_result['issues']:
                            st.write(f"• {issue}")

                    # Show detailed results
                    if validation_result['details']:
                        with st.expander("📋 Detaillierte Prüfungsergebnisse"):
                            for detail in validation_result['details']:
                                st.write(f"• {detail}")

                except Exception as e:
                    st.error(f"❌ Fehler bei Dokumentenprüfung: {e}")
            else:
                st.warning("❌ Kein Dokumentenordner zum Prüfen vorhanden")

    with col_btn3:
        if st.button("🔄 Aktualisieren", use_container_width=True):
            # Store refresh action and close popup
            st.session_state.document_check_refresh = True
            st.session_state.popup_action = 'close_and_refresh'
            st.rerun()

    with col_btn4:
        if st.button("✅ Prüfung abschließen", use_container_width=True, type="primary"):
            # Mark document check as completed
            document_check_data = {
                'item_data': item_data,
                'folder_path': str(folder_path) if folder_path else None,
                'checked_at': datetime.now(),
                'checked_by': 'Current User',  # TODO: Get from session
                'document_count': len(list(folder_path.glob('*'))) if folder_path and folder_path.exists() else 0
            }

            st.session_state.document_check_completed = document_check_data
            st.session_state.popup_action = 'document_check_complete'
            st.session_state.show_success_message = f"✅ Dokumentenprüfung für {item_data['article_number']} abgeschlossen!"
            st.rerun()

    # File upload widget as alternative
    st.write("---")
    st.write("### 📎 Alternative: Direkter Upload")

    uploaded_files = st.file_uploader(
        "Dokumente direkt hochladen:",
        accept_multiple_files=True,
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'docx', 'doc', 'xlsx', 'xls'],
        help="PDF, Bilder oder Office-Dokumente"
    )

    if uploaded_files and folder_path:
        if st.button("💾 Hochgeladene Dateien speichern", type="secondary"):
            try:
                # Ensure folder exists
                folder_path.mkdir(parents=True, exist_ok=True)

                saved_count = 0
                for uploaded_file in uploaded_files:
                    file_path = folder_path / uploaded_file.name
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    saved_count += 1

                st.success(f"✅ {saved_count} Datei(en) erfolgreich gespeichert!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Fehler beim Speichern: {e}")


def _open_folder_in_explorer(folder_path: Path):
    """Open folder in system file explorer."""
    try:
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{folder_path}"')
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(folder_path)])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(folder_path)])
    except Exception as e:
        logger.error(f"Error opening folder {folder_path}: {e}")
        raise


def _validate_documents(folder_path: Path, item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate documents in the folder."""
    try:
        files = list(folder_path.glob('*'))
        document_files = [f for f in files if f.is_file()]

        validation_result = {
            'valid': True,
            'issues': [],
            'details': []
        }

        # Basic validation
        if not document_files:
            validation_result['valid'] = False
            validation_result['issues'].append("Keine Dokumente gefunden")
            return validation_result

        # Check for common required documents
        required_extensions = ['.pdf', '.docx', '.doc']
        has_required = any(f.suffix.lower() in required_extensions for f in document_files)

        if not has_required:
            validation_result['issues'].append("Keine Standard-Dokumente (.pdf, .docx) gefunden")

        # File size validation
        for file in document_files:
            try:
                file_size = file.stat().st_size
                if file_size == 0:
                    validation_result['valid'] = False
                    validation_result['issues'].append(f"Leere Datei: {file.name}")
                elif file_size > 50 * 1024 * 1024:  # 50MB
                    validation_result['issues'].append(f"Sehr große Datei: {file.name} ({file_size/1024/1024:.1f} MB)")

                validation_result['details'].append(f"{file.name}: {file_size:,} Bytes, {file.suffix}")

            except Exception as e:
                validation_result['valid'] = False
                validation_result['issues'].append(f"Fehler bei {file.name}: {e}")

        # Summary
        validation_result['details'].insert(0, f"Insgesamt {len(document_files)} Datei(en) geprüft")

        if validation_result['issues'] and validation_result['valid']:
            validation_result['valid'] = False

        return validation_result

    except Exception as e:
        logger.error(f"Document validation error: {e}")
        return {
            'valid': False,
            'issues': [f"Validierungsfehler: {e}"],
            'details': []
        }


def handle_document_check_popup_actions():
    """Handle document check popup actions from session state."""
    try:
        # Handle document check completion
        if (st.session_state.get('popup_action') == 'document_check_complete' and
            st.session_state.get('document_check_completed')):

            document_check_data = st.session_state.document_check_completed

            try:
                # Here you would integrate with the document management system
                item_article = document_check_data['item_data'].get('article_number', 'Unknown')
                logger.info(f"Document check completed for {item_article}")

                # Clear session state
                st.session_state.popup_action = 'close_and_refresh'
                st.session_state.document_check_completed = None

            except Exception as e:
                st.error(f"❌ Fehler bei Dokumentenprüfung: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.document_check_completed = None

    except Exception as e:
        logger.error(f"Error in document check popup actions: {e}")
        st.error(f"Dokumentenprüfung-Fehler: {e}")