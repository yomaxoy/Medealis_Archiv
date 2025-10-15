#!/usr/bin/env python3
"""
Visual Inspection Popup Module.

This module contains the visual inspection popup functionality
extracted from streamlit_app.py for better organization.

Author: Medealis
Version: 3.0.0 - MIGRATED TO NEW SERVICES
"""

import streamlit as st
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# NEW: Check if DocumentGenerationService is available
try:
    from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
    DOCUMENT_GENERATION_AVAILABLE = True
except ImportError:
    DOCUMENT_GENERATION_AVAILABLE = False
    logging.warning("DocumentGenerationService not available - visual inspection document creation will fail")

logger = logging.getLogger(__name__)


@st.dialog("👁️ Sichtkontrolle durchführen")
def show_visual_inspection_popup(item_data):
    """Show visual inspection popup for waste quantity input."""
    st.write("### 👁️ Sichtkontrolle durchführen")
    st.write(f"**Artikel:** {item_data['article_number']} | **Charge:** {item_data['batch_number']}")

    # Get data for the popup
    delivery_number = item_data.get('delivery_number', '')
    article_number = item_data.get('article_number', '')
    batch_number = item_data.get('batch_number', '')

    # Waste quantity input
    st.markdown("#### Ausschuss erfassen")
    waste_quantity = st.number_input(
        "Ausschussmenge eingeben:",
        min_value=0,
        step=1,
        format="%d",
        help="Menge des nicht verwendbaren Materials"
    )

    # Quality notes
    st.markdown("#### Qualitätsnotizen")
    quality_notes = st.text_area(
        "Bemerkungen zur Qualitätskontrolle:",
        placeholder="Hier können Sie Bemerkungen zur visuellen Inspektion eingeben...",
        height=100
    )

    # Inspector name
    st.markdown("#### Prüfer")
    inspector_name = st.text_input(
        "Name des Prüfers:",
        placeholder="Vollständiger Name des durchführenden Mitarbeiters"
    )

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("✅ Prüfung bestätigen", use_container_width=True):
            # Validate inspector name
            if not inspector_name or len(inspector_name.strip()) < 2:
                st.error("Bitte geben Sie einen gültigen Prüfernamen ein!")
                return

            # Prepare inspection data
            inspection_data = {
                'delivery_number': delivery_number,
                'article_number': article_number,
                'batch_number': batch_number,
                'waste_quantity': waste_quantity,
                'quality_notes': quality_notes.strip(),
                'inspector_name': inspector_name.strip(),
                'status': 'Sichtgeprüft'
            }

            # Save visual inspection to database (ALWAYS)
            try:
                from warehouse.application.services.entity_services.item_service import ItemService

                item_service = ItemService()
                success = item_service.complete_visual_inspection(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    performed_by=inspector_name.strip(),
                    waste_quantity=waste_quantity,
                    quality_notes=quality_notes.strip(),
                    passed=True
                )

                if not success:
                    st.error("❌ Fehler beim Speichern der Sichtkontrolle in DB")
                    return

            except Exception as e:
                st.error(f"❌ Fehler beim Speichern: {e}")
                logger.error(f"Error saving visual inspection: {e}", exc_info=True)
                return

            # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR Dokumentenerstellung
            from warehouse.presentation.user.popups.components.storage_warning_dialog import (
                check_and_show_storage_warning
            )

            # Zeige Warnung wenn Server nicht verfügbar
            can_continue = check_and_show_storage_warning(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=item_data.get('supplier_name', ''),
                compact=True  # Kompakte Warnung
            )

            if not can_continue:
                st.error("❌ Dokumentenerstellung abgebrochen - keine Speicher-Option verfügbar")
                return

            # Generate Sichtkontrolle document
            if DOCUMENT_GENERATION_AVAILABLE:
                st.info(f"🔧 DEBUG: DocumentGenerationService verfügbar - erstelle Dokument mit Ausschuss={waste_quantity}")
                _generate_visual_inspection_document(
                    item_data, inspection_data, waste_quantity, quality_notes.strip(), inspector_name.strip()
                )
            else:
                st.warning("⚠️ DocumentGenerationService nicht verfügbar - Dokument kann nicht erstellt werden")

            st.success("✅ Sichtkontrolle erfolgreich abgeschlossen!")
            st.rerun()

    with col2:
        if st.button("❌ Artikel zurückweisen", use_container_width=True):
            # Validate inspector name
            if not inspector_name or len(inspector_name.strip()) < 2:
                st.error("Bitte geben Sie einen gültigen Prüfernamen ein!")
                return

            # Require quality notes for rejection
            if not quality_notes or len(quality_notes.strip()) < 5:
                st.error("Bitte geben Sie einen Grund für die Zurückweisung an!")
                return

            # Mark as waste/rejected in database (ALWAYS)
            try:
                from warehouse.application.services.entity_services.item_service import ItemService

                item_service = ItemService()
                success = item_service.mark_item_as_waste(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    reason=quality_notes.strip(),
                    employee=inspector_name.strip()
                )

                if not success:
                    st.error("❌ Fehler beim Markieren als Ausschuss")
                    return

            except Exception as e:
                st.error(f"❌ Fehler: {e}")
                logger.error(f"Error marking as waste: {e}", exc_info=True)
                return

            # Prepare rejection data for document generation
            rejection_data = {
                'delivery_number': delivery_number,
                'article_number': article_number,
                'batch_number': batch_number,
                'waste_quantity': waste_quantity,
                'quality_notes': quality_notes.strip(),
                'inspector_name': inspector_name.strip(),
                'status': 'rejected'
            }

            # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR Dokumentenerstellung
            from warehouse.presentation.user.popups.components.storage_warning_dialog import (
                check_and_show_storage_warning
            )

            # Zeige Warnung wenn Server nicht verfügbar
            can_continue = check_and_show_storage_warning(
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=item_data.get('supplier_name', ''),
                compact=True  # Kompakte Warnung
            )

            if not can_continue:
                st.error("❌ Dokumentenerstellung abgebrochen - keine Speicher-Option verfügbar")
                return

            # Generate rejection document
            if DOCUMENT_GENERATION_AVAILABLE:
                _generate_visual_inspection_document(
                    item_data, rejection_data, waste_quantity, quality_notes.strip(), inspector_name.strip()
                )
            else:
                st.warning("⚠️ DocumentGenerationService nicht verfügbar - Dokument kann nicht erstellt werden")

            st.error("❌ Artikel wurde zurückgewiesen!")
            st.rerun()

    with col3:
        if st.button("🚫 Abbrechen", use_container_width=True):
            # No handler exists - just close popup with rerun
            st.rerun()

    # Additional information section
    st.markdown("---")
    with st.expander("ℹ️ Hinweise zur Sichtkontrolle"):
        st.markdown("""
        **Bei der visuellen Sichtkontrolle zu prüfen:**
        - Unversehrtheit der Verpackung
        - Vollständigkeit der Lieferung
        - Sichtbare Qualitätsmängel
        - Übereinstimmung mit Bestellung
        - Ablaufdatum (falls zutreffend)

        **Hinweise:**
        - Ausschussmenge wird automatisch von der Gesamtmenge abgezogen
        - Qualitätsnotizen werden in der Dokumentation gespeichert
        - Prüfername wird für die Nachvollziehbarkeit benötigt
        """)


def _generate_visual_inspection_document(
    item_data: Dict[str, Any],
    inspection_data: Dict[str, Any],
    waste_quantity: int,
    quality_notes: str,
    inspector_name: str
) -> None:
    """
    Generate Sichtkontrolle document using DocumentGenerationService.
    Pattern based on Step1/Step2 popups for consistency and SharePoint upload.
    """
    try:
        # Extract data
        article_number = item_data.get('article_number', '')
        batch_number = item_data.get('batch_number', '')
        delivery_number = item_data.get('delivery_number', '')

        with st.spinner("📋 Erstelle Sichtkontrolle-Dokument..."):
            # FIXED: Use DocumentGenerationService for automatic SharePoint upload
            from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
            from warehouse.application.services.document_generation.document_types import DocumentType

            doc_service = DocumentGenerationService()

            # Calculate ausschussquote (waste percentage)
            total_quantity = int(item_data.get('quantity', 0))
            if total_quantity > 0:
                waste_percentage = (waste_quantity / total_quantity) * 100
                ausschussquote = f"{waste_percentage:.1f}%"
            else:
                ausschussquote = "0%"

            # Prepare additional data for Sichtkontrolle template
            additional_data = {
                # Template placeholders
                "ausschuss": str(waste_quantity),
                "ausschussquote": ausschussquote,
                "name": inspector_name,
                "qty": str(total_quantity),
                "date": datetime.now().strftime('%d.%m.%Y'),
                "time": datetime.now().strftime('%H:%M'),

                # Context data
                'waste_quantity': waste_quantity,
                'effective_quantity': max(0, total_quantity - waste_quantity),
                'quality_notes': quality_notes,
                'inspection_date': datetime.now().strftime('%d.%m.%Y'),
                'inspection_time': datetime.now().strftime('%H:%M'),
                'status': 'Sichtgeprüft'
            }

            # DEBUG: Show placeholder data
            st.info(f"🔧 DEBUG: Placeholder-Daten werden an DocumentGenerationService übergeben:")
            st.json(additional_data)

            # Generate Sichtkontrolle document (DOCX + PDF + SharePoint Upload)
            sichtkontrolle_result = doc_service.generate_document(
                document_type=DocumentType.SICHTKONTROLLE,
                batch_number=batch_number,
                delivery_number=delivery_number,
                article_number=article_number,
                supplier_name=item_data.get('supplier_name', ''),
                quantity=total_quantity,
                employee_name=inspector_name,
                additional_data=additional_data
            )

            if sichtkontrolle_result.success:
                st.success("📋 Sichtkontrolle-Dokument wurde erfolgreich erstellt!")

                # NOTE: Database save is now done BEFORE document generation
                # (See main button handler above)

                # Show file info
                if sichtkontrolle_result.document_path:
                    st.info(f"📄 **DOCX-Datei:** {sichtkontrolle_result.document_path.name}")
                    st.caption(f"📁 **Pfad:** {sichtkontrolle_result.document_path}")

                # Show PDF info if generated
                if hasattr(sichtkontrolle_result, 'pdf_path') and sichtkontrolle_result.pdf_path:
                    st.info(f"📄 **PDF-Datei:** {sichtkontrolle_result.pdf_path.name}")
                    st.caption(f"📁 **PDF-Pfad:** {sichtkontrolle_result.pdf_path}")
                    st.success("✅ **PDF erfolgreich erstellt!**")
                else:
                    st.warning("⚠️ PDF-Erstellung fehlgeschlagen - DOCX wurde erstellt")

                # INTENTIONAL: Store generation result for audit trail and history tracking
                # This is NOT for handler communication - kept for potential future use
                # (e.g., audit logs, document history, debugging)
                st.session_state['visual_inspection_document_generated'] = {
                    'file_path': str(sichtkontrolle_result.document_path) if sichtkontrolle_result.document_path else None,
                    'pdf_path': str(sichtkontrolle_result.pdf_path) if hasattr(sichtkontrolle_result, 'pdf_path') and sichtkontrolle_result.pdf_path else None,
                    'template_used': sichtkontrolle_result.template_used,
                    'timestamp': datetime.now().isoformat(),
                    'context_data': additional_data
                }

                # Optional: Auto-open document (same pattern as Step1/Step2)
                try:
                    if sichtkontrolle_result.document_path and sichtkontrolle_result.document_path.exists():
                        import os
                        import platform
                        file_path = str(sichtkontrolle_result.document_path)

                        if st.button("📂 Dokument öffnen", key="open_sichtkontrolle_doc"):
                            if platform.system() == "Windows":
                                os.startfile(file_path)
                            elif platform.system() == "Darwin":  # macOS
                                os.system(f"open '{file_path}'")
                            else:  # Linux
                                os.system(f"xdg-open '{file_path}'")
                            st.success("📂 Dokument wurde geöffnet!")
                except Exception as open_error:
                    logger.warning(f"Could not provide open button: {open_error}")

            else:
                # Handle generation error
                error_msg = sichtkontrolle_result.error or 'Unbekannter Fehler'
                st.error(f"❌ Fehler bei der Dokumentenerstellung: {error_msg}")
                logger.error(f"Sichtkontrolle generation failed: {error_msg}")
                # Note: Visual inspection already saved to DB - document generation failure is non-critical

    except Exception as e:
        error_msg = f"Fehler bei der Sichtkontrolle-Dokumentenerstellung: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        # Note: Visual inspection already saved to DB - document generation failure is non-critical