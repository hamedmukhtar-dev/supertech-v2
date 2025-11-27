import streamlit as st

def render_footer():
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align:center; font-size:14px; color:#555; padding:20px;'>

            <strong>DAR AL KHARTOUM TRAVEL & TOURISM CO. LTD</strong><br>
            شركة دار الخرطوم للسفر والسياحة المحدودة<br><br>

            <strong>Hamed Omer Mukhtar</strong><br>
            حامد عمر مختار<br><br>

            📞 Phone: +201113336672  
            <br>
            📱 WhatsApp: +249912399919  
            <br>
            📧 Email: <strong>hamed.mukhtar@daral-sd.com</strong><br>
            🌍 Website: <strong>www.daral-sd.com</strong><br><br>

            © 2025 HUMAIN Lifestyle — All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )
