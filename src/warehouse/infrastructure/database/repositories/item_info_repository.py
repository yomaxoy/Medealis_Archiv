"""
ItemInfo Repository

Repository für ItemInfo-Stammdaten (Artikel-Stamminformationen).
Unterstützt QR-Code Binary Storage.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from warehouse.infrastructure.database.connection import get_session
from warehouse.infrastructure.database.models.item_model import ItemInfoModel

logger = logging.getLogger(__name__)


class ItemInfoRepository:
    """Repository für ItemInfo-Operationen."""

    def get_item_info_by_article_number(
        self, article_number: str
    ) -> Optional[ItemInfoModel]:
        """
        Lädt ItemInfo anhand der Artikelnummer.

        Args:
            article_number: Artikelnummer

        Returns:
            ItemInfoModel oder None wenn nicht gefunden
        """
        try:
            with get_session() as session:
                item_info = (
                    session.query(ItemInfoModel)
                    .filter(ItemInfoModel.article_number == article_number)
                    .first()
                )

                if item_info:
                    # Detach from session for usage outside
                    session.expunge(item_info)

                return item_info

        except Exception as e:
            logger.error(f"Error loading ItemInfo for {article_number}: {str(e)}")
            return None

    def create_item_info(
        self, item_info_data: Dict[str, Any]
    ) -> Optional[ItemInfoModel]:
        """
        Erstellt einen neuen ItemInfo-Eintrag.

        Args:
            item_info_data: Dictionary mit ItemInfo-Daten {
                article_number: str,
                designation: str,
                hersteller: str (optional),
                kompatibilitaet: str (optional),
                drawing_reference: str (optional),
                revision_number: int (optional),
                storage_location: str (optional),
                material_specification: str (optional),
                description: str (optional),
                qr_code_image: bytes (optional),
                qr_code_filename: str (optional),
                qr_code_uploaded_at: datetime (optional)
            }

        Returns:
            ItemInfoModel oder None bei Fehler
        """
        try:
            with get_session() as session:
                # Prüfe ob bereits vorhanden
                existing = (
                    session.query(ItemInfoModel)
                    .filter(
                        ItemInfoModel.article_number == item_info_data["article_number"]
                    )
                    .first()
                )

                if existing:
                    art_nr = item_info_data["article_number"]
                    logger.warning(
                        f"ItemInfo for {art_nr} " f"already exists - skipping"
                    )
                    session.expunge(existing)
                    return existing

                # Erstelle neuen ItemInfo
                item_info = ItemInfoModel(
                    article_number=item_info_data["article_number"],
                    designation=item_info_data["designation"],
                    hersteller=item_info_data.get("hersteller"),
                    kompatibilitaet=item_info_data.get("kompatibilitaet"),
                    drawing_reference=item_info_data.get("drawing_reference"),
                    revision_number=item_info_data.get("revision_number"),
                    storage_location=item_info_data.get("storage_location"),
                    material_specification=item_info_data.get("material_specification"),
                    description=item_info_data.get("description"),
                    qr_code_image=item_info_data.get("qr_code_image"),
                    qr_code_filename=item_info_data.get("qr_code_filename"),
                    qr_code_uploaded_at=item_info_data.get("qr_code_uploaded_at"),
                )

                session.add(item_info)
                session.flush()

                logger.info(
                    f"ItemInfo created for article {item_info_data['article_number']}"
                )

                # Automatisch Workflow-Status "Artikeldetails vollständig" setzen
                self._set_iteminfo_complete_status(
                    session, item_info_data["article_number"]
                )

                # EXPLICIT COMMIT before detach
                # to ensure data is in DB before rerun
                session.commit()

                # Detach from session
                session.expunge(item_info)

                return item_info

        except Exception as e:
            logger.error(f"Error creating ItemInfo: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def update_item_info(
        self, article_number: str, update_data: Dict[str, Any]
    ) -> Optional[ItemInfoModel]:
        """
        Aktualisiert einen ItemInfo-Eintrag.

        Args:
            article_number: Artikelnummer
            update_data: Dictionary mit zu aktualisierenden Feldern

        Returns:
            ItemInfoModel oder None bei Fehler
        """
        try:
            with get_session() as session:
                item_info = (
                    session.query(ItemInfoModel)
                    .filter(ItemInfoModel.article_number == article_number)
                    .first()
                )

                if not item_info:
                    logger.warning(f"ItemInfo for {article_number} not found")
                    return None

                # Update fields
                for key, value in update_data.items():
                    if hasattr(item_info, key) and key != "article_number":
                        setattr(item_info, key, value)

                # Update timestamp
                item_info.updated_at = datetime.now()

                session.flush()

                logger.info(f"ItemInfo updated for article {article_number}")

                # Automatisch Workflow-Status "Artikeldetails vollständig" setzen
                self._set_iteminfo_complete_status(session, article_number)

                # EXPLICIT COMMIT before detach
                # to ensure data is in DB before rerun
                session.commit()

                # Detach from session
                session.expunge(item_info)

                return item_info

        except Exception as e:
            logger.error(f"Error updating ItemInfo: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def update_qr_code(
        self, article_number: str, qr_image: bytes, qr_filename: str
    ) -> bool:
        """
        Aktualisiert QR-Code für einen Artikel.

        Args:
            article_number: Artikelnummer
            qr_image: Binary QR-Code Image
            qr_filename: Dateiname

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with get_session() as session:
                item_info = (
                    session.query(ItemInfoModel)
                    .filter(ItemInfoModel.article_number == article_number)
                    .first()
                )

                if not item_info:
                    logger.warning(f"ItemInfo for {article_number} not found")
                    return False

                item_info.qr_code_image = qr_image
                item_info.qr_code_filename = qr_filename
                item_info.qr_code_uploaded_at = datetime.now()
                item_info.updated_at = datetime.now()

                session.flush()

                logger.info(
                    f"QR-Code updated for article {article_number}: {qr_filename}"
                )

                return True

        except Exception as e:
            logger.error(f"Error updating QR-Code: {str(e)}")
            logger.exception("Full traceback:")
            return False

    def get_qr_code(self, article_number: str) -> Optional[Dict[str, Any]]:
        """
        Lädt QR-Code Daten für einen Artikel.

        Args:
            article_number: Artikelnummer

        Returns:
            Dictionary {image: bytes, filename: str, uploaded_at: datetime} oder None
        """
        try:
            with get_session() as session:
                item_info = (
                    session.query(ItemInfoModel)
                    .filter(ItemInfoModel.article_number == article_number)
                    .first()
                )

                if not item_info or not item_info.qr_code_image:
                    return None

                return {
                    "image": item_info.qr_code_image,
                    "filename": item_info.qr_code_filename,
                    "uploaded_at": item_info.qr_code_uploaded_at,
                }

        except Exception as e:
            logger.error(f"Error loading QR-Code: {str(e)}")
            return None

    def delete_qr_code(self, article_number: str) -> bool:
        """
        Löscht QR-Code für einen Artikel.

        Args:
            article_number: Artikelnummer

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with get_session() as session:
                item_info = (
                    session.query(ItemInfoModel)
                    .filter(ItemInfoModel.article_number == article_number)
                    .first()
                )

                if not item_info:
                    logger.warning(f"ItemInfo for {article_number} not found")
                    return False

                item_info.qr_code_image = None
                item_info.qr_code_filename = None
                item_info.qr_code_uploaded_at = None
                item_info.updated_at = datetime.now()

                session.flush()

                logger.info(f"QR-Code deleted for article {article_number}")

                return True

        except Exception as e:
            logger.error(f"Error deleting QR-Code: {str(e)}")
            return False

    def _set_iteminfo_complete_status(self, session, article_number: str) -> None:
        """
        Setzt automatisch den Workflow-Status
        "Artikeldetails vollständig" für alle Items mit
        dieser Artikelnummer.

        Args:
            session: Aktive SQLAlchemy Session
            article_number: Artikelnummer
        """
        try:
            from warehouse.infrastructure.database.models.item_workflow_steps_model import (  # noqa: E501
                ItemWorkflowStepsModel,
            )

            # Finde alle Workflow-Einträge für diese Artikelnummer
            workflow_entries = (
                session.query(ItemWorkflowStepsModel)
                .filter(ItemWorkflowStepsModel.article_number == article_number)
                .all()
            )

            if not workflow_entries:
                logger.debug(f"No workflow entries found for article {article_number}")
                return

            # Setze Status für alle gefundenen Einträge
            current_user = (
                "System"  # TODO: Könnte aus session_state kommen falls verfügbar
            )
            current_time = datetime.now()

            for workflow in workflow_entries:
                # Nur setzen wenn noch nicht gesetzt
                if not workflow.iteminfo_complete_at:
                    workflow.iteminfo_complete_by = current_user
                    workflow.iteminfo_complete_at = current_time
                    logger.info(
                        f"Workflow status "
                        f"'Artikeldetails vollständig'"
                        f" set for {article_number}"
                        f"/{workflow.batch_number}"
                        f"/{workflow.delivery_number}"
                    )

            session.flush()

        except Exception as e:
            logger.error(f"Error setting iteminfo_complete status: {str(e)}")
            logger.exception("Full traceback:")


# Global instance
item_info_repository = ItemInfoRepository()
