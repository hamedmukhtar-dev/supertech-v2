import streamlit as st
from core.app_controller import init_app, navbar
from core.security.identity import device_fingerprint, ip_risk_score

init_app()
navbar()

st.title("🔒 Security & Identity Center")

ip = st.text_input("Your IP", "102.120.44.10", key="13_SECURITY_CENTER_YOUR_IP_dd5333")

st.write("Device Fingerprint:", device_fingerprint())
st.write("IP Risk Score:", ip_risk_score(ip))