from __future__ import annotations

import streamlit as st

from gui.phone_page import render_phone_tab
from gui.email_page import render_email_tab
from gui.scheduler_page import render_scheduler_tab


def main() -> None:
    st.set_page_config(page_title="Rzeczy", page_icon="💩", layout="wide")
    st.title("Rzeczy")
    st.caption("Różne")

    tabs = st.tabs(["Scheduler", "Telefon", "Email"])

    with tabs[0]:
        render_scheduler_tab()

    with tabs[1]:
        render_phone_tab()

    with tabs[2]:
        render_email_tab()


if __name__ == "__main__":
    main()


