# Backend

Backend uses Clean Architecture. No service code is implemented in Phase 1.

Planned structure:

- `backend/app/domain/` — domain models and business entities
- `backend/app/services/` — use-cases and orchestration
- `backend/app/adapters/` — database, vector store, external APIs
- `backend/config/` — configuration and env handling
- `backend/tests/` — unit and integration tests

See `docs/architecture.md` for design rationale.
