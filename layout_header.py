# layout_header.py — Light header (no dark background)
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
    logo = _logo_b64()
    st.markdown(
        """
<style>
.header-wrap{
  display:flex; align-items:center; gap:12px;
  padding:10px 12px; margin-bottom:8px;
  background:#ffffff; border:1px solid #E6E8EF; border-radius:14px;
}
.header-logo{ height:40px; width:40px; border-radius:10px; border:1px solid #C8A646; overflow:hidden; background:#fff; }
.header-title{ line-height:1.2; }
.header-title h2{ margin:0; font-size:1.15rem; font-weight:800; color:#1a1f2a; }
.header-title p{ margin:2px 0 0; color:#677181; font-size:.92rem; }
</style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
    if logo:
        st.markdown(f'<div class="header-logo"><img src="data:image/png;base64,{logo}" style="height:100%;width:100%;object-fit:cover;" /></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="header-logo"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="header-title">
          <h2>HUMAIN Lifestyle — Live Demo</h2>
          <p>Gateway to KSA • Travel • Umrah • Investors</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
