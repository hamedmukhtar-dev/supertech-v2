HUMAIN Orchestrator

This document describes how services interact in Phase 7.

- ai_service: provides AI endpoints for insights, fraud analysis, and CRM enrichment.
- bank_service: transactional banking API and ledger.
- payments_service: abstracts payment provider operations (charge/refund) and webhook handling.
- realtime_service: publishes and streams events for dashboards and consumers.

Local development: use docker-compose.dev.yml to run services locally.
