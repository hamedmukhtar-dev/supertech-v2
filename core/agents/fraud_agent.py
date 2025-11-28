from core.ai_engine import ai_insights

def run_fraud_agent(event):
    return ai_insights(f"Fraud Analysis Needed: {event}")