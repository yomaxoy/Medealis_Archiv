"""
Document Confirmation Popup - Step 2
Second step of the two-step workflow: Certificate and document verification
Based on splitting the original data_confirmation_popup.py
"""

import streamlit as st
import os
from datetime import datetime
from pathlib import Path
import logging
from warehouse.domain.enums.certificate_type import CertificateType

# NEW: Import centralized services via ServiceRegistry
try:
    from warehouse.application.services.service_registry import (
        get_document_storage_service,
        get_item_service
    )
    from warehouse.application.services import DocumentGenerationService
    CENTRALIZED_SERVICES_AVAILABLE = True
except ImportError:
    CENTRALIZED_SERVICES_AVAILABLE = False
    get_document_storage_service = None
    get_item_service = None
    DocumentGenerationService = None
    logging.warning("Centralized services not available - using fallback")

logger = logging.getLogger(__name__)


def _map_document_types_to_checkboxes(document_types):
    """
    Mappt Dokumenttypen-Array zu Checkbox-Zuständen.
    """
    checkboxes = {
        "Materialzeugnis": False,
        "Messprotokoll": False,
        "Beschichtungszeugnis": False,
        "hartezeugnis": False,
    }

    for doc_type in document_types:
        if not doc_type:
            continue

        doc_type_lower = doc_type.lower()

        if "materialzeugnis" in doc_type_lower or "material" in doc_type_lower:
            checkboxes["Materialzeugnis"] = True
        elif "messprotokoll" in doc_type_lower or "mess" in doc_type_lower or "protocol" in doc_type_lower:
            checkboxes["Messprotokoll"] = True
        elif "beschichtungszeugnis" in doc_type_lower or "beschichtung" in doc_type_lower or "coating" in doc_type_lower:
            checkboxes["Beschichtungszeugnis"] = True
        elif "härtezeugnis" in doc_type_lower or "hartezeugnis" in doc_type_lower or "härte" in doc_type_lower or "hardness" in doc_type_lower:
            checkboxes["hartezeugnis"] = True

    return checkboxes


@st.dialog("📄 Schritt 2: Dokumente bestätigen", width="large")
def show_document_confirmation_step2_popup(item_data, step1_data=None):
    """Show Step 2: Document confirmation - certificate flags and physical document attachment verification."""
    st.write("### 📄 Schritt 2: Dokumente und Zertifikate bestätigen")

    # Use step1_data if provided, otherwise fall back to item_data
    if step1_data:
        article_number = step1_data['article_number']
        batch_number = step1_data['batch_number']
    else:
        article_number = item_data.get('article_number', '')
        batch_number = item_data.get('batch_number', '')

    # Validate batch_number before proceeding
    if not batch_number or not batch_number.strip():
        st.error("❌ Fehler: Chargennummer ist leer. Bitte schließen Sie das Popup und prüfen Sie die Daten.")
        return

    st.write(f"**Artikel:** {article_number} | **Charge:** {batch_number}")

    st.info("💡 **In diesem Schritt:** Bestätigen Sie welche Zertifikate vorliegen und dass Label und Begleitschein korrekt angebracht/beigelegt wurden. Das Label wird mit den Zertifikatsinformationen erstellt.")

    # === MITARBEITERNAME ===
    st.markdown("#### 👤 Prüfer")
    employee_name = st.text_input(
        "Name des durchführenden Mitarbeiters:",
        value=st.session_state.get('current_user', ''),
        placeholder="Vollständiger Name für PDB-Dokument",
        key="step2_employee_name",
        help="Dieser Name wird auf dem PDB-Dokument angezeigt"
    )

    # === BEGLEITDOKUMENTE UPLOAD ===
    st.write("**📤 Begleitdokumente hochladen für KI-Analyse**")
    st.info("💡 Laden Sie Begleitdokumente hoch für automatische Erkennung und Validierung")

    # File uploader for accompanying documents
    uploaded_accompanying_docs = st.file_uploader(
        "Begleitdokumente auswählen",
        accept_multiple_files=True,
        type=['pdf', 'png', 'jpg', 'jpeg', 'docx'],
        key="accompanying_documents_step2",
        help="Unterstützte Formate: PDF, PNG, JPG, DOCX"
    )

    # Process uploaded documents
    if uploaded_accompanying_docs:
        st.write(f"📄 {len(uploaded_accompanying_docs)} Dokument(e) hochgeladen:")

        for i, doc in enumerate(uploaded_accompanying_docs):
            # Show document info
            col_doc_info, col_doc_action = st.columns([2, 1])

            with col_doc_info:
                st.write(f"📄 **{doc.name}** ({doc.size} bytes)")
                st.caption(f"Dateityp: {doc.type}")

            with col_doc_action:
                # KI-Analyse Button direkt sichtbar
                if st.button(f"🤖 Analysieren", key=f"ai_analyze_doc_{i}", type="primary", use_container_width=True):
                    try:
                        # Import unified document processing service
                        from warehouse.application.services.document_processing import process_document

                        st.info(f"🤖 Analysiere {doc.name}...")

                        # Read document data
                        document_data = doc.read()
                        doc.seek(0)  # Reset file pointer

                        # Analyze document with unified service
                        context = {
                            "article_number": article_number,
                            "batch_number": batch_number
                        }

                        accompanying_result = process_document(
                            document_data=document_data,
                            document_type="accompanying",
                            **context
                        )

                        # Convert unified service result to expected GUI format
                        if accompanying_result and not accompanying_result.get("error"):
                            # Extract data from accompanying document result
                            validation_status = accompanying_result.get("validation_status", {})
                            doc_analysis = accompanying_result.get("document_analysis", {})
                            article_search = accompanying_result.get("article_search", {})
                            batch_search = accompanying_result.get("batch_search", {})

                            analysis_result = {
                                "success": True,
                                "document_name": doc.name,
                                "document_type": doc_analysis.get("primary_type", "Unbekannt"),
                                "article_match": article_search.get("found", False),
                                "batch_match": batch_search.get("found", False),
                                "detected_article": article_search.get("detected_number"),
                                "detected_batch": batch_search.get("detected_number"),
                                "confidence": validation_status.get("match_confidence", "niedrig"),
                                "checkboxes": _map_document_types_to_checkboxes(doc_analysis.get("types", [])),
                                "raw_response": str(accompanying_result)
                            }
                        else:
                            analysis_result = {
                                "success": False,
                                "error": accompanying_result.get("error", "Processing failed") if accompanying_result else "Processing failed"
                            }

                        if analysis_result['success']:
                            st.success("✅ Analyse erfolgreich!")

                            # Show analysis results
                            doc_type = analysis_result.get('document_type', 'Unbekannt')
                            article_match = analysis_result.get('article_match', False)
                            batch_match = analysis_result.get('batch_match', False)
                            detected_article = analysis_result.get('detected_article', '')
                            detected_batch = analysis_result.get('detected_batch', '')
                            confidence = analysis_result.get('confidence', 'mittel')

                            st.write(f"**Dokumenttyp:** {doc_type}")
                            st.write(f"**Gefundene Artikelnummer:** {detected_article}")
                            st.write(f"**Gefundene Chargennummer:** {detected_batch}")
                            st.write(f"**Vertrauen:** {confidence}")

                            # Show validation results
                            if article_match:
                                st.success("✅ Artikelnummer stimmt überein")
                            else:
                                st.warning("⚠️ Artikelnummer stimmt nicht überein")

                            if batch_match:
                                st.success("✅ Chargennummer stimmt überein")
                            else:
                                st.warning("⚠️ Chargennummer stimmt nicht überein")

                            # NEW: Save document using centralized storage service
                            try:
                                if CENTRALIZED_SERVICES_AVAILABLE:
                                    storage_service = get_document_storage_service()

                                    # Create filename with prefix like Vermessungsprotokoll
                                    begleitpapiere_filename = f"Begleitpapiere_{article_number}_{doc.name}"

                                    save_result = storage_service.save_document(
                                        document_data=document_data,
                                        document_name=begleitpapiere_filename,
                                        document_type="begleitdokument",
                                        batch_number=batch_number,
                                        delivery_number=item_data.get('delivery_number', ''),
                                        article_number=article_number,
                                        supplier_name=item_data.get('supplier_name', '')
                                    )

                                    if save_result.success:
                                        st.success(f"💾 **Neue Storage Service**: Dokument gespeichert")
                                        st.info(f"📁 Pfad: {save_result.file_path}")
                                        st.caption(f"📊 Ordner: {save_result.storage_folder}")
                                    else:
                                        st.error(f"❌ Storage Service Fehler: {save_result.error}")
                                        raise Exception(f"Storage failed: {save_result.error}")

                                else:
                                    raise ImportError("Centralized services not available")

                            except Exception as storage_error:
                                # FALLBACK: Use old document_storage_service
                                st.warning(f"⚠️ Fallback zu altem System: {storage_error}")
                                try:
                                    from warehouse.application.services.document_storage import document_storage_service

                                    # Create filename with prefix like Vermessungsprotokoll
                                    begleitpapiere_filename = f"Begleitpapiere_{article_number}_{doc.name}"

                                    save_result = document_storage_service.save_document(
                                        document_data=document_data,
                                        document_name=begleitpapiere_filename,
                                        document_type="begleitdokument",
                                        batch_number=batch_number,
                                        article_number=article_number,
                                        delivery_number=item_data.get('delivery_number', ''),
                                        supplier_name=item_data.get('supplier_name', '')
                                    )

                                    if save_result['success']:
                                        st.success(f"💾 Dokument gespeichert: {save_result['filename']}")
                                        st.info(f"📁 Pfad: {save_result['file_path']}")
                                    else:
                                        st.error(f"❌ {save_result['error']}")

                                except Exception as fallback_error:
                                    st.error(f"❌ Beide Storage-Systeme fehlgeschlagen: {fallback_error}")

                            # Automatically set checkboxes based on document type
                            checkboxes = analysis_result.get('checkboxes', {})
                            if checkboxes:
                                if 'checkbox_updates' not in st.session_state:
                                    st.session_state.checkbox_updates = {}

                                # Update session state for automatic checkbox setting
                                st.session_state.checkbox_updates.update(checkboxes)

                                # Show which checkboxes will be set
                                set_checkboxes = [k for k, v in checkboxes.items() if v]
                                if set_checkboxes:
                                    st.info(f"🤖 Folgende Checkboxen werden automatisch gesetzt: {', '.join(set_checkboxes)}")

                            # Store analysis result for this document
                            if 'document_analysis_results' not in st.session_state:
                                st.session_state.document_analysis_results = {}

                            st.session_state.document_analysis_results[doc.name] = analysis_result

                        else:
                            st.error(f"❌ Analyse fehlgeschlagen: {analysis_result.get('error', 'Unbekannt')}")

                    except ImportError:
                        st.error("❌ Begleitdokument-Analysedienst nicht verfügbar")
                    except Exception as e:
                        st.error(f"❌ Fehler bei der Analyse: {e}")
                        import traceback
                        st.error(f"Details: {traceback.format_exc()}")

            # Show analysis results if available
            if hasattr(st.session_state, 'document_analysis_results') and doc.name in st.session_state.document_analysis_results:
                result = st.session_state.document_analysis_results[doc.name]
                if result['success']:
                    with st.expander(f"📊 Analyseergebnis für {doc.name}", expanded=False):
                        st.write(f"**Dokumenttyp:** {result.get('document_type', 'Unbekannt')}")
                        st.write(f"**Artikelnummer:** {'✅' if result.get('article_match') else '❌'} {result.get('detected_article', 'Nicht gefunden')}")
                        st.write(f"**Chargennummer:** {'✅' if result.get('batch_match') else '❌'} {result.get('detected_batch', 'Nicht gefunden')}")
                        st.write(f"**Vertrauen:** {result.get('confidence', 'mittel')}")

            st.write("---")

    st.write("---")

    # === DOKUMENTE PRÜFUNG ===
    st.write("**📄 Welche Begleitdokumente liegen der Lieferung bei?**")

    col3, col4 = st.columns(2)

    # Extract certificate data from item_data for pre-filling checkboxes
    certificates = item_data.get('certificates', {})

    # Check for automatic checkbox updates from AI analysis
    checkbox_updates = st.session_state.get('checkbox_updates', {})

    # LOG TO CONSOLE for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 STEP 2 POPUP OPEN: Item data certificates loaded: {certificates}")
    logger.info(f"🔍 STEP 2 POPUP OPEN: Checkbox updates: {checkbox_updates}")

    if checkbox_updates:
        st.info(f"🤖 KI-Analyse hat folgende Dokumenttypen erkannt: {', '.join(checkbox_updates.keys())}")

    with col3:
        materialzeugnis = st.checkbox(
            "📋 Materialzeugnis",
            key="popup_step2_materialzeugnis",
            value=certificates.get('material_certificate', False) or checkbox_updates.get('Materialzeugnis', False)
        )
        messprotokolle = st.checkbox(
            "📊 Messprotokolle",
            key="popup_step2_messprotokolle",
            value=certificates.get('measurement_protocol', False) or checkbox_updates.get('Messprotokoll', False)
        )
        beschichtungszeugnis = st.checkbox(
            "🎨 Beschichtungszeugnis",
            key="popup_step2_beschichtung",
            value=certificates.get('coating_certificate', False) or checkbox_updates.get('Beschichtungszeugnis', False)
        )

    with col4:
        haertezeugnis = st.checkbox(
            "🔨 Härtezeugnis",
            key="popup_step2_haerte",
            value=certificates.get('hardness_certificate', False) or checkbox_updates.get('hartezeugnis', False)
        )
        weitere_zeugnisse_text = st.text_input(
            "📝 Weitere Zeugnisse:",
            placeholder="z.B. Kalibrierungszeugnis...",
            key="popup_step2_weitere"
        )

    st.write("---")

    # === NEW FLAGS - PHYSICAL DOCUMENT VERIFICATION ===
    st.write("**📋 Physische Dokumente und Label Verifikation**")
    st.write("*Bestätigen Sie, dass die erstellten Dokumente korrekt angebracht bzw. beigelegt wurden:*")

    col5, col6 = st.columns(2)

    with col5:
        label_attached = st.checkbox(
            "🏷️ Label geprüft und angebracht",
            key="popup_step2_label_attached",
            value=certificates.get('label_present', False),
            help="Das gedruckte Label wurde überprüft und am Artikel angebracht"
        )

    with col6:
        accompanying_document_attached = st.checkbox(
            "📋 Begleitschein beigelegt",
            key="popup_step2_accompanying_document",
            value=certificates.get('accompanying_document', False),
            help="Der gedruckte Begleitschein wurde überprüft und der Lieferung beigelegt"
        )

    st.write("---")

    # === ARTIKEL ORDNER ===
    st.write("**📁 Artikel-Ordner zum Speichern der Dokumente:**")

    # Show Artikel-Ordner Path using central DocumentStorageService
    try:
        if CENTRALIZED_SERVICES_AVAILABLE:
            # Use ServiceRegistry to get proper service instance
            storage_service = get_document_storage_service()
            folder_path, warnings = storage_service.get_document_path(
                batch_number=batch_number,
                delivery_number=item_data.get('delivery_number', ''),
                article_number=article_number
            )
        else:
            # Fallback: Import service instance directly
            from warehouse.application.services.document_storage.document_storage_service import document_storage_service
            folder_path, warnings = document_storage_service.get_document_path(
                batch_number=batch_number,
                delivery_number=item_data.get('delivery_number', ''),
                article_number=article_number
            )

        col7, col8 = st.columns([3, 1])
        with col7:
            st.code(str(folder_path), language=None)
        with col8:
            if st.button("📂 Ordner öffnen", key="open_folder_step2_btn"):
                try:
                    # Create folder if not existing
                    folder_path.mkdir(parents=True, exist_ok=True)

                    # Open folder in Explorer
                    import platform

                    if platform.system() == "Windows":
                        # Use os.startfile for Windows - more reliable than subprocess
                        import os
                        os.startfile(str(folder_path))
                    elif platform.system() == "Darwin":  # macOS
                        import subprocess
                        subprocess.run(['open', str(folder_path)], check=True)
                    else:  # Linux
                        import subprocess
                        subprocess.run(['xdg-open', str(folder_path)], check=True)

                    st.success("📂 Ordner geöffnet!")
                except Exception as e:
                    st.error(f"❌ Fehler beim Öffnen des Ordners: {e}")

    except Exception as e:
        st.warning(f"⚠️ Ordner-Pfad konnte nicht ermittelt werden: {e}")

    st.write("---")

    # === AKTIONEN ===
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        button_clicked = st.button("✅ Dokumente bestätigen", type="primary", use_container_width=True)

        # STEP 2 PROCESSING - Certificate and document verification
        if button_clicked:
            # Validate employee name first
            if not employee_name or len(employee_name.strip()) < 2:
                st.error("❌ Bitte geben Sie einen gültigen Mitarbeiternamen ein!")
                return

            import logging
            logger = logging.getLogger(__name__)
            logger.info("🔥 STEP 2: Document confirmation button clicked!")
            logger.info(f"🔥 STEP 2: Employee name: {employee_name}")
            logger.info(f"🔥 STEP 2: Current checkbox states - materialzeugnis={materialzeugnis}, messprotokolle={messprotokolle}, beschichtungszeugnis={beschichtungszeugnis}, haertezeugnis={haertezeugnis}")
            logger.info(f"🔥 STEP 2: Physical document states - label_attached={label_attached}, accompanying_document_attached={accompanying_document_attached}")

            # Collect all certificate and document information
            documents_found = {
                'materialzeugnis': materialzeugnis,
                'messprotokolle': messprotokolle,
                'beschichtungszeugnis': beschichtungszeugnis,
                'haertezeugnis': haertezeugnis,
                'weitere_zeugnisse': weitere_zeugnisse_text.strip() if weitere_zeugnisse_text else ''
            }

            # Enhanced debugging - TO CONSOLE!
            logger.info(f"🔍 STEP 2 DEBUG: Documents found: {documents_found}")
            logger.info(f"🔍 STEP 2 DEBUG: Individual certificate values:")
            for key, value in documents_found.items():
                logger.info(f"   - {key}: {value} (type: {type(value)})")
            logger.info(f"🔍 STEP 2 DEBUG: Physical document flags:")
            logger.info(f"   - label_attached: {label_attached} (type: {type(label_attached)})")
            logger.info(f"   - accompanying_document_attached: {accompanying_document_attached} (type: {type(accompanying_document_attached)})")

            # Show simplified info to user
            st.write(f"🔍 Certificates selected: {list(k for k, v in documents_found.items() if v)}")
            st.write(f"🔍 Physical documents: Label={label_attached}, Begleitschein={accompanying_document_attached}")

            # CERTIFICATE AND DOCUMENT FLAG SAVE
            logger.info("🔥 STEP 2 SAVE: Saving certificate and document flags now!")
            st.write("🔥 Saving certificates and document flags...")
            try:
                item_service = st.session_state.services['item']

                # Log the exact parameters being sent
                save_params = {
                    'article_number': article_number,
                    'batch_number': batch_number,
                    'delivery_number': item_data.get('delivery_number', ''),
                    'employee_name': employee_name or 'System',
                    'measurement_protocol': documents_found.get('messprotokolle', False),
                    'material_certificate': documents_found.get('materialzeugnis', False),
                    'coating_certificate': documents_found.get('beschichtungszeugnis', False),
                    'hardness_certificate': documents_found.get('haertezeugnis', False),
                    'additional_certificates': bool(documents_found.get('weitere_zeugnisse', '').strip()),
                    'label_present': label_attached,  # NEW FLAG
                    'accompanying_document': accompanying_document_attached  # NEW FLAG
                }
                logger.info(f"🔥 STEP 2 SAVE: Parameters being sent: {save_params}")

                item_service.update_item(**save_params)
                logger.info("🔥 STEP 2 SAVE: SUCCESS - Certificates and document flags saved!")
                st.success("🔥 Certificates and document flags saved!")
            except Exception as e:
                logger.error(f"🔥 STEP 2 SAVE ERROR: {e}")
                import traceback
                logger.error(f"🔥 STEP 2 SAVE Traceback: {traceback.format_exc()}")
                st.error(f"❌ Error saving certificates and document flags: {e}")

            # NEW: CREATE PDB/LABEL WITH CERTIFICATE INFORMATION using new generation service
            try:
                pdb_created = False

                if CENTRALIZED_SERVICES_AVAILABLE:
                    st.write("✨ **Neue Generation Service**: Erstelle PDB mit Zertifikatsinformationen...")

                    # Prepare certificate data for PDB generation
                    certificate_data = {
                        # Certificate flags
                        'materialzeugnis': 'X' if documents_found.get('materialzeugnis') else '',
                        'messprotokolle': 'X' if documents_found.get('messprotokolle') else '',
                        'beschichtungszeugnis': 'X' if documents_found.get('beschichtungszeugnis') else '',
                        'haertezeugnis': 'X' if documents_found.get('haertezeugnis') else '',
                        'weitere_zeugnisse': documents_found.get('weitere_zeugnisse', ''),

                        # Physical document flags
                        'label_attached': 'X' if label_attached else '',
                        'accompanying_document': 'X' if accompanying_document_attached else '',

                        # Status and timestamps
                        'status': 'Dokumente geprüft',
                        'inspection_date': datetime.now().strftime('%d.%m.%Y'),
                        'inspection_time': datetime.now().strftime('%H:%M'),

                        # Document counts for summary
                        'certificate_count': sum(1 for flag in [documents_found.get('materialzeugnis'),
                                                               documents_found.get('messprotokolle'),
                                                               documents_found.get('beschichtungszeugnis'),
                                                               documents_found.get('haertezeugnis')] if flag),
                    }

                    # ⚠️ NEU: Storage-Verfügbarkeits-Check VOR PDB-Generierung
                    from warehouse.presentation.user.popups.components.storage_warning_dialog import (
                        check_and_show_storage_warning
                    )

                    # Zeige Warnung wenn Server nicht verfügbar
                    can_continue = check_and_show_storage_warning(
                        batch_number=batch_number,
                        delivery_number=item_data.get('delivery_number', ''),
                        article_number=article_number,
                        supplier_name=item_data.get('supplier_name', ''),
                        compact=True  # Kompakte Warnung
                    )

                    if not can_continue:
                        st.error("❌ PDB-Generierung abgebrochen - keine Speicher-Option verfügbar")
                        return

                    try:
                        # FIXED: Use DocumentGenerationService for automatic SharePoint upload
                        from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
                        from warehouse.application.services.document_generation.document_types import DocumentType

                        doc_service = DocumentGenerationService()

                        # CRITICAL FIX: Reload fresh item data from DB before PDB generation
                        # Problem: item_data parameter may contain stale data from before Step1 updates
                        # Solution: Always get fresh data from database
                        from warehouse.application.services.service_registry import get_item_service
                        item_service = get_item_service()
                        fresh_item_data = item_service.get_item_by_composite_key(
                            article_number,
                            batch_number,
                            item_data.get('delivery_number', '')
                        )

                        # Use fresh data if available, otherwise fall back to passed data
                        item_data_for_pdb = fresh_item_data if fresh_item_data else item_data

                        # Generate PDB document with certificate data (DOCX + PDF + SharePoint Upload)
                        pdb_result = doc_service.generate_document(
                            document_type=DocumentType.PDB,
                            batch_number=batch_number,
                            delivery_number=item_data_for_pdb.get('delivery_number', ''),
                            article_number=article_number,
                            supplier_name=item_data_for_pdb.get('supplier_name', ''),
                            quantity=item_data_for_pdb.get('quantity', 0),
                            employee_name=employee_name or 'System',
                            additional_data=certificate_data
                        )

                        if pdb_result.success:
                            st.success("✅ **PDB erfolgreich erstellt mit Zertifikatsinformationen**")
                            st.write(f"📄 DOCX-Pfad: {pdb_result.document_path}")

                            # Show PDF info if generated
                            if hasattr(pdb_result, 'pdf_path') and pdb_result.pdf_path:
                                st.write(f"📄 PDF-Pfad: {pdb_result.pdf_path}")
                                st.success("✅ **PDF erfolgreich erstellt!**")
                            else:
                                st.warning("⚠️ PDF-Erstellung fehlgeschlagen - DOCX wurde erstellt")

                            st.info(f"📊 Kontext-Vollständigkeit: {pdb_result.context_completeness:.1%}")
                            st.caption(f"🕜 Generierungszeit: {pdb_result.generation_time:.2f}s")

                            # Show certificate summary in PDB
                            cert_summary = []
                            if certificate_data['materialzeugnis']: cert_summary.append("📋 Materialzeugnis")
                            if certificate_data['messprotokolle']: cert_summary.append("📊 Messprotokolle")
                            if certificate_data['beschichtungszeugnis']: cert_summary.append("🎨 Beschichtungszeugnis")
                            if certificate_data['haertezeugnis']: cert_summary.append("🔨 Härtezeugnis")

                            if cert_summary:
                                st.info(f"📄 **Zertifikate in PDB eingetragen**: {', '.join(cert_summary)}")

                            pdb_created = True

                        else:
                            st.warning(f"⚠️ PDB konnte nicht erstellt werden: {pdb_result.error}")
                            logger.error(f"PDB generation failed: {pdb_result.error}")

                    except Exception as gen_error:
                        st.warning(f"⚠️ Generation Service Fehler: {gen_error}")
                        logger.error(f"Generation service error: {gen_error}")
                        raise gen_error

                if not pdb_created:
                    # FIXED: Use standardized DocumentGenerationService instead of fallback
                    st.info("🔄 **Retry**: Verwende standardisierte PDB Generation")

                    try:
                        from warehouse.application.services.document_generation.document_generation_service import DocumentGenerationService
                        from warehouse.application.services.document_generation.document_types import DocumentType

                        # Initialize generation service
                        doc_service = DocumentGenerationService()

                        # CRITICAL FIX: Reload fresh item data from DB before PDB generation
                        from warehouse.application.services.service_registry import get_item_service
                        item_service = get_item_service()
                        fresh_item_data = item_service.get_item_by_composite_key(
                            article_number,
                            batch_number,
                            item_data.get('delivery_number', '')
                        )

                        # Use fresh data if available, otherwise fall back to passed data
                        item_data_for_pdb = fresh_item_data if fresh_item_data else item_data

                        # Generate PDB document with complete data
                        pdb_result = doc_service.generate_document(
                            document_type=DocumentType.PDB,
                            batch_number=batch_number,
                            delivery_number=item_data_for_pdb.get('delivery_number', ''),
                            article_number=item_data_for_pdb.get('article_number', ''),
                            supplier_name=item_data_for_pdb.get('supplier_name', ''),
                            quantity=item_data_for_pdb.get('quantity', 0),
                            employee_name=employee_name or 'System'
                        )

                        # FIXED: Show creation results based on GenerationResult
                        if pdb_result.success:
                            st.success("✅ **PDB erfolgreich erstellt mit Zertifikatsinformationen**")
                            if pdb_result.document_path:
                                st.write(f"📄 {pdb_result.document_path.name}")
                            if hasattr(pdb_result, 'pdf_path') and pdb_result.pdf_path:
                                st.write(f"📄 {pdb_result.pdf_path.name}")
                            pdb_created = True
                        else:
                            st.warning("⚠️ PDB konnte nicht erstellt werden")
                            if pdb_result.error:
                                st.error(f"❌ {pdb_result.error}")

                    except Exception as retry_error:
                        st.error(f"❌ Retry failed: {retry_error}")
                        logger.error(f"Document generation retry failed: {retry_error}")

                if not pdb_created:
                    st.warning("⚠️ PDB/Label konnte mit keinem System erstellt werden")
                    st.info("📄 **Sie können das PDB manuell erstellen** oder den Vorgang später wiederholen.")

            except Exception as e:
                logger.error(f"🔥 STEP 2 PDB CREATION ERROR: {e}")
                import traceback
                logger.error(f"🔥 STEP 2 PDB Traceback: {traceback.format_exc()}")
                st.error(f"❌ Error creating PDB/Label: {e}")

            try:
                # Build certificates dictionary with CertificateType enum keys
                certificates_dict = {
                    CertificateType.MATERIALZEUGNIS.value: documents_found.get('materialzeugnis', False),
                    CertificateType.MESSPROTOKOLL.value: documents_found.get('messprotokolle', False),
                    CertificateType.BESCHICHTUNGSZEUGNIS.value: documents_found.get('beschichtungszeugnis', False),
                    CertificateType.HAERTEZEUGNIS.value: documents_found.get('haertezeugnis', False),
                    CertificateType.WEITERE_ZEUGNISSE.value: bool(documents_found.get('weitere_zeugnisse', '').strip()),
                    CertificateType.ETIKETT.value: label_attached,
                    CertificateType.BEGLEITSCHEIN.value: accompanying_document_attached
                }

                logger.info(f"🔥 ADMIN WORKFLOW: Certificates dict: {certificates_dict}")

                # Use new workflow method to complete document check
                item_service.complete_document_check(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=item_data.get('delivery_number', ''),
                    employee=st.session_state.get('current_user', 'System'),
                    certificates=certificates_dict
                )
                st.success("✅ Dokumentenprüfung abgeschlossen")

                # Process document information for summary
                document_summary = []

                if documents_found.get('materialzeugnis'):
                    document_summary.append("📋 Materialzeugnis")
                if documents_found.get('messprotokolle'):
                    document_summary.append("📊 Messprotokolle")
                if documents_found.get('beschichtungszeugnis'):
                    document_summary.append("🎨 Beschichtungszeugnis")
                if documents_found.get('haertezeugnis'):
                    document_summary.append("🔨 Härtezeugnis")
                if documents_found.get('weitere_zeugnisse'):
                    document_summary.append(f"📝 {documents_found['weitere_zeugnisse']}")

                # Show certificate summary
                if document_summary:
                    st.success("📄 **Gefundene Dokumente:**")
                    for doc in document_summary:
                        st.write(f"  - {doc}")
                else:
                    st.info("ℹ️ Keine Begleitdokumente ausgewählt")

                # Show physical document verification summary
                st.success("📋 **Physische Dokumente:**")
                if label_attached:
                    st.write("  - ✅ Label geprüft und angebracht")
                else:
                    st.write("  - ❌ Label nicht angebracht")

                if accompanying_document_attached:
                    st.write("  - ✅ Begleitschein beigelegt")
                else:
                    st.write("  - ❌ Begleitschein nicht beigelegt")

                # Force refresh of cached data
                if 'cached_items' in st.session_state:
                    del st.session_state.cached_items

                # REMOVED: Session state status cache - DB is single source of truth
                # article_key = f"{article_number}_{batch_number}_{item_data.get('delivery_number', '')}"
                # st.session_state[f'item_status_{article_key}'] = new_status

                st.balloons()
                st.success("🎉 **Artikel erfolgreich verarbeitet!**")
                st.success("✅ **Zwei-Schritt-Workflow abgeschlossen!**")

                # Clean popup state and store confirmed data for processing
                confirmed_data_item = {
                    'article_number': article_number,
                    'batch_number': batch_number,
                    'delivery_number': item_data.get('delivery_number', ''),
                    'status': new_status,
                    'documents_found': documents_found,
                    'label_attached': label_attached,
                    'accompanying_document_attached': accompanying_document_attached,
                    'step1_data': step1_data  # Include step1 data for reference
                }

                # INTENTIONAL: Handler communication required for Data Confirmation
                # Handler performs POST-PROCESSING (batch/quantity updates, document generation)
                st.session_state.confirmed_data_item = confirmed_data_item
                st.session_state['popup_action'] = 'step2_completed'

                # Clean up Step 1 data - no longer needed after Step 2 completion
                if 'step1_confirmed_data' in st.session_state:
                    del st.session_state['step1_confirmed_data']

                # Exit cleanly to close dialog
                st.success("✅ Dialog wird geschlossen...")
                st.rerun()

            except Exception as e:
                logger.error(f"🔥 STEP 2 FINAL ERROR: {e}")
                import traceback
                logger.error(f"🔥 STEP 2 FINAL Traceback: {traceback.format_exc()}")
                st.error(f"❌ Fehler bei der finalen Verarbeitung: {e}")

    with col_btn2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state['popup_action'] = 'cancel'
            # INTENTIONAL: Clean up Step 1 data on cancel - popup responsibility
            if 'step1_confirmed_data' in st.session_state:
                del st.session_state['step1_confirmed_data']
            st.rerun()