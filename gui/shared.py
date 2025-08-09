from __future__ import annotations

from typing import List, Optional
import json

import streamlit as st


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

    filtered.sort(key=lambda i: 0 if _normalize_bool_like(i.get("exists")) is True else 1)

    for idx, item in enumerate(filtered):
        name = item.get("name") or "(bez nazwy)"
        domain = item.get("domain") or "(brak domeny)"
        exists_val = item.get("exists", "Unknown")
        method = item.get("method") or "—"
        rate_limit = item.get("rateLimit", "—")
        freq_limit = item.get("frequent_rate_limit", "—")
        error_msg = item.get("error")

        st.markdown(f"**{name}**\n\n`{domain}`")

        norm_exists = _normalize_bool_like(exists_val)
        if norm_exists is True:
            st.success("Istnieje: TAK")
        elif isinstance(exists_val, str) and exists_val.strip().lower() == "unknown":
            st.warning("Istnieje: NIEZNANE")
        else:
            st.warning("Istnieje: NIEZNANE")

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


