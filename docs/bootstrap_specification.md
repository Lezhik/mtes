# MTES Bootstrap & Calibration Specification v1.0

## Purpose

This specification defines the procedures required to establish a validated, reproducible, measurable, and recoverable starting state for MTES before evolutionary operation begins.

Bootstrap SHALL verify that:

* infrastructure is operational
* providers are reliable
* semantic resources are valid
* genotype–phenotype locality is measurable
* workflow execution is stable
* publication infrastructure is functional
* reproducible baseline metrics exist

Bootstrap SHALL NOT prioritize:

* novelty maximization
* engagement maximization
* fitness maximization
* evolutionary optimization
* creativity maximization

A system that cannot pass bootstrap validation SHALL NOT enter production evolutionary operation.

---

# 1. Scope

This specification covers:

* infrastructure validation
* provider validation
* dictionary construction
* embedding validation
* golden benchmark creation
* locality calibration
* calibration generation
* population initialization
* Telegram validation
* trial publications
* readiness evaluation
* bootstrap reporting
* recalibration procedures

---

# 2. Dependencies

This specification depends on:

* MTES GA Specification
* MTES Genotype–Phenotype Mapping Specification
* MTES LLM Interaction Specification
* MTES Data Model Specification
* MTES Architecture Specification

---

# 3. Bootstrap Principles

Bootstrap SHALL prioritize:

1. reproducibility
2. reliability
3. observability
4. measurability

Bootstrap results SHALL be repeatable under equivalent conditions.

---

# 4. Bootstrap Pipeline

```text
Infrastructure Validation
    ↓
Provider Validation
    ↓
Dictionary Construction
    ↓
Embedding Validation
    ↓
Golden Dataset Creation
    ↓
Golden Prompt Set Creation
    ↓
Locality Calibration
    ↓
Calibration Tweet Generation
    ↓
Initial Population Generation
    ↓
Telegram Validation
    ↓
Trial Publications
    ↓
Readiness Evaluation
    ↓
Bootstrap Report
    ↓
Production Start
```

A stage SHALL NOT begin until the previous stage completes successfully.

Pipeline execution is intentionally sequential.

This is a reproducibility requirement, not a technical limitation.

Independent stages MAY be parallelized in future implementations if equivalent results can be demonstrated.

---

# 5. Infrastructure Validation

## 5.1 Objective

Verify all required infrastructure components.

## 5.2 Required Components

* database
* cache
* provider connectivity
* Telegram connectivity
* monitoring
* persistence layer

## 5.3 Acceptance Criteria

Mandatory:

```text
availability = 100%
```

Failure:

```text
BOOTSTRAP_FAILED
```

---

# 6. Provider Validation

## 6.1 Objective

Validate candidate providers before calibration.

## 6.2 Validation Volume

```text
minimum_requests = 100
recommended_requests = 500
```

## 6.3 Measured Metrics

* provider_success_rate
* schema_compliance
* anchor_integrity
* repair_rate
* latency_mean

## 6.4 Acceptance Criteria

Mandatory:

```text
provider_success_rate ≥ 0.95
schema_compliance ≥ 0.98
anchor_integrity ≥ 0.85
repair_rate ≤ 0.10
```

Recommended:

```text
provider_success_rate ≥ 0.98
anchor_integrity ≥ 0.90
repair_rate ≤ 0.08
```

## 6.5 Preliminary Provider Score

Used before Locality Calibration.

```text
preliminary_provider_score =
    0.50 * reliability_score
  + 0.20 * anchor_score
  + 0.15 * repair_score
  + 0.15 * latency_score
```

Normalization:

```text
reliability_score = provider_success_rate

anchor_score = anchor_integrity

repair_score =
    max(0, 1 - repair_rate)

latency_score =
    1 - min(
        latency_mean /
        latency_reference,
        1
    )
```

Where:

```text
latency_reference
```

is defined in bootstrap configuration.

## 6.6 Final Provider Score

Computed after Locality Calibration.

```text
provider_score =
    0.40 * reliability_score
  + 0.25 * locality_score
  + 0.15 * anchor_score
  + 0.10 * repair_score
  + 0.10 * latency_score
```

Additional normalization:

```text
locality_score =
    locality_correlation
```

## 6.7 Provider Ranking Transition

Preliminary scores SHALL be used until Locality Calibration completes.

Final Provider Scores SHALL be computed immediately after successful completion of Locality Calibration.

After Final Provider Scores are available, preliminary scores SHALL NOT be used for provider selection.

## 6.8 Default Provider Selection

Default provider SHALL be:

```text
highest provider_score
```

Subject to:

```text
locality_correlation ≥ 0.45
schema_compliance ≥ 0.98
anchor_integrity ≥ 0.85
```

Providers failing mandatory thresholds SHALL NOT become default providers.

---

# 7. Dictionary Construction

## 7.1 Objective

Construct the initial semantic resource pool.

## 7.2 Allowed Sources

Allowed:

* manually curated vocabulary
* WordNet
* lexical datasets
* embedding-derived vocabulary

Forbidden:

* LLM-generated dictionary entries

## 7.3 Size

```text
Recommended source vocabulary:
10,000–50,000 terms

Minimum:
5,000 terms
```

Clarification:

The dictionary is a semantic resource pool.

This does not imply all terms become active evolutionary vocabulary.

The active vocabulary MAY be a smaller subset consistent with GA specifications.

## 7.4 Coverage Requirements

Coverage SHALL include:

* positive terms
* negative terms
* neutral terms
* concrete concepts
* abstract concepts
* high-frequency terms
* low-frequency terms

No coordinate region SHALL dominate vocabulary composition.

Extreme coordinate regions SHOULD contain at least:

```text
5% of vocabulary
```

whenever feasible.

---

# 8. Embedding Validation

## 8.1 Objective

Validate embedding infrastructure.

## 8.2 Retrieval Consistency Definition

```text
retrieval_consistency =
    mean_jaccard_overlap(
        top_20_neighbors
    )
```

measured across repeated retrieval runs.

## 8.3 Measured Metrics

* latency
* dimensional consistency
* retrieval consistency

## 8.4 Acceptance Criteria

Mandatory:

```text
retrieval_consistency ≥ 0.95
```

Repeated retrieval runs SHALL produce stable nearest-neighbor rankings.

---

# 9. Golden Dataset Creation

## 9.1 Objective

Provide a fixed benchmark dataset.

## 9.2 Size

```text
Minimum:
500 genomes

Recommended:
1000 genomes
```

Sampling:

```text
Latin Hypercube Sampling
```

## 9.3 Dataset Properties

The dataset SHALL remain immutable.

## 9.4 Versioning Rules

Changes require:

```text
bootstrap_dataset_version increment
```

Historical datasets SHALL remain archived.

## 9.5 Storage Format

```text
JSONL
UTF-8
NFKC normalization
```

---

# 10. Golden Prompt Set

## 10.1 Objective

Provide a fixed benchmark for regression testing.

## 10.2 Size

```text
Minimum:
100 prompts

Recommended:
250 prompts
```

## 10.3 Coverage

Categories:

* schema-sensitive
* anchor-sensitive
* ambiguity-sensitive
* repair-sensitive
* compression-sensitive
* locality-sensitive
* sentiment-sensitive
* fragmentation-sensitive
* edge-case prompts

Maximum:

```text
20% per category
```

Minimum:

```text
5% per category
```

whenever feasible.

## 10.4 Behavioral Compliance

Each case SHALL verify:

* schema compliance
* anchor preservation
* constraint compliance
* valid repair behavior

```text
behavioral_compliance_rate =
    compliant_cases /
    total_cases
```

Mandatory:

```text
behavioral_compliance_rate ≥ 0.95
```

Recommended:

```text
behavioral_compliance_rate ≥ 0.98
```

Failure:

```text
PROMPT_SET_FAILED
```

## 10.5 Storage Format

```text
JSONL
UTF-8
NFKC normalization
```

---

# 11. Locality Calibration

## 11.1 Objective

Validate genotype–phenotype locality.

## 11.2 Dataset

Golden Dataset.

## 11.3 Generation Policy

Exactly:

```text
1 phenotype per genome
```

Best-of-N selection is forbidden.

## 11.4 Correlation Calculation

For every genome pair:

```text
(genotype_distance,
 phenotype_distance)
```

Compute:

```text
Spearman rank correlation
```

For 1000 genomes:

```text
499,500 pairs
```

Subsampling is forbidden.

Pairwise distance computation SHALL use cached embeddings.

Repeated embedding computation during pairwise calculations is forbidden.

### Embedding Cache Policy

Embeddings SHALL be computed once per calibration run.

Embeddings MAY be reused across runs if:

* embedding model unchanged
* dictionary unchanged
* phenotype set unchanged

Caches SHALL be invalidated when:

* embedding model changes
* embedding model version changes
* dictionary version changes

Storage mechanism is implementation-defined.

## 11.5 Calibration Runs

```text
Minimum:
3 runs

Recommended:
5 runs
```

Accepted value:

```text
mean(locality_correlation)
```

## 11.6 Stability Requirement

```text
std(locality_correlation) ≤ 0.05
```

Otherwise:

```text
CALIBRATION_FAILED
```

## 11.7 Acceptance Criteria

Mandatory:

```text
locality_correlation ≥ 0.45
```

Recommended:

```text
locality_correlation ≥ 0.55
```

## 11.8 Borderline Zone

```text
0.45 ≤ locality < 0.50
```

Status:

```text
READY_WITH_WARNINGS
```

## 11.9 Operator Approval

Borderline systems SHALL require explicit operator approval.

Approval SHALL be recorded in Bootstrap Report.

Example:

```json
{
  "operator_approval": true,
  "operator_approval_timestamp": "2026-01-01T00:00:00Z",
  "operator_notes": "Approved for MVP launch."
}
```

---

# 12. Calibration Tweet Generation

## 12.1 Objective

Validate operational generation quality.

## 12.2 Relationship to Locality Calibration

Locality Calibration measures locality.

Calibration Tweet Generation measures:

* validation pass rate
* repair behavior
* latency
* operational quality

Phenotypes MAY be reused when implementation permits.

## 12.3 Volume

```text
Recommended:
1000 candidates
```

## 12.4 Acceptance Criteria

Mandatory:

```text
validation_pass_rate ≥ 0.95
anchor_integrity ≥ 0.85
repair_rate ≤ 0.10
```

---

# 13. Initial Population Generation

## 13.1 Objective

Generate the first evolutionary population.

## 13.2 Population Size

```text
Recommended:
500–5000

MVP:
1000
```

## 13.3 Requirements

```text
duplicate_ratio ≤ 1%
```

Each continuous gene SHALL satisfy:

```text
std ≥ 0.15
```

Rationale:

Uniform sampling on [0,1] produces expected standard deviation near:

```text
0.29
```

The threshold is intentionally conservative.

Coordinate Coverage:

For each coordinate axis:

all coordinate values SHOULD be represented whenever feasible.

---

# 14. Telegram Validation

## 14.1 Objective

Validate Telegram integration.

## 14.2 Outbound Validation

* delivery
* formatting
* links

## 14.3 Inbound Validation

* publication status
* views
* reactions
* forwards

## 14.4 Operator Commands

All operator commands SHALL be authenticated.

Validation:

* emergency stop
* status requests
* command execution

---

# 15. Trial Publications

## 15.1 Objective

Validate production behavior.

## 15.2 Volume

```text
50–200 publications
```

## 15.3 Observation Window

```text
Minimum:
7 days
```

Publications SHOULD be distributed across the observation window.

Bulk publication at a single timestamp is discouraged.

## 15.4 Metrics

* publication_success_rate
* engagement_collection_success_rate
* workflow_failure_rate
* provider_failure_rate
* operator_command_success_rate

Engagement collection success rate measures collection reliability.

It does NOT measure engagement quality.

Formula:

```text
successful_collection_events /
total_collection_events
```

## 15.5 Acceptance Criteria

Mandatory:

```text
publication_success_rate ≥ 0.99

engagement_collection_success_rate ≥ 0.95

operator_command_success_rate ≥ 0.99

workflow_failure_rate ≤ 0.05
```

---

# 16. Readiness Evaluation

## 16.1 Mandatory Conditions

All bootstrap stages passed.

## 16.2 Calibration Conditions

Mandatory:

```text
provider_success_rate ≥ 0.95
schema_compliance ≥ 0.98
anchor_integrity ≥ 0.85
repair_rate ≤ 0.10
locality_correlation ≥ 0.45
```

## 16.3 Status

```text
READY
READY_WITH_WARNINGS
NOT_READY
```

Warnings SHALL NOT violate mandatory thresholds.

---

# 17. Bootstrap Report

## 17.1 Objective

Produce a permanent bootstrap record.

## 17.2 Storage Requirements

Bootstrap Reports SHALL be stored in:

```text
bootstrap_reports
```

collection.

The Data Model Specification SHALL define this collection.

Until updated, this document serves as the authoritative schema definition.

## 17.3 Example Schema

```json
{
  "bootstrap_version": "2.4",
  "dataset_version": "1.0",
  "prompt_set_version": "1.0",
  "readiness_status": "READY_WITH_WARNINGS",
  "operator_approval": true,
  "operator_approval_timestamp": "2026-01-01T00:00:00Z",
  "operator_notes": "Approved for launch",
  "reproducibility_record": {
    "bootstrap_version": "2.4",
    "dataset_version": "1.0",
    "prompt_set_version": "1.0",
    "dictionary_version": "1.0",
    "provider": "provider-x",
    "model": "model-y",
    "embedding_model": "embedding-z",
    "seed_policy": "hash(genome_id + generation_id)",
    "timestamp": "2026-01-01T00:00:00Z"
  }
}
```

The reproducibility_record SHALL conform to Section 20.

---

# 18. Recalibration

## 18.1 Trigger Conditions

* provider change
* model change
* embedding change
* dictionary change
* prompt change
* architecture change

## 18.2 Recalibration Matrix

| Change                    | Required Recalculation                                                        |
| ------------------------- | ----------------------------------------------------------------------------- |
| LLM model                 | Provider Validation + Locality Calibration                                    |
| Embedding model           | Embedding Validation + Locality Calibration                                   |
| Dictionary version        | Dictionary Construction Review + Locality Calibration + Population Generation |
| Prompt contract           | Provider Validation + Golden Prompt Set                                       |
| Major architecture change | Full Bootstrap                                                                |

Dictionary Construction Review refers to validation of an existing dictionary version, not reconstruction from scratch.

---

# 19. Production Start

Production MAY begin only if:

```text
Readiness Status = READY
```

Systems in:

```text
READY_WITH_WARNINGS
```

require explicit operator approval.

Systems in:

```text
NOT_READY
```

SHALL NOT enter production evolutionary operation.

---

# 20. Bootstrap Reproducibility Record

Required fields:

```json
{
  "bootstrap_version": "",
  "dataset_version": "",
  "prompt_set_version": "",
  "dictionary_version": "",
  "provider": "",
  "model": "",
  "embedding_model": "",
  "seed_policy": "",
  "timestamp": ""
}
```

This record SHALL be archived together with Bootstrap Reports.

---

# 21. Final Note

The purpose of bootstrap is not to maximize engagement, creativity, novelty, or fitness.

The purpose of bootstrap is to establish a validated, reproducible, measurable, and recoverable starting state.

A system that cannot pass bootstrap validation SHALL NOT enter production evolutionary operation.
