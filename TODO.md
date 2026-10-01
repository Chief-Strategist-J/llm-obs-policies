# Policies & AI Policy Orchestrator TODO & Prioritized Roadmap

For the complete architectural blueprint and itemized backlog, see the submodule document:
👉 [policy-orchestrator/TODO.md](file:///home/btpl-lap-22/live/llm-obs-infra/policies/policy-orchestrator/TODO.md)

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
