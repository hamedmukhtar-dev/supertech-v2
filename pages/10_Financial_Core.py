import streamlit as st
from core.app_controller import init_app, navbar
from core.finance.ledger import init_ledger, add_transaction, get_transactions

init_app()
navbar()
init_ledger()

st.title("💰 HUMAIN Financial Core")

user = st.text_input("User Email", key="financialcore_USER_EMAIL_b8bc15")
amount = st.number_input("Amount", step=1.0, key="financialcore_AMOUNT_3a0c38")
type = st.selectbox("Type", ["credit", "debit"], key="financialcore_TYPE_291c7a")

if st.button("Submit Transaction"):
    add_transaction(user, amount, type)
    st.success("Transaction added!")

st.subheader("📄 Ledger")
st.table(get_transactions())