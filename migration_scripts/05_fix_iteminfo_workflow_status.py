"""
Migration Script: Fix ItemInfo Workflow Status

Setzt den Workflow-Status "Artikeldetails vollständig" für alle Items,
deren Artikelnummer in der item_info Tabelle existiert.

Dies behebt das Problem, dass der Haken für ItemInfo nicht angezeigt wird.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import logging  # noqa: E402
from datetime import datetime  # noqa: E402

from warehouse.infrastructure.database.connection import get_session  # noqa: E402
from warehouse.infrastructure.database.models.item_model import (  # noqa: E402
    ItemInfoModel,
)
from warehouse.infrastructure.database.models.item_workflow_steps_model import (  # noqa: E402,E501
    ItemWorkflowStepsModel,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fix_iteminfo_workflow_status():
    """
    Setzt iteminfo_complete_by/iteminfo_complete_at für alle Workflow-Einträge,
    deren Artikelnummer in item_info existiert.
    """
    try:
        with get_session() as session:
            # 1. Hole alle Artikelnummern aus item_info
            iteminfo_articles = (
                session.query(ItemInfoModel.article_number).distinct().all()
            )
            article_numbers = [article[0] for article in iteminfo_articles]

            logger.info(
                f"Found {len(article_numbers)} distinct article numbers in item_info"
            )

            # 2. Für jede Artikelnummer, setze Workflow-Status
            total_updated = 0
            total_skipped = 0

            for article_number in article_numbers:
                # Finde alle Workflow-Einträge für diese Artikelnummer
                workflow_entries = (
                    session.query(ItemWorkflowStepsModel)
                    .filter(ItemWorkflowStepsModel.article_number == article_number)
                    .all()
                )

                if not workflow_entries:
                    logger.debug(
                        f"No workflow entries found for article {article_number}"
                    )
                    continue

                # Setze Status für alle gefundenen Einträge
                current_time = datetime.now()

                for workflow in workflow_entries:
                    # Nur setzen wenn noch nicht gesetzt
                    if not workflow.iteminfo_complete_at:
                        workflow.iteminfo_complete_by = "Migration Script"
                        workflow.iteminfo_complete_at = current_time
                        total_updated += 1
                        logger.info(
                            f"✅ Set iteminfo_complete for {article_number}/"
                            f"{workflow.batch_number}/{workflow.delivery_number}"
                        )
                    else:
                        total_skipped += 1
                        logger.debug(
                            f"⏭️  Skipped {article_number}/"
                            f"{workflow.batch_number}/"
                            f"{workflow.delivery_number} - already set"
                        )

            # Commit changes
            session.commit()

            logger.info("=" * 60)
            logger.info("Migration completed successfully!")
            logger.info(f"Total workflow entries updated: {total_updated}")
            logger.info(f"Total workflow entries skipped: {total_skipped}")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        logger.exception("Full traceback:")
        raise


if __name__ == "__main__":
    logger.info("Starting ItemInfo Workflow Status Fix Migration...")
    fix_iteminfo_workflow_status()
    logger.info("Migration finished!")
