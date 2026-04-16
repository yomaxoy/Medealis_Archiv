"""
ItemInfo Edit Dialog (Single Article)

Dialog zum Bearbeiten/Erstellen von ItemInfo für einen einzelnen Artikel.
Wird aus dem Extraktions-Popup heraus geöffnet.
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any
from PIL import Image

from warehouse.application.services.audit_service import audit_service
from warehouse.application.services.validation_service import validation_service
from warehouse.presentation.utils.user_context import get_current_username

logger = logging.getLogger(__name__)


@st.dialog("📝 Artikel-Informationen bearbeiten", width="large")
def show_iteminfo_edit_dialog(article_data: Dict[str, Any]):
    """
    Zeigt Dialog zum Bearbeiten von ItemInfo für einen einzelnen Artikel.

    Args:
        article_data: {
            article_number: str,
            description: str (optional),
            manufacturer: str (optional)
        }
    """
    article_number = article_data.get("article_number", "")

    if not article_number:
        st.error("❌ Keine Artikelnummer vorhanden!")
        if st.button("Schließen"):
            st.session_state.show_iteminfo_edit_dialog = False
            st.rerun()
        return

    st.markdown(f"### Artikelnummer: `{article_number}`")

    # Prüfe ob ItemInfo bereits existiert
    from warehouse.infrastructure.database.repositories.item_info_repository import (
        item_info_repository,
    )

    existing_iteminfo = item_info_repository.get_item_info_by_article_number(
        article_number
    )

    # 2-Spalten Layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 Stammdaten")

        # Bezeichnung aus description vorausgefüllt (vom Lieferschein) - PFLICHTFELD
        designation = st.text_input(
            "Bezeichnung *",
            value=existing_iteminfo.designation
            if existing_iteminfo
            else article_data.get("description", ""),
            key="iteminfo_edit_designation",
            placeholder="z.B. Schraubendreher Kreuzschlitz",
            help="Artikelbezeichnung (Pflichtfeld, max. 50 Zeichen)",
        )

        # Hersteller – verantwortlicher Hersteller des Abutments (PFLICHTFELD)
        hersteller = st.text_input(
            "Hersteller *",
            value=existing_iteminfo.hersteller
            if existing_iteminfo
            else article_data.get("hersteller", "Medealis GmbH"),
            key="iteminfo_edit_hersteller",
            placeholder="z.B. Medealis GmbH, Terrats Medical",
            help="Verantwortlicher Hersteller des Abutments (Pflichtfeld)",
        )

        # Kompatibilität – kompatible Implantatmarke (optional, automatisch abgeleitet)
        from warehouse.application.services.document_storage.storage_context import (
            determine_kompatibilitaet,
        )

        _article_number_for_komp = article_data.get("article_number", "")
        kompatibilitaet = st.text_input(
            "Kompatibilität",
            value=existing_iteminfo.kompatibilitaet
            if existing_iteminfo
            else article_data.get("kompatibilitaet", "")
            or determine_kompatibilitaet(_article_number_for_komp),
            key="iteminfo_edit_kompatibilitaet",
            placeholder="z.B. Straumann, Camlog, MegaGen",
            help="Kompatible Implantatmarke (automatisch "
            "aus Artikelnummer abgeleitet, editierbar)",
        )

        # Zeichnungsreferenz / Revision Number - PFLICHTFELD (INT)
        revision_number = st.number_input(
            "Zeichnungsreferenz (Rev.) *",
            value=existing_iteminfo.revision_number
            if existing_iteminfo and existing_iteminfo.revision_number
            else 0,
            min_value=0,
            step=1,
            key="iteminfo_edit_revision",
            help="Revisionsnummer der Zeichnung (Pflichtfeld, z.B. 1, 2, 3)",
        )

    with col2:
        st.markdown("#### 📦 Lager & Details")

        # LagerNo - PFLICHTFELD (INT)
        storage_location = st.number_input(
            "Lagerort (Nr.) *",
            value=int(existing_iteminfo.storage_location)
            if existing_iteminfo
            and existing_iteminfo.storage_location
            and existing_iteminfo.storage_location.isdigit()
            else 0,
            min_value=0,
            step=1,
            key="iteminfo_edit_storage",
            help="Lagernummer (Pflichtfeld, z.B. 123)",
        )

        # Zeichnungsreferenz Freitext (optional, für alphanumerische Werte)
        drawing_reference = st.text_input(
            "Zeichnungs-ID (optional)",
            value=existing_iteminfo.drawing_reference if existing_iteminfo else "",
            key="iteminfo_edit_drawing",
            placeholder="z.B. DRW-2024-001",
            help="Optionale alphanumerische Zeichnungsnummer",
        )

        description = st.text_area(
            "Zusätzliche Beschreibung",
            value=existing_iteminfo.description if existing_iteminfo else "",
            key="iteminfo_edit_description",
            height=100,
            placeholder="Optionale Zusatzinformationen...",
            help="Zusätzliche Beschreibung oder Notizen (optional)",
        )

    # Pflichtfeld-Hinweis
    st.caption("* Pflichtfelder")

    # QR-Code Upload Sektion
    st.markdown("#### 📸 QR-Code hochladen")

    # Zeige existierenden QR-Code falls vorhanden
    if existing_iteminfo and existing_iteminfo.qr_code_image:
        qr_fname = existing_iteminfo.qr_code_filename or "unbekannt"
        uploaded_at = existing_iteminfo.qr_code_uploaded_at
        qr_date = uploaded_at.strftime("%d.%m.%Y %H:%M") if uploaded_at else "unbekannt"
        st.info(f"✅ QR-Code vorhanden: {qr_fname} (hochgeladen am {qr_date})")

        col_qr1, col_qr2 = st.columns(2)
        with col_qr1:
            if st.button("🔄 QR-Code ersetzen", key="iteminfo_replace_qr"):
                st.session_state.replace_qr = True
                st.rerun()
        with col_qr2:
            if st.button("🗑️ QR-Code löschen", key="iteminfo_delete_qr"):
                item_info_repository.delete_qr_code(article_number)
                st.success("✅ QR-Code gelöscht!")
                st.rerun()

    # QR-Code Upload
    if (
        not existing_iteminfo
        or not existing_iteminfo.qr_code_image
        or st.session_state.get("replace_qr")
    ):
        qr_file = st.file_uploader(
            "QR-Code Bild",
            type=["png", "jpg", "jpeg"],
            key="iteminfo_edit_qr_upload",
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
                        "✅ QR-Code hochgeladen: "
                        f"{qr_file.name} "
                        f"({file_size_mb:.2f} MB)"
                    )

                    # Speichere in Session State
                    qr_file.seek(0)  # Reset file pointer
                    st.session_state.edit_qr_data = qr_file.read()
                    st.session_state.edit_qr_filename = qr_file.name

                except Exception as e:
                    st.error(f"❌ Fehler beim Laden des Bildes: {str(e)}")

    # Aktions-Buttons
    st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("❌ Abbrechen", use_container_width=True):
            # Cleanup
            st.session_state.show_iteminfo_edit_dialog = False
            st.session_state.pop("edit_qr_data", None)
            st.session_state.pop("edit_qr_filename", None)
            st.session_state.pop("replace_qr", None)
            st.rerun()

    with col_btn2:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            # VALIDATION FIRST
            validation_data = {
                "designation": designation,
                "storage_location": str(storage_location),
                "hersteller": hersteller,
                "kompatibilitaet": kompatibilitaet,
                "revision_number": revision_number,
            }

            validation_result = validation_service.validate_iteminfo(validation_data)

            if not validation_result.is_valid:
                st.error("❌ **Validierungsfehler:**")
                st.error(validation_result.get_formatted_errors())
                return  # Stop execution

            # Validation successful - prepare data
            # Prepare data
            iteminfo_data = {
                "article_number": article_number,
                "designation": designation.strip(),
                "hersteller": hersteller.strip() if hersteller else "Medealis GmbH",
                "kompatibilitaet": (
                    kompatibilitaet.strip() if kompatibilitaet else None
                ),
                "drawing_reference": drawing_reference.strip()
                if drawing_reference
                else None,
                "storage_location": str(storage_location),  # Convert int to str for DB
                "revision_number": revision_number,
                "description": description.strip() if description else None,
            }

            # QR-Code Daten hinzufügen falls vorhanden
            if st.session_state.get("edit_qr_data"):
                iteminfo_data["qr_code_image"] = st.session_state.edit_qr_data
                iteminfo_data["qr_code_filename"] = st.session_state.edit_qr_filename
                iteminfo_data["qr_code_uploaded_at"] = datetime.now()

            try:
                is_update = existing_iteminfo is not None

                if is_update:
                    # Update existing
                    result = item_info_repository.update_item_info(
                        article_number, iteminfo_data
                    )
                else:
                    # Create new
                    result = item_info_repository.create_item_info(iteminfo_data)

                if result:
                    st.success(f"✅ ItemInfo für Artikel {article_number} gespeichert!")

                    # AUDIT LOGGING
                    current_user = get_current_username()

                    if is_update:
                        audit_service.log_iteminfo_updated(
                            user=current_user,
                            article_number=article_number,
                            designation=designation.strip(),
                            hersteller=hersteller.strip() if hersteller else None,
                            kompatibilitaet=kompatibilitaet.strip()
                            if kompatibilitaet
                            else None,
                        )
                    else:
                        audit_service.log_iteminfo_created(
                            user=current_user,
                            article_number=article_number,
                            designation=designation.strip(),
                            hersteller=hersteller.strip() if hersteller else None,
                            kompatibilitaet=kompatibilitaet.strip()
                            if kompatibilitaet
                            else None,
                        )

                    # QR-Code Upload loggen falls vorhanden
                    if st.session_state.get("edit_qr_data"):
                        audit_service.log_qr_uploaded(
                            user=current_user,
                            article_number=article_number,
                            filename=st.session_state.edit_qr_filename,
                        )

                    # Cleanup
                    st.session_state.show_iteminfo_edit_dialog = False
                    st.session_state.pop("edit_qr_data", None)
                    st.session_state.pop("edit_qr_filename", None)
                    st.session_state.pop("replace_qr", None)

                    st.rerun()
                else:
                    st.error("❌ Fehler beim Speichern!")
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
                logger.exception("Error saving ItemInfo:")
