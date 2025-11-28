# core/pipelines/behavior_tracker.py
import streamlit as st

def track(event_name, details=""):
    if "behavior_log" not in st.session_state:
        st.session_state.behavior_log = []

    st.session_state.behavior_log.append(
        {"event": event_name, "details": details}
    )