import streamlit as st
from core.app_controller import init_app, navbar
from utils.language_detector import detect_language_from_ip
from utils.i18n import t
from database.users import add_user
from database.users import init_users

init_app()
init_users()
navbar()

lang = st.session_state.get("lang", "en")

st.title("📝 " + ("Register" if lang == "en" else "تسجيل حساب"))

email = st.text_input("Email", key="pages_02_Register_EMAIL_50fa82")
country = st.text_input("Country", key="pages_02_Register_COUNTRY_21804b")
ip = st.text_input("IP Address (auto-filled)", value=st.session_state.get("ip", ""), key="pages_02_Register_IP_1d3b18")
auto_lang = detect_language_from_ip()

if st.button(t(lang, "continue"), use_container_width=True):
    role = "staff" if email.endswith("@daral-sd.com") else "customer"
    add_user(email, role, country, ip, auto_lang)
    st.success("Account created!")
    st.switch_page("03_Login.py")