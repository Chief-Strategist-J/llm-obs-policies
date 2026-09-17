# API-First & Pure Data-Driven Architecture Specification
*(Language-Agnostic Workspace & Sub-Package Architecture Reference for Go, Python, Rust, Java, C++, Node.js/TypeScript, and C#)*

---

### Core Architectural Principles & Hard Rules

1. **Language-Agnostic Principle**: This architecture specification is strictly **language-agnostic**. The folder hierarchy, contract isolation, database migration rules, and data-driven engine boundaries apply identically regardless of whether the service is implemented in Go, Python, Rust, Java, C++, Node.js/TypeScript, or C#.
2. **Sub-Package Isolation Guardrail**: Every sub-package is fully isolated. No sub-package imports source code directly from another sub-package, even within the same language runtime. All cross-package runtime communication MUST execute through a versioned API contract and a generated client SDK.
3. **DRY Component Re-use Rule**: Never duplicate infrastructure boilerplate, broker setups, connection pools, serializers, or middleware execution pipelines. Every feature and service MUST re-use pre-existing shared components under `src/infra/messaging/` and `src/shared/`.
4. **Mandatory Directory Hierarchy `.gitkeep`**: When scaffolding or generating directory structures, include a `.gitkeep` file in every folder to preserve exact directory hierarchy across Git commits.
5. **Contract-First Constraint**: No implementation source code inside `src/` may be created, scaffolded, or merged until the corresponding API contract specification file (`contracts/openapi/`, `contracts/graphql/`, `contracts/proto/`, `contracts/asyncapi/`) is merged in a dedicated contract-only PR.
   - **Single Contract Selection**: Each feature endpoint or flow selects exactly ONE primary contract format (REST OpenAPI, GraphQL SDL, gRPC Proto, or AsyncAPI + JSON Schema). Speculative generation of unused contract formats (e.g. generating `.proto` or `.graphql` when building a REST API) is strictly prohibited.
   - **Automated Client & Stub Codegen**: Hand-writing request/response types or server interface stubs is forbidden. The build toolchain or code generator (`generate.sh` / protoc / openapi-generator) MUST automatically generate server interfaces, request validation types, and client SDKs from the authoritative contract specification.
   - **Immutability & Deprecation Lifecycle**: Merged contract versions (`v1.yaml`, `v1.graphql`) are strictly immutable. Any breaking modification requires a new version (`v2.yaml`) running in parallel with deprecation headers (`Deprecation`, `Sunset`) for a minimum sunset window of 6 months.
6. **Data-Driven Logic & The 5 Immutable Feature Data Pillars**: Core engine mechanics (adapters, pipeline decorators, rules evaluator, workflow runner) are written ONCE. Every feature inside `src/features/{feature-name}/` is defined purely as declarative DATA artifacts conforming to five standardized pillars:
   1. **Entity Schema Contract (`schema/`)**: Runtime field definitions, data types, validation constraints, default values, and bidirectional API/DB transformation mappers (`fromApi` / `toApi`).
   2. **Flow-by-Flow Parameterized Queries (`queries/`)**: Every database operation MUST be explicitly declared inside `features/{feature}/queries/{feature}.queries.[ext|sql]` as a named, flow-grouped parameterized query structure (`FLOW_SIGN_IN`, `FLOW_VERIFY_SESSION`, `FLOW_CREATE_API_KEY`). Raw inline SQL string construction inside services or handlers is strictly prohibited.
   3. **Rules as Data (`rules/`)**: Business logic decision trees declared as structured rule sets with priority weights, decision categories, deny-override conflict resolution, and async condition checkers (`evaluate.ts` / `rules.json`).
   4. **State Machines as Data (`machines/`)**: Multi-state lifecycle flows declared as state transition graphs with guard conditions, valid state triggers, and event side-effects evaluated by generic state machine actors.
   5. **Workflows as Data (`workflows/`)**: Multi-step DAG automation flows declared as step arrays (e.g. `evaluateRules`, `callEntity`, `callAI`, `humanApproval`) executed by the generic, OpenTelemetry-traced workflow engine.
7. **Declarative Anti-Corruption Layer (ACL)**: Imperative payload translation code (copying and renaming object properties line-by-line) is prohibited. Payload translation between external contract schemas and internal entity models MUST be handled declaratively using standardized data mapping operations (`rename`, `pick`, `omit`, `coerce`, `default`).
8. **Resilience Decorator Composition**: Infrastructure adapters MUST be wrapped using standardized pipeline decorator composition (`withTracing(withCircuitBreaker(withCache(withRetry(adapter))))`) at the call site, eliminating per-feature error handling, caching, or retry boilerplate.

---

### Polyglot Language Workspace Layout

For repositories hosting multi-language workspaces, projects are organized by language with zero-runtime-dependency shared libraries:

```
packages/
├── python/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── python-shared/
│       - pure types and pure utils only, zero business logic & no IO
│
├── rust/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── rust-shared/
│
├── go/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── go-shared/
│
├── node/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── node-shared/
│
├── java/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── java-shared/
│
└── apis/
    - API Gateway package - Stage 2 and above
```

#### `{lang}-shared/` Boundary Rules
- `{lang}-shared/` contains zero runtime side-effects, zero business logic, and zero IO calls.
- Exports only type definitions (`types/`) and pure utility functions (`utils/`) exported via its primary index file.
- If a utility requires network, disk, database IO, or state mutation, it belongs in a sub-package infrastructure adapter—never in `{lang}-shared/`.
- Sub-packages importing from `{lang}-shared/` must do so through its clean index interface.

---

### Contract Selection Matrix

| Scenario | Contract Selection | Target Directory |
|---|---|---|
| **Client-facing query or mutation** | GraphQL SDL | `shared/contracts/graphql/` or `contracts/graphql/` |
| **Service-to-service synchronous call** | REST OpenAPI OR gRPC Proto (Select ONE) | `contracts/openapi/` or `contracts/proto/` |
| **Async or event-driven streaming** | AsyncAPI + JSON Schema | `contracts/asyncapi/` & `shared/contracts/json-schema/` |
| **Internal only, no cross-package boundary** | Local feature types | `src/features/{feature}/types/` |

---

### Complete Unified API-Driven Workspace & Package Directory Tree

Every service/sub-package in every language enforces this complete, pure API-driven layout logically structured from workspace contract specifications down to implementation and verification manifests:

```

{package-name}/
│ - 2. Sub-Package Root Directory
│
├── contracts/
│   - Authoritative contract specs owned by this package
│   ├── .gitkeep
│   ├── openapi/
│   │   - OpenAPI REST specs & changelog
│   │   ├── .gitkeep
│   │   ├── v1.yaml
│   │   ├── v2.yaml
│   │   │   - Created only when breaking changes force major version
│   │   └── changelog.md
│   ├── graphql/
│   │   - Included only when GraphQL is selected
│   │   ├── .gitkeep
│   │   ├── v1.graphql
│   │   └── changelog.md
│   ├── proto/
│   │   - Included only when gRPC is selected
│   │   ├── .gitkeep
│   │   └── v1/
│   ├── asyncapi/
│   │   - Included only when async event streams exist
│   │   ├── .gitkeep
│   │   └── v1.yaml
│   ├── json-schema/
│   │   - Event payload validation schemas
│   │   ├── .gitkeep
│   │   └── {event}/
│   │       └── v1.json
│   └── changelog.md
│       - Package contract revision history
│
├── config/
│   - Centralized package environment & runtime configuration management
│   ├── .gitkeep
│   ├── env.schema
│   │   - Environment variable schema definition & runtime validation
│   ├── default.yaml
│   │   - Baseline default configuration values
│   ├── development.yaml
│   │   - Local development configuration overrides
│   ├── production.yaml
│   │   - Production environment configuration overrides
│   ├── test.yaml
│   │   - Automated test environment configuration overrides
│   └── feature-flags.yaml
│       - Service-scoped feature flags & fallback toggles
│
├── database/
│   - Language-agnostic Database, Partitioning & Persistence Management - The Persistence Heart
│   ├── .gitkeep
│   ├── migrations/
│   │   - Versioned SQL DDL migrations with mandatory rollback pairs
│   │   ├── .gitkeep
│   │   ├── 0001_initial_schema.sql
│   │   │   - Upward schema DDL migration script - NNNN_description.sql
│   │   └── 0001_initial_schema.rollback.sql
│   │       - Matching rollback DDL script - NNNN_description.rollback.sql
│   ├── rls/
│   │   - Row Level Security & Multi-Tenant Data Isolation Policies
│   │   ├── .gitkeep
│   │   └── 0001_tenant_isolation_rls.sql
│   │       - PostgreSQL / AlloyDB RLS policies for multi-tenant data safety
│   ├── indexes/
│   │   - Foreign Key & Query Performance Optimization Index Specs
│   │   ├── .gitkeep
│   │   └── 0001_performance_indexes.sql
│   │       - Foreign keys, GIN/B-tree indexes, and composite lookup optimizations
│   ├── partitioning/
│   │   - Data Partitioning Specs - Range-Based 8.1, Hash-Based 8.2, Directory-Based 8.3
│   │   ├── .gitkeep
│   │   ├── range_partitioning.yaml
│   │   │   - Range boundaries split points & auto-split threshold specs
│   │   ├── hash_partitioning.yaml
│   │   │   - Consistent hash ring positions & virtual node count specs
│   │   └── directory_partitioning.json
│   │       - Explicit directory lookup table & key-to-partition mapping entries
│   ├── storage_engine/
│   │   - Storage Engine Specs - LSM 8.7, Tiered 8.8, Hot/Cold 8.9, Polyglot 8.10
│   │   ├── .gitkeep
│   │   ├── lsm_storage.yaml
│   │   │   - Memtable flush thresholds, SSTable levels & compaction rules
│   │   ├── tiered_storage.yaml
│   │   │   - Access metadata idle thresholds & hot/warm/cold migration policies
│   │   ├── hot_cold_archiving.sql
│   │   │   - Bimodal hot-to-cold store scheduled archiving purge sweep
│   │   └── polyglot_dispatch.json
│   │       - Workload type to specialized store mappings - relational, search, vector, KV
│   ├── replication/
│   │   - Replication Topologies - Read Replica 8.4, Designated Writer 8.5, Multi-Master 8.6, Leader-Follower
│   │   ├── .gitkeep
│   │   ├── topology_spec.yaml
│   │   │   - Declarative replication topology - Leader-Follower, Active-Active, Active-Passive
│   │   └── chain_replication.yaml
│   │       - Chain replication head-to-tail propagation spec
│   ├── consensus/
│   │   - State Machine Replication & Raft Consensus Specs
│   │   ├── .gitkeep
│   │   ├── raft_consensus.yaml
│   │   │   - Raft election timeout, term tracking & log entry commit spec
│   │   └── wal_shipping.yaml
│   │       - Write-Ahead Log offset shipping & segment replay spec
│   ├── quorums/
│   │   - Dynamo-Style Read/Write Quorums & ACK Strategy Specs
│   │   ├── .gitkeep
│   │   ├── quorum_config.yaml
│   │   │   - Quorum rules - strict W+R>N, sloppy write/read light
│   │   └── ack_policy.yaml
│   │       - ACK strategy specs - Synchronous, Asynchronous, Semi-Synchronous k-ack
│   ├── cdc/
│   │   - Change Data Capture Pipeline Specs
│   │   ├── .gitkeep
│   │   ├── cdc_publisher_spec.json
│   │   │   - WAL tailer stream & Kafka event publisher spec
│   │   └── cdc_sink_spec.json
│   │       - Sink applier & offset checkpoint store spec
│   ├── sharding/
│   │   - Sharded Replication & Consistent Hashing Ring Maps
│   │   ├── .gitkeep
│   │   └── shard_hash_ring.yaml
│   │       - Consistent hash ring mapping & shard key routing rules
│   ├── crdts/
│   │   - Conflict-Free Replicated Data Types & Hybrid Clock Specs
│   │   ├── .gitkeep
│   │   ├── crdt_definitions.yaml
│   │   │   - GCounter, ORSet state-based CRDT merge schemas
│   │   └── hybrid_clock.yaml
│   │       - Hybrid logical clock tick & LWW conflict resolution spec
│   ├── anti_entropy/
│   │   - Background Anti-Entropy Sync & Merkle Tree Diff Jobs
│   │   ├── .gitkeep
│   │   └── merkle_tree_sync.sql
│   │       - Merkle tree hash diff sweep & anti-entropy repair job
│   ├── fencing/
│   │   - Monotonic Epoch Fencing & Standby Promotion Specs
│   │   ├── .gitkeep
│   │   └── fencing_epoch_failover.sql
│   │       - Fenced storage write & standby promotion failover script
│   ├── retention/
│   │   - Automated Backup Retention, Compliance & Soft-Delete Purge Jobs
│   │   ├── .gitkeep
│   │   └── soft_delete_30day_purge.sql
│   │       - Automated 30-day backup retention & soft-delete purge script
│   ├── seeds/
│   │   - Environment-Specific Database Seed Fixtures
│   │   ├── .gitkeep
│   │   ├── dev.seed.sql
│   │   │   - Local development environment fixtures
│   │   └── test.seed.sql
│   │       - Automated integration & E2E test suite fixtures
│   └── schema.lock
│       - Immutable cryptographic lock file of applied DB migrations
│
├── messaging/
│   - Language-agnostic Messaging & Event Topic Management - The Streaming Heart
│   ├── .gitkeep
│   ├── topics/
│   │   - Versioned Kafka Topic Provisioning Specs & Rollback Pairs
│   │   ├── .gitkeep
│   │   ├── 0001_create_user_events.json
│   │   │   - Topic provisioning spec - partitions, retention, min.insync.replicas
│   │   └── 0001_create_user_events.rollback.json
│   │       - Topic de-provisioning & rollback spec
│   ├── schema-registry/
│   │   - Schema Registry Definitions - Avro, Protobuf, JSON Schema
│   │   ├── .gitkeep
│   │   └── user_events.v1.json
│   ├── dlq/
│   │   - Dead Letter Queue Retry & Policy Specs
│   │   ├── .gitkeep
│   │   └── dlq_policy.yaml
│   ├── subscriptions/
│   │   - Consumer Group Subscriptions & Topic Mapping Specs
│   │   ├── .gitkeep
│   │   └── consumer_groups.yaml
│   └── topics.lock
│       - Immutable cryptographic lock file of provisioned topics
│
├── deploy/
│   - Infrastructure deployment specifications
│   ├── .gitkeep
│   ├── k8s/
│   │   - Kubernetes manifests - Deployment, Service, HPA, ConfigMap
│   └── helm/
│       - Helm deployment values charts
│
├── src/
│   - 3. Application Implementation Source Code
│   ├── api/
│   │   - Delivery entry points only
│   │   ├── .gitkeep
│   │   ├── rest/v1/
│   │   │   - REST handlers & declarative route rules
│   │   │   ├── .gitkeep
│   │   │   ├── router
│   │   │   ├── route.rules
│   │   │   └── handlers/
│   │   ├── graphql/v1/
│   │   │   - GraphQL resolvers & dataloaders
│   │   │   ├── .gitkeep
│   │   │   ├── schema
│   │   │   ├── resolvers/
│   │   │   └── dataloaders/
│   │   ├── grpc/v1/
│   │   │   - gRPC server stubs & handlers
│   │   │   ├── .gitkeep
│   │   │   ├── server
│   │   │   └── handlers/
│   │   └── events/
│   │       - Event delivery entry points
│   │       ├── .gitkeep
│   │       ├── consumers/
│   │       └── publishers/
│   │
│   ├── features/
│   │   - Isolated business domain feature modules
│   │   ├── .gitkeep
│   │   └── {feature-name}/
│   │       ├── .gitkeep
│   │       ├── index
│   │       │   - Public interface export for this feature
│   │       ├── context.md
│   │       │   - Business domain context, dependencies & ADR link
│   │       ├── schema
│   │       │   - Entity schema contract - fields, validate, fromApi, toApi
│   │       ├── queries/
│   │       │   - MANDATORY: Flow-by-Flow Database Queries
│   │       │   ├── .gitkeep
│   │       │   └── {feature}.queries.[ext|sql]
│   │       │       - Named, flow-grouped parameterized queries
│   │       ├── rules
│   │       │   - Business rules AS DATA - priority, category, async conditions
│   │       ├── machines
│   │       │   - State machine definitions AS DATA - State DAG / DSL
│   │       ├── workflows
│   │       │   - Step automation DAG definitions AS DATA
│   │       ├── service
│   │       │   - Pure domain service logic - no direct HTTP/IO
│   │       ├── repository
│   │       │   - Data access via queries/ and port interface
│   │       ├── types
│   │       │   - Feature-local domain types
│   │       └── tests/
│   │           - Feature-scoped unit & integration tests
│   │           ├── .gitkeep
│   │           ├── unit/
│   │           ├── integration/
│   │           └── contract/
│   │
│   ├── infra/
│   │   - Infrastructure adapters & generated client SDKs
│   │   ├── .gitkeep
│   │   ├── config/
│   │   │   - Strongly-typed configuration loader & secrets resolver engine
│   │   │   ├── .gitkeep
│   │   │   ├── config.loader
│   │   │   │   - Environment validator & vault secret loader
│   │   │   └── env.schema
│   │   │       - Strongly-typed environment schema binding
│   │   ├── database/
│   │   │   - Centralized Database infrastructure & driver abstraction
│   │   │   ├── .gitkeep
│   │   │   ├── pool/
│   │   │   │   - Connection pools, health checks & read/write split endpoints
│   │   │   ├── factory/
│   │   │   │   - Client connection factories
│   │   │   ├── transaction/
│   │   │   │   - Transaction manager & unit-of-work pipeline engine
│   │   │   ├── executor/
│   │   │   │   - Parameterized query execution & statement runner
│   │   │   ├── middleware/
│   │   │   │   - Query & mutation execution pipeline engines
│   │   │   ├── migrations/
│   │   │   │   - DDL schema migration runner & lock file validator
│   │   │   ├── tracing/
│   │   │   │   - OpenTelemetry DB span lifecycle & SQL query sanitizer
│   │   │   └── adapters/
│   │   │       - Database vendor driver adapters - Postgres, AlloyDB, DynamoDB, Redis
│   │   ├── messaging/
│   │   │   - Centralized Kafka infrastructure & broker abstraction
│   │   │   ├── .gitkeep
│   │   │   ├── broker/
│   │   │   │   - Connection pools, endpoints & health checks
│   │   │   ├── factory/
│   │   │   │   - Producer & consumer connection factories
│   │   │   ├── producers/
│   │   │   │   - Typed Kafka event producers
│   │   │   ├── consumers/
│   │   │   │   - Consumer group management & event dispatchers
│   │   │   ├── middleware/
│   │   │   │   - Producer & consumer pipeline engines - ProduceCtx/ConsumeCtx
│   │   │   ├── topics/
│   │   │   │   - Topic provisioner & schema registry bindings
│   │   │   ├── migrations/
│   │   │   │   - Kafka topic schema migration runner
│   │   │   ├── tracing/
│   │   │   │   - W3C trace context propagation & span lifecycle engine
│   │   │   └── cqrs/
│   │   │       - Command handlers, projection stores & query selectors
│   │   ├── clients/
│   │   │   - Generated client SDKs only - NEVER hand-written
│   │   │   ├── .gitkeep
│   │   │   └── {upstream-service}/
│   │   │       └── v1/
│   │   └── observability/
│   │       - Observability, Diagnostics, Continuous Profiling & Failure Diagnosis Runtime Engine
│   │       ├── .gitkeep
│   │       ├── tracing/
│   │       │   - OpenTelemetry SDK setup, W3C trace context, deepest-leaf-error walker & tail-based sampling
│   │       ├── clocks/
│   │       │   - Lamport logical clocks, vector clocks & hybrid logical clocks (HLC)
│   │       ├── profiling/
│   │       │   - Continuous profiling (Parca/Pyroscope) & flame graph differential engine
│   │       ├── race_detection/
│   │       │   - Happens-before vector clock race detection engine
│   │       ├── deadlock/
│   │       │   - Wait-for graph & Chandy-Misra-Haas distributed deadlock engine
│   │       ├── heap_analysis/
│   │       │   - Heap diffing, core dump inspector & GC pause correlator
│   │       ├── ebpf/
│   │       │   - eBPF kernel syscall tracing & latency histogram probes
│   │       ├── wire_analysis/
│   │       │   - Packet capture, PCAP decoder & TCP retransmission detector
│   │       ├── vector_inspection/
│   │       │   - Version-vector causality inspector & sibling conflict explainer
│   │       ├── divergence_audit/
│   │       │   - Anti-entropy read-repair replica divergence auditor
│   │       ├── idempotency_audit/
│   │       │   - Idempotency key dedupe store auditor & double-processing failure classifier
│   │       ├── transition_log/
│   │       │   - Explicit state machine transition logger & lifecycle history reconstructor
│   │       ├── snapshots/
│   │       │   - Chandy-Lamport distributed snapshot coordinator
│   │       ├── replay/
│   │       │   - Event-sourced replay-to-point & deterministic incident replayer
│   │       ├── wal_miner/
│   │       │   - Database WAL/binlog tailing miner & app log cross-checker
│   │       ├── shadow_traffic/
│   │       │   - Shadow traffic mirror proxy, response comparator & differential regression detector
│   │       ├── circuit_breaker_history/
│   │       │   - Circuit breaker state transition recorder & root-cause cascade classifier
│   │       ├── saturation_analysis/
│   │       │   - Little's Law L = λ × W queueing theory saturation point estimator
│   │       ├── analytics/
│   │       │   - BubbleUp-style distributional attribute divergence engine
│   │       └── topology/
│   │           - Service dependency graph builder & RED metrics overlay
│   │
│   └── shared/
│       - Package-internal shared repeating utilities & helpers
│       ├── .gitkeep
│       ├── utils/
│       │   - Pure cross-feature utility functions - formatting, date, string helpers
│       ├── constants/
│       │   - Shared package constants & system endpoint definitions
│       ├── errors/
│       │   - Standardized error classes & response envelope wrappers
│       └── types/
│           - Common package-wide utility types
│
├── tests/
│   - 4. Global Package Test Suite
│   ├── .gitkeep
│   ├── unit/
│   │   - Domain unit tests
│   ├── integration/
│   │   - Integration tests against containerized infrastructure
│   ├── contract/
│   │   - OpenAPI / AsyncAPI / gRPC contract compliance tests
│   ├── performance/
│   │   - K6 / Locust load, stress, and spike test scripts
│   │   ├── .gitkeep
│   │   ├── scenarios/
│   │   └── thresholds.json
│   │       - Latency SLAs - p95 < 100ms, error rate < 0.01%
│   ├── e2e/
│   │   - End-to-end user journey API workflows
│   └── diagnostics/
│       - Failure Diagnosis, Formal Verification, Boundary Replay & Fault Injection Workloads
│       ├── .gitkeep
│       ├── jepsen/
│       │   - Jepsen-style fault injection workloads & Knossos linearizability verification
│       ├── tla_plus/
│       │   - TLA+ formal state machine specifications & TLC model checker runners
│       ├── byzantine/
│       │   - Byzantine response corruption proxies & cross-validation test suites
│       ├── bisection/
│       │   - Automated git bisect reproducer scripts & regression verification
│       ├── chaos/
│       │   - Chaos engineering fault injection experiments - latency, drop, node kill
│       └── vcr_proxy/
│           - Boundary network record/replay VCR proxy harness
│
├── scripts/
│   - Automation & Build Scripts
│   ├── run.sh
│   ├── migrate.sh
│   ├── test.sh
│   └── generate.sh
│       - Client SDK & stub code generation script
│
├── Dockerfile
│   - Multi-stage production container build
├── Dockerfile.dev
│   - Development container with hot-reload & debug symbols
├── docker-compose.yml
│   - Isolated test & runtime infrastructure - Postgres, Redis, Kafka
├── .dockerignore
│   - Container build exclusion patterns
├── .env.example
├── .package-meta.yaml
└── .port-registry
```

---

### Language Tooling & Ecosystem Standards

Every sub-package enforces language-native quality, type safety, linting, and codegen standards:

#### Python
* **Package Manager**: `pyproject.toml` using `src/` layout per sub-package.
* **Linter & Formatter**: `ruff --select ALL`, zero warnings allowed.
* **Type System**: `mypy --strict`, zero type errors.
* **Security & Auditing**: `bandit` and `safety check` in CI pipeline.
* **Import Guardrail**: `ruff` imports rule banning cross-package imports.
* **Test Runner**: `pytest` with `pytest-cov` (minimum 80% coverage threshold).
* **Client Codegen**: `openapi-python-client` into `src/infra/clients/`.
* **GraphQL & gRPC**: `ariadne-codegen` from SDL; `grpcio-tools` with `buf generate`.
* **Tracing & ORM**: `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy`.

#### Rust
* **Package Manager**: Workspace `Cargo.toml`. Workspace members never depend directly on each other.
* **Linter & Formatter**: `clippy --deny warnings`, zero warnings allowed.
* **Type System**: Strict safe Rust (`#![deny(unsafe_code)]` unless explicitly justified).
* **Security & Auditing**: `cargo audit` and `cargo deny`.
* **Test Runner**: `cargo test` with `cargo tarpaulin` (minimum 80% coverage).
* **Client Codegen**: `openapi-generator` into `src/infra/clients/`.
* **GraphQL & gRPC**: `async-graphql` (schema-first SDL); `tonic` with `buf generate`.
* **Tracing & DB**: `opentelemetry`, `tracing-opentelemetry`, `sqlx` migrations.

#### Go
* **Package Manager**: Independent `go.mod` per sub-package. `replace` directives strictly forbidden in `main`.
* **Linter & Formatter**: `golangci-lint` with strict configuration, zero warnings.
* **Type System & Security**: `go vet`, `staticcheck`, `govulncheck`, and `gosec`.
* **Import Guardrail**: `depguard` blocking cross-module imports.
* **Test Runner**: `go test ./...` with minimum 80% coverage.
* **Client Codegen**: `oapi-codegen` into `src/infra/clients/`.
* **GraphQL & gRPC**: `gqlgen` (schema-first SDL); `connectrpc` with `buf generate`.
* **Tracing & DB**: `go.opentelemetry.io/otel`, `golang-migrate` with raw SQL.

#### Node.js / TypeScript
* **Package Manager**: Independent `package.json` per sub-package. No runtime cross-package imports.
* **Linter & Formatter**: `eslint --max-warnings 0` and `prettier`.
* **Type System**: `tsc --strict`, `noImplicitAny`, no `ts-ignore` without documented justification.
* **Security & Auditing**: `npm audit --audit-level=high`.
* **Import Guardrail**: `eslint-plugin-import` / `no-restricted-imports` banning cross-package imports.
* **Test Runner**: `vitest` (or `jest`), minimum 80% coverage.
* **Client Codegen**: `openapi-typescript-codegen` or `openapi-fetch` into `src/infra/clients/`.
* **GraphQL & gRPC**: `@graphql-codegen/cli` from SDL; `@connectrpc/connect` with `buf generate`.
* **Tracing & DB**: `@opentelemetry/sdk-node`, `db-migrate` or raw SQL runner.

#### Java
* **Package Manager**: Independent Maven module or Gradle subproject per sub-package.
* **Linter & Formatter**: `checkstyle`, `pmd`, `spotbugs` (zero violations).
* **Security & Architecture**: `ArchUnit` tests blocking cross-module type references in CI.
* **Test Runner**: `JUnit 5` with `JaCoCo` (minimum 80% coverage).
* **Client Codegen**: `openapi-generator-maven-plugin` into `infra/clients/`.
* **Tracing & DB**: `opentelemetry-java-instrumentation` agent, `flyway` SQL migrations.

---

### Centralized Configuration Management Guidelines

1. **Package Configuration Hierarchy (`config/`)**: Every package manages its runtime configuration using standard environment manifests (`default.yaml`, `development.yaml`, `production.yaml`, `test.yaml`) and strict environment variable schemas (`env.schema`).
2. **Strongly-Typed Config Engine (`src/infra/config/`)**:
   - Environment variables and configuration files MUST be parsed and validated against `env.schema` at startup.
   - Raw `process.env`, `os.environ`, or unvalidated config lookups inside domain features or HTTP handlers are strictly prohibited.
   - Secrets resolution (Vault, AWS Secrets Manager, Kubernetes secrets) MUST be handled through `src/infra/config/config.loader` prior to service boot.
3. **Workspace Configuration Boundary (`shared/config/`)**:
   - Workspace-wide environment variable schemas (`shared/config/schema/`) enforce consistent naming (`DATABASE_URL`, `REDIS_URL`, `KAFKA_BROKERS`, `OTEL_EXPORTER_OTLP_ENDPOINT`) across all services.
   - Centralized feature flags and rollout policies (`shared/config/feature-flags/`) ensure multi-tenant feature toggles and fallback behaviors are managed consistently across polyglot packages.

---

### Centralized Database Architecture Guidelines

1. **Package Database Specification (`database/`)**: Declarative database schemas, SQL DDL migrations (`migrations/`), RLS policies (`rls/`), optimization indexes (`indexes/`), data partitioning rules (`partitioning/`), storage engine settings (`storage_engine/`), replication topologies (`replication/`), consensus specifications (`consensus/`), quorums (`quorums/`), CDC specs (`cdc/`), sharding ring maps (`sharding/`), CRDT definitions (`crdts/`), anti-entropy jobs (`anti_entropy/`), fencing scripts (`fencing/`), backup retention policies (`retention/`), and seed fixtures (`seeds/`) are strictly owned by `database/` at the sub-package root level.
2. **Centralized Database Infra (`src/infra/database/`)**: Connection pooling, read/write splitting (`pool/`), connection factories (`factory/`), transaction runner (`transaction/`), parameterized query executors (`executor/`), DB middleware pipelines (`middleware/`), DDL schema migration runner (`migrations/`), and vendor driver adapters (`adapters/`) are strictly maintained in `src/infra/database/`. Never open raw DB connections or construct ad-hoc SQL driver instances inside domain features or HTTP handlers.
3. **Database Schema Locking & Migration Integrity (`database/schema.lock`)**: Applied migrations update `database/schema.lock`. Migration runners in `src/infra/database/migrations/` verify checksums against `schema.lock` before executing DDL migrations.

#### Database & Infrastructure Coordination Pipeline

The coordination between declarative specifications (`database/`), executable infrastructure runtime (`src/infra/database/`), domain query definitions (`src/features/{feature}/queries/`), and domain services (`src/features/{feature}/service/`) operates across four distinct execution phases:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DECLARATIVE SPECIFICATIONS (Package Root: database/)                                 │
│    - DDL SQL Migrations (migrations/) & Checksum Lock File (schema.lock)                │
│    - RLS Policies (rls/), Indexes (indexes/), Partitioning (partitioning/)              │
│    - Storage Engine (storage_engine/), Replication Topologies (replication/)            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼ Read & Executed At Boot / CI-CD
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. EXECUTABLE INFRASTRUCTURE RUNTIME ENGINE (src/infra/database/)                       │
│    - Migration Runner (migrations/) validates checksums & applies DDL SQL              │
│    - Connection Pool (pool/) initializes Primary & Read Replica connection pools        │
│    - Query Executor (executor/) receives SQL calls & runs through middleware pipeline    │
│    - OTEL Tracing (tracing/) & Vendor Driver Adapters (adapters/) execute queries        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                           ▲
                                           │ Dispatched via Injected Repository Ports
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. FEATURE DOMAIN LAYER (src/features/{feature-name}/)                                  │
│    - queries/{feature}.queries.sql holds flow-grouped parameterized queries            │
│    - repository/ connects queries to generic DB ports                                   │
│    - service/ executes pure business logic with ZERO database driver imports             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Phase 1 — Schema Migration & Verification (CI/CD & Startup)**:
   * `src/infra/database/migrations/` reads versioned DDL scripts from `database/migrations/` (e.g. `0001_initial_schema.sql`).
   * Verifies SHA256 checksums against `database/schema.lock` to ensure zero out-of-order or altered migration tampering.
   * Acquires a DDL lock and executes the migration against the target database cluster.

2. **Phase 2 — Connection Bootstrapping & Pool Management (Service Startup)**:
   * Strongly-typed config loader (`src/infra/config/`) resolves environment secrets (`DATABASE_URL`).
   * `src/infra/database/pool/` parses topology specs (`database/replication/topology_spec.yaml`) and read/write quorum rules (`database/quorums/quorum_config.yaml`).
   * Initializes Primary Write Pools and Read Replica Pools with OpenTelemetry tracing hooks attached (`src/infra/database/tracing/`).

3. **Phase 3 — Flow-by-Flow Query Dispatch (Runtime Execution)**:
   * Client HTTP request hits router -> Feature Service (`src/features/{feature}/service/`) executes business flow.
   * Service invokes Repository (`src/features/{feature}/repository/`), which selects named parameterized query string from `src/features/{feature}/queries/{feature}.queries.sql`.
   * Repository delegates query execution to `src/infra/database/executor/`.

4. **Phase 4 — Pipeline Decoration & Driver Execution (Infra Engine)**:
   * `src/infra/database/executor/` passes query through middleware (`src/infra/database/middleware/`):
     - Starts OpenTelemetry trace span & sanitizes SQL.
     - Applies resilience wrappers (`withRetry`, `withCircuitBreaker`, `withCache`).
     - Evaluates read replica version pins (`replica.applied_version >= client_last_write_version`) to choose Read Replica vs. Primary Node.
   * Vendor driver adapter (`src/infra/database/adapters/`) sends binary query protocol to database engine.
   * Results are returned -> mapped via `schema/fromApi` -> delivered back to domain service.

---

### Kafka & Messaging Architecture Guidelines

1. **Package Messaging Specification (`messaging/`)**: All versioned Kafka topic provisioning specs (`messaging/topics/`), schema registry payload definitions (`messaging/schema-registry/`), DLQ retry policies (`messaging/dlq/`), consumer group subscriptions (`messaging/subscriptions/`), and topic lock files (`topics.lock`) are strictly owned by `messaging/` at the sub-package root level.
2. **Centralized Messaging Infra (`src/infra/messaging/`)**: Low-level Kafka broker connections, connection pooling, SASL configs, connection factories (`factory/`), typed producers (`producers/`), consumers (`consumers/`), middleware (`middleware/`), and topic migration runners (`migrations/`) are maintained in `src/infra/messaging/`. Never open raw Kafka sockets or initialize driver instances inside feature handlers or HTTP routers.
3. **Topic Migrations & Rollback Engine (`messaging/topics/` & `src/infra/messaging/migrations/`)**: Every Kafka topic MUST be provisioned via versioned migration specs (`NNNN_topic_name.json`) and matching rollback files (`NNNN_topic_name.rollback.json`). Topic definitions declare partition counts, replication factor, retention MS, cleanup policy (`delete` | `compact`), and `min.insync.replicas`.
4. **Distributed Tracing Graph & W3C Context Propagation**:
   - **Producer Injection**: Producer automatically injects OpenTelemetry W3C Trace Context (`traceparent` and `tracestate`) into Kafka Message Headers before publishing.
   - **Consumer Extraction**: Consumer extracts `traceparent` from Kafka Message Headers to parent child spans, generating a complete, contiguous distributed tracing graph across microservice boundaries.
   - **Correlation & Baggage**: Passes `correlation_id` and `tenant_id` in headers for global trace query filtering.
5. **Scale & Performance Optimizations**:
   - **Idempotence & Reliability**: Enable idempotent producer (`enable.idempotence=true`, `acks=all`) for exactly-once in-order message delivery.
   - **Batching & Compression**: Configure producer batching (`linger.ms=10`, `batch.size=32768`) with `snappy` or `zstd` compression.
   - **Consumer Backpressure & Offsets**: Consumers process messages in batches, commit offsets asynchronously (`commitAsync`), and route unprocessable messages to Dead Letter Queue (DLQ) retry topics (`{topic}-dlq`).
6. **Pluggable Messaging Middleware Engine (`src/shared/messaging/middleware/`)**: All event producers and consumers MUST execute through composable middleware pipelines (`ProducerMiddlewarePipeline`, `ConsumerMiddlewarePipeline`). Imperative duplicate `try/catch`, logging, or tracing boilerplate inside individual producer methods or consumer handler classes is strictly prohibited.
7. **CQRS & Append-Only Event Stream (`src/shared/messaging/cqrs/`)**: Write commands publish immutable, append-only events to Kafka. Writes never mutate read tables directly. Consumers fold incoming event streams into materialized projection stores (`projection.store.ts`), and isolated query selectors (`query.selectors.ts`) serve reads with zero write-side coupling.

---

### Order of Development & Change Management (7-Step Sequence)

To prevent contract drift, schema locking, and coupling violations, all development follows a strict 7-step sequence:

```
[1. API Contract] ──► [2. DB Migration] ──► [3. Port Interface] ──► [4. Data-Driven Schema & Queries] ──► [5. Service Logic] ──► [6. API Handler] ──► [7. Test Suite]
```

1. **Step 1 — API Contract Definition (`contracts/`)**: Define or update `openapi/v1.yaml`, `graphql/`, or `proto/` in a contract-only PR. Generate client SDKs via `generate.sh`.
2. **Step 2 — Database Schema Migration (`database/migrations/`)**: Create a numbered migration file (`database/migrations/NNNN_description.sql`) and matching rollback file (`database/migrations/NNNN_description.rollback.sql`).
3. **Step 3 — Shared Infrastructure Port Interface (`shared/ports/`)**: Declare or update abstract infrastructure interface ports (e.g. `database.interface`, `cache.interface`).
4. **Step 4 — Data-Driven Entity & Query Declaration (`src/features/{feature}/`)**: Declare entity schemas (`schema/`), flow-by-flow queries (`queries/`), transformation mappers (`fromApi`/`toApi`), and declarative rules (`rules/`).
5. **Step 5 — Core Domain Service Implementation (`src/features/{feature}/service`)**: Implement business logic using pure domain models and injected repository ports (no direct HTTP/IO).
6. **Step 6 — API Router & Handler Mounting (`src/api/rest/v1/`)**: Connect contract stubs to domain service methods via resource handlers (`auth.handler`).
7. **Step 7 — Comprehensive Test Suite Verification (`tests/`)**: Validate with unit tests, containerized integration tests, contract compliance tests, and K6 performance load tests.

---

### Zero-Downtime Database & Schema Migration Rules

All database modifications must comply with zero-downtime Expand and Contract migration rules:

1. **Versioned SQL Files Only**: Every schema change is a versioned SQL file inside `database/migrations/` with a mandatory rollback counterpart. Manual database tinkering is forbidden.
2. **Column Rename (5-PR Sequence)**:
   - PR 1: Add new column via migration file.
   - PR 2: Dual-write to both old and new columns in application layer.
   - PR 3: Backfill old data into new column via async worker.
   - PR 4: Switch application reads to new column.
   - PR 5: Drop old column via migration with rollback file.

---

### Maintenance Mapping for the 17 Distributed Persistence & Replication Patterns

Every distributed data persistence, replication, consensus, and conflict resolution pattern is maintained using a **Declarative Spec (`database/`) + Generic Adapter (`src/infra/adapters/`)** pattern:

| # | Distributed Pattern | Declarative Spec Location (`database/`) | Executable Infrastructure Adapter (`src/infra/adapters/`) |
|---|---|---|---|
| **1** | **Leader-Follower Replication** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/leader_follower.adapter` |
| **2** | **Multi-Leader Replication** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/multi_leader.adapter` |
| **3** | **Leaderless Dynamo-Style Quorums** | `database/quorums/quorum_config.yaml` | `src/infra/adapters/database/replication/leaderless_dynamo.adapter` |
| **4** | **Sync / Async / Semi-Sync ACKs** | `database/quorums/ack_policy.yaml` | `src/infra/adapters/database/replication/ack_pipeline.adapter` |
| **5** | **Chain Replication** | `database/replication/chain_replication.yaml` | `src/infra/adapters/database/replication/chain_replication.adapter` |
| **6** | **Raft State Machine Replication** | `database/consensus/raft_consensus.yaml` | `src/infra/adapters/database/consensus/raft_consensus.adapter` |
| **7** | **Quorum Configuration Layer** | `database/quorums/quorum_config.yaml` | `src/infra/adapters/database/quorums/quorum_validator.adapter` |
| **8** | **WAL Shipping** | `database/consensus/wal_shipping.yaml` | `src/infra/adapters/database/wal/wal_shipper.adapter` |
| **9** | **Change Data Capture (CDC)** | `database/cdc/cdc_publisher_spec.json` | `src/infra/adapters/database/cdc/cdc_stream_pipeline.adapter` |
| **10** | **Sharded Replication** | `database/sharding/shard_hash_ring.yaml` | `src/infra/adapters/database/sharding/sharded_router.adapter` |
| **11** | **Active-Active Replication** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/active_active.adapter` |
| **12** | **Active-Passive (Failover) Replication** | `database/fencing/fencing_epoch_failover.sql` | `src/infra/adapters/database/replication/active_passive.adapter` |
| **13** | **Gossip / Epidemic Propagation** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/gossip_protocol.adapter` |
| **14** | **CRDT-Based Replication** | `database/crdts/crdt_definitions.yaml` | `src/infra/adapters/database/crdts/crdt_merger.adapter` |
| **15** | **Anti-Entropy Repair (Merkle Trees)** | `database/anti_entropy/merkle_tree_sync.sql` | `src/infra/adapters/database/anti_entropy/merkle_anti_entropy.adapter` |
| **16** | **Fencing Epoch Token Control** | `database/fencing/fencing_epoch_failover.sql` | `src/infra/adapters/database/fencing/fencing_token_guard.adapter` |
| **17** | **Hybrid Clock & Conflict Helpers** | `database/crdts/hybrid_clock.yaml` | `src/infra/adapters/database/crdts/hybrid_clock_resolver.adapter` |

#### Architectural Maintenance Rules for Persistence Patterns:
1. **Zero Domain Logic Pollution**: Business domain services in `src/features/` MUST NEVER contain replication, consensus, vector clock, or Merkle tree code. Domain services invoke generic repository ports (`shared/ports/database.interface`), which delegate to the underlying infrastructure adapter.
2. **Declarative Spec First**: Changes to quorum ratios ($W + R > N$), ACK timeouts, partition specs, or CRDT types MUST be declared in `database/` configuration files before updating infrastructure adapters.
3. **Fencing Token Validation**: Multi-leader and active-passive failovers MUST validate monotonic fencing epoch tokens on every storage write to prevent split-brain stale writes.

#### Executable Reference Pseudocode: 17 Distributed Persistence & Replication Patterns

##### 9.1 Leader-Follower Replication
```python
def leader_write(leader_state, key, value, followers):
    entry = LogEntry(index=len(leader_state.log), term=leader_state.term, key=key, value=value)
    leader_state.log.append(entry)
    for follower in followers:
        follower.replicate_queue.append(entry)
    leader_state.commit_index = entry.index
    return entry.index


def follower_apply(follower_state):
    while follower_state.replicate_queue:
        entry = follower_state.replicate_queue.pop(0)
        follower_state.store[entry.key] = entry.value
        follower_state.applied_index = entry.index


def follower_read(follower_state, key, min_index):
    if follower_state.applied_index < min_index:
        raise ReplicaLagError(follower_state.applied_index, min_index)
    return follower_state.store.get(key)
```

##### 9.2 Multi-Leader Replication
```python
def multi_leader_write(local_node, key, value):
    version = VectorClock.increment(local_node.clock, local_node.id)
    entry = VersionedEntry(key=key, value=value, version=version, node_id=local_node.id)
    local_node.store[key] = entry
    for peer in local_node.peers:
        peer.enqueue_sync(entry)
    return entry


def multi_leader_receive_sync(local_node, incoming_entry):
    existing = local_node.store.get(incoming_entry.key)
    if existing is None:
        local_node.store[incoming_entry.key] = incoming_entry
        return
    comparison = VectorClock.compare(incoming_entry.version, existing.version)
    if comparison == VectorClockComparison.CONCURRENT:
        resolved = resolve_concurrent_conflict(existing, incoming_entry)
        local_node.store[incoming_entry.key] = resolved
    elif comparison == VectorClockComparison.GREATER:
        local_node.store[incoming_entry.key] = incoming_entry
```

##### 9.3 Leaderless (Dynamo-Style) Replication
```python
def leaderless_write(nodes, key, value, W, N):
    version = generate_monotonic_timestamp()
    entry = VersionedEntry(key=key, value=value, version=version)
    acks = 0
    for node in nodes:
        if node.write(entry):
            acks += 1
    if acks < W:
        raise WriteQuorumFailed(acks=acks, required=W)
    return version


def leaderless_read(nodes, key, R, N):
    responses = []
    for node in nodes:
        res = node.read(key)
        if res is not None:
            responses.append(res)
    if len(responses) < R:
        raise ReadQuorumFailed(responses=len(responses), required=R)
    latest = max(responses, key=lambda x: x.version)
    stale_nodes = [r for r in responses if r.version < latest.version]
    if stale_nodes:
        trigger_read_repair_async(stale_nodes, key, latest)
    return latest.value
```

##### 9.4 Synchronous vs. Asynchronous Replication
```python
def sync_replication_write(leader, followers, key, value):
    entry = LogEntry(key=key, value=value, term=leader.term)
    leader.log.append(entry)
    ack_count = 1
    for follower in followers:
        if follower.append_entries_sync(entry):
            ack_count += 1
    if ack_count < len(followers) + 1:
        raise SyncReplicationTimeout()
    leader.commit_index += 1
    return leader.commit_index


def async_replication_write(leader, followers, key, value):
    entry = LogEntry(key=key, value=value, term=leader.term)
    leader.log.append(entry)
    leader.commit_index += 1
    for follower in followers:
        follower.append_entries_async(entry)
    return leader.commit_index


def semi_sync_replication_write(leader, sync_followers, async_followers, key, value):
    entry = LogEntry(key=key, value=value, term=leader.term)
    leader.log.append(entry)
    for follower in sync_followers:
        follower.append_entries_sync(entry)
    leader.commit_index += 1
    for follower in async_followers:
        follower.append_entries_async(entry)
    return leader.commit_index
```

##### 9.5 Chain Replication
```python
def chain_write(head_node, key, value):
    tx_id = generate_tx_id()
    return head_node.process_chain_write(tx_id, key, value)


def process_chain_write(self, tx_id, key, value):
    self.pending_store[tx_id] = (key, value)
    if self.next_node is not None:
        return self.next_node.process_chain_write(tx_id, key, value)
    else:
        self.committed_store[key] = value
        self.ack_chain_upstream(tx_id)
        return tx_id


def chain_read(tail_node, key):
    return tail_node.committed_store.get(key)
```

##### 9.6 Consensus-Based Replication (Raft Engine)
```python
def raft_request_vote(node, candidate_term, candidate_id, last_log_index, last_log_term):
    if candidate_term < node.current_term:
        return VoteResponse(term=node.current_term, vote_granted=False)
    if candidate_term > node.current_term:
        node.current_term = candidate_term
        node.voted_for = None
        node.role = Role.FOLLOWER
    up_to_date = (last_log_term > node.last_log_term()) or (
        last_log_term == node.last_log_term() and last_log_index >= len(node.log) - 1
    )
    if (node.voted_for is None or node.voted_for == candidate_id) and up_to_date:
        node.voted_for = candidate_id
        return VoteResponse(term=node.current_term, vote_granted=True)
    return VoteResponse(term=node.current_term, vote_granted=False)


def raft_append_entries(node, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit):
    if term < node.current_term:
        return AppendResponse(term=node.current_term, success=False)
    node.current_term = term
    node.role = Role.FOLLOWER
    if prev_log_index >= 0:
        if prev_log_index >= len(node.log) or node.log[prev_log_index].term != prev_log_term:
            return AppendResponse(term=node.current_term, success=False)
    node.log = node.log[: prev_log_index + 1] + entries
    if leader_commit > node.commit_index:
        node.commit_index = min(leader_commit, len(node.log) - 1)
        node.apply_logs_to_state_machine()
    return AppendResponse(term=node.current_term, success=True)
```

##### 9.7 Quorum Systems
```python
def evaluate_quorum_validity(N, W, R):
    is_strict = (W + R) > N
    is_write_capable = W > (N / 2)
    return {"strict_consistency": is_strict, "majority_write": is_write_capable}


def quorum_read_with_fallback(nodes, key, R, N):
    try:
        return leaderless_read(nodes, key, R, N)
    except ReadQuorumFailed:
        return fetch_stale_local_cache(key)
```

##### 9.8 Write-Ahead Log (WAL) Shipping
```python
def wal_flush_and_ship(wal_state, transaction, followers):
    record = WALRecord(lsn=wal_state.next_lsn, tx_id=transaction.id, payload=transaction.changes)
    wal_state.disk_file.append(record)
    wal_state.next_lsn += 1
    for follower in followers:
        follower.wal_receiver_queue.append(record)
    return record.lsn


def follower_wal_replay(follower_state):
    while follower_state.wal_receiver_queue:
        record = follower_state.wal_receiver_queue.pop(0)
        follower_state.disk_file.append(record)
        follower_state.apply_to_engine(record.payload)
        follower_state.flushed_lsn = record.lsn
```

##### 9.9 Change Data Capture (CDC)
```python
def cdc_wal_tailer(wal_stream, cdc_publisher, last_checkpoint_lsn):
    for record in wal_stream.read_from(last_checkpoint_lsn):
        if record.is_data_change():
            event = CDCEvent(
                table=record.table_name, operation=record.op_type, before=record.old_row, after=record.new_row, lsn=record.lsn
            )
            cdc_publisher.publish(event)
            checkpoint_lsn(record.lsn)


def cdc_apply_to_search_index(cdc_event, search_index_client):
    if cdc_event.operation == "INSERT" or cdc_event.operation == "UPDATE":
        search_index_client.index_document(id=cdc_event.after["id"], body=cdc_event.after)
    elif cdc_event.operation == "DELETE":
        search_index_client.delete_document(id=cdc_event.before["id"])
```

##### 9.10 Sharded Replication
```python
def get_shard_id(shard_key, num_shards):
    return hash_function(shard_key) % num_shards


def route_sharded_query(shard_map, shard_key, query):
    shard_id = get_shard_id(shard_key, len(shard_map))
    target_node = shard_map[shard_id]
    return target_node.execute(query)


def execute_scatter_gather(shard_map, global_query):
    results = []
    for node in shard_map.values():
        results.append(node.execute_async(global_query))
    merged = merge_query_results(await_all(results))
    return merged
```

##### 9.11 Active-Active Replication
```python
def active_active_write(region_a, region_b, key, value):
    ts = System.currentTimeMicros()
    entry = LWWEntry(value=value, timestamp=ts, writer_id=region_a.id)
    region_a.local_store.put(key, entry)
    region_b.async_replicate_queue.push((key, entry))
    return entry


def active_active_reconcile(node, key, incoming_entry):
    current = node.local_store.get(key)
    if current is None:
        node.local_store.put(key, incoming_entry)
    elif incoming_entry.timestamp > current.timestamp:
        node.local_store.put(key, incoming_entry)
    elif incoming_entry.timestamp == current.timestamp:
        if incoming_entry.writer_id > current.writer_id:
            node.local_store.put(key, incoming_entry)
```

##### 9.12 Active-Passive (Failover) Replication
```python
def failover_health_check(heartbeat_timestamp, timeout_ms):
    if current_time() - heartbeat_timestamp > timeout_ms:
        return ClusterHealth.PRIMARY_DEAD
    return ClusterHealth.OK


def execute_failover(cluster_state, candidate_node):
    cluster_state.primary_node.fence_writes()
    cluster_state.current_epoch += 1
    candidate_node.promote_to_primary(epoch=cluster_state.current_epoch)
    cluster_state.primary_node = candidate_node
    cluster_state.update_dns_routing(candidate_node.ip)
```

##### 9.13 Gossip / Epidemic Propagation
```python
def gossip_round(local_node, cluster_peers, k_random_nodes):
    targets = select_random_subset(cluster_peers, k_random_nodes)
    digest = local_node.generate_state_digest()
    for peer in targets:
        delta = peer.exchange_digest(digest)
        local_node.apply_state_delta(delta)


def update_local_gossip_state(local_node, key, value):
    local_node.heartbeat_counter += 1
    local_node.state_store[key] = GossipEntry(
        value=value, counter=local_node.heartbeat_counter, node_id=local_node.id
    )
```

##### 9.14 Conflict-Free Replicated Data Types (CRDTs)
```python
class PNCounter:
    def __init__(self, node_id):
        self.node_id = node_id
        self.P = {}
        self.N = {}

    def increment(self):
        self.P[self.node_id] = self.P.get(self.node_id, 0) + 1

    def decrement(self):
        self.N[self.node_id] = self.N.get(self.node_id, 0) + 1

    def value(self):
        return sum(self.P.values()) - sum(self.N.values())

    def merge(self, incoming):
        for k, v in incoming.P.items():
            self.P[k] = max(self.P.get(k, 0), v)
        for k, v in incoming.N.items():
            self.N[k] = max(self.N.get(k, 0), v)
```

##### 9.15 Anti-Entropy Repair (Merkle Trees)
```python
def compare_merkle_trees(local_node, remote_node, key_range):
    local_root = local_node.get_merkle_root(key_range)
    remote_root = remote_node.get_merkle_root(key_range)
    if local_root.hash == remote_root.hash:
        return
    sync_merkle_branches(local_node, remote_node, local_root, remote_root)


def sync_merkle_branches(local_node, remote_node, local_node_branch, remote_node_branch):
    if local_node_branch.is_leaf:
        if local_node_branch.hash != remote_node_branch.hash:
            repair_key(local_node, remote_node, local_node_branch.key)
        return
    for child_id in local_node_branch.children:
        if local_node_branch.children[child_id].hash != remote_node_branch.children[child_id].hash:
            sync_merkle_branches(
                local_node,
                remote_node,
                local_node_branch.children[child_id],
                remote_node_branch.children[child_id],
            )
```

##### 9.16 Monotonic Fencing Tokens
```python
def acquire_fencing_token(lock_service, resource_id):
    token = lock_service.increment_and_get_epoch(resource_id)
    return FencingToken(resource_id=resource_id, epoch=token)


def storage_write_with_fencing(storage_node, fencing_token, data):
    if fencing_token.epoch < storage_node.last_seen_epoch[fencing_token.resource_id]:
        raise StaleFencingTokenError(token_epoch=fencing_token.epoch, current_epoch=storage_node.last_seen_epoch[fencing_token.resource_id])
    storage_node.last_seen_epoch[fencing_token.resource_id] = fencing_token.epoch
    return storage_node.commit_write(data)
```

##### 9.17 Hybrid Logical Clocks (HLC)
```python
class HLC:
    def __init__(self, node_id):
        self.node_id = node_id
        self.l = 0
        self.c = 0

    def send_event(self, physical_time):
        l_prime = self.l
        self.l = max(l_prime, physical_time)
        if self.l == l_prime:
            self.c += 1
        else:
            self.c = 0
        return HLCTimestamp(l=self.l, c=self.c, node_id=self.node_id)

    def receive_event(self, msg_timestamp, physical_time):
        l_prime = self.l
        self.l = max(l_prime, msg_timestamp.l, physical_time)
        if self.l == l_prime and self.l == msg_timestamp.l:
            self.c = max(self.c, msg_timestamp.c) + 1
        elif self.l == l_prime:
            self.c += 1
        elif self.l == msg_timestamp.l:
            self.c = msg_timestamp.c + 1
        else:
            self.c = 0
        return HLCTimestamp(l=self.l, c=self.c, node_id=self.node_id)
```

---

### Maintenance Mapping for the 10 Data Partitioning & Storage Patterns

Data partitioning, LSM storage flushing, tiering, and polyglot workload dispatching are maintained via declarative declarations in `database/partitioning/` and `database/storage_engine/`, executed by generic adapters in `src/infra/adapters/database/`:

| # | Partitioning & Storage Pattern | Declarative Spec Location (`database/`) | Executable Infrastructure Adapter (`src/infra/adapters/`) |
|---|---|---|---|
| **8.1** | **Range-Based Partitioning** | `database/partitioning/range_partitioning.yaml` | `src/infra/adapters/database/partitioning/range_partition_router.adapter` |
| **8.2** | **Hash-Based Partitioning** | `database/partitioning/hash_partitioning.yaml` | `src/infra/adapters/database/partitioning/consistent_hash_ring.adapter` |
| **8.3** | **Directory-Based Partitioning** | `database/partitioning/directory_partitioning.json` | `src/infra/adapters/database/partitioning/directory_lookup_router.adapter` |
| **8.4** | **Read Replica Query Routing** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/read_replica_router.adapter` |
| **8.5** | **Write Replica (Designated Writer)** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/designated_writer_guard.adapter` |
| **8.6** | **Multi-Master Replication** | `database/replication/topology_spec.yaml` | `src/infra/adapters/database/replication/multi_master_reconciler.adapter` |
| **8.7** | **Log-Structured Storage (LSM)** | `database/storage_engine/lsm_storage.yaml` | `src/infra/adapters/database/storage/lsm_engine.adapter` |
| **8.8** | **Tiered Storage Management** | `database/storage_engine/tiered_storage.yaml` | `src/infra/adapters/database/storage/tiered_storage_migrator.adapter` |
| **8.9** | **Cold/Hot Data Separation** | `database/storage_engine/hot_cold_archiving.sql` | `src/infra/adapters/database/storage/hot_cold_archiver.adapter` |
| **8.10**| **Polyglot Persistence Dispatch** | `database/storage_engine/polyglot_dispatch.json` | `src/infra/adapters/database/storage/polyglot_workload_dispatcher.adapter` |

#### Architectural Rules for Data Partitioning & Storage Engine Maintenance:
1. **Dynamic Split & Ring Management**: Partition range splits (`range_partition_split`) and consistent hash ring virtual node additions (`add_node_to_ring`) MUST be declared in `database/partitioning/` configuration manifests and triggered via background administration workers.
2. **Read Replica Version Pins**: Read replica query routing (`route_read`) enforcing read-your-writes consistency MUST verify that `replica.applied_version >= client_last_write_version` before routing reads to replicas.
3. **Automated Storage Sweeps**: LSM compaction (`compact_sstables`), tiered migration (`tiering_sweep`), and cold archiving sweeps (`archive_sweep`) MUST be configured as scheduled database maintenance jobs declared in `database/storage_engine/`.

#### Executable Reference Pseudocode: 10 Data Partitioning & Storage Patterns

##### 8.1 Range-Based Partitioning
* **Definition**: Splits data across partitions based on contiguous ranges of a chosen key, so each partition owns one segment of the key’s ordered value space.
* **When to Use**: Frequent range-query workloads (time-range scans, alphabetical lookups) where preserving key ordering across partition boundaries matters more than perfectly even load distribution.
* **Who**: Router/partitioning layer of distributed databases (HBase region servers, Bigtable tablets, CockroachDB ranges).
* **How It Works**: Maintains a sorted list of split boundaries. Key lookups perform binary search over boundaries to identify the owning partition. Splits occur at median key when partition exceeds size threshold.

```python
def range_partition_lookup(partition_boundaries, key):
    index = binary_search_upper_bound(partition_boundaries, key)
    return partition_boundaries[index].partition_id


def range_partition_split(partition, split_key):
    left = Partition(start=partition.start, end=split_key, partition_id=new_partition_id())
    right = Partition(start=split_key, end=partition.end, partition_id=new_partition_id())
    return left, right


def range_partition_needs_split(partition, max_size):
    return partition.current_size() > max_size
```

##### 8.2 Hash-Based Partitioning
* **Definition**: Splits data across partitions based on the output of a hash function applied to the key, ensuring uniform distribution independent of key ordering.
* **When to Use**: Workloads needing even load distribution above all else, where point lookups dominate and range queries across keys are not required.
* **Who**: Routing proxy or client SDK (Cassandra, DynamoDB, sharded KV layer).
* **How It Works**: Hash function maps key to numeric token; partition = `hash(key) % N` or key's position on consistent hash ring with virtual nodes.

```python
def hash_partition_lookup(key, num_partitions):
    return stable_hash(key) % num_partitions


def consistent_hash_ring_lookup(ring_state, key):
    key_hash = stable_hash(key)
    position = bisect_right(ring_state.sorted_positions, key_hash)
    if position == len(ring_state.sorted_positions):
        position = 0
    return ring_state.node_at_position[ring_state.sorted_positions[position]]


def add_node_to_ring(ring_state, node_id, virtual_node_count):
    for i in range(virtual_node_count):
        position = stable_hash(f"{node_id}-{i}")
        ring_state.sorted_positions.append(position)
        ring_state.node_at_position[position] = node_id
    ring_state.sorted_positions.sort()
```

##### 8.3 Directory-Based Partitioning
* **Definition**: Uses a separate explicit lookup service that maps individual keys or key ranges to their owning partition, decoupling routing logic from algorithmic hashing.
* **When to Use**: Systems requiring dynamic key migration for rebalancing or dynamic partitioning rules for heterogeneous key subsets.
* **Who**: Dedicated metadata/directory service (etcd, ZooKeeper, metadata router).
* **How It Works**: Requests query directory lookup service. Operators reassign keys by updating directory entries in a strongly consistent coordination store.

```python
def directory_lookup(directory_store, key):
    entry = directory_store.get(key)
    if entry is None:
        raise UnroutedKeyError(key)
    return entry.partition_id


def directory_reassign(directory_store, key, new_partition_id):
    directory_store.put(key, DirectoryEntry(partition_id=new_partition_id, updated_at=current_time()))


def directory_bulk_reassign(directory_store, key_range, new_partition_id):
    for key in directory_store.keys_in_range(key_range):
        directory_reassign(directory_store, key, new_partition_id)
```

##### 8.4 Read Replica
* **Definition**: A copy of a dataset dedicated to serving read queries, kept up to date asynchronously from a primary that handles all writes.
* **When to Use**: Scaling read throughput independently of write throughput when read volume dominates.
* **Who**: Database streaming replication (Postgres/MySQL followers) and application query router.
* **How It Works**: Primary streams WAL to replicas. Query router routes reads to replicas based on lag tolerance or read-your-writes version requirements.

```python
def route_read(query, replica_pool, primary, requires_read_your_writes, client_last_write_version):
    if requires_read_your_writes:
        for replica in replica_pool:
            if replica.applied_version() >= client_last_write_version:
                return replica.execute(query)
        return primary.execute(query)
    replica = pick_least_loaded(replica_pool)
    return replica.execute(query)


def replica_apply_stream(replica_state, log_stream):
    for entry in log_stream:
        replica_state.apply(entry)
        replica_state.applied_version = entry.version
```

##### 8.5 Write Replica (Designated Writer)
* **Definition**: Dedicated single writer in a replica set that accepts writes, preventing multi-master concurrency conflicts by design.
* **When to Use**: Replicated systems prioritizing single-leader write simplicity over multi-region write availability.
* **Who**: Leader election layer (Raft consensus leader or primary node guard).
* **How It Works**: Non-writer nodes reject or proxy write operations to designated writer. Monotonic epoch fencing prevents stale writes during failover.

```python
def route_write(write_op, designated_writer, other_nodes):
    if write_op.target_node != designated_writer.node_id:
        raise NotWriterError(designated_writer.node_id)
    result = designated_writer.apply(write_op)
    for node in other_nodes:
        node.enqueue_replication(write_op)
    return result


def promote_new_writer(cluster_state, new_writer_node_id, fencing_epoch):
    if fencing_epoch <= cluster_state.current_epoch:
        raise StalePromotion(fencing_epoch, cluster_state.current_epoch)
    cluster_state.designated_writer = new_writer_node_id
    cluster_state.current_epoch = fencing_epoch
```

##### 8.6 Multi-Master Replication
* **Definition**: Replication topology where multiple nodes (often multi-region) independently accept writes and asynchronously reconcile.
* **When to Use**: High write availability requirements across geographical regions where cross-region latency must not block local writes.
* **Who**: Regional master nodes and conflict reconciliation engine (vector clock, HLC, CRDTs).
* **How It Works**: Masters process writes locally with version metadata (HLC/vector clock) and stream updates to peers for asynchronous reconciliation.

```python
def multi_master_write(local_master, key, value):
    version = HybridClock.tick(local_master.master_id)
    local_master.store[key] = VersionedValue(value, version)
    for peer in local_master.peers:
        peer.receive_write(key, value, version)
    return version


def receive_write(local_master, key, value, remote_version):
    existing = local_master.store.get(key)
    if existing is None or remote_version > existing.version:
        local_master.store[key] = VersionedValue(value, remote_version)
    elif remote_version == existing.version and existing.value != value:
        local_master.store[key] = resolve_conflict(existing, VersionedValue(value, remote_version))
```

##### 8.7 Log-Structured Storage (LSM)
* **Definition**: Storage engine design where writes land sequentially in memory (memtable) and flush to immutable sorted files (SSTables) on disk.
* **When to Use**: High write throughput ingestion pipelines (Cassandra, RocksDB, LevelDB).
* **Who**: Embedded storage engine layer.
* **How It Works**: Writes append to memtable; flushes produce SSTables. Background compaction merges SSTables to bound read amplification and prune obsolete entries.

```python
def lsm_write(lsm_state, key, value):
    lsm_state.memtable[key] = value
    if lsm_state.memtable.size() >= lsm_state.flush_threshold:
        flush_memtable(lsm_state)


def flush_memtable(lsm_state):
    sstable = SSTable.from_sorted_entries(sorted(lsm_state.memtable.items()))
    lsm_state.sstables.insert(0, sstable)
    lsm_state.memtable = {}


def lsm_read(lsm_state, key):
    if key in lsm_state.memtable:
        return lsm_state.memtable[key]
    for sstable in lsm_state.sstables:
        value = sstable.lookup(key)
        if value is not None:
            return value
    return None


def compact_sstables(lsm_state, level_threshold):
    if len(lsm_state.sstables) <= level_threshold:
        return
    merged = merge_sstables(lsm_state.sstables)
    lsm_state.sstables = [merged]
```

##### 8.8 Tiered Storage
* **Definition**: Strategy that automatically moves data across storage media (hot SSD, warm HDD, cold object storage) based on access patterns.
* **When to Use**: Long-tail access workloads where storing all data on high-performance media is cost-prohibitive.
* **Who**: Storage lifecycle policy manager.
* **How It Works**: Evaluates object idle time against policy thresholds and atomically migrates data between stores while updating location pointers.

```python
def evaluate_tier(access_metadata, tier_policy):
    idle_time = current_time() - access_metadata.last_accessed
    if idle_time < tier_policy.hot_max_idle:
        return "hot"
    if idle_time < tier_policy.warm_max_idle:
        return "warm"
    return "cold"


def migrate_tier(object_id, current_tier_store, target_tier_store, index):
    data = current_tier_store.read(object_id)
    target_tier_store.write(object_id, data)
    index.update_location(object_id, target_tier_store.tier_name)
    current_tier_store.delete(object_id)


def tiering_sweep(catalog, tier_policy, stores_by_tier, index):
    for object_id, access_metadata in catalog.all_entries():
        target_tier = evaluate_tier(access_metadata, tier_policy)
        current_tier = index.get_location(object_id)
        if target_tier != current_tier:
            migrate_tier(object_id, stores_by_tier[current_tier], stores_by_tier[target_tier], index)
```

##### 8.9 Cold/Hot Data Separation
* **Definition**: Bimodal application of tiering separating active operational data from historical archival data based on strict boundary rules.
* **When to Use**: Clear bimodal access patterns (e.g. recent 90 days hot vs historical cold).
* **Who**: Application data platform & archiving workers.
* **How It Works**: Hot store serves active writes/reads. Scheduled background job sweeps records older than retention threshold into compressed cold store.

```python
def route_write_hot(hot_store, key, value):
    hot_store.write(key, value)


def archive_sweep(hot_store, cold_store, retention_threshold):
    for key, metadata in hot_store.entries_older_than(retention_threshold):
        cold_store.write(key, hot_store.read(key))
        hot_store.delete(key)


def route_read(key, hot_store, cold_store):
    value = hot_store.read(key)
    if value is not None:
        return value
    return cold_store.read(key)
```

##### 8.10 Polyglot Persistence
* **Definition**: Routing operations across specialized database engines (Relational, Document/Search, Vector, Key-Value) optimized for specific workload access shapes.
* **When to Use**: Heterogeneous system workloads needing relational transactions, full-text search, vector embeddings, and ultra-fast session KV caches simultaneously.
* **Who**: Service workload router & CDC sync workers.
* **How It Works**: Dispatcher inspects workload type and routes to targeted store; CDC event pipelines keep secondary stores in sync with primary source of truth.

```python
def dispatch_by_workload(record, store_registry):
    if record.workload_type == "transactional":
        return store_registry["relational"].write(record)
    if record.workload_type == "search":
        return store_registry["document_search"].write(record)
    if record.workload_type == "embedding":
        return store_registry["vector"].write(record)
    if record.workload_type == "session_cache":
        return store_registry["key_value"].write(record)
    raise UnknownWorkloadType(record.workload_type)


def sync_across_stores(change_event, sink_writers):
    for sink in sink_writers:
        if sink.handles(change_event.entity_type):
            sink.apply(change_event)
```

---

### Maintenance Mapping for the 20 Complex Failure Diagnosis Patterns

All dynamic analysis, deadlock detection, profiling, tracing, formal verification, and fault injection patterns are maintained under a centralized **Observability & Diagnostics Runtime Engine (`src/infra/observability/`)** and **Diagnostics Test Suite (`tests/diagnostics/`)**:

| # | Failure Diagnosis Pattern | Specification / Log / Test Location | Executable Infrastructure Engine / Harness Location |
|---|---|---|---|
| **8.1** | **Happens-Before Race Detection** | `src/infra/observability/race_detection/` | `src/infra/observability/race_detection/race_detector.engine` |
| **8.2** | **Wait-For Graph Deadlock Detection** | `src/infra/observability/deadlock/` | `src/infra/observability/deadlock/wait_for_graph.engine` |
| **8.3** | **Chandy-Misra-Haas Distributed Deadlock Detection** | `src/infra/observability/deadlock/` | `src/infra/observability/deadlock/chandy_misra_haas.engine` |
| **8.4** | **Heap Diffing for Memory Leak Detection** | `src/infra/observability/heap_analysis/` | `src/infra/observability/heap_analysis/heap_differ.engine` |
| **8.5** | **Core Dump / Post-Mortem Memory Analysis** | `src/infra/observability/heap_analysis/` | `src/infra/observability/heap_analysis/core_dump_inspector.engine` |
| **8.6** | **Generational GC Pause Analysis** | `src/infra/observability/heap_analysis/` | `src/infra/observability/heap_analysis/gc_pause_correlator.engine` |
| **8.7** | **Continuous Profiling (Parca/Pyroscope-Style)** | `src/infra/observability/profiling/` | `src/infra/observability/profiling/continuous_profiler.engine` |
| **8.8** | **Flame Graph Differential Analysis** | `src/infra/observability/profiling/` | `src/infra/observability/profiling/flame_graph_differ.engine` |
| **8.9** | **eBPF Kernel-Level Syscall Tracing** | `src/infra/observability/ebpf/` | `src/infra/observability/ebpf/syscall_tracer.engine` |
| **8.10**| **Packet Capture / Wire-Level Analysis** | `src/infra/observability/wire_analysis/` | `src/infra/observability/wire_analysis/packet_capture_analyzer.engine` |
| **8.11**| **Jepsen-Style Linearizability Testing** | `tests/diagnostics/jepsen/` | `tests/diagnostics/jepsen/linearizability_verifier` |
| **8.12**| **TLA+ Formal Model Checking** | `tests/diagnostics/tla_plus/` | `tests/diagnostics/tla_plus/model_checker_runner` |
| **8.13**| **Byzantine Fault Injection & Diagnosis** | `tests/diagnostics/byzantine/` | `tests/diagnostics/byzantine/byzantine_injector_verifier` |
| **8.14**| **Quorum / Version-Vector Inspection** | `src/infra/observability/vector_inspection/` | `src/infra/observability/vector_inspection/version_vector_inspector.engine` |
| **8.15**| **Read-Repair / Anti-Entropy Divergence Audit** | `src/infra/observability/divergence_audit/` | `src/infra/observability/divergence_audit/anti_entropy_divergence_auditor.engine` |
| **8.16**| **Idempotency Key Audit** | `src/infra/observability/idempotency_audit/` | `src/infra/observability/idempotency_audit/idempotency_key_auditor.engine` |
| **8.17**| **Git Bisect / Automated Regression Bisection** | `tests/diagnostics/bisection/` | `tests/diagnostics/bisection/regression_bisector` |
| **8.18**| **Shadow-Traffic Differential Regression Detection** | `src/infra/observability/shadow_traffic/` | `src/infra/observability/shadow_traffic/shadow_traffic_comparator.engine` |
| **8.19**| **Circuit-Breaker State History Analysis** | `src/infra/observability/circuit_breaker_history/` | `src/infra/observability/circuit_breaker_history/circuit_breaker_cascade_analyzer.engine` |
| **8.20**| **Queueing-Theory (Little’s Law) Saturation Analysis** | `src/infra/observability/saturation_analysis/` | `src/infra/observability/saturation_analysis/littles_law_saturation_estimator.engine` |

#### Architectural Rules for Failure Diagnosis Maintenance:
1. **Zero Domain Logic Contamination**: Diagnostic tools, profilers, eBPF probes, and deadlock detectors MUST be maintained in `src/infra/observability/` or `tests/diagnostics/`. Feature service modules (`src/features/{feature}/`) MUST NEVER contain profiler sampling loops, raw socket capture, or formal verification logic.
2. **Production Overhead Constraints**: Continuous profiling (§8.7) and eBPF kernel tracing (§8.9) MUST maintain CPU overhead below 2%. Dynamic analysis tools with heavy overhead (ThreadSanitizer §8.1) MUST be restricted to CI/E2E test pipelines or targeted production debugging flags.
3. **Trace Context Correlation**: All diagnostic events (GC pauses, circuit breaker transitions, vector clock conflicts, shadow traffic diffs) MUST embed the OpenTelemetry W3C `traceparent` and `correlation_id` to allow unified timeline correlation.

#### Executable Reference Pseudocode: 20 Complex Failure Diagnosis Patterns

##### 8.1 Happens-Before Race Detection (ThreadSanitizer-Style)
* **Definition**: A dynamic analysis technique that tracks the happens-before partial order of memory accesses across threads at runtime, flagging any pair of unsynchronized accesses (at least one a write) to the same memory location that the analysis cannot prove are ordered.
* **When to Use**: During testing/CI for any concurrent code, and selectively in production for hard-to-reproduce concurrency bugs, accepting the tool’s runtime overhead as a worthwhile tradeoff.
* **Who**: A dynamic instrumentation tool (ThreadSanitizer, Go’s race detector) run as part of the build/test pipeline.
* **How It Works Internally**: The tool instruments every memory read/write and every synchronization primitive (lock, atomic, channel operation) at compile time. At runtime, it maintains vector-clock-like timestamps per thread and per memory location; on each access, it checks whether the access is ordered (via a happens-before relationship established by synchronization) relative to the last conflicting access — if not, and both accesses aren’t read-only, it reports a data race, including both stack traces.

```python
def record_access(access_log, thread_id, memory_address, is_write, vector_clock):
    access_log.setdefault(memory_address, []).append(
        AccessRecord(thread_id=thread_id, is_write=is_write, clock=dict(vector_clock))
    )


def check_race(access_log, memory_address, new_thread_id, new_is_write, new_clock):
    prior_accesses = access_log.get(memory_address, [])
    for prior in prior_accesses:
        if prior.thread_id == new_thread_id:
            continue
        if not (prior.is_write or new_is_write):
            continue
        if vector_clock_compare(prior.clock, new_clock) == "concurrent":
            return RaceDetected(prior_access=prior, new_thread_id=new_thread_id, address=memory_address)
    return None
```

##### 8.2 Wait-For Graph Deadlock Detection
* **Definition**: A technique that models “thread A is waiting for a lock held by thread B” as a directed graph edge, and detects deadlock as the presence of a cycle in that graph.
* **When to Use**: When a process appears hung with no CPU activity, and multiple threads are suspected to be waiting on each other’s locks.
* **Who**: A runtime debugger or a language runtime’s built-in deadlock detector (e.g., some JVM profilers, Go’s runtime deadlock panic).
* **How It Works Internally**: The detector inspects each blocked thread’s “waiting for lock X” state and each lock’s “currently held by thread Y” state, builds a directed graph (thread → lock it wants → thread holding it), and runs a cycle-detection algorithm (e.g., depth-first search with a visited set) over that graph; any cycle found is a proven deadlock, since every thread in the cycle is permanently blocked waiting for another thread in the same cycle.

```python
def build_wait_for_graph(blocked_threads, lock_owners):
    edges = {}
    for thread_id, wanted_lock in blocked_threads.items():
        owner = lock_owners.get(wanted_lock)
        if owner is not None:
            edges[thread_id] = owner
    return edges


def detect_cycle(wait_for_edges):
    visited = set()
    for start_node in wait_for_edges:
        path = set()
        current = start_node
        while current in wait_for_edges:
            if current in path:
                return build_cycle(path, current)
            path.add(current)
            current = wait_for_edges[current]
        visited |= path
    return None
```

##### 8.3 Chandy-Misra-Haas Distributed Deadlock Detection
* **Definition**: A distributed algorithm for detecting deadlock cycles that span multiple processes/nodes, where no single process can see the whole wait-for graph directly.
* **When to Use**: When lock/resource contention spans multiple services or nodes (e.g., a distributed transaction manager), and a local wait-for graph (§8.2) can’t see the full picture.
* **Who**: A distributed coordination component, or each node’s own transaction manager cooperating via the algorithm’s message protocol.
* **How It Works Internally**: A process suspecting deadlock (blocked waiting on a remote resource) sends a probe message along the direction of its wait-for edge, carrying the identities of the initiating and sending processes. Each process receiving a probe, if it is also blocked, forwards the probe further along its own wait-for edge; if a process ever receives a probe that it originally initiated, a cycle — and thus a genuine distributed deadlock — has been proven to exist.

```python
def initiate_probe(local_process_id, waited_on_process, blocked_resource):
    return Probe(initiator=local_process_id, sender=local_process_id, target=waited_on_process)


def on_receive_probe(process_state, probe, currently_blocked_on):
    if probe.initiator == process_state.process_id:
        return DeadlockDetected(cycle_initiator=probe.initiator)
    if currently_blocked_on is not None:
        forwarded = Probe(initiator=probe.initiator, sender=process_state.process_id, target=currently_blocked_on)
        return SendProbe(forwarded)
    return NoDeadlockYet()
```

##### 8.4 Heap Diffing for Memory Leak Detection
* **Definition**: A technique that captures two heap snapshots at different points in time and computes the difference in object counts/retained size per type, isolating what’s accumulating rather than being collected.
* **When to Use**: When a process’s memory usage grows monotonically over time without an obvious single allocation spike — the classic slow-leak profile.
* **Who**: A memory profiler (language-runtime-specific: pprof for Go, heap snapshots in Chrome DevTools/Node.js, jmap/VisualVM for the JVM).
* **How It Works Internally**: A full heap snapshot records every live object, its type, its size, and its retaining references (what’s keeping it alive). Diffing two snapshots taken minutes or hours apart identifies object types whose count grew disproportionately between the two, and following their retaining-reference chains reveals exactly which code path is holding onto objects that should have been eligible for collection.

```python
def capture_heap_snapshot(runtime_introspector):
    objects = runtime_introspector.enumerate_live_objects()
    grouped = {}
    for obj in objects:
        grouped.setdefault(obj.type_name, []).append(obj)
    return HeapSnapshot(by_type={t: len(objs) for t, objs in grouped.items()}, raw_objects=grouped)


def diff_snapshots(snapshot_before, snapshot_after, growth_threshold):
    growth = {}
    for type_name, count_after in snapshot_after.by_type.items():
        count_before = snapshot_before.by_type.get(type_name, 0)
        delta = count_after - count_before
        if delta > growth_threshold:
            growth[type_name] = delta
    return sorted(growth.items(), key=lambda kv: kv[1], reverse=True)


def trace_retaining_references(snapshot, type_name, sample_size):
    objects = snapshot.raw_objects.get(type_name, [])[:sample_size]
    return [obj.retaining_reference_chain() for obj in objects]
```

##### 8.5 Core Dump / Post-Mortem Memory Analysis
* **Definition**: Analyzing a full memory image of a crashed or hung process, captured at the moment of failure, to reconstruct exact program state without needing the process to still be running.
* **When to Use**: For crashes (segfaults, OOM kills) or hangs in native/unmanaged-memory languages (C, C++, Rust) where a garbage-collected heap profiler (§8.4) doesn’t apply.
* **Who**: An engineer using a debugger (gdb, lldb) or crash-analysis tool against a core dump file generated automatically at crash time.
* **How It Works Internally**: The OS (or a crash handler) writes the process’s entire address space, register state, and stack to a core file at the moment of a fatal signal. The debugger loads this file alongside the original binary’s debug symbols, letting the engineer inspect every thread’s exact call stack, every variable’s value, and walk raw memory structures exactly as they existed at the instant of failure — the ultimate ground truth for a crash, at the cost of requiring the crash to have actually happened and been captured.

```python
def load_core_dump(dump_path, binary_path, debugger):
    session = debugger.attach_core(dump_path, binary_path)
    return session


def enumerate_thread_stacks(debug_session):
    stacks = {}
    for thread in debug_session.threads():
        stacks[thread.id] = thread.backtrace()
    return stacks


def inspect_variable(debug_session, thread_id, frame_index, variable_name):
    frame = debug_session.thread(thread_id).frame(frame_index)
    return frame.read_variable(variable_name)
```

##### 8.6 Generational GC Pause Analysis
* **Definition**: Analyzing garbage collector logs/metrics to determine whether stop-the-world GC pauses are the actual cause of observed latency spikes or timeouts.
* **When to Use**: When a managed-runtime service (JVM, Go, .NET, Node.js) shows periodic latency spikes that correlate suspiciously with memory allocation rate rather than request load.
* **Who**: An engineer analyzing GC logs, or an APM tool that surfaces GC pause duration as a first-class metric alongside request latency.
* **How It Works Internally**: The runtime’s GC logs record each collection cycle’s start time, duration, and which generation (young/old) was collected. Overlaying these pause windows directly against the request-latency timeline reveals whether latency spikes align precisely with GC pauses (implicating GC tuning/allocation rate as the cause) or are independent of them (pointing elsewhere).

```python
def parse_gc_log(gc_log_lines):
    pauses = []
    for line in gc_log_lines:
        record = parse_gc_log_line(line)
        if record is not None:
            pauses.append(record)
    return pauses


def correlate_pauses_with_latency(gc_pauses, latency_samples, window_ms):
    correlated = []
    for pause in gc_pauses:
        overlapping = [s for s in latency_samples if abs(s.timestamp - pause.timestamp) <= window_ms]
        if overlapping:
            correlated.append((pause, overlapping))
    return correlated
```

##### 8.7 Continuous Profiling (Parca/Pyroscope-Style)
* **Definition**: Always-on, low-overhead sampling of every running process’s call stack (and often memory allocations) in production, aggregated over time into queryable flame graphs.
* **When to Use**: As standing production infrastructure, so that when a performance question arises, historical profile data already exists rather than needing to be captured reactively after the fact.
* **Who**: A continuous-profiling agent running on every host/pod, feeding a central profiling backend.
* **How It Works Internally**: A lightweight agent periodically interrupts each monitored process (via signal-based sampling or, more efficiently, eBPF-based sampling, §8.9) and records the current call stack across all threads. Samples are aggregated over time into a flame-graph-style representation where each function’s “width” represents the proportion of samples in which it was on the stack — because sampling is statistical and low-frequency, overhead stays low enough (typically 1–2%) to run continuously in production rather than only during ad-hoc investigations.

```python
def sample_stack(process_handle):
    return process_handle.get_current_stack_trace_all_threads()


def run_continuous_profiler(process_handles, sample_rate_hz, aggregator):
    interval = 1.0 / sample_rate_hz
    while True:
        for handle in process_handles:
            stack = sample_stack(handle)
            aggregator.record(stack)
        sleep(interval)


def aggregate_into_flame_graph(samples):
    root = FlameNode(name="root", count=0, children={})
    for stack in samples:
        node = root
        node.count += 1
        for frame in stack:
            node = node.children.setdefault(frame, FlameNode(name=frame, count=0, children={}))
            node.count += 1
    return root
```

##### 8.8 Flame Graph Differential Analysis
* **Definition**: Comparing two aggregated flame graphs — one from a known-healthy period, one from a degraded period — to visually and programmatically isolate which specific call path grew disproportionately expensive.
* **When to Use**: When continuous profiling data exists for both a good and a bad period, and the question is specifically “what changed in where time is being spent,” not just “what’s slow right now.”
* **Who**: The investigating engineer, using a profiling tool’s built-in diff view or a script comparing the two aggregated stack-sample datasets.
* **How It Works Internally**: Each flame graph is a tree where each node’s width is proportional to sample count along that call path. A differential view aligns the two trees by call path and colors each node by the delta in sample proportion between the two periods — a function that grew from 2% to 40% of total samples stands out immediately, pinpointing the regression without manually eyeballing two separate graphs.

```python
def diff_flame_graphs(good_root, bad_root, threshold_ratio):
    divergences = []

    def walk(good_node, bad_node, path):
        good_ratio = good_node.count / good_root.count if good_root.count else 0
        bad_ratio = bad_node.count / bad_root.count if bad_root.count else 0
        if abs(bad_ratio - good_ratio) > threshold_ratio:
            divergences.append((path, good_ratio, bad_ratio))
        for child_name, bad_child in bad_node.children.items():
            good_child = good_node.children.get(child_name, FlameNode(name=child_name, count=0, children={}))
            walk(good_child, bad_child, path + [child_name])

    walk(good_root, bad_root, [])
    return sorted(divergences, key=lambda d: abs(d[2] - d[1]), reverse=True)
```

##### 8.9 eBPF Kernel-Level Syscall Tracing (bpftrace/BCC-Style)
* **Definition**: Attaching lightweight, sandboxed probes directly to kernel functions, syscalls, or tracepoints, without modifying or restarting the application being observed.
* **When to Use**: When a performance or correctness question requires visibility below the application layer entirely — syscall latency, scheduler behavior, network stack internals, page faults — that no application-level instrumentation can see.
* **Who**: An engineer with kernel-tracing expertise, using tools like bpftrace or the BCC toolkit, typically during a targeted production investigation rather than as standing infrastructure (though continuous eBPF-based profiling is increasingly common, §8.7).
* **How It Works Internally**: A small eBPF program is compiled and loaded into the kernel, attached to a specific hook point (a syscall entry, a kernel function, a tracepoint). The kernel verifies the program is safe to run (bounded loops, no arbitrary memory access) before allowing it to execute in kernel context on every matching event, recording data into an efficient in-kernel data structure (a histogram, a ring buffer) that userspace tooling then reads and displays — all without stopping or modifying the traced process itself.

```python
def attach_syscall_probe(ebpf_loader, syscall_name, handler_program):
    program = ebpf_loader.compile(handler_program)
    ebpf_loader.attach_kprobe(syscall_name, program)
    return program


def read_histogram(ebpf_loader, program, map_name):
    return ebpf_loader.read_map(program, map_name)


def trace_syscall_latency(ebpf_loader, syscall_name, duration_seconds):
    program = attach_syscall_probe(ebpf_loader, syscall_name, latency_histogram_program())
    sleep(duration_seconds)
    histogram = read_histogram(ebpf_loader, program, "latency_hist")
    ebpf_loader.detach(program)
    return histogram
```

##### 8.10 Packet Capture / Wire-Level Analysis (tcpdump/Wireshark)
* **Definition**: Capturing raw network packets at the wire level to inspect exactly what bytes were sent and received, independent of what any application or library claims happened.
* **When to Use**: When a suspected bug lives specifically in network behavior — unexpected retransmissions, TLS handshake failures, malformed protocol framing — that application-level logs don’t capture because the application only sees what its network library chose to report.
* **Who**: An engineer directly capturing traffic on a suspect host or network segment, using tcpdump for capture and Wireshark (or a scriptable equivalent) for analysis.
* **How It Works Internally**: The capture tool places a network interface into promiscuous/capture mode and records every packet matching a filter (by host, port, protocol) to a file, including full headers and payload. The analysis tool then decodes each packet according to the relevant protocol stack (TCP/IP, TLS, HTTP), letting the engineer see exact sequence numbers, retransmissions, round-trip timing, and payload bytes — ground truth about what actually crossed the wire, bypassing any application-layer misreporting entirely.

```python
def start_capture(interface, filter_expression, output_file, capture_tool):
    return capture_tool.start(interface=interface, filter_expression=filter_expression, output_file=output_file)


def parse_capture_file(output_file, protocol_decoder):
    packets = protocol_decoder.read_pcap(output_file)
    return packets


def find_retransmissions(packets):
    seen_sequences = {}
    retransmissions = []
    for packet in packets:
        key = (packet.src, packet.dst, packet.sequence_number)
        if key in seen_sequences:
            retransmissions.append(packet)
        else:
            seen_sequences[key] = packet
    return retransmissions
```

##### 8.11 Jepsen-Style Linearizability Testing
* **Definition**: An empirical testing methodology that runs a real distributed system under induced faults (network partitions, clock skew, process pauses) while recording a full history of operations, then checks that recorded history against a formal consistency model (linearizability, serializability) using an automated checker.
* **When to Use**: Before trusting a database or consensus system’s advertised consistency guarantees in production — Jepsen-style testing has repeatedly found real violations in systems that “passed all their own tests.”
* **Who**: A dedicated testing harness (Jepsen itself, or a similar in-house tool) run against a real cluster of the system under test.
* **How It Works Internally**: The harness runs concurrent client operations (reads, writes, compare-and-swaps) against the system while simultaneously injecting faults on a schedule, recording every operation’s invocation and completion time alongside its result. After the run, a checker (e.g., the Knossos linearizability checker) attempts to find a legal sequential ordering of all recorded operations consistent with the claimed consistency model — if no such ordering exists, a genuine violation has been proven, not merely suspected.

```python
def run_fault_injection_workload(client_pool, fault_schedule, history_recorder):
    for fault in fault_schedule:
        schedule_fault(fault)
    for client in client_pool:
        for operation in client.generate_operations():
            invoke_time = current_wall_time_ms()
            result = client.execute(operation)
            complete_time = current_wall_time_ms()
            history_recorder.record(operation, result, invoke_time, complete_time)
    return history_recorder.get_history()


def check_linearizability(history, consistency_model_checker):
    return consistency_model_checker.verify(history)
```

##### 8.12 TLA+ Formal Model Checking
* **Definition**: Specifying a system’s behavior as a precise mathematical state machine in the TLA+ language, then using a model checker (TLC) to exhaustively (or statistically) explore reachable states and verify that specified invariants hold in every one.
* **When to Use**: For consensus, replication, or any protocol where correctness is safety-critical and the state space of possible interleavings is too large for testing to meaningfully sample — typically applied before or during implementation, not purely after a bug is found.
* **Who**: A protocol/systems engineer authoring the specification, often the same team designing the actual implementation.
* **How It Works Internally**: The specification defines the system’s possible states, the actions that transition between them, and a set of invariants that must hold in every reachable state (and often temporal properties about eventual behavior). The TLC model checker performs a breadth-first (or randomized, for large spaces) exploration of every state reachable from the initial state via every possible action ordering, halting and reporting a concrete counterexample trace the moment any explored state violates an invariant.

```python
def define_state_machine(initial_state, actions, invariants):
    return StateMachineSpec(initial_state=initial_state, actions=actions, invariants=invariants)


def explore_reachable_states(spec, max_states):
    frontier = [spec.initial_state]
    visited = set()
    while frontier and len(visited) < max_states:
        state = frontier.pop(0)
        state_key = hash_state(state)
        if state_key in visited:
            continue
        visited.add(state_key)
        for invariant in spec.invariants:
            if not invariant.holds(state):
                return InvariantViolation(state=state, invariant=invariant)
        for action in spec.actions:
            for next_state in action.apply(state):
                frontier.append(next_state)
    return NoViolationFound(states_explored=len(visited))
```

##### 8.13 Byzantine Fault Injection & Diagnosis
* **Definition**: Deliberately causing one or more nodes in a distributed system to return corrupted, inconsistent, or actively wrong (but well-formed) responses, to test whether the system correctly detects and tolerates this class of failure.
* **When to Use**: For systems explicitly designed to tolerate Byzantine faults (blockchain consensus, some multi-party financial systems), or to test the blast radius of a currently-crash-stop-only system if a Byzantine fault occurred despite not being designed for.
* **Who**: A dedicated fault-injection testing team or tool, operating against a controlled test cluster (Byzantine fault injection in live production is generally too risky to run deliberately).
* **How It Works Internally**: The injection tool intercepts a target node’s outgoing responses and deliberately modifies them (flips a value, returns a stale read, sends different answers to different requesters) while keeping the node otherwise appearing healthy (passing health checks, responding within normal latency). Correct behavior under the test is verified by checking whether the overall system either detects the discrepancy (via cross-validation, §3.6) or, for true BFT systems, continues producing correct results despite the corrupted node’s participation.

```python
def inject_byzantine_response(proxy_state, target_node, corruption_fn):
    proxy_state.corrupted_nodes[target_node] = corruption_fn


def intercept_response(proxy_state, node_id, original_response):
    corruption_fn = proxy_state.corrupted_nodes.get(node_id)
    if corruption_fn is not None:
        return corruption_fn(original_response)
    return original_response


def detect_byzantine_via_cross_validation(responses_by_node, agreement_threshold):
    value_counts = {}
    for node_id, response in responses_by_node.items():
        value_counts[response] = value_counts.get(response, 0) + 1
    majority_value, majority_count = max(value_counts.items(), key=lambda kv: kv[1])
    if majority_count / len(responses_by_node) < agreement_threshold:
        return SuspectedByzantineDisagreement(value_counts)
    dissenting_nodes = [n for n, r in responses_by_node.items() if r != majority_value]
    return dissenting_nodes
```

##### 8.14 Quorum / Version-Vector Inspection
* **Definition**: Directly querying the version-vector (or vector-clock) metadata attached to a specific key across all its replicas, to explain conflicting concurrent writes without manually reasoning through the causality math for every individual event.
* **When to Use**: In leaderless/Dynamo-style systems when a specific key shows unexpected “sibling” values, and you need to know exactly why the system considered two writes concurrent.
* **Who**: An operator or engineer using the database’s own inspection/debug tooling (e.g., Riak’s sibling-inspection API, Cassandra’s nodetool) directly against the affected key.
* **How It Works Internally**: The tool queries each replica holding the key in question and retrieves its stored version vector alongside the value. Comparing these vectors directly (using the same before/after/concurrent logic as vector clock comparison) shows precisely which writes the system genuinely could not causally order — turning an abstract “why do I have siblings” question into a concrete, per-key causality proof.

```python
def fetch_version_vectors(replicas, key):
    return {replica.id: replica.get_version_vector(key) for replica in replicas}


def explain_conflict(version_vectors):
    keys = list(version_vectors.keys())
    conflicts = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            relation = vector_clock_compare(version_vectors[keys[i]], version_vectors[keys[j]])
            if relation == "concurrent":
                conflicts.append((keys[i], keys[j]))
    return conflicts
```

##### 8.15 Read-Repair / Anti-Entropy Divergence Audit
* **Definition**: A direct, targeted comparison of a specific key’s (or key range’s) value across all replicas holding it, to determine whether and how they currently disagree — a consistency question, answered independent of how the disagreement arose.
* **When to Use**: When a symptom looks like “different clients see different values for the same key,” and the question is simply “what does each replica currently believe,” not “how did they get that way”.
* **Who**: An operator running the database’s built-in repair/audit tooling, or a script directly querying each replica.
* **How It Works Internally**: The tool issues a direct read against each replica individually (bypassing the normal quorum-read path that would silently resolve conflicts before the client sees them) and compares the raw returned values and their metadata; any disagreement found is either a transient replication-lag artifact (self-resolving) or a genuine divergence requiring manual repair, distinguishable by whether the values converge on a follow-up read after normal replication has had time to catch up.

```python
def audit_key_across_replicas(replicas, key):
    values = {}
    for replica in replicas:
        values[replica.id] = replica.direct_read(key)
    distinct_values = set(values.values())
    if len(distinct_values) <= 1:
        return NoDivergence()
    return DivergenceFound(values)


def repair_divergence(replicas, key, winning_value, winning_version):
    for replica in replicas:
        current = replica.direct_read(key)
        if current != winning_value:
            replica.put(key, winning_value, winning_version)
```

##### 8.16 Idempotency Key Audit
* **Definition**: Tracing a specific message or request’s unique idempotency key through a dedupe table to determine whether it was processed more than once, diagnosing apparent “double effect” bugs that are actually a delivery-layer artifact, not an application logic bug.
* **When to Use**: When an effect (a charge, a notification, a state transition) appears to have happened twice, and the question is whether this is genuine application logic failure or simply at-least-once redelivery slipping past (or bypassing) deduplication.
* **Who**: An engineer querying the dedupe/idempotency-key store directly during an incident investigation.
* **How It Works Internally**: Every processed message is recorded in a dedupe table keyed by its idempotency key, typically alongside a timestamp and a TTL. Auditing a suspected double-processing incident means querying this table for the specific key in question: if it shows two separate processing timestamps with no entry expiration between them, the deduplication check itself has a bug; if the entry expired before the second delivery arrived, the retention window is too short relative to the broker’s actual redelivery timing — two different fixes for what initially looks like the same symptom.

```python
def audit_idempotency_key(dedupe_store, idempotency_key):
    records = dedupe_store.find_all(idempotency_key)
    if len(records) <= 1:
        return SingleProcessing(records)
    return DoubleProcessingDetected(records)


def diagnose_double_processing_cause(records, dedupe_ttl_seconds):
    gap = records[-1].timestamp - records[0].timestamp
    if gap > dedupe_ttl_seconds:
        return TTLTooShort(gap=gap, ttl=dedupe_ttl_seconds)
    return DedupeLogicBug(gap=gap)
```

##### 8.17 Git Bisect / Automated Regression Bisection
* **Definition**: A binary-search procedure over commit history that automatically narrows down the exact commit that introduced a regression, given a reliable, automatable way to test “is this commit good or bad.”
* **When to Use**: When a regression is confirmed to exist somewhere between a known-good and known-bad point in history, and a fast, deterministic reproduction check (a test, a benchmark threshold, a specific assertion) is available to run at each candidate commit.
* **Who**: The investigating engineer, typically automated via git bisect run against a script that returns pass/fail.
* **How It Works Internally**: Given a known-good commit and a known-bad commit, the tool checks out the commit exactly halfway between them (by commit-graph distance), runs the provided test/check, and marks that commit good or bad based on the result — repeating this halving process until only a single commit remains, which is guaranteed to be the exact change that introduced the regression, in O(log n) test runs rather than O(n).

```python
def bisect(known_good_commit, known_bad_commit, commit_graph, reproducer_fn):
    candidates = commit_graph.commits_between(known_good_commit, known_bad_commit)
    low, high = 0, len(candidates) - 1
    while low < high:
        mid = (low + high) // 2
        commit_graph.checkout(candidates[mid])
        if reproducer_fn():
            high = mid
        else:
            low = mid + 1
    return candidates[low]
```

##### 8.18 Shadow-Traffic Differential Regression Detection
* **Definition**: Mirroring real, live production traffic to both a current (control) and a candidate (treatment) version of a service simultaneously, continuously diffing their outputs and latencies without ever exposing the candidate’s responses to real users.
* **When to Use**: When a change’s correctness or performance under real traffic patterns and data distributions can’t be adequately validated by synthetic benchmarks or a limited canary — the direct debugging-focused sibling of the Shadow Deployment pattern.
* **Who**: A traffic-mirroring proxy or service-mesh feature, plus an automated comparator process, operated by the team validating a risky change before full rollout.
* **How It Works Internally**: Every real incoming request is duplicated; one copy is served normally by the control version, the other is sent asynchronously to the candidate version purely for observation. A comparator records every (request, control_response, candidate_response) triple and computes both an output-equivalence rate and a latency/error-rate delta over a large enough sample of real traffic to surface regressions that only manifest on inputs no synthetic test suite happened to construct.

```python
def mirror_request(request, control_service, candidate_service, comparator):
    control_response = control_service.handle(request)
    candidate_response = candidate_service.handle_async(request)
    comparator.record(request, control_response, candidate_response)
    return control_response


def summarize_regression_signal(comparator, sample_window):
    samples = comparator.recent_samples(sample_window)
    mismatches = [s for s in samples if s.control_response != s.candidate_response]
    latency_deltas = [s.candidate_latency - s.control_latency for s in samples]
    return RegressionSummary(
        mismatch_rate=len(mismatches) / len(samples),
        avg_latency_delta=sum(latency_deltas) / len(latency_deltas),
    )
```

##### 8.19 Circuit-Breaker State History Analysis
* **Definition**: Reviewing the timeline of circuit-breaker state transitions (closed → open → half-open → closed) across every service in a call chain to reconstruct the true sequence and cause of a cascading failure.
* **When to Use**: During or after an incident where many services’ circuit breakers tripped roughly simultaneously, and the question is which breaker tripped first — the actual root cause — versus which tripped in a legitimate, correctly-functioning protective cascade.
* **Who**: An engineer during incident review, correlating circuit-breaker metrics/logs across the full dependency graph.
* **How It Works Internally**: Each service’s circuit breaker emits a timestamped event on every state transition, tagged with the specific downstream dependency it protects. Ordering these events precisely reveals whether breaker B’s opening was a genuine independent failure or simply a correctly-functioning protective response to breaker A having already opened moments earlier — the difference between “two bugs” and “one bug plus correctly-working protection.”

```python
def record_breaker_transition(history_store, service_name, dependency_name, new_state, timestamp):
    history_store.append(BreakerEvent(service=service_name, dependency=dependency_name, state=new_state, timestamp=timestamp))


def find_first_trip(history_store, incident_window_start, incident_window_end):
    events = history_store.query_range(incident_window_start, incident_window_end)
    open_events = [e for e in events if e.state == "open"]
    return min(open_events, key=lambda e: e.timestamp) if open_events else None


def classify_cascade(history_store, first_trip, subsequent_events, propagation_window_ms):
    cascade = []
    for event in subsequent_events:
        if event.timestamp - first_trip.timestamp <= propagation_window_ms:
            cascade.append(event)
    return cascade
```

##### 8.20 Queueing-Theory (Little’s Law) Saturation Analysis
* **Definition**: Applying the queueing-theory identity L = λ × W (average number in system = arrival rate × average time in system) to explain why latency degrades non-linearly once a system's utilization crosses a critical threshold, rather than degrading gracefully and proportionally.
* **When to Use**: When latency spiked disproportionately to a relatively modest increase in request rate, and the question is whether the system crossed a saturation threshold rather than simply “got a bit more load.”
* **Who**: An engineer doing capacity-planning-style analysis during or after an incident, using queue-depth and latency metrics already collected by standard monitoring.
* **How It Works Internally**: By measuring arrival rate (λ) and observed average time-in-system (W) at different load levels, an engineer can compute implied queue length (L) and compare it against the system’s actual serving capacity; because wait time under a queueing model grows non-linearly (often approaching infinity) as utilization approaches 100%, this analysis explains why a system that handled 80% utilization fine can fall over completely at 95% utilization — a qualitative, not merely quantitative, behavior change that simple “requests per second” dashboards don’t make visually obvious on their own.

```python
def compute_littles_law(arrival_rate, avg_time_in_system):
    return arrival_rate * avg_time_in_system


def estimate_saturation_point(historical_utilization, historical_latency):
    points = sorted(zip(historical_utilization, historical_latency), key=lambda p: p[0])
    for i in range(1, len(points)):
        prev_util, prev_latency = points[i - 1]
        curr_util, curr_latency = points[i]
        if prev_latency > 0 and (curr_latency / prev_latency) > ((curr_util / prev_util) ** 2):
            return curr_util
    return None
```

---

### Maintenance Mapping for the 17 Distributed Failure Diagnosis Patterns

Distributed event ordering, logical clocks, W3C trace context, state machine transition logs, event replay, WAL log tailing, boundary VCR proxies, chaos engineering, and statistical trace analysis are maintained under **Observability (`src/infra/observability/`)** and **Diagnostics Test Suites (`tests/diagnostics/`)**:

| # | Distributed Failure Diagnosis Pattern | Specification / Log / Test Location | Executable Infrastructure Engine / Harness Location |
|---|---|---|---|
| **8.1** | **Lamport Logical Clocks** | `src/infra/observability/clocks/` | `src/infra/observability/clocks/lamport_clock.engine` |
| **8.2** | **Vector Clocks** | `src/infra/observability/clocks/` | `src/infra/observability/clocks/vector_clock.engine` |
| **8.3** | **Hybrid Logical Clocks (HLC)** | `src/infra/observability/clocks/` | `src/infra/observability/clocks/hlc.engine` |
| **8.4** | **W3C Trace Context Propagation** | `src/infra/observability/tracing/` | `src/infra/observability/tracing/w3c_trace_propagator.engine` |
| **8.5** | **Correlation ID / Causation ID** | `src/infra/observability/tracing/` | `src/infra/observability/tracing/correlation_causation_tracker.engine` |
| **8.6** | **Explicit State Machine + Transition Log** | `src/infra/observability/transition_log/` | `src/infra/observability/transition_log/transition_logger.engine` |
| **8.7** | **Chandy-Lamport Snapshot Algorithm** | `src/infra/observability/snapshots/` | `src/infra/observability/snapshots/chandy_lamport_snapshot.engine` |
| **8.8** | **Event-Sourced Replay-to-Point** | `src/infra/observability/replay/` | `src/infra/observability/replay/event_sourced_replay.engine` |
| **8.9** | **Distributed Transaction Log Mining (WAL Tailing)** | `database/cdc/` | `src/infra/observability/wal_miner/wal_log_miner.engine` |
| **8.10**| **Deterministic Replay from Event Log** | `tests/diagnostics/replay/` | `src/infra/observability/replay/deterministic_event_replayer.engine` |
| **8.11**| **Record/Replay at Network Boundary (VCR Proxies)** | `tests/diagnostics/vcr_proxy/` | `tests/diagnostics/vcr_proxy/boundary_vcr_proxy.harness` |
| **8.12**| **Chaos Engineering (Fault Injection)** | `tests/diagnostics/chaos/` | `tests/diagnostics/chaos/chaos_fault_injector.harness` |
| **8.13**| **Deepest-Leaf-Error Walk** | `src/infra/observability/tracing/` | `src/infra/observability/tracing/deepest_leaf_error_walker.engine` |
| **8.14**| **Tail-Based Sampling (100% Retention on Error)** | `src/infra/observability/tracing/` | `src/infra/observability/tracing/tail_based_sampler.engine` |
| **8.15**| **Differential Trace Diff** | `src/infra/observability/tracing/` | `src/infra/observability/tracing/differential_trace_differ.engine` |
| **8.16**| **BubbleUp-Style Distributional Diff** | `src/infra/observability/analytics/` | `src/infra/observability/analytics/bubbleup_distributional_differ.engine` |
| **8.17**| **Service Dependency Graph + RED Metrics Overlay** | `src/infra/observability/topology/` | `src/infra/observability/topology/dependency_red_overlay.engine` |

#### Architectural Rules for Distributed Failure Diagnosis Maintenance:
1. **Mandatory Envelope Propagation**: Every event and async message MUST carry both `correlation_id` (flow identity) and `causation_id` (parent event identity) alongside the W3C `traceparent` header.
2. **Deterministic Replay Isolation**: Event replay (§8.8, §8.10) and boundary VCR proxies (§8.11) MUST execute in isolated sandbox environments with ZERO side-effects on live production storage or third-party APIs.
3. **Tail-Based Error Retention**: Production tracing collectors MUST implement tail-based sampling (§8.14) to enforce 100% retention for all error-status traces.

#### Executable Reference Pseudocode: 17 Distributed Failure Diagnosis Patterns

##### 8.1 Lamport Logical Clocks
* **Definition**: A per-process integer counter, incremented on every local event, that provides a total ordering of events across a distributed system without relying on physical clocks.
* **When to Use**: As a cheap baseline whenever you need some consistent ordering of events and don’t need to distinguish true causality from coincidental ordering.
* **Who**: Every process participating in the system, maintaining its own counter.
* **How It Works Internally**: Each process increments its counter before every local event. On sending a message, the current counter value is attached. On receiving a message, the process sets its counter to max(local_counter, received_counter) + 1. This guarantees that if event A causally precedes event B, A's timestamp is strictly less than B's — but the converse isn't guaranteed, so two truly unrelated events can still receive an ordered-looking pair of timestamps.

```python
def lamport_local_event(clock_state):
    clock_state.counter += 1
    return clock_state.counter


def lamport_send(clock_state):
    clock_state.counter += 1
    return clock_state.counter


def lamport_receive(clock_state, received_counter):
    clock_state.counter = max(clock_state.counter, received_counter) + 1
    return clock_state.counter
```

##### 8.2 Vector Clocks
* **Definition**: A per-process vector of counters (one slot per process in the system) that can definitively prove whether two events are causally related or provably concurrent.
* **When to Use**: Whenever you must distinguish “these two writes/events are causally related” from “these two happened independently with no knowledge of each other” — the exact question that matters for lost-update/conflict detection in replicated writes.
* **Who**: Every process, maintaining a full vector (not just its own counter).
* **How It Works Internally**: On a local event, a process increments only its own slot in its vector. On sending, it attaches the full vector. On receiving, it takes the componentwise maximum of its own vector and the received one, then increments its own slot. Comparing two vectors afterward: if one is componentwise ≤ the other everywhere, they’re causally ordered; if neither dominates the other, they are provably concurrent.

```python
def vector_local_event(vector_state, node_id):
    vector_state[node_id] = vector_state.get(node_id, 0) + 1
    return dict(vector_state)


def vector_receive(vector_state, node_id, received_vector):
    merged = dict(vector_state)
    for other_id, count in received_vector.items():
        merged[other_id] = max(merged.get(other_id, 0), count)
    merged[node_id] = merged.get(node_id, 0) + 1
    return merged


def vector_compare(vector_a, vector_b):
    a_leq_b = all(vector_a.get(k, 0) <= v for k, v in vector_b.items())
    b_leq_a = all(vector_b.get(k, 0) <= v for k, v in vector_a.items())
    if a_leq_b and not b_leq_a:
        return "before"
    if b_leq_a and not a_leq_b:
        return "after"
    if a_leq_b and b_leq_a:
        return "equal"
    return "concurrent"
```

##### 8.3 Hybrid Logical Clocks (HLC)
* **Definition**: A timestamp combining physical (wall-clock) time with a logical counter, staying both roughly wall-clock-sortable and causally correct.
* **When to Use**: When humans/operators need to ORDER BY timestamp across services and trust the result, but you also need the causal correctness guarantees plain physical timestamps can't provide.
* **Who**: Databases and distributed systems that expose timestamp-ordered reads to humans (CockroachDB, MongoDB use this internally).
* **How It Works Internally**: Each timestamp is a (physical_time, logical_counter) pair. On a local event, physical_time is read from the local (NTP/PTP-synced) clock; if it hasn't advanced since the last event, the logical counter increments instead, preserving strict ordering even when physical clocks tick at coarse granularity or momentarily disagree slightly across processes.

```python
def hlc_now(hlc_state, physical_time_fn):
    physical_now = physical_time_fn()
    if physical_now > hlc_state.physical_time:
        hlc_state.physical_time = physical_now
        hlc_state.logical_counter = 0
    else:
        hlc_state.logical_counter += 1
    return (hlc_state.physical_time, hlc_state.logical_counter)


def hlc_receive(hlc_state, physical_time_fn, received_physical, received_logical):
    physical_now = physical_time_fn()
    max_physical = max(hlc_state.physical_time, physical_now, received_physical)
    if max_physical == hlc_state.physical_time == received_physical:
        hlc_state.logical_counter = max(hlc_state.logical_counter, received_logical) + 1
    elif max_physical == hlc_state.physical_time:
        hlc_state.logical_counter += 1
    elif max_physical == received_physical:
        hlc_state.logical_counter = received_logical + 1
    else:
        hlc_state.logical_counter = 0
    hlc_state.physical_time = max_physical
    return (hlc_state.physical_time, hlc_state.logical_counter)
```

##### 8.4 W3C Trace Context Propagation
* **Definition**: A standardized HTTP header format (traceparent) that carries a trace ID and parent span ID across service boundaries, letting distributed traces be reconstructed after the fact.
* **When to Use**: In essentially any async or synchronous multi-service architecture — treated as non-negotiable baseline instrumentation, not an optional extra.
* **Who**: Every service’s HTTP/RPC client and server middleware, typically wired in by an observability/tracing library (OpenTelemetry SDK) rather than hand-written per call site.
* **How It Works Internally**: On an outbound call, the client middleware injects a traceparent header derived from the current span's trace ID and span ID. The receiving service's middleware extracts that header and starts its own span as a child of the received context, then re-injects an updated header on any further outbound calls it makes — building a tree of spans that a tracing backend can later reassemble into one trace.

```python
def inject_trace_context(current_span, outbound_headers):
    traceparent = format_traceparent(current_span.trace_id, current_span.span_id, current_span.flags)
    outbound_headers["traceparent"] = traceparent
    return outbound_headers


def extract_trace_context(inbound_headers, tracer):
    traceparent = inbound_headers.get("traceparent")
    if traceparent is None:
        return tracer.start_root_span()
    trace_id, parent_span_id, flags = parse_traceparent(traceparent)
    return tracer.start_child_span(trace_id, parent_span_id, flags)


def propagate_through_queue_message(current_span, message):
    message.headers["traceparent"] = format_traceparent(current_span.trace_id, current_span.span_id, current_span.flags)
    return message
```

##### 8.5 Correlation ID / Causation ID
* **Definition**: Two distinct identifiers attached to every event — correlation_id (constant across an entire business flow) and causation_id (pointing to the single direct parent event that caused this one) — used together to model fan-out/fan-in DAGs that a linear trace tree cannot represent.
* **When to Use**: When reconstructing “everything that resulted from X” across multiple independent consumers reacting to the same event (fan-out), which a strict parent-child trace tree structurally can’t express well.
* **Who**: The event-publishing and event-consuming code throughout the system, typically enforced by a shared event-envelope schema.
* **How It Works Internally**: Every event carries the correlation_id of the flow it belongs to (copied forward unchanged at every step) and a causation_id set to the ID of the specific event that directly triggered it. Querying "what happened because of event X" becomes a graph traversal following causation_id edges, while "show me everything in this business flow" becomes a flat filter on correlation_id.

```python
def build_event_envelope(correlation_id, causing_event_id, event_type, payload):
    return EventEnvelope(
        correlation_id=correlation_id,
        causation_id=causing_event_id,
        event_type=event_type,
        payload=payload,
    )


def trace_causal_chain(event_store, root_event_id):
    chain = [root_event_id]
    frontier = [root_event_id]
    while frontier:
        current_id = frontier.pop(0)
        children = event_store.find_by_causation_id(current_id)
        for child in children:
            chain.append(child.id)
            frontier.append(child.id)
    return chain
```

##### 8.6 Explicit State Machine + Transition Log
* **Definition**: Persisting an entity’s current state plus its last transition and the event that triggered it, rather than inferring the entity’s history by piecing together scattered log lines after the fact.
* **When to Use**: For long-running, multi-step async workflows (sagas, multi-day approval flows) where reconstructing “what step are we on and how did we get here” from raw logs is error-prone and slow mid-incident.
* **Who**: The workflow/process-manager code that owns the entity’s lifecycle.
* **How It Works Internally**: Every state transition writes (entity_id, previous_state, new_state, triggering_event_id, timestamp) as a durable record. Debugging a stuck or misbehaved workflow becomes reading this transition log directly, rather than grepping across many services' independent logs and manually inferring the sequence.

```python
def record_transition(transition_log_store, entity_id, previous_state, new_state, triggering_event_id):
    record = TransitionRecord(
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
        triggering_event_id=triggering_event_id,
        timestamp=current_wall_time_ms(),
    )
    transition_log_store.append(entity_id, record)
    return record


def reconstruct_entity_history(transition_log_store, entity_id):
    return transition_log_store.read_all(entity_id)
```

##### 8.7 Chandy-Lamport Snapshot Algorithm
* **Definition**: A distributed algorithm for capturing a globally consistent snapshot of system state across all processes and in-flight messages, without pausing the system.
* **When to Use**: For post-mortems requiring true global state at a specific past time when no pre-existing event log makes that state derivable for free.
* **Who**: A dedicated snapshot-coordination process, or the debugging/ops tooling initiating the snapshot across all participating processes.
* **How It Works Internally**: A coordinating process sends marker messages on all its outgoing channels and records its own local state. Each process, upon receiving its first marker (on any channel), immediately records its own local state and starts recording every subsequent message arriving on every other channel until a marker arrives there too — this per-channel marker-triggered recording is what guarantees the resulting global cut is consistent, without any process needing to stop.

```python
def initiate_snapshot(process_state, channels):
    process_state.recorded_state = process_state.local_state
    process_state.marker_received = {c: False for c in channels}
    process_state.recorded_messages = {c: [] for c in channels}
    for channel in channels:
        channel.send_marker()


def on_receive_marker(process_state, incoming_channel, channels):
    if process_state.recorded_state is None:
        process_state.recorded_state = process_state.local_state
        process_state.marker_received = {c: False for c in channels}
        process_state.recorded_messages = {c: [] for c in channels}
        process_state.marker_received[incoming_channel] = True
        for channel in channels:
            if channel != incoming_channel:
                channel.send_marker()
    else:
        process_state.marker_received[incoming_channel] = True


def on_receive_message(process_state, incoming_channel, message):
    if process_state.recorded_state is not None and not process_state.marker_received[incoming_channel]:
        process_state.recorded_messages[incoming_channel].append(message)
```

##### 8.8 Event-Sourced Replay-to-Point
* **Definition**: Reconstructing system state as of any past point by folding an append-only event log up to that point — applied here specifically as a debugging tool.
* **When to Use**: Any time the system already event-sources — this makes Chandy-Lamport-style snapshotting unnecessary, since the log already contains everything needed to derive any historical state on demand.
* **Who**: The debugging/tooling layer built on top of the existing event store.
* **How It Works Internally**: Given a target timestamp or sequence number, the tool folds the relevant aggregate’s events from InitialState (or the nearest snapshot before that point) up to the target, producing exactly the state that existed at that moment.

```python
def replay_to_point(event_store, stream_id, target_sequence, apply_fn, initial_state):
    events = event_store.read_stream_range(stream_id, 0, target_sequence)
    state = initial_state
    for event in events:
        state = apply_fn(state, event)
    return state


def replay_correlation_id_for_debugging(event_store, correlation_id, apply_fn, initial_state):
    events = event_store.find_by_correlation_id(correlation_id)
    state = initial_state
    trace = []
    for event in sorted(events, key=lambda e: e.sequence):
        state = apply_fn(state, event)
        trace.append((event.id, state))
    return trace
```

##### 8.9 Distributed Transaction Log Mining (WAL/Binlog Tailing)
* **Definition**: Reading a database’s own internal commit log (WAL, binlog) directly to determine ground truth of what actually persisted, bypassing application-level logging entirely.
* **When to Use**: When application logs are missing, incomplete, or simply wrong, and the database is the only reliable witness to what state changes truly occurred and in what order.
* **Who**: A CDC connector/agent (Debezium and similar), or a database administrator directly inspecting the WAL during an incident.
* **How It Works Internally**: The tool attaches to the database’s replication stream and reads every committed change in the exact order the database itself applied it, giving a ground-truth sequence of state changes independent of whatever the application code logged.

```python
def tail_wal_for_ground_truth(wal_reader, from_offset, output_sink):
    for change_record in wal_reader.stream_from(from_offset):
        output_sink.record(
            table=change_record.table,
            operation=change_record.operation,
            row_id=change_record.row_id,
            new_values=change_record.new_values,
            commit_timestamp=change_record.commit_timestamp,
        )


def cross_check_app_log_against_wal(app_log_entries, wal_ground_truth):
    discrepancies = []
    for entry in app_log_entries:
        matching_wal = wal_ground_truth.find(row_id=entry.row_id, timestamp_near=entry.timestamp)
        if matching_wal is None or matching_wal.new_values != entry.claimed_values:
            discrepancies.append((entry, matching_wal))
    return discrepancies
```

##### 8.10 Deterministic Replay from Event Log
* **Definition**: Reproducing a specific past incident offline by snapshotting pre-incident state and replaying the exact sequence of events for one correlation ID, entirely outside the live production system.
* **When to Use**: As the most reliable reproduction technique available, whenever an event log with sufficient granularity exists.
* **Who**: The engineer investigating the incident, running the replay against a sandboxed instance of the affected service(s).
* **How It Works Internally**: The pre-incident state is restored, and the exact events that occurred during the incident window for the relevant correlation ID are fed into the sandboxed system in their original order.

```python
def snapshot_pre_incident_state(event_store, snapshot_store, stream_id, incident_start_time, apply_fn, initial_state):
    events_before_incident = event_store.read_stream_before(stream_id, incident_start_time)
    state = initial_state
    for event in events_before_incident:
        state = apply_fn(state, event)
    snapshot_store.put(stream_id, state, incident_start_time)
    return state


def replay_incident_window(event_store, correlation_id, incident_start_time, incident_end_time, sandbox_system):
    events = event_store.find_by_correlation_id_in_window(correlation_id, incident_start_time, incident_end_time)
    for event in sorted(events, key=lambda e: e.sequence):
        sandbox_system.feed(event)
    return sandbox_system.get_final_state()
```

##### 8.11 Record/Replay at Network Boundary (VCR-Pattern Proxies)
* **Definition**: A proxy that captures real request/response pairs at a service’s network boundary during an incident, and later replays those exact captured responses against a sandboxed version of the service.
* **When to Use**: When the bug depends on the exact shape or timing of a specific external dependency’s response, and reproducing that dependency’s exact behavior on demand isn’t otherwise possible.
* **Who**: A recording/replay proxy sitting between the suspect service and its external dependency, operated by the investigating engineer.
* **How It Works Internally**: During normal operation, the proxy transparently logs every outbound request and response. During replay, the proxy serves those recorded responses instead of forwarding to the real dependency.

```python
def record_boundary_traffic(proxy_state, request, real_dependency):
    response = real_dependency.call(request)
    proxy_state.recordings.append(RecordedPair(request=request, response=response))
    return response


def replay_boundary_traffic(proxy_state, request, matcher_fn):
    for recording in proxy_state.recordings:
        if matcher_fn(recording.request, request):
            return recording.response
    raise NoMatchingRecording(request)
```

##### 8.12 Chaos Engineering (Fault Injection)
* **Definition**: The deliberate, proactive injection of failures (killed nodes, added latency, network partitions) into a system to discover failure modes before they occur naturally in production.
* **When to Use**: Proactively, before an incident — to study a suspected failure mode rather than to reproduce one specific past incident.
* **Who**: A dedicated chaos-engineering tool/team (Chaos Monkey and similar), running against a controlled subset of production or a staging environment.
* **How It Works Internally**: The tool selects a target and injects a defined fault (kill, delay, drop, corrupt) according to an experiment plan while monitoring system behavior against a hypothesis.

```python
def inject_latency_fault(target_service, delay_ms, duration_seconds):
    target_service.set_artificial_delay(delay_ms)
    schedule_after(duration_seconds, lambda: target_service.clear_artificial_delay())


def inject_node_kill(cluster_state, target_node_id):
    cluster_state.nodes[target_node_id].terminate()
    return cluster_state


def run_chaos_experiment(hypothesis, fault_fn, observation_fn, rollback_fn):
    fault_fn()
    observed = observation_fn()
    rollback_fn()
    return ExperimentResult(hypothesis_held=hypothesis.matches(observed), observed=observed)
```

##### 8.13 Deepest-Leaf-Error Walk
* **Definition**: A trace-analysis technique that finds the deepest span marked with an error status that itself has no error-marked children, distinguishing the actual root cause from every ancestor span that merely propagated the error status upward.
* **When to Use**: As the first move on any single failing trace — before reaching for any statistical or cross-trace technique.
* **Who**: The engineer (or an automated analysis tool) inspecting a specific trace in a tracing UI.
* **How It Works Internally**: Starting from the trace’s root span, the walker descends through every child marked as errored, continuing deeper as long as an errored child exists; the walk stops at the first span with an error status but no errored children.

```python
def find_root_cause_span(trace_tree):
    root_candidates = []

    def walk(span):
        error_children = [child for child in span.children if child.status == "error"]
        if span.status == "error" and not error_children:
            root_candidates.append(span)
        for child in error_children:
            walk(child)

    for root_span in trace_tree.root_spans:
        if root_span.status == "error":
            walk(root_span)
    return root_candidates
```

##### 8.14 Tail-Based Sampling (100% Retention on Error)
* **Definition**: A trace-sampling strategy that decides whether to retain a trace after observing its outcome, rather than deciding at the start of the trace (head-based sampling) before the outcome is known.
* **When to Use**: In any production system currently using head-based sampling where failing traces are lost to sampling filters.
* **Who**: The tracing infrastructure’s sampling layer/collector.
* **How It Works Internally**: All spans for a trace are buffered until the trace completes; only then is a sampling decision made, with a policy such as “always keep if any span has an error status”.

```python
def buffer_span(collector_state, trace_id, span):
    collector_state.buffers.setdefault(trace_id, []).append(span)


def finalize_trace_sampling_decision(collector_state, trace_id, export_fn):
    spans = collector_state.buffers.pop(trace_id, [])
    has_error = any(span.status == "error" for span in spans)
    if has_error or should_sample_by_rate(trace_id):
        export_fn(spans)
    return has_error
```

##### 8.15 Differential Trace Diff
* **Definition**: A technique that diffs span count, per-span duration, and span attributes between one known-good trace and one known-bad trace to isolate the exact point where their behavior diverges.
* **When to Use**: For emergent or interaction bugs where a single trace, examined alone, doesn’t reveal anything obviously wrong.
* **Who**: The investigating engineer, using a tracing tool’s comparison view or script.
* **How It Works Internally**: Two traces sharing a similar shape are aligned span-by-span; each corresponding pair is compared on duration, status, and attributes, flagging the first point of divergence.

```python
def align_spans(good_trace, bad_trace):
    aligned = []
    for good_span, bad_span in zip(good_trace.spans_in_order(), bad_trace.spans_in_order()):
        if good_span.name == bad_span.name:
            aligned.append((good_span, bad_span))
    return aligned


def diff_aligned_spans(aligned_pairs, duration_threshold_ms):
    divergences = []
    for good_span, bad_span in aligned_pairs:
        duration_delta = bad_span.duration_ms - good_span.duration_ms
        attribute_diff = {k: (good_span.attributes.get(k), v) for k, v in bad_span.attributes.items() if good_span.attributes.get(k) != v}
        if abs(duration_delta) > duration_threshold_ms or attribute_diff:
            divergences.append(SpanDivergence(span_name=good_span.name, duration_delta=duration_delta, attribute_diff=attribute_diff))
    return divergences
```

##### 8.16 BubbleUp-Style Distributional Diff
* **Definition**: An automated technique that, for every attribute across a large set of events, statistically tests whether its distribution differs significantly between a “good” event set and a “bad” event set, surfacing which fields correlate with the failure.
* **When to Use**: For unknown-unknown bugs with no pre-built dashboard or hypothesis about which field is responsible.
* **Who**: An analytics/observability platform (Honeycomb’s BubbleUp and similar tools).
* **How It Works Internally**: Partitions a large event set into good vs bad outcomes, then computes statistical divergence independently across every recorded attribute, ranking attributes by divergence score.

```python
def partition_events(events, is_bad_fn):
    good_events = [e for e in events if not is_bad_fn(e)]
    bad_events = [e for e in events if is_bad_fn(e)]
    return good_events, bad_events


def compute_attribute_divergence(good_events, bad_events, attribute_names, divergence_fn):
    scores = {}
    for attribute in attribute_names:
        good_values = [e.attributes.get(attribute) for e in good_events]
        bad_values = [e.attributes.get(attribute) for e in bad_events]
        scores[attribute] = divergence_fn(good_values, bad_values)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
```

##### 8.17 Service Dependency Graph + RED Metrics Overlay
* **Definition**: A visualization overlaying Rate/Error/Duration metrics onto a service call-dependency graph, used to quickly narrow which of many alarmed services is the actual cause versus a downstream victim.
* **When to Use**: As the very first triage step when many services show errors simultaneously.
* **Who**: The on-call engineer during initial incident triage.
* **How It Works Internally**: Builds dependency graph from trace samples, annotates nodes/edges with RED metrics, and filters candidate root causes by identifying upstream services whose errors predate downstream victims.

```python
def build_dependency_graph(trace_samples):
    edges = set()
    for trace in trace_samples:
        for parent_span, child_span in trace.parent_child_pairs():
            edges.add((parent_span.service_name, child_span.service_name))
    return DependencyGraph(edges=edges)


def overlay_red_metrics(dependency_graph, metrics_client, window_seconds):
    annotated = {}
    for service_name in dependency_graph.services():
        annotated[service_name] = RedMetrics(
            rate=metrics_client.query_rate(service_name, window_seconds),
            error_rate=metrics_client.query_error_rate(service_name, window_seconds),
            duration_p99=metrics_client.query_duration_p99(service_name, window_seconds),
        )
    return annotated


def rank_candidate_root_causes(dependency_graph, annotated_metrics, error_threshold):
    candidates = [s for s, m in annotated_metrics.items() if m.error_rate > error_threshold]
    upstream_only = [s for s in candidates if not any(dependency_graph.has_edge(other, s) and other in candidates for other in candidates)]
    return upstream_only
```

---

### Cross Sub-Package Communication Resolution Matrix

| Communication Scenario | Resolution Mechanism |
|---|---|
| **Shared Type (Same Language)** | Use `{lang}-shared/types/` via index export only. |
| **Runtime Service Call** | Full package boundary. Contract in `shared/contracts/` or `contracts/`, generated client SDK in `src/infra/clients/`. |
| **Pure Utility (No IO, Same Language)** | Use `{lang}-shared/utils/`. |
| **Pure Utility (Multi-Language)** | Shared utility contract or library at workspace root. |
| **Database Sharing** | Forbidden. Each sub-package owns its isolated database and schema. |
| **Event / Asynchronous Stream** | Schema in `shared/contracts/json-schema/` or `contracts/asyncapi/`, publish and subscribe via Kafka broker only. |
| **GraphQL Schema Overlap** | Schemas federated via `apis/gateway/graphql/stitcher`. Never merged manually inside `src/`. |

---

### Prohibited Speculative Generation Rules

To avoid repository bloat and maintain crisp architecture, the following are strictly prohibited:
- **`v2` Contracts**: Created ONLY when a breaking change forces a major version release.
- **Unselected Contract Trees**: Generating `proto/` or `graphql/` when building a REST service is forbidden.
- **Unneeded Client SDKs**: Generating client SDKs in `infra/clients/` when no upstream service call exists is forbidden.
- **Hand-Written API Types**: Hand-crafting request/response TypeScript/Go/Python types instead of generating them from contracts is forbidden.
