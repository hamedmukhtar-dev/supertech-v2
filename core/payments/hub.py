# core/payments/hub.py
def process_payment(method, amount):
    return {
        "method": method,
        "amount": amount,
        "status": "APPROVED",
        "reference": "TXN-" + str(hash(method + str(amount)))[:10]
    }

SUPPORTED_METHODS = [
    "Card",
    "Bank Transfer",
    "Mobile Money",
    "eWallet",
    "Internal Transfer"
]