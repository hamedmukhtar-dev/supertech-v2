import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from database.users import get_all_users
from core.pipelines.behavior_tracker import track
from core.pipelines.ai_enricher import enrich_behavior_log

init_app()
protect_page("staff")
navbar()

track("open_staff_dashboard")

st.title("🧑‍💼 Staff Dashboard – Smart CRM + AI")

users = get_all_users()
st.subheader("👥 Registered Users (CRM)")
st.table(users)

st.subheader("🧠 System Behavior Intelligence")
logs = st.session_state.get("behavior_log", [])
if st.button("Run AI Behavior Analysis", key="04_Staff_Dashboard_button_92c63e"):
    st.write(enrich_behavior_log(logs))