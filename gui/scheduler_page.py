from __future__ import annotations

from typing import Dict, List
import calendar
from datetime import date

import streamlit as st
from lib.schedule import optimize_schedule
import pandas as pd
import altair as alt
import io


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


def _weekday_pl_name(d: date) -> str:
    names = [
        "poniedziałek",
        "wtorek",
        "środa",
        "czwartek",
        "piątek",
        "sobota",
        "niedziela",
    ]
    return names[d.weekday()]


def _weekday_for_str(day_str: str) -> str:
    try:
        d = date.fromisoformat(day_str)
        return _weekday_pl_name(d)
    except Exception:
        return ""


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

    st.subheader("Preferencje")
    view_mode = st.radio(
        "Widok preferencji",
        options=["Kalendarz", "Lista"],
        horizontal=True,
        index=0,
        key="scheduler_view_mode",
    )

    if not state_prefs:
        st.info("Brak preferencji do wyświetlenia")
        return

    if view_mode == "Lista":
        for idx, (person, days) in enumerate(state_prefs.items()):
            st.subheader(person)

            for day in sorted(days.keys()):
                key = f"sched_{person}_{day}"
                current_val = int(days[day])

                col_label, col_slider = st.columns([1, 5])
                with col_label:
                    st.write(f"{day} ({_weekday_for_str(day)})")
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
    else:
        # Calendar view of sliders — separate calendar per person
        year = int(selected_year)
        month = int(selected_month)
        num_days = calendar.monthrange(year, month)[1]
        first_weekday = calendar.monthrange(year, month)[0]  # Mon=0..Sun=6
        total_cells = first_weekday + num_days
        total_rows = (total_cells + 6) // 7

        for idx, (person, days) in enumerate(state_prefs.items()):
            st.subheader(person)

            # Header row with weekday names
            cols = st.columns(7)
            for i, col in enumerate(cols):
                with col:
                    col.markdown(f"**{['Pn','Wt','Śr','Cz','Pt','So','Nd'][i]}**")

            # Rows of calendar
            for row in range(total_rows):
                cols = st.columns(7)
                for i in range(7):
                    day_index = row * 7 + i
                    day_num = day_index - first_weekday + 1
                    with cols[i]:
                        if 1 <= day_num <= num_days:
                            d_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                            st.markdown(f"**{day_num:02d}**")
                            key = f"sched_{person}_{d_str}"
                            current_val = int(days.get(d_str, 0))
                            new_val: int = st.slider(
                                label=f"{person} {d_str}",
                                min_value=0,
                                max_value=10,
                                value=current_val,
                                step=1,
                                key=key,
                                label_visibility="collapsed",
                            )
                            days[d_str] = int(new_val)
                        else:
                            st.empty()

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
                        color=alt.Color(field="osoba", type="nominal", legend=None),
                        tooltip=["osoba", "dni"],
                    )
                    .properties(width=320, height=320)
                )
                _spacer_left, _center, _right = st.columns([1, 2, 1])
                with _center:
                    st.altair_chart(chart, use_container_width=False)
                with _right:
                    st.markdown("**Dni pracy**")
                    df_sorted = df.sort_values(by=["dni", "osoba"], ascending=[False, True])
                    st.table(df_sorted)

            # Calendar visualization for the selected month
            try:
                year = int(selected_year)
                month = int(selected_month)
                num_days = calendar.monthrange(year, month)[1]
                first_weekday = calendar.monthrange(year, month)[0]  # Mon=0..Sun=6

                cal_rows = []
                for day_num in range(1, num_days + 1):
                    d_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                    assigned = assignments.get(d_str)
                    dow = (first_weekday + (day_num - 1)) % 7
                    week_idx = (first_weekday + (day_num - 1)) // 7
                    cal_rows.append(
                        {
                            "day": d_str,
                            "day_num": day_num,
                            "weekday": dow,  # 0..6, Pon..Nd
                            "week": week_idx,
                            "osoba": assigned or "—",
                        }
                    )

                df_cal = pd.DataFrame(cal_rows)
                # Base calendar grid
                base = (
                    alt.Chart(df_cal)
                    .mark_rect(stroke="lightgray")
                    .encode(
                        x=alt.X("weekday:O", title=None, axis=alt.Axis(labels=True, values=[0,1,2,3,4,5,6], labelExpr='{"0":"Pn","1":"Wt","2":"Śr","3":"Cz","4":"Pt","5":"So","6":"Nd"}[datum]')),
                        y=alt.Y("week:O", title=None, sort="ascending"),
                        color=alt.Color("osoba:N", title="Osoba"),
                        tooltip=["day", "osoba"],
                    )
                )

                # Overlay person name in the cell
                text = (
                    alt.Chart(df_cal)
                    .mark_text(baseline="middle", fontSize=11, color="black")
                    .encode(
                        x="weekday:O",
                        y="week:O",
                        text=alt.Text("osoba:N"),
                    )
                )

                st.altair_chart(base + text, use_container_width=True)
                
                # Export to Excel
                try:
                    sched_rows = []
                    for d, p in sorted(assignments.items()):
                        try:
                            day_dt = date.fromisoformat(d)
                            weekday_name = _weekday_pl_name(day_dt)
                        except Exception:
                            weekday_name = ""
                        sched_rows.append({"data": d, "dzien_tyg": weekday_name, "osoba": p})
                    sched_df = pd.DataFrame(sched_rows)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        sched_df.to_excel(writer, index=False, sheet_name="Harmonogram")
                        # Optional summary sheet
                        sum_df = (
                            sched_df.groupby("osoba").size().reset_index(name="dni").sort_values(["dni","osoba"], ascending=[False, True])
                        )
                        sum_df.to_excel(writer, index=False, sheet_name="Podsumowanie")
                    output.seek(0)

                    st.download_button(
                        label="Pobierz harmonogram (Excel)",
                        data=output,
                        file_name=f"harmonogram_{year:04d}_{month:02d}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except Exception as export_exc:
                    st.warning(f"Eksport do Excela nie jest dostępny: {export_exc}. Oferuję CSV.")
                    # Fallback CSV
                    try:
                        csv_bytes = sched_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="Pobierz harmonogram (CSV)",
                            data=csv_bytes,
                            file_name=f"harmonogram_{year:04d}_{month:02d}.csv",
                            mime="text/csv",
                        )
                    except Exception:
                        pass
            except Exception as cal_exc:
                st.warning(f"Nie udało się narysować kalendarza: {cal_exc}")
        except Exception as exc:
            st.error(f"Błąd optymalizacji: {exc}")

