"""
Folder Button Component
Wiederverwendbarer "Artikelordner öffnen"-Button für alle Views.
"""

import streamlit as st
from typing import Dict, Any, Optional
import logging

from warehouse.application.services.document_storage import path_resolver
from warehouse.application.services.document_storage.storage_context import (
    StorageContextData,
)
from warehouse.application.services.document_operations.document_opening_service import (  # noqa: E501
    document_opening_service,
)

logger = logging.getLogger(__name__)


def _determine_manufacturer_from_article(article_number: str) -> str:
    """
    Leitet Manufacturer automatisch von Artikelnummer ab.

    Nutzt die gleiche Logik wie StorageContext für Konsistenz.

    Args:
        article_number: Artikelnummer (z.B. CT0004, MG0001)

    Returns:
        Manufacturer-Name (z.B. C-Tech, MegaGen)
    """
    if not article_number:
        return ""

    article_upper = article_number.upper()

    # WICHTIG: Gleiche Mapping-Regeln wie in storage_context.py (Zeile 501)
    # Längste Prefixes zuerst!
    manufacturer_map = {
        # 2-character prefixes
        "AS": "Dentsply",
        "BR": "Bredent",
        "CT": "C-Tech",
        "DY": "Dyna",
        "MG": "MegaGen",
        "NE": "Neodent",
        "SI": "Southern Implants",
        "P4": "General Implants",
        "S4": "General Implants",
        # 1-character prefixes
        "A": "Zubehörteile",
        "B": "Bego",
        "C": "Camlog",
        "D": "Dentsply",
        "E": "Zubehörteile",
        "L": "Lasak",
        "M": "Medentis",
        "N": "Nobel Biocare",
        "O": "Osstem",
        "S": "Straumann",
        "Z": "Zimmer Biomet",
    }

    # Check längste Prefixes zuerst (sortiert nach Länge)
    for prefix in sorted(manufacturer_map.keys(), key=len, reverse=True):
        if article_upper.startswith(prefix):
            return manufacturer_map[prefix]

    return "Standard_Implantate"


def render_open_folder_button(
    item_data: Dict[str, Any],
    label: str = "🗂️ Artikelordner öffnen",
    button_type: str = "primary",
    key_suffix: str = "",
    use_server_path: bool = True,
    help_text: Optional[str] = None,
) -> bool:
    """
    Wiederverwendbarer Button zum Öffnen des Artikelordners im Windows Explorer.

    Der Button löst den Ordnerpfad über PathResolver auf und öffnet ihn mit
    DocumentOpeningService. Unterstützt sowohl Server- als auch lokale Pfade
    mit automatischem Fallback.

    Args:
        item_data: Dictionary mit Artikeldaten. Muss enthalten:
            - article_number: Artikelnummer
            - batch_number: Chargennummer
            - delivery_number: Lieferscheinnummer
            - supplier_name: Lieferantenname
            - manufacturer: Herstellername
        label: Button-Text (default: "🗂️ Artikelordner öffnen")
        button_type: Streamlit Button-Typ ("primary", "secondary")
        key_suffix: Suffix für unique Session-State-Key
        use_server_path: True = Server-Pfad bevorzugen, False = nur lokal
        help_text: Optionaler Hilfetext für den Button

    Returns:
        True wenn Button geklickt wurde, sonst False

    Beispiel:
        ```python
        # In einer View:
        item = {
            "article_number": "MG0001",
            "batch_number": "20240415-1234",
            "delivery_number": "LS24-077",
            "supplier_name": "Primec GmbH",
            "manufacturer": "MegaGen"
        }

        if render_open_folder_button(item, key_suffix="detail_view"):
            st.success("Ordner wurde geöffnet!")
        ```
    """

    # Validiere erforderliche Daten (ohne manufacturer - wird automatisch abgeleitet)
    required_fields = [
        "article_number",
        "batch_number",
        "delivery_number",
        "supplier_name",
    ]
    missing_fields = [field for field in required_fields if not item_data.get(field)]

    if missing_fields:
        st.warning(
            "⚠️ Artikelordner kann nicht geöffnet "
            "werden. Fehlende Daten: "
            f"{', '.join(missing_fields)}"
        )
        return False

    # Erstelle eindeutigen Key
    unique_key = (
        f"open_folder_{item_data['article_number']}"
        f"_{item_data['batch_number']}_{key_suffix}"
    )

    # Rendere Button
    if help_text is None:
        help_text = "Öffnet den Artikelordner mit allen Dokumenten im Windows Explorer"

    button_clicked = st.button(
        label,
        key=unique_key,
        type=button_type,
        help=help_text,
        use_container_width=False,
    )

    if not button_clicked:
        return False

    # Button wurde geklickt - jetzt erst Kompatibilitätsmarke ableiten
    # Backward-Compat: lese auch altes "manufacturer"-Feld falls vorhanden
    kompatibilitaet = item_data.get("kompatibilitaet", "") or item_data.get(
        "manufacturer", ""
    )
    if not kompatibilitaet:
        kompatibilitaet = _determine_manufacturer_from_article(
            item_data["article_number"]
        )
        logger.info(
            "Kompatibilität automatisch abgeleitet: "
            f"{item_data['article_number']} "
            f"→ {kompatibilitaet}"
        )

    # Ordner öffnen
    try:
        # Erstelle StorageContext aus item_data
        context = StorageContextData(
            batch_number=item_data["batch_number"],
            delivery_number=item_data["delivery_number"],
            article_number=item_data["article_number"],
            supplier_normalized=item_data["supplier_name"],
            kompatibilitaet=kompatibilitaet,
            context_source="ui",
        )

        # Bestimme Pfad (Server oder Lokal)
        folder_path = None

        if use_server_path:
            # Versuche zuerst Server-Pfad
            result = path_resolver.resolve_server_storage_path(
                context, create_folders=False
            )
            if result.success and result.path.exists():
                folder_path = result.path

                logger.info(f"Server-Pfad gefunden: {folder_path}")
            else:
                logger.warning(f"Server-Pfad nicht verfügbar: {result.error}")

        # Fallback auf lokalen Pfad wenn Server nicht verfügbar oder nicht gewünscht
        if folder_path is None:
            result = path_resolver.resolve_storage_path(context, create_folders=False)
            if result.success and result.path.exists():
                folder_path = result.path

                logger.info(f"Lokaler Pfad gefunden: {folder_path}")
            else:
                logger.warning(f"Lokaler Pfad nicht verfügbar: {result.error}")

        # Wenn kein Pfad existiert - Frage ob erstellt werden soll
        if folder_path is None or not folder_path.exists():
            st.warning("⚠️ Artikelordner existiert noch nicht.")

            # Zeige Option zum Erstellen
            col1, col2 = st.columns([1, 3])
            with col1:
                create_key = f"{unique_key}_create"
                if st.button("📁 Ordner erstellen", key=create_key, type="secondary"):
                    # Erstelle Ordner
                    if use_server_path:
                        result = path_resolver.resolve_server_storage_path(
                            context, create_folders=True
                        )
                    else:
                        result = path_resolver.resolve_storage_path(
                            context, create_folders=True
                        )

                    if result.success:
                        folder_path = result.path
                        # Öffne den neu erstellten Ordner (ohne UI-Feedback)
                        document_opening_service.open_folder(folder_path)
                        logger.info(f"Ordner erstellt und geöffnet: {folder_path}")
                    else:
                        st.error(
                            "❌ Fehler beim Erstellen " "des Ordners: " f"{result.error}"
                        )

            with col2:
                st.caption(f"Pfad: {result.path if result else 'Nicht verfügbar'}")

            return True

        # Ordner existiert - Öffne im Windows Explorer (ohne UI-Feedback)
        if document_opening_service.open_folder(folder_path):
            logger.info(f"Artikelordner geöffnet: {folder_path}")
        else:
            logger.error(f"Fehler beim Öffnen des Ordners: {folder_path}")

        return True

    except Exception as e:
        st.error(f"❌ Fehler beim Öffnen des Artikelordners: {str(e)}")
        logger.error(f"Fehler in render_open_folder_button: {e}", exc_info=True)
        return False


def render_compact_folder_button(
    item_data: Dict[str, Any], key_suffix: str = "", use_server_path: bool = True
) -> bool:
    """
    Kompakte Variante für Tabellen - nur Icon ohne Text.

    Args:
        item_data: Dictionary mit Artikeldaten (siehe render_open_folder_button)
        key_suffix: Suffix für unique Session-State-Key
        use_server_path: True = Server-Pfad bevorzugen, False = nur lokal

    Returns:
        True wenn Button geklickt wurde, sonst False

    Beispiel:
        ```python
        # In einer Tabellen-Zeile:
        col1, col2, col3, col_actions = st.columns([3, 2, 2, 1])
        with col_actions:
            render_compact_folder_button(item, key_suffix=f"row_{idx}")
        ```
    """
    return render_open_folder_button(
        item_data=item_data,
        label="🗂️",
        button_type="secondary",
        key_suffix=key_suffix,
        use_server_path=use_server_path,
        help_text="Artikelordner im Explorer öffnen",
    )


def render_folder_action_with_status(
    item_data: Dict[str, Any], key_suffix: str = "", use_server_path: bool = True
) -> bool:
    """
    Erweiterte Variante mit Ordner-Status-Indikator.
    Zeigt visuell an ob Ordner bereits existiert (grün)
    oder noch erstellt werden muss (gelb).

    Args:
        item_data: Dictionary mit Artikeldaten (siehe render_open_folder_button)
        key_suffix: Suffix für unique Session-State-Key
        use_server_path: True = Server-Pfad bevorzugen, False = nur lokal

    Returns:
        True wenn Button geklickt wurde, sonst False
    """

    # Prüfe ob Ordner existiert
    try:
        _komp = item_data.get("kompatibilitaet", "") or item_data.get(
            "manufacturer", ""
        )
        if not _komp:
            _komp = _determine_manufacturer_from_article(item_data["article_number"])
        context = StorageContextData(
            batch_number=item_data["batch_number"],
            delivery_number=item_data["delivery_number"],
            article_number=item_data["article_number"],
            supplier_normalized=item_data["supplier_name"],
            kompatibilitaet=_komp,
            context_source="ui",
        )

        folder_exists = False
        if use_server_path:
            result = path_resolver.resolve_server_storage_path(
                context, create_folders=False
            )
            folder_exists = result.success and result.path.exists()

        if not folder_exists:
            result = path_resolver.resolve_storage_path(context, create_folders=False)
            folder_exists = result.success and result.path.exists()

        # Zeige Button mit Status-Icon
        if folder_exists:
            label = "🗂️ Ordner öffnen"
            button_type = "primary"
        else:
            label = "📁 Ordner erstellen & öffnen"
            button_type = "secondary"

        return render_open_folder_button(
            item_data=item_data,
            label=label,
            button_type=button_type,
            key_suffix=key_suffix,
            use_server_path=use_server_path,
        )

    except Exception as e:
        logger.error(f"Fehler in render_folder_action_with_status: {e}")
        # Fallback auf Standard-Button
        return render_open_folder_button(
            item_data=item_data, key_suffix=key_suffix, use_server_path=use_server_path
        )
