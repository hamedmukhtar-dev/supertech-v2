from services.payments_service.providers.interface import PaymentProvider
import uuid

class MockProvider(PaymentProvider):
    def charge(self, user: str, amount: float, currency: str = "USD"):
        txn = "MOCK-" + uuid.uuid4().hex[:12]
        return {"status": "approved", "transaction_id": txn, "amount": amount, "currency": currency}

    def refund(self, transaction_id: str, amount: float):
        return {"status": "refunded", "transaction_id": transaction_id, "amount": amount}

# singleton
mock_provider = MockProvider()
