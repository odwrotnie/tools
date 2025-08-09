from __future__ import annotations

from typing import Dict, List

import streamlit as st
from lib.schedule import optimize_schedule


initial = {
        "2025-08-01": 1,
        "2025-08-02": 1,
        "2025-08-03": 1,
        "2025-08-04": 1,
        "2025-08-05": 1,
        "2025-08-06": 1,
        "2025-08-07": 1,
        "2025-08-08": 1,
        "2025-08-09": 1,
        "2025-08-10": 1,
        "2025-08-11": 1,
        "2025-08-12": 1,
        "2025-08-13": 1,
        "2025-08-14": 1,
        "2025-08-15": 1,
        "2025-08-16": 1,
        "2025-08-17": 1,
    }

preferences = {
    "pawel": initial.copy(),
    "michal": initial.copy(),
    "kasia": initial.copy(),
    "aga": initial.copy(),
}


def _ensure_state_initialized() -> None:
    if "scheduler_preferences" not in st.session_state:
        st.session_state["scheduler_preferences"] = {
            person: {day: int(val) for day, val in days.items()}
            for person, days in preferences.items()
        }


def render_scheduler_tab() -> None:
    st.header("Scheduler")

    _ensure_state_initialized()
    state_prefs: Dict[str, Dict[str, int]] = st.session_state["scheduler_preferences"]

    if not state_prefs:
        st.info("Brak preferencji do wyświetlenia")
        return

    for idx, (person, days) in enumerate(state_prefs.items()):
        st.subheader(person)

        for day in sorted(days.keys()):
            key = f"sched_{person}_{day}"
            current_val = int(days[day])

            col_label, col_slider = st.columns([1, 5])
            with col_label:
                st.write(day)
            with col_slider:
                new_val: int = st.slider(
                    label=f"Wartość dla {person} {day}",
                    min_value=0,
                    max_value=10,
                    value=current_val,
                    step=1,
                    key=key,
                    label_visibility="collapsed",
                )
            days[day] = int(new_val)

        if idx < len(state_prefs) - 1:
            st.divider()

    st.markdown("")
    if st.button("Optymalizuj harmonogram", type="primary"):
        try:
            with st.spinner("Optymalizuję z użyciem OR-Tools…"):
                assignments, total = optimize_schedule(state_prefs)
            st.success(f"Gotowe. Łączny wynik preferencji: {total}")
            # Show results as a simple table day -> person
            rows = [{"dzień": d, "osoba": p} for d, p in sorted(assignments.items())]
            st.table(rows)
        except Exception as exc:
            st.error(f"Błąd optymalizacji: {exc}")

