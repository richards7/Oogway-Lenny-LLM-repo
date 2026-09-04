# Demo Video Script & Presentation Outline

**Title**: The Lenny Growth Assistant — Grounded AI Product & Growth Partner  
**Target Duration**: 2:30 - 3:00 minutes  
**Format**: Screen Share + Camera Overlay  

---

## Part 1: Problem & Product Overview (0:00 - 0:45)
- **Speaker**: "Hi everyone! Product managers and growth leaders spend hours listening to podcasts like Lenny's Podcast for strategic nuggets, but turning those insights into shippable strategy documents or quick answers is tedious."
- **Screen**: Show Lenny Growth Assistant landing interface running locally on `localhost:3000`.
- **Key Points**: "We built **The Lenny Growth Assistant**—a full-stack, AI-powered assistant running completely locally via Ollama and pgvector. It ingests transcripts, answers questions with verifiable citations, generates Ship 30/30 atomic essays, and renders visual HTML artifacts safely."

---

## Part 2: Local Ollama & Grounded RAG Demo (0:45 - 1:30)
- **Action**: Type prompt into chat: *"What is Product-Led Growth (PLG) according to Elena Verna, and how does activation work?"*
- **Screen**: Show real-time streaming response, tool routing badge (`retrieve_and_answer`), and citation chips `[Source: Elena Verna on Product-Led Growth...]`.
- **Highlight**: Click on a citation chip to reveal the exact transcript snippet and cosine similarity score. Show `GET /config` header showing zero-cloud-key Ollama `llama3.1:8b` execution.

---

## Part 3: Ship 30/30 Skill & Visual Artifact Viewer (1:30 - 2:15)
- **Action**: Type prompt: *"Write a Ship 30/30 essay on Founder Mode based on Brian Chesky's episode."*
- **Screen**: Tool router selects `write_ship30_essay`. Side panel opens displaying the structured atomic essay (Hook, Thesis, Skimmable Subheadings, Bullet Points, Citations).
- **Action**: Type prompt: *"Generate an HTML visual table comparing Empowered Teams vs Feature Factories."*
- **Screen**: Artifact Viewer displays rendered HTML inside a sandboxed iframe. Toggle "View Source" to show sanitized clean markup and security model.

---

## Part 4: Technical Architecture & Trade-Offs (2:15 - 2:45)
- **Screen**: Show `architecture.md` / `docker-compose.yml`.
- **Key Points**: 
  - Single Postgres instance with `pgvector` for simplicity & single-port deployment.
  - Server-side tool-routing classifier step ensuring reliable function dispatch.
  - HTML security model: strict server sanitization + sandboxed `<iframe>` without `allow-scripts`.
  - Seamless fallback between local Ollama and Anthropic/OpenAI providers.

---

## Part 5: Outro & Repo Summary (2:45 - 3:00)
- **Speaker**: "The entire project is open-source, fully tested with automated pytest suites, and ready to spin up with `docker-compose up`. Thanks for watching!"
