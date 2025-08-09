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


def _rows_for_days(days_map: Dict[str, int]) -> List[dict]:
    rows: List[dict] = []
    for day in sorted(days_map.keys()):
        rows.append({"data": day, "wartość": days_map[day]})
    return rows


def render_scheduler_tab() -> None:
    st.header("Scheduler")

    if not preferences:
        st.info("Brak preferencji do wyświetlenia")
        return

    for idx, (person, days) in enumerate(preferences.items()):
        st.subheader(person)
        rows = _rows_for_days(days)
        st.table(rows)
        if idx < len(preferences) - 1:
            st.divider()

