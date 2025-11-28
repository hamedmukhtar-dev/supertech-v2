import streamlit as st
from core.app_controller import init_app, navbar
from core.monitoring.ai_monitor import ai_healthcheck, ai_usage_summary

init_app()
navbar()

st.title("🧠 AI Monitoring Center")

st.subheader("AI Health Check")
st.write(ai_healthcheck())

st.subheader("AI Usage Summary")
logs = ["login", "profile", "fraud_check"]
st.write(ai_usage_summary(logs))