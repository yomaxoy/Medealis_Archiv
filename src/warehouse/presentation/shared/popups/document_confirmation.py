"""
Document Confirmation Popup - Zeigt Bestätigung nach Dokumentenerstellung.

Zeigt übersichtlich welche Dokumente wo gespeichert wurden.
Verhindert Unsicherheit bei Dokumentenerstellung.

Features:
- Gruppierung nach Speicherort (Server/Lokal/SharePoint)
- Direkte Links zum Öffnen von Dateien
- Warnungen bei Fallback-Szenarien
- Fehler-Details bei Partial Success

Author: Medealis
Version: 1.0.0
"""

import streamlit as st
import logging
from pathlib import Path
from typing import Optional
import subprocess
import platform

from warehouse.application.services.document_storage.document_storage_service import (
    DocumentOperationResult,
    StorageResult,
)
from warehouse.presentation.shared.popup_styles import COMPACT_POPUP_CSS

logger = logging.getLogger(__name__)


def _auto_open_all_documents(result: DocumentOperationResult) -> None:
    """
    Öffnet alle Dokumente automatisch mit DocumentOpeningService.

    Nutzt den zentralen DocumentOpeningService für einheitliches Handling
    aller Dateitypen (DOCX, PDF, PNG, etc.).

    Args:
        result: DocumentOperationResult mit allen zu öffnenden Dokumenten
    """
    try:
        from warehouse.application.services.document_operations.document_opening_service import (
            document_opening_service,
        )

        opened_count = 0
        for doc in result.documents:
            # Nur PDFs überspringen – DOCX und PNG werden automatisch geöffnet
            if doc.document_type and "(PDF)" in doc.document_type:
                logger.debug(f"Skipping PDF auto-open: {doc.filename}")
                continue

            if doc.file_path and Path(doc.file_path).exists():
                try:
                    document_opening_service.open_document(doc.file_path)
                    opened_count += 1
                    logger.info(f"Auto-opened document: {doc.filename}")
                except Exception as e:
                    logger.warning(f"Failed to auto-open {doc.filename}: {e}")

        if opened_count > 0:
            logger.info(f"Auto-opened {opened_count} document(s)")

    except Exception as e:
        logger.error(f"Error in auto-open: {e}")
        # Non-critical - don't break the flow


def _open_file_explorer(file_path: str) -> None:
    """
    Öffnet den Datei-Explorer und markiert die Datei.

    Args:
        file_path: Absoluter Pfad zur Datei
    """
    try:
        path = Path(file_path)
        if not path.exists():
            st.warning(f"Datei nicht gefunden: {path}")
            return

        system = platform.system()
        if system == "Windows":
            subprocess.run(["explorer", "/select,", str(path)])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", "-R", str(path)])
        else:  # Linux
            subprocess.run(["xdg-open", str(path.parent)])

    except Exception as e:
        logger.error(f"Fehler beim Öffnen des Explorers: {e}")
        st.error(f"Konnte Explorer nicht öffnen: {e}")


def _render_document_card(doc: StorageResult, location_label: str) -> None:
    """
    Rendert eine einzelne Dokument-Karte.

    Args:
        doc: StorageResult mit Dokument-Informationen
        location_label: Label für den Speicherort (Server/Lokal/SharePoint)
    """
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            # Dokument-Name mit Icon
            doc_icon = "📄"
            if doc.document_type:
                if "barcode" in doc.document_type.lower():
                    doc_icon = "🏷️"
                elif "lieferschein" in doc.document_type.lower():
                    doc_icon = "📋"
                elif "prüf" in doc.document_type.lower():
                    doc_icon = "✅"

            st.markdown(f"**{doc_icon} {doc.filename or 'Unbekanntes Dokument'}**")

            # Speicherort
            storage_info = doc.storage_folder or doc.file_path or "Unbekannt"
            st.caption(f"📁 {storage_info}")

            # Dokumenttyp
            if doc.document_type:
                st.caption(f"🏷️ Typ: {doc.document_type}")

        with col2:
            # Öffnen-Button
            if doc.file_path and Path(doc.file_path).exists():
                if st.button("📂 Öffnen", key=f"open_{doc.file_path}", use_container_width=True):
                    _open_file_explorer(doc.file_path)
            elif doc.sharepoint_url:
                st.link_button("🌐 SharePoint", doc.sharepoint_url, use_container_width=True)

        # Warnungen für dieses Dokument
        if doc.warnings:
            for warning in doc.warnings:
                st.warning(f"⚠️ {warning}", icon="⚠️")

        st.markdown("---")


def _render_location_section(
    docs: list[StorageResult],
    location_name: str,
    icon: str,
    color: str
) -> None:
    """
    Rendert einen Abschnitt für einen Speicherort.

    Args:
        docs: Liste von StorageResults für diesen Speicherort
        location_name: Name des Speicherorts
        icon: Icon für den Speicherort
        color: Farbe für den Header
    """
    if not docs:
        return

    st.markdown(f"### {icon} {location_name} ({len(docs)} Dokument{'e' if len(docs) > 1 else ''})")

    for doc in docs:
        _render_document_card(doc, location_name)


@st.dialog(title="✅ Dokumente erfolgreich erstellt")
def show_document_confirmation_popup(result: DocumentOperationResult) -> None:
    """
    Zeigt Bestätigungs-Popup nach Dokumentenerstellung.

    Args:
        result: DocumentOperationResult mit allen erstellten Dokumenten

    Usage:
        result = DocumentOperationResult(operation_type="Wareneingang")
        result.add_document(storage_result1)
        result.add_document(storage_result2)

        if result.has_documents():
            show_document_confirmation_popup(result)
    """
    # Inject kompaktes CSS
    st.markdown(COMPACT_POPUP_CSS, unsafe_allow_html=True)

    # Header: Operation-Info
    if result.operation_type:
        st.info(f"**Operation:** {result.operation_type}", icon="ℹ️")

    # Status-Zusammenfassung
    total_docs = len(result.documents)

    if result.success:
        st.success(
            f"**{total_docs} Dokument{'e' if total_docs > 1 else ''} erfolgreich erstellt!**",
            icon="✅"
        )
    elif result.partial_success:
        st.warning(
            f"**{total_docs} Dokument{'e' if total_docs > 1 else ''} erstellt, aber mit Warnungen/Fehlern**",
            icon="⚠️"
        )
    else:
        st.error("**Dokumentenerstellung fehlgeschlagen!**", icon="❌")

    st.markdown("---")

    # Fehler anzeigen (falls vorhanden)
    if result.errors:
        with st.expander("❌ Fehler", expanded=True):
            for error in result.errors:
                st.error(error, icon="❌")

    # Warnungen anzeigen (falls vorhanden)
    if result.warnings:
        with st.expander("⚠️ Warnungen", expanded=False):
            for warning in result.warnings:
                st.warning(warning, icon="⚠️")

    # Dokumente nach Speicherort gruppieren
    docs_by_location = result.get_documents_by_location()

    # Server-Dokumente
    _render_location_section(
        docs_by_location['server'],
        "Server-Speicher",
        "🖥️",
        "#0066cc"
    )

    # SharePoint-Dokumente
    _render_location_section(
        docs_by_location['sharepoint'],
        "SharePoint",
        "☁️",
        "#00a4ef"
    )

    # Lokale Dokumente
    _render_location_section(
        docs_by_location['local'],
        "Lokaler Speicher",
        "💾",
        "#ff9900"
    )

    # Footer: Timestamp
    st.caption(f"🕒 Erstellt am {result.timestamp.strftime('%d.%m.%Y um %H:%M:%S')}")

    # Close Button mit Auto-Open
    if st.button("✅ Schließen", use_container_width=True, type="primary"):
        # Auto-open alle Dokumente vor dem Schließen (falls aktiviert)
        if result.auto_open and result.has_documents():
            _auto_open_all_documents(result)

        st.rerun()
