# HUMAIN • DEVELOPMENT ENVIRONMENT

## 1) Create your environment file

cp .env.example .env

Fill your keys:
- OPENAI_API_KEY
- PAYMENT_PROVIDER_TOKEN
- SESSION_SECRET
- JWT_SECRET

## 2) Run Streamlit

streamlit run pages/01_Home.py

## 3) Microservices (Phase 7+)

Each service imports:
    from core.config import settings

No secrets are stored in code.
Everything comes from .env or Vault later.

## 4) Databases

Local SQLite are stored in /data (ignored by Git).
Production will use PostgreSQL.

## 5) Vault Integration (Phase 9)

config.py already supports:
- Environment Variables
- Vault secret injection (future-ready)
