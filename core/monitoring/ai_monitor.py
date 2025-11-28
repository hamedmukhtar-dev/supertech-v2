# core/monitoring/ai_monitor.py
from core.ai_engine import ai_insights

def ai_healthcheck():
    return ai_insights("Provide a brief health status for the AI system.")

def ai_usage_summary(logs):
    return ai_insights(f"Summarize AI usage logs: {logs}")