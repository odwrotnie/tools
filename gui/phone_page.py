from __future__ import annotations

from typing import List

import streamlit as st

from phone import check_phone_sync
from .shared import render_results


def render_phone_tab() -> None:
    st.header("Telefon")
    cc = st.text_input("Kod kraju (np. 48)", value="48")
    phone = st.text_input("Numer telefonu", value="")
    if st.button("Sprawdź telefon", type="primary"):
        if not cc.strip() or not phone.strip():
            st.error("Podaj kod kraju i numer telefonu")
        else:
            try:
                with st.spinner("Sprawdzam telefon…"):
                    results: List[dict] = check_phone_sync(cc.strip(), phone.strip(), None)
                render_results("Wyniki (telefon)", results)
            except Exception as exc:
                st.error(f"Błąd: {exc}")


