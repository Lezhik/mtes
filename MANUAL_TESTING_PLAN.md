# MTES Manual Testing Plan (Initial)

| Field | Value |
|-------|-------|
| Document | MANUAL_TESTING_PLAN.md |
| Audience | Research operator / QA on first local or VPS deployment |
| Language | English |
| Scope | End-to-end **initial** manual validation before production evolution |
| References | `docs/software_requirements_specification.md`, `docs/bootstrap_specification.md`, `docs/acceptance_traceability.md`, `DEVELOPMENT_PLAN.md` |

---

## 1. Purpose

This plan guides **step-by-step manual testing** of MTES from a clean environment through:

1. Parameter and security configuration  
2. MongoDB setup and schema/index readiness  
3. Local LLM (and embedding) provider setup  
4. Dictionary construction and persistence  
5. Initial population creation  
6. Test tweet (phenotype) generation  
7. Test publication to Telegram  
8. Statistics collection from Telegram  
9. Operational report generation  

Use this document as a **checklist**. Record pass/fail, timestamps, and notes in the test log template (Section 12).

---

## 2. Implementation Status Legend

MTES is an MVP in active development. Steps are tagged:

| Tag | Meaning |
|-----|---------|
| **AVAILABLE** | Can be executed today with documented commands or scripts |
| **PARTIAL** | Core logic exists; CLI or provider wiring may require a short script or test harness |
| **PLANNED** | Specified behavior; operator must verify release notes before relying on CLI alone |

At the time of writing:

| Area | Status |
|------|--------|
| Unit/integration automated tests | **AVAILABLE** (`pytest -v` / `-s`) |
| CLI global flags `--json`, `--verbose`, `--verbose-sanitized` | **AVAILABLE** (Section 4.1) |
| `mtes report` | **AVAILABLE** (fixture-backed snapshot) |
| `mtes bootstrap --dry-run` | **AVAILABLE** |
| `mtes bootstrap` (full run) | **PARTIAL** (pipeline modules exist; CLI exits until handlers are wired) |
| `mtes generate` | **PARTIAL** (use pipeline test pattern or direct `GenerationPipeline`) |
| `mtes telegram publish` / `stats` | **PARTIAL** (gateway + publication service tested with mocks; CLI stub exits) |
| Live Ollama/OpenAI adapter in config | **PLANNED** (use mock for pipeline proof; connect local LLM per Section 5) |

When a step is **PARTIAL**, follow the **Alternative verification** subsection so manual testing can still proceed.

---

## 3. Prerequisites

### 3.1 Hardware and OS

| Item | Minimum | Recommended |
|------|---------|-------------|
| RAM | 4 GB | 8+ GB |
| Disk | 10 GB free | SSD |
| OS | Linux/macOS/Windows with Python 3.13 | Linux VPS |
| GPU | Not required | NVIDIA 8+ GB VRAM for local LLM |

### 3.2 Software

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.13+ | `uv` recommended |
| MongoDB | 7+ | Local install or Docker |
| Docker | Optional | For Testcontainers integration tests |
| Ollama (or compatible local server) | Latest | For local LLM manual tests |
| Telegram | Bot token + channel | Bot must be channel admin |

### 3.3 Repository setup

```bash
git clone <repository-url> mtes
cd mtes
uv sync --extra dev
uv pip install -e ".[dev]"
```

Confirm automated baseline:

```bash
uv run pytest tests/unit -q
```

For a more verbose baseline (test names and failures):

```bash
uv run pytest tests/unit -v
```

Expected: all unit tests pass (integration tests may skip without Docker).

---

## 4. Test Environment Layout

Create a dedicated manual-test workspace (do not use production data):

```text
mtes/
├── config/config.yaml          # operator copy from config.example.yaml
├── runtime/                    # PID files (created by daemon)
├── reports/                    # HTML/JSON reports (created by mtes report)
├── data/manual/                # optional: dictionary export, population export
└── logs/                       # operator notes / screenshots
```

---

## 4.1 CLI and diagnostic output modes

MTES supports **global CLI flags** (SRS §15.3–15.4, §16). They apply to all subcommands and must appear **before** the subcommand name.

```bash
uv run mtes [GLOBAL_FLAGS] <subcommand> [SUBCOMMAND_OPTIONS]
```

### Global flags

| Flag | Purpose | When to use in manual testing |
|------|---------|-------------------------------|
| `--config PATH` | Load YAML configuration | Every CLI step after Phase A.1 |
| `--json` | Machine-readable JSON on stdout | Automation, log archives, CI-style checks |
| `--verbose` | Human-readable diagnostic payload on stdout | Step-by-step manual runs; see command result details |
| `--verbose-sanitized` | Verbose output intended for shared logs (secrets redacted per SRS) | Screen sharing, tickets, peer review — **prefer over `--verbose` when passing `--operator-token`** |

**Precedence:** If `--json` is set, stdout uses JSON only; `--verbose` / `--verbose-sanitized` do not change JSON output.

**Silent success:** Without `--json`, `--verbose`, or `--verbose-sanitized`, many commands emit **no stdout** on success. For manual testing, always add `--verbose` or `--json` unless you intentionally test silent behavior.

**Recommended default for this plan:**

```bash
# Interactive manual testing (readable)
export MTES_CLI_FLAGS="--verbose --config config/config.yaml"

# Evidence capture / scripting
export MTES_CLI_JSON="--json --config config/config.yaml"
```

Example:

```bash
uv run mtes $MTES_CLI_FLAGS bootstrap --dry-run
uv run mtes $MTES_CLI_JSON report
```

### Commands that support CLI output today

| Subcommand | `--json` | `--verbose` / `--verbose-sanitized` | Notes |
|------------|----------|--------------------------------------|-------|
| `bootstrap --dry-run` | Yes | Yes | Prints stage list payload |
| `bootstrap` (full) | On failure only | On failure only | Exits with bootstrap failed until wired |
| `evolution <action>` | Yes (on success) | Yes | Prints `evolution_action`, `status` |
| `report` | Yes | Yes | Prints report file paths and generation number |
| `daemon start` | No | Yes | Heartbeat payloads when `--verbose` |
| `generate` | Planned | Planned | Use pytest verbose harness (Phase F) |
| `telegram …` | Planned | Planned | Use curl / pytest (Phase G) |

### Non-CLI verbose diagnostics

| Tool | Verbose option | Use for |
|------|----------------|---------|
| `pytest` | `-v` (names), `-vv` (detail), `-s` (stdout) | Pipeline, gateway, maintenance proofs |
| `mongosh` | Default pretty output | Inspect persisted documents |
| `curl` | Omit `-s` to see HTTP status | Telegram API smoke tests |
| `scripts/create_vector_indexes.py` | stdout messages on success | Index creation confirmation |
| `scripts/run_maintenance.py` | stdout summary line | TTL purge counts |

**Example — verbose pytest for generation proof:**

```bash
uv run pytest tests/unit/test_generation_pipeline.py -v -s
```

---

## Phase A — Parameter and Security Configuration

**Goal:** Validate configuration loading, operator auth, and monitoring ports.

### Step A.1 — Create configuration file (**AVAILABLE**)

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` for your environment:

```yaml
database:
  connection_string: mongodb://localhost:27017/mtes_manual

daemon:
  worker_count: 1
  generation_queue_size: 100
  publication_queue_size: 100
  resume_threshold: 50

monitoring:
  health_port: 8080
  metrics_port: 9090

metrics:
  locality_measurement_interval: 100

security:
  evolution_confirmation_required: true
  reset_requires_confirmation: true
  operator_auth_source: environment
```

**Pass criteria:** File exists; values match your host ports and MongoDB database name (`mtes_manual`).

### Step A.2 — Set operator environment variables (**AVAILABLE**)

```bash
# Linux/macOS
export MTES_OPERATOR_TOKEN="<long-random-secret>"
export MTES_OPERATOR_ALLOW_LIST="operator-1"
export MTES_MONGODB_URI="mongodb://localhost:27017/mtes_manual"
export MTES_CONFIG_PATH="$(pwd)/config/config.yaml"
```

Windows PowerShell:

```powershell
$env:MTES_OPERATOR_TOKEN = "<long-random-secret>"
$env:MTES_OPERATOR_ALLOW_LIST = "operator-1"
$env:MTES_MONGODB_URI = "mongodb://localhost:27017/mtes_manual"
$env:MTES_CONFIG_PATH = "$(Get-Location)\config\config.yaml"
```

**Pass criteria:** Variables visible in shell (`echo $MTES_OPERATOR_TOKEN`).

### Step A.3 — Verify evolution admin authentication (**AVAILABLE**)

**JSON mode** (for logs and scripting):

```bash
uv run mtes --json --config config/config.yaml evolution pause \
  --operator-id operator-1 --operator-token "<token>"
```

Expected: JSON with `"status": "accepted"` and exit code `0`.

**Verbose mode** (for interactive manual testing; use sanitized when sharing output):

```bash
uv run mtes --verbose-sanitized --config config/config.yaml evolution pause \
  --operator-id operator-1 --operator-token "<token>"
```

Expected: readable payload containing `accepted` and exit code `0`.

Negative test (wrong token):

```bash
uv run mtes --verbose evolution pause --operator-id operator-1 --operator-token "wrong"
```

Expected: non-zero exit (general error); no successful payload.

### Step A.4 — Record experiment metadata (**AVAILABLE**)

For manual runs, fix metadata used in persisted documents:

| Variable | Example | Purpose |
|----------|---------|---------|
| `MTES_SCHEMA_VERSION` | `3.4` | Data model schema stamp |
| `MTES_EXPERIMENT_ID` | `manual_test_001` | Experiment isolation |
| `MTES_RUN_ID` | `run_2026_06_03` | Run traceability |

```bash
export MTES_SCHEMA_VERSION="3.4"
export MTES_EXPERIMENT_ID="manual_test_001"
export MTES_RUN_ID="run_2026_06_03"
```

**Pass criteria:** Values documented in test log.

---

## Phase B — Database Setup

**Goal:** MongoDB reachable, collections writable, indexes ready.

### Step B.1 — Start MongoDB (**AVAILABLE**)

**Option 1 — Docker:**

```bash
docker run -d --name mtes-mongo -p 27017:27017 mongo:7
```

**Option 2 — Local service:** start `mongod` per OS documentation.

**Pass criteria:**

```bash
mongosh "mongodb://localhost:27017/mtes_manual" --eval "db.runCommand({ ping: 1 })"
```

Returns `{ ok: 1 }`.

### Step B.2 — Verify persistence client (**AVAILABLE**)

```bash
uv run pytest tests/integration/test_mongo_client.py -v
```

If Docker is unavailable, skip with note and verify `mongosh` ping only.

**Pass criteria:** Test passes or documented skip with successful ping.

### Step B.3 — Repository round-trip (**AVAILABLE**)

```bash
uv run pytest tests/integration/test_repositories.py -v
```

**Pass criteria:** Genome and candidate insert/load succeed.

### Step B.4 — Operational collections (**AVAILABLE**)

```bash
uv run pytest tests/integration/test_operational_repositories.py -v
```

**Pass criteria:** `bootstrap_reports`, `workflow_state`, `publication_queue` repositories accept documents.

### Step B.5 — Embedding model metadata and vector indexes (**PARTIAL**)

1. Insert embedding model metadata (example for local embeddings, dimension must match adapter):

```javascript
// mongosh mtes_manual
db.embedding_models.insertOne({
  _id: "local-e5-manual",
  version: "1.0",
  dimension: 384,
  distance_metric: "cosine",
  schema_version: "3.4",
  experiment_id: "manual_test_001",
  run_id: "run_2026_06_03",
  created_at: new Date().toISOString()
});
```

2. Create vector indexes (when Atlas Vector Search or compatible index API is configured):

```bash
uv run python scripts/create_vector_indexes.py --config config/config.yaml --dry-run
uv run python scripts/create_vector_indexes.py --config config/config.yaml
```

Scripts print progress to stdout (verbose by default). Capture terminal output for evidence.

**Pass criteria:** `embedding_models` document exists; index script completes without error (or dry-run output reviewed).

### Step B.6 — Maintenance TTL smoke (**AVAILABLE**, requires Docker)

```bash
uv run pytest tests/integration/test_maintenance_ttl.py -v
```

**Pass criteria:** Aged `phenotype_candidates` removed; recent document retained.

**Alternative without Docker:** run maintenance script against manual DB after inserting old/new documents with `created_at` timestamps.

```bash
uv run python scripts/run_maintenance.py
```

Expect a one-line summary (`maintenance_complete`, deleted counts) on stdout.

---

## Phase C — Local LLM and Embedding Setup

**Goal:** Confirm a local model can serve as the constrained phenotype compiler (and embeddings for mapping).

### Step C.1 — Install and start Ollama (**AVAILABLE**)

```bash
# Install from https://ollama.com per OS instructions
ollama pull mistral:7b-instruct
ollama serve
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

**Pass criteria:** Model list includes chosen instruct model.

### Step C.2 — Sanity-check completion API (**AVAILABLE**)

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "mistral:7b-instruct",
  "prompt": "Return JSON only: {\"candidate_text\": \"winter silence\"}",
  "stream": false
}'
```

**Pass criteria:** Response contains coherent text; latency acceptable (< 60 s on target hardware).

### Step C.3 — Wire MTES to local LLM (**PLANNED / PARTIAL**)

**Target architecture (per README):** local instruct model as **compiler**, not semantic author. Provider adapter must enforce JSON/schema phases P3/P4/P5.

**Interim manual proof (no live Ollama adapter required):**

```bash
uv run pytest tests/unit/test_generation_pipeline.py -v -s
uv run pytest tests/integration/test_pipeline_evolution.py -v
```

**Pass criteria:** Pipeline produces candidate text, fitness > 0, anchor integrity computed. With `-s`, generation output is visible in the terminal.

**When Ollama adapter is configured**, extend `config/config.yaml`:

```yaml
# Appendix — add when provider section is implemented
providers:
  primary:
    type: ollama
    base_url: http://localhost:11434
    model: mistral:7b-instruct
    timeout_seconds: 120
  embedding:
    type: local
    model_id: local-e5-manual
    dimension: 384
```

Repeat Step C.2 with `mtes generate` once CLI is wired.

### Step C.4 — Local embeddings (**PARTIAL**)

Bootstrap requires embedding validation and cached vectors for locality calibration.

**Interim:** use golden dataset embeddings in `data/golden/genomes.jsonl` for calibration smoke:

```bash
uv run pytest tests/unit/test_golden_assets.py -v
```

**Pass criteria:** Smoke subset runs; Spearman correlation in [-1, 1].

**Production manual test:** point embedding adapter at local sentence-transformers or Ollama embedding endpoint; persist `embedding_models` (Step B.5).

---

## Phase D — Dictionary Construction

**Goal:** Build semantic dictionary (5,000+ pool; MVP evolution uses 2,000–3,000 active tokens per specs).

### Step D.1 — Prepare dictionary JSON (**AVAILABLE**)

Format (see `tests/fixtures/dictionary_terms.json`):

```json
[
  {
    "token": "winter",
    "coordinate": [3, 5, 4, 2, 3],
    "bucket_id": "bucket_014",
    "axis_scores": [0.42, 0.51, 0.38, 0.47, 0.44]
  }
]
```

For manual testing:

1. Start from `tests/fixtures/dictionary_terms.json` for smoke.  
2. For broader test, export/bootstrap a larger list into `data/manual/dictionary_terms.json` (≥ 50 terms minimum for meaningful tests; production bootstrap targets 5,000+).

### Step D.2 — Load and validate in process (**AVAILABLE**)

```bash
uv run python -c "
from pathlib import Path
from mtes.mapping.dictionary_service import load_dictionary_from_json
svc = load_dictionary_from_json(Path('tests/fixtures/dictionary_terms.json'), dictionary_version='manual-1.0')
print('terms', len(svc._by_token))
print('anchor', svc.resolve_anchor((3, 5, 4, 2, 3)))
report = svc.compute_axis_correlation_report()
print('axis_warning', report.warning, 'max_corr', report.max_absolute_correlation)
"
```

This inline script acts as a **verbose dictionary check** (stdout diagnostics).

**Pass criteria:** No exception; axis correlation report printed; oversized buckets empty or documented.

### Step D.3 — Persist dictionary to MongoDB (**PARTIAL**)

Insert terms into `dictionary_terms` and buckets into `dictionary_buckets` via application bootstrap stage or manual script.

**Manual insert example (single term):**

```javascript
db.dictionary_terms.insertOne({
  _id: "term_winter",
  token: "winter",
  coordinate: [3, 5, 4, 2, 3],
  bucket_id: "bucket_014",
  axis_scores: [0.42, 0.51, 0.38, 0.47, 0.44],
  dictionary_version: "manual-1.0",
  schema_version: "3.4",
  experiment_id: "manual_test_001",
  run_id: "run_2026_06_03",
  created_at: new Date().toISOString()
});
```

Automated coverage:

```bash
uv run pytest tests/unit/test_dictionary_service.py -v
```

**Pass criteria:** Terms retrievable; `dictionary_version` recorded consistently.

### Step D.4 — Bootstrap stage check (**AVAILABLE**)

Compare output modes:

```bash
# JSON — for logs / automation
uv run mtes --json --config config/config.yaml bootstrap --dry-run

# Verbose — for interactive walkthrough
uv run mtes --verbose --config config/config.yaml bootstrap --dry-run
```

**Pass criteria:** Output lists stages in order; includes `dictionary_construction` before `initial_population_generation`.

---

## Phase E — Initial Population Formation

**Goal:** Create generation-0 genomes and population members per GA spec (six numeric genes, semantic genes with anchors).

### Step E.1 — Define test genomes (**AVAILABLE**)

Use golden assets or hand-crafted genomes:

```bash
uv run python -c "
from pathlib import Path
from mtes.core.golden_loaders import load_golden_dataset
records = load_golden_dataset(Path('data/golden/genomes.jsonl'))
print('loaded', len(records), 'first', records[0].genome.genome_id)
"
```

### Step E.2 — In-memory population (**AVAILABLE**)

```bash
uv run pytest tests/unit/test_ga_operators.py -v
```

**Pass criteria:** Population service holds target size; mutation/crossover run without error.

### Step E.3 — Persist initial population (**PARTIAL**)

Insert into `genomes` and `population_members`:

```javascript
db.genomes.insertOne({
  _id: "genome_manual_001",
  generation: 0,
  semantic_genes: [{ gene_id: 1, coordinate: [3,5,4,2,3], anchor: "winter" }],
  numeric_genes: {
    fragmentation_bias: 0.5,
    ambiguity_bias: 0.45,
    sentiment_contrast: 0.4,
    semantic_jump_radius: 0.35,
    compression_target: 0.55,
    anchor_rigidity: 0.7
  },
  parent_ids: [],
  seed: 12345,
  dictionary_version: "manual-1.0",
  mapping_version: "5.0",
  schema_version: "3.4",
  experiment_id: "manual_test_001",
  run_id: "run_2026_06_03",
  created_at: new Date().toISOString()
});

db.population_members.insertOne({
  _id: "pop_member_001",
  genome_id: "genome_manual_001",
  fitness_rank: 1.0,
  schema_version: "3.4",
  experiment_id: "manual_test_001",
  run_id: "run_2026_06_03",
  created_at: new Date().toISOString()
});
```

**Pass criteria:** `genomes` and `population_members` documents present in `mongosh`.

### Step E.4 — Evolution state (**AVAILABLE**)

```bash
uv run pytest tests/unit/test_evolution_bootstrap_gate.py -v
```

Insert bootstrap report with `readiness_status: "READY"` before testing `RUNNING` transition in integrated environments.

---

## Phase F — Test Tweet (Phenotype) Generation

**Goal:** Produce short-form text candidates from genomes with validation and fitness.

### Step F.1 — Single-generation pipeline (**AVAILABLE**)

```bash
uv run pytest tests/unit/test_generation_pipeline.py::test_generation_pipeline_produces_archived_candidate -v -s
```

**Pass criteria:** Output includes winter-related text; fitness > 0; routing family set. Use `-s` to surface any print/logging from the pipeline during manual review.

### Step F.2 — Manual inspection of candidate fields (**AVAILABLE**)

Record in test log:

| Field | Expected |
|-------|----------|
| `candidate_text` | Short text, anchor visible |
| `validation_status` | Passes validation rules |
| `anchor_integrity` | ≥ 0.85 for bootstrap gates |
| `fitness` | Computed scalar > 0 |

### Step F.3 — Persist phenotype candidate (**PARTIAL**)

```javascript
db.phenotype_candidates.insertOne({
  _id: "candidate_manual_001",
  genome_id: "genome_manual_001",
  text: "winter silence drifts slowly",
  routing_family: "P4-C",
  prompt_version: "1.0",
  validation_status: "passed",
  schema_version: "3.4",
  experiment_id: "manual_test_001",
  run_id: "run_2026_06_03",
  created_at: new Date().toISOString()
});
```

**Pass criteria:** Document readable; text matches generated sample.

### Step F.4 — CLI generate (**PLANNED**)

When implemented, run with verbose or JSON per need:

```bash
# Human-readable summary (fitness, novelty, anchor integrity, text)
uv run mtes --verbose --config config/config.yaml generate

# Structured output for archiving
uv run mtes --json --config config/config.yaml generate
```

Until wired, keep **PARTIAL** and use Step F.1 (`pytest -v -s`).

---

## Phase G — Test Publication to Telegram

**Goal:** Publish test tweets to a private channel without exceeding rate limits.

### Step G.1 — Telegram bot and channel (**AVAILABLE**)

1. Create bot via [@BotFather](https://t.me/BotFather); save **bot token**.  
2. Create private channel; add bot as **administrator** with post permission.  
3. Obtain **channel ID** (e.g. `-100xxxxxxxxxx`).

Store secrets outside git:

```bash
export MTES_TELEGRAM_BOT_TOKEN="<bot-token>"
export MTES_TELEGRAM_CHANNEL_ID="-100xxxxxxxxxx"
```

### Step G.2 — Direct API smoke (**AVAILABLE**)

```bash
# Verbose curl (shows HTTP status and response body)
curl "https://api.telegram.org/bot${MTES_TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${MTES_TELEGRAM_CHANNEL_ID}" \
  -d "text=MTES manual test post — safe to delete"
```

**Pass criteria:** HTTP 200; `"ok":true` in response body; message visible in channel.

### Step G.3 — MTES gateway publish (**PARTIAL**)

Automated mock coverage:

```bash
uv run pytest tests/unit/test_telegram_publication.py::test_telegram_publish_respects_rate_limit_and_records_message -v
```

**Manual wiring example (Python REPL):**

```python
import asyncio
from mtes.core.operator_auth import OperatorAuthService
from mtes.telegram.telegram_gateway import TelegramGateway, TelegramApiClient

# Implement TelegramApiClient using httpx + MTES_TELEGRAM_* env vars

async def main() -> None:
    gateway = TelegramGateway(
        api_client=...,  # your live client
        channel_id="<channel-id>",
        operator_auth=OperatorAuthService.from_environment(),
    )
    result = await gateway.publish_text("MTES gateway manual test")
    print(result)

asyncio.run(main())
```

**Pass criteria:** Message appears in channel; `mtes_publication_total` increments (Section H).

### Step G.4 — Publication queue (**PARTIAL**)

```bash
uv run pytest tests/unit/test_telegram_publication.py::test_publication_service_processes_queue_item -v
```

Enqueue via `PublicationService.enqueue_publication` then `process_pending_publications`.

**Rate limit:** default **30 messages/minute** (SRS §8.3). Space manual posts ≥ 2 seconds apart.

### Step G.5 — CLI telegram (**PLANNED**)

```bash
uv run mtes --verbose --config config/config.yaml telegram publish
uv run mtes --json --config config/config.yaml telegram stats
```

Track implementation status in `docs/acceptance_traceability.md`.

---

## Phase H — Statistics Collection from Telegram

**Goal:** Collect publication and engagement statistics for reports and bootstrap thresholds.

### Step H.1 — Prometheus metrics (**AVAILABLE**)

Start monitoring (when HTTP server is deployed with stack):

```bash
curl -s http://localhost:9090/metrics | findstr mtes_
```

Linux/macOS:

```bash
curl -s http://localhost:9090/metrics | grep mtes_
```

Record:

| Metric | Use |
|--------|-----|
| `mtes_publication_total` | Published message count |
| `mtes_telegram_failures_total` | Failed publishes |
| `mtes_generation_total` | Generation attempts |
| `mtes_locality_correlation` | Latest locality gauge |

**Pass criteria:** Metrics endpoints respond; counters increment after Phase G.

### Step H.2 — Telegram channel statistics (**AVAILABLE**)

For manual MVP, collect:

| Statistic | Source |
|-----------|--------|
| Posts sent | Count manual/API posts |
| Failures | Gateway logs / `mtes_telegram_failures_total` |
| Views/reactions | Telegram channel statistics UI |

Optional Bot API (if message IDs recorded):

```bash
curl -s "https://api.telegram.org/bot${MTES_TELEGRAM_BOT_TOKEN}/getChat" \
  -d "chat_id=${MTES_TELEGRAM_CHANNEL_ID}"
```

### Step H.3 — SRS CLI stats (**PLANNED**)

```bash
uv run mtes --verbose --config config/config.yaml telegram stats
uv run mtes --json --config config/config.yaml telegram stats
```

**Pass criteria (when implemented):** JSON includes last-24h summary per SRS §8.2; verbose mode prints human-readable 24h summary per SRS §8.2.

### Step H.4 — Trial window metrics (**AVAILABLE** — process)

For bootstrap readiness, follow `docs/runbooks/trial_publication.md`:

| Metric | Threshold |
|--------|-----------|
| `publication_success_rate` | ≥ 0.99 |
| `engagement_collection_success_rate` | ≥ 0.95 |

Document results in test log even if full 7-day window is shortened for **initial** manual test (note deviation).

---

## Phase I — Report Generation

**Goal:** Produce HTML and JSON operational reports under `./reports/`.

### Step I.1 — Generate reports (**AVAILABLE**)

```bash
mkdir -p reports

# JSON stdout + files on disk
uv run mtes --json --config config/config.yaml report

# Verbose stdout (paths and generation number)
uv run mtes --verbose --config config/config.yaml report
```

Verify files:

```bash
ls reports/mtes_report_*.json reports/mtes_report_*.html
```

**Pass criteria:** Both files exist; CLI prints paths with `--json` or `--verbose`; HTML shows evolution summary and recent content sections.

### Step I.2 — Validate JSON schema (**AVAILABLE**)

Check fields per SRS §9.2:

| Section | Required fields |
|---------|-----------------|
| `evolution_summary` | `generation_number`, `fitness_mean`, `fitness_std`, `locality_correlation`, `locality_correlation_std`, `anchor_integrity_mean` |
| `recent_content[]` | `generation_number`, `fitness_score`, `novelty_score`, `anchor_integrity`, `text` |

### Step I.3 — Performance (**AVAILABLE**)

Time the command:

```bash
uv run mtes --verbose --config config/config.yaml report
```

**Pass criteria:** Completes in **< 5 minutes** (SRS §18.4 recommended); typical fixture run **< 10 seconds**.

### Step I.5 — Daemon heartbeat verbose (**AVAILABLE**)

```bash
uv run mtes --verbose --config config/config.yaml daemon start
```

Interrupt with Ctrl+C after a few heartbeats. **Pass criteria:** Periodic `daemon` heartbeat payloads on stdout when `--verbose` is set.

### Step I.4 — Connect live MongoDB snapshot (**PLANNED**)

When `ReportDataSource` reads evolution/fitness collections, re-run after Phases E–F and confirm report reflects stored generation and candidates.

---

## Phase J — End-to-End Manual Sign-Off

Execute in order on a single run ID:

| # | Phase | Pass? | Notes |
|---|-------|-------|-------|
| 1 | A — Configuration | ☐ | |
| 2 | B — Database | ☐ | |
| 3 | C — Local LLM | ☐ | |
| 4 | D — Dictionary | ☐ | |
| 5 | E — Initial population | ☐ | |
| 6 | F — Tweet generation | ☐ | |
| 7 | G — Telegram publish | ☐ | |
| 8 | H — Statistics | ☐ | |
| 9 | I — Reports | ☐ | |

**Initial manual test complete** when all **AVAILABLE** steps pass and **PARTIAL** steps have documented alternatives with evidence (test output, screenshots, or mongosh exports).

---

## 10. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `mtes bootstrap` exits code 3 | Full bootstrap not wired to CLI | Use `--dry-run`; run module tests |
| `mtes generate` fails | CLI stub | Use `test_generation_pipeline` |
| `mtes telegram` exits code 6 | CLI stub | Use gateway unit test or curl API |
| Mongo connection refused | Mongo not running | Step B.1 |
| Operator auth fails | Missing env vars | Step A.2 |
| Evolution will not start | Bootstrap `NOT_READY` | Insert `bootstrap_reports` with `READY` |
| Publish hangs | Rate gate 30/min | Wait 2 s between posts |
| Report empty summary | Fixture snapshot default | Expected until DB-backed reports |
| Integration tests skip | No Docker | Install Docker or accept skip |
| CLI succeeds but prints nothing | No `--json` / `--verbose` | Add flags per Section 4.1 |
| `--verbose` shows token values | Sensitive command line | Use `--verbose-sanitized` and env-based tokens |

---

## 11. Evidence to Archive

For audit traceability (SRS §20), keep:

- `config/config.yaml` redacted copy (no secrets)  
- Test log (Section 12)  
- `reports/mtes_report_*.json` and `.html`  
- `mongosh` export of sample `genomes`, `phenotype_candidates`, `bootstrap_reports`  
- Screenshot of Telegram test channel  
- `curl` output for `/health` and `/metrics`  
- pytest summary: `uv run pytest tests/unit tests/integration -v`  
- CLI transcripts with `--verbose` or `--json` where applicable  

---

## 12. Manual Test Log Template

```text
Tester:         
Date:           
Run ID:         
Environment:    local | VPS
Git commit:     
CLI output mode:  verbose | verbose-sanitized | json | mixed

Phase A  [ ] PASS  [ ] FAIL  Notes:
Phase B  [ ] PASS  [ ] FAIL  Notes:
Phase C  [ ] PASS  [ ] FAIL  Notes:
Phase D  [ ] PASS  [ ] FAIL  Notes:
Phase E  [ ] PASS  [ ] FAIL  Notes:
Phase F  [ ] PASS  [ ] FAIL  Notes:
Phase G  [ ] PASS  [ ] FAIL  Notes:
Phase H  [ ] PASS  [ ] FAIL  Notes:
Phase I  [ ] PASS  [ ] FAIL  Notes:

Overall: [ ] APPROVED FOR EXTENDED TRIAL  [ ] BLOCKED
Approver:
```

---

## 13. Related Documents

| Document | Path |
|----------|------|
| Development plan | `DEVELOPMENT_PLAN.md` |
| Acceptance traceability | `docs/acceptance_traceability.md` |
| Trial publication runbook | `docs/runbooks/trial_publication.md` |
| Bootstrap specification | `docs/bootstrap_specification.md` |
| Software requirements | `docs/software_requirements_specification.md` |

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-03 | MTES team | Initial manual testing plan |
| 1.1 | 2026-06-03 | MTES team | Added CLI verbose/JSON modes and diagnostic flags throughout |
