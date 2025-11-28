FROM python:3.12-slim

WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/ai_service /app

# Install minimal dependencies
RUN pip install --no-cache-dir fastapi uvicorn openai pydantic

EXPOSE 8000

CMD ["uvicorn", "services.ai_service.main:app", "--host", "0.0.0.0", "--port", "8000"]