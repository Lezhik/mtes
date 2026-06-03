# MTES Software Requirements Specification (SRS) v1.0

# 1. Purpose

This document defines the software implementation requirements for the MTES system.

The purpose of this specification is to define:

* executable modules
* operator workflows
* command-line interface requirements
* daemon execution requirements
* monitoring requirements
* reporting requirements
* operational behavior
* deployment requirements
* evolution control requirements

This document intentionally focuses on operational software behavior.

This document intentionally does not define:

* evolutionary algorithms
* genotype representation
* fitness calculations
* phenotype generation rules
* genotype–phenotype mapping
* database schema
* system architecture
* bootstrap calibration methodology

These topics are defined in separate specifications.

---

# 2. System Overview

MTES is an automated evolutionary text-generation system capable of:

* initializing semantic resources
* generating candidate tweets
* executing evolutionary cycles
* publishing content through Telegram
* collecting publication statistics
* producing operational reports
* executing continuously in daemon mode

The system supports both interactive execution and unattended production operation.

---

# 3. High-Level Modules

| Module    | Purpose                               |
| --------- | ------------------------------------- |
| bootstrap | system initialization                 |
| generator | phenotype generation                  |
| evolution | evolutionary control and monitoring   |
| telegram  | publication and statistics collection |
| reports   | operational reporting                 |
| daemon    | scheduling and background execution   |

---

# 4. Bootstrap Module

## 4.1 Responsibilities

The bootstrap module SHALL:

* initialize semantic resources
* initialize dictionaries
* validate provider connectivity
* validate MongoDB connectivity
* initialize population state
* initialize archives
* initialize configuration-dependent resources

## 4.2 Command

```bash
mtes bootstrap
```

## 4.3 Idempotency

Bootstrap execution SHALL be idempotent.

If bootstrap resources already exist:

* existing resources SHALL be reused
* completed stages SHALL be skipped
* execution SHALL NOT destroy existing state

Optional force execution:

```bash
mtes bootstrap --force
```

Force execution MAY rebuild bootstrap resources.

---

# 5. Operating Modes

## 5.1 Console Mode

Console Mode SHALL support:

* interactive execution
* immediate output to stdout
* manual invocation
* debugging workflows
* validation workflows

Typical use cases:

* development
* testing
* debugging
* validation
* bootstrap verification

## 5.2 Daemon Mode

Daemon Mode SHALL support:

* continuous background execution
* timer-driven scheduling
* database persistence
* monitoring integration
* automatic recovery
* graceful shutdown

Intended for:

* production operation
* VPS deployment
* Docker deployment

## 5.3 Scheduling Model

Scheduling SHALL be implemented by an internal scheduler.

The implementation MAY use:

* asyncio scheduling
* APScheduler
* equivalent embedded scheduling mechanisms

External cron execution MAY be supported but SHALL NOT be required.

## 5.4 Daemon State Persistence

Daemon execution SHALL persist:

* active schedules
* unfinished jobs
* publication queues
* statistics collection state
* evolution state

Upon restart:

* pending jobs SHALL be recovered
* incomplete jobs MAY be retried
* state SHALL be restored from persistent storage

## 5.5 Concurrency and Backpressure

The daemon SHALL support configurable concurrency limits.

Worker count refers to evolutionary execution workers.

Generation, publication, maintenance, and monitoring subsystems MAY internally use independent execution contexts.

Example:

```yaml
daemon:
  worker_count: 1
  generation_queue_size: 100
  publication_queue_size: 100
  resume_threshold: 50
```

Requirements:

* bounded worker pools
* bounded publication queues
* bounded generation queues

When queue limits are exceeded:

* new jobs SHALL be delayed
* existing jobs SHALL continue
* daemon SHALL remain operational

---

# 6. Generation Module

## 6.1 Purpose

Generation is distinct from evolution.

Generation:

* produces one or more phenotypes
* may execute independently
* does not modify evolutionary state
* does not advance generation counters

Generation SHALL remain available even when evolution is PAUSED.

## 6.2 Commands

```bash
mtes generate
```

```bash
mtes generate --count N
```

```bash
mtes generate --daemon
```

## 6.3 Output

Output SHALL include:

* request identifier
* timestamp
* completion status
* generated text
* execution duration

JSON output:

```bash
mtes generate --json
```

## 6.4 Batch Generation

Requirements:

* maximum batch size: 100 by default
* configurable batch size
* partial failures SHALL NOT abort the batch
* successful items SHALL be persisted
* failed items SHALL be logged

---

# 7. Evolution Module

## 7.1 Purpose

The evolution module provides operational control over evolutionary execution.

Responsibilities:

* lifecycle management
* evolutionary execution control
* status reporting
* operator administration

The module SHALL NOT define evolutionary algorithms.

## 7.2 Evolution Lifecycle States

Supported states:

```text
CREATED
RUNNING
PAUSED
STOPPING
STOPPED
RESETTING
FAILED
```

Allowed transitions:

```text
CREATED -> RUNNING

RUNNING -> PAUSED
RUNNING -> STOPPING
RUNNING -> FAILED

PAUSED -> RUNNING
PAUSED -> STOPPING

STOPPING -> STOPPED

STOPPED -> RUNNING
STOPPED -> RESETTING

RESETTING -> CREATED
```

### Pause Semantics

PAUSED state SHALL be entered only at evolutionary cycle boundaries.

Requirements:

* active LLM calls SHALL complete
* active validation SHALL complete
* active evolutionary cycle SHALL complete
* no new cycle SHALL begin

Resume SHALL continue with the next evolutionary cycle.

Partially executed cycles SHALL NOT exist.

## 7.3 Commands

### Status

```bash
mtes evolution status
```

```bash
mtes evolution status --json
```

Example:

```text
status: RUNNING
generation: 154
population_size: 1000
fitness_mean: 0.72
fitness_std: 0.11
queue_depth: 12
active_workers: 1
```

### Pause

```bash
mtes evolution pause
```

### Resume

```bash
mtes evolution resume
```

### Stop

```bash
mtes evolution stop
```

### Reset

```bash
mtes evolution reset
```

## 7.4 Administrative Safeguards

Administrative commands:

* pause
* resume
* stop
* reset

SHALL require authenticated operator access.

Authentication MAY be implemented using:

* environment variable secrets
* local operator credentials
* Telegram operator authentication
* equivalent mechanisms defined by deployment configuration

### Standard Reset

```bash
mtes evolution reset --confirm
```

Standard reset SHALL:

* reset generation counter
* create a new population
* preserve archives
* preserve publication history
* preserve historical metrics

### Hard Reset

```bash
mtes evolution reset --hard-reset --confirm
```

Hard reset SHALL:

* remove archives
* remove population state
* remove historical metrics
* recreate initial system state

---

# 8. Telegram Module

## 8.1 Commands

```bash
mtes telegram publish
```

```bash
mtes telegram stats
```

```bash
mtes telegram stats --json
```

```bash
mtes telegram --daemon
```

## 8.2 Statistics Collection

Default period:

```text
last 24 hours
```

Output SHALL support:

* console summary
* JSON output

## 8.3 Rate Limiting

Default:

```text
30 messages per minute
```

## 8.4 Publication Modes

Supported:

* immediate publication
* scheduled publication

Scheduled publication SHALL use the internal scheduler.

---

# 9. Reporting Module

## 9.1 Command

```bash
mtes report
```

```bash
mtes report --json
```

## 9.2 Report Contents

### Evolution Summary

* generation number
* fitness mean
* fitness standard deviation
* locality correlation
* locality correlation standard deviation
* anchor integrity mean

Example:

```text
locality_correlation = 0.52 ± 0.03
```

### Recent Generated Content

Each entry SHOULD include:

* generation number
* fitness score
* novelty score
* anchor integrity
* generated text

## 9.3 Charts

Recommended:

* fitness trends
* locality trends
* publication activity
* validation trends
* repair trends

## 9.4 Output Formats

Required:

* HTML
* JSON

Optional:

* CSV

---

# 10. Metrics Export

## 10.1 Endpoint

```text
GET /metrics
```

Prometheus format.

## 10.2 Operational Metrics

Counters:

```text
mtes_generation_total
mtes_publication_total
mtes_validation_pass_total
mtes_repair_total
mtes_database_failures_total
mtes_telegram_failures_total
```

## 10.3 Research Metrics

Gauges:

```text
mtes_population_generation
mtes_fitness_mean
mtes_fitness_std
mtes_anchor_integrity_mean
mtes_locality_correlation
mtes_repair_rate
```

Provider metric:

```text
mtes_provider_info{provider="openai",status="active"} 1
```

### Locality Correlation Update Policy

Locality correlation SHALL NOT be recalculated after every generation.

It SHALL be updated using a configurable measurement interval.

Example:

```yaml
metrics:
  locality_measurement_interval: 100 generations
```

---

# 11. Health Endpoint

## 11.1 Endpoint

```text
GET /health
```

Example:

```json
{
  "status":"healthy",
  "evolution_status":"RUNNING",
  "queue_depth":12,
  "active_workers":1,
  "last_generation_at":"...",
  "last_publication_at":"..."
}
```

## 11.2 Status Values

```text
healthy
degraded
unhealthy
```

## 11.3 Requirements

* response time < 1 second
* read-only operation
* no authentication required for local deployments

---

# 12. Configuration

## 12.1 Format

YAML

## 12.2 Location

Default:

```text
./config.yaml
```

## 12.3 Example

```yaml
database:
  connection_string: mongodb://localhost:27017/mtes

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

---

# 13. Error Handling

## 13.1 Infrastructure Retry Policy

```text
1s
2s
4s
```

Maximum:

```text
3 attempts
```

## 13.2 Retry Layering

Infrastructure retries operate independently from application-level retries.

## 13.3 Provider Failover

```text
primary
→ secondary
→ fallback
```

## 13.4 Error Severity

### Critical

* invalid configuration
* MongoDB unavailable during startup

### Warning

* provider failure
* Telegram failure

---

# 14. Daemon Process Management

## 14.1 Signals

```text
SIGTERM
SIGINT
```

## 14.2 Graceful Shutdown

Shutdown SHALL:

* stop scheduling
* complete active evolutionary cycle
* flush logs
* persist state
* close MongoDB connections

## 14.3 Recovery SLA

Recommended:

```text
state restoration < 60 seconds
```

Recommended:

```text
daemon recovery < 120 seconds
```

## 14.4 PID File

Default:

```text
./runtime/mtes.pid
```

---

# 15. Logging

## 15.1 Levels

```text
ERROR
WARN
INFO
DEBUG
```

## 15.2 Structured Logging

Recommended:

```text
JSON Lines
```

## 15.3 Verbose Mode

```bash
--verbose
```

## 15.4 Sanitized Verbose Mode

```bash
--verbose-sanitized
```

## 15.5 Audit Logging

Administrative actions SHALL be logged.

Required fields:

* operator
* timestamp
* command
* result

---

# 16. CLI Reference

## Global Flags

```bash
--verbose
--verbose-sanitized
--config PATH
--json
```

Commands:

```bash
mtes bootstrap

mtes generate
mtes generate --count N

mtes evolution status --json
mtes evolution pause
mtes evolution resume
mtes evolution stop
mtes evolution reset

mtes telegram publish
mtes telegram stats --json

mtes report --json
```

---

# 17. Security Requirements

## 17.1 Prompt Safety

Required:

* prompt validation
* prompt sanitization
* malformed request rejection
* prompt injection mitigation

## 17.2 Rate Limiting

Required:

* Telegram throttling
* provider throttling
* operator command throttling

## 17.3 Secret Management

Secrets SHALL NOT be hardcoded.

## 17.4 Administrative Authorization

Administrative commands SHALL require authenticated operator access.

Authentication source SHALL be configurable.

Administrative actions SHALL generate audit log entries.

---

# 18. Non-Functional Requirements

## 18.1 Bootstrap

Technical bootstrap:

```text
< 60 minutes recommended
```

Calibration and publication trials excluded.

## 18.2 Generation

```text
provider-dependent
```

Target:

```text
< 60 seconds recommended
```

## 18.3 Health Endpoint

```text
< 1 second
```

## 18.4 Report Generation

```text
< 5 minutes recommended
```

## 18.5 Availability

Automatic recovery after restart SHOULD be supported.

---

# 19. Exit Codes

| Code | Meaning                    |
| ---- | -------------------------- |
| 0    | success                    |
| 1    | general error              |
| 2    | invalid arguments          |
| 3    | bootstrap failed           |
| 4    | provider validation failed |
| 5    | MongoDB connection failed  |
| 6    | Telegram connection failed |

---

# 20. Acceptance Criteria

Implementation SHALL be considered complete when:

* bootstrap succeeds
* generation succeeds
* evolution control succeeds
* daemon execution succeeds
* daemon recovery succeeds
* publication succeeds
* statistics collection succeeds
* health endpoint functions
* metrics endpoint functions
* HTML reports are generated
* JSON reports are generated
* audit logging functions
* graceful shutdown functions

---

# 21. Final Note

The purpose of MTES is not merely content generation.

MTES is an evolutionary research system that generates text, evaluates evolutionary progress, maintains population state, and supports long-running experimental execution.

This specification defines the operational software behavior required to run, observe, control, monitor, and maintain that system in both development and production environments.
