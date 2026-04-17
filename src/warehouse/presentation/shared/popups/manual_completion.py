"""
Manual Completion Popup (Shared)
Ermöglicht das manuelle Einlagern von Artikeln, deren Dokumentation
außerhalb des Systems erstellt wurde.
"""

import streamlit as st
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@st.dialog("🏭 Manuell einlagern", width="large")
def show_manual_completion_popup(item_data: Dict[str, Any]) -> None:
    """
    Popup zum manuellen Abschließen eines Artikels ohne vollständige Workflow-Schritte.
    Fehlende Schritte werden als 'Extern / [Mitarbeiter]' markiert.

    Args:
        item_data: Dictionary mit article_number, batch_number, delivery_number, quantity
    """
    article_number = item_data.get("article_number", "N/A")
    batch_number = item_data.get("batch_number", "N/A")
    delivery_number = item_data.get("delivery_number", "N/A")
    delivered_quantity = item_data.get("quantity", 0) or 0

    st.write("### 🏭 Artikel manuell einlagern")
    st.write(
        f"**Artikel:** {article_number} | **Charge:** {batch_number}"
    )
    st.write(
        f"**Lieferung:** {delivery_number} | **Liefermenge:** {delivered_quantity} Stk."
    )

    st.write("---")

    # Fehlende Schritte ermitteln
    missing_steps = []
    try:
        services = st.session_state.get("services", {})
        item_service = services.get("item")
        if item_service:
            missing_steps = item_service.get_missing_workflow_steps(
                article_number, batch_number, delivery_number
            )
    except Exception as e:
        logger.error("Fehler beim Laden fehlender Schritte: %s", e)

    if missing_steps:
        st.warning(
            "⚠️ **Folgende Schritte wurden im System nicht dokumentiert** "
            "und werden als *Extern* markiert:"
        )
        for step in missing_steps:
            st.write(f"  • {step}")
        st.info(
            "ℹ️ Alle fehlenden Schritte erhalten den Vermerk "
            "**'Extern / [Mitarbeitername]'** mit aktuellem Zeitstempel."
        )
    else:
        st.info("ℹ️ Alle Workflow-Schritte sind bereits abgeschlossen.")

    st.write("---")

    # Mitarbeiter (vorausgefüllt aus Session)
    default_employee = st.session_state.get("logged_in_user", "")
    employee = st.text_input(
        "Mitarbeiter *",
        value=default_employee,
        placeholder="Name des Mitarbeiters",
        key="manual_completion_employee",
    )

    # Begründung
    reason = st.text_area(
        "Begründung *",
        placeholder="z.B. Dokumentation extern erstellt – Unterlagen liegen in Papierform vor",
        key="manual_completion_reason",
        height=90,
    )

    st.write("---")
    st.write("**Ausschuss**")

    # Ausschuss-Menge
    waste_quantity = st.number_input(
        "Ausschuss-Menge (Stk.)",
        min_value=0,
        max_value=int(delivered_quantity) if delivered_quantity else 9999,
        value=0,
        step=1,
        help="Anzahl der Teile, die nicht eingelagert werden können (0 = kein Ausschuss)",
        key="manual_completion_waste_qty",
    )

    # Ausschuss-Grund – nur sichtbar wenn Ausschuss > 0
    waste_reason = None
    if waste_quantity > 0:
        waste_reason = st.text_input(
            "Ausschuss-Grund *",
            placeholder="z.B. Maßabweichung, Oberflächenfehler, fehlende Zertifikate",
            key="manual_completion_waste_reason",
        )

    st.write("---")

    # Bestätigungs-Checkbox
    confirmed = st.checkbox(
        "Ich bestätige, dass die vollständige Produktdokumentation "
        "außerhalb des Systems abgeschlossen wurde und vorliegt.",
        key="manual_completion_confirmed",
    )

    st.write("---")

    col_cancel, col_submit = st.columns([1, 1])

    # Submit-Bedingungen
    waste_reason_ok = (waste_quantity == 0) or bool(waste_reason and waste_reason.strip())
    submit_disabled = not (employee.strip() and reason.strip() and confirmed and waste_reason_ok)

    with col_cancel:
        if st.button("Abbrechen", use_container_width=True, key="manual_completion_cancel"):
            st.rerun()

    with col_submit:
        if st.button(
            "✅ Einlagern",
            use_container_width=True,
            type="primary",
            disabled=submit_disabled,
            key="manual_completion_submit",
        ):
            try:
                services = st.session_state.get("services", {})
                item_service = services.get("item")
                if not item_service:
                    st.error("❌ Service nicht verfügbar.")
                    return

                item_service.force_complete_item_processing(
                    article_number=article_number,
                    batch_number=batch_number,
                    delivery_number=delivery_number,
                    employee=employee.strip(),
                    reason=reason.strip(),
                    waste_quantity=int(waste_quantity),
                    waste_reason=waste_reason.strip() if waste_reason else None,
                )

                success_msg = (
                    f"✅ Artikel **{article_number}** (Charge {batch_number}) "
                    f"wurde erfolgreich eingelagert."
                )
                if waste_quantity > 0:
                    success_msg += f" | Ausschuss erfasst: **{waste_quantity} Stk.**"
                st.success(success_msg)
                st.rerun()

            except Exception as e:
                logger.error("Fehler beim manuellen Einlagern: %s", e)
                st.error(f"❌ Fehler beim Einlagern: {e}")
