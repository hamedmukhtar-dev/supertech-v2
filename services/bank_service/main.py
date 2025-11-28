from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from services.bank_service.routers import api as bank_router
from services.bank_service.db import session as db_session

app = FastAPI(title="HUMAIN — Banking Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB initialized on startup
@app.on_event("startup")
def startup():
    db_session.init_db()

app.include_router(bank_router.router, prefix="/bank", tags=["bank"])

@app.get("/")
def root():
    return {"service": "bank_service", "db": settings.BANK_DB}