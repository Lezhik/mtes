# MTES Genotype–Phenotype Mapping Specification v1.0

## 1. Purpose

MTES defines a deterministic genotype–phenotype mapping pipeline for short-form text evolution.

The system goal is not generic text generation. The primary research question is:

> Can a constrained LLM compilation pipeline preserve measurable genotype–phenotype locality under evolutionary mutation?

Success criteria are defined through:

- genome_delta ↔ phenotype_delta correlation
- anchor preservation
- constrained stylistic controllability
- bounded repair dependency

Genetic Algorithm logic is defined in a separate specification.

---

# 2. Core Principles

## 2.1 Deterministic Upstream Pipeline

All stages before compilation must be deterministic:

- semantic expansion
- anchor selection
- relation graph construction
- translation layer
- structural plan generation
- validation
- fitness evaluation

The LLM is used only for constrained surface realization.

---

## 2.2 LLM Role

The LLM acts as:

- constrained compiler
- stylistic renderer
- surface-level realization layer

The LLM is NOT:

- semantic planner
- graph constructor
- novelty engine
- evolutionary controller

---

## 2.3 Proxy Metric Policy

Some metrics are explicitly heuristic proxies.

Proxy metrics:

- semantic_entropy
- human_style_score
- neighborhood_entropy
- sentiment_contrast_score

Combined total fitness weight of all proxy metrics MUST remain <= 0.30.

---

# 3. Genome

## 3.1 Operational Genes

| Gene | Range | Purpose |
|---|---|---|
| fragmentation_bias | [0.0, 1.0] | Fragmented vs continuous phrasing |
| ambiguity_bias | [0.0, 1.0] | Indirection and semantic looseness |
| sentiment_contrast | [0.0, 1.0] | Emotional polarity shift |
| semantic_jump_radius | [0.0, 1.0] | Semantic exploration radius |
| compression_target | [0.0, 1.0] | Information density target |
| anchor_rigidity | [0.0, 1.0] | Strictness of anchor preservation |

---

## 3.2 MVP Default Values

| Gene | Default |
|---|---|
| fragmentation_bias | 0.50 |
| ambiguity_bias | 0.45 |
| sentiment_contrast | 0.40 |
| semantic_jump_radius | 0.35 |
| compression_target | 0.55 |
| anchor_rigidity | 0.70 |

All calibration sweeps freeze non-tested genes to MVP defaults.

---

# 4. Translation Layer

## 4.1 Deterministic Translation

Genes are converted into deterministic constraints.

No stochastic sampling is allowed.

---

## 4.2 Translation Mapping

| Gene | Constraint |
|---|---|
| fragmentation_bias | punctuation_density, short_clause_ratio |
| ambiguity_bias | semantic_entropy_target, indirect_reference_ratio |
| sentiment_contrast | required_sentiment_shift |
| semantic_jump_radius | semantic_expansion_radius |
| compression_target | target_information_density, target_token_limit |
| anchor_rigidity | anchor_similarity_threshold |

---

## 4.3 Compression Mapping

```text
compression_target <= 0.30 → token_limit = 48
compression_target <= 0.60 → token_limit = 36
compression_target > 0.60  → token_limit = 24
```

---

# 5. Semantic Expansion

## 5.1 Expansion

Expansion uses:

- sentence-transformers/all-mpnet-base-v2
- deterministic nearest-neighbor retrieval
- cosine similarity filtering

---

## 5.2 Expansion Radius

```text
candidate_kept if cosine_distance <= semantic_expansion_radius
```

semantic_jump_radius controls only semantic expansion.

It does NOT:

- modify relation density
- modify graph topology
- modify repair thresholds

---

# 6. Anchor Selection

## 6.1 Anchor Priority

Priority order:

1. explicit semantic anchors
2. TF-IDF centrality
3. embedding centrality
4. deterministic lexical fallback

---

## 6.2 Deterministic Tie Break

Tie order:

1. higher TF-IDF
2. higher embedding centrality
3. earlier token position
4. lexicographic order

---

## 6.3 Anchor Preservation Policy

Validation order:

1. exact token match
2. spaCy lemma match (`en_core_web_sm`)
3. cosine similarity >= threshold

Irregular verbs:

```text
run ↔ ran
write ↔ wrote
```

are accepted through lemma validation.

---

# 7. Relation Graph

## 7.1 Edge Score

```text
edge_score =
    0.50 * cosine_similarity +
    0.30 * polarity_alignment +
    0.20 * rarity_score
```

---

## 7.2 Rarity Corpus

Rarity statistics are computed from:

- 5M English tweets
- date range: 2023-01-01 → 2023-06-30
- source: public academic Twitter snapshot
- preprocessing:
  - lowercase
  - URLs removed
  - emoji preserved
  - hashtags preserved

Corpus release hash:

```text
mtes-twitter-corpus-v1-sha256:8d13c9e4a1
```

---

## 7.3 Relation Type Assignment

| Condition | Relation Type |
|---|---|
| cosine >= 0.80 AND polarity_alignment >= 0.70 | reinforcement |
| cosine >= 0.60 AND polarity_alignment < 0.40 | contrast |
| cosine < 0.45 AND rarity_score >= 0.60 | tension |
| otherwise | associative |

---

# 8. Deterministic Structural Plan

## 8.1 Algorithm

```python
anchors = select_core_anchors()
relation = dominant_relation_type(relation_graph)

if tie:
    relation = priority_order(
        reinforcement,
        contrast,
        tension,
        associative
    )

rhetorical_mode = lookup_rhetorical_mode(
    relation,
    short_clause_ratio
)

sentiment_pattern = lookup_sentiment_pattern(
    required_sentiment_shift
)

plan = {
    "anchors": anchors,
    "relation_focus": relation,
    "rhetorical_mode": rhetorical_mode,
    "sentiment_pattern": sentiment_pattern
}
```

---

## 8.2 Rhetorical Lookup Table

| Relation + Clause Style | Rhetorical Mode |
|---|---|
| tension + short | fragmented |
| tension + long | declarative |
| contrast + any | juxtaposed |
| reinforcement + short | emphatic |
| reinforcement + long | reflective |
| associative + any | observational |

---

## 8.3 Sentiment Pattern Lookup

| Shift | Pattern |
|---|---|
| < 0.20 | flat |
| 0.20–0.50 | negative_to_neutral |
| > 0.50 | negative_to_positive |

---

# 9. Compilation

## 9.1 Model

Recommended MVP compiler:

- mistralai/Mistral-7B-Instruct-v0.2
- structured JSON output
- temperature = 0.55
- top_p = 0.90

---

## 9.2 Compilation Contract

Compiler input:

```json
{
  "anchors": ["city", "night"],
  "relation_focus": "contrast",
  "rhetorical_mode": "fragmented",
  "sentiment_pattern": "negative_to_positive",
  "constraints": {
    "token_limit": 36,
    "punctuation_density": 0.12
  }
}
```

Required output:

```json
{
  "candidate_text": "..."
}
```

---

## 9.3 Few-Shot Examples

### Example A — Fragmented

Input:

```json
{
  "relation_focus": "tension",
  "rhetorical_mode": "fragmented"
}
```

Output:

```text
Too bright. Too loud. Still couldn't leave.
```

---

### Example B — Contrastive

Input:

```json
{
  "relation_focus": "contrast",
  "rhetorical_mode": "juxtaposed"
}
```

Output:

```text
The city looked alive, everyone inside it looked exhausted.
```

---

### Example C — Question-Based

Input:

```json
{
  "relation_focus": "associative",
  "rhetorical_mode": "observational"
}
```

Output:

```text
Why do empty stations feel louder after midnight?
```

---

# 10. Repair Layer

## 10.1 Hard Constraints

Reject if:

```text
anchor_integrity < 0.70
repair_operations > 3
repair_token_delta > 0.15
```

---

## 10.2 Repair Leakage Detection

Evaluation window:

```text
1 evaluation window = 10 generations
```

Leakage trigger:

```text
mean_repair_penalty > 0.08
for 3 consecutive windows
```

---

## 10.3 Diagnostic-First Recovery

| Detected Cause | Action |
|---|---|
| excessive semantic drift | reduce semantic_expansion_radius by 0.05 |
| compilation instability | reduce temperature by 0.05 |
| validation over-triggering | relax soft thresholds by 5% |

---

# 11. Fitness

## 11.1 Final Fitness

```text
final_fitness =
    0.35 * anchor_integrity +
    0.20 * compression_score +
    0.20 * local_novelty +
    0.10 * linguistic_quality +
    0.05 * ambiguity_score +
    0.05 * sentiment_contrast_score +
    0.05 * fragmentation_alignment -
    repair_penalty
```

Weights are MVP defaults and MUST be recalibrated after the first calibration run.

---

## 11.2 Compression Score

```text
compression_score =
    clamp(
        information_density - redundancy_penalty,
        0.0,
        1.0
    )
```

---

## 11.3 Redundancy Penalty

```text
redundancy_penalty =
    repeated_bigram_count / total_bigram_count
```

---

## 11.4 Fragmentation Alignment

Measures alignment between:

- target punctuation_density
- observed punctuation_density
- target short_clause_ratio
- observed short_clause_ratio

Formula:

```text
fragmentation_alignment =
    1 - mean_absolute_error(
        target_fragmentation_features,
        observed_fragmentation_features
    )
```

Normalized to [0.0, 1.0].

---

# 12. Phenotype Distance

## 12.1 Formula

```text
phenotype_distance =
    0.60 * embedding_distance +
    0.25 * stylometric_delta +
    0.15 * constraint_deviation
```

Weights prioritize semantic locality over stylistic variance.

All components normalized to [0.0, 1.0].

---

## 12.2 Stylometric Delta

```text
stylometric_delta = mean(
    punctuation_variability_delta,
    sentence_length_variability_delta,
    contraction_ratio_delta
)
```

Uses the same contraction dictionary defined in Section 15.6.

---

## 12.3 Constraint Deviation

```text
constraint_deviation = mean(
    abs(target_punctuation_density - observed_punctuation_density),
    abs(target_clause_ratio - observed_clause_ratio),
    abs(target_sentiment_shift - observed_sentiment_shift)
)
```

---

# 13. Novelty

## 13.1 Local Novelty

```text
local_novelty =
    1 - max_cosine_similarity(candidate, archive)
```

---

## 13.2 Neighborhood Entropy

```text
k = 20 nearest neighbors

p_i = normalized cluster membership frequency

neighborhood_entropy =
    -Σ(p_i * log(p_i))
```

Used only as a secondary novelty signal.

---

# 14. Atomic Metric Glossary

## 14.1 punctuation_density

```text
punctuation_tokens / total_tokens
```

Counted punctuation:

```text
. , ! ? ; : — …
```

Repeated punctuation:

```text
!!! → 3 punctuation tokens
```

Unicode punctuation is normalized before counting.

---

## 14.2 short_clause_ratio

Clause separator set:

```text
. , ; : —
```

Short clause:

```text
<= 5 tokens
```

Formula:

```text
short_clauses / total_clauses
```

---

## 14.3 semantic_entropy

Proxy metric.

```text
semantic_entropy =
    mean(min(wordnet_synset_count, 10) / 10)
```

Measures lexical ambiguity proxy, NOT contextual ambiguity.

---

## 14.4 indirect_reference_ratio

Indirect token set:

```text
someone
something
somewhere
it
they
that
those
maybe
somehow
```

Formula:

```text
indirect_reference_tokens / total_tokens
```

NER/coreference resolution is intentionally NOT used in MVP.

---

## 14.5 sentiment_contrast_score

Computed across sentence boundaries.

Single-sentence texts:

```text
score = 0.0
```

Multi-sentence texts:

```text
score = abs(max(sentence_sentiment) - min(sentence_sentiment))
```

Model:

- cardiffnlp/twitter-roberta-base-sentiment

---

## 14.6 human_style_score

```text
human_style_score = mean(
    punctuation_variability,
    sentence_length_variability,
    contraction_ratio
)
```

All components normalized to [0.0, 1.0].

punctuation_variability:

```text
coefficient_of_variation(
    punctuation_per_clause
)
```

sentence_length_variability:

```text
coefficient_of_variation(
    clause_lengths
)
```

Contraction dictionary:

```text
I'm, don't, can't, it's,
we're, didn't, won't,
isn't, that's
```

---

# 15. Tokenization Policy

Tokenizer:

```text
tiktoken cl100k_base
```

Rules:

- punctuation counted as tokens
- emoji counted as tokens
- hashtags preserved
- URLs removed before metrics
- em dash treated as punctuation token
- unicode quotes normalized
- contractions remain single lexical units

---

# 16. Candidate Selection

## 16.1 Outlier Policy

Upper fitness outliers:

```text
fitness > mean + 2*std
```

are considered stochastic anomalies.

---

## 16.2 Fallback

If all candidates are filtered:

```text
select candidate with max(anchor_integrity)
```

Tie break:

1. higher local_novelty
2. lower repair_penalty
3. lexicographic genome_id

---

# 17. Reproducibility

## 17.1 Seed Policy

```text
seed = hash(genome_id + generation_id)
```

All stochastic operations MUST use this seed.

---

## 17.2 Archive Schema Versioning

Archive records MUST store:

- schema_version
- genome
- phenotype
- metrics
- embedding
- seed
- generation

---

# 18. Calibration

## 18.1 Calibration Dataset

Minimum:

```text
500 genomes
```

Sampling:

```text
Latin Hypercube Sampling
```

---

## 18.2 Acceptance Thresholds

Initial MVP targets:

| Metric | Threshold |
|---|---|
| locality correlation | >= 0.45 |
| mean anchor_integrity | >= 0.85 |
| mean repair_penalty | <= 0.08 |

Thresholds are experimental MVP defaults and subject to recalibration.

---

# 19. CI / Regression

Regression suite MUST run:

- on every release
- on translation layer changes
- on metric definition changes
- on embedding model changes

---

# 20. Execution Priority

Recommended implementation order:

1. tokenization + metrics
2. translation layer
3. anchor selection
4. relation graph
5. structural plan
6. compilation
7. validation
8. repair
9. fitness evaluation
10. locality experiments

Fitness evaluation occurs both:

- before repair
- after repair

---

# 21. Final Notes

This specification intentionally prioritizes:

- determinism
- reproducibility
- locality preservation
- measurable causality

over maximal linguistic creativity.

The MVP goal is not perfect text quality.

The MVP goal is to determine whether constrained genotype–phenotype mapping can preserve stable evolutionary signal in LLM-mediated text generation.



---

## v4.9 Clarifications and Final Hardening

### Compression Score Normalization

```text
compression_score = clamp(
    information_density - redundancy_penalty,
    0.0,
    1.0
)
```

Definitions:

```text
information_density =
    unique_content_lemmas / total_content_tokens
```

```text
redundancy_penalty =
    repeated_bigram_count / max(total_bigrams, 1)
```

Normalization Rules:
- both components normalized to `[0,1]`
- final score clamped to `[0,1]`
- repeated bigrams counted once per repeated occurrence after first appearance
- URLs removed before calculation
- hashtags and emoji remain valid tokens

### Constraint Deviation

```text
constraint_deviation = mean_absolute_error(
    normalized_target_constraints,
    normalized_observed_constraints
)
```

Observed constraints include:
- clause length
- punctuation density
- sentiment shift
- ambiguity proxy level
- question probability

All components are normalized to `[0,1]` before aggregation.

### Human Style Score Policy

`human_style_score` is a deterministic stylometric proxy used only as a low-weight auxiliary regularizer.

It is not treated as a semantic quality metric and must not dominate selection pressure.

Components:
- punctuation variability
- sentence length variability
- contraction ratio

Maximum total contribution to final fitness: `<= 0.10`

Mathematical Definitions:

```text
punctuation_variability =
    std_dev(punctuation_frequency_per_sentence)
```

```text
sentence_length_variability =
    coefficient_of_variation(sentence_lengths)
```

```text
contraction_ratio =
    contraction_tokens / total_tokens
```

Contractions use a fixed deterministic dictionary.

### Candidate Outlier Rejection

Outlier rejection is a noise-control heuristic intended to suppress unstable stochastic generations.

Rule:

```text
candidate is outlier if:
fitness > mean_fitness + 2 * std_fitness
```

Additional safeguards:
- rejection applied only when candidate_count >= 4
- at least one valid candidate must always survive
- if all candidates would be rejected, retain:
  1. highest anchor_integrity candidate
  2. then highest fitness candidate

Selection priority remains:
1. anchor integrity
2. hard constraint validity
3. final fitness
4. novelty tie-break



---

# MTES v5.0 Final Clarifications

## 1. anchor_rigidity Integration

`anchor_rigidity` is retained as an operational gene.

Mapping:

```text
anchor_rigidity ∈ [0.0, 1.0]
→ anchor_similarity_threshold ∈ [0.82, 0.96]
```

Translation:

```text
anchor_similarity_threshold =
    0.82 + (anchor_rigidity * 0.14)
```

Behavior:
- low rigidity (`0.0–0.3`) allows semantic paraphrase preservation
- medium rigidity (`0.3–0.7`) prioritizes lemma preservation
- high rigidity (`0.7–1.0`) strongly prefers exact anchor retention

Anchor validation order:
1. exact match
2. spaCy lemma match
3. cosine similarity >= dynamic anchor_similarity_threshold

`anchor_rigidity` affects:
- anchor preservation validation
- repair acceptance
- soft validation pressure

It does NOT modify hard rejection threshold:

```text
anchor_integrity < 0.70
→ reject candidate
```

The hard rejection threshold remains globally fixed for MVP comparability.

---

## 2. question_probability Restoration

`question_probability` is restored as an operational gene.

Mapping:

```text
question_probability ∈ [0.0, 1.0]
```

Translation Layer Effects:
- probability of interrogative clause generation
- rhetorical_mode bias toward reflective/question-driven structures
- punctuation preference toward `?`

Structural Plan Integration:

```text
if question_probability >= 0.65:
    rhetorical_mode_bias = reflective
```

Compilation Constraints:

```text
question_probability < 0.30
→ avoid interrogative outputs

question_probability >= 0.65
→ require at least one interrogative clause
```

---

## 3. Relation Type Assignment Priority

Relation assignment uses deterministic ordered evaluation.

```text
if cosine >= 0.80 and polarity_alignment >= 0.70:
    reinforcement

elif cosine >= 0.60 and polarity_alignment <= 0.40:
    contrast

elif cosine <= 0.35 and rarity_score >= 0.70:
    tension

elif cosine >= 0.50:
    associative

else:
    distant
```

This ordering intentionally resolves overlapping conditions.

---

## 4. TF-IDF Centrality Corpus

TF-IDF centrality uses the same calibration corpus defined in Section 7.2.

Corpus:
- 5M English tweets
- date range: 2023-01-01 → 2023-06-30
- normalized lowercase preprocessing
- URLs removed
- hashtags preserved

IDF statistics are frozen for MVP reproducibility.

---

## 5. polarity_alignment Definition

`polarity_alignment` replaces previous `polarity_delta` naming.

Definition:

```text
polarity_alignment =
    1.0 - abs(sentiment_a - sentiment_b)
```

Interpretation:
- `1.0` = identical polarity
- `0.0` = maximal polarity divergence

This definition aligns with semantic meaning of “alignment”.

---

## 6. information_density Clarification

```text
information_density =
    unique_content_lemmas / total_content_tokens
```

Where:

```text
content_tokens =
    all non-stopword lexical tokens
```

Included:
- nouns
- verbs
- adjectives
- adverbs
- hashtags

Excluded:
- stopwords
- punctuation
- URLs

This definition prevents stopword-heavy outputs from artificially inflating density.

---

## 7. Proxy Metric Weight Policy

Proxy metrics are intentionally low-weight heuristic regularizers.

Proxy metrics:
- ambiguity_score
- sentiment_contrast_score
- human_style_score
- semantic_entropy
- neighborhood_entropy

Constraint:

```text
sum(proxy_metric_weights) <= 0.30
```

Final MVP fitness decomposition:

```text
final_fitness =
    0.35 * anchor_integrity +
    0.20 * compression_score +
    0.20 * local_novelty +
    0.10 * readability_floor +
    0.03 * human_style_score +
    0.05 * ambiguity_score +
    0.05 * sentiment_contrast_score +
    0.02 * fragmentation_alignment -
    repair_cost_penalty
```

Total proxy contribution:

```text
0.03 + 0.05 + 0.05 + indirect semantic proxies
< 0.30
```

---

## 8. Pre-Repair Fitness Usage

Fitness is evaluated twice:
1. before repair
2. after repair

Pre-repair fitness is used for:
- repair leakage diagnostics
- mutation instability detection
- archive observability
- validation pressure monitoring

Only post-repair fitness participates in selection.

---

## 9. MVP Finalization Note

MTES v5.0 intentionally prioritizes:
- deterministic genotype → phenotype mapping
- measurable locality
- constrained semantic inheritance
- reproducibility over stylistic richness

Remaining limitations are treated as known MVP trade-offs rather than unresolved architectural gaps.

