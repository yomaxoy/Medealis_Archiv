"""
Document Merge Popup
Popup for merging documents with proper database integration.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from warehouse.application.services.entity_services.item_service import ItemService


@st.dialog("📁 Dokumente zusammenführen", width="large")
def show_document_merge_popup(item_data):
    """
    Document merge popup with database integration
    """
    st.write("### 📁 Dokumente zusammenführen")

    # Initialize services
    item_service = ItemService()

    # Item information
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Artikel-Nr:** {item_data.get('article_number', 'N/A')}")
        st.write(f"**Chargen-Nr:** {item_data.get('batch_number', 'N/A')}")
    with col2:
        st.write(
            f"**Menge:** {item_data.get('delivery_quantity', item_data.get('quantity', 'N/A'))}"
        )
        st.write(f"**LS-Nr:** {item_data.get('delivery_number', 'N/A')}")

    st.divider()

    # Document selection
    st.write("### 📄 Verfügbare Dokumente")

    # Get documents using DocumentStorageService (SharePoint → Local fallback)
    try:
        import logging
        logger = logging.getLogger(__name__)

        from warehouse.application.services.service_registry import get_document_storage_service

        storage_service = get_document_storage_service()

        if not storage_service:
            st.error("❌ DocumentStorageService nicht verfügbar")
            doc_files = []
        else:
            delivery_number = item_data.get("delivery_number", "")
            batch_number = item_data.get("batch_number", "")
            article_number = item_data.get("article_number", "")
            supplier_name = item_data.get("supplier_name", "")

            # DEBUG LOGGING
            logger.info(f"🔥 ADMIN MERGE POPUP: delivery_number={delivery_number}")
            logger.info(f"🔥 ADMIN MERGE POPUP: batch_number={batch_number}")
            logger.info(f"🔥 ADMIN MERGE POPUP: article_number={article_number}")
            logger.info(f"🔥 ADMIN MERGE POPUP: supplier_name={supplier_name}")
            logger.info(f"🔥 ADMIN MERGE POPUP: Full item_data={item_data}")

            # Use new method that downloads from SharePoint with local fallback
            with st.spinner("📥 Lade Dokumente (SharePoint → Lokal)..."):
                doc_files = storage_service.get_documents_for_merge(
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    article_number=article_number,
                    supplier_name=supplier_name
                )

            logger.info(f"🔥 ADMIN MERGE POPUP: Found {len(doc_files)} documents")

            if not doc_files:
                st.warning("⚠️ Keine PDF-Dokumente gefunden (weder auf SharePoint noch lokal)")

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Dokumente: {e}")
        doc_files = []

    if doc_files:
        selected_docs = []

        for doc_file in doc_files:
            col_check, col_name, col_size = st.columns([1, 4, 1])

            with col_check:
                if st.checkbox("", key=f"select_{doc_file.name}"):
                    selected_docs.append(doc_file)

            with col_name:
                st.write(f"📄 {doc_file.name}")

            with col_size:
                file_size = doc_file.stat().st_size / 1024  # KB
                st.write(f"{file_size:.1f} KB")

        st.divider()

        # Merge options
        with st.form("merge_form"):
            output_name = st.text_input(
                "Ausgabedatei:", value=f"Merged_{delivery_number}.pdf"
            )

            merge_order = st.selectbox(
                "Reihenfolge:",
                ["Alphabetisch", "Chronologisch", "Benutzerdefiniert"],
            )

            include_cover = st.checkbox("Deckblatt hinzufügen", value=True)

            if include_cover:
                cover_title = st.text_input(
                    "Deckblatt Titel:", value=f"Dokumentation {delivery_number}"
                )

            col_merge, col_cancel = st.columns(2)

            with col_merge:
                if st.form_submit_button(
                    "🔗 Zusammenführen", use_container_width=True, type="primary"
                ):
                    if selected_docs:
                        try:
                            # Create document merge record using the item service
                            merge_data = {
                                "timestamp": datetime.now().isoformat(),
                                "selected_files": [
                                    doc.name for doc in selected_docs
                                ],
                                "output_name": output_name,
                                "merge_order": merge_order,
                                "include_cover": include_cover,
                                "cover_title": (
                                    cover_title if include_cover else None
                                ),
                                "article_number": item_data.get("article_number"),
                                "batch_number": item_data.get("batch_number"),
                                "delivery_number": item_data.get("delivery_number"),
                            }

                            # Store merge information in the item's notes field
                            article_number = item_data.get("article_number")
                            batch_number = item_data.get("batch_number")
                            delivery_number = item_data.get("delivery_number")

                            # Get current item to update notes
                            item = item_service.get_item(
                                article_number, batch_number, delivery_number
                            )
                            if item:
                                # Append merge information to notes
                                merge_note = f"Dokumente zusammengeführt: {output_name} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                                current_notes = item.get("notes", "")
                                updated_notes = (
                                    f"{current_notes}\n{merge_note}"
                                    if current_notes
                                    else merge_note
                                )

                                # Update item with merge information
                                notes_success = item_service.update_item_notes(
                                    article_number=article_number,
                                    batch_number=batch_number,
                                    delivery_number=delivery_number,
                                    notes=updated_notes,
                                )

                                # Mark workflow step as completed
                                workflow_success = item_service.complete_documents_merge(
                                    article_number=article_number,
                                    batch_number=batch_number,
                                    delivery_number=delivery_number,
                                    employee=st.session_state.get('current_user', 'System')
                                )

                                if notes_success and workflow_success:
                                    st.success(
                                        f"✅ Dokumente zusammengeführt: {output_name}"
                                    )
                                    st.success(
                                        "✅ Workflow-Schritt abgeschlossen"
                                    )
                                elif workflow_success:
                                    st.success("✅ Workflow-Schritt abgeschlossen")
                                    st.warning("⚠️ Notes-Update fehlgeschlagen")
                                else:
                                    st.warning(
                                        "⚠️ Dokumente zusammengeführt, aber Workflow-Update fehlgeschlagen"
                                    )
                            else:
                                st.warning("⚠️ Item nicht in der Datenbank gefunden")

                            st.rerun()

                        except Exception as e:
                            st.error(
                                f"❌ Fehler beim Speichern der Merge-Daten: {str(e)}"
                            )
                    else:
                        st.error("Bitte wählen Sie mindestens ein Dokument aus!")

            with col_cancel:
                if st.form_submit_button("❌ Abbrechen", use_container_width=True):
                    st.rerun()
    else:
        st.warning("⚠️ Keine PDF-Dokumente zum Zusammenführen verfügbar")
