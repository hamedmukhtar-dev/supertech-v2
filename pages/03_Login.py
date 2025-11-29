import streamlit as st
from core.app_controller import init_app, navbar, login_user
from utils.i18n import t

init_app()
navbar()

lang = st.session_state.get("lang", "en")
st.title("🔐 " + t(lang, "login"))

email = st.text_input("Email", key="pages_03_Login_EMAIL_07dbc3")
password = st.text_input("Password", type="password", key="pages_03_Login_PASSWORD_a49e4d")

if st.button(t(lang, "continue"), use_container_width=True):
    login_user(email)
    if st.session_state.user_role == "staff":
        st.switch_page("04_Staff_Dashboard.py")
    else:
        st.switch_page("05_Customer_Dashboard.py")
