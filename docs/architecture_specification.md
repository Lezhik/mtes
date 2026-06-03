# MTES Architecture Specification v1.0

## 1. Purpose

This specification defines the software architecture of MTES (Mutation-Traceable Evolutionary Synthesis).

The document defines:

* architectural principles
* module boundaries
* module responsibilities
* inter-module interaction contracts
* workflow coordination
* fault isolation
* concurrency model
* deployment architecture
* observability requirements
* security requirements

The goal is to provide a production-ready architecture suitable for deployment on a Linux VPS.

---

# 2. Scope

## 2.1 In Scope

This specification defines:

* system modules
* module interaction patterns
* workflow orchestration architecture
* infrastructure boundaries
* deployment architecture
* operational requirements

---

## 2.2 Out of Scope

This specification does not define:

* genetic algorithms
* mutation operators
* crossover operators
* fitness calculations
* locality calculations
* semantic mapping algorithms
* prompt engineering
* validation algorithms
* repair algorithms
* data schemas
* database collections

These topics are defined by dedicated specifications.

---

# 3. Related Specifications

Behavioral rules are defined in:

* MTES Genetic Specification
* MTES Mapping Specification
* MTES LLM Interaction Specification

Data storage is defined in:

* MTES Data Model Specification

---

# 4. Technology Stack

## 4.1 Runtime

Required:

```text
Python 3.13+
```

---

## 4.2 Database

Required:

```text
MongoDB Atlas
```

MongoDB SHALL be treated as an external managed service.

---

## 4.3 Deployment

Primary deployment target:

```text
Linux VPS
Docker Compose
```

---

# 5. Architectural Principles

## 5.1 Separation of Concerns

Modules SHALL focus on a single responsibility.

Business logic SHALL remain isolated from:

* infrastructure
* external providers
* monitoring
* deployment concerns

---

## 5.2 Provider Independence

The system SHALL support multiple providers.

Examples:

* OpenAI
* Anthropic
* Google
* local models

Provider-specific logic SHALL remain isolated.

The rest of the system SHALL communicate through adapter interfaces only.

---

## 5.3 Fault Isolation

Failure of a module SHALL NOT crash the entire system.

Examples:

* LLM outage
* Telegram outage
* embedding provider outage
* vector search outage

Failures SHALL remain localized whenever possible.

---

## 5.4 Async-First Design

The architecture SHALL use asynchronous execution.

Blocking operations SHALL be avoided.

External service calls SHALL be treated as high-latency operations.

The architecture SHALL use:

* asyncio
* asynchronous I/O
* non-blocking service calls

---

## 5.5 Workflow-Based Execution

The system SHALL use workflow-based execution.

Workflow state transitions SHALL be managed by the Workflow Coordinator.

---

# 6. High-Level Architecture

```text
Telegram Gateway
        |
        v

Publication Engine
        |
        v

Workflow Coordinator
        |
        v

MTES Core Engine

        |
        +------------------+
        |                  |

        v                  v

LLM Adapter Layer   Embedding Layer

        |                  |
        +--------+---------+
                 |
                 v

        Persistence Layer
                 |
                 v

           MongoDB Atlas


Monitoring Layer
(observes all modules)
```

---

# 7. Modules

## 7.1 Workflow Coordinator

### Purpose

Coordinate long-running workflows.

### Responsibilities

* workflow execution
* stage transitions
* workflow state management
* retries
* timeout handling
* pause and resume
* emergency stop integration

### Workflow Persistence

Workflow state SHALL be persisted through the Persistence Layer.

The Persistence Layer SHALL provide:

* workflow state storage
* workflow recovery support
* workflow resume support
* atomic workflow state transitions

Workflow state updates SHALL be atomic.

The architecture does not require distributed locking for single-instance deployment.

Workflow persistence requires workflow state records.

The corresponding storage schema is defined by the Data Model Specification.

At minimum, workflow state persistence SHALL support:

* workflow identifier
* current state
* current stage
* retry counters
* timestamps

### Recovery

The system SHALL support:

* restart after process failure
* restart after server reboot
* workflow continuation
* workflow cancellation

The Workflow Coordinator SHALL restore recoverable workflows during startup.

Recovery behavior SHALL be deterministic and idempotent whenever possible.

### Boundaries

The Workflow Coordinator SHALL NOT implement business rules.

Behavioral decisions are defined by dedicated specifications.

---

## 7.2 MTES Core Engine

### Purpose

Execute behavioral specifications.

### Responsibilities

* workflow stage execution
* specification coordination
* validation invocation
* fitness invocation
* archive invocation

### Boundaries

The Core Engine SHALL NOT communicate directly with provider APIs.

---

## 7.3 Persistence Layer

### Purpose

Provide storage abstraction.

### Responsibilities

* data access
* workflow persistence
* archive persistence
* state persistence
* recovery support

### Boundaries

MongoDB-specific logic SHALL remain isolated.

---

## 7.4 LLM Adapter Layer

### Purpose

Isolate LLM providers.

### Responsibilities

* request execution
* provider selection
* retries
* failover
* response normalization

### Boundaries

The rest of the system SHALL interact only with this layer.

---

## 7.5 Embedding Layer

### Purpose

Provide embedding services.

### Responsibilities

* embedding generation
* vector search
* embedding provider abstraction

### Boundaries

Embedding provider logic SHALL remain isolated.

---

## 7.6 Publication Engine

### Purpose

Manage publication workflows.

### Responsibilities

* publication orchestration
* publication scheduling
* publication tracking
* publication status monitoring
* engagement collection
* engagement normalization

### MVP Publication Target

Telegram SHALL be the primary publication target for MVP deployments.

Future platforms MAY be added through publication adapters.

### MVP Engagement Collection

For MVP deployments the system MAY collect:

* reaction counts
* view counts (if available)
* forward/share counts (if available)

Engagement collection is optional for MVP.

Collection mechanisms MAY include:

* Telegram API polling
* webhook events
* platform-specific adapters

Storage schemas are defined by the Data Model Specification.

### Boundaries

The Publication Engine SHALL remain platform-independent.

Platform-specific behavior SHALL remain inside publication adapters.

---

## 7.7 Telegram Gateway

### Purpose

Isolate Telegram integration.

### Responsibilities

Outbound:

* publication delivery
* notifications

Inbound:

* engagement statistics collection
* publication status updates
* operator commands
* Telegram events

### Communication Model

The Telegram Gateway SHALL support both outbound and inbound communication.

The Telegram Gateway SHALL NOT directly invoke Publication Engine business logic.

Inbound Telegram events SHALL be translated into service requests or operational signals.

### Boundaries

Telegram-specific logic SHALL remain isolated.

---

## 7.8 Monitoring Layer

### Purpose

Provide observability.

### Responsibilities

* logging
* metrics
* alerts
* diagnostics

### MTES-Specific Metrics

The architecture SHALL support collection of metrics defined by behavioral specifications.

Examples include:

* locality correlation
* repair rate
* repair cost
* prompt family distribution
* judge drift
* novelty collapse indicators
* engagement collection latency

The Monitoring Layer SHALL NOT participate in business logic.

---

## 7.9 Configuration Management

### Purpose

Manage runtime configuration.

### Responsibilities

* configuration loading
* configuration validation
* environment-specific configuration
* configuration distribution

Configuration SHALL be externalized from source code.

---

## 7.10 Global Rate Limiter

### Purpose

Coordinate request limits across external services.

### Responsibilities

* provider throttling
* backoff coordination
* rate-limit enforcement
* priority management

### Requirements

The Global Rate Limiter SHALL support:

* coroutine-safe operation
* shared rate-limit state
* provider-specific throttling

The architecture does not mandate a specific rate-limiting algorithm.

The rate limiter SHALL prevent uncontrolled request growth.

---

## 7.11 Health Check Service

### Purpose

Provide operational health information.

### Responsibilities

* readiness checks
* liveness checks
* dependency status reporting
* service diagnostics

### Health Information

The Health Check Service SHALL expose:

* application status
* database connectivity
* provider connectivity
* workflow status

Health checks SHALL be machine-readable.

---

## 7.12 Optional Cache Layer

### Purpose

Reduce expensive external requests.

### Responsibilities

* embedding cache
* candidate cache
* computation cache

The Cache Layer MAY be omitted during initial deployment.

The architecture SHALL remain fully functional without it.

If no cache exists, fresh computation SHALL be performed through the appropriate service layer.

---

## 7.13 Maintenance Worker

### Purpose

Execute periodic operational tasks.

### Responsibilities

* archive maintenance
* index maintenance
* cleanup operations
* health verification
* engagement synchronization

The Maintenance Worker SHALL NOT implement business logic.

The Maintenance Worker MAY run as:

* a dedicated process
* a scheduled coroutine
* a scheduled container task

---

# 8. Concurrency Model

## 8.1 Worker Model

Workers are logical execution roles.

Workers SHALL normally be implemented as asyncio coroutines.

Workers are not required to be:

* operating-system processes
* threads
* broker consumers

Workers MAY run inside a single process.

---

## 8.2 Bounded Concurrency

Bounded concurrency SHALL be enforced through:

```text
asyncio.Semaphore
```

or an equivalent mechanism.

The architecture SHALL prevent:

* unbounded task creation
* uncontrolled memory growth
* runaway provider utilization

---

# 9. System Protection Mechanisms

## 9.1 Quality Gates

The architecture SHALL support:

* warning states
* degraded mode
* workflow suspension
* emergency stop

Monitoring systems MAY emit quality-gate signals.

The Workflow Coordinator SHALL enforce resulting workflow transitions.

Quality-gate definitions are specified elsewhere.

---

## 9.2 Emergency Stop

The architecture SHALL support emergency shutdown.

Possible triggers:

* operator request
* severe infrastructure failure
* resource exhaustion
* critical dependency failure

Emergency stop SHALL:

* prevent new workflows
* preserve current state
* allow safe recovery

Recovery SHALL require explicit operator action.

---

# 10. Module Interaction Contracts

## 10.1 Allowed Dependencies

```text
Workflow Coordinator
    -> Core Engine
    -> Persistence Layer

Core Engine
    -> LLM Adapter Layer
    -> Embedding Layer
    -> Persistence Layer

Publication Engine
    -> Telegram Gateway
    -> Persistence Layer

Telegram Gateway
    -> Workflow Coordinator
    -> Monitoring Layer

Monitoring Layer
    -> observes all modules
```

---

## 10.2 Communication Rules

Modules SHALL communicate through explicit service interfaces.

Direct access to internal module state is forbidden.

Modules SHALL NOT depend on implementation details of other modules.

---

# 11. Failure Handling

## 11.1 LLM Failures

Examples:

* timeout
* provider outage
* invalid response
* rate limit

Allowed responses:

* retry
* provider failover
* workflow pause
* workflow failure

---

## 11.2 Embedding Failures

Allowed responses:

* retry
* provider failover
* workflow suspension

---

## 11.3 Telegram Failures

Allowed responses:

* retry
* delayed publication
* engagement sync retry

---

## 11.4 Database Failures

Allowed responses:

* retry
* workflow pause
* emergency stop escalation

---

# 12. Observability

## 12.1 Logging

The architecture SHALL provide structured logging.

Logs SHALL support:

* diagnostics
* debugging
* auditing

---

## 12.2 Metrics

The architecture SHALL provide metrics for:

* workflow execution
* provider performance
* publication activity
* engagement collection
* system resources

Metrics SHALL be machine-readable.

The architecture does not mandate a specific monitoring stack.

Examples:

* Prometheus + Grafana
* OpenTelemetry
* custom monitoring solutions

---

## 12.3 Alerts

Critical failures SHALL generate alerts.

Examples:

* provider outage
* database outage
* repeated workflow failures
* engagement collection failures

---

# 13. Security

## 13.1 Secrets

Secrets SHALL NOT be stored in source code.

Examples:

* API keys
* Telegram tokens
* database credentials

Secrets SHALL be injected through:

* environment variables
* secret management systems

---

## 13.2 Permissions

Services SHALL receive only required permissions.

---

## 13.3 Network Security

External communication SHALL use encrypted transport whenever supported.

---

## 13.4 Operator Commands

Operator commands received through Telegram SHALL be authenticated.

Authentication MAY include:

* allow-listed Telegram user IDs
* allow-listed chat IDs
* signed command verification

Authentication configuration SHALL remain external to source code.

---

# 14. Deployment Architecture

## 14.1 VPS Deployment

```text
Linux VPS

    Docker Compose

        +-- MTES Core
        +-- Publication Worker
        +-- Maintenance Worker
        +-- Optional Monitoring Stack
```

MongoDB Atlas SHALL remain external.

---

## 14.2 Future Scaling

Future deployments MAY introduce:

* Kubernetes
* multiple workers
* dedicated embedding services
* dedicated publication services

Workflow Coordinator is designed primarily for single-instance deployment.

Multi-instance workflow coordination MAY require additional locking mechanisms.

No major architectural redesign SHALL be required.

---

# 15. Extensibility

New providers SHALL be added through adapter implementations.

Examples:

* new LLM provider
* new embedding provider
* new publication platform

Existing modules SHALL require minimal modification.

---

# 16. Compliance Requirements

An implementation is compliant if it:

* follows module boundaries defined here
* preserves provider independence
* preserves fault isolation
* supports asynchronous execution
* supports workflow coordination
* supports observability requirements
* supports security requirements
* supports VPS deployment using Docker

---

# 17. Final Note

The architecture prioritizes:

* simplicity
* reproducibility
* operational stability
* provider independence
* VPS deployment practicality

The architecture intentionally avoids external message brokers and distributed infrastructure requirements in order to minimize operational complexity while preserving reliability and recoverability.
