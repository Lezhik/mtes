# MTES LLM Interaction Specification v3.1

## 1. Purpose

This specification defines all interactions between the MTES evolutionary system and Large Language Models (LLMs).

The purpose of this document is to ensure:

* deterministic system behavior where required;
* reproducible prompt execution;
* stable genotype-to-phenotype locality;
* controlled LLM influence;
* provider-independent implementation.

This specification is normative.

---

# 2. Core Principles

## 2.1 LLMs Are Execution Components

LLMs generate and evaluate text.

LLMs do not define:

* fitness;
* archive management;
* routing decisions;
* dictionary management;
* benchmark governance;
* validation decisions.

---

## 2.2 Deterministic Authority

The following components SHALL remain deterministic:

* routing engine;
* validation engine;
* fitness calculation;
* archive management;
* dictionary management;
* benchmark governance.

LLM outputs SHALL NOT override deterministic measurements.

---

## 2.3 LLM Is Not Source of Truth

All LLM outputs SHALL be treated as proposals.

System acceptance SHALL be determined exclusively through validation and evaluation pipelines.

---

## 2.4 Separation of Responsibilities

Deterministic MTES components SHALL define:

* search space;
* mappings;
* measurements;
* fitness;
* archive operations.

LLM components SHALL perform:

* constraint expansion;
* phenotype generation;
* candidate generation;
* optional judging;
* optional diagnostics.

---

# 3. Pipeline Overview

```text
Genome
↓
P3 Constraint Expansion
↓
P3 Constraint Validation
↓
P4 Phenotype Compilation
↓
Validation Pipeline
↓
Repair Retry (optional)
↓
P5 Candidate Expansion
↓
Candidate Ranking
↓
Mapping Evaluation
↓
Fitness Evaluation
↓
Archive
```

P6 Judge Evaluation is optional and may be executed during evaluation.

P7 Failure Diagnostics is invoked only after failures.

---

# 4. Phase Definitions

| Phase | Name                    | LLM Required |
| ----- | ----------------------- | ------------ |
| P1    | Dictionary Construction | No           |
| P2    | Mapping Construction    | No           |
| P3    | Constraint Expansion    | Yes          |
| P4    | Phenotype Compilation   | Yes          |
| P5    | Candidate Expansion     | Yes          |
| P6    | Judge Evaluation        | Optional     |
| P7    | Failure Diagnostics     | Optional     |

For MVP:

```text
LLM usage in P1 is prohibited.
LLM usage in P2 is prohibited.
```

Review models SHALL NOT participate in:

* dictionary construction;
* mapping construction;
* coordinate assignment.

Review models MAY be used only for:

* P6 Judge Evaluation;
* P7 Failure Diagnostics.

---

# 5. Decoding Profiles

## 5.1 General Rules

Decoding profiles are calibration defaults.

Parameter changes SHALL require:

* benchmark evaluation;
* audit logging;
* version increment.

Regular recalibration SHALL NOT occur before:

```text
10,000 evaluated generations
```

Emergency recalibration MAY occur immediately if any condition persists for 500 consecutive evaluated candidates:

```text
schema_compliance < 99.0%

validation_pass_rate < 90.0%

duplicate_candidate_rate > 10.0%
```

---

## 5.2 P3 Constraint Expansion

```text
temperature = 0.20
top_p = 0.80
presence_penalty = 0.00
frequency_penalty = 0.00
```

Purpose:

```text
Maximum constraint stability.
Minimum semantic invention.
```

---

## 5.3 P4 Phenotype Compilation

```text
temperature = 0.60
top_p = 0.95
presence_penalty = 0.10
frequency_penalty = 0.10
```

Purpose:

```text
Controlled generation.
Moderate linguistic flexibility.
```

---

## 5.4 P5 Candidate Expansion

```text
temperature = 0.80
top_p = 0.95
presence_penalty = 0.30
frequency_penalty = 0.20
```

Purpose:

```text
Maximum candidate diversity.
```

---

## 5.5 P6 Judge Evaluation

```text
temperature = 0.00
top_p = 0.10
presence_penalty = 0.00
frequency_penalty = 0.00
```

Rationale:

```text
P6 prioritizes reproducibility over creativity.

temperature = 0.00 SHALL be treated as
the primary determinism control.

top_p is retained for provider compatibility.

Some providers ignore top_p when
temperature = 0.00.

Such behavior is acceptable.
```

Provider-specific decoding behavior SHALL be documented.

---

# 6. Routing

## 6.1 Routing Dimensions

```text
anchor_rigidity
fragmentation_bias
compression_target
ambiguity_bias
```

---

## 6.2 Activation Scores

```text
anchor_score = anchor_rigidity

fragmentation_score = fragmentation_bias

compression_score = compression_target

ambiguity_score = ambiguity_bias
```

All scores are normalized to:

```text
[0,1]
```

---

## 6.3 Activation Threshold

```text
activation_threshold = 0.70
```

Family activates if:

```text
activation_score >= activation_threshold
```

---

## 6.4 Prompt Families

| Family | Trigger       |
| ------ | ------------- |
| P4-A   | Default       |
| P4-B   | Anchor        |
| P4-C   | Fragmentation |
| P4-D   | Compression   |
| P4-E   | Ambiguity     |
| P4-F   | Combined      |

---

## 6.5 Hysteresis

To avoid prompt thrashing:

```text
switch_threshold =
current_family_score + 0.10
```

New family becomes active only if:

```text
candidate_score >
current_family_score + 0.10
```

---

## 6.6 Combined Mode

Combined Mode activates when:

```text
active_family_count >= 2
```

Combined activation:

```text
combined_activation =
max(active_family_scores)
```

Instruction priority:

```text
1 Anchor
2 Compression
3 Fragmentation
4 Ambiguity
```

Conflict resolution:

```text
higher priority wins

lower priority becomes advisory

fallback to default prompt prohibited
```

If two instructions share equal priority:

```text
deterministic ordering by family identifier

P4-B
P4-C
P4-D
P4-E
```

---

## 6.7 Combined Mode Construction

Prompt construction SHALL be:

```text
Base Prompt

+

Activated Family Instructions

ordered by priority
```

The following are prohibited:

```text
instruction rewriting

instruction weighting

instruction merging
```

---

## 6.8 Combined Mode Example

Genome:

```text
anchor_rigidity = 0.82
fragmentation_bias = 0.76
compression_target = 0.41
ambiguity_bias = 0.22
```

Activated:

```text
P4-B Anchor

P4-C Fragmentation
```

Selected:

```text
P4-F Combined
```

Instruction order:

```text
1 Anchor Preservation

2 Fragmentation Guidance
```

---

# 7. P3 Constraint Expansion

## 7.1 Purpose

Transform genome state into explicit generation constraints.

P3 SHALL:

```text
expand existing meaning
```

P3 SHALL NOT:

```text
invent meaning

introduce new themes

introduce new anchors

optimize linguistic quality
```

---

## 7.2 Input

```json
{
  "semantic_genes": {},
  "numeric_genes": {},
  "active_dimensions": []
}
```

---

## 7.3 Output Schema

```json
{
  "generation_constraints": [
    {
      "type": "required",
      "dimension": "anchor",
      "value": "winter"
    },
    {
      "type": "target",
      "dimension": "fragmentation",
      "value": 0.80
    }
  ]
}
```

Constraint types:

```text
required

prohibited

target
```

### required

```text
Generation SHALL contain
specified concept or anchor.
```

### prohibited

```text
Generation SHALL NOT contain:

specified concept

specified anchor

specified token class

specified semantic relation
```

Enforcement:

```text
prompt instructions

semantic validation
```

### target

```text
Generation SHOULD approximate
specified target value.
```

---

## 7.4 P3 Validation

Before P4 execution:

```text
schema validation

constraint validation
```

MUST pass successfully.

---

## 7.5 Example

Input:

```json
{
  "anchor":"winter",
  "fragmentation":0.8
}
```

Output:

```json
{
  "generation_constraints":[
    {
      "type":"required",
      "dimension":"anchor",
      "value":"winter"
    },
    {
      "type":"target",
      "dimension":"fragmentation",
      "value":0.8
    }
  ]
}
```

---

# 8. P4 Phenotype Compilation

## 8.1 Input

Validated P3 output.

---

## 8.2 Output

Single candidate phenotype.

---

## 8.3 Compilation Rules

P4 SHALL:

```text
preserve required constraints

respect prohibited constraints

attempt target constraints
```

P4 SHALL NOT:

```text
optimize engagement

optimize virality

optimize persuasion

invent semantic content
```

---

## 8.4 Constraint Priority

```text
required > prohibited > target
```

Constraint conflicts SHALL be resolved according to this order.

---

# 9. P5 Candidate Expansion

## 9.1 Purpose

Generate multiple candidate phenotypes from a validated P4 candidate.

The purpose of P5 is to:

```text
increase exploration

improve novelty

preserve locality

maintain constraint compliance
```

---

## 9.2 Candidate Count

```text
5 alternatives
```

Default candidate count SHALL be:

```text
5
```

Implementations MAY support configuration.

All candidate counts SHALL be audit logged.

---

## 9.3 Constraint Score

```text
constraint_score =
satisfied_constraints
/
total_constraints
```

Range:

```text
[0,1]
```

---

## 9.4 Diversity Score

```text
diversity_score =
0.70 * embedding_distance
+
0.30 * token_set_distance
```

where:

```text
token_set_distance =
1 - Jaccard(token_sets)
```

---

### Embedding Metadata

Implementations SHALL record:

```text
embedding_model_id

embedding_model_version

embedding_dimension

distance_metric
```

---

## 9.5 Quality Score

```text
quality_score =
0.40 * coherence_metric
+
0.30 * readability_metric
+
0.30 * grammar_metric
```

---

### coherence_metric

```text
coherence_metric =
valid_links
/
total_links
```

Definition:

```text
sentence_link =
pair of adjacent sentences
```

Example:

```text
S1 → S2
S2 → S3
S3 → S4
```

Produces:

```text
total_links = 3
```

---

### Valid Link Rules

A sentence link is valid if at least one condition is satisfied:

```text
shared subject continuity

shared topic continuity

explicit discourse connector

reference resolution continuity
```

---

### Deterministic Coherence Detector

Implementation SHALL use:

```text
spaCy en_core_web_sm
```

or benchmark-equivalent implementation.

---

#### Rule 1: Shared Subject Continuity

Valid if:

```text
dependency parser identifies
same grammatical subject
in adjacent sentences
```

---

#### Rule 2: Shared Topic Continuity

Valid if:

```text
at least one non-stopword lemma
appears in both sentences
```

---

#### Rule 3: Explicit Discourse Connector

Valid if second sentence begins with:

```text
however
therefore
thus
meanwhile
instead
moreover
furthermore
consequently
but
and
yet
so
```

This list SHALL be fixed.

---

#### Rule 4: Reference Resolution Continuity

Valid if:

```text
pronoun reference
in sentence N+1

can be resolved
to an entity
present in sentence N
```

Detection SHALL use deterministic coreference rules.

---

### Single-Sentence Edge Case

If:

```text
total_links = 0
```

then:

```text
coherence_metric = 1.0
```

Rationale:

```text
No inter-sentence coherence violations are possible.
```

---

### readability_metric

```text
normalized Flesch Reading Ease
```

Implementation SHALL reuse Mapping Specification implementation.

---

### grammar_metric

```text
grammar_metric =
1 - error_rate
```

where:

```text
error_rate =
grammar_errors
/
token_count
```

Range:

```text
0 ≤ error_rate ≤ 1
```

---

### Deterministic Grammar Detector

Implementation SHALL use:

```text
language_tool_python
```

Configuration:

```text
language = en-US
```

Alternative implementations require benchmark equivalence validation.

---

### Grammar Error Types

Errors include:

```text
agreement violations

tense violations

invalid punctuation sequences

sentence boundary violations
```

Examples:

Agreement:

```text
The dogs runs.
```

Tense:

```text
Yesterday he goes home.
```

Punctuation:

```text
Hello,, world.
```

Boundary:

```text
winter shadows crossed the street
they vanished
```

---

## 9.6 Ranking Formula

```text
overall_score =
0.50 * constraint_score
+
0.30 * diversity_score
+
0.20 * quality_score
```

Highest score wins.

---

## 9.7 Duplicate Detection

Candidate considered duplicate if:

```text
embedding_distance < 0.05
```

This threshold is intentionally conservative and represents near-identical semantic defense.

Duplicates SHALL be regenerated.

Maximum:

```text
2 regeneration attempts
```

---

## 9.8 Candidate Selection

Only top-ranked candidate proceeds to:

```text
Mapping Evaluation
```

Remaining candidates SHALL be:

```text
logged

stored in candidate archive

available for novelty analysis

excluded from fitness evaluation

excluded from evolutionary selection
```

---

## 9.9 Candidate Archive

Candidate Archive is separate from the evolutionary Archive.

Candidate Archive:

```text
stores rejected P5 candidates

supports novelty estimation

supports diagnostics
```

Candidate Archive SHALL NOT:

```text
participate in selection

participate in reproduction

participate in fitness ranking
```

---

# 10. Judge Evaluation

## 10.1 Contribution Limits

Judge contribution SHALL affect only:

```text
linguistic_quality_component
```

Maximum:

```text
30%
```

Judge SHALL NEVER directly modify:

```text
final_fitness

novelty

locality

archive insertion
```

---

## 10.2 Judge Checklist

### Relevance

```text
[ ] semantic scope preserved

[ ] required anchors preserved

[ ] no unrelated concepts introduced
```

---

### Coherence

```text
[ ] references resolved

[ ] no contradictions

[ ] transitions valid
```

---

### Novelty

```text
[ ] not archive duplicate

[ ] not paraphrase duplicate

[ ] meaningful variation present
```

---

## 10.3 Judge Rubric Example

Candidate:

```text
Winter lights reflected on the river.
```

Evaluation:

```text
relevance = 0.95

coherence = 1.00

novelty = 0.62
```

Judge SHALL return scores only.

---

# 11. Validation Pipeline

## Stage 1

### Schema Validation

Severity:

```text
Critical
```

Checks:

```text
JSON schema compliance

required fields

value ranges
```

---

## Stage 2

### Constraint Validation

Severity:

```text
Critical
```

Checks:

```text
required constraints

prohibited constraints

target constraint format
```

---

## Stage 3

### Semantic Validation

---

#### Anchor Preservation

Uses Mapping Specification Section 6.3.

Severity:

```text
Critical
```

---

#### Compression Compliance

Tolerance:

```text
±10%
```

Severity:

```text
Critical
```

---

#### Mapping Consistency

```text
|observed - target| <= 0.15
```

Applied only to active routed dimensions.

Not performed for:

```text
P4-A
```

Severity:

```text
Critical
```

---

#### Structural Integrity

Severity:

```text
Warning
```

---

## Stage 4

### Integration Validation

Severity:

```text
Critical
```

Checks:

```text
archive schema compatibility

embedding pipeline compatibility

fitness pipeline compatibility

serialization compatibility
```

---

# 12. Failure Diagnostics

Failure categories:

```text
schema_failure

semantic_failure

routing_failure

mapping_failure

bucket_contamination

provider_failure
```

P7 is a cross-layer diagnostic phase.

---

# 13. Retry and Fallback

## 13.1 Retry Policy

```text
schema_failure = 1 retry

timeout = 2 retries

semantic_failure = 1 repair retry
```

---

## 13.2 Repair Prompt

### System

```text
Repair only the violated constraint.

Preserve all remaining content.

Maximum modification budget:
15% of tokens.
```

### User

```text
Violation:
{{violation}}

Candidate:
{{candidate}}
```

If modification exceeds:

```text
15%
```

then:

```text
repair fails

budget override prohibited
```

---

### Repair Example

Violation:

```text
Anchor Preservation Failed

Required Anchor:
winter
```

Candidate:

```text
The city lights reflected on the river.
```

Repair:

```text
The winter city lights reflected on the river.
```

---

## 13.3 Fallback

Provider configurable.

Recommended chain:

```text
Primary
→ Secondary
→ Tertiary
```

---

## 13.4 Recovery

Return to primary after:

```text
5 consecutive successful canary requests
```

---

## 13.5 Fallback Logging

Required:

```text
is_fallback_output

fallback_provider

fallback_model
```

Fallback outputs SHALL NOT receive modified fitness weighting.

---

# 14. Benchmark Governance

Minimum benchmark size:

```text
500 samples
```

Required metadata:

```text
benchmark_version

benchmark_date

benchmark_size
```

Changes require:

```text
review approval

version increment

full recalibration
```

---

# 15. Prompt Templates

## 15.1 P3 Constraint Expansion

### System

```text
You are a constraint compiler.

Expand implicit genome information into explicit generation constraints.

Do not invent meaning.
Do not add concepts.
Do not optimize text quality.

Return JSON only.
```

### User

```json
{
  "genome":"{{genome}}"
}
```

---

## 15.2 P4-A Default

### System

```text
Generate phenotype from constraints.

Preserve all constraints.

Do not optimize for:
- human appeal
- engagement
- helpfulness
- persuasion
- marketing value

Do not introduce concepts
not present in constraints.

Output text only.
```

### User

```json
{
  "constraints":"{{constraints}}"
}
```

### Few-Shot Example

Constraint:

```text
anchor = winter
```

Correct:

```text
Winter shadows crossed the station.
```

Incorrect:

```text
A beautiful holiday season filled everyone with joy.
```

---

## 15.3 P4-B Anchor Guided

Additional Instruction:

```text
Anchor preservation has highest priority.
```

Few-Shot:

Constraint:

```text
anchor = winter
```

Correct:

```text
Winter shadows crossed the empty street.
```

Incorrect:

```text
Cold shadows crossed the empty street.
```

---

## 15.4 P4-C Fragmentation

Additional Instruction:

```text
Prefer fragmented structure.
```

Few-Shot:

Correct:

```text
Broken lights.
Wet pavement.
Silence.
```

Incorrect:

```text
The lights reflected on the wet pavement while silence filled the street.
```

---

## 15.5 P4-D Compression

Additional Instruction:

```text
Minimize token count while preserving constraints.
```

Few-Shot:

Correct:

```text
Winter. Empty station.
```

Incorrect:

```text
It was winter and the station appeared completely empty.
```

---

## 15.6 P4-E Ambiguity

Additional Instruction:

```text
Allow multiple valid interpretations.
```

Few-Shot:

Correct:

```text
The key remained where it had always been.
```

Incorrect:

```text
John left the brass key on the kitchen table at noon.
```

---

## 15.7 P4-F Combined Mode

### System Addition

```text
Apply activated instructions
in priority order.

Do not reinterpret priorities.

Higher-priority instructions override lower-priority instructions.
```

Few-Shot:

Active:

```text
Anchor + Fragmentation
```

Output:

```text
Winter.
Broken signs.
Empty windows.
```

---

## 15.8 P6 Judge

### System

```text
Evaluate candidate.

Use checklist only.

Do not rewrite.
Do not explain.

Return scores only.
```

### User Example

```text
Candidate:

Winter lights reflected on the river.

Checklist:

Relevance
Coherence
Novelty
```

---

# 16. Integration Contracts

## 16.1 Mapping Consistency

Uses Mapping Specification metrics.

Duplicate implementations prohibited.

---

## 16.2 Fitness

Final fitness remains defined by Mapping Specification.

---

## 16.3 Execution Order

```text
Genome
→ P3
→ P3 Validation
→ P4
→ Validation
→ Repair
→ P5
→ Ranking
→ Mapping Evaluation
→ Fitness
→ Archive
```

---

# 17. End-to-End Example

Genome:

```json
{
  "anchor":"winter",
  "fragmentation":0.8
}
```

P3:

```json
{
  "generation_constraints":[
    {
      "type":"required",
      "dimension":"anchor",
      "value":"winter"
    }
  ]
}
```

P4:

```text
Winter.
Broken windows.
Silent street.
```

Validation:

```text
PASS
```

P5:

```text
5 candidates generated
```

Ranking:

```text
candidate_3 selected

overall_score = 0.74
```

Mapping Evaluation:

```text
PASS
```

Fitness:

```text
0.81
```

Archive:

```text
stored
```

---

# 18. Implementation Requirements

Required:

* Prompt Registry
* Prompt Versioning
* Routing Engine
* Validation Engine
* Repair Engine
* Fallback Controller
* Benchmark Governance
* Candidate Archive
* Audit Logging
* Judge Calibration

---

# 19. Acceptance Criteria

```text
routing_reproducibility = 100%

schema_compliance >= 99.9%

validation_pass_rate >= 95%

duplicate_candidate_rate <= 2%

fallback_activation_rate <= 5%

benchmark_drift <= 10%

judge_contribution <= 30%
```

---

# 20. Final Notes

This specification defines a bounded LLM subsystem.

LLMs execute generation and evaluation tasks.

Deterministic MTES components remain authoritative.

LLMs SHALL support the evolutionary process.

LLMs SHALL NOT define it.
