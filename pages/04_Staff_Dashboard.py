import streamlit as st
from utils.i18n import t

st.set_page_config(page_title="Staff Dashboard | HUMAIN Lifestyle", layout="wide")

lang = st.session_state.get("lang", "en")

if st.session_state.get("user_role") != "staff":
    st.error("Access denied")
    st.stop()

st.title("Staff Dashboard")

st.write("""
Welcome staff member.  
Here you can access:
- Daily operations reports  
- Customer analytics  
- AI system monitoring  
""")
