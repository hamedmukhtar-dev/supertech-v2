import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from database.users import get_all_users
from core.pipelines.user_profile_pipeline import generate_ai_profile
from core.pipelines.behavior_tracker import track

init_app()
protect_page("customer")
navbar()

track("open_ai_profile")

st.title("🧠 My AI Profile")

user_email = st.session_state.get("user_email", "unknown@example.com")

profile = generate_ai_profile(f"User email: {user_email}")
st.write(profile)

st.subheader("📈 Activity Log")
logs = st.session_state.get("behavior_log", [])
st.json(logs)