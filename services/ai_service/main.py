from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from services.ai_service.routers import api as ai_router

app = FastAPI(title="HUMAIN — AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router, prefix="/ai", tags=["ai"])

@app.get("/")
def root():
    return {"service": "ai_service", "model": settings.AI_MODEL}