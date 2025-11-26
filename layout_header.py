import streamlit as st

def render_header():
    header_style = """
        <style>
            .humain-header {
                background:linear-gradient(90deg,#006C35,#004D24);
                color:white;
                text-align:center;
                padding:25px;
                border-bottom:4px solid #D4AF37;
                box-shadow:0 4px 15px rgba(0,0,0,0.18);
                border-radius:0 0 14px 14px;
            }
            .humain-header h1 {
                font-size:2.2rem;
                font-weight:800;
                margin:0;
            }
            .humain-header p {
                font-size:1rem;
                opacity:.95;
            }
        </style>
    """

    st.markdown(header_style, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="humain-header">
            <h1>🌍 HUMAIN Lifestyle</h1>
            <p>Your Gateway to The Kingdom of Saudi Arabia 🇸🇦</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
