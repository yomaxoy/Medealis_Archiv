"""
Document Management View - Admin Presentation Layer
Manages document generation for deliveries, items, and reports.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from datetime import date, datetime

from warehouse.presentation.shared.components import render_open_folder_button

logger = logging.getLogger(__name__)


def show_document_management_view():
    """Show document management interface with tabs for different document types."""
    if not st.session_state.get('system_initialized'):
        st.warning("System nicht initialisiert")
        return

    # Get services
    services = st.session_state.get('services', {})
    if 'delivery' not in services:
        st.error("Delivery Service nicht verfügbar")
        return

    delivery_service = services['delivery']
    item_service = services['item']

    st.header("📄 Dokumentenverwaltung")
    st.write("Generierung und Verwaltung aller Dokumente für Lieferungen und Artikel")

    # Create tabs for different document types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Lieferschein-Dokumente",
        "📄 Artikel-Dokumente",
        "📊 Berichte & Export",
        "🔧 Bulk-Operationen",
        "📥 Lieferschein Upload"
    ])

    with tab1:
        _show_delivery_documents_section(delivery_service, item_service)

    with tab2:
        _show_item_documents_section(item_service)

    with tab3:
        _show_reports_section(delivery_service, item_service)

    with tab4:
        _show_bulk_operations_section(delivery_service, item_service)

    with tab5:
        _show_delivery_slip_upload_section()


def _show_delivery_documents_section(delivery_service, item_service):
    """Show delivery documents generation section."""
    st.subheader("📋 Lieferschein-Dokumente")
    st.write("Hier können Sie Lieferscheine und Prüfprotokolle für Deliveries generieren.")

    # Delivery selection for document generation
    try:
        deliveries_data = delivery_service.get_all_deliveries() if hasattr(delivery_service, 'get_all_deliveries') else []
        if deliveries_data:
            delivery_options = {f"{d['delivery_number']} ({d['supplier_id']})": d['delivery_number'] for d in deliveries_data}
            selected_delivery_display = st.selectbox(
                "Wählen Sie eine Lieferung:",
                options=list(delivery_options.keys()),
                key="doc_delivery_selection"
            )

            if selected_delivery_display:
                selected_delivery_number = delivery_options[selected_delivery_display]

                # Enhanced document generation section
                st.write("### 📄 Enhanced Document Generation")
                st.write("Integriert Datenbankdaten und erstellt organisierte Ordnerstruktur.")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🚀 Vollständige Lieferung erstellen", use_container_width=True, type="primary"):
                        _create_complete_delivery_documentation(selected_delivery_number)

                with col2:
                    if st.button("📁 Ordner öffnen", use_container_width=True):
                        _open_delivery_folder(selected_delivery_number)

                # Word document generation
                st.write("### 📝 Word-Dokumente")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📄 Alle Dokumente erstellen", use_container_width=True, type="primary"):
                        _create_all_word_documents(selected_delivery_number)

                with col2:
                    if st.button("📋 Nur PDB erstellen", use_container_width=True):
                        _create_pdb_document_only(selected_delivery_number)

                # Barcode generation
                st.write("### 🏷️ Barcode-Erstellung")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🏷️ Barcodes generieren", use_container_width=True):
                        _generate_barcodes_for_delivery(selected_delivery_number)

                with col2:
                    if st.button("📁 Artikel-Ordner öffnen", use_container_width=True):
                        _open_article_folder(selected_delivery_number)

                # PDF operations
                st.write("### 📎 PDF-Operationen")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📎 PDFs zusammenführen", use_container_width=True):
                        _merge_delivery_pdfs(selected_delivery_number)

                with col2:
                    if st.button("📋 Dokumente auflisten", use_container_width=True):
                        _list_delivery_documents(selected_delivery_number)

        else:
            st.info("Keine Lieferungen in der Datenbank gefunden.")

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Lieferungen: {e}")
        logger.error(f"Error loading deliveries for document generation: {e}")


def _show_item_documents_section(item_service):
    """Show item-specific documents section."""
    st.subheader("📄 Artikel-Dokumente")
    st.write("Hier können Sie Sichtkontrollen für Items generieren und Excel-Exporte erstellen.")

    # Item selection for document generation
    try:
        items_data = item_service.get_all_items() if hasattr(item_service, 'get_all_items') else []
        if items_data:
            item_options = {f"{item['article_number']} | {item['batch_number']} ({item.get('delivery_number', 'N/A')})": item for item in items_data}
            selected_item_display = st.selectbox(
                "Wählen Sie einen Artikel:",
                options=list(item_options.keys()),
                key="doc_item_selection"
            )

            if selected_item_display:
                selected_item = item_options[selected_item_display]

                # Artikel-Info Box
                st.info(f"**Ausgewählter Artikel:** {selected_item['article_number']} | **Charge:** {selected_item['batch_number']} | **Lieferung:** {selected_item.get('delivery_number', 'N/A')}")

                # Action-Buttons in 3 Spalten
                col1, col2, col3 = st.columns(3)

                with col1:
                    # Artikelordner öffnen Button
                    # Bereite Item-Daten für folder_button vor
                    folder_item_data = {
                        "article_number": selected_item["article_number"],
                        "batch_number": selected_item["batch_number"],
                        "delivery_number": selected_item.get("delivery_number", ""),
                        "supplier_name": selected_item.get("supplier_name", selected_item.get("supplier", "")),
                        "manufacturer": selected_item.get("manufacturer", selected_item.get("supplier_name", selected_item.get("supplier", ""))),
                    }
                    render_open_folder_button(
                        folder_item_data,
                        label="🗂️ Artikelordner öffnen",
                        button_type="primary",
                        key_suffix="doc_mgmt"
                    )

                with col2:
                    if st.button("📊 Excel-Export erstellen", use_container_width=True):
                        _create_excel_export(selected_item)

                with col3:
                    st.caption("💡 **Tipp:** Nutze den Ordner-Button für direkten Zugriff auf alle Artikel-Dokumente!")

                # Info-Box für Sichtkontrolle
                st.write("")  # Spacing
                st.info("👥 **Sichtkontrolle:** Verwende das Visual Inspection Popup im Sichtkontrolle-Tab für korrekte Ausschuss-Erfassung!")

        else:
            st.info("Keine Artikel in der Datenbank gefunden.")

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Artikel: {e}")
        logger.error(f"Error loading items for document generation: {e}")


def _show_reports_section(delivery_service, item_service):
    """Show reports and export section."""
    st.subheader("📊 Berichte & Export")
    st.write("Erstellen Sie Berichte und Exporte für Ihre Daten.")

    col1, col2 = st.columns(2)

    with col1:
        st.write("#### 📋 Lieferungs-Berichte")
        if st.button("📊 Lieferungs-Übersicht (Excel)", use_container_width=True):
            _export_deliveries_to_excel(delivery_service)

        if st.button("📄 Lieferungs-Bericht (PDF)", use_container_width=True):
            _create_delivery_report_pdf(delivery_service)

    with col2:
        st.write("#### 📦 Artikel-Berichte")
        if st.button("📊 Artikel-Übersicht (Excel)", use_container_width=True):
            _export_items_to_excel(item_service)

        if st.button("📄 Qualitäts-Bericht (PDF)", use_container_width=True):
            _create_quality_report_pdf(item_service)


def _show_bulk_operations_section(delivery_service, item_service):
    """Show bulk operations section."""
    st.subheader("🔧 Bulk-Operationen")
    st.write("Führen Sie Operationen für mehrere Datensätze gleichzeitig durch.")

    # Bulk delivery operations
    st.write("#### 📋 Bulk-Lieferungs-Operationen")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Alle Lieferungen dokumentieren", use_container_width=True, type="primary"):
            _bulk_create_delivery_documents(delivery_service)

    with col2:
        if st.button("🏷️ Alle Barcodes generieren", use_container_width=True):
            _bulk_generate_all_barcodes(item_service)

    # Bulk item operations
    st.write("#### 📦 Bulk-Artikel-Operationen")
    col1, col2 = st.columns(2)

    with col1:
        st.info("👁️ **Sichtkontrolle-Dokumente** werden über die Visual Inspection Popups erstellt, da diese benutzerdefinierte Ausschussmengen benötigen.")

    with col2:
        if st.button("📊 Vollständiger Excel-Export", use_container_width=True):
            _create_complete_excel_export(delivery_service, item_service)


# ================================
# DOCUMENT CREATION FUNCTIONS
# ================================

def _create_complete_delivery_documentation(delivery_number: str):
    """Create complete delivery documentation using enhanced service."""
    with st.spinner("Erstelle vollständige Dokumentation..."):
        try:
            from warehouse.application.services.delivery_workflow_service import DeliveryWorkflowService

            workflow_service = DeliveryWorkflowService()
            results = workflow_service.create_delivery_documents(
                delivery_number=delivery_number,
                open_documents=True,
                create_folder=True
            )

            if results.success:
                st.success(f"✅ Dokumentation erstellt: {len(results.documents_created)} Dokumente")
                if results.folder_path:
                    st.info(f"📁 Ordner erstellt: {results.folder_path}")

                # Show created documents
                for doc in results.documents_created:
                    doc_type = doc.get('type', 'Unknown')
                    doc_path = doc.get('path', '')
                    if doc_path:
                        st.write(f"📄 {doc_type}: `{Path(doc_path).name}`")
            else:
                st.error("❌ Fehler bei der Dokumenterstellung")
                for error in results.errors:
                    st.error(f"• {error}")

        except Exception as e:
            st.error(f"❌ Fehler: {e}")
            logger.error(f"Error creating complete delivery documentation: {e}")


def _create_all_word_documents(delivery_number: str):
    """Create all Word documents for a delivery."""
    with st.spinner("Erstelle Word-Dokumente (PDB, Begleitschein, Sichtkontrolle)..."):
        try:
            # FIXED: Use standardized services instead of enhanced_document_service
            from warehouse.application.services.delivery_workflow_service import DeliveryWorkflowService

            workflow_service = DeliveryWorkflowService()
            result = workflow_service.create_delivery_documents(
                delivery_number=delivery_number,
                open_documents=False,  # Don't open, just save
                create_folder=True
            )

            if result['success']:
                st.success(f"✅ {len(result['documents_created'])} Word-Dokumente erstellt!")

                # Show created documents
                for doc in result['documents_created']:
                    st.info(f"📄 {doc['type']}: {doc['path'].name}")

                if result['folder_path']:
                    st.info(f"📁 Gespeichert in: {result['folder_path']}")

                # Show any warnings
                if result['errors']:
                    for error in result['errors']:
                        st.warning(f"⚠️ {error}")

            else:
                st.error("❌ Fehler bei der Word-Dokument-Erstellung")
                for error in result['errors']:
                    st.error(f"• {error}")

        except Exception as e:
            st.error(f"❌ Fehler: {e}")
            logger.error(f"Error creating Word documents: {e}")


def _create_pdb_document_only(delivery_number: str):
    """Create only PDB document for a delivery."""
    with st.spinner("Erstelle PDB (Prüfprotokoll)..."):
        try:
            # FIXED: Use standardized services instead of enhanced_document_service
            from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
            from warehouse.application.services.document_generation.document_types import DocumentType

            # Get delivery data first
            services = st.session_state.get('services', {})
            delivery_service = services.get('delivery')

            if delivery_service:
                delivery_data = delivery_service.get_delivery(delivery_number)
                if delivery_data and 'items' in delivery_data:
                    doc_service = DocumentGenerationService()

                    # Create PDB for first item (or adjust logic as needed)
                    first_item = delivery_data['items'][0] if delivery_data['items'] else {}

                    pdb_result = doc_service.generate_document(
                        document_type=DocumentType.PDB,
                        batch_number=first_item.get('batch_number', ''),
                        delivery_number=delivery_number,
                        article_number=first_item.get('article_number', ''),
                        supplier_name=delivery_data.get('supplier_name', ''),
                        quantity=first_item.get('quantity', 0),
                        employee_name=st.session_state.get('current_user', 'System')
                    )

                    # Create compatible result format
                    result = {
                        'success': pdb_result.success,
                        'documents_created': [{'type': 'PDB', 'path': pdb_result.document_path}] if pdb_result.success else [],
                        'errors': [pdb_result.error] if not pdb_result.success else []
                    }
                else:
                    result = {'success': False, 'documents_created': [], 'errors': ['Delivery data not found']}
            else:
                result = {'success': False, 'documents_created': [], 'errors': ['Delivery service not available']}

            if result['success']:
                # Find and highlight the PDB document
                pdb_docs = [doc for doc in result['documents_created'] if doc['type'] == 'PDB']

                if pdb_docs:
                    pdb_doc = pdb_docs[0]
                    st.success(f"✅ PDB (Prüfprotokoll) erstellt: {pdb_doc['path'].name}")
                    st.info(f"📁 Gespeichert unter: {pdb_doc['path']}")

                    # Show info about other documents created
                    other_docs = [doc for doc in result['documents_created'] if doc['type'] != 'PDB']
                    if other_docs:
                        st.info(f"💡 Zusätzlich erstellt: {', '.join([doc['type'] for doc in other_docs])}")
                else:
                    st.error("❌ PDB konnte nicht erstellt werden")

                if result['errors']:
                    for error in result['errors']:
                        st.warning(f"⚠️ {error}")
            else:
                # Fallback to document generation service
                st.info("🔄 Versuche mit Standard-Daten...")
                from warehouse.application.services.document_generation import DocumentGenerationService, DocumentType

                # Create document generation service
                doc_service = DocumentGenerationService()

                # Generate PDB with default data
                result = doc_service.generate_document(
                    document_type=DocumentType.PDB,
                    article_number="A001",  # Default fallback
                    batch_number="B000001",  # Default fallback
                    delivery_number=delivery_number,
                    auto_open=True
                )

                doc_path = result.output_path if result.success else None

                st.success(f"✅ PDB mit Standard-Daten erstellt: {doc_path.name}")
                st.warning("⚠️ Dokument wurde mit Standard-Daten erstellt. Bitte Werte manuell anpassen!")
                st.info(f"📁 Gespeichert unter: {doc_path}")

        except Exception as e:
            st.error(f"❌ Fehler bei PDB-Erstellung: {e}")
            logger.error(f"Error creating PDB document: {e}")


def _generate_barcodes_for_delivery(delivery_number: str):
    """Generate barcodes for a specific delivery."""
    with st.spinner("Generiere Barcodes..."):
        try:
            # FIXED: Use standardized DocumentGenerationService instead of word_template_service
            from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
            from warehouse.application.services.document_generation.document_types import DocumentType

            # Get delivery data to extract article/batch info
            services = st.session_state.get('services', {})
            delivery_service = services.get('delivery')

            if delivery_service:
                delivery_data = delivery_service.get_delivery(delivery_number)
                if delivery_data and 'items' in delivery_data:
                    barcode_results = []
                    doc_service = DocumentGenerationService()

                    for item in delivery_data['items']:
                        try:
                            result = doc_service.generate_document(
                                document_type=DocumentType.BARCODE,
                                article_number=item.get('article_number', 'A001'),
                                batch_number=item.get('batch_number', 'B000001'),
                                delivery_number=delivery_number,
                                supplier_name=delivery_data.get('supplier_name', ''),
                                additional_data={'open_after_creation': True}
                            )
                            if result.success:
                                barcode_results.append(result)
                        except Exception as item_e:
                            st.warning(f"⚠️ Barcode-Fehler für {item.get('article_number', 'Unknown')}: {item_e}")

                    if barcode_results:
                        st.success(f"✅ Barcodes für {len(barcode_results)} Artikel erstellt!")

                        # Show folder info
                        if barcode_results[0].get('article_barcode'):
                            folder_path = Path(barcode_results[0]['article_barcode']).parent
                            st.info(f"📁 Barcodes gespeichert in: `{folder_path.name}`")
                    else:
                        st.warning("⚠️ Keine Barcodes erstellt")
                else:
                    st.error("❌ Lieferungsdaten nicht gefunden")
            else:
                st.error("❌ Delivery Service nicht verfügbar")

        except Exception as e:
            st.error(f"❌ Fehler bei Barcode-Generierung: {e}")
            logger.error(f"Error generating barcodes: {e}")


# REMOVED: _create_visual_inspection_document function
# Sichtkontrolle documents should ONLY be created via the Visual Inspection Popup
# which handles user-entered waste quantities correctly.


# ================================
# FOLDER & FILE OPERATIONS
# ================================

def _open_delivery_folder(delivery_number: str):
    """Open delivery folder in file explorer."""
    try:
        # FIXED: Use standardized services instead of enhanced_document_service
        from warehouse.application.services.document_storage.document_storage_service import document_storage_service
        from warehouse.application.services.document_operations.document_opening_service import DocumentOpeningService

        # Get delivery data to extract required parameters
        services = st.session_state.get('services', {})
        delivery_service = services.get('delivery')

        if delivery_service:
            delivery_data = delivery_service.get_delivery(delivery_number)
            if delivery_data and 'items' in delivery_data and delivery_data['items']:
                first_item = delivery_data['items'][0]
                folder_path, warnings = document_storage_service.get_document_path(
                    batch_number=first_item.get('batch_number', ''),
                    delivery_number=delivery_number,
                    article_number=first_item.get('article_number', ''),
                    supplier_name=delivery_data.get('supplier_name', ''),
                    create_folders=False
                )

                if folder_path and folder_path.exists():
                    opener = DocumentOpeningService()
                    success = opener.open_folder(folder_path)
                    if success:
                        st.success(f"✅ Ordner geöffnet: {folder_path}")
                    else:
                        st.warning("⚠️ Ordner konnte nicht geöffnet werden")
                else:
                    st.warning("⚠️ Ordner nicht gefunden")
            else:
                st.warning("⚠️ Lieferdaten nicht gefunden")
        else:
            st.warning("⚠️ Delivery Service nicht verfügbar")

    except Exception as e:
        st.error(f"❌ Fehler beim Öffnen des Ordners: {e}")
        logger.error(f"Error opening delivery folder: {e}")


def _open_article_folder(delivery_number: str):
    """Open article folder for delivery."""
    try:
        # FIXED: Use standardized services instead of enhanced_document_service
        from warehouse.application.services.document_storage.document_storage_service import document_storage_service
        from warehouse.application.services.document_operations.document_opening_service import DocumentOpeningService

        # Get delivery data to extract required parameters
        services = st.session_state.get('services', {})
        delivery_service = services.get('delivery')

        if delivery_service:
            delivery_data = delivery_service.get_delivery(delivery_number)
            if delivery_data and 'items' in delivery_data and delivery_data['items']:
                first_item = delivery_data['items'][0]
                folder_path, warnings = document_storage_service.get_document_path(
                    batch_number=first_item.get('batch_number', ''),
                    delivery_number=delivery_number,
                    article_number=first_item.get('article_number', ''),
                    supplier_name=delivery_data.get('supplier_name', ''),
                    create_folders=False
                )

                if folder_path and folder_path.exists():
                    opener = DocumentOpeningService()
                    success = opener.open_folder(folder_path)
                    if success:
                        st.success(f"✅ Artikel-Ordner geöffnet: {folder_path}")
                    else:
                        # Fallback to manual platform-specific opening
                        import os, platform, subprocess
                        try:
                            if platform.system() == "Windows":
                                os.startfile(str(folder_path))
                                st.success(f"✅ Artikel-Ordner geöffnet: {folder_path}")
                            elif platform.system() == "Darwin":  # macOS
                                subprocess.run(["open", str(folder_path)], check=False)
                                st.success(f"✅ Artikel-Ordner geöffnet: {folder_path}")
                            else:  # Linux
                                subprocess.run(["xdg-open", str(folder_path)], check=False)
                                st.success(f"✅ Artikel-Ordner geöffnet: {folder_path}")
                        except Exception:
                            st.warning("⚠️ Artikel-Ordner konnte nicht geöffnet werden")
                else:
                    st.warning("⚠️ Artikel-Ordner nicht gefunden")
            else:
                st.warning("⚠️ Lieferdaten nicht gefunden")
        else:
            st.warning("⚠️ Delivery Service nicht verfügbar")

    except Exception as e:
        st.error(f"❌ Fehler beim Öffnen des Artikel-Ordners: {e}")
        logger.error(f"Error opening article folder: {e}")


def _merge_delivery_pdfs(delivery_number: str):
    """Merge PDFs for a delivery."""
    with st.spinner("Führe PDFs zusammen..."):
        try:
            # FIXED: Use standardized services instead of enhanced_document_service
            from warehouse.application.services.document_operations.pdf_merge_service import PDFMergeService
            from warehouse.application.services.document_storage.document_storage_service import document_storage_service

            # Get delivery data to extract required parameters for path resolution
            services = st.session_state.get('services', {})
            delivery_service = services.get('delivery')

            if delivery_service:
                delivery_data = delivery_service.get_delivery(delivery_number)
                if delivery_data and 'items' in delivery_data and delivery_data['items']:
                    first_item = delivery_data['items'][0]

                    # Get delivery folder path
                    folder_path, warnings = document_storage_service.get_document_path(
                        batch_number=first_item.get('batch_number', ''),
                        delivery_number=delivery_number,
                        article_number=first_item.get('article_number', ''),
                        supplier_name=delivery_data.get('supplier_name', ''),
                        create_folders=False
                    )

                    if folder_path and folder_path.exists():
                        # Initialize PDF merge service
                        pdf_service = PDFMergeService()
                        merged_path = pdf_service.merge_delivery_pdfs(str(folder_path))

                        if merged_path:
                            st.success(f"✅ PDFs zusammengeführt: {merged_path.name}")
                        else:
                            st.warning("⚠️ Keine PDFs zum Zusammenführen gefunden")
                    else:
                        st.warning("⚠️ Lieferungsordner nicht gefunden")
                else:
                    st.warning("⚠️ Lieferdaten nicht gefunden")
            else:
                st.warning("⚠️ Delivery Service nicht verfügbar")

        except Exception as e:
            st.error(f"❌ Fehler beim PDF-Merge: {e}")
            logger.error(f"Error merging PDFs: {e}")


def _list_delivery_documents(delivery_number: str):
    """List all documents in delivery folder."""
    try:
        # FIXED: Use standardized services instead of enhanced_document_service
        from warehouse.application.services.document_storage.document_storage_service import document_storage_service

        # Get delivery data to extract required parameters
        services = st.session_state.get('services', {})
        delivery_service = services.get('delivery')

        if delivery_service:
            delivery_data = delivery_service.get_delivery(delivery_number)
            if delivery_data and 'items' in delivery_data and delivery_data['items']:
                first_item = delivery_data['items'][0]
                folder_path, warnings = document_storage_service.get_document_path(
                    batch_number=first_item.get('batch_number', ''),
                    delivery_number=delivery_number,
                    article_number=first_item.get('article_number', ''),
                    supplier_name=delivery_data.get('supplier_name', ''),
                    create_folders=False
                )

                if folder_path and folder_path.exists():
                    files = list(folder_path.rglob('*'))
                    document_files = [f for f in files if f.is_file()]

                    if document_files:
                        st.write(f"📁 Dateien in {folder_path.name}:")
                        for file in sorted(document_files):
                            file_size = file.stat().st_size
                            size_str = f"({file_size:,} bytes)" if file_size < 1024 else f"({file_size/1024:.1f} KB)"
                            st.write(f"• {file.name} {size_str}")
                    else:
                        st.info("Keine Dateien im Lieferungsordner gefunden")
                else:
                    st.warning("⚠️ Lieferungsordner nicht gefunden")
            else:
                st.warning("⚠️ Lieferdaten nicht gefunden")
        else:
            st.warning("⚠️ Delivery Service nicht verfügbar")

    except Exception as e:
        st.error(f"❌ Fehler beim Auflisten der Dokumente: {e}")
        logger.error(f"Error listing delivery documents: {e}")


# ================================
# EXPORT & REPORTING FUNCTIONS
# ================================

def _export_deliveries_to_excel(delivery_service):
    """Export deliveries to Excel."""
    with st.spinner("Erstelle Excel-Export..."):
        try:
            deliveries_data = delivery_service.get_all_deliveries()
            if deliveries_data:
                df = pd.DataFrame(deliveries_data)

                # Create Excel file
                excel_path = Path.home() / "Downloads" / f"deliveries_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(excel_path, index=False)

                st.success(f"✅ Excel-Export erstellt: {excel_path.name}")
                st.info(f"📁 Gespeichert unter: {excel_path}")
            else:
                st.warning("⚠️ Keine Lieferungsdaten zum Export gefunden")

        except Exception as e:
            st.error(f"❌ Fehler beim Excel-Export: {e}")
            logger.error(f"Error exporting deliveries to Excel: {e}")


def _export_items_to_excel(item_service):
    """Export items to Excel."""
    with st.spinner("Erstelle Artikel-Excel-Export..."):
        try:
            items_data = item_service.get_all_items() or []
            if items_data:
                df = pd.DataFrame(items_data)

                # Create Excel file
                excel_path = Path.home() / "Downloads" / f"items_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(excel_path, index=False)

                st.success(f"✅ Artikel-Excel-Export erstellt: {excel_path.name}")
                st.info(f"📁 Gespeichert unter: {excel_path}")
            else:
                st.warning("⚠️ Keine Artikeldaten zum Export gefunden")

        except Exception as e:
            st.error(f"❌ Fehler beim Artikel-Excel-Export: {e}")
            logger.error(f"Error exporting items to Excel: {e}")


def _create_excel_export(item_data: Dict[str, Any]):
    """Create Excel export for a specific item."""
    with st.spinner("Erstelle Item-Excel-Export..."):
        try:
            # Create DataFrame with item data
            df = pd.DataFrame([item_data])

            # Create Excel file
            excel_path = Path.home() / "Downloads" / f"item_{item_data.get('article_number', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(excel_path, index=False)

            st.success(f"✅ Item-Excel-Export erstellt: {excel_path.name}")
            st.info(f"📁 Gespeichert unter: {excel_path}")

        except Exception as e:
            st.error(f"❌ Fehler beim Item-Excel-Export: {e}")
            logger.error(f"Error creating item Excel export: {e}")


# ================================
# BULK OPERATIONS
# ================================

def _bulk_create_delivery_documents(delivery_service):
    """Create documents for all deliveries."""
    with st.spinner("Erstelle Dokumente für alle Lieferungen..."):
        try:
            deliveries_data = delivery_service.get_all_deliveries()
            if deliveries_data:
                success_count = 0
                error_count = 0

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, delivery in enumerate(deliveries_data):
                    delivery_number = delivery['delivery_number']
                    status_text.text(f"Verarbeite Lieferung {delivery_number}...")

                    try:
                        # FIXED: Use standardized services instead of enhanced_document_service
                        from warehouse.application.services.delivery_workflow_service import DeliveryWorkflowService

                        workflow_service = DeliveryWorkflowService()
                        result = workflow_service.create_delivery_documents(
                            delivery_number=delivery_number,
                            open_documents=False,
                            create_folder=True
                        )

                        if result['success']:
                            success_count += 1
                        else:
                            error_count += 1

                    except Exception as delivery_e:
                        error_count += 1
                        logger.error(f"Error processing delivery {delivery_number}: {delivery_e}")

                    progress_bar.progress((i + 1) / len(deliveries_data))

                status_text.text("")
                progress_bar.empty()

                st.success(f"✅ Bulk-Operation abgeschlossen: {success_count} erfolgreich, {error_count} Fehler")
            else:
                st.warning("⚠️ Keine Lieferungen für Bulk-Operation gefunden")

        except Exception as e:
            st.error(f"❌ Fehler bei Bulk-Operation: {e}")
            logger.error(f"Error in bulk delivery documents creation: {e}")


def _bulk_generate_all_barcodes(item_service):
    """Generate barcodes for all items."""
    with st.spinner("Generiere Barcodes für alle Artikel..."):
        try:
            items_data = item_service.get_all_items() or []
            if items_data:
                success_count = 0
                error_count = 0

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, item in enumerate(items_data):
                    article_number = item.get('article_number', 'Unknown')
                    status_text.text(f"Verarbeite Artikel {article_number}...")

                    try:
                        from warehouse.application.services.document_generation.barcode_generator import BarcodeGenerator

                        barcode_gen = BarcodeGenerator()
                        article_result = barcode_gen.generate_barcode_png(
                            barcode_data=item.get('article_number', 'A001'),
                            output_filename=f"Article_{item.get('article_number', 'A001')}"
                        )
                        batch_result = barcode_gen.generate_barcode_png(
                            barcode_data=item.get('batch_number', 'B000001'),
                            output_filename=f"Batch_{item.get('batch_number', 'B000001')}"
                        )
                        result = article_result.success and batch_result.success

                        if result:
                            success_count += 1
                        else:
                            error_count += 1

                    except Exception as item_e:
                        error_count += 1
                        logger.error(f"Error creating barcode for {article_number}: {item_e}")

                    progress_bar.progress((i + 1) / len(items_data))

                status_text.text("")
                progress_bar.empty()

                st.success(f"✅ Barcode-Bulk-Operation abgeschlossen: {success_count} erfolgreich, {error_count} Fehler")
            else:
                st.warning("⚠️ Keine Artikel für Barcode-Bulk-Operation gefunden")

        except Exception as e:
            st.error(f"❌ Fehler bei Barcode-Bulk-Operation: {e}")
            logger.error(f"Error in bulk barcode generation: {e}")


# REMOVED: _bulk_create_visual_inspections function
# Sichtkontrolle documents should ONLY be created via the Visual Inspection Popup
# which handles user-entered waste quantities correctly. Bulk creation with
# hard-coded values defeats the purpose of visual inspection.


def _create_delivery_report_pdf(delivery_service):
    """Create delivery report PDF."""
    st.info("📄 PDF-Berichtserstellung - Funktion wird implementiert")
    # TODO: Implement PDF report generation


def _create_quality_report_pdf(item_service):
    """Create quality report PDF."""
    st.info("📄 Qualitätsbericht PDF-Erstellung - Funktion wird implementiert")
    # TODO: Implement quality PDF report generation


def _create_complete_excel_export(delivery_service, item_service):
    """Create complete Excel export with all data."""
    with st.spinner("Erstelle vollständigen Excel-Export..."):
        try:
            # Get all data
            deliveries_data = delivery_service.get_all_deliveries()
            items_data = item_service.get_all_items() or []

            if deliveries_data or items_data:
                excel_path = Path.home() / "Downloads" / f"complete_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    if deliveries_data:
                        df_deliveries = pd.DataFrame(deliveries_data)
                        df_deliveries.to_excel(writer, sheet_name='Deliveries', index=False)

                    if items_data:
                        df_items = pd.DataFrame(items_data)
                        df_items.to_excel(writer, sheet_name='Items', index=False)

                st.success(f"✅ Vollständiger Excel-Export erstellt: {excel_path.name}")
                st.info(f"📁 Gespeichert unter: {excel_path}")
            else:
                st.warning("⚠️ Keine Daten für vollständigen Export gefunden")

        except Exception as e:
            st.error(f"❌ Fehler beim vollständigen Excel-Export: {e}")
            logger.error(f"Error creating complete Excel export: {e}")


def _show_delivery_slip_upload_section():
    """Show delivery slip upload and processing section."""
    st.subheader("📥 Lieferschein Upload & Automatische Verarbeitung")
    st.write("Laden Sie Lieferscheine hoch für automatische Lieferanten-Erkennung und organisierte Speicherung.")

    # Upload interface
    uploaded_files = st.file_uploader(
        "Wählen Sie Lieferschein-Dateien zum Upload:",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Unterstützte Formate: PDF, PNG, JPG. Mehrere Dateien möglich."
    )

    if uploaded_files:
        st.write(f"📄 {len(uploaded_files)} Datei(en) ausgewählt:")
        for file in uploaded_files:
            st.write(f"• {file.name} ({file.size:,} bytes)")

        # Processing options
        st.write("### ⚙️ Verarbeitungsoptionen")

        col1, col2 = st.columns(2)
        with col1:
            hint_supplier = st.text_input(
                "Lieferanten-Hinweis (optional):",
                help="Falls bekannt, können Sie den Lieferantennamen eingeben um die Erkennung zu verbessern",
                key="delivery_slip_supplier_hint"
            )

        with col2:
            extract_structured = st.checkbox(
                "Strukturierte Daten extrahieren",
                value=True,
                help="Extrahiert zusätzlich strukturierte Daten wie Artikelnummern und Mengen",
                key="delivery_slip_extract_structured"
            )

        # Process button
        if st.button("🚀 Lieferscheine verarbeiten", type="primary", use_container_width=True):
            _process_delivery_slips(uploaded_files, hint_supplier, extract_structured)

    # Show recent uploads if any
    _show_recent_delivery_slip_uploads()


def _process_delivery_slips(uploaded_files, hint_supplier: str, extract_structured: bool):
    """Process uploaded delivery slip files."""
    try:
        from warehouse.application.services.document_processing.document_processing_service import document_processing_service

        total_files = len(uploaded_files)
        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []
        success_count = 0
        error_count = 0

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Verarbeite {uploaded_file.name}...")

            try:
                # Read file data
                file_data = uploaded_file.read()

                # Prepare context
                context = {
                    'extract_structured_data': extract_structured
                }
                if hint_supplier and hint_supplier.strip():
                    context['hint_supplier'] = hint_supplier.strip()

                # Process delivery slip using unified document processing
                context['document_data'] = file_data  # Add document_data for PDF storage
                result = document_processing_service.process_document(
                    document_data=file_data,
                    document_type="delivery",
                    context=context
                )

                results.append({
                    'filename': uploaded_file.name,
                    'result': result
                })

                if result.get('success'):
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1
                results.append({
                    'filename': uploaded_file.name,
                    'result': {
                        'success': False,
                        'error': f"Upload-Fehler: {str(e)}",
                        'stage': 'upload'
                    }
                })
                logger.error(f"Error processing {uploaded_file.name}: {e}")

            progress_bar.progress((i + 1) / total_files)

        # Clear progress indicators
        status_text.text("")
        progress_bar.empty()

        # Show results
        st.write("### 📊 Verarbeitungsergebnisse")

        if success_count > 0:
            st.success(f"✅ {success_count} Lieferschein(e) erfolgreich verarbeitet")

        if error_count > 0:
            st.error(f"❌ {error_count} Fehler aufgetreten")

        # Detailed results
        for result_data in results:
            filename = result_data['filename']
            result = result_data['result']

            with st.expander(f"📄 {filename} - {'✅ Erfolg' if result.get('success') else '❌ Fehler'}"):
                if result.get('success'):
                    # Success case
                    supplier_info = result.get('supplier_detection', {})
                    storage_info = result.get('storage', {})

                    st.write("**Lieferanten-Erkennung:**")
                    st.write(f"• Lieferant: {supplier_info.get('supplier_name', 'Unbekannt')}")
                    st.write(f"• Confidence: {supplier_info.get('confidence', 0):.1%}")

                    if supplier_info.get('delivery_number'):
                        st.write(f"• Lieferscheinnummer: {supplier_info.get('delivery_number')}")

                    if supplier_info.get('delivery_date'):
                        st.write(f"• Lieferdatum: {supplier_info.get('delivery_date')}")

                    st.write("**Speicherung:**")
                    st.write(f"• Pfad: {storage_info.get('file_path', 'Unbekannt')}")

                    # Show detected items if available
                    detected_items = result.get('detected_items', [])
                    if detected_items:
                        st.write("**Erkannte Artikel:**")
                        for item in detected_items[:5]:  # Show first 5 items
                            article_num = item.get('article_number', 'Unbekannt')
                            quantity = item.get('quantity', 'Unbekannt')
                            description = item.get('description', '')
                            st.write(f"• {article_num}: {quantity} ({description[:50]}...)" if len(description) > 50 else f"• {article_num}: {quantity} ({description})")

                        if len(detected_items) > 5:
                            st.write(f"... und {len(detected_items) - 5} weitere Artikel")

                    # Show warnings if any
                    warnings = supplier_info.get('warnings', [])
                    if warnings:
                        st.write("**Warnungen:**")
                        for warning in warnings:
                            st.warning(warning)

                else:
                    # Error case
                    st.error(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
                    st.write(f"Stage: {result.get('stage', 'Unbekannt')}")

    except Exception as e:
        st.error(f"❌ Allgemeiner Verarbeitungsfehler: {e}")
        logger.error(f"General processing error: {e}")


def _show_recent_delivery_slip_uploads():
    """Show recent delivery slip uploads from storage."""
    try:
        from warehouse.application.services.service_registry import get_document_storage_service
        storage_service = get_document_storage_service()

        st.write("### 📁 Kürzlich verarbeitete Lieferscheine")

        # Get recent files (this would need to be implemented in the storage service)
        if hasattr(storage_service, 'get_recent_delivery_slips'):
            recent_files = storage_service.get_recent_delivery_slips(limit=10)

            if recent_files:
                for file_info in recent_files:
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"📄 {file_info.get('filename', 'Unbekannt')}")
                        st.caption(f"Lieferant: {file_info.get('supplier_name', 'Unbekannt')}")

                    with col2:
                        upload_date = file_info.get('upload_date', 'Unbekannt')
                        st.write(f"📅 {upload_date}")

                    with col3:
                        if st.button("📁", key=f"open_{file_info.get('id', 'unknown')}", help="Ordner öffnen"):
                            # Open folder functionality
                            file_path = file_info.get('file_path')
                            if file_path:
                                import os
                                import platform
                                import subprocess

                                folder_path = Path(file_path).parent
                                try:
                                    if platform.system() == "Windows":
                                        os.startfile(str(folder_path))
                                    elif platform.system() == "Darwin":  # macOS
                                        subprocess.run(["open", str(folder_path)], check=False)
                                    else:  # Linux
                                        subprocess.run(["xdg-open", str(folder_path)], check=False)
                                    st.success("✅ Ordner geöffnet")
                                except Exception as e:
                                    st.error(f"Fehler beim Öffnen: {e}")
            else:
                st.info("Noch keine Lieferscheine verarbeitet")
        else:
            st.info("Funktion für kürzlich verarbeitete Dateien wird implementiert")

    except Exception as e:
        st.error(f"Fehler beim Laden der kürzlichen Uploads: {e}")
        logger.error(f"Error loading recent uploads: {e}")