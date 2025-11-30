import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from database.users import get_all_users
from utils.i18n import t

# 🧑‍💼 Staff فقط
init_app()
protect_page("staff")
navbar()

st.title("🧑‍💼 Staff Dashboard — Operations Center")

email = st.session_state.get("email", "")
st.success(f"Welcome Admin: {email}")

st.subheader("📊 Registered Users")
rows = get_all_users()

if not rows:
    st.info("No registered users yet.")
else:
    st.dataframe(rows, use_container_width=True)
