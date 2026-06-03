# MTES — Mutation-Traceable Evolutionary Synthesis

![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-7%2B-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Status](https://img.shields.io/badge/Status-MVP--Implementation-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

MTES is a specification-first research project investigating whether measurable genotype–phenotype locality can be preserved in an LLM-assisted evolutionary system.

---

# Current Project Status

## Current Stage

**MVP implementation in progress** on branch `develop`.

The repository contains normative specifications under `docs/` and a Python 3.13 implementation under `src/mtes/`.

Implemented areas include persistence, mapping, GA operators, LLM adapters (mock/test), bootstrap calibration, CLI, daemon, Telegram gateway, publication queue, reporting, and maintenance workers.

Some operator workflows (live Telegram trial window, production provider calls) still require VPS deployment and manual runbooks.

See `DEVELOPMENT_PLAN.md` and `docs/acceptance_traceability.md` for remaining acceptance items.

---

# What Is MTES?

MTES (Mutation-Traceable Evolutionary Synthesis) is a research platform for evolutionary text generation.

The project investigates:

* genotype–phenotype locality
* mutation traceability
* evolutionary stability
* constrained LLM generation
* measurable evolutionary dynamics

The system treats LLMs as constrained phenotype compilers rather than semantic authors.

## Primary Research Question

> Can measurable genotype–phenotype locality be maintained in an LLM-assisted evolutionary system?

The goal is not maximal text quality.

The goal is measurable evolutionary behavior.

---

# Why Specification-First?

MTES follows a specification-first development process.

The project intentionally defines:

* architecture
* data model
* evolutionary behavior
* operational requirements
* bootstrap procedures
* monitoring requirements

before implementation begins.

The objective is to reduce architectural drift, improve reproducibility, and provide a stable foundation for future implementation and experimentation.

---

# Architecture Overview

```text
Genome
    ↓
Deterministic Translation
    ↓
Anchor Selection
    ↓
Semantic Expansion
    ↓
Relation Graph
    ↓
Structural Planning
    ↓
Constrained LLM Compilation
    ↓
Validation
    ↓
Fitness Evaluation
    ↓
Archive
```

---

# Illustrative Genome → Phenotype Example

The following example is illustrative.

```text
Input Genome

Anchors:
    automation
    fatigue

fragmentation_bias: 0.72
compression_target: 0.81
sentiment_contrast: 0.60
```

```text
↓
```

```text
Generated Text

"Automation became ritual long before anyone noticed."
```

```text
Fitness: 0.74
Novelty: 0.63
Anchor Integrity: 0.92
```

---

# Planned Capabilities

The following capabilities are planned for future implementation:

* deterministic genotype-to-constraint translation
* constrained LLM compilation
* evolutionary population management
* genotype–phenotype locality measurement
* mutation traceability analysis
* automated validation and repair
* Telegram publication
* operational monitoring
* daemon-style background execution
* reproducible experimentation

---

# Recommended Reading Order

For researchers and contributors new to the project:

1. README
2. Architecture Specification
3. Genotype–Phenotype Mapping Specification
4. Genetic Algorithm Specification
5. LLM Interaction Specification
6. Data Model Specification
7. Bootstrap & Calibration Specification
8. Software Requirements Specification

This order prioritizes understanding the research model before operational details.

---

# Documentation

| Document                                 | Location                                      |
| ---------------------------------------- | --------------------------------------------- |
| Architecture Specification               | docs/architecture_specification.md            |
| Data Model Specification                 | docs/data_model_specification.md              |
| Genotype–Phenotype Mapping Specification | docs/mapping_specification.md                 |
| Genetic Algorithm Specification          | docs/genetic_algorithm_specification.md       |
| LLM Interaction Specification            | docs/llm_interaction_specification.md           |
| Bootstrap & Calibration Specification    | docs/bootstrap_specification.md               |
| Software Requirements Specification      | docs/software_requirements_specification.md   |
| Detailed Design (implementation contract)| docs/detailed_design.md                         |
| Development Plan                         | DEVELOPMENT_PLAN.md                             |
| Acceptance traceability (SRS §20)        | docs/acceptance_traceability.md               |

---

# Future Usage Example (Planned Interface)

The following workflow illustrates the intended user experience after implementation begins.

## Environment Setup

```bash
git clone https://github.com/example/mtes.git

cd mtes

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

## Configuration

```bash
cp config.example.yaml config.yaml
```

Edit:

```yaml
providers:
  primary: openai

database:
  connection_string: mongodb://localhost:27017/mtes
```

## Bootstrap

```bash
mtes bootstrap
```

## Generate

```bash
mtes generate
```

Example output:

```text
Generation completed

Fitness: 0.74
Novelty: 0.63
Anchor Integrity: 0.92

Generated Text:
"Automation became ritual long before anyone noticed."
```

## Planned Next Steps

```bash
mtes evolution status

mtes generate --daemon

mtes telegram --daemon
```

---

# Technical Requirements

## Minimum

* Python 3.13+
* MongoDB 7+
* 4 GB RAM
* Internet access
* LLM provider credentials

## Recommended

* 8+ GB RAM
* SSD storage
* Linux environment
* Docker Compose

GPU is not required.

---

# MongoDB and In-Memory Cosine Retrieval

MTES uses **MongoDB 7+** as a document store only. **MongoDB Atlas is not required.** Atlas Search, Atlas Vector Search, and full-text search indexes are **not used**.

Semantic nearest-neighbor lookup (dictionary expansion, archive retrieval, bootstrap `retrieval_consistency`) runs in **application memory** using **cosine similarity** over embedding vectors loaded from MongoDB documents.

## Connection

```yaml
# config/config.yaml
database:
  connection_string: mongodb://localhost:27017/mtes
```

Environment override:

```bash
export MTES_MONGODB_URI="mongodb://localhost:27017/mtes"
```

Works with:

* local `mongod`
* Docker: `docker run -d -p 27017:27017 mongo:7`
* any MongoDB 7+ deployment that exposes the standard wire protocol

**No Atlas-specific connection options or search indexes are needed.**

## Required setup steps

1. Start MongoDB 7+ and create a database (for example `mtes`).
2. Insert at least one `embedding_models` document before bootstrap retrieval validation:

```javascript
db.embedding_models.insertOne({
  _id: "local-e5-manual",
  version: "1.0",
  dimension: 384,
  distance_metric: "cosine"
});
```

3. Ensure standard B-tree indexes (not vector search indexes):

```bash
uv run python scripts/ensure_mongodb_indexes.py --config config/config.yaml
```

Dry run:

```bash
uv run python scripts/ensure_mongodb_indexes.py --config config/config.yaml --dry-run
```

## Operational notes

| Topic | Guidance |
|-------|----------|
| Embedding storage | Vectors live in document fields (`embedding` arrays on `dictionary_terms`, `candidate_archive`, `tweet_archive`) |
| Similarity | Computed in Python via `InMemoryCosineRetrieval` (`src/mtes/persistence/in_memory_cosine_retrieval.py`) |
| RAM | Size in-memory corpora to available RAM; default load limit is 10,000 documents per retrieval query |
| Indexes | Standard MongoDB indexes on `token`, `genome_id`, `created_at`, etc. — created by `ensure_mongodb_indexes.py` |
| Atlas | Optional as a hosted MongoDB provider only if **Search/Vector Search features stay disabled** |

---

## Optional Local Models

Example local models:

* Mistral 7B Instruct
* Qwen Instruct
* Llama Instruct

Mistral-class models are expected to be suitable MVP compiler candidates.

Recommended local-model hardware:

* NVIDIA GPU
* CUDA 12+
* 8+ GB VRAM

---

# Cost and Hardware Notes

MTES may use external LLM providers.

Potential costs depend on:

* provider
* model
* generation volume
* calibration workload

Examples:

* OpenAI API
* Anthropic API
* OpenRouter-compatible providers

Development and testing should use conservative generation limits whenever possible.

---

## Bootstrap Timing

Technical Bootstrap:

```text
10–60 minutes
```

depending on:

* hardware
* network
* provider responsiveness

Trial Publication Period:

```text
minimum 7 days
```

Full Bootstrap Validation:

```text
7+ days
```

including trial publication observation.

---

# Example JSON Output

## Generation

```json
{
  "generation_number": 154,
  "genome_id": "gen_001",
  "phenotype": "Automation became ritual long before anyone noticed.",
  "fitness": 0.85,
  "novelty": 0.63,
  "anchor_integrity": 0.92,
  "repair_cost": 0.12,
  "validation": "PASSED",
  "timestamp": "2026-01-01T00:00:00Z"
}
```

## Telegram Statistics

```json
{
  "period": "24h",
  "publications": 12,
  "views": 1042,
  "reactions": 76,
  "forwards": 18
}
```

---

# Monitoring

## Health Endpoint

```text
GET /health
```

Example:

```json
{
  "status": "healthy",
  "evolution_status": "RUNNING",
  "queue_depth": 4,
  "active_workers": 1
}
```

Possible evolution_status values:

```text
CREATED
RUNNING
PAUSED
STOPPING
STOPPED
RESETTING
FAILED
```

See the Software Requirements Specification for lifecycle details.

---

## Metrics Endpoint

```text
GET /metrics
```

Prometheus-compatible output.

---

# Performance Targets

| Operation           | Target        |
| ------------------- | ------------- |
| Technical Bootstrap | < 60 minutes  |
| Single Generation   | < 60 seconds  |
| Report Generation   | < 5 minutes   |
| Health Endpoint     | < 1 second    |
| State Restoration   | < 60 seconds  |
| Daemon Recovery     | < 120 seconds |

Provider-dependent variation is expected.

### Note

A single generation may involve multiple LLM interactions, including:

* constraint expansion
* phenotype compilation
* candidate generation
* validation
* repair workflows

See the LLM Interaction Specification for pipeline details.

---

# Logging

Default log location:

```text
./logs/mtes.log
```

Planned audit events:

* evolution pause
* evolution resume
* evolution stop
* evolution reset

---

# Environment Variables

Example:

```text
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
```

---

# Troubleshooting (Future Implementation)

The following examples describe intended diagnostic workflows.

## MongoDB Connection Failed

```bash
mongosh mongodb://localhost:27017
```

## Provider Validation Failed

```bash
echo $OPENAI_API_KEY
```

## Bootstrap Failure

```bash
mtes bootstrap --verbose
```

```bash
cat ./logs/mtes.log
```

## Daemon Failure

```bash
curl http://localhost:8080/health
```

```bash
cat ./logs/mtes.log
```

---

# Windows Notes

Windows is expected to be supported.

Recommendations:

* PowerShell
* Python 3.13+
* WSL2 for long-running execution

Behavior differences:

* Ctrl+C is the primary shutdown mechanism
* SIGTERM is not natively supported

Linux is strongly recommended for production deployments.

---

# Reports

Planned report location:

```text
./reports/
```

Example:

```bash
ls -la ./reports/
```

---

# Contributing

Contributions are welcome.

Particularly valuable contributions include:

* evolutionary computation research
* locality measurement improvements
* fitness function experiments
* provider comparisons
* validation methodology improvements
* bug reports with reproduction steps

Future contribution guidelines may be published in:

```text
CONTRIBUTING.md
```

---

# Issues

When reporting issues, include:

* operating system
* Python version
* configuration summary
* reproduction steps
* relevant logs

---

# Suggested Makefile

```makefile
install:
	pip install -r requirements.txt

bootstrap:
	mtes bootstrap

generate:
	mtes generate --count 10

report:
	mtes report

generation-daemon:
	mtes generate --daemon

telegram-daemon:
	mtes telegram --daemon
```

---

# Citation

If you use MTES in research, please cite:

```bibtex
@software{mtes2026,
  title={Mutation-Traceable Evolutionary Synthesis},
  year={2026},
  url={https://github.com/example/mtes}
}
```

---

# License

Planned license:

```text
MIT License
```

---

# Final Note

MTES is an experimental research platform focused on genotype–phenotype locality in LLM-assisted evolutionary systems.

The repository currently represents a specification-driven design effort.

Implementation has not yet begun.

The long-term objective is to provide a reproducible environment for studying constrained evolutionary text generation, mutation-traceable phenotype synthesis, and measurable evolutionary dynamics.

This repository should currently be understood as an implementation-ready specification set rather than a functional software product.
