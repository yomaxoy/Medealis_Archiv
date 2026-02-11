"""
Document Merge Popup
User-facing popup for merging and managing documents.
Based on Admin merge_check_popup.py with exact same functionality.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging

from warehouse.application.services.validation_service import validation_service
from warehouse.application.services.audit_service import audit_service
from warehouse.presentation.utils.user_context import get_current_username

logger = logging.getLogger(__name__)


@st.dialog("📁 Dokumente zusammenführen", width="large")
def show_document_merge_popup(item_data: Dict[str, Any]) -> None:
    """
    Document merge popup with database integration (EXACT COPY of Admin view)

    Args:
        item_data: Dictionary mit Item-Informationen
    """
    st.write("### 📁 Dokumente prüfen & zusammenführen")
    st.write(
        f"**Artikel:** {item_data.get('article_number', 'N/A')} | **Charge:** {item_data.get('batch_number', 'N/A')}"
    )
    st.write(
        f"**Lieferung:** {item_data.get('delivery_number', 'N/A')} | **Menge:** {item_data.get('quantity', 'N/A')}"
    )

    st.write("---")

    # === ARTIKEL-ORDNER ERMITTELN ===
    folder_path = None
    try:
        from warehouse.application.services import determine_manufacturer
        from warehouse.application.services.service_registry import (
            get_document_storage_service,
        )

        # Bestimme Hersteller für Pfad
        manufacturer = determine_manufacturer(item_data.get("article_number", ""))

        # Hole Supplier-Name aus Delivery-Daten
        supplier_name = "Primec"  # Fallback
        try:
            from warehouse.application.services.service_registry import (
                get_data_integration_service,
            )

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
            all_documents = _get_all_merge_files_from_storage(item_data, folder_path)
            st.session_state[cache_key] = all_documents
    else:
        all_documents = st.session_state[cache_key]

    # === DOKUMENTE SCANNEN ===
    st.write("### 📋 Dokumente-Status")

    # PERFORMANCE: Use cached documents for status display
    scanned_docs = _create_scan_result_from_documents(all_documents, item_data)
    _show_document_status_matrix(scanned_docs, item_data)

    st.write("---")

    # === ERWEITERTE MERGE-FUNKTIONALITÄT ===
    # Use cached documents
    all_merge_files = all_documents

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
        st.info(
            f"ℹ️ {len(excluded_merge_files)} Dokument(e) automatisch ausgeschlossen: {', '.join([f.name for f in excluded_merge_files])}"
        )
        st.caption(
            "💡 Begleitschein und Wareneingang werden nicht in zusammengeführte Dokumente einbezogen"
        )

    if all_merge_files:
        st.write("### 🔗 Dokumente zusammenführen")

        # Zeige verfügbare PDF-Dateien
        st.write("**📄 Verfügbare PDF-Dateien für Merge:**")

        selected_files = []
        for pdf_file in all_merge_files:
            col_check, col_name, col_size = st.columns([1, 4, 1])

            with col_check:
                if st.checkbox(
                    "Auswählen",
                    key=f"select_{pdf_file.name}",
                    value=True,  # Auto-select all files
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
            col_merge, col_close = st.columns(2)

            with col_merge:
                if st.button(
                    "🔗 Zusammenführen",
                    key="merge_execute_btn",
                    use_container_width=True,
                    type="primary",
                ):
                    # ===== VALIDATION FIRST =====
                    validation_data = {
                        "pdb_available": bool(
                            scanned_docs["document_categories"]["pdb"]
                        ),
                        "measurement_protocol_available": bool(
                            scanned_docs["document_categories"]["vermessung"]
                        ),
                        "visual_inspection_available": bool(
                            scanned_docs["document_categories"]["sichtkontrolle"]
                        ),
                        "order_document_available": bool(
                            scanned_docs["document_categories"]["bestellung"]
                        ),
                        "delivery_slip_available": bool(
                            scanned_docs["document_categories"]["lieferschein"]
                        ),
                        "accompanying_documents_available": bool(
                            scanned_docs["document_categories"]["begleitpapiere"]
                        ),
                    }

                    validation_result = validation_service.validate_document_merge(
                        validation_data
                    )

                    if not validation_result.is_valid:
                        st.error("❌ **Validierungsfehler:**")
                        st.error(validation_result.get_formatted_errors())
                        st.warning(
                            "💡 **Hinweis:** Alle erforderlichen Dokumente müssen vorhanden sein, bevor Sie die Dokumente zusammenführen können."
                        )
                    else:
                        # Validation passed - proceed with merge
                        _execute_merge(
                            selected_files,
                            folder_path,
                            output_filename,
                            include_cover,
                            cover_title if include_cover else None,
                            item_data,
                            scanned_docs,
                        )

            with col_close:
                if st.button(
                    "❌ Schließen", key="merge_close_btn2", use_container_width=True
                ):
                    st.rerun()

        else:
            st.info("ℹ️ Wählen Sie mindestens eine PDF-Datei für den Merge aus.")

    else:
        st.warning("⚠️ Keine PDF-Dateien für Merge verfügbar.")

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


# ============================================================================
# HELPER FUNCTIONS (copied from Admin merge_check_popup.py)
# ============================================================================


def _create_scan_result_from_documents(
    documents: List[Path], item_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create scan result from already-loaded documents.

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


def _categorize_files(files: List[Path], scan_result: Dict[str, Any]) -> Dict[str, Any]:
    """Categorize files into document types based on filename patterns."""
    for file in files:
        filename_lower = file.name.lower()
        categorized = False

        # PDB
        if "pdb" in filename_lower or "produktdatenblatt" in filename_lower:
            scan_result["document_categories"]["pdb"].append(file)
            categorized = True

        # Sichtkontrolle
        if "sichtkontrolle" in filename_lower or "visual" in filename_lower:
            scan_result["document_categories"]["sichtkontrolle"].append(file)
            categorized = True

        # Vermessung/Messprotokoll
        if (
            "vermess" in filename_lower
            or "mess" in filename_lower
            or "measurement" in filename_lower
        ):
            scan_result["document_categories"]["vermessung"].append(file)
            categorized = True

        # Bestellung
        if "bestellung" in filename_lower or "order" in filename_lower:
            scan_result["document_categories"]["bestellung"].append(file)
            categorized = True

        # Lieferschein
        if "lieferschein" in filename_lower or "delivery" in filename_lower:
            # Exclude "delivery_slip" which is Begleitschein
            if "slip" not in filename_lower:
                scan_result["document_categories"]["lieferschein"].append(file)
                categorized = True

        # Begleitpapiere
        if "begleit" in filename_lower or "accompanying" in filename_lower:
            scan_result["document_categories"]["begleitpapiere"].append(file)
            categorized = True

        # Unknown
        if not categorized:
            scan_result["document_categories"]["unknown"].append(file)

    return scan_result


def _show_document_status_matrix(
    scanned_docs: Dict[str, Any], item_data: Dict[str, Any] = None
):
    """Display document status matrix with source information."""
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
            if files:
                st.success(f"✅ {category_name}")
            else:
                st.error(f"❌ {category_name}")

        with col_files:
            if files:
                st.write(", ".join([f.name for f in files]))
            else:
                st.write("Nicht gefunden")

    # Show unknown/uncategorized files
    unknown_files = scanned_docs["document_categories"]["unknown"]
    if unknown_files:
        st.write("**🤷 Nicht kategorisierte Dateien:**")
        st.write(", ".join([f.name for f in unknown_files]))


def _get_all_merge_files_from_storage(
    item_data: Dict[str, Any], article_folder_path: Path
) -> List[Path]:
    """
    Sammelt alle verfügbaren PDF-Dateien für den Merge aus Storage (SharePoint → Lokal).

    Args:
        item_data: Dict mit Artikel- und Lieferungsdaten
        article_folder_path: Pfad zum lokalen Artikel-Ordner (für Fallback)

    Returns:
        Liste aller verfügbaren PDF-Dateien, sortiert nach Dokumenttyp
    """
    try:
        logger.info(
            f"[USER MERGE] Collecting merge files using DocumentStorageService (SharePoint → Local)"
        )

        # Hole DocumentStorageService
        from warehouse.application.services.service_registry import (
            get_document_storage_service,
        )

        storage_service = get_document_storage_service()

        if not storage_service:
            logger.warning("[USER MERGE] DocumentStorageService not available")
            return []

        # Nutze die SharePoint-fähige Methode
        all_files = storage_service.get_documents_for_merge(
            batch_number=item_data.get("batch_number", ""),
            delivery_number=item_data.get("delivery_number", ""),
            article_number=item_data.get("article_number", ""),
            supplier_name=item_data.get("supplier_name", ""),
        )

        if not all_files:
            logger.warning("[USER MERGE] No files from storage service")
            return []

        # Sortiere nach Dokumenttyp
        sorted_files = _sort_files_by_document_type(all_files)

        logger.info(
            f"[USER MERGE] Total files collected from storage: {len(sorted_files)}"
        )
        logger.info(f"[USER MERGE] Files: {[f.name for f in sorted_files]}")

        return sorted_files

    except Exception as e:
        logger.error(f"[USER MERGE] Error collecting merge files from storage: {e}")
        return []


def _sort_files_by_document_type(files: List[Path]) -> List[Path]:
    """Sort files by document type priority (PDB first, then Vermessung, etc.)."""
    priority_order = {
        "pdb": 1,
        "vermess": 2,
        "sichtkontrolle": 3,
        "bestellung": 4,
        "lieferschein": 5,
        "begleit": 6,
    }

    def get_priority(file: Path) -> int:
        filename_lower = file.name.lower()
        for key, priority in priority_order.items():
            if key in filename_lower:
                return priority
        return 999  # Unknown files last

    return sorted(files, key=get_priority)


def _execute_merge(
    selected_files: List[Path],
    output_folder: Path,
    output_filename: str,
    include_cover: bool,
    cover_title: Optional[str],
    item_data: Dict[str, Any],
    scanned_docs: Dict[str, Any] = None,
):
    """Execute PDF merge operation and save to article folder."""
    try:
        from warehouse.application.services.entity_services.item_service import (
            ItemService,
        )
        from warehouse.application.services.document_operations.pdf_merge_service import (
            pdf_merge_service,
        )

        st.info(f"🔗 Führe {len(selected_files)} Dokumente zusammen...")

        # Merge PDFs
        output_path = output_folder / output_filename
        success = pdf_merge_service.merge_pdfs(
            file_paths=selected_files,
            output_path=output_path,
            include_cover=include_cover,
            cover_title=cover_title,
            article_number=item_data.get("article_number", ""),
            batch_number=item_data.get("batch_number", ""),
            delivery_number=item_data.get("delivery_number", ""),
            supplier_name=item_data.get("supplier_name", ""),
        )

        if success:
            st.success(f"✅ Dokumente erfolgreich zusammengeführt: {output_filename}")
            st.write(f"📁 Gespeichert in: {output_path}")

            # Update item notes with merge information
            try:
                item_service = ItemService()
                article_number = item_data.get("article_number")
                batch_number = item_data.get("batch_number")
                delivery_number = item_data.get("delivery_number")

                # Get current user
                current_user = get_current_username()

                # Mark workflow step as completed
                workflow_success = item_service.complete_documents_merge(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    employee=current_user,
                )

                if workflow_success:
                    st.success("✅ Workflow-Schritt abgeschlossen")
                    logger.info(f"Workflow step completed for merge: {output_filename}")

                    # ===== AUDIT LOGGING =====
                    # Build document list for notes
                    doc_list = [f.name for f in selected_files]
                    notes_text = f"Zusammengeführt: {len(selected_files)} Dokumente. Datei: {output_filename}"

                    audit_service.log_action(
                        action="DOCUMENTS_MERGED",
                        user=current_user,
                        entity_type="Item",
                        entity_id=f"{article_number}#{batch_number}#{delivery_number}",
                        data={
                            "Artikel": article_number,
                            "Charge": batch_number,
                            "Lieferung": delivery_number,
                            "Dateiname": output_filename,
                            "Anzahl Dokumente": len(selected_files),
                        },
                        notes=notes_text,
                    )

                else:
                    st.warning("⚠️ Workflow-Update fehlgeschlagen")
                    logger.warning(
                        f"Workflow update failed for merge: {output_filename}"
                    )

            except Exception as notes_error:
                logger.error(f"Error updating notes: {notes_error}")
                st.warning("⚠️ Merge erfolgreich, aber Notes-Update fehlgeschlagen")

            st.rerun()

        else:
            st.error(f"❌ Merge fehlgeschlagen")

    except Exception as e:
        logger.error(f"Error executing merge: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        st.error(f"❌ Fehler beim Zusammenführen: {e}")
