"""
Document Viewer - Browser-basierte Dokumenten-Anzeige für Multi-Client-Architektur.

Ersetzt os.startfile() / subprocess-basiertes Auto-Open mit Browser-kompatiblen
Download-Buttons und Inline-PDF-Viewern.

Funktioniert für alle Client-PCs (Browser-basiert, kein Filesystem-Zugriff nötig).
"""

import streamlit as st
import base64
import logging
from typing import Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


def show_document_with_download(
    document_data: bytes,
    filename: str,
    show_inline: bool = True,
    show_new_tab: bool = True,
    mime_type: str = "application/pdf"
) -> None:
    """
    Zeigt Dokument mit Download-Button und optionalem Inline-Viewer.

    Ersetzt Auto-Open für Browser-Client-Architektur.
    Funktioniert auf allen Client-PCs (Server + Remote-Browser-Clients).

    Args:
        document_data: Dokument als Bytes
        filename: Dateiname für Download
        show_inline: Zeigt Inline-PDF-Viewer
        show_new_tab: Zeigt "In neuem Tab öffnen" Button
        mime_type: MIME-Type des Dokuments (default: PDF)

    Example:
        # Statt: document_opening_service.open_after_generation(pdf_path)
        show_document_with_download(
            document_data=delivery.pdf_data,
            filename=f"Lieferschein_{delivery.delivery_number}.pdf",
            show_inline=True
        )
    """
    st.markdown(f"### 📄 {filename}")

    # Buttons: Download + Neuer Tab
    col1, col2 = st.columns(2)

    with col1:
        # Download-Button (Standard Streamlit)
        st.download_button(
            label="📥 Herunterladen",
            data=document_data,
            file_name=filename,
            mime=mime_type,
            type="primary",
            use_container_width=True,
            help="Dokument auf diesem PC speichern"
        )

    with col2:
        if show_new_tab:
            # "In neuem Tab öffnen" via Base64 Data-URL
            if _show_open_in_new_tab_button(document_data, filename, mime_type):
                logger.info(f"User opened document in new tab: {filename}")

    # Inline-Viewer (optional)
    if show_inline and mime_type == "application/pdf":
        with st.expander("📄 Vorschau anzeigen", expanded=False):
            _show_inline_pdf_viewer(document_data)


def show_document_download_only(
    document_data: bytes,
    filename: str,
    mime_type: str = "application/pdf",
    label: Optional[str] = None
) -> None:
    """
    Minimale Variante: Nur Download-Button (ohne Inline-Viewer).

    Args:
        document_data: Dokument als Bytes
        filename: Dateiname für Download
        mime_type: MIME-Type
        label: Optionales Label (default: "📥 {filename} herunterladen")

    Example:
        show_document_download_only(
            document_data=barcode_pdf,
            filename="Barcode_MG0001.pdf"
        )
    """
    if label is None:
        label = f"📥 {filename} herunterladen"

    st.download_button(
        label=label,
        data=document_data,
        file_name=filename,
        mime=mime_type,
        type="secondary",
        use_container_width=True
    )


def show_document_from_path(
    file_path: Union[str, Path],
    show_inline: bool = True,
    show_new_tab: bool = True
) -> None:
    """
    Lädt Dokument von Dateipfad und zeigt es an.

    Args:
        file_path: Pfad zur Datei
        show_inline: Zeigt Inline-Viewer
        show_new_tab: Zeigt "In neuem Tab öffnen" Button

    Example:
        # Für Server-PC (hat Filesystem-Zugriff)
        show_document_from_path(
            file_path="/path/to/Lieferschein_LS001.pdf",
            show_inline=True
        )
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            st.error(f"❌ Dokument nicht gefunden: {file_path.name}")
            logger.error(f"File not found: {file_path}")
            return

        # Lies Datei
        with open(file_path, 'rb') as f:
            document_data = f.read()

        # Erkenne MIME-Type
        mime_type = _get_mime_type(file_path.suffix)

        # Zeige Dokument
        show_document_with_download(
            document_data=document_data,
            filename=file_path.name,
            show_inline=show_inline,
            show_new_tab=show_new_tab,
            mime_type=mime_type
        )

    except Exception as e:
        st.error(f"❌ Fehler beim Laden des Dokuments: {e}")
        logger.error(f"Error loading document {file_path}: {e}", exc_info=True)


def show_multiple_documents(
    documents: list[dict],
    show_inline: bool = False
) -> None:
    """
    Zeigt mehrere Dokumente als Download-Liste.

    Args:
        documents: Liste von Dokumenten [{data: bytes, filename: str, mime_type: str}]
        show_inline: Zeigt Inline-Viewer für jedes Dokument

    Example:
        docs = [
            {"data": pdf1_bytes, "filename": "Barcode1.pdf", "mime_type": "application/pdf"},
            {"data": pdf2_bytes, "filename": "Barcode2.pdf", "mime_type": "application/pdf"},
        ]
        show_multiple_documents(docs, show_inline=False)
    """
    if not documents:
        st.info("📄 Keine Dokumente vorhanden")
        return

    st.markdown(f"### 📄 Dokumente ({len(documents)})")

    for idx, doc in enumerate(documents):
        with st.container():
            st.markdown(f"**{idx + 1}. {doc['filename']}**")

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="📥 Herunterladen",
                    data=doc['data'],
                    file_name=doc['filename'],
                    mime=doc.get('mime_type', 'application/pdf'),
                    key=f"download_doc_{idx}",
                    use_container_width=True
                )

            with col2:
                if _show_open_in_new_tab_button(
                    doc['data'],
                    doc['filename'],
                    doc.get('mime_type', 'application/pdf'),
                    key=f"newtab_doc_{idx}"
                ):
                    logger.info(f"User opened document {idx} in new tab: {doc['filename']}")

            if show_inline and doc.get('mime_type') == 'application/pdf':
                with st.expander(f"📄 Vorschau: {doc['filename']}", expanded=False):
                    _show_inline_pdf_viewer(doc['data'])

            st.divider()


# ============== Helper Functions ==============

def _show_inline_pdf_viewer(pdf_data: bytes, height: int = 800) -> None:
    """
    Zeigt PDF inline im Browser (Base64 iframe).

    Args:
        pdf_data: PDF als Bytes
        height: Höhe des Viewers in Pixel
    """
    try:
        # PDF zu Base64
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')

        # Embedded PDF Viewer (funktioniert in den meisten Browsern)
        pdf_display = f'''
        <iframe
            src="data:application/pdf;base64,{b64_pdf}"
            width="100%"
            height="{height}px"
            type="application/pdf"
            style="border: 1px solid #ccc; border-radius: 4px;"
        >
            <p>Ihr Browser unterstützt keine PDF-Anzeige.
               Bitte nutzen Sie den Download-Button.</p>
        </iframe>
        '''

        st.markdown(pdf_display, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Fehler beim Anzeigen der PDF-Vorschau: {e}")
        logger.error(f"PDF viewer error: {e}", exc_info=True)


def _show_open_in_new_tab_button(
    document_data: bytes,
    filename: str,
    mime_type: str,
    key: Optional[str] = None
) -> bool:
    """
    Zeigt "In neuem Tab öffnen" Button.

    Args:
        document_data: Dokument als Bytes
        filename: Dateiname
        mime_type: MIME-Type
        key: Optional key für Button

    Returns:
        True wenn Button geklickt wurde
    """
    try:
        # Dokument zu Base64
        b64_doc = base64.b64encode(document_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{b64_doc}"

        # HTML Link mit target="_blank"
        # HINWEIS: st.markdown mit Link funktioniert, aber Button schöner
        # Workaround: Nutze HTML-Button mit JavaScript

        html_button = f'''
        <a href="{data_url}" target="_blank" style="text-decoration: none;">
            <button style="
                background-color: #262730;
                color: white;
                border: 1px solid #4CAF50;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                cursor: pointer;
                width: 100%;
                font-size: 1rem;
            ">
                🌐 In neuem Tab öffnen
            </button>
        </a>
        '''

        st.markdown(html_button, unsafe_allow_html=True)

        return False  # Können Klick nicht tracken (HTML-Button)

    except Exception as e:
        logger.error(f"Error creating new tab button: {e}", exc_info=True)
        return False


def _get_mime_type(file_extension: str) -> str:
    """
    Ermittelt MIME-Type anhand Dateiendung.

    Args:
        file_extension: Dateiendung (z.B. '.pdf', '.docx')

    Returns:
        MIME-Type
    """
    mime_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.txt': 'text/plain',
    }

    return mime_types.get(file_extension.lower(), 'application/octet-stream')


def show_auto_open_disabled_info() -> None:
    """
    Zeigt Info-Box dass Auto-Open deaktiviert ist (Browser-Client-Architektur).

    Für Migration von bestehendem Code der Auto-Open nutzte.
    """
    st.info(
        "ℹ️ **Dokument bereitgestellt!** "
        "Nutzen Sie den Download-Button oder 'In neuem Tab öffnen' um das Dokument anzuzeigen. "
        "(Auto-Open ist für Browser-Clients deaktiviert)"
    )
