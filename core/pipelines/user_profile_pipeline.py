# core/pipelines/user_profile_pipeline.py
from core.ai_engine import ai_customer_profile

def generate_ai_profile(user_data):
    return ai_customer_profile(f"Generate deep AI persona for user: {user_data}")