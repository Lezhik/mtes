# MTES Data Model Specification v1.0

## 1. Purpose

This specification defines the MongoDB storage model for MTES.

This specification defines:

* collections
* document schemas
* indexes
* retention policies
* storage constraints
* versioning requirements

This specification does not define:

* genetic algorithms
* mapping logic
* fitness formulas
* locality calculations
* LLM behavior
* evolutionary policies
* archive eviction policies
* publication policies

Behavioral rules are defined in:

* MTES Genetic Specification
* MTES Mapping Specification
* MTES LLM Interaction Specification

---

# 2. Global Rules

## 2.1 Common Fields

All core collections SHALL contain:

```json
{
  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 2.2 Immutable Collections

The following collections SHALL be append-only:

* genomes
* mutation_history
* candidate_archive
* validation_records
* fitness_records
* tweet_archive
* audit_log

Corrections SHALL create new documents.

---

## 2.3 Vector Search Configuration

MongoDB Atlas Vector Search SHALL be used.

All vector indexes SHALL use:

```text
index_type = HNSW
metric = cosine
dimension = embedding_models.dimension
```

Embedding model metadata MUST exist before vector index creation.

Index creation scripts SHALL obtain dimensions from:

```text
embedding_models.dimension
```

Hardcoded dimensions are prohibited.

---

# 3. Dictionary Layer

## 3.1 dictionary_terms

Purpose:

Dictionary token storage.

Example:

```json
{
  "_id": "term_001",

  "token": "winter",

  "coordinate": [3,5,4,2,3],

  "bucket_id": "bucket_014",

  "embedding": [],

  "embedding_model_id": "e5-large",

  "dictionary_version": "4.2",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
token UNIQUE
coordinate
bucket_id
dictionary_version
vector(embedding)
```

---

## 3.2 dictionary_buckets

Purpose:

Dictionary coordinate occupancy tracking.

Example:

```json
{
  "_id": "bucket_014",

  "coordinate": [3,5,4,2,3],

  "term_count": 12,

  "dictionary_version": "4.2",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
coordinate UNIQUE
dictionary_version
```

---

# 4. Mapping Layer

## 4.1 pair_memory_state

Purpose:

Genome pair state storage.

Behavior, decay rules, and penalty calculations are defined by the Genetic Specification.

Canonical ordering requirement:

```text
genome_id_a < genome_id_b
```

Example:

```json
{
  "_id": "pair_001",

  "genome_id_a": "genome_001",
  "genome_id_b": "genome_002",

  "use_count": 3,

  "last_used_generation": 421,

  "current_penalty": 0.34,

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
(genome_id_a, genome_id_b) UNIQUE
last_used_generation
experiment_id
run_id
```

---

## 4.2 constraint_records

Purpose:

Constraint expansion storage.

Example:

```json
{
  "_id": "constraint_001",

  "genome_id": "genome_001",

  "constraint_set": {
    "generation_constraints": [
      {
        "type": "required",
        "dimension": "anchor",
        "value": "winter"
      }
    ]
  },

  "mapping_version": "4.9",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
genome_id
mapping_version
```

---

# 5. Evolution Layer

## 5.1 genomes

Purpose:

Source-of-truth genome storage.

Anchor policy:

```text
anchor stores the token resolved from coordinate
using dictionary_version at genome creation time.

anchor is not updated when dictionary_version changes.
```

Example:

```json
{
  "_id": "genome_001",

  "generation": 84,

  "semantic_genes": [
    {
      "gene_id": 1,
      "coordinate": [3,5,4,2,3],
      "anchor": "winter"
    }
  ],

  "numeric_genes": {
    "anchor_rigidity": 0.81
  },

  "parent_ids": [
    "genome_010",
    "genome_011"
  ],

  "seed": 123456789,

  "dictionary_version": "4.2",
  "mapping_version": "4.9",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
generation
parent_ids
experiment_id
run_id
```

---

## 5.2 mutation_history

Purpose:

Genome lineage tracking.

Example:

```json
{
  "_id": "mutation_001",

  "genome_id": "genome_001",

  "parent_ids": [
    "genome_010",
    "genome_011"
  ],

  "crossover_type": "uniform",

  "mutation_log": [
    {
      "mutation_type": "semantic",
      "gene_id": 1,
      "axis": 2,
      "old_value": 4,
      "new_value": 5
    }
  ],

  "timestamp": "2026-01-01T00:00:00Z",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
genome_id
timestamp
```

---

# 6. LLM Layer

## 6.1 phenotype_candidates

Purpose:

P4 generation output.

Example:

```json
{
  "_id": "candidate_raw_001",

  "genome_id": "genome_001",

  "text": "winter silence drifts slowly",

  "provider": "OpenAI",

  "model": "GPT",

  "routing_family": "P4-C",

  "prompt_version": "3.1",

  "validation_status": "pending",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
genome_id
validation_status
```

---

## 6.2 candidate_archive

Purpose:

P5 ranked candidate archive.

Example:

```json
{
  "_id": "candidate_001",

  "genome_id": "genome_001",

  "text": "winter silence drifts slowly",

  "constraint_score": 0.82,
  "quality_score": 0.75,
  "diversity_score": 0.61,
  "overall_score": 0.74,

  "selected": true,

  "routing_family": "P4-C",
  "prompt_version": "3.1",

  "embedding": [],
  "embedding_model_id": "e5-large",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
genome_id
selected
overall_score
routing_family
prompt_version
vector(embedding)
```

---

# 7. Evaluation Layer

## 7.1 validation_records

Purpose:

Validation results.

Example:

```json
{
  "_id": "validation_001",

  "candidate_id": "candidate_001",

  "schema_pass": true,
  "constraint_pass": true,
  "semantic_pass": false,
  "integration_pass": true,

  "failed_checks": [
    "anchor_preservation"
  ],

  "repair_attempts": 1,

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
candidate_id
semantic_pass
```

---

## 7.2 fitness_records

Purpose:

Fitness evaluation storage.

Population-level locality metrics are defined by the Mapping Specification.

This collection stores candidate-level measurements only.

Example:

```json
{
  "_id": "fitness_001",

  "candidate_id": "candidate_001",

  "genome_id": "genome_001",

  "fitness": 0.82,

  "novelty": 0.44,

  "nearest_archive_distance": 0.31,

  "genotype_distance_to_parent": 0.12,

  "phenotype_distance_to_parent": 0.15,

  "neighborhood_entropy": 0.42,

  "distance_metric": "cosine",

  "fitness_formula_version": "4.9",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
candidate_id
genome_id
fitness
novelty
```

---

# 8. Output Layer

## 8.1 tweet_archive

Purpose:

Published phenotype archive.

Example:

```json
{
  "_id": "tweet_001",

  "genome_id": "genome_001",

  "text": "winter silence drifts slowly",

  "fitness": 0.82,

  "coordinate_snapshot": [
    [3,5,4,2,3]
  ],

  "generation_snapshot": {
    "semantic_genes": [],
    "numeric_genes": {},

    "routing_family": "P4-C",

    "prompt_version": "3.1",

    "dictionary_version": "4.2",

    "mapping_version": "4.9",

    "decoding_profile": {
      "temperature": 0.60,
      "top_p": 0.95
    },

    "provider": "OpenAI",

    "model": "GPT",

    "seed": 123456789
  },

  "embedding": [],
  "embedding_model_id": "e5-large",

  "evicted": false,

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Notes:

```text
coordinate_snapshot contains coordinates only.

generation_snapshot.semantic_genes contains
full reconstruction data.
```

Indexes:

```text
genome_id
fitness
evicted
vector(embedding)
```

---

# 9. Infrastructure Layer

## 9.1 embedding_models

Purpose:

Embedding model metadata.

Example:

```json
{
  "_id": "e5-large",

  "version": "1.0",

  "dimension": 1024,

  "distance_metric": "cosine"
}
```

Indexes:

```text
_id UNIQUE
```

---

## 9.2 audit_log

Purpose:

Data and LLM interaction events.

Allowed event types:

```text
LLM_REQUEST
LLM_RESPONSE
MODEL_SELECTION
PROMPT_EXECUTION
VALIDATION_REPAIR
ARCHIVE_INSERTION
ARCHIVE_EVICTION
MIGRATION_EXECUTION
VECTOR_INDEX_REBUILD
```

Example:

```json
{
  "_id": "audit_001",

  "event_type": "LLM_REQUEST",

  "details": {},

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
event_type
created_at
```

---

## 9.3 system_events

Purpose:

Infrastructure and service lifecycle events.

Allowed severities:

```text
INFO
WARNING
ERROR
CRITICAL
```

Allowed event types:

```text
SERVICE_START
SERVICE_STOP
PROVIDER_FAILOVER
INDEX_REBUILD
MIGRATION_START
MIGRATION_COMPLETE
CONFIG_UPDATE
RESOURCE_WARNING
RESOURCE_FAILURE
```

Example:

```json
{
  "_id": "event_001",

  "event_type": "PROVIDER_FAILOVER",

  "severity": "WARNING",

  "message": "switched to secondary provider",

  "schema_version": "3.4",
  "experiment_id": "exp_001",
  "run_id": "run_001",
  "created_at": "2026-01-01T00:00:00Z"
}
```

Indexes:

```text
event_type
severity
created_at
```

---

# 10. Retention Policy

Core collections:

```text
No TTL
```

Temporary collections:

```text
constraint_records
phenotype_candidates
```

Minimum retention:

```text
90 days
```

Retention decisions SHALL follow behavioral specifications.

---

# 11. Pipeline Usage Matrix

| Collection           | Stage          |
| -------------------- | -------------- |
| dictionary_terms     | Dictionary     |
| dictionary_buckets   | Dictionary     |
| pair_memory_state    | Evolution      |
| constraint_records   | Mapping        |
| genomes              | Evolution      |
| mutation_history     | Evolution      |
| phenotype_candidates | P4             |
| candidate_archive    | P5             |
| validation_records   | Validation     |
| fitness_records      | Evaluation     |
| tweet_archive        | Output         |
| embedding_models     | Infrastructure |
| audit_log            | Infrastructure |
| system_events        | Infrastructure |

---

# 12. Operational Collections

The following collections support runtime orchestration and are defined in `docs/detailed_design.md` §2.3.3 until fully merged into this document.

| Collection | Purpose | Append-only |
| ---------- | ------- | ----------- |
| `bootstrap_reports` | Bootstrap readiness and reproducibility record | yes |
| `workflow_state` | Workflow FSM persistence | no |
| `evolution_state` | Evolution lifecycle state | no |
| `population_members` | Active population membership | no |
| `publication_queue` | Scheduled and pending publications | no |
| `daemon_state` | Daemon schedules and queue depths | no |

### bootstrap_reports (authoritative until schema merge)

Required fields:

```text
bootstrap_version
dataset_version
prompt_set_version
readiness_status   # READY | READY_WITH_WARNINGS | NOT_READY
reproducibility_record
```

Optional fields:

```text
operator_approval
operator_approval_timestamp
operator_notes
```

---

# 13. Acceptance Criteria

The storage model SHALL support:

```text
100% genome reconstruction
100% phenotype reconstruction
100% lineage reconstruction
100% version traceability
100% archive traceability
100% snapshot reproducibility
```
