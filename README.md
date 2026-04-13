# GymIQ — AI Gym Intelligence

> Phase 1 — FastAPI + Supabase + Groq

GymIQ is a backend API that brings AI intelligence to gym management. It handles member authentication, a guided onboarding survey that generates a personalised AI workout plan, QR-based check-ins, an Arabic-language exercise Q&A chatbot (RAG), and an AI nutrition coach — all in one service.

---

## Features

| Feature | Description |
|---|---|
| **Auth** | Phone + password registration & login with JWT tokens |
| **Gym Management** | Multi-tenant: each member belongs to a gym |
| **Onboarding Survey** | 6-question guided survey that builds a member profile |
| **AI Workout Plan** | Groq LLM generates a personalised plan after onboarding |
| **QR Check-ins** | Log and retrieve member check-in history |
| **Exercise Q&A (RAG)** | Ask Arabic exercise questions — answers grounded in your gym's library |
| **Nutrition Coach** | AI-generated 30-day nutrition plan + follow-up RAG Q&A |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) (async) |
| Database | [Supabase](https://supabase.com/) (PostgreSQL + pgvector) |
| ORM | SQLAlchemy (async) |
| LLM | [Groq](https://groq.com/) (Llama 3) |
| Embeddings | [Cohere](https://cohere.com/) |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Settings | `pydantic-settings` via `.env` |

---

## Project Structure

```
app/
├── main.py                  # App entry point, lifespan, exception handlers
├── database.py              # Async SQLAlchemy engine & session
├── core/
│   ├── config.py            # Settings from .env (Pydantic)
│   ├── security.py          # JWT creation/decoding, password hashing
│   └── exceptions.py        # Custom domain exceptions
├── models/                  # SQLAlchemy ORM models
│   ├── gym_model.py
│   ├── member_model.py
│   ├── member_profile_model.py
│   ├── workout_plan_model.py
│   ├── nutrition_plan_model.py
│   ├── checkin_model.py
│   ├── qa_log_model.py
│   └── vector_document_model.py
├── schemas/                 # Pydantic request/response schemas
├── repositories/            # Data access layer (one per model)
├── services/                # Business logic layer
│   ├── auth_service.py
│   ├── onboarding_service.py
│   ├── workout_plan_service.py
│   ├── checkin_service.py
│   ├── qa_log_service.py
│   ├── nutrition_plan_service.py
│   └── vector_document_service.py
├── routers/                 # FastAPI routers
│   ├── auth_router.py
│   ├── gym_router.py
│   ├── onboarding_router.py
│   ├── checkin_router.py
│   ├── qa_log_router.py
│   └── nutrition_router.py
├── client/                  # External service clients (Protocols + implementations)
│   ├── protocols.py         # LLMClientProtocol, EmbeddingClientProtocol
│   ├── llm_client.py        # GroqLLMClient
│   └── embedding_client.py  # CohereEmbeddingClient
└── dependencies/            # FastAPI dependency factory helpers
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd gym
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
GROQ_API_KEY=your-groq-api-key
COHERE_API_KEY=your-cohere-api-key
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
ENVIRONMENT=development
```

### 5. Run the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## API Reference

### Auth — `/auth`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new member with phone, password & gym ID |
| `POST` | `/auth/login` | Login and receive a JWT access token |

### Onboarding — `/onboarding`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/onboarding/start` | Start the 6-question survey (sets Step = Q1) |
| `POST` | `/onboarding/answer` | Submit an answer; advances Q1 → Q6, saves profile on Q6 |
| `POST` | `/onboarding/generate-plan` | Trigger AI workout plan generation (post-survey) |
| `GET` | `/onboarding/my-plan` | Retrieve my active workout plan |
| `PATCH` | `/members/me/profile` | Update profile fields at any time |

### Check-ins — `/checkins`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/checkins` | Simulate a QR check-in |
| `GET` | `/checkins/me` | My check-in history |
| `GET` | `/checkins/{member_id}` | Admin: check-in history for any member |

### Exercise Q&A (RAG) — `/exercises`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/exercises/seed` | Admin: upload `exercises.jsonl`, embed & store in pgvector |
| `POST` | `/exercises/ask` | Ask an exercise question in Arabic (RAG-grounded answer) |
| `GET` | `/exercises/my-history` | My last 20 Q&A interactions |
| `GET` | `/exercises/history/{member_id}` | Admin: Q&A history for a specific member |

### Nutrition Coach — `/nutrition`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/nutrition/generate` | Generate a personalised 30-day nutrition plan |
| `GET` | `/members/me/nutrition` | Retrieve my active nutrition plan |
| `POST` | `/nutrition/ask` | Ask a nutrition follow-up question (RAG) |
| `POST` | `/nutrition/embed-knowledge` | Admin: upload nutrition knowledge base JSON for embedding |

---

## How RAG Works

1. **Seeding**: An admin uploads a `.jsonl` file of exercise / nutrition documents.
2. **Embedding**: Each document is embedded via **Cohere** and stored in **Supabase pgvector**.
3. **Querying**: When a member asks a question, the query is embedded, the top-K most relevant documents are retrieved, and the context is passed to **Groq (Llama 3)** to produce a grounded Arabic answer.
4. **Logging**: Every Q&A pair is saved in `QALog` for history retrieval.

---

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require a Bearer token:

```
Authorization: Bearer <your_jwt_token>
```

Tokens are valid for **7 days** (10 080 minutes) by default and are scoped to a specific gym, so a member of Gym A cannot access data from Gym B.

---

## Architecture Principles

- **Layered architecture**: Routers → Services → Repositories → Models
- **Dependency injection**: Services and repositories are injected via FastAPI `Depends`
- **Protocol-based clients**: `LLMClientProtocol` and `EmbeddingClientProtocol` decouple the services from specific vendors (Groq / Cohere), making them easy to swap or mock in tests
- **Custom exceptions**: Domain-level exceptions (`NotFoundError`, `AuthenticationError`, etc.) are raised in services and handled globally in `main.py` — no HTTP exceptions leak into business logic
- **Async throughout**: Every DB call and external API call is fully async

---

## License

This project is proprietary software. All rights reserved.
