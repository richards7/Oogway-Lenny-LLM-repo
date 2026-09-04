# Product Requirements Document (PRD): The Lenny Growth Assistant

## Executive Summary
**The Lenny Growth Assistant** is a full-stack, AI-powered conversational web application designed for Product Managers, Growth Practitioners, and Founders. It ingests Lenny's Podcast transcripts into a pgvector-powered grounded knowledge base, answers product and growth strategy questions with verifiable transcript citations, generates Ship 30/30-style atomic essays via a dedicated skill tool, and renders self-contained Markdown and HTML visual artifacts in a secure, sandboxed side-panel viewer.

---

## 1. User & Persona
- **Primary Persona**: Product Manager / Growth Lead / Founder seeking fast, authoritative, cited growth insights without re-listening to hour-long podcast episodes.
- **Secondary Goal**: Transform retrieved insights into shippable, skimmable written content (atomic essays, strategy memos) or visual HTML/CSS components.

---

## 2. Key Success Metrics
1. **Citation Accuracy & Grounding**: $\ge 90\%$ of factual-claim responses contain a valid, resolvable citation to an ingested transcript chunk `[Source: Title (chunk X)]`.
2. **Hallucination Prevention**: If retrieval similarity score is below threshold ($<0.30$), the system explicitly states that the transcripts do not cover the topic.
3. **Response Latency**: P95 latency $< 8\text{s}$ on local Ollama config (`llama3.1:8b` / `qwen2.5:7b`) for standard RAG turns.
4. **Security**: Zero script execution or XSS vulnerabilities in HTML artifact rendering.

---

## 3. Scope & System Boundaries

### In Scope
- Single-tenant, no-authentication session management via UUIDs.
- Local vector database using PostgreSQL + `pgvector`.
- Local vector embeddings via `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Multi-provider LLM support: `OllamaProvider` (default demo path), `AnthropicProvider`, `OpenAIProvider`.
- Server-side tool-routing classifier selecting `retrieve_and_answer`, `write_ship30_essay`, or `generate_artifact`.
- Ship 30/30 Atomic Essay generation skill (~1,250 words ±15%, hook, skimmable formatting, grounded citations).
- Server-side HTML security sanitization stripping scripts, inline events, and unsafe schemes.
- Client-side sandboxed iframe rendering (`sandbox="allow-forms"`) with dual View/Source toggle.
- Structured JSON logging.

### Out of Scope
- Multi-tenant user login / authentication / RBAC.
- Payment processing or subscription billing.
- Live automatic transcript scraping or cron scheduling.
- Model fine-tuning.
- Mobile native apps.

---

## 4. Acceptance Criteria
1. **Health Check (`GET /health`)**: Returns `200 OK` with database connection state and active LLM provider health status.
2. **Session Creation (`POST /sessions`)**: Returns a valid UUID `session_id`.
3. **Conversational RAG (`POST /sessions/{id}/messages`)**: Answers product questions, includes citations, and streams/returns assistant messages.
4. **Ship 30/30 Skill**: When requested, produces a structured atomic essay following the Ship 30/30 template grounded in retrieved chunks.
5. **Artifact Viewer**: Renders Markdown and sanitized HTML visual artifacts in the side panel. Unsafe script tags in generated HTML are stripped (`sanitized: true`).
6. **Provider Toggle**: Switching `LLM_PROVIDER` in environment or UI updates the model pipeline seamlessly.
