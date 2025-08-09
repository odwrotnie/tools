from __future__ import annotations

from typing import Dict, List
import calendar
from datetime import date

import streamlit as st
from lib.schedule import optimize_schedule
import pandas as pd
import altair as alt


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

DEFAULT_PEOPLE: List[str] = ["pawel", "michal", "kasia", "aga"]


def _generate_days_for_month(year: int, month: int) -> List[str]:
    num_days = calendar.monthrange(year, month)[1]
    return [f"{year:04d}-{month:02d}-{d:02d}" for d in range(1, num_days + 1)]


def _ensure_people_initialized() -> None:
    if "scheduler_people" not in st.session_state:
        st.session_state["scheduler_people"] = list(preferences.keys()) or DEFAULT_PEOPLE


def _ensure_state_for_month(
    year: int, month: int, default_value: int = 1, force_rebuild: bool = False
) -> None:
    people: List[str] = st.session_state.get("scheduler_people", DEFAULT_PEOPLE)
    month_key = f"{year:04d}-{month:02d}"
    if (
        force_rebuild
        or "scheduler_preferences" not in st.session_state
        or st.session_state.get("scheduler_month_key") != month_key
    ):
        days_list = _generate_days_for_month(year, month)
        st.session_state["scheduler_preferences"] = {
            person: {day: int(default_value) for day in days_list}
            for person in people
        }
        st.session_state["scheduler_month_key"] = month_key
    else:
        # If people list changed, sync preferences without losing current values
        days_list = _generate_days_for_month(year, month)
        current = st.session_state.get("scheduler_preferences", {})
        # Remove missing people
        for person in list(current.keys()):
            if person not in people:
                del current[person]
        # Add new people with defaults
        for person in people:
            if person not in current:
                current[person] = {day: int(default_value) for day in days_list}
        # Ensure all persons have all days (keep existing values where present)
        for person in people:
            person_days = current.get(person, {})
            for day in days_list:
                if day not in person_days:
                    person_days[day] = int(default_value)
            # Optionally drop extra days not in current month
            for day in list(person_days.keys()):
                if day not in days_list:
                    del person_days[day]
        st.session_state["scheduler_preferences"] = current


def render_scheduler_tab() -> None:
    st.header("Scheduler")

    today = date.today()
    col_year, col_month = st.columns([2, 1])
    with col_year:
        selected_year = st.number_input("Rok", value=int(today.year), min_value=2000, max_value=2100, step=1)
    with col_month:
        selected_month = st.selectbox("Miesiąc", options=list(range(1, 13)), index=int(today.month) - 1, format_func=lambda m: f"{m:02d}")

    # People editor
    _ensure_people_initialized()
    current_people: List[str] = st.session_state.get("scheduler_people", DEFAULT_PEOPLE)
    people_text_default = "\n".join(current_people)
    people_text = st.text_area("Osoby (po jednej na linię)", value=people_text_default, height=100, key="scheduler_people_text")
    force_rebuild = False
    if st.button("Zapisz osoby"):
        new_people: List[str] = []
        seen = set()
        for line in people_text.splitlines():
            name = line.strip()
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            new_people.append(name)
        if not new_people:
            st.error("Lista osób nie może być pusta")
        else:
            st.session_state["scheduler_people"] = new_people
            force_rebuild = True

    _ensure_state_for_month(int(selected_year), int(selected_month), force_rebuild=force_rebuild)
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

            # Summary pie chart: who works how many days
            counts: Dict[str, int] = {}
            for person in assignments.values():
                counts[person] = counts.get(person, 0) + 1
            if counts:
                df = pd.DataFrame(
                    [{"osoba": person, "dni": days} for person, days in sorted(counts.items())]
                )
                chart = (
                    alt.Chart(df)
                    .mark_arc()
                    .encode(
                        theta=alt.Theta(field="dni", type="quantitative"),
                        color=alt.Color(field="osoba", type="nominal"),
                        tooltip=["osoba", "dni"],
                    )
                    .properties(width=300, height=300)
                )
                st.altair_chart(chart, use_container_width=False)
        except Exception as exc:
            st.error(f"Błąd optymalizacji: {exc}")

