# core/security/identity.py
import streamlit as st
import uuid

def device_fingerprint():
    if "device_id" not in st.session_state:
        st.session_state.device_id = uuid.uuid4().hex
    return st.session_state.device_id

def ip_risk_score(ip):
    if ip.startswith("41."):
        return "Low Risk"
    if ip.startswith("102."):
        return "Medium Risk"
    return "Unknown Risk"