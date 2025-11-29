import streamlit as st
import sqlite3
from layout_footer import render_footer
from layout_header import render_header

# ----------------------------
# Ensure session state defaults
# ----------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "ar"

# ----------------------------
# Multi-language Setup
# ----------------------------

def _on_lang_change_sidebar():
    v = st.session_state.get("LANG_SIDEBAR")
    st.session_state["lang"] = "ar" if v == "العربية" else "en"

def set_language():
    # One canonical selector in the sidebar with an explicit key
    st.sidebar.selectbox(
        "🌐 Language / اللغة",
        ["English", "العربية"],
        index=0 if st.session_state.get("lang", "en") == "en" else 1,
        key="LANG_SIDEBAR",
        on_change=_on_lang_change_sidebar,
    )
    return st.session_state["lang"]

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
        full_name = st.text_input(_(f"Full Name"), key="streamlitapp_FULL_NAME_37c217")
        email = st.text_input(_(f"Email"), key="streamlitapp_EMAIL_d1cb3c")
        phone = st.text_input(_(f"Phone Number"), key="streamlitapp_PHONE_NUMBER_cc9b34")
        # Explicit unique key to avoid duplicate element id with other selectboxes
        user_type = st.selectbox(_(f"User Type"), ["Traveler", "Student", "Business", "Health", "Other"], key="pilot_user_type")
        notes = st.text_area(_(f"Notes / What do you expect?"), key="streamlitapp_NOTES_WHAT_3f29b5")
        submitted = st.form_submit_button(_(f"Submit"))
        if submitted:
            conn = sqlite3.connect('data/app.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO pilot_signups (name, email, phone, role, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (full_name, email, phone, user_type, notes))
            conn.commit()
            conn.close()
            st.success(_("Thanks for joining the pilot! We’ll contact you soon."))

# Example usage on the main page
show_pilot_form()
