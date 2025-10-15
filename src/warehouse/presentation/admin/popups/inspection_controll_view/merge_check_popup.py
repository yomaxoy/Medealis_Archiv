"""
Merge Check Popup
Combined document checking and merging functionality with database integration.
"""

import streamlit as st
from pathlib import Path
from typing import Dict, List, Any
import logging
from warehouse.application.services.entity_services.item_service import ItemService

logger = logging.getLogger(__name__)


@st.dialog("📁 Dokumente prüfen & zusammenführen", width="large")
def show_merge_check_popup(item_data):
    """Show combined document check and merge popup."""
    st.write("### 📁 Dokumente prüfen & zusammenführen")
    st.write(
        f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}"
    )
    st.write(
        f"**Lieferung:** {item_data['delivery_number']} | **Menge:** {item_data['quantity']}"
    )

    st.write("---")

    # === ARTIKEL-ORDNER ERMITTELN ===
    folder_path = None
    try:
        from warehouse.application.services import determine_manufacturer
        from warehouse.application.services.service_registry import get_document_storage_service

        # Bestimme Hersteller für Pfad
        manufacturer = determine_manufacturer(item_data.get("article_number", ""))

        # Hole Supplier-Name aus Delivery-Daten
        supplier_name = "Primec"  # Fallback
        try:
            from warehouse.application.services.service_registry import get_data_integration_service
            data_integration_service = get_data_integration_service()

            delivery_data = data_integration_service.get_complete_delivery_data(
                item_data.get("delivery_number", ""), item_data.get("batch_number", "")
            )
            if delivery_data and "supplier_name" in delivery_data:
                supplier_name = delivery_data["supplier_name"]
        except Exception:
            pass

        # Normalisiere bekannte Supplier-IDs
        if supplier_name == "10006":
            supplier_name = "Primec"
        elif not supplier_name or supplier_name.strip() == "":
            supplier_name = "Primec"

        # FIXED: Add supplier_name to item_data for later use
        item_data["supplier_name"] = supplier_name

        storage_service = get_document_storage_service()
        folder_path, path_warnings = storage_service.get_document_path(
            batch_number=item_data.get("batch_number", ""),
            delivery_number=item_data.get("delivery_number", ""),
            article_number=item_data.get("article_number", ""),
            supplier_name=supplier_name,
            create_folders=False,
        )

        # Show path warnings if any
        if path_warnings:
            for warning in path_warnings:
                st.warning(f"⚠️ {warning}")

        # Zeige Ordnerpfad
        st.write("**📂 Artikel-Ordner:**")
        col_path, col_open = st.columns([3, 1])
        with col_path:
            st.code(str(folder_path), language=None)
        with col_open:
            if st.button("📂 Öffnen", key="merge_open_folder_btn"):
                try:
                    folder_path.mkdir(parents=True, exist_ok=True)
                    import subprocess
                    import platform

                    if platform.system() == "Windows":
                        subprocess.run(["explorer", str(folder_path)], check=True)
                    elif platform.system() == "Darwin":
                        subprocess.run(["open", str(folder_path)], check=True)
                    else:
                        subprocess.run(["xdg-open", str(folder_path)], check=True)
                    st.success("📂 Ordner geöffnet!")
                except Exception as e:
                    st.error(f"❌ Fehler beim Öffnen: {e}")

    except Exception as e:
        st.error(f"❌ Fehler beim Ermitteln des Ordnerpfads: {e}")
        return

    st.write("---")

    # === PERFORMANCE OPTIMIZATION: Load documents only ONCE ===
    # Cache key für Session-basiertes Caching
    cache_key = f"merge_docs_{item_data.get('batch_number', '')}_{item_data.get('delivery_number', '')}"

    # Lade Dokumente nur einmal pro Session
    if cache_key not in st.session_state:
        with st.spinner("📥 Lade Dokumente von SharePoint..."):
            all_documents = get_all_merge_files_from_storage(item_data, folder_path)
            st.session_state[cache_key] = all_documents
    else:
        all_documents = st.session_state[cache_key]

    # === DOKUMENTE SCANNEN ===
    st.write("### 📋 Dokumente-Status")

    # PERFORMANCE: Use cached documents for status display
    scanned_docs = create_scan_result_from_documents(all_documents, item_data)
    show_document_status_matrix(scanned_docs, item_data)

    st.write("---")

    # === ERWEITERTE MERGE-FUNKTIONALITÄT ===
    # Use cached documents
    all_merge_files = all_documents

    # Prüfe ob zusätzlicher Lieferschein gefunden wurde
    delivery_slip_from_supplier = find_delivery_slip_in_supplier_folder(item_data)
    delivery_slip_added = False
    if delivery_slip_from_supplier:
        # Prüfe ob Lieferschein bereits in den Dateien enthalten ist
        already_included = any(f.name == delivery_slip_from_supplier.name for f in all_merge_files)

        if not already_included:
            # FIXED: Add delivery slip to merge files list!
            all_merge_files.append(delivery_slip_from_supplier)
            delivery_slip_added = True
            st.info(f"📄 **Lieferschein automatisch hinzugefügt:** {delivery_slip_from_supplier.name}")
            st.caption(f"📁 Aus: {delivery_slip_from_supplier.parent}")

            # Re-sort files after adding delivery slip
            all_merge_files = sort_files_by_document_type(all_merge_files)

    # FILTER: Begleitschein und Wareneingang NICHT in Merge einbeziehen
    excluded_merge_files = []
    filtered_merge_files = []
    for file in all_merge_files:
        file_name_lower = file.name.lower()
        if "begleitschein" in file_name_lower or "wareneingang" in file_name_lower:
            excluded_merge_files.append(file)
        else:
            filtered_merge_files.append(file)

    all_merge_files = filtered_merge_files

    # Show info if files were excluded
    if excluded_merge_files:
        st.info(f"ℹ️ {len(excluded_merge_files)} Dokument(e) automatisch ausgeschlossen: {', '.join([f.name for f in excluded_merge_files])}")
        st.caption("💡 Begleitschein und Wareneingang werden nicht in zusammengeführte Dokumente einbezogen")

    if all_merge_files:
        st.write("### 🔗 Dokumente zusammenführen")

        # Zeige verfügbare PDF-Dateien (jetzt sortiert und mit Lieferschein)
        st.write("**📄 Verfügbare PDF-Dateien für Merge:**")

        if delivery_slip_added:
            st.caption("💡 Dateien sind automatisch in der optimalen Reihenfolge sortiert (PDB → Vermessungsprotokoll → Sichtkontrolle → Bestellung → Lieferschein → Begleitpapiere)")

        selected_files = []
        for pdf_file in all_merge_files:
            col_check, col_name, col_size = st.columns([1, 4, 1])

            with col_check:
                if st.checkbox(
                    "Auswählen",
                    key=f"select_{pdf_file.name}",
                    value=True,
                    label_visibility="collapsed",
                ):
                    selected_files.append(pdf_file)

            with col_name:
                st.write(f"📄 {pdf_file.name}")

            with col_size:
                try:
                    file_size = pdf_file.stat().st_size / 1024  # KB
                    st.write(f"{file_size:.1f} KB")
                except:
                    st.write("?")

        if selected_files:
            st.write("---")

            # Merge-Optionen
            col_name, col_cover = st.columns(2)

            with col_name:
                output_filename = st.text_input(
                    "📄 Dateiname für zusammengeführtes Dokument:",
                    value=f"{item_data.get('batch_number', 'CHARGE')}_{item_data.get('article_number', 'ARTIKEL')}_{item_data.get('delivery_number', 'LIEFERUNG')}.pdf",
                    key="merge_output_filename",
                )

            with col_cover:
                include_cover = st.checkbox(
                    "📋 Deckblatt hinzufügen", value=True, key="merge_include_cover"
                )
                if include_cover:
                    cover_title = st.text_input(
                        "Deckblatt Titel:",
                        value=f"Dokumentation {item_data.get('article_number', 'N/A')} - Charge {item_data.get('batch_number', 'N/A')}",
                        key="merge_cover_title",
                    )

            # Merge-Button
            col_merge, col_preview = st.columns(2)

            with col_preview:
                if st.button(
                    "👁️ Vorschau", key="merge_preview_btn", use_container_width=True
                ):
                    show_merge_preview(selected_files)

            with col_merge:
                if st.button(
                    "🔗 Zusammenführen",
                    key="merge_execute_btn",
                    use_container_width=True,
                    type="primary",
                ):
                    execute_merge(
                        selected_files,
                        folder_path,
                        output_filename,
                        include_cover,
                        cover_title if include_cover else None,
                        item_data,
                    )

        else:
            st.info("ℹ️ Wählen Sie mindestens eine PDF-Datei für den Merge aus.")

    else:
        # Zeige Information basierend auf verfügbaren Dateien
        if delivery_slip_from_supplier:
            st.info("📄 Nur Lieferschein aus Lieferanten-Ordner gefunden - weitere PDFs im Artikel-Ordner hinzufügen für Merge.")
        else:
            st.warning("⚠️ Keine PDF-Dateien für Merge verfügbar.")

    # === FUTURE: KI-ANALYSE SEKTION ===
    merged_file = check_for_merged_file(folder_path, item_data)
    if merged_file:
        st.write("---")
        st.write("### 🤖 KI-Analyse (kommt im nächsten Schritt)")
        st.info(
            "📊 Zusammengeführte Datei gefunden - KI-Analyse wird in der nächsten Phase implementiert"
        )

        col_ai_btn, col_info = st.columns(2)
        with col_ai_btn:
            if st.button("🤖 KI-Analyse starten", key="ai_analysis_btn", disabled=True):
                st.info("🚧 Wird im nächsten Implementierungsschritt verfügbar")

        with col_info:
            st.write(f"📄 **Datei:** {merged_file.name}")
            try:
                file_size = merged_file.stat().st_size / (1024 * 1024)  # MB
                st.write(f"📊 **Größe:** {file_size:.1f} MB")
            except:
                pass

    # === BUTTONS ===
    st.write("---")
    col_close, col_refresh, col_clear_cache = st.columns(3)

    with col_clear_cache:
        if st.button(
            "🗑️ Cache leeren", key="merge_clear_cache_btn", use_container_width=True
        ):
            # Clear document cache to force re-download
            if cache_key in st.session_state:
                del st.session_state[cache_key]
                st.success("✅ Cache geleert - Dokumente werden neu geladen")
            st.rerun()

    with col_refresh:
        if st.button(
            "🔄 Aktualisieren", key="merge_refresh_btn", use_container_width=True
        ):
            st.rerun()

    with col_close:
        if st.button("❌ Schließen", key="merge_close_btn", use_container_width=True):
            st.rerun()


def scan_folder_for_documents(folder_path: Path) -> Dict[str, Any]:
    """
    Scan folder for documents and categorize them.

    DEPRECATED: Use scan_documents_from_storage() for SharePoint + Local fallback.
    This function is kept for backwards compatibility with legacy local-only code.
    """
    scan_result = {
        "folder_exists": False,
        "total_files": 0,
        "pdf_files": [],
        "other_files": [],
        "document_categories": {
            "pdb": [],
            "sichtkontrolle": [],
            "vermessung": [],
            "bestellung": [],
            "lieferschein": [],
            "begleitpapiere": [],
            "unknown": [],
        },
    }

    if not folder_path or not folder_path.exists():
        return scan_result

    scan_result["folder_exists"] = True

    try:
        # Alle Dateien im Ordner finden
        all_files = [f for f in folder_path.iterdir() if f.is_file()]
        scan_result["total_files"] = len(all_files)

        # PDF-Dateien separieren
        pdf_files = [f for f in all_files if f.suffix.lower() == ".pdf"]
        other_files = [f for f in all_files if f.suffix.lower() != ".pdf"]

        scan_result["pdf_files"] = pdf_files
        scan_result["other_files"] = other_files

        # Kategorisierung
        scan_result = _categorize_files(all_files, scan_result)

    except Exception as e:
        logger.error(f"Error scanning folder {folder_path}: {e}")

    return scan_result


def create_scan_result_from_documents(documents: List[Path], item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    PERFORMANCE OPTIMIZATION: Create scan result from already-loaded documents.
    Avoids redundant SharePoint downloads.

    Args:
        documents: List of already-downloaded document Paths
        item_data: Item metadata (for source tracking)

    Returns:
        Dict with scan results and categorized documents
    """
    scan_result = {
        "folder_exists": bool(documents),
        "total_files": len(documents),
        "pdf_files": [f for f in documents if f.suffix.lower() == ".pdf"],
        "other_files": [f for f in documents if f.suffix.lower() != ".pdf"],
        "document_categories": {
            "pdb": [],
            "sichtkontrolle": [],
            "vermessung": [],
            "bestellung": [],
            "lieferschein": [],
            "begleitpapiere": [],
            "unknown": [],
        },
        "source": "sharepoint",  # Assume SharePoint since we're using storage service
    }

    if documents:
        scan_result = _categorize_files(documents, scan_result)

    return scan_result


def scan_documents_from_storage(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan documents from storage (SharePoint → Local fallback).

    Uses DocumentStorageService with PathResolver for proper storage detection:
    1. Primary: List documents from SharePoint
    2. Fallback: Scan local folder if SharePoint unavailable

    Args:
        item_data: Dict with batch_number, delivery_number, article_number, supplier_name

    Returns:
        Dict with scan results and categorized documents
    """
    scan_result = {
        "folder_exists": False,
        "total_files": 0,
        "pdf_files": [],
        "other_files": [],
        "document_categories": {
            "pdb": [],
            "sichtkontrolle": [],
            "vermessung": [],
            "bestellung": [],
            "lieferschein": [],
            "begleitpapiere": [],
            "unknown": [],
        },
        "source": "unknown",  # 'sharepoint', 'local', or 'unknown'
        "storage_path": None,
    }

    try:
        from warehouse.application.services.service_registry import get_document_storage_service
        storage_service = get_document_storage_service()

        if not storage_service:
            logger.warning("[DOC SCAN] DocumentStorageService not available, using legacy local scan")
            # Fallback to legacy local scan
            from warehouse.application.services.document_storage.path_resolver import PathResolver
            path_resolver = PathResolver()
            local_path = path_resolver.resolve_storage_path(
                batch_number=item_data.get('batch_number', ''),
                delivery_number=item_data.get('delivery_number', ''),
                article_number=item_data.get('article_number', ''),
                supplier_name=item_data.get('supplier_name', '')
            )
            if local_path:
                return scan_folder_for_documents(local_path)
            return scan_result

        # Get documents using DocumentStorageService.get_documents_for_merge (SharePoint → Local)
        logger.info(f"[DOC SCAN] Scanning documents from storage for batch: {item_data.get('batch_number', '')}")

        # Use get_documents_for_merge which handles SharePoint → Local fallback
        documents = storage_service.get_documents_for_merge(
            batch_number=item_data.get('batch_number', ''),
            delivery_number=item_data.get('delivery_number', ''),
            article_number=item_data.get('article_number', ''),
            supplier_name=item_data.get('supplier_name', '')
        )

        if not documents:
            logger.warning("[DOC SCAN] No documents found in storage")
            return scan_result

        # Documents are returned as List[Path] (either temp files from SharePoint or local paths)
        all_files = documents
        scan_result["folder_exists"] = True
        scan_result["total_files"] = len(all_files)

        # Separate PDFs
        pdf_files = [f for f in all_files if f.suffix.lower() == ".pdf"]
        other_files = [f for f in all_files if f.suffix.lower() != ".pdf"]

        scan_result["pdf_files"] = pdf_files
        scan_result["other_files"] = other_files

        # Kategorisierung
        scan_result = _categorize_files(all_files, scan_result)

        # Detect source from DocumentStorageService
        scan_result["source"] = getattr(storage_service, 'last_merge_source', 'unknown')

        logger.info(f"[DOC SCAN] Found {len(all_files)} documents from {scan_result['source']}")

    except Exception as e:
        logger.error(f"[DOC SCAN] Error scanning documents from storage: {e}")
        # Final fallback to legacy local scan
        from warehouse.application.services.document_storage.path_resolver import PathResolver
        path_resolver = PathResolver()
        local_path = path_resolver.resolve_storage_path(
            batch_number=item_data.get('batch_number', ''),
            delivery_number=item_data.get('delivery_number', ''),
            article_number=item_data.get('article_number', ''),
            supplier_name=item_data.get('supplier_name', '')
        )
        if local_path:
            result = scan_folder_for_documents(local_path)
            result["source"] = "local"
            return result

    return scan_result


def _categorize_files(all_files: List[Path], scan_result: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to categorize files by document type."""
    for file in all_files:
        file_name_lower = file.name.lower()

        # WICHTIG: Reihenfolge ist wichtig! Spezifischere Patterns zuerst prüfen
        if any(
            pattern in file_name_lower for pattern in ["pdb", "produktdatenblatt"]
        ):
            scan_result["document_categories"]["pdb"].append(file)
        elif any(
            pattern in file_name_lower
            for pattern in ["sichtkontrolle", "fo00141", "visuell"]
        ):
            scan_result["document_categories"]["sichtkontrolle"].append(file)
        elif any(
            pattern in file_name_lower
            for pattern in [
                "vermessungsprotokoll_",
                "vermessung",
                "messung",
                "protokoll",
            ]
        ):
            scan_result["document_categories"]["vermessung"].append(file)
        elif any(
            pattern in file_name_lower
            for pattern in ["bestellung", "order", "bestell"]
        ):
            scan_result["document_categories"]["bestellung"].append(file)
        # FIXED: Check Begleitschein/Begleitpapiere BEFORE Lieferschein
        # "Begleitschein_LS25-222" contains "ls" but is NOT a Lieferschein!
        elif any(
            pattern in file_name_lower
            for pattern in [
                "begleitschein",  # Match Begleitschein specifically
                "begleitpapiere_",
                "begleit",
                "zertifikat",
                "certificate",
                "accompany",
            ]
        ):
            scan_result["document_categories"]["begleitpapiere"].append(file)
        elif any(
            pattern in file_name_lower
            for pattern in ["lieferschein", "delivery"]  # Removed "ls" - too generic!
        ):
            scan_result["document_categories"]["lieferschein"].append(file)
        else:
            scan_result["document_categories"]["unknown"].append(file)

    return scan_result


def show_document_status_matrix(scanned_docs: Dict[str, Any], item_data: Dict[str, Any] = None):
    """Display document status matrix with enhanced delivery slip detection and source information."""
    if not scanned_docs["folder_exists"]:
        st.error("❌ Keine Dokumente gefunden (weder SharePoint noch lokal)")
        return

    # Show source information
    source = scanned_docs.get("source", "unknown")
    if source == "sharepoint":
        st.info("📡 **Quelle:** SharePoint (Online)")
    elif source == "local":
        st.info("💾 **Quelle:** Lokaler Ordner (Fallback)")
    else:
        st.warning("❓ **Quelle:** Unbekannt")

    st.write(
        f"**📊 Gefundene Dateien:** {scanned_docs['total_files']} gesamt, {len(scanned_docs['pdf_files'])} PDFs"
    )

    # Check for delivery slip in supplier folder if not found in article folder
    delivery_slip_in_supplier = None
    if item_data and not scanned_docs["document_categories"]["lieferschein"]:
        delivery_slip_in_supplier = find_delivery_slip_in_supplier_folder(item_data)

    # Document categories status
    categories = {
        "📋 PDB": scanned_docs["document_categories"]["pdb"],
        "👁️ Sichtkontrolle": scanned_docs["document_categories"]["sichtkontrolle"],
        "📏 Vermessungsprotokoll": scanned_docs["document_categories"]["vermessung"],
        "📋 Bestellung": scanned_docs["document_categories"]["bestellung"],
        "📄 Lieferschein": scanned_docs["document_categories"]["lieferschein"],
        "📦 Begleitpapiere": scanned_docs["document_categories"]["begleitpapiere"],
    }

    for category_name, files in categories.items():
        col_status, col_files = st.columns([1, 3])

        with col_status:
            # Special handling for delivery slip
            if category_name == "📄 Lieferschein":
                if files:
                    st.success(f"✅ {category_name}")
                elif delivery_slip_in_supplier:
                    st.success(f"✅ {category_name} (extern)")
                else:
                    st.error(f"❌ {category_name}")
            else:
                if files:
                    st.success(f"✅ {category_name}")
                else:
                    st.error(f"❌ {category_name}")

        with col_files:
            if category_name == "📄 Lieferschein":
                if files:
                    file_names = [f.name for f in files]
                    st.write(", ".join(file_names))
                elif delivery_slip_in_supplier:
                    st.write(f"📁 {delivery_slip_in_supplier.name} (aus Lieferanten-Ordner)")
                else:
                    st.write("Nicht gefunden")
            else:
                if files:
                    file_names = [f.name for f in files]
                    st.write(", ".join(file_names))
                else:
                    st.write("Nicht gefunden")

    # Unknown files
    if scanned_docs["document_categories"]["unknown"]:
        st.write("**🤷 Nicht kategorisierte Dateien:**")
        unknown_names = [f.name for f in scanned_docs["document_categories"]["unknown"]]
        st.write(", ".join(unknown_names))


def show_merge_preview(selected_files: List[Path]):
    """Show merge preview information."""
    try:
        from warehouse.application.services.service_registry import get_pdf_merge_service
        pdf_merge_service = get_pdf_merge_service()

        preview = pdf_merge_service.get_merge_preview(selected_files)

        st.write("**🔍 Merge-Vorschau:**")
        st.write(f"📄 **PDF-Dateien:** {preview['pdf_files']}")
        st.write(f"📊 **Gesamtgröße:** {preview['total_size_mb']:.1f} MB")

        if preview["warnings"]:
            st.write("⚠️ **Warnungen:**")
            for warning in preview["warnings"]:
                st.warning(warning)

        if preview["mergeable"]:
            st.success("✅ Dateien können zusammengeführt werden")
        else:
            st.error("❌ Dateien können nicht zusammengeführt werden")

    except Exception as e:
        st.error(f"❌ Fehler bei der Vorschau: {e}")


def execute_merge(
    selected_files: List[Path],
    folder_path: Path,
    output_filename: str,
    include_cover: bool,
    cover_title: str,
    item_data: Dict[str, Any],
):
    """Execute the PDF merge operation."""
    try:
        from warehouse.application.services.service_registry import get_pdf_merge_service
        pdf_merge_service = get_pdf_merge_service()

        # Validierung
        validation = pdf_merge_service.validate_merge_input(
            selected_files, folder_path / output_filename
        )

        if not validation["valid"]:
            st.error("❌ Merge nicht möglich:")
            for error in validation["errors"]:
                st.error(f"  • {error}")
            return

        # Warnungen anzeigen
        if validation["warnings"]:
            for warning in validation["warnings"]:
                st.warning(f"⚠️ {warning}")

        # Progress indicator
        with st.spinner("🔗 Führe PDFs zusammen..."):
            output_path = folder_path / output_filename

            success = pdf_merge_service.merge_pdfs(
                file_paths=selected_files,
                output_path=output_path,
                include_cover=include_cover,
                cover_title=cover_title,
                sort_by_document_order=True,
                article_number=item_data.get("article_number", ""),
                batch_number=item_data.get("batch_number", ""),
                delivery_number=item_data.get("delivery_number", ""),
                supplier_name=item_data.get("supplier_name", "")
            )

        if success:
            st.success(f"✅ PDFs erfolgreich zusammengeführt!")
            st.info(f"📄 **Datei erstellt:** {output_filename}")
            st.info(f"📁 **Lokaler Speicherort:** {folder_path}")

            # Upload merged PDF to SharePoint
            try:
                from warehouse.application.services.service_registry import get_document_storage_service
                storage_service = get_document_storage_service()

                if storage_service:
                    with st.spinner("📤 Lade gemergtes PDF auf SharePoint hoch..."):
                        # Read merged PDF
                        with open(output_path, 'rb') as f:
                            pdf_data = f.read()

                        # Upload to SharePoint
                        upload_result = storage_service.save_document(
                            document_data=pdf_data,
                            document_name=output_filename,
                            document_type="merged_pdf",
                            batch_number=item_data.get("batch_number", ""),
                            delivery_number=item_data.get("delivery_number", ""),
                            article_number=item_data.get("article_number", ""),
                            supplier_name=item_data.get("supplier_name", "")
                        )

                        if upload_result.success and upload_result.sharepoint_url:
                            st.success(f"✅ **Gemergtes PDF auf SharePoint hochgeladen!**")
                            st.info(f"📡 **SharePoint URL:** {upload_result.sharepoint_url}")
                        elif upload_result.success:
                            st.info("💾 Nur lokal gespeichert (SharePoint nicht verfügbar)")
                        else:
                            st.warning(f"⚠️ SharePoint-Upload fehlgeschlagen: {upload_result.error}")

            except Exception as e:
                logger.error(f"Error uploading merged PDF to SharePoint: {e}")
                st.warning(f"⚠️ SharePoint-Upload fehlgeschlagen: {str(e)}")

            # Store merge info in database via item service
            try:
                from warehouse.application.services.service_registry import get_item_service
                item_service = get_item_service()

                # Create merge record in item notes
                merge_note = f"PDF-Merge: {output_filename} ({', '.join([f.name for f in selected_files])}) - {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}"

                # Get current item and update notes
                article_number = item_data.get("article_number")
                batch_number = item_data.get("batch_number")
                delivery_number = item_data.get("delivery_number")

                item = item_service.get_item(
                    article_number, batch_number, delivery_number
                )
                if item:
                    current_notes = item.get("notes", "")
                    updated_notes = (
                        f"{current_notes}\n{merge_note}"
                        if current_notes
                        else merge_note
                    )

                    success = item_service.update_item_notes(
                        article_number=article_number,
                        batch_number=batch_number,
                        delivery_number=delivery_number,
                        notes=updated_notes,
                    )

                    if success:
                        st.success("✅ Merge-Information in der Datenbank gespeichert")
                    else:
                        st.warning(
                            "⚠️ Datenbankupdate für Merge-Information fehlgeschlagen"
                        )
                else:
                    st.warning(
                        "⚠️ Item nicht in der Datenbank gefunden für Merge-Dokumentation"
                    )

            except Exception as e:
                logger.error(f"Error storing merge info in database: {e}")
                st.warning(f"⚠️ Fehler beim Speichern der Merge-Information: {str(e)}")

            # Auto-refresh to show new file
            st.rerun()
        else:
            st.error("❌ Fehler beim Zusammenführen der PDFs")

    except Exception as e:
        logger.error(f"Merge execution error: {e}")
        st.error(f"❌ Fehler beim Merge: {e}")


def check_for_merged_file(folder_path: Path, item_data: Dict[str, Any]) -> Path:
    """Check if a merged file already exists."""
    if not folder_path or not folder_path.exists():
        return None

    try:
        # Look for files that might be merged documents
        potential_merged_files = []

        for file in folder_path.glob("*.pdf"):
            file_name_lower = file.name.lower()
            if any(
                keyword in file_name_lower
                for keyword in ["komplett", "merged", "dokumentation", "combined"]
            ):
                potential_merged_files.append(file)

        # Return the most recent one
        if potential_merged_files:
            return max(potential_merged_files, key=lambda f: f.stat().st_mtime)

    except Exception as e:
        logger.error(f"Error checking for merged file: {e}")

    return None


def find_delivery_slip_in_supplier_folder(item_data: Dict[str, Any]) -> Path:
    """
    Sucht Lieferschein im Lieferanten/Lieferscheine Ordner.

    Args:
        item_data: Dict mit delivery_number, supplier_name, etc.

    Returns:
        Path zum Lieferschein oder None wenn nicht gefunden
    """
    try:
        logger.info(f"Searching for delivery slip for delivery: {item_data.get('delivery_number', 'N/A')}")

        # Ermittle Supplier-Name (gleiche Logik wie im Hauptbereich)
        supplier_name = "Primec"  # Fallback
        try:
            from warehouse.application.services.service_registry import get_data_integration_service
            data_integration_service = get_data_integration_service()

            delivery_data = data_integration_service.get_complete_delivery_data(
                item_data.get("delivery_number", ""), item_data.get("batch_number", "")
            )
            if delivery_data and "supplier_name" in delivery_data:
                supplier_name = delivery_data["supplier_name"]
        except Exception as e:
            logger.warning(f"Could not get supplier name from delivery data: {e}")

        # NUTZE GLEICHE NORMALISIERUNG WIE PATH_RESOLVER (unified storage_context)
        from warehouse.application.services.document_storage.storage_context import storage_context
        from warehouse.application.services.service_registry import get_document_storage_service

        # Nutze einheitliche storage_context Normalisierung
        normalized_supplier = storage_context._basic_supplier_normalization(supplier_name)
        # Path cleaning für Dateisystem-Sicherheit
        normalized_supplier = normalized_supplier.replace(" ", "_")

        # Basis-Pfad mit normalisiertem Supplier-Namen
        storage_service = get_document_storage_service()
        base_path = storage_service.path_resolver.base_storage_path
        delivery_slip_folder = base_path / normalized_supplier / "Lieferscheine"

        logger.info(f"Looking for delivery slips in: {delivery_slip_folder}")

        if not delivery_slip_folder.exists():
            logger.warning(f"Delivery slip folder does not exist: {delivery_slip_folder}")
            return None

        # Suche nach PDF-Dateien mit passender Liefernummer
        delivery_number = item_data.get("delivery_number", "").strip()
        if not delivery_number:
            logger.warning("No delivery number provided for delivery slip search")
            return None

        # Durchsuche alle PDF-Dateien im Lieferscheine-Ordner
        for pdf_file in delivery_slip_folder.glob("*.pdf"):
            file_name_lower = pdf_file.name.lower()
            delivery_number_lower = delivery_number.lower()

            # Verschiedene Namens-Patterns prüfen
            if (delivery_number_lower in file_name_lower or
                f"ls_{delivery_number_lower}" in file_name_lower or
                f"lieferschein_{delivery_number_lower}" in file_name_lower or
                f"{delivery_number_lower}_" in file_name_lower):

                logger.info(f"Found delivery slip: {pdf_file}")
                return pdf_file

        logger.warning(f"No delivery slip found for delivery number: {delivery_number}")
        return None

    except Exception as e:
        logger.error(f"Error searching for delivery slip: {e}")
        return None


def sort_files_by_document_type(pdf_files: List[Path]) -> List[Path]:
    """
    Sortiert PDF-Dateien nach Dokumenttyp in sinnvoller Reihenfolge.

    Reihenfolge (User-definiert):
    1. PDB (Produktdatenblatt)
    2. Vermessungsprotokoll (ggf. mehrere)
    3. Sichtkontrolle
    4. Bestellung
    5. Lieferschein
    6. Begleitpapiere
    7. Sonstige

    Args:
        pdf_files: Liste der PDF-Dateien

    Returns:
        Sortierte Liste der PDF-Dateien
    """
    try:
        logger.info(f"Sorting {len(pdf_files)} PDF files by document type")

        sorted_files = []
        remaining_files = pdf_files.copy()

        # Define document type patterns in order (USER REQUESTED: PDB, Vermessung, Sichtkontrolle, Bestellung, Lieferschein, Begleitpapiere)
        document_order = [
            # 1. PDB (Produktdatenblatt)
            {
                "patterns": ["pdb", "produktdatenblatt", "datasheet", "product_data"],
                "name": "PDB"
            },
            # 2. Vermessungsprotokoll (ggf. mehrere)
            {
                "patterns": ["vermessungsprotokoll", "vermessung", "messung", "protokoll", "measurement"],
                "name": "Vermessungsprotokoll"
            },
            # 3. Sichtkontrolle
            {
                "patterns": ["sichtkontrolle", "fo00141", "visuell", "visual_inspection"],
                "name": "Sichtkontrolle"
            },
            # 4. Bestellung
            {
                "patterns": ["bestellung", "order", "bestell", "po_", "bestellungsdokument"],
                "name": "Bestellung"
            },
            # 5. Lieferschein
            {
                "patterns": ["lieferschein", "ls_", "delivery_slip", "packing_slip"],
                "name": "Lieferschein"
            },
            # 6. Begleitpapiere/Zertifikate
            {
                "patterns": ["begleitpapiere", "begleitschein", "begleit", "zertifikat", "certificate", "accompany", "cert_", "wareneingang"],
                "name": "Begleitpapiere"
            }
        ]

        # Sortiere nach Dokumenttypen
        for doc_type in document_order:
            type_files = []
            for file in remaining_files[:]:  # Kopie der Liste für sicheres Iterieren
                file_name_lower = file.name.lower()
                if any(pattern in file_name_lower for pattern in doc_type["patterns"]):
                    type_files.append(file)
                    remaining_files.remove(file)

            if type_files:
                # Sortiere Dateien gleichen Typs alphabetisch
                type_files.sort(key=lambda f: f.name.lower())
                sorted_files.extend(type_files)
                logger.info(f"Added {len(type_files)} {doc_type['name']} files")

        # Füge übrige Dateien am Ende hinzu (alphabetisch sortiert)
        if remaining_files:
            remaining_files.sort(key=lambda f: f.name.lower())
            sorted_files.extend(remaining_files)
            logger.info(f"Added {len(remaining_files)} unclassified files")

        logger.info(f"Final sort order: {[f.name for f in sorted_files]}")
        return sorted_files

    except Exception as e:
        logger.error(f"Error sorting files by document type: {e}")
        # Fallback: Return original list
        return pdf_files


def get_all_merge_files_from_storage(item_data: Dict[str, Any], article_folder_path: Path) -> List[Path]:
    """
    Sammelt alle verfügbaren PDF-Dateien für den Merge aus Storage (SharePoint → Lokal).

    NEUE IMPLEMENTIERUNG: Nutzt DocumentStorageService für SharePoint-Integration
    - Primär: Lädt Dokumente von SharePoint herunter
    - Fallback: Verwendet lokale Dateien wenn SharePoint nicht verfügbar

    Args:
        item_data: Dict mit Artikel- und Lieferungsdaten
        article_folder_path: Pfad zum lokalen Artikel-Ordner (für Fallback)

    Returns:
        Liste aller verfügbaren PDF-Dateien, sortiert nach Dokumenttyp
    """
    try:
        logger.info(f"[MERGE] Collecting merge files using DocumentStorageService (SharePoint → Local)")

        # Hole DocumentStorageService
        from warehouse.application.services.service_registry import get_document_storage_service
        storage_service = get_document_storage_service()

        if not storage_service:
            logger.warning("[MERGE] DocumentStorageService not available, falling back to legacy method")
            return get_all_merge_files_legacy(item_data, article_folder_path)

        # Nutze die SharePoint-fähige Methode
        all_files = storage_service.get_documents_for_merge(
            batch_number=item_data.get("batch_number", ""),
            delivery_number=item_data.get("delivery_number", ""),
            article_number=item_data.get("article_number", ""),
            supplier_name=item_data.get("supplier_name", "")
        )

        if not all_files:
            logger.warning("[MERGE] No files from storage service, trying legacy fallback")
            return get_all_merge_files_legacy(item_data, article_folder_path)

        # Sortiere nach Dokumenttyp
        sorted_files = sort_files_by_document_type(all_files)

        logger.info(f"[MERGE] Total files collected from storage: {len(sorted_files)}")
        logger.info(f"[MERGE] Files: {[f.name for f in sorted_files]}")

        return sorted_files

    except Exception as e:
        logger.error(f"[MERGE] Error collecting merge files from storage: {e}")
        # Fallback zur alten Methode
        return get_all_merge_files_legacy(item_data, article_folder_path)


def get_all_merge_files_legacy(item_data: Dict[str, Any], article_folder_path: Path) -> List[Path]:
    """
    LEGACY: Alte Implementierung - nur lokale Ordner.
    Wird nur als Fallback verwendet wenn DocumentStorageService nicht verfügbar ist.

    Args:
        item_data: Dict mit Artikel- und Lieferungsdaten
        article_folder_path: Pfad zum Artikel-Ordner

    Returns:
        Liste aller verfügbaren PDF-Dateien, sortiert nach Dokumenttyp
    """
    try:
        logger.info(f"[MERGE LEGACY] Collecting files from local folder: {article_folder_path}")

        all_files = []

        # 1. Sammle alle PDFs aus dem Artikel-Ordner
        if article_folder_path and article_folder_path.exists():
            article_pdfs = [f for f in article_folder_path.iterdir()
                          if f.is_file() and f.suffix.lower() == ".pdf"]
            all_files.extend(article_pdfs)
            logger.info(f"[MERGE LEGACY] Found {len(article_pdfs)} PDFs in article folder")

        # 2. Prüfe ob Lieferschein bereits im Artikel-Ordner vorhanden ist
        delivery_number = item_data.get("delivery_number", "").lower()
        has_delivery_slip_in_article_folder = False

        if delivery_number:
            for file in all_files:
                file_name_lower = file.name.lower()
                if ("lieferschein" in file_name_lower and delivery_number in file_name_lower) or \
                   f"ls_{delivery_number}" in file_name_lower:
                    has_delivery_slip_in_article_folder = True
                    logger.info(f"[MERGE LEGACY] Delivery slip already in article folder: {file.name}")
                    break

        # 3. Füge Lieferschein aus Lieferanten-Ordner hinzu (falls nicht bereits vorhanden)
        if not has_delivery_slip_in_article_folder:
            delivery_slip = find_delivery_slip_in_supplier_folder(item_data)
            if delivery_slip and delivery_slip.exists():
                all_files.append(delivery_slip)
                logger.info(f"[MERGE LEGACY] Added delivery slip from supplier folder: {delivery_slip.name}")

        # 4. Sortiere alle Dateien nach Dokumenttyp
        sorted_files = sort_files_by_document_type(all_files)

        logger.info(f"[MERGE LEGACY] Total files collected: {len(sorted_files)}")
        return sorted_files

    except Exception as e:
        logger.error(f"[MERGE LEGACY] Error collecting merge files: {e}")
        # Fallback: Return only article folder PDFs
        if article_folder_path and article_folder_path.exists():
            return [f for f in article_folder_path.iterdir()
                   if f.is_file() and f.suffix.lower() == ".pdf"]
        return []
