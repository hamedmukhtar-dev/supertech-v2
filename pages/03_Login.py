import streamlit as st
from core.app_controller import init_app, navbar, login_user
from utils.i18n import t

init_app()
navbar()

lang = st.session_state.get("lang", "en")
st.title("🔐 " + t(lang, "login"))

email = st.text_input("Email", key="03_Login_text_input_3d6320")
password = st.text_input("Password", type="password", key="03_Login_text_input_1438f8")

if st.button(t(lang, "continue"), use_container_width=True, key="03_Login_button_c2ca92"):
    login_user(email)
    if st.session_state.user_role == "staff":
        st.switch_page("04_Staff_Dashboard.py")
    else:
        st.switch_page("05_Customer_Dashboard.py")
