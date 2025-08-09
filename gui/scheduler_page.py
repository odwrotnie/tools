from __future__ import annotations

from typing import Dict, List

import streamlit as st


initial = {
        "2025-08-01": 0,
        "2025-08-02": 0,
        "2025-08-03": 0,
        "2025-08-04": 0,
        "2025-08-05": 0,
        "2025-08-06": 0,
        "2025-08-07": 0,
        "2025-08-08": 0,
        "2025-08-09": 0,
        "2025-08-10": 0,
        "2025-08-11": 0,
        "2025-08-12": 0,
        "2025-08-13": 0,
        "2025-08-14": 0,
        "2025-08-15": 0,
        "2025-08-16": 0,
        "2025-08-17": 0,
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

