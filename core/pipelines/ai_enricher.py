# core/pipelines/ai_enricher.py
from core.ai_engine import ai_insights

def enrich_behavior_log(logs):
    return ai_insights(f"Analyze full user behavior log: {logs}")