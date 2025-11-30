import streamlit as st
from core.app_controller import init_app, navbar
from database.users import get_user_by_email
from utils.i18n import t

init_app()
navbar()

lang = st.session_state.get("lang", "en")

st.title("🔐 Login")

email = st.text_input("Email", key="login_email")
password = st.text_input("Password", type="password", key="login_pass")

if st.button("Login", use_container_width=True):
    user = get_user_by_email(email)

    if not user:
        st.error("User not found.")
    else:
        st.session_state["logged_in"] = True
        st.session_state["email"] = email
        st.session_state["role"] = user[2]  # "staff" or "customer"

        if user[2] == "staff":
            st.success("Welcome Staff! Redirecting…")
            st.switch_page("pages/04_Staff_Dashboard.py")
        else:
            st.success("Welcome! Redirecting…")
            st.switch_page("pages/05_Customer_Dashboard.py")
