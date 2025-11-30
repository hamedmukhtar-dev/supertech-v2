import streamlit as st

def init_app():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "role" not in st.session_state:
        st.session_state.role = None

def protect_page(required_role=None):
    role = st.session_state.get("role", None)
    if required_role and role != required_role:
        st.error("🚫 Access denied")
        st.stop()

def navbar():
    role = st.session_state.get("role", None)

    if role == "staff":
        menu = [
            "Home",
            "Staff Dashboard",
            "AI Reports",
            "Live Analytics",
            "Security Center",
            "Logout",
        ]
    elif role == "customer":
        menu = [
            "Home",
            "Customer Dashboard",
            "Travel Simulation",
            "Logout",
        ]
    else:
        menu = [
            "Home",
            "Register",
            "Login",
        ]

    choice = st.radio("📌 Navigation", menu, horizontal=True)

    # Routing
    if choice == "Home":
        st.switch_page("pages/01_Home.py")
    elif choice == "Login":
        st.switch_page("pages/03_Login.py")
    elif choice == "Register":
        st.switch_page("pages/02_Register.py")
    elif choice == "Staff Dashboard":
        st.switch_page("pages/04_Staff_Dashboard.py")
    elif choice == "Customer Dashboard":
        st.switch_page("pages/05_Customer_Dashboard.py")
    elif choice == "Logout":
        st.session_state.clear()
        st.switch_page("pages/01_Home.py")
