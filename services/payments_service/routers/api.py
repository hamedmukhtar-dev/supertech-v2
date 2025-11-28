from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from services.payments_service.providers import mock_provider
from services.payments_service.utils.webhook import verify_webhook_signature
from core.config import settings

router = APIRouter()

class ChargeRequest(BaseModel):
    user: str
    amount: float
    currency: str = "USD"

class RefundRequest(BaseModel):
    transaction_id: str
    amount: float

@router.post("/charge")
def charge(req: ChargeRequest):
    # Use provider interface
    res = mock_provider.charge(user=req.user, amount=req.amount, currency=req.currency)
    return res

@router.post("/refund")
def refund(req: RefundRequest):
    res = mock_provider.refund(transaction_id=req.transaction_id, amount=req.amount)
    return res

@router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Signature", "")
    if not verify_webhook_signature(body, signature, settings.PAYMENT_PROVIDER_TOKEN):
        raise HTTPException(status_code=400, detail="Invalid signature")
    # Process webhook (mock)
    return {"status": "received"}
