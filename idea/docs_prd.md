# Multi‑LLM Council for Contract & Policy Analysis (MVP)

## 1. Problem
Professionals need fast, trustworthy contract/policy reviews that surface risks, cite evidence, and propose edits. Traditional review is slow and inconsistent.

## 2. Users & Primary Jobs
- Legal/ops/PMs/SMBs: upload a doc, add context, get a risk-annotated review with editable redlines.
- Compliance/HR: map policies to requirements, find gaps, export summaries.

## 3. Scope (MVP)
- Inputs: PDF/DOCX/Images; optional context (role, jurisdiction, priorities), optional related docs.
- Analysis: clause extraction, risk scoring, missing/negotiable points, suggested language, citations.
- Outputs: interactive table; Word redline; PDF/JSON report.
- Guardrails: per-finding citations; confidence scoring; “not legal advice” notice.

## 4. User Flow (Image 1 mapped)
1) Upload
   - Choose document type (e.g., MSA, NDA, Employment, Policy)
   - Caption/notes
2) Context
   - Role (buyer/seller/employer/employee), jurisdictions, effective date
   - Priorities (e.g., liability cap, IP ownership) + risk tolerance slider
   - Link other docs (appendix, prior versions)
3) Analyze (Council)
   - Agents run in parallel: Risk, Compliance, Negotiator, Drafting, Finance
   - Monitor checks coverage/citations; Judge synthesizes
4) Results
   - Findings grouped: Good, Risk/Negotiable, Missing
   - Clause table with: severity, rationale, suggested language, citations
   - Export: Word redline, PDF summary, JSON
5) Feedback/Refine
   - Adjust context/preferences; regenerate
   - Thumbs + corrections (telemetry & eval)

## 5. Data Model (simplified)
- Document(id, name, mime, storage_url, hash, created_by, created_at)
- Project(id, owner_id, title, doc_ids[], context_json)
- Clause(id, document_id, heading, text, page_spans[])
- Finding(id, project_id, clause_id?, type[good|risk|missing], severity, rationale, suggestions[], citations[], agent_sources[], confidence)
- Citation(id, document_id, page, span_start, span_end, text, external_source?)
- Run(id, project_id, status, timings, cost, llm_versions, metrics)

## 6. Council Design
- Risk Agent: Identify risky/ambiguous terms; rate severity; cite spans.
- Compliance Agent: Map to policy/regulatory norms; flag gaps; cite spans and external refs.
- Negotiator Agent: Propose negotiation points, fallback tiers, trade-offs.
- Drafting Agent: Provide concrete redline-ready language with placeholders.
- Finance Agent: Flag payment terms, penalties, TCO considerations.
- Monitor: Coverage check (all major clause categories touched), contradiction detection, hallucination/citation validation.
- Judge: Merge findings, resolve conflicts, deduplicate, assign confidence, produce final artifacts.

Consensus:
- Agreement score = fraction of agents with compatible conclusions.
- Confidence = f(agreement, retrieval density, monitor checks passed).
- Any finding without internal doc citation is “Advisory” and labeled.

## 7. Retrieval & Chunking
- Clause-aware segmentation: detect headings; chunk within ~1–2 clauses; overlap minimal.
- Embed chunks + headings; store spans for citation rendering.
- Query routing: agents retrieve top-k chunks + context + policy base snippets.

## 8. Prompts & Tools
- Tools: `retrieve(doc, query)`, `law_lookup(topic, jurisdiction)`, `policy_base(type)`, `math`, `redline_builder`.
- Every agent must: show rationale, cite spans (page + text snippet), propose action.

## 9. Non‑Functional
- Privacy: default no retention; encrypted storage; region pinning.
- Cost: parallel runs; caching embeddings; dedupe prompts; streaming outputs.
- Latency target: <90s for 20–30 page doc on base tier; show partials.

## 10. Deliverables
- Web app with 4 screens + exports
- API: upload, start_run, get_status, get_results, export_docx
- Evaluation harness: 10 synthetic contracts with expected findings; regression metrics.

## 11. Open Questions
- Supported jurisdictions at launch?
- Which doc types in MVP (NDA + MSA recommended)?
- Local mode vs SaaS for sensitive docs?
- Which LLM mix and fallback policy?