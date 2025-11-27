# layout_header.py
import base64
from pathlib import Path
import streamlit as st

def _logo_b64():
    p = Path("assets/logo.png")
    if p.exists():
        try:
            return base64.b64encode(p.read_bytes()).decode("utf-8")
        except Exception:
            return None
    return None

def render_header():
    b64 = _logo_b64()
    st.markdown(
        """
<style>
.hdr{
  background:linear-gradient(90deg,#006C35,#004D24);
  color:white; padding:18px 16px; border-bottom:4px solid #D4AF37;
  border-radius:0 0 14px 14px; box-shadow:0 4px 15px rgba(0,0,0,.18);
}
.hdr-wrap{ display:flex; gap:12px; align-items:center; }
.hdr h1{ margin:0; font-size:1.6rem; font-weight:900; letter-spacing:.3px; }
.hdr p{ margin:4px 0 0; opacity:.95; }
.hdr-logo{
  height:44px; width:44px; border-radius:10px; border:1px solid #D4AF37;
  background:white; overflow:hidden; display:flex; align-items:center; justify-content:center;
}
</style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="hdr"><div class="hdr-wrap">', unsafe_allow_html=True)
    if b64:
        st.markdown(f'<div class="hdr-logo"><img src="data:image/png;base64,{b64}" style="height:100%;width:100%;object-fit:cover;"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="hdr-logo"><span style="color:#333;">Logo</span></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div>
          <h1>HUMAIN Lifestyle</h1>
          <p>Your Gateway to The Kingdom of Saudi Arabia 🇸🇦</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div></div>', unsafe_allow_html=True)
