"""
Workflow Popups - Admin Presentation Layer
Core delivery processing workflow popup dialogs.
"""

import streamlit as st
import logging
import pandas as pd
from datetime import date, datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@st.dialog("✅ Lieferschein-Daten bestätigen")
def show_ls_data_confirmation_popup(item_index: int, item_data: Dict[str, Any]):
    """Show LS data confirmation popup with document generation."""
    st.write(f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}")

    st.write("**Bitte bestätigen Sie die folgenden Lieferschein-Daten:**")

    col1, col2 = st.columns(2)

    with col1:
        confirmed_ls_nr = st.text_input(
            "LS-Nr:",
            value=item_data.get('delivery_number', ''),
            key=f"conf_ls_{item_index}"
        )
        confirmed_article = st.text_input(
            "Artikelnummer:",
            value=item_data.get('article_number', ''),
            key=f"conf_article_{item_index}"
        )
        confirmed_we_date = st.date_input(
            "WE-Datum:",
            key=f"conf_date_{item_index}"
        )

    with col2:
        confirmed_batch = st.text_input(
            "Chargennummer:",
            value=item_data.get('batch_number', ''),
            key=f"conf_batch_{item_index}"
        )
        confirmed_quantity = st.text_input(
            "Lieferumfang:",
            value=item_data.get('quantity', ''),
            key=f"conf_quantity_{item_index}"
        )

    # Zusätzliche ItemInfo-Felder
    st.write("#### 📦 Artikel-Stammdaten")

    col3, col4 = st.columns(2)
    with col3:
        # Standardisiere Artikelbezeichnung basierend auf roher Bezeichnung (nur anzeigen, nicht editierbar)
        raw_designation = item_data.get('designation', '')
        try:
            from warehouse.domain.services.article_designation_service import article_designation_service
            designation_info = article_designation_service.standardize_designation(raw_designation)
            confirmed_designation = designation_info['standardized_designation']
            confirmed_manufacturer = designation_info['manufacturer']
        except Exception as e:
            st.warning(f"Fehler bei Bezeichnungsstandardisierung: {e}")
            confirmed_designation = raw_designation if raw_designation else "Docklocs Accessories [Unbekannt]"
            confirmed_manufacturer = ""

        # Zeige Artikelbezeichnung nur zur Information (nicht editierbar)
        st.info(f"📝 **Artikelbezeichnung (automatisch standardisiert):**\n{confirmed_designation}")

        confirmed_storage_location = st.text_input(
            "Lagerplatznummer:",
            value="",
            key=f"conf_storage_{item_index}",
            help="Lagerplatz für diesen Artikel"
        )

    with col4:
        confirmed_revision = st.number_input(
            "Zeichnungsrevision:",
            min_value=0,
            max_value=999,
            value=1,
            key=f"conf_revision_{item_index}",
            help="Muss bei jedem Wareneingang bestätigt werden"
        )

        # Zeige Rohdaten aus Lieferschein als Referenz
        if raw_designation:
            st.info(f"📋 **Ursprüngliche Bezeichnung (Lieferschein):**\n{raw_designation}")

    # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR Button
    st.write("---")
    from warehouse.application.services.document_storage.storage_availability_checker import (
        storage_availability_checker
    )

    # Prüfe Storage-Verfügbarkeit
    availability_check = storage_availability_checker.check_all_storage_options(
        batch_number=confirmed_batch,
        delivery_number=confirmed_ls_nr,
        article_number=confirmed_article,
        supplier_name=item_data.get('supplier_name', '')
    )

    # Zeige Warnung wenn Server nicht verfügbar
    if availability_check.get('server_unavailable_warning'):
        st.warning("⚠️ **Server-Speicher nicht verfügbar** - Dokumente werden lokal gespeichert")
        with st.expander("📁 Speicher-Details anzeigen"):
            for option in availability_check['all_options']:
                status_icon = "✅" if option.available else "❌"
                st.write(f"{status_icon} **{option.name}**")
                if option.path:
                    st.code(option.path, language="text")
                if not option.available and option.error:
                    st.caption(f"Fehler: {option.error}")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("✅ Daten bestätigen und Dokumente erstellen",
                    key=f"confirm_btn_{item_index}",
                    type="primary",
                    use_container_width=True):
            try:
                # Speichere oder aktualisiere ItemInfo (Artikel-Stammdaten)
                try:
                    item_service = st.session_state.services['item']

                    st.write("💾 Speichere Artikel-Stammdaten...")

                    item_service.save_item_info(
                        article_number=confirmed_article,
                        designation=confirmed_designation,
                        revision_number=confirmed_revision,
                        drawing_reference="",  # Kann später erweitert werden
                        storage_location=confirmed_storage_location,
                        manufacturer=confirmed_manufacturer,
                        material_specification="",  # Kann später erweitert werden
                        description=""  # Kann später erweitert werden
                    )

                    st.success(f"✅ Artikel-Stammdaten für {confirmed_article} gespeichert")

                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern der Artikel-Stammdaten: {e}")
                    # Weiter mit Dokumentenerstellung, auch wenn ItemInfo fehlschlägt

                # Import document generation service
                from warehouse.application.services.document_generation import DocumentGenerationService, DocumentType, ProcessingOptions

                st.write("🔄 Erstelle Dokumente...")
                doc_service = DocumentGenerationService()

                # Create Begleitschein
                begleitschein_result = doc_service.generate_document(
                    document_type=DocumentType.BEGLEITSCHEIN,
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=confirmed_ls_nr,
                    processing_options=ProcessingOptions(open_after_creation=True),
                )
                begleitschein_path = begleitschein_result.document_path if begleitschein_result.success else None

                # Create Wareneingangskontrolle document
                wek_result = doc_service.generate_document(
                    document_type=DocumentType.WARENEINGANGSKONTROLLE,
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=confirmed_ls_nr,
                    additional_data={
                        "we_date": confirmed_we_date.strftime("%d.%m.%Y") if confirmed_we_date else ""
                    },
                    processing_options=ProcessingOptions(open_after_creation=True),
                )
                wek_path = wek_result.document_path if wek_result.success else None

                # Create barcode files with validation
                try:
                    # Validate required fields for barcode creation
                    if not confirmed_article or not confirmed_article.strip():
                        st.warning("⚠️ Artikelnummer fehlt - Kein Artikel-Barcode erstellt")
                        barcode_success = False
                        barcode_result = {'article_barcode': None, 'batch_barcode': None}
                    elif not confirmed_batch or not confirmed_batch.strip():
                        st.warning("⚠️ Chargennummer fehlt - Kein Chargen-Barcode erstellt")
                        barcode_success = False
                        barcode_result = {'article_barcode': None, 'batch_barcode': None}
                    elif not confirmed_ls_nr or not confirmed_ls_nr.strip():
                        st.warning("⚠️ Lieferscheinnummer fehlt - Keine Barcodes erstellt")
                        barcode_success = False
                        barcode_result = {'article_barcode': None, 'batch_barcode': None}
                    else:
                        st.write(f"✅ Erstelle Barcodes für Artikel '{confirmed_article}', Charge '{confirmed_batch}', LS '{confirmed_ls_nr}'")

                        # FIXED: Use standardized DocumentGenerationService instead of word_template_service
                        from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
                        from warehouse.application.services.document_generation.document_types import DocumentType

                        doc_service = DocumentGenerationService()
                        barcode_result = doc_service.generate_document(
                            document_type=DocumentType.BARCODE,
                            article_number=confirmed_article,
                            batch_number=confirmed_batch,
                            delivery_number=confirmed_ls_nr,
                            additional_data={'open_after_creation': True}
                        )

                        if barcode_result.success:
                            st.write(f"✅ Barcode erstellt: {barcode_result.document_path.name}")
                        else:
                            st.error(f"❌ Barcode-Erstellung fehlgeschlagen: {barcode_result.error}")

                        # Show user where files are saved with folder open button
                        if barcode_result.success and barcode_result.document_path:
                            from pathlib import Path
                            folder_path = barcode_result.document_path.parent
                            st.info(f"📁 Barcode-Datei gespeichert in: `{folder_path.name}`")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📁 Ordner öffnen", key=f"open_folder_{confirmed_article}_{confirmed_batch}"):
                                    try:
                                        import subprocess
                                        subprocess.run(["explorer", str(folder_path)], check=False)
                                        st.success("✅ Ordner geöffnet!")
                                    except Exception as e:
                                        st.error(f"Ordner konnte nicht geöffnet werden: {e}")
                            with col2:
                                st.code(str(folder_path), language="text")

                        barcode_success = True
                except Exception as e:
                    st.error(f"❌ Barcode-Erstellung fehlgeschlagen: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    barcode_success = False
                    barcode_result = {'article_barcode': None, 'batch_barcode': None}

                st.success("✅ LS-Daten bestätigt!")
                if begleitschein_path:
                    st.success(f"✅ Begleitschein erstellt: {begleitschein_path.name}")
                else:
                    st.error("❌ Begleitschein konnte nicht erstellt werden")
                if wek_path:
                    st.success(f"✅ WEK erstellt: {wek_path.name}")
                else:
                    st.error("❌ Wareneingangskontrolle konnte nicht erstellt werden")
                if barcode_success:
                    if barcode_result.get('article_barcode'):
                        from pathlib import Path
                        article_barcode_name = Path(barcode_result['article_barcode']).name
                        st.success(f"✅ Artikel-Barcode erstellt: {article_barcode_name}")
                    if barcode_result.get('batch_barcode'):
                        batch_barcode_name = Path(barcode_result['batch_barcode']).name
                        st.success(f"✅ Chargen-Barcode erstellt: {batch_barcode_name}")

                # Clear session state
                st.session_state[f'show_ls_popup_{item_index}'] = False

                # Update item data status or remove from pending list
                if 'current_data' in st.session_state:
                    current_data = st.session_state.current_data
                    if item_index < len(current_data):
                        current_data[item_index]['status'] = 'Dokumente erstellt'

                st.rerun()

            except Exception as e:
                logger.error(f"Document creation error for item {item_index}: {e}")
                st.error(f"❌ Fehler bei Dokumentenerstellung: {e}")

    with col_btn2:
        if st.button("❌ Abbrechen", key=f"cancel_btn_{item_index}", use_container_width=True):
            st.session_state[f'show_ls_popup_{item_index}'] = False
            st.rerun()


@st.dialog("✅ Lieferschein-Daten bestätigen")
def show_ls_confirmation_popup(item_data: Dict[str, Any]):
    """Show LS (Lieferschein) data confirmation popup."""
    st.write(f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}")

    st.write("**Bitte bestätigen Sie die folgenden Lieferschein-Daten:**")

    col1, col2 = st.columns(2)
    with col1:
        confirmed_ls_nr = st.text_input("LS-Nr:", value=item_data.get('delivery_number', ''))
        confirmed_article = st.text_input("Artikelnummer:", value=item_data.get('article_number', ''))
        try:
            we_date_value = pd.to_datetime(item_data['we_date']).date() if item_data.get('we_date') else date.today()
        except:
            we_date_value = date.today()
        confirmed_we_date = st.date_input("WE-Datum:", value=we_date_value)

    with col2:
        confirmed_batch = st.text_input("Chargennummer:", value=item_data.get('batch_number', ''))
        confirmed_quantity = st.text_input("Lieferumfang:", value=item_data.get('quantity', ''))

    # Zusätzliche ItemInfo-Felder
    st.write("#### 📦 Artikel-Stammdaten")

    col3, col4 = st.columns(2)
    with col3:
        # Standardisiere Artikelbezeichnung basierend auf roher Bezeichnung (nur anzeigen, nicht editierbar)
        raw_designation = item_data.get('designation', '')
        try:
            from warehouse.domain.services.article_designation_service import article_designation_service
            designation_info = article_designation_service.standardize_designation(raw_designation)
            confirmed_designation = designation_info['standardized_designation']
            confirmed_manufacturer = designation_info['manufacturer']
        except Exception as e:
            st.warning(f"Fehler bei Bezeichnungsstandardisierung: {e}")
            confirmed_designation = raw_designation if raw_designation else "Docklocs Accessories [Unbekannt]"
            confirmed_manufacturer = ""

        # Zeige Artikelbezeichnung nur zur Information (nicht editierbar)
        st.info(f"📝 **Artikelbezeichnung (automatisch standardisiert):**\n{confirmed_designation}")

        confirmed_storage_location = st.text_input(
            "Lagerplatznummer:",
            value="",
            key="conf_storage_ls",
            help="Lagerplatz für diesen Artikel"
        )

    with col4:
        confirmed_revision = st.number_input(
            "Zeichnungsrevision:",
            min_value=0,
            max_value=999,
            value=1,
            key="conf_revision_ls",
            help="Muss bei jedem Wareneingang bestätigt werden"
        )

        # Zeige Rohdaten aus Lieferschein als Referenz
        if raw_designation:
            st.info(f"📋 **Ursprüngliche Bezeichnung (Lieferschein):**\n{raw_designation}")

    # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR Button
    st.write("---")
    from warehouse.application.services.document_storage.storage_availability_checker import (
        storage_availability_checker
    )

    # Prüfe Storage-Verfügbarkeit
    availability_check = storage_availability_checker.check_all_storage_options(
        batch_number=confirmed_batch,
        delivery_number=confirmed_ls_nr,
        article_number=confirmed_article,
        supplier_name=item_data.get('supplier_name', '')
    )

    # Zeige Warnung wenn Server nicht verfügbar
    if availability_check.get('server_unavailable_warning'):
        st.warning("⚠️ **Server-Speicher nicht verfügbar** - Dokumente werden lokal gespeichert")
        with st.expander("📁 Speicher-Details anzeigen"):
            for option in availability_check['all_options']:
                status_icon = "✅" if option.available else "❌"
                st.write(f"{status_icon} **{option.name}**")
                if option.path:
                    st.code(option.path, language="text")
                if not option.available and option.error:
                    st.caption(f"Fehler: {option.error}")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("✅ Bestätigen und Dokumente erstellen", type="primary", use_container_width=True):
            try:
                # Speichere oder aktualisiere ItemInfo (Artikel-Stammdaten)
                try:
                    item_service = st.session_state.services['item']

                    st.write("💾 Speichere Artikel-Stammdaten...")

                    item_service.save_item_info(
                        article_number=confirmed_article,
                        designation=confirmed_designation,
                        revision_number=confirmed_revision,
                        drawing_reference="",  # Kann später erweitert werden
                        storage_location=confirmed_storage_location,
                        manufacturer=confirmed_manufacturer,
                        material_specification="",  # Kann später erweitert werden
                        description=""  # Kann später erweitert werden
                    )

                    st.success(f"✅ Artikel-Stammdaten für {confirmed_article} gespeichert")

                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern der Artikel-Stammdaten: {e}")
                    # Weiter mit Dokumentenerstellung, auch wenn ItemInfo fehlschlägt

                # Create Begleitschein and Wareneingangskontrolle documents
                from warehouse.application.services.document_generation import DocumentGenerationService, DocumentType, ProcessingOptions

                st.write("🔄 Erstelle Dokumente...")
                doc_service = DocumentGenerationService()

                # Create Begleitschein
                begleitschein_result = doc_service.generate_document(
                    document_type=DocumentType.BEGLEITSCHEIN,
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=confirmed_ls_nr,
                    processing_options=ProcessingOptions(open_after_creation=True),
                )
                begleitschein_path = begleitschein_result.document_path if begleitschein_result.success else None

                # Create Wareneingangskontrolle document
                wek_result = doc_service.generate_document(
                    document_type=DocumentType.WARENEINGANGSKONTROLLE,
                    article_number=confirmed_article,
                    batch_number=confirmed_batch,
                    delivery_number=confirmed_ls_nr,
                    additional_data={
                        "we_date": confirmed_we_date.strftime("%d.%m.%Y") if confirmed_we_date else ""
                    },
                    processing_options=ProcessingOptions(open_after_creation=True),
                )
                wek_path = wek_result.document_path if wek_result.success else None

                # Create barcode files with validation
                try:
                    # Validate required fields for barcode creation
                    if not confirmed_article or not confirmed_article.strip():
                        st.warning("⚠️ Artikelnummer fehlt - Kein Artikel-Barcode erstellt")
                        barcode_success = False
                        barcode_result = {'article_barcode': None, 'batch_barcode': None}
                    elif not confirmed_batch or not confirmed_batch.strip():
                        st.warning("⚠️ Chargennummer fehlt - Kein Chargen-Barcode erstellt")
                        barcode_success = False
                        barcode_result = {'article_barcode': None, 'batch_barcode': None}
                    elif not confirmed_ls_nr or not confirmed_ls_nr.strip():
                        st.warning("⚠️ Lieferscheinnummer fehlt - Keine Barcodes erstellt")
                        barcode_success = False
                        barcode_result = {'article_barcode': None, 'batch_barcode': None}
                    else:
                        st.write(f"✅ Erstelle Barcodes für Artikel '{confirmed_article}', Charge '{confirmed_batch}', LS '{confirmed_ls_nr}'")

                        # FIXED: Use standardized DocumentGenerationService instead of word_template_service
                        from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
                        from warehouse.application.services.document_generation.document_types import DocumentType

                        doc_service = DocumentGenerationService()
                        barcode_result = doc_service.generate_document(
                            document_type=DocumentType.BARCODE,
                            article_number=confirmed_article,
                            batch_number=confirmed_batch,
                            delivery_number=confirmed_ls_nr,
                            additional_data={'open_after_creation': True}
                        )

                        if barcode_result.success:
                            st.write(f"✅ Barcode erstellt: {barcode_result.document_path.name}")
                        else:
                            st.error(f"❌ Barcode-Erstellung fehlgeschlagen: {barcode_result.error}")

                        # Show user where files are saved with folder open button
                        if barcode_result.success and barcode_result.document_path:
                            from pathlib import Path
                            folder_path = barcode_result.document_path.parent
                            st.info(f"📁 Barcode-Datei gespeichert in: `{folder_path.name}`")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📁 Ordner öffnen", key=f"open_folder_{confirmed_article}_{confirmed_batch}_ls"):
                                    try:
                                        import subprocess
                                        subprocess.run(["explorer", str(folder_path)], check=False)
                                        st.success("✅ Ordner geöffnet!")
                                    except Exception as e:
                                        st.error(f"Ordner konnte nicht geöffnet werden: {e}")
                            with col2:
                                st.code(str(folder_path), language="text")

                        barcode_success = True
                except Exception as e:
                    st.error(f"❌ Barcode-Erstellung fehlgeschlagen: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    barcode_success = False
                    barcode_result = {'article_barcode': None, 'batch_barcode': None}

                st.success("✅ LS-Daten bestätigt!")
                if begleitschein_path:
                    st.success(f"✅ Begleitschein erstellt: {begleitschein_path.name}")
                else:
                    st.error("❌ Begleitschein konnte nicht erstellt werden")
                if wek_path:
                    st.success(f"✅ WEK erstellt: {wek_path.name}")
                else:
                    st.error("❌ Wareneingangskontrolle konnte nicht erstellt werden")
                if barcode_success:
                    if barcode_result.get('article_barcode'):
                        from pathlib import Path
                        article_barcode_name = Path(barcode_result['article_barcode']).name
                        st.success(f"✅ Artikel-Barcode erstellt: {article_barcode_name}")
                    if barcode_result.get('batch_barcode'):
                        batch_barcode_name = Path(barcode_result['batch_barcode']).name
                        st.success(f"✅ Chargen-Barcode erstellt: {batch_barcode_name}")

                # Store confirmed data in session state
                confirmed_data = {
                    'delivery_number': confirmed_ls_nr,
                    'article_number': confirmed_article,
                    'batch_number': confirmed_batch,
                    'quantity': confirmed_quantity,
                    'we_date': confirmed_we_date,
                    'designation': confirmed_designation,
                    'storage_location': confirmed_storage_location,
                    'revision': confirmed_revision,
                    'manufacturer': confirmed_manufacturer
                }

                st.session_state.confirmed_ls_data = confirmed_data
                st.session_state.popup_action = 'ls_confirm'
                st.rerun()

            except Exception as e:
                logger.error(f"Document creation error in LS confirmation: {e}")
                st.error(f"❌ Fehler bei Dokumentenerstellung: {e}")

    with col_btn2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


@st.dialog("🔒 Artikel abschließen")
def show_finalize_popup(item_data: Dict[str, Any]):
    """Show finalize popup."""
    st.write(f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}")

    st.write("### 📋 Finalisierung")
    st.info("Diese Funktion schließt den Artikel im Workflow ab.")

    # Show current status
    st.write("**Aktueller Status:**")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"• **Artikel:** {item_data.get('article_number', 'N/A')}")
        st.write(f"• **Charge:** {item_data.get('batch_number', 'N/A')}")
        st.write(f"• **LS-Nr:** {item_data.get('delivery_number', 'N/A')}")
    with col2:
        st.write(f"• **Menge:** {item_data.get('quantity', 'N/A')}")
        st.write(f"• **Status:** {item_data.get('status', 'N/A')}")
        st.write(f"• **Lieferant:** {item_data.get('supplier', 'N/A')}")

    st.write("---")

    # Finalization options
    st.write("### ⚙️ Finalisierungs-Optionen")

    finalize_options = st.multiselect(
        "Wählen Sie die gewünschten Aktionen:",
        [
            "Qualitätsprüfung abgeschlossen markieren",
            "Artikel in Lager einbuchen",
            "Dokumentation archivieren",
            "Workflow-Status auf 'Abgeschlossen' setzen",
            "Benachrichtigung senden"
        ],
        default=["Workflow-Status auf 'Abgeschlossen' setzen"]
    )

    # Final notes
    final_notes = st.text_area(
        "Abschluss-Notizen:",
        placeholder="Optionale Notizen zum Workflow-Abschluss...",
        height=80
    )

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("✅ Artikel abschließen", type="primary", use_container_width=True):

            # Store finalization data
            finalization_data = {
                'item_data': item_data,
                'options': finalize_options,
                'notes': final_notes,
                'finalized_at': datetime.now(),
                'finalized_by': 'Current User'  # TODO: Get from session
            }

            st.session_state.finalization_data = finalization_data
            st.session_state.popup_action = 'finalize'

            # Show confirmation
            st.success("✅ Artikel wird abgeschlossen...")
            st.info("💡 Implementierung folgt - Workflow-Integration erforderlich")

            # For now, just show what would happen
            st.write("**Geplante Aktionen:**")
            for option in finalize_options:
                st.write(f"• {option}")

            if final_notes:
                st.write(f"**Notizen:** {final_notes}")

            st.rerun()

    with col_btn2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.popup_action = 'cancel'
            st.rerun()


def handle_workflow_popup_actions():
    """Handle workflow popup actions from session state."""
    try:
        # Handle LS confirmation
        if (st.session_state.get('popup_action') == 'ls_confirm' and
            st.session_state.get('confirmed_ls_data')):

            confirmed_data = st.session_state.confirmed_ls_data

            try:
                # Here you would integrate with the document creation workflow
                st.success(f"✅ Lieferschein-Daten für {confirmed_data['article_number']} bestätigt!")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.confirmed_ls_data = None
                st.rerun()

            except Exception as e:
                st.error(f"❌ Fehler bei LS-Bestätigung: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.confirmed_ls_data = None

        # Handle finalization
        elif (st.session_state.get('popup_action') == 'finalize' and
              st.session_state.get('finalization_data')):

            finalization_data = st.session_state.finalization_data

            try:
                # Here you would integrate with the finalization workflow
                item_article = finalization_data['item_data'].get('article_number', 'Unknown')
                st.success(f"✅ Artikel {item_article} abgeschlossen!")

                # Clear session state
                st.session_state.popup_action = None
                st.session_state.finalization_data = None
                st.rerun()

            except Exception as e:
                st.error(f"❌ Fehler bei Finalisierung: {e}")
                # Clear session state
                st.session_state.popup_action = None
                st.session_state.finalization_data = None

        # Handle cancellation
        elif st.session_state.get('popup_action') == 'cancel':
            st.session_state.popup_action = None
            st.session_state.confirmed_ls_data = None
            st.session_state.finalization_data = None

    except Exception as e:
        logger.error(f"Error in workflow popup actions: {e}")
        st.error(f"Workflow-Popup-Fehler: {e}")