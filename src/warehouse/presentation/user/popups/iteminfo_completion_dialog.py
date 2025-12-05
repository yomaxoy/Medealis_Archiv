"""
ItemInfo Completion Dialog

Ermöglicht die Vervollständigung von ItemInfo-Einträgen nach dem Lieferschein-Scan,
wenn Artikel noch nicht im System vorhanden sind.

Integriert:
- Vollständige ItemInfo-Felder (Designation, Manufacturer, Drawing, Storage Location, etc.)
- QR-Code Upload (Binary Storage in PostgreSQL)
- Multi-Artikel Workflow (Tabs oder Dropdown)
- Artikel-Skip/Delete Funktion
"""

import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)


@st.dialog("⚠️ Artikel-Informationen vervollständigen", width="large")
def show_iteminfo_completion_dialog(
    missing_articles: List[Dict[str, Any]], supplier_name: str = None
) -> bool:
    """
    Zeigt Dialog zur Vervollständigung fehlender ItemInfo-Einträge.

    Args:
        missing_articles: Liste von Artikeln ohne ItemInfo [{article_number, description, ...}, ...]
        supplier_name: Lieferantenname vom Lieferschein (wird als Hersteller vorausgefüllt)

    Returns:
        bool: True wenn alle ItemInfos vervollständigt/übersprungen wurden, False wenn noch in Bearbeitung
    """

    st.info(
        f"📋 **{len(missing_articles)} Artikel** sind noch nicht im System vorhanden. "
        "Bitte vervollständigen Sie die Artikeldaten oder überspringen Sie Artikel, "
        "die nicht ins System übernommen werden sollen."
    )

    # Session State initialisieren
    if "iteminfo_form_data" not in st.session_state:
        st.session_state.iteminfo_form_data = {}

    if "articles_to_skip" not in st.session_state:
        st.session_state.articles_to_skip = set()

    if "qr_uploads" not in st.session_state:
        st.session_state.qr_uploads = {}

    if "qr_filenames" not in st.session_state:
        st.session_state.qr_filenames = {}

    if "current_article_index" not in st.session_state:
        st.session_state.current_article_index = 0

    # Filtere übersprungene Artikel
    active_articles = [
        art
        for art in missing_articles
        if art["article_number"] not in st.session_state.articles_to_skip
    ]

    if not active_articles:
        st.success("✅ Alle Artikel wurden bearbeitet oder übersprungen.")
        if st.button("✅ Fortfahren", type="primary", use_container_width=True):
            return True
        return False

    # Stelle sicher, dass current_article_index gültig ist
    if st.session_state.current_article_index >= len(active_articles):
        st.session_state.current_article_index = 0

    # Artikel-Auswahl (Dropdown für große Listen, Tabs für kleine)
    if len(active_articles) <= 3:
        # Tabs für bis zu 3 Artikel
        tabs = st.tabs([f"Artikel {art['article_number']}" for art in active_articles])

        for idx, article in enumerate(active_articles):
            with tabs[idx]:
                _render_article_form(article, idx, supplier_name, active_articles)
    else:
        # Dropdown für viele Artikel - verwende current_article_index für Auto-Navigation
        article_options = [
            f"{art['article_number']} - {art.get('description', 'Keine Bezeichnung')}"
            for art in active_articles
        ]

        # Zeige aktuellen Artikel basierend auf current_article_index
        selected_index = st.selectbox(
            "Artikel auswählen",
            options=range(len(article_options)),
            format_func=lambda i: article_options[i],
            index=st.session_state.current_article_index,
            help="Wählen Sie den Artikel aus, den Sie bearbeiten möchten",
            key="article_selector",
        )

        # Update current_article_index wenn manuell geändert
        st.session_state.current_article_index = selected_index

        selected_article = active_articles[selected_index]

        _render_article_form(
            selected_article, selected_index, supplier_name, active_articles
        )

    # Fortschritt
    completed_count = len(st.session_state.iteminfo_form_data)
    skipped_count = len(st.session_state.articles_to_skip)
    total_count = len(missing_articles)

    st.progress(
        (completed_count + skipped_count) / total_count,
        text=f"📊 Fortschritt: {completed_count} ausgefüllt, {skipped_count} übersprungen, "
        f"{total_count - completed_count - skipped_count} verbleibend",
    )

    # Buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("❌ Abbrechen", use_container_width=True):
            # Reset Session State
            st.session_state.show_iteminfo_dialog = False
            st.session_state.iteminfo_form_data = {}
            st.session_state.articles_to_skip = set()
            st.session_state.qr_uploads = {}
            st.session_state.qr_filenames = {}
            st.rerun()

    with col2:
        all_complete = (completed_count + skipped_count) == total_count
        if st.button(
            "✅ Alle ItemInfos speichern und fortfahren",
            type="primary",
            disabled=not all_complete,
            use_container_width=True,
        ):
            if _save_all_iteminfos():
                # ItemInfos erfolgreich gespeichert
                st.session_state.iteminfo_completed = True
                st.session_state.show_iteminfo_dialog = False
                st.session_state.show_extraction_popup = (
                    True  # NEU: Öffne Extraktions-Popup
                )

                # Cleanup: Reset current_article_index für nächsten Durchlauf
                st.session_state.current_article_index = 0

                st.rerun()
            else:
                st.error("❌ Fehler beim Speichern. Bitte versuchen Sie es erneut.")
                return False

    return False


def _render_article_form(
    article: Dict[str, Any],
    form_index: int,
    supplier_name: str = None,
    active_articles: List[Dict[str, Any]] = None,
):
    """
    Rendert Formular für einen einzelnen Artikel.

    Args:
        article: Artikel-Daten {article_number, description, ...}
        form_index: Index für eindeutige Keys
        supplier_name: Lieferantenname vom Lieferschein (wird als Hersteller vorausgefüllt)
        active_articles: Liste aller aktiven Artikel (für Auto-Navigation zum nächsten)
    """
    article_number = article["article_number"]

    st.markdown(f"#### Artikelnummer: `{article_number}`")

    # Prüfe ob Daten bereits vorhanden
    if article_number in st.session_state.iteminfo_form_data:
        st.info("✅ Artikel-Informationen bereits ausgefüllt")
        if st.button(f"🔄 Erneut bearbeiten", key=f"edit_{form_index}"):
            del st.session_state.iteminfo_form_data[article_number]
            st.rerun()
        return

    # 2-Spalten Layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 📋 Stammdaten")

        # Bezeichnung aus description vorausgefüllt (vom Lieferschein)
        designation = st.text_input(
            "Bezeichnung",
            value=article.get("description", ""),
            key=f"designation_{form_index}",
            help="Artikelbezeichnung (automatisch aus Lieferschein übernommen)",
        )

        # Hersteller aus supplier_name vorausgefüllt (vom Lieferschein)
        # Mehrere Hersteller können kommagetrennt eingegeben werden
        manufacturer = st.text_input(
            "Hersteller",
            value=supplier_name or article.get("manufacturer", ""),
            key=f"manufacturer_{form_index}",
            help="Hersteller (automatisch aus Lieferschein übernommen). Mehrere Hersteller kommagetrennt möglich: z.B. 'Primec, Dentsply, Straumann'",
        )

        drawing_reference = st.text_input(
            "Zeichnungsreferenz",
            value=article.get("drawing_reference", ""),
            key=f"drawing_{form_index}",
            help="Zeichnungsnummer (optional)",
        )

    with col2:
        st.markdown("##### 📦 Lager & Details")

        storage_location = st.text_input(
            "Lagerort",
            value=article.get("storage_location", ""),
            key=f"storage_{form_index}",
            help="Lagernummer/Position (optional)",
        )

        description = st.text_area(
            "Zusätzliche Beschreibung",
            value=article.get("notes", ""),
            key=f"description_{form_index}",
            height=150,
            help="Zusätzliche Beschreibung oder Notizen (optional)",
        )

    # QR-Code Upload Sektion
    st.markdown("##### 📸 QR-Code hochladen")

    qr_file = st.file_uploader(
        "QR-Code Bild",
        type=["png", "jpg", "jpeg"],
        key=f"qr_upload_{form_index}",
        help="Optional: QR-Code Bild für Artikelrückverfolgung (max 5MB)",
    )

    if qr_file:
        # Validierung
        file_size_mb = len(qr_file.getvalue()) / (1024 * 1024)

        if file_size_mb > 5:
            st.error(f"❌ Datei zu groß: {file_size_mb:.2f} MB (max 5 MB)")
        else:
            # Preview
            try:
                image = Image.open(qr_file)
                st.image(image, caption=qr_file.name, width=200)
                st.success(
                    f"✅ QR-Code hochgeladen: {qr_file.name} ({file_size_mb:.2f} MB)"
                )

                # Speichere in Session State
                qr_file.seek(0)  # Reset file pointer
                st.session_state.qr_uploads[article_number] = qr_file.read()
                st.session_state.qr_filenames[article_number] = qr_file.name

            except Exception as e:
                st.error(f"❌ Fehler beim Laden des Bildes: {str(e)}")

    # Aktions-Buttons
    st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button(
            f"⏭️ Artikel überspringen",
            key=f"skip_{form_index}",
            use_container_width=True,
        ):
            st.session_state.articles_to_skip.add(article_number)
            # Entferne QR-Upload falls vorhanden
            st.session_state.qr_uploads.pop(article_number, None)
            st.session_state.qr_filenames.pop(article_number, None)
            st.rerun()

    with col_btn2:
        if st.button(
            f"💾 Artikel speichern",
            key=f"save_{form_index}",
            type="primary",
            use_container_width=True,
        ):
            # Validierung - Bezeichnung ist nicht mehr Pflicht (wird automatisch aus Lieferschein übernommen)
            # Fallback auf Artikelnummer falls leer
            final_designation = (
                designation.strip()
                if designation and designation.strip()
                else f"Artikel {article_number}"
            )

            # Speichere Formulardaten
            st.session_state.iteminfo_form_data[article_number] = {
                "article_number": article_number,
                "designation": final_designation,
                "manufacturer": manufacturer.strip() if manufacturer else None,
                "drawing_reference": drawing_reference.strip()
                if drawing_reference
                else None,
                "storage_location": storage_location.strip()
                if storage_location
                else None,
                "description": description.strip() if description else None,
                "has_qr": article_number in st.session_state.qr_uploads,
            }

            # NEU: Automatisch zum nächsten Artikel springen (nur bei Dropdown-Navigation)
            if active_articles and len(active_articles) > 3:
                # Finde nächsten unbearbeiteten Artikel
                next_index = form_index + 1
                while next_index < len(active_articles):
                    next_article = active_articles[next_index]
                    if (
                        next_article["article_number"]
                        not in st.session_state.iteminfo_form_data
                        and next_article["article_number"]
                        not in st.session_state.articles_to_skip
                    ):
                        # Nächster unbearbeiteter Artikel gefunden
                        st.session_state.current_article_index = next_index
                        break
                    next_index += 1

            st.success(f"✅ Artikel {article_number} gespeichert!")
            st.rerun()


def _save_all_iteminfos() -> bool:
    """
    Speichert alle vervollständigten ItemInfos in die Datenbank.

    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        from warehouse.infrastructure.database.repositories.item_info_repository import (
            item_info_repository,
        )

        saved_count = 0

        for article_number, form_data in st.session_state.iteminfo_form_data.items():
            # QR-Code Daten hinzufügen falls vorhanden
            qr_image = st.session_state.qr_uploads.get(article_number)
            qr_filename = st.session_state.qr_filenames.get(article_number)

            iteminfo_data = {
                "article_number": form_data["article_number"],
                "designation": form_data["designation"],
                "manufacturer": form_data.get("manufacturer"),
                "drawing_reference": form_data.get("drawing_reference"),
                "storage_location": form_data.get("storage_location"),
                "description": form_data.get("description"),
                "qr_code_image": qr_image,
                "qr_code_filename": qr_filename,
                "qr_code_uploaded_at": datetime.now() if qr_image else None,
            }

            # Erstelle ItemInfo über Repository
            result = item_info_repository.create_item_info(iteminfo_data)

            if result:
                saved_count += 1
                logger.info(f"ItemInfo created for article {article_number}")
            else:
                logger.error(f"Failed to create ItemInfo for article {article_number}")
                return False

        logger.info(f"Successfully saved {saved_count} ItemInfo entries")

        # Cleanup Session State
        st.session_state.iteminfo_form_data = {}
        st.session_state.articles_to_skip = set()
        st.session_state.qr_uploads = {}
        st.session_state.qr_filenames = {}

        return True

    except Exception as e:
        logger.error(f"Error saving ItemInfos: {str(e)}")
        logger.exception("Full traceback:")
        return False


def check_missing_iteminfos(
    extracted_articles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Prüft welche Artikel noch keine ItemInfo haben.

    Args:
        extracted_articles: Liste von extrahierten Artikeln aus AI [{article_number, ...}, ...]

    Returns:
        Liste der Artikel ohne ItemInfo
    """
    try:
        from warehouse.infrastructure.database.repositories.item_info_repository import (
            item_info_repository,
        )

        missing_articles = []

        for article in extracted_articles:
            article_number = article.get("article_number")

            if not article_number:
                continue

            # Prüfe ob ItemInfo existiert
            existing_iteminfo = item_info_repository.get_item_info_by_article_number(
                article_number
            )

            if existing_iteminfo is None:
                missing_articles.append(article)
                logger.info(f"Article {article_number} missing ItemInfo")

        logger.info(f"Found {len(missing_articles)} articles without ItemInfo")
        return missing_articles

    except Exception as e:
        logger.error(f"Error checking missing ItemInfos: {str(e)}")
        logger.exception("Full traceback:")
        return []
