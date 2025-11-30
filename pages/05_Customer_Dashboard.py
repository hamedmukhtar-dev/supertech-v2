import streamlit as st
from core.app_controller import init_app, navbar, protect_page

init_app()
protect_page("customer")
navbar()

st.title("👤 Customer Dashboard")

st.success("Welcome to HUMAIN Lifestyle! Enjoy your smart experience 🌍✨")
