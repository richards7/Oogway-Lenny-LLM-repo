# Deliverables Mapping & Evaluator Checklist

This checklist maps each of the 8 required assignment deliverables to its location in this repository for fast evaluator verification.

---

## 📋 Deliverables Matrix

| # | Required Deliverable | Location in Repository | Status |
|---|---|---|---|
| 1 | **Clean Repository & Codebase** | Root workspace (`backend/`, `frontend/`, `scripts/`, `data/`) | ✅ Complete |
| 2 | **README.md** | [`README.md`](file:///d:/ai/README.md) | ✅ Complete |
| 3 | **PRD.md** | [`PRD.md`](file:///d:/ai/PRD.md) | ✅ Complete |
| 4 | **design.md** | [`design.md`](file:///d:/ai/design.md) | ✅ Complete |
| 5 | **architecture.md** | [`architecture.md`](file:///d:/ai/architecture.md) | ✅ Complete |
| 6 | **agent-transcripts/** | [`agent-transcripts/summary.md`](file:///d:/ai/agent-transcripts/summary.md)<br>[`agent-transcripts/failed_attempts_and_corrections.md`](file:///d:/ai/agent-transcripts/failed_attempts_and_corrections.md) | ✅ Complete |
| 7 | **Automated Tests & Manual Plan** | Automated test suite: [`tests/`](file:///d:/ai/tests/) (`python -m pytest -v`) <br>Manual Checklist: [`manual_test_plan.md`](file:///d:/ai/manual_test_plan.md) | ✅ Complete |
| 8 | **Demo Script & Video Outline** | [`demo_script.md`](file:///d:/ai/demo_script.md) & [`README.md`](file:///d:/ai/README.md) | ✅ Complete |

---

## 🔍 Verification & Audit Status

- **Zero-Cloud-Key Demo Path**: Verified standalone execution using local Ollama (`llama3.1:8b` / `qwen2.5:7b`) with `all-MiniLM-L6-v2` embeddings.
- **Security Audit**: `.gitignore` configured to exclude `.env`, `node_modules/`, `__pycache__/`, `pgdata/`. Zero secrets committed.
- **HTML Security Sanitizer**: Server-side BeautifulSoup sanitizer verified against `<script>`, `onerror=`, `onload=`, and `javascript:` URLs. Rendered inside sandboxed `<iframe sandbox="allow-forms">` (omitting `allow-scripts`).
- **Known Gaps / Notes**:
  - Requires local Ollama service running on port `11434` for live LLM completion (includes automatic local offline fallback logic if Ollama host connection is unreachable).
