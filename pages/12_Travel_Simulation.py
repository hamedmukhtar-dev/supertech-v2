import streamlit as st
from core.app_controller import init_app, navbar
from core.travel_ndc.offer_builder import generate_flight_offers

init_app()
navbar()

st.title("✈️ Travel Simulation")

frm = st.text_input("From", "KRT")
to = st.text_input("To", "DXB")

if st.button("Search Flights"):
    offers = generate_flight_offers({"from": frm, "to": to})
    st.table(offers)