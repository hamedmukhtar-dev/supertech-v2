import streamlit as st

def init_app():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "role" not in st.session_state:
        st.session_state.role = None
    if "email" not in st.session_state:
        st.session_state.email = None

    st.set_page_config(page_title="HUMAIN Lifestyle", layout="wide")

def protect_page(required_role=None):
    if not st.session_state.get("logged_in"):
        st.error("🚫 Please login first.")
        st.switch_page("pages/03_Login.py")

    role = st.session_state.get("role", None)
    if required_role and role != required_role:
        st.error("🚫 Access Denied (Staff Only)")
        st.switch_page("pages/03_Login.py")

def logout_user():
    st.session_state.clear()
    st.switch_page("pages/01_Home.py")

def navbar():
    st.sidebar.markdown(
        """
        <h1 style='color:#D4AF37;text-align:center;'>⚜ HUMAIN ⚜</h1>
        <hr style='border:1px solid #D4AF37;'>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.page_link("pages/01_Home.py", label="🏠 Home")

    if not st.session_state.get("logged_in"):
        st.sidebar.page_link("pages/03_Login.py", label="🔐 Login")
        st.sidebar.page_link("pages/02_Register.py", label="📝 Register")
    else:
        role = st.session_state.get("role")
        if role == "staff":
            st.sidebar.page_link("pages/04_Staff_Dashboard.py", label="🧑‍💼 Staff Dashboard")
            st.sidebar.page_link("pages/08_Live_Analytics.py", label="📊 Live Analytics")
            st.sidebar.page_link("pages/09_AI_Monitoring.py", label="🧠 AI Monitoring")
            st.sidebar.page_link("pages/10_Financial_Core.py", label="💰 Financial Core")
            st.sidebar.page_link("pages/11_Payment_Hub.py", label="💳 Payment Hub")
            st.sidebar.page_link("pages/12_Travel_Simulation.py", label="✈ Travel Simulation")
            st.sidebar.page_link("pages/13_Security_Center.py", label="🔒 Security Center")

        st.sidebar.page_link("pages/05_Customer_Dashboard.py", label="👤 Customer Dashboard")
        st.sidebar.page_link("pages/06_AI_Reports.py", label="📈 AI Reports")

        if st.sidebar.button("🚪 Logout"):
            logout_user()
