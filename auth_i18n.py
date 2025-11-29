# (portion of file where language selector in sidebar is defined)
import streamlit as st

# ... other imports and functions above ...

with st.sidebar:
    st.markdown("### 🌐 " + t("اللغة", "Language"))
    lang = st.selectbox(
        "Language | اللغة",
        options=list(LANGS.keys()),
        format_func=lambda k: LANGS[k],
        index=0 if get_lang() == "ar" else 1,
        key="AUTH_LANG_SELECTBOX",
    )
    set_lang(lang)

# Note: keep the rest of auth_i18n logic unchanged
