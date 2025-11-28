import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from database.users import get_all_users

init_app()
protect_page("staff")
navbar()

st.title("🧑‍💼 Staff Dashboard")

users = get_all_users()

st.subheader("Registered Users:")
st.table(users)