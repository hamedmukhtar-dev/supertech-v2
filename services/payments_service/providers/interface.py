from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    @abstractmethod
    def charge(self, user: str, amount: float, currency: str = "USD"):
        pass

    @abstractmethod
    def refund(self, transaction_id: str, amount: float):
        pass
