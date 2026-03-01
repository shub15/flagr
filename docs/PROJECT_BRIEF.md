# Flagr / Overrule — Project Brief

## 1) What this project is

**Flagr (Overrule Legal Advisor)** is an AI-powered contract intelligence platform.
It ingests legal documents, runs a multi-agent legal analysis pipeline, and returns structured risk findings, recommendations, Q&A, refinement outputs, and exportable deliverables.

---

## 2) Core problem solved

- Speeds up legal contract review.
- Surfaces critical risk clauses and missing protections.
- Provides explainable, agent-level insights (council transparency).
- Supports iterative refinement, redaction, translation, and integrations.

---

## 3) High-level architecture

### A) Frontend (React + TypeScript + Vite)
- User authentication and protected routes.
- Contract upload and Drive import UI.
- Analysis dashboard, split views, knowledge and calendar tabs.
- Calls backend APIs for review, export, refine, translate, redact, voice, and integrations.

### B) Backend (FastAPI + Python)
- JWT auth, route orchestration, file parsing, AI pipeline.
- Multi-agent review engine with multiple LLM providers.
- RAG-backed legal context retrieval from vector DB.
- Persistent review storage and retrieval APIs.

### C) Data and infra
- SQL DB (SQLite/PostgreSQL) for users/reviews/feedback.
- Pinecone vector database for legal context embeddings.
- Optional Docker-based deployment.

---

## 4) Major backend modules

### `app/agents/`
- `skeptic.py`: finds legal risks and adversarial concerns.
- `strategist.py`: strategic/negotiation-oriented perspectives.
- `auditor.py`: compliance and completeness checks.
- `referee.py`: consolidates outputs across agents/LLMs.
- `base.py`: shared agent abstractions.

### `app/services/`
- `orchestrator.py`: fan-out/fan-in execution across agents.
- `llm_service.py`: OpenAI/Gemini/Grok/Mistral/Groq provider access.
- `council.py`: multi-LLM council and aggregation logic.
- `rag_service.py`: retrieval of legal context from vector DB.
- `pdf_processor.py`, `docx_processor.py`, `image_processor.py`: extraction by file type.
- `pdf_annotator.py`: annotation/highlight generation.
- `contract_qa_service.py`: question-answering over reviewed contracts.
- `contract_refinement.py`: refinement preview + feedback-driven updates.
- `export_service.py`: DOCX/PDF export generation.
- `redaction_service.py`: sensitive data redaction workflows.
- `translation_service.py`: language translation support.
- `trello_service.py`: Trello sync integration.

### `app/api/`
- `auth_routes.py`: signup, login, current-user endpoints.
- `routes.py`: primary product API surface.
- `voice_routes.py`: speech-to-text / text-to-speech.
- `council_endpoint.py`, `refinement_endpoints.py`: specialized endpoints.

### `app/models/`, `app/database/`, `app/auth/`, `app/vectordb/`
- Pydantic + ORM models, DB sessions, auth dependencies/security, Pinecone client wrappers.

---

## 5) Main API functionality map

### Authentication
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Contract review lifecycle
- `POST /api/review` — upload file and run multi-agent review.
- `GET /api/reviews`
- `GET /api/reviews/{review_id}`
- `POST /api/feedback`

### Retrieval, transparency, and Q&A
- `POST /api/reviews/{review_id}/ask`
- `GET /api/reviews/{review_id}/council`

### Legal doc ingestion / RAG management
- `POST /api/legal-docs/upload`
- `GET /api/legal-docs/status`

### Export / annotation / refinement
- `GET /api/reviews/{review_id}/annotated-pdf`
- `GET /api/reviews/{review_id}/annotated-pdf/redacted`
- `GET /api/reviews/{review_id}/export/docx`
- `GET /api/reviews/{review_id}/export/pdf`
- `GET /api/reviews/{review_id}/refinement-preview`
- `POST /api/reviews/{review_id}/refine-with-feedback`
- `GET /api/reviews/{review_id}/custom-refined-pdf`

### Utilities and integrations
- `POST /api/translate`
- `POST /api/redact`
- `POST /api/integrations/trello/sync`
- `POST /api/voice/stt`
- `POST /api/voice/tts`
- `GET /api/health`

---

## 6) Frontend functionality map

### Pages (`frontend/src/pages/`)
- `Login.tsx`: authentication entry.
- `Dashboard.tsx`: main workspace and integrations control.
- `Upload.tsx`: upload flow + import from Google Drive.
- `Split.tsx`: split analysis/results experience.
- `RefineTab.tsx`: clause refinement workflows.
- `Knowledge.tsx`: legal knowledge/insights view.
- `CalendarTab.tsx`: planning/schedule-oriented UI.

### Services (`frontend/src/services/`)
- `api.ts`: base API request helpers.
- `authService.ts`: auth token/session operations.
- `driveService.ts`: Google Drive picker + file import flow.

### Context and access control
- `AuthContext.tsx`: app-level auth state.
- `ProtectedRoute.tsx`: guarded routes for logged-in users.

---

## 7) Concepts and patterns used in this project

- **Fan-out, fan-in multi-agent orchestration**.
- **Multi-LLM council consensus** across providers.
- **RAG (Retrieval-Augmented Generation)** with legal corpora.
- **Hybrid extraction pipeline** (PDF, DOCX, image/OCR/vision).
- **Human-in-the-loop refinement** via feedback endpoints.
- **Explainability / transparency** via council and agent outputs.
- **Risk categorization** (critical, negotiable, good, missing).
- **Artifact generation** (annotated PDFs, exports, refined docs).
- **Security basics**: JWT auth + protected endpoints.
- **Integration-ready design**: Trello, Drive, voice, translation.

---

## 8) End-to-end user workflow

1. User signs up/logs in.
2. Uploads contract (local file or Google Drive import in UI).
3. Backend extracts text and runs multi-agent + RAG analysis.
4. User gets structured findings and recommendation score.
5. User asks follow-up questions or reviews council transparency.
6. User refines contract using feedback loop.
7. User exports reviewed/refined artifacts (DOCX/PDF).
8. Optional: redaction, translation, Trello sync, voice utilities.

---

## 9) Technology stack summary

### Frontend
- React, TypeScript, Vite, Tailwind/CSS utility styling.

### Backend
- FastAPI, Pydantic, SQLAlchemy, Python services.

### AI + data
- OpenAI / Gemini / Grok / Mistral / Groq (as configured).
- Pinecone vector DB for legal knowledge retrieval.

### Runtime / deployment
- Local dev via venv + npm.
- Docker support for backend containerized runs.

---

## 10) Current project strengths

- Broad legal workflow coverage beyond basic review.
- Good extensibility through modular services and APIs.
- Transparent AI reasoning path via council outputs.
- Practical utility features (redaction, export, translation, integrations).

---

## 11) Suggested future enhancements (optional)

- Add centralized observability/metrics for each agent/provider.
- Add retry + fallback policy visualization in UI.
- Add per-tenant/project config for integrations.
- Add richer automated test coverage for API workflows.
- Add role-based access control for enterprise scenarios.

---

This brief is designed as a quick reference for developers, reviewers, and stakeholders to understand the full project scope, capabilities, and core implementation concepts.
