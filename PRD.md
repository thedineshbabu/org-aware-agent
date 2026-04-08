# Org-Aware AI Agent
## Product Requirements Document

| Field | Value |
|---|---|
| **Version** | 1.0 — Draft |
| **Status** | For Review |
| **Date** | April 7, 2026 |
| **Owner** | Product / Engineering |
| **Classification** | Internal — Confidential |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Non-Goals](#3-goals--non-goals)
4. [Target Users & Personas](#4-target-users--personas)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Technical Architecture](#7-technical-architecture)
8. [Security & Compliance](#8-security--compliance)
9. [Phased Delivery Plan](#9-phased-delivery-plan)
10. [Success Metrics](#10-success-metrics)
11. [Risks & Mitigations](#11-risks--mitigations)
12. [Open Questions](#12-open-questions)
13. [Appendix — Glossary](#13-appendix--glossary)

---

## 1. Executive Summary

This document defines the requirements for an **Org-Aware AI Agent** — a self-hosted, enterprise-grade conversational AI platform that provides employees with a single intelligent interface to access organizational knowledge, query internal systems, automate tasks, and interact with integrated services including Identity & Access Management, Jira, and internal databases.

The agent is designed to be **identity-aware from the ground up**, meaning every interaction is contextualized by the authenticated user's role, department, and access permissions. Responses are grounded in real organizational data via Retrieval-Augmented Generation (RAG) over internal documents and structured database queries — not generic AI outputs.

> **Goal:** Deliver a production-grade, self-hosted AI agent that reduces internal search friction, automates repetitive workflows, and surfaces org-specific knowledge — all within the organization's security perimeter.

---

## 2. Problem Statement

### 2.1 Current Pain Points

- Employees waste significant time searching across disconnected systems — wikis, Jira, databases, email — to find information they need.
- No unified interface exists to query across all internal knowledge sources simultaneously.
- Repetitive tasks such as ticket creation, user lookups, and policy queries require manual navigation across multiple tools.
- New employees lack a fast path to organizational knowledge, slowing onboarding.
- Existing search tools are keyword-based and do not understand natural language or intent.

### 2.2 Opportunity

A conversational AI agent — grounded in real org data, aware of who is asking, and connected to internal systems — can dramatically reduce time-to-answer for employees and automate high-frequency, low-complexity tasks that currently consume engineering and operations bandwidth.

---

## 3. Goals & Non-Goals

### 3.1 Goals

- Provide a single-pane-of-glass conversational interface for all internal knowledge and task automation.
- Authenticate all users via existing SSO (Keycloak / Okta / Azure AD) with zero additional credential management.
- Ground all answers in verified internal sources via RAG and structured DB queries — minimizing hallucination risk.
- Support multi-tool agent reasoning: the agent can chain multiple internal service calls to answer complex queries.
- Maintain full audit logs of every agent interaction for compliance and security review.
- Be entirely self-hosted within the organization's infrastructure — no data leaves the perimeter.
- Deliver a polished, standalone web application UI accessible to all employees.

### 3.2 Non-Goals

- This is **not** a customer-facing product — internal use only.
- The agent will **not** make write operations to databases without explicit human approval flows.
- Real-time data streaming (e.g., live dashboards) is out of scope for v1.
- Mobile app (iOS/Android) is out of scope for v1 — responsive web only.
- Multi-language support beyond English is deferred to v2.

---

## 4. Target Users & Personas

| Persona | Role | Primary Use Cases |
|---|---|---|
| **The Employee** | General staff across departments | Policy lookups, HR questions, finding internal docs, submitting Jira tickets via chat |
| **The Developer** | Engineering / DevOps | Querying service statuses, searching runbooks, creating and triaging Jira issues, IAM lookups |
| **The Manager** | Team leads / Department heads | Team workload views, project status queries, approval workflows, org chart lookups |
| **The IT Admin** | IT / Security / IAM teams | User access queries, permission audits, onboarding checklists, IAM system queries |
| **The New Hire** | Employees < 90 days | Fast onboarding: who-is-who, process guidance, tool access requests, policy reading |

---

## 5. Functional Requirements

### 5.1 Core Agent Capabilities

| Capability | Description |
|---|---|
| **Natural Language Understanding** | Accept free-text queries in plain English. Understand intent, extract entities, and route to appropriate tool(s). |
| **Multi-Tool Reasoning** | Chain multiple tool calls in a single response (e.g., look up a user in IAM, then find their open Jira tickets). |
| **Streaming Responses** | Stream tokens progressively to the UI for perceived responsiveness. |
| **Source Attribution** | Every factual answer must cite the source document or data record it was derived from. |
| **Conversation Memory** | Maintain context within a session (multi-turn conversations). No cross-session memory by default. |
| **Confidence Signaling** | If the agent cannot find a reliable answer, it must say so rather than hallucinate. |
| **Feedback Collection** | Users can thumbs-up / thumbs-down any response. Feedback is stored for quality improvement. |

---

### 5.2 Identity & Access Management Integration

> **Key Principle:** Every query is user-scoped. The agent knows who is asking (via SSO JWT) and filters all results to data the user has permission to see.

- Authenticate via Keycloak / Okta / Azure AD using OIDC/OAuth2 — no separate login.
- Extract user identity attributes from JWT: user ID, email, department, role, group memberships.
- Inject identity context into every agent prompt so responses are role-appropriate.
- Support IAM lookup tool: query user accounts, group memberships, access roles, and provisioning status.
- Support access request workflow: user can request access to a system via chat; agent creates a ticket and notifies the approver.

---

### 5.3 RAG — Internal Knowledge Base

| Feature | Specification |
|---|---|
| **Supported Source Types** | PDF, DOCX, Markdown, Confluence pages, HTML, plain text |
| **Ingestion Pipeline** | Automated document crawler → chunker → embedder → vector store |
| **Vector Store** | Self-hosted Weaviate or Qdrant |
| **Embedding Model** | `text-embedding-3-small` (OpenAI) or `nomic-embed` (local/offline option) |
| **Retrieval Strategy** | Hybrid: semantic similarity + keyword BM25 re-ranking |
| **Chunk Size** | 512 tokens with 64-token overlap |
| **Freshness** | Documents re-indexed nightly; manual re-index trigger available |
| **Source Citation** | Every retrieved chunk displayed with document name, section, and last-updated date |
| **Access Control** | Document-level ACLs: only retrieve chunks the requesting user has read access to |

---

### 5.4 Structured Database Queries

- The agent exposes a **read-only SQL tool** backed by SQLAlchemy.
- Natural language is translated to SQL by the LLM; queries are validated and executed in a sandboxed read-only connection.
- Supported query types: aggregations, lookups, joins across whitelisted tables.
- Query results are summarized in natural language with raw data available on demand.
- All generated SQL is logged and reviewable by administrators.
- Write operations (`INSERT`, `UPDATE`, `DELETE`) are strictly blocked at the connection level.

---

### 5.5 Jira Integration

| Action | Description |
|---|---|
| **Search tickets** | Find tickets by keyword, assignee, status, project, or date range |
| **Create ticket** | Create a new issue via chat; agent populates fields from conversation context |
| **Update ticket** | Change status, add comment, or reassign — with user confirmation before execution |
| **My tickets** | List all open tickets assigned to the authenticated user |
| **Sprint status** | Summarize current sprint progress for a given project or team |

---

### 5.6 Standalone Web Application

- Responsive single-page application (React + Tailwind CSS).
- Chat interface with message history, streaming responses, and source citation cards.
- User profile panel showing authenticated identity and active permissions.
- Admin dashboard (role-gated): view audit logs, manage document ingestion, monitor agent health.
- Keyboard shortcuts for power users; WCAG 2.1 AA accessibility compliance.

---

## 6. Non-Functional Requirements

| Category | Requirement | Target | Notes |
|---|---|---|---|
| **Performance** | Response latency (P95) | < 4 seconds | First token streamed < 1s |
| **Availability** | Uptime SLA | 99.5% | Excluding planned maintenance |
| **Security** | Data residency | 100% on-prem | No external API calls for user data |
| **Security** | Auth token validation | Every request | JWT verified on each API call |
| **Scalability** | Concurrent users | 200+ | Horizontal scaling via Kubernetes |
| **Audit** | Log retention | 12 months | All queries and tool calls logged |
| **Privacy** | PII handling | Masked in logs | Emails/names redacted in audit trail |
| **Compliance** | Access control | Row-level | RAG and DB filtered per user role |

---

## 7. Technical Architecture

### 7.1 Component Overview

| Component | Technology & Rationale |
|---|---|
| **Frontend** | React 18 + Tailwind CSS — Fast SPA, excellent component ecosystem |
| **Backend / API** | Python 3.12 + FastAPI — Async, high performance, best AI/ML library support |
| **Agent Framework** | LangGraph — Stateful multi-step agents with explicit tool routing and retry logic |
| **LLM** | Claude (Anthropic API, `claude-sonnet-4`) — Strong reasoning, 200K context, robust tool use |
| **Vector Store** | Weaviate (self-hosted) — Production-grade, multi-modal, supports hybrid search |
| **Embeddings** | `text-embedding-3-small` or `nomic-embed-text` (local) — Cost-effective, high quality |
| **Relational DB** | PostgreSQL — Agent metadata, audit logs, user feedback, session state |
| **Auth** | Keycloak (OIDC) — Existing org SSO; issues JWTs consumed by FastAPI middleware |
| **Jira** | Atlassian REST API v3 — Ticket CRUD via service account with scoped permissions |
| **Infra** | Docker Compose (dev) → Kubernetes (prod) — Portable, scalable deployment |
| **Observability** | OpenTelemetry + Grafana — Traces, metrics, and structured logs |

---

### 7.2 System Architecture Diagram

```
User (Browser)
     │
     ▼
React Web App  ──── Auth via Keycloak (OIDC/SSO)
     │
     ▼
FastAPI Backend (Orchestrator)
     │
     ├── LangGraph Agent
     │       ├── Tool: RAG Search  ──► Weaviate (internal docs)
     │       ├── Tool: DB Query    ──► PostgreSQL / internal DBs
     │       ├── Tool: Jira API    ──► Create / search tickets
     │       ├── Tool: IAM Lookup  ──► Keycloak / Okta / Azure AD
     │       └── Tool: Identity Context (injected on every request)
     │
     └── Claude API (LLM backbone)
```

---

### 7.3 Agent Tool Registry

The LangGraph agent selects from the following registered tools based on the user's query intent:

| Tool Name | Trigger Keywords / Intent | Backend Action |
|---|---|---|
| `rag_search` | "how do I", "what is our policy", "find doc about" | Embed query → hybrid search Weaviate → return top-k chunks |
| `db_query` | "how many", "show me all", "count", "list users" | NL → SQL → read-only PostgreSQL query → summarize result |
| `jira_search` | "find ticket", "open issues", "sprint status" | Jira REST API search with JQL |
| `jira_create` | "create ticket", "log a bug", "raise an issue" | Collect fields via conversation → POST to Jira with confirmation |
| `iam_lookup` | "who has access", "look up user", "check permissions" | Query Keycloak/AD API for user/group/role info |
| `identity_context` | Injected on every request | Decode JWT → enrich prompt with user role, department, groups |

---

### 7.4 Folder Structure (Proposed Repo)

```
org-agent/
├── frontend/                  # React + Tailwind SPA
│   ├── src/
│   │   ├── components/        # Chat UI, citation cards, auth
│   │   ├── hooks/             # useChat, useAuth, useStream
│   │   └── pages/             # Chat, Admin, Login
│   └── Dockerfile
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── agent/             # LangGraph agent, tool definitions
│   │   ├── api/               # FastAPI routes
│   │   ├── auth/              # Keycloak OIDC middleware
│   │   ├── rag/               # Document ingestion, Weaviate client
│   │   ├── db/                # SQLAlchemy models, audit logging
│   │   └── tools/             # jira.py, iam.py, sql.py, rag.py
│   ├── requirements.txt
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml     # Local dev stack
│   └── k8s/                   # Kubernetes manifests
├── scripts/
│   └── ingest_docs.py         # Document ingestion CLI
└── README.md
```

---

## 8. Security & Compliance

### 8.1 Authentication & Authorization

- All users must authenticate via SSO before accessing the agent. No anonymous access.
- JWTs are validated on every API request — expired or tampered tokens are rejected.
- Role-Based Access Control (RBAC): agent tool availability is gated by user roles (e.g., only IT Admins can run IAM lookup tools).
- Document-level ACLs are enforced at retrieval time — users cannot access RAG chunks from documents they do not have read permission on.

### 8.2 Data Security

- All data remains within the organization's self-hosted infrastructure.
- Communication between all internal services encrypted via TLS 1.3.
- Database connections use least-privilege service accounts with read-only permissions for agent queries.
- Secrets (API keys, DB credentials) managed via environment variables or a secrets manager (e.g., HashiCorp Vault).

### 8.3 Audit Logging

- Every agent interaction is logged: user ID, timestamp, query text, tools invoked, tool inputs/outputs, final response.
- Logs are immutable and stored in a dedicated audit table in PostgreSQL.
- PII (email addresses, names) is masked in logs by default; unmasked logs require elevated admin access.
- Log retention: 12 months minimum, configurable per compliance policy.

---

## 9. Phased Delivery Plan

| Phase | Scope | Timeline | Success Criteria |
|---|---|---|---|
| **Phase 1 — Foundation** | FastAPI backend + React chat UI + Keycloak SSO + Claude LLM + basic Q&A | Weeks 1–3 | Authenticated users can have a basic conversation with the LLM |
| **Phase 2 — RAG** | Document ingestion pipeline + Weaviate + RAG retrieval tool + source citation | Weeks 4–5 | Agent answers internal policy questions with cited sources |
| **Phase 3 — DB + Jira** | Read-only SQL agent tool + Jira search/create tools | Weeks 6–7 | Agent can query org DBs and create Jira tickets via chat |
| **Phase 4 — IAM Awareness** | User context injection from Keycloak/Azure AD + RBAC tool gating + IAM lookup tool | Week 8 | Agent responses are user-scoped; IAM queries work end-to-end |
| **Phase 5 — Production Polish** | Streaming responses, feedback loop, admin dashboard, audit logs, K8s deployment, observability | Weeks 9–11 | Production-ready deployment with full audit trail and monitoring |

---

## 10. Success Metrics

| Metric | Target (90 days post-launch) |
|---|---|
| Weekly Active Users | > 60% of target org population |
| Mean Time to Answer | < 30 seconds for 80% of queries |
| User Satisfaction (CSAT) | > 4.0 / 5.0 average rating |
| Jira Tickets Created via Agent | > 25% of total ticket volume |
| RAG Answer Relevance (human eval) | > 85% marked as relevant or highly relevant |
| Zero-result Rate | < 10% of queries return no useful answer |
| Security Incidents | 0 unauthorized data access events |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM hallucination on internal data | Medium | Enforce RAG grounding; block responses with no retrieved sources; add confidence thresholds |
| Unauthorized data access via agent | Low | JWT-scoped retrieval, document-level ACLs, read-only DB connections, RBAC on tools |
| Poor RAG quality from unstructured docs | Medium | Invest in document pre-processing pipeline; add human feedback loop to surface low-quality chunks |
| Slow adoption by employees | Medium | Embed agent in existing workflows (Jira, portals); run lunch-and-learn demos; gamify early usage |
| Jira API rate limits at scale | Low | Implement request queuing and caching for frequent Jira queries |
| Keycloak token expiry during long sessions | Low | Implement silent token refresh in frontend; session heartbeat mechanism |
| High LLM API costs at scale | Medium | Implement response caching for frequent queries; route simple queries to smaller/cheaper models |

---

## 12. Open Questions

- Should the agent support voice input in addition to text? *(Deferred to v2 pending demand signal.)*
- Which specific database tables and schemas will be whitelisted for agent queries? Requires data governance sign-off.
- Should users be able to configure personal preferences (e.g., response verbosity, default Jira project)?
- What is the escalation path when the agent cannot answer a query — route to a human, open a ticket, or both?
- Will Confluence be the primary doc source, or will SharePoint / Google Drive also be ingested?
- Is there a requirement to support offline / air-gapped operation? *(Impacts LLM choice — may need local model.)*

---

## 13. Appendix — Glossary

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation — grounding LLM responses in retrieved documents rather than parametric memory alone. |
| **LangGraph** | A Python framework for building stateful, multi-step LLM agents with explicit tool routing graphs. |
| **OIDC** | OpenID Connect — identity layer on top of OAuth2 used for SSO authentication. |
| **JWT** | JSON Web Token — signed token issued by Keycloak/Okta after authentication, containing user claims. |
| **RBAC** | Role-Based Access Control — restricting system access based on user roles. |
| **Vector Store** | A database optimized for storing and searching high-dimensional embeddings (e.g., Weaviate, Qdrant). |
| **Weaviate** | Open-source, self-hostable vector database with hybrid semantic + keyword search. |
| **Tool (Agent)** | A discrete function the LangGraph agent can invoke — e.g., `rag_search`, `jira_create`, `db_query`. |
| **Chunking** | Splitting long documents into smaller segments for embedding and retrieval. |
| **ACL** | Access Control List — per-document permissions determining which users/roles can retrieve its content. |

---

*PRD v1.0 — Internal Confidential — April 7, 2026*