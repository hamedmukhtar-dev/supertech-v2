import streamlit as st
from utils.i18n import t

st.set_page_config(page_title="Login | HUMAIN Lifestyle", layout="centered")

lang = st.session_state.get("lang", "en")

st.title(t(lang, "login"))

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button(t(lang, "continue"), use_container_width=True):
    if email.endswith("@daral-sd.com"):
        st.session_state["user_role"] = "staff"
        st.switch_page("04_Staff_Dashboard.py")
    else:
        st.session_state["user_role"] = "customer"
        st.switch_page("05_Customer_Dashboard.py")
