import streamlit as st
from core.app_controller import init_app, navbar
from utils.i18n import t

init_app()
navbar()

lang = st.session_state.get("lang", "en")

st.title(t(lang, "welcome_title"))

st.write("Welcome to HUMAIN Lifestyle — AI Powered Edition.")

st.subheader("⚡ Quick Navigation")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/03_Login.py", label="🔐 Login")
with col2:
    st.page_link("pages/02_Register.py", label="📝 Register")
with col3:
    st.page_link("pages/06_AI_Reports.py", label="📊 AI Reports")
with col4:
    st.page_link("pages/05_Customer_Dashboard.py", label="🤖 My AI Assistant")