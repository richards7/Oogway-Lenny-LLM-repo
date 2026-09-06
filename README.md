# The Lenny Growth Assistant 🚀

A full-stack, AI-powered conversational web application built from scratch to ingest **Lenny's Podcast transcripts** into a grounded `pgvector` knowledge base, answer product and growth strategy questions with verifiable citations, generate **Ship 30/30-style atomic essays** via a dedicated skill tool, and produce self-contained Markdown and HTML visual artifacts rendered in a secure, in-app sandboxed Artifact Viewer.

Runs locally via **Ollama** (`llama3.1:8b` / `qwen2.5:7b`) with **zero cloud keys**, and seamlessly switches to cloud providers (**Anthropic Claude** or **OpenAI GPT-4o**) via configuration.

---

## 🛠 What We Built From Scratch

### 1. Database & Vector Storage (PostgreSQL + `pgvector`)
- **Unified Schema**: Implemented tables for `sessions`, `messages`, `sources`, `chunks`, and `artifacts` with `ON DELETE CASCADE` integrity constraints.
- **pgvector Cosine Search**: Configured an `ivfflat` index on 384-dimensional vector embeddings utilizing `vector_cosine_ops` for fast similarity search (`1 - (embedding <=> query_vec)`).

### 2. Ingestion & Embedding Pipeline
- **Transcript Seed Data**: Created 6 structured podcast episode transcripts covering Product-Led Growth (Elena Verna), Product Sense & LNO Framework (Shreyas Doshi), Founder Mode & Craft (Brian Chesky), Empowered Product Teams (Marty Cagan), SPADE Decision Framework (Gokul Rajaram), and Growth Loops & Retention (Lenny Rachitsky).
- **Text Chunker**: Built `scripts/ingest.py` splitting text into ~500 token segments with ~50 token overlap, preserving ordinal chunk positions for traceability.
- **Local Embedding Engine**: Integrated `sentence-transformers/all-MiniLM-L6-v2` generating 384D vector embeddings. Uses content hashing (MD5) for idempotent no-op re-runs.

### 3. FastAPI Backend & Services
- **Multi-Provider LLM Abstraction**: Unified `ChatProvider` supporting local `OllamaProvider` (default required demo path), `AnthropicProvider`, and `OpenAIProvider`. Includes local heuristic fallback handling if Ollama host is offline.
- **Server-Side Tool Classifier**: Deterministic intent router classifying prompts into `retrieve_and_answer`, `write_ship30_essay`, or `generate_artifact`.
- **Ship 30/30 Essay Skill**: Encodes Ship 30/30 principles producing atomic essays (~1,250 words ±15%, hook, single thesis takeaway, skimmable subheadings, bullet points, selective bolding, grounded citations).
- **HTML Security Sanitizer**: Built `sanitizer.py` using BeautifulSoup to strip `<script>`, `<style>`, inline event handlers (`onerror=`, `onload=`), and `javascript:`/`data:` schemes.
- **Auto-Initialization**: Startup `lifespan` handler automatically initializes `pgvector` extensions and triggers seed ingestion on fresh container launches.

### 4. React + Vite Frontend Workspace
- **Glassmorphism Dark Theme**: Designed a custom visual system using HSL dark tokens, subtle borders, and smooth backdrop blurs (`index.css`).
- **Header Component**: Live provider status indicator, active model selector, corpus index status, and session manager (`Header.jsx`).
- **Chat Window**: Renders message history, Markdown formatting, tool execution badges, and interactive citation chips with snippet details modal (`ChatWindow.jsx`).
- **Artifact Viewer**: Side-by-side panel featuring Rendered vs View Source tab toggle and sandboxed `<iframe sandbox="allow-forms">` strictly without `allow-scripts` (`ArtifactViewer.jsx`).

### 5. Automated Test & Verification Suite
- **17/17 Passing Pytest Tests**: Comprehensive test suite in `tests/` covering:
  - `test_retrieval.py`: Semantic retrieval similarity ($>0.50$) & negative out-of-corpus thresholding ($<0.30$).
  - `test_classifier.py`: Tool router classifier accuracy.
  - `test_sanitizer.py`: HTML security filter & XSS vector neutralization.
  - `test_persistence.py`: ORM model instantiation & real PostgreSQL round-trip CRUD (`@pytest.mark.db`).
  - `test_api.py` & `test_acceptance_criteria.py`: End-to-end HTTP route execution and consistent error envelopes.

---

## 📚 Documentation Index
- **[PRD.md](file:///d:/ai/PRD.md)** — Product Requirements Document & Persona Specs
- **[architecture.md](file:///d:/ai/architecture.md)** — System Architecture, DB Schemas, & API Contracts
- **[design.md](file:///d:/ai/design.md)** — UI/UX Design System, Layout, & Accessibility Specs
- **[manual_test_plan.md](file:///d:/ai/manual_test_plan.md)** — Step-by-Step Manual Validation Checklist
- **[demo_script.md](file:///d:/ai/demo_script.md)** — 2-3 Minute Video Walkthrough Outline & Script
- **[CHECKLIST.md](file:///d:/ai/CHECKLIST.md)** — Evaluator Deliverables Location Mapping
- **[agent-transcripts/](file:///d:/ai/agent-transcripts/)** — Coding Agent Execution Logs & Corrections Log

---

## 🌟 Key Product Features

1. **Grounded RAG with Citations**: $\ge 90\%$ of factual answers include resolvable transcript chunk citations `[Source: Title (chunk: X)]`. Low-confidence retrieval queries trigger an explicit non-coverage fallback to prevent hallucination.
2. **Server-Side Tool Router**: A deterministic classifier routes user prompts to specialized tools (`retrieve_and_answer`, `write_ship30_essay`, `generate_artifact`).
3. **Sandboxed Artifact Viewer**: Renders Markdown and HTML artifacts side-by-side with the chat. HTML is sanitized server-side and rendered in a sandboxed `<iframe sandbox="allow-forms">` strictly without `allow-scripts`.
4. **Pluggable Model Providers**: Abstract `ChatProvider` interface supporting local `OllamaProvider` (default), `AnthropicProvider`, and `OpenAIProvider`.
5. **PostgreSQL + pgvector**: Unified database schema storing sessions, messages, sources, chunks with an `ivfflat` cosine similarity index, and artifacts.

---

## ⚙️ Environment Variables Reference

| Variable | Description | Default Value |
|---|---|---|
| `POSTGRES_DB` | PostgreSQL Database Name | `lenny_growth` |
| `POSTGRES_USER` | PostgreSQL User Name | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL User Password | `postgres` |
| `DATABASE_URL` | Async SQLAlchemy PostgreSQL Connection URL | `postgresql+asyncpg://postgres:postgres@localhost:5433/lenny_growth` |
| `SYNC_DATABASE_URL` | Sync psycopg Connection URL (for ingestion script) | `postgresql+psycopg://postgres:postgres@localhost:5433/lenny_growth` |
| `LLM_PROVIDER` | Active LLM Provider (`ollama`, `anthropic`, `openai`) | `ollama` |
| `OLLAMA_BASE_URL` | Local Ollama Service REST API Base URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Primary Local Ollama Model | `llama3.1:8b` |
| `OLLAMA_FALLBACK_MODEL` | Fallback Local Ollama Model | `qwen2.5:7b` |
| `ANTHROPIC_API_KEY` | Optional Anthropic API Key | `""` (Empty string for zero-key demo) |
| `ANTHROPIC_MODEL` | Anthropic Model Name | `claude-3-5-sonnet-20241022` |
| `OPENAI_API_KEY` | Optional OpenAI API Key | `""` (Empty string for zero-key demo) |
| `OPENAI_MODEL` | OpenAI Model Name | `gpt-4o` |
| `EMBEDDING_MODEL` | Local Vector Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| `RETRIEVAL_TOP_K` | Vector Retrieval Top-K Results | `6` |
| `RETRIEVAL_SIMILARITY_THRESHOLD` | Minimum Grounding Cosine Similarity Threshold | `0.30` |

---

## 🚀 Quickstart Guide

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-username/lenny-growth-assistant.git
cd lenny-growth-assistant

# Copy environment variables (zero cloud keys required by default)
cp .env.example .env
```

### 2. Launch Services via Docker Compose
```bash
docker compose up -d
```
This spins up:
- `lenny_postgres`: PostgreSQL 16 with `pgvector` extension enabled on port `5433`.
- `lenny_backend`: FastAPI app running on `http://localhost:5001` (auto-ingests seed transcripts on startup if DB is empty).
- `lenny_frontend`: Vite React app served via Nginx on `http://localhost:3001`.

---

## 💻 Local Ollama Setup (Zero Cloud Keys Demo Path)

1. Download and install Ollama from [ollama.ai](https://ollama.ai).
2. Pull the default demo model:
   ```bash
   ollama pull llama3.1:8b
   # Fallback model:
   ollama pull qwen2.5:7b
   ```
3. Ensure Ollama is running on `http://localhost:11434`.
4. Verify backend health and active provider:
   ```bash
   curl http://localhost:5001/health
   curl http://localhost:5001/config
   ```

---

## ☁️ Cloud Model Configuration (Optional)

To switch to Anthropic or OpenAI, edit `.env`:
```env
# Switch active provider
LLM_PROVIDER=anthropic

# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

---

## 🧪 Running Automated Tests

Run fast unit-only tests (excluding external DB integration):
```bash
python -m pytest -m "not db" -v
```

Run full test suite (including PostgreSQL round-trip tests when DB is running):
```bash
python -m pytest -v
```
*Note: DB integration tests automatically skip if PostgreSQL is not reachable on `TEST_DATABASE_URL`.*

---

## ❓ Troubleshooting Guide

### 1. Ollama Not Running locally
- **Symptom**: `/health` reports `provider_available: false` or Ollama logs error.
- **Fix**: Start the Ollama application or daemon (`ollama serve`). If running backend in Docker Compose, ensure `OLLAMA_BASE_URL=http://host.docker.internal:11434` is set in `.env` so container connects to host Ollama service.
- **Fallback**: The backend automatically falls back to grounded offline heuristic responses if Ollama is unreachable, preventing HTTP 500 crashes.

### 2. Missing PostgreSQL Connection
- **Symptom**: `GET /health` returns HTTP 503 `DATABASE_UNAVAILABLE`.
- **Fix**: Check that PostgreSQL container is running (`docker compose ps`). Ensure port 5433 is not blocked by another local Postgres instance.

### 3. Missing Cloud Key Fallback Behavior
- **Symptom**: User selects `anthropic` or `openai` in `.env` without providing `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.
- **Fix**: API returns a structured HTTP 400 validation error envelope (`"ANTHROPIC_API_KEY is not configured"`). Switch `LLM_PROVIDER=ollama` in `.env` or select Ollama in the UI header dropdown.

### 4. Empty Retrieval Results / Non-Coverage Refusal
- **Symptom**: Query returns "I searched Lenny's Podcast transcripts, but could not find relevant content..."
- **Fix**: This is expected behavior for out-of-corpus queries (retrieval similarity $< 0.30$). For grounded answers, query topics covered in the transcripts (PLG, Product Sense, Founder Mode, Empowered Product Teams, SPADE Framework, Growth Loops).

---

## 📄 License
MIT License. Built for Forward-Deployment Engineering.

