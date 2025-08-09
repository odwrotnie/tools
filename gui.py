from __future__ import annotations

import streamlit as st

from gui.phone_page import render_phone_tab
from gui.email_page import render_email_tab


def main() -> None:
    st.set_page_config(page_title="OSINT: phone/email", page_icon="🔎", layout="centered")
    st.title("OSINT checker: phone / email")
    st.caption("Wykorzystuje biblioteki ignorant i holehe")

    tabs = st.tabs(["Telefon", "Email"])

    with tabs[0]:
        render_phone_tab()

    with tabs[1]:
        render_email_tab()


if __name__ == "__main__":
    main()


