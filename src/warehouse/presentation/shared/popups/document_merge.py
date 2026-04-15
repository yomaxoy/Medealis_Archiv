"""
Document Merge Popup (Shared)
Unified implementation for User and Admin apps.

Args:
    item_data: Dict mit Item-Informationen
    audit: True = mit Validation + AuditService-Logging + Workflow-Schritt (User-Modus)
           False = ohne Validation/Audit, nur Notes-Update (Admin-Modus)
"""

import streamlit as st
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


@st.dialog("📁 Dokumente zusammenführen", width="large")
def show_document_merge_popup(item_data: Dict[str, Any], audit: bool = True) -> None:
    """
    Unified document merge popup for User and Admin apps.

    Args:
        item_data: Dictionary mit Item-Informationen
        audit: True  → mit Dokumenten-Validierung, Workflow-Schritt und Audit-Logging (User)
               False → ohne Validierung/Audit, nur Notes-Update (Admin)
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

        item_data["supplier_name"] = supplier_name

        storage_service = get_document_storage_service()
        folder_path, path_warnings = storage_service.get_document_path(
            batch_number=item_data.get("batch_number", ""),
            delivery_number=item_data.get("delivery_number", ""),
            article_number=item_data.get("article_number", ""),
            supplier_name=supplier_name,
            create_folders=False,
        )

        if path_warnings:
            for warning in path_warnings:
                st.warning(f"⚠️ {warning}")

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

    # === DOKUMENTE LADEN (gecacht) ===
    cache_key = f"merge_docs_{item_data.get('batch_number', '')}_{item_data.get('delivery_number', '')}"

    if cache_key not in st.session_state:
        with st.spinner("📥 Lade Dokumente von SharePoint..."):
            all_documents = get_all_merge_files_from_storage(item_data, folder_path)
            st.session_state[cache_key] = all_documents
    else:
        all_documents = st.session_state[cache_key]

    # === DOKUMENTE SCANNEN & STATUS ANZEIGEN ===
    st.write("### 📋 Dokumente-Status")
    scanned_docs = create_scan_result_from_documents(all_documents, item_data)
    show_document_status_matrix(scanned_docs, item_data)

    st.write("---")

    # === MERGE-DATEIEN ZUSAMMENSTELLEN ===
    all_merge_files = list(all_documents)

    # Lieferschein aus Lieferanten-Ordner automatisch hinzufügen
    delivery_slip_from_supplier = find_delivery_slip_in_supplier_folder(item_data)
    delivery_slip_added = False
    if delivery_slip_from_supplier:
        already_included = any(f.name == delivery_slip_from_supplier.name for f in all_merge_files)
        if not already_included:
            all_merge_files.append(delivery_slip_from_supplier)
            delivery_slip_added = True
            st.info(f"📄 **Lieferschein automatisch hinzugefügt:** {delivery_slip_from_supplier.name}")
            st.caption(f"📁 Aus: {delivery_slip_from_supplier.parent}")
            all_merge_files = sort_files_by_document_type(all_merge_files)

    # Begleitschein und Wareneingang aus Merge ausschließen
    excluded_merge_files = []
    filtered_merge_files = []
    for file in all_merge_files:
        file_name_lower = file.name.lower()
        if "begleitschein" in file_name_lower or "wareneingang" in file_name_lower:
            excluded_merge_files.append(file)
        else:
            filtered_merge_files.append(file)

    all_merge_files = filtered_merge_files

    if excluded_merge_files:
        st.info(f"ℹ️ {len(excluded_merge_files)} Dokument(e) automatisch ausgeschlossen: {', '.join([f.name for f in excluded_merge_files])}")
        st.caption("💡 Begleitschein und Wareneingang werden nicht in zusammengeführte Dokumente einbezogen")

    if all_merge_files:
        st.write("### 🔗 Dokumente zusammenführen")

        st.write("**📄 Verfügbare PDF-Dateien für Merge:**")
        if delivery_slip_added:
            st.caption("💡 Dateien sind automatisch in der optimalen Reihenfolge sortiert (PDB → Messprotokoll → Sichtkontrolle → Bestellung → Lieferschein → Begleitpapiere)")

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
                    file_size = pdf_file.stat().st_size / 1024
                    st.write(f"{file_size:.1f} KB")
                except Exception:
                    st.write("?")

        if selected_files:
            st.write("---")

            col_name_input, col_cover = st.columns(2)

            with col_name_input:
                output_filename = st.text_input(
                    "📄 Dateiname für zusammengeführtes Dokument:",
                    value=f"nicht_{item_data.get('batch_number', 'CHARGE')}_{item_data.get('article_number', 'ARTIKEL')}_{item_data.get('delivery_number', 'LIEFERUNG')}.pdf",
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
                else:
                    cover_title = None

            col_merge, col_preview = st.columns(2)

            with col_preview:
                if st.button("👁️ Vorschau", key="merge_preview_btn", use_container_width=True):
                    show_merge_preview(selected_files)

            with col_merge:
                if st.button(
                    "🔗 Zusammenführen",
                    key="merge_execute_btn",
                    use_container_width=True,
                    type="primary",
                ):
                    if audit:
                        # User-Modus: Validierung vor dem Merge
                        from warehouse.application.services.validation_service import validation_service
                        validation_data = {
                            "pdb_available": bool(scanned_docs["document_categories"]["pdb"]),
                            "measurement_protocol_available": bool(scanned_docs["document_categories"]["vermessung"]),
                            "visual_inspection_available": bool(scanned_docs["document_categories"]["sichtkontrolle"]),
                            "order_document_available": bool(scanned_docs["document_categories"]["bestellung"]),
                            "delivery_slip_available": bool(scanned_docs["document_categories"]["lieferschein"]),
                            "accompanying_documents_available": bool(scanned_docs["document_categories"]["begleitpapiere"]),
                        }
                        validation_result = validation_service.validate_document_merge(validation_data)

                        if not validation_result.is_valid:
                            st.error("❌ **Validierungsfehler:**")
                            st.error(validation_result.get_formatted_errors())
                            st.warning(
                                "💡 **Hinweis:** Alle erforderlichen Dokumente müssen vorhanden sein, bevor Sie die Dokumente zusammenführen können."
                            )
                        else:
                            execute_merge(
                                selected_files, folder_path, output_filename,
                                include_cover, cover_title, item_data, audit=True,
                            )
                    else:
                        execute_merge(
                            selected_files, folder_path, output_filename,
                            include_cover, cover_title, item_data, audit=False,
                        )

        else:
            st.info("ℹ️ Wählen Sie mindestens eine PDF-Datei für den Merge aus.")

    else:
        if delivery_slip_from_supplier:
            st.info("📄 Nur Lieferschein aus Lieferanten-Ordner gefunden - weitere PDFs im Artikel-Ordner hinzufügen für Merge.")
        else:
            st.warning("⚠️ Keine PDF-Dateien für Merge verfügbar.")

    # === KI-ANALYSE (Platzhalter) ===
    merged_file = check_for_merged_file(folder_path, item_data)
    if merged_file:
        st.write("---")
        st.write("### 🤖 KI-Analyse (kommt im nächsten Schritt)")
        st.info("📊 Zusammengeführte Datei gefunden - KI-Analyse wird in der nächsten Phase implementiert")

        col_ai_btn, col_info = st.columns(2)
        with col_ai_btn:
            if st.button("🤖 KI-Analyse starten", key="ai_analysis_btn", disabled=True):
                st.info("🚧 Wird im nächsten Implementierungsschritt verfügbar")
        with col_info:
            st.write(f"📄 **Datei:** {merged_file.name}")
            try:
                file_size = merged_file.stat().st_size / (1024 * 1024)
                st.write(f"📊 **Größe:** {file_size:.1f} MB")
            except Exception:
                pass

    # === BUTTONS ===
    st.write("---")
    col_close, col_refresh, col_clear_cache = st.columns(3)

    with col_clear_cache:
        if st.button("🗑️ Cache leeren", key="merge_clear_cache_btn", use_container_width=True):
            if cache_key in st.session_state:
                del st.session_state[cache_key]
                st.success("✅ Cache geleert - Dokumente werden neu geladen")
            st.rerun()

    with col_refresh:
        if st.button("🔄 Aktualisieren", key="merge_refresh_btn", use_container_width=True):
            st.rerun()

    with col_close:
        if st.button("❌ Schließen", key="merge_close_btn", use_container_width=True):
            st.rerun()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_scan_result_from_documents(documents: List[Path], item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create scan result dict from already-loaded document paths."""
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
        "source": "sharepoint",
    }

    if documents:
        scan_result = _categorize_files(documents, scan_result)

    return scan_result


def _categorize_files(all_files: List[Path], scan_result: Dict[str, Any]) -> Dict[str, Any]:
    """Categorize files by document type based on filename patterns."""
    for file in all_files:
        file_name_lower = file.name.lower()

        # Reihenfolge wichtig: spezifischere Patterns zuerst
        if any(pattern in file_name_lower for pattern in ["pdb", "produktdatenblatt"]):
            scan_result["document_categories"]["pdb"].append(file)
        elif any(pattern in file_name_lower for pattern in ["sichtkontrolle", "fo00141", "visuell"]):
            scan_result["document_categories"]["sichtkontrolle"].append(file)
        elif any(pattern in file_name_lower for pattern in ["messprotokoll-", "vermessungsprotokoll_", "vermessung", "messung", "protokoll"]):
            scan_result["document_categories"]["vermessung"].append(file)
        elif any(pattern in file_name_lower for pattern in ["bestellung", "order", "bestell"]):
            scan_result["document_categories"]["bestellung"].append(file)
        # Begleitschein/-papiere VOR Lieferschein prüfen
        elif any(pattern in file_name_lower for pattern in ["begleitschein", "begleitpapiere_", "begleit", "zertifikat", "certificate", "accompany"]):
            scan_result["document_categories"]["begleitpapiere"].append(file)
        elif any(pattern in file_name_lower for pattern in ["lieferschein", "delivery"]):
            scan_result["document_categories"]["lieferschein"].append(file)
        else:
            scan_result["document_categories"]["unknown"].append(file)

    return scan_result


def show_document_status_matrix(scanned_docs: Dict[str, Any], item_data: Dict[str, Any] = None):
    """Display document status matrix with source information."""
    if not scanned_docs["folder_exists"]:
        st.error("❌ Keine Dokumente gefunden (weder SharePoint noch lokal)")
        return

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

    # Lieferschein aus Lieferanten-Ordner prüfen falls nicht im Artikel-Ordner
    delivery_slip_in_supplier = None
    if item_data and not scanned_docs["document_categories"]["lieferschein"]:
        delivery_slip_in_supplier = find_delivery_slip_in_supplier_folder(item_data)

    categories = {
        "📋 PDB": scanned_docs["document_categories"]["pdb"],
        "👁️ Sichtkontrolle": scanned_docs["document_categories"]["sichtkontrolle"],
        "📏 Messprotokoll": scanned_docs["document_categories"]["vermessung"],
        "📋 Bestellung": scanned_docs["document_categories"]["bestellung"],
        "📄 Lieferschein": scanned_docs["document_categories"]["lieferschein"],
        "📦 Begleitpapiere": scanned_docs["document_categories"]["begleitpapiere"],
    }

    for category_name, files in categories.items():
        col_status, col_files = st.columns([1, 3])

        with col_status:
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
                    st.write(", ".join(f.name for f in files))
                elif delivery_slip_in_supplier:
                    st.write(f"📁 {delivery_slip_in_supplier.name} (aus Lieferanten-Ordner)")
                else:
                    st.write("Nicht gefunden")
            else:
                if files:
                    st.write(", ".join(f.name for f in files))
                else:
                    st.write("Nicht gefunden")

    if scanned_docs["document_categories"]["unknown"]:
        st.write("**🤷 Nicht kategorisierte Dateien:**")
        st.write(", ".join(f.name for f in scanned_docs["document_categories"]["unknown"]))


def show_merge_preview(selected_files: List[Path]):
    """Show merge preview (size, warnings, mergeability)."""
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
    cover_title: Optional[str],
    item_data: Dict[str, Any],
    audit: bool = True,
):
    """
    Execute the PDF merge operation.

    Args:
        audit: True  → Workflow-Schritt + Audit-Logging (User)
               False → nur Notes-Update (Admin)
    """
    try:
        from warehouse.application.services.service_registry import get_pdf_merge_service
        pdf_merge_service = get_pdf_merge_service()

        validation = pdf_merge_service.validate_merge_input(
            selected_files, folder_path / output_filename
        )

        if not validation["valid"]:
            st.error("❌ Merge nicht möglich:")
            for error in validation["errors"]:
                st.error(f"  • {error}")
            return

        if validation["warnings"]:
            for warning in validation["warnings"]:
                st.warning(f"⚠️ {warning}")

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
                supplier_name=item_data.get("supplier_name", ""),
            )

        if success:
            st.success("✅ PDFs erfolgreich zusammengeführt!")
            st.info(f"📄 **Datei erstellt:** {output_filename}")
            st.info(f"📁 **Speicherort:** {folder_path}")

            # Datenbank-Update
            article_number = item_data.get("article_number")
            batch_number = item_data.get("batch_number")
            delivery_number = item_data.get("delivery_number")

            if audit:
                # User-Modus: Workflow-Schritt + Audit-Logging
                try:
                    from warehouse.application.services.entity_services.item_service import ItemService
                    from warehouse.application.services.audit_service import audit_service
                    from warehouse.presentation.utils.user_context import get_current_username

                    item_service = ItemService()
                    current_user = get_current_username()

                    workflow_success = item_service.complete_documents_merge(
                        article_number=article_number,
                        batch_number=batch_number,
                        delivery_number=delivery_number,
                        employee=current_user,
                    )

                    if workflow_success:
                        st.success("✅ Workflow-Schritt abgeschlossen")
                        logger.info(f"Workflow step completed for merge: {output_filename}")

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
                            notes=f"Zusammengeführt: {len(selected_files)} Dokumente. Datei: {output_filename}",
                        )
                    else:
                        st.warning("⚠️ Workflow-Update fehlgeschlagen")
                        logger.warning(f"Workflow update failed for merge: {output_filename}")

                except Exception as e:
                    logger.error(f"Error in audit/workflow update: {e}")
                    st.warning("⚠️ Merge erfolgreich, aber Workflow-Update fehlgeschlagen")

            else:
                # Admin-Modus: nur Notes-Update
                try:
                    from warehouse.application.services.service_registry import get_item_service
                    import datetime

                    item_service = get_item_service()
                    merge_note = (
                        f"PDF-Merge: {output_filename} "
                        f"({', '.join(f.name for f in selected_files)}) - "
                        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )

                    item = item_service.get_item(article_number, batch_number, delivery_number)
                    if item:
                        current_notes = item.get("notes", "")
                        updated_notes = f"{current_notes}\n{merge_note}" if current_notes else merge_note

                        update_success = item_service.update_item_notes(
                            article_number=article_number,
                            batch_number=batch_number,
                            delivery_number=delivery_number,
                            notes=updated_notes,
                        )
                        if update_success:
                            st.success("✅ Merge-Information in der Datenbank gespeichert")
                        else:
                            st.warning("⚠️ Datenbankupdate für Merge-Information fehlgeschlagen")
                    else:
                        st.warning("⚠️ Item nicht in der Datenbank gefunden für Merge-Dokumentation")

                except Exception as e:
                    logger.error(f"Error storing merge info in database: {e}")
                    st.warning(f"⚠️ Fehler beim Speichern der Merge-Information: {str(e)}")

            st.rerun()

        else:
            st.error("❌ Fehler beim Zusammenführen der PDFs")

    except Exception as e:
        logger.error(f"Merge execution error: {e}")
        st.error(f"❌ Fehler beim Merge: {e}")


def check_for_merged_file(folder_path: Path, item_data: Dict[str, Any]) -> Optional[Path]:
    """Check if a merged file already exists in the folder."""
    if not folder_path or not folder_path.exists():
        return None

    try:
        potential_merged_files = [
            file for file in folder_path.glob("*.pdf")
            if any(
                keyword in file.name.lower()
                for keyword in ["komplett", "merged", "dokumentation", "combined"]
            )
        ]
        if potential_merged_files:
            return max(potential_merged_files, key=lambda f: f.stat().st_mtime)
    except Exception as e:
        logger.error(f"Error checking for merged file: {e}")

    return None


def find_delivery_slip_in_supplier_folder(item_data: Dict[str, Any]) -> Optional[Path]:
    """Sucht Lieferschein im Lieferanten/Lieferscheine Ordner."""
    try:
        logger.info(f"Searching for delivery slip for delivery: {item_data.get('delivery_number', 'N/A')}")

        supplier_name = "Primec"
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

        from warehouse.application.services.document_storage.storage_context import storage_context
        from warehouse.application.services.service_registry import get_document_storage_service

        normalized_supplier = storage_context._basic_supplier_normalization(supplier_name)
        normalized_supplier = normalized_supplier.replace(" ", "_")

        storage_service = get_document_storage_service()
        base_path = storage_service.path_resolver.base_storage_path
        delivery_slip_folder = base_path / normalized_supplier / "Lieferscheine"

        logger.info(f"Looking for delivery slips in: {delivery_slip_folder}")

        if not delivery_slip_folder.exists():
            logger.warning(f"Delivery slip folder does not exist: {delivery_slip_folder}")
            return None

        delivery_number = item_data.get("delivery_number", "").strip()
        if not delivery_number:
            return None

        for pdf_file in delivery_slip_folder.glob("*.pdf"):
            file_name_lower = pdf_file.name.lower()
            delivery_number_lower = delivery_number.lower()

            if (
                delivery_number_lower in file_name_lower
                or f"ls_{delivery_number_lower}" in file_name_lower
                or f"lieferschein_{delivery_number_lower}" in file_name_lower
                or f"{delivery_number_lower}_" in file_name_lower
            ):
                logger.info(f"Found delivery slip: {pdf_file}")
                return pdf_file

        logger.warning(f"No delivery slip found for delivery number: {delivery_number}")
        return None

    except Exception as e:
        logger.error(f"Error searching for delivery slip: {e}")
        return None


def sort_files_by_document_type(pdf_files: List[Path]) -> List[Path]:
    """
    Sortiert PDF-Dateien nach Dokumenttyp.
    Reihenfolge: PDB → Vermessungsprotokoll → Sichtkontrolle → Bestellung → Lieferschein → Begleitpapiere → Sonstige
    """
    try:
        document_order = [
            {"patterns": ["pdb", "produktdatenblatt", "datasheet", "product_data"], "name": "PDB"},
            {"patterns": ["messprotokoll", "vermessungsprotokoll", "vermessung", "messung", "protokoll", "measurement"], "name": "Messprotokoll"},
            {"patterns": ["sichtkontrolle", "fo00141", "visuell", "visual_inspection"], "name": "Sichtkontrolle"},
            {"patterns": ["bestellung", "order", "bestell", "po_", "bestellungsdokument"], "name": "Bestellung"},
            {"patterns": ["lieferschein", "ls_", "delivery_slip", "packing_slip"], "name": "Lieferschein"},
            {"patterns": ["begleitpapiere", "begleitschein", "begleit", "zertifikat", "certificate", "accompany", "cert_", "wareneingang"], "name": "Begleitpapiere"},
        ]

        sorted_files = []
        remaining_files = pdf_files.copy()

        for doc_type in document_order:
            type_files = []
            for file in remaining_files[:]:
                if any(pattern in file.name.lower() for pattern in doc_type["patterns"]):
                    type_files.append(file)
                    remaining_files.remove(file)

            if type_files:
                type_files.sort(key=lambda f: f.name.lower())
                sorted_files.extend(type_files)

        if remaining_files:
            remaining_files.sort(key=lambda f: f.name.lower())
            sorted_files.extend(remaining_files)

        return sorted_files

    except Exception as e:
        logger.error(f"Error sorting files by document type: {e}")
        return pdf_files


def get_all_merge_files_from_storage(item_data: Dict[str, Any], article_folder_path: Path) -> List[Path]:
    """
    Sammelt alle verfügbaren PDF-Dateien für den Merge aus Storage (SharePoint → Lokal).
    """
    try:
        from warehouse.application.services.service_registry import get_document_storage_service
        storage_service = get_document_storage_service()

        if not storage_service:
            logger.warning("[MERGE] DocumentStorageService not available, falling back to legacy method")
            return _get_all_merge_files_legacy(item_data, article_folder_path)

        all_files = storage_service.get_documents_for_merge(
            batch_number=item_data.get("batch_number", ""),
            delivery_number=item_data.get("delivery_number", ""),
            article_number=item_data.get("article_number", ""),
            supplier_name=item_data.get("supplier_name", ""),
        )

        if not all_files:
            logger.warning("[MERGE] No files from storage service, trying legacy fallback")
            return _get_all_merge_files_legacy(item_data, article_folder_path)

        return sort_files_by_document_type(all_files)

    except Exception as e:
        logger.error(f"[MERGE] Error collecting merge files from storage: {e}")
        return _get_all_merge_files_legacy(item_data, article_folder_path)


def _get_all_merge_files_legacy(item_data: Dict[str, Any], article_folder_path: Path) -> List[Path]:
    """Fallback: Nur lokale Ordner wenn DocumentStorageService nicht verfügbar ist."""
    try:
        all_files = []

        if article_folder_path and article_folder_path.exists():
            all_files.extend(
                f for f in article_folder_path.iterdir()
                if f.is_file() and f.suffix.lower() == ".pdf"
            )

        delivery_number = item_data.get("delivery_number", "").lower()
        has_delivery_slip = delivery_number and any(
            ("lieferschein" in f.name.lower() and delivery_number in f.name.lower())
            or f"ls_{delivery_number}" in f.name.lower()
            for f in all_files
        )

        if not has_delivery_slip:
            delivery_slip = find_delivery_slip_in_supplier_folder(item_data)
            if delivery_slip and delivery_slip.exists():
                all_files.append(delivery_slip)

        return sort_files_by_document_type(all_files)

    except Exception as e:
        logger.error(f"[MERGE LEGACY] Error collecting merge files: {e}")
        if article_folder_path and article_folder_path.exists():
            return [f for f in article_folder_path.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
        return []
