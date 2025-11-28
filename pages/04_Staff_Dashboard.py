import streamlit as st
from core.app_controller import init_app, navbar, protect_page

init_app()
protect_page("staff")
navbar()

st.title("🧑‍💼 Staff Dashboard")
st.write("Advanced daily reports & internal operations panel.")
