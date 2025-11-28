from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey
from services.bank_service.db.session import Base
from sqlalchemy.orm import relationship

class Account(Base):
    __tablename__ = "accounts"
    user = Column(String, primary_key=True, index=True)
    balance = Column(Float, default=0.0)

class Ledger(Base):
    __tablename__ = "ledger"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user = Column(String, index=True)
    amount = Column(Float)
    type = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())