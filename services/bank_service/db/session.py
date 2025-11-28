from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
import os

# Convert fallback sqlite path to SQLAlchemy URL if needed
db_url = settings.BANK_DB
if not db_url.startswith(("postgres://", "postgresql://", "sqlite://", "mysql://")):
    # Treat as file path → sqlite
    db_url = f"sqlite:///{db_url}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import models then create tables
    from services.bank_service.models import models as models_module
    Base.metadata.create_all(bind=engine)