FROM python:3.12-slim
WORKDIR /app
COPY ./services/payments_service /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic
EXPOSE 8002
CMD ["uvicorn", "services.payments_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
