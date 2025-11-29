import streamlit as st
from core.app_controller import init_app, navbar
from core.finance.ledger import init_ledger, add_transaction, get_transactions

init_app()
navbar()
init_ledger()

st.title("💰 HUMAIN Financial Core")

user = st.text_input("User Email", key="pages_10_Financial_Core_USER_EMAIL_b8bc15")
amount = st.number_input("Amount", step=1.0, key="pages_10_Financial_Core_AMOUNT_3a0c38")
txn_type = st.selectbox("Type", ["credit", "debit"], key="pages_10_Financial_Core_TYPE_291c7a")

if st.button("Submit Transaction"):
    add_transaction(user, amount, txn_type)
    st.success("Transaction added!")

st.subheader("📄 Ledger")
st.table(get_transactions())