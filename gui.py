from __future__ import annotations

from typing import List, Optional

import streamlit as st

from mail import check_email_sync  # local module: mail.py
from phone import check_phone_sync  # local module: phone.py


def render_results(title: str, data: List[dict]) -> None:
    st.subheader(title)
    if not data:
        st.info("Brak wyników")
        return
    st.json(data)


def main() -> None:
    st.set_page_config(page_title="OSINT: phone/email", page_icon="🔎", layout="centered")
    st.title("OSINT checker: phone / email")
    st.caption("Wykorzystuje biblioteki ignorant i holehe")

    tabs = st.tabs(["Telefon", "Email"])

    with tabs[0]:
        st.header("Telefon")
        cc = st.text_input("Kod kraju (np. 48)", value="48")
        phone = st.text_input("Numer telefonu", value="")
        if st.button("Sprawdź telefon", type="primary"):
            if not cc.strip() or not phone.strip():
                st.error("Podaj kod kraju i numer telefonu")
            else:
                try:
                    with st.spinner("Sprawdzam telefon…"):
                        results = check_phone_sync(cc.strip(), phone.strip(), None)
                    render_results("Wyniki (telefon)", results)
                except Exception as exc:
                    st.error(f"Błąd: {exc}")

    with tabs[1]:
        st.header("Email")
        email_val = st.text_input("Adres e-mail", value="")
        if st.button("Sprawdź email", type="primary"):
            if not email_val.strip():
                st.error("Podaj adres e-mail")
            else:
                try:
                    with st.spinner("Sprawdzam e-mail…"):
                        results = check_email_sync(email_val.strip(), None)
                    render_results("Wyniki (email)", results)
                except Exception as exc:
                    st.error(f"Błąd: {exc}")


if __name__ == "__main__":
    main()


