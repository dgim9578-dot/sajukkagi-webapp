"""오행별 ``data-theme`` CSS 변수 주입 (Streamlit)."""

from __future__ import annotations

import json

import streamlit as st


def inject_element_theme_styles() -> None:
    """전역 CSS: ``[data-theme=wood|fire|...]`` 변수."""
    if st.session_state.get("_saju_element_theme_css"):
        return
    import saju_storage as storage

    css = storage.element_theme_css_block()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.session_state._saju_element_theme_css = True


def apply_element_data_theme(element_or_slug: str) -> None:
    """``.stApp`` 에 ``data-theme`` 슬러그 적용 (wood/fire/earth/metal/water)."""
    import saju_storage as storage

    slug = storage.element_theme_slug(element_or_slug)
    st.session_state.saju_element_theme_slug = slug
    inject_element_theme_styles()
    payload = json.dumps(slug, ensure_ascii=False)
    st.markdown(
        f"""
<script>
(function() {{
  const slug = {payload};
  const app = window.parent.document.querySelector(".stApp")
    || document.querySelector(".stApp");
  if (app) app.setAttribute("data-theme", slug);
}})();
</script>
""",
        unsafe_allow_html=True,
    )
