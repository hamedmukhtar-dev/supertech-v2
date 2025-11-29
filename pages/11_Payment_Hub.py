import streamlit as st
from core.app_controller import init_app, navbar
from core.payments.hub import process_payment, SUPPORTED_METHODS

init_app()
navbar()

st.title("💳 Payment Hub")

method = st.selectbox("Payment Method", SUPPORTED_METHODS, key="11_PAYMENT_HUB_PAYMENT_METHOD_2d17cd")
amount = st.number_input("Amount", step=1.0, key="11_PAYMENT_HUB_AMOUNT_73bd2a")

if st.button("Process Payment"):
    st.write(process_payment(method, amount))