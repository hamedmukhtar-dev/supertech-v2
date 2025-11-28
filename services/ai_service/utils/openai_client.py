from openai import OpenAI
from core.config import settings

class OpenAIClient:
    def __init__(self, api_key: str = None):
        # The OpenAI client will use environment or provided key
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()

    def completion(self, prompt: str, model: str = None) -> str:
        model_name = model or settings.AI_MODEL
        # Use the Responses API as requested in Phase 6
        resp = self.client.responses.create(model=model_name, input=prompt)
        # Access output_text (per Phase 6 usage)
        return getattr(resp, "output_text", "") or getattr(resp, "output", "")

# Singleton instance used by routers
openai_client = OpenAIClient(api_key=settings.OPENAI_API_KEY)