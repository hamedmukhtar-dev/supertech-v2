import streamlit as st
from core.app_controller import init_app, navbar
from core.finance.ledger import init_ledger, add_transaction, get_transactions

init_app()
navbar()
init_ledger()

st.title("💰 HUMAIN Financial Core")

user = st.text_input("User Email", key="10_Financial_Core_text_input_04da6f")
amount = st.number_input("Amount", step=1.0, key="10_Financial_Core_number_input_3d209f")
type = st.selectbox("Type", ["credit", "debit"], key="10_Financial_Core_selectbox_28912f")

if st.button("Submit Transaction"):
    add_transaction(user, amount, type)
    st.success("Transaction added!")

st.subheader("📄 Ledger")
st.table(get_transactions())