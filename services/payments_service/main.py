from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from services.payments_service.routers import api as payments_router

app = FastAPI(title="HUMAIN — Payments Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router.router, prefix="/payments", tags=["payments"])

@app.get("/")
def root():
    return {"service": "payments_service"}
