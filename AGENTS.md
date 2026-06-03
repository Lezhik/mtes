# AGENTS.md

# Engineering Guidelines for AI Agents

## 1. Purpose

This document defines mandatory engineering guidelines for AI agents contributing to the MTES project.

All generated code, refactorings, tests, architecture changes, documentation updates, and configuration changes must comply with these rules.

These guidelines exist to ensure that AI-generated contributions remain:

* understandable
* maintainable
* consistent
* testable
* aligned with project specifications

The preferred outcome is not clever code.

The preferred outcome is correct, simple, maintainable code.

---

# 2. Project Context

MTES is a specification-driven research project.

Implementation must follow project specifications.

Before implementing functionality, AI agents must consult the relevant specifications.

Generated code must never contradict project specifications.

When implementation details are unclear:

1. consult the relevant specification
2. consult related specifications
3. request clarification

Do not invent behavior.

Do not infer undocumented requirements.

Do not implement speculative functionality.

---

# 3. Specification Hierarchy

When specifications and code disagree:

Specifications always win.

When specifications disagree:

1. request clarification
2. stop implementation

Do not attempt to resolve specification conflicts independently.

---

# 4. Working With Specifications

Before generating code:

1. Identify the relevant specification.
2. Verify requirements.
3. Verify interfaces.
4. Verify data contracts.
5. Verify expected behavior.
6. Generate implementation.

Avoid speculative implementation.

Avoid implementing imagined future requirements.

Specification compliance is mandatory.

### Specification References

Add specification references when:

* implementing formulas containing specification-defined constants
* implementing named algorithms defined by specifications
* implementing behavior that would not be obvious from code alone

Examples:

* fitness formulas
* edge scoring calculations
* validation thresholds
* archive retention policies

Good:

```python
# Mapping Specification §8.1
edge_score = (
    0.50 * cosine_similarity +
    0.30 * polarity_delta +
    0.20 * rarity_score
)
```

Do not add specification references when:

* behavior is self-evident from naming
* the reference duplicates obvious code
* the reference adds noise without improving maintainability

---

# 5. AI Agent Workflow

Before generating code:

1. Identify relevant specifications.
2. Verify requirements.
3. Verify interfaces.
4. Verify data contracts.
5. Verify expected behavior.
6. Generate implementation.

After generating code:

1. Verify specification compliance.
2. Verify tests.
3. Verify typing.
4. Verify naming.
5. Verify architecture boundaries.
6. Run review checklist.

---

# 6. Project Structure

Preferred project layout:

```text
src/
└── mtes/
    ├── core/
    ├── mapping/
    ├── ga/
    ├── llm/
    ├── persistence/
    ├── publication/
    ├── telegram/
    ├── monitoring/
    └── shared/

tests/
├── unit/
└── integration/

docs/

docker/

scripts/

config/
```

## Module Responsibilities

### core/

* workflow orchestration
* application services
* execution coordination

### mapping/

* genotype→phenotype mapping
* translation layer
* anchor selection
* semantic expansion
* relation graph construction

### ga/

* mutation
* crossover
* selection
* population management

### llm/

* provider adapters
* prompt construction
* constrained compilation
* candidate generation

### persistence/

* repositories
* MongoDB integration
* archive storage

### publication/

* publication workflows
* publication scheduling

### telegram/

* Telegram integration

### monitoring/

* metrics
* health checks
* observability
* structured logging

### shared/

* reusable infrastructure
* common utilities
* shared types

New top-level modules require explicit approval.

When uncertain:

request clarification before creating new modules.

Avoid creating new top-level folders without approval.

---

# 7. Core Engineering Principles

Priority order:

1. KISS
2. SOLID
3. DRY
4. YAGNI

---

# 8. KISS

Keep implementations simple.

Prefer:

* straightforward solutions
* explicit behavior
* predictable control flow

Avoid:

* clever code
* speculative abstractions
* unnecessary indirection

Good:

```python
if candidate.is_valid:
    archive_repository.save(candidate)
```

Bad:

```python
archive_strategy_provider \
    .resolve(candidate) \
    .create_archive_handler() \
    .execute(candidate)
```

Simple solutions are preferred unless additional complexity is currently required.

---

# 9. SOLID

Apply SOLID pragmatically.

Good:

```python
class GenomeRepository:
    ...

class FitnessEvaluator:
    ...
```

Bad:

```python
class GenomeFitnessStorageManager:
    ...
```

Single responsibility is preferred.

Avoid multi-purpose classes.

---

# 10. DRY

Duplicate twice:

acceptable.

Duplicate three times:

extract shared behavior.

Rules:

```text
2 occurrences:
    acceptable

3+ identical occurrences:
    extract

3+ similar occurrences:
    evaluate abstraction

If abstraction reduces clarity:
    leave duplication
    document decision
```

---

# 11. YAGNI

Implement only what is currently required.

Avoid:

* speculative features
* unused extension points
* premature flexibility
* future-proofing without evidence

Optional specification items SHALL NOT be implemented until explicitly requested.

Interfaces for optional features MAY be defined if they improve current module boundaries.

---

# 12. Architecture Rules

Prefer:

* low coupling
* high cohesion
* explicit boundaries
* dependency inversion

Avoid:

* circular dependencies
* hidden dependencies
* god objects
* utility dumping grounds

---

# 13. Dependency Inversion

Prefer interfaces and protocols.

Good:

```python
class LlmCompiler(Protocol):
    async def compile(
        self,
        request: CompileRequest
    ) -> CompileResult:
        ...
```

Avoid direct dependencies on concrete implementations.

---

# 14. Protocol vs ABC

Default choice:

```python
typing.Protocol
```

Use ABC only when explicit runtime inheritance is required.

Prefer Protocol for service contracts.

---

# 15. Naming Rules

Names must be semantic and self-explanatory.

Good:

```python
generation_fitness_score
semantic_expansion_service
archive_record_repository
```

Bad:

```python
score
service
repo
tmp
obj
```

---

# 16. Class Naming

Prefer:

```python
GenomeTranslationService
GenerationFitnessEvaluator
ArchiveRecordRepository
PhenotypeCompiler
TelegramPublicationService
```

Avoid:

```python
Manager
Helper
Processor
Utils
Engine
```

---

# 17. Method Naming

Prefer:

```python
calculate_fitness_score()
validate_candidate_output()
publish_candidate_to_telegram()
load_generation_history()
```

Avoid:

```python
run()
process()
execute()
handle()
```

---

# 18. Method Size

Methods should be small.

Guidelines:

```text
≤ 30 lines:
    acceptable

30–50 lines:
    review for decomposition

> 50 lines:
    must be decomposed
```

Methods should perform one logical task.

---

# 19. Class Size

Large classes should be decomposed.

Refactor when:

* responsibilities are unrelated
* dependency list grows excessively
* private helper count becomes large

---

# 20. Type Hints

Type hints are mandatory.

Required for:

* function parameters
* return values
* public methods
* class attributes

Good:

```python
def calculate_fitness_score(
    genome: Genome
) -> float:
    ...
```

Bad:

```python
def calculate_fitness_score(genome):
    ...
```

---

# 21. Async Programming

MTES uses async-first architecture.

I/O-bound operations:

* use async/await
* never block the event loop

Bad:

```python
time.sleep(5)
```

Good:

```python
await asyncio.sleep(5)
```

### CPU-Bound Operations

Heavy CPU-bound workloads SHALL use:

```python
ProcessPoolExecutor
```

through:

```python
run_in_executor(...)
```

Examples:

* locality correlation calculation
* embedding distance computation
* population-level fitness evaluation

### Mixed Workloads

Operations expected to complete in less than approximately 10ms may execute directly on the event loop.

Examples:

* single candidate fitness calculation
* lightweight validation
* simple transformations

Operations expected to exceed approximately 10ms should use:

```python
run_in_executor(...)
```

Population-scale calculations should always use:

```python
ProcessPoolExecutor
```

---

# 22. Comments

Prefer self-documenting code.

Comments should explain:

* why
* constraints
* specification decisions

Bad:

```python
# increment counter
counter += 1
```

Good:

```python
# Required to preserve generation ordering guarantees.
counter += 1
```

---

# 23. Error Handling

Prefer:

* typed exceptions
* meaningful messages
* fail-fast behavior

Avoid:

* silent failures
* empty exception handlers

Exception definitions should live in module-local:

```text
exceptions.py
```

Examples:

```python
InvalidGenomeError
ConstraintViolationError
ProviderUnavailableError
MongoDbUnavailableError
```

---

# 24. Partial Implementation Policy

When a dependency is not yet implemented:

1. Define interface (Protocol).
2. Create stub implementation.
3. Raise NotImplementedError.
4. Document dependency explicitly.

Example:

```python
class SemanticExpansionService:
    async def expand(...):
        raise NotImplementedError(
            "SemanticExpansionService not implemented"
        )
```

Do not implement missing dependencies speculatively.

### External Dependency Failures

When external dependencies are unavailable:

* raise an appropriate typed exception
* fail explicitly
* preserve diagnostic information

Do not:

* silently degrade behavior
* switch to hidden fallback modes
* replace production behavior with mocks

Examples:

```python
MongoDbUnavailableError
ProviderUnavailableError
TelegramGatewayUnavailableError
```

---

# 25. Existing Code Modification Rules

Preserve:

* public contracts
* documented behavior
* data formats

If code conflicts with specifications:

specification wins.

### Scope of Change Rules

Bug fixes:

* modify only affected logic

Readability improvements:

* modify only affected methods or classes

Coupling reduction:

* modify module boundaries
* avoid unrelated redesign

Avoid expanding scope beyond the requested task.

---

# 26. When To Stop Refactoring

Stop when:

* current problem is solved
* readability improves
* complexity decreases
* additional changes provide diminishing value

Avoid endless cleanup cycles.

---

# 27. Logging

Use structured logging.

Include:

* correlation identifiers
* operation identifiers
* workflow stage
* generation identifiers

Never log:

* API keys
* secrets
* credentials
* tokens

---

# 28. Logging Schema

Preferred structure:

```json
{
  "timestamp": "ISO8601",
  "level": "INFO",
  "module": "llm.compiler",
  "operation": "compile_phenotype",
  "genome_id": "gen_001",
  "message": "Compilation completed"
}
```

Field names should remain consistent across modules.

---

# 29. Security

Security is mandatory.

Always:

* validate external input
* sanitize user-generated content
* use parameterized database operations
* store secrets outside source code

Never:

* hardcode credentials
* expose stack traces to users
* log sensitive information

---

# 30. Testing

New functionality should be testable.

Prefer:

* pytest
* deterministic fixtures
* isolated tests
* behavior-focused tests

Avoid:

* external network dependencies
* real provider calls
* nondeterministic timing

Example:

```python
def test_anchor_integrity_rejects_missing_anchor():
    ...
```

Property-based testing is encouraged when appropriate.

### MongoDB Integration Tests

Preferred:

```text
Testcontainers
```

Acceptable:

```text
dedicated disposable MongoDB instance
```

Avoid:

```text
production databases
shared developer databases
```

Use real MongoDB behavior in integration tests.

Do not use mongomock for integration tests.

mongomock may be used only for unit tests.

---

# 31. LLM Testing

Unit tests must not call real providers.

Use:

```python
MockLlmCompiler
FakeLlmProvider
```

Integration tests may verify adapter behavior separately.

---

# 32. Docker Guidelines

Containers should be:

* deterministic
* reproducible
* minimal

Prefer:

* explicit versions
* environment-based configuration

Avoid:

* hidden runtime dependencies
* manual configuration steps

---

# 33. Git Commit Guidelines

Use Conventional Commits.

Examples:

```text
feat(mapping): add locality correlation calculation
fix(persistence): resolve archive race condition
refactor(llm): simplify compiler adapter
docs(mapping): update translation rules
test(ga): add mutation coverage
chore(docker): update image versions
```

Allowed prefixes:

* feat
* fix
* refactor
* docs
* test
* chore

### Commit Subject Length

Preferred:

```text
≤ 72 characters
```

Keep commit subjects concise and descriptive.

---

# 34. Code Review Checklist

Apply this checklist before each commit and before marking a task complete.

```text
[ ] Specification compliance verified
[ ] Correct specification version verified
[ ] Type hints present
[ ] Names are descriptive
[ ] Methods are small
[ ] Classes are focused
[ ] No unnecessary abstractions
[ ] Error handling is explicit
[ ] Logging is appropriate
[ ] Tests are included
[ ] Documentation is updated
[ ] No credentials exposed
```

---

# 35. When To Request Clarification

Stop and request clarification when:

* specifications conflict
* behavior is undefined
* architecture is ambiguous
* multiple interpretations exist
* module placement is unclear
* new top-level modules seem necessary

Do not invent missing requirements.

---

# 36. Decision Hierarchy

When choosing between alternatives:

1. Correctness
2. Simplicity
3. Readability
4. Maintainability
5. Performance
6. Flexibility

Do not sacrifice clarity for premature optimization.

---

# 37. Final Rule

The preferred solution is usually the simplest solution that correctly satisfies the specification.

Code should be:

* understandable
* maintainable
* modular
* explicit

If two implementations solve the same problem, prefer the one that another engineer can understand six months later.

Simple beats clever.

Correct beats flexible.

Specification compliance beats personal preference.
