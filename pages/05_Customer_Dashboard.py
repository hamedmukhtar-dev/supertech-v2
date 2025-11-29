import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from core.pipelines.user_profile_pipeline import generate_ai_profile
from core.pipelines.behavior_tracker import track
from core.pipelines.ai_enricher import enrich_behavior_log

init_app()
protect_page("customer")
navbar()

track("open_customer_dashboard")

st.title("👤 My AI Assistant")

prompt = st.text_area("Ask your personalized AI assistant:", key="05_CUSTOMER_DASHBOARD_ASK_YOUR_PERSONALIZE_c2c603")

if st.button("Ask AI"):
    response = generate_ai_profile(prompt)
    st.write(response)

st.subheader("🔍 AI Behavior Analysis")
if st.button("Analyze My Behavior Log"):
    logs = st.session_state.get("behavior_log", [])
    st.write(enrich_behavior_log(logs))