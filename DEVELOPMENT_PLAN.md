# MTES Development Plan

Implementation sequence for MTES MVP. No calendar dates—order is strict unless a step explicitly allows parallel work. Each step lists goal, deliverables, specification references, and exit criteria.

**Contract documents:** `docs/detailed_design.md` (this plan’s parent contract), project specifications under `docs/`, `AGENTS.md`.

**Conventions:** Python 3.13+, `typing.Protocol` for service boundaries, async I/O, typed exceptions in module `exceptions.py`, pytest for tests.

---

## Phase 0 — Repository foundation

### Step 0.1 — Project scaffold

**Goal:** Runnable package layout and tooling.

**Deliverables:**
- `pyproject.toml` with Python 3.13+, dependencies placeholders
- `src/mtes/` package per `AGENTS.md` module layout
- `tests/unit/`, `tests/integration/`
- `config/config.example.yaml` aligned with SRS §12.3
- `.gitignore` for venv, logs, runtime, secrets

**References:** AGENTS.md §6, Architecture §4, SRS §12.

**Exit criteria:** `pip install -e .` succeeds; `pytest` runs zero tests green.

### Step 0.2 — Shared infrastructure types

**Goal:** Cross-cutting types and configuration loading.

**Deliverables:**
- `shared/config.py` — YAML load + validation
- `shared/types.py` — Genome, Candidate, EvolutionStatus enums
- `shared/exceptions.py` — typed errors (`InvalidGenomeError`, `MongoDbUnavailableError`, etc.)
- `shared/logging.py` — structured logging setup

**References:** SRS §12–15, AGENTS.md §27–28.

**Exit criteria:** Unit tests load example config; invalid config raises typed exception.

### Step 0.3 — Docker Compose skeleton

**Goal:** VPS-oriented deployment shell.

**Deliverables:**
- `docker/docker-compose.yml` with services: `mtes-core`, `publication-worker`, `maintenance-worker`
- Environment variable templates (no secrets committed)
- MongoDB connection via env (Atlas URI)

**References:** Architecture §14.

**Exit criteria:** `docker compose config` validates; containers start with stub entrypoints.

---

## Phase 1 — Persistence layer

### Step 1.1 — MongoDB connection and health

**Goal:** Async persistence with connectivity checks.

**Deliverables:**
- `persistence/client.py` — Motor client, connection lifecycle
- `persistence/health.py` — database ping for health service
- Retry policy 1s/2s/4s, max 3 attempts (SRS §13.1)

**References:** Data Model §2, Architecture §7.3, SRS §11.

**Exit criteria:** Integration test (Testcontainers or disposable MongoDB) connects and pings.

### Step 1.2 — Core collection repositories

**Goal:** CRUD for specification-defined collections.

**Deliverables:**
- Repositories: `dictionary_terms`, `dictionary_buckets`, `genomes`, `mutation_history`, `constraint_records`, `phenotype_candidates`, `candidate_archive`, `validation_records`, `fitness_records`, `tweet_archive`, `embedding_models`, `audit_log`, `system_events`, `pair_memory_state`
- Append-only enforcement for immutable collections
- Common field injection (`schema_version`, `experiment_id`, `run_id`, `created_at`)

**References:** Data Model §3–9.

**Exit criteria:** Round-trip insert/read for sample genome and candidate documents.

### Step 1.3 — Operational collection repositories [assumed schemas]

**Goal:** Persist workflow, evolution, bootstrap, queues.

**Deliverables:**
- Repositories: `bootstrap_reports`, `workflow_state`, `evolution_state`, `population_members`, `publication_queue`, `daemon_state`
- Atomic workflow state updates

**References:** detailed_design §2.3.3, Bootstrap §17, Architecture §7.1, SRS §5.4.

**Exit criteria:** Workflow state survives simulated restart (read after write).

### Step 1.4 — Vector index bootstrap script

**Goal:** Atlas Vector Search indexes from `embedding_models.dimension`.

**Deliverables:**
- `scripts/create_vector_indexes.py` — no hardcoded dimensions
- Audit log on `VECTOR_INDEX_REBUILD`

**References:** Data Model §2.3.

**Exit criteria:** Script runs against test MongoDB when `embedding_models` seeded.

---

## Phase 2 — Monitoring and HTTP surface

### Step 2.1 — Health and metrics HTTP server

**Goal:** Operational endpoints before business logic.

**Deliverables:**
- `monitoring/health_service.py` — `GET /health` < 1s
- `monitoring/metrics_registry.py` — Prometheus counters/gauges per SRS §10
- Embeddable aiohttp/uvicorn launcher used by daemon

**References:** SRS §10–11, README monitoring section.

**Exit criteria:** Integration test asserts `/health` JSON schema and `/metrics` contains `mtes_*` names.

### Step 2.2 — Global rate limiter

**Goal:** Coroutine-safe throttling shared by adapters.

**Deliverables:**
- `shared/rate_limiter.py` — provider-specific limits
- Integration hooks for LLM and Telegram adapters

**References:** Architecture §7.10.

**Exit criteria:** Unit test proves concurrent tasks respect cap.

---

## Phase 3 — Deterministic mapping pipeline (no LLM)

### Step 3.1 — Numeric gene LUT and translation

**Goal:** Deterministic gene→constraint mapping.

**Deliverables:**
- `mapping/numeric_lut.py` — canonical tanh LUT, verification checkpoints
- `mapping/translation_service.py` — six genes to constraints
- Compression token limits 48/36/24

**References:** GA §6, Mapping §3–4, v5.0 §1.

**Exit criteria:** LUT round-trip error ≤ 1 byte; translation tests match spec tables.

### Step 3.2 — Tokenization and metric primitives

**Goal:** Foundation for fitness and distance.

**Deliverables:**
- `mapping/tokenization.py` — tiktoken cl100k_base policy
- `mapping/metrics.py` — punctuation_density, short_clause_ratio, bigram redundancy, etc.

**References:** Mapping §14–15, v5.0 §6–7.

**Exit criteria:** Golden-file tests for metric examples in specification.

### Step 3.3 — Dictionary and bucket services

**Goal:** Coordinate assignment and bucket operations.

**Deliverables:**
- `mapping/dictionary_service.py` — term lookup, coordinate resolution
- Bucket balancing hooks (oversized/sparse) per GA §5.4
- Axis correlation warning computation

**References:** GA §4–5, Data Model §3.

**Exit criteria:** Load fixture dictionary; resolve anchor from coordinate.

### Step 3.4 — Semantic expansion and anchor selection

**Goal:** Deterministic expansion and anchor priority chain.

**Deliverables:**
- `mapping/semantic_expansion_service.py` — mpnet retrieval, cosine filter
- `mapping/anchor_selection_service.py` — TF-IDF, embedding centrality, tie-breaks
- spaCy lemma validation path

**References:** Mapping §5–6, v5.0 §4.

**Exit criteria:** Identical inputs produce identical expansion sets across runs.

### Step 3.5 — Relation graph and structural plan

**Goal:** Graph edges and plan generation without LLM.

**Deliverables:**
- `mapping/relation_graph_service.py` — edge score, rarity corpus hash, v5.0 relation ordering
- `mapping/structural_plan_service.py` — rhetorical and sentiment lookups

**References:** Mapping §7–8, v5.0 §3.

**Exit criteria:** Unit tests cover relation type priority examples.

### Step 3.6 — Phenotype distance and genotype distance

**Goal:** Distance functions for locality.

**Deliverables:**
- `mapping/genotype_distance.py` — GA §7 formulas
- `mapping/phenotype_distance.py` — embedding + stylometric + constraint deviation
- Embedding service interface (stub then real)

**References:** GA §7, Mapping §12.

**Exit criteria:** Pairwise distances match hand-calculated fixtures.

---

## Phase 4 — Embedding layer

### Step 4.1 — Embedding adapter and cache policy

**Goal:** Provider-independent embeddings with bootstrap validation.

**Deliverables:**
- `embedding/embedding_adapter.py` — Protocol + OpenAI/local implementations
- `embedding/embedding_service.py` — batch embed, cache per calibration rules
- Persist `embedding_models` metadata

**References:** Bootstrap §8, Data Model §9.1, Architecture §7.5.

**Exit criteria:** `retrieval_consistency` testable on repeated top-20 neighbors.

---

## Phase 5 — LLM adapter and phases P3–P5

### Step 5.1 — LLM adapter layer

**Goal:** Provider-independent LLM calls with failover.

**Deliverables:**
- `llm/llm_adapter.py` — Protocol, primary/secondary/fallback
- Response normalization, timeout, audit `LLM_REQUEST`/`LLM_RESPONSE`
- Decoding profile application per phase

**References:** LLM Spec §5–6, Architecture §7.4, SRS §13.3.

**Exit criteria:** Mock provider integration test; failover recorded in `system_events`.

### Step 5.2 — P3 constraint expansion

**Goal:** LLM expands genome to `generation_constraints` JSON.

**Deliverables:**
- `llm/constraint_expansion_service.py`
- P3 schema validation before P4
- Store `constraint_records`

**References:** LLM Spec §7.

**Exit criteria:** Mock LLM returns valid schema; invalid rejected.

### Step 5.3 — P4 routing and compilation

**Goal:** Prompt family selection and single phenotype compile.

**Deliverables:**
- `llm/prompt_router.py` — families P4-A…F, hysteresis, combined mode
- `llm/phenotype_compiler.py` — structured JSON output
- Store raw candidates in `phenotype_candidates`

**References:** LLM Spec §6, §8; Mapping §9.

**Exit criteria:** Routing table tests for activation thresholds; family audit logged.

### Step 5.4 — P5 candidate expansion and ranking

**Goal:** Five alternatives with constraint/diversity/overall scores.

**Deliverables:**
- `llm/candidate_expansion_service.py`
- Ranking → `candidate_archive`
- Outlier policy per Mapping v5.0 §Candidate Outlier Rejection

**References:** LLM Spec §9, Mapping §16.

**Exit criteria:** Exactly five candidates persisted; selection tie-break order verified.

---

## Phase 6 — Validation, repair, fitness

### Step 6.1 — Validation pipeline

**Goal:** Schema, constraint, semantic, integration passes.

**Deliverables:**
- `mapping/validation_service.py` — anchor integrity, hard thresholds
- `validation_records` persistence

**References:** Mapping §6, §10; LLM Spec validation sections.

**Exit criteria:** Failing anchor triggers reject; passes recorded.

### Step 6.2 — Repair layer

**Goal:** Bounded repair with leakage detection.

**Deliverables:**
- `llm/repair_service.py` — max 3 operations, token delta cap
- Diagnostic-first recovery actions
- Pre-repair vs post-repair fitness recording

**References:** Mapping §10, v5.0 §8.

**Exit criteria:** Repair leakage window triggers diagnostic action in tests.

### Step 6.3 — Fitness evaluator

**Goal:** Post-repair fitness for selection; pre-repair for diagnostics.

**Deliverables:**
- `mapping/fitness_evaluator.py` — v5.0 decomposition
- `fitness_records` persistence
- Proxy weight cap ≤ 0.30

**References:** Mapping §11, v5.0 §7.

**Exit criteria:** Fitness sum matches fixture genome/candidate pair.

---

## Phase 7 — Genetic algorithm engine

### Step 7.1 — Mutation and crossover

**Goal:** Spec-compliant operators.

**Deliverables:**
- `ga/mutation_service.py`, `ga/crossover_service.py`
- `mutation_history` writes
- Low-purity destination handling

**References:** GA §8–11.

**Exit criteria:** Mutation reflection tests; crossover blend proportions.

### Step 7.2 — Selection and pair memory

**Goal:** Parent selection pools and pair penalties.

**Deliverables:**
- `ga/selection_service.py` — pool allocation, parent score
- `ga/pair_memory_service.py` — exponential decay half-life 20 generations

**References:** GA §9–10, Data Model `pair_memory_state`.

**Exit criteria:** Pair memory updates on reuse; penalty decays.

### Step 7.3 — Diversity and locality repair

**Goal:** Collapse detection and offspring repair.

**Deliverables:**
- `ga/diversity_service.py`
- Locality repair loop distance > 0.35, max 3 iterations
- 5% bypass logging

**References:** GA §11–12.

**Exit criteria:** Simulated collapse triggers response; bypass logged.

### Step 7.4 — Population management

**Goal:** Maintain population size and generation counter.

**Deliverables:**
- `ga/population_service.py` — init, insert, replace
- `population_members` persistence

**References:** Bootstrap §13, SRS evolution metrics.

**Exit criteria:** Population size stable across generation tick tests.

---

## Phase 8 — Core engine and workflow coordinator

### Step 8.1 — Pipeline orchestration

**Goal:** Wire mapping → LLM → validation → fitness in one generation job.

**Deliverables:**
- `core/generation_pipeline.py` — single phenotype path
- `core/evolution_cycle.py` — one evolutionary generation
- No direct provider calls from core (adapters only)

**References:** Architecture §7.2, LLM pipeline overview.

**Exit criteria:** End-to-end test with mock LLM produces archived candidate.

### Step 8.2 — Workflow coordinator

**Goal:** Persisted workflows, retries, pause/resume hooks.

**Deliverables:**
- `core/workflow_coordinator.py`
- Startup recovery of incomplete workflows
- Emergency stop flag handling

**References:** Architecture §7.1, §9.

**Exit criteria:** Kill mid-workflow; restart resumes or fails deterministically.

### Step 8.3 — Evolution lifecycle service

**Goal:** FSM per SRS.

**Deliverables:**
- `core/evolution_lifecycle_service.py` — states and transitions
- Pause-at-boundary enforcement
- `evolution_state` persistence

**References:** SRS §7, detailed_design §2.5.

**Exit criteria:** Property test: no transition violates allowed table.

---

## Phase 9 — Bootstrap module

### Step 9.1 — Bootstrap stage runner

**Goal:** Sequential bootstrap pipeline CLI.

**Deliverables:**
- `core/bootstrap_pipeline.py` — stages per Bootstrap §4
- Idempotent skip for completed stages
- `--force` support

**References:** Bootstrap §4–19, SRS §4.

**Exit criteria:** Dry-run records stage order; failure stops pipeline.

### Step 9.2 — Provider and locality calibration

**Goal:** Provider scoring and Spearman locality.

**Deliverables:**
- `core/provider_validation.py` — preliminary and final scores
- `core/locality_calibration.py` — golden dataset pairs, cached embeddings, Spearman, stability std ≤ 0.05
- Golden dataset/prompt loaders (JSONL)

**References:** Bootstrap §6–11, Mapping §18.

**Exit criteria:** Unit test on toy dataset computes correlation; subsampling forbidden test documented.

### Step 9.3 — Bootstrap report and readiness

**Goal:** Persist report and gate production.

**Deliverables:**
- `core/bootstrap_report_service.py`
- Operator approval fields for borderline zone
- Readiness enum emission

**References:** Bootstrap §16–17, §20.

**Exit criteria:** Report document validates against schema; `NOT_READY` blocks evolution start.

---

## Phase 10 — CLI and daemon

### Step 10.1 — CLI commands (non-daemon)

**Goal:** Operator-facing commands.

**Deliverables:**
- `cli/main.py` — Typer app: `bootstrap`, `generate`, `evolution`, `telegram`, `report`
- Global flags: `--config`, `--json`, `--verbose`, `--verbose-sanitized`
- Exit codes per SRS §19

**References:** SRS §4–9, §16.

**Exit criteria:** CLI integration tests invoke each command with mocks.

### Step 10.2 — Daemon and scheduler

**Goal:** Background execution with recovery.

**Deliverables:**
- `core/daemon_service.py` — APScheduler/asyncio timers
- Bounded queues and worker pool
- PID file `./runtime/mtes.pid`
- SIGTERM/SIGINT graceful shutdown

**References:** SRS §5, §14.

**Exit criteria:** Daemon starts, schedules mock job, shuts down gracefully, restores state.

### Step 10.3 — Evolution admin authentication

**Goal:** Secure pause/resume/stop/reset.

**Deliverables:**
- `core/operator_auth.py` — env/Telegram allow-list
- Audit logging on admin commands

**References:** SRS §7.4, §17.

**Exit criteria:** Unauthenticated reset rejected; authenticated succeeds and audits.

---

## Phase 11 — Telegram and publication

### Step 11.1 — Telegram gateway

**Goal:** Isolated Telegram I/O.

**Deliverables:**
- `telegram/telegram_gateway.py` — outbound publish, inbound events
- Rate limit 30/min
- Operator command translation to coordinator signals

**References:** Architecture §7.7, SRS §8.

**Exit criteria:** Mock Telegram API tests for publish and command auth.

### Step 11.2 — Publication engine

**Goal:** Scheduling and queue processing.

**Deliverables:**
- `publication/publication_service.py`
- `publication_queue` driver
- Engagement collection optional path

**References:** Architecture §7.6, Bootstrap §14–15.

**Exit criteria:** Scheduled publication fires; failed publish retries per SRS.

---

## Phase 12 — Reporting and maintenance

### Step 12.1 — Report generation

**Goal:** HTML and JSON operational reports.

**Deliverables:**
- `core/report_service.py` — evolution summary, locality line, recent content
- Output under `./reports/`
- Optional charts

**References:** SRS §9.

**Exit criteria:** `mtes report` produces HTML+JSON < 5 minutes on fixture DB.

### Step 12.2 — Maintenance worker

**Goal:** Periodic housekeeping.

**Deliverables:**
- `core/maintenance_worker.py` — TTL purge, index health, engagement sync
- Docker scheduled task wiring

**References:** Architecture §7.13, Data Model §10.

**Exit criteria:** TTL job removes aged `phenotype_candidates` in test DB.

---

## Phase 13 — Integration, bootstrap trial, acceptance

### Step 13.1 — Integration test suite

**Goal:** Cross-module confidence without real providers.

**Deliverables:**
- Mock LLM, mock Telegram, Testcontainers MongoDB
- Full pipeline test: genome → candidate → fitness
- Evolution cycle test with pause boundary

**References:** AGENTS.md §30–31.

**Exit criteria:** CI runs integration tests green.

### Step 13.2 — Calibration and golden assets

**Goal:** Ship reproducible benchmark artifacts.

**Deliverables:**
- `data/golden/genomes.jsonl` (≥500 LHS samples)
- `data/golden/prompts.jsonl` (≥100 cases)
- Version fields wired to bootstrap report

**References:** Bootstrap §9–10.

**Exit criteria:** Bootstrap locality stage runs on committed golden set in CI (smoke subset allowed for speed with full run documented).

### Step 13.3 — Trial publication window

**Goal:** Validate production Telegram behavior.

**Deliverables:**
- Runbook for 50–200 trial posts over ≥7 days
- Metrics: publication_success_rate, engagement_collection_success_rate

**References:** Bootstrap §15.

**Exit criteria:** Mandatory thresholds met or documented waiver with operator approval.

### Step 13.4 — SRS acceptance checklist

**Goal:** Complete SRS §20.

**Deliverables:**
- Traceability matrix: each acceptance criterion → test or runbook
- Fix gaps until all criteria pass

**References:** SRS §20.

**Exit criteria:** All items in SRS §20 marked satisfied with evidence links.

---

## Phase 14 — Documentation and handoff

### Step 14.1 — Align README paths

**Goal:** Remove README/doc path conflict.

**Deliverables:**
- Update README documentation table to actual `docs/*_specification.md` paths

**References:** Conflict table detailed_design §1.10.

**Exit criteria:** README links match repository files.

### Step 14.2 — Update data model specification

**Goal:** Close schema gaps in normative spec.

**Deliverables:**
- Add `bootstrap_reports`, operational collections to `docs/data_model_specification.md` (separate change when approved)

**Exit criteria:** Data model matches implemented repositories.

---

## Dependency graph (summary)

```text
Phase 0 → Phase 1 → Phase 2
              ↓
         Phase 3 → Phase 4
              ↓
         Phase 5 → Phase 6
              ↓
         Phase 7 → Phase 8
              ↓
    Phase 9 (parallel after 8.1 partial)
              ↓
        Phase 10–12 (publication can parallel 10 after 8)
              ↓
         Phase 13–14
```

---

## Implementation rules (agent checklist)

Before marking any step complete:

- [ ] Specification section cited in code only where non-obvious (AGENTS.md §4)
- [ ] Type hints on public APIs
- [ ] No secrets in source
- [ ] Unit tests for deterministic components
- [ ] Integration tests use Testcontainers, not mongomock, for persistence integration
- [ ] LLM unit tests use mocks only
- [ ] CPU-bound locality batches use `run_in_executor` when >10ms expected at population scale

---

## Out of scope for this plan

- Word `.docx` generation (SPEC FORGE §5 optional path—not required when markdown contract is deliverable)
- Web UI, multi-tenant, Kubernetes
- P6 judge and P7 diagnostics (optional post-MVP unless explicitly requested)
- Structural genes and `question_probability` until GA/Mapping specs revised together

---

*This plan is the execution sequence the implementation agent follows after `docs/detailed_design.md` is accepted.*
