import streamlit as st
from utils.i18n import t

def init_app():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "user_role" not in st.session_state:
        st.session_state.user_role = None

def set_language(lang):
    st.session_state.lang = lang

def login_user(email):
    if email.endswith("@daral-sd.com"):
        st.session_state.user_role = "staff"
    else:
        st.session_state.user_role = "customer"

def logout_user():
    st.session_state.user_role = None

def protect_page(role=None):
    if role and st.session_state.get("user_role") != role:
        st.error("🚫 Access denied")
        st.stop()

def navbar():
    st.markdown(
        """
        <style>
        .nav-container {
            background:#111; padding:14px; border-radius:10px;
            margin-bottom:20px;
        }
        .nav-item { margin-right:25px; display:inline; font-size:18px; }
        a { text-decoration:none; color:#FFF; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='nav-container'>
            <span class='nav-item'><a href='/'>🏠 Home</a></span>
            <span class='nav-item'><a href='Login'>🔐 Login</a></span>
            <span class='nav-item'><a href='Customer Dashboard'>👤 Customer</a></span>
            <span class='nav-item'><a href='Staff Dashboard'>🧑‍💼 Staff</a></span>
            <span class='nav-item'><a href='AI Reports'>📊 AI Reports</a></span>
            <span class='nav-item'><a href='Logout'>🚪 Logout</a></span>
        </div>
        """,
        unsafe_allow_html=True
    )
