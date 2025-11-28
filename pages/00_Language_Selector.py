import streamlit as st
from pathlib import Path
from PIL import Image
from utils.language_detector import detect_language_from_ip
from utils.i18n import t

st.set_page_config(
    page_title="Choose Language | HUMAIN Lifestyle",
    layout="centered"
)

# Auto-detect language on first visit
if "lang" not in st.session_state:
    st.session_state.lang = detect_language_from_ip()

lang = st.session_state.get("lang", "en")

# Load logo
ASSETS_PATH = Path("assets")
LOGO_PATH = ASSETS_PATH / "daral_logo.png"
logo = Image.open(LOGO_PATH) if LOGO_PATH.exists() else None

# UI Layout
st.markdown(
    f"<h2 style='text-align:center; font-size:32px;'>🌍 HUMAIN Lifestyle</h2>",
    unsafe_allow_html=True
)

if logo:
    st.image(logo, width=230)

st.markdown(
    f"<h3 style='text-align:center; color:#444;'>{t(lang, 'language_selector_title')}</h3>",
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    if st.button("🇸🇦 العربية", use_container_width=True):
        st.session_state.lang = "ar"
        st.switch_page("01_Home.py")

with col2:
    if st.button("🇬🇧 English", use_container_width=True):
        st.session_state.lang = "en"
        st.switch_page("01_Home.py")
