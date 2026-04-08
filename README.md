# Org-Aware AI Agent

An enterprise-grade AI chat agent that is organization-aware — it knows who you are, what role you have, and what data you are allowed to access. Built on FastAPI + React, secured by Keycloak SSO, and powered by Claude (Anthropic) with a hybrid RAG retrieval backend using pgvector.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Authentication & Authorization](#authentication--authorization)
- [RAG System](#rag-system)
- [Development Status](#development-status)
- [Contributing](#contributing)

---

## Overview

The Org-Aware AI Agent is a multi-phase enterprise AI assistant that:

- Authenticates users via Keycloak (OIDC/OAuth2)
- Injects user identity and roles into every agent interaction
- Retrieves organization-specific knowledge using hybrid semantic + full-text search (pgvector + BM25)
- Enforces role-based document access control at retrieval time
- Provides grounded, cited responses via Claude (Anthropic)
- Maintains full audit trails for compliance

---

## Features

### Phase 1 — Foundation (Complete)
- SSO login via Keycloak OIDC
- Persistent chat sessions with message history stored in PostgreSQL
- JWT validation via JWKS with 15-minute cache
- Structured logging and health checks
- LangGraph-based stateful agent orchestration

### Phase 2 — Hybrid RAG (Complete)
- Document ingestion: PDF, DOCX, HTML, plain text
- Embeddings via OpenAI `text-embedding-3-small`
- Hybrid search: cosine similarity (pgvector) + BM25 full-text (PostgreSQL FTS)
- Weighted score fusion (default: 75% semantic, 25% keyword)
- Role-based and user-level ACL enforcement at SQL query time
- Source citations surfaced in every response

### Phase 3 — DB & Jira Integration (Stubs)
- Read-only SQL query tool with whitelisted tables
- Jira search and ticket creation stubs
- Service account authentication for Jira

### Phase 4 — IAM Awareness (Partial)
- Full user context injection from JWT claims (roles, groups, department)
- Role-based tool access control (placeholder)
- IAM lookup tool (planned)

### Phase 5 — Production Polish (Partial)
- Audit logging with PII masking
- OpenTelemetry traces, metrics, and logs
- User feedback collection (table ready, UI planned)
- Streaming responses (planned)
- Admin dashboard (planned)

---

## Architecture

### Request Flow

```
User Browser (React)
    │
    ▼
Keycloak OIDC Login ──── Access Token (JWT)
    │
    ▼
POST /api/v1/chat  (Authorization: Bearer <JWT>)
    │
    ▼
FastAPI  ──── JWT validation via JWKS
    │
    ▼
Agent Runner
    ├── Reconstruct message history from DB
    ├── Build AgentState (messages + user_context)
    └── Invoke LangGraph graph
            │
            ▼
        call_model node
            ├── Inject user context into system prompt
            ├── Call Claude with registered tools
            └── Route to tool node on tool_calls
                    │
                    ├── RAG Search ─── embed query → hybrid search → ACL filter
                    ├── DB Query (stub)
                    ├── Jira Tools (stub)
                    └── IAM Lookup (stub)
            │
            ▼
        Final Claude response + citations
    │
    ▼
Persist messages → Audit log → Return ChatResponse
    │
    ▼
React Frontend  ──── Render message + citation cards
```

### RAG Data Flow

```
User Query: "What is our vacation policy?"
    │
    ▼
Embed query (OpenAI text-embedding-3-small)
    │
    ├── Semantic branch: cosine similarity via pgvector
    └── Keyword branch:  ts_rank_cd via PostgreSQL FTS
            │
            ▼
        Score fusion:  0.75 × semantic_rank + 0.25 × keyword_rank
            │
            ▼
        ACL filter:  WHERE acl_roles && user_roles OR acl_users @> user_id
            │
            ▼
        Top-K chunks with metadata and source URLs
            │
            ▼
        Claude generates grounded response with citations
```

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 (async) |
| ASGI Server | Uvicorn 0.32 |
| LLM | Anthropic Claude (`claude-sonnet-4-5`) |
| Agent Orchestration | LangGraph 0.2.50+ |
| Tool Framework | LangChain 0.3+ |
| Database ORM | SQLAlchemy 2.0 (asyncio) |
| Migrations | Alembic 1.14 |
| Vector Search | pgvector (cosine similarity) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Authentication | Keycloak OIDC + PyJWT (JWKS) |
| Document Parsing | pdfplumber, python-docx, BeautifulSoup4 |
| Observability | OpenTelemetry + structlog |
| Validation | Pydantic 2.9 |

### Frontend

| Layer | Technology |
|---|---|
| UI Framework | React 18.3 |
| Language | TypeScript 5.6 |
| Build Tool | Vite 6.0 |
| Styling | Tailwind CSS 3.4 |
| Auth | react-oidc-context 3.2 + oidc-client-ts |
| HTTP Client | Axios 1.7 |
| Server State | TanStack React Query 5.62 |
| Routing | React Router DOM 6.28 |

### Infrastructure

| Component | Technology |
|---|---|
| Database | PostgreSQL 16 + pgvector |
| IAM | Keycloak 24.0 (self-hosted) |
| Web Server | Nginx (frontend reverse proxy) |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
org-aware-agent/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py          # LangGraph state machine & tool routing
│   │   │   ├── state.py          # AgentState TypedDict
│   │   │   ├── prompts.py        # System prompt templates
│   │   │   └── runner.py         # Agent execution wrapper
│   │   ├── api/
│   │   │   ├── chat.py           # POST /api/v1/chat
│   │   │   ├── health.py         # GET /health
│   │   │   └── sessions.py       # Session management (stub)
│   │   ├── auth/
│   │   │   ├── keycloak.py       # JWT validation via JWKS
│   │   │   ├── dependencies.py   # FastAPI dependency injection
│   │   │   ├── models.py         # UserContext dataclass
│   │   │   └── rbac.py           # RBAC filter (Phase 4)
│   │   ├── db/
│   │   │   ├── models.py         # SQLAlchemy ORM models
│   │   │   ├── engine.py         # AsyncEngine setup
│   │   │   ├── audit.py          # Audit logging
│   │   │   └── migrations/       # Alembic versions
│   │   ├── tools/
│   │   │   └── rag.py            # Hybrid RAG search tool
│   │   ├── core/
│   │   │   ├── config.py         # Settings from environment
│   │   │   ├── errors.py         # Custom exception handlers
│   │   │   ├── logging.py        # structlog setup
│   │   │   └── telemetry.py      # OpenTelemetry setup
│   │   └── main.py               # FastAPI app factory
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Chat.tsx          # Main chat interface
│   │   │   └── Login.tsx         # OIDC login redirect
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── CitationCard.tsx
│   │   │   ├── CitationList.tsx
│   │   │   ├── AuthGuard.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   └── useAuth.ts
│   │   ├── lib/
│   │   │   └── api.ts            # Axios client with OIDC token injection
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── nginx.conf
├── infra/
│   ├── keycloak/
│   │   └── realm-export.json     # Keycloak realm seed
│   └── postgres/
│       └── init.sql              # PostgreSQL + pgvector setup
├── scripts/
│   └── ingest_docs.py            # Document ingestion script
├── docker-compose.yml
├── .env.example
└── PRD.md
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Anthropic API key (for Claude LLM)
- OpenAI API key (for embeddings)

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/thedineshbabu/org-aware-agent.git
cd org-aware-agent

# 2. Create environment file
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and OPENAI_API_KEY at minimum

# 3. Start all services
docker-compose up -d

# 4. Wait for services to become healthy (approx. 60 seconds)
docker-compose logs -f backend
# Ready when: "startup_complete" appears in logs

# 5. Access the application
# Frontend:       http://localhost:3000
# Backend API:    http://localhost:8000
# API Docs:       http://localhost:8000/docs
# Keycloak Admin: http://localhost:8081 (admin / admin)
```

### Default Test Users (from realm-export.json)

| User | Password | Role |
|---|---|---|
| alice@example.com | password | employee |
| bob@example.com | password | developer |
| carol@example.com | password | it_admin |

### Database Migrations

Migrations run automatically on backend startup. To run manually:

```bash
docker-compose exec backend alembic -c app/db/migrations/alembic.ini upgrade head
```

### Ingesting Documents (Phase 2 RAG)

```bash
# Place PDF/DOCX/HTML files in a directory, then run:
python scripts/ingest_docs.py --input-dir ./docs --chunk-size 512
```

---

## Environment Variables

Copy `.env.example` to `.env` and populate the values below.

### Application

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment name |
| `LOG_LEVEL` | `INFO` | Log verbosity |

### PostgreSQL

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `orgagent` | Database name |
| `POSTGRES_USER` | `orgagent` | Database user |
| `POSTGRES_PASSWORD` | — | Database password (required) |
| `DATABASE_URL` | — | Full async connection string |
| `READONLY_DB_URL` | — | Read-only connection for agent DB queries |
| `WHITELISTED_TABLES` | — | Comma-separated tables the agent may query |

### Keycloak

| Variable | Default | Description |
|---|---|---|
| `KEYCLOAK_URL` | — | Keycloak server URL |
| `KEYCLOAK_REALM` | `org-agent` | Realm name |
| `KEYCLOAK_CLIENT_ID` | `org-agent-backend` | Backend client ID |
| `KEYCLOAK_CLIENT_SECRET` | — | Backend client secret |
| `KEYCLOAK_AUDIENCE` | `org-agent-backend` | JWT audience claim |

### LLM Provider

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | LLM backend: `anthropic` or `openai` |

### Anthropic (when `LLM_PROVIDER=anthropic`)

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Claude model ID |

### OpenAI (when `LLM_PROVIDER=openai`)

| Variable | Default | Description |
|---|---|---|
| `OPENAI_LLM_API_KEY` | — | OpenAI API key for the LLM |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model ID |

### RAG / Embeddings

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_PROVIDER` | `openai` | Embedding provider |
| `OPENAI_API_KEY` | — | **Required for Phase 2.** OpenAI API key |
| `RAG_TOP_K` | `8` | Number of chunks to retrieve |
| `RAG_HYBRID_ALPHA` | `0.75` | Weight for semantic vs keyword (0–1) |

### Jira (Phase 3)

| Variable | Default | Description |
|---|---|---|
| `JIRA_BASE_URL` | — | Atlassian domain |
| `JIRA_SERVICE_ACCOUNT_EMAIL` | — | Service account email |
| `JIRA_API_TOKEN` | — | Jira API token |
| `JIRA_CACHE_TTL_SECONDS` | — | Cache TTL for Jira responses |

### Cache (Optional)

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | — | Redis connection URL |
| `CACHE_ENABLED` | `false` | Enable Redis caching |

---

## API Reference

### `POST /api/v1/chat`

Send a message to the agent.

**Headers**
```
Authorization: Bearer <Keycloak JWT>
Content-Type: application/json
```

**Request Body**
```json
{
  "message": "What is our vacation policy?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
`session_id` is optional. If omitted, a new session is created.

**Response**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "content": "Based on our HR Handbook, employees receive 15 days of paid time off per year...",
  "citations": [
    {
      "doc_name": "HR-Handbook.pdf",
      "section": "Time Off",
      "url": "s3://org-docs/hr-handbook.pdf",
      "chunk_text": "Employees receive 15 days of paid vacation annually...",
      "last_updated": "2025-03-15"
    }
  ],
  "requires_confirmation": false,
  "pending_ticket": null,
  "latency_ms": 1250
}
```

---

### `GET /health`

Service health check.

**Response**
```json
{
  "status": "ok",
  "checks": {
    "database": "ok"
  }
}
```

---

### Sessions (Stub)

```
GET  /api/v1/sessions
POST /api/v1/sessions
GET  /api/v1/sessions/{session_id}
```

---

## Database Schema

### `sessions`
Tracks chat sessions per user.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | TEXT | Keycloak subject claim |
| `title` | TEXT | Auto-generated session title |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last activity time |

### `messages`
Stores full chat history.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | FK → sessions |
| `role` | TEXT | `user` or `assistant` |
| `content` | TEXT | Message text |
| `tool_name` | TEXT | Tool used (if any) |
| `created_at` | TIMESTAMP | Message time |

### `document_chunks`
RAG document storage with hybrid search indexes.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `doc_name` | TEXT | Source document name |
| `section` | TEXT | Document section |
| `url` | TEXT | Source URL or path |
| `chunk_text` | TEXT | Raw chunk content |
| `embedding` | vector(1536) | OpenAI embedding |
| `fts` | tsvector | Full-text search index |
| `acl_roles` | TEXT[] | Roles permitted to access this chunk |
| `acl_users` | TEXT[] | Explicit user IDs with access |

Indexes: `ivfflat` on `embedding`, `gin` on `fts`.

### `agent_audit_log`
Immutable audit trail for every agent interaction.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | TEXT | Keycloak subject |
| `query_text` | TEXT | User query (PII masked) |
| `tools_invoked` | JSONB | List of tools used with metadata |
| `latency_ms` | INT | End-to-end latency |
| `created_at` | TIMESTAMP | Interaction time |

### `user_feedback`
Thumbs up/down feedback on responses.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `message_id` | UUID | FK → messages |
| `user_id` | TEXT | Keycloak subject |
| `rating` | INT | `1` (positive) or `-1` (negative) |
| `comment` | TEXT | Optional free-text comment |
| `created_at` | TIMESTAMP | Feedback time |

---

## Authentication & Authorization

### Authentication Flow

1. Frontend redirects to Keycloak `/authorize` endpoint
2. User logs in; Keycloak issues authorization code
3. Frontend exchanges code for access token + ID token
4. Every API request includes `Authorization: Bearer <JWT>`
5. Backend validates JWT signature against Keycloak JWKS (cached 15 min)
6. Claims verified: `exp`, `aud` (`org-agent-backend`)
7. User context extracted: `sub`, `email`, `name`, `realm_access.roles`, `groups`, `department`

### Role-Based Tool Access

| Role | Permitted Tools |
|---|---|
| `employee` | RAG search, Jira search |
| `developer` | RAG search, Jira search, DB query |
| `manager` | RAG search, Jira search, DB query |
| `it_admin` | All tools including IAM lookup |

### Document ACL

Each document chunk stores `acl_roles` and `acl_users` arrays. The RAG query filters chunks at SQL time:

```sql
WHERE (acl_roles IS NULL)
   OR (acl_roles && :user_roles)
   OR (:user_id = ANY(acl_users))
```

---

## RAG System

### Hybrid Search

The RAG tool performs two parallel searches and fuses their scores:

```
final_score = α × (1 / semantic_rank) + (1 - α) × (1 / keyword_rank)
```

- `α` defaults to `0.75` (configurable via `RAG_HYBRID_ALPHA`)
- Semantic branch: pgvector cosine distance (`<=>`)
- Keyword branch: PostgreSQL `ts_rank_cd` with `plainto_tsquery`

### Document Ingestion

The ingestion pipeline (`scripts/ingest_docs.py`):

1. Parse documents (PDF → pdfplumber, DOCX → python-docx, HTML → BeautifulSoup4)
2. Chunk text with configurable `--chunk-size` (default 512 tokens)
3. Embed chunks via OpenAI `text-embedding-3-small` (1536 dimensions)
4. Insert into `document_chunks` with metadata and optional ACL

---

## Development Status

| Phase | Feature | Status |
|---|---|---|
| 1 | FastAPI + React foundation | Complete |
| 1 | Keycloak SSO | Complete |
| 1 | Chat with DB-persisted history | Complete |
| 1 | JWT validation (JWKS) | Complete |
| 2 | pgvector hybrid RAG | Complete |
| 2 | Document ACL enforcement | Complete |
| 2 | Source citations in responses | Complete |
| 3 | DB query tool | Stub |
| 3 | Jira search / create | Stub |
| 4 | User context injection | Complete |
| 4 | RBAC tool filtering | Placeholder |
| 4 | IAM lookup tool | Not started |
| 5 | Streaming responses | Not started |
| 5 | Audit logging + PII masking | Complete |
| 5 | OpenTelemetry observability | Configured |
| 5 | Admin dashboard | Not started |
| 5 | User feedback UI | Partial |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push to your fork: `git push origin feature/my-feature`
5. Open a pull request against `master`

### Branch Conventions

- `feature/*` — new features
- `fix/*` — bug fixes
- `chore/*` — maintenance tasks

### Commit Style

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add streaming response support
fix: correct JWKS cache invalidation on key rotation
chore: upgrade langchain to 0.3.5
```
