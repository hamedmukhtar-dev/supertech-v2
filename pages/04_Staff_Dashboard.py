import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from database.users import get_all_users
from core.ai_engine import ai_daily_summary, ai_detect_fraud

init_app()
protect_page("staff")
navbar()

st.title("🧑‍💼 Staff Dashboard – AI Enhanced")

users = get_all_users()
st.subheader("👥 Registered Users")
st.table(users)

st.subheader("🧠 AI Daily Summary")
logs = str(users)
st.write(ai_daily_summary(logs))

st.subheader("⚠️ AI Fraud Detection")
st.write(ai_detect_fraud(logs))