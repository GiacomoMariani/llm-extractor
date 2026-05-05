# LLM Extractor

A practical FastAPI backend for AI application patterns: structured extraction, classification, summarization, document ingestion, document Q&A with citations, tool-using assistant workflows, evaluation runs, and basic usage tracking.

This project is intentionally built as a learning-to-production bridge. It avoids large framework magic and keeps the core application pieces visible: request models, service boundaries, storage, background ingestion, retrieval, evaluation, and observability hooks.

---

## Table of Contents

- [What This Project Demonstrates](#what-this-project-demonstrates)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running with Docker](#running-with-docker)
- [API Authentication](#api-authentication)
- [API Reference](#api-reference)
- [Document Q&A Workflow](#document-qa-workflow)
- [Tool Assistant Workflow](#tool-assistant-workflow)
- [Evaluation](#evaluation)
- [Usage and Cost Tracking](#usage-and-cost-tracking)
- [Testing](#testing)
- [Persistence](#persistence)
- [Operational Notes](#operational-notes)
- [Known Limitations](#known-limitations)
- [Suggested Roadmap](#suggested-roadmap)

---

## What This Project Demonstrates

`llm-extractor` is a compact backend service that demonstrates the core skills needed to build real LLM-powered products:

- API design with FastAPI and Pydantic validation
- structured JSON output from text
- deterministic rule-based model substitutes for local development and tests
- document ingestion and chunking
- local embedding-based retrieval
- hybrid vector + keyword search
- grounded document answers with citations
- background ingestion job lifecycle
- tool-calling style assistant behavior
- human-in-the-loop approval before side-effecting actions
- SQLite-backed persistence for documents, jobs, evaluations, and usage records
- basic request logging, request IDs, health checks, and Docker packaging

The current implementation is still a learning/portfolio backend, not a fully production-hardened service.

---

## Features

### Core Text Endpoints

- `POST /extract` — extracts structured fields from support text.
- `POST /classify` — classifies text into `billing`, `technical`, `refund`, or `general`.
- `POST /summarize` — returns a short summary from input text.
- `POST /answer` — answers a question from supplied context.
- `POST /route` — routes user input to a likely task type.
- `POST /chat` — returns a simple assistant reply.

### Document Q&A

- Upload `.txt` documents.
- Create ingestion jobs.
- Process ingestion in FastAPI background tasks.
- Store documents and chunks in SQLite.
- Generate local embeddings with `sentence-transformers`.
- Retrieve relevant chunks using hybrid vector and keyword scoring.
- Return grounded answers with citation snippets and retrieval scores.

### Tool Assistant

- Looks up order status.
- Checks refund eligibility.
- Creates pending refund requests.
- Requires confirmation before submitting a refund request.
- Records tool calls in the response.

### Evaluation and Observability

- Document Q&A evaluation script.
- Extraction evaluation script.
- Stored latest document Q&A evaluation run.
- Usage records for document embedding and document answering.
- Basic cost estimation.
- Request logging middleware with `X-Request-ID` support.
- Docker health check.

---

## Architecture Overview

The application follows a simple layered structure:

```text
HTTP routes
  ↓
Pydantic request/response models
  ↓
Service layer
  ↓
Providers, tools, stores, and clients
  ↓
SQLite / local model / external HTTP API where configured
```

Key design choices:

1. **Routes stay thin.**
   FastAPI route handlers validate input, call services, translate application errors into HTTP errors, and return response models.

2. **Services contain application behavior.**
   Extraction, classification, summarization, answering, ingestion, retrieval, tool use, evaluation, and usage tracking are separated into service modules.

3. **Rule-based components make the project testable.**
   The current system uses deterministic local implementations for many model-like behaviors. This keeps tests predictable and avoids requiring a paid model API during development.

4. **Document Q&A is grounded.**
   Answers are generated from retrieved document chunks and returned with citations containing chunk IDs, snippets, vector scores, keyword scores, and hybrid scores.

5. **Background ingestion is abstracted.**
   The current queue implementation uses FastAPI `BackgroundTasks`, but the `DocumentIngestionQueue` protocol creates a boundary where a durable queue can later be added.

---

## Project Structure

```text
.
├── main.py                              # FastAPI app, route definitions, dependencies
├── auth.py                              # API key dependency
├── settings.py                          # Environment-based settings
├── Dockerfile                           # Container image definition
├── requirements.txt                     # Python dependencies
├── models/                              # Pydantic request/response models
├── services/                            # Application services and persistence
├── providers/                           # Embedding/model provider abstractions
├── clients/                             # External/local order API clients
├── tools/                               # Tool functions used by the assistant
├── evals/                               # Evaluation case definitions
├── scripts/                             # Evaluation runners
└── tests/                               # API, unit, and client tests
```

Important files:

| File | Purpose |
|---|---|
| `main.py` | Defines the FastAPI app, middleware, dependencies, and HTTP routes. |
| `auth.py` | Enforces `X-API-Key` authentication for protected endpoints. |
| `services/document_ingestion_service.py` | Chunks uploaded documents, embeds chunks, stores documents, and records usage. |
| `services/document_ingestion_worker.py` | Manages ingestion job status transitions. |
| `services/ingestion_queue.py` | Defines the ingestion queue protocol and FastAPI background-task implementation. |
| `services/retrieval_service.py` | Performs hybrid vector + keyword retrieval. |
| `services/document_answering_service.py` | Retrieves chunks, answers questions, and returns citations. |
| `services/tool_assistant_service.py` | Implements order-status and refund-assistant workflow logic. |
| `services/usage_tracking_service.py` | Records estimated token usage and estimated cost. |
| `services/evaluation_result_store.py` | Persists document Q&A evaluation summaries and case results. |

---

## Requirements

- Python 3.12 recommended
- FastAPI
- Uvicorn
- Pydantic
- python-multipart
- sentence-transformers
- pytest
- httpx

The application uses `sentence-transformers/all-MiniLM-L6-v2` by default for local document embeddings. The first run may download the model.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/GiacomoMariani/llm-extractor.git
cd llm-extractor
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure an API key

```bash
export APP_API_KEY="dev-secret-key"
```

On Windows PowerShell:

```powershell
$env:APP_API_KEY="dev-secret-key"
```

### 5. Run the API

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

## Configuration

Environment variables:

| Variable | Default | Purpose |
|---|---:|---|
| `APP_API_KEY` | none | Required for protected endpoints. Requests must send this value in `X-API-Key`. |
| `APP_DB_PATH` | `app.db` | SQLite database path for documents, chunks, ingestion jobs, evaluations, and usage records. |
| `EXTRACTOR_TYPE` | `rule` | Extraction backend. Supported values include `rule`, `mock_llm`, and `mock_llm_json`. |
| `ORDER_CLIENT_TYPE` | `local` | Order client backend. Supported values: `local`, `http`, `http_with_fallback`. |
| `ORDER_API_BASE_URL` | none | Required when using `ORDER_CLIENT_TYPE=http` or `http_with_fallback`. |
| `ORDER_API_KEY` | none | Optional bearer token for the external order API client. |

Example local development configuration:

```bash
export APP_API_KEY="dev-secret-key"
export APP_DB_PATH="app.db"
export EXTRACTOR_TYPE="rule"
export ORDER_CLIENT_TYPE="local"
```

Example external order API configuration:

```bash
export APP_API_KEY="dev-secret-key"
export ORDER_CLIENT_TYPE="http_with_fallback"
export ORDER_API_BASE_URL="https://orders.example.com"
export ORDER_API_KEY="order-api-secret"
```

---

## Running with Docker

### Build the image

```bash
docker build -t llm-extractor .
```

### Run the container

```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_API_KEY="dev-secret-key" \
  -e APP_DB_PATH="/app/data/app.db" \
  -v "$(pwd)/data:/app/data" \
  llm-extractor
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Notes:

- The Dockerfile exposes port `8000`.
- The container includes a health check against `/health`.
- Mounting `/app/data` keeps the SQLite database outside the disposable container filesystem.

---

## API Authentication

Protected endpoints require this header:

```http
X-API-Key: dev-secret-key
```

If `APP_API_KEY` is missing on the server, protected routes return `500` because the server is misconfigured.

If the request omits or sends the wrong key, protected routes return `401`.

Protected endpoints include:

- `POST /extract`
- `POST /answer`
- `POST /documents/upload`
- `GET /documents/jobs/{job_id}`
- `POST /documents/ask`
- `POST /tool-assistant`
- `POST /chat`
- `GET /evals/document-qa/latest`
- `GET /usage/summary`
- `GET /usage/recent`

---

## API Reference

### `GET /health`

Returns service health.

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{
  "status": "ok"
}
```

---

### `POST /extract`

Extracts structured fields from support-style text.

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "text": "Urgent: please refund order ORD-123. Contact ada@example.com."
  }'
```

Response shape:

```json
{
  "email": "ada@example.com",
  "order_id": "ORD-123",
  "urgency": "high",
  "has_refund_request": true
}
```

Fields:

| Field | Type | Meaning |
|---|---|---|
| `email` | string or null | Extracted email address. |
| `order_id` | string or null | Extracted order identifier. |
| `urgency` | string | Estimated urgency: usually `low`, `medium`, or `high`. |
| `has_refund_request` | boolean | Whether the text appears to request a refund. |

---

### `POST /classify`

Classifies a text request.

```bash
curl -X POST http://127.0.0.1:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I was charged twice and need help with my invoice."
  }'
```

Response:

```json
{
  "category": "billing"
}
```

Possible categories:

- `billing`
- `technical`
- `refund`
- `general`

---

### `POST /summarize`

Returns the first relevant sentences up to `max_sentences`.

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI powers the backend. Pytest is used for testing. Docker packages the service.",
    "max_sentences": 2
  }'
```

Response:

```json
{
  "summary": "FastAPI powers the backend. Pytest is used for testing."
}
```

Constraints:

- `text`: 1 to 10,000 characters
- `max_sentences`: 1 to 5

---

### `POST /answer`

Answers a question from provided context.

```bash
curl -X POST http://127.0.0.1:8000/answer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "question": "What framework powers the backend?",
    "context": "FastAPI powers the backend. Pytest is used for testing."
  }'
```

Response:

```json
{
  "answer": "FastAPI powers the backend."
}
```

---

### `POST /route`

Routes user input to a task type.

```bash
curl -X POST http://127.0.0.1:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Please summarize this support message."
  }'
```

Response:

```json
{
  "route": "summarize"
}
```

Possible routes:

- `extract`
- `classify`
- `summarize`
- `answer`

---

### `POST /chat`

Returns a simple assistant reply.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "message": "Hello"
  }'
```

Response shape:

```json
{
  "reply": "..."
}
```

---

## Document Q&A Workflow

The document workflow has three steps:

1. Upload a `.txt` document.
2. Poll the ingestion job until it completes.
3. Ask questions against the resulting `document_id`.

### 1. Upload a document

Create a sample text file:

```bash
cat > guide.txt <<'END'
FastAPI is the backend framework used in this project.
Pytest is used for testing.
Docker packages the service for deployment.
END
```

Upload it:

```bash
curl -X POST http://127.0.0.1:8000/documents/upload \
  -H "X-API-Key: dev-secret-key" \
  -F "file=@guide.txt"
```

Response shape:

```json
{
  "job_id": "job-abc123def456",
  "filename": "guide.txt",
  "status": "queued",
  "document_id": null,
  "chunk_count": null,
  "error_message": null,
  "created_at": "2026-05-05T08:00:00+00:00",
  "updated_at": "2026-05-05T08:00:00+00:00"
}
```

Only `.txt` files are currently supported. Uploaded text must be valid UTF-8 and non-empty.

### 2. Fetch ingestion job status

```bash
curl http://127.0.0.1:8000/documents/jobs/job-abc123def456 \
  -H "X-API-Key: dev-secret-key"
```

Completed response shape:

```json
{
  "job_id": "job-abc123def456",
  "filename": "guide.txt",
  "status": "completed",
  "document_id": "doc-abc123def456",
  "chunk_count": 1,
  "error_message": null,
  "created_at": "2026-05-05T08:00:00+00:00",
  "updated_at": "2026-05-05T08:00:01+00:00"
}
```

Job statuses:

| Status | Meaning |
|---|---|
| `queued` | The upload has been accepted and scheduled for background processing. |
| `processing` | The worker is ingesting the document. |
| `completed` | The document was stored and can be queried. |
| `failed` | Ingestion failed. Inspect `error_message`. |

### 3. Ask a question

```bash
curl -X POST http://127.0.0.1:8000/documents/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "document_id": "doc-abc123def456",
    "question": "What framework is used for the backend?",
    "top_k": 3
  }'
```

Response shape:

```json
{
  "answer": "FastAPI is the backend framework used in this project.",
  "citations": [
    {
      "chunk_id": "doc-abc123def456-chunk-1",
      "snippet": "FastAPI is the backend framework used in this project. Pytest is used for testing...",
      "vector_score": 1.0,
      "keyword_score": 1.0,
      "hybrid_score": 1.0
    }
  ]
}
```

Citation fields:

| Field | Meaning |
|---|---|
| `chunk_id` | Stable ID of the retrieved chunk. |
| `snippet` | Short excerpt from the retrieved chunk. |
| `vector_score` | Normalized vector similarity score. |
| `keyword_score` | Normalized keyword overlap score. |
| `hybrid_score` | Weighted combined retrieval score. |

---

## Tool Assistant Workflow

The tool assistant demonstrates a constrained assistant that can call business tools.

Supported behaviors:

- order status lookup
- refund eligibility check
- pending refund request creation
- confirmation-gated refund submission

The default local order fixtures include:

| Order ID | Status | Refund Eligible |
|---|---|---:|
| `ORD-123` | `shipped` | yes |
| `ORD-456` | `processing` | yes |
| `ORD-789` | `delivered` | no |

### Check order status

```bash
curl -X POST http://127.0.0.1:8000/tool-assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "message": "Where is ORD-123?"
  }'
```

Response shape:

```json
{
  "answer": "Order ORD-123 is currently shipped. Estimated delivery is 2026-05-02.",
  "tool_called": "get_order_status",
  "tool_result": {
    "found": true,
    "order_id": "ORD-123",
    "status": "shipped",
    "estimated_delivery": "2026-05-02"
  },
  "tool_calls": [
    {
      "tool_name": "get_order_status",
      "result": {
        "found": true,
        "order_id": "ORD-123",
        "status": "shipped",
        "estimated_delivery": "2026-05-02"
      }
    }
  ]
}
```

### Ask about refund eligibility

```bash
curl -X POST http://127.0.0.1:8000/tool-assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "message": "Can I get a refund for ORD-789?"
  }'
```

### Create a pending refund request

```bash
curl -X POST http://127.0.0.1:8000/tool-assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "message": "I want to request a refund for ORD-123."
  }'
```

Response shape:

```json
{
  "answer": "Order ORD-123 is eligible for a refund. Please confirm PEND-001 if you want me to submit the refund request.",
  "tool_called": "create_pending_refund_request",
  "tool_result": {
    "created": true,
    "pending_action_id": "PEND-001",
    "order_id": "ORD-123",
    "action": "create_refund_request",
    "status": "pending_confirmation",
    "message": "Refund request is pending confirmation."
  },
  "tool_calls": [
    {
      "tool_name": "create_pending_refund_request",
      "result": {
        "created": true,
        "pending_action_id": "PEND-001",
        "order_id": "ORD-123",
        "action": "create_refund_request",
        "status": "pending_confirmation",
        "message": "Refund request is pending confirmation."
      }
    }
  ]
}
```

### Confirm the pending action

```bash
curl -X POST http://127.0.0.1:8000/tool-assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "message": "Confirm PEND-001."
  }'
```

This two-step pattern is important: the assistant can prepare an action, but the user must explicitly confirm before the side effect is completed.

---

## Evaluation

The repository includes evaluation cases and scripts for two capabilities.

### Extraction evaluation

```bash
python scripts/run_extraction_eval.py
```

This loads cases from:

```text
evals/extraction_cases.json
```

It compares actual structured extraction output against expected JSON.

### Document Q&A evaluation

```bash
python scripts/run_document_qa_eval.py
```

This loads cases from:

```text
evals/document_qa_cases.json
```

The document Q&A evaluation checks:

- answer content
- citation count
- citation content
- retrieval score presence
- latency per case

It stores the latest evaluation run in SQLite.

Fetch the latest stored document Q&A evaluation:

```bash
curl http://127.0.0.1:8000/evals/document-qa/latest \
  -H "X-API-Key: dev-secret-key"
```

Response shape:

```json
{
  "run_id": "eval-abc123def456",
  "total_cases": 3,
  "passed": 3,
  "failed": 0,
  "average_latency_ms": 12.34,
  "created_at": "2026-05-05T08:00:00+00:00",
  "results": []
}
```

---

## Usage and Cost Tracking

The app records usage for document embedding and document answering operations.

Usage records include:

- operation name
- provider
- model name
- estimated input tokens
- estimated output tokens
- estimated cost
- metadata
- creation timestamp

The token estimator is intentionally simple: approximately one token per four characters. Default pricing is zero unless a service records usage with explicit pricing.

### Usage summary

```bash
curl http://127.0.0.1:8000/usage/summary \
  -H "X-API-Key: dev-secret-key"
```

Response:

```json
{
  "total_estimated_cost_usd": 0.0,
  "recent_record_count": 2
}
```

### Recent usage records

```bash
curl "http://127.0.0.1:8000/usage/recent?limit=10" \
  -H "X-API-Key: dev-secret-key"
```

Response shape:

```json
{
  "records": [
    {
      "usage_id": "usage-abc123def456",
      "operation": "document_answer",
      "provider": "local",
      "model_name": "RuleBasedAnswerer",
      "input_tokens": 100,
      "output_tokens": 12,
      "estimated_cost_usd": 0.0,
      "metadata": {
        "document_id": "doc-abc123def456"
      },
      "created_at": "2026-05-05T08:00:00+00:00"
    }
  ]
}
```

---

## Testing

Run the test suite:

```bash
pytest -q
```

The tests cover:

- API routes
- service behavior
- document ingestion
- ingestion queues
- stored text ingestion
- retrieval scoring
- document answering
- evaluation result storage
- usage tracking
- tool assistant behavior
- order client fallback and retry behavior

For local app testing, remember to configure:

```bash
export APP_API_KEY="dev-secret-key"
```

The test suite itself sets a test API key through fixtures.

---

## Persistence

The app uses SQLite.

By default, persistent application data is written to:

```text
app.db
```

The upload staging store defaults to:

```text
uploaded_texts.db
```

Tables include data for:

- documents
- chunks
- ingestion jobs
- evaluation runs
- evaluation case results
- usage records
- staged uploaded text

Set `APP_DB_PATH` to control the main application database location:

```bash
export APP_DB_PATH="data/app.db"
```

For Docker, prefer mounting a volume and setting `APP_DB_PATH` inside that volume.

---

## Operational Notes

### Request logging

Every request is logged with:

- method
- path
- status code
- duration in milliseconds
- request ID

If a request sends `X-Request-ID`, the app reuses it. Otherwise, the middleware creates a short request ID and returns it in the response header.

### Background jobs

Document uploads create ingestion jobs and enqueue work through the `DocumentIngestionQueue` protocol.

The current implementation uses FastAPI `BackgroundTasks`. This is useful for learning and small local deployments, but it is not a durable queue. If the process exits before the background task completes, queued work can be lost.

### Uploaded text staging

Document upload stores raw text in a staging table and queues a pointer to that stored text. This avoids putting large raw text directly into the queue payload.

Completed ingestion deletes the staged text. Failed or abandoned staging records need a retention cleanup policy before production use.

### External order API mode

The order tools can use:

- a local fixture client
- an HTTP order client
- an HTTP client with local fallback

The HTTP client handles:

- `404` as order not found
- retryable status codes: `429`, `500`, `502`, `503`, `504`
- `Retry-After` for rate limits when provided
- fallback to local fixtures when configured as `http_with_fallback`

---

## Known Limitations

This project is intentionally practical but not fully production-ready.

Current limitations:

1. **The queue is not durable.**
   FastAPI background tasks are not a replacement for Redis, RQ, Celery, SQS, or another durable queue.

2. **Only `.txt` upload is supported.**
   PDF, DOCX, HTML, Markdown, and structured document parsing are not implemented.

3. **The main answerer is rule-based.**
   It selects relevant sentences from context. It does not yet call a real LLM for natural-language synthesis.

4. **Cost tracking is approximate.**
   Token counts are estimated by character length and default pricing is zero.

5. **Authentication is basic.**
   API-key auth is useful for development but does not provide user identity, roles, scopes, or tenant isolation.

6. **SQLite is local-first.**
   SQLite is excellent for learning and small deployments, but multi-instance production deployments usually require a managed database.

7. **Stale staged uploads are not automatically expired.**
   Successful jobs clean up staged text, but failed or abandoned records need a retention lifecycle.

8. **Monitoring is basic.**
   Logs and health checks exist, but metrics, traces, dashboards, and alerting are not yet implemented.

---

## Suggested Roadmap

Recommended next improvements:

### 1. Add stale upload retention cleanup

Implement cleanup for staged upload records older than a configured age.

Useful output:

- `delete_older_than(...)` or equivalent store method
- unit tests
- optional admin endpoint or scheduled cleanup command

### 2. Replace background tasks with a durable queue backend

Keep the current `DocumentIngestionQueue` protocol and add an implementation backed by a durable queue.

Options:

- Redis + RQ
- Celery
- Dramatiq
- SQS
- database-backed queue

### 3. Improve secrets handling

Move from raw environment variables toward deployment-managed secrets.

Examples:

- Docker secrets
- cloud secret manager
- runtime secret injection

### 4. Add richer observability

Add production-grade telemetry:

- structured JSON logs
- metrics for request latency and error rate
- ingestion job metrics
- evaluation pass/fail trend
- usage and cost dashboard

### 5. Improve document support

Add parsers for:

- PDF
- DOCX
- Markdown
- HTML

Keep ingestion normalized into plain text before chunking.

### 6. Add real LLM provider integration

Replace or supplement rule-based components with real model providers while preserving:

- structured output validation
- retries
- fallback behavior
- usage tracking
- evaluation coverage

### 7. Add permissions and tenancy

For a production document Q&A system, add:

- user identity
- document ownership
- tenant boundaries
- per-document access control
- audit logging

---

## Development Philosophy

This project favors boring, inspectable reliability over framework-heavy abstraction.

Good AI application engineering is mostly careful software engineering around uncertain model behavior:

- validate inputs
- constrain outputs
- isolate side effects
- track jobs
- return citations
- log failures
- measure quality
- estimate cost
- keep clear service boundaries

That makes the codebase a useful foundation for practicing production AI engineering rather than just demonstrating a local prototype.
