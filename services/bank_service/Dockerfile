FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/bank_service /app

RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary pydantic

EXPOSE 8001

CMD ["uvicorn", "services.bank_service.main:app", "--host", "0.0.0.0", "--port", "8001"]