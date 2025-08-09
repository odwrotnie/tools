from __future__ import annotations

from typing import List, Optional
import json

import streamlit as st

from mail import check_email_sync  # local module: mail.py
from phone import check_phone_sync  # local module: phone.py


def render_results(title: str, data: List[dict]) -> None:
    st.subheader(title)
    if not data:
        st.info("Brak wyników")
        return
    st.json(data)


def _filter_exists_not_false(data: List[dict]) -> List[dict]:
    filtered: List[dict] = []
    for item in data:
        exists_val = item.get("exists", None)
        # Odrzuć tylko, gdy to jest dokładnie False lub string 'false'
        if exists_val is False:
            continue
        if isinstance(exists_val, str) and exists_val.strip().lower() == "false":
            continue
        filtered.append(item)
    return filtered


def _normalize_bool_like(value: object) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "1"}:
            return True
        if v in {"false", "no", "0"}:
            return False
    return None


def render_email_cards(data: List[dict]) -> None:
    st.subheader("Wyniki (email)")
    if data is None:
        st.info("Brak wyników")
        return

    filtered = _filter_exists_not_false(data)
    if not filtered:
        st.info("Brak wyników spełniających filtr exists != false")
        return

    # Sortowanie: najpierw wpisy z exists==True
    filtered.sort(key=lambda i: 0 if _normalize_bool_like(i.get("exists")) is True else 1)

    # Jedna kolumna: po jednej karcie w wierszu
    for idx, item in enumerate(filtered):
        name = item.get("name") or "(bez nazwy)"
        domain = item.get("domain") or "(brak domeny)"
        exists_val = item.get("exists", "Unknown")
        method = item.get("method") or "—"
        rate_limit = item.get("rateLimit", "—")
        freq_limit = item.get("frequent_rate_limit", "—")
        error_msg = item.get("error")

        # Tytuł karty
        st.markdown(f"**{name}**\n\n`{domain}`")

        # Status (False odfiltrowany)
        norm_exists = _normalize_bool_like(exists_val)
        if norm_exists is True:
            st.success("Istnieje: TAK")
        elif isinstance(exists_val, str) and exists_val.strip().lower() == "unknown":
            st.warning("Istnieje: NIEZNANE")
        else:
            st.warning("Istnieje: NIEZNANE")

        # Metadane
        meta_lines = [
            f"Metoda: {method}",
            f"Rate limit: {rate_limit}",
            f"Częsty rate limit: {freq_limit}",
        ]
        st.caption(" | ".join(meta_lines))

        if error_msg:
            st.error(f"Błąd: {error_msg}")

        with st.expander("Szczegóły"):
            st.code(json.dumps(item, ensure_ascii=False, indent=2), language="json")

        if idx < len(filtered) - 1:
            st.divider()


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
                    render_email_cards(results)
                except Exception as exc:
                    st.error(f"Błąd: {exc}")


if __name__ == "__main__":
    main()


