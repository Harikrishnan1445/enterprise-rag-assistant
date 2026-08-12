![CI](https://github.com/Harikrishnan1445/enterprise-rag-assistant/actions/workflows/ci.yml/badge.svg)

# Enterprise Knowledge Intelligence & RAG Assistant

A local-first, fully containerized Retrieval-Augmented Generation (RAG) system: upload documents, ask natural-language questions, and get answers grounded in your own content — with cited sources, conversation history, and a measured (not assumed) evaluation of retrieval and answer quality.

Built end-to-end with a **$0 infrastructure cost** constraint: no paid APIs, no cloud LLM, no cloud vector DB. Everything runs locally via Docker + Ollama.

---

## Problem Statement

Generic LLMs can't answer questions about private or organization-specific documents, and they hallucinate when asked to. This project implements a full RAG pipeline — document ingestion, chunking, local embedding, vector search, and grounded local LLM generation with source citations — so answers are traceable back to the actual uploaded content, not invented.

---

## Architecture

```
Browser (static frontend, served by FastAPI)
        │
        ▼
   FastAPI application (Docker container: app)
        │
        ├── Auth (JWT, bcrypt)
        ├── Document upload → extract → clean → chunk
        ├── Local embedding (sentence-transformers, all-MiniLM-L6-v2)
        │
        ▼
   PostgreSQL + pgvector (Docker container: db)
        │  (HNSW index, cosine similarity)
        ▼
   Vector search → top-K relevant chunks
        │
        ▼
   Local LLM generation (Ollama, phi3:mini — runs on host)
        │
        ▼
   Grounded answer + cited source chunks → stored in conversation history
```

The FastAPI app and PostgreSQL both run inside Docker Compose on a shared network. Ollama runs on the host machine (not containerized) and is reached from inside the container via `host.docker.internal`. The frontend is a static single-page app served directly by FastAPI at `/` — no separate frontend service or build step.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Frontend | Static HTML/CSS/JS (vanilla), served by FastAPI |
| Language | Python 3.13 |
| Database | PostgreSQL 16 + pgvector |
| ORM / migrations | SQLAlchemy (async) + Alembic |
| Auth | JWT (python-jose, HS256) + bcrypt (passlib) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, 384-dim, local) |
| LLM | Ollama, `phi3:mini` (local, CPU inference) |
| Testing | pytest, pytest-asyncio, httpx |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions (lint, migrate, test, build) |
| Linting | Ruff |

No paid services are used anywhere in the stack.

---

## Features

- Web UI: login/register, drag-and-drop document upload, chat interface with live retrieval visualization
- User registration & login (JWT-based auth, bcrypt password hashing)
- Role-based authorization
- Document upload (PDF, DOCX, TXT) with async processing
- Text extraction → cleaning → chunking pipeline
- Local embedding generation and pgvector storage
- Semantic search (cosine similarity) with HNSW indexing
- RAG-grounded chat: answers cite the specific source chunks used, with expandable source previews
- Persistent conversation history
- Global error handling & structured logging
- Automated tests (16/16 passing) and CI-enforced on every push

---

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create a user |
| POST | `/api/v1/auth/login` | Obtain a JWT |
| GET | `/api/v1/users/me` | Current user profile |
| GET | `/api/v1/users` | List users |
| POST | `/api/v1/documents` | Upload a document |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Get a document |
| DELETE | `/api/v1/documents/{id}` | Delete a document |
| POST | `/api/v1/documents/{id}/process` | Trigger extraction/chunking/embedding |
| POST | `/api/v1/chat` | Ask a question (RAG) |
| GET | `/api/v1/chat/conversations` | List conversation history |
| GET | `/health` | Liveness check |
| GET | `/health/db` | Database connectivity check |

Full interactive docs available via Swagger UI at `/docs` once running.

---

## Database Schema

- **users** — id, email, hashed_password, full_name, role, is_active
- **documents** — owner_id → users, filename, file_type, processing_status
- **document_chunks** — document_id → documents, chunk_index, text, `embedding vector(384)` (HNSW-indexed, cosine ops)
- **conversations** — user_id → users
- **messages** — conversation_id → conversations, role (user/assistant)
- **feedback** — message_id → messages, user_id → users, rating, comment
- **query_logs** — standalone request logging

---

## Setup

### Prerequisites
- Docker Desktop
- [Ollama](https://ollama.com) installed on the host, with `phi3:mini` pulled (`ollama pull phi3:mini`)

### Run
```bash
# clone the repo, then:
cp .env.example .env      # fill in secrets
docker compose up --build -d

# apply database migrations (first run only)
docker compose exec app alembic upgrade head
```

Open `http://localhost:8000` in a browser for the web UI, or `http://localhost:8000/docs` for interactive API docs.

### Run tests
```bash
docker compose exec app pytest
```

---

## RAG Evaluation (Phase 30 — measured, not estimated)

An evaluation harness (`scripts/evaluate_rag.py`) runs 8 hand-written question/expected-answer/expected-source test cases across 4 topic-distinct documents, calling the real `RAGService` in-process.

| Metric | Result |
|---|---|
| Retrieval accuracy (expected doc in top-3) | 8/8 (100%) |
| Answer correctness (≥half expected keywords present) | 8/8 (100%) |
| Average response time | ~19.5s (CPU-only local inference) |

**Note:** this is an 8-question test set across 4 documents — enough to demonstrate a real evaluation methodology and get genuine signal, not a large-scale benchmark.

---

## Security (Phase 31)

| Item | Status |
|---|---|
| Password hashing (bcrypt) | ✅ Pass |
| JWT validation (fails closed) | ✅ Pass |
| Role-based authorization | ✅ Pass |
| Document ownership enforcement | ✅ Pass (minor note below) |
| Secrets never committed | ✅ Confirmed via git history check |
| SQL injection | ✅ Pass — ORM-parameterized queries only |
| CORS policy | ✅ Fixed — was missing, added and scoped to local dev origins |

**Known minor issue (not fixed, low severity):** requesting another user's document returns 403 vs. a nonexistent document's 404, which lets a non-owner infer that a given document ID exists. No other data is exposed. Documented here rather than silently left out.

---

## Performance (Phase 32)

All numbers below are from real measured requests, not estimates.

| Component | Measured |
|---|---|
| Vector retrieval | 45–75ms |
| LLM generation (phi3:mini, CPU) | 24.1s–31.8s |
| Total request time | ~32–34s |

LLM generation on local CPU accounts for 96–99% of total latency — an inherent cost of the $0/local-only constraint, not a defect. A HNSW index was added on the embedding column for future scale; at the current small corpus size, PostgreSQL's planner correctly favors a sequential scan (verified via `EXPLAIN`), so the index has no effect yet but is in place and ready to activate as data grows.

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push:
1. Install dependencies
2. Lint (Ruff)
3. Run database migrations against a fresh Postgres/pgvector service container
4. Run the full test suite (16/16 passing)
5. Build the Docker image (gated on tests passing)

---

## Limitations

- Local CPU-only LLM inference is slow (~25–30s/request) — a deliberate tradeoff for zero infrastructure cost
- RAG evaluation covers 8 questions across 4 documents — a proof of methodology, not a large-scale benchmark
- Minor IDOR information-leak (document existence, not content) noted but not fixed

## Future Improvements

- Expand RAG evaluation corpus and test cases
- Fix the 403/404 existence-leak on document endpoints
- Investigate GPU-accelerated inference or a smaller/faster local model for latency
