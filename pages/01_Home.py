import streamlit as st
from utils.i18n import t

st.set_page_config(
    page_title="HUMAIN Lifestyle | Home",
    layout="wide"
)

lang = st.session_state.get("lang", "en")

# Main UI Title
st.title(t(lang, "welcome_title"))

# Dynamic welcome text
if lang == "en":
    st.write("""
Welcome to **HUMAIN Lifestyle** — your gateway to travel, lifestyle,
and digital services in the Kingdom of Saudi Arabia.
This Home Page will soon include full navigation, dashboards, and AI services.
""")
else:
    st.write("""
مرحباً بك في **HUMAIN Lifestyle** — بوابتك للسفر، أسلوب الحياة،
والخدمات الرقمية داخل المملكة العربية السعودية.
سيتم إضافة لوحة التحكم والانتقال والخدمات الذكية قريباً.
""")
