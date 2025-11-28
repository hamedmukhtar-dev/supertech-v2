import streamlit as st
from core.app_controller import logout_user

logout_user()
st.success("You are logged out.")
st.switch_page("01_Home.py")
