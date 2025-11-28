# Architecture Overview

This repository contains modular microservices for the HUMAIN platform. Phase 7 introduces CI/CD, Payments and Realtime services and integration helpers.

Components:
- API Gateway (future): central routing and auth
- ai_service: AI wrappers (OpenAI)
- bank_service: transactional core and ledger
- payments_service: provider adapters and webhook handling
- realtime_service: event streaming and websocket handlers
- Observability, CI/CD, and testing pipelines

Data flows:
User -> API Gateway -> Service -> DB / AI / Event Bus

Security:
- Secrets are injected via environment variables (.env or vault)
- Webhook signatures validated via HMAC helper

Deployment:
- CI builds images, pushes to registry (placeholder), and deploys to k8s in later phases
