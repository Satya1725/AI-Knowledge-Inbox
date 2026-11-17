# AI Knowledge Inbox
Save notes and URLs, then ask questions about them. Answers are generated from your saved content and cite their sources.

- **Frontend:** React + TypeScript + Vite + Tailwind
- **Backend:** FastAPI + SQLite + OpenAI / Gemini

---

## Setup

### Option A: Docker (one command)

```bash
copy backend\.env.example backend\.env     # macOS/Linux: cp backend/.env.example backend/.env
# add OPENAI_API_KEY or GEMINI_API_KEY to backend/.env
docker compose up --build
```

Open http://localhost:8080. The API is also exposed at http://localhost:8000, with Swagger docs at `/docs`. Data is kept in the `inbox-data` volume. `docker compose down -v` wipes it.

### Option B: Run locally

You need Python 3.10+, Node 20+, and an OpenAI and/or Gemini API key.

**1. Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
```

Open `backend/.env` and add **one** key: OpenAI **or** Gemini. Adding both is fine too.

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
EMBEDDING_PROVIDER=openai         # preferred provider; if it has no key, the other one is used
CHAT_PROVIDER=openai
```

If both keys are set, the UI shows an **OpenAI / Gemini** switch for answers.

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

**3. Tests (optional)**

```bash
cd backend
pytest
```

The tests use a fake AI provider, so they need no API key.

---

## How it works

**Saving a note or URL**

1. `POST /ingest` saves the item and returns immediately (`202`, status `processing`).
2. A background task then does the rest:
   - For a URL, it downloads the page and keeps only the readable text.
   - It splits the text into chunks.
   - It creates an embedding for each chunk.
   - It stores the chunks and vectors in SQLite.
3. The item becomes `ready`, or `failed` with a readable reason. The UI polls and shows this live.

**Asking a question**

1. `POST /query` embeds the question.
2. It compares the question with every stored chunk (cosine similarity) and keeps the top 5.
3. The chunks are sent to the LLM as numbered sources `[1]`, `[2]`, and so on, with instructions to answer only from them and cite them.
4. The UI shows the answer with clickable citations and the source snippets.

If nothing relevant is found, the API says so and skips the LLM call.

**API**

| Method | Path | Purpose |
|---|---|---|
| POST | `/ingest` | Save a note `{type:"note", text}` or a URL `{type:"url", url}` |
| GET | `/items` | List saved items |
| DELETE | `/items/{id}` | Delete an item |
| POST | `/items/{id}/reindex` | Re-fetch and re-index an item (also retries a failed one) |
| POST | `/query` | Ask a question `{question, provider?}` and get an answer with sources |
| GET | `/providers` | List which AI providers are configured |

Errors always look like `{"error": {"code", "message"}}`, with sensible status codes: `422` for bad input, `404` for an unknown item, `502` when the AI API fails, and `503` when a key is missing. Logs are JSON, and every request has an `X-Request-ID`.

**Backend layout**

```
backend/app/
  main.py          app setup, logging, error handlers
  routes/          HTTP endpoints (thin)
  services/        chunking, fetcher, ingestion, retrieval, answering
  ai/              OpenAI + Gemini providers behind one interface
  repository.py    all SQL
```

---

## Try it: sample data

👉 **[TESTING.md](TESTING.md)** has the full UI test script: 4 notes with titles, URLs, questions with expected answers, the notification and loading states to look for, and error cases.

A quick example. **Sample note** (paste into the Note tab):

```
Project Falcon – kickoff notes

The launch date for Project Falcon is March 14. Priya owns the backend API and Marcus owns the mobile app.
Budget is capped at $40,000 for Q1.

Decisions: we are using PostgreSQL instead of MongoDB because we need strong consistency for payments.
The weekly sync is every Tuesday at 11am.

Risks: the payment provider's sandbox is unstable, and the design team is two weeks behind on onboarding screens.
```

**Sample URLs** (paste into the URL tab):

- https://en.wikipedia.org/wiki/Retrieval-augmented_generation
- https://en.wikipedia.org/wiki/Vector_database
- https://paulgraham.com/greatwork.html

**Questions to try:**

- When is Project Falcon launching and who owns the backend?
- Why did the team choose PostgreSQL?
- What are the risks for Project Falcon?
- What problem does retrieval-augmented generation solve?
- How do vector databases find similar items?
- What is the capital of France? (should answer that it isn't in your saved content)

---

## Why the chunking works this way

- **Split by paragraph first.** A paragraph is usually one idea, so chunks stay readable and make clean snippets in the UI.
- **Pack small paragraphs together,** up to about 800 characters (~200 tokens). A short note doesn't become many weak, tiny vectors.
- **Split long paragraphs by sentence.** Text with no sentence breaks at all gets hard-cut.
- **Overlap of 150 characters.** A fact that sits on a chunk boundary can still be found from either side.
- **Characters, not tokens.** This avoids a tokenizer dependency and is close enough for English text.

## Why this vector store

Vectors live in **SQLite** next to the text, and search is a **brute-force cosine** comparison in numpy.

- One file, no extra service, nothing to deploy.
- Deleting an item also deletes its chunks (foreign key cascade).
- Vectors are normalised when saved, so search is a single matrix multiplication. That takes milliseconds for a few thousand chunks.
- Each chunk records which embedding model created it. If you switch from OpenAI to Gemini embeddings, the two are never mixed.

## What breaks at scale

| Problem | Why |
|---|---|
| Search gets slower as content grows | Every query loads and compares every vector |
| Background jobs are lost on restart | They run inside the API process, with no queue and no retries |
| Slow concurrent writes | SQLite allows only one writer at a time |
| Some URLs return nothing | Pages that need JavaScript or a login can't be read |
| URL fetching isn't locked down | It could reach internal addresses (SSRF) |
| Long questions over lots of content | No token budget is applied to the prompt |
| Provider rate limits | Large pages trigger many embedding calls, with no throttling |

## What I'd change for production

1. **Vector index:** move to pgvector or Qdrant (approximate search) instead of brute force.
2. **Job queue:** Redis + Celery/Arq for ingestion, with retries.
3. **Postgres** instead of SQLite.
4. **Better retrieval:** hybrid keyword + vector search, plus a reranker.
5. **Streaming answers** so text appears as it is generated.
6. **Security:** block private IPs when fetching URLs, add rate limiting, and add auth with per-user data.
7. **Monitoring:** tracing across fetch → embed → LLM, plus token and cost tracking.
8. **Evals:** a small set of test questions with expected sources, to catch quality regressions.
