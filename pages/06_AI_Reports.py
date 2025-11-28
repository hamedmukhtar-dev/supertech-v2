import streamlit as st
from core.app_controller import init_app, navbar

init_app()
navbar()

st.title("📊 AI Reports")

prompt = st.text_area("Ask AI for insights:")

if st.button("Generate Report"):
    st.write("AI analysis will appear here...")