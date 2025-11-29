import streamlit as st
from core.app_controller import init_app, navbar
from core.travel_ndc.offer_builder import generate_flight_offers

init_app()
navbar()

st.title("✈️ Travel Simulation")

frm = st.text_input("From", "KRT", key="12_TRAVEL_SIMULATION_text_input_69d08e")
to = st.text_input("To", "DXB", key="12_TRAVEL_SIMULATION_text_input_3140dd")

if st.button("Search Flights"):
    offers = generate_flight_offers({"from": frm, "to": to})
    st.table(offers)