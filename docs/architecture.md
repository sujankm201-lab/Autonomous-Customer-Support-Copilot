# Architecture Overview

High-level architecture for Autonomous Customer Support Copilot:

- Frontend: React + Vite + TypeScript + Tailwind CSS. Responsible for user auth, chat UI, uploads, and admin dashboards.
- Backend: Python + FastAPI. Implements API, auth (JWT), business logic, RAG orchestration, intent detection, and escalation flows.
- Database: MongoDB for users, tickets, conversation history, and analytics.
- Vector DB: ChromaDB for embeddings used by RAG.
- Embeddings: Sentence Transformers (or OpenAI embeddings as an alternative).
- LLM: OpenAI or Anthropic Claude via LangChain integration.
- Storage: Object storage for uploaded files (S3-compatible) or local storage for dev.
- Infra: Docker + docker-compose during development, CI for tests and linting.

Clean Architecture principles:
- `domain/` models and interfaces
- `services/` business logic and use-cases
- `adapters/` external systems (DB, vector store, LLM)
- `api/` transport layer (FastAPI) and request validation
