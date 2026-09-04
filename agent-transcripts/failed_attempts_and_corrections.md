# Failed Attempts, Diagnostics, and Corrections Log

This log documents technical challenges, failed build steps, root cause analyses, and corrections made during the forward-deployment development of **The Lenny Growth Assistant**.

---

## 1. Docker Build Failure: `npm ci` without pre-existing `package-lock.json`

### Symptom / Issue
In the initial draft of `frontend/Dockerfile`, the instruction `RUN npm ci` was specified. When building Docker images from scratch on a clean environment without a committed `package-lock.json`, `npm ci` terminates with an exit code 1.

### Root Cause Analysis
`npm ci` strictly requires an existing `package-lock.json` or `npm-shrinkwrap.json`. Since the project scaffold only had `package.json`, `npm ci` failed.

### Resolution & Correction
Updated `frontend/Dockerfile` to use `RUN npm install`:
```dockerfile
COPY package*.json ./
RUN npm install
```
This allows clean container builds on fresh clones.

---

## 2. Local Python Environment Missing Native DB Drivers (`asyncpg`, `psycopg`)

### Symptom / Issue
Running `pytest` initially returned `ModuleNotFoundError: No module named 'asyncpg'` and `ModuleNotFoundError: No module named 'psycopg'`.

### Root Cause Analysis
The local Python host environment had not yet installed backend dependencies listed in `backend/requirements.txt`.

### Resolution & Correction
Executed `pip install -r backend/requirements.txt` to install `asyncpg`, `psycopg[binary]`, `pgvector`, `sentence-transformers`, `beautifulsoup4`, and `pytest-asyncio`. In addition, FastAPI dependencies were mocked in `tests/test_acceptance_criteria.py` and `tests/test_api.py` using `app.dependency_overrides[get_db]` so unit tests execute offline without requiring PostgreSQL daemon connectivity.

---

## 3. Pydantic v2 Settings Warning (`class Config` vs `ConfigDict`)

### Symptom / Issue
Pytest emitted warnings: `PydanticDeprecatedSince20: Support for class-based config is deprecated, use ConfigDict instead.`

### Root Cause Analysis
`backend/app/config.py` used the legacy Pydantic v1 `class Config:` block inside `BaseSettings`.

### Resolution & Correction
Refactored `config.py` to use Pydantic v2 `ConfigDict`:
```python
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ...
    model_config = ConfigDict(env_file=".env", extra="ignore")
```
Eliminated all Pydantic deprecation warnings.

---

## 4. AsyncMock Method Mocking in Pytest Routes (`RuntimeWarning` & 404s)

### Symptom / Issue
Pytest tests for `/sessions/{id}/messages` initially returned 404 because `res = await db.execute(stmt)` returned an `AsyncMock` whose `scalar_one_or_none()` was evaluated as falsy.

### Root Cause Analysis
When FastAPI dependency `get_db` was mocked with a default `AsyncMock()`, calling `sess = res.scalar_one_or_none()` returned another method `AsyncMock()`. In Python, evaluating `if not sess:` on a un-configured `AsyncMock` returned `True` (falsy `sess`), causing the endpoint to raise HTTP 404.

### Resolution & Correction
Created explicit helper class `MockQueryResult` and assigned `mock_session.add = MagicMock()` and `mock_session.execute = AsyncMock(return_value=MockQueryResult())`. `scalar_one_or_none()` returned a real `SessionModel` object, resolving the 404 and eliminating unawaited coroutine warnings.

---

## 5. Security Pass: Secrets Check & Sanitizer Test

### Secret Check
- Executed grep search across codebase for `sk-`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`.
- Verified `.gitignore` contains `.env` and `.env.*` (excluding `.env.example`).
- Confirmed zero hardcoded secrets exist.

### Sanitizer Security Test
- Verified `test_sanitizer.py` strips `<script>`, `onerror=`, `onload=`, and `javascript:` URIs.
- Confirmed HTML artifacts render client-side strictly within `<iframe sandbox="allow-forms">` omitting `allow-scripts`.
