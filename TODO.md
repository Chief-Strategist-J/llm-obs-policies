# Policies & AI Policy Orchestrator TODO & Prioritized Roadmap

For the complete architectural blueprint and itemized backlog, see the submodule document:
👉 [policy-orchestrator/TODO.md](file:///home/btpl-lap-22/live/llm-obs-infra/policies/policy-orchestrator/TODO.md)

---

### 📊 Master Algorithm Engine Status (100% Complete)

| Domain Category | Algorithms Implemented | Dedicated REST Endpoints | Database Migration Seeds | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Vector Algorithms (`vectorAlgo/`)** | 200 / 200 | 200 mounted routes | Seeded in Catalog | 🟢 100% Complete |
| **File Indexing & Search (`fileIndexingAndSearching/`)** | 206 / 206 | 135 + 59 routes | Seeded in Catalog | 🟢 100% Complete |
| **Knowledge Graph (`knowlageGraph/`)** | 200 / 200 | 200 mounted routes | Seeded in Catalog | 🟢 100% Complete |
| **Graph Algorithms (`graphs/`)** | 320 / 320 | 320 mounted routes | Seeded in Catalog | 🟢 100% Complete |
| **OpenAPI 3.1 Specification** | 700 paths / 686 schemas | Complete | Synchronized | 🟢 100% Complete |
| **Database Migrations** | 869 contracts + 11 adapters | PostgreSQL + SQLite | Seeded & Verified | 🟢 100% Complete |
| **TOTALS** | **926 / 926 Live** | **700 Endpoints** | **869 Records** | **🟢 100% Complete** |

---

### 🚀 Prioritized Roadmap Summary

- **🔴 P0 (Critical / Next Sprint)**:
  1. AST-Safe Automated Zero-Inline-Comment Migrator (`libcst` / `tree-sitter`).
  2. Real-Time Streaming Telemetry & SSE (`/api/v1/agent/stream`).
  3. Multi-Project Workspace Batch Synchronizer (`policy-orchestrator sync`).
  4. GraphRAG Hybrid Fusion (Neo4j subgraphs + Qdrant dense vector embeddings).

- **🟠 P1 (High Priority)**:
  5. Hypothetical Document Embeddings (HyDE) & Cross-Encoder Reranker.
  6. Auto-Generated Scraper & AST Tool Self-Registration in `ToolRegistryPort`.
  7. Self-Updating Policy Proposal Engine (Automated PR Generator).
  8. OpenTelemetry Span Exporter to OTLP / Grafana Tempo.

- **🟡 P2 (Medium Priority)**:
  9. Multi-Agent Swarm Delegation (Linter, Security, Refactor, Docs Agents).
  10. Temporal / Durable Workflow Orchestration Worker.
  11. CloudEvents Git PR Webhook Consumer.

- **🟢 P3 (Future)**:
  12. Local Model Distillation & Quantized Policy Model Fine-Tuning.
  13. Multi-Modal Architecture Diagram Extractor.

