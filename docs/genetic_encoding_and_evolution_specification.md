# MTES Genetic Encoding & Evolution Specification v1.0

## Status

Final MVP Baseline

Version: 1.0

Scope:

* Genetic Representation
* Mutation
* Selection
* Crossover
* Diversity Management

Out of Scope:

* Phenotype Mapping
* Translation Layer Logic
* LLM Compilation

---

# 1. Purpose

This specification defines the genetic representation and evolutionary operators used by MTES.

The primary objective is not biological realism.

The objective is to maximize:

* genotype–phenotype locality
* reproducibility
* controllability
* interpretability

The representation is designed to increase the probability that small genotype changes produce small phenotype changes.

No claim is made that the coordinate system fully models natural language semantics.

---

# 2. Design Principles

## 2.1 Locality First

Small mutations should usually produce small semantic shifts.

Locality is treated as a measurable engineering property.

---

## 2.2 Uniform Nominal Mutation Step

All semantic coordinate mutations use identical genotype-space step size.

Phenotype impact is not assumed to be uniform.

Different coordinates may produce different behavioral effects due to:

* bucket density
* bucket purity
* mapping interactions
* phenotype compilation

The system guarantees uniform nominal mutation magnitude, not uniform phenotype impact.

---

## 2.3 Flat Coordinate Space

The system intentionally avoids hierarchical representations.

Hierarchical structures create depth-dependent mutation impact.

All semantic coordinates exist in a single uniform space.

---

## 2.4 Coordinates Are Search Controls

The coordinate system is:

* a search representation
* a locality mechanism
* an interpretability mechanism

It is not:

* a complete semantic theory
* a discourse model
* a stance model

Properties such as irony, humor, sarcasm, framing, imagery and narrative structure remain outside coordinate representation.

---

# 3. Genome Structure

## 3.1 Gene Categories

### Semantic Genes

Represent symbolic content.

Encoding:

```text
5 axes
8 values per axis
coordinate = (a,b,c,d,e)
```

Range:

```text
axis value ∈ {0..7}
```

---

### Numeric Genes

Directly mapped to MTES Mapping Specification operational genes.

Exactly six numeric genes exist:

* fragmentation_bias
* ambiguity_bias
* sentiment_contrast
* semantic_jump_radius
* compression_target
* anchor_rigidity

Encoding:

```text
1 byte per gene
range 0..255
```

---

### Structural Genes

Disabled for MVP.

Structural genes may be introduced only if:

1. Mapping Specification defines corresponding phenotype contracts
2. locality targets remain satisfied for at least 100 generations
3. Mapping Spec and GA Spec are revised together

Candidate future genes:

```text
question_probability
emphasis_probability
contrast_probability
```

---

### Control Genes

Post-MVP only.

Examples:

```text
mutation_rate_modifier
exploration_bias
```

Activation criterion:

```text
locality target achieved
AND
diversity collapse persists >50 generations
```

---

## 3.2 Genome Layout

Example:

```text
9 semantic genes
6 numeric genes
```

Total:

```text
15 genes
```

---

# 4. Semantic Coordinate System

## 4.1 Axes

Five heuristic axes are used:

| Axis                | Meaning                  |
| ------------------- | ------------------------ |
| Valence             | negative ↔ positive      |
| Abstraction         | concrete ↔ abstract      |
| Agency              | passive ↔ active         |
| Social Scope        | individual ↔ collective  |
| Communicative Force | descriptive ↔ persuasive |

These axes are engineered search projections.

They are not assumed to be independent latent semantic variables.

---

## 4.2 Axis Correlation Monitoring

Dictionary validation computes Pearson correlation between all axis score pairs.

Target:

```text
|r| < 0.50
```

Violation generates warning status.

---

# 5. Dictionary Construction

## 5.1 MVP Vocabulary

```text
2000–3000 tokens
```

---

## 5.2 Assignment Pipeline

### Step 1 — Embedding Extraction

Fixed embedding model.

Versioned.

---

### Step 2 — Axis Scoring

MVP reference model:

```text
Ridge Regression
(alpha=1.0)
```

Alternative models require version change.

Output:

```text
score ∈ [0,1]
```

Model versions must be archived.

---

### Step 3 — Coordinate Quantization

```text
bucket = floor(score * 8)
```

clamped to:

```text
[0,7]
```

---

### Step 4 — Bucket Balancing

Target occupancy:

```text
5–20 tokens
```

Priority order:

```text
Oversized handling
before
Sparse handling
```

Reason:

Oversized buckets create locality distortion faster than sparse buckets.

#### Oversized Bucket

1. sort by centroid distance
2. retain closest 20
3. move overflow to nearest coordinate bucket by embedding distance

#### Sparse Bucket

1. locate nearest coordinate bucket
2. merge
3. recompute centroid
4. preserve history

All moves logged.

---

### Step 5 — Human Review

Review sample:

```text
5% random sample
minimum 100 tokens
```

Purpose:

```text
assignment sanity validation
```

---

## 5.3 Bucket Purity

Metric:

```text
mean pairwise cosine similarity
```

Target:

```text
>= 0.70
```

Purity is a clustering sanity metric only.

---

# 6. Numeric Encoding

## 6.1 Purpose

Avoid catastrophic bit-flip behavior.

Neighboring byte values should produce small parameter changes.

---

## 6.2 Canonical LUT Formula

```text
u = byte / 255

value =
0.5 + 0.5*tanh(1.25*(u - 0.5))
```

Canonical implementation only.

Steepness 1.25 chosen to:

* preserve center sensitivity
* avoid edge saturation
* maintain monotonicity

---

## 6.3 LUT Requirements

Must be:

```text
strictly monotonic
deterministic
versioned
```

---

## 6.4 Precision Rules

Storage:

```text
uint8
```

Runtime:

```text
float64
```

Serialization:

```text
6 decimal places
```

---

## 6.5 Round-Trip Rule

```text
byte -> value -> byte
```

Requirement:

```text
error <= 1 byte
```

---

## 6.6 LUT Verification Checkpoints

Reference points:

| Byte | Value |
| ---- | ----- |
| 0    | 0.223 |
| 32   | 0.283 |
| 64   | 0.351 |
| 96   | 0.425 |
| 128  | 0.501 |
| 160  | 0.577 |
| 192  | 0.649 |
| 208  | 0.682 |
| 224  | 0.717 |
| 255  | 0.777 |

Requirement:

```text
absolute error <= 0.001
```

---

# 7. Distance Functions

## 7.1 Semantic Distance

```text
d_semantic =
Σ|Ai-Bi|
/
35
```

Range:

```text
[0,1]
```

---

## 7.2 Numeric Distance

Mean absolute difference across six numeric genes.

---

## 7.3 Genome Distance

```text
0.70*d_semantic
+
0.30*d_numeric
```

Initial calibration.

---

# 8. Mutation

## 8.1 Semantic Mutation

Random:

```text
gene
axis
```

Apply:

```text
±1 shift
```

---

## 8.2 Boundary Handling

Reflection.

Examples:

```text
0 -> -1 => 1
7 -> 8 => 6
```

---

## 8.3 Low-Purity Destination

If purity < 0.70:

1. nearest valid bucket
2. nearest valid coordinate
3. reject mutation

Tie-break:

```text
lowest coordinate id
```

---

# 9. Parent Selection

## 9.1 Pool Allocation

```text
70% exploitation
20% novelty
10% exploration
```

---

## 9.2 Parent Score

```text
0.50 fitness_rank
+
0.25 compatibility
+
0.15 novelty
+
0.10 diversity_bonus
```

---

## 9.3 Pair Memory

Exponential decay.

Half-life:

```text
20 generations
```

---

## 9.4 Inter-Pool Crossover

Probability:

```text
20%
```

Applied before compatibility ranking.

Known limitation:

Cross-pool pairs naturally receive lower fitness_proximity scores.

Behavior is accepted to preserve exploration.

---

# 10. Compatibility

## 10.1 Compatibility Score

```text
0.40 semantic_similarity
+
0.20 structural_similarity
+
0.20 fitness_proximity
+
0.20 archive_diversity
```

---

## 10.2 Archive Diversity

k-NN:

```text
k = 20
```

Mean distance to nearest archive entries.

---

## 10.3 Dynamic Baseline Calibration

Bootstrap:

```text
expected_random_distance = 0.38
```

Warm-up:

```text
50 generations
```

After warm-up:

```text
EMA_t =
0.90 * EMA_(t-1)
+
0.10 * observed_distance
```

Effective window:

```text
~10 generations
```

Override trigger:

```text
>20% deviation
for 10 consecutive generations
```

---

# 11. Crossover

## 11.1 Adaptive Blend Crossover

Per semantic gene:

```text
40% parent A
40% parent B
20% adaptive blend
```

---

## 11.2 Blend Modes

Uniform selection among:

* Interval Sampling
* Weighted Midpoint
* Axis Mutation Injection

---

## 11.3 Parent Canonicalization

Before blending:

```text
Parent A = lower genome id
Parent B = higher genome id
```

---

## 11.4 Locality Repair

Trigger:

```text
distance > 0.35
```

Maximum:

```text
3 iterations
```

Repair only modifies semantic genes.

---

## 11.5 Repair Bypass

Probability:

```text
5%
```

Bypass offspring remain subject to:

* validation
* archive monitoring
* selection pressure

Bypass offspring are generated within existing crossover quota.

Population size remains unchanged.

---

## 11.6 Bypass Logging

Record:

* parent ids
* pre-repair distance
* validation result
* archive admission
* next-generation parent selection outcome

Definition:

```text
bypass_survival_rate =
selected_as_parent_next_generation
/
total_bypass_offspring
```

Target:

```text
<15%
```

---

# 12. Diversity Management

## 12.1 Collapse Detection

```text
mean_genome_distance < 0.15
```

Initial calibration value.

---

## 12.2 Sparse Region Detection

Window:

```text
20 generations
```

Condition:

```text
occupancy < 3
```

---

## 12.3 Sparse Chain Fallback

1. nearest dense bucket
2. quarantine bucket
3. reclustering review

---

## 12.4 Failure Modes

| ID   | Severity | Condition              | Action            |
| ---- | -------- | ---------------------- | ----------------- |
| FM-1 | Critical | correlation < 0.40     | recalibrate axes  |
| FM-2 | Warning  | purity < 0.70          | recluster         |
| FM-3 | Warning  | sparse region growth   | rebalance         |
| FM-4 | Critical | diversity collapse     | inject novelty    |
| FM-5 | Warning  | archive drift          | archive review    |
| FM-6 | Warning  | occupancy imbalance    | rebalance buckets |
| FM-7 | Critical | repair activation >50% | diagnostics       |

FM-7 diagnostic sequence:

1. bucket purity
2. compatibility distribution
3. blend frequency
4. repair threshold

Timeout:

```text
10 generations
```

Fallback:

```text
reduce blend frequency by 50%
or
reduce repair threshold by 10%
```

---

# 13. Full Evolution Cycle Example

(omitted here for brevity in normative text; maintained in implementation appendix)

---

# 14. Assumptions

A1:

Coordinate distance correlates with embedding distance.

Minimum target:

```text
r >= 0.40
```

Desired target:

```text
r >= 0.55
```

This metric evaluates encoding geometry, not phenotype quality.

---

A2:

Bucket purity improves locality.

Not proof of semantic equivalence.

---

A3:

Five axes improve locality versus random token mutation.

---

A4:

Conservative crossover may reduce exploration.

Accepted MVP trade-off.

---

# 15. Escalation Policy

Persistent critical failure:

```text
>20 generations
```

Triggers mandatory review.

---

# 16. Mapping Integration Contract

## 16.1 Single Source of Truth

MTES Mapping Specification.

---

## 16.2 Numeric Gene Mapping

| GA Gene              | Mapping Gene         |
| -------------------- | -------------------- |
| fragmentation_bias   | fragmentation_bias   |
| ambiguity_bias       | ambiguity_bias       |
| sentiment_contrast   | sentiment_contrast   |
| semantic_jump_radius | semantic_jump_radius |
| compression_target   | compression_target   |
| anchor_rigidity      | anchor_rigidity      |

---

## 16.3 Fitness–Selection Interface

Input:

```text
fitness_score
```

Output:

```text
fitness_rank
```

Tie-break:

1. novelty
2. diversity bonus
3. lower genome id

Contract:

GA consumes fitness_score only.

No raw phenotype metrics cross the boundary.

---

# 17. Acceptance Criteria

| Metric                                   | Target   |
| ---------------------------------------- | -------- |
| coordinate_embedding_correlation         | ≥ 0.40   |
| desired_coordinate_embedding_correlation | ≥ 0.55   |
| bucket_purity                            | ≥ 0.70   |
| empty_coordinate_rate                    | ≤ 10%    |
| mutation_reproducibility                 | 100%     |
| LUT_monotonicity                         | 100%     |
| round_trip_error                         | ≤ 1 byte |
| bypass_survival_rate                     | < 15%    |
| repair_activation_rate                   | < 50%    |

---

# 18. Final Notes

This specification defines a controllable evolutionary representation.

Its primary goals are:

* measurable locality
* deterministic mutation
* reproducible crossover
* stable integration with Mapping Specification

Semantic completeness is intentionally secondary to evolutionary controllability within the MVP.
