### ⬇️ PART 1 START

import streamlit as st
from pathlib import Path
from PIL import Image
from layout_header import render_header
from layout_footer import render_footer
from auth_i18n import show_auth_ui
import sqlite3
import os

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(
    page_title="HUMAIN Lifestyle ✈️",
    page_icon="🌍",
    layout="wide",
)

# ----------------------------
# Global Variables & Assets
# ----------------------------
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

# ----------------------------
# Language Selector
# ----------------------------
lang = st.sidebar.selectbox("🌐 Select Language", ["English", "العربية"])
_ = lambda x: x if lang == "English" else {
    "Welcome": "مرحبًا",
    "Login": "تسجيل الدخول",
    "Signup": "تسجيل",
    "Home": "الرئيسية",
    "Trip Planner": "مخطط الرحلات",
    "Experiences": "الأنشطة والتجارب",
    "Saved": "المحفوظات",
    "Booking Requests": "طلبات الحجز",
    "AI Assistant": "المساعد الذكي",
    "About": "حول",
    "Contact": "اتصل بنا",
    "Join Pilot Program": "انضم للنسخة التجريبية",
}.get(x, x)

### ⬆️ PART 1 END
### ⬇️ PART 2 START

# ----------------------------
# Database Setup
# ----------------------------
DB_PATH = "humain_lifestyle.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pilot_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            role TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Pilot Signup Form
# ----------------------------
def show_pilot_signup_form():
    st.subheader(_("Join Pilot Program"))
    with st.form("pilot_signup"):
        name = st.text_input(_("Full Name"))
        email = st.text_input(_("Email"))
        phone = st.text_input(_("Phone Number"))
        role = st.selectbox(_("User Type"), ["Traveler", "Student", "Business", "Professional", "Parent", "Other"])
        notes = st.text_area(_("Notes / What do you expect?"))
        submitted = st.form_submit_button(_("Submit"))
        if submitted:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO pilot_signups (name, email, phone, role, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, phone, role, notes))
            conn.commit()
            conn.close()
            st.success(_("Thanks for joining the pilot! We’ll contact you soon."))

### ⬆️ PART 2 END
### ⬇️ PART 3 START

# ----------------------------
# Footer Component
# ----------------------------
from layout_footer import render_footer
from layout_header import render_header

# ----------------------------
# Multi-language Setup
# ----------------------------
def set_language():
    lang = st.sidebar.selectbox("🌐 Language / اللغة", ["English", "العربية"])
    if lang == "العربية":
        st.session_state.lang = "ar"
        return "ar"
    else:
        st.session_state.lang = "en"
        return "en"

language = set_language()
locales = {
    "en": {
        "Join Pilot Program": "Join Pilot Program",
        "Full Name": "Full Name",
        "Email": "Email",
        "Phone Number": "Phone Number",
        "User Type": "User Type",
        "Notes / What do you expect?": "Notes / What do you expect?",
        "Submit": "Submit",
        "Thanks for joining the pilot! We’ll contact you soon.": "Thanks for joining the pilot! We’ll contact you soon."
    },
    "ar": {
        "Join Pilot Program": "انضم إلى البرنامج التجريبي",
        "Full Name": "الاسم الكامل",
        "Email": "البريد الإلكتروني",
        "Phone Number": "رقم الهاتف",
        "User Type": "نوع المستخدم",
        "Notes / What do you expect?": "ملاحظات / ماذا تتوقع؟",
        "Submit": "إرسال",
        "Thanks for joining the pilot! We’ll contact you soon.": "شكرًا لانضمامك للبرنامج التجريبي! سنتواصل معك قريبًا."
    }
}
def _(text):
    return locales[language].get(text, text)

### ⬆️ PART 3 END
### ⬇️ PART 4 START

# ----------------------------
# Main Interface
# ----------------------------

st.title("🌍 HUMAIN Lifestyle")
st.caption("by DAR AL KHARTOUM TRAVEL & TOURISM CO. LTD")
render_header()

# Show pilot form on homepage
def show_pilot_form():
    st.subheader(_(f"Join Pilot Program"))
    with st.form("pilot_signup_form"):
        full_name = st.text_input(_(f"Full Name"))
        email = st.text_input(_(f"Email"))
        phone = st.text_input(_(f"Phone Number"))
        user_type = st.selectbox(_(f"User Type"), ["Traveler", "Student", "Business", "Health", "Other"])
        notes = st.text_area(_(f"Notes / What do you expect?"))

        submitted = st.form_submit_button(_(f"Submit"))
        if submitted:
            insert_pilot_user(full_name, email, phone, user_type, notes)
            st.success(_(f"Thanks for joining the pilot! We’ll contact you soon."))

show_pilot_form()

# ----------------------------
# Footer
# ----------------------------
render_footer()

### ⬆️ PART 4 END
### ⬇️ PART 5 START

# ----------------------------
# AI General Assistant (Optional - For Future Expansion)
# ----------------------------

def ai_general_assistant():
    st.markdown("---")
    st.subheader(_(f"💬 General Assistant (Coming Soon)"))
    st.info(_(f"We’re working on integrating an AI assistant to answer your travel, lifestyle, and business inquiries. Stay tuned!"))

# ----------------------------
# Booking Requests View (Simple CRM)
# ----------------------------

def show_booking_requests():
    st.markdown("---")
    st.subheader(_(f"📋 Booking Requests Log"))

    requests = get_all_booking_requests()
    if not requests:
        st.info(_(f"No booking requests found yet."))
        return

    for req in requests:
        st.markdown(f"""
        **🧑 Name:** {req[1]}  
        **📧 Email:** {req[2]}  
        **📱 Phone:** {req[3]}  
        **📍 Destination:** {req[4]}  
        **🗓️ Date:** {req[5]}  
        **📝 Notes:** {req[6]}  
        ---
        """)

# Optional future AI panel
# ai_general_assistant()
# show_booking_requests()

### ⬆️ PART 5 END
### ⬇️ PART 6 START

# ----------------------------
# Language Toggle Button (Arabic / English)
# ----------------------------

def language_switcher():
    lang = st.sidebar.radio("🌐 Select Language / اختر اللغة", ("English", "العربية"))
    st.session_state.lang = 'ar' if lang == "العربية" else 'en'

# ----------------------------
# App Main View Routing
# ----------------------------

def main():
    st.set_page_config(page_title="HUMAIN Lifestyle | DAR AL KHARTOUM", layout="wide")
    language_switcher()

    render_header()

    st.markdown("## 👋 Welcome to HUMAIN Lifestyle Portal")
    st.write(_("""
    Discover smart travel, fintech, wellness, and lifestyle services designed for the modern Arab and African traveler.
    """))

    tab = st.sidebar.selectbox(
        _(f"Choose View"),
        options=[
            _(f"🏠 Home"),
            _(f"📝 Pilot Signup"),
            _(f"📋 Booking Requests Log"),
            _(f"⚙️ Settings"),
        ]
    )

    if tab == _(f"🏠 Home"):
        show_home()
    elif tab == _(f"📝 Pilot Signup"):
        pilot_signup_form()
    elif tab == _(f"📋 Booking Requests Log"):
        show_booking_requests()
    elif tab == _(f"⚙️ Settings"):
        st.warning(_(f"Settings coming soon!"))

    render_footer()

### ⬆️ PART 6 END
### ⬇️ PART 7 START

# ----------------------------
# Launch App
# ----------------------------

if __name__ == "__main__":
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    main()

### ⬆️ PART 7 END
