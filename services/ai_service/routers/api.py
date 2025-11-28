from fastapi import APIRouter, Depends
from pydantic import BaseModel
from core.config import settings
from services.ai_service.utils.openai_client import openai_client

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

class AiResponse(BaseModel):
    text: str

@router.post("/insights", response_model=AiResponse)
def insights(req: PromptRequest):
    text = openai_client.completion(req.prompt, model=settings.AI_MODEL)
    return {"text": text}

@router.post("/fraud", response_model=AiResponse)
def fraud(req: PromptRequest):
    text = openai_client.completion(f"Fraud analysis: {req.prompt}", model=settings.AI_MODEL)
    return {"text": text}

@router.post("/crm", response_model=AiResponse)
def crm(req: PromptRequest):
    text = openai_client.completion(f"CRM optimization: {req.prompt}", model=settings.AI_MODEL)
    return {"text": text}

@router.get("/health", response_model=dict)
def health():
    # Lightweight health check for AI service
    return {"status": "ok", "model": settings.AI_MODEL}