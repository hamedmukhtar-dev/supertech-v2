import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from database.users import get_all_users

init_app()
protect_page("staff")
navbar()

st.title("🧑‍💼 Staff Dashboard – CRM")

users = get_all_users()
if not users:
    st.info("No registered users yet.")
else:
    st.subheader("👥 Registered Users")
    st.table(users)
