import streamlit as st
from core.app_controller import init_app, navbar
from core.ai_engine import ai_insights

init_app()
navbar()

st.title("📊 AI Business Reports")

query = st.text_area("Enter your business question:", key="06_AI_REPORTS_ENTER_YOUR_BUSINESS__0caec0")
if st.button("Generate AI Report"):
    st.write(ai_insights(query))