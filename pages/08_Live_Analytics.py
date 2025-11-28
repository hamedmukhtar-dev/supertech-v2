import streamlit as st
from core.app_controller import init_app, navbar
from core.realtime.stream_engine import generate_realtime_events

init_app()
navbar()

st.title("📊 Live Analytics Dashboard")

ph = st.empty()

for event in generate_realtime_events():
    ph.write(event)