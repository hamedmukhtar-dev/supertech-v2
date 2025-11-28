import streamlit as st
from core.app_controller import init_app, navbar, protect_page
from core.ai_engine import ai_customer_profile

init_app()
protect_page("customer")
navbar()

st.title("👤 Customer Dashboard")

st.write("Your personalized AI insights and travel services.")

prompt = st.text_area("Ask your personal AI assistant:")
if st.button("Ask AI"):
    st.write(ai_customer_profile(prompt))