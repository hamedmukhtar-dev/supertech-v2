from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.config import settings
from services.bank_service.db.session import get_db
from services.bank_service.models.models import Account, Ledger

router = APIRouter()

class BalanceResponse(BaseModel):
    user: str
    balance: float

class TransferRequest(BaseModel):
    sender: str
    receiver: str
    amount: float

class TxRequest(BaseModel):
    user: str
    amount: float

@router.get("/balance", response_model=BalanceResponse)
def balance(user: str, db: Session = Depends(lambda: next(get_db()))):
    acct = db.query(Account).filter(Account.user == user).first()
    bal = acct.balance if acct else 0.0
    return {"user": user, "balance": bal}

@router.post("/deposit")
def deposit(req: TxRequest, db: Session = Depends(lambda: next(get_db()))):
    acct = db.query(Account).filter(Account.user == req.user).first()
    if not acct:
        acct = Account(user=req.user, balance=req.amount)
        db.add(acct)
    else:
        acct.balance += req.amount
    entry = Ledger(user=req.user, amount=req.amount, type="credit")
    db.add(entry)
    db.commit()
    db.refresh(acct)
    return {"user": req.user, "balance": acct.balance}

@router.post("/withdraw")
def withdraw(req: TxRequest, db: Session = Depends(lambda: next(get_db()))):
    acct = db.query(Account).filter(Account.user == req.user).first()
    if not acct or acct.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    acct.balance -= req.amount
    entry = Ledger(user=req.user, amount=-req.amount, type="debit")
    db.add(entry)
    db.commit()
    db.refresh(acct)
    return {"user": req.user, "balance": acct.balance}

@router.post("/transfer")
def transfer(req: TransferRequest, db: Session = Depends(lambda: next(get_db()))):
    sender = db.query(Account).filter(Account.user == req.sender).first()
    receiver = db.query(Account).filter(Account.user == req.receiver).first()
    if not sender or sender.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    if not receiver:
        receiver = Account(user=req.receiver, balance=0.0)
        db.add(receiver)
        db.commit()
        db.refresh(receiver)
    # perform transfer
    sender.balance -= req.amount
    receiver.balance += req.amount
    db.add(Ledger(user=req.sender, amount=-req.amount, type="transfer_out"))
    db.add(Ledger(user=req.receiver, amount=req.amount, type="transfer_in"))
    db.commit()
    return {"message": f"Transfer {req.amount} from {req.sender} to {req.receiver}"}

@router.get("/ledger")
def ledger(limit: int = 100, db: Session = Depends(lambda: next(get_db()))):
    rows = db.query(Ledger).order_by(Ledger.timestamp.desc()).limit(limit).all()
    return [{"id": r.id, "user": r.user, "amount": r.amount, "type": r.type, "timestamp": r.timestamp} for r in rows]