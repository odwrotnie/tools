from __future__ import annotations

from typing import List

import streamlit as st

from mail import check_email_sync
from .shared import render_email_cards


def render_email_tab() -> None:
    st.header("Email")
    email_val = st.text_input("Adres e-mail", value="")
    if st.button("Sprawdź email", type="primary"):
        if not email_val.strip():
            st.error("Podaj adres e-mail")
        else:
            try:
                with st.spinner("Sprawdzam e-mail…"):
                    results: List[dict] = check_email_sync(email_val.strip(), None)
                render_email_cards(results)
            except Exception as exc:
                st.error(f"Błąd: {exc}")


