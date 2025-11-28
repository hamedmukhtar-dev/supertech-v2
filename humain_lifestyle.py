import streamlit as st

# استيراد المكتبات والملفات الأخرى
from pathlib import Path
from PIL import Image
from layout_header import render_header
from layout_footer import render_footer
from auth_i18n import show_auth_ui
import sqlite3
import os

# تعريف المتغيرات والموارد
ASSETS_PATH = Path("assets")
LOGO_PATH = ASSETS_PATH / "daral_logo.png"

if LOGO_PATH.exists():
    logo = Image.open(LOGO_PATH)
else:
    logo = None

COMPANY_NAME = "DAR AL KHARTOUM TRAVEL & TOURISM CO. LTD"
CEO_NAME = "Hamed Omer Mukhtar"
EMAIL = "hamed.mukhtar@daral-sd.com"
PHONE = "+201113336672"
WHATSAPP = "+249912399919"
WEBSITE = "www.daral-sd.com"

# اختيار اللغة
lang = st.sidebar.selectbox("🌐 Select Language", ["English", "العربية"])
_ = lambda x: x if lang == "English" else {
    "Welcome": "مرحبًا",
    "Login": "تسجيل الدخول",
    # بقية الترجمات
}.get(x, x)

# الدوال والواجهة الرئيسية
def main():
    render_header()
    # بقية الكود لواجهتك

    render_footer()

if __name__ == "__main__":
    main()