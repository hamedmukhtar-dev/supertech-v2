import streamlit as st
from core.app_controller import init_app, navbar
from utils.i18n import t

init_app()
navbar()
lang = st.session_state.get("lang", "en")

st.title(t(lang, "welcome_title"))
st.write("Welcome to HUMAIN Lifestyle — Pro Edition.")
