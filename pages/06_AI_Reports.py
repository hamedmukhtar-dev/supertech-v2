import streamlit as st
from core.app_controller import init_app, navbar

init_app()
navbar()

st.title("📊 AI Reports")
st.write("AI-driven business insights & analytics dashboard.")
