import streamlit as st
from utils.i18n import t

st.set_page_config(
    page_title="HUMAIN Lifestyle | Home",
    layout="wide"
)

lang = st.session_state.get("lang", "en")

# Main UI
st.title(t(lang, "welcome_title"))

st.write("""
Welcome to HUMAIN Lifestyle — Your gateway to travel, lifestyle, 
and digital services. This page will be expanded with navigation 
and dashboard features.
""" if lang == "en" else """
مرحباً بك في HUMAIN Lifestyle — بوابتك للسفر ونمط الحياة 
والخدمات الرقمية. سيتم توسيع هذه الصفحة لاحقاً مع لوحات التحكم.
""")