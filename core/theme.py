# core/theme.py
THEME_CSS = """
<style>
body, .stApp {
    background-color: #000000;
    color: #EDEDED !important;
}

h1, h2, h3, h4 {
    color: #D4AF37 !important;
}

.sidebar .sidebar-content {
    background-color: #111111 !important;
}
</style>
"""

def inject_theme(st):
    st.markdown(THEME_CSS, unsafe_allow_html=True)