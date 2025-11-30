import streamlit as st
from pathlib import Path

def render_header(lang="ar"):
    # تحميل الشعار
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        st.image(str(logo_path), width=110)
    else:
        st.write("⚠️ Logo not found")

    # الترجمة
    if lang == "ar":
        title = "منصّة HUMAIN Lifestyle الذكية"
        slogan = "نقدّم حلول سفر وسياحة مبتكرة تجمع بين التقنية الحديثة والخبرة العميقة، لنصنع تجربة سفر آمنة، مريحة، وسلسة للمسافر."
    else:
        title = "HUMAIN Lifestyle Smart Platform"
        slogan = "We provide innovative travel solutions combining technology and deep expertise to deliver a safe, smooth, and modern travel experience."

    # عنوان المنصّة
    st.markdown(
        f"""
        <div style='text-align:right; padding:10px;'>
            <h1 style='color:#0f5b45; margin-bottom:-10px;'>{title}</h1>
            <p style='color:#444;'>{slogan}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # زر اختيار اللغة (unique key to avoid duplicate element id)
    col1, col2 = st.columns([6, 1])
    with col2:
        # Make the selectbox have a stable explicit key and normalize stored language
        lang_sel = st.selectbox("🌐", ["العربية", "English"], index=0, key="LAYOUT_HEADER_LANG")
        # Canonicalize to 'ar' or 'en' (preserve the st.session_state['lang'] key)
        st.session_state['lang'] = 'ar' if lang_sel in ('العربية', 'ar') else 'en'
