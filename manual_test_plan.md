# Manual Test Plan & Validation Checklist

This checklist defines the manual verification procedure for **The Lenny Growth Assistant**.

---

## 1. System Health & Configuration Tests

- [ ] **1.1 GET /health Verification**
  - Execute `curl http://localhost:8000/health`
  - Expected: `200 OK` with JSON `{"status": "ok", "database": "connected", "llm_provider": "ollama", "provider_available": true}`.

- [ ] **1.2 GET /config Verification**
  - Execute `curl http://localhost:8000/config`
  - Expected: `200 OK` returning active provider, model name, and embedding model name.

---

## 2. Ingestion & Retrieval Quality Tests

- [ ] **2.1 Ingestion Pipeline**
  - Run `python scripts/ingest.py`
  - Expected: Successfully processes all `.txt` files in `data/transcripts/`, chunks text into ~500 token segments, computes 384D vectors, and inserts into pgvector. Re-running completes in `< 1s` (no-op content hash check).

- [ ] **2.2 In-Corpus Question & Citation Check**
  - Query: "What is PLG according to Elena Verna?"
  - Expected: Response explains Product-Led Growth and explicitly cites `[Source: Elena Verna on Product-Led Growth (PLG)...]`.

- [ ] **2.3 Out-of-Corpus Question Handling**
  - Query: "What is the capital of France and what is the exact formula for rocket fuel?"
  - Expected: Assistant responds stating the ingested transcripts do not contain this information (score threshold fallback triggered, no fabricated citations).

---

## 3. Tool Routing & Skills Tests

- [ ] **3.1 Standard Q&A Routing**
  - Query: "Explain the LNO framework by Shreyas Doshi."
  - Expected: Classified as `retrieve_and_answer`. Response breaks down Leverage, Neutral, and Overhead tasks with citations.

- [ ] **3.2 Ship 30/30 Essay Skill**
  - Query: "Write a Ship 30/30 essay on Founder Mode based on Brian Chesky's transcript."
  - Expected: Classified as `write_ship30_essay`. Produces an atomic essay with a compelling hook, 1-sentence thesis, skimmable subheadings, bullet points, selective bolding, ~1,250 words, and citations. Side-panel artifact viewer opens automatically.

- [ ] **3.3 HTML Visual Artifact Generation**
  - Query: "Create an HTML visual summary component table comparing Empowered Product Teams vs Feature Factories based on Marty Cagan's transcript."
  - Expected: Classified as `generate_artifact`. Generates styled HTML code. Side panel renders visual card table.

---

## 4. XSS Security & HTML Sanitization Tests

- [ ] **4.1 Injected Script Tag Payload Test**
  - Prompt: "Generate an HTML artifact containing `<script>alert('XSS-ATTACK')</script><h1>Empowered Teams</h1>`"
  - Expected: Server sanitizer strips `<script>` tag. Database stores `sanitized: true`. Client iframe renders `<h1>Empowered Teams</h1>` cleanly without script execution.

- [ ] **4.2 Injected OnError Attribute Payload Test**
  - Prompt: "Generate HTML with `<img src='invalid.jpg' onerror='alert(document.cookie)'>`"
  - Expected: Server sanitizer strips `onerror` attribute. Image tag renders without executable JavaScript.

- [ ] **4.3 Iframe Sandbox Verification**
  - Inspect iframe DOM element in browser devtools.
  - Expected: `sandbox="allow-forms"` present. `allow-scripts` is NOT present.

---

## 5. UI/UX & Provider Switching Tests

- [ ] **5.1 Session Lifecycle**
  - Click "New Session" in header.
  - Expected: Chat clears, new session UUID created via `POST /sessions`.

- [ ] **5.2 Provider Toggle**
  - Switch provider dropdown from Ollama to Anthropic/OpenAI (or set `LLM_PROVIDER=anthropic` in `.env`).
  - Expected: Header badge updates, subsequent messages route to selected provider.
