import streamlit as st
from core.app_controller import init_app, navbar
from core.ai_engine import ai_insights

init_app()
navbar()

st.title("📊 AI Business Reports")

query = st.text_area("Enter your business question:")
if st.button("Generate AI Report"):
    st.write(ai_insights(query))