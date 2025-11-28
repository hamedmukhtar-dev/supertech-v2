import streamlit as st
from utils.i18n import t

st.set_page_config(page_title="Customer Dashboard | HUMAIN Lifestyle", layout="wide")

lang = st.session_state.get("lang", "en")

if st.session_state.get("user_role") != "customer":
    st.error("Access denied")
    st.stop()

st.title("Customer Dashboard")

st.write("""
Welcome to your dashboard.  
Here you will be able to:
- View your travel bookings  
- Manage your HUMAIN Lifestyle profile  
- Access personalized AI services  
""")
